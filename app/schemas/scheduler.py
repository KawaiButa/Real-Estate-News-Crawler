# app/schemas/scheduler.py
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ScheduleBase(BaseModel):
    script_path: str
    schedule_type: str  # "interval" or "cron"

class ScheduleCreate(ScheduleBase):
    interval_seconds: Optional[int] = None
    cron_expression: Optional[str] = None
    job_id: Optional[str] = None

class ScheduleResponse(ScheduleBase):
    job_id: str
    next_run_time: str

class ExecutionResult(BaseModel):
    timestamp: str
    stdout: str
    stderr: str
    return_code: int
