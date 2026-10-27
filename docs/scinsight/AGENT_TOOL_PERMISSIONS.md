# Agent and tool permissions

Permissions are enforced in three layers. The prompt is never one of them.

1. **Flowise:** each node and tool calls only its fixed endpoint(s) on `$vars.sci_api_url`.
2. **API key → role:** Flowise holds one key, `SCI_AGENT_KEY`, which maps to role `agent_service`.
3. **API authorisation:** checked per route in `backend/scinsight/app.py`, `service.py` and `security.py`.

## Agents → endpoints

| Agent | Endpoints it can call (code-fixed) |
|---|---|
| Chatflow tools | The 14 endpoints in [FLOWISE_CHATFLOW.md](FLOWISE_CHATFLOW.md) |
| Supervisor | POST /context/validate · GET /calculations/{id} · POST /decisions · GET /decisions/{id} · POST /decisions/{id}/withdraw |
| Factory-Planning | POST /context/validate · GET /sap/production-orders · POST /optimizer/material-readiness · POST /rag/search |
| Procurement | POST /context/validate · POST /optimizer/replenishment · GET /sap/suppliers · POST /forecast/lead-time · POST /rag/search |
| Warehouse | POST /context/validate · POST /optimizer/warehouse-balancing · POST /rag/search |
| Inventory-Optimizer | POST /context/validate · POST /optimizer/replenishment · POST /forecast/demand · POST /rag/search |
| Logistics | POST /context/validate · POST /optimizer/warehouse-balancing · POST /rag/search |
| Quality | POST /context/validate · POST /quality/check-stock · POST /rag/search |
| Decision-Outcome-Learning | POST /context/validate · GET /decisions/{id} · POST /outcomes/reconcile · GET /learning/metrics |

No agent can call: review, SAP execution record, model training or promotion, audit read, or any SAP write.

## Roles → actions (server-side)

| Action | agent_service (Flowise) | planner | production_planner | procurement / warehouse / logistics / quality manager | supply_chain_director | sap_executor | mlops_engineer |
|---|---|---|---|---|---|---|---|
| Read SAP data, run calculations, RAG search | ✓ | ✓ | ✓ | ✓ | ✓ | – | ✓ |
| Create recommendation (`POST /decisions`) | ✓ | ✓ | – | – | – | – | – |
| Withdraw own pending recommendation | creator | creator | creator | creator | ✓ (any) | – | – |
| Review (approve / reject / modify / defer) | **never (403)** | – | factory | own domain | all domains | – | – |
| Record SAP execution (reference only) | – | – | – | – | ✓ | ✓ | – |
| Reconcile outcome | ✓ | ✓ | – | – | ✓ | – | ✓ |
| Train lead-time model | – | – | – | – | – | – | ✓ |
| Promote model (manual gate) | – | – | – | – | ✓ | – | – |
| Read audit log | – | – | – | – | ✓ | – | – |
| Write to SAP | nobody: `/api/v1/sap/*` writes get 405; `SAP_WRITE_ENABLED=true` stops the service from starting |

Roles add up. Every synthetic human user also holds `planner`, except the SAP executor and MLOps users, so a manager can
also create and reconcile. Users and roles are defined in `backend/scinsight/fixtures.py`, `USERS`.

Domain authority (`REVIEW_AUTHORITY` in `security.py`):
- factory → production_planner
- procurement → procurement_manager
- warehouse / inventory → warehouse_manager
- logistics → logistics_manager
- quality → quality_manager

The supply_chain_director can review every domain.

## Network and secrets

- Flowise's SSRF policy (`HTTP_SECURITY_CHECK=false` plus a custom `HTTP_DENY_LIST`) denies loopback, cloud metadata, 10/8,
  192.168/16 and the IPv6 private ranges. Only the Docker bridge (172.16/12: api, flowise) is reachable.
- Flowise prediction for all 9 flows requires the `scinsight-flows` API key (`apikeyid` on each flow). Without it the request
  is refused ("Unauthorized"; Flowise returns HTTP 500 with that message).
- The agent key is stored in the Flowise Variable `sci_agent_key`. It never appears in a prompt, flow export or tool output.
