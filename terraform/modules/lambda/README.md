# Lambda Module - Serverless Functions

Este módulo crea las funciones Lambda necesarias para la plataforma de integración Janis-Cencosud, implementando procesamiento serverless para webhooks, enriquecimiento de datos y polling de APIs.

## Arquitectura de Lambda Functions

### Funciones Creadas

El módulo puede crear hasta 3 funciones Lambda especializadas:

1. **Webhook Processor** - Procesamiento en tiempo real de webhooks
2. **Data Enrichment** - Enriquecimiento y validación de datos
3. **API Polling** - Polling periódico de la API de Janis

Cada función es opcional y se controla mediante variables de configuración.

## Funciones Lambda

### 1. Webhook Processor

**Propósito**: Procesar webhooks de Janis en tiempo real

**Características**:
- Runtime: Python 3.11 (configurable)
- Timeout: 30 segundos (configurable)
- Memory: 512 MB (configurable)
- VPC: Desplegada en subnets privadas
- Trigger: API Gateway

**Flujo de Datos**:
```
Janis WMS → API Gateway → Lambda (Webhook Processor) → Kinesis Firehose → S3 Bronze
```

**Variables de Entorno**:
- `BRONZE_BUCKET`: Nombre del bucket Bronze para datos crudos
- `FIREHOSE_STREAM_NAME`: Nombre del stream de Kinesis Firehose
- `ENVIRONMENT`: Ambiente de deployment (dev/staging/prod)

**Permisos IAM**:
- CloudWatch Logs: Crear y escribir logs
- S3: Leer/escribir en buckets Bronze y Scripts
- Kinesis Firehose: Enviar registros al stream
- Secrets Manager: Leer credenciales de Janis
- VPC: Crear/gestionar ENIs

**Integración**:
- Recibe eventos desde API Gateway
- Valida esquema JSON del webhook
- Enriquece datos con metadata
- Envía a Kinesis Firehose para buffering
- Escribe directamente a S3 Bronze si es necesario

### 2. Data Enrichment

**Propósito**: Enriquecer y validar datos antes de escribir a Silver layer

**Características**:
- Runtime: Python 3.11 (configurable)
- Timeout: 30 segundos (configurable)
- Memory: 512 MB (configurable)
- VPC: Desplegada en subnets privadas
- Trigger: S3 Event Notifications o Step Functions

**Flujo de Datos**:
```
S3 Bronze → Lambda (Data Enrichment) → S3 Silver
```

**Variables de Entorno**:
- `BRONZE_BUCKET`: Bucket de origen (Bronze)
- `SILVER_BUCKET`: Bucket de destino (Silver)
- `ENVIRONMENT`: Ambiente de deployment

**Permisos IAM**:
- CloudWatch Logs: Crear y escribir logs
- S3: Leer de Bronze, escribir a Silver
- Secrets Manager: Leer credenciales si es necesario
- VPC: Crear/gestionar ENIs

**Funcionalidades**:
- Validación de esquemas de datos
- Normalización de formatos
- Enriquecimiento con datos de referencia
- Deduplicación de registros
- Manejo de errores y reintentos

### 3. API Polling

**Propósito**: Polling periódico de la API de Janis como red de seguridad

**Características**:
- Runtime: Python 3.11 (configurable)
- Timeout: 300 segundos (5 minutos)
- Memory: 512 MB (configurable)
- VPC: Desplegada en subnets privadas
- Trigger: MWAA (Apache Airflow) vía EventBridge

**Flujo de Datos**:
```
EventBridge → MWAA → Lambda (API Polling) → S3 Bronze
```

**Variables de Entorno**:
- `BRONZE_BUCKET`: Bucket de destino (Bronze)
- `JANIS_API_SECRET`: Clave de Secrets Manager para credenciales
- `ENVIRONMENT`: Ambiente de deployment

**Permisos IAM**:
- CloudWatch Logs: Crear y escribir logs
- S3: Escribir en bucket Bronze
- Secrets Manager: Leer credenciales de API de Janis
- VPC: Crear/gestionar ENIs

**Funcionalidades**:
- Autenticación con API de Janis
- Paginación de resultados
- Manejo de rate limiting
- Escritura incremental a S3
- Reconciliación con datos de webhooks

## Uso

### Configuración Básica

```hcl
module "lambda" {
  source = "./modules/lambda"

  # General Configuration
  name_prefix = "janis-cencosud-dev"
  environment = "dev"

  # Network Configuration
  private_subnet_ids       = module.vpc.private_subnet_ids
  lambda_security_group_id = module.security_groups.sg_lambda_id

  # S3 Buckets
  bronze_bucket_name = module.s3.bronze_bucket_id
  bronze_bucket_arn  = module.s3.bronze_bucket_arn
  silver_bucket_name = module.s3.silver_bucket_id
  scripts_bucket_arn = module.s3.scripts_bucket_arn

  # Kinesis Firehose (opcional)
  firehose_delivery_stream_name = module.kinesis_firehose.delivery_stream_name
  firehose_delivery_stream_arn  = module.kinesis_firehose.delivery_stream_arn

  # API Gateway (opcional)
  api_gateway_execution_arn = module.api_gateway.execution_arn

  # Tags corporativos
  tags = {
    Environment = "dev"
    Project     = "janis-cencosud"
    ManagedBy   = "terraform"
  }
}
```

### Configuración Avanzada

```hcl
module "lambda" {
  source = "./modules/lambda"

  # ... configuración básica ...

  # Lambda Runtime Configuration
  lambda_runtime     = "python3.11"
  lambda_timeout     = 60
  lambda_memory_size = 1024

  # Log Retention
  log_retention_days = 90

  # Function Creation Flags
  create_webhook_processor = true
  create_data_enrichment   = true
  create_api_polling       = true

  # Deployment Packages
  webhook_processor_zip_path = "../lambda/webhook-processor/deployment.zip"
  data_enrichment_zip_path   = "../lambda/data-enrichment/deployment.zip"
  api_polling_zip_path       = "../lambda/api-polling/deployment.zip"

  # Additional Environment Variables
  lambda_environment_variables = {
    LOG_LEVEL           = "INFO"
    ENABLE_XRAY_TRACING = "true"
    MAX_RETRIES         = "3"
  }

  tags = local.all_tags
}
```

### Deshabilitar Funciones Específicas

```hcl
module "lambda" {
  source = "./modules/lambda"

  # ... configuración básica ...

  # Solo crear webhook processor
  create_webhook_processor = true
  create_data_enrichment   = false
  create_api_polling       = false

  tags = local.all_tags
}
```

## Outputs

El módulo proporciona outputs para todas las funciones Lambda:

```hcl
# IAM Role
module.lambda.lambda_execution_role_arn
module.lambda.lambda_execution_role_name

# Webhook Processor
module.lambda.webhook_processor_function_name
module.lambda.webhook_processor_function_arn
module.lambda.webhook_processor_invoke_arn

# Data Enrichment
module.lambda.data_enrichment_function_name
module.lambda.data_enrichment_function_arn

# API Polling
module.lambda.api_polling_function_name
module.lambda.api_polling_function_arn

# All Functions
module.lambda.all_function_arns

# Log Groups
module.lambda.log_group_names
```

## Seguridad

### IAM Role y Políticas

El módulo crea un IAM Role compartido para todas las funciones Lambda con los siguientes permisos:

**CloudWatch Logs**:
- `logs:CreateLogGroup`
- `logs:CreateLogStream`
- `logs:PutLogEvents`

**Amazon S3**:
- `s3:PutObject` - Escribir objetos
- `s3:GetObject` - Leer objetos
- `s3:ListBucket` - Listar contenido de buckets

**Kinesis Firehose** (si está configurado):
- `firehose:PutRecord`
- `firehose:PutRecordBatch`

**Secrets Manager**:
- `secretsmanager:GetSecretValue` - Leer credenciales de Janis

**VPC Networking**:
- `ec2:CreateNetworkInterface`
- `ec2:DescribeNetworkInterfaces`
- `ec2:DeleteNetworkInterface`

### VPC Configuration

Todas las funciones Lambda se despliegan dentro de la VPC en subnets privadas:

- **Subnets**: Private Subnet 1A (y 1B si Multi-AZ está habilitado)
- **Security Group**: SG-Lambda con reglas restrictivas
- **Conectividad**: A través de NAT Gateway para acceso a internet
- **VPC Endpoints**: Acceso privado a servicios AWS (S3, Secrets Manager, etc.)

### Secrets Management

Las credenciales sensibles se almacenan en AWS Secrets Manager:

```json
{
  "secret_name": "janis/api-credentials",
  "secret_value": {
    "api_key": "your-api-key",
    "api_secret": "your-api-secret",
    "base_url": "https://api.janis.com"
  }
}
```

Las funciones Lambda acceden a estos secretos en tiempo de ejecución usando el SDK de AWS.

## Monitoreo

### CloudWatch Logs

Cada función Lambda tiene su propio Log Group:

- `/aws/lambda/{name_prefix}-webhook-processor`
- `/aws/lambda/{name_prefix}-data-enrichment`
- `/aws/lambda/{name_prefix}-api-polling`

**Retención**: Configurable (default: 90 días)

### Métricas de CloudWatch

Métricas automáticas disponibles:

- **Invocations**: Número de invocaciones
- **Duration**: Tiempo de ejecución
- **Errors**: Número de errores
- **Throttles**: Invocaciones throttled
- **ConcurrentExecutions**: Ejecuciones concurrentes
- **DeadLetterErrors**: Errores al enviar a DLQ

### Alarmas Recomendadas

```hcl
# Alarma de errores
resource "aws_cloudwatch_metric_alarm" "lambda_errors" {
  alarm_name          = "${var.name_prefix}-lambda-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "Errors"
  namespace           = "AWS/Lambda"
  period              = "300"
  statistic           = "Sum"
  threshold           = "10"
  alarm_description   = "Lambda function errors"
  
  dimensions = {
    FunctionName = module.lambda.webhook_processor_function_name
  }
}

# Alarma de throttling
resource "aws_cloudwatch_metric_alarm" "lambda_throttles" {
  alarm_name          = "${var.name_prefix}-lambda-throttles"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "1"
  metric_name         = "Throttles"
  namespace           = "AWS/Lambda"
  period              = "60"
  statistic           = "Sum"
  threshold           = "5"
  alarm_description   = "Lambda function throttling"
  
  dimensions = {
    FunctionName = module.lambda.webhook_processor_function_name
  }
}
```

## Deployment

### Preparar Deployment Package

```bash
# Crear directorio de deployment
mkdir -p lambda/webhook-processor
cd lambda/webhook-processor

# Instalar dependencias
pip install -r requirements.txt -t .

# Crear archivo ZIP
zip -r deployment.zip .

# Mover a ubicación esperada por Terraform
mv deployment.zip ../../terraform/lambda-packages/
```

### Deploy con Terraform

```bash
# Inicializar Terraform
cd terraform
terraform init

# Validar configuración
terraform validate

# Plan
terraform plan -var-file="environments/dev/terraform.tfvars"

# Apply
terraform apply -var-file="environments/dev/terraform.tfvars"
```

### Actualizar Código de Lambda

```bash
# Actualizar código
cd lambda/webhook-processor
# ... hacer cambios ...

# Recrear deployment package
zip -r deployment.zip .

# Aplicar cambios con Terraform
cd ../../terraform
terraform apply -var-file="environments/dev/terraform.tfvars"
```

## Testing

### Testing Local

```python
# test_webhook_processor.py
import json
from webhook_processor import handler

def test_webhook_processing():
    event = {
        "body": json.dumps({
            "event_type": "order.created",
            "entity_id": "12345",
            "timestamp": "2024-02-04T10:00:00Z"
        })
    }
    
    context = {}
    
    response = handler(event, context)
    
    assert response["statusCode"] == 200
    assert "message" in json.loads(response["body"])
```

### Testing en AWS

```bash
# Invocar función manualmente
aws lambda invoke \
  --function-name janis-cencosud-dev-webhook-processor \
  --payload '{"test": "data"}' \
  response.json

# Ver logs
aws logs tail /aws/lambda/janis-cencosud-dev-webhook-processor --follow

# Ver métricas
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Invocations \
  --dimensions Name=FunctionName,Value=janis-cencosud-dev-webhook-processor \
  --start-time 2024-02-04T00:00:00Z \
  --end-time 2024-02-04T23:59:59Z \
  --period 3600 \
  --statistics Sum
```

## Optimización de Performance

### Memory Sizing

```hcl
# Testing con diferentes memory sizes
lambda_memory_size = 512   # Default
lambda_memory_size = 1024  # Para procesamiento más pesado
lambda_memory_size = 2048  # Para transformaciones complejas
```

**Nota**: Más memoria = más CPU = ejecución más rápida (pero más costosa)

### Timeout Configuration

```hcl
# Webhook processor (rápido)
lambda_timeout = 30

# Data enrichment (medio)
lambda_timeout = 60

# API polling (largo)
lambda_timeout = 300
```

### Provisioned Concurrency

Para funciones con alta demanda y sensibles a cold starts:

```hcl
resource "aws_lambda_provisioned_concurrency_config" "webhook_processor" {
  function_name                     = module.lambda.webhook_processor_function_name
  provisioned_concurrent_executions = 5
  qualifier                         = aws_lambda_alias.webhook_processor_live.name
}
```

## Troubleshooting

### Error: Function timeout

**Causa**: La función excede el timeout configurado

**Solución**:
1. Aumentar `lambda_timeout` en variables
2. Optimizar código para reducir tiempo de ejecución
3. Considerar procesamiento asíncrono

### Error: ENI creation failed

**Causa**: Problemas con VPC networking

**Solución**:
1. Verificar que subnets privadas tienen IPs disponibles
2. Verificar que Security Group permite tráfico saliente
3. Verificar que NAT Gateway está funcionando

### Error: Access denied to S3

**Causa**: Permisos IAM insuficientes

**Solución**:
1. Verificar que `bronze_bucket_arn` es correcto
2. Verificar que IAM policy incluye permisos S3
3. Verificar que bucket policy no bloquea acceso

### Error: Cannot connect to Secrets Manager

**Causa**: VPC Endpoints no configurados o Security Group bloqueando

**Solución**:
1. Habilitar VPC Endpoint para Secrets Manager
2. Verificar Security Group permite HTTPS (443) saliente
3. Verificar que secret existe en Secrets Manager

## Estimación de Costos

### Compute Costs

**Pricing** (us-east-1):
- $0.20 por 1M requests
- $0.0000166667 por GB-segundo

**Ejemplo** (webhook processor):
- 1M requests/mes
- 512 MB memory
- 100ms average duration

**Cálculo**:
- Requests: 1M × $0.20 = $0.20
- Compute: 1M × 0.1s × 0.5GB × $0.0000166667 = $0.83
- **Total**: ~$1.03/mes

### Data Transfer

- Dentro de VPC: Gratis
- A S3 (mismo región): Gratis
- A internet: $0.09/GB

### CloudWatch Logs

- Ingestion: $0.50/GB
- Storage: $0.03/GB/mes
- Queries: $0.005/GB scanned

## Mejores Prácticas

### Código

- ✅ Usar environment variables para configuración
- ✅ Implementar proper error handling
- ✅ Usar logging estructurado (JSON)
- ✅ Implementar idempotencia
- ✅ Validar inputs
- ✅ Usar connection pooling para databases

### Deployment

- ✅ Usar versioning de funciones Lambda
- ✅ Implementar aliases (dev, staging, prod)
- ✅ Usar deployment packages optimizados
- ✅ Minimizar tamaño de deployment package
- ✅ Usar Lambda Layers para dependencias compartidas

### Monitoreo

- ✅ Configurar alarmas para errores y throttling
- ✅ Usar X-Ray para distributed tracing
- ✅ Implementar custom metrics
- ✅ Monitorear cold starts
- ✅ Revisar logs regularmente

### Seguridad

- ✅ Usar IAM roles con permisos mínimos
- ✅ Almacenar secretos en Secrets Manager
- ✅ Desplegar en VPC privada
- ✅ Habilitar encryption en reposo
- ✅ Usar HTTPS para todas las comunicaciones

## Referencias

- [AWS Lambda Best Practices](https://docs.aws.amazon.com/lambda/latest/dg/best-practices.html)
- [Lambda Pricing](https://aws.amazon.com/lambda/pricing/)
- [Lambda Limits](https://docs.aws.amazon.com/lambda/latest/dg/gettingstarted-limits.html)
- [VPC Lambda Functions](https://docs.aws.amazon.com/lambda/latest/dg/configuration-vpc.html)
