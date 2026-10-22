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
        3 upserts the credentials: Qwen (openAIApi) and the Flowise API key for Execute Flow (chatflowApi)
        4 upserts the 14 Custom Tools, then the 7 specialist Agentflows, the supervisor Agentflow and the Chatflow (by name),
          replacing __TOOL:<name>__ / __FLOW:<name>__ / __QWEN_*__ / __FLOWISE_*__ placeholders, and protects every flow with the API key
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
                                 "__TOOL:<name>__": "id of the imported Custom Tool <name>", "__FLOW:<name>__": "id of the imported flow <name>"}}
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
    dump(HERE / "manifest.json", manifest)
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
    }
    log("credentials: Qwen (openAIApi), Flowise API key for Execute Flow (chatflowApi)")

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
        text = (ROOT / flow["file"]).read_text(encoding="utf-8")
        for placeholder, value in bindings.items():
            text = text.replace(json.dumps(placeholder)[1:-1], json.dumps(value)[1:-1])
        unresolved = sorted({part.split("__")[0] for part in text.split("__FLOW:")[1:]}) if "__FLOW:" in text else []
        if unresolved or "__TOOL:" in text or "__QWEN_" in text or "__FLOWISE_" in text:
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
    i.add_argument("--sci-api-url", default="http://scinsight-api:8100", help="SCInsight API URL reachable from the Flowise container")
    i.add_argument("--qwen-model", default="")
    i.add_argument("--qwen-base-url", default="")
    i.add_argument("--key-env", default="FLOWISE_SCI_API_KEY", help="env variable that stores the Flowise API key")
    i.add_argument("--no-write-env", dest="write_env", action="store_false")
    i.add_argument("--state-file", default="", help="write the API key and flow ids to this JSON file instead of the env file")
    args = parser.parse_args()
    return build(Path(args.compose_dir)) if args.command == "build" else import_flows(args)


if __name__ == "__main__":
    sys.exit(main())
