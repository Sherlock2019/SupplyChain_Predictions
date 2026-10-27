# 04_ai_ml/rag (generated)

Modules: `backend/app/rag.py`, `backend/scinsight/rag.py`

| ID | Function / class | Kind | Status | Original | Annotated copy | Summary |
|---|---|---|---|---|---|---|
| F0731 | `HashEmbedder` | class | used | [backend/app/rag.py:21](../../../backend/app/rag.py#L21) | [annotated](../../04_ai_ml/rag/app_rag.py) |  |
| F0732 | `HashEmbedder.embed` | method | used | [backend/app/rag.py:24](../../../backend/app/rag.py#L24) | [annotated](../../04_ai_ml/rag/app_rag.py) |  |
| F0733 | `HashEmbedder._one` | method | used | [backend/app/rag.py:27](../../../backend/app/rag.py#L27) | [annotated](../../04_ai_ml/rag/app_rag.py) |  |
| F0734 | `FastEmbedder` | class | used | [backend/app/rag.py:38](../../../backend/app/rag.py#L38) | [annotated](../../04_ai_ml/rag/app_rag.py) |  |
| F0735 | `FastEmbedder.__init__` | method | used (framework) | [backend/app/rag.py:39](../../../backend/app/rag.py#L39) | [annotated](../../04_ai_ml/rag/app_rag.py) |  |
| F0736 | `FastEmbedder.embed` | method | used | [backend/app/rag.py:46](../../../backend/app/rag.py#L46) | [annotated](../../04_ai_ml/rag/app_rag.py) |  |
| F0737 | `get_embedder` | function | used | [backend/app/rag.py:54](../../../backend/app/rag.py#L54) | [annotated](../../04_ai_ml/rag/app_rag.py) |  |
| F0738 | `cosine` | function | used | [backend/app/rag.py:61](../../../backend/app/rag.py#L61) | [annotated](../../04_ai_ml/rag/app_rag.py) |  |
| F0739 | `chunk_markdown` | function | used | [backend/app/rag.py:65](../../../backend/app/rag.py#L65) | [annotated](../../04_ai_ml/rag/app_rag.py) | Split on second-level headings; each chunk carries the document title and sectio |
| F0740 | `chunk_markdown.flush` | nested | used | [backend/app/rag.py:75](../../../backend/app/rag.py#L75) | [annotated](../../04_ai_ml/rag/app_rag.py) |  |
| F0741 | `keyword_boost` | function | used | [backend/app/rag.py:90](../../../backend/app/rag.py#L90) | [annotated](../../04_ai_ml/rag/app_rag.py) |  |
| F0742 | `Chunk` | class | used | [backend/app/rag.py:97](../../../backend/app/rag.py#L97) | [annotated](../../04_ai_ml/rag/app_rag.py) |  |
| F0743 | `MemoryRag` | class | used | [backend/app/rag.py:107](../../../backend/app/rag.py#L107) | [annotated](../../04_ai_ml/rag/app_rag.py) |  |
| F0744 | `MemoryRag.__init__` | method | used (framework) | [backend/app/rag.py:110](../../../backend/app/rag.py#L110) | [annotated](../../04_ai_ml/rag/app_rag.py) |  |
| F0745 | `MemoryRag.add` | method | used | [backend/app/rag.py:114](../../../backend/app/rag.py#L114) | [annotated](../../04_ai_ml/rag/app_rag.py) |  |
| F0746 | `MemoryRag.search` | method | used | [backend/app/rag.py:120](../../../backend/app/rag.py#L120) | [annotated](../../04_ai_ml/rag/app_rag.py) |  |
| F0747 | `MemoryRag.stats` | method | used | [backend/app/rag.py:130](../../../backend/app/rag.py#L130) | [annotated](../../04_ai_ml/rag/app_rag.py) |  |
| F0748 | `MemoryRag.load_directory` | method | used | [backend/app/rag.py:133](../../../backend/app/rag.py#L133) | [annotated](../../04_ai_ml/rag/app_rag.py) |  |
| F0749 | `PgVectorRag` | class | used | [backend/app/rag.py:139](../../../backend/app/rag.py#L139) | [annotated](../../04_ai_ml/rag/app_rag.py) |  |
| F0750 | `PgVectorRag.__init__` | method | used (framework) | [backend/app/rag.py:142](../../../backend/app/rag.py#L142) | [annotated](../../04_ai_ml/rag/app_rag.py) |  |
| F0751 | `PgVectorRag._connect` | method | used | [backend/app/rag.py:159](../../../backend/app/rag.py#L159) | [annotated](../../04_ai_ml/rag/app_rag.py) |  |
| F0752 | `PgVectorRag.add` | method | used | [backend/app/rag.py:167](../../../backend/app/rag.py#L167) | [annotated](../../04_ai_ml/rag/app_rag.py) |  |
| F0753 | `PgVectorRag.stats` | method | used | [backend/app/rag.py:181](../../../backend/app/rag.py#L181) | [annotated](../../04_ai_ml/rag/app_rag.py) |  |
| F0754 | `PgVectorRag.load_directory` | method | used | [backend/app/rag.py:187](../../../backend/app/rag.py#L187) | [annotated](../../04_ai_ml/rag/app_rag.py) | Index the approved corpus once; re-index everything if the embedding model chang |
| F0755 | `PgVectorRag.search` | method | used | [backend/app/rag.py:204](../../../backend/app/rag.py#L204) | [annotated](../../04_ai_ml/rag/app_rag.py) |  |
| F0756 | `create_rag` | function | used | [backend/app/rag.py:224](../../../backend/app/rag.py#L224) | [annotated](../../04_ai_ml/rag/app_rag.py) |  |
| F0757 | `DocumentError` | class | used | [backend/scinsight/rag.py:27](../../../backend/scinsight/rag.py#L27) | [annotated](../../04_ai_ml/rag/scinsight_rag.py) |  |
| F0758 | `parse_document` | function | used | [backend/scinsight/rag.py:31](../../../backend/scinsight/rag.py#L31) | [annotated](../../04_ai_ml/rag/scinsight_rag.py) |  |
| F0759 | `chunk_document` | function | used | [backend/scinsight/rag.py:54](../../../backend/scinsight/rag.py#L54) | [annotated](../../04_ai_ml/rag/scinsight_rag.py) | Split on '## ' sections, then into <= CHUNK_CHARS windows with OVERLAP; each chu |
| F0760 | `HashEmbedder` | class | used | [backend/scinsight/rag.py:80](../../../backend/scinsight/rag.py#L80) | [annotated](../../04_ai_ml/rag/scinsight_rag.py) |  |
| F0761 | `HashEmbedder.embed` | method | used | [backend/scinsight/rag.py:83](../../../backend/scinsight/rag.py#L83) | [annotated](../../04_ai_ml/rag/scinsight_rag.py) |  |
| F0762 | `make_embedder` | function | used | [backend/scinsight/rag.py:95](../../../backend/scinsight/rag.py#L95) | [annotated](../../04_ai_ml/rag/scinsight_rag.py) |  |
| F0763 | `KnowledgeBase` | class | used | [backend/scinsight/rag.py:103](../../../backend/scinsight/rag.py#L103) | [annotated](../../04_ai_ml/rag/scinsight_rag.py) |  |
| F0764 | `KnowledgeBase.__init__` | method | used (framework) | [backend/scinsight/rag.py:104](../../../backend/scinsight/rag.py#L104) | [annotated](../../04_ai_ml/rag/scinsight_rag.py) |  |
| F0765 | `KnowledgeBase.ingest_dir` | method | used | [backend/scinsight/rag.py:107](../../../backend/scinsight/rag.py#L107) | [annotated](../../04_ai_ml/rag/scinsight_rag.py) |  |
| F0766 | `KnowledgeBase.search` | method | used | [backend/scinsight/rag.py:139](../../../backend/scinsight/rag.py#L139) | [annotated](../../04_ai_ml/rag/scinsight_rag.py) |  |
