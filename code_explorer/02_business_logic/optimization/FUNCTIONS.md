# Topic index: optimization (generated)

No code copies here: the functions below live in their home module (one annotated copy per real module).

| ID | Function | Original file | Annotated copy | Summary |
|---|---|---|---|---|
| F0198 | `SupplyChainEngine.stock_balance` | backend/app/engine.py | [annotated](../../02_business_logic/aurelia_engine/app_engine.py) |  |
| F0291 | `optimize_transfers` | backend/app/optimizer.py | [annotated](../../02_business_logic/optimization/app_optimizer.py) |  |
| F0305 | `generate_transfer_candidates` | backend/scinsight/business.py | [annotated](../../02_business_logic/scinsight_rules/scinsight_business.py) | Donor warehouses with surplus = transferable stock above their own target cover  |
| F0306 | `evaluate_transfer_feasibility` | backend/scinsight/business.py | [annotated](../../02_business_logic/scinsight_rules/scinsight_business.py) | Is the transfer possible and in time? Reasons are listed; costs come only from t |
| F0307 | `compare_supply_options` | backend/scinsight/business.py | [annotated](../../02_business_logic/scinsight_rules/scinsight_business.py) | Rank options: feasible and in time first, then full coverage, then lowest cost,  |
| F0327 | `Service.warehouse_balancing` | backend/scinsight/service.py | [annotated](../../02_business_logic/scinsight_use_cases/scinsight_service.py) |  |
