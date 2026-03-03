@echo off
REM Script para verificar el estado de LocalStack

echo ========================================
echo Verificando LocalStack
echo ========================================
echo.

echo [1/4] Estado del contenedor Docker:
docker ps --filter "name=localstack" --format "table {{.Names}}\t{{.Status}}"
echo.

echo [2/4] Servicios disponibles:
curl -s http://localhost:4566/_localstack/health
echo.
echo.

echo [3/4] VPCs existentes:
set AWS_ACCESS_KEY_ID=test
set AWS_SECRET_ACCESS_KEY=test
aws --endpoint-url=http://localhost:4566 ec2 describe-vpcs --region us-east-1 --query "Vpcs[*].[VpcId,CidrBlock,IsDefault]" --output table
echo.

echo [4/4] Subnets existentes:
aws --endpoint-url=http://localhost:4566 ec2 describe-subnets --region us-east-1 --query "Subnets[*].[SubnetId,CidrBlock,VpcId]" --output table
echo.

echo ========================================
echo Verificacion completada
echo ========================================
