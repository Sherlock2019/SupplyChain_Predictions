"""Static checks of the Flowise flows generated from the live Flowise node classes (flowise/generated/*.json)."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

GENERATED = Path(__file__).resolve().parents[1] / "flowise" / "generated"
READ_ONLY = {"sap_snapshot", "factory_material_readiness", "warehouse_stock_balance", "supplier_risk", "quality_status", "logistics_status", "inventory_overview", "sales_order_fulfilment", "stocktake_reconciliation", "search_governed_knowledge"}


def load(kind: str) -> dict:
    path = GENERATED / f"{kind}.json"
    if not path.exists():
        pytest.skip("run flowise/bootstrap.py to generate flows")
    return json.loads(path.read_text())


@pytest.mark.parametrize("kind", ["chatflow", "agentflow"])
def test_edges_reference_real_nodes_and_handles(kind):
    flow = load(kind)
    nodes = {n["id"]: n for n in flow["nodes"]}

    def handles(node):  # a node with several outputs stores one "options" anchor listing them
        for anchor in node["data"]["outputAnchors"]:
            yield from (o["id"] for o in anchor["options"]) if anchor.get("type") == "options" else (anchor["id"],)
    for edge in flow["edges"]:
        assert edge["source"] in nodes and edge["target"] in nodes
        assert edge["sourceHandle"] in set(handles(nodes[edge["source"]]))
        if kind == "chatflow":
            assert any(a["id"] == edge["targetHandle"] for a in nodes[edge["target"]]["data"]["inputAnchors"])
    assert all(n["data"].get("version") for n in flow["nodes"])  # versions come from the installed Flowise classes


def test_chatflow_is_tool_agent_with_mcp_sap_odata_and_memory():
    flow = load("chatflow")
    names = [n["data"]["name"] for n in flow["nodes"]]
    assert {"chatOpenAICustom", "bufferWindowMemory", "customMCP", "toolAgent", "requestsGet", "stickyNote", "inputModerationSimple",
            # RAG pipeline: load -> chunk -> embed -> pgvector store (record manager) -> retriever tool
            "folderFiles", "markdownTextSplitter", "openAIEmbeddingsCustom", "postgres", "postgresRecordManager", "retrieverTool"} == set(names)
    mcp = next(n for n in flow["nodes"] if n["data"]["name"] == "customMCP")
    assert set(json.loads(mcp["data"]["inputs"]["mcpActions"])) == READ_ONLY
    assert "$vars.mcp_api_key" in mcp["data"]["inputs"]["mcpServerConfig"]
    sap = [n for n in flow["nodes"] if n["data"]["name"] == "requestsGet"]  # explicit SAP OData tools, read-only GETs
    assert len(sap) == 4 and all("/sap/opu/odata/sap/ZSCM_COPILOT_SRV/" in n["data"]["inputs"]["requestsGetUrl"] for n in sap)
    assert all("$vars.copilot_tool_key" in n["data"]["inputs"]["requestsGetHeaders"] for n in sap)
    tool_edges = [e for e in flow["edges"] if e["target"] == "toolAgent_0" and "-input-tools-" in e["targetHandle"]]
    assert len(tool_edges) == 6  # MCP + 4 SAP OData tools + RAG retriever tool
    assert names.count("stickyNote") >= 9  # architecture panels


def test_agentflow_full_workflow_sap_rag_nine_roles_and_human_input():
    flow = load("agentflow")
    by_name: dict[str, list] = {}
    for node in flow["nodes"]:
        by_name.setdefault(node["data"]["name"], []).append(node)
    labels = {n["id"]: n["data"]["label"] for n in flow["nodes"]}
    nxt = {e["source"]: e["target"] for e in flow["edges"]}
    start = by_name["startAgentflow"][0]["id"]
    # front end -> gateway -> SAP OData (read-only GET) -> RAG (pgvector) -> supervisor
    sap, rag = nxt[start], nxt[nxt[start]]
    assert "SAP" in labels[sap] and "RAG" in labels[rag] and labels[nxt[rag]].startswith("Supply-chain supervisor")
    http = {n["id"]: n["data"]["inputs"] for n in by_name["httpAgentflow"]}
    assert http[sap]["method"] == "GET" and "/sap/opu/odata/sap/ZSCM_COPILOT_SRV/" in http[sap]["url"]
    assert http[rag]["method"] == "GET" and http[rag]["url"].endswith("/api/v1/rag/search")
    supervisor = by_name["conditionAgentAgentflow"][0]
    assert len(supervisor["data"]["inputs"]["conditionAgentScenarios"]) == len(supervisor["data"]["outputAnchors"]) == 10  # 9 roles + SAP boundary
    agents = by_name["agentAgentflow"]
    assert len(agents) == 9 and len(by_name["humanInputAgentflow"]) == 6
    assert {a["data"]["label"].split(" · ")[0] for a in agents} >= {"Supervisor Agent", "Forecast Agent", "Factory Agent", "Procurement Agent", "Inventory Agent",
                                                                    "Logistics Agent", "Quality Agent", "Cost Intelligence Agent", "Learning Agent"}
    for agent in agents:
        tool = agent["data"]["inputs"]["agentTools"][0]
        assert tool["agentSelectedTool"] == "customMCP"
        assert set(json.loads(tool["agentSelectedToolConfig"]["mcpActions"])) <= READ_ONLY
        assert f"{{{{ {rag} }}}}" in agent["data"]["inputs"]["agentMessages"][0]["content"]  # RAG context reaches every specialist
    submits = [i for nid, i in http.items() if nid not in (sap, rag)]
    assert len(submits) == 6 and all(i["method"] == "POST" and i["url"].endswith("/api/v1/recommendations/from-agent") for i in submits)
    assert len([e for e in flow["edges"] if e["data"].get("isHumanInput")]) == 12
    assert len(by_name["stickyNoteAgentflow"]) >= 11  # 9 architecture panels + workflow + governance

@pytest.mark.parametrize("kind", ["chatflow", "agentflow"])
def test_no_secrets_in_flow_json(kind):
    text = json.dumps(load(kind))
    env = Path(__file__).resolve().parents[1] / ".env"
    if env.exists():
        for line in env.read_text().splitlines():
            key, _, value = line.partition("=")
            if key.endswith(("_KEY", "_PASSWORD", "_SECRET", "SECRETKEY")) and len(value) >= 12:
                assert value not in text, f"{key} leaked into {kind}"
