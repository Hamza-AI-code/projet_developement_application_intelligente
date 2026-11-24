# Compte rendu · TP6 : conteneuriser MaintAI (Docker, Docker Compose)

**Groupe :** G2  ·  **Membres :** Salma Chair  ·  **Date :** 24/11/2026

> Remplissez chaque partie dans ce fichier, puis rendez-le avec la pull request du TP6.
> Collez les sorties du terminal entre les lignes ``` (trois accents graves).

---

## 1. Mise en place (dans `TP/TP6`)

Sortie de `docker run hello-world` (première ligne) et de `docker version` (lignes Client et Server) :

```
⚠️ À COLLER : relancer `docker run hello-world` et `docker version`
```

Dernière ligne de `python -m pytest` après la mise en place :

```
======== 7 failed, 31 passed, 6 warnings in 14.23s ========
```

Les 5 échecs de `tests/test_docker.py` portaient sur les fichiers à compléter (Dockerfile, .dockerignore, compose.yaml, ui/app.py). Les 2 échecs de `tests/test_package.py` venaient du package non installé dans le nouveau venv, corrigés par `pip install -e .`.

## 2. Image et conteneur (pendant le premier build)

1. Quelle différence entre une image et un conteneur ?
   Une image est un modèle figé, en lecture seule : un système de fichiers en couches (Python, bibliothèques, code) et une commande de démarrage. Un conteneur est une instance de cette image en cours d'exécution, avec sa propre couche modifiable, son réseau et ses processus. Une même image peut lancer plusieurs conteneurs.
2. Pourquoi `COPY requirements-docker.txt` est-il placé avant `COPY maintai` ?
   Chaque instruction crée une couche mise en cache. Les bibliothèques changent rarement, alors que le code change souvent. En copiant d'abord `requirements-docker.txt` et en lançant `pip install`, cette étape lente reste en cache : une modification du code ne refait que les couches qui suivent `COPY maintai`.
3. Pourquoi `requirements-docker.txt` contient-il `scikit-learn==1.8.0` et pas `scikit-learn>=1.5` ?
   Le modèle `model.joblib` a été écrit par scikit-learn 1.8.0. Avec `>=1.5`, l'image pourrait installer une autre version, et le modèle risquerait de ne pas se recharger ou de prédire autrement. La version figée garantit le même environnement qu'à l'entraînement et un build reproductible.
4. Pourquoi ni `mlflow`, ni `dvc`, ni `pytest` dans l'image ?
   L'image sert seulement à faire tourner l'API et l'interface. On n'y entraîne pas de modèle (mlflow), on n'y versionne pas de données (dvc) et on n'y lance pas de tests (pytest). Les ajouter alourdirait l'image et augmenterait sa surface d'attaque pour rien.

## 3. Sprint 1 : le Dockerfile

Votre `Dockerfile` :

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements-docker.txt .
RUN pip install --no-cache-dir -r requirements-docker.txt
COPY maintai ./maintai
COPY ui ./ui
ENV MAINTAI_MODELS_DIR=/app/models \
    MAINTAI_DATA_PATH=/app/data/sensors.csv
EXPOSE 8000
CMD ["uvicorn", "maintai.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

| Build | Durée | Taille de l'image (`docker images`) |
|---|---|---|
| premier build | 46,2 s | 845 MB |
| après une modification de `maintai/predict.py` | 1,5 s | 845 MB |

Que signifie `CACHED` dans le journal du second build ?

`CACHED` signifie que Docker a réutilisé une couche déjà construite au lieu de refaire l'instruction, car ni l'instruction ni les fichiers copiés n'avaient changé. Au second build, `WORKDIR`, `COPY requirements-docker.txt` et `RUN pip install` sont `CACHED`. Seules les couches à partir de `COPY maintai`, le premier fichier modifié, sont reconstruites : on passe de 46 s à 1,5 s.

## 4. Sprint 1 : lancer un conteneur

Votre commande `docker run` :

```
docker run -d --name maintai-api -p 8000:8000 --env-file .env -v "$(pwd)/models:/app/models:ro" maintai:0.4.0
```

| Essai | Réponse |
|---|---|
| `GET /health` | `{"status":"ok","model_loaded":true}` |
| `POST /v1/predict` sans clé | 401 : `{"detail":"Clé API absente ou invalide"}` |
| `POST /v1/predict` avec la clé | `{"failure_probability":0.9475,"alert":true,"threshold":0.3,"model_version":"2026-11-24T16:44:14Z"}` |

**Piège 1.** Sans l'option `-v ...models...`, que répondent `/health` et `/v1/predict` ? Pourquoi ?

`/health` répond `{"status":"ok","model_loaded":false}`, et `/v1/predict` répond 503 : `{"detail":"Modèle non chargé : lancez python -m maintai.train puis redémarrez l'API"}`. Le modèle n'est pas dans l'image, car `models/` est exclu par `.dockerignore`. Sans le volume, `/app/models` est vide dans le conteneur. L'API démarre quand même (le `FileNotFoundError` est intercepté au démarrage), mais elle ne peut pas prédire.

**Piège 2.** Avec `--host 127.0.0.1`, que disent `docker logs test` et `http://localhost:8002/health` ? Pourquoi ?

`docker logs test` indique `Uvicorn running on http://127.0.0.1:8000`, donc le serveur tourne. Mais `curl http://localhost:8002/health` échoue avec `Recv failure: Connection reset by peer`. Dans le conteneur, 127.0.0.1 désigne la boucle locale du conteneur lui-même. Les requêtes venant du PC par le port publié arrivent sur l'interface réseau du conteneur, pas sur sa boucle locale, et uvicorn ne les écoute pas. Il faut écouter sur `0.0.0.0`, c'est-à-dire toutes les interfaces.

## 5. Sprint 2 : Docker Compose

Votre `compose.yaml` :

```yaml
services:
  api:
    build: .
    image: maintai:0.4.0
    env_file: .env                     # MAINTAI_API_KEY, comme au TP2
    ports:
      - "8000:8000"                    # PC:conteneur
    volumes:
      - ./models:/app/models:ro        # le modèle vient du PC, en lecture seule

  ui:
    image: maintai:0.4.0               # la même image, une autre commande
    command: ["python", "-m", "streamlit", "run", "ui/app.py",
              "--server.address=0.0.0.0", "--server.port=8501", "--server.headless=true"]
    environment:
      MAINTAI_API_URL: http://api:8000 # l'API vue depuis ce conteneur : le nom du service
    ports:
      - "8501:8501"
    volumes:
      - ./data:/app/data:ro
    depends_on:
      - api
```

Sortie de `docker compose ps` :

```
⚠️ À COLLER : relancer `docker compose up -d` puis `docker compose ps`
```

Quelle URL affiche la barre latérale de l'interface ? D'où vient-elle ?

La barre latérale affiche `http://api:8000`. Cette valeur vient de la variable d'environnement `MAINTAI_API_URL`, définie dans `compose.yaml` pour le service `ui` et lue dans `ui/app.py` par `os.getenv("MAINTAI_API_URL", "http://localhost:8000")`. Sans cette variable, par exemple hors Docker, la valeur par défaut `http://localhost:8000` est utilisée.

Résultat des deux commandes `docker compose exec ui ...` (avec `api` puis avec `localhost`). Pourquoi la seconde échoue-t-elle ?

```
⚠️ À COLLER : sortie de
docker compose exec ui python -c "import httpx; print(httpx.get('http://api:8000/health').json())"
docker compose exec ui python -c "import httpx; print(httpx.get('http://localhost:8000/health').json())"
```

La première réussit : Compose crée un réseau commun où chaque service est joignable par son nom, et `api` désigne le conteneur de l'API. La seconde échoue (`ConnectError`), car dans le conteneur `ui`, `localhost` désigne le conteneur `ui` lui-même, où rien n'écoute sur le port 8000. Le port publié `8000:8000` concerne le PC, pas les autres conteneurs.

Dernière ligne de `python -m pytest` à la fin du sprint 2 :

```
======== 38 passed, 6 warnings in 14.79s ========
```

## 6. Décision : l'ADR 005

Dans `docs/adr/005-image-docker.md`. Résumez ici votre décision en deux phrases :

L'image `maintai:0.4.0` ne contient que Python 3.11, les bibliothèques en versions figées et le code (`maintai/`, `ui/`). Le modèle et les données arrivent par des volumes en lecture seule et la clé API par `env_file`, pour que l'image reste légère, sans secret, et réutilisable avec n'importe quel modèle sans reconstruction.

## 7. Questions de compréhension

1. Qu'est-ce qui entre dans l'image, et qu'est-ce qui arrive au lancement ? Donnez le moyen pour chaque élément.
   - **Dans l'image (au build)** : Python 3.11 (`FROM python:3.11-slim`), les bibliothèques (`COPY requirements-docker.txt` + `RUN pip install`), le code (`COPY maintai`, `COPY ui`), les chemins par défaut (`ENV`) et la commande de démarrage (`CMD`).
   - **Au lancement** : le modèle (volume `-v ./models:/app/models:ro`), les données (volume `./data:/app/data:ro`), la clé API et les origines CORS (`--env-file .env` / `env_file`), l'URL de l'API pour l'interface (`environment: MAINTAI_API_URL`) et les ports (`-p` / `ports`).
2. Pourquoi la clé API n'est-elle jamais dans l'image ?
   Une image se partage, se pousse sur un registre et s'inspecte (`docker history`, extraction des couches) : toute personne qui l'obtient lirait la clé. Une clé dans l'image obligerait aussi à reconstruire l'image pour la changer, et la même clé servirait partout. Passée au lancement, elle reste sur la machine qui exécute le conteneur, et chaque environnement a la sienne. C'est pour ça que `.env` est dans `.dockerignore` et dans `.gitignore`.
3. Livrer un modèle (TP4, TP5) : qu'est-ce que Docker ajoute à la liste ?
   On livrait déjà le modèle, ses métriques, les versions figées des bibliothèques (TP4), ainsi que la trace de l'entraînement et la version des données (MLflow, DVC au TP5). Docker ajoute **l'environnement d'exécution complet** : le système (Debian slim), la version exacte de Python, les bibliothèques déjà installées et la commande de lancement. L'API tourne donc de la même façon sur n'importe quelle machine qui a Docker, sans installer Python ni créer de venv.

## 8. Le rendu Git

- Lien de la pull request : ⚠️ À COMPLÉTER
- Le tag `tp6` existe sur GitHub : ⚠️ oui / non
- `git status` avant le commit : `.env`, `models/` ou `data/*.csv` apparaissaient-ils ? non (ils sont dans `.gitignore`) ⚠️ à vérifier

## 9. Ce qui reste flou

…
