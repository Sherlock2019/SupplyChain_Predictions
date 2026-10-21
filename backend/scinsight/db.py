"""Database access for SupplyChain Insight AI: PostgreSQL (deployments) or SQLite (hermetic tests), with versioned SQL migrations.

Migrations live in backend/scinsight/migrations as NNNN_name.sql (all databases) or NNNN_name.postgres.sql (PostgreSQL only)
and are applied once each, in order, recorded in schema_migrations.
"""
from __future__ import annotations

import sqlite3
import threading
from collections.abc import Iterable
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

MIGRATIONS = Path(__file__).resolve().parent / "migrations"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def ensure_postgres_database(url: str) -> bool:
    """Create the target PostgreSQL database if it does not exist (existing Compose volumes / managed PostgreSQL never
    re-run init scripts). Returns True when it was created."""
    from urllib.parse import urlsplit, urlunsplit

    import psycopg

    parts = urlsplit(url)
    name = parts.path.lstrip("/")
    admin = urlunsplit((parts.scheme, parts.netloc, "/postgres", parts.query, ""))
    with psycopg.connect(admin, autocommit=True) as conn:
        if conn.execute("select 1 from pg_database where datname=%s", (name,)).fetchone():
            return False
        conn.execute(psycopg.sql.SQL("create database {}").format(psycopg.sql.Identifier(name)))
        return True


class Database:
    def __init__(self, url: str):
        self.url = url
        self._lock = threading.RLock()
        if url.startswith("sqlite:///"):
            self.dialect = "sqlite"
            path = url.removeprefix("sqlite:///")
            if path != ":memory:":
                Path(path).parent.mkdir(parents=True, exist_ok=True)
            self._conn = sqlite3.connect(path, check_same_thread=False)
            self._conn.row_factory = lambda cursor, row: {col[0]: row[i] for i, col in enumerate(cursor.description)}
            self._conn.execute("pragma foreign_keys = on")
        elif url.startswith(("postgresql://", "postgres://")):
            from psycopg.rows import dict_row
            from psycopg_pool import ConnectionPool

            self.dialect = "postgres"
            self._pool = ConnectionPool(url, min_size=1, max_size=10, kwargs={"row_factory": dict_row}, open=True)
        else:
            raise ValueError("SCI_DATABASE_URL must be sqlite:///path or postgresql://...")

    # ------------------------------------------------------------------ execution
    def _sql(self, sql: str) -> str:
        return sql.replace("?", "%s") if self.dialect == "postgres" else sql

    def query(self, sql: str, params: Iterable[Any] = ()) -> list[dict]:
        if self.dialect == "sqlite":
            with self._lock:
                return self._conn.execute(sql, tuple(params)).fetchall()
        with self._pool.connection() as conn:
            return conn.execute(self._sql(sql), tuple(params)).fetchall()

    def one(self, sql: str, params: Iterable[Any] = ()) -> dict | None:
        rows = self.query(sql, params)
        return rows[0] if rows else None

    def execute(self, sql: str, params: Iterable[Any] = ()) -> int:
        if self.dialect == "sqlite":
            with self._lock, self._conn:
                return self._conn.execute(sql, tuple(params)).rowcount
        with self._pool.connection() as conn, conn.transaction():
            return conn.execute(self._sql(sql), tuple(params)).rowcount

    def executemany(self, sql: str, rows: list[tuple]) -> None:
        if not rows:
            return
        if self.dialect == "sqlite":
            with self._lock, self._conn:
                self._conn.executemany(sql, rows)
            return
        with self._pool.connection() as conn, conn.transaction(), conn.cursor() as cur:
            cur.executemany(self._sql(sql), rows)

    def transaction(self, statements: list[tuple[str, tuple]]) -> None:
        """Run several statements atomically (all or nothing)."""
        if self.dialect == "sqlite":
            with self._lock, self._conn:
                for sql, params in statements:
                    self._conn.execute(sql, params)
            return
        with self._pool.connection() as conn, conn.transaction():
            conn.execute("select pg_advisory_xact_lock(8817001)")
            for sql, params in statements:
                conn.execute(self._sql(sql), params)

    def atomic(self, fn, lock_id: int = 8817002):
        """Run fn(q) inside one transaction holding an exclusive lock; q(sql, params) returns rows. For read-then-write logic
        such as the audit hash chain or status transitions, so concurrent requests cannot interleave."""
        if self.dialect == "sqlite":
            with self._lock, self._conn:
                return fn(lambda sql, params=(): self._conn.execute(sql, tuple(params)).fetchall()
                          if sql.lstrip().lower().startswith("select") else self._conn.execute(sql, tuple(params)).rowcount)
        with self._pool.connection() as conn, conn.transaction():
            conn.execute("select pg_advisory_xact_lock(%s)", (lock_id,))

            def q(sql, params=()):
                cur = conn.execute(self._sql(sql), tuple(params))
                return cur.fetchall() if sql.lstrip().lower().startswith("select") else cur.rowcount
            return fn(q)

    def _script(self, script: str) -> None:
        if self.dialect == "sqlite":
            with self._lock:
                self._conn.executescript(script)
            return
        # Strip full-line comments first: a ';' inside a comment must not split a statement.
        code = "\n".join(line for line in script.splitlines() if not line.strip().startswith("--"))
        with self._pool.connection() as conn, conn.transaction():
            conn.execute("select pg_advisory_xact_lock(8817000)")
            for statement in filter(None, (s.strip() for s in code.split(";"))):
                conn.execute(statement)

    # ------------------------------------------------------------------ migrations
    def migrate(self) -> list[str]:
        self._script("create table if not exists schema_migrations (version text primary key, applied_at text not null)")
        applied = {r["version"] for r in self.query("select version from schema_migrations")}
        done = []
        for path in sorted(MIGRATIONS.glob("*.sql")):
            version = path.stem
            if version in applied:
                continue
            if path.stem.endswith(".postgres") and self.dialect != "postgres":
                continue
            self._script(path.read_text(encoding="utf-8"))
            self.execute("insert into schema_migrations(version, applied_at) values(?, ?)", (version, now_iso()))
            done.append(version)
        return done
