# ============================================================================
# S3 Module - Data Lake Buckets
# Creates Bronze, Silver, and Gold layer buckets with proper security
# ============================================================================

# ============================================================================
# Bronze Layer Bucket - Raw Data
# ============================================================================

resource "aws_s3_bucket" "bronze" {
  bucket = "${var.name_prefix}-datalake-bronze"

  tags = merge(var.tags, {
    Name        = "${var.name_prefix}-datalake-bronze"
    Layer       = "bronze"
    Description = "Raw data from Janis API and webhooks"
  })
}

resource "aws_s3_bucket_versioning" "bronze" {
  bucket = aws_s3_bucket.bronze.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "bronze" {
  bucket = aws_s3_bucket.bronze.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "bronze" {
  bucket = aws_s3_bucket.bronze.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_lifecycle_configuration" "bronze" {
  bucket = aws_s3_bucket.bronze.id

  rule {
    id     = "transition-to-glacier"
    status = "Enabled"

    transition {
      days          = var.bronze_glacier_transition_days
      storage_class = "GLACIER"
    }

    expiration {
      days = var.bronze_expiration_days
    }
  }
}

# ============================================================================
# Silver Layer Bucket - Cleaned and Validated Data
# ============================================================================

resource "aws_s3_bucket" "silver" {
  bucket = "${var.name_prefix}-datalake-silver"

  tags = merge(var.tags, {
    Name        = "${var.name_prefix}-datalake-silver"
    Layer       = "silver"
    Description = "Cleaned and validated data"
  })
}

resource "aws_s3_bucket_versioning" "silver" {
  bucket = aws_s3_bucket.silver.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "silver" {
  bucket = aws_s3_bucket.silver.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "silver" {
  bucket = aws_s3_bucket.silver.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_lifecycle_configuration" "silver" {
  bucket = aws_s3_bucket.silver.id

  rule {
    id     = "transition-to-glacier"
    status = "Enabled"

    transition {
      days          = var.silver_glacier_transition_days
      storage_class = "GLACIER"
    }

    expiration {
      days = var.silver_expiration_days
    }
  }
}

# ============================================================================
# Gold Layer Bucket - Business-Ready Data
# ============================================================================

resource "aws_s3_bucket" "gold" {
  bucket = "${var.name_prefix}-datalake-gold"

  tags = merge(var.tags, {
    Name        = "${var.name_prefix}-datalake-gold"
    Layer       = "gold"
    Description = "Business-ready aggregated data"
  })
}

resource "aws_s3_bucket_versioning" "gold" {
  bucket = aws_s3_bucket.gold.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "gold" {
  bucket = aws_s3_bucket.gold.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "gold" {
  bucket = aws_s3_bucket.gold.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_lifecycle_configuration" "gold" {
  bucket = aws_s3_bucket.gold.id

  rule {
    id     = "intelligent-tiering"
    status = "Enabled"

    transition {
      days          = var.gold_intelligent_tiering_days
      storage_class = "INTELLIGENT_TIERING"
    }
  }
}

# ============================================================================
# Scripts Bucket - Lambda code, Glue scripts, MWAA DAGs
# ============================================================================

resource "aws_s3_bucket" "scripts" {
  bucket = "${var.name_prefix}-scripts"

  tags = merge(var.tags, {
    Name    = "${var.name_prefix}-scripts"
    Purpose = "scripts"
    Content = "lambda-glue-mwaa"
  })
}

resource "aws_s3_bucket_versioning" "scripts" {
  bucket = aws_s3_bucket.scripts.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "scripts" {
  bucket = aws_s3_bucket.scripts.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "scripts" {
  bucket = aws_s3_bucket.scripts.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# ============================================================================
# Logs Bucket - Access logs and application logs
# ============================================================================

resource "aws_s3_bucket" "logs" {
  bucket = "${var.name_prefix}-logs"

  tags = merge(var.tags, {
    Name        = "${var.name_prefix}-logs"
    Purpose     = "logs"
    Description = "S3 access logs and application logs"
  })
}

resource "aws_s3_bucket_versioning" "logs" {
  bucket = aws_s3_bucket.logs.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "logs" {
  bucket = aws_s3_bucket.logs.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "logs" {
  bucket = aws_s3_bucket.logs.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_lifecycle_configuration" "logs" {
  bucket = aws_s3_bucket.logs.id

  rule {
    id     = "expire-old-logs"
    status = "Enabled"

    transition {
      days          = 30
      storage_class = "STANDARD_IA"
    }

    transition {
      days          = 60
      storage_class = "GLACIER"
    }

    expiration {
      days = var.logs_expiration_days
    }
  }
}

# ============================================================================
# Enable S3 Access Logging for Data Lake Buckets
# ============================================================================

resource "aws_s3_bucket_logging" "bronze" {
  bucket = aws_s3_bucket.bronze.id

  target_bucket = aws_s3_bucket.logs.id
  target_prefix = "s3-access-logs/bronze/"
}

resource "aws_s3_bucket_logging" "silver" {
  bucket = aws_s3_bucket.silver.id

  target_bucket = aws_s3_bucket.logs.id
  target_prefix = "s3-access-logs/silver/"
}

resource "aws_s3_bucket_logging" "gold" {
  bucket = aws_s3_bucket.gold.id

  target_bucket = aws_s3_bucket.logs.id
  target_prefix = "s3-access-logs/gold/"
}

resource "aws_s3_bucket_logging" "scripts" {
  bucket = aws_s3_bucket.scripts.id

  target_bucket = aws_s3_bucket.logs.id
  target_prefix = "s3-access-logs/scripts/"
}
