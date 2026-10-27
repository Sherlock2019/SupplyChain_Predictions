# Function index (generated)

Every function, method and class of the tracked Python source, with stable ids. Status: `used` = reachable from a route, LangGraph graph, MCP tool, Flowise node or script entry point; `used (framework)` = called by FastAPI / Pydantic / LangGraph; `tooling` = scripts and deploy helpers; `test` = pytest; `unused?` = no caller found (review).

Regenerate: `python3 code_explorer/tools/build_code_explorer.py`.

| ID | Folder | Function / class | Original file | Kind | Status | Summary | Called by | FastAPI endpoint | Flowise node |
|---|---|---|---|---|---|---|---|---|---|
| F0001 | 01_fastapi/app_setup | `Settings` | [backend/app/config.py:11](../backend/app/config.py#L11) | pydantic_model | used |  | F0769, F0008, F0008, F0483, F0728, F0729, F0017, F0610, F0622, F0904, F0904, F09 |  |  |
| F0002 | 01_fastapi/app_setup | `Settings.parse_keys` | [backend/app/config.py:87](../backend/app/config.py#L87) | method | used (framework) |  | F0003, F0004 |  |  |
| F0003 | 01_fastapi/app_setup | `Settings.assistants` | [backend/app/config.py:96](../backend/app/config.py#L96) | method | used (framework) |  |  |  |  |
| F0004 | 01_fastapi/app_setup | `Settings.managers` | [backend/app/config.py:100](../backend/app/config.py#L100) | method | used (framework) |  |  |  |  |
| F0005 | 01_fastapi/app_setup | `Settings.tenants_for` | [backend/app/config.py:104](../backend/app/config.py#L104) | method | used | Tenants an identity may use; None = unrestricted. | F0019 |  |  |
| F0006 | 01_fastapi/app_setup | `Settings.llm_enabled` | [backend/app/config.py:113](../backend/app/config.py#L113) | method | used (framework) |  |  |  |  |
| F0007 | 01_fastapi/app_setup | `Settings.langfuse_enabled` | [backend/app/config.py:117](../backend/app/config.py#L117) | method | used (framework) |  |  |  |  |
| F0008 | 01_fastapi/app_setup | `get_settings` | [backend/app/config.py:122](../backend/app/config.py#L122) | function | used |  | F0544, F0551, F0484, F0565, F0575, F0580, F0589, F0599, F0017, F0009, F0010 |  |  |
| F0009 | 01_fastapi/app_setup | `_langfuse_client` | [backend/app/observability.py:22](../backend/app/observability.py#L22) | function | used |  | F0010, F0012 |  |  |
| F0010 | 01_fastapi/app_setup | `langfuse_callbacks` | [backend/app/observability.py:41](../backend/app/observability.py#L41) | function | used | LangChain callback handlers for one run; empty when Langfuse is not configured. | F0572, F0585, F0011 |  |  |
| F0011 | 01_fastapi/app_setup | `run_config` | [backend/app/observability.py:51](../backend/app/observability.py#L51) | function | used |  | F0614, F0615 |  |  |
| F0012 | 01_fastapi/app_setup | `flush` | [backend/app/observability.py:59](../backend/app/observability.py#L59) | function | used |  | F0614, F0615 |  |  |
| F0013 | 01_fastapi/app_setup | `SciSettings` | [backend/scinsight/settings.py:13](../backend/scinsight/settings.py#L13) | pydantic_model | used |  | F1993, F1993, F0312, F2034, F0908, F0908 |  |  |
| F0014 | 01_fastapi/app_setup | `SciSettings.user_keys` | [backend/scinsight/settings.py:52](../backend/scinsight/settings.py#L52) | method | used |  | F1993 |  |  |
| F0015 | 01_fastapi/app_setup | `SciSettings.missing_keys` | [backend/scinsight/settings.py:55](../backend/scinsight/settings.py#L55) | method | used |  | F1993 |  |  |
| F0016 | 01_fastapi/endpoints | `_expectation` | [backend/app/main.py:75](../backend/app/main.py#L75) | function | used | Plain-language expected result of one executed action (what the outcome check will look fo | F0059, F0099, F0110 |  |  |
| F0017 | 01_fastapi/endpoints | `create_app` | [backend/app/main.py:85](../backend/app/main.py#L85) | function | used |  | F0905, F0872, F2176, F2187, F1985 |  |  |
| F0018 | 01_fastapi/endpoints | `create_app.request_context` | [backend/app/main.py:123](../backend/app/main.py#L123) | nested | used |  |  |  |  |
| F0019 | 01_fastapi/endpoints | `create_app.principal` | [backend/app/main.py:143](../backend/app/main.py#L143) | nested | used |  | F0020, F0020, F0021, F0021, F0078 |  |  |
| F0020 | 01_fastapi/endpoints | `create_app.manager` | [backend/app/main.py:158](../backend/app/main.py#L158) | nested | used |  | F0017, F0029, F0058, F0058, F0059, F0059, F0081, F0081, F0987, F0987, F0091, F00 |  |  |
| F0021 | 01_fastapi/endpoints | `create_app.reader` | [backend/app/main.py:166](../backend/app/main.py#L166) | nested | used |  | F0017, F0031, F0031, F0033, F0033, F0035, F0035, F0036, F0036, F0037, F0037, F00 |  |  |
| F0022 | 01_fastapi/endpoints | `create_app.watch_owner` | [backend/app/main.py:169](../backend/app/main.py#L169) | nested | used |  | F0068, F0069, F0070, F0071 |  |  |
| F0023 | 01_fastapi/endpoints | `create_app.save` | [backend/app/main.py:172](../backend/app/main.py#L172) | nested | used |  | F0040, F0041, F0042, F0043, F0044, F0045, F0046, F0047, F0048, F0104, F0105, F01 |  |  |
| F0024 | 01_fastapi/endpoints | `create_app.value_error_handler` | [backend/app/main.py:184](../backend/app/main.py#L184) | nested | used |  |  |  |  |
| F0025 | 01_fastapi/endpoints | `create_app.health` | [backend/app/main.py:189](../backend/app/main.py#L189) | route | used |  |  | GET /health |  |
| F0026 | 01_fastapi/endpoints | `create_app.ready` | [backend/app/main.py:193](../backend/app/main.py#L193) | route | used |  |  | GET /ready |  |
| F0027 | 01_fastapi/endpoints | `create_app.metrics` | [backend/app/main.py:197](../backend/app/main.py#L197) | route | used |  |  | GET /metrics |  |
| F0028 | 01_fastapi/endpoints | `create_app.public_config` | [backend/app/main.py:201](../backend/app/main.py#L201) | route | used | Non-secret links for the dashboard header. | F0871, F0872 | GET /api/v1/config/public |  |
| F0029 | 01_fastapi/endpoints | `create_app.demo_session` | [backend/app/main.py:231](../backend/app/main.py#L231) | route | used | Local demo only (DEMO_AUTO_LOGIN=true): returns the demo planner and manager keys so the U | F0872 | GET /api/v1/demo/session |  |
| F0030 | 01_fastapi/endpoints | `create_app._public` | [backend/app/main.py:240](../backend/app/main.py#L240) | nested | used |  | F0028 |  |  |
| F0031 | 01_fastapi/endpoints | `create_app.status` | [backend/app/main.py:243](../backend/app/main.py#L243) | route | used |  | F0097, F0887, F0871 | GET /api/v1/status |  |
| F0032 | 01_fastapi/endpoints | `create_app.status.probe` | [backend/app/main.py:247](../backend/app/main.py#L247) | nested | used |  | F0031 |  |  |
| F0033 | 01_fastapi/endpoints | `create_app.snapshot` | [backend/app/main.py:279](../backend/app/main.py#L279) | route | used |  | F0471, F0861, F2179, F0964 | GET /api/v1/snapshot |  |
| F0034 | 01_fastapi/endpoints | `create_app.tenant_catalogue` | [backend/app/main.py:292](../backend/app/main.py#L292) | route | used | Industries and customers for the top-bar selector (send the id back as the X-Tenant header | F0963 | GET /api/v1/tenants |  |
| F0035 | 01_fastapi/endpoints | `create_app.network_map` | [backend/app/main.py:297](../backend/app/main.py#L297) | route | used |  | F0964 | GET /api/v1/network/map |  |
| F0036 | 01_fastapi/endpoints | `create_app.sap_metadata` | [backend/app/main.py:302](../backend/app/main.py#L302) | route | used |  | F2099, F0862, F0818, F0819 | GET /sap/opu/odata/sap/ZSCM_COPILOT_SRV/$metadata |  |
| F0037 | 01_fastapi/endpoints | `create_app.sap_sandbox_documents` | [backend/app/main.py:307](../backend/app/main.py#L307) | route | used |  | F2099, F0818, F0819, F0942 | GET /sap/opu/odata/sap/ZSCM_COPILOT_SRV/A_SandboxDocument |  |
| F0038 | 01_fastapi/endpoints | `create_app.sap_odata` | [backend/app/main.py:313](../backend/app/main.py#L313) | route | used |  | F2047, F2099, F0888, F0862, F2181, F2185, F0818, F0819, F0942, F0875 | GET /sap/opu/odata/sap/ZSCM_COPILOT_SRV/{entity} |  |
| F0039 | 01_fastapi/endpoints | `create_app.block_sap_write` | [backend/app/main.py:328](../backend/app/main.py#L328) | route | used |  | F2047, F2084, F2098, F2099, F0888, F0862, F2181, F2185, F0818, F0819, F0942, F08 | POST/PUT/PATCH/DELETE /sap/opu/odata/sap/{path:path} |  |
| F0040 | 01_fastapi/endpoints | `create_app.factory_readiness` | [backend/app/main.py:336](../backend/app/main.py#L336) | route | used |  | F0472, F0889, F0863, F0864, F0865, F0866, F0867, F2181 | POST /api/v1/analysis/factory-readiness |  |
| F0041 | 01_fastapi/endpoints | `create_app.stock_balance` | [backend/app/main.py:341](../backend/app/main.py#L341) | route | used |  | F0473, F0889, F0863, F0864, F0959, F0965 | POST /api/v1/analysis/stock-balance |  |
| F0042 | 01_fastapi/endpoints | `create_app.demand_forecast` | [backend/app/main.py:345](../backend/app/main.py#L345) | route | used |  | F0474, F0864 | POST /api/v1/analysis/forecast |  |
| F0043 | 01_fastapi/endpoints | `create_app.what_if` | [backend/app/main.py:349](../backend/app/main.py#L349) | route | used |  | F0889, F0864 | POST /api/v1/analysis/what-if |  |
| F0044 | 01_fastapi/endpoints | `create_app.supplier_risk` | [backend/app/main.py:354](../backend/app/main.py#L354) | route | used |  | F0475, F0889, F0864 | POST /api/v1/analysis/supplier-risk |  |
| F0045 | 01_fastapi/endpoints | `create_app.quality` | [backend/app/main.py:358](../backend/app/main.py#L358) | route | used |  | F0476, F0889, F0864, F0866 | POST /api/v1/analysis/quality |  |
| F0046 | 01_fastapi/endpoints | `create_app.logistics` | [backend/app/main.py:362](../backend/app/main.py#L362) | route | used |  | F0477, F0889, F0864 | POST /api/v1/analysis/logistics |  |
| F0047 | 01_fastapi/endpoints | `create_app.sales_orders` | [backend/app/main.py:366](../backend/app/main.py#L366) | route | used |  | F0479, F0900, F0942, F0965 | POST /api/v1/analysis/sales-orders |  |
| F0048 | 01_fastapi/endpoints | `create_app.stocktake` | [backend/app/main.py:370](../backend/app/main.py#L370) | route | used |  | F0480, F0900 | POST /api/v1/analysis/stocktake |  |
| F0049 | 01_fastapi/endpoints | `create_app.forecast_vs_actuals` | [backend/app/main.py:374](../backend/app/main.py#L374) | route | used |  |  | GET /api/v1/analysis/forecast-vs-actuals |  |
| F0050 | 01_fastapi/endpoints | `create_app.production_overview` | [backend/app/main.py:379](../backend/app/main.py#L379) | route | used |  |  | GET /api/v1/production/overview |  |
| F0051 | 01_fastapi/endpoints | `create_app.products` | [backend/app/main.py:384](../backend/app/main.py#L384) | route | used |  | F0946 | GET /api/v1/products |  |
| F0052 | 01_fastapi/endpoints | `create_app.product` | [backend/app/main.py:389](../backend/app/main.py#L389) | route | used |  | F0900, F0940, F0946, F0964 | GET /api/v1/products/{material} |  |
| F0053 | 01_fastapi/endpoints | `create_app.role_catalogue` | [backend/app/main.py:395](../backend/app/main.py#L395) | route | used |  | F0955 | GET /api/v1/roles |  |
| F0054 | 01_fastapi/endpoints | `create_app.role_view` | [backend/app/main.py:400](../backend/app/main.py#L400) | route | used |  | F0878, F0956, F0957 | GET /api/v1/roles/{role} |  |
| F0055 | 01_fastapi/endpoints | `create_app.north_star` | [backend/app/main.py:407](../backend/app/main.py#L407) | route | used |  | F0958 | GET /api/v1/northstar |  |
| F0056 | 01_fastapi/endpoints | `create_app.learning` | [backend/app/main.py:412](../backend/app/main.py#L412) | route | used |  | F0959 | GET /api/v1/learning |  |
| F0057 | 01_fastapi/endpoints | `create_app.moat_view` | [backend/app/main.py:417](../backend/app/main.py#L417) | route | used | Customer data intelligence flywheel, moat evidence, consent gate and the five moat-strengt | F0959, F0960 | GET /api/v1/moat |  |
| F0058 | 01_fastapi/endpoints | `create_app.moat_consent` | [backend/app/main.py:423](../backend/app/main.py#L423) | route | used | The customer decides whether its data may contribute to industry learning (manager only, a | F0960 | POST /api/v1/moat/consent |  |
| F0059 | 01_fastapi/endpoints | `create_app.record_outcome` | [backend/app/main.py:431](../backend/app/main.py#L431) | route | used | Record the real result of an executed recommendation against an SAP document (decision out | F0900, F0901, F0865, F0942, F0877, F0959 | POST /api/v1/recommendations/{recommendation_id}/outcome |  |
| F0060 | 01_fastapi/endpoints | `create_app.sales_outlook` | [backend/app/main.py:445](../backend/app/main.py#L445) | route | used |  | F0946 | GET /api/v1/sales/outlook |  |
| F0061 | 01_fastapi/endpoints | `create_app.product_brief` | [backend/app/main.py:450](../backend/app/main.py#L450) | route | used |  | F0946, F0964 | GET /api/v1/products/{material}/brief |  |
| F0062 | 01_fastapi/endpoints | `create_app.sites` | [backend/app/main.py:455](../backend/app/main.py#L455) | route | used |  | F0964 | GET /api/v1/sites |  |
| F0063 | 01_fastapi/endpoints | `create_app.site` | [backend/app/main.py:460](../backend/app/main.py#L460) | route | used |  | F0964 | GET /api/v1/sites/{code} |  |
| F0064 | 01_fastapi/endpoints | `create_app.dashboards_list` | [backend/app/main.py:465](../backend/app/main.py#L465) | route | used |  | F0900 | GET /api/v1/dashboards |  |
| F0065 | 01_fastapi/endpoints | `create_app.dashboard` | [backend/app/main.py:469](../backend/app/main.py#L469) | route | used |  | F0900, F0940, F0941, F0964 | GET /api/v1/dashboards/{persona} |  |
| F0066 | 01_fastapi/endpoints | `create_app.get_insights` | [backend/app/main.py:474](../backend/app/main.py#L474) | route | used |  | F0900, F0940, F0964 | GET /api/v1/insights |  |
| F0067 | 01_fastapi/endpoints | `create_app.watch_kinds` | [backend/app/main.py:482](../backend/app/main.py#L482) | route | used |  | F0900, F0940 | GET /api/v1/watches/kinds |  |
| F0068 | 01_fastapi/endpoints | `create_app.list_watches` | [backend/app/main.py:486](../backend/app/main.py#L486) | route | used |  | F0900, F0940, F0965 | GET /api/v1/watches |  |
| F0069 | 01_fastapi/endpoints | `create_app.create_watch` | [backend/app/main.py:490](../backend/app/main.py#L490) | route | used |  | F0900, F0940, F0965 | POST /api/v1/watches |  |
| F0070 | 01_fastapi/endpoints | `create_app.delete_watch` | [backend/app/main.py:500](../backend/app/main.py#L500) | route | used |  | F0900, F0940 | DELETE /api/v1/watches/{watch_id} |  |
| F0071 | 01_fastapi/endpoints | `create_app.evaluate_watches` | [backend/app/main.py:506](../backend/app/main.py#L506) | route | used |  | F0900, F0940 | POST /api/v1/watches/evaluate |  |
| F0072 | 01_fastapi/endpoints | `create_app.get_analysis` | [backend/app/main.py:516](../backend/app/main.py#L516) | route | used |  |  | GET /api/v1/analyses/{analysis_id} |  |
| F0073 | 01_fastapi/endpoints | `create_app.inventory` | [backend/app/main.py:524](../backend/app/main.py#L524) | route | used |  | F0478, F0864, F2181 | GET /api/v1/inventory |  |
| F0074 | 01_fastapi/endpoints | `create_app.supplier_scorecard` | [backend/app/main.py:529](../backend/app/main.py#L529) | route | used |  | F0864 | GET /api/v1/suppliers/scorecard |  |
| F0075 | 01_fastapi/endpoints | `create_app.kpis` | [backend/app/main.py:534](../backend/app/main.py#L534) | route | used |  | F0888, F0864, F0873, F0965 | GET /api/v1/kpis |  |
| F0076 | 01_fastapi/endpoints | `create_app.rag_search` | [backend/app/main.py:540](../backend/app/main.py#L540) | route | used |  | F0481, F1993, F2014, F0629, F0678, F0890, F0844, F1937, F1939, F1944, F0868, F08 | POST /api/v1/rag/search | Flowise Custom Tool · search_supply_chain_policy, Factory-Planning-Agentflow · 5 · Policy search (RAG), Inventory-Optimi |
| F0077 | 01_fastapi/endpoints | `create_app.rag_search_get` | [backend/app/main.py:545](../backend/app/main.py#L545) | route | used | Same search via query parameters — used by the Flowise AgentFlow RAG step (no JSON escapin | F0481, F1993, F2014, F0629, F0678, F0890, F0844, F1937, F1939, F1944, F0868, F08 | GET /api/v1/rag/search |  |
| F0078 | 01_fastapi/endpoints | `create_app.embeddings` | [backend/app/main.py:553](../backend/app/main.py#L553) | route | used | Lets Flowise (OpenAI Embeddings Custom node) index and query with exactly the embedding mo |  | POST /v1/embeddings |  |
| F0079 | 01_fastapi/endpoints | `create_app.embeddings.encode` | [backend/app/main.py:562](../backend/app/main.py#L562) | nested | used |  | F0078 |  |  |
| F0080 | 01_fastapi/endpoints | `create_app.rag_stats` | [backend/app/main.py:570](../backend/app/main.py#L570) | route | used |  | F0864 | GET /api/v1/rag/stats |  |
| F0081 | 01_fastapi/endpoints | `create_app.rag_add` | [backend/app/main.py:575](../backend/app/main.py#L575) | route | used |  | F1993, F2015, F0868 | POST /api/v1/rag/documents |  |
| F0082 | 01_fastapi/endpoints | `create_app._graph_call` | [backend/app/main.py:652](../backend/app/main.py#L652) | nested | used |  | F0083, F0085, F0086, F0087, F0088, F0092 |  |  |
| F0083 | 01_fastapi/endpoints | `create_app.chat` | [backend/app/main.py:660](../backend/app/main.py#L660) | route | used |  | F0891, F0869, F0962 | POST /api/v1/chat |  |
| F0084 | 01_fastapi/endpoints | `create_app._agentflow_view` | [backend/app/main.py:687](../backend/app/main.py#L687) | nested | used |  | F0085, F0086 |  |  |
| F0085 | 01_fastapi/endpoints | `create_app.langgraph_agentflow` | [backend/app/main.py:711](../backend/app/main.py#L711) | route | used |  | F0892, F0870 | POST /api/v1/langgraph/agentflow |  |
| F0086 | 01_fastapi/endpoints | `create_app.langgraph_agentflow_resume` | [backend/app/main.py:718](../backend/app/main.py#L718) | route | used |  | F0892, F0870 | POST /api/v1/langgraph/agentflow/{thread_id}/resume |  |
| F0087 | 01_fastapi/endpoints | `create_app.business_start` | [backend/app/main.py:724](../backend/app/main.py#L724) | route | used |  | F0893, F0869 | POST /api/v1/workflows/business |  |
| F0088 | 01_fastapi/endpoints | `create_app.business_resume` | [backend/app/main.py:731](../backend/app/main.py#L731) | route | used |  | F0893, F0869 | POST /api/v1/workflows/business/{thread_id}/resume |  |
| F0089 | 01_fastapi/endpoints | `create_app.current_harness` | [backend/app/main.py:744](../backend/app/main.py#L744) | nested | used |  | F0017, F0090, F0092 |  |  |
| F0090 | 01_fastapi/endpoints | `create_app.deep_harness` | [backend/app/main.py:748](../backend/app/main.py#L748) | route | used |  | F0874 | GET /api/v1/deep-agents/harness |  |
| F0091 | 01_fastapi/endpoints | `create_app.set_deep_harness` | [backend/app/main.py:757](../backend/app/main.py#L757) | route | used |  | F0874 | PUT /api/v1/deep-agents/harness |  |
| F0092 | 01_fastapi/endpoints | `create_app.supplier_research` | [backend/app/main.py:780](../backend/app/main.py#L780) | route | used |  | F0894 | POST /api/v1/deep-agents/supplier-research |  |
| F0093 | 01_fastapi/endpoints | `create_app._flow_id` | [backend/app/main.py:804](../backend/app/main.py#L804) | nested | used |  | F0094 |  |  |
| F0094 | 01_fastapi/endpoints | `create_app.flowise_predict` | [backend/app/main.py:818](../backend/app/main.py#L818) | route | used |  | F0895, F0896 | POST /api/v1/flowise/{flow}/predict |  |
| F0095 | 01_fastapi/endpoints | `create_app.submit_recommendation` | [backend/app/main.py:856](../backend/app/main.py#L856) | route | used |  | F0482, F0108, F0900, F0901, F0865, F0867, F0942, F0959, F0965 | POST /api/v1/recommendations |  |
| F0096 | 01_fastapi/endpoints | `create_app.submit_from_agent` | [backend/app/main.py:865](../backend/app/main.py#L865) | route | used |  | F0900, F0901, F0865, F0866, F0819, F0942, F0877, F0959 | POST /api/v1/recommendations/from-agent |  |
| F0097 | 01_fastapi/endpoints | `create_app.recommendations` | [backend/app/main.py:880](../backend/app/main.py#L880) | route | used |  | F0482, F0900, F0901, F0865, F0867, F0942, F0959, F0965 | GET /api/v1/recommendations |  |
| F0098 | 01_fastapi/endpoints | `create_app.decide` | [backend/app/main.py:885](../backend/app/main.py#L885) | route | used |  | F0109, F0888, F0900, F0901, F0865, F0942, F0877, F0959 | POST /api/v1/recommendations/{recommendation_id}/decision |  |
| F0099 | 01_fastapi/endpoints | `create_app.execute` | [backend/app/main.py:899](../backend/app/main.py#L899) | route | used | 1-click execution of an ACCEPTED recommendation into the SAP sandbox (manager only; agents | F0900, F0901, F0865, F0942, F0877, F0959 | POST /api/v1/recommendations/{recommendation_id}/execute |  |
| F0100 | 01_fastapi/endpoints | `create_app.sap_documents` | [backend/app/main.py:926](../backend/app/main.py#L926) | route | used |  |  | GET /api/v1/sap/documents |  |
| F0101 | 01_fastapi/endpoints | `create_app.audit` | [backend/app/main.py:931](../backend/app/main.py#L931) | route | used |  | F1993, F2027, F0901, F1960, F1968, F1944, F0848, F0862, F0865, F0874, F0878, F19 | GET /api/v1/audit |  |
| F0102 | 01_fastapi/endpoints | `create_app.poc_sap_inventory` | [backend/app/main.py:940](../backend/app/main.py#L940) | route | used |  | F0875, F0878, F0879 | GET /sap/inventory |  |
| F0103 | 01_fastapi/endpoints | `create_app.poc_sap_production_orders` | [backend/app/main.py:946](../backend/app/main.py#L946) | route | used |  | F2181, F0875, F0879 | GET /sap/production-orders |  |
| F0104 | 01_fastapi/endpoints | `create_app.poc_forecast_demand` | [backend/app/main.py:952](../backend/app/main.py#L952) | route | used |  | F0876, F0879 | POST /forecast/demand |  |
| F0105 | 01_fastapi/endpoints | `create_app.poc_forecast_lead_time` | [backend/app/main.py:956](../backend/app/main.py#L956) | route | used |  | F0876, F0879 | POST /forecast/supplier-lead-time |  |
| F0106 | 01_fastapi/endpoints | `create_app.poc_material_readiness` | [backend/app/main.py:960](../backend/app/main.py#L960) | route | used |  | F0876, F0879 | POST /optimizer/material-readiness |  |
| F0107 | 01_fastapi/endpoints | `create_app.poc_warehouse_transfer` | [backend/app/main.py:965](../backend/app/main.py#L965) | route | used |  | F0876, F0877, F0879 | POST /optimizer/warehouse-transfer |  |
| F0108 | 01_fastapi/endpoints | `create_app.poc_decisions` | [backend/app/main.py:969](../backend/app/main.py#L969) | route | used |  |  | POST /decisions |  |
| F0109 | 01_fastapi/endpoints | `create_app.poc_human_review` | [backend/app/main.py:973](../backend/app/main.py#L973) | route | used |  | F0877, F0879 | POST /decisions/{decision_id}/human-review |  |
| F0110 | 01_fastapi/endpoints | `create_app.poc_reconcile` | [backend/app/main.py:977](../backend/app/main.py#L977) | route | used |  | F0877, F0879 | POST /outcomes/reconcile |  |
| F0111 | 01_fastapi/endpoints | `create_app.poc_model_performance` | [backend/app/main.py:1003](../backend/app/main.py#L1003) | route | used |  | F0877, F0879 | GET /learning/model-performance |  |
| F0147 | 01_fastapi/pydantic_models | `StrictModel` | [backend/app/schemas.py:11](../backend/app/schemas.py#L11) | pydantic_model | used (framework) |  |  |  |  |
| F0148 | 01_fastapi/pydantic_models | `FactoryReadinessRequest` | [backend/app/schemas.py:15](../backend/app/schemas.py#L15) | pydantic_model | used |  | F0040, F0040, F0106, F0106 |  |  |
| F0149 | 01_fastapi/pydantic_models | `StockBalanceRequest` | [backend/app/schemas.py:22](../backend/app/schemas.py#L22) | pydantic_model | used |  | F0041, F0041, F0107, F0107 |  |  |
| F0150 | 01_fastapi/pydantic_models | `ForecastRequest` | [backend/app/schemas.py:28](../backend/app/schemas.py#L28) | pydantic_model | used |  | F0042, F0042, F0104, F0104 |  |  |
| F0151 | 01_fastapi/pydantic_models | `WhatIfRequest` | [backend/app/schemas.py:34](../backend/app/schemas.py#L34) | pydantic_model | used |  | F0043, F0043 |  |  |
| F0152 | 01_fastapi/pydantic_models | `SupplierRiskRequest` | [backend/app/schemas.py:41](../backend/app/schemas.py#L41) | pydantic_model | used |  | F0044, F0044 |  |  |
| F0153 | 01_fastapi/pydantic_models | `QualityRequest` | [backend/app/schemas.py:45](../backend/app/schemas.py#L45) | pydantic_model | used |  | F0045, F0045 |  |  |
| F0154 | 01_fastapi/pydantic_models | `LogisticsRequest` | [backend/app/schemas.py:50](../backend/app/schemas.py#L50) | pydantic_model | used |  | F0046, F0046 |  |  |
| F0155 | 01_fastapi/pydantic_models | `SalesOrderRequest` | [backend/app/schemas.py:55](../backend/app/schemas.py#L55) | pydantic_model | used |  | F0047, F0047 |  |  |
| F0156 | 01_fastapi/pydantic_models | `StocktakeRequest` | [backend/app/schemas.py:59](../backend/app/schemas.py#L59) | pydantic_model | used |  | F0048, F0048 |  |  |
| F0157 | 01_fastapi/pydantic_models | `WatchRequest` | [backend/app/schemas.py:63](../backend/app/schemas.py#L63) | pydantic_model | used |  | F0069, F0069 |  |  |
| F0158 | 01_fastapi/pydantic_models | `RagQuery` | [backend/app/schemas.py:70](../backend/app/schemas.py#L70) | pydantic_model | used |  | F0076, F0076 |  |  |
| F0159 | 01_fastapi/pydantic_models | `RagDocument` | [backend/app/schemas.py:76](../backend/app/schemas.py#L76) | pydantic_model | used |  | F0081, F0081 |  |  |
| F0160 | 01_fastapi/pydantic_models | `RecommendationRequest` | [backend/app/schemas.py:83](../backend/app/schemas.py#L83) | pydantic_model | used |  | F0095, F0095, F0108, F0108 |  |  |
| F0161 | 01_fastapi/pydantic_models | `RecommendationFromTextRequest` | [backend/app/schemas.py:89](../backend/app/schemas.py#L89) | pydantic_model | used | Agent hand-off (Flowise HumanInput 'proceed'): the gateway, not the LLM, picks the analysi | F0096, F0096 |  |  |
| F0162 | 01_fastapi/pydantic_models | `DecisionRequest` | [backend/app/schemas.py:102](../backend/app/schemas.py#L102) | pydantic_model | used |  | F0098, F0098, F0109, F0109 |  |  |
| F0163 | 01_fastapi/pydantic_models | `ConsentRequest` | [backend/app/schemas.py:110](../backend/app/schemas.py#L110) | pydantic_model | used |  | F0058, F0058 |  |  |
| F0164 | 01_fastapi/pydantic_models | `ChatRequest` | [backend/app/schemas.py:114](../backend/app/schemas.py#L114) | pydantic_model | used |  | F0083, F0083, F0085, F0085 |  |  |
| F0165 | 01_fastapi/pydantic_models | `OutcomeRequest` | [backend/app/schemas.py:120](../backend/app/schemas.py#L120) | pydantic_model | used | The real result of an executed recommendation, observed in SAP (approval alone is never pr | F0059, F0059 |  |  |
| F0166 | 01_fastapi/pydantic_models | `BusinessWorkflowRequest` | [backend/app/schemas.py:129](../backend/app/schemas.py#L129) | pydantic_model | used |  | F0087, F0087 |  |  |
| F0167 | 01_fastapi/pydantic_models | `ResumeRequest` | [backend/app/schemas.py:143](../backend/app/schemas.py#L143) | pydantic_model | used |  | F0086, F0086, F0088, F0088 |  |  |
| F0168 | 01_fastapi/pydantic_models | `EmbeddingsRequest` | [backend/app/schemas.py:148](../backend/app/schemas.py#L148) | pydantic_model | used | OpenAI-compatible embeddings request (extra fields such as `user` are ignored, as OpenAI c | F0078, F0078, F0169 |  |  |
| F0169 | 01_fastapi/pydantic_models | `EmbeddingsRequest._limits` | [backend/app/schemas.py:155](../backend/app/schemas.py#L155) | method | used (framework) |  |  |  |  |
| F0170 | 01_fastapi/pydantic_models | `SupplierLeadTimeRequest` | [backend/app/schemas.py:163](../backend/app/schemas.py#L163) | pydantic_model | used |  | F0105, F0105 |  |  |
| F0171 | 01_fastapi/pydantic_models | `ReconcileRequest` | [backend/app/schemas.py:168](../backend/app/schemas.py#L168) | pydantic_model | used | What SAP shows actually happened after an executed decision (goods receipt, delivery or po | F0110, F0110, F2022 |  |  |
| F0172 | 01_fastapi/pydantic_models | `DeepAgentHarness` | [backend/app/schemas.py:182](../backend/app/schemas.py#L182) | pydantic_model | used | Harness settings of the Deep Agents supplier-research agent (model, step budget, subagents | F0554, F0017, F0089, F0090, F0091, F0091, F0173 |  |  |
| F0173 | 01_fastapi/pydantic_models | `DeepAgentHarness._unique` | [backend/app/schemas.py:204](../backend/app/schemas.py#L204) | method | used (framework) |  |  |  |  |
| F0174 | 01_fastapi/pydantic_models | `SupplierResearchRequest` | [backend/app/schemas.py:211](../backend/app/schemas.py#L211) | pydantic_model | used |  | F0092, F0092 |  |  |
| F0175 | 01_fastapi/pydantic_models | `FlowisePredictRequest` | [backend/app/schemas.py:225](../backend/app/schemas.py#L225) | pydantic_model | used |  | F0094, F0094 |  |  |
| F0176 | 01_fastapi/pydantic_models | `FlowisePredictRequest.question_or_resume` | [backend/app/schemas.py:231](../backend/app/schemas.py#L231) | method | used (framework) |  |  |  |  |
| F0177 | 01_fastapi/pydantic_models | `Strict` | [backend/scinsight/schemas.py:12](../backend/scinsight/schemas.py#L12) | pydantic_model | used (framework) |  |  |  |  |
| F0178 | 01_fastapi/pydantic_models | `ContextRequest` | [backend/scinsight/schemas.py:16](../backend/scinsight/schemas.py#L16) | pydantic_model | used |  | F1999, F1999 |  |  |
| F0179 | 01_fastapi/pydantic_models | `MaterialReadinessRequest` | [backend/scinsight/schemas.py:20](../backend/scinsight/schemas.py#L20) | pydantic_model | used |  | F2007, F2007, F0180 |  |  |
| F0180 | 01_fastapi/pydantic_models | `MaterialReadinessRequest._one_way` | [backend/scinsight/schemas.py:27](../backend/scinsight/schemas.py#L27) | method | used (framework) |  |  |  |  |
| F0181 | 01_fastapi/pydantic_models | `WarehouseBalancingRequest` | [backend/scinsight/schemas.py:37](../backend/scinsight/schemas.py#L37) | pydantic_model | used |  | F2008, F2008 |  |  |
| F0182 | 01_fastapi/pydantic_models | `ReplenishmentRequest` | [backend/scinsight/schemas.py:42](../backend/scinsight/schemas.py#L42) | pydantic_model | used |  | F2009, F2009 |  |  |
| F0183 | 01_fastapi/pydantic_models | `DemandForecastRequest` | [backend/scinsight/schemas.py:49](../backend/scinsight/schemas.py#L49) | pydantic_model | used |  | F2010, F2010 |  |  |
| F0184 | 01_fastapi/pydantic_models | `LeadTimeRequest` | [backend/scinsight/schemas.py:55](../backend/scinsight/schemas.py#L55) | pydantic_model | used |  | F2011, F2011 |  |  |
| F0185 | 01_fastapi/pydantic_models | `QualityCheckRequest` | [backend/scinsight/schemas.py:61](../backend/scinsight/schemas.py#L61) | pydantic_model | used |  | F2012, F2012 |  |  |
| F0186 | 01_fastapi/pydantic_models | `RagSearchRequest` | [backend/scinsight/schemas.py:67](../backend/scinsight/schemas.py#L67) | pydantic_model | used |  | F2014, F2014 |  |  |
| F0187 | 01_fastapi/pydantic_models | `DecisionCreateRequest` | [backend/scinsight/schemas.py:72](../backend/scinsight/schemas.py#L72) | pydantic_model | used |  | F2016, F2016 |  |  |
| F0188 | 01_fastapi/pydantic_models | `ReviewRequest` | [backend/scinsight/schemas.py:79](../backend/scinsight/schemas.py#L79) | pydantic_model | used |  | F2019, F2019 |  |  |
| F0189 | 01_fastapi/pydantic_models | `SapExecutionRequest` | [backend/scinsight/schemas.py:85](../backend/scinsight/schemas.py#L85) | pydantic_model | used |  | F2021, F2021 |  |  |
| F0190 | 01_fastapi/pydantic_models | `ReconcileRequest` | [backend/scinsight/schemas.py:91](../backend/scinsight/schemas.py#L91) | pydantic_model | used |  | F2022 |  |  |
| F0191 | 01_fastapi/pydantic_models | `RetrainingRequest` | [backend/scinsight/schemas.py:95](../backend/scinsight/schemas.py#L95) | pydantic_model | used |  | F2026, F2026 |  |  |
| F0192 | 02_business_logic/aurelia_engine | `SupplyChainEngine` | [backend/app/engine.py:14](../backend/app/engine.py#L14) | class | used |  | F0452, F0230, F2157, F0245, F0260, F2039, F0922, F0922, F0933, F0933, F0943, F09 |  |  |
| F0193 | 02_business_logic/aurelia_engine | `SupplyChainEngine.__init__` | [backend/app/engine.py:15](../backend/app/engine.py#L15) | method | used (framework) |  |  |  |  |
| F0194 | 02_business_logic/aurelia_engine | `SupplyChainEngine._confirmed_pos` | [backend/app/engine.py:19](../backend/app/engine.py#L19) | method | used |  | F0197, F0210, F0212 |  |  |
| F0195 | 02_business_logic/aurelia_engine | `SupplyChainEngine._warehouses` | [backend/app/engine.py:26](../backend/app/engine.py#L26) | method | used |  | F0198, F0205, F0206, F0212, F0220, F0226, F0945 |  |  |
| F0196 | 02_business_logic/aurelia_engine | `SupplyChainEngine._in_transit_to` | [backend/app/engine.py:29](../backend/app/engine.py#L29) | method | used |  | F0198, F0205, F0206, F0210 |  |  |
| F0197 | 02_business_logic/aurelia_engine | `SupplyChainEngine.factory_readiness` | [backend/app/engine.py:40](../backend/app/engine.py#L40) | method | used |  | F0455, F0208, F0040, F0106, F0923, F0924, F0925, F0926, F0927 |  |  |
| F0198 | 02_business_logic/aurelia_engine | `SupplyChainEngine.stock_balance` | [backend/app/engine.py:125](../backend/app/engine.py#L125) | method | used |  | F0456, F0237, F0200, F0222, F0041, F0107, F0928 |  |  |
| F0199 | 02_business_logic/aurelia_engine | `SupplyChainEngine.demand_forecast` | [backend/app/engine.py:169](../backend/app/engine.py#L169) | method | used |  | F0457, F0042, F0104 |  |  |
| F0200 | 02_business_logic/aurelia_engine | `SupplyChainEngine.what_if` | [backend/app/engine.py:180](../backend/app/engine.py#L180) | method | used |  | F0043 |  |  |
| F0201 | 02_business_logic/aurelia_engine | `SupplyChainEngine.supplier_risk` | [backend/app/engine.py:206](../backend/app/engine.py#L206) | method | used |  | F0458, F0202, F0249, F0044, F0929 |  |  |
| F0202 | 02_business_logic/aurelia_engine | `SupplyChainEngine.supplier_scorecard` | [backend/app/engine.py:262](../backend/app/engine.py#L262) | method | used |  | F0234, F0212, F0213, F0224, F0248, F0074, F0261, F0929 |  |  |
| F0203 | 02_business_logic/aurelia_engine | `SupplyChainEngine.quality_status` | [backend/app/engine.py:270](../backend/app/engine.py#L270) | method | used |  | F0459, F0241, F0045, F0261, F0930 |  |  |
| F0204 | 02_business_logic/aurelia_engine | `SupplyChainEngine.logistics_status` | [backend/app/engine.py:308](../backend/app/engine.py#L308) | method | used |  | F0460, F0242, F0222, F0224, F0248, F0249, F0046, F0261, F0931 |  |  |
| F0205 | 02_business_logic/aurelia_engine | `SupplyChainEngine.inventory_overview` | [backend/app/engine.py:337](../backend/app/engine.py#L337) | method | used |  | F0461, F0248, F0249, F0073, F0932 |  |  |
| F0206 | 02_business_logic/aurelia_engine | `SupplyChainEngine.sales_order_fulfilment` | [backend/app/engine.py:363](../backend/app/engine.py#L363) | method | used | Allocate warehouse stock (+ inbound arriving before each requested date) to open orders by | F0462, F0236, F0238, F0212, F0213, F0222, F0248, F0249, F0047, F0261, F0935 |  |  |
| F0207 | 02_business_logic/aurelia_engine | `SupplyChainEngine.stocktake_reconciliation` | [backend/app/engine.py:423](../backend/app/engine.py#L423) | method | used | Explain each count difference from unposted goods movements, quality decisions and expiry; | F0463, F0239, F0222, F0248, F0249, F0048, F0261, F0936 |  |  |
| F0208 | 02_business_logic/aurelia_engine | `SupplyChainEngine.production_overview` | [backend/app/engine.py:471](../backend/app/engine.py#L471) | method | used |  | F0241, F0222, F2157, F0248, F0050, F0261 |  |  |
| F0209 | 02_business_logic/aurelia_engine | `SupplyChainEngine.forecast_vs_actuals` | [backend/app/engine.py:480](../backend/app/engine.py#L480) | method | used |  | F0212, F0220, F0049, F0938 |  |  |
| F0210 | 02_business_logic/aurelia_engine | `SupplyChainEngine.position_health` | [backend/app/engine.py:498](../backend/app/engine.py#L498) | method | used | Coverage of every stocked position against its target: finished goods at DCs (demand x hor | F0236, F0237, F0241, F0221, F0222, F2157, F0261 |  |  |
| F0211 | 02_business_logic/aurelia_engine | `SupplyChainEngine.products` | [backend/app/engine.py:547](../backend/app/engine.py#L547) | method | used |  | F0051, F0937 |  |  |
| F0212 | 02_business_logic/aurelia_engine | `SupplyChainEngine.product_360` | [backend/app/engine.py:556](../backend/app/engine.py#L556) | method | used | Everything about one finished good: stock by DC, sales, projected end of stock, component  | F0211, F0213, F0220, F0222, F0052, F0937 |  |  |
| F0213 | 02_business_logic/aurelia_engine | `SupplyChainEngine.product_brief` | [backend/app/engine.py:812](../backend/app/engine.py#L812) | method | used | One-screen product brief: supply status, reserve above safety stock, time to out-of-stock  | F0061, F0261, F0944 |  |  |
| F0214 | 02_business_logic/aurelia_engine | `SupplyChainEngine.product_brief.add` | [backend/app/engine.py:831](../backend/app/engine.py#L831) | nested | used |  | F0213 |  |  |
| F0215 | 02_business_logic/aurelia_engine | `SupplyChainEngine.product_brief.qty` | [backend/app/engine.py:874](../backend/app/engine.py#L874) | nested | used |  | F0213 |  |  |
| F0216 | 02_business_logic/aurelia_engine | `SupplyChainEngine.product_brief.when` | [backend/app/engine.py:877](../backend/app/engine.py#L877) | nested | used |  | F0213, F0217 |  |  |
| F0217 | 02_business_logic/aurelia_engine | `SupplyChainEngine.product_brief.by` | [backend/app/engine.py:880](../backend/app/engine.py#L880) | nested | used |  | F0213 |  |  |
| F0218 | 02_business_logic/aurelia_engine | `SupplyChainEngine.product_brief.level` | [backend/app/engine.py:941](../backend/app/engine.py#L941) | nested | used |  | F0213 |  |  |
| F0219 | 02_business_logic/aurelia_engine | `SupplyChainEngine.supplier_lead_time` | [backend/app/engine.py:969](../backend/app/engine.py#L969) | method | used | Empirical lead-time forecast from SAP receipt history (promised vs received dates), never  | F0105 |  |  |
| F0220 | 02_business_logic/aurelia_engine | `SupplyChainEngine.sales_outlook` | [backend/app/engine.py:996](../backend/app/engine.py#L996) | method | used | Current sales rates per product and DC (last 7 / 28 days vs the 14-day forecast) and a cal | F0060, F0261, F0945 |  |  |
| F0221 | 02_business_logic/aurelia_engine | `SupplyChainEngine.sites` | [backend/app/engine.py:1048](../backend/app/engine.py#L1048) | method | used |  | F0224, F0062 |  |  |
| F0222 | 02_business_logic/aurelia_engine | `SupplyChainEngine.site_360` | [backend/app/engine.py:1058](../backend/app/engine.py#L1058) | method | used |  | F0063 |  |  |
| F0223 | 02_business_logic/aurelia_engine | `SupplyChainEngine.supplier_tier` | [backend/app/engine.py:1122](../backend/app/engine.py#L1122) | method | used | local = same country as the plant; regional = same geographic zone; international = otherw | F0224 |  |  |
| F0224 | 02_business_logic/aurelia_engine | `SupplyChainEngine.network_map` | [backend/app/engine.py:1129](../backend/app/engine.py#L1129) | method | used |  | F2157, F0035, F0255, F0966 |  |  |
| F0225 | 02_business_logic/aurelia_engine | `SupplyChainEngine.expiry_risk` | [backend/app/engine.py:1211](../backend/app/engine.py#L1211) | method | used |  | F0236, F0237, F0222, F0261 |  |  |
| F0226 | 02_business_logic/aurelia_engine | `SupplyChainEngine.kpis` | [backend/app/engine.py:1223](../backend/app/engine.py#L1223) | method | used |  | F2157, F0075, F0932 |  |  |
| F0227 | 02_business_logic/aurelia_views | `_status_cover` | [backend/app/dashboards.py:28](../backend/app/dashboards.py#L28) | function | used (framework) |  | F0233 |  |  |
| F0228 | 02_business_logic/aurelia_views | `_in` | [backend/app/dashboards.py:34](../backend/app/dashboards.py#L34) | function | used (framework) |  | F0236, F0237, F0238, F0239, F0240, F0241, F0242 |  |  |
| F0229 | 02_business_logic/aurelia_views | `Dashboards` | [backend/app/dashboards.py:38](../backend/app/dashboards.py#L38) | class | used |  | F0260, F2039 |  |  |
| F0230 | 02_business_logic/aurelia_views | `Dashboards.__init__` | [backend/app/dashboards.py:39](../backend/app/dashboards.py#L39) | method | used (framework) |  |  |  |  |
| F0231 | 02_business_logic/aurelia_views | `Dashboards.product_scope` | [backend/app/dashboards.py:42](../backend/app/dashboards.py#L42) | method | used | A finished good plus its BOM components; None means the whole network. | F0232, F0261 |  |  |
| F0232 | 02_business_logic/aurelia_views | `Dashboards.build` | [backend/app/dashboards.py:51](../backend/app/dashboards.py#L51) | method | used |  | F0065, F0280 |  |  |
| F0233 | 02_business_logic/aurelia_views | `Dashboards._understock_chart` | [backend/app/dashboards.py:62](../backend/app/dashboards.py#L62) | method | used (framework) |  | F0236, F0237, F0241 |  |  |
| F0234 | 02_business_logic/aurelia_views | `Dashboards._supplier_rows` | [backend/app/dashboards.py:70](../backend/app/dashboards.py#L70) | method | used (framework) |  | F0240 |  |  |
| F0235 | 02_business_logic/aurelia_views | `Dashboards._mentions` | [backend/app/dashboards.py:81](../backend/app/dashboards.py#L81) | method | used (framework) |  | F0236 |  |  |
| F0236 | 02_business_logic/aurelia_views | `Dashboards._executive` | [backend/app/dashboards.py:89](../backend/app/dashboards.py#L89) | method | used (framework) |  |  |  |  |
| F0237 | 02_business_logic/aurelia_views | `Dashboards._inventory` | [backend/app/dashboards.py:122](../backend/app/dashboards.py#L122) | method | used (framework) |  |  |  |  |
| F0238 | 02_business_logic/aurelia_views | `Dashboards._sales` | [backend/app/dashboards.py:157](../backend/app/dashboards.py#L157) | method | used (framework) |  |  |  |  |
| F0239 | 02_business_logic/aurelia_views | `Dashboards._stocktake` | [backend/app/dashboards.py:193](../backend/app/dashboards.py#L193) | method | used (framework) |  |  |  |  |
| F0240 | 02_business_logic/aurelia_views | `Dashboards._procurement` | [backend/app/dashboards.py:223](../backend/app/dashboards.py#L223) | method | used (framework) |  |  |  |  |
| F0241 | 02_business_logic/aurelia_views | `Dashboards._production` | [backend/app/dashboards.py:257](../backend/app/dashboards.py#L257) | method | used (framework) |  |  |  |  |
| F0242 | 02_business_logic/aurelia_views | `Dashboards._logistics` | [backend/app/dashboards.py:283](../backend/app/dashboards.py#L283) | method | used (framework) |  |  |  |  |
| F0243 | 02_business_logic/aurelia_views | `_id` | [backend/app/insights.py:15](../backend/app/insights.py#L15) | function | used |  | F0248 |  |  |
| F0244 | 02_business_logic/aurelia_views | `InsightEngine` | [backend/app/insights.py:19](../backend/app/insights.py#L19) | class | used |  | F0230, F0260, F2039, F0934, F0939 |  |  |
| F0245 | 02_business_logic/aurelia_views | `InsightEngine.__init__` | [backend/app/insights.py:20](../backend/app/insights.py#L20) | method | used (framework) |  |  |  |  |
| F0246 | 02_business_logic/aurelia_views | `InsightEngine._plant` | [backend/app/insights.py:24](../backend/app/insights.py#L24) | method | used |  | F0248 |  |  |
| F0247 | 02_business_logic/aurelia_views | `InsightEngine._mat` | [backend/app/insights.py:27](../backend/app/insights.py#L27) | method | used |  | F0248 |  |  |
| F0248 | 02_business_logic/aurelia_views | `InsightEngine.insights` | [backend/app/insights.py:30](../backend/app/insights.py#L30) | method | used |  | F0236, F0066, F0934 |  |  |
| F0249 | 02_business_logic/aurelia_views | `InsightEngine.evaluate` | [backend/app/insights.py:133](../backend/app/insights.py#L133) | method | used |  | F0069, F0071, F0939 |  |  |
| F0250 | 02_business_logic/aurelia_views | `MoatEngine` | [backend/app/moat.py:43](../backend/app/moat.py#L43) | class | used |  | F0017 |  |  |
| F0251 | 02_business_logic/aurelia_views | `MoatEngine.__init__` | [backend/app/moat.py:44](../backend/app/moat.py#L44) | method | used (framework) |  |  |  |  |
| F0252 | 02_business_logic/aurelia_views | `MoatEngine.consent` | [backend/app/moat.py:48](../backend/app/moat.py#L48) | method | used | Recorded consent wins; without a record, synthetic demo customers are opted in and real on | F0058, F0254, F0255 |  |  |
| F0253 | 02_business_logic/aurelia_views | `MoatEngine._series` | [backend/app/moat.py:56](../backend/app/moat.py#L56) | method | used |  | F0254, F0255 |  |  |
| F0254 | 02_business_logic/aurelia_views | `MoatEngine.model_comparison` | [backend/app/moat.py:61](../backend/app/moat.py#L61) | method | used |  | F0255 |  |  |
| F0255 | 02_business_logic/aurelia_views | `MoatEngine.view` | [backend/app/moat.py:92](../backend/app/moat.py#L92) | method | used |  | F0057 |  |  |
| F0256 | 02_business_logic/aurelia_views | `agent_system_prompt` | [backend/app/roles.py:142](../backend/app/roles.py#L142) | function | used | Role-specific instructions for the specialised agent (LangGraph chat graph). | F0551, F0579 |  |  |
| F0257 | 02_business_logic/aurelia_views | `_status` | [backend/app/roles.py:151](../backend/app/roles.py#L151) | function | used |  | F0258, F0282, F0289 |  |  |
| F0258 | 02_business_logic/aurelia_views | `kpi` | [backend/app/roles.py:159](../backend/app/roles.py#L159) | function | used | A KPI with its agreed definition. available=False means the SAP source is not in this snap | F0267, F0270, F0281, F0282, F0283, F0284, F0285, F0286, F0287, F0288, F0289 |  |  |
| F0259 | 02_business_logic/aurelia_views | `RoleCenter` | [backend/app/roles.py:168](../backend/app/roles.py#L168) | class | used |  | F2039 |  |  |
| F0260 | 02_business_logic/aurelia_views | `RoleCenter.__init__` | [backend/app/roles.py:169](../backend/app/roles.py#L169) | method | used (framework) |  |  |  |  |
| F0261 | 02_business_logic/aurelia_views | `RoleCenter._facts` | [backend/app/roles.py:173](../backend/app/roles.py#L173) | method | used |  | F0269, F0272, F0290 |  |  |
| F0262 | 02_business_logic/aurelia_views | `RoleCenter._otif` | [backend/app/roles.py:202](../backend/app/roles.py#L202) | method | used |  | F0267, F0269 |  |  |
| F0263 | 02_business_logic/aurelia_views | `RoleCenter._inventory_value` | [backend/app/roles.py:206](../backend/app/roles.py#L206) | method | used |  | F0266, F0267, F0270, F0281, F0285, F0287, F0288 |  |  |
| F0264 | 02_business_logic/aurelia_views | `RoleCenter._annual_cogs` | [backend/app/roles.py:209](../backend/app/roles.py#L209) | method | used |  | F0267, F0285 |  |  |
| F0265 | 02_business_logic/aurelia_views | `RoleCenter._wape` | [backend/app/roles.py:213](../backend/app/roles.py#L213) | method | used |  | F0267, F0282, F0289 |  |  |
| F0266 | 02_business_logic/aurelia_views | `RoleCenter._supply_chain_cost` | [backend/app/roles.py:217](../backend/app/roles.py#L217) | method | used | 30-day estimate: procurement (open POs) + transport (proposed transfers) + storage (carryi | F0267, F0269, F0288 |  |  |
| F0267 | 02_business_logic/aurelia_views | `RoleCenter.platform_kpis` | [backend/app/roles.py:232](../backend/app/roles.py#L232) | method | used |  | F0269, F0281 |  |  |
| F0268 | 02_business_logic/aurelia_views | `RoleCenter.learning_summary` | [backend/app/roles.py:255](../backend/app/roles.py#L255) | method | used |  | F0269, F0281, F0288, F0289, F0290 |  |  |
| F0269 | 02_business_logic/aurelia_views | `RoleCenter.north_star` | [backend/app/roles.py:274](../backend/app/roles.py#L274) | method | used |  | F0055 |  |  |
| F0270 | 02_business_logic/aurelia_views | `RoleCenter.industry_kpis` | [backend/app/roles.py:297](../backend/app/roles.py#L297) | method | used |  | F0269 |  |  |
| F0271 | 02_business_logic/aurelia_views | `RoleCenter.catalogue` | [backend/app/roles.py:342](../backend/app/roles.py#L342) | method | used |  | F0053 |  |  |
| F0272 | 02_business_logic/aurelia_views | `RoleCenter.build` | [backend/app/roles.py:345](../backend/app/roles.py#L345) | method | used |  | F0054 |  |  |
| F0273 | 02_business_logic/aurelia_views | `RoleCenter._issue_actions` | [backend/app/roles.py:371](../backend/app/roles.py#L371) | method | used (framework) |  | F0281, F0282, F0283, F0284, F0285, F0286, F0288 |  |  |
| F0274 | 02_business_logic/aurelia_views | `RoleCenter._stock_predictions` | [backend/app/roles.py:377](../backend/app/roles.py#L377) | method | used (framework) |  | F0281, F0282, F0285, F0286, F0288 |  |  |
| F0275 | 02_business_logic/aurelia_views | `RoleCenter._production_predictions` | [backend/app/roles.py:391](../backend/app/roles.py#L391) | method | used (framework) |  | F0281, F0283, F0284 |  |  |
| F0276 | 02_business_logic/aurelia_views | `RoleCenter._supplier_predictions` | [backend/app/roles.py:404](../backend/app/roles.py#L404) | method | used (framework) |  | F0281, F0284 |  |  |
| F0277 | 02_business_logic/aurelia_views | `RoleCenter._shipment_predictions` | [backend/app/roles.py:419](../backend/app/roles.py#L419) | method | used (framework) |  | F0286 |  |  |
| F0278 | 02_business_logic/aurelia_views | `RoleCenter._quality_predictions` | [backend/app/roles.py:430](../backend/app/roles.py#L430) | method | used (framework) |  | F0283, F0285, F0287, F0288 |  |  |
| F0279 | 02_business_logic/aurelia_views | `RoleCenter._go` | [backend/app/roles.py:448](../backend/app/roles.py#L448) | method | used (framework) |  | F0281, F0289 |  |  |
| F0280 | 02_business_logic/aurelia_views | `RoleCenter._charts` | [backend/app/roles.py:453](../backend/app/roles.py#L453) | method | used (framework) |  | F0281, F0282, F0283, F0284, F0285, F0286, F0287 |  |  |
| F0281 | 02_business_logic/aurelia_views | `RoleCenter._director` | [backend/app/roles.py:458](../backend/app/roles.py#L458) | method | used (framework) |  |  |  |  |
| F0282 | 02_business_logic/aurelia_views | `RoleCenter._demand` | [backend/app/roles.py:476](../backend/app/roles.py#L476) | method | used (framework) |  |  |  |  |
| F0283 | 02_business_logic/aurelia_views | `RoleCenter._production` | [backend/app/roles.py:507](../backend/app/roles.py#L507) | method | used (framework) |  |  |  |  |
| F0284 | 02_business_logic/aurelia_views | `RoleCenter._procurement` | [backend/app/roles.py:524](../backend/app/roles.py#L524) | method | used (framework) |  |  |  |  |
| F0285 | 02_business_logic/aurelia_views | `RoleCenter._warehouse` | [backend/app/roles.py:551](../backend/app/roles.py#L551) | method | used (framework) |  |  |  |  |
| F0286 | 02_business_logic/aurelia_views | `RoleCenter._logistics` | [backend/app/roles.py:584](../backend/app/roles.py#L584) | method | used (framework) |  |  |  |  |
| F0287 | 02_business_logic/aurelia_views | `RoleCenter._quality` | [backend/app/roles.py:608](../backend/app/roles.py#L608) | method | used (framework) |  |  |  |  |
| F0288 | 02_business_logic/aurelia_views | `RoleCenter._finance` | [backend/app/roles.py:649](../backend/app/roles.py#L649) | method | used (framework) |  |  |  |  |
| F0289 | 02_business_logic/aurelia_views | `RoleCenter._mlops` | [backend/app/roles.py:689](../backend/app/roles.py#L689) | method | used (framework) |  |  |  |  |
| F0290 | 02_business_logic/aurelia_views | `RoleCenter.learning` | [backend/app/roles.py:729](../backend/app/roles.py#L729) | method | used |  | F0056, F0111, F0255 |  |  |
| F0291 | 02_business_logic/optimization | `optimize_transfers` | [backend/app/optimizer.py:7](../backend/app/optimizer.py#L7) | function | used |  | F0198, F0200 |  |  |
| F0292 | 02_business_logic/optimization | `_greedy` | [backend/app/optimizer.py:60](../backend/app/optimizer.py#L60) | function | used |  | F0291 |  |  |
| F0293 | 02_business_logic/scinsight_rules | `BusinessRuleError` | [backend/scinsight/business.py:26](../backend/scinsight/business.py#L26) | class | used | A request that cannot be answered safely (invalid BOM, unit mismatch, missing master data) | F0302, F0320, F0325, F0916 |  |  |
| F0294 | 02_business_logic/scinsight_rules | `_d` | [backend/scinsight/business.py:30](../backend/scinsight/business.py#L30) | function | used |  | F0297, F0298, F0301, F0302, F0303, F0308, F0310 |  |  |
| F0295 | 02_business_logic/scinsight_rules | `round_qty` | [backend/scinsight/business.py:36](../backend/scinsight/business.py#L36) | function | used |  | F0300, F0302, F0303 |  |  |
| F0296 | 02_business_logic/scinsight_rules | `_dedupe` | [backend/scinsight/business.py:40](../backend/scinsight/business.py#L40) | function | used |  | F0297, F0301, F0303, F0308 |  |  |
| F0297 | 02_business_logic/scinsight_rules | `calculate_usable_stock` | [backend/scinsight/business.py:48](../backend/scinsight/business.py#L48) | function | used | Usable quantity from SAP batches with an itemised exclusion list. With transfer_arrival, a | F0319, F0325, F0326, F0327, F0328, F0329, F0913, F0914 |  |  |
| F0298 | 02_business_logic/scinsight_rules | `average_daily_demand` | [backend/scinsight/business.py:79](../backend/scinsight/business.py#L79) | function | used | Mean units/day over the last `window_days` days (missing days count as zero demand; duplic | F0317 |  |  |
| F0299 | 02_business_logic/scinsight_rules | `calculate_days_of_cover` | [backend/scinsight/business.py:86](../backend/scinsight/business.py#L86) | function | used | Days the usable stock lasts at the given demand. None when there is no demand (cover is un | F0327, F0915 |  |  |
| F0300 | 02_business_logic/scinsight_rules | `calculate_replenishment_quantity` | [backend/scinsight/business.py:93](../backend/scinsight/business.py#L93) | function | used | Quantity needed so that stock covers lead time + target cover. Zero demand -> 0. | F0327, F0915 |  |  |
| F0301 | 02_business_logic/scinsight_rules | `detect_expiry_risk` | [backend/scinsight/business.py:100](../backend/scinsight/business.py#L100) | function | used | Released batches expired or expiring within the horizon, most urgent first. | F0329, F0921 |  |  |
| F0302 | 02_business_logic/scinsight_rules | `calculate_bom_requirements` | [backend/scinsight/business.py:115](../backend/scinsight/business.py#L115) | function | used | Material requirements for `quantity` finished units from the approved BOM version valid on | F0320, F0325, F0916 |  |  |
| F0303 | 02_business_logic/scinsight_rules | `calculate_material_shortage` | [backend/scinsight/business.py:138](../backend/scinsight/business.py#L138) | function | used | Missing quantity on the need date. Inbound counts only if confirmed (or received) and prom | F0325, F0917 |  |  |
| F0304 | 02_business_logic/scinsight_rules | `Site` | [backend/scinsight/business.py:160](../backend/scinsight/business.py#L160) | class | used |  | F0305, F0327, F0918 |  |  |
| F0305 | 02_business_logic/scinsight_rules | `generate_transfer_candidates` | [backend/scinsight/business.py:169](../backend/scinsight/business.py#L169) | function | used | Donor warehouses with surplus = transferable stock above their own target cover (FEFO: nea | F0327, F0918 |  |  |
| F0306 | 02_business_logic/scinsight_rules | `evaluate_transfer_feasibility` | [backend/scinsight/business.py:184](../backend/scinsight/business.py#L184) | function | used | Is the transfer possible and in time? Reasons are listed; costs come only from the lane ma | F0327, F0918 |  |  |
| F0307 | 02_business_logic/scinsight_rules | `compare_supply_options` | [backend/scinsight/business.py:206](../backend/scinsight/business.py#L206) | function | used | Rank options: feasible and in time first, then full coverage, then lowest cost, then faste | F0325, F0327, F0328, F0918, F0919 |  |  |
| F0308 | 02_business_logic/scinsight_rules | `estimate_supplier_lead_time` | [backend/scinsight/business.py:219](../backend/scinsight/business.py#L219) | function | used | Empirical lead time from received purchase orders (order date -> goods receipt). Duplicate | F0324, F0332, F0920 |  |  |
| F0309 | 02_business_logic/scinsight_rules | `calculate_prediction_error` | [backend/scinsight/business.py:234](../backend/scinsight/business.py#L234) | function | used | Signed error = actual - predicted (positive = later/higher than predicted). | F0310, F0920 |  |  |
| F0310 | 02_business_logic/scinsight_rules | `reconcile_actual_outcome` | [backend/scinsight/business.py:241](../backend/scinsight/business.py#L241) | function | used | Match a lead-time prediction with the SAP goods receipt of its purchase order. | F0341, F0920 |  |  |
| F0311 | 02_business_logic/scinsight_use_cases | `Service` | [backend/scinsight/service.py:26](../backend/scinsight/service.py#L26) | class | used |  | F1993 |  |  |
| F0312 | 02_business_logic/scinsight_use_cases | `Service.__init__` | [backend/scinsight/service.py:27](../backend/scinsight/service.py#L27) | method | used (framework) |  |  |  |  |
| F0313 | 02_business_logic/scinsight_use_cases | `Service.snapshot` | [backend/scinsight/service.py:31](../backend/scinsight/service.py#L31) | method | used |  | F1996, F1998, F1999, F0319, F0320, F0321, F0323, F0325, F0327, F0328, F0329, F03 |  |  |
| F0314 | 02_business_logic/scinsight_use_cases | `Service._save_run` | [backend/scinsight/service.py:42](../backend/scinsight/service.py#L42) | method | used |  | F0325, F0327, F0328, F0329, F0330, F0332 |  |  |
| F0315 | 02_business_logic/scinsight_use_cases | `Service.calculation` | [backend/scinsight/service.py:52](../backend/scinsight/service.py#L52) | method | used |  | F2013, F0333 |  |  |
| F0316 | 02_business_logic/scinsight_use_cases | `Service._batches` | [backend/scinsight/service.py:58](../backend/scinsight/service.py#L58) | method | used |  | F0325, F0326, F0328, F0329 |  |  |
| F0317 | 02_business_logic/scinsight_use_cases | `Service._demand` | [backend/scinsight/service.py:65](../backend/scinsight/service.py#L65) | method | used |  | F0326 |  |  |
| F0318 | 02_business_logic/scinsight_use_cases | `Service._require_item` | [backend/scinsight/service.py:68](../backend/scinsight/service.py#L68) | method | used |  | F0327, F0328, F0329 |  |  |
| F0319 | 02_business_logic/scinsight_use_cases | `Service.inventory` | [backend/scinsight/service.py:78](../backend/scinsight/service.py#L78) | method | used |  | F2000 |  |  |
| F0320 | 02_business_logic/scinsight_use_cases | `Service.bom` | [backend/scinsight/service.py:99](../backend/scinsight/service.py#L99) | method | used |  | F2001 |  |  |
| F0321 | 02_business_logic/scinsight_use_cases | `Service.table` | [backend/scinsight/service.py:111](../backend/scinsight/service.py#L111) | method | used |  | F2002, F2003, F2004 |  |  |
| F0322 | 02_business_logic/scinsight_use_cases | `Service.catalog` | [backend/scinsight/service.py:120](../backend/scinsight/service.py#L120) | method | used | Identifiers and names only (no quantities): lets an agent map 'vitamin C serum' to SER-VIT | F1999 |  |  |
| F0323 | 02_business_logic/scinsight_use_cases | `Service.suppliers` | [backend/scinsight/service.py:133](../backend/scinsight/service.py#L133) | method | used |  | F2005 |  |  |
| F0324 | 02_business_logic/scinsight_use_cases | `Service._supplier_options` | [backend/scinsight/service.py:142](../backend/scinsight/service.py#L142) | method | used |  | F0325, F0328 |  |  |
| F0325 | 02_business_logic/scinsight_use_cases | `Service.material_readiness` | [backend/scinsight/service.py:160](../backend/scinsight/service.py#L160) | method | used |  | F2007 |  |  |
| F0326 | 02_business_logic/scinsight_use_cases | `Service._sites` | [backend/scinsight/service.py:232](../backend/scinsight/service.py#L232) | method | used |  | F0327 |  |  |
| F0327 | 02_business_logic/scinsight_use_cases | `Service.warehouse_balancing` | [backend/scinsight/service.py:240](../backend/scinsight/service.py#L240) | method | used |  | F2008, F0328 |  |  |
| F0328 | 02_business_logic/scinsight_use_cases | `Service.replenishment` | [backend/scinsight/service.py:291](../backend/scinsight/service.py#L291) | method | used |  | F2009 |  |  |
| F0329 | 02_business_logic/scinsight_use_cases | `Service.quality_check` | [backend/scinsight/service.py:312](../backend/scinsight/service.py#L312) | method | used |  | F2012 |  |  |
| F0330 | 02_business_logic/scinsight_use_cases | `Service.forecast_demand` | [backend/scinsight/service.py:326](../backend/scinsight/service.py#L326) | method | used |  | F2010 |  |  |
| F0331 | 02_business_logic/scinsight_use_cases | `Service.forecast_demand.predict` | [backend/scinsight/service.py:333](../backend/scinsight/service.py#L333) | nested | used |  | F0330 |  |  |
| F0332 | 02_business_logic/scinsight_use_cases | `Service.lead_time` | [backend/scinsight/service.py:351](../backend/scinsight/service.py#L351) | method | used |  | F2011 |  |  |
| F0333 | 02_business_logic/scinsight_use_cases | `Service.create_decision` | [backend/scinsight/service.py:374](../backend/scinsight/service.py#L374) | method | used |  | F2016 |  |  |
| F0334 | 02_business_logic/scinsight_use_cases | `Service._rec` | [backend/scinsight/service.py:400](../backend/scinsight/service.py#L400) | method | used |  | F0333, F0335, F0336 |  |  |
| F0335 | 02_business_logic/scinsight_use_cases | `Service.get_decision` | [backend/scinsight/service.py:406](../backend/scinsight/service.py#L406) | method | used |  | F2018, F0333, F0337, F0339, F0340, F0341 |  |  |
| F0336 | 02_business_logic/scinsight_use_cases | `Service.list_decisions` | [backend/scinsight/service.py:418](../backend/scinsight/service.py#L418) | method | used |  | F2017 |  |  |
| F0337 | 02_business_logic/scinsight_use_cases | `Service.review` | [backend/scinsight/service.py:423](../backend/scinsight/service.py#L423) | method | used |  | F2019 |  |  |
| F0338 | 02_business_logic/scinsight_use_cases | `Service.review.apply` | [backend/scinsight/service.py:430](../backend/scinsight/service.py#L430) | nested | used |  | F0337 |  |  |
| F0339 | 02_business_logic/scinsight_use_cases | `Service.withdraw` | [backend/scinsight/service.py:444](../backend/scinsight/service.py#L444) | method | used |  | F2020 |  |  |
| F0340 | 02_business_logic/scinsight_use_cases | `Service.record_sap_execution` | [backend/scinsight/service.py:453](../backend/scinsight/service.py#L453) | method | used |  | F2021 |  |  |
| F0341 | 02_business_logic/scinsight_use_cases | `Service.reconcile` | [backend/scinsight/service.py:469](../backend/scinsight/service.py#L469) | method | used |  | F2022 |  |  |
| F0342 | 02_business_logic/scinsight_use_cases | `Service.reconcile.write` | [backend/scinsight/service.py:489](../backend/scinsight/service.py#L489) | nested | used |  | F0341 |  |  |
| F0343 | 02_business_logic/scinsight_use_cases | `Service.learning_metrics` | [backend/scinsight/service.py:509](../backend/scinsight/service.py#L509) | method | used |  | F2023 |  |  |
| F0344 | 03_sap_data/repositories | `_now` | [backend/app/store.py:96](../backend/app/store.py#L96) | function | used |  | F0358, F0361, F0364, F0368, F0369, F0374, F0375, F0378, F0381, F0382, F0385, F03 |  |  |
| F0345 | 03_sap_data/repositories | `_digest` | [backend/app/store.py:100](../backend/app/store.py#L100) | function | used |  | F0358, F0359 |  |  |
| F0346 | 03_sap_data/repositories | `_SqliteDb` | [backend/app/store.py:104](../backend/app/store.py#L104) | class | used |  | F0355 |  |  |
| F0347 | 03_sap_data/repositories | `_SqliteDb.__init__` | [backend/app/store.py:107](../backend/app/store.py#L107) | method | used (framework) |  |  |  |  |
| F0348 | 03_sap_data/repositories | `_SqliteDb.run` | [backend/app/store.py:115](../backend/app/store.py#L115) | method | used |  | F2146, F2151, F2164, F0349, F0364, F0369, F0375, F0385, F0387 |  |  |
| F0349 | 03_sap_data/repositories | `_SqliteDb.query` | [backend/app/store.py:130](../backend/app/store.py#L130) | method | used |  | F2139, F2140, F2141, F2143, F2146, F2150, F2152, F2154, F2156, F2159, F2160, F21 |  |  |
| F0350 | 03_sap_data/repositories | `_PostgresDb` | [backend/app/store.py:134](../backend/app/store.py#L134) | class | used |  | F0355 |  |  |
| F0351 | 03_sap_data/repositories | `_PostgresDb.__init__` | [backend/app/store.py:137](../backend/app/store.py#L137) | method | used (framework) |  |  |  |  |
| F0352 | 03_sap_data/repositories | `_PostgresDb.run` | [backend/app/store.py:147](../backend/app/store.py#L147) | method | used |  | F2146, F2151, F2164, F0353, F0364, F0369, F0375, F0385, F0387 |  |  |
| F0353 | 03_sap_data/repositories | `_PostgresDb.query` | [backend/app/store.py:167](../backend/app/store.py#L167) | method | used |  | F2139, F2140, F2141, F2143, F2146, F2150, F2152, F2154, F2156, F2159, F2160, F21 |  |  |
| F0354 | 03_sap_data/repositories | `Store` | [backend/app/store.py:171](../backend/app/store.py#L171) | class | used |  | F0452, F0230, F2139, F0017, F0017, F0251, F0260, F0392, F0905, F0872, F2176, F21 |  |  |
| F0355 | 03_sap_data/repositories | `Store.__init__` | [backend/app/store.py:172](../backend/app/store.py#L172) | method | used (framework) |  |  |  |  |
| F0356 | 03_sap_data/repositories | `Store.memory` | [backend/app/store.py:180](../backend/app/store.py#L180) | method | used |  | F0452, F0905, F0872, F2176, F1985, F0878, F0953 |  |  |
| F0357 | 03_sap_data/repositories | `Store.dialect` | [backend/app/store.py:184](../backend/app/store.py#L184) | method | used |  | F0026, F0031 |  |  |
| F0358 | 03_sap_data/repositories | `Store.audit` | [backend/app/store.py:189](../backend/app/store.py#L189) | method | used |  | F2170, F0019, F0020, F0023, F0039, F0058, F0059, F0069, F0081, F1801, F0987, F00 |  |  |
| F0359 | 03_sap_data/repositories | `Store.verify_chain` | [backend/app/store.py:214](../backend/app/store.py#L214) | method | used |  | F0031, F0101, F0952 |  |  |
| F0360 | 03_sap_data/repositories | `Store.audit_events` | [backend/app/store.py:223](../backend/app/store.py#L223) | method | used |  | F2053, F2169, F0101, F2185 |  |  |
| F0361 | 03_sap_data/repositories | `Store.save_analysis` | [backend/app/store.py:228](../backend/app/store.py#L228) | method | used |  | F0453, F0023, F0952 |  |  |
| F0362 | 03_sap_data/repositories | `Store.get_analysis` | [backend/app/store.py:237](../backend/app/store.py#L237) | method | used |  | F0072, F0363, F0364 |  |  |
| F0363 | 03_sap_data/repositories | `Store.latest_actionable` | [backend/app/store.py:241](../backend/app/store.py#L241) | method | used | Newest stored analysis of `kind` among the ids that has proposed actions (server-side sele | F0096 |  |  |
| F0364 | 03_sap_data/repositories | `Store.submit` | [backend/app/store.py:247](../backend/app/store.py#L247) | method | used |  | F0465, F0095, F0096, F0952 |  |  |
| F0365 | 03_sap_data/repositories | `Store._recommendation` | [backend/app/store.py:268](../backend/app/store.py#L268) | method | used |  | F0364, F0366, F0367 |  |  |
| F0366 | 03_sap_data/repositories | `Store.get_recommendation` | [backend/app/store.py:272](../backend/app/store.py#L272) | method | used |  | F0059, F0099, F0110, F0364, F0368, F0375 |  |  |
| F0367 | 03_sap_data/repositories | `Store.list_recommendations` | [backend/app/store.py:276](../backend/app/store.py#L276) | method | used | Optionally only recommendations whose analysis came from one SAP snapshot (one customer). | F0097, F0255, F0261, F0281, F0388 |  |  |
| F0368 | 03_sap_data/repositories | `Store.decide` | [backend/app/store.py:289](../backend/app/store.py#L289) | method | used |  | F0098, F0952 |  |  |
| F0369 | 03_sap_data/repositories | `Store.create_watch` | [backend/app/store.py:298](../backend/app/store.py#L298) | method | used |  | F0069 |  |  |
| F0370 | 03_sap_data/repositories | `Store._watch` | [backend/app/store.py:305](../backend/app/store.py#L305) | method | used |  | F0371, F0372 |  |  |
| F0371 | 03_sap_data/repositories | `Store.get_watch` | [backend/app/store.py:310](../backend/app/store.py#L310) | method | used |  | F0369 |  |  |
| F0372 | 03_sap_data/repositories | `Store.list_watches` | [backend/app/store.py:314](../backend/app/store.py#L314) | method | used |  | F0068, F0071 |  |  |
| F0373 | 03_sap_data/repositories | `Store.delete_watch` | [backend/app/store.py:317](../backend/app/store.py#L317) | method | used |  | F0070 |  |  |
| F0374 | 03_sap_data/repositories | `Store.record_watch` | [backend/app/store.py:320](../backend/app/store.py#L320) | method | used |  | F0071 |  |  |
| F0375 | 03_sap_data/repositories | `Store.execute_recommendation` | [backend/app/store.py:324](../backend/app/store.py#L324) | method | used | Accepted -> executed, recording the sandbox SAP documents created for each action (atomic, | F0099 |  |  |
| F0376 | 03_sap_data/repositories | `Store.sap_documents` | [backend/app/store.py:339](../backend/app/store.py#L339) | method | used |  | F0037, F0099, F0100 |  |  |
| F0377 | 03_sap_data/repositories | `Store.next_doc_number` | [backend/app/store.py:344](../backend/app/store.py#L344) | method | used |  | F0099 |  |  |
| F0378 | 03_sap_data/repositories | `Store.create_outcome` | [backend/app/store.py:352](../backend/app/store.py#L352) | method | used |  | F0059, F0099, F0110 |  |  |
| F0379 | 03_sap_data/repositories | `Store._outcome` | [backend/app/store.py:357](../backend/app/store.py#L357) | method | used |  | F0380, F0381 |  |  |
| F0380 | 03_sap_data/repositories | `Store.list_outcomes` | [backend/app/store.py:362](../backend/app/store.py#L362) | method | used |  | F2052, F0059, F0110, F0255, F0261 |  |  |
| F0381 | 03_sap_data/repositories | `Store.record_outcome` | [backend/app/store.py:367](../backend/app/store.py#L367) | method | used |  | F0059, F0110 |  |  |
| F0382 | 03_sap_data/repositories | `Store.record_feedback` | [backend/app/store.py:380](../backend/app/store.py#L380) | method | used | Why an expert approved, modified or rejected a recommendation — a training label once the  | F0098 |  |  |
| F0383 | 03_sap_data/repositories | `Store.feedback` | [backend/app/store.py:385](../backend/app/store.py#L385) | method | used |  | F0388 |  |  |
| F0384 | 03_sap_data/repositories | `Store.consent` | [backend/app/store.py:390](../backend/app/store.py#L390) | method | used |  | F0252, F0385 |  |  |
| F0385 | 03_sap_data/repositories | `Store.set_consent` | [backend/app/store.py:394](../backend/app/store.py#L394) | method | used |  | F0058 |  |  |
| F0386 | 03_sap_data/repositories | `Store.get_setting` | [backend/app/store.py:400](../backend/app/store.py#L400) | method | used |  | F0089, F0090, F0387 |  |  |
| F0387 | 03_sap_data/repositories | `Store.set_setting` | [backend/app/store.py:404](../backend/app/store.py#L404) | method | used |  | F0091 |  |  |
| F0388 | 03_sap_data/repositories | `Store.decision_stats` | [backend/app/store.py:409](../backend/app/store.py#L409) | method | used | Acceptance and override (rejection) rates with the reasons experts gave. | F0255, F0261 |  |  |
| F0389 | 03_sap_data/repositories | `Store.counts` | [backend/app/store.py:428](../backend/app/store.py#L428) | method | used | Recommendation counts by status; optionally only for one SAP snapshot (one customer). | F0236, F0031, F0255, F0952 |  |  |
| F0390 | 03_sap_data/repositories | `TenantContext` | [backend/app/tenants.py:27](../backend/app/tenants.py#L27) | class | used |  | F0392, F2039, F2039, F0393, F2040 |  |  |
| F0391 | 03_sap_data/repositories | `TenantRegistry` | [backend/app/tenants.py:40](../backend/app/tenants.py#L40) | class | used |  | F2112, F2139, F0017, F0018, F0019, F0022, F0034, F0057, F0058, F0251, F0399 |  |  |
| F0392 | 03_sap_data/repositories | `TenantRegistry.__init__` | [backend/app/tenants.py:41](../backend/app/tenants.py#L41) | method | used (framework) |  |  |  |  |
| F0393 | 03_sap_data/repositories | `TenantRegistry.get` | [backend/app/tenants.py:68](../backend/app/tenants.py#L68) | method | used |  | F1791, F2168, F0017, F0033, F0253, F0254, F0255, F1822, F1892, F1895, F1897, F18 |  |  |
| F0394 | 03_sap_data/repositories | `TenantRegistry.catalogue` | [backend/app/tenants.py:88](../backend/app/tenants.py#L88) | method | used |  | F0034 |  |  |
| F0395 | 03_sap_data/repositories | `TenantRegistry.activate` | [backend/app/tenants.py:94](../backend/app/tenants.py#L94) | method | used |  | F0018 |  |  |
| F0396 | 03_sap_data/repositories | `TenantRegistry.deactivate` | [backend/app/tenants.py:98](../backend/app/tenants.py#L98) | method | used |  | F0018 |  |  |
| F0397 | 03_sap_data/repositories | `TenantRegistry.current_id` | [backend/app/tenants.py:102](../backend/app/tenants.py#L102) | method | used |  | F2112, F0019, F0022, F0034, F0057, F0058 |  |  |
| F0398 | 03_sap_data/repositories | `TenantProxy` | [backend/app/tenants.py:107](../backend/app/tenants.py#L107) | class | used | Attribute access is forwarded to the active tenant's object (sap / engine / insights / das | F0017 |  |  |
| F0399 | 03_sap_data/repositories | `TenantProxy.__init__` | [backend/app/tenants.py:110](../backend/app/tenants.py#L110) | method | used (framework) |  |  |  |  |
| F0400 | 03_sap_data/repositories | `TenantProxy.__getattr__` | [backend/app/tenants.py:114](../backend/app/tenants.py#L114) | method | used (framework) |  |  |  |  |
| F0401 | 03_sap_data/sap_connectors | `SapRepository` | [backend/app/sap.py:31](../backend/app/sap.py#L31) | class | used |  | F0452, F0483, F0193, F2072, F2073, F2074, F2157, F2039, F0922, F0933, F0943, F09 |  |  |
| F0402 | 03_sap_data/sap_connectors | `SapRepository.__init__` | [backend/app/sap.py:32](../backend/app/sap.py#L32) | method | used (framework) |  |  |  |  |
| F0403 | 03_sap_data/sap_connectors | `SapRepository._validate` | [backend/app/sap.py:37](../backend/app/sap.py#L37) | method | used (framework) |  | F0402 |  |  |
| F0404 | 03_sap_data/sap_connectors | `SapRepository.as_of` | [backend/app/sap.py:61](../backend/app/sap.py#L61) | method | used | Business date of the extract; all date logic is relative to it so results are reproducible | F0197, F0198, F0201, F0202, F0203, F0204, F0205, F0206, F0207, F0208, F0209, F02 |  |  |
| F0405 | 03_sap_data/sap_connectors | `SapRepository.snapshot` | [backend/app/sap.py:69](../backend/app/sap.py#L69) | method | used |  | F0453, F0454, F0461, F0248, F0023, F0025, F0026, F0031, F0033, F0059, F0066, F00 |  |  |
| F0406 | 03_sap_data/sap_connectors | `SapRepository.has` | [backend/app/sap.py:75](../backend/app/sap.py#L75) | method | used |  | F0196, F0197, F0212, F0224, F2073, F2074, F0255 |  |  |
| F0407 | 03_sap_data/sap_connectors | `SapRepository.section` | [backend/app/sap.py:78](../backend/app/sap.py#L78) | method | used |  | F0454, F0231, F0237, F0238, F0240, F0194, F0195, F0196, F0197, F0198, F0199, F02 |  |  |
| F0408 | 03_sap_data/sap_connectors | `SapRepository.codes` | [backend/app/sap.py:83](../backend/app/sap.py#L83) | method | used |  | F0409 |  |  |
| F0409 | 03_sap_data/sap_connectors | `SapRepository.validate_codes` | [backend/app/sap.py:86](../backend/app/sap.py#L86) | method | used |  | F0197, F0198, F0199, F0203, F0204, F0205, F0206, F0209, F0212, F0219, F0220, F02 |  |  |
| F0410 | 03_sap_data/sap_connectors | `SapRepository.material` | [backend/app/sap.py:92](../backend/app/sap.py#L92) | method | used |  | F0231, F0232, F0235, F0237, F0197, F0198, F0201, F0206, F0207, F0212, F0213, F02 |  |  |
| F0411 | 03_sap_data/sap_connectors | `SapRepository.supplier` | [backend/app/sap.py:96](../backend/app/sap.py#L96) | method | used |  | F0234, F0201, F0219, F0261, F0270 |  |  |
| F0412 | 03_sap_data/sap_connectors | `SapRepository.stock_rows` | [backend/app/sap.py:104](../backend/app/sap.py#L104) | method | used |  | F0197, F0413 |  |  |
| F0413 | 03_sap_data/sap_connectors | `SapRepository.on_hand` | [backend/app/sap.py:107](../backend/app/sap.py#L107) | method | used |  | F0197, F0198, F0205, F0206, F0210, F0212, F0226 |  |  |
| F0414 | 03_sap_data/sap_connectors | `SapRepository.odata` | [backend/app/sap.py:118](../backend/app/sap.py#L118) | method | used |  | F0038, F0102, F0103 |  |  |
| F0415 | 03_sap_data/sap_connectors | `SapRepository.metadata` | [backend/app/sap.py:138](../backend/app/sap.py#L138) | method | used |  | F2072, F0036 |  |  |
| F0416 | 03_sap_data/sql | `now_iso` | [backend/scinsight/db.py:18](../backend/scinsight/db.py#L18) | function | used |  | F0429, F0432, F0534, F0535, F0537, F0765, F1809, F1892, F1895, F1897, F1904, F19 |  |  |
| F0417 | 03_sap_data/sql | `ensure_postgres_database` | [backend/scinsight/db.py:22](../backend/scinsight/db.py#L22) | function | used | Create the target PostgreSQL database if it does not exist (existing Compose volumes / man | F1993 |  |  |
| F0418 | 03_sap_data/sql | `Database` | [backend/scinsight/db.py:39](../backend/scinsight/db.py#L39) | class | used |  | F1993, F1993, F0432, F0532, F0534, F0535, F0536, F0537, F0764, F1903, F0775, F03 |  |  |
| F0419 | 03_sap_data/sql | `Database.__init__` | [backend/scinsight/db.py:40](../backend/scinsight/db.py#L40) | method | used (framework) |  |  |  |  |
| F0420 | 03_sap_data/sql | `Database._sql` | [backend/scinsight/db.py:61](../backend/scinsight/db.py#L61) | method | used |  | F0421, F0423, F0424, F0425, F0427 |  |  |
| F0421 | 03_sap_data/sql | `Database.query` | [backend/scinsight/db.py:64](../backend/scinsight/db.py#L64) | method | used |  | F2015, F2027, F0422, F0429, F0532, F0537, F0766, F1847, F1860, F1887, F1907, F19 |  |  |
| F0422 | 03_sap_data/sql | `Database.one` | [backend/scinsight/db.py:71](../backend/scinsight/db.py#L71) | method | used |  | F0432, F0535, F0536, F1806, F0765, F1904, F1905, F1906, F1912, F1915, F0776, F03 |  |  |
| F0423 | 03_sap_data/sql | `Database.execute` | [backend/scinsight/db.py:75](../backend/scinsight/db.py#L75) | method | used |  | F0429, F0432, F0534, F0535, F0537, F1809, F1904, F1908, F1909, F1910, F1911, F19 |  |  |
| F0424 | 03_sap_data/sql | `Database.executemany` | [backend/scinsight/db.py:82](../backend/scinsight/db.py#L82) | method | used |  | F0752, F0432, F0433 |  |  |
| F0425 | 03_sap_data/sql | `Database.transaction` | [backend/scinsight/db.py:92](../backend/scinsight/db.py#L92) | method | used | Run several statements atomically (all or nothing). | F0352, F0358, F0423, F0424, F0426, F0428, F0535, F0765, F1808, F1897, F0340 |  |  |
| F0426 | 03_sap_data/sql | `Database.atomic` | [backend/scinsight/db.py:104](../backend/scinsight/db.py#L104) | method | used | Run fn(q) inside one transaction holding an exclusive lock; q(sql, params) returns rows. F | F0779, F0337, F0341 |  |  |
| F0427 | 03_sap_data/sql | `Database.atomic.q` | [backend/scinsight/db.py:114](../backend/scinsight/db.py#L114) | nested | used |  | F0426 |  |  |
| F0428 | 03_sap_data/sql | `Database._script` | [backend/scinsight/db.py:119](../backend/scinsight/db.py#L119) | method | used |  | F0429 |  |  |
| F0429 | 03_sap_data/sql | `Database.migrate` | [backend/scinsight/db.py:132](../backend/scinsight/db.py#L132) | method | used |  | F1993 |  |  |
| F0430 | 03_sap_data/synthetic_sap | `key_hash` | [backend/scinsight/fixtures.py:93](../backend/scinsight/fixtures.py#L93) | function | used |  | F0432, F0776 |  |  |
| F0431 | 03_sap_data/synthetic_sap | `_d` | [backend/scinsight/fixtures.py:97](../backend/scinsight/fixtures.py#L97) | function | used |  | F0432 |  |  |
| F0432 | 03_sap_data/synthetic_sap | `load` | [backend/scinsight/fixtures.py:101](../backend/scinsight/fixtures.py#L101) | function | used | Load the synthetic fixtures (idempotent: rows are replaced by primary key). Returns counts | F1993 |  |  |
| F0433 | 03_sap_data/synthetic_sap | `load.upsert` | [backend/scinsight/fixtures.py:113](../backend/scinsight/fixtures.py#L113) | nested | used |  | F0432 |  |  |
| F0434 | 03_sap_data/synthetic_sap | `iso` | [scripts/generate_tenants.py:242](../scripts/generate_tenants.py#L242) | function | used |  | F0436 |  |  |
| F0435 | 03_sap_data/synthetic_sap | `person` | [scripts/generate_tenants.py:246](../scripts/generate_tenants.py#L246) | function | used |  | F0436 |  |  |
| F0436 | 03_sap_data/synthetic_sap | `build` | [scripts/generate_tenants.py:252](../scripts/generate_tenants.py#L252) | function | used |  | F0437 |  |  |
| F0437 | 03_sap_data/synthetic_sap | `main` | [scripts/generate_tenants.py:379](../scripts/generate_tenants.py#L379) | function | used |  |  |  |  |
| F0438 | 04_ai_ml/agent_tools | `CopilotBackend` | [backend/app/copilot.py:21](../backend/app/copilot.py#L21) | class | used |  | F0483, F0484 |  |  |
| F0439 | 04_ai_ml/agent_tools | `CopilotBackend.snapshot` | [backend/app/copilot.py:22](../backend/app/copilot.py#L22) | method | used (framework) |  |  |  |  |
| F0440 | 04_ai_ml/agent_tools | `CopilotBackend.factory_readiness` | [backend/app/copilot.py:23](../backend/app/copilot.py#L23) | method | used (framework) |  |  |  |  |
| F0441 | 04_ai_ml/agent_tools | `CopilotBackend.stock_balance` | [backend/app/copilot.py:24](../backend/app/copilot.py#L24) | method | used (framework) |  |  |  |  |
| F0442 | 04_ai_ml/agent_tools | `CopilotBackend.demand_forecast` | [backend/app/copilot.py:25](../backend/app/copilot.py#L25) | method | used (framework) |  |  |  |  |
| F0443 | 04_ai_ml/agent_tools | `CopilotBackend.supplier_risk` | [backend/app/copilot.py:26](../backend/app/copilot.py#L26) | method | used (framework) |  |  |  |  |
| F0444 | 04_ai_ml/agent_tools | `CopilotBackend.quality_status` | [backend/app/copilot.py:27](../backend/app/copilot.py#L27) | method | used (framework) |  |  |  |  |
| F0445 | 04_ai_ml/agent_tools | `CopilotBackend.logistics_status` | [backend/app/copilot.py:28](../backend/app/copilot.py#L28) | method | used (framework) |  |  |  |  |
| F0446 | 04_ai_ml/agent_tools | `CopilotBackend.inventory` | [backend/app/copilot.py:29](../backend/app/copilot.py#L29) | method | used (framework) |  |  |  |  |
| F0447 | 04_ai_ml/agent_tools | `CopilotBackend.sales_orders` | [backend/app/copilot.py:30](../backend/app/copilot.py#L30) | method | used (framework) |  |  |  |  |
| F0448 | 04_ai_ml/agent_tools | `CopilotBackend.stocktake` | [backend/app/copilot.py:31](../backend/app/copilot.py#L31) | method | used (framework) |  |  |  |  |
| F0449 | 04_ai_ml/agent_tools | `CopilotBackend.search_knowledge` | [backend/app/copilot.py:32](../backend/app/copilot.py#L32) | method | used (framework) |  |  |  |  |
| F0450 | 04_ai_ml/agent_tools | `CopilotBackend.submit_recommendation` | [backend/app/copilot.py:33](../backend/app/copilot.py#L33) | method | used (framework) |  |  |  |  |
| F0451 | 04_ai_ml/agent_tools | `LocalBackend` | [backend/app/copilot.py:36](../backend/app/copilot.py#L36) | class | used | In-process engine with its own ledger. Used by unit tests and when no gateway URL is confi | F0483 |  |  |
| F0452 | 04_ai_ml/agent_tools | `LocalBackend.__init__` | [backend/app/copilot.py:39](../backend/app/copilot.py#L39) | method | used (framework) |  |  |  |  |
| F0453 | 04_ai_ml/agent_tools | `LocalBackend._save` | [backend/app/copilot.py:46](../backend/app/copilot.py#L46) | method | used |  | F0455, F0456, F0457, F0458, F0459, F0460, F0462, F0463 |  |  |
| F0454 | 04_ai_ml/agent_tools | `LocalBackend.snapshot` | [backend/app/copilot.py:50](../backend/app/copilot.py#L50) | method | used |  | F0541, F0590, F0486, F0503 |  |  |
| F0455 | 04_ai_ml/agent_tools | `LocalBackend.factory_readiness` | [backend/app/copilot.py:58](../backend/app/copilot.py#L58) | method | used |  | F0592, F0487, F0504 |  |  |
| F0456 | 04_ai_ml/agent_tools | `LocalBackend.stock_balance` | [backend/app/copilot.py:62](../backend/app/copilot.py#L62) | method | used |  | F0593, F0488, F0505 |  |  |
| F0457 | 04_ai_ml/agent_tools | `LocalBackend.demand_forecast` | [backend/app/copilot.py:66](../backend/app/copilot.py#L66) | method | used |  | F0506 |  |  |
| F0458 | 04_ai_ml/agent_tools | `LocalBackend.supplier_risk` | [backend/app/copilot.py:70](../backend/app/copilot.py#L70) | method | used |  | F0594, F0489, F0507 |  |  |
| F0459 | 04_ai_ml/agent_tools | `LocalBackend.quality_status` | [backend/app/copilot.py:73](../backend/app/copilot.py#L73) | method | used |  | F0595, F0490, F0508 |  |  |
| F0460 | 04_ai_ml/agent_tools | `LocalBackend.logistics_status` | [backend/app/copilot.py:76](../backend/app/copilot.py#L76) | method | used |  | F0596, F0491, F0509 |  |  |
| F0461 | 04_ai_ml/agent_tools | `LocalBackend.inventory` | [backend/app/copilot.py:79](../backend/app/copilot.py#L79) | method | used |  | F0597, F0492, F0510 |  |  |
| F0462 | 04_ai_ml/agent_tools | `LocalBackend.sales_orders` | [backend/app/copilot.py:82](../backend/app/copilot.py#L82) | method | used |  | F0493, F0511 |  |  |
| F0463 | 04_ai_ml/agent_tools | `LocalBackend.stocktake` | [backend/app/copilot.py:85](../backend/app/copilot.py#L85) | method | used |  | F0494, F0512 |  |  |
| F0464 | 04_ai_ml/agent_tools | `LocalBackend.search_knowledge` | [backend/app/copilot.py:88](../backend/app/copilot.py#L88) | method | used |  | F0542, F0598, F0495, F0513 |  |  |
| F0465 | 04_ai_ml/agent_tools | `LocalBackend.submit_recommendation` | [backend/app/copilot.py:91](../backend/app/copilot.py#L91) | method | used |  | F0552, F0603 |  |  |
| F0466 | 04_ai_ml/agent_tools | `ApiError` | [backend/app/copilot.py:95](../backend/app/copilot.py#L95) | class | used |  | F0469 |  |  |
| F0467 | 04_ai_ml/agent_tools | `ApiBackend` | [backend/app/copilot.py:99](../backend/app/copilot.py#L99) | class | used | HTTP client for the FastAPI gateway; every call is authenticated and audited by the gatewa | F0483 |  |  |
| F0468 | 04_ai_ml/agent_tools | `ApiBackend.__init__` | [backend/app/copilot.py:102](../backend/app/copilot.py#L102) | method | used (framework) |  |  |  |  |
| F0469 | 04_ai_ml/agent_tools | `ApiBackend._call` | [backend/app/copilot.py:105](../backend/app/copilot.py#L105) | method | used |  | F0471, F0472, F0473, F0474, F0475, F0476, F0477, F0478, F0479, F0480, F0481, F04 |  |  |
| F0470 | 04_ai_ml/agent_tools | `ApiBackend._clean` | [backend/app/copilot.py:115](../backend/app/copilot.py#L115) | method | used |  | F0474, F0476, F0477, F0478, F0479, F0481 |  |  |
| F0471 | 04_ai_ml/agent_tools | `ApiBackend.snapshot` | [backend/app/copilot.py:119](../backend/app/copilot.py#L119) | method | used |  | F0541, F0590, F0486, F0503 |  |  |
| F0472 | 04_ai_ml/agent_tools | `ApiBackend.factory_readiness` | [backend/app/copilot.py:122](../backend/app/copilot.py#L122) | method | used |  | F0592, F0487, F0504 |  |  |
| F0473 | 04_ai_ml/agent_tools | `ApiBackend.stock_balance` | [backend/app/copilot.py:125](../backend/app/copilot.py#L125) | method | used |  | F0593, F0488, F0505 |  |  |
| F0474 | 04_ai_ml/agent_tools | `ApiBackend.demand_forecast` | [backend/app/copilot.py:128](../backend/app/copilot.py#L128) | method | used |  | F0506 |  |  |
| F0475 | 04_ai_ml/agent_tools | `ApiBackend.supplier_risk` | [backend/app/copilot.py:131](../backend/app/copilot.py#L131) | method | used |  | F0594, F0489, F0507 |  |  |
| F0476 | 04_ai_ml/agent_tools | `ApiBackend.quality_status` | [backend/app/copilot.py:134](../backend/app/copilot.py#L134) | method | used |  | F0595, F0490, F0508 |  |  |
| F0477 | 04_ai_ml/agent_tools | `ApiBackend.logistics_status` | [backend/app/copilot.py:137](../backend/app/copilot.py#L137) | method | used |  | F0596, F0491, F0509 |  |  |
| F0478 | 04_ai_ml/agent_tools | `ApiBackend.inventory` | [backend/app/copilot.py:140](../backend/app/copilot.py#L140) | method | used |  | F0597, F0492, F0510 |  |  |
| F0479 | 04_ai_ml/agent_tools | `ApiBackend.sales_orders` | [backend/app/copilot.py:143](../backend/app/copilot.py#L143) | method | used |  | F0493, F0511 |  |  |
| F0480 | 04_ai_ml/agent_tools | `ApiBackend.stocktake` | [backend/app/copilot.py:146](../backend/app/copilot.py#L146) | method | used |  | F0494, F0512 |  |  |
| F0481 | 04_ai_ml/agent_tools | `ApiBackend.search_knowledge` | [backend/app/copilot.py:149](../backend/app/copilot.py#L149) | method | used |  | F0542, F0598, F0495, F0513 |  |  |
| F0482 | 04_ai_ml/agent_tools | `ApiBackend.submit_recommendation` | [backend/app/copilot.py:152](../backend/app/copilot.py#L152) | method | used |  | F0552, F0603 |  |  |
| F0483 | 04_ai_ml/agent_tools | `build_backend` | [backend/app/copilot.py:156](../backend/app/copilot.py#L156) | function | used |  | F0484 |  |  |
| F0484 | 04_ai_ml/agent_tools | `get_backend` | [backend/app/copilot.py:168](../backend/app/copilot.py#L168) | function | used |  | F0541, F0542, F0548, F0552, F0583, F0590, F0592, F0593, F0594, F0595, F0596, F05 |  |  |
| F0485 | 04_ai_ml/agent_tools | `_dump` | [backend/app/mcp_server.py:29](../backend/app/mcp_server.py#L29) | function | used |  | F0486, F0487, F0488, F0489, F0490, F0491, F0492, F0493, F0494, F0495 |  |  |
| F0486 | 04_ai_ml/agent_tools | `sap_snapshot` | [backend/app/mcp_server.py:36](../backend/app/mcp_server.py#L36) | function | used | SAP snapshot provenance and valid plant, material and supplier codes. Call first. |  |  |  |
| F0487 | 04_ai_ml/agent_tools | `factory_material_readiness` | [backend/app/mcp_server.py:42](../backend/app/mcp_server.py#L42) | function | used | BOM material readiness for a production run (plant FR10/FR20/TPM1, finished good code, uni |  |  |  |
| F0488 | 04_ai_ml/agent_tools | `warehouse_stock_balance` | [backend/app/mcp_server.py:48](../backend/app/mcp_server.py#L48) | function | used | XGBoost demand forecast and OR-Tools transfer proposals across DC01, DC21 and DC22 for one |  |  |  |
| F0489 | 04_ai_ml/agent_tools | `supplier_risk` | [backend/app/mcp_server.py:54](../backend/app/mcp_server.py#L54) | function | used | Supplier scorecard: OTIF, delays, quality rejects, open PO exposure and single-source risk |  |  |  |
| F0490 | 04_ai_ml/agent_tools | `quality_status` | [backend/app/mcp_server.py:60](../backend/app/mcp_server.py#L60) | function | used | Open inspection lots, blocked/expired batches and affected production orders. |  |  |  |
| F0491 | 04_ai_ml/agent_tools | `logistics_status` | [backend/app/mcp_server.py:66](../backend/app/mcp_server.py#L66) | function | used | In-transit shipments, delays, revised ETAs and escalations. |  |  |  |
| F0492 | 04_ai_ml/agent_tools | `inventory_overview` | [backend/app/mcp_server.py:72](../backend/app/mcp_server.py#L72) | function | used | Finished-goods stock, days of cover, open sales orders and in-transit stock by warehouse. |  |  |  |
| F0493 | 04_ai_ml/agent_tools | `sales_order_fulfilment` | [backend/app/mcp_server.py:78](../backend/app/mcp_server.py#L78) | function | used | Open sales orders: on-time status, shortfalls and the cheapest on-time transfer or partial |  |  |  |
| F0494 | 04_ai_ml/agent_tools | `stocktake_reconciliation` | [backend/app/mcp_server.py:84](../backend/app/mcp_server.py#L84) | function | used | Explain stock count differences with evidence and recommend posting, adjustment or recount |  |  |  |
| F0495 | 04_ai_ml/agent_tools | `search_governed_knowledge` | [backend/app/mcp_server.py:90](../backend/app/mcp_server.py#L90) | function | used | Search approved contracts, SOPs, quality policies, product specs and logistics policies. C |  |  |  |
| F0496 | 04_ai_ml/agent_tools | `health` | [backend/app/mcp_server.py:96](../backend/app/mcp_server.py#L96) | route | used |  |  | GET /health |  |
| F0497 | 04_ai_ml/agent_tools | `ApiKeyMiddleware` | [backend/app/mcp_server.py:101](../backend/app/mcp_server.py#L101) | class | used | Bearer or X-API-Key check for /mcp; keys come from MCP_API_KEYS (comma separated). | F0500 |  |  |
| F0498 | 04_ai_ml/agent_tools | `ApiKeyMiddleware.__init__` | [backend/app/mcp_server.py:104](../backend/app/mcp_server.py#L104) | method | used (framework) |  |  |  |  |
| F0499 | 04_ai_ml/agent_tools | `ApiKeyMiddleware.dispatch` | [backend/app/mcp_server.py:108](../backend/app/mcp_server.py#L108) | method | used (framework) |  |  |  |  |
| F0500 | 04_ai_ml/agent_tools | `create_mcp_app` | [backend/app/mcp_server.py:117](../backend/app/mcp_server.py#L117) | function | used |  | F0951 |  |  |
| F0501 | 04_ai_ml/agent_tools | `_dump` | [backend/app/tools.py:13](../backend/app/tools.py#L13) | function | used |  | F0502 |  |  |
| F0502 | 04_ai_ml/agent_tools | `_safe` | [backend/app/tools.py:18](../backend/app/tools.py#L18) | function | used |  | F0503, F0504, F0505, F0506, F0507, F0508, F0509, F0510, F0511, F0512, F0513 |  |  |
| F0503 | 04_ai_ml/agent_tools | `sap_snapshot` | [backend/app/tools.py:25](../backend/app/tools.py#L25) | function | used | Return SAP snapshot provenance plus valid plant, material and supplier codes. Call this be |  |  |  |
| F0504 | 04_ai_ml/agent_tools | `factory_material_readiness` | [backend/app/tools.py:31](../backend/app/tools.py#L31) | function | used | Check BOM material readiness for a production run. |  |  |  |
| F0505 | 04_ai_ml/agent_tools | `warehouse_stock_balance` | [backend/app/tools.py:44](../backend/app/tools.py#L44) | function | used | Forecast demand (XGBoost) and optimise stock transfers between DC01, DC21 and DC22 (OR-Too |  |  |  |
| F0506 | 04_ai_ml/agent_tools | `demand_forecast` | [backend/app/tools.py:50](../backend/app/tools.py#L50) | function | used | XGBoost daily demand forecast for a finished good, optionally for one warehouse (DC01, DC2 |  |  |  |
| F0507 | 04_ai_ml/agent_tools | `supplier_risk` | [backend/app/tools.py:56](../backend/app/tools.py#L56) | function | used | Supplier scorecard: OTIF, delays, quality rejects, open PO exposure, single-source risk. A |  |  |  |
| F0508 | 04_ai_ml/agent_tools | `quality_status` | [backend/app/tools.py:62](../backend/app/tools.py#L62) | function | used | Quality inspection lots (QM): inspection/blocked/expired batches and which production orde |  |  |  |
| F0509 | 04_ai_ml/agent_tools | `logistics_status` | [backend/app/tools.py:68](../backend/app/tools.py#L68) | function | used | In-transit shipments, delays, revised ETAs and escalations for a warehouse and/or material |  |  |  |
| F0510 | 04_ai_ml/agent_tools | `inventory_overview` | [backend/app/tools.py:74](../backend/app/tools.py#L74) | function | used | Finished-goods stock, days of cover, open sales orders and in-transit stock by warehouse. |  |  |  |
| F0511 | 04_ai_ml/agent_tools | `sales_order_fulfilment` | [backend/app/tools.py:80](../backend/app/tools.py#L80) | function | used | Open sales orders: can each ship on time from DC stock + inbound? Shortfalls get the cheap |  |  |  |
| F0512 | 04_ai_ml/agent_tools | `stocktake_reconciliation` | [backend/app/tools.py:86](../backend/app/tools.py#L86) | function | used | Explain stock count differences (unposted goods movements, scrap not posted) and recommend |  |  |  |
| F0513 | 04_ai_ml/agent_tools | `search_governed_knowledge` | [backend/app/tools.py:92](../backend/app/tools.py#L92) | function | used | Search approved supplier contracts, SOPs, quality policies, product specs and logistics po |  |  |  |
| F0514 | 04_ai_ml/evaluation | `http` | [scripts/scinsight_compare.py:30](../scripts/scinsight_compare.py#L30) | function | used |  | F0515, F0516, F0517, F0520 |  |  |
| F0515 | 04_ai_ml/evaluation | `sci` | [scripts/scinsight_compare.py:46](../scripts/scinsight_compare.py#L46) | function | used |  | F0519, F0520 |  |  |
| F0516 | 04_ai_ml/evaluation | `ask_flowise` | [scripts/scinsight_compare.py:51](../scripts/scinsight_compare.py#L51) | function | used |  | F0520, F0521 |  |  |
| F0517 | 04_ai_ml/evaluation | `ask_langgraph` | [scripts/scinsight_compare.py:61](../scripts/scinsight_compare.py#L61) | function | used |  | F0520, F0521 |  |  |
| F0518 | 04_ai_ml/evaluation | `path_get` | [scripts/scinsight_compare.py:78](../scripts/scinsight_compare.py#L78) | function | used |  | F0519 |  |  |
| F0519 | 04_ai_ml/evaluation | `check_facts` | [scripts/scinsight_compare.py:89](../scripts/scinsight_compare.py#L89) | function | used |  | F0521 |  |  |
| F0520 | 04_ai_ml/evaluation | `approval_cycle` | [scripts/scinsight_compare.py:107](../scripts/scinsight_compare.py#L107) | function | used | Ask a transfer question, approve as the warehouse manager in the API, resume, expect the v | F0521 |  |  |
| F0521 | 04_ai_ml/evaluation | `main` | [scripts/scinsight_compare.py:128](../scripts/scinsight_compare.py#L128) | function | used |  |  |  |  |
| F0522 | 04_ai_ml/evaluation | `write_report` | [scripts/scinsight_compare.py:159](../scripts/scinsight_compare.py#L159) | function | used |  | F0521 |  |  |
| F0523 | 04_ai_ml/evaluation | `write_report.stats` | [scripts/scinsight_compare.py:160](../scripts/scinsight_compare.py#L160) | nested | used |  | F0522 |  |  |
| F0524 | 04_ai_ml/forecasting | `_history` | [backend/app/forecasting.py:10](../backend/app/forecasting.py#L10) | function | used |  | F0527, F0529, F0530, F0531 |  |  |
| F0525 | 04_ai_ml/forecasting | `_features` | [backend/app/forecasting.py:16](../backend/app/forecasting.py#L16) | function | used |  | F0526, F0530, F0531 |  |  |
| F0526 | 04_ai_ml/forecasting | `_fit_predict` | [backend/app/forecasting.py:28](../backend/app/forecasting.py#L28) | function | used |  | F0527, F0529 |  |  |
| F0527 | 04_ai_ml/forecasting | `backtest` | [backend/app/forecasting.py:40](../backend/app/forecasting.py#L40) | function | used | Forecast vs actuals: train without the last `holdout_days`, predict them, then forecast th | F0209 |  |  |
| F0528 | 04_ai_ml/forecasting | `_errors` | [backend/app/forecasting.py:62](../backend/app/forecasting.py#L62) | function | used |  | F0529 |  |  |
| F0529 | 04_ai_ml/forecasting | `evaluate_models` | [backend/app/forecasting.py:69](../backend/app/forecasting.py#L69) | function | used | Model quality on the same holdout: XGBoost vs a seasonal-naive baseline (same weekday last | F0254, F0261 |  |  |
| F0530 | 04_ai_ml/forecasting | `pooled_evaluation` | [backend/app/forecasting.py:91](../backend/app/forecasting.py#L91) | function | used | Train one model on demand-normalised series from several customers and score it on the tar | F0254 |  |  |
| F0531 | 04_ai_ml/forecasting | `forecast` | [backend/app/forecasting.py:129](../backend/app/forecasting.py#L129) | function | used |  | F0198, F0199, F0212 |  |  |
| F0532 | 04_ai_ml/forecasting | `_rows` | [backend/scinsight/learning.py:24](../backend/scinsight/learning.py#L24) | function | used |  | F0534, F0536 |  |  |
| F0533 | 04_ai_ml/forecasting | `_features` | [backend/scinsight/learning.py:38](../backend/scinsight/learning.py#L38) | function | used |  | F0534, F0536 |  |  |
| F0534 | 04_ai_ml/forecasting | `train_lead_time_model` | [backend/scinsight/learning.py:43](../backend/scinsight/learning.py#L43) | function | used |  | F2024 |  |  |
| F0535 | 04_ai_ml/forecasting | `promote` | [backend/scinsight/learning.py:73](../backend/scinsight/learning.py#L73) | function | used |  | F2025 |  |  |
| F0536 | 04_ai_ml/forecasting | `predict_lead_time` | [backend/scinsight/learning.py:88](../backend/scinsight/learning.py#L88) | function | used | Re-fit the promoted configuration deterministically on all receipts and predict (no pickle | F0332 |  |  |
| F0537 | 04_ai_ml/forecasting | `retraining_request` | [backend/scinsight/learning.py:101](../backend/scinsight/learning.py#L101) | function | used |  | F2026 |  |  |
| F0538 | 04_ai_ml/langgraph | `AgentFlowState` | [backend/app/agentflow.py:61](../backend/app/agentflow.py#L61) | class | used |  | F0540, F0541, F0542, F0544, F0545, F0546, F0549, F0551, F0552, F0553 |  |  |
| F0539 | 04_ai_ml/langgraph | `RouteDecision` | [backend/app/agentflow.py:71](../backend/app/agentflow.py#L71) | pydantic_model | used | Pick exactly one role specialist for the planner's latest request. | F0544 |  |  |
| F0540 | 04_ai_ml/langgraph | `_last_human` | [backend/app/agentflow.py:82](../backend/app/agentflow.py#L82) | function | used |  | F0542, F0544, F0551 |  |  |
| F0541 | 04_ai_ml/langgraph | `sap_read` | [backend/app/agentflow.py:87](../backend/app/agentflow.py#L87) | function | used | Read the SAP S/4HANA snapshot provenance and valid codes (read-only; writes are blocked by |  |  |  |
| F0542 | 04_ai_ml/langgraph | `rag_retrieve` | [backend/app/agentflow.py:99](../backend/app/agentflow.py#L99) | function | used | Retrieve governed policy context (contracts, SOPs, quality and logistics policies) from Po |  |  |  |
| F0543 | 04_ai_ml/langgraph | `_keyword_route` | [backend/app/agentflow.py:122](../backend/app/agentflow.py#L122) | function | used |  | F0544 |  |  |
| F0544 | 04_ai_ml/langgraph | `supervisor` | [backend/app/agentflow.py:132](../backend/app/agentflow.py#L132) | function | used |  |  |  |  |
| F0545 | 04_ai_ml/langgraph | `route_next` | [backend/app/agentflow.py:147](../backend/app/agentflow.py#L147) | function | used |  |  |  |  |
| F0546 | 04_ai_ml/langgraph | `_conversation` | [backend/app/agentflow.py:152](../backend/app/agentflow.py#L152) | function | used | Prior human turns and final answers only, so specialists never see dangling tool calls fro | F0551 |  |  |
| F0547 | 04_ai_ml/langgraph | `_analysis_from` | [backend/app/agentflow.py:158](../backend/app/agentflow.py#L158) | function | used |  | F0551 |  |  |
| F0548 | 04_ai_ml/langgraph | `_deterministic` | [backend/app/agentflow.py:171](../backend/app/agentflow.py#L171) | function | used |  | F0551 |  |  |
| F0549 | 04_ai_ml/langgraph | `_knowledge_block` | [backend/app/agentflow.py:192](../backend/app/agentflow.py#L192) | function | used |  | F0551 |  |  |
| F0550 | 04_ai_ml/langgraph | `_specialist` | [backend/app/agentflow.py:200](../backend/app/agentflow.py#L200) | function | used |  |  |  |  |
| F0551 | 04_ai_ml/langgraph | `_specialist.node` | [backend/app/agentflow.py:206](../backend/app/agentflow.py#L206) | nested | used |  | F0550 |  |  |
| F0552 | 04_ai_ml/langgraph | `approval_gate` | [backend/app/agentflow.py:234](../backend/app/agentflow.py#L234) | function | used | Planner Human Input: submit the specialist's stored analysis to the manager queue, or disc |  |  |  |
| F0553 | 04_ai_ml/langgraph | `boundary` | [backend/app/agentflow.py:262](../backend/app/agentflow.py#L262) | function | used |  |  |  |  |
| F0554 | 04_ai_ml/langgraph | `harness_of` | [backend/app/deep_agent.py:62](../backend/app/deep_agent.py#L62) | function | used | Validated harness: stored settings merged over the defaults (invalid or unknown values are | F0565, F0571, F0832, F0833 |  |  |
| F0555 | 04_ai_ml/langgraph | `system_prompt` | [backend/app/deep_agent.py:67](../backend/app/deep_agent.py#L67) | function | used |  | F0565, F0832, F0833 |  |  |
| F0556 | 04_ai_ml/langgraph | `_this_run` | [backend/app/deep_agent.py:94](../backend/app/deep_agent.py#L94) | function | used | Messages of the current run: everything after the last user message (limits reset on every | F0559, F0560 |  |  |
| F0557 | 04_ai_ml/langgraph | `HarnessGuard` | [backend/app/deep_agent.py:100](../backend/app/deep_agent.py#L100) | class | used | Loop controls of the harness, enforced around each model and tool call (no extra graph ste | F0565, F0833 |  |  |
| F0558 | 04_ai_ml/langgraph | `HarnessGuard.__init__` | [backend/app/deep_agent.py:108](../backend/app/deep_agent.py#L108) | method | used (framework) |  |  |  |  |
| F0559 | 04_ai_ml/langgraph | `HarnessGuard._stop_message` | [backend/app/deep_agent.py:112](../backend/app/deep_agent.py#L112) | method | used |  | F0561, F0562 |  |  |
| F0560 | 04_ai_ml/langgraph | `HarnessGuard._refusal` | [backend/app/deep_agent.py:119](../backend/app/deep_agent.py#L119) | method | used |  | F0563, F0564 |  |  |
| F0561 | 04_ai_ml/langgraph | `HarnessGuard.wrap_model_call` | [backend/app/deep_agent.py:145](../backend/app/deep_agent.py#L145) | method | used |  | F0833 |  |  |
| F0562 | 04_ai_ml/langgraph | `HarnessGuard.awrap_model_call` | [backend/app/deep_agent.py:148](../backend/app/deep_agent.py#L148) | method | used (framework) |  |  |  |  |
| F0563 | 04_ai_ml/langgraph | `HarnessGuard.wrap_tool_call` | [backend/app/deep_agent.py:151](../backend/app/deep_agent.py#L151) | method | used |  | F0833 |  |  |
| F0564 | 04_ai_ml/langgraph | `HarnessGuard.awrap_tool_call` | [backend/app/deep_agent.py:154](../backend/app/deep_agent.py#L154) | method | used (framework) |  |  |  |  |
| F0565 | 04_ai_ml/langgraph | `build_deep_agent` | [backend/app/deep_agent.py:158](../backend/app/deep_agent.py#L158) | function | used | The Deep Agent for one harness (compiled LangGraph with model, tools and subagent task too | F0566, F0831, F0832, F0833 |  |  |
| F0566 | 04_ai_ml/langgraph | `_agent_for` | [backend/app/deep_agent.py:180](../backend/app/deep_agent.py#L180) | function | used |  | F0571 |  |  |
| F0567 | 04_ai_ml/langgraph | `ResearchState` | [backend/app/deep_agent.py:187](../backend/app/deep_agent.py#L187) | class | used |  | F0571, F0572 |  |  |
| F0568 | 04_ai_ml/langgraph | `ResearchInput` | [backend/app/deep_agent.py:194](../backend/app/deep_agent.py#L194) | class | used | What a run takes (Studio's Input form): the question, and optionally harness overrides for | F0572 |  |  |
| F0569 | 04_ai_ml/langgraph | `HarnessConfig` | [backend/app/deep_agent.py:199](../backend/app/deep_agent.py#L199) | pydantic_model | used | Assistant context: Studio's configuration panel shows every harness setting with its curre | F0570, F0571, F0572 |  |  |
| F0570 | 04_ai_ml/langgraph | `_context_harness` | [backend/app/deep_agent.py:204](../backend/app/deep_agent.py#L204) | function | used | Harness settings given in the run/assistant context (only the ones actually set, so defaul | F0571 |  |  |
| F0571 | 04_ai_ml/langgraph | `deep_research` | [backend/app/deep_agent.py:211](../backend/app/deep_agent.py#L211) | function | used | Run the Deep Agent configured by this run's harness settings. | F0572 |  |  |
| F0572 | 04_ai_ml/langgraph | `build_graph` | [backend/app/deep_agent.py:225](../backend/app/deep_agent.py#L225) | function | used |  | F0612 |  |  |
| F0573 | 04_ai_ml/langgraph | `_last_text` | [backend/app/graphs.py:51](../backend/app/graphs.py#L51) | function | used |  | F0575, F0584 |  |  |
| F0574 | 04_ai_ml/langgraph | `guard` | [backend/app/graphs.py:55](../backend/app/graphs.py#L55) | function | used |  |  |  |  |
| F0575 | 04_ai_ml/langgraph | `route_after_guard` | [backend/app/graphs.py:59](../backend/app/graphs.py#L59) | function | used |  |  |  |  |
| F0576 | 04_ai_ml/langgraph | `refuse` | [backend/app/graphs.py:65](../backend/app/graphs.py#L65) | function | used |  |  |  |  |
| F0577 | 04_ai_ml/langgraph | `_tool_rounds` | [backend/app/graphs.py:69](../backend/app/graphs.py#L69) | function | used |  | F0580 |  |  |
| F0578 | 04_ai_ml/langgraph | `ChatState` | [backend/app/graphs.py:79](../backend/app/graphs.py#L79) | class | used |  | F0580 |  |  |
| F0579 | 04_ai_ml/langgraph | `_role_setup` | [backend/app/graphs.py:83](../backend/app/graphs.py#L83) | function | used | System prompt and tool set for the role's specialised agent; no role = the general copilot | F0580, F0961 |  |  |
| F0580 | 04_ai_ml/langgraph | `agent` | [backend/app/graphs.py:95](../backend/app/graphs.py#L95) | function | used |  |  |  |  |
| F0581 | 04_ai_ml/langgraph | `_first_human` | [backend/app/graphs.py:109](../backend/app/graphs.py#L109) | function | used |  | F0580 |  |  |
| F0582 | 04_ai_ml/langgraph | `route_after_agent` | [backend/app/graphs.py:116](../backend/app/graphs.py#L116) | function | used |  |  |  |  |
| F0583 | 04_ai_ml/langgraph | `fallback_answer` | [backend/app/graphs.py:121](../backend/app/graphs.py#L121) | function | used | Deterministic keyword router used when no LLM is configured; it only restates engine outpu | F0580, F0584 |  |  |
| F0584 | 04_ai_ml/langgraph | `fallback` | [backend/app/graphs.py:149](../backend/app/graphs.py#L149) | function | used |  |  |  |  |
| F0585 | 04_ai_ml/langgraph | `traced` | [backend/app/graphs.py:167](../backend/app/graphs.py#L167) | function | used | Attach Langfuse tracing to a compiled graph (still a Pregel graph, so LangGraph Server acc |  |  |  |
| F0586 | 04_ai_ml/langgraph | `BusinessState` | [backend/app/graphs.py:180](../backend/app/graphs.py#L180) | class | used |  | F0589, F0590, F0591, F0592, F0593, F0594, F0595, F0596, F0597, F0598, F0599, F06 |  |  |
| F0587 | 04_ai_ml/langgraph | `ExtractedRequest` | [backend/app/graphs.py:202](../backend/app/graphs.py#L202) | pydantic_model | used | Structured parameters for a supply-chain request. Leave a field empty when it is not state | F0589 |  |  |
| F0588 | 04_ai_ml/langgraph | `_regex_extract` | [backend/app/graphs.py:214](../backend/app/graphs.py#L214) | function | used |  | F0543, F0548, F0589 |  |  |
| F0589 | 04_ai_ml/langgraph | `intake` | [backend/app/graphs.py:248](../backend/app/graphs.py#L248) | function | used | Fill missing parameters from free text: Qwen structured output, deterministic regex as fal |  |  |  |
| F0590 | 04_ai_ml/langgraph | `validate` | [backend/app/graphs.py:271](../backend/app/graphs.py#L271) | function | used |  |  |  |  |
| F0591 | 04_ai_ml/langgraph | `route_workflow` | [backend/app/graphs.py:299](../backend/app/graphs.py#L299) | function | used |  |  |  |  |
| F0592 | 04_ai_ml/langgraph | `run_factory` | [backend/app/graphs.py:303](../backend/app/graphs.py#L303) | function | used |  |  |  |  |
| F0593 | 04_ai_ml/langgraph | `run_balance` | [backend/app/graphs.py:308](../backend/app/graphs.py#L308) | function | used |  |  |  |  |
| F0594 | 04_ai_ml/langgraph | `run_supplier` | [backend/app/graphs.py:313](../backend/app/graphs.py#L313) | function | used |  |  |  |  |
| F0595 | 04_ai_ml/langgraph | `run_quality` | [backend/app/graphs.py:318](../backend/app/graphs.py#L318) | function | used |  |  |  |  |
| F0596 | 04_ai_ml/langgraph | `run_logistics` | [backend/app/graphs.py:323](../backend/app/graphs.py#L323) | function | used |  |  |  |  |
| F0597 | 04_ai_ml/langgraph | `run_inventory` | [backend/app/graphs.py:328](../backend/app/graphs.py#L328) | function | used |  |  |  |  |
| F0598 | 04_ai_ml/langgraph | `policy_context` | [backend/app/graphs.py:343](../backend/app/graphs.py#L343) | function | used |  |  |  |  |
| F0599 | 04_ai_ml/langgraph | `explain` | [backend/app/graphs.py:350](../backend/app/graphs.py#L350) | function | used |  |  |  |  |
| F0600 | 04_ai_ml/langgraph | `needs_approval` | [backend/app/graphs.py:372](../backend/app/graphs.py#L372) | function | used |  |  |  |  |
| F0601 | 04_ai_ml/langgraph | `approval_gate` | [backend/app/graphs.py:376](../backend/app/graphs.py#L376) | function | used | Human-in-the-loop: the planner decides whether the advisory recommendation goes to the man |  |  |  |
| F0602 | 04_ai_ml/langgraph | `route_approval` | [backend/app/graphs.py:395](../backend/app/graphs.py#L395) | function | used |  |  |  |  |
| F0603 | 04_ai_ml/langgraph | `submit` | [backend/app/graphs.py:399](../backend/app/graphs.py#L399) | function | used |  |  |  |  |
| F0604 | 04_ai_ml/langgraph | `discard` | [backend/app/graphs.py:406](../backend/app/graphs.py#L406) | function | used |  |  |  |  |
| F0605 | 04_ai_ml/langgraph | `no_action` | [backend/app/graphs.py:410](../backend/app/graphs.py#L410) | function | used |  |  |  |  |
| F0606 | 04_ai_ml/langgraph | `rejected` | [backend/app/graphs.py:414](../backend/app/graphs.py#L414) | function | used |  |  |  |  |
| F0607 | 04_ai_ml/langgraph | `_message_dict` | [backend/app/runner.py:15](../backend/app/runner.py#L15) | function | used |  | F0608 |  |  |
| F0608 | 04_ai_ml/langgraph | `normalise` | [backend/app/runner.py:36](../backend/app/runner.py#L36) | function | used |  | F0613, F0618 |  |  |
| F0609 | 04_ai_ml/langgraph | `LocalRunner` | [backend/app/runner.py:45](../backend/app/runner.py#L45) | class | used |  | F0623, F0821, F0821 |  |  |
| F0610 | 04_ai_ml/langgraph | `LocalRunner.__init__` | [backend/app/runner.py:48](../backend/app/runner.py#L48) | method | used (framework) |  |  |  |  |
| F0611 | 04_ai_ml/langgraph | `LocalRunner._checkpointer` | [backend/app/runner.py:54](../backend/app/runner.py#L54) | method | used (framework) |  | F0610 |  |  |
| F0612 | 04_ai_ml/langgraph | `LocalRunner.graph` | [backend/app/runner.py:68](../backend/app/runner.py#L68) | method | used |  | F0614, F0615 |  |  |
| F0613 | 04_ai_ml/langgraph | `LocalRunner._result` | [backend/app/runner.py:86](../backend/app/runner.py#L86) | method | used |  | F0614, F0615 |  |  |
| F0614 | 04_ai_ml/langgraph | `LocalRunner.run` | [backend/app/runner.py:91](../backend/app/runner.py#L91) | method | used |  | F0626 |  |  |
| F0615 | 04_ai_ml/langgraph | `LocalRunner.resume` | [backend/app/runner.py:99](../backend/app/runner.py#L99) | method | used |  | F0627 |  |  |
| F0616 | 04_ai_ml/langgraph | `RemoteRunner` | [backend/app/runner.py:109](../backend/app/runner.py#L109) | class | used | LangGraph Server (the same server LangSmith Studio connects to). | F0623 |  |  |
| F0617 | 04_ai_ml/langgraph | `RemoteRunner.__init__` | [backend/app/runner.py:114](../backend/app/runner.py#L114) | method | used (framework) |  |  |  |  |
| F0618 | 04_ai_ml/langgraph | `RemoteRunner._result` | [backend/app/runner.py:120](../backend/app/runner.py#L120) | method | used |  | F0619, F0620 |  |  |
| F0619 | 04_ai_ml/langgraph | `RemoteRunner.run` | [backend/app/runner.py:127](../backend/app/runner.py#L127) | method | used |  | F0626 |  |  |
| F0620 | 04_ai_ml/langgraph | `RemoteRunner.resume` | [backend/app/runner.py:135](../backend/app/runner.py#L135) | method | used |  | F0627 |  |  |
| F0621 | 04_ai_ml/langgraph | `GraphRunner` | [backend/app/runner.py:142](../backend/app/runner.py#L142) | class | used |  | F0017, F0017 |  |  |
| F0622 | 04_ai_ml/langgraph | `GraphRunner.__init__` | [backend/app/runner.py:143](../backend/app/runner.py#L143) | method | used (framework) |  |  |  |  |
| F0623 | 04_ai_ml/langgraph | `GraphRunner.impl` | [backend/app/runner.py:147](../backend/app/runner.py#L147) | method | used |  | F0626, F0627 |  |  |
| F0624 | 04_ai_ml/langgraph | `GraphRunner.mode` | [backend/app/runner.py:153](../backend/app/runner.py#L153) | method | used |  | F0028, F0031 |  |  |
| F0625 | 04_ai_ml/langgraph | `GraphRunner._timed` | [backend/app/runner.py:157](../backend/app/runner.py#L157) | method | used |  | F0626, F0627 |  |  |
| F0626 | 04_ai_ml/langgraph | `GraphRunner.run` | [backend/app/runner.py:169](../backend/app/runner.py#L169) | method | used |  | F0083, F0085, F0087, F0092, F0823, F0824, F0825, F0826, F0827, F0829, F0830 |  |  |
| F0627 | 04_ai_ml/langgraph | `GraphRunner.resume` | [backend/app/runner.py:172](../backend/app/runner.py#L172) | method | used |  | F0086, F0088, F0825, F0826, F0829, F0830 |  |  |
| F0628 | 04_ai_ml/langgraph | `ask_sc_agent_manager` | [backend/scinsight/lg/chat.py:31](../backend/scinsight/lg/chat.py#L31) | function | used | The SC Agent Manager (supervisor). Use it for EVERY planning or analysis question: product |  |  |  |
| F0629 | 04_ai_ml/langgraph | `search_supply_chain_policy` | [backend/scinsight/lg/chat.py:43](../backend/scinsight/lg/chat.py#L43) | function | used | Search the governed policy, SOP, specification and supplier-agreement documents (PostgreSQ |  |  |  |
| F0630 | 04_ai_ml/langgraph | `ChatState` | [backend/scinsight/lg/chat.py:56](../backend/scinsight/lg/chat.py#L56) | class | used |  | F0632, F0633, F0634, F0635, F0636 |  |  |
| F0631 | 04_ai_ml/langgraph | `_this_turn` | [backend/scinsight/lg/chat.py:60](../backend/scinsight/lg/chat.py#L60) | function | used |  | F0634, F0635 |  |  |
| F0632 | 04_ai_ml/langgraph | `guardrail` | [backend/scinsight/lg/chat.py:65](../backend/scinsight/lg/chat.py#L65) | function | used |  | F0636 |  |  |
| F0633 | 04_ai_ml/langgraph | `blocked` | [backend/scinsight/lg/chat.py:69](../backend/scinsight/lg/chat.py#L69) | function | used |  | F0636 |  |  |
| F0634 | 04_ai_ml/langgraph | `assistant` | [backend/scinsight/lg/chat.py:73](../backend/scinsight/lg/chat.py#L73) | function | used |  | F0636 |  |  |
| F0635 | 04_ai_ml/langgraph | `evidence_gate` | [backend/scinsight/lg/chat.py:81](../backend/scinsight/lg/chat.py#L81) | function | used | Port of the Flowise post-processing: every number must exist in this turn's tool results,  | F0636 |  |  |
| F0636 | 04_ai_ml/langgraph | `build_chat` | [backend/scinsight/lg/chat.py:108](../backend/scinsight/lg/chat.py#L108) | function | used |  | F0812 |  |  |
| F0637 | 04_ai_ml/langgraph | `out_of_scope_reply` | [backend/scinsight/lg/common.py:30](../backend/scinsight/lg/common.py#L30) | function | used |  | F0711 |  |  |
| F0638 | 04_ai_ml/langgraph | `client` | [backend/scinsight/lg/common.py:39](../backend/scinsight/lg/common.py#L39) | function | used |  | F0639 |  |  |
| F0639 | 04_ai_ml/langgraph | `api` | [backend/scinsight/lg/common.py:46](../backend/scinsight/lg/common.py#L46) | function | used | Call the SCInsight API with the agent key (role agent_service: read, calculate, create rec | F0629, F0656, F0669, F0670, F0671, F0674, F0675, F0676, F0678, F0683, F0684, F06 |  |  |
| F0640 | 04_ai_ml/langgraph | `detail` | [backend/scinsight/lg/common.py:62](../backend/scinsight/lg/common.py#L62) | function | used |  | F0656, F0669, F0670, F0671, F0674, F0675, F0676, F0678, F0683, F0684, F0685 |  |  |
| F0641 | 04_ai_ml/langgraph | `strip` | [backend/scinsight/lg/common.py:67](../backend/scinsight/lg/common.py#L67) | function | used |  | F0629, F0667 |  |  |
| F0642 | 04_ai_ml/langgraph | `llm` | [backend/scinsight/lg/common.py:76](../backend/scinsight/lg/common.py#L76) | function | used | Qwen through the same OpenAI-compatible endpoint Flowise uses (temperature 0). | F0634, F0693, F0697, F0705 |  |  |
| F0643 | 04_ai_ml/langgraph | `prompt` | [backend/scinsight/lg/common.py:84](../backend/scinsight/lg/common.py#L84) | function | used |  | F0634, F0644, F0693, F0705 |  |  |
| F0644 | 04_ai_ml/langgraph | `explain_prompt` | [backend/scinsight/lg/common.py:89](../backend/scinsight/lg/common.py#L89) | function | used | (system, user template) of a specialist's explanation step, exactly as exported for Flowis | F0697 |  |  |
| F0645 | 04_ai_ml/langgraph | `fill` | [backend/scinsight/lg/common.py:96](../backend/scinsight/lg/common.py#L96) | function | used | Resolve the Flowise template variables used in the shared prompts ({{ question }}, {{ $flo | F0693, F0697 |  |  |
| F0646 | 04_ai_ml/langgraph | `text_of` | [backend/scinsight/lg/common.py:102](../backend/scinsight/lg/common.py#L102) | function | used |  | F0635, F0636, F0689, F0693, F0697, F0705, F0806, F0812 |  |  |
| F0647 | 04_ai_ml/langgraph | `_list` | [backend/scinsight/lg/common.py:110](../backend/scinsight/lg/common.py#L110) | function | used |  | F0653, F0654 |  |  |
| F0648 | 04_ai_ml/langgraph | `_kv` | [backend/scinsight/lg/common.py:114](../backend/scinsight/lg/common.py#L114) | function | used |  | F0654 |  |  |
| F0649 | 04_ai_ml/langgraph | `_fmt` | [backend/scinsight/lg/common.py:118](../backend/scinsight/lg/common.py#L118) | function | used |  | F0635, F0648, F0650, F0651, F0652, F0653, F0654, F0655, F0669, F0676, F0677, F06 |  |  |
| F0650 | 04_ai_ml/langgraph | `_excluded` | [backend/scinsight/lg/common.py:128](../backend/scinsight/lg/common.py#L128) | function | used |  | F0653, F0654 |  |  |
| F0651 | 04_ai_ml/langgraph | `_late` | [backend/scinsight/lg/common.py:132](../backend/scinsight/lg/common.py#L132) | function | used |  | F0654 |  |  |
| F0652 | 04_ai_ml/langgraph | `_near` | [backend/scinsight/lg/common.py:136](../backend/scinsight/lg/common.py#L136) | function | used |  | F0654 |  |  |
| F0653 | 04_ai_ml/langgraph | `_opt` | [backend/scinsight/lg/common.py:140](../backend/scinsight/lg/common.py#L140) | function | used |  | F0654 |  |  |
| F0654 | 04_ai_ml/langgraph | `summarize` | [backend/scinsight/lg/common.py:151](../backend/scinsight/lg/common.py#L151) | function | used |  | F0667 |  |  |
| F0655 | 04_ai_ml/langgraph | `_po_unconfirmed` | [backend/scinsight/lg/common.py:201](../backend/scinsight/lg/common.py#L201) | function | used |  | F0654 |  |  |
| F0656 | 04_ai_ml/langgraph | `context` | [backend/scinsight/lg/common.py:206](../backend/scinsight/lg/common.py#L206) | function | used |  | F0691, F0703 |  |  |
| F0657 | 04_ai_ml/langgraph | `_catalog` | [backend/scinsight/lg/common.py:222](../backend/scinsight/lg/common.py#L222) | function | used |  | F0659 |  |  |
| F0658 | 04_ai_ml/langgraph | `_name_hits` | [backend/scinsight/lg/common.py:230](../backend/scinsight/lg/common.py#L230) | function | used | How many meaningful words of a catalog name appear in the question (prefix match handles p | F0659 |  |  |
| F0659 | 04_ai_ml/langgraph | `detect_codes` | [backend/scinsight/lg/common.py:237](../backend/scinsight/lg/common.py#L237) | function | used | Deterministic identifier detection (codes first, then catalog names). Same rules as detect | F0694, F0814 |  |  |
| F0660 | 04_ai_ml/langgraph | `detect_codes.first` | [backend/scinsight/lg/common.py:244](../backend/scinsight/lg/common.py#L244) | nested | used |  | F0659 |  |  |
| F0661 | 04_ai_ml/langgraph | `merge_identifiers` | [backend/scinsight/lg/common.py:278](../backend/scinsight/lg/common.py#L278) | function | used | Code-detected identifiers win; the model only fills what code could not find. | F0694, F0814 |  |  |
| F0662 | 04_ai_ml/langgraph | `parse_extracted` | [backend/scinsight/lg/common.py:283](../backend/scinsight/lg/common.py#L283) | function | used | Lenient JSON parse of the identifier extraction (bare NONE / null tolerated, per-key fallb | F0693 |  |  |
| F0663 | 04_ai_ml/langgraph | `_val` | [backend/scinsight/lg/common.py:297](../backend/scinsight/lg/common.py#L297) | function | used |  | F0661, F0664, F0665, F0666 |  |  |
| F0664 | 04_ai_ml/langgraph | `_code` | [backend/scinsight/lg/common.py:303](../backend/scinsight/lg/common.py#L303) | function | used |  | F0669, F0670, F0671, F0674, F0675 |  |  |
| F0665 | 04_ai_ml/langgraph | `_num` | [backend/scinsight/lg/common.py:308](../backend/scinsight/lg/common.py#L308) | function | used |  | F0669, F0670, F0674 |  |  |
| F0666 | 04_ai_ml/langgraph | `_day` | [backend/scinsight/lg/common.py:316](../backend/scinsight/lg/common.py#L316) | function | used |  | F0669, F0670, F0674 |  |  |
| F0667 | 04_ai_ml/langgraph | `_done` | [backend/scinsight/lg/common.py:321](../backend/scinsight/lg/common.py#L321) | function | used |  | F0669, F0670, F0671, F0674, F0675 |  |  |
| F0668 | 04_ai_ml/langgraph | `_fail` | [backend/scinsight/lg/common.py:328](../backend/scinsight/lg/common.py#L328) | function | used |  | F0669, F0670, F0671, F0674, F0675 |  |  |
| F0669 | 04_ai_ml/langgraph | `calc_factory` | [backend/scinsight/lg/common.py:332](../backend/scinsight/lg/common.py#L332) | function | used |  |  |  |  |
| F0670 | 04_ai_ml/langgraph | `calc_procurement` | [backend/scinsight/lg/common.py:352](../backend/scinsight/lg/common.py#L352) | function | used |  |  |  |  |
| F0671 | 04_ai_ml/langgraph | `_balancing` | [backend/scinsight/lg/common.py:376](../backend/scinsight/lg/common.py#L376) | function | used |  | F0672, F0673 |  |  |
| F0672 | 04_ai_ml/langgraph | `calc_warehouse` | [backend/scinsight/lg/common.py:384](../backend/scinsight/lg/common.py#L384) | function | used |  |  |  |  |
| F0673 | 04_ai_ml/langgraph | `calc_logistics` | [backend/scinsight/lg/common.py:388](../backend/scinsight/lg/common.py#L388) | function | used |  |  |  |  |
| F0674 | 04_ai_ml/langgraph | `calc_inventory` | [backend/scinsight/lg/common.py:392](../backend/scinsight/lg/common.py#L392) | function | used |  |  |  |  |
| F0675 | 04_ai_ml/langgraph | `calc_quality` | [backend/scinsight/lg/common.py:409](../backend/scinsight/lg/common.py#L409) | function | used |  |  |  |  |
| F0676 | 04_ai_ml/langgraph | `calc_learning` | [backend/scinsight/lg/common.py:417](../backend/scinsight/lg/common.py#L417) | function | used |  |  |  |  |
| F0677 | 04_ai_ml/langgraph | `calc_learning.v` | [backend/scinsight/lg/common.py:452](../backend/scinsight/lg/common.py#L452) | nested | used |  | F0676 |  |  |
| F0678 | 04_ai_ml/langgraph | `policy` | [backend/scinsight/lg/common.py:474](../backend/scinsight/lg/common.py#L474) | function | used |  | F0696 |  |  |
| F0679 | 04_ai_ml/langgraph | `numbers` | [backend/scinsight/lg/common.py:489](../backend/scinsight/lg/common.py#L489) | function | used |  | F0680 |  |  |
| F0680 | 04_ai_ml/langgraph | `unsupported_numbers` | [backend/scinsight/lg/common.py:499](../backend/scinsight/lg/common.py#L499) | function | used |  | F0635, F0681 |  |  |
| F0681 | 04_ai_ml/langgraph | `gate` | [backend/scinsight/lg/common.py:504](../backend/scinsight/lg/common.py#L504) | function | used |  | F0698 |  |  |
| F0682 | 04_ai_ml/langgraph | `guard` | [backend/scinsight/lg/common.py:521](../backend/scinsight/lg/common.py#L521) | function | used |  | F0637, F0706 |  |  |
| F0683 | 04_ai_ml/langgraph | `save` | [backend/scinsight/lg/common.py:534](../backend/scinsight/lg/common.py#L534) | function | used |  | F0713 |  |  |
| F0684 | 04_ai_ml/langgraph | `verify` | [backend/scinsight/lg/common.py:552](../backend/scinsight/lg/common.py#L552) | function | used |  | F0720 |  |  |
| F0685 | 04_ai_ml/langgraph | `withdraw` | [backend/scinsight/lg/common.py:567](../backend/scinsight/lg/common.py#L567) | function | used |  | F0721 |  |  |
| F0686 | 04_ai_ml/langgraph | `Input` | [backend/scinsight/lg/specialists.py:38](../backend/scinsight/lg/specialists.py#L38) | class | used |  | F0690 |  |  |
| F0687 | 04_ai_ml/langgraph | `Output` | [backend/scinsight/lg/specialists.py:42](../backend/scinsight/lg/specialists.py#L42) | class | used |  | F0690 |  |  |
| F0688 | 04_ai_ml/langgraph | `SpecialistState` | [backend/scinsight/lg/specialists.py:48](../backend/scinsight/lg/specialists.py#L48) | class | used |  | F0690, F0691, F0692, F0693, F0694, F0695, F0696, F0697, F0698 |  |  |
| F0689 | 04_ai_ml/langgraph | `last_question` | [backend/scinsight/lg/specialists.py:66](../backend/scinsight/lg/specialists.py#L66) | function | used |  | F0691, F0703 |  |  |
| F0690 | 04_ai_ml/langgraph | `build_specialist` | [backend/scinsight/lg/specialists.py:70](../backend/scinsight/lg/specialists.py#L70) | function | used |  |  |  |  |
| F0691 | 04_ai_ml/langgraph | `build_specialist.check_access` | [backend/scinsight/lg/specialists.py:73](../backend/scinsight/lg/specialists.py#L73) | nested | used |  | F0690 |  |  |
| F0692 | 04_ai_ml/langgraph | `build_specialist.stop_access` | [backend/scinsight/lg/specialists.py:77](../backend/scinsight/lg/specialists.py#L77) | nested | used |  | F0690 |  |  |
| F0693 | 04_ai_ml/langgraph | `build_specialist.read_request` | [backend/scinsight/lg/specialists.py:80](../backend/scinsight/lg/specialists.py#L80) | nested | used |  | F0690 |  |  |
| F0694 | 04_ai_ml/langgraph | `build_specialist.calculate` | [backend/scinsight/lg/specialists.py:85](../backend/scinsight/lg/specialists.py#L85) | nested | used |  | F0690 |  |  |
| F0695 | 04_ai_ml/langgraph | `build_specialist.stop_input` | [backend/scinsight/lg/specialists.py:89](../backend/scinsight/lg/specialists.py#L89) | nested | used |  | F0690 |  |  |
| F0696 | 04_ai_ml/langgraph | `build_specialist.policy_search` | [backend/scinsight/lg/specialists.py:92](../backend/scinsight/lg/specialists.py#L92) | nested | used |  | F0690 |  |  |
| F0697 | 04_ai_ml/langgraph | `build_specialist.write_answer` | [backend/scinsight/lg/specialists.py:95](../backend/scinsight/lg/specialists.py#L95) | nested | used |  | F0690 |  |  |
| F0698 | 04_ai_ml/langgraph | `build_specialist.check_numbers` | [backend/scinsight/lg/specialists.py:101](../backend/scinsight/lg/specialists.py#L101) | nested | used |  | F0690 |  |  |
| F0699 | 04_ai_ml/langgraph | `Input` | [backend/scinsight/lg/supervisor.py:27](../backend/scinsight/lg/supervisor.py#L27) | class | used |  | F0722 |  |  |
| F0700 | 04_ai_ml/langgraph | `Output` | [backend/scinsight/lg/supervisor.py:32](../backend/scinsight/lg/supervisor.py#L32) | class | used |  | F0722 |  |  |
| F0701 | 04_ai_ml/langgraph | `SupervisorState` | [backend/scinsight/lg/supervisor.py:39](../backend/scinsight/lg/supervisor.py#L39) | class | used |  | F0703, F0704, F0705, F0706, F0707, F0709, F0710, F0711, F0712, F0713, F0714, F07 |  |  |
| F0702 | 04_ai_ml/langgraph | `_reply` | [backend/scinsight/lg/supervisor.py:56](../backend/scinsight/lg/supervisor.py#L56) | function | used |  | F0704, F0710, F0711, F0712, F0715, F0717, F0718, F0720, F0721 |  |  |
| F0703 | 04_ai_ml/langgraph | `check_access` | [backend/scinsight/lg/supervisor.py:60](../backend/scinsight/lg/supervisor.py#L60) | function | used |  | F0722 |  |  |
| F0704 | 04_ai_ml/langgraph | `stop_access` | [backend/scinsight/lg/supervisor.py:68](../backend/scinsight/lg/supervisor.py#L68) | function | used |  | F0722 |  |  |
| F0705 | 04_ai_ml/langgraph | `understand` | [backend/scinsight/lg/supervisor.py:72](../backend/scinsight/lg/supervisor.py#L72) | function | used |  | F0722 |  |  |
| F0706 | 04_ai_ml/langgraph | `safety_guard` | [backend/scinsight/lg/supervisor.py:77](../backend/scinsight/lg/supervisor.py#L77) | function | used |  | F0722 |  |  |
| F0707 | 04_ai_ml/langgraph | `route` | [backend/scinsight/lg/supervisor.py:82](../backend/scinsight/lg/supervisor.py#L82) | function | used |  | F0722 |  |  |
| F0708 | 04_ai_ml/langgraph | `specialist_node` | [backend/scinsight/lg/supervisor.py:89](../backend/scinsight/lg/supervisor.py#L89) | function | used |  | F0722 |  |  |
| F0709 | 04_ai_ml/langgraph | `specialist_node.run` | [backend/scinsight/lg/supervisor.py:90](../backend/scinsight/lg/supervisor.py#L90) | nested | used |  | F0708 |  |  |
| F0710 | 04_ai_ml/langgraph | `refuse_sap_change` | [backend/scinsight/lg/supervisor.py:97](../backend/scinsight/lg/supervisor.py#L97) | function | used |  | F0722 |  |  |
| F0711 | 04_ai_ml/langgraph | `out_of_scope` | [backend/scinsight/lg/supervisor.py:101](../backend/scinsight/lg/supervisor.py#L101) | function | used |  | F0722 |  |  |
| F0712 | 04_ai_ml/langgraph | `learning_report` | [backend/scinsight/lg/supervisor.py:105](../backend/scinsight/lg/supervisor.py#L105) | function | used |  | F0722 |  |  |
| F0713 | 04_ai_ml/langgraph | `save_recommendation` | [backend/scinsight/lg/supervisor.py:109](../backend/scinsight/lg/supervisor.py#L109) | function | used |  | F0722 |  |  |
| F0714 | 04_ai_ml/langgraph | `after_save` | [backend/scinsight/lg/supervisor.py:113](../backend/scinsight/lg/supervisor.py#L113) | function | used |  | F0722 |  |  |
| F0715 | 04_ai_ml/langgraph | `analysis_only` | [backend/scinsight/lg/supervisor.py:119](../backend/scinsight/lg/supervisor.py#L119) | function | used |  | F0722 |  |  |
| F0716 | 04_ai_ml/langgraph | `_approval_text` | [backend/scinsight/lg/supervisor.py:123](../backend/scinsight/lg/supervisor.py#L123) | function | used |  | F0717, F0718 |  |  |
| F0717 | 04_ai_ml/langgraph | `handoff` | [backend/scinsight/lg/supervisor.py:128](../backend/scinsight/lg/supervisor.py#L128) | function | used |  | F0722 |  |  |
| F0718 | 04_ai_ml/langgraph | `prepare_approval` | [backend/scinsight/lg/supervisor.py:132](../backend/scinsight/lg/supervisor.py#L132) | function | used |  | F0722 |  |  |
| F0719 | 04_ai_ml/langgraph | `human_approval` | [backend/scinsight/lg/supervisor.py:136](../backend/scinsight/lg/supervisor.py#L136) | function | used |  | F0722 |  |  |
| F0720 | 04_ai_ml/langgraph | `show_decision` | [backend/scinsight/lg/supervisor.py:143](../backend/scinsight/lg/supervisor.py#L143) | function | used |  | F0722 |  |  |
| F0721 | 04_ai_ml/langgraph | `withdraw` | [backend/scinsight/lg/supervisor.py:147](../backend/scinsight/lg/supervisor.py#L147) | function | used |  | F0722 |  |  |
| F0722 | 04_ai_ml/langgraph | `build_supervisor` | [backend/scinsight/lg/supervisor.py:151](../backend/scinsight/lg/supervisor.py#L151) | function | used |  | F0810, F0811 |  |  |
| F0723 | 04_ai_ml/langgraph | `_dump` | [scripts/langgraph_assistants.py:45](../scripts/langgraph_assistants.py#L45) | function | used |  | F0724 |  |  |
| F0724 | 04_ai_ml/langgraph | `write_files` | [scripts/langgraph_assistants.py:54](../scripts/langgraph_assistants.py#L54) | function | used |  | F0727 |  |  |
| F0725 | 04_ai_ml/langgraph | `_call` | [scripts/langgraph_assistants.py:79](../scripts/langgraph_assistants.py#L79) | function | used |  | F0726 |  |  |
| F0726 | 04_ai_ml/langgraph | `create_assistants` | [scripts/langgraph_assistants.py:86](../scripts/langgraph_assistants.py#L86) | function | used |  | F0727 |  |  |
| F0727 | 04_ai_ml/langgraph | `main` | [scripts/langgraph_assistants.py:104](../scripts/langgraph_assistants.py#L104) | function | used |  |  |  |  |
| F0728 | 04_ai_ml/llm | `chat_model` | [backend/app/llm.py:18](../backend/app/llm.py#L18) | function | used |  | F0544, F0551, F0565, F0580, F0589, F0599 |  |  |
| F0729 | 04_ai_ml/llm | `llm_health` | [backend/app/llm.py:30](../backend/app/llm.py#L30) | function | used |  | F0031 |  |  |
| F0730 | 04_ai_ml/llm | `deterministic_summary` | [backend/app/llm.py:45](../backend/app/llm.py#L45) | function | used | Template answer used when the LLM is disabled or unreachable; it only restates engine outp | F0551, F0583, F0599 |  |  |
| F0731 | 04_ai_ml/rag | `HashEmbedder` | [backend/app/rag.py:21](../backend/app/rag.py#L21) | class | used |  | F0737, F0744, F0949, F0954 |  |  |
| F0732 | 04_ai_ml/rag | `HashEmbedder.embed` | [backend/app/rag.py:24](../backend/app/rag.py#L24) | method | used |  | F0745, F0746, F0752, F0755 |  |  |
| F0733 | 04_ai_ml/rag | `HashEmbedder._one` | [backend/app/rag.py:27](../backend/app/rag.py#L27) | method | used |  | F0732 |  |  |
| F0734 | 04_ai_ml/rag | `FastEmbedder` | [backend/app/rag.py:38](../backend/app/rag.py#L38) | class | used |  | F0737, F0950 |  |  |
| F0735 | 04_ai_ml/rag | `FastEmbedder.__init__` | [backend/app/rag.py:39](../backend/app/rag.py#L39) | method | used (framework) |  |  |  |  |
| F0736 | 04_ai_ml/rag | `FastEmbedder.embed` | [backend/app/rag.py:46](../backend/app/rag.py#L46) | method | used |  | F0745, F0746, F0752, F0755 |  |  |
| F0737 | 04_ai_ml/rag | `get_embedder` | [backend/app/rag.py:54](../backend/app/rag.py#L54) | function | used |  | F0756, F1868 |  |  |
| F0738 | 04_ai_ml/rag | `cosine` | [backend/app/rag.py:61](../backend/app/rag.py#L61) | function | used |  | F0746 |  |  |
| F0739 | 04_ai_ml/rag | `chunk_markdown` | [backend/app/rag.py:65](../backend/app/rag.py#L65) | function | used | Split on second-level headings; each chunk carries the document title and section for cont | F0745, F0752, F0947 |  |  |
| F0740 | 04_ai_ml/rag | `chunk_markdown.flush` | [backend/app/rag.py:75](../backend/app/rag.py#L75) | nested | used |  | F0739 |  |  |
| F0741 | 04_ai_ml/rag | `keyword_boost` | [backend/app/rag.py:90](../backend/app/rag.py#L90) | function | used |  | F0746, F0755, F0948 |  |  |
| F0742 | 04_ai_ml/rag | `Chunk` | [backend/app/rag.py:97](../backend/app/rag.py#L97) | class | used |  | F0744, F0745 |  |  |
| F0743 | 04_ai_ml/rag | `MemoryRag` | [backend/app/rag.py:107](../backend/app/rag.py#L107) | class | used |  | F0483, F0756, F0949, F0950 |  |  |
| F0744 | 04_ai_ml/rag | `MemoryRag.__init__` | [backend/app/rag.py:110](../backend/app/rag.py#L110) | method | used (framework) |  |  |  |  |
| F0745 | 04_ai_ml/rag | `MemoryRag.add` | [backend/app/rag.py:114](../backend/app/rag.py#L114) | method | used |  | F0081, F0748 |  |  |
| F0746 | 04_ai_ml/rag | `MemoryRag.search` | [backend/app/rag.py:120](../backend/app/rag.py#L120) | method | used |  | F0464, F0076, F0077, F0949, F0950, F0954 |  |  |
| F0747 | 04_ai_ml/rag | `MemoryRag.stats` | [backend/app/rag.py:130](../backend/app/rag.py#L130) | method | used |  | F0026, F0031, F0080, F0949, F0954 |  |  |
| F0748 | 04_ai_ml/rag | `MemoryRag.load_directory` | [backend/app/rag.py:133](../backend/app/rag.py#L133) | method | used |  | F0483, F0756, F0949, F0950, F0954 |  |  |
| F0749 | 04_ai_ml/rag | `PgVectorRag` | [backend/app/rag.py:139](../backend/app/rag.py#L139) | class | used |  | F0756, F0954 |  |  |
| F0750 | 04_ai_ml/rag | `PgVectorRag.__init__` | [backend/app/rag.py:142](../backend/app/rag.py#L142) | method | used (framework) |  |  |  |  |
| F0751 | 04_ai_ml/rag | `PgVectorRag._connect` | [backend/app/rag.py:159](../backend/app/rag.py#L159) | method | used |  | F0752, F0753, F0754, F0755 |  |  |
| F0752 | 04_ai_ml/rag | `PgVectorRag.add` | [backend/app/rag.py:167](../backend/app/rag.py#L167) | method | used |  | F0081, F0754 |  |  |
| F0753 | 04_ai_ml/rag | `PgVectorRag.stats` | [backend/app/rag.py:181](../backend/app/rag.py#L181) | method | used |  | F0026, F0031, F0080, F0949, F0954 |  |  |
| F0754 | 04_ai_ml/rag | `PgVectorRag.load_directory` | [backend/app/rag.py:187](../backend/app/rag.py#L187) | method | used | Index the approved corpus once; re-index everything if the embedding model changed. | F0483, F0756, F0949, F0950, F0954 |  |  |
| F0755 | 04_ai_ml/rag | `PgVectorRag.search` | [backend/app/rag.py:204](../backend/app/rag.py#L204) | method | used |  | F0464, F0076, F0077, F0949, F0950, F0954 |  |  |
| F0756 | 04_ai_ml/rag | `create_rag` | [backend/app/rag.py:224](../backend/app/rag.py#L224) | function | used |  | F0483, F0017 |  |  |
| F0757 | 04_ai_ml/rag | `DocumentError` | [backend/scinsight/rag.py:37](../backend/scinsight/rag.py#L37) | class | used |  | F0758, F0765, F1808, F1860, F1863, F1891 |  |  |
| F0758 | 04_ai_ml/rag | `parse_document` | [backend/scinsight/rag.py:41](../backend/scinsight/rag.py#L41) | function | used |  | F0765, F1808, F1860, F1863, F1891 |  |  |
| F0759 | 04_ai_ml/rag | `chunk_document` | [backend/scinsight/rag.py:64](../backend/scinsight/rag.py#L64) | function | unused? | Split on '## ' sections, then into <= size windows with overlap; each chunk carries its se |  |  |  |
| F0760 | 04_ai_ml/rag | `HashEmbedder` | [backend/scinsight/rag.py:71](../backend/scinsight/rag.py#L71) | class | used |  | F0762, F1868 |  |  |
| F0761 | 04_ai_ml/rag | `HashEmbedder.embed` | [backend/scinsight/rag.py:75](../backend/scinsight/rag.py#L75) | method | used |  | F0745, F0746, F0752, F0755 |  |  |
| F0762 | 04_ai_ml/rag | `make_embedder` | [backend/scinsight/rag.py:87](../backend/scinsight/rag.py#L87) | function | used |  | F1993 |  |  |
| F0763 | 04_ai_ml/rag | `KnowledgeBase` | [backend/scinsight/rag.py:99](../backend/scinsight/rag.py#L99) | class | used |  | F1993, F1945 |  |  |
| F0764 | 04_ai_ml/rag | `KnowledgeBase.__init__` | [backend/scinsight/rag.py:100](../backend/scinsight/rag.py#L100) | method | used (framework) |  |  |  |  |
| F0765 | 04_ai_ml/rag | `KnowledgeBase.ingest_dir` | [backend/scinsight/rag.py:138](../backend/scinsight/rag.py#L138) | method | used | Validate and (re)index changed documents into each tenant's ACTIVE index (baseline when no | F1993 |  |  |
| F0766 | 04_ai_ml/rag | `KnowledgeBase.search` | [backend/scinsight/rag.py:183](../backend/scinsight/rag.py#L183) | method | used | Tenant-, role- and date-filtered retrieval with citations, using the active configuration  | F2014, F1836, F1874 |  |  |
| F0767 | 05_security_governance/authentication | `Principal` | [backend/app/auth.py:11](../backend/app/auth.py#L11) | class | used |  | F0770, F0770, F0771, F2114, F2115, F2116, F2117, F2118, F2119, F2120, F2121, F21 |  |  |
| F0768 | 05_security_governance/authentication | `ApiKeyAuth` | [backend/app/auth.py:17](../backend/app/auth.py#L17) | class | used |  | F0017 |  |  |
| F0769 | 05_security_governance/authentication | `ApiKeyAuth.__init__` | [backend/app/auth.py:18](../backend/app/auth.py#L18) | method | used (framework) |  |  |  |  |
| F0770 | 05_security_governance/authentication | `ApiKeyAuth.authenticate` | [backend/app/auth.py:21](../backend/app/auth.py#L21) | method | used |  | F0019 |  |  |
| F0771 | 05_security_governance/authentication | `ApiKeyAuth.require` | [backend/app/auth.py:28](../backend/app/auth.py#L28) | method | used |  | F0020, F0021 |  |  |
| F0772 | 05_security_governance/authorization | `Principal` | [backend/scinsight/security.py:32](../backend/scinsight/security.py#L32) | class | used |  | F1994, F1995, F1996, F1998, F1999, F2000, F2001, F2002, F2003, F2004, F2005, F20 |  |  |
| F0773 | 05_security_governance/authorization | `Principal.is_human` | [backend/scinsight/security.py:39](../backend/scinsight/security.py#L39) | method | used (framework) |  |  |  |  |
| F0774 | 05_security_governance/authorization | `Security` | [backend/scinsight/security.py:44](../backend/scinsight/security.py#L44) | class | used |  | F1993, F0312 |  |  |
| F0775 | 05_security_governance/authorization | `Security.__init__` | [backend/scinsight/security.py:45](../backend/scinsight/security.py#L45) | method | used (framework) |  |  |  |  |
| F0776 | 05_security_governance/authorization | `Security.authenticate` | [backend/scinsight/security.py:48](../backend/scinsight/security.py#L48) | method | used |  | F1994 |  |  |
| F0777 | 05_security_governance/authorization | `Security.require` | [backend/scinsight/security.py:62](../backend/scinsight/security.py#L62) | method | used |  | F1995, F2016, F2024, F2025, F2027, F1820, F1844, F1845, F0340, F0341 |  |  |
| F0778 | 05_security_governance/authorization | `Security.require_reviewer` | [backend/scinsight/security.py:67](../backend/scinsight/security.py#L67) | method | used |  | F0337 |  |  |
| F0779 | 05_security_governance/authorization | `Security.audit` | [backend/scinsight/security.py:74](../backend/scinsight/security.py#L74) | method | used |  | F1999, F2006, F2024, F2025, F2026, F1821, F0776, F0778, F0314, F0333, F0337, F03 |  |  |
| F0780 | 05_security_governance/authorization | `Security.audit.write` | [backend/scinsight/security.py:77](../backend/scinsight/security.py#L77) | nested | used |  | F0779 |  |  |
| F0781 | 05_security_governance/authorization | `Security.verify_chain` | [backend/scinsight/security.py:85](../backend/scinsight/security.py#L85) | method | used |  | F2027 |  |  |
| F0782 | 05_security_governance/secrets_setup | `token` | [scripts/gen-env.py:21](../scripts/gen-env.py#L21) | function | used |  | F0784 |  |  |
| F0783 | 05_security_governance/secrets_setup | `password` | [scripts/gen-env.py:25](../scripts/gen-env.py#L25) | function | used |  | F0784 |  |  |
| F0784 | 05_security_governance/secrets_setup | `secret_map` | [scripts/gen-env.py:32](../scripts/gen-env.py#L32) | function | used |  | F0785 |  |  |
| F0785 | 05_security_governance/secrets_setup | `main` | [scripts/gen-env.py:91](../scripts/gen-env.py#L91) | function | used |  |  |  |  |
| F0786 | 06_testing/agent_tests | `_target` | [tests/scinsight/test_flowise_e2e.py:26](../tests/scinsight/test_flowise_e2e.py#L26) | function | used |  |  |  |  |
| F0787 | 06_testing/agent_tests | `_http` | [tests/scinsight/test_flowise_e2e.py:42](../tests/scinsight/test_flowise_e2e.py#L42) | function | used |  | F0788, F0789 |  |  |
| F0788 | 06_testing/agent_tests | `predict` | [tests/scinsight/test_flowise_e2e.py:56](../tests/scinsight/test_flowise_e2e.py#L56) | function | used |  | F0791, F0793, F0794, F0802 |  |  |
| F0789 | 06_testing/agent_tests | `sci` | [tests/scinsight/test_flowise_e2e.py:61](../tests/scinsight/test_flowise_e2e.py#L61) | function | used |  | F0790, F0797, F0798, F0799, F0800, F0801 |  |  |
| F0790 | 06_testing/agent_tests | `calculation_of` | [tests/scinsight/test_flowise_e2e.py:65](../tests/scinsight/test_flowise_e2e.py#L65) | function | used |  | F0797, F0798, F0799, F0800 |  |  |
| F0791 | 06_testing/agent_tests | `ask_supervisor` | [tests/scinsight/test_flowise_e2e.py:73](../tests/scinsight/test_flowise_e2e.py#L73) | function | used |  | F0795, F0796, F0797, F0798, F0799, F0800, F0801 |  |  |
| F0792 | 06_testing/agent_tests | `paused_recommendation` | [tests/scinsight/test_flowise_e2e.py:79](../tests/scinsight/test_flowise_e2e.py#L79) | function | used |  | F0797, F0798, F0799, F0800 |  |  |
| F0793 | 06_testing/agent_tests | `resume` | [tests/scinsight/test_flowise_e2e.py:87](../tests/scinsight/test_flowise_e2e.py#L87) | function | used |  | F0797, F0798, F0799 |  |  |
| F0794 | 06_testing/agent_tests | `test_prediction_without_api_key_is_refused` | [tests/scinsight/test_flowise_e2e.py:94](../tests/scinsight/test_flowise_e2e.py#L94) | test | test |  |  |  |  |
| F0795 | 06_testing/agent_tests | `test_sap_write_request_is_refused_without_calling_a_specialist` | [tests/scinsight/test_flowise_e2e.py:99](../tests/scinsight/test_flowise_e2e.py#L99) | test | test |  |  |  |  |
| F0796 | 06_testing/agent_tests | `test_instruction_override_is_blocked` | [tests/scinsight/test_flowise_e2e.py:105](../tests/scinsight/test_flowise_e2e.py#L105) | test | test |  |  |  |  |
| F0797 | 06_testing/agent_tests | `test_scenario_1_factory_shortage_pauses_and_proceed_is_not_an_approval` | [tests/scinsight/test_flowise_e2e.py:111](../tests/scinsight/test_flowise_e2e.py#L111) | test | test |  |  |  |  |
| F0798 | 06_testing/agent_tests | `test_scenario_2_transfer_is_approved_only_by_the_warehouse_manager` | [tests/scinsight/test_flowise_e2e.py:123](../tests/scinsight/test_flowise_e2e.py#L123) | test | test |  |  |  |  |
| F0799 | 06_testing/agent_tests | `test_scenario_3_quality_exclusions_and_reject_withdraws` | [tests/scinsight/test_flowise_e2e.py:137](../tests/scinsight/test_flowise_e2e.py#L137) | test | test |  |  |  |  |
| F0800 | 06_testing/agent_tests | `test_procurement_recommends_an_approved_supplier_with_demonstrated_lead_time` | [tests/scinsight/test_flowise_e2e.py:147](../tests/scinsight/test_flowise_e2e.py#L147) | test | test |  |  |  |  |
| F0801 | 06_testing/agent_tests | `test_learning_reports_the_verified_plus_four_day_error` | [tests/scinsight/test_flowise_e2e.py:157](../tests/scinsight/test_flowise_e2e.py#L157) | test | test |  |  |  |  |
| F0802 | 06_testing/agent_tests | `test_chatflow_answers_with_allowlisted_tools_and_the_evidence_footer` | [tests/scinsight/test_flowise_e2e.py:166](../tests/scinsight/test_flowise_e2e.py#L166) | test | test |  |  |  |  |
| F0803 | 06_testing/agent_tests | `ScriptedModel` | [tests/scinsight/test_langgraph_mirror.py:31](../tests/scinsight/test_langgraph_mirror.py#L31) | class | used | Stands in for Qwen: answers each prompt type deterministically (classification, extraction | F0807, F0812 |  |  |
| F0804 | 06_testing/agent_tests | `ScriptedModel.__init__` | [tests/scinsight/test_langgraph_mirror.py:34](../tests/scinsight/test_langgraph_mirror.py#L34) | method | used |  |  |  |  |
| F0805 | 06_testing/agent_tests | `ScriptedModel.bind_tools` | [tests/scinsight/test_langgraph_mirror.py:38](../tests/scinsight/test_langgraph_mirror.py#L38) | method | used |  | F0580, F0634 |  |  |
| F0806 | 06_testing/agent_tests | `ScriptedModel.invoke` | [tests/scinsight/test_langgraph_mirror.py:42](../tests/scinsight/test_langgraph_mirror.py#L42) | method | used |  |  |  |  |
| F0807 | 06_testing/agent_tests | `lg` | [tests/scinsight/test_langgraph_mirror.py:57](../tests/scinsight/test_langgraph_mirror.py#L57) | function | used |  | F0809, F0810, F0811 |  |  |
| F0808 | 06_testing/agent_tests | `calc_of` | [tests/scinsight/test_langgraph_mirror.py:65](../tests/scinsight/test_langgraph_mirror.py#L65) | function | used |  | F0809, F0810 |  |  |
| F0809 | 06_testing/agent_tests | `test_specialist_subgraph_mirrors_the_flowise_specialist` | [tests/scinsight/test_langgraph_mirror.py:71](../tests/scinsight/test_langgraph_mirror.py#L71) | test | test |  |  |  |  |
| F0810 | 06_testing/agent_tests | `test_supervisor_interrupt_is_not_the_approval_and_resume_reads_the_api` | [tests/scinsight/test_langgraph_mirror.py:82](../tests/scinsight/test_langgraph_mirror.py#L82) | test | test |  |  |  |  |
| F0811 | 06_testing/agent_tests | `test_supervisor_reject_withdraws_and_guards_refuse` | [tests/scinsight/test_langgraph_mirror.py:105](../tests/scinsight/test_langgraph_mirror.py#L105) | test | test |  |  |  |  |
| F0812 | 06_testing/agent_tests | `test_chat_front_door_calls_the_manager_and_checks_numbers` | [tests/scinsight/test_langgraph_mirror.py:123](../tests/scinsight/test_langgraph_mirror.py#L123) | test | test |  |  |  |  |
| F0813 | 06_testing/agent_tests | `test_role_questions_cover_every_role_with_valid_routes` | [tests/scinsight/test_langgraph_mirror.py:141](../tests/scinsight/test_langgraph_mirror.py#L141) | test | test |  |  |  |  |
| F0814 | 06_testing/agent_tests | `test_identifiers_are_detected_by_code_before_the_model` | [tests/scinsight/test_langgraph_mirror.py:148](../tests/scinsight/test_langgraph_mirror.py#L148) | test | test |  |  |  |  |
| F0815 | 06_testing/agent_tests | `load` | [tests/test_flowise_flows.py:13](../tests/test_flowise_flows.py#L13) | function | used |  | F0816, F0818, F0819, F0820 |  |  |
| F0816 | 06_testing/agent_tests | `test_edges_reference_real_nodes_and_handles` | [tests/test_flowise_flows.py:20](../tests/test_flowise_flows.py#L20) | test | test |  |  |  |  |
| F0817 | 06_testing/agent_tests | `test_edges_reference_real_nodes_and_handles.handles` | [tests/test_flowise_flows.py:25](../tests/test_flowise_flows.py#L25) | nested | used |  | F0816 |  |  |
| F0818 | 06_testing/agent_tests | `test_chatflow_is_tool_agent_with_mcp_sap_odata_and_memory` | [tests/test_flowise_flows.py:36](../tests/test_flowise_flows.py#L36) | test | test |  |  |  |  |
| F0819 | 06_testing/agent_tests | `test_agentflow_full_workflow_sap_rag_nine_roles_and_human_input` | [tests/test_flowise_flows.py:53](../tests/test_flowise_flows.py#L53) | test | test |  |  |  |  |
| F0820 | 06_testing/agent_tests | `test_no_secrets_in_flow_json` | [tests/test_flowise_flows.py:83](../tests/test_flowise_flows.py#L83) | test | test |  |  |  |  |
| F0821 | 06_testing/agent_tests | `runner` | [tests/test_graphs_and_agents.py:10](../tests/test_graphs_and_agents.py#L10) | function | used |  | F0823, F0824, F0825, F0826, F0827, F0829, F0830 |  |  |
| F0822 | 06_testing/agent_tests | `test_graphs_have_expected_topology` | [tests/test_graphs_and_agents.py:15](../tests/test_graphs_and_agents.py#L15) | test | test |  |  |  |  |
| F0823 | 06_testing/agent_tests | `test_chat_graph_guard_refuses_sap_writes` | [tests/test_graphs_and_agents.py:22](../tests/test_graphs_and_agents.py#L22) | test | test |  |  |  |  |
| F0824 | 06_testing/agent_tests | `test_chat_graph_deterministic_fallback_keeps_thread_memory` | [tests/test_graphs_and_agents.py:27](../tests/test_graphs_and_agents.py#L27) | test | test |  |  |  |  |
| F0825 | 06_testing/agent_tests | `test_business_graph_interrupts_then_submits` | [tests/test_graphs_and_agents.py:35](../tests/test_graphs_and_agents.py#L35) | test | test |  |  |  |  |
| F0826 | 06_testing/agent_tests | `test_business_graph_discard_and_free_text_intake` | [tests/test_graphs_and_agents.py:50](../tests/test_graphs_and_agents.py#L50) | test | test |  |  |  |  |
| F0827 | 06_testing/agent_tests | `test_business_graph_rejects_invalid_and_completes_no_action` | [tests/test_graphs_and_agents.py:58](../tests/test_graphs_and_agents.py#L58) | test | test |  |  |  |  |
| F0828 | 06_testing/agent_tests | `test_langgraph_agentflow_topology` | [tests/test_graphs_and_agents.py:65](../tests/test_graphs_and_agents.py#L65) | test | test |  |  |  |  |
| F0829 | 06_testing/agent_tests | `test_langgraph_agentflow_routes_interrupts_and_submits` | [tests/test_graphs_and_agents.py:74](../tests/test_graphs_and_agents.py#L74) | test | test |  |  |  |  |
| F0830 | 06_testing/agent_tests | `test_langgraph_agentflow_boundary_and_discard` | [tests/test_graphs_and_agents.py:92](../tests/test_graphs_and_agents.py#L92) | test | test |  |  |  |  |
| F0831 | 06_testing/agent_tests | `test_deep_agent_is_built_with_subagents_and_planning_tools` | [tests/test_graphs_and_agents.py:101](../tests/test_graphs_and_agents.py#L101) | test | test |  |  |  |  |
| F0832 | 06_testing/agent_tests | `test_deep_agent_harness_controls_tools_subagents_steps_and_prompt` | [tests/test_graphs_and_agents.py:110](../tests/test_graphs_and_agents.py#L110) | test | test |  |  |  |  |
| F0833 | 06_testing/agent_tests | `test_harness_guard_enforces_loop_controls_per_run` | [tests/test_graphs_and_agents.py:130](../tests/test_graphs_and_agents.py#L130) | test | test |  |  |  |  |
| F0834 | 06_testing/api_tests | `test_scenario_1_factory_material_shortage` | [tests/scinsight/test_api_scenarios.py:7](../tests/scinsight/test_api_scenarios.py#L7) | test | test |  |  |  |  |
| F0835 | 06_testing/api_tests | `test_production_order_quantity_cannot_be_overridden` | [tests/scinsight/test_api_scenarios.py:28](../tests/scinsight/test_api_scenarios.py#L28) | test | test |  |  |  |  |
| F0836 | 06_testing/api_tests | `test_scenario_2_three_warehouse_balancing` | [tests/scinsight/test_api_scenarios.py:34](../tests/scinsight/test_api_scenarios.py#L34) | test | test |  |  |  |  |
| F0837 | 06_testing/api_tests | `test_scenario_3_expiry_and_quality_protection` | [tests/scinsight/test_api_scenarios.py:48](../tests/scinsight/test_api_scenarios.py#L48) | test | test |  |  |  |  |
| F0838 | 06_testing/api_tests | `test_decision_lifecycle_requires_an_authorised_human` | [tests/scinsight/test_api_scenarios.py:58](../tests/scinsight/test_api_scenarios.py#L58) | test | test |  |  |  |  |
| F0839 | 06_testing/api_tests | `test_defer_then_review_and_withdraw` | [tests/scinsight/test_api_scenarios.py:82](../tests/scinsight/test_api_scenarios.py#L82) | test | test |  |  |  |  |
| F0840 | 06_testing/api_tests | `test_outcome_learning_loop_and_model_governance` | [tests/scinsight/test_api_scenarios.py:95](../tests/scinsight/test_api_scenarios.py#L95) | test | test |  |  |  |  |
| F0841 | 06_testing/api_tests | `test_purchase_request_carries_a_reconcilable_lead_time_prediction` | [tests/scinsight/test_api_scenarios.py:114](../tests/scinsight/test_api_scenarios.py#L114) | test | test |  |  |  |  |
| F0842 | 06_testing/api_tests | `test_reconcile_requires_executed_recommendation` | [tests/scinsight/test_api_scenarios.py:135](../tests/scinsight/test_api_scenarios.py#L135) | test | test |  |  |  |  |
| F0843 | 06_testing/api_tests | `test_demand_forecast_has_backtest_and_feeds_metrics` | [tests/scinsight/test_api_scenarios.py:141](../tests/scinsight/test_api_scenarios.py#L141) | test | test |  |  |  |  |
| F0844 | 06_testing/api_tests | `test_rag_is_tenant_scoped_cited_and_flags_injection` | [tests/scinsight/test_api_scenarios.py:147](../tests/scinsight/test_api_scenarios.py#L147) | test | test |  |  |  |  |
| F0845 | 06_testing/api_tests | `test_unauthenticated_and_invalid_keys` | [tests/scinsight/test_security.py:11](../tests/scinsight/test_security.py#L11) | test | test |  |  |  |  |
| F0846 | 06_testing/api_tests | `test_configured_keys_rotate_out_stored_dev_keys` | [tests/scinsight/test_security.py:17](../tests/scinsight/test_security.py#L17) | test | test |  |  |  |  |
| F0847 | 06_testing/api_tests | `test_postgres_deployment_refuses_to_start_without_all_keys` | [tests/scinsight/test_security.py:25](../tests/scinsight/test_security.py#L25) | test | test |  |  |  |  |
| F0848 | 06_testing/api_tests | `test_forged_tenant_is_rejected_and_audited` | [tests/scinsight/test_security.py:30](../tests/scinsight/test_security.py#L30) | test | test |  |  |  |  |
| F0849 | 06_testing/api_tests | `test_cross_tenant_data_is_invisible` | [tests/scinsight/test_security.py:36](../tests/scinsight/test_security.py#L36) | test | test |  |  |  |  |
| F0850 | 06_testing/api_tests | `test_sap_writes_are_blocked` | [tests/scinsight/test_security.py:43](../tests/scinsight/test_security.py#L43) | test | test |  |  |  |  |
| F0851 | 06_testing/api_tests | `test_sap_write_enabled_refuses_to_start` | [tests/scinsight/test_security.py:49](../tests/scinsight/test_security.py#L49) | test | test |  |  |  |  |
| F0852 | 06_testing/api_tests | `test_expired_snapshot_blocks_calculations` | [tests/scinsight/test_security.py:54](../tests/scinsight/test_security.py#L54) | test | test |  |  |  |  |
| F0853 | 06_testing/api_tests | `test_missing_snapshot_blocks_calculations` | [tests/scinsight/test_security.py:61](../tests/scinsight/test_security.py#L61) | test | test |  |  |  |  |
| F0854 | 06_testing/api_tests | `test_invalid_bom_and_unit_mismatch_are_explained` | [tests/scinsight/test_security.py:66](../tests/scinsight/test_security.py#L66) | test | test |  |  |  |  |
| F0855 | 06_testing/api_tests | `test_malformed_and_injected_tool_arguments` | [tests/scinsight/test_security.py:73](../tests/scinsight/test_security.py#L73) | test | test |  |  |  |  |
| F0856 | 06_testing/api_tests | `test_unknown_calculation_and_no_action_calculation` | [tests/scinsight/test_security.py:83](../tests/scinsight/test_security.py#L83) | test | test |  |  |  |  |
| F0857 | 06_testing/api_tests | `test_roles_are_enforced_server_side` | [tests/scinsight/test_security.py:89](../tests/scinsight/test_security.py#L89) | test | test |  |  |  |  |
| F0858 | 06_testing/api_tests | `test_incomplete_outcome_is_not_used_for_training` | [tests/scinsight/test_security.py:98](../tests/scinsight/test_security.py#L98) | test | test |  |  |  |  |
| F0859 | 06_testing/api_tests | `test_pending_outcome_is_reported_not_invented` | [tests/scinsight/test_security.py:105](../tests/scinsight/test_security.py#L105) | test | test |  |  |  |  |
| F0860 | 06_testing/api_tests | `test_concurrent_reviews_cannot_both_win` | [tests/scinsight/test_security.py:111](../tests/scinsight/test_security.py#L111) | test | test |  |  |  |  |
| F0861 | 06_testing/api_tests | `test_health_is_public_but_data_requires_key` | [tests/test_api.py:6](../tests/test_api.py#L6) | test | test |  |  |  |  |
| F0862 | 06_testing/api_tests | `test_sap_odata_reads_and_blocks_writes` | [tests/test_api.py:12](../tests/test_api.py#L12) | test | test |  |  |  |  |
| F0863 | 06_testing/api_tests | `test_analysis_validation_errors` | [tests/test_api.py:24](../tests/test_api.py#L24) | test | test |  |  |  |  |
| F0864 | 06_testing/api_tests | `test_all_analysis_endpoints` | [tests/test_api.py:31](../tests/test_api.py#L31) | test | test |  |  |  |  |
| F0865 | 06_testing/api_tests | `test_recommendation_lifecycle_and_roles` | [tests/test_api.py:50](../tests/test_api.py#L50) | test | test |  |  |  |  |
| F0866 | 06_testing/api_tests | `test_agent_handoff_selects_analysis_server_side` | [tests/test_api.py:72](../tests/test_api.py#L72) | test | test |  |  |  |  |
| F0867 | 06_testing/api_tests | `test_recommendation_requires_actions` | [tests/test_api.py:88](../tests/test_api.py#L88) | test | test |  |  |  |  |
| F0868 | 06_testing/api_tests | `test_rag_search_and_manager_only_ingest` | [tests/test_api.py:98](../tests/test_api.py#L98) | test | test |  |  |  |  |
| F0869 | 06_testing/api_tests | `test_chat_and_business_workflow_through_api` | [tests/test_api.py:106](../tests/test_api.py#L106) | test | test |  |  |  |  |
| F0870 | 06_testing/api_tests | `test_langgraph_agentflow_through_api` | [tests/test_api.py:121](../tests/test_api.py#L121) | test | test |  |  |  |  |
| F0871 | 06_testing/api_tests | `test_status_and_public_config` | [tests/test_api.py:129](../tests/test_api.py#L129) | test | test |  |  |  |  |
| F0872 | 06_testing/api_tests | `test_demo_session_disabled_by_default_and_enabled_for_local_demo` | [tests/test_api.py:136](../tests/test_api.py#L136) | test | test |  |  |  |  |
| F0873 | 06_testing/api_tests | `test_metrics_exposed` | [tests/test_api.py:147](../tests/test_api.py#L147) | test | test |  |  |  |  |
| F0874 | 06_testing/api_tests | `test_deep_agent_harness_settings_are_governed` | [tests/test_api.py:153](../tests/test_api.py#L153) | test | test |  |  |  |  |
| F0875 | 06_testing/api_tests | `test_sap_read_endpoints_are_read_only` | [tests/test_poc_contract.py:9](../tests/test_poc_contract.py#L9) | test | test |  |  |  |  |
| F0876 | 06_testing/api_tests | `test_forecasts_and_optimizers` | [tests/test_poc_contract.py:18](../tests/test_poc_contract.py#L18) | test | test |  |  |  |  |
| F0877 | 06_testing/api_tests | `test_decision_lifecycle_human_review_and_reconciliation` | [tests/test_poc_contract.py:31](../tests/test_poc_contract.py#L31) | test | test |  |  |  |  |
| F0878 | 06_testing/api_tests | `test_tenant_scoped_authorization` | [tests/test_poc_contract.py:51](../tests/test_poc_contract.py#L51) | test | test |  |  |  |  |
| F0879 | 06_testing/api_tests | `test_contract_is_documented_in_openapi` | [tests/test_poc_contract.py:65](../tests/test_poc_contract.py#L65) | test | test |  |  |  |  |
| F0880 | 06_testing/ops_tooling | `price` | [scripts/aws-cost-estimate.py:16](../scripts/aws-cost-estimate.py#L16) | function | used |  | F0881 |  |  |
| F0881 | 06_testing/ops_tooling | `main` | [scripts/aws-cost-estimate.py:30](../scripts/aws-cost-estimate.py#L30) | function | used |  |  |  |  |
| F0882 | 06_testing/smoke | `read_env` | [scripts/smoke.py:27](../scripts/smoke.py#L27) | function | used |  | F0903 |  |  |
| F0883 | 06_testing/smoke | `Smoke` | [scripts/smoke.py:36](../scripts/smoke.py#L36) | class | used |  | F0903 |  |  |
| F0884 | 06_testing/smoke | `Smoke.__init__` | [scripts/smoke.py:37](../scripts/smoke.py#L37) | method | used (framework) |  |  |  |  |
| F0885 | 06_testing/smoke | `Smoke.api` | [scripts/smoke.py:45](../scripts/smoke.py#L45) | method | used (framework) |  | F0887, F0888, F0889, F0890, F0891, F0892, F0893, F0894, F0895, F0896, F0900, F09 |  |  |
| F0886 | 06_testing/smoke | `Smoke.check` | [scripts/smoke.py:48](../scripts/smoke.py#L48) | method | used (framework) |  |  |  |  |
| F0887 | 06_testing/smoke | `Smoke.platform` | [scripts/smoke.py:59](../scripts/smoke.py#L59) | method | used (framework) |  |  |  |  |
| F0888 | 06_testing/smoke | `Smoke.security` | [scripts/smoke.py:67](../scripts/smoke.py#L67) | method | used (framework) |  |  |  |  |
| F0889 | 06_testing/smoke | `Smoke.analytics` | [scripts/smoke.py:75](../scripts/smoke.py#L75) | method | used (framework) |  |  |  |  |
| F0890 | 06_testing/smoke | `Smoke.rag` | [scripts/smoke.py:87](../scripts/smoke.py#L87) | method | used (framework) |  |  |  |  |
| F0891 | 06_testing/smoke | `Smoke.langgraph_chat` | [scripts/smoke.py:92](../scripts/smoke.py#L92) | method | used (framework) |  |  |  |  |
| F0892 | 06_testing/smoke | `Smoke.langgraph_agentflow` | [scripts/smoke.py:103](../scripts/smoke.py#L103) | method | used (framework) |  |  |  |  |
| F0893 | 06_testing/smoke | `Smoke.langgraph_business` | [scripts/smoke.py:116](../scripts/smoke.py#L116) | method | used (framework) |  |  |  |  |
| F0894 | 06_testing/smoke | `Smoke.deep_agent` | [scripts/smoke.py:126](../scripts/smoke.py#L126) | method | used (framework) |  |  |  |  |
| F0895 | 06_testing/smoke | `Smoke.flowise_chatflow` | [scripts/smoke.py:131](../scripts/smoke.py#L131) | method | used (framework) |  |  |  |  |
| F0896 | 06_testing/smoke | `Smoke.flowise_agentflow` | [scripts/smoke.py:137](../scripts/smoke.py#L137) | method | used (framework) |  |  |  |  |
| F0897 | 06_testing/smoke | `Smoke.mcp` | [scripts/smoke.py:146](../scripts/smoke.py#L146) | method | used (framework) |  |  |  |  |
| F0898 | 06_testing/smoke | `Smoke.mcp.run` | [scripts/smoke.py:147](../scripts/smoke.py#L147) | nested | tooling |  | F0897 |  |  |
| F0899 | 06_testing/smoke | `Smoke.langgraph_server` | [scripts/smoke.py:164](../scripts/smoke.py#L164) | method | used (framework) |  |  |  |  |
| F0900 | 06_testing/smoke | `Smoke.operations_workspace` | [scripts/smoke.py:172](../scripts/smoke.py#L172) | method | used (framework) |  |  |  |  |
| F0901 | 06_testing/smoke | `Smoke.manager_decision` | [scripts/smoke.py:193](../scripts/smoke.py#L193) | method | used (framework) |  |  |  |  |
| F0902 | 06_testing/smoke | `Smoke.observability` | [scripts/smoke.py:203](../scripts/smoke.py#L203) | method | used (framework) |  |  |  |  |
| F0903 | 06_testing/smoke | `main` | [scripts/smoke.py:225](../scripts/smoke.py#L225) | function | used |  |  |  |  |
| F0904 | 06_testing/unit_tests | `settings` | [tests/conftest.py:30](../tests/conftest.py#L30) | function | used |  | F0905 |  |  |
| F0905 | 06_testing/unit_tests | `client` | [tests/conftest.py:47](../tests/conftest.py#L47) | function | used |  |  |  |  |
| F0906 | 06_testing/unit_tests | `assistant_headers` | [tests/conftest.py:54](../tests/conftest.py#L54) | function | used |  |  |  |  |
| F0907 | 06_testing/unit_tests | `manager_headers` | [tests/conftest.py:59](../tests/conftest.py#L59) | function | used |  |  |  |  |
| F0908 | 06_testing/unit_tests | `settings` | [tests/scinsight/conftest.py:22](../tests/scinsight/conftest.py#L22) | function | used |  | F2034, F0909 |  |  |
| F0909 | 06_testing/unit_tests | `app` | [tests/scinsight/conftest.py:27](../tests/scinsight/conftest.py#L27) | function | used |  | F2034, F0910 |  |  |
| F0910 | 06_testing/unit_tests | `client` | [tests/scinsight/conftest.py:32](../tests/scinsight/conftest.py#L32) | function | used |  |  |  |  |
| F0911 | 06_testing/unit_tests | `key` | [tests/scinsight/conftest.py:37](../tests/scinsight/conftest.py#L37) | function | used |  |  |  |  |
| F0912 | 06_testing/unit_tests | `batch` | [tests/scinsight/test_business_rules.py:13](../tests/scinsight/test_business_rules.py#L13) | function | used |  | F0913, F0914, F0921 |  |  |
| F0913 | 06_testing/unit_tests | `test_usable_stock_excludes_blocked_inspection_reserved_expired_and_flags_near_expiry` | [tests/scinsight/test_business_rules.py:17](../tests/scinsight/test_business_rules.py#L17) | test | test |  |  |  |  |
| F0914 | 06_testing/unit_tests | `test_duplicate_batches_are_counted_once` | [tests/scinsight/test_business_rules.py:28](../tests/scinsight/test_business_rules.py#L28) | test | test |  |  |  |  |
| F0915 | 06_testing/unit_tests | `test_days_of_cover_and_replenishment_handle_zero_demand` | [tests/scinsight/test_business_rules.py:33](../tests/scinsight/test_business_rules.py#L33) | test | test |  |  |  |  |
| F0916 | 06_testing/unit_tests | `test_bom_requirements_units_rounding_and_invalid_versions` | [tests/scinsight/test_business_rules.py:40](../tests/scinsight/test_business_rules.py#L40) | test | test |  |  |  |  |
| F0917 | 06_testing/unit_tests | `test_shortage_counts_only_confirmed_timely_inbound_and_dedupes_pos` | [tests/scinsight/test_business_rules.py:56](../tests/scinsight/test_business_rules.py#L56) | test | test |  |  |  |  |
| F0918 | 06_testing/unit_tests | `test_transfer_candidates_feasibility_and_ranking` | [tests/scinsight/test_business_rules.py:66](../tests/scinsight/test_business_rules.py#L66) | test | test |  |  |  |  |
| F0919 | 06_testing/unit_tests | `test_nothing_is_recommended_when_no_option_is_in_time` | [tests/scinsight/test_business_rules.py:81](../tests/scinsight/test_business_rules.py#L81) | test | test |  |  |  |  |
| F0920 | 06_testing/unit_tests | `test_lead_time_estimate_and_prediction_error_and_reconciliation` | [tests/scinsight/test_business_rules.py:86](../tests/scinsight/test_business_rules.py#L86) | test | test |  |  |  |  |
| F0921 | 06_testing/unit_tests | `test_expiry_risk_is_ordered_most_urgent_first` | [tests/scinsight/test_business_rules.py:102](../tests/scinsight/test_business_rules.py#L102) | test | test |  |  |  |  |
| F0922 | 06_testing/unit_tests | `engine` | [tests/test_engine.py:12](../tests/test_engine.py#L12) | function | used |  | F0923, F0924, F0925, F0926, F0927, F0928, F0929, F0930, F0931, F0932 |  |  |
| F0923 | 06_testing/unit_tests | `test_readiness_counts_only_unrestricted_stock_and_confirmed_pos` | [tests/test_engine.py:17](../tests/test_engine.py#L17) | test | test |  |  |  |  |
| F0924 | 06_testing/unit_tests | `test_readiness_proposes_expedite_of_later_confirmed_po` | [tests/test_engine.py:32](../tests/test_engine.py#L32) | test | test |  |  |  |  |
| F0925 | 06_testing/unit_tests | `test_expired_batches_are_excluded` | [tests/test_engine.py:43](../tests/test_engine.py#L43) | test | test |  |  |  |  |
| F0926 | 06_testing/unit_tests | `test_ready_when_all_components_covered` | [tests/test_engine.py:50](../tests/test_engine.py#L50) | test | test |  |  |  |  |
| F0927 | 06_testing/unit_tests | `test_unknown_codes_are_rejected_with_valid_values` | [tests/test_engine.py:56](../tests/test_engine.py#L56) | test | test |  |  |  |  |
| F0928 | 06_testing/unit_tests | `test_stock_balance_moves_surplus_to_gap_with_ortools` | [tests/test_engine.py:61](../tests/test_engine.py#L61) | test | test |  |  |  |  |
| F0929 | 06_testing/unit_tests | `test_supplier_risk_scores` | [tests/test_engine.py:74](../tests/test_engine.py#L74) | test | test |  |  |  |  |
| F0930 | 06_testing/unit_tests | `test_quality_status_links_lots_to_production_orders` | [tests/test_engine.py:87](../tests/test_engine.py#L87) | test | test |  |  |  |  |
| F0931 | 06_testing/unit_tests | `test_logistics_escalates_long_delays` | [tests/test_engine.py:93](../tests/test_engine.py#L93) | test | test |  |  |  |  |
| F0932 | 06_testing/unit_tests | `test_inventory_and_kpis` | [tests/test_engine.py:100](../tests/test_engine.py#L100) | test | test |  |  |  |  |
| F0933 | 06_testing/unit_tests | `engine` | [tests/test_mentana_features.py:13](../tests/test_mentana_features.py#L13) | function | used |  | F0934, F0935, F0936, F0937, F0938, F0939 |  |  |
| F0934 | 06_testing/unit_tests | `test_insights_are_plain_english_deterministic_and_sorted` | [tests/test_mentana_features.py:18](../tests/test_mentana_features.py#L18) | test | test |  |  |  |  |
| F0935 | 06_testing/unit_tests | `test_sales_orders_find_shortfall_and_cheapest_on_time_transfer` | [tests/test_mentana_features.py:28](../tests/test_mentana_features.py#L28) | test | test |  |  |  |  |
| F0936 | 06_testing/unit_tests | `test_stocktake_explains_differences_with_evidence` | [tests/test_mentana_features.py:37](../tests/test_mentana_features.py#L37) | test | test |  |  |  |  |
| F0937 | 06_testing/unit_tests | `test_product_360_end_of_stock_resupply_suppliers_and_donor` | [tests/test_mentana_features.py:46](../tests/test_mentana_features.py#L46) | test | test |  |  |  |  |
| F0938 | 06_testing/unit_tests | `test_forecast_vs_actuals_backtest` | [tests/test_mentana_features.py:59](../tests/test_mentana_features.py#L59) | test | test |  |  |  |  |
| F0939 | 06_testing/unit_tests | `test_watch_evaluation` | [tests/test_mentana_features.py:65](../tests/test_mentana_features.py#L65) | test | test |  |  |  |  |
| F0940 | 06_testing/unit_tests | `test_api_dashboards_products_insights_watches` | [tests/test_mentana_features.py:73](../tests/test_mentana_features.py#L73) | test | test |  |  |  |  |
| F0941 | 06_testing/unit_tests | `test_dashboards_focus_on_one_product` | [tests/test_mentana_features.py:95](../tests/test_mentana_features.py#L95) | test | test |  |  |  |  |
| F0942 | 06_testing/unit_tests | `test_one_click_execution_only_after_acceptance_and_only_for_manager` | [tests/test_mentana_features.py:111](../tests/test_mentana_features.py#L111) | test | test |  |  |  |  |
| F0943 | 06_testing/unit_tests | `engine` | [tests/test_product_brief_outlook.py:11](../tests/test_product_brief_outlook.py#L11) | function | used |  | F0944, F0945 |  |  |
| F0944 | 06_testing/unit_tests | `test_brief_pairs_every_issue_with_a_fix_and_action` | [tests/test_product_brief_outlook.py:16](../tests/test_product_brief_outlook.py#L16) | test | test |  |  |  |  |
| F0945 | 06_testing/unit_tests | `test_outlook_sales_rates_and_calendar` | [tests/test_product_brief_outlook.py:34](../tests/test_product_brief_outlook.py#L34) | test | test |  |  |  |  |
| F0946 | 06_testing/unit_tests | `test_brief_and_outlook_endpoints_follow_tenant` | [tests/test_product_brief_outlook.py:48](../tests/test_product_brief_outlook.py#L48) | test | test |  |  |  |  |
| F0947 | 06_testing/unit_tests | `test_chunking_keeps_title_and_section` | [tests/test_rag_mcp_store.py:14](../tests/test_rag_mcp_store.py#L14) | test | test |  |  |  |  |
| F0948 | 06_testing/unit_tests | `test_keyword_boost_rewards_exact_sap_codes` | [tests/test_rag_mcp_store.py:19](../tests/test_rag_mcp_store.py#L19) | test | test |  |  |  |  |
| F0949 | 06_testing/unit_tests | `test_memory_rag_finds_category_and_injection_text_is_just_data` | [tests/test_rag_mcp_store.py:24](../tests/test_rag_mcp_store.py#L24) | test | test |  |  |  |  |
| F0950 | 06_testing/unit_tests | `test_fastembed_semantic_retrieval` | [tests/test_rag_mcp_store.py:33](../tests/test_rag_mcp_store.py#L33) | test | test |  |  |  |  |
| F0951 | 06_testing/unit_tests | `test_mcp_server_tools_health_and_auth` | [tests/test_rag_mcp_store.py:43](../tests/test_rag_mcp_store.py#L43) | test | test |  |  |  |  |
| F0952 | 06_testing/unit_tests | `_exercise_store` | [tests/test_rag_mcp_store.py:68](../tests/test_rag_mcp_store.py#L68) | function | used |  | F0953, F0954 |  |  |
| F0953 | 06_testing/unit_tests | `test_sqlite_store` | [tests/test_rag_mcp_store.py:81](../tests/test_rag_mcp_store.py#L81) | test | test |  |  |  |  |
| F0954 | 06_testing/unit_tests | `test_postgres_store_and_pgvector_rag` | [tests/test_rag_mcp_store.py:85](../tests/test_rag_mcp_store.py#L85) | test | test |  |  |  |  |
| F0955 | 06_testing/unit_tests | `test_catalogue_puts_the_five_mvp_roles_first` | [tests/test_roles_and_moat.py:12](../tests/test_roles_and_moat.py#L12) | test | test |  |  |  |  |
| F0956 | 06_testing/unit_tests | `test_every_role_answers_the_four_questions` | [tests/test_roles_and_moat.py:19](../tests/test_roles_and_moat.py#L19) | test | test |  |  |  |  |
| F0957 | 06_testing/unit_tests | `test_role_views_know_the_aurelia_situation` | [tests/test_roles_and_moat.py:35](../tests/test_roles_and_moat.py#L35) | test | test |  |  |  |  |
| F0958 | 06_testing/unit_tests | `test_north_star_platform_kpis_and_industry_kpis` | [tests/test_roles_and_moat.py:51](../tests/test_roles_and_moat.py#L51) | test | test |  |  |  |  |
| F0959 | 06_testing/unit_tests | `test_approval_is_not_proof_until_the_outcome_is_recorded` | [tests/test_roles_and_moat.py:61](../tests/test_roles_and_moat.py#L61) | test | test |  |  |  |  |
| F0960 | 06_testing/unit_tests | `test_moat_view_flywheel_metrics_and_consent_gate` | [tests/test_roles_and_moat.py:86](../tests/test_roles_and_moat.py#L86) | test | test |  |  |  |  |
| F0961 | 06_testing/unit_tests | `test_role_agent_gets_scoped_tools_and_industry_rules` | [tests/test_roles_and_moat.py:106](../tests/test_roles_and_moat.py#L106) | test | test |  |  |  |  |
| F0962 | 06_testing/unit_tests | `test_chat_accepts_only_known_roles` | [tests/test_roles_and_moat.py:115](../tests/test_roles_and_moat.py#L115) | test | test |  |  |  |  |
| F0963 | 06_testing/unit_tests | `test_catalogue_lists_industries_and_customers` | [tests/test_tenants_and_map.py:13](../tests/test_tenants_and_map.py#L13) | test | test |  |  |  |  |
| F0964 | 06_testing/unit_tests | `test_every_view_works_for_each_customer` | [tests/test_tenants_and_map.py:22](../tests/test_tenants_and_map.py#L22) | test | test |  |  |  |  |
| F0965 | 06_testing/unit_tests | `test_customers_are_isolated` | [tests/test_tenants_and_map.py:37](../tests/test_tenants_and_map.py#L37) | test | test |  |  |  |  |
| F0966 | 06_testing/unit_tests | `test_network_map_tiers_and_sourcing` | [tests/test_tenants_and_map.py:50](../tests/test_tenants_and_map.py#L50) | test | test |  |  |  |  |
| F0967 | 07_flowise_functions/deployment | `log` | [flowise/bootstrap.py:37](../flowise/bootstrap.py#L37) | function | used |  | F0975 |  |  |
| F0968 | 07_flowise_functions/deployment | `read_env` | [flowise/bootstrap.py:41](../flowise/bootstrap.py#L41) | function | used |  | F0975 |  |  |
| F0969 | 07_flowise_functions/deployment | `write_env` | [flowise/bootstrap.py:50](../flowise/bootstrap.py#L50) | function | used |  | F0975 |  |  |
| F0970 | 07_flowise_functions/deployment | `Flowise` | [flowise/bootstrap.py:62](../flowise/bootstrap.py#L62) | class | used |  | F0975 |  |  |
| F0971 | 07_flowise_functions/deployment | `Flowise.__init__` | [flowise/bootstrap.py:63](../flowise/bootstrap.py#L63) | method | used (framework) |  |  |  |  |
| F0972 | 07_flowise_functions/deployment | `Flowise.call` | [flowise/bootstrap.py:70](../flowise/bootstrap.py#L70) | method | used |  | F0973, F0975, F0976, F1782, F0980, F0981, F0982 |  |  |
| F0973 | 07_flowise_functions/deployment | `Flowise.wait` | [flowise/bootstrap.py:96](../flowise/bootstrap.py#L96) | method | used |  | F2172, F0619, F0620, F0975, F1782, F0981 |  |  |
| F0974 | 07_flowise_functions/deployment | `build_flows` | [flowise/bootstrap.py:106](../flowise/bootstrap.py#L106) | function | used |  | F0975 |  |  |
| F0975 | 07_flowise_functions/deployment | `main` | [flowise/bootstrap.py:129](../flowise/bootstrap.py#L129) | function | used |  |  |  |  |
| F0976 | 07_flowise_functions/deployment | `main.upsert_credential` | [flowise/bootstrap.py:183](../flowise/bootstrap.py#L183) | nested | used |  | F0975 |  |  |
| F0977 | 07_flowise_functions/deployment | `rag_documents` | [flowise/scinsight/deploy.py:44](../flowise/scinsight/deploy.py#L44) | function | used | Governed documents eligible for the native RAG DB: valid front matter, tenant scinsight-co | F0978 |  |  |
| F0978 | 07_flowise_functions/deployment | `build` | [flowise/scinsight/deploy.py:61](../flowise/scinsight/deploy.py#L61) | function | used |  | F0984 |  |  |
| F0979 | 07_flowise_functions/deployment | `build.dump` | [flowise/scinsight/deploy.py:70](../flowise/scinsight/deploy.py#L70) | nested | used |  | F0978 |  |  |
| F0980 | 07_flowise_functions/deployment | `ensure_api_key` | [flowise/scinsight/deploy.py:134](../flowise/scinsight/deploy.py#L134) | function | used |  | F0981 |  |  |
| F0981 | 07_flowise_functions/deployment | `import_flows` | [flowise/scinsight/deploy.py:149](../flowise/scinsight/deploy.py#L149) | function | used |  | F0984 |  |  |
| F0982 | 07_flowise_functions/deployment | `import_flows.credential` | [flowise/scinsight/deploy.py:177](../flowise/scinsight/deploy.py#L177) | nested | used |  | F0981 |  |  |
| F0983 | 07_flowise_functions/deployment | `import_flows.bind` | [flowise/scinsight/deploy.py:202](../flowise/scinsight/deploy.py#L202) | nested | used |  | F0981 |  |  |
| F0984 | 07_flowise_functions/deployment | `main` | [flowise/scinsight/deploy.py:275](../flowise/scinsight/deploy.py#L275) | function | used |  |  |  |  |
| F0985 | 01_fastapi/endpoints | `create_app.code_functions` | [backend/app/main.py:626](../backend/app/main.py#L626) | route | used |  | F1796 | GET /api/v1/code/functions |  |
| F0986 | 01_fastapi/endpoints | `create_app.code_function` | [backend/app/main.py:631](../backend/app/main.py#L631) | route | used |  | F1796 | GET /api/v1/code/function |  |
| F0987 | 01_fastapi/endpoints | `create_app.code_update` | [backend/app/main.py:639](../backend/app/main.py#L639) | route | used |  | F1796 | PUT /api/v1/code/function |  |
| F0988 | 01_fastapi/pydantic_models | `CodeUpdateRequest` | [backend/app/schemas.py:218](../backend/app/schemas.py#L218) | pydantic_model | used | Replace one backend function or class (UI backend code section; development only). | F0987, F0987 |  |  |
| F1781 | 06_testing/other | `build` | [flowise/code_explorer/deploy_code_map.py:27](../flowise/code_explorer/deploy_code_map.py#L27) | function | used |  | F1783 |  |  |
| F1782 | 06_testing/other | `import_flows` | [flowise/code_explorer/deploy_code_map.py:44](../flowise/code_explorer/deploy_code_map.py#L44) | function | used |  | F1783 |  |  |
| F1783 | 06_testing/other | `main` | [flowise/code_explorer/deploy_code_map.py:69](../flowise/code_explorer/deploy_code_map.py#L69) | function | used |  |  |  |  |
| F1784 | 06_testing/other | `_defs` | [backend/app/code_editor.py:42](../backend/app/code_editor.py#L42) | function | used (framework) | qualname -> def/class node, including methods and nested functions. | F1791, F1792, F1793 |  |  |
| F1785 | 06_testing/other | `_defs.walk` | [backend/app/code_editor.py:46](../backend/app/code_editor.py#L46) | nested | used (framework) |  | F1784 |  |  |
| F1786 | 06_testing/other | `_span` | [backend/app/code_editor.py:57](../backend/app/code_editor.py#L57) | function | used (framework) |  | F1791, F1793, F1794 |  |  |
| F1787 | 06_testing/other | `CodeEditor` | [backend/app/code_editor.py:61](../backend/app/code_editor.py#L61) | class | used |  | F0017, F1797, F1798, F1799 |  |  |
| F1788 | 06_testing/other | `CodeEditor.__init__` | [backend/app/code_editor.py:62](../backend/app/code_editor.py#L62) | method | used (framework) |  |  |  |  |
| F1789 | 06_testing/other | `CodeEditor._registry` | [backend/app/code_editor.py:69](../backend/app/code_editor.py#L69) | method | used (framework) |  | F1791, F1793 |  |  |
| F1790 | 06_testing/other | `CodeEditor._files` | [backend/app/code_editor.py:77](../backend/app/code_editor.py#L77) | method | used |  | F1952, F1791, F1793 |  |  |
| F1791 | 06_testing/other | `CodeEditor.list` | [backend/app/code_editor.py:145](../backend/app/code_editor.py#L145) | method | used (framework) |  |  |  |  |
| F1792 | 06_testing/other | `CodeEditor._locate` | [backend/app/code_editor.py:172](../backend/app/code_editor.py#L172) | method | used (framework) |  | F1793, F1794 |  |  |
| F1793 | 06_testing/other | `CodeEditor.get` | [backend/app/code_editor.py:185](../backend/app/code_editor.py#L185) | method | used (framework) |  |  |  |  |
| F1794 | 06_testing/other | `CodeEditor.update` | [backend/app/code_editor.py:215](../backend/app/code_editor.py#L215) | method | used (framework) |  |  |  |  |
| F1795 | 06_testing/unit_tests | `repo` | [tests/test_code_editor.py:24](../tests/test_code_editor.py#L24) | function | used |  | F1797, F1798, F1799 |  |  |
| F1796 | 06_testing/unit_tests | `test_api_lists_and_shows_backend_functions_read_only_by_default` | [tests/test_code_editor.py:31](../tests/test_code_editor.py#L31) | test | test |  |  |  |  |
| F1797 | 06_testing/unit_tests | `test_edit_replaces_only_the_selected_method_and_keeps_a_backup` | [tests/test_code_editor.py:58](../tests/test_code_editor.py#L58) | test | test |  |  |  |  |
| F1798 | 06_testing/unit_tests | `test_invalid_edits_are_refused_and_the_file_is_untouched` | [tests/test_code_editor.py:71](../tests/test_code_editor.py#L71) | test | test |  |  |  |  |
| F1799 | 06_testing/unit_tests | `test_editing_is_off_outside_development_and_stale_saves_are_refused` | [tests/test_code_editor.py:83](../tests/test_code_editor.py#L83) | test | test |  |  |  |  |
| F1800 | 06_testing/other | `CodeEditor._apps_of` | [backend/app/code_editor.py:80](../backend/app/code_editor.py#L80) | method | used | file -> ids of the apps that load it (transitive backend imports from each app's entry mod | F1952, F1791, F1793 |  |  |
| F1801 | 01_fastapi/endpoints | `create_app.rag_tuning_proxy` | [backend/app/main.py:583](../backend/app/main.py#L583) | route | used |  | F1819, F1824, F1825, F1826, F1827, F1828, F1829, F1830, F1831, F1832, F1833, F18 | GET/POST/PUT /api/v1/rag-tuning/{path:path} |  |
| F1802 | 04_ai_ml/rag | `HashEmbedder.__init__` | [backend/scinsight/rag.py:72](../backend/scinsight/rag.py#L72) | method | used (framework) |  |  |  |  |
| F1803 | 04_ai_ml/rag | `_vec` | [backend/scinsight/rag.py:95](../backend/scinsight/rag.py#L95) | function | used |  | F1807, F0766 |  |  |
| F1804 | 04_ai_ml/rag | `KnowledgeBase.embedder_for` | [backend/scinsight/rag.py:104](../backend/scinsight/rag.py#L104) | method | used | The embedder of an index: the service's own model, or another approved model (never a sile | F1807, F0766, F1895 |  |  |
| F1805 | 04_ai_ml/rag | `KnowledgeBase.baseline` | [backend/scinsight/rag.py:111](../backend/scinsight/rag.py#L111) | method | used |  | F1806, F1904 |  |  |
| F1806 | 04_ai_ml/rag | `KnowledgeBase.active` | [backend/scinsight/rag.py:114](../backend/scinsight/rag.py#L114) | method | used | (config version id, configuration, index version) used by live search for this tenant. | F0765, F0766, F1832, F1836, F1860 |  |  |
| F1807 | 04_ai_ml/rag | `KnowledgeBase._chunk_statements` | [backend/scinsight/rag.py:122](../backend/scinsight/rag.py#L122) | method | used |  | F0765, F1808 |  |  |
| F1808 | 04_ai_ml/rag | `KnowledgeBase.build_index` | [backend/scinsight/rag.py:166](../backend/scinsight/rag.py#L166) | method | used | Write a complete index version for one tenant (the active index is never touched). | F1892 |  |  |
| F1809 | 04_ai_ml/rag | `KnowledgeBase._log` | [backend/scinsight/rag.py:260](../backend/scinsight/rag.py#L260) | method | used |  | F0766 |  |  |
| F1810 | 06_testing/other | `DraftRequest` | [backend/scinsight/rag_tuning/api.py:38](../backend/scinsight/rag_tuning/api.py#L38) | pydantic_model | used |  | F1825, F1825 |  |  |
| F1811 | 06_testing/other | `PreviewRequest` | [backend/scinsight/rag_tuning/api.py:44](../backend/scinsight/rag_tuning/api.py#L44) | pydantic_model | used |  | F1831, F1831 |  |  |
| F1812 | 06_testing/other | `RetrieveRequest` | [backend/scinsight/rag_tuning/api.py:50](../backend/scinsight/rag_tuning/api.py#L50) | pydantic_model | used |  | F1836, F1836 |  |  |
| F1813 | 06_testing/other | `ModelTestRequest` | [backend/scinsight/rag_tuning/api.py:57](../backend/scinsight/rag_tuning/api.py#L57) | pydantic_model | used |  | F1833, F1833 |  |  |
| F1814 | 06_testing/other | `ConfigRef` | [backend/scinsight/rag_tuning/api.py:61](../backend/scinsight/rag_tuning/api.py#L61) | pydantic_model | used |  | F1834, F1834, F1843, F1843, F1844, F1844, F1845, F1845 |  |  |
| F1815 | 06_testing/other | `EvaluateRequest` | [backend/scinsight/rag_tuning/api.py:66](../backend/scinsight/rag_tuning/api.py#L66) | pydantic_model | used |  | F1838, F1838 |  |  |
| F1816 | 06_testing/other | `GridRequest` | [backend/scinsight/rag_tuning/api.py:72](../backend/scinsight/rag_tuning/api.py#L72) | pydantic_model | used |  | F1839, F1839 |  |  |
| F1817 | 06_testing/other | `_llm_answer_fn` | [backend/scinsight/rag_tuning/api.py:80](../backend/scinsight/rag_tuning/api.py#L80) | function | used | OpenAI-compatible chat call (the same Qwen endpoint as the agents). Returns (answer, usage | F1837 |  |  |
| F1818 | 06_testing/other | `_llm_answer_fn.answer` | [backend/scinsight/rag_tuning/api.py:85](../backend/scinsight/rag_tuning/api.py#L85) | nested | used |  | F1817 |  |  |
| F1819 | 06_testing/other | `register` | [backend/scinsight/rag_tuning/api.py:99](../backend/scinsight/rag_tuning/api.py#L99) | function | used |  | F1993 |  |  |
| F1820 | 06_testing/other | `register.admin` | [backend/scinsight/rag_tuning/api.py:106](../backend/scinsight/rag_tuning/api.py#L106) | nested | used |  | F1824, F1824, F1825, F1825, F1826, F1826, F1827, F1827, F1828, F1828, F1829, F18 |  |  |
| F1821 | 06_testing/other | `register.audit` | [backend/scinsight/rag_tuning/api.py:110](../backend/scinsight/rag_tuning/api.py#L110) | nested | used |  | F1825, F1833, F1834, F1838, F1839, F1844, F1845 |  |  |
| F1822 | 06_testing/other | `register.cfg_of` | [backend/scinsight/rag_tuning/api.py:113](../backend/scinsight/rag_tuning/api.py#L113) | nested | used |  | F1827, F1834, F1836, F1837, F1838, F1843, F1844, F1845 |  |  |
| F1823 | 06_testing/other | `register.job` | [backend/scinsight/rag_tuning/api.py:120](../backend/scinsight/rag_tuning/api.py#L120) | nested | used |  | F1833, F1834, F1838, F1839 |  |  |
| F1824 | 06_testing/other | `register.get_config` | [backend/scinsight/rag_tuning/api.py:124](../backend/scinsight/rag_tuning/api.py#L124) | route | used |  | F1801, F1954, F2036 | GET /api/v1/rag-tuning/config |  |
| F1825 | 06_testing/other | `register.save_draft` | [backend/scinsight/rag_tuning/api.py:138](../backend/scinsight/rag_tuning/api.py#L138) | route | used |  | F1801, F1954 | PUT /api/v1/rag-tuning/draft |  |
| F1826 | 06_testing/other | `register.history` | [backend/scinsight/rag_tuning/api.py:144](../backend/scinsight/rag_tuning/api.py#L144) | route | used |  | F1801, F1954 | GET /api/v1/rag-tuning/history |  |
| F1827 | 06_testing/other | `register.config_diff` | [backend/scinsight/rag_tuning/api.py:148](../backend/scinsight/rag_tuning/api.py#L148) | route | used |  | F1801, F1954 | GET /api/v1/rag-tuning/diff/{config_id} |  |
| F1828 | 06_testing/other | `register.list_documents` | [backend/scinsight/rag_tuning/api.py:154](../backend/scinsight/rag_tuning/api.py#L154) | route | used |  | F1801, F1954, F2036 | GET /api/v1/rag-tuning/documents |  |
| F1829 | 06_testing/other | `register.validate_metadata` | [backend/scinsight/rag_tuning/api.py:158](../backend/scinsight/rag_tuning/api.py#L158) | route | used |  | F1801, F1954 | POST /api/v1/rag-tuning/metadata/validate |  |
| F1830 | 06_testing/other | `register.document_source` | [backend/scinsight/rag_tuning/api.py:166](../backend/scinsight/rag_tuning/api.py#L166) | route | used |  | F1801, F1954 | GET /api/v1/rag-tuning/documents/{doc_id}/source |  |
| F1831 | 06_testing/other | `register.chunk_preview` | [backend/scinsight/rag_tuning/api.py:174](../backend/scinsight/rag_tuning/api.py#L174) | route | used |  | F1801, F1954 | POST /api/v1/rag-tuning/chunks/preview |  |
| F1832 | 06_testing/other | `register.embedding_models` | [backend/scinsight/rag_tuning/api.py:187](../backend/scinsight/rag_tuning/api.py#L187) | route | used |  | F1801, F1954 | GET /api/v1/rag-tuning/embedding-models |  |
| F1833 | 06_testing/other | `register.test_model` | [backend/scinsight/rag_tuning/api.py:193](../backend/scinsight/rag_tuning/api.py#L193) | route | used |  | F1801, F1954 | POST /api/v1/rag-tuning/embedding-models/test |  |
| F1834 | 06_testing/other | `register.build_candidate` | [backend/scinsight/rag_tuning/api.py:202](../backend/scinsight/rag_tuning/api.py#L202) | route | used |  | F1801, F1954 | POST /api/v1/rag-tuning/index/build-candidate |  |
| F1835 | 06_testing/other | `register.get_job` | [backend/scinsight/rag_tuning/api.py:209](../backend/scinsight/rag_tuning/api.py#L209) | route | used |  | F1801, F1923, F1954 | GET /api/v1/rag-tuning/jobs/{job_id} |  |
| F1836 | 06_testing/other | `register.retrieve_preview` | [backend/scinsight/rag_tuning/api.py:217](../backend/scinsight/rag_tuning/api.py#L217) | route | used | retrieve_with_config: the live search function with a stored configuration and/or hot over | F1801, F1954 | POST /api/v1/rag-tuning/retrieve/preview |  |
| F1837 | 06_testing/other | `register._benchmark` | [backend/scinsight/rag_tuning/api.py:239](../backend/scinsight/rag_tuning/api.py#L239) | nested | used |  | F1838, F1839 |  |  |
| F1838 | 06_testing/other | `register.evaluate` | [backend/scinsight/rag_tuning/api.py:255](../backend/scinsight/rag_tuning/api.py#L255) | route | used |  | F1801, F1954 | POST /api/v1/rag-tuning/evaluate |  |
| F1839 | 06_testing/other | `register.evaluate_grid` | [backend/scinsight/rag_tuning/api.py:263](../backend/scinsight/rag_tuning/api.py#L263) | route | used | Shows the workload first; runs only when confirm=true (no silent Cartesian products). | F1801, F1954 | POST /api/v1/rag-tuning/evaluate/grid |  |
| F1840 | 06_testing/other | `register.list_experiments` | [backend/scinsight/rag_tuning/api.py:287](../backend/scinsight/rag_tuning/api.py#L287) | route | used |  | F1801, F1954 | GET /api/v1/rag-tuning/experiments |  |
| F1841 | 06_testing/other | `register.compare` | [backend/scinsight/rag_tuning/api.py:291](../backend/scinsight/rag_tuning/api.py#L291) | route | used |  | F1801, F1954 | GET /api/v1/rag-tuning/experiments/compare |  |
| F1842 | 06_testing/other | `register.get_experiment` | [backend/scinsight/rag_tuning/api.py:298](../backend/scinsight/rag_tuning/api.py#L298) | route | used |  | F1801, F1954 | GET /api/v1/rag-tuning/experiments/{exp_id} |  |
| F1843 | 06_testing/other | `register.validate` | [backend/scinsight/rag_tuning/api.py:306](../backend/scinsight/rag_tuning/api.py#L306) | route | used |  | F1801, F1954 | POST /api/v1/rag-tuning/validate |  |
| F1844 | 06_testing/other | `register.publish` | [backend/scinsight/rag_tuning/api.py:311](../backend/scinsight/rag_tuning/api.py#L311) | route | used |  | F1801, F1954, F2036 | POST /api/v1/rag-tuning/publish |  |
| F1845 | 06_testing/other | `register.rollback` | [backend/scinsight/rag_tuning/api.py:325](../backend/scinsight/rag_tuning/api.py#L325) | route | used |  | F1801, F1954 | POST /api/v1/rag-tuning/rollback |  |
| F1846 | 06_testing/other | `register.flowise_status` | [backend/scinsight/rag_tuning/api.py:340](../backend/scinsight/rag_tuning/api.py#L340) | route | used |  | F1801, F1954 | GET /api/v1/rag-tuning/flowise |  |
| F1847 | 06_testing/other | `register.metrics` | [backend/scinsight/rag_tuning/api.py:344](../backend/scinsight/rag_tuning/api.py#L344) | route | used |  | F1801, F1954 | GET /api/v1/rag-tuning/metrics |  |
| F1848 | 06_testing/other | `_sections` | [backend/scinsight/rag_tuning/chunking.py:18](../backend/scinsight/rag_tuning/chunking.py#L18) | function | used |  | F1851 |  |  |
| F1849 | 06_testing/other | `_windows` | [backend/scinsight/rag_tuning/chunking.py:33](../backend/scinsight/rag_tuning/chunking.py#L33) | function | used |  | F1850, F1851, F1851 |  |  |
| F1850 | 06_testing/other | `_clauses` | [backend/scinsight/rag_tuning/chunking.py:44](../backend/scinsight/rag_tuning/chunking.py#L44) | function | used |  | F1851 |  |  |
| F1851 | 06_testing/other | `chunk` | [backend/scinsight/rag_tuning/chunking.py:71](../backend/scinsight/rag_tuning/chunking.py#L71) | function | used | Chunks of one document: [{chunk_index, section, text (as indexed), content (without prefix | F0759, F1807, F1853, F1933 |  |  |
| F1852 | 06_testing/other | `overlap_chars` | [backend/scinsight/rag_tuning/chunking.py:89](../backend/scinsight/rag_tuning/chunking.py#L89) | function | used | Characters at the end of `left` repeated at the start of `right` (what the overlap actuall | F1853 |  |  |
| F1853 | 06_testing/other | `preview_document_chunks` | [backend/scinsight/rag_tuning/chunking.py:97](../backend/scinsight/rag_tuning/chunking.py#L97) | function | used | What the configuration would index for one document (nothing is written). | F1831, F1933 |  |  |
| F1854 | 06_testing/other | `RagTuningConfig` | [backend/scinsight/rag_tuning/config.py:26](../backend/scinsight/rag_tuning/config.py#L26) | pydantic_model | used | One RAG configuration version. Cold fields define the index; hot fields only change how it | F0759, F1805, F1806, F1807, F1808, F0766, F1822, F1824, F1836, F1839, F1851, F18 |  |  |
| F1855 | 06_testing/other | `RagTuningConfig.validate_chunking` | [backend/scinsight/rag_tuning/config.py:48](../backend/scinsight/rag_tuning/config.py#L48) | method | used (framework) |  |  |  |  |
| F1856 | 06_testing/other | `baseline_config` | [backend/scinsight/rag_tuning/config.py:58](../backend/scinsight/rag_tuning/config.py#L58) | function | used | The configuration the service ran with before tuning existed (backend/scinsight/rag.py: 90 | F1805 |  |  |
| F1857 | 06_testing/other | `diff` | [backend/scinsight/rag_tuning/config.py:63](../backend/scinsight/rag_tuning/config.py#L63) | function | used | Changed settings, split into those that need a rebuild (cold) and those that apply at quer | F1827, F1892, F1908, F1931 |  |  |
| F1858 | 06_testing/other | `index_signature` | [backend/scinsight/rag_tuning/config.py:70](../backend/scinsight/rag_tuning/config.py#L70) | function | used | The cold settings: two configurations with the same signature can share one index. | F1839 |  |  |
| F1859 | 06_testing/other | `_front_matter` | [backend/scinsight/rag_tuning/documents.py:20](../backend/scinsight/rag_tuning/documents.py#L20) | function | used |  | F1860 |  |  |
| F1860 | 06_testing/other | `inventory` | [backend/scinsight/rag_tuning/documents.py:25](../backend/scinsight/rag_tuning/documents.py#L25) | function | used | Every source file of the caller's tenant with its metadata, index state and deficiencies ( | F1828, F1829 |  |  |
| F1861 | 06_testing/other | `validate_document_metadata` | [backend/scinsight/rag_tuning/documents.py:71](../backend/scinsight/rag_tuning/documents.py#L71) | function | used | Checks on one document: missing fields, scope, validity and source quality (severity: erro | F1860 |  |  |
| F1862 | 06_testing/other | `_cross_document_checks` | [backend/scinsight/rag_tuning/documents.py:98](../backend/scinsight/rag_tuning/documents.py#L98) | function | used |  | F1860 |  |  |
| F1863 | 06_testing/other | `source_text` | [backend/scinsight/rag_tuning/documents.py:120](../backend/scinsight/rag_tuning/documents.py#L120) | function | used | The source document of the caller's tenant (front matter + body) for preview; other tenant | F1830, F1831 |  |  |
| F1864 | 06_testing/other | `ModelUnavailable` | [backend/scinsight/rag_tuning/embeddings.py:30](../backend/scinsight/rag_tuning/embeddings.py#L30) | class | used |  | F1868 |  |  |
| F1865 | 06_testing/other | `approved` | [backend/scinsight/rag_tuning/embeddings.py:34](../backend/scinsight/rag_tuning/embeddings.py#L34) | function | used |  | F1833, F1839, F1867, F1868, F1869, F1892, F1893 |  |  |
| F1866 | 06_testing/other | `_installed` | [backend/scinsight/rag_tuning/embeddings.py:38](../backend/scinsight/rag_tuning/embeddings.py#L38) | function | used |  | F1867, F1868 |  |  |
| F1867 | 06_testing/other | `list_supported_embedding_models` | [backend/scinsight/rag_tuning/embeddings.py:47](../backend/scinsight/rag_tuning/embeddings.py#L47) | function | used | The approved list with what is actually known about each model (installed, dimensions, lan | F1832 |  |  |
| F1868 | 06_testing/other | `get_embedder` | [backend/scinsight/rag_tuning/embeddings.py:56](../backend/scinsight/rag_tuning/embeddings.py#L56) | function | used | Embedder for an approved model. Raises ModelUnavailable instead of substituting a differen | F0762, F1804, F1869 |  |  |
| F1869 | 06_testing/other | `test_model` | [backend/scinsight/rag_tuning/embeddings.py:80](../backend/scinsight/rag_tuning/embeddings.py#L80) | function | used | Load the model (downloading it if allowed), embed sample texts, check dimensions and measu | F1833 |  |  |
| F1870 | 06_testing/other | `load_dataset` | [backend/scinsight/rag_tuning/evaluation.py:29](../backend/scinsight/rag_tuning/evaluation.py#L29) | function | used |  | F1838, F1839, F1874, F1942 |  |  |
| F1871 | 06_testing/other | `_p95` | [backend/scinsight/rag_tuning/evaluation.py:35](../backend/scinsight/rag_tuning/evaluation.py#L35) | function | used |  | F1875 |  |  |
| F1872 | 06_testing/other | `score_case` | [backend/scinsight/rag_tuning/evaluation.py:42](../backend/scinsight/rag_tuning/evaluation.py#L42) | function | used | Deterministic retrieval scores of one case. | F1874, F1940 |  |  |
| F1873 | 06_testing/other | `score_answer` | [backend/scinsight/rag_tuning/evaluation.py:64](../backend/scinsight/rag_tuning/evaluation.py#L64) | function | used | Checks of an LLM answer against the retrieved evidence (deterministic; the model's confide | F1874, F1941 |  |  |
| F1874 | 06_testing/other | `run_rag_benchmark` | [backend/scinsight/rag_tuning/evaluation.py:82](../backend/scinsight/rag_tuning/evaluation.py#L82) | function | used | Every case through KnowledgeBase.search (the function behind /api/v1/rag/search) with the  | F1837 |  |  |
| F1875 | 06_testing/other | `summarize` | [backend/scinsight/rag_tuning/evaluation.py:103](../backend/scinsight/rag_tuning/evaluation.py#L103) | function | used |  | F1874 |  |  |
| F1876 | 06_testing/other | `summarize.mean` | [backend/scinsight/rag_tuning/evaluation.py:104](../backend/scinsight/rag_tuning/evaluation.py#L104) | nested | used |  | F1875 |  |  |
| F1877 | 06_testing/other | `compare_experiments` | [backend/scinsight/rag_tuning/evaluation.py:127](../backend/scinsight/rag_tuning/evaluation.py#L127) | function | used | Side-by-side measured metrics and a recommendation from the acceptance criteria (no invent | F1841, F1895 |  |  |
| F1878 | 06_testing/other | `compare_experiments.check` | [backend/scinsight/rag_tuning/evaluation.py:136](../backend/scinsight/rag_tuning/evaluation.py#L136) | nested | used |  | F1877 |  |  |
| F1879 | 06_testing/other | `FlowiseError` | [backend/scinsight/rag_tuning/flowise_adapter.py:22](../backend/scinsight/rag_tuning/flowise_adapter.py#L22) | class | used |  | F1883, F1884, F1886, F1889 |  |  |
| F1880 | 06_testing/other | `FlowiseAdapter` | [backend/scinsight/rag_tuning/flowise_adapter.py:26](../backend/scinsight/rag_tuning/flowise_adapter.py#L26) | class | used |  | F1819 |  |  |
| F1881 | 06_testing/other | `FlowiseAdapter.__init__` | [backend/scinsight/rag_tuning/flowise_adapter.py:27](../backend/scinsight/rag_tuning/flowise_adapter.py#L27) | method | used (framework) |  |  |  |  |
| F1882 | 06_testing/other | `FlowiseAdapter.configured` | [backend/scinsight/rag_tuning/flowise_adapter.py:30](../backend/scinsight/rag_tuning/flowise_adapter.py#L30) | method | used (framework) |  | F1886 |  |  |
| F1883 | 06_testing/other | `FlowiseAdapter._call` | [backend/scinsight/rag_tuning/flowise_adapter.py:34](../backend/scinsight/rag_tuning/flowise_adapter.py#L34) | method | used |  | F1884, F1889, F1890 |  |  |
| F1884 | 06_testing/other | `FlowiseAdapter.chatflow` | [backend/scinsight/rag_tuning/flowise_adapter.py:46](../backend/scinsight/rag_tuning/flowise_adapter.py#L46) | method | used |  | F1886, F1889, F1890, F1897 |  |  |
| F1885 | 06_testing/other | `FlowiseAdapter._nodes` | [backend/scinsight/rag_tuning/flowise_adapter.py:55](../backend/scinsight/rag_tuning/flowise_adapter.py#L55) | method | used (framework) |  | F1886, F1889 |  |  |
| F1886 | 06_testing/other | `FlowiseAdapter.status` | [backend/scinsight/rag_tuning/flowise_adapter.py:63](../backend/scinsight/rag_tuning/flowise_adapter.py#L63) | method | used (framework) | What the live chatflow RAG DB uses right now, and what its table holds. |  |  |  |
| F1887 | 06_testing/other | `FlowiseAdapter.table_rows` | [backend/scinsight/rag_tuning/flowise_adapter.py:83](../backend/scinsight/rag_tuning/flowise_adapter.py#L83) | method | used (framework) |  | F1886, F1889, F1890 |  |  |
| F1888 | 06_testing/other | `FlowiseAdapter.compatible` | [backend/scinsight/rag_tuning/flowise_adapter.py:92](../backend/scinsight/rag_tuning/flowise_adapter.py#L92) | method | used | Reasons the chatflow RAG DB cannot follow this configuration (empty = it can). | F1895 |  |  |
| F1889 | 06_testing/other | `FlowiseAdapter.sync` | [backend/scinsight/rag_tuning/flowise_adapter.py:99](../backend/scinsight/rag_tuning/flowise_adapter.py#L99) | method | used (framework) | Apply chunk size / overlap / top-k and the version tag to the chatflow, re-index it and ve |  |  |  |
| F1890 | 06_testing/other | `FlowiseAdapter.restore` | [backend/scinsight/rag_tuning/flowise_adapter.py:124](../backend/scinsight/rag_tuning/flowise_adapter.py#L124) | method | used (framework) |  | F1889 |  |  |
| F1891 | 06_testing/other | `current_docs_sha` | [backend/scinsight/rag_tuning/indexing.py:14](../backend/scinsight/rag_tuning/indexing.py#L14) | function | used | doc_id:version -> sha256 of the source files that an index of this tenant must contain. | F1893 |  |  |
| F1892 | 06_testing/other | `build_candidate_index` | [backend/scinsight/rag_tuning/indexing.py:27](../backend/scinsight/rag_tuning/indexing.py#L27) | function | used | Index the tenant's documents with the configuration's cold settings under a new index vers | F1834, F1837 |  |  |
| F1893 | 06_testing/other | `validate_index` | [backend/scinsight/rag_tuning/indexing.py:61](../backend/scinsight/rag_tuning/indexing.py#L61) | function | used | Complete, single-model, right dimensions, and built from the current documents (not stale) | F1892, F1895 |  |  |
| F1894 | 06_testing/other | `list_indexes` | [backend/scinsight/rag_tuning/indexing.py:86](../backend/scinsight/rag_tuning/indexing.py#L86) | function | used |  | F1826 |  |  |
| F1895 | 06_testing/other | `validate_config` | [backend/scinsight/rag_tuning/publishing.py:14](../backend/scinsight/rag_tuning/publishing.py#L14) | function | used | Every check a configuration must pass before it can become active. | F1843, F1898, F1899 |  |  |
| F1896 | 06_testing/other | `validate_config.check` | [backend/scinsight/rag_tuning/publishing.py:21](../backend/scinsight/rag_tuning/publishing.py#L21) | nested | used |  | F1895 |  |  |
| F1897 | 06_testing/other | `_activate` | [backend/scinsight/rag_tuning/publishing.py:53](../backend/scinsight/rag_tuning/publishing.py#L53) | function | used |  | F1898, F1899 |  |  |
| F1898 | 06_testing/other | `publish_rag_config` | [backend/scinsight/rag_tuning/publishing.py:78](../backend/scinsight/rag_tuning/publishing.py#L78) | function | used |  | F1844 |  |  |
| F1899 | 06_testing/other | `rollback_rag_config` | [backend/scinsight/rag_tuning/publishing.py:87](../backend/scinsight/rag_tuning/publishing.py#L87) | function | used | Re-activate a version that was published before (its index is kept); refused if that index | F1845 |  |  |
| F1900 | 06_testing/other | `_id` | [backend/scinsight/rag_tuning/registry.py:13](../backend/scinsight/rag_tuning/registry.py#L13) | function | used |  | F1904, F1908, F1910, F1913 |  |  |
| F1901 | 06_testing/other | `_row` | [backend/scinsight/rag_tuning/registry.py:17](../backend/scinsight/rag_tuning/registry.py#L17) | function | used |  | F1905, F1906, F1907 |  |  |
| F1902 | 06_testing/other | `Registry` | [backend/scinsight/rag_tuning/registry.py:28](../backend/scinsight/rag_tuning/registry.py#L28) | class | used |  | F1819 |  |  |
| F1903 | 06_testing/other | `Registry.__init__` | [backend/scinsight/rag_tuning/registry.py:29](../backend/scinsight/rag_tuning/registry.py#L29) | method | used (framework) |  |  |  |  |
| F1904 | 06_testing/other | `Registry.ensure_baseline` | [backend/scinsight/rag_tuning/registry.py:33](../backend/scinsight/rag_tuning/registry.py#L33) | method | used |  | F1905, F1907 |  |  |
| F1905 | 06_testing/other | `Registry.get_active_rag_config` | [backend/scinsight/rag_tuning/registry.py:41](../backend/scinsight/rag_tuning/registry.py#L41) | method | used |  | F1824, F1827, F1839, F1892, F1895, F1897, F1908 |  |  |
| F1906 | 06_testing/other | `Registry.get` | [backend/scinsight/rag_tuning/registry.py:45](../backend/scinsight/rag_tuning/registry.py#L45) | method | used |  | F1908 |  |  |
| F1907 | 06_testing/other | `Registry.history` | [backend/scinsight/rag_tuning/registry.py:51](../backend/scinsight/rag_tuning/registry.py#L51) | method | used (framework) |  |  |  |  |
| F1908 | 06_testing/other | `Registry.save_draft_config` | [backend/scinsight/rag_tuning/registry.py:55](../backend/scinsight/rag_tuning/registry.py#L55) | method | used | Store a validated draft and say how it differs from the active configuration (and whether  | F1825, F1839 |  |  |
| F1909 | 06_testing/other | `Registry.set_status` | [backend/scinsight/rag_tuning/registry.py:66](../backend/scinsight/rag_tuning/registry.py#L66) | method | used |  | F1892, F1895 |  |  |
| F1910 | 06_testing/other | `Registry.start_job` | [backend/scinsight/rag_tuning/registry.py:72](../backend/scinsight/rag_tuning/registry.py#L72) | method | used | Run fn() in a background thread (HTTP returns at once; the console polls the job). | F1823 |  |  |
| F1911 | 06_testing/other | `Registry.start_job.run` | [backend/scinsight/rag_tuning/registry.py:78](../backend/scinsight/rag_tuning/registry.py#L78) | nested | used |  | F1910, F1910 |  |  |
| F1912 | 06_testing/other | `Registry.job` | [backend/scinsight/rag_tuning/registry.py:92](../backend/scinsight/rag_tuning/registry.py#L92) | method | used |  | F1910 |  |  |
| F1913 | 06_testing/other | `Registry.save_experiment` | [backend/scinsight/rag_tuning/registry.py:99](../backend/scinsight/rag_tuning/registry.py#L99) | method | used |  | F1837 |  |  |
| F1914 | 06_testing/other | `Registry.experiments` | [backend/scinsight/rag_tuning/registry.py:105](../backend/scinsight/rag_tuning/registry.py#L105) | method | used |  | F1839, F1840, F1895 |  |  |
| F1915 | 06_testing/other | `Registry.experiment` | [backend/scinsight/rag_tuning/registry.py:110](../backend/scinsight/rag_tuning/registry.py#L110) | method | used |  | F1841, F1842 |  |  |
| F1916 | 06_testing/other | `terms` | [backend/scinsight/rag_tuning/retrieval.py:19](../backend/scinsight/rag_tuning/retrieval.py#L19) | function | used |  | F1917, F1918 |  |  |
| F1917 | 06_testing/other | `keyword_score` | [backend/scinsight/rag_tuning/retrieval.py:23](../backend/scinsight/rag_tuning/retrieval.py#L23) | function | used |  | F1918 |  |  |
| F1918 | 06_testing/other | `rank` | [backend/scinsight/rag_tuning/retrieval.py:32](../backend/scinsight/rag_tuning/retrieval.py#L32) | function | used | Score and order chunk rows; returns copies with semantic / keyword / rerank / score fields | F0766 |  |  |
| F1919 | 06_testing/other | `env` | [scripts/rag_tuning.py:35](../scripts/rag_tuning.py#L35) | function | used |  | F1925 |  |  |
| F1920 | 06_testing/other | `Client` | [scripts/rag_tuning.py:40](../scripts/rag_tuning.py#L40) | class | used |  | F1925, F1926 |  |  |
| F1921 | 06_testing/other | `Client.__init__` | [scripts/rag_tuning.py:41](../scripts/rag_tuning.py#L41) | method | used (framework) |  |  |  |  |
| F1922 | 06_testing/other | `Client.call` | [scripts/rag_tuning.py:44](../scripts/rag_tuning.py#L44) | method | used (framework) |  | F1923 |  |  |
| F1923 | 06_testing/other | `Client.job` | [scripts/rag_tuning.py:53](../scripts/rag_tuning.py#L53) | method | used (framework) |  |  |  |  |
| F1924 | 06_testing/other | `show` | [scripts/rag_tuning.py:63](../scripts/rag_tuning.py#L63) | function | used |  | F1925, F1926 |  |  |
| F1925 | 06_testing/other | `main` | [scripts/rag_tuning.py:67](../scripts/rag_tuning.py#L67) | function | used |  |  |  |  |
| F1926 | 06_testing/other | `verify` | [scripts/rag_tuning.py:162](../scripts/rag_tuning.py#L162) | function | used | End to end: ask the live Flowise chatflow, then check which configuration answered on both | F1925 |  |  |
| F1927 | 06_testing/unit_tests | `kdir` | [tests/scinsight/test_rag_tuning.py:22](../tests/scinsight/test_rag_tuning.py#L22) | function | used |  | F1928, F1935, F1948 |  |  |
| F1928 | 06_testing/unit_tests | `client` | [tests/scinsight/test_rag_tuning.py:29](../tests/scinsight/test_rag_tuning.py#L29) | function | used |  | F1929, F1930, F1932, F1934, F1935, F1936, F1937, F1938, F1939, F1942, F1943, F19 |  |  |
| F1929 | 06_testing/unit_tests | `draft` | [tests/scinsight/test_rag_tuning.py:34](../tests/scinsight/test_rag_tuning.py#L34) | function | used |  | F1937, F1944, F1945, F1947, F1948 |  |  |
| F1930 | 06_testing/unit_tests | `run_job` | [tests/scinsight/test_rag_tuning.py:40](../tests/scinsight/test_rag_tuning.py#L40) | function | used |  | F1936, F1937, F1942, F1944, F1948 |  |  |
| F1931 | 06_testing/unit_tests | `test_config_validation_rejects_overlap_not_smaller_than_size_and_negative_overlap` | [tests/scinsight/test_rag_tuning.py:47](../tests/scinsight/test_rag_tuning.py#L47) | test | test |  |  |  |  |
| F1932 | 06_testing/unit_tests | `test_only_admins_see_the_console_and_tenant_comes_from_the_key` | [tests/scinsight/test_rag_tuning.py:58](../tests/scinsight/test_rag_tuning.py#L58) | test | test |  |  |  |  |
| F1933 | 06_testing/unit_tests | `test_chunk_preview_sizes_overlap_and_clause_boundaries` | [tests/scinsight/test_rag_tuning.py:67](../tests/scinsight/test_rag_tuning.py#L67) | test | test |  |  |  |  |
| F1934 | 06_testing/unit_tests | `test_chunk_preview_endpoint_compares_without_writing` | [tests/scinsight/test_rag_tuning.py:79](../tests/scinsight/test_rag_tuning.py#L79) | test | test |  |  |  |  |
| F1935 | 06_testing/unit_tests | `test_metadata_checks_report_missing_expired_and_superseded_without_inventing` | [tests/scinsight/test_rag_tuning.py:90](../tests/scinsight/test_rag_tuning.py#L90) | test | test |  |  |  |  |
| F1936 | 06_testing/unit_tests | `test_embedding_models_are_an_approved_list_and_dimensions_are_checked` | [tests/scinsight/test_rag_tuning.py:108](../tests/scinsight/test_rag_tuning.py#L108) | test | test |  |  |  |  |
| F1937 | 06_testing/unit_tests | `test_candidate_index_is_separate_and_active_search_is_unchanged` | [tests/scinsight/test_rag_tuning.py:116](../tests/scinsight/test_rag_tuning.py#L116) | test | test |  |  |  |  |
| F1938 | 06_testing/unit_tests | `test_top_k_threshold_and_access_control_in_retrieval_preview` | [tests/scinsight/test_rag_tuning.py:128](../tests/scinsight/test_rag_tuning.py#L128) | test | test |  |  |  |  |
| F1939 | 06_testing/unit_tests | `test_unauthorized_tenant_never_sees_other_documents` | [tests/scinsight/test_rag_tuning.py:142](../tests/scinsight/test_rag_tuning.py#L142) | test | test |  |  |  |  |
| F1940 | 06_testing/unit_tests | `test_metrics_definitions_hit_recall_precision_mrr_and_leakage` | [tests/scinsight/test_rag_tuning.py:150](../tests/scinsight/test_rag_tuning.py#L150) | test | test |  |  |  |  |
| F1941 | 06_testing/unit_tests | `test_answer_checks_catch_wrong_citations_and_unsupported_numbers` | [tests/scinsight/test_rag_tuning.py:159](../tests/scinsight/test_rag_tuning.py#L159) | test | test |  |  |  |  |
| F1942 | 06_testing/unit_tests | `test_benchmark_runs_the_real_search_and_is_reproducible` | [tests/scinsight/test_rag_tuning.py:168](../tests/scinsight/test_rag_tuning.py#L168) | test | test |  |  |  |  |
| F1943 | 06_testing/unit_tests | `test_grid_shows_workload_before_running` | [tests/scinsight/test_rag_tuning.py:179](../tests/scinsight/test_rag_tuning.py#L179) | test | test |  |  |  |  |
| F1944 | 06_testing/unit_tests | `test_publish_needs_director_benchmark_and_confirm_then_rollback` | [tests/scinsight/test_rag_tuning.py:185](../tests/scinsight/test_rag_tuning.py#L185) | test | test |  |  |  |  |
| F1945 | 06_testing/unit_tests | `test_candidate_index_failure_keeps_the_active_configuration` | [tests/scinsight/test_rag_tuning.py:204](../tests/scinsight/test_rag_tuning.py#L204) | test | test |  |  |  |  |
| F1946 | 06_testing/unit_tests | `test_candidate_index_failure_keeps_the_active_configuration.boom` | [tests/scinsight/test_rag_tuning.py:208](../tests/scinsight/test_rag_tuning.py#L208) | nested | used |  | F1945 |  |  |
| F1947 | 06_testing/unit_tests | `test_rollback_only_to_previously_published_versions` | [tests/scinsight/test_rag_tuning.py:218](../tests/scinsight/test_rag_tuning.py#L218) | test | test |  |  |  |  |
| F1948 | 06_testing/unit_tests | `test_stale_index_is_detected_when_documents_change` | [tests/scinsight/test_rag_tuning.py:224](../tests/scinsight/test_rag_tuning.py#L224) | test | test |  |  |  |  |
| F1950 | 01_fastapi/endpoints | `create_app.code_files` | [backend/app/main.py:604](../backend/app/main.py#L604) | route | used |  | F1991 | GET /api/v1/code/files |  |
| F1951 | 01_fastapi/endpoints | `create_app.code_file` | [backend/app/main.py:610](../backend/app/main.py#L610) | route | used |  |  | GET /api/v1/code/file |  |
| F1952 | 06_testing/other | `CodeEditor.files` | [backend/app/code_editor.py:107](../backend/app/code_editor.py#L107) | method | used | Every backend file with the apps that load it; the page shows a file's full source and lin | F1950 |  |  |
| F1953 | 06_testing/other | `CodeEditor.file` | [backend/app/code_editor.py:136](../backend/app/code_editor.py#L136) | method | used |  | F1951 |  |  |
| F1954 | 06_testing/unit_tests | `test_rag_tuning_proxy_is_open_to_every_role_but_publish_needs_a_manager` | [tests/test_code_editor.py:49](../tests/test_code_editor.py#L49) | test | test |  |  |  |  |
| F1955 | 01_fastapi/endpoints | `create_app.code_template` | [backend/app/main.py:618](../backend/app/main.py#L618) | route | used |  | F1991 | GET /api/v1/code/template |  |
| F1956 | 06_testing/other | `CodeEditor.template` | [backend/app/code_editor.py:124](../backend/app/code_editor.py#L124) | method | used | One starter template by file name (only the names the apps list; no path from the browser  | F1955 |  |  |
| F1957 | 06_testing/other | `TemplateSettings` | [templates/backend/fastapi_app.py:23](../templates/backend/fastapi_app.py#L23) | pydantic_model | used |  | F1960, F1960 |  |  |
| F1958 | 06_testing/other | `Principal` | [templates/backend/fastapi_app.py:30](../templates/backend/fastapi_app.py#L30) | class | used |  | F1961, F1961, F1962, F1963, F1965, F1966, F1967, F1968 |  |  |
| F1959 | 06_testing/other | `ItemRequest` | [templates/backend/fastapi_app.py:37](../templates/backend/fastapi_app.py#L37) | pydantic_model | used | Request body: validated before the route runs (422 otherwise). | F1966, F1966 |  |  |
| F1960 | 06_testing/other | `create_app` | [templates/backend/fastapi_app.py:43](../templates/backend/fastapi_app.py#L43) | function | used |  |  |  |  |
| F1961 | 06_testing/other | `create_app.principal` | [templates/backend/fastapi_app.py:52](../templates/backend/fastapi_app.py#L52) | nested | used |  | F1962, F1962, F1963, F1963, F1967, F1967 |  |  |
| F1962 | 06_testing/other | `create_app.reader` | [templates/backend/fastapi_app.py:58](../templates/backend/fastapi_app.py#L58) | nested | used |  | F1965, F1965 |  |  |
| F1963 | 06_testing/other | `create_app.manager` | [templates/backend/fastapi_app.py:61](../templates/backend/fastapi_app.py#L61) | nested | used |  | F1966, F1966, F1968, F1968 |  |  |
| F1964 | 06_testing/other | `create_app.health` | [templates/backend/fastapi_app.py:67](../templates/backend/fastapi_app.py#L67) | route | used |  |  | GET /health |  |
| F1965 | 06_testing/other | `create_app.get_stock` | [templates/backend/fastapi_app.py:71](../templates/backend/fastapi_app.py#L71) | route | used |  | F2028, F2031, F1988 | GET /api/v1/stock/{sku} |  |
| F1966 | 06_testing/other | `create_app.adjust` | [templates/backend/fastapi_app.py:78](../templates/backend/fastapi_app.py#L78) | route | used |  | F1988 | POST /api/v1/adjustments |  |
| F1967 | 06_testing/other | `create_app.sap_read_only` | [templates/backend/fastapi_app.py:84](../templates/backend/fastapi_app.py#L84) | route | used |  | F0017, F0100, F1993, F2000, F2001, F2002, F2003, F2004, F2005, F2006, F0669, F06 | POST/PUT/PATCH/DELETE /api/v1/sap/{path:path} |  |
| F1968 | 06_testing/other | `create_app.read_audit` | [templates/backend/fastapi_app.py:88](../templates/backend/fastapi_app.py#L88) | route | used |  | F0017, F0101, F1993, F2027, F0901, F1944, F0848, F0862, F0865, F0874, F0878, F19 | GET /api/v1/audit |  |
| F1972 | 06_testing/other | `State` | [templates/backend/langgraph_graph.py:19](../templates/backend/langgraph_graph.py#L19) | class | used |  | F1973, F1974, F1975, F1976, F1977, F1978 |  |  |
| F1973 | 06_testing/other | `understand` | [templates/backend/langgraph_graph.py:27](../templates/backend/langgraph_graph.py#L27) | function | used |  | F1978 |  |  |
| F1974 | 06_testing/other | `calculate` | [templates/backend/langgraph_graph.py:33](../templates/backend/langgraph_graph.py#L33) | function | used |  | F1978 |  |  |
| F1975 | 06_testing/other | `approval` | [templates/backend/langgraph_graph.py:38](../templates/backend/langgraph_graph.py#L38) | function | used |  | F1978 |  |  |
| F1976 | 06_testing/other | `answer` | [templates/backend/langgraph_graph.py:44](../templates/backend/langgraph_graph.py#L44) | function | used |  | F1978 |  |  |
| F1977 | 06_testing/other | `route_after_understand` | [templates/backend/langgraph_graph.py:50](../templates/backend/langgraph_graph.py#L50) | function | used |  | F1978 |  |  |
| F1978 | 06_testing/other | `build_graph` | [templates/backend/langgraph_graph.py:54](../templates/backend/langgraph_graph.py#L54) | function | used |  |  |  |  |
| F1979 | 06_testing/other | `stock_level` | [templates/backend/mcp_server.py:24](../templates/backend/mcp_server.py#L24) | function | used | Current on-hand quantity of one SKU (read-only). |  |  |  |
| F1980 | 06_testing/other | `low_stock` | [templates/backend/mcp_server.py:32](../templates/backend/mcp_server.py#L32) | function | used | SKUs whose on-hand quantity is below the threshold (read-only). |  |  |  |
| F1981 | 06_testing/other | `ApiKeyMiddleware` | [templates/backend/mcp_server.py:38](../templates/backend/mcp_server.py#L38) | class | used | Bearer or X-API-Key check on /mcp; keys come from TPL_MCP_KEYS (comma separated). | F1984 |  |  |
| F1982 | 06_testing/other | `ApiKeyMiddleware.__init__` | [templates/backend/mcp_server.py:41](../templates/backend/mcp_server.py#L41) | method | used (framework) |  |  |  |  |
| F1983 | 06_testing/other | `ApiKeyMiddleware.dispatch` | [templates/backend/mcp_server.py:45](../templates/backend/mcp_server.py#L45) | method | used (framework) |  |  |  |  |
| F1984 | 06_testing/other | `create_mcp_app` | [templates/backend/mcp_server.py:54](../templates/backend/mcp_server.py#L54) | function | used |  |  |  |  |
| F1985 | 06_testing/unit_tests | `fused` | [tests/test_fused_app.py:15](../tests/test_fused_app.py#L15) | function | used |  | F2035, F2036 |  |  |
| F1988 | 06_testing/unit_tests | `test_fastapi_template_auth_roles_validation_and_read_only_sap` | [tests/test_templates.py:11](../tests/test_templates.py#L11) | test | test |  |  |  |  |
| F1990 | 06_testing/unit_tests | `test_langgraph_template_interrupts_for_approval_then_resumes` | [tests/test_templates.py:32](../tests/test_templates.py#L32) | test | test |  |  |  |  |
| F1991 | 06_testing/unit_tests | `test_backend_code_page_serves_each_apps_templates_and_nothing_else` | [tests/test_templates.py:42](../tests/test_templates.py#L42) | test | test |  |  |  |  |
| F1992 | 06_testing/unit_tests | `test_mcp_template_tools_are_read_only_and_the_endpoint_needs_a_key` | [tests/test_templates.py:53](../tests/test_templates.py#L53) | test | test |  |  |  |  |
| F1993 | 01_fastapi/endpoints | `create_router` | [backend/scinsight/app.py:37](../backend/scinsight/app.py#L37) | function | used | Database, fixtures, security, RAG and every SCInsight route; backend/app/main.py includes  | F0017, F2034, F1985 |  |  |
| F1994 | 01_fastapi/endpoints | `create_router.principal` | [backend/scinsight/app.py:61](../backend/scinsight/app.py#L61) | nested | used |  | F1993, F1995, F1995, F2006, F2006, F2019, F2019, F2021, F2021, F2022, F2022, F20 |  |  |
| F1995 | 01_fastapi/endpoints | `create_router.reader` | [backend/scinsight/app.py:66](../backend/scinsight/app.py#L66) | nested | used |  | F1998, F1998, F1999, F1999, F2000, F2000, F2001, F2001, F2002, F2002, F2003, F20 |  |  |
| F1996 | 01_fastapi/endpoints | `create_router.biz_date` | [backend/scinsight/app.py:70](../backend/scinsight/app.py#L70) | nested | used |  | F1993, F2014 |  |  |
| F1997 | 01_fastapi/endpoints | `create_router.health` | [backend/scinsight/app.py:73](../backend/scinsight/app.py#L73) | route | used |  |  | GET /health |  |
| F1998 | 01_fastapi/endpoints | `create_router.context` | [backend/scinsight/app.py:79](../backend/scinsight/app.py#L79) | route | used |  |  | GET /api/v1/context |  |
| F1999 | 01_fastapi/endpoints | `create_router.validate_context` | [backend/scinsight/app.py:85](../backend/scinsight/app.py#L85) | route | used |  | F0656 | POST /api/v1/context/validate | Decision-Outcome-Learning-Agentflow · 2 · Check access, Factory-Planning-Agentflow · 2 · Check access, Inventory-Optimiz |
| F2000 | 01_fastapi/endpoints | `create_router.sap_inventory` | [backend/scinsight/app.py:94](../backend/scinsight/app.py#L94) | route | used |  | F0845, F0849, F0853 | GET /api/v1/sap/inventory | Flowise Custom Tool · get_sap_inventory |
| F2001 | 01_fastapi/endpoints | `create_router.sap_bom` | [backend/scinsight/app.py:99](../backend/scinsight/app.py#L99) | route | used |  |  | GET /api/v1/sap/bom/{sku} | Flowise Custom Tool · get_material_bom |
| F2002 | 01_fastapi/endpoints | `create_router.sap_production_orders` | [backend/scinsight/app.py:103](../backend/scinsight/app.py#L103) | route | used |  | F0669 | GET /api/v1/sap/production-orders | Flowise Custom Tool · get_production_orders, Factory-Planning-Agentflow · 4 · Calculate with SAP data |
| F2003 | 01_fastapi/endpoints | `create_router.sap_purchase_orders` | [backend/scinsight/app.py:107](../backend/scinsight/app.py#L107) | route | used |  | F0841, F0850, F1988 | GET /api/v1/sap/purchase-orders | Flowise Custom Tool · get_open_purchase_orders |
| F2004 | 01_fastapi/endpoints | `create_router.sap_warehouses` | [backend/scinsight/app.py:112](../backend/scinsight/app.py#L112) | route | used |  | F0846, F0848 | GET /api/v1/sap/warehouses |  |
| F2005 | 01_fastapi/endpoints | `create_router.sap_suppliers` | [backend/scinsight/app.py:116](../backend/scinsight/app.py#L116) | route | used |  | F0670 | GET /api/v1/sap/suppliers | Procurement-Agentflow · 4 · Calculate with SAP data |
| F2006 | 01_fastapi/endpoints | `create_router.sap_write_blocked` | [backend/scinsight/app.py:120](../backend/scinsight/app.py#L120) | route | used |  | F0017, F0100, F0669, F0670, F1960, F1967, F0841, F0845, F0846, F0848, F0849, F08 | POST/PUT/PATCH/DELETE /api/v1/sap/{path:path} |  |
| F2007 | 01_fastapi/endpoints | `create_router.material_readiness` | [backend/scinsight/app.py:126](../backend/scinsight/app.py#L126) | route | used |  | F0669, F0834, F0835, F0839, F0852, F0854, F0855 | POST /api/v1/optimizer/material-readiness | Flowise Custom Tool · check_material_readiness, Factory-Planning-Agentflow · 4 · Calculate with SAP data |
| F2008 | 01_fastapi/endpoints | `create_router.warehouse_balancing` | [backend/scinsight/app.py:130](../backend/scinsight/app.py#L130) | route | used |  | F0671, F0836, F0838, F0855, F0857, F0860 | POST /api/v1/optimizer/warehouse-balancing | Flowise Custom Tool · optimize_warehouse_transfer, Logistics-Agentflow · 4 · Calculate with SAP data, Warehouse-Agentflo |
| F2009 | 01_fastapi/endpoints | `create_router.replenishment` | [backend/scinsight/app.py:134](../backend/scinsight/app.py#L134) | route | used |  | F0670, F0674, F0841 | POST /api/v1/optimizer/replenishment | Flowise Custom Tool · calculate_stock_cover, Inventory-Optimizer-Agentflow · 4 · Calculate with SAP data, Procurement-Ag |
| F2010 | 01_fastapi/endpoints | `create_router.forecast_demand` | [backend/scinsight/app.py:138](../backend/scinsight/app.py#L138) | route | used |  | F0674, F0843, F0855, F0856 | POST /api/v1/forecast/demand | Flowise Custom Tool · forecast_demand, Inventory-Optimizer-Agentflow · 4 · Calculate with SAP data |
| F2011 | 01_fastapi/endpoints | `create_router.forecast_lead_time` | [backend/scinsight/app.py:142](../backend/scinsight/app.py#L142) | route | used |  | F0670, F0842 | POST /api/v1/forecast/lead-time | Flowise Custom Tool · get_supplier_reliability, Procurement-Agentflow · 4 · Calculate with SAP data |
| F2012 | 01_fastapi/endpoints | `create_router.quality_check` | [backend/scinsight/app.py:146](../backend/scinsight/app.py#L146) | route | used |  | F0675, F0837 | POST /api/v1/quality/check-stock | Flowise Custom Tool · check_batch_quality, Quality-Agentflow · 4 · Calculate with SAP data |
| F2013 | 01_fastapi/endpoints | `create_router.calculation` | [backend/scinsight/app.py:150](../backend/scinsight/app.py#L150) | route | used |  | F0683, F0519, F0790, F0808 | GET /api/v1/calculations/{calculation_id} |  |
| F2014 | 01_fastapi/endpoints | `create_router.rag_search` | [backend/scinsight/app.py:155](../backend/scinsight/app.py#L155) | route | used |  | F0481, F0017, F0076, F0077, F0629, F0678, F0890, F0844, F1937, F1939, F1944, F08 | POST /api/v1/rag/search | Flowise Custom Tool · search_supply_chain_policy, Factory-Planning-Agentflow · 5 · Policy search (RAG), Inventory-Optimi |
| F2015 | 01_fastapi/endpoints | `create_router.rag_documents` | [backend/scinsight/app.py:161](../backend/scinsight/app.py#L161) | route | used |  | F0017, F0081, F0868 | GET /api/v1/rag/documents |  |
| F2016 | 01_fastapi/endpoints | `create_router.create_decision` | [backend/scinsight/app.py:170](../backend/scinsight/app.py#L170) | route | used |  | F0683, F0838, F0839, F0841, F0855, F0856, F0857, F0860 | POST /api/v1/decisions | Flowise Custom Tool · save_recommendation, Supervisor-Agentflow · 7 · Save recommendation |
| F2017 | 01_fastapi/endpoints | `create_router.list_decisions` | [backend/scinsight/app.py:175](../backend/scinsight/app.py#L175) | route | used |  | F0683, F0838, F0839, F0841, F0855, F0856, F0857, F0860 | GET /api/v1/decisions |  |
| F2018 | 01_fastapi/endpoints | `create_router.get_decision` | [backend/scinsight/app.py:179](../backend/scinsight/app.py#L179) | route | used |  | F0676, F0684, F0685, F0520, F0838, F0839, F0841, F0797, F0798, F0799, F0800, F08 | GET /api/v1/decisions/{rec_id} | Flowise Custom Tool · get_decision_status |
| F2019 | 01_fastapi/endpoints | `create_router.review` | [backend/scinsight/app.py:183](../backend/scinsight/app.py#L183) | route | used |  | F0676, F0684, F0685, F0520, F0838, F0839, F0841, F0797, F0798, F0799, F0800, F08 | POST /api/v1/decisions/{rec_id}/review |  |
| F2020 | 01_fastapi/endpoints | `create_router.withdraw` | [backend/scinsight/app.py:187](../backend/scinsight/app.py#L187) | route | used |  | F0676, F0684, F0685, F0520, F0838, F0839, F0841, F0797, F0798, F0799, F0800, F08 | POST /api/v1/decisions/{rec_id}/withdraw | Supervisor-Agentflow · 10 · Withdraw |
| F2021 | 01_fastapi/endpoints | `create_router.sap_execution` | [backend/scinsight/app.py:191](../backend/scinsight/app.py#L191) | route | used |  | F0676, F0684, F0685, F0520, F0838, F0839, F0841, F0797, F0798, F0799, F0800, F08 | POST /api/v1/decisions/{rec_id}/sap-execution |  |
| F2022 | 01_fastapi/endpoints | `create_router.reconcile` | [backend/scinsight/app.py:196](../backend/scinsight/app.py#L196) | route | used |  | F0676, F0840, F0841, F0842, F0858, F0859 | POST /api/v1/outcomes/reconcile | Decision-Outcome-Learning-Agentflow · 3 · Check the outcome with SAP data |
| F2023 | 01_fastapi/endpoints | `create_router.learning_metrics` | [backend/scinsight/app.py:200](../backend/scinsight/app.py#L200) | route | used |  | F0676, F0840, F0843, F0801 | GET /api/v1/learning/metrics | Flowise Custom Tool · get_verified_outcomes, Decision-Outcome-Learning-Agentflow · 3 · Check the outcome with SAP data |
| F2024 | 01_fastapi/endpoints | `create_router.train` | [backend/scinsight/app.py:204](../backend/scinsight/app.py#L204) | route | used |  | F0840 | POST /api/v1/learning/train-lead-time-model |  |
| F2025 | 01_fastapi/endpoints | `create_router.promote` | [backend/scinsight/app.py:211](../backend/scinsight/app.py#L211) | route | used |  | F0840 | POST /api/v1/learning/models/{model_id}/promote |  |
| F2026 | 01_fastapi/endpoints | `create_router.retraining` | [backend/scinsight/app.py:218](../backend/scinsight/app.py#L218) | route | used |  | F0840 | POST /api/v1/learning/retraining-requests |  |
| F2027 | 01_fastapi/endpoints | `create_router.audit` | [backend/scinsight/app.py:224](../backend/scinsight/app.py#L224) | route | used |  | F0017, F0101, F0901, F1960, F1968, F1944, F0848, F0862, F0865, F0874, F0878, F19 | GET /api/v1/audit |  |
| F2028 | 06_testing/other | `create_inner_router` | [templates/backend/fastapi_router.py:18](../templates/backend/fastapi_router.py#L18) | function | used | A module's routes and its shared objects (router.state), like backend/scinsight/app.py:cre | F2032 |  |  |
| F2029 | 06_testing/other | `create_inner_router.caller` | [templates/backend/fastapi_router.py:24](../templates/backend/fastapi_router.py#L24) | nested | used |  | F2031, F2031 |  |  |
| F2030 | 06_testing/other | `create_inner_router.health` | [templates/backend/fastapi_router.py:29](../templates/backend/fastapi_router.py#L29) | route | used |  |  | GET /health |  |
| F2031 | 06_testing/other | `create_inner_router.get_stock` | [templates/backend/fastapi_router.py:33](../templates/backend/fastapi_router.py#L33) | route | used |  | F1960, F1965, F1988 | GET /api/v1/stock/{sku} |  |
| F2032 | 06_testing/other | `create_app` | [templates/backend/fastapi_router.py:42](../templates/backend/fastapi_router.py#L42) | function | used |  |  |  |  |
| F2033 | 06_testing/other | `create_app.health` | [templates/backend/fastapi_router.py:47](../templates/backend/fastapi_router.py#L47) | route | used |  |  | GET /health |  |
| F2034 | 06_testing/unit_tests | `create_app` | [tests/scinsight/conftest.py:12](../tests/scinsight/conftest.py#L12) | function | used | Test harness only: the SCInsight router on a bare app (in production it lives in backend/a | F0909 |  |  |
| F2035 | 06_testing/unit_tests | `test_one_fastapi_instance_serves_both_apis_with_their_own_auth` | [tests/test_fused_app.py:21](../tests/test_fused_app.py#L21) | test | test |  |  |  |  |
| F2036 | 06_testing/unit_tests | `test_rag_tuning_page_reaches_the_scinsight_routes_in_process` | [tests/test_fused_app.py:35](../tests/test_fused_app.py#L35) | test | test |  |  |  |  |
| F2037 | 06_testing/unit_tests | `test_router_template_is_one_app_with_a_prefixed_module` | [tests/test_templates.py:23](../tests/test_templates.py#L23) | test | test |  |  |  |  |
| F2038 | 01_fastapi/endpoints | `create_app.erp_audit` | [backend/app/main.py:771](../backend/app/main.py#L771) | nested | used |  | F0017 |  |  |
| F2039 | 03_sap_data/repositories | `TenantRegistry._build` | [backend/app/tenants.py:60](../backend/app/tenants.py#L60) | method | used |  | F0393, F2040 |  |  |
| F2040 | 03_sap_data/repositories | `TenantRegistry.use_snapshot` | [backend/app/tenants.py:77](../backend/app/tenants.py#L77) | method | used (framework) | Switch one customer to another validated snapshot file (None = its built-in snapshot): ERP | F2162, F2163, F2165 |  |  |
| F2041 | 06_testing/other | `_r` | [backend/app/erp/checks.py:25](../backend/app/erp/checks.py#L25) | function | used |  | F2042, F2045, F2046, F2047, F2048, F2049, F2050, F2051, F2052, F2053, F2054 |  |  |
| F2042 | 06_testing/other | `_guard` | [backend/app/erp/checks.py:29](../backend/app/erp/checks.py#L29) | function | used |  | F2044 |  |  |
| F2043 | 06_testing/other | `_analyses_since` | [backend/app/erp/checks.py:36](../backend/app/erp/checks.py#L36) | function | used |  | F2047, F2048 |  |  |
| F2044 | 06_testing/other | `validate_integrations` | [backend/app/erp/checks.py:40](../backend/app/erp/checks.py#L40) | function | used |  | F2134 |  |  |
| F2045 | 06_testing/other | `validate_integrations.adapter` | [backend/app/erp/checks.py:48](../backend/app/erp/checks.py#L48) | nested | used |  | F2044 |  |  |
| F2046 | 06_testing/other | `validate_integrations.engine` | [backend/app/erp/checks.py:59](../backend/app/erp/checks.py#L59) | nested | used |  | F2044 |  |  |
| F2047 | 06_testing/other | `validate_integrations.flowise` | [backend/app/erp/checks.py:69](../backend/app/erp/checks.py#L69) | nested | used |  | F2044 |  |  |
| F2048 | 06_testing/other | `validate_integrations.langgraph` | [backend/app/erp/checks.py:107](../backend/app/erp/checks.py#L107) | nested | used |  | F2044 |  |  |
| F2049 | 06_testing/other | `validate_integrations.deep_agents` | [backend/app/erp/checks.py:131](../backend/app/erp/checks.py#L131) | nested | used |  | F2044 |  |  |
| F2050 | 06_testing/other | `validate_integrations.rag` | [backend/app/erp/checks.py:139](../backend/app/erp/checks.py#L139) | nested | used |  | F2044 |  |  |
| F2051 | 06_testing/other | `validate_integrations.dashboards` | [backend/app/erp/checks.py:144](../backend/app/erp/checks.py#L144) | nested | used |  | F2044 |  |  |
| F2052 | 06_testing/other | `validate_integrations.outcomes` | [backend/app/erp/checks.py:151](../backend/app/erp/checks.py#L151) | nested | used |  | F2044 |  |  |
| F2053 | 06_testing/other | `validate_integrations.audit` | [backend/app/erp/checks.py:157](../backend/app/erp/checks.py#L157) | nested | used |  | F2044 |  |  |
| F2054 | 06_testing/other | `validate_integrations.scinsight` | [backend/app/erp/checks.py:162](../backend/app/erp/checks.py#L162) | nested | used |  | F2044 |  |  |
| F2055 | 06_testing/other | `_question` | [backend/app/erp/checks.py:174](../backend/app/erp/checks.py#L174) | function | used |  | F2047, F2048 |  |  |
| F2056 | 06_testing/other | `save_check` | [backend/app/erp/checks.py:181](../backend/app/erp/checks.py#L181) | function | used |  | F2134 |  |  |
| F2057 | 06_testing/other | `last_check` | [backend/app/erp/checks.py:186](../backend/app/erp/checks.py#L186) | function | used |  | F2133 |  |  |
| F2058 | 06_testing/other | `ErpError` | [backend/app/erp/connectors.py:39](../backend/app/erp/connectors.py#L39) | class | used | Safe-to-show error (no secrets, no stack). | F2060, F2060, F2074, F2079, F2080, F2081, F2084, F2085, F2086, F2087, F2088, F21 |  |  |
| F2059 | 06_testing/other | `sanitize` | [backend/app/erp/connectors.py:43](../backend/app/erp/connectors.py#L43) | function | used (framework) |  | F2072, F2080, F2084 |  |  |
| F2060 | 06_testing/other | `check_destination` | [backend/app/erp/connectors.py:50](../backend/app/erp/connectors.py#L50) | function | used | SSRF guard: scheme, cloud-metadata and link-local addresses, production allow-list and HTT | F2145, F2149 |  |  |
| F2061 | 06_testing/other | `ErpConnector` | [backend/app/erp/connectors.py:76](../backend/app/erp/connectors.py#L76) | class | used |  | F2149 |  |  |
| F2062 | 06_testing/other | `ErpConnector.get_capabilities` | [backend/app/erp/connectors.py:79](../backend/app/erp/connectors.py#L79) | method | used (framework) |  |  |  |  |
| F2063 | 06_testing/other | `ErpConnector.test_connection` | [backend/app/erp/connectors.py:82](../backend/app/erp/connectors.py#L82) | method | used (framework) |  | F2068 |  |  |
| F2064 | 06_testing/other | `ErpConnector.discover_entities` | [backend/app/erp/connectors.py:85](../backend/app/erp/connectors.py#L85) | method | used (framework) |  |  |  |  |
| F2065 | 06_testing/other | `ErpConnector.read_entity` | [backend/app/erp/connectors.py:88](../backend/app/erp/connectors.py#L88) | method | used (framework) |  |  |  |  |
| F2066 | 06_testing/other | `ErpConnector.validate_mapping` | [backend/app/erp/connectors.py:91](../backend/app/erp/connectors.py#L91) | method | used (framework) |  |  |  |  |
| F2067 | 06_testing/other | `ErpConnector.sync_data` | [backend/app/erp/connectors.py:94](../backend/app/erp/connectors.py#L94) | method | used (framework) |  |  |  |  |
| F2068 | 06_testing/other | `ErpConnector.get_health` | [backend/app/erp/connectors.py:97](../backend/app/erp/connectors.py#L97) | method | used (framework) |  |  |  |  |
| F2069 | 06_testing/other | `MockSapConnector` | [backend/app/erp/connectors.py:102](../backend/app/erp/connectors.py#L102) | class | used | The customer's existing validated SAP snapshot (data/…json): what SPARC used before any ER | F2045, F2149 |  |  |
| F2070 | 06_testing/other | `MockSapConnector.__init__` | [backend/app/erp/connectors.py:106](../backend/app/erp/connectors.py#L106) | method | used (framework) |  |  |  |  |
| F2071 | 06_testing/other | `MockSapConnector.get_capabilities` | [backend/app/erp/connectors.py:109](../backend/app/erp/connectors.py#L109) | method | used (framework) |  |  |  |  |
| F2072 | 06_testing/other | `MockSapConnector.test_connection` | [backend/app/erp/connectors.py:112](../backend/app/erp/connectors.py#L112) | method | used (framework) |  |  |  |  |
| F2073 | 06_testing/other | `MockSapConnector.discover_entities` | [backend/app/erp/connectors.py:121](../backend/app/erp/connectors.py#L121) | method | used (framework) |  |  |  |  |
| F2074 | 06_testing/other | `MockSapConnector.read_entity` | [backend/app/erp/connectors.py:127](../backend/app/erp/connectors.py#L127) | method | used (framework) |  |  |  |  |
| F2075 | 06_testing/other | `MockSapConnector.validate_mapping` | [backend/app/erp/connectors.py:134](../backend/app/erp/connectors.py#L134) | method | used (framework) |  |  |  |  |
| F2076 | 06_testing/other | `MockSapConnector.sync_data` | [backend/app/erp/connectors.py:137](../backend/app/erp/connectors.py#L137) | method | used (framework) |  |  |  |  |
| F2077 | 06_testing/other | `SapODataConnector` | [backend/app/erp/connectors.py:143](../backend/app/erp/connectors.py#L143) | class | used | SAP S/4HANA or ECC (SAP Gateway) through OData. Only GET reaches SAP; pages with $top/$ski | F2045, F2149, F2152 |  |  |
| F2078 | 06_testing/other | `SapODataConnector.__init__` | [backend/app/erp/connectors.py:146](../backend/app/erp/connectors.py#L146) | method | used (framework) |  |  |  |  |
| F2079 | 06_testing/other | `SapODataConnector._auth` | [backend/app/erp/connectors.py:151](../backend/app/erp/connectors.py#L151) | method | used (framework) |  | F2080 |  |  |
| F2080 | 06_testing/other | `SapODataConnector._get` | [backend/app/erp/connectors.py:168](../backend/app/erp/connectors.py#L168) | method | used (framework) |  | F2081, F2084, F2087 |  |  |
| F2081 | 06_testing/other | `SapODataConnector._metadata` | [backend/app/erp/connectors.py:185](../backend/app/erp/connectors.py#L185) | method | used (framework) |  | F2085, F2086 |  |  |
| F2082 | 06_testing/other | `SapODataConnector._services` | [backend/app/erp/connectors.py:191](../backend/app/erp/connectors.py#L191) | method | used (framework) |  | F2084, F2085, F2086 |  |  |
| F2083 | 06_testing/other | `SapODataConnector.get_capabilities` | [backend/app/erp/connectors.py:195](../backend/app/erp/connectors.py#L195) | method | used (framework) |  |  |  |  |
| F2084 | 06_testing/other | `SapODataConnector.test_connection` | [backend/app/erp/connectors.py:198](../backend/app/erp/connectors.py#L198) | method | used (framework) | Authorized GET of $metadata for every service the mapping uses (or the first one): proves  |  |  |  |
| F2085 | 06_testing/other | `SapODataConnector.discover_entities` | [backend/app/erp/connectors.py:219](../backend/app/erp/connectors.py#L219) | method | used (framework) |  |  |  |  |
| F2086 | 06_testing/other | `SapODataConnector.validate_mapping` | [backend/app/erp/connectors.py:229](../backend/app/erp/connectors.py#L229) | method | used (framework) |  |  |  |  |
| F2087 | 06_testing/other | `SapODataConnector._rows` | [backend/app/erp/connectors.py:239](../backend/app/erp/connectors.py#L239) | method | used (framework) |  | F2088, F2089 |  |  |
| F2088 | 06_testing/other | `SapODataConnector.read_entity` | [backend/app/erp/connectors.py:251](../backend/app/erp/connectors.py#L251) | method | used (framework) |  |  |  |  |
| F2089 | 06_testing/other | `SapODataConnector.sync_data` | [backend/app/erp/connectors.py:260](../backend/app/erp/connectors.py#L260) | method | used (framework) | Full read of every enabled section into a copy of the current snapshot. Sections not enabl |  |  |  |
| F2090 | 06_testing/other | `parse_metadata` | [backend/app/erp/connectors.py:298](../backend/app/erp/connectors.py#L298) | function | used (framework) | {entity set: property and navigation-property names} from an OData V2/V4 $metadata documen | F2081 |  |  |
| F2091 | 06_testing/other | `http_hint` | [backend/app/erp/connectors.py:309](../backend/app/erp/connectors.py#L309) | function | used (framework) |  | F2081, F2084, F2087 |  |  |
| F2092 | 06_testing/other | `_odate` | [backend/app/erp/emulator.py:23](../backend/app/erp/emulator.py#L23) | function | used |  | F2095 |  |  |
| F2093 | 06_testing/other | `_num` | [backend/app/erp/emulator.py:30](../backend/app/erp/emulator.py#L30) | function | used |  | F2094 |  |  |
| F2094 | 06_testing/other | `build_entities` | [backend/app/erp/emulator.py:34](../backend/app/erp/emulator.py#L34) | function | used | {service: {entity set: rows}} in SAP shape, from a SPARC snapshot. | F2099, F2174 |  |  |
| F2095 | 06_testing/other | `build_entities.d` | [backend/app/erp/emulator.py:38](../backend/app/erp/emulator.py#L38) | nested | used |  | F2094 |  |  |
| F2096 | 06_testing/other | `metadata_xml` | [backend/app/erp/emulator.py:78](../backend/app/erp/emulator.py#L78) | function | used |  | F2097 |  |  |
| F2097 | 06_testing/other | `respond` | [backend/app/erp/emulator.py:90](../backend/app/erp/emulator.py#L90) | function | used | (status, body, content type) for one request; shared by the FastAPI route and the tests' h | F2099, F2175 |  |  |
| F2098 | 06_testing/other | `router` | [backend/app/erp/emulator.py:122](../backend/app/erp/emulator.py#L122) | function | used |  | F0017 |  |  |
| F2099 | 06_testing/other | `router.odata` | [backend/app/erp/emulator.py:126](../backend/app/erp/emulator.py#L126) | route | used |  | F2047, F2084, F0017, F0036, F0037, F0038, F0039, F0888, F0862, F2181, F2185, F08 | GET /sap/opu/odata/sap/{path:path} |  |
| F2100 | 06_testing/other | `SectionMapping` | [backend/app/erp/mapping.py:51](../backend/app/erp/mapping.py#L51) | pydantic_model | used |  | F2064, F2065, F2066, F2067, F2073, F2074, F2075, F2076, F2082, F2084, F2085, F20 |  |  |
| F2101 | 06_testing/other | `default_mapping` | [backend/app/erp/mapping.py:94](../backend/app/erp/mapping.py#L94) | function | used (framework) |  | F2146 |  |  |
| F2102 | 06_testing/other | `_get` | [backend/app/erp/mapping.py:101](../backend/app/erp/mapping.py#L101) | function | used (framework) |  | F2103 |  |  |
| F2103 | 06_testing/other | `resolve` | [backend/app/erp/mapping.py:113](../backend/app/erp/mapping.py#L113) | function | used (framework) |  | F2105 |  |  |
| F2104 | 06_testing/other | `convert` | [backend/app/erp/mapping.py:124](../backend/app/erp/mapping.py#L124) | function | used (framework) |  | F2105 |  |  |
| F2105 | 06_testing/other | `transform` | [backend/app/erp/mapping.py:138](../backend/app/erp/mapping.py#L138) | function | used (framework) | Map SAP rows to SPARC rows; rows missing a required field are rejected with a reason (neve | F2088, F2089 |  |  |
| F2106 | 06_testing/other | `validate_mapping` | [backend/app/erp/mapping.py:163](../backend/app/erp/mapping.py#L163) | function | used | Problems that block activation. metadata = {entity set: properties + navigation properties | F2086, F2151 |  |  |
| F2107 | 06_testing/other | `ActivateIn` | [backend/app/erp/routes.py:19](../backend/app/erp/routes.py#L19) | pydantic_model | used |  | F2129 |  |  |
| F2108 | 06_testing/other | `PreviewIn` | [backend/app/erp/routes.py:24](../backend/app/erp/routes.py#L24) | pydantic_model | used |  | F2126, F2126 |  |  |
| F2109 | 06_testing/other | `SyncIn` | [backend/app/erp/routes.py:30](../backend/app/erp/routes.py#L30) | pydantic_model | used |  | F2127 |  |  |
| F2110 | 06_testing/other | `ValidateAllIn` | [backend/app/erp/routes.py:35](../backend/app/erp/routes.py#L35) | pydantic_model | used |  | F2134 |  |  |
| F2111 | 06_testing/other | `register` | [backend/app/erp/routes.py:40](../backend/app/erp/routes.py#L40) | function | used |  | F0017 |  |  |
| F2112 | 06_testing/other | `register.tenant` | [backend/app/erp/routes.py:43](../backend/app/erp/routes.py#L43) | nested | used |  | F2114, F2116, F2117, F2118, F2119, F2120, F2121, F2122, F2123, F2124, F2125, F21 |  |  |
| F2113 | 06_testing/other | `register.run` | [backend/app/erp/routes.py:46](../backend/app/erp/routes.py#L46) | nested | used |  | F2117, F2118, F2119, F2120, F2121, F2122, F2123, F2124, F2125, F2126, F2127, F21 |  |  |
| F2114 | 06_testing/other | `register.log` | [backend/app/erp/routes.py:54](../backend/app/erp/routes.py#L54) | nested | used |  | F2117, F2119, F2120, F2122, F2124, F2125, F2126, F2127, F2129, F2130, F2134 |  |  |
| F2115 | 06_testing/other | `register.providers` | [backend/app/erp/routes.py:57](../backend/app/erp/routes.py#L57) | route | used |  |  | GET /api/v1/erp/providers |  |
| F2116 | 06_testing/other | `register.connections` | [backend/app/erp/routes.py:62](../backend/app/erp/routes.py#L62) | route | used |  | F2178, F2180, F2185 | GET /api/v1/erp/connections |  |
| F2117 | 06_testing/other | `register.create` | [backend/app/erp/routes.py:68](../backend/app/erp/routes.py#L68) | route | used |  | F2178, F2180, F2185 | POST /api/v1/erp/connections |  |
| F2118 | 06_testing/other | `register.get` | [backend/app/erp/routes.py:74](../backend/app/erp/routes.py#L74) | route | used |  | F2180, F2181, F2182, F2183, F2184, F2185, F2186, F2187 | GET /api/v1/erp/connections/{conn_id} |  |
| F2119 | 06_testing/other | `register.patch` | [backend/app/erp/routes.py:79](../backend/app/erp/routes.py#L79) | route | used |  | F2180, F2181, F2182, F2183, F2184, F2185, F2186, F2187 | PATCH /api/v1/erp/connections/{conn_id} |  |
| F2120 | 06_testing/other | `register.test` | [backend/app/erp/routes.py:89](../backend/app/erp/routes.py#L89) | route | used |  | F2180, F2181, F2182, F2183, F2184, F2185, F2186, F2187 | POST /api/v1/erp/connections/{conn_id}/test |  |
| F2121 | 06_testing/other | `register.health` | [backend/app/erp/routes.py:95](../backend/app/erp/routes.py#L95) | route | used |  | F2180, F2181, F2182, F2183, F2184, F2185, F2186, F2187 | GET /api/v1/erp/connections/{conn_id}/health |  |
| F2122 | 06_testing/other | `register.entities` | [backend/app/erp/routes.py:100](../backend/app/erp/routes.py#L100) | route | used |  | F2180, F2181, F2182, F2183, F2184, F2185, F2186, F2187 | GET /api/v1/erp/connections/{conn_id}/entities |  |
| F2123 | 06_testing/other | `register.mappings` | [backend/app/erp/routes.py:106](../backend/app/erp/routes.py#L106) | route | used |  | F2180, F2181, F2182, F2183, F2184, F2185, F2186, F2187 | GET /api/v1/erp/connections/{conn_id}/mappings |  |
| F2124 | 06_testing/other | `register.put_mappings` | [backend/app/erp/routes.py:111](../backend/app/erp/routes.py#L111) | route | used |  | F2180, F2181, F2182, F2183, F2184, F2185, F2186, F2187 | PUT /api/v1/erp/connections/{conn_id}/mappings |  |
| F2125 | 06_testing/other | `register.validate` | [backend/app/erp/routes.py:117](../backend/app/erp/routes.py#L117) | route | used |  | F2180, F2181, F2182, F2183, F2184, F2185, F2186, F2187 | POST /api/v1/erp/connections/{conn_id}/validate |  |
| F2126 | 06_testing/other | `register.preview` | [backend/app/erp/routes.py:123](../backend/app/erp/routes.py#L123) | route | used |  | F2180, F2181, F2182, F2183, F2184, F2185, F2186, F2187 | POST /api/v1/erp/connections/{conn_id}/preview |  |
| F2127 | 06_testing/other | `register.sync` | [backend/app/erp/routes.py:129](../backend/app/erp/routes.py#L129) | route | used |  | F2180, F2181, F2182, F2183, F2184, F2185, F2186, F2187 | POST /api/v1/erp/connections/{conn_id}/sync |  |
| F2128 | 06_testing/other | `register.sync_history` | [backend/app/erp/routes.py:137](../backend/app/erp/routes.py#L137) | route | used |  | F2180, F2181, F2182, F2183, F2184, F2185, F2186, F2187 | GET /api/v1/erp/connections/{conn_id}/sync-history |  |
| F2129 | 06_testing/other | `register.activate` | [backend/app/erp/routes.py:142](../backend/app/erp/routes.py#L142) | route | used |  | F2180, F2181, F2182, F2183, F2184, F2185, F2186, F2187 | POST /api/v1/erp/connections/{conn_id}/activate |  |
| F2130 | 06_testing/other | `register.rollback` | [backend/app/erp/routes.py:153](../backend/app/erp/routes.py#L153) | route | used |  | F2180, F2181, F2182, F2183, F2184, F2185, F2186, F2187 | POST /api/v1/erp/connections/{conn_id}/rollback |  |
| F2131 | 06_testing/other | `register.logs` | [backend/app/erp/routes.py:160](../backend/app/erp/routes.py#L160) | route | used |  | F2180, F2181, F2182, F2183, F2184, F2185, F2186, F2187 | GET /api/v1/erp/connections/{conn_id}/logs |  |
| F2132 | 06_testing/other | `register.activation_history` | [backend/app/erp/routes.py:165](../backend/app/erp/routes.py#L165) | route | used |  |  | GET /api/v1/erp/activation-history |  |
| F2133 | 06_testing/other | `register.integration_status` | [backend/app/erp/routes.py:170](../backend/app/erp/routes.py#L170) | route | used |  | F2180 | GET /api/v1/erp/integration-status |  |
| F2134 | 06_testing/other | `register.validate_all` | [backend/app/erp/routes.py:175](../backend/app/erp/routes.py#L175) | route | used |  | F2180 | POST /api/v1/erp/validate-integrations |  |
| F2135 | 06_testing/other | `_now` | [backend/app/erp/service.py:59](../backend/app/erp/service.py#L59) | function | used |  | F2146, F2151, F2152, F2156, F2164 |  |  |
| F2136 | 06_testing/other | `ConnectionIn` | [backend/app/erp/service.py:63](../backend/app/erp/service.py#L63) | pydantic_model | used | Connection settings. `secret` is write-only (only with secret_ref="stored"); it is never r | F2117, F2117, F2145, F2146, F2147, F2148 |  |  |
| F2137 | 06_testing/other | `MappingIn` | [backend/app/erp/service.py:85](../backend/app/erp/service.py#L85) | pydantic_model | used |  | F2124, F2124, F2151 |  |  |
| F2138 | 06_testing/other | `ErpService` | [backend/app/erp/service.py:90](../backend/app/erp/service.py#L90) | class | used |  | F2111, F0017 |  |  |
| F2139 | 06_testing/other | `ErpService.__init__` | [backend/app/erp/service.py:91](../backend/app/erp/service.py#L91) | method | used (framework) |  |  |  |  |
| F2140 | 06_testing/other | `ErpService._row` | [backend/app/erp/service.py:103](../backend/app/erp/service.py#L103) | method | used |  | F2143, F2144, F2146, F2148, F2150, F2151, F2152, F2153, F2154, F2155, F2156, F21 |  |  |
| F2141 | 06_testing/other | `ErpService._secret` | [backend/app/erp/service.py:109](../backend/app/erp/service.py#L109) | method | used | (secret, source). env:NAME reads the variable a secrets manager injects; stored reads the  | F2142, F2149 |  |  |
| F2142 | 06_testing/other | `ErpService.public` | [backend/app/erp/service.py:119](../backend/app/erp/service.py#L119) | method | used (framework) |  | F2143, F2144 |  |  |
| F2143 | 06_testing/other | `ErpService.list` | [backend/app/erp/service.py:126](../backend/app/erp/service.py#L126) | method | used (framework) |  |  |  |  |
| F2144 | 06_testing/other | `ErpService.get` | [backend/app/erp/service.py:130](../backend/app/erp/service.py#L130) | method | used (framework) |  | F2146 |  |  |
| F2145 | 06_testing/other | `ErpService._rules` | [backend/app/erp/service.py:134](../backend/app/erp/service.py#L134) | method | used (framework) |  | F2146 |  |  |
| F2146 | 06_testing/other | `ErpService._save` | [backend/app/erp/service.py:162](../backend/app/erp/service.py#L162) | method | used (framework) |  | F2147, F2148 |  |  |
| F2147 | 06_testing/other | `ErpService.create` | [backend/app/erp/service.py:192](../backend/app/erp/service.py#L192) | method | used (framework) |  |  |  |  |
| F2148 | 06_testing/other | `ErpService.patch` | [backend/app/erp/service.py:195](../backend/app/erp/service.py#L195) | method | used (framework) |  |  |  |  |
| F2149 | 06_testing/other | `ErpService.connector` | [backend/app/erp/service.py:201](../backend/app/erp/service.py#L201) | method | used |  | F2045, F2152, F2153, F2154, F2155, F2156 |  |  |
| F2150 | 06_testing/other | `ErpService.mapping` | [backend/app/erp/service.py:211](../backend/app/erp/service.py#L211) | method | used |  | F2045, F2123, F2151, F2152, F2153, F2154, F2155, F2156, F2168 |  |  |
| F2151 | 06_testing/other | `ErpService.set_mapping` | [backend/app/erp/service.py:216](../backend/app/erp/service.py#L216) | method | used |  | F2124 |  |  |
| F2152 | 06_testing/other | `ErpService.test` | [backend/app/erp/service.py:231](../backend/app/erp/service.py#L231) | method | used (framework) |  |  |  |  |
| F2153 | 06_testing/other | `ErpService.discover` | [backend/app/erp/service.py:243](../backend/app/erp/service.py#L243) | method | used |  | F2122 |  |  |
| F2154 | 06_testing/other | `ErpService.validate` | [backend/app/erp/service.py:247](../backend/app/erp/service.py#L247) | method | used (framework) |  |  |  |  |
| F2155 | 06_testing/other | `ErpService.preview` | [backend/app/erp/service.py:253](../backend/app/erp/service.py#L253) | method | used (framework) |  |  |  |  |
| F2156 | 06_testing/other | `ErpService.sync` | [backend/app/erp/service.py:260](../backend/app/erp/service.py#L260) | method | used |  | F2170 |  |  |
| F2157 | 06_testing/other | `ErpService._smoke` | [backend/app/erp/service.py:289](../backend/app/erp/service.py#L289) | method | used | The candidate must load and the engine must compute on it before it can ever be activated. | F2156 |  |  |
| F2158 | 06_testing/other | `ErpService._write` | [backend/app/erp/service.py:304](../backend/app/erp/service.py#L304) | method | used |  | F2157, F2163 |  |  |
| F2159 | 06_testing/other | `ErpService.job` | [backend/app/erp/service.py:310](../backend/app/erp/service.py#L310) | method | used |  | F2156, F2160 |  |  |
| F2160 | 06_testing/other | `ErpService.sync_history` | [backend/app/erp/service.py:317](../backend/app/erp/service.py#L317) | method | used (framework) |  |  |  |  |
| F2161 | 06_testing/other | `ErpService.active` | [backend/app/erp/service.py:323](../backend/app/erp/service.py#L323) | method | used (framework) |  | F2164, F2167, F2168 |  |  |
| F2162 | 06_testing/other | `ErpService.activate` | [backend/app/erp/service.py:326](../backend/app/erp/service.py#L326) | method | used (framework) |  |  |  |  |
| F2163 | 06_testing/other | `ErpService._swap` | [backend/app/erp/service.py:347](../backend/app/erp/service.py#L347) | method | used (framework) |  | F2162, F2165, F2167 |  |  |
| F2164 | 06_testing/other | `ErpService._record` | [backend/app/erp/service.py:351](../backend/app/erp/service.py#L351) | method | used (framework) |  | F2162, F2165 |  |  |
| F2165 | 06_testing/other | `ErpService.rollback` | [backend/app/erp/service.py:362](../backend/app/erp/service.py#L362) | method | used (framework) | Back to the snapshot that was active before the current one (or the customer's built-in sn |  |  |  |
| F2166 | 06_testing/other | `ErpService.activation_history` | [backend/app/erp/service.py:376](../backend/app/erp/service.py#L376) | method | used (framework) |  |  |  |  |
| F2167 | 06_testing/other | `ErpService.restore` | [backend/app/erp/service.py:379](../backend/app/erp/service.py#L379) | method | used (framework) | At startup: put every customer back on its last activated snapshot (the database is the so |  |  |  |
| F2168 | 06_testing/other | `ErpService.health` | [backend/app/erp/service.py:392](../backend/app/erp/service.py#L392) | method | used (framework) |  |  |  |  |
| F2169 | 06_testing/other | `ErpService.logs` | [backend/app/erp/service.py:410](../backend/app/erp/service.py#L410) | method | used (framework) |  |  |  |  |
| F2170 | 06_testing/other | `ErpService.run_scheduled` | [backend/app/erp/service.py:415](../backend/app/erp/service.py#L415) | method | used |  | F2172 |  |  |
| F2171 | 06_testing/other | `ErpService.start_scheduler` | [backend/app/erp/service.py:430](../backend/app/erp/service.py#L430) | method | used |  | F0017 |  |  |
| F2172 | 06_testing/other | `ErpService.start_scheduler.loop` | [backend/app/erp/service.py:431](../backend/app/erp/service.py#L431) | nested | used |  | F2171 |  |  |
| F2173 | 06_testing/other | `options` | [backend/app/erp/service.py:441](../backend/app/erp/service.py#L441) | function | used |  | F2115 |  |  |
| F2174 | 06_testing/unit_tests | `emulator_transport` | [tests/test_erp.py:20](../tests/test_erp.py#L20) | function | used |  | F2176, F2187 |  |  |
| F2175 | 06_testing/unit_tests | `emulator_transport.handle` | [tests/test_erp.py:23](../tests/test_erp.py#L23) | nested | used |  | F2174 |  |  |
| F2176 | 06_testing/unit_tests | `app` | [tests/test_erp.py:39](../tests/test_erp.py#L39) | function | used |  | F2177, F2185 |  |  |
| F2177 | 06_testing/unit_tests | `c` | [tests/test_erp.py:49](../tests/test_erp.py#L49) | function | used |  | F2178, F2179, F2180, F2181, F2182, F2183, F2184, F2185, F2186, F2187 |  |  |
| F2178 | 06_testing/unit_tests | `live` | [tests/test_erp.py:60](../tests/test_erp.py#L60) | function | used |  | F2181, F2182, F2183, F2184, F2185, F2186, F2187 |  |  |
| F2179 | 06_testing/unit_tests | `snapshot_id` | [tests/test_erp.py:66](../tests/test_erp.py#L66) | function | used |  | F2180, F2181, F2182, F2186, F2187 |  |  |
| F2180 | 06_testing/unit_tests | `test_a_mock_sap_connection` | [tests/test_erp.py:70](../tests/test_erp.py#L70) | test | test |  |  |  |  |
| F2181 | 06_testing/unit_tests | `test_b_live_connection_sync_activate_and_rollback` | [tests/test_erp.py:87](../tests/test_erp.py#L87) | test | test |  |  |  |  |
| F2182 | 06_testing/unit_tests | `test_c_failures_keep_the_active_snapshot` | [tests/test_erp.py:128](../tests/test_erp.py#L128) | test | test |  |  |  |  |
| F2183 | 06_testing/unit_tests | `test_invalid_mapping_blocks_activation` | [tests/test_erp.py:151](../tests/test_erp.py#L151) | test | test |  |  |  |  |
| F2184 | 06_testing/unit_tests | `test_oauth_client_credentials` | [tests/test_erp.py:165](../tests/test_erp.py#L165) | test | test |  |  |  |  |
| F2185 | 06_testing/unit_tests | `test_d_security` | [tests/test_erp.py:170](../tests/test_erp.py#L170) | test | test |  |  |  |  |
| F2186 | 06_testing/unit_tests | `test_activation_is_per_customer` | [tests/test_erp.py:200](../tests/test_erp.py#L200) | test | test |  |  |  |  |
| F2187 | 06_testing/unit_tests | `test_activation_survives_restart` | [tests/test_erp.py:209](../tests/test_erp.py#L209) | test | test |  |  |  |  |
