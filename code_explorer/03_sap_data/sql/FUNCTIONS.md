# 03_sap_data/sql (generated)

Modules: `backend/scinsight/db.py`

| ID | Function / class | Kind | Status | Original | Annotated copy | Summary |
|---|---|---|---|---|---|---|
| F0416 | `now_iso` | function | used | [backend/scinsight/db.py:18](../../../backend/scinsight/db.py#L18) | [annotated](../../03_sap_data/sql/scinsight_db.py) |  |
| F0417 | `ensure_postgres_database` | function | used | [backend/scinsight/db.py:22](../../../backend/scinsight/db.py#L22) | [annotated](../../03_sap_data/sql/scinsight_db.py) | Create the target PostgreSQL database if it does not exist (existing Compose vol |
| F0418 | `Database` | class | used | [backend/scinsight/db.py:39](../../../backend/scinsight/db.py#L39) | [annotated](../../03_sap_data/sql/scinsight_db.py) |  |
| F0419 | `Database.__init__` | method | used (framework) | [backend/scinsight/db.py:40](../../../backend/scinsight/db.py#L40) | [annotated](../../03_sap_data/sql/scinsight_db.py) |  |
| F0420 | `Database._sql` | method | used | [backend/scinsight/db.py:61](../../../backend/scinsight/db.py#L61) | [annotated](../../03_sap_data/sql/scinsight_db.py) |  |
| F0421 | `Database.query` | method | used | [backend/scinsight/db.py:64](../../../backend/scinsight/db.py#L64) | [annotated](../../03_sap_data/sql/scinsight_db.py) |  |
| F0422 | `Database.one` | method | used | [backend/scinsight/db.py:71](../../../backend/scinsight/db.py#L71) | [annotated](../../03_sap_data/sql/scinsight_db.py) |  |
| F0423 | `Database.execute` | method | used | [backend/scinsight/db.py:75](../../../backend/scinsight/db.py#L75) | [annotated](../../03_sap_data/sql/scinsight_db.py) |  |
| F0424 | `Database.executemany` | method | used | [backend/scinsight/db.py:82](../../../backend/scinsight/db.py#L82) | [annotated](../../03_sap_data/sql/scinsight_db.py) |  |
| F0425 | `Database.transaction` | method | used | [backend/scinsight/db.py:92](../../../backend/scinsight/db.py#L92) | [annotated](../../03_sap_data/sql/scinsight_db.py) | Run several statements atomically (all or nothing). |
| F0426 | `Database.atomic` | method | used | [backend/scinsight/db.py:104](../../../backend/scinsight/db.py#L104) | [annotated](../../03_sap_data/sql/scinsight_db.py) | Run fn(q) inside one transaction holding an exclusive lock; q(sql, params) retur |
| F0427 | `Database.atomic.q` | nested | used | [backend/scinsight/db.py:114](../../../backend/scinsight/db.py#L114) | [annotated](../../03_sap_data/sql/scinsight_db.py) |  |
| F0428 | `Database._script` | method | used | [backend/scinsight/db.py:119](../../../backend/scinsight/db.py#L119) | [annotated](../../03_sap_data/sql/scinsight_db.py) |  |
| F0429 | `Database.migrate` | method | used | [backend/scinsight/db.py:132](../../../backend/scinsight/db.py#L132) | [annotated](../../03_sap_data/sql/scinsight_db.py) |  |
