# app/api/routes/scheduler.py
import os
import shutil
from typing import Any, Optional
from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse

from app.services.schedule_service import SchedulerService, get_scheduler_service
from app.schemas.scheduler import ScheduleCreate, ScheduleResponse
from app.utils.constants import SCRIPTS_DIR
from app.utils.service_results import handle_result
from app.utils.exceptions import AppException

router = APIRouter(prefix="/scheduler", tags=["Scheduler"])
templates = Jinja2Templates(directory="app/templates")

# Ensure the scripts directory exists
os.makedirs(SCRIPTS_DIR, exist_ok=True)

# API endpoints
@router.get("/schedules/", response_model=list[ScheduleResponse])
async def list_schedules(
    service: SchedulerService = Depends(get_scheduler_service),
) -> ScheduleResponse:
    """List all scheduled jobs"""
    result = await service.list_schedules()
    return handle_result(result)


@router.post("/schedules/", response_model=ScheduleResponse)
async def create_schedule(
    schedule: ScheduleCreate, service: SchedulerService = Depends(get_scheduler_service)
) -> ScheduleResponse:
    """Create a new scheduled job"""
    result = await service.create_schedule(schedule)
    return handle_result(result)


@router.get("/schedules/{job_id}", response_model=ScheduleResponse)
async def get_schedule(
    job_id: str, service: SchedulerService = Depends(get_scheduler_service)
) -> ScheduleResponse:
    """Get details of a specific scheduled job"""
    result = await service.get_schedule(job_id)
    return handle_result(result)


@router.delete("/schedules/{job_id}")
async def delete_schedule(
    job_id: str, service: SchedulerService = Depends(get_scheduler_service)
) -> ScheduleResponse:
    """Delete a scheduled job"""
    result = await service.delete_schedule(job_id)
    return handle_result(result)


@router.post("/schedules/{job_id}/execute", response_model=ScheduleResponse)
async def execute_now(
    job_id: str, service: SchedulerService = Depends(get_scheduler_service)
) -> ScheduleResponse:
    """Execute a scheduled job immediately"""
    result = await service.execute_job_now(job_id)
    return handle_result(result)


# UI routes for Jinja2 templates
@router.get("/", response_class=HTMLResponse)
async def scheduler_dashboard(
    request: Request, service: SchedulerService = Depends(get_scheduler_service)
) -> HTMLResponse:
    """Render the scheduler dashboard"""
    result = await service.list_schedules()
    if isinstance(result.value, AppException):
        raise HTTPException(
            status_code=result.value.status_code, detail=result.value.message
        )
    return templates.TemplateResponse(
        "scheduler/index.html", {"request": request, "schedules": result.value}
    )

# New route to show job details
@router.get("/schedules/{job_id}/detail", response_class=HTMLResponse)
async def scheduler_detail(
    request: Request,
    job_id: str,
    service: SchedulerService = Depends(get_scheduler_service)
):
    """Render the job detail view"""
    schedule_result = await service.get_schedule(job_id)
    if isinstance(schedule_result.value, AppException):
        raise HTTPException(status_code=schedule_result.value.status_code, detail=schedule_result.value.message)
    
    history_result = await service.get_execution_history(job_id)
    
    # Get script content
    script_content = ""
    try:
        with open(schedule_result.value.script_path, 'r') as f:
            script_content = f.read()
    except Exception as e:
        script_content = f"Error reading script: {str(e)}"
    
    return templates.TemplateResponse(
        "scheduler/detail.html",
        {
            "request": request, 
            "schedule": schedule_result.value,
            "execution_history": [] if isinstance(history_result.value, AppException) else history_result.value,
            "script_content": script_content
        }
    )

# Modified route to show the new schedule form with available scripts
@router.get("/new", response_class=HTMLResponse)
async def new_schedule_form(request: Request) -> HTMLResponse:
    """Render the new schedule form"""
    # Get all .sh files in the scripts directory
    available_scripts = []
    if os.path.exists(SCRIPTS_DIR):
        for filename in os.listdir(SCRIPTS_DIR):
            if filename.endswith('.sh'):
                available_scripts.append({
                    "name": filename,
                    "path": os.path.join(SCRIPTS_DIR, filename)
                })
    
    return templates.TemplateResponse(
        "scheduler/create.html",
        {"request": request, "available_scripts": available_scripts}
    )

@router.post("/new", response_model=Any)
async def handle_new_schedule(
    request: Request,
    script_selection_method: str = Form(...),
    schedule_type: str = Form(...),
    job_id: Optional[str] = Form(None),
    existing_script: Optional[str] = Form(None),
    script_file: Optional[UploadFile] = File(None),
    script_name: Optional[str] = Form(None),
    interval_seconds: Optional[int] = Form(None),
    cron_expression: Optional[str] = Form(None),
    service: SchedulerService = Depends(get_scheduler_service)
):
    """Handle form submission for a new schedule"""
    script_path = ""
    
    try:
        # Handle script selection or upload
        if script_selection_method == "existing":
            script_path = existing_script
        else:  # upload
            if not script_file:
                raise HTTPException(status_code=400, detail="No script file provided")
            
            # Sanitize script name
            if not script_name:
                script_name = script_file.filename
                if script_name.endswith(".sh"):
                    script_name = script_name[:-3]
            
            # Replace non-alphanumeric characters with hyphens
            import re
            script_name = re.sub(r'[^a-zA-Z0-9]', '-', script_name).lower()
            if not script_name.endswith('.sh'):
                script_name += '.sh'
                
            script_path = os.path.join(SCRIPTS_DIR, script_name)
            
            # Write file to disk
            with open(script_path, "wb") as buffer:
                shutil.copyfileobj(script_file.file, buffer)
            
            # Make the script executable
            os.chmod(script_path, 0o755)
        
        # Create schedule object
        schedule = ScheduleCreate(
            script_path=script_path,
            schedule_type=schedule_type,
            interval_seconds=interval_seconds,
            cron_expression=cron_expression,
            job_id=job_id
        )
        
        # Create the schedule
        result = await service.create_schedule(schedule)
        if isinstance(result.value, AppException):
            raise HTTPException(status_code=result.value.status_code, detail=result.value.message)
        
        return RedirectResponse(url="/scheduler/", status_code=303)
    
    except Exception as e:
        # If any error occurred and we uploaded a file, try to clean up
        if script_selection_method == "upload" and os.path.exists(script_path):
            try:
                os.remove(script_path)
            except:
                pass
        raise HTTPException(status_code=500, detail=str(e))