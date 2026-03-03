# LocalStack Environment - Main Configuration

module "vpc" {
  source = "../../modules/vpc"

  environment          = var.environment
  project_name         = var.project_name
  vpc_cidr             = var.vpc_cidr
  availability_zones   = var.availability_zones
  public_subnet_cidrs  = var.public_subnet_cidrs
  private_subnet_cidrs = var.private_subnet_cidrs

  common_tags = {
    Environment = var.environment
    Project     = var.project_name
    Owner       = var.owner
    ManagedBy   = "terraform"
  }
}

module "security_groups" {
  source = "../../modules/security-groups"

  environment  = var.environment
  project_name = var.project_name
  vpc_id       = module.vpc.vpc_id
  vpc_cidr     = var.vpc_cidr

  common_tags = {
    Environment = var.environment
    Project     = var.project_name
    Owner       = var.owner
    ManagedBy   = "terraform"
  }
}

module "monitoring" {
  source = "../../modules/monitoring"

  environment  = var.environment
  project_name = var.project_name
  alarm_email  = var.alarm_email

  common_tags = {
    Environment = var.environment
    Project     = var.project_name
    Owner       = var.owner
    ManagedBy   = "terraform"
  }
}

module "eventbridge" {
  source = "../../modules/eventbridge"

  environment  = var.environment
  project_name = var.project_name

  common_tags = {
    Environment = var.environment
    Project     = var.project_name
    Owner       = var.owner
    ManagedBy   = "terraform"
  }
}
