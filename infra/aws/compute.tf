data "aws_caller_identity" "current" {}

data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"] # Canonical
  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd-gp3/ubuntu-noble-24.04-amd64-server-*"]
  }
  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

# AWS Deep Learning Base AMI: NVIDIA driver, Docker and the NVIDIA container toolkit preinstalled.
data "aws_ami" "gpu" {
  most_recent = true
  owners      = ["amazon"]
  filter {
    name   = "name"
    values = ["Deep Learning Base OSS Nvidia Driver GPU AMI (Ubuntu 24.04)*"]
  }
  filter {
    name   = "architecture"
    values = ["x86_64"]
  }
}

# ---------------------------------------------------------------------- IAM
data "aws_iam_policy_document" "ec2_assume" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["ec2.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "app" {
  name               = "${local.name}-app"
  assume_role_policy = data.aws_iam_policy_document.ec2_assume.json
}

resource "aws_iam_role" "gpu" {
  name               = "${local.name}-gpu"
  assume_role_policy = data.aws_iam_policy_document.ec2_assume.json
}

resource "aws_iam_role_policy_attachment" "ssm" {
  for_each   = { app = aws_iam_role.app.name, gpu = aws_iam_role.gpu.name }
  role       = each.value
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

data "aws_iam_policy_document" "app" {
  statement {
    sid       = "ReadReleaseBundles"
    actions   = ["s3:GetObject", "s3:ListBucket"]
    resources = [aws_s3_bucket.artifacts.arn, "${aws_s3_bucket.artifacts.arn}/*"]
  }
  statement {
    sid       = "ReadRuntimeSecrets"
    actions   = ["secretsmanager:GetSecretValue"]
    resources = [aws_secretsmanager_secret.app.arn]
  }
  statement {
    sid       = "PullAppImage"
    actions   = ["ecr:BatchCheckLayerAvailability", "ecr:GetDownloadUrlForLayer", "ecr:BatchGetImage", "ecr:DescribeImages"]
    resources = [aws_ecr_repository.app.arn]
  }
  statement {
    sid       = "EcrLogin"
    actions   = ["ecr:GetAuthorizationToken"]
    resources = ["*"]
  }
  statement {
    sid       = "ShipContainerLogs"
    actions   = ["logs:CreateLogStream", "logs:PutLogEvents", "logs:DescribeLogStreams"]
    resources = ["${aws_cloudwatch_log_group.app.arn}:*"]
  }
}

resource "aws_iam_role_policy" "app" {
  role   = aws_iam_role.app.id
  policy = data.aws_iam_policy_document.app.json
}

data "aws_iam_policy_document" "gpu" {
  statement {
    sid       = "ReadVllmKey"
    actions   = ["secretsmanager:GetSecretValue"]
    resources = [aws_secretsmanager_secret.app.arn]
  }
  statement {
    sid       = "ShipContainerLogs"
    actions   = ["logs:CreateLogStream", "logs:PutLogEvents", "logs:DescribeLogStreams"]
    resources = ["${aws_cloudwatch_log_group.app.arn}:*"]
  }
}

resource "aws_iam_role_policy" "gpu" {
  role   = aws_iam_role.gpu.id
  policy = data.aws_iam_policy_document.gpu.json
}

resource "aws_iam_instance_profile" "app" {
  name = "${local.name}-app"
  role = aws_iam_role.app.name
}

resource "aws_iam_instance_profile" "gpu" {
  name = "${local.name}-gpu"
  role = aws_iam_role.gpu.name
}

# ------------------------------------------------------------------ GPU VM
resource "aws_instance" "gpu" {
  count                       = var.enable_gpu ? 1 : 0
  ami                         = data.aws_ami.gpu.id
  instance_type               = var.gpu_instance_type
  subnet_id                   = aws_subnet.public.id
  vpc_security_group_ids      = [aws_security_group.gpu.id]
  iam_instance_profile        = aws_iam_instance_profile.gpu.name
  user_data_replace_on_change = true
  user_data = templatefile("${path.module}/templates/gpu-cloud-init.sh.tftpl", {
    region      = var.region
    secret_id   = aws_secretsmanager_secret.app.id
    log_group   = aws_cloudwatch_log_group.app.name
    vllm_image  = var.vllm_image
    vllm_model  = var.vllm_model
    served_name = var.qwen_served_name
  })
  root_block_device {
    volume_size           = var.gpu_root_volume_gb
    volume_type           = "gp3"
    encrypted             = true
    delete_on_termination = true
  }
  metadata_options {
    http_endpoint               = "enabled"
    http_tokens                 = "required"
    http_put_response_hop_limit = 2
  }
  tags = { Name = "${local.name}-gpu-qwen" }
}

# ------------------------------------------------------------------ app VM
resource "aws_eip" "app" {
  domain = "vpc"
  tags   = { Name = "${local.name}-app" }
}

locals {
  base_domain = "${replace(aws_eip.app.public_ip, ".", "-")}.sslip.io"
  # GPU VM (vLLM) when enabled; otherwise Qwen on CPU via Ollama inside the app VM; otherwise no LLM.
  qwen_base_url = var.enable_gpu ? "http://${aws_instance.gpu[0].private_ip}:8000/v1" : (var.cpu_llm_model != "" ? "http://ollama:11434/v1" : "")
  qwen_model    = var.enable_gpu ? var.qwen_served_name : "${replace(var.cpu_llm_model, ":", "-")}-scm"
  app_image     = "${aws_ecr_repository.app.repository_url}:${var.release_version}"
}

resource "aws_instance" "app" {
  ami                         = data.aws_ami.ubuntu.id
  instance_type               = var.app_instance_type
  subnet_id                   = aws_subnet.public.id
  vpc_security_group_ids      = [aws_security_group.app.id]
  iam_instance_profile        = aws_iam_instance_profile.app.name
  user_data_replace_on_change = false
  user_data = templatefile("${path.module}/templates/app-cloud-init.sh.tftpl", {
    region               = var.region
    bucket               = aws_s3_bucket.artifacts.id
    release_version      = var.release_version
    secret_id            = aws_secretsmanager_secret.app.id
    log_group            = aws_cloudwatch_log_group.app.name
    registry             = split("/", aws_ecr_repository.app.repository_url)[0]
    app_image            = local.app_image
    db_host              = aws_db_instance.postgres.address
    base_domain          = local.base_domain
    acme_email           = var.acme_email
    qwen_base_url        = local.qwen_base_url
    qwen_model           = local.qwen_model
    cpu_llm_model        = var.enable_gpu ? "" : var.cpu_llm_model
    public_ip            = aws_eip.app.public_ip
    qwen_metrics_target  = var.enable_gpu ? "${aws_instance.gpu[0].private_ip}:8000" : ""
    enable_observability = var.enable_observability
  })
  root_block_device {
    volume_size           = var.app_root_volume_gb
    volume_type           = "gp3"
    encrypted             = true
    delete_on_termination = true
  }
  metadata_options {
    http_endpoint               = "enabled"
    http_tokens                 = "required"
    http_put_response_hop_limit = 2
  }
  tags = { Name = "${local.name}-app" }
}

resource "aws_eip_association" "app" {
  instance_id   = aws_instance.app.id
  allocation_id = aws_eip.app.id
}

# ---------------------------------------------------------- health & cost
resource "aws_cloudwatch_metric_alarm" "status" {
  for_each            = merge({ app = aws_instance.app.id }, var.enable_gpu ? { gpu = aws_instance.gpu[0].id } : {})
  alarm_name          = "${local.name}-${each.key}-status-check"
  namespace           = "AWS/EC2"
  metric_name         = "StatusCheckFailed"
  statistic           = "Maximum"
  period              = 300
  evaluation_periods  = 2
  threshold           = 1
  comparison_operator = "GreaterThanOrEqualToThreshold"
  dimensions          = { InstanceId = each.value }
}

resource "aws_budgets_budget" "poc" {
  count        = var.monthly_budget_usd > 0 && var.budget_email != "" ? 1 : 0
  name         = "${local.name}-monthly"
  budget_type  = "COST"
  limit_amount = tostring(var.monthly_budget_usd)
  limit_unit   = "USD"
  time_unit    = "MONTHLY"
  cost_filter {
    name   = "TagKeyValue"
    values = [format("user:Project$%s", var.project_name)]
  }
  dynamic "notification" {
    for_each = [50, 80, 100]
    content {
      comparison_operator        = "GREATER_THAN"
      threshold                  = notification.value
      threshold_type             = "PERCENTAGE"
      notification_type          = "ACTUAL"
      subscriber_email_addresses = [var.budget_email]
    }
  }
}
