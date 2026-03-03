# Plan de Integración: Trabajo de Max y Vicente

**Fecha:** 18 de Febrero, 2026  
**Objetivo:** Integrar el pipeline Bronze-to-Silver de Max con los módulos robustos de Vicente

---

## Estado Actual

### ✅ Trabajo de Max (Rama: `bronze-to-silver-max`)

**Archivos descargados a `max/`:**
- Pipeline completo funcional con LocalStack
- 10 módulos de transformación implementados
- Configuración JSON flexible
- Tests con datos reales
- Terraform para infraestructura local
- Documentación completa

**Módulos implementados:**
1. JSONFlattener - Aplana JSON anidados
2. DataCleaner - Limpieza de datos
3. DataNormalizer - Normalización de formatos
4. DataTypeConverter - Conversión de tipos
5. DuplicateDetector - Detección de duplicados
6. ConflictResolver - Resolución de conflictos
7. DataGapHandler - Manejo de gaps
8. IcebergTableManager - Gestión de tablas Iceberg
9. IcebergWriter - Escritura a Iceberg
10. ETLPipeline - Orquestador

### ✅ Trabajo de Vicente (Rama: `main` + `feature/task-11-schema-evolution`)

**Archivos en `glue/`:**
- Módulos con property-based testing
- Schema evolution management completo
- Documentación exhaustiva
- Tests con Hypothesis
- Validaciones robustas

**Módulos implementados:**
1. DataTypeConverter - Con validaciones exhaustivas
2. DataNormalizer - Con regex robustos
3. DataGapHandler - Con metadata flags
4. IcebergManager - Con snapshots y rollback
5. IcebergWriter - Con ACID transactions
6. SchemaEvolutionManager - Completo con rollback

---

## Análisis de Compatibilidad

### ✅ Compatible sin Conflictos

Los trabajos de Max y Vicente son **completamente compatibles** porque:

1. **Ubicaciones diferentes:**
   - Max: `max/` (nueva carpeta)
   - Vicente: `glue/` (carpeta existente)
   - **No hay conflictos de archivos**

2. **Enfoques complementarios:**
   - Max: Pipeline end-to-end funcional
   - Vicente: Módulos robustos con testing
   - **Se pueden fusionar sin problemas**

3. **Módulos duplicados son mejorables:**
   - Ambos tienen DataTypeConverter, DataNormalizer, etc.
   - Podemos tomar lo mejor de cada implementación
   - **Fusión enriquecerá ambos trabajos**

---

## Plan de Integración (3 Fases)

### Fase 1: Validación y Testing (HOY - 1-2 horas)

**Objetivo:** Verificar que el pipeline de Max funciona correctamente

**Pasos:**
1. ✅ Descargar carpeta `max/` (COMPLETADO)
2. ⏳ Instalar dependencias de Max
3. ⏳ Verificar que LocalStack está corriendo
4. ⏳ Ejecutar pipeline de Max con datos de prueba
5. ⏳ Validar resultados en S3 Silver

**Comandos:**
```bash
# Instalar dependencias de Max
cd max
pip install -r requirements.txt

# Verificar LocalStack
docker ps

# Si no está corriendo, iniciar
cd terraform
terraform init
terraform apply

# Ejecutar pipeline
cd ..
python run_pipeline_to_silver.py
```

**Criterios de éxito:**
- Pipeline ejecuta sin errores
- Datos se escriben a S3 Silver
- Transformaciones se aplican correctamente

---

### Fase 2: Fusión de Módulos (MAÑANA - 4-6 horas)

**Objetivo:** Combinar lo mejor de ambas implementaciones

#### 2.1 Adoptar Módulos Únicos de Max

**Copiar a `glue/modules/`:**
- `json_flattener.py` (solo Max lo tiene)
- `duplicate_detector.py` (solo Max lo tiene)
- `conflict_resolver.py` (solo Max lo tiene)
- `data_cleaner.py` (solo Max lo tiene)

**Acción:**
```bash
cp max/src/modules/json_flattener.py glue/modules/
cp max/src/modules/duplicate_detector.py glue/modules/
cp max/src/modules/conflict_resolver.py glue/modules/
cp max/src/modules/data_cleaner.py glue/modules/
```

#### 2.2 Fusionar Módulos Duplicados

**DataTypeConverter:**
- Base: Vicente (más validaciones)
- Agregar: Lógica PySpark de Max
- Resultado: Módulo híbrido robusto

**DataNormalizer:**
- Base: Vicente (regex más robustos)
- Agregar: Integración PySpark de Max
- Resultado: Módulo híbrido robusto

**DataGapHandler:**
- Base: Vicente (metadata flags)
- Agregar: Lógica de Max
- Resultado: Módulo híbrido robusto

**IcebergManager/Writer:**
- Base: Vicente (snapshots, rollback, compaction)
- Agregar: Simplificaciones de Max
- Resultado: Módulo completo y usable

#### 2.3 Integrar SchemaEvolutionManager

**Agregar a pipeline de Max:**
- Copiar `schema_evolution_manager.py` a `max/src/modules/`
- Integrar en `etl_pipeline.py`
- Agregar configuración en JSON

---

### Fase 3: Pipeline Unificado (PRÓXIMA SEMANA - 2-3 días)

**Objetivo:** Crear pipeline único que combine ambos trabajos

#### 3.1 Estructura Propuesta

```
glue/
├── modules/              # Todos los módulos fusionados
│   ├── json_flattener.py
│   ├── data_cleaner.py
│   ├── data_normalizer.py
│   ├── data_type_converter.py
│   ├── duplicate_detector.py
│   ├── conflict_resolver.py
│   ├── data_gap_handler.py
│   ├── iceberg_manager.py
│   ├── iceberg_writer.py
│   └── schema_evolution_manager.py
├── pipeline/
│   ├── etl_pipeline.py       # De Max (mejorado)
│   └── bronze_to_silver_job.py
├── config/
│   ├── pipeline_config.json  # De Max
│   └── conversion_rules.py   # De Vicente
├── tests/
│   ├── unit/                 # Tests de Max
│   ├── property/             # Tests de Vicente
│   └── integration/          # Nuevos tests E2E
└── scripts/
    ├── run_local.py          # De Max
    └── run_aws.py            # Nuevo
```

#### 3.2 Crear Tests de Integración

**Nuevos tests en `glue/tests/integration/`:**
- `test_pipeline_end_to_end.py`
- `test_schema_evolution_in_pipeline.py`
- `test_deduplication_flow.py`

#### 3.3 Documentación Unificada

**Actualizar:**
- `glue/README.md` - Combinar ambas documentaciones
- `glue/LOCAL_DEVELOPMENT.md` - Agregar LocalStack de Max
- Crear `glue/ARCHITECTURE.md` - Explicar diseño completo

---

## Tareas Inmediatas (Próximas 2 horas)

### 1. Probar Pipeline de Max ⏳

```bash
# Terminal 1: Verificar/Iniciar LocalStack
cd max/terraform
terraform init
terraform apply

# Terminal 2: Ejecutar pipeline
cd max
python run_pipeline_to_silver.py
```

**Verificar:**
- ¿El pipeline ejecuta sin errores?
- ¿Los datos se escriben a S3?
- ¿Las transformaciones funcionan?

### 2. Documentar Resultados ⏳

Crear `Documentacion/RESULTADOS_PRUEBA_MAX.md` con:
- Capturas de pantalla de ejecución
- Logs importantes
- Datos de salida
- Problemas encontrados
- Soluciones aplicadas

### 3. Comparar Salidas ⏳

**Comparar:**
- Esquema de datos de salida de Max
- Esquema esperado según requirements
- Identificar diferencias

---

## Decisiones Pendientes

### 1. Estructura de Directorios Final

**Opción A:** Mantener `max/` y `glue/` separados
- Pros: No rompe nada existente
- Contras: Duplicación de código

**Opción B:** Fusionar todo en `glue/`
- Pros: Código unificado, más mantenible
- Contras: Requiere más trabajo de integración

**Recomendación:** Opción B (fusionar en `glue/`)

### 2. Configuración: JSON vs Python

**Opción A:** Solo JSON (enfoque de Max)
- Pros: Más flexible, fácil de modificar
- Contras: Menos type-safe

**Opción B:** Solo Python (enfoque de Vicente)
- Pros: Type-safe, validación en tiempo de desarrollo
- Contras: Menos flexible

**Opción C:** Híbrido (JSON + Python)
- Pros: Flexibilidad + Type safety
- Contras: Más complejo

**Recomendación:** Opción C (híbrido)

### 3. Testing Strategy

**Mantener ambos enfoques:**
- Unit tests (de Max) para funcionalidad básica
- Property-based tests (de Vicente) para correctness
- Integration tests (nuevos) para E2E

---

## Métricas de Éxito

### Fase 1 (HOY)
- ✅ Pipeline de Max ejecuta sin errores
- ✅ Datos se escriben correctamente a Silver
- ✅ Documentación de resultados completa

### Fase 2 (MAÑANA)
- ✅ Todos los módulos de Max copiados a `glue/`
- ✅ Módulos duplicados fusionados
- ✅ SchemaEvolutionManager integrado
- ✅ Tests unitarios pasan

### Fase 3 (PRÓXIMA SEMANA)
- ✅ Pipeline unificado funcional
- ✅ Tests de integración pasan
- ✅ Documentación completa
- ✅ LocalStack funciona con pipeline completo

---

## Riesgos y Mitigaciones

### Riesgo 1: Incompatibilidades entre módulos
**Mitigación:** Probar cada módulo individualmente antes de integrar

### Riesgo 2: Tests fallan después de fusión
**Mitigación:** Mantener tests separados hasta validar integración

### Riesgo 3: LocalStack no funciona en Windows
**Mitigación:** Documentar workarounds, usar WSL si es necesario

### Riesgo 4: Pérdida de funcionalidad
**Mitigación:** Mantener branches separadas hasta validar todo

---

## Próximos Pasos Inmediatos

1. **AHORA:** Probar pipeline de Max
2. **HOY:** Documentar resultados
3. **MAÑANA:** Comenzar Fase 2 (fusión de módulos)
4. **ESTA SEMANA:** Completar Fase 2
5. **PRÓXIMA SEMANA:** Fase 3 (pipeline unificado)

---

## Notas Importantes

- ✅ No hay conflictos de archivos (carpetas separadas)
- ✅ Ambos trabajos son valiosos y complementarios
- ✅ La integración enriquecerá el proyecto
- ✅ Podemos mantener ambas ramas hasta validar todo
- ✅ El trabajo de Vicente (Task 11) ya está en su propia rama

---

**Preparado por:** Vicente  
**Última actualización:** 2026-02-18 (Fase 1 en progreso)
