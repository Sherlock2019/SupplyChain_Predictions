#!/usr/bin/env python3
"""RAG tuning from the terminal: the same SCInsight API endpoints as the dashboard's RAG Tuning page.

    python3 scripts/rag_tuning.py config                       # active configuration + retrieval path
    python3 scripts/rag_tuning.py documents                    # knowledge base inventory
    python3 scripts/rag_tuning.py validate                     # metadata and source-quality checks
    python3 scripts/rag_tuning.py preview POL-PROC-001 --size 600 --overlap 100 [--strategy clause]
    python3 scripts/rag_tuning.py models                       # approved embedding models
    python3 scripts/rag_tuning.py retrieve "Who must approve a warehouse stock transfer?" [--top-k 5 --threshold 0.5 --mode hybrid]
    python3 scripts/rag_tuning.py draft --size 600 --overlap 100 [--top-k 5] [--name medium]
    python3 scripts/rag_tuning.py build RCFG-XXXXXXXX           # candidate index (background job, waits)
    python3 scripts/rag_tuning.py evaluate RCFG-A RCFG-B        # benchmark (dataset v1)
    python3 scripts/rag_tuning.py compare EXP-A EXP-B
    python3 scripts/rag_tuning.py history | flowise | metrics
    python3 scripts/rag_tuning.py publish RCFG-XXXXXXXX --confirm   /   rollback RCFG-XXXXXXXX --confirm
    python3 scripts/rag_tuning.py verify "Who must approve a warehouse stock transfer?"   # ask the live Flowise chatflow

Keys come from .env (SCI_DIRECTOR_KEY for the SCInsight API, FLOWISE_SCI_API_KEY / FLOWISE_SCI_CHATFLOW_ID for verify);
they are never printed.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def env() -> dict:
    path = ROOT / ".env"
    return dict(re.findall(r"^([A-Z0-9_]+)=(.*)$", path.read_text(), re.M)) if path.exists() else {}


class Client:
    def __init__(self, base: str, key: str):
        self.base, self.key = base.rstrip("/"), key

    def call(self, method: str, path: str, body: dict | None = None):
        req = urllib.request.Request(self.base + path, method=method, data=json.dumps(body).encode() if body is not None else None,
                                     headers={"X-API-Key": self.key, "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=600) as r:
                return json.loads(r.read() or b"{}")
        except urllib.error.HTTPError as exc:
            sys.exit(f"{method} {path} -> {exc.code}: {exc.read().decode()[:800]}")

    def job(self, job: dict) -> dict:
        while job["status"] in ("running", "queued"):
            print(f"  job {job['id']} {job['kind']}: {job['status']}…", file=sys.stderr)
            time.sleep(2)
            job = self.call("GET", f"/api/v1/rag-tuning/jobs/{job['id']}")
        if job["status"] == "failed":
            sys.exit(f"job failed: {job['error']}")
        return job["result"]


def show(data) -> None:
    print(json.dumps(data, indent=1, default=str))


def main() -> int:
    e = env()
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--api", default="http://localhost:8100")
    ap.add_argument("--key", default=e.get("SCI_DIRECTOR_KEY", ""), help="SCInsight administrator key (default: SCI_DIRECTOR_KEY from .env)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("config", "documents", "validate", "models", "history", "flowise", "metrics"):
        sub.add_parser(name)
    p = sub.add_parser("preview")
    p.add_argument("doc_id")
    for s in (p, d := sub.add_parser("draft")):
        s.add_argument("--size", type=int)
        s.add_argument("--overlap", type=int)
        s.add_argument("--strategy", choices=["section", "fixed", "clause"])
        s.add_argument("--model")
    d.add_argument("--top-k", type=int)
    d.add_argument("--threshold", type=float)
    d.add_argument("--mode", choices=["semantic", "keyword", "hybrid"])
    d.add_argument("--rerank", choices=["none", "lexical"])
    d.add_argument("--name", default="cli draft")
    r = sub.add_parser("retrieve")
    r.add_argument("query")
    r.add_argument("--config")
    r.add_argument("--top-k", type=int)
    r.add_argument("--threshold", type=float)
    r.add_argument("--mode", choices=["semantic", "keyword", "hybrid"])
    r.add_argument("--rerank", choices=["none", "lexical"])
    r.add_argument("--role")
    sub.add_parser("build").add_argument("config_id")
    ev = sub.add_parser("evaluate")
    ev.add_argument("config_ids", nargs="+")
    ev.add_argument("--answers", action="store_true")
    c = sub.add_parser("compare")
    c.add_argument("active")
    c.add_argument("candidate")
    for name in ("publish", "rollback"):
        s = sub.add_parser(name)
        s.add_argument("config_id")
        s.add_argument("--confirm", action="store_true")
    v = sub.add_parser("verify")
    v.add_argument("question")
    v.add_argument("--flowise", default="http://localhost:3101")
    a = ap.parse_args()
    if not a.key:
        sys.exit("no administrator key: set SCI_DIRECTOR_KEY in .env or pass --key")
    api, base = Client(a.api, a.key), "/api/v1/rag-tuning"
    active = lambda: api.call("GET", f"{base}/config")["active"]  # noqa: E731

    if a.cmd in ("config", "documents", "models", "history", "flowise", "metrics"):
        show(api.call("GET", f"{base}/{ {'models': 'embedding-models'}.get(a.cmd, a.cmd) }"))
    elif a.cmd == "validate":
        show(api.call("POST", f"{base}/metadata/validate"))
    elif a.cmd in ("preview", "draft"):
        cfg = dict(active()["config"])
        cfg.update({k: v for k, v in {"chunk_size": a.size, "chunk_overlap": a.overlap, "chunk_strategy": a.strategy, "embedding_model": a.model}.items() if v is not None})
        if a.cmd == "preview":
            out = api.call("POST", f"{base}/chunks/preview", {"doc_id": a.doc_id, "config": cfg, "compare_with": active()["config"]})
            for label, prev in (("candidate", out["preview"]), ("active", out["compare"])):
                print(f"== {label}: {prev['count']} chunks, avg {prev['avg_chars']} {prev['unit']}")
                for ch in prev["chunks"]:
                    print(f"  {ch['chunk_id']} [{ch['section']}] {ch['chars']} chars ~{ch['approx_tokens']} tok overlap {ch['overlap_with_previous']}")
        else:
            cfg.update({k: v for k, v in {"top_k": a.top_k, "similarity_threshold": a.threshold, "retrieval_mode": a.mode, "rerank": a.rerank}.items() if v is not None})
            cfg["candidate_k"] = max(cfg["candidate_k"], cfg["top_k"])
            out = api.call("PUT", f"{base}/draft", {"config": cfg, "name": a.name})
            show({"id": out["id"], "diff": out["diff"]})
    elif a.cmd == "retrieve":
        over = {k: v for k, v in {"top_k": a.top_k, "similarity_threshold": a.threshold, "retrieval_mode": a.mode, "rerank": a.rerank}.items() if v is not None}
        if "top_k" in over:
            over["candidate_k"] = max(16, over["top_k"])
        out = api.call("POST", f"{base}/retrieve/preview", {"query": a.query, "config_id": a.config, "overrides": over, "roles": [a.role] if a.role else []})
        print(f"config {out['config_version']} · index {out['index_version']} · {out['embedding_model']} · {out['latency_ms']}")
        for i, h in enumerate(out["results"], 1):
            print(f"{i}. {h['citation']['doc_id']} v{h['citation']['version']} [{h['citation']['section']}] score {h['score']} (sem {h['semantic_score']}, kw {h['keyword_score']})")
        for x in out["excluded"][:10]:
            print(f"   excluded {x['doc_id']} [{x['section']}]: {x['reason']}")
    elif a.cmd == "build":
        show(api.job(api.call("POST", f"{base}/index/build-candidate", {"config_id": a.config_id})))
    elif a.cmd == "evaluate":
        res = api.job(api.call("POST", f"{base}/evaluate", {"config_ids": a.config_ids, "with_answers": a.answers}))
        for exp in res["experiments"]:
            s = exp["summary"]
            print(f"{exp['experiment_id']} {exp['config_id']}: hit@{s['k']} {s['hit_rate']} recall {s['recall']} precision {s['precision']} mrr {s['mrr']} "
                  f"evidence {s['evidence_coverage']} no-evidence {s['no_evidence_pass']} leakage {s['leakage']} mean {s['latency_mean_ms']} ms p95 {s['latency_p95_ms']} ms")
    elif a.cmd == "compare":
        show(api.call("GET", f"{base}/experiments/compare?active={a.active}&candidate={a.candidate}"))
    elif a.cmd in ("publish", "rollback"):
        if not a.confirm:
            sys.exit(f"{a.cmd} changes the live Company RAG Search: add --confirm")
        show(api.call("POST", f"{base}/{a.cmd}", {"config_id": a.config_id, "confirm": True}))
    elif a.cmd == "verify":
        return verify(api, base, e, a.question, a.flowise)
    return 0


def verify(api: Client, base: str, e: dict, question: str, flowise_url: str) -> int:
    """End to end: ask the live Flowise chatflow, then check which configuration answered on both RAG paths."""
    act = api.call("GET", f"{base}/config")["active"]
    before = {r["ts"] for r in api.call("GET", f"{base}/metrics?limit=200")["recent"]}
    chat_id, fkey = e.get("FLOWISE_SCI_CHATFLOW_ID", ""), e.get("FLOWISE_SCI_API_KEY", "")
    if not chat_id or not fkey:
        sys.exit("FLOWISE_SCI_CHATFLOW_ID / FLOWISE_SCI_API_KEY missing in .env")
    t0 = time.perf_counter()
    req = urllib.request.Request(f"{flowise_url.rstrip('/')}/api/v1/prediction/{chat_id}", method="POST",
                                 data=json.dumps({"question": question, "overrideConfig": {"sessionId": f"rag-verify-{int(time.time())}"}}).encode(),
                                 headers={"Authorization": f"Bearer {fkey}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=600) as r:
        pred = json.loads(r.read())
    elapsed = round(time.perf_counter() - t0, 1)
    tools = [t.get("tool") for t in pred.get("usedTools") or []]
    sources = [(d.get("metadata") or {}) for d in pred.get("sourceDocuments") or []]
    api_calls = [r for r in api.call("GET", f"{base}/metrics?limit=200")["recent"] if r["ts"] not in before and r["source"] == "api"]
    fl = api.call("GET", f"{base}/flowise")
    report = {"question": question, "seconds": elapsed, "answer": (pred.get("text") or "")[:800], "tools_used": tools,
              "active_config": act["id"], "active_index": act["index_version"],
              "api_path": {"calls": len(api_calls), "config_versions": sorted({r["config_id"] for r in api_calls}),
                           "doc_ids": sorted({d for r in api_calls for d in r["doc_ids"]})},
              "flowise_rag_db": {"source_tags": sorted({str(s.get("rag_config_version", "untagged")) for s in sources}),
                                 "sources": sorted({Path(str(s.get("source", ""))).name for s in sources}), "table_rows": fl.get("table_rows"),
                                 "splitter": f"{fl.get('chunk_size')}/{fl.get('chunk_overlap')}", "top_k": fl.get("top_k")}}
    checks = []
    if "search_supply_chain_policy" in tools:
        checks.append(("API path used the active configuration", set(report["api_path"]["config_versions"]) == {act["id"]}))
    if "company_policy_rag_db" in tools:
        want = "untagged" if act["name"] == "baseline" else act["id"]
        checks.append(("chatflow RAG DB sources carry the active configuration tag", report["flowise_rag_db"]["source_tags"] in ([want], [])))
    checks.append(("no other-tenant document in the answer sources", "POL-NW-001" not in json.dumps(report)))
    checks.append(("a Company RAG tool was invoked", bool({"search_supply_chain_policy", "company_policy_rag_db"} & set(tools))))
    report["checks"] = [{"check": c, "ok": bool(ok)} for c, ok in checks]
    show(report)
    return 0 if all(ok for _, ok in checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
