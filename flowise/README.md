# Flowise workflows

## What

The Flowise side of SPARC: two flows built and provisioned automatically, with no clicking in the Flowise editor.

* **Chatflow — "Aurelia Supply Chain Copilot - Chatflow"**: ChatOpenAI-Custom (Qwen) → Tool Agent ← Buffer Window Memory (8)
  ← Custom MCP (10 read-only tools via `{{$vars.mcp_url}}` with `{{$vars.mcp_api_key}}`).
* **AgentFlow V2 — "Aurelia Supply Chain Supervisor - AgentFlow V2"**: Start → Condition Agent (4 scenarios) → factory
  readiness agent / stock balancing agent / supplier & quality research agent (each with a scoped MCP tool set) or the
  protected SAP boundary reply. The factory and balancing branches continue with Human Input (proceed/reject) → Custom
  Function (hand-off payload) → HTTP `POST {{$vars.copilot_api_url}}/api/v1/recommendations/from-agent` → reply.

## Why

Flowise gives business users a visual, low-code view of the agents; LangGraph gives engineers code-level control. SPARC
runs both on the same governed tools so they can be compared like for like. Building the flows from the installed
`flowise-components` classes (rather than hand-edited JSON) keeps inputs, anchors and node versions exactly in line with
the running Flowise, so an upgrade cannot silently break them.

## So what

* The flows are reproducible: one command recreates the account, API key, variables, Qwen credential and both flows.
* The agents cannot invent numbers or write to SAP: the hand-off never carries quantities — FastAPI selects the newest
  stored analysis of the expected kind among the ids the agent cited and copies its deterministic proposed actions.
* Flowise can only reach the Docker bridge network: SSRF policy `HTTP_SECURITY_CHECK=false` plus an explicit
  `HTTP_DENY_LIST` in `docker-compose.yml`.

## For who

* **Business users and demo audiences** — open Flowise (http://localhost:3000 locally, signed in automatically) to see the
  agent graph, or use the *Flowise ⇄ LangGraph* page in SPARC to run both side by side.
* **Engineers** — change or extend the flows in `build-flows.cjs` and re-provision.

## Where

| File | Purpose |
| --- | --- |
| `build-flows.cjs` | Builds the Chatflow and AgentFlow V2 **inside the Flowise container** from the installed `flowise-components` node classes. |
| `bootstrap.py` | Headless provisioning: admin account → login → scoped API key → Variables (`copilot_api_url`, `copilot_tool_key`, `mcp_url`, `mcp_api_key`) → Qwen `openAIApi` credential → build + upsert both flows → writes `FLOWISE_API_KEY` / flow ids to `.env`. Idempotent. |
| `generated/*.json` | The last flows produced by `bootstrap.py` (for review and tests). |
| `inspect-nodes.cjs` | Prints node input definitions from the running Flowise (troubleshooting). |

## How

```bash
python3 flowise/bootstrap.py --env-file .env --compose-dir .
docker compose --profile core up -d api   # the gateway proxy picks up the new API key
```

`./start-localdemo.sh` and `make flowise` run the same provisioning. `tests/test_flowise_flows.py` checks the integrity of
`generated/*.json`; `scripts/smoke.py` runs both flows end to end against Qwen and the MCP server.

## What next

* Provision the same flows in the cloud: the app VM's bootstrap runs this provisioning, and `scripts/deploy-aws.sh` waits
  for it. This happens once the cloud environment is approved and running.
* Connect the flows to the selected customer tenant; today they use the Aurelia demo tenant.
