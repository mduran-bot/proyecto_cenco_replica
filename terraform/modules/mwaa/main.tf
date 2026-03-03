# ============================================================================
# MWAA Module - Managed Apache Airflow
# Creates MWAA environment for workflow orchestration
# ============================================================================

# ============================================================================
# IAM Role for MWAA
# ============================================================================

resource "aws_iam_role" "mwaa_execution_role" {
  name = "${var.name_prefix}-mwaa-execution-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = [
            "airflow.amazonaws.com",
            "airflow-env.amazonaws.com"
          ]
        }
      }
    ]
  })

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-mwaa-execution-role"
  })
}

# ============================================================================
# IAM Policy for MWAA
# ============================================================================

resource "aws_iam_role_policy" "mwaa_execution_policy" {
  name = "${var.name_prefix}-mwaa-execution-policy"
  role = aws_iam_role.mwaa_execution_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = "airflow:PublishMetrics"
        Resource = "arn:aws:airflow:${var.aws_region}:*:environment/${var.name_prefix}-mwaa"
      },
      {
        Effect = "Allow"
        Action = [
          "s3:ListAllMyBuckets"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject*",
          "s3:GetBucket*",
          "s3:List*"
        ]
        Resource = [
          var.scripts_bucket_arn,
          "${var.scripts_bucket_arn}/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject*",
          "s3:PutObject*",
          "s3:DeleteObject*"
        ]
        Resource = [
          var.bronze_bucket_arn,
          "${var.bronze_bucket_arn}/*",
          var.silver_bucket_arn,
          "${var.silver_bucket_arn}/*",
          var.gold_bucket_arn,
          "${var.gold_bucket_arn}/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogStream",
          "logs:CreateLogGroup",
          "logs:PutLogEvents",
          "logs:GetLogEvents",
          "logs:GetLogRecord",
          "logs:GetLogGroupFields",
          "logs:GetQueryResults"
        ]
        Resource = "arn:aws:logs:${var.aws_region}:*:log-group:airflow-${var.name_prefix}-*"
      },
      {
        Effect = "Allow"
        Action = [
          "logs:DescribeLogGroups"
        ]
        Resource = "*"
      },
      {
        Effect   = "Allow"
        Action   = "cloudwatch:PutMetricData"
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "sqs:ChangeMessageVisibility",
          "sqs:DeleteMessage",
          "sqs:GetQueueAttributes",
          "sqs:GetQueueUrl",
          "sqs:ReceiveMessage",
          "sqs:SendMessage"
        ]
        Resource = "arn:aws:sqs:${var.aws_region}:*:airflow-celery-*"
      },
      {
        Effect = "Allow"
        Action = [
          "glue:StartJobRun",
          "glue:GetJobRun",
          "glue:GetJobRuns",
          "glue:BatchStopJobRun"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "lambda:InvokeFunction"
        ]
        Resource = var.lambda_function_arns
      }
    ]
  })
}

# ============================================================================
# MWAA Environment
# ============================================================================

resource "aws_mwaa_environment" "main" {
  count = var.create_mwaa_environment ? 1 : 0

  name              = "${var.name_prefix}-mwaa"
  airflow_version   = var.airflow_version
  environment_class = var.environment_class
  max_workers       = var.max_workers
  min_workers       = var.min_workers

  dag_s3_path          = "dags/"
  requirements_s3_path = var.requirements_s3_path
  plugins_s3_path      = var.plugins_s3_path

  source_bucket_arn  = var.scripts_bucket_arn
  execution_role_arn = aws_iam_role.mwaa_execution_role.arn

  network_configuration {
    security_group_ids = [var.mwaa_security_group_id]
    subnet_ids         = var.private_subnet_ids
  }

  logging_configuration {
    dag_processing_logs {
      enabled   = true
      log_level = var.dag_processing_log_level
    }

    scheduler_logs {
      enabled   = true
      log_level = var.scheduler_log_level
    }

    task_logs {
      enabled   = true
      log_level = var.task_log_level
    }

    webserver_logs {
      enabled   = true
      log_level = var.webserver_log_level
    }

    worker_logs {
      enabled   = true
      log_level = var.worker_log_level
    }
  }

  airflow_configuration_options = var.airflow_configuration_options

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-mwaa"
  })
}
