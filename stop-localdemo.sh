#!/usr/bin/env bash
# Stop the local demo.  ./stop-localdemo.sh          keep data (fast restart)
#                       ./stop-localdemo.sh --reset  also delete all demo data volumes
set -euo pipefail
cd "$(dirname "$0")"
PROFILES="--profile core --profile localdb --profile local-llm --profile observability --profile demo-nologin"
if [ "${1:-}" = "--reset" ]; then
  docker compose $PROFILES down -v --remove-orphans
  rm -f .localdemo-profiles
  sed -i 's/^FLOWISE_API_KEY=.*/FLOWISE_API_KEY=/' .env 2>/dev/null || true
  echo "Demo stopped and data wiped. ./start-localdemo.sh recreates everything."
else
  docker compose $PROFILES stop
  echo "Demo stopped (data kept). ./start-localdemo.sh to resume."
fi
