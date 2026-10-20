locals {
  name = "${var.project_name}-${var.environment}"
  apis = [
    "compute.googleapis.com", "sqladmin.googleapis.com", "servicenetworking.googleapis.com", "secretmanager.googleapis.com",
    "artifactregistry.googleapis.com", "storage.googleapis.com", "logging.googleapis.com", "monitoring.googleapis.com",
    "iap.googleapis.com",
  ]
}

resource "google_project_service" "apis" {
  for_each           = toset(local.apis)
  service            = each.value
  disable_on_destroy = false
}

# ------------------------------------------------------------------ network
resource "google_compute_network" "this" {
  name                    = local.name
  auto_create_subnetworks = false
  depends_on              = [google_project_service.apis]
}

resource "google_compute_subnetwork" "this" {
  name                     = "${local.name}-subnet"
  network                  = google_compute_network.this.id
  ip_cidr_range            = "10.43.0.0/20"
  region                   = var.region
  private_ip_google_access = true
}

resource "google_compute_global_address" "private_services" {
  name          = "${local.name}-psa"
  purpose       = "VPC_PEERING"
  address_type  = "INTERNAL"
  prefix_length = 20
  network       = google_compute_network.this.id
}

resource "google_service_networking_connection" "private_services" {
  network                 = google_compute_network.this.id
  service                 = "servicenetworking.googleapis.com"
  reserved_peering_ranges = [google_compute_global_address.private_services.name]
}

resource "google_compute_firewall" "https" {
  name          = "${local.name}-https"
  network       = google_compute_network.this.name
  source_ranges = var.allowed_cidrs
  target_tags   = ["aurelia-app"]
  allow {
    protocol = "tcp"
    ports    = ["443"]
  }
}

resource "google_compute_firewall" "acme" {
  name          = "${local.name}-acme"
  description   = "Let's Encrypt HTTP-01; Caddy redirects everything else to HTTPS"
  network       = google_compute_network.this.name
  source_ranges = ["0.0.0.0/0"]
  target_tags   = ["aurelia-app"]
  allow {
    protocol = "tcp"
    ports    = ["80"]
  }
}

resource "google_compute_firewall" "vllm" {
  name        = "${local.name}-vllm"
  network     = google_compute_network.this.name
  source_tags = ["aurelia-app"]
  target_tags = ["aurelia-gpu"]
  allow {
    protocol = "tcp"
    ports    = ["8000"]
  }
}

resource "google_compute_firewall" "iap_ssh" {
  name          = "${local.name}-iap-ssh"
  description   = "SSH only through Identity-Aware Proxy"
  network       = google_compute_network.this.name
  source_ranges = ["35.235.240.0/20"]
  target_tags   = ["aurelia-app", "aurelia-gpu"]
  allow {
    protocol = "tcp"
    ports    = ["22"]
  }
}

resource "google_compute_address" "app" {
  name   = "${local.name}-app"
  region = var.region
}

# ------------------------------------------------------------------ secrets
resource "random_password" "token" {
  for_each = toset([
    "POSTGRES_PASSWORD", "PLANNER_API_KEY", "MANAGER_API_KEY", "FLOWISE_TOOL_KEY", "LANGGRAPH_TOOL_KEY", "MCP_TOOL_KEY",
    "MCP_CLIENT_KEY", "QWEN_API_KEY", "FLOWISE_SECRETKEY", "FLOWISE_JWT_SECRET", "FLOWISE_JWT_REFRESH_SECRET",
    "FLOWISE_SESSION_SECRET", "FLOWISE_TOKEN_HASH_SECRET", "LANGFUSE_NEXTAUTH_SECRET", "LANGFUSE_SALT",
    "CLICKHOUSE_PASSWORD", "REDIS_PASSWORD", "MINIO_PASSWORD",
  ])
  length  = 32
  special = false
}

resource "random_password" "login" {
  for_each         = toset(["FLOWISE_ADMIN_PASSWORD", "GRAFANA_ADMIN_PASSWORD", "LANGFUSE_ADMIN_PASSWORD"])
  length           = 24
  special          = true
  override_special = "!#%"
  min_upper        = 2
  min_lower        = 2
  min_numeric      = 2
  min_special      = 1
}

resource "random_id" "langfuse" {
  for_each    = toset(["public", "secret", "encryption"])
  byte_length = each.key == "encryption" ? 32 : 16
}

resource "random_id" "suffix" {
  byte_length = 3
}

resource "google_secret_manager_secret" "app" {
  secret_id = "${local.name}-app"
  replication {
    auto {}
  }
  depends_on = [google_project_service.apis]
}

resource "google_secret_manager_secret_version" "app" {
  secret = google_secret_manager_secret.app.id
  secret_data = jsonencode(merge(
    { for k, v in random_password.token : k => v.result },
    { for k, v in random_password.login : k => v.result },
    {
      LANGFUSE_PUBLIC_KEY     = "pk-lf-${random_id.langfuse["public"].hex}"
      LANGFUSE_SECRET_KEY     = "sk-lf-${random_id.langfuse["secret"].hex}"
      LANGFUSE_ENCRYPTION_KEY = random_id.langfuse["encryption"].hex
    }
  ))
}

# A plain secret for the GPU VM (Container-Optimized OS has no jq).
resource "google_secret_manager_secret" "qwen" {
  secret_id = "${local.name}-qwen-api-key"
  replication {
    auto {}
  }
  depends_on = [google_project_service.apis]
}

resource "google_secret_manager_secret_version" "qwen" {
  secret      = google_secret_manager_secret.qwen.id
  secret_data = random_password.token["QWEN_API_KEY"].result
}

# ----------------------------------------------------------- artifacts
resource "google_artifact_registry_repository" "app" {
  repository_id = local.name
  location      = var.region
  format        = "DOCKER"
  depends_on    = [google_project_service.apis]
}

resource "google_storage_bucket" "artifacts" {
  name                        = "${local.name}-artifacts-${random_id.suffix.hex}"
  location                    = var.region
  uniform_bucket_level_access = true
  public_access_prevention    = "enforced"
  force_destroy               = true
  versioning {
    enabled = true
  }
}

# ----------------------------------------------------------- Cloud SQL
resource "google_sql_database_instance" "postgres" {
  name                = "${local.name}-pg-${random_id.suffix.hex}"
  database_version    = "POSTGRES_17"
  region              = var.region
  deletion_protection = false
  settings {
    tier              = var.db_tier
    edition           = "ENTERPRISE"
    availability_type = "ZONAL"
    disk_type         = "PD_SSD"
    disk_size         = 20
    ip_configuration {
      ipv4_enabled    = false
      private_network = google_compute_network.this.id
      ssl_mode        = "ENCRYPTED_ONLY"
    }
    backup_configuration {
      enabled = true
    }
  }
  depends_on = [google_service_networking_connection.private_services]
}

resource "google_sql_database" "supplychain" {
  name     = "supplychain"
  instance = google_sql_database_instance.postgres.name
}

resource "google_sql_user" "app" {
  name     = "supplychain"
  instance = google_sql_database_instance.postgres.name
  password = random_password.token["POSTGRES_PASSWORD"].result
}

# ------------------------------------------------------------ identities
resource "google_service_account" "app" {
  account_id   = "${var.project_name}-app"
  display_name = "Aurelia SCM application VM"
}

resource "google_service_account" "gpu" {
  account_id   = "${var.project_name}-gpu"
  display_name = "Aurelia SCM Qwen GPU VM"
}

resource "google_secret_manager_secret_iam_member" "app" {
  secret_id = google_secret_manager_secret.app.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.app.email}"
}

resource "google_secret_manager_secret_iam_member" "gpu" {
  secret_id = google_secret_manager_secret.qwen.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.gpu.email}"
}

resource "google_artifact_registry_repository_iam_member" "app" {
  location   = google_artifact_registry_repository.app.location
  repository = google_artifact_registry_repository.app.name
  role       = "roles/artifactregistry.reader"
  member     = "serviceAccount:${google_service_account.app.email}"
}

resource "google_storage_bucket_iam_member" "app" {
  bucket = google_storage_bucket.artifacts.name
  role   = "roles/storage.objectViewer"
  member = "serviceAccount:${google_service_account.app.email}"
}

resource "google_project_iam_member" "logging" {
  for_each = {
    app-log = { role = "roles/logging.logWriter", sa = google_service_account.app.email }
    app-mon = { role = "roles/monitoring.metricWriter", sa = google_service_account.app.email }
    gpu-log = { role = "roles/logging.logWriter", sa = google_service_account.gpu.email }
    gpu-mon = { role = "roles/monitoring.metricWriter", sa = google_service_account.gpu.email }
  }
  project = var.project_id
  role    = each.value.role
  member  = "serviceAccount:${each.value.sa}"
}

# --------------------------------------------------------------- compute
resource "google_compute_instance" "gpu" {
  count        = var.enable_gpu ? 1 : 0
  name         = "${local.name}-gpu-qwen"
  machine_type = var.gpu_machine_type
  zone         = var.zone
  tags         = ["aurelia-gpu"]
  boot_disk {
    initialize_params {
      image = "cos-cloud/cos-stable"
      size  = var.gpu_disk_gb
      type  = "pd-balanced"
    }
  }
  network_interface {
    subnetwork = google_compute_subnetwork.this.id
    access_config {}
  }
  scheduling {
    on_host_maintenance = "TERMINATE"
    automatic_restart   = true
  }
  service_account {
    email  = google_service_account.gpu.email
    scopes = ["cloud-platform"]
  }
  shielded_instance_config {
    enable_secure_boot = true
  }
  metadata = {
    startup-script = templatefile("${path.module}/templates/gpu-startup.sh.tftpl", {
      project_id  = var.project_id
      secret_name = google_secret_manager_secret.qwen.secret_id
      vllm_image  = var.vllm_image
      vllm_model  = var.vllm_model
      served_name = var.qwen_served_name
    })
  }
  depends_on = [google_secret_manager_secret_version.qwen]
}

locals {
  base_domain   = "${replace(google_compute_address.app.address, ".", "-")}.sslip.io"
  qwen_base_url = var.enable_gpu ? "http://${google_compute_instance.gpu[0].network_interface[0].network_ip}:8000/v1" : ""
  registry      = "${var.region}-docker.pkg.dev"
  app_image     = "${local.registry}/${var.project_id}/${google_artifact_registry_repository.app.repository_id}/app:${var.release_version}"
}

resource "google_compute_instance" "app" {
  name         = "${local.name}-app"
  machine_type = var.app_machine_type
  zone         = var.zone
  tags         = ["aurelia-app"]
  boot_disk {
    initialize_params {
      image = "ubuntu-os-cloud/ubuntu-2404-lts-amd64"
      size  = var.app_disk_gb
      type  = "pd-balanced"
    }
  }
  network_interface {
    subnetwork = google_compute_subnetwork.this.id
    access_config {
      nat_ip = google_compute_address.app.address
    }
  }
  service_account {
    email  = google_service_account.app.email
    scopes = ["cloud-platform"]
  }
  shielded_instance_config {
    enable_secure_boot = true
  }
  metadata = {
    startup-script = templatefile("${path.module}/templates/app-startup.sh.tftpl", {
      project_id           = var.project_id
      bucket               = google_storage_bucket.artifacts.name
      release_version      = var.release_version
      secret_name          = google_secret_manager_secret.app.secret_id
      registry             = local.registry
      app_image            = local.app_image
      db_host              = google_sql_database_instance.postgres.private_ip_address
      db_ca_b64            = base64encode(google_sql_database_instance.postgres.server_ca_cert[0].cert)
      base_domain          = local.base_domain
      acme_email           = var.acme_email
      qwen_base_url        = local.qwen_base_url
      qwen_model           = var.qwen_served_name
      qwen_metrics_target  = var.enable_gpu ? "${google_compute_instance.gpu[0].network_interface[0].network_ip}:8000" : ""
      enable_observability = var.enable_observability
    })
  }
  depends_on = [google_secret_manager_secret_version.app, google_sql_user.app]
}

resource "google_billing_budget" "poc" {
  count           = var.billing_account != "" && var.monthly_budget_usd > 0 ? 1 : 0
  billing_account = var.billing_account
  display_name    = "${local.name}-monthly"
  budget_filter {
    projects = ["projects/${var.project_id}"]
  }
  amount {
    specified_amount {
      currency_code = "USD"
      units         = tostring(var.monthly_budget_usd)
    }
  }
  dynamic "threshold_rules" {
    for_each = [0.5, 0.8, 1.0]
    content {
      threshold_percent = threshold_rules.value
    }
  }
}
