---
doc_id: POL-WH-020
title: Warehouse transfer policy (inter-warehouse stock moves)
category: warehouse_transfer_policy
version: 2.4
tenant: scinsight-cosmetics
valid_from: 2026-01-01
valid_to: 2027-12-31
access_roles: planner,warehouse_manager,logistics_manager,supply_chain_director,agent_service
synthetic: true
---
# Warehouse transfer policy (inter-warehouse stock moves)
## When transfers are allowed
A transfer between Warehouses A, B and C is allowed when the receiving warehouse is projected below 14 days of cover and
the sending warehouse keeps at least 14 days of cover after the transfer.

## What can be transferred
Only released, unreserved batches with at least 60 days of remaining shelf life on arrival may be transferred.
Near-expiry stock is sold locally first (FEFO).

## Approval
Transfers are approved by the warehouse manager. Costs use the contracted lane rates in the SAP transport master.
