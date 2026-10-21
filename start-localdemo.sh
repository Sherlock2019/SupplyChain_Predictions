#!/usr/bin/env bash
# SPARC — Smart Supply Chain Performer Copilot — one-command local demo.
#
#   ./start-localdemo.sh            full demo: Qwen (Ollama) + Flowise + LangGraph + MCP + Grafana + Langfuse
#   ./start-localdemo.sh --lite     no observability stack (Grafana/Langfuse), faster start, less RAM
#   ./start-localdemo.sh --no-llm   deterministic mode (no GPU/Ollama needed; agents use the rule-based fallback)
#   ./start-localdemo.sh --rebuild  rebuild the application image first
#   ./start-localdemo.sh --open     open the dashboard in the browser at the end
#   ./start-localdemo.sh --with-login  keep the normal login pages (default demo has no login anywhere)
#   ./stop-localdemo.sh [--reset]   stop (and optionally wipe all demo data)
#   Runs in the background: Ctrl-C or closing the terminal only stops the progress display, never the start-up.
#   ./start-localdemo.sh status | logs     is it ready? (URLs) · follow the start-up log
#   ./start-localdemo.sh --foreground      old behaviour: run attached to this terminal
set -euo pipefail
cd "$(dirname "$0")"
BGLOG=.localdemo.log; BGPID=.localdemo.pid
bg_running() { [ -f "$BGPID" ] && kill -0 "$(cat "$BGPID")" 2>/dev/null; }

case "${1:-}" in
  logs) [ -f "$BGLOG" ] || { echo "no start-up log yet"; exit 1; }; exec tail -n 60 -f "$BGLOG" ;;
  status)
    if bg_running; then echo "starting (pid $(cat "$BGPID")) — last lines:"; tail -n 5 "$BGLOG"
    elif grep -q 'demo is running' "$BGLOG" 2>/dev/null; then sed -n '/demo is running/,$p' "$BGLOG"
    else echo "not running — last lines of $BGLOG:"; tail -n 15 "$BGLOG" 2>/dev/null; fi
    exit 0 ;;
esac

LITE=0; NOLLM=0; REBUILD=0; OPEN=0; NOLOGIN=1; FOREGROUND=0
for arg in "$@"; do
  case "$arg" in
    --lite) LITE=1 ;; --no-llm) NOLLM=1 ;; --rebuild) REBUILD=1 ;; --open) OPEN=1 ;; --with-login) NOLOGIN=0 ;; --foreground) FOREGROUND=1 ;;
    -h|--help) sed -n '2,15p' "$0"; exit 0 ;;
    *) echo "unknown option $arg"; exit 2 ;;
  esac
done

if [ "$FOREGROUND" = 0 ]; then
  if bg_running; then echo "already starting (pid $(cat "$BGPID")) — following its log (Ctrl-C stops following only)"; exec tail -n 30 -f --pid="$(cat "$BGPID")" "$BGLOG"; fi
  # Detach the whole start-up from this terminal (own session, no stdin): SSH logout or Ctrl-C cannot interrupt it.
  nohup setsid "$0" "$@" --foreground >"$BGLOG" 2>&1 </dev/null &
  echo $! > "$BGPID"
  printf '\033[1mSPARC start-up runs in the background\033[0m (pid %s) — log: %s\n' "$(cat "$BGPID")" "$BGLOG"
  printf '  Ctrl-C only stops this progress view · later: ./start-localdemo.sh status · ./start-localdemo.sh logs · stop: ./stop-localdemo.sh\n'
  tail -n +1 -f --pid="$(cat "$BGPID")" "$BGLOG" 2>/dev/null || true
  exit 0
fi

c_ok() { printf '  \033[32m✔\033[0m %s\n' "$*"; }
c_warn() { printf '  \033[33m!\033[0m %s\n' "$*"; }
step() { printf '\n\033[1m▶ %s\033[0m\n' "$*"; }
die() { printf '  \033[31m✘ %s\033[0m\n' "$*"; exit 1; }

step "Checking prerequisites"
command -v docker >/dev/null || die "docker is required"
# A busy or stuck machine (interrupted build, out of memory) must not hang the launcher — and say which problem it is.
check() {  # check SECONDS "what failed" command...
  local secs=$1 what=$2 rc=0; shift 2
  timeout "$secs" "$@" >/dev/null 2>&1 || rc=$?
  [ "$rc" = 0 ] && return 0
  [ "$rc" = 124 ] && die "$what did not answer within ${secs}s — the machine is overloaded or Docker is stuck. Check: uptime; free -h; then sudo systemctl restart docker"
  die "$what failed (exit $rc)"
}
check 30 "docker compose (v2 plugin)" docker compose version
check 45 "the Docker daemon" docker info
MEM_GB=$(awk '/MemTotal/ {printf "%d", $2/1048576}' /proc/meminfo 2>/dev/null || echo 0)
if [ "$NOLLM" = 0 ] && [ "${MEM_GB:-0}" -gt 0 ] && [ "$MEM_GB" -lt 15 ] && [ "${QWEN_MODEL:-qwen2.5-7b-scm}" = qwen2.5-7b-scm ]; then
  c_warn "only ${MEM_GB} GB RAM: Qwen 7B + the full stack may run out of memory — use --no-llm or --lite, or QWEN_MODEL=qwen2.5-3b-scm in .env"
fi
command -v python3 >/dev/null || die "python3 is required"
command -v curl >/dev/null || die "curl is required"
c_ok "docker, compose, python3, curl"

step "Environment"
if [ ! -f .env ]; then python3 scripts/gen-env.py >/dev/null; c_ok "generated .env with random secrets"; else c_ok "using existing .env"; fi
python3 scripts/gen-env.py --add-missing | grep -v "no new settings" | sed "s/^/  /" || true  # keys introduced by newer releases
set -a; source .env; set +a

PROFILES=(--profile core --profile localdb)
if [ "$NOLLM" = 0 ] && command -v ollama >/dev/null && curl -fs http://127.0.0.1:11434/api/tags >/dev/null; then
  # QWEN_MODEL in .env picks the size: qwen2.5-7b-scm (default) or qwen2.5-3b-scm (faster on CPU-only machines).
  SCM_MODEL=${QWEN_MODEL:-qwen2.5-7b-scm}
  BASE_MODEL=$(echo "$SCM_MODEL" | sed -E 's/^(qwen[0-9.]+)-([0-9.]+b)-scm$/\1:\2/')
  if ! ollama list | grep -q "^${SCM_MODEL}"; then
    ollama list | grep -q "^${BASE_MODEL}" || { c_warn "pulling ${BASE_MODEL} (first run only)"; ollama pull "$BASE_MODEL"; }
    printf 'FROM %s\nPARAMETER num_ctx 16384\nPARAMETER temperature 0\n' "$BASE_MODEL" > .localdemo-Modelfile
    ollama create "$SCM_MODEL" -f .localdemo-Modelfile >/dev/null
  fi
  PROFILES+=(--profile local-llm)
  export LLM_MODE=qwen
  c_ok "Qwen via Ollama (${SCM_MODEL}, 16k context)"
else
  export LLM_MODE=deterministic
  c_warn "LLM disabled (deterministic mode) — no Ollama found or --no-llm given; Flowise flows need the LLM"
fi
[ "$LITE" = 0 ] && PROFILES+=(--profile observability) && c_ok "observability: Prometheus, Grafana, Langfuse" || c_warn "lite mode: observability stack skipped"
if [ "$NOLOGIN" = 1 ]; then
  # No login pages: dashboard auto sign-in, Grafana anonymous, Flowise + Langfuse behind the local auto-login proxy.
  export DEMO_AUTO_LOGIN=true GRAFANA_ANONYMOUS=true FLOWISE_HOST_PORT=3101 LANGFUSE_HOST_PORT=3103
  PROFILES+=(--profile demo-nologin)
  c_ok "no-login mode: dashboard, Flowise, Grafana and Langfuse open without a login page (local only)"
else
  export DEMO_AUTO_LOGIN=false GRAFANA_ANONYMOUS=false FLOWISE_HOST_PORT=3000 LANGFUSE_HOST_PORT=3003
  c_ok "login pages enabled"
fi
echo "${PROFILES[*]}" > .localdemo-profiles

step "Starting containers"
if [ "$REBUILD" = 1 ] || ! docker image inspect aurelia-scm-app:local >/dev/null 2>&1; then
  c_warn "building application image (first build takes a few minutes; log: .localdemo-build.log)"
  # Plain progress: BuildKit's interactive display fails with "failed to get console" when output is not a terminal
  # (fresh Docker installs, SSH sessions, CI). Older Compose versions without --progress fall back to the env variable.
  export BUILDKIT_PROGRESS=plain
  if ! { docker compose --progress plain build api >.localdemo-build.log 2>&1 || docker compose build api >>.localdemo-build.log 2>&1; }; then
    tail -n 25 .localdemo-build.log
    die "application image build failed — full log: .localdemo-build.log"
  fi
fi
docker compose "${PROFILES[@]}" up -d --no-build --remove-orphans >/dev/null 2>&1 || docker compose "${PROFILES[@]}" up -d --no-build
c_ok "containers started"

wait_for() {  # name url seconds
  local end=$((SECONDS + $3))
  until curl -fs -o /dev/null "$2"; do
    [ $SECONDS -ge $end ] && die "$1 did not become ready ($2) — see: docker compose logs $1"
    sleep 3
  done
  c_ok "$1 ready"
}
step "Waiting for services"
wait_for api http://localhost:8000/health 240
wait_for langgraph http://localhost:8123/ok 240
wait_for mcp http://localhost:8002/health 120
wait_for scinsight-api http://localhost:8100/health 240
wait_for flowise http://localhost:3000/api/v1/ping 240
[ "$LITE" = 0 ] && { wait_for grafana http://localhost:3002/api/health 180; wait_for langfuse http://localhost:3003/api/public/health 300; }

if [ "$LITE" = 0 ]; then
  # Grafana only applies GF_SECURITY_ADMIN_PASSWORD on first start; keep the admin password in sync with .env.
  docker compose exec -T grafana grafana cli --homepath /usr/share/grafana admin reset-admin-password "$GRAFANA_ADMIN_PASSWORD" >/dev/null 2>&1 \
    && c_ok "Grafana login admin / ${GRAFANA_ADMIN_PASSWORD}" || c_warn "could not sync the Grafana admin password"
fi

step "Provisioning Flowise (account, API key, variables, Chatflow + AgentFlow V2)"
python3 flowise/bootstrap.py --env-file .env --compose-dir . | sed 's/^/  /'
step "Importing SupplyChain Insight AI flows (14 tools, 7 specialist Agentflows, supervisor, Chatflow)"
python3 flowise/scinsight/deploy.py import --env-file .env | grep -v '^{' | sed 's/^/  /'
set -a; source .env; set +a
docker compose "${PROFILES[@]}" up -d --no-build api >/dev/null 2>&1
wait_for api http://localhost:8000/health 120

step "Seeding demo data (analyses + review queue)"
api() { curl -fsS -X "$1" "http://localhost:8000$2" -H "X-API-Key: $PLANNER_API_KEY" -H 'Content-Type: application/json' ${3:+-d "$3"}; }
field() { python3 -c "import sys,json;print(json.load(sys.stdin)$1)"; }
if [ "$(api GET '/api/v1/recommendations?status=pending_review' | field '.__len__()')" -lt 2 ]; then
  AN1=$(api POST /api/v1/analysis/factory-readiness '{"plant":"FR20","material":"FG-SERUM-50","quantity":6000,"need_by":"2026-10-27"}' | field '["analysis_id"]')
  api POST /api/v1/recommendations "{\"analysis_id\":\"$AN1\",\"explanation\":\"Expedite PO 4500001002 (6.72 kg RM-ACTIVE) and source 1,160 cartons from Smurfit Luxury Pack.\",\"source\":\"dashboard\"}" >/dev/null
  AN2=$(api POST /api/v1/analysis/stock-balance '{"material":"FG-PERFUME-100"}' | field '["analysis_id"]')
  api POST /api/v1/recommendations "{\"analysis_id\":\"$AN2\",\"explanation\":\"Rebalance perfume stock into Dubai ahead of the Q4 gifting promotion.\",\"source\":\"dashboard\"}" >/dev/null
  AN3=$(api POST /api/v1/analysis/supplier-risk '{"supplier":"PackGlass Europe"}' | field '["analysis_id"]')
  api POST /api/v1/recommendations "{\"analysis_id\":\"$AN3\",\"explanation\":\"Issue SCAR for rejected lot QL-260014 and evaluate Verallia Premium.\",\"source\":\"dashboard\"}" >/dev/null
  c_ok "3 recommendations waiting for the manager (readiness, balancing, supplier risk)"
else
  c_ok "review queue already has pending recommendations"
fi

step "Status"
api GET /api/v1/status | python3 -c '
import sys,json
d=json.load(sys.stdin)
for k,v in d["components"].items():
    s=v.get("status"); mark="\033[32m●\033[0m" if s=="up" else ("\033[33m●\033[0m" if s in ("disabled","not_configured") else "\033[31m●\033[0m")
    print(f"  {mark} {k:<18} {s}")'

if [ "$NOLOGIN" = 1 ]; then
  cat <<EOF

$(printf '\033[1m')SPARC · Smart Supply Chain Performer Copilot — local demo is running (no login pages)$(printf '\033[0m')

  Dashboard          http://localhost:8000          opens signed in (switch Manager / Planner in the header)
  API docs           http://localhost:8000/docs
  Flowise            http://localhost:3000          opens signed in (Chatflow + AgentFlow V2 canvases)
  SCInsight API      http://localhost:8100/docs     Swagger; user keys SCI_*_KEY in .env (docs/scinsight/README.md)
  LangSmith Studio   https://smith.langchain.com/studio/?baseUrl=http://localhost:8123   (LangSmith account required by LangChain)
  MCP server         http://localhost:8002/mcp      X-API-Key: ${MCP_CLIENT_KEY}
EOF
  [ "$LITE" = 0 ] && cat <<EOF
  Grafana            http://localhost:3002          opens without login
  Langfuse           http://localhost:3003          opens signed in
EOF
  cat <<EOF

  Demo script: docs/DEMO_GUIDE.md   ·   verify everything: .venv/bin/python scripts/smoke.py   ·   stop: ./stop-localdemo.sh
EOF
else
cat <<EOF

$(printf '\033[1m')SPARC · Smart Supply Chain Performer Copilot — local demo is running$(printf '\033[0m')

  Dashboard          http://localhost:8000          planner key : ${PLANNER_API_KEY}
                                                    manager key : ${MANAGER_API_KEY}
  API docs           http://localhost:8000/docs
  Flowise            http://localhost:3000          ${FLOWISE_ADMIN_EMAIL:-admin@aurelia.local} / ${FLOWISE_ADMIN_PASSWORD}
  SCInsight API      http://localhost:8100/docs     Swagger; user keys SCI_*_KEY in .env (docs/scinsight/README.md)
  LangSmith Studio   https://smith.langchain.com/studio/?baseUrl=http://localhost:8123
  MCP server         http://localhost:8002/mcp      X-API-Key: ${MCP_CLIENT_KEY}
EOF
if [ "$LITE" = 0 ]; then cat <<EOF
  Grafana            http://localhost:3002          admin / ${GRAFANA_ADMIN_PASSWORD}
  Langfuse           http://localhost:3003          ${LANGFUSE_ADMIN_EMAIL:-admin@aurelia.local} / ${LANGFUSE_ADMIN_PASSWORD}
EOF
fi
cat <<EOF

  Demo script: docs/DEMO_GUIDE.md   ·   verify everything: .venv/bin/python scripts/smoke.py   ·   stop: ./stop-localdemo.sh
EOF
fi

if [ "$OPEN" = 1 ]; then
  if command -v wslview >/dev/null; then wslview http://localhost:8000
  elif grep -qi microsoft /proc/version 2>/dev/null; then cmd.exe /c start http://localhost:8000 >/dev/null 2>&1 || true
  elif command -v xdg-open >/dev/null; then xdg-open http://localhost:8000 >/dev/null 2>&1 || true
  elif command -v open >/dev/null; then open http://localhost:8000; fi
fi
