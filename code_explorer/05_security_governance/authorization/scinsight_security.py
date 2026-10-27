# ======================================================================================================
# ANNOTATED COPY (learning only: never imported, never executed)
# ORIGINAL FILE: backend/scinsight/security.py
# What this module is: authentication (API key -> user), tenant scoping, role checks, per-domain review
# authority (who may approve what) and the tamper-evident audit hash chain of the SCInsight API.
# Only comment lines were added (AST-verified).
# ======================================================================================================

"""Authentication, tenant scoping, role checks and the tamper-evident audit chain.

The tenant and the roles come ONLY from the authenticated API key (users + role_assignments). A client-supplied tenant
(X-Tenant header) is never trusted: if it differs from the key's tenant the request is rejected. Approval authority is
checked per recommendation domain on the server — a Flowise session or an LLM cannot grant itself a role.
"""
from __future__ import annotations

# hashlib: SHA-256 for the audit chain. hmac: constant-time comparison (prevents timing attacks on key hashes).
import hashlib
import hmac
# json: audit details are stored as canonical JSON text.
import json
# @dataclass generates __init__/__eq__/__repr__; frozen=True makes instances immutable (a Principal cannot be edited).
from dataclasses import dataclass

# HTTPException: raising it inside a dependency/endpoint returns the HTTP error to the client.
from fastapi import HTTPException

# Database wrapper + UTC timestamp helper.
from backend.scinsight.db import Database, now_iso
# key_hash(key) = SHA-256 hex digest of an API key (keys are never stored in clear text).
from backend.scinsight.fixtures import key_hash

# Who may record a human decision, per recommendation domain.
# BUSINESS RULE: a factory recommendation can only be decided by the production planner or the director, etc.
REVIEW_AUTHORITY = {
    "factory": {"production_planner", "supply_chain_director"},
    "procurement": {"procurement_manager", "supply_chain_director"},
    "warehouse": {"warehouse_manager", "supply_chain_director"},
    "inventory": {"warehouse_manager", "supply_chain_director"},
    "logistics": {"logistics_manager", "supply_chain_director"},
    "quality": {"quality_manager", "supply_chain_director"},
}
# Roles held by people (as opposed to services such as the Flowise agent key).
HUMAN_ROLES = {"planner", "production_planner", "procurement_manager", "warehouse_manager", "logistics_manager", "quality_manager", "supply_chain_director"}
# Roles allowed to call the read/calculate endpoints: every human role + the agent service + the MLOps engineer.
# `|` on sets = union.
READ_ROLES = HUMAN_ROLES | {"agent_service", "mlops_engineer"}


# ===== CLASS: Principal =====
# ID: F0772 · class · used
# ORIGINAL FILE: backend/scinsight/security.py:32-41
# ROLE: The authenticated caller, built ONLY from the database row of its API key (never from the request body or an LLM).
# FIELDS:
#   user_id: str          -> e.g. u-production-planner.
#   tenant_id: str        -> e.g. scinsight-cosmetics (all SQL queries filter on it).
#   roles: frozenset[str] -> immutable set of role names from role_assignments.
#   name: str             -> display name.
# CALLED BY:
#   <- F0113 create_app.principal() (references)
#   <- F0114 create_app.reader() (references)
#   <- F0115 create_app.biz_date() (references)
#   <- F0117 create_app.context() (references)
#   <- F0118 create_app.validate_context() (references)
#   <- F0119 create_app.sap_inventory() (references)
#   <- F0120 create_app.sap_bom() (references)
#   <- F0121 create_app.sap_production_orders() (references)
#   <- F0122 create_app.sap_purchase_orders() (references)
#   <- F0123 create_app.sap_warehouses() (references)
#   <- F0124 create_app.sap_suppliers() (references)
#   <- F0125 create_app.sap_write_blocked() (references)
# CALLS:
#   (none found)
@dataclass(frozen=True)
class Principal:
    user_id: str
    tenant_id: str
    roles: frozenset[str]
    name: str

    # ===== FUNCTION: Principal.is_human() =====
    # ID: F0773 · method · used (framework)
    # ORIGINAL FILE: backend/scinsight/security.py:39-41
    # ROLE: True when the caller is a person (has a human role) and is NOT the agent service.
    # INPUTS:
    #   self -> the principal.
    # OUTPUT:
    #   bool -> used to forbid approvals by agents and reported as "can_approve".
    # @property: read like an attribute (p.is_human), computed on each access.
    # CALLED BY:
    #   (none found)
    # CALLS:
    #   (none found)
    @property
    def is_human(self) -> bool:
        # `&` = set intersection; bool(non-empty set) is True.
        return bool(self.roles & HUMAN_ROLES) and "agent_service" not in self.roles


# ===== CLASS: Security =====
# ID: F0774 · class · used
# ORIGINAL FILE: backend/scinsight/security.py:44-92
# ROLE: Security service shared by all routes: authenticate keys, check roles / reviewer authority, write and verify the audit chain.
# FIELDS:
#   db: Database -> where users, role_assignments and audit_events live.
# CALLED BY:
#   <- F0112 create_app() (calls)
#   <- F0312 Service.__init__() (references)
# CALLS:
#   (none found)
class Security:
    # ===== FUNCTION: Security.__init__() =====
    # ID: F0775 · method · used (framework)
    # ORIGINAL FILE: backend/scinsight/security.py:45-46
    # ROLE: Keep a reference to the database.
    # INPUTS:
    #   db: Database -> the open database.
    # OUTPUT:
    #   None.
    # CALLED BY:
    #   (none found)
    # CALLS:
    #   -> F0418 Database (references)
    def __init__(self, db: Database):
        self.db = db

    # ===== FUNCTION: Security.authenticate() =====
    # ID: F0776 · method · used
    # ORIGINAL FILE: backend/scinsight/security.py:48-60
    # ROLE: Turn an API key into a Principal; reject missing / invalid keys (401) and forged tenants (403). Every failure is audited.
    # INPUTS:
    #   api_key: str | None         -> the key from X-API-Key or Authorization: Bearer.
    #   claimed_tenant: str | None  -> the X-Tenant header (only compared, never trusted).
    # OUTPUT:
    #   Principal -> user id, tenant, roles, name.
    # CALLED BY:
    #   <- F0113 create_app.principal() (calls)
    # CALLS:
    #   -> F0779 Security.audit() (calls)
    #   -> F0422 Database.one() (calls)
    #   -> F0430 key_hash() (calls)
    #   -> F0421 Database.query() (calls)
    #   -> F0772 Principal (calls)
    #   -> F0772 Principal (references)
    def authenticate(self, api_key: str | None, claimed_tenant: str | None = None) -> Principal:
        # No key at all -> 401 Unauthorized (and an audit entry by "anonymous").
        if not api_key:
            self.audit("anonymous", "-", [], "auth.missing_key", {})
            raise HTTPException(status_code=401, detail="Missing API key (X-API-Key or Authorization: Bearer)")
        # Look up the ACTIVE user whose stored hash equals the hash of the presented key ("?" = bound SQL parameter).
        row = self.db.one("select * from users where api_key_hash=? and active=1", (key_hash(api_key),))
        # hmac.compare_digest compares in constant time (defence in depth against timing side channels).
        if row is None or not hmac.compare_digest(row["api_key_hash"], key_hash(api_key)):
            self.audit("anonymous", "-", [], "auth.invalid_key", {})
            raise HTTPException(status_code=401, detail="Invalid API key")
        # Roles of this user IN ITS OWN tenant; frozenset(...) of a generator expression -> immutable set.
        roles = frozenset(r["role"] for r in self.db.query("select role from role_assignments where user_id=? and tenant_id=?", (row["id"], row["tenant_id"])))
        # SECURITY: a client cannot switch tenant by sending another X-Tenant value.
        if claimed_tenant and claimed_tenant != row["tenant_id"]:
            self.audit(row["tenant_id"], row["id"], sorted(roles), "auth.forged_tenant", {"claimed": claimed_tenant})
            raise HTTPException(status_code=403, detail="Tenant mismatch: the tenant is defined by your credentials, not by the request")
        # Positional construction: Principal(user_id, tenant_id, roles, name).
        return Principal(row["id"], row["tenant_id"], roles, row["name"])

    # ===== FUNCTION: Security.require() =====
    # ID: F0777 · method · used
    # ORIGINAL FILE: backend/scinsight/security.py:62-65
    # ROLE: Generic role gate: raise 403 unless the caller holds at least one of the allowed roles.
    # INPUTS:
    #   principal: Principal -> the caller.
    #   allowed: set[str]    -> accepted roles.
    #   what: str            -> description used in the error message ("Training a model").
    # OUTPUT:
    #   None (raises HTTPException 403 when not allowed).
    # @staticmethod: does not need `self`; called as security.require(...) or Security.require(...).
    # CALLED BY:
    #   <- F0114 create_app.reader() (calls)
    #   <- F0135 create_app.create_decision() (calls)
    #   <- F0143 create_app.train() (calls)
    #   <- F0144 create_app.promote() (calls)
    #   <- F0146 create_app.audit() (calls)
    #   <- F1820 register.admin() (calls)
    #   <- F1844 register.publish() (calls)
    #   <- F1845 register.rollback() (calls)
    #   <- F0340 Service.record_sap_execution() (calls)
    #   <- F0341 Service.reconcile() (calls)
    # CALLS:
    #   -> F0772 Principal (references)
    @staticmethod
    def require(principal: Principal, allowed: set[str], what: str) -> None:
        # Empty intersection -> no matching role.
        if not principal.roles & allowed:
            raise HTTPException(status_code=403, detail=f"{what} requires one of: {', '.join(sorted(allowed))}")

    # ===== FUNCTION: Security.require_reviewer() =====
    # ID: F0778 · method · used
    # ORIGINAL FILE: backend/scinsight/security.py:67-71
    # ROLE: Human-approval gate: only a HUMAN with the reviewer role of the recommendation's domain may decide it.
    # INPUTS:
    #   principal: Principal -> the would-be reviewer.
    #   domain: str          -> recommendation domain (factory, procurement, warehouse, inventory, logistics, quality).
    # OUTPUT:
    #   None (raises 403 and audits "review.forbidden" when not authorised).
    # CALLED BY:
    #   <- F0337 Service.review() (calls)
    # CALLS:
    #   -> F0772 Principal (references)
    #   -> F0779 Security.audit() (calls)
    def require_reviewer(self, principal: Principal, domain: str) -> None:
        # Unknown domains fall back to "director only" (safe default).
        allowed = REVIEW_AUTHORITY.get(domain, {"supply_chain_director"})
        # Two conditions: must be human (the agent key is refused even if misconfigured) AND hold a domain reviewer role.
        if not principal.is_human or not principal.roles & allowed:
            self.audit(principal.tenant_id, principal.user_id, sorted(principal.roles), "review.forbidden", {"domain": domain})
            raise HTTPException(status_code=403, detail=f"Only an authorised human reviewer ({', '.join(sorted(allowed))}) can decide a {domain} recommendation")

    # ------------------------------------------------------------------ audit hash chain
    # ===== FUNCTION: Security.audit() =====
    # ID: F0779 · method · used
    # ORIGINAL FILE: backend/scinsight/security.py:74-83
    # ROLE: Append one event to the tamper-evident audit chain: hash = SHA-256(previous hash | ts | tenant | actor | action | details).
    # INPUTS:
    #   tenant_id: str    -> tenant of the event ("anonymous" for failed logins).
    #   actor: str        -> user id ("-" when unknown).
    #   roles: list[str]  -> roles of the actor at that moment.
    #   action: str       -> event name, e.g. "decision.approve", "sap.write_blocked".
    #   details: dict     -> event data (stored as sorted-key JSON).
    # OUTPUT:
    #   None (one row inserted into audit_events).
    # CALLED BY:
    #   <- F0118 create_app.validate_context() (calls)
    #   <- F0125 create_app.sap_write_blocked() (calls)
    #   <- F0143 create_app.train() (calls)
    #   <- F0144 create_app.promote() (calls)
    #   <- F0145 create_app.retraining() (calls)
    #   <- F1821 register.audit() (calls)
    #   <- F0776 Security.authenticate() (calls)
    #   <- F0778 Security.require_reviewer() (calls)
    #   <- F0314 Service._save_run() (calls)
    #   <- F0333 Service.create_decision() (calls)
    #   <- F0337 Service.review() (calls)
    #   <- F0339 Service.withdraw() (calls)
    # CALLS:
    #   -> F0416 now_iso() (calls)
    #   -> F0426 Database.atomic() (calls)
    #   -> F0780 Security.audit.write() (references)
    def audit(self, tenant_id: str, actor: str, roles: list[str], action: str, details: dict) -> None:
        # sort_keys=True: identical details always give identical JSON text -> reproducible hashes. default=str handles dates.
        ts, body = now_iso(), json.dumps(details, sort_keys=True, default=str)

        # ===== FUNCTION: Security.audit.write() =====
        # ID: F0780 · nested · used
        # ORIGINAL FILE: backend/scinsight/security.py:77-82
        # ROLE: The read-then-append step, run inside Database.atomic so two requests cannot both extend the same chain head.
        # INPUTS:
        #   q -> function q(sql, params) provided by Database.atomic (returns rows for SELECT, rowcount otherwise).
        # OUTPUT:
        #   None.
        # CALLED BY:
        #   <- F0779 Security.audit() (references)
        # CALLS:
        #   (none found)
        def write(q):  # read the chain head and append under one lock (no interleaving between concurrent requests)
            # Last event = current head of the chain.
            last = q("select id, hash from audit_events order by id desc limit 1")
            # First event links to the constant "GENESIS"; otherwise link to the previous hash and take the next id.
            prev, next_id = (last[0]["hash"], last[0]["id"] + 1) if last else ("GENESIS", 1)
            # "|".join(...) builds the canonical string; .encode() -> bytes; .hexdigest() -> 64 hex characters.
            digest = hashlib.sha256("|".join((prev, ts, tenant_id, actor, action, body)).encode()).hexdigest()
            q("insert into audit_events(id,tenant_id,actor,roles,action,details,ts,prev_hash,hash) values(?,?,?,?,?,?,?,?,?)",
              (next_id, tenant_id, actor, json.dumps(roles), action, body, ts, prev, digest))
        # lock_id: a PostgreSQL advisory lock number reserved for the audit chain (SQLite uses a Python lock instead).
        self.db.atomic(write, lock_id=8817003)

    # ===== FUNCTION: Security.verify_chain() =====
    # ID: F0781 · method · used
    # ORIGINAL FILE: backend/scinsight/security.py:85-92
    # ROLE: Recompute every hash from GENESIS; any edited, deleted or inserted row breaks the chain.
    # INPUTS:
    #   self -> uses self.db.
    # OUTPUT:
    #   bool -> True if the whole chain is intact.
    # CALLED BY:
    #   <- F0146 create_app.audit() (calls)
    # CALLS:
    #   -> F0421 Database.query() (calls)
    def verify_chain(self) -> bool:
        prev = "GENESIS"
        # Iterate in insertion order.
        for e in self.db.query("select * from audit_events order by id"):
            expected = hashlib.sha256("|".join((prev, e["ts"], e["tenant_id"], e["actor"], e["action"], e["details"])).encode()).hexdigest()
            # Both links must match: the stored previous hash and the recomputed own hash.
            if e["prev_hash"] != prev or e["hash"] != expected:
                return False
            prev = e["hash"]
        return True
