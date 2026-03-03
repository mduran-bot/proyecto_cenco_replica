provider "aws" {
  region                      = "us-east-1"
  access_key                  = "test"
  secret_key                  = "test"
  skip_credentials_validation = true
  skip_metadata_api_check     = true
  skip_requesting_account_id  = true
  s3_use_path_style           = true

  endpoints {
    s3   = "http://localhost:4566"
    glue = "http://localhost:4566"
    iam  = "http://localhost:4566"
  }
}
# Buckets para el pipeline de datos
resource "aws_s3_bucket" "bronze_layer" {
  bucket = "data-lake-bronze"
}

resource "aws_s3_bucket" "silver_layer" {
  bucket = "data-lake-silver"
}

# Bucket para guardar los scripts de Glue
resource "aws_s3_bucket" "glue_scripts" {
  bucket = "glue-scripts-bin"
}

# Bucket Gold
resource "aws_s3_bucket" "gold" {
  bucket = "data-lake-gold"
}

resource "aws_s3_bucket" "metadata" {
  bucket        = "data-lake-metadata"
  force_destroy = true
}

resource "aws_s3_bucket" "dlq" {
  bucket        = "data-lake-dlq"
  force_destroy = true
}
