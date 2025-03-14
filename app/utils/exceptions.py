# app/utils/exceptions.py
class AppExceptionCase(Exception):
    def __init__(self, status_code: int = 500, message: str = ""):
        self.status_code = status_code
        self.message = message

class AppException:
    class ScriptNotFound(AppExceptionCase):
        def __init__(self):
            super().__init__(status_code=404, message="Script file not found")
    
    class JobNotFound(AppExceptionCase):
        def __init__(self):
            super().__init__(status_code=404, message="Schedule not found")
    
    class JobAlreadyExists(AppExceptionCase):
        def __init__(self):
            super().__init__(status_code=409, message="Job already exists")
    
    class MissingIntervalSeconds(AppExceptionCase):
        def __init__(self):
            super().__init__(status_code=400, message="interval_seconds is required for interval schedule type")
    
    class MissingCronExpression(AppExceptionCase):
        def __init__(self):
            super().__init__(status_code=400, message="cron_expression is required for cron schedule type")
    
    class InvalidScheduleType(AppExceptionCase):
        def __init__(self):
            super().__init__(status_code=400, message="schedule_type must be 'interval' or 'cron'")
    
    class NoExecutionHistory(AppExceptionCase):
        def __init__(self):
            super().__init__(status_code=404, message="No execution history found for this job")
    
    class UnexpectedError(AppExceptionCase):
        def __init__(self, message: str = "An unexpected error occurred"):
            super().__init__(status_code=500, message=message)
