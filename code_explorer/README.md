# SCInsight Functions & Code Explorer

A commented, navigable reference of the code that runs the SupplyChain Insight AI POC (SCInsight API, SPARC / Aurelia gateway,
LangGraph graphs, MCP tools, Flowise custom functions). The application itself is untouched: `backend/` stays the source of truth;
everything here is a copy or an index.

## Where to look

| What | Where |
|---|---|
| Every function, method, class (stable ids F0001…), status used / framework / tooling / test | [FUNCTION_INDEX.md](FUNCTION_INDEX.md) |
| Coverage, what is not annotated and why, problems | [COVERAGE.md](COVERAGE.md) |
| All FastAPI endpoints (method, full path, dependencies, body model, Flowise callers) | [01_fastapi/ENDPOINTS.md](01_fastapi/ENDPOINTS.md) |
| Flowise node → FastAPI handler mapping | [07_flowise_functions/tool_mappings/FLOWISE_TO_PYTHON.md](07_flowise_functions/tool_mappings/FLOWISE_TO_PYTHON.md) |
| Searchable viewer (code, callers, callees as links) — open in a browser | [viewer/index.html](viewer/index.html) |
| Machine-readable index and call graph | [registry/functions.json](registry/functions.json), [registry/dependencies.json](registry/dependencies.json) |
| Flowise visual code map | Flowise → Agentflows → category "SCInsight Code Explorer" (see [flowise/code_explorer/README_IMPORT.md](../flowise/code_explorer/README_IMPORT.md)) |

## Folders

One annotated copy per real module, placed in the folder of its main role (modules are never split). Each folder has a generated
`FUNCTIONS.md`. Topic folders (`02_business_logic/inventory`, `bom`, `shortages`, `production`, `procurement`, `optimization`,
`05_security_governance/human_approval`, `audit_logging`, `validation`) only hold an index pointing into the home modules.

- `01_fastapi/` — `endpoints/` (both FastAPI apps), `pydantic_models/`, `app_setup/` (settings, config, metrics). Dependencies
  (`principal`, `reader`, `manager`) are nested in the app factories, so they appear in `endpoints/`.
- `02_business_logic/` — `scinsight_rules/` (business.py: stock, BOM, shortage, transfers, lead time), `scinsight_use_cases/` (service.py),
  `aurelia_engine/`, `aurelia_views/` (roles, dashboards, insights, moat), `optimization/` (OR-Tools).
- `03_sap_data/` — `synthetic_sap/` (fixtures), `sap_connectors/` (OData adapter), `sql/` (Database + migrations), `repositories/` (store, tenants).
- `04_ai_ml/` — `llm/`, `rag/`, `forecasting/` (XGBoost, governed lead-time model), `agent_tools/` (LangChain tools, MCP server, agent backend), `langgraph/`, `evaluation/`.
- `05_security_governance/` — `authentication/`, `authorization/` (roles, reviewer authority, audit hash chain), topic indexes.
- `06_testing/` — index of the pytest files and smoke / ops tooling (original source in the viewer and the Flowise map).
- `07_flowise_functions/` — `custom_js/` (the real JavaScript of the 14 Custom Tools and 32 Agentflow Custom Functions), `tool_mappings/`, `deployment/`.

## How an annotated function reads

```python
    # ===== FUNCTION: Service.material_readiness() =====       <- generated
    # ID: F0325 · method · used                                 <- generated
    # ORIGINAL FILE: backend/scinsight/service.py:160-229       <- generated
    # ROLE: ... / INPUTS: ... / OUTPUT: ... / EXAMPLE: ...      <- written by hand
    # CALLED BY:  <- F0126 create_app.material_readiness() ...  <- generated from the call graph
    # CALLS:      -> F0302 calculate_bom_requirements() ...     <- generated from the call graph
    def material_readiness(self, p: Principal, req: dict) -> dict:
        # comments on the meaningful lines (hand-written)
        ...
```

Only comment lines are added. `build_code_explorer.py` proves every copy has the same Python AST as its original.

## Regenerate after a code change

```bash
python3 code_explorer/tools/build_code_explorer.py          # index, call graph, headers, docs, viewer, Flowise spec
python3 code_explorer/tools/build_code_explorer.py --check  # fails if an annotated copy no longer matches its original
python3 flowise/code_explorer/deploy_code_map.py build      # Flowise exports (inside the Flowise container)
python3 flowise/code_explorer/deploy_code_map.py import --flowise-url http://127.0.0.1:3101
```

When `--check` reports a STALE copy, copy the new original over the annotated file and re-add the comments (or keep the old comments
on unchanged functions); new functions appear in the index, viewer and Flowise map automatically with their original source.

## Limits (honest)

- Calls are found by static analysis (direct names, module aliases, `self.`, typed variables, `get_backend()`, HTTP paths, functions passed
  as values). Dynamic dispatch such as `getattr(self, f"_{persona}")` is covered by marking framework-called methods `used (framework)`.
- Hand-written line comments cover the 38 backend modules. Tests, `scripts/` and the Flowise deploy helpers are indexed with their
  original source, not commented line by line.
- The Flowise canvases were verified by reading the stored flows back through the Flowise API (node and edge counts); their on-screen
  rendering was not checked in a browser. A sticky note in Flowise 3.1.2 is an auto-growing text area, so long functions make tall notes.
