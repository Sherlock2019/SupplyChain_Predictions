# 02_business_logic/scinsight_use_cases (generated)

Modules: `backend/scinsight/service.py`

| ID | Function / class | Kind | Status | Original | Annotated copy | Summary |
|---|---|---|---|---|---|---|
| F0311 | `Service` | class | used | [backend/scinsight/service.py:26](../../../backend/scinsight/service.py#L26) | [annotated](../../02_business_logic/scinsight_use_cases/scinsight_service.py) |  |
| F0312 | `Service.__init__` | method | used (framework) | [backend/scinsight/service.py:27](../../../backend/scinsight/service.py#L27) | [annotated](../../02_business_logic/scinsight_use_cases/scinsight_service.py) |  |
| F0313 | `Service.snapshot` | method | used | [backend/scinsight/service.py:31](../../../backend/scinsight/service.py#L31) | [annotated](../../02_business_logic/scinsight_use_cases/scinsight_service.py) |  |
| F0314 | `Service._save_run` | method | used | [backend/scinsight/service.py:42](../../../backend/scinsight/service.py#L42) | [annotated](../../02_business_logic/scinsight_use_cases/scinsight_service.py) |  |
| F0315 | `Service.calculation` | method | used | [backend/scinsight/service.py:52](../../../backend/scinsight/service.py#L52) | [annotated](../../02_business_logic/scinsight_use_cases/scinsight_service.py) |  |
| F0316 | `Service._batches` | method | used | [backend/scinsight/service.py:58](../../../backend/scinsight/service.py#L58) | [annotated](../../02_business_logic/scinsight_use_cases/scinsight_service.py) |  |
| F0317 | `Service._demand` | method | used | [backend/scinsight/service.py:65](../../../backend/scinsight/service.py#L65) | [annotated](../../02_business_logic/scinsight_use_cases/scinsight_service.py) |  |
| F0318 | `Service._require_item` | method | used | [backend/scinsight/service.py:68](../../../backend/scinsight/service.py#L68) | [annotated](../../02_business_logic/scinsight_use_cases/scinsight_service.py) |  |
| F0319 | `Service.inventory` | method | used | [backend/scinsight/service.py:78](../../../backend/scinsight/service.py#L78) | [annotated](../../02_business_logic/scinsight_use_cases/scinsight_service.py) |  |
| F0320 | `Service.bom` | method | used | [backend/scinsight/service.py:99](../../../backend/scinsight/service.py#L99) | [annotated](../../02_business_logic/scinsight_use_cases/scinsight_service.py) |  |
| F0321 | `Service.table` | method | used | [backend/scinsight/service.py:111](../../../backend/scinsight/service.py#L111) | [annotated](../../02_business_logic/scinsight_use_cases/scinsight_service.py) |  |
| F0322 | `Service.catalog` | method | used | [backend/scinsight/service.py:120](../../../backend/scinsight/service.py#L120) | [annotated](../../02_business_logic/scinsight_use_cases/scinsight_service.py) | Identifiers and names only (no quantities): lets an agent map 'vitamin C serum'  |
| F0323 | `Service.suppliers` | method | used | [backend/scinsight/service.py:133](../../../backend/scinsight/service.py#L133) | [annotated](../../02_business_logic/scinsight_use_cases/scinsight_service.py) |  |
| F0324 | `Service._supplier_options` | method | used | [backend/scinsight/service.py:142](../../../backend/scinsight/service.py#L142) | [annotated](../../02_business_logic/scinsight_use_cases/scinsight_service.py) |  |
| F0325 | `Service.material_readiness` | method | used | [backend/scinsight/service.py:160](../../../backend/scinsight/service.py#L160) | [annotated](../../02_business_logic/scinsight_use_cases/scinsight_service.py) |  |
| F0326 | `Service._sites` | method | used | [backend/scinsight/service.py:232](../../../backend/scinsight/service.py#L232) | [annotated](../../02_business_logic/scinsight_use_cases/scinsight_service.py) |  |
| F0327 | `Service.warehouse_balancing` | method | used | [backend/scinsight/service.py:240](../../../backend/scinsight/service.py#L240) | [annotated](../../02_business_logic/scinsight_use_cases/scinsight_service.py) |  |
| F0328 | `Service.replenishment` | method | used | [backend/scinsight/service.py:291](../../../backend/scinsight/service.py#L291) | [annotated](../../02_business_logic/scinsight_use_cases/scinsight_service.py) |  |
| F0329 | `Service.quality_check` | method | used | [backend/scinsight/service.py:312](../../../backend/scinsight/service.py#L312) | [annotated](../../02_business_logic/scinsight_use_cases/scinsight_service.py) |  |
| F0330 | `Service.forecast_demand` | method | used | [backend/scinsight/service.py:326](../../../backend/scinsight/service.py#L326) | [annotated](../../02_business_logic/scinsight_use_cases/scinsight_service.py) |  |
| F0331 | `Service.forecast_demand.predict` | nested | used | [backend/scinsight/service.py:333](../../../backend/scinsight/service.py#L333) | [annotated](../../02_business_logic/scinsight_use_cases/scinsight_service.py) |  |
| F0332 | `Service.lead_time` | method | used | [backend/scinsight/service.py:351](../../../backend/scinsight/service.py#L351) | [annotated](../../02_business_logic/scinsight_use_cases/scinsight_service.py) |  |
| F0333 | `Service.create_decision` | method | used | [backend/scinsight/service.py:374](../../../backend/scinsight/service.py#L374) | [annotated](../../02_business_logic/scinsight_use_cases/scinsight_service.py) |  |
| F0334 | `Service._rec` | method | used | [backend/scinsight/service.py:400](../../../backend/scinsight/service.py#L400) | [annotated](../../02_business_logic/scinsight_use_cases/scinsight_service.py) |  |
| F0335 | `Service.get_decision` | method | used | [backend/scinsight/service.py:406](../../../backend/scinsight/service.py#L406) | [annotated](../../02_business_logic/scinsight_use_cases/scinsight_service.py) |  |
| F0336 | `Service.list_decisions` | method | used | [backend/scinsight/service.py:418](../../../backend/scinsight/service.py#L418) | [annotated](../../02_business_logic/scinsight_use_cases/scinsight_service.py) |  |
| F0337 | `Service.review` | method | used | [backend/scinsight/service.py:423](../../../backend/scinsight/service.py#L423) | [annotated](../../02_business_logic/scinsight_use_cases/scinsight_service.py) |  |
| F0338 | `Service.review.apply` | nested | used | [backend/scinsight/service.py:430](../../../backend/scinsight/service.py#L430) | [annotated](../../02_business_logic/scinsight_use_cases/scinsight_service.py) |  |
| F0339 | `Service.withdraw` | method | used | [backend/scinsight/service.py:444](../../../backend/scinsight/service.py#L444) | [annotated](../../02_business_logic/scinsight_use_cases/scinsight_service.py) |  |
| F0340 | `Service.record_sap_execution` | method | used | [backend/scinsight/service.py:453](../../../backend/scinsight/service.py#L453) | [annotated](../../02_business_logic/scinsight_use_cases/scinsight_service.py) |  |
| F0341 | `Service.reconcile` | method | used | [backend/scinsight/service.py:469](../../../backend/scinsight/service.py#L469) | [annotated](../../02_business_logic/scinsight_use_cases/scinsight_service.py) |  |
| F0342 | `Service.reconcile.write` | nested | used | [backend/scinsight/service.py:489](../../../backend/scinsight/service.py#L489) | [annotated](../../02_business_logic/scinsight_use_cases/scinsight_service.py) |  |
| F0343 | `Service.learning_metrics` | method | used | [backend/scinsight/service.py:509](../../../backend/scinsight/service.py#L509) | [annotated](../../02_business_logic/scinsight_use_cases/scinsight_service.py) |  |
