# 01_fastapi/endpoints (generated)

Modules: `backend/app/main.py`, `backend/scinsight/app.py`

| ID | Function / class | Kind | Status | Original | Annotated copy | Summary |
|---|---|---|---|---|---|---|
| F0016 | `_expectation` | function | used | [backend/app/main.py:69](../../../backend/app/main.py#L69) | [annotated](../../01_fastapi/endpoints/app_main.py) | Plain-language expected result of one executed action (what the outcome check wi |
| F0017 | `create_app` | function | used | [backend/app/main.py:79](../../../backend/app/main.py#L79) | [annotated](../../01_fastapi/endpoints/app_main.py) |  |
| F0018 | `create_app.request_context` | nested | used | [backend/app/main.py:110](../../../backend/app/main.py#L110) | [annotated](../../01_fastapi/endpoints/app_main.py) |  |
| F0019 | `create_app.principal` | nested | used | [backend/app/main.py:130](../../../backend/app/main.py#L130) | [annotated](../../01_fastapi/endpoints/app_main.py) |  |
| F0020 | `create_app.manager` | nested | used | [backend/app/main.py:145](../../../backend/app/main.py#L145) | [annotated](../../01_fastapi/endpoints/app_main.py) |  |
| F0021 | `create_app.reader` | nested | used | [backend/app/main.py:153](../../../backend/app/main.py#L153) | [annotated](../../01_fastapi/endpoints/app_main.py) |  |
| F0022 | `create_app.watch_owner` | nested | used | [backend/app/main.py:156](../../../backend/app/main.py#L156) | [annotated](../../01_fastapi/endpoints/app_main.py) |  |
| F0023 | `create_app.save` | nested | used | [backend/app/main.py:159](../../../backend/app/main.py#L159) | [annotated](../../01_fastapi/endpoints/app_main.py) |  |
| F0024 | `create_app.value_error_handler` | nested | used | [backend/app/main.py:171](../../../backend/app/main.py#L171) | [annotated](../../01_fastapi/endpoints/app_main.py) |  |
| F0025 | `create_app.health` | route | used | [backend/app/main.py:176](../../../backend/app/main.py#L176) | [annotated](../../01_fastapi/endpoints/app_main.py) |  |
| F0026 | `create_app.ready` | route | used | [backend/app/main.py:180](../../../backend/app/main.py#L180) | [annotated](../../01_fastapi/endpoints/app_main.py) |  |
| F0027 | `create_app.metrics` | route | used | [backend/app/main.py:184](../../../backend/app/main.py#L184) | [annotated](../../01_fastapi/endpoints/app_main.py) |  |
| F0028 | `create_app.public_config` | route | used | [backend/app/main.py:188](../../../backend/app/main.py#L188) | [annotated](../../01_fastapi/endpoints/app_main.py) | Non-secret links for the dashboard header. |
| F0029 | `create_app.demo_session` | route | used | [backend/app/main.py:218](../../../backend/app/main.py#L218) | [annotated](../../01_fastapi/endpoints/app_main.py) | Local demo only (DEMO_AUTO_LOGIN=true): returns the demo planner and manager key |
| F0030 | `create_app._public` | nested | used | [backend/app/main.py:227](../../../backend/app/main.py#L227) | [annotated](../../01_fastapi/endpoints/app_main.py) |  |
| F0031 | `create_app.status` | route | used | [backend/app/main.py:230](../../../backend/app/main.py#L230) | [annotated](../../01_fastapi/endpoints/app_main.py) |  |
| F0032 | `create_app.status.probe` | nested | used | [backend/app/main.py:234](../../../backend/app/main.py#L234) | [annotated](../../01_fastapi/endpoints/app_main.py) |  |
| F0033 | `create_app.snapshot` | route | used | [backend/app/main.py:266](../../../backend/app/main.py#L266) | [annotated](../../01_fastapi/endpoints/app_main.py) |  |
| F0034 | `create_app.tenant_catalogue` | route | used | [backend/app/main.py:279](../../../backend/app/main.py#L279) | [annotated](../../01_fastapi/endpoints/app_main.py) | Industries and customers for the top-bar selector (send the id back as the X-Ten |
| F0035 | `create_app.network_map` | route | used | [backend/app/main.py:284](../../../backend/app/main.py#L284) | [annotated](../../01_fastapi/endpoints/app_main.py) |  |
| F0036 | `create_app.sap_metadata` | route | used | [backend/app/main.py:289](../../../backend/app/main.py#L289) | [annotated](../../01_fastapi/endpoints/app_main.py) |  |
| F0037 | `create_app.sap_sandbox_documents` | route | used | [backend/app/main.py:294](../../../backend/app/main.py#L294) | [annotated](../../01_fastapi/endpoints/app_main.py) |  |
| F0038 | `create_app.sap_odata` | route | used | [backend/app/main.py:300](../../../backend/app/main.py#L300) | [annotated](../../01_fastapi/endpoints/app_main.py) |  |
| F0039 | `create_app.block_sap_write` | route | used | [backend/app/main.py:315](../../../backend/app/main.py#L315) | [annotated](../../01_fastapi/endpoints/app_main.py) |  |
| F0040 | `create_app.factory_readiness` | route | used | [backend/app/main.py:322](../../../backend/app/main.py#L322) | [annotated](../../01_fastapi/endpoints/app_main.py) |  |
| F0041 | `create_app.stock_balance` | route | used | [backend/app/main.py:327](../../../backend/app/main.py#L327) | [annotated](../../01_fastapi/endpoints/app_main.py) |  |
| F0042 | `create_app.demand_forecast` | route | used | [backend/app/main.py:331](../../../backend/app/main.py#L331) | [annotated](../../01_fastapi/endpoints/app_main.py) |  |
| F0043 | `create_app.what_if` | route | used | [backend/app/main.py:335](../../../backend/app/main.py#L335) | [annotated](../../01_fastapi/endpoints/app_main.py) |  |
| F0044 | `create_app.supplier_risk` | route | used | [backend/app/main.py:340](../../../backend/app/main.py#L340) | [annotated](../../01_fastapi/endpoints/app_main.py) |  |
| F0045 | `create_app.quality` | route | used | [backend/app/main.py:344](../../../backend/app/main.py#L344) | [annotated](../../01_fastapi/endpoints/app_main.py) |  |
| F0046 | `create_app.logistics` | route | used | [backend/app/main.py:348](../../../backend/app/main.py#L348) | [annotated](../../01_fastapi/endpoints/app_main.py) |  |
| F0047 | `create_app.sales_orders` | route | used | [backend/app/main.py:352](../../../backend/app/main.py#L352) | [annotated](../../01_fastapi/endpoints/app_main.py) |  |
| F0048 | `create_app.stocktake` | route | used | [backend/app/main.py:356](../../../backend/app/main.py#L356) | [annotated](../../01_fastapi/endpoints/app_main.py) |  |
| F0049 | `create_app.forecast_vs_actuals` | route | used | [backend/app/main.py:360](../../../backend/app/main.py#L360) | [annotated](../../01_fastapi/endpoints/app_main.py) |  |
| F0050 | `create_app.production_overview` | route | used | [backend/app/main.py:365](../../../backend/app/main.py#L365) | [annotated](../../01_fastapi/endpoints/app_main.py) |  |
| F0051 | `create_app.products` | route | used | [backend/app/main.py:370](../../../backend/app/main.py#L370) | [annotated](../../01_fastapi/endpoints/app_main.py) |  |
| F0052 | `create_app.product` | route | used | [backend/app/main.py:375](../../../backend/app/main.py#L375) | [annotated](../../01_fastapi/endpoints/app_main.py) |  |
| F0053 | `create_app.role_catalogue` | route | used | [backend/app/main.py:381](../../../backend/app/main.py#L381) | [annotated](../../01_fastapi/endpoints/app_main.py) |  |
| F0054 | `create_app.role_view` | route | used | [backend/app/main.py:386](../../../backend/app/main.py#L386) | [annotated](../../01_fastapi/endpoints/app_main.py) |  |
| F0055 | `create_app.north_star` | route | used | [backend/app/main.py:393](../../../backend/app/main.py#L393) | [annotated](../../01_fastapi/endpoints/app_main.py) |  |
| F0056 | `create_app.learning` | route | used | [backend/app/main.py:398](../../../backend/app/main.py#L398) | [annotated](../../01_fastapi/endpoints/app_main.py) |  |
| F0057 | `create_app.moat_view` | route | used | [backend/app/main.py:403](../../../backend/app/main.py#L403) | [annotated](../../01_fastapi/endpoints/app_main.py) | Customer data intelligence flywheel, moat evidence, consent gate and the five mo |
| F0058 | `create_app.moat_consent` | route | used | [backend/app/main.py:409](../../../backend/app/main.py#L409) | [annotated](../../01_fastapi/endpoints/app_main.py) | The customer decides whether its data may contribute to industry learning (manag |
| F0059 | `create_app.record_outcome` | route | used | [backend/app/main.py:417](../../../backend/app/main.py#L417) | [annotated](../../01_fastapi/endpoints/app_main.py) | Record the real result of an executed recommendation against an SAP document (de |
| F0060 | `create_app.sales_outlook` | route | used | [backend/app/main.py:431](../../../backend/app/main.py#L431) | [annotated](../../01_fastapi/endpoints/app_main.py) |  |
| F0061 | `create_app.product_brief` | route | used | [backend/app/main.py:436](../../../backend/app/main.py#L436) | [annotated](../../01_fastapi/endpoints/app_main.py) |  |
| F0062 | `create_app.sites` | route | used | [backend/app/main.py:441](../../../backend/app/main.py#L441) | [annotated](../../01_fastapi/endpoints/app_main.py) |  |
| F0063 | `create_app.site` | route | used | [backend/app/main.py:446](../../../backend/app/main.py#L446) | [annotated](../../01_fastapi/endpoints/app_main.py) |  |
| F0064 | `create_app.dashboards_list` | route | used | [backend/app/main.py:451](../../../backend/app/main.py#L451) | [annotated](../../01_fastapi/endpoints/app_main.py) |  |
| F0065 | `create_app.dashboard` | route | used | [backend/app/main.py:455](../../../backend/app/main.py#L455) | [annotated](../../01_fastapi/endpoints/app_main.py) |  |
| F0066 | `create_app.get_insights` | route | used | [backend/app/main.py:460](../../../backend/app/main.py#L460) | [annotated](../../01_fastapi/endpoints/app_main.py) |  |
| F0067 | `create_app.watch_kinds` | route | used | [backend/app/main.py:468](../../../backend/app/main.py#L468) | [annotated](../../01_fastapi/endpoints/app_main.py) |  |
| F0068 | `create_app.list_watches` | route | used | [backend/app/main.py:472](../../../backend/app/main.py#L472) | [annotated](../../01_fastapi/endpoints/app_main.py) |  |
| F0069 | `create_app.create_watch` | route | used | [backend/app/main.py:476](../../../backend/app/main.py#L476) | [annotated](../../01_fastapi/endpoints/app_main.py) |  |
| F0070 | `create_app.delete_watch` | route | used | [backend/app/main.py:486](../../../backend/app/main.py#L486) | [annotated](../../01_fastapi/endpoints/app_main.py) |  |
| F0071 | `create_app.evaluate_watches` | route | used | [backend/app/main.py:492](../../../backend/app/main.py#L492) | [annotated](../../01_fastapi/endpoints/app_main.py) |  |
| F0072 | `create_app.get_analysis` | route | used | [backend/app/main.py:502](../../../backend/app/main.py#L502) | [annotated](../../01_fastapi/endpoints/app_main.py) |  |
| F0073 | `create_app.inventory` | route | used | [backend/app/main.py:510](../../../backend/app/main.py#L510) | [annotated](../../01_fastapi/endpoints/app_main.py) |  |
| F0074 | `create_app.supplier_scorecard` | route | used | [backend/app/main.py:515](../../../backend/app/main.py#L515) | [annotated](../../01_fastapi/endpoints/app_main.py) |  |
| F0075 | `create_app.kpis` | route | used | [backend/app/main.py:520](../../../backend/app/main.py#L520) | [annotated](../../01_fastapi/endpoints/app_main.py) |  |
| F0076 | `create_app.rag_search` | route | used | [backend/app/main.py:526](../../../backend/app/main.py#L526) | [annotated](../../01_fastapi/endpoints/app_main.py) |  |
| F0077 | `create_app.rag_search_get` | route | used | [backend/app/main.py:531](../../../backend/app/main.py#L531) | [annotated](../../01_fastapi/endpoints/app_main.py) | Same search via query parameters — used by the Flowise AgentFlow RAG step (no JS |
| F0078 | `create_app.embeddings` | route | used | [backend/app/main.py:539](../../../backend/app/main.py#L539) | [annotated](../../01_fastapi/endpoints/app_main.py) | Lets Flowise (OpenAI Embeddings Custom node) index and query with exactly the em |
| F0079 | `create_app.embeddings.encode` | nested | used | [backend/app/main.py:548](../../../backend/app/main.py#L548) | [annotated](../../01_fastapi/endpoints/app_main.py) |  |
| F0080 | `create_app.rag_stats` | route | used | [backend/app/main.py:556](../../../backend/app/main.py#L556) | [annotated](../../01_fastapi/endpoints/app_main.py) |  |
| F0081 | `create_app.rag_add` | route | used | [backend/app/main.py:561](../../../backend/app/main.py#L561) | [annotated](../../01_fastapi/endpoints/app_main.py) |  |
| F0082 | `create_app._graph_call` | nested | used | [backend/app/main.py:568](../../../backend/app/main.py#L568) | [annotated](../../01_fastapi/endpoints/app_main.py) |  |
| F0083 | `create_app.chat` | route | used | [backend/app/main.py:576](../../../backend/app/main.py#L576) | [annotated](../../01_fastapi/endpoints/app_main.py) |  |
| F0084 | `create_app._agentflow_view` | nested | used | [backend/app/main.py:603](../../../backend/app/main.py#L603) | [annotated](../../01_fastapi/endpoints/app_main.py) |  |
| F0085 | `create_app.langgraph_agentflow` | route | used | [backend/app/main.py:627](../../../backend/app/main.py#L627) | [annotated](../../01_fastapi/endpoints/app_main.py) |  |
| F0086 | `create_app.langgraph_agentflow_resume` | route | used | [backend/app/main.py:634](../../../backend/app/main.py#L634) | [annotated](../../01_fastapi/endpoints/app_main.py) |  |
| F0087 | `create_app.business_start` | route | used | [backend/app/main.py:640](../../../backend/app/main.py#L640) | [annotated](../../01_fastapi/endpoints/app_main.py) |  |
| F0088 | `create_app.business_resume` | route | used | [backend/app/main.py:647](../../../backend/app/main.py#L647) | [annotated](../../01_fastapi/endpoints/app_main.py) |  |
| F0089 | `create_app.current_harness` | nested | used | [backend/app/main.py:660](../../../backend/app/main.py#L660) | [annotated](../../01_fastapi/endpoints/app_main.py) |  |
| F0090 | `create_app.deep_harness` | route | used | [backend/app/main.py:664](../../../backend/app/main.py#L664) | [annotated](../../01_fastapi/endpoints/app_main.py) |  |
| F0091 | `create_app.set_deep_harness` | route | used | [backend/app/main.py:673](../../../backend/app/main.py#L673) | [annotated](../../01_fastapi/endpoints/app_main.py) |  |
| F0092 | `create_app.supplier_research` | route | used | [backend/app/main.py:679](../../../backend/app/main.py#L679) | [annotated](../../01_fastapi/endpoints/app_main.py) |  |
| F0093 | `create_app._flow_id` | nested | used | [backend/app/main.py:703](../../../backend/app/main.py#L703) | [annotated](../../01_fastapi/endpoints/app_main.py) |  |
| F0094 | `create_app.flowise_predict` | route | used | [backend/app/main.py:717](../../../backend/app/main.py#L717) | [annotated](../../01_fastapi/endpoints/app_main.py) |  |
| F0095 | `create_app.submit_recommendation` | route | used | [backend/app/main.py:755](../../../backend/app/main.py#L755) | [annotated](../../01_fastapi/endpoints/app_main.py) |  |
| F0096 | `create_app.submit_from_agent` | route | used | [backend/app/main.py:764](../../../backend/app/main.py#L764) | [annotated](../../01_fastapi/endpoints/app_main.py) |  |
| F0097 | `create_app.recommendations` | route | used | [backend/app/main.py:779](../../../backend/app/main.py#L779) | [annotated](../../01_fastapi/endpoints/app_main.py) |  |
| F0098 | `create_app.decide` | route | used | [backend/app/main.py:784](../../../backend/app/main.py#L784) | [annotated](../../01_fastapi/endpoints/app_main.py) |  |
| F0099 | `create_app.execute` | route | used | [backend/app/main.py:798](../../../backend/app/main.py#L798) | [annotated](../../01_fastapi/endpoints/app_main.py) | 1-click execution of an ACCEPTED recommendation into the SAP sandbox (manager on |
| F0100 | `create_app.sap_documents` | route | used | [backend/app/main.py:825](../../../backend/app/main.py#L825) | [annotated](../../01_fastapi/endpoints/app_main.py) |  |
| F0101 | `create_app.audit` | route | used | [backend/app/main.py:830](../../../backend/app/main.py#L830) | [annotated](../../01_fastapi/endpoints/app_main.py) |  |
| F0102 | `create_app.poc_sap_inventory` | route | used | [backend/app/main.py:839](../../../backend/app/main.py#L839) | [annotated](../../01_fastapi/endpoints/app_main.py) |  |
| F0103 | `create_app.poc_sap_production_orders` | route | used | [backend/app/main.py:845](../../../backend/app/main.py#L845) | [annotated](../../01_fastapi/endpoints/app_main.py) |  |
| F0104 | `create_app.poc_forecast_demand` | route | used | [backend/app/main.py:851](../../../backend/app/main.py#L851) | [annotated](../../01_fastapi/endpoints/app_main.py) |  |
| F0105 | `create_app.poc_forecast_lead_time` | route | used | [backend/app/main.py:855](../../../backend/app/main.py#L855) | [annotated](../../01_fastapi/endpoints/app_main.py) |  |
| F0106 | `create_app.poc_material_readiness` | route | used | [backend/app/main.py:859](../../../backend/app/main.py#L859) | [annotated](../../01_fastapi/endpoints/app_main.py) |  |
| F0107 | `create_app.poc_warehouse_transfer` | route | used | [backend/app/main.py:864](../../../backend/app/main.py#L864) | [annotated](../../01_fastapi/endpoints/app_main.py) |  |
| F0108 | `create_app.poc_decisions` | route | used | [backend/app/main.py:868](../../../backend/app/main.py#L868) | [annotated](../../01_fastapi/endpoints/app_main.py) |  |
| F0109 | `create_app.poc_human_review` | route | used | [backend/app/main.py:872](../../../backend/app/main.py#L872) | [annotated](../../01_fastapi/endpoints/app_main.py) |  |
| F0110 | `create_app.poc_reconcile` | route | used | [backend/app/main.py:876](../../../backend/app/main.py#L876) | [annotated](../../01_fastapi/endpoints/app_main.py) |  |
| F0111 | `create_app.poc_model_performance` | route | used | [backend/app/main.py:902](../../../backend/app/main.py#L902) | [annotated](../../01_fastapi/endpoints/app_main.py) |  |
| F0112 | `create_app` | function | used | [backend/scinsight/app.py:34](../../../backend/scinsight/app.py#L34) | [annotated](../../01_fastapi/endpoints/scinsight_app.py) |  |
| F0113 | `create_app.principal` | nested | used | [backend/scinsight/app.py:57](../../../backend/scinsight/app.py#L57) | [annotated](../../01_fastapi/endpoints/scinsight_app.py) |  |
| F0114 | `create_app.reader` | nested | used | [backend/scinsight/app.py:62](../../../backend/scinsight/app.py#L62) | [annotated](../../01_fastapi/endpoints/scinsight_app.py) |  |
| F0115 | `create_app.biz_date` | nested | used | [backend/scinsight/app.py:66](../../../backend/scinsight/app.py#L66) | [annotated](../../01_fastapi/endpoints/scinsight_app.py) |  |
| F0116 | `create_app.health` | route | used | [backend/scinsight/app.py:69](../../../backend/scinsight/app.py#L69) | [annotated](../../01_fastapi/endpoints/scinsight_app.py) |  |
| F0117 | `create_app.context` | route | used | [backend/scinsight/app.py:75](../../../backend/scinsight/app.py#L75) | [annotated](../../01_fastapi/endpoints/scinsight_app.py) |  |
| F0118 | `create_app.validate_context` | route | used | [backend/scinsight/app.py:81](../../../backend/scinsight/app.py#L81) | [annotated](../../01_fastapi/endpoints/scinsight_app.py) |  |
| F0119 | `create_app.sap_inventory` | route | used | [backend/scinsight/app.py:90](../../../backend/scinsight/app.py#L90) | [annotated](../../01_fastapi/endpoints/scinsight_app.py) |  |
| F0120 | `create_app.sap_bom` | route | used | [backend/scinsight/app.py:95](../../../backend/scinsight/app.py#L95) | [annotated](../../01_fastapi/endpoints/scinsight_app.py) |  |
| F0121 | `create_app.sap_production_orders` | route | used | [backend/scinsight/app.py:99](../../../backend/scinsight/app.py#L99) | [annotated](../../01_fastapi/endpoints/scinsight_app.py) |  |
| F0122 | `create_app.sap_purchase_orders` | route | used | [backend/scinsight/app.py:103](../../../backend/scinsight/app.py#L103) | [annotated](../../01_fastapi/endpoints/scinsight_app.py) |  |
| F0123 | `create_app.sap_warehouses` | route | used | [backend/scinsight/app.py:108](../../../backend/scinsight/app.py#L108) | [annotated](../../01_fastapi/endpoints/scinsight_app.py) |  |
| F0124 | `create_app.sap_suppliers` | route | used | [backend/scinsight/app.py:112](../../../backend/scinsight/app.py#L112) | [annotated](../../01_fastapi/endpoints/scinsight_app.py) |  |
| F0125 | `create_app.sap_write_blocked` | route | used | [backend/scinsight/app.py:116](../../../backend/scinsight/app.py#L116) | [annotated](../../01_fastapi/endpoints/scinsight_app.py) |  |
| F0126 | `create_app.material_readiness` | route | used | [backend/scinsight/app.py:122](../../../backend/scinsight/app.py#L122) | [annotated](../../01_fastapi/endpoints/scinsight_app.py) |  |
| F0127 | `create_app.warehouse_balancing` | route | used | [backend/scinsight/app.py:126](../../../backend/scinsight/app.py#L126) | [annotated](../../01_fastapi/endpoints/scinsight_app.py) |  |
| F0128 | `create_app.replenishment` | route | used | [backend/scinsight/app.py:130](../../../backend/scinsight/app.py#L130) | [annotated](../../01_fastapi/endpoints/scinsight_app.py) |  |
| F0129 | `create_app.forecast_demand` | route | used | [backend/scinsight/app.py:134](../../../backend/scinsight/app.py#L134) | [annotated](../../01_fastapi/endpoints/scinsight_app.py) |  |
| F0130 | `create_app.forecast_lead_time` | route | used | [backend/scinsight/app.py:138](../../../backend/scinsight/app.py#L138) | [annotated](../../01_fastapi/endpoints/scinsight_app.py) |  |
| F0131 | `create_app.quality_check` | route | used | [backend/scinsight/app.py:142](../../../backend/scinsight/app.py#L142) | [annotated](../../01_fastapi/endpoints/scinsight_app.py) |  |
| F0132 | `create_app.calculation` | route | used | [backend/scinsight/app.py:146](../../../backend/scinsight/app.py#L146) | [annotated](../../01_fastapi/endpoints/scinsight_app.py) |  |
| F0133 | `create_app.rag_search` | route | used | [backend/scinsight/app.py:151](../../../backend/scinsight/app.py#L151) | [annotated](../../01_fastapi/endpoints/scinsight_app.py) |  |
| F0134 | `create_app.rag_documents` | route | used | [backend/scinsight/app.py:157](../../../backend/scinsight/app.py#L157) | [annotated](../../01_fastapi/endpoints/scinsight_app.py) |  |
| F0135 | `create_app.create_decision` | route | used | [backend/scinsight/app.py:163](../../../backend/scinsight/app.py#L163) | [annotated](../../01_fastapi/endpoints/scinsight_app.py) |  |
| F0136 | `create_app.list_decisions` | route | used | [backend/scinsight/app.py:168](../../../backend/scinsight/app.py#L168) | [annotated](../../01_fastapi/endpoints/scinsight_app.py) |  |
| F0137 | `create_app.get_decision` | route | used | [backend/scinsight/app.py:172](../../../backend/scinsight/app.py#L172) | [annotated](../../01_fastapi/endpoints/scinsight_app.py) |  |
| F0138 | `create_app.review` | route | used | [backend/scinsight/app.py:176](../../../backend/scinsight/app.py#L176) | [annotated](../../01_fastapi/endpoints/scinsight_app.py) |  |
| F0139 | `create_app.withdraw` | route | used | [backend/scinsight/app.py:180](../../../backend/scinsight/app.py#L180) | [annotated](../../01_fastapi/endpoints/scinsight_app.py) |  |
| F0140 | `create_app.sap_execution` | route | used | [backend/scinsight/app.py:184](../../../backend/scinsight/app.py#L184) | [annotated](../../01_fastapi/endpoints/scinsight_app.py) |  |
| F0141 | `create_app.reconcile` | route | used | [backend/scinsight/app.py:189](../../../backend/scinsight/app.py#L189) | [annotated](../../01_fastapi/endpoints/scinsight_app.py) |  |
| F0142 | `create_app.learning_metrics` | route | used | [backend/scinsight/app.py:193](../../../backend/scinsight/app.py#L193) | [annotated](../../01_fastapi/endpoints/scinsight_app.py) |  |
| F0143 | `create_app.train` | route | used | [backend/scinsight/app.py:197](../../../backend/scinsight/app.py#L197) | [annotated](../../01_fastapi/endpoints/scinsight_app.py) |  |
| F0144 | `create_app.promote` | route | used | [backend/scinsight/app.py:204](../../../backend/scinsight/app.py#L204) | [annotated](../../01_fastapi/endpoints/scinsight_app.py) |  |
| F0145 | `create_app.retraining` | route | used | [backend/scinsight/app.py:211](../../../backend/scinsight/app.py#L211) | [annotated](../../01_fastapi/endpoints/scinsight_app.py) |  |
| F0146 | `create_app.audit` | route | used | [backend/scinsight/app.py:217](../../../backend/scinsight/app.py#L217) | [annotated](../../01_fastapi/endpoints/scinsight_app.py) |  |
