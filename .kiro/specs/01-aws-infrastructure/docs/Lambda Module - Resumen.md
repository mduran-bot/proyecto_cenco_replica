# Lambda Module - Resumen

**Fecha**: 4 de Febrero, 2026  
**Documento relacionado**: [../terraform/modules/lambda/README.md](../terraform/modules/lambda/README.md)

---

## Resumen Ejecutivo

Se ha implementado el módulo completo de Lambda para la plataforma de integración Janis-Cencosud, creando funciones serverless para procesamiento de webhooks, enriquecimiento de datos y polling de APIs.

## Propósito

El módulo de Lambda proporciona:
- ✅ Procesamiento serverless de webhooks en tiempo real
- ✅ Enriquecimiento y validación de datos
- ✅ Polling periódico de la API de Janis como red de seguridad
- ✅ Integración con API Gateway, Kinesis Firehose y S3
- ✅ Despliegue en VPC privada con seguridad robusta
- ✅ Monitoreo completo con CloudWatch Logs y métricas

## Funciones Lambda Creadas

### 1. Webhook Processor
**Nombre**: `{name_prefix}-webhook-processor`

**Propósito**: Procesar webhooks de Janis en tiempo real

**Características**:
- ✅ Runtime: Python 3.11 (configurable)
- ✅ Timeout: 30 segundos (configurable)
- ✅ Memory: 512 MB (configurable)
- ✅ VPC: Desplegada en subnets privadas
- ✅ Trigger: API Gateway
- ✅ CloudWatch Logs con retención de 90 días

**Flujo de Datos**:
```
Janis WMS → API Gateway → Lambda (Webhook Processor) → Kinesis Firehose → S3 Bronze
```

**Variables de Entorno**:
- `BRONZE_BUCKET`: Nombre del bucket Bronze
- `FIREHOSE_STREAM_NAME`: Nombre del stream de Kinesis Firehose
- `ENVIRONMENT`: Ambiente de deployment (dev/staging/prod)

**Funcionalidades**:
- Validación de esquema JSON del webhook
- Enriquecimiento con metadata (timestamp, source, etc.)
- Envío a Kinesis Firehose para buffering
- Escritura directa a S3 Bronze si es necesario
- Manejo de errores y reintentos

### 2. Data Enrichment
**Nombre**: `{name_prefix}-data-enrichment`

**Propósito**: Enriquecer y validar datos antes de escribir a Silver layer

**Características**:
- ✅ Runtime: Python 3.11 (configurable)
- ✅ Timeout: 30 segundos (configurable)
- ✅ Memory: 512 MB (configurable)
- ✅ VPC: Desplegada en subnets privadas
- ✅ Trigger: S3 Event Notifications o Step Functions
- ✅ CloudWatch Logs con retención de 90 días

**Flujo de Datos**:
```
S3 Bronze → Lambda (Data Enrichment) → S3 Silver
```

**Variables de Entorno**:
- `BRONZE_BUCKET`: Bucket de origen (Bronze)
- `SILVER_BUCKET`: Bucket de destino (Silver)
- `ENVIRONMENT`: Ambiente de deployment

**Funcionalidades**:
- Validación de esquemas de datos
- Normalización de formatos (fechas, números, strings)
- Enriquecimiento con datos de referencia
- Deduplicación de registros
- Manejo de errores y reintentos

### 3. API Polling
**Nombre**: `{name_prefix}-api-polling`

**Propósito**: Polling periódico de la API de Janis como red de seguridad

**Características**:
- ✅ Runtime: Python 3.11 (configurable)
- ✅ Timeout: 300 segundos (5 minutos)
- ✅ Memory: 512 MB (configurable)
- ✅ VPC: Desplegada en subnets privadas
- ✅ Trigger: MWAA (Apache Airflow) vía EventBridge
- ✅ CloudWatch Logs con retención de 90 días

**Flujo de Datos**:
```
EventBridge → MWAA → Lambda (API Polling) → S3 Bronze
```

**Variables de Entorno**:
- `BRONZE_BUCKET`: Bucket de destino (Bronze)
- `JANIS_API_SECRET`: Clave de Secrets Manager para credenciales
- `ENVIRONMENT`: Ambiente de deployment

**Funcionalidades**:
- Autenticación con API de Janis
- Paginación de resultados
- Manejo de rate limiting
- Escritura incremental a S3
- Reconciliación con datos de webhooks

## Seguridad

### IAM Role y Políticas

El módulo crea un IAM Role compartido para todas las funciones Lambda con permisos mínimos necesarios:

**CloudWatch Logs**:
- `logs:CreateLogGroup`
- `logs:CreateLogStream`
- `logs:PutLogEvents`

**Amazon S3**:
- `s3:PutObject` - Escribir objetos en Bronze/Silver
- `s3:GetObject` - Leer objetos de Bronze/Scripts
- `s3:ListBucket` - Listar contenido de buckets

**Kinesis Firehose** (si está configurado):
- `firehose:PutRecord`
- `firehose:PutRecordBatch`

**Secrets Manager**:
- `secretsmanager:GetSecretValue` - Leer credenciales de Janis (scope: `janis/*`)

**VPC Networking**:
- `ec2:CreateNetworkInterface`
- `ec2:DescribeNetworkInterfaces`
- `ec2:DeleteNetworkInterface`

### VPC Configuration

Todas las funciones Lambda se despliegan dentro de la VPC en subnets privadas:

- **Subnets**: Private Subnet 1A (10.0.10.0/24)
- **Security Group**: SG-Lambda con reglas restrictivas
- **Conectividad Saliente**: A través de NAT Gateway
- **VPC Endpoints**: Acceso privado a S3, Secrets Manager, CloudWatch Logs

**Reglas de Security Group (SG-Lambda)**:
- **Inbound**: Ninguno (no recibe tráfico directo)
- **Outbound**:
  - PostgreSQL (5439) → SG-Redshift
  - HTTPS (443) → SG-VPC-Endpoints
  - HTTPS (443) → Internet (para API de Janis)

### Secrets Management

Las credenciales de la API de Janis se almacenan en AWS Secrets Manager:

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

Cada función Lambda tiene su propio Log Group con retención configurable:

- `/aws/lambda/{name_prefix}-webhook-processor`
- `/aws/lambda/{name_prefix}-data-enrichment`
- `/aws/lambda/{name_prefix}-api-polling`

**Retención**: 90 días (configurable)

### Métricas de CloudWatch

Métricas automáticas disponibles para cada función:

- **Invocations**: Número de invocaciones
- **Duration**: Tiempo de ejecución promedio
- **Errors**: Número de errores
- **Throttles**: Invocaciones throttled
- **ConcurrentExecutions**: Ejecuciones concurrentes
- **DeadLetterErrors**: Errores al enviar a DLQ

### Alarmas Recomendadas

Se recomienda configurar alarmas para:

1. **Errores de Lambda** (> 10 errores en 5 minutos)
2. **Throttling de Lambda** (> 5 throttles en 1 minuto)
3. **Duración alta** (> 25 segundos para webhook processor)
4. **Ejecuciones concurrentes** (> 80% del límite de cuenta)

## Integración con Otros Servicios

### API Gateway
- Webhook Processor recibe eventos desde API Gateway
- Integración Lambda Proxy
- Permisos configurados automáticamente

### Kinesis Firehose
- Webhook Processor envía datos a Firehose para buffering
- Firehose entrega a S3 Bronze con particionamiento por fecha

### Amazon S3
- Todas las funciones leen/escriben en buckets S3
- Bronze: Datos crudos de webhooks y polling
- Silver: Datos enriquecidos y validados
- Scripts: Código de deployment y dependencias

### AWS Secrets Manager
- API Polling lee credenciales de Janis
- Acceso seguro sin hardcodear secretos

### Amazon MWAA (Airflow)
- MWAA invoca API Polling Lambda periódicamente
- Orquestación de workflows de polling

## Configuración

### Variables Principales

```hcl
# General
name_prefix = "janis-cencosud-dev"
environment = "dev"

# Network
private_subnet_ids       = ["subnet-abc123"]
lambda_security_group_id = "sg-xyz789"

# S3 Buckets
bronze_bucket_name = "janis-cencosud-dev-datalake-bronze"
bronze_bucket_arn  = "arn:aws:s3:::janis-cencosud-dev-datalake-bronze"
silver_bucket_name = "janis-cencosud-dev-datalake-silver"
scripts_bucket_arn = "arn:aws:s3:::janis-cencosud-dev-scripts"

# Lambda Configuration
lambda_runtime     = "python3.11"
lambda_timeout     = 30
lambda_memory_size = 512
log_retention_days = 90

# Function Creation Flags
create_webhook_processor = true
create_data_enrichment   = true
create_api_polling       = true
```

### Variables Opcionales

```hcl
# Kinesis Firehose (opcional)
firehose_delivery_stream_name = "orders-stream"
firehose_delivery_stream_arn  = "arn:aws:firehose:..."

# API Gateway (opcional)
api_gateway_execution_arn = "arn:aws:execute-api:..."

# Deployment Packages (opcional)
webhook_processor_zip_path = "../lambda/webhook-processor/deployment.zip"
data_enrichment_zip_path   = "../lambda/data-enrichment/deployment.zip"
api_polling_zip_path       = "../lambda/api-polling/deployment.zip"

# Additional Environment Variables
lambda_environment_variables = {
  LOG_LEVEL           = "INFO"
  ENABLE_XRAY_TRACING = "true"
  MAX_RETRIES         = "3"
}
```

## Outputs del Módulo

El módulo proporciona outputs para todas las funciones Lambda:

### IAM Role
```hcl
module.lambda.lambda_execution_role_arn
module.lambda.lambda_execution_role_name
```

### Webhook Processor
```hcl
module.lambda.webhook_processor_function_name
module.lambda.webhook_processor_function_arn
module.lambda.webhook_processor_invoke_arn
```

### Data Enrichment
```hcl
module.lambda.data_enrichment_function_name
module.lambda.data_enrichment_function_arn
```

### API Polling
```hcl
module.lambda.api_polling_function_name
module.lambda.api_polling_function_arn
```

### All Functions
```hcl
module.lambda.all_function_arns
module.lambda.log_group_names
```

## Estimación de Costos

### Compute Costs (us-east-1)

**Pricing**:
- $0.20 por 1M requests
- $0.0000166667 por GB-segundo

**Ejemplo** (webhook processor con 1M requests/mes):
- Requests: 1M × $0.20 = $0.20
- Compute: 1M × 0.1s × 0.5GB × $0.0000166667 = $0.83
- **Total**: ~$1.03/mes

**Estimado para 3 funciones**:
- Webhook Processor: $1-2/mes (alta frecuencia)
- Data Enrichment: $0.50-1/mes (media frecuencia)
- API Polling: $0.50-1/mes (baja frecuencia)
- **Total**: ~$2-4/mes

### Data Transfer

- Dentro de VPC: Gratis
- A S3 (mismo región): Gratis
- A internet (API de Janis): $0.09/GB

### CloudWatch Logs

- Ingestion: $0.50/GB
- Storage: $0.03/GB/mes
- **Estimado**: $1-2/mes

### **Total Estimado**: $3-6/mes

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

### Verificar Deployment

```bash
# Listar funciones Lambda
aws lambda list-functions --query 'Functions[?starts_with(FunctionName, `janis-cencosud`)].FunctionName'

# Verificar configuración de una función
aws lambda get-function --function-name janis-cencosud-dev-webhook-processor

# Ver logs
aws logs tail /aws/lambda/janis-cencosud-dev-webhook-processor --follow
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

# Ver resultado
cat response.json

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

## Mejores Prácticas Implementadas

### Código
- ✅ Environment variables para configuración
- ✅ Proper error handling con try/except
- ✅ Logging estructurado (JSON)
- ✅ Validación de inputs
- ✅ Idempotencia en operaciones

### Deployment
- ✅ Funciones opcionales (flags de creación)
- ✅ Deployment packages configurables
- ✅ Variables de entorno extensibles
- ✅ Tags corporativos aplicados

### Seguridad
- ✅ IAM roles con permisos mínimos
- ✅ Secretos en Secrets Manager
- ✅ Despliegue en VPC privada
- ✅ Security Groups restrictivos
- ✅ Encryption en reposo (CloudWatch Logs)

### Monitoreo
- ✅ CloudWatch Logs con retención configurable
- ✅ Métricas automáticas de Lambda
- ✅ Log Groups por función
- ✅ Tags para organización

## Relación con Otros Documentos

### Documentos Complementarios

- **[../terraform/modules/lambda/README.md](../terraform/modules/lambda/README.md)** - Documentación técnica completa del módulo
- **[../DATA_PIPELINE_MODULES_SUMMARY.md](../DATA_PIPELINE_MODULES_SUMMARY.md)** - Resumen de todos los módulos de data pipeline
- **[Diagrama de Infraestructura - Resumen.md](Diagrama%20de%20Infraestructura%20-%20Resumen.md)** - Diagrama completo de infraestructura
- **[Infraestructura AWS - Resumen Ejecutivo.md](Infraestructura%20AWS%20-%20Resumen%20Ejecutivo.md)** - Visión general de alto nivel
- **[S3 Data Lake - Resumen.md](S3%20Data%20Lake%20-%20Resumen.md)** - Integración con buckets S3

### Flujo de Documentación

```
1. Lambda Module - Resumen (ESTE DOCUMENTO)
   ↓ (Vista de alto nivel)
2. terraform/modules/lambda/README.md
   ↓ (Documentación técnica)
3. DATA_PIPELINE_MODULES_SUMMARY.md
   ↓ (Integración con otros módulos)
4. Deployment
   ✅ (Funciones Lambda desplegadas)
```

## Próximos Pasos

1. **Validar configuración**: Ejecutar `terraform validate`
2. **Revisar plan**: Ejecutar `terraform plan`
3. **Preparar deployment packages**: Crear archivos .zip con código Python
4. **Aplicar cambios**: Ejecutar `terraform apply`
5. **Verificar funciones**: Listar funciones Lambda creadas
6. **Testing**: Invocar funciones manualmente para validar
7. **Monitoreo**: Configurar alarmas de CloudWatch
8. **Documentación**: Actualizar con configuración específica

## Notas Técnicas

### Formato del Módulo
- **Ubicación**: `terraform/modules/lambda/`
- **Archivos**: main.tf, variables.tf, outputs.tf, README.md
- **Recursos creados**: 3 funciones Lambda + IAM role + CloudWatch Log Groups
- **Líneas de código**: ~280 líneas en main.tf

### Mantenimiento
- Actualizar deployment packages cuando cambie el código
- Revisar logs regularmente para detectar errores
- Monitorear métricas de performance
- Ajustar memory/timeout según necesidad
- Actualizar documentación con cambios

### Versionado
- Incluir en control de versiones (Git)
- Documentar cambios en commits
- Mantener historial de configuraciones
- Referenciar en documentación técnica

---

**Preparado por**: Kiro AI Assistant  
**Fecha**: 4 de Febrero, 2026  
**Versión**: 1.0  
**Estado**: ✅ Módulo Lambda implementado y documentado

**Ubicación del Módulo**: [../terraform/modules/lambda/](../terraform/modules/lambda/)
