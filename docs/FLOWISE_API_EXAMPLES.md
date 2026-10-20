# POC contract API — Flowise and LangGraph examples

Short REST paths for Flowise HTTP nodes, LangGraph tools and any other client. They are thin wrappers over the same
deterministic engine, governance ledger, authentication, tenant scope and audit chain as `/api/v1/...`. Live, typed
documentation: **http://localhost:8000/docs** (tag *POC contract (Flowise / LangGraph REST)*).

| Method | Path | Who | What |
| --- | --- | --- | --- |
| GET | `/sap/inventory?plant=&material=` | planner, manager | SAP material stock (read-only OData `A_MaterialStock`) |
| GET | `/sap/production-orders?plant=&material=` | planner, manager | SAP production orders (read-only) |
| POST | `/forecast/demand` | planner, manager | XGBoost daily demand forecast → stored analysis `AN-…` |
| POST | `/forecast/supplier-lead-time` | planner, manager | Empirical lead time: contract + observed delays (mean, P90, on-time %) |
| POST | `/optimizer/material-readiness` | planner, manager | BOM readiness (stock + confirmed POs, quality-held stock excluded) |
| POST | `/optimizer/warehouse-transfer` | planner, manager | OR-Tools minimum-cost transfers between DC01, DC21, DC22 |
| POST | `/decisions` | planner, manager | Submit a stored analysis for human review |
| POST | `/decisions/{id}/human-review` | **manager** | Accept / accept with changes (`modified` + `reason_code`) / reject |
| POST | `/outcomes/reconcile` | **manager** | Compare what SAP shows happened with what the executed decision expected |
| GET | `/learning/model-performance` | planner, manager | WAPE vs baseline, drift, verified-outcome rate |

Rules enforced by the gateway: SAP writes return **405**; quantities come only from the deterministic engine; only a
manager decides; execution creates SAP **sandbox** documents only; with `TENANT_SCOPES` set, a key outside its tenants
gets **403** (`X-Tenant: cosmetics/aurelia` selects the customer).

## curl

```bash
KEY=$(grep ^PLANNER_API_KEY .env | cut -d= -f2); MGR=$(grep ^MANAGER_API_KEY .env | cut -d= -f2); API=http://localhost:8000

curl -s -H "X-API-Key: $KEY" "$API/sap/inventory?plant=DC21"
curl -s -H "X-API-Key: $KEY" -H 'Content-Type: application/json' $API/forecast/supplier-lead-time -d '{"supplier":"AirlessPack Asia"}'
# -> contract 42 d, predicted 55 d, P90 57 d, on-time 0 %, confidence low (2 receipts)

AN=$(curl -s -H "X-API-Key: $KEY" -H 'Content-Type: application/json' $API/optimizer/warehouse-transfer -d '{"material":"FG-PERFUME-100"}' | jq -r .analysis_id)
ID=$(curl -s -H "X-API-Key: $KEY" -H 'Content-Type: application/json' $API/decisions -d "{\"analysis_id\":\"$AN\",\"explanation\":\"Protect Dubai\"}" | jq .id)
curl -s -H "X-API-Key: $MGR" -H 'Content-Type: application/json' $API/decisions/$ID/human-review -d '{"decision":"accepted","modified":true,"reason_code":"timing","comment":"ship Monday"}'
curl -s -X POST -H "X-API-Key: $MGR" $API/api/v1/recommendations/$ID/execute          # SAP sandbox documents
curl -s -H "X-API-Key: $MGR" -H 'Content-Type: application/json' $API/outcomes/reconcile \
  -d "{\"decision_id\":$ID,\"sap_document\":\"5000012345\",\"actual_quantity\":1110,\"actual_date\":\"2026-10-23\",\"realized_impact_eur\":4200}"
curl -s -H "X-API-Key: $KEY" $API/learning/model-performance
```

## Flowise — AgentFlow V2 **HTTP** node

Create the Flowise Variables `copilot_api_url` (e.g. `http://api:8000` inside Docker) and `copilot_tool_key` (a planner key)
— `flowise/bootstrap.py` does this automatically.

| Field | Value |
| --- | --- |
| Method | `POST` |
| URL | `{{ $vars.copilot_api_url }}/optimizer/warehouse-transfer` |
| Headers | `X-API-Key` = `{{ $vars.copilot_tool_key }}` · `Content-Type` = `application/json` |
| Body type | JSON |
| Body | `{"material": "FG-PERFUME-100", "horizon_days": 14}` |
| Response | JSON → use `{{ httpAgentflow_0 }}` (e.g. `.analysis_id`) in the next node |

GET with the question passed safely as a query parameter (as the SAP → RAG steps of the AgentFlow do):
`GET {{ $vars.copilot_api_url }}/api/v1/rag/search` · Query params `q` = `{{ question }}`, `top_k` = `3`.

## Flowise — Chatflow **Requests Get** tool

| Field | Value |
| --- | --- |
| URL | `{{$vars.copilot_api_url}}/sap/production-orders` |
| Name | `sap_production_orders` |
| Description | SAP production orders: order, plant, material, quantity, finish date, status (read-only). |
| Headers | `{"X-API-Key": "{{$vars.copilot_tool_key}}"}` |

The Flowise canvas **"SPARC FastAPI gateway - configuration map"** has these tools wired to a Tool Agent, plus panels for
the middleware chain, security, routes, SAP adapter, agent endpoints, data stores, configuration and observability.

## LangGraph — tool calling the contract

```python
import httpx
from langchain_core.tools import tool

API, KEY = "http://api:8000", "<planner key>"

@tool
def supplier_lead_time(supplier: str) -> dict:
    """Empirical supplier lead-time forecast from SAP receipts (contract + observed delays)."""
    return httpx.post(f"{API}/forecast/supplier-lead-time", json={"supplier": supplier}, headers={"X-API-Key": KEY}, timeout=30).json()
```

Human approval stays outside the agent: a graph step can submit `POST /decisions`, but only a manager key can call
`/decisions/{id}/human-review`, and agents never receive manager keys.
