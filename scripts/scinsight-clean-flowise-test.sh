#!/usr/bin/env bash
# Definition-of-done check for the SCInsight Flowise exports: start a brand-new, EMPTY Flowise (same image as the stack,
# its own SQLite volume, port 3010), import ONLY the committed export files with flowise/scinsight/deploy.py, then execute
# the flows there with the end-to-end tests. Nothing is copied from the running Flowise instance.
#
#   bash scripts/scinsight-clean-flowise-test.sh          # create, import, test (the container stays up for inspection)
#   bash scripts/scinsight-clean-flowise-test.sh --down   # remove the clean container and its volume
set -euo pipefail
cd "$(dirname "$0")/.."
NAME=scinsight-flowise-clean
VOLUME=scinsight-flowise-clean-data
STATE=deploy-evidence/scinsight-clean-flowise.json

if [ "${1:-}" = "--down" ]; then
  docker rm -f "$NAME" >/dev/null 2>&1 || true
  docker volume rm "$VOLUME" >/dev/null 2>&1 || true
  rm -f "$STATE"
  echo "removed $NAME"
  exit 0
fi

FLOWISE=$(docker compose ps -q flowise)
[ -n "$FLOWISE" ] || { echo "the stack's flowise service is not running (needed for its image and network)"; exit 1; }
IMAGE=$(docker inspect "$FLOWISE" --format '{{.Config.Image}}')
NETWORK=$(docker inspect "$FLOWISE" --format '{{range $name, $_ := .NetworkSettings.Networks}}{{$name}} {{end}}' | awk '{print $1}')
# Same SSRF policy as the stack: HTTP_SECURITY_CHECK=false replaces Flowise's built-in deny list (which blocks every private
# range, including the Docker bridge where scinsight-api lives) with HTTP_DENY_LIST (loopback, metadata, 10/8, 192.168/16 ... stay denied).
DENY=$(docker inspect "$FLOWISE" --format '{{range .Config.Env}}{{println .}}{{end}}' | sed -n 's/^HTTP_DENY_LIST=//p')
CHECK=$(docker inspect "$FLOWISE" --format '{{range .Config.Env}}{{println .}}{{end}}' | sed -n 's/^HTTP_SECURITY_CHECK=//p')
rnd() { python3 -c "import secrets; print(secrets.token_urlsafe(32))"; }

docker rm -f "$NAME" >/dev/null 2>&1 || true
docker volume rm "$VOLUME" >/dev/null 2>&1 || true
echo "starting a clean Flowise ($IMAGE) on network $NETWORK, http://127.0.0.1:3010 (SQLite, empty)"
docker run -d --name "$NAME" --network "$NETWORK" -p 127.0.0.1:3010:3000 \
  --add-host host.docker.internal:host-gateway \
  -e PORT=3000 -e DISABLE_FLOWISE_TELEMETRY=true -e SECRETKEY_STORAGE_TYPE=local -e FLOWISE_SECRETKEY_OVERWRITE="$(rnd)" \
  -e JWT_AUTH_TOKEN_SECRET="$(rnd)" -e JWT_REFRESH_TOKEN_SECRET="$(rnd)" -e EXPRESS_SESSION_SECRET="$(rnd)" -e TOKEN_HASH_SECRET="$(rnd)" \
  -e APP_URL=http://localhost:3010 -e SECURE_COOKIES=false -e HTTP_SECURITY_CHECK="${CHECK:-true}" -e HTTP_DENY_LIST="$DENY" \
  -v "$VOLUME":/root/.flowise "$IMAGE" >/dev/null
for _ in $(seq 1 60); do curl -fsS http://127.0.0.1:3010/api/v1/ping >/dev/null 2>&1 && break; sleep 3; done
curl -fsS http://127.0.0.1:3010/api/v1/ping >/dev/null || { docker logs --tail 40 "$NAME"; exit 1; }

mkdir -p deploy-evidence
python3 flowise/scinsight/deploy.py import --flowise-url http://127.0.0.1:3010 --flowise-internal-url "http://$NAME:3000" --state-file "$STATE"
echo "executing the imported flows in the clean instance"
SCI_E2E_STATE="$STATE" .venv/bin/python -m pytest tests/scinsight/test_flowise_e2e.py -p no:cacheprovider -o addopts="" -q -W ignore::UserWarning -rA
