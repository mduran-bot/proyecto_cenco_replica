# ============================================================================
# Lambda Module - Serverless Functions
# Creates Lambda functions for webhook processing and data enrichment
# ============================================================================

# ============================================================================
# IAM Role for Lambda Functions
# ============================================================================

resource "aws_iam_role" "lambda_execution_role" {
  name = "${var.name_prefix}-lambda-execution-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-lambda-execution-role"
  })
}

# ============================================================================
# IAM Policy for Lambda Functions
# ============================================================================

resource "aws_iam_role_policy" "lambda_policy" {
  name = "${var.name_prefix}-lambda-policy"
  role = aws_iam_role.lambda_execution_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:*:*:*"
      },
      {
        Effect = "Allow"
        Action = [
          "s3:PutObject",
          "s3:GetObject",
          "s3:ListBucket"
        ]
        Resource = [
          "${var.bronze_bucket_arn}",
          "${var.bronze_bucket_arn}/*",
          "${var.scripts_bucket_arn}",
          "${var.scripts_bucket_arn}/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "firehose:PutRecord",
          "firehose:PutRecordBatch"
        ]
        Resource = var.firehose_delivery_stream_arn != "" ? [var.firehose_delivery_stream_arn] : []
      },
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue"
        ]
        Resource = "arn:aws:secretsmanager:*:*:secret:janis/*"
      },
      {
        Effect = "Allow"
        Action = [
          "ec2:CreateNetworkInterface",
          "ec2:DescribeNetworkInterfaces",
          "ec2:DeleteNetworkInterface"
        ]
        Resource = "*"
      }
    ]
  })
}

# ============================================================================
# Lambda Function: Webhook Processor
# ============================================================================

resource "aws_lambda_function" "webhook_processor" {
  count = var.create_webhook_processor ? 1 : 0

  function_name = "${var.name_prefix}-webhook-processor"
  role          = aws_iam_role.lambda_execution_role.arn
  handler       = "index.handler"
  runtime       = var.lambda_runtime
  timeout       = var.lambda_timeout
  memory_size   = var.lambda_memory_size

  # Placeholder code - replace with actual deployment package
  filename         = var.webhook_processor_zip_path != "" ? var.webhook_processor_zip_path : null
  source_code_hash = var.webhook_processor_zip_path != "" ? filebase64sha256(var.webhook_processor_zip_path) : null

  # If no zip provided, use inline code
  dynamic "environment" {
    for_each = var.webhook_processor_zip_path == "" ? [1] : []
    content {
      variables = {
        PLACEHOLDER = "true"
      }
    }
  }

  environment {
    variables = merge(
      {
        BRONZE_BUCKET        = var.bronze_bucket_name
        FIREHOSE_STREAM_NAME = var.firehose_delivery_stream_name
        ENVIRONMENT          = var.environment
      },
      var.lambda_environment_variables
    )
  }

  vpc_config {
    subnet_ids         = var.private_subnet_ids
    security_group_ids = [var.lambda_security_group_id]
  }

  tags = merge(var.tags, {
    Name     = "${var.name_prefix}-webhook-processor"
    Function = "webhook-processing"
  })
}

# ============================================================================
# Lambda Function: Data Enrichment
# ============================================================================

resource "aws_lambda_function" "data_enrichment" {
  count = var.create_data_enrichment ? 1 : 0

  function_name = "${var.name_prefix}-data-enrichment"
  role          = aws_iam_role.lambda_execution_role.arn
  handler       = "index.handler"
  runtime       = var.lambda_runtime
  timeout       = var.lambda_timeout
  memory_size   = var.lambda_memory_size

  # Placeholder code - replace with actual deployment package
  filename         = var.data_enrichment_zip_path != "" ? var.data_enrichment_zip_path : null
  source_code_hash = var.data_enrichment_zip_path != "" ? filebase64sha256(var.data_enrichment_zip_path) : null

  environment {
    variables = merge(
      {
        BRONZE_BUCKET = var.bronze_bucket_name
        SILVER_BUCKET = var.silver_bucket_name
        ENVIRONMENT   = var.environment
      },
      var.lambda_environment_variables
    )
  }

  vpc_config {
    subnet_ids         = var.private_subnet_ids
    security_group_ids = [var.lambda_security_group_id]
  }

  tags = merge(var.tags, {
    Name     = "${var.name_prefix}-data-enrichment"
    Function = "data-enrichment"
  })
}

# ============================================================================
# Lambda Function: API Polling
# ============================================================================

resource "aws_lambda_function" "api_polling" {
  count = var.create_api_polling ? 1 : 0

  function_name = "${var.name_prefix}-api-polling"
  role          = aws_iam_role.lambda_execution_role.arn
  handler       = "index.handler"
  runtime       = var.lambda_runtime
  timeout       = 300 # 5 minutes for API polling
  memory_size   = var.lambda_memory_size

  # Placeholder code - replace with actual deployment package
  filename         = var.api_polling_zip_path != "" ? var.api_polling_zip_path : null
  source_code_hash = var.api_polling_zip_path != "" ? filebase64sha256(var.api_polling_zip_path) : null

  environment {
    variables = merge(
      {
        BRONZE_BUCKET    = var.bronze_bucket_name
        JANIS_API_SECRET = "janis/api-credentials" # Secret Manager key
        ENVIRONMENT      = var.environment
      },
      var.lambda_environment_variables
    )
  }

  vpc_config {
    subnet_ids         = var.private_subnet_ids
    security_group_ids = [var.lambda_security_group_id]
  }

  tags = merge(var.tags, {
    Name     = "${var.name_prefix}-api-polling"
    Function = "api-polling"
  })
}

# ============================================================================
# CloudWatch Log Groups
# ============================================================================

resource "aws_cloudwatch_log_group" "webhook_processor" {
  count = var.create_webhook_processor ? 1 : 0

  name              = "/aws/lambda/${aws_lambda_function.webhook_processor[0].function_name}"
  retention_in_days = var.log_retention_days

  tags = var.tags
}

resource "aws_cloudwatch_log_group" "data_enrichment" {
  count = var.create_data_enrichment ? 1 : 0

  name              = "/aws/lambda/${aws_lambda_function.data_enrichment[0].function_name}"
  retention_in_days = var.log_retention_days

  tags = var.tags
}

resource "aws_cloudwatch_log_group" "api_polling" {
  count = var.create_api_polling ? 1 : 0

  name              = "/aws/lambda/${aws_lambda_function.api_polling[0].function_name}"
  retention_in_days = var.log_retention_days

  tags = var.tags
}

# ============================================================================
# Lambda Permissions for API Gateway (if needed)
# ============================================================================

resource "aws_lambda_permission" "api_gateway_webhook" {
  count = var.create_webhook_processor && var.api_gateway_execution_arn != "" ? 1 : 0

  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.webhook_processor[0].function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${var.api_gateway_execution_arn}/*/*"
}
