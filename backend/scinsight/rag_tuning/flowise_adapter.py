"""Keeps the Flowise chatflow's own Company RAG DB in step with the published configuration.

The chatflow SCInsight-Cosmetics-Chatflow-v1 reaches company policies through two tools:
  company_policy_rag_db       Flowise Retriever tool -> Postgres vector store (table scinsight_flowise_rag, database scinsight)
                              <- Folder loader (opt/flows/scinsight/knowledge) <- Markdown text splitter, embeddings = gateway
                              /v1/embeddings (BAAI/bge-small-en-v1.5), record manager with full cleanup
  search_supply_chain_policy  Custom Tool -> POST api:8000/scinsight/api/v1/rag/search -> KnowledgeBase.search (tuned directly)
On publish this module updates the first path: splitter chunkSize / chunkOverlap, vector store topK, and a rag_config_version
tag in the loader metadata; then re-indexes through Flowise's upsert API and verifies the table. Threshold, retrieval mode,
reranking and the context budget have no equivalent on the Flowise Postgres retriever: they apply to the API path only.
The chatflow JSON before the change is kept (rag_config_versions.flowise_backup) and restored on failure or rollback.
"""
from __future__ import annotations

import json
import urllib.error
import urllib.request

GATEWAY_EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"  # what the gateway /v1/embeddings serves to Flowise


class FlowiseError(RuntimeError):
    pass


class FlowiseAdapter:
    def __init__(self, url: str, api_key: str, chatflow_id: str, chatflow_name: str, db, table: str = "scinsight_flowise_rag"):
        self.url, self.api_key, self.chatflow_id, self.chatflow_name, self.db, self.table = url.rstrip("/"), api_key, chatflow_id, chatflow_name, db, table

    @property
    def configured(self) -> bool:
        return bool(self.url and self.api_key)

    def _call(self, method: str, path: str, body: dict | None = None, timeout: int = 300):
        req = urllib.request.Request(self.url + path, method=method, data=json.dumps(body).encode() if body is not None else None,
                                     headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                text = r.read().decode()
                return json.loads(text) if text else {}
        except urllib.error.HTTPError as exc:
            raise FlowiseError(f"Flowise {method} {path} -> {exc.code}: {exc.read().decode()[:300]}") from exc
        except OSError as exc:
            raise FlowiseError(f"Flowise unreachable at {self.url}: {exc}") from exc

    def chatflow(self) -> dict:
        if self.chatflow_id:
            return self._call("GET", f"/api/v1/chatflows/{self.chatflow_id}")
        flow = next((f for f in self._call("GET", "/api/v1/chatflows") if f["name"] == self.chatflow_name), None)
        if flow is None:
            raise FlowiseError(f"chatflow {self.chatflow_name} not found")
        self.chatflow_id = flow["id"]
        return flow

    @staticmethod
    def _nodes(flow_data: dict) -> dict:
        by_name = {}
        for n in flow_data["nodes"]:
            by_name.setdefault(n["data"].get("name"), n)
        return {"splitter": by_name.get("markdownTextSplitter"), "store": by_name.get("postgres"), "loader": by_name.get("folderFiles"),
                "embeddings": by_name.get("openAIEmbeddingsCustom"), "retriever": by_name.get("retrieverTool")}

    def status(self) -> dict:
        """What the live chatflow RAG DB uses right now, and what its table holds."""
        if not self.configured:
            return {"configured": False, "detail": "FLOWISE_URL / FLOWISE_API_KEY not set for the SCInsight API: the chatflow RAG DB is not synchronised"}
        try:
            flow = self.chatflow()
        except FlowiseError as exc:
            return {"configured": True, "reachable": False, "detail": str(exc)}
        nodes = self._nodes(json.loads(flow["flowData"]))
        if not nodes["splitter"] or not nodes["store"]:
            return {"configured": True, "reachable": True, "chatflow": flow["name"], "detail": "no Markdown splitter / Postgres store node found"}
        inp = lambda n, k: (n or {}).get("data", {}).get("inputs", {}).get(k)  # noqa: E731
        meta = inp(nodes["loader"], "metadata") or "{}"
        return {"configured": True, "reachable": True, "chatflow": flow["name"], "chatflow_id": flow["id"],
                "retriever_tool": inp(nodes["retriever"], "name"), "chunk_size": inp(nodes["splitter"], "chunkSize"),
                "chunk_overlap": inp(nodes["splitter"], "chunkOverlap"), "top_k": inp(nodes["store"], "topK"),
                "table": inp(nodes["store"], "tableName"), "embedding_model": inp(nodes["embeddings"], "modelName"),
                "rag_config_version": json.loads(meta).get("rag_config_version") if isinstance(meta, str) and meta.strip().startswith("{") else None,
                "table_rows": self.table_rows()}

    def table_rows(self) -> dict | None:
        if self.db.dialect != "postgres":
            return None
        try:
            rows = self.db.query(f"select metadata->>'rag_config_version' as v, count(*) as n from {self.table} group by 1")
        except Exception:  # noqa: BLE001 - table not created until the first Flowise upsert
            return None
        return {(r["v"] or "untagged"): r["n"] for r in rows}

    def compatible(self, cfg) -> list[str]:
        """Reasons the chatflow RAG DB cannot follow this configuration (empty = it can)."""
        problems = []
        if cfg.embedding_model != GATEWAY_EMBEDDING_MODEL:
            problems.append(f"the chatflow RAG DB embeds through the gateway /v1/embeddings, which serves only {GATEWAY_EMBEDDING_MODEL}")
        return problems

    def sync(self, cfg, config_id: str) -> dict:
        """Apply chunk size / overlap / top-k and the version tag to the chatflow, re-index it and verify the table."""
        flow = self.chatflow()
        backup = flow["flowData"]
        data = json.loads(backup)
        nodes = self._nodes(data)
        nodes["splitter"]["data"]["inputs"].update({"chunkSize": cfg.chunk_size, "chunkOverlap": cfg.chunk_overlap})
        nodes["store"]["data"]["inputs"]["topK"] = cfg.top_k
        loader = nodes["loader"]["data"]["inputs"]
        meta = json.loads(loader.get("metadata") or "{}")
        meta["rag_config_version"] = config_id
        loader["metadata"] = json.dumps(meta)
        self._call("PUT", f"/api/v1/chatflows/{flow['id']}", {"flowData": json.dumps(data)})
        try:
            upsert = self._call("POST", f"/api/v1/vector/upsert/{flow['id']}", {}, timeout=600)
            rows = self.table_rows()
            if rows is not None and set(rows) != {config_id}:
                raise FlowiseError(f"after re-indexing the chatflow RAG DB holds {rows}: expected only rows tagged {config_id}")
        except Exception:
            self.restore(backup)  # the previous chatflow and its index come back; the active configuration stays active
            raise
        return {"backup": backup, "upsert": {k: upsert.get(k) for k in ("numAdded", "numUpdated", "numSkipped", "numDeleted")},
                "table_rows": rows, "applied": {"chunk_size": cfg.chunk_size, "chunk_overlap": cfg.chunk_overlap, "top_k": cfg.top_k,
                                                "splitter": "Flowise Markdown text splitter (characters)", "tag": config_id}}

    def restore(self, backup: str) -> dict:
        flow = self.chatflow()
        self._call("PUT", f"/api/v1/chatflows/{flow['id']}", {"flowData": backup})
        upsert = self._call("POST", f"/api/v1/vector/upsert/{flow['id']}", {}, timeout=600)
        return {"restored": True, "upsert": {k: upsert.get(k) for k in ("numAdded", "numUpdated", "numSkipped", "numDeleted")}, "table_rows": self.table_rows()}
