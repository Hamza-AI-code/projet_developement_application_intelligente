"""Fabrique un jeu de données synthétique de capteurs : data/sensors.csv."""

import numpy as np
import pandas as pd

from maintai import config


def make_dataset(n: int = 2000, seed: int = config.SEED) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    temperature = rng.normal(65, 10, n).clip(20, 110)
    vibration = rng.gamma(2.0, 1.2, n).clip(0, 20)
    load = rng.uniform(10, 100, n)
    runtime = rng.uniform(0, 20000, n)
    score = (
        0.08 * (temperature - 65)
        + 0.45 * (vibration - 2.4)
        + 0.02 * (load - 55)
        + 0.00012 * (runtime - 10000)
        - 1.8
    )
    proba = 1 / (1 + np.exp(-score))
    failure = (rng.uniform(0, 1, n) < proba).astype(int)
    return pd.DataFrame(
        {
            "temperature_c": temperature.round(1),
            "vibration_mm_s": vibration.round(2),
            "load_pct": load.round(1),
            "runtime_hours": runtime.round(0),
            "failure": failure,
        }
    )


def main(path=None) -> None:
    path = path or config.DATA_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    df = make_dataset()
    df.to_csv(path, index=False)
    print(
        f"{len(df)} relevés écrits dans {path} (taux de panne {df[config.TARGET].mean():.3f})"
    )


if __name__ == "__main__":
    main()
