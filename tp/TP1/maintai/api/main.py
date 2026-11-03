"""L'API MaintAI : GET /health, POST /v1/predict."""

from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI, HTTPException

from maintai.api.schemas import PredictionOut, SensorReading
from maintai.predict import load_predictor

state: dict = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    state["predictor"] = load_predictor()  # chargé UNE fois, au démarrage
    yield
    state.clear()


app = FastAPI(title="MaintAI", version="1.0", lifespan=lifespan)
router = APIRouter(prefix="/v1")


@app.get("/health")
def health():
    return {"status": "ok", "model_loaded": state.get("predictor") is not None}


@router.post("/predict", response_model=PredictionOut)
def predict(reading: SensorReading) -> PredictionOut:
    predictor = state.get("predictor")
    if predictor is None:
        raise HTTPException(
            status_code=503,
            detail="Modèle non chargé : lancez python -m maintai.train puis relancez l'API",
        )
    return PredictionOut(**predictor.predict(reading.model_dump()))


app.include_router(router)
