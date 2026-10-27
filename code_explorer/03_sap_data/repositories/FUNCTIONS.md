# 03_sap_data/repositories (generated)

Modules: `backend/app/store.py`, `backend/app/tenants.py`

| ID | Function / class | Kind | Status | Original | Annotated copy | Summary |
|---|---|---|---|---|---|---|
| F0344 | `_now` | function | used | [backend/app/store.py:96](../../../backend/app/store.py#L96) | [annotated](../../03_sap_data/repositories/app_store.py) |  |
| F0345 | `_digest` | function | used | [backend/app/store.py:100](../../../backend/app/store.py#L100) | [annotated](../../03_sap_data/repositories/app_store.py) |  |
| F0346 | `_SqliteDb` | class | used | [backend/app/store.py:104](../../../backend/app/store.py#L104) | [annotated](../../03_sap_data/repositories/app_store.py) |  |
| F0347 | `_SqliteDb.__init__` | method | used (framework) | [backend/app/store.py:107](../../../backend/app/store.py#L107) | [annotated](../../03_sap_data/repositories/app_store.py) |  |
| F0348 | `_SqliteDb.run` | method | used | [backend/app/store.py:115](../../../backend/app/store.py#L115) | [annotated](../../03_sap_data/repositories/app_store.py) |  |
| F0349 | `_SqliteDb.query` | method | used | [backend/app/store.py:130](../../../backend/app/store.py#L130) | [annotated](../../03_sap_data/repositories/app_store.py) |  |
| F0350 | `_PostgresDb` | class | used | [backend/app/store.py:134](../../../backend/app/store.py#L134) | [annotated](../../03_sap_data/repositories/app_store.py) |  |
| F0351 | `_PostgresDb.__init__` | method | used (framework) | [backend/app/store.py:137](../../../backend/app/store.py#L137) | [annotated](../../03_sap_data/repositories/app_store.py) |  |
| F0352 | `_PostgresDb.run` | method | used | [backend/app/store.py:147](../../../backend/app/store.py#L147) | [annotated](../../03_sap_data/repositories/app_store.py) |  |
| F0353 | `_PostgresDb.query` | method | used | [backend/app/store.py:167](../../../backend/app/store.py#L167) | [annotated](../../03_sap_data/repositories/app_store.py) |  |
| F0354 | `Store` | class | used | [backend/app/store.py:171](../../../backend/app/store.py#L171) | [annotated](../../03_sap_data/repositories/app_store.py) |  |
| F0355 | `Store.__init__` | method | used (framework) | [backend/app/store.py:172](../../../backend/app/store.py#L172) | [annotated](../../03_sap_data/repositories/app_store.py) |  |
| F0356 | `Store.memory` | method | used | [backend/app/store.py:180](../../../backend/app/store.py#L180) | [annotated](../../03_sap_data/repositories/app_store.py) |  |
| F0357 | `Store.dialect` | method | used | [backend/app/store.py:184](../../../backend/app/store.py#L184) | [annotated](../../03_sap_data/repositories/app_store.py) |  |
| F0358 | `Store.audit` | method | used | [backend/app/store.py:189](../../../backend/app/store.py#L189) | [annotated](../../03_sap_data/repositories/app_store.py) |  |
| F0359 | `Store.verify_chain` | method | used | [backend/app/store.py:214](../../../backend/app/store.py#L214) | [annotated](../../03_sap_data/repositories/app_store.py) |  |
| F0360 | `Store.audit_events` | method | used | [backend/app/store.py:223](../../../backend/app/store.py#L223) | [annotated](../../03_sap_data/repositories/app_store.py) |  |
| F0361 | `Store.save_analysis` | method | used | [backend/app/store.py:228](../../../backend/app/store.py#L228) | [annotated](../../03_sap_data/repositories/app_store.py) |  |
| F0362 | `Store.get_analysis` | method | used | [backend/app/store.py:237](../../../backend/app/store.py#L237) | [annotated](../../03_sap_data/repositories/app_store.py) |  |
| F0363 | `Store.latest_actionable` | method | used | [backend/app/store.py:241](../../../backend/app/store.py#L241) | [annotated](../../03_sap_data/repositories/app_store.py) | Newest stored analysis of `kind` among the ids that has proposed actions (server |
| F0364 | `Store.submit` | method | used | [backend/app/store.py:247](../../../backend/app/store.py#L247) | [annotated](../../03_sap_data/repositories/app_store.py) |  |
| F0365 | `Store._recommendation` | method | used | [backend/app/store.py:268](../../../backend/app/store.py#L268) | [annotated](../../03_sap_data/repositories/app_store.py) |  |
| F0366 | `Store.get_recommendation` | method | used | [backend/app/store.py:272](../../../backend/app/store.py#L272) | [annotated](../../03_sap_data/repositories/app_store.py) |  |
| F0367 | `Store.list_recommendations` | method | used | [backend/app/store.py:276](../../../backend/app/store.py#L276) | [annotated](../../03_sap_data/repositories/app_store.py) | Optionally only recommendations whose analysis came from one SAP snapshot (one c |
| F0368 | `Store.decide` | method | used | [backend/app/store.py:289](../../../backend/app/store.py#L289) | [annotated](../../03_sap_data/repositories/app_store.py) |  |
| F0369 | `Store.create_watch` | method | used | [backend/app/store.py:298](../../../backend/app/store.py#L298) | [annotated](../../03_sap_data/repositories/app_store.py) |  |
| F0370 | `Store._watch` | method | used | [backend/app/store.py:305](../../../backend/app/store.py#L305) | [annotated](../../03_sap_data/repositories/app_store.py) |  |
| F0371 | `Store.get_watch` | method | used | [backend/app/store.py:310](../../../backend/app/store.py#L310) | [annotated](../../03_sap_data/repositories/app_store.py) |  |
| F0372 | `Store.list_watches` | method | used | [backend/app/store.py:314](../../../backend/app/store.py#L314) | [annotated](../../03_sap_data/repositories/app_store.py) |  |
| F0373 | `Store.delete_watch` | method | used | [backend/app/store.py:317](../../../backend/app/store.py#L317) | [annotated](../../03_sap_data/repositories/app_store.py) |  |
| F0374 | `Store.record_watch` | method | used | [backend/app/store.py:320](../../../backend/app/store.py#L320) | [annotated](../../03_sap_data/repositories/app_store.py) |  |
| F0375 | `Store.execute_recommendation` | method | used | [backend/app/store.py:324](../../../backend/app/store.py#L324) | [annotated](../../03_sap_data/repositories/app_store.py) | Accepted -> executed, recording the sandbox SAP documents created for each actio |
| F0376 | `Store.sap_documents` | method | used | [backend/app/store.py:339](../../../backend/app/store.py#L339) | [annotated](../../03_sap_data/repositories/app_store.py) |  |
| F0377 | `Store.next_doc_number` | method | used | [backend/app/store.py:344](../../../backend/app/store.py#L344) | [annotated](../../03_sap_data/repositories/app_store.py) |  |
| F0378 | `Store.create_outcome` | method | used | [backend/app/store.py:352](../../../backend/app/store.py#L352) | [annotated](../../03_sap_data/repositories/app_store.py) |  |
| F0379 | `Store._outcome` | method | used | [backend/app/store.py:357](../../../backend/app/store.py#L357) | [annotated](../../03_sap_data/repositories/app_store.py) |  |
| F0380 | `Store.list_outcomes` | method | used | [backend/app/store.py:362](../../../backend/app/store.py#L362) | [annotated](../../03_sap_data/repositories/app_store.py) |  |
| F0381 | `Store.record_outcome` | method | used | [backend/app/store.py:367](../../../backend/app/store.py#L367) | [annotated](../../03_sap_data/repositories/app_store.py) |  |
| F0382 | `Store.record_feedback` | method | used | [backend/app/store.py:380](../../../backend/app/store.py#L380) | [annotated](../../03_sap_data/repositories/app_store.py) | Why an expert approved, modified or rejected a recommendation — a training label |
| F0383 | `Store.feedback` | method | used | [backend/app/store.py:385](../../../backend/app/store.py#L385) | [annotated](../../03_sap_data/repositories/app_store.py) |  |
| F0384 | `Store.consent` | method | used | [backend/app/store.py:390](../../../backend/app/store.py#L390) | [annotated](../../03_sap_data/repositories/app_store.py) |  |
| F0385 | `Store.set_consent` | method | used | [backend/app/store.py:394](../../../backend/app/store.py#L394) | [annotated](../../03_sap_data/repositories/app_store.py) |  |
| F0386 | `Store.get_setting` | method | used | [backend/app/store.py:400](../../../backend/app/store.py#L400) | [annotated](../../03_sap_data/repositories/app_store.py) |  |
| F0387 | `Store.set_setting` | method | used | [backend/app/store.py:404](../../../backend/app/store.py#L404) | [annotated](../../03_sap_data/repositories/app_store.py) |  |
| F0388 | `Store.decision_stats` | method | used | [backend/app/store.py:409](../../../backend/app/store.py#L409) | [annotated](../../03_sap_data/repositories/app_store.py) | Acceptance and override (rejection) rates with the reasons experts gave. |
| F0389 | `Store.counts` | method | used | [backend/app/store.py:428](../../../backend/app/store.py#L428) | [annotated](../../03_sap_data/repositories/app_store.py) | Recommendation counts by status; optionally only for one SAP snapshot (one custo |
| F0390 | `TenantContext` | class | used | [backend/app/tenants.py:27](../../../backend/app/tenants.py#L27) | [annotated](../../03_sap_data/repositories/app_tenants.py) |  |
| F0391 | `TenantRegistry` | class | used | [backend/app/tenants.py:40](../../../backend/app/tenants.py#L40) | [annotated](../../03_sap_data/repositories/app_tenants.py) |  |
| F0392 | `TenantRegistry.__init__` | method | used (framework) | [backend/app/tenants.py:41](../../../backend/app/tenants.py#L41) | [annotated](../../03_sap_data/repositories/app_tenants.py) |  |
| F2039 | `TenantRegistry._build` | method | used | [backend/app/tenants.py:60](../../../backend/app/tenants.py#L60) | [annotated](../../03_sap_data/repositories/app_tenants.py) |  |
| F0393 | `TenantRegistry.get` | method | used | [backend/app/tenants.py:68](../../../backend/app/tenants.py#L68) | [annotated](../../03_sap_data/repositories/app_tenants.py) |  |
| F2040 | `TenantRegistry.use_snapshot` | method | used (framework) | [backend/app/tenants.py:77](../../../backend/app/tenants.py#L77) | [annotated](../../03_sap_data/repositories/app_tenants.py) | Switch one customer to another validated snapshot file (None = its built-in snap |
| F0394 | `TenantRegistry.catalogue` | method | used | [backend/app/tenants.py:88](../../../backend/app/tenants.py#L88) | [annotated](../../03_sap_data/repositories/app_tenants.py) |  |
| F0395 | `TenantRegistry.activate` | method | used | [backend/app/tenants.py:94](../../../backend/app/tenants.py#L94) | [annotated](../../03_sap_data/repositories/app_tenants.py) |  |
| F0396 | `TenantRegistry.deactivate` | method | used | [backend/app/tenants.py:98](../../../backend/app/tenants.py#L98) | [annotated](../../03_sap_data/repositories/app_tenants.py) |  |
| F0397 | `TenantRegistry.current_id` | method | used | [backend/app/tenants.py:102](../../../backend/app/tenants.py#L102) | [annotated](../../03_sap_data/repositories/app_tenants.py) |  |
| F0398 | `TenantProxy` | class | used | [backend/app/tenants.py:107](../../../backend/app/tenants.py#L107) | [annotated](../../03_sap_data/repositories/app_tenants.py) | Attribute access is forwarded to the active tenant's object (sap / engine / insi |
| F0399 | `TenantProxy.__init__` | method | used (framework) | [backend/app/tenants.py:110](../../../backend/app/tenants.py#L110) | [annotated](../../03_sap_data/repositories/app_tenants.py) |  |
| F0400 | `TenantProxy.__getattr__` | method | used (framework) | [backend/app/tenants.py:114](../../../backend/app/tenants.py#L114) | [annotated](../../03_sap_data/repositories/app_tenants.py) |  |
