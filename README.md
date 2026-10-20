# SPARC — Smart Supply Chain Performer Copilot

*Smart supply chain **P**erformer — **A**I **R**esilience **C**opilot.* Demo customer: Aurelia Cosmetics (fictional).

## What

SPARC is an SAP-first supply-chain copilot. It reads SAP data (stock, sales orders, purchase orders, production orders,
quality lots, shipments), predicts where and when products will run out, and proposes concrete fixes — a stock transfer,
an expedited purchase order, an extra production run, a different supplier — that a planner submits and a manager approves.

It implements the two governed pilot use cases from the Scope of Work — **factory material readiness** and
**three-warehouse stock balancing** — plus supplier risk, quality, logistics, sales-order and stocktake workflows, and
exposes them through five agent runtimes (Flowise Chatflow, Flowise AgentFlow V2, LangGraph Chat Graph, LangGraph
AgentFlow, LangGraph Business Graph + Deep Agents) that all share one governed, read-only tool layer.

## Why

Supply-chain teams usually find a stock-out when it has already happened: the data needed to see it coming is spread
across SAP transactions, spreadsheets and e-mails, and nobody has time to join it every morning. Generic AI chat is not
the answer on its own — language models are unreliable at arithmetic and must never write to SAP unchecked.

SPARC keeps the split strict: **Python calculates every quantity** (XGBoost forecast, OR-Tools optimisation, MRP-style
netting), **language models only route, retrieve and explain**, SAP stays **read-only**, and every decision is approved
by a person and recorded in a tamper-evident audit chain.

## So what

What a user gets on day one — the product is designed around the people who make supply-chain decisions, not around the
AI agents:

* **My role** — one screen per role (Supply Chain Director, Demand Planner, Production Planner, Procurement Manager,
  Warehouse Manager; then Logistics, Quality, Finance and AI/MLOps) answering four questions: **what matters** (KPIs with
  agreed definitions, formulas, targets and SAP sources), **what is likely to go wrong** (dated predictions with their
  basis), **what it will cost** (value at risk vs cost of the fixes) and **what to do next** (actions with buttons) — plus
  the role's own specialised agent (e.g. *Procurement Agent*) with scoped tools and industry rules.
* **North Star** — *maximise reliable customer fulfilment at the lowest sustainable supply-chain cost and inventory risk*,
  next to the learning KPI (*improve verified outcomes over time vs the business baseline*) and the five platform KPIs
  (OTIF, material readiness, inventory turnover, forecast WAPE, supply-chain cost) plus industry-specific KPIs.
* **Intelligence moat** — the customer data intelligence flywheel (data → prediction → human decision → verified outcome →
  validated labels), the six data moats with live evidence, the five moat-strength metrics, a consent / privacy gate for
  industry learning, a customer-only vs generic vs industry vs cold-start model comparison and an opportunity calculator.
* **Today** — the single most urgent issue with one button to fix it (e.g. *"Dubai runs out of Eau de Parfum in 8 days →
  transfer 1,170 units from Paris, arrives 23 Oct, €819"*), followed by every other open insight with its evidence.
* **Product brief** — supply now, reserve above safety stock, time to out-of-stock, and every issue paired with a proposed fix.
* **Current sales rates and an out-of-stock calendar** — units per day (7 d, 28 d, forecast, trend) and the dates each
  warehouse drops below safety stock or runs out, next to the shipments and production that should prevent it.
* **Role dashboards, Warehouses, Network map** — top-10 views per role, site dashboards with management contacts, and a
  map of supplier tiers (local / regional / international) with "SAP promise vs actual delivery" lead times.
* **Approvals with 1-click execution** into an SAP sandbox outbox — never a production SAP system — fully audited.

Business value: earlier warning (days to weeks instead of after the fact), fewer emergency shipments, and decisions that
can be explained line by line because every number traces back to SAP data.

## For who

| Role | Uses SPARC to |
| --- | --- |
| Supply-chain manager | See the riskiest products and sites, accept or reject proposals, execute them in the SAP sandbox |
| Inventory planner | Rebalance stock between warehouses before a stock-out; watch days of cover |
| Sales order desk | Find orders that will be short and the transfer or partial delivery that saves them |
| Production planner | Check whether a production order has all components on time; add production when demand exceeds the plan |
| Procurement / supplier manager | Spot late or high-risk suppliers, expedite POs, compare alternative sources on time and landed cost |
| Warehouse & stocktake control | Explain count differences (unposted movements, scrap) and decide recounts |
| Logistics control tower | Track delayed shipments and their impact on stock |
| Engineers / evaluators | Compare Flowise and LangGraph side by side on the same governed tools, inspect traces in Langfuse |

## Where

**Where it runs**

| Environment | Status |
| --- | --- |
| Workstation (Docker Compose, Qwen via Ollama) | Running and verified — see *How* |
| AWS (primary): app VM + GPU VM (vLLM, NVIDIA L4) + RDS PostgreSQL/pgvector, behind Caddy HTTPS | Terraform ready (`infra/aws`, plan: 67 resources, ~$1.10/h). **Not deployed** — the account's GPU quota is 0 vCPU |
| GCP (alternative): same layout on Compute Engine + Cloud SQL | Terraform ready (`infra/gcp`). Not deployed |

**Where things are in this repository**

| Path | Contents |
| --- | --- |
| `backend/app/` | FastAPI gateway, SAP mock repository, deterministic engine, insights, dashboards, tenants, LangGraph graphs, Deep Agent, MCP server, RAG |
| `frontend/` | The web app (vanilla JS, no build step): `index.html`, `app.js`, `charts.js`, `styles.css` |
| `flowise/` | Headless Flowise provisioning and the generated Chatflow / AgentFlow V2 — see [flowise/README.md](flowise/README.md) |
| `data/` | SAP snapshot for Aurelia (`sap_mock.json`) and synthetic customers per industry (`tenants/`) |
| `infra/aws`, `infra/gcp` | Terraform for both clouds |
| `scripts/` | Smoke tests, cloud preflight, deploy, cost estimate, tenant generator |
| `docs/` | [Architecture and controls](docs/ARCHITECTURE.md) · [demo guide](docs/DEMO_GUIDE.md) · [cloud costs](docs/CLOUD_COSTS.md) · [feature comparison](docs/FEATURE_COMPARISON.md) |
| `tests/` | pytest suite |

**Where to find each answer**

| Screen | What it answers | API |
| --- | --- | --- |
| My role | What matters, what will go wrong, what it costs, what to do next — for one role, with its agent | `GET /api/v1/roles`, `GET /api/v1/roles/{role}?material=` |
| North Star | Business North Star, learning KPI, five platform KPIs, industry KPIs | `GET /api/v1/northstar` |
| Intelligence moat | Flywheel, six data moats, five moat metrics, consent gate, model comparison, value | `GET /api/v1/moat`, `POST /api/v1/moat/consent` |
| Decision outcome learning | Approve / modify / reject with a reason; record the real outcome against an SAP document | `POST /api/v1/recommendations/{id}/decision`, `POST /api/v1/recommendations/{id}/outcome`, `GET /api/v1/learning` |
| Today | What is most urgent right now, and the one-click fix | `GET /api/v1/insights` |
| Dashboards | Role KPIs and top-10 charts; with a product picked, the product brief leads | `GET /api/v1/dashboards/{persona}?material=` |
| Product brief | Supply now, reserve, time to out-of-stock, every issue paired with a proposed fix | `GET /api/v1/products/{material}/brief` |
| Sales rates + calendar | Units/day (7 d, 28 d, forecast, trend) and predicted stock-out / below-safety dates vs arrivals | `GET /api/v1/sales/outlook?material=` |
| Products | Full analysis: projections, MRP-style component netting, supply options | `GET /api/v1/products/{material}` |
| Warehouses | Site dashboard with (fictional) management contacts | `GET /api/v1/sites/{code}` |
| Network map | Supplier tiers, ingredient origins, flows, promise vs reality | `GET /api/v1/network/map` |
| Industry › customer | Switch tenant (cosmetics, e-commerce, pharma, automotive, food) | `GET /api/v1/tenants`, header `X-Tenant` |

## How

**Run the local demo in one command**

```bash
./start-localdemo.sh            # full demo (Qwen via Ollama, Flowise, LangGraph, MCP, Grafana, Langfuse); prints URLs + logins
./start-localdemo.sh --lite     # skip Grafana/Langfuse (less RAM)
./start-localdemo.sh --no-llm   # no GPU/Ollama: deterministic fallback
./start-localdemo.sh --open     # also open the dashboard in the browser
./stop-localdemo.sh [--reset]   # stop (and optionally wipe demo data)
```

The launcher generates `.env` if needed, prepares the Qwen model, starts the containers, provisions Flowise, seeds three
recommendations into the manager review queue and prints a status table. The local demo has no login pages (Flowise and
Langfuse are signed in automatically; local password `Admin@admin1`). Walkthrough: [docs/DEMO_GUIDE.md](docs/DEMO_GUIDE.md).

**Or step by step** — prerequisites: Docker, Python 3.12, an NVIDIA GPU with Ollama (or set `LLM_MODE=deterministic`).

```bash
make install                 # .venv with dev tools
make env                     # .env with random secrets
make qwen-local              # ollama pull qwen2.5:7b + 16k-context variant
make up                      # FastAPI, MCP, LangGraph Server, Flowise, Postgres, Prometheus, Grafana, Langfuse
make flowise                 # provision Flowise account, API key, variables, Chatflow + AgentFlow V2
make test                    # unit tests
make smoke                   # 15 end-to-end checks through real HTTP calls
```

Open http://localhost:8000 and sign in with `PLANNER_API_KEY` (or `MANAGER_API_KEY`) from `.env`.

**How it is built**

| Capability | Implementation |
| --- | --- |
| Frontend | Calm UI with one primary call to action per screen; two looks switchable in the top bar — **Apple** and **SAP Fiori (Horizon)** (`?look=sap`) — each in light and dark; copilot drawer on every page |
| Roles & learning | `roles.py` (9 roles, KPI catalogue with definitions/formulas/targets/sources, predictions, € impact, actions, agents), `moat.py` (flywheel, consent gate, pooled industry models), outcome + decision-feedback ledger |
| FastAPI gateway | Typed APIs, Swagger, API-key roles, correlation IDs, Prometheus metrics, review queue, SHA-256 audit chain, Flowise proxy, LangGraph runner, `X-Tenant` customer selection |
| SAP S/4HANA mock | OData-shaped MM/PP/QM/SD/PUR/WM/LE entity sets + `$metadata`; write verbs → 405 |
| Analytics | XGBoost demand forecast · OR-Tools (GLOP) transfer optimisation · MRP-style component netting · supplier scorecard · QM impact |
| Insights & watches | Deterministic insights (stock-outs, late orders, production, suppliers, shipments, count differences) and per-user subscriptions |
| Flowise Chatflow | Tool Agent + Qwen (ChatOpenAI-Custom) + memory + Custom MCP tool |
| Flowise AgentFlow V2 | Condition-Agent supervisor → 3 specialist Agents (scoped MCP tools) → Human Input → governed hand-off; SAP-write boundary branch |
| LangGraph Chat Graph | `MessagesState`, guardrail node, Qwen tool-calling loop, deterministic fallback; Studio Chat mode |
| LangGraph AgentFlow | Qwen supervisor → factory / balancing / research specialists → `interrupt()` planner approval → review queue; SAP boundary |
| LangGraph Business Graph | intake → validate → 6 workflows → policy RAG → narrative → `interrupt()` → review queue; Studio Graph mode |
| Deep Agents | Supplier research with planning, virtual FS and contract / quality / logistics subagents |
| Flowise ⇄ LangGraph | One prompt sent to both runtimes side by side (chat pair or agent-flow pair), with approvals on both |
| Qwen | Qwen2.5-7B-Instruct via OpenAI-compatible API: vLLM on an NVIDIA L4 (cloud) · Ollama (workstation) |
| MCP | Streamable-HTTP server, 10 read-only tools, API-key protected |
| RAG | fastembed `BAAI/bge-small-en-v1.5` → pgvector (HNSW), 11 governed documents / 41 chunks |
| Databases | PostgreSQL 17 + pgvector (Compose / Amazon RDS / Cloud SQL): governance ledger, RAG, LangGraph checkpoints, Flowise, Langfuse |
| Observability | Prometheus + Grafana dashboard · Langfuse v4 traces · CloudWatch Logs / Cloud Logging · EC2 alarms · budgets |
| Cloud | Terraform for AWS (primary) and GCP (alternative), Caddy HTTPS on `*.<ip>.sslip.io`, no SSH port (AWS SSM / GCP IAP), GitLab CI/CD with a manual cost gate |

**Deploy to the cloud** (after the cost approval gate)

```bash
scripts/cloud-preflight.sh aws us-east-1     # identity, offerings, GPU quota, tfvars with your IP, terraform plan -> aws.tfplan
python3 scripts/aws-cost-estimate.py         # live AWS list prices for the plan
# ---- approval gate: review docs/CLOUD_COSTS.md and the plan ----
scripts/deploy-aws.sh v1                     # apply plan, push image to ECR, upload bundle to S3, wait for bootstrap, cloud smoke tests
terraform -chdir=infra/aws destroy           # teardown
```

GCP: `scripts/cloud-preflight.sh gcp <project-id>` then `scripts/deploy-gcp.sh v1` (requires `gcloud auth login` and
`gcloud auth application-default login`).

**How it is verified**

* `pytest`: 65 passed, 2 opt-in integration tests skipped (engine, product brief and sales outlook, tenants and map, API
  governance, graphs incl. interrupt/resume, RAG, MCP, Postgres store + pgvector, Flowise flow integrity).
* `scripts/smoke.py` against the local stack: 15/15 checks through real HTTP calls (Qwen, LangGraph Server, Flowise, MCP,
  Langfuse, Grafana). Evidence is written to `deploy-evidence/` locally and is not committed (it holds machine-specific IDs).
* `terraform validate` passes for AWS and GCP; AWS `terraform plan`: 67 resources.

## What next

1. **Cloud deployment** — the AWS GPU quota request (G-family, 4 vCPU) was closed without an increase. Options: reopen the
   case in AWS Support Center, deploy a CPU-only variant (smaller model, slower answers), or use the GCP Terraform with an
   L4 GPU. Every option needs a fresh cost approval before anything is provisioned.
2. **Real data** — replace the synthetic sales history and demo customers with approved SAP extracts (billing history,
   deployment plans), then re-validate forecast accuracy.
3. **Multi-tenant agents** — dashboards, maps and analytics follow the selected customer; the AI agents, MCP tools and RAG
   knowledge base are still connected to the Aurelia tenant only.
4. **Production SAP integration** — today execution writes to a sandbox outbox; a real integration needs the client's SAP
   interfaces, authorisations and change control.
5. **Pilot** — run with one planning team for two to four weeks and measure stock-outs avoided, emergency freight and
   time saved per decision.

All names, people and contacts in the demo data are fictional; real company figures appear only on the network map's
reference card, labelled as historical public data.
