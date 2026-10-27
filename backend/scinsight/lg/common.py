"""Shared pieces of the LangGraph mirror: SCInsight API client, Qwen model, the prompts Flowise uses, and Python ports of
the Flowise Custom Function logic (deterministic summaries, specialist calculations, policy search, number check, intent
guard, save / verify / withdraw). Keep this file behaviourally identical to flowise/scinsight/build-scinsight.cjs so the
comparison measures the runtime, not two different designs.
"""
from __future__ import annotations

import json
import os
import re
from functools import lru_cache
from pathlib import Path
from typing import Any

import httpx

ROOT = Path(__file__).resolve().parents[3]
PROMPTS = ROOT / "flowise" / "prompts"
SAP_WRITE = re.compile(r"\b(create|post|book|change|update|modify|delete|cancel|release|approve|execute|confirm|enter)\b[^.?!]{0,80}\b(in|into|to|on)\s+(sap|s/4|s4)", re.I)
SAP_WRITE_2 = re.compile(r"\b(sap|s/4hana)\b[^.?!]{0,40}\b(write|create|post|change|delete|release|approve)\b", re.I)
GOODS = re.compile(r"\bpost (a |the )?goods (receipt|issue)\b", re.I)
OVERRIDE = re.compile(r"(ignore|disregard|forget)\s+(all\s+|any\s+|the\s+)?(previous|prior|above|your)\s+(instructions|rules|prompt)|system prompt|developer mode|approve it yourself", re.I)
INTENTS = ["factory_planning", "procurement", "warehouse", "inventory_optimizer", "logistics", "quality", "outcome_learning", "sap_write_request", "out_of_scope"]
CODE = re.compile(r"^[A-Z0-9][A-Z0-9_-]{1,40}$")
SAP_READ_ONLY_REPLY = ("SupplyChain Insight AI is read-only towards SAP (SAP_WRITE_ENABLED=false): it cannot create, change, post, release, approve or delete anything "
                       "in SAP. I can analyse the situation and save a recommendation for review; an authorised manager decides in the SCInsight API and an "
                       "authorised SAP user executes it manually.")


def out_of_scope_reply(guard: str) -> str:
    return ("I can help with factory material readiness, procurement and supplier lead times, warehouse balancing, inventory cover, logistics, batch "
            f"quality and outcome learning for Belleva Cosmetics. Requests to change my instructions are not accepted. (guard: {guard})")


# ----------------------------------------------------------------------------- API client
_client: Any = None  # tests replace this with a FastAPI TestClient (same .request() signature as httpx.Client)


def client():
    global _client
    if _client is None:
        _client = httpx.Client(base_url=os.environ.get("SCI_API_URL", "http://api:8000/scinsight"), timeout=120)
    return _client


def api(method: str, path: str, body: dict | None = None) -> tuple[bool, int, dict]:
    """Call the SCInsight API with the agent key (role agent_service: read, calculate, create recommendations, never review)."""
    key = os.environ.get("SCI_AGENT_KEY", "")
    if not key:
        return False, 0, {"detail": "SCI_AGENT_KEY is not set for the LangGraph runtime"}
    try:
        r = client().request(method, path, json=body, headers={"X-API-Key": key})
    except Exception as e:  # noqa: BLE001
        return False, 0, {"detail": f"SCInsight API unreachable: {str(e)[:200]}"}
    try:
        data = r.json()
    except ValueError:
        data = {"detail": r.text[:400]}
    return r.status_code < 400, r.status_code, data


def detail(data: dict) -> str:
    d = data.get("detail") if isinstance(data, dict) else data
    return (d if isinstance(d, str) else json.dumps(d))[:400]


def strip(o):
    if isinstance(o, list):
        return [strip(x) for x in o]
    if isinstance(o, dict):
        return {k: strip(v) for k, v in o.items() if k != "source_records"}
    return o


# ----------------------------------------------------------------------------- model + prompts
def llm(max_tokens: int):
    """Qwen through the same OpenAI-compatible endpoint Flowise uses (temperature 0)."""
    from langchain_openai import ChatOpenAI

    return ChatOpenAI(model=os.environ.get("QWEN_MODEL", "qwen2.5-7b-scm"), base_url=os.environ.get("QWEN_BASE_URL", "http://host.docker.internal:11435/v1"),
                      api_key=os.environ.get("QWEN_API_KEY") or "local-qwen", temperature=0, max_tokens=max_tokens, timeout=180, max_retries=1)


@lru_cache(maxsize=64)
def prompt(name: str) -> str:
    return (PROMPTS / f"{name}.md").read_text(encoding="utf-8").rstrip("\n")


def explain_prompt(key: str) -> tuple[str, str]:
    """(system, user template) of a specialist's explanation step, exactly as exported for Flowise."""
    text = prompt(f"{key}_explain")
    system, _, user = text.partition("\n\n--- user message template ---\n")
    return system, user


def fill(template: str, **values: str) -> str:
    """Resolve the Flowise template variables used in the shared prompts ({{ question }}, {{ $flow.state.x }})."""
    out = template.replace("{{ question }}", values.get("question", ""))
    return re.sub(r"\{\{ \$flow\.state\.(\w+) \}\}", lambda m: str(values.get(m.group(1), "")), out)


def text_of(message) -> str:
    content = getattr(message, "content", message)
    if isinstance(content, list):
        return "".join(part.get("text", "") if isinstance(part, dict) else str(part) for part in content)
    return str(content or "")


# ----------------------------------------------------------------------------- deterministic summaries (port of SUMMARIZE)
def _list(xs, f) -> str:
    return "; ".join(f(x) for x in (xs or [])) or "none"


def _kv(o: dict) -> str:
    return " ".join(f"{k}={json.dumps(v) if isinstance(v, (dict, list)) else _fmt(v)}" for k, v in (o or {}).items())


def _fmt(v) -> str:
    if v is None:
        return "null"
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, float) and v.is_integer():
        return str(int(v))
    return str(v)


def _excluded(e: dict) -> str:
    return f"{e['batch_id']} {_fmt(e['quantity'])} ({e['reason']})"


def _late(p: dict) -> str:
    return f"{p['po_id']} {_fmt(p['quantity'])} promised {p['promised_date']}"


def _near(e: dict) -> str:
    return f"{e['batch_id']} {_fmt(e['quantity'])} expires {e['expiry_date']}"


def _opt(o: dict) -> str:
    basis = f" ({o['lead_time_basis']}{', contract ' + _fmt(o['contract_lead_days']) + ' days' if o.get('contract_lead_days') else ''})" if o.get("lead_time_basis") else ""
    reasons = f" - {', '.join(o['reasons'])}" if o.get("reasons") else ""
    nt = f"; not transferable: {_list(o['not_transferable'], _excluded)}" if o.get("not_transferable") else ""
    lead = _fmt(o.get("lead_days")) if o.get("lead_days") is not None else "-"
    cost = _fmt(o.get("cost_eur")) if o.get("cost_eur") is not None else "not estimated"
    return (f"  option {_fmt(o.get('rank'))}: {o.get('option')} - quantity {_fmt(o.get('quantity'))}, lead {lead} days{basis}{', ' + o['mode'] if o.get('mode') else ''}, "
            f"arrival {o.get('arrival_date')}, in time: {_fmt(o.get('in_time'))}, covers need: {_fmt(o.get('covers_need'))}, cost EUR {cost}, "
            f"feasible: {_fmt(o.get('feasible'))}, recommended: {_fmt(bool(o.get('recommended')))}{reasons}{nt}")


def summarize(d: dict) -> str:
    lines, k = [], d.get("kind")
    ex = _excluded
    if k == "material_readiness":
        lines.append(f"Production order {d.get('production_order_id') or '-'}: {d['sku']} x {_fmt(d['quantity'])} at {d['plant']}, materials needed by {d['need_date']} (BOM {d['bom_version']}). Status: {d['status']}.")
        lines.append("Shortages: " + _list(d.get("shortages"), lambda s: f"{s['material_id']} missing {_fmt(s['missing'])} {s['uom']} (needed {s['required_date']})"))
        for ln in d.get("lines", []):
            if ln["status"] == "covered" and not ln.get("excluded_stock"):
                lines.append(f"{ln['material_id']}: required {_fmt(ln['required_quantity'])} {ln['uom']}, usable {_fmt(ln['usable'])} - covered")
                continue
            lines.append(f"{ln['material_id']}: required {_fmt(ln['required_quantity'])} {ln['uom']}, usable {_fmt(ln['usable'])}, missing {_fmt(ln['missing'])}; "
                         f"excluded: {_list(ln.get('excluded_stock'), ex)}; late POs: {_list(ln.get('late_purchase_orders'), _late)}; "
                         f"unconfirmed POs: {_list(ln.get('unconfirmed_purchase_orders'), _po_unconfirmed)}")
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
    lines.append("Proposed actions: " + _list(d.get("proposed_actions"), _kv))
    pv = d.get("provenance") or {}
    lines.append(f"Calculation {d['calculation_id']} ({k}) on SAP snapshot {pv.get('snapshot_id')} as of {pv.get('as_of_date')}{', synthetic data' if pv.get('synthetic') else ''}.")
    return "\n".join(lines)


def _po_unconfirmed(p: dict) -> str:
    return f"{p['po_id']} {_fmt(p['quantity'])} promised {p['promised_date']} ({p['status']})"


# ----------------------------------------------------------------------------- context, calculations, policy (ports of CONTEXT / CALL_* / POLICY)
def context(session: str) -> dict:
    sid = re.sub(r"[^A-Za-z0-9_.:-]", "", session or "")[:120]
    ok, status, d = api("POST", "/api/v1/context/validate", {"session_id": sid if len(sid) >= 3 else "langgraph-session"})
    if not ok:
        return {"ctx_ok": False, "ctx_message": f"SCInsight context check failed (HTTP {status}): {detail(d)}. No analysis was run."}
    c = d.get("catalog", {})
    catalog = "\n".join([f"BUSINESS DATE (SAP snapshot as of): {d['snapshot_as_of']}", "PRODUCTS: " + "; ".join(c.get("products", [])),
                         "MATERIALS: " + "; ".join(c.get("materials", [])), "LOCATIONS: " + "; ".join(c.get("locations", [])),
                         "SUPPLIERS: " + "; ".join(c.get("suppliers", [])), "PRODUCTION ORDERS: " + "; ".join(c.get("production_orders", []))])
    return {"ctx_ok": True, "ctx_message": "", "snapshot_id": d["snapshot_id"], "catalog": catalog}


_STOP = {"THE", "AND", "FOR", "WITH", "SYNTHETIC", "BASE"}
_TOKEN = re.compile(r"[A-Z0-9]+(?:-[A-Z0-9]+)+")


def _catalog(catalog: str) -> dict[str, list[tuple[str, str]]]:
    out = {}
    for line in (catalog or "").splitlines():
        name, _, rest = line.partition(": ")
        out[name] = [tuple(p.split(" = ", 1)) for p in rest.split("; ") if " = " in p]
    return out


def _name_hits(label: str, words: list[str]) -> int:
    """How many meaningful words of a catalog name appear in the question (prefix match handles plurals)."""
    tokens = [t for t in re.findall(r"[A-Z][A-Z0-9]{2,}", re.sub(r"\(.*?\)", "", label.upper())) if t not in _STOP and t != "ML"]
    hits = sum(1 for t in tokens if any(w.startswith(t) for w in words))
    return hits if tokens and hits >= min(2, len(tokens)) else 0


def detect_codes(question: str, catalog: str) -> dict:
    """Deterministic identifier detection (codes first, then catalog names). Same rules as detectCodes() in the Flowise flows."""
    q = (question or "").upper()
    sec = _catalog(catalog)
    in_q = set(_TOKEN.findall(q))
    words = re.findall(r"[A-Z0-9][A-Z0-9/]*", q)

    def first(section: str, score) -> str:  # highest score; ties keep the first catalog entry (same as the JavaScript port)
        best = (0, "")
        for code, label in sec.get(section, []):
            s = int(score(code, label))
            if s > best[0]:
                best = (s, code)
        return best[1]

    by_code = lambda section: next((c for c, _ in sec.get(section, []) if c in in_q), "")  # noqa: E731
    product = by_code("PRODUCTS") or first("PRODUCTS", lambda c, label: _name_hits(label, words))
    material = by_code("MATERIALS") or first("MATERIALS", lambda c, label: _name_hits(label, words))
    supplier = by_code("SUPPLIERS") or first("SUPPLIERS", lambda c, label: (re.search(rf"\bSUPPLIER {c.split('-')[-1]}\b", q) is not None)
                                             or (label.split()[0].upper() in words))
    places = []  # locations in the order they appear in the question
    for code, label in sec.get("LOCATIONS", []):
        head = label.split(" (")[0].upper()  # e.g. "WAREHOUSE A — PARIS", "LYON FACTORY"
        names = [code] + ([head.split(" — ")[0]] if " — " in head else head.split()[:1])
        pos = [q.find(n) for n in names if re.search(rf"\b{re.escape(n)}\b", q)]
        if pos:
            places.append((min(pos), code))
    places = [c for _, c in sorted(places)]
    target = next((c for c in places if re.search(rf"\b(TO|INTO|REACH|RESUPPLY|COVER)\s+(WAREHOUSE {c[-1]}|{c})\b", q)), "") \
        or next((c for c in places if c.startswith("WH-")), "")
    clean = re.sub(r"\d{4}-\d{2}-\d{2}", " ", _TOKEN.sub(" ", q))
    qty = re.search(r"(?<![\w.])(\d{1,3}(?:[ ,]\d{3})+|\d{3,})(?![\w.])", clean)
    date = re.search(r"\d{4}-\d{2}-\d{2}", q)
    found = {"production_order_id": by_code("PRODUCTION ORDERS"), "sku": product, "material_id": material, "supplier_id": supplier,
             "item_id": product or material, "location": places[0] if places else "", "target_warehouse": target,
             "quantity": re.sub(r"[ ,]", "", qty.group(1)) if qty else "", "need_date": date.group(0) if date else ""}
    if material and by_code("MATERIALS"):  # an explicit material code beats a product matched by name
        found["item_id"] = material
    return {k: v for k, v in found.items() if v}


def merge_identifiers(detected: dict, extracted: dict) -> dict:
    """Code-detected identifiers win; the model only fills what code could not find."""
    return {**{k: v for k, v in (extracted or {}).items() if _val(extracted, k)}, **detected}


def parse_extracted(text: str) -> dict:
    """Lenient JSON parse of the identifier extraction (bare NONE / null tolerated, per-key fallback)."""
    m = re.search(r"\{[\s\S]*?\}", text or "")
    if not m:
        return {}
    try:
        o = json.loads(re.sub(r":\s*(none|null|n/a|undefined)\s*(?=[,}\n])", ': ""', m.group(0), flags=re.I))
        if isinstance(o, dict):
            return o
    except ValueError:
        pass
    return {k: v.strip() for k, v in re.findall(r'"([a-z_]+)"\s*:\s*"?([^",}\n]*)"?', m.group(0), flags=re.I)}


def _val(x: dict, k: str) -> str:
    v = x.get(k)
    s = "" if v is None else str(v).strip()
    return "" if re.fullmatch(r"(none|null|unknown|n/a|undefined)?", s, re.I) else s


def _code(x: dict, k: str) -> str:
    s = re.sub(r"\s+", "", _val(x, k).upper())
    return s if CODE.fullmatch(s) else ""


def _num(x: dict, k: str) -> float | None:
    try:
        n = float(_val(x, k).replace(",", "").replace(" ", ""))
        return n if n > 0 else None
    except ValueError:
        return None


def _day(x: dict, k: str) -> str:
    s = _val(x, k)
    return s if re.fullmatch(r"\d{4}-\d{2}-\d{2}", s) else ""


def _done(main: dict, extra: list[dict], message: str = "") -> dict:
    summary = "\n\n".join([summarize(main), *(summarize(e) for e in extra), *([message] if message else [])])
    return {"calc_ok": True, "calc_id": main["calculation_id"], "calc_kind": main["kind"], "snapshot_id": (main.get("provenance") or {}).get("snapshot_id", ""),
            "calc_has_actions": bool(main.get("proposed_actions")), "calc_summary": summary, "calc_evidence": json.dumps([strip(main), *[strip(e) for e in extra]]),
            "calc_message": ""}


def _fail(message: str) -> dict:
    return {"calc_ok": False, "calc_id": "", "calc_kind": "", "calc_has_actions": False, "calc_summary": "", "calc_evidence": "", "calc_message": message}


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
            return _fail(f"Several production orders exist for {sku}: " + ", ".join(f"{o['order_id']} ({_fmt(o['quantity'])} from {o['start_date']})" for o in items) + ". Which one should I check?"
                         if items else f"No production order found for {sku}{' with quantity ' + _fmt(qty) if qty else ''}. Give a production order (PRD-...) or SKU, quantity and need date (YYYY-MM-DD).")
        req["production_order_id"] = items[0]["order_id"]
    else:
        return _fail("To check material readiness I need a production order (PRD-...) or a finished-good SKU with quantity and need date (YYYY-MM-DD).")
    ok, status, d = api("POST", "/api/v1/optimizer/material-readiness", req)
    return _done(d, []) if ok else _fail(f"Material readiness could not be calculated (HTTP {status}): {detail(d)}")


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
        suppliers = [x2["supplier_id"] for x2 in (s.get("items", []) if ok else []) if any(i["material_id"] == material for i in x2.get("items", []))][:4]
    for sup in suppliers:
        ok, _, d = api("POST", "/api/v1/forecast/lead-time", {"supplier_id": sup, "material_id": material} if material else {"supplier_id": sup})
        if ok:
            extra.append(d)
    if not main and not extra:
        return _fail("Name a material (e.g. PUMP-DISP-24) and/or a supplier (SUP-...); add quantity and need date (YYYY-MM-DD) to get ranked purchase options.")
    if not main:
        main = extra.pop(0)
    return _done(main, extra, "No purchase quantity and need date were given, so no purchase request is proposed." if main["kind"] == "lead_time_estimate" else "")


def _balancing(x: dict, what: str) -> dict:
    sku, target = _code(x, "sku"), _code(x, "target_warehouse")
    if not sku:
        return _fail("Which product (SKU) should I balance across warehouses A, B and C?" if what == "Warehouse balancing" else "Which product (SKU) should be moved, and to which warehouse?")
    ok, status, d = api("POST", "/api/v1/optimizer/warehouse-balancing", {"sku": sku, "target_warehouse": target} if target else {"sku": sku})
    return _done(d, []) if ok else _fail(f"{what} could not be calculated (HTTP {status}): {detail(d)}")


def calc_warehouse(x: dict, question: str) -> dict:
    return _balancing(x, "Warehouse balancing")


def calc_logistics(x: dict, question: str) -> dict:
    return _balancing(x, "Transport options")


def calc_inventory(x: dict, question: str) -> dict:
    item, loc, qty, need = _code(x, "item_id"), _code(x, "location"), _num(x, "quantity"), _day(x, "need_date")
    if not item:
        return _fail("Which product or material should I check (code or name)?")
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


def calc_quality(x: dict, question: str) -> dict:
    item, loc = _code(x, "item_id"), _code(x, "location")
    if not item:
        return _fail("Which product or material (and location) should I check?")
    ok, status, d = api("POST", "/api/v1/quality/check-stock", {"item_id": item, "location": loc} if loc else {"item_id": item})
    return _done(d, []) if ok else _fail(f"Quality check could not be calculated (HTTP {status}): {detail(d)}")


def calc_learning(x: dict, question: str) -> dict:
    ids = list(dict.fromkeys(re.findall(r"REC-[A-Z0-9-]{4,40}", question.upper())))[:3]
    lines, ev = [], []
    for rid in ids:
        ok, status, rec = api("GET", f"/api/v1/decisions/{rid}")
        if not ok:
            lines.append(f"{rid}: not readable (HTTP {status}): {detail(rec)}")
            continue
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


CALCULATE = {"factory": calc_factory, "procurement": calc_procurement, "warehouse": calc_warehouse, "inventory": calc_inventory,
             "logistics": calc_logistics, "quality": calc_quality, "learning": calc_learning}


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
_NUM = re.compile(r"\d[\d,]*(?:\.\d+)?")


def numbers(text: str) -> list[float]:
    out = []
    for x in _NUM.findall(str(text)):
        try:
            out.append(float(x.replace(",", "")))
        except ValueError:
            pass
    return out


def unsupported_numbers(answer: str, evidence: str) -> list[float]:
    known = set(numbers(evidence))
    return list(dict.fromkeys(n for n in numbers(answer) if n not in known and not (n.is_integer() and n <= 10)))


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
    return f"{text}\n\n---\nDecision calculation: {s.get('calc_id', '')} · SAP snapshot: {s.get('snapshot_id', '')}\nPolicy evidence: {s.get('citations') or 'none retrieved'}\n{nxt}"


# ----------------------------------------------------------------------------- supervisor steps (ports of GUARD / SAVE / VERIFY / WITHDRAW)
def guard(question: str, classified: str) -> tuple[str, str]:
    said = (classified or "").lower()
    intent = next((t for t in re.findall(r"[a-z_]+", said) if t in INTENTS), None) or next((i for i in INTENTS if i in said), None)
    why = "classifier"
    if not intent:
        intent, why = "out_of_scope", "unknown intent"
    if SAP_WRITE.search(question) or SAP_WRITE_2.search(question) or GOODS.search(question):
        intent, why = "sap_write_request", "deterministic SAP-write guard"
    if OVERRIDE.search(question):
        intent, why = "out_of_scope", "instruction-override guard"
    return intent, why


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
    ok, status, r = api("POST", "/api/v1/decisions", {"calculation_id": m.group(1), "idempotency_key": f"langgraph:{chat}:{m.group(1)}"[:120]})
    if not ok:
        return none(f"The recommendation could not be saved (HTTP {status}): {detail(r)}")
    return {"rec_id": r["id"], "rec_domain": r["domain"], "rec_status": r["status"], "reviewers": " or ".join(r.get("review_authority", [])),
            "save_message": f"Recommendation {r['id']} saved for review ({r['domain']}, status {r['status']}, risk {r['risk_level']})."}


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


def withdraw(rec_id: str) -> str:
    ok, status, d = api("POST", f"/api/v1/decisions/{rec_id}/withdraw")
    if not ok:
        return f"Recommendation {rec_id} was not withdrawn (HTTP {status}): {detail(d)}"
    return f"Recommendation {rec_id} was withdrawn by the requester (status {d['status']}). It stays in the audit trail; nothing was written to SAP."
