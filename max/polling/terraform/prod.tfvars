# ============================================================================
# Production Configuration - API Polling System
# ============================================================================
# Este archivo configura la infraestructura de polling:
# - DynamoDB para control de estado
# - S3 staging bucket
# - SNS para notificaciones
# - IAM roles y policies
# - MWAA (Managed Apache Airflow)
# - EventBridge para scheduling
# ============================================================================

# ============================================================================
# AWS Configuration
# ============================================================================

aws_region = "us-east-1"

# Credenciales AWS (pasar por variables de entorno)
# export AWS_ACCESS_KEY_ID="xxx"
# export AWS_SECRET_ACCESS_KEY="xxx"
# export AWS_SESSION_TOKEN="xxx"  # Para SSO
aws_access_key_id     = ""
aws_secret_access_key = ""
aws_session_token     = ""

# LocalStack (dejar vacío para AWS real)
localstack_endpoint    = ""
localstack_s3_endpoint = ""

# ============================================================================
# Project Configuration
# ============================================================================

project_name = "janis-polling"
environment  = "prod"

# ============================================================================
# IAM Roles (EXISTENTES - deben ser proporcionados)
# ============================================================================

# Rol para MWAA - debe tener permisos para:
# - DynamoDB: GetItem, PutItem, UpdateItem, DeleteItem, Query, Scan
# - S3: GetObject, PutObject, ListBucket (Bronze bucket y MWAA bucket)
# - Secrets Manager: GetSecretValue, DescribeSecret
# - SNS: Publish
# - CloudWatch: PutMetricData, CreateLogStream, PutLogEvents
mwaa_execution_role_arn = "arn:aws:iam::181398079618:role/NOMBRE_ROL_MWAA"

# Rol para EventBridge - debe tener permisos para:
# - MWAA: airflow:CreateCliToken
eventbridge_role_arn = "arn:aws:iam::181398079618:role/NOMBRE_ROL_EVENTBRIDGE"

# ============================================================================
# VPC Configuration (EXISTENTE)
# ============================================================================

# VPC existente de Cencosud
vpc_id = "vpc-0e70f630594378796"

# Subnets privadas en diferentes AZs (us-east-1a y us-east-1b)
private_subnet_ids = [
  "subnet-0f96d2e7838f2789c",  # us-east-1a - 100.64.0.0/18
  "subnet-0f2a9da0a0eb89bcc"   # us-east-1b - 100.64.64.0/18
]

# ============================================================================
# MWAA Configuration
# ============================================================================

airflow_version   = "2.7.2"
environment_class = "mw1.small"
min_workers       = 1
max_workers       = 3

# ============================================================================
# S3 Bronze Bucket (DEBE EXISTIR O CREARSE)
# ============================================================================

# Nombre del bucket Bronze donde se escribirán los datos
# Estructura: s3://{bucket}/bronze/{client}/{data_type}/
bronze_bucket_name = "cencosud.test.super.peru.raw"


# ============================================================================
# Multi-Tenant Configuration
# ============================================================================

# Lista de clientes a configurar
clients = ["wongio", "metro"]

# ============================================================================
# EventBridge Configuration
# ============================================================================

# Frecuencia de polling en minutos (cada 5 minutos)
polling_rate_minutes = 5

# ============================================================================
# DynamoDB Configuration
# ============================================================================

dynamodb_billing_mode         = "PAY_PER_REQUEST"
enable_point_in_time_recovery = true

# ============================================================================
# S3 Staging Configuration
# ============================================================================

enable_s3_versioning        = true
s3_intelligent_tiering_days = 30
s3_glacier_transition_days  = 90
s3_expiration_days          = 365

# ============================================================================
# SNS Configuration
# ============================================================================

# Emails para notificaciones de errores
error_notification_emails = [
  "vicente.morales@externos-cl.cencosud.com"
]

# ============================================================================
# Secrets Manager ARNs (DEBEN CREARSE MANUALMENTE)
# ============================================================================

# ARNs de los secrets con credenciales de Janis API
# Formato del secret: {"api_key": "xxx", "api_secret": "yyy"}
# Nombre sugerido: janis-api-credentials-{client}
secrets_manager_arns = [
  "arn:aws:secretsmanager:us-east-1:181398079618:secret:janis-api-credentials-wongio-*",
  "arn:aws:secretsmanager:us-east-1:181398079618:secret:janis-api-credentials-metro-*"
]

# ============================================================================
# Monitoring Configuration
# ============================================================================

enable_monitoring  = true
log_retention_days = 30

# ============================================================================
# INSTRUCCIONES DE DEPLOYMENT
# ============================================================================
#
# PREREQUISITOS:
#
# 1. VPC y Subnets (✅ YA EXISTEN):
#    - VPC: vpc-0e70f630594378796
#    - Subnets privadas en us-east-1a y us-east-1b
#
# 2. S3 Bronze Bucket:
#    - Crear bucket: cencosud-datalake-bronze-prod
#    - O actualizar bronze_bucket_name con bucket existente
#
# 3. Secrets Manager (PENDIENTE - requiere permisos):
#    - Crear secret: janis-api-credentials-wongio
#    - Formato JSON: {"api_key": "xxx", "api_secret": "yyy"}
#    - Actualizar ARN en secrets_manager_arns
#
# 4. Credenciales AWS:
#    - Configurar SSO: aws configure sso
#    - O exportar variables de entorno
#
# PASOS DE DEPLOYMENT:
#
# 1. Configurar credenciales AWS:
#    aws configure sso
#    # O exportar:
#    export AWS_ACCESS_KEY_ID="xxx"
#    export AWS_SECRET_ACCESS_KEY="xxx"
#    export AWS_SESSION_TOKEN="xxx"
#
# 2. Inicializar Terraform:
#    cd max/polling/terraform
#    terraform init
#
# 3. Validar configuración:
#    terraform validate
#    terraform fmt -check
#
# 4. Planificar cambios:
#    terraform plan -var-file="prod.tfvars"
#
# 5. Aplicar infraestructura:
#    terraform apply -var-file="prod.tfvars"
#
# 6. Subir DAGs a MWAA:
#    # Obtener nombre del bucket MWAA
#    MWAA_BUCKET=$(terraform output -raw mwaa_s3_bucket_name)
#    
#    # Subir DAGs
#    aws s3 sync ../dags/ s3://$MWAA_BUCKET/dags/
#    
#    # Subir requirements
#    aws s3 cp ../requirements.txt s3://$MWAA_BUCKET/requirements.txt
#
# 7. Configurar variables en Airflow UI:
#    - Acceder a MWAA webserver URL (ver output)
#    - Admin > Variables
#    - Agregar:
#      * JANIS_API_BASE_URL: https://oms.janis.in/api
#      * DYNAMODB_TABLE_NAME: janis-polling-prod-polling-control
#      * S3_BRONZE_BUCKET: cencosud-datalake-bronze-prod
#
# OUTPUTS IMPORTANTES:
#
# - mwaa_webserver_url: URL para acceder a Airflow UI
# - mwaa_environment_name: Nombre del ambiente MWAA
# - mwaa_s3_bucket_name: Bucket donde subir DAGs
# - dynamodb_table_name: Tabla de control de polling
#
# ============================================================================
