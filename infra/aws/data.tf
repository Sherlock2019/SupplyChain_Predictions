# ------------------------------------------------------------------ secrets
# Same keys as scripts/gen-env.py; the VM bootstrap turns this JSON into the Compose .env.
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

locals {
  app_secrets = merge(
    { for k, v in random_password.token : k => v.result },
    { for k, v in random_password.login : k => v.result },
    {
      LANGFUSE_PUBLIC_KEY     = "pk-lf-${random_id.langfuse["public"].hex}"
      LANGFUSE_SECRET_KEY     = "sk-lf-${random_id.langfuse["secret"].hex}"
      LANGFUSE_ENCRYPTION_KEY = random_id.langfuse["encryption"].hex
    }
  )
}

resource "aws_secretsmanager_secret" "app" {
  name                    = "${local.name}/app-${random_id.suffix.hex}"
  description             = "Aurelia supply-chain copilot runtime secrets (Compose .env source)"
  recovery_window_in_days = 0
}

resource "aws_secretsmanager_secret_version" "app" {
  secret_id     = aws_secretsmanager_secret.app.id
  secret_string = jsonencode(local.app_secrets)
}

# ------------------------------------------------------------- artifacts
resource "aws_s3_bucket" "artifacts" {
  bucket        = "${local.name}-artifacts-${random_id.suffix.hex}"
  force_destroy = true
}

resource "aws_s3_bucket_public_access_block" "artifacts" {
  bucket                  = aws_s3_bucket.artifacts.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_versioning" "artifacts" {
  bucket = aws_s3_bucket.artifacts.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "artifacts" {
  bucket = aws_s3_bucket.artifacts.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_ecr_repository" "app" {
  name                 = "${local.name}/app"
  image_tag_mutability = "MUTABLE"
  force_delete         = true
  image_scanning_configuration {
    scan_on_push = true
  }
  encryption_configuration {
    encryption_type = "AES256"
  }
}

resource "aws_ecr_lifecycle_policy" "app" {
  repository = aws_ecr_repository.app.name
  policy = jsonencode({
    rules = [{
      rulePriority = 1
      description  = "Keep the last 10 images"
      selection    = { tagStatus = "any", countType = "imageCountMoreThan", countNumber = 10 }
      action       = { type = "expire" }
    }]
  })
}

# ------------------------------------------------------------ PostgreSQL
resource "aws_db_subnet_group" "this" {
  name       = local.name
  subnet_ids = [for s in aws_subnet.db : s.id]
}

resource "aws_db_parameter_group" "pg17" {
  name   = "${local.name}-pg17"
  family = "postgres17"
  parameter {
    name  = "rds.force_ssl"
    value = "1"
  }
}

resource "aws_db_instance" "postgres" {
  identifier                   = "${local.name}-pg"
  engine                       = "postgres"
  engine_version               = "17"
  instance_class               = var.db_instance_class
  allocated_storage            = var.db_allocated_storage_gb
  storage_type                 = "gp3"
  storage_encrypted            = true
  db_name                      = "supplychain"
  username                     = "supplychain"
  password                     = random_password.token["POSTGRES_PASSWORD"].result
  db_subnet_group_name         = aws_db_subnet_group.this.name
  vpc_security_group_ids       = [aws_security_group.db.id]
  parameter_group_name         = aws_db_parameter_group.pg17.name
  publicly_accessible          = false
  multi_az                     = false
  backup_retention_period      = 1
  skip_final_snapshot          = true
  deletion_protection          = false
  auto_minor_version_upgrade   = true
  performance_insights_enabled = false
  apply_immediately            = true
}

# ------------------------------------------------------------ logging
resource "aws_cloudwatch_log_group" "app" {
  name              = "/${var.project_name}/${var.environment}"
  retention_in_days = var.log_retention_days
}
