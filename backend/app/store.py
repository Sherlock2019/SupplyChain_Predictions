"""Governance ledger: stored analyses, recommendation review queue, and a tamper-evident audit chain.

SQLite for unit tests and laptops; PostgreSQL (Compose, Amazon RDS, Cloud SQL) for every deployment.
Recommendations never touch SAP: an accepted recommendation is executed manually by an authorized planner.
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SQLITE_SCHEMA = """
create table if not exists analysis (
  id text primary key, kind text not null, request text not null, result text not null,
  snapshot_id text not null, actor text not null, created_at text not null
);
create table if not exists recommendation (
  id integer primary key autoincrement, analysis_id text unique not null references analysis(id),
  kind text not null default '', actions text not null, explanation text not null, status text not null,
  submitted_by text not null, submitted_at text not null, source text not null default 'api',
  decided_by text, decided_at text, decision_comment text
);
create table if not exists audit (
  id integer primary key autoincrement, ts text not null, actor text not null, role text not null,
  action text not null, correlation_id text, details text not null,
  prev_hash text not null, hash text not null
);
create table if not exists watch (
  id integer primary key autoincrement, owner text not null, name text not null, kind text not null, params text not null,
  threshold real not null, created_at text not null, last_value text, last_triggered integer, last_checked text
);
create table if not exists sap_document (
  id integer primary key autoincrement, doc_number text unique not null, doc_type text not null, recommendation_id integer not null,
  payload text not null, created_by text not null, created_at text not null, status text not null
);create table if not exists outcome (
  id integer primary key autoincrement, recommendation_id integer unique not null, snapshot_id text not null, kind text not null,
  expected text not null, due_date text, status text not null, achieved integer, observed text, realized_impact_eur real,
  source_document text, note text, observed_by text, observed_at text, created_at text not null
);
create table if not exists decision_feedback (
  id integer primary key autoincrement, recommendation_id integer not null, decision text not null, reason_code text,
  modified integer not null default 0, comment text, actor text not null, created_at text not null
);
create table if not exists consent (
  tenant_id text primary key, industry_learning integer not null, updated_by text not null, updated_at text not null
);
create table if not exists setting (
  key text primary key, value text not null, updated_by text not null, updated_at text not null
);"""

POSTGRES_SCHEMA = """
create table if not exists analysis (
  id text primary key, kind text not null, request text not null, result text not null,
  snapshot_id text not null, actor text not null, created_at text not null
);
create table if not exists recommendation (
  id bigint generated always as identity primary key, analysis_id text unique not null references analysis(id),
  kind text not null default '', actions text not null, explanation text not null, status text not null,
  submitted_by text not null, submitted_at text not null, source text not null default 'api',
  decided_by text, decided_at text, decision_comment text
);
create table if not exists audit (
  id bigint generated always as identity primary key, ts text not null, actor text not null, role text not null,
  action text not null, correlation_id text, details text not null,
  prev_hash text not null, hash text not null
);
create table if not exists watch (
  id bigint generated always as identity primary key, owner text not null, name text not null, kind text not null, params text not null,
  threshold double precision not null, created_at text not null, last_value text, last_triggered integer, last_checked text
);
create table if not exists sap_document (
  id bigint generated always as identity primary key, doc_number text unique not null, doc_type text not null, recommendation_id bigint not null,
  payload text not null, created_by text not null, created_at text not null, status text not null
);create table if not exists outcome (
  id bigint generated always as identity primary key, recommendation_id bigint unique not null, snapshot_id text not null, kind text not null,
  expected text not null, due_date text, status text not null, achieved integer, observed text, realized_impact_eur double precision,
  source_document text, note text, observed_by text, observed_at text, created_at text not null
);
create table if not exists decision_feedback (
  id bigint generated always as identity primary key, recommendation_id bigint not null, decision text not null, reason_code text,
  modified integer not null default 0, comment text, actor text not null, created_at text not null
);
create table if not exists consent (
  tenant_id text primary key, industry_learning integer not null, updated_by text not null, updated_at text not null
);
create table if not exists setting (
  key text primary key, value text not null, updated_by text not null, updated_at text not null
);"""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _digest(prev: str, ts: str, actor: str, role: str, action: str, correlation_id: str | None, body: str) -> str:
    return hashlib.sha256("|".join((prev, ts, actor, role, action, correlation_id or "", body)).encode()).hexdigest()


class _SqliteDb:
    dialect = "sqlite"

    def __init__(self, path: str):
        if path != ":memory:":
            Path(path).parent.mkdir(parents=True, exist_ok=True)
        self._db = sqlite3.connect(path, check_same_thread=False)
        self._db.row_factory = lambda cursor, row: {col[0]: row[i] for i, col in enumerate(cursor.description)}
        self._db.executescript(SQLITE_SCHEMA)
        self._lock = threading.RLock()

    def run(self, statements: list[tuple[str, tuple]], fetch: str = "none", serialize: bool = False) -> Any:
        with self._lock, self._db:
            result = None
            for sql, params in statements:
                cursor = self._db.execute(sql, params)
                if fetch == "one":
                    result = cursor.fetchone()
                elif fetch == "all":
                    result = cursor.fetchall()
                elif fetch == "rowcount":
                    result = cursor.rowcount
                elif fetch == "lastid":
                    result = cursor.lastrowid
            return result

    def query(self, sql: str, params: tuple = (), fetch: str = "all") -> Any:
        return self.run([(sql, params)], fetch)


class _PostgresDb:
    dialect = "postgres"

    def __init__(self, url: str):
        from psycopg.rows import dict_row
        from psycopg_pool import ConnectionPool

        self._pool = ConnectionPool(url, min_size=1, max_size=8, kwargs={"row_factory": dict_row}, open=True)
        with self._pool.connection() as connection:
            connection.execute("select pg_advisory_xact_lock(7316002)")
            for statement in filter(None, (part.strip() for part in POSTGRES_SCHEMA.split(";"))):
                connection.execute(statement)

    def run(self, statements: list[tuple[str, tuple]], fetch: str = "none", serialize: bool = False) -> Any:
        with self._pool.connection() as connection, connection.transaction():
            if serialize:
                connection.execute("select pg_advisory_xact_lock(7316003)")
            result = None
            for sql, params in statements:
                sql = sql.replace("?", "%s")
                if fetch == "lastid" and sql.lstrip().lower().startswith("insert"):
                    sql += " returning id"
                cursor = connection.execute(sql, params)
                if fetch == "one":
                    result = cursor.fetchone()
                elif fetch == "all":
                    result = cursor.fetchall()
                elif fetch == "rowcount":
                    result = cursor.rowcount
                elif fetch == "lastid" and cursor.description:
                    result = cursor.fetchone()["id"]
            return result

    def query(self, sql: str, params: tuple = (), fetch: str = "all") -> Any:
        return self.run([(sql, params)], fetch)


class Store:
    def __init__(self, database_url: str):
        if database_url.startswith("sqlite:///"):
            self._db = _SqliteDb(database_url.removeprefix("sqlite:///"))
        elif database_url.startswith(("postgresql://", "postgres://")):
            self._db = _PostgresDb(database_url)
        else:
            raise ValueError("DATABASE_URL must be sqlite:///path or postgresql://...")

    @classmethod
    def memory(cls) -> "Store":
        return cls("sqlite:///:memory:")

    @property
    def dialect(self) -> str:
        return self._db.dialect

    # ------------------------------------------------------------------ audit
    def audit(self, actor: str, role: str, action: str, details: dict, correlation_id: str | None = None) -> None:
        body = json.dumps(details, sort_keys=True, default=str, separators=(",", ":"))

        if self._db.dialect == "sqlite":
            with self._db._lock:
                prior = self._db.query("select hash from audit order by id desc limit 1", fetch="one")
                prev = prior["hash"] if prior else "0" * 64
                ts = _now()
                self._db.query(
                    "insert into audit(ts,actor,role,action,correlation_id,details,prev_hash,hash) values(?,?,?,?,?,?,?,?)",
                    (ts, actor, role, action, correlation_id, body, prev, _digest(prev, ts, actor, role, action, correlation_id, body)),
                    fetch="none",
                )
            return

        with self._db._pool.connection() as connection, connection.transaction():
            connection.execute("select pg_advisory_xact_lock(7316003)")
            prior = connection.execute("select hash from audit order by id desc limit 1").fetchone()
            prev = prior["hash"] if prior else "0" * 64
            ts = _now()
            connection.execute(
                "insert into audit(ts,actor,role,action,correlation_id,details,prev_hash,hash) values(%s,%s,%s,%s,%s,%s,%s,%s)",
                (ts, actor, role, action, correlation_id, body, prev, _digest(prev, ts, actor, role, action, correlation_id, body)),
            )

    def verify_chain(self) -> bool:
        prev = "0" * 64
        for row in self._db.query("select * from audit order by id"):
            expected = _digest(prev, row["ts"], row["actor"], row["role"], row["action"], row["correlation_id"], row["details"])
            if row["prev_hash"] != prev or row["hash"] != expected:
                return False
            prev = row["hash"]
        return True

    def audit_events(self, limit: int = 100) -> list[dict]:
        rows = self._db.query("select * from audit order by id desc limit ?", (min(limit, 1000),))
        return [{**row, "details": json.loads(row["details"])} for row in rows]

    # --------------------------------------------------------------- analyses
    def save_analysis(self, kind: str, request: dict, result: dict, snapshot_id: str, actor: str) -> str:
        analysis_id = f"AN-{uuid.uuid4().hex[:12]}"
        self._db.query(
            "insert into analysis(id,kind,request,result,snapshot_id,actor,created_at) values(?,?,?,?,?,?,?)",
            (analysis_id, kind, json.dumps(request, default=str), json.dumps(result, default=str), snapshot_id, actor, _now()),
            fetch="none",
        )
        return analysis_id

    def get_analysis(self, analysis_id: str) -> dict | None:
        row = self._db.query("select * from analysis where id=?", (analysis_id,), fetch="one")
        return None if row is None else {**row, "request": json.loads(row["request"]), "result": json.loads(row["result"])}

    def latest_actionable(self, analysis_ids: list[str], kind: str) -> dict | None:
        """Newest stored analysis of `kind` among the ids that has proposed actions (server-side selection)."""
        candidates = [a for a in (self.get_analysis(i) for i in dict.fromkeys(analysis_ids)) if a and a["kind"] == kind and a["result"].get("proposed_actions")]
        return max(candidates, key=lambda a: a["created_at"]) if candidates else None

    # --------------------------------------------------------- recommendations
    def submit(self, analysis_id: str, explanation: str, actor: str, source: str = "api") -> dict:
        analysis = self.get_analysis(analysis_id)
        if analysis is None:
            raise KeyError(analysis_id)
        actions = analysis["result"].get("proposed_actions", [])
        if not actions:
            raise ValueError("Analysis contains no proposed actions")
        existing = self._db.query("select * from recommendation where analysis_id=?", (analysis_id,), fetch="one")
        if existing:
            return self._recommendation(existing)
        rec_id = self._db.run(
            [
                (
                    "insert into recommendation(analysis_id,kind,actions,explanation,status,submitted_by,submitted_at,source) values(?,?,?,?,'pending_review',?,?,?)",
                    (analysis_id, analysis["kind"], json.dumps(actions), explanation, actor, _now(), source),
                )
            ],
            fetch="lastid",
        )
        return self.get_recommendation(int(rec_id))  # type: ignore[return-value]

    @staticmethod
    def _recommendation(row: dict) -> dict:
        return {**row, "actions": json.loads(row["actions"])}

    def get_recommendation(self, rec_id: int) -> dict | None:
        row = self._db.query("select * from recommendation where id=?", (rec_id,), fetch="one")
        return None if row is None else self._recommendation(row)

    def list_recommendations(self, status: str | None = None, snapshot_id: str | None = None) -> list[dict]:
        """Optionally only recommendations whose analysis came from one SAP snapshot (one customer)."""
        sql = "select r.* from recommendation r join analysis a on a.id = r.analysis_id where 1=1"
        params: list = []
        if status:
            sql += " and r.status=?"
            params.append(status)
        if snapshot_id:
            sql += " and a.snapshot_id=?"
            params.append(snapshot_id)
        rows = self._db.query(sql + " order by r.id desc", tuple(params))
        return [self._recommendation(row) for row in rows]

    def decide(self, rec_id: int, decision: str, actor: str, comment: str) -> dict | None:
        changed = self._db.query(
            "update recommendation set status=?,decided_by=?,decided_at=?,decision_comment=? where id=? and status='pending_review'",
            (decision, actor, _now(), comment, rec_id),
            fetch="rowcount",
        )
        return self.get_recommendation(rec_id) if changed else None

    # ------------------------------------------------------------- watches
    def create_watch(self, owner: str, name: str, kind: str, params: dict, threshold: float) -> dict:
        watch_id = self._db.run(
            [("insert into watch(owner,name,kind,params,threshold,created_at) values(?,?,?,?,?,?)", (owner, name, kind, json.dumps(params), threshold, _now()))],
            fetch="lastid",
        )
        return self.get_watch(int(watch_id))  # type: ignore[return-value]

    @staticmethod
    def _watch(row: dict) -> dict:
        return {**row, "params": json.loads(row["params"]), "last_value": json.loads(row["last_value"]) if row.get("last_value") else None,
                "last_triggered": None if row.get("last_triggered") is None else bool(row["last_triggered"])}

    def get_watch(self, watch_id: int) -> dict | None:
        row = self._db.query("select * from watch where id=?", (watch_id,), fetch="one")
        return None if row is None else self._watch(row)

    def list_watches(self, owner: str) -> list[dict]:
        return [self._watch(r) for r in self._db.query("select * from watch where owner=? order by id", (owner,))]

    def delete_watch(self, watch_id: int, owner: str) -> bool:
        return bool(self._db.query("delete from watch where id=? and owner=?", (watch_id, owner), fetch="rowcount"))

    def record_watch(self, watch_id: int, value, triggered: bool) -> None:
        self._db.query("update watch set last_value=?, last_triggered=?, last_checked=? where id=?", (json.dumps(value), int(triggered), _now(), watch_id), fetch="none")

    # ---------------------------------------------------- SAP sandbox execution
    def execute_recommendation(self, rec_id: int, documents: list[dict], actor: str) -> dict | None:
        """Accepted -> executed, recording the sandbox SAP documents created for each action (atomic, idempotent)."""
        changed = self._db.run(
            [("update recommendation set status='executed' where id=? and status='accepted'", (rec_id,))], fetch="rowcount"
        )
        if not changed:
            return None
        for doc in documents:
            self._db.query(
                "insert into sap_document(doc_number,doc_type,recommendation_id,payload,created_by,created_at,status) values(?,?,?,?,?,?,?)",
                (doc["doc_number"], doc["doc_type"], rec_id, json.dumps(doc["payload"]), actor, _now(), "created_in_sandbox"),
                fetch="none",
            )
        return self.get_recommendation(rec_id)

    def sap_documents(self, rec_id: int | None = None) -> list[dict]:
        rows = (self._db.query("select * from sap_document where recommendation_id=? order by id", (rec_id,)) if rec_id
                else self._db.query("select * from sap_document order by id desc limit 200"))
        return [{**r, "payload": json.loads(r["payload"])} for r in rows]

    def next_doc_number(self, prefix: str) -> str:
        row = self._db.query("select count(*) as n from sap_document where doc_type=?", (prefix,), fetch="one")
        base = {"STO": 4500900000, "PR": 1000900000, "POCHG": 4500800000, "INVADJ": 4900900000, "RECOUNT": 9900000, "TASK": 8800000, "DLV": 8000900000}[prefix]
        return str(base + int(row["n"]) + 1)

    # ------------------------------------------------ decision outcome learning
    # An approval is not proof that a recommendation was right: every executed recommendation gets an outcome record that
    # stays "awaiting_observation" until the real result is recorded against an SAP document.
    def create_outcome(self, rec_id: int, snapshot_id: str, kind: str, expected: dict, due_date: str | None) -> None:
        self._db.query(
            "insert into outcome(recommendation_id,snapshot_id,kind,expected,due_date,status,created_at) values(?,?,?,?,?,'awaiting_observation',?)",
            (rec_id, snapshot_id, kind, json.dumps(expected), due_date, _now()), fetch="none")

    @staticmethod
    def _outcome(row: dict) -> dict:
        return {**row, "expected": json.loads(row["expected"]), "observed": json.loads(row["observed"]) if row.get("observed") else None,
                "achieved": None if row.get("achieved") is None else bool(row["achieved"])}

    def list_outcomes(self, snapshot_id: str | None = None) -> list[dict]:
        rows = (self._db.query("select * from outcome where snapshot_id=? order by id desc", (snapshot_id,)) if snapshot_id
                else self._db.query("select * from outcome order by id desc"))
        return [self._outcome(r) for r in rows]

    def record_outcome(self, rec_id: int, achieved: bool, observed: dict, realized_impact_eur: float | None,
                       source_document: str, note: str, actor: str) -> dict | None:
        changed = self._db.query(
            "update outcome set status=?,achieved=?,observed=?,realized_impact_eur=?,source_document=?,note=?,observed_by=?,observed_at=? "
            "where recommendation_id=? and status='awaiting_observation'",
            ("verified" if achieved else "not_achieved", int(achieved), json.dumps(observed), realized_impact_eur, source_document, note, actor, _now(), rec_id),
            fetch="rowcount")
        if not changed:
            return None
        row = self._db.query("select * from outcome where recommendation_id=?", (rec_id,), fetch="one")
        return self._outcome(row)

    # ------------------------------------------ human expertise + consent (the data-moat inputs)
    def record_feedback(self, rec_id: int, decision: str, reason_code: str | None, modified: bool, comment: str, actor: str) -> None:
        """Why an expert approved, modified or rejected a recommendation — a training label once the outcome is known."""
        self._db.query("insert into decision_feedback(recommendation_id,decision,reason_code,modified,comment,actor,created_at) values(?,?,?,?,?,?,?)",
                       (rec_id, decision, reason_code, int(modified), comment, actor, _now()), fetch="none")

    def feedback(self, rec_ids: list[int] | None = None) -> list[dict]:
        rows = self._db.query("select * from decision_feedback order by id desc")
        rows = [{**r, "modified": bool(r["modified"])} for r in rows]
        return [r for r in rows if rec_ids is None or r["recommendation_id"] in rec_ids]

    def consent(self, tenant_id: str) -> dict | None:
        row = self._db.query("select * from consent where tenant_id=?", (tenant_id,), fetch="one")
        return None if row is None else {**row, "industry_learning": bool(row["industry_learning"])}

    def set_consent(self, tenant_id: str, industry_learning: bool, actor: str) -> dict:
        self._db.run([("delete from consent where tenant_id=?", (tenant_id,)),
                      ("insert into consent(tenant_id,industry_learning,updated_by,updated_at) values(?,?,?,?)", (tenant_id, int(industry_learning), actor, _now()))])
        return self.consent(tenant_id)  # type: ignore[return-value]

    # --------------------------------------------------------- settings (e.g. the Deep Agent harness)
    def get_setting(self, key: str) -> dict | None:
        row = self._db.query("select * from setting where key=?", (key,), fetch="one")
        return None if row is None else {**row, "value": json.loads(row["value"])}

    def set_setting(self, key: str, value: dict, actor: str) -> dict:
        self._db.run([("delete from setting where key=?", (key,)),
                      ("insert into setting(key,value,updated_by,updated_at) values(?,?,?,?)", (key, json.dumps(value), actor, _now()))])
        return self.get_setting(key)  # type: ignore[return-value]

    def decision_stats(self, snapshot_id: str | None = None) -> dict:
        """Acceptance and override (rejection) rates with the reasons experts gave."""
        recs = self.list_recommendations(snapshot_id=snapshot_id)
        decided = [r for r in recs if r["status"] in ("accepted", "executed", "rejected")]
        rejected = [r for r in decided if r["status"] == "rejected"]
        fb = {f["recommendation_id"]: f for f in reversed(self.feedback([r["id"] for r in decided]))}  # latest feedback per recommendation
        modified = [r for r in decided if r["status"] != "rejected" and fb.get(r["id"], {}).get("modified")]
        overridden = rejected + modified
        codes: dict[str, int] = {}
        for r in overridden:
            code = fb.get(r["id"], {}).get("reason_code") or "unspecified"
            codes[code] = codes.get(code, 0) + 1
        return {"submitted": len(recs), "decided": len(decided), "accepted": len(decided) - len(rejected), "rejected": len(rejected), "modified": len(modified),
                "acceptance_pct": round(100 * (len(decided) - len(rejected)) / len(decided), 1) if decided else None,
                "override_pct": round(100 * len(overridden) / len(decided), 1) if decided else None, "reason_codes": codes,
                "override_reasons": [{"recommendation_id": r["id"], "kind": r["kind"], "decision": "modified" if r in modified else "rejected",
                                      "reason_code": fb.get(r["id"], {}).get("reason_code"),
                                      "reason": r.get("decision_comment") or "(no reason given)"} for r in overridden][:10]}

    def counts(self, snapshot_id: str | None = None) -> dict:
        """Recommendation counts by status; optionally only for one SAP snapshot (one customer)."""
        if snapshot_id:
            rows = self._db.query("select r.status, count(*) as n from recommendation r join analysis a on a.id = r.analysis_id where a.snapshot_id=? group by r.status", (snapshot_id,))
            analyses = self._db.query("select count(*) as n from analysis where snapshot_id=?", (snapshot_id,), fetch="one")
            return {"analyses": int(analyses["n"]), "recommendations": {row["status"]: int(row["n"]) for row in rows}}
        rows = self._db.query("select status, count(*) as n from recommendation group by status")
        analyses = self._db.query("select count(*) as n from analysis", fetch="one")
        return {"analyses": int(analyses["n"]), "recommendations": {row["status"]: int(row["n"]) for row in rows}}
