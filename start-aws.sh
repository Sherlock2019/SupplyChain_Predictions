#!/usr/bin/env bash
# SPARC on an AWS EC2 instance (or any Linux VM with a public IP) — one command, runs in the background.
#
#   ./start-aws.sh                 start in the background with login pages, print the public URLs, return immediately
#   ./start-aws.sh --small-llm     Qwen2.5-3B instead of 7B (CPU-only instances answer much faster)
#   ./start-aws.sh --no-llm        no LLM: agents use the deterministic fallback; dashboards, roles and moat work fully
#   ./start-aws.sh --lite          skip Grafana and Langfuse (less RAM)
#   ./start-aws.sh --rebuild       rebuild the application image first
#   ./start-aws.sh --dashboard-login  ask for the planner / manager key (default: the dashboard opens signed in, demo)
#   ./start-aws.sh status          start-up progress, container health and the URLs with logins
#   ./start-aws.sh logs            follow the start-up log (Ctrl-C stops following, not the app)
#   ./start-aws.sh stop            stop everything (data is kept; ./stop-localdemo.sh --reset wipes it)
#
# The app keeps running after you log out of SSH, and Docker restarts it after a reboot.
# Security group: allow YOUR IP only on TCP 8000 (dashboard), 3000 (Flowise), 8100 (SCInsight API), 3002 (Grafana), 3003 (Langfuse).
set -euo pipefail
cd "$(dirname "$0")"
LOG=.aws-launch.log
PIDFILE=.aws-launch.pid

ok() { printf '  \033[32m✔\033[0m %s\n' "$*"; }
warn() { printf '  \033[33m!\033[0m %s\n' "$*"; }
die() { printf '  \033[31m✘ %s\033[0m\n' "$*"; exit 1; }
bold() { printf '\033[1m%s\033[0m\n' "$*"; }

public_ip() {  # EC2 instance metadata (IMDSv2), then a public echo service
  local token ip
  token=$(curl -fsS -m 2 -X PUT http://169.254.169.254/latest/api/token -H 'X-aws-ec2-metadata-token-ttl-seconds: 60' 2>/dev/null || true)
  ip=$(curl -fsS -m 2 -H "X-aws-ec2-metadata-token: ${token}" http://169.254.169.254/latest/meta-data/public-ipv4 2>/dev/null || true)
  [ -n "$ip" ] || ip=$(curl -fsS -m 5 https://checkip.amazonaws.com 2>/dev/null | tr -d '\n' || true)
  echo "$ip"
}

set_env() {  # set_env KEY VALUE — replace or append in .env
  python3 - "$1" "$2" <<'PY'
import pathlib, sys
key, value = sys.argv[1], sys.argv[2]
p = pathlib.Path(".env")
lines = p.read_text().splitlines()
out, done = [], False
for line in lines:
    if line.split("=", 1)[0] == key:
        out.append(f"{key}={value}"); done = True
    else:
        out.append(line)
if not done:
    out.append(f"{key}={value}")
p.write_text("\n".join(out) + "\n")
PY
}

launcher_running() { [ -f "$PIDFILE" ] && kill -0 "$(cat "$PIDFILE")" 2>/dev/null; }

print_urls() {  # print_urls IP LITE(0|1)
  local ip=$1 lite=${2:-0}
  set -a; source .env; set +a
  if [ "${DEMO_AUTO_LOGIN:-}" = true ]; then
    printf '\n  Dashboard          http://%s:8000          opens signed in, no keys (switch role in the header)\n' "$ip"
  else
    printf '\n  Dashboard          http://%s:8000          planner key : %s\n%49s manager key : %s\n' "$ip" "$PLANNER_API_KEY" "" "$MANAGER_API_KEY"
  fi
  cat <<EOF
  API docs           http://${ip}:8000/docs
  Flowise            http://${ip}:3000          ${FLOWISE_ADMIN_EMAIL:-admin@admin.com} / ${FLOWISE_ADMIN_PASSWORD}
                                                 SCInsight flows: SCInsight-Cosmetics-* (chat bot, SC Agent Manager, 7 specialists)
  SCInsight API      http://${ip}:8100/docs     Swagger; user keys SCI_*_KEY in .env (e.g. SCI_WAREHOUSE_KEY approves transfers)
  LangGraph API      http://${ip}:8123          (LangSmith Studio: https://smith.langchain.com/studio/?baseUrl=http://${ip}:8123)
                                                 SCInsight mirror: scinsight_chat, scinsight_supervisor, scinsight_<specialist>
  MCP server         http://${ip}:8002/mcp      X-API-Key: ${MCP_CLIENT_KEY}
EOF
  if [ "$lite" = 0 ]; then cat <<EOF
  Grafana            http://${ip}:3002          admin / ${GRAFANA_ADMIN_PASSWORD}
  Langfuse           http://${ip}:3003          ${LANGFUSE_ADMIN_EMAIL:-admin@admin.com} / ${LANGFUSE_ADMIN_PASSWORD}
EOF
  fi
  cat <<EOF

  Security group: allow your IP only on TCP 8000, 3000, 8100, 3002, 3003 (and 8123/8002 if you use Studio or MCP).
  Studio note: Studio runs in your browser and calls http://${ip}:8123 directly — open 8123 to your IP to use it.
EOF
}

status() {
  local ip; ip=$(public_ip)
  bold "SPARC on ${ip:-<no public IP>}"
  if launcher_running; then
    warn "still starting (pid $(cat "$PIDFILE")) — follow with: ./start-aws.sh logs"
    tail -n 4 "$LOG" 2>/dev/null | sed 's/^/    /'
  elif grep -q 'demo is running' "$LOG" 2>/dev/null; then ok "start-up finished"
  elif [ -f "$LOG" ]; then warn "start-up did not finish — last lines of $LOG:"; tail -n 15 "$LOG" | sed 's/^/    /'
  fi
  echo
  for svc in "dashboard/API|http://localhost:8000/health" "SCInsight API|http://localhost:8100/health" "LangGraph|http://localhost:8123/ok" "MCP|http://localhost:8002/health" \
             "Flowise|http://localhost:3000/api/v1/ping" "Grafana|http://localhost:3002/api/health" "Langfuse|http://localhost:3003/api/public/health"; do
    name=${svc%%|*}; url=${svc#*|}
    if curl -fs -m 3 -o /dev/null "$url"; then ok "$name"; else warn "$name not answering yet"; fi
  done
  local lite=1; grep -q observability .localdemo-profiles 2>/dev/null && lite=0
  if [ -n "$ip" ] && [ -f .env ]; then print_urls "$ip" "$lite"; fi
}

case "${1:-}" in
  status) status; exit 0 ;;
  logs) [ -f "$LOG" ] || die "no start-up log yet — run ./start-aws.sh"; exec tail -n 50 -f "$LOG" ;;
  stop) launcher_running && kill "$(cat "$PIDFILE")" 2>/dev/null || true; rm -f "$PIDFILE"; exec bash ./stop-localdemo.sh ;;
  -h|--help) sed -n '2,15p' "$0"; exit 0 ;;
esac

PASS=(--with-login --open-dashboard); SMALL=0
for arg in "$@"; do
  case "$arg" in
    --small-llm) SMALL=1 ;;
    --dashboard-login) PASS=("${PASS[@]/--open-dashboard}") ;;
    --no-llm|--lite|--rebuild) PASS+=("$arg") ;;
    *) die "unknown option $arg (see ./start-aws.sh --help)" ;;
  esac
done

bold "SPARC · AWS launcher"
if launcher_running; then warn "already starting (pid $(cat "$PIDFILE"))"; status; exit 0; fi
# Check the requirements and install what is missing (Docker + compose, python3, curl, git, Ollama), then start Docker on boot.
rc=0; if [[ " ${PASS[*]} " == *" --no-llm "* ]]; then bash scripts/ensure-prereqs.sh --no-llm || rc=$?; else bash scripts/ensure-prereqs.sh || rc=$?; fi
if [ "$rc" = 3 ]; then  # just added to the docker group: continue in a shell that has it (no log-out needed)
  command -v sg >/dev/null || die "log out and back in (docker group), then re-run ./start-aws.sh"
  exec sg docker -c "$(printf '%q ' bash "$0" "$@")"
fi
[ "$rc" = 0 ] || exit "$rc"
command -v ollama >/dev/null || [[ " ${PASS[*]} " == *" --no-llm "* ]] || warn "no Ollama — starting without an LLM (deterministic fallback)"

IP=$(public_ip)
[ -n "$IP" ] || die "could not find this instance's public IP (is a public IPv4 / Elastic IP attached?)"
ok "public IP ${IP}"
[ -f .env ] || { python3 scripts/gen-env.py >/dev/null; ok "generated .env with random secrets"; }
# Every tool must know its public address, or logins and links redirect to localhost.
for kv in "PUBLIC_IP=${IP}" "PUBLIC_BASE_URL=http://${IP}:8000" "PUBLIC_FLOWISE_URL=http://${IP}:3000" "PUBLIC_LANGGRAPH_URL=http://${IP}:8123" \
          "PUBLIC_MCP_URL=http://${IP}:8002" "PUBLIC_GRAFANA_URL=http://${IP}:3002" "PUBLIC_LANGFUSE_URL=http://${IP}:3003"; do
  set_env "${kv%%=*}" "${kv#*=}"
done
if [[ " ${PASS[*]} " == *" --open-dashboard "* ]]; then set_env DEMO_AUTO_LOGIN true; else set_env DEMO_AUTO_LOGIN false; fi  # read by print_urls
if [ "$SMALL" = 1 ]; then set_env QWEN_MODEL qwen2.5-3b-scm; ok "Qwen2.5-3B (CPU-friendly)"; fi
ok "public URLs written to .env"

# Run the full start-up detached from this terminal: closing SSH does not stop it.
nohup setsid bash ./start-localdemo.sh --foreground "${PASS[@]}" >"$LOG" 2>&1 </dev/null &
echo $! > "$PIDFILE"
ok "starting in the background (pid $(cat "$PIDFILE")) — first start 10–20 min, later starts 2–3 min"
cat <<EOF

  Progress     ./start-aws.sh logs      (Ctrl-C stops following, not the app)
  Ready?       ./start-aws.sh status
  Stop         ./start-aws.sh stop
EOF
LITE=0; [[ " ${PASS[*]} " == *" --lite "* ]] && LITE=1
print_urls "$IP" "$LITE"
