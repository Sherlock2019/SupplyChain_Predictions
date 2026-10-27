#!/usr/bin/env python3
"""Export and import the SupplyChain Insight AI (SCInsight) Flowise flows (stdlib only).

    python3 flowise/scinsight/deploy.py build             # generate the export files from the installed Flowise node classes
    python3 flowise/scinsight/deploy.py import [options]  # import the export files into a Flowise instance and bind them

build   runs flowise/scinsight/build-scinsight.cjs inside the Flowise container and writes
        flowise/tools/*.json, flowise/chatflows/*.json, flowise/agentflows/*.json, flowise/prompts/*.md and
        flowise/scinsight/manifest.json. The files hold placeholders, never credential ids, keys or flow ids.
import  reads ONLY those export files (so it also works against a clean Flowise instance) and:
        1 registers / logs in the admin, mints the API key "scinsight-flows" (chatflows, agentflows, tools, variables, credentials, executions)
        2 sets the Flowise Variables sci_api_url and sci_agent_key (the key never appears in a flow, prompt or export)
        3 upserts the credentials: Qwen (openAIApi), the Flowise API key for Execute Flow (chatflowApi), the RAG DB (PostgresApi)
          and the gateway embeddings key (openAIApi); creates / re-indexes the Document Store "SCInsight policy RAG DB"
        4 upserts the 14 Custom Tools, then the 7 specialist Agentflows, the supervisor Agentflow and the Chatflow (by name),
          replacing __TOOL:<name>__ / __FLOW:<name>__ / __QWEN_*__ / __FLOWISE_*__ / __SCI_*__ / __DOCSTORE:<name>__ placeholders,
          protects every flow with the API key, and indexes the Chatflow RAG DB (Flowise vector upsert API)
        5 writes FLOWISE_SCI_API_KEY / FLOWISE_SCI_CHATFLOW_ID / FLOWISE_SCI_SUPERVISOR_ID into the env file
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
FLOWISE_DIR = HERE.parent
ROOT = FLOWISE_DIR.parent
sys.path.insert(0, str(FLOWISE_DIR))
from bootstrap import Flowise, log, read_env, write_env  # noqa: E402

KEY_NAME = "scinsight-flows"
QWEN_CREDENTIAL = "scinsight-qwen"
FLOWISE_API_CREDENTIAL = "scinsight-flowise-api"
PG_CREDENTIAL = "scinsight-postgres-rag"
EMB_CREDENTIAL = "scinsight-rag-embeddings"
KNOWLEDGE_SRC = ROOT / "data" / "scinsight" / "knowledge"
KNOWLEDGE_OUT = HERE / "knowledge"  # mounted in the Flowise container at /opt/flows/scinsight/knowledge (RAG DB folder loader)
RAG_AGENT_ROLES = {"agent_service", "all"}  # the RAG DB is read through the agent key: index only what that key may read


def rag_documents() -> list[Path]:
    """Governed documents eligible for the native RAG DB: valid front matter, tenant scinsight-cosmetics, readable by the agent key."""
    out = []
    for path in sorted(KNOWLEDGE_SRC.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        if not text.startswith("---\n") or "\n---\n" not in text[4:]:
            continue
        meta = dict(line.split(":", 1) for line in text[4:].split("\n---\n", 1)[0].splitlines() if ":" in line)
        meta = {k.strip(): v.strip() for k, v in meta.items()}
        roles = {r.strip() for r in meta.get("access_roles", "").split(",")}
        if meta.get("tenant") == "scinsight-cosmetics" and meta.get("doc_id") and roles & RAG_AGENT_ROLES:
            out.append(path)
    return out
PERMISSION_GROUPS = {"chatflows", "agentflows", "tools", "variables", "credentials", "executions"}


# ----------------------------------------------------------------------------- build (export files)
def build(compose_dir: Path) -> int:
    command = ["docker", "compose", "exec", "-T", "-w", "/usr/local/lib/node_modules/flowise", "flowise", "node", "/opt/flows/scinsight/build-scinsight.cjs"]
    result = subprocess.run(command, cwd=compose_dir, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise SystemExit(f"build-scinsight.cjs failed: {result.stderr[-2000:]}")
    bundle = json.loads(result.stdout)
    for sub in ("tools", "chatflows", "agentflows", "prompts"):
        (FLOWISE_DIR / sub).mkdir(exist_ok=True)

    def dump(path: Path, data) -> str:
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        return str(path.relative_to(ROOT)).replace("\\", "/")

    manifest = {"generated_by": "flowise/scinsight/build-scinsight.cjs", "tools": [], "flows": [], "prompts": [],
                "import_order": "tools -> specialist agentflows -> supervisor agentflow -> chatflow",
                "placeholders": {"__QWEN_CREDENTIAL__": "Flowise credential (openAIApi) for the Qwen OpenAI-compatible endpoint",
                                 "__QWEN_MODEL__": "model name, e.g. qwen2.5-7b-scm", "__QWEN_BASE_URL__": "OpenAI-compatible base URL",
                                 "__FLOWISE_API_CREDENTIAL__": "Flowise credential (chatflowApi) holding the Flowise API key used by Execute Flow",
                                 "__FLOWISE_INTERNAL_URL__": "Flowise URL reachable from inside the Flowise container, e.g. http://flowise:3000",
                                 "__TOOL:<name>__": "id of the imported Custom Tool <name>", "__FLOW:<name>__": "id of the imported flow <name>",
                                 "__SCI_PG_CREDENTIAL__": "Flowise credential (PostgresApi) of the RAG DB", "__SCI_EMB_CREDENTIAL__": "Flowise credential (openAIApi) holding the gateway key for /v1/embeddings",
                                 "__SCI_EMBEDDINGS_URL__": "OpenAI-compatible embeddings base URL (FastAPI gateway /v1, bge-small)",
                                 "__SCI_PG_HOST__ / __SCI_PG_PORT__ / __SCI_PG_DATABASE__ / __SCI_PG_SSL__": "PostgreSQL of the RAG DB (database scinsight)",
                                 "__DOCSTORE:<name>__": "id:name of the Flowise Document Store <name> (Agentflow Retriever nodes)"}}
    for tool in bundle["tools"]:
        manifest["tools"].append(dump(FLOWISE_DIR / "tools" / f"{tool['name']}.json", tool))
    for spec in bundle["specialists"]:
        manifest["flows"].append({"name": spec["name"], "type": "AGENTFLOW", "role": "specialist", "intent": spec["intent"],
                                  "file": dump(FLOWISE_DIR / "agentflows" / f"{spec['name']}.json", spec["flow"])})
    sup = bundle["supervisor"]
    manifest["flows"].append({"name": sup["name"], "type": "AGENTFLOW", "role": "supervisor", "file": dump(FLOWISE_DIR / "agentflows" / f"{sup['name']}.json", sup["flow"])})
    chat = bundle["chatflow"]
    post = FLOWISE_DIR / "chatflows" / f"{chat['name']}.postprocessing.js"
    post.write_text("// Flowise > Chatflow configuration > Post Processing (evidence gate). Imported automatically by deploy.py.\n" + chat["postProcessing"], encoding="utf-8")
    manifest["flows"].append({"name": chat["name"], "type": "CHATFLOW", "role": "chat", "file": dump(FLOWISE_DIR / "chatflows" / f"{chat['name']}.json", chat["flow"]),
                              "chatbotConfig": dump(FLOWISE_DIR / "chatflows" / f"{chat['name']}.chatbotConfig.json", chat["chatbotConfig"]),
                              "postProcessing": str(post.relative_to(ROOT)).replace("\\", "/")})
    # Conversation starters: the 5 most-used questions of each role (data/scinsight/role_questions.json, shared with LangGraph + tests)
    roles = json.loads((ROOT / "data" / "scinsight" / "role_questions.json").read_text(encoding="utf-8"))["roles"]
    by_intent = {"factory": "factory_planning", "procurement": "procurement", "warehouse": "warehouse", "inventory": "inventory_optimizer",
                 "logistics": "logistics", "quality": "quality", "learning": "outcome_learning"}
    director = next(r for r in roles if r["role"] == "supply_chain_director")
    starters = lambda role: {"starterPrompts": {str(i): {"prompt": q["q"]} for i, q in enumerate(role["questions"])}}  # noqa: E731 - Flowise format
    for flow in manifest["flows"]:
        role = director if flow["role"] in ("supervisor", "chat") else next(r for r in roles if by_intent.get(r["specialist"]) == flow.get("intent"))
        config = {**(chat["chatbotConfig"] if flow["role"] == "chat" else {}), **starters(role)}
        folder = "chatflows" if flow["type"] == "CHATFLOW" else "agentflows"
        flow["chatbotConfig"] = dump(FLOWISE_DIR / folder / f"{flow['name']}.chatbotConfig.json", config)
        flow["starters_role"] = role["title"]
    for name, text in bundle["prompts"].items():
        path = FLOWISE_DIR / "prompts" / name
        path.write_text(text.rstrip() + "\n", encoding="utf-8")
        manifest["prompts"].append(str(path.relative_to(ROOT)).replace("\\", "/"))
    # company RAG DB: the Document Store spec + the governed documents the agent key may read (folder loader input)
    KNOWLEDGE_OUT.mkdir(exist_ok=True)
    for old in KNOWLEDGE_OUT.glob("*.md"):
        old.unlink()
    docs = rag_documents()
    for path in docs:
        (KNOWLEDGE_OUT / path.name).write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
    manifest["rag"] = {"docstore": dump(HERE / "rag_docstore.json", bundle["ragDocStore"]),
                       "knowledge": [str((KNOWLEDGE_OUT / p.name).relative_to(ROOT)).replace("\\", "/") for p in docs],
                       "source": "data/scinsight/knowledge (tenant scinsight-cosmetics, readable by agent_service)"}
    dump(HERE / "manifest.json", manifest)
    log(f"RAG DB: {len(docs)} governed documents -> {KNOWLEDGE_OUT.relative_to(ROOT)}")
    for flow in manifest["flows"]:
        data = json.loads((ROOT / flow["file"]).read_text(encoding="utf-8"))
        log(f"{flow['type']:9} {flow['name']}: {len(data['nodes'])} nodes, {len(data['edges'])} edges -> {flow['file']}")
    log(f"{len(manifest['tools'])} tools, {len(manifest['prompts'])} prompts, manifest flowise/scinsight/manifest.json")
    return 0


# ----------------------------------------------------------------------------- import (bind + upsert)
def ensure_api_key(flowise: Flowise, existing_key: str) -> dict:
    keys = flowise.call("GET", "/api/v1/apikey")
    match = next((k for k in keys if k.get("keyName") == KEY_NAME), None)
    if match and existing_key and match.get("apiKey") == existing_key:
        return match
    if match:
        flowise.call("DELETE", f"/api/v1/apikey/{match['id']}")
    catalogue = flowise.call("GET", "/api/v1/auth/permissions/API_KEY")
    permissions = sorted({p["key"] for group in catalogue.values() for p in group} if isinstance(catalogue, dict) else set())
    wanted = [p for p in permissions if p.split(":")[0] in PERMISSION_GROUPS]
    keys = flowise.call("POST", "/api/v1/apikey", {"keyName": KEY_NAME, "permissions": wanted or permissions})
    log(f"created API key '{KEY_NAME}' ({len(wanted or permissions)} permissions)")
    return next(k for k in keys if k.get("keyName") == KEY_NAME)


def import_flows(args) -> int:
    env_path = Path(args.env_file).resolve()
    env = read_env(env_path)
    manifest = json.loads((HERE / "manifest.json").read_text(encoding="utf-8"))
    flowise = Flowise(args.flowise_url)
    flowise.wait()
    email, password = env.get("FLOWISE_ADMIN_EMAIL", "admin@aurelia.local"), env["FLOWISE_ADMIN_PASSWORD"]
    try:
        flowise.call("POST", "/api/v1/account/register", {"user": {"name": "SCInsight Admin", "email": email, "credential": password}}, auth="none")
        log(f"registered admin {email}")
    except RuntimeError as exc:
        log("admin account exists" if "-> 400" in str(exc) else f"admin registration skipped ({str(exc)[:120]})")
    flowise.call("POST", "/api/v1/auth/login", {"email": email, "password": password}, auth="none")
    key = ensure_api_key(flowise, env.get(args.key_env, ""))
    flowise.api_key = key["apiKey"]

    variables = {"sci_api_url": args.sci_api_url, "sci_agent_key": env["SCI_AGENT_KEY"]}
    current = {v["name"]: v for v in flowise.call("GET", "/api/v1/variables", auth="key")}
    for name, value in variables.items():
        body = {"name": name, "value": value, "type": "static"}
        if name in current:
            flowise.call("PUT", f"/api/v1/variables/{current[name]['id']}", body, auth="key")
        else:
            flowise.call("POST", "/api/v1/variables", body, auth="key")
    log(f"variables: {', '.join(variables)} (values are not printed)")

    credentials = flowise.call("GET", "/api/v1/credentials", auth="key")

    def credential(name: str, kind: str, data: dict) -> str:
        found = next((c for c in credentials if c.get("name") == name), None)
        body = {"name": name, "credentialName": kind, "plainDataObj": data}
        if found:
            flowise.call("PUT", f"/api/v1/credentials/{found['id']}", body, auth="key")
            return found["id"]
        return flowise.call("POST", "/api/v1/credentials", body, auth="key")["id"]

    bindings = {
        "__QWEN_CREDENTIAL__": credential(QWEN_CREDENTIAL, "openAIApi", {"openAIApiKey": env.get("QWEN_API_KEY") or "local-qwen"}),
        "__FLOWISE_API_CREDENTIAL__": credential(FLOWISE_API_CREDENTIAL, "chatflowApi", {"chatflowApiKey": flowise.api_key}),
        "__QWEN_MODEL__": args.qwen_model or env.get("QWEN_MODEL", "qwen2.5-7b-scm"),
        "__QWEN_BASE_URL__": args.qwen_base_url or env.get("QWEN_BASE_URL", "http://host.docker.internal:11435/v1"),
        "__FLOWISE_INTERNAL_URL__": args.flowise_internal_url,
        # company RAG DB (PostgreSQL + pgvector, bge-small embeddings through the FastAPI gateway)
        "__SCI_PG_CREDENTIAL__": credential(PG_CREDENTIAL, "PostgresApi", {"user": env.get("POSTGRES_USER", "supplychain"), "password": env["POSTGRES_PASSWORD"]}),
        "__SCI_EMB_CREDENTIAL__": credential(EMB_CREDENTIAL, "openAIApi", {"openAIApiKey": env["FLOWISE_TOOL_KEY"]}),
        "__SCI_EMBEDDINGS_URL__": args.embeddings_url,
        "__SCI_PG_HOST__": env.get("POSTGRES_HOST", "postgres"),
        "__SCI_PG_DATABASE__": args.rag_database,
    }
    # typed values: the whole JSON string "__X__" is replaced by a number / boolean
    typed = {"__SCI_PG_PORT__": int(env.get("POSTGRES_PORT", "5432")), "__SCI_PG_SSL__": env.get("FLOWISE_DATABASE_SSL", "false") == "true"}
    log("credentials: Qwen (openAIApi), Flowise API key for Execute Flow (chatflowApi), RAG DB (PostgresApi), gateway embeddings (openAIApi)")

    def bind(text: str) -> str:
        for placeholder, value in typed.items():
            text = text.replace(json.dumps(placeholder), json.dumps(value))
        for placeholder, value in bindings.items():
            text = text.replace(json.dumps(placeholder)[1:-1], json.dumps(value)[1:-1])
        return text

    # Document Store of the company RAG DB (read by the Agentflow Retriever nodes): create once, then upsert = (re)index the folder
    spec = json.loads(bind((ROOT / manifest["rag"]["docstore"]).read_text(encoding="utf-8")))
    stores = flowise.call("GET", "/api/v1/document-store/store")
    store = next((s for s in stores if s.get("name") == spec["name"]), None) or \
        flowise.call("POST", "/api/v1/document-store/store", {"name": spec["name"], "description": spec["description"]})
    loaders = json.loads(store.get("loaders") or "[]") if isinstance(store.get("loaders"), str) else (store.get("loaders") or [])
    upsert = {k: spec[k] for k in ("loader", "splitter", "embedding", "vectorStore", "recordManager")}
    if loaders:  # keep one loader: refresh it instead of adding a second copy of every document
        upsert.update({"docId": loaders[0]["id"], "replaceExisting": True})
    result = flowise.call("POST", f"/api/v1/document-store/upsert/{store['id']}", upsert)
    bindings[f"__DOCSTORE:{spec['name']}__"] = f"{store['id']}:{spec['name']}"
    log(f"RAG DB document store '{spec['name']}' -> {store['id']} (added {result.get('numAdded', 0)}, updated {result.get('numUpdated', 0)}, "
        f"skipped {result.get('numSkipped', 0)}, deleted {result.get('numDeleted', 0)})")

    tools = {t["name"]: t for t in flowise.call("GET", "/api/v1/tools", auth="key")}
    for rel in manifest["tools"]:
        tool = json.loads((ROOT / rel).read_text(encoding="utf-8"))
        body = {k: tool[k] for k in ("name", "description", "color", "iconSrc", "schema", "func")}
        row = flowise.call("PUT", f"/api/v1/tools/{tools[tool['name']]['id']}", body, auth="key") if tool["name"] in tools \
            else flowise.call("POST", "/api/v1/tools", body, auth="key")
        bindings[f"__TOOL:{tool['name']}__"] = row["id"]
    log(f"custom tools: {len(manifest['tools'])} upserted")

    existing = {row["name"]: row for row in flowise.call("GET", "/api/v1/chatflows", auth="key")}
    existing.update({row["name"]: row for row in flowise.call("GET", "/api/v1/chatflows?type=AGENTFLOW", auth="key")})
    ids = {}
    for flow in manifest["flows"]:  # specialists first: the supervisor references their ids
        text = bind((ROOT / flow["file"]).read_text(encoding="utf-8"))
        unresolved = sorted({part.split("__")[0] for part in text.split("__FLOW:")[1:]}) if "__FLOW:" in text else []
        if unresolved or any(p in text for p in ("__TOOL:", "__QWEN_", "__FLOWISE_", "__SCI_", "__DOCSTORE:")):
            raise SystemExit(f"{flow['name']}: unresolved placeholders {unresolved or '(tool/credential)'}")
        flow_data = json.loads(text)
        body = {"name": flow["name"], "flowData": json.dumps(flow_data), "deployed": True, "isPublic": False, "type": flow["type"],
                "category": "SupplyChain Insight AI", "apikeyid": key["id"]}
        if flow.get("chatbotConfig"):  # e.g. the Chatflow post-processing evidence gate
            body["chatbotConfig"] = (ROOT / flow["chatbotConfig"]).read_text(encoding="utf-8")
        row = flowise.call("PUT", f"/api/v1/chatflows/{existing[flow['name']]['id']}", body, auth="key") if flow["name"] in existing \
            else flowise.call("POST", "/api/v1/chatflows", body, auth="key")
        ids[flow["name"]] = row["id"]
        bindings[f"__FLOW:{flow['name']}__"] = row["id"]
        log(f"{flow['type']:9} {flow['name']} -> {row['id']} ({len(flow_data['nodes'])} nodes)")

    chat = next(f["name"] for f in manifest["flows"] if f["role"] == "chat")
    sup = next(f["name"] for f in manifest["flows"] if f["role"] == "supervisor")
    # Index the Chatflow RAG DB: folder loader -> markdown splitter -> embeddings -> pgvector (record manager: no duplicates)
    try:
        try:
            result = flowise.call("POST", f"/api/v1/vector/upsert/{ids[chat]}", {}, auth="key")
        except RuntimeError:
            result = flowise.call("POST", f"/api/v1/vector/internal-upsert/{ids[chat]}", {})
        log(f"Chatflow RAG DB (pgvector scinsight_flowise_rag): added {result.get('numAdded', 0)}, updated {result.get('numUpdated', 0)}, "
            f"skipped {result.get('numSkipped', 0)}, deleted {result.get('numDeleted', 0)}")
    except RuntimeError as exc:
        log(f"WARNING: Chatflow RAG DB indexing failed — the retriever tool returns nothing until it succeeds: {str(exc)[:300]}")
    if args.state_file:  # e.g. a second (clean) Flowise instance: keep its key and ids out of the main .env
        state = Path(args.state_file)
        state.write_text(json.dumps({"flowise_url": args.flowise_url, "api_key": flowise.api_key, "chatflow_id": ids[chat], "supervisor_id": ids[sup], "flows": ids}, indent=1))
        state.chmod(0o600)
        log(f"wrote {state}")
    elif args.write_env:
        write_env(env_path, {args.key_env: flowise.api_key, "FLOWISE_SCI_CHATFLOW_ID": ids[chat], "FLOWISE_SCI_SUPERVISOR_ID": ids[sup]})
        log(f"updated {env_path} ({args.key_env}, FLOWISE_SCI_CHATFLOW_ID, FLOWISE_SCI_SUPERVISOR_ID)")
    print(json.dumps({"flowise_url": args.flowise_url, "flows": ids}))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    b = sub.add_parser("build")
    b.add_argument("--compose-dir", default=str(ROOT))
    i = sub.add_parser("import")
    i.add_argument("--env-file", default=str(ROOT / ".env"))
    i.add_argument("--flowise-url", default="http://127.0.0.1:3000", help="Flowise URL reachable from this script")
    i.add_argument("--flowise-internal-url", default="http://flowise:3000", help="Flowise URL reachable from inside its own container (Execute Flow)")
    i.add_argument("--sci-api-url", default="http://api:8000/scinsight", help="SCInsight API URL reachable from the Flowise container")
    i.add_argument("--embeddings-url", default="http://api:8000/v1", help="OpenAI-compatible embeddings base URL reachable from the Flowise container")
    i.add_argument("--rag-database", default="scinsight", help="PostgreSQL database of the RAG DB tables")
    i.add_argument("--qwen-model", default="")
    i.add_argument("--qwen-base-url", default="")
    i.add_argument("--key-env", default="FLOWISE_SCI_API_KEY", help="env variable that stores the Flowise API key")
    i.add_argument("--no-write-env", dest="write_env", action="store_false")
    i.add_argument("--state-file", default="", help="write the API key and flow ids to this JSON file instead of the env file")
    args = parser.parse_args()
    return build(Path(args.compose_dir)) if args.command == "build" else import_flows(args)


if __name__ == "__main__":
    sys.exit(main())
