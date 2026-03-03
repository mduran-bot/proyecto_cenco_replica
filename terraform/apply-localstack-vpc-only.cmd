@echo off
set AWS_ACCESS_KEY_ID=test
set AWS_SECRET_ACCESS_KEY=test
set AWS_DEFAULT_REGION=us-east-1

echo Aplicando solo VPC y recursos base...
terraform apply -var-file=localstack.tfvars -target=module.vpc -target=module.security_groups -target=module.nacls -target=module.waf -target=module.eventbridge -target=aws_s3_bucket.test -auto-approve
