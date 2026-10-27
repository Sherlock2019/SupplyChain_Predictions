#!/usr/bin/env python3
"""Build the SCInsight Functions & Code Explorer from the real source (stdlib only, read-only on the application).

    python3 code_explorer/tools/build_code_explorer.py          # regenerate everything
    python3 code_explorer/tools/build_code_explorer.py --check  # verify only (exit 1 on stale / modified annotated copies)

Steps
  1. Inventory: every function / method / class of the tracked Python files (AST), FastAPI routes (method + path), Pydantic models.
  2. Call graph: resolved calls between project functions (direct names, module aliases, self./typed attributes), plus HTTP edges
     (string paths like "/api/v1/..." matched to routes) and Flowise edges (Custom Tools and Agentflow Custom Functions -> routes).
  3. Usage: reachable from an entry point (route, LangGraph graph, MCP tool, script main, Flowise node) = used; otherwise unused.
  4. Annotated copies: proves each copy has the same AST as its original; refreshes the generated header lines (ID, ORIGINAL FILE
     lines, CALLED BY, CALLS) of every function header written as "# ROLE: ...".
  5. Writes registry/functions.json, registry/dependencies.json, FUNCTION_INDEX.md, COVERAGE.md, folder FUNCTIONS.md files,
     07_flowise_functions/*, viewer/index.html and the Flowise code-map spec flowise/code_explorer/codemap_spec.json.
"""
from __future__ import annotations

import argparse
import ast
import html
import json
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CE = ROOT / "code_explorer"

# original module -> annotated copy (home folder = engineering layer of the module)
ANNOTATED = {
    "backend/scinsight/app.py": "01_fastapi/endpoints/scinsight_app.py",
    "backend/app/main.py": "01_fastapi/endpoints/app_main.py",
    "backend/scinsight/schemas.py": "01_fastapi/pydantic_models/scinsight_schemas.py",
    "backend/app/schemas.py": "01_fastapi/pydantic_models/app_schemas.py",
    "backend/scinsight/settings.py": "01_fastapi/app_setup/scinsight_settings.py",
    "backend/app/config.py": "01_fastapi/app_setup/app_config.py",
    "backend/app/observability.py": "01_fastapi/app_setup/app_observability.py",
    "backend/scinsight/business.py": "02_business_logic/scinsight_rules/scinsight_business.py",
    "backend/scinsight/service.py": "02_business_logic/scinsight_use_cases/scinsight_service.py",
    "backend/app/engine.py": "02_business_logic/aurelia_engine/app_engine.py",
    "backend/app/optimizer.py": "02_business_logic/optimization/app_optimizer.py",
    "backend/app/dashboards.py": "02_business_logic/aurelia_views/app_dashboards.py",
    "backend/app/roles.py": "02_business_logic/aurelia_views/app_roles.py",
    "backend/app/insights.py": "02_business_logic/aurelia_views/app_insights.py",
    "backend/app/moat.py": "02_business_logic/aurelia_views/app_moat.py",
    "backend/scinsight/db.py": "03_sap_data/sql/scinsight_db.py",
    "backend/scinsight/fixtures.py": "03_sap_data/synthetic_sap/scinsight_fixtures.py",
    "backend/app/sap.py": "03_sap_data/sap_connectors/app_sap.py",
    "backend/app/store.py": "03_sap_data/repositories/app_store.py",
    "backend/app/tenants.py": "03_sap_data/repositories/app_tenants.py",
    "backend/scinsight/rag.py": "04_ai_ml/rag/scinsight_rag.py",
    "backend/app/rag.py": "04_ai_ml/rag/app_rag.py",
    "backend/scinsight/learning.py": "04_ai_ml/forecasting/scinsight_learning.py",
    "backend/app/forecasting.py": "04_ai_ml/forecasting/app_forecasting.py",
    "backend/app/llm.py": "04_ai_ml/llm/app_llm.py",
    "backend/app/copilot.py": "04_ai_ml/agent_tools/app_copilot.py",
    "backend/app/tools.py": "04_ai_ml/agent_tools/app_tools.py",
    "backend/app/mcp_server.py": "04_ai_ml/agent_tools/app_mcp_server.py",
    "backend/scinsight/lg/common.py": "04_ai_ml/langgraph/scinsight_lg_common.py",
    "backend/scinsight/lg/supervisor.py": "04_ai_ml/langgraph/scinsight_lg_supervisor.py",
    "backend/scinsight/lg/specialists.py": "04_ai_ml/langgraph/scinsight_lg_specialists.py",
    "backend/scinsight/lg/chat.py": "04_ai_ml/langgraph/scinsight_lg_chat.py",
    "backend/app/graphs.py": "04_ai_ml/langgraph/app_graphs.py",
    "backend/app/agentflow.py": "04_ai_ml/langgraph/app_agentflow.py",
    "backend/app/deep_agent.py": "04_ai_ml/langgraph/app_deep_agent.py",
    "backend/app/runner.py": "04_ai_ml/langgraph/app_runner.py",
    "backend/scinsight/security.py": "05_security_governance/authorization/scinsight_security.py",
    "backend/app/auth.py": "05_security_governance/authentication/app_auth.py",
}
# modules indexed but not hand-annotated: (category folder, sub-folder)
INDEXED = {
    "flowise/scinsight/deploy.py": ("07_flowise_functions", "deployment"),
    "flowise/bootstrap.py": ("07_flowise_functions", "deployment"),
    "scripts/scinsight_compare.py": ("04_ai_ml", "evaluation"),
    "scripts/langgraph_assistants.py": ("04_ai_ml", "langgraph"),
    "scripts/generate_tenants.py": ("03_sap_data", "synthetic_sap"),
    "scripts/gen-env.py": ("05_security_governance", "secrets_setup"),
    "scripts/smoke.py": ("06_testing", "smoke"),
    "scripts/aws-cost-estimate.py": ("06_testing", "ops_tooling"),
}
CATEGORIES = {
    "01_fastapi": "FastAPI — application setup, routes, endpoints, Pydantic models, dependencies",
    "02_business_logic": "Business logic — inventory, BOM, shortages, production, procurement, optimisation, role views",
    "03_sap_data": "SAP / data — synthetic SAP, OData adapter, SQL / repositories, tenants",
    "04_ai_ml": "AI / ML — LLM, RAG, forecasting & governed ML, agent tools, LangGraph, evaluation",
    "05_security_governance": "Security & governance — authentication, authorization, human approval, audit",
    "06_testing": "Testing — unit, API, agent tests and smoke tooling",
    "07_flowise_functions": "Flowise — custom JavaScript functions, tool → endpoint mappings, deployment, code maps",
}
# topic indexes (no code copies: FUNCTIONS.md pointing into the home modules)
TOPICS = {
    "02_business_logic/inventory": r"usable_stock|days_of_cover|average_daily_demand|inventory|position_health|expiry|replenish|on_hand|stock_rows",
    "02_business_logic/bom": r"bom",
    "02_business_logic/shortages": r"shortage|material_readiness|factory_readiness|production_overview",
    "02_business_logic/production": r"production|factory|readiness",
    "02_business_logic/procurement": r"supplier|lead_time|purchase|procure",
    "02_business_logic/optimization": r"transfer|balanc|optimi|supply_options|feasibility",
    "05_security_governance/human_approval": r"review|decision|approv|withdraw|sap_execution|record_outcome|reconcile|human",
    "05_security_governance/audit_logging": r"audit|verify_chain|_digest",
    "05_security_governance/validation": r"validate|_one_way|_limits|_unique|question_or_resume|guard|require",
}
TYPED = {  # variable / attribute name -> project class (resolution of obj.method calls)
    "service": "Service", "security": "Security", "db": "Database", "kb": "KnowledgeBase", "store": "Store", "engine": "SupplyChainEngine",
    "e": "SupplyChainEngine", "sap": "SapRepository", "roles": "RoleCenter", "dashboards": "Dashboards", "insight_engine": "InsightEngine",
    "insights": "InsightEngine", "moat": "MoatEngine", "runner": "GraphRunner", "auth": "ApiKeyAuth", "tenants": "TenantRegistry",
    "registry": "TenantRegistry", "flowise": "Flowise", "rag": "MemoryRag|PgVectorRag", "_db": "_SqliteDb|_PostgresDb",
    "impl": "LocalRunner|RemoteRunner", "embedder": "FastEmbedder|HashEmbedder", "repository": "MemoryRag|PgVectorRag",
}
SKIP_NAMES = {"get", "items", "append", "extend", "join", "split", "format", "update", "keys", "values", "strip", "lower", "upper", "replace",
              "startswith", "endswith", "pop", "setdefault", "add", "sort", "copy", "count", "index", "invoke", "query", "one", "execute", "run",
              "search", "build", "embed", "dump", "loads", "dumps", "read_text", "write_text", "call", "info", "warning", "labels", "inc", "observe"}


def git_files(pattern: str) -> list[str]:
    # tracked + new (not ignored) files; code_explorer/ itself holds copies and is never indexed
    out = subprocess.run(["git", "ls-files", "--cached", "--others", "--exclude-standard", pattern], cwd=ROOT,
                         capture_output=True, text=True, check=True).stdout.split()
    return sorted(p for p in set(out) if not p.startswith("code_explorer/"))


def category_of(path: str) -> tuple[str, str]:
    if path in ANNOTATED:
        parts = ANNOTATED[path].split("/")
        return parts[0], parts[1]
    if path in INDEXED:
        return INDEXED[path]
    if path.startswith("tests/"):
        name = Path(path).name
        sub = "agent_tests" if re.search(r"graph|flowise|langgraph|agent", name) else "api_tests" if re.search(r"api|contract|security|scenario", name) else "unit_tests"
        return "06_testing", sub
    return "06_testing", "other"


# ----------------------------------------------------------------------------- 1. inventory
class Fn:
    def __init__(self, **kw):
        self.__dict__.update(kw)


def route_of(dec: ast.expr) -> tuple[str, str] | None:
    if isinstance(dec, ast.Call) and isinstance(dec.func, ast.Attribute) and dec.args and isinstance(dec.args[0], ast.Constant) \
            and isinstance(dec.args[0].value, str) and dec.args[0].value.startswith("/"):
        verb = dec.func.attr
        if verb in ("get", "post", "put", "delete", "patch"):
            return verb.upper(), dec.args[0].value
        if verb == "api_route":
            methods = next((k.value for k in dec.keywords if k.arg == "methods"), None)
            return "/".join(e.value for e in methods.elts) if isinstance(methods, ast.List) else "ANY", dec.args[0].value
        if verb == "custom_route":
            return "GET", dec.args[0].value
    return None


def inventory(paths: list[str]) -> tuple[list[Fn], dict]:
    fns, modules = [], {}
    for path in paths:
        src = (ROOT / path).read_text(encoding="utf-8")
        tree = ast.parse(src)
        imports = {}  # local name -> (module, attribute or None)
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module and node.module.startswith("backend"):
                for a in node.names:
                    imports[a.asname or a.name] = (node.module, a.name)
            elif isinstance(node, ast.Import):
                for a in node.names:
                    if a.name.startswith("backend"):
                        imports[a.asname or a.name.split(".")[-1]] = (a.name, None)
        modules[path] = {"imports": imports, "lines": src.splitlines()}

        def visit(node, prefix: str, cls: str | None, parent: str | None):
            for child in ast.iter_child_nodes(node):
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    qual = f"{prefix}{child.name}"
                    is_class = isinstance(child, ast.ClassDef)
                    decos = [ast.unparse(d) for d in child.decorator_list]
                    routes = [r for r in (route_of(d) for d in child.decorator_list) if r]
                    bases = [ast.unparse(b) for b in child.bases] if is_class else []
                    sig = ""
                    if not is_class:
                        sig = f"{'async ' if isinstance(child, ast.AsyncFunctionDef) else ''}def {child.name}({ast.unparse(child.args)})" + \
                              (f" -> {ast.unparse(child.returns)}" if child.returns else "")
                    else:
                        sig = f"class {child.name}({', '.join(bases)})" if bases else f"class {child.name}"
                    first = min([d.lineno for d in child.decorator_list] + [child.lineno])
                    raises = sorted({ast.unparse(r.exc.func if isinstance(r.exc, ast.Call) else r.exc).split("(")[0]
                                     for r in ast.walk(child) if isinstance(r, ast.Raise) and r.exc is not None}) if not is_class else []
                    kind = "class" if is_class else ("route" if routes else "method" if cls else "nested" if parent else "function")
                    if is_class and any(b in ("BaseModel", "Strict", "StrictModel", "BaseSettings") or b.endswith("Request") for b in bases):
                        kind = "pydantic_model"
                    if path.startswith("tests/") and child.name.startswith("test_"):
                        kind = "test"
                    fns.append(Fn(qual=qual, name=child.name, path=path, first=first, line=child.lineno, end=child.end_lineno, kind=kind,
                                  cls=cls, parent=parent, sig=sig, decorators=decos, routes=routes, raises=raises,
                                  doc=(ast.get_docstring(child) or "").split("\n")[0], node=child, is_async=isinstance(child, ast.AsyncFunctionDef)))
                    if is_class:
                        visit(child, f"{qual}.", child.name, parent)
                    else:
                        visit(child, f"{qual}.", None, qual)
                else:  # defs inside if / try / with / for blocks keep the enclosing scope
                    visit(child, prefix, cls, parent)
        visit(tree, "", None, None)
    return fns, modules


# ----------------------------------------------------------------------------- 2. call graph
def module_of_path(path: str) -> str:
    return path[:-3].replace("/", ".")


def build_edges(fns: list[Fn], modules: dict) -> list[dict]:
    by_mod_name = defaultdict(list)          # (module, top-level name) -> fns
    by_class_method = defaultdict(list)      # (class, method) -> fns
    by_name_any = defaultdict(list)
    for f in fns:
        mod = module_of_path(f.path)
        top = f.qual.split(".")[0]
        if f.qual == top:
            by_mod_name[(mod, top)].append(f)
        if f.cls:
            by_class_method[(f.cls, f.name)].append(f)
        by_name_any[f.name].append(f)
    route_fns = [f for f in fns if f.routes]
    edges, seen = [], set()
    module_refs: dict[str, str] = {}  # function id -> evidence of use by module-level code (entry points)

    def add(src, dst, kind, line, evidence):
        key = (src.id, dst.id, kind)
        if key in seen or src.id == dst.id:
            return
        seen.add(key)
        edges.append({"from": src.id, "to": dst.id, "kind": kind, "evidence": f"{src.path}:{line} {evidence}"})

    module_fns = []  # pseudo functions holding the module-level code (graph builds, loops, tables) of each file
    for path, info in modules.items():
        module_fns.append(Fn(qual="<module>", name="<module>", path=path, first=1, line=1, end=len(info["lines"]), kind="module", cls=None,
                             parent=None, node=ast.parse("\n".join(info["lines"])), id=f"module:{path}", routes=[]))
    for f in fns + module_fns:
        if f.kind in ("class", "pydantic_model"):
            continue
        mod = module_of_path(f.path)
        imports = modules[f.path]["imports"]
        nested = {g.name: g for g in fns if g.parent == f.qual and g.path == f.path}
        siblings = {g.name: g for g in fns if g.parent == f.parent and g.parent and g.path == f.path}
        own_class = f.cls

        def body_nodes(node):
            for child in ast.iter_child_nodes(node):
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    for d in child.decorator_list:  # decorators belong to the enclosing scope
                        yield from ast.walk(d)
                    continue
                yield child
                yield from body_nodes(child)

        call_funcs: set[int] = set()
        nodes = list(body_nodes(f.node))
        for node in nodes:  # first pass: remember which Name/Attribute nodes are call targets
            if isinstance(node, ast.Call):
                call_funcs.add(id(node.func))
        for node in nodes:
            # FastAPI Depends(x) -> dependency edge
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "Depends" and node.args and isinstance(node.args[0], ast.Name):
                pass
            if isinstance(node, ast.Constant) and isinstance(node.value, str) and re.match(r"^/(api/v1|sap|forecast|optimizer|decisions|outcomes|learning|v1)/", node.value):
                path = node.value.split("?")[0]
                for r in route_fns:
                    for verb, rpath in r.routes:
                        pattern = "^" + re.sub(r"\{[^}]+\}", "[^/]+", rpath) + ("" if rpath.endswith("}") else "$")
                        if (path == rpath or re.match(pattern, path) or (path.endswith("/") and rpath.startswith(path))) and r.path != f.path:
                            add(f, r, "http_request", node.lineno, f"HTTP {verb} {rpath}")
            if isinstance(node, ast.Call):
                fn, kind = node.func, "calls"
            elif isinstance(node, (ast.Name, ast.Attribute)) and isinstance(getattr(node, "ctx", None), ast.Load) and id(node) not in call_funcs:
                fn, kind = node, "references"  # passed as a value: add_node(fn), db.atomic(apply), dispatch tables, callbacks
            else:
                continue
            if isinstance(node, ast.Call):
                call_funcs.add(id(node.func))
            targets, how = [], ""
            if isinstance(fn, ast.Name):
                n = fn.id
                if n in nested:
                    targets, how = [nested[n]], "nested function"
                elif n in siblings:
                    targets, how = [siblings[n]], "sibling closure"
                elif (mod, n) in by_mod_name:
                    targets, how = by_mod_name[(mod, n)], "same module"
                elif n in imports:
                    m, attr = imports[n]
                    targets, how = by_mod_name.get((m, attr or n), []), f"imported from {m}"
            elif isinstance(fn, ast.Attribute):
                attr, base = fn.attr, fn.value
                if isinstance(base, ast.Name):
                    b = base.id
                    if b in ("self", "cls") and own_class:
                        targets, how = by_class_method.get((own_class, attr), []), "self method"
                    elif b in imports and imports[b][1] is None or (b in imports and (imports[b][0] + "." + imports[b][1]) in {module_of_path(p) for p in modules}):
                        m = imports[b][0] if imports[b][1] is None else imports[b][0] + "." + imports[b][1]
                        targets, how = by_mod_name.get((m, attr), []), f"module {b}"
                    elif b in imports and imports[b][1]:
                        targets, how = by_class_method.get((imports[b][1], attr), []), f"class {imports[b][1]}"
                    elif b in TYPED:
                        targets = [g for c in TYPED[b].split("|") for g in by_class_method.get((c, attr), [])]
                        how = f"typed variable {b} -> {TYPED[b]}"
                    elif (mod, b) in by_mod_name and by_mod_name[(mod, b)][0].kind == "class":
                        targets, how = by_class_method.get((b, attr), []), f"class {b}"
                elif isinstance(base, ast.Attribute) and isinstance(base.value, ast.Name) and base.value.id == "self" and base.attr in TYPED:
                    targets = [g for c in TYPED[base.attr].split("|") for g in by_class_method.get((c, attr), [])]
                    how = f"typed attribute self.{base.attr} -> {TYPED[base.attr]}"
                elif isinstance(base, ast.Call) and isinstance(base.func, ast.Name) and base.func.id == "get_backend":
                    targets = by_class_method.get(("LocalBackend", attr), []) + by_class_method.get(("ApiBackend", attr), [])
                    how = "get_backend() -> LocalBackend | ApiBackend"
                elif isinstance(base, ast.Subscript) and isinstance(base.value, ast.Name) and base.value.id in ("CALCULATE", "GRAPHS"):
                    pass
                if kind == "calls" and not targets and attr not in SKIP_NAMES and len(by_name_any.get(attr, [])) == 1 and by_name_any[attr][0].cls:
                    targets, how = by_name_any[attr], "inferred: unique method name"
            for t in targets:
                if t.kind in ("test",) or t is f:
                    continue
                if f.kind == "module":
                    module_refs.setdefault(t.id, f"{f.path}:{node.lineno} module-level {how}")
                else:
                    add(f, t, kind, node.lineno, how + (" (passed as a value)" if kind == "references" else ""))
            # Depends(...) dependency injection inside signatures handled below
        for d in (f.node.args.defaults + f.node.args.kw_defaults) if hasattr(f.node, "args") else []:
            if isinstance(d, ast.Call) and isinstance(d.func, ast.Name) and d.func.id == "Depends" and d.args and isinstance(d.args[0], ast.Name):
                dep = siblings.get(d.args[0].id) or nested.get(d.args[0].id)
                if dep:
                    add(f, dep, "depends_on", f.line, f"Depends({d.args[0].id}) (authorization / validation)")
            # Pydantic body models
        if f.routes:
            for a in f.node.args.args:
                ann = ast.unparse(a.annotation) if a.annotation else ""
                model = ann.split(".")[-1]
                cand = [g for g in fns if g.kind == "pydantic_model" and g.name == model]
                for g in cand[:1]:
                    add(f, g, "validates_input", f.line, f"body: {ann}")
    return edges, module_refs


# ----------------------------------------------------------------------------- 3. Flowise
def flowise_nodes(fns: list[Fn]) -> tuple[list[dict], list[dict], list[dict]]:
    route_fns = [f for f in fns if f.routes]

    def match(method: str, path: str):
        path = path.split("?")[0]
        out = []
        for r in route_fns:
            for verb, rpath in r.routes:
                if method and method not in verb.split("/"):
                    continue
                pattern = "^" + re.sub(r"\{[^}]+\}", "[^/]+", rpath) + "$"
                if path == rpath or re.match(pattern, path) or re.match(pattern, path + "x"):
                    out.append(r)
        return out

    nodes, edges, js = [], [], []
    for tool in sorted((ROOT / "flowise" / "tools").glob("*.json")):
        t = json.loads(tool.read_text(encoding="utf-8"))
        m = re.search(r"allowlisted tool: (\w+) (\S+)", t["func"])
        node = {"id": f"flowise:tool:{t['name']}", "label": f"Flowise Custom Tool · {t['name']}", "flow": "Flowise Tools", "kind": "flowise_tool",
                "source": f"flowise/tools/{tool.name}", "method": m.group(1) if m else "", "path": m.group(2) if m else "", "code": t["func"],
                "description": t["description"]}
        nodes.append(node)
        js.append((f"tools/{t['name']}.js", f"// Flowise Custom Tool {t['name']} (generated by flowise/scinsight/build-scinsight.cjs)\n// {t['description']}\n" + t["func"]))
        for r in match(node["method"], node["path"]):
            edges.append({"from": node["id"], "to": r.id, "kind": "http_request", "evidence": f"{node['source']}: {node['method']} {node['path']}"})
    for folder in ("agentflows", "chatflows"):
        for flow in sorted((ROOT / "flowise" / folder).glob("SCInsight-*-v1.json")):
            data = json.loads(flow.read_text(encoding="utf-8"))
            fname = flow.stem
            for n in data["nodes"]:
                d = n.get("data", {})
                code = (d.get("inputs") or {}).get("customFunctionJavascriptFunction")
                label = d.get("label", n["id"])
                if d.get("name") in ("executeFlowAgentflow",):
                    pass
                if not code:
                    continue
                nid = f"flowise:{fname}:{n['id']}"
                node = {"id": nid, "label": f"{fname.replace('SCInsight-Cosmetics-', '').replace('-v1', '')} · {label}", "flow": fname,
                        "kind": "flowise_custom_function", "source": f"flowise/{folder}/{flow.name} node {n['id']}", "code": code}
                nodes.append(node)
                safe = re.sub(r"[^A-Za-z0-9]+", "_", label).strip("_")
                js.append((f"agentflows/{fname}__{n['id']}__{safe}.js", f"// Flowise Custom Function '{label}' in {fname} ({n['id']})\n"
                                                                       f"// Generated from flowise/scinsight/build-scinsight.cjs (PRELUDE + step function)\n" + code))
                for method, path in re.findall(r"api\('(GET|POST)',\s*[`']([^`']+)[`']", code):
                    path = re.sub(r"\$\{[^}]+\}", "x", path)
                    for r in match(method, path.rstrip("/") + ("x" if path.endswith("/") else "")):
                        edges.append({"from": nid, "to": r.id, "kind": "http_request", "evidence": f"{node['source']}: api('{method}', '{path}')"})
    return nodes, edges, js


# ----------------------------------------------------------------------------- 4. annotated copies
def ast_equal(orig: str, ann: str) -> bool:
    return ast.dump(ast.parse((ROOT / orig).read_text(encoding="utf-8"))) == ast.dump(ast.parse((CE / ann).read_text(encoding="utf-8")))


def header_span(lines: list[str], first: int) -> tuple[int, int] | None:
    """(start, end) line indexes (0-based, inclusive) of the comment block directly above line `first` (1-based)."""
    i = first - 2
    end = i
    while i >= 0 and lines[i].strip().startswith("#"):
        i -= 1
    start = i + 1
    if start > end:
        return None
    return start, end


def refresh_headers(orig: str, ann: str, fns_by_key: dict, edges_out: dict, edges_in: dict, labels: dict) -> list[str]:
    """Rewrite the generated part of every '# ROLE:' header; return the updated lines (logic untouched)."""
    path = CE / ann
    lines = path.read_text(encoding="utf-8").splitlines()
    tree = ast.parse("\n".join(lines))
    spans = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            first = min([d.lineno for d in node.decorator_list] + [node.lineno])
            spans.append((first, node))
    qual_of = {}

    def walk(node, prefix):
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                qual_of[id(child)] = f"{prefix}{child.name}"
                walk(child, f"{prefix}{child.name}.")
            else:
                walk(child, prefix)
    walk(tree, "")
    for first, node in sorted(spans, key=lambda x: -x[0]):  # bottom-up so indexes stay valid
        span = header_span(lines, first)
        if not span:
            continue
        s, e = span
        block = lines[s:e + 1]
        if not any(l.strip().startswith("# ROLE:") for l in block):
            continue
        # the header starts at its generated "# ID:" line (second and later runs) or at "# ROLE:" (first run)
        idx = next(k for k, l in enumerate(block) if l.strip().startswith(("# =====", "# ID:", "# ROLE:")))
        indent = re.match(r"\s*", block[idx]).group(0)
        f = fns_by_key.get((orig, qual_of[id(node)]))
        if f is None:
            continue
        manual = [l for l in block[idx:] if not re.match(r"\s*# (=====|CALLED BY:|CALLS:|  ->|  <-|  \(none found\)|ORIGINAL FILE:|ID:)", l)]
        calls = edges_out.get(f.id, [])
        called = edges_in.get(f.id, [])
        what = "CLASS" if f.kind in ("class", "pydantic_model") else "FUNCTION"
        gen = [f"{indent}# ===== {what}: {f.qual}{'' if what == 'CLASS' else '()'} =====",
               f"{indent}# ID: {f.id} · {f.kind} · {f.status}", f"{indent}# ORIGINAL FILE: {orig}:{f.first}-{f.end}"]
        tail = [f"{indent}# CALLED BY:"] + ([f"{indent}#   <- {labels[x['from']]} ({x['kind']})" for x in called[:12]] or [f"{indent}#   (none found)"])
        tail += [f"{indent}# CALLS:"] + ([f"{indent}#   -> {labels[x['to']]} ({x['kind']})" for x in calls[:12]] or [f"{indent}#   (none found)"])
        lines[s + idx:e + 1] = gen + manual + tail
    return lines


# ----------------------------------------------------------------------------- 5. outputs
def snippet(lines: list[str], node_first: int, node_end: int) -> str:
    span = header_span(lines, node_first)
    start = span[0] if span else node_first - 1
    return "\n".join(lines[start:node_end])


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()

    paths = [p for p in git_files("*.py") if not p.endswith("__init__.py")]
    fns, modules = inventory(paths)
    # stable ids
    id_file = CE / "registry" / "id_map.json"
    ids = json.loads(id_file.read_text()) if id_file.exists() else {}
    counter = max([int(v[1:]) for v in ids.values()] + [0])
    for f in sorted(fns, key=lambda f: (category_of(f.path), f.path, f.first)):
        key = f"{f.path}::{f.qual}"
        if key not in ids:
            counter += 1
            ids[key] = f"F{counter:04d}"
        f.id = ids[key]
        f.category, f.sub = category_of(f.path)
    labels = {f.id: f"{f.id} {f.qual}{'' if f.kind in ('class', 'pydantic_model') else '()'}" for f in fns}

    edges, module_refs = build_edges(fns, modules)
    fnodes, fedges, js_files = flowise_nodes(fns)
    for n in fnodes:
        labels[n["id"]] = n["label"]
    all_edges = edges + fedges

    # usage: entry points + reachability
    by_id = {f.id: f for f in fns}
    out_map, in_map = defaultdict(list), defaultdict(list)
    for e in all_edges:
        out_map[e["from"]].append(e)
        in_map[e["to"]].append(e)
    entry = set()
    for f in fns:
        src_line = modules[f.path]["lines"]
        if f.routes or any("mcp.tool" in d or "@tool" in d or d == "tool" for d in f.decorators) or f.kind == "test":
            entry.add(f.id)
        if f.name in ("main", "create_app", "create_mcp_app", "build_supervisor", "build_specialist", "build_chat", "build_graph", "get_backend"):
            entry.add(f.id)
        if f.path.startswith(("tests/",)):
            entry.add(f.id)
    # LangGraph node registration: functions passed by name to add_node / tuples in build functions
    for path, info in modules.items():
        text = "\n".join(info["lines"])
        for name in set(re.findall(r"add_node\(\s*\"?\w*\"?,?\s*(\w+)\)", text)) | set(re.findall(r"for fn in \(([^)]*)\)", text, re.S)):
            for n in re.findall(r"\w+", name):
                for f in fns:
                    if f.path == path and f.name == n:
                        entry.add(f.id)
        for m in re.finditer(r"CALCULATE = \{([^}]*)\}", text):
            for n in re.findall(r":\s*(\w+)", m.group(1)):
                entry |= {f.id for f in fns if f.path == path and f.name == n}
        for m in re.finditer(r"TOOLS = \[([^\]]*)\]|READ_ONLY_TOOLS = \[([^\]]*)\]", text, re.S):
            for n in re.findall(r"\w+", (m.group(1) or m.group(2))):
                entry |= {f.id for f in fns if f.path == path and f.name == n}
        if "exception_handler" in text or "middleware(" in text:
            entry |= {f.id for f in fns if f.path == path and any("exception_handler" in d or "middleware" in d for d in f.decorators)}
    for n in fnodes:
        entry.add(n["id"])
    entry |= set(module_refs)  # used by module-level code (graph builds, tool lists, dispatch tables)
    reach, stack = set(), list(entry)
    while stack:
        x = stack.pop()
        if x in reach:
            continue
        reach.add(x)
        stack += [e["to"] for e in out_map.get(x, [])]
    for f in fns:
        # methods of a reachable class, dunder methods and validators are used through the framework
        cls_reached = f.cls and any(g.id in reach for g in fns if g.path == f.path and g.kind in ("class", "pydantic_model") and g.name == f.cls)
        framework = f.name.startswith("__") or any("validator" in d or "property" in d or "staticmethod" in d or "classmethod" in d for d in f.decorators) or f.kind == "pydantic_model"
        if f.kind == "test":
            f.status = "test"
        elif f.id in reach:
            f.status = "used"
        elif f.kind in ("class",) or framework or cls_reached:
            f.status = "used (framework)"
        elif f.path.startswith(("scripts/", "flowise/")):
            f.status = "tooling"
        else:
            f.status = "unused?"
    # second pass: callees of framework-dispatched methods (getattr dispatch, decorators, properties) are used too
    stack = [f.id for f in fns if f.status == "used (framework)"]
    while stack:
        x = stack.pop()
        for e in out_map.get(x, []):
            g = by_id.get(e["to"])
            if g and g.status in ("unused?", "tooling"):
                g.status = "used (framework)" if g.status == "unused?" else g.status
                stack.append(g.id)
    # classes reached when any of their methods / constructor are
    for f in fns:
        if f.kind in ("class", "pydantic_model") and f.status != "used":
            if any(g.cls == f.name and g.path == f.path and g.status.startswith("used") for g in fns) or f.id in reach:
                f.status = "used"

    # tests that reference a function name
    test_text = {p: "\n".join(modules[p]["lines"]) for p in paths if p.startswith("tests/")}
    for f in fns:
        f.tests = sorted(p for p, t in test_text.items() if re.search(rf"\b{re.escape(f.name)}\b", t) and not f.path.startswith("tests/"))[:6] if len(f.name) > 3 else []

    # annotated copies: verify + refresh headers
    problems, ann_ok = [], {}
    fns_by_key = {(f.path, f.qual): f for f in fns}
    for orig, ann in ANNOTATED.items():
        if not (CE / ann).exists():
            problems.append(f"missing annotated copy {ann}")
            ann_ok[orig] = False
            continue
        ok = ast_equal(orig, ann)
        ann_ok[orig] = ok
        if not ok:
            problems.append(f"STALE annotated copy {ann}: its code differs from {orig} (re-annotate it)")
            continue
        if not args.check:
            new = refresh_headers(orig, ann, fns_by_key, out_map, in_map, labels)
            (CE / ann).write_text("\n".join(new) + "\n", encoding="utf-8")
            if not ast_equal(orig, ann):
                raise SystemExit(f"BUG: header refresh changed the code of {ann}")
    if args.check:
        print("\n".join(problems) or f"OK: {len(ANNOTATED)} annotated copies match their originals")
        return 1 if problems else 0

    # code text for every function (annotated copy when available)
    ann_lines, ann_nodes = {}, {}
    for orig, ann in ANNOTATED.items():
        lines = (CE / ann).read_text(encoding="utf-8").splitlines()
        ann_lines[orig] = lines
        tree = ast.parse("\n".join(lines))

        def walk(node, prefix, orig=orig):
            for child in ast.iter_child_nodes(node):
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    q = f"{prefix}{child.name}"
                    ann_nodes[(orig, q)] = (min([d.lineno for d in child.decorator_list] + [child.lineno]), child.end_lineno)
                    walk(child, f"{q}.", orig)
                else:
                    walk(child, prefix, orig)
        walk(tree, "")
    for f in fns:
        if (f.path, f.qual) in ann_nodes:
            a, b = ann_nodes[(f.path, f.qual)]
            if f.kind == "class":  # class view = header + class line + fields, methods have their own entries
                body_end = min([g.first for g in fns if g.path == f.path and g.cls == f.name and g.qual.startswith(f.qual + ".")] + [f.end + 1]) - 1
                a2, b2 = ann_nodes[(f.path, f.qual)]
                f.code = snippet(ann_lines[f.path], a2, a2 + (body_end - f.first))
            else:
                f.code = snippet(ann_lines[f.path], a, b)
            f.annotated = f"code_explorer/{ANNOTATED[f.path]}"
        else:
            f.code = "\n".join(modules[f.path]["lines"][f.first - 1:f.end])
            f.annotated = None

    # registry
    reg = []
    for f in sorted(fns, key=lambda f: f.id):
        reg.append({"id": f.id, "name": f.qual, "kind": f.kind, "status": f.status, "category": f.category, "subfolder": f.sub,
                    "file": f.path, "lines": [f.first, f.end], "signature": f.sig, "async": f.is_async, "decorators": f.decorators,
                    "routes": [{"method": m, "path": p} for m, p in f.routes], "raises": f.raises, "summary": f.doc,
                    "annotated_copy": f.annotated, "calls": [e["to"] for e in out_map.get(f.id, [])],
                    "called_by": [e["from"] for e in in_map.get(f.id, [])], "tests": f.tests})
    (CE / "registry").mkdir(exist_ok=True)
    id_file.write_text(json.dumps(ids, indent=1, sort_keys=True) + "\n")
    (CE / "registry" / "functions.json").write_text(json.dumps({"generated_by": "code_explorer/tools/build_code_explorer.py", "functions": reg,
                                                               "flowise_nodes": [{k: v for k, v in n.items() if k != "code"} for n in fnodes]}, indent=1) + "\n")
    (CE / "registry" / "dependencies.json").write_text(json.dumps({"edges": all_edges, "kinds": sorted({e["kind"] for e in all_edges})}, indent=1) + "\n")

    # Flowise custom JS copies
    jsdir = CE / "07_flowise_functions" / "custom_js"
    for rel, text in js_files:
        p = jsdir / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text if text.endswith("\n") else text + "\n", encoding="utf-8")

    write_docs(fns, fnodes, all_edges, out_map, in_map, labels, ann_ok, problems)
    write_backend_docs(fns, out_map, labels, problems)
    write_viewer(fns, fnodes, all_edges, labels)
    write_codemap_spec(fns, fnodes, all_edges, labels)
    used = sum(f.status.startswith("used") for f in fns)
    print(f"{len(fns)} definitions ({sum(f.kind not in ('class', 'pydantic_model', 'test') for f in fns)} functions/methods, "
          f"{sum(f.kind in ('class', 'pydantic_model') for f in fns)} classes, {sum(f.kind == 'test' for f in fns)} tests), "
          f"{sum(len(f.routes) for f in fns)} routes, {len(fnodes)} Flowise nodes, {len(all_edges)} edges, {used} used, "
          f"{sum(f.status == 'unused?' for f in fns)} unused?, problems: {len(problems)}")
    return 1 if problems else 0


def md_table(rows: list[list], head: list[str]) -> str:
    esc = lambda v: str(v).replace("|", "\\|").replace("\n", " ")  # noqa: E731
    return "\n".join(["| " + " | ".join(head) + " |", "|" + "---|" * len(head)] + ["| " + " | ".join(esc(c) for c in r) + " |" for r in rows])


def write_docs(fns, fnodes, edges, out_map, in_map, labels, ann_ok, problems):
    def link(f):
        return f"[{f.path}:{f.first}](../{f.path}#L{f.first})"
    rows = []
    for f in sorted(fns, key=lambda f: f.id):
        route = "; ".join(f"{m} {p}" for m, p in f.routes)
        flowise = ", ".join(labels[e["from"]] for e in in_map.get(f.id, []) if e["from"].startswith("flowise:"))[:120]
        callers = ", ".join(labels[e["from"]].split(" ", 1)[0] for e in in_map.get(f.id, []) if not e["from"].startswith("flowise:"))[:80]
        rows.append([f.id, f"{f.category}/{f.sub}", f"`{f.qual}`", link(f), f.kind, f.status, (f.doc or "")[:90], callers, route, flowise])
    (CE / "FUNCTION_INDEX.md").write_text(
        "# Function index (generated)\n\nEvery function, method and class of the tracked Python source, with stable ids. "
        "Status: `used` = reachable from a route, LangGraph graph, MCP tool, Flowise node or script entry point; `used (framework)` = called by "
        "FastAPI / Pydantic / LangGraph; `tooling` = scripts and deploy helpers; `test` = pytest; `unused?` = no caller found (review).\n\n"
        "Regenerate: `python3 code_explorer/tools/build_code_explorer.py`.\n\n"
        + md_table(rows, ["ID", "Folder", "Function / class", "Original file", "Kind", "Status", "Summary", "Called by", "FastAPI endpoint", "Flowise node"]) + "\n",
        encoding="utf-8")

    # endpoints
    rrows = []
    for f in sorted([f for f in fns if f.routes], key=lambda f: (f.path, f.first)):
        for m, p in f.routes:
            deps = ", ".join(labels[e["to"]] for e in out_map.get(f.id, []) if e["kind"] in ("depends_on", "validates_input"))
            calls = ", ".join(labels[e["to"]] for e in out_map.get(f.id, []) if e["kind"] == "calls")[:160]
            fl = ", ".join(labels[e["from"]] for e in in_map.get(f.id, []) if e["from"].startswith("flowise:"))[:160]
            rrows.append([f.id, m, p, f"`{f.name}`", "scinsight :8100" if "scinsight" in f.path else "gateway :8000", deps, calls, fl])
    (CE / "01_fastapi" / "ENDPOINTS.md").write_text("# FastAPI endpoints (generated)\n\nBoth apps declare routes directly on `app` (no `APIRouter`, no prefixes), "
                                                    "so the decorator path is the full path.\n\n" + md_table(rrows, ["ID", "Method", "Path", "Handler", "App", "Depends / body model", "Calls", "Called from Flowise"]) + "\n", encoding="utf-8")

    # tool mappings
    trows = []
    for n in fnodes:
        tgt = [labels[e["to"]] for e in edges if e["from"] == n["id"]]
        trows.append([n["label"], n["source"], ", ".join(sorted(set(tgt))) or "(no API call)"])
    d = CE / "07_flowise_functions" / "tool_mappings"
    d.mkdir(parents=True, exist_ok=True)
    (d / "FLOWISE_TO_PYTHON.md").write_text("# Flowise → FastAPI → Python (generated)\n\nEvery Flowise Custom Tool and Agentflow Custom Function, the SCInsight "
                                            "endpoints it calls (parsed from its JavaScript), and therefore the Python handler that runs.\n\n"
                                            + md_table(trows, ["Flowise node", "Source", "FastAPI handler(s)"]) + "\n", encoding="utf-8")

    # folder FUNCTIONS.md (home folders) + topic indexes
    groups = defaultdict(list)
    for f in fns:
        groups[f"{f.category}/{f.sub}"].append(f)
    for folder, items in groups.items():
        p = CE / folder
        p.mkdir(parents=True, exist_ok=True)
        rows = [[f.id, f"`{f.qual}`", f.kind, f.status, link_from(folder, f), f"[annotated](../../{f.annotated.split('code_explorer/', 1)[1]})" if f.annotated else "—",
                 (f.doc or "")[:80]] for f in sorted(items, key=lambda f: (f.path, f.first))]
        modules_here = sorted({f.path for f in items})
        (p / "FUNCTIONS.md").write_text(f"# {folder} (generated)\n\nModules: " + ", ".join(f"`{m}`" for m in modules_here) + "\n\n"
                                        + md_table(rows, ["ID", "Function / class", "Kind", "Status", "Original", "Annotated copy", "Summary"]) + "\n", encoding="utf-8")
    for folder, pattern in TOPICS.items():
        items = [f for f in fns if f.kind not in ("test",) and re.search(pattern, f.qual, re.I) and f.annotated and f.category == folder.split("/")[0]]
        p = CE / folder
        p.mkdir(parents=True, exist_ok=True)
        rows = [[f.id, f"`{f.qual}`", f.path, f"[annotated](../../{f.annotated.split('code_explorer/', 1)[1]})", (f.doc or "")[:80]] for f in items]
        (p / "FUNCTIONS.md").write_text(f"# Topic index: {folder.split('/')[1]} (generated)\n\nNo code copies here: the functions below live in their home "
                                        "module (one annotated copy per real module).\n\n" + md_table(rows, ["ID", "Function", "Original file", "Annotated copy", "Summary"]) + "\n", encoding="utf-8")

    # coverage
    total = len(fns)
    annotated = sum(1 for f in fns if f.annotated)
    unused = [f for f in fns if f.status == "unused?"]
    cov = [f"# Coverage report (generated)\n",
           f"- Definitions discovered: **{total}** ({sum(f.kind not in ('class', 'pydantic_model', 'test') for f in fns)} functions / methods, "
           f"{sum(f.kind in ('class', 'pydantic_model') for f in fns)} classes / models, {sum(f.kind == 'test' for f in fns)} tests)",
           f"- FastAPI endpoints: **{sum(len(f.routes) for f in fns if f.path.startswith('backend'))}** "
           f"(SCInsight {sum(len(f.routes) for f in fns if f.path == 'backend/scinsight/app.py')}, gateway {sum(len(f.routes) for f in fns if f.path == 'backend/app/main.py')}, "
           f"MCP {sum(len(f.routes) for f in fns if f.path == 'backend/app/mcp_server.py')})",
           f"- Flowise nodes with code: **{len(fnodes)}** (Custom Tools + Agentflow Custom Functions), copied to `07_flowise_functions/custom_js/`",
           f"- Definitions with an annotated copy: **{annotated}** in **{len(ANNOTATED)}** modules; AST-identical to the original: "
           f"**{sum(ann_ok.values())}/{len(ANNOTATED)}**",
           f"- Call / dependency edges: **{len(edges)}**",
           "", "## Not annotated line by line (indexed with full original source in the registry, viewer and Flowise map)", ""]
    for path in sorted({f.path for f in fns if not f.annotated}):
        cov.append(f"- `{path}` — {'pytest tests' if path.startswith('tests/') else 'ops / deploy tooling (not part of the runtime)'}")
    cov += ["", "## Unused? (no caller found by static analysis — review before deleting; dynamic calls may exist)", ""]
    cov += [f"- {f.id} `{f.qual}` ({f.path}:{f.first})" for f in unused] or ["- none"]
    cov += ["", "## Problems", ""] + ([f"- {p}" for p in problems] or ["- none"])
    (CE / "COVERAGE.md").write_text("\n".join(cov) + "\n", encoding="utf-8")


# Main backend functions for the README: hand-picked (layer, "file::qualname", role). Links / line numbers are resolved from the
# live code, and a name that no longer exists is reported as a problem, so the table cannot silently go stale.
MAIN_FUNCTIONS = [
    ("FastAPI app", "backend/scinsight/app.py::create_app", "SCInsight API factory (:8100): loads fixtures, RAG and security, registers the 31 governed routes"),
    ("FastAPI app", "backend/app/main.py::create_app", "SPARC / Aurelia gateway factory (:8000): middleware, SAP facade, analyses, agents, RAG, approvals, UI"),
    ("FastAPI app", "backend/app/main.py::create_app.request_context", "Middleware: correlation id, active tenant, Prometheus request metrics"),
    ("FastAPI app", "backend/app/main.py::create_app.value_error_handler", "Turns any business ValueError into HTTP 422 VALIDATION_ERROR"),
    ("FastAPI app", "backend/app/config.py::get_settings", "Gateway settings from environment / .env (cached)"),
    ("FastAPI app", "backend/scinsight/settings.py::SciSettings", "SCInsight settings: database, user keys, RAG and SAP-write guard"),
    ("Security", "backend/app/main.py::create_app.principal", "Dependency: API key -> identity + role, tenant scope check; denials audited"),
    ("Security", "backend/app/main.py::create_app.reader", "Dependency: assistant or manager may read and analyse"),
    ("Security", "backend/app/main.py::create_app.manager", "Dependency: only a manager may decide, execute or change settings"),
    ("Security", "backend/app/auth.py::ApiKeyAuth.authenticate", "Constant-time API-key lookup -> Principal (identity, role)"),
    ("Security", "backend/scinsight/app.py::create_app.principal", "SCInsight dependency: key -> user, tenant and roles (never taken from the request body)"),
    ("Security", "backend/scinsight/security.py::Security.require", "Role check for an action (agent_service can never approve)"),
    ("Security", "backend/scinsight/security.py::Security.audit", "Append-only, hash-chained audit event"),
    ("Security", "backend/scinsight/security.py::Security.verify_chain", "Verifies the audit hash chain was not altered"),
    ("SAP data", "backend/app/sap.py::SapRepository", "Read-only SAP S/4HANA mock: validated snapshot + OData-shaped entity sets"),
    ("SAP data", "backend/app/sap.py::SapRepository.validate_codes", "Rejects unknown plant / material / supplier codes before any calculation"),
    ("SAP data", "backend/app/tenants.py::TenantRegistry.get", "Per-customer SAP, engine and dashboards (multi-tenant)"),
    ("SAP data", "backend/scinsight/fixtures.py::load", "Loads the synthetic Belleva SAP fixtures (idempotent)"),
    ("SAP data", "backend/scinsight/db.py::Database.transaction", "SQLite / PostgreSQL access; several statements all-or-nothing"),
    ("Business rules", "backend/app/engine.py::SupplyChainEngine.factory_readiness", "BOM material readiness for a production run (shortages, ETAs)"),
    ("Business rules", "backend/app/engine.py::SupplyChainEngine.stock_balance", "Demand forecast + transfer proposals across warehouses"),
    ("Business rules", "backend/app/engine.py::SupplyChainEngine.supplier_scorecard", "OTIF, delays, quality rejects, single-source risk per supplier"),
    ("Business rules", "backend/app/engine.py::SupplyChainEngine.sales_order_fulfilment", "Allocates stock + inbound to open sales orders by date"),
    ("Business rules", "backend/app/engine.py::SupplyChainEngine.position_health", "Coverage of every stocked position against its target"),
    ("Business rules", "backend/app/forecasting.py::forecast", "XGBoost daily demand forecast"),
    ("Business rules", "backend/app/optimizer.py::optimize_transfers", "OR-Tools warehouse rebalancing (greedy fallback)"),
    ("Business rules", "backend/scinsight/business.py::calculate_usable_stock", "Usable stock from SAP batches with an itemised exclusion list"),
    ("Business rules", "backend/scinsight/business.py::calculate_bom_requirements", "Material requirements from the approved BOM version"),
    ("Business rules", "backend/scinsight/business.py::calculate_material_shortage", "Shortage after usable stock and POs arriving before the need date"),
    ("Business rules", "backend/scinsight/business.py::evaluate_transfer_feasibility", "Can a warehouse transfer arrive in time and in quantity"),
    ("Business rules", "backend/scinsight/business.py::compare_supply_options", "Ranks supply options: feasible, in time, coverage, cost, speed"),
    ("Business rules", "backend/scinsight/business.py::estimate_supplier_lead_time", "Empirical supplier lead time from goods receipts"),
    ("Business rules", "backend/scinsight/business.py::reconcile_actual_outcome", "Compares a prediction with the real SAP outcome"),
    ("Use cases", "backend/scinsight/service.py::Service.material_readiness", "Production readiness: BOM, usable stock, shortages, supply options -> CALC id"),
    ("Use cases", "backend/scinsight/service.py::Service.warehouse_balancing", "Warehouse transfer analysis -> CALC id"),
    ("Use cases", "backend/scinsight/service.py::Service.forecast_demand", "Demand forecast and days of cover -> CALC id"),
    ("Use cases", "backend/scinsight/service.py::Service.create_decision", "Turns a calculation into a recommendation (REC) waiting for approval"),
    ("Use cases", "backend/scinsight/service.py::Service.review", "Manager approves / rejects a recommendation (never the agent)"),
    ("Use cases", "backend/scinsight/service.py::Service.reconcile", "Verifies the outcome against SAP goods receipts after execution"),
    ("Use cases", "backend/scinsight/learning.py::train_lead_time_model", "Trains a lead-time model; promoted only if it beats the baseline"),
    ("Persistence", "backend/app/store.py::Store.audit", "Gateway audit log (hash chained)"),
    ("Persistence", "backend/app/store.py::Store.submit", "Saves a recommendation from an analysis"),
    ("Persistence", "backend/app/store.py::Store.decide", "Records the manager's decision"),
    ("Persistence", "backend/app/store.py::Store.execute_recommendation", "Writes approved documents to the SAP sandbox outbox (never production SAP)"),
    ("RAG", "backend/scinsight/rag.py::KnowledgeBase.ingest_dir", "SCInsight RAG ingestion: validate front matter, chunk, embed, store"),
    ("RAG", "backend/scinsight/rag.py::KnowledgeBase.search", "Tenant / role / validity-filtered vector search with citations"),
    ("RAG", "backend/scinsight/rag.py::chunk_document", "Section-aware chunking (900 chars, 120 overlap)"),
    ("RAG", "backend/app/rag.py::PgVectorRag.search", "Gateway RAG search on PostgreSQL + pgvector"),
    ("RAG", "backend/app/rag.py::FastEmbedder.embed", "BAAI/bge-small-en-v1.5 embeddings (also served at /v1/embeddings for Flowise)"),
    ("AI agents", "backend/app/llm.py::chat_model", "Qwen through an OpenAI-compatible endpoint (vLLM / Ollama)"),
    ("AI agents", "backend/app/copilot.py::get_backend", "One governed backend for every agent runtime (local engine or HTTP API)"),
    ("AI agents", "backend/app/runner.py::GraphRunner.run", "Runs a LangGraph graph on LangGraph Server or in-process"),
    ("AI agents", "backend/app/runner.py::GraphRunner.resume", "Resumes a graph after a human-in-the-loop interrupt"),
    ("AI agents", "backend/app/graphs.py::approval_gate", "Business graph: pauses for human approval before submitting"),
    ("AI agents", "backend/app/agentflow.py::supervisor", "LangGraph mirror of the Flowise AgentFlow: picks the role specialist"),
    ("AI agents", "backend/app/deep_agent.py::build_deep_agent", "Deep Agent supplier research with harness limits"),
    ("AI agents", "backend/scinsight/lg/supervisor.py::build_supervisor", "LangGraph mirror of the SC Agent Manager Agentflow"),
    ("AI agents", "backend/scinsight/lg/chat.py::evidence_gate", "Every number in an answer must come from a tool result"),
    ("AI agents", "backend/app/mcp_server.py::create_mcp_app", "Restricted MCP server exposing read-only tools"),
    ("Developer tools", "backend/app/code_editor.py::CodeEditor.update", "Backend code page: validated, backed-up edit of one function (development only)"),
]


def write_backend_docs(fns, out_map, labels, problems):
    """BACKEND_FUNCTIONS.md (every backend definition, linked) + the generated README section (modules + FastAPI endpoints)."""
    back = [f for f in fns if f.path.startswith("backend/")]
    files = sorted({f.path for f in back})
    anchor = lambda p: re.sub(r"[^a-z0-9_ -]", "", p.lower()).replace(" ", "-")  # noqa: E731  GitHub heading slug

    def role(path):  # first line of the module docstring, else the annotated copy's "What this module is" line
        doc = ast.get_docstring(ast.parse((ROOT / path).read_text(encoding="utf-8"))) or ""
        if not doc and path in ANNOTATED:
            m = re.search(r"# What this module is: (.*)", (CE / ANNOTATED[path]).read_text(encoding="utf-8"))
            doc = m.group(1) if m else ""
        return doc.strip().splitlines()[0][:140] if doc.strip() else ""

    def auth(f):  # FastAPI dependencies of a route: who may call it
        deps = {labels[e["to"]].split(" ", 1)[1].split(".")[-1].rstrip("()") for e in out_map.get(f.id, []) if e["kind"] == "depends_on"}
        return ", ".join(sorted(deps)) or "public"

    # full list, one table per module
    out = ["# Backend functions (generated)", "",
           f"Every function, method, class and route under `backend/`: **{len(back)}** definitions in **{len(files)}** modules, "
           f"**{sum(len(f.routes) for f in back)}** FastAPI routes. Links open the exact source line; *annotated* opens the commented copy.", "",
           "Regenerate: `python3 code_explorer/tools/build_code_explorer.py`.", ""]
    for path in files:
        items = sorted((f for f in back if f.path == path), key=lambda f: f.first)
        out += [f"## {path}", "", role(path), ""]
        rows = [[f.id, f"[`{f.qual}`](../{f.path}#L{f.first})", f.kind, "; ".join(f"{m} {p}" for m, p in f.routes), f.status,
                 f"[annotated](../{f.annotated})" if f.annotated else "—", (f.doc or "").splitlines()[0][:90] if f.doc else ""] for f in items]
        out += [md_table(rows, ["ID", "Function", "Kind", "FastAPI route", "Status", "Annotated", "Summary"]), ""]
    (CE / "BACKEND_FUNCTIONS.md").write_text("\n".join(out), encoding="utf-8")

    # README section (links relative to the repository root)
    mrows = [[f"[{p}]({p})", role(p), sum(1 for f in back if f.path == p and f.kind not in ("class", "pydantic_model")),
              sum(1 for f in back if f.path == p and f.kind in ("class", "pydantic_model")), sum(len(f.routes) for f in back if f.path == p),
              f"[list](code_explorer/BACKEND_FUNCTIONS.md#{anchor(p)})"] for p in files]
    rrows = []
    for f in sorted((f for f in back if f.routes), key=lambda f: (f.path, f.first)):
        app = "SCInsight :8100" if f.path.startswith("backend/scinsight") else ("MCP" if "mcp_server" in f.path else "Gateway :8000")
        for m, p in f.routes:
            rrows.append([app, m, f"`{p}`", f"[`{f.name}`]({f.path}#L{f.first})", auth(f), (f.doc or "").splitlines()[0][:80] if f.doc else ""])
    by_key = {f"{f.path}::{f.qual}": f for f in back}
    main_rows, code_doc, layer_now = [], ["# Main backend code (generated)", "",
                                          "The complete, current source of every element in the README table *Main backend functions*: whole FastAPI app "
                                          "factories with all their routes, whole classes with all their methods, full functions. Copied from `backend/` "
                                          "on each run of `python3 code_explorer/tools/build_code_explorer.py` (key, password, secret and token strings are masked).", ""], None
    secret = re.compile(r"""((?:api_key|apikey|password|secret|token)\w*\s*(?::\s*[\w |\[\]]+)?=\s*)(["'])[^"']+\2""", re.I)
    for layer, key, role_text in MAIN_FUNCTIONS:
        f = by_key.get(key)
        if not f:
            problems.append(f"MAIN_FUNCTIONS: {key} not found in the code (update the list)")
            continue
        app = "SCInsight" if f.path.startswith("backend/scinsight") else "Gateway"
        anchor_id = f.id.lower()
        main_rows.append([layer, f"[`{f.qual}`]({f.path}#L{f.first})", app, role_text, f"[full code](code_explorer/MAIN_BACKEND_CODE.md#{anchor_id})", f.id])
        # full source of the element (decorators included), from the live file
        src = (ROOT / f.path).read_text(encoding="utf-8").splitlines()[f.first - 1:f.end]
        indent = min((len(s) - len(s.lstrip()) for s in src if s.strip()), default=0)
        code = "\n".join(secret.sub(r"\1\2***\2", s[indent:]) for s in src)
        if layer != layer_now:
            code_doc += [f"## {layer}", ""]
            layer_now = layer
        code_doc += [f'<a id="{anchor_id}"></a>', f"### {f.id} · `{f.qual}` ({app})", "",
                     f"{role_text}  ", f"Source: [{f.path}:{f.first}-{f.end}](../{f.path}#L{f.first}) · {f.end - f.first + 1} lines"
                     + (f" · [annotated copy](../{f.annotated})" if f.annotated else ""), "",
                     "<details><summary>Show the full code</summary>", "", "```python", code, "```", "", "</details>", ""]
    (CE / "MAIN_BACKEND_CODE.md").write_text("\n".join(code_doc), encoding="utf-8")
    section = "\n".join([
        "<!-- BACKEND_FUNCTIONS:START (generated by code_explorer/tools/build_code_explorer.py; do not edit by hand) -->",
        "## Backend functions", "",
        f"**{len(back)}** Python definitions in **{len(files)}** backend modules, **{len(rrows)}** FastAPI routes. "
        "Full linked list of every function: [code_explorer/BACKEND_FUNCTIONS.md](code_explorer/BACKEND_FUNCTIONS.md) · "
        "call graph and ids: [code_explorer/FUNCTION_INDEX.md](code_explorer/FUNCTION_INDEX.md) · in the dashboard: **System → Backend code**.", "",
        "### Main backend functions", "",
        "The functions that carry the app, by layer (SCInsight = API on :8100, Gateway = SPARC / Aurelia on :8000). "
        "A request goes FastAPI route -> security dependency -> use case -> business rules on SAP data -> stored, audited result; "
        "agents and RAG call the same routes.", "",
        "Full source of every element below (whole FastAPI factories with their routes, whole classes): "
        "[code_explorer/MAIN_BACKEND_CODE.md](code_explorer/MAIN_BACKEND_CODE.md).", "",
        md_table(main_rows, ["Layer", "Function", "App", "Role", "Code", "ID"]), "",
        "### Modules", "", md_table(mrows, ["Module", "What it does", "Functions", "Classes", "Routes", "Functions list"]), "",
        "### FastAPI endpoints", "",
        "Access: `reader` = assistant or manager key, `manager` = manager key; SCInsight routes use their own role dependencies.", "",
        md_table(rrows, ["App", "Method", "Path", "Handler", "Access", "Summary"]), "",
        "<!-- BACKEND_FUNCTIONS:END -->"])
    readme = ROOT / "README.md"
    text = readme.read_text(encoding="utf-8")
    if "<!-- BACKEND_FUNCTIONS:START" in text:
        text = re.sub(r"<!-- BACKEND_FUNCTIONS:START.*?<!-- BACKEND_FUNCTIONS:END -->", lambda _: section, text, flags=re.S)
    else:
        text = text.replace("\n## What next\n", "\n" + section + "\n\n## What next\n", 1)
    readme.write_text(text, encoding="utf-8")


def link_from(folder: str, f) -> str:
    return f"[{f.path}:{f.first}](../../../{f.path}#L{f.first})"


def write_viewer(fns, fnodes, edges, labels):
    data = {"functions": [{"id": f.id, "name": f.qual, "kind": f.kind, "status": f.status, "category": f.category, "sub": f.sub, "file": f.path,
                           "lines": [f.first, f.end], "sig": f.sig, "summary": f.doc, "annotated": f.annotated, "code": f.code,
                           "routes": [f"{m} {p}" for m, p in f.routes], "tests": f.tests} for f in sorted(fns, key=lambda f: f.id)],
            "flowise": [{"id": n["id"], "name": n["label"], "kind": n["kind"], "status": "used", "category": "07_flowise_functions",
                         "sub": "custom_js", "file": n["source"], "lines": [0, 0], "sig": "", "summary": n.get("description", ""), "annotated": None,
                         "code": n["code"], "routes": [], "tests": []} for n in fnodes],
            "edges": edges, "labels": labels, "categories": CATEGORIES}
    page = VIEWER.replace("__DATA__", json.dumps(data).replace("</", "<\\/"))
    (CE / "viewer").mkdir(exist_ok=True)
    (CE / "viewer" / "index.html").write_text(page, encoding="utf-8")


def write_codemap_spec(fns, fnodes, edges, labels):
    """Input of flowise/code_explorer/build-code-map.cjs (runs inside the Flowise container, where /opt/flows = ./flowise)."""
    items = []
    for f in sorted(fns, key=lambda f: (f.category, f.sub, f.path, f.first)):
        if f.kind == "test" or f.kind == "class" and f.category != "01_fastapi":
            continue
        items.append({"id": f.id, "name": f.qual, "kind": f.kind, "status": f.status, "category": f.category, "sub": f.sub, "file": f.path,
                      "lines": f"{f.first}-{f.end}", "summary": f.doc, "annotated": f.annotated or "(original source)", "code": f.code,
                      "routes": [f"{m} {p}" for m, p in f.routes]})
    flow_items = [{"id": n["id"], "name": n["label"], "kind": n["kind"], "status": "used", "category": "07_flowise_functions", "sub": "custom_js",
                   "file": n["source"], "lines": "", "summary": n.get("description", ""), "annotated": "code_explorer/07_flowise_functions/custom_js",
                   "code": n["code"], "routes": []} for n in fnodes]
    keep = {i["id"] for i in items + flow_items}
    spec = {"categories": CATEGORIES, "items": items + flow_items, "labels": {k: v for k, v in labels.items() if k in keep},
            "edges": [e for e in edges if e["from"] in keep and e["to"] in keep]}
    out = ROOT / "flowise" / "code_explorer"
    out.mkdir(exist_ok=True)
    (out / "codemap_spec.json").write_text(json.dumps(spec) + "\n", encoding="utf-8")


VIEWER = r"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>SCInsight Code Explorer</title><style>
:root{--bg:#fafafa;--fg:#1d2330;--mut:#5d6677;--card:#fff;--line:#e3e6ec;--acc:#1a5fd1;--code:#f4f6f9}
@media (prefers-color-scheme:dark){:root{--bg:#14171c;--fg:#e6e9ef;--mut:#9aa3b2;--card:#1c2028;--line:#2b313c;--acc:#7aa8ff;--code:#11141a}}
*{box-sizing:border-box}body{margin:0;font:14px/1.5 system-ui,sans-serif;background:var(--bg);color:var(--fg)}
header{padding:12px 16px;border-bottom:1px solid var(--line)}h1{font-size:18px;margin:0}main{display:flex;height:calc(100vh - 54px)}
nav{width:360px;min-width:260px;border-right:1px solid var(--line);overflow:auto;padding:8px}section{flex:1;overflow:auto;padding:16px}
input{width:100%;padding:8px;border:1px solid var(--line);border-radius:6px;background:var(--card);color:var(--fg)}
.cat{margin-top:10px;font-weight:600;font-size:12px;color:var(--mut);text-transform:uppercase}.it{padding:3px 6px;border-radius:4px;cursor:pointer;font-family:ui-monospace,monospace;font-size:12px}
.it:hover,.it.on{background:var(--code)}pre{background:var(--code);padding:12px;border-radius:6px;overflow:auto;font-size:12px;line-height:1.45}
a{color:var(--acc);cursor:pointer}.tag{display:inline-block;padding:1px 6px;border:1px solid var(--line);border-radius:10px;font-size:11px;margin-right:4px}
@media (max-width:700px){main{flex-direction:column;height:auto}nav{width:auto;max-height:40vh}}
</style></head><body><header><h1>SCInsight Functions &amp; Code Explorer</h1></header><main><nav><input id="q" placeholder="search name, file, route…"><div id="list"></div></nav>
<section id="view"><p>Select a function. Code shown is the annotated copy (real code + comments) when one exists, else the original source.</p></section></main>
<script>const D=__DATA__;const all=D.functions.concat(D.flowise);const byId=Object.fromEntries(all.map(f=>[f.id,f]));
const out={},inn={};D.edges.forEach(e=>{(out[e.from]=out[e.from]||[]).push(e);(inn[e.to]=inn[e.to]||[]).push(e)});
const esc=s=>String(s??'').replace(/[&<>]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[c]));
function list(){const q=document.getElementById('q').value.toLowerCase();let h='',cur='';
all.filter(f=>!q||(f.name+f.file+f.routes.join(' ')+f.id).toLowerCase().includes(q)).sort((a,b)=>(a.category+a.sub).localeCompare(b.category+b.sub)||a.id.localeCompare(b.id)).forEach(f=>{
const c=f.category+'/'+f.sub;if(c!==cur){cur=c;h+=`<div class="cat">${esc(c)}</div>`}h+=`<div class="it" data-id="${esc(f.id)}">${esc(f.id.startsWith('flowise:')?'JS':f.id)} ${esc(f.name)}</div>`});
const l=document.getElementById('list');l.innerHTML=h;l.querySelectorAll('.it').forEach(e=>e.onclick=()=>show(e.dataset.id))}
const lk=e=>`<li><a onclick="show('${e}')">${esc(D.labels[e]||e)}</a></li>`;
function show(id){const f=byId[id];if(!f)return;location.hash=id;
document.getElementById('view').innerHTML=`<h2>${esc(f.name)}</h2><p><span class="tag">${esc(f.kind)}</span><span class="tag">${esc(f.status)}</span>${f.routes.map(r=>`<span class="tag">${esc(r)}</span>`).join('')}</p>
<p>${esc(f.summary)}</p><p><b>Original:</b> ${esc(f.file)}${f.lines[0]?':'+f.lines[0]+'-'+f.lines[1]:''}<br><b>Annotated copy:</b> ${esc(f.annotated||'—')}</p>
${f.sig?`<p><code>${esc(f.sig)}</code></p>`:''}<h3>Called by</h3><ul>${(inn[id]||[]).map(e=>lk(e.from)).join('')||'<li>none found</li>'}</ul>
<h3>Calls</h3><ul>${(out[id]||[]).map(e=>lk(e.to)).join('')||'<li>none found</li>'}</ul>${f.tests.length?`<h3>Tests</h3><ul>${f.tests.map(t=>`<li>${esc(t)}</li>`).join('')}</ul>`:''}
<h3>Source</h3><pre>${esc(f.code)}</pre>`}
document.getElementById('q').oninput=list;list();if(location.hash)show(decodeURIComponent(location.hash.slice(1)));</script></body></html>"""

if __name__ == "__main__":
    sys.exit(main())
