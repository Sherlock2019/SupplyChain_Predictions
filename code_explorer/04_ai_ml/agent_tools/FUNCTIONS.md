# 04_ai_ml/agent_tools (generated)

Modules: `backend/app/copilot.py`, `backend/app/mcp_server.py`, `backend/app/tools.py`

| ID | Function / class | Kind | Status | Original | Annotated copy | Summary |
|---|---|---|---|---|---|---|
| F0438 | `CopilotBackend` | class | used | [backend/app/copilot.py:21](../../../backend/app/copilot.py#L21) | [annotated](../../04_ai_ml/agent_tools/app_copilot.py) |  |
| F0439 | `CopilotBackend.snapshot` | method | used (framework) | [backend/app/copilot.py:22](../../../backend/app/copilot.py#L22) | [annotated](../../04_ai_ml/agent_tools/app_copilot.py) |  |
| F0440 | `CopilotBackend.factory_readiness` | method | used (framework) | [backend/app/copilot.py:23](../../../backend/app/copilot.py#L23) | [annotated](../../04_ai_ml/agent_tools/app_copilot.py) |  |
| F0441 | `CopilotBackend.stock_balance` | method | used (framework) | [backend/app/copilot.py:24](../../../backend/app/copilot.py#L24) | [annotated](../../04_ai_ml/agent_tools/app_copilot.py) |  |
| F0442 | `CopilotBackend.demand_forecast` | method | used (framework) | [backend/app/copilot.py:25](../../../backend/app/copilot.py#L25) | [annotated](../../04_ai_ml/agent_tools/app_copilot.py) |  |
| F0443 | `CopilotBackend.supplier_risk` | method | used (framework) | [backend/app/copilot.py:26](../../../backend/app/copilot.py#L26) | [annotated](../../04_ai_ml/agent_tools/app_copilot.py) |  |
| F0444 | `CopilotBackend.quality_status` | method | used (framework) | [backend/app/copilot.py:27](../../../backend/app/copilot.py#L27) | [annotated](../../04_ai_ml/agent_tools/app_copilot.py) |  |
| F0445 | `CopilotBackend.logistics_status` | method | used (framework) | [backend/app/copilot.py:28](../../../backend/app/copilot.py#L28) | [annotated](../../04_ai_ml/agent_tools/app_copilot.py) |  |
| F0446 | `CopilotBackend.inventory` | method | used (framework) | [backend/app/copilot.py:29](../../../backend/app/copilot.py#L29) | [annotated](../../04_ai_ml/agent_tools/app_copilot.py) |  |
| F0447 | `CopilotBackend.sales_orders` | method | used (framework) | [backend/app/copilot.py:30](../../../backend/app/copilot.py#L30) | [annotated](../../04_ai_ml/agent_tools/app_copilot.py) |  |
| F0448 | `CopilotBackend.stocktake` | method | used (framework) | [backend/app/copilot.py:31](../../../backend/app/copilot.py#L31) | [annotated](../../04_ai_ml/agent_tools/app_copilot.py) |  |
| F0449 | `CopilotBackend.search_knowledge` | method | used (framework) | [backend/app/copilot.py:32](../../../backend/app/copilot.py#L32) | [annotated](../../04_ai_ml/agent_tools/app_copilot.py) |  |
| F0450 | `CopilotBackend.submit_recommendation` | method | used (framework) | [backend/app/copilot.py:33](../../../backend/app/copilot.py#L33) | [annotated](../../04_ai_ml/agent_tools/app_copilot.py) |  |
| F0451 | `LocalBackend` | class | used | [backend/app/copilot.py:36](../../../backend/app/copilot.py#L36) | [annotated](../../04_ai_ml/agent_tools/app_copilot.py) | In-process engine with its own ledger. Used by unit tests and when no gateway UR |
| F0452 | `LocalBackend.__init__` | method | used (framework) | [backend/app/copilot.py:39](../../../backend/app/copilot.py#L39) | [annotated](../../04_ai_ml/agent_tools/app_copilot.py) |  |
| F0453 | `LocalBackend._save` | method | used | [backend/app/copilot.py:46](../../../backend/app/copilot.py#L46) | [annotated](../../04_ai_ml/agent_tools/app_copilot.py) |  |
| F0454 | `LocalBackend.snapshot` | method | used | [backend/app/copilot.py:50](../../../backend/app/copilot.py#L50) | [annotated](../../04_ai_ml/agent_tools/app_copilot.py) |  |
| F0455 | `LocalBackend.factory_readiness` | method | used | [backend/app/copilot.py:58](../../../backend/app/copilot.py#L58) | [annotated](../../04_ai_ml/agent_tools/app_copilot.py) |  |
| F0456 | `LocalBackend.stock_balance` | method | used | [backend/app/copilot.py:62](../../../backend/app/copilot.py#L62) | [annotated](../../04_ai_ml/agent_tools/app_copilot.py) |  |
| F0457 | `LocalBackend.demand_forecast` | method | used | [backend/app/copilot.py:66](../../../backend/app/copilot.py#L66) | [annotated](../../04_ai_ml/agent_tools/app_copilot.py) |  |
| F0458 | `LocalBackend.supplier_risk` | method | used | [backend/app/copilot.py:70](../../../backend/app/copilot.py#L70) | [annotated](../../04_ai_ml/agent_tools/app_copilot.py) |  |
| F0459 | `LocalBackend.quality_status` | method | used | [backend/app/copilot.py:73](../../../backend/app/copilot.py#L73) | [annotated](../../04_ai_ml/agent_tools/app_copilot.py) |  |
| F0460 | `LocalBackend.logistics_status` | method | used | [backend/app/copilot.py:76](../../../backend/app/copilot.py#L76) | [annotated](../../04_ai_ml/agent_tools/app_copilot.py) |  |
| F0461 | `LocalBackend.inventory` | method | used | [backend/app/copilot.py:79](../../../backend/app/copilot.py#L79) | [annotated](../../04_ai_ml/agent_tools/app_copilot.py) |  |
| F0462 | `LocalBackend.sales_orders` | method | used | [backend/app/copilot.py:82](../../../backend/app/copilot.py#L82) | [annotated](../../04_ai_ml/agent_tools/app_copilot.py) |  |
| F0463 | `LocalBackend.stocktake` | method | used | [backend/app/copilot.py:85](../../../backend/app/copilot.py#L85) | [annotated](../../04_ai_ml/agent_tools/app_copilot.py) |  |
| F0464 | `LocalBackend.search_knowledge` | method | used | [backend/app/copilot.py:88](../../../backend/app/copilot.py#L88) | [annotated](../../04_ai_ml/agent_tools/app_copilot.py) |  |
| F0465 | `LocalBackend.submit_recommendation` | method | used | [backend/app/copilot.py:91](../../../backend/app/copilot.py#L91) | [annotated](../../04_ai_ml/agent_tools/app_copilot.py) |  |
| F0466 | `ApiError` | class | used | [backend/app/copilot.py:95](../../../backend/app/copilot.py#L95) | [annotated](../../04_ai_ml/agent_tools/app_copilot.py) |  |
| F0467 | `ApiBackend` | class | used | [backend/app/copilot.py:99](../../../backend/app/copilot.py#L99) | [annotated](../../04_ai_ml/agent_tools/app_copilot.py) | HTTP client for the FastAPI gateway; every call is authenticated and audited by  |
| F0468 | `ApiBackend.__init__` | method | used (framework) | [backend/app/copilot.py:102](../../../backend/app/copilot.py#L102) | [annotated](../../04_ai_ml/agent_tools/app_copilot.py) |  |
| F0469 | `ApiBackend._call` | method | used | [backend/app/copilot.py:105](../../../backend/app/copilot.py#L105) | [annotated](../../04_ai_ml/agent_tools/app_copilot.py) |  |
| F0470 | `ApiBackend._clean` | method | used | [backend/app/copilot.py:115](../../../backend/app/copilot.py#L115) | [annotated](../../04_ai_ml/agent_tools/app_copilot.py) |  |
| F0471 | `ApiBackend.snapshot` | method | used | [backend/app/copilot.py:119](../../../backend/app/copilot.py#L119) | [annotated](../../04_ai_ml/agent_tools/app_copilot.py) |  |
| F0472 | `ApiBackend.factory_readiness` | method | used | [backend/app/copilot.py:122](../../../backend/app/copilot.py#L122) | [annotated](../../04_ai_ml/agent_tools/app_copilot.py) |  |
| F0473 | `ApiBackend.stock_balance` | method | used | [backend/app/copilot.py:125](../../../backend/app/copilot.py#L125) | [annotated](../../04_ai_ml/agent_tools/app_copilot.py) |  |
| F0474 | `ApiBackend.demand_forecast` | method | used | [backend/app/copilot.py:128](../../../backend/app/copilot.py#L128) | [annotated](../../04_ai_ml/agent_tools/app_copilot.py) |  |
| F0475 | `ApiBackend.supplier_risk` | method | used | [backend/app/copilot.py:131](../../../backend/app/copilot.py#L131) | [annotated](../../04_ai_ml/agent_tools/app_copilot.py) |  |
| F0476 | `ApiBackend.quality_status` | method | used | [backend/app/copilot.py:134](../../../backend/app/copilot.py#L134) | [annotated](../../04_ai_ml/agent_tools/app_copilot.py) |  |
| F0477 | `ApiBackend.logistics_status` | method | used | [backend/app/copilot.py:137](../../../backend/app/copilot.py#L137) | [annotated](../../04_ai_ml/agent_tools/app_copilot.py) |  |
| F0478 | `ApiBackend.inventory` | method | used | [backend/app/copilot.py:140](../../../backend/app/copilot.py#L140) | [annotated](../../04_ai_ml/agent_tools/app_copilot.py) |  |
| F0479 | `ApiBackend.sales_orders` | method | used | [backend/app/copilot.py:143](../../../backend/app/copilot.py#L143) | [annotated](../../04_ai_ml/agent_tools/app_copilot.py) |  |
| F0480 | `ApiBackend.stocktake` | method | used | [backend/app/copilot.py:146](../../../backend/app/copilot.py#L146) | [annotated](../../04_ai_ml/agent_tools/app_copilot.py) |  |
| F0481 | `ApiBackend.search_knowledge` | method | used | [backend/app/copilot.py:149](../../../backend/app/copilot.py#L149) | [annotated](../../04_ai_ml/agent_tools/app_copilot.py) |  |
| F0482 | `ApiBackend.submit_recommendation` | method | used | [backend/app/copilot.py:152](../../../backend/app/copilot.py#L152) | [annotated](../../04_ai_ml/agent_tools/app_copilot.py) |  |
| F0483 | `build_backend` | function | used | [backend/app/copilot.py:156](../../../backend/app/copilot.py#L156) | [annotated](../../04_ai_ml/agent_tools/app_copilot.py) |  |
| F0484 | `get_backend` | function | used | [backend/app/copilot.py:168](../../../backend/app/copilot.py#L168) | [annotated](../../04_ai_ml/agent_tools/app_copilot.py) |  |
| F0485 | `_dump` | function | used | [backend/app/mcp_server.py:29](../../../backend/app/mcp_server.py#L29) | [annotated](../../04_ai_ml/agent_tools/app_mcp_server.py) |  |
| F0486 | `sap_snapshot` | function | used | [backend/app/mcp_server.py:36](../../../backend/app/mcp_server.py#L36) | [annotated](../../04_ai_ml/agent_tools/app_mcp_server.py) | SAP snapshot provenance and valid plant, material and supplier codes. Call first |
| F0487 | `factory_material_readiness` | function | used | [backend/app/mcp_server.py:42](../../../backend/app/mcp_server.py#L42) | [annotated](../../04_ai_ml/agent_tools/app_mcp_server.py) | BOM material readiness for a production run (plant FR10/FR20/TPM1, finished good |
| F0488 | `warehouse_stock_balance` | function | used | [backend/app/mcp_server.py:48](../../../backend/app/mcp_server.py#L48) | [annotated](../../04_ai_ml/agent_tools/app_mcp_server.py) | XGBoost demand forecast and OR-Tools transfer proposals across DC01, DC21 and DC |
| F0489 | `supplier_risk` | function | used | [backend/app/mcp_server.py:54](../../../backend/app/mcp_server.py#L54) | [annotated](../../04_ai_ml/agent_tools/app_mcp_server.py) | Supplier scorecard: OTIF, delays, quality rejects, open PO exposure and single-s |
| F0490 | `quality_status` | function | used | [backend/app/mcp_server.py:60](../../../backend/app/mcp_server.py#L60) | [annotated](../../04_ai_ml/agent_tools/app_mcp_server.py) | Open inspection lots, blocked/expired batches and affected production orders. |
| F0491 | `logistics_status` | function | used | [backend/app/mcp_server.py:66](../../../backend/app/mcp_server.py#L66) | [annotated](../../04_ai_ml/agent_tools/app_mcp_server.py) | In-transit shipments, delays, revised ETAs and escalations. |
| F0492 | `inventory_overview` | function | used | [backend/app/mcp_server.py:72](../../../backend/app/mcp_server.py#L72) | [annotated](../../04_ai_ml/agent_tools/app_mcp_server.py) | Finished-goods stock, days of cover, open sales orders and in-transit stock by w |
| F0493 | `sales_order_fulfilment` | function | used | [backend/app/mcp_server.py:78](../../../backend/app/mcp_server.py#L78) | [annotated](../../04_ai_ml/agent_tools/app_mcp_server.py) | Open sales orders: on-time status, shortfalls and the cheapest on-time transfer  |
| F0494 | `stocktake_reconciliation` | function | used | [backend/app/mcp_server.py:84](../../../backend/app/mcp_server.py#L84) | [annotated](../../04_ai_ml/agent_tools/app_mcp_server.py) | Explain stock count differences with evidence and recommend posting, adjustment  |
| F0495 | `search_governed_knowledge` | function | used | [backend/app/mcp_server.py:90](../../../backend/app/mcp_server.py#L90) | [annotated](../../04_ai_ml/agent_tools/app_mcp_server.py) | Search approved contracts, SOPs, quality policies, product specs and logistics p |
| F0496 | `health` | route | used | [backend/app/mcp_server.py:96](../../../backend/app/mcp_server.py#L96) | [annotated](../../04_ai_ml/agent_tools/app_mcp_server.py) |  |
| F0497 | `ApiKeyMiddleware` | class | used | [backend/app/mcp_server.py:101](../../../backend/app/mcp_server.py#L101) | [annotated](../../04_ai_ml/agent_tools/app_mcp_server.py) | Bearer or X-API-Key check for /mcp; keys come from MCP_API_KEYS (comma separated |
| F0498 | `ApiKeyMiddleware.__init__` | method | used (framework) | [backend/app/mcp_server.py:104](../../../backend/app/mcp_server.py#L104) | [annotated](../../04_ai_ml/agent_tools/app_mcp_server.py) |  |
| F0499 | `ApiKeyMiddleware.dispatch` | method | used (framework) | [backend/app/mcp_server.py:108](../../../backend/app/mcp_server.py#L108) | [annotated](../../04_ai_ml/agent_tools/app_mcp_server.py) |  |
| F0500 | `create_mcp_app` | function | used | [backend/app/mcp_server.py:117](../../../backend/app/mcp_server.py#L117) | [annotated](../../04_ai_ml/agent_tools/app_mcp_server.py) |  |
| F0501 | `_dump` | function | used | [backend/app/tools.py:13](../../../backend/app/tools.py#L13) | [annotated](../../04_ai_ml/agent_tools/app_tools.py) |  |
| F0502 | `_safe` | function | used | [backend/app/tools.py:18](../../../backend/app/tools.py#L18) | [annotated](../../04_ai_ml/agent_tools/app_tools.py) |  |
| F0503 | `sap_snapshot` | function | used | [backend/app/tools.py:25](../../../backend/app/tools.py#L25) | [annotated](../../04_ai_ml/agent_tools/app_tools.py) | Return SAP snapshot provenance plus valid plant, material and supplier codes. Ca |
| F0504 | `factory_material_readiness` | function | used | [backend/app/tools.py:31](../../../backend/app/tools.py#L31) | [annotated](../../04_ai_ml/agent_tools/app_tools.py) | Check BOM material readiness for a production run. |
| F0505 | `warehouse_stock_balance` | function | used | [backend/app/tools.py:44](../../../backend/app/tools.py#L44) | [annotated](../../04_ai_ml/agent_tools/app_tools.py) | Forecast demand (XGBoost) and optimise stock transfers between DC01, DC21 and DC |
| F0506 | `demand_forecast` | function | used | [backend/app/tools.py:50](../../../backend/app/tools.py#L50) | [annotated](../../04_ai_ml/agent_tools/app_tools.py) | XGBoost daily demand forecast for a finished good, optionally for one warehouse  |
| F0507 | `supplier_risk` | function | used | [backend/app/tools.py:56](../../../backend/app/tools.py#L56) | [annotated](../../04_ai_ml/agent_tools/app_tools.py) | Supplier scorecard: OTIF, delays, quality rejects, open PO exposure, single-sour |
| F0508 | `quality_status` | function | used | [backend/app/tools.py:62](../../../backend/app/tools.py#L62) | [annotated](../../04_ai_ml/agent_tools/app_tools.py) | Quality inspection lots (QM): inspection/blocked/expired batches and which produ |
| F0509 | `logistics_status` | function | used | [backend/app/tools.py:68](../../../backend/app/tools.py#L68) | [annotated](../../04_ai_ml/agent_tools/app_tools.py) | In-transit shipments, delays, revised ETAs and escalations for a warehouse and/o |
| F0510 | `inventory_overview` | function | used | [backend/app/tools.py:74](../../../backend/app/tools.py#L74) | [annotated](../../04_ai_ml/agent_tools/app_tools.py) | Finished-goods stock, days of cover, open sales orders and in-transit stock by w |
| F0511 | `sales_order_fulfilment` | function | used | [backend/app/tools.py:80](../../../backend/app/tools.py#L80) | [annotated](../../04_ai_ml/agent_tools/app_tools.py) | Open sales orders: can each ship on time from DC stock + inbound? Shortfalls get |
| F0512 | `stocktake_reconciliation` | function | used | [backend/app/tools.py:86](../../../backend/app/tools.py#L86) | [annotated](../../04_ai_ml/agent_tools/app_tools.py) | Explain stock count differences (unposted goods movements, scrap not posted) and |
| F0513 | `search_governed_knowledge` | function | used | [backend/app/tools.py:92](../../../backend/app/tools.py#L92) | [annotated](../../04_ai_ml/agent_tools/app_tools.py) | Search approved supplier contracts, SOPs, quality policies, product specs and lo |
