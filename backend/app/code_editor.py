"""Backend code section of the SPARC UI: browse every backend function and, on a development machine, edit one function.

Viewing reads the live source (AST, so line numbers are always current) and adds the code-explorer data when it is present
(code_explorer/registry/functions.json: stable id, status, calls / called by; annotated copy with comments).

Editing is off unless CODE_EDITOR_ENABLED=true AND APP_ENV is development or test, and only a manager may save. A save replaces
exactly one function or class of a file under backend/: the new text must parse, define that same name, and leave the module
parseable and compilable. The previous file is kept in backend/.data/code_backups/ and every save is audited by the caller.
Running servers pick the change up on restart (or immediately with `uvicorn --reload` on a source checkout).
"""
from __future__ import annotations

import ast
import hashlib
import json
import os
import textwrap
from datetime import datetime, timezone
from pathlib import Path

EDITABLE_PREFIX = "backend/"
DEV_ENVS = ("development", "test")
# The backend apps of docker-compose.yml and their entry modules; the files each app runs are found by following imports.
APPS = [
    {"id": "scinsight-api", "name": "SCInsight API", "kind": "FastAPI", "port": 8100,
     "start": "uvicorn backend.scinsight.app:create_app --factory", "entry": "backend/scinsight/app.py::create_app",
     "modules": ["backend.scinsight.app"]},
    {"id": "api", "name": "SPARC / Aurelia gateway", "kind": "FastAPI", "port": 8000,
     "start": "uvicorn backend.app.main:app", "entry": "backend/app/main.py::create_app", "modules": ["backend.app.main"]},
    {"id": "langgraph", "name": "LangGraph Server", "kind": "LangGraph", "port": 8123, "start": "langgraph dev (graphs in langgraph.json)",
     "entry": "backend/scinsight/lg/supervisor.py::build_supervisor",
     "modules": ["backend.app.graphs", "backend.app.agentflow", "backend.app.deep_agent", "backend.scinsight.lg.chat",
                 "backend.scinsight.lg.supervisor", "backend.scinsight.lg.specialists"]},
    {"id": "mcp", "name": "MCP server", "kind": "FastMCP", "port": 8002, "start": "python -m backend.app.mcp_server",
     "entry": "backend/app/mcp_server.py::create_mcp_app", "modules": ["backend.app.mcp_server"]},
]


def _defs(tree: ast.AST) -> dict[str, ast.AST]:
    """qualname -> def/class node, including methods and nested functions."""
    out: dict[str, ast.AST] = {}

    def walk(node, prefix):
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                out[f"{prefix}{child.name}"] = child
                walk(child, f"{prefix}{child.name}.")
            else:
                walk(child, prefix)
    walk(tree, "")
    return out


def _span(node) -> tuple[int, int]:
    return min([d.lineno for d in node.decorator_list] + [node.lineno]), node.end_lineno


class CodeEditor:
    def __init__(self, root: Path, enabled: bool, app_env: str):
        self.root = Path(root)
        self.edit_allowed = bool(enabled) and app_env in DEV_ENVS
        self.reason = ("" if self.edit_allowed else
                       "editing is disabled: set CODE_EDITOR_ENABLED=true on a development machine (APP_ENV=development)")

    # ------------------------------------------------------------------ index
    def _registry(self) -> dict[str, dict]:
        path = self.root / "code_explorer" / "registry" / "functions.json"
        try:
            rows = json.loads(path.read_text(encoding="utf-8"))["functions"]
        except (OSError, ValueError, KeyError):
            return {}
        return {f"{r['file']}::{r['name']}": r for r in rows}

    def _files(self) -> list[Path]:
        return sorted(p for p in (self.root / "backend").rglob("*.py") if ".data" not in p.parts and p.name != "__init__.py")

    def _apps_of(self, trees: dict[str, ast.AST]) -> dict[str, list[str]]:
        """file -> ids of the apps that load it (transitive backend imports from each app's entry modules)."""
        mod_of = {rel: rel[:-3].replace("/", ".") for rel in trees}
        known = set(mod_of.values())
        deps: dict[str, set[str]] = {}
        for rel, tree in trees.items():
            out = set()
            for n in ast.walk(tree):
                if isinstance(n, ast.ImportFrom) and n.module and n.module.startswith("backend"):
                    out |= {n.module} | {f"{n.module}.{a.name}" for a in n.names}
                elif isinstance(n, ast.Import):
                    out |= {a.name for a in n.names}
            deps[mod_of[rel]] = out & known
        apps: dict[str, list[str]] = {rel: [] for rel in trees}
        by_mod = {m: rel for rel, m in mod_of.items()}
        for app in APPS:
            seen, stack = set(), [m for m in app["modules"] if m in known]
            while stack:
                m = stack.pop()
                if m not in seen:
                    seen.add(m)
                    stack += deps.get(m, ())
            for m in seen:
                apps[by_mod[m]].append(app["id"])
        return apps

    def list(self, query: str = "", limit: int = 2000) -> dict:
        registry, rows = self._registry(), []
        q = query.lower().strip()
        trees = {}
        for path in self._files():
            try:
                trees[path.relative_to(self.root).as_posix()] = ast.parse(path.read_text(encoding="utf-8"))
            except SyntaxError:
                continue
        apps_of = self._apps_of(trees)
        for rel, tree in trees.items():
            defs = _defs(tree)
            for qual, node in defs.items():
                key = f"{rel}::{qual}"
                reg = registry.get(key, {})
                if q and q not in key.lower() and q not in (reg.get("summary") or "").lower():
                    continue
                first, end = _span(node)
                rows.append({"key": key, "id": reg.get("id"), "file": rel, "name": qual, "lines": [first, end],
                             "kind": reg.get("kind") or ("class" if isinstance(node, ast.ClassDef) else "function"),
                             "status": reg.get("status"), "category": reg.get("category") or rel.split("/")[1], "apps": apps_of[rel],
                             "summary": reg.get("summary") or (ast.get_docstring(node) or "").split("\n")[0]})
        components = [{k: v for k, v in app.items() if k != "modules"} | {"files": sorted(f for f, a in apps_of.items() if app["id"] in a)}
                      for app in APPS]
        return {"functions": rows[:limit], "total": len(rows), "edit_allowed": self.edit_allowed, "reason": self.reason,
                "registry": bool(registry), "components": components}

    def _locate(self, key: str) -> tuple[Path, str, list[str], ast.AST]:
        rel, sep, qual = key.partition("::")
        if not sep or not rel.startswith(EDITABLE_PREFIX) or ".." in Path(rel).parts or not rel.endswith(".py"):
            raise KeyError(key)
        path = self.root / rel
        if not path.is_file():
            raise KeyError(key)
        text = path.read_text(encoding="utf-8")
        node = _defs(ast.parse(text)).get(qual)
        if node is None:
            raise KeyError(key)
        return path, text, text.splitlines(), node

    def get(self, key: str) -> dict:
        path, text, lines, node = self._locate(key)
        first, end = _span(node)
        reg = self._registry()
        row = reg.get(key, {})
        labels = {r["id"]: f"{r['id']} {r['name']}" for r in reg.values()}
        keys = {r["id"]: k for k, r in reg.items()}
        annotated = None
        if row.get("annotated_copy"):
            try:
                ann_text = (self.root / row["annotated_copy"]).read_text(encoding="utf-8")
                ann_node = _defs(ast.parse(ann_text)).get(row["name"])
                if ann_node is not None:
                    a, b = _span(ann_node)
                    ann_lines = ann_text.splitlines()
                    while a > 1 and ann_lines[a - 2].strip().startswith("#"):  # include the comment header above the def
                        a -= 1
                    annotated = "\n".join(ann_lines[a - 1:b])
            except (OSError, SyntaxError):
                annotated = None
        link = lambda ids: [{"id": i, "label": labels.get(i, i), "key": keys.get(i)} for i in ids]  # noqa: E731
        return {"key": key, "id": row.get("id"), "file": path.relative_to(self.root).as_posix(), "name": key.split("::", 1)[1],
                "lines": [first, end], "source": "\n".join(lines[first - 1:end]), "annotated": annotated,
                "summary": row.get("summary") or (ast.get_docstring(node) or "").split("\n")[0], "status": row.get("status"),
                "routes": row.get("routes", []), "calls": link(row.get("calls", [])), "called_by": link(row.get("called_by", [])),
                "sha256": hashlib.sha256(text.encode()).hexdigest(), "edit_allowed": self.edit_allowed, "reason": self.reason,
                "apps": self._apps_of({p.relative_to(self.root).as_posix(): ast.parse(p.read_text(encoding="utf-8")) for p in self._files()})
                .get(path.relative_to(self.root).as_posix(), [])}

    # ------------------------------------------------------------------ edit
    def update(self, key: str, source: str, expected_sha256: str | None = None) -> dict:
        if not self.edit_allowed:
            raise PermissionError(self.reason)
        path, text, lines, node = self._locate(key)
        if expected_sha256 and expected_sha256 != hashlib.sha256(text.encode()).hexdigest():
            raise ValueError("the file changed since you opened it: reload the function before saving")
        first, end = _span(node)
        indent = lines[first - 1][: len(lines[first - 1]) - len(lines[first - 1].lstrip())]
        body = textwrap.dedent(source.replace("\r\n", "\n")).strip("\n")
        try:
            parsed = ast.parse(body)
        except SyntaxError as exc:
            raise ValueError(f"syntax error in the new code, line {exc.lineno}: {exc.msg}") from exc
        tops = [n for n in parsed.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))]
        if len(parsed.body) != 1 or len(tops) != 1 or tops[0].name != node.name:
            raise ValueError(f"the new code must be exactly one definition named {node.name}")
        new_block = [(indent + line) if line.strip() else "" for line in body.splitlines()]
        new_text = "\n".join(lines[:first - 1] + new_block + lines[end:]) + ("\n" if text.endswith("\n") else "")
        if new_text == text:
            return {"key": key, "changed": False}
        try:
            compile(new_text, str(path), "exec")
        except SyntaxError as exc:
            raise ValueError(f"the module would no longer compile, line {exc.lineno}: {exc.msg}") from exc
        backups = self.root / "backend" / ".data" / "code_backups"
        backups.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        backup = backups / f"{stamp}__{path.relative_to(self.root).as_posix().replace('/', '__')}"
        backup.write_text(text, encoding="utf-8")
        tmp = path.with_suffix(path.suffix + ".tmp")
        tmp.write_text(new_text, encoding="utf-8")
        os.replace(tmp, path)
        return {"key": key, "changed": True, "file": path.relative_to(self.root).as_posix(), "backup": backup.relative_to(self.root).as_posix(),
                "sha256_before": hashlib.sha256(text.encode()).hexdigest(), "sha256_after": hashlib.sha256(new_text.encode()).hexdigest(),
                "lines": [first, first + len(new_block) - 1],
                "note": "Saved. A running API loads the change after a restart (or immediately with uvicorn --reload on a source checkout)."}
