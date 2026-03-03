# Análisis de Estructura S3 Gold - Producción Cencosud

**Fecha de Análisis**: 17 de Febrero de 2026  
**Ambiente**: Testing (cencosud.test.super.peru.*)  
**Propósito**: Entender la estructura actual de S3 Gold para replicarla con datos de API Janis

---

## Resumen Ejecutivo

Este documento analiza la estructura actual del bucket S3 Gold de producción de Cencosud para entender cómo deben estructurarse los datos provenientes de la API de Janis. El objetivo es mantener compatibilidad total con el sistema actual de Redshift que ya consume datos desde esta capa.

## Estructura de Buckets S3

### Buckets Identificados

```
Bronze:  cencosud.test.super.peru.raw
Silver:  cencosud.test.super.peru.raw-structured  
Gold:    cencosud.test.super.peru.analytics
```

### Flujo Actual de Datos

```
MySQL (Janis) → S3 Bronze → S3 Silver → S3 Gold → Redshift
```

### Flujo Objetivo (Nuevo)

```
API Janis → S3 Bronze → S3 Silver → S3 Gold → Redshift
                                        ↑
                                  (Mismo formato)
```

---

## Estructura de S3 Gold (Analytics)

### Carpetas Principales

```
s3://cencosud.test.super.peru.analytics/
├── DataDiscovery/
├── ExternalAccess/          ← CARPETA PRINCIPAL PARA REDSHIFT
│   ├── milocal_smk_pe/
│   ├── prime_smk_pe/
│   ├── tablesredshift/      ← Tablas específicas de Redshift
│   ├── rp9_smk_pe/
│   ├── flex_smk_pe/
│   └── [otros sistemas]
├── InternalProcessing/
└── datalake/
    └── inventarios/
```

### Patrón de Organización

**Estructura por Sistema:**
```
ExternalAccess/{sistema}_smk_pe/automatico/{tabla}/year=YYYY/month=MM/day=DD/
```

**Ejemplo Real:**
```
ExternalAccess/milocal_smk_pe/automatico/vw_milocal_centro/
  └── year=2024/
      └── month=07/
          └── day=10/
              └── part-00000-{uuid}.c000.snappy.parquet
```

---

## Características de Archivos en Gold

### Formato de Archivos

- **Formato**: Apache Parquet
- **Compresión**: Snappy
- **Naming**: `part-{number}-{uuid}.c000.snappy.parquet`
- **Tamaño Típico**: 8-12 MB (optimizado para Redshift COPY)

### Particionamiento

**Esquema de Particiones:**
```
year=YYYY/month=MM/day=DD/
```

**Características:**
- Particionamiento por fecha (año, mes, día)
- Formato Hive-style partitioning
- Facilita queries incrementales en Redshift
- Optimiza costos de escaneo en Athena/Spectrum

### Ejemplo de Archivo

```
Ubicación:
s3://cencosud.test.super.peru.analytics/ExternalAccess/milocal_smk_pe/automatico/vw_milocal_centro/year=2024/month=07/day=10/part-00000-5a8af952-c799-46c8-855e-0f969f6c7694.c000.snappy.parquet

Tamaño: 8.8 KB
Formato: Parquet con compresión Snappy
Particiones: year=2024, month=07, day=10
```

---

## Tablas Identificadas en Gold

### Tablas de MiLocal (E-commerce)

```
ExternalAccess/milocal_smk_pe/automatico/
├── vw_milocal_centro/                    (Centros/Tiendas)
├── vw_milocal_material/                  (Productos/Materiales)
├── vw_milocal_fact_stock_mat/            (Stock por Material)
├── vw_milocal_fact_venta_cliente_mat/    (Ventas por Cliente)
├── vw_milocal_fact_venta_mat/            (Ventas por Material)
└── vw_milocal_productos_quiebre/         (Productos sin Stock)
```

### Tablas en tablesredshift/

```
ExternalAccess/tablesredshift/
├── dim_cliente_adicional/
└── tbl_scraping_fblead/
```

---

## Integración con Redshift

### Esquema de Redshift Identificado

Basado en el análisis previo de Redshift:

**Esquemas Principales:**
- `dw_cencofcic` - Data Warehouse principal
- `dl_cs_bi` - Data Lake Cencosud BI (vacío, candidato para Janis)
- `dl_sp_maestras` - Maestras y dimensiones

**Tablas Relacionadas con Online/Janis:**
- `dim_estado_orden_online`
- `dim_estado_picking_online`
- `dim_estado_material_online`
- `dim_estado_sustituido_online`
- `dim_tipo_delivery_online`
- `dim_transportadora_online`
- `dim_transporte_online`

### Carga desde S3 a Redshift

**Comando COPY Típico:**
```sql
COPY schema.table
FROM 's3://cencosud.test.super.peru.analytics/ExternalAccess/{sistema}/{tabla}/'
IAM_ROLE 'arn:aws:iam::account:role/RedshiftRole'
FORMAT AS PARQUET
MANIFEST
COMPUPDATE OFF;
```

---

## Propuesta de Estructura para Datos de Janis

### Opción 1: Carpeta Dedicada para Janis (Recomendada)

```
s3://cencosud.test.super.peru.analytics/ExternalAccess/janis_smk_pe/automatico/
├── orders/
│   └── year=YYYY/month=MM/day=DD/
│       └── part-{n}-{uuid}.c000.snappy.parquet
├── order_items/
│   └── year=YYYY/month=MM/day=DD/
│       └── part-{n}-{uuid}.c000.snappy.parquet
├── products/
│   └── year=YYYY/month=MM/day=DD/
│       └── part-{n}-{uuid}.c000.snappy.parquet
├── skus/
│   └── year=YYYY/month=MM/day=DD/
│       └── part-{n}-{uuid}.c000.snappy.parquet
├── stores/
│   └── year=YYYY/month=MM/day=DD/
│       └── part-{n}-{uuid}.c000.snappy.parquet
└── stock/
    └── year=YYYY/month=MM/day=DD/
        └── part-{n}-{uuid}.c000.snappy.parquet
```

**Ventajas:**
- Separación clara de datos de Janis
- Fácil de gestionar y monitorear
- Consistente con patrón existente (milocal_smk_pe, prime_smk_pe)
- No interfiere con datos existentes

### Opción 2: Integración en tablesredshift/

```
s3://cencosud.test.super.peru.analytics/ExternalAccess/tablesredshift/
├── janis_orders/
├── janis_order_items/
├── janis_products/
└── [otras tablas]
```

**Ventajas:**
- Integración directa con tablas de Redshift
- Más simple para queries

**Desventajas:**
- Mezcla datos de diferentes fuentes
- Menos flexible para evolución

---

## Especificaciones Técnicas para Implementación

### Requisitos de Formato

1. **Formato de Archivo**
   - Tipo: Apache Parquet
   - Compresión: Snappy
   - Encoding: UTF-8

2. **Tamaño de Archivos**
   - Objetivo: 64-128 MB por archivo
   - Razón: Optimización para Redshift COPY
   - Estrategia: Combinar registros en batches

3. **Particionamiento**
   - Esquema: `year=YYYY/month=MM/day=DD/`
   - Basado en: `date_created` o `date_modified` del registro
   - Formato de fecha: ISO 8601

4. **Naming Convention**
   ```
   part-{sequence:05d}-{uuid}.c000.snappy.parquet
   
   Ejemplo:
   part-00000-a1b2c3d4-e5f6-7890-abcd-ef1234567890.c000.snappy.parquet
   ```

### Esquema de Datos

**Conversiones Requeridas (API Janis → Parquet):**

| Tipo API Janis | Tipo Parquet | Notas |
|----------------|--------------|-------|
| `string` | `STRING` | Directo |
| `integer` | `INT64` | Para IDs grandes |
| `number` | `DOUBLE` | Para decimales |
| `boolean` | `BOOLEAN` | Directo |
| `timestamp` (Unix) | `TIMESTAMP` | Convertir a ISO 8601 UTC |
| `object` (JSON) | `STRING` | Serializar como JSON string |
| `array` | `STRING` | Serializar como JSON string |

### Metadata en Archivos

**Campos Adicionales a Incluir:**
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

---

## Mapeo de Entidades Janis → S3 Gold

### Entidades Principales

| Entidad API Janis | Carpeta S3 Gold | Partición | Frecuencia Actualización |
|-------------------|-----------------|-----------|--------------------------|
| Orders | `janis_smk_pe/automatico/orders/` | `date_created` | Tiempo real (webhooks) + cada 5 min (polling) |
| Order Items | `janis_smk_pe/automatico/order_items/` | `date_created` (de order) | Tiempo real + cada 5 min |
| Products | `janis_smk_pe/automatico/products/` | `date_modified` | Cada 1 hora |
| SKUs | `janis_smk_pe/automatico/skus/` | `date_modified` | Cada 1 hora |
| Stores | `janis_smk_pe/automatico/stores/` | `date_modified` | Cada 24 horas |
| Stock | `janis_smk_pe/automatico/stock/` | `date` | Cada 10 minutos |
| Prices | `janis_smk_pe/automatico/prices/` | `date_modified` | Cada 30 minutos |

---

## Consideraciones para Transformación Bronze → Silver → Gold

### Capa Bronze (Raw)

**Ubicación**: `s3://cencosud.test.super.peru.raw/janis/`

**Características:**
- Datos raw sin transformar
- Formato: JSON (como llega de API/webhooks)
- Particionamiento: `year=YYYY/month=MM/day=DD/hour=HH/`
- Retención: 90 días

### Capa Silver (Structured)

**Ubicación**: `s3://cencosud.test.super.peru.raw-structured/janis/`

**Características:**
- Datos limpios y normalizados
- Formato: Parquet sin comprimir o con Snappy
- Deduplicación aplicada
- Tipos de datos convertidos
- Particionamiento: `year=YYYY/month=MM/day=DD/`
- Retención: 365 días

### Capa Gold (Analytics)

**Ubicación**: `s3://cencosud.test.super.peru.analytics/ExternalAccess/janis_smk_pe/`

**Características:**
- Datos curados y optimizados para BI
- Formato: Parquet con compresión Snappy
- Agregaciones pre-calculadas
- Campos calculados incluidos
- Optimizado para Redshift COPY
- Particionamiento: `year=YYYY/month=MM/day=DD/`
- Retención: Indefinida (datos históricos)

---

## Transformaciones Específicas para Gold

### 1. Conversión de Tipos de Datos

```python
# Ejemplo de transformaciones
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

### 2. Campos Calculados

**Campos a Agregar en Gold:**
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

### 3. Normalización de Datos

- Trim whitespace de strings
- Normalizar emails a lowercase
- Estandarizar formatos de teléfono
- Convertir todos los timestamps a UTC
- Validar y limpiar códigos postales

---

## Plan de Implementación

### Fase 1: Análisis y Diseño (Semana 1)

1. ✅ Analizar estructura actual de S3 Gold
2. ⏳ Definir esquema de tablas Parquet para Janis
3. ⏳ Crear matriz de mapeo API Janis → S3 Gold
4. ⏳ Documentar transformaciones requeridas

### Fase 2: Desarrollo (Semanas 2-3)

5. ⏳ Implementar jobs de Glue para Bronze → Silver
6. ⏳ Implementar jobs de Glue para Silver → Gold
7. ⏳ Crear scripts de generación de archivos Parquet
8. ⏳ Implementar particionamiento automático

### Fase 3: Testing (Semana 4)

9. ⏳ Validar formato de archivos Parquet
10. ⏳ Probar carga en Redshift desde S3 Gold
11. ⏳ Validar compatibilidad de esquemas
12. ⏳ Performance testing de queries

### Fase 4: Migración (Semana 5-6)

13. ⏳ Carga inicial de datos históricos
14. ⏳ Activar pipeline en tiempo real
15. ⏳ Monitoreo y ajustes
16. ⏳ Cutover a producción

---

## Próximos Pasos Inmediatos

### 1. Actualizar Specs

**Specs a Modificar:**
- ✅ `02-initial-data-load` - Agregar requisitos de formato S3 Gold
- ⏳ `data-transformation` - Actualizar transformaciones Bronze→Silver→Gold
- ⏳ `webhook-ingestion` - Asegurar compatibilidad con estructura Gold
- ⏳ `api-polling` - Asegurar compatibilidad con estructura Gold
- ⏳ `redshift-loading` - Actualizar para cargar desde nueva estructura Gold

### 2. Crear Documentación Técnica

- ⏳ Esquema detallado de tablas Parquet
- ⏳ Guía de transformaciones de datos
- ⏳ Procedimientos de validación
- ⏳ Runbook de operaciones

### 3. Implementar Módulos de Transformación

- ⏳ Módulo de conversión de tipos de datos
- ⏳ Módulo de generación de Parquet
- ⏳ Módulo de particionamiento
- ⏳ Módulo de validación de esquemas

---

## Conclusiones

1. **Estructura Clara**: S3 Gold tiene una estructura bien definida y consistente
2. **Patrón Replicable**: El patrón `{sistema}_smk_pe/automatico/{tabla}/` es fácil de replicar
3. **Formato Estándar**: Parquet con Snappy es el estándar para Redshift
4. **Particionamiento Consistente**: year/month/day es el esquema universal
5. **Compatibilidad**: Mantener este formato asegura compatibilidad con Redshift existente

---

**Documento generado**: 17 de Febrero de 2026  
**Próxima Revisión**: Después de definir esquemas Parquet detallados  
**Estado**: ✅ Análisis Completo - Listo para Actualización de Specs
