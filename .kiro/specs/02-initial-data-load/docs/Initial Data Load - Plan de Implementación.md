# Initial Data Load - Plan de Implementación

**Fecha**: 15 de enero de 2026  
**Versión**: 1.0  
**Estado**: Plan Completado - Implementación Pendiente

## Resumen Ejecutivo

Este documento describe el plan de implementación completo para la **Carga Inicial de Datos Históricos** desde MySQL-Janis hacia el Data Lake de Cencosud en AWS, con carga final en Amazon Redshift.

### Características Clave

- **Enfoque**: Extracción directa MySQL → S3 Gold → Redshift (bypass Bronze/Silver para migración única)
- **Procesamiento**: Paralelo con hasta 10 workers concurrentes
- **Formato**: Parquet con compresión Snappy optimizado para Redshift COPY
- **Validación**: Reconciliación completa con checksums y conteos
- **Seguridad**: Cifrado end-to-end, IAM authentication, audit logging
- **Tiempo Estimado**: 18-26 horas de ejecución después de completar código

## Arquitectura de la Solución

### Flujo de Datos

```
MySQL-Janis (Backup)
    ↓
Schema Analysis & Validation
    ↓
Parallel Extraction Workers (10x)
    ↓ (Streaming + Transformación)
S3 Gold Layer (Parquet)
    ↓ (Manifest Files)
Redshift COPY Command
    ↓
Validation & Reconciliation
    ↓
Atomic Cutover
```

### Componentes Principales

1. **Schema Analysis Module**
   - Analiza esquemas de Redshift y MySQL
   - Genera matriz de compatibilidad
   - Identifica conversiones necesarias

2. **Source Data Validation Module**
   - Valida existencia de 25 tablas esperadas
   - Verifica calidad de datos (duplicados, NULLs, fechas)
   - Chequea integridad referencial

3. **Data Type Conversion Module**
   - BIGINT Unix timestamp → TIMESTAMP ISO 8601
   - TINYINT(1) → BOOLEAN
   - VARCHAR/TEXT → VARCHAR(65535)
   - DATETIME → TIMESTAMP

4. **Parallel Extraction Worker**
   - Streaming query execution
   - Batch processing (10,000 registros/batch)
   - Conversión y normalización en vuelo
   - Escritura optimizada a S3 Gold

5. **Manifest Generator**
   - Escanea archivos Parquet en S3
   - Genera manifests para Redshift COPY
   - Valida completitud de archivos

6. **Redshift Loader**
   - Crea tablas paralelas con sufijo "_new"
   - Ejecuta COPY commands con manifests
   - Maneja errores y reintentos

7. **Validation & Reconciliation Module**
   - Compara conteos MySQL vs Redshift
   - Valida conversiones de tipos
   - Genera checksums para tablas críticas
   - Identifica registros huérfanos

8. **Cutover Orchestrator**
   - Renombrado atómico de tablas
   - Scripts de rollback automáticos
   - Ejecución de ANALYZE

## Plan de Implementación

### Estructura de Tareas

El plan consta de **21 tareas principales** organizadas en fases:

#### Fase 1: Preparación (Tasks 1-4)
- Setup de infraestructura (S3, Secrets Manager, KMS, CloudWatch)
- Implementación de análisis de esquemas
- Validación de datos fuente
- **Checkpoint**: Revisión de resultados de validación

#### Fase 2: Transformación (Tasks 5-6)
- Módulo de conversión de tipos de datos
- Módulo de manejo de data gaps
- Campos calculados y NULL markers

#### Fase 3: Extracción (Tasks 7-9)
- Worker de extracción paralela
- Generador de manifests
- **Checkpoint**: Validación de componentes de extracción

#### Fase 4: Carga (Tasks 10-12)
- Loader de Redshift
- Módulo de validación y reconciliación
- Orchestrator de cutover

#### Fase 5: Resiliencia (Tasks 13-14)
- Manejo de errores y recuperación
- Retry logic con exponential backoff
- **Checkpoint**: Testing de manejo de errores

#### Fase 6: Observabilidad (Tasks 15-16)
- Módulo de monitoreo y métricas
- Módulo de seguridad y compliance
- Property tests para validación

#### Fase 7: Orquestación (Tasks 17-19)
- Orchestrator principal (AWS Glue Job)
- Scripts de deployment
- **Checkpoint**: Test end-to-end

#### Fase 8: Documentación (Tasks 20-21)
- Documentación operacional
- Runbooks de deployment y troubleshooting
- **Checkpoint**: Revisión de production readiness

### Testing Strategy

#### Property-Based Tests (23 tests)
Usando framework **Hypothesis** con mínimo 100 iteraciones:

- **Property 2**: Record Count Consistency
- **Property 3**: Data Type Conversion Correctness
- **Property 4**: Timestamp Normalization
- **Property 5**: File Size Optimization (64-128 MB)
- **Property 6**: Partition Structure Consistency
- **Property 7**: Manifest File Completeness
- **Property 8**: NOT NULL Constraint Preservation
- **Property 13**: Data Gap Handling Consistency
- **Property 14**: Encryption in Transit (TLS 1.2+)
- **Property 15**: Encryption at Rest (KMS)
- **Property 16**: Retry with Exponential Backoff
- **Property 17**: Processing State Persistence
- **Property 18**: Checksum Consistency
- **Property 20**: CloudWatch Metrics Emission
- **Property 21**: Critical Event Notification
- **Property 22**: Least Privilege Access
- **Property 23**: Audit Log Completeness

#### Unit Tests
- Schema analysis con esquemas conocidos
- Data validation con casos edge
- Redshift loader con mocks
- Cutover orchestrator con simulaciones

### Optimizaciones Clave

#### File Size Optimization
- **Target**: 64-128 MB por archivo Parquet
- **Compresión**: Snappy (balance velocidad/ratio)
- **Beneficio**: Optimiza Redshift COPY performance

#### Parallel Processing
- **Workers**: Hasta 10 concurrentes
- **Batch Size**: 10,000 registros por batch
- **Streaming**: Procesamiento en vuelo sin acumular en memoria

#### Partition Strategy
```
s3://gold/table_name/year=YYYY/month=MM/day=DD/
```
- Facilita queries incrementales futuras
- Optimiza lifecycle policies

## Manejo de Data Gaps

### Campos Calculados

```python
# items_substituted_qty
COUNT(items WHERE substitute_type = 'substitute')

# items_qty_missing
SUM(quantity - COALESCE(quantity_picked, 0))

# total_changes
amount - originalAmount
```

### Campos No Disponibles
- Marcados como NULL
- Metadata flag `_unavailable: true`
- Documentados en Data Gap Report

## Seguridad y Compliance

### Encryption
- **In Transit**: TLS 1.2+ para MySQL, S3, Redshift
- **At Rest**: S3 SSE-KMS, Redshift cluster encryption

### Authentication
- **MySQL**: IAM database authentication
- **AWS Services**: IAM roles con least privilege
- **Credentials**: AWS Secrets Manager con rotación

### Audit Logging
- MySQL query execution logs
- S3 file upload logs
- Redshift COPY command logs
- User access logs

## Monitoreo y Alertas

### CloudWatch Metrics
- `MySQL/RecordsExtracted`
- `S3/UploadThroughput`
- `S3/UploadSuccessRate`
- `Redshift/CopyDuration`
- `Redshift/CopySuccessRate`
- `Processing/TableDuration`

### CloudWatch Alarms
- MySQL connection failures
- S3 upload failures
- Redshift COPY failures
- Processing time thresholds
- High error rate (>1%)

### SNS Notifications
- Process start
- Process completion
- Critical errors
- Summary report

## Error Handling

### Retry Logic
- **Max Attempts**: 3
- **Backoff**: Exponential (1s, 2s, 4s, 8s, 16s)
- **Max Delay**: 60 segundos

### Processing State
- Guardado en S3 después de cada tabla
- Checkpoint con último ID procesado
- Restart desde punto de fallo

### Recovery Mechanisms
- Restart de tablas individuales
- Skip de tablas problemáticas
- Validación y reprocesamiento manual

## Cutover Strategy

### Atomic Rename
```sql
BEGIN TRANSACTION;
  ALTER TABLE orders RENAME TO orders_old;
  ALTER TABLE orders_new RENAME TO orders;
  ANALYZE orders;
COMMIT;
```

### Rollback Plan
```sql
BEGIN TRANSACTION;
  ALTER TABLE orders RENAME TO orders_failed;
  ALTER TABLE orders_old RENAME TO orders;
COMMIT;
```

## Validación y Reconciliación

### Record Count Comparison
```
MySQL Count vs Redshift Count
Tolerance: 0% (must match exactly)
```

### Data Type Validation
- Verificar conversiones aplicadas correctamente
- Validar NOT NULL constraints
- Verificar rangos de fechas preservados

### Checksum Validation
```python
# Tablas críticas
critical_tables = [
    'wms_orders',
    'wms_order_items',
    'wms_stores',
    'customers'
]

# Generar checksums
for table in critical_tables:
    mysql_checksum = calculate_checksum(mysql, table)
    redshift_checksum = calculate_checksum(redshift, table)
    assert mysql_checksum == redshift_checksum
```

### Reconciliation Report
- Total records loaded per table
- Data type conversion summary
- Orphaned records summary
- Processing time metrics
- File sizes and compression ratios

## Deployment

### Infrastructure (Terraform)
```bash
cd terraform/modules/initial-data-load
terraform init
terraform plan -var-file="prod.tfvars"
terraform apply -var-file="prod.tfvars"
```

### Glue Job Deployment
```bash
# Package code
cd glue/initial-data-load
zip -r initial-data-load.zip *.py

# Upload to S3
aws s3 cp initial-data-load.zip s3://cencosud-glue-scripts/

# Create/Update Glue job
aws glue create-job --name initial-data-load \
  --role GlueServiceRole \
  --command "Name=pythonshell,ScriptLocation=s3://cencosud-glue-scripts/initial-data-load.zip"
```

### Execution
```bash
# Start Glue job
aws glue start-job-run --job-name initial-data-load \
  --arguments '{
    "mysql_host": "mysql.janis.com",
    "mysql_database": "janis_prod",
    "s3_gold_bucket": "cencosud-datalake-gold",
    "redshift_cluster": "cencosud-redshift-prod"
  }'

# Monitor progress
aws glue get-job-run --job-name initial-data-load --run-id <run-id>
```

## Estimaciones

### Tiempo de Ejecución
- **Schema Analysis**: 30 minutos
- **Source Validation**: 1 hora
- **Extraction (25 tables)**: 12-18 horas
- **Manifest Generation**: 30 minutos
- **Redshift COPY**: 2-4 horas
- **Validation**: 1-2 horas
- **Cutover**: 15 minutos
- **Total**: 18-26 horas

### Recursos AWS
- **Glue Workers**: 10x G.1X (4 vCPU, 16 GB RAM cada uno)
- **S3 Storage**: ~500 GB (estimado para datos históricos)
- **Redshift**: Cluster existente de Cencosud
- **CloudWatch**: Logs y métricas estándar

### Costos Estimados (USD)
- **Glue**: ~$150-200 (20 horas x 10 workers)
- **S3**: ~$12/mes (500 GB)
- **Data Transfer**: ~$45 (500 GB out to Redshift)
- **CloudWatch**: ~$10/mes
- **Total One-Time**: ~$200-250

## Análisis de Esquema Redshift Completado ✅

**Fecha**: 17 de Febrero de 2026

Se ha completado un análisis exhaustivo del esquema de Redshift existente en Cencosud. Ver documentos:
- **Análisis Completo**: `../redshift_schema_analysis.md`
- **Resumen Ejecutivo**: `Análisis de Esquema Redshift - Resumen Ejecutivo.md`

### Hallazgos Clave

1. **Esquema de Destino Identificado**: `dl_cs_bi` (vacío, listo para datos de Janis)
2. **Patrones de Diseño**: Surrogate keys (`sk_*`), flags como `smallint`, naming conventions claras
3. **Conversiones Necesarias**: 
   - BIGINT (Unix timestamp) → TIMESTAMP
   - TINYINT(1) → SMALLINT (flags booleanos)
   - Generación de surrogate keys durante migración
4. **Cluster Info**: dl-desa, 2 nodos ra3.xlplus, us-east-1

### Tablas Existentes Analizadas

**Schema `dw_cencofcic`** (5 tablas):
- `dim_material` (62 columnas) - Dimensión de productos muy completa
- `dim_ean` (3 columnas) - Códigos de barras
- `dim_promocion` (14 columnas) - Promociones comerciales
- `dim_proveedor` (8 columnas) - Proveedores
- `fact_rcv` (1 columna) - Tabla de hechos incompleta

## Próximos Pasos

### Fase 1: Análisis y Mapeo (Semana 1)

1. **Obtener Esquema MySQL Janis** ⭐ CRÍTICO
   - Conectar a base de datos MySQL de Janis
   - Extraer DDL de 25 tablas esperadas
   - Documentar tipos de datos, constraints y relaciones
   - Identificar volumen de datos por tabla

2. **Crear Matriz de Compatibilidad MySQL → Redshift**
   - Mapear cada tabla MySQL a esquema Redshift
   - Identificar conversiones de tipos necesarias
   - Documentar transformaciones requeridas
   - Definir estrategia de surrogate keys

3. **Validar Esquema de Destino con Stakeholders**
   - Confirmar uso de esquema `dl_cs_bi` vs `dw_cencofcic`
   - Definir naming conventions finales
   - Aprobar estrategia de surrogate keys
   - Crear DDL de tablas de destino

### Fase 2: Implementación (Semanas 2-4)

4. **Implementar Task 1**: Setup de infraestructura
   - Crear estructura de directorios
   - Configurar Secrets Manager con credenciales MySQL
   - Setup KMS keys
   - Crear S3 Gold bucket

5. **Implementar Task 2**: Schema Analysis Module
   - Conectar a Redshift (read-only) ✅ Completado
   - Conectar a MySQL
   - Generar compatibility matrix automáticamente

6. **Implementar Task 3**: Source Data Validation
   - Validar 25 tablas en MySQL
   - Ejecutar data quality checks
   - Generar reporte de validación

7. **Checkpoint**: Revisar resultados con stakeholders

## Referencias

### Documentos Relacionados
- **Design**: `.kiro/specs/initial-data-load/design.md`
- **Requirements**: `.kiro/specs/initial-data-load/requirements.md`
- **Tasks**: `.kiro/specs/initial-data-load/tasks.md`
- **Architecture**: `Documento Detallado de Diseño Janis-Cenco.md` (Capítulo 4)

### Steering Files
- **Terraform Best Practices**: `.kiro/steering/Terraform Best Practices.md`
- **AWS Best Practices**: `.kiro/steering/Buenas practicas de AWS.md`
- **Tech Stack**: `.kiro/steering/tech.md`

---

**Última Actualización**: 15 de enero de 2026  
**Próxima Revisión**: Después de completar Tasks 1-4 (Preparación y Validación)
