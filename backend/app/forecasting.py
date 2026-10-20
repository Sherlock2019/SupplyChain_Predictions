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


def _errors(actual: np.ndarray, predicted: np.ndarray) -> dict:
    err = predicted - actual
    total = float(np.sum(actual)) or 1e-6
    return {"wape_pct": round(float(np.sum(np.abs(err)) / total * 100), 2), "bias_pct": round(float(np.sum(err) / total * 100), 2),
            "mae": round(float(np.mean(np.abs(err))), 2)}


@lru_cache(maxsize=64)
def evaluate_models(base_daily_demand: float, holdout_days: int = 14) -> dict:
    """Model quality on the same holdout: XGBoost vs a seasonal-naive baseline (same weekday last week).
    Drift = error on the most recent 7 days vs the 7 days before (both out of sample)."""
    history = _history(base_daily_demand)
    n = history.size
    days = np.arange(n - holdout_days, n, dtype=float)
    xgb, engine = _fit_predict(history, np.arange(n - holdout_days, dtype=float), days)
    actual = history[n - holdout_days:]
    naive = history[n - holdout_days - 7:n - 7]
    model, baseline = _errors(actual, xgb), _errors(actual, naive)
    half = holdout_days // 2
    earlier, recent = _errors(actual[:half], xgb[:half]), _errors(actual[half:], xgb[half:])
    return {
        "engine": engine, "holdout_days": holdout_days, "model": model, "baseline": {"name": "seasonal naive (same weekday last week)", **baseline},
        "error_reduction_pct": round(100 * (1 - model["wape_pct"] / baseline["wape_pct"]), 1) if baseline["wape_pct"] else None,
        "drift": {"earlier_wape_pct": earlier["wape_pct"], "recent_wape_pct": recent["wape_pct"],
                  "change_pts": round(recent["wape_pct"] - earlier["wape_pct"], 2)},
        "demand_cv_pct": round(float(np.std(history[-28:]) / np.mean(history[-28:]) * 100), 1),
    }


@lru_cache(maxsize=256)
def pooled_evaluation(target_bases: tuple[float, ...], donor_bases: tuple[float, ...], include_target: bool,
                      scale_by_history: bool = True, holdout_days: int = 14) -> dict | None:
    """Train one model on demand-normalised series from several customers and score it on the target customer's holdout.

    include_target=False: the target's history is not used for training. scale_by_history=False is a cold start: the
    forecast is scaled by the planned daily demand level only (what a newly onboarded customer has on day one).
    Returns None without training data."""
    n = _history(1.0).size
    xs, ys = [], []
    for base in donor_bases:  # other (consenting) customers: their full history
        history = _history(base)
        xs.append(_features(np.arange(n, dtype=float)))
        ys.append(history / history[:n - holdout_days].mean())
    if include_target:
        for base in target_bases:  # the target's own history, never its holdout
            history = _history(base)
            days = np.arange(n - holdout_days, dtype=float)
            xs.append(_features(days))
            ys.append(history[: n - holdout_days] / history[: n - holdout_days].mean())
    if not xs or not target_bases:
        return None
    from xgboost import XGBRegressor

    model = XGBRegressor(n_estimators=100, max_depth=3, learning_rate=0.06, subsample=0.9, random_state=42, n_jobs=1)
    model.fit(np.vstack(xs), np.concatenate(ys))
    holdout = np.arange(n - holdout_days, n, dtype=float)
    abs_err = total = 0.0
    for base in target_bases:
        history = _history(base)
        scale = history[: n - holdout_days].mean() if scale_by_history else base
        predicted = model.predict(_features(holdout)) * scale
        actual = history[n - holdout_days:]
        abs_err += float(np.sum(np.abs(predicted - actual)))
        total += float(np.sum(actual))
    return {"wape_pct": round(100 * abs_err / total, 2), "series": len(target_bases), "training_series": len(donor_bases) + (len(target_bases) if include_target else 0)}


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

