"""La fiche technique des entrées et des sorties de l'API."""

from pydantic import BaseModel, ConfigDict, Field


class SensorReading(BaseModel):
    """Un relevé de capteurs. Les bornes sont physiques, pas celles de sensors.csv."""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "temperature_c": 60.0,
                    "vibration_mm_s": 2.0,
                    "load_pct": 50.0,
                    "runtime_hours": 5000,
                }
            ]
        },
    )

    temperature_c: float = Field(
        ge=-40, le=150, description="Température du moteur (°C)"
    )
    vibration_mm_s: float = Field(
        ge=0, le=50, description="Vitesse de vibration efficace (mm/s)"
    )
    load_pct: float = Field(
        ge=0, le=120, description="Charge du moteur (% de la charge nominale)"
    )
    runtime_hours: float = Field(
        ge=0, le=200_000, description="Heures de fonctionnement cumulées (h)"
    )


class PredictionOut(BaseModel):
    failure_probability: float = Field(ge=0, le=1, description="Probabilité de panne")
    alert: bool = Field(description="Vrai si la probabilité atteint le seuil (0,3)")
