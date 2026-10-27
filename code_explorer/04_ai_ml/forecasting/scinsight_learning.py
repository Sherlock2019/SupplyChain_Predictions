# ======================================================================================================
# ANNOTATED COPY (learning only: never imported, never executed)
# ORIGINAL FILE: backend/scinsight/learning.py
# What this module is: governed ML for SCInsight — a reproducible supplier lead-time model (scikit-learn gradient
# boosting) trained on SAP goods receipts with a time-based holdout, compared to two baselines, stored as a CANDIDATE,
# and promotable only by a human director through a gate (must beat the best baseline).
# Only comment lines were added (AST-verified).
# ======================================================================================================

"""Governed learning: a small, reproducible supplier lead-time model with a holdout evaluation and a manual promotion gate.

Training data = SAP goods receipts (order date -> receipt date) — the synthetic history in the POC. Split by time: the
latest 25% of orders form the holdout. Baselines: (a) contract lead time, (b) supplier mean on the training set. A model
version is stored as a CANDIDATE; only a human director can promote it, and only if it beats the best baseline on the
holdout. One verified outcome never "proves" an improvement; the metrics come from the holdout set.
"""
from __future__ import annotations

import json
import math
import uuid
from datetime import date

# numpy: arrays for features / metrics. GradientBoostingRegressor: tree-ensemble regressor from scikit-learn.
import numpy as np
from fastapi import HTTPException
from sklearn.ensemble import GradientBoostingRegressor

from backend.scinsight.db import Database, now_iso

# Model family name stored in model_versions.
MODEL_NAME = "supplier_lead_time"


# ===== FUNCTION: _rows() =====
# ID: F0532 · function · used
# ORIGINAL FILE: backend/scinsight/learning.py:24-35
# ROLE: Training rows = received POs joined with their contract lead time, ordered by order date, deduplicated, with the
#       actual lead time in days added as "lead".
# INPUTS:
#   db: Database, tenant: str.
# OUTPUT:
#   list[dict] -> purchase_orders rows + contract_lead_time_days + lead.
# CALLED BY:
#   <- F0534 train_lead_time_model() (calls)
#   <- F0536 predict_lead_time() (calls)
# CALLS:
#   -> F0418 Database (references)
#   -> F0421 Database.query() (calls)
def _rows(db: Database, tenant: str) -> list[dict]:
    rows = db.query("select po.*, si.contract_lead_time_days from purchase_orders po join supplier_items si on si.tenant_id=po.tenant_id "
                    "and si.supplier_id=po.supplier_id and si.material_id=po.material_id where po.tenant_id=? and po.received_date is not null "
                    "order by po.order_date, po.po_id", (tenant,))
    seen, out = set(), []
    for r in rows:  # duplicate receipts are counted once
        if r["po_id"] in seen:
            continue
        seen.add(r["po_id"])
        # Label: receipt date - order date, in days.
        r["lead"] = (date.fromisoformat(r["received_date"]) - date.fromisoformat(r["order_date"])).days
        out.append(r)
    return out


# ===== FUNCTION: _features() =====
# ID: F0533 · function · used
# ORIGINAL FILE: backend/scinsight/learning.py:38-40
# ROLE: Feature matrix: supplier one-hot + log(1 + quantity) + order month + contract lead time.
# INPUTS:
#   rows: list[dict], suppliers: list[str] (fixed column order of the one-hot part).
# OUTPUT:
#   np.ndarray -> shape (n_rows, len(suppliers) + 3).
# CALLED BY:
#   <- F0534 train_lead_time_model() (calls)
#   <- F0536 predict_lead_time() (calls)
# CALLS:
#   (none found)
def _features(rows: list[dict], suppliers: list[str]) -> np.ndarray:
    # List concatenation inside the comprehension builds one feature row per PO.
    return np.array([[1.0 if r["supplier_id"] == s else 0.0 for s in suppliers] + [math.log1p(float(r["quantity"])),
                     float(date.fromisoformat(r["order_date"]).month), float(r["contract_lead_time_days"])] for r in rows])


# ===== FUNCTION: train_lead_time_model() =====
# ID: F0534 · function · used
# ORIGINAL FILE: backend/scinsight/learning.py:43-70
# ROLE: Train a CANDIDATE lead-time model: time split 75/25, fit gradient boosting, compute MAE/bias on the holdout and the
#       MAE of two baselines (contract lead time, supplier mean); store a model_versions row with status "candidate".
# INPUTS:
#   db: Database, tenant: str, user_id: str (who trained it — kept for the route's audit).
# OUTPUT:
#   dict -> model_version_id, version, status, train_rows, holdout_rows, metrics, baselines, beats_best_baseline, note.
# RAISES:
#   HTTPException 409 when there are fewer than 20 receipts.
# CALLED BY:
#   <- F2024 create_router.train() (calls)
# CALLS:
#   -> F0418 Database (references)
#   -> F0532 _rows() (calls)
#   -> F0533 _features() (calls)
#   -> F0416 now_iso() (calls)
#   -> F0423 Database.execute() (calls)
def train_lead_time_model(db: Database, tenant: str, user_id: str) -> dict:
    rows = _rows(db, tenant)
    if len(rows) < 20:
        raise HTTPException(status_code=409, detail=f"only {len(rows)} goods receipts; at least 20 are needed for a meaningful holdout")
    # Rows are sorted by order date -> the latest 25% are the holdout (no future data leaks into training).
    cut = int(len(rows) * 0.75)
    train, hold = rows[:cut], rows[cut:]
    suppliers = sorted({r["supplier_id"] for r in rows})
    # Small, fixed hyper-parameters and random_state=7 -> fully reproducible.
    model = GradientBoostingRegressor(n_estimators=150, max_depth=2, learning_rate=0.05, random_state=7)
    model.fit(_features(train, suppliers), [r["lead"] for r in train])
    actual = np.array([r["lead"] for r in hold], dtype=float)
    pred = model.predict(_features(hold, suppliers))
    # Baseline (b): mean lead per supplier on the TRAINING set (suppliers absent from training fall back to the overall mean).
    sup_mean = {s: float(np.mean([r["lead"] for r in train if r["supplier_id"] == s])) for s in suppliers if any(r["supplier_id"] == s for r in train)}
    overall = float(np.mean([r["lead"] for r in train]))
    base_contract = np.array([float(r["contract_lead_time_days"]) for r in hold])
    base_mean = np.array([sup_mean.get(r["supplier_id"], overall) for r in hold])
    # Mean absolute error helper (lambda assigned to a name).
    mae = lambda p: round(float(np.mean(np.abs(actual - p))), 3)  # noqa: E731
    metrics = {"mae_days": mae(pred), "bias_days": round(float(np.mean(pred - actual)), 3)}
    baselines = {"contract_lead_time_mae_days": mae(base_contract), "supplier_mean_mae_days": mae(base_mean)}
    version = f"lt-gbr-{now_iso()[:10]}-{uuid.uuid4().hex[:6]}"
    mid = f"MV-{uuid.uuid4().hex[:10].upper()}"
    # The algorithm column documents the exact configuration; the suppliers list is kept in metrics for re-fitting.
    db.execute("insert into model_versions(id,tenant_id,model_name,version,algorithm,trained_at,train_rows,holdout_rows,metrics,baseline_metrics,status) "
               "values(?,?,?,?,?,?,?,?,?,?,?)",
               (mid, tenant, MODEL_NAME, version, "sklearn GradientBoostingRegressor(n=150, depth=2, lr=0.05, seed=7); features: supplier one-hot, "
                "log(quantity), order month, contract lead time", now_iso(), len(train), len(hold), json.dumps({**metrics, "suppliers": suppliers}), json.dumps(baselines), "candidate"))
    best_baseline = min(baselines.values())
    return {"model_version_id": mid, "version": version, "status": "candidate", "train_rows": len(train), "holdout_rows": len(hold),
            "metrics": metrics, "baselines": baselines, "beats_best_baseline": metrics["mae_days"] < best_baseline,
            "note": "Synthetic history: results demonstrate the governed pipeline, not real supplier performance. Promotion is manual."}


# ===== FUNCTION: promote() =====
# ID: F0535 · function · used
# ORIGINAL FILE: backend/scinsight/learning.py:73-85
# ROLE: Promotion gate: a candidate is promoted only if its holdout MAE beats the best baseline; otherwise it is rejected.
#       The previously promoted model is superseded in the same transaction.
# INPUTS:
#   db: Database, tenant: str, model_id: str, user_id: str (the director).
# OUTPUT:
#   dict -> promoted model_versions row + {"gate": "passed: ..."}.
# RAISES:
#   HTTPException 404 (unknown), 409 (not a candidate / gate failed).
# CALLED BY:
#   <- F2025 create_router.promote() (calls)
# CALLS:
#   -> F0418 Database (references)
#   -> F0422 Database.one() (calls)
#   -> F0423 Database.execute() (calls)
#   -> F0425 Database.transaction() (calls)
#   -> F0416 now_iso() (calls)
def promote(db: Database, tenant: str, model_id: str, user_id: str) -> dict:
    row = db.one("select * from model_versions where id=? and tenant_id=?", (model_id, tenant))
    if row is None:
        raise HTTPException(status_code=404, detail="model version not found")
    if row["status"] != "candidate":
        raise HTTPException(status_code=409, detail=f"model version is {row['status']}")
    metrics, baselines = json.loads(row["metrics"]), json.loads(row["baseline_metrics"])
    if metrics["mae_days"] >= min(baselines.values()):
        # Record the rejection, then refuse.
        db.execute("update model_versions set status='rejected' where id=?", (model_id,))
        raise HTTPException(status_code=409, detail=f"promotion gate: model MAE {metrics['mae_days']} does not beat the best baseline {min(baselines.values())}; rejected")
    db.transaction([("update model_versions set status='superseded' where tenant_id=? and model_name=? and status='promoted'", (tenant, row["model_name"])),
                    ("update model_versions set status='promoted', promoted_by=?, promoted_at=? where id=?", (user_id, now_iso(), model_id))])
    return {**db.one("select * from model_versions where id=?", (model_id,)), "gate": "passed: beats best baseline on the holdout"}


# ===== FUNCTION: predict_lead_time() =====
# ID: F0536 · function · used
# ORIGINAL FILE: backend/scinsight/learning.py:88-98
# ROLE: Prediction with the PROMOTED configuration: re-fit deterministically on all receipts (no pickled model files) and predict
#       the lead time for a supplier / quantity / order date.
# INPUTS:
#   db: Database, tenant: str, model_row: dict (promoted model_versions row), supplier_id: str, quantity: float, on: date.
# OUTPUT:
#   float | None -> predicted days (1 decimal); None when the supplier was not in the model's feature set.
# CALLED BY:
#   <- F0332 Service.lead_time() (calls)
# CALLS:
#   -> F0418 Database (references)
#   -> F0532 _rows() (calls)
#   -> F0422 Database.one() (calls)
#   -> F0533 _features() (calls)
def predict_lead_time(db: Database, tenant: str, model_row: dict, supplier_id: str, quantity: float, on: date) -> float | None:
    """Re-fit the promoted configuration deterministically on all receipts and predict (no pickles: reproducible from data)."""
    rows = _rows(db, tenant)
    suppliers = json.loads(model_row["metrics"]).get("suppliers") or sorted({r["supplier_id"] for r in rows})
    if supplier_id not in suppliers:
        return None
    contract = db.one("select contract_lead_time_days from supplier_items where tenant_id=? and supplier_id=? order by material_id limit 1", (tenant, supplier_id))
    model = GradientBoostingRegressor(n_estimators=150, max_depth=2, learning_rate=0.05, random_state=7)
    model.fit(_features(rows, suppliers), [r["lead"] for r in rows])
    # One synthetic feature row for the request.
    x = _features([{"supplier_id": supplier_id, "quantity": quantity, "order_date": on.isoformat(), "contract_lead_time_days": contract["contract_lead_time_days"]}], suppliers)
    return round(float(model.predict(x)[0]), 1)


# ===== FUNCTION: retraining_request() =====
# ID: F0537 · function · used
# ORIGINAL FILE: backend/scinsight/learning.py:101-108
# ROLE: Record a retraining REQUEST with evidence (verified learning records, their mean absolute error); training is separate.
# INPUTS:
#   db: Database, tenant: str, user_id: str, reason: str.
# OUTPUT:
#   dict -> {"id": "RR-...", "status": "pending_human_approval", "evidence", "note"}.
# CALLED BY:
#   <- F2026 create_router.retraining() (calls)
# CALLS:
#   -> F0418 Database (references)
#   -> F0421 Database.query() (calls)
#   -> F0423 Database.execute() (calls)
#   -> F0416 now_iso() (calls)
def retraining_request(db: Database, tenant: str, user_id: str, reason: str) -> dict:
    verified = db.query("select * from learning_records where tenant_id=? and approved_for_training=1", (tenant,))
    rid = f"RR-{uuid.uuid4().hex[:10].upper()}"
    evidence = {"verified_learning_records": len(verified), "mean_abs_error_days": round(sum(r["abs_error"] for r in verified) / len(verified), 2) if verified else None}
    db.execute("insert into retraining_requests(id,tenant_id,model_name,reason,evidence,status,requested_by,created_at) values(?,?,?,?,?,?,?,?)",
               (rid, tenant, MODEL_NAME, reason[:1000], json.dumps(evidence), "pending_human_approval", user_id, now_iso()))
    return {"id": rid, "status": "pending_human_approval", "evidence": evidence,
            "note": "A request only. Training runs on POST /api/v1/learning/train-lead-time-model by an MLOps engineer; promotion needs the director."}
