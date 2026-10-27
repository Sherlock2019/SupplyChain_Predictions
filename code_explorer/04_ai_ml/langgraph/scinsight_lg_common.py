# ======================================================================================================
# ANNOTATED COPY (learning only: never imported, never executed)
# ORIGINAL FILE: backend/scinsight/lg/common.py
# What this module is: the shared building blocks of the LangGraph mirror of the SCInsight Flowise flows:
#   - the SCInsight API client (agent key from the environment, never from the model),
#   - the Qwen chat model and the prompts exported by Flowise (flowise/prompts/*.md),
#   - Python ports of the Flowise Custom Function JavaScript: SUMMARIZE (summarize), CONTEXT (context), detectCodes
#     (detect_codes), CALL_* (calc_*), POLICY (policy), GATE (gate), GUARD (guard), SAVE (save), VERIFY (verify),
#     WITHDRAW (withdraw). Same rules as flowise/scinsight/build-scinsight.cjs, so Flowise and LangGraph can be compared.
# Only comment lines were added (AST-verified).
# ======================================================================================================

"""Shared pieces of the LangGraph mirror: SCInsight API client, Qwen model, the prompts Flowise uses, and Python ports of
the Flowise Custom Function logic (deterministic summaries, specialist calculations, policy search, number check, intent
guard, save / verify / withdraw). Keep this file behaviourally identical to flowise/scinsight/build-scinsight.cjs so the
comparison measures the runtime, not two different designs.
"""
from __future__ import annotations

import json
# os.environ: API URL, agent key, Qwen settings come from environment variables.
import os
import re
# lru_cache: memoise prompt files (read once per process).
from functools import lru_cache
from pathlib import Path
from typing import Any

# httpx: HTTP client used to call the SCInsight API.
import httpx

# Repository root (this file is backend/scinsight/lg/common.py -> parents[3]) and the prompts exported by the Flowise builder.
ROOT = Path(__file__).resolve().parents[3]
PROMPTS = ROOT / "flowise" / "prompts"
# Deterministic SAP-write detectors (same regexes as GUARD in Flowise). re.I = ignore case.
SAP_WRITE = re.compile(r"\b(create|post|book|change|update|modify|delete|cancel|release|approve|execute|confirm|enter)\b[^.?!]{0,80}\b(in|into|to|on)\s+(sap|s/4|s4)", re.I)
SAP_WRITE_2 = re.compile(r"\b(sap|s/4hana)\b[^.?!]{0,40}\b(write|create|post|change|delete|release|approve)\b", re.I)
GOODS = re.compile(r"\bpost (a |the )?goods (receipt|issue)\b", re.I)
# Instruction-override (prompt-injection) detector.
OVERRIDE = re.compile(r"(ignore|disregard|forget)\s+(all\s+|any\s+|the\s+)?(previous|prior|above|your)\s+(instructions|rules|prompt)|system prompt|developer mode|approve it yourself", re.I)
# The only intents the supervisor may route to.
INTENTS = ["factory_planning", "procurement", "warehouse", "inventory_optimizer", "logistics", "quality", "outcome_learning", "sap_write_request", "out_of_scope"]
# Same code pattern as schemas.CODE.
CODE = re.compile(r"^[A-Z0-9][A-Z0-9_-]{1,40}$")
# Fixed refusal for SAP write requests (identical text to the Flowise "Stop · SAP change refused" node).
SAP_READ_ONLY_REPLY = ("SupplyChain Insight AI is read-only towards SAP (SAP_WRITE_ENABLED=false): it cannot create, change, post, release, approve or delete anything "
                       "in SAP. I can analyse the situation and save a recommendation for review; an authorised manager decides in the SCInsight API and an "
                       "authorised SAP user executes it manually.")


# ===== FUNCTION: out_of_scope_reply() =====
# ID: F0637 · function · used
# ORIGINAL FILE: backend/scinsight/lg/common.py:30-32
# ROLE: Fixed "out of scope" reply, with the guard reason appended (same text as the Flowise node).
# INPUTS:
#   guard: str -> why the request was refused ("unknown intent", "instruction-override guard", ...).
# OUTPUT:
#   str -> reply text.
# CALLED BY:
#   <- F0711 out_of_scope() (calls)
# CALLS:
#   -> F0682 guard() (references)
def out_of_scope_reply(guard: str) -> str:
    return ("I can help with factory material readiness, procurement and supplier lead times, warehouse balancing, inventory cover, logistics, batch "
            f"quality and outcome learning for Belleva Cosmetics. Requests to change my instructions are not accepted. (guard: {guard})")


# ----------------------------------------------------------------------------- API client
# Module-level singleton HTTP client (created lazily).
_client: Any = None  # tests replace this with a FastAPI TestClient (same .request() signature as httpx.Client)


# ===== FUNCTION: client() =====
# ID: F0638 · function · used
# ORIGINAL FILE: backend/scinsight/lg/common.py:39-43
# ROLE: Lazily create the shared httpx client pointing at SCI_API_URL (default: the Docker service scinsight-api:8100).
# INPUTS:
#   none.
# OUTPUT:
#   httpx.Client (or the test client injected into _client).
# CALLED BY:
#   <- F0639 api() (calls)
# CALLS:
#   (none found)
def client():
    # `global` lets the function assign the module-level variable.
    global _client
    if _client is None:
        _client = httpx.Client(base_url=os.environ.get("SCI_API_URL", "http://scinsight-api:8100"), timeout=120)
    return _client


# ===== FUNCTION: api() =====
# ID: F0639 · function · used
# ORIGINAL FILE: backend/scinsight/lg/common.py:46-59
# ROLE: Call the SCInsight API as the agent service (key SCI_AGENT_KEY: read, calculate, create recommendations, never review).
#       Never raises: network/JSON problems become (False, status, {"detail": ...}).
# INPUTS:
#   method: str ("GET"/"POST"), path: str ("/api/v1/..."), body: dict | None (JSON body).
# OUTPUT:
#   tuple[bool, int, dict] -> (ok = status < 400, HTTP status (0 = unreachable), parsed JSON).
# CALLED BY:
#   <- F0629 search_supply_chain_policy() (calls)
#   <- F0656 context() (calls)
#   <- F0669 calc_factory() (calls)
#   <- F0670 calc_procurement() (calls)
#   <- F0671 _balancing() (calls)
#   <- F0674 calc_inventory() (calls)
#   <- F0675 calc_quality() (calls)
#   <- F0676 calc_learning() (calls)
#   <- F0678 policy() (calls)
#   <- F0683 save() (calls)
#   <- F0684 verify() (calls)
#   <- F0685 withdraw() (calls)
# CALLS:
#   -> F0638 client() (calls)
def api(method: str, path: str, body: dict | None = None) -> tuple[bool, int, dict]:
    """Call the SCInsight API with the agent key (role agent_service: read, calculate, create recommendations, never review)."""
    key = os.environ.get("SCI_AGENT_KEY", "")
    if not key:
        return False, 0, {"detail": "SCI_AGENT_KEY is not set for the LangGraph runtime"}
    try:
        # The key travels in the X-API-Key header; the LLM never sees it.
        r = client().request(method, path, json=body, headers={"X-API-Key": key})
    except Exception as e:  # noqa: BLE001
        return False, 0, {"detail": f"SCInsight API unreachable: {str(e)[:200]}"}
    try:
        data = r.json()
    # Non-JSON error page -> keep the first 400 characters as the detail.
    except ValueError:
        data = {"detail": r.text[:400]}
    return r.status_code < 400, r.status_code, data


# ===== FUNCTION: detail() =====
# ID: F0640 · function · used
# ORIGINAL FILE: backend/scinsight/lg/common.py:62-64
# ROLE: Short, printable error detail from an API response (max 400 chars).
# INPUTS:
#   data: dict -> response JSON.
# OUTPUT:
#   str.
# CALLED BY:
#   <- F0656 context() (calls)
#   <- F0669 calc_factory() (calls)
#   <- F0670 calc_procurement() (calls)
#   <- F0671 _balancing() (calls)
#   <- F0674 calc_inventory() (calls)
#   <- F0675 calc_quality() (calls)
#   <- F0676 calc_learning() (calls)
#   <- F0678 policy() (calls)
#   <- F0683 save() (calls)
#   <- F0684 verify() (calls)
#   <- F0685 withdraw() (calls)
# CALLS:
#   (none found)
def detail(data: dict) -> str:
    d = data.get("detail") if isinstance(data, dict) else data
    return (d if isinstance(d, str) else json.dumps(d))[:400]


# ===== FUNCTION: strip() =====
# ID: F0641 · function · used
# ORIGINAL FILE: backend/scinsight/lg/common.py:67-72
# ROLE: Recursively drop "source_records" (record-level lineage) to keep evidence small for the model context.
# INPUTS:
#   o: any JSON value.
# OUTPUT:
#   the same structure without "source_records" keys.
# CALLED BY:
#   <- F0629 search_supply_chain_policy() (calls)
#   <- F0667 _done() (calls)
# CALLS:
#   (none found)
def strip(o):
    if isinstance(o, list):
        return [strip(x) for x in o]
    if isinstance(o, dict):
        return {k: strip(v) for k, v in o.items() if k != "source_records"}
    return o


# ----------------------------------------------------------------------------- model + prompts
# ===== FUNCTION: llm() =====
# ID: F0642 · function · used
# ORIGINAL FILE: backend/scinsight/lg/common.py:76-81
# ROLE: The Qwen chat model through the same OpenAI-compatible endpoint Flowise uses (temperature 0 = deterministic).
# INPUTS:
#   max_tokens: int -> answer length limit (20 for the classifier, 300 extraction, 900 explanation, 1200 chat).
# OUTPUT:
#   langchain_openai.ChatOpenAI instance.
# CALLED BY:
#   <- F0634 assistant() (calls)
#   <- F0693 build_specialist.read_request() (calls)
#   <- F0697 build_specialist.write_answer() (calls)
#   <- F0705 understand() (calls)
# CALLS:
#   (none found)
def llm(max_tokens: int):
    """Qwen through the same OpenAI-compatible endpoint Flowise uses (temperature 0)."""
    # Local import: tests that never call the model do not need langchain_openai loaded.
    from langchain_openai import ChatOpenAI

    return ChatOpenAI(model=os.environ.get("QWEN_MODEL", "qwen2.5-7b-scm"), base_url=os.environ.get("QWEN_BASE_URL", "http://host.docker.internal:11435/v1"),
                      api_key=os.environ.get("QWEN_API_KEY") or "local-qwen", temperature=0, max_tokens=max_tokens, timeout=180, max_retries=1)


# ===== FUNCTION: prompt() =====
# ID: F0643 · function · used
# ORIGINAL FILE: backend/scinsight/lg/common.py:84-86
# ROLE: Read a prompt exported by the Flowise builder (flowise/prompts/<name>.md), cached.
# INPUTS:
#   name: str -> e.g. "supervisor_classifier", "factory_extract".
# OUTPUT:
#   str -> prompt text without the trailing newline.
# @lru_cache(maxsize=64): the result for each name is kept in memory after the first read.
# CALLED BY:
#   <- F0634 assistant() (calls)
#   <- F0644 explain_prompt() (calls)
#   <- F0693 build_specialist.read_request() (calls)
#   <- F0705 understand() (calls)
# CALLS:
#   (none found)
@lru_cache(maxsize=64)
def prompt(name: str) -> str:
    return (PROMPTS / f"{name}.md").read_text(encoding="utf-8").rstrip("\n")


# ===== FUNCTION: explain_prompt() =====
# ID: F0644 · function · used
# ORIGINAL FILE: backend/scinsight/lg/common.py:89-93
# ROLE: (system prompt, user message template) of a specialist's explanation step, split at the exported separator.
# INPUTS:
#   key: str -> specialist key ("factory", "warehouse", ...).
# OUTPUT:
#   tuple[str, str].
# CALLED BY:
#   <- F0697 build_specialist.write_answer() (calls)
# CALLS:
#   -> F0643 prompt() (calls)
def explain_prompt(key: str) -> tuple[str, str]:
    """(system, user template) of a specialist's explanation step, exactly as exported for Flowise."""
    text = prompt(f"{key}_explain")
    system, _, user = text.partition("\n\n--- user message template ---\n")
    return system, user


# ===== FUNCTION: fill() =====
# ID: F0645 · function · used
# ORIGINAL FILE: backend/scinsight/lg/common.py:96-99
# ROLE: Resolve the Flowise template variables used in the shared prompts: {{ question }} and {{ $flow.state.x }}.
# INPUTS:
#   template: str, **values: str -> e.g. question=..., calc_summary=..., policy=..., catalog=...
# OUTPUT:
#   str -> filled prompt.
# CALLED BY:
#   <- F0693 build_specialist.read_request() (calls)
#   <- F0697 build_specialist.write_answer() (calls)
# CALLS:
#   (none found)
def fill(template: str, **values: str) -> str:
    """Resolve the Flowise template variables used in the shared prompts ({{ question }}, {{ $flow.state.x }})."""
    out = template.replace("{{ question }}", values.get("question", ""))
    # re.sub with a function: each {{ $flow.state.NAME }} is replaced by values[NAME] (or "").
    return re.sub(r"\{\{ \$flow\.state\.(\w+) \}\}", lambda m: str(values.get(m.group(1), "")), out)


# ===== FUNCTION: text_of() =====
# ID: F0646 · function · used
# ORIGINAL FILE: backend/scinsight/lg/common.py:102-106
# ROLE: Plain text of a LangChain message (content may be a string or a list of content parts).
# INPUTS:
#   message: a message object or a string.
# OUTPUT:
#   str.
# CALLED BY:
#   <- F0635 evidence_gate() (calls)
#   <- F0636 build_chat() (calls)
#   <- F0689 last_question() (calls)
#   <- F0693 build_specialist.read_request() (calls)
#   <- F0697 build_specialist.write_answer() (calls)
#   <- F0705 understand() (calls)
#   <- F0806 ScriptedModel.invoke() (calls)
#   <- F0812 test_chat_front_door_calls_the_manager_and_checks_numbers() (calls)
# CALLS:
#   (none found)
def text_of(message) -> str:
    # getattr with default: a plain string has no .content -> use the string itself.
    content = getattr(message, "content", message)
    if isinstance(content, list):
        return "".join(part.get("text", "") if isinstance(part, dict) else str(part) for part in content)
    return str(content or "")


# ----------------------------------------------------------------------------- deterministic summaries (port of SUMMARIZE)
# ===== FUNCTION: _list() =====
# ID: F0647 · function · used
# ORIGINAL FILE: backend/scinsight/lg/common.py:110-111
# ROLE: "a; b; c" of f(x) for each x, or "none" for an empty list.
# INPUTS:
#   xs: list | None, f: callable.
# OUTPUT:
#   str.
# CALLED BY:
#   <- F0653 _opt() (calls)
#   <- F0654 summarize() (calls)
# CALLS:
#   (none found)
def _list(xs, f) -> str:
    return "; ".join(f(x) for x in (xs or [])) or "none"


# ===== FUNCTION: _kv() =====
# ID: F0648 · function · used
# ORIGINAL FILE: backend/scinsight/lg/common.py:114-115
# ROLE: "key=value key=value" rendering of a dict (nested values as JSON).
# INPUTS:
#   o: dict.
# OUTPUT:
#   str.
# CALLED BY:
#   <- F0654 summarize() (references)
# CALLS:
#   -> F0649 _fmt() (calls)
def _kv(o: dict) -> str:
    return " ".join(f"{k}={json.dumps(v) if isinstance(v, (dict, list)) else _fmt(v)}" for k, v in (o or {}).items())


# ===== FUNCTION: _fmt() =====
# ID: F0649 · function · used
# ORIGINAL FILE: backend/scinsight/lg/common.py:118-125
# ROLE: Format a value exactly like JavaScript would print it (null, true/false, 20000 instead of 20000.0) so the Python and
#       Flowise summaries are identical and the evidence gate sees the same numbers.
# INPUTS:
#   v: any.
# OUTPUT:
#   str.
# CALLED BY:
#   <- F0635 evidence_gate() (calls)
#   <- F0648 _kv() (calls)
#   <- F0650 _excluded() (calls)
#   <- F0651 _late() (calls)
#   <- F0652 _near() (calls)
#   <- F0653 _opt() (calls)
#   <- F0654 summarize() (calls)
#   <- F0655 _po_unconfirmed() (calls)
#   <- F0669 calc_factory() (calls)
#   <- F0676 calc_learning() (calls)
#   <- F0677 calc_learning.v() (calls)
#   <- F0681 gate() (calls)
# CALLS:
#   (none found)
def _fmt(v) -> str:
    if v is None:
        return "null"
    # bool is checked before int/float because bool is a subclass of int in Python.
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, float) and v.is_integer():
        return str(int(v))
    return str(v)


# ===== FUNCTION: _excluded() =====
# ID: F0650 · function · used
# ORIGINAL FILE: backend/scinsight/lg/common.py:128-129
# ROLE: "batch quantity (reason)" for an excluded batch.
# INPUTS:
#   e: dict -> {batch_id, quantity, reason}.
# OUTPUT:
#   str.
# CALLED BY:
#   <- F0653 _opt() (references)
#   <- F0654 summarize() (references)
# CALLS:
#   -> F0649 _fmt() (calls)
def _excluded(e: dict) -> str:
    return f"{e['batch_id']} {_fmt(e['quantity'])} ({e['reason']})"


# ===== FUNCTION: _late() =====
# ID: F0651 · function · used
# ORIGINAL FILE: backend/scinsight/lg/common.py:132-133
# ROLE: "PO quantity promised date" for a late purchase order.
# INPUTS:
#   p: dict.
# OUTPUT:
#   str.
# CALLED BY:
#   <- F0654 summarize() (references)
# CALLS:
#   -> F0649 _fmt() (calls)
def _late(p: dict) -> str:
    return f"{p['po_id']} {_fmt(p['quantity'])} promised {p['promised_date']}"


# ===== FUNCTION: _near() =====
# ID: F0652 · function · used
# ORIGINAL FILE: backend/scinsight/lg/common.py:136-137
# ROLE: "batch quantity expires date" for a near-expiry batch.
# INPUTS:
#   e: dict.
# OUTPUT:
#   str.
# CALLED BY:
#   <- F0654 summarize() (references)
# CALLS:
#   -> F0649 _fmt() (calls)
def _near(e: dict) -> str:
    return f"{e['batch_id']} {_fmt(e['quantity'])} expires {e['expiry_date']}"


# ===== FUNCTION: _opt() =====
# ID: F0653 · function · used
# ORIGINAL FILE: backend/scinsight/lg/common.py:140-148
# ROLE: One-line rendering of a ranked supply option (rank, option, quantity, lead time + basis, mode, arrival, in time,
#       coverage, cost, feasibility, recommendation, reasons, non-transferable batches).
# INPUTS:
#   o: dict -> option from compare_supply_options.
# OUTPUT:
#   str.
# CALLED BY:
#   <- F0654 summarize() (calls)
# CALLS:
#   -> F0649 _fmt() (calls)
#   -> F0647 _list() (calls)
#   -> F0650 _excluded() (references)
def _opt(o: dict) -> str:
    basis = f" ({o['lead_time_basis']}{', contract ' + _fmt(o['contract_lead_days']) + ' days' if o.get('contract_lead_days') else ''})" if o.get("lead_time_basis") else ""
    reasons = f" - {', '.join(o['reasons'])}" if o.get("reasons") else ""
    nt = f"; not transferable: {_list(o['not_transferable'], _excluded)}" if o.get("not_transferable") else ""
    lead = _fmt(o.get("lead_days")) if o.get("lead_days") is not None else "-"
    cost = _fmt(o.get("cost_eur")) if o.get("cost_eur") is not None else "not estimated"
    return (f"  option {_fmt(o.get('rank'))}: {o.get('option')} - quantity {_fmt(o.get('quantity'))}, lead {lead} days{basis}{', ' + o['mode'] if o.get('mode') else ''}, "
            f"arrival {o.get('arrival_date')}, in time: {_fmt(o.get('in_time'))}, covers need: {_fmt(o.get('covers_need'))}, cost EUR {cost}, "
            f"feasible: {_fmt(o.get('feasible'))}, recommended: {_fmt(bool(o.get('recommended')))}{reasons}{nt}")


# ===== FUNCTION: summarize() =====
# ID: F0654 · function · used
# ORIGINAL FILE: backend/scinsight/lg/common.py:151-198
# ROLE: Deterministic, number-preserving text summary of any stored calculation (by its "kind"); the explanation LLM only
#       rephrases this text, and the evidence gate checks the LLM's numbers against it.
# INPUTS:
#   d: dict -> a calculation returned by the SCInsight API.
# OUTPUT:
#   str -> multi-line summary ending with the proposed actions and the calculation / snapshot provenance.
# CALLED BY:
#   <- F0667 _done() (calls)
# CALLS:
#   -> F0650 _excluded() (references)
#   -> F0649 _fmt() (calls)
#   -> F0647 _list() (calls)
#   -> F0651 _late() (references)
#   -> F0655 _po_unconfirmed() (references)
#   -> F0653 _opt() (calls)
#   -> F0648 _kv() (references)
#   -> F0652 _near() (references)
def summarize(d: dict) -> str:
    lines, k = [], d.get("kind")
    ex = _excluded
    # One branch per calculation kind, mirroring the JavaScript SUMMARIZE.
    if k == "material_readiness":
        lines.append(f"Production order {d.get('production_order_id') or '-'}: {d['sku']} x {_fmt(d['quantity'])} at {d['plant']}, materials needed by {d['need_date']} (BOM {d['bom_version']}). Status: {d['status']}.")
        lines.append("Shortages: " + _list(d.get("shortages"), lambda s: f"{s['material_id']} missing {_fmt(s['missing'])} {s['uom']} (needed {s['required_date']})"))
        for ln in d.get("lines", []):
            # Fully covered line without exclusions -> short form.
            if ln["status"] == "covered" and not ln.get("excluded_stock"):
                lines.append(f"{ln['material_id']}: required {_fmt(ln['required_quantity'])} {ln['uom']}, usable {_fmt(ln['usable'])} - covered")
                continue
            lines.append(f"{ln['material_id']}: required {_fmt(ln['required_quantity'])} {ln['uom']}, usable {_fmt(ln['usable'])}, missing {_fmt(ln['missing'])}; "
                         f"excluded: {_list(ln.get('excluded_stock'), ex)}; late POs: {_list(ln.get('late_purchase_orders'), _late)}; "
                         f"unconfirmed POs: {_list(ln.get('unconfirmed_purchase_orders'), _po_unconfirmed)}")
            # list.extend with a generator: one line per supply option.
            lines.extend(_opt(o) for o in ln.get("supply_options", []))
        if "partial_production_possible" in d:
            lines.append(f"Partial production possible now: {_fmt(d['partial_production_possible'])}.")
        lines.append("Alternatives: " + _list(d.get("alternatives"), _kv))
    elif k == "warehouse_balancing":
        lines.append(f"{d['sku']} balancing towards {d.get('target_warehouse') or 'the lowest-cover warehouse'}. Status: {d['status']}.")
        for p in d.get("positions", []):
            lines.append(f"{p['warehouse']} ({p['name']}): usable {_fmt(p['usable'])}, demand {_fmt(p['daily_demand'])}/day, cover {_fmt(p['days_of_cover'])} days "
                         f"(target {_fmt(p['target_cover_days'])}), projected stock-out {p.get('projected_stockout') or 'none'}; excluded: {_list(p.get('excluded_stock'), ex)}; "
                         f"near expiry: {_list(p.get('near_expiry'), _near)}")
        lines.extend(_opt(o) for o in d.get("options", []))
    elif k == "replenishment":
        lines.append(f"{d['item_id']} at {d['location']}: usable {_fmt(d['usable'])}, quantity to replenish {_fmt(d['quantity'])}, need date {d['need_date']}.")
        lines.extend(_opt(o) for o in d.get("options", []))
    elif k == "quality_check":
        lines.append(f"{d['item_id']} at {d.get('location') or 'all locations'}: on hand {_fmt(d['on_hand'])}, usable {_fmt(d['usable'])}.")
        lines.append("Excluded: " + _list(d.get("excluded"), ex))
        lines.append("Near expiry: " + _list(d.get("near_expiry"), _near))
        lines.append("Expiry risks: " + _list(d.get("expiry_risks"), _kv))
        lines.append("FEFO order of usable batches: " + _list(d.get("fefo_order"), lambda b: f"{b['batch_id']} {_fmt(b.get('quantity', ''))}" if isinstance(b, dict) else str(b)))
        if d.get("note"):
            lines.append(d["note"])
    elif k == "lead_time_estimate":
        e = d.get("estimate", {})
        lines.append(f"{d['supplier_id']} ({d['supplier']}) {d.get('material_id') or ''}: predicted lead time {_fmt(d['predicted_lead_time_days'])} days ({d['basis']}, "
                     f"model {d['model_version']}); receipts {_fmt(e.get('receipts'))}, mean {_fmt(e.get('estimate_days'))}, p90 {_fmt(e.get('p90_days'))}, "
                     f"min {_fmt(e.get('min_days'))}, max {_fmt(e.get('max_days'))}, contract {_fmt(e.get('contract_days'))} days, on-time rate {_fmt(e.get('on_time_rate'))}.")
    elif k == "demand_forecast":
        b = d.get("backtest", {})
        lines.append(f"{d['sku']} at {d['warehouse']}: forecast {_fmt(d['total'])} units over {len(d.get('forecast', []))} days ({d['method']}, {d['model_version']}); "
                     f"back-test over {_fmt(b.get('holdout_days'))} days: WAPE {_fmt(b.get('wape_pct'))}% vs naive {_fmt(b.get('naive_same_weekday_wape_pct'))}%.")
    # Every kind ends with the proposed actions and the provenance line.
    lines.append("Proposed actions: " + _list(d.get("proposed_actions"), _kv))
    pv = d.get("provenance") or {}
    lines.append(f"Calculation {d['calculation_id']} ({k}) on SAP snapshot {pv.get('snapshot_id')} as of {pv.get('as_of_date')}{', synthetic data' if pv.get('synthetic') else ''}.")
    return "\n".join(lines)


# ===== FUNCTION: _po_unconfirmed() =====
# ID: F0655 · function · used
# ORIGINAL FILE: backend/scinsight/lg/common.py:201-202
# ROLE: "PO quantity promised date (status)" for an unconfirmed purchase order.
# INPUTS:
#   p: dict.
# OUTPUT:
#   str.
# CALLED BY:
#   <- F0654 summarize() (references)
# CALLS:
#   -> F0649 _fmt() (calls)
def _po_unconfirmed(p: dict) -> str:
    return f"{p['po_id']} {_fmt(p['quantity'])} promised {p['promised_date']} ({p['status']})"


# ----------------------------------------------------------------------------- context, calculations, policy (ports of CONTEXT / CALL_* / POLICY)
# ===== FUNCTION: context() =====
# ID: F0656 · function · used
# ORIGINAL FILE: backend/scinsight/lg/common.py:206-215
# ROLE: Port of the Flowise CONTEXT step: POST /api/v1/context/validate and build the text catalog of identifiers for the prompts.
# INPUTS:
#   session: str -> LangGraph thread id (sanitised to safe characters, max 120).
# OUTPUT:
#   dict -> {"ctx_ok", "ctx_message", "snapshot_id", "catalog"} (or ctx_ok False + message).
# CALLED BY:
#   <- F0691 build_specialist.check_access() (calls)
#   <- F0703 check_access() (calls)
# CALLS:
#   -> F0639 api() (calls)
#   -> F0118 create_app.validate_context() (http_request)
#   -> F0640 detail() (calls)
def context(session: str) -> dict:
    sid = re.sub(r"[^A-Za-z0-9_.:-]", "", session or "")[:120]
    ok, status, d = api("POST", "/api/v1/context/validate", {"session_id": sid if len(sid) >= 3 else "langgraph-session"})
    if not ok:
        return {"ctx_ok": False, "ctx_message": f"SCInsight context check failed (HTTP {status}): {detail(d)}. No analysis was run."}
    c = d.get("catalog", {})
    # One "SECTION: CODE = name; CODE = name" line per catalog section (parsed back by _catalog / detect_codes).
    catalog = "\n".join([f"BUSINESS DATE (SAP snapshot as of): {d['snapshot_as_of']}", "PRODUCTS: " + "; ".join(c.get("products", [])),
                         "MATERIALS: " + "; ".join(c.get("materials", [])), "LOCATIONS: " + "; ".join(c.get("locations", [])),
                         "SUPPLIERS: " + "; ".join(c.get("suppliers", [])), "PRODUCTION ORDERS: " + "; ".join(c.get("production_orders", []))])
    return {"ctx_ok": True, "ctx_message": "", "snapshot_id": d["snapshot_id"], "catalog": catalog}


# Words ignored when matching catalog names, and the pattern of hyphenated codes (e.g. SUN-SPF50-100).
_STOP = {"THE", "AND", "FOR", "WITH", "SYNTHETIC", "BASE"}
_TOKEN = re.compile(r"[A-Z0-9]+(?:-[A-Z0-9]+)+")


# ===== FUNCTION: _catalog() =====
# ID: F0657 · function · used
# ORIGINAL FILE: backend/scinsight/lg/common.py:222-227
# ROLE: Parse the catalog text back into {section: [(code, label), ...]}.
# INPUTS:
#   catalog: str.
# OUTPUT:
#   dict[str, list[tuple[str, str]]].
# CALLED BY:
#   <- F0659 detect_codes() (calls)
# CALLS:
#   (none found)
def _catalog(catalog: str) -> dict[str, list[tuple[str, str]]]:
    out = {}
    for line in (catalog or "").splitlines():
        name, _, rest = line.partition(": ")
        # split(" = ", 1): only the first " = " separates code and name.
        out[name] = [tuple(p.split(" = ", 1)) for p in rest.split("; ") if " = " in p]
    return out


# ===== FUNCTION: _name_hits() =====
# ID: F0658 · function · used
# ORIGINAL FILE: backend/scinsight/lg/common.py:230-234
# ROLE: How many meaningful words of a catalog name appear in the question (prefix match handles plurals); needs >= 2 hits
#       (or all words when the name has one word) to count.
# INPUTS:
#   label: str (catalog name), words: list[str] (uppercase question words).
# OUTPUT:
#   int -> number of hits, or 0 when below the threshold.
# CALLED BY:
#   <- F0659 detect_codes() (calls)
# CALLS:
#   (none found)
def _name_hits(label: str, words: list[str]) -> int:
    """How many meaningful words of a catalog name appear in the question (prefix match handles plurals)."""
    # Remove "(...)" parts, keep words of >= 3 letters/digits starting with a letter, drop stop words.
    tokens = [t for t in re.findall(r"[A-Z][A-Z0-9]{2,}", re.sub(r"\(.*?\)", "", label.upper())) if t not in _STOP and t != "ML"]
    hits = sum(1 for t in tokens if any(w.startswith(t) for w in words))
    return hits if tokens and hits >= min(2, len(tokens)) else 0


# ===== FUNCTION: detect_codes() =====
# ID: F0659 · function · used
# ORIGINAL FILE: backend/scinsight/lg/common.py:237-275
# ROLE: Deterministic identifier detection from the question: explicit codes first, then catalog names; also locations (in
#       order of appearance), the target warehouse ("to WH-B" / "to warehouse B"), a quantity and a date. Codes found here
#       win over the LLM's extraction.
# INPUTS:
#   question: str, catalog: str (from context()).
# OUTPUT:
#   dict -> subset of {production_order_id, sku, material_id, supplier_id, item_id, location, target_warehouse, quantity, need_date}.
# EXAMPLE: "Can we produce PRD-1001 on time?" -> {"production_order_id": "PRD-1001", ...}.
# CALLED BY:
#   <- F0694 build_specialist.calculate() (calls)
#   <- F0814 test_identifiers_are_detected_by_code_before_the_model() (calls)
# CALLS:
#   -> F0657 _catalog() (calls)
#   -> F0660 detect_codes.first() (calls)
#   -> F0658 _name_hits() (calls)
def detect_codes(question: str, catalog: str) -> dict:
    """Deterministic identifier detection (codes first, then catalog names). Same rules as detectCodes() in the Flowise flows."""
    q = (question or "").upper()
    sec = _catalog(catalog)
    # Hyphenated tokens present in the question.
    in_q = set(_TOKEN.findall(q))
    words = re.findall(r"[A-Z0-9][A-Z0-9/]*", q)

    # ===== FUNCTION: detect_codes.first() =====
    # ID: F0660 · nested · used
    # ORIGINAL FILE: backend/scinsight/lg/common.py:244-250
    # ROLE: Best-scoring catalog entry of a section; ties keep the first entry.
    # INPUTS:
    #   section: str, score: callable(code, label) -> number.
    # OUTPUT:
    #   str -> code, or "" when no entry scores above 0.
    # CALLED BY:
    #   <- F0659 detect_codes() (calls)
    # CALLS:
    #   (none found)
    def first(section: str, score) -> str:  # highest score; ties keep the first catalog entry (same as the JavaScript port)
        best = (0, "")
        for code, label in sec.get(section, []):
            s = int(score(code, label))
            if s > best[0]:
                best = (s, code)
        return best[1]

    # First catalog code of a section that literally appears in the question.
    by_code = lambda section: next((c for c, _ in sec.get(section, []) if c in in_q), "")  # noqa: E731
    product = by_code("PRODUCTS") or first("PRODUCTS", lambda c, label: _name_hits(label, words))
    material = by_code("MATERIALS") or first("MATERIALS", lambda c, label: _name_hits(label, words))
    # Supplier: "supplier A" or the first word of its name (e.g. "ALPINE").
    supplier = by_code("SUPPLIERS") or first("SUPPLIERS", lambda c, label: (re.search(rf"\bSUPPLIER {c.split('-')[-1]}\b", q) is not None)
                                             or (label.split()[0].upper() in words))
    places = []  # locations in the order they appear in the question
    for code, label in sec.get("LOCATIONS", []):
        head = label.split(" (")[0].upper()  # e.g. "WAREHOUSE A — PARIS", "LYON FACTORY"
        # Names to look for: the code, plus "WAREHOUSE A" (before the dash) or the first word ("LYON").
        names = [code] + ([head.split(" — ")[0]] if " — " in head else head.split()[:1])
        pos = [q.find(n) for n in names if re.search(rf"\b{re.escape(n)}\b", q)]
        if pos:
            places.append((min(pos), code))
    # Sort by position in the question and keep only the codes.
    places = [c for _, c in sorted(places)]
    # Target = a location preceded by TO / INTO / REACH / RESUPPLY / COVER, else the first warehouse mentioned.
    target = next((c for c in places if re.search(rf"\b(TO|INTO|REACH|RESUPPLY|COVER)\s+(WAREHOUSE {c[-1]}|{c})\b", q)), "") \
        or next((c for c in places if c.startswith("WH-")), "")
    # Remove codes and dates before looking for a quantity, so "SPF50" or "2026" are not read as quantities.
    clean = re.sub(r"\d{4}-\d{2}-\d{2}", " ", _TOKEN.sub(" ", q))
    # Quantity: "20,000" / "20 000" / or a plain number of >= 3 digits not glued to letters or dots.
    qty = re.search(r"(?<![\w.])(\d{1,3}(?:[ ,]\d{3})+|\d{3,})(?![\w.])", clean)
    date = re.search(r"\d{4}-\d{2}-\d{2}", q)
    found = {"production_order_id": by_code("PRODUCTION ORDERS"), "sku": product, "material_id": material, "supplier_id": supplier,
             "item_id": product or material, "location": places[0] if places else "", "target_warehouse": target,
             "quantity": re.sub(r"[ ,]", "", qty.group(1)) if qty else "", "need_date": date.group(0) if date else ""}
    if material and by_code("MATERIALS"):  # an explicit material code beats a product matched by name
        found["item_id"] = material
    # Keep only non-empty values.
    return {k: v for k, v in found.items() if v}


# ===== FUNCTION: merge_identifiers() =====
# ID: F0661 · function · used
# ORIGINAL FILE: backend/scinsight/lg/common.py:278-280
# ROLE: Combine identifiers: code-detected values win; the LLM extraction only fills the gaps.
# INPUTS:
#   detected: dict (detect_codes), extracted: dict (parse_extracted).
# OUTPUT:
#   dict -> merged identifiers.
# CALLED BY:
#   <- F0694 build_specialist.calculate() (calls)
#   <- F0814 test_identifiers_are_detected_by_code_before_the_model() (calls)
# CALLS:
#   -> F0663 _val() (calls)
def merge_identifiers(detected: dict, extracted: dict) -> dict:
    """Code-detected identifiers win; the model only fills what code could not find."""
    # Later keys win in a dict literal: {**extracted_clean, **detected}.
    return {**{k: v for k, v in (extracted or {}).items() if _val(extracted, k)}, **detected}


# ===== FUNCTION: parse_extracted() =====
# ID: F0662 · function · used
# ORIGINAL FILE: backend/scinsight/lg/common.py:283-294
# ROLE: Lenient parse of the LLM identifier extraction: first {...} object, NONE/null tolerated, per-key regex fallback.
# INPUTS:
#   text: str -> raw model output.
# OUTPUT:
#   dict -> key -> string value (possibly empty).
# CALLED BY:
#   <- F0693 build_specialist.read_request() (calls)
# CALLS:
#   (none found)
def parse_extracted(text: str) -> dict:
    """Lenient JSON parse of the identifier extraction (bare NONE / null tolerated, per-key fallback)."""
    # Non-greedy match of the first flat JSON object.
    m = re.search(r"\{[\s\S]*?\}", text or "")
    if not m:
        return {}
    try:
        # Replace bare none/null/n/a/undefined values with "" so json.loads accepts them.
        o = json.loads(re.sub(r":\s*(none|null|n/a|undefined)\s*(?=[,}\n])", ': ""', m.group(0), flags=re.I))
        if isinstance(o, dict):
            return o
    except ValueError:
        pass
    # Fallback: pull "key": value pairs one by one.
    return {k: v.strip() for k, v in re.findall(r'"([a-z_]+)"\s*:\s*"?([^",}\n]*)"?', m.group(0), flags=re.I)}


# ===== FUNCTION: _val() =====
# ID: F0663 · function · used
# ORIGINAL FILE: backend/scinsight/lg/common.py:297-300
# ROLE: Clean string value of a key; placeholders such as none / null / unknown / n/a become "".
# INPUTS:
#   x: dict, k: str.
# OUTPUT:
#   str.
# CALLED BY:
#   <- F0661 merge_identifiers() (calls)
#   <- F0664 _code() (calls)
#   <- F0665 _num() (calls)
#   <- F0666 _day() (calls)
# CALLS:
#   (none found)
def _val(x: dict, k: str) -> str:
    v = x.get(k)
    s = "" if v is None else str(v).strip()
    return "" if re.fullmatch(r"(none|null|unknown|n/a|undefined)?", s, re.I) else s


# ===== FUNCTION: _code() =====
# ID: F0664 · function · used
# ORIGINAL FILE: backend/scinsight/lg/common.py:303-305
# ROLE: Value as an uppercase code without spaces, only if it matches the CODE pattern (else "").
# INPUTS:
#   x: dict, k: str.
# OUTPUT:
#   str.
# CALLED BY:
#   <- F0669 calc_factory() (calls)
#   <- F0670 calc_procurement() (calls)
#   <- F0671 _balancing() (calls)
#   <- F0674 calc_inventory() (calls)
#   <- F0675 calc_quality() (calls)
# CALLS:
#   -> F0663 _val() (calls)
def _code(x: dict, k: str) -> str:
    s = re.sub(r"\s+", "", _val(x, k).upper())
    return s if CODE.fullmatch(s) else ""


# ===== FUNCTION: _num() =====
# ID: F0665 · function · used
# ORIGINAL FILE: backend/scinsight/lg/common.py:308-313
# ROLE: Value as a positive number ("20,000" -> 20000.0), else None.
# INPUTS:
#   x: dict, k: str.
# OUTPUT:
#   float | None.
# CALLED BY:
#   <- F0669 calc_factory() (calls)
#   <- F0670 calc_procurement() (calls)
#   <- F0674 calc_inventory() (calls)
# CALLS:
#   -> F0663 _val() (calls)
def _num(x: dict, k: str) -> float | None:
    try:
        n = float(_val(x, k).replace(",", "").replace(" ", ""))
        return n if n > 0 else None
    except ValueError:
        return None


# ===== FUNCTION: _day() =====
# ID: F0666 · function · used
# ORIGINAL FILE: backend/scinsight/lg/common.py:316-318
# ROLE: Value as an ISO date string YYYY-MM-DD, else "".
# INPUTS:
#   x: dict, k: str.
# OUTPUT:
#   str.
# CALLED BY:
#   <- F0669 calc_factory() (calls)
#   <- F0670 calc_procurement() (calls)
#   <- F0674 calc_inventory() (calls)
# CALLS:
#   -> F0663 _val() (calls)
def _day(x: dict, k: str) -> str:
    s = _val(x, k)
    return s if re.fullmatch(r"\d{4}-\d{2}-\d{2}", s) else ""


# ===== FUNCTION: _done() =====
# ID: F0667 · function · used
# ORIGINAL FILE: backend/scinsight/lg/common.py:321-325
# ROLE: Successful calculation state for the graph (port of OUTCOME.done): ids, summary of main + extra results, evidence JSON.
# INPUTS:
#   main: dict (main calculation), extra: list[dict] (supporting calculations), message: str (optional note).
# OUTPUT:
#   dict -> calc_ok True, calc_id, calc_kind, snapshot_id, calc_has_actions, calc_summary, calc_evidence, calc_message "".
# CALLED BY:
#   <- F0669 calc_factory() (calls)
#   <- F0670 calc_procurement() (calls)
#   <- F0671 _balancing() (calls)
#   <- F0674 calc_inventory() (calls)
#   <- F0675 calc_quality() (calls)
# CALLS:
#   -> F0654 summarize() (calls)
#   -> F0641 strip() (calls)
def _done(main: dict, extra: list[dict], message: str = "") -> dict:
    summary = "\n\n".join([summarize(main), *(summarize(e) for e in extra), *([message] if message else [])])
    return {"calc_ok": True, "calc_id": main["calculation_id"], "calc_kind": main["kind"], "snapshot_id": (main.get("provenance") or {}).get("snapshot_id", ""),
            "calc_has_actions": bool(main.get("proposed_actions")), "calc_summary": summary, "calc_evidence": json.dumps([strip(main), *[strip(e) for e in extra]]),
            "calc_message": ""}


# ===== FUNCTION: _fail() =====
# ID: F0668 · function · used
# ORIGINAL FILE: backend/scinsight/lg/common.py:328-329
# ROLE: Failed / incomplete calculation state (port of OUTCOME.fail): the message is shown to the user ("which product?").
# INPUTS:
#   message: str.
# OUTPUT:
#   dict -> calc_ok False + calc_message.
# CALLED BY:
#   <- F0669 calc_factory() (calls)
#   <- F0670 calc_procurement() (calls)
#   <- F0671 _balancing() (calls)
#   <- F0674 calc_inventory() (calls)
#   <- F0675 calc_quality() (calls)
# CALLS:
#   (none found)
def _fail(message: str) -> dict:
    return {"calc_ok": False, "calc_id": "", "calc_kind": "", "calc_has_actions": False, "calc_summary": "", "calc_evidence": "", "calc_message": message}


# ===== FUNCTION: calc_factory() =====
# ID: F0669 · function · used
# ORIGINAL FILE: backend/scinsight/lg/common.py:332-349
# ROLE: Factory specialist calculation (port of CALL_FACTORY): production order, or SKU + quantity + date, or resolve the single
#       production order of a SKU from SAP; then POST /api/v1/optimizer/material-readiness.
# INPUTS:
#   x: dict (identifiers), question: str (unused here, same signature as the others).
# OUTPUT:
#   dict -> _done(...) or _fail(...).
# CALLED BY:
#   (none found)
# CALLS:
#   -> F0664 _code() (calls)
#   -> F0665 _num() (calls)
#   -> F0666 _day() (calls)
#   -> F0639 api() (calls)
#   -> F0121 create_app.sap_production_orders() (http_request)
#   -> F0125 create_app.sap_write_blocked() (http_request)
#   -> F0668 _fail() (calls)
#   -> F0649 _fmt() (calls)
#   -> F0126 create_app.material_readiness() (http_request)
#   -> F0667 _done() (calls)
#   -> F0640 detail() (calls)
def calc_factory(x: dict, question: str) -> dict:
    po, sku, qty, need = _code(x, "production_order_id"), _code(x, "sku"), _num(x, "quantity"), _day(x, "need_date")
    req: dict = {}
    if po.startswith("PRD-"):
        req["production_order_id"] = po
    elif sku and qty and need:
        req.update(sku=sku, quantity=qty, need_date=need)
    elif sku:  # resolve the production order deterministically from SAP instead of letting the model pick one
        ok, _, orders = api("GET", f"/api/v1/sap/production-orders?sku={sku}")
        items = [o for o in (orders.get("items", []) if ok else []) if not qty or float(o["quantity"]) == qty]
        if len(items) != 1:
            # Ambiguous or none -> ask the user instead of guessing.
            return _fail(f"Several production orders exist for {sku}: " + ", ".join(f"{o['order_id']} ({_fmt(o['quantity'])} from {o['start_date']})" for o in items) + ". Which one should I check?"
                         if items else f"No production order found for {sku}{' with quantity ' + _fmt(qty) if qty else ''}. Give a production order (PRD-...) or SKU, quantity and need date (YYYY-MM-DD).")
        req["production_order_id"] = items[0]["order_id"]
    else:
        return _fail("To check material readiness I need a production order (PRD-...) or a finished-good SKU with quantity and need date (YYYY-MM-DD).")
    ok, status, d = api("POST", "/api/v1/optimizer/material-readiness", req)
    return _done(d, []) if ok else _fail(f"Material readiness could not be calculated (HTTP {status}): {detail(d)}")


# ===== FUNCTION: calc_procurement() =====
# ID: F0670 · function · used
# ORIGINAL FILE: backend/scinsight/lg/common.py:352-373
# ROLE: Procurement specialist calculation (port of CALL_PROCUREMENT): ranked purchase options when material + quantity + date are
#       known, plus supplier lead-time reliability for the named supplier or the (max 4) suppliers of the material.
# INPUTS:
#   x: dict, question: str.
# OUTPUT:
#   dict -> _done(main, extra, note) or _fail.
# CALLED BY:
#   (none found)
# CALLS:
#   -> F0664 _code() (calls)
#   -> F0665 _num() (calls)
#   -> F0666 _day() (calls)
#   -> F0639 api() (calls)
#   -> F0128 create_app.replenishment() (http_request)
#   -> F0668 _fail() (calls)
#   -> F0640 detail() (calls)
#   -> F0124 create_app.sap_suppliers() (http_request)
#   -> F0125 create_app.sap_write_blocked() (http_request)
#   -> F0130 create_app.forecast_lead_time() (http_request)
#   -> F0667 _done() (calls)
def calc_procurement(x: dict, question: str) -> dict:
    material, supplier, qty, need = _code(x, "material_id"), _code(x, "supplier_id"), _num(x, "quantity"), _day(x, "need_date")
    loc = _code(x, "location") or "FAC-1"
    main, extra = None, []
    if material and qty and need:
        ok, status, d = api("POST", "/api/v1/optimizer/replenishment", {"item_id": material, "location": loc, "quantity": qty, "need_date": need})
        if not ok:
            return _fail(f"Supplier options could not be calculated (HTTP {status}): {detail(d)}")
        main = d
    suppliers = [supplier] if supplier else []
    if not suppliers and material:
        ok, _, s = api("GET", "/api/v1/sap/suppliers")
        # Suppliers whose items include the material (slice [:4] limits API calls).
        suppliers = [x2["supplier_id"] for x2 in (s.get("items", []) if ok else []) if any(i["material_id"] == material for i in x2.get("items", []))][:4]
    for sup in suppliers:
        ok, _, d = api("POST", "/api/v1/forecast/lead-time", {"supplier_id": sup, "material_id": material} if material else {"supplier_id": sup})
        if ok:
            extra.append(d)
    if not main and not extra:
        return _fail("Name a material (e.g. PUMP-DISP-24) and/or a supplier (SUP-...); add quantity and need date (YYYY-MM-DD) to get ranked purchase options.")
    if not main:
        # No purchase calculation: the first lead-time estimate becomes the main result.
        main = extra.pop(0)
    return _done(main, extra, "No purchase quantity and need date were given, so no purchase request is proposed." if main["kind"] == "lead_time_estimate" else "")


# ===== FUNCTION: _balancing() =====
# ID: F0671 · function · used
# ORIGINAL FILE: backend/scinsight/lg/common.py:376-381
# ROLE: Shared warehouse/logistics calculation: POST /api/v1/optimizer/warehouse-balancing for a SKU (and optional target).
# INPUTS:
#   x: dict, what: str ("Warehouse balancing" | "Transport options") -> wording of the messages.
# OUTPUT:
#   dict -> _done or _fail.
# CALLED BY:
#   <- F0672 calc_warehouse() (calls)
#   <- F0673 calc_logistics() (calls)
# CALLS:
#   -> F0664 _code() (calls)
#   -> F0668 _fail() (calls)
#   -> F0639 api() (calls)
#   -> F0127 create_app.warehouse_balancing() (http_request)
#   -> F0667 _done() (calls)
#   -> F0640 detail() (calls)
def _balancing(x: dict, what: str) -> dict:
    sku, target = _code(x, "sku"), _code(x, "target_warehouse")
    if not sku:
        return _fail("Which product (SKU) should I balance across warehouses A, B and C?" if what == "Warehouse balancing" else "Which product (SKU) should be moved, and to which warehouse?")
    ok, status, d = api("POST", "/api/v1/optimizer/warehouse-balancing", {"sku": sku, "target_warehouse": target} if target else {"sku": sku})
    return _done(d, []) if ok else _fail(f"{what} could not be calculated (HTTP {status}): {detail(d)}")


# ===== FUNCTION: calc_warehouse() =====
# ID: F0672 · function · used
# ORIGINAL FILE: backend/scinsight/lg/common.py:384-385
# ROLE: Warehouse specialist calculation (port of CALL_WAREHOUSE).
# INPUTS:
#   x: dict, question: str.
# OUTPUT:
#   dict.
# CALLED BY:
#   (none found)
# CALLS:
#   -> F0671 _balancing() (calls)
def calc_warehouse(x: dict, question: str) -> dict:
    return _balancing(x, "Warehouse balancing")


# ===== FUNCTION: calc_logistics() =====
# ID: F0673 · function · used
# ORIGINAL FILE: backend/scinsight/lg/common.py:388-389
# ROLE: Logistics specialist calculation (port of CALL_LOGISTICS): same balancing endpoint, transport wording.
# INPUTS:
#   x: dict, question: str.
# OUTPUT:
#   dict.
# CALLED BY:
#   (none found)
# CALLS:
#   -> F0671 _balancing() (calls)
def calc_logistics(x: dict, question: str) -> dict:
    return _balancing(x, "Transport options")


# ===== FUNCTION: calc_inventory() =====
# ID: F0674 · function · used
# ORIGINAL FILE: backend/scinsight/lg/common.py:392-406
# ROLE: Inventory specialist calculation (port of CALL_INVENTORY): replenishment, plus a 14-day demand forecast when the location
#       (or the balancing target) is a warehouse.
# INPUTS:
#   x: dict, question: str.
# OUTPUT:
#   dict -> _done(replenishment, [forecast]) or _fail.
# CALLED BY:
#   (none found)
# CALLS:
#   -> F0664 _code() (calls)
#   -> F0665 _num() (calls)
#   -> F0666 _day() (calls)
#   -> F0668 _fail() (calls)
#   -> F0639 api() (calls)
#   -> F0128 create_app.replenishment() (http_request)
#   -> F0640 detail() (calls)
#   -> F0129 create_app.forecast_demand() (http_request)
#   -> F0667 _done() (calls)
def calc_inventory(x: dict, question: str) -> dict:
    item, loc, qty, need = _code(x, "item_id"), _code(x, "location"), _num(x, "quantity"), _day(x, "need_date")
    if not item:
        return _fail("Which product or material should I check (code or name)?")
    # Optional keys are added only when present (dict unpacking of conditional dicts).
    req = {"item_id": item, **({"location": loc} if loc else {}), **({"quantity": qty} if qty else {}), **({"need_date": need} if need else {})}
    ok, status, d = api("POST", "/api/v1/optimizer/replenishment", req)
    if not ok:
        return _fail(f"Replenishment could not be calculated (HTTP {status}): {detail(d)}")
    extra = []
    wh = loc or d.get("target_warehouse") or ""
    if wh.startswith("WH-"):
        ok, _, f = api("POST", "/api/v1/forecast/demand", {"sku": item, "warehouse": wh, "horizon_days": 14})
        if ok:
            extra.append(f)
    return _done(d, extra)


# ===== FUNCTION: calc_quality() =====
# ID: F0675 · function · used
# ORIGINAL FILE: backend/scinsight/lg/common.py:409-414
# ROLE: Quality specialist calculation (port of CALL_QUALITY): POST /api/v1/quality/check-stock.
# INPUTS:
#   x: dict, question: str.
# OUTPUT:
#   dict.
# CALLED BY:
#   (none found)
# CALLS:
#   -> F0664 _code() (calls)
#   -> F0668 _fail() (calls)
#   -> F0639 api() (calls)
#   -> F0131 create_app.quality_check() (http_request)
#   -> F0667 _done() (calls)
#   -> F0640 detail() (calls)
def calc_quality(x: dict, question: str) -> dict:
    item, loc = _code(x, "item_id"), _code(x, "location")
    if not item:
        return _fail("Which product or material (and location) should I check?")
    ok, status, d = api("POST", "/api/v1/quality/check-stock", {"item_id": item, "location": loc} if loc else {"item_id": item})
    return _done(d, []) if ok else _fail(f"Quality check could not be calculated (HTTP {status}): {detail(d)}")


# ===== FUNCTION: calc_learning() =====
# ID: F0676 · function · used
# ORIGINAL FILE: backend/scinsight/lg/common.py:417-467
# ROLE: Outcome-learning report (port of CALL_LEARNING): for up to 3 REC ids in the question, read the recommendation, reconcile it
#       when executed, then append the verified learning metrics. Fully deterministic (no LLM rewording).
# INPUTS:
#   x: dict (unused), question: str (REC ids are read from it).
# OUTPUT:
#   dict -> calc_ok True, calc_kind "learning", calc_summary = the report, calc_evidence = JSON of all API answers.
# CALLED BY:
#   (none found)
# CALLS:
#   -> F0639 api() (calls)
#   -> F0137 create_app.get_decision() (http_request)
#   -> F0138 create_app.review() (http_request)
#   -> F0139 create_app.withdraw() (http_request)
#   -> F0140 create_app.sap_execution() (http_request)
#   -> F0640 detail() (calls)
#   -> F0649 _fmt() (calls)
#   -> F0141 create_app.reconcile() (http_request)
#   -> F0142 create_app.learning_metrics() (http_request)
#   -> F0677 calc_learning.v() (calls)
def calc_learning(x: dict, question: str) -> dict:
    # dict.fromkeys keeps order and removes duplicates; [:3] caps the number of ids.
    ids = list(dict.fromkeys(re.findall(r"REC-[A-Z0-9-]{4,40}", question.upper())))[:3]
    lines, ev = [], []
    for rid in ids:
        ok, status, rec = api("GET", f"/api/v1/decisions/{rid}")
        if not ok:
            lines.append(f"{rid}: not readable (HTTP {status}): {detail(rec)}")
            continue
        # Last review (or None): `(list or [None])[-1]`.
        p, rv = rec.get("prediction") or {}, (rec.get("reviews") or [None])[-1]
        sx = ", ".join(f"{s['sap_document']} ({s['doc_type']})" for s in rec.get("sap_execution", [])) or "none recorded"
        lines.append(f"{rid} \"{rec['title']}\": status {rec['status']}; prediction {p.get('metric', 'none')} = {_fmt(p.get('predicted', '-'))}; "
                     f"review: {rv['decision'] + ' by ' + rv['reviewer_id'] if rv else 'none'}; SAP execution: {sx}.")
        ev.append(rec)
        if rec["status"] == "executed":
            ok, status, r = api("POST", "/api/v1/outcomes/reconcile", {"recommendation_id": rid})
            if not ok:
                lines.append(f"  reconciliation failed (HTTP {status}): {detail(r)}")
                continue
            ev.append(r)
            if r.get("status") == "already_reconciled":
                o = r.get("learning_record") or {}
                lines.append(f"  already reconciled earlier: learning record {o.get('id')}, signed error {_fmt(o.get('signed_error'))}, absolute error {_fmt(o.get('abs_error'))}, outcome {o.get('outcome_status')}.")
            elif r.get("error"):
                e = r["error"]
                lines.append(f"  outcome {r['status']}: predicted {_fmt(e['predicted'])} days, actual {_fmt(e['actual'])} days (goods receipt {r['source_document']} on {r['received_date']}); "
                             f"signed error {_fmt(e['signed_error'])}, absolute error {_fmt(e['absolute_error'])}, percentage error {_fmt(e['percentage_error'])}%; "
                             f"learning record {r['learning_record_id']}, approved for training: {_fmt(r['approved_for_training'])}.")
            else:
                lines.append(f"  outcome status {r.get('status')}: {r.get('reason') or r.get('detail') or ''}")
        else:
            lines.append("  not executed in SAP yet, so there is no outcome to verify.")
    ok, status, m = api("GET", "/api/v1/learning/metrics")
    if ok:
        ev.append(m)

        # ===== FUNCTION: calc_learning.v() =====
        # ID: F0677 · nested · used
        # ORIGINAL FILE: backend/scinsight/lg/common.py:452-454
        # ROLE: Metric value, or "not available (reason)".
        # INPUTS:
        #   o: dict | None -> metric object {"value", "reason"}.
        # OUTPUT:
        #   str.
        # CALLED BY:
        #   <- F0676 calc_learning() (calls)
        # CALLS:
        #   -> F0649 _fmt() (calls)
        def v(o):
            o = o or {}
            return _fmt(o["value"]) if o.get("value") is not None else f"not available{' (' + o['reason'] + ')' if o.get('reason') else ''}"
        cov, mae = m.get("verified_outcome_coverage") or {}, m.get("supplier_lead_time_mae_days") or {}
        lines.append(f"Learning metrics (verified outcomes only): verified outcome coverage {v(cov)} ({_fmt(cov.get('verified'))} of {_fmt(cov.get('executed'))} executed); "
                     f"supplier lead-time MAE {v(mae)} days over {_fmt(mae.get('records'))} records; demand forecast WAPE {v(m.get('demand_forecast_wape_pct'))}%; "
                     f"acceptance rate {v(m.get('recommendation_acceptance_rate'))}; modification rate {v(m.get('recommendation_modification_rate'))}; "
                     f"execution rate {v(m.get('recommendation_execution_rate'))}; stock-out warning accuracy {v(m.get('stockout_warning_accuracy'))}; business impact {v(m.get('business_impact_eur'))}.")
        lines.append("Models: " + (", ".join(f"{mv.get('version') or mv.get('id')} {mv.get('status')}" for mv in m.get("models", []))
                                   or "no trained model; promotion is a manual gate (director) and requires beating the best baseline"))
    else:
        lines.append(f"Learning metrics unavailable (HTTP {status}): {detail(m)}")
    if not ids:
        lines.insert(0, "No recommendation id (REC-...) in the question, so only the verified learning metrics are reported.")
    return {"calc_ok": True, "calc_id": "none (learning report)", "calc_kind": "learning", "calc_has_actions": False, "calc_summary": "\n".join(lines),
            "calc_evidence": json.dumps(ev), "calc_message": ""}


# Dispatch table: specialist key -> its calculation function (used by specialists.build_specialist's "calculate" node).
CALCULATE = {"factory": calc_factory, "procurement": calc_procurement, "warehouse": calc_warehouse, "inventory": calc_inventory,
             "logistics": calc_logistics, "quality": calc_quality, "learning": calc_learning}


# ===== FUNCTION: policy() =====
# ID: F0678 · function · used
# ORIGINAL FILE: backend/scinsight/lg/common.py:474-482
# ROLE: Governed policy search (port of POLICY): POST /api/v1/rag/search with topic + question; flagged (instruction-like) chunks
#       are withheld from the model; returns cited excerpts.
# INPUTS:
#   topic: str (specialist's policy topic), question: str.
# OUTPUT:
#   dict -> {"policy": text with [doc_id vX section "..."] citations, "citations": "doc v1 \"section\"; ..."}.
# CALLED BY:
#   <- F0696 build_specialist.policy_search() (calls)
# CALLS:
#   -> F0639 api() (calls)
#   -> F0076 create_app.rag_search() (http_request)
#   -> F0077 create_app.rag_search_get() (http_request)
#   -> F0133 create_app.rag_search() (http_request)
#   -> F0640 detail() (calls)
def policy(topic: str, question: str) -> dict:
    ok, status, d = api("POST", "/api/v1/rag/search", {"query": f"{topic} {question}"[:900], "top_k": 3})
    if not ok:
        return {"policy": f"Policy search unavailable (HTTP {status}): {detail(d)}", "citations": ""}
    hits = [h for h in d.get("results", []) if not h.get("flags")]
    withheld = len(d.get("results", [])) - len(hits)
    text = "\n".join(f"[{h['citation']['doc_id']} v{h['citation']['version']} section \"{h['citation']['section']}\"] {h['text']}" for h in hits) or "No matching policy excerpt."
    return {"policy": text + (f"\n({withheld} retrieved excerpt(s) withheld: instruction-like text)" if withheld else ""),
            "citations": "; ".join(f"{h['citation']['doc_id']} v{h['citation']['version']} \"{h['citation']['section']}\"" for h in hits)}


# ----------------------------------------------------------------------------- number check (port of GATE / CHAT_GATE)
# Numbers such as 20000, 20,000, 6.0.
_NUM = re.compile(r"\d[\d,]*(?:\.\d+)?")


# ===== FUNCTION: numbers() =====
# ID: F0679 · function · used
# ORIGINAL FILE: backend/scinsight/lg/common.py:489-496
# ROLE: All numbers in a text as floats ("20,000" -> 20000.0).
# INPUTS:
#   text: str.
# OUTPUT:
#   list[float].
# CALLED BY:
#   <- F0680 unsupported_numbers() (calls)
# CALLS:
#   (none found)
def numbers(text: str) -> list[float]:
    out = []
    for x in _NUM.findall(str(text)):
        try:
            out.append(float(x.replace(",", "")))
        except ValueError:
            pass
    return out


# ===== FUNCTION: unsupported_numbers() =====
# ID: F0680 · function · used
# ORIGINAL FILE: backend/scinsight/lg/common.py:499-501
# ROLE: Numbers in the answer that do NOT appear in the evidence (small integers <= 10 are tolerated: list numbering, "3 options").
# INPUTS:
#   answer: str, evidence: str.
# OUTPUT:
#   list[float] -> unsupported numbers, unique, in order.
# CALLED BY:
#   <- F0635 evidence_gate() (calls)
#   <- F0681 gate() (calls)
# CALLS:
#   -> F0679 numbers() (calls)
def unsupported_numbers(answer: str, evidence: str) -> list[float]:
    known = set(numbers(evidence))
    return list(dict.fromkeys(n for n in numbers(answer) if n not in known and not (n.is_integer() and n <= 10)))


# ===== FUNCTION: gate() =====
# ID: F0681 · function · used
# ORIGINAL FILE: backend/scinsight/lg/common.py:504-517
# ROLE: Evidence gate (port of GATE): if the LLM answer contains a number not found in the calculation/policy evidence, the answer is
#       withheld and the deterministic summary is shown instead; always appends the CALC id, snapshot, citations and approval note.
# INPUTS:
#   answer: str (LLM draft), s: dict (specialist state), question: str, reviewers: str.
# OUTPUT:
#   str -> final specialist answer.
# CALLED BY:
#   <- F0698 build_specialist.check_numbers() (calls)
# CALLS:
#   -> F0680 unsupported_numbers() (calls)
#   -> F0649 _fmt() (calls)
def gate(answer: str, s: dict, question: str, reviewers: str) -> str:
    answer = (answer or "").strip()
    evidence = " ".join([s.get("calc_evidence", ""), s.get("calc_summary", ""), s.get("policy", ""), question])
    bad = unsupported_numbers(answer, evidence)
    if not answer:
        text = s.get("calc_summary", "")
    elif bad:
        text = (f"{s.get('calc_summary', '')}\n\n(Evidence gate: the narrative answer was withheld because it contained numbers that are not in the calculation "
                f"or policy evidence: {', '.join(_fmt(n) for n in bad[:8])}. The figures above come straight from the calculation.)")
    else:
        text = answer
    nxt = (f"Proposed actions need a decision by an authorised human ({reviewers}) recorded in the SCInsight API. Nothing has been approved or written to SAP."
           if s.get("calc_has_actions") else "No action is proposed, so nothing needs approval.")
    # The "Decision calculation: CALC-..." line is what save() later parses to create the recommendation.
    return f"{text}\n\n---\nDecision calculation: {s.get('calc_id', '')} · SAP snapshot: {s.get('snapshot_id', '')}\nPolicy evidence: {s.get('citations') or 'none retrieved'}\n{nxt}"


# ----------------------------------------------------------------------------- supervisor steps (ports of GUARD / SAVE / VERIFY / WITHDRAW)
# ===== FUNCTION: guard() =====
# ID: F0682 · function · used
# ORIGINAL FILE: backend/scinsight/lg/common.py:521-531
# ROLE: Deterministic intent guard after the LLM classifier (port of GUARD): accept only known intents; SAP-write requests and
#       instruction overrides are forced to refusal routes whatever the classifier said.
# INPUTS:
#   question: str, classified: str (raw classifier output).
# OUTPUT:
#   tuple[str, str] -> (intent, reason: "classifier" | "unknown intent" | "deterministic SAP-write guard" | "instruction-override guard").
# CALLED BY:
#   <- F0637 out_of_scope_reply() (references)
#   <- F0706 safety_guard() (calls)
# CALLS:
#   (none found)
def guard(question: str, classified: str) -> tuple[str, str]:
    said = (classified or "").lower()
    # First word that is an exact intent, else any intent name contained in the text.
    intent = next((t for t in re.findall(r"[a-z_]+", said) if t in INTENTS), None) or next((i for i in INTENTS if i in said), None)
    why = "classifier"
    if not intent:
        intent, why = "out_of_scope", "unknown intent"
    if SAP_WRITE.search(question) or SAP_WRITE_2.search(question) or GOODS.search(question):
        intent, why = "sap_write_request", "deterministic SAP-write guard"
    # Override check last: it wins over everything.
    if OVERRIDE.search(question):
        intent, why = "out_of_scope", "instruction-override guard"
    return intent, why


# ===== FUNCTION: save() =====
# ID: F0683 · function · used
# ORIGINAL FILE: backend/scinsight/lg/common.py:534-549
# ROLE: Save step (port of SAVE): read the CALC id from the specialist answer, verify it in the API, and create a recommendation
#       (idempotent per chat + calc) only when the calculation proposes actions.
# INPUTS:
#   specialist_output: str, chat_id: str.
# OUTPUT:
#   dict -> rec_id, rec_domain, rec_status, reviewers, save_message (empty ids + reason when nothing is saved).
# CALLED BY:
#   <- F0713 save_recommendation() (calls)
# CALLS:
#   -> F0639 api() (calls)
#   -> F0132 create_app.calculation() (http_request)
#   -> F0640 detail() (calls)
#   -> F0135 create_app.create_decision() (http_request)
#   -> F0136 create_app.list_decisions() (http_request)
def save(specialist_output: str, chat_id: str) -> dict:
    none = lambda msg: {"rec_id": "", "rec_domain": "", "rec_status": "", "reviewers": "", "save_message": msg}  # noqa: E731
    m = re.search(r"Decision calculation: (CALC-[A-Z0-9-]{4,40})", specialist_output or "")
    if not m:
        return none("The specialist returned no calculation id, so no recommendation was created.")
    ok, status, calc = api("GET", f"/api/v1/calculations/{m.group(1)}")
    if not ok:
        return none(f"Calculation {m.group(1)} could not be verified (HTTP {status}): {detail(calc)}")
    if not calc.get("proposed_actions"):
        return none(f"Calculation {m.group(1)} proposes no action, so nothing needs approval.")
    chat = re.sub(r"[^A-Za-z0-9_.:-]", "", chat_id or "")[:60]
    # Only the calculation id is sent: the server copies the quantities (the LLM cannot change them).
    ok, status, r = api("POST", "/api/v1/decisions", {"calculation_id": m.group(1), "idempotency_key": f"langgraph:{chat}:{m.group(1)}"[:120]})
    if not ok:
        return none(f"The recommendation could not be saved (HTTP {status}): {detail(r)}")
    return {"rec_id": r["id"], "rec_domain": r["domain"], "rec_status": r["status"], "reviewers": " or ".join(r.get("review_authority", [])),
            "save_message": f"Recommendation {r['id']} saved for review ({r['domain']}, status {r['status']}, risk {r['risk_level']})."}


# ===== FUNCTION: verify() =====
# ID: F0684 · function · used
# ORIGINAL FILE: backend/scinsight/lg/common.py:552-564
# ROLE: Show the verified decision (port of VERIFY): read the recommendation from the API; resuming the graph is NOT an approval.
# INPUTS:
#   rec_id: str.
# OUTPUT:
#   str -> "still pending ..." or "approved/rejected/... by <reviewer> ..." text.
# CALLED BY:
#   <- F0720 show_decision() (calls)
# CALLS:
#   -> F0639 api() (calls)
#   -> F0137 create_app.get_decision() (http_request)
#   -> F0138 create_app.review() (http_request)
#   -> F0139 create_app.withdraw() (http_request)
#   -> F0140 create_app.sap_execution() (http_request)
#   -> F0640 detail() (calls)
def verify(rec_id: str) -> str:
    ok, status, d = api("GET", f"/api/v1/decisions/{rec_id}")
    if not ok:
        return f"Could not read recommendation {rec_id} (HTTP {status}): {detail(d)}"
    last = (d.get("reviews") or [None])[-1]
    if not d.get("verified_review") or not last:
        return (f"Recommendation {rec_id} is still **{d['status']}** in the SCInsight API: no authorised reviewer has recorded a decision yet. Resuming here is not an "
                f"approval. A {' or '.join(d.get('review_authority', []))} records the decision with their own key (POST /api/v1/decisions/{rec_id}/review). Nothing was written to SAP.")
    mods = f"; modifications: {json.dumps(last['modifications'])}" if last.get("modifications") else ""
    tail = ("Execution in SAP is a separate manual step by an authorised SAP user and is recorded afterwards; SCInsight never writes to SAP."
            if d["status"] in ("approved", "modified") else "Nothing will be executed.")
    return (f"Recommendation {rec_id}: **{d['status']}** by {last['reviewer_id']} ({', '.join(last.get('reviewer_roles', []))}) on {last['created_at']}: "
            f"\"{last['explanation']}\"{mods}.\nVerified from the SCInsight API (server-side identity and roles). {tail}")


# ===== FUNCTION: withdraw() =====
# ID: F0685 · function · used
# ORIGINAL FILE: backend/scinsight/lg/common.py:567-571
# ROLE: Withdraw step (port of WITHDRAW): POST /api/v1/decisions/{id}/withdraw when the user rejects at the approval pause.
# INPUTS:
#   rec_id: str.
# OUTPUT:
#   str -> result message.
# CALLED BY:
#   <- F0721 withdraw() (calls)
# CALLS:
#   -> F0639 api() (calls)
#   -> F0137 create_app.get_decision() (http_request)
#   -> F0138 create_app.review() (http_request)
#   -> F0139 create_app.withdraw() (http_request)
#   -> F0140 create_app.sap_execution() (http_request)
#   -> F0640 detail() (calls)
def withdraw(rec_id: str) -> str:
    ok, status, d = api("POST", f"/api/v1/decisions/{rec_id}/withdraw")
    if not ok:
        return f"Recommendation {rec_id} was not withdrawn (HTTP {status}): {detail(d)}"
    return f"Recommendation {rec_id} was withdrawn by the requester (status {d['status']}). It stays in the audit trail; nothing was written to SAP."
