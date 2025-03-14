# app/utils/service_result.py
from typing import Any, Generic, TypeVar, Union
from app.utils.exceptions import AppExceptionCase
from app.schemas.scheduler import ScheduleCreate, ScheduleResponse

T = TypeVar('T')

class ServiceResult(Generic[T]):
    def __init__(self, value: Union[T, AppExceptionCase]):
        self.value = value

def handle_result(result: ServiceResult) -> ScheduleResponse:
    """Handle service result and return appropriate response or raise exception"""
    if isinstance(result.value, AppExceptionCase):
        from fastapi import HTTPException
        raise HTTPException(
            status_code=result.value.status_code,
            detail=result.value.message
        )
    return result.value
