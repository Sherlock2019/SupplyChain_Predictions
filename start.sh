#!/usr/bin/env bash
# SPARC — one start command for your PC (WSL, Linux, macOS) and for a cloud VM (AWS EC2 or any Linux VM with a public IP).
#
#   ./start.sh                 start; picks the launcher and the options that fit this machine (see below)
#   ./start.sh status          ready? container health and the URLs
#   ./start.sh logs            follow the start-up (Ctrl-C stops following, not the app)
#   ./start.sh stop            stop (data kept)
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
    status|logs|stop) cmd=$arg ;;
    --local) where=local ;;
    --aws|--cloud) where=aws ;;
    --full) size=(--full) ;;
    --lite|--no-llm|--small-llm) size+=("$arg") ;;
    --rebuild|--open) extra+=("$arg") ;;
    -h|--help) sed -n '2,16p' "$0"; exit 0 ;;
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
