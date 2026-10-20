variable "region" {
  description = "AWS region (must offer the GPU instance type)"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  type    = string
  default = "aurelia-scm"
}

variable "environment" {
  type    = string
  default = "poc"
}

variable "owner" {
  description = "Owner tag for cost allocation"
  type        = string
  default     = "supply-chain-copilot"
}

variable "allowed_cidrs" {
  description = "Operator CIDRs allowed to reach HTTPS (443). Use your public IP /32."
  type        = list(string)
  validation {
    condition     = length(var.allowed_cidrs) > 0 && alltrue([for c in var.allowed_cidrs : c != "0.0.0.0/0"])
    error_message = "Restrict access to explicit operator CIDRs; 0.0.0.0/0 is not allowed for the POC."
  }
}

variable "app_instance_type" {
  description = "CPU VM running FastAPI, Flowise, LangGraph, MCP, Langfuse, Grafana, Caddy"
  type        = string
  default     = "r6i.xlarge"
}

variable "app_root_volume_gb" {
  type    = number
  default = 80
}

variable "enable_gpu" {
  description = "Create the GPU VM serving Qwen with vLLM. When false the app uses LLM_MODE=deterministic."
  type        = bool
  default     = true
}

variable "cpu_llm_model" {
  description = "When enable_gpu is false: Ollama model served on CPU by the app VM (empty = deterministic mode, no LLM)."
  type        = string
  default     = "qwen2.5:3b"
}

variable "gpu_instance_type" {
  description = "NVIDIA L4 (g6.xlarge) or A10G (g5.xlarge)"
  type        = string
  default     = "g6.xlarge"
}

variable "gpu_root_volume_gb" {
  type    = number
  default = 120
}

variable "vllm_image" {
  type    = string
  default = "vllm/vllm-openai:v0.32.0"
}

variable "vllm_model" {
  description = "Hugging Face model served by vLLM"
  type        = string
  default     = "Qwen/Qwen2.5-7B-Instruct-AWQ"
}

variable "qwen_served_name" {
  type    = string
  default = "qwen2.5-7b-instruct"
}

variable "db_instance_class" {
  type    = string
  default = "db.t4g.small"
}

variable "db_allocated_storage_gb" {
  type    = number
  default = 20
}

variable "enable_observability" {
  description = "Run Prometheus, Grafana and the self-hosted Langfuse v4 stack on the app VM"
  type        = bool
  default     = true
}

variable "release_version" {
  description = "Release bundle (s3://<bucket>/releases/<version>.tar.gz) and image tag the VM deploys"
  type        = string
  default     = "v1"
}

variable "acme_email" {
  description = "Optional e-mail for Let's Encrypt expiry notices"
  type        = string
  default     = ""
}

variable "monthly_budget_usd" {
  description = "Create an AWS Budget with e-mail alerts at 50/80/100%. 0 disables."
  type        = number
  default     = 0
}

variable "budget_email" {
  type    = string
  default = ""
}

variable "log_retention_days" {
  type    = number
  default = 14
}
