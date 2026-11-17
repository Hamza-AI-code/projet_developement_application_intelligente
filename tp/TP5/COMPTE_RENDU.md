# Compte rendu · TP5 : suivre les entraînements (MLflow) et versionner les données (DVC)

**Groupe : G2  ·  Membres : Yassine Sinif  ·  Date : 17/11/2026**

> Notes are written in English. Terminal outputs are pasted between the ``` lines.

---

## 1. Mise en place (dans `TP/TP5`)

Last line of `python -m pytest` after `pip install -r requirements.txt` and `pip install -e .` (first run, before writing `log_run`):

```
======================== 5 failed, 27 passed, 2 warnings in 23.40s ========================
```

Which tests fail, and why?

The 5 tests of `tests/test_tracking.py` fail (`test_training_creates_a_run`, `test_run_records_metrics`,
`test_run_records_data_version`, `test_run_stores_the_model`, `test_options_change_the_run`).
The cause is a single one: `log_run` in `maintai/tracking.py` was only a stub (`return ""`), so training worked but
nothing was recorded in MLflow. The tests search the experiment `maintai`, find no run (MLflow even warns
"Cannot retrieve experiment by name maintai") and the assertion `len(runs) >= 1` fails. The printed line
`Run MLflow : ` was empty for the same reason.

Before `pip install -e .`, where did the installed `maintai` package point? And after?

Before, `maintai` was either not installed or was a copy in `site-packages` (a frozen snapshot of the code, which
does not follow my edits). After `pip install -e .`, `pip show maintai` says
`Editable project location: C:\Users\yassi\Downloads\TP5\TP5`: the package points to my working folder, so any
change in the code is used immediately and `streamlit run ui/app.py` can import `maintai` without `python -m`.

## 2. Sprint 1 : MLflow

My `log_run` function (`maintai/tracking.py`):

```python
def log_run(params: dict, metrics: dict, model, X_example, data_path: Path) -> str:
    mlflow.set_experiment(EXPERIMENT)
    with mlflow.start_run() as run:
        mlflow.log_params(params)
        mlflow.log_param("data_md5", file_md5(data_path))  # data version = file fingerprint
        mlflow.log_metrics(metrics)
        mlflow.sklearn.log_model(
            model, name="model", input_example=X_example, skops_trusted_types=TRUSTED_TYPES
        )
    return run.info.run_id
```

`data_md5` is a parameter (a label describing the input), not a metric (a number measuring a result).

Last line of `python -m pytest` at the end of sprint 1:

```
32 passed, 6 warnings in 29.22s
```

My runs (read from the MLflow database / `mlflow ui`, data v1, 5000 rows):

| Command | recall | precision | accuracy |
|---|---|---|---|
| `python -m maintai.train` | 0.750 | 0.622 | 0.904 |
| `python -m maintai.train --C 0.01` | 0.691 | 0.653 | 0.908 |
| `python -m maintai.train --threshold 0.2` | 0.838 | 0.543 | 0.882 |
| `python -m maintai.train --model forest` | 0.728 | 0.562 | 0.886 |
| (my test) `--model forest --threshold 0.2` | 0.831 | 0.479 | 0.854 |

Which run would I choose for MaintAI, and why?

`--threshold 0.2` (logistic regression, C=1.0): it has the best recall (0.838). A missed failure costs more than a
false alarm, so I accept lower precision (0.543). The forest does not help: at a similar recall its precision is
worse (0.479) and the model is heavier. Accuracy is not a good criterion: the "never fail" baseline already scores
0.864 with recall 0.

In `mlflow ui`, open a run's model. Which scikit-learn version is in its `requirements.txt`? Which TP4 problem does this solve?

`scikit-learn==1.8.0` (together with `numpy==2.4.4`, `pandas==3.0.2`, `scipy==1.18.1`, `skops==0.16.0`, `mlflow==3.18.0`).
In TP4 a model trained with one scikit-learn version could break or give wrong results when loaded on a machine
with another version. Now each run stores the exact library versions next to the model, so we know which
environment to rebuild to load it safely.

Where does MLflow store the runs on my disk? Do these files go into Git? Why?

In `mlflow.db` (SQLite: parameters, metrics, run list) and in the `mlruns/` folder (artifacts: the model files),
both in the project folder. They are in `.gitignore` and do not go into Git: they are generated, local, can be large
and change at every run. Git would fill up with binary files and every teammate would have conflicts.

## 3. Sprint 2 : DVC

Content of `data/sensors.csv.dvc` after `dvc add data/sensors.csv`:

```
outs:
- md5: 73e0b7cb3c6f795c70c3ddf970b99c15
  size: 126815
  hash: md5
  path: sensors.csv
```

Compare the `md5` of this file with the `data_md5` parameter of my last MLflow run. What do I notice?

They are identical (`73e0b7cb3c6f795c70c3ddf970b99c15`). Both tools compute the md5 of the same file, so the run
is linked to the exact data version: from a run I can find the DVC version, and from the `.dvc` file I can find
the runs trained on it.

Why does `data/sensors.csv` not go into Git, while `data/sensors.csv.dvc` does?

Git is made for small text files; a large dataset would bloat the repository and every version would be stored
forever in its history. The `.dvc` file is a tiny text "pointer" (md5, size, path): Git versions the pointer, and DVC
stores the real file in its cache/remote storage under that md5. `dvc add` also puts the csv in `data/.gitignore`.

After `python -m maintai.dataset --n 8000 --seed 7`, what does `dvc status` say?

```
data\sensors.csv.dvc:
	changed outs:
		modified:           data\sensors.csv
```

| Version | Git commit (`git log --oneline`) | md5 (first 8 characters) | Number of rows |
|---|---|---|---|
| v1 | 95db2d2 | 73e0b7cb | 5000 |
| v2 | 564f3c2 | 93fdeef2 | 8000 |

(Row counts are the lines of the csv minus the header: 5001 and 8001 lines.)

Go back to v1 (`git checkout <commit> -- data/sensors.csv.dvc`, then `dvc checkout`). How many rows does `data/sensors.csv` have? Then go back to v2.

v1: `data/sensors.csv` has 5000 rows (5001 lines with the header). After checking out the v2 pointer again and
`dvc checkout`: 8000 rows (8001 lines). Switching data version is just switching a tiny pointer file.

Delete `data/sensors.csv` and the `.dvc/cache` folder, then run `dvc pull`. What happens?

```
A       data\sensors.csv
1 file fetched and 1 file added
```

The file is fetched back from the remote storage (`C:/dvc-stockage`) and is identical (8000 rows). This shows the
storage is the safe copy of the data: the local cache can be lost without losing anything, as long as `dvc push` was done.

## 4. Relier modèle et données

I trained a model on v2 with the same settings (logistic regression, C=1.0, threshold 0.3) and compared it to the v1 run:

| Run | data_md5 (8 characters) | n_train | recall | precision |
|---|---|---|---|---|
| v1 (859869291c6f) | 73e0b7cb | 4000 | 0.750 | 0.622 |
| v2 (509ba434a94c) | 93fdeef2 | 6400 | 0.741 | 0.650 |

Can we say the v2 model is "better"? Why be careful when comparing two runs trained on different data?

Not really. Recall is slightly lower (0.741 vs 0.750), precision and accuracy are slightly higher; these small
differences could just be noise. Above all, the two runs are not tested on the same test set: v2 has different
rows, a different failure rate (12.8% vs 13.6%) and a different baseline (0.872 vs 0.864 accuracy). A metric
difference can come from the data and not from the model. To compare fairly, change one thing at a time
(same data, different settings) or evaluate both models on the same fixed test set.

## 5. Décision : l'ADR 004

See `docs/adr/004-choix-du-modele.md`: logistic regression, C=1.0, threshold 0.2, run
`01c40d35381b4623bd5c5fc617e46fa8`, `data_md5` = `73e0b7cb3c6f795c70c3ddf970b99c15` (data v1).

## 6. Questions de compréhension

1. Difference between Git, DVC and MLflow? What does each version?
   Git versions the code (and small text files, including the `.dvc` pointers). DVC versions the data (large files,
   stored in a cache/remote storage, identified by their md5). MLflow records the experiments: parameters, metrics,
   data fingerprint and the trained model of each run.
2. Why is the DVC storage added with `--local` in this TP? What would be needed for the whole group to share the same data?
   `--local` writes the remote in `.dvc/config.local`, which is not committed to Git: the path `C:/dvc-stockage` only
   exists on my computer and would be wrong for others. To share the data, the group needs a storage everyone can
   reach (a shared folder, S3/Google Drive/SSH server...) declared in the committed `.dvc/config`, with each person
   running `dvc pull`.
3. Delivering a model is three things (TP4). Which ones, and where are they now?
   (1) The code (the `maintai` package, in Git), (2) the model file (`model.joblib` + `model_info.json`; now also
   stored in each MLflow run with its library versions), (3) the environment / library versions (`requirements.txt`
   and the MLflow `requirements.txt`). Plus the data version, which is now tracked by DVC and `data_md5`.

## 7. Le rendu Git

- Pull request link: not available (no GitHub remote configured on this machine). Local commits: `95db2d2`
  (MLflow + DVC v1) and `564f3c2` (data v2), then the report commit.
- The `tp5` tag exists on GitHub: no (the tag exists locally; push it with `git push origin tp5` once the remote is set)
- `git status` before the commit: `mlflow.db`, `mlruns/`, `data/sensors.csv` or `.dvc/cache` appeared: no
  (they are ignored by `.gitignore`, `data/.gitignore` and `.dvc/.gitignore`)

## 8. Ce qui reste flou

The comparison of runs depends on one random train/test split: I would like to know how much recall varies with
the seed (cross-validation). I also do not know how DVC would handle a team sharing one remote with concurrent pushes.
