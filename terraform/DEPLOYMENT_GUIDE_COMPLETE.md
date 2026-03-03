# Guía Completa de Deployment - Infraestructura Janis-Cencosud

**Fecha**: 2026-02-04  
**Estado**: ✅ Listo para deployment

## Resumen Ejecutivo

La infraestructura Terraform está completamente integrada con todos los módulos del data pipeline. Esta guía te llevará paso a paso desde la validación hasta el deployment completo.

## Arquitectura Desplegada

### Componentes Habilitados en Testing
- ✅ VPC con subnets públicas y privadas
- ✅ Security Groups para todos los servicios
- ✅ NAT Gateway para conectividad saliente
- ✅ S3 Data Lake (Bronze, Silver, Gold, Scripts, Logs)
- ✅ Kinesis Firehose para ingesta en tiempo real
- ✅ EventBridge para scheduling
- ✅ CloudWatch para monitoreo

### Componentes Deshabilitados (Sin Código)
- ❌ Lambda Functions (requieren código Python)
- ❌ API Gateway (depende de Lambda)
- ❌ Glue Jobs (requieren scripts PySpark)
- ❌ MWAA (costoso, no necesario para testing inicial)

## Pre-requisitos

### 1. Software Requerido
```powershell
# Verificar Terraform
terraform version
# Requerido: >= 1.0

# Verificar AWS CLI
aws --version
# Requerido: >= 2.0

# Verificar PowerShell
$PSVersionTable.PSVersion
# Requerido: >= 5.1
```

### 2. Credenciales AWS
```powershell
# Configurar credenciales (si no están configuradas)
aws configure

# O usar variables de entorno
$env:AWS_ACCESS_KEY_ID = "tu-access-key"
$env:AWS_SECRET_ACCESS_KEY = "tu-secret-key"
$env:AWS_SESSION_TOKEN = "tu-session-token"  # Si usas STS

# Verificar credenciales
aws sts get-caller-identity
```

### 3. Permisos Requeridos
Tu usuario/rol AWS debe tener permisos para crear:
- VPC, Subnets, Route Tables, Internet Gateway, NAT Gateway
- Security Groups, Network ACLs
- S3 Buckets y Bucket Policies
- Kinesis Firehose Delivery Streams
- IAM Roles y Policies
- CloudWatch Log Groups y Alarms
- EventBridge Event Bus y Rules
- VPC Endpoints (si habilitados)

## Paso 1: Validación Pre-Deployment

### 1.1 Ejecutar Script de Validación
```powershell
cd terraform
.\validate-integration.ps1
```

Este script verifica:
- ✓ Estructura de directorios completa
- ✓ Archivos principales presentes
- ✓ Módulos con archivos requeridos
- ✓ Variables definidas en tfvars
- ✓ Sintaxis de Terraform válida
- ✓ Módulos declarados en main.tf
- ✓ Outputs definidos en outputs.tf
- ✓ Configuración de testing optimizada

### 1.2 Revisar Configuración
```powershell
# Ver configuración de testing
Get-Content terraform.tfvars.testing

# Verificar variables críticas
# - aws_account_id: Debe ser tu cuenta AWS
# - cost_center: Debe ser tu cost center
# - existing_redshift_sg_id: Debe ser un SG válido (o dummy para testing)
```

### 1.3 Formatear Código
```powershell
terraform fmt -recursive
```

## Paso 2: Inicialización de Terraform

### 2.1 Inicializar Backend Local
```powershell
terraform init
```

Esto descargará:
- AWS Provider (~200 MB)
- Módulos locales

**Tiempo estimado**: 2-5 minutos

### 2.2 Verificar Inicialización
```powershell
# Verificar providers instalados
terraform providers

# Verificar módulos
terraform get
```

## Paso 3: Planificación del Deployment

### 3.1 Crear Plan de Ejecución
```powershell
terraform plan -var-file="terraform.tfvars.testing" -out=testing.tfplan
```

**Tiempo estimado**: 1-2 minutos

### 3.2 Revisar Plan
```powershell
# Ver plan en formato legible
terraform show testing.tfplan

# Ver solo recursos a crear
terraform show -json testing.tfplan | ConvertFrom-Json | Select-Object -ExpandProperty planned_values
```

### 3.3 Verificar Recursos Esperados

El plan debe mostrar la creación de aproximadamente:
- **VPC**: 1 VPC, 3 subnets, 1 IGW, 1 NAT Gateway, 3 route tables
- **Security Groups**: 7 security groups
- **S3**: 5 buckets (bronze, silver, gold, scripts, logs)
- **Kinesis Firehose**: 1 delivery stream
- **IAM**: 2-3 roles (Firehose, Lambda, Glue)
- **CloudWatch**: 2-3 log groups
- **EventBridge**: 1 event bus, 5 scheduled rules

**Total esperado**: ~30-40 recursos

### 3.4 Verificar Costos Estimados

Recursos que generan costos:
- **NAT Gateway**: ~$32/mes + $0.045/GB transferido
- **S3 Storage**: ~$0.023/GB/mes (Standard)
- **Kinesis Firehose**: ~$0.029/GB ingested
- **CloudWatch Logs**: ~$0.50/GB ingested
- **EventBridge**: ~$1/millón de eventos

**Costo mensual estimado**: $35-50/mes (sin datos)

## Paso 4: Aplicar Cambios

### 4.1 Backup del Estado Actual (si existe)
```powershell
# Si ya tienes un state file
if (Test-Path "terraform.tfstate") {
    Copy-Item "terraform.tfstate" "terraform.tfstate.backup.$(Get-Date -Format 'yyyyMMdd-HHmmss')"
}
```

### 4.2 Aplicar Plan
```powershell
terraform apply testing.tfplan
```

**Tiempo estimado**: 5-10 minutos

El deployment creará recursos en este orden:
1. VPC y subnets (1-2 min)
2. Internet Gateway y Route Tables (30 seg)
3. NAT Gateway (2-3 min) ⏱️ El más lento
4. Security Groups (30 seg)
5. S3 Buckets (1 min)
6. IAM Roles (30 seg)
7. Kinesis Firehose (1 min)
8. CloudWatch y EventBridge (1 min)

### 4.3 Monitorear Progreso
```powershell
# En otra terminal, monitorear recursos creados
aws ec2 describe-vpcs --filters "Name=tag:Application,Values=janis-cencosud-integration"
aws s3 ls | findstr janis-cencosud
aws firehose list-delivery-streams
```

## Paso 5: Verificación Post-Deployment

### 5.1 Verificar Outputs
```powershell
# Ver todos los outputs
terraform output

# Ver outputs específicos
terraform output vpc_id
terraform output bronze_bucket_name
terraform output firehose_orders_stream_name
```

### 5.2 Verificar Recursos en AWS Console

#### VPC
```powershell
# Obtener VPC ID
$VPC_ID = terraform output -raw vpc_id

# Ver detalles de VPC
aws ec2 describe-vpcs --vpc-ids $VPC_ID
```

#### S3 Buckets
```powershell
# Listar buckets creados
aws s3 ls | findstr janis-cencosud

# Verificar configuración de un bucket
$BRONZE_BUCKET = terraform output -raw bronze_bucket_name
aws s3api get-bucket-versioning --bucket $BRONZE_BUCKET
aws s3api get-bucket-encryption --bucket $BRONZE_BUCKET
aws s3api get-bucket-lifecycle-configuration --bucket $BRONZE_BUCKET
```

#### Kinesis Firehose
```powershell
# Describir delivery stream
$STREAM_NAME = terraform output -raw firehose_orders_stream_name
aws firehose describe-delivery-stream --delivery-stream-name $STREAM_NAME
```

#### Security Groups
```powershell
# Listar security groups
aws ec2 describe-security-groups --filters "Name=vpc-id,Values=$VPC_ID"
```

### 5.3 Verificar Conectividad

#### NAT Gateway
```powershell
# Verificar que NAT Gateway tiene IP pública
$NAT_IP = terraform output -raw nat_gateway_public_ip
Write-Host "NAT Gateway IP: $NAT_IP"

# Verificar que está activo
aws ec2 describe-nat-gateways --filter "Name=vpc-id,Values=$VPC_ID"
```

#### VPC Flow Logs (si habilitado)
```powershell
# Verificar flow logs
aws ec2 describe-flow-logs --filter "Name=resource-id,Values=$VPC_ID"
```

### 5.4 Probar Kinesis Firehose

```powershell
# Enviar datos de prueba
$STREAM_NAME = terraform output -raw firehose_orders_stream_name

$TestData = @{
    event_type = "order.created"
    entity_id = "test-order-001"
    timestamp = (Get-Date).ToString("o")
    data = @{
        order_id = "test-order-001"
        status = "pending"
    }
} | ConvertTo-Json

# Enviar a Firehose
aws firehose put-record `
    --delivery-stream-name $STREAM_NAME `
    --record "Data=$([Convert]::ToBase64String([System.Text.Encoding]::UTF8.GetBytes($TestData)))"

# Esperar 5 minutos y verificar en S3
Start-Sleep -Seconds 300

$BRONZE_BUCKET = terraform output -raw bronze_bucket_name
aws s3 ls "s3://$BRONZE_BUCKET/orders/" --recursive
```

## Paso 6: Troubleshooting

### Error: "Error creating NAT Gateway: timeout"
**Causa**: NAT Gateway tarda 2-3 minutos en crearse  
**Solución**: Esperar y reintentar
```powershell
terraform apply testing.tfplan
```

### Error: "BucketAlreadyExists"
**Causa**: Nombre de bucket ya existe globalmente  
**Solución**: Cambiar `project_name` en tfvars
```hcl
project_name = "janis-cencosud-integration-tu-nombre"
```

### Error: "UnauthorizedOperation"
**Causa**: Credenciales AWS sin permisos suficientes  
**Solución**: Verificar permisos IAM
```powershell
aws sts get-caller-identity
aws iam get-user
```

### Error: "InvalidParameterValue: Security group not found"
**Causa**: `existing_redshift_sg_id` no existe  
**Solución**: Usar un SG dummy para testing
```hcl
existing_redshift_sg_id = "sg-00000000"  # Dummy para testing
```

### Warning: "Terraform state lock"
**Causa**: Otro proceso tiene el state bloqueado  
**Solución**: Esperar o forzar unlock
```powershell
terraform force-unlock <LOCK_ID>
```

## Paso 7: Limpieza (Opcional)

### 7.1 Destruir Infraestructura
```powershell
# CUIDADO: Esto eliminará TODOS los recursos
terraform destroy -var-file="terraform.tfvars.testing"
```

### 7.2 Destrucción Selectiva
```powershell
# Eliminar solo un recurso específico
terraform destroy -target=module.kinesis_firehose -var-file="terraform.tfvars.testing"
```

### 7.3 Verificar Limpieza
```powershell
# Verificar que no quedan recursos
aws ec2 describe-vpcs --filters "Name=tag:Application,Values=janis-cencosud-integration"
aws s3 ls | findstr janis-cencosud
```

## Paso 8: Próximos Pasos

### 8.1 Habilitar Lambda Functions

1. **Crear código Lambda**:
```python
# lambda/webhook-processor/lambda_function.py
import json
import boto3

def lambda_handler(event, context):
    print(f"Received event: {json.dumps(event)}")
    # Procesar webhook
    return {
        'statusCode': 200,
        'body': json.dumps({'message': 'Webhook processed'})
    }
```

2. **Empaquetar código**:
```powershell
cd lambda/webhook-processor
Compress-Archive -Path * -DestinationPath webhook-processor.zip
```

3. **Subir a S3**:
```powershell
$SCRIPTS_BUCKET = terraform output -raw scripts_bucket_name
aws s3 cp webhook-processor.zip "s3://$SCRIPTS_BUCKET/lambda/webhook-processor.zip"
```

4. **Habilitar en tfvars**:
```hcl
create_lambda_webhook_processor = true
```

5. **Aplicar cambios**:
```powershell
terraform apply -var-file="terraform.tfvars.testing"
```

### 8.2 Habilitar API Gateway

1. Verificar que Lambda webhook-processor funciona
2. Cambiar flag en tfvars:
```hcl
create_api_gateway = true
```
3. Aplicar cambios
4. Probar endpoint:
```powershell
$API_URL = terraform output -raw api_gateway_webhook_endpoint_url
Invoke-RestMethod -Uri "$API_URL/orders" -Method POST -Body '{"test": "data"}' -ContentType "application/json"
```

### 8.3 Habilitar Glue Jobs

1. Crear scripts PySpark
2. Subir a S3 scripts bucket
3. Habilitar en tfvars:
```hcl
create_glue_bronze_to_silver_job = true
create_glue_silver_to_gold_job = true
```
4. Aplicar cambios
5. Ejecutar job manualmente:
```powershell
$JOB_NAME = terraform output -raw glue_bronze_to_silver_job_name
aws glue start-job-run --job-name $JOB_NAME
```

### 8.4 Habilitar MWAA

1. Crear DAGs de Airflow
2. Subir a S3 scripts bucket (carpeta dags/)
3. Habilitar en tfvars:
```hcl
create_mwaa_environment = true
```
4. Aplicar cambios (tarda ~30 minutos)
5. Acceder a Airflow UI:
```powershell
$MWAA_URL = terraform output -raw mwaa_webserver_url
Start-Process $MWAA_URL
```

## Checklist de Deployment

- [ ] Pre-requisitos verificados (Terraform, AWS CLI, credenciales)
- [ ] Script de validación ejecutado sin errores
- [ ] Configuración de testing revisada
- [ ] `terraform init` ejecutado exitosamente
- [ ] `terraform plan` revisado y aprobado
- [ ] Costos estimados aceptables
- [ ] `terraform apply` ejecutado exitosamente
- [ ] Outputs verificados
- [ ] Recursos verificados en AWS Console
- [ ] Kinesis Firehose probado con datos de prueba
- [ ] Documentación actualizada

## Recursos Adicionales

- [Terraform AWS Provider Docs](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)
- [AWS VPC Best Practices](https://docs.aws.amazon.com/vpc/latest/userguide/vpc-best-practices.html)
- [Kinesis Firehose Developer Guide](https://docs.aws.amazon.com/firehose/latest/dev/what-is-this-service.html)
- [S3 Lifecycle Policies](https://docs.aws.amazon.com/AmazonS3/latest/userguide/object-lifecycle-mgmt.html)

## Soporte

Para problemas o preguntas:
1. Revisar logs de Terraform: `terraform.log`
2. Revisar CloudWatch Logs en AWS Console
3. Consultar documentación de módulos en `terraform/modules/*/README.md`
4. Revisar `Documentación Cenco/` para detalles de arquitectura

---

**¡Éxito con el deployment!** 🚀
