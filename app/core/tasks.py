"""Task processing functionality."""

import asyncio
import base64
import os
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from google import genai
from google.genai import types
import tiktoken
import json
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv
import time
import re
import markdown
from markdown.extensions import fenced_code, tables, toc, attr_list, def_list, footnotes
from markdown.extensions.codehilite import CodeHiliteExtension
from weasyprint import HTML, CSS
from weasyprint.text.fonts import FontConfiguration
from jinja2 import Environment, FileSystemLoader
import yaml
import logging
from tqdm import tqdm
import signal
import sys
from bs4 import BeautifulSoup
from config import SECTION_ORDER, AVAILABLE_LANGUAGES, PROMPT_FUNCTIONS, LLM_MODEL, LLM_TEMPERATURE

# Load environment variables from .env file
load_dotenv()

# Global flag for graceful shutdown
shutdown_requested = False

def signal_handler(signum, frame):
    """Handle interrupt signals gracefully."""
    global shutdown_requested
    if not shutdown_requested:
        shutdown_requested = True
    else:
        sys.exit(1)

# Register signal handlers
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

def count_tokens(text: str) -> int:
    """Count the number of tokens in a text string."""
    encoding = tiktoken.get_encoding("cl100k_base")  # Using OpenAI's encoding
    return len(encoding.encode(text))

def format_time(seconds: float) -> str:
    """Format time in seconds to a human-readable string."""
    if seconds < 60:
        return f"{seconds:.2f} seconds"
    minutes = int(seconds // 60)
    remaining_seconds = seconds % 60
    if minutes < 60:
        return f"{minutes} minutes {remaining_seconds:.2f} seconds"
    hours = int(minutes // 60)
    remaining_minutes = minutes % 60
    return f"{hours} hours {remaining_minutes} minutes {remaining_seconds:.2f} seconds"

def generate_content(client: genai.Client, prompt: str, output_path: Path) -> Dict:
    """Generate content for a single prompt and save to file. Returns token counts and timing."""
    start_time = time.time()
    try:
        contents = [
            types.Content(
                role="user",
                parts=[types.Part.from_text(text=prompt)],
            ),
        ]   
        tools = [types.Tool(google_search=types.GoogleSearch())]
        generate_content_config = types.GenerateContentConfig(
            temperature=LLM_TEMPERATURE,
            tools=tools,
            response_mime_type="text/plain",
        )

        # Create output directory if it doesn't exist
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Count input tokens
        input_tokens = count_tokens(prompt)
        
        # Collect output text
        full_output = ""
        
        # Open file for writing
        with open(output_path, 'w', encoding='utf-8') as f:
            response = client.models.generate_content_stream(
                model=LLM_MODEL,
                contents=contents,
                config=generate_content_config,
            )
            
            for chunk in response:
                if shutdown_requested:
                    raise InterruptedError("Generation interrupted by user")
                
                if chunk.text:
                    f.write(chunk.text)
                    f.flush()
                    full_output += chunk.text

        # Count output tokens
        output_tokens = count_tokens(full_output)
        
        execution_time = time.time() - start_time
        return {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": input_tokens + output_tokens,
            "execution_time": execution_time,
            "status": "success"
        }
    except Exception as e:
        execution_time = time.time() - start_time
        logging.error(f"Error generating content for {output_path.name}: {str(e)}")
        return {
            "input_tokens": 0,
            "output_tokens": 0,
            "total_tokens": 0,
            "execution_time": execution_time,
            "status": "error",
            "error": str(e)
        }

def get_user_input() -> tuple[str, str, list[str], list[tuple[str, str]]]:
    """Get company name, platform company name, languages, and prompts from user input."""
    company_name = input("\nEnter company name: ")
    platform_company_name = input("\nEnter platform company name (e.g., NESIC): ")
    
    print("\nAvailable languages:")
    for key, lang in AVAILABLE_LANGUAGES.items():
        print(f"{key}: {lang}")
    
    while True:
        languages = input("\nSelect language(s) (1-10, comma separated, default is 1 for Japanese): ").strip()
        if not languages:
            languages = "1"
            
        # Split by comma and remove whitespace
        language_keys = [key.strip() for key in languages.split(",")]
        
        # Validate all language keys
        if all(key in AVAILABLE_LANGUAGES for key in language_keys):
            break
        print("Invalid selection. Please choose numbers between 1 and 10, separated by commas.")

    # Prompt selection
    print("\nAvailable report sections:")
    for idx, (section_id, prompt_func) in enumerate(PROMPT_FUNCTIONS, 1):
        print(f"{idx}: {section_id}")
    print("0: Generate entire report (all sections)")

    while True:
        sections = input("\nSelect sections (comma-separated numbers, or 0 for all): ").strip()
        if not sections:
            sections = "0"

        # Split by comma and remove whitespace
        section_indices = [idx.strip() for idx in sections.split(",")]

        # Validate section indices
        try:
            section_indices = [int(idx) for idx in section_indices]
            if 0 in section_indices:
                selected_prompts = PROMPT_FUNCTIONS
                break
            elif all(1 <= idx <= len(PROMPT_FUNCTIONS) for idx in section_indices):
                # Convert indices to 0-based and get selected prompts
                selected_prompts = [PROMPT_FUNCTIONS[idx-1] for idx in section_indices]
                break
            else:
                print(f"Invalid selection. Please choose numbers between 0 and {len(PROMPT_FUNCTIONS)}.")
        except ValueError:
            print("Invalid input. Please enter numbers separated by commas.")
    
    return company_name, platform_company_name, language_keys, selected_prompts

def run_generation(company_name: str, platform_company_name: str, language: str, selected_prompts: list[tuple[str, str]], progress=None, language_task_id=None):
    """Generate content for selected prompts in parallel using ThreadPoolExecutor."""
    start_time = time.time()
    
    # Get API key from .env file
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not found in .env file")

    client = genai.Client(api_key=api_key)

    # Create timestamp for the directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Create base output directory with timestamp
    base_dir = Path("output") / f"{company_name}_{language}_{timestamp}"
    base_dir.mkdir(parents=True, exist_ok=True)
    
    # Create subdirectories
    markdown_dir = base_dir / "markdown"
    pdf_dir = base_dir / "pdf"
    misc_dir = base_dir / "misc"
    
    for dir_path in [markdown_dir, pdf_dir, misc_dir]:
        dir_path.mkdir(exist_ok=True)
    
    # Save generation config in misc directory
    config = {
        "company_name": company_name,
        "platform_company_name": platform_company_name,
        "language": language,
        "timestamp": datetime.now().isoformat(),
        "sections": [section[0] for section in selected_prompts],  # Only selected sections
        "model": LLM_MODEL,
        "temperature": LLM_TEMPERATURE
    }
    with open(misc_dir / "generation_config.yaml", "w") as f:
        yaml.dump(config, f)
    
    # Calculate optimal number of workers for prompt generation
    max_workers_prompts = max(len(selected_prompts), 10)
    
    # Process all prompts
    results = {}
    
    # If no progress display is provided, create a dummy progress context
    class DummyProgress:
        def add_task(self, *args, **kwargs):
            return None
        def update(self, *args, **kwargs):
            pass
    
    progress = progress or DummyProgress()
    
    # Create section tasks if we have a real progress display
    section_tasks = {}
    if not isinstance(progress, DummyProgress):
        for prompt_name, _ in selected_prompts:
            task_desc = f"[green]{language}: {prompt_name:.<30}"
            section_tasks[prompt_name] = progress.add_task(task_desc, total=1, visible=True)
    
    with ThreadPoolExecutor(max_workers=max_workers_prompts) as executor:
        futures = []
        for prompt_name, prompt_func_name in selected_prompts:
            if shutdown_requested:
                break
                
            # Get the prompt function from the prompt_testing module
            from app.core.prompts import get_prompt_fn
            prompt_func = get_prompt_fn(prompt_func_name)
            prompt = prompt_func(company_name, platform_company_name, language)
            output_path = markdown_dir / f"{prompt_name}.md"
            
            future = executor.submit(generate_content, client, prompt, output_path)
            futures.append((prompt_name, future))
        
        # Collect results
        for prompt_name, future in futures:
            try:
                if not shutdown_requested:
                    result = future.result()
                    results[prompt_name] = result
                    
                    # Update progress for this section
                    if prompt_name in section_tasks:
                        progress.update(section_tasks[prompt_name], 
                            advance=1,
                            description=f"[bold green]{language}: {prompt_name:.<30}✓"
                        )
                    
                    # Update language-level progress if provided
                    if language_task_id is not None:
                        progress.update(language_task_id, 
                            advance=1/len(selected_prompts),
                            description=f"[cyan]{language} Progress"
                        )
                else:
                    results[prompt_name] = {
                        "status": "interrupted",
                        "error": "Generation interrupted by user"
                    }
                    if prompt_name in section_tasks:
                        progress.update(section_tasks[prompt_name],
                            description=f"[yellow]{language}: {prompt_name:.<30}⚠"
                        )
            except Exception as e:
                logging.error(f"Error processing {prompt_name}: {str(e)}")
                results[prompt_name] = {
                    "status": "error",
                    "error": str(e)
                }
                if prompt_name in section_tasks:
                    progress.update(section_tasks[prompt_name],
                        description=f"[red]{language}: {prompt_name:.<30}✗"
                    )
    
    total_execution_time = time.time() - start_time
    
    # Compile token statistics
    token_stats = {
        "prompts": results,
        "summary": {
            "total_input_tokens": sum(r.get("input_tokens", 0) for r in results.values()),
            "total_output_tokens": sum(r.get("output_tokens", 0) for r in results.values()),
            "total_tokens": sum(r.get("total_tokens", 0) for r in results.values()),
            "total_execution_time": total_execution_time,
            "timestamp": datetime.now().isoformat(),
            "company_name": company_name,
            "platform_company_name": platform_company_name,
            "language": language,
            "model": LLM_MODEL,
            "temperature": LLM_TEMPERATURE,
            "successful_prompts": sum(1 for r in results.values() if r.get("status") == "success"),
            "failed_prompts": sum(1 for r in results.values() if r.get("status") in ["error", "interrupted"]),
            "interrupted": shutdown_requested
        }
    }
    
    # Save token statistics in misc directory
    stats_path = misc_dir / "token_usage_report.json"
    with open(stats_path, 'w', encoding='utf-8') as f:
        json.dump(token_stats, f, indent=2, ensure_ascii=False)
    
    return token_stats, base_dir

__all__ = ["run_generation", "get_user_input", "format_time"] 