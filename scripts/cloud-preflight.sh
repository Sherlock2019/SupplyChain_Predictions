#!/usr/bin/env bash
# Cloud preflight + Terraform plan. Never applies anything.
#   scripts/cloud-preflight.sh aws   [region]
#   scripts/cloud-preflight.sh gcp   <project-id> [region] [zone]
set -uo pipefail
cd "$(dirname "$0")/.."
CLOUD=${1:?usage: cloud-preflight.sh aws|gcp ...}
STAMP=$(date -u +%Y%m%dT%H%M%SZ)
mkdir -p deploy-evidence
REPORT=deploy-evidence/${CLOUD}-preflight-${STAMP}.log
exec > >(tee "$REPORT") 2>&1
ok() { echo "  [ok]   $*"; }
bad() { echo "  [FAIL] $*"; FAILED=1; }
warn() { echo "  [warn] $*"; }
FAILED=0

echo "== Local toolchain"
command -v terraform >/dev/null && ok "$(terraform version | head -1)" || bad "terraform missing"
command -v docker >/dev/null && ok "$(docker --version)" || bad "docker missing"
OPERATOR_IP=$(curl -fsS https://checkip.amazonaws.com | tr -d '[:space:]')
[ -n "$OPERATOR_IP" ] && ok "operator public IP ${OPERATOR_IP} -> allowed_cidrs [\"${OPERATOR_IP}/32\"]" || bad "cannot detect operator IP"

if [ "$CLOUD" = "aws" ]; then
  REGION=${2:-us-east-1}
  echo "== AWS identity and region ${REGION}"
  if aws sts get-caller-identity --output json > /tmp/aws-id.json 2>/dev/null; then
    ok "account $(jq -r .Account /tmp/aws-id.json) as $(jq -r .Arn /tmp/aws-id.json)"
  else bad "aws credentials not configured"; fi
  for TYPE in r6i.xlarge g6.xlarge; do
    AZS=$(aws ec2 describe-instance-type-offerings --region "$REGION" --location-type availability-zone --filters Name=instance-type,Values=$TYPE --query 'InstanceTypeOfferings[].Location' --output text 2>/dev/null)
    [ -n "$AZS" ] && ok "$TYPE offered in: $AZS" || bad "$TYPE not offered in $REGION"
  done
  echo "== Service quotas (vCPU)"
  G=$(aws service-quotas get-service-quota --region "$REGION" --service-code ec2 --quota-code L-DB2E81BA --query Quota.Value --output text 2>/dev/null)
  S=$(aws service-quotas get-service-quota --region "$REGION" --service-code ec2 --quota-code L-1216C47A --query Quota.Value --output text 2>/dev/null)
  [ "${G%.*}" -ge 4 ] 2>/dev/null && ok "Running On-Demand G and VT vCPU quota: $G (g6.xlarge needs 4)" || bad "G/VT vCPU quota is ${G:-unknown}; request >= 4 (quota L-DB2E81BA)"
  [ "${S%.*}" -ge 8 ] 2>/dev/null && ok "Running On-Demand Standard vCPU quota: $S (r6i.xlarge needs 4)" || warn "Standard vCPU quota ${S:-unknown}"
  USED=$(aws ec2 describe-instances --region "$REGION" --filters Name=instance-state-name,Values=running,pending --query 'Reservations[].Instances[].InstanceType' --output text 2>/dev/null | wc -w)
  ok "currently running instances in region: $USED"
  aws ec2 describe-addresses --region "$REGION" --query 'length(Addresses)' --output text >/dev/null 2>&1 && ok "Elastic IP API reachable ($(aws ec2 describe-addresses --region "$REGION" --query 'length(Addresses)' --output text) allocated)"
  RDS=$(aws rds describe-db-engine-versions --region "$REGION" --engine postgres --engine-version 17 --default-only --query 'DBEngineVersions[0].EngineVersion' --output text 2>/dev/null)
  [ -n "$RDS" ] && ok "RDS PostgreSQL default 17.x: $RDS (pgvector supported)" || warn "could not query RDS versions"
  AMI=$(aws ec2 describe-images --region "$REGION" --owners amazon --filters "Name=name,Values=Deep Learning Base OSS Nvidia Driver GPU AMI (Ubuntu 24.04)*" --query 'sort_by(Images,&CreationDate)[-1].Name' --output text 2>/dev/null)
  [ -n "$AMI" ] && [ "$AMI" != "None" ] && ok "GPU AMI: $AMI" || bad "Deep Learning Base GPU AMI not found"
  TFVARS=infra/aws/terraform.tfvars
  if [ ! -f "$TFVARS" ]; then
    sed -e "s#\"203.0.113.10/32\"#\"${OPERATOR_IP}/32\"#" -e "s#us-east-1#${REGION}#" infra/aws/terraform.tfvars.example > "$TFVARS"
    ok "wrote $TFVARS"
  else
    ok "using existing $TFVARS"
  fi
  echo "== Terraform init / validate / plan"
  (cd infra/aws && terraform init -input=false -no-color >/dev/null && terraform validate -no-color && terraform plan -input=false -no-color -out=aws.tfplan | tail -60) || bad "terraform plan failed"
  [ -f infra/aws/aws.tfplan ] && (cd infra/aws && terraform show -json aws.tfplan > ../../deploy-evidence/aws-plan-${STAMP}.json) && ok "plan saved: infra/aws/aws.tfplan"
else
  PROJECT=${2:-}
  REGION=${3:-us-central1}
  ZONE=${4:-us-central1-a}
  echo "== GCP identity, project ${PROJECT:-<unset>}, ${REGION}/${ZONE}"
  ACCOUNT=$(gcloud auth list --filter=status:ACTIVE --format='value(account)' 2>/dev/null)
  [ -n "$ACCOUNT" ] && ok "gcloud account $ACCOUNT" || bad "gcloud is not authenticated (run: gcloud auth login && gcloud auth application-default login)"
  [ -n "$PROJECT" ] && ok "project $PROJECT" || bad "project id argument missing"
  if [ -n "$ACCOUNT" ] && [ -n "$PROJECT" ]; then
    gcloud billing projects describe "$PROJECT" --format='value(billingEnabled)' 2>/dev/null | grep -qi true && ok "billing enabled" || bad "billing not enabled on $PROJECT"
    gcloud compute machine-types describe g2-standard-4 --zone "$ZONE" --project "$PROJECT" >/dev/null 2>&1 && ok "g2-standard-4 (L4) available in $ZONE" || bad "g2-standard-4 not available in $ZONE"
    L4=$(gcloud compute regions describe "$REGION" --project "$PROJECT" --format=json 2>/dev/null | jq -r '.quotas[] | select(.metric=="NVIDIA_L4_GPUS") | .limit')
    [ "${L4%.*}" -ge 1 ] 2>/dev/null && ok "NVIDIA_L4_GPUS quota $L4" || bad "NVIDIA_L4_GPUS quota ${L4:-0}; request >= 1"
    TFVARS=infra/gcp/terraform.tfvars
    [ -f "$TFVARS" ] || sed -e "s#\"203.0.113.10/32\"#\"${OPERATOR_IP}/32\"#" -e "s#my-gcp-project#${PROJECT}#" -e "s#us-central1-a#${ZONE}#" -e "s#\"us-central1\"#\"${REGION}\"#" infra/gcp/terraform.tfvars.example > "$TFVARS"
    echo "== Terraform init / validate / plan"
    (cd infra/gcp && terraform init -input=false -no-color >/dev/null && terraform validate -no-color && terraform plan -input=false -no-color -out=gcp.tfplan | tail -60) || bad "terraform plan failed"
  else
    echo "== Terraform init / validate (plan needs authenticated gcloud)"
    (cd infra/gcp && terraform init -input=false -backend=false -no-color >/dev/null && terraform validate -no-color) || bad "terraform validate failed"
  fi
fi
echo
[ "$FAILED" = 0 ] && echo "PREFLIGHT PASSED — report: $REPORT" || echo "PREFLIGHT HAS FAILURES — report: $REPORT"
exit $FAILED
