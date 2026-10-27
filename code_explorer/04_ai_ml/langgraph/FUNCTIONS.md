# 04_ai_ml/langgraph (generated)

Modules: `backend/app/agentflow.py`, `backend/app/deep_agent.py`, `backend/app/graphs.py`, `backend/app/runner.py`, `backend/scinsight/lg/chat.py`, `backend/scinsight/lg/common.py`, `backend/scinsight/lg/specialists.py`, `backend/scinsight/lg/supervisor.py`, `scripts/langgraph_assistants.py`

| ID | Function / class | Kind | Status | Original | Annotated copy | Summary |
|---|---|---|---|---|---|---|
| F0538 | `AgentFlowState` | class | used | [backend/app/agentflow.py:61](../../../backend/app/agentflow.py#L61) | [annotated](../../04_ai_ml/langgraph/app_agentflow.py) |  |
| F0539 | `RouteDecision` | pydantic_model | used | [backend/app/agentflow.py:71](../../../backend/app/agentflow.py#L71) | [annotated](../../04_ai_ml/langgraph/app_agentflow.py) | Pick exactly one role specialist for the planner's latest request. |
| F0540 | `_last_human` | function | used | [backend/app/agentflow.py:82](../../../backend/app/agentflow.py#L82) | [annotated](../../04_ai_ml/langgraph/app_agentflow.py) |  |
| F0541 | `sap_read` | function | used | [backend/app/agentflow.py:87](../../../backend/app/agentflow.py#L87) | [annotated](../../04_ai_ml/langgraph/app_agentflow.py) | Read the SAP S/4HANA snapshot provenance and valid codes (read-only; writes are  |
| F0542 | `rag_retrieve` | function | used | [backend/app/agentflow.py:99](../../../backend/app/agentflow.py#L99) | [annotated](../../04_ai_ml/langgraph/app_agentflow.py) | Retrieve governed policy context (contracts, SOPs, quality and logistics policie |
| F0543 | `_keyword_route` | function | used | [backend/app/agentflow.py:122](../../../backend/app/agentflow.py#L122) | [annotated](../../04_ai_ml/langgraph/app_agentflow.py) |  |
| F0544 | `supervisor` | function | used | [backend/app/agentflow.py:132](../../../backend/app/agentflow.py#L132) | [annotated](../../04_ai_ml/langgraph/app_agentflow.py) |  |
| F0545 | `route_next` | function | used | [backend/app/agentflow.py:147](../../../backend/app/agentflow.py#L147) | [annotated](../../04_ai_ml/langgraph/app_agentflow.py) |  |
| F0546 | `_conversation` | function | used | [backend/app/agentflow.py:152](../../../backend/app/agentflow.py#L152) | [annotated](../../04_ai_ml/langgraph/app_agentflow.py) | Prior human turns and final answers only, so specialists never see dangling tool |
| F0547 | `_analysis_from` | function | used | [backend/app/agentflow.py:158](../../../backend/app/agentflow.py#L158) | [annotated](../../04_ai_ml/langgraph/app_agentflow.py) |  |
| F0548 | `_deterministic` | function | used | [backend/app/agentflow.py:171](../../../backend/app/agentflow.py#L171) | [annotated](../../04_ai_ml/langgraph/app_agentflow.py) |  |
| F0549 | `_knowledge_block` | function | used | [backend/app/agentflow.py:192](../../../backend/app/agentflow.py#L192) | [annotated](../../04_ai_ml/langgraph/app_agentflow.py) |  |
| F0550 | `_specialist` | function | used | [backend/app/agentflow.py:200](../../../backend/app/agentflow.py#L200) | [annotated](../../04_ai_ml/langgraph/app_agentflow.py) |  |
| F0551 | `_specialist.node` | nested | used | [backend/app/agentflow.py:206](../../../backend/app/agentflow.py#L206) | [annotated](../../04_ai_ml/langgraph/app_agentflow.py) |  |
| F0552 | `approval_gate` | function | used | [backend/app/agentflow.py:234](../../../backend/app/agentflow.py#L234) | [annotated](../../04_ai_ml/langgraph/app_agentflow.py) | Planner Human Input: submit the specialist's stored analysis to the manager queu |
| F0553 | `boundary` | function | used | [backend/app/agentflow.py:262](../../../backend/app/agentflow.py#L262) | [annotated](../../04_ai_ml/langgraph/app_agentflow.py) |  |
| F0554 | `harness_of` | function | used | [backend/app/deep_agent.py:62](../../../backend/app/deep_agent.py#L62) | [annotated](../../04_ai_ml/langgraph/app_deep_agent.py) | Validated harness: stored settings merged over the defaults (invalid or unknown  |
| F0555 | `system_prompt` | function | used | [backend/app/deep_agent.py:67](../../../backend/app/deep_agent.py#L67) | [annotated](../../04_ai_ml/langgraph/app_deep_agent.py) |  |
| F0556 | `_this_run` | function | used | [backend/app/deep_agent.py:94](../../../backend/app/deep_agent.py#L94) | [annotated](../../04_ai_ml/langgraph/app_deep_agent.py) | Messages of the current run: everything after the last user message (limits rese |
| F0557 | `HarnessGuard` | class | used | [backend/app/deep_agent.py:100](../../../backend/app/deep_agent.py#L100) | [annotated](../../04_ai_ml/langgraph/app_deep_agent.py) | Loop controls of the harness, enforced around each model and tool call (no extra |
| F0558 | `HarnessGuard.__init__` | method | used (framework) | [backend/app/deep_agent.py:108](../../../backend/app/deep_agent.py#L108) | [annotated](../../04_ai_ml/langgraph/app_deep_agent.py) |  |
| F0559 | `HarnessGuard._stop_message` | method | used | [backend/app/deep_agent.py:112](../../../backend/app/deep_agent.py#L112) | [annotated](../../04_ai_ml/langgraph/app_deep_agent.py) |  |
| F0560 | `HarnessGuard._refusal` | method | used | [backend/app/deep_agent.py:119](../../../backend/app/deep_agent.py#L119) | [annotated](../../04_ai_ml/langgraph/app_deep_agent.py) |  |
| F0561 | `HarnessGuard.wrap_model_call` | method | used | [backend/app/deep_agent.py:145](../../../backend/app/deep_agent.py#L145) | [annotated](../../04_ai_ml/langgraph/app_deep_agent.py) |  |
| F0562 | `HarnessGuard.awrap_model_call` | method | used (framework) | [backend/app/deep_agent.py:148](../../../backend/app/deep_agent.py#L148) | [annotated](../../04_ai_ml/langgraph/app_deep_agent.py) |  |
| F0563 | `HarnessGuard.wrap_tool_call` | method | used | [backend/app/deep_agent.py:151](../../../backend/app/deep_agent.py#L151) | [annotated](../../04_ai_ml/langgraph/app_deep_agent.py) |  |
| F0564 | `HarnessGuard.awrap_tool_call` | method | used (framework) | [backend/app/deep_agent.py:154](../../../backend/app/deep_agent.py#L154) | [annotated](../../04_ai_ml/langgraph/app_deep_agent.py) |  |
| F0565 | `build_deep_agent` | function | used | [backend/app/deep_agent.py:158](../../../backend/app/deep_agent.py#L158) | [annotated](../../04_ai_ml/langgraph/app_deep_agent.py) | The Deep Agent for one harness (compiled LangGraph with model, tools and subagen |
| F0566 | `_agent_for` | function | used | [backend/app/deep_agent.py:180](../../../backend/app/deep_agent.py#L180) | [annotated](../../04_ai_ml/langgraph/app_deep_agent.py) |  |
| F0567 | `ResearchState` | class | used | [backend/app/deep_agent.py:187](../../../backend/app/deep_agent.py#L187) | [annotated](../../04_ai_ml/langgraph/app_deep_agent.py) |  |
| F0568 | `ResearchInput` | class | used | [backend/app/deep_agent.py:194](../../../backend/app/deep_agent.py#L194) | [annotated](../../04_ai_ml/langgraph/app_deep_agent.py) | What a run takes (Studio's Input form): the question, and optionally harness ove |
| F0569 | `HarnessConfig` | pydantic_model | used | [backend/app/deep_agent.py:199](../../../backend/app/deep_agent.py#L199) | [annotated](../../04_ai_ml/langgraph/app_deep_agent.py) | Assistant context: Studio's configuration panel shows every harness setting with |
| F0570 | `_context_harness` | function | used | [backend/app/deep_agent.py:204](../../../backend/app/deep_agent.py#L204) | [annotated](../../04_ai_ml/langgraph/app_deep_agent.py) | Harness settings given in the run/assistant context (only the ones actually set, |
| F0571 | `deep_research` | function | used | [backend/app/deep_agent.py:211](../../../backend/app/deep_agent.py#L211) | [annotated](../../04_ai_ml/langgraph/app_deep_agent.py) | Run the Deep Agent configured by this run's harness settings. |
| F0572 | `build_graph` | function | used | [backend/app/deep_agent.py:225](../../../backend/app/deep_agent.py#L225) | [annotated](../../04_ai_ml/langgraph/app_deep_agent.py) |  |
| F0573 | `_last_text` | function | used | [backend/app/graphs.py:51](../../../backend/app/graphs.py#L51) | [annotated](../../04_ai_ml/langgraph/app_graphs.py) |  |
| F0574 | `guard` | function | used | [backend/app/graphs.py:55](../../../backend/app/graphs.py#L55) | [annotated](../../04_ai_ml/langgraph/app_graphs.py) |  |
| F0575 | `route_after_guard` | function | used | [backend/app/graphs.py:59](../../../backend/app/graphs.py#L59) | [annotated](../../04_ai_ml/langgraph/app_graphs.py) |  |
| F0576 | `refuse` | function | used | [backend/app/graphs.py:65](../../../backend/app/graphs.py#L65) | [annotated](../../04_ai_ml/langgraph/app_graphs.py) |  |
| F0577 | `_tool_rounds` | function | used | [backend/app/graphs.py:69](../../../backend/app/graphs.py#L69) | [annotated](../../04_ai_ml/langgraph/app_graphs.py) |  |
| F0578 | `ChatState` | class | used | [backend/app/graphs.py:79](../../../backend/app/graphs.py#L79) | [annotated](../../04_ai_ml/langgraph/app_graphs.py) |  |
| F0579 | `_role_setup` | function | used | [backend/app/graphs.py:83](../../../backend/app/graphs.py#L83) | [annotated](../../04_ai_ml/langgraph/app_graphs.py) | System prompt and tool set for the role's specialised agent; no role = the gener |
| F0580 | `agent` | function | used | [backend/app/graphs.py:95](../../../backend/app/graphs.py#L95) | [annotated](../../04_ai_ml/langgraph/app_graphs.py) |  |
| F0581 | `_first_human` | function | used | [backend/app/graphs.py:109](../../../backend/app/graphs.py#L109) | [annotated](../../04_ai_ml/langgraph/app_graphs.py) |  |
| F0582 | `route_after_agent` | function | used | [backend/app/graphs.py:116](../../../backend/app/graphs.py#L116) | [annotated](../../04_ai_ml/langgraph/app_graphs.py) |  |
| F0583 | `fallback_answer` | function | used | [backend/app/graphs.py:121](../../../backend/app/graphs.py#L121) | [annotated](../../04_ai_ml/langgraph/app_graphs.py) | Deterministic keyword router used when no LLM is configured; it only restates en |
| F0584 | `fallback` | function | used | [backend/app/graphs.py:149](../../../backend/app/graphs.py#L149) | [annotated](../../04_ai_ml/langgraph/app_graphs.py) |  |
| F0585 | `traced` | function | used | [backend/app/graphs.py:167](../../../backend/app/graphs.py#L167) | [annotated](../../04_ai_ml/langgraph/app_graphs.py) | Attach Langfuse tracing to a compiled graph (still a Pregel graph, so LangGraph  |
| F0586 | `BusinessState` | class | used | [backend/app/graphs.py:180](../../../backend/app/graphs.py#L180) | [annotated](../../04_ai_ml/langgraph/app_graphs.py) |  |
| F0587 | `ExtractedRequest` | pydantic_model | used | [backend/app/graphs.py:202](../../../backend/app/graphs.py#L202) | [annotated](../../04_ai_ml/langgraph/app_graphs.py) | Structured parameters for a supply-chain request. Leave a field empty when it is |
| F0588 | `_regex_extract` | function | used | [backend/app/graphs.py:214](../../../backend/app/graphs.py#L214) | [annotated](../../04_ai_ml/langgraph/app_graphs.py) |  |
| F0589 | `intake` | function | used | [backend/app/graphs.py:248](../../../backend/app/graphs.py#L248) | [annotated](../../04_ai_ml/langgraph/app_graphs.py) | Fill missing parameters from free text: Qwen structured output, deterministic re |
| F0590 | `validate` | function | used | [backend/app/graphs.py:271](../../../backend/app/graphs.py#L271) | [annotated](../../04_ai_ml/langgraph/app_graphs.py) |  |
| F0591 | `route_workflow` | function | used | [backend/app/graphs.py:299](../../../backend/app/graphs.py#L299) | [annotated](../../04_ai_ml/langgraph/app_graphs.py) |  |
| F0592 | `run_factory` | function | used | [backend/app/graphs.py:303](../../../backend/app/graphs.py#L303) | [annotated](../../04_ai_ml/langgraph/app_graphs.py) |  |
| F0593 | `run_balance` | function | used | [backend/app/graphs.py:308](../../../backend/app/graphs.py#L308) | [annotated](../../04_ai_ml/langgraph/app_graphs.py) |  |
| F0594 | `run_supplier` | function | used | [backend/app/graphs.py:313](../../../backend/app/graphs.py#L313) | [annotated](../../04_ai_ml/langgraph/app_graphs.py) |  |
| F0595 | `run_quality` | function | used | [backend/app/graphs.py:318](../../../backend/app/graphs.py#L318) | [annotated](../../04_ai_ml/langgraph/app_graphs.py) |  |
| F0596 | `run_logistics` | function | used | [backend/app/graphs.py:323](../../../backend/app/graphs.py#L323) | [annotated](../../04_ai_ml/langgraph/app_graphs.py) |  |
| F0597 | `run_inventory` | function | used | [backend/app/graphs.py:328](../../../backend/app/graphs.py#L328) | [annotated](../../04_ai_ml/langgraph/app_graphs.py) |  |
| F0598 | `policy_context` | function | used | [backend/app/graphs.py:343](../../../backend/app/graphs.py#L343) | [annotated](../../04_ai_ml/langgraph/app_graphs.py) |  |
| F0599 | `explain` | function | used | [backend/app/graphs.py:350](../../../backend/app/graphs.py#L350) | [annotated](../../04_ai_ml/langgraph/app_graphs.py) |  |
| F0600 | `needs_approval` | function | used | [backend/app/graphs.py:372](../../../backend/app/graphs.py#L372) | [annotated](../../04_ai_ml/langgraph/app_graphs.py) |  |
| F0601 | `approval_gate` | function | used | [backend/app/graphs.py:376](../../../backend/app/graphs.py#L376) | [annotated](../../04_ai_ml/langgraph/app_graphs.py) | Human-in-the-loop: the planner decides whether the advisory recommendation goes  |
| F0602 | `route_approval` | function | used | [backend/app/graphs.py:395](../../../backend/app/graphs.py#L395) | [annotated](../../04_ai_ml/langgraph/app_graphs.py) |  |
| F0603 | `submit` | function | used | [backend/app/graphs.py:399](../../../backend/app/graphs.py#L399) | [annotated](../../04_ai_ml/langgraph/app_graphs.py) |  |
| F0604 | `discard` | function | used | [backend/app/graphs.py:406](../../../backend/app/graphs.py#L406) | [annotated](../../04_ai_ml/langgraph/app_graphs.py) |  |
| F0605 | `no_action` | function | used | [backend/app/graphs.py:410](../../../backend/app/graphs.py#L410) | [annotated](../../04_ai_ml/langgraph/app_graphs.py) |  |
| F0606 | `rejected` | function | used | [backend/app/graphs.py:414](../../../backend/app/graphs.py#L414) | [annotated](../../04_ai_ml/langgraph/app_graphs.py) |  |
| F0607 | `_message_dict` | function | used | [backend/app/runner.py:15](../../../backend/app/runner.py#L15) | [annotated](../../04_ai_ml/langgraph/app_runner.py) |  |
| F0608 | `normalise` | function | used | [backend/app/runner.py:36](../../../backend/app/runner.py#L36) | [annotated](../../04_ai_ml/langgraph/app_runner.py) |  |
| F0609 | `LocalRunner` | class | used | [backend/app/runner.py:45](../../../backend/app/runner.py#L45) | [annotated](../../04_ai_ml/langgraph/app_runner.py) |  |
| F0610 | `LocalRunner.__init__` | method | used (framework) | [backend/app/runner.py:48](../../../backend/app/runner.py#L48) | [annotated](../../04_ai_ml/langgraph/app_runner.py) |  |
| F0611 | `LocalRunner._checkpointer` | method | used (framework) | [backend/app/runner.py:54](../../../backend/app/runner.py#L54) | [annotated](../../04_ai_ml/langgraph/app_runner.py) |  |
| F0612 | `LocalRunner.graph` | method | used | [backend/app/runner.py:68](../../../backend/app/runner.py#L68) | [annotated](../../04_ai_ml/langgraph/app_runner.py) |  |
| F0613 | `LocalRunner._result` | method | used | [backend/app/runner.py:86](../../../backend/app/runner.py#L86) | [annotated](../../04_ai_ml/langgraph/app_runner.py) |  |
| F0614 | `LocalRunner.run` | method | used | [backend/app/runner.py:91](../../../backend/app/runner.py#L91) | [annotated](../../04_ai_ml/langgraph/app_runner.py) |  |
| F0615 | `LocalRunner.resume` | method | used | [backend/app/runner.py:99](../../../backend/app/runner.py#L99) | [annotated](../../04_ai_ml/langgraph/app_runner.py) |  |
| F0616 | `RemoteRunner` | class | used | [backend/app/runner.py:109](../../../backend/app/runner.py#L109) | [annotated](../../04_ai_ml/langgraph/app_runner.py) | LangGraph Server (the same server LangSmith Studio connects to). |
| F0617 | `RemoteRunner.__init__` | method | used (framework) | [backend/app/runner.py:114](../../../backend/app/runner.py#L114) | [annotated](../../04_ai_ml/langgraph/app_runner.py) |  |
| F0618 | `RemoteRunner._result` | method | used | [backend/app/runner.py:120](../../../backend/app/runner.py#L120) | [annotated](../../04_ai_ml/langgraph/app_runner.py) |  |
| F0619 | `RemoteRunner.run` | method | used | [backend/app/runner.py:127](../../../backend/app/runner.py#L127) | [annotated](../../04_ai_ml/langgraph/app_runner.py) |  |
| F0620 | `RemoteRunner.resume` | method | used | [backend/app/runner.py:135](../../../backend/app/runner.py#L135) | [annotated](../../04_ai_ml/langgraph/app_runner.py) |  |
| F0621 | `GraphRunner` | class | used | [backend/app/runner.py:142](../../../backend/app/runner.py#L142) | [annotated](../../04_ai_ml/langgraph/app_runner.py) |  |
| F0622 | `GraphRunner.__init__` | method | used (framework) | [backend/app/runner.py:143](../../../backend/app/runner.py#L143) | [annotated](../../04_ai_ml/langgraph/app_runner.py) |  |
| F0623 | `GraphRunner.impl` | method | used | [backend/app/runner.py:147](../../../backend/app/runner.py#L147) | [annotated](../../04_ai_ml/langgraph/app_runner.py) |  |
| F0624 | `GraphRunner.mode` | method | used | [backend/app/runner.py:153](../../../backend/app/runner.py#L153) | [annotated](../../04_ai_ml/langgraph/app_runner.py) |  |
| F0625 | `GraphRunner._timed` | method | used | [backend/app/runner.py:157](../../../backend/app/runner.py#L157) | [annotated](../../04_ai_ml/langgraph/app_runner.py) |  |
| F0626 | `GraphRunner.run` | method | used | [backend/app/runner.py:169](../../../backend/app/runner.py#L169) | [annotated](../../04_ai_ml/langgraph/app_runner.py) |  |
| F0627 | `GraphRunner.resume` | method | used | [backend/app/runner.py:172](../../../backend/app/runner.py#L172) | [annotated](../../04_ai_ml/langgraph/app_runner.py) |  |
| F0628 | `ask_sc_agent_manager` | function | used | [backend/scinsight/lg/chat.py:31](../../../backend/scinsight/lg/chat.py#L31) | [annotated](../../04_ai_ml/langgraph/scinsight_lg_chat.py) | The SC Agent Manager (supervisor). Use it for EVERY planning or analysis questio |
| F0629 | `search_supply_chain_policy` | function | used | [backend/scinsight/lg/chat.py:43](../../../backend/scinsight/lg/chat.py#L43) | [annotated](../../04_ai_ml/langgraph/scinsight_lg_chat.py) | Search the governed policy, SOP, specification and supplier-agreement documents  |
| F0630 | `ChatState` | class | used | [backend/scinsight/lg/chat.py:56](../../../backend/scinsight/lg/chat.py#L56) | [annotated](../../04_ai_ml/langgraph/scinsight_lg_chat.py) |  |
| F0631 | `_this_turn` | function | used | [backend/scinsight/lg/chat.py:60](../../../backend/scinsight/lg/chat.py#L60) | [annotated](../../04_ai_ml/langgraph/scinsight_lg_chat.py) |  |
| F0632 | `guardrail` | function | used | [backend/scinsight/lg/chat.py:65](../../../backend/scinsight/lg/chat.py#L65) | [annotated](../../04_ai_ml/langgraph/scinsight_lg_chat.py) |  |
| F0633 | `blocked` | function | used | [backend/scinsight/lg/chat.py:69](../../../backend/scinsight/lg/chat.py#L69) | [annotated](../../04_ai_ml/langgraph/scinsight_lg_chat.py) |  |
| F0634 | `assistant` | function | used | [backend/scinsight/lg/chat.py:73](../../../backend/scinsight/lg/chat.py#L73) | [annotated](../../04_ai_ml/langgraph/scinsight_lg_chat.py) |  |
| F0635 | `evidence_gate` | function | used | [backend/scinsight/lg/chat.py:81](../../../backend/scinsight/lg/chat.py#L81) | [annotated](../../04_ai_ml/langgraph/scinsight_lg_chat.py) | Port of the Flowise post-processing: every number must exist in this turn's tool |
| F0636 | `build_chat` | function | used | [backend/scinsight/lg/chat.py:108](../../../backend/scinsight/lg/chat.py#L108) | [annotated](../../04_ai_ml/langgraph/scinsight_lg_chat.py) |  |
| F0637 | `out_of_scope_reply` | function | used | [backend/scinsight/lg/common.py:30](../../../backend/scinsight/lg/common.py#L30) | [annotated](../../04_ai_ml/langgraph/scinsight_lg_common.py) |  |
| F0638 | `client` | function | used | [backend/scinsight/lg/common.py:39](../../../backend/scinsight/lg/common.py#L39) | [annotated](../../04_ai_ml/langgraph/scinsight_lg_common.py) |  |
| F0639 | `api` | function | used | [backend/scinsight/lg/common.py:46](../../../backend/scinsight/lg/common.py#L46) | [annotated](../../04_ai_ml/langgraph/scinsight_lg_common.py) | Call the SCInsight API with the agent key (role agent_service: read, calculate,  |
| F0640 | `detail` | function | used | [backend/scinsight/lg/common.py:62](../../../backend/scinsight/lg/common.py#L62) | [annotated](../../04_ai_ml/langgraph/scinsight_lg_common.py) |  |
| F0641 | `strip` | function | used | [backend/scinsight/lg/common.py:67](../../../backend/scinsight/lg/common.py#L67) | [annotated](../../04_ai_ml/langgraph/scinsight_lg_common.py) |  |
| F0642 | `llm` | function | used | [backend/scinsight/lg/common.py:76](../../../backend/scinsight/lg/common.py#L76) | [annotated](../../04_ai_ml/langgraph/scinsight_lg_common.py) | Qwen through the same OpenAI-compatible endpoint Flowise uses (temperature 0). |
| F0643 | `prompt` | function | used | [backend/scinsight/lg/common.py:84](../../../backend/scinsight/lg/common.py#L84) | [annotated](../../04_ai_ml/langgraph/scinsight_lg_common.py) |  |
| F0644 | `explain_prompt` | function | used | [backend/scinsight/lg/common.py:89](../../../backend/scinsight/lg/common.py#L89) | [annotated](../../04_ai_ml/langgraph/scinsight_lg_common.py) | (system, user template) of a specialist's explanation step, exactly as exported  |
| F0645 | `fill` | function | used | [backend/scinsight/lg/common.py:96](../../../backend/scinsight/lg/common.py#L96) | [annotated](../../04_ai_ml/langgraph/scinsight_lg_common.py) | Resolve the Flowise template variables used in the shared prompts ({{ question } |
| F0646 | `text_of` | function | used | [backend/scinsight/lg/common.py:102](../../../backend/scinsight/lg/common.py#L102) | [annotated](../../04_ai_ml/langgraph/scinsight_lg_common.py) |  |
| F0647 | `_list` | function | used | [backend/scinsight/lg/common.py:110](../../../backend/scinsight/lg/common.py#L110) | [annotated](../../04_ai_ml/langgraph/scinsight_lg_common.py) |  |
| F0648 | `_kv` | function | used | [backend/scinsight/lg/common.py:114](../../../backend/scinsight/lg/common.py#L114) | [annotated](../../04_ai_ml/langgraph/scinsight_lg_common.py) |  |
| F0649 | `_fmt` | function | used | [backend/scinsight/lg/common.py:118](../../../backend/scinsight/lg/common.py#L118) | [annotated](../../04_ai_ml/langgraph/scinsight_lg_common.py) |  |
| F0650 | `_excluded` | function | used | [backend/scinsight/lg/common.py:128](../../../backend/scinsight/lg/common.py#L128) | [annotated](../../04_ai_ml/langgraph/scinsight_lg_common.py) |  |
| F0651 | `_late` | function | used | [backend/scinsight/lg/common.py:132](../../../backend/scinsight/lg/common.py#L132) | [annotated](../../04_ai_ml/langgraph/scinsight_lg_common.py) |  |
| F0652 | `_near` | function | used | [backend/scinsight/lg/common.py:136](../../../backend/scinsight/lg/common.py#L136) | [annotated](../../04_ai_ml/langgraph/scinsight_lg_common.py) |  |
| F0653 | `_opt` | function | used | [backend/scinsight/lg/common.py:140](../../../backend/scinsight/lg/common.py#L140) | [annotated](../../04_ai_ml/langgraph/scinsight_lg_common.py) |  |
| F0654 | `summarize` | function | used | [backend/scinsight/lg/common.py:151](../../../backend/scinsight/lg/common.py#L151) | [annotated](../../04_ai_ml/langgraph/scinsight_lg_common.py) |  |
| F0655 | `_po_unconfirmed` | function | used | [backend/scinsight/lg/common.py:201](../../../backend/scinsight/lg/common.py#L201) | [annotated](../../04_ai_ml/langgraph/scinsight_lg_common.py) |  |
| F0656 | `context` | function | used | [backend/scinsight/lg/common.py:206](../../../backend/scinsight/lg/common.py#L206) | [annotated](../../04_ai_ml/langgraph/scinsight_lg_common.py) |  |
| F0657 | `_catalog` | function | used | [backend/scinsight/lg/common.py:222](../../../backend/scinsight/lg/common.py#L222) | [annotated](../../04_ai_ml/langgraph/scinsight_lg_common.py) |  |
| F0658 | `_name_hits` | function | used | [backend/scinsight/lg/common.py:230](../../../backend/scinsight/lg/common.py#L230) | [annotated](../../04_ai_ml/langgraph/scinsight_lg_common.py) | How many meaningful words of a catalog name appear in the question (prefix match |
| F0659 | `detect_codes` | function | used | [backend/scinsight/lg/common.py:237](../../../backend/scinsight/lg/common.py#L237) | [annotated](../../04_ai_ml/langgraph/scinsight_lg_common.py) | Deterministic identifier detection (codes first, then catalog names). Same rules |
| F0660 | `detect_codes.first` | nested | used | [backend/scinsight/lg/common.py:244](../../../backend/scinsight/lg/common.py#L244) | [annotated](../../04_ai_ml/langgraph/scinsight_lg_common.py) |  |
| F0661 | `merge_identifiers` | function | used | [backend/scinsight/lg/common.py:278](../../../backend/scinsight/lg/common.py#L278) | [annotated](../../04_ai_ml/langgraph/scinsight_lg_common.py) | Code-detected identifiers win; the model only fills what code could not find. |
| F0662 | `parse_extracted` | function | used | [backend/scinsight/lg/common.py:283](../../../backend/scinsight/lg/common.py#L283) | [annotated](../../04_ai_ml/langgraph/scinsight_lg_common.py) | Lenient JSON parse of the identifier extraction (bare NONE / null tolerated, per |
| F0663 | `_val` | function | used | [backend/scinsight/lg/common.py:297](../../../backend/scinsight/lg/common.py#L297) | [annotated](../../04_ai_ml/langgraph/scinsight_lg_common.py) |  |
| F0664 | `_code` | function | used | [backend/scinsight/lg/common.py:303](../../../backend/scinsight/lg/common.py#L303) | [annotated](../../04_ai_ml/langgraph/scinsight_lg_common.py) |  |
| F0665 | `_num` | function | used | [backend/scinsight/lg/common.py:308](../../../backend/scinsight/lg/common.py#L308) | [annotated](../../04_ai_ml/langgraph/scinsight_lg_common.py) |  |
| F0666 | `_day` | function | used | [backend/scinsight/lg/common.py:316](../../../backend/scinsight/lg/common.py#L316) | [annotated](../../04_ai_ml/langgraph/scinsight_lg_common.py) |  |
| F0667 | `_done` | function | used | [backend/scinsight/lg/common.py:321](../../../backend/scinsight/lg/common.py#L321) | [annotated](../../04_ai_ml/langgraph/scinsight_lg_common.py) |  |
| F0668 | `_fail` | function | used | [backend/scinsight/lg/common.py:328](../../../backend/scinsight/lg/common.py#L328) | [annotated](../../04_ai_ml/langgraph/scinsight_lg_common.py) |  |
| F0669 | `calc_factory` | function | used | [backend/scinsight/lg/common.py:332](../../../backend/scinsight/lg/common.py#L332) | [annotated](../../04_ai_ml/langgraph/scinsight_lg_common.py) |  |
| F0670 | `calc_procurement` | function | used | [backend/scinsight/lg/common.py:352](../../../backend/scinsight/lg/common.py#L352) | [annotated](../../04_ai_ml/langgraph/scinsight_lg_common.py) |  |
| F0671 | `_balancing` | function | used | [backend/scinsight/lg/common.py:376](../../../backend/scinsight/lg/common.py#L376) | [annotated](../../04_ai_ml/langgraph/scinsight_lg_common.py) |  |
| F0672 | `calc_warehouse` | function | used | [backend/scinsight/lg/common.py:384](../../../backend/scinsight/lg/common.py#L384) | [annotated](../../04_ai_ml/langgraph/scinsight_lg_common.py) |  |
| F0673 | `calc_logistics` | function | used | [backend/scinsight/lg/common.py:388](../../../backend/scinsight/lg/common.py#L388) | [annotated](../../04_ai_ml/langgraph/scinsight_lg_common.py) |  |
| F0674 | `calc_inventory` | function | used | [backend/scinsight/lg/common.py:392](../../../backend/scinsight/lg/common.py#L392) | [annotated](../../04_ai_ml/langgraph/scinsight_lg_common.py) |  |
| F0675 | `calc_quality` | function | used | [backend/scinsight/lg/common.py:409](../../../backend/scinsight/lg/common.py#L409) | [annotated](../../04_ai_ml/langgraph/scinsight_lg_common.py) |  |
| F0676 | `calc_learning` | function | used | [backend/scinsight/lg/common.py:417](../../../backend/scinsight/lg/common.py#L417) | [annotated](../../04_ai_ml/langgraph/scinsight_lg_common.py) |  |
| F0677 | `calc_learning.v` | nested | used | [backend/scinsight/lg/common.py:452](../../../backend/scinsight/lg/common.py#L452) | [annotated](../../04_ai_ml/langgraph/scinsight_lg_common.py) |  |
| F0678 | `policy` | function | used | [backend/scinsight/lg/common.py:474](../../../backend/scinsight/lg/common.py#L474) | [annotated](../../04_ai_ml/langgraph/scinsight_lg_common.py) |  |
| F0679 | `numbers` | function | used | [backend/scinsight/lg/common.py:489](../../../backend/scinsight/lg/common.py#L489) | [annotated](../../04_ai_ml/langgraph/scinsight_lg_common.py) |  |
| F0680 | `unsupported_numbers` | function | used | [backend/scinsight/lg/common.py:499](../../../backend/scinsight/lg/common.py#L499) | [annotated](../../04_ai_ml/langgraph/scinsight_lg_common.py) |  |
| F0681 | `gate` | function | used | [backend/scinsight/lg/common.py:504](../../../backend/scinsight/lg/common.py#L504) | [annotated](../../04_ai_ml/langgraph/scinsight_lg_common.py) |  |
| F0682 | `guard` | function | used | [backend/scinsight/lg/common.py:521](../../../backend/scinsight/lg/common.py#L521) | [annotated](../../04_ai_ml/langgraph/scinsight_lg_common.py) |  |
| F0683 | `save` | function | used | [backend/scinsight/lg/common.py:534](../../../backend/scinsight/lg/common.py#L534) | [annotated](../../04_ai_ml/langgraph/scinsight_lg_common.py) |  |
| F0684 | `verify` | function | used | [backend/scinsight/lg/common.py:552](../../../backend/scinsight/lg/common.py#L552) | [annotated](../../04_ai_ml/langgraph/scinsight_lg_common.py) |  |
| F0685 | `withdraw` | function | used | [backend/scinsight/lg/common.py:567](../../../backend/scinsight/lg/common.py#L567) | [annotated](../../04_ai_ml/langgraph/scinsight_lg_common.py) |  |
| F0686 | `Input` | class | used | [backend/scinsight/lg/specialists.py:38](../../../backend/scinsight/lg/specialists.py#L38) | [annotated](../../04_ai_ml/langgraph/scinsight_lg_specialists.py) |  |
| F0687 | `Output` | class | used | [backend/scinsight/lg/specialists.py:42](../../../backend/scinsight/lg/specialists.py#L42) | [annotated](../../04_ai_ml/langgraph/scinsight_lg_specialists.py) |  |
| F0688 | `SpecialistState` | class | used | [backend/scinsight/lg/specialists.py:48](../../../backend/scinsight/lg/specialists.py#L48) | [annotated](../../04_ai_ml/langgraph/scinsight_lg_specialists.py) |  |
| F0689 | `last_question` | function | used | [backend/scinsight/lg/specialists.py:66](../../../backend/scinsight/lg/specialists.py#L66) | [annotated](../../04_ai_ml/langgraph/scinsight_lg_specialists.py) |  |
| F0690 | `build_specialist` | function | used | [backend/scinsight/lg/specialists.py:70](../../../backend/scinsight/lg/specialists.py#L70) | [annotated](../../04_ai_ml/langgraph/scinsight_lg_specialists.py) |  |
| F0691 | `build_specialist.check_access` | nested | used | [backend/scinsight/lg/specialists.py:73](../../../backend/scinsight/lg/specialists.py#L73) | [annotated](../../04_ai_ml/langgraph/scinsight_lg_specialists.py) |  |
| F0692 | `build_specialist.stop_access` | nested | used | [backend/scinsight/lg/specialists.py:77](../../../backend/scinsight/lg/specialists.py#L77) | [annotated](../../04_ai_ml/langgraph/scinsight_lg_specialists.py) |  |
| F0693 | `build_specialist.read_request` | nested | used | [backend/scinsight/lg/specialists.py:80](../../../backend/scinsight/lg/specialists.py#L80) | [annotated](../../04_ai_ml/langgraph/scinsight_lg_specialists.py) |  |
| F0694 | `build_specialist.calculate` | nested | used | [backend/scinsight/lg/specialists.py:85](../../../backend/scinsight/lg/specialists.py#L85) | [annotated](../../04_ai_ml/langgraph/scinsight_lg_specialists.py) |  |
| F0695 | `build_specialist.stop_input` | nested | used | [backend/scinsight/lg/specialists.py:89](../../../backend/scinsight/lg/specialists.py#L89) | [annotated](../../04_ai_ml/langgraph/scinsight_lg_specialists.py) |  |
| F0696 | `build_specialist.policy_search` | nested | used | [backend/scinsight/lg/specialists.py:92](../../../backend/scinsight/lg/specialists.py#L92) | [annotated](../../04_ai_ml/langgraph/scinsight_lg_specialists.py) |  |
| F0697 | `build_specialist.write_answer` | nested | used | [backend/scinsight/lg/specialists.py:95](../../../backend/scinsight/lg/specialists.py#L95) | [annotated](../../04_ai_ml/langgraph/scinsight_lg_specialists.py) |  |
| F0698 | `build_specialist.check_numbers` | nested | used | [backend/scinsight/lg/specialists.py:101](../../../backend/scinsight/lg/specialists.py#L101) | [annotated](../../04_ai_ml/langgraph/scinsight_lg_specialists.py) |  |
| F0699 | `Input` | class | used | [backend/scinsight/lg/supervisor.py:27](../../../backend/scinsight/lg/supervisor.py#L27) | [annotated](../../04_ai_ml/langgraph/scinsight_lg_supervisor.py) |  |
| F0700 | `Output` | class | used | [backend/scinsight/lg/supervisor.py:32](../../../backend/scinsight/lg/supervisor.py#L32) | [annotated](../../04_ai_ml/langgraph/scinsight_lg_supervisor.py) |  |
| F0701 | `SupervisorState` | class | used | [backend/scinsight/lg/supervisor.py:39](../../../backend/scinsight/lg/supervisor.py#L39) | [annotated](../../04_ai_ml/langgraph/scinsight_lg_supervisor.py) |  |
| F0702 | `_reply` | function | used | [backend/scinsight/lg/supervisor.py:56](../../../backend/scinsight/lg/supervisor.py#L56) | [annotated](../../04_ai_ml/langgraph/scinsight_lg_supervisor.py) |  |
| F0703 | `check_access` | function | used | [backend/scinsight/lg/supervisor.py:60](../../../backend/scinsight/lg/supervisor.py#L60) | [annotated](../../04_ai_ml/langgraph/scinsight_lg_supervisor.py) |  |
| F0704 | `stop_access` | function | used | [backend/scinsight/lg/supervisor.py:68](../../../backend/scinsight/lg/supervisor.py#L68) | [annotated](../../04_ai_ml/langgraph/scinsight_lg_supervisor.py) |  |
| F0705 | `understand` | function | used | [backend/scinsight/lg/supervisor.py:72](../../../backend/scinsight/lg/supervisor.py#L72) | [annotated](../../04_ai_ml/langgraph/scinsight_lg_supervisor.py) |  |
| F0706 | `safety_guard` | function | used | [backend/scinsight/lg/supervisor.py:77](../../../backend/scinsight/lg/supervisor.py#L77) | [annotated](../../04_ai_ml/langgraph/scinsight_lg_supervisor.py) |  |
| F0707 | `route` | function | used | [backend/scinsight/lg/supervisor.py:82](../../../backend/scinsight/lg/supervisor.py#L82) | [annotated](../../04_ai_ml/langgraph/scinsight_lg_supervisor.py) |  |
| F0708 | `specialist_node` | function | used | [backend/scinsight/lg/supervisor.py:89](../../../backend/scinsight/lg/supervisor.py#L89) | [annotated](../../04_ai_ml/langgraph/scinsight_lg_supervisor.py) |  |
| F0709 | `specialist_node.run` | nested | used | [backend/scinsight/lg/supervisor.py:90](../../../backend/scinsight/lg/supervisor.py#L90) | [annotated](../../04_ai_ml/langgraph/scinsight_lg_supervisor.py) |  |
| F0710 | `refuse_sap_change` | function | used | [backend/scinsight/lg/supervisor.py:97](../../../backend/scinsight/lg/supervisor.py#L97) | [annotated](../../04_ai_ml/langgraph/scinsight_lg_supervisor.py) |  |
| F0711 | `out_of_scope` | function | used | [backend/scinsight/lg/supervisor.py:101](../../../backend/scinsight/lg/supervisor.py#L101) | [annotated](../../04_ai_ml/langgraph/scinsight_lg_supervisor.py) |  |
| F0712 | `learning_report` | function | used | [backend/scinsight/lg/supervisor.py:105](../../../backend/scinsight/lg/supervisor.py#L105) | [annotated](../../04_ai_ml/langgraph/scinsight_lg_supervisor.py) |  |
| F0713 | `save_recommendation` | function | used | [backend/scinsight/lg/supervisor.py:109](../../../backend/scinsight/lg/supervisor.py#L109) | [annotated](../../04_ai_ml/langgraph/scinsight_lg_supervisor.py) |  |
| F0714 | `after_save` | function | used | [backend/scinsight/lg/supervisor.py:113](../../../backend/scinsight/lg/supervisor.py#L113) | [annotated](../../04_ai_ml/langgraph/scinsight_lg_supervisor.py) |  |
| F0715 | `analysis_only` | function | used | [backend/scinsight/lg/supervisor.py:119](../../../backend/scinsight/lg/supervisor.py#L119) | [annotated](../../04_ai_ml/langgraph/scinsight_lg_supervisor.py) |  |
| F0716 | `_approval_text` | function | used | [backend/scinsight/lg/supervisor.py:123](../../../backend/scinsight/lg/supervisor.py#L123) | [annotated](../../04_ai_ml/langgraph/scinsight_lg_supervisor.py) |  |
| F0717 | `handoff` | function | used | [backend/scinsight/lg/supervisor.py:128](../../../backend/scinsight/lg/supervisor.py#L128) | [annotated](../../04_ai_ml/langgraph/scinsight_lg_supervisor.py) |  |
| F0718 | `prepare_approval` | function | used | [backend/scinsight/lg/supervisor.py:132](../../../backend/scinsight/lg/supervisor.py#L132) | [annotated](../../04_ai_ml/langgraph/scinsight_lg_supervisor.py) |  |
| F0719 | `human_approval` | function | used | [backend/scinsight/lg/supervisor.py:136](../../../backend/scinsight/lg/supervisor.py#L136) | [annotated](../../04_ai_ml/langgraph/scinsight_lg_supervisor.py) |  |
| F0720 | `show_decision` | function | used | [backend/scinsight/lg/supervisor.py:143](../../../backend/scinsight/lg/supervisor.py#L143) | [annotated](../../04_ai_ml/langgraph/scinsight_lg_supervisor.py) |  |
| F0721 | `withdraw` | function | used | [backend/scinsight/lg/supervisor.py:147](../../../backend/scinsight/lg/supervisor.py#L147) | [annotated](../../04_ai_ml/langgraph/scinsight_lg_supervisor.py) |  |
| F0722 | `build_supervisor` | function | used | [backend/scinsight/lg/supervisor.py:151](../../../backend/scinsight/lg/supervisor.py#L151) | [annotated](../../04_ai_ml/langgraph/scinsight_lg_supervisor.py) |  |
| F0723 | `_dump` | function | used | [scripts/langgraph_assistants.py:45](../../../scripts/langgraph_assistants.py#L45) | — |  |
| F0724 | `write_files` | function | used | [scripts/langgraph_assistants.py:54](../../../scripts/langgraph_assistants.py#L54) | — |  |
| F0725 | `_call` | function | used | [scripts/langgraph_assistants.py:79](../../../scripts/langgraph_assistants.py#L79) | — |  |
| F0726 | `create_assistants` | function | used | [scripts/langgraph_assistants.py:86](../../../scripts/langgraph_assistants.py#L86) | — |  |
| F0727 | `main` | function | used | [scripts/langgraph_assistants.py:104](../../../scripts/langgraph_assistants.py#L104) | — |  |
