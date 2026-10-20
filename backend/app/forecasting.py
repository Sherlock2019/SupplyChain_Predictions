"""Small deterministic training pipeline using XGBoost for the POC demand forecast."""
from __future__ import annotations

import math
from functools import lru_cache

import numpy as np


def _history(base: float, days: int = 180) -> np.ndarray:
    # Reproducible synthetic SAP history with weekly seasonality and a mild trend.
    x = np.arange(days, dtype=float)
    return base * (1 + 0.0015 * x + 0.16 * np.sin(2 * math.pi * x / 7) + 0.05 * np.sin(2 * math.pi * x / 30))


def _features(day_indexes: np.ndarray) -> np.ndarray:
    return np.column_stack(
        [
            day_indexes,
            np.sin(2 * math.pi * day_indexes / 7),
            np.cos(2 * math.pi * day_indexes / 7),
            np.sin(2 * math.pi * day_indexes / 30),
            np.cos(2 * math.pi * day_indexes / 30),
        ]
    )


def _fit_predict(history: np.ndarray, train_days: np.ndarray, predict_days: np.ndarray) -> tuple[np.ndarray, str]:
    try:
        from xgboost import XGBRegressor

        model = XGBRegressor(n_estimators=100, max_depth=3, learning_rate=0.06, subsample=0.9, random_state=42, n_jobs=1)
        model.fit(_features(train_days), history[train_days.astype(int)])
        return model.predict(_features(predict_days)), "xgboost"
    except ImportError:  # pragma: no cover
        coefficients = np.polyfit(train_days, history[train_days.astype(int)], 1)
        return np.polyval(coefficients, predict_days), "linear-fallback"


@lru_cache(maxsize=64)
def backtest(base_daily_demand: float, holdout_days: int = 14, horizon_days: int = 14, show_days: int = 45) -> dict:
    """Forecast vs actuals: train without the last `holdout_days`, predict them, then forecast the future horizon."""
    history = _history(base_daily_demand)
    n = history.size
    holdout_pred, engine = _fit_predict(history, np.arange(n - holdout_days, dtype=float), np.arange(n - holdout_days, n, dtype=float))
    future_pred, _ = _fit_predict(history, np.arange(n, dtype=float), np.arange(n, n + horizon_days, dtype=float))
    actual = history[n - holdout_days:]
    mape = float(np.mean(np.abs(actual - holdout_pred) / np.maximum(actual, 1e-6)) * 100)
    return {
        "engine": engine,
        "offsets_actual": list(range(-show_days, 0)),
        "actual": [round(float(v), 1) for v in history[n - show_days:]],
        "offsets_backtest": list(range(-holdout_days, 0)),
        "backtest": [round(float(v), 1) for v in holdout_pred],
        "offsets_forecast": list(range(0, horizon_days)),
        "forecast": [round(max(0.0, float(v)), 1) for v in future_pred],
        "holdout_mape_pct": round(mape, 2),
        "holdout_days": holdout_days,
    }


@lru_cache(maxsize=64)
def forecast(base_daily_demand: float, horizon_days: int) -> dict:
    history = _history(base_daily_demand)
    train_days = np.arange(history.size, dtype=float)
    future_days = np.arange(history.size, history.size + horizon_days, dtype=float)
    engine = "xgboost"
    try:
        from xgboost import XGBRegressor

        model = XGBRegressor(n_estimators=100, max_depth=3, learning_rate=0.06, subsample=0.9, random_state=42, n_jobs=1)
        model.fit(_features(train_days), history)
        predicted = model.predict(_features(future_days))
        fitted = model.predict(_features(train_days))
    except ImportError:  # pragma: no cover - minimal emergency install only
        engine = "linear-fallback"
        coefficients = np.polyfit(train_days, history, 1)
        predicted = np.polyval(coefficients, future_days)
        fitted = np.polyval(coefficients, train_days)
    mae = float(np.mean(np.abs(history - fitted)))
    values = [round(max(0.0, float(value)), 2) for value in predicted]
    return {
        "engine": engine,
        "horizon_days": horizon_days,
        "daily_forecast": values,
        "total_forecast": round(sum(values), 2),
        "training_rows": int(history.size),
        "training_mae": round(mae, 3),
        "model_scope": "synthetic POC history; replace with approved SAP billing history before production",
    }

