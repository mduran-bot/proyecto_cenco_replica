# Tech Stack and Build System

## Core AWS Services

### Data Pipeline
- **Amazon API Gateway**: REST endpoints para webhooks de Janis
- **AWS Lambda**: Procesamiento serverless y enriquecimiento de datos
- **Amazon Kinesis Data Firehose**: Streaming y buffering de datos
- **Amazon S3**: Data Lake con capas Bronze/Silver/Gold
- **Apache Iceberg**: Formato de tabla con transacciones ACID y time travel
- **AWS Glue**: Motor ETL serverless para transformaciones
- **Amazon Redshift**: Data Warehouse columnar para BI

### Orquestación y Scheduling
- **Amazon EventBridge**: Scheduling inteligente para reducir overhead de MWAA
- **Amazon MWAA (Apache Airflow)**: Orquestación de workflows bajo demanda
- **AWS Step Functions**: Coordinación de procesos complejos

### Seguridad y Monitoreo
- **AWS VPC**: Red privada con subnets públicas/privadas
- **AWS WAF**: Protección contra ataques web
- **AWS Secrets Manager**: Gestión segura de credenciales
- **Amazon CloudWatch**: Monitoreo, métricas y alertas
- **AWS KMS**: Cifrado de datos en reposo

## Infrastructure as Code

### Terraform
- **Versión**: >= 1.0
- **Provider AWS**: ~> 5.0
- **Estructura modular** con separación por ambientes
- **Remote state** en S3 con DynamoDB locking
- **Módulos reutilizables** para componentes comunes

### Organización de Código
```
terraform/
├── environments/
│   ├── dev/
│   ├── staging/
│   └── prod/
├── modules/
│   ├── vpc/
│   ├── lambda/
│   ├── api-gateway/
│   ├── kinesis/
│   ├── glue/
│   └── redshift/
└── shared/
    ├── backend.tf
    ├── providers.tf
    └── variables.tf
```

## Development Tools

### Apache Airflow (MWAA)
- **Versión**: 2.7.2
- **Python**: 3.11
- **Environment**: mw1.small con auto-scaling
- **DAGs**: Triggered por EventBridge (schedule_interval=None)

### AWS Glue
- **Versión**: Glue 4.0
- **Runtime**: PySpark
- **Worker Type**: G.1X (4 vCPU, 16 GB RAM)
- **Auto-scaling**: 2-10 workers

### Lambda Functions
- **Runtime**: Python 3.11
- **Memory**: 512 MB (ajustable)
- **Timeout**: 30 segundos
- **VPC**: Dentro de subnets privadas

## Common Commands

### Terraform Operations
```bash
# Formatear código
terraform fmt -recursive

# Validar configuración
terraform validate

# Planificar cambios
terraform plan -var-file="environments/prod/terraform.tfvars"

# Aplicar cambios
terraform apply -var-file="environments/prod/terraform.tfvars"

# Verificar security issues
tfsec .
```

### MWAA/Airflow Operations
```bash
# Listar DAGs
aws mwaa list-dags --name cencosud-mwaa-environment

# Trigger manual de DAG
aws mwaa create-cli-token --name cencosud-mwaa-environment
# Usar token en Airflow UI para trigger manual

# Ver logs de DAG
aws logs describe-log-groups --log-group-name-prefix "/aws/mwaa"
```

### AWS CLI Útiles
```bash
# Monitorear Kinesis Firehose
aws firehose describe-delivery-stream --delivery-stream-name orders-stream

# Ver métricas de API Gateway
aws cloudwatch get-metric-statistics --namespace AWS/ApiGateway

# Listar objetos en S3 Bronze
aws s3 ls s3://cencosud-datalake-bronze/orders/ --recursive

# Ejecutar Glue job manualmente
aws glue start-job-run --job-name bronze-to-silver-orders
```

## Data Formats and Standards

### JSON Schema Validation
- Webhooks validados contra esquemas JSON predefinidos
- Campos requeridos: event_type, entity_id, timestamp
- Timestamps en formato ISO 8601 (UTC)

### Apache Iceberg Configuration
- **Formato**: Parquet con compresión Snappy
- **Partitioning**: Hidden partitioning por fecha
- **Catalog**: AWS Glue Data Catalog
- **Transacciones**: ACID compliant

### Naming Conventions
- **Recursos AWS**: snake_case con prefijo del proyecto
- **S3 Buckets**: cencosud-datalake-{layer}-{environment}
- **Lambda Functions**: janis-{function-purpose}-{environment}
- **Glue Jobs**: {source}-to-{target}-{entity-type}

## Testing and Validation

### Pre-commit Hooks
```yaml
repos:
  - repo: https://github.com/antonbabenko/pre-commit-terraform
    hooks:
      - id: terraform_fmt
      - id: terraform_validate
      - id: terraform_docs
      - id: terraform_tflint
```

### Data Quality Checks
- Validación de esquemas JSON en Lambda
- Data quality metrics en Glue jobs
- Reconciliación de conteos entre capas
- Alertas automáticas por anomalías de datos