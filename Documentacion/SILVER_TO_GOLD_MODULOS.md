# Módulos Silver-to-Gold ETL

**Fecha:** 19 de Febrero, 2026  
**Versión:** 1.0.0  
**Estado:** ✅ Implementado

---

## Resumen Ejecutivo

Este documento describe los **7 módulos especializados** para transformaciones ETL de la capa Silver a Gold, implementados en el paquete `glue/modules/silver_to_gold/`.

Estos módulos proporcionan capacidades avanzadas de:
- **Trazabilidad completa** de datos desde Bronze hasta Gold
- **Validación de calidad** en 4 dimensiones
- **Desnormalización** para análisis de negocio
- **Manejo robusto de errores** con Dead Letter Queue
- **Procesamiento incremental** basado en timestamps
- **Agregaciones** para métricas de negocio

---

## Arquitectura del Paquete

```
glue/modules/silver_to_gold/
├── __init__.py                      # Inicialización del paquete
├── data_lineage_tracker.py         # Trazabilidad de datos
├── data_quality_validator.py       # Validación de calidad
├── denormalization_engine.py       # Desnormalización
├── error_handler.py                # Manejo de errores y DLQ
├── incremental_processor.py        # Procesamiento incremental
└── silver_to_gold_aggregator.py    # Agregaciones de negocio
```

---

## Módulos Implementados

### 1. DataLineageTracker

**Archivo:** `data_lineage_tracker.py`  
**Propósito:** Trazabilidad completa de datos desde Bronze hasta Gold

#### Funcionalidad

- **Tracking por registro**: Agrega columnas de lineage a cada registro
  - `_lineage_pipeline_id`: ID único del pipeline
  - `_lineage_source`: Origen de los datos
  - `_lineage_timestamp`: Timestamp de procesamiento
  - `_lineage_record_hash`: Hash MD5 del registro (opcional)

- **Tracking por etapa**: Registra métricas de cada módulo del pipeline
  - Registros de entrada y salida
  - Registros eliminados
  - Drop rate por etapa

- **Reportes de auditoría**: Guarda logs completos en S3
  - Reporte JSON con todas las etapas
  - Estado final del pipeline (success/failed)
  - Timestamps de cada operación

#### Configuración

```python
config = {
    "lineage": {
        "enabled": True,
        "pipeline_id": "pipeline_20260219_120000",
        "source_path": "s3://bucket/silver/orders/",
        "track_hash": True,  # Agregar hash por registro
        "metadata_bucket": "data-lake-metadata",
        "endpoint_url": "http://localhost:4566"  # Para LocalStack
    }
}
```

#### Uso

```python
from modules.silver_to_gold import DataLineageTracker

tracker = DataLineageTracker()

# Agregar columnas de lineage
df = tracker.transform(df, config)

# Trackear una etapa del pipeline
tracker.track_stage(
    df_before=df_input,
    df_after=df_output,
    stage_name="DataCleaner",
    pipeline_id="pipeline_20260219_120000",
    config=config
)

# Guardar reporte final
tracker.save_lineage_report(
    config=config,
    pipeline_id="pipeline_20260219_120000",
    status="success"
)
```

#### Salida

**Columnas agregadas al DataFrame:**
- `_lineage_pipeline_id`: string
- `_lineage_source`: string
- `_lineage_timestamp`: timestamp
- `_lineage_record_hash`: string (si track_hash=true)

**Reporte en S3:**
```json
{
  "pipeline_id": "pipeline_20260219_120000",
  "generated_at": "2026-02-19T12:00:00",
  "status": "success",
  "total_stages": 5,
  "stages": [
    {
      "pipeline_id": "pipeline_20260219_120000",
      "stage": "DataCleaner",
      "timestamp": "2026-02-19T12:00:01",
      "records_in": 1000,
      "records_out": 950,
      "records_dropped": 50,
      "drop_rate": "5.0%"
    }
  ]
}
```

---

### 2. DataQualityValidator

**Archivo:** `data_quality_validator.py`  
**Propósito:** Validación de calidad de datos en 4 dimensiones

#### Dimensiones de Calidad

1. **Completeness**: Campos críticos no nulos
2. **Validity**: Valores dentro de listas permitidas
3. **Consistency**: Reglas de coherencia entre columnas
4. **Accuracy**: Valores dentro de rangos esperados

#### Funcionalidad

- **Validación por registro**: Marca cada registro como válido/inválido
- **Quality Gate**: Bloquea el pipeline si calidad < threshold
- **Columnas de diagnóstico**:
  - `_quality_valid`: boolean (true si pasa todas las validaciones)
  - `_quality_issues`: string con lista de problemas encontrados

#### Configuración

```python
config = {
    "quality": {
        "critical_columns": ["order_id", "customer_id", "total_amount"],
        "valid_values": {
            "status": ["pending", "completed", "cancelled"],
            "payment_method": ["credit_card", "debit_card", "cash"]
        },
        "numeric_ranges": {
            "total_amount": {"min": 0, "max": 1000000},
            "quantity": {"min": 1, "max": 100}
        },
        "consistency_rules": [
            {
                "when_column": "status",
                "when_value": "completed",
                "then_column": "completed_at",
                "then_not_null": True
            }
        ],
        "quality_gate": True,  # Bloquear si calidad < threshold
        "threshold": 0.95  # 95% de registros válidos mínimo
    }
}
```

#### Uso

```python
from modules.silver_to_gold import DataQualityValidator

validator = DataQualityValidator()

# Validar calidad
df = validator.transform(df, config)

# Si quality_gate=True y calidad < threshold, lanza ValueError
```

#### Salida

**Columnas agregadas:**
- `_quality_valid`: boolean
- `_quality_issues`: string (ej: "COMPLETENESS_FAIL;VALIDITY_FAIL;")

**Ejemplo de registro inválido:**
```
_quality_valid: False
_quality_issues: "COMPLETENESS_FAIL;RANGE_FAIL;"
```

**Quality Gate:**
Si `quality_gate=True` y calidad < threshold:
```
ValueError: [DataQualityValidator] Quality Gate BLOQUEADO: 
92.5% < umbral 95.0%. Registros inválidos: 75/1000. 
Revisa columna '_quality_issues' para detalles.
```

---

### 3. DenormalizationEngine

**Archivo:** `denormalization_engine.py`  
**Propósito:** Combinar entidades relacionadas en tablas planas

#### Funcionalidad

- **Joins configurables**: Une tablas Silver relacionadas
- **Tablas planas**: Genera tablas desnormalizadas para BI
- **Optimización para análisis**: Reduce joins en queries de Power BI

#### Configuración

```python
config = {
    "denormalization": {
        "enabled": True,
        "joins": [
            {
                "table": "silver_customers",
                "on": "customer_id",
                "type": "left",
                "select": ["customer_name", "customer_email", "customer_segment"]
            },
            {
                "table": "silver_products",
                "on": "product_id",
                "type": "left",
                "select": ["product_name", "product_category", "product_price"]
            }
        ]
    }
}
```

#### Uso

```python
from modules.silver_to_gold import DenormalizationEngine

engine = DenormalizationEngine()

# Desnormalizar (une con tablas relacionadas)
df = engine.transform(df, config)
```

#### Nota

En modo local (sin tablas Silver adicionales), el módulo retorna el DataFrame base sin cambios. En producción, leería tablas Silver de clientes/productos desde Iceberg.

---

### 4. ErrorHandler

**Archivo:** `error_handler.py`  
**Propósito:** Manejo robusto de errores con DLQ y retry

#### Funcionalidad

- **Dead Letter Queue (DLQ)**: Registros fallidos se guardan en S3
- **Retry con exponential backoff**: Reintentos automáticos (2s, 4s, 8s)
- **Recovery modes**:
  - `exclude`: Excluye registros fallidos del pipeline
  - `flag`: Mantiene todos pero marca los fallidos

#### Configuración

```python
config = {
    "error_handler": {
        "dlq_enabled": True,
        "dlq_bucket": "data-lake-dlq",
        "dlq_prefix": "failed-records",
        "recovery_mode": "exclude",  # o "flag"
        "endpoint_url": "http://localhost:4566"  # Para LocalStack
    }
}
```

#### Uso

```python
from modules.silver_to_gold import ErrorHandler

handler = ErrorHandler()

# Manejar errores (requiere columna _quality_valid del DataQualityValidator)
df = handler.transform(df, config)

# Retry con backoff para operaciones críticas
def critical_operation():
    # Operación que puede fallar
    return result

result = handler.retry_with_backoff(
    operation=critical_operation,
    operation_name="Escritura a Iceberg"
)

# Registrar error crítico del pipeline
try:
    # Operación del pipeline
    pass
except Exception as e:
    handler.log_pipeline_error(
        stage="DataCleaner",
        error=e,
        config=config
    )
```

#### Salida

**Columna agregada:**
- `_error_handled`: boolean (true si el registro fue procesado por error handler)

**Archivos en DLQ (S3):**
```
s3://data-lake-dlq/failed-records/20260219_120000/
├── part-00000.json  # Registros fallidos con metadata
```

**Contenido de DLQ:**
```json
{
  "order_id": "12345",
  "customer_id": null,
  "_quality_valid": false,
  "_quality_issues": "COMPLETENESS_FAIL;",
  "_dlq_timestamp": "2026-02-19T12:00:00",
  "_dlq_reason": "COMPLETENESS_FAIL;"
}
```

---

### 5. IncrementalProcessor

**Archivo:** `incremental_processor.py`  
**Propósito:** Procesamiento incremental basado en timestamps

#### Funcionalidad

- **Filtrado por timestamp**: Procesa solo datos nuevos
- **Metadata tracking**: Guarda último timestamp procesado en S3
- **Optimización**: Reduce volumen de datos procesados

#### Configuración

```python
config = {
    "incremental": {
        "enabled": True,
        "timestamp_column": "fecha_venta",
        "metadata_bucket": "data-lake-metadata",
        "metadata_key": "incremental/last_processed.json"
    }
}
```

#### Uso

```python
from modules.silver_to_gold import IncrementalProcessor

processor = IncrementalProcessor()

# Filtrar solo registros nuevos
df = processor.transform(df, config)

# Después de escribir exitosamente, actualizar timestamp
processor.update_timestamp(df, config)
```

#### Metadata en S3

**Archivo:** `s3://data-lake-metadata/incremental/last_processed.json`
```json
{
  "last_timestamp": "2026-02-19T12:00:00"
}
```

---

### 6. SilverToGoldAggregator

**Archivo:** `silver_to_gold_aggregator.py`  
**Propósito:** Cálculo de agregaciones para métricas de negocio

#### Funcionalidad

- **Dimensiones de tiempo**: Agrega year, month, day, week
- **Agregaciones configurables**: sum, avg, min, max, count
- **Métricas de negocio**: Calcula KPIs por dimensiones

#### Configuración

```python
config = {
    "aggregations": {
        "date_column": "fecha_venta",
        "dimensions": ["year", "month", "customer_segment", "product_category"],
        "metrics": [
            {
                "column": "total_amount",
                "functions": ["sum", "avg", "min", "max"]
            },
            {
                "column": "*",
                "functions": ["count"]
            }
        ]
    }
}
```

#### Uso

```python
from modules.silver_to_gold import SilverToGoldAggregator

aggregator = SilverToGoldAggregator()

# Calcular agregaciones
df_aggregated = aggregator.transform(df, config)
```

#### Salida

**Columnas agregadas:**
- `year`, `month`, `day`, `week`: dimensiones de tiempo
- `total_total_amount`: suma de total_amount
- `promedio_total_amount`: promedio de total_amount
- `min_total_amount`: mínimo de total_amount
- `max_total_amount`: máximo de total_amount
- `num_registros`: conteo de registros

**Ejemplo de resultado:**
```
year | month | customer_segment | total_total_amount | promedio_total_amount | num_registros
2026 | 2     | premium          | 150000            | 1500                  | 100
2026 | 2     | standard         | 80000             | 800                   | 100
```

---

## Pipeline Silver-to-Gold Completo

### Flujo Recomendado

```python
from modules.silver_to_gold import (
    DataLineageTracker,
    IncrementalProcessor,
    DataQualityValidator,
    ErrorHandler,
    DenormalizationEngine,
    SilverToGoldAggregator
)

# 1. Inicializar módulos
lineage_tracker = DataLineageTracker()
incremental_processor = IncrementalProcessor()
quality_validator = DataQualityValidator()
error_handler = ErrorHandler()
denorm_engine = DenormalizationEngine()
aggregator = SilverToGoldAggregator()

# 2. Leer datos de Silver
df = spark.read.format("iceberg").load("silver.orders")

# 3. Procesamiento incremental
df = incremental_processor.transform(df, config)

# 4. Agregar lineage tracking
df = lineage_tracker.transform(df, config)

# 5. Validar calidad
df_before_quality = df
df = quality_validator.transform(df, config)
lineage_tracker.track_stage(df_before_quality, df, "DataQualityValidator", pipeline_id, config)

# 6. Manejar errores
df_before_errors = df
df = error_handler.transform(df, config)
lineage_tracker.track_stage(df_before_errors, df, "ErrorHandler", pipeline_id, config)

# 7. Desnormalizar (opcional)
df_before_denorm = df
df = denorm_engine.transform(df, config)
lineage_tracker.track_stage(df_before_denorm, df, "DenormalizationEngine", pipeline_id, config)

# 8. Calcular agregaciones (opcional)
df_aggregated = aggregator.transform(df, config)

# 9. Escribir a Gold
df.write.format("iceberg").mode("append").save("gold.orders")
df_aggregated.write.format("iceberg").mode("overwrite").save("gold.orders_metrics")

# 10. Actualizar timestamp incremental
incremental_processor.update_timestamp(df, config)

# 11. Guardar reporte de lineage
lineage_tracker.save_lineage_report(config, pipeline_id, "success")
```

---

## Configuración Completa de Ejemplo

```python
config = {
    "lineage": {
        "enabled": True,
        "pipeline_id": "pipeline_20260219_120000",
        "source_path": "s3://bucket/silver/orders/",
        "track_hash": True,
        "metadata_bucket": "data-lake-metadata",
        "endpoint_url": "http://localhost:4566"
    },
    "incremental": {
        "enabled": True,
        "timestamp_column": "fecha_venta",
        "metadata_bucket": "data-lake-metadata",
        "metadata_key": "incremental/last_processed.json"
    },
    "quality": {
        "critical_columns": ["order_id", "customer_id", "total_amount"],
        "valid_values": {
            "status": ["pending", "completed", "cancelled"]
        },
        "numeric_ranges": {
            "total_amount": {"min": 0, "max": 1000000}
        },
        "consistency_rules": [
            {
                "when_column": "status",
                "when_value": "completed",
                "then_column": "completed_at",
                "then_not_null": True
            }
        ],
        "quality_gate": True,
        "threshold": 0.95
    },
    "error_handler": {
        "dlq_enabled": True,
        "dlq_bucket": "data-lake-dlq",
        "dlq_prefix": "failed-records",
        "recovery_mode": "exclude",
        "endpoint_url": "http://localhost:4566"
    },
    "denormalization": {
        "enabled": True,
        "joins": [
            {
                "table": "silver_customers",
                "on": "customer_id",
                "type": "left",
                "select": ["customer_name", "customer_email"]
            }
        ]
    },
    "aggregations": {
        "date_column": "fecha_venta",
        "dimensions": ["year", "month", "customer_segment"],
        "metrics": [
            {
                "column": "total_amount",
                "functions": ["sum", "avg"]
            },
            {
                "column": "*",
                "functions": ["count"]
            }
        ]
    }
}
```

---

## Testing

### Unit Tests

```bash
# Ejecutar tests de módulos Silver-to-Gold
pytest glue/tests/unit/test_silver_to_gold/ -v
```

### Integration Tests

```bash
# Ejecutar pipeline completo Silver-to-Gold
cd glue
python scripts/test_silver_to_gold_pipeline.py
```

---

## Próximos Pasos

### Corto Plazo (1-2 Semanas)

1. **Unit Tests**: Implementar tests para cada módulo
2. **Integration Tests**: Pipeline completo Silver-to-Gold
3. **Documentación**: Ejemplos de uso por módulo

### Mediano Plazo (3-4 Semanas)

4. **Performance**: Optimizar para grandes volúmenes
5. **Monitoring**: Integrar con CloudWatch
6. **Alerting**: Configurar alertas por calidad de datos

---

## Documentación Relacionada

- **[ESTADO_MODULOS_INTEGRACION.md](ESTADO_MODULOS_INTEGRACION.md)** - Estado de todos los módulos
- **[RESUMEN_ESTADO_ACTUAL.md](RESUMEN_ESTADO_ACTUAL.md)** - Estado general del proyecto
- **[glue/README.md](../glue/README.md)** - Documentación de módulos Glue

---

**Documento creado:** 19 de Febrero, 2026  
**Última actualización:** 19 de Febrero, 2026  
**Versión:** 1.0.0  
**Estado:** ✅ Implementado - Pendiente de testing
