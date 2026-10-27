# Backend functions (generated)

Every function, method, class and route under `backend/`: **896** definitions in **50** modules, **139** FastAPI routes. Links open the exact source line; *annotated* opens the commented copy.

Regenerate: `python3 code_explorer/tools/build_code_explorer.py`.

## backend/app/agentflow.py

LangGraph AgentFlow — the full SPARC agent workflow, mirroring the Flowise AgentFlow V2.

| ID | Function | Kind | FastAPI route | Status | Annotated | Summary |
|---|---|---|---|---|---|---|
| F0538 | [`AgentFlowState`](../backend/app/agentflow.py#L61) | class |  | used | [annotated](../code_explorer/04_ai_ml/langgraph/app_agentflow.py) |  |
| F0539 | [`RouteDecision`](../backend/app/agentflow.py#L71) | pydantic_model |  | used | [annotated](../code_explorer/04_ai_ml/langgraph/app_agentflow.py) | Pick exactly one role specialist for the planner's latest request. |
| F0540 | [`_last_human`](../backend/app/agentflow.py#L82) | function |  | used | [annotated](../code_explorer/04_ai_ml/langgraph/app_agentflow.py) |  |
| F0541 | [`sap_read`](../backend/app/agentflow.py#L87) | function |  | used | [annotated](../code_explorer/04_ai_ml/langgraph/app_agentflow.py) | Read the SAP S/4HANA snapshot provenance and valid codes (read-only; writes are blocked by |
| F0542 | [`rag_retrieve`](../backend/app/agentflow.py#L99) | function |  | used | [annotated](../code_explorer/04_ai_ml/langgraph/app_agentflow.py) | Retrieve governed policy context (contracts, SOPs, quality and logistics policies) from Po |
| F0543 | [`_keyword_route`](../backend/app/agentflow.py#L122) | function |  | used | [annotated](../code_explorer/04_ai_ml/langgraph/app_agentflow.py) |  |
| F0544 | [`supervisor`](../backend/app/agentflow.py#L132) | function |  | used | [annotated](../code_explorer/04_ai_ml/langgraph/app_agentflow.py) |  |
| F0545 | [`route_next`](../backend/app/agentflow.py#L147) | function |  | used | [annotated](../code_explorer/04_ai_ml/langgraph/app_agentflow.py) |  |
| F0546 | [`_conversation`](../backend/app/agentflow.py#L152) | function |  | used | [annotated](../code_explorer/04_ai_ml/langgraph/app_agentflow.py) | Prior human turns and final answers only, so specialists never see dangling tool calls fro |
| F0547 | [`_analysis_from`](../backend/app/agentflow.py#L158) | function |  | used | [annotated](../code_explorer/04_ai_ml/langgraph/app_agentflow.py) |  |
| F0548 | [`_deterministic`](../backend/app/agentflow.py#L171) | function |  | used | [annotated](../code_explorer/04_ai_ml/langgraph/app_agentflow.py) |  |
| F0549 | [`_knowledge_block`](../backend/app/agentflow.py#L192) | function |  | used | [annotated](../code_explorer/04_ai_ml/langgraph/app_agentflow.py) |  |
| F0550 | [`_specialist`](../backend/app/agentflow.py#L200) | function |  | used | [annotated](../code_explorer/04_ai_ml/langgraph/app_agentflow.py) |  |
| F0551 | [`_specialist.node`](../backend/app/agentflow.py#L206) | nested |  | used | [annotated](../code_explorer/04_ai_ml/langgraph/app_agentflow.py) |  |
| F0552 | [`approval_gate`](../backend/app/agentflow.py#L234) | function |  | used | [annotated](../code_explorer/04_ai_ml/langgraph/app_agentflow.py) | Planner Human Input: submit the specialist's stored analysis to the manager queue, or disc |
| F0553 | [`boundary`](../backend/app/agentflow.py#L262) | function |  | used | [annotated](../code_explorer/04_ai_ml/langgraph/app_agentflow.py) |  |

## backend/app/auth.py

API-key authentication of the SPARC / Aurelia FastAPI gateway (backend/app/main.py). Keys map to an

| ID | Function | Kind | FastAPI route | Status | Annotated | Summary |
|---|---|---|---|---|---|---|
| F0767 | [`Principal`](../backend/app/auth.py#L11) | class |  | used | [annotated](../code_explorer/05_security_governance/authentication/app_auth.py) |  |
| F0768 | [`ApiKeyAuth`](../backend/app/auth.py#L17) | class |  | used | [annotated](../code_explorer/05_security_governance/authentication/app_auth.py) |  |
| F0769 | [`ApiKeyAuth.__init__`](../backend/app/auth.py#L18) | method |  | used (framework) | [annotated](../code_explorer/05_security_governance/authentication/app_auth.py) |  |
| F0770 | [`ApiKeyAuth.authenticate`](../backend/app/auth.py#L21) | method |  | used | [annotated](../code_explorer/05_security_governance/authentication/app_auth.py) |  |
| F0771 | [`ApiKeyAuth.require`](../backend/app/auth.py#L28) | method |  | used | [annotated](../code_explorer/05_security_governance/authentication/app_auth.py) |  |

## backend/app/code_editor.py

Backend code section of the SPARC UI: browse every backend function and, on a development machine, edit one function.

| ID | Function | Kind | FastAPI route | Status | Annotated | Summary |
|---|---|---|---|---|---|---|
| F1784 | [`_defs`](../backend/app/code_editor.py#L39) | function |  | used | — | qualname -> def/class node, including methods and nested functions. |
| F1785 | [`_defs.walk`](../backend/app/code_editor.py#L43) | nested |  | used | — |  |
| F1786 | [`_span`](../backend/app/code_editor.py#L54) | function |  | used | — |  |
| F1787 | [`CodeEditor`](../backend/app/code_editor.py#L58) | class |  | used | — |  |
| F1788 | [`CodeEditor.__init__`](../backend/app/code_editor.py#L59) | method |  | used (framework) | — |  |
| F1789 | [`CodeEditor._registry`](../backend/app/code_editor.py#L66) | method |  | used | — |  |
| F1790 | [`CodeEditor._files`](../backend/app/code_editor.py#L74) | method |  | used | — |  |
| F1800 | [`CodeEditor._apps_of`](../backend/app/code_editor.py#L77) | method |  | used | — | file -> ids of the apps that load it (transitive backend imports from each app's entry mod |
| F1791 | [`CodeEditor.list`](../backend/app/code_editor.py#L103) | method |  | used | — |  |
| F1792 | [`CodeEditor._locate`](../backend/app/code_editor.py#L130) | method |  | used (framework) | — |  |
| F1793 | [`CodeEditor.get`](../backend/app/code_editor.py#L143) | method |  | used (framework) | — |  |
| F1794 | [`CodeEditor.update`](../backend/app/code_editor.py#L173) | method |  | used (framework) | — |  |

## backend/app/config.py

configuration of the SPARC / Aurelia gateway (backend/app), read from environment variables / .env.

| ID | Function | Kind | FastAPI route | Status | Annotated | Summary |
|---|---|---|---|---|---|---|
| F0001 | [`Settings`](../backend/app/config.py#L11) | pydantic_model |  | used | [annotated](../code_explorer/01_fastapi/app_setup/app_config.py) |  |
| F0002 | [`Settings.parse_keys`](../backend/app/config.py#L73) | method |  | used (framework) | [annotated](../code_explorer/01_fastapi/app_setup/app_config.py) |  |
| F0003 | [`Settings.assistants`](../backend/app/config.py#L82) | method |  | used (framework) | [annotated](../code_explorer/01_fastapi/app_setup/app_config.py) |  |
| F0004 | [`Settings.managers`](../backend/app/config.py#L86) | method |  | used (framework) | [annotated](../code_explorer/01_fastapi/app_setup/app_config.py) |  |
| F0005 | [`Settings.tenants_for`](../backend/app/config.py#L90) | method |  | used | [annotated](../code_explorer/01_fastapi/app_setup/app_config.py) | Tenants an identity may use; None = unrestricted. |
| F0006 | [`Settings.llm_enabled`](../backend/app/config.py#L99) | method |  | used (framework) | [annotated](../code_explorer/01_fastapi/app_setup/app_config.py) |  |
| F0007 | [`Settings.langfuse_enabled`](../backend/app/config.py#L103) | method |  | used (framework) | [annotated](../code_explorer/01_fastapi/app_setup/app_config.py) |  |
| F0008 | [`get_settings`](../backend/app/config.py#L108) | function |  | used | [annotated](../code_explorer/01_fastapi/app_setup/app_config.py) |  |

## backend/app/copilot.py

One governed backend for every agent runtime (LangGraph, Deep Agents, MCP).

| ID | Function | Kind | FastAPI route | Status | Annotated | Summary |
|---|---|---|---|---|---|---|
| F0438 | [`CopilotBackend`](../backend/app/copilot.py#L21) | class |  | used | [annotated](../code_explorer/04_ai_ml/agent_tools/app_copilot.py) |  |
| F0439 | [`CopilotBackend.snapshot`](../backend/app/copilot.py#L22) | method |  | used (framework) | [annotated](../code_explorer/04_ai_ml/agent_tools/app_copilot.py) |  |
| F0440 | [`CopilotBackend.factory_readiness`](../backend/app/copilot.py#L23) | method |  | used (framework) | [annotated](../code_explorer/04_ai_ml/agent_tools/app_copilot.py) |  |
| F0441 | [`CopilotBackend.stock_balance`](../backend/app/copilot.py#L24) | method |  | used (framework) | [annotated](../code_explorer/04_ai_ml/agent_tools/app_copilot.py) |  |
| F0442 | [`CopilotBackend.demand_forecast`](../backend/app/copilot.py#L25) | method |  | used (framework) | [annotated](../code_explorer/04_ai_ml/agent_tools/app_copilot.py) |  |
| F0443 | [`CopilotBackend.supplier_risk`](../backend/app/copilot.py#L26) | method |  | used (framework) | [annotated](../code_explorer/04_ai_ml/agent_tools/app_copilot.py) |  |
| F0444 | [`CopilotBackend.quality_status`](../backend/app/copilot.py#L27) | method |  | used (framework) | [annotated](../code_explorer/04_ai_ml/agent_tools/app_copilot.py) |  |
| F0445 | [`CopilotBackend.logistics_status`](../backend/app/copilot.py#L28) | method |  | used (framework) | [annotated](../code_explorer/04_ai_ml/agent_tools/app_copilot.py) |  |
| F0446 | [`CopilotBackend.inventory`](../backend/app/copilot.py#L29) | method |  | used (framework) | [annotated](../code_explorer/04_ai_ml/agent_tools/app_copilot.py) |  |
| F0447 | [`CopilotBackend.sales_orders`](../backend/app/copilot.py#L30) | method |  | used (framework) | [annotated](../code_explorer/04_ai_ml/agent_tools/app_copilot.py) |  |
| F0448 | [`CopilotBackend.stocktake`](../backend/app/copilot.py#L31) | method |  | used (framework) | [annotated](../code_explorer/04_ai_ml/agent_tools/app_copilot.py) |  |
| F0449 | [`CopilotBackend.search_knowledge`](../backend/app/copilot.py#L32) | method |  | used (framework) | [annotated](../code_explorer/04_ai_ml/agent_tools/app_copilot.py) |  |
| F0450 | [`CopilotBackend.submit_recommendation`](../backend/app/copilot.py#L33) | method |  | used (framework) | [annotated](../code_explorer/04_ai_ml/agent_tools/app_copilot.py) |  |
| F0451 | [`LocalBackend`](../backend/app/copilot.py#L36) | class |  | used | [annotated](../code_explorer/04_ai_ml/agent_tools/app_copilot.py) | In-process engine with its own ledger. Used by unit tests and when no gateway URL is confi |
| F0452 | [`LocalBackend.__init__`](../backend/app/copilot.py#L39) | method |  | used (framework) | [annotated](../code_explorer/04_ai_ml/agent_tools/app_copilot.py) |  |
| F0453 | [`LocalBackend._save`](../backend/app/copilot.py#L46) | method |  | used | [annotated](../code_explorer/04_ai_ml/agent_tools/app_copilot.py) |  |
| F0454 | [`LocalBackend.snapshot`](../backend/app/copilot.py#L50) | method |  | used | [annotated](../code_explorer/04_ai_ml/agent_tools/app_copilot.py) |  |
| F0455 | [`LocalBackend.factory_readiness`](../backend/app/copilot.py#L58) | method |  | used | [annotated](../code_explorer/04_ai_ml/agent_tools/app_copilot.py) |  |
| F0456 | [`LocalBackend.stock_balance`](../backend/app/copilot.py#L62) | method |  | used | [annotated](../code_explorer/04_ai_ml/agent_tools/app_copilot.py) |  |
| F0457 | [`LocalBackend.demand_forecast`](../backend/app/copilot.py#L66) | method |  | used | [annotated](../code_explorer/04_ai_ml/agent_tools/app_copilot.py) |  |
| F0458 | [`LocalBackend.supplier_risk`](../backend/app/copilot.py#L70) | method |  | used | [annotated](../code_explorer/04_ai_ml/agent_tools/app_copilot.py) |  |
| F0459 | [`LocalBackend.quality_status`](../backend/app/copilot.py#L73) | method |  | used | [annotated](../code_explorer/04_ai_ml/agent_tools/app_copilot.py) |  |
| F0460 | [`LocalBackend.logistics_status`](../backend/app/copilot.py#L76) | method |  | used | [annotated](../code_explorer/04_ai_ml/agent_tools/app_copilot.py) |  |
| F0461 | [`LocalBackend.inventory`](../backend/app/copilot.py#L79) | method |  | used | [annotated](../code_explorer/04_ai_ml/agent_tools/app_copilot.py) |  |
| F0462 | [`LocalBackend.sales_orders`](../backend/app/copilot.py#L82) | method |  | used | [annotated](../code_explorer/04_ai_ml/agent_tools/app_copilot.py) |  |
| F0463 | [`LocalBackend.stocktake`](../backend/app/copilot.py#L85) | method |  | used | [annotated](../code_explorer/04_ai_ml/agent_tools/app_copilot.py) |  |
| F0464 | [`LocalBackend.search_knowledge`](../backend/app/copilot.py#L88) | method |  | used | [annotated](../code_explorer/04_ai_ml/agent_tools/app_copilot.py) |  |
| F0465 | [`LocalBackend.submit_recommendation`](../backend/app/copilot.py#L91) | method |  | used | [annotated](../code_explorer/04_ai_ml/agent_tools/app_copilot.py) |  |
| F0466 | [`ApiError`](../backend/app/copilot.py#L95) | class |  | used | [annotated](../code_explorer/04_ai_ml/agent_tools/app_copilot.py) |  |
| F0467 | [`ApiBackend`](../backend/app/copilot.py#L99) | class |  | used | [annotated](../code_explorer/04_ai_ml/agent_tools/app_copilot.py) | HTTP client for the FastAPI gateway; every call is authenticated and audited by the gatewa |
| F0468 | [`ApiBackend.__init__`](../backend/app/copilot.py#L102) | method |  | used (framework) | [annotated](../code_explorer/04_ai_ml/agent_tools/app_copilot.py) |  |
| F0469 | [`ApiBackend._call`](../backend/app/copilot.py#L105) | method |  | used | [annotated](../code_explorer/04_ai_ml/agent_tools/app_copilot.py) |  |
| F0470 | [`ApiBackend._clean`](../backend/app/copilot.py#L115) | method |  | used | [annotated](../code_explorer/04_ai_ml/agent_tools/app_copilot.py) |  |
| F0471 | [`ApiBackend.snapshot`](../backend/app/copilot.py#L119) | method |  | used | [annotated](../code_explorer/04_ai_ml/agent_tools/app_copilot.py) |  |
| F0472 | [`ApiBackend.factory_readiness`](../backend/app/copilot.py#L122) | method |  | used | [annotated](../code_explorer/04_ai_ml/agent_tools/app_copilot.py) |  |
| F0473 | [`ApiBackend.stock_balance`](../backend/app/copilot.py#L125) | method |  | used | [annotated](../code_explorer/04_ai_ml/agent_tools/app_copilot.py) |  |
| F0474 | [`ApiBackend.demand_forecast`](../backend/app/copilot.py#L128) | method |  | used | [annotated](../code_explorer/04_ai_ml/agent_tools/app_copilot.py) |  |
| F0475 | [`ApiBackend.supplier_risk`](../backend/app/copilot.py#L131) | method |  | used | [annotated](../code_explorer/04_ai_ml/agent_tools/app_copilot.py) |  |
| F0476 | [`ApiBackend.quality_status`](../backend/app/copilot.py#L134) | method |  | used | [annotated](../code_explorer/04_ai_ml/agent_tools/app_copilot.py) |  |
| F0477 | [`ApiBackend.logistics_status`](../backend/app/copilot.py#L137) | method |  | used | [annotated](../code_explorer/04_ai_ml/agent_tools/app_copilot.py) |  |
| F0478 | [`ApiBackend.inventory`](../backend/app/copilot.py#L140) | method |  | used | [annotated](../code_explorer/04_ai_ml/agent_tools/app_copilot.py) |  |
| F0479 | [`ApiBackend.sales_orders`](../backend/app/copilot.py#L143) | method |  | used | [annotated](../code_explorer/04_ai_ml/agent_tools/app_copilot.py) |  |
| F0480 | [`ApiBackend.stocktake`](../backend/app/copilot.py#L146) | method |  | used | [annotated](../code_explorer/04_ai_ml/agent_tools/app_copilot.py) |  |
| F0481 | [`ApiBackend.search_knowledge`](../backend/app/copilot.py#L149) | method |  | used | [annotated](../code_explorer/04_ai_ml/agent_tools/app_copilot.py) |  |
| F0482 | [`ApiBackend.submit_recommendation`](../backend/app/copilot.py#L152) | method |  | used | [annotated](../code_explorer/04_ai_ml/agent_tools/app_copilot.py) |  |
| F0483 | [`build_backend`](../backend/app/copilot.py#L156) | function |  | used | [annotated](../code_explorer/04_ai_ml/agent_tools/app_copilot.py) |  |
| F0484 | [`get_backend`](../backend/app/copilot.py#L168) | function |  | used | [annotated](../code_explorer/04_ai_ml/agent_tools/app_copilot.py) |  |

## backend/app/dashboards.py

Role / task dashboards. Each persona gets KPI tiles, charts and tables computed deterministically from the snapshot.

| ID | Function | Kind | FastAPI route | Status | Annotated | Summary |
|---|---|---|---|---|---|---|
| F0227 | [`_status_cover`](../backend/app/dashboards.py#L28) | function |  | used (framework) | [annotated](../code_explorer/02_business_logic/aurelia_views/app_dashboards.py) |  |
| F0228 | [`_in`](../backend/app/dashboards.py#L34) | function |  | used (framework) | [annotated](../code_explorer/02_business_logic/aurelia_views/app_dashboards.py) |  |
| F0229 | [`Dashboards`](../backend/app/dashboards.py#L38) | class |  | used | [annotated](../code_explorer/02_business_logic/aurelia_views/app_dashboards.py) |  |
| F0230 | [`Dashboards.__init__`](../backend/app/dashboards.py#L39) | method |  | used (framework) | [annotated](../code_explorer/02_business_logic/aurelia_views/app_dashboards.py) |  |
| F0231 | [`Dashboards.product_scope`](../backend/app/dashboards.py#L42) | method |  | used | [annotated](../code_explorer/02_business_logic/aurelia_views/app_dashboards.py) | A finished good plus its BOM components; None means the whole network. |
| F0232 | [`Dashboards.build`](../backend/app/dashboards.py#L51) | method |  | used | [annotated](../code_explorer/02_business_logic/aurelia_views/app_dashboards.py) |  |
| F0233 | [`Dashboards._understock_chart`](../backend/app/dashboards.py#L62) | method |  | used (framework) | [annotated](../code_explorer/02_business_logic/aurelia_views/app_dashboards.py) |  |
| F0234 | [`Dashboards._supplier_rows`](../backend/app/dashboards.py#L70) | method |  | used (framework) | [annotated](../code_explorer/02_business_logic/aurelia_views/app_dashboards.py) |  |
| F0235 | [`Dashboards._mentions`](../backend/app/dashboards.py#L81) | method |  | used (framework) | [annotated](../code_explorer/02_business_logic/aurelia_views/app_dashboards.py) |  |
| F0236 | [`Dashboards._executive`](../backend/app/dashboards.py#L89) | method |  | used (framework) | [annotated](../code_explorer/02_business_logic/aurelia_views/app_dashboards.py) |  |
| F0237 | [`Dashboards._inventory`](../backend/app/dashboards.py#L122) | method |  | used (framework) | [annotated](../code_explorer/02_business_logic/aurelia_views/app_dashboards.py) |  |
| F0238 | [`Dashboards._sales`](../backend/app/dashboards.py#L157) | method |  | used (framework) | [annotated](../code_explorer/02_business_logic/aurelia_views/app_dashboards.py) |  |
| F0239 | [`Dashboards._stocktake`](../backend/app/dashboards.py#L193) | method |  | used (framework) | [annotated](../code_explorer/02_business_logic/aurelia_views/app_dashboards.py) |  |
| F0240 | [`Dashboards._procurement`](../backend/app/dashboards.py#L223) | method |  | used (framework) | [annotated](../code_explorer/02_business_logic/aurelia_views/app_dashboards.py) |  |
| F0241 | [`Dashboards._production`](../backend/app/dashboards.py#L257) | method |  | used (framework) | [annotated](../code_explorer/02_business_logic/aurelia_views/app_dashboards.py) |  |
| F0242 | [`Dashboards._logistics`](../backend/app/dashboards.py#L283) | method |  | used (framework) | [annotated](../code_explorer/02_business_logic/aurelia_views/app_dashboards.py) |  |

## backend/app/deep_agent.py

Deep Agents supplier-continuity research harness — with run-time harness settings.

| ID | Function | Kind | FastAPI route | Status | Annotated | Summary |
|---|---|---|---|---|---|---|
| F0554 | [`harness_of`](../backend/app/deep_agent.py#L62) | function |  | used | [annotated](../code_explorer/04_ai_ml/langgraph/app_deep_agent.py) | Validated harness: stored settings merged over the defaults (invalid or unknown values are |
| F0555 | [`system_prompt`](../backend/app/deep_agent.py#L67) | function |  | used | [annotated](../code_explorer/04_ai_ml/langgraph/app_deep_agent.py) |  |
| F0556 | [`_this_run`](../backend/app/deep_agent.py#L94) | function |  | used | [annotated](../code_explorer/04_ai_ml/langgraph/app_deep_agent.py) | Messages of the current run: everything after the last user message (limits reset on every |
| F0557 | [`HarnessGuard`](../backend/app/deep_agent.py#L100) | class |  | used | [annotated](../code_explorer/04_ai_ml/langgraph/app_deep_agent.py) | Loop controls of the harness, enforced around each model and tool call (no extra graph ste |
| F0558 | [`HarnessGuard.__init__`](../backend/app/deep_agent.py#L108) | method |  | used (framework) | [annotated](../code_explorer/04_ai_ml/langgraph/app_deep_agent.py) |  |
| F0559 | [`HarnessGuard._stop_message`](../backend/app/deep_agent.py#L112) | method |  | used | [annotated](../code_explorer/04_ai_ml/langgraph/app_deep_agent.py) |  |
| F0560 | [`HarnessGuard._refusal`](../backend/app/deep_agent.py#L119) | method |  | used | [annotated](../code_explorer/04_ai_ml/langgraph/app_deep_agent.py) |  |
| F0561 | [`HarnessGuard.wrap_model_call`](../backend/app/deep_agent.py#L145) | method |  | used | [annotated](../code_explorer/04_ai_ml/langgraph/app_deep_agent.py) |  |
| F0562 | [`HarnessGuard.awrap_model_call`](../backend/app/deep_agent.py#L148) | method |  | used (framework) | [annotated](../code_explorer/04_ai_ml/langgraph/app_deep_agent.py) |  |
| F0563 | [`HarnessGuard.wrap_tool_call`](../backend/app/deep_agent.py#L151) | method |  | used | [annotated](../code_explorer/04_ai_ml/langgraph/app_deep_agent.py) |  |
| F0564 | [`HarnessGuard.awrap_tool_call`](../backend/app/deep_agent.py#L154) | method |  | used (framework) | [annotated](../code_explorer/04_ai_ml/langgraph/app_deep_agent.py) |  |
| F0565 | [`build_deep_agent`](../backend/app/deep_agent.py#L158) | function |  | used | [annotated](../code_explorer/04_ai_ml/langgraph/app_deep_agent.py) | The Deep Agent for one harness (compiled LangGraph with model, tools and subagent task too |
| F0566 | [`_agent_for`](../backend/app/deep_agent.py#L180) | function |  | used | [annotated](../code_explorer/04_ai_ml/langgraph/app_deep_agent.py) |  |
| F0567 | [`ResearchState`](../backend/app/deep_agent.py#L187) | class |  | used | [annotated](../code_explorer/04_ai_ml/langgraph/app_deep_agent.py) |  |
| F0568 | [`ResearchInput`](../backend/app/deep_agent.py#L194) | class |  | used | [annotated](../code_explorer/04_ai_ml/langgraph/app_deep_agent.py) | What a run takes (Studio's Input form): the question, and optionally harness overrides for |
| F0569 | [`HarnessConfig`](../backend/app/deep_agent.py#L199) | pydantic_model |  | used | [annotated](../code_explorer/04_ai_ml/langgraph/app_deep_agent.py) | Assistant context: Studio's configuration panel shows every harness setting with its curre |
| F0570 | [`_context_harness`](../backend/app/deep_agent.py#L204) | function |  | used | [annotated](../code_explorer/04_ai_ml/langgraph/app_deep_agent.py) | Harness settings given in the run/assistant context (only the ones actually set, so defaul |
| F0571 | [`deep_research`](../backend/app/deep_agent.py#L211) | function |  | used | [annotated](../code_explorer/04_ai_ml/langgraph/app_deep_agent.py) | Run the Deep Agent configured by this run's harness settings. |
| F0572 | [`build_graph`](../backend/app/deep_agent.py#L225) | function |  | used | [annotated](../code_explorer/04_ai_ml/langgraph/app_deep_agent.py) |  |

## backend/app/engine.py

Deterministic business calculations. LLMs may explain these outputs but never create quantities.

| ID | Function | Kind | FastAPI route | Status | Annotated | Summary |
|---|---|---|---|---|---|---|
| F0192 | [`SupplyChainEngine`](../backend/app/engine.py#L14) | class |  | used | [annotated](../code_explorer/02_business_logic/aurelia_engine/app_engine.py) |  |
| F0193 | [`SupplyChainEngine.__init__`](../backend/app/engine.py#L15) | method |  | used (framework) | [annotated](../code_explorer/02_business_logic/aurelia_engine/app_engine.py) |  |
| F0194 | [`SupplyChainEngine._confirmed_pos`](../backend/app/engine.py#L19) | method |  | used | [annotated](../code_explorer/02_business_logic/aurelia_engine/app_engine.py) |  |
| F0195 | [`SupplyChainEngine._warehouses`](../backend/app/engine.py#L26) | method |  | used | [annotated](../code_explorer/02_business_logic/aurelia_engine/app_engine.py) |  |
| F0196 | [`SupplyChainEngine._in_transit_to`](../backend/app/engine.py#L29) | method |  | used | [annotated](../code_explorer/02_business_logic/aurelia_engine/app_engine.py) |  |
| F0197 | [`SupplyChainEngine.factory_readiness`](../backend/app/engine.py#L40) | method |  | used | [annotated](../code_explorer/02_business_logic/aurelia_engine/app_engine.py) |  |
| F0198 | [`SupplyChainEngine.stock_balance`](../backend/app/engine.py#L125) | method |  | used | [annotated](../code_explorer/02_business_logic/aurelia_engine/app_engine.py) |  |
| F0199 | [`SupplyChainEngine.demand_forecast`](../backend/app/engine.py#L169) | method |  | used | [annotated](../code_explorer/02_business_logic/aurelia_engine/app_engine.py) |  |
| F0200 | [`SupplyChainEngine.what_if`](../backend/app/engine.py#L180) | method |  | used | [annotated](../code_explorer/02_business_logic/aurelia_engine/app_engine.py) |  |
| F0201 | [`SupplyChainEngine.supplier_risk`](../backend/app/engine.py#L206) | method |  | used | [annotated](../code_explorer/02_business_logic/aurelia_engine/app_engine.py) |  |
| F0202 | [`SupplyChainEngine.supplier_scorecard`](../backend/app/engine.py#L262) | method |  | used | [annotated](../code_explorer/02_business_logic/aurelia_engine/app_engine.py) |  |
| F0203 | [`SupplyChainEngine.quality_status`](../backend/app/engine.py#L270) | method |  | used | [annotated](../code_explorer/02_business_logic/aurelia_engine/app_engine.py) |  |
| F0204 | [`SupplyChainEngine.logistics_status`](../backend/app/engine.py#L308) | method |  | used | [annotated](../code_explorer/02_business_logic/aurelia_engine/app_engine.py) |  |
| F0205 | [`SupplyChainEngine.inventory_overview`](../backend/app/engine.py#L337) | method |  | used | [annotated](../code_explorer/02_business_logic/aurelia_engine/app_engine.py) |  |
| F0206 | [`SupplyChainEngine.sales_order_fulfilment`](../backend/app/engine.py#L363) | method |  | used | [annotated](../code_explorer/02_business_logic/aurelia_engine/app_engine.py) | Allocate warehouse stock (+ inbound arriving before each requested date) to open orders by |
| F0207 | [`SupplyChainEngine.stocktake_reconciliation`](../backend/app/engine.py#L423) | method |  | used | [annotated](../code_explorer/02_business_logic/aurelia_engine/app_engine.py) | Explain each count difference from unposted goods movements, quality decisions and expiry; |
| F0208 | [`SupplyChainEngine.production_overview`](../backend/app/engine.py#L471) | method |  | used | [annotated](../code_explorer/02_business_logic/aurelia_engine/app_engine.py) |  |
| F0209 | [`SupplyChainEngine.forecast_vs_actuals`](../backend/app/engine.py#L480) | method |  | used | [annotated](../code_explorer/02_business_logic/aurelia_engine/app_engine.py) |  |
| F0210 | [`SupplyChainEngine.position_health`](../backend/app/engine.py#L498) | method |  | used | [annotated](../code_explorer/02_business_logic/aurelia_engine/app_engine.py) | Coverage of every stocked position against its target: finished goods at DCs (demand x hor |
| F0211 | [`SupplyChainEngine.products`](../backend/app/engine.py#L547) | method |  | used | [annotated](../code_explorer/02_business_logic/aurelia_engine/app_engine.py) |  |
| F0212 | [`SupplyChainEngine.product_360`](../backend/app/engine.py#L556) | method |  | used | [annotated](../code_explorer/02_business_logic/aurelia_engine/app_engine.py) | Everything about one finished good: stock by DC, sales, projected end of stock, component  |
| F0213 | [`SupplyChainEngine.product_brief`](../backend/app/engine.py#L812) | method |  | used | [annotated](../code_explorer/02_business_logic/aurelia_engine/app_engine.py) | One-screen product brief: supply status, reserve above safety stock, time to out-of-stock  |
| F0214 | [`SupplyChainEngine.product_brief.add`](../backend/app/engine.py#L831) | nested |  | used | [annotated](../code_explorer/02_business_logic/aurelia_engine/app_engine.py) |  |
| F0215 | [`SupplyChainEngine.product_brief.qty`](../backend/app/engine.py#L874) | nested |  | used | [annotated](../code_explorer/02_business_logic/aurelia_engine/app_engine.py) |  |
| F0216 | [`SupplyChainEngine.product_brief.when`](../backend/app/engine.py#L877) | nested |  | used | [annotated](../code_explorer/02_business_logic/aurelia_engine/app_engine.py) |  |
| F0217 | [`SupplyChainEngine.product_brief.by`](../backend/app/engine.py#L880) | nested |  | used | [annotated](../code_explorer/02_business_logic/aurelia_engine/app_engine.py) |  |
| F0218 | [`SupplyChainEngine.product_brief.level`](../backend/app/engine.py#L941) | nested |  | used | [annotated](../code_explorer/02_business_logic/aurelia_engine/app_engine.py) |  |
| F0219 | [`SupplyChainEngine.supplier_lead_time`](../backend/app/engine.py#L969) | method |  | used | [annotated](../code_explorer/02_business_logic/aurelia_engine/app_engine.py) | Empirical lead-time forecast from SAP receipt history (promised vs received dates), never  |
| F0220 | [`SupplyChainEngine.sales_outlook`](../backend/app/engine.py#L996) | method |  | used | [annotated](../code_explorer/02_business_logic/aurelia_engine/app_engine.py) | Current sales rates per product and DC (last 7 / 28 days vs the 14-day forecast) and a cal |
| F0221 | [`SupplyChainEngine.sites`](../backend/app/engine.py#L1048) | method |  | used | [annotated](../code_explorer/02_business_logic/aurelia_engine/app_engine.py) |  |
| F0222 | [`SupplyChainEngine.site_360`](../backend/app/engine.py#L1058) | method |  | used | [annotated](../code_explorer/02_business_logic/aurelia_engine/app_engine.py) |  |
| F0223 | [`SupplyChainEngine.supplier_tier`](../backend/app/engine.py#L1122) | method |  | used | [annotated](../code_explorer/02_business_logic/aurelia_engine/app_engine.py) | local = same country as the plant; regional = same geographic zone; international = otherw |
| F0224 | [`SupplyChainEngine.network_map`](../backend/app/engine.py#L1129) | method |  | used | [annotated](../code_explorer/02_business_logic/aurelia_engine/app_engine.py) |  |
| F0225 | [`SupplyChainEngine.expiry_risk`](../backend/app/engine.py#L1211) | method |  | used | [annotated](../code_explorer/02_business_logic/aurelia_engine/app_engine.py) |  |
| F0226 | [`SupplyChainEngine.kpis`](../backend/app/engine.py#L1223) | method |  | used | [annotated](../code_explorer/02_business_logic/aurelia_engine/app_engine.py) |  |

## backend/app/forecasting.py

Small deterministic training pipeline using XGBoost for the POC demand forecast.

| ID | Function | Kind | FastAPI route | Status | Annotated | Summary |
|---|---|---|---|---|---|---|
| F0524 | [`_history`](../backend/app/forecasting.py#L10) | function |  | used | [annotated](../code_explorer/04_ai_ml/forecasting/app_forecasting.py) |  |
| F0525 | [`_features`](../backend/app/forecasting.py#L16) | function |  | used | [annotated](../code_explorer/04_ai_ml/forecasting/app_forecasting.py) |  |
| F0526 | [`_fit_predict`](../backend/app/forecasting.py#L28) | function |  | used | [annotated](../code_explorer/04_ai_ml/forecasting/app_forecasting.py) |  |
| F0527 | [`backtest`](../backend/app/forecasting.py#L40) | function |  | used | [annotated](../code_explorer/04_ai_ml/forecasting/app_forecasting.py) | Forecast vs actuals: train without the last `holdout_days`, predict them, then forecast th |
| F0528 | [`_errors`](../backend/app/forecasting.py#L62) | function |  | used | [annotated](../code_explorer/04_ai_ml/forecasting/app_forecasting.py) |  |
| F0529 | [`evaluate_models`](../backend/app/forecasting.py#L69) | function |  | used | [annotated](../code_explorer/04_ai_ml/forecasting/app_forecasting.py) | Model quality on the same holdout: XGBoost vs a seasonal-naive baseline (same weekday last |
| F0530 | [`pooled_evaluation`](../backend/app/forecasting.py#L91) | function |  | used | [annotated](../code_explorer/04_ai_ml/forecasting/app_forecasting.py) | Train one model on demand-normalised series from several customers and score it on the tar |
| F0531 | [`forecast`](../backend/app/forecasting.py#L129) | function |  | used | [annotated](../code_explorer/04_ai_ml/forecasting/app_forecasting.py) |  |

## backend/app/graphs.py

LangGraph Chat Graph and Business Graph (exposed to LangGraph Server / LangSmith Studio by langgraph.json).

| ID | Function | Kind | FastAPI route | Status | Annotated | Summary |
|---|---|---|---|---|---|---|
| F0573 | [`_last_text`](../backend/app/graphs.py#L51) | function |  | used | [annotated](../code_explorer/04_ai_ml/langgraph/app_graphs.py) |  |
| F0574 | [`guard`](../backend/app/graphs.py#L55) | function |  | used | [annotated](../code_explorer/04_ai_ml/langgraph/app_graphs.py) |  |
| F0575 | [`route_after_guard`](../backend/app/graphs.py#L59) | function |  | used | [annotated](../code_explorer/04_ai_ml/langgraph/app_graphs.py) |  |
| F0576 | [`refuse`](../backend/app/graphs.py#L65) | function |  | used | [annotated](../code_explorer/04_ai_ml/langgraph/app_graphs.py) |  |
| F0577 | [`_tool_rounds`](../backend/app/graphs.py#L69) | function |  | used | [annotated](../code_explorer/04_ai_ml/langgraph/app_graphs.py) |  |
| F0578 | [`ChatState`](../backend/app/graphs.py#L79) | class |  | used | [annotated](../code_explorer/04_ai_ml/langgraph/app_graphs.py) |  |
| F0579 | [`_role_setup`](../backend/app/graphs.py#L83) | function |  | used | [annotated](../code_explorer/04_ai_ml/langgraph/app_graphs.py) | System prompt and tool set for the role's specialised agent; no role = the general copilot |
| F0580 | [`agent`](../backend/app/graphs.py#L95) | function |  | used | [annotated](../code_explorer/04_ai_ml/langgraph/app_graphs.py) |  |
| F0581 | [`_first_human`](../backend/app/graphs.py#L109) | function |  | used | [annotated](../code_explorer/04_ai_ml/langgraph/app_graphs.py) |  |
| F0582 | [`route_after_agent`](../backend/app/graphs.py#L116) | function |  | used | [annotated](../code_explorer/04_ai_ml/langgraph/app_graphs.py) |  |
| F0583 | [`fallback_answer`](../backend/app/graphs.py#L121) | function |  | used | [annotated](../code_explorer/04_ai_ml/langgraph/app_graphs.py) | Deterministic keyword router used when no LLM is configured; it only restates engine outpu |
| F0584 | [`fallback`](../backend/app/graphs.py#L149) | function |  | used | [annotated](../code_explorer/04_ai_ml/langgraph/app_graphs.py) |  |
| F0585 | [`traced`](../backend/app/graphs.py#L167) | function |  | used | [annotated](../code_explorer/04_ai_ml/langgraph/app_graphs.py) | Attach Langfuse tracing to a compiled graph (still a Pregel graph, so LangGraph Server acc |
| F0586 | [`BusinessState`](../backend/app/graphs.py#L180) | class |  | used | [annotated](../code_explorer/04_ai_ml/langgraph/app_graphs.py) |  |
| F0587 | [`ExtractedRequest`](../backend/app/graphs.py#L202) | pydantic_model |  | used | [annotated](../code_explorer/04_ai_ml/langgraph/app_graphs.py) | Structured parameters for a supply-chain request. Leave a field empty when it is not state |
| F0588 | [`_regex_extract`](../backend/app/graphs.py#L214) | function |  | used | [annotated](../code_explorer/04_ai_ml/langgraph/app_graphs.py) |  |
| F0589 | [`intake`](../backend/app/graphs.py#L248) | function |  | used | [annotated](../code_explorer/04_ai_ml/langgraph/app_graphs.py) | Fill missing parameters from free text: Qwen structured output, deterministic regex as fal |
| F0590 | [`validate`](../backend/app/graphs.py#L271) | function |  | used | [annotated](../code_explorer/04_ai_ml/langgraph/app_graphs.py) |  |
| F0591 | [`route_workflow`](../backend/app/graphs.py#L299) | function |  | used | [annotated](../code_explorer/04_ai_ml/langgraph/app_graphs.py) |  |
| F0592 | [`run_factory`](../backend/app/graphs.py#L303) | function |  | used | [annotated](../code_explorer/04_ai_ml/langgraph/app_graphs.py) |  |
| F0593 | [`run_balance`](../backend/app/graphs.py#L308) | function |  | used | [annotated](../code_explorer/04_ai_ml/langgraph/app_graphs.py) |  |
| F0594 | [`run_supplier`](../backend/app/graphs.py#L313) | function |  | used | [annotated](../code_explorer/04_ai_ml/langgraph/app_graphs.py) |  |
| F0595 | [`run_quality`](../backend/app/graphs.py#L318) | function |  | used | [annotated](../code_explorer/04_ai_ml/langgraph/app_graphs.py) |  |
| F0596 | [`run_logistics`](../backend/app/graphs.py#L323) | function |  | used | [annotated](../code_explorer/04_ai_ml/langgraph/app_graphs.py) |  |
| F0597 | [`run_inventory`](../backend/app/graphs.py#L328) | function |  | used | [annotated](../code_explorer/04_ai_ml/langgraph/app_graphs.py) |  |
| F0598 | [`policy_context`](../backend/app/graphs.py#L343) | function |  | used | [annotated](../code_explorer/04_ai_ml/langgraph/app_graphs.py) |  |
| F0599 | [`explain`](../backend/app/graphs.py#L350) | function |  | used | [annotated](../code_explorer/04_ai_ml/langgraph/app_graphs.py) |  |
| F0600 | [`needs_approval`](../backend/app/graphs.py#L372) | function |  | used | [annotated](../code_explorer/04_ai_ml/langgraph/app_graphs.py) |  |
| F0601 | [`approval_gate`](../backend/app/graphs.py#L376) | function |  | used | [annotated](../code_explorer/04_ai_ml/langgraph/app_graphs.py) | Human-in-the-loop: the planner decides whether the advisory recommendation goes to the man |
| F0602 | [`route_approval`](../backend/app/graphs.py#L395) | function |  | used | [annotated](../code_explorer/04_ai_ml/langgraph/app_graphs.py) |  |
| F0603 | [`submit`](../backend/app/graphs.py#L399) | function |  | used | [annotated](../code_explorer/04_ai_ml/langgraph/app_graphs.py) |  |
| F0604 | [`discard`](../backend/app/graphs.py#L406) | function |  | used | [annotated](../code_explorer/04_ai_ml/langgraph/app_graphs.py) |  |
| F0605 | [`no_action`](../backend/app/graphs.py#L410) | function |  | used | [annotated](../code_explorer/04_ai_ml/langgraph/app_graphs.py) |  |
| F0606 | [`rejected`](../backend/app/graphs.py#L414) | function |  | used | [annotated](../code_explorer/04_ai_ml/langgraph/app_graphs.py) |  |

## backend/app/insights.py

Automatic insights in plain English and personalised watches (subscriptions).

| ID | Function | Kind | FastAPI route | Status | Annotated | Summary |
|---|---|---|---|---|---|---|
| F0243 | [`_id`](../backend/app/insights.py#L15) | function |  | used | [annotated](../code_explorer/02_business_logic/aurelia_views/app_insights.py) |  |
| F0244 | [`InsightEngine`](../backend/app/insights.py#L19) | class |  | used | [annotated](../code_explorer/02_business_logic/aurelia_views/app_insights.py) |  |
| F0245 | [`InsightEngine.__init__`](../backend/app/insights.py#L20) | method |  | used (framework) | [annotated](../code_explorer/02_business_logic/aurelia_views/app_insights.py) |  |
| F0246 | [`InsightEngine._plant`](../backend/app/insights.py#L24) | method |  | used | [annotated](../code_explorer/02_business_logic/aurelia_views/app_insights.py) |  |
| F0247 | [`InsightEngine._mat`](../backend/app/insights.py#L27) | method |  | used | [annotated](../code_explorer/02_business_logic/aurelia_views/app_insights.py) |  |
| F0248 | [`InsightEngine.insights`](../backend/app/insights.py#L30) | method |  | used | [annotated](../code_explorer/02_business_logic/aurelia_views/app_insights.py) |  |
| F0249 | [`InsightEngine.evaluate`](../backend/app/insights.py#L133) | method |  | used | [annotated](../code_explorer/02_business_logic/aurelia_views/app_insights.py) |  |

## backend/app/llm.py

Qwen through an OpenAI-compatible endpoint: vLLM on a cloud GPU, Ollama on a local workstation.

| ID | Function | Kind | FastAPI route | Status | Annotated | Summary |
|---|---|---|---|---|---|---|
| F0728 | [`chat_model`](../backend/app/llm.py#L18) | function |  | used | [annotated](../code_explorer/04_ai_ml/llm/app_llm.py) |  |
| F0729 | [`llm_health`](../backend/app/llm.py#L30) | function |  | used | [annotated](../code_explorer/04_ai_ml/llm/app_llm.py) |  |
| F0730 | [`deterministic_summary`](../backend/app/llm.py#L45) | function |  | used | [annotated](../code_explorer/04_ai_ml/llm/app_llm.py) | Template answer used when the LLM is disabled or unreachable; it only restates engine outp |

## backend/app/main.py

the SPARC / Aurelia FastAPI gateway (port 8000): one create_app() factory registers middleware

| ID | Function | Kind | FastAPI route | Status | Annotated | Summary |
|---|---|---|---|---|---|---|
| F0016 | [`_expectation`](../backend/app/main.py#L71) | function |  | used | [annotated](../code_explorer/01_fastapi/endpoints/app_main.py) | Plain-language expected result of one executed action (what the outcome check will look fo |
| F0017 | [`create_app`](../backend/app/main.py#L81) | function |  | used | [annotated](../code_explorer/01_fastapi/endpoints/app_main.py) |  |
| F0018 | [`create_app.request_context`](../backend/app/main.py#L112) | nested |  | used | [annotated](../code_explorer/01_fastapi/endpoints/app_main.py) |  |
| F0019 | [`create_app.principal`](../backend/app/main.py#L132) | nested |  | used | [annotated](../code_explorer/01_fastapi/endpoints/app_main.py) |  |
| F0020 | [`create_app.manager`](../backend/app/main.py#L147) | nested |  | used | [annotated](../code_explorer/01_fastapi/endpoints/app_main.py) |  |
| F0021 | [`create_app.reader`](../backend/app/main.py#L155) | nested |  | used | [annotated](../code_explorer/01_fastapi/endpoints/app_main.py) |  |
| F0022 | [`create_app.watch_owner`](../backend/app/main.py#L158) | nested |  | used | [annotated](../code_explorer/01_fastapi/endpoints/app_main.py) |  |
| F0023 | [`create_app.save`](../backend/app/main.py#L161) | nested |  | used | [annotated](../code_explorer/01_fastapi/endpoints/app_main.py) |  |
| F0024 | [`create_app.value_error_handler`](../backend/app/main.py#L173) | nested |  | used | [annotated](../code_explorer/01_fastapi/endpoints/app_main.py) |  |
| F0025 | [`create_app.health`](../backend/app/main.py#L178) | route | GET /health | used | [annotated](../code_explorer/01_fastapi/endpoints/app_main.py) |  |
| F0026 | [`create_app.ready`](../backend/app/main.py#L182) | route | GET /ready | used | [annotated](../code_explorer/01_fastapi/endpoints/app_main.py) |  |
| F0027 | [`create_app.metrics`](../backend/app/main.py#L186) | route | GET /metrics | used | [annotated](../code_explorer/01_fastapi/endpoints/app_main.py) |  |
| F0028 | [`create_app.public_config`](../backend/app/main.py#L190) | route | GET /api/v1/config/public | used | [annotated](../code_explorer/01_fastapi/endpoints/app_main.py) | Non-secret links for the dashboard header. |
| F0029 | [`create_app.demo_session`](../backend/app/main.py#L220) | route | GET /api/v1/demo/session | used | [annotated](../code_explorer/01_fastapi/endpoints/app_main.py) | Local demo only (DEMO_AUTO_LOGIN=true): returns the demo planner and manager keys so the U |
| F0030 | [`create_app._public`](../backend/app/main.py#L229) | nested |  | used | [annotated](../code_explorer/01_fastapi/endpoints/app_main.py) |  |
| F0031 | [`create_app.status`](../backend/app/main.py#L232) | route | GET /api/v1/status | used | [annotated](../code_explorer/01_fastapi/endpoints/app_main.py) |  |
| F0032 | [`create_app.status.probe`](../backend/app/main.py#L236) | nested |  | used | [annotated](../code_explorer/01_fastapi/endpoints/app_main.py) |  |
| F0033 | [`create_app.snapshot`](../backend/app/main.py#L268) | route | GET /api/v1/snapshot | used | [annotated](../code_explorer/01_fastapi/endpoints/app_main.py) |  |
| F0034 | [`create_app.tenant_catalogue`](../backend/app/main.py#L281) | route | GET /api/v1/tenants | used | [annotated](../code_explorer/01_fastapi/endpoints/app_main.py) | Industries and customers for the top-bar selector (send the id back as the X-Tenant header |
| F0035 | [`create_app.network_map`](../backend/app/main.py#L286) | route | GET /api/v1/network/map | used | [annotated](../code_explorer/01_fastapi/endpoints/app_main.py) |  |
| F0036 | [`create_app.sap_metadata`](../backend/app/main.py#L291) | route | GET /sap/opu/odata/sap/ZSCM_COPILOT_SRV/$metadata | used | [annotated](../code_explorer/01_fastapi/endpoints/app_main.py) |  |
| F0037 | [`create_app.sap_sandbox_documents`](../backend/app/main.py#L296) | route | GET /sap/opu/odata/sap/ZSCM_COPILOT_SRV/A_SandboxDocument | used | [annotated](../code_explorer/01_fastapi/endpoints/app_main.py) |  |
| F0038 | [`create_app.sap_odata`](../backend/app/main.py#L302) | route | GET /sap/opu/odata/sap/ZSCM_COPILOT_SRV/{entity} | used | [annotated](../code_explorer/01_fastapi/endpoints/app_main.py) |  |
| F0039 | [`create_app.block_sap_write`](../backend/app/main.py#L317) | route | POST/PUT/PATCH/DELETE /sap/opu/odata/sap/{path:path} | used | [annotated](../code_explorer/01_fastapi/endpoints/app_main.py) |  |
| F0040 | [`create_app.factory_readiness`](../backend/app/main.py#L324) | route | POST /api/v1/analysis/factory-readiness | used | [annotated](../code_explorer/01_fastapi/endpoints/app_main.py) |  |
| F0041 | [`create_app.stock_balance`](../backend/app/main.py#L329) | route | POST /api/v1/analysis/stock-balance | used | [annotated](../code_explorer/01_fastapi/endpoints/app_main.py) |  |
| F0042 | [`create_app.demand_forecast`](../backend/app/main.py#L333) | route | POST /api/v1/analysis/forecast | used | [annotated](../code_explorer/01_fastapi/endpoints/app_main.py) |  |
| F0043 | [`create_app.what_if`](../backend/app/main.py#L337) | route | POST /api/v1/analysis/what-if | used | [annotated](../code_explorer/01_fastapi/endpoints/app_main.py) |  |
| F0044 | [`create_app.supplier_risk`](../backend/app/main.py#L342) | route | POST /api/v1/analysis/supplier-risk | used | [annotated](../code_explorer/01_fastapi/endpoints/app_main.py) |  |
| F0045 | [`create_app.quality`](../backend/app/main.py#L346) | route | POST /api/v1/analysis/quality | used | [annotated](../code_explorer/01_fastapi/endpoints/app_main.py) |  |
| F0046 | [`create_app.logistics`](../backend/app/main.py#L350) | route | POST /api/v1/analysis/logistics | used | [annotated](../code_explorer/01_fastapi/endpoints/app_main.py) |  |
| F0047 | [`create_app.sales_orders`](../backend/app/main.py#L354) | route | POST /api/v1/analysis/sales-orders | used | [annotated](../code_explorer/01_fastapi/endpoints/app_main.py) |  |
| F0048 | [`create_app.stocktake`](../backend/app/main.py#L358) | route | POST /api/v1/analysis/stocktake | used | [annotated](../code_explorer/01_fastapi/endpoints/app_main.py) |  |
| F0049 | [`create_app.forecast_vs_actuals`](../backend/app/main.py#L362) | route | GET /api/v1/analysis/forecast-vs-actuals | used | [annotated](../code_explorer/01_fastapi/endpoints/app_main.py) |  |
| F0050 | [`create_app.production_overview`](../backend/app/main.py#L367) | route | GET /api/v1/production/overview | used | [annotated](../code_explorer/01_fastapi/endpoints/app_main.py) |  |
| F0051 | [`create_app.products`](../backend/app/main.py#L372) | route | GET /api/v1/products | used | [annotated](../code_explorer/01_fastapi/endpoints/app_main.py) |  |
| F0052 | [`create_app.product`](../backend/app/main.py#L377) | route | GET /api/v1/products/{material} | used | [annotated](../code_explorer/01_fastapi/endpoints/app_main.py) |  |
| F0053 | [`create_app.role_catalogue`](../backend/app/main.py#L383) | route | GET /api/v1/roles | used | [annotated](../code_explorer/01_fastapi/endpoints/app_main.py) |  |
| F0054 | [`create_app.role_view`](../backend/app/main.py#L388) | route | GET /api/v1/roles/{role} | used | [annotated](../code_explorer/01_fastapi/endpoints/app_main.py) |  |
| F0055 | [`create_app.north_star`](../backend/app/main.py#L395) | route | GET /api/v1/northstar | used | [annotated](../code_explorer/01_fastapi/endpoints/app_main.py) |  |
| F0056 | [`create_app.learning`](../backend/app/main.py#L400) | route | GET /api/v1/learning | used | [annotated](../code_explorer/01_fastapi/endpoints/app_main.py) |  |
| F0057 | [`create_app.moat_view`](../backend/app/main.py#L405) | route | GET /api/v1/moat | used | [annotated](../code_explorer/01_fastapi/endpoints/app_main.py) | Customer data intelligence flywheel, moat evidence, consent gate and the five moat-strengt |
| F0058 | [`create_app.moat_consent`](../backend/app/main.py#L411) | route | POST /api/v1/moat/consent | used | [annotated](../code_explorer/01_fastapi/endpoints/app_main.py) | The customer decides whether its data may contribute to industry learning (manager only, a |
| F0059 | [`create_app.record_outcome`](../backend/app/main.py#L419) | route | POST /api/v1/recommendations/{recommendation_id}/outcome | used | [annotated](../code_explorer/01_fastapi/endpoints/app_main.py) | Record the real result of an executed recommendation against an SAP document (decision out |
| F0060 | [`create_app.sales_outlook`](../backend/app/main.py#L433) | route | GET /api/v1/sales/outlook | used | [annotated](../code_explorer/01_fastapi/endpoints/app_main.py) |  |
| F0061 | [`create_app.product_brief`](../backend/app/main.py#L438) | route | GET /api/v1/products/{material}/brief | used | [annotated](../code_explorer/01_fastapi/endpoints/app_main.py) |  |
| F0062 | [`create_app.sites`](../backend/app/main.py#L443) | route | GET /api/v1/sites | used | [annotated](../code_explorer/01_fastapi/endpoints/app_main.py) |  |
| F0063 | [`create_app.site`](../backend/app/main.py#L448) | route | GET /api/v1/sites/{code} | used | [annotated](../code_explorer/01_fastapi/endpoints/app_main.py) |  |
| F0064 | [`create_app.dashboards_list`](../backend/app/main.py#L453) | route | GET /api/v1/dashboards | used | [annotated](../code_explorer/01_fastapi/endpoints/app_main.py) |  |
| F0065 | [`create_app.dashboard`](../backend/app/main.py#L457) | route | GET /api/v1/dashboards/{persona} | used | [annotated](../code_explorer/01_fastapi/endpoints/app_main.py) |  |
| F0066 | [`create_app.get_insights`](../backend/app/main.py#L462) | route | GET /api/v1/insights | used | [annotated](../code_explorer/01_fastapi/endpoints/app_main.py) |  |
| F0067 | [`create_app.watch_kinds`](../backend/app/main.py#L470) | route | GET /api/v1/watches/kinds | used | [annotated](../code_explorer/01_fastapi/endpoints/app_main.py) |  |
| F0068 | [`create_app.list_watches`](../backend/app/main.py#L474) | route | GET /api/v1/watches | used | [annotated](../code_explorer/01_fastapi/endpoints/app_main.py) |  |
| F0069 | [`create_app.create_watch`](../backend/app/main.py#L478) | route | POST /api/v1/watches | used | [annotated](../code_explorer/01_fastapi/endpoints/app_main.py) |  |
| F0070 | [`create_app.delete_watch`](../backend/app/main.py#L488) | route | DELETE /api/v1/watches/{watch_id} | used | [annotated](../code_explorer/01_fastapi/endpoints/app_main.py) |  |
| F0071 | [`create_app.evaluate_watches`](../backend/app/main.py#L494) | route | POST /api/v1/watches/evaluate | used | [annotated](../code_explorer/01_fastapi/endpoints/app_main.py) |  |
| F0072 | [`create_app.get_analysis`](../backend/app/main.py#L504) | route | GET /api/v1/analyses/{analysis_id} | used | [annotated](../code_explorer/01_fastapi/endpoints/app_main.py) |  |
| F0073 | [`create_app.inventory`](../backend/app/main.py#L512) | route | GET /api/v1/inventory | used | [annotated](../code_explorer/01_fastapi/endpoints/app_main.py) |  |
| F0074 | [`create_app.supplier_scorecard`](../backend/app/main.py#L517) | route | GET /api/v1/suppliers/scorecard | used | [annotated](../code_explorer/01_fastapi/endpoints/app_main.py) |  |
| F0075 | [`create_app.kpis`](../backend/app/main.py#L522) | route | GET /api/v1/kpis | used | [annotated](../code_explorer/01_fastapi/endpoints/app_main.py) |  |
| F0076 | [`create_app.rag_search`](../backend/app/main.py#L528) | route | POST /api/v1/rag/search | used | [annotated](../code_explorer/01_fastapi/endpoints/app_main.py) |  |
| F0077 | [`create_app.rag_search_get`](../backend/app/main.py#L533) | route | GET /api/v1/rag/search | used | [annotated](../code_explorer/01_fastapi/endpoints/app_main.py) | Same search via query parameters — used by the Flowise AgentFlow RAG step (no JSON escapin |
| F0078 | [`create_app.embeddings`](../backend/app/main.py#L541) | route | POST /v1/embeddings | used | [annotated](../code_explorer/01_fastapi/endpoints/app_main.py) | Lets Flowise (OpenAI Embeddings Custom node) index and query with exactly the embedding mo |
| F0079 | [`create_app.embeddings.encode`](../backend/app/main.py#L550) | nested |  | used | [annotated](../code_explorer/01_fastapi/endpoints/app_main.py) |  |
| F0080 | [`create_app.rag_stats`](../backend/app/main.py#L558) | route | GET /api/v1/rag/stats | used | [annotated](../code_explorer/01_fastapi/endpoints/app_main.py) |  |
| F0081 | [`create_app.rag_add`](../backend/app/main.py#L563) | route | POST /api/v1/rag/documents | used | [annotated](../code_explorer/01_fastapi/endpoints/app_main.py) |  |
| F1801 | [`create_app.rag_tuning_proxy`](../backend/app/main.py#L570) | route | GET/POST/PUT /api/v1/rag-tuning/{path:path} | used | [annotated](../code_explorer/01_fastapi/endpoints/app_main.py) |  |
| F0985 | [`create_app.code_functions`](../backend/app/main.py#L584) | route | GET /api/v1/code/functions | used | [annotated](../code_explorer/01_fastapi/endpoints/app_main.py) |  |
| F0986 | [`create_app.code_function`](../backend/app/main.py#L589) | route | GET /api/v1/code/function | used | [annotated](../code_explorer/01_fastapi/endpoints/app_main.py) |  |
| F0987 | [`create_app.code_update`](../backend/app/main.py#L597) | route | PUT /api/v1/code/function | used | [annotated](../code_explorer/01_fastapi/endpoints/app_main.py) |  |
| F0082 | [`create_app._graph_call`](../backend/app/main.py#L610) | nested |  | used | [annotated](../code_explorer/01_fastapi/endpoints/app_main.py) |  |
| F0083 | [`create_app.chat`](../backend/app/main.py#L618) | route | POST /api/v1/chat | used | [annotated](../code_explorer/01_fastapi/endpoints/app_main.py) |  |
| F0084 | [`create_app._agentflow_view`](../backend/app/main.py#L645) | nested |  | used | [annotated](../code_explorer/01_fastapi/endpoints/app_main.py) |  |
| F0085 | [`create_app.langgraph_agentflow`](../backend/app/main.py#L669) | route | POST /api/v1/langgraph/agentflow | used | [annotated](../code_explorer/01_fastapi/endpoints/app_main.py) |  |
| F0086 | [`create_app.langgraph_agentflow_resume`](../backend/app/main.py#L676) | route | POST /api/v1/langgraph/agentflow/{thread_id}/resume | used | [annotated](../code_explorer/01_fastapi/endpoints/app_main.py) |  |
| F0087 | [`create_app.business_start`](../backend/app/main.py#L682) | route | POST /api/v1/workflows/business | used | [annotated](../code_explorer/01_fastapi/endpoints/app_main.py) |  |
| F0088 | [`create_app.business_resume`](../backend/app/main.py#L689) | route | POST /api/v1/workflows/business/{thread_id}/resume | used | [annotated](../code_explorer/01_fastapi/endpoints/app_main.py) |  |
| F0089 | [`create_app.current_harness`](../backend/app/main.py#L702) | nested |  | used | [annotated](../code_explorer/01_fastapi/endpoints/app_main.py) |  |
| F0090 | [`create_app.deep_harness`](../backend/app/main.py#L706) | route | GET /api/v1/deep-agents/harness | used | [annotated](../code_explorer/01_fastapi/endpoints/app_main.py) |  |
| F0091 | [`create_app.set_deep_harness`](../backend/app/main.py#L715) | route | PUT /api/v1/deep-agents/harness | used | [annotated](../code_explorer/01_fastapi/endpoints/app_main.py) |  |
| F0092 | [`create_app.supplier_research`](../backend/app/main.py#L721) | route | POST /api/v1/deep-agents/supplier-research | used | [annotated](../code_explorer/01_fastapi/endpoints/app_main.py) |  |
| F0093 | [`create_app._flow_id`](../backend/app/main.py#L745) | nested |  | used | [annotated](../code_explorer/01_fastapi/endpoints/app_main.py) |  |
| F0094 | [`create_app.flowise_predict`](../backend/app/main.py#L759) | route | POST /api/v1/flowise/{flow}/predict | used | [annotated](../code_explorer/01_fastapi/endpoints/app_main.py) |  |
| F0095 | [`create_app.submit_recommendation`](../backend/app/main.py#L797) | route | POST /api/v1/recommendations | used | [annotated](../code_explorer/01_fastapi/endpoints/app_main.py) |  |
| F0096 | [`create_app.submit_from_agent`](../backend/app/main.py#L806) | route | POST /api/v1/recommendations/from-agent | used | [annotated](../code_explorer/01_fastapi/endpoints/app_main.py) |  |
| F0097 | [`create_app.recommendations`](../backend/app/main.py#L821) | route | GET /api/v1/recommendations | used | [annotated](../code_explorer/01_fastapi/endpoints/app_main.py) |  |
| F0098 | [`create_app.decide`](../backend/app/main.py#L826) | route | POST /api/v1/recommendations/{recommendation_id}/decision | used | [annotated](../code_explorer/01_fastapi/endpoints/app_main.py) |  |
| F0099 | [`create_app.execute`](../backend/app/main.py#L840) | route | POST /api/v1/recommendations/{recommendation_id}/execute | used | [annotated](../code_explorer/01_fastapi/endpoints/app_main.py) | 1-click execution of an ACCEPTED recommendation into the SAP sandbox (manager only; agents |
| F0100 | [`create_app.sap_documents`](../backend/app/main.py#L867) | route | GET /api/v1/sap/documents | used | [annotated](../code_explorer/01_fastapi/endpoints/app_main.py) |  |
| F0101 | [`create_app.audit`](../backend/app/main.py#L872) | route | GET /api/v1/audit | used | [annotated](../code_explorer/01_fastapi/endpoints/app_main.py) |  |
| F0102 | [`create_app.poc_sap_inventory`](../backend/app/main.py#L881) | route | GET /sap/inventory | used | [annotated](../code_explorer/01_fastapi/endpoints/app_main.py) |  |
| F0103 | [`create_app.poc_sap_production_orders`](../backend/app/main.py#L887) | route | GET /sap/production-orders | used | [annotated](../code_explorer/01_fastapi/endpoints/app_main.py) |  |
| F0104 | [`create_app.poc_forecast_demand`](../backend/app/main.py#L893) | route | POST /forecast/demand | used | [annotated](../code_explorer/01_fastapi/endpoints/app_main.py) |  |
| F0105 | [`create_app.poc_forecast_lead_time`](../backend/app/main.py#L897) | route | POST /forecast/supplier-lead-time | used | [annotated](../code_explorer/01_fastapi/endpoints/app_main.py) |  |
| F0106 | [`create_app.poc_material_readiness`](../backend/app/main.py#L901) | route | POST /optimizer/material-readiness | used | [annotated](../code_explorer/01_fastapi/endpoints/app_main.py) |  |
| F0107 | [`create_app.poc_warehouse_transfer`](../backend/app/main.py#L906) | route | POST /optimizer/warehouse-transfer | used | [annotated](../code_explorer/01_fastapi/endpoints/app_main.py) |  |
| F0108 | [`create_app.poc_decisions`](../backend/app/main.py#L910) | route | POST /decisions | used | [annotated](../code_explorer/01_fastapi/endpoints/app_main.py) |  |
| F0109 | [`create_app.poc_human_review`](../backend/app/main.py#L914) | route | POST /decisions/{decision_id}/human-review | used | [annotated](../code_explorer/01_fastapi/endpoints/app_main.py) |  |
| F0110 | [`create_app.poc_reconcile`](../backend/app/main.py#L918) | route | POST /outcomes/reconcile | used | [annotated](../code_explorer/01_fastapi/endpoints/app_main.py) |  |
| F0111 | [`create_app.poc_model_performance`](../backend/app/main.py#L944) | route | GET /learning/model-performance | used | [annotated](../code_explorer/01_fastapi/endpoints/app_main.py) |  |

## backend/app/mcp_server.py

Restricted MCP server (Streamable HTTP) exposing read-only SAP, analytics and RAG tools.

| ID | Function | Kind | FastAPI route | Status | Annotated | Summary |
|---|---|---|---|---|---|---|
| F0485 | [`_dump`](../backend/app/mcp_server.py#L29) | function |  | used | [annotated](../code_explorer/04_ai_ml/agent_tools/app_mcp_server.py) |  |
| F0486 | [`sap_snapshot`](../backend/app/mcp_server.py#L36) | function |  | used | [annotated](../code_explorer/04_ai_ml/agent_tools/app_mcp_server.py) | SAP snapshot provenance and valid plant, material and supplier codes. Call first. |
| F0487 | [`factory_material_readiness`](../backend/app/mcp_server.py#L42) | function |  | used | [annotated](../code_explorer/04_ai_ml/agent_tools/app_mcp_server.py) | BOM material readiness for a production run (plant FR10/FR20/TPM1, finished good code, uni |
| F0488 | [`warehouse_stock_balance`](../backend/app/mcp_server.py#L48) | function |  | used | [annotated](../code_explorer/04_ai_ml/agent_tools/app_mcp_server.py) | XGBoost demand forecast and OR-Tools transfer proposals across DC01, DC21 and DC22 for one |
| F0489 | [`supplier_risk`](../backend/app/mcp_server.py#L54) | function |  | used | [annotated](../code_explorer/04_ai_ml/agent_tools/app_mcp_server.py) | Supplier scorecard: OTIF, delays, quality rejects, open PO exposure and single-source risk |
| F0490 | [`quality_status`](../backend/app/mcp_server.py#L60) | function |  | used | [annotated](../code_explorer/04_ai_ml/agent_tools/app_mcp_server.py) | Open inspection lots, blocked/expired batches and affected production orders. |
| F0491 | [`logistics_status`](../backend/app/mcp_server.py#L66) | function |  | used | [annotated](../code_explorer/04_ai_ml/agent_tools/app_mcp_server.py) | In-transit shipments, delays, revised ETAs and escalations. |
| F0492 | [`inventory_overview`](../backend/app/mcp_server.py#L72) | function |  | used | [annotated](../code_explorer/04_ai_ml/agent_tools/app_mcp_server.py) | Finished-goods stock, days of cover, open sales orders and in-transit stock by warehouse. |
| F0493 | [`sales_order_fulfilment`](../backend/app/mcp_server.py#L78) | function |  | used | [annotated](../code_explorer/04_ai_ml/agent_tools/app_mcp_server.py) | Open sales orders: on-time status, shortfalls and the cheapest on-time transfer or partial |
| F0494 | [`stocktake_reconciliation`](../backend/app/mcp_server.py#L84) | function |  | used | [annotated](../code_explorer/04_ai_ml/agent_tools/app_mcp_server.py) | Explain stock count differences with evidence and recommend posting, adjustment or recount |
| F0495 | [`search_governed_knowledge`](../backend/app/mcp_server.py#L90) | function |  | used | [annotated](../code_explorer/04_ai_ml/agent_tools/app_mcp_server.py) | Search approved contracts, SOPs, quality policies, product specs and logistics policies. C |
| F0496 | [`health`](../backend/app/mcp_server.py#L96) | route | GET /health | used | [annotated](../code_explorer/04_ai_ml/agent_tools/app_mcp_server.py) |  |
| F0497 | [`ApiKeyMiddleware`](../backend/app/mcp_server.py#L101) | class |  | used | [annotated](../code_explorer/04_ai_ml/agent_tools/app_mcp_server.py) | Bearer or X-API-Key check for /mcp; keys come from MCP_API_KEYS (comma separated). |
| F0498 | [`ApiKeyMiddleware.__init__`](../backend/app/mcp_server.py#L104) | method |  | used (framework) | [annotated](../code_explorer/04_ai_ml/agent_tools/app_mcp_server.py) |  |
| F0499 | [`ApiKeyMiddleware.dispatch`](../backend/app/mcp_server.py#L108) | method |  | used (framework) | [annotated](../code_explorer/04_ai_ml/agent_tools/app_mcp_server.py) |  |
| F0500 | [`create_mcp_app`](../backend/app/mcp_server.py#L117) | function |  | used | [annotated](../code_explorer/04_ai_ml/agent_tools/app_mcp_server.py) |  |

## backend/app/moat.py

Customer Data Intelligence Flywheel: how private data, human expertise and verified outcomes become intelligence.

| ID | Function | Kind | FastAPI route | Status | Annotated | Summary |
|---|---|---|---|---|---|---|
| F0250 | [`MoatEngine`](../backend/app/moat.py#L43) | class |  | used | [annotated](../code_explorer/02_business_logic/aurelia_views/app_moat.py) |  |
| F0251 | [`MoatEngine.__init__`](../backend/app/moat.py#L44) | method |  | used (framework) | [annotated](../code_explorer/02_business_logic/aurelia_views/app_moat.py) |  |
| F0252 | [`MoatEngine.consent`](../backend/app/moat.py#L48) | method |  | used | [annotated](../code_explorer/02_business_logic/aurelia_views/app_moat.py) | Recorded consent wins; without a record, synthetic demo customers are opted in and real on |
| F0253 | [`MoatEngine._series`](../backend/app/moat.py#L56) | method |  | used | [annotated](../code_explorer/02_business_logic/aurelia_views/app_moat.py) |  |
| F0254 | [`MoatEngine.model_comparison`](../backend/app/moat.py#L61) | method |  | used | [annotated](../code_explorer/02_business_logic/aurelia_views/app_moat.py) |  |
| F0255 | [`MoatEngine.view`](../backend/app/moat.py#L92) | method |  | used | [annotated](../code_explorer/02_business_logic/aurelia_views/app_moat.py) |  |

## backend/app/observability.py

Langfuse tracing for LangChain/LangGraph runs and Prometheus metrics shared by all services.

| ID | Function | Kind | FastAPI route | Status | Annotated | Summary |
|---|---|---|---|---|---|---|
| F0009 | [`_langfuse_client`](../backend/app/observability.py#L22) | function |  | used | [annotated](../code_explorer/01_fastapi/app_setup/app_observability.py) |  |
| F0010 | [`langfuse_callbacks`](../backend/app/observability.py#L41) | function |  | used | [annotated](../code_explorer/01_fastapi/app_setup/app_observability.py) | LangChain callback handlers for one run; empty when Langfuse is not configured. |
| F0011 | [`run_config`](../backend/app/observability.py#L51) | function |  | used | [annotated](../code_explorer/01_fastapi/app_setup/app_observability.py) |  |
| F0012 | [`flush`](../backend/app/observability.py#L59) | function |  | used | [annotated](../code_explorer/01_fastapi/app_setup/app_observability.py) |  |

## backend/app/optimizer.py

Warehouse rebalancing with OR-Tools and deterministic constraint inputs.

| ID | Function | Kind | FastAPI route | Status | Annotated | Summary |
|---|---|---|---|---|---|---|
| F0291 | [`optimize_transfers`](../backend/app/optimizer.py#L7) | function |  | used | [annotated](../code_explorer/02_business_logic/optimization/app_optimizer.py) |  |
| F0292 | [`_greedy`](../backend/app/optimizer.py#L60) | function |  | used | [annotated](../code_explorer/02_business_logic/optimization/app_optimizer.py) |  |

## backend/app/rag.py

Governed RAG: approved contracts, SOPs, quality policies, product specs and logistics policies.

| ID | Function | Kind | FastAPI route | Status | Annotated | Summary |
|---|---|---|---|---|---|---|
| F0731 | [`HashEmbedder`](../backend/app/rag.py#L21) | class |  | used | [annotated](../code_explorer/04_ai_ml/rag/app_rag.py) |  |
| F0732 | [`HashEmbedder.embed`](../backend/app/rag.py#L24) | method |  | used | [annotated](../code_explorer/04_ai_ml/rag/app_rag.py) |  |
| F0733 | [`HashEmbedder._one`](../backend/app/rag.py#L27) | method |  | used | [annotated](../code_explorer/04_ai_ml/rag/app_rag.py) |  |
| F0734 | [`FastEmbedder`](../backend/app/rag.py#L38) | class |  | used | [annotated](../code_explorer/04_ai_ml/rag/app_rag.py) |  |
| F0735 | [`FastEmbedder.__init__`](../backend/app/rag.py#L39) | method |  | used (framework) | [annotated](../code_explorer/04_ai_ml/rag/app_rag.py) |  |
| F0736 | [`FastEmbedder.embed`](../backend/app/rag.py#L46) | method |  | used | [annotated](../code_explorer/04_ai_ml/rag/app_rag.py) |  |
| F0737 | [`get_embedder`](../backend/app/rag.py#L54) | function |  | used | [annotated](../code_explorer/04_ai_ml/rag/app_rag.py) |  |
| F0738 | [`cosine`](../backend/app/rag.py#L61) | function |  | used | [annotated](../code_explorer/04_ai_ml/rag/app_rag.py) |  |
| F0739 | [`chunk_markdown`](../backend/app/rag.py#L65) | function |  | used | [annotated](../code_explorer/04_ai_ml/rag/app_rag.py) | Split on second-level headings; each chunk carries the document title and section for cont |
| F0740 | [`chunk_markdown.flush`](../backend/app/rag.py#L75) | nested |  | used | [annotated](../code_explorer/04_ai_ml/rag/app_rag.py) |  |
| F0741 | [`keyword_boost`](../backend/app/rag.py#L90) | function |  | used | [annotated](../code_explorer/04_ai_ml/rag/app_rag.py) |  |
| F0742 | [`Chunk`](../backend/app/rag.py#L97) | class |  | used | [annotated](../code_explorer/04_ai_ml/rag/app_rag.py) |  |
| F0743 | [`MemoryRag`](../backend/app/rag.py#L107) | class |  | used | [annotated](../code_explorer/04_ai_ml/rag/app_rag.py) |  |
| F0744 | [`MemoryRag.__init__`](../backend/app/rag.py#L110) | method |  | used (framework) | [annotated](../code_explorer/04_ai_ml/rag/app_rag.py) |  |
| F0745 | [`MemoryRag.add`](../backend/app/rag.py#L114) | method |  | used | [annotated](../code_explorer/04_ai_ml/rag/app_rag.py) |  |
| F0746 | [`MemoryRag.search`](../backend/app/rag.py#L120) | method |  | used | [annotated](../code_explorer/04_ai_ml/rag/app_rag.py) |  |
| F0747 | [`MemoryRag.stats`](../backend/app/rag.py#L130) | method |  | used | [annotated](../code_explorer/04_ai_ml/rag/app_rag.py) |  |
| F0748 | [`MemoryRag.load_directory`](../backend/app/rag.py#L133) | method |  | used | [annotated](../code_explorer/04_ai_ml/rag/app_rag.py) |  |
| F0749 | [`PgVectorRag`](../backend/app/rag.py#L139) | class |  | used | [annotated](../code_explorer/04_ai_ml/rag/app_rag.py) |  |
| F0750 | [`PgVectorRag.__init__`](../backend/app/rag.py#L142) | method |  | used (framework) | [annotated](../code_explorer/04_ai_ml/rag/app_rag.py) |  |
| F0751 | [`PgVectorRag._connect`](../backend/app/rag.py#L159) | method |  | used | [annotated](../code_explorer/04_ai_ml/rag/app_rag.py) |  |
| F0752 | [`PgVectorRag.add`](../backend/app/rag.py#L167) | method |  | used | [annotated](../code_explorer/04_ai_ml/rag/app_rag.py) |  |
| F0753 | [`PgVectorRag.stats`](../backend/app/rag.py#L181) | method |  | used | [annotated](../code_explorer/04_ai_ml/rag/app_rag.py) |  |
| F0754 | [`PgVectorRag.load_directory`](../backend/app/rag.py#L187) | method |  | used | [annotated](../code_explorer/04_ai_ml/rag/app_rag.py) | Index the approved corpus once; re-index everything if the embedding model changed. |
| F0755 | [`PgVectorRag.search`](../backend/app/rag.py#L204) | method |  | used | [annotated](../code_explorer/04_ai_ml/rag/app_rag.py) |  |
| F0756 | [`create_rag`](../backend/app/rag.py#L224) | function |  | used | [annotated](../code_explorer/04_ai_ml/rag/app_rag.py) |  |

## backend/app/roles.py

Role-centred decision views: the product is organised around the people who make supply-chain decisions.

| ID | Function | Kind | FastAPI route | Status | Annotated | Summary |
|---|---|---|---|---|---|---|
| F0256 | [`agent_system_prompt`](../backend/app/roles.py#L142) | function |  | used | [annotated](../code_explorer/02_business_logic/aurelia_views/app_roles.py) | Role-specific instructions for the specialised agent (LangGraph chat graph). |
| F0257 | [`_status`](../backend/app/roles.py#L151) | function |  | used | [annotated](../code_explorer/02_business_logic/aurelia_views/app_roles.py) |  |
| F0258 | [`kpi`](../backend/app/roles.py#L159) | function |  | used | [annotated](../code_explorer/02_business_logic/aurelia_views/app_roles.py) | A KPI with its agreed definition. available=False means the SAP source is not in this snap |
| F0259 | [`RoleCenter`](../backend/app/roles.py#L168) | class |  | used | [annotated](../code_explorer/02_business_logic/aurelia_views/app_roles.py) |  |
| F0260 | [`RoleCenter.__init__`](../backend/app/roles.py#L169) | method |  | used (framework) | [annotated](../code_explorer/02_business_logic/aurelia_views/app_roles.py) |  |
| F0261 | [`RoleCenter._facts`](../backend/app/roles.py#L173) | method |  | used | [annotated](../code_explorer/02_business_logic/aurelia_views/app_roles.py) |  |
| F0262 | [`RoleCenter._otif`](../backend/app/roles.py#L202) | method |  | used | [annotated](../code_explorer/02_business_logic/aurelia_views/app_roles.py) |  |
| F0263 | [`RoleCenter._inventory_value`](../backend/app/roles.py#L206) | method |  | used | [annotated](../code_explorer/02_business_logic/aurelia_views/app_roles.py) |  |
| F0264 | [`RoleCenter._annual_cogs`](../backend/app/roles.py#L209) | method |  | used | [annotated](../code_explorer/02_business_logic/aurelia_views/app_roles.py) |  |
| F0265 | [`RoleCenter._wape`](../backend/app/roles.py#L213) | method |  | used | [annotated](../code_explorer/02_business_logic/aurelia_views/app_roles.py) |  |
| F0266 | [`RoleCenter._supply_chain_cost`](../backend/app/roles.py#L217) | method |  | used | [annotated](../code_explorer/02_business_logic/aurelia_views/app_roles.py) | 30-day estimate: procurement (open POs) + transport (proposed transfers) + storage (carryi |
| F0267 | [`RoleCenter.platform_kpis`](../backend/app/roles.py#L232) | method |  | used | [annotated](../code_explorer/02_business_logic/aurelia_views/app_roles.py) |  |
| F0268 | [`RoleCenter.learning_summary`](../backend/app/roles.py#L255) | method |  | used | [annotated](../code_explorer/02_business_logic/aurelia_views/app_roles.py) |  |
| F0269 | [`RoleCenter.north_star`](../backend/app/roles.py#L274) | method |  | used | [annotated](../code_explorer/02_business_logic/aurelia_views/app_roles.py) |  |
| F0270 | [`RoleCenter.industry_kpis`](../backend/app/roles.py#L297) | method |  | used | [annotated](../code_explorer/02_business_logic/aurelia_views/app_roles.py) |  |
| F0271 | [`RoleCenter.catalogue`](../backend/app/roles.py#L342) | method |  | used | [annotated](../code_explorer/02_business_logic/aurelia_views/app_roles.py) |  |
| F0272 | [`RoleCenter.build`](../backend/app/roles.py#L345) | method |  | used | [annotated](../code_explorer/02_business_logic/aurelia_views/app_roles.py) |  |
| F0273 | [`RoleCenter._issue_actions`](../backend/app/roles.py#L371) | method |  | used (framework) | [annotated](../code_explorer/02_business_logic/aurelia_views/app_roles.py) |  |
| F0274 | [`RoleCenter._stock_predictions`](../backend/app/roles.py#L377) | method |  | used (framework) | [annotated](../code_explorer/02_business_logic/aurelia_views/app_roles.py) |  |
| F0275 | [`RoleCenter._production_predictions`](../backend/app/roles.py#L391) | method |  | used (framework) | [annotated](../code_explorer/02_business_logic/aurelia_views/app_roles.py) |  |
| F0276 | [`RoleCenter._supplier_predictions`](../backend/app/roles.py#L404) | method |  | used (framework) | [annotated](../code_explorer/02_business_logic/aurelia_views/app_roles.py) |  |
| F0277 | [`RoleCenter._shipment_predictions`](../backend/app/roles.py#L419) | method |  | used (framework) | [annotated](../code_explorer/02_business_logic/aurelia_views/app_roles.py) |  |
| F0278 | [`RoleCenter._quality_predictions`](../backend/app/roles.py#L430) | method |  | used (framework) | [annotated](../code_explorer/02_business_logic/aurelia_views/app_roles.py) |  |
| F0279 | [`RoleCenter._go`](../backend/app/roles.py#L448) | method |  | used (framework) | [annotated](../code_explorer/02_business_logic/aurelia_views/app_roles.py) |  |
| F0280 | [`RoleCenter._charts`](../backend/app/roles.py#L453) | method |  | used (framework) | [annotated](../code_explorer/02_business_logic/aurelia_views/app_roles.py) |  |
| F0281 | [`RoleCenter._director`](../backend/app/roles.py#L458) | method |  | used (framework) | [annotated](../code_explorer/02_business_logic/aurelia_views/app_roles.py) |  |
| F0282 | [`RoleCenter._demand`](../backend/app/roles.py#L476) | method |  | used (framework) | [annotated](../code_explorer/02_business_logic/aurelia_views/app_roles.py) |  |
| F0283 | [`RoleCenter._production`](../backend/app/roles.py#L507) | method |  | used (framework) | [annotated](../code_explorer/02_business_logic/aurelia_views/app_roles.py) |  |
| F0284 | [`RoleCenter._procurement`](../backend/app/roles.py#L524) | method |  | used (framework) | [annotated](../code_explorer/02_business_logic/aurelia_views/app_roles.py) |  |
| F0285 | [`RoleCenter._warehouse`](../backend/app/roles.py#L551) | method |  | used (framework) | [annotated](../code_explorer/02_business_logic/aurelia_views/app_roles.py) |  |
| F0286 | [`RoleCenter._logistics`](../backend/app/roles.py#L584) | method |  | used (framework) | [annotated](../code_explorer/02_business_logic/aurelia_views/app_roles.py) |  |
| F0287 | [`RoleCenter._quality`](../backend/app/roles.py#L608) | method |  | used (framework) | [annotated](../code_explorer/02_business_logic/aurelia_views/app_roles.py) |  |
| F0288 | [`RoleCenter._finance`](../backend/app/roles.py#L649) | method |  | used (framework) | [annotated](../code_explorer/02_business_logic/aurelia_views/app_roles.py) |  |
| F0289 | [`RoleCenter._mlops`](../backend/app/roles.py#L689) | method |  | used (framework) | [annotated](../code_explorer/02_business_logic/aurelia_views/app_roles.py) |  |
| F0290 | [`RoleCenter.learning`](../backend/app/roles.py#L729) | method |  | used | [annotated](../code_explorer/02_business_logic/aurelia_views/app_roles.py) |  |

## backend/app/runner.py

Execute LangGraph graphs either on LangGraph Server (deployments) or in-process (tests / single binary).

| ID | Function | Kind | FastAPI route | Status | Annotated | Summary |
|---|---|---|---|---|---|---|
| F0607 | [`_message_dict`](../backend/app/runner.py#L15) | function |  | used | [annotated](../code_explorer/04_ai_ml/langgraph/app_runner.py) |  |
| F0608 | [`normalise`](../backend/app/runner.py#L36) | function |  | used | [annotated](../code_explorer/04_ai_ml/langgraph/app_runner.py) |  |
| F0609 | [`LocalRunner`](../backend/app/runner.py#L45) | class |  | used | [annotated](../code_explorer/04_ai_ml/langgraph/app_runner.py) |  |
| F0610 | [`LocalRunner.__init__`](../backend/app/runner.py#L48) | method |  | used (framework) | [annotated](../code_explorer/04_ai_ml/langgraph/app_runner.py) |  |
| F0611 | [`LocalRunner._checkpointer`](../backend/app/runner.py#L54) | method |  | used (framework) | [annotated](../code_explorer/04_ai_ml/langgraph/app_runner.py) |  |
| F0612 | [`LocalRunner.graph`](../backend/app/runner.py#L68) | method |  | used | [annotated](../code_explorer/04_ai_ml/langgraph/app_runner.py) |  |
| F0613 | [`LocalRunner._result`](../backend/app/runner.py#L86) | method |  | used | [annotated](../code_explorer/04_ai_ml/langgraph/app_runner.py) |  |
| F0614 | [`LocalRunner.run`](../backend/app/runner.py#L91) | method |  | used | [annotated](../code_explorer/04_ai_ml/langgraph/app_runner.py) |  |
| F0615 | [`LocalRunner.resume`](../backend/app/runner.py#L99) | method |  | used | [annotated](../code_explorer/04_ai_ml/langgraph/app_runner.py) |  |
| F0616 | [`RemoteRunner`](../backend/app/runner.py#L109) | class |  | used | [annotated](../code_explorer/04_ai_ml/langgraph/app_runner.py) | LangGraph Server (the same server LangSmith Studio connects to). |
| F0617 | [`RemoteRunner.__init__`](../backend/app/runner.py#L114) | method |  | used (framework) | [annotated](../code_explorer/04_ai_ml/langgraph/app_runner.py) |  |
| F0618 | [`RemoteRunner._result`](../backend/app/runner.py#L120) | method |  | used | [annotated](../code_explorer/04_ai_ml/langgraph/app_runner.py) |  |
| F0619 | [`RemoteRunner.run`](../backend/app/runner.py#L127) | method |  | used | [annotated](../code_explorer/04_ai_ml/langgraph/app_runner.py) |  |
| F0620 | [`RemoteRunner.resume`](../backend/app/runner.py#L135) | method |  | used | [annotated](../code_explorer/04_ai_ml/langgraph/app_runner.py) |  |
| F0621 | [`GraphRunner`](../backend/app/runner.py#L142) | class |  | used | [annotated](../code_explorer/04_ai_ml/langgraph/app_runner.py) |  |
| F0622 | [`GraphRunner.__init__`](../backend/app/runner.py#L143) | method |  | used (framework) | [annotated](../code_explorer/04_ai_ml/langgraph/app_runner.py) |  |
| F0623 | [`GraphRunner.impl`](../backend/app/runner.py#L147) | method |  | used | [annotated](../code_explorer/04_ai_ml/langgraph/app_runner.py) |  |
| F0624 | [`GraphRunner.mode`](../backend/app/runner.py#L153) | method |  | used | [annotated](../code_explorer/04_ai_ml/langgraph/app_runner.py) |  |
| F0625 | [`GraphRunner._timed`](../backend/app/runner.py#L157) | method |  | used | [annotated](../code_explorer/04_ai_ml/langgraph/app_runner.py) |  |
| F0626 | [`GraphRunner.run`](../backend/app/runner.py#L169) | method |  | used | [annotated](../code_explorer/04_ai_ml/langgraph/app_runner.py) |  |
| F0627 | [`GraphRunner.resume`](../backend/app/runner.py#L172) | method |  | used | [annotated](../code_explorer/04_ai_ml/langgraph/app_runner.py) |  |

## backend/app/sap.py

Read-only SAP S/4HANA mock: validated snapshot plus OData-shaped entity sets.

| ID | Function | Kind | FastAPI route | Status | Annotated | Summary |
|---|---|---|---|---|---|---|
| F0401 | [`SapRepository`](../backend/app/sap.py#L31) | class |  | used | [annotated](../code_explorer/03_sap_data/sap_connectors/app_sap.py) |  |
| F0402 | [`SapRepository.__init__`](../backend/app/sap.py#L32) | method |  | used (framework) | [annotated](../code_explorer/03_sap_data/sap_connectors/app_sap.py) |  |
| F0403 | [`SapRepository._validate`](../backend/app/sap.py#L37) | method |  | used (framework) | [annotated](../code_explorer/03_sap_data/sap_connectors/app_sap.py) |  |
| F0404 | [`SapRepository.as_of`](../backend/app/sap.py#L61) | method |  | used | [annotated](../code_explorer/03_sap_data/sap_connectors/app_sap.py) | Business date of the extract; all date logic is relative to it so results are reproducible |
| F0405 | [`SapRepository.snapshot`](../backend/app/sap.py#L69) | method |  | used | [annotated](../code_explorer/03_sap_data/sap_connectors/app_sap.py) |  |
| F0406 | [`SapRepository.has`](../backend/app/sap.py#L75) | method |  | used | [annotated](../code_explorer/03_sap_data/sap_connectors/app_sap.py) |  |
| F0407 | [`SapRepository.section`](../backend/app/sap.py#L78) | method |  | used | [annotated](../code_explorer/03_sap_data/sap_connectors/app_sap.py) |  |
| F0408 | [`SapRepository.codes`](../backend/app/sap.py#L83) | method |  | used | [annotated](../code_explorer/03_sap_data/sap_connectors/app_sap.py) |  |
| F0409 | [`SapRepository.validate_codes`](../backend/app/sap.py#L86) | method |  | used | [annotated](../code_explorer/03_sap_data/sap_connectors/app_sap.py) |  |
| F0410 | [`SapRepository.material`](../backend/app/sap.py#L92) | method |  | used | [annotated](../code_explorer/03_sap_data/sap_connectors/app_sap.py) |  |
| F0411 | [`SapRepository.supplier`](../backend/app/sap.py#L96) | method |  | used | [annotated](../code_explorer/03_sap_data/sap_connectors/app_sap.py) |  |
| F0412 | [`SapRepository.stock_rows`](../backend/app/sap.py#L104) | method |  | used | [annotated](../code_explorer/03_sap_data/sap_connectors/app_sap.py) |  |
| F0413 | [`SapRepository.on_hand`](../backend/app/sap.py#L107) | method |  | used | [annotated](../code_explorer/03_sap_data/sap_connectors/app_sap.py) |  |
| F0414 | [`SapRepository.odata`](../backend/app/sap.py#L118) | method |  | used | [annotated](../code_explorer/03_sap_data/sap_connectors/app_sap.py) |  |
| F0415 | [`SapRepository.metadata`](../backend/app/sap.py#L138) | method |  | used | [annotated](../code_explorer/03_sap_data/sap_connectors/app_sap.py) |  |

## backend/app/schemas.py

the Pydantic request models of the SPARC / Aurelia gateway (backend/app/main.py). Every JSON body is

| ID | Function | Kind | FastAPI route | Status | Annotated | Summary |
|---|---|---|---|---|---|---|
| F0147 | [`StrictModel`](../backend/app/schemas.py#L11) | pydantic_model |  | used (framework) | [annotated](../code_explorer/01_fastapi/pydantic_models/app_schemas.py) |  |
| F0148 | [`FactoryReadinessRequest`](../backend/app/schemas.py#L15) | pydantic_model |  | used | [annotated](../code_explorer/01_fastapi/pydantic_models/app_schemas.py) |  |
| F0149 | [`StockBalanceRequest`](../backend/app/schemas.py#L22) | pydantic_model |  | used | [annotated](../code_explorer/01_fastapi/pydantic_models/app_schemas.py) |  |
| F0150 | [`ForecastRequest`](../backend/app/schemas.py#L28) | pydantic_model |  | used | [annotated](../code_explorer/01_fastapi/pydantic_models/app_schemas.py) |  |
| F0151 | [`WhatIfRequest`](../backend/app/schemas.py#L34) | pydantic_model |  | used | [annotated](../code_explorer/01_fastapi/pydantic_models/app_schemas.py) |  |
| F0152 | [`SupplierRiskRequest`](../backend/app/schemas.py#L41) | pydantic_model |  | used | [annotated](../code_explorer/01_fastapi/pydantic_models/app_schemas.py) |  |
| F0153 | [`QualityRequest`](../backend/app/schemas.py#L45) | pydantic_model |  | used | [annotated](../code_explorer/01_fastapi/pydantic_models/app_schemas.py) |  |
| F0154 | [`LogisticsRequest`](../backend/app/schemas.py#L50) | pydantic_model |  | used | [annotated](../code_explorer/01_fastapi/pydantic_models/app_schemas.py) |  |
| F0155 | [`SalesOrderRequest`](../backend/app/schemas.py#L55) | pydantic_model |  | used | [annotated](../code_explorer/01_fastapi/pydantic_models/app_schemas.py) |  |
| F0156 | [`StocktakeRequest`](../backend/app/schemas.py#L59) | pydantic_model |  | used | [annotated](../code_explorer/01_fastapi/pydantic_models/app_schemas.py) |  |
| F0157 | [`WatchRequest`](../backend/app/schemas.py#L63) | pydantic_model |  | used | [annotated](../code_explorer/01_fastapi/pydantic_models/app_schemas.py) |  |
| F0158 | [`RagQuery`](../backend/app/schemas.py#L70) | pydantic_model |  | used | [annotated](../code_explorer/01_fastapi/pydantic_models/app_schemas.py) |  |
| F0159 | [`RagDocument`](../backend/app/schemas.py#L76) | pydantic_model |  | used | [annotated](../code_explorer/01_fastapi/pydantic_models/app_schemas.py) |  |
| F0160 | [`RecommendationRequest`](../backend/app/schemas.py#L83) | pydantic_model |  | used | [annotated](../code_explorer/01_fastapi/pydantic_models/app_schemas.py) |  |
| F0161 | [`RecommendationFromTextRequest`](../backend/app/schemas.py#L89) | pydantic_model |  | used | [annotated](../code_explorer/01_fastapi/pydantic_models/app_schemas.py) | Agent hand-off (Flowise HumanInput 'proceed'): the gateway, not the LLM, picks the analysi |
| F0162 | [`DecisionRequest`](../backend/app/schemas.py#L102) | pydantic_model |  | used | [annotated](../code_explorer/01_fastapi/pydantic_models/app_schemas.py) |  |
| F0163 | [`ConsentRequest`](../backend/app/schemas.py#L110) | pydantic_model |  | used | [annotated](../code_explorer/01_fastapi/pydantic_models/app_schemas.py) |  |
| F0164 | [`ChatRequest`](../backend/app/schemas.py#L114) | pydantic_model |  | used | [annotated](../code_explorer/01_fastapi/pydantic_models/app_schemas.py) |  |
| F0165 | [`OutcomeRequest`](../backend/app/schemas.py#L120) | pydantic_model |  | used | [annotated](../code_explorer/01_fastapi/pydantic_models/app_schemas.py) | The real result of an executed recommendation, observed in SAP (approval alone is never pr |
| F0166 | [`BusinessWorkflowRequest`](../backend/app/schemas.py#L129) | pydantic_model |  | used | [annotated](../code_explorer/01_fastapi/pydantic_models/app_schemas.py) |  |
| F0167 | [`ResumeRequest`](../backend/app/schemas.py#L143) | pydantic_model |  | used | [annotated](../code_explorer/01_fastapi/pydantic_models/app_schemas.py) |  |
| F0168 | [`EmbeddingsRequest`](../backend/app/schemas.py#L148) | pydantic_model |  | used | [annotated](../code_explorer/01_fastapi/pydantic_models/app_schemas.py) | OpenAI-compatible embeddings request (extra fields such as `user` are ignored, as OpenAI c |
| F0169 | [`EmbeddingsRequest._limits`](../backend/app/schemas.py#L155) | method |  | used (framework) | [annotated](../code_explorer/01_fastapi/pydantic_models/app_schemas.py) |  |
| F0170 | [`SupplierLeadTimeRequest`](../backend/app/schemas.py#L163) | pydantic_model |  | used | [annotated](../code_explorer/01_fastapi/pydantic_models/app_schemas.py) |  |
| F0171 | [`ReconcileRequest`](../backend/app/schemas.py#L168) | pydantic_model |  | used | [annotated](../code_explorer/01_fastapi/pydantic_models/app_schemas.py) | What SAP shows actually happened after an executed decision (goods receipt, delivery or po |
| F0172 | [`DeepAgentHarness`](../backend/app/schemas.py#L182) | pydantic_model |  | used | [annotated](../code_explorer/01_fastapi/pydantic_models/app_schemas.py) | Harness settings of the Deep Agents supplier-research agent (model, step budget, subagents |
| F0173 | [`DeepAgentHarness._unique`](../backend/app/schemas.py#L204) | method |  | used (framework) | [annotated](../code_explorer/01_fastapi/pydantic_models/app_schemas.py) |  |
| F0174 | [`SupplierResearchRequest`](../backend/app/schemas.py#L211) | pydantic_model |  | used | [annotated](../code_explorer/01_fastapi/pydantic_models/app_schemas.py) |  |
| F0988 | [`CodeUpdateRequest`](../backend/app/schemas.py#L218) | pydantic_model |  | used | [annotated](../code_explorer/01_fastapi/pydantic_models/app_schemas.py) | Replace one backend function or class (UI backend code section; development only). |
| F0175 | [`FlowisePredictRequest`](../backend/app/schemas.py#L225) | pydantic_model |  | used | [annotated](../code_explorer/01_fastapi/pydantic_models/app_schemas.py) |  |
| F0176 | [`FlowisePredictRequest.question_or_resume`](../backend/app/schemas.py#L231) | method |  | used (framework) | [annotated](../code_explorer/01_fastapi/pydantic_models/app_schemas.py) |  |

## backend/app/store.py

Governance ledger: stored analyses, recommendation review queue, and a tamper-evident audit chain.

| ID | Function | Kind | FastAPI route | Status | Annotated | Summary |
|---|---|---|---|---|---|---|
| F0344 | [`_now`](../backend/app/store.py#L96) | function |  | used | [annotated](../code_explorer/03_sap_data/repositories/app_store.py) |  |
| F0345 | [`_digest`](../backend/app/store.py#L100) | function |  | used | [annotated](../code_explorer/03_sap_data/repositories/app_store.py) |  |
| F0346 | [`_SqliteDb`](../backend/app/store.py#L104) | class |  | used | [annotated](../code_explorer/03_sap_data/repositories/app_store.py) |  |
| F0347 | [`_SqliteDb.__init__`](../backend/app/store.py#L107) | method |  | used (framework) | [annotated](../code_explorer/03_sap_data/repositories/app_store.py) |  |
| F0348 | [`_SqliteDb.run`](../backend/app/store.py#L115) | method |  | used | [annotated](../code_explorer/03_sap_data/repositories/app_store.py) |  |
| F0349 | [`_SqliteDb.query`](../backend/app/store.py#L130) | method |  | used | [annotated](../code_explorer/03_sap_data/repositories/app_store.py) |  |
| F0350 | [`_PostgresDb`](../backend/app/store.py#L134) | class |  | used | [annotated](../code_explorer/03_sap_data/repositories/app_store.py) |  |
| F0351 | [`_PostgresDb.__init__`](../backend/app/store.py#L137) | method |  | used (framework) | [annotated](../code_explorer/03_sap_data/repositories/app_store.py) |  |
| F0352 | [`_PostgresDb.run`](../backend/app/store.py#L147) | method |  | used | [annotated](../code_explorer/03_sap_data/repositories/app_store.py) |  |
| F0353 | [`_PostgresDb.query`](../backend/app/store.py#L167) | method |  | used | [annotated](../code_explorer/03_sap_data/repositories/app_store.py) |  |
| F0354 | [`Store`](../backend/app/store.py#L171) | class |  | used | [annotated](../code_explorer/03_sap_data/repositories/app_store.py) |  |
| F0355 | [`Store.__init__`](../backend/app/store.py#L172) | method |  | used (framework) | [annotated](../code_explorer/03_sap_data/repositories/app_store.py) |  |
| F0356 | [`Store.memory`](../backend/app/store.py#L180) | method |  | used | [annotated](../code_explorer/03_sap_data/repositories/app_store.py) |  |
| F0357 | [`Store.dialect`](../backend/app/store.py#L184) | method |  | used | [annotated](../code_explorer/03_sap_data/repositories/app_store.py) |  |
| F0358 | [`Store.audit`](../backend/app/store.py#L189) | method |  | used | [annotated](../code_explorer/03_sap_data/repositories/app_store.py) |  |
| F0359 | [`Store.verify_chain`](../backend/app/store.py#L214) | method |  | used | [annotated](../code_explorer/03_sap_data/repositories/app_store.py) |  |
| F0360 | [`Store.audit_events`](../backend/app/store.py#L223) | method |  | used | [annotated](../code_explorer/03_sap_data/repositories/app_store.py) |  |
| F0361 | [`Store.save_analysis`](../backend/app/store.py#L228) | method |  | used | [annotated](../code_explorer/03_sap_data/repositories/app_store.py) |  |
| F0362 | [`Store.get_analysis`](../backend/app/store.py#L237) | method |  | used | [annotated](../code_explorer/03_sap_data/repositories/app_store.py) |  |
| F0363 | [`Store.latest_actionable`](../backend/app/store.py#L241) | method |  | used | [annotated](../code_explorer/03_sap_data/repositories/app_store.py) | Newest stored analysis of `kind` among the ids that has proposed actions (server-side sele |
| F0364 | [`Store.submit`](../backend/app/store.py#L247) | method |  | used | [annotated](../code_explorer/03_sap_data/repositories/app_store.py) |  |
| F0365 | [`Store._recommendation`](../backend/app/store.py#L268) | method |  | used | [annotated](../code_explorer/03_sap_data/repositories/app_store.py) |  |
| F0366 | [`Store.get_recommendation`](../backend/app/store.py#L272) | method |  | used | [annotated](../code_explorer/03_sap_data/repositories/app_store.py) |  |
| F0367 | [`Store.list_recommendations`](../backend/app/store.py#L276) | method |  | used | [annotated](../code_explorer/03_sap_data/repositories/app_store.py) | Optionally only recommendations whose analysis came from one SAP snapshot (one customer). |
| F0368 | [`Store.decide`](../backend/app/store.py#L289) | method |  | used | [annotated](../code_explorer/03_sap_data/repositories/app_store.py) |  |
| F0369 | [`Store.create_watch`](../backend/app/store.py#L298) | method |  | used | [annotated](../code_explorer/03_sap_data/repositories/app_store.py) |  |
| F0370 | [`Store._watch`](../backend/app/store.py#L305) | method |  | used | [annotated](../code_explorer/03_sap_data/repositories/app_store.py) |  |
| F0371 | [`Store.get_watch`](../backend/app/store.py#L310) | method |  | used | [annotated](../code_explorer/03_sap_data/repositories/app_store.py) |  |
| F0372 | [`Store.list_watches`](../backend/app/store.py#L314) | method |  | used | [annotated](../code_explorer/03_sap_data/repositories/app_store.py) |  |
| F0373 | [`Store.delete_watch`](../backend/app/store.py#L317) | method |  | used | [annotated](../code_explorer/03_sap_data/repositories/app_store.py) |  |
| F0374 | [`Store.record_watch`](../backend/app/store.py#L320) | method |  | used | [annotated](../code_explorer/03_sap_data/repositories/app_store.py) |  |
| F0375 | [`Store.execute_recommendation`](../backend/app/store.py#L324) | method |  | used | [annotated](../code_explorer/03_sap_data/repositories/app_store.py) | Accepted -> executed, recording the sandbox SAP documents created for each action (atomic, |
| F0376 | [`Store.sap_documents`](../backend/app/store.py#L339) | method |  | used | [annotated](../code_explorer/03_sap_data/repositories/app_store.py) |  |
| F0377 | [`Store.next_doc_number`](../backend/app/store.py#L344) | method |  | used | [annotated](../code_explorer/03_sap_data/repositories/app_store.py) |  |
| F0378 | [`Store.create_outcome`](../backend/app/store.py#L352) | method |  | used | [annotated](../code_explorer/03_sap_data/repositories/app_store.py) |  |
| F0379 | [`Store._outcome`](../backend/app/store.py#L357) | method |  | used | [annotated](../code_explorer/03_sap_data/repositories/app_store.py) |  |
| F0380 | [`Store.list_outcomes`](../backend/app/store.py#L362) | method |  | used | [annotated](../code_explorer/03_sap_data/repositories/app_store.py) |  |
| F0381 | [`Store.record_outcome`](../backend/app/store.py#L367) | method |  | used | [annotated](../code_explorer/03_sap_data/repositories/app_store.py) |  |
| F0382 | [`Store.record_feedback`](../backend/app/store.py#L380) | method |  | used | [annotated](../code_explorer/03_sap_data/repositories/app_store.py) | Why an expert approved, modified or rejected a recommendation — a training label once the  |
| F0383 | [`Store.feedback`](../backend/app/store.py#L385) | method |  | used | [annotated](../code_explorer/03_sap_data/repositories/app_store.py) |  |
| F0384 | [`Store.consent`](../backend/app/store.py#L390) | method |  | used | [annotated](../code_explorer/03_sap_data/repositories/app_store.py) |  |
| F0385 | [`Store.set_consent`](../backend/app/store.py#L394) | method |  | used | [annotated](../code_explorer/03_sap_data/repositories/app_store.py) |  |
| F0386 | [`Store.get_setting`](../backend/app/store.py#L400) | method |  | used | [annotated](../code_explorer/03_sap_data/repositories/app_store.py) |  |
| F0387 | [`Store.set_setting`](../backend/app/store.py#L404) | method |  | used | [annotated](../code_explorer/03_sap_data/repositories/app_store.py) |  |
| F0388 | [`Store.decision_stats`](../backend/app/store.py#L409) | method |  | used | [annotated](../code_explorer/03_sap_data/repositories/app_store.py) | Acceptance and override (rejection) rates with the reasons experts gave. |
| F0389 | [`Store.counts`](../backend/app/store.py#L428) | method |  | used | [annotated](../code_explorer/03_sap_data/repositories/app_store.py) | Recommendation counts by status; optionally only for one SAP snapshot (one customer). |

## backend/app/tenants.py

Industry / customer tenants: one SAP snapshot and engine stack per customer, selected per request (X-Tenant header).

| ID | Function | Kind | FastAPI route | Status | Annotated | Summary |
|---|---|---|---|---|---|---|
| F0390 | [`TenantContext`](../backend/app/tenants.py#L27) | class |  | used | [annotated](../code_explorer/03_sap_data/repositories/app_tenants.py) |  |
| F0391 | [`TenantRegistry`](../backend/app/tenants.py#L40) | class |  | used | [annotated](../code_explorer/03_sap_data/repositories/app_tenants.py) |  |
| F0392 | [`TenantRegistry.__init__`](../backend/app/tenants.py#L41) | method |  | used (framework) | [annotated](../code_explorer/03_sap_data/repositories/app_tenants.py) |  |
| F0393 | [`TenantRegistry.get`](../backend/app/tenants.py#L59) | method |  | used | [annotated](../code_explorer/03_sap_data/repositories/app_tenants.py) |  |
| F0394 | [`TenantRegistry.catalogue`](../backend/app/tenants.py#L74) | method |  | used | [annotated](../code_explorer/03_sap_data/repositories/app_tenants.py) |  |
| F0395 | [`TenantRegistry.activate`](../backend/app/tenants.py#L80) | method |  | used | [annotated](../code_explorer/03_sap_data/repositories/app_tenants.py) |  |
| F0396 | [`TenantRegistry.deactivate`](../backend/app/tenants.py#L84) | method |  | used | [annotated](../code_explorer/03_sap_data/repositories/app_tenants.py) |  |
| F0397 | [`TenantRegistry.current_id`](../backend/app/tenants.py#L88) | method |  | used | [annotated](../code_explorer/03_sap_data/repositories/app_tenants.py) |  |
| F0398 | [`TenantProxy`](../backend/app/tenants.py#L93) | class |  | used | [annotated](../code_explorer/03_sap_data/repositories/app_tenants.py) | Attribute access is forwarded to the active tenant's object (sap / engine / insights / das |
| F0399 | [`TenantProxy.__init__`](../backend/app/tenants.py#L96) | method |  | used (framework) | [annotated](../code_explorer/03_sap_data/repositories/app_tenants.py) |  |
| F0400 | [`TenantProxy.__getattr__`](../backend/app/tenants.py#L100) | method |  | used (framework) | [annotated](../code_explorer/03_sap_data/repositories/app_tenants.py) |  |

## backend/app/tools.py

Read-only LangChain tools shared by the LangGraph Chat Graph, Business Graph and Deep Agent.

| ID | Function | Kind | FastAPI route | Status | Annotated | Summary |
|---|---|---|---|---|---|---|
| F0501 | [`_dump`](../backend/app/tools.py#L13) | function |  | used | [annotated](../code_explorer/04_ai_ml/agent_tools/app_tools.py) |  |
| F0502 | [`_safe`](../backend/app/tools.py#L18) | function |  | used | [annotated](../code_explorer/04_ai_ml/agent_tools/app_tools.py) |  |
| F0503 | [`sap_snapshot`](../backend/app/tools.py#L25) | function |  | used | [annotated](../code_explorer/04_ai_ml/agent_tools/app_tools.py) | Return SAP snapshot provenance plus valid plant, material and supplier codes. Call this be |
| F0504 | [`factory_material_readiness`](../backend/app/tools.py#L31) | function |  | used | [annotated](../code_explorer/04_ai_ml/agent_tools/app_tools.py) | Check BOM material readiness for a production run. |
| F0505 | [`warehouse_stock_balance`](../backend/app/tools.py#L44) | function |  | used | [annotated](../code_explorer/04_ai_ml/agent_tools/app_tools.py) | Forecast demand (XGBoost) and optimise stock transfers between DC01, DC21 and DC22 (OR-Too |
| F0506 | [`demand_forecast`](../backend/app/tools.py#L50) | function |  | used | [annotated](../code_explorer/04_ai_ml/agent_tools/app_tools.py) | XGBoost daily demand forecast for a finished good, optionally for one warehouse (DC01, DC2 |
| F0507 | [`supplier_risk`](../backend/app/tools.py#L56) | function |  | used | [annotated](../code_explorer/04_ai_ml/agent_tools/app_tools.py) | Supplier scorecard: OTIF, delays, quality rejects, open PO exposure, single-source risk. A |
| F0508 | [`quality_status`](../backend/app/tools.py#L62) | function |  | used | [annotated](../code_explorer/04_ai_ml/agent_tools/app_tools.py) | Quality inspection lots (QM): inspection/blocked/expired batches and which production orde |
| F0509 | [`logistics_status`](../backend/app/tools.py#L68) | function |  | used | [annotated](../code_explorer/04_ai_ml/agent_tools/app_tools.py) | In-transit shipments, delays, revised ETAs and escalations for a warehouse and/or material |
| F0510 | [`inventory_overview`](../backend/app/tools.py#L74) | function |  | used | [annotated](../code_explorer/04_ai_ml/agent_tools/app_tools.py) | Finished-goods stock, days of cover, open sales orders and in-transit stock by warehouse. |
| F0511 | [`sales_order_fulfilment`](../backend/app/tools.py#L80) | function |  | used | [annotated](../code_explorer/04_ai_ml/agent_tools/app_tools.py) | Open sales orders: can each ship on time from DC stock + inbound? Shortfalls get the cheap |
| F0512 | [`stocktake_reconciliation`](../backend/app/tools.py#L86) | function |  | used | [annotated](../code_explorer/04_ai_ml/agent_tools/app_tools.py) | Explain stock count differences (unposted goods movements, scrap not posted) and recommend |
| F0513 | [`search_governed_knowledge`](../backend/app/tools.py#L92) | function |  | used | [annotated](../code_explorer/04_ai_ml/agent_tools/app_tools.py) | Search approved supplier contracts, SOPs, quality policies, product specs and logistics po |

## backend/scinsight/app.py

SupplyChain Insight AI — business-tool service (FastAPI, Swagger at /docs).

| ID | Function | Kind | FastAPI route | Status | Annotated | Summary |
|---|---|---|---|---|---|---|
| F0112 | [`create_app`](../backend/scinsight/app.py#L36) | function |  | used | [annotated](../code_explorer/01_fastapi/endpoints/scinsight_app.py) |  |
| F0113 | [`create_app.principal`](../backend/scinsight/app.py#L59) | nested |  | used | [annotated](../code_explorer/01_fastapi/endpoints/scinsight_app.py) |  |
| F0114 | [`create_app.reader`](../backend/scinsight/app.py#L64) | nested |  | used | [annotated](../code_explorer/01_fastapi/endpoints/scinsight_app.py) |  |
| F0115 | [`create_app.biz_date`](../backend/scinsight/app.py#L68) | nested |  | used | [annotated](../code_explorer/01_fastapi/endpoints/scinsight_app.py) |  |
| F0116 | [`create_app.health`](../backend/scinsight/app.py#L71) | route | GET /health | used | [annotated](../code_explorer/01_fastapi/endpoints/scinsight_app.py) |  |
| F0117 | [`create_app.context`](../backend/scinsight/app.py#L77) | route | GET /api/v1/context | used | [annotated](../code_explorer/01_fastapi/endpoints/scinsight_app.py) |  |
| F0118 | [`create_app.validate_context`](../backend/scinsight/app.py#L83) | route | POST /api/v1/context/validate | used | [annotated](../code_explorer/01_fastapi/endpoints/scinsight_app.py) |  |
| F0119 | [`create_app.sap_inventory`](../backend/scinsight/app.py#L92) | route | GET /api/v1/sap/inventory | used | [annotated](../code_explorer/01_fastapi/endpoints/scinsight_app.py) |  |
| F0120 | [`create_app.sap_bom`](../backend/scinsight/app.py#L97) | route | GET /api/v1/sap/bom/{sku} | used | [annotated](../code_explorer/01_fastapi/endpoints/scinsight_app.py) |  |
| F0121 | [`create_app.sap_production_orders`](../backend/scinsight/app.py#L101) | route | GET /api/v1/sap/production-orders | used | [annotated](../code_explorer/01_fastapi/endpoints/scinsight_app.py) |  |
| F0122 | [`create_app.sap_purchase_orders`](../backend/scinsight/app.py#L105) | route | GET /api/v1/sap/purchase-orders | used | [annotated](../code_explorer/01_fastapi/endpoints/scinsight_app.py) |  |
| F0123 | [`create_app.sap_warehouses`](../backend/scinsight/app.py#L110) | route | GET /api/v1/sap/warehouses | used | [annotated](../code_explorer/01_fastapi/endpoints/scinsight_app.py) |  |
| F0124 | [`create_app.sap_suppliers`](../backend/scinsight/app.py#L114) | route | GET /api/v1/sap/suppliers | used | [annotated](../code_explorer/01_fastapi/endpoints/scinsight_app.py) |  |
| F0125 | [`create_app.sap_write_blocked`](../backend/scinsight/app.py#L118) | route | POST/PUT/PATCH/DELETE /api/v1/sap/{path:path} | used | [annotated](../code_explorer/01_fastapi/endpoints/scinsight_app.py) |  |
| F0126 | [`create_app.material_readiness`](../backend/scinsight/app.py#L124) | route | POST /api/v1/optimizer/material-readiness | used | [annotated](../code_explorer/01_fastapi/endpoints/scinsight_app.py) |  |
| F0127 | [`create_app.warehouse_balancing`](../backend/scinsight/app.py#L128) | route | POST /api/v1/optimizer/warehouse-balancing | used | [annotated](../code_explorer/01_fastapi/endpoints/scinsight_app.py) |  |
| F0128 | [`create_app.replenishment`](../backend/scinsight/app.py#L132) | route | POST /api/v1/optimizer/replenishment | used | [annotated](../code_explorer/01_fastapi/endpoints/scinsight_app.py) |  |
| F0129 | [`create_app.forecast_demand`](../backend/scinsight/app.py#L136) | route | POST /api/v1/forecast/demand | used | [annotated](../code_explorer/01_fastapi/endpoints/scinsight_app.py) |  |
| F0130 | [`create_app.forecast_lead_time`](../backend/scinsight/app.py#L140) | route | POST /api/v1/forecast/lead-time | used | [annotated](../code_explorer/01_fastapi/endpoints/scinsight_app.py) |  |
| F0131 | [`create_app.quality_check`](../backend/scinsight/app.py#L144) | route | POST /api/v1/quality/check-stock | used | [annotated](../code_explorer/01_fastapi/endpoints/scinsight_app.py) |  |
| F0132 | [`create_app.calculation`](../backend/scinsight/app.py#L148) | route | GET /api/v1/calculations/{calculation_id} | used | [annotated](../code_explorer/01_fastapi/endpoints/scinsight_app.py) |  |
| F0133 | [`create_app.rag_search`](../backend/scinsight/app.py#L153) | route | POST /api/v1/rag/search | used | [annotated](../code_explorer/01_fastapi/endpoints/scinsight_app.py) |  |
| F0134 | [`create_app.rag_documents`](../backend/scinsight/app.py#L159) | route | GET /api/v1/rag/documents | used | [annotated](../code_explorer/01_fastapi/endpoints/scinsight_app.py) |  |
| F0135 | [`create_app.create_decision`](../backend/scinsight/app.py#L168) | route | POST /api/v1/decisions | used | [annotated](../code_explorer/01_fastapi/endpoints/scinsight_app.py) |  |
| F0136 | [`create_app.list_decisions`](../backend/scinsight/app.py#L173) | route | GET /api/v1/decisions | used | [annotated](../code_explorer/01_fastapi/endpoints/scinsight_app.py) |  |
| F0137 | [`create_app.get_decision`](../backend/scinsight/app.py#L177) | route | GET /api/v1/decisions/{rec_id} | used | [annotated](../code_explorer/01_fastapi/endpoints/scinsight_app.py) |  |
| F0138 | [`create_app.review`](../backend/scinsight/app.py#L181) | route | POST /api/v1/decisions/{rec_id}/review | used | [annotated](../code_explorer/01_fastapi/endpoints/scinsight_app.py) |  |
| F0139 | [`create_app.withdraw`](../backend/scinsight/app.py#L185) | route | POST /api/v1/decisions/{rec_id}/withdraw | used | [annotated](../code_explorer/01_fastapi/endpoints/scinsight_app.py) |  |
| F0140 | [`create_app.sap_execution`](../backend/scinsight/app.py#L189) | route | POST /api/v1/decisions/{rec_id}/sap-execution | used | [annotated](../code_explorer/01_fastapi/endpoints/scinsight_app.py) |  |
| F0141 | [`create_app.reconcile`](../backend/scinsight/app.py#L194) | route | POST /api/v1/outcomes/reconcile | used | [annotated](../code_explorer/01_fastapi/endpoints/scinsight_app.py) |  |
| F0142 | [`create_app.learning_metrics`](../backend/scinsight/app.py#L198) | route | GET /api/v1/learning/metrics | used | [annotated](../code_explorer/01_fastapi/endpoints/scinsight_app.py) |  |
| F0143 | [`create_app.train`](../backend/scinsight/app.py#L202) | route | POST /api/v1/learning/train-lead-time-model | used | [annotated](../code_explorer/01_fastapi/endpoints/scinsight_app.py) |  |
| F0144 | [`create_app.promote`](../backend/scinsight/app.py#L209) | route | POST /api/v1/learning/models/{model_id}/promote | used | [annotated](../code_explorer/01_fastapi/endpoints/scinsight_app.py) |  |
| F0145 | [`create_app.retraining`](../backend/scinsight/app.py#L216) | route | POST /api/v1/learning/retraining-requests | used | [annotated](../code_explorer/01_fastapi/endpoints/scinsight_app.py) |  |
| F0146 | [`create_app.audit`](../backend/scinsight/app.py#L222) | route | GET /api/v1/audit | used | [annotated](../code_explorer/01_fastapi/endpoints/scinsight_app.py) |  |

## backend/scinsight/business.py

Deterministic supply-chain business functions — the only place quantities, dates and costs are calculated.

| ID | Function | Kind | FastAPI route | Status | Annotated | Summary |
|---|---|---|---|---|---|---|
| F0293 | [`BusinessRuleError`](../backend/scinsight/business.py#L26) | class |  | used | [annotated](../code_explorer/02_business_logic/scinsight_rules/scinsight_business.py) | A request that cannot be answered safely (invalid BOM, unit mismatch, missing master data) |
| F0294 | [`_d`](../backend/scinsight/business.py#L30) | function |  | used | [annotated](../code_explorer/02_business_logic/scinsight_rules/scinsight_business.py) |  |
| F0295 | [`round_qty`](../backend/scinsight/business.py#L36) | function |  | used | [annotated](../code_explorer/02_business_logic/scinsight_rules/scinsight_business.py) |  |
| F0296 | [`_dedupe`](../backend/scinsight/business.py#L40) | function |  | used | [annotated](../code_explorer/02_business_logic/scinsight_rules/scinsight_business.py) |  |
| F0297 | [`calculate_usable_stock`](../backend/scinsight/business.py#L48) | function |  | used | [annotated](../code_explorer/02_business_logic/scinsight_rules/scinsight_business.py) | Usable quantity from SAP batches with an itemised exclusion list. With transfer_arrival, a |
| F0298 | [`average_daily_demand`](../backend/scinsight/business.py#L79) | function |  | used | [annotated](../code_explorer/02_business_logic/scinsight_rules/scinsight_business.py) | Mean units/day over the last `window_days` days (missing days count as zero demand; duplic |
| F0299 | [`calculate_days_of_cover`](../backend/scinsight/business.py#L86) | function |  | used | [annotated](../code_explorer/02_business_logic/scinsight_rules/scinsight_business.py) | Days the usable stock lasts at the given demand. None when there is no demand (cover is un |
| F0300 | [`calculate_replenishment_quantity`](../backend/scinsight/business.py#L93) | function |  | used | [annotated](../code_explorer/02_business_logic/scinsight_rules/scinsight_business.py) | Quantity needed so that stock covers lead time + target cover. Zero demand -> 0. |
| F0301 | [`detect_expiry_risk`](../backend/scinsight/business.py#L100) | function |  | used | [annotated](../code_explorer/02_business_logic/scinsight_rules/scinsight_business.py) | Released batches expired or expiring within the horizon, most urgent first. |
| F0302 | [`calculate_bom_requirements`](../backend/scinsight/business.py#L115) | function |  | used | [annotated](../code_explorer/02_business_logic/scinsight_rules/scinsight_business.py) | Material requirements for `quantity` finished units from the approved BOM version valid on |
| F0303 | [`calculate_material_shortage`](../backend/scinsight/business.py#L138) | function |  | used | [annotated](../code_explorer/02_business_logic/scinsight_rules/scinsight_business.py) | Missing quantity on the need date. Inbound counts only if confirmed (or received) and prom |
| F0304 | [`Site`](../backend/scinsight/business.py#L160) | class |  | used | [annotated](../code_explorer/02_business_logic/scinsight_rules/scinsight_business.py) |  |
| F0305 | [`generate_transfer_candidates`](../backend/scinsight/business.py#L169) | function |  | used | [annotated](../code_explorer/02_business_logic/scinsight_rules/scinsight_business.py) | Donor warehouses with surplus = transferable stock above their own target cover (FEFO: nea |
| F0306 | [`evaluate_transfer_feasibility`](../backend/scinsight/business.py#L184) | function |  | used | [annotated](../code_explorer/02_business_logic/scinsight_rules/scinsight_business.py) | Is the transfer possible and in time? Reasons are listed; costs come only from the lane ma |
| F0307 | [`compare_supply_options`](../backend/scinsight/business.py#L206) | function |  | used | [annotated](../code_explorer/02_business_logic/scinsight_rules/scinsight_business.py) | Rank options: feasible and in time first, then full coverage, then lowest cost, then faste |
| F0308 | [`estimate_supplier_lead_time`](../backend/scinsight/business.py#L219) | function |  | used | [annotated](../code_explorer/02_business_logic/scinsight_rules/scinsight_business.py) | Empirical lead time from received purchase orders (order date -> goods receipt). Duplicate |
| F0309 | [`calculate_prediction_error`](../backend/scinsight/business.py#L234) | function |  | used | [annotated](../code_explorer/02_business_logic/scinsight_rules/scinsight_business.py) | Signed error = actual - predicted (positive = later/higher than predicted). |
| F0310 | [`reconcile_actual_outcome`](../backend/scinsight/business.py#L241) | function |  | used | [annotated](../code_explorer/02_business_logic/scinsight_rules/scinsight_business.py) | Match a lead-time prediction with the SAP goods receipt of its purchase order. |

## backend/scinsight/db.py

Database access for SupplyChain Insight AI: PostgreSQL (deployments) or SQLite (hermetic tests), with versioned SQL migrations.

| ID | Function | Kind | FastAPI route | Status | Annotated | Summary |
|---|---|---|---|---|---|---|
| F0416 | [`now_iso`](../backend/scinsight/db.py#L18) | function |  | used | [annotated](../code_explorer/03_sap_data/sql/scinsight_db.py) |  |
| F0417 | [`ensure_postgres_database`](../backend/scinsight/db.py#L22) | function |  | used | [annotated](../code_explorer/03_sap_data/sql/scinsight_db.py) | Create the target PostgreSQL database if it does not exist (existing Compose volumes / man |
| F0418 | [`Database`](../backend/scinsight/db.py#L39) | class |  | used | [annotated](../code_explorer/03_sap_data/sql/scinsight_db.py) |  |
| F0419 | [`Database.__init__`](../backend/scinsight/db.py#L40) | method |  | used (framework) | [annotated](../code_explorer/03_sap_data/sql/scinsight_db.py) |  |
| F0420 | [`Database._sql`](../backend/scinsight/db.py#L61) | method |  | used | [annotated](../code_explorer/03_sap_data/sql/scinsight_db.py) |  |
| F0421 | [`Database.query`](../backend/scinsight/db.py#L64) | method |  | used | [annotated](../code_explorer/03_sap_data/sql/scinsight_db.py) |  |
| F0422 | [`Database.one`](../backend/scinsight/db.py#L71) | method |  | used | [annotated](../code_explorer/03_sap_data/sql/scinsight_db.py) |  |
| F0423 | [`Database.execute`](../backend/scinsight/db.py#L75) | method |  | used | [annotated](../code_explorer/03_sap_data/sql/scinsight_db.py) |  |
| F0424 | [`Database.executemany`](../backend/scinsight/db.py#L82) | method |  | used | [annotated](../code_explorer/03_sap_data/sql/scinsight_db.py) |  |
| F0425 | [`Database.transaction`](../backend/scinsight/db.py#L92) | method |  | used | [annotated](../code_explorer/03_sap_data/sql/scinsight_db.py) | Run several statements atomically (all or nothing). |
| F0426 | [`Database.atomic`](../backend/scinsight/db.py#L104) | method |  | used | [annotated](../code_explorer/03_sap_data/sql/scinsight_db.py) | Run fn(q) inside one transaction holding an exclusive lock; q(sql, params) returns rows. F |
| F0427 | [`Database.atomic.q`](../backend/scinsight/db.py#L114) | nested |  | used | [annotated](../code_explorer/03_sap_data/sql/scinsight_db.py) |  |
| F0428 | [`Database._script`](../backend/scinsight/db.py#L119) | method |  | used | [annotated](../code_explorer/03_sap_data/sql/scinsight_db.py) |  |
| F0429 | [`Database.migrate`](../backend/scinsight/db.py#L132) | method |  | used | [annotated](../code_explorer/03_sap_data/sql/scinsight_db.py) |  |

## backend/scinsight/fixtures.py

Deterministic SYNTHETIC SAP fixtures for SupplyChain Insight AI (every record is fictional and labelled synthetic).

| ID | Function | Kind | FastAPI route | Status | Annotated | Summary |
|---|---|---|---|---|---|---|
| F0430 | [`key_hash`](../backend/scinsight/fixtures.py#L93) | function |  | used | [annotated](../code_explorer/03_sap_data/synthetic_sap/scinsight_fixtures.py) |  |
| F0431 | [`_d`](../backend/scinsight/fixtures.py#L97) | function |  | used | [annotated](../code_explorer/03_sap_data/synthetic_sap/scinsight_fixtures.py) |  |
| F0432 | [`load`](../backend/scinsight/fixtures.py#L101) | function |  | used | [annotated](../code_explorer/03_sap_data/synthetic_sap/scinsight_fixtures.py) | Load the synthetic fixtures (idempotent: rows are replaced by primary key). Returns counts |
| F0433 | [`load.upsert`](../backend/scinsight/fixtures.py#L113) | nested |  | used | [annotated](../code_explorer/03_sap_data/synthetic_sap/scinsight_fixtures.py) |  |

## backend/scinsight/learning.py

Governed learning: a small, reproducible supplier lead-time model with a holdout evaluation and a manual promotion gate.

| ID | Function | Kind | FastAPI route | Status | Annotated | Summary |
|---|---|---|---|---|---|---|
| F0532 | [`_rows`](../backend/scinsight/learning.py#L24) | function |  | used | [annotated](../code_explorer/04_ai_ml/forecasting/scinsight_learning.py) |  |
| F0533 | [`_features`](../backend/scinsight/learning.py#L38) | function |  | used | [annotated](../code_explorer/04_ai_ml/forecasting/scinsight_learning.py) |  |
| F0534 | [`train_lead_time_model`](../backend/scinsight/learning.py#L43) | function |  | used | [annotated](../code_explorer/04_ai_ml/forecasting/scinsight_learning.py) |  |
| F0535 | [`promote`](../backend/scinsight/learning.py#L73) | function |  | used | [annotated](../code_explorer/04_ai_ml/forecasting/scinsight_learning.py) |  |
| F0536 | [`predict_lead_time`](../backend/scinsight/learning.py#L88) | function |  | used | [annotated](../code_explorer/04_ai_ml/forecasting/scinsight_learning.py) | Re-fit the promoted configuration deterministically on all receipts and predict (no pickle |
| F0537 | [`retraining_request`](../backend/scinsight/learning.py#L101) | function |  | used | [annotated](../code_explorer/04_ai_ml/forecasting/scinsight_learning.py) |  |

## backend/scinsight/lg/chat.py

The SCInsight chat bot as a LangGraph graph, the same as SCInsight-Cosmetics-Chatflow-v1:

| ID | Function | Kind | FastAPI route | Status | Annotated | Summary |
|---|---|---|---|---|---|---|
| F0628 | [`ask_sc_agent_manager`](../backend/scinsight/lg/chat.py#L31) | function |  | used | [annotated](../code_explorer/04_ai_ml/langgraph/scinsight_lg_chat.py) | The SC Agent Manager (supervisor). Use it for EVERY planning or analysis question: product |
| F0629 | [`search_supply_chain_policy`](../backend/scinsight/lg/chat.py#L43) | function |  | used | [annotated](../code_explorer/04_ai_ml/langgraph/scinsight_lg_chat.py) | Search the governed policy, SOP, specification and supplier-agreement documents (PostgreSQ |
| F0630 | [`ChatState`](../backend/scinsight/lg/chat.py#L56) | class |  | used | [annotated](../code_explorer/04_ai_ml/langgraph/scinsight_lg_chat.py) |  |
| F0631 | [`_this_turn`](../backend/scinsight/lg/chat.py#L60) | function |  | used | [annotated](../code_explorer/04_ai_ml/langgraph/scinsight_lg_chat.py) |  |
| F0632 | [`guardrail`](../backend/scinsight/lg/chat.py#L65) | function |  | used | [annotated](../code_explorer/04_ai_ml/langgraph/scinsight_lg_chat.py) |  |
| F0633 | [`blocked`](../backend/scinsight/lg/chat.py#L69) | function |  | used | [annotated](../code_explorer/04_ai_ml/langgraph/scinsight_lg_chat.py) |  |
| F0634 | [`assistant`](../backend/scinsight/lg/chat.py#L73) | function |  | used | [annotated](../code_explorer/04_ai_ml/langgraph/scinsight_lg_chat.py) |  |
| F0635 | [`evidence_gate`](../backend/scinsight/lg/chat.py#L81) | function |  | used | [annotated](../code_explorer/04_ai_ml/langgraph/scinsight_lg_chat.py) | Port of the Flowise post-processing: every number must exist in this turn's tool results,  |
| F0636 | [`build_chat`](../backend/scinsight/lg/chat.py#L108) | function |  | used | [annotated](../code_explorer/04_ai_ml/langgraph/scinsight_lg_chat.py) |  |

## backend/scinsight/lg/common.py

Shared pieces of the LangGraph mirror: SCInsight API client, Qwen model, the prompts Flowise uses, and Python ports of

| ID | Function | Kind | FastAPI route | Status | Annotated | Summary |
|---|---|---|---|---|---|---|
| F0637 | [`out_of_scope_reply`](../backend/scinsight/lg/common.py#L30) | function |  | used | [annotated](../code_explorer/04_ai_ml/langgraph/scinsight_lg_common.py) |  |
| F0638 | [`client`](../backend/scinsight/lg/common.py#L39) | function |  | used | [annotated](../code_explorer/04_ai_ml/langgraph/scinsight_lg_common.py) |  |
| F0639 | [`api`](../backend/scinsight/lg/common.py#L46) | function |  | used | [annotated](../code_explorer/04_ai_ml/langgraph/scinsight_lg_common.py) | Call the SCInsight API with the agent key (role agent_service: read, calculate, create rec |
| F0640 | [`detail`](../backend/scinsight/lg/common.py#L62) | function |  | used | [annotated](../code_explorer/04_ai_ml/langgraph/scinsight_lg_common.py) |  |
| F0641 | [`strip`](../backend/scinsight/lg/common.py#L67) | function |  | used | [annotated](../code_explorer/04_ai_ml/langgraph/scinsight_lg_common.py) |  |
| F0642 | [`llm`](../backend/scinsight/lg/common.py#L76) | function |  | used | [annotated](../code_explorer/04_ai_ml/langgraph/scinsight_lg_common.py) | Qwen through the same OpenAI-compatible endpoint Flowise uses (temperature 0). |
| F0643 | [`prompt`](../backend/scinsight/lg/common.py#L84) | function |  | used | [annotated](../code_explorer/04_ai_ml/langgraph/scinsight_lg_common.py) |  |
| F0644 | [`explain_prompt`](../backend/scinsight/lg/common.py#L89) | function |  | used | [annotated](../code_explorer/04_ai_ml/langgraph/scinsight_lg_common.py) | (system, user template) of a specialist's explanation step, exactly as exported for Flowis |
| F0645 | [`fill`](../backend/scinsight/lg/common.py#L96) | function |  | used | [annotated](../code_explorer/04_ai_ml/langgraph/scinsight_lg_common.py) | Resolve the Flowise template variables used in the shared prompts ({{ question }}, {{ $flo |
| F0646 | [`text_of`](../backend/scinsight/lg/common.py#L102) | function |  | used | [annotated](../code_explorer/04_ai_ml/langgraph/scinsight_lg_common.py) |  |
| F0647 | [`_list`](../backend/scinsight/lg/common.py#L110) | function |  | used | [annotated](../code_explorer/04_ai_ml/langgraph/scinsight_lg_common.py) |  |
| F0648 | [`_kv`](../backend/scinsight/lg/common.py#L114) | function |  | used | [annotated](../code_explorer/04_ai_ml/langgraph/scinsight_lg_common.py) |  |
| F0649 | [`_fmt`](../backend/scinsight/lg/common.py#L118) | function |  | used | [annotated](../code_explorer/04_ai_ml/langgraph/scinsight_lg_common.py) |  |
| F0650 | [`_excluded`](../backend/scinsight/lg/common.py#L128) | function |  | used | [annotated](../code_explorer/04_ai_ml/langgraph/scinsight_lg_common.py) |  |
| F0651 | [`_late`](../backend/scinsight/lg/common.py#L132) | function |  | used | [annotated](../code_explorer/04_ai_ml/langgraph/scinsight_lg_common.py) |  |
| F0652 | [`_near`](../backend/scinsight/lg/common.py#L136) | function |  | used | [annotated](../code_explorer/04_ai_ml/langgraph/scinsight_lg_common.py) |  |
| F0653 | [`_opt`](../backend/scinsight/lg/common.py#L140) | function |  | used | [annotated](../code_explorer/04_ai_ml/langgraph/scinsight_lg_common.py) |  |
| F0654 | [`summarize`](../backend/scinsight/lg/common.py#L151) | function |  | used | [annotated](../code_explorer/04_ai_ml/langgraph/scinsight_lg_common.py) |  |
| F0655 | [`_po_unconfirmed`](../backend/scinsight/lg/common.py#L201) | function |  | used | [annotated](../code_explorer/04_ai_ml/langgraph/scinsight_lg_common.py) |  |
| F0656 | [`context`](../backend/scinsight/lg/common.py#L206) | function |  | used | [annotated](../code_explorer/04_ai_ml/langgraph/scinsight_lg_common.py) |  |
| F0657 | [`_catalog`](../backend/scinsight/lg/common.py#L222) | function |  | used | [annotated](../code_explorer/04_ai_ml/langgraph/scinsight_lg_common.py) |  |
| F0658 | [`_name_hits`](../backend/scinsight/lg/common.py#L230) | function |  | used | [annotated](../code_explorer/04_ai_ml/langgraph/scinsight_lg_common.py) | How many meaningful words of a catalog name appear in the question (prefix match handles p |
| F0659 | [`detect_codes`](../backend/scinsight/lg/common.py#L237) | function |  | used | [annotated](../code_explorer/04_ai_ml/langgraph/scinsight_lg_common.py) | Deterministic identifier detection (codes first, then catalog names). Same rules as detect |
| F0660 | [`detect_codes.first`](../backend/scinsight/lg/common.py#L244) | nested |  | used | [annotated](../code_explorer/04_ai_ml/langgraph/scinsight_lg_common.py) |  |
| F0661 | [`merge_identifiers`](../backend/scinsight/lg/common.py#L278) | function |  | used | [annotated](../code_explorer/04_ai_ml/langgraph/scinsight_lg_common.py) | Code-detected identifiers win; the model only fills what code could not find. |
| F0662 | [`parse_extracted`](../backend/scinsight/lg/common.py#L283) | function |  | used | [annotated](../code_explorer/04_ai_ml/langgraph/scinsight_lg_common.py) | Lenient JSON parse of the identifier extraction (bare NONE / null tolerated, per-key fallb |
| F0663 | [`_val`](../backend/scinsight/lg/common.py#L297) | function |  | used | [annotated](../code_explorer/04_ai_ml/langgraph/scinsight_lg_common.py) |  |
| F0664 | [`_code`](../backend/scinsight/lg/common.py#L303) | function |  | used | [annotated](../code_explorer/04_ai_ml/langgraph/scinsight_lg_common.py) |  |
| F0665 | [`_num`](../backend/scinsight/lg/common.py#L308) | function |  | used | [annotated](../code_explorer/04_ai_ml/langgraph/scinsight_lg_common.py) |  |
| F0666 | [`_day`](../backend/scinsight/lg/common.py#L316) | function |  | used | [annotated](../code_explorer/04_ai_ml/langgraph/scinsight_lg_common.py) |  |
| F0667 | [`_done`](../backend/scinsight/lg/common.py#L321) | function |  | used | [annotated](../code_explorer/04_ai_ml/langgraph/scinsight_lg_common.py) |  |
| F0668 | [`_fail`](../backend/scinsight/lg/common.py#L328) | function |  | used | [annotated](../code_explorer/04_ai_ml/langgraph/scinsight_lg_common.py) |  |
| F0669 | [`calc_factory`](../backend/scinsight/lg/common.py#L332) | function |  | used | [annotated](../code_explorer/04_ai_ml/langgraph/scinsight_lg_common.py) |  |
| F0670 | [`calc_procurement`](../backend/scinsight/lg/common.py#L352) | function |  | used | [annotated](../code_explorer/04_ai_ml/langgraph/scinsight_lg_common.py) |  |
| F0671 | [`_balancing`](../backend/scinsight/lg/common.py#L376) | function |  | used | [annotated](../code_explorer/04_ai_ml/langgraph/scinsight_lg_common.py) |  |
| F0672 | [`calc_warehouse`](../backend/scinsight/lg/common.py#L384) | function |  | used | [annotated](../code_explorer/04_ai_ml/langgraph/scinsight_lg_common.py) |  |
| F0673 | [`calc_logistics`](../backend/scinsight/lg/common.py#L388) | function |  | used | [annotated](../code_explorer/04_ai_ml/langgraph/scinsight_lg_common.py) |  |
| F0674 | [`calc_inventory`](../backend/scinsight/lg/common.py#L392) | function |  | used | [annotated](../code_explorer/04_ai_ml/langgraph/scinsight_lg_common.py) |  |
| F0675 | [`calc_quality`](../backend/scinsight/lg/common.py#L409) | function |  | used | [annotated](../code_explorer/04_ai_ml/langgraph/scinsight_lg_common.py) |  |
| F0676 | [`calc_learning`](../backend/scinsight/lg/common.py#L417) | function |  | used | [annotated](../code_explorer/04_ai_ml/langgraph/scinsight_lg_common.py) |  |
| F0677 | [`calc_learning.v`](../backend/scinsight/lg/common.py#L452) | nested |  | used | [annotated](../code_explorer/04_ai_ml/langgraph/scinsight_lg_common.py) |  |
| F0678 | [`policy`](../backend/scinsight/lg/common.py#L474) | function |  | used | [annotated](../code_explorer/04_ai_ml/langgraph/scinsight_lg_common.py) |  |
| F0679 | [`numbers`](../backend/scinsight/lg/common.py#L489) | function |  | used | [annotated](../code_explorer/04_ai_ml/langgraph/scinsight_lg_common.py) |  |
| F0680 | [`unsupported_numbers`](../backend/scinsight/lg/common.py#L499) | function |  | used | [annotated](../code_explorer/04_ai_ml/langgraph/scinsight_lg_common.py) |  |
| F0681 | [`gate`](../backend/scinsight/lg/common.py#L504) | function |  | used | [annotated](../code_explorer/04_ai_ml/langgraph/scinsight_lg_common.py) |  |
| F0682 | [`guard`](../backend/scinsight/lg/common.py#L521) | function |  | used | [annotated](../code_explorer/04_ai_ml/langgraph/scinsight_lg_common.py) |  |
| F0683 | [`save`](../backend/scinsight/lg/common.py#L534) | function |  | used | [annotated](../code_explorer/04_ai_ml/langgraph/scinsight_lg_common.py) |  |
| F0684 | [`verify`](../backend/scinsight/lg/common.py#L552) | function |  | used | [annotated](../code_explorer/04_ai_ml/langgraph/scinsight_lg_common.py) |  |
| F0685 | [`withdraw`](../backend/scinsight/lg/common.py#L567) | function |  | used | [annotated](../code_explorer/04_ai_ml/langgraph/scinsight_lg_common.py) |  |

## backend/scinsight/lg/specialists.py

The 7 SCInsight specialists as LangGraph subgraphs, step for step the same as the Flowise specialist Agentflows:

| ID | Function | Kind | FastAPI route | Status | Annotated | Summary |
|---|---|---|---|---|---|---|
| F0686 | [`Input`](../backend/scinsight/lg/specialists.py#L38) | class |  | used | [annotated](../code_explorer/04_ai_ml/langgraph/scinsight_lg_specialists.py) |  |
| F0687 | [`Output`](../backend/scinsight/lg/specialists.py#L42) | class |  | used | [annotated](../code_explorer/04_ai_ml/langgraph/scinsight_lg_specialists.py) |  |
| F0688 | [`SpecialistState`](../backend/scinsight/lg/specialists.py#L48) | class |  | used | [annotated](../code_explorer/04_ai_ml/langgraph/scinsight_lg_specialists.py) |  |
| F0689 | [`last_question`](../backend/scinsight/lg/specialists.py#L66) | function |  | used | [annotated](../code_explorer/04_ai_ml/langgraph/scinsight_lg_specialists.py) |  |
| F0690 | [`build_specialist`](../backend/scinsight/lg/specialists.py#L70) | function |  | used | [annotated](../code_explorer/04_ai_ml/langgraph/scinsight_lg_specialists.py) |  |
| F0691 | [`build_specialist.check_access`](../backend/scinsight/lg/specialists.py#L73) | nested |  | used | [annotated](../code_explorer/04_ai_ml/langgraph/scinsight_lg_specialists.py) |  |
| F0692 | [`build_specialist.stop_access`](../backend/scinsight/lg/specialists.py#L77) | nested |  | used | [annotated](../code_explorer/04_ai_ml/langgraph/scinsight_lg_specialists.py) |  |
| F0693 | [`build_specialist.read_request`](../backend/scinsight/lg/specialists.py#L80) | nested |  | used | [annotated](../code_explorer/04_ai_ml/langgraph/scinsight_lg_specialists.py) |  |
| F0694 | [`build_specialist.calculate`](../backend/scinsight/lg/specialists.py#L85) | nested |  | used | [annotated](../code_explorer/04_ai_ml/langgraph/scinsight_lg_specialists.py) |  |
| F0695 | [`build_specialist.stop_input`](../backend/scinsight/lg/specialists.py#L89) | nested |  | used | [annotated](../code_explorer/04_ai_ml/langgraph/scinsight_lg_specialists.py) |  |
| F0696 | [`build_specialist.policy_search`](../backend/scinsight/lg/specialists.py#L92) | nested |  | used | [annotated](../code_explorer/04_ai_ml/langgraph/scinsight_lg_specialists.py) |  |
| F0697 | [`build_specialist.write_answer`](../backend/scinsight/lg/specialists.py#L95) | nested |  | used | [annotated](../code_explorer/04_ai_ml/langgraph/scinsight_lg_specialists.py) |  |
| F0698 | [`build_specialist.check_numbers`](../backend/scinsight/lg/specialists.py#L101) | nested |  | used | [annotated](../code_explorer/04_ai_ml/langgraph/scinsight_lg_specialists.py) |  |

## backend/scinsight/lg/supervisor.py

SC Agent Manager (supervisor) as a LangGraph graph, node for node the same as SCInsight-Cosmetics-Supervisor-Agentflow-v1:

| ID | Function | Kind | FastAPI route | Status | Annotated | Summary |
|---|---|---|---|---|---|---|
| F0699 | [`Input`](../backend/scinsight/lg/supervisor.py#L27) | class |  | used | [annotated](../code_explorer/04_ai_ml/langgraph/scinsight_lg_supervisor.py) |  |
| F0700 | [`Output`](../backend/scinsight/lg/supervisor.py#L32) | class |  | used | [annotated](../code_explorer/04_ai_ml/langgraph/scinsight_lg_supervisor.py) |  |
| F0701 | [`SupervisorState`](../backend/scinsight/lg/supervisor.py#L39) | class |  | used | [annotated](../code_explorer/04_ai_ml/langgraph/scinsight_lg_supervisor.py) |  |
| F0702 | [`_reply`](../backend/scinsight/lg/supervisor.py#L56) | function |  | used | [annotated](../code_explorer/04_ai_ml/langgraph/scinsight_lg_supervisor.py) |  |
| F0703 | [`check_access`](../backend/scinsight/lg/supervisor.py#L60) | function |  | used | [annotated](../code_explorer/04_ai_ml/langgraph/scinsight_lg_supervisor.py) |  |
| F0704 | [`stop_access`](../backend/scinsight/lg/supervisor.py#L68) | function |  | used | [annotated](../code_explorer/04_ai_ml/langgraph/scinsight_lg_supervisor.py) |  |
| F0705 | [`understand`](../backend/scinsight/lg/supervisor.py#L72) | function |  | used | [annotated](../code_explorer/04_ai_ml/langgraph/scinsight_lg_supervisor.py) |  |
| F0706 | [`safety_guard`](../backend/scinsight/lg/supervisor.py#L77) | function |  | used | [annotated](../code_explorer/04_ai_ml/langgraph/scinsight_lg_supervisor.py) |  |
| F0707 | [`route`](../backend/scinsight/lg/supervisor.py#L82) | function |  | used | [annotated](../code_explorer/04_ai_ml/langgraph/scinsight_lg_supervisor.py) |  |
| F0708 | [`specialist_node`](../backend/scinsight/lg/supervisor.py#L89) | function |  | used | [annotated](../code_explorer/04_ai_ml/langgraph/scinsight_lg_supervisor.py) |  |
| F0709 | [`specialist_node.run`](../backend/scinsight/lg/supervisor.py#L90) | nested |  | used | [annotated](../code_explorer/04_ai_ml/langgraph/scinsight_lg_supervisor.py) |  |
| F0710 | [`refuse_sap_change`](../backend/scinsight/lg/supervisor.py#L97) | function |  | used | [annotated](../code_explorer/04_ai_ml/langgraph/scinsight_lg_supervisor.py) |  |
| F0711 | [`out_of_scope`](../backend/scinsight/lg/supervisor.py#L101) | function |  | used | [annotated](../code_explorer/04_ai_ml/langgraph/scinsight_lg_supervisor.py) |  |
| F0712 | [`learning_report`](../backend/scinsight/lg/supervisor.py#L105) | function |  | used | [annotated](../code_explorer/04_ai_ml/langgraph/scinsight_lg_supervisor.py) |  |
| F0713 | [`save_recommendation`](../backend/scinsight/lg/supervisor.py#L109) | function |  | used | [annotated](../code_explorer/04_ai_ml/langgraph/scinsight_lg_supervisor.py) |  |
| F0714 | [`after_save`](../backend/scinsight/lg/supervisor.py#L113) | function |  | used | [annotated](../code_explorer/04_ai_ml/langgraph/scinsight_lg_supervisor.py) |  |
| F0715 | [`analysis_only`](../backend/scinsight/lg/supervisor.py#L119) | function |  | used | [annotated](../code_explorer/04_ai_ml/langgraph/scinsight_lg_supervisor.py) |  |
| F0716 | [`_approval_text`](../backend/scinsight/lg/supervisor.py#L123) | function |  | used | [annotated](../code_explorer/04_ai_ml/langgraph/scinsight_lg_supervisor.py) |  |
| F0717 | [`handoff`](../backend/scinsight/lg/supervisor.py#L128) | function |  | used | [annotated](../code_explorer/04_ai_ml/langgraph/scinsight_lg_supervisor.py) |  |
| F0718 | [`prepare_approval`](../backend/scinsight/lg/supervisor.py#L132) | function |  | used | [annotated](../code_explorer/04_ai_ml/langgraph/scinsight_lg_supervisor.py) |  |
| F0719 | [`human_approval`](../backend/scinsight/lg/supervisor.py#L136) | function |  | used | [annotated](../code_explorer/04_ai_ml/langgraph/scinsight_lg_supervisor.py) |  |
| F0720 | [`show_decision`](../backend/scinsight/lg/supervisor.py#L143) | function |  | used | [annotated](../code_explorer/04_ai_ml/langgraph/scinsight_lg_supervisor.py) |  |
| F0721 | [`withdraw`](../backend/scinsight/lg/supervisor.py#L147) | function |  | used | [annotated](../code_explorer/04_ai_ml/langgraph/scinsight_lg_supervisor.py) |  |
| F0722 | [`build_supervisor`](../backend/scinsight/lg/supervisor.py#L151) | function |  | used | [annotated](../code_explorer/04_ai_ml/langgraph/scinsight_lg_supervisor.py) |  |

## backend/scinsight/rag.py

Private RAG: Document -> Validate -> Extract -> Chunk -> Embed -> Store -> Retrieve -> Cite.

| ID | Function | Kind | FastAPI route | Status | Annotated | Summary |
|---|---|---|---|---|---|---|
| F0757 | [`DocumentError`](../backend/scinsight/rag.py#L37) | class |  | used | [annotated](../code_explorer/04_ai_ml/rag/scinsight_rag.py) |  |
| F0758 | [`parse_document`](../backend/scinsight/rag.py#L41) | function |  | used | [annotated](../code_explorer/04_ai_ml/rag/scinsight_rag.py) |  |
| F0759 | [`chunk_document`](../backend/scinsight/rag.py#L64) | function |  | unused? | [annotated](../code_explorer/04_ai_ml/rag/scinsight_rag.py) | Split on '## ' sections, then into <= size windows with overlap; each chunk carries its se |
| F0760 | [`HashEmbedder`](../backend/scinsight/rag.py#L71) | class |  | used | [annotated](../code_explorer/04_ai_ml/rag/scinsight_rag.py) |  |
| F1802 | [`HashEmbedder.__init__`](../backend/scinsight/rag.py#L72) | method |  | used (framework) | [annotated](../code_explorer/04_ai_ml/rag/scinsight_rag.py) |  |
| F0761 | [`HashEmbedder.embed`](../backend/scinsight/rag.py#L75) | method |  | used | [annotated](../code_explorer/04_ai_ml/rag/scinsight_rag.py) |  |
| F0762 | [`make_embedder`](../backend/scinsight/rag.py#L87) | function |  | used | [annotated](../code_explorer/04_ai_ml/rag/scinsight_rag.py) |  |
| F1803 | [`_vec`](../backend/scinsight/rag.py#L95) | function |  | used | [annotated](../code_explorer/04_ai_ml/rag/scinsight_rag.py) |  |
| F0763 | [`KnowledgeBase`](../backend/scinsight/rag.py#L99) | class |  | used | [annotated](../code_explorer/04_ai_ml/rag/scinsight_rag.py) |  |
| F0764 | [`KnowledgeBase.__init__`](../backend/scinsight/rag.py#L100) | method |  | used (framework) | [annotated](../code_explorer/04_ai_ml/rag/scinsight_rag.py) |  |
| F1804 | [`KnowledgeBase.embedder_for`](../backend/scinsight/rag.py#L104) | method |  | used | [annotated](../code_explorer/04_ai_ml/rag/scinsight_rag.py) | The embedder of an index: the service's own model, or another approved model (never a sile |
| F1805 | [`KnowledgeBase.baseline`](../backend/scinsight/rag.py#L111) | method |  | used | [annotated](../code_explorer/04_ai_ml/rag/scinsight_rag.py) |  |
| F1806 | [`KnowledgeBase.active`](../backend/scinsight/rag.py#L114) | method |  | used | [annotated](../code_explorer/04_ai_ml/rag/scinsight_rag.py) | (config version id, configuration, index version) used by live search for this tenant. |
| F1807 | [`KnowledgeBase._chunk_statements`](../backend/scinsight/rag.py#L122) | method |  | used | [annotated](../code_explorer/04_ai_ml/rag/scinsight_rag.py) |  |
| F0765 | [`KnowledgeBase.ingest_dir`](../backend/scinsight/rag.py#L138) | method |  | used | [annotated](../code_explorer/04_ai_ml/rag/scinsight_rag.py) | Validate and (re)index changed documents into each tenant's ACTIVE index (baseline when no |
| F1808 | [`KnowledgeBase.build_index`](../backend/scinsight/rag.py#L166) | method |  | used | [annotated](../code_explorer/04_ai_ml/rag/scinsight_rag.py) | Write a complete index version for one tenant (the active index is never touched). |
| F0766 | [`KnowledgeBase.search`](../backend/scinsight/rag.py#L183) | method |  | used | [annotated](../code_explorer/04_ai_ml/rag/scinsight_rag.py) | Tenant-, role- and date-filtered retrieval with citations, using the active configuration  |
| F1809 | [`KnowledgeBase._log`](../backend/scinsight/rag.py#L260) | method |  | used | [annotated](../code_explorer/04_ai_ml/rag/scinsight_rag.py) |  |

## backend/scinsight/rag_tuning/api.py

FastAPI routes of the RAG Tuning Console (SCInsight API, prefix /api/v1/rag-tuning).

| ID | Function | Kind | FastAPI route | Status | Annotated | Summary |
|---|---|---|---|---|---|---|
| F1810 | [`DraftRequest`](../backend/scinsight/rag_tuning/api.py#L38) | pydantic_model |  | used | — |  |
| F1811 | [`PreviewRequest`](../backend/scinsight/rag_tuning/api.py#L44) | pydantic_model |  | used | — |  |
| F1812 | [`RetrieveRequest`](../backend/scinsight/rag_tuning/api.py#L50) | pydantic_model |  | used | — |  |
| F1813 | [`ModelTestRequest`](../backend/scinsight/rag_tuning/api.py#L57) | pydantic_model |  | used | — |  |
| F1814 | [`ConfigRef`](../backend/scinsight/rag_tuning/api.py#L61) | pydantic_model |  | used | — |  |
| F1815 | [`EvaluateRequest`](../backend/scinsight/rag_tuning/api.py#L66) | pydantic_model |  | used | — |  |
| F1816 | [`GridRequest`](../backend/scinsight/rag_tuning/api.py#L72) | pydantic_model |  | used | — |  |
| F1817 | [`_llm_answer_fn`](../backend/scinsight/rag_tuning/api.py#L80) | function |  | used | — | OpenAI-compatible chat call (the same Qwen endpoint as the agents). Returns (answer, usage |
| F1818 | [`_llm_answer_fn.answer`](../backend/scinsight/rag_tuning/api.py#L85) | nested |  | used | — |  |
| F1819 | [`register`](../backend/scinsight/rag_tuning/api.py#L99) | function |  | used | — |  |
| F1820 | [`register.admin`](../backend/scinsight/rag_tuning/api.py#L106) | nested |  | used | — |  |
| F1821 | [`register.audit`](../backend/scinsight/rag_tuning/api.py#L110) | nested |  | used | — |  |
| F1822 | [`register.cfg_of`](../backend/scinsight/rag_tuning/api.py#L113) | nested |  | used | — |  |
| F1823 | [`register.job`](../backend/scinsight/rag_tuning/api.py#L120) | nested |  | used | — |  |
| F1824 | [`register.get_config`](../backend/scinsight/rag_tuning/api.py#L124) | route | GET /api/v1/rag-tuning/config | used | — |  |
| F1825 | [`register.save_draft`](../backend/scinsight/rag_tuning/api.py#L138) | route | PUT /api/v1/rag-tuning/draft | used | — |  |
| F1826 | [`register.history`](../backend/scinsight/rag_tuning/api.py#L144) | route | GET /api/v1/rag-tuning/history | used | — |  |
| F1827 | [`register.config_diff`](../backend/scinsight/rag_tuning/api.py#L148) | route | GET /api/v1/rag-tuning/diff/{config_id} | used | — |  |
| F1828 | [`register.list_documents`](../backend/scinsight/rag_tuning/api.py#L154) | route | GET /api/v1/rag-tuning/documents | used | — |  |
| F1829 | [`register.validate_metadata`](../backend/scinsight/rag_tuning/api.py#L158) | route | POST /api/v1/rag-tuning/metadata/validate | used | — |  |
| F1830 | [`register.document_source`](../backend/scinsight/rag_tuning/api.py#L166) | route | GET /api/v1/rag-tuning/documents/{doc_id}/source | used | — |  |
| F1831 | [`register.chunk_preview`](../backend/scinsight/rag_tuning/api.py#L174) | route | POST /api/v1/rag-tuning/chunks/preview | used | — |  |
| F1832 | [`register.embedding_models`](../backend/scinsight/rag_tuning/api.py#L187) | route | GET /api/v1/rag-tuning/embedding-models | used | — |  |
| F1833 | [`register.test_model`](../backend/scinsight/rag_tuning/api.py#L193) | route | POST /api/v1/rag-tuning/embedding-models/test | used | — |  |
| F1834 | [`register.build_candidate`](../backend/scinsight/rag_tuning/api.py#L202) | route | POST /api/v1/rag-tuning/index/build-candidate | used | — |  |
| F1835 | [`register.get_job`](../backend/scinsight/rag_tuning/api.py#L209) | route | GET /api/v1/rag-tuning/jobs/{job_id} | used | — |  |
| F1836 | [`register.retrieve_preview`](../backend/scinsight/rag_tuning/api.py#L217) | route | POST /api/v1/rag-tuning/retrieve/preview | used | — | retrieve_with_config: the live search function with a stored configuration and/or hot over |
| F1837 | [`register._benchmark`](../backend/scinsight/rag_tuning/api.py#L239) | nested |  | used | — |  |
| F1838 | [`register.evaluate`](../backend/scinsight/rag_tuning/api.py#L255) | route | POST /api/v1/rag-tuning/evaluate | used | — |  |
| F1839 | [`register.evaluate_grid`](../backend/scinsight/rag_tuning/api.py#L263) | route | POST /api/v1/rag-tuning/evaluate/grid | used | — | Shows the workload first; runs only when confirm=true (no silent Cartesian products). |
| F1840 | [`register.list_experiments`](../backend/scinsight/rag_tuning/api.py#L287) | route | GET /api/v1/rag-tuning/experiments | used | — |  |
| F1841 | [`register.compare`](../backend/scinsight/rag_tuning/api.py#L291) | route | GET /api/v1/rag-tuning/experiments/compare | used | — |  |
| F1842 | [`register.get_experiment`](../backend/scinsight/rag_tuning/api.py#L298) | route | GET /api/v1/rag-tuning/experiments/{exp_id} | used | — |  |
| F1843 | [`register.validate`](../backend/scinsight/rag_tuning/api.py#L306) | route | POST /api/v1/rag-tuning/validate | used | — |  |
| F1844 | [`register.publish`](../backend/scinsight/rag_tuning/api.py#L311) | route | POST /api/v1/rag-tuning/publish | used | — |  |
| F1845 | [`register.rollback`](../backend/scinsight/rag_tuning/api.py#L325) | route | POST /api/v1/rag-tuning/rollback | used | — |  |
| F1846 | [`register.flowise_status`](../backend/scinsight/rag_tuning/api.py#L340) | route | GET /api/v1/rag-tuning/flowise | used | — |  |
| F1847 | [`register.metrics`](../backend/scinsight/rag_tuning/api.py#L344) | route | GET /api/v1/rag-tuning/metrics | used | — |  |

## backend/scinsight/rag_tuning/chunking.py

Splitters for the governed documents. Sizes are characters.

| ID | Function | Kind | FastAPI route | Status | Annotated | Summary |
|---|---|---|---|---|---|---|
| F1848 | [`_sections`](../backend/scinsight/rag_tuning/chunking.py#L18) | function |  | used | — |  |
| F1849 | [`_windows`](../backend/scinsight/rag_tuning/chunking.py#L33) | function |  | used | — |  |
| F1850 | [`_clauses`](../backend/scinsight/rag_tuning/chunking.py#L44) | function |  | used | — |  |
| F1851 | [`chunk`](../backend/scinsight/rag_tuning/chunking.py#L71) | function |  | used | — | Chunks of one document: [{chunk_index, section, text (as indexed), content (without prefix |
| F1852 | [`overlap_chars`](../backend/scinsight/rag_tuning/chunking.py#L89) | function |  | used | — | Characters at the end of `left` repeated at the start of `right` (what the overlap actuall |
| F1853 | [`preview_document_chunks`](../backend/scinsight/rag_tuning/chunking.py#L97) | function |  | used | — | What the configuration would index for one document (nothing is written). |

## backend/scinsight/rag_tuning/config.py

The tunable RAG configuration: one validated object per configuration version.

| ID | Function | Kind | FastAPI route | Status | Annotated | Summary |
|---|---|---|---|---|---|---|
| F1854 | [`RagTuningConfig`](../backend/scinsight/rag_tuning/config.py#L26) | pydantic_model |  | used | — | One RAG configuration version. Cold fields define the index; hot fields only change how it |
| F1855 | [`RagTuningConfig.validate_chunking`](../backend/scinsight/rag_tuning/config.py#L48) | method |  | used (framework) | — |  |
| F1856 | [`baseline_config`](../backend/scinsight/rag_tuning/config.py#L58) | function |  | used | — | The configuration the service ran with before tuning existed (backend/scinsight/rag.py: 90 |
| F1857 | [`diff`](../backend/scinsight/rag_tuning/config.py#L63) | function |  | used | — | Changed settings, split into those that need a rebuild (cold) and those that apply at quer |
| F1858 | [`index_signature`](../backend/scinsight/rag_tuning/config.py#L70) | function |  | used | — | The cold settings: two configurations with the same signature can share one index. |

## backend/scinsight/rag_tuning/documents.py

Knowledge-base inventory and metadata quality checks. Deficiencies are reported as found; no value is ever invented.

| ID | Function | Kind | FastAPI route | Status | Annotated | Summary |
|---|---|---|---|---|---|---|
| F1859 | [`_front_matter`](../backend/scinsight/rag_tuning/documents.py#L17) | function |  | used | — |  |
| F1860 | [`inventory`](../backend/scinsight/rag_tuning/documents.py#L22) | function |  | used | — | Every source file of the caller's tenant with its metadata, index state and deficiencies ( |
| F1861 | [`validate_document_metadata`](../backend/scinsight/rag_tuning/documents.py#L56) | function |  | used | — | Checks on one document: missing fields, scope, validity and source quality (severity: erro |
| F1862 | [`_cross_document_checks`](../backend/scinsight/rag_tuning/documents.py#L83) | function |  | used | — |  |
| F1863 | [`source_text`](../backend/scinsight/rag_tuning/documents.py#L105) | function |  | used | — | The source document of the caller's tenant (front matter + body) for preview; other tenant |

## backend/scinsight/rag_tuning/embeddings.py

Backend-approved embedding models. The console can only pick from this list: a model id typed in the browser never

| ID | Function | Kind | FastAPI route | Status | Annotated | Summary |
|---|---|---|---|---|---|---|
| F1864 | [`ModelUnavailable`](../backend/scinsight/rag_tuning/embeddings.py#L30) | class |  | used | — |  |
| F1865 | [`approved`](../backend/scinsight/rag_tuning/embeddings.py#L34) | function |  | used | — |  |
| F1866 | [`_installed`](../backend/scinsight/rag_tuning/embeddings.py#L38) | function |  | used | — |  |
| F1867 | [`list_supported_embedding_models`](../backend/scinsight/rag_tuning/embeddings.py#L47) | function |  | used | — | The approved list with what is actually known about each model (installed, dimensions, lan |
| F1868 | [`get_embedder`](../backend/scinsight/rag_tuning/embeddings.py#L56) | function |  | used | — | Embedder for an approved model. Raises ModelUnavailable instead of substituting a differen |
| F1869 | [`test_model`](../backend/scinsight/rag_tuning/embeddings.py#L80) | function |  | used | — | Load the model (downloading it if allowed), embed sample texts, check dimensions and measu |

## backend/scinsight/rag_tuning/evaluation.py

Benchmark of a configuration on the versioned question set, through the real KnowledgeBase.search.

| ID | Function | Kind | FastAPI route | Status | Annotated | Summary |
|---|---|---|---|---|---|---|
| F1870 | [`load_dataset`](../backend/scinsight/rag_tuning/evaluation.py#L29) | function |  | used | — |  |
| F1871 | [`_p95`](../backend/scinsight/rag_tuning/evaluation.py#L35) | function |  | used | — |  |
| F1872 | [`score_case`](../backend/scinsight/rag_tuning/evaluation.py#L42) | function |  | used | — | Deterministic retrieval scores of one case. |
| F1873 | [`score_answer`](../backend/scinsight/rag_tuning/evaluation.py#L64) | function |  | used | — | Checks of an LLM answer against the retrieved evidence (deterministic; the model's confide |
| F1874 | [`run_rag_benchmark`](../backend/scinsight/rag_tuning/evaluation.py#L82) | function |  | used | — | Every case through KnowledgeBase.search (the function behind /api/v1/rag/search) with the  |
| F1875 | [`summarize`](../backend/scinsight/rag_tuning/evaluation.py#L103) | function |  | used | — |  |
| F1876 | [`summarize.mean`](../backend/scinsight/rag_tuning/evaluation.py#L104) | nested |  | used | — |  |
| F1877 | [`compare_experiments`](../backend/scinsight/rag_tuning/evaluation.py#L127) | function |  | used | — | Side-by-side measured metrics and a recommendation from the acceptance criteria (no invent |
| F1878 | [`compare_experiments.check`](../backend/scinsight/rag_tuning/evaluation.py#L136) | nested |  | used | — |  |

## backend/scinsight/rag_tuning/flowise_adapter.py

Keeps the Flowise chatflow's own Company RAG DB in step with the published configuration.

| ID | Function | Kind | FastAPI route | Status | Annotated | Summary |
|---|---|---|---|---|---|---|
| F1879 | [`FlowiseError`](../backend/scinsight/rag_tuning/flowise_adapter.py#L22) | class |  | used | — |  |
| F1880 | [`FlowiseAdapter`](../backend/scinsight/rag_tuning/flowise_adapter.py#L26) | class |  | used | — |  |
| F1881 | [`FlowiseAdapter.__init__`](../backend/scinsight/rag_tuning/flowise_adapter.py#L27) | method |  | used (framework) | — |  |
| F1882 | [`FlowiseAdapter.configured`](../backend/scinsight/rag_tuning/flowise_adapter.py#L30) | method |  | used (framework) | — |  |
| F1883 | [`FlowiseAdapter._call`](../backend/scinsight/rag_tuning/flowise_adapter.py#L34) | method |  | used | — |  |
| F1884 | [`FlowiseAdapter.chatflow`](../backend/scinsight/rag_tuning/flowise_adapter.py#L46) | method |  | used | — |  |
| F1885 | [`FlowiseAdapter._nodes`](../backend/scinsight/rag_tuning/flowise_adapter.py#L55) | method |  | used | — |  |
| F1886 | [`FlowiseAdapter.status`](../backend/scinsight/rag_tuning/flowise_adapter.py#L63) | method |  | used (framework) | — | What the live chatflow RAG DB uses right now, and what its table holds. |
| F1887 | [`FlowiseAdapter.table_rows`](../backend/scinsight/rag_tuning/flowise_adapter.py#L83) | method |  | used | — |  |
| F1888 | [`FlowiseAdapter.compatible`](../backend/scinsight/rag_tuning/flowise_adapter.py#L92) | method |  | used | — | Reasons the chatflow RAG DB cannot follow this configuration (empty = it can). |
| F1889 | [`FlowiseAdapter.sync`](../backend/scinsight/rag_tuning/flowise_adapter.py#L99) | method |  | used | — | Apply chunk size / overlap / top-k and the version tag to the chatflow, re-index it and ve |
| F1890 | [`FlowiseAdapter.restore`](../backend/scinsight/rag_tuning/flowise_adapter.py#L124) | method |  | used | — |  |

## backend/scinsight/rag_tuning/indexing.py

Candidate indexes: built next to the active index (separate index_version rows), validated, never published here.

| ID | Function | Kind | FastAPI route | Status | Annotated | Summary |
|---|---|---|---|---|---|---|
| F1891 | [`current_docs_sha`](../backend/scinsight/rag_tuning/indexing.py#L14) | function |  | used | — | doc_id:version -> sha256 of the source files that an index of this tenant must contain. |
| F1892 | [`build_candidate_index`](../backend/scinsight/rag_tuning/indexing.py#L27) | function |  | used | — | Index the tenant's documents with the configuration's cold settings under a new index vers |
| F1893 | [`validate_index`](../backend/scinsight/rag_tuning/indexing.py#L61) | function |  | used | — | Complete, single-model, right dimensions, and built from the current documents (not stale) |
| F1894 | [`list_indexes`](../backend/scinsight/rag_tuning/indexing.py#L86) | function |  | used | — |  |

## backend/scinsight/rag_tuning/publishing.py

Controlled publication: validate -> sync the Flowise chatflow RAG DB -> switch the active pointer. Rollback re-activates a

| ID | Function | Kind | FastAPI route | Status | Annotated | Summary |
|---|---|---|---|---|---|---|
| F1895 | [`validate_config`](../backend/scinsight/rag_tuning/publishing.py#L14) | function |  | used | — | Every check a configuration must pass before it can become active. |
| F1896 | [`validate_config.check`](../backend/scinsight/rag_tuning/publishing.py#L21) | nested |  | used | — |  |
| F1897 | [`_activate`](../backend/scinsight/rag_tuning/publishing.py#L53) | function |  | used | — |  |
| F1898 | [`publish_rag_config`](../backend/scinsight/rag_tuning/publishing.py#L78) | function |  | used | — |  |
| F1899 | [`rollback_rag_config`](../backend/scinsight/rag_tuning/publishing.py#L87) | function |  | used | — | Re-activate a version that was published before (its index is kept); refused if that index |

## backend/scinsight/rag_tuning/registry.py

Configuration versions, background jobs and experiment records (tables from migration 0003_rag_tuning.sql).

| ID | Function | Kind | FastAPI route | Status | Annotated | Summary |
|---|---|---|---|---|---|---|
| F1900 | [`_id`](../backend/scinsight/rag_tuning/registry.py#L13) | function |  | used | — |  |
| F1901 | [`_row`](../backend/scinsight/rag_tuning/registry.py#L17) | function |  | used | — |  |
| F1902 | [`Registry`](../backend/scinsight/rag_tuning/registry.py#L28) | class |  | used | — |  |
| F1903 | [`Registry.__init__`](../backend/scinsight/rag_tuning/registry.py#L29) | method |  | used (framework) | — |  |
| F1904 | [`Registry.ensure_baseline`](../backend/scinsight/rag_tuning/registry.py#L33) | method |  | used | — |  |
| F1905 | [`Registry.get_active_rag_config`](../backend/scinsight/rag_tuning/registry.py#L41) | method |  | used | — |  |
| F1906 | [`Registry.get`](../backend/scinsight/rag_tuning/registry.py#L45) | method |  | used | — |  |
| F1907 | [`Registry.history`](../backend/scinsight/rag_tuning/registry.py#L51) | method |  | used (framework) | — |  |
| F1908 | [`Registry.save_draft_config`](../backend/scinsight/rag_tuning/registry.py#L55) | method |  | used | — | Store a validated draft and say how it differs from the active configuration (and whether  |
| F1909 | [`Registry.set_status`](../backend/scinsight/rag_tuning/registry.py#L66) | method |  | used | — |  |
| F1910 | [`Registry.start_job`](../backend/scinsight/rag_tuning/registry.py#L72) | method |  | used | — | Run fn() in a background thread (HTTP returns at once; the console polls the job). |
| F1911 | [`Registry.start_job.run`](../backend/scinsight/rag_tuning/registry.py#L78) | nested |  | used | — |  |
| F1912 | [`Registry.job`](../backend/scinsight/rag_tuning/registry.py#L92) | method |  | used | — |  |
| F1913 | [`Registry.save_experiment`](../backend/scinsight/rag_tuning/registry.py#L99) | method |  | used | — |  |
| F1914 | [`Registry.experiments`](../backend/scinsight/rag_tuning/registry.py#L105) | method |  | used | — |  |
| F1915 | [`Registry.experiment`](../backend/scinsight/rag_tuning/registry.py#L110) | method |  | used | — |  |

## backend/scinsight/rag_tuning/retrieval.py

Ranking stage shared by live search and the tuning console (one implementation, so a preview equals production).

| ID | Function | Kind | FastAPI route | Status | Annotated | Summary |
|---|---|---|---|---|---|---|
| F1916 | [`terms`](../backend/scinsight/rag_tuning/retrieval.py#L19) | function |  | used | — |  |
| F1917 | [`keyword_score`](../backend/scinsight/rag_tuning/retrieval.py#L23) | function |  | used | — |  |
| F1918 | [`rank`](../backend/scinsight/rag_tuning/retrieval.py#L32) | function |  | used | — | Score and order chunk rows; returns copies with semantic / keyword / rerank / score fields |

## backend/scinsight/schemas.py

Request models. Strict (extra fields forbidden) so malformed or injected tool arguments are rejected with 422.

| ID | Function | Kind | FastAPI route | Status | Annotated | Summary |
|---|---|---|---|---|---|---|
| F0177 | [`Strict`](../backend/scinsight/schemas.py#L12) | pydantic_model |  | used (framework) | [annotated](../code_explorer/01_fastapi/pydantic_models/scinsight_schemas.py) |  |
| F0178 | [`ContextRequest`](../backend/scinsight/schemas.py#L16) | pydantic_model |  | used | [annotated](../code_explorer/01_fastapi/pydantic_models/scinsight_schemas.py) |  |
| F0179 | [`MaterialReadinessRequest`](../backend/scinsight/schemas.py#L20) | pydantic_model |  | used | [annotated](../code_explorer/01_fastapi/pydantic_models/scinsight_schemas.py) |  |
| F0180 | [`MaterialReadinessRequest._one_way`](../backend/scinsight/schemas.py#L27) | method |  | used (framework) | [annotated](../code_explorer/01_fastapi/pydantic_models/scinsight_schemas.py) |  |
| F0181 | [`WarehouseBalancingRequest`](../backend/scinsight/schemas.py#L37) | pydantic_model |  | used | [annotated](../code_explorer/01_fastapi/pydantic_models/scinsight_schemas.py) |  |
| F0182 | [`ReplenishmentRequest`](../backend/scinsight/schemas.py#L42) | pydantic_model |  | used | [annotated](../code_explorer/01_fastapi/pydantic_models/scinsight_schemas.py) |  |
| F0183 | [`DemandForecastRequest`](../backend/scinsight/schemas.py#L49) | pydantic_model |  | used | [annotated](../code_explorer/01_fastapi/pydantic_models/scinsight_schemas.py) |  |
| F0184 | [`LeadTimeRequest`](../backend/scinsight/schemas.py#L55) | pydantic_model |  | used | [annotated](../code_explorer/01_fastapi/pydantic_models/scinsight_schemas.py) |  |
| F0185 | [`QualityCheckRequest`](../backend/scinsight/schemas.py#L61) | pydantic_model |  | used | [annotated](../code_explorer/01_fastapi/pydantic_models/scinsight_schemas.py) |  |
| F0186 | [`RagSearchRequest`](../backend/scinsight/schemas.py#L67) | pydantic_model |  | used | [annotated](../code_explorer/01_fastapi/pydantic_models/scinsight_schemas.py) |  |
| F0187 | [`DecisionCreateRequest`](../backend/scinsight/schemas.py#L72) | pydantic_model |  | used | [annotated](../code_explorer/01_fastapi/pydantic_models/scinsight_schemas.py) |  |
| F0188 | [`ReviewRequest`](../backend/scinsight/schemas.py#L79) | pydantic_model |  | used | [annotated](../code_explorer/01_fastapi/pydantic_models/scinsight_schemas.py) |  |
| F0189 | [`SapExecutionRequest`](../backend/scinsight/schemas.py#L85) | pydantic_model |  | used | [annotated](../code_explorer/01_fastapi/pydantic_models/scinsight_schemas.py) |  |
| F0190 | [`ReconcileRequest`](../backend/scinsight/schemas.py#L91) | pydantic_model |  | used | [annotated](../code_explorer/01_fastapi/pydantic_models/scinsight_schemas.py) |  |
| F0191 | [`RetrainingRequest`](../backend/scinsight/schemas.py#L95) | pydantic_model |  | used | [annotated](../code_explorer/01_fastapi/pydantic_models/scinsight_schemas.py) |  |

## backend/scinsight/security.py

Authentication, tenant scoping, role checks and the tamper-evident audit chain.

| ID | Function | Kind | FastAPI route | Status | Annotated | Summary |
|---|---|---|---|---|---|---|
| F0772 | [`Principal`](../backend/scinsight/security.py#L32) | class |  | used | [annotated](../code_explorer/05_security_governance/authorization/scinsight_security.py) |  |
| F0773 | [`Principal.is_human`](../backend/scinsight/security.py#L39) | method |  | used (framework) | [annotated](../code_explorer/05_security_governance/authorization/scinsight_security.py) |  |
| F0774 | [`Security`](../backend/scinsight/security.py#L44) | class |  | used | [annotated](../code_explorer/05_security_governance/authorization/scinsight_security.py) |  |
| F0775 | [`Security.__init__`](../backend/scinsight/security.py#L45) | method |  | used (framework) | [annotated](../code_explorer/05_security_governance/authorization/scinsight_security.py) |  |
| F0776 | [`Security.authenticate`](../backend/scinsight/security.py#L48) | method |  | used | [annotated](../code_explorer/05_security_governance/authorization/scinsight_security.py) |  |
| F0777 | [`Security.require`](../backend/scinsight/security.py#L62) | method |  | used | [annotated](../code_explorer/05_security_governance/authorization/scinsight_security.py) |  |
| F0778 | [`Security.require_reviewer`](../backend/scinsight/security.py#L67) | method |  | used | [annotated](../code_explorer/05_security_governance/authorization/scinsight_security.py) |  |
| F0779 | [`Security.audit`](../backend/scinsight/security.py#L74) | method |  | used | [annotated](../code_explorer/05_security_governance/authorization/scinsight_security.py) |  |
| F0780 | [`Security.audit.write`](../backend/scinsight/security.py#L77) | nested |  | used | [annotated](../code_explorer/05_security_governance/authorization/scinsight_security.py) |  |
| F0781 | [`Security.verify_chain`](../backend/scinsight/security.py#L85) | method |  | used | [annotated](../code_explorer/05_security_governance/authorization/scinsight_security.py) |  |

## backend/scinsight/service.py

Use cases of the SupplyChain Insight AI business-tool service (called by the FastAPI routes and the tests).

| ID | Function | Kind | FastAPI route | Status | Annotated | Summary |
|---|---|---|---|---|---|---|
| F0311 | [`Service`](../backend/scinsight/service.py#L26) | class |  | used | [annotated](../code_explorer/02_business_logic/scinsight_use_cases/scinsight_service.py) |  |
| F0312 | [`Service.__init__`](../backend/scinsight/service.py#L27) | method |  | used (framework) | [annotated](../code_explorer/02_business_logic/scinsight_use_cases/scinsight_service.py) |  |
| F0313 | [`Service.snapshot`](../backend/scinsight/service.py#L31) | method |  | used | [annotated](../code_explorer/02_business_logic/scinsight_use_cases/scinsight_service.py) |  |
| F0314 | [`Service._save_run`](../backend/scinsight/service.py#L42) | method |  | used | [annotated](../code_explorer/02_business_logic/scinsight_use_cases/scinsight_service.py) |  |
| F0315 | [`Service.calculation`](../backend/scinsight/service.py#L52) | method |  | used | [annotated](../code_explorer/02_business_logic/scinsight_use_cases/scinsight_service.py) |  |
| F0316 | [`Service._batches`](../backend/scinsight/service.py#L58) | method |  | used | [annotated](../code_explorer/02_business_logic/scinsight_use_cases/scinsight_service.py) |  |
| F0317 | [`Service._demand`](../backend/scinsight/service.py#L65) | method |  | used | [annotated](../code_explorer/02_business_logic/scinsight_use_cases/scinsight_service.py) |  |
| F0318 | [`Service._require_item`](../backend/scinsight/service.py#L68) | method |  | used | [annotated](../code_explorer/02_business_logic/scinsight_use_cases/scinsight_service.py) |  |
| F0319 | [`Service.inventory`](../backend/scinsight/service.py#L78) | method |  | used | [annotated](../code_explorer/02_business_logic/scinsight_use_cases/scinsight_service.py) |  |
| F0320 | [`Service.bom`](../backend/scinsight/service.py#L99) | method |  | used | [annotated](../code_explorer/02_business_logic/scinsight_use_cases/scinsight_service.py) |  |
| F0321 | [`Service.table`](../backend/scinsight/service.py#L111) | method |  | used | [annotated](../code_explorer/02_business_logic/scinsight_use_cases/scinsight_service.py) |  |
| F0322 | [`Service.catalog`](../backend/scinsight/service.py#L120) | method |  | used | [annotated](../code_explorer/02_business_logic/scinsight_use_cases/scinsight_service.py) | Identifiers and names only (no quantities): lets an agent map 'vitamin C serum' to SER-VIT |
| F0323 | [`Service.suppliers`](../backend/scinsight/service.py#L133) | method |  | used | [annotated](../code_explorer/02_business_logic/scinsight_use_cases/scinsight_service.py) |  |
| F0324 | [`Service._supplier_options`](../backend/scinsight/service.py#L142) | method |  | used | [annotated](../code_explorer/02_business_logic/scinsight_use_cases/scinsight_service.py) |  |
| F0325 | [`Service.material_readiness`](../backend/scinsight/service.py#L160) | method |  | used | [annotated](../code_explorer/02_business_logic/scinsight_use_cases/scinsight_service.py) |  |
| F0326 | [`Service._sites`](../backend/scinsight/service.py#L232) | method |  | used | [annotated](../code_explorer/02_business_logic/scinsight_use_cases/scinsight_service.py) |  |
| F0327 | [`Service.warehouse_balancing`](../backend/scinsight/service.py#L240) | method |  | used | [annotated](../code_explorer/02_business_logic/scinsight_use_cases/scinsight_service.py) |  |
| F0328 | [`Service.replenishment`](../backend/scinsight/service.py#L291) | method |  | used | [annotated](../code_explorer/02_business_logic/scinsight_use_cases/scinsight_service.py) |  |
| F0329 | [`Service.quality_check`](../backend/scinsight/service.py#L312) | method |  | used | [annotated](../code_explorer/02_business_logic/scinsight_use_cases/scinsight_service.py) |  |
| F0330 | [`Service.forecast_demand`](../backend/scinsight/service.py#L326) | method |  | used | [annotated](../code_explorer/02_business_logic/scinsight_use_cases/scinsight_service.py) |  |
| F0331 | [`Service.forecast_demand.predict`](../backend/scinsight/service.py#L333) | nested |  | used | [annotated](../code_explorer/02_business_logic/scinsight_use_cases/scinsight_service.py) |  |
| F0332 | [`Service.lead_time`](../backend/scinsight/service.py#L351) | method |  | used | [annotated](../code_explorer/02_business_logic/scinsight_use_cases/scinsight_service.py) |  |
| F0333 | [`Service.create_decision`](../backend/scinsight/service.py#L374) | method |  | used | [annotated](../code_explorer/02_business_logic/scinsight_use_cases/scinsight_service.py) |  |
| F0334 | [`Service._rec`](../backend/scinsight/service.py#L400) | method |  | used | [annotated](../code_explorer/02_business_logic/scinsight_use_cases/scinsight_service.py) |  |
| F0335 | [`Service.get_decision`](../backend/scinsight/service.py#L406) | method |  | used | [annotated](../code_explorer/02_business_logic/scinsight_use_cases/scinsight_service.py) |  |
| F0336 | [`Service.list_decisions`](../backend/scinsight/service.py#L418) | method |  | used | [annotated](../code_explorer/02_business_logic/scinsight_use_cases/scinsight_service.py) |  |
| F0337 | [`Service.review`](../backend/scinsight/service.py#L423) | method |  | used | [annotated](../code_explorer/02_business_logic/scinsight_use_cases/scinsight_service.py) |  |
| F0338 | [`Service.review.apply`](../backend/scinsight/service.py#L430) | nested |  | used | [annotated](../code_explorer/02_business_logic/scinsight_use_cases/scinsight_service.py) |  |
| F0339 | [`Service.withdraw`](../backend/scinsight/service.py#L444) | method |  | used | [annotated](../code_explorer/02_business_logic/scinsight_use_cases/scinsight_service.py) |  |
| F0340 | [`Service.record_sap_execution`](../backend/scinsight/service.py#L453) | method |  | used | [annotated](../code_explorer/02_business_logic/scinsight_use_cases/scinsight_service.py) |  |
| F0341 | [`Service.reconcile`](../backend/scinsight/service.py#L469) | method |  | used | [annotated](../code_explorer/02_business_logic/scinsight_use_cases/scinsight_service.py) |  |
| F0342 | [`Service.reconcile.write`](../backend/scinsight/service.py#L489) | nested |  | used | [annotated](../code_explorer/02_business_logic/scinsight_use_cases/scinsight_service.py) |  |
| F0343 | [`Service.learning_metrics`](../backend/scinsight/service.py#L509) | method |  | used | [annotated](../code_explorer/02_business_logic/scinsight_use_cases/scinsight_service.py) |  |

## backend/scinsight/settings.py

Runtime settings for the SupplyChain Insight AI service (environment variables; see .env.example).

| ID | Function | Kind | FastAPI route | Status | Annotated | Summary |
|---|---|---|---|---|---|---|
| F0013 | [`SciSettings`](../backend/scinsight/settings.py#L13) | pydantic_model |  | used | [annotated](../code_explorer/01_fastapi/app_setup/scinsight_settings.py) |  |
| F0014 | [`SciSettings.user_keys`](../backend/scinsight/settings.py#L52) | method |  | used | [annotated](../code_explorer/01_fastapi/app_setup/scinsight_settings.py) |  |
| F0015 | [`SciSettings.missing_keys`](../backend/scinsight/settings.py#L55) | method |  | used | [annotated](../code_explorer/01_fastapi/app_setup/scinsight_settings.py) |  |
