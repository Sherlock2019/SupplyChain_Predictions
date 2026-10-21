-- SupplyChain Insight AI — core schema (portable: PostgreSQL 17 and SQLite).
-- Master data is keyed by (tenant_id, natural key); every table carries tenant_id so every query can be tenant-scoped.

create table if not exists tenants (
  id text primary key, name text not null, industry text not null, synthetic integer not null default 1,
  industry_sharing_enabled integer not null default 0, created_at text not null
);
create table if not exists users (
  id text primary key, tenant_id text not null references tenants(id), name text not null, email text not null,
  api_key_hash text not null unique, active integer not null default 1, created_at text not null
);
create table if not exists role_assignments (
  user_id text not null references users(id), tenant_id text not null references tenants(id), role text not null,
  primary key (user_id, tenant_id, role)
);
create table if not exists sap_snapshots (
  id text primary key, tenant_id text not null references tenants(id), source_system text not null, extracted_at text not null,
  as_of_date text not null, status text not null, synthetic integer not null default 1, provenance text not null
);
create table if not exists warehouses (
  tenant_id text not null, code text not null, name text not null, kind text not null, region text not null, city text not null,
  target_cover_days integer not null default 14, primary key (tenant_id, code)
);
create table if not exists products (
  tenant_id text not null, sku text not null, name text not null, category text not null, uom text not null,
  shelf_life_days integer not null, unit_cost_eur real not null, primary key (tenant_id, sku)
);
create table if not exists materials (
  tenant_id text not null, material_id text not null, name text not null, uom text not null, unit_cost_eur real not null,
  critical integer not null default 0, primary key (tenant_id, material_id)
);
create table if not exists bom_components (
  tenant_id text not null, sku text not null, bom_version text not null, material_id text not null, qty_per_unit real not null,
  uom text not null, scrap_pct real not null default 0, valid_from text not null, valid_to text, status text not null,
  primary key (tenant_id, sku, bom_version, material_id)
);
create table if not exists inventory_batches (
  tenant_id text not null, batch_id text not null, location text not null, item_id text not null, item_type text not null,
  quantity real not null, uom text not null, status text not null, expiry_date text, reserved_for text, snapshot_id text not null,
  primary key (tenant_id, batch_id)
);
create table if not exists production_orders (
  tenant_id text not null, order_id text not null, sku text not null, quantity real not null, uom text not null, plant text not null,
  start_date text not null, due_date text not null, status text not null, primary key (tenant_id, order_id)
);
create table if not exists suppliers (
  tenant_id text not null, supplier_id text not null, name text not null, country text not null, approved integer not null,
  primary key (tenant_id, supplier_id)
);
create table if not exists supplier_items (
  tenant_id text not null, supplier_id text not null, material_id text not null, unit_price_eur real not null, moq real not null,
  contract_lead_time_days integer not null, primary key (tenant_id, supplier_id, material_id)
);
create table if not exists purchase_orders (
  tenant_id text not null, po_id text not null, supplier_id text not null, material_id text not null, quantity real not null,
  uom text not null, plant text not null, order_date text not null, promised_date text not null, status text not null,
  received_date text, received_quantity real, primary key (tenant_id, po_id)
);
create table if not exists sales_history (
  tenant_id text not null, sku text not null, warehouse text not null, day text not null, quantity real not null,
  primary key (tenant_id, sku, warehouse, day)
);
create table if not exists transport_lanes (
  tenant_id text not null, lane_id text not null, origin text not null, destination text not null, mode text not null,
  lead_days integer not null, cost_per_unit_eur real not null, fixed_cost_eur real not null, capacity_units integer not null,
  primary key (tenant_id, lane_id)
);
create table if not exists agent_runs (
  id text primary key, tenant_id text not null, user_id text not null, kind text not null, request text not null,
  result text not null, snapshot_id text not null, created_at text not null
);
create table if not exists recommendations (
  id text primary key, tenant_id text not null, calculation_id text not null, domain text not null, title text not null,
  proposed_actions text not null, evidence text not null, prediction text, risk_level text not null, status text not null,
  idempotency_key text not null, model_version text, created_by text not null, created_at text not null, updated_at text not null,
  unique (tenant_id, idempotency_key)
);
create table if not exists human_decisions (
  id text primary key, tenant_id text not null, recommendation_id text not null, reviewer_id text not null, reviewer_roles text not null,
  decision text not null, explanation text not null, modifications text, created_at text not null
);
create table if not exists sap_execution_refs (
  id text primary key, tenant_id text not null, recommendation_id text not null, sap_document text not null, doc_type text not null,
  executed_at text not null, recorded_by text not null, source text not null, unique (tenant_id, sap_document)
);
create table if not exists observed_outcomes (
  id text primary key, tenant_id text not null, recommendation_id text not null, source_document text not null, metric text not null,
  predicted real, actual real, unit text not null, observed_at text not null, complete integer not null, quality_flags text not null
);
create table if not exists learning_records (
  id text primary key, tenant_id text not null, recommendation_id text not null, outcome_id text not null, features text not null,
  label text not null, signed_error real, abs_error real, human_decision text not null, outcome_status text not null,
  model_version text, label_version text not null, approved_for_training integer not null, created_at text not null,
  unique (tenant_id, recommendation_id, label_version)
);
create table if not exists model_versions (
  id text primary key, tenant_id text not null, model_name text not null, version text not null, algorithm text not null,
  trained_at text not null, train_rows integer not null, holdout_rows integer not null, metrics text not null,
  baseline_metrics text not null, status text not null, promoted_by text, promoted_at text
);
create table if not exists retraining_requests (
  id text primary key, tenant_id text not null, model_name text not null, reason text not null, evidence text not null,
  status text not null, requested_by text not null, created_at text not null
);
create table if not exists audit_events (
  id integer primary key, tenant_id text not null, actor text not null, roles text not null, action text not null,
  details text not null, ts text not null, prev_hash text not null, hash text not null
);
create table if not exists rag_documents (
  tenant_id text not null, doc_id text not null, version text not null, title text not null, category text not null,
  valid_from text not null, valid_to text, access_roles text not null, source_path text not null, sha256 text not null,
  flags text not null, ingested_at text not null, primary key (tenant_id, doc_id, version)
);
create table if not exists rag_chunks (
  id text primary key, tenant_id text not null, doc_id text not null, version text not null, chunk_index integer not null,
  section text not null, text text not null, embedding text not null, embedding_model text not null
);
create index if not exists ix_inventory_item on inventory_batches (tenant_id, item_id, location);
create index if not exists ix_sales on sales_history (tenant_id, sku, warehouse, day);
create index if not exists ix_reco_status on recommendations (tenant_id, status);
create index if not exists ix_chunks_tenant on rag_chunks (tenant_id, doc_id);
