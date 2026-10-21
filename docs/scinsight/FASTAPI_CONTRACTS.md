# FastAPI contracts: SCInsight API

- **Base URL:** `http://localhost:8100` (from Flowise: `http://scinsight-api:8100`). Swagger is at `/docs`, OpenAPI at `/openapi.json`.
- **Auth:** `X-API-Key: <key>` or `Authorization: Bearer <key>`. The optional `X-Tenant` header must match the key's tenant (otherwise 403, audited).
- **Request bodies are strict:** unknown fields get 422. Codes match `^[A-Z0-9][A-Z0-9_-]{1,40}$`.

## Errors

| Code | Meaning |
|---|---|
| 401 | Missing or unknown key |
| 403 | Wrong tenant, missing role, wrong review domain, or the agent attempting a review |
| 404 | Item, order, supplier, calculation or recommendation not found *for this tenant* |
| 405 | Any write to `/api/v1/sap/*` (audited) |
| 409 | Stale or missing SAP snapshot (older than `SCI_SNAPSHOT_MAX_AGE_DAYS=2`); decision already taken; SAP document already linked; recommendation not executed |
| 422 | Validation, e.g. a production order sent together with sku/quantity/need_date, or a calculation with no proposed action |

## Context

| Method | Path | Body | Returns |
|---|---|---|---|
| GET | /health | – | status, sap_mode, sap_write_enabled=false, human_approval_required, database |
| GET | /api/v1/context | – | user, tenant, roles, is_human, snapshot |
| POST | /api/v1/context/validate | `{session_id}` | valid, tenant, user, roles, can_approve, snapshot, `authorized_context_ref`, `catalog` (codes and names only) |

## Synthetic SAP (read-only)

| Method | Path | Query |
|---|---|---|
| GET | /api/v1/sap/inventory | `item_id`, `location`, `include_unusable` |
| GET | /api/v1/sap/bom/{sku} | `on` (date; default: the snapshot date) |
| GET | /api/v1/sap/production-orders | `sku`, `status` |
| GET | /api/v1/sap/purchase-orders | `material_id`, `supplier_id`, `status` |
| GET | /api/v1/sap/warehouses | – |
| GET | /api/v1/sap/suppliers | – (with supplier items) |
| POST/PUT/PATCH/DELETE | /api/v1/sap/{anything} | → **405** |

## Calculations (each is stored and returns `calculation_id` + `provenance`)

| Method | Path | Body |
|---|---|---|
| POST | /api/v1/optimizer/material-readiness | `{production_order_id}` **or** `{sku, quantity, need_date, plant?}` |
| POST | /api/v1/optimizer/warehouse-balancing | `{sku, target_warehouse?}` |
| POST | /api/v1/optimizer/replenishment | `{item_id, location?, quantity?, need_date?}`. A finished good routes to balancing; a material needs a quantity |
| POST | /api/v1/forecast/demand | `{sku, warehouse, horizon_days=14}` |
| POST | /api/v1/forecast/lead-time | `{supplier_id, material_id?, quantity?}` |
| POST | /api/v1/quality/check-stock | `{item_id, location?, horizon_days=90}` |
| GET | /api/v1/calculations/{id} | – |

Example: `POST /api/v1/optimizer/material-readiness {"production_order_id":"PRD-1001"}` returns
`status: short`, `shortages: [{material_id: PUMP-DISP-24, missing: 20000, uom: EA, required_date: 2026-10-27}]` and
`partial_production_possible: 30000`. The proposed actions are a `purchase_request` (SUP-A, 20,000, arrival 2026-10-30,
`lead_days` 9, €8,400) and `replan_production`.

## RAG

| Method | Path | Body / returns |
|---|---|---|
| POST | /api/v1/rag/search | `{query, top_k=4}` → `results[{text, score, flags, citation{doc_id, version, title, section, chunk, source, valid_from, valid_to}}]`, `note`, `embedding_model` |
| GET | /api/v1/rag/documents | Documents of the tenant + last ingestion report (accepted / rejected / skipped) |

## Decisions

| Method | Path | Body | Who |
|---|---|---|---|
| POST | /api/v1/decisions | `{calculation_id, title?, idempotency_key?, po_id?}` → 201 `pending_review`. Actions are copied from the stored calculation; purchase requests carry a `lead_time_days` prediction | agent_service, planner |
| GET | /api/v1/decisions | `?status=` | readers |
| GET | /api/v1/decisions/{id} | → recommendation + `reviews`, `sap_execution`, `outcomes`, `verified_review`, `review_authority` | readers |
| POST | /api/v1/decisions/{id}/review | `{decision: approve\|reject\|modify\|defer, explanation (≥3 chars), modifications? (required for modify)}` | domain reviewer or director (only from pending or deferred) |
| POST | /api/v1/decisions/{id}/withdraw | – | creator or director (pending only) |
| POST | /api/v1/decisions/{id}/sap-execution | `{sap_document, doc_type, executed_at}`. Records a manual SAP execution; nothing is written to SAP | sap_executor, director |

## Learning

| Method | Path | Body | Who |
|---|---|---|---|
| POST | /api/v1/outcomes/reconcile | `{recommendation_id}`. Executed recommendations only; idempotent | agent_service, planner, director, mlops |
| GET | /api/v1/learning/metrics | – | readers |
| POST | /api/v1/learning/train-lead-time-model | – → candidate model with holdout metrics vs 2 baselines | mlops_engineer |
| POST | /api/v1/learning/models/{id}/promote | – → 409 unless it beats the best baseline | supply_chain_director |
| POST | /api/v1/learning/retraining-requests | `{reason}` → `pending_human_approval` | readers |
| GET | /api/v1/audit | `?limit=` → events + `chain_valid` | supply_chain_director |
