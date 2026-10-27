# 01_fastapi/pydantic_models (generated)

Modules: `backend/app/schemas.py`, `backend/scinsight/schemas.py`

| ID | Function / class | Kind | Status | Original | Annotated copy | Summary |
|---|---|---|---|---|---|---|
| F0147 | `StrictModel` | pydantic_model | used (framework) | [backend/app/schemas.py:11](../../../backend/app/schemas.py#L11) | [annotated](../../01_fastapi/pydantic_models/app_schemas.py) |  |
| F0148 | `FactoryReadinessRequest` | pydantic_model | used | [backend/app/schemas.py:15](../../../backend/app/schemas.py#L15) | [annotated](../../01_fastapi/pydantic_models/app_schemas.py) |  |
| F0149 | `StockBalanceRequest` | pydantic_model | used | [backend/app/schemas.py:22](../../../backend/app/schemas.py#L22) | [annotated](../../01_fastapi/pydantic_models/app_schemas.py) |  |
| F0150 | `ForecastRequest` | pydantic_model | used | [backend/app/schemas.py:28](../../../backend/app/schemas.py#L28) | [annotated](../../01_fastapi/pydantic_models/app_schemas.py) |  |
| F0151 | `WhatIfRequest` | pydantic_model | used | [backend/app/schemas.py:34](../../../backend/app/schemas.py#L34) | [annotated](../../01_fastapi/pydantic_models/app_schemas.py) |  |
| F0152 | `SupplierRiskRequest` | pydantic_model | used | [backend/app/schemas.py:41](../../../backend/app/schemas.py#L41) | [annotated](../../01_fastapi/pydantic_models/app_schemas.py) |  |
| F0153 | `QualityRequest` | pydantic_model | used | [backend/app/schemas.py:45](../../../backend/app/schemas.py#L45) | [annotated](../../01_fastapi/pydantic_models/app_schemas.py) |  |
| F0154 | `LogisticsRequest` | pydantic_model | used | [backend/app/schemas.py:50](../../../backend/app/schemas.py#L50) | [annotated](../../01_fastapi/pydantic_models/app_schemas.py) |  |
| F0155 | `SalesOrderRequest` | pydantic_model | used | [backend/app/schemas.py:55](../../../backend/app/schemas.py#L55) | [annotated](../../01_fastapi/pydantic_models/app_schemas.py) |  |
| F0156 | `StocktakeRequest` | pydantic_model | used | [backend/app/schemas.py:59](../../../backend/app/schemas.py#L59) | [annotated](../../01_fastapi/pydantic_models/app_schemas.py) |  |
| F0157 | `WatchRequest` | pydantic_model | used | [backend/app/schemas.py:63](../../../backend/app/schemas.py#L63) | [annotated](../../01_fastapi/pydantic_models/app_schemas.py) |  |
| F0158 | `RagQuery` | pydantic_model | used | [backend/app/schemas.py:70](../../../backend/app/schemas.py#L70) | [annotated](../../01_fastapi/pydantic_models/app_schemas.py) |  |
| F0159 | `RagDocument` | pydantic_model | used | [backend/app/schemas.py:76](../../../backend/app/schemas.py#L76) | [annotated](../../01_fastapi/pydantic_models/app_schemas.py) |  |
| F0160 | `RecommendationRequest` | pydantic_model | used | [backend/app/schemas.py:83](../../../backend/app/schemas.py#L83) | [annotated](../../01_fastapi/pydantic_models/app_schemas.py) |  |
| F0161 | `RecommendationFromTextRequest` | pydantic_model | used | [backend/app/schemas.py:89](../../../backend/app/schemas.py#L89) | [annotated](../../01_fastapi/pydantic_models/app_schemas.py) | Agent hand-off (Flowise HumanInput 'proceed'): the gateway, not the LLM, picks t |
| F0162 | `DecisionRequest` | pydantic_model | used | [backend/app/schemas.py:102](../../../backend/app/schemas.py#L102) | [annotated](../../01_fastapi/pydantic_models/app_schemas.py) |  |
| F0163 | `ConsentRequest` | pydantic_model | used | [backend/app/schemas.py:110](../../../backend/app/schemas.py#L110) | [annotated](../../01_fastapi/pydantic_models/app_schemas.py) |  |
| F0164 | `ChatRequest` | pydantic_model | used | [backend/app/schemas.py:114](../../../backend/app/schemas.py#L114) | [annotated](../../01_fastapi/pydantic_models/app_schemas.py) |  |
| F0165 | `OutcomeRequest` | pydantic_model | used | [backend/app/schemas.py:120](../../../backend/app/schemas.py#L120) | [annotated](../../01_fastapi/pydantic_models/app_schemas.py) | The real result of an executed recommendation, observed in SAP (approval alone i |
| F0166 | `BusinessWorkflowRequest` | pydantic_model | used | [backend/app/schemas.py:129](../../../backend/app/schemas.py#L129) | [annotated](../../01_fastapi/pydantic_models/app_schemas.py) |  |
| F0167 | `ResumeRequest` | pydantic_model | used | [backend/app/schemas.py:143](../../../backend/app/schemas.py#L143) | [annotated](../../01_fastapi/pydantic_models/app_schemas.py) |  |
| F0168 | `EmbeddingsRequest` | pydantic_model | used | [backend/app/schemas.py:148](../../../backend/app/schemas.py#L148) | [annotated](../../01_fastapi/pydantic_models/app_schemas.py) | OpenAI-compatible embeddings request (extra fields such as `user` are ignored, a |
| F0169 | `EmbeddingsRequest._limits` | method | used (framework) | [backend/app/schemas.py:155](../../../backend/app/schemas.py#L155) | [annotated](../../01_fastapi/pydantic_models/app_schemas.py) |  |
| F0170 | `SupplierLeadTimeRequest` | pydantic_model | used | [backend/app/schemas.py:163](../../../backend/app/schemas.py#L163) | [annotated](../../01_fastapi/pydantic_models/app_schemas.py) |  |
| F0171 | `ReconcileRequest` | pydantic_model | used | [backend/app/schemas.py:168](../../../backend/app/schemas.py#L168) | [annotated](../../01_fastapi/pydantic_models/app_schemas.py) | What SAP shows actually happened after an executed decision (goods receipt, deli |
| F0172 | `DeepAgentHarness` | pydantic_model | used | [backend/app/schemas.py:182](../../../backend/app/schemas.py#L182) | [annotated](../../01_fastapi/pydantic_models/app_schemas.py) | Harness settings of the Deep Agents supplier-research agent (model, step budget, |
| F0173 | `DeepAgentHarness._unique` | method | used (framework) | [backend/app/schemas.py:204](../../../backend/app/schemas.py#L204) | [annotated](../../01_fastapi/pydantic_models/app_schemas.py) |  |
| F0174 | `SupplierResearchRequest` | pydantic_model | used | [backend/app/schemas.py:211](../../../backend/app/schemas.py#L211) | [annotated](../../01_fastapi/pydantic_models/app_schemas.py) |  |
| F0988 | `CodeUpdateRequest` | pydantic_model | used | [backend/app/schemas.py:218](../../../backend/app/schemas.py#L218) | [annotated](../../01_fastapi/pydantic_models/app_schemas.py) | Replace one backend function or class (UI backend code section; development only |
| F0175 | `FlowisePredictRequest` | pydantic_model | used | [backend/app/schemas.py:225](../../../backend/app/schemas.py#L225) | [annotated](../../01_fastapi/pydantic_models/app_schemas.py) |  |
| F0176 | `FlowisePredictRequest.question_or_resume` | method | used (framework) | [backend/app/schemas.py:231](../../../backend/app/schemas.py#L231) | [annotated](../../01_fastapi/pydantic_models/app_schemas.py) |  |
| F0177 | `Strict` | pydantic_model | used (framework) | [backend/scinsight/schemas.py:12](../../../backend/scinsight/schemas.py#L12) | [annotated](../../01_fastapi/pydantic_models/scinsight_schemas.py) |  |
| F0178 | `ContextRequest` | pydantic_model | used | [backend/scinsight/schemas.py:16](../../../backend/scinsight/schemas.py#L16) | [annotated](../../01_fastapi/pydantic_models/scinsight_schemas.py) |  |
| F0179 | `MaterialReadinessRequest` | pydantic_model | used | [backend/scinsight/schemas.py:20](../../../backend/scinsight/schemas.py#L20) | [annotated](../../01_fastapi/pydantic_models/scinsight_schemas.py) |  |
| F0180 | `MaterialReadinessRequest._one_way` | method | used (framework) | [backend/scinsight/schemas.py:27](../../../backend/scinsight/schemas.py#L27) | [annotated](../../01_fastapi/pydantic_models/scinsight_schemas.py) |  |
| F0181 | `WarehouseBalancingRequest` | pydantic_model | used | [backend/scinsight/schemas.py:37](../../../backend/scinsight/schemas.py#L37) | [annotated](../../01_fastapi/pydantic_models/scinsight_schemas.py) |  |
| F0182 | `ReplenishmentRequest` | pydantic_model | used | [backend/scinsight/schemas.py:42](../../../backend/scinsight/schemas.py#L42) | [annotated](../../01_fastapi/pydantic_models/scinsight_schemas.py) |  |
| F0183 | `DemandForecastRequest` | pydantic_model | used | [backend/scinsight/schemas.py:49](../../../backend/scinsight/schemas.py#L49) | [annotated](../../01_fastapi/pydantic_models/scinsight_schemas.py) |  |
| F0184 | `LeadTimeRequest` | pydantic_model | used | [backend/scinsight/schemas.py:55](../../../backend/scinsight/schemas.py#L55) | [annotated](../../01_fastapi/pydantic_models/scinsight_schemas.py) |  |
| F0185 | `QualityCheckRequest` | pydantic_model | used | [backend/scinsight/schemas.py:61](../../../backend/scinsight/schemas.py#L61) | [annotated](../../01_fastapi/pydantic_models/scinsight_schemas.py) |  |
| F0186 | `RagSearchRequest` | pydantic_model | used | [backend/scinsight/schemas.py:67](../../../backend/scinsight/schemas.py#L67) | [annotated](../../01_fastapi/pydantic_models/scinsight_schemas.py) |  |
| F0187 | `DecisionCreateRequest` | pydantic_model | used | [backend/scinsight/schemas.py:72](../../../backend/scinsight/schemas.py#L72) | [annotated](../../01_fastapi/pydantic_models/scinsight_schemas.py) |  |
| F0188 | `ReviewRequest` | pydantic_model | used | [backend/scinsight/schemas.py:79](../../../backend/scinsight/schemas.py#L79) | [annotated](../../01_fastapi/pydantic_models/scinsight_schemas.py) |  |
| F0189 | `SapExecutionRequest` | pydantic_model | used | [backend/scinsight/schemas.py:85](../../../backend/scinsight/schemas.py#L85) | [annotated](../../01_fastapi/pydantic_models/scinsight_schemas.py) |  |
| F0190 | `ReconcileRequest` | pydantic_model | used | [backend/scinsight/schemas.py:91](../../../backend/scinsight/schemas.py#L91) | [annotated](../../01_fastapi/pydantic_models/scinsight_schemas.py) |  |
| F0191 | `RetrainingRequest` | pydantic_model | used | [backend/scinsight/schemas.py:95](../../../backend/scinsight/schemas.py#L95) | [annotated](../../01_fastapi/pydantic_models/scinsight_schemas.py) |  |
