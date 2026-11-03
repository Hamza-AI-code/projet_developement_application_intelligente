# Compte rendu · TP1 : une API de prédiction pour MaintAI

**Groupe :** G2  ·  **Membres :** Salma Chair, …  ·  **Date :** …

> Remplissez chaque partie dans ce fichier, puis rendez-le avec la pull request du TP1.
> Collez les sorties du terminal entre les lignes ``` (trois accents graves).

---

## 1. Mise en place

Dernière ligne de `python -m pytest`, juste après la mise en place (rien n'est encore écrit) :

```
3 failed, 10 passed
```

Dans `tests/test_api.py`, 4 tests sur 7 passent déjà alors que rien n'est écrit. Lesquels ? Pour les deux tests qui attendent un code 422, expliquez pourquoi ils passent « pour une mauvaise raison » (indice : regardez `extra="forbid"` dans `schemas.py`).

Les 4 tests qui passent déjà sont :

- le test de `GET /health`, car cette route est déjà écrite ;
- le test de la route inconnue, qui reçoit 404, car FastAPI gère tout seul les adresses qui n'existent pas ;
- les deux tests qui attendent **422** : la température de 500 °C et l'entrée invalide.

Les deux tests 422 passent pour une mauvaise raison. Au départ, `SensorReading` ne contient aucun champ (juste `pass`) et a `extra="forbid"` : tout champ qu'il ne connaît pas est refusé. Or, pour lui, **tous** les champs sont inconnus. Il refuse donc **tous** les relevés en 422, même un relevé parfaitement normal. Les tests obtiennent bien 422, mais pas parce que 500 °C dépasse une borne : aucune borne n'existe encore. Un test vert ne prouve rien tant qu'un relevé valide n'obtient pas 200.

## 2. Le schéma d'entrée (`maintai/api/schemas.py`)

| Variable | Type | Minimum (`ge`) | Maximum (`le`) | Justification physique (pas le min / max des données) |
|---|---|---|---|---|
| `temperature_c` | `float` | -40 | 150 | -40 °C : démarrage à froid en hiver ; 150 °C : limite des isolants d'un moteur (classe H), au-delà le bobinage est détruit |
| `vibration_mm_s` | `float` | 0 | 50 | une vitesse de vibration ne peut pas être négative ; la norme ISO 10816 classe une machine comme « inacceptable » dès 11 mm/s environ, et 50 laisse de la marge pour mesurer une machine en train de casser |
| `load_pct` | `float` | 0 | 120 | 0 % : moteur à l'arrêt ; une surcharge temporaire jusqu'à environ 120 % de la charge nominale reste possible |
| `runtime_hours` | `float` | 0 | 200 000 | des heures de fonctionnement ne sont jamais négatives ; 200 000 h, soit environ 23 ans en continu, dépassent la durée de vie d'un moteur industriel. Type `float` pour accepter 15000,5 h |

Après avoir écrit `schemas.py` seul, que donne `python -m pytest`, et quel est le message d'erreur des tests qui échouent ? Pourquoi est-ce un bon signe ?

```
3 failed, 10 passed
E   NotImplementedError
```

On a toujours 3 tests en échec, mais l'erreur n'est plus la même : ce n'est plus un 422, c'est `NotImplementedError` levée dans `predict()`. C'est un bon signe : le schéma accepte maintenant les relevés valides, qui vont jusqu'à ma fonction. Il ne manque plus que le corps de `predict()`. Et les tests 422 passent maintenant pour la bonne raison, puisque 500 °C dépasse `le=150`.

## 3. La fonction `predict()` (`maintai/api/main.py`)

Votre code :

```python
predictor = state.get("predictor")
if predictor is None:
    raise HTTPException(
        status_code=503,
        detail="Modèle non chargé : lancez python -m maintai.train puis relancez l'API",
    )
return PredictionOut(**predictor.predict(reading.model_dump()))
```

Pourquoi répondre **503** et pas 500 quand le modèle manque ?

500 veut dire « erreur du serveur » : il y a un bug dans le code. Ici, le code est correct ; il manque seulement le fichier `models/model.joblib`. 503 veut dire « service indisponible pour l'instant » : le client comprend qu'il peut réessayer plus tard, et l'administrateur sait qu'il doit lancer `python -m maintai.train`. Sans cette vérification, `predictor.predict` planterait sur `None` et l'API renverrait un 500 trompeur.

Pourquoi le modèle est-il chargé **une seule fois**, au démarrage, et pas à chaque requête ?

Lire `model.joblib` sur le disque prend du temps. Si on le relisait à chaque requête, chaque prédiction serait lente, et l'API le serait encore plus avec beaucoup de clients en même temps. Chargé une seule fois au démarrage dans `state`, le modèle reste en mémoire, et chaque prédiction ne prend que quelques millisecondes.

## 4. Les tests

Dernière ligne de `python -m pytest` à la fin du TP :

```
13 passed
```

## 5. L'API en marche

Après `python -m maintai.dataset` et `python -m maintai.train`, lancez `uvicorn maintai.api.main:app --reload`, puis envoyez ces requêtes depuis `/docs` (ou avec `curl.exe`).

| Requête | Code obtenu | Réponse (le corps JSON) |
|---|---|---|
| `GET /health` | 200 | `{"status": "ok", "model_loaded": true}` |
| `POST /v1/predict` avec `{"temperature_c": 72.5, "vibration_mm_s": 6.1, "load_pct": 85, "runtime_hours": 15000}` | 200 | `{"failure_probability": 0.8623, "alert": true}` |
| `POST /v1/predict` avec une température de 500 | 422 | `{"detail": [{"type": "less_than_equal", "loc": ["body", "temperature_c"], "msg": "Input should be less than or equal to 150", "input": 500, "ctx": {"le": 150.0}}]}` |
| `POST /v1/predicte` (faute de frappe dans l'adresse) | 404 | `{"detail": "Not Found"}` |

Dans `/docs`, où voit-on les bornes que vous avez choisies ?

Sur la route `POST /v1/predict` : ouvrez « Request body », puis l'onglet **Schema**. Chaque champ affiche son type, sa description, ainsi que `minimum` et `maximum`. On les retrouve aussi tout en bas de la page, dans la section **Schemas** → `SensorReading`.

## 6. Questions de compréhension

1. REST et FastAPI : quelle est la différence ?
   REST est un ensemble de **règles** pour concevoir une API web : des URL claires, les méthodes GET et POST, des codes de statut précis, du JSON, une version. FastAPI est une **bibliothèque Python**, c'est-à-dire l'outil avec lequel on écrit une API qui suit ces règles. On écrit donc une API REST *avec* FastAPI, et on la fait tourner *avec* uvicorn.
2. Le schéma Pydantic sert à trois choses. Lesquelles ?
   (1) **Valider** : il refuse les entrées invalides en 422 avant même d'appeler la fonction. (2) **Documenter** : il construit automatiquement la page `/docs`, avec les types, les bornes et les descriptions. (3) **Donner un objet Python typé** : `reading.temperature_c` est un `float` déjà vérifié, et `reading.model_dump()` le transforme en dictionnaire pour le modèle.
3. Dans `http://localhost:8000/v1/predict`, que désignent `localhost`, `8000` et `/v1/predict` ?
   `localhost`, c'est la machine elle-même : le serveur tourne sur mon PC. `8000` est le **port**, la « porte » sur laquelle uvicorn écoute. `/v1/predict` est la **route**, un chemin défini dans le code Python et non un dossier sur le disque.
4. Pourquoi `/v1` dans l'adresse ?
   C'est la **version** de l'API. Si le contrat change un jour (un nouveau champ, une réponse différente), on pourra créer `/v2` sans casser les programmes qui utilisent encore `/v1`.
5. Dans la commande `uvicorn maintai.api.main:app`, que désignent `maintai.api.main` et `app` ?
   `maintai.api.main` est le fichier `maintai/api/main.py`, écrit avec des points et sans `.py`. `app` est la variable de ce fichier qui contient l'application : `app = FastAPI(...)`.

## 7. Le rendu Git

- Lien de la pull request : …
- Le tag `tp1` existe sur GitHub : oui / non
- Qui a relu la pull request, et quel commentaire a-t-il laissé ?
  …

## 8. Ce qui reste flou

…
