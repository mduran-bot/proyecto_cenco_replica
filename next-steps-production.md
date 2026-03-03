# Próximos Pasos — Pipeline ETL a Producción

## Estado Actual ✅

```
LocalStack (desarrollo local)
Bronze (JSON raw) → Silver (limpio) → Gold (agregado)
```

Todo funciona en local. El objetivo ahora es llevar esto a AWS real.

---

## Fase 1: Preparar Infraestructura AWS Real

### 1.1 Terraform — Recursos Faltantes

Actualizar `terraform/main.tf` para agregar lo que falta:

```hcl
# Bucket Gold (agregar al main.tf existente)
resource "aws_s3_bucket" "gold" {
  bucket = "data-lake-gold"
}

resource "aws_s3_bucket" "metadata" {
  bucket = "data-lake-metadata"
}

# Glue Job Silver-to-Gold (nuevo)
resource "aws_glue_job" "silver_to_gold" {
  name     = "silver-to-gold"
  role_arn = aws_iam_role.glue_role.arn
  
  command {
    script_location = "s3://glue-scripts-bin/scripts/main_job_gold.py"
    python_version  = "3"
  }
  
  default_arguments = {
    "--config_path" = "s3://glue-scripts-bin/config/silver-to-gold-config.json"
  }
}
```

**Checklist Fase 1:**
- [ ] Agregar bucket `data-lake-gold` en Terraform
- [ ] Agregar bucket `data-lake-metadata` en Terraform
- [ ] Crear Glue Job `silver-to-gold` en Terraform
- [ ] Verificar permisos IAM del rol Glue (leer Silver, escribir Gold, leer/escribir metadata)
- [ ] Aplicar `terraform apply` en cuenta AWS real

---

## Fase 2: Adaptar Código para AWS Glue

### 2.1 Crear `main_job_gold.py` (equivalente a `main_job.py` para Gold)

El `run_pipeline_to_gold.py` es para LocalStack. Para AWS Glue necesitas un script que:
- Lee argumentos de Glue (`--JOB_NAME`, `--config_path`)
- Usa SparkSession de Glue (no `local[*]`)
- Lee desde Iceberg en lugar de JSON
- Escribe a Iceberg en lugar de JSON
- Registra métricas en CloudWatch

```python
# src/etl-silver-to-gold/main_job_gold.py
import sys
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job

args = getResolvedOptions(sys.argv, ['JOB_NAME', 'config_path'])
sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args['JOB_NAME'], args)

# ... resto igual que ETLPipelineGold pero con formato iceberg
```

**Checklist Fase 2:**
- [ ] Crear `main_job_gold.py` para AWS Glue
- [ ] Cambiar `format: "json"` → `format: "iceberg"` en config de producción
- [ ] Cambiar `incremental.enabled: false` → `true` en producción
- [ ] Subir script a `s3://glue-scripts-bin/scripts/`
- [ ] Subir config a `s3://glue-scripts-bin/config/`

---

## Fase 3: Configurar Apache Iceberg en Producción

### 3.1 SparkSession con Iceberg para Glue

```python
spark = SparkSession.builder \
    .config("spark.sql.extensions", 
            "org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions") \
    .config("spark.sql.catalog.glue_catalog", 
            "org.apache.iceberg.spark.SparkCatalog") \
    .config("spark.sql.catalog.glue_catalog.warehouse", 
            "s3://data-lake-silver/iceberg") \
    .config("spark.sql.catalog.glue_catalog.catalog-impl", 
            "org.apache.iceberg.aws.glue.GlueCatalog") \
    .getOrCreate()
```

### 3.2 Leer y Escribir Iceberg

```python
# Leer Silver (Iceberg)
df = spark.read.format("iceberg").load("glue_catalog.silver.ventas_procesadas")

# Escribir Gold (Iceberg)
df.write.format("iceberg").mode("append").save("glue_catalog.gold.ventas_agregadas")
```

### 3.3 Crear tablas Iceberg en AWS Glue Data Catalog

```sql
-- Ejecutar una vez para crear las tablas Gold
CREATE TABLE glue_catalog.gold.ventas_agregadas (
    year INT,
    month INT,
    total_monto DECIMAL(18,2),
    promedio_monto DECIMAL(18,2),
    num_registros BIGINT,
    _processing_timestamp TIMESTAMP
)
USING iceberg
PARTITIONED BY (year, month)
LOCATION 's3://data-lake-gold/iceberg/ventas_agregadas'
```

**Checklist Fase 3:**
- [ ] Configurar SparkSession con Iceberg + Glue Catalog
- [ ] Crear tablas Iceberg en Gold con esquema correcto
- [ ] Verificar que Silver ya está en formato Iceberg (el `IcebergWriter` del B2S lo hace)
- [ ] Probar lectura de Silver Iceberg desde Glue

---

## Fase 4: Configuración Real de los Pipelines

### 4.1 Cuando tengas acceso a las tablas reales

Para cada tabla Silver que quieras procesar a Gold:

1. **Inspeccionar esquema:**
```bash
aws glue get-table --database-name silver --name ventas_procesadas
```

2. **Crear config específico por tabla:**
```
config/
  silver-to-gold-ventas.json       ← columnas de ventas
  silver-to-gold-clientes.json     ← columnas de clientes
  silver-to-gold-inventario.json   ← columnas de inventario
```

3. **Definir con el equipo de negocio:**
   - ¿Qué dimensiones necesitan los dashboards?
   - ¿Qué métricas necesitan calcular?
   - ¿Con qué granularidad? (día, semana, mes)

### 4.2 Activar procesamiento incremental

Una vez en producción con datos reales:
```json
"incremental": {
    "enabled": true,
    "timestamp_column": "<columna_real_que_existe>",
    "metadata_bucket": "data-lake-metadata",
    "metadata_key": "silver-to-gold/<nombre_tabla>/last_timestamp.json"
}
```

**Checklist Fase 4:**
- [ ] Inspeccionar esquemas reales de tablas Silver
- [ ] Reunión con equipo de negocio para definir métricas Gold
- [ ] Crear configs específicos por tabla
- [ ] Activar `incremental.enabled: true` con columna timestamp correcta
- [ ] Un `metadata_key` diferente por cada tabla

---

## Fase 5: Monitoreo y Observabilidad

### 5.1 CloudWatch Logs

Agregar logging estructurado en cada módulo:
```python
import boto3
cloudwatch = boto3.client('logs', region_name='us-east-1')

# Al finalizar cada módulo
cloudwatch.put_metric_data(
    Namespace='ETL/SilverToGold',
    MetricData=[{
        'MetricName': 'RecordsProcessed',
        'Value': record_count,
        'Unit': 'Count'
    }]
)
```

### 5.2 Alertas

Configurar alarmas en CloudWatch para:
- Pipeline con 0 registros procesados
- Error rate > 0 en cualquier módulo
- Tiempo de ejecución > umbral definido

**Checklist Fase 5:**
- [ ] Agregar métricas CloudWatch a cada módulo Gold
- [ ] Crear dashboard CloudWatch con métricas del pipeline
- [ ] Configurar alarma SNS si pipeline falla
- [ ] Configurar alarma si Gold tiene 0 registros

---

## Fase 6: Orquestación y Scheduling

### 6.1 AWS Glue Workflows

Crear un workflow que ejecute los jobs en orden:

```
Trigger (schedule o evento S3)
    ↓
Glue Job: bronze-to-silver
    ↓ (solo si exitoso)
Glue Job: silver-to-gold
    ↓ (solo si exitoso)
CloudWatch: notificación éxito
```

### 6.2 Schedule recomendado

| Pipeline | Frecuencia | Justificación |
|---|---|---|
| Bronze → Silver | Cada hora | Procesa datos raw rápido |
| Silver → Gold | Una vez al día | Métricas de negocio diarias |

**Checklist Fase 6:**
- [ ] Crear Glue Workflow en Terraform
- [ ] Configurar trigger por schedule (EventBridge)
- [ ] Configurar dependencia Silver-to-Gold espera a Bronze-to-Silver
- [ ] Probar workflow completo en AWS

---

## Fase 7: Testing en Producción

### 7.1 Tests unitarios pendientes

```
etl-silver-to-gold/tests/
  test_incremental_processor.py
  test_silver_to_gold_aggregator.py
  test_denormalization_engine.py
```

### 7.2 Test end-to-end en AWS

```bash
# 1. Subir datos de prueba a Bronze real
aws s3 cp tests/fixtures/sample_ventas_lines.json \
  s3://data-lake-bronze/ventas/

# 2. Ejecutar workflow completo
aws glue start-workflow-run --name etl-pipeline-workflow

# 3. Verificar Gold
aws s3 ls s3://data-lake-gold/ventas_agregadas/ --recursive
```

**Checklist Fase 7:**
- [ ] Tests unitarios para los 3 módulos Gold
- [ ] Property-based tests con Hypothesis (Propiedades 1-6 del design.md)
- [ ] Test end-to-end en AWS con datos reales
- [ ] Validar métricas Gold contra cálculos manuales

---

## Resumen de Prioridades

| Prioridad | Tarea | Fase |
|---|---|---|
| 🔴 Alta | Terraform bucket Gold + metadata | 1 |
| 🔴 Alta | `main_job_gold.py` para Glue | 2 |
| 🔴 Alta | Configurar Iceberg en producción | 3 |
| 🟡 Media | Configs reales por tabla | 4 |
| 🟡 Media | CloudWatch métricas y alertas | 5 |
| 🟢 Normal | Glue Workflow + scheduling | 6 |
| 🟢 Normal | Tests unitarios Gold | 7 |

---

## Lo que NO cambia al ir a producción

- Los módulos `IncrementalProcessor`, `SilverToGoldAggregator`, `DenormalizationEngine` — mismo código
- La lógica de transformación — idéntica
- Los configs `.json` — solo cambian valores, no estructura

**El código está listo. Lo que falta es infraestructura y configuración.**

---

*Última actualización: 19 Febrero 2026*
*Estado: Bronze→Silver→Gold funcionando en LocalStack ✅*