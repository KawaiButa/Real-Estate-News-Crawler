# app/services/scheduler_service.py
import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.jobstores.base import ConflictingIdError

import os
import logging
import subprocess
from datetime import datetime
from typing import Dict, List

from app.schemas.scheduler import ScheduleCreate, ScheduleResponse, ExecutionResult
from app.utils.constants import DATA_DIR, JOB_DATABASE_URL
from app.utils.service_results import ServiceResult
from app.utils.exceptions import AppException
from app.crud.scheduler_crud import SchedulerCRUD

execution_history: Dict[str, List[ExecutionResult]] = {}
job_stories = {"default": SQLAlchemyJobStore(url=JOB_DATABASE_URL)}

# Create scheduler
scheduler = AsyncIOScheduler(job_stories=job_stories)


class SchedulerService:
    def __init__(self, scheduler: AsyncIOScheduler, crud: SchedulerCRUD):
        self.scheduler = scheduler
        self.crud = crud
        self.logger = logging.getLogger(__name__)

    async def run_shell_script(self, script_path: str, job_id: str) -> ExecutionResult:
        """Execute a shell script and return the results"""
        self.logger.info(f"Executing script: {script_path}")

        if not os.path.exists(script_path):
            self.logger.error(f"Script not found: {script_path}")
            return ExecutionResult(
                timestamp=datetime.now().isoformat(),
                stdout="",
                stderr="Script file not found",
                return_code=1,
            )

        try:
            # Execute the shell script
            result = subprocess.run(
                ["sh", script_path], capture_output=True, text=True, check=False
            )

            execution_result = ExecutionResult(
                timestamp=datetime.now().isoformat(),
                stdout=result.stdout,
                stderr=result.stderr,
                return_code=result.returncode,
            )

            # Store execution result in history
            if job_id not in execution_history:
                execution_history[job_id] = []
            execution_history[job_id].append(execution_result)
            # Keep only the last 100 executions
            if len(execution_history[job_id]) > 100:
                execution_history[job_id] = execution_history[job_id][-100:]

            self.logger.info(
                f"Script execution completed with code: {result.returncode}"
            )
            if result.returncode != 0:
                self.logger.warning(
                    f"Script returned non-zero exit code: {result.stderr}"
                )

            return execution_result

        except Exception as e:
            self.logger.error(f"Error executing script: {str(e)}")
            return ExecutionResult(
                timestamp=datetime.now().isoformat(),
                stdout="",
                stderr=str(e),
                return_code=1,
            )

    async def create_schedule(self, schedule: ScheduleCreate) -> ServiceResult:
        """Create a new scheduled job"""
        # Validate the script path
        if not os.path.exists(schedule.script_path):
            return ServiceResult(AppException.ScriptNotFound())

        # Generate job ID if not provided
        job_id = schedule.job_id or f"job_{datetime.now().strftime('%Y%m%d%H%M%S')}"

        # Initialize execution history for this job
        if job_id not in execution_history:
            execution_history[job_id] = []

        # Create a wrapper function to run the script and store result
        async def job_function() -> ServiceResult[ScheduleResponse]:
            result = await asyncio.to_thread(
                self.run_shell_script, schedule.script_path, job_id
            )

        try:
            # Configure trigger based on schedule type
            if schedule.schedule_type == "interval":
                if not schedule.interval_seconds:
                    return ServiceResult(AppException.MissingIntervalSeconds())

                trigger = IntervalTrigger(seconds=schedule.interval_seconds)

            elif schedule.schedule_type == "cron":
                if not schedule.cron_expression:
                    return ServiceResult(AppException.MissingCronExpression())

                # Parse cron expression
                trigger = CronTrigger.from_crontab(schedule.cron_expression)

            else:
                return ServiceResult(AppException.InvalidScheduleType())

            # Add job to scheduler
            job = self.scheduler.add_job(
                job_function, trigger=trigger, id=job_id, replace_existing=True
            )

            # Store job in database
            await self.crud.create_schedule(
                job_id, schedule.script_path, schedule.schedule_type
            )

            return ServiceResult(
                ScheduleResponse(
                    job_id=job_id,
                    script_path=schedule.script_path,
                    schedule_type=schedule.schedule_type,
                    next_run_time=(
                        job.next_run_time.isoformat()
                        if job.next_run_time
                        else "Not scheduled"
                    ),
                )
            )

        except ConflictingIdError:
            self.logger.warning(f"Job {job_id} already exists")
            return ServiceResult(AppException.JobAlreadyExists())
        except Exception as e:
            self.logger.error(f"Error creating schedule: {str(e)}")
            return ServiceResult(AppException.UnexpectedError(str(e)))

    async def list_schedules(self) -> ServiceResult:
        """List all scheduled jobs"""
        try:
            schedules = []
            for job in self.scheduler.get_jobs():
                schedule_type = (
                    "interval" if isinstance(job.trigger, IntervalTrigger) else "cron"
                )
                schedules.append(
                    ScheduleResponse(
                        job_id=job.id,
                        script_path=(
                            getattr(job.args[0], "__self__", "Unknown").script_path
                            if job.args
                            else "Unknown"
                        ),
                        schedule_type=schedule_type,
                        next_run_time=(
                            job.next_run_time.isoformat()
                            if job.next_run_time
                            else "Not scheduled"
                        ),
                    )
                )
            return ServiceResult(schedules)
        except Exception as e:
            self.logger.error(f"Error listing schedules: {str(e)}")
            return ServiceResult(AppException.UnexpectedError(str(e)))

    async def get_schedule(self, job_id: str) -> ServiceResult:
        """Get details of a specific scheduled job"""
        job = self.scheduler.get_job(job_id)
        if not job:
            return ServiceResult(AppException.JobNotFound())

        schedule_type = (
            "interval" if isinstance(job.trigger, IntervalTrigger) else "cron"
        )
        return ServiceResult(
            ScheduleResponse(
                job_id=job.id,
                script_path=(
                    getattr(job.args[0], "__self__", "Unknown").script_path
                    if job.args
                    else "Unknown"
                ),
                schedule_type=schedule_type,
                next_run_time=(
                    job.next_run_time.isoformat()
                    if job.next_run_time
                    else "Not scheduled"
                ),
            )
        )

    async def delete_schedule(self, job_id: str) -> ServiceResult:
        """Delete a scheduled job"""
        job = self.scheduler.get_job(job_id)
        if not job:
            return ServiceResult(AppException.JobNotFound())

        try:
            self.scheduler.remove_job(job_id)
            await self.crud.delete_schedule(job_id)
            return ServiceResult(
                {"status": "success", "message": f"Job {job_id} removed"}
            )
        except Exception as e:
            self.logger.error(f"Error deleting schedule: {str(e)}")
            return ServiceResult(AppException.UnexpectedError(str(e)))

    async def execute_job_now(self, job_id: str) -> ServiceResult:
        """Trigger immediate execution of a scheduled job"""
        job = self.scheduler.get_job(job_id)
        if not job:
            return ServiceResult(AppException.JobNotFound())

        try:
            # Extract script path from database
            schedule_data = await self.crud.get_schedule(job_id)
            if not schedule_data:
                return ServiceResult(AppException.JobNotFound())

            script_path = schedule_data.script_path

            # Run script and get result
            result = await self.run_shell_script(script_path, job_id)

            return ServiceResult(result)
        except Exception as e:
            self.logger.error(f"Error executing job: {str(e)}")
            return ServiceResult(AppException.UnexpectedError(str(e)))

    async def get_execution_history(self, job_id: str) -> ServiceResult:
        """Get execution history for a specific job"""
        if job_id not in execution_history:
            return ServiceResult(AppException.NoExecutionHistory())

        return ServiceResult(execution_history[job_id])


def get_scheduler_service() -> SchedulerService:
    # Assume you have a global scheduler instance, e.g.:
    crud = SchedulerCRUD()  # or retrieve your SchedulerCRUD instance
    return SchedulerService(scheduler, crud)
