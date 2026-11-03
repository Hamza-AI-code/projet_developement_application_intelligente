"""Charge le modèle une fois et prédit un relevé."""

import json

import joblib
import pandas as pd

from maintai import config


class Predictor:
    def __init__(self, models_dir=None):
        models_dir = models_dir or config.MODELS_DIR
        self.model = joblib.load(models_dir / "model.joblib")
        self.info = json.loads(
            (models_dir / "model_info.json").read_text(encoding="utf-8")
        )
        self.features = self.info["features"]
        self.threshold = self.info["threshold"]

    def predict(self, reading: dict) -> dict:
        X = pd.DataFrame([reading])[self.features]
        proba = float(self.model.predict_proba(X)[0, 1])
        return {
            "failure_probability": round(proba, 4),
            "alert": proba >= self.threshold,
        }


def load_predictor(models_dir=None):
    """Renvoie un Predictor, ou None si le modèle n'existe pas encore."""
    try:
        return Predictor(models_dir)
    except FileNotFoundError:
        return None
