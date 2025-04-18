#!/usr/bin/env python3

import sys
from pathlib import Path
# Add the parent directory to sys.path
sys.path.append(str(Path(__file__).parent.parent))

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.logging import RichHandler
from rich.panel import Panel
import logging
from concurrent.futures import ThreadPoolExecutor
from typing import List, Tuple
import sys

from app.core.tasks import run_generation, get_user_input, format_time
from app.core.generator import process_markdown_files
from config import AVAILABLE_LANGUAGES, LLM_MODEL, LLM_TEMPERATURE

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True)]
)
logger = logging.getLogger("rich")

# Rich console for better output
console = Console()

def main():
    try:
        # Get user input including prompt selection
        company_name, platform_company_name, language_keys, selected_prompts = get_user_input()
        
        # Create tasks for each language
        tasks = []
        for language_key in language_keys:
            language = AVAILABLE_LANGUAGES[language_key]
            console.print(f"\nGenerating prompts for {company_name} in {language}...")
            console.print(f"Using model: {LLM_MODEL} with temperature: {LLM_TEMPERATURE}")
            console.print("Output will be saved in the 'output' directory.\n")
            tasks.append((company_name, platform_company_name, language))

        # Calculate optimal number of workers for language-level parallelization
        max_workers_languages = max(len(tasks) * 2, 20)
        
        # Process all languages in parallel using ThreadPoolExecutor
        results = []
        
        # Create a single progress display for all languages
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(complete_style="green", finished_style="green"),
            TaskProgressColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            console=console,
            expand=True
        ) as progress:
            # Create language-level progress tasks
            language_tasks = {
                lang: progress.add_task(f"[cyan]{lang} Progress", total=len(selected_prompts))
                for _, _, lang in tasks
            }
            
            with ThreadPoolExecutor(max_workers=max_workers_languages) as executor:
                futures = []
                for company, platform_company, lang in tasks:
                    future = executor.submit(
                        run_generation,
                        company,
                        platform_company,
                        lang,
                        selected_prompts,  # Pass selected prompts
                        progress=progress,
                        language_task_id=language_tasks[lang]
                    )
                    futures.append((company, platform_company, lang, future))
                
                # Collect results
                for company, platform_company, lang, future in futures:
                    try:
                        token_stats, base_dir = future.result()
                        results.append((lang, token_stats, base_dir))
                        
                        # Display results for this language
                        console.print(f"\n[bold]Generation Summary for {lang}:[/bold]")
                        console.print(Panel.fit(
                            "\n".join([
                                f"Total Execution Time: {format_time(token_stats['summary']['total_execution_time'])}",
                                f"Total Tokens: {token_stats['summary']['total_tokens']:,}",
                                f"Successful Prompts: [green]{token_stats['summary']['successful_prompts']}[/]",
                                f"Failed Prompts: [red]{token_stats['summary']['failed_prompts']}[/]"
                            ]),
                            title=f"Results - {lang}",
                            border_style="cyan"
                        ))

                        # Generate PDF if there were successful prompts
                        if token_stats['summary']['successful_prompts'] > 0:
                            console.print(f"\n[bold cyan]Generating PDF report for {lang}...[/bold cyan]")
                            pdf_path = process_markdown_files(base_dir, company_name, lang)
                            
                            if pdf_path:
                                console.print(f"\n[green]PDF report generated for {lang}: {pdf_path}[/green]")
                            else:
                                console.print(f"\n[yellow]PDF generation failed for {lang}.[/yellow]")
                    except Exception as e:
                        console.print(f"\n[red]Error processing {lang}: {str(e)}[/red]")
                        logger.exception(f"Error processing {lang}")

        # Display final summary for all languages
        if results:
            console.print("\n[bold]Overall Generation Summary:[/bold]")
            total_execution_time = sum(stats['summary']['total_execution_time'] for _, stats, _ in results)
            total_tokens = sum(stats['summary']['total_tokens'] for _, stats, _ in results)
            total_successful = sum(stats['summary']['successful_prompts'] for _, stats, _ in results)
            total_failed = sum(stats['summary']['failed_prompts'] for _, stats, _ in results)
            
            console.print(Panel.fit(
                "\n".join([
                    f"Total Languages Processed: {len(results)}",
                    f"Total Execution Time: {format_time(total_execution_time)}",
                    f"Total Tokens Across All Languages: {total_tokens:,}",
                    f"Total Successful Prompts: [green]{total_successful}[/]",
                    f"Total Failed Prompts: [red]{total_failed}[/]"
                ]),
                title="Overall Results",
                border_style="cyan"
            ))
        
    except KeyboardInterrupt:
        console.print("\n[yellow]Process interrupted by user.[/yellow]")
    except Exception as e:
        console.print(f"\nError occurred: {str(e)}")
        logger.exception("Unexpected error occurred")
        console.print("Please check your configuration and try again.")

if __name__ == "__main__":
    main()