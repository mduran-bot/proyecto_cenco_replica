# ============================================================================
# S3 Module - Polling Staging Bucket
# ============================================================================
# This module creates an S3 bucket for temporary storage of polling data
# before it's processed by the ETL pipeline.
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
# S3 Bucket
# ============================================================================

resource "aws_s3_bucket" "polling_staging" {
  bucket = var.bucket_name

  tags = merge(var.tags, {
    Name      = var.bucket_name
    Purpose   = "API Polling Staging"
    ManagedBy = "terraform"
  })
}

# ============================================================================
# Bucket Versioning
# ============================================================================

resource "aws_s3_bucket_versioning" "polling_staging" {
  bucket = aws_s3_bucket.polling_staging.id

  versioning_configuration {
    status = var.enable_versioning ? "Enabled" : "Suspended"
  }
}

# ============================================================================
# Server-Side Encryption
# ============================================================================

resource "aws_s3_bucket_server_side_encryption_configuration" "polling_staging" {
  bucket = aws_s3_bucket.polling_staging.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = var.kms_key_arn != null ? "aws:kms" : "AES256"
      kms_master_key_id = var.kms_key_arn
    }
    bucket_key_enabled = var.kms_key_arn != null ? true : false
  }
}

# ============================================================================
# Public Access Block
# ============================================================================

resource "aws_s3_bucket_public_access_block" "polling_staging" {
  bucket = aws_s3_bucket.polling_staging.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# ============================================================================
# Lifecycle Configuration
# ============================================================================

resource "aws_s3_bucket_lifecycle_configuration" "polling_staging" {
  bucket = aws_s3_bucket.polling_staging.id

  rule {
    id     = "transition-old-data"
    status = "Enabled"

    filter {}

    # Transition to Intelligent Tiering after 30 days
    transition {
      days          = var.intelligent_tiering_days
      storage_class = "INTELLIGENT_TIERING"
    }

    # Transition to Glacier after 90 days
    transition {
      days          = var.glacier_transition_days
      storage_class = "GLACIER"
    }

    # Delete after retention period
    expiration {
      days = var.expiration_days
    }
  }

  # Rule for incomplete multipart uploads
  rule {
    id     = "abort-incomplete-multipart-uploads"
    status = "Enabled"

    filter {}

    abort_incomplete_multipart_upload {
      days_after_initiation = 7
    }
  }
}

# ============================================================================
# Bucket Logging (Optional)
# ============================================================================

resource "aws_s3_bucket_logging" "polling_staging" {
  count = var.logging_bucket_name != "" ? 1 : 0

  bucket = aws_s3_bucket.polling_staging.id

  target_bucket = var.logging_bucket_name
  target_prefix = "s3-access-logs/polling-staging/"
}

# ============================================================================
# Bucket Notification (Optional - for triggering Lambda/Glue)
# ============================================================================

resource "aws_s3_bucket_notification" "polling_staging" {
  count = length(var.lambda_notifications) > 0 || length(var.sqs_notifications) > 0 ? 1 : 0

  bucket = aws_s3_bucket.polling_staging.id

  dynamic "lambda_function" {
    for_each = var.lambda_notifications
    content {
      lambda_function_arn = lambda_function.value.function_arn
      events              = lambda_function.value.events
      filter_prefix       = lambda_function.value.filter_prefix
      filter_suffix       = lambda_function.value.filter_suffix
    }
  }

  dynamic "queue" {
    for_each = var.sqs_notifications
    content {
      queue_arn     = queue.value.queue_arn
      events        = queue.value.events
      filter_prefix = queue.value.filter_prefix
      filter_suffix = queue.value.filter_suffix
    }
  }
}
