@echo off
REM Script para desplegar la VPC en LocalStack

echo ========================================
echo Desplegando VPC en LocalStack
echo ========================================
echo.

REM Configurar credenciales dummy para LocalStack
set AWS_ACCESS_KEY_ID=test
set AWS_SECRET_ACCESS_KEY=test
set AWS_DEFAULT_REGION=us-east-1

REM Cambiar al directorio de Terraform
cd terraform

echo [Paso 1/4] Inicializando Terraform...
terraform init
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Terraform init fallo
    pause
    exit /b 1
)
echo.

echo [Paso 2/4] Validando configuracion...
terraform validate
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Terraform validate fallo
    pause
    exit /b 1
)
echo.

echo [Paso 3/4] Generando plan...
terraform plan -var-file="localstack.tfvars" -out=localstack.tfplan
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Terraform plan fallo
    pause
    exit /b 1
)
echo.

echo [Paso 4/4] Aplicando configuracion...
echo ATENCION: Esto creara recursos en LocalStack
pause
terraform apply localstack.tfplan
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Terraform apply fallo
    pause
    exit /b 1
)
echo.

echo ========================================
echo Deployment completado!
echo ========================================
echo.

echo Verificando recursos creados...
echo.

echo VPCs:
aws --endpoint-url=http://localhost:4566 ec2 describe-vpcs --region us-east-1 --query "Vpcs[*].[VpcId,CidrBlock,Tags[?Key=='Name'].Value|[0]]" --output table
echo.

echo Subnets:
aws --endpoint-url=http://localhost:4566 ec2 describe-subnets --region us-east-1 --query "Subnets[*].[SubnetId,CidrBlock,AvailabilityZone,Tags[?Key=='Name'].Value|[0]]" --output table
echo.

echo Security Groups:
aws --endpoint-url=http://localhost:4566 ec2 describe-security-groups --region us-east-1 --query "SecurityGroups[*].[GroupId,GroupName]" --output table
echo.

cd ..
pause
