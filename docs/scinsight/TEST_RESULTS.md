# Test results

Run on 2026-10-20 (container clock; the synthetic business date is 2026-10-21) on the local stack:
- WSL2 Ubuntu, Docker
- Flowise **3.1.2** (`flowiseai/flowise:3.1.2`)
- PostgreSQL 17 + pgvector
- Qwen 2.5 7B (`qwen2.5-7b-scm`, Ollama, num_ctx 16384, temperature 0)

## 1. Unit, API and security tests (hermetic, SQLite, no LLM)

`pytest tests` gives **122 passed, 11 skipped**. Lint (`ruff`) is clean. The 9 Flowise end-to-end tests are opt-in and skipped
by default; 2 skips predate this work.

SCInsight files: `tests/scinsight/test_business_rules.py`, `test_api_scenarios.py`, `test_security.py`. They cover:
- **Business functions:** usable stock, BOM with scrap and unit conversion, shortage, days of cover, replenishment, transfer
  candidates and feasibility, supply option ranking, expiry risk, lead-time estimate, prediction error, reconciliation.
- **Scenario 1** (20,000 pumps), **scenario 2** (2,004 from WH-C), **scenario 3** (4,500 usable of 7,500).
- **Review lifecycle:** agent 403, wrong domain 403, modify needs modifications, decided once (409), deferral, withdrawal
  (creator only), SAP execution record (role-gated; a document can be linked only once, otherwise 409).
- **Learning:** REC-HIST-0001 gives +4 days, verified and idempotent. A purchase request carries a reconcilable lead-time
  prediction. The model is trained as a candidate and the promotion gate decides.
- **Security (brief section 17):**
  - unauthenticated / invalid key → 401
  - forged tenant → 403, audited
  - cross-tenant data invisible
  - SAP writes → 405
  - `SAP_WRITE_ENABLED=true` → refuses to start
  - strict schemas → 422
  - a production-order quantity cannot be overridden by a caller or model → 422
  - RAG tenant isolation, injection flagging, metadata-less document rejected
  - audit chain valid
  - configured keys rotate out stored dev keys
  - a PostgreSQL deployment refuses to start without all user keys

## 2. PostgreSQL verification (the stack's `scinsight` database)

- Migrations 0001 and 0002 (pgvector, HNSW) are applied.
- 9 documents ingested into 22 chunks with `vector(384)`; the broken document is rejected.
- Restart is idempotent (no re-ingest).
- Scenario 1 gives 20,000 missing. Policy RAG returns POL-WH-020 and POL-QA-045.
- Review once gives 200, a second review 409. `chain_valid: true`.
- Live service: `/health` reports postgres; `/docs` returns 200; the generated agent key gets 200 and the public dev key 401.

## 3. Flowise execution: stack instance (`SCI_E2E=1 pytest tests/scinsight/test_flowise_e2e.py`)

**9 passed in 62 s.** These are real prediction-API calls with the LLM. The numeric assertions check the stored calculation the answer cites.

| Test | Result |
|---|---|
| Prediction without API key | Refused ("Unauthorized"; Flowise answers HTTP 500 with that message, not 401) |
| SAP-write request | "read-only" reply; no specialist called |
| Instruction override | Blocked by the deterministic guard |
| Scenario 1 via supervisor → Factory-Planning | CALC shows PUMP-DISP-24 missing 20,000; run **paused**; Proceed with no review → "still pending_review … not an approval"; API still pending |
| Scenario 2 via supervisor → Warehouse | CALC shows WH-C→WH-B 2,004; agent key review 403, quality manager 403, warehouse manager 200; Proceed → "approved by u-warehouse-manager" |
| Scenario 3 via supervisor → Quality | CALC shows usable 4,500 of 7,500, 4 exclusions; Reject → withdrawn (API confirms) |
| Procurement | purchase_request SUP-A, lead_days 9.0; recommendation domain procurement, prediction 9.0 |
| Learning | REC-HIST-0001 outcome predicted 5, actual 9; MAE 4.0 |
| Chatflow | Only allowlisted tools; real tool outputs (no errors); evidence footer present |

## 4. Clean instance: export → reimport → execute (`scripts/scinsight-clean-flowise-test.sh`)

- A brand-new Flowise 3.1.2 container with an empty SQLite volume on `:3010`.
- `deploy.py import` read only the committed export files: admin registered, 14 tools, 7 specialists, supervisor, Chatflow.
- The same e2e suite against it: **9 passed in 63 s**.

The first attempt failed with `isDeniedIP … denied by policy`, because the clean container used Flowise's default SSRF policy.
The fix is configuration (`HTTP_SECURITY_CHECK=false` + `HTTP_DENY_LIST`), now in the script and in
[FLOWISE_IMPORT_GUIDE.md](FLOWISE_IMPORT_GUIDE.md).

## 4b. Completeness audit (all 9 flows, stack and clean instance)

Structure checks:
- every node is wired
- every condition / human-input branch is connected
- every node has a description panel
- no unbound placeholder
- credentials are set
- every Execute Flow / Chatflow Tool target exists
- every flow is API-key protected

All 9 flows pass, on both instances. 0 problems.

Execution checks:
- each of the 7 specialists called directly
- every supervisor route: 7 specialists, SAP-write refusal, override refusal, out of scope
- the chatflow routed to each of the 7 specialists, plus an SAP lookup and a policy search

All correct.

## 5. Problems found by executing in Flowise (and fixed)

| Found | Fix |
|---|---|
| Explanation LLM never saw the calculation (`llmUserMessage` is ignored when memory is off) and invented numbers; the evidence gate withheld them | User content moved into `llmMessages` |
| Structured-output parser aborted runs when Qwen left out a key or wrote `NONE` unquoted | JSON or plain-text answers, parsed leniently in code |
| Chatflow: model sent PRD-1001 **with an invented quantity 500**, and the API accepted the override | API: a production order is sent alone (422 otherwise); tool drops extra fields; regression test |
| Human Input text duplicated the analysis | Flowise prepends the last message; removed the duplicate |
| Lead-time estimate could never become a recommendation; new purchase requests were not reconcilable | Purchase requests carry `lead_days`; recommendations store a lead-time prediction; material purchases are reviewed by procurement |
| A duplicate SAP document crashed with a 500 | 409 with the linked recommendation |
| Learning specialist: Qwen restated the REC-HIST-0001 result as "matched exactly, no error" (true error +4); both numbers were in the evidence, so the number gate passed it | The learning report is returned deterministically, without LLM rewording |
| The flat chatflow (one agent, 14 tools) mis-read a readiness result ("can run on time") | The chatflow's SC Agent Manager now delegates to the 7 specialist Agentflows; the same question is now answered correctly through `factory_specialist` |
| The public dev keys were still valid on the PostgreSQL deployment (seeded by an earlier check) | Configured keys always replace stored hashes; PostgreSQL deployments refuse to start without all keys |

## 6. Residual risks (honest)

- **The 7B model makes semantic mistakes that the number gate cannot catch.** In one chat answer it wrote "50,000 EA is missing"
  (the shortage is 20,000; both numbers exist in the evidence). The gate also withholds many narratives (e.g. the learning
  report, "Is Supplier A reliable?"); the deterministic summary is shown instead, which is safe but less fluent. A stronger model
  and an answer-level verifier are pilot prerequisites. For decisions, use the supervisor Agentflow, which explains from a
  deterministic summary.
- **Flowise prediction without a key** is refused with HTTP 500 "Unauthorized", not 401. This is Flowise behaviour.
- **Screenshots** of the Flowise canvases were not captured (headless browser automation hangs on the Flowise canvas in this
  environment). The flows are verified by execution and by the exports.
- **Latency:** 10–20 s per supervisor question on this workstation (one specialist; Qwen via the host's Ollama), 1–4 s for guarded refusals.
