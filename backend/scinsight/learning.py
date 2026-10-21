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

import numpy as np
from fastapi import HTTPException
from sklearn.ensemble import GradientBoostingRegressor

from backend.scinsight.db import Database, now_iso

MODEL_NAME = "supplier_lead_time"


def _rows(db: Database, tenant: str) -> list[dict]:
    rows = db.query("select po.*, si.contract_lead_time_days from purchase_orders po join supplier_items si on si.tenant_id=po.tenant_id "
                    "and si.supplier_id=po.supplier_id and si.material_id=po.material_id where po.tenant_id=? and po.received_date is not null "
                    "order by po.order_date, po.po_id", (tenant,))
    seen, out = set(), []
    for r in rows:  # duplicate receipts are counted once
        if r["po_id"] in seen:
            continue
        seen.add(r["po_id"])
        r["lead"] = (date.fromisoformat(r["received_date"]) - date.fromisoformat(r["order_date"])).days
        out.append(r)
    return out


def _features(rows: list[dict], suppliers: list[str]) -> np.ndarray:
    return np.array([[1.0 if r["supplier_id"] == s else 0.0 for s in suppliers] + [math.log1p(float(r["quantity"])),
                     float(date.fromisoformat(r["order_date"]).month), float(r["contract_lead_time_days"])] for r in rows])


def train_lead_time_model(db: Database, tenant: str, user_id: str) -> dict:
    rows = _rows(db, tenant)
    if len(rows) < 20:
        raise HTTPException(status_code=409, detail=f"only {len(rows)} goods receipts; at least 20 are needed for a meaningful holdout")
    cut = int(len(rows) * 0.75)
    train, hold = rows[:cut], rows[cut:]
    suppliers = sorted({r["supplier_id"] for r in rows})
    model = GradientBoostingRegressor(n_estimators=150, max_depth=2, learning_rate=0.05, random_state=7)
    model.fit(_features(train, suppliers), [r["lead"] for r in train])
    actual = np.array([r["lead"] for r in hold], dtype=float)
    pred = model.predict(_features(hold, suppliers))
    sup_mean = {s: float(np.mean([r["lead"] for r in train if r["supplier_id"] == s])) for s in suppliers if any(r["supplier_id"] == s for r in train)}
    overall = float(np.mean([r["lead"] for r in train]))
    base_contract = np.array([float(r["contract_lead_time_days"]) for r in hold])
    base_mean = np.array([sup_mean.get(r["supplier_id"], overall) for r in hold])
    mae = lambda p: round(float(np.mean(np.abs(actual - p))), 3)  # noqa: E731
    metrics = {"mae_days": mae(pred), "bias_days": round(float(np.mean(pred - actual)), 3)}
    baselines = {"contract_lead_time_mae_days": mae(base_contract), "supplier_mean_mae_days": mae(base_mean)}
    version = f"lt-gbr-{now_iso()[:10]}-{uuid.uuid4().hex[:6]}"
    mid = f"MV-{uuid.uuid4().hex[:10].upper()}"
    db.execute("insert into model_versions(id,tenant_id,model_name,version,algorithm,trained_at,train_rows,holdout_rows,metrics,baseline_metrics,status) "
               "values(?,?,?,?,?,?,?,?,?,?,?)",
               (mid, tenant, MODEL_NAME, version, "sklearn GradientBoostingRegressor(n=150, depth=2, lr=0.05, seed=7); features: supplier one-hot, "
                "log(quantity), order month, contract lead time", now_iso(), len(train), len(hold), json.dumps({**metrics, "suppliers": suppliers}), json.dumps(baselines), "candidate"))
    best_baseline = min(baselines.values())
    return {"model_version_id": mid, "version": version, "status": "candidate", "train_rows": len(train), "holdout_rows": len(hold),
            "metrics": metrics, "baselines": baselines, "beats_best_baseline": metrics["mae_days"] < best_baseline,
            "note": "Synthetic history: results demonstrate the governed pipeline, not real supplier performance. Promotion is manual."}


def promote(db: Database, tenant: str, model_id: str, user_id: str) -> dict:
    row = db.one("select * from model_versions where id=? and tenant_id=?", (model_id, tenant))
    if row is None:
        raise HTTPException(status_code=404, detail="model version not found")
    if row["status"] != "candidate":
        raise HTTPException(status_code=409, detail=f"model version is {row['status']}")
    metrics, baselines = json.loads(row["metrics"]), json.loads(row["baseline_metrics"])
    if metrics["mae_days"] >= min(baselines.values()):
        db.execute("update model_versions set status='rejected' where id=?", (model_id,))
        raise HTTPException(status_code=409, detail=f"promotion gate: model MAE {metrics['mae_days']} does not beat the best baseline {min(baselines.values())}; rejected")
    db.transaction([("update model_versions set status='superseded' where tenant_id=? and model_name=? and status='promoted'", (tenant, row["model_name"])),
                    ("update model_versions set status='promoted', promoted_by=?, promoted_at=? where id=?", (user_id, now_iso(), model_id))])
    return {**db.one("select * from model_versions where id=?", (model_id,)), "gate": "passed: beats best baseline on the holdout"}


def predict_lead_time(db: Database, tenant: str, model_row: dict, supplier_id: str, quantity: float, on: date) -> float | None:
    """Re-fit the promoted configuration deterministically on all receipts and predict (no pickles: reproducible from data)."""
    rows = _rows(db, tenant)
    suppliers = json.loads(model_row["metrics"]).get("suppliers") or sorted({r["supplier_id"] for r in rows})
    if supplier_id not in suppliers:
        return None
    contract = db.one("select contract_lead_time_days from supplier_items where tenant_id=? and supplier_id=? order by material_id limit 1", (tenant, supplier_id))
    model = GradientBoostingRegressor(n_estimators=150, max_depth=2, learning_rate=0.05, random_state=7)
    model.fit(_features(rows, suppliers), [r["lead"] for r in rows])
    x = _features([{"supplier_id": supplier_id, "quantity": quantity, "order_date": on.isoformat(), "contract_lead_time_days": contract["contract_lead_time_days"]}], suppliers)
    return round(float(model.predict(x)[0]), 1)


def retraining_request(db: Database, tenant: str, user_id: str, reason: str) -> dict:
    verified = db.query("select * from learning_records where tenant_id=? and approved_for_training=1", (tenant,))
    rid = f"RR-{uuid.uuid4().hex[:10].upper()}"
    evidence = {"verified_learning_records": len(verified), "mean_abs_error_days": round(sum(r["abs_error"] for r in verified) / len(verified), 2) if verified else None}
    db.execute("insert into retraining_requests(id,tenant_id,model_name,reason,evidence,status,requested_by,created_at) values(?,?,?,?,?,?,?,?)",
               (rid, tenant, MODEL_NAME, reason[:1000], json.dumps(evidence), "pending_human_approval", user_id, now_iso()))
    return {"id": rid, "status": "pending_human_approval", "evidence": evidence,
            "note": "A request only. Training runs on POST /api/v1/learning/train-lead-time-model by an MLOps engineer; promotion needs the director."}
