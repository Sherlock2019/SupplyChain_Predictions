#!/usr/bin/env bash
# SPARC mock-up demo on AWS EC2 (or any Linux VM with a public IP): no LLM, no Grafana/Langfuse — runs on a 4 GB t3.medium.
#
#   ./start-demo.sh            start in the background, print the public URLs (dashboard opens signed in, no keys)
#   ./start-demo.sh status     ready? + URLs   ·   ./start-demo.sh logs   ·   ./start-demo.sh stop
#
# Synthetic SAP data and the deterministic calculations, recommendations and approvals all work; agent answers come from the
# rule-based fallback instead of Qwen. Requirements (Docker, swap on small machines) are installed automatically.
# Same as ./start-aws.sh --lite --no-llm.
set -euo pipefail
cd "$(dirname "$0")"
case "${1:-}" in
  status|logs|stop) exec bash ./start-aws.sh "$1" ;;
  -h|--help) sed -n '2,9p' "$0"; exit 0 ;;
esac
exec bash ./start-aws.sh --lite --no-llm "$@"
