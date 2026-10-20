# SOP SC-104 — Factory material readiness check

## Purpose

Confirm that every component on the approved bill of materials is available before a production order is released at FR10, FR20, or the contract manufacturer TPM1.

## Calculation rules

Material readiness uses unrestricted stock plus purchase orders confirmed on or before the production need date. Quality-inspection, blocked, and expired inventory are excluded until SAP records a usage decision or release. Requirements include BOM scrap percentages and are rounded up for each-unit (EA) components. Unconfirmed purchase orders are never counted as supply.

## Status thresholds

A production order is READY when every component is covered. It is AT RISK when at least 75% of components are covered and NOT READY below 75%.

## Actions and approval

When a shortage exists, the planner may propose expediting a later confirmed purchase order, sourcing additional material, or rescheduling production. All proposals are advisory. The supply planner reviews the evidence and the supply-chain manager accepts or rejects the recommendation. Approved actions are executed manually in SAP by an authorized planner. The copilot never writes to SAP.
