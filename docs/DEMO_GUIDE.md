# Demo guide (about 25 minutes)

Use the planner key first, then the manager key. Keys are in `.env` locally or `deploy-evidence/<cloud>.env` after a cloud
deployment (`PLANNER_API_KEY`, `MANAGER_API_KEY`). Local URLs are shown; cloud URLs are `https://<service>.<ip-dashes>.sslip.io`.

`./start-localdemo.sh` runs the **no-login** local demo: every tool opens already signed in. Use `--with-login` to get the
normal login pages; the local credentials are then:

| Service | Local | No-login demo | Credentials (`--with-login` or manual sign-in) |
| --- | --- | --- | --- |
| Dashboard / API docs | http://localhost:8000 · /docs | signed in; Manager/Planner switch in the header | `PLANNER_API_KEY` / `MANAGER_API_KEY` |
| Flowise | http://localhost:3000 | signed in (auto-login proxy) | `admin@admin.com` / `Admin@admin1` (Flowise requires an e-mail and a strong password) |
| Grafana | http://localhost:3002 | anonymous admin | `admin` / `admin` |
| Langfuse | http://localhost:3003 | signed in (auto-login proxy) | `admin@admin.com` / `Admin@admin1` (Langfuse requires 8+ characters) |
| LangSmith Studio | https://smith.langchain.com/studio/?baseUrl=http://localhost:8123 | hosted by LangChain — needs your LangSmith account | — |
| MCP | http://localhost:8002/mcp | — | header `X-API-Key: MCP_CLIENT_KEY` |

Cloud deployments always keep login pages and use random passwords from Terraform.

## 0a. Designed around the people who decide (7 min)
The top bar has a **Look** switch: *Apple* or *SAP Fiori* (Horizon), each in light and dark (share `?look=sap`).

1. **Today** — the **North Star** band: reliable fulfilment (projected OTIF 83.3%), supply-chain cost (30 d), inventory
   risk; next to it the **learning KPI** (forecast error vs baseline, verified outcomes, realised impact). Below: the five
   platform KPIs — tap any tile for its definition, formula, target and SAP source — and the industry KPIs (Cosmetics:
   packaging readiness, promotion forecast accuracy *needs data*, batch expiry loss, ingredient availability).
2. **My role → Director** — four answers on one screen: *what matters* (KPIs vs target), *what is likely to go wrong*
   (Serum runs out at DC22 in 5 days; production order 10000102 will miss 27 Oct; BioActive PO likely 13 days late),
   *what it will cost* (value at risk vs the €819 transfer) and *what to do next* (Plan transfer). **Ask the Supervisor
   Agent** opens the role's own agent (LangGraph + Qwen, scoped tools, cosmetics rules).
3. Switch role: **Procurement** (on-time delivery 41%, defect rate 4.4%, PPV), **Warehouse** (stock accuracy, FEFO batches,
   *picking accuracy — needs WM data*), **AI / MLOps** (WAPE, error vs baseline, drift, verified outcomes).
4. **Approvals** — *Approve*, *Approve with changes* or *Reject* with a reason code (this is the human-expertise label).
   After **Execute in SAP (sandbox)** the card asks **Did it work?** — record the real outcome with an SAP document number;
   only then does it count as a verified outcome.
5. **Intelligence moat** — the flywheel with live counts, the five moat-strength metrics, six data moats with evidence
   ("AirlessPack Asia: SAP promises 42 d, actually 55 d"), the model comparison (customer-only vs generic vs industry vs
   cold start), the consent gate (*Allow Aurelia to contribute*) and the opportunity calculator ($225k illustrative).

## 0. The 5-minute business tour (new UI)
Every screen has one filled blue button — the recommended next step. Tinted buttons are alternatives; blue text links are optional.
The top bar holds the **industry › customer** switcher (cosmetics, e-commerce, pharmaceutical, automotive, food; synthetic demo
customers except Aurelia) and the search field (**/** or **Ctrl/⌘ K**).

1. **Today** — "4 critical and 7 warnings". The *Most urgent* card shows "Dubai has 3.5 days of perfume left" with one big
   **Rebalance stock** button. *Why?* opens the evidence (SAP data, no LLM). The rest of the feed is below; *Watch* subscribes.
2. **Products → Revitalising Serum** — Singapore runs out on 25 Oct, before the 30 Oct production lands; the best donor is
   Dubai (601 units, arrives 24 Oct, €367). Component table: RM-ACTIVE is late — expedite PO 4500001002 (BioActive, 40-day
   effective time to deliver, single source). Header action: **Plan stock transfer**.
2b. **Warehouses** — per-site dashboard with the (fictional) management contacts. **Network map** — sites, tier-1 suppliers
   (local / regional / international), tier-2 ingredient origins and delayed shipments on OpenStreetMap; side tables show
   spend within the production zone and SAP lead time vs actual. The L'Oréal card is public historical context only.
2c. **Dashboards → Product = Eau de Parfum** — the *product brief* leads: supply now (7,130 + 600 in transit + 3,000 planned),
   reserve above safety stock (5,000 units, 14 days), time to out-of-stock (8 days, Dubai, 28 Oct), and *Issues and proposed
   fixes* — each with a button (Plan transfer, Check readiness, Review supplier). Below: **current sales rates** (7-day vs 28-day
   vs forecast, trend, 28-day sparkline) and the **out-of-stock calendar** (stock-outs, below-safety dates, shipment arrivals and
   production landing; click a day for the fix). With *All products* the rates and calendar cover the whole network.
3. **Dashboards** — switch roles: *Procurement* (top suppliers by OTIF, time to deliver, rejects), *Inventory planner* (top 10
   understocked, expiry risk), *Sales order desk* (fill rate 93.4%, Changi short 380), *Stocktake control* (accuracy, explained vs
   unexplained).
4. **Sales orders** → *Submit for manager approval*; **Approvals** → *Accept* → **⚡ Execute in SAP (sandbox)** creates a stock transport
   order (STO 45009xxxxx); it appears under *SAP sandbox documents* and in the audit chain.
5. **Stocktake** — 6 counts: 3 explained by unposted movements/scrap (document numbers shown), 1 within tolerance, 1 recount.
6. Press **/** anywhere and ask "Which sales orders are at risk?" — the copilot drawer answers with the same governed tools.

## 1. Platform and governance (3 min)
1. Dashboard → sign in with the **planner** key. Overview shows KPIs, at-risk positions (DC21 perfume 3.5 days of cover, DC22 serum 5 days), the supplier scorecard (PackGlass and BioActive high risk) and the live status of every component, including the Qwen endpoint and the graph runtime (`langgraph-server`).
2. Swagger `/docs` → `POST /sap/opu/odata/sap/ZSCM_COPILOT_SRV/A_PurchaseOrderItem` returns **405**: SAP is read-only.

## 2. Use case 1 — factory material readiness (4 min)
1. Factory readiness → FR20 · FG-SERUM-50 · 6000 · 2026-10-27 → **NOT READY (50 %)**.
2. Point out: 15 kg RM-ACTIVE in quality inspection is excluded; PO 4500001002 arrives 28 Oct (one day late) → proposal *expedite 6.72 kg*; cartons short 1 160 → *source from Smurfit Luxury Pack* (approved secondary source).
3. Try FR10 · FG-PERFUME-100 · 8000 → the 1 800 blocked bottles (rejected lot QL-260014) and the unconfirmed PO 4500001006 are not counted.
4. *Submit for manager approval*.

## 3. Use case 2 — three-warehouse balancing (3 min)
1. Stock balancing → FG-PERFUME-100 → XGBoost forecast + OR-Tools: transfers DC01→DC21 and DC22→DC21; the 600 units in transit (SH-880101, delayed 2 days) are counted.
2. What-if +25 % demand shows a hypothetical scenario (not submittable).

## 4. Copilot chat — three runtimes, same governed tools (6 min)
1. Runtime **LangGraph Chat Graph**: "Can FR20 produce 6000 FG-SERUM-50 by 2026-10-27?" → Qwen calls `factory_material_readiness`; follow-up "Which component is short and by how much?" uses thread memory.
2. "Create a purchase order in SAP for 50 kg RM-ACTIVE" → refused by the guardrail node (no LLM call).
3. Runtime **Flowise Chatflow**: "Is PackGlass Europe a continuity risk? Cite the contract." → Tool Agent calls MCP `supplier_risk` / `search_governed_knowledge`.
4. Runtime **Flowise AgentFlow V2**: "Rebalance FG-PERFUME-100 across the three DCs" → supervisor routes to the balancing agent → **Human input required** → *Proceed* → the gateway selects the stored stock-balance analysis and queues it. "Delete PO 4500001006 in SAP" → protected-boundary branch.
5. Open Flowise → Agentflows → *Aurelia Supply Chain Supervisor - AgentFlow V2* to show the canvas, and Executions for the run trace.

## 4b. Flowise ⇄ LangGraph side by side (4 min)
1. Overview → *Agent backends*: open the Flowise Chatflow and AgentFlow V2 canvases (Flowise login) and LangSmith Studio on the LangGraph Server (`supply_chain_chat`, `supply_chain_agentflow`).
2. Tab **Flowise ⇄ LangGraph** → pairing *Agent flows* → "Can FR20 produce 6000 FG-SERUM-50 by 2026-10-27?". Both supervisors route to their factory specialist, call the same governed tool, and pause for planner approval (Flowise Human Input / LangGraph `interrupt()`). Approve on both → two recommendations appear in Approvals (sources `flowise` and `langgraph`).
3. "Delete purchase order 4500001006 in SAP" → both runtimes take their protected-boundary branch.
4. Switch pairing to *Chat flows* to compare the Flowise Tool Agent with the LangGraph Chat Graph.

## 5. LangGraph Business Graph with interrupt (3 min)
1. Business workflow → "Rebalance FG-SERUM-50 …" → intake (Qwen structured output) → validation → OR-Tools → policy RAG (SOP SC-211) → Qwen briefing → **interrupt()**.
2. *Submit to review queue* resumes the same thread on LangGraph Server.
3. LangSmith Studio (Graph mode) → `supply_chain_business` shows the graph, the thread and the interrupt; `supply_chain_chat` works in Chat mode.

## 6. Deep Agent research (3 min)
Deep Agent research → BioActive Labs → the agent calls `supplier_risk`, delegates to the contract/quality/logistics analyst subagents (`task` tool) and writes a cited report (single source, 0 % OTIF, 28-day lead time, expedite clause, Seoul Actives qualification in Q2 2027). Takes 1–2 minutes on a 7B model.

## 7. Manager decision, audit and observability (3 min)
1. Sign in with the **manager** key → Approvals → accept/reject with a comment. The response states `sap_written: false`.
2. Audit chain → `hash chain valid`; events show analyses, denials, agent runs, submissions (sources api/dashboard/flowise/langgraph) and decisions.
3. Grafana → *SPARC — Smart Supply Chain Performer Copilot*; Langfuse → Tracing shows LangGraph nodes, tool calls and Qwen generations with token counts.
4. Optional: in RAG search ask about PackGlass — the supplier e-mail with "SYSTEM OVERRIDE …" is retrieved as data and never followed.

## Reset
`docker compose ... down -v` removes local data; `make up && make flowise` recreates everything.
