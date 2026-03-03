# Configuración para Producción

## 📋 Tabla de Contenidos

- [Requisitos Previos](#requisitos-previos)
- [Configuración de S3 Buckets](#configuración-de-s3-buckets)
- [Configuración de AWS Glue Jobs](#configuración-de-aws-glue-jobs)
- [Configuración de IAM Roles](#configuración-de-iam-roles)
- [Variables de Entorno](#variables-de-entorno)
- [Configuración de Secrets Manager](#configuración-de-secrets-manager)
- [Configuración de EventBridge](#configuración-de-eventbridge)

---

## Requisitos Previos

### Cuentas y Accesos

- ✅ Cuenta AWS con permisos de administrador
- ✅ Acceso a API de Janis (API keys por cliente)
- ✅ Credenciales de MySQL Janis (para carga inicial)
- ✅ Acceso a Redshift cluster
- ✅ Permisos para crear recursos en AWS

### Herramientas Necesarias

```bash
# AWS CLI
aws --version  # >= 2.0

# Terraform (opcional, para IaC)
terraform --version  # >= 1.0

# Python
python --version  # >= 3.11

# Git
git --version
```

---

## Configuración de S3 Buckets

### Crear Buckets

```bash
# Bronze Layer
aws s3 mb s3://cencosud-datalake-bronze-prod --region us-east-1

# Silver Layer
aws s3 mb s3://cencosud-datalake-silver-prod --region us-east-1

# Gold Layer
aws s3 mb s3://cencosud-datalake-gold-prod --region us-east-1

# Scripts y configuración
aws s3 mb s3://cencosud-glue-assets-prod --region us-east-1
```

### Configurar Lifecycle Policies

**Bronze (Retención indefinida con transición a Glacier)**:

```json
{
  "Rules": [
    {
      "Id": "TransitionToGlacierAfter90Days",
      "Status": "Enabled",
      "Transitions": [
        {
          "Days": 90,
          "StorageClass": "GLACIER"
        }
      ]
    }
  ]
}
```

```bash
aws s3api put-bucket-lifecycle-configuration \
  --bucket cencosud-datalake-bronze-prod \
  --lifecycle-configuration file://bronze-lifecycle.json
```

**Silver (Retención 1 año)**:

```json
{
  "Rules": [
    {
      "Id": "DeleteAfter365Days",
      "Status": "Enabled",
      "Expiration": {
        "Days": 365
      }
    }
  ]
}
```

**Gold (Retención 2 años)**:

```json
{
  "Rules": [
    {
      "Id": "DeleteAfter730Days",
      "Status": "Enabled",
      "Expiration": {
        "Days": 730
      }
    }
  ]
}
```

### Configurar Encriptación

```bash
# Habilitar encriptación SSE-S3 en todos los buckets
for bucket in bronze silver gold assets; do
  aws s3api put-bucket-encryption \
    --bucket cencosud-datalake-${bucket}-prod \
    --server-side-encryption-configuration '{
      "Rules": [{
        "ApplyServerSideEncryptionByDefault": {
          "SSEAlgorithm": "AES256"
        }
      }]
    }'
done
```

### Configurar Versionado (Solo Bronze)

```bash
aws s3api put-bucket-versioning \
  --bucket cencosud-datalake-bronze-prod \
  --versioning-configuration Status=Enabled
```

### Configurar Tags

```bash
# Aplicar tags a todos los buckets
for bucket in bronze silver gold assets; do
  aws s3api put-bucket-tagging \
    --bucket cencosud-datalake-${bucket}-prod \
    --tagging 'TagSet=[
      {Key=Environment,Value=production},
      {Key=Project,Value=janis-cencosud-integration},
      {Key=Owner,Value=data-engineering},
      {Key=CostCenter,Value=analytics}
    ]'
done
```

---

## Configuración de AWS Glue Jobs

### Subir Scripts a S3

```bash
# Comprimir módulos
cd max/glue
zip -r modules.zip modules/

# Subir a S3
aws s3 cp modules.zip s3://cencosud-glue-assets-prod/scripts/
aws s3 cp etl-bronze-to-silver/run_pipeline.py s3://cencosud-glue-assets-prod/scripts/
aws s3 cp etl-silver-to-gold/run_pipeline_to_gold.py s3://cencosud-glue-assets-prod/scripts/
aws s3 cp etl-silver-to-gold/config/ s3://cencosud-glue-assets-prod/config/ --recursive
```

### Crear Glue Job: Bronze → Silver

```bash
aws glue create-job \
  --name etl-bronze-to-silver-orders-prod \
  --role arn:aws:iam::123456789:role/GlueServiceRole \
  --command '{
    "Name": "glueetl",
    "ScriptLocation": "s3://cencosud-glue-assets-prod/scripts/run_pipeline.py",
    "PythonVersion": "3"
  }' \
  --default-arguments '{
    "--job-language": "python",
    "--extra-py-files": "s3://cencosud-glue-assets-prod/scripts/modules.zip",
    "--enable-metrics": "true",
    "--enable-continuous-cloudwatch-log": "true",
    "--enable-spark-ui": "true",
    "--spark-event-logs-path": "s3://cencosud-glue-assets-prod/spark-logs/",
    "--TempDir": "s3://cencosud-glue-assets-prod/temp/",
    "--bronze-bucket": "cencosud-datalake-bronze-prod",
    "--silver-bucket": "cencosud-datalake-silver-prod"
  }' \
  --glue-version "4.0" \
  --worker-type "G.1X" \
  --number-of-workers 2 \
  --max-retries 3 \
  --timeout 60 \
  --tags '{
    "Environment": "production",
    "Project": "janis-cencosud-integration"
  }'
```

### Crear Glue Job: Silver → Gold

```bash
aws glue create-job \
  --name etl-silver-to-gold-orders-prod \
  --role arn:aws:iam::123456789:role/GlueServiceRole \
  --command '{
    "Name": "glueetl",
    "ScriptLocation": "s3://cencosud-glue-assets-prod/scripts/run_pipeline_to_gold.py",
    "PythonVersion": "3"
  }' \
  --default-arguments '{
    "--job-language": "python",
    "--extra-py-files": "s3://cencosud-glue-assets-prod/scripts/modules.zip",
    "--enable-metrics": "true",
    "--enable-continuous-cloudwatch-log": "true",
    "--enable-spark-ui": "true",
    "--spark-event-logs-path": "s3://cencosud-glue-assets-prod/spark-logs/",
    "--TempDir": "s3://cencosud-glue-assets-prod/temp/",
    "--silver-bucket": "cencosud-datalake-silver-prod",
    "--gold-bucket": "cencosud-datalake-gold-prod",
    "--config-path": "s3://cencosud-glue-assets-prod/config/silver-to-gold-config.json"
  }' \
  --glue-version "4.0" \
  --worker-type "G.1X" \
  --number-of-workers 2 \
  --max-retries 3 \
  --timeout 60
```

### Parámetros de Configuración por Job

#### Bronze → Silver

| Parámetro | Valor | Descripción |
|-----------|-------|-------------|
| `--entity-type` | `orders` | Tipo de entidad a procesar |
| `--client` | `metro` o `wongio` | Cliente a procesar |
| `--bronze-bucket` | `cencosud-datalake-bronze-prod` | Bucket de origen |
| `--silver-bucket` | `cencosud-datalake-silver-prod` | Bucket de destino |
| `--date-partition` | `2026-02-26` (opcional) | Partición específica a procesar |

#### Silver → Gold

| Parámetro | Valor | Descripción |
|-----------|-------|-------------|
| `--gold-table` | `wms_orders` | Tabla Gold a generar |
| `--client` | `metro` o `wongio` | Cliente a procesar |
| `--silver-bucket` | `cencosud-datalake-silver-prod` | Bucket de origen |
| `--gold-bucket` | `cencosud-datalake-gold-prod` | Bucket de destino |
| `--config-path` | `s3://...config.json` | Configuración de mapeo |

---

## Configuración de IAM Roles

### Glue Service Role

**Archivo**: `glue-service-role-policy.json`

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:DeleteObject"
      ],
      "Resource": [
        "arn:aws:s3:::cencosud-datalake-bronze-prod/*",
        "arn:aws:s3:::cencosud-datalake-silver-prod/*",
        "arn:aws:s3:::cencosud-datalake-gold-prod/*",
        "arn:aws:s3:::cencosud-glue-assets-prod/*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::cencosud-datalake-bronze-prod",
        "arn:aws:s3:::cencosud-datalake-silver-prod",
        "arn:aws:s3:::cencosud-datalake-gold-prod",
        "arn:aws:s3:::cencosud-glue-assets-prod"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "glue:GetDatabase",
        "glue:GetTable",
        "glue:GetPartitions",
        "glue:CreateTable",
        "glue:UpdateTable",
        "glue:DeleteTable",
        "glue:BatchCreatePartition",
        "glue:BatchDeletePartition"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "arn:aws:logs:*:*:/aws-glue/*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "cloudwatch:PutMetricData"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "secretsmanager:GetSecretValue"
      ],
      "Resource": "arn:aws:secretsmanager:*:*:secret:janis/*"
    }
  ]
}
```

### Crear Role

```bash
# 1. Crear trust policy
cat > glue-trust-policy.json << EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "glue.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF

# 2. Crear role
aws iam create-role \
  --role-name GlueServiceRole \
  --assume-role-policy-document file://glue-trust-policy.json

# 3. Attach policy
aws iam put-role-policy \
  --role-name GlueServiceRole \
  --policy-name GlueServicePolicy \
  --policy-document file://glue-service-role-policy.json
```

---

## Variables de Entorno

### Configuración de Glue Jobs

Las variables se pasan como `--arguments` al ejecutar el job:

```bash
aws glue start-job-run \
  --job-name etl-bronze-to-silver-orders-prod \
  --arguments '{
    "--entity-type": "orders",
    "--client": "metro",
    "--bronze-bucket": "cencosud-datalake-bronze-prod",
    "--silver-bucket": "cencosud-datalake-silver-prod",
    "--date-partition": "2026-02-26"
  }'
```

### Variables de Configuración Global

**Archivo**: `max/glue/etl-bronze-to-silver/config/production.json`

```json
{
  "environment": "production",
  "aws_region": "us-east-1",
  "bronze_bucket": "cencosud-datalake-bronze-prod",
  "silver_bucket": "cencosud-datalake-silver-prod",
  "gold_bucket": "cencosud-datalake-gold-prod",
  "glue_database": "cencosud_datalake",
  "log_level": "INFO",
  "enable_metrics": true,
  "enable_data_quality_checks": true,
  "max_retries": 3,
  "timeout_minutes": 60,
  "spark_config": {
    "spark.sql.adaptive.enabled": "true",
    "spark.sql.adaptive.coalescePartitions.enabled": "true",
    "spark.sql.files.maxPartitionBytes": "134217728",
    "spark.sql.shuffle.partitions": "200"
  }
}
```

---

## Configuración de Secrets Manager

### Crear Secrets para API Keys de Janis

```bash
# Metro
aws secretsmanager create-secret \
  --name janis/metro/api_key \
  --description "API Key de Janis para cliente Metro" \
  --secret-string '{"api_key":"YOUR_METRO_API_KEY_HERE"}' \
  --tags Key=Environment,Value=production Key=Client,Value=metro

# Wongio
aws secretsmanager create-secret \
  --name janis/wongio/api_key \
  --description "API Key de Janis para cliente Wongio" \
  --secret-string '{"api_key":"YOUR_WONGIO_API_KEY_HERE"}' \
  --tags Key=Environment,Value=production Key=Client,Value=wongio
```

### Crear Secret para MySQL (Carga Inicial)

```bash
aws secretsmanager create-secret \
  --name janis/mysql/credentials \
  --description "Credenciales MySQL de Janis para carga inicial" \
  --secret-string '{
    "host": "janis-mysql.example.com",
    "port": 3306,
    "username": "readonly_user",
    "password": "YOUR_PASSWORD_HERE",
    "database": "janis_wms"
  }' \
  --tags Key=Environment,Value=production
```

### Acceder a Secrets desde Glue

```python
import boto3
import json

def get_secret(secret_name):
    """Obtener secret desde Secrets Manager"""
    client = boto3.client('secretsmanager', region_name='us-east-1')
    response = client.get_secret_value(SecretId=secret_name)
    return json.loads(response['SecretString'])

# Uso
api_key = get_secret('janis/metro/api_key')['api_key']
```

---

## Configuración de EventBridge

### Rule: Trigger Bronze → Silver cada 5 minutos

```bash
aws events put-rule \
  --name trigger-bronze-to-silver-every-5min \
  --schedule-expression "rate(5 minutes)" \
  --state ENABLED \
  --description "Trigger Bronze to Silver pipeline every 5 minutes"

# Agregar target (Glue Job)
aws events put-targets \
  --rule trigger-bronze-to-silver-every-5min \
  --targets '[
    {
      "Id": "1",
      "Arn": "arn:aws:glue:us-east-1:123456789:job/etl-bronze-to-silver-orders-prod",
      "RoleArn": "arn:aws:iam::123456789:role/EventBridgeToGlue",
      "Input": "{\"--entity-type\":\"orders\",\"--client\":\"metro\"}"
    }
  ]'
```

### Rule: Trigger Silver → Gold cada 10 minutos

```bash
aws events put-rule \
  --name trigger-silver-to-gold-every-10min \
  --schedule-expression "rate(10 minutes)" \
  --state ENABLED

aws events put-targets \
  --rule trigger-silver-to-gold-every-10min \
  --targets '[
    {
      "Id": "1",
      "Arn": "arn:aws:glue:us-east-1:123456789:job/etl-silver-to-gold-orders-prod",
      "RoleArn": "arn:aws:iam::123456789:role/EventBridgeToGlue",
      "Input": "{\"--gold-table\":\"wms_orders\",\"--client\":\"metro\"}"
    }
  ]'
```

### Rule: Polling de Janis API cada 15 minutos

```bash
aws events put-rule \
  --name poll-janis-orders-every-15min \
  --schedule-expression "rate(15 minutes)" \
  --state ENABLED

aws events put-targets \
  --rule poll-janis-orders-every-15min \
  --targets '[
    {
      "Id": "1",
      "Arn": "arn:aws:airflow:us-east-1:123456789:environment/cencosud-mwaa-prod",
      "RoleArn": "arn:aws:iam::123456789:role/EventBridgeToMWAA",
      "Input": "{\"dag_name\":\"dag_poll_orders\",\"conf\":{}}"
    }
  ]'
```

---

## Configuración de CloudWatch Alarms

### Alarm: Glue Job Failed

```bash
aws cloudwatch put-metric-alarm \
  --alarm-name glue-job-bronze-to-silver-failed \
  --alarm-description "Alert when Bronze to Silver job fails" \
  --metric-name JobRunsFailed \
  --namespace AWS/Glue \
  --statistic Sum \
  --period 300 \
  --evaluation-periods 1 \
  --threshold 1 \
  --comparison-operator GreaterThanOrEqualToThreshold \
  --dimensions Name=JobName,Value=etl-bronze-to-silver-orders-prod \
  --alarm-actions arn:aws:sns:us-east-1:123456789:data-engineering-alerts
```

### Alarm: High Latency

```bash
aws cloudwatch put-metric-alarm \
  --alarm-name glue-job-high-latency \
  --alarm-description "Alert when job takes more than 30 minutes" \
  --metric-name JobRunTime \
  --namespace AWS/Glue \
  --statistic Average \
  --period 300 \
  --evaluation-periods 1 \
  --threshold 1800 \
  --comparison-operator GreaterThanThreshold \
  --dimensions Name=JobName,Value=etl-bronze-to-silver-orders-prod \
  --alarm-actions arn:aws:sns:us-east-1:123456789:data-engineering-alerts
```

---

## Checklist de Configuración

### Pre-Deployment

- [ ] Buckets S3 creados con encriptación
- [ ] Lifecycle policies configuradas
- [ ] IAM roles creados con permisos mínimos
- [ ] Secrets Manager configurado con API keys
- [ ] Scripts subidos a S3
- [ ] Glue jobs creados
- [ ] EventBridge rules configuradas
- [ ] CloudWatch alarms configuradas
- [ ] SNS topics para alertas creados

### Post-Deployment

- [ ] Ejecutar test de Bronze → Silver
- [ ] Ejecutar test de Silver → Gold
- [ ] Verificar datos en cada capa
- [ ] Validar alertas funcionando
- [ ] Documentar credenciales y accesos
- [ ] Capacitar equipo de operaciones

---

**Última actualización**: 2026-02-26  
**Versión**: 1.0.0
