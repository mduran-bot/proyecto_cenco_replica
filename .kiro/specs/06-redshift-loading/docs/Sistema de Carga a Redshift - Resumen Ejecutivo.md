# Sistema de Carga a Redshift - Resumen Ejecutivo

## Fecha de Actualización
15 de Enero, 2026

## Propósito

El Sistema de Carga a Redshift es el componente final del pipeline de datos Janis-Cencosud, responsable de transferir datos curados desde las capas Silver/Gold del Data Lake hacia el Amazon Redshift existente de Cencosud. Este sistema implementa una estrategia de migración sin downtime que permite validación paralela antes del cutover definitivo, garantizando compatibilidad total con la infraestructura actual y los sistemas BI dependientes.

## Arquitectura de Alto Nivel

### Componentes Principales

1. **AWS Glue Jobs**: Generación de manifests y lectura de snapshots de Iceberg
2. **Amazon MWAA (Airflow)**: Orquestación de workflows de carga
3. **Amazon EventBridge**: Scheduling inteligente de cargas (cada 15 minutos)
4. **Amazon DynamoDB**: Gestión de estado para cargas incrementales
5. **Amazon Redshift**: Data Warehouse destino con tablas de producción
6. **Amazon CloudWatch**: Monitoreo, métricas y alertas
7. **Amazon SNS**: Notificaciones de eventos críticos

### Flujo de Datos

```
Iceberg Silver/Gold → Glue Snapshot Reader → Manifest Generator → Redshift COPY → Staging Tables → Validation → UPSERT → Production Tables → Materialized Views → Power BI
```

### Proceso de Carga

1. **EventBridge** dispara DAG de MWAA cada 15 minutos (horario laboral) o cada 60 minutos (fuera de horario)
2. **Glue Job** consulta metadata de Iceberg para identificar cambios incrementales desde último snapshot
3. **Manifest Generator** crea archivos manifest JSON con paths de S3 de archivos Parquet
4. **COPY Command** carga datos desde S3 a tablas staging en Redshift usando manifest
5. **Data Quality Validator** ejecuta validaciones exhaustivas (row counts, checksums, constraints, referential integrity)
6. **UPSERT Executor** merge datos validados a tablas de producción usando MERGE o DELETE+INSERT
7. **Materialized View Manager** refresca vistas materializadas para BI
8. **State Manager** actualiza estado en DynamoDB con snapshot ID procesado

## Características Clave

### 1. Carga Incremental con Iceberg Snapshots
- Lectura eficiente de cambios usando metadata de Iceberg
- Identificación de archivos nuevos/modificados entre snapshots
- Generación de manifests con solo los archivos delta
- Tracking de último snapshot procesado en DynamoDB

### 2. Validación de Compatibilidad de Esquemas
- Extracción de esquemas desde Redshift (pg_table_def, pg_constraint)
- Comparación con esquemas de Iceberg desde Glue Data Catalog
- Validación de distribution keys, sort keys, compression encodings
- Fail-fast antes de cargar datos si hay incompatibilidades

### 3. Conversión de Tipos de Datos
- Mapeo completo Iceberg → Redshift
- Conversión de timestamps con manejo de timezones (UTC → configured TZ)
- Preservación de precisión en DECIMAL/NUMERIC
- Determinación dinámica de longitudes VARCHAR basada en profiling

### 4. Tablas Staging para Validación
- Creación de tablas `_staging` con esquema idéntico a producción
- Carga aislada para validación sin impactar producción
- Preservación de distribution keys, sort keys y compression
- Cleanup automático después de merge exitoso

### 5. Validación de Calidad de Datos
- **Row Count Validation**: Source vs staging vs production delta
- **Checksum Validation**: Verificación de integridad de columnas críticas
- **Constraint Validation**: NOT NULL, rangos, formatos
- **Referential Integrity**: Validación de foreign keys
- **Anomaly Detection**: Comparación con baselines históricos

### 6. UPSERT Atómico
- **MERGE Statement** (preferido): UPSERT atómico en Redshift 1.0.20+
- **DELETE+INSERT** (fallback): Para versiones anteriores de Redshift
- Transacciones explícitas para atomicidad
- Minimización de duración de locks
- Manejo de deadlocks y timeouts con retry

### 7. Vistas Materializadas para BI
- Pre-agregaciones para patrones comunes de consulta
- Refresh incremental cuando es posible
- Scheduling durante períodos de bajo uso (2-6 AM)
- Monitoreo de uso y cleanup de vistas no utilizadas

### 8. Gestión de Estado Persistente
- DynamoDB para tracking de snapshots procesados
- Idempotencia: prevención de cargas duplicadas
- Recovery desde fallas parciales
- Soporte para cargas concurrentes de diferentes tablas

### 9. Error Handling Robusto
- Clasificación de errores: connection, transaction, COPY, data quality
- Retry con exponential backoff (1s, 2s, 4s)
- Rollback automático en fallas
- Routing de registros fallidos a tablas de error
- Logging estructurado a CloudWatch

### 10. Monitoreo y Alertas Comprehensivo
- Dashboards en tiempo real: load status, performance, data freshness
- Alarmas configurables: failures, degradation, capacity
- Notificaciones SNS para eventos críticos
- Lambda para alertas personalizadas y análisis de tendencias

## Componentes de Implementación

### Python Classes (Glue Jobs)

| Componente | Responsabilidad | Archivo |
|------------|-----------------|---------|
| IcebergSnapshotReader | Lectura de metadata de Iceberg y generación de manifests | `glue/redshift-loading/iceberg_reader.py` |
| SchemaValidator | Validación de compatibilidad de esquemas | `glue/redshift-loading/schema_validator.py` |
| DataTypeMapper | Conversión de tipos Iceberg → Redshift | `glue/redshift-loading/type_mapper.py` |
| StagingTableManager | Gestión de tablas staging | `glue/redshift-loading/staging_manager.py` |
| CopyExecutor | Ejecución de comandos COPY optimizados | `glue/redshift-loading/copy_executor.py` |
| DataQualityValidator | Validaciones de calidad de datos | `glue/redshift-loading/quality_validator.py` |
| UpsertExecutor | Ejecución de MERGE/DELETE+INSERT | `glue/redshift-loading/upsert_executor.py` |
| StateManager | Gestión de estado en DynamoDB | `glue/redshift-loading/state_manager.py` |
| MaterializedViewManager | Gestión de vistas materializadas | `glue/redshift-loading/mv_manager.py` |
| ConnectionPoolManager | Pool de conexiones a Redshift | `glue/shared/redshift_utils/connection_pool.py` |

### Airflow DAGs (MWAA)

| DAG | Propósito | Trigger |
|-----|-----------|---------|
| dag_redshift_loader.py | Orquestación de carga incremental | EventBridge (schedule_interval=None) |

**Tareas del DAG**:
1. `check_new_snapshots`: Verificar si hay nuevos snapshots en Iceberg
2. `run_glue_job`: Ejecutar Glue job de carga
3. `validate_load`: Validar resultados de carga
4. `refresh_views`: Refrescar vistas materializadas si necesario

### Terraform Modules

| Módulo | Recursos | Ubicación |
|--------|----------|-----------|
| glue-redshift-loader | Glue job, IAM role, Glue connections | `terraform/modules/glue/` |
| dynamodb-state | DynamoDB table para state management | `terraform/modules/dynamodb/` |
| eventbridge-scheduler | EventBridge rules para scheduling | `terraform/modules/eventbridge/` |
| cloudwatch-monitoring | Log groups, alarms, dashboards, SNS topics | `terraform/modules/cloudwatch/` |
| iam-redshift-loading | IAM roles y policies | `terraform/modules/iam/` |

## Propiedades de Correctness

El sistema implementa 12 propiedades de correctness que garantizan comportamiento correcto:

### Schema y Metadata (Properties 1-2)
- Preservación exacta de metadata de esquemas (columnas, tipos, constraints, keys)
- Compatibilidad con objetos dependientes (views, procedures, functions)

### Tipos de Datos (Property 3)
- Conversión correcta de todos los tipos Iceberg → Redshift
- Preservación de precisión y valores semánticos

### Procesamiento Incremental (Properties 4-5)
- Identificación correcta de archivos delta entre snapshots
- Generación completa y válida de manifests

### Staging y Validación (Property 6)
- Identidad de esquema entre staging y producción

### Calidad de Datos (Properties 7-10)
- Invariante de row count (source = staging = production delta)
- Invariante de checksum para columnas críticas
- Satisfacción de constraints (NOT NULL, ranges, formats)
- Preservación de integridad referencial

### Transacciones (Property 11)
- Atomicidad completa: all-or-nothing commits

### Error Handling (Property 12)
- Routing completo de registros fallidos con metadata

## Performance SLA

| Operación | Target | Volumen Máximo |
|-----------|--------|----------------|
| Snapshot Reading | 30 segundos | 1,000 archivos |
| Manifest Generation | 10 segundos | 1,000 archivos |
| COPY to Staging | 5 minutos | 1M records |
| Data Quality Validation | 2 minutos | 1M records |
| UPSERT to Production | 3 minutos | 100K records |
| End-to-End Load | 15 minutos | 1M records |

**Throughput Mínimo**: 100,000 records/minuto para COPY operations

## Configuración de AWS Glue

### Job Configuration

```python
glue_job_config = {
    "GlueVersion": "4.0",
    "WorkerType": "G.1X",  # 4 vCPU, 16 GB RAM
    "NumberOfWorkers": 2,  # Mínimo
    "MaxCapacity": 10,     # Auto-scaling hasta 10 workers
    "Timeout": 30,         # 30 minutos
    "MaxRetries": 3,
    "ExecutionProperty": {
        "MaxConcurrentRuns": 5  # Permitir cargas concurrentes de diferentes tablas
    }
}
```

### Connection Pool Configuration

```python
pool_config = {
    'min_connections': 2,
    'max_connections': 10,
    'connection_timeout': 30,
    'idle_timeout': 300,
    'max_lifetime': 3600
}
```

## Scheduling Strategy

### EventBridge Rules

**Business Hours** (8 AM - 8 PM):
- Frecuencia: Cada 15 minutos
- Cron: `cron(0/15 8-20 * * ? *)`
- Rationale: Alta frecuencia para datos frescos durante horario laboral

**Off-Hours** (8 PM - 8 AM):
- Frecuencia: Cada 60 minutos
- Cron: `cron(0 20-7 * * ? *)`
- Rationale: Reducir overhead de MWAA durante bajo uso

## Estrategia de Migración

### Fase 1: Validación Paralela (2 semanas)

**Objetivo**: Ejecutar pipeline nuevo en paralelo sin impactar producción

**Implementación**:
1. Deploy de infraestructura (Glue, MWAA, EventBridge, DynamoDB)
2. Crear tablas staging con sufijo `_new`
3. Cargar datos a tablas paralelas en mismo schedule que pipeline existente
4. Comparar datos entre tablas old y new:
   - Row counts
   - Checksums
   - Sample data validation
5. Monitorear performance y error rates
6. Iterar en fixes sin impactar producción

**Criterios de Éxito**:
- 99.9% data match rate entre pipelines old y new
- Load times dentro de SLA de 15 minutos
- Zero impacto en producción

### Fase 2: Preparación de Cutover (1 semana)

**Objetivo**: Preparar cutover a producción con mínimo downtime

**Implementación**:
1. Programar ventana de cutover (ej: Domingo 2-6 AM)
2. Preparar y probar procedimientos de rollback
3. Crear runbook de cutover con pasos detallados
4. Notificar a usuarios BI de ventana de mantenimiento
5. Preparar dashboards de monitoreo para validación de cutover
6. Conducir dry-run de cutover en ambiente staging

**Criterios de Éxito**:
- Procedimiento de rollback probado y validado
- Todos los stakeholders notificados
- Runbook revisado y aprobado

### Fase 3: Cutover a Producción (ventana de 4 horas)

**Objetivo**: Cambiar de pipeline old a new con mínimo downtime

**Procedimiento**:
1. **T-0:00**: Detener pipeline old (MySQL→Redshift)
2. **T-0:05**: Ejecutar carga final desde pipeline old
3. **T-0:15**: Renombrar tablas:
   - `orders` → `orders_old`
   - `orders_new` → `orders`
4. **T-0:20**: Actualizar materialized views para apuntar a tablas nuevas
5. **T-0:30**: Ejecutar smoke tests en tablas nuevas
6. **T-0:45**: Habilitar pipeline nuevo (EventBridge + MWAA)
7. **T-1:00**: Monitorear primera carga automatizada
8. **T-2:00**: Validar dashboards y reportes BI
9. **T-4:00**: Declarar cutover completo o ejecutar rollback

**Procedimiento de Rollback** (si necesario):
1. Detener pipeline nuevo
2. Renombrar tablas: `orders` → `orders_new`, `orders_old` → `orders`
3. Reiniciar pipeline old (MySQL→Redshift)
4. Validar dashboards BI
5. Investigar issues y reprogramar cutover

**Criterios de Éxito**:
- Todas las tablas renombradas exitosamente
- Primera carga automatizada completa exitosamente
- Dashboards BI muestran datos correctos
- Sin pérdida o corrupción de datos

### Fase 4: Monitoreo y Optimización (ongoing)

**Objetivo**: Monitorear pipeline nuevo y optimizar performance

**Implementación**:
1. Monitorear métricas CloudWatch diariamente durante primera semana
2. Revisar error logs y resolver issues
3. Optimizar queries lentos identificados por usuarios BI
4. Ajustar WLM queues basado en patrones de uso reales
5. Ajustar schedules de refresh de materialized views
6. Decomisionar pipeline old después de 30 días de operación estable

**Criterios de Éxito**:
- Load SLA cumplido 99% del tiempo
- Zero incidentes de calidad de datos
- Satisfacción de usuarios BI mantenida o mejorada

## Operaciones y Mantenimiento

### Procedimientos Operacionales Diarios

**Morning Checks (9 AM)**:
1. Revisar CloudWatch dashboard para cargas nocturnas
2. Verificar alertas de cargas fallidas o calidad de datos
3. Validar data freshness (último timestamp de carga)
4. Revisar tabla de errores para registros fallidos

**Load Monitoring**:
- Cargas cada 15 minutos durante horario laboral (8 AM - 8 PM)
- Cargas cada hora fuera de horario (8 PM - 8 AM)
- Monitorear duración de carga y alertar si excede 10 minutos

### Comandos Útiles

**Trigger Manual de Job**:
```bash
aws glue start-job-run \
  --job-name janis-cencosud-redshift-loader-prod \
  --arguments '{"--table_name":"orders","--target_environment":"prod"}'
```

**Ver Logs de Job**:
```bash
aws logs tail /aws-glue/jobs/output --follow
```

**Verificar Estado en DynamoDB**:
```bash
aws dynamodb get-item \
  --table-name redshift-load-state \
  --key '{"table_name":{"S":"orders"}}'
```

**Verificar Tablas de Error**:
```sql
SELECT error_type, COUNT(*) as error_count
FROM redshift_load_errors
WHERE load_date >= CURRENT_DATE - 7
GROUP BY error_type
ORDER BY error_count DESC;
```

**Reprocessar desde DLQ**:
```bash
aws glue start-job-run \
  --job-name janis-cencosud-dlq-reprocessor-prod \
  --arguments '{"--error_table":"redshift_load_errors","--date":"2026-01-15"}'
```

## Seguridad

### Network Security
- Glue jobs ejecutan en subnets privadas
- VPC endpoints para S3 y Redshift (evitar NAT Gateway)
- Security groups restrictivos (solo outbound necesario)
- Redshift en subnet privada sin acceso público

### Data Security
- Cifrado en reposo: Usar configuración existente de Redshift (KMS o hardware)
- Cifrado en tránsito: SSL/TLS para todas las conexiones a Redshift
- Manifest files en S3 con SSE-S3
- DynamoDB con encryption at rest (AWS-managed keys)

### Access Control
- IAM roles separados para Glue, MWAA, y Redshift
- Principio de menor privilegio
- No wildcard permissions en producción
- Auditoría completa con CloudTrail

## Monitoreo y Alertas

### CloudWatch Dashboards

**Dashboard 1: Real-time Load Status**
- Current loads in progress
- Success rate (last 24 hours)
- Average load duration
- Records loaded per table

**Dashboard 2: Historical Trends**
- Daily load counts
- Performance over time
- Error rates by type
- Data freshness by table

**Dashboard 3: Data Quality**
- Quality scores by table
- Constraint violations
- Referential integrity issues
- Anomaly detection alerts

**Dashboard 4: Resource Utilization**
- Glue worker usage
- Redshift query queue depth
- DynamoDB read/write capacity
- S3 request rates

### CloudWatch Alarms

**Critical Alarms** (notificación inmediata):
- Load failure rate > 5% en 15 minutos
- Data quality score degradation > 5% en 15 minutos
- Error table record count > 100
- Load duration > 20 minutos

**Warning Alarms** (notificación en horario laboral):
- Load duration > 15 minutos por 30 minutos
- Data quality score degradation > 2% en 1 hora
- Error table record count > 10
- Redshift storage > 80% capacity

## Plan de Implementación

El plan de implementación detallado se encuentra en `.kiro/specs/redshift-loading/tasks.md` y consta de 26 tareas principales organizadas en fases:

### Fase 1: Componentes Core (Tasks 1-8)
- Setup de estructura de proyecto
- Implementación de Iceberg Snapshot Reader
- Implementación de Schema Compatibility Validator
- Implementación de Data Type Mapper
- Implementación de Staging Table Manager
- Implementación de COPY Command Executor

### Fase 2: Validación y UPSERT (Tasks 9-12)
- Implementación de Data Quality Validator
- Implementación de UPSERT Executor
- Implementación de State Manager

### Fase 3: Vistas y Error Handling (Tasks 13-14)
- Implementación de Materialized View Manager
- Implementación de Error Handling y Recovery

### Fase 4: Orquestación (Tasks 15-18)
- Implementación de AWS Glue Job
- Implementación de MWAA DAG
- Implementación de EventBridge Scheduling

### Fase 5: Monitoreo e Infraestructura (Tasks 19-21)
- Implementación de monitoring y alerting
- Implementación de Terraform infrastructure

### Fase 6: Integraciones y Operaciones (Tasks 22-26)
- Optimizaciones para Power BI
- Backup y disaster recovery
- Cost optimization
- Documentación operacional
- Validación end-to-end

## Testing Strategy

### Property-Based Testing
- Framework: Hypothesis para Python
- Mínimo 100 iteraciones por property test
- Validación de 12 propiedades de correctness
- Tests marcados con `*` son opcionales para MVP rápido

### Unit Testing
- Testing de componentes individuales
- Edge cases y error conditions
- Integration points (S3, Redshift, DynamoDB, Glue Catalog)

### Integration Testing
- End-to-end load cycle completo
- Validación de data quality reports
- Testing de error recovery scenarios
- Performance testing con volúmenes máximos

## Próximos Pasos

1. **Implementación Fase 1**: Desarrollar componentes core (Snapshot Reader, Schema Validator, Type Mapper)
2. **Testing Unitario**: Validar cada componente individualmente
3. **Implementación Fase 2**: Desarrollar validación y UPSERT
4. **Integration Testing**: Validar end-to-end en ambiente dev
5. **Implementación Fase 3-5**: Completar orquestación, monitoreo e infraestructura
6. **Parallel Validation**: Ejecutar en paralelo con pipeline existente (2 semanas)
7. **Production Cutover**: Migración a producción con rollback plan

## Referencias

- **Especificación Completa**: `.kiro/specs/redshift-loading/design.md`
- **Requerimientos**: `.kiro/specs/redshift-loading/requirements.md`
- **Plan de Implementación**: `.kiro/specs/redshift-loading/tasks.md`
- **Arquitectura General**: `Documento Detallado de Diseño Janis-Cenco.md`
- **Sistemas Upstream**: `Sistema de Transformación de Datos - Resumen Ejecutivo.md`