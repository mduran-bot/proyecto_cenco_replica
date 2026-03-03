# Guía de Deployment a Producción

## 📋 Pasos de Deployment

### Fase 1: Preparación (Día 1)

#### 1.1 Validar Requisitos
```bash
# Verificar acceso a AWS
aws sts get-caller-identity

# Verificar región
aws configure get region  # Debe ser us-east-1

# Verificar permisos
aws iam get-user
```

#### 1.2 Crear Infraestructura Base
```bash
# Ejecutar script de creación de buckets
cd max/glue/docProd/scripts
./01-create-s3-buckets.sh

# Crear IAM roles
./02-create-iam-roles.sh

# Configurar Secrets Manager
./03-configure-secrets.sh
```

#### 1.3 Subir Assets a S3
```bash
# Comprimir y subir módulos
cd max/glue
zip -r modules.zip modules/
aws s3 cp modules.zip s3://cencosud-glue-assets-prod/scripts/

# Subir scripts
aws s3 sync etl-bronze-to-silver/ s3://cencosud-glue-assets-prod/scripts/bronze-to-silver/
aws s3 sync etl-silver-to-gold/ s3://cencosud-glue-assets-prod/scripts/silver-to-gold/
```

---

### Fase 2: Deployment de Glue Jobs (Día 2)

#### 2.1 Crear Glue Jobs
```bash
# Bronze → Silver
aws glue create-job --cli-input-json file://glue-jobs/bronze-to-silver.json

# Silver → Gold
aws glue create-job --cli-input-json file://glue-jobs/silver-to-gold.json
```

#### 2.2 Test Manual de Jobs
```bash
# Test Bronze → Silver con datos de prueba
aws glue start-job-run \
  --job-name etl-bronze-to-silver-orders-prod \
  --arguments '{
    "--entity-type":"orders",
    "--client":"metro",
    "--date-partition":"2026-02-26"
  }'

# Monitorear ejecución
aws glue get-job-run \
  --job-name etl-bronze-to-silver-orders-prod \
  --run-id jr_xxx
```

---

### Fase 3: Configurar Orquestación (Día 3)

#### 3.1 Configurar EventBridge
```bash
# Crear rules
./04-create-eventbridge-rules.sh

# Verificar rules
aws events list-rules --name-prefix trigger-
```

#### 3.2 Configurar MWAA (Airflow)
```bash
# Subir DAGs
aws s3 cp airflow/dags/ s3://cencosud-mwaa-prod/dags/ --recursive

# Verificar DAGs
aws mwaa list-environments
```

---

### Fase 4: Carga Inicial (Día 4-5)

#### 4.1 Ejecutar Migración desde MySQL
```bash
# Ejecutar script de carga inicial
python max/cargainicial/mysql_to_s3_bronze.py \
  --client metro \
  --start-date 2024-01-01 \
  --end-date 2026-02-26 \
  --batch-size 1000

# Monitorear progreso
aws s3 ls s3://cencosud-datalake-bronze-prod/metro/orders/ --recursive | wc -l
```

#### 4.2 Procesar Datos Iniciales
```bash
# Trigger Bronze → Silver para todas las particiones
for date in $(seq -f "%Y-%m-%d" 2024-01-01 2026-02-26); do
  aws glue start-job-run \
    --job-name etl-bronze-to-silver-orders-prod \
    --arguments "{\"--date-partition\":\"$date\"}"
done
```

---

### Fase 5: Configurar Webhooks (Día 6)

#### 5.1 Desplegar API Gateway + Lambda
```bash
# Desplegar stack de webhooks
cd terraform/modules/webhooks
terraform init
terraform apply -var-file=prod.tfvars
```

#### 5.2 Configurar Webhooks en Janis
```bash
# Obtener URL del webhook
aws apigateway get-rest-apis --query 'items[?name==`cencosud-webhooks-prod`].id' --output text

# URL: https://{api-id}.execute-api.us-east-1.amazonaws.com/prod/webhooks/{client}/{entity}
```

**Configurar en Janis Admin Panel**:
- URL: `https://xxx.execute-api.us-east-1.amazonaws.com/prod/webhooks/metro/orders`
- Eventos: `order.created`, `order.updated`
- Secret: (obtener de Secrets Manager)

---

### Fase 6: Monitoreo y Alertas (Día 7)

#### 6.1 Configurar CloudWatch Dashboards
```bash
# Crear dashboard
aws cloudwatch put-dashboard \
  --dashboard-name cencosud-etl-prod \
  --dashboard-body file://cloudwatch/dashboard.json
```

#### 6.2 Configurar Alarmas
```bash
# Crear alarmas
./05-create-cloudwatch-alarms.sh

# Verificar alarmas
aws cloudwatch describe-alarms --alarm-name-prefix glue-job-
```

#### 6.3 Configurar SNS para Alertas
```bash
# Crear topic
aws sns create-topic --name data-engineering-alerts-prod

# Suscribir emails
aws sns subscribe \
  --topic-arn arn:aws:sns:us-east-1:123456789:data-engineering-alerts-prod \
  --protocol email \
  --notification-endpoint team@cencosud.com
```

---

## Validación Post-Deployment

### Checklist de Validación

#### Infraestructura
- [ ] Buckets S3 creados y accesibles
- [ ] IAM roles con permisos correctos
- [ ] Secrets Manager configurado
- [ ] Glue jobs creados y funcionales

#### Pipeline
- [ ] Bronze: Datos llegando desde webhooks
- [ ] Bronze: Polling funcionando cada 15 min
- [ ] Silver: Transformaciones aplicadas correctamente
- [ ] Gold: Datos en formato Parquet particionado

#### Orquestación
- [ ] EventBridge rules activas
- [ ] MWAA DAGs ejecutándose
- [ ] Latencias dentro de SLA

#### Monitoreo
- [ ] CloudWatch dashboards visibles
- [ ] Alarmas configuradas y funcionando
- [ ] SNS notifications llegando

---

## Rollback Procedures

### Rollback de Glue Job

```bash
# 1. Detener job en ejecución
aws glue stop-job-run \
  --job-name etl-bronze-to-silver-orders-prod \
  --run-id jr_xxx

# 2. Revertir a versión anterior del script
aws s3 cp \
  s3://cencosud-glue-assets-prod/scripts/run_pipeline.py.backup \
  s3://cencosud-glue-assets-prod/scripts/run_pipeline.py

# 3. Actualizar job
aws glue update-job \
  --job-name etl-bronze-to-silver-orders-prod \
  --job-update file://glue-jobs/bronze-to-silver-v1.json
```

### Rollback de Datos

```bash
# Silver: Restaurar desde backup
aws s3 sync \
  s3://cencosud-datalake-silver-prod-backup/metro_orders_clean/ \
  s3://cencosud-datalake-silver-prod/metro_orders_clean/

# Gold: Restaurar desde backup
aws s3 sync \
  s3://cencosud-datalake-gold-prod-backup/metro/orders/ \
  s3://cencosud-datalake-gold-prod/metro/orders/
```

---

## Troubleshooting Común

### Job Falla con "Out of Memory"

**Solución**: Aumentar workers
```bash
aws glue update-job \
  --job-name etl-bronze-to-silver-orders-prod \
  --job-update '{
    "NumberOfWorkers": 5,
    "WorkerType": "G.2X"
  }'
```

### Latencia Alta en Pipeline

**Solución**: Reducir intervalo de EventBridge
```bash
aws events put-rule \
  --name trigger-bronze-to-silver-every-5min \
  --schedule-expression "rate(3 minutes)"
```

### Duplicados en Silver

**Solución**: Verificar módulo DuplicateDetector
```bash
# Ver logs del job
aws logs tail /aws-glue/jobs/output \
  --follow \
  --filter-pattern "DuplicateDetector"
```

---

**Última actualización**: 2026-02-26  
**Versión**: 1.0.0
