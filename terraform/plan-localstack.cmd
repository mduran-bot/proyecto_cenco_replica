@echo off
set AWS_ACCESS_KEY_ID=test
set AWS_SECRET_ACCESS_KEY=test
set AWS_DEFAULT_REGION=us-east-1

echo Generando plan de Terraform para LocalStack...
terraform plan -var-file=localstack.tfvars
