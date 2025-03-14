import os


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
DATABASE_URL = f"sqlite+aiosqlite:///{os.path.join(DATA_DIR, 'scheduler.db')}"
JOB_DATABASE_URL = f"sqlite:///{os.path.join(DATA_DIR, 'jobs.sqlite')}"
SCRIPTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "scripts")
