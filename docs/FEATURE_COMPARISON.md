# Feature comparison — Mentana AI Agent vs SPARC (Smart Supply Chain Performer Copilot)

Source: the public product page https://www.mentana.ai/products/mentana-ai-agent (read 2026-10-20). Only features stated on
that page are listed for Mentana; nothing about its internals is assumed.

| Capability (Mentana page) | Aurelia copilot | Where |
| --- | --- | --- |
| Guardrails: deterministic, auditable, explainable answers | ✅ Deterministic engine for every number; SHA-256 audit chain; every insight shows its evidence ("Why?") | Command center, `/api/v1/insights`, Approvals → audit |
| Automatic insights in plain English | ✅ Insight feed: stock-outs, overstock, late orders, production readiness, supplier risk, shipment delays, stock-count differences — severity, evidence, one-click fix, "Ask copilot" | Command center |
| Subscriptions to personalised queries | ✅ Watchlists: days of cover, supplier risk, orders at risk, count differences, shipment delay, saved copilot questions; re-checked on every visit with change detection | Watchlists, `/api/v1/watches` |
| Recommendations with ML forecasting and explanations | ✅ XGBoost forecast + back-test MAPE, OR-Tools transfers, sales-order resolutions, stocktake actions, supplier actions | all workspaces |
| 1-click execution synced to ERP, with human approval | ✅ (sandbox) Manager accepts → **Execute in SAP** creates STO / PR / PO change / inventory adjustment / recount documents in the SAP mock sandbox outbox; agents can never execute | Approvals & execution |
| Monitor dashboard with persistent context | ✅ Role dashboards + watchlists (persisted per user) + LangGraph threads persisted on LangGraph Server | My dashboard |
| Stock-out risk view, forecast vs actuals chart | ✅ Stock-out bars, days-of-cover, 60-day projected stock by DC, forecast vs actuals with back-test | Dashboards, Product 360 |
| Inventory management (rebalance, avoid stock-outs and overstock) | ✅ Balancing + what-if + best donor warehouse + overstock insights | Inventory, Product 360 |
| Sales order management | ✅ Every open order allocated by date and priority; at-risk orders get the cheapest on-time transfer or a partial-delivery proposal | Sales orders |
| Stocktake management (explain discrepancies with evidence) | ✅ Count differences explained from unposted goods movements and pending scrap; tolerance → adjustment or recount | Stocktake |

## Beyond the Mentana page

* **Product 360** — per finished good: stock by DC, sales and forecast, projected end-of-stock per DC, best donor warehouse,
  resupply needs per BOM component with order-by dates, ranked suppliers (risk, OTIF, time to deliver) and alternative sources.
* **Role dashboards** — supply-chain manager, inventory planner, sales order desk, stocktake control, procurement, production,
  logistics: top-10 understocked positions, top suppliers by reliability, time to deliver, rejects, exposure, expiry risk, fill rate.
* **Shelf-life / expiry risk** (critical for cosmetics), value at risk, carbon per transfer, inventory record accuracy.
* **Two agent runtimes** with chat and agent flows (Flowise Chatflow + AgentFlow V2, LangGraph Chat Graph + AgentFlow), Deep Agents
  research, MCP server, governed RAG over contracts/SOPs, self-hosted Qwen; copilot drawer on every page.
* **Read-only SAP by design** for agents; production SAP write-back is a configuration decision (`SAP_EXECUTION_MODE`).

## Honest gaps

* Execution writes to a **sandbox outbox** in the SAP mock, not to a real SAP system (needs SAP BAPI/OData write services and
  authorisation design).
* Sales-order *coordination with customers and teams* (notifications, e-mail/Teams) is not implemented — the copilot proposes
  resolutions; communication stays manual.
* The demo dataset is small (3 finished goods, 7 suppliers): "top 10" charts show all suppliers; a real SAP extract fills them.
