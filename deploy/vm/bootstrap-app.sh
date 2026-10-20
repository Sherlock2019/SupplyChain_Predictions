#!/usr/bin/env bash
# Cloud-agnostic application VM deployment (AWS and GCP). Expects /opt/aurelia/.env written by the provider bootstrap
# and the application image already pulled. Idempotent: safe to re-run for updates.
set -euo pipefail
cd "$(dirname "$0")/../.."
APP_DIR=$(pwd)
log() { echo "[$(date -Is)] $*"; }

set -a; source .env; set +a

log "Preparing PostgreSQL databases on ${POSTGRES_HOST}"
export PGPASSWORD="$POSTGRES_PASSWORD" PGSSLMODE=require PGCONNECT_TIMEOUT=10
for i in $(seq 1 60); do
  psql -h "$POSTGRES_HOST" -U "$POSTGRES_USER" -d supplychain -c "select 1" >/dev/null 2>&1 && break
  sleep 10
done
psql -v ON_ERROR_STOP=1 -h "$POSTGRES_HOST" -U "$POSTGRES_USER" -d supplychain <<'SQL'
CREATE EXTENSION IF NOT EXISTS vector;
SELECT 'CREATE DATABASE flowise' WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'flowise')\gexec
SELECT 'CREATE DATABASE langfuse' WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'langfuse')\gexec
SQL

mkdir -p observability/targets
if [ -n "${QWEN_METRICS_TARGET:-}" ]; then
  printf '[{"targets": ["%s"], "labels": {"service": "vllm-qwen"}}]\n' "$QWEN_METRICS_TARGET" > observability/targets/vllm.json
else
  echo "[]" > observability/targets/vllm.json
fi

PROFILES=(--profile core --profile edge)
if [ "${ENABLE_OBSERVABILITY:-true}" = "true" ]; then PROFILES+=(--profile observability); fi
if [ -n "${CPU_LLM_MODEL:-}" ]; then PROFILES+=(--profile cpu-llm); fi

log "Pulling third-party images"
docker compose "${PROFILES[@]}" pull --ignore-pull-failures --quiet || true
log "Starting services: ${PROFILES[*]}"
docker compose "${PROFILES[@]}" up -d --no-build

wait_http() {  # name url attempts
  for i in $(seq 1 "$3"); do
    if docker compose exec -T api curl -fsS -o /dev/null "$2"; then log "$1 is up"; return 0; fi
    sleep 10
  done
  log "WARNING: $1 did not become ready"; return 1
}
wait_http api http://127.0.0.1:8000/health 60
wait_http flowise http://flowise:3000/api/v1/ping 60
wait_http langgraph http://langgraph:8123/ok 60

if [ -n "${CPU_LLM_MODEL:-}" ]; then
  log "Preparing ${CPU_LLM_MODEL} on CPU (Ollama) as ${QWEN_MODEL} with a 16k context"
  for i in $(seq 1 30); do docker compose exec -T ollama ollama list >/dev/null 2>&1 && break; sleep 5; done
  docker compose exec -T ollama ollama pull "${CPU_LLM_MODEL}"
  printf 'FROM %s\nPARAMETER num_ctx 16384\nPARAMETER temperature 0\n' "${CPU_LLM_MODEL}" > deploy/ollama/Modelfile.cpu
  docker compose exec -T ollama ollama create "${QWEN_MODEL}" -f /modelfiles/Modelfile.cpu
  docker compose exec -T ollama ollama run "${QWEN_MODEL}" "ready" >/dev/null 2>&1 || true  # load into memory
fi

if [ -n "${QWEN_BASE_URL:-}" ] && [ "${LLM_MODE:-qwen}" = "qwen" ]; then
  log "Waiting for Qwen (vLLM downloads the model on first boot)"
  for i in $(seq 1 90); do
    if docker compose exec -T api curl -fsS -H "Authorization: Bearer ${QWEN_API_KEY}" "${QWEN_BASE_URL}/models" >/dev/null 2>&1; then log "Qwen is serving"; break; fi
    sleep 20
  done
fi

log "Bootstrapping Flowise (account, API key, variables, Chatflow + AgentFlow V2)"
python3 flowise/bootstrap.py --env-file .env --compose-dir "$APP_DIR"
# Restart the API so its Flowise proxy picks up the generated FLOWISE_API_KEY.
docker compose "${PROFILES[@]}" up -d --no-build api

date -Is > BOOTSTRAP_COMPLETE
log "Deployment complete: https://app.${BASE_DOMAIN} (http://${PUBLIC_IP:-<public-ip>} redirects there)"
