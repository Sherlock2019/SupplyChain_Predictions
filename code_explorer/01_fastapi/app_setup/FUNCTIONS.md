# 01_fastapi/app_setup (generated)

Modules: `backend/app/config.py`, `backend/app/observability.py`, `backend/scinsight/settings.py`

| ID | Function / class | Kind | Status | Original | Annotated copy | Summary |
|---|---|---|---|---|---|---|
| F0001 | `Settings` | pydantic_model | used | [backend/app/config.py:11](../../../backend/app/config.py#L11) | [annotated](../../01_fastapi/app_setup/app_config.py) |  |
| F0002 | `Settings.parse_keys` | method | used (framework) | [backend/app/config.py:87](../../../backend/app/config.py#L87) | [annotated](../../01_fastapi/app_setup/app_config.py) |  |
| F0003 | `Settings.assistants` | method | used (framework) | [backend/app/config.py:96](../../../backend/app/config.py#L96) | [annotated](../../01_fastapi/app_setup/app_config.py) |  |
| F0004 | `Settings.managers` | method | used (framework) | [backend/app/config.py:100](../../../backend/app/config.py#L100) | [annotated](../../01_fastapi/app_setup/app_config.py) |  |
| F0005 | `Settings.tenants_for` | method | used | [backend/app/config.py:104](../../../backend/app/config.py#L104) | [annotated](../../01_fastapi/app_setup/app_config.py) | Tenants an identity may use; None = unrestricted. |
| F0006 | `Settings.llm_enabled` | method | used (framework) | [backend/app/config.py:113](../../../backend/app/config.py#L113) | [annotated](../../01_fastapi/app_setup/app_config.py) |  |
| F0007 | `Settings.langfuse_enabled` | method | used (framework) | [backend/app/config.py:117](../../../backend/app/config.py#L117) | [annotated](../../01_fastapi/app_setup/app_config.py) |  |
| F0008 | `get_settings` | function | used | [backend/app/config.py:122](../../../backend/app/config.py#L122) | [annotated](../../01_fastapi/app_setup/app_config.py) |  |
| F0009 | `_langfuse_client` | function | used | [backend/app/observability.py:22](../../../backend/app/observability.py#L22) | [annotated](../../01_fastapi/app_setup/app_observability.py) |  |
| F0010 | `langfuse_callbacks` | function | used | [backend/app/observability.py:41](../../../backend/app/observability.py#L41) | [annotated](../../01_fastapi/app_setup/app_observability.py) | LangChain callback handlers for one run; empty when Langfuse is not configured. |
| F0011 | `run_config` | function | used | [backend/app/observability.py:51](../../../backend/app/observability.py#L51) | [annotated](../../01_fastapi/app_setup/app_observability.py) |  |
| F0012 | `flush` | function | used | [backend/app/observability.py:59](../../../backend/app/observability.py#L59) | [annotated](../../01_fastapi/app_setup/app_observability.py) |  |
| F0013 | `SciSettings` | pydantic_model | used | [backend/scinsight/settings.py:13](../../../backend/scinsight/settings.py#L13) | [annotated](../../01_fastapi/app_setup/scinsight_settings.py) |  |
| F0014 | `SciSettings.user_keys` | method | used | [backend/scinsight/settings.py:52](../../../backend/scinsight/settings.py#L52) | [annotated](../../01_fastapi/app_setup/scinsight_settings.py) |  |
| F0015 | `SciSettings.missing_keys` | method | used | [backend/scinsight/settings.py:55](../../../backend/scinsight/settings.py#L55) | [annotated](../../01_fastapi/app_setup/scinsight_settings.py) |  |
