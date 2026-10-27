# 02_business_logic/aurelia_engine (generated)

Modules: `backend/app/engine.py`

| ID | Function / class | Kind | Status | Original | Annotated copy | Summary |
|---|---|---|---|---|---|---|
| F0192 | `SupplyChainEngine` | class | used | [backend/app/engine.py:14](../../../backend/app/engine.py#L14) | [annotated](../../02_business_logic/aurelia_engine/app_engine.py) |  |
| F0193 | `SupplyChainEngine.__init__` | method | used (framework) | [backend/app/engine.py:15](../../../backend/app/engine.py#L15) | [annotated](../../02_business_logic/aurelia_engine/app_engine.py) |  |
| F0194 | `SupplyChainEngine._confirmed_pos` | method | used | [backend/app/engine.py:19](../../../backend/app/engine.py#L19) | [annotated](../../02_business_logic/aurelia_engine/app_engine.py) |  |
| F0195 | `SupplyChainEngine._warehouses` | method | used | [backend/app/engine.py:26](../../../backend/app/engine.py#L26) | [annotated](../../02_business_logic/aurelia_engine/app_engine.py) |  |
| F0196 | `SupplyChainEngine._in_transit_to` | method | used | [backend/app/engine.py:29](../../../backend/app/engine.py#L29) | [annotated](../../02_business_logic/aurelia_engine/app_engine.py) |  |
| F0197 | `SupplyChainEngine.factory_readiness` | method | used | [backend/app/engine.py:40](../../../backend/app/engine.py#L40) | [annotated](../../02_business_logic/aurelia_engine/app_engine.py) |  |
| F0198 | `SupplyChainEngine.stock_balance` | method | used | [backend/app/engine.py:125](../../../backend/app/engine.py#L125) | [annotated](../../02_business_logic/aurelia_engine/app_engine.py) |  |
| F0199 | `SupplyChainEngine.demand_forecast` | method | used | [backend/app/engine.py:169](../../../backend/app/engine.py#L169) | [annotated](../../02_business_logic/aurelia_engine/app_engine.py) |  |
| F0200 | `SupplyChainEngine.what_if` | method | used | [backend/app/engine.py:180](../../../backend/app/engine.py#L180) | [annotated](../../02_business_logic/aurelia_engine/app_engine.py) |  |
| F0201 | `SupplyChainEngine.supplier_risk` | method | used | [backend/app/engine.py:206](../../../backend/app/engine.py#L206) | [annotated](../../02_business_logic/aurelia_engine/app_engine.py) |  |
| F0202 | `SupplyChainEngine.supplier_scorecard` | method | used | [backend/app/engine.py:262](../../../backend/app/engine.py#L262) | [annotated](../../02_business_logic/aurelia_engine/app_engine.py) |  |
| F0203 | `SupplyChainEngine.quality_status` | method | used | [backend/app/engine.py:270](../../../backend/app/engine.py#L270) | [annotated](../../02_business_logic/aurelia_engine/app_engine.py) |  |
| F0204 | `SupplyChainEngine.logistics_status` | method | used | [backend/app/engine.py:308](../../../backend/app/engine.py#L308) | [annotated](../../02_business_logic/aurelia_engine/app_engine.py) |  |
| F0205 | `SupplyChainEngine.inventory_overview` | method | used | [backend/app/engine.py:337](../../../backend/app/engine.py#L337) | [annotated](../../02_business_logic/aurelia_engine/app_engine.py) |  |
| F0206 | `SupplyChainEngine.sales_order_fulfilment` | method | used | [backend/app/engine.py:363](../../../backend/app/engine.py#L363) | [annotated](../../02_business_logic/aurelia_engine/app_engine.py) | Allocate warehouse stock (+ inbound arriving before each requested date) to open |
| F0207 | `SupplyChainEngine.stocktake_reconciliation` | method | used | [backend/app/engine.py:423](../../../backend/app/engine.py#L423) | [annotated](../../02_business_logic/aurelia_engine/app_engine.py) | Explain each count difference from unposted goods movements, quality decisions a |
| F0208 | `SupplyChainEngine.production_overview` | method | used | [backend/app/engine.py:471](../../../backend/app/engine.py#L471) | [annotated](../../02_business_logic/aurelia_engine/app_engine.py) |  |
| F0209 | `SupplyChainEngine.forecast_vs_actuals` | method | used | [backend/app/engine.py:480](../../../backend/app/engine.py#L480) | [annotated](../../02_business_logic/aurelia_engine/app_engine.py) |  |
| F0210 | `SupplyChainEngine.position_health` | method | used | [backend/app/engine.py:498](../../../backend/app/engine.py#L498) | [annotated](../../02_business_logic/aurelia_engine/app_engine.py) | Coverage of every stocked position against its target: finished goods at DCs (de |
| F0211 | `SupplyChainEngine.products` | method | used | [backend/app/engine.py:547](../../../backend/app/engine.py#L547) | [annotated](../../02_business_logic/aurelia_engine/app_engine.py) |  |
| F0212 | `SupplyChainEngine.product_360` | method | used | [backend/app/engine.py:556](../../../backend/app/engine.py#L556) | [annotated](../../02_business_logic/aurelia_engine/app_engine.py) | Everything about one finished good: stock by DC, sales, projected end of stock,  |
| F0213 | `SupplyChainEngine.product_brief` | method | used | [backend/app/engine.py:812](../../../backend/app/engine.py#L812) | [annotated](../../02_business_logic/aurelia_engine/app_engine.py) | One-screen product brief: supply status, reserve above safety stock, time to out |
| F0214 | `SupplyChainEngine.product_brief.add` | nested | used | [backend/app/engine.py:831](../../../backend/app/engine.py#L831) | [annotated](../../02_business_logic/aurelia_engine/app_engine.py) |  |
| F0215 | `SupplyChainEngine.product_brief.qty` | nested | used | [backend/app/engine.py:874](../../../backend/app/engine.py#L874) | [annotated](../../02_business_logic/aurelia_engine/app_engine.py) |  |
| F0216 | `SupplyChainEngine.product_brief.when` | nested | used | [backend/app/engine.py:877](../../../backend/app/engine.py#L877) | [annotated](../../02_business_logic/aurelia_engine/app_engine.py) |  |
| F0217 | `SupplyChainEngine.product_brief.by` | nested | used | [backend/app/engine.py:880](../../../backend/app/engine.py#L880) | [annotated](../../02_business_logic/aurelia_engine/app_engine.py) |  |
| F0218 | `SupplyChainEngine.product_brief.level` | nested | used | [backend/app/engine.py:941](../../../backend/app/engine.py#L941) | [annotated](../../02_business_logic/aurelia_engine/app_engine.py) |  |
| F0219 | `SupplyChainEngine.supplier_lead_time` | method | used | [backend/app/engine.py:969](../../../backend/app/engine.py#L969) | [annotated](../../02_business_logic/aurelia_engine/app_engine.py) | Empirical lead-time forecast from SAP receipt history (promised vs received date |
| F0220 | `SupplyChainEngine.sales_outlook` | method | used | [backend/app/engine.py:996](../../../backend/app/engine.py#L996) | [annotated](../../02_business_logic/aurelia_engine/app_engine.py) | Current sales rates per product and DC (last 7 / 28 days vs the 14-day forecast) |
| F0221 | `SupplyChainEngine.sites` | method | used | [backend/app/engine.py:1048](../../../backend/app/engine.py#L1048) | [annotated](../../02_business_logic/aurelia_engine/app_engine.py) |  |
| F0222 | `SupplyChainEngine.site_360` | method | used | [backend/app/engine.py:1058](../../../backend/app/engine.py#L1058) | [annotated](../../02_business_logic/aurelia_engine/app_engine.py) |  |
| F0223 | `SupplyChainEngine.supplier_tier` | method | used | [backend/app/engine.py:1122](../../../backend/app/engine.py#L1122) | [annotated](../../02_business_logic/aurelia_engine/app_engine.py) | local = same country as the plant; regional = same geographic zone; internationa |
| F0224 | `SupplyChainEngine.network_map` | method | used | [backend/app/engine.py:1129](../../../backend/app/engine.py#L1129) | [annotated](../../02_business_logic/aurelia_engine/app_engine.py) |  |
| F0225 | `SupplyChainEngine.expiry_risk` | method | used | [backend/app/engine.py:1211](../../../backend/app/engine.py#L1211) | [annotated](../../02_business_logic/aurelia_engine/app_engine.py) |  |
| F0226 | `SupplyChainEngine.kpis` | method | used | [backend/app/engine.py:1223](../../../backend/app/engine.py#L1223) | [annotated](../../02_business_logic/aurelia_engine/app_engine.py) |  |
