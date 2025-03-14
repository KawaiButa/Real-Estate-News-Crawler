# app/main.py
import os
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager

from app.services.schedule_service import scheduler
from app.api.routes import scheduler as scheduler_controller
from app.utils.constants import DATA_DIR, SCRIPTS_DIR
from app.utils.exceptions import AppExceptionCase
from app.models.scheduler import Base
from app.crud.scheduler_crud import async_session, engine

# Define base directories


# Ensure directories exist
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(SCRIPTS_DIR, exist_ok=True)


# Dependency to get DB session
async def get_db():
    async with async_session() as session:
        yield session


# Lifespan context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create database tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Start scheduler
    scheduler.start()

    yield

    # Shutdown scheduler
    scheduler.shutdown()


# Create FastAPI app
app = FastAPI(title="FastAPI Shell Script Scheduler", lifespan=lifespan)

# Mount static files
app.mount("/static", StaticFiles(directory="app/statics"), name="static")

# Register exception handler
@app.exception_handler(AppExceptionCase)
async def app_exception_handler(request: Request, exc: AppExceptionCase):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})


# Include routers
app.include_router(scheduler_controller.router)


# Redirect root to scheduler dashboard
@app.get("/")
async def redirect_to_scheduler():
    from fastapi.responses import RedirectResponse

    return RedirectResponse(url="/scheduler/")
