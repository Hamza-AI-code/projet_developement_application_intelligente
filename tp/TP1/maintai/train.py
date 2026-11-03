"""Entraîne le modèle, écrit models/model.joblib et models/model_info.json (le contrat)."""

import json

import joblib
from sklearn.dummy import DummyClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, precision_score, recall_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from maintai import config
from maintai.data import load_data, split


def evaluate(model, X_test, y_test) -> dict:
    proba = model.predict_proba(X_test)[:, 1]
    pred = (proba >= config.THRESHOLD).astype(int)
    return {
        "accuracy": round(accuracy_score(y_test, pred), 3),
        "recall": round(recall_score(y_test, pred, zero_division=0), 3),
        "precision": round(precision_score(y_test, pred, zero_division=0), 3),
    }


def train(data_path=None, models_dir=None) -> dict:
    models_dir = models_dir or config.MODELS_DIR
    models_dir.mkdir(parents=True, exist_ok=True)
    X_train, X_test, y_train, y_test = split(load_data(data_path))

    baseline = DummyClassifier(strategy="most_frequent").fit(X_train, y_train)
    model = make_pipeline(StandardScaler(), LogisticRegression(max_iter=1000))
    model.fit(X_train, y_train)

    results = {
        "baseline": evaluate(baseline, X_test, y_test),
        "model": evaluate(model, X_test, y_test),
    }
    joblib.dump(model, models_dir / "model.joblib")
    info = {
        "features": config.FEATURES,
        "target": config.TARGET,
        "threshold": config.THRESHOLD,
        "model": "LogisticRegression",
        "metrics": results,
    }
    (models_dir / "model_info.json").write_text(
        json.dumps(info, indent=2), encoding="utf-8"
    )
    return results


def main() -> None:
    results = train()
    print(f"{'Modèle':<22}{'Accuracy':>10}{'Rappel':>10}{'Précision':>11}")
    for name, m in results.items():
        print(f"{name:<22}{m['accuracy']:>10}{m['recall']:>10}{m['precision']:>11}")
    print(f"Modèle écrit dans {config.MODEL_PATH}")


if __name__ == "__main__":
    main()
