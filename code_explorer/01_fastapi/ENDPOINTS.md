# FastAPI endpoints (generated)

Both apps declare routes directly on `app` (no `APIRouter`, no prefixes), so the decorator path is the full path.

| ID | Method | Path | Handler | App | Depends / body model | Calls | Called from Flowise |
|---|---|---|---|---|---|---|---|
| F2099 | GET | /sap/opu/odata/sap/{path:path} | `odata` | gateway :8000 |  | F2094 build_entities(), F2097 respond() |  |
| F2115 | GET | /api/v1/erp/providers | `providers` | gateway :8000 |  | F2173 options() |  |
| F2116 | GET | /api/v1/erp/connections | `connections` | gateway :8000 |  | F2112 register.tenant() |  |
| F2117 | POST | /api/v1/erp/connections | `create` | gateway :8000 | F2136 ConnectionIn | F2113 register.run(), F2112 register.tenant(), F2114 register.log() |  |
| F2118 | GET | /api/v1/erp/connections/{conn_id} | `get` | gateway :8000 |  | F2113 register.run(), F2112 register.tenant() |  |
| F2119 | PATCH | /api/v1/erp/connections/{conn_id} | `patch` | gateway :8000 |  | F2113 register.run(), F2112 register.tenant(), F2114 register.log() |  |
| F2120 | POST | /api/v1/erp/connections/{conn_id}/test | `test` | gateway :8000 |  | F2113 register.run(), F2112 register.tenant(), F2114 register.log() |  |
| F2121 | GET | /api/v1/erp/connections/{conn_id}/health | `health` | gateway :8000 |  | F2113 register.run(), F2112 register.tenant() |  |
| F2122 | GET | /api/v1/erp/connections/{conn_id}/entities | `entities` | gateway :8000 |  | F2113 register.run(), F2153 ErpService.discover(), F2112 register.tenant(), F2114 register.log() |  |
| F2123 | GET | /api/v1/erp/connections/{conn_id}/mappings | `mappings` | gateway :8000 |  | F2113 register.run(), F2150 ErpService.mapping(), F2112 register.tenant() |  |
| F2124 | PUT | /api/v1/erp/connections/{conn_id}/mappings | `put_mappings` | gateway :8000 | F2137 MappingIn | F2113 register.run(), F2151 ErpService.set_mapping(), F2112 register.tenant(), F2114 register.log() |  |
| F2125 | POST | /api/v1/erp/connections/{conn_id}/validate | `validate` | gateway :8000 |  | F2113 register.run(), F2112 register.tenant(), F2114 register.log() |  |
| F2126 | POST | /api/v1/erp/connections/{conn_id}/preview | `preview` | gateway :8000 | F2108 PreviewIn | F2113 register.run(), F2112 register.tenant(), F2114 register.log() |  |
| F2127 | POST | /api/v1/erp/connections/{conn_id}/sync | `sync` | gateway :8000 |  | F2114 register.log(), F2113 register.run(), F2112 register.tenant() |  |
| F2128 | GET | /api/v1/erp/connections/{conn_id}/sync-history | `sync_history` | gateway :8000 |  | F2113 register.run(), F2112 register.tenant() |  |
| F2129 | POST | /api/v1/erp/connections/{conn_id}/activate | `activate` | gateway :8000 |  | F2113 register.run(), F2112 register.tenant(), F2114 register.log() |  |
| F2130 | POST | /api/v1/erp/connections/{conn_id}/rollback | `rollback` | gateway :8000 |  | F2113 register.run(), F2112 register.tenant(), F2114 register.log() |  |
| F2131 | GET | /api/v1/erp/connections/{conn_id}/logs | `logs` | gateway :8000 |  | F2113 register.run(), F2112 register.tenant() |  |
| F2132 | GET | /api/v1/erp/activation-history | `activation_history` | gateway :8000 |  | F2112 register.tenant() |  |
| F2133 | GET | /api/v1/erp/integration-status | `integration_status` | gateway :8000 |  | F2112 register.tenant(), F2057 last_check() |  |
| F2134 | POST | /api/v1/erp/validate-integrations | `validate_all` | gateway :8000 |  | F2044 validate_integrations(), F2112 register.tenant(), F2056 save_check(), F2114 register.log() |  |
| F0025 | GET | /health | `health` | gateway :8000 |  |  |  |
| F0026 | GET | /ready | `ready` | gateway :8000 |  | F0747 MemoryRag.stats(), F0753 PgVectorRag.stats() |  |
| F0027 | GET | /metrics | `metrics` | gateway :8000 |  |  |  |
| F0028 | GET | /api/v1/config/public | `public_config` | gateway :8000 |  | F0030 create_app._public() |  |
| F0029 | GET | /api/v1/demo/session | `demo_session` | gateway :8000 |  |  |  |
| F0031 | GET | /api/v1/status | `status` | gateway :8000 | F0021 create_app.reader() | F0032 create_app.status.probe(), F0747 MemoryRag.stats(), F0753 PgVectorRag.stats(), F0389 Store.counts(), F0359 Store.verify_chain() |  |
| F0033 | GET | /api/v1/snapshot | `snapshot` | gateway :8000 | F0021 create_app.reader() | F0393 TenantRegistry.get(), F0407 SapRepository.section() |  |
| F0034 | GET | /api/v1/tenants | `tenant_catalogue` | gateway :8000 |  | F0394 TenantRegistry.catalogue(), F0397 TenantRegistry.current_id() |  |
| F0035 | GET | /api/v1/network/map | `network_map` | gateway :8000 | F0021 create_app.reader() | F0224 SupplyChainEngine.network_map() |  |
| F0036 | GET | /sap/opu/odata/sap/ZSCM_COPILOT_SRV/$metadata | `sap_metadata` | gateway :8000 | F0021 create_app.reader() | F0415 SapRepository.metadata() |  |
| F0037 | GET | /sap/opu/odata/sap/ZSCM_COPILOT_SRV/A_SandboxDocument | `sap_sandbox_documents` | gateway :8000 | F0021 create_app.reader() | F0376 Store.sap_documents() |  |
| F0038 | GET | /sap/opu/odata/sap/ZSCM_COPILOT_SRV/{entity} | `sap_odata` | gateway :8000 | F0021 create_app.reader() | F0414 SapRepository.odata() |  |
| F0039 | POST/PUT/PATCH/DELETE | /sap/opu/odata/sap/{path:path} | `block_sap_write` | gateway :8000 | F0021 create_app.reader() | F0358 Store.audit() |  |
| F0040 | POST | /api/v1/analysis/factory-readiness | `factory_readiness` | gateway :8000 | F0021 create_app.reader(), F0148 FactoryReadinessRequest | F0197 SupplyChainEngine.factory_readiness(), F0023 create_app.save() |  |
| F0041 | POST | /api/v1/analysis/stock-balance | `stock_balance` | gateway :8000 | F0021 create_app.reader(), F0149 StockBalanceRequest | F0023 create_app.save(), F0198 SupplyChainEngine.stock_balance() |  |
| F0042 | POST | /api/v1/analysis/forecast | `demand_forecast` | gateway :8000 | F0021 create_app.reader(), F0150 ForecastRequest | F0023 create_app.save(), F0199 SupplyChainEngine.demand_forecast() |  |
| F0043 | POST | /api/v1/analysis/what-if | `what_if` | gateway :8000 | F0021 create_app.reader(), F0151 WhatIfRequest | F0200 SupplyChainEngine.what_if(), F0023 create_app.save() |  |
| F0044 | POST | /api/v1/analysis/supplier-risk | `supplier_risk` | gateway :8000 | F0021 create_app.reader(), F0152 SupplierRiskRequest | F0023 create_app.save(), F0201 SupplyChainEngine.supplier_risk() |  |
| F0045 | POST | /api/v1/analysis/quality | `quality` | gateway :8000 | F0021 create_app.reader(), F0153 QualityRequest | F0023 create_app.save(), F0203 SupplyChainEngine.quality_status() |  |
| F0046 | POST | /api/v1/analysis/logistics | `logistics` | gateway :8000 | F0021 create_app.reader(), F0154 LogisticsRequest | F0023 create_app.save(), F0204 SupplyChainEngine.logistics_status() |  |
| F0047 | POST | /api/v1/analysis/sales-orders | `sales_orders` | gateway :8000 | F0021 create_app.reader(), F0155 SalesOrderRequest | F0023 create_app.save(), F0206 SupplyChainEngine.sales_order_fulfilment() |  |
| F0048 | POST | /api/v1/analysis/stocktake | `stocktake` | gateway :8000 | F0021 create_app.reader(), F0156 StocktakeRequest | F0023 create_app.save(), F0207 SupplyChainEngine.stocktake_reconciliation() |  |
| F0049 | GET | /api/v1/analysis/forecast-vs-actuals | `forecast_vs_actuals` | gateway :8000 | F0021 create_app.reader() | F0209 SupplyChainEngine.forecast_vs_actuals() |  |
| F0050 | GET | /api/v1/production/overview | `production_overview` | gateway :8000 | F0021 create_app.reader() | F0208 SupplyChainEngine.production_overview() |  |
| F0051 | GET | /api/v1/products | `products` | gateway :8000 | F0021 create_app.reader() | F0211 SupplyChainEngine.products() |  |
| F0052 | GET | /api/v1/products/{material} | `product` | gateway :8000 | F0021 create_app.reader() | F0212 SupplyChainEngine.product_360() |  |
| F0053 | GET | /api/v1/roles | `role_catalogue` | gateway :8000 | F0021 create_app.reader() | F0271 RoleCenter.catalogue() |  |
| F0054 | GET | /api/v1/roles/{role} | `role_view` | gateway :8000 | F0021 create_app.reader() | F0272 RoleCenter.build() |  |
| F0055 | GET | /api/v1/northstar | `north_star` | gateway :8000 | F0021 create_app.reader() | F0269 RoleCenter.north_star() |  |
| F0056 | GET | /api/v1/learning | `learning` | gateway :8000 | F0021 create_app.reader() | F0290 RoleCenter.learning() |  |
| F0057 | GET | /api/v1/moat | `moat_view` | gateway :8000 | F0021 create_app.reader() | F0255 MoatEngine.view(), F0397 TenantRegistry.current_id() |  |
| F0058 | POST | /api/v1/moat/consent | `moat_consent` | gateway :8000 | F0020 create_app.manager(), F0163 ConsentRequest | F0397 TenantRegistry.current_id(), F0385 Store.set_consent(), F0358 Store.audit(), F0252 MoatEngine.consent() |  |
| F0059 | POST | /api/v1/recommendations/{recommendation_id}/outcome | `record_outcome` | gateway :8000 | F0020 create_app.manager(), F0165 OutcomeRequest | F0366 Store.get_recommendation(), F0380 Store.list_outcomes(), F0378 Store.create_outcome(), F0016 _expectation(), F0381 Store.record_outcome(), F0358 Store.aud |  |
| F0060 | GET | /api/v1/sales/outlook | `sales_outlook` | gateway :8000 | F0021 create_app.reader() | F0220 SupplyChainEngine.sales_outlook() |  |
| F0061 | GET | /api/v1/products/{material}/brief | `product_brief` | gateway :8000 | F0021 create_app.reader() | F0213 SupplyChainEngine.product_brief() |  |
| F0062 | GET | /api/v1/sites | `sites` | gateway :8000 | F0021 create_app.reader() | F0221 SupplyChainEngine.sites() |  |
| F0063 | GET | /api/v1/sites/{code} | `site` | gateway :8000 | F0021 create_app.reader() | F0222 SupplyChainEngine.site_360() |  |
| F0064 | GET | /api/v1/dashboards | `dashboards_list` | gateway :8000 |  |  |  |
| F0065 | GET | /api/v1/dashboards/{persona} | `dashboard` | gateway :8000 | F0021 create_app.reader() | F0232 Dashboards.build() |  |
| F0066 | GET | /api/v1/insights | `get_insights` | gateway :8000 | F0021 create_app.reader() | F0248 InsightEngine.insights() |  |
| F0067 | GET | /api/v1/watches/kinds | `watch_kinds` | gateway :8000 |  |  |  |
| F0068 | GET | /api/v1/watches | `list_watches` | gateway :8000 | F0021 create_app.reader() | F0372 Store.list_watches(), F0022 create_app.watch_owner() |  |
| F0069 | POST | /api/v1/watches | `create_watch` | gateway :8000 | F0021 create_app.reader(), F0157 WatchRequest | F0249 InsightEngine.evaluate(), F0369 Store.create_watch(), F0022 create_app.watch_owner(), F0358 Store.audit() |  |
| F0070 | DELETE | /api/v1/watches/{watch_id} | `delete_watch` | gateway :8000 | F0021 create_app.reader() | F0373 Store.delete_watch(), F0022 create_app.watch_owner() |  |
| F0071 | POST | /api/v1/watches/evaluate | `evaluate_watches` | gateway :8000 | F0021 create_app.reader() | F0372 Store.list_watches(), F0022 create_app.watch_owner(), F0249 InsightEngine.evaluate(), F0374 Store.record_watch() |  |
| F0072 | GET | /api/v1/analyses/{analysis_id} | `get_analysis` | gateway :8000 | F0021 create_app.reader() | F0362 Store.get_analysis() |  |
| F0073 | GET | /api/v1/inventory | `inventory` | gateway :8000 | F0021 create_app.reader() | F0205 SupplyChainEngine.inventory_overview() |  |
| F0074 | GET | /api/v1/suppliers/scorecard | `supplier_scorecard` | gateway :8000 | F0021 create_app.reader() | F0202 SupplyChainEngine.supplier_scorecard() |  |
| F0075 | GET | /api/v1/kpis | `kpis` | gateway :8000 | F0021 create_app.reader() | F0226 SupplyChainEngine.kpis() |  |
| F0076 | POST | /api/v1/rag/search | `rag_search` | gateway :8000 | F0021 create_app.reader(), F0158 RagQuery | F0746 MemoryRag.search(), F0755 PgVectorRag.search() | Flowise Custom Tool · search_supply_chain_policy, Factory-Planning-Agentflow · 5 · Policy search (RAG), Inventory-Optimizer-Agentflow · 5 · Policy search (RAG), |
| F0077 | GET | /api/v1/rag/search | `rag_search_get` | gateway :8000 | F0021 create_app.reader() | F0746 MemoryRag.search(), F0755 PgVectorRag.search() |  |
| F0078 | POST | /v1/embeddings | `embeddings` | gateway :8000 | F0168 EmbeddingsRequest | F0019 create_app.principal(), F0079 create_app.embeddings.encode() |  |
| F0080 | GET | /api/v1/rag/stats | `rag_stats` | gateway :8000 | F0021 create_app.reader() | F0747 MemoryRag.stats(), F0753 PgVectorRag.stats() |  |
| F0081 | POST | /api/v1/rag/documents | `rag_add` | gateway :8000 | F0020 create_app.manager(), F0159 RagDocument | F0745 MemoryRag.add(), F0752 PgVectorRag.add(), F0358 Store.audit() |  |
| F1801 | GET/POST/PUT | /api/v1/rag-tuning/{path:path} | `rag_tuning_proxy` | gateway :8000 | F0021 create_app.reader() | F0358 Store.audit() |  |
| F1950 | GET | /api/v1/code/files | `code_files` | gateway :8000 | F0021 create_app.reader() | F1952 CodeEditor.files() |  |
| F1951 | GET | /api/v1/code/file | `code_file` | gateway :8000 | F0021 create_app.reader() | F1953 CodeEditor.file() |  |
| F1955 | GET | /api/v1/code/template | `code_template` | gateway :8000 | F0021 create_app.reader() | F1956 CodeEditor.template() |  |
| F0985 | GET | /api/v1/code/functions | `code_functions` | gateway :8000 | F0021 create_app.reader() |  |  |
| F0986 | GET | /api/v1/code/function | `code_function` | gateway :8000 | F0021 create_app.reader() |  |  |
| F0987 | PUT | /api/v1/code/function | `code_update` | gateway :8000 | F0020 create_app.manager(), F0988 CodeUpdateRequest | F0358 Store.audit() |  |
| F0083 | POST | /api/v1/chat | `chat` | gateway :8000 | F0021 create_app.reader(), F0164 ChatRequest | F0082 create_app._graph_call(), F0358 Store.audit() |  |
| F0085 | POST | /api/v1/langgraph/agentflow | `langgraph_agentflow` | gateway :8000 | F0021 create_app.reader(), F0164 ChatRequest | F0082 create_app._graph_call(), F0084 create_app._agentflow_view(), F0358 Store.audit() |  |
| F0086 | POST | /api/v1/langgraph/agentflow/{thread_id}/resume | `langgraph_agentflow_resume` | gateway :8000 | F0021 create_app.reader(), F0167 ResumeRequest | F0084 create_app._agentflow_view(), F0082 create_app._graph_call(), F0358 Store.audit() |  |
| F0087 | POST | /api/v1/workflows/business | `business_start` | gateway :8000 | F0021 create_app.reader(), F0166 BusinessWorkflowRequest | F0082 create_app._graph_call(), F0358 Store.audit() |  |
| F0088 | POST | /api/v1/workflows/business/{thread_id}/resume | `business_resume` | gateway :8000 | F0021 create_app.reader(), F0167 ResumeRequest | F0082 create_app._graph_call(), F0358 Store.audit() |  |
| F0090 | GET | /api/v1/deep-agents/harness | `deep_harness` | gateway :8000 | F0021 create_app.reader() | F0386 Store.get_setting(), F0089 create_app.current_harness(), F0172 DeepAgentHarness |  |
| F0091 | PUT | /api/v1/deep-agents/harness | `set_deep_harness` | gateway :8000 | F0020 create_app.manager(), F0172 DeepAgentHarness | F0387 Store.set_setting(), F0358 Store.audit() |  |
| F0092 | POST | /api/v1/deep-agents/supplier-research | `supplier_research` | gateway :8000 | F0021 create_app.reader(), F0174 SupplierResearchRequest | F0089 create_app.current_harness(), F0082 create_app._graph_call(), F0358 Store.audit() |  |
| F0094 | POST | /api/v1/flowise/{flow}/predict | `flowise_predict` | gateway :8000 | F0021 create_app.reader(), F0175 FlowisePredictRequest | F0093 create_app._flow_id(), F0358 Store.audit() |  |
| F0095 | POST | /api/v1/recommendations | `submit_recommendation` | gateway :8000 | F0021 create_app.reader(), F0160 RecommendationRequest | F0364 Store.submit(), F0358 Store.audit() |  |
| F0096 | POST | /api/v1/recommendations/from-agent | `submit_from_agent` | gateway :8000 | F0021 create_app.reader(), F0161 RecommendationFromTextRequest | F0363 Store.latest_actionable(), F0364 Store.submit(), F0358 Store.audit() |  |
| F0097 | GET | /api/v1/recommendations | `recommendations` | gateway :8000 | F0021 create_app.reader() | F0367 Store.list_recommendations() |  |
| F0098 | POST | /api/v1/recommendations/{recommendation_id}/decision | `decide` | gateway :8000 | F0020 create_app.manager(), F0162 DecisionRequest | F0368 Store.decide(), F0382 Store.record_feedback(), F0358 Store.audit() |  |
| F0099 | POST | /api/v1/recommendations/{recommendation_id}/execute | `execute` | gateway :8000 | F0020 create_app.manager() | F0366 Store.get_recommendation(), F0377 Store.next_doc_number(), F0375 Store.execute_recommendation(), F0016 _expectation(), F0378 Store.create_outcome(), F0358 |  |
| F0100 | GET | /api/v1/sap/documents | `sap_documents` | gateway :8000 | F0021 create_app.reader() | F0376 Store.sap_documents() |  |
| F0101 | GET | /api/v1/audit | `audit` | gateway :8000 | F0020 create_app.manager() | F0359 Store.verify_chain(), F0360 Store.audit_events() |  |
| F0102 | GET | /sap/inventory | `poc_sap_inventory` | gateway :8000 | F0021 create_app.reader() | F0414 SapRepository.odata() |  |
| F0103 | GET | /sap/production-orders | `poc_sap_production_orders` | gateway :8000 | F0021 create_app.reader() | F0414 SapRepository.odata() |  |
| F0104 | POST | /forecast/demand | `poc_forecast_demand` | gateway :8000 | F0021 create_app.reader(), F0150 ForecastRequest | F0023 create_app.save(), F0199 SupplyChainEngine.demand_forecast() |  |
| F0105 | POST | /forecast/supplier-lead-time | `poc_forecast_lead_time` | gateway :8000 | F0021 create_app.reader(), F0170 SupplierLeadTimeRequest | F0023 create_app.save(), F0219 SupplyChainEngine.supplier_lead_time() |  |
| F0106 | POST | /optimizer/material-readiness | `poc_material_readiness` | gateway :8000 | F0021 create_app.reader(), F0148 FactoryReadinessRequest | F0197 SupplyChainEngine.factory_readiness(), F0023 create_app.save() |  |
| F0107 | POST | /optimizer/warehouse-transfer | `poc_warehouse_transfer` | gateway :8000 | F0021 create_app.reader(), F0149 StockBalanceRequest | F0023 create_app.save(), F0198 SupplyChainEngine.stock_balance() |  |
| F0108 | POST | /decisions | `poc_decisions` | gateway :8000 | F0021 create_app.reader(), F0160 RecommendationRequest | F0095 create_app.submit_recommendation() |  |
| F0109 | POST | /decisions/{decision_id}/human-review | `poc_human_review` | gateway :8000 | F0020 create_app.manager(), F0162 DecisionRequest | F0098 create_app.decide() |  |
| F0110 | POST | /outcomes/reconcile | `poc_reconcile` | gateway :8000 | F0020 create_app.manager(), F0171 ReconcileRequest | F0366 Store.get_recommendation(), F0380 Store.list_outcomes(), F0378 Store.create_outcome(), F0016 _expectation(), F0381 Store.record_outcome(), F0358 Store.aud |  |
| F0111 | GET | /learning/model-performance | `poc_model_performance` | gateway :8000 | F0021 create_app.reader() | F0290 RoleCenter.learning() |  |
| F0496 | GET | /health | `health` | gateway :8000 |  |  |  |
| F1997 | GET | /health | `health` | scinsight :8100 |  |  |  |
| F1998 | GET | /api/v1/context | `context` | scinsight :8100 | F1995 create_router.reader() | F0313 Service.snapshot() |  |
| F1999 | POST | /api/v1/context/validate | `validate_context` | scinsight :8100 | F1995 create_router.reader(), F0178 ContextRequest | F0313 Service.snapshot(), F0779 Security.audit(), F0322 Service.catalog() | Decision-Outcome-Learning-Agentflow · 2 · Check access, Factory-Planning-Agentflow · 2 · Check access, Inventory-Optimizer-Agentflow · 2 · Check access, Logisti |
| F2000 | GET | /api/v1/sap/inventory | `sap_inventory` | scinsight :8100 | F1995 create_router.reader() | F0319 Service.inventory() | Flowise Custom Tool · get_sap_inventory |
| F2001 | GET | /api/v1/sap/bom/{sku} | `sap_bom` | scinsight :8100 | F1995 create_router.reader() | F0320 Service.bom() | Flowise Custom Tool · get_material_bom |
| F2002 | GET | /api/v1/sap/production-orders | `sap_production_orders` | scinsight :8100 | F1995 create_router.reader() | F0321 Service.table() | Flowise Custom Tool · get_production_orders, Factory-Planning-Agentflow · 4 · Calculate with SAP data |
| F2003 | GET | /api/v1/sap/purchase-orders | `sap_purchase_orders` | scinsight :8100 | F1995 create_router.reader() | F0321 Service.table() | Flowise Custom Tool · get_open_purchase_orders |
| F2004 | GET | /api/v1/sap/warehouses | `sap_warehouses` | scinsight :8100 | F1995 create_router.reader() | F0321 Service.table() |  |
| F2005 | GET | /api/v1/sap/suppliers | `sap_suppliers` | scinsight :8100 | F1995 create_router.reader() | F0323 Service.suppliers() | Procurement-Agentflow · 4 · Calculate with SAP data |
| F2006 | POST/PUT/PATCH/DELETE | /api/v1/sap/{path:path} | `sap_write_blocked` | scinsight :8100 | F1994 create_router.principal() | F0779 Security.audit() |  |
| F2007 | POST | /api/v1/optimizer/material-readiness | `material_readiness` | scinsight :8100 | F1995 create_router.reader(), F0179 MaterialReadinessRequest | F0325 Service.material_readiness() | Flowise Custom Tool · check_material_readiness, Factory-Planning-Agentflow · 4 · Calculate with SAP data |
| F2008 | POST | /api/v1/optimizer/warehouse-balancing | `warehouse_balancing` | scinsight :8100 | F1995 create_router.reader(), F0181 WarehouseBalancingRequest | F0327 Service.warehouse_balancing() | Flowise Custom Tool · optimize_warehouse_transfer, Logistics-Agentflow · 4 · Calculate with SAP data, Warehouse-Agentflow · 4 · Calculate with SAP data |
| F2009 | POST | /api/v1/optimizer/replenishment | `replenishment` | scinsight :8100 | F1995 create_router.reader(), F0182 ReplenishmentRequest | F0328 Service.replenishment() | Flowise Custom Tool · calculate_stock_cover, Inventory-Optimizer-Agentflow · 4 · Calculate with SAP data, Procurement-Agentflow · 4 · Calculate with SAP data |
| F2010 | POST | /api/v1/forecast/demand | `forecast_demand` | scinsight :8100 | F1995 create_router.reader(), F0183 DemandForecastRequest | F0330 Service.forecast_demand() | Flowise Custom Tool · forecast_demand, Inventory-Optimizer-Agentflow · 4 · Calculate with SAP data |
| F2011 | POST | /api/v1/forecast/lead-time | `forecast_lead_time` | scinsight :8100 | F1995 create_router.reader(), F0184 LeadTimeRequest | F0332 Service.lead_time() | Flowise Custom Tool · get_supplier_reliability, Procurement-Agentflow · 4 · Calculate with SAP data |
| F2012 | POST | /api/v1/quality/check-stock | `quality_check` | scinsight :8100 | F1995 create_router.reader(), F0185 QualityCheckRequest | F0329 Service.quality_check() | Flowise Custom Tool · check_batch_quality, Quality-Agentflow · 4 · Calculate with SAP data |
| F2013 | GET | /api/v1/calculations/{calculation_id} | `calculation` | scinsight :8100 | F1995 create_router.reader() | F0315 Service.calculation() |  |
| F2014 | POST | /api/v1/rag/search | `rag_search` | scinsight :8100 | F1995 create_router.reader(), F0186 RagSearchRequest | F0766 KnowledgeBase.search(), F1996 create_router.biz_date() | Flowise Custom Tool · search_supply_chain_policy, Factory-Planning-Agentflow · 5 · Policy search (RAG), Inventory-Optimizer-Agentflow · 5 · Policy search (RAG), |
| F2015 | GET | /api/v1/rag/documents | `rag_documents` | scinsight :8100 | F1995 create_router.reader() | F0421 Database.query() |  |
| F2016 | POST | /api/v1/decisions | `create_decision` | scinsight :8100 | F1995 create_router.reader(), F0187 DecisionCreateRequest | F0777 Security.require(), F0333 Service.create_decision() | Flowise Custom Tool · save_recommendation, Supervisor-Agentflow · 7 · Save recommendation |
| F2017 | GET | /api/v1/decisions | `list_decisions` | scinsight :8100 | F1995 create_router.reader() | F0336 Service.list_decisions() |  |
| F2018 | GET | /api/v1/decisions/{rec_id} | `get_decision` | scinsight :8100 | F1995 create_router.reader() | F0335 Service.get_decision() | Flowise Custom Tool · get_decision_status |
| F2019 | POST | /api/v1/decisions/{rec_id}/review | `review` | scinsight :8100 | F1994 create_router.principal(), F0188 ReviewRequest | F0337 Service.review() |  |
| F2020 | POST | /api/v1/decisions/{rec_id}/withdraw | `withdraw` | scinsight :8100 | F1995 create_router.reader() | F0339 Service.withdraw() | Supervisor-Agentflow · 10 · Withdraw |
| F2021 | POST | /api/v1/decisions/{rec_id}/sap-execution | `sap_execution` | scinsight :8100 | F1994 create_router.principal(), F0189 SapExecutionRequest | F0340 Service.record_sap_execution() |  |
| F2022 | POST | /api/v1/outcomes/reconcile | `reconcile` | scinsight :8100 | F1994 create_router.principal(), F0171 ReconcileRequest | F0341 Service.reconcile() | Decision-Outcome-Learning-Agentflow · 3 · Check the outcome with SAP data |
| F2023 | GET | /api/v1/learning/metrics | `learning_metrics` | scinsight :8100 | F1995 create_router.reader() | F0343 Service.learning_metrics() | Flowise Custom Tool · get_verified_outcomes, Decision-Outcome-Learning-Agentflow · 3 · Check the outcome with SAP data |
| F2024 | POST | /api/v1/learning/train-lead-time-model | `train` | scinsight :8100 | F1994 create_router.principal() | F0777 Security.require(), F0534 train_lead_time_model(), F0779 Security.audit() |  |
| F2025 | POST | /api/v1/learning/models/{model_id}/promote | `promote` | scinsight :8100 | F1994 create_router.principal() | F0777 Security.require(), F0535 promote(), F0779 Security.audit() |  |
| F2026 | POST | /api/v1/learning/retraining-requests | `retraining` | scinsight :8100 | F1995 create_router.reader(), F0191 RetrainingRequest | F0537 retraining_request(), F0779 Security.audit() |  |
| F2027 | GET | /api/v1/audit | `audit` | scinsight :8100 | F1994 create_router.principal() | F0777 Security.require(), F0781 Security.verify_chain(), F0421 Database.query() |  |
| F1824 | GET | /api/v1/rag-tuning/config | `get_config` | scinsight :8100 | F1820 register.admin() | F1905 Registry.get_active_rag_config() |  |
| F1825 | PUT | /api/v1/rag-tuning/draft | `save_draft` | scinsight :8100 | F1820 register.admin(), F1810 DraftRequest | F1908 Registry.save_draft_config(), F1821 register.audit() |  |
| F1826 | GET | /api/v1/rag-tuning/history | `history` | scinsight :8100 | F1820 register.admin() | F1894 list_indexes() |  |
| F1827 | GET | /api/v1/rag-tuning/diff/{config_id} | `config_diff` | scinsight :8100 | F1820 register.admin() | F1822 register.cfg_of(), F1857 diff(), F1905 Registry.get_active_rag_config() |  |
| F1828 | GET | /api/v1/rag-tuning/documents | `list_documents` | scinsight :8100 | F1820 register.admin() | F1860 inventory() |  |
| F1829 | POST | /api/v1/rag-tuning/metadata/validate | `validate_metadata` | scinsight :8100 | F1820 register.admin() | F1860 inventory() |  |
| F1830 | GET | /api/v1/rag-tuning/documents/{doc_id}/source | `document_source` | scinsight :8100 | F1820 register.admin() | F1863 source_text() |  |
| F1831 | POST | /api/v1/rag-tuning/chunks/preview | `chunk_preview` | scinsight :8100 | F1820 register.admin(), F1811 PreviewRequest | F1863 source_text(), F1853 preview_document_chunks() |  |
| F1832 | GET | /api/v1/rag-tuning/embedding-models | `embedding_models` | scinsight :8100 | F1820 register.admin() | F1806 KnowledgeBase.active(), F1867 list_supported_embedding_models() |  |
| F1833 | POST | /api/v1/rag-tuning/embedding-models/test | `test_model` | scinsight :8100 | F1820 register.admin(), F1813 ModelTestRequest | F1865 approved(), F1821 register.audit(), F1823 register.job(), F1869 test_model() |  |
| F1834 | POST | /api/v1/rag-tuning/index/build-candidate | `build_candidate` | scinsight :8100 | F1820 register.admin(), F1814 ConfigRef | F1822 register.cfg_of(), F1821 register.audit(), F1823 register.job(), F1892 build_candidate_index() |  |
| F1835 | GET | /api/v1/rag-tuning/jobs/{job_id} | `get_job` | scinsight :8100 | F1820 register.admin() |  |  |
| F1836 | POST | /api/v1/rag-tuning/retrieve/preview | `retrieve_preview` | scinsight :8100 | F1820 register.admin(), F1812 RetrieveRequest | F1822 register.cfg_of(), F1806 KnowledgeBase.active(), F0766 KnowledgeBase.search() |  |
| F1838 | POST | /api/v1/rag-tuning/evaluate | `evaluate` | scinsight :8100 | F1820 register.admin(), F1815 EvaluateRequest | F1822 register.cfg_of(), F1870 load_dataset(), F1821 register.audit(), F1823 register.job(), F1837 register._benchmark() |  |
| F1839 | POST | /api/v1/rag-tuning/evaluate/grid | `evaluate_grid` | scinsight :8100 | F1820 register.admin(), F1816 GridRequest | F1905 Registry.get_active_rag_config(), F1865 approved(), F1858 index_signature(), F1870 load_dataset(), F1914 Registry.experiments(), F1908 Registry.save_draft |  |
| F1840 | GET | /api/v1/rag-tuning/experiments | `list_experiments` | scinsight :8100 | F1820 register.admin() | F1914 Registry.experiments() |  |
| F1841 | GET | /api/v1/rag-tuning/experiments/compare | `compare` | scinsight :8100 | F1820 register.admin() | F1877 compare_experiments(), F1915 Registry.experiment() |  |
| F1842 | GET | /api/v1/rag-tuning/experiments/{exp_id} | `get_experiment` | scinsight :8100 | F1820 register.admin() | F1915 Registry.experiment() |  |
| F1843 | POST | /api/v1/rag-tuning/validate | `validate` | scinsight :8100 | F1820 register.admin(), F1814 ConfigRef | F1822 register.cfg_of(), F1895 validate_config() |  |
| F1844 | POST | /api/v1/rag-tuning/publish | `publish` | scinsight :8100 | F1820 register.admin(), F1814 ConfigRef | F0777 Security.require(), F1822 register.cfg_of(), F1898 publish_rag_config(), F1821 register.audit() |  |
| F1845 | POST | /api/v1/rag-tuning/rollback | `rollback` | scinsight :8100 | F1820 register.admin(), F1814 ConfigRef | F0777 Security.require(), F1822 register.cfg_of(), F1899 rollback_rag_config(), F1821 register.audit() |  |
| F1846 | GET | /api/v1/rag-tuning/flowise | `flowise_status` | scinsight :8100 | F1820 register.admin() |  |  |
| F1847 | GET | /api/v1/rag-tuning/metrics | `metrics` | scinsight :8100 | F1820 register.admin() | F0421 Database.query() |  |
| F1964 | GET | /health | `health` | gateway :8000 |  |  |  |
| F1965 | GET | /api/v1/stock/{sku} | `get_stock` | gateway :8000 | F1962 create_app.reader() |  |  |
| F1966 | POST | /api/v1/adjustments | `adjust` | gateway :8000 | F1963 create_app.manager(), F1959 ItemRequest |  |  |
| F1967 | POST/PUT/PATCH/DELETE | /api/v1/sap/{path:path} | `sap_read_only` | gateway :8000 | F1961 create_app.principal() |  |  |
| F1968 | GET | /api/v1/audit | `read_audit` | gateway :8000 | F1963 create_app.manager() |  |  |
| F2030 | GET | /health | `health` | gateway :8000 |  |  |  |
| F2031 | GET | /api/v1/stock/{sku} | `get_stock` | gateway :8000 | F2029 create_inner_router.caller() |  |  |
| F2033 | GET | /health | `health` | gateway :8000 |  |  |  |
