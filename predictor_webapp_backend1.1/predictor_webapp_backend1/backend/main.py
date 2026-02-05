from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import joblib
import pandas as pd
from pathlib import Path

# Import our custom modules (The Layers we just built)
from database import get_db, engine
import models
import schemas

# Initialize the App
app = FastAPI(title="SYNQ API", version="1.0.0")

# --- 0. AI BRAIN LOADING ---
HERE = Path(__file__).resolve().parent
MODEL_PATH = HERE / "predictor.pkl"

try:
    rf_model = joblib.load(MODEL_PATH)
    print("✅ AI Brain Loaded Successfully")
except:
    print("⚠️ Warning: predictor.pkl not found. AI predictions will be mocked.")
    rf_model = None


# --- 1. PLAYER ENDPOINTS (REST API) ---

@app.post("/players/", response_model=schemas.AthleteResponse)
def create_player(player: schemas.AthleteCreate, db: Session = Depends(get_db)):
    """
    CREATE a new player.
    Generates UUID automatically in models.py.
    """
    db_player = models.Athlete(**player.dict())
    db.add(db_player)
    db.commit()
    db.refresh(db_player)
    return db_player

@app.get("/players/", response_model=List[schemas.AthleteResponse])
def get_players(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    RETRIEVE the list of all players.
    Used by Dashboard to populate the list.
    """
    return db.query(models.Athlete).offset(skip).limit(limit).all()


# --- 2. FATIGUE ENDPOINT (The Strap Connection) ---

@app.post("/predict_fatigue/", response_model=schemas.MetricResponse)
def log_vitals(data: schemas.MetricInput, db: Session = Depends(get_db)):
    """
    Step 1: Receive Raw Data (BPM, HRV, RMSSD)
    Step 2: Run SYNQ AI Logic
    Step 3: Save Result to DB
    """
    
    # A. PREPARE DATA FOR AI
    # We map the strap inputs to what the model expects
    input_df = pd.DataFrame([{
        'Heart_Rate': data.bpm,         
        'Body_Temperature': 37.0,       # Default
        'Blood_Oxygen': 98,             # Default
        'Unnamed: 3': 1                 # Hidden bias feature
    }])

    # B. RUN SYNQ AI
    fatigue_result = "Normal" # Default safe state
    
    if rf_model:
        try:
            # The AI analyzes the dataframe
            prediction = rf_model.predict(input_df)[0]
            fatigue_result = str(prediction)
        except Exception as e:
            print(f"AI Error: {e}")
            fatigue_result = "AI_Error"

    # C. SAVE TO DATABASE
    new_metric = models.DailyMetric(
        athlete_id=data.athlete_id,
        bpm=data.bpm,
        hrv=data.hrv,
        rmssd=data.rmssd,
        fatigue_status=fatigue_result
    )
    
    db.add(new_metric)
    db.commit()
    db.refresh(new_metric)
    
    return new_metric


# --- 3. WORKOUT ENDPOINT (The Checklist Logic) ---

@app.post("/log_workout/", response_model=schemas.WorkoutResponse)
def log_workout_checklist(log: schemas.WorkoutLog, db: Session = Depends(get_db)):
    """
    Calculates Compliance Score based on checklist.
    """
    # Calculate Completion %
    total_planned = len(log.exercises_planned)
    total_done = len(log.exercises_completed)
    
    if total_planned == 0:
        compliance = 0.0
    else:
        compliance = total_done / total_planned
        
    actual_load_score = log.planned_load_score * compliance
    
    new_session = models.TrainingSession(
        athlete_id=log.athlete_id,
        session_type=log.session_type,
        exercises_planned=log.exercises_planned,
        exercises_completed=log.exercises_completed,
        planned_load=log.planned_load_score,
        actual_load=actual_load_score,
        compliance_score=compliance
    )
    
    db.add(new_session)
    db.commit()
    db.refresh(new_session)
    
    return {
        "status": "Logged", 
        "compliance_score": f"{compliance*100:.1f}%", 
        "actual_load": actual_load_score
    }