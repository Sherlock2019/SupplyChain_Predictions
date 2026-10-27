# 02_business_logic/aurelia_views (generated)

Modules: `backend/app/dashboards.py`, `backend/app/insights.py`, `backend/app/moat.py`, `backend/app/roles.py`

| ID | Function / class | Kind | Status | Original | Annotated copy | Summary |
|---|---|---|---|---|---|---|
| F0227 | `_status_cover` | function | used (framework) | [backend/app/dashboards.py:28](../../../backend/app/dashboards.py#L28) | [annotated](../../02_business_logic/aurelia_views/app_dashboards.py) |  |
| F0228 | `_in` | function | used (framework) | [backend/app/dashboards.py:34](../../../backend/app/dashboards.py#L34) | [annotated](../../02_business_logic/aurelia_views/app_dashboards.py) |  |
| F0229 | `Dashboards` | class | used | [backend/app/dashboards.py:38](../../../backend/app/dashboards.py#L38) | [annotated](../../02_business_logic/aurelia_views/app_dashboards.py) |  |
| F0230 | `Dashboards.__init__` | method | used (framework) | [backend/app/dashboards.py:39](../../../backend/app/dashboards.py#L39) | [annotated](../../02_business_logic/aurelia_views/app_dashboards.py) |  |
| F0231 | `Dashboards.product_scope` | method | used | [backend/app/dashboards.py:42](../../../backend/app/dashboards.py#L42) | [annotated](../../02_business_logic/aurelia_views/app_dashboards.py) | A finished good plus its BOM components; None means the whole network. |
| F0232 | `Dashboards.build` | method | used | [backend/app/dashboards.py:51](../../../backend/app/dashboards.py#L51) | [annotated](../../02_business_logic/aurelia_views/app_dashboards.py) |  |
| F0233 | `Dashboards._understock_chart` | method | used (framework) | [backend/app/dashboards.py:62](../../../backend/app/dashboards.py#L62) | [annotated](../../02_business_logic/aurelia_views/app_dashboards.py) |  |
| F0234 | `Dashboards._supplier_rows` | method | used (framework) | [backend/app/dashboards.py:70](../../../backend/app/dashboards.py#L70) | [annotated](../../02_business_logic/aurelia_views/app_dashboards.py) |  |
| F0235 | `Dashboards._mentions` | method | used (framework) | [backend/app/dashboards.py:81](../../../backend/app/dashboards.py#L81) | [annotated](../../02_business_logic/aurelia_views/app_dashboards.py) |  |
| F0236 | `Dashboards._executive` | method | used (framework) | [backend/app/dashboards.py:89](../../../backend/app/dashboards.py#L89) | [annotated](../../02_business_logic/aurelia_views/app_dashboards.py) |  |
| F0237 | `Dashboards._inventory` | method | used (framework) | [backend/app/dashboards.py:122](../../../backend/app/dashboards.py#L122) | [annotated](../../02_business_logic/aurelia_views/app_dashboards.py) |  |
| F0238 | `Dashboards._sales` | method | used (framework) | [backend/app/dashboards.py:157](../../../backend/app/dashboards.py#L157) | [annotated](../../02_business_logic/aurelia_views/app_dashboards.py) |  |
| F0239 | `Dashboards._stocktake` | method | used (framework) | [backend/app/dashboards.py:193](../../../backend/app/dashboards.py#L193) | [annotated](../../02_business_logic/aurelia_views/app_dashboards.py) |  |
| F0240 | `Dashboards._procurement` | method | used (framework) | [backend/app/dashboards.py:223](../../../backend/app/dashboards.py#L223) | [annotated](../../02_business_logic/aurelia_views/app_dashboards.py) |  |
| F0241 | `Dashboards._production` | method | used (framework) | [backend/app/dashboards.py:257](../../../backend/app/dashboards.py#L257) | [annotated](../../02_business_logic/aurelia_views/app_dashboards.py) |  |
| F0242 | `Dashboards._logistics` | method | used (framework) | [backend/app/dashboards.py:283](../../../backend/app/dashboards.py#L283) | [annotated](../../02_business_logic/aurelia_views/app_dashboards.py) |  |
| F0243 | `_id` | function | used | [backend/app/insights.py:15](../../../backend/app/insights.py#L15) | [annotated](../../02_business_logic/aurelia_views/app_insights.py) |  |
| F0244 | `InsightEngine` | class | used | [backend/app/insights.py:19](../../../backend/app/insights.py#L19) | [annotated](../../02_business_logic/aurelia_views/app_insights.py) |  |
| F0245 | `InsightEngine.__init__` | method | used (framework) | [backend/app/insights.py:20](../../../backend/app/insights.py#L20) | [annotated](../../02_business_logic/aurelia_views/app_insights.py) |  |
| F0246 | `InsightEngine._plant` | method | used | [backend/app/insights.py:24](../../../backend/app/insights.py#L24) | [annotated](../../02_business_logic/aurelia_views/app_insights.py) |  |
| F0247 | `InsightEngine._mat` | method | used | [backend/app/insights.py:27](../../../backend/app/insights.py#L27) | [annotated](../../02_business_logic/aurelia_views/app_insights.py) |  |
| F0248 | `InsightEngine.insights` | method | used | [backend/app/insights.py:30](../../../backend/app/insights.py#L30) | [annotated](../../02_business_logic/aurelia_views/app_insights.py) |  |
| F0249 | `InsightEngine.evaluate` | method | used | [backend/app/insights.py:133](../../../backend/app/insights.py#L133) | [annotated](../../02_business_logic/aurelia_views/app_insights.py) |  |
| F0250 | `MoatEngine` | class | used | [backend/app/moat.py:43](../../../backend/app/moat.py#L43) | [annotated](../../02_business_logic/aurelia_views/app_moat.py) |  |
| F0251 | `MoatEngine.__init__` | method | used (framework) | [backend/app/moat.py:44](../../../backend/app/moat.py#L44) | [annotated](../../02_business_logic/aurelia_views/app_moat.py) |  |
| F0252 | `MoatEngine.consent` | method | used | [backend/app/moat.py:48](../../../backend/app/moat.py#L48) | [annotated](../../02_business_logic/aurelia_views/app_moat.py) | Recorded consent wins; without a record, synthetic demo customers are opted in a |
| F0253 | `MoatEngine._series` | method | used | [backend/app/moat.py:56](../../../backend/app/moat.py#L56) | [annotated](../../02_business_logic/aurelia_views/app_moat.py) |  |
| F0254 | `MoatEngine.model_comparison` | method | used | [backend/app/moat.py:61](../../../backend/app/moat.py#L61) | [annotated](../../02_business_logic/aurelia_views/app_moat.py) |  |
| F0255 | `MoatEngine.view` | method | used | [backend/app/moat.py:92](../../../backend/app/moat.py#L92) | [annotated](../../02_business_logic/aurelia_views/app_moat.py) |  |
| F0256 | `agent_system_prompt` | function | used | [backend/app/roles.py:142](../../../backend/app/roles.py#L142) | [annotated](../../02_business_logic/aurelia_views/app_roles.py) | Role-specific instructions for the specialised agent (LangGraph chat graph). |
| F0257 | `_status` | function | used | [backend/app/roles.py:151](../../../backend/app/roles.py#L151) | [annotated](../../02_business_logic/aurelia_views/app_roles.py) |  |
| F0258 | `kpi` | function | used | [backend/app/roles.py:159](../../../backend/app/roles.py#L159) | [annotated](../../02_business_logic/aurelia_views/app_roles.py) | A KPI with its agreed definition. available=False means the SAP source is not in |
| F0259 | `RoleCenter` | class | used | [backend/app/roles.py:168](../../../backend/app/roles.py#L168) | [annotated](../../02_business_logic/aurelia_views/app_roles.py) |  |
| F0260 | `RoleCenter.__init__` | method | used (framework) | [backend/app/roles.py:169](../../../backend/app/roles.py#L169) | [annotated](../../02_business_logic/aurelia_views/app_roles.py) |  |
| F0261 | `RoleCenter._facts` | method | used | [backend/app/roles.py:173](../../../backend/app/roles.py#L173) | [annotated](../../02_business_logic/aurelia_views/app_roles.py) |  |
| F0262 | `RoleCenter._otif` | method | used | [backend/app/roles.py:202](../../../backend/app/roles.py#L202) | [annotated](../../02_business_logic/aurelia_views/app_roles.py) |  |
| F0263 | `RoleCenter._inventory_value` | method | used | [backend/app/roles.py:206](../../../backend/app/roles.py#L206) | [annotated](../../02_business_logic/aurelia_views/app_roles.py) |  |
| F0264 | `RoleCenter._annual_cogs` | method | used | [backend/app/roles.py:209](../../../backend/app/roles.py#L209) | [annotated](../../02_business_logic/aurelia_views/app_roles.py) |  |
| F0265 | `RoleCenter._wape` | method | used | [backend/app/roles.py:213](../../../backend/app/roles.py#L213) | [annotated](../../02_business_logic/aurelia_views/app_roles.py) |  |
| F0266 | `RoleCenter._supply_chain_cost` | method | used | [backend/app/roles.py:217](../../../backend/app/roles.py#L217) | [annotated](../../02_business_logic/aurelia_views/app_roles.py) | 30-day estimate: procurement (open POs) + transport (proposed transfers) + stora |
| F0267 | `RoleCenter.platform_kpis` | method | used | [backend/app/roles.py:232](../../../backend/app/roles.py#L232) | [annotated](../../02_business_logic/aurelia_views/app_roles.py) |  |
| F0268 | `RoleCenter.learning_summary` | method | used | [backend/app/roles.py:255](../../../backend/app/roles.py#L255) | [annotated](../../02_business_logic/aurelia_views/app_roles.py) |  |
| F0269 | `RoleCenter.north_star` | method | used | [backend/app/roles.py:274](../../../backend/app/roles.py#L274) | [annotated](../../02_business_logic/aurelia_views/app_roles.py) |  |
| F0270 | `RoleCenter.industry_kpis` | method | used | [backend/app/roles.py:297](../../../backend/app/roles.py#L297) | [annotated](../../02_business_logic/aurelia_views/app_roles.py) |  |
| F0271 | `RoleCenter.catalogue` | method | used | [backend/app/roles.py:342](../../../backend/app/roles.py#L342) | [annotated](../../02_business_logic/aurelia_views/app_roles.py) |  |
| F0272 | `RoleCenter.build` | method | used | [backend/app/roles.py:345](../../../backend/app/roles.py#L345) | [annotated](../../02_business_logic/aurelia_views/app_roles.py) |  |
| F0273 | `RoleCenter._issue_actions` | method | used (framework) | [backend/app/roles.py:371](../../../backend/app/roles.py#L371) | [annotated](../../02_business_logic/aurelia_views/app_roles.py) |  |
| F0274 | `RoleCenter._stock_predictions` | method | used (framework) | [backend/app/roles.py:377](../../../backend/app/roles.py#L377) | [annotated](../../02_business_logic/aurelia_views/app_roles.py) |  |
| F0275 | `RoleCenter._production_predictions` | method | used (framework) | [backend/app/roles.py:391](../../../backend/app/roles.py#L391) | [annotated](../../02_business_logic/aurelia_views/app_roles.py) |  |
| F0276 | `RoleCenter._supplier_predictions` | method | used (framework) | [backend/app/roles.py:404](../../../backend/app/roles.py#L404) | [annotated](../../02_business_logic/aurelia_views/app_roles.py) |  |
| F0277 | `RoleCenter._shipment_predictions` | method | used (framework) | [backend/app/roles.py:419](../../../backend/app/roles.py#L419) | [annotated](../../02_business_logic/aurelia_views/app_roles.py) |  |
| F0278 | `RoleCenter._quality_predictions` | method | used (framework) | [backend/app/roles.py:430](../../../backend/app/roles.py#L430) | [annotated](../../02_business_logic/aurelia_views/app_roles.py) |  |
| F0279 | `RoleCenter._go` | method | used (framework) | [backend/app/roles.py:448](../../../backend/app/roles.py#L448) | [annotated](../../02_business_logic/aurelia_views/app_roles.py) |  |
| F0280 | `RoleCenter._charts` | method | used (framework) | [backend/app/roles.py:453](../../../backend/app/roles.py#L453) | [annotated](../../02_business_logic/aurelia_views/app_roles.py) |  |
| F0281 | `RoleCenter._director` | method | used (framework) | [backend/app/roles.py:458](../../../backend/app/roles.py#L458) | [annotated](../../02_business_logic/aurelia_views/app_roles.py) |  |
| F0282 | `RoleCenter._demand` | method | used (framework) | [backend/app/roles.py:476](../../../backend/app/roles.py#L476) | [annotated](../../02_business_logic/aurelia_views/app_roles.py) |  |
| F0283 | `RoleCenter._production` | method | used (framework) | [backend/app/roles.py:507](../../../backend/app/roles.py#L507) | [annotated](../../02_business_logic/aurelia_views/app_roles.py) |  |
| F0284 | `RoleCenter._procurement` | method | used (framework) | [backend/app/roles.py:524](../../../backend/app/roles.py#L524) | [annotated](../../02_business_logic/aurelia_views/app_roles.py) |  |
| F0285 | `RoleCenter._warehouse` | method | used (framework) | [backend/app/roles.py:551](../../../backend/app/roles.py#L551) | [annotated](../../02_business_logic/aurelia_views/app_roles.py) |  |
| F0286 | `RoleCenter._logistics` | method | used (framework) | [backend/app/roles.py:584](../../../backend/app/roles.py#L584) | [annotated](../../02_business_logic/aurelia_views/app_roles.py) |  |
| F0287 | `RoleCenter._quality` | method | used (framework) | [backend/app/roles.py:608](../../../backend/app/roles.py#L608) | [annotated](../../02_business_logic/aurelia_views/app_roles.py) |  |
| F0288 | `RoleCenter._finance` | method | used (framework) | [backend/app/roles.py:649](../../../backend/app/roles.py#L649) | [annotated](../../02_business_logic/aurelia_views/app_roles.py) |  |
| F0289 | `RoleCenter._mlops` | method | used (framework) | [backend/app/roles.py:689](../../../backend/app/roles.py#L689) | [annotated](../../02_business_logic/aurelia_views/app_roles.py) |  |
| F0290 | `RoleCenter.learning` | method | used | [backend/app/roles.py:729](../../../backend/app/roles.py#L729) | [annotated](../../02_business_logic/aurelia_views/app_roles.py) |  |
