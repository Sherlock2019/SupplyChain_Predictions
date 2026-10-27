from __future__ import annotations

import ast
from pathlib import Path

import pytest

from backend.app.code_editor import CodeEditor

MODULE = '''"""demo"""


def keep(x):
    return x


class Box:
    @staticmethod
    def size(n):
        return n * 2
'''


@pytest.fixture()
def repo(tmp_path: Path) -> Path:
    (tmp_path / "backend" / "app").mkdir(parents=True)
    (tmp_path / "backend" / "app" / "demo.py").write_text(MODULE)
    return tmp_path


def test_api_lists_and_shows_backend_functions_read_only_by_default(client, assistant_headers, manager_headers):
    listing = client.get("/api/v1/code/functions", params={"q": "calculate_material_shortage"}, headers=assistant_headers).json()
    assert listing["edit_allowed"] is False
    row = next(f for f in listing["functions"] if f["name"] == "calculate_material_shortage")
    assert row["file"] == "backend/scinsight/business.py"
    assert row["apps"] == ["scinsight-api"]  # files are grouped by the docker-compose app that imports them
    apps = {c["id"]: c for c in listing["components"]}
    assert apps["scinsight-api"]["kind"] == apps["api"]["kind"] == "FastAPI"
    assert "backend/app/engine.py" in apps["api"]["files"] and "backend/app/engine.py" in apps["mcp"]["files"]
    assert "backend/app/main.py" not in apps["mcp"]["files"]
    detail = client.get("/api/v1/code/function", params={"key": row["key"]}, headers=assistant_headers).json()
    assert detail["source"].lstrip().startswith("def calculate_material_shortage(")
    body = {"key": row["key"], "source": detail["source"]}
    assert client.put("/api/v1/code/function", json=body, headers=assistant_headers).status_code == 403  # planner key: never
    assert client.put("/api/v1/code/function", json=body, headers=manager_headers).status_code == 403  # flag off: never
    assert client.get("/api/v1/code/function", params={"key": "backend/../.env::x"}, headers=assistant_headers).status_code == 404


def test_rag_tuning_proxy_is_for_managers_and_needs_the_server_side_key(client, assistant_headers, manager_headers):
    assert client.get("/api/v1/rag-tuning/config", headers=assistant_headers).status_code == 403  # planners never reach the console
    r = client.get("/api/v1/rag-tuning/config", headers=manager_headers)
    assert r.status_code == 503 and "SCI_TUNING_KEY" in r.text  # not configured in tests: no key, no forwarding


def test_edit_replaces_only_the_selected_method_and_keeps_a_backup(repo):
    editor = CodeEditor(repo, enabled=True, app_env="development")
    key = "backend/app/demo.py::Box.size"
    current = editor.get(key)
    assert current["source"].startswith("    @staticmethod")
    result = editor.update(key, "@staticmethod\ndef size(n):\n    return n * 3\n", current["sha256"])
    text = (repo / "backend" / "app" / "demo.py").read_text()
    assert "return n * 3" in text and "def keep(x):" in text
    assert "    @staticmethod\n    def size(n):" in text  # re-indented to the class body
    ast.parse(text)
    assert (repo / result["backup"]).read_text() == MODULE


@pytest.mark.parametrize("source,error", [
    ("def size(n)\n    return n", "syntax error"),
    ("def other(n):\n    return n", "exactly one definition named size"),
    ("def size(n):\n    return n\nx = 1", "exactly one definition named size"),
])
def test_invalid_edits_are_refused_and_the_file_is_untouched(repo, source, error):
    editor = CodeEditor(repo, enabled=True, app_env="development")
    with pytest.raises(ValueError, match=error):
        editor.update("backend/app/demo.py::Box.size", source)
    assert (repo / "backend" / "app" / "demo.py").read_text() == MODULE


def test_editing_is_off_outside_development_and_stale_saves_are_refused(repo):
    with pytest.raises(PermissionError):
        CodeEditor(repo, enabled=True, app_env="production").update("backend/app/demo.py::keep", "def keep(x):\n    return 1\n")
    editor = CodeEditor(repo, enabled=True, app_env="development")
    with pytest.raises(ValueError, match="changed since you opened it"):
        editor.update("backend/app/demo.py::keep", "def keep(x):\n    return 1\n", "0" * 64)
