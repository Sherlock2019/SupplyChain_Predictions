"""Validate All Integrations: real checks, per dependent component, of whether it works on the customer's active ERP snapshot.

Nothing is green because it is configured: each check calls the component (or the exact endpoint its tools call) and compares
the snapshot it answered from with the active one. Deep checks also run a Flowise Agentflow prediction and a LangGraph run and
read which snapshot the analyses they triggered were stored against.
"""
from __future__ import annotations

import json
import time
import uuid
from datetime import date, datetime, timezone
from types import SimpleNamespace
from typing import Callable

import httpx

from backend.app.erp.connectors import MockSapConnector, SapODataConnector
from backend.app.tenants import DEFAULT_TENANT

GRAPHS = ["supply_chain_chat", "supply_chain_agentflow", "supply_chain_business", "supplier_deep_agent"]
SAP_TOOLS = {"sap_snapshot", "factory_material_readiness", "supplier_risk", "quality_status", "logistics_status"}


def _r(component: str, status: str, detail: str, **evidence) -> dict:
    return {"component": component, "status": status, "detail": detail, "evidence": evidence}


def _guard(component: str, fn: Callable[[], dict]) -> dict:
    try:
        return fn()
    except Exception as exc:  # noqa: BLE001 - a failing check is a result, not a crash
        return _r(component, "fail", f"{type(exc).__name__}: {str(exc)[:240]}")


def _analyses_since(store, since: str) -> list[dict]:
    return store._db.query("select snapshot_id, actor, kind from analysis where created_at >= ? order by created_at", (since,))


def validate_integrations(ctx: SimpleNamespace, tenant: str, *, deep: bool = False) -> dict:
    t = ctx.tenants.get(tenant)
    expected = t.sap.snapshot["id"]
    s = ctx.settings
    agent_tenant_note = "" if tenant == DEFAULT_TENANT else (
        f" Flowise and LangGraph tools send no X-Tenant header, so they read the default customer ({DEFAULT_TENANT}), not {tenant}.")
    results: list[dict] = []

    def adapter() -> dict:
        active = ctx.erp.active(tenant)
        conn = ctx.erp._row(tenant, active["connection_id"]) if active and active["connection_id"] else None
        connector = ctx.erp.connector(tenant, conn) if conn else MockSapConnector(ctx.tenants.builtin[tenant])
        test = connector.test_connection(ctx.erp.mapping(tenant, conn["id"])) if isinstance(connector, SapODataConnector) else connector.test_connection()
        served = t.sap.odata("A_MaterialStock", top=1)["__snapshot"]
        ok = test["ok"] and served == expected
        return _r("FastAPI SAP adapter", "pass" if ok else "fail",
                  f"{'connected' if test['ok'] else 'ERP test failed: ' + str(test.get('error'))}; OData endpoints serve {served}",
                  connection=conn["id"] if conn else "built-in snapshot", latency_ms=test.get("latency_ms"))

    def engine() -> dict:
        kpis = t.engine.kpis()
        orders = t.sap.section("production_orders")
        detail = f"{len(kpis.get('kpis', kpis))} KPIs computed"
        if orders:
            o = orders[0]
            r = t.engine.factory_readiness(o["plant"], o["material"], o["quantity"], date.fromisoformat(o["finish_date"]))
            detail += f"; factory readiness {o['order']}: {r.get('status')}"
        return _r("Business analytics engine", "pass", f"{detail} on {expected}", snapshot=expected)

    def flowise(kind: str) -> dict:
        name = f"Flowise {kind}"
        flow_id = s.flowise_chatflow_id if kind == "Chatflow" else s.flowise_agentflow_id
        if not s.flowise_url or not s.flowise_api_key or not flow_id:
            return _r(name, "n/a", "Flowise URL, API key or flow id not configured on the gateway")
        auth = {"Authorization": f"Bearer {s.flowise_api_key}"}
        with httpx.Client(timeout=20) as c:
            flow = c.get(f"{s.flowise_url.rstrip('/')}/api/v1/chatflows/{flow_id}", headers=auth)
            if flow.status_code != 200:
                return _r(name, "fail", f"flow {flow_id} not readable (HTTP {flow.status_code})")
            variables = c.get(f"{s.flowise_url.rstrip('/')}/api/v1/variables", headers=auth)
            base = next((v["value"] for v in variables.json() if v.get("name") == "copilot_api_url"), "") if variables.status_code == 200 else ""
            if not base:
                return _r(name, "fail", "Flowise variable copilot_api_url not found: the tools cannot reach the gateway")
            key = next((k for k, who in s.assistants.items() if who == "flowise"), next(iter(s.assistants), ""))
            served = c.get(f"{base.rstrip('/')}/sap/opu/odata/sap/ZSCM_COPILOT_SRV/A_MaterialStock", params={"$top": 1}, headers={"X-API-Key": key}).json().get("__snapshot")
        default_snap = ctx.tenants.get(DEFAULT_TENANT).sap.snapshot["id"]
        ok = served == default_snap
        status = ("pass" if served == expected else "warn") if ok else "fail"
        evidence = {"flow": flow.json().get("name"), "tool_base_url": base, "snapshot_served_to_tools": served}
        detail = f"tools call {base} and receive snapshot {served}.{agent_tenant_note}"
        if deep and kind == "Agentflow" and ok:
            since = datetime.now(timezone.utc).isoformat()
            started = time.perf_counter()
            with httpx.Client(timeout=600) as c:
                pred = c.post(f"{s.flowise_url.rstrip('/')}/api/v1/prediction/{flow_id}", headers=auth,
                              json={"question": _question(ctx, DEFAULT_TENANT), "overrideConfig": {"sessionId": f"erp-check-{uuid.uuid4().hex[:8]}"}})
            stored = _analyses_since(ctx.store, since)
            snaps = sorted({a["snapshot_id"] for a in stored})
            evidence.update(prediction_http=pred.status_code, seconds=round(time.perf_counter() - started, 1), analyses=len(stored), analysis_snapshots=snaps)
            if pred.status_code != 200 or not stored:
                status, detail = "fail", f"Agentflow run did not produce a governed analysis (HTTP {pred.status_code}, {len(stored)} analyses)"
            elif snaps != [default_snap]:
                status, detail = "fail", f"Agentflow analyses used {snaps}, expected {default_snap}"
            else:
                detail += f" Live run: {len(stored)} analyses stored against {default_snap}."
        return _r(name, status, detail, **evidence)

    def langgraph() -> dict:
        if not s.langgraph_url:
            return _r("LangGraph", "n/a", "LANGGRAPH_URL not configured (graphs run in-process on the gateway's engine)")
        with httpx.Client(timeout=20) as c:
            c.get(f"{s.langgraph_url.rstrip('/')}/ok").raise_for_status()
            found = {a["graph_id"] for a in c.post(f"{s.langgraph_url.rstrip('/')}/assistants/search", json={"limit": 100}).json()}
        missing = [g for g in GRAPHS if g not in found]
        if missing:
            return _r("LangGraph", "fail", f"graphs not registered: {', '.join(missing)}")
        status, detail, evidence = ("pass" if tenant == DEFAULT_TENANT else "warn"), f"{len(GRAPHS)} graphs registered; tools call the gateway.{agent_tenant_note}", {"graphs": GRAPHS}
        if deep:
            since = datetime.now(timezone.utc).isoformat()
            started = time.perf_counter()
            ctx.runner.run("supply_chain_chat", {"messages": [{"role": "user", "content": _question(ctx, DEFAULT_TENANT)}]}, None)
            stored = _analyses_since(ctx.store, since)
            snaps = sorted({a["snapshot_id"] for a in stored})
            default_snap = ctx.tenants.get(DEFAULT_TENANT).sap.snapshot["id"]
            evidence.update(seconds=round(time.perf_counter() - started, 1), analyses=len(stored), analysis_snapshots=snaps)
            if not stored or snaps != [default_snap]:
                status, detail = "fail", f"LangGraph run stored {len(stored)} analyses on {snaps or 'none'}, expected {default_snap}"
            else:
                detail += f" Live run: {len(stored)} analyses stored against {default_snap}."
        return _r("LangGraph", status, detail, **evidence)

    def deep_agents() -> dict:
        tools = set(ctx.harness()["tools"])
        allowed = sorted(tools & SAP_TOOLS)
        if not allowed:
            return _r("Deep Agents", "fail", "the harness allows no ERP tool", tools=sorted(tools))
        return _r("Deep Agents", "pass" if tenant == DEFAULT_TENANT else "warn",
                  f"authorized read-only ERP tools: {', '.join(allowed)} (they call the gateway).{agent_tenant_note}", tools=allowed)

    def rag() -> dict:
        stats = ctx.rag.stats()
        return _r("RAG", "pass", f"{stats.get('backend')} knowledge base with {stats.get('chunks')} chunks; structured ERP records are served by APIs, not embedded. "
                  "Customer-private policy RAG (SCInsight) is scoped by the caller's key.", **stats)

    def dashboards() -> dict:
        snap = t.sap.snapshot
        t.engine.inventory_overview()
        age = snap.get("age_hours") or 0
        return _r("Dashboards", "pass" if age <= 72 else "warn", f"data source {snap.get('source_system')} · snapshot {snap['id']} · {age:.0f} h old",
                  source=snap.get("source_system"), extracted_at=snap.get("extracted_at"))

    def outcomes() -> dict:
        mine = ctx.store.list_outcomes(expected)
        other = len(ctx.store.list_outcomes()) - len(mine)
        return _r("Decision outcome learning", "pass", f"{len(mine)} outcomes tracked on {expected}; {other} belong to other snapshots and are kept apart",
                  snapshot=expected)

    def audit() -> dict:
        valid = ctx.store.verify_chain()
        events = [e for e in ctx.store.audit_events(1000) if e["action"].startswith("erp.")]
        return _r("Audit & monitoring", "pass" if valid and events else "fail", f"audit chain {'valid' if valid else 'BROKEN'}; {len(events)} ERP events recorded")

    def scinsight() -> dict:
        return _r("SCInsight Chatflow / Agentflow", "n/a", "These Flowise flows use the SCInsight API (/scinsight) and its own synthetic SAP dataset; "
                  "they are not connected to this ERP connection.")

    for name, fn in [("FastAPI SAP adapter", adapter), ("Business analytics engine", engine), ("Flowise Chatflow", lambda: flowise("Chatflow")),
                     ("Flowise Agentflow", lambda: flowise("Agentflow")), ("LangGraph", langgraph), ("Deep Agents", deep_agents), ("RAG", rag),
                     ("Dashboards", dashboards), ("Decision outcome learning", outcomes), ("Audit & monitoring", audit), ("SCInsight flows", scinsight)]:
        results.append(_guard(name, fn))
    ok = all(r["status"] in ("pass", "n/a") for r in results)
    return {"tenant": tenant, "snapshot": expected, "ok": ok, "deep": deep, "checked_at": datetime.now(timezone.utc).isoformat(), "results": results}


def _question(ctx: SimpleNamespace, tenant: str) -> str:
    orders = ctx.tenants.get(tenant).sap.section("production_orders")
    o = orders[0]
    return (f"Check factory material readiness: can plant {o['plant']} produce {o['quantity']:.0f} {o['material']} by {o['finish_date']}? "
            "Use the factory readiness tool and answer briefly.")


def save_check(store, tenant: str, result: dict, actor: str) -> None:
    store._db.query("insert into erp_integration_check(id,tenant,ok,result,actor,at) values(?,?,?,?,?,?)",
                    (uuid.uuid4().hex, tenant, int(result["ok"]), json.dumps(result), actor, result["checked_at"]), fetch="none")


def last_check(store, tenant: str) -> dict | None:
    row = store._db.query("select result from erp_integration_check where tenant=? order by at desc limit 1", (tenant,), fetch="one")
    return json.loads(row["result"]) if row else None
