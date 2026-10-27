# 01_fastapi/endpoints (generated)

Modules: `backend/app/main.py`, `backend/scinsight/app.py`

| ID | Function / class | Kind | Status | Original | Annotated copy | Summary |
|---|---|---|---|---|---|---|
| F0016 | `_expectation` | function | used | [backend/app/main.py:75](../../../backend/app/main.py#L75) | [annotated](../../01_fastapi/endpoints/app_main.py) | Plain-language expected result of one executed action (what the outcome check wi |
| F0017 | `create_app` | function | used | [backend/app/main.py:85](../../../backend/app/main.py#L85) | [annotated](../../01_fastapi/endpoints/app_main.py) |  |
| F0018 | `create_app.request_context` | nested | used | [backend/app/main.py:123](../../../backend/app/main.py#L123) | [annotated](../../01_fastapi/endpoints/app_main.py) |  |
| F0019 | `create_app.principal` | nested | used | [backend/app/main.py:143](../../../backend/app/main.py#L143) | [annotated](../../01_fastapi/endpoints/app_main.py) |  |
| F0020 | `create_app.manager` | nested | used | [backend/app/main.py:158](../../../backend/app/main.py#L158) | [annotated](../../01_fastapi/endpoints/app_main.py) |  |
| F0021 | `create_app.reader` | nested | used | [backend/app/main.py:166](../../../backend/app/main.py#L166) | [annotated](../../01_fastapi/endpoints/app_main.py) |  |
| F0022 | `create_app.watch_owner` | nested | used | [backend/app/main.py:169](../../../backend/app/main.py#L169) | [annotated](../../01_fastapi/endpoints/app_main.py) |  |
| F0023 | `create_app.save` | nested | used | [backend/app/main.py:172](../../../backend/app/main.py#L172) | [annotated](../../01_fastapi/endpoints/app_main.py) |  |
| F0024 | `create_app.value_error_handler` | nested | used | [backend/app/main.py:184](../../../backend/app/main.py#L184) | [annotated](../../01_fastapi/endpoints/app_main.py) |  |
| F0025 | `create_app.health` | route | used | [backend/app/main.py:189](../../../backend/app/main.py#L189) | [annotated](../../01_fastapi/endpoints/app_main.py) |  |
| F0026 | `create_app.ready` | route | used | [backend/app/main.py:193](../../../backend/app/main.py#L193) | [annotated](../../01_fastapi/endpoints/app_main.py) |  |
| F0027 | `create_app.metrics` | route | used | [backend/app/main.py:197](../../../backend/app/main.py#L197) | [annotated](../../01_fastapi/endpoints/app_main.py) |  |
| F0028 | `create_app.public_config` | route | used | [backend/app/main.py:201](../../../backend/app/main.py#L201) | [annotated](../../01_fastapi/endpoints/app_main.py) | Non-secret links for the dashboard header. |
| F0029 | `create_app.demo_session` | route | used | [backend/app/main.py:231](../../../backend/app/main.py#L231) | [annotated](../../01_fastapi/endpoints/app_main.py) | Local demo only (DEMO_AUTO_LOGIN=true): returns the demo planner and manager key |
| F0030 | `create_app._public` | nested | used | [backend/app/main.py:240](../../../backend/app/main.py#L240) | [annotated](../../01_fastapi/endpoints/app_main.py) |  |
| F0031 | `create_app.status` | route | used | [backend/app/main.py:243](../../../backend/app/main.py#L243) | [annotated](../../01_fastapi/endpoints/app_main.py) |  |
| F0032 | `create_app.status.probe` | nested | used | [backend/app/main.py:247](../../../backend/app/main.py#L247) | [annotated](../../01_fastapi/endpoints/app_main.py) |  |
| F0033 | `create_app.snapshot` | route | used | [backend/app/main.py:279](../../../backend/app/main.py#L279) | [annotated](../../01_fastapi/endpoints/app_main.py) |  |
| F0034 | `create_app.tenant_catalogue` | route | used | [backend/app/main.py:292](../../../backend/app/main.py#L292) | [annotated](../../01_fastapi/endpoints/app_main.py) | Industries and customers for the top-bar selector (send the id back as the X-Ten |
| F0035 | `create_app.network_map` | route | used | [backend/app/main.py:297](../../../backend/app/main.py#L297) | [annotated](../../01_fastapi/endpoints/app_main.py) |  |
| F0036 | `create_app.sap_metadata` | route | used | [backend/app/main.py:302](../../../backend/app/main.py#L302) | [annotated](../../01_fastapi/endpoints/app_main.py) |  |
| F0037 | `create_app.sap_sandbox_documents` | route | used | [backend/app/main.py:307](../../../backend/app/main.py#L307) | [annotated](../../01_fastapi/endpoints/app_main.py) |  |
| F0038 | `create_app.sap_odata` | route | used | [backend/app/main.py:313](../../../backend/app/main.py#L313) | [annotated](../../01_fastapi/endpoints/app_main.py) |  |
| F0039 | `create_app.block_sap_write` | route | used | [backend/app/main.py:328](../../../backend/app/main.py#L328) | [annotated](../../01_fastapi/endpoints/app_main.py) |  |
| F0040 | `create_app.factory_readiness` | route | used | [backend/app/main.py:336](../../../backend/app/main.py#L336) | [annotated](../../01_fastapi/endpoints/app_main.py) |  |
| F0041 | `create_app.stock_balance` | route | used | [backend/app/main.py:341](../../../backend/app/main.py#L341) | [annotated](../../01_fastapi/endpoints/app_main.py) |  |
| F0042 | `create_app.demand_forecast` | route | used | [backend/app/main.py:345](../../../backend/app/main.py#L345) | [annotated](../../01_fastapi/endpoints/app_main.py) |  |
| F0043 | `create_app.what_if` | route | used | [backend/app/main.py:349](../../../backend/app/main.py#L349) | [annotated](../../01_fastapi/endpoints/app_main.py) |  |
| F0044 | `create_app.supplier_risk` | route | used | [backend/app/main.py:354](../../../backend/app/main.py#L354) | [annotated](../../01_fastapi/endpoints/app_main.py) |  |
| F0045 | `create_app.quality` | route | used | [backend/app/main.py:358](../../../backend/app/main.py#L358) | [annotated](../../01_fastapi/endpoints/app_main.py) |  |
| F0046 | `create_app.logistics` | route | used | [backend/app/main.py:362](../../../backend/app/main.py#L362) | [annotated](../../01_fastapi/endpoints/app_main.py) |  |
| F0047 | `create_app.sales_orders` | route | used | [backend/app/main.py:366](../../../backend/app/main.py#L366) | [annotated](../../01_fastapi/endpoints/app_main.py) |  |
| F0048 | `create_app.stocktake` | route | used | [backend/app/main.py:370](../../../backend/app/main.py#L370) | [annotated](../../01_fastapi/endpoints/app_main.py) |  |
| F0049 | `create_app.forecast_vs_actuals` | route | used | [backend/app/main.py:374](../../../backend/app/main.py#L374) | [annotated](../../01_fastapi/endpoints/app_main.py) |  |
| F0050 | `create_app.production_overview` | route | used | [backend/app/main.py:379](../../../backend/app/main.py#L379) | [annotated](../../01_fastapi/endpoints/app_main.py) |  |
| F0051 | `create_app.products` | route | used | [backend/app/main.py:384](../../../backend/app/main.py#L384) | [annotated](../../01_fastapi/endpoints/app_main.py) |  |
| F0052 | `create_app.product` | route | used | [backend/app/main.py:389](../../../backend/app/main.py#L389) | [annotated](../../01_fastapi/endpoints/app_main.py) |  |
| F0053 | `create_app.role_catalogue` | route | used | [backend/app/main.py:395](../../../backend/app/main.py#L395) | [annotated](../../01_fastapi/endpoints/app_main.py) |  |
| F0054 | `create_app.role_view` | route | used | [backend/app/main.py:400](../../../backend/app/main.py#L400) | [annotated](../../01_fastapi/endpoints/app_main.py) |  |
| F0055 | `create_app.north_star` | route | used | [backend/app/main.py:407](../../../backend/app/main.py#L407) | [annotated](../../01_fastapi/endpoints/app_main.py) |  |
| F0056 | `create_app.learning` | route | used | [backend/app/main.py:412](../../../backend/app/main.py#L412) | [annotated](../../01_fastapi/endpoints/app_main.py) |  |
| F0057 | `create_app.moat_view` | route | used | [backend/app/main.py:417](../../../backend/app/main.py#L417) | [annotated](../../01_fastapi/endpoints/app_main.py) | Customer data intelligence flywheel, moat evidence, consent gate and the five mo |
| F0058 | `create_app.moat_consent` | route | used | [backend/app/main.py:423](../../../backend/app/main.py#L423) | [annotated](../../01_fastapi/endpoints/app_main.py) | The customer decides whether its data may contribute to industry learning (manag |
| F0059 | `create_app.record_outcome` | route | used | [backend/app/main.py:431](../../../backend/app/main.py#L431) | [annotated](../../01_fastapi/endpoints/app_main.py) | Record the real result of an executed recommendation against an SAP document (de |
| F0060 | `create_app.sales_outlook` | route | used | [backend/app/main.py:445](../../../backend/app/main.py#L445) | [annotated](../../01_fastapi/endpoints/app_main.py) |  |
| F0061 | `create_app.product_brief` | route | used | [backend/app/main.py:450](../../../backend/app/main.py#L450) | [annotated](../../01_fastapi/endpoints/app_main.py) |  |
| F0062 | `create_app.sites` | route | used | [backend/app/main.py:455](../../../backend/app/main.py#L455) | [annotated](../../01_fastapi/endpoints/app_main.py) |  |
| F0063 | `create_app.site` | route | used | [backend/app/main.py:460](../../../backend/app/main.py#L460) | [annotated](../../01_fastapi/endpoints/app_main.py) |  |
| F0064 | `create_app.dashboards_list` | route | used | [backend/app/main.py:465](../../../backend/app/main.py#L465) | [annotated](../../01_fastapi/endpoints/app_main.py) |  |
| F0065 | `create_app.dashboard` | route | used | [backend/app/main.py:469](../../../backend/app/main.py#L469) | [annotated](../../01_fastapi/endpoints/app_main.py) |  |
| F0066 | `create_app.get_insights` | route | used | [backend/app/main.py:474](../../../backend/app/main.py#L474) | [annotated](../../01_fastapi/endpoints/app_main.py) |  |
| F0067 | `create_app.watch_kinds` | route | used | [backend/app/main.py:482](../../../backend/app/main.py#L482) | [annotated](../../01_fastapi/endpoints/app_main.py) |  |
| F0068 | `create_app.list_watches` | route | used | [backend/app/main.py:486](../../../backend/app/main.py#L486) | [annotated](../../01_fastapi/endpoints/app_main.py) |  |
| F0069 | `create_app.create_watch` | route | used | [backend/app/main.py:490](../../../backend/app/main.py#L490) | [annotated](../../01_fastapi/endpoints/app_main.py) |  |
| F0070 | `create_app.delete_watch` | route | used | [backend/app/main.py:500](../../../backend/app/main.py#L500) | [annotated](../../01_fastapi/endpoints/app_main.py) |  |
| F0071 | `create_app.evaluate_watches` | route | used | [backend/app/main.py:506](../../../backend/app/main.py#L506) | [annotated](../../01_fastapi/endpoints/app_main.py) |  |
| F0072 | `create_app.get_analysis` | route | used | [backend/app/main.py:516](../../../backend/app/main.py#L516) | [annotated](../../01_fastapi/endpoints/app_main.py) |  |
| F0073 | `create_app.inventory` | route | used | [backend/app/main.py:524](../../../backend/app/main.py#L524) | [annotated](../../01_fastapi/endpoints/app_main.py) |  |
| F0074 | `create_app.supplier_scorecard` | route | used | [backend/app/main.py:529](../../../backend/app/main.py#L529) | [annotated](../../01_fastapi/endpoints/app_main.py) |  |
| F0075 | `create_app.kpis` | route | used | [backend/app/main.py:534](../../../backend/app/main.py#L534) | [annotated](../../01_fastapi/endpoints/app_main.py) |  |
| F0076 | `create_app.rag_search` | route | used | [backend/app/main.py:540](../../../backend/app/main.py#L540) | [annotated](../../01_fastapi/endpoints/app_main.py) |  |
| F0077 | `create_app.rag_search_get` | route | used | [backend/app/main.py:545](../../../backend/app/main.py#L545) | [annotated](../../01_fastapi/endpoints/app_main.py) | Same search via query parameters — used by the Flowise AgentFlow RAG step (no JS |
| F0078 | `create_app.embeddings` | route | used | [backend/app/main.py:553](../../../backend/app/main.py#L553) | [annotated](../../01_fastapi/endpoints/app_main.py) | Lets Flowise (OpenAI Embeddings Custom node) index and query with exactly the em |
| F0079 | `create_app.embeddings.encode` | nested | used | [backend/app/main.py:562](../../../backend/app/main.py#L562) | [annotated](../../01_fastapi/endpoints/app_main.py) |  |
| F0080 | `create_app.rag_stats` | route | used | [backend/app/main.py:570](../../../backend/app/main.py#L570) | [annotated](../../01_fastapi/endpoints/app_main.py) |  |
| F0081 | `create_app.rag_add` | route | used | [backend/app/main.py:575](../../../backend/app/main.py#L575) | [annotated](../../01_fastapi/endpoints/app_main.py) |  |
| F1801 | `create_app.rag_tuning_proxy` | route | used | [backend/app/main.py:583](../../../backend/app/main.py#L583) | [annotated](../../01_fastapi/endpoints/app_main.py) |  |
| F1950 | `create_app.code_files` | route | used | [backend/app/main.py:604](../../../backend/app/main.py#L604) | [annotated](../../01_fastapi/endpoints/app_main.py) |  |
| F1951 | `create_app.code_file` | route | used | [backend/app/main.py:610](../../../backend/app/main.py#L610) | [annotated](../../01_fastapi/endpoints/app_main.py) |  |
| F1955 | `create_app.code_template` | route | used | [backend/app/main.py:618](../../../backend/app/main.py#L618) | [annotated](../../01_fastapi/endpoints/app_main.py) |  |
| F0985 | `create_app.code_functions` | route | used | [backend/app/main.py:626](../../../backend/app/main.py#L626) | [annotated](../../01_fastapi/endpoints/app_main.py) |  |
| F0986 | `create_app.code_function` | route | used | [backend/app/main.py:631](../../../backend/app/main.py#L631) | [annotated](../../01_fastapi/endpoints/app_main.py) |  |
| F0987 | `create_app.code_update` | route | used | [backend/app/main.py:639](../../../backend/app/main.py#L639) | [annotated](../../01_fastapi/endpoints/app_main.py) |  |
| F0082 | `create_app._graph_call` | nested | used | [backend/app/main.py:652](../../../backend/app/main.py#L652) | [annotated](../../01_fastapi/endpoints/app_main.py) |  |
| F0083 | `create_app.chat` | route | used | [backend/app/main.py:660](../../../backend/app/main.py#L660) | [annotated](../../01_fastapi/endpoints/app_main.py) |  |
| F0084 | `create_app._agentflow_view` | nested | used | [backend/app/main.py:687](../../../backend/app/main.py#L687) | [annotated](../../01_fastapi/endpoints/app_main.py) |  |
| F0085 | `create_app.langgraph_agentflow` | route | used | [backend/app/main.py:711](../../../backend/app/main.py#L711) | [annotated](../../01_fastapi/endpoints/app_main.py) |  |
| F0086 | `create_app.langgraph_agentflow_resume` | route | used | [backend/app/main.py:718](../../../backend/app/main.py#L718) | [annotated](../../01_fastapi/endpoints/app_main.py) |  |
| F0087 | `create_app.business_start` | route | used | [backend/app/main.py:724](../../../backend/app/main.py#L724) | [annotated](../../01_fastapi/endpoints/app_main.py) |  |
| F0088 | `create_app.business_resume` | route | used | [backend/app/main.py:731](../../../backend/app/main.py#L731) | [annotated](../../01_fastapi/endpoints/app_main.py) |  |
| F0089 | `create_app.current_harness` | nested | used | [backend/app/main.py:744](../../../backend/app/main.py#L744) | [annotated](../../01_fastapi/endpoints/app_main.py) |  |
| F0090 | `create_app.deep_harness` | route | used | [backend/app/main.py:748](../../../backend/app/main.py#L748) | [annotated](../../01_fastapi/endpoints/app_main.py) |  |
| F0091 | `create_app.set_deep_harness` | route | used | [backend/app/main.py:757](../../../backend/app/main.py#L757) | [annotated](../../01_fastapi/endpoints/app_main.py) |  |
| F2038 | `create_app.erp_audit` | nested | used | [backend/app/main.py:771](../../../backend/app/main.py#L771) | [annotated](../../01_fastapi/endpoints/app_main.py) |  |
| F0092 | `create_app.supplier_research` | route | used | [backend/app/main.py:780](../../../backend/app/main.py#L780) | [annotated](../../01_fastapi/endpoints/app_main.py) |  |
| F0093 | `create_app._flow_id` | nested | used | [backend/app/main.py:804](../../../backend/app/main.py#L804) | [annotated](../../01_fastapi/endpoints/app_main.py) |  |
| F0094 | `create_app.flowise_predict` | route | used | [backend/app/main.py:818](../../../backend/app/main.py#L818) | [annotated](../../01_fastapi/endpoints/app_main.py) |  |
| F0095 | `create_app.submit_recommendation` | route | used | [backend/app/main.py:856](../../../backend/app/main.py#L856) | [annotated](../../01_fastapi/endpoints/app_main.py) |  |
| F0096 | `create_app.submit_from_agent` | route | used | [backend/app/main.py:865](../../../backend/app/main.py#L865) | [annotated](../../01_fastapi/endpoints/app_main.py) |  |
| F0097 | `create_app.recommendations` | route | used | [backend/app/main.py:880](../../../backend/app/main.py#L880) | [annotated](../../01_fastapi/endpoints/app_main.py) |  |
| F0098 | `create_app.decide` | route | used | [backend/app/main.py:885](../../../backend/app/main.py#L885) | [annotated](../../01_fastapi/endpoints/app_main.py) |  |
| F0099 | `create_app.execute` | route | used | [backend/app/main.py:899](../../../backend/app/main.py#L899) | [annotated](../../01_fastapi/endpoints/app_main.py) | 1-click execution of an ACCEPTED recommendation into the SAP sandbox (manager on |
| F0100 | `create_app.sap_documents` | route | used | [backend/app/main.py:926](../../../backend/app/main.py#L926) | [annotated](../../01_fastapi/endpoints/app_main.py) |  |
| F0101 | `create_app.audit` | route | used | [backend/app/main.py:931](../../../backend/app/main.py#L931) | [annotated](../../01_fastapi/endpoints/app_main.py) |  |
| F0102 | `create_app.poc_sap_inventory` | route | used | [backend/app/main.py:940](../../../backend/app/main.py#L940) | [annotated](../../01_fastapi/endpoints/app_main.py) |  |
| F0103 | `create_app.poc_sap_production_orders` | route | used | [backend/app/main.py:946](../../../backend/app/main.py#L946) | [annotated](../../01_fastapi/endpoints/app_main.py) |  |
| F0104 | `create_app.poc_forecast_demand` | route | used | [backend/app/main.py:952](../../../backend/app/main.py#L952) | [annotated](../../01_fastapi/endpoints/app_main.py) |  |
| F0105 | `create_app.poc_forecast_lead_time` | route | used | [backend/app/main.py:956](../../../backend/app/main.py#L956) | [annotated](../../01_fastapi/endpoints/app_main.py) |  |
| F0106 | `create_app.poc_material_readiness` | route | used | [backend/app/main.py:960](../../../backend/app/main.py#L960) | [annotated](../../01_fastapi/endpoints/app_main.py) |  |
| F0107 | `create_app.poc_warehouse_transfer` | route | used | [backend/app/main.py:965](../../../backend/app/main.py#L965) | [annotated](../../01_fastapi/endpoints/app_main.py) |  |
| F0108 | `create_app.poc_decisions` | route | used | [backend/app/main.py:969](../../../backend/app/main.py#L969) | [annotated](../../01_fastapi/endpoints/app_main.py) |  |
| F0109 | `create_app.poc_human_review` | route | used | [backend/app/main.py:973](../../../backend/app/main.py#L973) | [annotated](../../01_fastapi/endpoints/app_main.py) |  |
| F0110 | `create_app.poc_reconcile` | route | used | [backend/app/main.py:977](../../../backend/app/main.py#L977) | [annotated](../../01_fastapi/endpoints/app_main.py) |  |
| F0111 | `create_app.poc_model_performance` | route | used | [backend/app/main.py:1003](../../../backend/app/main.py#L1003) | [annotated](../../01_fastapi/endpoints/app_main.py) |  |
| F1993 | `create_router` | function | used | [backend/scinsight/app.py:37](../../../backend/scinsight/app.py#L37) | [annotated](../../01_fastapi/endpoints/scinsight_app.py) | Database, fixtures, security, RAG and every SCInsight route; backend/app/main.py |
| F1994 | `create_router.principal` | nested | used | [backend/scinsight/app.py:61](../../../backend/scinsight/app.py#L61) | [annotated](../../01_fastapi/endpoints/scinsight_app.py) |  |
| F1995 | `create_router.reader` | nested | used | [backend/scinsight/app.py:66](../../../backend/scinsight/app.py#L66) | [annotated](../../01_fastapi/endpoints/scinsight_app.py) |  |
| F1996 | `create_router.biz_date` | nested | used | [backend/scinsight/app.py:70](../../../backend/scinsight/app.py#L70) | [annotated](../../01_fastapi/endpoints/scinsight_app.py) |  |
| F1997 | `create_router.health` | route | used | [backend/scinsight/app.py:73](../../../backend/scinsight/app.py#L73) | [annotated](../../01_fastapi/endpoints/scinsight_app.py) |  |
| F1998 | `create_router.context` | route | used | [backend/scinsight/app.py:79](../../../backend/scinsight/app.py#L79) | [annotated](../../01_fastapi/endpoints/scinsight_app.py) |  |
| F1999 | `create_router.validate_context` | route | used | [backend/scinsight/app.py:85](../../../backend/scinsight/app.py#L85) | [annotated](../../01_fastapi/endpoints/scinsight_app.py) |  |
| F2000 | `create_router.sap_inventory` | route | used | [backend/scinsight/app.py:94](../../../backend/scinsight/app.py#L94) | [annotated](../../01_fastapi/endpoints/scinsight_app.py) |  |
| F2001 | `create_router.sap_bom` | route | used | [backend/scinsight/app.py:99](../../../backend/scinsight/app.py#L99) | [annotated](../../01_fastapi/endpoints/scinsight_app.py) |  |
| F2002 | `create_router.sap_production_orders` | route | used | [backend/scinsight/app.py:103](../../../backend/scinsight/app.py#L103) | [annotated](../../01_fastapi/endpoints/scinsight_app.py) |  |
| F2003 | `create_router.sap_purchase_orders` | route | used | [backend/scinsight/app.py:107](../../../backend/scinsight/app.py#L107) | [annotated](../../01_fastapi/endpoints/scinsight_app.py) |  |
| F2004 | `create_router.sap_warehouses` | route | used | [backend/scinsight/app.py:112](../../../backend/scinsight/app.py#L112) | [annotated](../../01_fastapi/endpoints/scinsight_app.py) |  |
| F2005 | `create_router.sap_suppliers` | route | used | [backend/scinsight/app.py:116](../../../backend/scinsight/app.py#L116) | [annotated](../../01_fastapi/endpoints/scinsight_app.py) |  |
| F2006 | `create_router.sap_write_blocked` | route | used | [backend/scinsight/app.py:120](../../../backend/scinsight/app.py#L120) | [annotated](../../01_fastapi/endpoints/scinsight_app.py) |  |
| F2007 | `create_router.material_readiness` | route | used | [backend/scinsight/app.py:126](../../../backend/scinsight/app.py#L126) | [annotated](../../01_fastapi/endpoints/scinsight_app.py) |  |
| F2008 | `create_router.warehouse_balancing` | route | used | [backend/scinsight/app.py:130](../../../backend/scinsight/app.py#L130) | [annotated](../../01_fastapi/endpoints/scinsight_app.py) |  |
| F2009 | `create_router.replenishment` | route | used | [backend/scinsight/app.py:134](../../../backend/scinsight/app.py#L134) | [annotated](../../01_fastapi/endpoints/scinsight_app.py) |  |
| F2010 | `create_router.forecast_demand` | route | used | [backend/scinsight/app.py:138](../../../backend/scinsight/app.py#L138) | [annotated](../../01_fastapi/endpoints/scinsight_app.py) |  |
| F2011 | `create_router.forecast_lead_time` | route | used | [backend/scinsight/app.py:142](../../../backend/scinsight/app.py#L142) | [annotated](../../01_fastapi/endpoints/scinsight_app.py) |  |
| F2012 | `create_router.quality_check` | route | used | [backend/scinsight/app.py:146](../../../backend/scinsight/app.py#L146) | [annotated](../../01_fastapi/endpoints/scinsight_app.py) |  |
| F2013 | `create_router.calculation` | route | used | [backend/scinsight/app.py:150](../../../backend/scinsight/app.py#L150) | [annotated](../../01_fastapi/endpoints/scinsight_app.py) |  |
| F2014 | `create_router.rag_search` | route | used | [backend/scinsight/app.py:155](../../../backend/scinsight/app.py#L155) | [annotated](../../01_fastapi/endpoints/scinsight_app.py) |  |
| F2015 | `create_router.rag_documents` | route | used | [backend/scinsight/app.py:161](../../../backend/scinsight/app.py#L161) | [annotated](../../01_fastapi/endpoints/scinsight_app.py) |  |
| F2016 | `create_router.create_decision` | route | used | [backend/scinsight/app.py:170](../../../backend/scinsight/app.py#L170) | [annotated](../../01_fastapi/endpoints/scinsight_app.py) |  |
| F2017 | `create_router.list_decisions` | route | used | [backend/scinsight/app.py:175](../../../backend/scinsight/app.py#L175) | [annotated](../../01_fastapi/endpoints/scinsight_app.py) |  |
| F2018 | `create_router.get_decision` | route | used | [backend/scinsight/app.py:179](../../../backend/scinsight/app.py#L179) | [annotated](../../01_fastapi/endpoints/scinsight_app.py) |  |
| F2019 | `create_router.review` | route | used | [backend/scinsight/app.py:183](../../../backend/scinsight/app.py#L183) | [annotated](../../01_fastapi/endpoints/scinsight_app.py) |  |
| F2020 | `create_router.withdraw` | route | used | [backend/scinsight/app.py:187](../../../backend/scinsight/app.py#L187) | [annotated](../../01_fastapi/endpoints/scinsight_app.py) |  |
| F2021 | `create_router.sap_execution` | route | used | [backend/scinsight/app.py:191](../../../backend/scinsight/app.py#L191) | [annotated](../../01_fastapi/endpoints/scinsight_app.py) |  |
| F2022 | `create_router.reconcile` | route | used | [backend/scinsight/app.py:196](../../../backend/scinsight/app.py#L196) | [annotated](../../01_fastapi/endpoints/scinsight_app.py) |  |
| F2023 | `create_router.learning_metrics` | route | used | [backend/scinsight/app.py:200](../../../backend/scinsight/app.py#L200) | [annotated](../../01_fastapi/endpoints/scinsight_app.py) |  |
| F2024 | `create_router.train` | route | used | [backend/scinsight/app.py:204](../../../backend/scinsight/app.py#L204) | [annotated](../../01_fastapi/endpoints/scinsight_app.py) |  |
| F2025 | `create_router.promote` | route | used | [backend/scinsight/app.py:211](../../../backend/scinsight/app.py#L211) | [annotated](../../01_fastapi/endpoints/scinsight_app.py) |  |
| F2026 | `create_router.retraining` | route | used | [backend/scinsight/app.py:218](../../../backend/scinsight/app.py#L218) | [annotated](../../01_fastapi/endpoints/scinsight_app.py) |  |
| F2027 | `create_router.audit` | route | used | [backend/scinsight/app.py:224](../../../backend/scinsight/app.py#L224) | [annotated](../../01_fastapi/endpoints/scinsight_app.py) |  |
