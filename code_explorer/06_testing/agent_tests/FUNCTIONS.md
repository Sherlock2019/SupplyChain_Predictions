# 06_testing/agent_tests (generated)

Modules: `tests/scinsight/test_flowise_e2e.py`, `tests/scinsight/test_langgraph_mirror.py`, `tests/test_flowise_flows.py`, `tests/test_graphs_and_agents.py`

| ID | Function / class | Kind | Status | Original | Annotated copy | Summary |
|---|---|---|---|---|---|---|
| F0786 | `_target` | function | used | [tests/scinsight/test_flowise_e2e.py:26](../../../tests/scinsight/test_flowise_e2e.py#L26) | — |  |
| F0787 | `_http` | function | used | [tests/scinsight/test_flowise_e2e.py:42](../../../tests/scinsight/test_flowise_e2e.py#L42) | — |  |
| F0788 | `predict` | function | used | [tests/scinsight/test_flowise_e2e.py:56](../../../tests/scinsight/test_flowise_e2e.py#L56) | — |  |
| F0789 | `sci` | function | used | [tests/scinsight/test_flowise_e2e.py:61](../../../tests/scinsight/test_flowise_e2e.py#L61) | — |  |
| F0790 | `calculation_of` | function | used | [tests/scinsight/test_flowise_e2e.py:65](../../../tests/scinsight/test_flowise_e2e.py#L65) | — |  |
| F0791 | `ask_supervisor` | function | used | [tests/scinsight/test_flowise_e2e.py:73](../../../tests/scinsight/test_flowise_e2e.py#L73) | — |  |
| F0792 | `paused_recommendation` | function | used | [tests/scinsight/test_flowise_e2e.py:79](../../../tests/scinsight/test_flowise_e2e.py#L79) | — |  |
| F0793 | `resume` | function | used | [tests/scinsight/test_flowise_e2e.py:87](../../../tests/scinsight/test_flowise_e2e.py#L87) | — |  |
| F0794 | `test_prediction_without_api_key_is_refused` | test | test | [tests/scinsight/test_flowise_e2e.py:94](../../../tests/scinsight/test_flowise_e2e.py#L94) | — |  |
| F0795 | `test_sap_write_request_is_refused_without_calling_a_specialist` | test | test | [tests/scinsight/test_flowise_e2e.py:99](../../../tests/scinsight/test_flowise_e2e.py#L99) | — |  |
| F0796 | `test_instruction_override_is_blocked` | test | test | [tests/scinsight/test_flowise_e2e.py:105](../../../tests/scinsight/test_flowise_e2e.py#L105) | — |  |
| F0797 | `test_scenario_1_factory_shortage_pauses_and_proceed_is_not_an_approval` | test | test | [tests/scinsight/test_flowise_e2e.py:111](../../../tests/scinsight/test_flowise_e2e.py#L111) | — |  |
| F0798 | `test_scenario_2_transfer_is_approved_only_by_the_warehouse_manager` | test | test | [tests/scinsight/test_flowise_e2e.py:123](../../../tests/scinsight/test_flowise_e2e.py#L123) | — |  |
| F0799 | `test_scenario_3_quality_exclusions_and_reject_withdraws` | test | test | [tests/scinsight/test_flowise_e2e.py:137](../../../tests/scinsight/test_flowise_e2e.py#L137) | — |  |
| F0800 | `test_procurement_recommends_an_approved_supplier_with_demonstrated_lead_time` | test | test | [tests/scinsight/test_flowise_e2e.py:147](../../../tests/scinsight/test_flowise_e2e.py#L147) | — |  |
| F0801 | `test_learning_reports_the_verified_plus_four_day_error` | test | test | [tests/scinsight/test_flowise_e2e.py:157](../../../tests/scinsight/test_flowise_e2e.py#L157) | — |  |
| F0802 | `test_chatflow_answers_with_allowlisted_tools_and_the_evidence_footer` | test | test | [tests/scinsight/test_flowise_e2e.py:166](../../../tests/scinsight/test_flowise_e2e.py#L166) | — |  |
| F0803 | `ScriptedModel` | class | used | [tests/scinsight/test_langgraph_mirror.py:31](../../../tests/scinsight/test_langgraph_mirror.py#L31) | — | Stands in for Qwen: answers each prompt type deterministically (classification,  |
| F0804 | `ScriptedModel.__init__` | method | used | [tests/scinsight/test_langgraph_mirror.py:34](../../../tests/scinsight/test_langgraph_mirror.py#L34) | — |  |
| F0805 | `ScriptedModel.bind_tools` | method | used | [tests/scinsight/test_langgraph_mirror.py:38](../../../tests/scinsight/test_langgraph_mirror.py#L38) | — |  |
| F0806 | `ScriptedModel.invoke` | method | used | [tests/scinsight/test_langgraph_mirror.py:42](../../../tests/scinsight/test_langgraph_mirror.py#L42) | — |  |
| F0807 | `lg` | function | used | [tests/scinsight/test_langgraph_mirror.py:57](../../../tests/scinsight/test_langgraph_mirror.py#L57) | — |  |
| F0808 | `calc_of` | function | used | [tests/scinsight/test_langgraph_mirror.py:65](../../../tests/scinsight/test_langgraph_mirror.py#L65) | — |  |
| F0809 | `test_specialist_subgraph_mirrors_the_flowise_specialist` | test | test | [tests/scinsight/test_langgraph_mirror.py:71](../../../tests/scinsight/test_langgraph_mirror.py#L71) | — |  |
| F0810 | `test_supervisor_interrupt_is_not_the_approval_and_resume_reads_the_api` | test | test | [tests/scinsight/test_langgraph_mirror.py:82](../../../tests/scinsight/test_langgraph_mirror.py#L82) | — |  |
| F0811 | `test_supervisor_reject_withdraws_and_guards_refuse` | test | test | [tests/scinsight/test_langgraph_mirror.py:105](../../../tests/scinsight/test_langgraph_mirror.py#L105) | — |  |
| F0812 | `test_chat_front_door_calls_the_manager_and_checks_numbers` | test | test | [tests/scinsight/test_langgraph_mirror.py:123](../../../tests/scinsight/test_langgraph_mirror.py#L123) | — |  |
| F0813 | `test_role_questions_cover_every_role_with_valid_routes` | test | test | [tests/scinsight/test_langgraph_mirror.py:141](../../../tests/scinsight/test_langgraph_mirror.py#L141) | — |  |
| F0814 | `test_identifiers_are_detected_by_code_before_the_model` | test | test | [tests/scinsight/test_langgraph_mirror.py:148](../../../tests/scinsight/test_langgraph_mirror.py#L148) | — |  |
| F0815 | `load` | function | used | [tests/test_flowise_flows.py:13](../../../tests/test_flowise_flows.py#L13) | — |  |
| F0816 | `test_edges_reference_real_nodes_and_handles` | test | test | [tests/test_flowise_flows.py:20](../../../tests/test_flowise_flows.py#L20) | — |  |
| F0817 | `test_edges_reference_real_nodes_and_handles.handles` | nested | used | [tests/test_flowise_flows.py:25](../../../tests/test_flowise_flows.py#L25) | — |  |
| F0818 | `test_chatflow_is_tool_agent_with_mcp_sap_odata_and_memory` | test | test | [tests/test_flowise_flows.py:36](../../../tests/test_flowise_flows.py#L36) | — |  |
| F0819 | `test_agentflow_full_workflow_sap_rag_nine_roles_and_human_input` | test | test | [tests/test_flowise_flows.py:53](../../../tests/test_flowise_flows.py#L53) | — |  |
| F0820 | `test_no_secrets_in_flow_json` | test | test | [tests/test_flowise_flows.py:83](../../../tests/test_flowise_flows.py#L83) | — |  |
| F0821 | `runner` | function | used | [tests/test_graphs_and_agents.py:10](../../../tests/test_graphs_and_agents.py#L10) | — |  |
| F0822 | `test_graphs_have_expected_topology` | test | test | [tests/test_graphs_and_agents.py:15](../../../tests/test_graphs_and_agents.py#L15) | — |  |
| F0823 | `test_chat_graph_guard_refuses_sap_writes` | test | test | [tests/test_graphs_and_agents.py:22](../../../tests/test_graphs_and_agents.py#L22) | — |  |
| F0824 | `test_chat_graph_deterministic_fallback_keeps_thread_memory` | test | test | [tests/test_graphs_and_agents.py:27](../../../tests/test_graphs_and_agents.py#L27) | — |  |
| F0825 | `test_business_graph_interrupts_then_submits` | test | test | [tests/test_graphs_and_agents.py:35](../../../tests/test_graphs_and_agents.py#L35) | — |  |
| F0826 | `test_business_graph_discard_and_free_text_intake` | test | test | [tests/test_graphs_and_agents.py:50](../../../tests/test_graphs_and_agents.py#L50) | — |  |
| F0827 | `test_business_graph_rejects_invalid_and_completes_no_action` | test | test | [tests/test_graphs_and_agents.py:58](../../../tests/test_graphs_and_agents.py#L58) | — |  |
| F0828 | `test_langgraph_agentflow_topology` | test | test | [tests/test_graphs_and_agents.py:65](../../../tests/test_graphs_and_agents.py#L65) | — |  |
| F0829 | `test_langgraph_agentflow_routes_interrupts_and_submits` | test | test | [tests/test_graphs_and_agents.py:74](../../../tests/test_graphs_and_agents.py#L74) | — |  |
| F0830 | `test_langgraph_agentflow_boundary_and_discard` | test | test | [tests/test_graphs_and_agents.py:92](../../../tests/test_graphs_and_agents.py#L92) | — |  |
| F0831 | `test_deep_agent_is_built_with_subagents_and_planning_tools` | test | test | [tests/test_graphs_and_agents.py:101](../../../tests/test_graphs_and_agents.py#L101) | — |  |
| F0832 | `test_deep_agent_harness_controls_tools_subagents_steps_and_prompt` | test | test | [tests/test_graphs_and_agents.py:110](../../../tests/test_graphs_and_agents.py#L110) | — |  |
| F0833 | `test_harness_guard_enforces_loop_controls_per_run` | test | test | [tests/test_graphs_and_agents.py:130](../../../tests/test_graphs_and_agents.py#L130) | — |  |
