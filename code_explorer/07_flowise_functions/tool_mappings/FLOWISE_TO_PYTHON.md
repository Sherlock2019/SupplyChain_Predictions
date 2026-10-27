# Flowise → FastAPI → Python (generated)

Every Flowise Custom Tool and Agentflow Custom Function, the SCInsight endpoints it calls (parsed from its JavaScript), and therefore the Python handler that runs.

| Flowise node | Source | FastAPI handler(s) |
|---|---|---|
| Flowise Custom Tool · calculate_stock_cover | flowise/tools/calculate_stock_cover.json | F0128 create_app.replenishment() |
| Flowise Custom Tool · check_batch_quality | flowise/tools/check_batch_quality.json | F0131 create_app.quality_check() |
| Flowise Custom Tool · check_material_readiness | flowise/tools/check_material_readiness.json | F0126 create_app.material_readiness() |
| Flowise Custom Tool · forecast_demand | flowise/tools/forecast_demand.json | F0129 create_app.forecast_demand() |
| Flowise Custom Tool · get_decision_status | flowise/tools/get_decision_status.json | F0137 create_app.get_decision() |
| Flowise Custom Tool · get_material_bom | flowise/tools/get_material_bom.json | F0120 create_app.sap_bom() |
| Flowise Custom Tool · get_open_purchase_orders | flowise/tools/get_open_purchase_orders.json | F0122 create_app.sap_purchase_orders() |
| Flowise Custom Tool · get_production_orders | flowise/tools/get_production_orders.json | F0121 create_app.sap_production_orders() |
| Flowise Custom Tool · get_sap_inventory | flowise/tools/get_sap_inventory.json | F0119 create_app.sap_inventory() |
| Flowise Custom Tool · get_supplier_reliability | flowise/tools/get_supplier_reliability.json | F0130 create_app.forecast_lead_time() |
| Flowise Custom Tool · get_verified_outcomes | flowise/tools/get_verified_outcomes.json | F0142 create_app.learning_metrics() |
| Flowise Custom Tool · optimize_warehouse_transfer | flowise/tools/optimize_warehouse_transfer.json | F0127 create_app.warehouse_balancing() |
| Flowise Custom Tool · save_recommendation | flowise/tools/save_recommendation.json | F0135 create_app.create_decision() |
| Flowise Custom Tool · search_supply_chain_policy | flowise/tools/search_supply_chain_policy.json | F0076 create_app.rag_search(), F0133 create_app.rag_search() |
| Decision-Outcome-Learning-Agentflow · 2 · Check access | flowise/agentflows/SCInsight-Cosmetics-Decision-Outcome-Learning-Agentflow-v1.json node customFunctionAgentflow_0 | F0118 create_app.validate_context() |
| Decision-Outcome-Learning-Agentflow · 3 · Check the outcome with SAP data | flowise/agentflows/SCInsight-Cosmetics-Decision-Outcome-Learning-Agentflow-v1.json node customFunctionAgentflow_1 | F0141 create_app.reconcile(), F0142 create_app.learning_metrics() |
| Decision-Outcome-Learning-Agentflow · 4 · Final report | flowise/agentflows/SCInsight-Cosmetics-Decision-Outcome-Learning-Agentflow-v1.json node customFunctionAgentflow_2 | (no API call) |
| Factory-Planning-Agentflow · 2 · Check access | flowise/agentflows/SCInsight-Cosmetics-Factory-Planning-Agentflow-v1.json node customFunctionAgentflow_0 | F0118 create_app.validate_context() |
| Factory-Planning-Agentflow · 4 · Calculate with SAP data | flowise/agentflows/SCInsight-Cosmetics-Factory-Planning-Agentflow-v1.json node customFunctionAgentflow_1 | F0121 create_app.sap_production_orders(), F0126 create_app.material_readiness() |
| Factory-Planning-Agentflow · 5 · Policy search (RAG) | flowise/agentflows/SCInsight-Cosmetics-Factory-Planning-Agentflow-v1.json node customFunctionAgentflow_2 | F0076 create_app.rag_search(), F0133 create_app.rag_search() |
| Factory-Planning-Agentflow · 8 · Check every number | flowise/agentflows/SCInsight-Cosmetics-Factory-Planning-Agentflow-v1.json node customFunctionAgentflow_3 | (no API call) |
| Inventory-Optimizer-Agentflow · 2 · Check access | flowise/agentflows/SCInsight-Cosmetics-Inventory-Optimizer-Agentflow-v1.json node customFunctionAgentflow_0 | F0118 create_app.validate_context() |
| Inventory-Optimizer-Agentflow · 4 · Calculate with SAP data | flowise/agentflows/SCInsight-Cosmetics-Inventory-Optimizer-Agentflow-v1.json node customFunctionAgentflow_1 | F0128 create_app.replenishment(), F0129 create_app.forecast_demand() |
| Inventory-Optimizer-Agentflow · 5 · Policy search (RAG) | flowise/agentflows/SCInsight-Cosmetics-Inventory-Optimizer-Agentflow-v1.json node customFunctionAgentflow_2 | F0076 create_app.rag_search(), F0133 create_app.rag_search() |
| Inventory-Optimizer-Agentflow · 8 · Check every number | flowise/agentflows/SCInsight-Cosmetics-Inventory-Optimizer-Agentflow-v1.json node customFunctionAgentflow_3 | (no API call) |
| Logistics-Agentflow · 2 · Check access | flowise/agentflows/SCInsight-Cosmetics-Logistics-Agentflow-v1.json node customFunctionAgentflow_0 | F0118 create_app.validate_context() |
| Logistics-Agentflow · 4 · Calculate with SAP data | flowise/agentflows/SCInsight-Cosmetics-Logistics-Agentflow-v1.json node customFunctionAgentflow_1 | F0127 create_app.warehouse_balancing() |
| Logistics-Agentflow · 5 · Policy search (RAG) | flowise/agentflows/SCInsight-Cosmetics-Logistics-Agentflow-v1.json node customFunctionAgentflow_2 | F0076 create_app.rag_search(), F0133 create_app.rag_search() |
| Logistics-Agentflow · 8 · Check every number | flowise/agentflows/SCInsight-Cosmetics-Logistics-Agentflow-v1.json node customFunctionAgentflow_3 | (no API call) |
| Procurement-Agentflow · 2 · Check access | flowise/agentflows/SCInsight-Cosmetics-Procurement-Agentflow-v1.json node customFunctionAgentflow_0 | F0118 create_app.validate_context() |
| Procurement-Agentflow · 4 · Calculate with SAP data | flowise/agentflows/SCInsight-Cosmetics-Procurement-Agentflow-v1.json node customFunctionAgentflow_1 | F0124 create_app.sap_suppliers(), F0128 create_app.replenishment(), F0130 create_app.forecast_lead_time() |
| Procurement-Agentflow · 5 · Policy search (RAG) | flowise/agentflows/SCInsight-Cosmetics-Procurement-Agentflow-v1.json node customFunctionAgentflow_2 | F0076 create_app.rag_search(), F0133 create_app.rag_search() |
| Procurement-Agentflow · 8 · Check every number | flowise/agentflows/SCInsight-Cosmetics-Procurement-Agentflow-v1.json node customFunctionAgentflow_3 | (no API call) |
| Quality-Agentflow · 2 · Check access | flowise/agentflows/SCInsight-Cosmetics-Quality-Agentflow-v1.json node customFunctionAgentflow_0 | F0118 create_app.validate_context() |
| Quality-Agentflow · 4 · Calculate with SAP data | flowise/agentflows/SCInsight-Cosmetics-Quality-Agentflow-v1.json node customFunctionAgentflow_1 | F0131 create_app.quality_check() |
| Quality-Agentflow · 5 · Policy search (RAG) | flowise/agentflows/SCInsight-Cosmetics-Quality-Agentflow-v1.json node customFunctionAgentflow_2 | F0076 create_app.rag_search(), F0133 create_app.rag_search() |
| Quality-Agentflow · 8 · Check every number | flowise/agentflows/SCInsight-Cosmetics-Quality-Agentflow-v1.json node customFunctionAgentflow_3 | (no API call) |
| Supervisor-Agentflow · 2 · Check access | flowise/agentflows/SCInsight-Cosmetics-Supervisor-Agentflow-v1.json node customFunctionAgentflow_0 | F0118 create_app.validate_context() |
| Supervisor-Agentflow · 4 · Safety guard | flowise/agentflows/SCInsight-Cosmetics-Supervisor-Agentflow-v1.json node customFunctionAgentflow_1 | (no API call) |
| Supervisor-Agentflow · 7 · Save recommendation | flowise/agentflows/SCInsight-Cosmetics-Supervisor-Agentflow-v1.json node customFunctionAgentflow_2 | F0135 create_app.create_decision() |
| Supervisor-Agentflow · 10 · Show the verified decision | flowise/agentflows/SCInsight-Cosmetics-Supervisor-Agentflow-v1.json node customFunctionAgentflow_3 | (no API call) |
| Supervisor-Agentflow · 10 · Withdraw | flowise/agentflows/SCInsight-Cosmetics-Supervisor-Agentflow-v1.json node customFunctionAgentflow_4 | F0139 create_app.withdraw() |
| Warehouse-Agentflow · 2 · Check access | flowise/agentflows/SCInsight-Cosmetics-Warehouse-Agentflow-v1.json node customFunctionAgentflow_0 | F0118 create_app.validate_context() |
| Warehouse-Agentflow · 4 · Calculate with SAP data | flowise/agentflows/SCInsight-Cosmetics-Warehouse-Agentflow-v1.json node customFunctionAgentflow_1 | F0127 create_app.warehouse_balancing() |
| Warehouse-Agentflow · 5 · Policy search (RAG) | flowise/agentflows/SCInsight-Cosmetics-Warehouse-Agentflow-v1.json node customFunctionAgentflow_2 | F0076 create_app.rag_search(), F0133 create_app.rag_search() |
| Warehouse-Agentflow · 8 · Check every number | flowise/agentflows/SCInsight-Cosmetics-Warehouse-Agentflow-v1.json node customFunctionAgentflow_3 | (no API call) |
