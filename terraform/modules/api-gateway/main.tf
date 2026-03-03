# ============================================================================
# API Gateway Module - REST API for Webhooks
# Creates API Gateway REST API with Lambda integration
# ============================================================================

# ============================================================================
# REST API
# ============================================================================

resource "aws_api_gateway_rest_api" "webhooks" {
  name        = "${var.name_prefix}-webhooks-api"
  description = "API Gateway for Janis webhooks"

  endpoint_configuration {
    types = ["REGIONAL"]
  }

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-webhooks-api"
  })
}

# ============================================================================
# API Gateway Resources and Methods
# ============================================================================

# /webhooks resource
resource "aws_api_gateway_resource" "webhooks" {
  rest_api_id = aws_api_gateway_rest_api.webhooks.id
  parent_id   = aws_api_gateway_rest_api.webhooks.root_resource_id
  path_part   = "webhooks"
}

# /webhooks/{entity} resource
resource "aws_api_gateway_resource" "entity" {
  rest_api_id = aws_api_gateway_rest_api.webhooks.id
  parent_id   = aws_api_gateway_resource.webhooks.id
  path_part   = "{entity}"
}

# POST /webhooks/{entity}
resource "aws_api_gateway_method" "post_webhook" {
  rest_api_id   = aws_api_gateway_rest_api.webhooks.id
  resource_id   = aws_api_gateway_resource.entity.id
  http_method   = "POST"
  authorization = "NONE" # Consider using API Key or IAM auth in production

  request_parameters = {
    "method.request.path.entity" = true
  }
}

# Lambda Integration
resource "aws_api_gateway_integration" "lambda" {
  rest_api_id = aws_api_gateway_rest_api.webhooks.id
  resource_id = aws_api_gateway_resource.entity.id
  http_method = aws_api_gateway_method.post_webhook.http_method

  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = var.webhook_processor_invoke_arn
}

# ============================================================================
# API Gateway Deployment
# ============================================================================

resource "aws_api_gateway_deployment" "main" {
  depends_on = [
    aws_api_gateway_integration.lambda
  ]

  rest_api_id = aws_api_gateway_rest_api.webhooks.id

  triggers = {
    redeployment = sha1(jsonencode([
      aws_api_gateway_resource.webhooks.id,
      aws_api_gateway_resource.entity.id,
      aws_api_gateway_method.post_webhook.id,
      aws_api_gateway_integration.lambda.id,
    ]))
  }

  lifecycle {
    create_before_destroy = true
  }
}

# ============================================================================
# API Gateway Stage
# ============================================================================

resource "aws_api_gateway_stage" "main" {
  deployment_id = aws_api_gateway_deployment.main.id
  rest_api_id   = aws_api_gateway_rest_api.webhooks.id
  stage_name    = var.environment

  access_log_settings {
    destination_arn = aws_cloudwatch_log_group.api_gateway.arn
    format = jsonencode({
      requestId      = "$context.requestId"
      ip             = "$context.identity.sourceIp"
      caller         = "$context.identity.caller"
      user           = "$context.identity.user"
      requestTime    = "$context.requestTime"
      httpMethod     = "$context.httpMethod"
      resourcePath   = "$context.resourcePath"
      status         = "$context.status"
      protocol       = "$context.protocol"
      responseLength = "$context.responseLength"
    })
  }

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-api-stage-${var.environment}"
  })
}

# ============================================================================
# CloudWatch Log Group for API Gateway
# ============================================================================

resource "aws_cloudwatch_log_group" "api_gateway" {
  name              = "/aws/apigateway/${var.name_prefix}-webhooks"
  retention_in_days = var.log_retention_days

  tags = var.tags
}

# ============================================================================
# API Gateway Account (for CloudWatch Logs)
# ============================================================================

resource "aws_api_gateway_account" "main" {
  cloudwatch_role_arn = aws_iam_role.api_gateway_cloudwatch.arn
}

resource "aws_iam_role" "api_gateway_cloudwatch" {
  name = "${var.name_prefix}-api-gateway-cloudwatch-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "apigateway.amazonaws.com"
        }
      }
    ]
  })

  tags = var.tags
}

resource "aws_iam_role_policy_attachment" "api_gateway_cloudwatch" {
  role       = aws_iam_role.api_gateway_cloudwatch.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonAPIGatewayPushToCloudWatchLogs"
}

# ============================================================================
# Usage Plan and API Key (Optional)
# ============================================================================

resource "aws_api_gateway_usage_plan" "main" {
  count = var.create_usage_plan ? 1 : 0

  name = "${var.name_prefix}-usage-plan"

  api_stages {
    api_id = aws_api_gateway_rest_api.webhooks.id
    stage  = aws_api_gateway_stage.main.stage_name
  }

  quota_settings {
    limit  = var.quota_limit
    period = "DAY"
  }

  throttle_settings {
    burst_limit = var.throttle_burst_limit
    rate_limit  = var.throttle_rate_limit
  }

  tags = var.tags
}

resource "aws_api_gateway_api_key" "main" {
  count = var.create_api_key ? 1 : 0

  name = "${var.name_prefix}-api-key"

  tags = var.tags
}

resource "aws_api_gateway_usage_plan_key" "main" {
  count = var.create_usage_plan && var.create_api_key ? 1 : 0

  key_id        = aws_api_gateway_api_key.main[0].id
  key_type      = "API_KEY"
  usage_plan_id = aws_api_gateway_usage_plan.main[0].id
}
