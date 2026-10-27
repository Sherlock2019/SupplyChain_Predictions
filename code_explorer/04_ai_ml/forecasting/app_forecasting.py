# ======================================================================================================
# ANNOTATED COPY (learning only: never imported, never executed)
# ORIGINAL FILE: backend/app/forecasting.py
# What this module is: the XGBoost demand-forecast pipeline of the SPARC gateway: a reproducible synthetic 180-day history per
# demand series, calendar features, training / prediction, back-test (MAPE), model evaluation vs a seasonal-naive baseline with
# drift, and pooled (multi-customer) evaluation for the "industry learning" view. Results are cached (lru_cache).
# Only comment lines were added (AST-verified).
# ======================================================================================================

"""Small deterministic training pipeline using XGBoost for the POC demand forecast."""
from __future__ import annotations

import math
# lru_cache: identical inputs -> cached result (training is deterministic, so caching is safe).
from functools import lru_cache

import numpy as np


# ===== FUNCTION: _history() =====
# ID: F0524 · function · used
# ORIGINAL FILE: backend/app/forecasting.py:10-13
# ROLE: Synthetic daily demand history: base level x (1 + slight trend + weekly + monthly seasonality).
# INPUTS:
#   base: float (average units per day), days: int (180).
# OUTPUT:
#   np.ndarray -> one value per day.
# CALLED BY:
#   <- F0527 backtest() (calls)
#   <- F0529 evaluate_models() (calls)
#   <- F0530 pooled_evaluation() (calls)
#   <- F0531 forecast() (calls)
# CALLS:
#   (none found)
def _history(base: float, days: int = 180) -> np.ndarray:
    # Reproducible synthetic SAP history with weekly seasonality and a mild trend.
    x = np.arange(days, dtype=float)
    return base * (1 + 0.0015 * x + 0.16 * np.sin(2 * math.pi * x / 7) + 0.05 * np.sin(2 * math.pi * x / 30))


# ===== FUNCTION: _features() =====
# ID: F0525 · function · used
# ORIGINAL FILE: backend/app/forecasting.py:16-25
# ROLE: Feature matrix for day indexes: trend + sin/cos of the weekly and monthly cycles.
# INPUTS:
#   day_indexes: np.ndarray.
# OUTPUT:
#   np.ndarray -> shape (n, 5).
# CALLED BY:
#   <- F0526 _fit_predict() (calls)
#   <- F0530 pooled_evaluation() (calls)
#   <- F0531 forecast() (calls)
# CALLS:
#   (none found)
def _features(day_indexes: np.ndarray) -> np.ndarray:
    # column_stack: put the 5 one-dimensional arrays side by side as columns.
    return np.column_stack(
        [
            day_indexes,
            np.sin(2 * math.pi * day_indexes / 7),
            np.cos(2 * math.pi * day_indexes / 7),
            np.sin(2 * math.pi * day_indexes / 30),
            np.cos(2 * math.pi * day_indexes / 30),
        ]
    )


# ===== FUNCTION: _fit_predict() =====
# ID: F0526 · function · used
# ORIGINAL FILE: backend/app/forecasting.py:28-37
# ROLE: Fit on train_days and predict predict_days with XGBoost (fallback: a linear trend if xgboost is not installed).
# INPUTS:
#   history: np.ndarray, train_days: np.ndarray, predict_days: np.ndarray.
# OUTPUT:
#   tuple[np.ndarray, str] -> (predictions, engine name).
# CALLED BY:
#   <- F0527 backtest() (calls)
#   <- F0529 evaluate_models() (calls)
# CALLS:
#   -> F0525 _features() (calls)
def _fit_predict(history: np.ndarray, train_days: np.ndarray, predict_days: np.ndarray) -> tuple[np.ndarray, str]:
    try:
        from xgboost import XGBRegressor

        # Fixed hyper-parameters and random_state=42, n_jobs=1 -> identical results on every run.
        model = XGBRegressor(n_estimators=100, max_depth=3, learning_rate=0.06, subsample=0.9, random_state=42, n_jobs=1)
        # history[train_days.astype(int)]: the target values of the training days (fancy indexing).
        model.fit(_features(train_days), history[train_days.astype(int)])
        return model.predict(_features(predict_days)), "xgboost"
    except ImportError:  # pragma: no cover
        coefficients = np.polyfit(train_days, history[train_days.astype(int)], 1)
        return np.polyval(coefficients, predict_days), "linear-fallback"


# ===== FUNCTION: backtest() =====
# ID: F0527 · function · used
# ORIGINAL FILE: backend/app/forecasting.py:40-59
# ROLE: Forecast vs actuals for charts: train without the last `holdout_days`, predict them (back-test, MAPE), then retrain on all
#       days and forecast the future horizon.
# INPUTS:
#   base_daily_demand: float, holdout_days: int (14), horizon_days: int (14), show_days: int (45 days of actuals shown).
# OUTPUT:
#   dict -> engine, offsets_*/actual/backtest/forecast series, holdout_mape_pct, holdout_days.
# CALLED BY:
#   <- F0209 SupplyChainEngine.forecast_vs_actuals() (calls)
# CALLS:
#   -> F0524 _history() (calls)
#   -> F0526 _fit_predict() (calls)
@lru_cache(maxsize=64)
def backtest(base_daily_demand: float, holdout_days: int = 14, horizon_days: int = 14, show_days: int = 45) -> dict:
    """Forecast vs actuals: train without the last `holdout_days`, predict them, then forecast the future horizon."""
    history = _history(base_daily_demand)
    n = history.size
    holdout_pred, engine = _fit_predict(history, np.arange(n - holdout_days, dtype=float), np.arange(n - holdout_days, n, dtype=float))
    future_pred, _ = _fit_predict(history, np.arange(n, dtype=float), np.arange(n, n + horizon_days, dtype=float))
    actual = history[n - holdout_days:]
    # MAPE = mean(|actual - predicted| / actual) x 100 (np.maximum avoids division by zero).
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


# ===== FUNCTION: _errors() =====
# ID: F0528 · function · used
# ORIGINAL FILE: backend/app/forecasting.py:62-66
# ROLE: Error metrics: WAPE %, bias %, MAE.
# INPUTS:
#   actual: np.ndarray, predicted: np.ndarray.
# OUTPUT:
#   dict.
# CALLED BY:
#   <- F0529 evaluate_models() (calls)
# CALLS:
#   (none found)
def _errors(actual: np.ndarray, predicted: np.ndarray) -> dict:
    err = predicted - actual
    total = float(np.sum(actual)) or 1e-6
    return {"wape_pct": round(float(np.sum(np.abs(err)) / total * 100), 2), "bias_pct": round(float(np.sum(err) / total * 100), 2),
            "mae": round(float(np.mean(np.abs(err))), 2)}


# ===== FUNCTION: evaluate_models() =====
# ID: F0529 · function · used
# ORIGINAL FILE: backend/app/forecasting.py:69-88
# ROLE: Model quality on the same holdout: XGBoost vs seasonal naive (same weekday last week), error reduction, drift
#       (error of the recent half vs the earlier half of the holdout), demand coefficient of variation.
# INPUTS:
#   base_daily_demand: float, holdout_days: int (14).
# OUTPUT:
#   dict -> engine, model, baseline, error_reduction_pct, drift, demand_cv_pct.
# CALLED BY:
#   <- F0254 MoatEngine.model_comparison() (calls)
#   <- F0261 RoleCenter._facts() (calls)
# CALLS:
#   -> F0524 _history() (calls)
#   -> F0526 _fit_predict() (calls)
#   -> F0528 _errors() (calls)
@lru_cache(maxsize=64)
def evaluate_models(base_daily_demand: float, holdout_days: int = 14) -> dict:
    """Model quality on the same holdout: XGBoost vs a seasonal-naive baseline (same weekday last week).
    Drift = error on the most recent 7 days vs the 7 days before (both out of sample)."""
    history = _history(base_daily_demand)
    n = history.size
    days = np.arange(n - holdout_days, n, dtype=float)
    xgb, engine = _fit_predict(history, np.arange(n - holdout_days, dtype=float), days)
    actual = history[n - holdout_days:]
    # Seasonal naive: the values 7 days earlier.
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


# ===== FUNCTION: pooled_evaluation() =====
# ID: F0530 · function · used
# ORIGINAL FILE: backend/app/forecasting.py:91-126
# ROLE: Pooled ("industry") model: train one XGBoost on demand-normalised series of several customers and score it on the target
#       customer's holdout; options to exclude the target's history and to simulate a cold start (scale by planned demand only).
# INPUTS:
#   target_bases: tuple[float, ...], donor_bases: tuple[float, ...], include_target: bool, scale_by_history: bool (True), holdout_days: int (14).
#   (tuples, not lists, because lru_cache needs hashable arguments)
# OUTPUT:
#   dict | None -> {"wape_pct", "series", "training_series"}, or None without training data.
# CALLED BY:
#   <- F0254 MoatEngine.model_comparison() (calls)
# CALLS:
#   -> F0524 _history() (calls)
#   -> F0525 _features() (calls)
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
        # Normalise by the series' own mean so different volume levels can be pooled.
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
    # vstack / concatenate: stack all series' rows into one training set.
    model.fit(np.vstack(xs), np.concatenate(ys))
    holdout = np.arange(n - holdout_days, n, dtype=float)
    abs_err = total = 0.0
    for base in target_bases:
        history = _history(base)
        # Scale the normalised prediction back to units: history mean (normal) or planned level (cold start).
        scale = history[: n - holdout_days].mean() if scale_by_history else base
        predicted = model.predict(_features(holdout)) * scale
        actual = history[n - holdout_days:]
        abs_err += float(np.sum(np.abs(predicted - actual)))
        total += float(np.sum(actual))
    return {"wape_pct": round(100 * abs_err / total, 2), "series": len(target_bases), "training_series": len(donor_bases) + (len(target_bases) if include_target else 0)}


# ===== FUNCTION: forecast() =====
# ID: F0531 · function · used
# ORIGINAL FILE: backend/app/forecasting.py:129-157
# ROLE: The forecast used by the engine: train on the full history and forecast `horizon_days` daily values (never negative),
#       with the in-sample training MAE.
# INPUTS:
#   base_daily_demand: float, horizon_days: int.
# OUTPUT:
#   dict -> engine, horizon_days, daily_forecast[], total_forecast, training_rows, training_mae, model_scope.
# CALLED BY:
#   <- F0198 SupplyChainEngine.stock_balance() (calls)
#   <- F0199 SupplyChainEngine.demand_forecast() (calls)
#   <- F0212 SupplyChainEngine.product_360() (calls)
# CALLS:
#   -> F0524 _history() (calls)
#   -> F0525 _features() (calls)
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
