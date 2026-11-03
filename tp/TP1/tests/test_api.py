VALID = {
    "temperature_c": 60.0,
    "vibration_mm_s": 2.0,
    "load_pct": 50.0,
    "runtime_hours": 5000,
}


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok", "model_loaded": True}


def test_releve_normal_200(client):
    r = client.post("/v1/predict", json=VALID)
    assert r.status_code == 200
    body = r.json()
    assert 0 <= body["failure_probability"] <= 1
    assert isinstance(body["alert"], bool)


def test_alerte_coherente_avec_le_seuil(client):
    body = client.post(
        "/v1/predict", json={**VALID, "temperature_c": 105, "vibration_mm_s": 12}
    ).json()
    assert body["alert"] == (body["failure_probability"] >= 0.3)


def test_500_degres_refuse(client):
    assert (
        client.post("/v1/predict", json={**VALID, "temperature_c": 500}).status_code
        == 422
    )


def test_champ_inconnu_refuse(client):
    assert client.post("/v1/predict", json={**VALID, "pression": 3}).status_code == 422


def test_route_inconnue_404(client):
    assert client.post("/v1/predcit", json=VALID).status_code == 404


def test_modele_absent_503(client_sans_modele):
    assert client_sans_modele.post("/v1/predict", json=VALID).status_code == 503
