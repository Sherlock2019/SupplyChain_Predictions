#!/usr/bin/env bash
# Deploy the APPROVED AWS plan, push the image and release bundle, wait for the VM bootstrap, then verify in the cloud.
# Run scripts/cloud-preflight.sh aws first and obtain cost approval for infra/aws/aws.tfplan.
#   scripts/deploy-aws.sh [version]
set -euo pipefail
cd "$(dirname "$0")/.."
VERSION=${1:-v1}
STAMP=$(date -u +%Y%m%dT%H%M%SZ)
mkdir -p deploy-evidence
exec > >(tee "deploy-evidence/aws-deploy-${STAMP}.log") 2>&1
log() { echo "[$(date -u +%H:%M:%S)] $*"; }

PLAN=${PLAN:-aws.tfplan}  # e.g. PLAN=cpu.tfplan for the approved CPU-only variant
[ -f "infra/aws/${PLAN}" ] || { echo "No approved plan (infra/aws/${PLAN}). Run scripts/cloud-preflight.sh aws"; exit 1; }
log "terraform apply (approved plan ${PLAN})"
terraform -chdir=infra/aws apply -input=false -no-color "${PLAN}"
terraform -chdir=infra/aws output -json > "deploy-evidence/aws-outputs-${STAMP}.json"
out() { terraform -chdir=infra/aws output -raw "$1"; }
REGION=$(grep -E '^region' infra/aws/terraform.tfvars | sed -E 's/.*"(.*)".*/\1/')
ECR=$(out ecr_repository_url); BUCKET=$(out artifact_bucket); DOMAIN=$(out base_domain); SECRET=$(out secret_id)

log "build + push ${ECR}:${VERSION}"
aws ecr get-login-password --region "$REGION" | docker login --username AWS --password-stdin "${ECR%%/*}"
docker build -t "${ECR}:${VERSION}" .
docker push "${ECR}:${VERSION}"

log "upload release bundle"
scripts/package-release.sh "$VERSION" >/dev/null
aws s3 cp "release/${VERSION}.tar.gz" "s3://${BUCKET}/releases/${VERSION}.tar.gz" --region "$REGION" --only-show-errors

log "operator credentials -> deploy-evidence/aws.env (git-ignored, 0600)"
aws secretsmanager get-secret-value --secret-id "$SECRET" --region "$REGION" --query SecretString --output text \
  | jq -r 'to_entries[] | "\(.key)=\(.value)"' > deploy-evidence/aws.env
echo "CLOUD_PROVIDER=aws" >> deploy-evidence/aws.env
chmod 600 deploy-evidence/aws.env

log "waiting for https://app.${DOMAIN}/health (VM bootstrap: Docker, RDS init, Qwen download, Flowise provisioning)"
for i in $(seq 1 120); do
  if curl -fsS --max-time 10 "https://app.${DOMAIN}/health" >/dev/null 2>&1; then log "app is serving"; break; fi
  sleep 30
done
log "waiting for the VM bootstrap to finish (Flowise flows provisioned)"
APP_ID=$(out app_instance_id)
for i in $(seq 1 80); do
  CMD=$(aws ssm send-command --region "$REGION" --instance-ids "$APP_ID" --document-name AWS-RunShellScript \
        --parameters 'commands=["test -f /opt/aurelia/BOOTSTRAP_COMPLETE && cat /opt/aurelia/BOOTSTRAP_COMPLETE"]' --query Command.CommandId --output text 2>/dev/null || true)
  sleep 8
  RES=$(aws ssm get-command-invocation --region "$REGION" --command-id "$CMD" --instance-id "$APP_ID" --query StandardOutputContent --output text 2>/dev/null || true)
  if [ -n "$RES" ] && [ "$RES" != "None" ]; then log "bootstrap complete at $RES"; break; fi
  sleep 22
done
log "cloud smoke tests"
.venv/bin/python scripts/smoke.py --env-file deploy-evidence/aws.env --base-domain "$DOMAIN" --label aws || true
terraform -chdir=infra/aws output urls
