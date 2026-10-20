variable "project_id" {
  description = "GCP project with billing enabled"
  type        = string
}

variable "region" {
  type    = string
  default = "us-central1"
}

variable "zone" {
  description = "Zone offering NVIDIA L4 (g2-standard-*)"
  type        = string
  default     = "us-central1-a"
}

variable "project_name" {
  type    = string
  default = "aurelia-scm"
}

variable "environment" {
  type    = string
  default = "poc"
}

variable "allowed_cidrs" {
  description = "Operator CIDRs allowed to reach HTTPS (443)"
  type        = list(string)
  validation {
    condition     = length(var.allowed_cidrs) > 0 && alltrue([for c in var.allowed_cidrs : c != "0.0.0.0/0"])
    error_message = "Restrict access to explicit operator CIDRs."
  }
}

variable "app_machine_type" {
  type    = string
  default = "e2-highmem-4"
}

variable "app_disk_gb" {
  type    = number
  default = 80
}

variable "enable_gpu" {
  type    = bool
  default = true
}

variable "gpu_machine_type" {
  description = "g2-standard-4 = 1x NVIDIA L4"
  type        = string
  default     = "g2-standard-4"
}

variable "gpu_disk_gb" {
  type    = number
  default = 120
}

variable "vllm_image" {
  type    = string
  default = "vllm/vllm-openai:v0.32.0"
}

variable "vllm_model" {
  type    = string
  default = "Qwen/Qwen2.5-7B-Instruct-AWQ"
}

variable "qwen_served_name" {
  type    = string
  default = "qwen2.5-7b-instruct"
}

variable "db_tier" {
  type    = string
  default = "db-custom-1-3840"
}

variable "enable_observability" {
  type    = bool
  default = true
}

variable "release_version" {
  type    = string
  default = "v1"
}

variable "acme_email" {
  type    = string
  default = ""
}

variable "billing_account" {
  description = "Billing account id for an optional budget (leave empty to skip)"
  type        = string
  default     = ""
}

variable "monthly_budget_usd" {
  type    = number
  default = 0
}
