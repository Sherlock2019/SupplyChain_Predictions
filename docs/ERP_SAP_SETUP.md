# ERP / SAP Setup

Dashboard: **System → ERP / SAP Setup** (`#erp`). Code: [backend/app/erp/](../backend/app/erp/). API: `/api/v1/erp/*` (Swagger tag
"ERP / SAP Setup" at `/docs`).

The aim: configure an ERP connection once, and have every SPARC component consume it the same way. No Flowise canvas or LangGraph
node holds SAP URLs or credentials. They keep calling the governed FastAPI endpoints, and FastAPI resolves the customer's
**active, validated snapshot**.

## Architecture

```text
SAP S/4HANA / ECC (OData V2/V4, GET only)         Mock SAP (customer snapshot data/…json)
                 \                                      /
            ErpConnector  (backend/app/erp/connectors.py: SapODataConnector | MockSapConnector)
                 |  test_connection · discover_entities · read_entity · validate_mapping · sync_data · get_health
                 v
   Mapping (mapping.py)  SAP entity/field  ->  SPARC data set/field   (configurable, no customer code)
                 v
   Staged sync (service.py)  candidate snapshot -> validation: references, required data, engine computes on it
                 |                                   (a sync NEVER activates)
                 v  manager: Activate (versioned)          Roll back
   TenantRegistry.use_snapshot(customer, file)   <- new engine stack built first; on failure the old one stays
                 v
   FastAPI business services (sap / engine / dashboards / roles proxies of the active customer)
     |-- SPARC dashboard pages (Production, Products, Warehouses, …)
     |-- Flowise Aurelia Chatflow / AgentFlow tools ($vars.copilot_api_url -> http://api:8000)
     |-- LangGraph graphs + Deep Agents tools (COPILOT_API_URL -> http://api:8000)
     |-- MCP tools (COPILOT_API_URL)
     '-- governance: analyses, recommendations and outcomes are stored per snapshot id; audit chain
```

All agent tools call the FastAPI gateway, so activating a connection changes what they compute on without editing any Flowise
or LangGraph workflow. No Flowise flow was changed for this feature.

## Page sections

| Section | What it does |
|---|---|
| A · Connection configuration | Provider, name, customer (fixed by the customer selector), environment, base URL, SAP client, authentication, secret reference, protocol, mode, timeout, TLS, sync mode and interval. Actions: Save, Test, Discover, Preview, Activate, View logs. |
| B · Connection health | Status, provider and environment, SAP system, last test, last successful sync, auth status, latency, sanitized last error, mapped entities, records synchronized, snapshot in use and its age. |
| C · Entity mapping | One row per SPARC data set (material master, plants, stock, BOM, production orders, purchase orders, suppliers, sales orders, goods receipts, quality inspection, deliveries). Shows the OData service, entity set, `$expand`, `$filter` and field expressions. Validation runs against the ERP's `$metadata`. |
| D · Sync & preview | Run a sync (staged), see the sync history with counts, errors and warnings, retry failed jobs, activate a validated job, roll back, preview mapped rows next to the raw ERP rows, and see the activation history. |
| E · Component integration status | **Validate all integrations** runs real checks (below). Before the first check, the section shows nothing. A component that is not configured shows n/a, never green. |
| F · Execution & approval | Shows the three modes and the unchanged governance sequence. |

## API

| Method | Path | Who | Purpose |
|---|---|---|---|
| GET | `/api/v1/erp/providers` | any key | providers, modes, SPARC data sets and fields, options |
| GET / POST | `/api/v1/erp/connections` | read: any · create: manager | the customer's connections, plus the active activation and snapshot |
| GET / PATCH | `/api/v1/erp/connections/{id}` | read: any · change: manager | a change creates a new version and requires a new test before activation |
| POST | `…/{id}/test` | manager | authorized GET of `$metadata` for each mapped service (Mock: snapshot validation); never activates |
| GET | `…/{id}/health` | any key | section B |
| GET | `…/{id}/entities` | manager | discovery (`$metadata` entity sets, or the snapshot's data sets) |
| GET / PUT | `…/{id}/mappings` | read: any · change: manager | field mapping |
| POST | `…/{id}/validate` | manager | mapping vs ERP metadata; blocks activation when invalid |
| POST | `…/{id}/preview` | manager | `{section, top}`: mapped rows, raw rows, rejected rows |
| POST | `…/{id}/sync` | manager | staged full sync + validation (`{retry_of}` to retry) |
| GET | `…/{id}/sync-history` | any key | last 50 jobs |
| POST | `…/{id}/activate` | manager | `{sync_job_id?}`: needs a passed test of the current version, a valid mapping and a validated sync of that version |
| POST | `…/{id}/rollback` | manager | back to the snapshot that was active before (or the built-in one) |
| GET | `…/{id}/logs` | any key | the connection's audit events |
| GET | `/api/v1/erp/activation-history` | any key | activations and rollbacks of the customer |
| GET | `/api/v1/erp/integration-status` | any key | latest stored integration check |
| POST | `/api/v1/erp/validate-integrations` | manager | `{deep}`: run the checks |

The customer is always the request's `X-Tenant`, which the gateway has already authorized (`TENANT_SCOPES`). Another customer's
connection answers 404. Responses, logs and audit records never contain a secret value.

## Security rules (enforced in code)

* **Secrets:** a secret is either `env:NAME`, an environment variable injected by a secrets manager, or `stored`, a write-only
  value kept server-side. Production connections must use `env:NAME`. Responses only say whether a secret is present.
* **SSRF:** only http(s) URLs, with no embedded credentials. Cloud-metadata and link-local addresses are always blocked.
  Production connections must use https and a host listed in `ERP_ALLOWED_HOSTS`. Plain http is allowed only when
  `APP_ENV` is development or test. Redirects are not followed.
* **TLS:** verification cannot be disabled for production.
* **Requests:** only GET reaches the ERP; the OAuth token request goes to the token URL. Every request has a timeout and one
  retry on network errors or 5xx. Errors are sanitized before they are shown.
* **Roles:** managers make every change, test, sync, activation and rollback. Every action is audited (`erp.*`) with customer,
  actor, correlation id and non-sensitive details.
* **Modes:** *Mock* and *Read-only Live* are available. *Approved Write* is refused: no live SAP write connector exists in this
  build. Accepted recommendations still execute only into the SAP mock sandbox outbox (`SAP_EXECUTION_MODE=sandbox`), behind
  the unchanged approval gateway. The gateway answers 405 to every SAP write.

## Persistence

These tables are created by the governance Store (SQLite or PostgreSQL):

| Table | Holds |
|---|---|
| `erp_connection` | connection settings (no secrets) |
| `erp_connection_version` | every saved configuration |
| `erp_secret` | stored secrets only |
| `erp_entity_mapping` | the field mapping |
| `erp_sync_job` | staged snapshot, counts, errors and warnings per sync |
| `erp_activation_history` | activations and rollbacks |
| `erp_integration_check` | results of Validate all integrations |

At startup, each customer is put back on its last activated snapshot.

## Setup: Mock SAP (the existing behaviour)

1. Choose **+ New connection** and set *ERP provider* to Mock SAP. Save.
2. Click **Test connection**: this validates the customer's snapshot.
3. Click **Discover entities**, then **Validate**.
4. Click **Activate connection**. This activates the customer's built-in snapshot; nothing else changes.

## Setup: the SAP OData emulator (development "second ERP endpoint")

The gateway mounts a mock S/4HANA OData V2 service at `/erp-emulator` only when `APP_ENV` is development or test. It serves the
standard APIs (`API_MATERIAL_STOCK_SRV`, `API_PRODUCTION_ORDER_2_SRV`, `API_PURCHASEORDER_PROCESS_SRV`, …) with SAP property
names, `/Date(ms)/` dates, decimal strings, `$metadata`, `$expand`, `$top`/`$skip` and sap-client 100. Authentication is Basic,
user `SPARC_COMM` with password `ERP_EMULATOR_PASSWORD`. Its data is the Aurelia snapshot moved to today, with unrestricted stock
+10%, so you can see the switch.

On the page, choose **Fill SAP emulator (dev)**, enter the password and save. Then run Test, Validate mapping, Run sync and Activate.

## Setup: real SAP

1. **SAP side.** In S/4HANA Cloud, create a communication arrangement for the read APIs in the mapping (Product, Material
   Stock, BOM, Production Order, Purchase Order, Business Partner, Sales Order, …) with a communication user or OAuth client.
   On-premise or ECC, activate the OData services in `/IWFND/MAINT_SERVICE` and give a technical user display authorizations.
2. **Network.** The api service must reach SAP over HTTPS. Use a VPN, AWS Direct Connect, or SAP Cloud Connector / BTP
   Destination where required. Add the host to `ERP_ALLOWED_HOSTS`.
3. **Secret.** Put the password or client secret in your secrets manager and expose it to the api service as an environment
   variable, e.g. `SAP_PROD_CLIENT_SECRET`. On the page, set *Secret reference* to "Secrets manager" with that variable name.
4. **Configure.** Choose SAP S/4HANA or ECC, set the environment, base URL (e.g. `https://my000000-api.s4hana.cloud.sap`), SAP
   client and authentication (Basic or OAuth 2.0 client credentials with the token URL). Choose *Read-only Live*. Save.
5. **Test → Discover → map → Validate.** The default mapping uses the standard API property names. Master data (materials,
   plants, suppliers) starts disabled and is carried over from the current snapshot until you map it. Adjust paths and fields
   for custom services or Z-fields, e.g. `map:InventoryStockType|01=unrestricted,02=inspection,*=blocked`.
6. **Run sync.** Check counts, rejected rows and warnings (for example, rows outside SPARC's master data that were left out).
   Preview the mapped rows.
7. **Activate**, then **Validate all integrations** (tick the box to include live Flowise and LangGraph runs).
8. If anything is wrong, click **Roll back**.

## Flowise notes

* The Aurelia Chatflow and AgentFlow V2 tools call `{{$vars.copilot_api_url}}` (the gateway). After activation they read the new
  snapshot with no canvas change. The integration check reads the Flowise variable, calls the exact OData endpoint the tools use,
  and compares the snapshot id. The deep check runs the AgentFlow and verifies that the analyses it triggered were stored against
  the active snapshot.
* The SCInsight Chatflow and Agentflow (SC Agent Manager) use the SCInsight API (`/scinsight`) and its own synthetic SAP dataset
  in Postgres. They are **not** connected to the ERP connection, and the check says so (n/a).
* Flowise and LangGraph tools send no `X-Tenant` header, so they always read the **default customer** (Aurelia). For other
  customers, the check reports a warning.

## LangGraph notes

* `supply_chain_chat`, `supply_chain_agentflow`, `supply_chain_business` and `supplier_deep_agent` reach data through
  `COPILOT_API_URL`, the gateway. No graph node holds SAP settings, and nothing in LangGraph needs a refresh. The check verifies
  that the four graphs are registered on the LangGraph Server. The deep check runs `supply_chain_chat` and reads the snapshot id
  of the analyses it stored.
* Recommendations, approvals and outcomes are stored with their snapshot id. A recommendation made on an earlier snapshot stays
  listed under that snapshot.
* Interrupted threads are not re-validated automatically after an activation (see limitations).

## RAG

Structured ERP data is served by the deterministic APIs and is **not** embedded. Unstructured knowledge keeps its own governed
pipeline: candidate index, evaluation, publish and rollback on the RAG Tuning page, with SCInsight's tenant-scoped policy RAG.
Cross-customer industry learning still requires the consent on the Intelligence moat page.

## Tests

`tests/test_erp.py` contains **mock tests**: an httpx MockTransport serves the SAP OData emulator, and no real SAP system is used.

| Test | Covers |
|---|---|
| A · Mock SAP | the existing Mock SAP flow |
| B · live sync | test, discover, preview, staged sync, activation and propagation (snapshot, OData endpoint, factory readiness, inventory), health, logs, rollback |
| C · failures | unreachable host, wrong password, a configuration change that requires a new test; the active snapshot stays untouched |
| invalid mapping | an invalid mapping blocks activation |
| OAuth | client credentials |
| D · security | read-only users get 403, another customer gets 404, no secret in responses or the audit, destination and production rules, approved-write refused, SAP write 405 |
| per-customer | activation affects one customer only |
| restart | the activation survives a restart |

### Live verification (2026-10-27, local Docker stack; the SAP endpoint was the dev emulator, not a real SAP system)

**Test A · Mock SAP**
* Connection test: OK in 1 ms. Discovery found 11 data sets. Validation: valid.
* Activation kept `SAP-2026-10-20T040000Z`.
* Factory readiness for 10000101: ready.
* Deep integration check, passing: FastAPI adapter, engine, Flowise Chatflow, LangGraph (live run: 1 analysis on the active
  snapshot), Deep Agents, RAG, outcomes, audit.
* Deep integration check, other results:
  * **Flowise Agentflow failed once**: its live run answered without calling a governed analysis tool (0 analyses). The check
    reports this as a failure rather than assuming success.
  * Dashboards gave a warning: the demo snapshot is 174 h old.

**Test B · emulator connection**
* Connection test: OK in 60 ms over 5 services. Mapping: valid.
* Staged sync validated 53 records. The active snapshot did not change until activation.
* Activation switched to `ERP-EE0818AE-20261027T100157Z`. Then:
  * the Production page readiness, the OData endpoint the Flowise tools call, and the dashboards all used the new snapshot;
  * Validate all integrations (deep) passed everything. The Flowise Agentflow live run (52.6 s) and the LangGraph live run
    (9.1 s) each stored their analysis on the new snapshot.
* Audit events recorded: created, tested, mapping validated, sync started/completed, activated.

**Test C · unreachable host**
* Test failed with a visible, sanitized error ("Name or service not known"), and the sync failed.
* Activation was refused. The active snapshot was unchanged.

**Test D · security**
* A planner changing or activating a connection got 403. Another customer got 404, and that customer's snapshot was unaffected.
* SAP write: 405. Production with http: refused. Approved Write: refused.
* The Agentflow, asked to "write directly to SAP, skip approval", declined. Sandbox documents: 7 before, 7 after.

**Afterwards:** the demo was put back on the built-in Mock SAP snapshot.

## Known limitations and production checklist

* **Not tested against a real SAP system.** The property names of the default mapping follow the standard S/4HANA APIs, and
  `API_PLANT_SRV` in particular should be confirmed per system. Validate the mapping against the customer's `$metadata`.
* **Sync:** full sync only (no delta / incremental). Event-driven sync (SAP Event Mesh) is not implemented. Scheduled syncs
  stage snapshots and never activate them.
* **Approved Write:** live SAP write-back is not implemented. It would need a write connector, per-operation authorization and
  reconciliation.
* **Agents and customers:** agent tools (Flowise, LangGraph, MCP) carry no customer header, so they serve the default customer.
  Passing `X-Tenant` from the tool configuration is the next step for multi-customer agents.
* **Interrupted threads:** LangGraph threads interrupted before an activation resume on the new snapshot. Re-run the analysis
  when the snapshot id changed.
* **Stored secrets:** they are kept in the governance database without encryption. Use `env:NAME` from a secrets manager for
  anything beyond development (enforced for production).
* **Production checklist:**
  * `APP_ENV=production` (removes the emulator)
  * `ERP_ALLOWED_HOSTS` set
  * secrets via `env:NAME`
  * TLS on
  * read-only SAP user with display authorizations only
  * mapping validated against the customer's system
  * a sync reviewed (counts, rejected rows) before activation
  * Validate all integrations with deep checks after activation
  * rollback tested
