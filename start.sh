#!/usr/bin/env bash
# SPARC — one start command for your PC (WSL, Linux, macOS) and for a cloud VM (AWS EC2 or any Linux VM with a public IP).
#
#   ./start.sh                 start; picks the launcher and the options that fit this machine (see below)
#   ./start.sh status          ready? container health and the URLs
#   ./start.sh logs            follow the start-up (Ctrl-C stops following, not the app)
#   ./start.sh stop            stop (data kept)
#   ./start.sh doctor          why is it not up? health, containers, image, logs, out-of-memory kills (paste the output)
#
# Overrides:  --local | --aws               force where it runs (default: detected)
#             --full | --lite | --no-llm | --small-llm (aws only)   force the size (default: from RAM)
#             --rebuild                     rebuild the application image first (automatic after a git pull anyway)
#
# Automatic size:  under 8 GB RAM -> --lite --no-llm (dashboards, calculations, ERP setup; no Flowise chat answers)
#                  8-15 GB       -> --lite (Qwen; on a cloud VM the faster 3B model)
#                  16 GB or more -> everything (Qwen 7B, Flowise, LangGraph, MCP, Grafana, Langfuse)
set -euo pipefail
cd "$(dirname "$0")"

where="" ; size=() ; extra=() ; cmd=""
for arg in "$@"; do
  case "$arg" in
    status|logs|stop|doctor) cmd=$arg ;;
    --local) where=local ;;
    --aws|--cloud) where=aws ;;
    --full) size=(--full) ;;
    --lite|--no-llm|--small-llm) size+=("$arg") ;;
    --rebuild|--open) extra+=("$arg") ;;
    -h|--help) sed -n '2,17p' "$0"; exit 0 ;;
    *) echo "unknown option $arg (see ./start.sh --help)"; exit 1 ;;
  esac
done

# Where am I?  WSL / macOS / no cloud metadata = your PC; cloud metadata (AWS, GCP, Azure) = a VM with a public IP.
if [ -z "$where" ]; then
  if grep -qi microsoft /proc/version 2>/dev/null || [ "$(uname)" = Darwin ]; then where=local
  elif curl -fs -m 2 -X PUT http://169.254.169.254/latest/api/token -H 'X-aws-ec2-metadata-token-ttl-seconds: 10' >/dev/null 2>&1 \
       || curl -fs -m 2 -H 'Metadata-Flavor: Google' http://169.254.169.254/computeMetadata/v1/ >/dev/null 2>&1 \
       || grep -qi -E 'amazon|google|microsoft corporation' /sys/class/dmi/id/sys_vendor 2>/dev/null; then where=aws
  else where=local
  fi
fi
launcher=./start-localdemo.sh; [ "$where" = aws ] && launcher=./start-aws.sh

if [ "$cmd" = doctor ]; then  # everything needed to see why the app is not up, in one paste (no secrets)
  h() { printf '\n=== %s\n' "$*"; }
  h "where: $where · $(git log --oneline -1 2>/dev/null)"; free -h | head -2
  h "served dashboard: new version (ERP / SAP Setup)?"; curl -s -m 5 localhost:8000/ | grep -c page-erp || echo "0 (old version or not answering)"
  for u in localhost:8000/health localhost:8000/scinsight/health localhost:8123/ok localhost:3000/api/v1/ping; do
    printf '%-32s %s\n' "$u" "$(curl -s -m 5 -o /dev/null -w '%{http_code}' "http://$u" || true)"; done
  h "containers"; docker compose ps -a --format 'table {{.Service}}\t{{.Status}}\t{{.Image}}' 2>&1 | head -20
  h "app image"; docker image inspect -f 'built {{.Created}} · source {{ index .Config.Labels "scm.source-hash" }}' aurelia-scm-app:local 2>&1
  h "launcher log (last 15)"; tail -n 15 .aws-launch.log .localdemo.log 2>/dev/null | grep -v -i -E 'key|password|secret'
  h "build log (last 10)"; tail -n 10 .localdemo-build.log 2>/dev/null
  h "api log (last 25)"; docker compose logs --tail 25 api 2>&1 | grep -v -i -E 'api[_-]?key=|password|secret' | cut -c1-220
  h "out of memory kills"; (sudo -n dmesg 2>/dev/null || dmesg 2>/dev/null) | grep -i -E 'killed process|out of memory' | tail -3 || true
  exit 0
fi
if [ -n "$cmd" ]; then
  [ "$cmd" = stop ] && [ "$where" = local ] && exec bash ./stop-localdemo.sh
  exec bash "$launcher" "$cmd"
fi

# How big a stack fits?
if [ "${#size[@]}" = 0 ]; then
  if [ "$(uname)" = Darwin ]; then mem=$(( $(sysctl -n hw.memsize) / 1073741824 )); else mem=$(awk '/MemTotal/ {printf "%.0f", $2/1048576}' /proc/meminfo); fi
  if [ "$mem" -lt 8 ]; then size=(--lite --no-llm)
  elif [ "$mem" -lt 16 ]; then size=(--lite); [ "$where" = aws ] && size+=(--small-llm)
  else size=()
  fi
  echo "SPARC: ${where} machine, ${mem} GB RAM -> ${size[*]:-full stack}"
else
  [ "${size[0]}" = --full ] && size=()
fi
[ "$where" = local ] && [ "${#size[@]}" -gt 0 ] && size=("${size[@]/--small-llm}")  # the 3B model switch exists on the cloud launcher only
[ "$where" = aws ] && [ "${#extra[@]}" -gt 0 ] && extra=("${extra[@]/--open}")

# The SCInsight API is a router of the one FastAPI app now: remove the old separate container if an earlier version left it running.
if command -v docker >/dev/null && docker ps -aq --filter name=scinsight-api 2>/dev/null | grep -q .; then
  echo "SPARC: removing the old separate SCInsight API container (now served by the api service at /scinsight)"
  docker rm -f $(docker ps -aq --filter name=scinsight-api) >/dev/null
fi

args=()
for a in ${size[@]+"${size[@]}"} ${extra[@]+"${extra[@]}"}; do [ -n "$a" ] && args+=("$a"); done
exec bash "$launcher" ${args[@]+"${args[@]}"}
