# Plan de Adaptación a Estructura S3 Gold Existente

**Fecha**: 17 de Febrero de 2026  
**Objetivo**: Adaptar el pipeline de datos de Janis para que genere datos en S3 Gold con la misma estructura que el sistema actual de producción de Cencosud

---

## Resumen Ejecutivo

Hemos analizado la estructura actual de S3 Gold en producción de Cencosud y confirmado que:

1. **Redshift consume datos desde S3 Gold** en el bucket `cencosud.test.super.peru.analytics`
2. **La estructura está bien definida** con patrones consistentes
3. **Nuestro pipeline debe replicar exactamente** esta estructura para mantener compatibilidad

---

## Hallazgos Clave

### Estructura Actual de Producción

```
Flujo Actual:
MySQL (Janis) → S3 Bronze → S3 Silver → S3 Gold → Redshift

Buckets:
- Bronze:  cencosud.test.super.peru.raw
- Silver:  cencosud.test.super.peru.raw-structured
- Gold:    cencosud.test.super.peru.analytics
```

### Formato de Archivos en Gold

- **Formato**: Apache Parquet con compresión Snappy
- **Particionamiento**: `year=YYYY/month=MM/day=DD/`
- **Naming**: `part-{n}-{uuid}.c000.snappy.parquet`
- **Tamaño**: 64-128 MB (optimizado para Redshift COPY)
- **Ubicación**: `ExternalAccess/{sistema}_smk_pe/automatico/{tabla}/`

### Ejemplo Real

```
s3://cencosud.test.super.peru.analytics/
  ExternalAccess/
    milocal_smk_pe/
      automatico/
        vw_milocal_centro/
          year=2024/
            month=07/
              day=10/
                part-00000-{uuid}.c000.snappy.parquet
```

---

## Propuesta de Estructura para Datos de Janis

### Ubicación Recomendada

```
s3://cencosud.test.super.peru.analytics/
  ExternalAccess/
    janis_smk_pe/              ← NUEVO
      automatico/
        orders/
          year=YYYY/month=MM/day=DD/
            part-{n}-{uuid}.c000.snappy.parquet
        order_items/
          year=YYYY/month=MM/day=DD/
            part-{n}-{uuid}.c000.snappy.parquet
        products/
          year=YYYY/month=MM/day=DD/
            part-{n}-{uuid}.c000.snappy.parquet
        skus/
          year=YYYY/month=MM/day=DD/
            part-{n}-{uuid}.c000.snappy.parquet
        stores/
          year=YYYY/month=MM/day=DD/
            part-{n}-{uuid}.c000.snappy.parquet
        stock/
          year=YYYY/month=MM/day=DD/
            part-{n}-{uuid}.c000.snappy.parquet
        prices/
          year=YYYY/month=MM/day=DD/
            part-{n}-{uuid}.c000.snappy.parquet
```

**Razones:**
- Consistente con patrón existente (`milocal_smk_pe`, `prime_smk_pe`)
- Separación clara de datos de Janis
- Fácil de gestionar y monitorear
- No interfiere con datos existentes

---

## Specs que Requieren Actualización

### 1. Spec: 02-initial-data-load ⭐ CRÍTICO

**Cambios Necesarios:**

- ✅ Requirement 3: Cambiar de "Direct Data Extraction to Gold Layer" a "Data Extraction to Bronze Layer"
- ✅ Requirement 6: Actualizar para generar archivos Parquet en formato compatible con estructura Gold existente
- ✅ Agregar nuevo Requirement: "S3 Gold Structure Compatibility"
  - Debe especificar estructura de carpetas `janis_smk_pe/automatico/{tabla}/`
  - Debe especificar particionamiento `year=YYYY/month=MM/day=DD/`
  - Debe especificar formato Parquet con Snappy
  - Debe especificar naming convention de archivos

**Impacto**: ALTO - Este spec define la carga inicial y debe seguir el flujo Bronze→Silver→Gold

---

### 2. Spec: data-transformation ⭐ CRÍTICO

**Cambios Necesarios:**

- ✅ Requirement 6: "Silver to Gold Transformation"
  - Actualizar para generar estructura compatible con S3 Gold existente
  - Especificar ubicación exacta: `ExternalAccess/janis_smk_pe/automatico/`
  - Definir formato de archivos Parquet con Snappy
  - Implementar particionamiento por fecha
  
- ✅ Agregar nuevo Requirement: "Gold Layer Structure Compliance"
  - Validar que archivos generados cumplan con formato esperado
  - Verificar tamaños de archivo (64-128 MB)
  - Validar naming convention
  - Asegurar compatibilidad con Redshift COPY

**Impacto**: ALTO - Este spec define las transformaciones Bronze→Silver→Gold

---

### 3. Spec: webhook-ingestion

**Cambios Necesarios:**

- ✅ Requirement 5: "Data Buffering and Streaming"
  - Actualizar particionamiento para ser compatible con estructura final Gold
  - Asegurar que metadata incluida sea compatible con transformaciones downstream

- ✅ Requirement 6: "Bronze Layer Storage"
  - Especificar estructura de carpetas compatible con pipeline completo
  - Ubicación: `s3://cencosud.test.super.peru.raw/janis/`

**Impacto**: MEDIO - Los webhooks alimentan Bronze, que luego se transforma a Gold

---

### 4. Spec: api-polling

**Cambios Necesarios:**

- ✅ Requirement 9: "Data Delivery to Kinesis Firehose"
  - Actualizar metadata para incluir información necesaria para transformaciones
  - Asegurar compatibilidad con estructura Bronze esperada

**Impacto**: MEDIO - El polling alimenta Bronze, que luego se transforma a Gold

---

### 5. Spec: redshift-loading ⭐ CRÍTICO

**Cambios Necesarios:**

- ✅ Requirement 1: "Existing Redshift Integration"
  - Actualizar para cargar desde nueva ubicación en S3 Gold
  - Especificar path: `s3://cencosud.test.super.peru.analytics/ExternalAccess/janis_smk_pe/automatico/`

- ✅ Requirement 3: "Incremental Data Loading"
  - Actualizar manifest files para apuntar a nueva estructura
  - Usar particionamiento `year=YYYY/month=MM/day=DD/` para cargas incrementales

- ✅ Agregar nuevo Requirement: "S3 Gold Path Configuration"
  - Definir paths exactos para cada tabla
  - Configurar COPY commands con paths correctos
  - Implementar validación de estructura antes de carga

**Impacto**: ALTO - Redshift debe cargar desde la ubicación correcta en Gold

---

## Cambios Técnicos Requeridos

### 1. Módulos de Glue

**Nuevos Módulos Necesarios:**

```python
# glue/modules/gold_structure_generator.py
class GoldStructureGenerator:
    """
    Genera archivos Parquet en estructura compatible con S3 Gold existente
    """
    def generate_parquet_file(
        self,
        data: DataFrame,
        table_name: str,
        partition_date: datetime,
        output_bucket: str = "cencosud.test.super.peru.analytics"
    ):
        # Genera path: ExternalAccess/janis_smk_pe/automatico/{table}/year=YYYY/month=MM/day=DD/
        # Escribe Parquet con Snappy compression
        # Naming: part-{n}-{uuid}.c000.snappy.parquet
        pass
```

**Módulos a Actualizar:**

- `data_type_converter.py` - Asegurar conversiones compatibles con Parquet
- `data_normalizer.py` - Normalizar datos para formato Gold
- `data_gap_handler.py` - Manejar campos faltantes según estructura Gold

### 2. Configuración de Terraform

**Módulos a Actualizar:**

```hcl
# terraform/modules/glue/main.tf
resource "aws_glue_job" "silver_to_gold" {
  # Actualizar para generar estructura Gold correcta
  default_arguments = {
    "--gold_bucket"     = "cencosud.test.super.peru.analytics"
    "--gold_prefix"     = "ExternalAccess/janis_smk_pe/automatico"
    "--partition_format" = "year={year}/month={month}/day={day}"
    "--file_format"     = "parquet"
    "--compression"     = "snappy"
  }
}
```

### 3. Scripts de Validación

**Nuevo Script:**

```python
# scripts/validate_gold_structure.py
"""
Valida que archivos en S3 Gold cumplan con estructura esperada
"""
def validate_gold_structure(bucket, prefix):
    # Verificar estructura de carpetas
    # Validar formato de archivos Parquet
    # Verificar particionamiento
    # Validar naming convention
    # Verificar tamaños de archivo
    pass
```

---

## Plan de Implementación

### Fase 1: Actualización de Specs (Esta Semana)

**Prioridad**: CRÍTICA

1. ✅ Analizar estructura S3 Gold actual (COMPLETADO)
2. ⏳ Actualizar spec `02-initial-data-load`
3. ⏳ Actualizar spec `data-transformation`
4. ⏳ Actualizar spec `redshift-loading`
5. ⏳ Actualizar spec `webhook-ingestion`
6. ⏳ Actualizar spec `api-polling`

**Tiempo Estimado**: 2-3 días

---

### Fase 2: Desarrollo de Módulos (Semana Próxima)

**Prioridad**: ALTA

1. ⏳ Implementar `gold_structure_generator.py`
2. ⏳ Actualizar módulos de transformación existentes
3. ⏳ Crear scripts de validación
4. ⏳ Actualizar configuración de Terraform
5. ⏳ Crear tests unitarios

**Tiempo Estimado**: 5-7 días

---

### Fase 3: Testing y Validación (Semana 3)

**Prioridad**: ALTA

1. ⏳ Probar generación de archivos Parquet
2. ⏳ Validar estructura de carpetas
3. ⏳ Probar carga en Redshift desde nueva estructura
4. ⏳ Validar compatibilidad de esquemas
5. ⏳ Performance testing

**Tiempo Estimado**: 5-7 días

---

### Fase 4: Migración y Cutover (Semana 4-5)

**Prioridad**: MEDIA

1. ⏳ Carga inicial de datos históricos
2. ⏳ Activar pipeline en tiempo real
3. ⏳ Monitoreo y ajustes
4. ⏳ Cutover a producción

**Tiempo Estimado**: 7-10 días

---

## Riesgos y Mitigaciones

### Riesgo 1: Incompatibilidad de Esquemas

**Descripción**: Los esquemas de datos de API Janis pueden no mapear perfectamente a estructura Gold

**Mitigación**:
- Crear matriz de mapeo detallada API → Gold
- Implementar validación de esquemas en cada etapa
- Crear tests de integración end-to-end

### Riesgo 2: Performance de Transformaciones

**Descripción**: Transformaciones Bronze→Silver→Gold pueden ser lentas

**Mitigación**:
- Optimizar jobs de Glue con particionamiento
- Implementar procesamiento paralelo
- Usar caching cuando sea posible

### Riesgo 3: Tamaño de Archivos

**Descripción**: Archivos muy pequeños o muy grandes afectan performance de Redshift

**Mitigación**:
- Implementar batching inteligente (64-128 MB)
- Monitorear tamaños de archivo
- Ajustar estrategia de particionamiento si es necesario

---

## Métricas de Éxito

### Criterios de Aceptación

1. ✅ Archivos generados en S3 Gold siguen estructura exacta de producción
2. ✅ Formato Parquet con Snappy compression
3. ✅ Particionamiento correcto por fecha
4. ✅ Naming convention compatible
5. ✅ Tamaños de archivo entre 64-128 MB
6. ✅ Redshift puede cargar datos sin modificaciones
7. ✅ Queries de BI funcionan sin cambios

### KPIs

- **Compatibilidad de Estructura**: 100%
- **Tasa de Éxito de Carga en Redshift**: >99.9%
- **Tiempo de Transformación Bronze→Gold**: <15 minutos
- **Tamaño Promedio de Archivos**: 64-128 MB
- **Errores de Esquema**: 0

---

## Próximos Pasos Inmediatos

### Acción 1: Revisar y Aprobar Plan

**Responsable**: Equipo de Arquitectura  
**Plazo**: Hoy

**Preguntas a Resolver:**
1. ¿Aprobamos la ubicación `janis_smk_pe` en S3 Gold?
2. ¿Hay alguna consideración adicional de naming?
3. ¿Necesitamos coordinación con equipo de BI?

### Acción 2: Actualizar Specs

**Responsable**: Equipo de Desarrollo  
**Plazo**: 2-3 días

**Specs a Actualizar:**
1. `02-initial-data-load`
2. `data-transformation`
3. `redshift-loading`
4. `webhook-ingestion`
5. `api-polling`

### Acción 3: Crear Matriz de Mapeo

**Responsable**: Equipo de Datos  
**Plazo**: 3-4 días

**Entregables:**
- Mapeo detallado API Janis → Estructura Gold
- Esquemas Parquet para cada tabla
- Transformaciones requeridas documentadas

---

## Documentos Relacionados

- ✅ [Análisis Estructura S3 Gold Producción](./Análisis%20Estructura%20S3%20Gold%20Producción.md)
- ✅ [Análisis de Esquema Redshift - Resumen Ejecutivo](./Análisis%20de%20Esquema%20Redshift%20-%20Resumen%20Ejecutivo.md)
- ⏳ [Matriz de Mapeo API Janis → S3 Gold](./Matriz%20Mapeo%20Janis%20Gold.md) (Por crear)
- ⏳ [Esquemas Parquet Detallados](./Esquemas%20Parquet%20Janis.md) (Por crear)

---

## Conclusiones

1. **Estructura Clara**: Hemos identificado la estructura exacta que debe seguir S3 Gold
2. **Plan Definido**: Tenemos un plan claro de actualización de specs y desarrollo
3. **Compatibilidad Asegurada**: Siguiendo este plan, mantendremos compatibilidad total con Redshift
4. **Riesgos Identificados**: Conocemos los riesgos y tenemos mitigaciones
5. **Timeline Realista**: 4-5 semanas para implementación completa

**Recomendación**: Proceder con actualización de specs inmediatamente.

---

**Documento generado**: 17 de Febrero de 2026  
**Estado**: ✅ Plan Completo - Listo para Aprobación  
**Próxima Acción**: Revisar y aprobar con equipo
