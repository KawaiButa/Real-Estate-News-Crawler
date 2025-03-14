# app/models/scheduler.py
from sqlalchemy import Column, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class ScheduleDB(Base):
    __tablename__ = "schedules"
    
    job_id = Column(String, primary_key=True, index=True)
    script_path = Column(String, nullable=False)
    schedule_type = Column(String, nullable=False)  # "interval" or "cron"
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
