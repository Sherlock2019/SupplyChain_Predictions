# FastAPI endpoints (generated)

Both apps declare routes directly on `app` (no `APIRouter`, no prefixes), so the decorator path is the full path.

| ID | Method | Path | Handler | App | Depends / body model | Calls | Called from Flowise |
|---|---|---|---|---|---|---|---|
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
| F0116 | GET | /health | `health` | scinsight :8100 |  |  |  |
| F0117 | GET | /api/v1/context | `context` | scinsight :8100 | F0114 create_app.reader() | F0313 Service.snapshot() |  |
| F0118 | POST | /api/v1/context/validate | `validate_context` | scinsight :8100 | F0114 create_app.reader(), F0178 ContextRequest | F0313 Service.snapshot(), F0779 Security.audit(), F0322 Service.catalog() | Decision-Outcome-Learning-Agentflow · 2 · Check access, Factory-Planning-Agentflow · 2 · Check access, Inventory-Optimizer-Agentflow · 2 · Check access, Logisti |
| F0119 | GET | /api/v1/sap/inventory | `sap_inventory` | scinsight :8100 | F0114 create_app.reader() | F0319 Service.inventory() | Flowise Custom Tool · get_sap_inventory |
| F0120 | GET | /api/v1/sap/bom/{sku} | `sap_bom` | scinsight :8100 | F0114 create_app.reader() | F0320 Service.bom() | Flowise Custom Tool · get_material_bom |
| F0121 | GET | /api/v1/sap/production-orders | `sap_production_orders` | scinsight :8100 | F0114 create_app.reader() | F0321 Service.table() | Flowise Custom Tool · get_production_orders, Factory-Planning-Agentflow · 4 · Calculate with SAP data |
| F0122 | GET | /api/v1/sap/purchase-orders | `sap_purchase_orders` | scinsight :8100 | F0114 create_app.reader() | F0321 Service.table() | Flowise Custom Tool · get_open_purchase_orders |
| F0123 | GET | /api/v1/sap/warehouses | `sap_warehouses` | scinsight :8100 | F0114 create_app.reader() | F0321 Service.table() |  |
| F0124 | GET | /api/v1/sap/suppliers | `sap_suppliers` | scinsight :8100 | F0114 create_app.reader() | F0323 Service.suppliers() | Procurement-Agentflow · 4 · Calculate with SAP data |
| F0125 | POST/PUT/PATCH/DELETE | /api/v1/sap/{path:path} | `sap_write_blocked` | scinsight :8100 | F0113 create_app.principal() | F0779 Security.audit() |  |
| F0126 | POST | /api/v1/optimizer/material-readiness | `material_readiness` | scinsight :8100 | F0114 create_app.reader(), F0179 MaterialReadinessRequest | F0325 Service.material_readiness() | Flowise Custom Tool · check_material_readiness, Factory-Planning-Agentflow · 4 · Calculate with SAP data |
| F0127 | POST | /api/v1/optimizer/warehouse-balancing | `warehouse_balancing` | scinsight :8100 | F0114 create_app.reader(), F0181 WarehouseBalancingRequest | F0327 Service.warehouse_balancing() | Flowise Custom Tool · optimize_warehouse_transfer, Logistics-Agentflow · 4 · Calculate with SAP data, Warehouse-Agentflow · 4 · Calculate with SAP data |
| F0128 | POST | /api/v1/optimizer/replenishment | `replenishment` | scinsight :8100 | F0114 create_app.reader(), F0182 ReplenishmentRequest | F0328 Service.replenishment() | Flowise Custom Tool · calculate_stock_cover, Inventory-Optimizer-Agentflow · 4 · Calculate with SAP data, Procurement-Agentflow · 4 · Calculate with SAP data |
| F0129 | POST | /api/v1/forecast/demand | `forecast_demand` | scinsight :8100 | F0114 create_app.reader(), F0183 DemandForecastRequest | F0330 Service.forecast_demand() | Flowise Custom Tool · forecast_demand, Inventory-Optimizer-Agentflow · 4 · Calculate with SAP data |
| F0130 | POST | /api/v1/forecast/lead-time | `forecast_lead_time` | scinsight :8100 | F0114 create_app.reader(), F0184 LeadTimeRequest | F0332 Service.lead_time() | Flowise Custom Tool · get_supplier_reliability, Procurement-Agentflow · 4 · Calculate with SAP data |
| F0131 | POST | /api/v1/quality/check-stock | `quality_check` | scinsight :8100 | F0114 create_app.reader(), F0185 QualityCheckRequest | F0329 Service.quality_check() | Flowise Custom Tool · check_batch_quality, Quality-Agentflow · 4 · Calculate with SAP data |
| F0132 | GET | /api/v1/calculations/{calculation_id} | `calculation` | scinsight :8100 | F0114 create_app.reader() | F0315 Service.calculation() |  |
| F0133 | POST | /api/v1/rag/search | `rag_search` | scinsight :8100 | F0114 create_app.reader(), F0186 RagSearchRequest | F0766 KnowledgeBase.search(), F0115 create_app.biz_date() | Flowise Custom Tool · search_supply_chain_policy, Factory-Planning-Agentflow · 5 · Policy search (RAG), Inventory-Optimizer-Agentflow · 5 · Policy search (RAG), |
| F0134 | GET | /api/v1/rag/documents | `rag_documents` | scinsight :8100 | F0114 create_app.reader() | F0421 Database.query() |  |
| F0135 | POST | /api/v1/decisions | `create_decision` | scinsight :8100 | F0114 create_app.reader(), F0187 DecisionCreateRequest | F0777 Security.require(), F0333 Service.create_decision() | Flowise Custom Tool · save_recommendation, Supervisor-Agentflow · 7 · Save recommendation |
| F0136 | GET | /api/v1/decisions | `list_decisions` | scinsight :8100 | F0114 create_app.reader() | F0336 Service.list_decisions() |  |
| F0137 | GET | /api/v1/decisions/{rec_id} | `get_decision` | scinsight :8100 | F0114 create_app.reader() | F0335 Service.get_decision() | Flowise Custom Tool · get_decision_status |
| F0138 | POST | /api/v1/decisions/{rec_id}/review | `review` | scinsight :8100 | F0113 create_app.principal(), F0188 ReviewRequest | F0337 Service.review() |  |
| F0139 | POST | /api/v1/decisions/{rec_id}/withdraw | `withdraw` | scinsight :8100 | F0114 create_app.reader() | F0339 Service.withdraw() | Supervisor-Agentflow · 10 · Withdraw |
| F0140 | POST | /api/v1/decisions/{rec_id}/sap-execution | `sap_execution` | scinsight :8100 | F0113 create_app.principal(), F0189 SapExecutionRequest | F0340 Service.record_sap_execution() |  |
| F0141 | POST | /api/v1/outcomes/reconcile | `reconcile` | scinsight :8100 | F0113 create_app.principal(), F0171 ReconcileRequest | F0341 Service.reconcile() | Decision-Outcome-Learning-Agentflow · 3 · Check the outcome with SAP data |
| F0142 | GET | /api/v1/learning/metrics | `learning_metrics` | scinsight :8100 | F0114 create_app.reader() | F0343 Service.learning_metrics() | Flowise Custom Tool · get_verified_outcomes, Decision-Outcome-Learning-Agentflow · 3 · Check the outcome with SAP data |
| F0143 | POST | /api/v1/learning/train-lead-time-model | `train` | scinsight :8100 | F0113 create_app.principal() | F0777 Security.require(), F0534 train_lead_time_model(), F0779 Security.audit() |  |
| F0144 | POST | /api/v1/learning/models/{model_id}/promote | `promote` | scinsight :8100 | F0113 create_app.principal() | F0777 Security.require(), F0535 promote(), F0779 Security.audit() |  |
| F0145 | POST | /api/v1/learning/retraining-requests | `retraining` | scinsight :8100 | F0114 create_app.reader(), F0191 RetrainingRequest | F0537 retraining_request(), F0779 Security.audit() |  |
| F0146 | GET | /api/v1/audit | `audit` | scinsight :8100 | F0113 create_app.principal() | F0777 Security.require(), F0781 Security.verify_chain(), F0421 Database.query() |  |
