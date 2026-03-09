from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

# 1. DATABASE CONFIGURATION
# Resolve the database path relative to this file so it works on any machine.
BASE_DIR = Path(__file__).resolve().parent.parent  # predictor_webapp_backend1/
SQLALCHEMY_DATABASE_URL = f"sqlite:///{BASE_DIR / 'synq.db'}"

# 2. THE ENGINE (The Connection Core)
# connect_args={"check_same_thread": False} is CRITICAL.
# It allows the Chest Strap (BLE) and the Web Dashboard to 
# access the database simultaneously without crashing.
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False}
)

# 3. THE SESSION FACTORY (The "Door Handle")
# Every time SYNQ AI or Xeno LLM needs to touch data, 
# they grab a fresh 'Session' from here.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 4. THE BASE CLASS (The Blueprint)
# All your tables (Athlete, DailyMetric, TrainingSession) 
# will inherit from this so the DB knows they exist.
class Base(DeclarativeBase):
    pass

# 5. DEPENDENCY INJECTION (The "Janitor")
# This helper function is used by FastAPI endpoints.
# It opens a connection for the request and guarantees it closes
# afterwards, keeping the database healthy.
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()