# Fase 1.2: Análisis Comparativo de Módulos Duplicados

## Fecha
2026-02-19

## Objetivo
Analizar las diferencias entre las implementaciones de Max y Vicente para los 4 módulos duplicados y definir la estrategia de merge.

---

## Módulos a Fusionar

### 1. data_type_converter.py

#### Vicente (Base)
- **Fortalezas**:
  - Validación robusta con manejo de errores específicos
  - Soporte completo para pandas (pd.isna, pd.to_datetime)
  - Métodos estáticos bien documentados con ejemplos
  - Reglas de conversión predefinidas por tabla (CONVERSION_RULES)
  - Método `apply_conversions_to_dataframe` para aplicar conversiones en batch
  
- **Características**:
  - Conversiones: bigint→timestamp, tinyint→boolean, varchar, decimal, json→varchar, text→varchar, datetime→timestamp
  - Límite MAX_VARCHAR_LENGTH = 65535
  - Validación de rangos (timestamps 1970-2100)
  - Manejo de precisión/escala en decimales

#### Max
- **Fortalezas**:
  - Lógica de inferencia de tipos desde MySQL
  - Integración directa con PySpark DataFrames
  - Método `infer_type_from_mysql` para detectar tipos automáticamente
  
- **Características**:
  - Conversiones similares pero con enfoque en PySpark
  - Menos validación pero más automatización

#### Estrategia de Merge
**Base: Vicente** (más robusto y completo)

**Agregar de Max**:
- Método `infer_type_from_mysql` para detección automática de tipos
- Optimizaciones específicas para PySpark si existen
- Lógica de inferencia de tipos desde metadatos MySQL

**Resultado esperado**:
- Mantener toda la validación y robustez de Vicente
- Agregar capacidad de inferencia automática de tipos de Max
- Soporte dual: pandas y PySpark

---

### 2. data_normalizer.py

#### Vicente (Base)
- **Fortalezas**:
  - Regex robusto para validación de emails (RFC 5322 simplificado)
  - Normalización de teléfonos con código de país configurable
  - Métodos para limpieza de whitespace y case normalization
  - Reglas predefinidas por tabla (NORMALIZATION_RULES)
  - Método `apply_normalizations_to_dataframe` para batch processing
  
- **Características**:
  - Normalizaciones: timestamp→UTC, email, phone, trim, case, remove_extra_spaces
  - Validación de formato de email
  - Soporte para múltiples formatos de teléfono

#### Max
- **Fortalezas**:
  - Integración con PySpark UDFs
  - Normalización específica para campos de Janis API
  - Manejo de casos edge específicos del dominio
  
- **Características**:
  - Normalizaciones similares pero optimizadas para PySpark
  - Menos validación pero más performance en grandes volúmenes

#### Estrategia de Merge
**Base: Vicente** (validación más robusta)

**Agregar de Max**:
- Optimizaciones de PySpark UDFs si mejoran performance
- Casos edge específicos del dominio Janis
- Lógica de normalización específica para campos de la API

**Resultado esperado**:
- Mantener validación robusta de Vicente
- Agregar optimizaciones de PySpark de Max
- Soporte dual: pandas y PySpark

---

### 3. data_gap_handler.py

#### Vicente (Base)
- **Fortalezas**:
  - Cálculos bien definidos con fórmulas documentadas
  - Sistema de metadata para tracking de gaps (_data_gaps)
  - Método `generate_data_gap_report` para documentación
  - Reglas predefinidas (CALCULATED_FIELD_RULES, UNAVAILABLE_FIELDS)
  - Manejo explícito de campos no disponibles
  
- **Características**:
  - Cálculos: items_substituted_qty, items_qty_missing, total_changes
  - Marca campos no disponibles con NULL + metadata
  - Genera reportes de impacto para BI

#### Max
- **Fortalezas**:
  - Lógica de filling con valores por defecto
  - Estrategias de interpolación para gaps temporales
  - Manejo de gaps en series de tiempo
  
- **Características**:
  - Filling de gaps con defaults configurables
  - Menos metadata pero más automatización

#### Estrategia de Merge
**Base: Vicente** (metadata y tracking más completo)

**Agregar de Max**:
- Lógica de filling con valores por defecto
- Estrategias de interpolación si son útiles
- Manejo de gaps en series de tiempo

**Resultado esperado**:
- Mantener sistema de metadata de Vicente
- Agregar capacidades de filling automático de Max
- Combinar tracking explícito con filling inteligente

---

### 4. iceberg_writer.py

#### Vicente (Base)
- **Fortalezas**:
  - Soporte completo para ACID transactions
  - Operaciones: append, overwrite, merge (UPSERT)
  - Método `_merge_into_table` con MERGE INTO SQL
  - Partition overwrite dinámico
  - Logging detallado de operaciones
  
- **Características**:
  - Usa `writeTo()` API de Spark 3.x
  - Soporte para merge_keys en UPSERT
  - Manejo de temporary views para merge
  - Configuración de catalog_name

#### Max
- **Fortalezas**:
  - Integración con IcebergTableManager
  - Retry logic con exponential backoff
  - Manejo automático de schema evolution
  - Método `_ensure_table_exists` para creación automática
  - Retorna count de registros escritos
  
- **Características**:
  - Usa `write.format("iceberg")` API
  - max_retries = 3, retry_delay_seconds = 5
  - Creación automática de tablas si no existen
  - Schema evolution best-effort

#### Estrategia de Merge
**Base: Vicente** (operaciones ACID más completas)

**Agregar de Max**:
- Retry logic con exponential backoff (crítico para producción)
- Integración con IcebergTableManager
- Método `_ensure_table_exists` para auto-creación
- Retorno de count de registros
- Schema evolution automática

**Resultado esperado**:
- Mantener operaciones ACID completas de Vicente (append, overwrite, merge)
- Agregar retry logic y resilience de Max
- Combinar auto-creación de tablas con operaciones avanzadas
- Mejor manejo de errores y logging

---

## Resumen de Estrategia General

### Principios de Merge
1. **Base siempre Vicente**: Implementaciones más robustas con validación completa
2. **Agregar de Max**: Optimizaciones PySpark, retry logic, auto-creación, inferencia
3. **Mantener compatibilidad**: Soporte dual pandas/PySpark donde sea posible
4. **Mejorar resilience**: Agregar retry logic y manejo de errores de Max
5. **Documentación completa**: Mantener docstrings y ejemplos de Vicente

### Orden de Implementación
1. `data_type_converter.py` - Agregar inferencia de tipos
2. `data_normalizer.py` - Agregar optimizaciones PySpark
3. `data_gap_handler.py` - Agregar filling automático
4. `iceberg_writer.py` - Agregar retry logic y auto-creación

### Testing
- Actualizar tests existentes de Vicente
- Agregar tests para nuevas funcionalidades de Max
- Validar compatibilidad pandas/PySpark
- Probar retry logic y error handling

---

## Próximos Pasos

1. Crear versiones merged de cada módulo
2. Actualizar tests unitarios
3. Validar imports y compatibilidad
4. Ejecutar suite completa de tests
5. Documentar cambios en FASE_1.2_RESULTADO_INTEGRACION.md
