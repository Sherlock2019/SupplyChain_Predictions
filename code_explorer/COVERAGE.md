# Coverage report (generated)

- Definitions discovered: **1353** (1059 functions / methods, 130 classes / models, 164 tests)
- FastAPI endpoints: **163** (SCInsight 31, gateway 87, MCP 1)
- Flowise nodes with code: **46** (Custom Tools + Agentflow Custom Functions), copied to `07_flowise_functions/custom_js/`
- Definitions with an annotated copy: **781** in **38** modules; AST-identical to the original: **38/38**
- Call / dependency edges: **3745**

## Not annotated line by line (indexed with full original source in the registry, viewer and Flowise map)

- `backend/app/code_editor.py` — ops / deploy tooling (not part of the runtime)
- `backend/app/erp/checks.py` — ops / deploy tooling (not part of the runtime)
- `backend/app/erp/connectors.py` — ops / deploy tooling (not part of the runtime)
- `backend/app/erp/emulator.py` — ops / deploy tooling (not part of the runtime)
- `backend/app/erp/mapping.py` — ops / deploy tooling (not part of the runtime)
- `backend/app/erp/routes.py` — ops / deploy tooling (not part of the runtime)
- `backend/app/erp/service.py` — ops / deploy tooling (not part of the runtime)
- `backend/scinsight/rag_tuning/api.py` — ops / deploy tooling (not part of the runtime)
- `backend/scinsight/rag_tuning/chunking.py` — ops / deploy tooling (not part of the runtime)
- `backend/scinsight/rag_tuning/config.py` — ops / deploy tooling (not part of the runtime)
- `backend/scinsight/rag_tuning/documents.py` — ops / deploy tooling (not part of the runtime)
- `backend/scinsight/rag_tuning/embeddings.py` — ops / deploy tooling (not part of the runtime)
- `backend/scinsight/rag_tuning/evaluation.py` — ops / deploy tooling (not part of the runtime)
- `backend/scinsight/rag_tuning/flowise_adapter.py` — ops / deploy tooling (not part of the runtime)
- `backend/scinsight/rag_tuning/indexing.py` — ops / deploy tooling (not part of the runtime)
- `backend/scinsight/rag_tuning/publishing.py` — ops / deploy tooling (not part of the runtime)
- `backend/scinsight/rag_tuning/registry.py` — ops / deploy tooling (not part of the runtime)
- `backend/scinsight/rag_tuning/retrieval.py` — ops / deploy tooling (not part of the runtime)
- `flowise/bootstrap.py` — ops / deploy tooling (not part of the runtime)
- `flowise/code_explorer/deploy_code_map.py` — ops / deploy tooling (not part of the runtime)
- `flowise/scinsight/deploy.py` — ops / deploy tooling (not part of the runtime)
- `scripts/aws-cost-estimate.py` — ops / deploy tooling (not part of the runtime)
- `scripts/gen-env.py` — ops / deploy tooling (not part of the runtime)
- `scripts/generate_tenants.py` — ops / deploy tooling (not part of the runtime)
- `scripts/langgraph_assistants.py` — ops / deploy tooling (not part of the runtime)
- `scripts/rag_tuning.py` — ops / deploy tooling (not part of the runtime)
- `scripts/scinsight_compare.py` — ops / deploy tooling (not part of the runtime)
- `scripts/smoke.py` — ops / deploy tooling (not part of the runtime)
- `templates/backend/fastapi_app.py` — ops / deploy tooling (not part of the runtime)
- `templates/backend/fastapi_router.py` — ops / deploy tooling (not part of the runtime)
- `templates/backend/langgraph_graph.py` — ops / deploy tooling (not part of the runtime)
- `templates/backend/mcp_server.py` — ops / deploy tooling (not part of the runtime)
- `tests/conftest.py` — pytest tests
- `tests/scinsight/conftest.py` — pytest tests
- `tests/scinsight/test_api_scenarios.py` — pytest tests
- `tests/scinsight/test_business_rules.py` — pytest tests
- `tests/scinsight/test_flowise_e2e.py` — pytest tests
- `tests/scinsight/test_langgraph_mirror.py` — pytest tests
- `tests/scinsight/test_rag_tuning.py` — pytest tests
- `tests/scinsight/test_security.py` — pytest tests
- `tests/test_api.py` — pytest tests
- `tests/test_code_editor.py` — pytest tests
- `tests/test_engine.py` — pytest tests
- `tests/test_erp.py` — pytest tests
- `tests/test_flowise_flows.py` — pytest tests
- `tests/test_fused_app.py` — pytest tests
- `tests/test_graphs_and_agents.py` — pytest tests
- `tests/test_mentana_features.py` — pytest tests
- `tests/test_poc_contract.py` — pytest tests
- `tests/test_product_brief_outlook.py` — pytest tests
- `tests/test_rag_mcp_store.py` — pytest tests
- `tests/test_roles_and_moat.py` — pytest tests
- `tests/test_templates.py` — pytest tests
- `tests/test_tenants_and_map.py` — pytest tests

## Unused? (no caller found by static analysis — review before deleting; dynamic calls may exist)

- F0759 `chunk_document` (backend/scinsight/rag.py:64)

## Problems

- none
