from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

# 1. DATABASE CONFIGURATION
# This points to the file 'synq.db' in your project folder.
# It acts as the central storage for:
# - Athlete Profiles (UUIDs)
# - Chest Strap Logs (Integers)
# - Xeno LLM History
SQLALCHEMY_DATABASE_URL = "sqlite:///./synq.db"

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