# Architecture and controls

## Runtime view

```text
                      Operator browser (HTTPS, allow-listed CIDR)
                                   │  Caddy (Let's Encrypt via sslip.io)
 ┌──────────────┬──────────────────┼────────────────────┬───────────────┬──────────────┐
 app.<domain>   flowise.<domain>   studio.<domain>      mcp.<domain>    grafana / langfuse
 │ Dashboard    │ Flowise 3.1.2    │ LangGraph Server   │ MCP server    │ Prometheus · Grafana
 │ FastAPI      │  Chatflow        │  supply_chain_chat │ Streamable    │ Langfuse v4 (ClickHouse,
 │  gateway     │  AgentFlow V2    │  supply_chain_     │ HTTP, API key │  Redis, SeaweedFS S3)
 │              │                  │    business        │               │
 │              │                  │  supplier_deep_    │               │
 │              │                  │    agent           │               │
 └──────┬───────┴────────┬─────────┴─────────┬──────────┴──────┬────────┘
        │  every agent tool call goes back through the governed gateway (API key, audit, metrics)
        ▼
  FastAPI gateway ── SAP S/4HANA mock (read-only OData; POST/PUT/PATCH/DELETE -> 405)
        │         ── deterministic engine: BOM readiness · XGBoost forecast · OR-Tools transfers ·
        │            supplier scorecard · QM impact · logistics escalation
        │         ── RAG: fastembed bge-small-en-v1.5 → pgvector (HNSW, cosine + SAP-code boost)
        │         ── governance ledger: analyses, recommendation queue, SHA-256 audit chain
        ▼
  PostgreSQL 17 + pgvector  (Compose locally · Amazon RDS · Cloud SQL)   databases: supplychain, flowise, langfuse

  Qwen2.5-7B-Instruct ── OpenAI-compatible API, tool calling (hermes parser)
     cloud: vLLM on NVIDIA L4 GPU VM (private, reachable only from the app VM)
     workstation: Ollama (GPUs vLLM does not support)
```

## Agent runtimes

| Runtime | What it is | Where the LLM is used | Human control |
| --- | --- | --- | --- |
| LangGraph Chat Graph | `MessagesState` graph: input guard → Qwen tool-calling agent ↔ `ToolNode` (9 read-only tools); deterministic fallback when the LLM is down; thread memory via the server checkpointer | tool selection, argument extraction, answer wording | SAP-write intents are refused by the guard before any LLM call |
| LangGraph AgentFlow | mirrors the Flowise AgentFlow V2: guardrail + Qwen structured-output supervisor → `create_agent` specialists (factory, balancing, research; scoped tools) → `interrupt()` → review queue; boundary node for SAP writes | routing and specialist reasoning | planner decides at `interrupt()`; the analysis to submit is read from the specialist's tool output in graph state, never from LLM text |
| LangGraph Business Graph | typed state machine: intake (Qwen structured output) → validate → one of six workflows → policy RAG → grounded narrative → `interrupt()` → submit/discard | parameter extraction and the briefing narrative only | planner decides at `interrupt()`; manager decides in the dashboard |
| Deep Agents | `create_deep_agent` with `write_todos` planning, virtual file system and three subagents (contract, quality, logistics analysts) | planning, delegation, report | advisory report only; no write tools exist |
| Flowise Chatflow | Tool Agent + ChatOpenAI-Custom (Qwen) + buffer-window memory + Custom MCP tool (8 tools) | tool calling and answer | — |
| Flowise AgentFlow V2 | Start → Condition Agent supervisor → factory / balancing / research Agent nodes (scoped MCP tools) → Human Input → HTTP hand-off → reply; SAP-write requests routed to a fixed boundary reply | routing and specialist reasoning | Human Input proceed/reject; the gateway selects the stored analysis server-side |

## Trust boundaries and controls

* **SAP is read-only.** The adapter exposes GET entity sets only; write verbs return 405 and are audited. No tool, graph node or flow can write to SAP. Accepted recommendations are executed manually by an authorized planner.
* **Numbers come from code, not the model.** Quantities, dates and costs are produced by the deterministic engine and stored with an `analysis_id`. A recommendation copies the proposed actions from the stored analysis; the Flowise hand-off endpoint (`/recommendations/from-agent`) selects the analysis server-side by kind and recency among the ids the agent cited, so an LLM cannot inject or alter quantities.
* **Roles.** Assistant keys (planner, flowise, langgraph, mcp) can read, analyse and submit; only the manager key can accept/reject or read the audit log.
* **Audit.** Every analysis, submission, decision, denial and agent run is appended to a SHA-256 hash chain (`/api/v1/audit` reports `chain_valid`).
* **Prompt injection.** Tool output and documents are framed as data; a supplier e-mail containing an "override" instruction is deliberately included in the corpus to demonstrate it is ignored.
* **SSRF.** Flowise tools/HTTP nodes may only reach the Docker bridge range (MCP, gateway); loopback, link-local (cloud metadata), VPC 10/8 and other private ranges are denied.
* **Network.** Only 443 (operator CIDR) and 80 (ACME challenge/redirect) are open; services bind to 127.0.0.1 behind Caddy; vLLM accepts traffic only from the app VM; PostgreSQL only from the app VM; no SSH port (AWS SSM / GCP IAP).
* **Secrets.** Generated by Terraform into AWS Secrets Manager / Google Secret Manager; written to a 0600 `.env` on the VM; never in images, flows or Git. Flowise flows reference `$vars` and a Flowise credential.

## Observability

* **Prometheus/Grafana** – request rate, error ratio, p95 latency per route, analyses per workflow, agent runs/latency per runtime, LLM errors, auth denials, vLLM token throughput (dashboard "SPARC — Smart Supply Chain Performer Copilot").
* **Langfuse v4** – LangGraph Chat/Business graphs and the Deep Agent emit OpenTelemetry spans (nodes, tool calls, LLM generations with token usage) via the Langfuse callback handler.
* **Cloud logs** – Docker daemon ships every container's logs to CloudWatch Logs (`awslogs`) or Cloud Logging (`gcplogs`); EC2 status-check alarms; optional AWS Budget / GCP budget alerts.
* **Flowise** keeps its own execution history for Chatflow and AgentFlow runs (Executions view).
