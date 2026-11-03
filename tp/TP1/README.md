# MaintAI — TP1 : une API de prédiction de panne

```bat
python -m venv .venv
.venv\Scripts\activate.bat
pip install -r requirements.txt
python -m maintai.dataset      # écrit data\sensors.csv
python -m maintai.train        # écrit models\model.joblib et models\model_info.json
python -m pytest               # 13 passed
uvicorn maintai.api.main:app --reload   # puis http://localhost:8000/docs
```

| Route | Méthode | Rôle |
|---|---|---|
| `/health` | GET | état de l'API et du modèle |
| `/v1/predict` | POST | relevé de 4 capteurs → `failure_probability`, `alert` (seuil 0,3) |
