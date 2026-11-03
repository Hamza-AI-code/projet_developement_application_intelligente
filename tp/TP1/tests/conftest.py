"""Fixtures : un dossier temporaire avec des données, un modèle, et un client de test."""

import pytest
from fastapi.testclient import TestClient

from maintai import dataset, train
from maintai.api import main as api_main
from maintai.predict import load_predictor


@pytest.fixture(scope="session")
def tmp_project(tmp_path_factory):
    root = tmp_path_factory.mktemp("maintai")
    data_path = root / "sensors.csv"
    dataset.make_dataset().to_csv(data_path, index=False)
    models_dir = root / "models"
    results = train.train(data_path=data_path, models_dir=models_dir)
    return {"data_path": data_path, "models_dir": models_dir, "results": results}


@pytest.fixture
def client(tmp_project, monkeypatch):
    monkeypatch.setattr(
        api_main, "load_predictor", lambda: load_predictor(tmp_project["models_dir"])
    )
    with TestClient(api_main.app) as c:
        yield c


@pytest.fixture
def client_sans_modele(tmp_path, monkeypatch):
    monkeypatch.setattr(api_main, "load_predictor", lambda: load_predictor(tmp_path))
    with TestClient(api_main.app) as c:
        yield c
