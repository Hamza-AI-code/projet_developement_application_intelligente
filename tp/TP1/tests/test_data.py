from maintai import config, dataset


def test_colonnes_attendues():
    df = dataset.make_dataset(200)
    assert list(df.columns) == config.FEATURES + [config.TARGET]


def test_cible_binaire_et_pannes_presentes():
    df = dataset.make_dataset(500)
    assert set(df[config.TARGET].unique()) == {0, 1}
    assert 0.05 < df[config.TARGET].mean() < 0.5


def test_valeurs_physiques():
    df = dataset.make_dataset(500)
    assert df["vibration_mm_s"].min() >= 0
    assert df["load_pct"].between(0, 100).all()
