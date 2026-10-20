terraform {
  required_version = ">= 1.6"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 7.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
  }
  # backend "gcs" { bucket = "<state-bucket>" prefix = "aurelia-scm" }
}

provider "google" {
  project = var.project_id
  region  = var.region
  zone    = var.zone
  default_labels = {
    project     = var.project_name
    environment = var.environment
    managed-by  = "terraform"
    data-class  = "synthetic-poc"
  }
}
