# 06_testing/api_tests (generated)

Modules: `tests/scinsight/test_api_scenarios.py`, `tests/scinsight/test_security.py`, `tests/test_api.py`, `tests/test_poc_contract.py`

| ID | Function / class | Kind | Status | Original | Annotated copy | Summary |
|---|---|---|---|---|---|---|
| F0834 | `test_scenario_1_factory_material_shortage` | test | test | [tests/scinsight/test_api_scenarios.py:7](../../../tests/scinsight/test_api_scenarios.py#L7) | — |  |
| F0835 | `test_production_order_quantity_cannot_be_overridden` | test | test | [tests/scinsight/test_api_scenarios.py:28](../../../tests/scinsight/test_api_scenarios.py#L28) | — |  |
| F0836 | `test_scenario_2_three_warehouse_balancing` | test | test | [tests/scinsight/test_api_scenarios.py:34](../../../tests/scinsight/test_api_scenarios.py#L34) | — |  |
| F0837 | `test_scenario_3_expiry_and_quality_protection` | test | test | [tests/scinsight/test_api_scenarios.py:48](../../../tests/scinsight/test_api_scenarios.py#L48) | — |  |
| F0838 | `test_decision_lifecycle_requires_an_authorised_human` | test | test | [tests/scinsight/test_api_scenarios.py:58](../../../tests/scinsight/test_api_scenarios.py#L58) | — |  |
| F0839 | `test_defer_then_review_and_withdraw` | test | test | [tests/scinsight/test_api_scenarios.py:82](../../../tests/scinsight/test_api_scenarios.py#L82) | — |  |
| F0840 | `test_outcome_learning_loop_and_model_governance` | test | test | [tests/scinsight/test_api_scenarios.py:95](../../../tests/scinsight/test_api_scenarios.py#L95) | — |  |
| F0841 | `test_purchase_request_carries_a_reconcilable_lead_time_prediction` | test | test | [tests/scinsight/test_api_scenarios.py:114](../../../tests/scinsight/test_api_scenarios.py#L114) | — |  |
| F0842 | `test_reconcile_requires_executed_recommendation` | test | test | [tests/scinsight/test_api_scenarios.py:135](../../../tests/scinsight/test_api_scenarios.py#L135) | — |  |
| F0843 | `test_demand_forecast_has_backtest_and_feeds_metrics` | test | test | [tests/scinsight/test_api_scenarios.py:141](../../../tests/scinsight/test_api_scenarios.py#L141) | — |  |
| F0844 | `test_rag_is_tenant_scoped_cited_and_flags_injection` | test | test | [tests/scinsight/test_api_scenarios.py:147](../../../tests/scinsight/test_api_scenarios.py#L147) | — |  |
| F0845 | `test_unauthenticated_and_invalid_keys` | test | test | [tests/scinsight/test_security.py:12](../../../tests/scinsight/test_security.py#L12) | — |  |
| F0846 | `test_configured_keys_rotate_out_stored_dev_keys` | test | test | [tests/scinsight/test_security.py:18](../../../tests/scinsight/test_security.py#L18) | — |  |
| F0847 | `test_postgres_deployment_refuses_to_start_without_all_keys` | test | test | [tests/scinsight/test_security.py:26](../../../tests/scinsight/test_security.py#L26) | — |  |
| F0848 | `test_forged_tenant_is_rejected_and_audited` | test | test | [tests/scinsight/test_security.py:31](../../../tests/scinsight/test_security.py#L31) | — |  |
| F0849 | `test_cross_tenant_data_is_invisible` | test | test | [tests/scinsight/test_security.py:37](../../../tests/scinsight/test_security.py#L37) | — |  |
| F0850 | `test_sap_writes_are_blocked` | test | test | [tests/scinsight/test_security.py:44](../../../tests/scinsight/test_security.py#L44) | — |  |
| F0851 | `test_sap_write_enabled_refuses_to_start` | test | test | [tests/scinsight/test_security.py:50](../../../tests/scinsight/test_security.py#L50) | — |  |
| F0852 | `test_expired_snapshot_blocks_calculations` | test | test | [tests/scinsight/test_security.py:55](../../../tests/scinsight/test_security.py#L55) | — |  |
| F0853 | `test_missing_snapshot_blocks_calculations` | test | test | [tests/scinsight/test_security.py:62](../../../tests/scinsight/test_security.py#L62) | — |  |
| F0854 | `test_invalid_bom_and_unit_mismatch_are_explained` | test | test | [tests/scinsight/test_security.py:67](../../../tests/scinsight/test_security.py#L67) | — |  |
| F0855 | `test_malformed_and_injected_tool_arguments` | test | test | [tests/scinsight/test_security.py:74](../../../tests/scinsight/test_security.py#L74) | — |  |
| F0856 | `test_unknown_calculation_and_no_action_calculation` | test | test | [tests/scinsight/test_security.py:84](../../../tests/scinsight/test_security.py#L84) | — |  |
| F0857 | `test_roles_are_enforced_server_side` | test | test | [tests/scinsight/test_security.py:90](../../../tests/scinsight/test_security.py#L90) | — |  |
| F0858 | `test_incomplete_outcome_is_not_used_for_training` | test | test | [tests/scinsight/test_security.py:99](../../../tests/scinsight/test_security.py#L99) | — |  |
| F0859 | `test_pending_outcome_is_reported_not_invented` | test | test | [tests/scinsight/test_security.py:106](../../../tests/scinsight/test_security.py#L106) | — |  |
| F0860 | `test_concurrent_reviews_cannot_both_win` | test | test | [tests/scinsight/test_security.py:112](../../../tests/scinsight/test_security.py#L112) | — |  |
| F0861 | `test_health_is_public_but_data_requires_key` | test | test | [tests/test_api.py:6](../../../tests/test_api.py#L6) | — |  |
| F0862 | `test_sap_odata_reads_and_blocks_writes` | test | test | [tests/test_api.py:12](../../../tests/test_api.py#L12) | — |  |
| F0863 | `test_analysis_validation_errors` | test | test | [tests/test_api.py:24](../../../tests/test_api.py#L24) | — |  |
| F0864 | `test_all_analysis_endpoints` | test | test | [tests/test_api.py:31](../../../tests/test_api.py#L31) | — |  |
| F0865 | `test_recommendation_lifecycle_and_roles` | test | test | [tests/test_api.py:50](../../../tests/test_api.py#L50) | — |  |
| F0866 | `test_agent_handoff_selects_analysis_server_side` | test | test | [tests/test_api.py:72](../../../tests/test_api.py#L72) | — |  |
| F0867 | `test_recommendation_requires_actions` | test | test | [tests/test_api.py:88](../../../tests/test_api.py#L88) | — |  |
| F0868 | `test_rag_search_and_manager_only_ingest` | test | test | [tests/test_api.py:98](../../../tests/test_api.py#L98) | — |  |
| F0869 | `test_chat_and_business_workflow_through_api` | test | test | [tests/test_api.py:106](../../../tests/test_api.py#L106) | — |  |
| F0870 | `test_langgraph_agentflow_through_api` | test | test | [tests/test_api.py:121](../../../tests/test_api.py#L121) | — |  |
| F0871 | `test_status_and_public_config` | test | test | [tests/test_api.py:129](../../../tests/test_api.py#L129) | — |  |
| F0872 | `test_demo_session_disabled_by_default_and_enabled_for_local_demo` | test | test | [tests/test_api.py:136](../../../tests/test_api.py#L136) | — |  |
| F0873 | `test_metrics_exposed` | test | test | [tests/test_api.py:147](../../../tests/test_api.py#L147) | — |  |
| F0874 | `test_deep_agent_harness_settings_are_governed` | test | test | [tests/test_api.py:153](../../../tests/test_api.py#L153) | — |  |
| F0875 | `test_sap_read_endpoints_are_read_only` | test | test | [tests/test_poc_contract.py:9](../../../tests/test_poc_contract.py#L9) | — |  |
| F0876 | `test_forecasts_and_optimizers` | test | test | [tests/test_poc_contract.py:18](../../../tests/test_poc_contract.py#L18) | — |  |
| F0877 | `test_decision_lifecycle_human_review_and_reconciliation` | test | test | [tests/test_poc_contract.py:31](../../../tests/test_poc_contract.py#L31) | — |  |
| F0878 | `test_tenant_scoped_authorization` | test | test | [tests/test_poc_contract.py:51](../../../tests/test_poc_contract.py#L51) | — |  |
| F0879 | `test_contract_is_documented_in_openapi` | test | test | [tests/test_poc_contract.py:65](../../../tests/test_poc_contract.py#L65) | — |  |
