# Integración Pipeline Silver-to-Gold (Max)

## Resumen Ejecutivo

Se integró el pipeline ETL Silver-to-Gold desarrollado por Max, que transforma datos limpios desde la capa Silver hacia datos agregados y optimizados para análisis en la capa Gold.

**Fecha de Integración**: 19 de Febrero 2026  
**Branch Origen**: `origin/bronze-to-silver-max`  
**Branch Destino**: `feature/integracion-max-vicente`

---

## Arquitectura del Pipeline

### Flujo Completo

```
S3 Silver (JSON limpio)
    ↓
IncrementalProcessor
    ↓ (filtra solo datos nuevos)
SilverToGoldAggregator
    ↓ (agrega métricas de negocio)
DenormalizationEngine
    ↓ (joins con dimensiones)
DataQualityValidator
    ↓ (valida calidad de datos)
ErrorHandler
    ↓ (maneja errores y DLQ)
DataLineageTracker
    ↓ (trazabilidad completa)
S3 Gold (JSON agregado)
```

---

## Módulos Implementados

### 1. Módulos Principales de Transformación

#### IncrementalProcessor
**Ubicación**: `glue/modules/silver_to_gold/incremental_processor.py`

**Responsabilidad**: Procesar solo datos nuevos o modificados desde Silver

**Características**:
- Lee último timestamp procesado desde metadata en S3
- Filtra DataFrame por `fecha_venta > last_timestamp`
- Actualiza metadata después de procesamiento exitoso
- Optimiza recursos al evitar reprocesar datos históricos

**Configuración**:
```json
"incremental": {
    "enabled": true,
    "timestamp_column": "fecha_venta",
    "metadata_bucket": "data-lake-metadata",
    "metadata_key": "silver-to-gold/last_processed_timestamp.json"
}
```

#### SilverToGoldAggregator
**Ubicación**: `glue/modules/silver_to_gold/silver_to_gold_aggregator.py`

**Responsabilidad**: Calcular agregaciones para métricas de negocio

**Características**:
- Agrega dimensiones de tiempo (year, month, day, week)
- Calcula métricas configurables: sum, avg, min, max, count
- Agrupa por dimensiones de negocio (sucursal, estado, etc.)
- Optimiza consultas analíticas pre-calculando métricas

**Ejemplo de Agregación**:
```python
# Por sucursal y estado
df.groupBy("metadata_sucursal", "estado").agg(
    sum("monto").alias("total_monto"),
    avg("monto").alias("promedio_monto"),
    min("monto").alias("min_monto"),
    max("monto").alias("max_monto"),
    count("*").alias("num_registros")
)
```

#### DenormalizationEngine
**Ubicación**: `glue/modules/silver_to_gold/denormalization_engine.py`

**Responsabilidad**: Combinar entidades relacionadas en tablas planas

**Características**:
- Joins configurables con tablas de dimensiones
- Preserva registros base (left joins)
- Simplifica consultas analíticas
- Preparado para producción (actualmente stub en LocalStack)

**Configuración**:
```json
"denormalization": {
    "enabled": false,
    "joins": [
        {"table": "silver.clientes", "key": "cliente_id", "type": "left"},
        {"table": "silver.productos", "key": "producto_id", "type": "left"}
    ]
}
```

---

### 2. Módulos Cross-Cutting

#### DataQualityValidator
**Ubicación**: `glue/modules/silver_to_gold/data_quality_validator.py`

**Responsabilidad**: Validar calidad de datos en 4 dimensiones

**Dimensiones de Calidad**:
1. **Completeness**: Campos críticos no nulos
2. **Validity**: Valores dentro de rangos permitidos
3. **Consistency**: Coherencia entre columnas relacionadas
4. **Accuracy**: Valores dentro de rangos de negocio

**Características**:
- Agrega columnas `_quality_valid`, `_quality_issues`
- Quality Gate opcional: bloquea pipeline si calidad < umbral
- Reglas de negocio configurables
- Reportes detallados de problemas

**Ejemplo de Reglas**:
```json
"quality": {
    "critical_columns": ["estado", "metadata_sucursal"],
    "valid_values": {
        "estado": ["completado", "pendiente", "cancelado", "rechazado"]
    },
    "numeric_ranges": {
        "monto": {"min": 0, "max": 99999999}
    },
    "consistency_rules": [
        {
            "when_column": "estado",
            "when_value": "completado",
            "then_column": "monto",
            "then_not_null": true
        }
    ],
    "quality_gate": false,
    "threshold": 0.8
}
```

#### ErrorHandler
**Ubicación**: `glue/modules/silver_to_gold/error_handler.py`

**Responsabilidad**: Manejo robusto de errores

**Características**:
- **Dead Letter Queue (DLQ)**: Registros fallidos a S3
- **Retry con Exponential Backoff**: 3 intentos con delays 2s, 4s, 8s
- **Recovery Modes**:
  - `exclude`: Elimina registros problemáticos
  - `flag`: Marca registros pero los mantiene
- **Logging de Errores**: Auditoría completa en S3

**Flujo de Manejo de Errores**:
```
Registro con error
    ↓
¿DLQ habilitado?
    ↓ Sí
Enviar a s3://data-lake-dlq/silver-to-gold/failed/
    ↓
¿Recovery mode?
    ↓ exclude → Eliminar del pipeline
    ↓ flag → Marcar con _error_handled=true
```

#### DataLineageTracker
**Ubicación**: `glue/modules/silver_to_gold/data_lineage_tracker.py`

**Responsabilidad**: Trazabilidad completa de datos

**Características**:
- Agrega columnas de lineage a cada registro
- Hash MD5 por registro para detectar cambios
- Log de cada etapa del pipeline
- Reportes JSON en S3 para auditoría

**Columnas de Lineage**:
- `_lineage_pipeline_id`: ID único del pipeline
- `_lineage_source`: Origen de los datos
- `_lineage_timestamp`: Timestamp de procesamiento
- `_lineage_record_hash`: Hash del registro

**Reporte de Lineage**:
```json
{
    "pipeline_id": "silver-to-gold-20260219-143022",
    "generated_at": "2026-02-19T14:30:45",
    "status": "success",
    "total_stages": 7,
    "stages": [
        {
            "stage": "IncrementalProcessor",
            "records_in": 100,
            "records_out": 15,
            "records_dropped": 85,
            "drop_rate": "85.0%"
        }
    ]
}
```

---

## Configuración

### Archivo de Configuración
**Ubicación**: `glue/config/silver-to-gold-config.json`

**Secciones**:
- `input`: Ruta y formato de datos Silver
- `output`: Ruta y formato de datos Gold
- `incremental`: Configuración de procesamiento incremental
- `aggregations`: Dimensiones y métricas a calcular
- `denormalization`: Joins con tablas de dimensiones
- `quality`: Reglas de validación de calidad
- `error_handler`: Configuración de DLQ y recovery
- `lineage`: Configuración de trazabilidad

---

## Scripts de Ejecución

### Pipeline Orquestador
**Ubicación**: `glue/scripts/etl_pipeline_gold.py`

**Clase**: `ETLPipelineGold`

**Responsabilidad**: Orquestar todos los módulos en secuencia

**Orden de Ejecución**:
1. Leer datos de Silver
2. Iniciar lineage tracking
3. Ejecutar módulos principales (Incremental → Aggregator → Denormalization)
4. Validar calidad
5. Manejar errores
6. Agregar timestamp de procesamiento
7. Escribir a Gold
8. Actualizar metadata incremental
9. Guardar reporte de lineage

### Script de Ejecución Local
**Ubicación**: `glue/scripts/run_pipeline_to_gold.py`

**Propósito**: Ejecutar pipeline en LocalStack para testing

**Características**:
- Configuración de Spark para LocalStack
- Endpoints S3 locales (http://localhost:4566)
- Credenciales de prueba
- Logging detallado

**Uso**:
```bash
python glue/scripts/run_pipeline_to_gold.py
```

---

## Especificación Completa

### Documentos del Spec
**Ubicación**: `.kiro/specs/etl-silver-to-gold/`

**Archivos**:
- `requirements.md`: Requisitos funcionales con historias de usuario
- `design.md`: Diseño técnico con interfaces y propiedades de correctness
- `tasks.md`: Lista de tareas de implementación

### Requisitos Principales

**Requisito 1: Agregaciones para BI**
- Calcular totales por cliente, producto y fecha
- Incluir métricas: sum, avg, count, min, max
- Crear dimensiones de tiempo (día, semana, mes, año)

**Requisito 2: Desnormalización de Entidades**
- Combinar información de cliente, producto y venta
- Preservar todas las columnas relevantes

**Requisito 3: Procesamiento Incremental**
- Leer último timestamp procesado
- Filtrar solo registros nuevos
- Actualizar metadata después de procesamiento

---

## Integración con Pipeline Existente

### Conexión con Bronze-to-Silver

El pipeline Silver-to-Gold se conecta naturalmente con el trabajo previo:

```
API Janis
    ↓
Bronze (JSON raw)
    ↓
[Pipeline Bronze-to-Silver - Ya implementado]
    ↓ JSONFlattener
    ↓ DataCleaner
    ↓ DataNormalizer
    ↓ DataTypeConverter
    ↓ DuplicateDetector
    ↓ ConflictResolver
    ↓ DataGapHandler
    ↓
Silver (JSON limpio)
    ↓
[Pipeline Silver-to-Gold - Recién integrado]
    ↓ IncrementalProcessor
    ↓ SilverToGoldAggregator
    ↓ DenormalizationEngine
    ↓ DataQualityValidator
    ↓ ErrorHandler
    ↓ DataLineageTracker
    ↓
Gold (JSON agregado)
    ↓
Redshift (para BI)
```

### Datos de Entrada Esperados

El pipeline espera datos en formato Silver con estructura:
```json
{
    "id": 1001,
    "cliente_nombre": "Juan Pérez",
    "producto_nombre": "Laptop HP",
    "monto": 2500.80,
    "fecha_venta": "2026-02-15T10:30:00",
    "estado": "completado",
    "metadata_sucursal": "Sucursal Centro",
    "es_valido": true,
    "has_critical_gaps": false
}
```

---

## Testing y Validación

### Próximos Pasos para Testing

1. **Preparar Datos de Prueba en Silver**
   - Usar output del pipeline Bronze-to-Silver
   - Verificar que existan datos en `s3://data-lake-silver/ventas_procesadas/`

2. **Ejecutar Pipeline Silver-to-Gold**
   ```bash
   python glue/scripts/run_pipeline_to_gold.py
   ```

3. **Validar Output en Gold**
   - Verificar datos en `s3://data-lake-gold/ventas_agregadas/`
   - Revisar agregaciones calculadas
   - Validar dimensiones de tiempo

4. **Revisar Metadata y Lineage**
   - Verificar timestamp incremental en `s3://data-lake-metadata/`
   - Revisar reporte de lineage
   - Validar registros en DLQ si hay errores

---

## Archivos Integrados

### Estructura de Directorios

```
.kiro/specs/etl-silver-to-gold/
├── requirements.md
├── design.md
└── tasks.md

glue/
├── config/
│   └── silver-to-gold-config.json
├── modules/
│   └── silver_to_gold/
│       ├── __init__.py
│       ├── incremental_processor.py
│       ├── silver_to_gold_aggregator.py
│       ├── denormalization_engine.py
│       ├── data_quality_validator.py
│       ├── error_handler.py
│       └── data_lineage_tracker.py
└── scripts/
    ├── etl_pipeline_gold.py
    └── run_pipeline_to_gold.py
```

### Archivos Preservados

✅ **No se eliminó ningún archivo local**
✅ **Toda la documentación existente se mantiene**
✅ **Todos los módulos Bronze-to-Silver intactos**
✅ **Scripts de testing existentes preservados**

---

## Beneficios de la Integración

### Capacidades Nuevas

1. **Procesamiento Incremental**: Solo procesa datos nuevos, optimizando recursos
2. **Agregaciones Pre-calculadas**: Mejora performance de consultas BI
3. **Validación de Calidad**: Garantiza datos confiables en Gold
4. **Manejo Robusto de Errores**: DLQ y recovery automático
5. **Trazabilidad Completa**: Auditoría de cada transformación

### Preparación para Producción

- ✅ Configuración flexible por ambiente
- ✅ Manejo de errores robusto
- ✅ Logging y monitoreo integrado
- ✅ Procesamiento incremental eficiente
- ✅ Validación de calidad de datos

---

## Documentación Relacionada

- [SILVER_TO_GOLD_MODULOS.md](./SILVER_TO_GOLD_MODULOS.md) - Documentación técnica detallada de cada módulo ⭐
- [Pipeline Bronze-to-Silver](./RESULTADOS_PRUEBA_MAX.md)
- [Pipeline con Mapeo de Esquemas](./PIPELINE_CON_MAPEO_ESQUEMA.md)
- [Estado de Módulos de Integración](./ESTADO_MODULOS_INTEGRACION.md)
- [Guía de Testing](./COMO_PROBAR_PIPELINE.md)

---

## Próximos Pasos

1. ✅ **Integración Completada**: Todos los archivos copiados sin conflictos
2. ⏳ **Testing End-to-End**: Ejecutar pipeline completo Bronze → Silver → Gold
3. ⏳ **Validación de Datos**: Verificar agregaciones y métricas en Gold
4. ⏳ **Documentación de Resultados**: Crear reporte de testing
5. ⏳ **Preparación para PR**: Consolidar cambios para merge

---

**Estado**: ✅ Integración Completada  
**Siguiente Acción**: Testing del pipeline Silver-to-Gold con datos reales
