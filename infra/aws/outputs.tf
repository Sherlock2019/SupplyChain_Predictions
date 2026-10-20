output "app_public_ip" {
  value = aws_eip.app.public_ip
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

output "ecr_repository_url" {
  value = aws_ecr_repository.app.repository_url
}

output "app_image" {
  value = local.app_image
}

output "artifact_bucket" {
  value = aws_s3_bucket.artifacts.id
}

output "secret_id" {
  value = aws_secretsmanager_secret.app.id
}

output "rds_endpoint" {
  value = aws_db_instance.postgres.address
}

output "app_instance_id" {
  value = aws_instance.app.id
}

output "gpu_instance_id" {
  value = var.enable_gpu ? aws_instance.gpu[0].id : ""
}

output "gpu_private_ip" {
  value = var.enable_gpu ? aws_instance.gpu[0].private_ip : ""
}

output "log_group" {
  value = aws_cloudwatch_log_group.app.name
}

output "ssm_shell" {
  value = "aws ssm start-session --region ${var.region} --target ${aws_instance.app.id}"
}

output "release_version" {
  value = var.release_version
}
