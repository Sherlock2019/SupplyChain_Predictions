output "app_public_ip" {
  value = google_compute_address.app.address
}

output "base_domain" {
  value = local.base_domain
}

output "urls" {
  value = {
    dashboard        = "https://app.${local.base_domain}"
    api_docs         = "https://app.${local.base_domain}/docs"
    flowise          = "https://flowise.${local.base_domain}"
    langgraph_api    = "https://studio.${local.base_domain}"
    langsmith_studio = "https://smith.langchain.com/studio/?baseUrl=https://studio.${local.base_domain}"
    mcp              = "https://mcp.${local.base_domain}/mcp"
    grafana          = var.enable_observability ? "https://grafana.${local.base_domain}" : ""
    langfuse         = var.enable_observability ? "https://langfuse.${local.base_domain}" : ""
  }
}

output "app_image" {
  value = local.app_image
}

output "registry" {
  value = local.registry
}

output "artifact_bucket" {
  value = google_storage_bucket.artifacts.name
}

output "secret_name" {
  value = google_secret_manager_secret.app.secret_id
}

output "cloudsql_private_ip" {
  value = google_sql_database_instance.postgres.private_ip_address
}

output "ssh" {
  value = "gcloud compute ssh ${google_compute_instance.app.name} --zone ${var.zone} --tunnel-through-iap"
}

output "release_version" {
  value = var.release_version
}
