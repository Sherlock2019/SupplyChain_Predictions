"""ERP connectors behind one interface: the existing mock SAP snapshot, and SAP S/4HANA / ECC OData (V2 and V4).

Read-only: connectors only send GET to the ERP (the OAuth token request is the only POST, to the token URL). Secrets are passed in
by the service and never returned; errors are sanitized before they leave this module.
"""
from __future__ import annotations

import ipaddress
import json
import re
import time
from abc import ABC, abstractmethod
from copy import deepcopy
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import httpx

from backend.app.erp.mapping import REFERENCES, SECTIONS, SectionMapping, transform, validate_mapping
from backend.app.sap import ODATA_ENTITIES, SapRepository

PROVIDERS = {
    "mock_sap": {"label": "Mock SAP (customer snapshot)", "protocols": ["snapshot"], "modes": ["mock"], "available": True},
    "sap_s4hana": {"label": "SAP S/4HANA (Cloud or on-premise)", "protocols": ["odata_v2", "odata_v4"], "modes": ["read_only_live"], "available": True},
    "sap_ecc": {"label": "SAP ECC 6.0 with SAP Gateway", "protocols": ["odata_v2"], "modes": ["read_only_live"], "available": True},
    "generic_rest": {"label": "Generic REST ERP", "protocols": ["rest"], "modes": [], "available": False,
                     "reason": "No generic REST connector is implemented yet; add one in backend/app/erp/connectors.py"},
}
MODES = {
    "mock": {"label": "Mock", "available": True, "description": "Existing SAP snapshot and simulated sandbox transactions"},
    "read_only_live": {"label": "Read-only Live", "available": True, "description": "Reads real ERP data; ERP writes are refused"},
    "approved_write": {"label": "Approved Write", "available": False,
                       "description": "Not available in this build: no live SAP write connector exists. Accepted recommendations execute in the SAP sandbox outbox."},
}
BLOCKED_HOSTS = {"metadata.google.internal", "metadata", "169.254.169.254", "fd00:ec2::254"}


class ErpError(ValueError):
    """Safe-to-show error (no secrets, no stack)."""


def sanitize(text: str, *secrets: str) -> str:
    for s in secrets:
        if s:
            text = text.replace(s, "***")
    return re.sub(r"(?i)(authorization|apikey|password|secret|token)([\"'=: ]+)[^\s,\"']+", r"\1\2***", text)[:300]


def check_destination(url: str, *, environment: str, allowed_hosts: set[str], allow_http: bool) -> None:
    """SSRF guard: scheme, cloud-metadata and link-local addresses, production allow-list and HTTPS."""
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower()
    if parsed.scheme not in ("https", "http") or not host or parsed.username or parsed.password:
        raise ErpError("URL must be https://host[:port][/path] without credentials")
    if host in BLOCKED_HOSTS:
        raise ErpError(f"Destination {host} is not allowed")
    try:
        ip = ipaddress.ip_address(host)
        if ip.is_link_local or ip.is_multicast or ip.is_unspecified:
            raise ErpError(f"Destination {host} is not allowed")
    except ValueError as exc:
        if isinstance(exc, ErpError):
            raise
    if environment == "production":
        if parsed.scheme != "https":
            raise ErpError("Production connections must use https://")
        if host not in allowed_hosts:
            raise ErpError(f"{host} is not in ERP_ALLOWED_HOSTS (required for production connections)")
    elif parsed.scheme == "http" and not allow_http:
        raise ErpError("Use https:// (http:// is only allowed when APP_ENV is development or test)")
    elif allowed_hosts and host not in allowed_hosts:
        raise ErpError(f"{host} is not in ERP_ALLOWED_HOSTS")


class ErpConnector(ABC):
    provider = ""

    @abstractmethod
    def get_capabilities(self) -> dict: ...

    @abstractmethod
    def test_connection(self) -> dict: ...

    @abstractmethod
    def discover_entities(self, mapping: dict[str, SectionMapping]) -> list[dict]: ...

    @abstractmethod
    def read_entity(self, section: str, mapping: dict[str, SectionMapping], top: int) -> dict: ...

    @abstractmethod
    def validate_mapping(self, mapping: dict[str, SectionMapping]) -> list[str]: ...

    @abstractmethod
    def sync_data(self, base: dict, mapping: dict[str, SectionMapping]) -> dict: ...

    def get_health(self) -> dict:
        result = self.test_connection()
        return {"status": "connected" if result["ok"] else "error", "latency_ms": result.get("latency_ms"), "error": result.get("error")}


class MockSapConnector(ErpConnector):
    """The customer's existing validated SAP snapshot (data/…json): what SPARC used before any ERP connection."""
    provider = "mock_sap"

    def __init__(self, path: Path):
        self.path = Path(path)

    def get_capabilities(self) -> dict:
        return {"read": True, "write": "sandbox outbox only", "incremental_sync": False, "discovery": True, "protocol": "snapshot"}

    def test_connection(self) -> dict:
        started = time.perf_counter()
        try:
            repo = SapRepository(self.path)
        except (OSError, ValueError, KeyError) as exc:
            return {"ok": False, "error": sanitize(str(exc)), "latency_ms": round((time.perf_counter() - started) * 1000)}
        return {"ok": True, "system": {"id": repo.snapshot["source_system"], "snapshot": repo.snapshot["id"]}, "auth": "not required",
                "latency_ms": round((time.perf_counter() - started) * 1000), "checks": [{"entity": e["name"], "status": "up", "detail": f"{e['rows']} rows"} for e in repo.metadata()["entity_sets"]]}

    def discover_entities(self, mapping: dict[str, SectionMapping]) -> list[dict]:
        repo = SapRepository(self.path)
        inverse = {v: k for k, v in ODATA_ENTITIES.items()}
        return [{"section": s, "label": SECTIONS[s]["label"], "entity_set": inverse.get(s, s), "available": repo.has(s), "rows": len(repo.section(s)) if repo.has(s) else 0}
                for s in SECTIONS]

    def read_entity(self, section: str, mapping: dict[str, SectionMapping], top: int) -> dict:
        repo = SapRepository(self.path)
        if not repo.has(section):
            raise ErpError(f"{section} is not in this snapshot")
        rows = repo.section(section)[:top]
        return {"section": section, "source": f"snapshot {repo.snapshot['id']}", "rows": rows, "raw": rows, "errors": []}

    def validate_mapping(self, mapping: dict[str, SectionMapping]) -> list[str]:
        return []  # the snapshot is already in SPARC's shape

    def sync_data(self, base: dict, mapping: dict[str, SectionMapping]) -> dict:
        data = json.loads(self.path.read_text(encoding="utf-8"))
        counts = {s: len(data[s]) for s in SECTIONS if isinstance(data.get(s), list)}
        return {"snapshot": data, "counts": counts, "errors": [], "warnings": [], "carried": []}


class SapODataConnector(ErpConnector):
    """SAP S/4HANA or ECC (SAP Gateway) through OData. Only GET reaches SAP; pages with $top/$skip; bounded retries."""

    def __init__(self, provider: str, config: dict, secret: str, *, transport: httpx.BaseTransport | None = None):
        self.provider, self.config, self.secret, self.transport = provider, config, secret, transport
        self._token: str | None = None

    # ------------------------------------------------------------ HTTP
    def _auth(self) -> tuple[dict, Any]:
        method = self.config.get("auth", "basic")
        if method == "basic":
            return {}, httpx.BasicAuth(self.config.get("username", ""), self.secret)
        if method == "api_key":
            return {"APIKey": self.secret}, None
        if self._token is None:
            if not self.config.get("token_url") or not self.config.get("client_id"):
                raise ErpError("OAuth needs a token URL and a client ID")
            with httpx.Client(timeout=self.config.get("timeout_seconds", 15), verify=self.config.get("verify_tls", True), follow_redirects=False,
                              transport=self.transport) as client:
                response = client.post(self.config["token_url"], data={"grant_type": "client_credentials"}, auth=(self.config["client_id"], self.secret))
            if response.status_code != 200 or "access_token" not in response.text:
                raise ErpError(f"OAuth token request failed: HTTP {response.status_code}")
            self._token = response.json()["access_token"]
        return {"Authorization": f"Bearer {self._token}"}, None

    def _get(self, path: str, params: dict | None = None) -> httpx.Response:
        headers, auth = self._auth()
        params = {**({"sap-client": self.config["sap_client"]} if self.config.get("sap_client") else {}), **(params or {})}
        last: Exception | None = None
        for attempt in range(2):  # one retry on network errors and 5xx
            try:
                with httpx.Client(base_url=self.config["base_url"], headers={"Accept": "application/json", **headers}, auth=auth,
                                  timeout=self.config.get("timeout_seconds", 15), verify=self.config.get("verify_tls", True),
                                  follow_redirects=False, transport=self.transport) as client:
                    response = client.get(path, params=params)
                if response.status_code < 500 or attempt == 1:
                    return response
            except httpx.HTTPError as exc:
                last = exc
            time.sleep(0.5)
        raise ErpError(sanitize(f"ERP not reachable: {type(last).__name__}: {last}", self.secret))

    def _metadata(self, service: str) -> dict[str, set[str]]:
        response = self._get(f"{service}/$metadata")
        if response.status_code != 200:
            raise ErpError(f"{service}/$metadata: {http_hint(response.status_code)}")
        return parse_metadata(response.text)

    def _services(self, mapping: dict[str, SectionMapping]) -> list[str]:
        return sorted({m.service for m in mapping.values() if m.enabled and m.service})

    # ------------------------------------------------------------ interface
    def get_capabilities(self) -> dict:
        return {"read": True, "write": False, "incremental_sync": False, "discovery": True, "protocol": self.config.get("protocol", "odata_v2")}

    def test_connection(self, mapping: dict[str, SectionMapping] | None = None) -> dict:
        """Authorized GET of $metadata for every service the mapping uses (or the first one): proves network, TLS, credentials
        and API authorization. Never activates anything."""
        started = time.perf_counter()
        services = self._services(mapping or {}) or ["/sap/opu/odata/sap/API_PRODUCT_SRV"]
        checks = []
        try:
            for service in services:
                t = time.perf_counter()
                response = self._get(f"{service}/$metadata")
                ok = response.status_code == 200 and "EntitySet" in response.text
                checks.append({"entity": service, "status": "up" if ok else "error", "http": response.status_code,
                               "detail": "metadata read" if ok else http_hint(response.status_code), "ms": round((time.perf_counter() - t) * 1000)})
        except ErpError as exc:
            return {"ok": False, "error": sanitize(str(exc), self.secret), "checks": checks, "auth": "unknown",
                    "latency_ms": round((time.perf_counter() - started) * 1000)}
        ok = bool(checks) and all(c["status"] == "up" for c in checks)
        auth = "rejected" if any(c["http"] in (401, 403) for c in checks) else "ok" if ok else "unknown"
        return {"ok": ok, "checks": checks, "auth": auth, "system": {"id": self.config.get("base_url"), "client": self.config.get("sap_client") or None},
                "error": None if ok else next(c["detail"] for c in checks if c["status"] != "up"), "latency_ms": round((time.perf_counter() - started) * 1000)}

    def discover_entities(self, mapping: dict[str, SectionMapping]) -> list[dict]:
        found = []
        for service in self._services(mapping):
            try:
                sets = self._metadata(service)
                found.append({"service": service, "entity_sets": sorted(sets), "error": None})
            except ErpError as exc:
                found.append({"service": service, "entity_sets": [], "error": str(exc)})
        return found

    def validate_mapping(self, mapping: dict[str, SectionMapping]) -> list[str]:
        metadata: dict[str, set[str]] = {}
        problems = []
        for service in self._services(mapping):
            try:
                metadata.update(self._metadata(service))
            except ErpError as exc:
                problems.append(str(exc))
        return problems + validate_mapping(mapping, metadata)

    def _rows(self, m: SectionMapping, top: int, skip: int = 0) -> list[dict]:
        params: dict[str, Any] = {"$top": top, "$skip": skip, "$format": "json"}
        if m.expand:
            params["$expand"] = m.expand
        if m.filter:
            params["$filter"] = m.filter
        response = self._get(f"{m.service}/{m.entity_set}", params)
        if response.status_code != 200:
            raise ErpError(f"{m.entity_set}: {http_hint(response.status_code)}")
        data = response.json()
        return data["d"].get("results", []) if isinstance(data.get("d"), dict) else data.get("value", [])

    def read_entity(self, section: str, mapping: dict[str, SectionMapping], top: int) -> dict:
        m = mapping.get(section)
        if m is None or not m.service or not m.entity_set:
            raise ErpError(f"{section} has no SAP entity mapped")
        raw = self._rows(m, top)
        rows, errors = transform(section, raw, m.fields)
        flat = [{k: v for k, v in r.items() if not k.startswith("__") and not isinstance(v, (dict, list))} for r in raw]
        return {"section": section, "source": f"{m.service}/{m.entity_set}", "rows": rows, "raw": flat, "errors": errors[:20]}

    def sync_data(self, base: dict, mapping: dict[str, SectionMapping], *, page: int = 500, max_rows: int = 20000) -> dict:
        """Full read of every enabled section into a copy of the current snapshot. Sections not enabled are carried over."""
        data = deepcopy(base)
        counts, errors, warnings, carried = {}, [], [], []
        for section in SECTIONS:
            m = mapping.get(section)
            if m is None or not m.enabled:
                carried.append(section)
                continue
            raw: list[dict] = []
            while len(raw) < max_rows:
                batch = self._rows(m, page, len(raw))
                raw += batch
                if len(batch) < page:
                    break
            rows, errs = transform(section, raw, m.fields)
            errors += errs
            data[section] = rows
            counts[section] = len(rows)
        # SAP transactional data carries supplier numbers; SPARC's transactional rows name the supplier
        names = {s["code"]: s["name"] for s in data.get("suppliers", []) if s.get("code")}
        for section in ("purchase_orders", "po_history", "quality_lots"):
            for row in data.get(section, []) if section not in carried else []:
                row["supplier"] = names.get(row.get("supplier"), row.get("supplier"))
        # keep transactional rows inside SPARC's master data; report what was dropped
        plants = {p["code"] for p in data.get("plants", [])}
        materials = {p["code"] for p in data.get("materials", [])}
        for section, refs in REFERENCES.items():
            if section in carried or section not in data:
                continue
            keep = [r for r in data[section] if all(r.get(f) in (plants if f == "plant" else materials) for f in refs)]
            if len(keep) < len(data[section]):
                warnings.append(f"{SECTIONS[section]['label']}: {len(data[section]) - len(keep)} rows reference plants/materials outside SPARC's master data and were left out")
                data[section] = keep
                counts[section] = len(keep)
        return {"snapshot": data, "counts": counts, "errors": errors[:200], "warnings": warnings, "carried": carried}


def parse_metadata(xml: str) -> dict[str, set[str]]:
    """{entity set: property and navigation-property names} from an OData V2/V4 $metadata document."""
    types: dict[str, set[str]] = {}
    for m in re.finditer(r"<EntityType\b[^>]*\bName=\"([^\"]+)\"(.*?)</EntityType>", xml, re.S):
        types[m.group(1)] = set(re.findall(r"<(?:Property|NavigationProperty)\b[^>]*\bName=\"([^\"]+)\"", m.group(2)))
    sets = {}
    for m in re.finditer(r"<EntitySet\b[^>]*\bName=\"([^\"]+)\"[^>]*\bEntityType=\"([^\"]+)\"", xml):
        sets[m.group(1)] = types.get(m.group(2).split(".")[-1], set())
    return sets


def http_hint(code: int) -> str:
    return {401: "HTTP 401: credentials rejected", 403: "HTTP 403: user not authorized for this API (communication arrangement / role)",
            404: "HTTP 404: service not found or not activated (/IWFND/MAINT_SERVICE)", 503: "HTTP 503: SAP system unavailable"}.get(code, f"HTTP {code}")
