# app/crud/scheduler_crud.py
import os
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import Optional, List

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.models.scheduler import ScheduleDB
from app.utils.constants import DATABASE_URL
engine = create_async_engine(DATABASE_URL)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class SchedulerCRUD:
    def __init__(self):
        self.db = async_session

    async def create_schedule(
        self, job_id: str, script_path: str, schedule_type: str
    ) -> ScheduleDB:
        """Create a new schedule record in the database"""
        db_schedule = ScheduleDB(
            job_id=job_id, script_path=script_path, schedule_type=schedule_type
        )
        self.db.add(db_schedule)
        await self.db.commit()
        await self.db.refresh(db_schedule)
        return db_schedule

    async def get_schedule(self, job_id: str) -> Optional[ScheduleDB]:
        """Get a schedule record by job_id"""
        result = await self.db.execute(
            select(ScheduleDB).where(ScheduleDB.job_id == job_id)
        )
        return result.scalars().first()

    async def list_schedules(self) -> List[ScheduleDB]:
        """List all schedule records"""
        result = await self.db.execute(select(ScheduleDB))
        return result.scalars().all()

    async def delete_schedule(self, job_id: str) -> bool:
        """Delete a schedule record"""
        db_schedule = await self.get_schedule(job_id)
        if not db_schedule:
            return False

        await self.db.delete(db_schedule)
        await self.db.commit()
        return True
