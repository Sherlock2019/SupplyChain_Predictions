PROFILES = --profile core --profile localdb --profile local-llm --profile observability
PY = .venv/bin/python

.PHONY: install env qwen-local test lint up down flowise smoke preflight-aws plan-aws cost-aws deploy-aws preflight-gcp deploy-gcp destroy-aws release

install:            ## Python dev environment
	python3 -m venv .venv && .venv/bin/pip install -e '.[dev]'

env:                ## Generate .env with random secrets
	python3 scripts/gen-env.py

qwen-local:         ## Local Qwen via Ollama (16k context)
	ollama pull qwen2.5:7b && ollama create qwen2.5-7b-scm -f deploy/ollama/Modelfile

test:
	$(PY) -m pytest

lint:
	.venv/bin/ruff check backend tests scripts

up:                 ## Full local stack
	docker compose build api && docker compose $(PROFILES) up -d

down:
	docker compose $(PROFILES) down

flowise:            ## Provision Flowise account, API key, variables, Chatflow and AgentFlow V2
	python3 flowise/bootstrap.py --env-file .env --compose-dir . && docker compose $(PROFILES) up -d api

smoke:              ## End-to-end verification against the local stack
	$(PY) scripts/smoke.py --env-file .env

preflight-aws:      ## Quotas, offerings, terraform plan (no changes)
	scripts/cloud-preflight.sh aws us-east-1

cost-aws:           ## Live AWS list prices for the plan
	python3 scripts/aws-cost-estimate.py --region us-east-1

deploy-aws:         ## Apply the APPROVED plan, push, bootstrap, cloud smoke tests
	scripts/deploy-aws.sh v1

destroy-aws:
	terraform -chdir=infra/aws destroy

preflight-gcp:
	scripts/cloud-preflight.sh gcp $(GCP_PROJECT) us-central1 us-central1-a

deploy-gcp:
	scripts/deploy-gcp.sh v1

release:
	scripts/package-release.sh v1
