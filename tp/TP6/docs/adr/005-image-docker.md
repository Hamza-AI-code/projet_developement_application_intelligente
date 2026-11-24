# ADR 005 : une image Docker qui contient le code, pas le modèle ni les secrets

Date : 24/11/2026 · Auteurs : Salma Chair

## Contexte
MaintAI doit tourner à l'identique sur n'importe quelle machine, avec les versions de bibliothèques qui ont écrit le modèle (scikit-learn 1.8.0). Il faut décider de ce qui entre dans l'image Docker et de ce qui arrive au lancement.

## Options étudiées
1. **Tout dans l'image (code, bibliothèques, modèle, données, clé API)** : un seul fichier à livrer et rien à monter au lancement. En revanche, l'image est lourde et doit être reconstruite à chaque nouveau modèle, et la clé est lisible par toute personne qui récupère l'image.
2. **Code et bibliothèques dans l'image ; modèle, données et clé au lancement** : l'image est plus légère, sans secret, et la même image sert pour tous les modèles et tous les environnements. En revanche, il faut penser à monter `models/` et à fournir `.env`, sinon l'API démarre sans modèle (503) ou sans clé (500).

## Décision
Option 2. L'image `maintai:0.4.0` contient `python:3.11-slim`, les bibliothèques de `requirements-docker.txt` (versions figées) et les dossiers `maintai/` et `ui/`. Le modèle et les données arrivent par des volumes en lecture seule, et la clé par `--env-file` / `env_file`. Raison principale : un secret ne doit jamais être dans une image, et le modèle doit pouvoir changer sans reconstruire l'image.

## Conséquences
- On peut changer de modèle (TP5) en remplaçant `models/` puis en redémarrant le conteneur, sans rebuild.
- `.dockerignore` doit exclure `data/`, `models/`, `.env`, `mlflow.db`, `mlruns/` et `.dvc/`, et il faut le tenir à jour.
- Il faut surveiller `/health` (`model_loaded`) : un oubli du volume ne fait pas planter l'API, il la rend inutile (503).
- `requirements-docker.txt` doit rester aligné sur les versions qui ont entraîné le modèle.
