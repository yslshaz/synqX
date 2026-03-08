from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict

import joblib
import numpy as np
import pandas as pd
from flask import Flask, jsonify, render_template, request, render_template_string
from flask_sqlalchemy import SQLAlchemy
import os

def _ensure_numpy_core_aliases() -> None:
    """
    Compatibility shim: some pickles created with NumPy 2.x may reference 'numpy._core'.
    If you run this on NumPy 1.x, unpickling can fail with:
        ModuleNotFoundError: No module named 'numpy._core'
    This maps the expected modules to NumPy 1.x equivalents.
    """
    import numpy.core as npcore

    # Base alias
    sys.modules.setdefault("numpy._core", npcore)

    # Common submodules that may be referenced by pickled objects
    submods = [
        "_multiarray_umath",
        "multiarray",
        "umath",
        "numeric",
        "fromnumeric",
        "shape_base",
        "overrides",
        "_add_newdocs",
        "_add_newdocs_scalars",
    ]
    for sm in submods:
        try:
            sys.modules.setdefault(f"numpy._core.{sm}", __import__(f"numpy.core.{sm}", fromlist=["*"]))
        except Exception:
            # If a submodule doesn't exist in this NumPy build, ignore it
            pass


def load_model(model_path: Path):
    _ensure_numpy_core_aliases()
    return joblib.load(model_path)


HERE = Path(__file__).resolve().parent
MODEL_PATH = Path(__file__).resolve().parent / "predictor.pkl"
if not MODEL_PATH.exists():
    # allow running with the mounted path in environments like ChatGPT sandbox
    alt = Path("/mnt/data/predictor.pkl")
    if alt.exists():
        MODEL_PATH = alt

model = load_model(MODEL_PATH)

# Prefer feature names embedded in the model (scikit-learn >= 1.0)
FEATURES = list(getattr(model, "feature_names_in_", []))
if not FEATURES:
    # Fallback: if the model doesn't have feature_names_in_, you must fill this manually.
    FEATURES = ["Heart_Rate", "Body_Temperature", "Blood_Oxygen", "Unnamed: 3",
                "Heart_Rate_Body_Temp", "Oxygen_Heart_Rate_Ratio"]

CLASSES = list(getattr(model, "classes_", []))



app = Flask(__name__)

@app.route("/")
def welcome():
    return render_template("welcome.html")

@app.route("/athleteprofile")
def athleteprofile():
    return render_template("athleteprofile.html")

@app.route("/athletes")
def athletes():
    return render_template("athletes.html")

@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")

@app.route("/mlpage")
def mlpage():
    return render_template("mlpage.html")

@app.route("/onboarding")
def onboarding():
    return render_template("onboarding.html")

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///C:/Users/USER/Desktop/SYNQX/predictor_webapp_backend1.1/synq.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Import models so they are registered with Flask-SQLAlchemy
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))
from backend import models


# Ensure all tables exist (auto-create if missing) using SQLAlchemy Base
from backend.database import Base, engine
with app.app_context():
    Base.metadata.create_all(engine)

@app.route('/api/athletes', methods=['GET', 'POST'])
def athletes_endpoint():
    if request.method == 'GET':
        athletes = db.session.query(models.Athlete).all()
        result = []
        for a in athletes:
            # Fetch latest vital reading for this athlete
            latest_vital = (
                db.session.query(models.VitalReading)
                .filter_by(athlete_id=a.id)
                .order_by(models.VitalReading.timestamp.desc())
                .first()
            )
            heart_rate = latest_vital.heart_rate if latest_vital else None
            body_temperature = latest_vital.body_temperature if latest_vital else None
            blood_oxygen = latest_vital.blood_oxygen if latest_vital else None

            # ML prediction and DB linkage (Step 1)
            fatigue_status = None
            fatigue_assessment = None
            if latest_vital and heart_rate is not None and body_temperature is not None and blood_oxygen is not None:
                # Prepare features for ML model
                features = {}
                for f in FEATURES:
                    if f == "Heart_Rate":
                        features[f] = heart_rate
                    elif f == "Body_Temperature":
                        features[f] = body_temperature
                    elif f == "Blood_Oxygen":
                        features[f] = blood_oxygen
                    elif f == "Heart_Rate_Body_Temp":
                        features[f] = heart_rate * body_temperature
                    elif f == "Oxygen_Heart_Rate_Ratio":
                        features[f] = blood_oxygen / heart_rate if heart_rate else 0
                    else:
                        features[f] = 0
                # ML prediction
                X = pd.DataFrame([features], columns=FEATURES)
                pred = model.predict(X)[0]
                fatigue_status = str(pred)
                # Link to DB: create or update FatigueAssessment
                fatigue_assessment = (
                    db.session.query(models.FatigueAssessment)
                    .filter_by(athlete_id=a.id, vital_reading_id=latest_vital.id)
                    .first()
                )
                if fatigue_assessment:
                    fatigue_assessment.fatigue_status = fatigue_status
                    db.session.commit()
                else:
                    fatigue_assessment = models.FatigueAssessment(
                        athlete_id=a.id,
                        vital_reading_id=latest_vital.id,
                        fatigue_status=fatigue_status
                    )
                    db.session.add(fatigue_assessment)
                    db.session.commit()
            # If no valid vitals, do not create assessment

            # Step 2: Return fatigue_status and DB linkage
            result.append({
                'id': a.id,
                'name': a.name,
                'player_name': a.name,  # for frontend compatibility
                'player_id': a.id,      # for frontend compatibility
                'heart_rate': heart_rate,
                'body_temperature': body_temperature,
                'blood_oxygen': blood_oxygen,
                'fatigue_status': fatigue_assessment.fatigue_status if fatigue_assessment else None,
                'fatigue_assessment_id': fatigue_assessment.id if fatigue_assessment else None,
                'vital_reading_id': latest_vital.id if latest_vital else None,
                'notes': getattr(a, 'notes', None),
                'position': a.position,
                'height_cm': a.height_cm,
                'weight_kg': a.weight_kg,
                'age': a.age,
                'created_at': a.created_at.isoformat() if a.created_at else None
            })
        return jsonify(result)
    elif request.method == 'POST':
        data = request.get_json()
        athlete = models.Athlete(
            name=data.get('athlete_name'),
            position=None,
            height_cm=None,
            weight_kg=None,
            age=None
        )
        db.session.add(athlete)
        db.session.commit()
        db.session.refresh(athlete)

        # Create initial vital reading if vitals are provided
        heart_rate = data.get('heart_rate', 0)
        body_temperature = data.get('body_temperature', 0.0)
        blood_oxygen = data.get('blood_oxygen', 0)
        vital = models.VitalReading(
            athlete_id=athlete.id,
            heart_rate=heart_rate,
            body_temperature=body_temperature,
            blood_oxygen=blood_oxygen
        )
        db.session.add(vital)
        db.session.commit()

        return jsonify({
            'id': athlete.id,
            'name': athlete.name,
            'heart_rate': heart_rate,
            'body_temperature': body_temperature,
            'blood_oxygen': blood_oxygen,
            'position': athlete.position,
            'height_cm': athlete.height_cm,
            'weight_kg': athlete.weight_kg,
            'age': athlete.age,
            'created_at': athlete.created_at.isoformat() if athlete.created_at else None
        }), 201


@app.get("/schema")
def schema():
    return jsonify(
        {
            "features": FEATURES,
            "classes": CLASSES,
            "model_path": str(MODEL_PATH),
        }
    )


@app.post("/predict")
def predict():
    """
    Accepts JSON:
        {
            "Heart_Rate": 80,
            "Body_Temperature": 36.7,
            "Blood_Oxygen": 98,
            "Unnamed: 3": 1,
            "Heart_Rate_Body_Temp": 2936,
            "Oxygen_Heart_Rate_Ratio": 1.225
        }

    Returns:
        {
            "prediction": "Not Fatigued",
            "probabilities": {"Fatigued": 0.1, ...}
        }
    """
    payload: Dict[str, Any] = request.get_json(silent=True) or {}
    print("/predict received payload:", payload)

    # No longer map 'spo2' fields; only use 'Blood_Oxygen' and 'Oxygen_Heart_Rate_Ratio'
    mapped_payload = dict(payload)

    # Validate
    missing = [f for f in FEATURES if f not in mapped_payload]
    if missing:
        print("/predict missing features:", missing)
        print("/predict expected features:", FEATURES)
        return (
            jsonify(
                {
                    "error": "Missing required feature(s).",
                    "missing": missing,
                    "expected_features": FEATURES,
                }
            ),
            400,
        )

    # Build a 1-row DataFrame in the exact expected column order
    row = {}
    bad = {}
    missing = []
    for f in FEATURES:
        v = mapped_payload.get(f)
        # Treat empty string as missing
        if v is None or (isinstance(v, str) and v.strip() == ""):
            missing.append(f)
            continue
        try:
            # Convert to float; allows numeric strings too
            row[f] = float(v)
        except Exception:
            bad[f] = v

    if missing:
        print("/predict missing features (empty or not provided):", missing)
        return (
            jsonify(
                {
                    "error": "Missing required feature(s) (empty or not provided).",
                    "missing": missing,
                    "expected_features": FEATURES,
                }
            ),
            400,
        )

    if bad:
        return (
            jsonify(
                {
                    "error": "Some features are not numeric.",
                    "bad": bad,
                }
            ),
            400,
        )

    X = pd.DataFrame([row], columns=FEATURES)

    pred = model.predict(X)[0]
    result: Dict[str, Any] = {"prediction": str(pred)}

    if hasattr(model, "predict_proba"):
        probs = model.predict_proba(X)[0]
        result["probabilities"] = {str(c): float(p) for c, p in zip(CLASSES, probs)}

    return jsonify(result)

if __name__ == "__main__":
    # http://127.0.0.1:5000
    app.run(host="0.0.0.0", port=5000, debug=True)

@app.route('/api/live_vitals', methods=['POST'])
def receive_live_vitals():
    """
    Endpoint for the Coospo H6 hardware script.
    Receives averaged heart rate every 3 minutes.
    Accepts: {
        "athlete_id": str,
        "bpm": int,           # Heart Rate
        "hrv": float (optional),
        "rmssd": float (optional)
    }
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data received"}), 400

    try:
        athlete_id = str(data.get('athlete_id', '1'))
        heart_rate = data.get('bpm') or data.get('heart_rate')
        hrv = data.get('hrv')
        rmssd = data.get('rmssd')

        # Store all available fields, defaulting temp/oxygen to 0 for pilot
        new_reading = models.VitalReading(
            athlete_id=athlete_id,
            heart_rate=heart_rate,
            hrv=hrv,
            rmssd=rmssd,
            body_temperature=0.0,
            blood_oxygen=0
        )
        db.session.add(new_reading)
        db.session.commit()

        print(f"Successfully logged {heart_rate} BPM for Athlete {athlete_id}")
        return jsonify({"status": "success", "message": "Vitals logged to vital_readings"}), 201

    except Exception as e:
        db.session.rollback()
        print(f"Error logging vitals: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500