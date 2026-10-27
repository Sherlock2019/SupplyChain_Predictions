# Topic index: inventory (generated)

No code copies here: the functions below live in their home module (one annotated copy per real module).

| ID | Function | Original file | Annotated copy | Summary |
|---|---|---|---|---|
| F0237 | `Dashboards._inventory` | backend/app/dashboards.py | [annotated](../../02_business_logic/aurelia_views/app_dashboards.py) |  |
| F0205 | `SupplyChainEngine.inventory_overview` | backend/app/engine.py | [annotated](../../02_business_logic/aurelia_engine/app_engine.py) |  |
| F0210 | `SupplyChainEngine.position_health` | backend/app/engine.py | [annotated](../../02_business_logic/aurelia_engine/app_engine.py) | Coverage of every stocked position against its target: finished goods at DCs (de |
| F0225 | `SupplyChainEngine.expiry_risk` | backend/app/engine.py | [annotated](../../02_business_logic/aurelia_engine/app_engine.py) |  |
| F0263 | `RoleCenter._inventory_value` | backend/app/roles.py | [annotated](../../02_business_logic/aurelia_views/app_roles.py) |  |
| F0297 | `calculate_usable_stock` | backend/scinsight/business.py | [annotated](../../02_business_logic/scinsight_rules/scinsight_business.py) | Usable quantity from SAP batches with an itemised exclusion list. With transfer_ |
| F0298 | `average_daily_demand` | backend/scinsight/business.py | [annotated](../../02_business_logic/scinsight_rules/scinsight_business.py) | Mean units/day over the last `window_days` days (missing days count as zero dema |
| F0299 | `calculate_days_of_cover` | backend/scinsight/business.py | [annotated](../../02_business_logic/scinsight_rules/scinsight_business.py) | Days the usable stock lasts at the given demand. None when there is no demand (c |
| F0300 | `calculate_replenishment_quantity` | backend/scinsight/business.py | [annotated](../../02_business_logic/scinsight_rules/scinsight_business.py) | Quantity needed so that stock covers lead time + target cover. Zero demand -> 0. |
| F0301 | `detect_expiry_risk` | backend/scinsight/business.py | [annotated](../../02_business_logic/scinsight_rules/scinsight_business.py) | Released batches expired or expiring within the horizon, most urgent first. |
| F0319 | `Service.inventory` | backend/scinsight/service.py | [annotated](../../02_business_logic/scinsight_use_cases/scinsight_service.py) |  |
| F0328 | `Service.replenishment` | backend/scinsight/service.py | [annotated](../../02_business_logic/scinsight_use_cases/scinsight_service.py) |  |
