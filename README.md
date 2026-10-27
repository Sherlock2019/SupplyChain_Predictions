# SPARC — Smart Supply Chain Performer Copilot

*Smart supply chain **P**erformer — **A**I **R**esilience **C**opilot.* Demo customer: Aurelia Cosmetics (fictional).

This repository holds two systems that run side by side in the same Docker stack:

| System | What it is | Entry points |
| --- | --- | --- |
| **SupplyChain Insight AI (SCInsight)**, the current POC | Flowise chat bot + SC Agent Manager + 7 specialist agents on a governed FastAPI service: synthetic SAP, deterministic calculations, policy RAG, human approval, outcome learning | Flowise `SCInsight-Cosmetics-*` flows · Swagger http://localhost:8000/docs |
| **SPARC** (earlier copilot, described from *What* onwards) | Role dashboards, analytics engine, Flowise + LangGraph copilots for the fictional Aurelia Cosmetics | Dashboard http://localhost:8000 |

## SupplyChain Insight AI (SCInsight)

A planning assistant for a fictional cosmetics company (Belleva Cosmetics: 1 factory, warehouses A/B/C, 20 products,
10 materials, synthetic SAP data). You ask in plain language; an AI manager sends the question to the right specialist;
the specialist reads SAP data and **code calculates every number**; the AI only explains the result and cites company rules;
any proposed action waits for a **human manager's approval**; and the real outcome from SAP is later checked against the
prediction so the system learns.

**Rules enforced in code, not in prompts:** the LLM never invents numbers (every number is checked against a stored
calculation) · SAP is read-only (writes return 405; the service refuses to start with `SAP_WRITE_ENABLED=true`) · tenant
and roles come from the API key on the server · the Flowise agent can never approve: only a manager with their own key ·
approval is not proof: outcomes are verified against SAP goods receipts · models are promoted only by a director, and only
when they beat the baseline.

**Run it** — one command on your PC (WSL, Linux, macOS) or on a cloud VM (AWS EC2, …):

```bash
./start.sh            # detects PC vs cloud VM and picks what fits the RAM (<8 GB: --lite --no-llm · 8–15 GB: --lite · 16 GB+: everything)
./start.sh status     # ready? URLs   ·   ./start.sh logs   ·   ./start.sh stop
./start.sh --lite --no-llm --rebuild   # override the automatic choice (--full, --small-llm on a cloud VM, --local / --aws)
```

Advanced (what `start.sh` calls):

```bash
python3 scripts/gen-env.py --add-missing    # adds the SCI_* user keys to an existing .env (new install: python3 scripts/gen-env.py)
./start-localdemo.sh                        # whole stack; also imports the SCInsight flows into Flowise
# or only what SCInsight needs:
docker compose --profile core --profile localdb up -d postgres flowise api   # api = dashboard + SCInsight API at /scinsight
python3 flowise/scinsight/deploy.py import  # 14 tools + 9 flows, bound to your Flowise; writes FLOWISE_SCI_* to .env
```

Open Flowise at http://localhost:3000 and the SCInsight API at http://localhost:8000/docs. In Swagger, use *Authorize* with a
user key from `.env`, e.g. `SCI_WAREHOUSE_KEY`.

**The Flowise flows**

| Flow | What it is for |
| --- | --- |
| `SCInsight-Cosmetics-Chatflow-v1` | **Chat front door**: guardrail → memory → Qwen → one of two tools (*Ask the SC Agent Manager* or *company RAG search*) → every number checked → answer with sources |
| `SCInsight-Cosmetics-Supervisor-Agentflow-v1` | **SC Agent Manager**: check access → understand the request → safety guard → route to ONE specialist → save recommendation → **human approval (pause)** → show the verified decision. Use this one for the full demo |
| `…-Factory-Planning-Agentflow-v1` | Can we produce on time? BOM, usable stock, purchase orders → shortages and options |
| `…-Procurement-Agentflow-v1` | Which supplier? Real lead time from goods receipts, cost, arrival vs need |
| `…-Warehouse-Agentflow-v1` | Move stock between warehouses A/B/C? Days of cover and the best transfer |
| `…-Inventory-Optimizer-Agentflow-v1` | How long will stock last? Cover, replenishment, demand forecast |
| `…-Logistics-Agentflow-v1` | How to ship it? Lane, transit time, freight cost |
| `…-Quality-Agentflow-v1` | Which batches are usable vs expired, blocked, reserved or in inspection |
| `…-Decision-Outcome-Learning-Agentflow-v1` | Was a past recommendation right? Predicted vs actual, learning metrics |

Every canvas reads left to right in numbered steps, with a panel under each node: what it does, input, output. Each
specialist: check access → read the request → calculate with SAP data → policy search → write the answer → check every number.

**Try it** (chat with the Supervisor Agentflow):

| Ask | Expected (from the calculation) |
| --- | --- |
| *Can we produce production order PRD-1001 on time?* | No: 20,000 pumps missing; make 30,000 now; buy 20,000 from Supplier A (9-day real lead time, €8,400). Pauses for production-planner approval |
| *Warehouse B is low on SPF50 sunscreen. Should we transfer stock?* | Move 2,004 units from Warehouse C, arriving 23 Oct, €821.40 |
| *Which SPF50 batches at Warehouse C are usable?* | 4,500 of 7,500; expired, QA-blocked, reserved and in-inspection batches excluded |
| *Was the lead time prediction of REC-HIST-0001 right?* | Predicted 5 days, actually 9: +4 days, verified |
| *Create a purchase order in SAP* | Refused: SAP is read-only |

Approve a paused recommendation as the responsible manager in Swagger (`POST /api/v1/decisions/{id}/review`, authorised
with that manager's key: `SCI_PLANNER_KEY` for production (PRD-1001), `SCI_WAREHOUSE_KEY` for transfers,
`SCI_PROCUREMENT_KEY` for purchases, `SCI_QUALITY_KEY` for quality), then click *Proceed* in Flowise to see the verified decision.
More: [docs/scinsight/DEMO_SCENARIOS.md](docs/scinsight/DEMO_SCENARIOS.md).

**The same agents in LangGraph (for a Flowise-vs-LangGraph comparison).** `backend/scinsight/lg/` mirrors the chat bot,
SC Agent Manager and 7 specialists as LangGraph graphs (`scinsight_chat`, `scinsight_supervisor`, `scinsight_<specialist>` on the
LangGraph server, :8123). They use the same API, the same prompts and real `interrupt()` approval. `python3 scripts/scinsight_compare.py` runs the 40
role questions on both runtimes. Result: identical accuracy (41/43 routes, 42/43 facts, same speed), so the recommended hybrid is
Flowise for the chat front door and LangGraph for the tested agent logic. See [FLOWISE_VS_LANGGRAPH.md](docs/scinsight/FLOWISE_VS_LANGGRAPH.md),
[LANGGRAPH_MIRROR.md](docs/scinsight/LANGGRAPH_MIRROR.md) and [the per-question results](docs/scinsight/FLOWISE_VS_LANGGRAPH_RESULTS.md). Studio presets and the 5 questions per role are in
[langgraph/studio/](langgraph/studio/README.md).

**Where things are**

| Path | Contents |
| --- | --- |
| `backend/scinsight/` | SCInsight FastAPI service: synthetic SAP, business rules, decisions, learning, RAG, security, migrations |
| `backend/scinsight/lg/` | LangGraph mirror of the Flowise flows (chat, supervisor, 7 specialist subgraphs) |
| `data/scinsight/role_questions.json` | 5 most-used questions per role: Flowise conversation starters, Studio inputs, comparison test set |
| `langgraph/studio/` | Studio presets: harness YAML, ready-to-paste inputs per role (assistants created by `scripts/langgraph_assistants.py`) |
| `data/scinsight/knowledge/` | Synthetic policies, SOPs and supplier agreements for the RAG knowledge base |
| `flowise/chatflows/`, `flowise/agentflows/`, `flowise/tools/`, `flowise/prompts/` | Flowise exports (placeholders only, no keys or credential ids) |
| `flowise/scinsight/` | `build-scinsight.cjs` generates the exports from the installed Flowise; `deploy.py build / import` |
| `tests/scinsight/` | Business rules, API scenarios, security, Flowise end-to-end (opt-in, real LLM) |
| `docs/scinsight/` | [Overview](docs/scinsight/README.md) · [architecture](docs/scinsight/ARCHITECTURE.md) · [chatflow](docs/scinsight/FLOWISE_CHATFLOW.md) · [agentflows](docs/scinsight/FLOWISE_AGENTFLOWS.md) · [permissions](docs/scinsight/AGENT_TOOL_PERMISSIONS.md) · [API](docs/scinsight/FASTAPI_CONTRACTS.md) · [synthetic SAP](docs/scinsight/SAP_SYNTHETIC_DATA.md) · [approval](docs/scinsight/HUMAN_APPROVAL.md) · [learning](docs/scinsight/OUTCOME_LEARNING.md) · [import guide](docs/scinsight/FLOWISE_IMPORT_GUIDE.md) · [test results](docs/scinsight/TEST_RESULTS.md) |



**Limits (POC):** synthetic SAP data only (no live SAP connection); users are API keys, not SSO; Qwen 2.5 7B can still word
an answer wrongly when every number in it is correct, so a stronger model is a pilot prerequisite (details in
[TEST_RESULTS.md](docs/scinsight/TEST_RESULTS.md)).

---

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
| Any Linux VM, e.g. your own EC2 instance (`./start-aws.sh`) | Same Docker Compose stack, started in the background |
| AWS (primary): app VM + GPU VM (vLLM, NVIDIA L4) + RDS PostgreSQL/pgvector, behind Caddy HTTPS | Terraform ready (`infra/aws`, plan: 67 resources, ~$1.10/h). **Not deployed**: the stack was destroyed on 2026-10-20 and the account's GPU quota is 0 vCPU |
| GCP (alternative): same layout on Compute Engine + Cloud SQL | Terraform ready (`infra/gcp`). Not deployed |

**Where things are in this repository**

| Path | Contents |
| --- | --- |
| `backend/app/` | FastAPI gateway, SAP mock repository, deterministic engine, insights, dashboards, tenants, LangGraph graphs, Deep Agent, MCP server, RAG |
| `backend/scinsight/`, `flowise/scinsight/`, `docs/scinsight/` | SupplyChain Insight AI (see the section at the top) |
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
./start-localdemo.sh status     # ready? URLs  ·  ./start-localdemo.sh logs  ·  --foreground = run attached to the terminal
```

The start-up runs in the background: closing the terminal or pressing Ctrl-C only stops the progress view.

The launcher generates `.env` if needed, prepares the Qwen model, starts the containers, provisions Flowise, seeds three
recommendations into the manager review queue and prints a status table. The local demo has no login pages (Flowise and
Langfuse are signed in automatically; local password `Admin@admin1`). Walkthrough: [docs/DEMO_GUIDE.md](docs/DEMO_GUIDE.md).

**On an AWS EC2 instance (or any Linux VM with a public IP)** — runs in the background, survives SSH logout and reboots:

```bash
git clone https://github.com/Sherlock2019/SupplyChain_Predictions.git && cd SupplyChain_Predictions
./start-aws.sh                  # login pages ON, public URLs http://<public-ip>:8000 …, returns immediately
./start-aws.sh --small-llm      # Qwen2.5-3B: much faster on CPU-only instances (add --no-llm for no LLM at all)
./start-aws.sh status           # progress, health and URLs with logins  ·  ./start-aws.sh logs  ·  ./start-aws.sh stop
./start-demo.sh                 # mock-up demo: no LLM, no Grafana/Langfuse — fits a 4 GB t3.medium (= start-aws.sh --lite --no-llm)
```

Allow **your IP only** in the instance's security group on TCP 8000 (dashboard + SCInsight API / Swagger at /scinsight), 3000 (Flowise),
3002 (Grafana) and 3003 (Langfuse), plus 8123 if you use LangGraph Studio. The launcher installs what is missing (Docker + compose,
python3, git, Ollama unless `--no-llm`) and adds swap on small machines. The dashboard opens signed in on AWS (`--dashboard-login`
asks for keys). Sizes, measured: `./start-demo.sh` 4 GB RAM / 20 GB disk (t3.medium); `--small-llm` 16 GB / 30 GB (t3.xlarge);
Qwen 7B 16 GB / 40 GB, a GPU (g4dn.xlarge) for usable speed.

On EC2 use `./start-aws.sh` (login pages on, public URLs), not `./start-localdemo.sh` directly. After `git pull`, just run it again: the
launcher fingerprints the source and **rebuilds the app image automatically when the code changed**, then re-imports the Flowise flows
and the LangGraph Studio presets. If it stops with *"docker compose … did not answer"*, the machine is out of memory or Docker is
busy: it prints free memory, load and what is still running. Wait for a running build to finish (`./start-aws.sh logs`) or
`./stop-localdemo.sh && sudo systemctl restart docker`, and on small instances use `--small-llm` or `--lite`.

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

* `pytest`: 122 passed, 11 opt-in tests skipped, for SPARC and SCInsight together (engine, product brief and sales outlook,
  tenants and map, API governance, graphs incl. interrupt/resume, RAG, MCP, Postgres store + pgvector, Flowise flow
  integrity, SCInsight business rules / API / security).
* `scripts/smoke.py` against the local stack: 15/15 checks through real HTTP calls (Qwen, LangGraph Server, Flowise, MCP,
  Langfuse, Grafana). Evidence is written to `deploy-evidence/` locally and is not committed (it holds machine-specific IDs).
* `terraform validate` passes for AWS and GCP; AWS `terraform plan`: 67 resources.

## RAG Tuning Console

Dashboard **AI / RAG → RAG Tuning** (manager key) or `scripts/rag_tuning.py`: inspect the knowledge base and its metadata,
preview chunking (characters), compare approved embedding models, tune top-K / threshold / hybrid / rerank on real questions,
benchmark configurations on the versioned question set (`data/scinsight/rag_benchmark/v1.json`: Hit@K, Recall@K, Precision@K,
MRR, leakage, latency), then publish (director only) or roll back. It controls the real Company RAG Search of the chatflow:
the governed policy search (SCInsight API, versioned indexes in `rag_chunks`) and, on publish, the chatflow's Flowise RAG DB
(re-indexed and verified). Code: [backend/scinsight/rag_tuning/](backend/scinsight/rag_tuning/). Guide, metrics and the
live verification report: [docs/RAG_TUNING_GUIDE.md](docs/RAG_TUNING_GUIDE.md).

## ERP / SAP Setup

Dashboard **System → ERP / SAP Setup**: configure a customer's ERP connection (Mock SAP snapshot, SAP S/4HANA or ECC over OData),
test it with a real authorized request, discover entities, map SAP fields to SPARC data, sync into a **staged** snapshot that the
business engine must compute on, then activate it (manager only) or roll back. Activation swaps that customer's snapshot inside
FastAPI, so the engine, dashboards, Flowise tools and LangGraph tools all use it from the next call; **Validate all integrations**
proves it per component. Read-only: SAP writes stay disabled (sandbox outbox only). Secrets stay on the server.
Code: [backend/app/erp/](backend/app/erp/). Setup for Mock SAP and real SAP, API, checks, tests and limitations:
[docs/ERP_SAP_SETUP.md](docs/ERP_SAP_SETUP.md).

## Backend apps that run the POC

Three Python backend services, all from the same Docker image (`aurelia-scm-app:local`), defined in [docker-compose.yml](docker-compose.yml).
**One FastAPI app** serves both APIs: the SCInsight API is a router of it, included at `/scinsight`, and keeps its own keys,
roles, database and audit chain.

| Service | What it is | Port | Started with | Code |
| --- | --- | --- | --- | --- |
| **api** (FastAPI) | **One FastAPI app**: the **SPARC / Aurelia gateway** at the root (dashboard UI, SAP OData mock, analytics engine, agents, approvals, `/v1/embeddings` for the Flowise RAG, RAG Tuning and Backend code pages) and the **SCInsight API** routes at **`/scinsight`**: the governed backend of the current POC (synthetic SAP data, calculations, policy RAG, recommendations waiting for manager approval, outcome checks, audit), called by every Flowise SCInsight tool at `http://api:8000/scinsight` | **8000** (one Swagger: `/docs`) | the image's default `uvicorn backend.app.main:app` | [backend/app/main.py](backend/app/main.py) includes the router of [backend/scinsight/app.py](backend/scinsight/app.py) |
| **langgraph** | **LangGraph Server**: runs the LangGraph graphs listed in `langgraph.json`, including the LangGraph copies of the SCInsight Flowise flows | **8123** | `langgraph dev` | [backend/app/graphs.py](backend/app/graphs.py), [backend/scinsight/lg/](backend/scinsight/lg/) |
| **mcp** | **MCP server**: read-only SAP, analytics and RAG tools for MCP clients | **8002** | `python -m backend.app.mcp_server` | [backend/app/mcp_server.py](backend/app/mcp_server.py) |

**Templates, one per app type.** Each template is a small, runnable starter in the style of the real code: same patterns,
fewer features. Copy one to start a new service. They are not imported by the running apps; [tests/test_templates.py](tests/test_templates.py)
keeps them working. The dashboard's **System → Backend code** page pins each app's template above its real files and can
show it side by side with the file you are reading.

| App type | Template | Real code it mirrors | Shows |
| --- | --- | --- | --- |
| FastAPI app | [templates/backend/fastapi_app.py](templates/backend/fastapi_app.py) | [backend/scinsight/app.py](backend/scinsight/app.py) | factory, settings, API-key auth, reader / manager roles, Pydantic bodies, read-only SAP (405), audit |
| One FastAPI app built from routers | [templates/backend/fastapi_router.py](templates/backend/fastapi_router.py) | [backend/app/main.py](backend/app/main.py) including [backend/scinsight/app.py](backend/scinsight/app.py) `create_router` at `/scinsight` | modules as `APIRouter`s with their own auth, included under a prefix: one app, one port, one Swagger |
| LangGraph graph (LangGraph Server) | [templates/backend/langgraph_graph.py](templates/backend/langgraph_graph.py) | [backend/scinsight/lg/supervisor.py](backend/scinsight/lg/supervisor.py), [backend/app/graphs.py](backend/app/graphs.py) | typed state, deterministic steps, routing, human-approval interrupt and resume |
| MCP server | [templates/backend/mcp_server.py](templates/backend/mcp_server.py) | [backend/app/mcp_server.py](backend/app/mcp_server.py) | FastMCP read-only tools, API-key middleware, Streamable HTTP |

Each file's docstring has its run command, e.g. `uvicorn templates.backend.fastapi_app:create_app --factory --port 8200`.

**What they depend on**

| Service | Role | Port |
| --- | --- | --- |
| **flowise** (3.1.2) | Chat bot, Agentflows, Document Store; calls the SCInsight API | 3101 |
| **postgres** (pgvector, pg17) | Database for the apps, the RAG vectors and the Flowise RAG DB | 55432 (localhost only) |
| **Qwen LLM** | Local demo: runs in Ollama on the host, outside Docker; `ollama-relay` forwards it to the containers (the `ollama` / `qwen` compose services are not started in this mode) | 11434 → 11435 |
| **langfuse** + **langfuse-worker**, with **clickhouse**, **redis** and **objectstore** (SeaweedFS) behind them | Tracing of LLM and agent runs | 3103 |
| **prometheus** + **grafana** | Metrics and dashboards | 9090 / 3002 |
| **demo-edge** (Caddy) | Local proxy for the demo URLs | 3000 / 3003 (localhost only) |

How a chat question flows: Flowise chat → SC Agent Manager Agentflow → **SCInsight API (`/scinsight` on :8000)**, which reads SAP data from
Postgres and does the calculations, with Qwen explaining the result. The **gateway :8000** provides the embeddings for the
Flowise RAG DB and hosts the dashboard.

**View and edit the code of each app** in the dashboard: **System → Backend code**. One tab per app above; each file appears
under every app that imports it, and a function shows which apps a save affects. Editing is local-only and opt-in:

```bash
docker compose -f docker-compose.yml -f docker-compose.code-edit.yml --profile core up -d --no-deps api mcp langgraph
```

The apps then run the repository's `backend/` (bind mount). A manager saves one function at a time: it must compile and keep
its name; a stale save is refused; the old file goes to `backend/.data/code_backups/`. The two FastAPI apps reload by
themselves; `docker compose restart mcp langgraph` for the others. `./start-localdemo.sh` goes back to the image code
(editing off).

<!-- BACKEND_FUNCTIONS:START (generated by code_explorer/tools/build_code_explorer.py; do not edit by hand) -->
## Backend functions

**1038** Python definitions in **56** backend modules, **163** FastAPI routes. Full linked list of every function: [code_explorer/BACKEND_FUNCTIONS.md](code_explorer/BACKEND_FUNCTIONS.md) · call graph and ids: [code_explorer/FUNCTION_INDEX.md](code_explorer/FUNCTION_INDEX.md) · in the dashboard: **System → Backend code**.

### Main backend functions

The functions that carry the app, by layer (one FastAPI app on :8000: SCInsight = router at /scinsight, Gateway = SPARC / Aurelia at the root). A request goes FastAPI route -> security dependency -> use case -> business rules on SAP data -> stored, audited result; agents and RAG call the same routes.

Full source of every element below (whole FastAPI factories with their routes, whole classes): [code_explorer/MAIN_BACKEND_CODE.md](code_explorer/MAIN_BACKEND_CODE.md).

| Layer | Function | App | Role | Code | ID |
|---|---|---|---|---|---|
| FastAPI app | [`create_router`](backend/scinsight/app.py#L37) | SCInsight | SCInsight routes (APIRouter included at /scinsight): loads fixtures, RAG and security, registers the 31 governed routes | [full code](code_explorer/MAIN_BACKEND_CODE.md#f1993) | F1993 |
| FastAPI app | [`create_app`](backend/app/main.py#L85) | Gateway | The one FastAPI app (:8000): includes the SCInsight router at /scinsight; gateway middleware, SAP facade, analyses, agents, RAG, approvals, UI | [full code](code_explorer/MAIN_BACKEND_CODE.md#f0017) | F0017 |
| FastAPI app | [`create_app.request_context`](backend/app/main.py#L123) | Gateway | Middleware: correlation id, active tenant, Prometheus request metrics | [full code](code_explorer/MAIN_BACKEND_CODE.md#f0018) | F0018 |
| FastAPI app | [`create_app.value_error_handler`](backend/app/main.py#L184) | Gateway | Turns any business ValueError into HTTP 422 VALIDATION_ERROR | [full code](code_explorer/MAIN_BACKEND_CODE.md#f0024) | F0024 |
| FastAPI app | [`get_settings`](backend/app/config.py#L122) | Gateway | Gateway settings from environment / .env (cached) | [full code](code_explorer/MAIN_BACKEND_CODE.md#f0008) | F0008 |
| FastAPI app | [`SciSettings`](backend/scinsight/settings.py#L13) | SCInsight | SCInsight settings: database, user keys, RAG and SAP-write guard | [full code](code_explorer/MAIN_BACKEND_CODE.md#f0013) | F0013 |
| Security | [`create_app.principal`](backend/app/main.py#L143) | Gateway | Dependency: API key -> identity + role, tenant scope check; denials audited | [full code](code_explorer/MAIN_BACKEND_CODE.md#f0019) | F0019 |
| Security | [`create_app.reader`](backend/app/main.py#L166) | Gateway | Dependency: assistant or manager may read and analyse | [full code](code_explorer/MAIN_BACKEND_CODE.md#f0021) | F0021 |
| Security | [`create_app.manager`](backend/app/main.py#L158) | Gateway | Dependency: only a manager may decide, execute or change settings | [full code](code_explorer/MAIN_BACKEND_CODE.md#f0020) | F0020 |
| Security | [`ApiKeyAuth.authenticate`](backend/app/auth.py#L21) | Gateway | Constant-time API-key lookup -> Principal (identity, role) | [full code](code_explorer/MAIN_BACKEND_CODE.md#f0770) | F0770 |
| Security | [`create_router.principal`](backend/scinsight/app.py#L61) | SCInsight | SCInsight dependency: key -> user, tenant and roles (never taken from the request body) | [full code](code_explorer/MAIN_BACKEND_CODE.md#f1994) | F1994 |
| Security | [`Security.require`](backend/scinsight/security.py#L62) | SCInsight | Role check for an action (agent_service can never approve) | [full code](code_explorer/MAIN_BACKEND_CODE.md#f0777) | F0777 |
| Security | [`Security.audit`](backend/scinsight/security.py#L74) | SCInsight | Append-only, hash-chained audit event | [full code](code_explorer/MAIN_BACKEND_CODE.md#f0779) | F0779 |
| Security | [`Security.verify_chain`](backend/scinsight/security.py#L85) | SCInsight | Verifies the audit hash chain was not altered | [full code](code_explorer/MAIN_BACKEND_CODE.md#f0781) | F0781 |
| SAP data | [`SapRepository`](backend/app/sap.py#L31) | Gateway | Read-only SAP S/4HANA mock: validated snapshot + OData-shaped entity sets | [full code](code_explorer/MAIN_BACKEND_CODE.md#f0401) | F0401 |
| SAP data | [`SapRepository.validate_codes`](backend/app/sap.py#L86) | Gateway | Rejects unknown plant / material / supplier codes before any calculation | [full code](code_explorer/MAIN_BACKEND_CODE.md#f0409) | F0409 |
| SAP data | [`TenantRegistry.get`](backend/app/tenants.py#L68) | Gateway | Per-customer SAP, engine and dashboards (multi-tenant) | [full code](code_explorer/MAIN_BACKEND_CODE.md#f0393) | F0393 |
| SAP data | [`load`](backend/scinsight/fixtures.py#L101) | SCInsight | Loads the synthetic Belleva SAP fixtures (idempotent) | [full code](code_explorer/MAIN_BACKEND_CODE.md#f0432) | F0432 |
| SAP data | [`Database.transaction`](backend/scinsight/db.py#L92) | SCInsight | SQLite / PostgreSQL access; several statements all-or-nothing | [full code](code_explorer/MAIN_BACKEND_CODE.md#f0425) | F0425 |
| Business rules | [`SupplyChainEngine.factory_readiness`](backend/app/engine.py#L40) | Gateway | BOM material readiness for a production run (shortages, ETAs) | [full code](code_explorer/MAIN_BACKEND_CODE.md#f0197) | F0197 |
| Business rules | [`SupplyChainEngine.stock_balance`](backend/app/engine.py#L125) | Gateway | Demand forecast + transfer proposals across warehouses | [full code](code_explorer/MAIN_BACKEND_CODE.md#f0198) | F0198 |
| Business rules | [`SupplyChainEngine.supplier_scorecard`](backend/app/engine.py#L262) | Gateway | OTIF, delays, quality rejects, single-source risk per supplier | [full code](code_explorer/MAIN_BACKEND_CODE.md#f0202) | F0202 |
| Business rules | [`SupplyChainEngine.sales_order_fulfilment`](backend/app/engine.py#L363) | Gateway | Allocates stock + inbound to open sales orders by date | [full code](code_explorer/MAIN_BACKEND_CODE.md#f0206) | F0206 |
| Business rules | [`SupplyChainEngine.position_health`](backend/app/engine.py#L498) | Gateway | Coverage of every stocked position against its target | [full code](code_explorer/MAIN_BACKEND_CODE.md#f0210) | F0210 |
| Business rules | [`forecast`](backend/app/forecasting.py#L129) | Gateway | XGBoost daily demand forecast | [full code](code_explorer/MAIN_BACKEND_CODE.md#f0531) | F0531 |
| Business rules | [`optimize_transfers`](backend/app/optimizer.py#L7) | Gateway | OR-Tools warehouse rebalancing (greedy fallback) | [full code](code_explorer/MAIN_BACKEND_CODE.md#f0291) | F0291 |
| Business rules | [`calculate_usable_stock`](backend/scinsight/business.py#L48) | SCInsight | Usable stock from SAP batches with an itemised exclusion list | [full code](code_explorer/MAIN_BACKEND_CODE.md#f0297) | F0297 |
| Business rules | [`calculate_bom_requirements`](backend/scinsight/business.py#L115) | SCInsight | Material requirements from the approved BOM version | [full code](code_explorer/MAIN_BACKEND_CODE.md#f0302) | F0302 |
| Business rules | [`calculate_material_shortage`](backend/scinsight/business.py#L138) | SCInsight | Shortage after usable stock and POs arriving before the need date | [full code](code_explorer/MAIN_BACKEND_CODE.md#f0303) | F0303 |
| Business rules | [`evaluate_transfer_feasibility`](backend/scinsight/business.py#L184) | SCInsight | Can a warehouse transfer arrive in time and in quantity | [full code](code_explorer/MAIN_BACKEND_CODE.md#f0306) | F0306 |
| Business rules | [`compare_supply_options`](backend/scinsight/business.py#L206) | SCInsight | Ranks supply options: feasible, in time, coverage, cost, speed | [full code](code_explorer/MAIN_BACKEND_CODE.md#f0307) | F0307 |
| Business rules | [`estimate_supplier_lead_time`](backend/scinsight/business.py#L219) | SCInsight | Empirical supplier lead time from goods receipts | [full code](code_explorer/MAIN_BACKEND_CODE.md#f0308) | F0308 |
| Business rules | [`reconcile_actual_outcome`](backend/scinsight/business.py#L241) | SCInsight | Compares a prediction with the real SAP outcome | [full code](code_explorer/MAIN_BACKEND_CODE.md#f0310) | F0310 |
| Use cases | [`Service.material_readiness`](backend/scinsight/service.py#L160) | SCInsight | Production readiness: BOM, usable stock, shortages, supply options -> CALC id | [full code](code_explorer/MAIN_BACKEND_CODE.md#f0325) | F0325 |
| Use cases | [`Service.warehouse_balancing`](backend/scinsight/service.py#L240) | SCInsight | Warehouse transfer analysis -> CALC id | [full code](code_explorer/MAIN_BACKEND_CODE.md#f0327) | F0327 |
| Use cases | [`Service.forecast_demand`](backend/scinsight/service.py#L326) | SCInsight | Demand forecast and days of cover -> CALC id | [full code](code_explorer/MAIN_BACKEND_CODE.md#f0330) | F0330 |
| Use cases | [`Service.create_decision`](backend/scinsight/service.py#L374) | SCInsight | Turns a calculation into a recommendation (REC) waiting for approval | [full code](code_explorer/MAIN_BACKEND_CODE.md#f0333) | F0333 |
| Use cases | [`Service.review`](backend/scinsight/service.py#L423) | SCInsight | Manager approves / rejects a recommendation (never the agent) | [full code](code_explorer/MAIN_BACKEND_CODE.md#f0337) | F0337 |
| Use cases | [`Service.reconcile`](backend/scinsight/service.py#L469) | SCInsight | Verifies the outcome against SAP goods receipts after execution | [full code](code_explorer/MAIN_BACKEND_CODE.md#f0341) | F0341 |
| Use cases | [`train_lead_time_model`](backend/scinsight/learning.py#L43) | SCInsight | Trains a lead-time model; promoted only if it beats the baseline | [full code](code_explorer/MAIN_BACKEND_CODE.md#f0534) | F0534 |
| Persistence | [`Store.audit`](backend/app/store.py#L189) | Gateway | Gateway audit log (hash chained) | [full code](code_explorer/MAIN_BACKEND_CODE.md#f0358) | F0358 |
| Persistence | [`Store.submit`](backend/app/store.py#L247) | Gateway | Saves a recommendation from an analysis | [full code](code_explorer/MAIN_BACKEND_CODE.md#f0364) | F0364 |
| Persistence | [`Store.decide`](backend/app/store.py#L289) | Gateway | Records the manager's decision | [full code](code_explorer/MAIN_BACKEND_CODE.md#f0368) | F0368 |
| Persistence | [`Store.execute_recommendation`](backend/app/store.py#L324) | Gateway | Writes approved documents to the SAP sandbox outbox (never production SAP) | [full code](code_explorer/MAIN_BACKEND_CODE.md#f0375) | F0375 |
| RAG | [`KnowledgeBase.ingest_dir`](backend/scinsight/rag.py#L138) | SCInsight | SCInsight RAG ingestion: validate front matter, chunk, embed, store | [full code](code_explorer/MAIN_BACKEND_CODE.md#f0765) | F0765 |
| RAG | [`KnowledgeBase.search`](backend/scinsight/rag.py#L183) | SCInsight | Company RAG Search: active configuration, tenant / role / validity filter, citations, query log | [full code](code_explorer/MAIN_BACKEND_CODE.md#f0766) | F0766 |
| RAG tuning | [`register`](backend/scinsight/rag_tuning/api.py#L99) | SCInsight | RAG Tuning Console routes /api/v1/rag-tuning (admins; publish / rollback: director) | [full code](code_explorer/MAIN_BACKEND_CODE.md#f1819) | F1819 |
| RAG tuning | [`chunk`](backend/scinsight/rag_tuning/chunking.py#L71) | SCInsight | Section / fixed / clause splitters (characters) for previews and index builds | [full code](code_explorer/MAIN_BACKEND_CODE.md#f1851) | F1851 |
| RAG tuning | [`build_candidate_index`](backend/scinsight/rag_tuning/indexing.py#L27) | SCInsight | Builds a candidate index version next to the active one, then validates it | [full code](code_explorer/MAIN_BACKEND_CODE.md#f1892) | F1892 |
| RAG tuning | [`run_rag_benchmark`](backend/scinsight/rag_tuning/evaluation.py#L82) | SCInsight | Benchmark v1 through the live search: Hit@K, Recall@K, Precision@K, MRR, leakage, latency | [full code](code_explorer/MAIN_BACKEND_CODE.md#f1874) | F1874 |
| RAG tuning | [`publish_rag_config`](backend/scinsight/rag_tuning/publishing.py#L78) | SCInsight | Validate, sync the Flowise chatflow RAG DB, switch the active configuration | [full code](code_explorer/MAIN_BACKEND_CODE.md#f1898) | F1898 |
| RAG tuning | [`FlowiseAdapter.sync`](backend/scinsight/rag_tuning/flowise_adapter.py#L99) | SCInsight | Mirrors chunking / top-k into the chatflow RAG DB, re-indexes and verifies it | [full code](code_explorer/MAIN_BACKEND_CODE.md#f1889) | F1889 |
| RAG | [`PgVectorRag.search`](backend/app/rag.py#L204) | Gateway | Gateway RAG search on PostgreSQL + pgvector | [full code](code_explorer/MAIN_BACKEND_CODE.md#f0755) | F0755 |
| RAG | [`FastEmbedder.embed`](backend/app/rag.py#L46) | Gateway | BAAI/bge-small-en-v1.5 embeddings (also served at /v1/embeddings for Flowise) | [full code](code_explorer/MAIN_BACKEND_CODE.md#f0736) | F0736 |
| AI agents | [`chat_model`](backend/app/llm.py#L18) | Gateway | Qwen through an OpenAI-compatible endpoint (vLLM / Ollama) | [full code](code_explorer/MAIN_BACKEND_CODE.md#f0728) | F0728 |
| AI agents | [`get_backend`](backend/app/copilot.py#L168) | Gateway | One governed backend for every agent runtime (local engine or HTTP API) | [full code](code_explorer/MAIN_BACKEND_CODE.md#f0484) | F0484 |
| AI agents | [`GraphRunner.run`](backend/app/runner.py#L169) | Gateway | Runs a LangGraph graph on LangGraph Server or in-process | [full code](code_explorer/MAIN_BACKEND_CODE.md#f0626) | F0626 |
| AI agents | [`GraphRunner.resume`](backend/app/runner.py#L172) | Gateway | Resumes a graph after a human-in-the-loop interrupt | [full code](code_explorer/MAIN_BACKEND_CODE.md#f0627) | F0627 |
| AI agents | [`approval_gate`](backend/app/graphs.py#L376) | Gateway | Business graph: pauses for human approval before submitting | [full code](code_explorer/MAIN_BACKEND_CODE.md#f0601) | F0601 |
| AI agents | [`supervisor`](backend/app/agentflow.py#L132) | Gateway | LangGraph mirror of the Flowise AgentFlow: picks the role specialist | [full code](code_explorer/MAIN_BACKEND_CODE.md#f0544) | F0544 |
| AI agents | [`build_deep_agent`](backend/app/deep_agent.py#L158) | Gateway | Deep Agent supplier research with harness limits | [full code](code_explorer/MAIN_BACKEND_CODE.md#f0565) | F0565 |
| AI agents | [`build_supervisor`](backend/scinsight/lg/supervisor.py#L151) | SCInsight | LangGraph mirror of the SC Agent Manager Agentflow | [full code](code_explorer/MAIN_BACKEND_CODE.md#f0722) | F0722 |
| AI agents | [`evidence_gate`](backend/scinsight/lg/chat.py#L81) | SCInsight | Every number in an answer must come from a tool result | [full code](code_explorer/MAIN_BACKEND_CODE.md#f0635) | F0635 |
| AI agents | [`create_mcp_app`](backend/app/mcp_server.py#L117) | Gateway | Restricted MCP server exposing read-only tools | [full code](code_explorer/MAIN_BACKEND_CODE.md#f0500) | F0500 |
| Developer tools | [`CodeEditor.update`](backend/app/code_editor.py#L215) | Gateway | Backend code page: validated, backed-up edit of one function (development only) | [full code](code_explorer/MAIN_BACKEND_CODE.md#f1794) | F1794 |

### Modules

| Module | What it does | Functions | Classes | Routes | Functions list |
|---|---|---|---|---|---|
| [backend/app/agentflow.py](backend/app/agentflow.py) | LangGraph AgentFlow — the full SPARC agent workflow, mirroring the Flowise AgentFlow V2. | 14 | 2 | 0 | [list](code_explorer/BACKEND_FUNCTIONS.md#backendappagentflowpy) |
| [backend/app/auth.py](backend/app/auth.py) | API-key authentication of the SPARC / Aurelia FastAPI gateway (backend/app/main.py). Keys map to an | 3 | 2 | 0 | [list](code_explorer/BACKEND_FUNCTIONS.md#backendappauthpy) |
| [backend/app/code_editor.py](backend/app/code_editor.py) | Backend code section of the SPARC UI: browse every backend function and, on a development machine, edit one function. | 14 | 1 | 0 | [list](code_explorer/BACKEND_FUNCTIONS.md#backendappcode_editorpy) |
| [backend/app/config.py](backend/app/config.py) | configuration of the SPARC / Aurelia gateway (backend/app), read from environment variables / .env. | 7 | 1 | 0 | [list](code_explorer/BACKEND_FUNCTIONS.md#backendappconfigpy) |
| [backend/app/copilot.py](backend/app/copilot.py) | One governed backend for every agent runtime (LangGraph, Deep Agents, MCP). | 43 | 4 | 0 | [list](code_explorer/BACKEND_FUNCTIONS.md#backendappcopilotpy) |
| [backend/app/dashboards.py](backend/app/dashboards.py) | Role / task dashboards. Each persona gets KPI tiles, charts and tables computed deterministically from the snapshot. | 15 | 1 | 0 | [list](code_explorer/BACKEND_FUNCTIONS.md#backendappdashboardspy) |
| [backend/app/deep_agent.py](backend/app/deep_agent.py) | Deep Agents supplier-continuity research harness — with run-time harness settings. | 15 | 4 | 0 | [list](code_explorer/BACKEND_FUNCTIONS.md#backendappdeep_agentpy) |
| [backend/app/engine.py](backend/app/engine.py) | Deterministic business calculations. LLMs may explain these outputs but never create quantities. | 34 | 1 | 0 | [list](code_explorer/BACKEND_FUNCTIONS.md#backendappenginepy) |
| [backend/app/erp/checks.py](backend/app/erp/checks.py) | Validate All Integrations: real checks, per dependent component, of whether it works on the customer's active ERP snapshot. | 17 | 0 | 0 | [list](code_explorer/BACKEND_FUNCTIONS.md#backendapperpcheckspy) |
| [backend/app/erp/connectors.py](backend/app/erp/connectors.py) | ERP connectors behind one interface: the existing mock SAP snapshot, and SAP S/4HANA / ECC OData (V2 and V4). | 30 | 4 | 0 | [list](code_explorer/BACKEND_FUNCTIONS.md#backendapperpconnectorspy) |
| [backend/app/erp/emulator.py](backend/app/erp/emulator.py) | SAP S/4HANA OData V2 emulator — DEVELOPMENT AND TEST ONLY (never mounted when APP_ENV is staging or production). | 8 | 0 | 1 | [list](code_explorer/BACKEND_FUNCTIONS.md#backendapperpemulatorpy) |
| [backend/app/erp/mapping.py](backend/app/erp/mapping.py) | SAP entity -> SPARC snapshot mapping. | 6 | 1 | 0 | [list](code_explorer/BACKEND_FUNCTIONS.md#backendapperpmappingpy) |
| [backend/app/erp/routes.py](backend/app/erp/routes.py) | /api/v1/erp: the ERP / SAP Setup page's API. Reads for every signed-in role; changes, tests, syncs, activation and rollback | 24 | 4 | 20 | [list](code_explorer/BACKEND_FUNCTIONS.md#backendapperproutespy) |
| [backend/app/erp/service.py](backend/app/erp/service.py) | ERP connections per customer: configuration (versioned), secrets (server-side only), mappings, staged synchronization, | 36 | 3 | 0 | [list](code_explorer/BACKEND_FUNCTIONS.md#backendapperpservicepy) |
| [backend/app/forecasting.py](backend/app/forecasting.py) | Small deterministic training pipeline using XGBoost for the POC demand forecast. | 8 | 0 | 0 | [list](code_explorer/BACKEND_FUNCTIONS.md#backendappforecastingpy) |
| [backend/app/graphs.py](backend/app/graphs.py) | LangGraph Chat Graph and Business Graph (exposed to LangGraph Server / LangSmith Studio by langgraph.json). | 31 | 3 | 0 | [list](code_explorer/BACKEND_FUNCTIONS.md#backendappgraphspy) |
| [backend/app/insights.py](backend/app/insights.py) | Automatic insights in plain English and personalised watches (subscriptions). | 6 | 1 | 0 | [list](code_explorer/BACKEND_FUNCTIONS.md#backendappinsightspy) |
| [backend/app/llm.py](backend/app/llm.py) | Qwen through an OpenAI-compatible endpoint: vLLM on a cloud GPU, Ollama on a local workstation. | 3 | 0 | 0 | [list](code_explorer/BACKEND_FUNCTIONS.md#backendappllmpy) |
| [backend/app/main.py](backend/app/main.py) | the SPARC / Aurelia FastAPI gateway (port 8000): one create_app() factory registers middleware | 104 | 0 | 87 | [list](code_explorer/BACKEND_FUNCTIONS.md#backendappmainpy) |
| [backend/app/mcp_server.py](backend/app/mcp_server.py) | Restricted MCP server (Streamable HTTP) exposing read-only SAP, analytics and RAG tools. | 15 | 1 | 1 | [list](code_explorer/BACKEND_FUNCTIONS.md#backendappmcp_serverpy) |
| [backend/app/moat.py](backend/app/moat.py) | Customer Data Intelligence Flywheel: how private data, human expertise and verified outcomes become intelligence. | 5 | 1 | 0 | [list](code_explorer/BACKEND_FUNCTIONS.md#backendappmoatpy) |
| [backend/app/observability.py](backend/app/observability.py) | Langfuse tracing for LangChain/LangGraph runs and Prometheus metrics shared by all services. | 4 | 0 | 0 | [list](code_explorer/BACKEND_FUNCTIONS.md#backendappobservabilitypy) |
| [backend/app/optimizer.py](backend/app/optimizer.py) | Warehouse rebalancing with OR-Tools and deterministic constraint inputs. | 2 | 0 | 0 | [list](code_explorer/BACKEND_FUNCTIONS.md#backendappoptimizerpy) |
| [backend/app/rag.py](backend/app/rag.py) | Governed RAG: approved contracts, SOPs, quality policies, product specs and logistics policies. | 21 | 5 | 0 | [list](code_explorer/BACKEND_FUNCTIONS.md#backendappragpy) |
| [backend/app/roles.py](backend/app/roles.py) | Role-centred decision views: the product is organised around the people who make supply-chain decisions. | 34 | 1 | 0 | [list](code_explorer/BACKEND_FUNCTIONS.md#backendapprolespy) |
| [backend/app/runner.py](backend/app/runner.py) | Execute LangGraph graphs either on LangGraph Server (deployments) or in-process (tests / single binary). | 18 | 3 | 0 | [list](code_explorer/BACKEND_FUNCTIONS.md#backendapprunnerpy) |
| [backend/app/sap.py](backend/app/sap.py) | Read-only SAP S/4HANA mock: validated snapshot plus OData-shaped entity sets. | 14 | 1 | 0 | [list](code_explorer/BACKEND_FUNCTIONS.md#backendappsappy) |
| [backend/app/schemas.py](backend/app/schemas.py) | the Pydantic request models of the SPARC / Aurelia gateway (backend/app/main.py). Every JSON body is | 3 | 28 | 0 | [list](code_explorer/BACKEND_FUNCTIONS.md#backendappschemaspy) |
| [backend/app/store.py](backend/app/store.py) | Governance ledger: stored analyses, recommendation review queue, and a tamper-evident audit chain. | 43 | 3 | 0 | [list](code_explorer/BACKEND_FUNCTIONS.md#backendappstorepy) |
| [backend/app/tenants.py](backend/app/tenants.py) | Industry / customer tenants: one SAP snapshot and engine stack per customer, selected per request (X-Tenant header). | 10 | 3 | 0 | [list](code_explorer/BACKEND_FUNCTIONS.md#backendapptenantspy) |
| [backend/app/tools.py](backend/app/tools.py) | Read-only LangChain tools shared by the LangGraph Chat Graph, Business Graph and Deep Agent. | 13 | 0 | 0 | [list](code_explorer/BACKEND_FUNCTIONS.md#backendapptoolspy) |
| [backend/scinsight/app.py](backend/scinsight/app.py) | SupplyChain Insight AI — the SCInsight API routes (an APIRouter of the ONE FastAPI app, backend/app/main.py). | 35 | 0 | 31 | [list](code_explorer/BACKEND_FUNCTIONS.md#backendscinsightapppy) |
| [backend/scinsight/business.py](backend/scinsight/business.py) | Deterministic supply-chain business functions — the only place quantities, dates and costs are calculated. | 16 | 2 | 0 | [list](code_explorer/BACKEND_FUNCTIONS.md#backendscinsightbusinesspy) |
| [backend/scinsight/db.py](backend/scinsight/db.py) | Database access for SupplyChain Insight AI: PostgreSQL (deployments) or SQLite (hermetic tests), with versioned SQL migrations. | 13 | 1 | 0 | [list](code_explorer/BACKEND_FUNCTIONS.md#backendscinsightdbpy) |
| [backend/scinsight/fixtures.py](backend/scinsight/fixtures.py) | Deterministic SYNTHETIC SAP fixtures for SupplyChain Insight AI (every record is fictional and labelled synthetic). | 4 | 0 | 0 | [list](code_explorer/BACKEND_FUNCTIONS.md#backendscinsightfixturespy) |
| [backend/scinsight/learning.py](backend/scinsight/learning.py) | Governed learning: a small, reproducible supplier lead-time model with a holdout evaluation and a manual promotion gate. | 6 | 0 | 0 | [list](code_explorer/BACKEND_FUNCTIONS.md#backendscinsightlearningpy) |
| [backend/scinsight/lg/chat.py](backend/scinsight/lg/chat.py) | The SCInsight chat bot as a LangGraph graph, the same as SCInsight-Cosmetics-Chatflow-v1: | 8 | 1 | 0 | [list](code_explorer/BACKEND_FUNCTIONS.md#backendscinsightlgchatpy) |
| [backend/scinsight/lg/common.py](backend/scinsight/lg/common.py) | Shared pieces of the LangGraph mirror: SCInsight API client, Qwen model, the prompts Flowise uses, and Python ports of | 49 | 0 | 0 | [list](code_explorer/BACKEND_FUNCTIONS.md#backendscinsightlgcommonpy) |
| [backend/scinsight/lg/specialists.py](backend/scinsight/lg/specialists.py) | The 7 SCInsight specialists as LangGraph subgraphs, step for step the same as the Flowise specialist Agentflows: | 10 | 3 | 0 | [list](code_explorer/BACKEND_FUNCTIONS.md#backendscinsightlgspecialistspy) |
| [backend/scinsight/lg/supervisor.py](backend/scinsight/lg/supervisor.py) | SC Agent Manager (supervisor) as a LangGraph graph, node for node the same as SCInsight-Cosmetics-Supervisor-Agentflow-v1: | 21 | 3 | 0 | [list](code_explorer/BACKEND_FUNCTIONS.md#backendscinsightlgsupervisorpy) |
| [backend/scinsight/rag.py](backend/scinsight/rag.py) | Private RAG: Document -> Validate -> Extract -> Chunk -> Embed -> Store -> Retrieve -> Cite. | 15 | 3 | 0 | [list](code_explorer/BACKEND_FUNCTIONS.md#backendscinsightragpy) |
| [backend/scinsight/rag_tuning/api.py](backend/scinsight/rag_tuning/api.py) | FastAPI routes of the RAG Tuning Console (SCInsight API, prefix /api/v1/rag-tuning). | 31 | 7 | 23 | [list](code_explorer/BACKEND_FUNCTIONS.md#backendscinsightrag_tuningapipy) |
| [backend/scinsight/rag_tuning/chunking.py](backend/scinsight/rag_tuning/chunking.py) | Splitters for the governed documents. Sizes are characters. | 6 | 0 | 0 | [list](code_explorer/BACKEND_FUNCTIONS.md#backendscinsightrag_tuningchunkingpy) |
| [backend/scinsight/rag_tuning/config.py](backend/scinsight/rag_tuning/config.py) | The tunable RAG configuration: one validated object per configuration version. | 4 | 1 | 0 | [list](code_explorer/BACKEND_FUNCTIONS.md#backendscinsightrag_tuningconfigpy) |
| [backend/scinsight/rag_tuning/documents.py](backend/scinsight/rag_tuning/documents.py) | Knowledge-base inventory and metadata quality checks. Deficiencies are reported as found; no value is ever invented. | 5 | 0 | 0 | [list](code_explorer/BACKEND_FUNCTIONS.md#backendscinsightrag_tuningdocumentspy) |
| [backend/scinsight/rag_tuning/embeddings.py](backend/scinsight/rag_tuning/embeddings.py) | Backend-approved embedding models. The console can only pick from this list: a model id typed in the browser never | 5 | 1 | 0 | [list](code_explorer/BACKEND_FUNCTIONS.md#backendscinsightrag_tuningembeddingspy) |
| [backend/scinsight/rag_tuning/evaluation.py](backend/scinsight/rag_tuning/evaluation.py) | Benchmark of a configuration on the versioned question set, through the real KnowledgeBase.search. | 9 | 0 | 0 | [list](code_explorer/BACKEND_FUNCTIONS.md#backendscinsightrag_tuningevaluationpy) |
| [backend/scinsight/rag_tuning/flowise_adapter.py](backend/scinsight/rag_tuning/flowise_adapter.py) | Keeps the Flowise chatflow's own Company RAG DB in step with the published configuration. | 10 | 2 | 0 | [list](code_explorer/BACKEND_FUNCTIONS.md#backendscinsightrag_tuningflowise_adapterpy) |
| [backend/scinsight/rag_tuning/indexing.py](backend/scinsight/rag_tuning/indexing.py) | Candidate indexes: built next to the active index (separate index_version rows), validated, never published here. | 4 | 0 | 0 | [list](code_explorer/BACKEND_FUNCTIONS.md#backendscinsightrag_tuningindexingpy) |
| [backend/scinsight/rag_tuning/publishing.py](backend/scinsight/rag_tuning/publishing.py) | Controlled publication: validate -> sync the Flowise chatflow RAG DB -> switch the active pointer. Rollback re-activates a | 5 | 0 | 0 | [list](code_explorer/BACKEND_FUNCTIONS.md#backendscinsightrag_tuningpublishingpy) |
| [backend/scinsight/rag_tuning/registry.py](backend/scinsight/rag_tuning/registry.py) | Configuration versions, background jobs and experiment records (tables from migration 0003_rag_tuning.sql). | 15 | 1 | 0 | [list](code_explorer/BACKEND_FUNCTIONS.md#backendscinsightrag_tuningregistrypy) |
| [backend/scinsight/rag_tuning/retrieval.py](backend/scinsight/rag_tuning/retrieval.py) | Ranking stage shared by live search and the tuning console (one implementation, so a preview equals production). | 3 | 0 | 0 | [list](code_explorer/BACKEND_FUNCTIONS.md#backendscinsightrag_tuningretrievalpy) |
| [backend/scinsight/schemas.py](backend/scinsight/schemas.py) | Request models. Strict (extra fields forbidden) so malformed or injected tool arguments are rejected with 422. | 1 | 14 | 0 | [list](code_explorer/BACKEND_FUNCTIONS.md#backendscinsightschemaspy) |
| [backend/scinsight/security.py](backend/scinsight/security.py) | Authentication, tenant scoping, role checks and the tamper-evident audit chain. | 8 | 2 | 0 | [list](code_explorer/BACKEND_FUNCTIONS.md#backendscinsightsecuritypy) |
| [backend/scinsight/service.py](backend/scinsight/service.py) | Use cases of the SupplyChain Insight AI business-tool service (called by the FastAPI routes and the tests). | 32 | 1 | 0 | [list](code_explorer/BACKEND_FUNCTIONS.md#backendscinsightservicepy) |
| [backend/scinsight/settings.py](backend/scinsight/settings.py) | Runtime settings for the SupplyChain Insight AI service (environment variables; see .env.example). | 2 | 1 | 0 | [list](code_explorer/BACKEND_FUNCTIONS.md#backendscinsightsettingspy) |

### FastAPI endpoints

Access: `reader` = assistant or manager key, `manager` = manager key; SCInsight routes use their own role dependencies.

| App | Method | Path | Handler | Access | Summary |
|---|---|---|---|---|---|
| Gateway :8000 | GET | `/sap/opu/odata/sap/{path:path}` | [`odata`](backend/app/erp/emulator.py#L126) | public |  |
| Gateway :8000 | GET | `/api/v1/erp/providers` | [`providers`](backend/app/erp/routes.py#L57) | public |  |
| Gateway :8000 | GET | `/api/v1/erp/connections` | [`connections`](backend/app/erp/routes.py#L62) | public |  |
| Gateway :8000 | POST | `/api/v1/erp/connections` | [`create`](backend/app/erp/routes.py#L68) | public |  |
| Gateway :8000 | GET | `/api/v1/erp/connections/{conn_id}` | [`get`](backend/app/erp/routes.py#L74) | public |  |
| Gateway :8000 | PATCH | `/api/v1/erp/connections/{conn_id}` | [`patch`](backend/app/erp/routes.py#L79) | public |  |
| Gateway :8000 | POST | `/api/v1/erp/connections/{conn_id}/test` | [`test`](backend/app/erp/routes.py#L89) | public |  |
| Gateway :8000 | GET | `/api/v1/erp/connections/{conn_id}/health` | [`health`](backend/app/erp/routes.py#L95) | public |  |
| Gateway :8000 | GET | `/api/v1/erp/connections/{conn_id}/entities` | [`entities`](backend/app/erp/routes.py#L100) | public |  |
| Gateway :8000 | GET | `/api/v1/erp/connections/{conn_id}/mappings` | [`mappings`](backend/app/erp/routes.py#L106) | public |  |
| Gateway :8000 | PUT | `/api/v1/erp/connections/{conn_id}/mappings` | [`put_mappings`](backend/app/erp/routes.py#L111) | public |  |
| Gateway :8000 | POST | `/api/v1/erp/connections/{conn_id}/validate` | [`validate`](backend/app/erp/routes.py#L117) | public |  |
| Gateway :8000 | POST | `/api/v1/erp/connections/{conn_id}/preview` | [`preview`](backend/app/erp/routes.py#L123) | public |  |
| Gateway :8000 | POST | `/api/v1/erp/connections/{conn_id}/sync` | [`sync`](backend/app/erp/routes.py#L129) | public |  |
| Gateway :8000 | GET | `/api/v1/erp/connections/{conn_id}/sync-history` | [`sync_history`](backend/app/erp/routes.py#L137) | public |  |
| Gateway :8000 | POST | `/api/v1/erp/connections/{conn_id}/activate` | [`activate`](backend/app/erp/routes.py#L142) | public |  |
| Gateway :8000 | POST | `/api/v1/erp/connections/{conn_id}/rollback` | [`rollback`](backend/app/erp/routes.py#L153) | public |  |
| Gateway :8000 | GET | `/api/v1/erp/connections/{conn_id}/logs` | [`logs`](backend/app/erp/routes.py#L160) | public |  |
| Gateway :8000 | GET | `/api/v1/erp/activation-history` | [`activation_history`](backend/app/erp/routes.py#L165) | public |  |
| Gateway :8000 | GET | `/api/v1/erp/integration-status` | [`integration_status`](backend/app/erp/routes.py#L170) | public |  |
| Gateway :8000 | POST | `/api/v1/erp/validate-integrations` | [`validate_all`](backend/app/erp/routes.py#L175) | public |  |
| Gateway :8000 | GET | `/health` | [`health`](backend/app/main.py#L189) | public |  |
| Gateway :8000 | GET | `/ready` | [`ready`](backend/app/main.py#L193) | public |  |
| Gateway :8000 | GET | `/metrics` | [`metrics`](backend/app/main.py#L197) | public |  |
| Gateway :8000 | GET | `/api/v1/config/public` | [`public_config`](backend/app/main.py#L201) | public | Non-secret links for the dashboard header. |
| Gateway :8000 | GET | `/api/v1/demo/session` | [`demo_session`](backend/app/main.py#L231) | public | Local demo only (DEMO_AUTO_LOGIN=true): returns the demo planner and manager key |
| Gateway :8000 | GET | `/api/v1/status` | [`status`](backend/app/main.py#L243) | reader |  |
| Gateway :8000 | GET | `/api/v1/snapshot` | [`snapshot`](backend/app/main.py#L279) | reader |  |
| Gateway :8000 | GET | `/api/v1/tenants` | [`tenant_catalogue`](backend/app/main.py#L292) | public | Industries and customers for the top-bar selector (send the id back as the X-Ten |
| Gateway :8000 | GET | `/api/v1/network/map` | [`network_map`](backend/app/main.py#L297) | reader |  |
| Gateway :8000 | GET | `/sap/opu/odata/sap/ZSCM_COPILOT_SRV/$metadata` | [`sap_metadata`](backend/app/main.py#L302) | reader |  |
| Gateway :8000 | GET | `/sap/opu/odata/sap/ZSCM_COPILOT_SRV/A_SandboxDocument` | [`sap_sandbox_documents`](backend/app/main.py#L307) | reader |  |
| Gateway :8000 | GET | `/sap/opu/odata/sap/ZSCM_COPILOT_SRV/{entity}` | [`sap_odata`](backend/app/main.py#L313) | reader |  |
| Gateway :8000 | POST/PUT/PATCH/DELETE | `/sap/opu/odata/sap/{path:path}` | [`block_sap_write`](backend/app/main.py#L328) | reader |  |
| Gateway :8000 | POST | `/api/v1/analysis/factory-readiness` | [`factory_readiness`](backend/app/main.py#L336) | reader |  |
| Gateway :8000 | POST | `/api/v1/analysis/stock-balance` | [`stock_balance`](backend/app/main.py#L341) | reader |  |
| Gateway :8000 | POST | `/api/v1/analysis/forecast` | [`demand_forecast`](backend/app/main.py#L345) | reader |  |
| Gateway :8000 | POST | `/api/v1/analysis/what-if` | [`what_if`](backend/app/main.py#L349) | reader |  |
| Gateway :8000 | POST | `/api/v1/analysis/supplier-risk` | [`supplier_risk`](backend/app/main.py#L354) | reader |  |
| Gateway :8000 | POST | `/api/v1/analysis/quality` | [`quality`](backend/app/main.py#L358) | reader |  |
| Gateway :8000 | POST | `/api/v1/analysis/logistics` | [`logistics`](backend/app/main.py#L362) | reader |  |
| Gateway :8000 | POST | `/api/v1/analysis/sales-orders` | [`sales_orders`](backend/app/main.py#L366) | reader |  |
| Gateway :8000 | POST | `/api/v1/analysis/stocktake` | [`stocktake`](backend/app/main.py#L370) | reader |  |
| Gateway :8000 | GET | `/api/v1/analysis/forecast-vs-actuals` | [`forecast_vs_actuals`](backend/app/main.py#L374) | reader |  |
| Gateway :8000 | GET | `/api/v1/production/overview` | [`production_overview`](backend/app/main.py#L379) | reader |  |
| Gateway :8000 | GET | `/api/v1/products` | [`products`](backend/app/main.py#L384) | reader |  |
| Gateway :8000 | GET | `/api/v1/products/{material}` | [`product`](backend/app/main.py#L389) | reader |  |
| Gateway :8000 | GET | `/api/v1/roles` | [`role_catalogue`](backend/app/main.py#L395) | reader |  |
| Gateway :8000 | GET | `/api/v1/roles/{role}` | [`role_view`](backend/app/main.py#L400) | reader |  |
| Gateway :8000 | GET | `/api/v1/northstar` | [`north_star`](backend/app/main.py#L407) | reader |  |
| Gateway :8000 | GET | `/api/v1/learning` | [`learning`](backend/app/main.py#L412) | reader |  |
| Gateway :8000 | GET | `/api/v1/moat` | [`moat_view`](backend/app/main.py#L417) | reader | Customer data intelligence flywheel, moat evidence, consent gate and the five mo |
| Gateway :8000 | POST | `/api/v1/moat/consent` | [`moat_consent`](backend/app/main.py#L423) | manager | The customer decides whether its data may contribute to industry learning (manag |
| Gateway :8000 | POST | `/api/v1/recommendations/{recommendation_id}/outcome` | [`record_outcome`](backend/app/main.py#L431) | manager | Record the real result of an executed recommendation against an SAP document (de |
| Gateway :8000 | GET | `/api/v1/sales/outlook` | [`sales_outlook`](backend/app/main.py#L445) | reader |  |
| Gateway :8000 | GET | `/api/v1/products/{material}/brief` | [`product_brief`](backend/app/main.py#L450) | reader |  |
| Gateway :8000 | GET | `/api/v1/sites` | [`sites`](backend/app/main.py#L455) | reader |  |
| Gateway :8000 | GET | `/api/v1/sites/{code}` | [`site`](backend/app/main.py#L460) | reader |  |
| Gateway :8000 | GET | `/api/v1/dashboards` | [`dashboards_list`](backend/app/main.py#L465) | public |  |
| Gateway :8000 | GET | `/api/v1/dashboards/{persona}` | [`dashboard`](backend/app/main.py#L469) | reader |  |
| Gateway :8000 | GET | `/api/v1/insights` | [`get_insights`](backend/app/main.py#L474) | reader |  |
| Gateway :8000 | GET | `/api/v1/watches/kinds` | [`watch_kinds`](backend/app/main.py#L482) | public |  |
| Gateway :8000 | GET | `/api/v1/watches` | [`list_watches`](backend/app/main.py#L486) | reader |  |
| Gateway :8000 | POST | `/api/v1/watches` | [`create_watch`](backend/app/main.py#L490) | reader |  |
| Gateway :8000 | DELETE | `/api/v1/watches/{watch_id}` | [`delete_watch`](backend/app/main.py#L500) | reader |  |
| Gateway :8000 | POST | `/api/v1/watches/evaluate` | [`evaluate_watches`](backend/app/main.py#L506) | reader |  |
| Gateway :8000 | GET | `/api/v1/analyses/{analysis_id}` | [`get_analysis`](backend/app/main.py#L516) | reader |  |
| Gateway :8000 | GET | `/api/v1/inventory` | [`inventory`](backend/app/main.py#L524) | reader |  |
| Gateway :8000 | GET | `/api/v1/suppliers/scorecard` | [`supplier_scorecard`](backend/app/main.py#L529) | reader |  |
| Gateway :8000 | GET | `/api/v1/kpis` | [`kpis`](backend/app/main.py#L534) | reader |  |
| Gateway :8000 | POST | `/api/v1/rag/search` | [`rag_search`](backend/app/main.py#L540) | reader |  |
| Gateway :8000 | GET | `/api/v1/rag/search` | [`rag_search_get`](backend/app/main.py#L545) | reader | Same search via query parameters — used by the Flowise AgentFlow RAG step (no JS |
| Gateway :8000 | POST | `/v1/embeddings` | [`embeddings`](backend/app/main.py#L553) | public | Lets Flowise (OpenAI Embeddings Custom node) index and query with exactly the em |
| Gateway :8000 | GET | `/api/v1/rag/stats` | [`rag_stats`](backend/app/main.py#L570) | reader |  |
| Gateway :8000 | POST | `/api/v1/rag/documents` | [`rag_add`](backend/app/main.py#L575) | manager |  |
| Gateway :8000 | GET/POST/PUT | `/api/v1/rag-tuning/{path:path}` | [`rag_tuning_proxy`](backend/app/main.py#L583) | reader |  |
| Gateway :8000 | GET | `/api/v1/code/files` | [`code_files`](backend/app/main.py#L604) | reader |  |
| Gateway :8000 | GET | `/api/v1/code/file` | [`code_file`](backend/app/main.py#L610) | reader |  |
| Gateway :8000 | GET | `/api/v1/code/template` | [`code_template`](backend/app/main.py#L618) | reader |  |
| Gateway :8000 | GET | `/api/v1/code/functions` | [`code_functions`](backend/app/main.py#L626) | reader |  |
| Gateway :8000 | GET | `/api/v1/code/function` | [`code_function`](backend/app/main.py#L631) | reader |  |
| Gateway :8000 | PUT | `/api/v1/code/function` | [`code_update`](backend/app/main.py#L639) | manager |  |
| Gateway :8000 | POST | `/api/v1/chat` | [`chat`](backend/app/main.py#L660) | reader |  |
| Gateway :8000 | POST | `/api/v1/langgraph/agentflow` | [`langgraph_agentflow`](backend/app/main.py#L711) | reader |  |
| Gateway :8000 | POST | `/api/v1/langgraph/agentflow/{thread_id}/resume` | [`langgraph_agentflow_resume`](backend/app/main.py#L718) | reader |  |
| Gateway :8000 | POST | `/api/v1/workflows/business` | [`business_start`](backend/app/main.py#L724) | reader |  |
| Gateway :8000 | POST | `/api/v1/workflows/business/{thread_id}/resume` | [`business_resume`](backend/app/main.py#L731) | reader |  |
| Gateway :8000 | GET | `/api/v1/deep-agents/harness` | [`deep_harness`](backend/app/main.py#L748) | reader |  |
| Gateway :8000 | PUT | `/api/v1/deep-agents/harness` | [`set_deep_harness`](backend/app/main.py#L757) | manager |  |
| Gateway :8000 | POST | `/api/v1/deep-agents/supplier-research` | [`supplier_research`](backend/app/main.py#L780) | reader |  |
| Gateway :8000 | POST | `/api/v1/flowise/{flow}/predict` | [`flowise_predict`](backend/app/main.py#L818) | reader |  |
| Gateway :8000 | POST | `/api/v1/recommendations` | [`submit_recommendation`](backend/app/main.py#L856) | reader |  |
| Gateway :8000 | POST | `/api/v1/recommendations/from-agent` | [`submit_from_agent`](backend/app/main.py#L865) | reader |  |
| Gateway :8000 | GET | `/api/v1/recommendations` | [`recommendations`](backend/app/main.py#L880) | reader |  |
| Gateway :8000 | POST | `/api/v1/recommendations/{recommendation_id}/decision` | [`decide`](backend/app/main.py#L885) | manager |  |
| Gateway :8000 | POST | `/api/v1/recommendations/{recommendation_id}/execute` | [`execute`](backend/app/main.py#L899) | manager | 1-click execution of an ACCEPTED recommendation into the SAP sandbox (manager on |
| Gateway :8000 | GET | `/api/v1/sap/documents` | [`sap_documents`](backend/app/main.py#L926) | reader |  |
| Gateway :8000 | GET | `/api/v1/audit` | [`audit`](backend/app/main.py#L931) | manager |  |
| Gateway :8000 | GET | `/sap/inventory` | [`poc_sap_inventory`](backend/app/main.py#L940) | reader |  |
| Gateway :8000 | GET | `/sap/production-orders` | [`poc_sap_production_orders`](backend/app/main.py#L946) | reader |  |
| Gateway :8000 | POST | `/forecast/demand` | [`poc_forecast_demand`](backend/app/main.py#L952) | reader |  |
| Gateway :8000 | POST | `/forecast/supplier-lead-time` | [`poc_forecast_lead_time`](backend/app/main.py#L956) | reader |  |
| Gateway :8000 | POST | `/optimizer/material-readiness` | [`poc_material_readiness`](backend/app/main.py#L960) | reader |  |
| Gateway :8000 | POST | `/optimizer/warehouse-transfer` | [`poc_warehouse_transfer`](backend/app/main.py#L965) | reader |  |
| Gateway :8000 | POST | `/decisions` | [`poc_decisions`](backend/app/main.py#L969) | reader |  |
| Gateway :8000 | POST | `/decisions/{decision_id}/human-review` | [`poc_human_review`](backend/app/main.py#L973) | manager |  |
| Gateway :8000 | POST | `/outcomes/reconcile` | [`poc_reconcile`](backend/app/main.py#L977) | manager |  |
| Gateway :8000 | GET | `/learning/model-performance` | [`poc_model_performance`](backend/app/main.py#L1003) | reader |  |
| MCP | GET | `/health` | [`health`](backend/app/mcp_server.py#L96) | public |  |
| SCInsight /scinsight | GET | `/health` | [`health`](backend/scinsight/app.py#L73) | public |  |
| SCInsight /scinsight | GET | `/api/v1/context` | [`context`](backend/scinsight/app.py#L79) | reader |  |
| SCInsight /scinsight | POST | `/api/v1/context/validate` | [`validate_context`](backend/scinsight/app.py#L85) | reader |  |
| SCInsight /scinsight | GET | `/api/v1/sap/inventory` | [`sap_inventory`](backend/scinsight/app.py#L94) | reader |  |
| SCInsight /scinsight | GET | `/api/v1/sap/bom/{sku}` | [`sap_bom`](backend/scinsight/app.py#L99) | reader |  |
| SCInsight /scinsight | GET | `/api/v1/sap/production-orders` | [`sap_production_orders`](backend/scinsight/app.py#L103) | reader |  |
| SCInsight /scinsight | GET | `/api/v1/sap/purchase-orders` | [`sap_purchase_orders`](backend/scinsight/app.py#L107) | reader |  |
| SCInsight /scinsight | GET | `/api/v1/sap/warehouses` | [`sap_warehouses`](backend/scinsight/app.py#L112) | reader |  |
| SCInsight /scinsight | GET | `/api/v1/sap/suppliers` | [`sap_suppliers`](backend/scinsight/app.py#L116) | reader |  |
| SCInsight /scinsight | POST/PUT/PATCH/DELETE | `/api/v1/sap/{path:path}` | [`sap_write_blocked`](backend/scinsight/app.py#L120) | principal |  |
| SCInsight /scinsight | POST | `/api/v1/optimizer/material-readiness` | [`material_readiness`](backend/scinsight/app.py#L126) | reader |  |
| SCInsight /scinsight | POST | `/api/v1/optimizer/warehouse-balancing` | [`warehouse_balancing`](backend/scinsight/app.py#L130) | reader |  |
| SCInsight /scinsight | POST | `/api/v1/optimizer/replenishment` | [`replenishment`](backend/scinsight/app.py#L134) | reader |  |
| SCInsight /scinsight | POST | `/api/v1/forecast/demand` | [`forecast_demand`](backend/scinsight/app.py#L138) | reader |  |
| SCInsight /scinsight | POST | `/api/v1/forecast/lead-time` | [`forecast_lead_time`](backend/scinsight/app.py#L142) | reader |  |
| SCInsight /scinsight | POST | `/api/v1/quality/check-stock` | [`quality_check`](backend/scinsight/app.py#L146) | reader |  |
| SCInsight /scinsight | GET | `/api/v1/calculations/{calculation_id}` | [`calculation`](backend/scinsight/app.py#L150) | reader |  |
| SCInsight /scinsight | POST | `/api/v1/rag/search` | [`rag_search`](backend/scinsight/app.py#L155) | reader |  |
| SCInsight /scinsight | GET | `/api/v1/rag/documents` | [`rag_documents`](backend/scinsight/app.py#L161) | reader |  |
| SCInsight /scinsight | POST | `/api/v1/decisions` | [`create_decision`](backend/scinsight/app.py#L170) | reader |  |
| SCInsight /scinsight | GET | `/api/v1/decisions` | [`list_decisions`](backend/scinsight/app.py#L175) | reader |  |
| SCInsight /scinsight | GET | `/api/v1/decisions/{rec_id}` | [`get_decision`](backend/scinsight/app.py#L179) | reader |  |
| SCInsight /scinsight | POST | `/api/v1/decisions/{rec_id}/review` | [`review`](backend/scinsight/app.py#L183) | principal |  |
| SCInsight /scinsight | POST | `/api/v1/decisions/{rec_id}/withdraw` | [`withdraw`](backend/scinsight/app.py#L187) | reader |  |
| SCInsight /scinsight | POST | `/api/v1/decisions/{rec_id}/sap-execution` | [`sap_execution`](backend/scinsight/app.py#L191) | principal |  |
| SCInsight /scinsight | POST | `/api/v1/outcomes/reconcile` | [`reconcile`](backend/scinsight/app.py#L196) | principal |  |
| SCInsight /scinsight | GET | `/api/v1/learning/metrics` | [`learning_metrics`](backend/scinsight/app.py#L200) | reader |  |
| SCInsight /scinsight | POST | `/api/v1/learning/train-lead-time-model` | [`train`](backend/scinsight/app.py#L204) | principal |  |
| SCInsight /scinsight | POST | `/api/v1/learning/models/{model_id}/promote` | [`promote`](backend/scinsight/app.py#L211) | principal |  |
| SCInsight /scinsight | POST | `/api/v1/learning/retraining-requests` | [`retraining`](backend/scinsight/app.py#L218) | reader |  |
| SCInsight /scinsight | GET | `/api/v1/audit` | [`audit`](backend/scinsight/app.py#L224) | principal |  |
| SCInsight /scinsight | GET | `/api/v1/rag-tuning/config` | [`get_config`](backend/scinsight/rag_tuning/api.py#L124) | admin |  |
| SCInsight /scinsight | PUT | `/api/v1/rag-tuning/draft` | [`save_draft`](backend/scinsight/rag_tuning/api.py#L138) | admin |  |
| SCInsight /scinsight | GET | `/api/v1/rag-tuning/history` | [`history`](backend/scinsight/rag_tuning/api.py#L144) | admin |  |
| SCInsight /scinsight | GET | `/api/v1/rag-tuning/diff/{config_id}` | [`config_diff`](backend/scinsight/rag_tuning/api.py#L148) | admin |  |
| SCInsight /scinsight | GET | `/api/v1/rag-tuning/documents` | [`list_documents`](backend/scinsight/rag_tuning/api.py#L154) | admin |  |
| SCInsight /scinsight | POST | `/api/v1/rag-tuning/metadata/validate` | [`validate_metadata`](backend/scinsight/rag_tuning/api.py#L158) | admin |  |
| SCInsight /scinsight | GET | `/api/v1/rag-tuning/documents/{doc_id}/source` | [`document_source`](backend/scinsight/rag_tuning/api.py#L166) | admin |  |
| SCInsight /scinsight | POST | `/api/v1/rag-tuning/chunks/preview` | [`chunk_preview`](backend/scinsight/rag_tuning/api.py#L174) | admin |  |
| SCInsight /scinsight | GET | `/api/v1/rag-tuning/embedding-models` | [`embedding_models`](backend/scinsight/rag_tuning/api.py#L187) | admin |  |
| SCInsight /scinsight | POST | `/api/v1/rag-tuning/embedding-models/test` | [`test_model`](backend/scinsight/rag_tuning/api.py#L193) | admin |  |
| SCInsight /scinsight | POST | `/api/v1/rag-tuning/index/build-candidate` | [`build_candidate`](backend/scinsight/rag_tuning/api.py#L202) | admin |  |
| SCInsight /scinsight | GET | `/api/v1/rag-tuning/jobs/{job_id}` | [`get_job`](backend/scinsight/rag_tuning/api.py#L209) | admin |  |
| SCInsight /scinsight | POST | `/api/v1/rag-tuning/retrieve/preview` | [`retrieve_preview`](backend/scinsight/rag_tuning/api.py#L217) | admin | retrieve_with_config: the live search function with a stored configuration and/o |
| SCInsight /scinsight | POST | `/api/v1/rag-tuning/evaluate` | [`evaluate`](backend/scinsight/rag_tuning/api.py#L255) | admin |  |
| SCInsight /scinsight | POST | `/api/v1/rag-tuning/evaluate/grid` | [`evaluate_grid`](backend/scinsight/rag_tuning/api.py#L263) | admin | Shows the workload first; runs only when confirm=true (no silent Cartesian produ |
| SCInsight /scinsight | GET | `/api/v1/rag-tuning/experiments` | [`list_experiments`](backend/scinsight/rag_tuning/api.py#L287) | admin |  |
| SCInsight /scinsight | GET | `/api/v1/rag-tuning/experiments/compare` | [`compare`](backend/scinsight/rag_tuning/api.py#L291) | admin |  |
| SCInsight /scinsight | GET | `/api/v1/rag-tuning/experiments/{exp_id}` | [`get_experiment`](backend/scinsight/rag_tuning/api.py#L298) | admin |  |
| SCInsight /scinsight | POST | `/api/v1/rag-tuning/validate` | [`validate`](backend/scinsight/rag_tuning/api.py#L306) | admin |  |
| SCInsight /scinsight | POST | `/api/v1/rag-tuning/publish` | [`publish`](backend/scinsight/rag_tuning/api.py#L311) | admin |  |
| SCInsight /scinsight | POST | `/api/v1/rag-tuning/rollback` | [`rollback`](backend/scinsight/rag_tuning/api.py#L325) | admin |  |
| SCInsight /scinsight | GET | `/api/v1/rag-tuning/flowise` | [`flowise_status`](backend/scinsight/rag_tuning/api.py#L340) | admin |  |
| SCInsight /scinsight | GET | `/api/v1/rag-tuning/metrics` | [`metrics`](backend/scinsight/rag_tuning/api.py#L344) | admin |  |

<!-- BACKEND_FUNCTIONS:END -->

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
