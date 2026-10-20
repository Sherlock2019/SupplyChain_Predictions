data "aws_availability_zones" "available" {
  state = "available"
}

data "aws_ec2_instance_type_offerings" "gpu" {
  location_type = "availability-zone"
  filter {
    name   = "instance-type"
    values = [var.gpu_instance_type]
  }
}

locals {
  name = "${var.project_name}-${var.environment}"
  # Place the public subnet in an AZ that offers the GPU type; the second AZ only hosts the RDS subnet group.
  gpu_azs    = sort(data.aws_ec2_instance_type_offerings.gpu.locations)
  primary_az = length(local.gpu_azs) > 0 ? local.gpu_azs[0] : data.aws_availability_zones.available.names[0]
  second_az  = [for az in data.aws_availability_zones.available.names : az if az != local.primary_az][0]
}

resource "aws_vpc" "this" {
  cidr_block           = "10.42.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true
  tags                 = { Name = local.name }
}

resource "aws_internet_gateway" "this" {
  vpc_id = aws_vpc.this.id
  tags   = { Name = local.name }
}

resource "aws_subnet" "public" {
  vpc_id                  = aws_vpc.this.id
  cidr_block              = "10.42.10.0/24"
  availability_zone       = local.primary_az
  map_public_ip_on_launch = true
  tags                    = { Name = "${local.name}-public" }
}

resource "aws_subnet" "db" {
  for_each          = { a = local.primary_az, b = local.second_az }
  vpc_id            = aws_vpc.this.id
  cidr_block        = each.key == "a" ? "10.42.20.0/24" : "10.42.21.0/24"
  availability_zone = each.value
  tags              = { Name = "${local.name}-db-${each.key}" }
}

resource "aws_route_table" "public" {
  vpc_id = aws_vpc.this.id
  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.this.id
  }
  tags = { Name = "${local.name}-public" }
}

resource "aws_route_table_association" "public" {
  subnet_id      = aws_subnet.public.id
  route_table_id = aws_route_table.public.id
}

# ------------------------------------------------------------------ firewalls
resource "aws_security_group" "app" {
  name        = "${local.name}-app"
  description = "HTTPS for operators; HTTP only for ACME challenges and redirect"
  vpc_id      = aws_vpc.this.id
  tags        = { Name = "${local.name}-app" }
}

resource "aws_vpc_security_group_ingress_rule" "app_https" {
  for_each          = toset(var.allowed_cidrs)
  security_group_id = aws_security_group.app.id
  description       = "Operator HTTPS"
  cidr_ipv4         = each.value
  from_port         = 443
  to_port           = 443
  ip_protocol       = "tcp"
}

resource "aws_vpc_security_group_ingress_rule" "app_acme" {
  security_group_id = aws_security_group.app.id
  description       = "ACME HTTP-01 challenge and redirect to HTTPS (Caddy)"
  cidr_ipv4         = "0.0.0.0/0"
  from_port         = 80
  to_port           = 80
  ip_protocol       = "tcp"
}

resource "aws_vpc_security_group_egress_rule" "app_all" {
  security_group_id = aws_security_group.app.id
  cidr_ipv4         = "0.0.0.0/0"
  ip_protocol       = "-1"
}

resource "aws_security_group" "gpu" {
  name        = "${local.name}-gpu"
  description = "vLLM reachable only from the application VM"
  vpc_id      = aws_vpc.this.id
  tags        = { Name = "${local.name}-gpu" }
}

resource "aws_vpc_security_group_ingress_rule" "gpu_vllm" {
  security_group_id            = aws_security_group.gpu.id
  description                  = "OpenAI-compatible vLLM API and /metrics from the app VM"
  referenced_security_group_id = aws_security_group.app.id
  from_port                    = 8000
  to_port                      = 8000
  ip_protocol                  = "tcp"
}

resource "aws_vpc_security_group_egress_rule" "gpu_all" {
  security_group_id = aws_security_group.gpu.id
  cidr_ipv4         = "0.0.0.0/0"
  ip_protocol       = "-1"
}

resource "aws_security_group" "db" {
  name        = "${local.name}-db"
  description = "PostgreSQL from the application VM only"
  vpc_id      = aws_vpc.this.id
  tags        = { Name = "${local.name}-db" }
}

resource "aws_vpc_security_group_ingress_rule" "db_pg" {
  security_group_id            = aws_security_group.db.id
  referenced_security_group_id = aws_security_group.app.id
  from_port                    = 5432
  to_port                      = 5432
  ip_protocol                  = "tcp"
}
