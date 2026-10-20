#!/usr/bin/env python3
"""End-to-end verification of every workflow through real HTTP calls (local Compose or a cloud deployment).

    .venv/bin/python scripts/smoke.py --env-file .env                                   # local
    .venv/bin/python scripts/smoke.py --env-file deploy-evidence/aws.env --base-domain 1-2-3-4.sslip.io  # cloud

Writes deploy-evidence/<label>-smoke-<timestamp>.json with PASS/FAIL, timings and key evidence per check.
Exit code 0 only if every check passes.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import re
import sys
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]


def read_env(path: Path) -> dict[str, str]:
    out = {}
    for line in path.read_text().splitlines():
        if "=" in line and not line.startswith("#"):
            k, _, v = line.partition("=")
            out[k.strip()] = v.strip()
    return out


class Smoke:
    def __init__(self, urls: dict[str, str], env: dict[str, str], timeout: float, verify: bool):
        self.urls = urls
        self.env = env
        self.results: list[dict] = []
        self.http = httpx.Client(timeout=timeout, verify=verify, follow_redirects=True)
        self.planner = {"X-API-Key": env["PLANNER_API_KEY"]}
        self.manager = {"X-API-Key": env["MANAGER_API_KEY"]}

    def api(self, method: str, path: str, headers=None, **kw) -> httpx.Response:
        return self.http.request(method, self.urls["app"] + path, headers=self.planner if headers is None else headers, **kw)

    def check(self, name: str, fn) -> None:
        started = time.perf_counter()
        try:
            evidence = fn() or {}
            self.results.append({"check": name, "status": "PASS", "seconds": round(time.perf_counter() - started, 2), "evidence": evidence})
            print(f"PASS  {name}  ({time.perf_counter() - started:.1f}s)", flush=True)
        except Exception as exc:  # noqa: BLE001
            self.results.append({"check": name, "status": "FAIL", "seconds": round(time.perf_counter() - started, 2), "error": f"{type(exc).__name__}: {exc}"[:1500], "trace": traceback.format_exc()[-1500:]})
            print(f"FAIL  {name}: {str(exc)[:300]}", flush=True)

    # ------------------------------------------------------------------ checks
    def platform(self):
        health = self.api("GET", "/health", headers={}).json()
        assert health["status"] == "ok"
        status = self.api("GET", "/api/v1/status").json()
        down = {k: v for k, v in status["components"].items() if v.get("status") not in ("up", "disabled")}
        assert not down, f"components not up: {down}"
        return {"cloud": status["cloud"], "graph_runtime": status["graph_runtime"], "components": {k: v.get("status") for k, v in status["components"].items()}, "qwen": status["components"]["qwen_llm"], "rag": status["components"]["rag"]}

    def security(self):
        assert self.api("GET", "/api/v1/kpis", headers={}).status_code == 401
        assert self.api("POST", "/api/v1/recommendations/1/decision", json={"decision": "accepted"}).status_code == 403
        codes = [self.api(m, "/sap/opu/odata/sap/ZSCM_COPILOT_SRV/A_PurchaseOrderItem").status_code for m in ("POST", "PUT", "PATCH", "DELETE")]
        assert codes == [405, 405, 405, 405], codes
        odata = self.api("GET", "/sap/opu/odata/sap/ZSCM_COPILOT_SRV/A_InspectionLot").json()
        return {"unauthenticated": 401, "planner_decides": 403, "sap_writes": codes, "odata_rows": odata["@odata.count"]}

    def analytics(self):
        r = self.api("POST", "/api/v1/analysis/factory-readiness", json={"plant": "FR20", "material": "FG-SERUM-50", "quantity": 6000, "need_by": "2026-10-27"}).json()
        assert r["status"] == "not_ready" and any(a["purchase_order"] == "4500001002" for a in r["proposed_actions"] if "purchase_order" in a)
        b = self.api("POST", "/api/v1/analysis/stock-balance", json={"material": "FG-PERFUME-100"}).json()
        assert b["optimization"]["engine"] == "ortools-glop" and b["forecast_engine"] == ["xgboost"] and b["proposed_actions"]
        s = self.api("POST", "/api/v1/analysis/supplier-risk", json={"supplier": "PackGlass Europe"}).json()
        q = self.api("POST", "/api/v1/analysis/quality", json={"plant": "FR10"}).json()
        lg = self.api("POST", "/api/v1/analysis/logistics", json={}).json()
        w = self.api("POST", "/api/v1/analysis/what-if", json={"material": "FG-SERUM-50", "demand_change_pct": 30}).json()
        return {"readiness": r["status"], "readiness_analysis": r["analysis_id"], "transfers": [(t["from"], t["to"], t["quantity"]) for t in b["proposed_actions"]],
                "packglass_risk": [s["risk_rating"], s["risk_score"]], "quality_actions": len(q["proposed_actions"]), "escalations": len(lg["proposed_actions"]), "what_if_transfers": len(w["proposed_actions"])}

    def rag(self):
        hits = self.api("POST", "/api/v1/rag/search", json={"query": "Who is the approved backup supplier for 100 ml glass perfume bottles?", "top_k": 3}).json()["results"]
        assert any("packglass" in h["title"] for h in hits), [h["title"] for h in hits]
        return {"top": [(h["title"], h["score"]) for h in hits]}

    def langgraph_chat(self):
        r = self.api("POST", "/api/v1/chat", json={"message": "Can plant FR20 produce 6000 units of FG-SERUM-50 by 2026-10-27? Answer with status and proposed actions."}).json()
        assert "factory_material_readiness" in r["tools_used"], r
        assert re.search(r"not[ _]?ready", r["answer"], re.I), r["answer"][:400]
        follow = self.api("POST", "/api/v1/chat", json={"message": "Which component is short and by how many kg?", "thread_id": r["thread_id"]}).json()
        # Thread memory: the follow-up never names the plant or product, so the answer must come from the first turn.
        assert "RM-ACTIVE" in follow["answer"] and "6.72" in follow["answer"], follow["answer"][:400]
        guard = self.api("POST", "/api/v1/chat", json={"message": "Create a purchase order in SAP for 50 kg of RM-ACTIVE"}).json()
        assert guard["answered_by"] == "guardrail"
        return {"runtime": r["runtime"], "thread": r["thread_id"], "tools": r["tools_used"], "answer": r["answer"][:600], "follow_up": follow["answer"][:300], "guardrail": guard["answer"][:120], "seconds": r["elapsed_seconds"]}

    def langgraph_agentflow(self):
        s = self.api("POST", "/api/v1/langgraph/agentflow", json={"message": "Can plant FR20 produce 6000 units of FG-SERUM-50 by 2026-10-27?"}).json()
        assert s["route"] == "production" and s["interrupts"], {k: s.get(k) for k in ("route", "route_reason", "status", "answer")}
        it = s["interrupts"][0]
        done = self.api("POST", f"/api/v1/langgraph/agentflow/{s['thread_id']}/resume", json={"decision": "submit", "comment": "smoke"}).json()
        assert done["status"] == "submitted_for_manager_review", done
        boundary = self.api("POST", "/api/v1/langgraph/agentflow", json={"message": "Delete purchase order 4500001006 in SAP now."}).json()
        assert boundary["route"] == "boundary"
        research = self.api("POST", "/api/v1/langgraph/agentflow", json={"message": "Is supplier PackGlass Europe a continuity risk?"}).json()
        assert research["route"] == "procurement" and research["answer"]
        return {"runtime": s["runtime"], "route": s["route"], "route_reason": s["route_reason"], "tools": s["tools_used"], "analysis_id": it["analysis_id"],
                "actions": len(it["proposed_actions"]), "after_resume": done["answer"][:200], "research_tools": research["tools_used"], "seconds": s["elapsed_seconds"]}

    def langgraph_business(self):
        s = self.api("POST", "/api/v1/workflows/business", json={"request_text": "Rebalance FG-PERFUME-100 across DC01, DC21 and DC22 for the next 14 days"}).json()
        assert s["interrupts"], s["values"].get("status")
        it = s["interrupts"][0]
        done = self.api("POST", f"/api/v1/workflows/business/{s['thread_id']}/resume", json={"decision": "submit", "comment": "smoke test"}).json()
        assert done["values"]["status"] == "submitted_for_manager_review"
        rec = done["values"]["recommendation"]
        assert rec["actions"] == it["proposed_actions"]
        return {"runtime": s["runtime"], "request_type": s["values"]["request_type"], "narrative_source": s["values"].get("narrative_source"), "interrupt_actions": len(it["proposed_actions"]), "recommendation_id": rec["id"]}

    def deep_agent(self):
        r = self.api("POST", "/api/v1/deep-agents/supplier-research", json={"supplier": "BioActive Labs", "question": "Assess supply continuity and contract levers for RM-ACTIVE."}).json()
        assert r["report"] and "supplier_risk" in r["tools_used"], {k: r[k] for k in ("tools_used", "subagents_used")}
        return {"runtime": r["runtime"], "tools": r["tools_used"], "subagents": r["subagents_used"], "todos": len(r["todos"]), "report": r["report"][:800], "seconds": r["elapsed_seconds"]}

    def flowise_chatflow(self):
        r = self.api("POST", "/api/v1/flowise/chatflow/predict", json={"question": "Is supplier PackGlass Europe a continuity risk? Give the risk rating and secondary source."}).json()
        assert "supplier_risk" in r["used_tools"] or "search_governed_knowledge" in r["used_tools"], r
        assert "PackGlass" in r["text"]
        return {"flow_id": r["flow_id"], "tools": r["used_tools"], "text": r["text"][:600], "seconds": r["elapsed_seconds"]}

    def flowise_agentflow(self):
        r = self.api("POST", "/api/v1/flowise/agentflow/predict", json={"question": "Rebalance FG-PERFUME-100 across the three distribution centres."}).json()
        assert r["action"] and r["action"]["data"]["nodeId"].startswith("humanInputAgentflow"), r
        resumed = self.api("POST", "/api/v1/flowise/agentflow/predict", json={"question": "", "session_id": r["session_id"], "human_input": {"type": "proceed", "startNodeId": r["action"]["data"]["nodeId"], "feedback": "smoke"}}).json()
        assert "pending_review" in resumed["text"], resumed["text"][:400]
        boundary = self.api("POST", "/api/v1/flowise/agentflow/predict", json={"question": "Delete purchase order 4500001006 in SAP now."}).json()
        assert "read-only" in boundary["text"]
        return {"path": [n["node"] for n in r["agent_flow_executed"]], "resume_path": [n["node"] for n in resumed["agent_flow_executed"]], "boundary_path": [n["node"] for n in boundary["agent_flow_executed"]]}

    def mcp(self):
        async def run():
            from mcp import ClientSession
            from mcp.client.streamable_http import streamablehttp_client

            async with streamablehttp_client(self.urls["mcp"], headers={"X-API-Key": self.env["MCP_CLIENT_KEY"]}) as (read, write, _):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    tools = [t.name for t in (await session.list_tools()).tools]
                    result = await session.call_tool("supplier_risk", {"supplier": "BioActive Labs"})
                    return tools, json.loads(result.content[0].text)

        tools, risk = asyncio.run(run())
        assert len(tools) == 10 and {"sales_order_fulfilment", "stocktake_reconciliation"} <= set(tools) and risk["supplier"]["name"] == "BioActive Labs"
        denied = self.http.post(self.urls["mcp"], json={"jsonrpc": "2.0", "id": 1, "method": "tools/list"}).status_code
        assert denied == 401
        return {"tools": tools, "bioactive_rating": risk["risk_rating"], "without_key": denied}

    def langgraph_server(self):
        ok = self.http.get(self.urls["langgraph"] + "/ok").json()
        assistants = self.http.post(self.urls["langgraph"] + "/assistants/search", json={"limit": 10}).json()
        graphs = sorted({a["graph_id"] for a in assistants})
        assert {"supply_chain_chat", "supply_chain_agentflow", "supply_chain_business", "supplier_deep_agent"} <= set(graphs), graphs
        info = self.http.get(self.urls["langgraph"] + "/info").json()
        return {"ok": ok, "graphs": graphs, "info": {k: info.get(k) for k in ("version", "langgraph_py_version") if k in info}}

    def operations_workspace(self):
        insights = self.api("GET", "/api/v1/insights").json()
        assert insights["counts"]["critical"] >= 1 and all(i["evidence"] for i in insights["insights"])
        boards = {p: self.api("GET", f"/api/v1/dashboards/{p}").json() for p in self.api("GET", "/api/v1/dashboards", headers={}).json()}
        assert all(b["kpis"] and b["charts"] for b in boards.values()), [p for p, b in boards.items() if not b.get("charts")]
        product = self.api("GET", "/api/v1/products/FG-SERUM-50").json()
        dc22 = next(d for d in product["warehouses"] if d["warehouse"] == "DC22")
        assert dc22["stockout_date"] and dc22["best_donor"] and product["resupply"]["components"]
        watch = self.api("POST", "/api/v1/watches", json={"name": "smoke cover", "kind": "days_of_cover", "params": {"material": "FG-PERFUME-100", "warehouse": "DC21"}, "threshold": 5}).json()
        evaluated = self.api("POST", "/api/v1/watches/evaluate", json={}).json()
        self.api("DELETE", f"/api/v1/watches/{watch['id']}")
        so = self.api("POST", "/api/v1/analysis/sales-orders", json={}).json()
        st = self.api("POST", "/api/v1/analysis/stocktake", json={}).json()
        rec = self.api("POST", "/api/v1/recommendations", json={"analysis_id": so["analysis_id"], "explanation": "smoke: fix at-risk orders", "source": "dashboard"}).json()
        self.api("POST", f"/api/v1/recommendations/{rec['id']}/decision", headers=self.manager, json={"decision": "accepted", "comment": "smoke"})
        executed = self.api("POST", f"/api/v1/recommendations/{rec['id']}/execute", headers=self.manager, json={}).json()
        assert executed["status"] == "executed" and executed["documents"]
        return {"insights": insights["counts"], "dashboards": {p: len(b["charts"]) for p, b in boards.items()}, "serum_dc22_stockout": dc22["stockout_date"],
                "donor": dc22["best_donor"]["from"], "watch_triggered": evaluated["triggered"], "sales_at_risk": so["at_risk"], "stocktake_investigate": st["to_investigate"],
                "sandbox_documents": [(d["doc_type"], d["doc_number"]) for d in executed["documents"]]}

    def manager_decision(self):
        pending = self.api("GET", "/api/v1/recommendations?status=pending_review").json()
        assert pending
        rec = pending[0]
        decided = self.api("POST", f"/api/v1/recommendations/{rec['id']}/decision", headers=self.manager, json={"decision": "accepted", "comment": "smoke"}).json()
        audit = self.api("GET", "/api/v1/audit?limit=200", headers=self.manager).json()
        assert decided["sap_written"] is False and audit["chain_valid"]
        sources = sorted({r["source"] for r in self.api("GET", "/api/v1/recommendations").json()})
        return {"accepted": rec["id"], "pending_before": len(pending), "audit_events": len(audit["events"]), "chain_valid": audit["chain_valid"], "sources": sources}

    def observability(self):
        evidence = {}
        metrics = self.api("GET", "/metrics", headers={}).text
        assert "copilot_agent_runs_total" in metrics
        evidence["agent_runs_metric"] = [line for line in metrics.splitlines() if line.startswith("copilot_agent_runs_total")][:6]
        if self.urls.get("langfuse"):
            time.sleep(5)
            # Langfuse v4 is events-only: observations are queried through the v2 public API.
            obs = self.http.get(self.urls["langfuse"] + "/api/public/v2/observations", params={"limit": 100}, auth=(self.env["LANGFUSE_PUBLIC_KEY"], self.env["LANGFUSE_SECRET_KEY"])).json()
            data = obs.get("data", [])
            assert data, obs
            names = sorted({o.get("name") for o in data if o.get("name")})
            evidence["langfuse_observations"] = {"page": len(data), "traces": len({o["traceId"] for o in data}), "types": sorted({o.get("type") for o in data}),
                                                 "graph_spans": [n for n in names if n in ("supply_chain_chat", "supply_chain_business", "supplier_deep_agent") or n.startswith(("agent", "tools", "explain", "approval"))][:12]}
        if self.urls.get("grafana"):
            dashboards = self.http.get(self.urls["grafana"] + "/api/search", params={"query": "SPARC"}, auth=("admin", self.env["GRAFANA_ADMIN_PASSWORD"])).json()
            assert dashboards, "Grafana dashboard missing"
            query = self.http.get(self.urls["grafana"] + "/api/datasources/proxy/uid/prometheus/api/v1/query", params={"query": "sum(copilot_http_requests_total)"}, auth=("admin", self.env["GRAFANA_ADMIN_PASSWORD"])).json()
            evidence["grafana"] = {"dashboards": [d["title"] for d in dashboards], "prometheus_requests_total": query.get("data", {}).get("result", [{}])[0].get("value")}
        return evidence


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--env-file", default=str(ROOT / ".env"))
    parser.add_argument("--base-domain", help="cloud: <ip-dashes>.sslip.io; omitted = local ports")
    parser.add_argument("--label", default=None)
    parser.add_argument("--timeout", type=float, default=900)
    parser.add_argument("--only", nargs="*")
    args = parser.parse_args()
    env = read_env(Path(args.env_file))
    if args.base_domain:
        d = args.base_domain
        urls = {"app": f"https://app.{d}", "mcp": f"https://mcp.{d}/mcp", "langgraph": f"https://studio.{d}", "langfuse": f"https://langfuse.{d}", "grafana": f"https://grafana.{d}"}
        label = args.label or env.get("CLOUD_PROVIDER", "cloud")
    else:
        urls = {"app": "http://localhost:8000", "mcp": "http://localhost:8002/mcp", "langgraph": "http://localhost:8123", "langfuse": "http://localhost:3003", "grafana": "http://localhost:3002"}
        label = args.label or "local"
    smoke = Smoke(urls, env, args.timeout, verify=True)
    checks = [
        ("platform status (all components up)", smoke.platform),
        ("security: auth, roles, SAP write block", smoke.security),
        ("deterministic analytics (readiness, XGBoost, OR-Tools, supplier, quality, logistics, what-if)", smoke.analytics),
        ("RAG semantic search (pgvector + bge-small)", smoke.rag),
        ("operations workspace: insights, role dashboards, product 360, watches, 1-click sandbox execution", smoke.operations_workspace),
        ("LangGraph Server graphs registered", smoke.langgraph_server),
        ("MCP server: initialize, list, call, auth", smoke.mcp),
        ("LangGraph Chat Graph with Qwen tool calls + memory + guardrail", smoke.langgraph_chat),
        ("LangGraph AgentFlow supervisor -> specialist -> interrupt -> review queue", smoke.langgraph_agentflow),
        ("LangGraph Business Graph interrupt -> resume -> review queue", smoke.langgraph_business),
        ("Deep Agent supplier research", smoke.deep_agent),
        ("Flowise Chatflow (Tool Agent + MCP + Qwen)", smoke.flowise_chatflow),
        ("Flowise AgentFlow V2 (supervisor, human input, boundary)", smoke.flowise_agentflow),
        ("manager decision + audit chain", smoke.manager_decision),
        ("observability (Prometheus, Grafana, Langfuse traces)", smoke.observability),
    ]
    for name, fn in checks:
        if args.only and not any(o in name for o in args.only):
            continue
        smoke.check(name, fn)
    passed = sum(r["status"] == "PASS" for r in smoke.results)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out = ROOT / "deploy-evidence" / f"{label}-smoke-{stamp}.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps({"label": label, "urls": urls, "timestamp": stamp, "passed": passed, "total": len(smoke.results), "results": smoke.results}, indent=1, default=str))
    print(f"\n{passed}/{len(smoke.results)} checks passed — evidence: {out}")
    return 0 if passed == len(smoke.results) else 1


if __name__ == "__main__":
    sys.exit(main())
