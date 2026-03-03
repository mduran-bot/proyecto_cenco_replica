# ============================================================================
# MWAA Module - Managed Apache Airflow
# ============================================================================

# S3 Bucket for MWAA DAGs
resource "aws_s3_bucket" "mwaa" {
  bucket = "${var.name_prefix}-mwaa-dags"
  
  tags = merge(var.tags, {
    Name      = "${var.name_prefix}-mwaa-dags"
    Component = "mwaa-storage"
  })
}

resource "aws_s3_bucket_versioning" "mwaa" {
  bucket = aws_s3_bucket.mwaa.id
  
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_public_access_block" "mwaa" {
  bucket = aws_s3_bucket.mwaa.id
  
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Security Group for MWAA
resource "aws_security_group" "mwaa" {
  name        = "${var.name_prefix}-mwaa-sg"
  description = "Security group for MWAA environment"
  vpc_id      = var.vpc_id
  
  # Self-referencing rule for internal communication
  ingress {
    from_port = 0
    to_port   = 0
    protocol  = "-1"
    self      = true
    description = "Allow all traffic within security group"
  }
  
  # Outbound to internet (for pip installs, API calls, etc.)
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
    description = "Allow all outbound traffic"
  }
  
  tags = merge(var.tags, {
    Name = "${var.name_prefix}-mwaa-sg"
  })
}

# ============================================================================
# MWAA Environment
# ============================================================================

resource "aws_mwaa_environment" "this" {
  name = "${var.name_prefix}-mwaa-environment"
  
  # Airflow Configuration
  airflow_version   = var.airflow_version
  environment_class = var.environment_class
  
  # Networking
  network_configuration {
    security_group_ids = [aws_security_group.mwaa.id]
    subnet_ids         = var.private_subnet_ids
  }
  
  # S3 Configuration
  source_bucket_arn    = aws_s3_bucket.mwaa.arn
  dag_s3_path          = "dags/"
  plugins_s3_path      = "plugins/"
  requirements_s3_path = "requirements.txt"
  
  # IAM Role (EXISTENTE - proporcionado externamente)
  execution_role_arn = var.execution_role_arn
  
  # Logging Configuration
  logging_configuration {
    dag_processing_logs {
      enabled   = true
      log_level = "INFO"
    }
    
    scheduler_logs {
      enabled   = true
      log_level = "INFO"
    }
    
    task_logs {
      enabled   = true
      log_level = "INFO"
    }
    
    webserver_logs {
      enabled   = true
      log_level = "INFO"
    }
    
    worker_logs {
      enabled   = true
      log_level = "INFO"
    }
  }
  
  # Auto-scaling
  max_workers = var.max_workers
  min_workers = var.min_workers
  
  # Web server access mode
  webserver_access_mode = "PUBLIC_ONLY"
  
  tags = var.tags
}
