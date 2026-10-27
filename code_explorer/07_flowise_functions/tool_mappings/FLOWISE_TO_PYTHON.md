# Flowise → FastAPI → Python (generated)

Every Flowise Custom Tool and Agentflow Custom Function, the SCInsight endpoints it calls (parsed from its JavaScript), and therefore the Python handler that runs.

| Flowise node | Source | FastAPI handler(s) |
|---|---|---|
| Flowise Custom Tool · calculate_stock_cover | flowise/tools/calculate_stock_cover.json | F2009 create_router.replenishment() |
| Flowise Custom Tool · check_batch_quality | flowise/tools/check_batch_quality.json | F2012 create_router.quality_check() |
| Flowise Custom Tool · check_material_readiness | flowise/tools/check_material_readiness.json | F2007 create_router.material_readiness() |
| Flowise Custom Tool · forecast_demand | flowise/tools/forecast_demand.json | F2010 create_router.forecast_demand() |
| Flowise Custom Tool · get_decision_status | flowise/tools/get_decision_status.json | F2018 create_router.get_decision() |
| Flowise Custom Tool · get_material_bom | flowise/tools/get_material_bom.json | F2001 create_router.sap_bom() |
| Flowise Custom Tool · get_open_purchase_orders | flowise/tools/get_open_purchase_orders.json | F2003 create_router.sap_purchase_orders() |
| Flowise Custom Tool · get_production_orders | flowise/tools/get_production_orders.json | F2002 create_router.sap_production_orders() |
| Flowise Custom Tool · get_sap_inventory | flowise/tools/get_sap_inventory.json | F2000 create_router.sap_inventory() |
| Flowise Custom Tool · get_supplier_reliability | flowise/tools/get_supplier_reliability.json | F2011 create_router.forecast_lead_time() |
| Flowise Custom Tool · get_verified_outcomes | flowise/tools/get_verified_outcomes.json | F2023 create_router.learning_metrics() |
| Flowise Custom Tool · optimize_warehouse_transfer | flowise/tools/optimize_warehouse_transfer.json | F2008 create_router.warehouse_balancing() |
| Flowise Custom Tool · save_recommendation | flowise/tools/save_recommendation.json | F2016 create_router.create_decision() |
| Flowise Custom Tool · search_supply_chain_policy | flowise/tools/search_supply_chain_policy.json | F0076 create_app.rag_search(), F2014 create_router.rag_search() |
| Decision-Outcome-Learning-Agentflow · 2 · Check access | flowise/agentflows/SCInsight-Cosmetics-Decision-Outcome-Learning-Agentflow-v1.json node customFunctionAgentflow_0 | F1999 create_router.validate_context() |
| Decision-Outcome-Learning-Agentflow · 3 · Check the outcome with SAP data | flowise/agentflows/SCInsight-Cosmetics-Decision-Outcome-Learning-Agentflow-v1.json node customFunctionAgentflow_1 | F2022 create_router.reconcile(), F2023 create_router.learning_metrics() |
| Decision-Outcome-Learning-Agentflow · 4 · Final report | flowise/agentflows/SCInsight-Cosmetics-Decision-Outcome-Learning-Agentflow-v1.json node customFunctionAgentflow_2 | (no API call) |
| Factory-Planning-Agentflow · 2 · Check access | flowise/agentflows/SCInsight-Cosmetics-Factory-Planning-Agentflow-v1.json node customFunctionAgentflow_0 | F1999 create_router.validate_context() |
| Factory-Planning-Agentflow · 4 · Calculate with SAP data | flowise/agentflows/SCInsight-Cosmetics-Factory-Planning-Agentflow-v1.json node customFunctionAgentflow_1 | F2002 create_router.sap_production_orders(), F2007 create_router.material_readiness() |
| Factory-Planning-Agentflow · 5 · Policy search (RAG) | flowise/agentflows/SCInsight-Cosmetics-Factory-Planning-Agentflow-v1.json node customFunctionAgentflow_2 | F0076 create_app.rag_search(), F2014 create_router.rag_search() |
| Factory-Planning-Agentflow · 8 · Check every number | flowise/agentflows/SCInsight-Cosmetics-Factory-Planning-Agentflow-v1.json node customFunctionAgentflow_3 | (no API call) |
| Inventory-Optimizer-Agentflow · 2 · Check access | flowise/agentflows/SCInsight-Cosmetics-Inventory-Optimizer-Agentflow-v1.json node customFunctionAgentflow_0 | F1999 create_router.validate_context() |
| Inventory-Optimizer-Agentflow · 4 · Calculate with SAP data | flowise/agentflows/SCInsight-Cosmetics-Inventory-Optimizer-Agentflow-v1.json node customFunctionAgentflow_1 | F2009 create_router.replenishment(), F2010 create_router.forecast_demand() |
| Inventory-Optimizer-Agentflow · 5 · Policy search (RAG) | flowise/agentflows/SCInsight-Cosmetics-Inventory-Optimizer-Agentflow-v1.json node customFunctionAgentflow_2 | F0076 create_app.rag_search(), F2014 create_router.rag_search() |
| Inventory-Optimizer-Agentflow · 8 · Check every number | flowise/agentflows/SCInsight-Cosmetics-Inventory-Optimizer-Agentflow-v1.json node customFunctionAgentflow_3 | (no API call) |
| Logistics-Agentflow · 2 · Check access | flowise/agentflows/SCInsight-Cosmetics-Logistics-Agentflow-v1.json node customFunctionAgentflow_0 | F1999 create_router.validate_context() |
| Logistics-Agentflow · 4 · Calculate with SAP data | flowise/agentflows/SCInsight-Cosmetics-Logistics-Agentflow-v1.json node customFunctionAgentflow_1 | F2008 create_router.warehouse_balancing() |
| Logistics-Agentflow · 5 · Policy search (RAG) | flowise/agentflows/SCInsight-Cosmetics-Logistics-Agentflow-v1.json node customFunctionAgentflow_2 | F0076 create_app.rag_search(), F2014 create_router.rag_search() |
| Logistics-Agentflow · 8 · Check every number | flowise/agentflows/SCInsight-Cosmetics-Logistics-Agentflow-v1.json node customFunctionAgentflow_3 | (no API call) |
| Procurement-Agentflow · 2 · Check access | flowise/agentflows/SCInsight-Cosmetics-Procurement-Agentflow-v1.json node customFunctionAgentflow_0 | F1999 create_router.validate_context() |
| Procurement-Agentflow · 4 · Calculate with SAP data | flowise/agentflows/SCInsight-Cosmetics-Procurement-Agentflow-v1.json node customFunctionAgentflow_1 | F2005 create_router.sap_suppliers(), F2009 create_router.replenishment(), F2011 create_router.forecast_lead_time() |
| Procurement-Agentflow · 5 · Policy search (RAG) | flowise/agentflows/SCInsight-Cosmetics-Procurement-Agentflow-v1.json node customFunctionAgentflow_2 | F0076 create_app.rag_search(), F2014 create_router.rag_search() |
| Procurement-Agentflow · 8 · Check every number | flowise/agentflows/SCInsight-Cosmetics-Procurement-Agentflow-v1.json node customFunctionAgentflow_3 | (no API call) |
| Quality-Agentflow · 2 · Check access | flowise/agentflows/SCInsight-Cosmetics-Quality-Agentflow-v1.json node customFunctionAgentflow_0 | F1999 create_router.validate_context() |
| Quality-Agentflow · 4 · Calculate with SAP data | flowise/agentflows/SCInsight-Cosmetics-Quality-Agentflow-v1.json node customFunctionAgentflow_1 | F2012 create_router.quality_check() |
| Quality-Agentflow · 5 · Policy search (RAG) | flowise/agentflows/SCInsight-Cosmetics-Quality-Agentflow-v1.json node customFunctionAgentflow_2 | F0076 create_app.rag_search(), F2014 create_router.rag_search() |
| Quality-Agentflow · 8 · Check every number | flowise/agentflows/SCInsight-Cosmetics-Quality-Agentflow-v1.json node customFunctionAgentflow_3 | (no API call) |
| Supervisor-Agentflow · 2 · Check access | flowise/agentflows/SCInsight-Cosmetics-Supervisor-Agentflow-v1.json node customFunctionAgentflow_0 | F1999 create_router.validate_context() |
| Supervisor-Agentflow · 4 · Safety guard | flowise/agentflows/SCInsight-Cosmetics-Supervisor-Agentflow-v1.json node customFunctionAgentflow_1 | (no API call) |
| Supervisor-Agentflow · 7 · Save recommendation | flowise/agentflows/SCInsight-Cosmetics-Supervisor-Agentflow-v1.json node customFunctionAgentflow_2 | F2016 create_router.create_decision() |
| Supervisor-Agentflow · 10 · Show the verified decision | flowise/agentflows/SCInsight-Cosmetics-Supervisor-Agentflow-v1.json node customFunctionAgentflow_3 | (no API call) |
| Supervisor-Agentflow · 10 · Withdraw | flowise/agentflows/SCInsight-Cosmetics-Supervisor-Agentflow-v1.json node customFunctionAgentflow_4 | F2020 create_router.withdraw() |
| Warehouse-Agentflow · 2 · Check access | flowise/agentflows/SCInsight-Cosmetics-Warehouse-Agentflow-v1.json node customFunctionAgentflow_0 | F1999 create_router.validate_context() |
| Warehouse-Agentflow · 4 · Calculate with SAP data | flowise/agentflows/SCInsight-Cosmetics-Warehouse-Agentflow-v1.json node customFunctionAgentflow_1 | F2008 create_router.warehouse_balancing() |
| Warehouse-Agentflow · 5 · Policy search (RAG) | flowise/agentflows/SCInsight-Cosmetics-Warehouse-Agentflow-v1.json node customFunctionAgentflow_2 | F0076 create_app.rag_search(), F2014 create_router.rag_search() |
| Warehouse-Agentflow · 8 · Check every number | flowise/agentflows/SCInsight-Cosmetics-Warehouse-Agentflow-v1.json node customFunctionAgentflow_3 | (no API call) |
