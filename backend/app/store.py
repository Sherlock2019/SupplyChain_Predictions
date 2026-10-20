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
);
"""

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
);
"""


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

    def counts(self, snapshot_id: str | None = None) -> dict:
        """Recommendation counts by status; optionally only for one SAP snapshot (one customer)."""
        if snapshot_id:
            rows = self._db.query("select r.status, count(*) as n from recommendation r join analysis a on a.id = r.analysis_id where a.snapshot_id=? group by r.status", (snapshot_id,))
            analyses = self._db.query("select count(*) as n from analysis where snapshot_id=?", (snapshot_id,), fetch="one")
            return {"analyses": int(analyses["n"]), "recommendations": {row["status"]: int(row["n"]) for row in rows}}
        rows = self._db.query("select status, count(*) as n from recommendation group by status")
        analyses = self._db.query("select count(*) as n from analysis", fetch="one")
        return {"analyses": int(analyses["n"]), "recommendations": {row["status"]: int(row["n"]) for row in rows}}
