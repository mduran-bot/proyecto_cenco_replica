# Resumen de Módulos de Data Pipeline

**Fecha**: 4 de Febrero, 2026  
**Estado**: ✅ Todos los módulos creados

---

## Módulos Creados

Se han creado 5 nuevos módulos para completar la infraestructura de data pipeline:

### 1. Lambda Module ✅
**Ubicación**: `terraform/modules/lambda/`

**Funciones Lambda creadas**:
- **webhook-processor**: Procesa webhooks de Janis en tiempo real
- **data-enrichment**: Enriquece datos antes de escribir a Silver
- **api-polling**: Polling periódico de API de Janis

**Características**:
- IAM role con permisos para S3, Firehose, Secrets Manager
- VPC integration con subnets privadas
- CloudWatch Logs con retención configurable
- Permisos para API Gateway
- Variables de entorno configurables

**Archivos**:
- `main.tf` - 3 funciones Lambda + IAM roles
- `variables.tf` - Configuración de runtime, memoria, timeout
- `outputs.tf` - ARNs y nombres de funciones

---

### 2. API Gateway Module ✅
**Ubicación**: `terraform/modules/api-gateway/`

**Recursos creados**:
- REST API regional para webhooks
- Endpoint `/webhooks/{entity}` con método POST
- Integración Lambda proxy
- Stage de deployment por ambiente
- Usage plan y throttling
- API Key (opcional)

**Características**:
- Access logging a CloudWatch
- Throttling: 2000 req/s, burst 5000
- Quota: 100,000 requests/día
- IAM role para CloudWatch Logs

**Archivos**:
- `main.tf` - API Gateway + deployment + stage
- `variables.tf` - Configuración de throttling y quotas
- `outputs.tf` - URLs de endpoints y API keys

---

### 3. Kinesis Firehose Module ✅
**Ubicación**: `terraform/modules/kinesis-firehose/`

**Delivery Streams creados**:
- **orders-stream**: Stream para órdenes

**Características**:
- Delivery a S3 Bronze con particionamiento por fecha
- Buffering: 5MB o 300 segundos
- Compresión GZIP
- Error handling con prefijos separados
- Transformación Lambda opcional
- CloudWatch alarms para delivery failures
- **IAM policy mejorada**: Manejo correcto de permisos Lambda opcionales (4 Feb 2026)

**Archivos**:
- `main.tf` - Firehose stream + IAM + alarms
- `variables.tf` - Configuración de buffering y compresión
- `outputs.tf` - ARNs de streams
- `KINESIS_IAM_POLICY_IMPROVEMENT.md` - Documentación de mejora IAM ⭐ NUEVO

---

### 4. AWS Glue Module ✅
**Ubicación**: `terraform/modules/glue/`

**Recursos creados**:
- **3 Glue Catalog Databases**: bronze, silver, gold
- **2 Glue Jobs**:
  - bronze-to-silver: Limpieza y validación
  - silver-to-gold: Agregación para BI

**Características**:
- IAM role con permisos para S3 y Glue
- Glue 4.0 con Python 3
- Worker type: G.1X (configurable)
- Job bookmarks habilitados
- Spark UI y metrics habilitados
- VPC integration preparada

**Archivos**:
- `main.tf` - Databases + jobs + IAM
- `variables.tf` - Configuración de workers
- `outputs.tf` - Nombres de databases y jobs

---

### 5. MWAA Module ✅
**Ubicación**: `terraform/modules/mwaa/`

**Recursos creados**:
- MWAA Environment (Managed Airflow)
- IAM execution role con permisos completos

**Características**:
- Airflow 2.7.2
- Environment class: mw1.small (configurable)
- Auto-scaling: 1-10 workers
- VPC integration con subnets privadas
- Logging completo (DAG, scheduler, task, webserver, worker)
- Permisos para invocar Lambda y Glue jobs
- Acceso a buckets S3 (Bronze, Silver, Gold, Scripts)

**Archivos**:
- `main.tf` - MWAA environment + IAM
- `variables.tf` - Configuración de Airflow
- `outputs.tf` - ARN y webserver URL

---

## Arquitectura Completa

```
┌─────────────────────────────────────────────────────────────────┐
│                         INGESTA DE DATOS                         │
└─────────────────────────────────────────────────────────────────┘

Webhooks Janis → API Gateway → Lambda (webhook-processor) → Kinesis Firehose → S3 Bronze

EventBridge → MWAA → Lambda (api-polling) → S3 Bronze

┌─────────────────────────────────────────────────────────────────┐
│                      TRANSFORMACIÓN ETL                          │
└─────────────────────────────────────────────────────────────────┘

S3 Bronze → Glue Job (bronze-to-silver) → S3 Silver (Iceberg)

S3 Silver → Glue Job (silver-to-gold) → S3 Gold (Iceberg)

┌─────────────────────────────────────────────────────────────────┐
│                      CONSUMO DE DATOS                            │
└─────────────────────────────────────────────────────────────────┘

S3 Gold → Redshift COPY → Power BI / Tableau
```

---

## Integración Pendiente en main.tf

**ACTUALIZACIÓN (4 Feb 2026)**: ✅ **COMPLETADO** - Todos los módulos han sido integrados en `terraform/main.tf`.

Los siguientes módulos están ahora activos:
- ✅ Kinesis Firehose Module (líneas 211-233)
- ✅ Lambda Module (líneas 235-270)
- ✅ API Gateway Module (líneas 272-296)
- ✅ AWS Glue Module (líneas 298-326)
- ✅ MWAA Module (líneas 328-363)

---

## Variables Adicionales Necesarias

**ACTUALIZACIÓN (4 Feb 2026)**: ✅ **COMPLETADO** - Todas las variables han sido agregadas en `terraform/variables.tf`.

```hcl
# Lambda Module
module "lambda" {
  source = "./modules/lambda"
  
  name_prefix               = local.name_prefix
  environment               = var.environment
  private_subnet_ids        = module.vpc.private_subnet_ids
  lambda_security_group_id  = module.security_groups.sg_lambda_id
  bronze_bucket_name        = module.s3.bronze_bucket_id
  bronze_bucket_arn         = module.s3.bronze_bucket_arn
  silver_bucket_name        = module.s3.silver_bucket_id
  scripts_bucket_arn        = module.s3.scripts_bucket_arn
  
  tags = local.all_tags
}

# API Gateway Module
module "api_gateway" {
  source = "./modules/api-gateway"
  
  name_prefix                   = local.name_prefix
  environment                   = var.environment
  webhook_processor_invoke_arn  = module.lambda.webhook_processor_invoke_arn
  
  tags = local.all_tags
}

# Kinesis Firehose Module
module "kinesis_firehose" {
  source = "./modules/kinesis-firehose"
  
  name_prefix        = local.name_prefix
  bronze_bucket_arn  = module.s3.bronze_bucket_arn
  
  tags = local.all_tags
}

# Glue Module
module "glue" {
  source = "./modules/glue"
  
  name_prefix         = local.name_prefix
  bronze_bucket_name  = module.s3.bronze_bucket_id
  bronze_bucket_arn   = module.s3.bronze_bucket_arn
  silver_bucket_name  = module.s3.silver_bucket_id
  silver_bucket_arn   = module.s3.silver_bucket_arn
  gold_bucket_name    = module.s3.gold_bucket_id
  gold_bucket_arn     = module.s3.gold_bucket_arn
  scripts_bucket_name = module.s3.scripts_bucket_id
  scripts_bucket_arn  = module.s3.scripts_bucket_arn
  
  tags = local.all_tags
}

# MWAA Module
module "mwaa" {
  count = var.create_mwaa_environment ? 1 : 0

  source = "./modules/mwaa"
  
  name_prefix            = local.name_prefix
  aws_region             = var.aws_region
  private_subnet_ids     = module.vpc.private_subnet_ids
  mwaa_security_group_id = module.security_groups.sg_mwaa_id
  scripts_bucket_arn     = module.s3.scripts_bucket_arn
  bronze_bucket_arn      = module.s3.bronze_bucket_arn
  silver_bucket_arn      = module.s3.silver_bucket_arn
  gold_bucket_arn        = module.s3.gold_bucket_arn
  lambda_function_arns   = [
    module.lambda.api_polling_function_arn
  ]
  
  tags = local.all_tags
}

# EventBridge Module - Integración automática con MWAA
module "eventbridge" {
  source = "./modules/eventbridge"
  
  name_prefix          = local.name_prefix
  # Use MWAA ARN from module if created, otherwise use variable (for manual override)
  mwaa_environment_arn = var.create_mwaa_environment ? module.mwaa[0].mwaa_environment_arn : var.mwaa_environment_arn
  environment          = var.environment
  
  tags = local.all_tags
}
```

**Integración EventBridge + MWAA mejorada**:
- ✅ EventBridge detecta automáticamente el ARN de MWAA cuando se crea con Terraform
- ✅ Soporta MWAA existente usando la variable `mwaa_environment_arn`
- ✅ No requiere configuración manual del ARN
- ✅ Evita errores de configuración

---

## Variables Adicionales Necesarias

**ACTUALIZACIÓN (4 Feb 2026)**: ✅ **COMPLETADO** - Todas las variables han sido agregadas en `terraform/variables.tf`.

Las siguientes secciones de variables han sido agregadas:

### Kinesis Firehose Configuration (líneas 387-408)
- `firehose_buffering_size` (default: 5 MB)
- `firehose_buffering_interval` (default: 300 segundos)
- `firehose_compression_format` (default: "GZIP")

### Lambda Configuration (líneas 410-447)
- `lambda_runtime` (default: "python3.11")
- `lambda_timeout` (default: 30 segundos)
- `lambda_memory_size` (default: 512 MB)
- `create_lambda_webhook_processor` (default: true)
- `create_lambda_data_enrichment` (default: true)
- `create_lambda_api_polling` (default: true)

### API Gateway Configuration (líneas 449-489)
- `create_api_gateway` (default: true)
- `api_gateway_create_usage_plan` (default: true)
- `api_gateway_quota_limit` (default: 100000 requests/día)
- `api_gateway_throttle_burst_limit` (default: 5000)
- `api_gateway_throttle_rate_limit` (default: 2000 req/s)
- `api_gateway_create_api_key` (default: true)

### AWS Glue Configuration (líneas 491-520)
- `glue_worker_type` (default: "G.1X")
- `glue_number_of_workers` (default: 2)
- `create_glue_bronze_to_silver_job` (default: true)
- `create_glue_silver_to_gold_job` (default: true)

### MWAA Configuration (líneas 522-558)
- `create_mwaa_environment` (default: true)
- `mwaa_airflow_version` (default: "2.7.2")
- `mwaa_environment_class` (default: "mw1.small")
- `mwaa_max_workers` (default: 10)
- `mwaa_min_workers` (default: 1)

---

## Outputs Adicionales

**ACTUALIZACIÓN (4 Feb 2026)**: ✅ **COMPLETADO** - Todos los outputs han sido agregados en `terraform/outputs.tf`.

Los siguientes outputs están ahora disponibles:

### Kinesis Firehose Outputs
- `firehose_orders_stream_name`
- `firehose_orders_stream_arn`

### Lambda Outputs
- `lambda_execution_role_arn`
- `webhook_processor_function_name`
- `webhook_processor_function_arn`
- `data_enrichment_function_name`
- `api_polling_function_name`
- `all_lambda_function_arns`

### API Gateway Outputs
- `api_gateway_id`
- `api_gateway_stage_invoke_url`
- `api_gateway_webhook_endpoint_url`
- `api_gateway_api_key_value` (sensitive)

### AWS Glue Outputs
- `glue_bronze_database_name`
- `glue_silver_database_name`
- `glue_gold_database_name`
- `glue_bronze_to_silver_job_name`
- `glue_silver_to_gold_job_name`
- `all_glue_job_names`

### MWAA Outputs
- `mwaa_environment_arn`
- `mwaa_webserver_url`
- `mwaa_execution_role_arn`

---

```hcl
# Lambda Configuration
variable "lambda_runtime" {
  description = "Lambda runtime version"
  type        = string
  default     = "python3.11"
}

variable "lambda_memory_size" {
  description = "Lambda memory size in MB"
  type        = number
  default     = 512
}

variable "lambda_timeout" {
  description = "Lambda timeout in seconds"
  type        = number
  default     = 30
}

# Glue Configuration
variable "glue_worker_type" {
  description = "Glue worker type"
  type        = string
  default     = "G.1X"
}

variable "glue_number_of_workers" {
  description = "Number of Glue workers"
  type        = number
  default     = 2
}

# MWAA Configuration
variable "mwaa_environment_class" {
  description = "MWAA environment class"
  type        = string
  default     = "mw1.small"
}

variable "mwaa_max_workers" {
  description = "MWAA maximum workers"
  type        = number
  default     = 10
}

variable "mwaa_min_workers" {
  description = "MWAA minimum workers"
  type        = number
  default     = 1
}

# Kinesis Firehose Configuration
variable "firehose_buffering_size" {
  description = "Firehose buffer size in MB"
  type        = number
  default     = 5
}

variable "firehose_buffering_interval" {
  description = "Firehose buffer interval in seconds"
  type        = number
  default     = 300
}
```

---

## Outputs Adicionales

Agregar en `terraform/outputs.tf`:

```hcl
# Lambda Outputs
output "lambda_function_arns" {
  description = "ARNs of Lambda functions"
  value       = module.lambda.all_function_arns
}

# API Gateway Outputs
output "api_gateway_url" {
  description = "API Gateway invoke URL"
  value       = module.api_gateway.stage_invoke_url
}

output "webhook_endpoint" {
  description = "Webhook endpoint URL"
  value       = module.api_gateway.webhook_endpoint_url
}

# Kinesis Firehose Outputs
output "firehose_stream_name" {
  description = "Kinesis Firehose stream name"
  value       = module.kinesis_firehose.orders_stream_name
}

# Glue Outputs
output "glue_databases" {
  description = "Glue catalog database names"
  value = {
    bronze = module.glue.bronze_database_name
    silver = module.glue.silver_database_name
    gold   = module.glue.gold_database_name
  }
}

output "glue_jobs" {
  description = "Glue job names"
  value       = module.glue.all_job_names
}

# MWAA Outputs
output "mwaa_webserver_url" {
  description = "MWAA Airflow webserver URL"
  value       = module.mwaa.mwaa_webserver_url
}

output "mwaa_environment_arn" {
  description = "MWAA environment ARN"
  value       = module.mwaa.mwaa_environment_arn
}
```

---

## Estimación de Costos Adicionales

### Lambda
- **Requests**: $0.20 por 1M requests
- **Compute**: $0.0000166667 por GB-segundo
- **Estimado**: $5-10/mes (bajo volumen)

### API Gateway
- **Requests**: $3.50 por 1M requests
- **Data transfer**: $0.09/GB
- **Estimado**: $10-20/mes

### Kinesis Firehose
- **Data ingestion**: $0.029 por GB
- **Estimado**: $5-15/mes (depende del volumen)

### AWS Glue
- **DPU-Hour**: $0.44 por DPU-hour
- **G.1X worker**: 1 DPU
- **Estimado**: $20-50/mes (ejecuciones diarias)

### MWAA
- **mw1.small**: $0.49/hora = $354/mes
- **Workers**: Incluidos en el precio base
- **Estimado**: $354/mes (ambiente pequeño)

### **Total Adicional**: ~$394-449/mes

---

## Estado de Implementación

✅ **S3 Module** - Creado e integrado en main.tf  
✅ **Lambda Module** - Creado e integrado en main.tf  
✅ **API Gateway Module** - Creado e integrado en main.tf  
✅ **Kinesis Firehose Module** - Creado e integrado en main.tf  
✅ **AWS Glue Module** - Creado e integrado en main.tf  
✅ **MWAA Module** - Creado e integrado en main.tf  

**ACTUALIZACIÓN**: Todos los módulos han sido integrados en `terraform/main.tf` y están listos para deployment.  

---

## Próximos Pasos

**ACTUALIZACIÓN (4 Feb 2026)**: Con la integración completa, los próximos pasos son:

1. **Actualizar terraform.tfvars.testing** con las nuevas variables (si es necesario)
   ```bash
   cd terraform
   # Revisar y actualizar terraform.tfvars.testing con valores específicos
   ```

2. **Ejecutar terraform init** para inicializar los nuevos módulos
   ```bash
   terraform init -upgrade
   ```

3. **Ejecutar terraform validate** para validar la configuración
   ```bash
   terraform validate
   ```

4. **Ejecutar terraform plan** para revisar los recursos que se crearán
   ```bash
   terraform plan -var-file="terraform.tfvars.testing"
   ```

5. **Preparar deployment packages para Lambda** (si se van a crear las funciones)
   - Crear archivos `.zip` con el código Python
   - Subir a S3 o especificar path local
   - Actualizar variables `*_zip_path` si es necesario

6. **Preparar DAGs de Airflow** (si se va a crear MWAA)
   - Crear directorio `dags/` en scripts bucket
   - Subir archivos `.py` con DAGs de Airflow

7. **Preparar scripts de Glue** (si se van a crear los jobs)
   - Crear directorio `glue/` en scripts bucket
   - Subir scripts `bronze-to-silver/main.py` y `silver-to-gold/main.py`

8. **Ejecutar terraform apply** cuando esté listo
   ```bash
   terraform apply -var-file="terraform.tfvars.testing"
   ```

---

## Notas Importantes

### Código de Lambda
Los módulos Lambda están configurados pero **requieren código de deployment**:
- Crear archivos `.zip` con el código Python
- Subir a S3 o especificar path local
- Actualizar variables `*_zip_path`

### DAGs de Airflow
MWAA requiere DAGs en S3:
- Crear directorio `dags/` en scripts bucket
- Subir archivos `.py` con DAGs de Airflow
- MWAA los sincronizará automáticamente

### Scripts de Glue
Glue jobs requieren scripts Python:
- Crear directorio `glue/` en scripts bucket
- Subir scripts `bronze-to-silver/main.py` y `silver-to-gold/main.py`

### Dependencias
Algunos módulos dependen de otros:
- API Gateway → Lambda (invoke ARN)
- Lambda → Kinesis Firehose (stream ARN)
- MWAA → Lambda (function ARNs)
- Todos → S3 (bucket ARNs)

---

## Referencias

- [AWS Lambda Best Practices](https://docs.aws.amazon.com/lambda/latest/dg/best-practices.html)
- [API Gateway Developer Guide](https://docs.aws.amazon.com/apigateway/latest/developerguide/)
- [Kinesis Firehose Documentation](https://docs.aws.amazon.com/firehose/latest/dev/)
- [AWS Glue Developer Guide](https://docs.aws.amazon.com/glue/latest/dg/)
- [MWAA User Guide](https://docs.aws.amazon.com/mwaa/latest/userguide/)
