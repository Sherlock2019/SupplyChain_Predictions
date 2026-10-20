terraform {
  required_version = ">= 1.6"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
  }
  # For team use, configure an S3 backend with locking, e.g.:
  # backend "s3" { bucket = "<state-bucket>" key = "aurelia-scm/terraform.tfstate" region = "us-east-1" use_lockfile = true }
}

provider "aws" {
  region = var.region
  default_tags {
    tags = {
      Project            = var.project_name
      Environment        = var.environment
      ManagedBy          = "terraform"
      DataClassification = "synthetic-poc"
      Owner              = var.owner
    }
  }
}
