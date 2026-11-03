# ADR 002 — Validation des entrées de l'API MaintAI

- **Statut :** accepté
- **Date :** 2026-11-03

## Contexte
L'API reçoit des relevés de capteurs envoyés par d'autres programmes (tableau de bord, appli mobile, système d'atelier).
Une valeur impossible (capteur débranché, faute de frappe, unité confondue) ne doit jamais atteindre le modèle :
il renverrait une probabilité qui a l'air sérieuse alors qu'elle n'a aucun sens.

## Décision 1 — Les bornes de chaque variable sont physiques
Les bornes sont celles qu'un moteur réel peut afficher, **pas** le min/max de `sensors.csv`.

| Variable | Bornes | Justification |
|---|---|---|
| `temperature_c` | -40 → 150 °C | -40 °C : démarrage à froid en hiver ; 150 °C : limite des isolants classe H, au-delà le moteur est détruit |
| `vibration_mm_s` | 0 → 50 mm/s | une vitesse efficace est ≥ 0 ; ISO 10816 classe « inacceptable » dès ~11 mm/s, 50 laisse de la marge pour mesurer une machine en train de casser |
| `load_pct` | 0 → 120 % | 0 % à l'arrêt ; une surcharge temporaire jusqu'à ~120 % de la charge nominale est possible |
| `runtime_hours` | 0 → 200 000 h | ≈ 23 ans de fonctionnement continu, au-delà de la durée de vie d'un moteur industriel ; `float` pour accepter 15000,5 h |

De plus, `extra="forbid"` refuse tout champ inconnu (une faute de frappe sur un nom de champ ne passe pas en silence).

**Option écartée :** copier le min/max de `sensors.csv`. On perdrait les machines un peu plus chaudes ou plus usées
que celles vues à l'entraînement — justement celles qui risquent de tomber en panne — qui seraient refusées en 422.

## Décision 2 — Modèle absent : l'API démarre et répond 503
Si `models/model.joblib` n'existe pas, l'API démarre quand même : `/health` répond `"model_loaded": false`
et `/v1/predict` renvoie **503 Service Unavailable** avec un message qui dit quoi faire.

**Option écartée :** refuser de démarrer. On gagnerait une erreur visible immédiatement, mais on perdrait `/health`
(impossible de diagnostiquer à distance), `/docs`, et le serveur tomberait en boucle dans un orchestrateur.
Un 500 serait pire encore : il dit « bug » alors que le problème est un fichier manquant.

## Conséquences
- 500 °C → 422 avant même l'appel de `predict()` ; le modèle ne voit que des valeurs plausibles.
- Les bornes sont écrites une seule fois (schéma Pydantic) et servent à valider, documenter `/docs` et typer.
- Si un nouveau capteur mesure au-delà des bornes, il faudra modifier le schéma (et cet ADR).
