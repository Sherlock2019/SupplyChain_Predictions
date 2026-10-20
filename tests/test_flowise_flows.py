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
    for edge in flow["edges"]:
        assert edge["source"] in nodes and edge["target"] in nodes
        assert any(a["id"] == edge["sourceHandle"] for a in nodes[edge["source"]]["data"]["outputAnchors"])
        if kind == "chatflow":
            assert any(a["id"] == edge["targetHandle"] for a in nodes[edge["target"]]["data"]["inputAnchors"])
    assert all(n["data"].get("version") for n in flow["nodes"])  # versions come from the installed Flowise classes


def test_chatflow_is_tool_agent_with_mcp_and_memory():
    flow = load("chatflow")
    names = {n["data"]["name"] for n in flow["nodes"]}
    assert names == {"chatOpenAICustom", "bufferWindowMemory", "customMCP", "toolAgent"}
    mcp = next(n for n in flow["nodes"] if n["data"]["name"] == "customMCP")
    assert set(json.loads(mcp["data"]["inputs"]["mcpActions"])) == READ_ONLY
    assert "$vars.mcp_api_key" in mcp["data"]["inputs"]["mcpServerConfig"]


def test_agentflow_supervisor_specialists_and_human_input():
    flow = load("agentflow")
    by_name: dict[str, list] = {}
    for node in flow["nodes"]:
        by_name.setdefault(node["data"]["name"], []).append(node)
    supervisor = by_name["conditionAgentAgentflow"][0]
    assert len(supervisor["data"]["inputs"]["conditionAgentScenarios"]) == len(supervisor["data"]["outputAnchors"]) == 4
    assert len(by_name["agentAgentflow"]) == 3 and len(by_name["humanInputAgentflow"]) == 2
    for agent in by_name["agentAgentflow"]:
        tool = agent["data"]["inputs"]["agentTools"][0]
        assert tool["agentSelectedTool"] == "customMCP"
        assert set(json.loads(tool["agentSelectedToolConfig"]["mcpActions"])) <= READ_ONLY
    for http in by_name["httpAgentflow"]:
        assert http["data"]["inputs"]["url"].endswith("/api/v1/recommendations/from-agent")
        assert http["data"]["inputs"]["method"] == "POST"
    human_edges = [e for e in flow["edges"] if e["data"].get("isHumanInput")]
    assert len(human_edges) == 4


@pytest.mark.parametrize("kind", ["chatflow", "agentflow"])
def test_no_secrets_in_flow_json(kind):
    text = json.dumps(load(kind))
    env = Path(__file__).resolve().parents[1] / ".env"
    if env.exists():
        for line in env.read_text().splitlines():
            key, _, value = line.partition("=")
            if key.endswith(("_KEY", "_PASSWORD", "_SECRET", "SECRETKEY")) and len(value) >= 12:
                assert value not in text, f"{key} leaked into {kind}"
