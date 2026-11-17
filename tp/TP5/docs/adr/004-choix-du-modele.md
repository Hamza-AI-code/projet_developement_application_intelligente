# ADR 004 : Model and alert threshold for MaintAI

Date: 17/11/2026 · Authors: Yassine Sinif (group G2)

## Context
MaintAI predicts machine failures from sensor readings. A missed failure costs much more than a false alarm,
so recall matters more than precision. About 13% of readings are failures, so accuracy alone is misleading
(the "never fail" baseline already gets 0.864 accuracy with recall 0).

## Options studied
Five MLflow runs on the same data (v1, 5000 rows, `data_md5` = `73e0b7cb3c6f795c70c3ddf970b99c15`):

| Run | Model / settings | recall | precision | accuracy |
|---|---|---|---|---|
| 859869291c6f | logreg, C=1.0, threshold 0.3 | 0.750 | 0.622 | 0.904 |
| 79db14085bc0 | logreg, C=0.01, threshold 0.3 | 0.691 | 0.653 | 0.908 |
| 01c40d35381b | logreg, C=1.0, threshold 0.2 | 0.838 | 0.543 | 0.882 |
| 2a0baa7d929 | forest, threshold 0.3 | 0.728 | 0.562 | 0.886 |
| 06b89ea7ddd8 | forest, threshold 0.2 | 0.831 | 0.479 | 0.854 |

## Decision
Logistic regression (C=1.0) with an alert threshold of 0.2, i.e. run `01c40d35381b4623bd5c5fc617e46fa8`,
trained on data version v1 (`data_md5` = `73e0b7cb3c6f795c70c3ddf970b99c15`).
It has the best recall (0.838) of all runs, and it keeps a better precision than the forest at a similar recall
(0.543 vs 0.479). It is also simpler, faster and easier to explain than a random forest.

## Consequences
- About 84% of failures are caught; the price is more false alarms (about 46% of alerts are false).
- The model is reproducible: the run id gives the parameters and library versions, `data_md5` gives the exact data.
- The numbers come from one train/test split of synthetic data; they must be re-checked on real data.
  If the data changes (new DVC version), retrain and compare again before keeping this decision.
