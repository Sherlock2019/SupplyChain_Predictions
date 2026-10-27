# ======================================================================================================
# ANNOTATED COPY (learning only: never imported, never executed)
# ORIGINAL FILE: backend/scinsight/db.py
# What this module is: the data-access layer of the SCInsight API. One small class hides the difference between
# SQLite (hermetic tests) and PostgreSQL (deployments): parameter style, connections/pool, transactions, locks,
# and the versioned SQL migrations (backend/scinsight/migrations/*.sql).
# Only comment lines were added (AST-verified).
# ======================================================================================================

"""Database access for SupplyChain Insight AI: PostgreSQL (deployments) or SQLite (hermetic tests), with versioned SQL migrations.

Migrations live in backend/scinsight/migrations as NNNN_name.sql (all databases) or NNNN_name.postgres.sql (PostgreSQL only)
and are applied once each, in order, recorded in schema_migrations.
"""
from __future__ import annotations

# sqlite3: Python's built-in SQLite driver. threading: a re-entrant lock serialises access to the single SQLite connection.
import sqlite3
import threading
# Iterable: type of the SQL parameters (tuple or list).
from collections.abc import Iterable
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Folder of the .sql migration files, next to this module.
MIGRATIONS = Path(__file__).resolve().parent / "migrations"


# ===== FUNCTION: now_iso() =====
# ID: F0416 · function · used
# ORIGINAL FILE: backend/scinsight/db.py:18-19
# ROLE: Current UTC time as an ISO-8601 string with seconds, e.g. "2026-10-21T06:00:00+00:00" (all timestamps in the DB).
# INPUTS:
#   none.
# OUTPUT:
#   str -> ISO timestamp.
# CALLED BY:
#   <- F0429 Database.migrate() (calls)
#   <- F0432 load() (calls)
#   <- F0534 train_lead_time_model() (calls)
#   <- F0535 promote() (calls)
#   <- F0537 retraining_request() (calls)
#   <- F0765 KnowledgeBase.ingest_dir() (calls)
#   <- F1809 KnowledgeBase._log() (calls)
#   <- F1892 build_candidate_index() (calls)
#   <- F1895 validate_config() (calls)
#   <- F1897 _activate() (calls)
#   <- F1904 Registry.ensure_baseline() (calls)
#   <- F1908 Registry.save_draft_config() (calls)
# CALLS:
#   (none found)
def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


# ===== FUNCTION: ensure_postgres_database() =====
# ID: F0417 · function · used
# ORIGINAL FILE: backend/scinsight/db.py:22-36
# ROLE: Create the target PostgreSQL database when it does not exist (existing volumes / managed PostgreSQL never re-run init scripts).
# INPUTS:
#   url: str -> postgresql://user:pass@host:port/dbname (the password stays inside the URL, never logged here).
# OUTPUT:
#   bool -> True when the database was created, False when it already existed.
# CALLED BY:
#   <- F1993 create_router() (calls)
# CALLS:
#   (none found)
def ensure_postgres_database(url: str) -> bool:
    """Create the target PostgreSQL database if it does not exist (existing Compose volumes / managed PostgreSQL never
    re-run init scripts). Returns True when it was created."""
    # Local imports: psycopg is only needed for PostgreSQL deployments (SQLite tests never import it).
    from urllib.parse import urlsplit, urlunsplit

    import psycopg

    # Split the URL into scheme, netloc (user:pass@host:port), path (/dbname), query, fragment.
    parts = urlsplit(url)
    name = parts.path.lstrip("/")
    # Same server, but connect to the always-present maintenance database "postgres".
    admin = urlunsplit((parts.scheme, parts.netloc, "/postgres", parts.query, ""))
    # autocommit=True: CREATE DATABASE cannot run inside a transaction. `with` closes the connection automatically.
    with psycopg.connect(admin, autocommit=True) as conn:
        # %s = psycopg parameter placeholder: the name is passed safely as data.
        if conn.execute("select 1 from pg_database where datname=%s", (name,)).fetchone():
            return False
        # Identifiers cannot be bound as parameters: psycopg.sql.Identifier quotes the database name safely.
        conn.execute(psycopg.sql.SQL("create database {}").format(psycopg.sql.Identifier(name)))
        return True


# ===== CLASS: Database =====
# ID: F0418 · class · used
# ORIGINAL FILE: backend/scinsight/db.py:39-145
# ROLE: Database wrapper used by every SCInsight module: query/one/execute/executemany/transaction/atomic + migrations.
# FIELDS:
#   url: str        -> connection URL.
#   dialect: str    -> "sqlite" or "postgres".
#   _lock: RLock    -> serialises SQLite access (one shared connection) across FastAPI worker threads.
#   _conn / _pool   -> SQLite connection, or psycopg ConnectionPool (1..10 connections) for PostgreSQL.
# CALLED BY:
#   <- F1993 create_router() (references)
#   <- F1993 create_router() (calls)
#   <- F0432 load() (references)
#   <- F0532 _rows() (references)
#   <- F0534 train_lead_time_model() (references)
#   <- F0535 promote() (references)
#   <- F0536 predict_lead_time() (references)
#   <- F0537 retraining_request() (references)
#   <- F0764 KnowledgeBase.__init__() (references)
#   <- F1903 Registry.__init__() (references)
#   <- F0775 Security.__init__() (references)
#   <- F0312 Service.__init__() (references)
# CALLS:
#   (none found)
class Database:
    # ===== FUNCTION: Database.__init__() =====
    # ID: F0419 · method · used (framework)
    # ORIGINAL FILE: backend/scinsight/db.py:40-58
    # ROLE: Open the database selected by the URL scheme.
    # INPUTS:
    #   url: str -> "sqlite:///path" (or sqlite:///:memory:) or "postgresql://...".
    # OUTPUT:
    #   None (raises ValueError for any other scheme).
    # CALLED BY:
    #   (none found)
    # CALLS:
    #   (none found)
    def __init__(self, url: str):
        self.url = url
        # RLock = re-entrant: the same thread may acquire it again (e.g. query() called inside atomic()).
        self._lock = threading.RLock()
        if url.startswith("sqlite:///"):
            self.dialect = "sqlite"
            # str.removeprefix (Python 3.9+): "sqlite:///a/b.db" -> "a/b.db".
            path = url.removeprefix("sqlite:///")
            if path != ":memory:":
                # Create the parent folder of the database file if needed.
                Path(path).parent.mkdir(parents=True, exist_ok=True)
            # check_same_thread=False: FastAPI serves requests from several threads; the RLock keeps it safe.
            self._conn = sqlite3.connect(path, check_same_thread=False)
            # Make every fetched row a dict {column_name: value} (same shape as psycopg's dict_row).
            self._conn.row_factory = lambda cursor, row: {col[0]: row[i] for i, col in enumerate(cursor.description)}
            # SQLite does not enforce foreign keys unless asked.
            self._conn.execute("pragma foreign_keys = on")
        elif url.startswith(("postgresql://", "postgres://")):
            # Imported only for PostgreSQL. dict_row: rows as dicts. ConnectionPool: reuses connections between requests.
            from psycopg.rows import dict_row
            from psycopg_pool import ConnectionPool

            self.dialect = "postgres"
            self._pool = ConnectionPool(url, min_size=1, max_size=10, kwargs={"row_factory": dict_row}, open=True)
        else:
            raise ValueError("SCI_DATABASE_URL must be sqlite:///path or postgresql://...")

    # ------------------------------------------------------------------ execution
    # ===== FUNCTION: Database._sql() =====
    # ID: F0420 · method · used
    # ORIGINAL FILE: backend/scinsight/db.py:61-62
    # ROLE: Translate the portable "?" placeholder into PostgreSQL's "%s" (SQLite keeps "?").
    # INPUTS:
    #   sql: str -> SQL text written with "?" placeholders.
    # OUTPUT:
    #   str -> SQL for the current dialect.
    # CALLED BY:
    #   <- F0421 Database.query() (calls)
    #   <- F0423 Database.execute() (calls)
    #   <- F0424 Database.executemany() (calls)
    #   <- F0425 Database.transaction() (calls)
    #   <- F0427 Database.atomic.q() (calls)
    # CALLS:
    #   (none found)
    def _sql(self, sql: str) -> str:
        return sql.replace("?", "%s") if self.dialect == "postgres" else sql

    # ===== FUNCTION: Database.query() =====
    # ID: F0421 · method · used
    # ORIGINAL FILE: backend/scinsight/db.py:64-69
    # ROLE: Run a SELECT and return all rows as a list of dicts.
    # INPUTS:
    #   sql: str               -> SELECT statement with "?" placeholders.
    #   params: Iterable[Any]  -> values bound to the placeholders (never string-concatenated -> no SQL injection).
    # OUTPUT:
    #   list[dict] -> rows.
    # CALLED BY:
    #   <- F2015 create_router.rag_documents() (calls)
    #   <- F2027 create_router.audit() (calls)
    #   <- F0422 Database.one() (calls)
    #   <- F0429 Database.migrate() (calls)
    #   <- F0532 _rows() (calls)
    #   <- F0537 retraining_request() (calls)
    #   <- F0766 KnowledgeBase.search() (calls)
    #   <- F1847 register.metrics() (calls)
    #   <- F1860 inventory() (calls)
    #   <- F1887 FlowiseAdapter.table_rows() (calls)
    #   <- F1907 Registry.history() (calls)
    #   <- F1914 Registry.experiments() (calls)
    # CALLS:
    #   -> F0420 Database._sql() (calls)
    def query(self, sql: str, params: Iterable[Any] = ()) -> list[dict]:
        if self.dialect == "sqlite":
            # `with self._lock:` acquires the lock and always releases it, even on error.
            with self._lock:
                return self._conn.execute(sql, tuple(params)).fetchall()
        # Borrow a pooled connection for the duration of the block.
        with self._pool.connection() as conn:
            return conn.execute(self._sql(sql), tuple(params)).fetchall()

    # ===== FUNCTION: Database.one() =====
    # ID: F0422 · method · used
    # ORIGINAL FILE: backend/scinsight/db.py:71-73
    # ROLE: Convenience: first row of a query, or None.
    # INPUTS:
    #   sql, params -> as in query().
    # OUTPUT:
    #   dict | None.
    # CALLED BY:
    #   <- F0432 load() (calls)
    #   <- F0535 promote() (calls)
    #   <- F0536 predict_lead_time() (calls)
    #   <- F1806 KnowledgeBase.active() (calls)
    #   <- F0765 KnowledgeBase.ingest_dir() (calls)
    #   <- F1904 Registry.ensure_baseline() (calls)
    #   <- F1905 Registry.get_active_rag_config() (calls)
    #   <- F1906 Registry.get() (calls)
    #   <- F1912 Registry.job() (calls)
    #   <- F1915 Registry.experiment() (calls)
    #   <- F0776 Security.authenticate() (calls)
    #   <- F0313 Service.snapshot() (calls)
    # CALLS:
    #   -> F0421 Database.query() (calls)
    def one(self, sql: str, params: Iterable[Any] = ()) -> dict | None:
        rows = self.query(sql, params)
        return rows[0] if rows else None

    # ===== FUNCTION: Database.execute() =====
    # ID: F0423 · method · used
    # ORIGINAL FILE: backend/scinsight/db.py:75-80
    # ROLE: Run one INSERT / UPDATE / DELETE in its own transaction; return the number of affected rows.
    # INPUTS:
    #   sql, params -> statement + bound values.
    # OUTPUT:
    #   int -> rowcount (e.g. 0 when an UPDATE's WHERE matched nothing; callers use it for status transitions).
    # CALLED BY:
    #   <- F0429 Database.migrate() (calls)
    #   <- F0432 load() (calls)
    #   <- F0534 train_lead_time_model() (calls)
    #   <- F0535 promote() (calls)
    #   <- F0537 retraining_request() (calls)
    #   <- F1809 KnowledgeBase._log() (calls)
    #   <- F1904 Registry.ensure_baseline() (calls)
    #   <- F1908 Registry.save_draft_config() (calls)
    #   <- F1909 Registry.set_status() (calls)
    #   <- F1910 Registry.start_job() (calls)
    #   <- F1911 Registry.start_job.run() (calls)
    #   <- F1913 Registry.save_experiment() (calls)
    # CALLS:
    #   -> F0425 Database.transaction() (calls)
    #   -> F0420 Database._sql() (calls)
    def execute(self, sql: str, params: Iterable[Any] = ()) -> int:
        if self.dialect == "sqlite":
            # `with self._conn:` = SQLite transaction: commit on success, rollback on exception.
            with self._lock, self._conn:
                return self._conn.execute(sql, tuple(params)).rowcount
        # conn.transaction(): commit at the end of the block, rollback on exception.
        with self._pool.connection() as conn, conn.transaction():
            return conn.execute(self._sql(sql), tuple(params)).rowcount

    # ===== FUNCTION: Database.executemany() =====
    # ID: F0424 · method · used
    # ORIGINAL FILE: backend/scinsight/db.py:82-90
    # ROLE: Run the same statement for many parameter rows in one transaction (bulk fixture loading).
    # INPUTS:
    #   sql: str          -> statement with placeholders.
    #   rows: list[tuple] -> one tuple of values per row.
    # OUTPUT:
    #   None.
    # CALLED BY:
    #   <- F0752 PgVectorRag.add() (calls)
    #   <- F0432 load() (calls)
    #   <- F0433 load.upsert() (calls)
    # CALLS:
    #   -> F0425 Database.transaction() (calls)
    #   -> F0420 Database._sql() (calls)
    def executemany(self, sql: str, rows: list[tuple]) -> None:
        # Nothing to do for an empty list.
        if not rows:
            return
        if self.dialect == "sqlite":
            with self._lock, self._conn:
                self._conn.executemany(sql, rows)
            return
        with self._pool.connection() as conn, conn.transaction(), conn.cursor() as cur:
            cur.executemany(self._sql(sql), rows)

    # ===== FUNCTION: Database.transaction() =====
    # ID: F0425 · method · used
    # ORIGINAL FILE: backend/scinsight/db.py:92-102
    # ROLE: Run several statements atomically (all succeed or none), e.g. "insert execution record + set status executed".
    # INPUTS:
    #   statements: list[tuple[str, tuple]] -> [(sql, params), ...].
    # OUTPUT:
    #   None.
    # CALLED BY:
    #   <- F0352 _PostgresDb.run() (calls)
    #   <- F0358 Store.audit() (calls)
    #   <- F0423 Database.execute() (calls)
    #   <- F0424 Database.executemany() (calls)
    #   <- F0426 Database.atomic() (calls)
    #   <- F0428 Database._script() (calls)
    #   <- F0535 promote() (calls)
    #   <- F0765 KnowledgeBase.ingest_dir() (calls)
    #   <- F1808 KnowledgeBase.build_index() (calls)
    #   <- F1897 _activate() (calls)
    #   <- F0340 Service.record_sap_execution() (calls)
    # CALLS:
    #   -> F0420 Database._sql() (calls)
    def transaction(self, statements: list[tuple[str, tuple]]) -> None:
        """Run several statements atomically (all or nothing)."""
        if self.dialect == "sqlite":
            with self._lock, self._conn:
                # Tuple unpacking in the for loop: each item is (sql, params).
                for sql, params in statements:
                    self._conn.execute(sql, params)
            return
        with self._pool.connection() as conn, conn.transaction():
            # Transaction-scoped advisory lock 8817001: serialises these multi-statement writes across API workers.
            conn.execute("select pg_advisory_xact_lock(8817001)")
            for sql, params in statements:
                conn.execute(self._sql(sql), params)

    # ===== FUNCTION: Database.atomic() =====
    # ID: F0426 · method · used
    # ORIGINAL FILE: backend/scinsight/db.py:104-117
    # ROLE: Run fn(q) inside ONE transaction holding an exclusive lock, for read-then-write logic (audit chain, status changes).
    # INPUTS:
    #   fn: callable      -> function receiving q(sql, params=()); q returns rows for SELECT, rowcount otherwise.
    #   lock_id: int      -> PostgreSQL advisory lock number (8817002 default; 8817003 for the audit chain).
    # OUTPUT:
    #   whatever fn returns (e.g. True/False "was the row changed").
    # CALLED BY:
    #   <- F0779 Security.audit() (calls)
    #   <- F0337 Service.review() (calls)
    #   <- F0341 Service.reconcile() (calls)
    # CALLS:
    #   -> F0425 Database.transaction() (calls)
    #   -> F0427 Database.atomic.q() (references)
    def atomic(self, fn, lock_id: int = 8817002):
        """Run fn(q) inside one transaction holding an exclusive lock; q(sql, params) returns rows. For read-then-write logic
        such as the audit hash chain or status transitions, so concurrent requests cannot interleave."""
        if self.dialect == "sqlite":
            with self._lock, self._conn:
                # Inline lambda as q: SELECT -> fetchall(), anything else -> rowcount. The Python RLock provides exclusivity.
                return fn(lambda sql, params=(): self._conn.execute(sql, tuple(params)).fetchall()
                          if sql.lstrip().lower().startswith("select") else self._conn.execute(sql, tuple(params)).rowcount)
        with self._pool.connection() as conn, conn.transaction():
            # Other transactions asking for the same lock id wait until this transaction commits.
            conn.execute("select pg_advisory_xact_lock(%s)", (lock_id,))

            # ===== FUNCTION: Database.atomic.q() =====
            # ID: F0427 · nested · used
            # ORIGINAL FILE: backend/scinsight/db.py:114-116
            # ROLE: The q() helper for PostgreSQL: same contract as the SQLite lambda above.
            # INPUTS:
            #   sql: str, params: tuple -> statement + values.
            # OUTPUT:
            #   list[dict] for SELECT, int rowcount otherwise.
            # CALLED BY:
            #   <- F0426 Database.atomic() (references)
            # CALLS:
            #   -> F0420 Database._sql() (calls)
            def q(sql, params=()):
                cur = conn.execute(self._sql(sql), tuple(params))
                return cur.fetchall() if sql.lstrip().lower().startswith("select") else cur.rowcount
            return fn(q)

    # ===== FUNCTION: Database._script() =====
    # ID: F0428 · method · used
    # ORIGINAL FILE: backend/scinsight/db.py:119-129
    # ROLE: Execute a multi-statement SQL script (used by migrations).
    # INPUTS:
    #   script: str -> the content of a .sql file.
    # OUTPUT:
    #   None.
    # CALLED BY:
    #   <- F0429 Database.migrate() (calls)
    # CALLS:
    #   -> F0425 Database.transaction() (calls)
    def _script(self, script: str) -> None:
        if self.dialect == "sqlite":
            with self._lock:
                # executescript runs every ";"-separated statement.
                self._conn.executescript(script)
            return
        # Strip full-line comments first: a ';' inside a comment must not split a statement.
        code = "\n".join(line for line in script.splitlines() if not line.strip().startswith("--"))
        with self._pool.connection() as conn, conn.transaction():
            # Lock 8817000: two API containers starting together cannot run the same migration twice.
            conn.execute("select pg_advisory_xact_lock(8817000)")
            # Split on ";", strip whitespace, filter(None, ...) drops empty strings.
            for statement in filter(None, (s.strip() for s in code.split(";"))):
                conn.execute(statement)

    # ------------------------------------------------------------------ migrations
    # ===== FUNCTION: Database.migrate() =====
    # ID: F0429 · method · used
    # ORIGINAL FILE: backend/scinsight/db.py:132-145
    # ROLE: Apply, in file-name order, every migration not yet recorded in schema_migrations.
    # INPUTS:
    #   self -> the database.
    # OUTPUT:
    #   list[str] -> versions applied by this call (e.g. ["0001_core", "0002_pgvector.postgres"]).
    # CALLED BY:
    #   <- F1993 create_router() (calls)
    # CALLS:
    #   -> F0428 Database._script() (calls)
    #   -> F0421 Database.query() (calls)
    #   -> F0423 Database.execute() (calls)
    #   -> F0416 now_iso() (calls)
    def migrate(self) -> list[str]:
        # Bookkeeping table: one row per applied migration.
        self._script("create table if not exists schema_migrations (version text primary key, applied_at text not null)")
        # Set comprehension of the versions already applied.
        applied = {r["version"] for r in self.query("select version from schema_migrations")}
        done = []
        # sorted(): 0001_... before 0002_...; glob("*.sql") lists the migration files.
        for path in sorted(MIGRATIONS.glob("*.sql")):
            # path.stem = file name without the last extension ("0002_pgvector.postgres").
            version = path.stem
            if version in applied:
                continue
            # PostgreSQL-only migrations (pgvector) are skipped on SQLite.
            if path.stem.endswith(".postgres") and self.dialect != "postgres":
                continue
            self._script(path.read_text(encoding="utf-8"))
            self.execute("insert into schema_migrations(version, applied_at) values(?, ?)", (version, now_iso()))
            done.append(version)
        return done
