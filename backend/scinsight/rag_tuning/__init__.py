"""RAG tuning for the SCInsight Company RAG Search (governed policy search + the Flowise chatflow RAG DB).

Draft -> preview -> candidate index -> benchmark -> validate -> publish -> monitor -> rollback, against the real
KnowledgeBase in backend/scinsight/rag.py (tables rag_documents / rag_chunks, one index version per configuration).
See docs/RAG_TUNING_GUIDE.md.
"""
