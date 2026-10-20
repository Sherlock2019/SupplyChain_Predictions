# Cloud cost estimate and approval gate

Prices below were retrieved on **2026-10-20** from the **AWS Price List API** (`scripts/aws-cost-estimate.py`, on-demand, Linux, us-east-1).
GCP figures are public list prices for us-central1 and must be re-checked in the GCP pricing calculator before approval
(the GCP Billing Catalog API was not queried because no GCP credentials were available). Taxes and data transfer are excluded.

## AWS (primary) — what `infra/aws` creates

| Resource | Spec | Unit price | Notes |
| --- | --- | --- | --- |
| App VM | r6i.xlarge (4 vCPU, 32 GiB) | $0.252 / h | FastAPI, MCP, LangGraph Server, Flowise, Langfuse v4 stack, Prometheus, Grafana, Caddy |
| GPU VM | g6.xlarge (1× NVIDIA L4 24 GB, 4 vCPU, 16 GiB) | $0.8048 / h | vLLM serving Qwen2.5-7B-Instruct |
| RDS PostgreSQL 17 | db.t4g.small, single-AZ, 20 GB gp3 | $0.032 / h + $0.115 / GB-mo | pgvector; databases supplychain, flowise, langfuse |
| EBS gp3 | 80 GB (app) + 120 GB (GPU) | $0.08 / GB-mo | encrypted |
| Public IPv4 | Elastic IP (app) + GPU instance IP | $0.005 / h each | |
| Secrets Manager | 1 secret | $0.40 / mo | |
| S3, ECR, CloudWatch Logs | release bundle, ~2.3 GB image, 14-day logs | ≈ $1–3 / mo | |

| Usage pattern | Estimate (USD) |
| --- | --- |
| **Per running hour (everything on)** | **$1.10** |
| One 8-hour demo day | ≈ $9.40 |
| One full 24-hour day | ≈ $27 |
| Workshop month (8 h × 22 days = 176 h) | ≈ $212 |
| Always-on month (730 h) | ≈ $821 |
| VMs stopped (RDS, IPs, disks still billed) | ≈ $49 / month |
| `terraform destroy` | $0 |

Recommended: deploy, verify, demo, then stop the GPU VM (or destroy) the same day. Set `monthly_budget_usd` + `budget_email`
in `terraform.tfvars` to get AWS Budget alerts at 50/80/100 %.

## AWS CPU-only variant (no GPU quota needed) — `enable_gpu=false`

Used because the account's G-family GPU quota is 0 vCPU (request closed without an increase). Qwen2.5-3B runs on CPU
through Ollama inside the app VM; everything else is identical. AWS Price List API, 2026-10-20, us-east-1:

| Resource | Spec | Unit price |
| --- | --- | --- |
| App VM | r6i.2xlarge (8 vCPU, 64 GiB) — app stack + Ollama Qwen2.5-3B on CPU | $0.504 / h |
| RDS PostgreSQL 17 | db.t4g.small, 20 GB gp3 | $0.032 / h + $0.115 / GB-mo |
| Public IPv4 | Elastic IP (app) | $0.005 / h |
| EBS gp3, Secrets Manager | 80 GB, 1 secret | $0.08 / GB-mo, $0.40 / mo |

| Usage pattern | Estimate (USD) |
| --- | --- |
| **Per running hour** | **$0.54** |
| One 8-hour demo day | ≈ $4.63 |
| One full 24-hour day | ≈ $13.29 |
| Always-on month (730 h) | ≈ $404 |
| VMs stopped | ≈ $36 / month |

```bash
terraform -chdir=infra/aws plan -out=cpu.tfplan -var enable_gpu=false -var app_instance_type=r6i.2xlarge -var cpu_llm_model=qwen2.5:3b
PLAN=cpu.tfplan scripts/deploy-aws.sh v1
python3 scripts/aws-cost-estimate.py --app r6i.2xlarge --gpu none
```

Trade-off: AI agent answers are slower and less precise than Qwen2.5-7B on an L4; all dashboards, roles, the moat, approvals
and the deterministic analytics are unaffected. Approved by the user on 2026-10-20 (65 resources).

## GCP (alternative) — what `infra/gcp` creates (list prices, verify before approval)

| Resource | Spec | Approx. list price |
| --- | --- | --- |
| App VM | e2-highmem-4 (4 vCPU, 32 GB) | ≈ $0.18 / h |
| GPU VM | g2-standard-4 (1× NVIDIA L4) | ≈ $0.71 / h |
| Cloud SQL PostgreSQL 17 | db-custom-1-3840, 20 GB SSD | ≈ $0.07 / h |
| Disks, static IP, Secret Manager, GCS, Artifact Registry | | ≈ $25 / mo |

≈ **$1.00 per running hour**, ≈ $24 per 24-hour day, ≈ $720 always-on month.

## Approval record (fill before `terraform apply`)

- Provider / region: ______  Plan file: `infra/aws/aws.tfplan` (67 resources)
- GPU quota confirmed (AWS "Running On-Demand G and VT instances" ≥ 4 vCPU): ______
- Expected powered-on hours: ______  Budget cap / alert e-mail: ______
- Approver and timestamp: ______  Teardown date: ______
