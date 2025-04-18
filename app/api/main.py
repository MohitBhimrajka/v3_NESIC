"""Main FastAPI application."""

import os
import sys
import uuid
import json
import shutil
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
from fastapi import FastAPI, BackgroundTasks, HTTPException, Query, Response
from fastapi.responses import FileResponse
from pydantic import BaseModel
import asyncio
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Import our core functionality
from app.core.tasks import run_generation
from app.core.generator import process_markdown_files
from config import AVAILABLE_LANGUAGES, PROMPT_FUNCTIONS, LLM_MODEL, LLM_TEMPERATURE

# Create FastAPI app
app = FastAPI(
    title="PDF Generation API",
    description="API for generating company research PDFs",
    version="1.0.0",
)

# Store for tasks
TASKS = {}

class GenerationRequest(BaseModel):
    """Request model for generation tasks."""
    company_name: str
    platform_company_name: str = ""
    language_key: str = "2"  # Default to English
    sections: List[int] = []  # Empty list means all sections
    
class TaskResponse(BaseModel):
    """Response model for task creation."""
    task_id: str
    status: str
    created_at: str
    
class TaskStatus(BaseModel):
    """Task status model."""
    task_id: str
    status: str
    created_at: str
    completed_at: Optional[str] = None
    progress: float = 0.0
    result: Optional[Dict[str, Any]] = None

def process_generation_task(
    task_id: str,
    company_name: str,
    platform_company_name: str,
    language_key: str,
    section_indices: List[int],
):
    """Process a generation task in the background."""
    try:
        TASKS[task_id]["status"] = "running"
        
        # Determine language
        if language_key not in AVAILABLE_LANGUAGES:
            raise ValueError(f"Invalid language key: {language_key}")
        language = AVAILABLE_LANGUAGES[language_key]
        
        # Determine which sections to generate
        if not section_indices:
            # Generate all sections
            selected_prompts = PROMPT_FUNCTIONS
        else:
            selected_prompts = []
            for idx in section_indices:
                if 1 <= idx <= len(PROMPT_FUNCTIONS):
                    selected_prompts.append(PROMPT_FUNCTIONS[idx-1])
                else:
                    raise ValueError(f"Invalid section index: {idx}")
        
        # Run the generation
        token_stats, base_dir = run_generation(
            company_name,
            platform_company_name,
            language,
            selected_prompts,
        )
        
        # Generate the PDF
        pdf_path = None
        if token_stats['summary']['successful_prompts'] > 0:
            pdf_path = process_markdown_files(base_dir, company_name, language)
        
        # Update task status
        TASKS[task_id].update({
            "status": "completed",
            "completed_at": datetime.now().isoformat(),
            "progress": 1.0,
            "result": {
                "token_stats": token_stats,
                "base_dir": str(base_dir),
                "pdf_path": str(pdf_path) if pdf_path else None,
            }
        })
        
    except Exception as e:
        logger.exception(f"Error processing task {task_id}: {str(e)}")
        TASKS[task_id].update({
            "status": "failed",
            "completed_at": datetime.now().isoformat(),
            "error": str(e),
        })

@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "PDF Generation API", "docs": "/docs"}

@app.post("/generate", response_model=TaskResponse)
async def generate_pdf(
    request: GenerationRequest, background_tasks: BackgroundTasks
):
    """Start a PDF generation task."""
    task_id = str(uuid.uuid4())
    now = datetime.now().isoformat()
    
    TASKS[task_id] = {
        "task_id": task_id,
        "status": "pending",
        "created_at": now,
        "request": request.dict(),
    }
    
    # Use FastAPI's BackgroundTasks to run the generation task
    background_tasks.add_task(
        process_generation_task,
        task_id,
        request.company_name,
        request.platform_company_name,
        request.language_key,
        request.sections,
    )
    
    return TaskResponse(task_id=task_id, status="pending", created_at=now)

@app.get("/status/{task_id}", response_model=TaskStatus)
async def get_task_status(task_id: str):
    """Get the status of a task."""
    if task_id not in TASKS:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return TaskStatus(**TASKS[task_id])

@app.get("/result/{task_id}/pdf")
async def get_pdf_result(task_id: str):
    """Get the PDF result of a completed task."""
    if task_id not in TASKS:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task = TASKS[task_id]
    if task["status"] != "completed":
        raise HTTPException(status_code=400, detail=f"Task not completed (status: {task['status']})")
    
    if "result" not in task or not task["result"].get("pdf_path"):
        raise HTTPException(status_code=404, detail="PDF not found")
    
    pdf_path = Path(task["result"]["pdf_path"])
    if not pdf_path.exists():
        raise HTTPException(status_code=404, detail="PDF file not found")
    
    return FileResponse(
        path=pdf_path,
        filename=pdf_path.name,
        media_type="application/pdf",
    )

@app.get("/tasks")
async def list_tasks():
    """List all tasks."""
    return {
        task_id: {
            "task_id": task_id,
            "status": task["status"],
            "created_at": task["created_at"],
            "completed_at": task.get("completed_at"),
        }
        for task_id, task in TASKS.items()
    }

@app.get("/languages")
async def list_languages():
    """List available languages."""
    return AVAILABLE_LANGUAGES

@app.get("/sections")
async def list_sections():
    """List available sections."""
    return {
        idx: section_id 
        for idx, (section_id, _) in enumerate(PROMPT_FUNCTIONS, 1)
    } 