# ======================================================================================================
# ANNOTATED COPY (learning only: never imported, never executed)
# ORIGINAL FILE: backend/app/auth.py
# What this module is: API-key authentication of the SPARC / Aurelia FastAPI gateway (backend/app/main.py). Keys map to an
# identity and one of two roles: "assistant" (agents, planners) or "manager" (approvals, execution, audit).
# Only comment lines were added (AST-verified).
# ======================================================================================================
from __future__ import annotations

# hmac.compare_digest: constant-time string comparison (no timing leak about how many characters matched).
import hmac
from dataclasses import dataclass

from fastapi import Header, HTTPException, Request

from backend.app.config import Settings


# ===== CLASS: Principal =====
# ID: F0767 · class · used
# ORIGINAL FILE: backend/app/auth.py:11-14
# ROLE: The authenticated caller of the gateway.
# FIELDS:
#   identity: str -> e.g. "flowise", "langgraph", "manager".
#   role: str     -> "assistant" or "manager".
# CALLED BY:
#   <- F0770 ApiKeyAuth.authenticate() (calls)
#   <- F0770 ApiKeyAuth.authenticate() (references)
#   <- F0771 ApiKeyAuth.require() (references)
#   <- F2114 register.log() (references)
#   <- F2115 register.providers() (references)
#   <- F2116 register.connections() (references)
#   <- F2117 register.create() (references)
#   <- F2118 register.get() (references)
#   <- F2119 register.patch() (references)
#   <- F2120 register.test() (references)
#   <- F2121 register.health() (references)
#   <- F2122 register.entities() (references)
# CALLS:
#   (none found)
@dataclass(frozen=True)
class Principal:
    identity: str
    role: str


# ===== CLASS: ApiKeyAuth =====
# ID: F0768 · class · used
# ORIGINAL FILE: backend/app/auth.py:17-32
# ROLE: Authenticator built from the configured key lists (Settings.managers / Settings.assistants).
# FIELDS:
#   settings: Settings.
# CALLED BY:
#   <- F0017 create_app() (calls)
# CALLS:
#   (none found)
class ApiKeyAuth:
    # ===== FUNCTION: ApiKeyAuth.__init__() =====
    # ID: F0769 · method · used (framework)
    # ORIGINAL FILE: backend/app/auth.py:18-19
    # ROLE: Keep the settings.
    # INPUTS:
    #   settings: Settings.
    # OUTPUT:
    #   None.
    # CALLED BY:
    #   (none found)
    # CALLS:
    #   -> F0001 Settings (references)
    def __init__(self, settings: Settings):
        self.settings = settings

    # ===== FUNCTION: ApiKeyAuth.authenticate() =====
    # ID: F0770 · method · used
    # ORIGINAL FILE: backend/app/auth.py:21-26
    # ROLE: Find which configured key the X-API-Key header matches; managers are checked first.
    # INPUTS:
    #   request: Request (unused, kept for the FastAPI dependency signature), x_api_key: str | None (header X-API-Key).
    # OUTPUT:
    #   Principal -> (identity, role); 401 when missing or unknown.
    # CALLED BY:
    #   <- F0019 create_app.principal() (calls)
    # CALLS:
    #   -> F0767 Principal (calls)
    #   -> F0767 Principal (references)
    def authenticate(self, request: Request, x_api_key: str | None = Header(default=None)) -> Principal:
        # Iterate over (role, {key: identity}) pairs.
        for role, keys in (("manager", self.settings.managers), ("assistant", self.settings.assistants)):
            for key, identity in keys.items():
                # .encode(): compare bytes; compare_digest takes the same time whatever the input.
                if x_api_key and hmac.compare_digest(x_api_key.encode(), key.encode()):
                    return Principal(identity, role)
        raise HTTPException(status_code=401, detail="Missing or invalid X-API-Key")

    # ===== FUNCTION: ApiKeyAuth.require() =====
    # ID: F0771 · method · used
    # ORIGINAL FILE: backend/app/auth.py:28-32
    # ROLE: Role gate: allow the principal only if its role is one of `roles`.
    # INPUTS:
    #   principal: Principal, *roles: str (variadic: require(p, "assistant", "manager")).
    # OUTPUT:
    #   Principal -> the same principal (403 otherwise).
    # CALLED BY:
    #   <- F0020 create_app.manager() (calls)
    #   <- F0021 create_app.reader() (calls)
    # CALLS:
    #   -> F0767 Principal (references)
    @staticmethod
    def require(principal: Principal, *roles: str) -> Principal:
        if principal.role not in roles:
            raise HTTPException(status_code=403, detail=f"Role {principal.role} is not allowed")
        return principal
