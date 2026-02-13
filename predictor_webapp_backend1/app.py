from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict

import joblib
import numpy as np
import pandas as pd
from flask import Flask, jsonify, render_template, request
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
# Configure Flask-SQLAlchemy to use the same SQLite DB as backend/database.py
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///synq.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Import models so they are registered with Flask-SQLAlchemy
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))
from backend import models

# Ensure all tables exist (auto-create if missing)
with app.app_context():
    db.create_all()


@app.get("/")
def index():
    return render_template("index.html")

@app.get("/mlpage")
def mlpage():
    return render_template("mlpage.html")

@app.get("/mlpage.html")
def mlpage_html():
    return render_template("mlpage.html")

@app.route('/api/athletes', methods=['GET', 'POST'])
def athletes_endpoint():
    if request.method == 'GET':
        athletes = db.session.query(models.Athlete).all()
        result = []
        for a in athletes:
            result.append({
                'athlete_id': a.id,
                'athlete_name': a.name,
                'heart_rate': getattr(a, 'heart_rate', None),
                'body_temperature': getattr(a, 'body_temperature', None),
                'blood_oxygen': getattr(a, 'blood_oxygen', None),
                'fatigue_status': getattr(a, 'fatigue_status', None),
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
        # Set extra fields if present
        for field in ['heart_rate', 'body_temperature', 'blood_oxygen', 'fatigue_status', 'notes']:
            if hasattr(athlete, field) and field in data:
                setattr(athlete, field, data[field])
        db.session.add(athlete)
        db.session.commit()
        db.session.refresh(athlete)
        return jsonify({
            'athlete_id': athlete.id,
            'athlete_name': athlete.name,
            'heart_rate': getattr(athlete, 'heart_rate', None),
            'body_temperature': getattr(athlete, 'body_temperature', None),
            'blood_oxygen': getattr(athlete, 'blood_oxygen', None),
            'fatigue_status': getattr(athlete, 'fatigue_status', None),
            'notes': getattr(athlete, 'notes', None),
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
      { "Heart_Rate": 80, "Body_Temperature": 36.7, ... }

    Returns:
      { "prediction": "Not Fatigued", "probabilities": {"Fatigued": 0.1, ...} }
    """
    payload: Dict[str, Any] = request.get_json(silent=True) or {}

    # Validate
    missing = [f for f in FEATURES if f not in payload]
    if missing:
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
    for f in FEATURES:
        v = payload.get(f)
        try:
            # Convert to float; allows numeric strings too
            row[f] = float(v)
        except Exception:
            bad[f] = v

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