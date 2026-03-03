# Operación y Mantenimiento

## 📋 Operaciones Diarias

### Monitoreo de Pipeline

#### Dashboard Principal
**URL**: https://console.aws.amazon.com/cloudwatch/dashboards/cencosud-etl-prod

**Métricas Clave**:
- Latencia Bronze → Silver: < 5 min
- Latencia Silver → Gold: < 10 min
- Tasa de error: < 0.1%
- Registros procesados/hora

#### Verificación Manual Diaria

```bash
# 1. Verificar últimos registros en Bronze
aws s3 ls s3://cencosud-datalake-bronze-prod/metro/orders/date=$(date +%Y-%m-%d)/ | tail -5

# 2. Verificar Silver actualizado
aws s3 ls s3://cencosud-datalake-silver-prod/metro_orders_clean/ --recursive | tail -1

# 3. Verificar Gold actualizado
aws s3 ls s3://cencosud-datalake-gold-prod/metro/orders/year=$(date +%Y)/month=$(date +%-m)/day=$(date +%-d)/

# 4. Verificar jobs ejecutándose
aws glue get-job-runs --job-name etl-bronze-to-silver-orders-prod --max-results 5
```

---

## 🔧 Mantenimiento Semanal

### Lunes: Revisión de Métricas

```bash
# Generar reporte semanal
python scripts/generate_weekly_report.py \
  --start-date $(date -d '7 days ago' +%Y-%m-%d) \
  --end-date $(date +%Y-%m-%d)
```

### Miércoles: Limpieza de Logs

```bash
# Eliminar logs antiguos (> 30 días)
aws logs delete-log-group --log-group-name /aws-glue/jobs/output/old-logs
```

### Viernes: Backup de Configuración

```bash
# Backup de Glue jobs
aws glue get-jobs --output json > backups/glue-jobs-$(date +%Y%m%d).json

# Backup de EventBridge rules
aws events list-rules --output json > backups/eventbridge-rules-$(date +%Y%m%d).json
```

---

## 🚨 Troubleshooting

### Problema: Job Falla Constantemente

**Síntomas**:
- Job falla con error "Out of Memory"
- Logs muestran "GC overhead limit exceeded"

**Diagnóstico**:
```bash
# Ver logs del job
aws logs tail /aws-glue/jobs/error --follow

# Ver métricas de memoria
aws cloudwatch get-metric-statistics \
  --namespace AWS/Glue \
  --metric-name glue.driver.jvm.heap.used \
  --dimensions Name=JobName,Value=etl-bronze-to-silver-orders-prod \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Average
```

**Solución**:
```bash
# Aumentar workers
aws glue update-job \
  --job-name etl-bronze-to-silver-orders-prod \
  --job-update '{
    "NumberOfWorkers": 5,
    "WorkerType": "G.2X"
  }'
```

---

### Problema: Latencia Alta

**Síntomas**:
- Datos tardan > 30 min en llegar a Gold
- Dashboard muestra latencia en rojo

**Diagnóstico**:
```bash
# Ver tiempo de ejecución de jobs
aws glue get-job-runs \
  --job-name etl-bronze-to-silver-orders-prod \
  --max-results 10 \
  --query 'JobRuns[*].[Id,ExecutionTime]'
```

**Solución**:
```bash
# Reducir intervalo de EventBridge
aws events put-rule \
  --name trigger-bronze-to-silver-every-5min \
  --schedule-expression "rate(3 minutes)"

# O aumentar paralelismo
aws glue update-job \
  --job-name etl-bronze-to-silver-orders-prod \
  --job-update '{
    "MaxConcurrentRuns": 3
  }'
```

---

### Problema: Duplicados en Silver

**Síntomas**:
- Queries muestran registros duplicados
- Logs indican "Duplicate detected"

**Diagnóstico**:
```bash
# Contar duplicados en Silver
aws s3 cp s3://cencosud-datalake-silver-prod/metro_orders_clean/part-00000.json - | \
  jq -r '.data_id' | sort | uniq -d | wc -l
```

**Solución**:
```bash
# Re-ejecutar pipeline con deduplicación forzada
aws glue start-job-run \
  --job-name etl-bronze-to-silver-orders-prod \
  --arguments '{
    "--entity-type":"orders",
    "--client":"metro",
    "--force-deduplication":"true"
  }'
```

---

### Problema: Webhooks No Llegan

**Síntomas**:
- Bronze no recibe datos nuevos
- API Gateway muestra 0 requests

**Diagnóstico**:
```bash
# Ver logs de API Gateway
aws logs tail /aws/apigateway/cencosud-webhooks-prod --follow

# Ver métricas de Lambda
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Invocations \
  --dimensions Name=FunctionName,Value=webhook-processor-prod \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Sum
```

**Solución**:
1. Verificar configuración en Janis Admin Panel
2. Verificar firma del webhook
3. Revisar logs de Lambda para errores

---

## 📊 Métricas y KPIs

### SLAs Definidos

| Métrica | Target | Crítico |
|---------|--------|---------|
| Latencia Bronze → Silver | < 5 min | > 15 min |
| Latencia Silver → Gold | < 10 min | > 30 min |
| Latencia Gold → Redshift | < 30 min | > 60 min |
| Tasa de error | < 0.1% | > 1% |
| Disponibilidad | > 99.9% | < 99% |

### Queries de Monitoreo

```sql
-- Redshift: Verificar última actualización
SELECT 
  MAX(etl_timestamp) as last_update,
  COUNT(*) as total_records,
  COUNT(DISTINCT order_id) as unique_orders
FROM wms_orders
WHERE date_created >= CURRENT_DATE - 7;

-- Redshift: Verificar calidad de datos
SELECT 
  COUNT(*) as total,
  COUNT(CASE WHEN customer_email IS NULL THEN 1 END) as missing_email,
  COUNT(CASE WHEN total_amount <= 0 THEN 1 END) as invalid_amount
FROM wms_orders
WHERE date_created = CURRENT_DATE;
```

---

## 🔄 Procedimientos de Mantenimiento

### Compactación de Archivos Pequeños

```bash
# Ejecutar compactación en Silver
aws glue start-job-run \
  --job-name compact-silver-files-prod \
  --arguments '{
    "--table":"metro_orders_clean",
    "--target-file-size":"128MB"
  }'
```

### Actualización de Esquemas

```bash
# 1. Backup de configuración actual
aws s3 cp \
  s3://cencosud-glue-assets-prod/config/redshift_schemas.json \
  s3://cencosud-glue-assets-prod/config/backups/redshift_schemas_$(date +%Y%m%d).json

# 2. Subir nueva configuración
aws s3 cp \
  config/redshift_schemas_v2.json \
  s3://cencosud-glue-assets-prod/config/redshift_schemas.json

# 3. Re-ejecutar pipeline Silver → Gold
aws glue start-job-run \
  --job-name etl-silver-to-gold-orders-prod \
  --arguments '{"--gold-table":"wms_orders","--client":"metro"}'
```

### Rotación de Logs

```bash
# Script de rotación automática
#!/bin/bash
# rotate-logs.sh

RETENTION_DAYS=30

# Eliminar logs antiguos
aws logs describe-log-groups --query 'logGroups[*].logGroupName' --output text | \
while read log_group; do
  aws logs put-retention-policy \
    --log-group-name "$log_group" \
    --retention-in-days $RETENTION_DAYS
done
```

---

## 📞 Contactos y Escalación

### Equipo de Data Engineering

- **On-call**: +56 9 XXXX XXXX
- **Email**: data-engineering@cencosud.com
- **Slack**: #data-engineering-alerts

### Escalación

1. **Nivel 1** (0-30 min): Data Engineer on-call
2. **Nivel 2** (30-60 min): Lead Data Engineer
3. **Nivel 3** (> 60 min): Head of Data Engineering

### Proveedores

- **AWS Support**: Caso Enterprise
- **Janis Support**: support@janis.in

---

**Última actualización**: 2026-02-26  
**Versión**: 1.0.0
