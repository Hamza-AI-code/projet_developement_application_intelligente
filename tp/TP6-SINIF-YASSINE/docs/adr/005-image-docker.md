# ADR 005 : Le modèle et la clé API restent hors de l'image Docker

Date : 24/11/2026 17:54 · Auteurs : Yassine Sinif

## Contexte
MaintAI doit tourner à l'identique sur n'importe quel PC ou serveur, dans une image Docker. Mais le modèle (`model.joblib`) se ré-entraîne régulièrement (TP4, TP5), les données changent, et la clé API est un secret : une image se partage et chacune de ses couches se lit.

## Options étudiées
1. **Tout dans l'image** (code, bibliothèques, modèle, données, `.env`) : un seul objet à livrer, démarrage sans option. Mais chaque ré-entraînement oblige à reconstruire l'image, l'image grossit, et la clé API devient lisible par quiconque a l'image (`docker history`).
2. **Code et bibliothèques dans l'image, le reste au lancement** : le modèle et les données arrivent par des volumes en lecture seule, la clé par `--env-file` (ou `env_file` dans Compose). L'image est légère, partageable, sans secret, et le cache Docker évite de réinstaller les bibliothèques à chaque changement de code. Au prix d'un `-v` et d'un `--env-file` à ne pas oublier.

## Décision
Option 2. L'image contient seulement Python 3.11, les bibliothèques figées (`requirements-docker.txt`, `scikit-learn==1.8.0` comme le modèle) et le code. Le `.dockerignore` laisse dehors `data/`, `models/`, `.env`, `mlflow.db`, `mlruns/` et `.dvc/`. La raison principale : un secret ne doit jamais entrer dans une image, et un modèle qui change ne doit pas obliger à reconstruire.

## Conséquences
- Facilite : ré-entraîner et remplacer le modèle sans reconstruire l'image, changer de clé par simple redémarrage, partager l'image sans fuite, builds rapides grâce au cache.
- Complique : sans le volume `models/`, l'API démarre mais répond `model_loaded: false` (503 sur `/v1/predict`) ; il faut penser au `-v` ou à Compose.
- À surveiller : garder `scikit-learn` figé à la version qui a écrit le modèle, et ne jamais retirer `.env` du `.dockerignore`.
