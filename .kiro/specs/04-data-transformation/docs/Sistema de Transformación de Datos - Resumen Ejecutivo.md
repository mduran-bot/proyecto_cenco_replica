# Sistema de Transformación de Datos - Resumen Ejecutivo

## Fecha de Actualización
15 de Enero, 2026

## Propósito

El Sistema de Transformación de Datos implementa una arquitectura de medallion (Bronze → Silver → Gold) que procesa y refina datos desde su estado raw hasta datos curados listos para consumo de BI. El sistema utiliza AWS Glue como motor ETL serverless y Apache Iceberg como formato de tabla para proporcionar transacciones ACID, time travel y schema evolution sin reescritura de datos.

Este sistema es el corazón del Data Lake, transformando datos crudos de webhooks y polling en información de alta calidad para análisis de negocio.

## Arquitectura de Alto Nivel

### Componentes Principales

1. **AWS Glue ETL Jobs**: Motor de procesamiento serverless con auto-scaling
2. **Apache Iceberg Tables**: Formato de tabla con capacidades ACID y time travel
3. **AWS Glue Data Catalog**: Catálogo centralizado de metadatos y esquemas
4. **Amazon S3**: Almacenamiento de datos en capas Bronze/Silver/Gold
5. **Amazon CloudWatch**: Monitoreo, métricas y alertas de calidad
6. **Dead Letter Queue (S3)**: Captura de registros fallidos para reprocessamiento

### Flujo de Datos

```
S3 Bronze Layer → Glue Bronze-to-Silver Jobs → Iceberg Silver Tables → Glue Silver-to-Gold Jobs → Iceberg Gold Tables → Redshift
        ↓                    ↓                           ↓                        ↓
   Raw JSON          Data Cleansing              Deduplication            Aggregation
   Partitioned       Type Conversion             Quality Gates            Denormalization
                     Normalization               Lineage Tracking         BI Optimization
```

## Capas del Data Lake

### Bronze Layer (Datos Raw)
- **Contenido**: Datos sin procesar, réplica exacta de las fuentes
- **Formato**: JSON comprimido con GZIP
- **Particionamiento**: Por tipo de entidad y fecha de ingesta
- **Retención**: 365 días (Standard → IA → Glacier → Delete)
- **Propósito**: Preservar datos originales para auditoría y reprocessamiento

### Silver Layer (Datos Limpios)
- **Contenido**: Datos normalizados, deduplicados y validados
- **Formato**: Apache Iceberg con Parquet + Snappy compression
- **Particionamiento**: Hidden partitioning por fecha y business keys
- **Características**: Transacciones ACID, time travel, schema evolution
- **Propósito**: Datos confiables para análisis y transformaciones downstream

### Gold Layer (Datos Curados)
- **Contenido**: Datos agregados, denormalizados y optimizados para BI
- **Formato**: Apache Iceberg con Parquet optimizado
- **Tablas**: Daily Sales Summary, Order Fulfillment Metrics, Product Performance
- **Actualización**: Incremental cada hora
- **Propósito**: Datos listos para consumo directo en Power BI y dashboards

## Ventajas de la Arquitectura

### Apache Iceberg sobre Parquet Plano
- **Transacciones ACID**: Garantiza consistencia de datos incluso con escrituras concurrentes
- **Time Travel**: Consultar datos históricos sin duplicar storage
- **Schema Evolution**: Agregar/modificar columnas sin reescribir datos
- **Hidden Partitioning**: Particionamiento automático sin exponer en queries
- **Optimización Automática**: Compactación de archivos pequeños en background

### AWS Glue Serverless
- **Auto-scaling**: De 2 a 10 workers según carga de trabajo
- **Pago por uso**: Solo se paga por tiempo de ejecución real
- **Integración nativa**: Con S3, Iceberg y Data Catalog
- **Job Bookmarks**: Procesamiento incremental automático
- **Spark UI**: Debugging y optimización de performance

### Arquitectura Medallion
- **Separación de responsabilidades**: Cada capa tiene un propósito claro
- **Reprocessamiento flexible**: Regenerar Silver/Gold desde Bronze sin pérdida
- **Debugging simplificado**: Inspeccionar datos en cada etapa de transformación
- **Auditoría completa**: Trazabilidad desde raw hasta curado

## Características Clave

### 1. Conversión de Tipos de Datos
- MySQL BIGINT (timestamps) → Iceberg TIMESTAMP
- MySQL TINYINT(1) → Iceberg BOOLEAN
- MySQL VARCHAR → Iceberg STRING
- MySQL DECIMAL → Iceberg DECIMAL con precisión preservada
- MySQL JSON → Iceberg STRING (flattened en columnas individuales)

### 2. Normalización de Formatos
- Timestamps: Conversión a formato 'YYYY-MM-DD HH:MM:SS' UTC
- Emails: Validación con regex y normalización lowercase
- Teléfonos: Formato estándar +56XXXXXXXXX
- Strings: Trim de whitespace, conversión de empty strings a NULL

### 3. Deduplicación Inteligente
- Detección por business keys (order_id, product_id, sku_id)
- Resolución de conflictos por timestamp más reciente
- Prioridad de fuente: webhook > polling
- Auditoría completa de decisiones de deduplicación

### 4. Manejo de Data Gaps
- Identificación de campos faltantes según mapping
- Cálculo de campos derivados cuando sea posible
- Anotación con metadata (data_gap_flag, gap_reason)
- Reportes de gaps para análisis de calidad

### 5. Validación de Calidad de Datos
- Validación de nulls en campos críticos
- Validación de tipos de datos
- Validación de rangos y formatos
- Quality gates que bloquean datos de baja calidad
- Métricas: Completeness, Validity, Consistency, Accuracy

### 6. Schema Evolution Segura
- Detección automática de cambios de esquema
- Validación antes de aplicar cambios
- Versionado de esquemas en Glue Data Catalog
- Alertas para cambios que requieren intervención manual
- Rollback capability a versiones anteriores

### 7. Error Handling y Recovery
- Clasificación de errores (retryable, quality, fatal, partial)
- Retry con exponential backoff (3 intentos)
- Checkpointing cada 1,000 registros
- Dead Letter Queue para registros fallidos
- Reprocessamiento manual desde DLQ

### 8. Data Lineage Completo
- Rastreo de transformaciones Bronze → Silver → Gold
- Metadata de cada operación (job ID, timestamp, rules applied)
- Trazabilidad a nivel de registro individual
- Integración con herramientas de governance

## Transformaciones Bronze-to-Silver

### Componentes de Procesamiento

| Componente | Responsabilidad | Tecnología |
|------------|-----------------|------------|
| DataTypeConverter | Conversión de tipos MySQL a Redshift | PySpark |
| DataNormalizer | Normalización de formatos | PySpark + Regex |
| DataCleaner | Limpieza de datos (trim, null conversion) | PySpark |
| JSONFlattener | Aplanamiento de estructuras JSON anidadas | PySpark |
| DeduplicationEngine | Eliminación de duplicados | Iceberg MERGE |
| DataGapHandler | Manejo de campos faltantes | PySpark |
| IcebergWriter | Escritura transaccional a Iceberg | PyIceberg |

### Flujo de Procesamiento

1. **Lectura**: Leer datos JSON desde S3 Bronze con job bookmarks
2. **Conversión**: Convertir tipos de datos MySQL a tipos Iceberg
3. **Normalización**: Normalizar formatos de timestamps, emails, teléfonos
4. **Limpieza**: Aplicar reglas de limpieza (trim, null conversion)
5. **Flattening**: Aplanar estructuras JSON anidadas en columnas
6. **Deduplicación**: Identificar y resolver duplicados por business key
7. **Gap Handling**: Calcular campos derivados y anotar gaps
8. **Validación**: Ejecutar quality checks y calcular métricas
9. **Escritura**: Escribir a Iceberg Silver con transacción ACID
10. **Lineage**: Registrar metadata de transformación

## Transformaciones Silver-to-Gold

### Agregaciones Predefinidas

**Daily Sales Summary**:
```sql
SELECT 
    date,
    store_id,
    product_category,
    COUNT(DISTINCT order_id) as total_orders,
    SUM(amount) as total_revenue,
    AVG(amount) as avg_order_value,
    SUM(items_qty) as total_items_sold,
    COUNT(DISTINCT customer_id) as unique_customers
FROM silver.orders
GROUP BY date, store_id, product_category
```

**Order Fulfillment Metrics**:
```sql
SELECT
    date,
    store_id,
    COUNT(*) as total_orders,
    SUM(CASE WHEN status = 'delivered' THEN 1 ELSE 0 END) as delivered_orders,
    AVG(DATEDIFF(delivered_date, created_date)) as avg_fulfillment_days,
    SUM(items_substituted_qty) as total_substitutions,
    SUM(items_qty_missing) as total_missing_items
FROM silver.orders
GROUP BY date, store_id
```

**Product Performance**:
```sql
SELECT
    product_id,
    product_name,
    category,
    SUM(quantity_sold) as total_quantity_sold,
    SUM(revenue) as total_revenue,
    AVG(unit_price) as avg_price,
    COUNT(DISTINCT order_id) as order_count,
    AVG(rating) as avg_rating
FROM silver.order_items oi
JOIN silver.products p ON oi.product_id = p.product_id
GROUP BY product_id, product_name, category
```

### Procesamiento Incremental

- **Job Bookmarks**: Glue rastrea última ejecución exitosa
- **Watermarking**: Procesar solo registros nuevos/modificados desde último run
- **Merge Strategy**: UPSERT en Gold tables basado en business keys
- **Efficiency**: Reduce tiempo de procesamiento en 90%+ vs. full refresh

## Esquemas de Datos

### Silver Layer Schema (Ejemplo: Orders)

```python
orders_silver_schema = StructType([
    # Business fields
    StructField("order_id", StringType(), nullable=False),
    StructField("date_created", TimestampType(), nullable=False),
    StructField("date_modified", TimestampType(), nullable=True),
    StructField("status", StringType(), nullable=False),
    StructField("amount", DecimalType(10, 2), nullable=False),
    StructField("customer_email", StringType(), nullable=True),
    StructField("customer_phone", StringType(), nullable=True),
    
    # Source tracking
    StructField("source", StringType(), nullable=False),  # webhook/polling
    StructField("ingestion_timestamp", TimestampType(), nullable=False),
    StructField("processing_timestamp", TimestampType(), nullable=False),
    
    # Data quality metadata
    StructField("data_gap_flag", BooleanType(), nullable=False),
    StructField("gap_reason", StringType(), nullable=True),
    
    # Audit fields
    StructField("etl_job_id", StringType(), nullable=False),
    StructField("record_version", IntegerType(), nullable=False)
])
```

### Particionamiento Iceberg

**Orders Table**:
- Particionamiento: `year(date_created)`, `month(date_created)`, `day(date_created)`
- Rationale: Queries típicamente filtran por rangos de fecha

**Products Table**:
- Particionamiento: `category`
- Rationale: Productos consultados por categoría para analytics

**Stock Table**:
- Particionamiento: `store_id`, `date`
- Rationale: Consultas de stock son específicas por tienda y fecha

## Calidad de Datos

### Métricas de Calidad

| Métrica | Definición | Threshold |
|---------|------------|-----------|
| Completeness | % de campos no-null en campos críticos | 99% |
| Validity | % de valores que cumplen formato esperado | 98% |
| Consistency | % de consistencia entre tablas relacionadas | 95% |
| Accuracy | % de valores dentro de rangos esperados | 97% |

### Quality Gates

- **Bronze-to-Silver**: Bloquear si completeness < 99% en campos críticos
- **Silver-to-Gold**: Bloquear si validity < 98% o consistency < 95%
- **Alertas**: Notificación inmediata si quality score cae > 5% en 15 minutos
- **DLQ**: Registros que fallan validación van a Dead Letter Queue

### Reportes de Calidad

- **Frecuencia**: Generados después de cada job execution
- **Contenido**: Quality scores por tabla y columna, trend analysis
- **Distribución**: CloudWatch Logs + S3 para análisis histórico
- **Alertas**: SNS notification si degradación detectada

## Monitoreo y Alertas

### Métricas Clave

**Job Metrics**:
- JobDuration: Duración de ejecución de jobs
- JobSuccessRate: Tasa de éxito de jobs
- RecordsProcessed: Cantidad de registros procesados
- RecordsPerMinute: Throughput de procesamiento
- WorkersUsed: Número de workers utilizados

**Quality Metrics**:
- CompletenessScore: Score de completitud de datos
- ValidityScore: Score de validez de formatos
- ConsistencyScore: Score de consistencia cross-table
- AccuracyScore: Score de precisión de valores
- QualityGateFailures: Cantidad de fallos de quality gates

**Resource Metrics**:
- CPUUtilization: Utilización de CPU
- MemoryUtilization: Utilización de memoria
- DiskIOUtilization: Utilización de I/O de disco
- NetworkBytesTransferred: Bytes transferidos por red

**Iceberg Metrics**:
- TableFileCount: Cantidad de archivos en tabla
- TableSizeBytes: Tamaño total de tabla
- SnapshotCount: Cantidad de snapshots históricos
- CompactionDuration: Duración de compactación

### Alarmas Críticas (Notificación Inmediata)

- Job failure rate > 5% en 15 minutos
- Quality score degradation > 5% en 15 minutos
- DLQ message count > 100
- Resource exhaustion (CPU > 90%, Memory > 85%)
- Schema evolution failure

### Alarmas de Warning (Notificación en Horas Laborales)

- Job duration > 2x baseline por 30 minutos
- Quality score degradation > 2% en 1 hora
- DLQ message count > 10
- Iceberg table file count > 10,000 (necesita compaction)

### Dashboard CloudWatch

- **Job Performance Panel**: Duración, success rate, throughput
- **Data Quality Panel**: Quality scores por tabla, trend analysis
- **Resource Utilization Panel**: CPU, memoria, I/O, network
- **Iceberg Health Panel**: File count, table size, snapshot count
- **Error Analysis Panel**: Error types, DLQ size, failed records

## Propiedades de Correctness

El sistema implementa 34 propiedades de correctness que garantizan comportamiento correcto:

### Transformación de Datos (Properties 1-5)
- Conversión correcta de tipos de datos MySQL a Redshift
- Normalización de formatos (timestamps, emails, teléfonos)
- Flattening correcto de estructuras JSON anidadas
- Aplicación de reglas de limpieza de datos
- Round-trip write-read preserva todos los valores

### Deduplicación (Properties 6-7)
- Detección de duplicados por business keys
- Resolución de conflictos basada en timestamps

### Data Gaps (Properties 8-10)
- Cálculo correcto de campos derivados
- Anotación de campos faltantes con metadata
- Manejo graceful de campos no-críticos faltantes

### Transacciones ACID (Properties 11-12)
- Operaciones atómicas y consistentes
- Time travel a snapshots históricos

### Agregaciones (Properties 13-14)
- Cálculos correctos de agregaciones Gold
- Procesamiento incremental eficiente

### Schema Evolution (Properties 15-20)
- Detección de cambios de esquema
- Evolución segura sin pérdida de datos
- Validación antes de aplicar cambios
- Versionado completo de esquemas
- Alertas para cambios unsafe
- Rollback capability

### Calidad de Datos (Properties 21-24)
- Ejecución de todas las validaciones configuradas
- Cálculo preciso de métricas de calidad
- Reportes completos de calidad
- Enforcement de quality gates

### Error Handling (Properties 25-30)
- Recovery desde checkpoints
- Manejo comprehensivo de errores
- Persistencia de estado de procesamiento
- Routing a DLQ con metadata completa
- Retry con exponential backoff
- Reprocessamiento manual desde DLQ

### Observabilidad (Properties 31-34)
- Publicación de métricas a CloudWatch
- Notificaciones de eventos críticos
- Trazabilidad completa de lineage
- Metadata completa de transformaciones

## Performance SLA

| Transformación | Target | Volumen Máximo |
|----------------|--------|----------------|
| Bronze-to-Silver Orders | 10 minutos | 100,000 records |
| Bronze-to-Silver Products | 5 minutos | 50,000 records |
| Bronze-to-Silver Stock | 8 minutos | 200,000 records |
| Silver-to-Gold Aggregations | 15 minutos | 1,000,000 records |
| Data Quality Validation | 5 minutos | 100,000 records |

**Throughput Mínimo**: 100,000 records/minuto para Bronze-to-Silver

## Configuración de AWS Glue

### Job Configuration

```python
glue_job_config = {
    "GlueVersion": "4.0",
    "WorkerType": "G.1X",  # 4 vCPU, 16 GB RAM
    "NumberOfWorkers": 2,  # Mínimo
    "MaxCapacity": 10,     # Auto-scaling hasta 10 workers
    "Timeout": 120,        # 2 horas
    "MaxRetries": 3,
    "ExecutionProperty": {
        "MaxConcurrentRuns": 1
    }
}
```

### Iceberg Configuration

```python
iceberg_config = {
    "format-version": "2",
    "write.format.default": "parquet",
    "write.parquet.compression-codec": "snappy",
    "write.target-file-size-bytes": "134217728",  # 128 MB
    "history.expire.max-snapshot-age-ms": "2592000000"  # 30 días
}
```

## Seguridad

### Network Security
- Glue jobs ejecutan en subnets privadas
- VPC endpoints para servicios AWS (S3, Glue Data Catalog)
- Security groups restrictivos (solo outbound necesario)

### Data Security
- Cifrado en reposo: S3 SSE-S3 (AES-256)
- Cifrado en tránsito: TLS 1.2+ para todas las comunicaciones
- Iceberg tables con encryption habilitado

### Access Control
- IAM roles separados para Bronze-to-Silver y Silver-to-Gold
- Principio de menor privilegio
- No wildcard permissions en producción
- Auditoría completa con CloudTrail

## Operaciones y Mantenimiento

### Procedimientos Operacionales

1. **Trigger Manual de Job**
   ```bash
   aws glue start-job-run --job-name bronze-to-silver-orders
   ```

2. **Ver Logs de Job**
   ```bash
   aws logs tail /aws-glue/jobs/output --follow
   ```

3. **Verificar DLQ**
   ```bash
   aws s3 ls s3://cencosud-datalake-dlq/data-transformation/
   ```

4. **Reprocessar desde DLQ**
   ```bash
   aws glue start-job-run \
     --job-name dlq-reprocessor \
     --arguments '{"--dlq-path":"s3://path/to/dlq/records"}'
   ```

5. **Rollback Iceberg Table**
   ```python
   from pyiceberg.catalog import load_catalog
   catalog = load_catalog("glue")
   table = catalog.load_table("silver.orders")
   table.rollback_to_snapshot(snapshot_id)
   ```

### Troubleshooting Común

- **Job timeout**: Aumentar timeout o reducir batch size
- **Out of memory**: Aumentar worker type o número de workers
- **Quality gate failures**: Revisar logs de validación, investigar fuente de datos
- **Schema evolution errors**: Verificar compatibilidad de cambios, usar rollback si necesario
- **DLQ accumulation**: Identificar patrón de errores, corregir causa raíz, reprocessar

## Plan de Implementación

El plan de implementación se encuentra detallado en `.kiro/specs/data-transformation/tasks.md` y consta de múltiples fases:

### Fase 1: Infraestructura Base
- Setup de Terraform para Glue jobs
- Configuración de Iceberg en Glue Data Catalog
- Setup de S3 buckets para Silver/Gold layers
- Configuración de IAM roles y policies

### Fase 2: Bronze-to-Silver Jobs
- Implementación de componentes de transformación
- Desarrollo de deduplication engine
- Implementación de data gap handler
- Testing con datos de desarrollo

### Fase 3: Silver-to-Gold Jobs
- Implementación de agregaciones predefinidas
- Desarrollo de procesamiento incremental
- Implementación de denormalization engine
- Testing de performance

### Fase 4: Calidad y Monitoreo
- Implementación de data quality validator
- Configuración de CloudWatch metrics y alarms
- Setup de data lineage tracking
- Implementación de error handling y DLQ

### Fase 5: Deployment y Operaciones
- Deployment a ambiente de producción
- Documentación de runbooks operacionales
- Training de equipo de operaciones
- Monitoreo intensivo post-deployment

## Testing Strategy

### Property-Based Testing
- Framework: Hypothesis para Python/PySpark
- Mínimo 100 iteraciones por property test
- Validación de 34 propiedades de correctness

### Unit Testing
- Testing de componentes individuales
- Edge cases y error conditions
- Integration points (S3, Iceberg, CloudWatch)

### Performance Testing
- Validación de throughput (100k records/min)
- Testing de auto-scaling de workers
- Stress testing con volúmenes máximos

## Próximos Pasos

1. **Implementación Fase 1**: Desplegar infraestructura base con Terraform
2. **Desarrollo Bronze-to-Silver**: Implementar transformaciones para orders
3. **Testing**: Validación end-to-end en ambiente dev
4. **Rollout Gradual**: Agregar productos, stock, prices progresivamente
5. **Silver-to-Gold**: Implementar agregaciones para BI
6. **Production Deployment**: Rollout a producción con monitoreo intensivo

## Referencias

- **Especificación Completa**: `.kiro/specs/data-transformation/design.md`
- **Requerimientos**: `.kiro/specs/data-transformation/requirements.md`
- **Plan de Implementación**: `.kiro/specs/data-transformation/tasks.md`
- **Arquitectura General**: `Documento Detallado de Diseño Janis-Cenco.md`
- **Sistemas Upstream**: `Sistema de Webhooks - Resumen Ejecutivo.md`, `Sistema de Polling API - Resumen Ejecutivo.md`

## Contacto

Para preguntas o soporte relacionado con el Sistema de Transformación de Datos, contactar al equipo de Data Engineering.
