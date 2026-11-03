"""Chargement et découpage des données."""

import pandas as pd
from sklearn.model_selection import train_test_split

from maintai import config


def load_data(path=None) -> pd.DataFrame:
    return pd.read_csv(path or config.DATA_PATH)


def split(df: pd.DataFrame, test_size: float = 0.2):
    X = df[config.FEATURES]
    y = df[config.TARGET]
    return train_test_split(
        X, y, test_size=test_size, random_state=config.SEED, stratify=y
    )
