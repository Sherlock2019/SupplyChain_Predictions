# SPARC — Smart Supply Chain Performer Copilot

*Smart supply chain **P**erformer — **A**I **R**esilience **C**opilot.* Demo customer: Aurelia Cosmetics (fictional).

This repository holds two systems that run side by side in the same Docker stack:

| System | What it is | Entry points |
| --- | --- | --- |
| **SupplyChain Insight AI (SCInsight)**, the current POC | Flowise chat bot + SC Agent Manager + 7 specialist agents on a governed FastAPI service: synthetic SAP, deterministic calculations, policy RAG, human approval, outcome learning | Flowise `SCInsight-Cosmetics-*` flows · Swagger http://localhost:8100/docs |
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

**Run it**

```bash
python3 scripts/gen-env.py --add-missing    # adds the SCI_* user keys to an existing .env (new install: python3 scripts/gen-env.py)
./start-localdemo.sh                        # whole stack; also imports the SCInsight flows into Flowise
# or only what SCInsight needs:
docker compose --profile core up -d postgres flowise scinsight-api
python3 flowise/scinsight/deploy.py import  # 14 tools + 9 flows, bound to your Flowise; writes FLOWISE_SCI_* to .env
```

Open Flowise at http://localhost:3000 and the SCInsight API at http://localhost:8100/docs. In Swagger, use *Authorize* with a
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

**How it is verified**

* `pytest tests`: 122 passed, 11 skipped (9 of the skips are the opt-in Flowise end-to-end tests).
* `SCI_E2E=1 pytest tests/scinsight/test_flowise_e2e.py`: 9/9 against the stack's Flowise (real Qwen runs: scenarios, approval pause and resume, security).
* `bash scripts/scinsight-clean-flowise-test.sh`: a brand-new empty Flowise imports only the committed exports and passes the same 9 tests.
* Completeness audit of all 9 flows (wiring, branches, panels, credentials, API key) plus every route executed: 0 problems.

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

Allow **your IP only** in the instance's security group on TCP 8000 (dashboard), 3000 (Flowise), 8100 (SCInsight API / Swagger),
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
