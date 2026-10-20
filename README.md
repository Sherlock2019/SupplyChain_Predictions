# SPARC — Smart Supply Chain Performer Copilot

*Smart supply chain **P**erformer — **A**I **R**esilience **C**opilot.* Demo customer: Aurelia Cosmetics (fictional).

A cloud-deployable, SAP-first supply-chain copilot for cosmetics operations. It implements the two governed pilot use cases
from the Scope of Work — **factory material readiness** and **three-warehouse stock balancing** — plus supplier risk, quality
and logistics workflows, and exposes them through five agent runtimes that all share one governed, read-only tool layer.

**Principles:** SAP is read-only · Python calculates every quantity · LLMs route, retrieve and explain · a planner approves
submission, a manager accepts or rejects, an authorized planner executes in SAP · every step is audited.

## What is implemented

| Capability | Implementation |
| --- | --- |
| Frontend | Calm, Apple-HIG-inspired UI with one primary call to action per screen. **Today** (a *Most urgent* spotlight plus a plain-English insight feed with evidence, one-click fixes and a watchlist), **role dashboards** (manager, inventory, sales orders, stocktake, procurement, production, logistics; product filter) with **current sales rates** and an **out-of-stock calendar**, a **product brief** (supply now, reserve above safety stock, time to out-of-stock, issues → proposed fixes, top suppliers and warehouses), **Products** (stock by DC, end-of-stock projection, component resupply with order-by dates, top-5 warehouses, fastest/cheapest suppliers), **Warehouses** (site dashboard + management contacts), **Network map** (Leaflet + OpenStreetMap: supplier tiers, ingredient origins, delayed shipments), **industry › customer switcher** (synthetic multi-tenant demo data; agents/RAG stay on Aurelia), sales-order and stocktake workspaces, approvals with **1-click execution to the SAP sandbox**, watchlists, copilot drawer on every page, light/dark |
| Insights & watches | Deterministic insights (stock-outs, late orders, production, suppliers, shipments, count differences) and per-user subscriptions — see [feature comparison](docs/FEATURE_COMPARISON.md) |
| FastAPI gateway | Typed APIs, Swagger, API-key roles, correlation IDs, Prometheus metrics, review queue, SHA-256 audit chain, Flowise proxy, LangGraph runner |
| SAP S/4HANA mock | OData-shaped MM/PP/QM/SD/PUR/WM/LE entity sets + `$metadata`; write verbs → 405 |
| Flowise Chatflow | Tool Agent + Qwen (ChatOpenAI-Custom) + memory + Custom MCP tool |
| Flowise AgentFlow V2 | Condition-Agent supervisor → 3 specialist Agents (scoped MCP tools) → Human Input → governed hand-off; SAP-write boundary branch |
| LangGraph Chat Graph | `MessagesState`, guardrail node, Qwen tool-calling loop, deterministic fallback; Studio Chat mode |
| LangGraph AgentFlow | LangGraph counterpart of the Flowise AgentFlow V2: Qwen supervisor → factory / balancing / research specialist agents → `interrupt()` planner approval → review queue; SAP boundary |
| Flowise ⇄ LangGraph | Dashboard tab sending one prompt to both runtimes side by side (chat pair or agent-flow pair), with approvals on both |
| LangGraph Business Graph | intake → validate → 6 workflows → policy RAG → narrative → `interrupt()` → review queue; Studio Graph mode |
| Deep Agents | supplier research with planning, virtual FS and contract / quality / logistics subagents |
| Qwen | Qwen2.5-7B-Instruct via OpenAI-compatible API: vLLM on an NVIDIA L4 (cloud) · Ollama (workstation) |
| MCP | Streamable-HTTP server, 10 read-only tools, API-key protected |
| RAG | fastembed `BAAI/bge-small-en-v1.5` → pgvector (HNSW), 11 governed documents / 41 chunks |
| Analytics | XGBoost demand forecast · OR-Tools (GLOP) transfer optimisation · supplier scorecard · QM impact |
| Databases | PostgreSQL 17 + pgvector (Compose / Amazon RDS / Cloud SQL): governance ledger, RAG, LangGraph checkpoints, Flowise, Langfuse |
| Observability | Prometheus + Grafana dashboard · Langfuse v4 traces · CloudWatch Logs / Cloud Logging · EC2 alarms · budgets |
| Cloud | Terraform for **AWS (primary)** and **GCP (alternative)**, Caddy HTTPS, GitLab CI/CD with a manual cost gate |

Details: [architecture and controls](docs/ARCHITECTURE.md) · [demo guide](docs/DEMO_GUIDE.md) · [cloud costs](docs/CLOUD_COSTS.md) · [Flowise](flowise/README.md)

## Local demo in one command

```bash
./start-localdemo.sh            # full demo (Qwen via Ollama, Flowise, LangGraph, MCP, Grafana, Langfuse); prints URLs + logins
./start-localdemo.sh --lite     # skip Grafana/Langfuse (less RAM)
./start-localdemo.sh --no-llm   # no GPU/Ollama: deterministic fallback
./start-localdemo.sh --open     # also open the dashboard in the browser
./stop-localdemo.sh [--reset]   # stop (and optionally wipe demo data)
```

The launcher generates `.env` if needed, prepares the Qwen model, starts the containers, provisions Flowise, seeds three
recommendations into the manager review queue and prints a status table. Walkthrough: [docs/DEMO_GUIDE.md](docs/DEMO_GUIDE.md).

## Local quick start (step by step)

Prerequisites: Docker, Python 3.12, an NVIDIA GPU with Ollama (or set `LLM_MODE=deterministic`).

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

## Screens and APIs at a glance

| Screen | What it answers | API |
| --- | --- | --- |
| Today | What is most urgent right now, and the one-click fix | `GET /api/v1/insights` |
| Dashboards | Role KPIs and top-10 charts; with a product picked, the product brief leads | `GET /api/v1/dashboards/{persona}?material=` |
| Product brief | Supply now, reserve, time to out-of-stock, every issue paired with a proposed fix | `GET /api/v1/products/{material}/brief` |
| Sales rates + calendar | Units/day (7 d, 28 d, forecast, trend) and predicted stock-out / below-safety dates vs arrivals | `GET /api/v1/sales/outlook?material=` |
| Products | Full analysis: projections, MRP-style component netting, supply options | `GET /api/v1/products/{material}` |
| Warehouses | Site dashboard with (fictional) management contacts | `GET /api/v1/sites/{code}` |
| Network map | Supplier tiers, ingredient origins, flows, promise vs reality | `GET /api/v1/network/map` |
| Industry › customer | Switch tenant (cosmetics, e-commerce, pharma, automotive, food) | `GET /api/v1/tenants`, header `X-Tenant` |

All numbers and fixes come from the deterministic engine (`backend/app/engine.py`) over the SAP snapshot; no language model
computes quantities. Sales history and all non-Aurelia customers are synthetic demo data.

## Cloud deployment (AWS primary, GCP alternative)

```bash
scripts/cloud-preflight.sh aws us-east-1     # identity, offerings, GPU quota, tfvars with your IP, terraform plan -> aws.tfplan
python3 scripts/aws-cost-estimate.py         # live AWS list prices for the plan
# ---- approval gate: review docs/CLOUD_COSTS.md and the plan ----
scripts/deploy-aws.sh v1                     # apply plan, push image to ECR, upload bundle to S3, wait for bootstrap, cloud smoke tests
terraform -chdir=infra/aws destroy           # teardown
```

GCP: `scripts/cloud-preflight.sh gcp <project-id>` then `scripts/deploy-gcp.sh v1` (requires `gcloud auth login` and
`gcloud auth application-default login`).

Each deployment creates an app VM (Docker Compose stack behind Caddy with Let's Encrypt certificates on
`*.<ip-dashes>.sslip.io`), a private GPU VM running vLLM, managed PostgreSQL with pgvector, a container registry, object
storage, a secret store and log shipping. HTTPS is restricted to the operator CIDR; there is no SSH port (AWS SSM / GCP IAP).

## Verification status

* `pytest`: 65 passed, 2 opt-in integration tests skipped (engine, product brief and sales outlook, tenants and map, API
  governance, graphs incl. interrupt/resume, RAG, MCP, Postgres store + pgvector, Flowise flow integrity).
* `scripts/smoke.py` against the local stack: 15/15 checks through real HTTP calls (Qwen, LangGraph Server, Flowise, MCP,
  Langfuse, Grafana). Evidence is written to `deploy-evidence/` locally and is not committed (it holds machine-specific IDs).
* `terraform validate` passes for AWS and GCP; AWS `terraform plan`: 67 resources (~$1.10/h, see docs/CLOUD_COSTS.md).
* **Cloud: not deployed.** The AWS account has a 0-vCPU quota for G-family GPU instances; the quota request was closed
  without an increase. Deploy only after the quota is granted (or with a CPU-only/GCP variant) and a fresh cost approval.
