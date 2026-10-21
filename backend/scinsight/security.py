"""Authentication, tenant scoping, role checks and the tamper-evident audit chain.

The tenant and the roles come ONLY from the authenticated API key (users + role_assignments). A client-supplied tenant
(X-Tenant header) is never trusted: if it differs from the key's tenant the request is rejected. Approval authority is
checked per recommendation domain on the server — a Flowise session or an LLM cannot grant itself a role.
"""
from __future__ import annotations

import hashlib
import hmac
import json
from dataclasses import dataclass

from fastapi import HTTPException

from backend.scinsight.db import Database, now_iso
from backend.scinsight.fixtures import key_hash

# Who may record a human decision, per recommendation domain.
REVIEW_AUTHORITY = {
    "factory": {"production_planner", "supply_chain_director"},
    "procurement": {"procurement_manager", "supply_chain_director"},
    "warehouse": {"warehouse_manager", "supply_chain_director"},
    "inventory": {"warehouse_manager", "supply_chain_director"},
    "logistics": {"logistics_manager", "supply_chain_director"},
    "quality": {"quality_manager", "supply_chain_director"},
}
HUMAN_ROLES = {"planner", "production_planner", "procurement_manager", "warehouse_manager", "logistics_manager", "quality_manager", "supply_chain_director"}
READ_ROLES = HUMAN_ROLES | {"agent_service", "mlops_engineer"}


@dataclass(frozen=True)
class Principal:
    user_id: str
    tenant_id: str
    roles: frozenset[str]
    name: str

    @property
    def is_human(self) -> bool:
        return bool(self.roles & HUMAN_ROLES) and "agent_service" not in self.roles


class Security:
    def __init__(self, db: Database):
        self.db = db

    def authenticate(self, api_key: str | None, claimed_tenant: str | None = None) -> Principal:
        if not api_key:
            self.audit("anonymous", "-", [], "auth.missing_key", {})
            raise HTTPException(status_code=401, detail="Missing API key (X-API-Key or Authorization: Bearer)")
        row = self.db.one("select * from users where api_key_hash=? and active=1", (key_hash(api_key),))
        if row is None or not hmac.compare_digest(row["api_key_hash"], key_hash(api_key)):
            self.audit("anonymous", "-", [], "auth.invalid_key", {})
            raise HTTPException(status_code=401, detail="Invalid API key")
        roles = frozenset(r["role"] for r in self.db.query("select role from role_assignments where user_id=? and tenant_id=?", (row["id"], row["tenant_id"])))
        if claimed_tenant and claimed_tenant != row["tenant_id"]:
            self.audit(row["tenant_id"], row["id"], sorted(roles), "auth.forged_tenant", {"claimed": claimed_tenant})
            raise HTTPException(status_code=403, detail="Tenant mismatch: the tenant is defined by your credentials, not by the request")
        return Principal(row["id"], row["tenant_id"], roles, row["name"])

    @staticmethod
    def require(principal: Principal, allowed: set[str], what: str) -> None:
        if not principal.roles & allowed:
            raise HTTPException(status_code=403, detail=f"{what} requires one of: {', '.join(sorted(allowed))}")

    def require_reviewer(self, principal: Principal, domain: str) -> None:
        allowed = REVIEW_AUTHORITY.get(domain, {"supply_chain_director"})
        if not principal.is_human or not principal.roles & allowed:
            self.audit(principal.tenant_id, principal.user_id, sorted(principal.roles), "review.forbidden", {"domain": domain})
            raise HTTPException(status_code=403, detail=f"Only an authorised human reviewer ({', '.join(sorted(allowed))}) can decide a {domain} recommendation")

    # ------------------------------------------------------------------ audit hash chain
    def audit(self, tenant_id: str, actor: str, roles: list[str], action: str, details: dict) -> None:
        ts, body = now_iso(), json.dumps(details, sort_keys=True, default=str)

        def write(q):  # read the chain head and append under one lock (no interleaving between concurrent requests)
            last = q("select id, hash from audit_events order by id desc limit 1")
            prev, next_id = (last[0]["hash"], last[0]["id"] + 1) if last else ("GENESIS", 1)
            digest = hashlib.sha256("|".join((prev, ts, tenant_id, actor, action, body)).encode()).hexdigest()
            q("insert into audit_events(id,tenant_id,actor,roles,action,details,ts,prev_hash,hash) values(?,?,?,?,?,?,?,?,?)",
              (next_id, tenant_id, actor, json.dumps(roles), action, body, ts, prev, digest))
        self.db.atomic(write, lock_id=8817003)

    def verify_chain(self) -> bool:
        prev = "GENESIS"
        for e in self.db.query("select * from audit_events order by id"):
            expected = hashlib.sha256("|".join((prev, e["ts"], e["tenant_id"], e["actor"], e["action"], e["details"])).encode()).hexdigest()
            if e["prev_hash"] != prev or e["hash"] != expected:
                return False
            prev = e["hash"]
        return True
