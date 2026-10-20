# Flowise workflows

| File | Purpose |
| --- | --- |
| `build-flows.cjs` | Builds the Chatflow and AgentFlow V2 **inside the Flowise container** from the installed `flowise-components` node classes, so inputs/anchors/versions match the running Flowise exactly. |
| `bootstrap.py` | Headless provisioning: admin account → login → scoped API key → Variables (`copilot_api_url`, `copilot_tool_key`, `mcp_url`, `mcp_api_key`) → Qwen `openAIApi` credential → build + upsert both flows → writes `FLOWISE_API_KEY` / flow ids to `.env`. Idempotent. |
| `generated/*.json` | The last flows produced by `bootstrap.py` (for review and tests). |
| `inspect-nodes.cjs` | Prints node input definitions from the running Flowise (troubleshooting). |

```bash
python3 flowise/bootstrap.py --env-file .env --compose-dir .
docker compose --profile core up -d api   # the gateway proxy picks up the new API key
```

**Chatflow — "Aurelia Supply Chain Copilot - Chatflow"**: ChatOpenAI-Custom (Qwen) → Tool Agent ← Buffer Window Memory (8) ← Custom MCP (8 read-only tools via `{{$vars.mcp_url}}` with `{{$vars.mcp_api_key}}`).

**AgentFlow V2 — "Aurelia Supply Chain Supervisor - AgentFlow V2"**: Start → Condition Agent (4 scenarios) →
factory readiness agent / stock balancing agent / supplier & quality research agent (each with a scoped MCP tool set) or the
protected SAP boundary reply. The factory and balancing branches continue with Human Input (proceed/reject) → Custom Function
(hand-off payload) → HTTP `POST {{$vars.copilot_api_url}}/api/v1/recommendations/from-agent` → reply.

The hand-off never carries quantities: FastAPI selects the newest stored analysis of the expected kind among the ids the agent cited
and copies its deterministic proposed actions.

SSRF policy (`HTTP_SECURITY_CHECK=false` + explicit `HTTP_DENY_LIST` in `docker-compose.yml`): only the Docker bridge range is reachable.
