# Integración Max-Vicente: Design Document

**Fecha:** 19 de Febrero, 2026  
**Estado:** 🚧 En Progreso - Fase 1.2  
**Objetivo:** Diseño técnico para integrar el pipeline Bronze-to-Silver de Max con los módulos robustos de Vicente

---

## 1. Visión General

### 1.1 Contexto

Tenemos dos implementaciones complementarias del sistema de transformación de datos:

**Max (`max/`):**
- Pipeline completo Bronze-to-Silver funcional
- 10 módulos de transformación implementados
- Validado con LocalStack y datos reales
- Orquestación con ETLPipeline
- Configuración JSON flexible

**Vicente (`glue/`):**
- Módulos con property-based testing robusto
- IcebergTableManager con snapshots y rollback
- SchemaEvolutionManager completo
- Tests con Hypothesis (100+ casos por property)
- Validaciones exhaustivas

### 1.2 Objetivo de la Integración

Crear un sistema unificado que combine:
- Pipeline funcional de Max
- Testing robusto de Vicente
- Módulos únicos de ambas implementaciones
- Sistema completo end-to-end validado

---

## 2. Arquitectura del Sistema Integrado

### 2.1 Flujo de Datos

```
S3 Bronze (JSON)
    ↓
[1] JSONFlattener (Max) ✅
    ↓
[2] DataCleaner (Max) ✅
    ↓
[3] DataNormalizer (Fusionado) 📋
    ↓
[4] DataTypeConverter (Fusionado) 📋
    ↓
[5] DuplicateDetector (Max) ✅
    ↓
[6] ConflictResolver (Max) ✅
    ↓
[7] DataGapHandler (Fusionado) 📋
    ↓
[8] SchemaEvolutionManager (Vicente) ⏳
    ↓
[9] IcebergWriter (Fusionado) 📋
    ↓
S3 Silver (Iceberg)
```

**Leyenda:**
- ✅ Integrado y testeado
- 📋 Análisis completado, listo para fusión
- ⏳ Pendiente de implementación

### 2.2 Componentes del Sistema

#### Capa de Ingesta
- **Fuente:** S3 Bronze (JSON files)
- **Formato:** JSON con estructuras anidadas
- **Volumen:** Variable (12-1M+ registros)

#### Capa de Transformación
- **Motor:** PySpark en AWS Glue
- **Módulos:** 10 transformaciones en secuencia
- **Configuración:** JSON + Python

#### Capa de Almacenamiento
- **Formato:** Apache Iceberg (Parquet + Snappy)
- **Catálogo:** AWS Glue Data Catalog
- **Features:** ACID, Time Travel, Schema Evolution

---

## 3. Decisiones de Diseño

### Decisión 1: Estrategia de Fusión de Módulos

**Contexto:** 4 módulos existen en ambas implementaciones con diferentes enfoques.

**Opciones Consideradas:**
1. Usar solo módulos de Max
2. Usar solo módulos de Vicente
3. Fusionar ambas implementaciones

**Decisión:** Fusionar módulos usando Vicente como base y agregando funcionalidad de Max.

**Rationale:**
- Vicente tiene validación más robusta
- Max tiene optimizaciones PySpark específicas
- Fusión aprovecha lo mejor de ambos
- Mantiene compatibilidad con tests existentes

**Análisis Detallado:** Ver [FASE_1.2_ANALISIS_COMPARATIVO.md](../../Documentacion/FASE_1.2_ANALISIS_COMPARATIVO.md)

### Decisión 2: Orden de Integración

**Contexto:** Necesitamos priorizar qué módulos fusionar primero.

**Decisión:** Orden de fusión:
1. DataTypeConverter (crítico para conversiones)
2. DataNormalizer (crítico para calidad de datos)
3. DataGapHandler (importante para completitud)
4. IcebergWriter (crítico para escritura)

**Rationale:**
- DataTypeConverter es fundamental para el pipeline
- DataNormalizer afecta calidad de datos downstream
- DataGapHandler puede implementarse después
- IcebergWriter es el último paso del pipeline

### Decisión 3: Uso de IcebergTableManager

**Contexto:** Vicente tiene IcebergTableManager completo con snapshots y rollback.

**Decisión:** Usar IcebergTableManager de Vicente como base para gestión de tablas.

**Rationale:**
- Funcionalidad completa de snapshots
- Rollback capability crítico para producción
- Time travel para auditoría
- Property tests validados

### Decisión 4: Configuración del Pipeline

**Contexto:** Max usa JSON, Vicente usa Python directo.

**Decisión:** Mantener configuración JSON de Max con extensiones para features de Vicente.

**Rationale:**
- JSON es más flexible para diferentes ambientes
- Fácil de modificar sin cambiar código
- Soporta configuración por tabla/entidad
- Compatible con AWS Systems Manager

### Decisión 5: Testing Strategy

**Contexto:** Necesitamos validar módulos fusionados.

**Decisión:** Combinar unit tests de Max con property tests de Vicente.

**Rationale:**
- Unit tests validan casos específicos
- Property tests validan propiedades universales
- Cobertura completa de edge cases
- Confianza en corrección del código

---

## 4. Módulos Integrados

### 4.1 Módulos Únicos de Max (Completados ✅)

#### JSONFlattener
- **Función:** Aplanar estructuras JSON anidadas
- **Estado:** ✅ Integrado
- **Ubicación:** `glue/modules/json_flattener.py`
- **Tests:** 5 unit tests
- **Documentación:** [INTEGRACION_JSONFLATTENER.md](../../Documentacion/INTEGRACION_JSONFLATTENER.md)

#### DataCleaner
- **Función:** Limpieza de datos (trim, nulls, encoding)
- **Estado:** ✅ Integrado
- **Ubicación:** `glue/modules/data_cleaner.py`
- **Tests:** 6 unit tests
- **Documentación:** [FASE_1.1_INTEGRACION_MODULOS_MAX.md](../../Documentacion/FASE_1.1_INTEGRACION_MODULOS_MAX.md)

#### DuplicateDetector
- **Función:** Detección de duplicados por business keys
- **Estado:** ✅ Integrado
- **Ubicación:** `glue/modules/duplicate_detector.py`
- **Tests:** 6 unit tests
- **Documentación:** [INTEGRACION_DUPLICATE_DETECTOR.md](../../Documentacion/INTEGRACION_DUPLICATE_DETECTOR.md)

#### ConflictResolver
- **Función:** Resolución de conflictos en duplicados
- **Estado:** ✅ Integrado
- **Ubicación:** `glue/modules/conflict_resolver.py`
- **Tests:** 6 unit tests
- **Documentación:** [INTEGRACION_DUPLICATE_DETECTOR.md](../../Documentacion/INTEGRACION_DUPLICATE_DETECTOR.md)

### 4.2 Módulos a Fusionar (Análisis Completado 📋)

#### DataTypeConverter
- **Base:** Vicente (validación robusta)
- **Agregar:** Inferencia automática de tipos de Max
- **Estado:** 📋 Análisis completado
- **Estrategia:** Mantener validaciones + agregar `infer_type_from_mysql`
- **Análisis:** [FASE_1.2_ANALISIS_COMPARATIVO.md](../../Documentacion/FASE_1.2_ANALISIS_COMPARATIVO.md#1-data_type_converterpy)

#### DataNormalizer
- **Base:** Vicente (regex robustos)
- **Agregar:** Optimizaciones PySpark UDFs de Max
- **Estado:** 📋 Análisis completado
- **Estrategia:** Mantener validación + agregar optimizaciones
- **Análisis:** [FASE_1.2_ANALISIS_COMPARATIVO.md](../../Documentacion/FASE_1.2_ANALISIS_COMPARATIVO.md#2-data_normalizerpy)

#### DataGapHandler
- **Base:** Vicente (metadata tracking)
- **Agregar:** Filling automático de Max
- **Estado:** 📋 Análisis completado
- **Estrategia:** Mantener metadata + agregar interpolación
- **Análisis:** [FASE_1.2_ANALISIS_COMPARATIVO.md](../../Documentacion/FASE_1.2_ANALISIS_COMPARATIVO.md#3-data_gap_handlerpy)

#### IcebergWriter
- **Base:** Vicente (operaciones ACID completas)
- **Agregar:** Retry logic y auto-creación de Max
- **Estado:** 📋 Análisis completado
- **Estrategia:** Mantener ACID + agregar resilience
- **Análisis:** [FASE_1.2_ANALISIS_COMPARATIVO.md](../../Documentacion/FASE_1.2_ANALISIS_COMPARATIVO.md#4-iceberg_writerpy)

### 4.3 Módulos de Vicente (Pendientes ⏳)

#### IcebergTableManager
- **Función:** Gestión completa de tablas Iceberg
- **Estado:** ✅ Completado
- **Features:** Snapshots, rollback, ACID, time travel
- **Tests:** 3 property tests (100+ casos cada uno)

#### SchemaEvolutionManager
- **Función:** Gestión de evolución de esquemas
- **Estado:** ⏳ Pendiente de implementación
- **Features:** Detección, validación, aplicación, rollback
- **Prioridad:** Media

---

## 5. Interfaces y Contratos

### 5.1 Interfaz de Módulos de Transformación

Todos los módulos de transformación siguen esta interfaz:

```python
class TransformationModule:
    def transform(self, df: DataFrame, config: dict) -> DataFrame:
        """
        Transforma el DataFrame según la lógica del módulo.
        
        Args:
            df: PySpark DataFrame de entrada
            config: Diccionario de configuración
            
        Returns:
            DataFrame transformado
            
        Raises:
            ValueError: Si la configuración es inválida
        """
        pass
```

### 5.2 Configuración JSON

Estructura de configuración para el pipeline:

```json
{
  "source": {
    "type": "s3",
    "bucket": "data-lake-bronze",
    "prefix": "orders/"
  },
  "transformations": {
    "json_flattening": {
      "enabled": true,
      "max_depth": 10
    },
    "data_cleaning": {
      "enabled": true,
      "trim_strings": true,
      "empty_to_null": true
    },
    "data_normalization": {
      "enabled": true,
      "normalize_timestamps": true,
      "normalize_emails": true
    },
    "type_conversion": {
      "enabled": true,
      "infer_from_mysql": true
    },
    "duplicate_detection": {
      "enabled": true,
      "key_columns": ["order_id"]
    },
    "conflict_resolution": {
      "enabled": true,
      "timestamp_column": "dateModified"
    },
    "data_gap_handling": {
      "enabled": true,
      "calculate_fields": true,
      "fill_defaults": true
    }
  },
  "destination": {
    "type": "iceberg",
    "database": "silver",
    "table": "orders",
    "write_mode": "append"
  }
}
```

### 5.3 Interfaz de IcebergWriter

```python
class IcebergWriter:
    def write(
        self,
        df: DataFrame,
        table_name: str,
        mode: str = "append",
        merge_keys: Optional[List[str]] = None
    ) -> int:
        """
        Escribe DataFrame a tabla Iceberg.
        
        Args:
            df: DataFrame a escribir
            table_name: Nombre de la tabla
            mode: append, overwrite, o merge
            merge_keys: Claves para UPSERT (solo para mode=merge)
            
        Returns:
            Número de registros escritos
            
        Raises:
            ValueError: Si los parámetros son inválidos
            RuntimeError: Si la escritura falla después de reintentos
        """
        pass
```

---

## 6. Patrones de Diseño

### 6.1 Pipeline Pattern

El ETLPipeline orquesta la ejecución secuencial de módulos:

```python
class ETLPipeline:
    def __init__(self, config: dict):
        self.config = config
        self.modules = self._initialize_modules()
    
    def execute(self) -> DataFrame:
        df = self._read_source()
        
        for module in self.modules:
            df = module.transform(df, self.config)
            self._log_metrics(module, df)
        
        self._write_destination(df)
        return df
```

### 6.2 Strategy Pattern

Cada módulo implementa una estrategia de transformación específica:

```python
# Estrategia de limpieza
class DataCleaner(TransformationModule):
    def transform(self, df, config):
        df = self._trim_strings(df)
        df = self._empty_to_null(df)
        return df

# Estrategia de normalización
class DataNormalizer(TransformationModule):
    def transform(self, df, config):
        df = self._normalize_timestamps(df)
        df = self._normalize_emails(df)
        return df
```

### 6.3 Retry Pattern

IcebergWriter implementa retry con exponential backoff:

```python
def _write_with_retry(self, df, table_name, mode):
    max_retries = 3
    retry_delay = 5
    
    for attempt in range(max_retries):
        try:
            return self._write(df, table_name, mode)
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(retry_delay * (2 ** attempt))
            else:
                raise
```

---

## 7. Consideraciones de Performance

### 7.1 Optimizaciones PySpark

- **Evitar collect():** Mantener operaciones lazy
- **Usar broadcast joins:** Para tablas pequeñas
- **Partitioning:** Particionar por fecha para queries eficientes
- **Caching:** Cachear DataFrames reutilizados

### 7.2 Optimizaciones Iceberg

- **Compaction:** Consolidar archivos pequeños
- **Sorting:** Ordenar por columnas frecuentemente filtradas
- **Partitioning:** Hidden partitioning por fecha
- **Snapshots:** Limpiar snapshots antiguos

### 7.3 Métricas de Performance

Métricas a monitorear:
- Tiempo de ejecución por módulo
- Registros procesados por segundo
- Tamaño de archivos Parquet generados
- Número de snapshots Iceberg

---

## 8. Testing Strategy

### 8.1 Unit Tests

- **Cobertura:** >80% para módulos críticos
- **Framework:** pytest
- **Ubicación:** `glue/tests/unit/`
- **Ejecución:** `pytest glue/tests/unit/ -v`

### 8.2 Property-Based Tests

- **Framework:** Hypothesis
- **Casos:** 100+ por property
- **Ubicación:** `glue/tests/property/`
- **Ejecución:** `pytest glue/tests/property/ -v`

### 8.3 Integration Tests

- **Scope:** Pipeline completo Bronze → Silver
- **Datos:** Fixtures con casos reales
- **Validación:** Conteos, tipos, valores
- **Ubicación:** `glue/tests/integration/`

---

## 9. Plan de Implementación

### Fase 1.1: Integración de Módulos Únicos ✅
- ✅ JSONFlattener
- ✅ DataCleaner
- ✅ DuplicateDetector
- ✅ ConflictResolver
- ✅ 23 unit tests creados
- ✅ Documentación completa

### Fase 1.2: Análisis y Fusión de Módulos Duplicados 📋
- ✅ Análisis comparativo completado
- 📋 DataTypeConverter (próximo)
- 📋 DataNormalizer
- 📋 DataGapHandler
- 📋 IcebergWriter

### Fase 1.3: Implementación de SchemaEvolutionManager ⏳
- ⏳ Diseño de interfaz
- ⏳ Implementación base
- ⏳ Property tests
- ⏳ Integración con pipeline

### Fase 1.4: Pipeline Unificado ⏳
- ⏳ ETLPipeline actualizado
- ⏳ Configuración híbrida
- ⏳ Tests de integración
- ⏳ Documentación completa

---

## 10. Riesgos y Mitigaciones

### Riesgo 1: Incompatibilidades entre Módulos
- **Probabilidad:** Media
- **Impacto:** Alto
- **Mitigación:** Tests de integración exhaustivos

### Riesgo 2: Performance Degradado
- **Probabilidad:** Baja
- **Impacto:** Alto
- **Mitigación:** Benchmarking antes/después

### Riesgo 3: Pérdida de Funcionalidad
- **Probabilidad:** Baja
- **Impacto:** Alto
- **Mitigación:** Mantener branches separadas

---

## 11. Referencias

### Documentación de Integración
- [Requirements](requirements.md)
- [FASE_1.1_INTEGRACION_MODULOS_MAX.md](../../Documentacion/FASE_1.1_INTEGRACION_MODULOS_MAX.md)
- [FASE_1.2_ANALISIS_COMPARATIVO.md](../../Documentacion/FASE_1.2_ANALISIS_COMPARATIVO.md)
- [ESTADO_MODULOS_INTEGRACION.md](../../Documentacion/ESTADO_MODULOS_INTEGRACION.md)

### Código
- Módulos Max: `max/src/modules/`
- Módulos Vicente: `glue/modules/`
- Tests: `glue/tests/`

### Specs
- [Data Transformation Tasks](../data-transformation/tasks.md)
- [Initial Data Load](../02-initial-data-load/)

---

**Documento creado:** 19 de Febrero, 2026  
**Última actualización:** 19 de Febrero, 2026  
**Estado:** Fase 1.2 en progreso - Análisis completado
