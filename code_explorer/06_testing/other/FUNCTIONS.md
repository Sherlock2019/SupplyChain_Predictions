# 06_testing/other (generated)

Modules: `backend/app/code_editor.py`, `backend/scinsight/rag_tuning/api.py`, `backend/scinsight/rag_tuning/chunking.py`, `backend/scinsight/rag_tuning/config.py`, `backend/scinsight/rag_tuning/documents.py`, `backend/scinsight/rag_tuning/embeddings.py`, `backend/scinsight/rag_tuning/evaluation.py`, `backend/scinsight/rag_tuning/flowise_adapter.py`, `backend/scinsight/rag_tuning/indexing.py`, `backend/scinsight/rag_tuning/publishing.py`, `backend/scinsight/rag_tuning/registry.py`, `backend/scinsight/rag_tuning/retrieval.py`, `flowise/code_explorer/deploy_code_map.py`, `scripts/rag_tuning.py`

| ID | Function / class | Kind | Status | Original | Annotated copy | Summary |
|---|---|---|---|---|---|---|
| F1784 | `_defs` | function | used | [backend/app/code_editor.py:39](../../../backend/app/code_editor.py#L39) | — | qualname -> def/class node, including methods and nested functions. |
| F1785 | `_defs.walk` | nested | used | [backend/app/code_editor.py:43](../../../backend/app/code_editor.py#L43) | — |  |
| F1786 | `_span` | function | used | [backend/app/code_editor.py:54](../../../backend/app/code_editor.py#L54) | — |  |
| F1787 | `CodeEditor` | class | used | [backend/app/code_editor.py:58](../../../backend/app/code_editor.py#L58) | — |  |
| F1788 | `CodeEditor.__init__` | method | used (framework) | [backend/app/code_editor.py:59](../../../backend/app/code_editor.py#L59) | — |  |
| F1789 | `CodeEditor._registry` | method | used | [backend/app/code_editor.py:66](../../../backend/app/code_editor.py#L66) | — |  |
| F1790 | `CodeEditor._files` | method | used | [backend/app/code_editor.py:74](../../../backend/app/code_editor.py#L74) | — |  |
| F1800 | `CodeEditor._apps_of` | method | used | [backend/app/code_editor.py:77](../../../backend/app/code_editor.py#L77) | — | file -> ids of the apps that load it (transitive backend imports from each app's |
| F1791 | `CodeEditor.list` | method | used | [backend/app/code_editor.py:103](../../../backend/app/code_editor.py#L103) | — |  |
| F1792 | `CodeEditor._locate` | method | used (framework) | [backend/app/code_editor.py:130](../../../backend/app/code_editor.py#L130) | — |  |
| F1793 | `CodeEditor.get` | method | used (framework) | [backend/app/code_editor.py:143](../../../backend/app/code_editor.py#L143) | — |  |
| F1794 | `CodeEditor.update` | method | used (framework) | [backend/app/code_editor.py:173](../../../backend/app/code_editor.py#L173) | — |  |
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
| F1859 | `_front_matter` | function | used | [backend/scinsight/rag_tuning/documents.py:17](../../../backend/scinsight/rag_tuning/documents.py#L17) | — |  |
| F1860 | `inventory` | function | used | [backend/scinsight/rag_tuning/documents.py:22](../../../backend/scinsight/rag_tuning/documents.py#L22) | — | Every source file of the caller's tenant with its metadata, index state and defi |
| F1861 | `validate_document_metadata` | function | used | [backend/scinsight/rag_tuning/documents.py:56](../../../backend/scinsight/rag_tuning/documents.py#L56) | — | Checks on one document: missing fields, scope, validity and source quality (seve |
| F1862 | `_cross_document_checks` | function | used | [backend/scinsight/rag_tuning/documents.py:83](../../../backend/scinsight/rag_tuning/documents.py#L83) | — |  |
| F1863 | `source_text` | function | used | [backend/scinsight/rag_tuning/documents.py:105](../../../backend/scinsight/rag_tuning/documents.py#L105) | — | The source document of the caller's tenant (front matter + body) for preview; ot |
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
| F1885 | `FlowiseAdapter._nodes` | method | used | [backend/scinsight/rag_tuning/flowise_adapter.py:55](../../../backend/scinsight/rag_tuning/flowise_adapter.py#L55) | — |  |
| F1886 | `FlowiseAdapter.status` | method | used (framework) | [backend/scinsight/rag_tuning/flowise_adapter.py:63](../../../backend/scinsight/rag_tuning/flowise_adapter.py#L63) | — | What the live chatflow RAG DB uses right now, and what its table holds. |
| F1887 | `FlowiseAdapter.table_rows` | method | used | [backend/scinsight/rag_tuning/flowise_adapter.py:83](../../../backend/scinsight/rag_tuning/flowise_adapter.py#L83) | — |  |
| F1888 | `FlowiseAdapter.compatible` | method | used | [backend/scinsight/rag_tuning/flowise_adapter.py:92](../../../backend/scinsight/rag_tuning/flowise_adapter.py#L92) | — | Reasons the chatflow RAG DB cannot follow this configuration (empty = it can). |
| F1889 | `FlowiseAdapter.sync` | method | used | [backend/scinsight/rag_tuning/flowise_adapter.py:99](../../../backend/scinsight/rag_tuning/flowise_adapter.py#L99) | — | Apply chunk size / overlap / top-k and the version tag to the chatflow, re-index |
| F1890 | `FlowiseAdapter.restore` | method | used | [backend/scinsight/rag_tuning/flowise_adapter.py:124](../../../backend/scinsight/rag_tuning/flowise_adapter.py#L124) | — |  |
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
