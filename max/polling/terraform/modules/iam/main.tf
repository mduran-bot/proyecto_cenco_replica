# ============================================================================
# IAM Module - API Polling System
# ============================================================================
# This module creates IAM roles and policies for the API polling system
# components including MWAA execution role and EventBridge invocation role.
# ============================================================================

terraform {
  required_version = ">= 1.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# ============================================================================
# MWAA Execution Role
# ============================================================================

resource "aws_iam_role" "mwaa_execution" {
  name = var.mwaa_role_name
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = [
            "airflow.amazonaws.com",
            "airflow-env.amazonaws.com"
          ]
        }
        Action = "sts:AssumeRole"
      }
    ]
  })

  tags = merge(var.tags, {
    Name      = var.mwaa_role_name
    Purpose   = "MWAA Execution Role for API Polling"
    ManagedBy = "terraform"
  })
}

# Policy for DynamoDB access (polling control table)
resource "aws_iam_role_policy" "mwaa_dynamodb" {
  name = "${var.mwaa_role_name}-dynamodb"
  role = aws_iam_role.mwaa_execution.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "dynamodb:GetItem",
          "dynamodb:PutItem",
          "dynamodb:UpdateItem",
          "dynamodb:DeleteItem",
          "dynamodb:Query",
          "dynamodb:Scan",
          "dynamodb:DescribeTable"
        ]
        Resource = var.dynamodb_table_arn
      }
    ]
  })
}

# Policy for S3 access (DAGs, staging bucket)
resource "aws_iam_role_policy" "mwaa_s3" {
  name = "${var.mwaa_role_name}-s3"
  role = aws_iam_role.mwaa_execution.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject",
          "s3:ListBucket"
        ]
        Resource = concat(
          [for bucket in var.s3_bucket_arns : "${bucket}/*"],
          var.s3_bucket_arns
        )
      }
    ]
  })
}

# Policy for SNS access (error notifications)
resource "aws_iam_role_policy" "mwaa_sns" {
  name = "${var.mwaa_role_name}-sns"
  role = aws_iam_role.mwaa_execution.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "sns:Publish"
        ]
        Resource = var.sns_topic_arn
      }
    ]
  })
}

# Policy for CloudWatch Logs
resource "aws_iam_role_policy" "mwaa_cloudwatch" {
  name = "${var.mwaa_role_name}-cloudwatch"
  role = aws_iam_role.mwaa_execution.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents",
          "logs:DescribeLogStreams"
        ]
        Resource = "arn:aws:logs:${var.aws_region}:${var.aws_account_id}:log-group:/aws/mwaa/*"
      },
      {
        Effect = "Allow"
        Action = [
          "cloudwatch:PutMetricData"
        ]
        Resource = "*"
      }
    ]
  })
}

# Policy for Secrets Manager (API credentials)
resource "aws_iam_role_policy" "mwaa_secrets" {
  count = length(var.secrets_manager_arns) > 0 ? 1 : 0
  name  = "${var.mwaa_role_name}-secrets"
  role  = aws_iam_role.mwaa_execution.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue",
          "secretsmanager:DescribeSecret"
        ]
        Resource = var.secrets_manager_arns
      }
    ]
  })
}

# ============================================================================
# EventBridge Role (to invoke MWAA)
# ============================================================================

resource "aws_iam_role" "eventbridge_mwaa" {
  name = var.eventbridge_role_name
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "events.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })

  tags = merge(var.tags, {
    Name      = var.eventbridge_role_name
    Purpose   = "EventBridge to MWAA Invocation"
    ManagedBy = "terraform"
  })
}

# Policy for EventBridge to invoke MWAA
resource "aws_iam_role_policy" "eventbridge_mwaa_invoke" {
  name = "${var.eventbridge_role_name}-invoke"
  role = aws_iam_role.eventbridge_mwaa.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "airflow:CreateCliToken"
        ]
        Resource = var.mwaa_environment_arn
      }
    ]
  })
}
