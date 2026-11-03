import json


def test_modele_ecrit(tmp_project):
    assert (tmp_project["models_dir"] / "model.joblib").exists()


def test_contrat_model_info(tmp_project):
    info = json.loads(
        (tmp_project["models_dir"] / "model_info.json").read_text(encoding="utf-8")
    )
    assert info["features"] == [
        "temperature_c",
        "vibration_mm_s",
        "load_pct",
        "runtime_hours",
    ]
    assert info["target"] == "failure"
    assert info["threshold"] == 0.3


def test_bat_la_baseline(tmp_project):
    r = tmp_project["results"]
    assert r["model"]["recall"] > r["baseline"]["recall"]
