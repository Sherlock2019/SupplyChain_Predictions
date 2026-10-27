"""Configuration versions, background jobs and experiment records (tables from migration 0003_rag_tuning.sql)."""
from __future__ import annotations

import json
import threading
import traceback
import uuid

from backend.scinsight.db import Database, now_iso
from backend.scinsight.rag_tuning.config import RagTuningConfig, diff


def _id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8].upper()}"


def _row(r: dict | None) -> dict | None:
    if r is None:
        return None
    out = dict(r)
    for k in ("config", "validation", "flowise_sync"):
        if out.get(k):
            out[k] = json.loads(out[k])
    out.pop("flowise_backup", None)  # the saved chatflow JSON is large and internal; it is kept for rollback only
    return out


class Registry:
    def __init__(self, db: Database, kb):
        self.db, self.kb = db, kb

    # ------------------------------------------------------------------ configuration versions
    def ensure_baseline(self, tenant_id: str) -> None:
        # The configuration that ran before tuning is recorded once as the first active version (so it can be rolled back to).
        if self.db.one("select id from rag_config_versions where tenant_id=?", (tenant_id,)) is None:
            self.db.execute("insert into rag_config_versions(id,tenant_id,status,config,index_version,name,notes,created_by,created_at,published_by,published_at) "
                            "values(?,?,?,?,?,?,?,?,?,?,?)",
                            (_id("RCFG"), tenant_id, "active", self.kb.baseline().model_dump_json(), "baseline", "baseline",
                             "configuration before RAG tuning (backend/scinsight/rag.py)", "system", now_iso(), "system", now_iso()))

    def get_active_rag_config(self, tenant_id: str) -> dict:
        self.ensure_baseline(tenant_id)
        return _row(self.db.one("select * from rag_config_versions where tenant_id=? and status='active'", (tenant_id,)))

    def get(self, tenant_id: str, config_id: str) -> dict:
        row = _row(self.db.one("select * from rag_config_versions where tenant_id=? and id=?", (tenant_id, config_id)))
        if row is None:
            raise KeyError(config_id)
        return row

    def history(self, tenant_id: str) -> list[dict]:
        self.ensure_baseline(tenant_id)
        return [_row(r) for r in self.db.query("select * from rag_config_versions where tenant_id=? order by created_at desc", (tenant_id,))]

    def save_draft_config(self, tenant_id: str, user_id: str, cfg: RagTuningConfig, name: str, notes: str = "") -> dict:
        """Store a validated draft and say how it differs from the active configuration (and whether it needs a new index)."""
        active = self.get_active_rag_config(tenant_id)
        delta = diff(active["config"], cfg.model_dump())
        # Hot-only drafts can reuse the active index; cold changes get their own index version when it is built.
        index_version = None if delta["needs_new_index"] else active["index_version"]
        cid = _id("RCFG")
        self.db.execute("insert into rag_config_versions(id,tenant_id,status,config,index_version,name,notes,created_by,created_at) values(?,?,?,?,?,?,?,?,?)",
                        (cid, tenant_id, "draft", cfg.model_dump_json(), index_version, name[:80] or cid, notes[:500], user_id, now_iso()))
        return {**self.get(tenant_id, cid), "diff": delta}

    def set_status(self, config_id: str, status: str, **fields) -> None:
        sets = ", ".join(["status=?"] + [f"{k}=?" for k in fields])
        values = [status] + [json.dumps(v) if isinstance(v, (dict, list)) else v for v in fields.values()]
        self.db.execute(f"update rag_config_versions set {sets} where id=?", (*values, config_id))

    # ------------------------------------------------------------------ jobs
    def start_job(self, tenant_id: str, user_id: str, kind: str, params: dict, fn, inline: bool = False) -> dict:
        """Run fn() in a background thread (HTTP returns at once; the console polls the job)."""
        jid = _id("JOB")
        self.db.execute("insert into rag_jobs(id,tenant_id,kind,status,created_by,created_at,params) values(?,?,?,?,?,?,?)",
                        (jid, tenant_id, kind, "running", user_id, now_iso(), json.dumps(params)))

        def run():
            try:
                result = fn()
                self.db.execute("update rag_jobs set status='done', finished_at=?, result=? where id=?", (now_iso(), json.dumps(result, default=str), jid))
            except Exception as exc:  # noqa: BLE001 - every failure is reported on the job, never swallowed
                self.db.execute("update rag_jobs set status='failed', finished_at=?, error=? where id=?",
                                (now_iso(), f"{type(exc).__name__}: {exc}"[:2000], jid))
                traceback.print_exc()
        if inline:
            run()
        else:
            threading.Thread(target=run, name=f"rag-{kind}-{jid}", daemon=True).start()
        return self.job(tenant_id, jid)

    def job(self, tenant_id: str, job_id: str) -> dict:
        r = self.db.one("select * from rag_jobs where tenant_id=? and id=?", (tenant_id, job_id))
        if r is None:
            raise KeyError(job_id)
        return {**r, "params": json.loads(r["params"]), "result": json.loads(r["result"]) if r["result"] else None}

    # ------------------------------------------------------------------ experiments
    def save_experiment(self, tenant_id: str, user_id: str, config_id: str, dataset_version: str, params: dict, summary: dict, cases: list) -> str:
        eid = _id("EXP")
        self.db.execute("insert into rag_experiments(id,tenant_id,config_id,dataset_version,created_by,created_at,params,summary,cases) values(?,?,?,?,?,?,?,?,?)",
                        (eid, tenant_id, config_id, dataset_version, user_id, now_iso(), json.dumps(params), json.dumps(summary), json.dumps(cases)))
        return eid

    def experiments(self, tenant_id: str, config_id: str | None = None) -> list[dict]:
        rows = self.db.query("select id, config_id, dataset_version, created_by, created_at, params, summary from rag_experiments where tenant_id=? "
                             + ("and config_id=? " if config_id else "") + "order by created_at desc", (tenant_id, config_id) if config_id else (tenant_id,))
        return [{**r, "params": json.loads(r["params"]), "summary": json.loads(r["summary"])} for r in rows]

    def experiment(self, tenant_id: str, exp_id: str) -> dict:
        r = self.db.one("select * from rag_experiments where tenant_id=? and id=?", (tenant_id, exp_id))
        if r is None:
            raise KeyError(exp_id)
        return {**r, "params": json.loads(r["params"]), "summary": json.loads(r["summary"]), "cases": json.loads(r["cases"])}
