from __future__ import annotations

import hmac
from dataclasses import dataclass

from fastapi import Header, HTTPException, Request

from backend.app.config import Settings


@dataclass(frozen=True)
class Principal:
    identity: str
    role: str


class ApiKeyAuth:
    def __init__(self, settings: Settings):
        self.settings = settings

    def authenticate(self, request: Request, x_api_key: str | None = Header(default=None)) -> Principal:
        for role, keys in (("manager", self.settings.managers), ("assistant", self.settings.assistants)):
            for key, identity in keys.items():
                if x_api_key and hmac.compare_digest(x_api_key.encode(), key.encode()):
                    return Principal(identity, role)
        raise HTTPException(status_code=401, detail="Missing or invalid X-API-Key")

    @staticmethod
    def require(principal: Principal, *roles: str) -> Principal:
        if principal.role not in roles:
            raise HTTPException(status_code=403, detail=f"Role {principal.role} is not allowed")
        return principal

