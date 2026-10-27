# Compte rendu · TP1 : une API de prédiction pour MaintAI

**Groupe :** G2  ·  **Membres :** Hamza ZAIDI  ·  **Date :** 27/10/2026

---

## 1. Mise en place

Dernière ligne de `python -m pytest`, juste après la mise en place (rien n'est encore écrit) :

```
======= 3 failed, 10 passed, 1 warning ========
```

Les 4 tests de `tests/test_api.py` qui passent déjà : `test_health`, `test_out_of_range_value_is_rejected`, `test_missing_field_is_rejected` et `test_openapi_documents_predict`.

Les deux tests qui attendent un code 422 passent pour une mauvaise raison. Au début, `SensorReading` n'a aucun champ, et `extra="forbid"` refuse tous les champs inconnus. Donc tout relevé est refusé avec un 422, même un relevé correct. Le test passe, mais pas parce que la température est trop grande ou qu'un champ manque.

## 2. Le schéma d'entrée (`maintai/api/schemas.py`)

| Variable | Type | Minimum (`ge`) | Maximum (`le`) | Justification physique (pas le min / max des données) |
|---|---|---|---|---|
| `temperature_c` | float | -40 | 150 | Une machine peut être très froide à l'arrêt en hiver. Au-delà de 150 °C, c'est plutôt une erreur de capteur. |
| `vibration_mm_s` | float | 0 | 50 | Une vibration ne peut pas être négative. 50 mm/s est déjà très élevé pour une machine, donc au-delà on suspecte le capteur. |
| `load_pct` | float | 0 | 100 | C'est un pourcentage de la charge nominale. |
| `runtime_hours` | float | 0 | 100000 | Les heures ne peuvent pas être négatives. 100 000 h font environ 11 ans de marche continue, plus que la vie d'une machine. |

Après avoir écrit `schemas.py` seul, `python -m pytest` donne :

```
FAILED tests/test_api.py::test_predict_returns_probability - NotImplementedError
FAILED tests/test_api.py::test_high_risk_reading_raises_alert - NotImplementedError
FAILED tests/test_api.py::test_503_when_model_missing - NotImplementedError
======= 3 failed, 10 passed, 1 warning ========
```

C'est un bon signe : il y a toujours 3 échecs, mais l'erreur est maintenant `NotImplementedError`. Cela veut dire que les relevés valides passent la validation et arrivent jusqu'à `predict()`, qui n'est pas encore écrite. Le schéma fonctionne donc.

Je n'ai pas pris le min / max des données d'entraînement. Une machine plus chaude ou qui vibre plus que dans les données serait refusée, alors que c'est justement elle qui risque de tomber en panne.

## 3. La fonction `predict()` (`maintai/api/main.py`)

Mon code :

```python
predictor = state.get("predictor")
if predictor is None:
    raise HTTPException(status_code=503, detail="Modèle non chargé")
return PredictionOut(**predictor.predict(reading.model_dump()))
```

Pourquoi répondre **503** et pas 500 quand le modèle manque ?

Un 500 veut dire qu'il y a un bug dans le serveur. Ici, le code est correct : c'est le modèle qui n'est pas disponible (par exemple parce que `python -m maintai.train` n'a pas été lancé). Le 503 veut dire « service indisponible pour le moment », donc le client sait qu'il peut réessayer plus tard.

Pourquoi le modèle est-il chargé **une seule fois**, au démarrage, et pas à chaque requête ?

Lire le fichier du modèle prend du temps. Si on le faisait à chaque requête, l'API serait lente. On le charge une fois au démarrage, on le garde en mémoire, et on peut aussi voir tout de suite si le modèle manque.

## 4. Les tests

Dernière ligne de `python -m pytest` à la fin du TP :

```
============ 13 passed, 1 warning in 2.50s ============
```

## 5. L'API en marche

| Requête | Code obtenu | Réponse (le corps JSON) |
|---|---|---|
| `GET /health` | 200 | `{"status": "ok", "model_loaded": true}` |
| `POST /v1/predict` avec `{"temperature_c": 72.5, "vibration_mm_s": 6.1, "load_pct": 85, "runtime_hours": 15000}` | 200 | `{"failure_probability": 0.9553, "alert": true, "threshold": 0.3, "model_version": "2026-10-27T21:30:00Z"}` |
| `POST /v1/predict` avec une température de 500 | 422 | `{"detail": [{"type": "less_than_equal", "loc": ["body", "temperature_c"], "msg": "Input should be less than or equal to 150", "input": 500, "ctx": {"le": 150.0}}]}` |
| `POST /v1/predicte` (faute de frappe dans l'adresse) | 404 | `{"detail": "Not Found"}` |

Dans `/docs`, où voit-on les bornes que j'ai choisies ?

En bas de la page, dans **Schemas**, en ouvrant `SensorReading`. Chaque champ affiche son `minimum` et son `maximum`.

## 6. Questions de compréhension

1. REST et FastAPI : quelle est la différence ?
   REST est une façon d'organiser une API (des URL, des méthodes comme GET et POST, des codes de statut). FastAPI est la bibliothèque Python qu'on utilise pour écrire une API qui suit ces règles.
2. Le schéma Pydantic sert à trois choses. Lesquelles ?
   Il vérifie les données reçues (et renvoie 422 si elles sont mauvaises), il donne à la fonction un objet Python déjà vérifié, et il génère la documentation dans `/docs`.
3. Dans `http://localhost:8000/v1/predict`, que désignent `localhost`, `8000` et `/v1/predict` ?
   `localhost` est ma propre machine, `8000` est le port où l'API écoute, et `/v1/predict` est la route définie dans le code Python.
4. Pourquoi `/v1` dans l'adresse ?
   C'est la version de l'API. Plus tard, on pourra créer une `/v2` sans casser les clients qui utilisent encore `/v1`.
5. Dans la commande `uvicorn maintai.api.main:app`, que désignent `maintai.api.main` et `app` ?
   `maintai.api.main` est le fichier `maintai/api/main.py`, écrit avec des points et sans `.py`. `app` est la variable de ce fichier qui contient l'application FastAPI.

## 7. Le rendu Git

- Lien de la pull request : à ajouter (lien de ma pull request)
- Le tag `tp1` existe sur GitHub : oui / non (à choisir)
- Qui a relu la pull request, et quel commentaire a-t-il laissé ?
  à ajouter

## 8. Ce qui reste flou

Je ne comprends pas encore très bien comment `lifespan` fonctionne avec le `yield` : je sais que le code avant le `yield` s'exécute au démarrage, mais pas bien comment l'API reste en marche entre les deux. Je ne sais pas non plus ce que vaut la prédiction quand une valeur est acceptée par le schéma mais très différente des données d'entraînement.
