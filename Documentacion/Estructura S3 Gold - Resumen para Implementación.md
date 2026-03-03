# Estructura S3 Gold - Resumen para Implementación

**Fecha**: 17 de Febrero de 2026  
**Propósito**: Guía rápida de implementación basada en análisis de estructura S3 Gold existente  
**Documento Completo**: `.kiro/specs/02-initial-data-load/docs/Análisis Estructura S3 Gold Producción.md`

---

## Resumen Ejecutivo

El análisis de la estructura S3 Gold de producción de Cencosud establece los requisitos exactos de formato y organización que deben seguir los datos de Janis para mantener compatibilidad total con el sistema de Redshift existente.

## Estructura de Buckets

### Capas de Datos

```
Bronze:  s3://cencosud.test.super.peru.raw/janis/
Silver:  s3://cencosud.test.super.peru.raw-structured/janis/
Gold:    s3://cencosud.test.super.peru.analytics/ExternalAccess/janis_smk_pe/
```

### Patrón de Organización Gold

```
ExternalAccess/janis_smk_pe/automatico/{tabla}/year=YYYY/month=MM/day=DD/
```

**Ejemplo:**
```
ExternalAccess/janis_smk_pe/automatico/orders/
  └── year=2024/
      └── month=02/
          └── day=17/
              ├── part-00000-a1b2c3d4-e5f6-7890-abcd-ef1234567890.c000.snappy.parquet
              ├── part-00001-b2c3d4e5-f6a7-8901-bcde-f12345678901.c000.snappy.parquet
              └── ...
```

## Especificaciones Técnicas Críticas

### 1. Formato de Archivos

| Característica | Valor Requerido |
|----------------|-----------------|
| Formato | Apache Parquet |
| Compresión | Snappy |
| Encoding | UTF-8 |
| Tamaño Objetivo | 64-128 MB por archivo |
| Naming Pattern | `part-{sequence:05d}-{uuid}.c000.snappy.parquet` |

### 2. Particionamiento

- **Esquema**: `year=YYYY/month=MM/day=DD/`
- **Estilo**: Hive-style partitioning
- **Basado en**: Campo `date_created` o `date_modified` del registro
- **Formato de fecha**: ISO 8601

### 3. Conversiones de Tipos de Datos

| Tipo API Janis | Tipo Parquet | Notas |
|----------------|--------------|-------|
| `string` | `STRING` | Directo |
| `integer` | `INT64` | Para IDs grandes |
| `number` | `DOUBLE` | Para decimales |
| `boolean` | `BOOLEAN` | Directo |
| `timestamp` (Unix) | `TIMESTAMP` | Convertir a ISO 8601 UTC |
| `object` (JSON) | `STRING` | Serializar como JSON string |
| `array` | `STRING` | Serializar como JSON string |

## Entidades Principales y Frecuencias

| Entidad | Carpeta S3 Gold | Partición | Frecuencia |
|---------|-----------------|-----------|------------|
| Orders | `janis_smk_pe/automatico/orders/` | `date_created` | Tiempo real + cada 5 min |
| Order Items | `janis_smk_pe/automatico/order_items/` | `date_created` | Tiempo real + cada 5 min |
| Products | `janis_smk_pe/automatico/products/` | `date_modified` | Cada 1 hora |
| SKUs | `janis_smk_pe/automatico/skus/` | `date_modified` | Cada 1 hora |
| Stores | `janis_smk_pe/automatico/stores/` | `date_modified` | Cada 24 horas |
| Stock | `janis_smk_pe/automatico/stock/` | `date` | Cada 10 minutos |
| Prices | `janis_smk_pe/automatico/prices/` | `date_modified` | Cada 30 minutos |

## Metadata en Archivos

Incluir campos adicionales en cada registro:

```json
{
  "_metadata": {
    "source": "janis-api",
    "ingestion_timestamp": "2026-02-17T19:00:00Z",
    "source_type": "webhook|polling",
    "api_version": "v2",
    "processing_job_id": "glue-job-12345"
  }
}
```

## Transformaciones Requeridas

### 1. Conversión de Tipos de Datos

```python
transformations = {
    # Timestamps
    "date_created": lambda x: convert_unix_to_iso8601(x),
    "date_modified": lambda x: convert_unix_to_iso8601(x),
    
    # Booleanos
    "is_active": lambda x: 1 if x else 0,  # Redshift usa SMALLINT
    
    # JSON a String
    "metadata": lambda x: json.dumps(x) if x else None,
    
    # Decimales
    "amount": lambda x: Decimal(str(x)),
    "price": lambda x: Decimal(str(x))
}
```

### 2. Normalización de Datos

- Trim whitespace de strings
- Normalizar emails a lowercase
- Estandarizar formatos de teléfono (+51XXXXXXXXX)
- Convertir todos los timestamps a UTC
- Validar y limpiar códigos postales

### 3. Campos Calculados

```python
calculated_fields = {
    # Para Orders
    "items_substituted_qty": "COUNT(items WHERE substitute_type = 'substitute')",
    "items_qty_missing": "SUM(quantity - COALESCE(quantity_picked, 0))",
    "total_changes": "amount - originalAmount",
    
    # Para Products
    "is_available": "stock_quantity > 0 AND is_active = true",
    "price_per_unit": "price / unit_multiplier"
}
```

## Integración con Redshift

### Comando COPY Típico

```sql
COPY schema.table
FROM 's3://cencosud.test.super.peru.analytics/ExternalAccess/janis_smk_pe/automatico/{tabla}/'
IAM_ROLE 'arn:aws:iam::account:role/RedshiftRole'
FORMAT AS PARQUET
MANIFEST
COMPUPDATE OFF;
```

### Esquemas de Destino

**Bronze Layer (Réplica 1:1)**:
- `janis_aurorape_replica`
- `janis_metroio_replica`
- `janis_wongio_replica`

**Silver Layer (Staging y Limpieza)**:
- `dl_sp_table_stg`
- `dl_sp_proc_stg`

**Gold Layer (Business-Ready)**:
- `dl_sp_dashboards_ecommerce`
- `dl_sp_dashboards_ventas`

## Checklist de Implementación

### Módulos a Actualizar

- [ ] **Data Type Converter**: Asegurar conversiones exactas según tabla de mapeo
- [ ] **Parquet Generator**: Implementar naming convention `part-{seq:05d}-{uuid}.c000.snappy.parquet`
- [ ] **Partitioning Module**: Generar estructura `year=YYYY/month=MM/day=DD/`
- [ ] **File Size Optimizer**: Mantener archivos entre 64-128 MB
- [ ] **Metadata Injector**: Agregar campos `_metadata` a cada registro

### Validaciones Requeridas

- [ ] Formato de archivos Parquet con compresión Snappy
- [ ] Naming convention correcta
- [ ] Tamaño de archivos en rango 64-128 MB
- [ ] Estructura de particiones Hive-style
- [ ] Compatibilidad de esquemas con Redshift
- [ ] Prueba de COPY command desde S3 Gold a Redshift

## Ventajas de Esta Estructura

1. **Compatibilidad Total**: Mantiene compatibilidad con sistema Redshift existente
2. **Patrón Consistente**: Alineado con `milocal_smk_pe`, `prime_smk_pe`, etc.
3. **Optimización Redshift**: Tamaño de archivos optimizado para COPY commands
4. **Escalabilidad**: Particionamiento por fecha facilita queries incrementales
5. **Separación Clara**: Datos de Janis aislados en carpeta dedicada

## Próximos Pasos

1. **Actualizar Specs**: Modificar specs de `data-transformation`, `webhook-ingestion`, `api-polling`, `redshift-loading`
2. **Implementar Módulos**: Crear módulos de generación de Parquet con formato exacto
3. **Testing**: Validar formato de archivos y compatibilidad con Redshift
4. **Documentación**: Crear guías de operación y troubleshooting

## Referencias

- **Análisis Completo**: `.kiro/specs/02-initial-data-load/docs/Análisis Estructura S3 Gold Producción.md`
- **Análisis Redshift**: `.kiro/specs/02-initial-data-load/docs/Análisis de Esquema Redshift - Resumen Ejecutivo.md`
- **Mapeo Detallado**: `.kiro/specs/02-initial-data-load/docs/Análisis Esquema Redshift - Mapeo Detallado.md`
- **Design Spec**: `.kiro/specs/02-initial-data-load/design.md`

---

**Documento generado**: 17 de Febrero de 2026  
**Estado**: ✅ Listo para Implementación  
**Próxima Revisión**: Después de implementar módulos de transformación
