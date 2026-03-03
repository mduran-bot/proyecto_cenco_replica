# ============================================================================
# AWS Glue Module - ETL Jobs
# Creates Glue catalog, databases, and job definitions
# ============================================================================

# ============================================================================
# IAM Role for Glue
# ============================================================================

resource "aws_iam_role" "glue_role" {
  name = "${var.name_prefix}-glue-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "glue.amazonaws.com"
        }
      }
    ]
  })

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-glue-role"
  })
}

# ============================================================================
# IAM Policy for Glue
# ============================================================================

resource "aws_iam_role_policy" "glue_policy" {
  name = "${var.name_prefix}-glue-policy"
  role = aws_iam_role.glue_role.id

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
        Resource = [
          var.bronze_bucket_arn,
          "${var.bronze_bucket_arn}/*",
          var.silver_bucket_arn,
          "${var.silver_bucket_arn}/*",
          var.gold_bucket_arn,
          "${var.gold_bucket_arn}/*",
          var.scripts_bucket_arn,
          "${var.scripts_bucket_arn}/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "glue:*",
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "ec2:CreateNetworkInterface",
          "ec2:DescribeNetworkInterfaces",
          "ec2:DeleteNetworkInterface",
          "ec2:DescribeVpcEndpoints",
          "ec2:DescribeSubnets",
          "ec2:DescribeVpcAttribute",
          "ec2:DescribeRouteTables",
          "ec2:DescribeSecurityGroups"
        ]
        Resource = "*"
      }
    ]
  })
}

# Attach AWS managed policy for Glue
resource "aws_iam_role_policy_attachment" "glue_service" {
  role       = aws_iam_role.glue_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSGlueServiceRole"
}

# ============================================================================
# Glue Catalog Database
# ============================================================================

resource "aws_glue_catalog_database" "bronze" {
  name        = "${replace(var.name_prefix, "-", "_")}_bronze"
  description = "Bronze layer - raw data from Janis"

  tags = merge(var.tags, {
    Layer = "bronze"
  })
}

resource "aws_glue_catalog_database" "silver" {
  name        = "${replace(var.name_prefix, "-", "_")}_silver"
  description = "Silver layer - cleaned and validated data"

  tags = merge(var.tags, {
    Layer = "silver"
  })
}

resource "aws_glue_catalog_database" "gold" {
  name        = "${replace(var.name_prefix, "-", "_")}_gold"
  description = "Gold layer - business-ready aggregated data"

  tags = merge(var.tags, {
    Layer = "gold"
  })
}

# ============================================================================
# Glue Job: Bronze to Silver
# ============================================================================

resource "aws_glue_job" "bronze_to_silver" {
  count = var.create_bronze_to_silver_job ? 1 : 0

  name     = "${var.name_prefix}-bronze-to-silver"
  role_arn = aws_iam_role.glue_role.arn

  command {
    name            = "glueetl"
    script_location = "s3://${var.scripts_bucket_name}/glue/bronze-to-silver/main.py"
    python_version  = "3"
  }

  default_arguments = {
    "--job-language"                     = "python"
    "--job-bookmark-option"              = "job-bookmark-enable"
    "--enable-metrics"                   = "true"
    "--enable-continuous-cloudwatch-log" = "true"
    "--enable-spark-ui"                  = "true"
    "--spark-event-logs-path"            = "s3://${var.scripts_bucket_name}/glue/spark-logs/"
    "--TempDir"                          = "s3://${var.scripts_bucket_name}/glue/temp/"
    "--bronze_database"                  = aws_glue_catalog_database.bronze.name
    "--silver_database"                  = aws_glue_catalog_database.silver.name
    "--bronze_bucket"                    = var.bronze_bucket_name
    "--silver_bucket"                    = var.silver_bucket_name
  }

  glue_version      = "4.0"
  max_retries       = 1
  timeout           = 60
  number_of_workers = var.glue_number_of_workers
  worker_type       = var.glue_worker_type

  execution_property {
    max_concurrent_runs = 3
  }

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-bronze-to-silver"
    Job  = "bronze-to-silver"
  })
}

# ============================================================================
# Glue Job: Silver to Gold
# ============================================================================

resource "aws_glue_job" "silver_to_gold" {
  count = var.create_silver_to_gold_job ? 1 : 0

  name     = "${var.name_prefix}-silver-to-gold"
  role_arn = aws_iam_role.glue_role.arn

  command {
    name            = "glueetl"
    script_location = "s3://${var.scripts_bucket_name}/glue/silver-to-gold/main.py"
    python_version  = "3"
  }

  default_arguments = {
    "--job-language"                     = "python"
    "--job-bookmark-option"              = "job-bookmark-enable"
    "--enable-metrics"                   = "true"
    "--enable-continuous-cloudwatch-log" = "true"
    "--enable-spark-ui"                  = "true"
    "--spark-event-logs-path"            = "s3://${var.scripts_bucket_name}/glue/spark-logs/"
    "--TempDir"                          = "s3://${var.scripts_bucket_name}/glue/temp/"
    "--silver_database"                  = aws_glue_catalog_database.silver.name
    "--gold_database"                    = aws_glue_catalog_database.gold.name
    "--silver_bucket"                    = var.silver_bucket_name
    "--gold_bucket"                      = var.gold_bucket_name
  }

  glue_version      = "4.0"
  max_retries       = 1
  timeout           = 60
  number_of_workers = var.glue_number_of_workers
  worker_type       = var.glue_worker_type

  execution_property {
    max_concurrent_runs = 3
  }

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-silver-to-gold"
    Job  = "silver-to-gold"
  })
}

# ============================================================================
# CloudWatch Log Groups for Glue Jobs
# ============================================================================

resource "aws_cloudwatch_log_group" "glue_bronze_to_silver" {
  count = var.create_bronze_to_silver_job ? 1 : 0

  name              = "/aws-glue/jobs/${aws_glue_job.bronze_to_silver[0].name}"
  retention_in_days = var.log_retention_days

  tags = var.tags
}

resource "aws_cloudwatch_log_group" "glue_silver_to_gold" {
  count = var.create_silver_to_gold_job ? 1 : 0

  name              = "/aws-glue/jobs/${aws_glue_job.silver_to_gold[0].name}"
  retention_in_days = var.log_retention_days

  tags = var.tags
}
