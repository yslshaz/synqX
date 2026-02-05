import uuid
import enum
from datetime import datetime
from typing import List, Optional
from sqlalchemy import String, Integer, Float, ForeignKey, DateTime, JSON, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database import Base

# Helper function to generate UUIDs
def generate_uuid():
    return str(uuid.uuid4())

# 1. ATHLETE TABLE (Profile)
class Athlete(Base):
    __tablename__ = "athletes"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=generate_uuid
    )

    name: Mapped[str] = mapped_column(String(100))
    position: Mapped[Optional[str]] = mapped_column(String(50))
    height_cm: Mapped[Optional[float]] = mapped_column(Float)
    weight_kg: Mapped[Optional[float]] = mapped_column(Float)
    age: Mapped[Optional[int]] = mapped_column(Integer)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow
    )

    # Relationships
    training_sessions: Mapped[List["TrainingSession"]] = relationship(
        back_populates="athlete"
    )

    goals: Mapped[List["Goal"]] = relationship(
        back_populates="athlete"
    )

    baselines: Mapped[List["Baseline"]] = relationship(
        back_populates="athlete"
    )

    vital_readings: Mapped[List["VitalReading"]] = relationship(
        back_populates="athlete",
        cascade="all, delete-orphan"
    )

    fatigue_assessments: Mapped[List["FatigueAssessment"]] = relationship(
        back_populates="athlete",
        cascade="all, delete-orphan"
    )


class SessionType(enum.Enum):
    gym = "gym"
    cardio = "cardio"
    leg_day = "leg_day"
    rest = "rest"


class EffortLevel(enum.Enum):
    very_easy = 1
    easy = 2
    moderate = 3
    hard = 4
    max = 5


# 3. TRAINING SESSION (Checklist & History)
class TrainingSession(Base):
    __tablename__ = "training_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    athlete_id: Mapped[str] = mapped_column(ForeignKey("athletes.id"))

    timestamp: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow
    )

    # --- SESSION MEANING ---
    session_type: Mapped[SessionType] = mapped_column(Enum(SessionType))
    completed: Mapped[bool] = mapped_column(default=False)
    went_all_out: Mapped[bool] = mapped_column(default=False)
    perceived_effort: Mapped[Optional[EffortLevel]] = mapped_column(
        Enum(EffortLevel)
    )

    # --- CHECKLIST ---
    exercises_planned: Mapped[Optional[list]] = mapped_column(JSON)
    exercises_completed: Mapped[Optional[list]] = mapped_column(JSON)

    # --- LOAD METRICS ---
    planned_load: Mapped[float] = mapped_column(Float, default=0.0)
    actual_load: Mapped[float] = mapped_column(Float, default=0.0)
    compliance_score: Mapped[float] = mapped_column(Float, default=0.0)

    athlete: Mapped["Athlete"] = relationship(back_populates="training_sessions")


class GoalType(enum.Enum):
    lean = "lean"
    strength = "strength"
    weight_loss = "weight_loss"


# 4. GOAL TABLE (Context for Xeno LLM)
class Goal(Base):
    __tablename__ = "goals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    athlete_id: Mapped[str] = mapped_column(ForeignKey("athletes.id"))
    
    goal_type: Mapped[GoalType] = mapped_column(Enum(GoalType)) # "Explosiveness"
    target_date: Mapped[Optional[datetime]] = mapped_column(DateTime)
    
    athlete: Mapped["Athlete"] = relationship(back_populates="goals")


# 5. BASELINE TABLE (The Engine's Reference)
class Baseline(Base):
    __tablename__ = "baselines"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    athlete_id: Mapped[str] = mapped_column(ForeignKey("athletes.id"))
    
    metric_name: Mapped[str] = mapped_column(String(50)) # e.g. "rmssd"
    avg_7_day: Mapped[float] = mapped_column(Float)
    
    athlete: Mapped["Athlete"] = relationship(back_populates="baselines")

class VitalReading(Base):
    __tablename__ = "vital_readings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    athlete_id: Mapped[str] = mapped_column(ForeignKey("athletes.id"))

    timestamp: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow
    )

    # --- RAW SENSOR DATA ---
    heart_rate: Mapped[int] = mapped_column(Integer)
    hrv: Mapped[Optional[float]] = mapped_column(Float)
    rmssd: Mapped[Optional[float]] = mapped_column(Float)

    body_temperature: Mapped[Optional[float]] = mapped_column(Float)
    spo2: Mapped[Optional[int]] = mapped_column(Integer)

    athlete: Mapped["Athlete"] = relationship(back_populates="vital_readings")

class FatigueAssessment(Base):
    __tablename__ = "fatigue_assessments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    athlete_id: Mapped[str] = mapped_column(
        ForeignKey("athletes.id"), nullable=False
    )

    vital_reading_id: Mapped[int] = mapped_column(
        ForeignKey("vital_readings.id"), nullable=False
    )

    fatigue_status: Mapped[str] = mapped_column(String(20))
    confidence: Mapped[Optional[float]] = mapped_column(Float)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow
    )

    # ✅ Correct relationships
    athlete: Mapped["Athlete"] = relationship(back_populates="fatigue_assessments")
    vital_reading: Mapped["VitalReading"] = relationship()


