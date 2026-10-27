# ======================================================================================================
# ANNOTATED COPY (learning only: never imported, never executed)
# ORIGINAL FILE: backend/app/store.py
# What this module is: the governance ledger of the SPARC gateway — stored analyses (AN-...), the recommendation review queue,
# watches, SAP sandbox documents, decision outcomes, expert feedback, consent, settings, and a SHA-256 hash-chained audit log.
# SQLite for tests / laptops, PostgreSQL for deployments, behind one small "run statements" interface.
# Only comment lines were added (AST-verified).
# ======================================================================================================

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

# DDL (CREATE TABLE IF NOT EXISTS) for SQLite: executed at start-up by _SqliteDb.__init__.
# Tables: analysis, recommendation, audit (hash chain), watch, sap_document (sandbox outbox), outcome, decision_feedback, consent, setting.
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

# Same schema for PostgreSQL (identity columns instead of autoincrement, double precision instead of real).
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


# ===== FUNCTION: _now() =====
# ID: F0344 · function · used
# ORIGINAL FILE: backend/app/store.py:96-97
# ROLE: Current UTC time as ISO-8601 text (with microseconds).
# INPUTS:
#   none.
# OUTPUT:
#   str.
# CALLED BY:
#   <- F0358 Store.audit() (calls)
#   <- F0361 Store.save_analysis() (calls)
#   <- F0364 Store.submit() (calls)
#   <- F0368 Store.decide() (calls)
#   <- F0369 Store.create_watch() (calls)
#   <- F0374 Store.record_watch() (calls)
#   <- F0375 Store.execute_recommendation() (calls)
#   <- F0378 Store.create_outcome() (calls)
#   <- F0381 Store.record_outcome() (calls)
#   <- F0382 Store.record_feedback() (calls)
#   <- F0385 Store.set_consent() (calls)
#   <- F0387 Store.set_setting() (calls)
# CALLS:
#   (none found)
def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# ===== FUNCTION: _digest() =====
# ID: F0345 · function · used
# ORIGINAL FILE: backend/app/store.py:100-101
# ROLE: Hash of one audit entry chained to the previous one: SHA-256(prev | ts | actor | role | action | correlation | details).
# INPUTS:
#   prev, ts, actor, role, action: str; correlation_id: str | None; body: str (canonical JSON details).
# OUTPUT:
#   str -> 64 hex characters.
# CALLED BY:
#   <- F0358 Store.audit() (calls)
#   <- F0359 Store.verify_chain() (calls)
# CALLS:
#   (none found)
def _digest(prev: str, ts: str, actor: str, role: str, action: str, correlation_id: str | None, body: str) -> str:
    return hashlib.sha256("|".join((prev, ts, actor, role, action, correlation_id or "", body)).encode()).hexdigest()


# ===== CLASS: _SqliteDb =====
# ID: F0346 · class · used
# ORIGINAL FILE: backend/app/store.py:104-131
# ROLE: SQLite backend: one shared connection protected by a re-entrant lock; creates the schema on open.
# FIELDS:
#   dialect = "sqlite", _db: sqlite3.Connection, _lock: RLock.
# CALLED BY:
#   <- F0355 Store.__init__() (calls)
# CALLS:
#   (none found)
class _SqliteDb:
    dialect = "sqlite"

    # ===== FUNCTION: _SqliteDb.__init__() =====
    # ID: F0347 · method · used (framework)
    # ORIGINAL FILE: backend/app/store.py:107-113
    # ROLE: Open (or create) the database file and the tables.
    # INPUTS:
    #   path: str -> file path or ":memory:".
    # OUTPUT:
    #   None.
    # CALLED BY:
    #   (none found)
    # CALLS:
    #   (none found)
    def __init__(self, path: str):
        if path != ":memory:":
            Path(path).parent.mkdir(parents=True, exist_ok=True)
        self._db = sqlite3.connect(path, check_same_thread=False)
        # Rows as dicts {column: value}.
        self._db.row_factory = lambda cursor, row: {col[0]: row[i] for i, col in enumerate(cursor.description)}
        self._db.executescript(SQLITE_SCHEMA)
        self._lock = threading.RLock()

    # ===== FUNCTION: _SqliteDb.run() =====
    # ID: F0348 · method · used
    # ORIGINAL FILE: backend/app/store.py:115-128
    # ROLE: Run several statements in ONE transaction and return what `fetch` asks for from the last statement.
    # INPUTS:
    #   statements: list[(sql, params)], fetch: "none" | "one" | "all" | "rowcount" | "lastid", serialize: bool (unused on SQLite: the lock already serialises).
    # OUTPUT:
    #   Any -> row, rows, rowcount, last inserted id, or None.
    # CALLED BY:
    #   <- F0349 _SqliteDb.query() (calls)
    #   <- F0364 Store.submit() (calls)
    #   <- F0369 Store.create_watch() (calls)
    #   <- F0375 Store.execute_recommendation() (calls)
    #   <- F0385 Store.set_consent() (calls)
    #   <- F0387 Store.set_setting() (calls)
    # CALLS:
    #   (none found)
    def run(self, statements: list[tuple[str, tuple]], fetch: str = "none", serialize: bool = False) -> Any:
        # Lock + connection context manager = exclusive, atomic (commit/rollback).
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

    # ===== FUNCTION: _SqliteDb.query() =====
    # ID: F0349 · method · used
    # ORIGINAL FILE: backend/app/store.py:130-131
    # ROLE: Single-statement shortcut of run().
    # INPUTS:
    #   sql: str, params: tuple, fetch: str (default "all").
    # OUTPUT:
    #   Any.
    # CALLED BY:
    #   <- F0358 Store.audit() (calls)
    #   <- F0359 Store.verify_chain() (calls)
    #   <- F0360 Store.audit_events() (calls)
    #   <- F0361 Store.save_analysis() (calls)
    #   <- F0362 Store.get_analysis() (calls)
    #   <- F0364 Store.submit() (calls)
    #   <- F0366 Store.get_recommendation() (calls)
    #   <- F0367 Store.list_recommendations() (calls)
    #   <- F0368 Store.decide() (calls)
    #   <- F0371 Store.get_watch() (calls)
    #   <- F0372 Store.list_watches() (calls)
    #   <- F0373 Store.delete_watch() (calls)
    # CALLS:
    #   -> F0348 _SqliteDb.run() (calls)
    def query(self, sql: str, params: tuple = (), fetch: str = "all") -> Any:
        return self.run([(sql, params)], fetch)


# ===== CLASS: _PostgresDb =====
# ID: F0350 · class · used
# ORIGINAL FILE: backend/app/store.py:134-168
# ROLE: PostgreSQL backend with a connection pool; creates the schema at start-up under an advisory lock.
# FIELDS:
#   dialect = "postgres", _pool: ConnectionPool.
# CALLED BY:
#   <- F0355 Store.__init__() (calls)
# CALLS:
#   (none found)
class _PostgresDb:
    dialect = "postgres"

    # ===== FUNCTION: _PostgresDb.__init__() =====
    # ID: F0351 · method · used (framework)
    # ORIGINAL FILE: backend/app/store.py:137-145
    # ROLE: Open the pool and create the tables (lock 7316002 prevents two gateway workers from racing).
    # INPUTS:
    #   url: str.
    # OUTPUT:
    #   None.
    # CALLED BY:
    #   (none found)
    # CALLS:
    #   (none found)
    def __init__(self, url: str):
        from psycopg.rows import dict_row
        from psycopg_pool import ConnectionPool

        self._pool = ConnectionPool(url, min_size=1, max_size=8, kwargs={"row_factory": dict_row}, open=True)
        with self._pool.connection() as connection:
            connection.execute("select pg_advisory_xact_lock(7316002)")
            for statement in filter(None, (part.strip() for part in POSTGRES_SCHEMA.split(";"))):
                connection.execute(statement)

    # ===== FUNCTION: _PostgresDb.run() =====
    # ID: F0352 · method · used
    # ORIGINAL FILE: backend/app/store.py:147-165
    # ROLE: Same contract as _SqliteDb.run; "?" placeholders become "%s"; "lastid" adds "returning id" to INSERTs;
    #       serialize=True takes the audit/ledger advisory lock 7316003.
    # INPUTS:
    #   statements, fetch, serialize.
    # OUTPUT:
    #   Any.
    # CALLED BY:
    #   <- F0353 _PostgresDb.query() (calls)
    #   <- F0364 Store.submit() (calls)
    #   <- F0369 Store.create_watch() (calls)
    #   <- F0375 Store.execute_recommendation() (calls)
    #   <- F0385 Store.set_consent() (calls)
    #   <- F0387 Store.set_setting() (calls)
    # CALLS:
    #   -> F0425 Database.transaction() (calls)
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

    # ===== FUNCTION: _PostgresDb.query() =====
    # ID: F0353 · method · used
    # ORIGINAL FILE: backend/app/store.py:167-168
    # ROLE: Single-statement shortcut of run().
    # INPUTS:
    #   sql, params, fetch.
    # OUTPUT:
    #   Any.
    # CALLED BY:
    #   <- F0358 Store.audit() (calls)
    #   <- F0359 Store.verify_chain() (calls)
    #   <- F0360 Store.audit_events() (calls)
    #   <- F0361 Store.save_analysis() (calls)
    #   <- F0362 Store.get_analysis() (calls)
    #   <- F0364 Store.submit() (calls)
    #   <- F0366 Store.get_recommendation() (calls)
    #   <- F0367 Store.list_recommendations() (calls)
    #   <- F0368 Store.decide() (calls)
    #   <- F0371 Store.get_watch() (calls)
    #   <- F0372 Store.list_watches() (calls)
    #   <- F0373 Store.delete_watch() (calls)
    # CALLS:
    #   -> F0352 _PostgresDb.run() (calls)
    def query(self, sql: str, params: tuple = (), fetch: str = "all") -> Any:
        return self.run([(sql, params)], fetch)


# ===== CLASS: Store =====
# ID: F0354 · class · used
# ORIGINAL FILE: backend/app/store.py:171-436
# ROLE: The governance ledger API used by every gateway endpoint (analyses, recommendations, audit, watches, outcomes, ...).
# FIELDS:
#   _db: _SqliteDb | _PostgresDb.
# CALLED BY:
#   <- F0452 LocalBackend.__init__() (references)
#   <- F0230 Dashboards.__init__() (references)
#   <- F0017 create_app() (references)
#   <- F0017 create_app() (calls)
#   <- F0251 MoatEngine.__init__() (references)
#   <- F0260 RoleCenter.__init__() (references)
#   <- F0392 TenantRegistry.__init__() (references)
#   <- F0905 client() (references)
#   <- F0872 test_demo_session_disabled_by_default_and_enabled_for_local_demo() (references)
#   <- F0878 test_tenant_scoped_authorization() (references)
#   <- F0952 _exercise_store() (references)
#   <- F0953 test_sqlite_store() (references)
# CALLS:
#   (none found)
class Store:
    # ===== FUNCTION: Store.__init__() =====
    # ID: F0355 · method · used (framework)
    # ORIGINAL FILE: backend/app/store.py:172-178
    # ROLE: Choose the backend from DATABASE_URL.
    # INPUTS:
    #   database_url: str -> sqlite:///path or postgresql://...
    # OUTPUT:
    #   None (ValueError otherwise).
    # CALLED BY:
    #   (none found)
    # CALLS:
    #   -> F0346 _SqliteDb (calls)
    #   -> F0350 _PostgresDb (calls)
    def __init__(self, database_url: str):
        if database_url.startswith("sqlite:///"):
            self._db = _SqliteDb(database_url.removeprefix("sqlite:///"))
        elif database_url.startswith(("postgresql://", "postgres://")):
            self._db = _PostgresDb(database_url)
        else:
            raise ValueError("DATABASE_URL must be sqlite:///path or postgresql://...")

    # ===== FUNCTION: Store.memory() =====
    # ID: F0356 · method · used
    # ORIGINAL FILE: backend/app/store.py:180-182
    # ROLE: In-memory store for tests.
    # INPUTS:
    #   cls (classmethod receives the class).
    # OUTPUT:
    #   Store.
    # CALLED BY:
    #   <- F0452 LocalBackend.__init__() (calls)
    #   <- F0905 client() (calls)
    #   <- F0872 test_demo_session_disabled_by_default_and_enabled_for_local_demo() (calls)
    #   <- F0878 test_tenant_scoped_authorization() (calls)
    #   <- F0953 test_sqlite_store() (calls)
    # CALLS:
    #   (none found)
    @classmethod
    def memory(cls) -> "Store":
        return cls("sqlite:///:memory:")

    # ===== FUNCTION: Store.dialect() =====
    # ID: F0357 · method · used
    # ORIGINAL FILE: backend/app/store.py:184-186
    # ROLE: "sqlite" or "postgres".
    # INPUTS:
    #   self.
    # OUTPUT:
    #   str.
    # CALLED BY:
    #   <- F0026 create_app.ready() (references)
    #   <- F0031 create_app.status() (references)
    # CALLS:
    #   (none found)
    @property
    def dialect(self) -> str:
        return self._db.dialect

    # ------------------------------------------------------------------ audit
    # ===== FUNCTION: Store.audit() =====
    # ID: F0358 · method · used
    # ORIGINAL FILE: backend/app/store.py:189-212
    # ROLE: Append one hash-chained audit entry (atomic read of the chain head + insert).
    # INPUTS:
    #   actor: str, role: str, action: str, details: dict, correlation_id: str | None (X-Correlation-ID of the request).
    # OUTPUT:
    #   None.
    # CALLED BY:
    #   <- F0019 create_app.principal() (calls)
    #   <- F0020 create_app.manager() (calls)
    #   <- F0023 create_app.save() (calls)
    #   <- F0039 create_app.block_sap_write() (calls)
    #   <- F0058 create_app.moat_consent() (calls)
    #   <- F0059 create_app.record_outcome() (calls)
    #   <- F0069 create_app.create_watch() (calls)
    #   <- F0081 create_app.rag_add() (calls)
    #   <- F0987 create_app.code_update() (calls)
    #   <- F0083 create_app.chat() (calls)
    #   <- F0085 create_app.langgraph_agentflow() (calls)
    #   <- F0086 create_app.langgraph_agentflow_resume() (calls)
    # CALLS:
    #   -> F0349 _SqliteDb.query() (calls)
    #   -> F0353 _PostgresDb.query() (calls)
    #   -> F0344 _now() (calls)
    #   -> F0345 _digest() (calls)
    #   -> F0425 Database.transaction() (calls)
    def audit(self, actor: str, role: str, action: str, details: dict, correlation_id: str | None = None) -> None:
        # Canonical JSON (sorted keys, no spaces) -> reproducible hash.
        body = json.dumps(details, sort_keys=True, default=str, separators=(",", ":"))

        if self._db.dialect == "sqlite":
            # Hold the RLock across "read head" + "insert" (the nested query() calls re-acquire it: re-entrant).
            with self._db._lock:
                prior = self._db.query("select hash from audit order by id desc limit 1", fetch="one")
                # The first entry links to 64 zeros.
                prev = prior["hash"] if prior else "0" * 64
                ts = _now()
                self._db.query(
                    "insert into audit(ts,actor,role,action,correlation_id,details,prev_hash,hash) values(?,?,?,?,?,?,?,?)",
                    (ts, actor, role, action, correlation_id, body, prev, _digest(prev, ts, actor, role, action, correlation_id, body)),
                    fetch="none",
                )
            return

        # PostgreSQL: one transaction holding the advisory lock 7316003 (no two requests extend the same head).
        with self._db._pool.connection() as connection, connection.transaction():
            connection.execute("select pg_advisory_xact_lock(7316003)")
            prior = connection.execute("select hash from audit order by id desc limit 1").fetchone()
            prev = prior["hash"] if prior else "0" * 64
            ts = _now()
            connection.execute(
                "insert into audit(ts,actor,role,action,correlation_id,details,prev_hash,hash) values(%s,%s,%s,%s,%s,%s,%s,%s)",
                (ts, actor, role, action, correlation_id, body, prev, _digest(prev, ts, actor, role, action, correlation_id, body)),
            )

    # ===== FUNCTION: Store.verify_chain() =====
    # ID: F0359 · method · used
    # ORIGINAL FILE: backend/app/store.py:214-221
    # ROLE: Recompute the whole chain; False if any entry was edited, removed or inserted.
    # INPUTS:
    #   self.
    # OUTPUT:
    #   bool.
    # CALLED BY:
    #   <- F0031 create_app.status() (calls)
    #   <- F0101 create_app.audit() (calls)
    #   <- F0952 _exercise_store() (calls)
    # CALLS:
    #   -> F0349 _SqliteDb.query() (calls)
    #   -> F0353 _PostgresDb.query() (calls)
    #   -> F0345 _digest() (calls)
    def verify_chain(self) -> bool:
        prev = "0" * 64
        for row in self._db.query("select * from audit order by id"):
            expected = _digest(prev, row["ts"], row["actor"], row["role"], row["action"], row["correlation_id"], row["details"])
            if row["prev_hash"] != prev or row["hash"] != expected:
                return False
            prev = row["hash"]
        return True

    # ===== FUNCTION: Store.audit_events() =====
    # ID: F0360 · method · used
    # ORIGINAL FILE: backend/app/store.py:223-225
    # ROLE: Newest audit entries (max 1000) with details parsed.
    # INPUTS:
    #   limit: int.
    # OUTPUT:
    #   list[dict].
    # CALLED BY:
    #   <- F0101 create_app.audit() (calls)
    # CALLS:
    #   -> F0349 _SqliteDb.query() (calls)
    #   -> F0353 _PostgresDb.query() (calls)
    def audit_events(self, limit: int = 100) -> list[dict]:
        rows = self._db.query("select * from audit order by id desc limit ?", (min(limit, 1000),))
        return [{**row, "details": json.loads(row["details"])} for row in rows]

    # --------------------------------------------------------------- analyses
    # ===== FUNCTION: Store.save_analysis() =====
    # ID: F0361 · method · used
    # ORIGINAL FILE: backend/app/store.py:228-235
    # ROLE: Store a deterministic analysis result; returns its id "AN-" + 12 hex chars (quoted by agents).
    # INPUTS:
    #   kind: str, request: dict, result: dict, snapshot_id: str, actor: str.
    # OUTPUT:
    #   str -> analysis id.
    # CALLED BY:
    #   <- F0453 LocalBackend._save() (calls)
    #   <- F0023 create_app.save() (calls)
    #   <- F0952 _exercise_store() (calls)
    # CALLS:
    #   -> F0349 _SqliteDb.query() (calls)
    #   -> F0353 _PostgresDb.query() (calls)
    #   -> F0344 _now() (calls)
    def save_analysis(self, kind: str, request: dict, result: dict, snapshot_id: str, actor: str) -> str:
        analysis_id = f"AN-{uuid.uuid4().hex[:12]}"
        self._db.query(
            "insert into analysis(id,kind,request,result,snapshot_id,actor,created_at) values(?,?,?,?,?,?,?)",
            (analysis_id, kind, json.dumps(request, default=str), json.dumps(result, default=str), snapshot_id, actor, _now()),
            fetch="none",
        )
        return analysis_id

    # ===== FUNCTION: Store.get_analysis() =====
    # ID: F0362 · method · used
    # ORIGINAL FILE: backend/app/store.py:237-239
    # ROLE: Read a stored analysis (request / result parsed).
    # INPUTS:
    #   analysis_id: str.
    # OUTPUT:
    #   dict | None.
    # CALLED BY:
    #   <- F0072 create_app.get_analysis() (calls)
    #   <- F0363 Store.latest_actionable() (calls)
    #   <- F0364 Store.submit() (calls)
    # CALLS:
    #   -> F0349 _SqliteDb.query() (calls)
    #   -> F0353 _PostgresDb.query() (calls)
    def get_analysis(self, analysis_id: str) -> dict | None:
        row = self._db.query("select * from analysis where id=?", (analysis_id,), fetch="one")
        return None if row is None else {**row, "request": json.loads(row["request"]), "result": json.loads(row["result"])}

    # ===== FUNCTION: Store.latest_actionable() =====
    # ID: F0363 · method · used
    # ORIGINAL FILE: backend/app/store.py:241-244
    # ROLE: Server-side selection for agent hand-offs: among the AN ids mentioned by the agent, the newest analysis of the expected
    #       kind that has proposed actions (the LLM never chooses the quantities).
    # INPUTS:
    #   analysis_ids: list[str], kind: str.
    # OUTPUT:
    #   dict | None.
    # CALLED BY:
    #   <- F0096 create_app.submit_from_agent() (calls)
    # CALLS:
    #   -> F0362 Store.get_analysis() (calls)
    def latest_actionable(self, analysis_ids: list[str], kind: str) -> dict | None:
        """Newest stored analysis of `kind` among the ids that has proposed actions (server-side selection)."""
        candidates = [a for a in (self.get_analysis(i) for i in dict.fromkeys(analysis_ids)) if a and a["kind"] == kind and a["result"].get("proposed_actions")]
        return max(candidates, key=lambda a: a["created_at"]) if candidates else None

    # --------------------------------------------------------- recommendations
    # ===== FUNCTION: Store.submit() =====
    # ID: F0364 · method · used
    # ORIGINAL FILE: backend/app/store.py:247-266
    # ROLE: Submit an analysis to the review queue (status pending_review); actions are copied from the stored analysis; idempotent
    #       per analysis id.
    # INPUTS:
    #   analysis_id: str, explanation: str, actor: str, source: str.
    # OUTPUT:
    #   dict -> recommendation (KeyError unknown analysis; ValueError no actions).
    # CALLED BY:
    #   <- F0465 LocalBackend.submit_recommendation() (calls)
    #   <- F0095 create_app.submit_recommendation() (calls)
    #   <- F0096 create_app.submit_from_agent() (calls)
    #   <- F0952 _exercise_store() (calls)
    # CALLS:
    #   -> F0362 Store.get_analysis() (calls)
    #   -> F0349 _SqliteDb.query() (calls)
    #   -> F0353 _PostgresDb.query() (calls)
    #   -> F0365 Store._recommendation() (calls)
    #   -> F0348 _SqliteDb.run() (calls)
    #   -> F0352 _PostgresDb.run() (calls)
    #   -> F0344 _now() (calls)
    #   -> F0366 Store.get_recommendation() (calls)
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

    # ===== FUNCTION: Store._recommendation() =====
    # ID: F0365 · method · used
    # ORIGINAL FILE: backend/app/store.py:268-270
    # ROLE: Recommendation row with its actions JSON parsed.
    # INPUTS:
    #   row: dict.
    # OUTPUT:
    #   dict.
    # CALLED BY:
    #   <- F0364 Store.submit() (calls)
    #   <- F0366 Store.get_recommendation() (calls)
    #   <- F0367 Store.list_recommendations() (calls)
    # CALLS:
    #   (none found)
    @staticmethod
    def _recommendation(row: dict) -> dict:
        return {**row, "actions": json.loads(row["actions"])}

    # ===== FUNCTION: Store.get_recommendation() =====
    # ID: F0366 · method · used
    # ORIGINAL FILE: backend/app/store.py:272-274
    # ROLE: One recommendation by id.
    # INPUTS:
    #   rec_id: int.
    # OUTPUT:
    #   dict | None.
    # CALLED BY:
    #   <- F0059 create_app.record_outcome() (calls)
    #   <- F0099 create_app.execute() (calls)
    #   <- F0110 create_app.poc_reconcile() (calls)
    #   <- F0364 Store.submit() (calls)
    #   <- F0368 Store.decide() (calls)
    #   <- F0375 Store.execute_recommendation() (calls)
    # CALLS:
    #   -> F0349 _SqliteDb.query() (calls)
    #   -> F0353 _PostgresDb.query() (calls)
    #   -> F0365 Store._recommendation() (calls)
    def get_recommendation(self, rec_id: int) -> dict | None:
        row = self._db.query("select * from recommendation where id=?", (rec_id,), fetch="one")
        return None if row is None else self._recommendation(row)

    # ===== FUNCTION: Store.list_recommendations() =====
    # ID: F0367 · method · used
    # ORIGINAL FILE: backend/app/store.py:276-287
    # ROLE: Recommendations, newest first, optionally by status and/or by SAP snapshot (= one customer).
    # INPUTS:
    #   status: str | None, snapshot_id: str | None.
    # OUTPUT:
    #   list[dict].
    # CALLED BY:
    #   <- F0097 create_app.recommendations() (calls)
    #   <- F0255 MoatEngine.view() (calls)
    #   <- F0261 RoleCenter._facts() (calls)
    #   <- F0281 RoleCenter._director() (calls)
    #   <- F0388 Store.decision_stats() (calls)
    # CALLS:
    #   -> F0349 _SqliteDb.query() (calls)
    #   -> F0353 _PostgresDb.query() (calls)
    #   -> F0365 Store._recommendation() (calls)
    def list_recommendations(self, status: str | None = None, snapshot_id: str | None = None) -> list[dict]:
        """Optionally only recommendations whose analysis came from one SAP snapshot (one customer)."""
        # "where 1=1" lets every optional filter start with " and ...".
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

    # ===== FUNCTION: Store.decide() =====
    # ID: F0368 · method · used
    # ORIGINAL FILE: backend/app/store.py:289-295
    # ROLE: Manager decision: pending_review -> accepted | rejected (only once: the WHERE on status makes it safe).
    # INPUTS:
    #   rec_id: int, decision: str, actor: str, comment: str.
    # OUTPUT:
    #   dict | None -> updated recommendation, or None when it was not pending.
    # CALLED BY:
    #   <- F0098 create_app.decide() (calls)
    #   <- F0952 _exercise_store() (calls)
    # CALLS:
    #   -> F0349 _SqliteDb.query() (calls)
    #   -> F0353 _PostgresDb.query() (calls)
    #   -> F0344 _now() (calls)
    #   -> F0366 Store.get_recommendation() (calls)
    def decide(self, rec_id: int, decision: str, actor: str, comment: str) -> dict | None:
        changed = self._db.query(
            "update recommendation set status=?,decided_by=?,decided_at=?,decision_comment=? where id=? and status='pending_review'",
            (decision, actor, _now(), comment, rec_id),
            fetch="rowcount",
        )
        return self.get_recommendation(rec_id) if changed else None

    # ------------------------------------------------------------- watches
    # ===== FUNCTION: Store.create_watch() =====
    # ID: F0369 · method · used
    # ORIGINAL FILE: backend/app/store.py:298-303
    # ROLE: Create a saved watch (alert rule) for an owner.
    # INPUTS:
    #   owner: str ("identity@tenant"), name, kind: str, params: dict, threshold: float.
    # OUTPUT:
    #   dict -> the watch.
    # CALLED BY:
    #   <- F0069 create_app.create_watch() (calls)
    # CALLS:
    #   -> F0348 _SqliteDb.run() (calls)
    #   -> F0352 _PostgresDb.run() (calls)
    #   -> F0344 _now() (calls)
    #   -> F0371 Store.get_watch() (calls)
    def create_watch(self, owner: str, name: str, kind: str, params: dict, threshold: float) -> dict:
        watch_id = self._db.run(
            [("insert into watch(owner,name,kind,params,threshold,created_at) values(?,?,?,?,?,?)", (owner, name, kind, json.dumps(params), threshold, _now()))],
            fetch="lastid",
        )
        return self.get_watch(int(watch_id))  # type: ignore[return-value]

    # ===== FUNCTION: Store._watch() =====
    # ID: F0370 · method · used
    # ORIGINAL FILE: backend/app/store.py:305-308
    # ROLE: Watch row with JSON / boolean columns converted.
    # INPUTS:
    #   row: dict.
    # OUTPUT:
    #   dict.
    # CALLED BY:
    #   <- F0371 Store.get_watch() (calls)
    #   <- F0372 Store.list_watches() (calls)
    # CALLS:
    #   (none found)
    @staticmethod
    def _watch(row: dict) -> dict:
        return {**row, "params": json.loads(row["params"]), "last_value": json.loads(row["last_value"]) if row.get("last_value") else None,
                "last_triggered": None if row.get("last_triggered") is None else bool(row["last_triggered"])}

    # ===== FUNCTION: Store.get_watch() =====
    # ID: F0371 · method · used
    # ORIGINAL FILE: backend/app/store.py:310-312
    # ROLE: One watch by id.
    # INPUTS:
    #   watch_id: int.
    # OUTPUT:
    #   dict | None.
    # CALLED BY:
    #   <- F0369 Store.create_watch() (calls)
    # CALLS:
    #   -> F0349 _SqliteDb.query() (calls)
    #   -> F0353 _PostgresDb.query() (calls)
    #   -> F0370 Store._watch() (calls)
    def get_watch(self, watch_id: int) -> dict | None:
        row = self._db.query("select * from watch where id=?", (watch_id,), fetch="one")
        return None if row is None else self._watch(row)

    # ===== FUNCTION: Store.list_watches() =====
    # ID: F0372 · method · used
    # ORIGINAL FILE: backend/app/store.py:314-315
    # ROLE: Watches of one owner.
    # INPUTS:
    #   owner: str.
    # OUTPUT:
    #   list[dict].
    # CALLED BY:
    #   <- F0068 create_app.list_watches() (calls)
    #   <- F0071 create_app.evaluate_watches() (calls)
    # CALLS:
    #   -> F0370 Store._watch() (calls)
    #   -> F0349 _SqliteDb.query() (calls)
    #   -> F0353 _PostgresDb.query() (calls)
    def list_watches(self, owner: str) -> list[dict]:
        return [self._watch(r) for r in self._db.query("select * from watch where owner=? order by id", (owner,))]

    # ===== FUNCTION: Store.delete_watch() =====
    # ID: F0373 · method · used
    # ORIGINAL FILE: backend/app/store.py:317-318
    # ROLE: Delete a watch of this owner (an owner cannot delete someone else's watch).
    # INPUTS:
    #   watch_id: int, owner: str.
    # OUTPUT:
    #   bool -> True when a row was deleted.
    # CALLED BY:
    #   <- F0070 create_app.delete_watch() (calls)
    # CALLS:
    #   -> F0349 _SqliteDb.query() (calls)
    #   -> F0353 _PostgresDb.query() (calls)
    def delete_watch(self, watch_id: int, owner: str) -> bool:
        return bool(self._db.query("delete from watch where id=? and owner=?", (watch_id, owner), fetch="rowcount"))

    # ===== FUNCTION: Store.record_watch() =====
    # ID: F0374 · method · used
    # ORIGINAL FILE: backend/app/store.py:320-321
    # ROLE: Store the last evaluated value of a watch.
    # INPUTS:
    #   watch_id: int, value, triggered: bool.
    # OUTPUT:
    #   None.
    # CALLED BY:
    #   <- F0071 create_app.evaluate_watches() (calls)
    # CALLS:
    #   -> F0349 _SqliteDb.query() (calls)
    #   -> F0353 _PostgresDb.query() (calls)
    #   -> F0344 _now() (calls)
    def record_watch(self, watch_id: int, value, triggered: bool) -> None:
        self._db.query("update watch set last_value=?, last_triggered=?, last_checked=? where id=?", (json.dumps(value), int(triggered), _now(), watch_id), fetch="none")

    # ---------------------------------------------------- SAP sandbox execution
    # ===== FUNCTION: Store.execute_recommendation() =====
    # ID: F0375 · method · used
    # ORIGINAL FILE: backend/app/store.py:324-337
    # ROLE: accepted -> executed (only once) and record the sandbox SAP documents of each action (never a production SAP system).
    # INPUTS:
    #   rec_id: int, documents: list[dict] ({doc_type, doc_number, payload}), actor: str.
    # OUTPUT:
    #   dict | None -> recommendation, or None when it was not "accepted".
    # CALLED BY:
    #   <- F0099 create_app.execute() (calls)
    # CALLS:
    #   -> F0348 _SqliteDb.run() (calls)
    #   -> F0352 _PostgresDb.run() (calls)
    #   -> F0349 _SqliteDb.query() (calls)
    #   -> F0353 _PostgresDb.query() (calls)
    #   -> F0344 _now() (calls)
    #   -> F0366 Store.get_recommendation() (calls)
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

    # ===== FUNCTION: Store.sap_documents() =====
    # ID: F0376 · method · used
    # ORIGINAL FILE: backend/app/store.py:339-342
    # ROLE: Sandbox SAP documents of one recommendation, or the latest 200.
    # INPUTS:
    #   rec_id: int | None.
    # OUTPUT:
    #   list[dict].
    # CALLED BY:
    #   <- F0037 create_app.sap_sandbox_documents() (calls)
    #   <- F0099 create_app.execute() (calls)
    #   <- F0100 create_app.sap_documents() (calls)
    # CALLS:
    #   -> F0349 _SqliteDb.query() (calls)
    #   -> F0353 _PostgresDb.query() (calls)
    def sap_documents(self, rec_id: int | None = None) -> list[dict]:
        rows = (self._db.query("select * from sap_document where recommendation_id=? order by id", (rec_id,)) if rec_id
                else self._db.query("select * from sap_document order by id desc limit 200"))
        return [{**r, "payload": json.loads(r["payload"])} for r in rows]

    # ===== FUNCTION: Store.next_doc_number() =====
    # ID: F0377 · method · used
    # ORIGINAL FILE: backend/app/store.py:344-347
    # ROLE: Next sandbox document number for a document type (number range base + count + 1).
    # INPUTS:
    #   prefix: str -> "STO" | "PR" | "POCHG" | "INVADJ" | "RECOUNT" | "TASK" | "DLV".
    # OUTPUT:
    #   str.
    # CALLED BY:
    #   <- F0099 create_app.execute() (calls)
    # CALLS:
    #   -> F0349 _SqliteDb.query() (calls)
    #   -> F0353 _PostgresDb.query() (calls)
    def next_doc_number(self, prefix: str) -> str:
        row = self._db.query("select count(*) as n from sap_document where doc_type=?", (prefix,), fetch="one")
        base = {"STO": 4500900000, "PR": 1000900000, "POCHG": 4500800000, "INVADJ": 4900900000, "RECOUNT": 9900000, "TASK": 8800000, "DLV": 8000900000}[prefix]
        return str(base + int(row["n"]) + 1)

    # ------------------------------------------------ decision outcome learning
    # An approval is not proof that a recommendation was right: every executed recommendation gets an outcome record that
    # stays "awaiting_observation" until the real result is recorded against an SAP document.
    # ===== FUNCTION: Store.create_outcome() =====
    # ID: F0378 · method · used
    # ORIGINAL FILE: backend/app/store.py:352-355
    # ROLE: Open the outcome record of an executed recommendation (expected result + due date).
    # INPUTS:
    #   rec_id: int, snapshot_id: str, kind: str, expected: dict, due_date: str | None.
    # OUTPUT:
    #   None.
    # CALLED BY:
    #   <- F0059 create_app.record_outcome() (calls)
    #   <- F0099 create_app.execute() (calls)
    #   <- F0110 create_app.poc_reconcile() (calls)
    # CALLS:
    #   -> F0349 _SqliteDb.query() (calls)
    #   -> F0353 _PostgresDb.query() (calls)
    #   -> F0344 _now() (calls)
    def create_outcome(self, rec_id: int, snapshot_id: str, kind: str, expected: dict, due_date: str | None) -> None:
        self._db.query(
            "insert into outcome(recommendation_id,snapshot_id,kind,expected,due_date,status,created_at) values(?,?,?,?,?,'awaiting_observation',?)",
            (rec_id, snapshot_id, kind, json.dumps(expected), due_date, _now()), fetch="none")

    # ===== FUNCTION: Store._outcome() =====
    # ID: F0379 · method · used
    # ORIGINAL FILE: backend/app/store.py:357-360
    # ROLE: Outcome row with JSON / boolean columns converted.
    # INPUTS:
    #   row: dict.
    # OUTPUT:
    #   dict.
    # CALLED BY:
    #   <- F0380 Store.list_outcomes() (calls)
    #   <- F0381 Store.record_outcome() (calls)
    # CALLS:
    #   (none found)
    @staticmethod
    def _outcome(row: dict) -> dict:
        return {**row, "expected": json.loads(row["expected"]), "observed": json.loads(row["observed"]) if row.get("observed") else None,
                "achieved": None if row.get("achieved") is None else bool(row["achieved"])}

    # ===== FUNCTION: Store.list_outcomes() =====
    # ID: F0380 · method · used
    # ORIGINAL FILE: backend/app/store.py:362-365
    # ROLE: Outcomes, newest first, optionally for one snapshot.
    # INPUTS:
    #   snapshot_id: str | None.
    # OUTPUT:
    #   list[dict].
    # CALLED BY:
    #   <- F0059 create_app.record_outcome() (calls)
    #   <- F0110 create_app.poc_reconcile() (calls)
    #   <- F0255 MoatEngine.view() (calls)
    #   <- F0261 RoleCenter._facts() (calls)
    # CALLS:
    #   -> F0349 _SqliteDb.query() (calls)
    #   -> F0353 _PostgresDb.query() (calls)
    #   -> F0379 Store._outcome() (calls)
    def list_outcomes(self, snapshot_id: str | None = None) -> list[dict]:
        rows = (self._db.query("select * from outcome where snapshot_id=? order by id desc", (snapshot_id,)) if snapshot_id
                else self._db.query("select * from outcome order by id desc"))
        return [self._outcome(r) for r in rows]

    # ===== FUNCTION: Store.record_outcome() =====
    # ID: F0381 · method · used
    # ORIGINAL FILE: backend/app/store.py:367-377
    # ROLE: Record the observed result once (awaiting_observation -> verified | not_achieved).
    # INPUTS:
    #   rec_id: int, achieved: bool, observed: dict, realized_impact_eur: float | None, source_document: str, note: str, actor: str.
    # OUTPUT:
    #   dict | None -> updated outcome, None when already recorded / missing.
    # CALLED BY:
    #   <- F0059 create_app.record_outcome() (calls)
    #   <- F0110 create_app.poc_reconcile() (calls)
    # CALLS:
    #   -> F0349 _SqliteDb.query() (calls)
    #   -> F0353 _PostgresDb.query() (calls)
    #   -> F0344 _now() (calls)
    #   -> F0379 Store._outcome() (calls)
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
    # ===== FUNCTION: Store.record_feedback() =====
    # ID: F0382 · method · used
    # ORIGINAL FILE: backend/app/store.py:380-383
    # ROLE: Store why an expert approved / modified / rejected (training label once the outcome is known).
    # INPUTS:
    #   rec_id: int, decision: str, reason_code: str | None, modified: bool, comment: str, actor: str.
    # OUTPUT:
    #   None.
    # CALLED BY:
    #   <- F0098 create_app.decide() (calls)
    # CALLS:
    #   -> F0349 _SqliteDb.query() (calls)
    #   -> F0353 _PostgresDb.query() (calls)
    #   -> F0344 _now() (calls)
    def record_feedback(self, rec_id: int, decision: str, reason_code: str | None, modified: bool, comment: str, actor: str) -> None:
        """Why an expert approved, modified or rejected a recommendation — a training label once the outcome is known."""
        self._db.query("insert into decision_feedback(recommendation_id,decision,reason_code,modified,comment,actor,created_at) values(?,?,?,?,?,?,?)",
                       (rec_id, decision, reason_code, int(modified), comment, actor, _now()), fetch="none")

    # ===== FUNCTION: Store.feedback() =====
    # ID: F0383 · method · used
    # ORIGINAL FILE: backend/app/store.py:385-388
    # ROLE: Feedback rows, newest first, optionally limited to some recommendation ids.
    # INPUTS:
    #   rec_ids: list[int] | None.
    # OUTPUT:
    #   list[dict].
    # CALLED BY:
    #   <- F0388 Store.decision_stats() (calls)
    # CALLS:
    #   -> F0349 _SqliteDb.query() (calls)
    #   -> F0353 _PostgresDb.query() (calls)
    def feedback(self, rec_ids: list[int] | None = None) -> list[dict]:
        rows = self._db.query("select * from decision_feedback order by id desc")
        rows = [{**r, "modified": bool(r["modified"])} for r in rows]
        return [r for r in rows if rec_ids is None or r["recommendation_id"] in rec_ids]

    # ===== FUNCTION: Store.consent() =====
    # ID: F0384 · method · used
    # ORIGINAL FILE: backend/app/store.py:390-392
    # ROLE: Consent of a tenant to industry learning.
    # INPUTS:
    #   tenant_id: str.
    # OUTPUT:
    #   dict | None.
    # CALLED BY:
    #   <- F0252 MoatEngine.consent() (calls)
    #   <- F0385 Store.set_consent() (calls)
    # CALLS:
    #   -> F0349 _SqliteDb.query() (calls)
    #   -> F0353 _PostgresDb.query() (calls)
    def consent(self, tenant_id: str) -> dict | None:
        row = self._db.query("select * from consent where tenant_id=?", (tenant_id,), fetch="one")
        return None if row is None else {**row, "industry_learning": bool(row["industry_learning"])}

    # ===== FUNCTION: Store.set_consent() =====
    # ID: F0385 · method · used
    # ORIGINAL FILE: backend/app/store.py:394-397
    # ROLE: Replace the consent of a tenant (delete + insert in one transaction).
    # INPUTS:
    #   tenant_id: str, industry_learning: bool, actor: str.
    # OUTPUT:
    #   dict.
    # CALLED BY:
    #   <- F0058 create_app.moat_consent() (calls)
    # CALLS:
    #   -> F0348 _SqliteDb.run() (calls)
    #   -> F0352 _PostgresDb.run() (calls)
    #   -> F0344 _now() (calls)
    #   -> F0384 Store.consent() (calls)
    def set_consent(self, tenant_id: str, industry_learning: bool, actor: str) -> dict:
        self._db.run([("delete from consent where tenant_id=?", (tenant_id,)),
                      ("insert into consent(tenant_id,industry_learning,updated_by,updated_at) values(?,?,?,?)", (tenant_id, int(industry_learning), actor, _now()))])
        return self.consent(tenant_id)  # type: ignore[return-value]

    # --------------------------------------------------------- settings (e.g. the Deep Agent harness)
    # ===== FUNCTION: Store.get_setting() =====
    # ID: F0386 · method · used
    # ORIGINAL FILE: backend/app/store.py:400-402
    # ROLE: Read a JSON setting.
    # INPUTS:
    #   key: str.
    # OUTPUT:
    #   dict | None.
    # CALLED BY:
    #   <- F0089 create_app.current_harness() (calls)
    #   <- F0090 create_app.deep_harness() (calls)
    #   <- F0387 Store.set_setting() (calls)
    # CALLS:
    #   -> F0349 _SqliteDb.query() (calls)
    #   -> F0353 _PostgresDb.query() (calls)
    def get_setting(self, key: str) -> dict | None:
        row = self._db.query("select * from setting where key=?", (key,), fetch="one")
        return None if row is None else {**row, "value": json.loads(row["value"])}

    # ===== FUNCTION: Store.set_setting() =====
    # ID: F0387 · method · used
    # ORIGINAL FILE: backend/app/store.py:404-407
    # ROLE: Replace a JSON setting (who changed it is stored).
    # INPUTS:
    #   key: str, value: dict, actor: str.
    # OUTPUT:
    #   dict.
    # CALLED BY:
    #   <- F0091 create_app.set_deep_harness() (calls)
    # CALLS:
    #   -> F0348 _SqliteDb.run() (calls)
    #   -> F0352 _PostgresDb.run() (calls)
    #   -> F0344 _now() (calls)
    #   -> F0386 Store.get_setting() (calls)
    def set_setting(self, key: str, value: dict, actor: str) -> dict:
        self._db.run([("delete from setting where key=?", (key,)),
                      ("insert into setting(key,value,updated_by,updated_at) values(?,?,?,?)", (key, json.dumps(value), actor, _now()))])
        return self.get_setting(key)  # type: ignore[return-value]

    # ===== FUNCTION: Store.decision_stats() =====
    # ID: F0388 · method · used
    # ORIGINAL FILE: backend/app/store.py:409-426
    # ROLE: Acceptance and override statistics of recommendations, with the experts' reason codes.
    # INPUTS:
    #   snapshot_id: str | None.
    # OUTPUT:
    #   dict -> submitted, decided, accepted, rejected, modified, acceptance_pct, override_pct, reason_codes, override_reasons.
    # CALLED BY:
    #   <- F0255 MoatEngine.view() (calls)
    #   <- F0261 RoleCenter._facts() (calls)
    # CALLS:
    #   -> F0367 Store.list_recommendations() (calls)
    #   -> F0383 Store.feedback() (calls)
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

    # ===== FUNCTION: Store.counts() =====
    # ID: F0389 · method · used
    # ORIGINAL FILE: backend/app/store.py:428-436
    # ROLE: Recommendation counts by status (+ number of analyses), optionally for one snapshot.
    # INPUTS:
    #   snapshot_id: str | None.
    # OUTPUT:
    #   dict -> {"analyses": n, "recommendations": {status: n}}.
    # CALLED BY:
    #   <- F0236 Dashboards._executive() (calls)
    #   <- F0031 create_app.status() (calls)
    #   <- F0255 MoatEngine.view() (calls)
    #   <- F0952 _exercise_store() (calls)
    # CALLS:
    #   -> F0349 _SqliteDb.query() (calls)
    #   -> F0353 _PostgresDb.query() (calls)
    def counts(self, snapshot_id: str | None = None) -> dict:
        """Recommendation counts by status; optionally only for one SAP snapshot (one customer)."""
        if snapshot_id:
            rows = self._db.query("select r.status, count(*) as n from recommendation r join analysis a on a.id = r.analysis_id where a.snapshot_id=? group by r.status", (snapshot_id,))
            analyses = self._db.query("select count(*) as n from analysis where snapshot_id=?", (snapshot_id,), fetch="one")
            return {"analyses": int(analyses["n"]), "recommendations": {row["status"]: int(row["n"]) for row in rows}}
        rows = self._db.query("select status, count(*) as n from recommendation group by status")
        analyses = self._db.query("select count(*) as n from analysis", fetch="one")
        return {"analyses": int(analyses["n"]), "recommendations": {row["status"]: int(row["n"]) for row in rows}}
