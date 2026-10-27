#!/usr/bin/env python3
"""Flowise vs LangGraph: send the same questions to both SC Agent Managers and compare them on the same checks.

    python3 scripts/scinsight_compare.py                 # all 40 role questions + 3 guards + one approval cycle per runtime
    python3 scripts/scinsight_compare.py --limit 1       # 1 question per role (quick)

Per question and runtime: specialist chosen (vs expected), facts checked on the calculation the answer cites (never on wording),
paused for approval, latency, errors. Writes docs/scinsight/FLOWISE_VS_LANGGRAPH.md and deploy-evidence/compare-<time>.json.
"""
from __future__ import annotations

import argparse
import json
import re
import statistics
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENV = dict(line.split("=", 1) for line in (ROOT / ".env").read_text().splitlines() if "=" in line and not line.startswith("#"))
FLOWISE, LANGGRAPH, SCI = "http://127.0.0.1:3000", "http://127.0.0.1:8123", "http://127.0.0.1:8000/scinsight"
LABEL_TO_INTENT = {"Factory-Planning": "factory_planning", "Procurement": "procurement", "Warehouse": "warehouse", "Inventory-Optimizer": "inventory_optimizer",
                   "Logistics": "logistics", "Quality": "quality", "Decision-Outcome-Learning": "outcome_learning",
                   "SAP change refused": "sap_write_request", "out of scope": "out_of_scope"}


def http(url: str, body=None, headers=None, method=None, timeout=900):
    req = urllib.request.Request(url, data=json.dumps(body).encode() if body is not None else None,
                                 headers={"Content-Type": "application/json", **(headers or {})}, method=method or ("POST" if body is not None else "GET"))
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, json.loads(r.read() or b"null")
    except urllib.error.HTTPError as e:
        raw = e.read()
        try:
            return e.code, json.loads(raw)
        except ValueError:
            return e.code, {"text": raw.decode(errors="replace")[:300]}
    except Exception as e:  # noqa: BLE001
        return 0, {"text": str(e)[:300]}


def sci(path: str, slot: str = "AGENT", body=None):
    return http(SCI + path, body, {"X-API-Key": ENV[f"SCI_{slot}_KEY"]})


# ----------------------------------------------------------------------------- the two runtimes
def ask_flowise(q: str) -> dict:
    t = time.time()
    status, d = http(f"{FLOWISE}/api/v1/prediction/{ENV['FLOWISE_SCI_SUPERVISOR_ID']}", {"question": q}, {"Authorization": f"Bearer {ENV['FLOWISE_SCI_API_KEY']}"})
    secs = time.time() - t
    labels = [str(n.get("nodeLabel", "")) for n in (d.get("agentFlowExecutedData") or [])] if isinstance(d, dict) else []
    intent = next((v for k, v in LABEL_TO_INTENT.items() for lab in labels if k in lab and ("Specialist" in lab or "Stop" in lab)), "")
    return {"ok": status == 200, "status": status, "secs": secs, "text": d.get("text", "") if isinstance(d, dict) else "", "intent": intent,
            "paused": bool(isinstance(d, dict) and d.get("action")), "handle": {"chat": d.get("chatId"), "node": ((d.get("action") or {}).get("data") or {}).get("nodeId")}}


def ask_langgraph(q: str) -> dict:
    t = time.time()
    status, thread = http(f"{LANGGRAPH}/threads", {})
    tid = (thread or {}).get("thread_id") if isinstance(thread, dict) else None
    if not tid:  # e.g. the LangGraph server is restarting: record the failure, keep going
        return {"ok": False, "status": status, "secs": time.time() - t, "text": "", "intent": "", "paused": False, "handle": {}, "error": "no thread"}
    status, v = http(f"{LANGGRAPH}/threads/{tid}/runs/wait", {"assistant_id": "scinsight_supervisor", "input": {"messages": [{"type": "human", "content": q}]}})
    secs = time.time() - t
    _, st = http(f"{LANGGRAPH}/threads/{tid}/state")
    values = (st or {}).get("values") or (v if isinstance(v, dict) else {})
    paused = "human_approval" in ((st or {}).get("next") or [])
    text = values.get("answer") or ""
    return {"ok": status == 200 and "__error__" not in (v or {}), "status": status, "secs": secs, "text": text, "intent": values.get("intent", ""),
            "paused": paused, "handle": {"thread": tid}, "error": (v or {}).get("__error__") if isinstance(v, dict) else None}


# ----------------------------------------------------------------------------- checks
def path_get(obj, path: str):
    for part in path.split("."):
        if isinstance(obj, list):
            obj = obj[int(part)] if part.isdigit() and int(part) < len(obj) else None
        elif isinstance(obj, dict):
            obj = obj.get(part)
        else:
            return None
    return obj


def check_facts(text: str, expect: dict) -> tuple[bool, str]:
    if "text" in expect:
        ok = expect["text"].lower() in text.lower()
        return ok, "" if ok else f"missing '{expect['text']}'"
    m = re.search(r"Decision calculation: (CALC-[A-Z0-9-]+)", text)
    if not m:
        return False, "no calculation cited"
    status, calc = sci(f"/api/v1/calculations/{m.group(1)}")
    if status != 200:
        return False, f"calculation not found ({status})"
    for path, want in expect.items():
        got = path_get(calc, path)
        same = (isinstance(want, (int, float)) and isinstance(got, (int, float)) and abs(got - want) < 1e-6) or got == want
        if not same:
            return False, f"{path}={got!r} (expected {want!r})"
    return True, ""


def approval_cycle(runtime: str) -> dict:
    """Ask a transfer question, approve as the warehouse manager in the API, resume, expect the verified decision."""
    q = "Warehouse B is low on SPF50 sunscreen. Should we transfer stock from another warehouse?"
    r = ask_flowise(q) if runtime == "flowise" else ask_langgraph(q)
    rec = re.search(r"(REC-[A-Z0-9]+)", r["text"])
    if not (r["paused"] and rec):
        return {"ok": False, "detail": "did not pause with a recommendation"}
    sci(f"/api/v1/decisions/{rec.group(1)}/review", "WAREHOUSE", {"decision": "approve", "explanation": f"comparison run ({runtime})"})
    t = time.time()
    if runtime == "flowise":
        _, d = http(f"{FLOWISE}/api/v1/prediction/{ENV['FLOWISE_SCI_SUPERVISOR_ID']}",
                    {"question": "proceed", "chatId": r["handle"]["chat"], "humanInput": {"type": "proceed", "startNodeId": r["handle"]["node"], "feedback": "ok"}},
                    {"Authorization": f"Bearer {ENV['FLOWISE_SCI_API_KEY']}"})
        text = d.get("text", "")
    else:
        _, v = http(f"{LANGGRAPH}/threads/{r['handle']['thread']}/runs/wait", {"assistant_id": "scinsight_supervisor", "command": {"resume": "proceed"}})
        text = (v or {}).get("answer", "")
    ok = "**approved** by u-warehouse-manager" in text
    return {"ok": ok, "rec": rec.group(1), "resume_secs": round(time.time() - t, 1), "detail": "" if ok else text[-200:]}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=5, help="questions per role (1-5)")
    args = parser.parse_args()
    data = json.loads((ROOT / "data" / "scinsight" / "role_questions.json").read_text())
    cases = [(r["title"], q) for r in data["roles"] for q in r["questions"][: args.limit]] + [("Guard", g) for g in data["guards"]]
    rows = []
    for i, (role, case) in enumerate(cases, 1):
        expected = case["intent"] if isinstance(case["intent"], list) else [case["intent"]]
        row = {"role": role, "q": case["q"], "expected": " or ".join(expected)}
        for name, ask in (("flowise", ask_flowise), ("langgraph", ask_langgraph)):
            try:
                r = ask(case["q"])
            except Exception as e:  # noqa: BLE001 - one broken call must not stop the comparison
                r = {"ok": False, "status": 0, "secs": 0, "text": "", "intent": "", "paused": False, "error": str(e)[:200]}
            facts, why = check_facts(r["text"], case["expect"]) if r["ok"] else (False, f"HTTP {r['status']} {r.get('error') or ''}")
            row[name] = {"ok": r["ok"], "route_ok": r["intent"] in expected, "intent": r["intent"], "facts_ok": facts, "why": why,
                         "paused": r["paused"], "secs": round(r["secs"], 1)}
        f, lg = row["flowise"], row["langgraph"]
        print(f"[{i:2}/{len(cases)}] {role:22} F:{'route' if f['route_ok'] else 'ROUTE?'}/{'facts' if f['facts_ok'] else 'FACTS?'} {f['secs']:5.1f}s | "
              f"LG:{'route' if lg['route_ok'] else 'ROUTE?'}/{'facts' if lg['facts_ok'] else 'FACTS?'} {lg['secs']:5.1f}s | {case['q'][:60]}", flush=True)
        rows.append(row)
    cycles = {name: approval_cycle(name) for name in ("flowise", "langgraph")}
    print("approval cycle:", json.dumps(cycles))
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    (ROOT / "deploy-evidence").mkdir(exist_ok=True)
    (ROOT / "deploy-evidence" / f"compare-{stamp}.json").write_text(json.dumps({"rows": rows, "approval": cycles}, indent=1))
    write_report(rows, cycles, stamp)
    return 0


def write_report(rows: list[dict], cycles: dict, stamp: str) -> None:
    def stats(name: str) -> dict:
        rs = [r[name] for r in rows]
        secs = [r["secs"] for r in rs if r["ok"]]
        return {"route": sum(r["route_ok"] for r in rs), "facts": sum(r["facts_ok"] for r in rs), "errors": sum(not r["ok"] for r in rs),
                "paused": sum(r["paused"] for r in rs), "median": statistics.median(secs) if secs else 0, "mean": statistics.mean(secs) if secs else 0, "n": len(rs)}
    s = {n: stats(n) for n in ("flowise", "langgraph")}
    mark = lambda ok: "✓" if ok else "✗"  # noqa: E731
    lines = [
        "# Flowise vs LangGraph: same SCInsight agent, two runtimes", "",
        f"Run {stamp} UTC on this machine (Qwen 2.5 7B via Ollama, temperature 0). Both runtimes call the same SCInsight API with the same agent key "
        "and use the same prompt files, so differences come from the runtime, not the design. Produced by `scripts/scinsight_compare.py`.", "",
        "| | Flowise (Agentflow V2) | LangGraph (StateGraph) |", "|---|---|---|",
        f"| Right specialist chosen | {s['flowise']['route']}/{s['flowise']['n']} | {s['langgraph']['route']}/{s['langgraph']['n']} |",
        f"| Facts correct (checked on the cited calculation) | {s['flowise']['facts']}/{s['flowise']['n']} | {s['langgraph']['facts']}/{s['langgraph']['n']} |",
        f"| Errors | {s['flowise']['errors']} | {s['langgraph']['errors']} |",
        f"| Paused for approval | {s['flowise']['paused']} | {s['langgraph']['paused']} |",
        f"| Median / mean time per question | {s['flowise']['median']:.1f} s / {s['flowise']['mean']:.1f} s | {s['langgraph']['median']:.1f} s / {s['langgraph']['mean']:.1f} s |",
        f"| Approval cycle (pause → manager approves in API → resume → verified) | {mark(cycles['flowise']['ok'])} | {mark(cycles['langgraph']['ok'])} |", "",
        "## Per question", "", "| Role | Question | Expected | Flowise route · facts · time | LangGraph route · facts · time |", "|---|---|---|---|---|"]
    for r in rows:
        cell = lambda x: f"{mark(x['route_ok'])} {x['intent'] or '—'} · {mark(x['facts_ok'])}{' ' + x['why'] if x['why'] else ''} · {x['secs']} s"  # noqa: E731
        lines.append(f"| {r['role']} | {r['q']} | {r['expected']} | {cell(r['flowise'])} | {cell(r['langgraph'])} |")
    (ROOT / "docs" / "scinsight" / "FLOWISE_VS_LANGGRAPH_RESULTS.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(s))


if __name__ == "__main__":
    raise SystemExit(main())
