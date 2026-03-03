# ============================================================================
# Security Groups Module
# Creates all security groups for the infrastructure
# ============================================================================

# ============================================================================
# SG-API-Gateway
# Purpose: Protect API Gateway webhook endpoints
# ============================================================================

resource "aws_security_group" "api_gateway" {
  name        = "${var.name_prefix}-sg-api-gateway"
  description = "Security group for API Gateway webhook endpoints"
  vpc_id      = var.vpc_id

  tags = merge(var.tags, {
    Name      = "${var.name_prefix}-sg-api-gateway"
    Component = "security-group"
    Purpose   = "api-gateway"
  })
}

resource "aws_vpc_security_group_ingress_rule" "api_gateway_https" {
  security_group_id = aws_security_group.api_gateway.id
  description       = "HTTPS from Janis webhooks"

  from_port   = 443
  to_port     = 443
  ip_protocol = "tcp"
  cidr_ipv4   = length(var.allowed_janis_ip_ranges) > 0 ? var.allowed_janis_ip_ranges[0] : "0.0.0.0/0"
}

# Additional ingress rules for multiple Janis IP ranges
resource "aws_vpc_security_group_ingress_rule" "api_gateway_https_additional" {
  count = length(var.allowed_janis_ip_ranges) > 1 ? length(var.allowed_janis_ip_ranges) - 1 : 0

  security_group_id = aws_security_group.api_gateway.id
  description       = "HTTPS from Janis webhooks (additional range ${count.index + 1})"

  from_port   = 443
  to_port     = 443
  ip_protocol = "tcp"
  cidr_ipv4   = var.allowed_janis_ip_ranges[count.index + 1]
}

resource "aws_vpc_security_group_egress_rule" "api_gateway_all" {
  security_group_id = aws_security_group.api_gateway.id
  description       = "Allow all outbound traffic"

  ip_protocol = "-1"
  cidr_ipv4   = "0.0.0.0/0"
}

# ============================================================================
# SG-Redshift-Existing
# Purpose: Control access to existing Cencosud Redshift cluster
# ============================================================================

resource "aws_security_group" "redshift" {
  name        = "${var.name_prefix}-sg-redshift"
  description = "Security group for Redshift cluster"
  vpc_id      = var.vpc_id

  tags = merge(var.tags, {
    Name      = "${var.name_prefix}-sg-redshift"
    Component = "security-group"
    Purpose   = "redshift"
  })
}

# Inbound from Lambda
resource "aws_vpc_security_group_ingress_rule" "redshift_from_lambda" {
  security_group_id = aws_security_group.redshift.id
  description       = "PostgreSQL from Lambda functions"

  from_port                    = 5439
  to_port                      = 5439
  ip_protocol                  = "tcp"
  referenced_security_group_id = aws_security_group.lambda.id
}

# Inbound from MWAA
resource "aws_vpc_security_group_ingress_rule" "redshift_from_mwaa" {
  security_group_id = aws_security_group.redshift.id
  description       = "PostgreSQL from MWAA Airflow"

  from_port                    = 5439
  to_port                      = 5439
  ip_protocol                  = "tcp"
  referenced_security_group_id = aws_security_group.mwaa.id
}

# Inbound from existing BI systems (Security Groups)
resource "aws_vpc_security_group_ingress_rule" "redshift_from_bi_sg" {
  count = length(var.existing_bi_security_groups)

  security_group_id = aws_security_group.redshift.id
  description       = "PostgreSQL from existing BI system ${count.index + 1}"

  from_port                    = 5439
  to_port                      = 5439
  ip_protocol                  = "tcp"
  referenced_security_group_id = var.existing_bi_security_groups[count.index]
}

# Inbound from existing BI systems (IP ranges)
resource "aws_vpc_security_group_ingress_rule" "redshift_from_bi_ip" {
  count = length(var.existing_bi_ip_ranges)

  security_group_id = aws_security_group.redshift.id
  description       = "PostgreSQL from existing BI IP range ${count.index + 1}"

  from_port   = 5439
  to_port     = 5439
  ip_protocol = "tcp"
  cidr_ipv4   = var.existing_bi_ip_ranges[count.index]
}

# Inbound from MySQL pipeline (temporary during migration)
resource "aws_vpc_security_group_ingress_rule" "redshift_from_mysql_pipeline" {
  count = var.existing_mysql_pipeline_sg_id != "" ? 1 : 0

  security_group_id = aws_security_group.redshift.id
  description       = "PostgreSQL from MySQL pipeline (temporary)"

  from_port                    = 5439
  to_port                      = 5439
  ip_protocol                  = "tcp"
  referenced_security_group_id = var.existing_mysql_pipeline_sg_id
}

# Outbound to VPC Endpoints only
resource "aws_vpc_security_group_egress_rule" "redshift_to_vpc_endpoints" {
  security_group_id = aws_security_group.redshift.id
  description       = "HTTPS to VPC Endpoints"

  from_port                    = 443
  to_port                      = 443
  ip_protocol                  = "tcp"
  referenced_security_group_id = aws_security_group.vpc_endpoints.id
}

# ============================================================================
# SG-Lambda
# Purpose: Lambda function network security
# ============================================================================

resource "aws_security_group" "lambda" {
  name        = "${var.name_prefix}-sg-lambda"
  description = "Security group for Lambda functions"
  vpc_id      = var.vpc_id

  tags = merge(var.tags, {
    Name      = "${var.name_prefix}-sg-lambda"
    Component = "security-group"
    Purpose   = "lambda"
  })
}

# Outbound to Redshift
resource "aws_vpc_security_group_egress_rule" "lambda_to_redshift" {
  security_group_id = aws_security_group.lambda.id
  description       = "PostgreSQL to Redshift cluster"

  from_port                    = 5439
  to_port                      = 5439
  ip_protocol                  = "tcp"
  referenced_security_group_id = aws_security_group.redshift.id
}

# Outbound to VPC Endpoints
resource "aws_vpc_security_group_egress_rule" "lambda_to_vpc_endpoints" {
  security_group_id = aws_security_group.lambda.id
  description       = "HTTPS to VPC Endpoints"

  from_port                    = 443
  to_port                      = 443
  ip_protocol                  = "tcp"
  referenced_security_group_id = aws_security_group.vpc_endpoints.id
}

# Outbound to internet (for Janis API polling)
resource "aws_vpc_security_group_egress_rule" "lambda_to_internet" {
  security_group_id = aws_security_group.lambda.id
  description       = "HTTPS to internet (Janis API)"

  from_port   = 443
  to_port     = 443
  ip_protocol = "tcp"
  cidr_ipv4   = "0.0.0.0/0"
}

# ============================================================================
# SG-MWAA
# Purpose: MWAA environment security
# ============================================================================

resource "aws_security_group" "mwaa" {
  name        = "${var.name_prefix}-sg-mwaa"
  description = "Security group for MWAA Airflow environment"
  vpc_id      = var.vpc_id

  tags = merge(var.tags, {
    Name      = "${var.name_prefix}-sg-mwaa"
    Component = "security-group"
    Purpose   = "mwaa"
  })
}

# Inbound from self (worker communication)
resource "aws_vpc_security_group_ingress_rule" "mwaa_self" {
  security_group_id = aws_security_group.mwaa.id
  description       = "HTTPS from MWAA workers (self-reference)"

  from_port                    = 443
  to_port                      = 443
  ip_protocol                  = "tcp"
  referenced_security_group_id = aws_security_group.mwaa.id
}

# Outbound to VPC Endpoints
resource "aws_vpc_security_group_egress_rule" "mwaa_to_vpc_endpoints" {
  security_group_id = aws_security_group.mwaa.id
  description       = "HTTPS to VPC Endpoints"

  from_port                    = 443
  to_port                      = 443
  ip_protocol                  = "tcp"
  referenced_security_group_id = aws_security_group.vpc_endpoints.id
}

# Outbound to internet
resource "aws_vpc_security_group_egress_rule" "mwaa_to_internet" {
  security_group_id = aws_security_group.mwaa.id
  description       = "HTTPS to internet"

  from_port   = 443
  to_port     = 443
  ip_protocol = "tcp"
  cidr_ipv4   = "0.0.0.0/0"
}

# Outbound to Redshift
resource "aws_vpc_security_group_egress_rule" "mwaa_to_redshift" {
  security_group_id = aws_security_group.mwaa.id
  description       = "PostgreSQL to Redshift cluster"

  from_port                    = 5439
  to_port                      = 5439
  ip_protocol                  = "tcp"
  referenced_security_group_id = aws_security_group.redshift.id
}

# ============================================================================
# SG-Glue
# Purpose: Glue job network security
# ============================================================================

resource "aws_security_group" "glue" {
  name        = "${var.name_prefix}-sg-glue"
  description = "Security group for AWS Glue jobs"
  vpc_id      = var.vpc_id

  tags = merge(var.tags, {
    Name      = "${var.name_prefix}-sg-glue"
    Component = "security-group"
    Purpose   = "glue"
  })
}

# Inbound from self (Spark cluster communication)
resource "aws_vpc_security_group_ingress_rule" "glue_self" {
  security_group_id = aws_security_group.glue.id
  description       = "All TCP from Glue (self-reference for Spark)"

  from_port                    = 0
  to_port                      = 65535
  ip_protocol                  = "tcp"
  referenced_security_group_id = aws_security_group.glue.id
}

# Outbound to VPC Endpoints
resource "aws_vpc_security_group_egress_rule" "glue_to_vpc_endpoints" {
  security_group_id = aws_security_group.glue.id
  description       = "HTTPS to VPC Endpoints"

  from_port                    = 443
  to_port                      = 443
  ip_protocol                  = "tcp"
  referenced_security_group_id = aws_security_group.vpc_endpoints.id
}

# Outbound to self (Spark cluster communication)
resource "aws_vpc_security_group_egress_rule" "glue_self_egress" {
  security_group_id = aws_security_group.glue.id
  description       = "All TCP to Glue (self-reference for Spark)"

  from_port                    = 0
  to_port                      = 65535
  ip_protocol                  = "tcp"
  referenced_security_group_id = aws_security_group.glue.id
}

# ============================================================================
# SG-EventBridge
# Purpose: EventBridge VPC endpoint security
# ============================================================================

resource "aws_security_group" "eventbridge" {
  name        = "${var.name_prefix}-sg-eventbridge"
  description = "Security group for EventBridge VPC endpoint"
  vpc_id      = var.vpc_id

  tags = merge(var.tags, {
    Name      = "${var.name_prefix}-sg-eventbridge"
    Component = "security-group"
    Purpose   = "eventbridge"
  })
}

# Outbound to MWAA
resource "aws_vpc_security_group_egress_rule" "eventbridge_to_mwaa" {
  security_group_id = aws_security_group.eventbridge.id
  description       = "HTTPS to MWAA for DAG triggering"

  from_port                    = 443
  to_port                      = 443
  ip_protocol                  = "tcp"
  referenced_security_group_id = aws_security_group.mwaa.id
}

# Outbound to VPC Endpoints
resource "aws_vpc_security_group_egress_rule" "eventbridge_to_vpc_endpoints" {
  security_group_id = aws_security_group.eventbridge.id
  description       = "HTTPS to VPC Endpoints"

  from_port                    = 443
  to_port                      = 443
  ip_protocol                  = "tcp"
  referenced_security_group_id = aws_security_group.vpc_endpoints.id
}

# ============================================================================
# SG-VPC-Endpoints
# Purpose: Common security group for all VPC Interface Endpoints
# ============================================================================

resource "aws_security_group" "vpc_endpoints" {
  name        = "${var.name_prefix}-sg-vpc-endpoints"
  description = "Security group for VPC Interface Endpoints"
  vpc_id      = var.vpc_id

  tags = merge(var.tags, {
    Name      = "${var.name_prefix}-sg-vpc-endpoints"
    Component = "security-group"
    Purpose   = "vpc-endpoints"
  })
}

# Inbound from entire VPC
resource "aws_vpc_security_group_ingress_rule" "vpc_endpoints_from_vpc" {
  security_group_id = aws_security_group.vpc_endpoints.id
  description       = "HTTPS from all VPC resources"

  from_port   = 443
  to_port     = 443
  ip_protocol = "tcp"
  cidr_ipv4   = var.vpc_cidr
}

# Outbound to AWS services
resource "aws_vpc_security_group_egress_rule" "vpc_endpoints_to_aws" {
  security_group_id = aws_security_group.vpc_endpoints.id
  description       = "HTTPS to AWS services"

  from_port   = 443
  to_port     = 443
  ip_protocol = "tcp"
  cidr_ipv4   = "0.0.0.0/0"
}
