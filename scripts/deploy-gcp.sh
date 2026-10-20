#!/usr/bin/env bash
# Deploy the APPROVED GCP plan (alternative target). Mirrors deploy-aws.sh.
#   scripts/deploy-gcp.sh [version]
set -euo pipefail
cd "$(dirname "$0")/.."
VERSION=${1:-v1}
STAMP=$(date -u +%Y%m%dT%H%M%SZ)
mkdir -p deploy-evidence
exec > >(tee "deploy-evidence/gcp-deploy-${STAMP}.log") 2>&1
log() { echo "[$(date -u +%H:%M:%S)] $*"; }

[ -f infra/gcp/gcp.tfplan ] || { echo "No approved plan (infra/gcp/gcp.tfplan). Run scripts/cloud-preflight.sh gcp <project>"; exit 1; }
terraform -chdir=infra/gcp apply -input=false -no-color gcp.tfplan
out() { terraform -chdir=infra/gcp output -raw "$1"; }
IMAGE=$(out app_image); REGISTRY=$(out registry); BUCKET=$(out artifact_bucket); DOMAIN=$(out base_domain); SECRET=$(out secret_name)
PROJECT=$(grep -E '^project_id' infra/gcp/terraform.tfvars | sed -E 's/.*"(.*)".*/\1/')

gcloud auth configure-docker "$REGISTRY" --quiet
docker build -t "$IMAGE" . && docker push "$IMAGE"
scripts/package-release.sh "$VERSION" >/dev/null
gcloud storage cp "release/${VERSION}.tar.gz" "gs://${BUCKET}/releases/${VERSION}.tar.gz"
gcloud secrets versions access latest --secret "$SECRET" --project "$PROJECT" | jq -r 'to_entries[] | "\(.key)=\(.value)"' > deploy-evidence/gcp.env
echo "CLOUD_PROVIDER=gcp" >> deploy-evidence/gcp.env
chmod 600 deploy-evidence/gcp.env
for i in $(seq 1 120); do curl -fsS --max-time 10 "https://app.${DOMAIN}/health" >/dev/null 2>&1 && break; sleep 30; done
sleep 300  # Flowise provisioning runs after the API is healthy
.venv/bin/python scripts/smoke.py --env-file deploy-evidence/gcp.env --base-domain "$DOMAIN" --label gcp || true
terraform -chdir=infra/gcp output urls
