# ============================================================================
# VPC Endpoints Module
# Creates Gateway and Interface Endpoints
# ============================================================================

# ============================================================================
# S3 Gateway Endpoint
# ============================================================================

resource "aws_vpc_endpoint" "s3" {
  count = var.enable_s3_endpoint ? 1 : 0

  vpc_id            = var.vpc_id
  service_name      = "com.amazonaws.${data.aws_region.current.name}.s3"
  vpc_endpoint_type = "Gateway"
  route_table_ids   = var.route_table_ids

  tags = merge(var.tags, {
    Name      = "${var.name_prefix}-s3-endpoint"
    Component = "vpc-endpoint"
    Type      = "gateway"
    Service   = "s3"
  })
}

# ============================================================================
# Interface Endpoints
# ============================================================================

# AWS Glue
resource "aws_vpc_endpoint" "glue" {
  count = var.enable_glue_endpoint ? 1 : 0

  vpc_id              = var.vpc_id
  service_name        = "com.amazonaws.${data.aws_region.current.name}.glue"
  vpc_endpoint_type   = "Interface"
  subnet_ids          = [var.private_subnet_ids[0]] # Solo primera subnet para evitar error de AZ duplicada
  security_group_ids  = [var.vpc_endpoints_security_group_id]
  private_dns_enabled = true

  tags = merge(var.tags, {
    Name      = "${var.name_prefix}-glue-endpoint"
    Component = "vpc-endpoint"
    Type      = "interface"
    Service   = "glue"
  })
}

# AWS Secrets Manager
resource "aws_vpc_endpoint" "secretsmanager" {
  count = var.enable_secrets_manager_endpoint ? 1 : 0

  vpc_id              = var.vpc_id
  service_name        = "com.amazonaws.${data.aws_region.current.name}.secretsmanager"
  vpc_endpoint_type   = "Interface"
  subnet_ids          = [var.private_subnet_ids[0]] # Solo primera subnet para evitar error de AZ duplicada
  security_group_ids  = [var.vpc_endpoints_security_group_id]
  private_dns_enabled = true

  tags = merge(var.tags, {
    Name      = "${var.name_prefix}-secretsmanager-endpoint"
    Component = "vpc-endpoint"
    Type      = "interface"
    Service   = "secretsmanager"
  })
}

# CloudWatch Logs
resource "aws_vpc_endpoint" "logs" {
  count = var.enable_logs_endpoint ? 1 : 0

  vpc_id              = var.vpc_id
  service_name        = "com.amazonaws.${data.aws_region.current.name}.logs"
  vpc_endpoint_type   = "Interface"
  subnet_ids          = [var.private_subnet_ids[0]] # Solo primera subnet para evitar error de AZ duplicada
  security_group_ids  = [var.vpc_endpoints_security_group_id]
  private_dns_enabled = true

  tags = merge(var.tags, {
    Name      = "${var.name_prefix}-logs-endpoint"
    Component = "vpc-endpoint"
    Type      = "interface"
    Service   = "logs"
  })
}

# AWS KMS
resource "aws_vpc_endpoint" "kms" {
  count = var.enable_kms_endpoint ? 1 : 0

  vpc_id              = var.vpc_id
  service_name        = "com.amazonaws.${data.aws_region.current.name}.kms"
  vpc_endpoint_type   = "Interface"
  subnet_ids          = [var.private_subnet_ids[0]] # Solo primera subnet para evitar error de AZ duplicada
  security_group_ids  = [var.vpc_endpoints_security_group_id]
  private_dns_enabled = true

  tags = merge(var.tags, {
    Name      = "${var.name_prefix}-kms-endpoint"
    Component = "vpc-endpoint"
    Type      = "interface"
    Service   = "kms"
  })
}

# AWS STS
resource "aws_vpc_endpoint" "sts" {
  count = var.enable_sts_endpoint ? 1 : 0

  vpc_id              = var.vpc_id
  service_name        = "com.amazonaws.${data.aws_region.current.name}.sts"
  vpc_endpoint_type   = "Interface"
  subnet_ids          = [var.private_subnet_ids[0]] # Solo primera subnet para evitar error de AZ duplicada
  security_group_ids  = [var.vpc_endpoints_security_group_id]
  private_dns_enabled = true

  tags = merge(var.tags, {
    Name      = "${var.name_prefix}-sts-endpoint"
    Component = "vpc-endpoint"
    Type      = "interface"
    Service   = "sts"
  })
}

# Amazon EventBridge
resource "aws_vpc_endpoint" "events" {
  count = var.enable_events_endpoint ? 1 : 0

  vpc_id              = var.vpc_id
  service_name        = "com.amazonaws.${data.aws_region.current.name}.events"
  vpc_endpoint_type   = "Interface"
  subnet_ids          = [var.private_subnet_ids[0]] # Solo primera subnet para evitar error de AZ duplicada
  security_group_ids  = [var.vpc_endpoints_security_group_id]
  private_dns_enabled = true

  tags = merge(var.tags, {
    Name      = "${var.name_prefix}-events-endpoint"
    Component = "vpc-endpoint"
    Type      = "interface"
    Service   = "events"
  })
}

# ============================================================================
# Data Sources
# ============================================================================

data "aws_region" "current" {}
