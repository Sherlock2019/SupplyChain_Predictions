"""Benchmark of a configuration on the versioned question set, through the real KnowledgeBase.search.

Retrieval metrics (deterministic, per case, then averaged over the cases they apply to):
  Hit Rate@K    1 if at least one relevant document is in the top K, else 0        (cases with relevant documents)
  Recall@K      relevant documents found in the top K / relevant documents         (cases with relevant documents)
  Precision@K   returned chunks from a relevant document / K                       (cases with relevant documents)
  MRR           1 / rank of the first relevant chunk (0 if none)                   (cases with relevant documents)
  Evidence      expected facts present in the retrieved text / expected facts      (deterministic grounding of the context)
  No-evidence   1 if nothing is returned for a question the corpus cannot answer  (insufficient_evidence cases)
  Leakage       chunks from a forbidden document (other tenant / role without access) — must be 0
Answer metrics (optional, LLM answers checked deterministically against the retrieved evidence; never the model's own claim):
  fact coverage, citation correctness (cited ids were retrieved and are relevant), unsupported numbers, refusal behaviour.
"""
from __future__ import annotations

import json
import re
import statistics
import time
from datetime import date
from pathlib import Path

DATASET_DIR = Path(__file__).resolve().parents[3] / "data" / "scinsight" / "rag_benchmark"
NUMBER = re.compile(r"\d+(?:[.,]\d+)*")
DOC_ID = re.compile(r"\b[A-Z]{2,5}(?:-[A-Z0-9]+){1,3}\b")
REFUSAL = re.compile(r"no (relevant |matching )?(company )?(policy|document|evidence)|not (found|covered|available) in|insufficient|cannot find|do not have", re.I)


def load_dataset(version: str = "v1") -> dict:
    if not re.fullmatch(r"v\d+", version):
        raise ValueError("dataset version must look like v1")
    return json.loads((DATASET_DIR / f"{version}.json").read_text(encoding="utf-8"))


def _p95(values: list[float]) -> float:
    if not values:
        return 0.0
    s = sorted(values)
    return round(s[min(len(s) - 1, int(round(0.95 * (len(s) - 1))))], 1)


def score_case(case: dict, result: dict, k: int) -> dict:
    """Deterministic retrieval scores of one case."""
    docs = [h["citation"]["doc_id"] for h in result["results"]]
    relevant, forbidden = set(case.get("relevant_doc_ids", [])), set(case.get("forbidden_doc_ids", []))
    text = "\n".join(h["text"] for h in result["results"]).lower()
    out = {"id": case["id"], "category": case["category"], "question": case["question"], "roles": case["roles"], "returned": docs,
           "scores": [h["score"] for h in result["results"]], "latency_ms": result["latency_ms"],
           "leakage": sum(1 for d in docs if d in forbidden)}
    if relevant:
        first = next((i for i, d in enumerate(docs) if d in relevant), None)
        out.update({"hit": 1.0 if first is not None else 0.0, "recall": len(relevant & set(docs)) / len(relevant),
                    "precision": sum(1 for d in docs if d in relevant) / k, "rr": 1.0 / (first + 1) if first is not None else 0.0})
    if case.get("expected_facts"):
        out["evidence"] = sum(1 for f in case["expected_facts"] if f.lower() in text) / len(case["expected_facts"])
    if case.get("expected_citation_versions"):
        versions = {h["citation"]["doc_id"]: h["citation"]["version"] for h in result["results"]}
        out["version_ok"] = 1.0 if all(versions.get(d) == v for d, v in case["expected_citation_versions"].items()) else 0.0
    if case["expected_behavior"] == "insufficient_evidence":  # the corpus cannot answer: the right result is no passage at all
        out["no_evidence_ok"] = 0.0 if docs else 1.0
    return out


def score_answer(case: dict, answer: str, result: dict) -> dict:
    """Checks of an LLM answer against the retrieved evidence (deterministic; the model's confidence is not used)."""
    retrieved = {h["citation"]["doc_id"] for h in result["results"]}
    context = "\n".join(h["text"] for h in result["results"])
    cited = set(DOC_ID.findall(answer))  # every document id the answer cites, retrieved or not
    prose = DOC_ID.sub(" ", answer)      # numbers inside document ids (POL-WH-020) are not claims
    unsupported = sorted({n for n in NUMBER.findall(prose) if n not in context and n.replace(",", "") not in context.replace(",", "")})
    out = {"answer": answer[:1500], "cited": sorted(cited), "unsupported_numbers": unsupported,
           "citation_correct": 1.0 if cited and cited <= retrieved and (not case.get("relevant_doc_ids") or cited & set(case["relevant_doc_ids"])) else 0.0}
    if case.get("expected_facts"):
        out["fact_coverage"] = sum(1 for f in case["expected_facts"] if f.lower() in answer.lower()) / len(case["expected_facts"])
    if case["expected_behavior"] in ("insufficient_evidence", "no_forbidden_evidence"):
        if case["expected_behavior"] == "insufficient_evidence":
            out["refusal_ok"] = 1.0 if REFUSAL.search(answer) else 0.0
        out["citation_correct"] = 1.0 if not cited & set(case.get("forbidden_doc_ids", [])) else 0.0
    return out


def run_rag_benchmark(kb, tenant_id: str, cfg, index_version: str, config_id: str, on: date, dataset_version: str = "v1",
                      answer_fn=None) -> tuple[dict, list[dict]]:
    """Every case through KnowledgeBase.search (the function behind /api/v1/rag/search) with the case's role fixture."""
    data = load_dataset(dataset_version)
    if data["tenant"] != tenant_id:
        raise ValueError(f"dataset {dataset_version} is labelled for tenant {data['tenant']}")
    cases = []
    for case in data["cases"]:
        result = kb.search(tenant_id, frozenset(case["roles"]), case["question"], None, on, cfg=cfg, index_version=index_version,
                           config_id=config_id, source="benchmark")
        scored = score_case(case, result, cfg.top_k)
        if answer_fn is not None:
            t0 = time.perf_counter()
            answer, usage = answer_fn(case["question"], result["results"])
            scored["llm_ms"] = round((time.perf_counter() - t0) * 1000, 1)
            scored["tokens"] = usage
            scored.update(score_answer(case, answer, result))
        cases.append(scored)
    return summarize(cases, cfg.top_k, answer_fn is not None), cases


def summarize(cases: list[dict], k: int, with_answers: bool) -> dict:
    def mean(key):
        vals = [c[key] for c in cases if key in c]
        return round(statistics.mean(vals), 4) if vals else None
    totals = [c["latency_ms"]["total"] for c in cases]
    out = {"k": k, "cases": len(cases), "hit_rate": mean("hit"), "recall": mean("recall"), "precision": mean("precision"), "mrr": mean("rr"),
           "evidence_coverage": mean("evidence"), "version_accuracy": mean("version_ok"), "no_evidence_pass": mean("no_evidence_ok"),
           "leakage": sum(c["leakage"] for c in cases), "latency_mean_ms": round(statistics.mean(totals), 1) if totals else None,
           "latency_p95_ms": _p95(totals), "embed_mean_ms": round(statistics.mean(c["latency_ms"]["embed"] for c in cases), 1) if cases else None,
           "retrieve_mean_ms": round(statistics.mean(c["latency_ms"]["retrieve"] for c in cases), 1) if cases else None,
           "cost_per_query": "N/A (local embedding model, no provider price)"}
    if with_answers:
        llm = [c["llm_ms"] for c in cases if "llm_ms" in c]
        out.update({"answer_fact_coverage": mean("fact_coverage"), "citation_correctness": mean("citation_correct"), "refusal_pass": mean("refusal_ok"),
                    "answers_with_unsupported_numbers": sum(1 for c in cases if c.get("unsupported_numbers")),
                    "llm_mean_ms": round(statistics.mean(llm), 1) if llm else None,
                    "tokens_total": sum((c.get("tokens") or {}).get("total_tokens", 0) for c in cases),
                    "answer_judge": "deterministic checks against the retrieved evidence (no LLM judge)"})
    return out


ACCEPTANCE = {"min_hit_rate_delta": 0.0, "min_recall_delta": -0.05, "max_leakage": 0, "max_p95_factor": 2.0, "max_p95_extra_ms": 200}


def compare_experiments(active: dict, candidate: dict, criteria: dict | None = None) -> dict:
    """Side-by-side measured metrics and a recommendation from the acceptance criteria (no invented numbers)."""
    c = {**ACCEPTANCE, **(criteria or {})}
    a, b = active["summary"], candidate["summary"]
    keys = ["hit_rate", "recall", "precision", "mrr", "evidence_coverage", "no_evidence_pass", "version_accuracy", "leakage",
            "latency_mean_ms", "latency_p95_ms", "answer_fact_coverage", "citation_correctness", "refusal_pass", "cost_per_query"]
    rows = [{"metric": k, "active": a.get(k), "candidate": b.get(k)} for k in keys if a.get(k) is not None or b.get(k) is not None]
    checks = []

    def check(name, ok, detail):
        checks.append({"check": name, "ok": bool(ok), "detail": detail})
    if a.get("hit_rate") is not None and b.get("hit_rate") is not None:
        check("hit_rate", b["hit_rate"] - a["hit_rate"] >= c["min_hit_rate_delta"], f"{b['hit_rate']} vs {a['hit_rate']} (min delta {c['min_hit_rate_delta']})")
    if a.get("recall") is not None and b.get("recall") is not None:
        check("recall", b["recall"] - a["recall"] >= c["min_recall_delta"], f"{b['recall']} vs {a['recall']} (min delta {c['min_recall_delta']})")
    check("leakage", (b.get("leakage") or 0) <= c["max_leakage"], f"{b.get('leakage')} forbidden chunks returned (max {c['max_leakage']})")
    if a.get("latency_p95_ms") and b.get("latency_p95_ms") is not None:
        limit = max(a["latency_p95_ms"] * c["max_p95_factor"], a["latency_p95_ms"] + c["max_p95_extra_ms"])
        check("latency_p95", b["latency_p95_ms"] <= limit, f"{b['latency_p95_ms']} ms vs limit {round(limit, 1)} ms")
    if a.get("no_evidence_pass") is not None and b.get("no_evidence_pass") is not None:
        check("no_evidence", b["no_evidence_pass"] >= a["no_evidence_pass"], f"{b['no_evidence_pass']} vs {a['no_evidence_pass']}")
    same_dataset = active.get("dataset_version") == candidate.get("dataset_version")
    check("same_dataset", same_dataset, f"{candidate.get('dataset_version')} vs {active.get('dataset_version')}")
    passed = all(x["ok"] for x in checks)
    better = [r["metric"] for r in rows if isinstance(r["active"], (int, float)) and isinstance(r["candidate"], (int, float))
              and r["metric"] in ("hit_rate", "recall", "precision", "mrr", "evidence_coverage", "no_evidence_pass") and r["candidate"] > r["active"]]
    rec = ("Recommended: the candidate meets every acceptance criterion" + (f" and improves {', '.join(better)}" if better else " (no metric improved)")
           if passed else "Not recommended: " + "; ".join(x["check"] + " " + x["detail"] for x in checks if not x["ok"]))
    return {"rows": rows, "checks": checks, "passed": passed, "recommendation": rec, "criteria": c,
            "basis": f"measured on dataset {candidate.get('dataset_version')}: experiments {active.get('id')} (active) and {candidate.get('id')} (candidate)"}
