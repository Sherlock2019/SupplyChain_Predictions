# SupplyChain Insight AI — Cosmetics POC

A planning assistant for a synthetic cosmetics company (Belleva Cosmetics: 1 factory, 3 warehouses, 20 SKUs, 10 materials).
Flowise flows hold the conversation. Every number comes from a FastAPI calculation engine over synthetic SAP data. Policies come
from a governed PostgreSQL + pgvector knowledge base. Any proposed action waits for an authorised human, and approvals are checked
later against real outcomes.

> **Status:** proof of concept on synthetic data. It is not connected to a real SAP system and never writes to SAP.

## What is in the box

| Part | Where | What it does |
|---|---|---|
| SCInsight API (FastAPI) | `backend/scinsight/` · port **8100** · Swagger `http://localhost:8100/docs` | Synthetic SAP read API, deterministic calculations, recommendations and human review, outcome reconciliation, learning metrics, governed RAG, audit hash chain |
| Database | PostgreSQL database `scinsight` (+ pgvector), SQLite for unit tests | 26 tables, versioned migrations (`backend/scinsight/migrations/`) |
| Knowledge base | `data/scinsight/knowledge/*.md` | 9 synthetic policies, SOPs and agreements with front-matter metadata (plus one deliberately broken document that ingestion rejects) |
| Chatflow | `flowise/chatflows/SCInsight-Cosmetics-Chatflow-v1.json` | Tool Agent over 14 allowlisted Custom Tools, memory, input guardrail, post-processing evidence gate |
| Supervisor Agentflow | `flowise/agentflows/SCInsight-Cosmetics-Supervisor-Agentflow-v1.json` | Context check, intent and guard, specialist (Execute Flow), save recommendation, Human Input, verified status |
| 7 specialist Agentflows | `flowise/agentflows/SCInsight-Cosmetics-*-Agentflow-v1.json` | Factory Planning, Procurement, Warehouse, Inventory Optimizer, Logistics, Quality, Decision-Outcome-Learning |
| Custom Tools | `flowise/tools/*.json` | 14 tools; each calls one fixed SCInsight endpoint |
| Prompts | `flowise/prompts/*.md` | Every system prompt used by the flows (generated, read-only copies) |
| Builder / importer | `flowise/scinsight/build-scinsight.cjs`, `flowise/scinsight/deploy.py` | Generate the exports from the installed Flowise's node classes, then import and bind them into any Flowise 3.x |

## Quick start (local)

```bash
python3 scripts/gen-env.py --add-missing        # adds SCI_*_KEY user keys to an existing .env (new installs: gen-env.py)
./start-localdemo.sh                             # whole stack; it also imports the SCInsight flows into Flowise
# or step by step:
docker compose --profile core up -d postgres flowise scinsight-api
python3 flowise/scinsight/deploy.py import       # tools, variables, credentials, 9 flows; writes FLOWISE_SCI_* to .env
```

Open:
- **Swagger:** http://localhost:8100/docs. Authorize with a user key from `.env` (`SCI_PLANNER_KEY`, `SCI_WAREHOUSE_KEY`, …).
- **Flowise:** http://localhost:3000. Use the `SCInsight-Cosmetics-*` flows, category "SupplyChain Insight AI".

Ask the supervisor (Flowise chat on `SCInsight-Cosmetics-Supervisor-Agentflow-v1`, or the prediction API with `FLOWISE_SCI_API_KEY`):

```bash
curl -s -X POST http://localhost:3000/api/v1/prediction/$FLOWISE_SCI_SUPERVISOR_ID \
  -H "Authorization: Bearer $FLOWISE_SCI_API_KEY" -H 'Content-Type: application/json' \
  -d '{"question":"Can we produce production order PRD-1001 on time?"}'
```

More questions are in [DEMO_SCENARIOS.md](DEMO_SCENARIOS.md).

## Non-negotiable rules, and how they are enforced

| Rule | Enforcement (code, not prompt) |
|---|---|
| The LLM never invents numbers | Calculations run in `backend/scinsight/business.py` and `service.py` and are stored with a `CALC-…` id. The agentflow evidence gate and the chatflow post-processing gate withhold any answer containing a number that is not in the calculation or policy evidence. Recommendations copy quantities from the stored calculation on the server side. |
| Tenant and roles are server-side | The API key is mapped to a user via its SHA-256 hash, then to tenant and roles (`users`, `role_assignments`). A mismatching `X-Tenant` header gets 403 and is audited. |
| SAP is read-only | `SAP_WRITE_ENABLED=true` stops the service from starting. Any POST/PUT/PATCH/DELETE on `/api/v1/sap/*` gets 405 and is audited. The supervisor refuses SAP-write requests through a deterministic guard. |
| Human Input is not the security authority | Flowise "Proceed" only reads the review status back from the API. Only a human key with the domain role can review; the Flowise agent key gets 403. |
| Approval is not proof | Outcomes are reconciled against SAP goods receipts (`/outcomes/reconcile`). Only verified outcomes feed metrics and training data. |
| Manual model promotion | Training produces a *candidate*. Only the supply-chain director can promote it, and only when it beats the best baseline on the holdout. |
| No secrets in prompts or exports | Keys live in Flowise Variables (`sci_agent_key`) and credentials. The exports contain placeholders only (`__QWEN_CREDENTIAL__`, `__TOOL:…__`, `__FLOW:…__`). |
| Tool allowlist | Each Custom Tool and Custom Function calls one fixed path on `$vars.sci_api_url` and validates its arguments before sending. Flowise's SSRF deny list blocks every other private range. |

## Documents

- [ARCHITECTURE.md](ARCHITECTURE.md): components, data flow, data stores
- [FLOWISE_CHATFLOW.md](FLOWISE_CHATFLOW.md) and [FLOWISE_AGENTFLOWS.md](FLOWISE_AGENTFLOWS.md): the flows node by node
- [AGENT_TOOL_PERMISSIONS.md](AGENT_TOOL_PERMISSIONS.md): which agent and role may call what
- [FASTAPI_CONTRACTS.md](FASTAPI_CONTRACTS.md): endpoints, payloads, errors
- [SAP_SYNTHETIC_DATA.md](SAP_SYNTHETIC_DATA.md): the fixture company and the three scenarios
- [HUMAN_APPROVAL.md](HUMAN_APPROVAL.md) and [OUTCOME_LEARNING.md](OUTCOME_LEARNING.md): the governance loop
- [FLOWISE_IMPORT_GUIDE.md](FLOWISE_IMPORT_GUIDE.md): import into any Flowise, including a clean instance
- [DEMO_SCENARIOS.md](DEMO_SCENARIOS.md) and [TEST_RESULTS.md](TEST_RESULTS.md)
