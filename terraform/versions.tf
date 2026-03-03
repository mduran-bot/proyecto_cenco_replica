terraform {
  required_version = ">= 1.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  # Backend configuration - Uncomment and configure for remote state
  # backend "s3" {
  #   bucket         = "cencosud-terraform-state"
  #   key            = "janis-cencosud/infrastructure/terraform.tfstate"
  #   region         = "us-east-1"
  #   encrypt        = true
  #   dynamodb_table = "terraform-state-lock"
  # }
}

provider "aws" {
  region = var.aws_region

  # Default tags applied to all resources
  default_tags {
    tags = merge(
      {
        Project     = var.project_name
        Environment = var.environment
        Owner       = var.owner
        CostCenter  = var.cost_center
        ManagedBy   = "terraform"
      },
      var.additional_tags
    )
  }
}
