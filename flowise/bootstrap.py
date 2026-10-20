#!/usr/bin/env python3
"""Headless Flowise 3.x provisioning for the Aurelia supply-chain copilot (stdlib only; runs on any VM).

1. Register the admin account on a fresh Flowise database (no manual sign-up page).
2. Log in and mint an API key with the permissions the gateway and this script need.
3. Upsert Flowise Variables (gateway URL, tool keys, MCP URL/key) and a Qwen "openAIApi" credential.
4. Build the Chatflow and AgentFlow V2 inside the Flowise container (flowise/build-flows.cjs) and upsert them.
5. Record FLOWISE_API_KEY / FLOWISE_CHATFLOW_ID / FLOWISE_AGENTFLOW_ID in .env for the FastAPI Flowise proxy.

    python3 flowise/bootstrap.py --env-file .env [--compose-dir .] [--flowise-url http://127.0.0.1:3000]
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

CHATFLOW_NAME = "Aurelia Supply Chain Copilot - Chatflow"
AGENTFLOW_NAME = "Aurelia Supply Chain Supervisor - AgentFlow V2"
KEY_NAME = "aurelia-gateway"
CREDENTIAL_NAME = "qwen-openai-compatible"


def log(message: str) -> None:
    print(f"[flowise-bootstrap] {message}", flush=True)


def read_env(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in path.read_text().splitlines():
        if "=" in line and not line.lstrip().startswith("#"):
            key, _, value = line.partition("=")
            values[key.strip()] = value.strip()
    return values


def write_env(path: Path, updates: dict[str, str]) -> None:
    lines = path.read_text().splitlines()
    seen = set()
    for i, line in enumerate(lines):
        key = line.partition("=")[0].strip()
        if key in updates:
            lines[i] = f"{key}={updates[key]}"
            seen.add(key)
    lines += [f"{k}={v}" for k, v in updates.items() if k not in seen]
    path.write_text("\n".join(lines) + "\n")


class Flowise:
    def __init__(self, base: str):
        self.base = base.rstrip("/")
        # Session cookies are replayed explicitly: in the cloud Flowise marks them Secure (it sits behind HTTPS), while this
        # script talks to it over the VM loopback, and http.cookiejar refuses to send Secure cookies over plain HTTP.
        self.cookies: dict[str, str] = {}
        self.api_key = ""

    def call(self, method: str, path: str, body=None, auth: str = "cookie", ok=(200, 201)):
        data = json.dumps(body).encode() if body is not None else None
        request = urllib.request.Request(self.base + path, data=data, method=method)
        request.add_header("Content-Type", "application/json")
        # Behind Caddy every request arrives as HTTPS; tell Flowise the same so it issues its Secure session cookie.
        request.add_header("X-Forwarded-Proto", "https")
        if auth == "key":
            request.add_header("Authorization", f"Bearer {self.api_key}")
        elif auth == "cookie":
            # "internal" requests are authenticated by the UI session cookie instead of an API key.
            request.add_header("x-request-from", "internal")
            if self.cookies:
                request.add_header("Cookie", "; ".join(f"{k}={v}" for k, v in self.cookies.items()))
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                raw, status, headers = response.read(), response.status, response.headers
        except urllib.error.HTTPError as exc:
            raw, status, headers = exc.read(), exc.code, exc.headers
        for cookie in headers.get_all("Set-Cookie") or []:
            name, _, rest = cookie.partition("=")
            self.cookies[name.strip()] = rest.split(";", 1)[0]
        payload = json.loads(raw) if raw and raw[:1] in (b"{", b"[") else raw.decode(errors="replace")
        if status not in ok:
            raise RuntimeError(f"{method} {path} -> {status}: {str(payload)[:400]}")
        return payload

    def wait(self, attempts: int = 90) -> None:
        for _ in range(attempts):
            try:
                self.call("GET", "/api/v1/ping", auth="none")
                return
            except Exception:  # noqa: BLE001
                time.sleep(5)
        raise RuntimeError("Flowise did not become ready")


def build_flows(compose_dir: Path, env: dict[str, str], credential_id: str) -> dict:
    command = [
        "docker", "compose", "exec", "-T",
        "-e", f"QWEN_MODEL={env.get('QWEN_MODEL', '')}",
        "-e", f"QWEN_BASE_URL={env.get('QWEN_BASE_URL', '')}",
        "-e", f"QWEN_CREDENTIAL_ID={credential_id}",
        "-w", "/usr/local/lib/node_modules/flowise",
        "flowise", "node", "/opt/flows/build-flows.cjs",
    ]
    result = subprocess.run(command, cwd=compose_dir, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise RuntimeError(f"build-flows.cjs failed: {result.stderr[-1500:]}")
    return json.loads(result.stdout)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--env-file", default=".env")
    parser.add_argument("--compose-dir", default=".")
    parser.add_argument("--flowise-url", default=os.environ.get("FLOWISE_LOCAL_URL", "http://127.0.0.1:3000"))
    args = parser.parse_args()
    env_path = Path(args.env_file).resolve()
    env = read_env(env_path)
    email = env.get("FLOWISE_ADMIN_EMAIL", "admin@aurelia.local")
    password = env["FLOWISE_ADMIN_PASSWORD"]

    flowise = Flowise(args.flowise_url)
    flowise.wait()

    try:
        flowise.call("POST", "/api/v1/account/register", {"user": {"name": "Aurelia Admin", "email": email, "credential": password}}, auth="none")
        log(f"registered admin {email}")
    except RuntimeError as exc:
        log("admin account already exists" if "-> 400" in str(exc) else f"admin registration skipped ({str(exc)[:120]})")
    flowise.call("POST", "/api/v1/auth/login", {"email": email, "password": password}, auth="none")
    log("logged in")

    existing_key = env.get("FLOWISE_API_KEY", "")
    keys = flowise.call("GET", "/api/v1/apikey")
    match = next((k for k in keys if k.get("keyName") == KEY_NAME), None)
    if match and existing_key and match.get("apiKey") == existing_key:
        flowise.api_key = existing_key
    else:
        if match:
            flowise.call("DELETE", f"/api/v1/apikey/{match['id']}")
        catalogue = flowise.call("GET", "/api/v1/auth/permissions/API_KEY")
        permissions = sorted({p["key"] for group in catalogue.values() for p in group} if isinstance(catalogue, dict) else set())
        wanted = [p for p in permissions if p.split(":")[0] in {"chatflows", "agentflows", "variables", "credentials", "executions", "apikeys"}]
        keys = flowise.call("POST", "/api/v1/apikey", {"keyName": KEY_NAME, "permissions": wanted or permissions})
        flowise.api_key = next(k["apiKey"] for k in keys if k.get("keyName") == KEY_NAME)
        log(f"created API key '{KEY_NAME}' with {len(wanted or permissions)} permissions")

    variables = {
        "copilot_api_url": "http://api:8000",
        "copilot_tool_key": env["FLOWISE_TOOL_KEY"],
        "mcp_url": "http://mcp:8000/mcp",
        "mcp_api_key": env["MCP_CLIENT_KEY"],
    }
    current = {v["name"]: v for v in flowise.call("GET", "/api/v1/variables", auth="key")}
    for name, value in variables.items():
        body = {"name": name, "value": value, "type": "static"}
        if name in current:
            flowise.call("PUT", f"/api/v1/variables/{current[name]['id']}", body, auth="key")
        else:
            flowise.call("POST", "/api/v1/variables", body, auth="key")
    log(f"variables set: {', '.join(variables)}")

    credentials = flowise.call("GET", "/api/v1/credentials", auth="key")
    credential = next((c for c in credentials if c.get("name") == CREDENTIAL_NAME), None)
    cred_body = {"name": CREDENTIAL_NAME, "credentialName": "openAIApi", "plainDataObj": {"openAIApiKey": env.get("QWEN_API_KEY", "local-qwen")}}
    if credential:
        flowise.call("PUT", f"/api/v1/credentials/{credential['id']}", cred_body, auth="key")
        credential_id = credential["id"]
    else:
        credential_id = flowise.call("POST", "/api/v1/credentials", cred_body, auth="key")["id"]
    log(f"Qwen credential {credential_id}")

    flows = build_flows(Path(args.compose_dir).resolve(), env, credential_id)
    generated = Path(__file__).resolve().parent / "generated"
    try:
        generated.mkdir(exist_ok=True)
        for kind, name in (("chatflow", CHATFLOW_NAME), ("agentflow", AGENTFLOW_NAME)):
            (generated / f"{kind}.json").write_text(json.dumps({"name": name, "type": kind.upper(), **flows[kind]}, indent=1))
    except OSError:
        pass

    existing = {row["name"]: row for row in flowise.call("GET", "/api/v1/chatflows", auth="key")}
    ids = {}
    for kind, name, flow_type in (("chatflow", CHATFLOW_NAME, "CHATFLOW"), ("agentflow", AGENTFLOW_NAME, "AGENTFLOW")):
        body = {"name": name, "flowData": json.dumps(flows[kind]), "deployed": True, "isPublic": False, "type": flow_type, "category": "Supply Chain"}
        if name in existing:
            row = flowise.call("PUT", f"/api/v1/chatflows/{existing[name]['id']}", body, auth="key")
        else:
            row = flowise.call("POST", "/api/v1/chatflows", body, auth="key")
        ids[kind] = row["id"]
        log(f"{flow_type} '{name}' -> {row['id']} ({len(flows[kind]['nodes'])} nodes, {len(flows[kind]['edges'])} edges)")

    write_env(env_path, {"FLOWISE_API_KEY": flowise.api_key, "FLOWISE_CHATFLOW_ID": ids["chatflow"], "FLOWISE_AGENTFLOW_ID": ids["agentflow"]})
    log(f"updated {env_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
