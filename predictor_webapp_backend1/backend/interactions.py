from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

# --- 1. ATHLETE SCHEMAS ---
class AthleteBase(BaseModel):
    name: str
    position: Optional[str] = None
    height_cm: Optional[float] = None
    weight_kg: Optional[float] = None
    age: Optional[int] = None

class AthleteCreate(AthleteBase):
    pass

class AthleteResponse(AthleteBase):
    id: str
    created_at: datetime
    
    class Config:
        from_attributes = True


# --- 2. METRIC SCHEMAS (Strap & AI Interaction) ---

# INPUT: The RAW data coming from the CooSpo Chest Strap
class MetricInput(BaseModel):
    athlete_id: str
    bpm: int           # Heart Rate
    hrv: float         # General HRV
    rmssd: float       # Raw ms value (The input for SYNQ)

# OUTPUT: The processed data returned to the Dashboard
class MetricResponse(MetricInput):
    id: int
    date: datetime
    
    # This is the NEW field calculated by SYNQ AI
    fatigue_status: str  # "Normal", "Moderate", "Fatigued"
    
    class Config:
        from_attributes = True


# --- 3. WORKOUT SCHEMAS (Checklist Logic) ---

class WorkoutLog(BaseModel):
    athlete_id: str
    session_type: str                  # "Gym" or "Cardio"
    
    exercises_planned: List[str]       # e.g. ["Squat", "Bench"]
    exercises_completed: List[str]     # e.g. ["Squat"]
    
    planned_load_score: float          # The expected load from Xeno

class WorkoutResponse(BaseModel):
    status: str
    compliance_score: str              # e.g. "50%"
    actual_load: float                 # The calculated load