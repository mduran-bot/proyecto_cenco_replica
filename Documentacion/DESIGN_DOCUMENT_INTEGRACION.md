# Design Document de Integración Max-Vicente

**Fecha:** 19 de Febrero, 2026  
**Ubicación:** `.kiro/specs/integration-max-vicente/design.md`  
**Estado:** 🚧 En Progreso - Fase 1.2

---

## 📋 Resumen Ejecutivo

Se ha creado un **Design Document técnico completo** que documenta la arquitectura, decisiones de diseño, y plan de implementación para integrar el pipeline Bronze-to-Silver de Max con los módulos robustos de Vicente.

**Documento:** [.kiro/specs/integration-max-vicente/design.md](../.kiro/specs/integration-max-vicente/design.md)

---

## 🎯 Contenido del Design Document

### 1. Visión General
- Contexto de las dos implementaciones (Max y Vicente)
- Objetivo de crear un sistema unificado
- Arquitectura del sistema integrado

### 2. Arquitectura del Sistema

**Flujo de Datos Completo:**
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

### 3. Decisiones de Diseño Fundamentales

#### Decisión 1: Estrategia de Fusión
**Decisión:** Fusionar módulos usando Vicente como base y agregando funcionalidad de Max.

**Rationale:**
- Vicente tiene validación más robusta
- Max tiene optimizaciones PySpark específicas
- Fusión aprovecha lo mejor de ambos
- Mantiene compatibilidad con tests existentes

#### Decisión 2: Orden de Integración
**Decisión:** DataTypeConverter → DataNormalizer → DataGapHandler → IcebergWriter

**Rationale:**
- DataTypeConverter es fundamental para el pipeline
- DataNormalizer afecta calidad de datos downstream
- Orden lógico de dependencias

#### Decisión 3: Uso de IcebergTableManager
**Decisión:** Usar IcebergTableManager de Vicente como base para gestión de tablas.

**Rationale:**
- Funcionalidad completa de snapshots
- Rollback capability crítico para producción
- Time travel para auditoría
- Property tests validados

#### Decisión 4: Configuración del Pipeline
**Decisión:** Mantener configuración JSON de Max con extensiones para features de Vicente.

**Rationale:**
- JSON es más flexible para diferentes ambientes
- Fácil de modificar sin cambiar código
- Soporta configuración por tabla/entidad
- Compatible con AWS Systems Manager

#### Decisión 5: Testing Strategy
**Decisión:** Combinar unit tests de Max con property tests de Vicente.

**Rationale:**
- Unit tests validan casos específicos
- Property tests validan propiedades universales
- Cobertura completa de edge cases
- Confianza en corrección del código

### 4. Módulos Integrados

#### Módulos Únicos de Max (Completados ✅)
1. **JSONFlattener** - Aplanar estructuras JSON anidadas
2. **DataCleaner** - Limpieza de datos (trim, nulls, encoding)
3. **DuplicateDetector** - Detección de duplicados por business keys
4. **ConflictResolver** - Resolución de conflictos en duplicados

#### Módulos a Fusionar (Análisis Completado 📋)
1. **DataTypeConverter** - Vicente (base) + Max (inferencia automática)
2. **DataNormalizer** - Vicente (regex robustos) + Max (optimizaciones PySpark)
3. **DataGapHandler** - Vicente (metadata tracking) + Max (filling automático)
4. **IcebergWriter** - Vicente (ACID completo) + Max (retry logic)

#### Módulos de Vicente (Pendientes ⏳)
1. **IcebergTableManager** - ✅ Completado (snapshots, rollback, ACID, time travel)
2. **SchemaEvolutionManager** - ⏳ Pendiente de implementación

### 5. Interfaces y Contratos

#### Interfaz de Módulos de Transformación
```python
class TransformationModule:
    def transform(self, df: DataFrame, config: dict) -> DataFrame:
        """Transforma el DataFrame según la lógica del módulo."""
        pass
```

#### Configuración JSON
```json
{
  "source": {
    "type": "s3",
    "bucket": "data-lake-bronze",
    "prefix": "orders/"
  },
  "transformations": {
    "json_flattening": {"enabled": true, "max_depth": 10},
    "data_cleaning": {"enabled": true, "trim_strings": true},
    "data_normalization": {"enabled": true, "normalize_timestamps": true},
    "type_conversion": {"enabled": true, "infer_from_mysql": true},
    "duplicate_detection": {"enabled": true, "key_columns": ["order_id"]},
    "conflict_resolution": {"enabled": true, "timestamp_column": "dateModified"},
    "data_gap_handling": {"enabled": true, "calculate_fields": true}
  },
  "destination": {
    "type": "iceberg",
    "database": "silver",
    "table": "orders",
    "write_mode": "append"
  }
}
```

### 6. Patrones de Diseño

#### Pipeline Pattern
El ETLPipeline orquesta la ejecución secuencial de módulos.

#### Strategy Pattern
Cada módulo implementa una estrategia de transformación específica.

#### Retry Pattern
IcebergWriter implementa retry con exponential backoff.

### 7. Consideraciones de Performance

#### Optimizaciones PySpark
- Evitar collect() - mantener operaciones lazy
- Usar broadcast joins para tablas pequeñas
- Partitioning por fecha para queries eficientes
- Caching de DataFrames reutilizados

#### Optimizaciones Iceberg
- Compaction de archivos pequeños
- Sorting por columnas frecuentemente filtradas
- Hidden partitioning por fecha
- Limpieza de snapshots antiguos

### 8. Testing Strategy

#### Unit Tests
- Cobertura >80% para módulos críticos
- Framework: pytest
- Ubicación: `glue/tests/unit/`

#### Property-Based Tests
- Framework: Hypothesis
- 100+ casos por property
- Ubicación: `glue/tests/property/`

#### Integration Tests
- Scope: Pipeline completo Bronze → Silver
- Datos: Fixtures con casos reales
- Ubicación: `glue/tests/integration/`

### 9. Plan de Implementación

#### Fase 1.1: Integración de Módulos Únicos ✅
- ✅ JSONFlattener, DataCleaner, DuplicateDetector, ConflictResolver
- ✅ 23 unit tests creados
- ✅ Documentación completa

#### Fase 1.2: Análisis y Fusión de Módulos Duplicados 📋
- ✅ Análisis comparativo completado
- 📋 DataTypeConverter (próximo)
- 📋 DataNormalizer
- 📋 DataGapHandler
- 📋 IcebergWriter

#### Fase 1.3: Implementación de SchemaEvolutionManager ⏳
- ⏳ Diseño de interfaz
- ⏳ Implementación base
- ⏳ Property tests
- ⏳ Integración con pipeline

#### Fase 1.4: Pipeline Unificado ⏳
- ⏳ ETLPipeline actualizado
- ⏳ Configuración híbrida
- ⏳ Tests de integración
- ⏳ Documentación completa

### 10. Riesgos y Mitigaciones

#### Riesgo 1: Incompatibilidades entre Módulos
- **Probabilidad:** Media
- **Impacto:** Alto
- **Mitigación:** Tests de integración exhaustivos

#### Riesgo 2: Performance Degradado
- **Probabilidad:** Baja
- **Impacto:** Alto
- **Mitigación:** Benchmarking antes/después

#### Riesgo 3: Pérdida de Funcionalidad
- **Probabilidad:** Baja
- **Impacto:** Alto
- **Mitigación:** Mantener branches separadas

---

## 🔗 Documentación Relacionada

### Especificación Completa
- **[Design Document](../.kiro/specs/integration-max-vicente/design.md)** - Documento técnico completo ⭐
- **[Requirements](../.kiro/specs/integration-max-vicente/requirements.md)** - Requisitos funcionales
- **[README](../.kiro/specs/integration-max-vicente/README.md)** - Índice de documentación

### Documentación de Integración
- **[ESTADO_MODULOS_INTEGRACION.md](ESTADO_MODULOS_INTEGRACION.md)** - Estado detallado de todos los módulos
- **[FASE_1.1_INTEGRACION_MODULOS_MAX.md](FASE_1.1_INTEGRACION_MODULOS_MAX.md)** - Resultado Fase 1.1
- **[FASE_1.2_ANALISIS_COMPARATIVO.md](FASE_1.2_ANALISIS_COMPARATIVO.md)** - Análisis comparativo detallado
- **[FASE_1.2_RESULTADO_INTEGRACION.md](FASE_1.2_RESULTADO_INTEGRACION.md)** - Resultado Fase 1.2
- **[FASE_1.2_RESUMEN_EJECUTIVO.md](FASE_1.2_RESUMEN_EJECUTIVO.md)** - Resumen ejecutivo Fase 1.2

### Código
- Módulos Max: `max/src/modules/`
- Módulos Vicente: `glue/modules/`
- Tests: `glue/tests/`

---

## 🚀 Cómo Usar Este Documento

### Para Desarrolladores
1. Leer el design document completo para entender la arquitectura
2. Revisar las decisiones de diseño y su rationale
3. Seguir las interfaces y contratos definidos
4. Implementar según el plan de fases

### Para Revisores
1. Validar que las decisiones de diseño son apropiadas
2. Verificar que los riesgos están identificados y mitigados
3. Confirmar que el plan de implementación es realista
4. Revisar que las interfaces son claras y consistentes

### Para Project Managers
1. Usar el plan de implementación para tracking
2. Monitorear riesgos identificados
3. Validar progreso contra fases definidas
4. Coordinar recursos según prioridades

---

## 📊 Métricas de Progreso

**Módulos Completados:** 16/17 (94%)

**Fases Completadas:**
- ✅ Fase 1.1: Integración de Módulos Únicos
- ✅ Fase 1.2: Análisis Comparativo (design document completado)
- ⏳ Fase 1.2: Fusión de Módulos (en progreso)
- ⏳ Fase 1.3: SchemaEvolutionManager
- ⏳ Fase 1.4: Pipeline Unificado

**Documentación:**
- ✅ Design document completo
- ✅ Análisis comparativo detallado
- ✅ Estrategias de fusión definidas
- ✅ Interfaces y contratos documentados
- ✅ Plan de implementación por fases

---

## ✅ Próximos Pasos

### Inmediatos (Esta Semana)
1. **Fusionar DataTypeConverter** (Fase 1.2)
   - Combinar validaciones de Vicente con inferencia de Max
   - Crear tests de integración
   - Actualizar documentación

2. **Fusionar DataNormalizer** (Fase 1.2)
   - Combinar regex de Vicente con optimizaciones de Max
   - Validar performance
   - Actualizar tests

3. **Fusionar DataGapHandler** (Fase 1.2)
   - Combinar metadata tracking con filling automático
   - Crear tests exhaustivos
   - Documentar comportamiento

### Corto Plazo (Próximas 2 Semanas)
1. **Fusionar IcebergWriter** (Fase 1.2)
   - Combinar ACID de Vicente con retry logic de Max
   - Tests de resiliencia
   - Validar en ambiente real

2. **Implementar SchemaEvolutionManager** (Fase 1.3)
   - Diseño de interfaz
   - Implementación base
   - Property tests

3. **Pipeline Unificado** (Fase 1.4)
   - Integrar todos los módulos
   - Tests end-to-end
   - Documentación completa

---

## 📝 Notas Importantes

### Principios de Integración
1. **Preservar lo mejor de ambos** - No descartar funcionalidad útil
2. **Mantener compatibilidad** - No romper código existente
3. **Testing exhaustivo** - Validar cada fusión
4. **Documentación clara** - Explicar decisiones y cambios

### Criterios de Éxito
- ✅ Todos los módulos integrados sin conflictos
- ✅ Tests pasando (unit + property + integration)
- ✅ Performance igual o mejor que implementaciones originales
- ✅ Documentación completa y actualizada
- ✅ Pipeline end-to-end funcionando en AWS Glue

---

**Documento creado:** 19 de Febrero, 2026  
**Última actualización:** 19 de Febrero, 2026  
**Estado:** Design document completado - Fase 1.2 en progreso
