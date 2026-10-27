# 06_testing/other (generated)

Modules: `backend/app/code_editor.py`, `backend/app/erp/checks.py`, `backend/app/erp/connectors.py`, `backend/app/erp/emulator.py`, `backend/app/erp/mapping.py`, `backend/app/erp/routes.py`, `backend/app/erp/service.py`, `backend/scinsight/rag_tuning/api.py`, `backend/scinsight/rag_tuning/chunking.py`, `backend/scinsight/rag_tuning/config.py`, `backend/scinsight/rag_tuning/documents.py`, `backend/scinsight/rag_tuning/embeddings.py`, `backend/scinsight/rag_tuning/evaluation.py`, `backend/scinsight/rag_tuning/flowise_adapter.py`, `backend/scinsight/rag_tuning/indexing.py`, `backend/scinsight/rag_tuning/publishing.py`, `backend/scinsight/rag_tuning/registry.py`, `backend/scinsight/rag_tuning/retrieval.py`, `flowise/code_explorer/deploy_code_map.py`, `scripts/rag_tuning.py`, `templates/backend/fastapi_app.py`, `templates/backend/fastapi_router.py`, `templates/backend/langgraph_graph.py`, `templates/backend/mcp_server.py`

| ID | Function / class | Kind | Status | Original | Annotated copy | Summary |
|---|---|---|---|---|---|---|
| F1784 | `_defs` | function | used (framework) | [backend/app/code_editor.py:42](../../../backend/app/code_editor.py#L42) | — | qualname -> def/class node, including methods and nested functions. |
| F1785 | `_defs.walk` | nested | used (framework) | [backend/app/code_editor.py:46](../../../backend/app/code_editor.py#L46) | — |  |
| F1786 | `_span` | function | used (framework) | [backend/app/code_editor.py:57](../../../backend/app/code_editor.py#L57) | — |  |
| F1787 | `CodeEditor` | class | used | [backend/app/code_editor.py:61](../../../backend/app/code_editor.py#L61) | — |  |
| F1788 | `CodeEditor.__init__` | method | used (framework) | [backend/app/code_editor.py:62](../../../backend/app/code_editor.py#L62) | — |  |
| F1789 | `CodeEditor._registry` | method | used (framework) | [backend/app/code_editor.py:69](../../../backend/app/code_editor.py#L69) | — |  |
| F1790 | `CodeEditor._files` | method | used | [backend/app/code_editor.py:77](../../../backend/app/code_editor.py#L77) | — |  |
| F1800 | `CodeEditor._apps_of` | method | used | [backend/app/code_editor.py:80](../../../backend/app/code_editor.py#L80) | — | file -> ids of the apps that load it (transitive backend imports from each app's |
| F1952 | `CodeEditor.files` | method | used | [backend/app/code_editor.py:107](../../../backend/app/code_editor.py#L107) | — | Every backend file with the apps that load it; the page shows a file's full sour |
| F1956 | `CodeEditor.template` | method | used | [backend/app/code_editor.py:124](../../../backend/app/code_editor.py#L124) | — | One starter template by file name (only the names the apps list; no path from th |
| F1953 | `CodeEditor.file` | method | used | [backend/app/code_editor.py:136](../../../backend/app/code_editor.py#L136) | — |  |
| F1791 | `CodeEditor.list` | method | used (framework) | [backend/app/code_editor.py:145](../../../backend/app/code_editor.py#L145) | — |  |
| F1792 | `CodeEditor._locate` | method | used (framework) | [backend/app/code_editor.py:172](../../../backend/app/code_editor.py#L172) | — |  |
| F1793 | `CodeEditor.get` | method | used (framework) | [backend/app/code_editor.py:185](../../../backend/app/code_editor.py#L185) | — |  |
| F1794 | `CodeEditor.update` | method | used (framework) | [backend/app/code_editor.py:215](../../../backend/app/code_editor.py#L215) | — |  |
| F2041 | `_r` | function | used | [backend/app/erp/checks.py:25](../../../backend/app/erp/checks.py#L25) | — |  |
| F2042 | `_guard` | function | used | [backend/app/erp/checks.py:29](../../../backend/app/erp/checks.py#L29) | — |  |
| F2043 | `_analyses_since` | function | used | [backend/app/erp/checks.py:36](../../../backend/app/erp/checks.py#L36) | — |  |
| F2044 | `validate_integrations` | function | used | [backend/app/erp/checks.py:40](../../../backend/app/erp/checks.py#L40) | — |  |
| F2045 | `validate_integrations.adapter` | nested | used | [backend/app/erp/checks.py:48](../../../backend/app/erp/checks.py#L48) | — |  |
| F2046 | `validate_integrations.engine` | nested | used | [backend/app/erp/checks.py:59](../../../backend/app/erp/checks.py#L59) | — |  |
| F2047 | `validate_integrations.flowise` | nested | used | [backend/app/erp/checks.py:69](../../../backend/app/erp/checks.py#L69) | — |  |
| F2048 | `validate_integrations.langgraph` | nested | used | [backend/app/erp/checks.py:107](../../../backend/app/erp/checks.py#L107) | — |  |
| F2049 | `validate_integrations.deep_agents` | nested | used | [backend/app/erp/checks.py:131](../../../backend/app/erp/checks.py#L131) | — |  |
| F2050 | `validate_integrations.rag` | nested | used | [backend/app/erp/checks.py:139](../../../backend/app/erp/checks.py#L139) | — |  |
| F2051 | `validate_integrations.dashboards` | nested | used | [backend/app/erp/checks.py:144](../../../backend/app/erp/checks.py#L144) | — |  |
| F2052 | `validate_integrations.outcomes` | nested | used | [backend/app/erp/checks.py:151](../../../backend/app/erp/checks.py#L151) | — |  |
| F2053 | `validate_integrations.audit` | nested | used | [backend/app/erp/checks.py:157](../../../backend/app/erp/checks.py#L157) | — |  |
| F2054 | `validate_integrations.scinsight` | nested | used | [backend/app/erp/checks.py:162](../../../backend/app/erp/checks.py#L162) | — |  |
| F2055 | `_question` | function | used | [backend/app/erp/checks.py:174](../../../backend/app/erp/checks.py#L174) | — |  |
| F2056 | `save_check` | function | used | [backend/app/erp/checks.py:181](../../../backend/app/erp/checks.py#L181) | — |  |
| F2057 | `last_check` | function | used | [backend/app/erp/checks.py:186](../../../backend/app/erp/checks.py#L186) | — |  |
| F2058 | `ErpError` | class | used | [backend/app/erp/connectors.py:39](../../../backend/app/erp/connectors.py#L39) | — | Safe-to-show error (no secrets, no stack). |
| F2059 | `sanitize` | function | used (framework) | [backend/app/erp/connectors.py:43](../../../backend/app/erp/connectors.py#L43) | — |  |
| F2060 | `check_destination` | function | used | [backend/app/erp/connectors.py:50](../../../backend/app/erp/connectors.py#L50) | — | SSRF guard: scheme, cloud-metadata and link-local addresses, production allow-li |
| F2061 | `ErpConnector` | class | used | [backend/app/erp/connectors.py:76](../../../backend/app/erp/connectors.py#L76) | — |  |
| F2062 | `ErpConnector.get_capabilities` | method | used (framework) | [backend/app/erp/connectors.py:79](../../../backend/app/erp/connectors.py#L79) | — |  |
| F2063 | `ErpConnector.test_connection` | method | used (framework) | [backend/app/erp/connectors.py:82](../../../backend/app/erp/connectors.py#L82) | — |  |
| F2064 | `ErpConnector.discover_entities` | method | used (framework) | [backend/app/erp/connectors.py:85](../../../backend/app/erp/connectors.py#L85) | — |  |
| F2065 | `ErpConnector.read_entity` | method | used (framework) | [backend/app/erp/connectors.py:88](../../../backend/app/erp/connectors.py#L88) | — |  |
| F2066 | `ErpConnector.validate_mapping` | method | used (framework) | [backend/app/erp/connectors.py:91](../../../backend/app/erp/connectors.py#L91) | — |  |
| F2067 | `ErpConnector.sync_data` | method | used (framework) | [backend/app/erp/connectors.py:94](../../../backend/app/erp/connectors.py#L94) | — |  |
| F2068 | `ErpConnector.get_health` | method | used (framework) | [backend/app/erp/connectors.py:97](../../../backend/app/erp/connectors.py#L97) | — |  |
| F2069 | `MockSapConnector` | class | used | [backend/app/erp/connectors.py:102](../../../backend/app/erp/connectors.py#L102) | — | The customer's existing validated SAP snapshot (data/…json): what SPARC used bef |
| F2070 | `MockSapConnector.__init__` | method | used (framework) | [backend/app/erp/connectors.py:106](../../../backend/app/erp/connectors.py#L106) | — |  |
| F2071 | `MockSapConnector.get_capabilities` | method | used (framework) | [backend/app/erp/connectors.py:109](../../../backend/app/erp/connectors.py#L109) | — |  |
| F2072 | `MockSapConnector.test_connection` | method | used (framework) | [backend/app/erp/connectors.py:112](../../../backend/app/erp/connectors.py#L112) | — |  |
| F2073 | `MockSapConnector.discover_entities` | method | used (framework) | [backend/app/erp/connectors.py:121](../../../backend/app/erp/connectors.py#L121) | — |  |
| F2074 | `MockSapConnector.read_entity` | method | used (framework) | [backend/app/erp/connectors.py:127](../../../backend/app/erp/connectors.py#L127) | — |  |
| F2075 | `MockSapConnector.validate_mapping` | method | used (framework) | [backend/app/erp/connectors.py:134](../../../backend/app/erp/connectors.py#L134) | — |  |
| F2076 | `MockSapConnector.sync_data` | method | used (framework) | [backend/app/erp/connectors.py:137](../../../backend/app/erp/connectors.py#L137) | — |  |
| F2077 | `SapODataConnector` | class | used | [backend/app/erp/connectors.py:143](../../../backend/app/erp/connectors.py#L143) | — | SAP S/4HANA or ECC (SAP Gateway) through OData. Only GET reaches SAP; pages with |
| F2078 | `SapODataConnector.__init__` | method | used (framework) | [backend/app/erp/connectors.py:146](../../../backend/app/erp/connectors.py#L146) | — |  |
| F2079 | `SapODataConnector._auth` | method | used (framework) | [backend/app/erp/connectors.py:151](../../../backend/app/erp/connectors.py#L151) | — |  |
| F2080 | `SapODataConnector._get` | method | used (framework) | [backend/app/erp/connectors.py:168](../../../backend/app/erp/connectors.py#L168) | — |  |
| F2081 | `SapODataConnector._metadata` | method | used (framework) | [backend/app/erp/connectors.py:185](../../../backend/app/erp/connectors.py#L185) | — |  |
| F2082 | `SapODataConnector._services` | method | used (framework) | [backend/app/erp/connectors.py:191](../../../backend/app/erp/connectors.py#L191) | — |  |
| F2083 | `SapODataConnector.get_capabilities` | method | used (framework) | [backend/app/erp/connectors.py:195](../../../backend/app/erp/connectors.py#L195) | — |  |
| F2084 | `SapODataConnector.test_connection` | method | used (framework) | [backend/app/erp/connectors.py:198](../../../backend/app/erp/connectors.py#L198) | — | Authorized GET of $metadata for every service the mapping uses (or the first one |
| F2085 | `SapODataConnector.discover_entities` | method | used (framework) | [backend/app/erp/connectors.py:219](../../../backend/app/erp/connectors.py#L219) | — |  |
| F2086 | `SapODataConnector.validate_mapping` | method | used (framework) | [backend/app/erp/connectors.py:229](../../../backend/app/erp/connectors.py#L229) | — |  |
| F2087 | `SapODataConnector._rows` | method | used (framework) | [backend/app/erp/connectors.py:239](../../../backend/app/erp/connectors.py#L239) | — |  |
| F2088 | `SapODataConnector.read_entity` | method | used (framework) | [backend/app/erp/connectors.py:251](../../../backend/app/erp/connectors.py#L251) | — |  |
| F2089 | `SapODataConnector.sync_data` | method | used (framework) | [backend/app/erp/connectors.py:260](../../../backend/app/erp/connectors.py#L260) | — | Full read of every enabled section into a copy of the current snapshot. Sections |
| F2090 | `parse_metadata` | function | used (framework) | [backend/app/erp/connectors.py:298](../../../backend/app/erp/connectors.py#L298) | — | {entity set: property and navigation-property names} from an OData V2/V4 $metada |
| F2091 | `http_hint` | function | used (framework) | [backend/app/erp/connectors.py:309](../../../backend/app/erp/connectors.py#L309) | — |  |
| F2092 | `_odate` | function | used | [backend/app/erp/emulator.py:23](../../../backend/app/erp/emulator.py#L23) | — |  |
| F2093 | `_num` | function | used | [backend/app/erp/emulator.py:30](../../../backend/app/erp/emulator.py#L30) | — |  |
| F2094 | `build_entities` | function | used | [backend/app/erp/emulator.py:34](../../../backend/app/erp/emulator.py#L34) | — | {service: {entity set: rows}} in SAP shape, from a SPARC snapshot. |
| F2095 | `build_entities.d` | nested | used | [backend/app/erp/emulator.py:38](../../../backend/app/erp/emulator.py#L38) | — |  |
| F2096 | `metadata_xml` | function | used | [backend/app/erp/emulator.py:78](../../../backend/app/erp/emulator.py#L78) | — |  |
| F2097 | `respond` | function | used | [backend/app/erp/emulator.py:90](../../../backend/app/erp/emulator.py#L90) | — | (status, body, content type) for one request; shared by the FastAPI route and th |
| F2098 | `router` | function | used | [backend/app/erp/emulator.py:122](../../../backend/app/erp/emulator.py#L122) | — |  |
| F2099 | `router.odata` | route | used | [backend/app/erp/emulator.py:126](../../../backend/app/erp/emulator.py#L126) | — |  |
| F2100 | `SectionMapping` | pydantic_model | used | [backend/app/erp/mapping.py:51](../../../backend/app/erp/mapping.py#L51) | — |  |
| F2101 | `default_mapping` | function | used (framework) | [backend/app/erp/mapping.py:94](../../../backend/app/erp/mapping.py#L94) | — |  |
| F2102 | `_get` | function | used (framework) | [backend/app/erp/mapping.py:101](../../../backend/app/erp/mapping.py#L101) | — |  |
| F2103 | `resolve` | function | used (framework) | [backend/app/erp/mapping.py:113](../../../backend/app/erp/mapping.py#L113) | — |  |
| F2104 | `convert` | function | used (framework) | [backend/app/erp/mapping.py:124](../../../backend/app/erp/mapping.py#L124) | — |  |
| F2105 | `transform` | function | used (framework) | [backend/app/erp/mapping.py:138](../../../backend/app/erp/mapping.py#L138) | — | Map SAP rows to SPARC rows; rows missing a required field are rejected with a re |
| F2106 | `validate_mapping` | function | used | [backend/app/erp/mapping.py:163](../../../backend/app/erp/mapping.py#L163) | — | Problems that block activation. metadata = {entity set: properties + navigation  |
| F2107 | `ActivateIn` | pydantic_model | used | [backend/app/erp/routes.py:19](../../../backend/app/erp/routes.py#L19) | — |  |
| F2108 | `PreviewIn` | pydantic_model | used | [backend/app/erp/routes.py:24](../../../backend/app/erp/routes.py#L24) | — |  |
| F2109 | `SyncIn` | pydantic_model | used | [backend/app/erp/routes.py:30](../../../backend/app/erp/routes.py#L30) | — |  |
| F2110 | `ValidateAllIn` | pydantic_model | used | [backend/app/erp/routes.py:35](../../../backend/app/erp/routes.py#L35) | — |  |
| F2111 | `register` | function | used | [backend/app/erp/routes.py:40](../../../backend/app/erp/routes.py#L40) | — |  |
| F2112 | `register.tenant` | nested | used | [backend/app/erp/routes.py:43](../../../backend/app/erp/routes.py#L43) | — |  |
| F2113 | `register.run` | nested | used | [backend/app/erp/routes.py:46](../../../backend/app/erp/routes.py#L46) | — |  |
| F2114 | `register.log` | nested | used | [backend/app/erp/routes.py:54](../../../backend/app/erp/routes.py#L54) | — |  |
| F2115 | `register.providers` | route | used | [backend/app/erp/routes.py:57](../../../backend/app/erp/routes.py#L57) | — |  |
| F2116 | `register.connections` | route | used | [backend/app/erp/routes.py:62](../../../backend/app/erp/routes.py#L62) | — |  |
| F2117 | `register.create` | route | used | [backend/app/erp/routes.py:68](../../../backend/app/erp/routes.py#L68) | — |  |
| F2118 | `register.get` | route | used | [backend/app/erp/routes.py:74](../../../backend/app/erp/routes.py#L74) | — |  |
| F2119 | `register.patch` | route | used | [backend/app/erp/routes.py:79](../../../backend/app/erp/routes.py#L79) | — |  |
| F2120 | `register.test` | route | used | [backend/app/erp/routes.py:89](../../../backend/app/erp/routes.py#L89) | — |  |
| F2121 | `register.health` | route | used | [backend/app/erp/routes.py:95](../../../backend/app/erp/routes.py#L95) | — |  |
| F2122 | `register.entities` | route | used | [backend/app/erp/routes.py:100](../../../backend/app/erp/routes.py#L100) | — |  |
| F2123 | `register.mappings` | route | used | [backend/app/erp/routes.py:106](../../../backend/app/erp/routes.py#L106) | — |  |
| F2124 | `register.put_mappings` | route | used | [backend/app/erp/routes.py:111](../../../backend/app/erp/routes.py#L111) | — |  |
| F2125 | `register.validate` | route | used | [backend/app/erp/routes.py:117](../../../backend/app/erp/routes.py#L117) | — |  |
| F2126 | `register.preview` | route | used | [backend/app/erp/routes.py:123](../../../backend/app/erp/routes.py#L123) | — |  |
| F2127 | `register.sync` | route | used | [backend/app/erp/routes.py:129](../../../backend/app/erp/routes.py#L129) | — |  |
| F2128 | `register.sync_history` | route | used | [backend/app/erp/routes.py:137](../../../backend/app/erp/routes.py#L137) | — |  |
| F2129 | `register.activate` | route | used | [backend/app/erp/routes.py:142](../../../backend/app/erp/routes.py#L142) | — |  |
| F2130 | `register.rollback` | route | used | [backend/app/erp/routes.py:153](../../../backend/app/erp/routes.py#L153) | — |  |
| F2131 | `register.logs` | route | used | [backend/app/erp/routes.py:160](../../../backend/app/erp/routes.py#L160) | — |  |
| F2132 | `register.activation_history` | route | used | [backend/app/erp/routes.py:165](../../../backend/app/erp/routes.py#L165) | — |  |
| F2133 | `register.integration_status` | route | used | [backend/app/erp/routes.py:170](../../../backend/app/erp/routes.py#L170) | — |  |
| F2134 | `register.validate_all` | route | used | [backend/app/erp/routes.py:175](../../../backend/app/erp/routes.py#L175) | — |  |
| F2135 | `_now` | function | used | [backend/app/erp/service.py:59](../../../backend/app/erp/service.py#L59) | — |  |
| F2136 | `ConnectionIn` | pydantic_model | used | [backend/app/erp/service.py:63](../../../backend/app/erp/service.py#L63) | — | Connection settings. `secret` is write-only (only with secret_ref="stored"); it  |
| F2137 | `MappingIn` | pydantic_model | used | [backend/app/erp/service.py:85](../../../backend/app/erp/service.py#L85) | — |  |
| F2138 | `ErpService` | class | used | [backend/app/erp/service.py:90](../../../backend/app/erp/service.py#L90) | — |  |
| F2139 | `ErpService.__init__` | method | used (framework) | [backend/app/erp/service.py:91](../../../backend/app/erp/service.py#L91) | — |  |
| F2140 | `ErpService._row` | method | used | [backend/app/erp/service.py:103](../../../backend/app/erp/service.py#L103) | — |  |
| F2141 | `ErpService._secret` | method | used | [backend/app/erp/service.py:109](../../../backend/app/erp/service.py#L109) | — | (secret, source). env:NAME reads the variable a secrets manager injects; stored  |
| F2142 | `ErpService.public` | method | used (framework) | [backend/app/erp/service.py:119](../../../backend/app/erp/service.py#L119) | — |  |
| F2143 | `ErpService.list` | method | used (framework) | [backend/app/erp/service.py:126](../../../backend/app/erp/service.py#L126) | — |  |
| F2144 | `ErpService.get` | method | used (framework) | [backend/app/erp/service.py:130](../../../backend/app/erp/service.py#L130) | — |  |
| F2145 | `ErpService._rules` | method | used (framework) | [backend/app/erp/service.py:134](../../../backend/app/erp/service.py#L134) | — |  |
| F2146 | `ErpService._save` | method | used (framework) | [backend/app/erp/service.py:162](../../../backend/app/erp/service.py#L162) | — |  |
| F2147 | `ErpService.create` | method | used (framework) | [backend/app/erp/service.py:192](../../../backend/app/erp/service.py#L192) | — |  |
| F2148 | `ErpService.patch` | method | used (framework) | [backend/app/erp/service.py:195](../../../backend/app/erp/service.py#L195) | — |  |
| F2149 | `ErpService.connector` | method | used | [backend/app/erp/service.py:201](../../../backend/app/erp/service.py#L201) | — |  |
| F2150 | `ErpService.mapping` | method | used | [backend/app/erp/service.py:211](../../../backend/app/erp/service.py#L211) | — |  |
| F2151 | `ErpService.set_mapping` | method | used | [backend/app/erp/service.py:216](../../../backend/app/erp/service.py#L216) | — |  |
| F2152 | `ErpService.test` | method | used (framework) | [backend/app/erp/service.py:231](../../../backend/app/erp/service.py#L231) | — |  |
| F2153 | `ErpService.discover` | method | used | [backend/app/erp/service.py:243](../../../backend/app/erp/service.py#L243) | — |  |
| F2154 | `ErpService.validate` | method | used (framework) | [backend/app/erp/service.py:247](../../../backend/app/erp/service.py#L247) | — |  |
| F2155 | `ErpService.preview` | method | used (framework) | [backend/app/erp/service.py:253](../../../backend/app/erp/service.py#L253) | — |  |
| F2156 | `ErpService.sync` | method | used | [backend/app/erp/service.py:260](../../../backend/app/erp/service.py#L260) | — |  |
| F2157 | `ErpService._smoke` | method | used | [backend/app/erp/service.py:289](../../../backend/app/erp/service.py#L289) | — | The candidate must load and the engine must compute on it before it can ever be  |
| F2158 | `ErpService._write` | method | used | [backend/app/erp/service.py:304](../../../backend/app/erp/service.py#L304) | — |  |
| F2159 | `ErpService.job` | method | used | [backend/app/erp/service.py:310](../../../backend/app/erp/service.py#L310) | — |  |
| F2160 | `ErpService.sync_history` | method | used (framework) | [backend/app/erp/service.py:317](../../../backend/app/erp/service.py#L317) | — |  |
| F2161 | `ErpService.active` | method | used (framework) | [backend/app/erp/service.py:323](../../../backend/app/erp/service.py#L323) | — |  |
| F2162 | `ErpService.activate` | method | used (framework) | [backend/app/erp/service.py:326](../../../backend/app/erp/service.py#L326) | — |  |
| F2163 | `ErpService._swap` | method | used (framework) | [backend/app/erp/service.py:347](../../../backend/app/erp/service.py#L347) | — |  |
| F2164 | `ErpService._record` | method | used (framework) | [backend/app/erp/service.py:351](../../../backend/app/erp/service.py#L351) | — |  |
| F2165 | `ErpService.rollback` | method | used (framework) | [backend/app/erp/service.py:362](../../../backend/app/erp/service.py#L362) | — | Back to the snapshot that was active before the current one (or the customer's b |
| F2166 | `ErpService.activation_history` | method | used (framework) | [backend/app/erp/service.py:376](../../../backend/app/erp/service.py#L376) | — |  |
| F2167 | `ErpService.restore` | method | used (framework) | [backend/app/erp/service.py:379](../../../backend/app/erp/service.py#L379) | — | At startup: put every customer back on its last activated snapshot (the database |
| F2168 | `ErpService.health` | method | used (framework) | [backend/app/erp/service.py:392](../../../backend/app/erp/service.py#L392) | — |  |
| F2169 | `ErpService.logs` | method | used (framework) | [backend/app/erp/service.py:410](../../../backend/app/erp/service.py#L410) | — |  |
| F2170 | `ErpService.run_scheduled` | method | used | [backend/app/erp/service.py:415](../../../backend/app/erp/service.py#L415) | — |  |
| F2171 | `ErpService.start_scheduler` | method | used | [backend/app/erp/service.py:430](../../../backend/app/erp/service.py#L430) | — |  |
| F2172 | `ErpService.start_scheduler.loop` | nested | used | [backend/app/erp/service.py:431](../../../backend/app/erp/service.py#L431) | — |  |
| F2173 | `options` | function | used | [backend/app/erp/service.py:441](../../../backend/app/erp/service.py#L441) | — |  |
| F1810 | `DraftRequest` | pydantic_model | used | [backend/scinsight/rag_tuning/api.py:38](../../../backend/scinsight/rag_tuning/api.py#L38) | — |  |
| F1811 | `PreviewRequest` | pydantic_model | used | [backend/scinsight/rag_tuning/api.py:44](../../../backend/scinsight/rag_tuning/api.py#L44) | — |  |
| F1812 | `RetrieveRequest` | pydantic_model | used | [backend/scinsight/rag_tuning/api.py:50](../../../backend/scinsight/rag_tuning/api.py#L50) | — |  |
| F1813 | `ModelTestRequest` | pydantic_model | used | [backend/scinsight/rag_tuning/api.py:57](../../../backend/scinsight/rag_tuning/api.py#L57) | — |  |
| F1814 | `ConfigRef` | pydantic_model | used | [backend/scinsight/rag_tuning/api.py:61](../../../backend/scinsight/rag_tuning/api.py#L61) | — |  |
| F1815 | `EvaluateRequest` | pydantic_model | used | [backend/scinsight/rag_tuning/api.py:66](../../../backend/scinsight/rag_tuning/api.py#L66) | — |  |
| F1816 | `GridRequest` | pydantic_model | used | [backend/scinsight/rag_tuning/api.py:72](../../../backend/scinsight/rag_tuning/api.py#L72) | — |  |
| F1817 | `_llm_answer_fn` | function | used | [backend/scinsight/rag_tuning/api.py:80](../../../backend/scinsight/rag_tuning/api.py#L80) | — | OpenAI-compatible chat call (the same Qwen endpoint as the agents). Returns (ans |
| F1818 | `_llm_answer_fn.answer` | nested | used | [backend/scinsight/rag_tuning/api.py:85](../../../backend/scinsight/rag_tuning/api.py#L85) | — |  |
| F1819 | `register` | function | used | [backend/scinsight/rag_tuning/api.py:99](../../../backend/scinsight/rag_tuning/api.py#L99) | — |  |
| F1820 | `register.admin` | nested | used | [backend/scinsight/rag_tuning/api.py:106](../../../backend/scinsight/rag_tuning/api.py#L106) | — |  |
| F1821 | `register.audit` | nested | used | [backend/scinsight/rag_tuning/api.py:110](../../../backend/scinsight/rag_tuning/api.py#L110) | — |  |
| F1822 | `register.cfg_of` | nested | used | [backend/scinsight/rag_tuning/api.py:113](../../../backend/scinsight/rag_tuning/api.py#L113) | — |  |
| F1823 | `register.job` | nested | used | [backend/scinsight/rag_tuning/api.py:120](../../../backend/scinsight/rag_tuning/api.py#L120) | — |  |
| F1824 | `register.get_config` | route | used | [backend/scinsight/rag_tuning/api.py:124](../../../backend/scinsight/rag_tuning/api.py#L124) | — |  |
| F1825 | `register.save_draft` | route | used | [backend/scinsight/rag_tuning/api.py:138](../../../backend/scinsight/rag_tuning/api.py#L138) | — |  |
| F1826 | `register.history` | route | used | [backend/scinsight/rag_tuning/api.py:144](../../../backend/scinsight/rag_tuning/api.py#L144) | — |  |
| F1827 | `register.config_diff` | route | used | [backend/scinsight/rag_tuning/api.py:148](../../../backend/scinsight/rag_tuning/api.py#L148) | — |  |
| F1828 | `register.list_documents` | route | used | [backend/scinsight/rag_tuning/api.py:154](../../../backend/scinsight/rag_tuning/api.py#L154) | — |  |
| F1829 | `register.validate_metadata` | route | used | [backend/scinsight/rag_tuning/api.py:158](../../../backend/scinsight/rag_tuning/api.py#L158) | — |  |
| F1830 | `register.document_source` | route | used | [backend/scinsight/rag_tuning/api.py:166](../../../backend/scinsight/rag_tuning/api.py#L166) | — |  |
| F1831 | `register.chunk_preview` | route | used | [backend/scinsight/rag_tuning/api.py:174](../../../backend/scinsight/rag_tuning/api.py#L174) | — |  |
| F1832 | `register.embedding_models` | route | used | [backend/scinsight/rag_tuning/api.py:187](../../../backend/scinsight/rag_tuning/api.py#L187) | — |  |
| F1833 | `register.test_model` | route | used | [backend/scinsight/rag_tuning/api.py:193](../../../backend/scinsight/rag_tuning/api.py#L193) | — |  |
| F1834 | `register.build_candidate` | route | used | [backend/scinsight/rag_tuning/api.py:202](../../../backend/scinsight/rag_tuning/api.py#L202) | — |  |
| F1835 | `register.get_job` | route | used | [backend/scinsight/rag_tuning/api.py:209](../../../backend/scinsight/rag_tuning/api.py#L209) | — |  |
| F1836 | `register.retrieve_preview` | route | used | [backend/scinsight/rag_tuning/api.py:217](../../../backend/scinsight/rag_tuning/api.py#L217) | — | retrieve_with_config: the live search function with a stored configuration and/o |
| F1837 | `register._benchmark` | nested | used | [backend/scinsight/rag_tuning/api.py:239](../../../backend/scinsight/rag_tuning/api.py#L239) | — |  |
| F1838 | `register.evaluate` | route | used | [backend/scinsight/rag_tuning/api.py:255](../../../backend/scinsight/rag_tuning/api.py#L255) | — |  |
| F1839 | `register.evaluate_grid` | route | used | [backend/scinsight/rag_tuning/api.py:263](../../../backend/scinsight/rag_tuning/api.py#L263) | — | Shows the workload first; runs only when confirm=true (no silent Cartesian produ |
| F1840 | `register.list_experiments` | route | used | [backend/scinsight/rag_tuning/api.py:287](../../../backend/scinsight/rag_tuning/api.py#L287) | — |  |
| F1841 | `register.compare` | route | used | [backend/scinsight/rag_tuning/api.py:291](../../../backend/scinsight/rag_tuning/api.py#L291) | — |  |
| F1842 | `register.get_experiment` | route | used | [backend/scinsight/rag_tuning/api.py:298](../../../backend/scinsight/rag_tuning/api.py#L298) | — |  |
| F1843 | `register.validate` | route | used | [backend/scinsight/rag_tuning/api.py:306](../../../backend/scinsight/rag_tuning/api.py#L306) | — |  |
| F1844 | `register.publish` | route | used | [backend/scinsight/rag_tuning/api.py:311](../../../backend/scinsight/rag_tuning/api.py#L311) | — |  |
| F1845 | `register.rollback` | route | used | [backend/scinsight/rag_tuning/api.py:325](../../../backend/scinsight/rag_tuning/api.py#L325) | — |  |
| F1846 | `register.flowise_status` | route | used | [backend/scinsight/rag_tuning/api.py:340](../../../backend/scinsight/rag_tuning/api.py#L340) | — |  |
| F1847 | `register.metrics` | route | used | [backend/scinsight/rag_tuning/api.py:344](../../../backend/scinsight/rag_tuning/api.py#L344) | — |  |
| F1848 | `_sections` | function | used | [backend/scinsight/rag_tuning/chunking.py:18](../../../backend/scinsight/rag_tuning/chunking.py#L18) | — |  |
| F1849 | `_windows` | function | used | [backend/scinsight/rag_tuning/chunking.py:33](../../../backend/scinsight/rag_tuning/chunking.py#L33) | — |  |
| F1850 | `_clauses` | function | used | [backend/scinsight/rag_tuning/chunking.py:44](../../../backend/scinsight/rag_tuning/chunking.py#L44) | — |  |
| F1851 | `chunk` | function | used | [backend/scinsight/rag_tuning/chunking.py:71](../../../backend/scinsight/rag_tuning/chunking.py#L71) | — | Chunks of one document: [{chunk_index, section, text (as indexed), content (with |
| F1852 | `overlap_chars` | function | used | [backend/scinsight/rag_tuning/chunking.py:89](../../../backend/scinsight/rag_tuning/chunking.py#L89) | — | Characters at the end of `left` repeated at the start of `right` (what the overl |
| F1853 | `preview_document_chunks` | function | used | [backend/scinsight/rag_tuning/chunking.py:97](../../../backend/scinsight/rag_tuning/chunking.py#L97) | — | What the configuration would index for one document (nothing is written). |
| F1854 | `RagTuningConfig` | pydantic_model | used | [backend/scinsight/rag_tuning/config.py:26](../../../backend/scinsight/rag_tuning/config.py#L26) | — | One RAG configuration version. Cold fields define the index; hot fields only cha |
| F1855 | `RagTuningConfig.validate_chunking` | method | used (framework) | [backend/scinsight/rag_tuning/config.py:48](../../../backend/scinsight/rag_tuning/config.py#L48) | — |  |
| F1856 | `baseline_config` | function | used | [backend/scinsight/rag_tuning/config.py:58](../../../backend/scinsight/rag_tuning/config.py#L58) | — | The configuration the service ran with before tuning existed (backend/scinsight/ |
| F1857 | `diff` | function | used | [backend/scinsight/rag_tuning/config.py:63](../../../backend/scinsight/rag_tuning/config.py#L63) | — | Changed settings, split into those that need a rebuild (cold) and those that app |
| F1858 | `index_signature` | function | used | [backend/scinsight/rag_tuning/config.py:70](../../../backend/scinsight/rag_tuning/config.py#L70) | — | The cold settings: two configurations with the same signature can share one inde |
| F1859 | `_front_matter` | function | used | [backend/scinsight/rag_tuning/documents.py:20](../../../backend/scinsight/rag_tuning/documents.py#L20) | — |  |
| F1860 | `inventory` | function | used | [backend/scinsight/rag_tuning/documents.py:25](../../../backend/scinsight/rag_tuning/documents.py#L25) | — | Every source file of the caller's tenant with its metadata, index state and defi |
| F1861 | `validate_document_metadata` | function | used | [backend/scinsight/rag_tuning/documents.py:71](../../../backend/scinsight/rag_tuning/documents.py#L71) | — | Checks on one document: missing fields, scope, validity and source quality (seve |
| F1862 | `_cross_document_checks` | function | used | [backend/scinsight/rag_tuning/documents.py:98](../../../backend/scinsight/rag_tuning/documents.py#L98) | — |  |
| F1863 | `source_text` | function | used | [backend/scinsight/rag_tuning/documents.py:120](../../../backend/scinsight/rag_tuning/documents.py#L120) | — | The source document of the caller's tenant (front matter + body) for preview; ot |
| F1864 | `ModelUnavailable` | class | used | [backend/scinsight/rag_tuning/embeddings.py:30](../../../backend/scinsight/rag_tuning/embeddings.py#L30) | — |  |
| F1865 | `approved` | function | used | [backend/scinsight/rag_tuning/embeddings.py:34](../../../backend/scinsight/rag_tuning/embeddings.py#L34) | — |  |
| F1866 | `_installed` | function | used | [backend/scinsight/rag_tuning/embeddings.py:38](../../../backend/scinsight/rag_tuning/embeddings.py#L38) | — |  |
| F1867 | `list_supported_embedding_models` | function | used | [backend/scinsight/rag_tuning/embeddings.py:47](../../../backend/scinsight/rag_tuning/embeddings.py#L47) | — | The approved list with what is actually known about each model (installed, dimen |
| F1868 | `get_embedder` | function | used | [backend/scinsight/rag_tuning/embeddings.py:56](../../../backend/scinsight/rag_tuning/embeddings.py#L56) | — | Embedder for an approved model. Raises ModelUnavailable instead of substituting  |
| F1869 | `test_model` | function | used | [backend/scinsight/rag_tuning/embeddings.py:80](../../../backend/scinsight/rag_tuning/embeddings.py#L80) | — | Load the model (downloading it if allowed), embed sample texts, check dimensions |
| F1870 | `load_dataset` | function | used | [backend/scinsight/rag_tuning/evaluation.py:29](../../../backend/scinsight/rag_tuning/evaluation.py#L29) | — |  |
| F1871 | `_p95` | function | used | [backend/scinsight/rag_tuning/evaluation.py:35](../../../backend/scinsight/rag_tuning/evaluation.py#L35) | — |  |
| F1872 | `score_case` | function | used | [backend/scinsight/rag_tuning/evaluation.py:42](../../../backend/scinsight/rag_tuning/evaluation.py#L42) | — | Deterministic retrieval scores of one case. |
| F1873 | `score_answer` | function | used | [backend/scinsight/rag_tuning/evaluation.py:64](../../../backend/scinsight/rag_tuning/evaluation.py#L64) | — | Checks of an LLM answer against the retrieved evidence (deterministic; the model |
| F1874 | `run_rag_benchmark` | function | used | [backend/scinsight/rag_tuning/evaluation.py:82](../../../backend/scinsight/rag_tuning/evaluation.py#L82) | — | Every case through KnowledgeBase.search (the function behind /api/v1/rag/search) |
| F1875 | `summarize` | function | used | [backend/scinsight/rag_tuning/evaluation.py:103](../../../backend/scinsight/rag_tuning/evaluation.py#L103) | — |  |
| F1876 | `summarize.mean` | nested | used | [backend/scinsight/rag_tuning/evaluation.py:104](../../../backend/scinsight/rag_tuning/evaluation.py#L104) | — |  |
| F1877 | `compare_experiments` | function | used | [backend/scinsight/rag_tuning/evaluation.py:127](../../../backend/scinsight/rag_tuning/evaluation.py#L127) | — | Side-by-side measured metrics and a recommendation from the acceptance criteria  |
| F1878 | `compare_experiments.check` | nested | used | [backend/scinsight/rag_tuning/evaluation.py:136](../../../backend/scinsight/rag_tuning/evaluation.py#L136) | — |  |
| F1879 | `FlowiseError` | class | used | [backend/scinsight/rag_tuning/flowise_adapter.py:22](../../../backend/scinsight/rag_tuning/flowise_adapter.py#L22) | — |  |
| F1880 | `FlowiseAdapter` | class | used | [backend/scinsight/rag_tuning/flowise_adapter.py:26](../../../backend/scinsight/rag_tuning/flowise_adapter.py#L26) | — |  |
| F1881 | `FlowiseAdapter.__init__` | method | used (framework) | [backend/scinsight/rag_tuning/flowise_adapter.py:27](../../../backend/scinsight/rag_tuning/flowise_adapter.py#L27) | — |  |
| F1882 | `FlowiseAdapter.configured` | method | used (framework) | [backend/scinsight/rag_tuning/flowise_adapter.py:30](../../../backend/scinsight/rag_tuning/flowise_adapter.py#L30) | — |  |
| F1883 | `FlowiseAdapter._call` | method | used | [backend/scinsight/rag_tuning/flowise_adapter.py:34](../../../backend/scinsight/rag_tuning/flowise_adapter.py#L34) | — |  |
| F1884 | `FlowiseAdapter.chatflow` | method | used | [backend/scinsight/rag_tuning/flowise_adapter.py:46](../../../backend/scinsight/rag_tuning/flowise_adapter.py#L46) | — |  |
| F1885 | `FlowiseAdapter._nodes` | method | used (framework) | [backend/scinsight/rag_tuning/flowise_adapter.py:55](../../../backend/scinsight/rag_tuning/flowise_adapter.py#L55) | — |  |
| F1886 | `FlowiseAdapter.status` | method | used (framework) | [backend/scinsight/rag_tuning/flowise_adapter.py:63](../../../backend/scinsight/rag_tuning/flowise_adapter.py#L63) | — | What the live chatflow RAG DB uses right now, and what its table holds. |
| F1887 | `FlowiseAdapter.table_rows` | method | used (framework) | [backend/scinsight/rag_tuning/flowise_adapter.py:83](../../../backend/scinsight/rag_tuning/flowise_adapter.py#L83) | — |  |
| F1888 | `FlowiseAdapter.compatible` | method | used | [backend/scinsight/rag_tuning/flowise_adapter.py:92](../../../backend/scinsight/rag_tuning/flowise_adapter.py#L92) | — | Reasons the chatflow RAG DB cannot follow this configuration (empty = it can). |
| F1889 | `FlowiseAdapter.sync` | method | used (framework) | [backend/scinsight/rag_tuning/flowise_adapter.py:99](../../../backend/scinsight/rag_tuning/flowise_adapter.py#L99) | — | Apply chunk size / overlap / top-k and the version tag to the chatflow, re-index |
| F1890 | `FlowiseAdapter.restore` | method | used (framework) | [backend/scinsight/rag_tuning/flowise_adapter.py:124](../../../backend/scinsight/rag_tuning/flowise_adapter.py#L124) | — |  |
| F1891 | `current_docs_sha` | function | used | [backend/scinsight/rag_tuning/indexing.py:14](../../../backend/scinsight/rag_tuning/indexing.py#L14) | — | doc_id:version -> sha256 of the source files that an index of this tenant must c |
| F1892 | `build_candidate_index` | function | used | [backend/scinsight/rag_tuning/indexing.py:27](../../../backend/scinsight/rag_tuning/indexing.py#L27) | — | Index the tenant's documents with the configuration's cold settings under a new  |
| F1893 | `validate_index` | function | used | [backend/scinsight/rag_tuning/indexing.py:61](../../../backend/scinsight/rag_tuning/indexing.py#L61) | — | Complete, single-model, right dimensions, and built from the current documents ( |
| F1894 | `list_indexes` | function | used | [backend/scinsight/rag_tuning/indexing.py:86](../../../backend/scinsight/rag_tuning/indexing.py#L86) | — |  |
| F1895 | `validate_config` | function | used | [backend/scinsight/rag_tuning/publishing.py:14](../../../backend/scinsight/rag_tuning/publishing.py#L14) | — | Every check a configuration must pass before it can become active. |
| F1896 | `validate_config.check` | nested | used | [backend/scinsight/rag_tuning/publishing.py:21](../../../backend/scinsight/rag_tuning/publishing.py#L21) | — |  |
| F1897 | `_activate` | function | used | [backend/scinsight/rag_tuning/publishing.py:53](../../../backend/scinsight/rag_tuning/publishing.py#L53) | — |  |
| F1898 | `publish_rag_config` | function | used | [backend/scinsight/rag_tuning/publishing.py:78](../../../backend/scinsight/rag_tuning/publishing.py#L78) | — |  |
| F1899 | `rollback_rag_config` | function | used | [backend/scinsight/rag_tuning/publishing.py:87](../../../backend/scinsight/rag_tuning/publishing.py#L87) | — | Re-activate a version that was published before (its index is kept); refused if  |
| F1900 | `_id` | function | used | [backend/scinsight/rag_tuning/registry.py:13](../../../backend/scinsight/rag_tuning/registry.py#L13) | — |  |
| F1901 | `_row` | function | used | [backend/scinsight/rag_tuning/registry.py:17](../../../backend/scinsight/rag_tuning/registry.py#L17) | — |  |
| F1902 | `Registry` | class | used | [backend/scinsight/rag_tuning/registry.py:28](../../../backend/scinsight/rag_tuning/registry.py#L28) | — |  |
| F1903 | `Registry.__init__` | method | used (framework) | [backend/scinsight/rag_tuning/registry.py:29](../../../backend/scinsight/rag_tuning/registry.py#L29) | — |  |
| F1904 | `Registry.ensure_baseline` | method | used | [backend/scinsight/rag_tuning/registry.py:33](../../../backend/scinsight/rag_tuning/registry.py#L33) | — |  |
| F1905 | `Registry.get_active_rag_config` | method | used | [backend/scinsight/rag_tuning/registry.py:41](../../../backend/scinsight/rag_tuning/registry.py#L41) | — |  |
| F1906 | `Registry.get` | method | used | [backend/scinsight/rag_tuning/registry.py:45](../../../backend/scinsight/rag_tuning/registry.py#L45) | — |  |
| F1907 | `Registry.history` | method | used (framework) | [backend/scinsight/rag_tuning/registry.py:51](../../../backend/scinsight/rag_tuning/registry.py#L51) | — |  |
| F1908 | `Registry.save_draft_config` | method | used | [backend/scinsight/rag_tuning/registry.py:55](../../../backend/scinsight/rag_tuning/registry.py#L55) | — | Store a validated draft and say how it differs from the active configuration (an |
| F1909 | `Registry.set_status` | method | used | [backend/scinsight/rag_tuning/registry.py:66](../../../backend/scinsight/rag_tuning/registry.py#L66) | — |  |
| F1910 | `Registry.start_job` | method | used | [backend/scinsight/rag_tuning/registry.py:72](../../../backend/scinsight/rag_tuning/registry.py#L72) | — | Run fn() in a background thread (HTTP returns at once; the console polls the job |
| F1911 | `Registry.start_job.run` | nested | used | [backend/scinsight/rag_tuning/registry.py:78](../../../backend/scinsight/rag_tuning/registry.py#L78) | — |  |
| F1912 | `Registry.job` | method | used | [backend/scinsight/rag_tuning/registry.py:92](../../../backend/scinsight/rag_tuning/registry.py#L92) | — |  |
| F1913 | `Registry.save_experiment` | method | used | [backend/scinsight/rag_tuning/registry.py:99](../../../backend/scinsight/rag_tuning/registry.py#L99) | — |  |
| F1914 | `Registry.experiments` | method | used | [backend/scinsight/rag_tuning/registry.py:105](../../../backend/scinsight/rag_tuning/registry.py#L105) | — |  |
| F1915 | `Registry.experiment` | method | used | [backend/scinsight/rag_tuning/registry.py:110](../../../backend/scinsight/rag_tuning/registry.py#L110) | — |  |
| F1916 | `terms` | function | used | [backend/scinsight/rag_tuning/retrieval.py:19](../../../backend/scinsight/rag_tuning/retrieval.py#L19) | — |  |
| F1917 | `keyword_score` | function | used | [backend/scinsight/rag_tuning/retrieval.py:23](../../../backend/scinsight/rag_tuning/retrieval.py#L23) | — |  |
| F1918 | `rank` | function | used | [backend/scinsight/rag_tuning/retrieval.py:32](../../../backend/scinsight/rag_tuning/retrieval.py#L32) | — | Score and order chunk rows; returns copies with semantic / keyword / rerank / sc |
| F1781 | `build` | function | used | [flowise/code_explorer/deploy_code_map.py:27](../../../flowise/code_explorer/deploy_code_map.py#L27) | — |  |
| F1782 | `import_flows` | function | used | [flowise/code_explorer/deploy_code_map.py:44](../../../flowise/code_explorer/deploy_code_map.py#L44) | — |  |
| F1783 | `main` | function | used | [flowise/code_explorer/deploy_code_map.py:69](../../../flowise/code_explorer/deploy_code_map.py#L69) | — |  |
| F1919 | `env` | function | used | [scripts/rag_tuning.py:35](../../../scripts/rag_tuning.py#L35) | — |  |
| F1920 | `Client` | class | used | [scripts/rag_tuning.py:40](../../../scripts/rag_tuning.py#L40) | — |  |
| F1921 | `Client.__init__` | method | used (framework) | [scripts/rag_tuning.py:41](../../../scripts/rag_tuning.py#L41) | — |  |
| F1922 | `Client.call` | method | used (framework) | [scripts/rag_tuning.py:44](../../../scripts/rag_tuning.py#L44) | — |  |
| F1923 | `Client.job` | method | used (framework) | [scripts/rag_tuning.py:53](../../../scripts/rag_tuning.py#L53) | — |  |
| F1924 | `show` | function | used | [scripts/rag_tuning.py:63](../../../scripts/rag_tuning.py#L63) | — |  |
| F1925 | `main` | function | used | [scripts/rag_tuning.py:67](../../../scripts/rag_tuning.py#L67) | — |  |
| F1926 | `verify` | function | used | [scripts/rag_tuning.py:162](../../../scripts/rag_tuning.py#L162) | — | End to end: ask the live Flowise chatflow, then check which configuration answer |
| F1957 | `TemplateSettings` | pydantic_model | used | [templates/backend/fastapi_app.py:23](../../../templates/backend/fastapi_app.py#L23) | — |  |
| F1958 | `Principal` | class | used | [templates/backend/fastapi_app.py:30](../../../templates/backend/fastapi_app.py#L30) | — |  |
| F1959 | `ItemRequest` | pydantic_model | used | [templates/backend/fastapi_app.py:37](../../../templates/backend/fastapi_app.py#L37) | — | Request body: validated before the route runs (422 otherwise). |
| F1960 | `create_app` | function | used | [templates/backend/fastapi_app.py:43](../../../templates/backend/fastapi_app.py#L43) | — |  |
| F1961 | `create_app.principal` | nested | used | [templates/backend/fastapi_app.py:52](../../../templates/backend/fastapi_app.py#L52) | — |  |
| F1962 | `create_app.reader` | nested | used | [templates/backend/fastapi_app.py:58](../../../templates/backend/fastapi_app.py#L58) | — |  |
| F1963 | `create_app.manager` | nested | used | [templates/backend/fastapi_app.py:61](../../../templates/backend/fastapi_app.py#L61) | — |  |
| F1964 | `create_app.health` | route | used | [templates/backend/fastapi_app.py:67](../../../templates/backend/fastapi_app.py#L67) | — |  |
| F1965 | `create_app.get_stock` | route | used | [templates/backend/fastapi_app.py:71](../../../templates/backend/fastapi_app.py#L71) | — |  |
| F1966 | `create_app.adjust` | route | used | [templates/backend/fastapi_app.py:78](../../../templates/backend/fastapi_app.py#L78) | — |  |
| F1967 | `create_app.sap_read_only` | route | used | [templates/backend/fastapi_app.py:84](../../../templates/backend/fastapi_app.py#L84) | — |  |
| F1968 | `create_app.read_audit` | route | used | [templates/backend/fastapi_app.py:88](../../../templates/backend/fastapi_app.py#L88) | — |  |
| F2028 | `create_inner_router` | function | used | [templates/backend/fastapi_router.py:18](../../../templates/backend/fastapi_router.py#L18) | — | A module's routes and its shared objects (router.state), like backend/scinsight/ |
| F2029 | `create_inner_router.caller` | nested | used | [templates/backend/fastapi_router.py:24](../../../templates/backend/fastapi_router.py#L24) | — |  |
| F2030 | `create_inner_router.health` | route | used | [templates/backend/fastapi_router.py:29](../../../templates/backend/fastapi_router.py#L29) | — |  |
| F2031 | `create_inner_router.get_stock` | route | used | [templates/backend/fastapi_router.py:33](../../../templates/backend/fastapi_router.py#L33) | — |  |
| F2032 | `create_app` | function | used | [templates/backend/fastapi_router.py:42](../../../templates/backend/fastapi_router.py#L42) | — |  |
| F2033 | `create_app.health` | route | used | [templates/backend/fastapi_router.py:47](../../../templates/backend/fastapi_router.py#L47) | — |  |
| F1972 | `State` | class | used | [templates/backend/langgraph_graph.py:19](../../../templates/backend/langgraph_graph.py#L19) | — |  |
| F1973 | `understand` | function | used | [templates/backend/langgraph_graph.py:27](../../../templates/backend/langgraph_graph.py#L27) | — |  |
| F1974 | `calculate` | function | used | [templates/backend/langgraph_graph.py:33](../../../templates/backend/langgraph_graph.py#L33) | — |  |
| F1975 | `approval` | function | used | [templates/backend/langgraph_graph.py:38](../../../templates/backend/langgraph_graph.py#L38) | — |  |
| F1976 | `answer` | function | used | [templates/backend/langgraph_graph.py:44](../../../templates/backend/langgraph_graph.py#L44) | — |  |
| F1977 | `route_after_understand` | function | used | [templates/backend/langgraph_graph.py:50](../../../templates/backend/langgraph_graph.py#L50) | — |  |
| F1978 | `build_graph` | function | used | [templates/backend/langgraph_graph.py:54](../../../templates/backend/langgraph_graph.py#L54) | — |  |
| F1979 | `stock_level` | function | used | [templates/backend/mcp_server.py:24](../../../templates/backend/mcp_server.py#L24) | — | Current on-hand quantity of one SKU (read-only). |
| F1980 | `low_stock` | function | used | [templates/backend/mcp_server.py:32](../../../templates/backend/mcp_server.py#L32) | — | SKUs whose on-hand quantity is below the threshold (read-only). |
| F1981 | `ApiKeyMiddleware` | class | used | [templates/backend/mcp_server.py:38](../../../templates/backend/mcp_server.py#L38) | — | Bearer or X-API-Key check on /mcp; keys come from TPL_MCP_KEYS (comma separated) |
| F1982 | `ApiKeyMiddleware.__init__` | method | used (framework) | [templates/backend/mcp_server.py:41](../../../templates/backend/mcp_server.py#L41) | — |  |
| F1983 | `ApiKeyMiddleware.dispatch` | method | used (framework) | [templates/backend/mcp_server.py:45](../../../templates/backend/mcp_server.py#L45) | — |  |
| F1984 | `create_mcp_app` | function | used | [templates/backend/mcp_server.py:54](../../../templates/backend/mcp_server.py#L54) | — |  |
