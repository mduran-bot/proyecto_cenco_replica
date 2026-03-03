# Integración Max-Vicente: Requirements

**Fecha:** 18 de Febrero, 2026  
**Estado:** 🚧 En Progreso  
**Objetivo:** Integrar el pipeline Bronze-to-Silver de Max con los módulos robustos de Vicente

---

## 1. Contexto y Motivación

### 1.1 Situación Actual

Tenemos dos implementaciones complementarias del sistema de transformación de datos:

**Trabajo de Max (`max/`):**
- Pipeline completo Bronze-to-Silver funcional
- 10 módulos de transformación implementados
- Validado con LocalStack y datos reales
- Orquestación con ETLPipeline
- Configuración JSON flexible

**Trabajo de Vicente (`glue/`):**
- Módulos con property-based testing robusto
- IcebergManager con snapshots y rollback
- SchemaEvolutionManager completo
- Tests con Hypothesis (100+ casos por property)
- Validaciones exhaustivas

**Problema:** Los componentes NO han sido integrados ni probados juntos como un sistema completo.

### 1.2 Valor de la Integración

- Combinar pipeline funcional de Max con testing robusto de Vicente
- Obtener módulos únicos de Max (JSONFlattener, DataCleaner, etc.)
- Aprovechar property-based testing de Vicente
- Crear sistema completo end-to-end validado

---

## 2. User Stories

### US-1: Como desarrollador, quiero tener todos los módulos en un solo lugar
**Criterios de aceptación:**
- 1.1 Todos los módulos de Max están copiados a `glue/modules/`
- 1.2 No hay duplicación de archivos
- 1.3 Los imports funcionan correctamente
- 1.4 La estructura de directorios es clara y mantenible

### US-2: Como desarrollador, quiero módulos fusionados que combinen lo mejor de ambas implementaciones
**Criterios de aceptación:**
- 2.1 DataTypeConverter fusionado mantiene validaciones de Vicente y lógica PySpark de Max
- 2.2 DataNormalizer fusionado mantiene regex robustos de Vicente y transformaciones de Max
- 2.3 DataGapHandler fusionado mantiene metadata flags de Vicente y lógica de Max
- 2.4 IcebergManager fusionado mantiene snapshots/rollback de Vicente y simplicidad de Max
- 2.5 Todos los módulos fusionados tienen tests que pasan

### US-3: Como desarrollador, quiero un pipeline unificado que use todos los módulos integrados
**Criterios de aceptación:**
- 3.1 ETLPipeline puede ejecutar todos los módulos en secuencia
- 3.2 Pipeline puede leer desde Bronze (S3)
- 3.3 Pipeline puede escribir a Silver (S3 + Iceberg)
- 3.4 Pipeline maneja errores gracefully
- 3.5 Pipeline tiene logging completo

### US-4: Como desarrollador, quiero tests que validen la integración completa
**Criterios de aceptación:**
- 4.1 Tests unitarios pasan para todos los módulos
- 4.2 Property-based tests pasan para módulos críticos
- 4.3 Tests de integración validan flujo end-to-end
- 4.4 Tests pueden ejecutarse en ambiente local (con limitaciones de Windows)
- 4.5 Documentación explica cómo ejecutar tests

### US-5: Como desarrollador, quiero documentación clara del sistema integrado
**Criterios de aceptación:**
- 5.1 README actualizado explica arquitectura completa
- 5.2 Documentación de cada módulo está actualizada
- 5.3 Guía de desarrollo local incluye ambos enfoques
- 5.4 Plan de deployment a AWS Glue está documentado
- 5.5 Troubleshooting guide cubre problemas comunes

---

## 3. Requerimientos Funcionales

### RF-1: Copiar Módulos Únicos de Max
**Descripción:** Copiar módulos que solo existen en Max a `glue/modules/`

**Módulos a copiar:**
- `json_flattener.py` - Aplanamiento de JSON anidados
- `data_cleaner.py` - Limpieza específica de datos
- `duplicate_detector.py` - Detección de duplicados
- `conflict_resolver.py` - Resolución de conflictos

**Validación:**
- Módulos copiados sin errores de sintaxis
- Imports funcionan correctamente
- Documentación de cada módulo está presente

### RF-2: Fusionar Módulos Duplicados
**Descripción:** Combinar módulos que existen en ambas implementaciones

**Módulos a fusionar:**

#### RF-2.1: DataTypeConverter
- **Base:** Vicente (validaciones exhaustivas)
- **Agregar:** Lógica PySpark de Max
- **Resultado:** Módulo híbrido con validaciones + transformaciones

#### RF-2.2: DataNormalizer
- **Base:** Vicente (regex robustos)
- **Agregar:** Transformaciones PySpark de Max
- **Resultado:** Módulo híbrido con normalización completa

#### RF-2.3: DataGapHandler
- **Base:** Vicente (metadata flags)
- **Agregar:** Lógica de gaps de Max
- **Resultado:** Módulo híbrido con manejo completo de gaps

#### RF-2.4: IcebergManager/Writer
- **Base:** Vicente (snapshots, rollback, compaction)
- **Agregar:** Simplificaciones de Max
- **Resultado:** Módulo completo y usable

**Validación:**
- Tests unitarios pasan para módulos fusionados
- Property-based tests pasan (donde aplique)
- No hay regresiones en funcionalidad

### RF-3: Integrar SchemaEvolutionManager
**Descripción:** Agregar SchemaEvolutionManager de Vicente al pipeline

**Acciones:**
- Copiar `schema_evolution_manager.py` a `glue/modules/`
- Integrar en ETLPipeline
- Agregar configuración necesaria
- Crear tests de integración

**Validación:**
- SchemaEvolutionManager detecta cambios de schema
- Cambios se aplican correctamente a tablas Iceberg
- Rollback funciona en caso de error

### RF-4: Pipeline Unificado
**Descripción:** Crear pipeline que use todos los módulos integrados

**Componentes:**
- ETLPipeline actualizado con todos los módulos
- Configuración JSON que incluye todos los módulos
- Logging completo de cada etapa
- Manejo de errores robusto

**Flujo del pipeline:**
1. Lectura desde Bronze (S3)
2. JSONFlattener (si hay JSON anidados)
3. DataCleaner (limpieza inicial)
4. DataNormalizer (normalización de formatos)
5. DataTypeConverter (conversión de tipos)
6. DuplicateDetector (detección de duplicados)
7. ConflictResolver (resolución de conflictos)
8. DataGapHandler (manejo de gaps)
9. SchemaEvolutionManager (detección y aplicación de cambios)
10. IcebergWriter (escritura a Silver)

**Validación:**
- Pipeline ejecuta sin errores con datos de prueba
- Cada módulo se ejecuta en el orden correcto
- Datos se transforman correctamente
- Escritura a Iceberg funciona

### RF-5: Tests de Integración
**Descripción:** Crear tests que validen el sistema completo

**Tests a implementar:**
- `test_pipeline_end_to_end.py` - Pipeline completo Bronze → Silver
- `test_schema_evolution_integration.py` - Schema evolution en pipeline
- `test_deduplication_flow.py` - Flujo de deduplicación completo
- `test_error_handling.py` - Manejo de errores del pipeline

**Validación:**
- Todos los tests pasan en ambiente local (con limitaciones)
- Tests documentan comportamiento esperado
- Tests pueden ejecutarse en CI/CD

---

## 4. Requerimientos No Funcionales

### RNF-1: Compatibilidad
- Código debe funcionar en AWS Glue 4.0 (PySpark)
- Debe ser compatible con Python 3.11
- Debe funcionar con Apache Iceberg 1.4+

### RNF-2: Mantenibilidad
- Código debe seguir PEP 8
- Funciones deben tener docstrings
- Módulos deben tener documentación clara
- Estructura de directorios debe ser intuitiva

### RNF-3: Testing
- Cobertura de código > 80% para módulos críticos
- Property-based tests para lógica compleja
- Tests de integración para flujos end-to-end
- Tests deben ejecutarse en < 5 minutos

### RNF-4: Performance
- Pipeline debe procesar 1M registros en < 10 minutos
- Transformaciones deben ser eficientes (sin collect() innecesarios)
- Escritura a Iceberg debe usar batch writes

### RNF-5: Observabilidad
- Logging completo de cada etapa
- Métricas de performance (tiempo, registros procesados)
- Manejo de errores con contexto claro
- Trazabilidad de datos (correlation IDs)

---

## 5. Restricciones y Limitaciones

### Limitación 1: Windows Development
- PySpark no puede escribir archivos en Windows (winutils.exe)
- Tests de escritura deben ejecutarse en Linux/Docker
- Desarrollo local limitado a validación de transformaciones

### Limitación 2: LocalStack
- LocalStack no soporta todas las features de Iceberg
- Tests de Iceberg deben ejecutarse contra S3 real o en AWS Glue
- Validación local es parcial

### Limitación 3: Tiempo
- Integración debe completarse en 1-2 días
- No podemos reescribir todo desde cero
- Debemos priorizar funcionalidad crítica

---

## 6. Dependencias

### Dependencias Técnicas
- PySpark 3.3+
- Apache Iceberg 1.4+
- Hypothesis (para property-based testing)
- pytest (para tests unitarios)
- LocalStack (para desarrollo local)

### Dependencias de Código
- Módulos de Max en `max/src/modules/`
- Módulos de Vicente en `glue/modules/`
- Tests de Vicente en `glue/tests/property/`
- Configuración de Max en `max/config/`

---

## 7. Criterios de Éxito

### Fase 1: Integración de Código (1 día)
- ✅ Todos los módulos de Max copiados a `glue/modules/`
- ✅ Módulos duplicados fusionados
- ✅ SchemaEvolutionManager integrado
- ✅ Imports funcionan correctamente

### Fase 2: Pipeline Unificado (1 día)
- ✅ ETLPipeline actualizado con todos los módulos
- ✅ Configuración JSON completa
- ✅ Pipeline ejecuta sin errores con datos de prueba
- ✅ Logging completo implementado

### Fase 3: Testing (1 día)
- ✅ Tests unitarios pasan para todos los módulos
- ✅ Property-based tests pasan
- ✅ Tests de integración implementados y pasando
- ✅ Documentación de tests completa

### Fase 4: Documentación (medio día)
- ✅ README actualizado
- ✅ Guía de desarrollo local actualizada
- ✅ Arquitectura documentada
- ✅ Plan de deployment a AWS Glue

---

## 8. Riesgos

### Riesgo 1: Incompatibilidades entre módulos
**Probabilidad:** Media  
**Impacto:** Alto  
**Mitigación:** Probar cada módulo individualmente antes de integrar

### Riesgo 2: Tests fallan después de fusión
**Probabilidad:** Alta  
**Impacto:** Medio  
**Mitigación:** Mantener tests separados hasta validar integración

### Riesgo 3: Performance degradado
**Probabilidad:** Baja  
**Impacto:** Alto  
**Mitigación:** Benchmarking antes y después de integración

### Riesgo 4: Pérdida de funcionalidad
**Probabilidad:** Baja  
**Impacto:** Alto  
**Mitigación:** Mantener branches separadas hasta validar todo

---

## 9. Plan de Rollback

Si la integración falla:
1. Revertir cambios en `glue/modules/`
2. Restaurar módulos originales de Vicente
3. Mantener código de Max en `max/` separado
4. Documentar problemas encontrados
5. Replantear estrategia de integración

---

## 10. Próximos Pasos

1. **Crear spec de diseño** con arquitectura detallada
2. **Crear tasks** para cada fase de integración
3. **Ejecutar Fase 1:** Copiar y fusionar módulos
4. **Ejecutar Fase 2:** Pipeline unificado
5. **Ejecutar Fase 3:** Testing completo
6. **Ejecutar Fase 4:** Documentación

---

**Documento creado:** 18 de Febrero, 2026  
**Última actualización:** 18 de Febrero, 2026  
**Estado:** Requirements definidos - Listo para diseño
