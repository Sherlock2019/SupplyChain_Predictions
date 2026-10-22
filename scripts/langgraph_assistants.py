#!/usr/bin/env python3
"""Create the LangGraph Studio presets for you: YAML files to paste into Studio, and named assistants on the LangGraph server.

    .venv/bin/python scripts/langgraph_assistants.py              # write langgraph/studio/*.yaml and create/update the assistants
    .venv/bin/python scripts/langgraph_assistants.py --files-only # only the YAML files
    python3 scripts/langgraph_assistants.py --assistants-only     # only the assistants (stdlib only; used by start-localdemo.sh)

Assistants are saved configurations of a graph. In Studio pick one from the assistant dropdown (or "Manage Assistants"):
  supplier_deep_agent  · Deep agent · standard / quick / thorough / executive summary   (harness presets)
  scinsight_supervisor · SC Agent Manager · pause for approval / hand back without pausing
Idempotent: assistants are matched by name and updated in place.
"""
from __future__ import annotations

import argparse
import json
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STUDIO = ROOT / "langgraph" / "studio"
ALL_TOOLS = ["supplier_risk", "sap_snapshot", "search_governed_knowledge", "quality_status", "logistics_status", "factory_material_readiness"]
ALL_SUBAGENTS = ["contract-analyst", "quality-analyst", "logistics-analyst"]
STANDARD = {"temperature": 0, "max_tokens": 1500, "max_steps": 60, "max_model_calls": 15, "max_tool_calls": 20, "max_calls_per_tool": 6, "max_subagent_calls": 4,
            "model_timeout_seconds": 120, "model_retries": 1, "tool_retries": 1, "subagents": ALL_SUBAGENTS, "tools": ALL_TOOLS,
            "require_plan": True, "require_citations": True, "report_style": "full"}
HARNESS_PRESETS = {  # name -> (what it is for, harness)
    "standard": ("The defaults: balanced depth and speed.", STANDARD),
    "quick": ("Fast first look: one contract check, few tool calls, executive summary (about 30 s on this machine).",
              {**STANDARD, "max_tokens": 1200, "max_steps": 40, "max_model_calls": 6, "max_tool_calls": 6, "max_calls_per_tool": 2, "max_subagent_calls": 1,
               "subagents": ["contract-analyst"], "report_style": "executive"}),
    "thorough": ("Full due diligence: all analysts, larger budgets, longer report.",
                 {**STANDARD, "temperature": 0.1, "max_tokens": 3000, "max_steps": 100, "max_model_calls": 25, "max_tool_calls": 35, "max_calls_per_tool": 8,
                  "max_subagent_calls": 6, "model_timeout_seconds": 240}),
    "executive": ("Same research as standard, written as at most 8 bullet points for leadership.", {**STANDARD, "max_tokens": 1200, "report_style": "executive"}),
}
SUPERVISOR_PRESETS = {
    "pause for approval": ("Saves the recommendation and pauses (interrupt) until you resume with proceed / reject.", {"pause_for_approval": True}),
    "hand back, no pause": ("Saves the recommendation and returns at once (what the chat bot uses).", {"pause_for_approval": False}),
}
GRAPH_OF = {"factory": "scinsight_factory_planning", "procurement": "scinsight_procurement", "warehouse": "scinsight_warehouse",
            "inventory": "scinsight_inventory_optimizer", "logistics": "scinsight_logistics", "quality": "scinsight_quality", "learning": "scinsight_outcome_learning"}


def _dump(path: Path, docs: list[dict], header: str) -> str:
    import yaml  # only needed for the files (dev virtualenv); creating assistants is stdlib only

    path.parent.mkdir(parents=True, exist_ok=True)
    body = "\n---\n".join(yaml.safe_dump(d, sort_keys=False, allow_unicode=True, width=200).rstrip() for d in docs)
    path.write_text(f"# {header}\n{body}\n", encoding="utf-8")
    return str(path.relative_to(ROOT))


def write_files() -> list[str]:
    written = []
    for name, (why, h) in HARNESS_PRESETS.items():
        written.append(_dump(STUDIO / "harness" / "supplier_deep_agent" / f"{name}.yaml", [h],
                             f"supplier_deep_agent harness preset '{name}': {why}\n# Paste into Studio > Input > Harness (YAML), or pick the assistant 'Deep agent · {name}'."))
    roles = json.loads((ROOT / "data" / "scinsight" / "role_questions.json").read_text())["roles"]
    for r in roles:
        docs = [{"messages": [{"type": "human", "content": q["q"]}]} for q in r["questions"]]
        written.append(_dump(STUDIO / "inputs" / "scinsight_supervisor" / f"{r['role']}.yaml", docs,
                             f"{r['title']}: 5 ready-to-paste inputs for scinsight_supervisor (also work for scinsight_chat).\n"
                             "# Studio > Input > View Raw: paste ONE block (between the --- lines), then Submit."))
        if r.get("specialist"):
            written.append(_dump(STUDIO / "inputs" / GRAPH_OF[r["specialist"]] / f"{r['role']}.yaml", docs,
                                 f"{r['title']}: 5 ready-to-paste inputs for {GRAPH_OF[r['specialist']]}.\n# Studio > Input > View Raw: paste ONE block, then Submit."))
    supplier = [{"messages": [{"type": "human", "content": q}]} for q in (
        "Supplier: BioActive Labs. Task: Assess supply continuity, quality and contract risk, and list the contract levers available.",
        "Supplier: PackGlass Europe. Task: Is this supplier a single-source risk, and what are our contract levers?",
        "Supplier: BioActive Labs. Task: Summarise quality issues and open inspection lots for the materials it supplies.",
        "Supplier: AirlessPack Asia. Task: Are there shipment delays that threaten production, and what can we do?",
        "Supplier: PackGlass Europe. Task: Give an executive risk rating with the three key facts.")]
    written.append(_dump(STUDIO / "inputs" / "supplier_deep_agent" / "procurement_manager.yaml", supplier,
                         "supplier_deep_agent (SPARC data): 5 ready-to-paste research inputs. Studio > Input > View Raw: paste ONE block, then Submit."))
    return written


def _call(base: str, method: str, path: str, body: dict | None = None):
    req = urllib.request.Request(base + path, data=json.dumps(body).encode() if body is not None else None,
                                 headers={"Content-Type": "application/json"}, method=method)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read() or b"null")


def create_assistants(base: str) -> list[str]:
    done = []
    wanted = [("supplier_deep_agent", f"Deep agent · {name}", why, {"harness": h}) for name, (why, h) in HARNESS_PRESETS.items()]
    wanted += [("scinsight_supervisor", f"SC Agent Manager · {name}", why, cfg) for name, (why, cfg) in SUPERVISOR_PRESETS.items()]
    existing = {a.get("name"): a for a in _call(base, "POST", "/assistants/search", {"limit": 100})}
    for graph_id, name, why, configurable in wanted:
        body = {"graph_id": graph_id, "name": name, "description": why, "config": {"configurable": configurable}, "metadata": {"source": "scripts/langgraph_assistants.py"}}
        if name in existing:
            _call(base, "PATCH", f"/assistants/{existing[name]['assistant_id']}", body)
            done.append(f"updated  {name}")
        else:
            _call(base, "POST", "/assistants", body)
            done.append(f"created  {name}")
    return done


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--langgraph-url", default="http://localhost:8123")
    parser.add_argument("--files-only", action="store_true")
    parser.add_argument("--assistants-only", action="store_true")
    args = parser.parse_args()
    if not args.assistants_only:
        files = write_files()
        print(f"wrote {len(files)} YAML files under langgraph/studio/")
    if not args.files_only:
        for line in create_assistants(args.langgraph_url):
            print(line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
