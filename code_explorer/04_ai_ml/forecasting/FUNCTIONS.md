# 04_ai_ml/forecasting (generated)

Modules: `backend/app/forecasting.py`, `backend/scinsight/learning.py`

| ID | Function / class | Kind | Status | Original | Annotated copy | Summary |
|---|---|---|---|---|---|---|
| F0524 | `_history` | function | used | [backend/app/forecasting.py:10](../../../backend/app/forecasting.py#L10) | [annotated](../../04_ai_ml/forecasting/app_forecasting.py) |  |
| F0525 | `_features` | function | used | [backend/app/forecasting.py:16](../../../backend/app/forecasting.py#L16) | [annotated](../../04_ai_ml/forecasting/app_forecasting.py) |  |
| F0526 | `_fit_predict` | function | used | [backend/app/forecasting.py:28](../../../backend/app/forecasting.py#L28) | [annotated](../../04_ai_ml/forecasting/app_forecasting.py) |  |
| F0527 | `backtest` | function | used | [backend/app/forecasting.py:40](../../../backend/app/forecasting.py#L40) | [annotated](../../04_ai_ml/forecasting/app_forecasting.py) | Forecast vs actuals: train without the last `holdout_days`, predict them, then f |
| F0528 | `_errors` | function | used | [backend/app/forecasting.py:62](../../../backend/app/forecasting.py#L62) | [annotated](../../04_ai_ml/forecasting/app_forecasting.py) |  |
| F0529 | `evaluate_models` | function | used | [backend/app/forecasting.py:69](../../../backend/app/forecasting.py#L69) | [annotated](../../04_ai_ml/forecasting/app_forecasting.py) | Model quality on the same holdout: XGBoost vs a seasonal-naive baseline (same we |
| F0530 | `pooled_evaluation` | function | used | [backend/app/forecasting.py:91](../../../backend/app/forecasting.py#L91) | [annotated](../../04_ai_ml/forecasting/app_forecasting.py) | Train one model on demand-normalised series from several customers and score it  |
| F0531 | `forecast` | function | used | [backend/app/forecasting.py:129](../../../backend/app/forecasting.py#L129) | [annotated](../../04_ai_ml/forecasting/app_forecasting.py) |  |
| F0532 | `_rows` | function | used | [backend/scinsight/learning.py:24](../../../backend/scinsight/learning.py#L24) | [annotated](../../04_ai_ml/forecasting/scinsight_learning.py) |  |
| F0533 | `_features` | function | used | [backend/scinsight/learning.py:38](../../../backend/scinsight/learning.py#L38) | [annotated](../../04_ai_ml/forecasting/scinsight_learning.py) |  |
| F0534 | `train_lead_time_model` | function | used | [backend/scinsight/learning.py:43](../../../backend/scinsight/learning.py#L43) | [annotated](../../04_ai_ml/forecasting/scinsight_learning.py) |  |
| F0535 | `promote` | function | used | [backend/scinsight/learning.py:73](../../../backend/scinsight/learning.py#L73) | [annotated](../../04_ai_ml/forecasting/scinsight_learning.py) |  |
| F0536 | `predict_lead_time` | function | used | [backend/scinsight/learning.py:88](../../../backend/scinsight/learning.py#L88) | [annotated](../../04_ai_ml/forecasting/scinsight_learning.py) | Re-fit the promoted configuration deterministically on all receipts and predict  |
| F0537 | `retraining_request` | function | used | [backend/scinsight/learning.py:101](../../../backend/scinsight/learning.py#L101) | [annotated](../../04_ai_ml/forecasting/scinsight_learning.py) |  |
