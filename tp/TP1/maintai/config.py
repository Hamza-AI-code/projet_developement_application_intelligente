"""Réglages du projet : chemins, variables, seuil."""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = ROOT / "data" / "sensors.csv"
MODELS_DIR = ROOT / "models"
MODEL_PATH = MODELS_DIR / "model.joblib"
MODEL_INFO_PATH = MODELS_DIR / "model_info.json"

FEATURES = ["temperature_c", "vibration_mm_s", "load_pct", "runtime_hours"]
TARGET = "failure"
THRESHOLD = 0.3
SEED = 42
