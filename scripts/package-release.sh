#!/usr/bin/env bash
# Package the VM release bundle (Compose stack, configs, Flowise provisioning). No secrets, no source build needed on VMs.
#   scripts/package-release.sh v1   -> release/v1.tar.gz
set -euo pipefail
cd "$(dirname "$0")/.."
VERSION=${1:?version}
mkdir -p release
tar --exclude='__pycache__' --exclude='flowise/generated' -czf "release/${VERSION}.tar.gz" \
  docker-compose.yml deploy observability flowise/build-flows.cjs flowise/bootstrap.py flowise/inspect-nodes.cjs scripts/smoke.py
echo "release/${VERSION}.tar.gz ($(du -h "release/${VERSION}.tar.gz" | cut -f1))"
tar -tzf "release/${VERSION}.tar.gz" | head -40
