# Arquitectura del Pipeline ETL Bronze → Silver → Gold

## 📋 Tabla de Contenidos

- [Visión General](#visión-general)
- [Arquitectura de Capas](#arquitectura-de-capas)
- [Flujo de Datos](#flujo-de-datos)
- [Módulos de Transformación](#módulos-de-transformación)
- [Decisiones de Diseño](#decisiones-de-diseño)

---

## Visión General

El pipeline ETL implementa una arquitectura moderna de Data Lake con tres capas (Bronze, Silver, Gold) que procesan datos desde el sistema WMS Janis hacia el Data Warehouse de Cencosud en AWS Redshift.

### Objetivos del Pipeline

- **Ingesta confiable**: Capturar todos los eventos de Janis sin pérdida
- **Transformación escalable**: Procesar grandes volúmenes de datos eficientemente
- **Calidad de datos**: Garantizar datos limpios y consistentes para BI
- **Auditoría completa**: Mantener historial de cambios para compliance

### Tecnologías Utilizadas

- **AWS Glue**: Motor ETL serverless con PySpark
- **Apache Iceberg**: Formato de tabla con transacciones ACID
- **Amazon S3**: Data Lake storage con particionamiento
- **AWS EventBridge**: Orquestación de pipelines
- **Amazon MWAA**: Airflow managed para workflows complejos

---

## Arquitectura de Capas

### 🟤 Capa Bronze (Raw Data)

**Propósito**: Almacenar datos crudos tal como llegan desde Janis

**Características**:
- **Inmutable**: Cada evento crea un nuevo archivo
- **Formato**: JSON con metadata wrapper
- **Particionamiento**: `{client_id}/orders/date={YYYY-MM-DD}/`
- **Retención**: Indefinida (auditoría y reprocessing)

**Estructura de Datos**:
```json
{
  "_metadata": {
    "client_id": "metro",
    "entity_type": "orders",
    "ingestion_timestamp": "2026-02-26 14:18:07",
    "source": "webhook|polling|initial_load",
    "api_version": "v2",
    "event_type": "order.created|order.updated",
    "version": 1
  },
  "data": {
    // Payload completo de Janis API
  }
}
```

**Ventajas**:
- ✅ Auditoría completa de todos los cambios
- ✅ Time travel: recuperar estado en cualquier momento
- ✅ Reprocessing sin pérdida de datos
- ✅ Debugging: ver datos originales sin transformar

---

### 🥈 Capa Silver (Clean Data)

**Propósito**: Datos limpios, normalizados y listos para análisis

**Características**:
- **Mutable**: UPSERT por clave primaria (order_id)
- **Formato**: JSON flat (42 columnas)
- **Particionamiento**: `{client_id}_orders_clean/`
- **Retención**: Última versión de cada registro

**Transformaciones Aplicadas**:

1. **JSONFlattener**: Aplanar estructuras nested
   - `data.customer.email` → `data_customer_email`
   - `data.items[]` → Array preservado
   - 42 columnas generadas

2. **DataCleaner**: Limpieza de datos
   - Trim de strings
   - Normalización de espacios
   - Eliminación de caracteres especiales

3. **DataNormalizer**: Normalización de valores
   - Emails a lowercase
   - Códigos a uppercase
   - Formatos consistentes

4. **DataTypeConverter**: Conversión de tipos
   - Unix timestamps → ISO 8601
   - Strings numéricos → números
   - Validación de tipos

5. **DataGapHandler**: Manejo de datos faltantes
   - Valores por defecto
   - Flags de datos incompletos
   - Estrategias de imputación

6. **DuplicateDetector**: Detección de duplicados
   - Deduplicación por order_id
   - Última versión gana (por timestamp)
   - Logging de duplicados encontrados

7. **ConflictResolver**: Resolución de conflictos
   - Merge de versiones conflictivas
   - Priorización de fuentes
   - Registro de conflictos

8. **IcebergManager**: Gestión de tablas Iceberg
   - UPSERT transaccional
   - Metadata de versiones
   - Compactación automática

**Estructura de Datos**:
```json
{
  "_metadata_api_version": "v2",
  "_metadata_client_id": "metro",
  "_metadata_entity_type": "orders",
  "_metadata_ingestion_timestamp": "2026-02-26T14:18:07",
  "_metadata_source": "webhook",
  "_processing_timestamp": "2026-02-26T14:18:54.993",
  "data_id": "ORD-METRO-001",
  "data_status": "confirmed",
  "data_customer_email": "customer@metro.com",
  "data_customer_firstName": "Juan",
  "data_totalAmount": 250.75,
  // ... 37 columnas más
}
```

**Ventajas**:
- ✅ Queries eficientes (datos flat)
- ✅ Última versión siempre disponible
- ✅ Transacciones ACID con Iceberg
- ✅ Schema evolution sin downtime

---

### 🥇 Capa Gold (Business Data)

**Propósito**: Datos optimizados para BI y análisis de negocio

**Características**:
- **Mutable**: UPSERT con agregaciones
- **Formato**: Parquet con compresión Snappy
- **Particionamiento**: `{client_id}/{entity}/year={YYYY}/month={MM}/day={DD}/`
- **Retención**: Última versión con métricas calculadas

**Transformaciones Aplicadas**:

1. **SchemaMapper**: Mapeo a esquema Redshift
   - Campos renombrados según convención
   - Tipos de datos compatibles con Redshift
   - Columnas calculadas

2. **BusinessRulesEngine**: Reglas de negocio
   - Cálculo de KPIs
   - Clasificaciones de negocio
   - Flags de alertas

3. **AggregationEngine**: Agregaciones
   - `total_changes`: Número de actualizaciones
   - `days_since_created`: Antigüedad del pedido
   - `last_status_change`: Última modificación

4. **DataQualityValidator**: Validación de calidad
   - Checks de integridad
   - Validación de rangos
   - Alertas de anomalías

5. **PartitionOptimizer**: Optimización de particiones
   - Particionamiento por fecha
   - Compactación de archivos pequeños
   - Eliminación de particiones vacías

**Estructura de Datos**:
```json
{
  "order_id": "ORD-METRO-001",
  "client_id": "metro",
  "status": "confirmed",
  "total_amount": 250.75,
  "customer_email": "customer@metro.com",
  "date_created": "2026-02-26T12:00:00Z",
  "date_modified": "2026-02-26T14:00:00Z",
  "total_changes": 2,
  "days_since_created": 0,
  "last_status_change": "2026-02-26T14:00:00Z",
  "_processing_timestamp": "2026-02-26T14:25:19.272652",
  "year": 2026,
  "month": 2,
  "day": 26
}
```

**Ventajas**:
- ✅ Performance óptimo para queries BI
- ✅ Campos calculados pre-computados
- ✅ Formato Parquet comprimido (menor costo)
- ✅ Listo para MERGE en Redshift

---

## Flujo de Datos

### Flujo Completo End-to-End

```
┌─────────────────────────────────────────────────────────────────┐
│                        JANIS WMS API                            │
│                    (Sistema Fuente)                             │
└────────────┬────────────────────────────────────────────────────┘
             │
             ├─── Webhooks (Tiempo Real)
             │    └─> API Gateway → Lambda → Kinesis Firehose
             │
             └─── Polling (Backup cada 15 min)
                  └─> EventBridge → MWAA → Lambda → S3
             │
             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    🟤 BRONZE LAYER (S3)                         │
│                                                                 │
│  Formato: JSON raw con metadata                                │
│  Comportamiento: INMUTABLE (append-only)                       │
│  Particionamiento: {client}/orders/date={YYYY-MM-DD}/          │
│                                                                 │
│  Ejemplo: s3://bronze/metro/orders/date=2026-02-26/            │
│    ├── part-00000-xxx.txt (v1 - pending)                       │
│    ├── part-00001-xxx.txt (v2 - confirmed)                     │
│    └── part-00002-xxx.txt (v3 - shipped)                       │
└────────────┬────────────────────────────────────────────────────┘
             │
             │ Trigger: EventBridge (cada 5 min) o Manual
             │ Job: etl-bronze-to-silver/run_pipeline.py
             │
             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    🥈 SILVER LAYER (S3)                         │
│                                                                 │
│  Formato: JSON flat (42 columnas)                              │
│  Comportamiento: MUTABLE (UPSERT por order_id)                 │
│  Particionamiento: {client}_orders_clean/                      │
│                                                                 │
│  Transformaciones:                                              │
│    1. JSONFlattener      → Aplanar nested structures           │
│    2. DataCleaner        → Limpieza de datos                   │
│    3. DataNormalizer     → Normalización de valores            │
│    4. DataTypeConverter  → Conversión de tipos                 │
│    5. DataGapHandler     → Manejo de gaps                      │
│    6. DuplicateDetector  → Deduplicación                       │
│    7. ConflictResolver   → Resolución de conflictos            │
│    8. IcebergManager     → UPSERT transaccional                │
│                                                                 │
│  Ejemplo: s3://silver/metro_orders_clean/                      │
│    └── part-00000-xxx.json (última versión de cada order)      │
└────────────┬────────────────────────────────────────────────────┘
             │
             │ Trigger: EventBridge (cada 10 min) o Manual
             │ Job: etl-silver-to-gold/run_pipeline_to_gold.py
             │
             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    🥇 GOLD LAYER (S3)                           │
│                                                                 │
│  Formato: Parquet con compresión Snappy                        │
│  Comportamiento: MUTABLE (UPSERT con agregaciones)             │
│  Particionamiento: {client}/orders/year/month/day/             │
│                                                                 │
│  Transformaciones:                                              │
│    1. SchemaMapper           → Mapeo a esquema Redshift        │
│    2. BusinessRulesEngine    → Reglas de negocio               │
│    3. AggregationEngine      → Cálculo de métricas             │
│    4. DataQualityValidator   → Validación de calidad           │
│    5. PartitionOptimizer     → Optimización de particiones     │
│                                                                 │
│  Ejemplo: s3://gold/metro/orders/year=2026/month=2/day=26/     │
│    └── part-00000-xxx.snappy.parquet                           │
└────────────┬────────────────────────────────────────────────────┘
             │
             │ Trigger: EventBridge (cada 30 min) o Manual
             │ Job: redshift-loader/load_to_redshift.py
             │
             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    AMAZON REDSHIFT                              │
│                  (Data Warehouse)                               │
│                                                                 │
│  Operación: MERGE (UPSERT)                                      │
│  Tabla: wms_orders                                              │
│  Uso: Power BI, Tableau, SQL queries                           │
└─────────────────────────────────────────────────────────────────┘
```

---

## Módulos de Transformación

### Bronze → Silver (8 Módulos)

#### 1. JSONFlattener
**Propósito**: Convertir JSON nested a estructura flat

**Entrada**:
```json
{
  "data": {
    "customer": {
      "email": "test@example.com",
      "firstName": "Juan"
    }
  }
}
```

**Salida**:
```json
{
  "data_customer_email": "test@example.com",
  "data_customer_firstName": "Juan"
}
```

**Configuración**:
- Prefijo: `data_`
- Separador: `_`
- Arrays: Preservados como JSON strings

---

#### 2. DataCleaner
**Propósito**: Limpieza básica de datos

**Operaciones**:
- Trim de espacios en blanco
- Normalización de line breaks
- Eliminación de caracteres de control
- Normalización de NULL values

**Ejemplo**:
```python
# Antes
"  Juan Pérez  \n" → "Juan Pérez"
"" → None
"null" → None
```

---

#### 3. DataNormalizer
**Propósito**: Normalización de formatos

**Operaciones**:
- Emails: lowercase
- Códigos: uppercase
- Teléfonos: formato estándar
- Direcciones: capitalización correcta

**Ejemplo**:
```python
# Antes
"JUAN@EXAMPLE.COM" → "juan@example.com"
"ord-123" → "ORD-123"
```

---

#### 4. DataTypeConverter
**Propósito**: Conversión de tipos de datos

**Conversiones**:
- Unix timestamp → ISO 8601
- String numbers → Numeric types
- Boolean strings → Boolean
- Date strings → Date objects

**Ejemplo**:
```python
# Antes
1772122687991 → "2026-02-26T12:18:07.991Z"
"250.75" → 250.75
"true" → True
```

---

#### 5. DataGapHandler
**Propósito**: Manejo de datos faltantes

**Estrategias**:
- Valores por defecto según tipo
- Forward fill para series temporales
- Interpolación para valores numéricos
- Flags de datos imputados

**Ejemplo**:
```python
# Antes
{"amount": None} → {"amount": 0.0, "_amount_imputed": True}
```

---

#### 6. DuplicateDetector
**Propósito**: Detección y eliminación de duplicados

**Lógica**:
- Deduplicación por `order_id`
- Última versión gana (por `_metadata_ingestion_timestamp`)
- Logging de duplicados encontrados

**Ejemplo**:
```python
# 3 registros con mismo order_id
# Se mantiene el más reciente
ORD-001 (12:00) → Descartado
ORD-001 (13:00) → Descartado
ORD-001 (14:00) → Mantenido ✓
```

---

#### 7. ConflictResolver
**Propósito**: Resolución de conflictos entre versiones

**Estrategias**:
- Prioridad por fuente (webhook > polling)
- Merge de campos no conflictivos
- Logging de conflictos resueltos

**Ejemplo**:
```python
# Webhook: status=confirmed, amount=250.75
# Polling:  status=confirmed, amount=250.80
# Resultado: status=confirmed, amount=250.75 (webhook gana)
```

---

#### 8. IcebergManager
**Propósito**: Gestión de tablas Iceberg con UPSERT

**Operaciones**:
- UPSERT transaccional por order_id
- Metadata de versiones
- Compactación automática
- Time travel queries

**Configuración**:
```python
{
  "table_name": "metro_orders_clean",
  "primary_key": "data_id",
  "partition_by": "date",
  "sort_by": "_processing_timestamp"
}
```

---

### Silver → Gold (5 Módulos)

#### 1. SchemaMapper
**Propósito**: Mapeo a esquema Redshift

**Mapeos**:
```python
{
  "data_id": "order_id",
  "data_customer_email": "customer_email",
  "data_totalAmount": "total_amount",
  "_processing_timestamp": "etl_timestamp"
}
```

---

#### 2. BusinessRulesEngine
**Propósito**: Aplicar reglas de negocio

**Reglas**:
- Clasificación de pedidos (pequeño/mediano/grande)
- Flags de alertas (pedido urgente, monto alto)
- Cálculo de comisiones
- Segmentación de clientes

---

#### 3. AggregationEngine
**Propósito**: Cálculo de métricas agregadas

**Métricas**:
```python
{
  "total_changes": "COUNT(statusChanges)",
  "days_since_created": "DATEDIFF(NOW(), date_created)",
  "last_status_change": "MAX(statusChanges.dateCreated)"
}
```

---

#### 4. DataQualityValidator
**Propósito**: Validación de calidad de datos

**Validaciones**:
- Rangos de valores (amount > 0)
- Integridad referencial
- Completitud de campos obligatorios
- Detección de anomalías

---

#### 5. PartitionOptimizer
**Propósito**: Optimización de particiones

**Operaciones**:
- Compactación de archivos pequeños
- Eliminación de particiones vacías
- Rebalanceo de datos
- Estadísticas de particiones

---

## Decisiones de Diseño

### ¿Por qué 3 capas?

**Bronze (Raw)**:
- Auditoría y compliance
- Reprocessing sin pérdida
- Debugging de problemas

**Silver (Clean)**:
- Análisis exploratorio
- Queries ad-hoc
- Fuente para múltiples Gold tables

**Gold (Business)**:
- Performance óptimo para BI
- Campos pre-calculados
- Optimizado para Redshift

### ¿Por qué Iceberg en Silver?

- **ACID transactions**: Garantiza consistencia
- **Schema evolution**: Cambios sin downtime
- **Time travel**: Queries históricas
- **UPSERT eficiente**: Mejor que reescribir todo

### ¿Por qué Parquet en Gold?

- **Compresión**: 10x menor que JSON
- **Columnar**: Queries más rápidas
- **Compatible**: Redshift Spectrum, Athena
- **Costo**: Menor storage y transfer

### ¿Por qué particionamiento por fecha?

- **Queries eficientes**: Filtrar por fecha es común
- **Lifecycle policies**: Archivar datos antiguos
- **Paralelismo**: Procesar múltiples particiones
- **Debugging**: Aislar problemas por fecha

---

## Métricas y Monitoreo

### KPIs del Pipeline

- **Latencia Bronze → Silver**: < 5 minutos
- **Latencia Silver → Gold**: < 10 minutos
- **Latencia Gold → Redshift**: < 30 minutos
- **Tasa de error**: < 0.1%
- **Duplicados detectados**: Logging completo
- **Calidad de datos**: > 99.9%

### Alertas Configuradas

- Pipeline fallido (SNS notification)
- Latencia excedida (CloudWatch alarm)
- Calidad de datos baja (custom metric)
- Duplicados excesivos (threshold alert)

---

**Última actualización**: 2026-02-26  
**Versión**: 1.0.0
