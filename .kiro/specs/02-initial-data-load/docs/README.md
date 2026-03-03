# Documentación - Initial Data Load

Esta carpeta contiene la documentación específica relacionada con el spec de carga inicial de datos (02-initial-data-load).

## Contenido

### Análisis y Planificación

- **Initial Data Load - Plan de Implementación.md**: Plan detallado para la carga inicial de datos desde MySQL
- **Plan de Adaptación a Estructura Gold Existente.md**: Estrategia de adaptación a la estructura S3 Gold existente

### Análisis de Infraestructura Existente

- **Análisis de Esquema Redshift - Resumen Ejecutivo.md**: Resumen del análisis del esquema de Redshift (db_conf database)
- **Análisis Esquema Redshift - Mapeo Detallado.md**: Mapeo detallado entre esquemas MySQL y Redshift (datalabs database)
- **Análisis Estructura S3 Gold Producción.md**: Análisis de la estructura actual de S3 Gold y requisitos de formato para compatibilidad

### Mapeo de Datos ⭐ NUEVO

- **Matriz Mapeo API Janis a S3 Gold.md**: Matriz completa de mapeo entre API Janis y estructura Parquet en S3 Gold, incluyendo:
  - Convenciones de nomenclatura y tipos de datos
  - Esquemas detallados de 6 entidades (Orders, Order Items, Products, Stores, Stock, Prices)
  - Transformaciones específicas por tipo de dato
  - Metadata de ingesta y validaciones de calidad
  - Configuración de archivos Parquet y comandos COPY de Redshift

### Herramientas de Validación

- **Herramienta Análisis Parquet - Guía de Uso.md**: Documentación completa del script `analyze_parquet_schemas.py` para:
  - Analizar esquemas de archivos Parquet locales
  - Validar tipos de datos y estructura
  - Identificar problemas de calidad de datos
  - Verificar compatibilidad con Redshift
  - Comparar esquemas entre ambientes

## Hallazgos Clave

### Estructura S3 Gold (17 Feb 2026)

El análisis de la estructura S3 Gold de producción reveló:

1. **Patrón de Organización**: `ExternalAccess/{sistema}_smk_pe/automatico/{tabla}/year=YYYY/month=MM/day=DD/`
2. **Formato de Archivos**: Apache Parquet con compresión Snappy
3. **Naming Convention**: `part-{sequence:05d}-{uuid}.c000.snappy.parquet`
4. **Tamaño Óptimo**: 64-128 MB por archivo (optimizado para Redshift COPY)
5. **Particionamiento**: Hive-style por fecha (year/month/day)

### Esquemas Redshift Identificados

**Base de Datos: datalabs**
- `janis_aurorape_replica`, `janis_metroio_replica`, `janis_wongio_replica` - Esquemas vacíos preparados para datos de Janis
- `dl_sp_table_stg` - Tablas de staging con dimensiones
- `dl_sp_dashboards_ecommerce` - Dashboards transaccionales

**Base de Datos: db_conf**
- `dw_cencofcic` - Data Warehouse principal con 5 tablas
- `dl_cs_bi` - Data Lake Cencosud BI (vacío, candidato para Janis)

### Implicaciones para Implementación

1. **Compatibilidad Total**: Mantener formato Parquet + Snappy para compatibilidad con sistema existente
2. **Estructura Consistente**: Usar patrón `janis_smk_pe/automatico/` para alinearse con `milocal_smk_pe`, `prime_smk_pe`
3. **Optimización Redshift**: Archivos de 64-128 MB optimizan performance de COPY commands
4. **Capas Bronze/Silver/Gold**: Estructura de 3 capas ya establecida en buckets existentes

## Archivos del Spec

- `../requirements.md`: Requerimientos funcionales
- `../design.md`: Diseño técnico (actualizado con estructura S3 Gold)
- `../tasks.md`: Lista de tareas de implementación

## Próximos Pasos

1. Actualizar módulos de transformación para generar archivos con formato exacto de producción
2. Implementar generación de archivos Parquet con naming convention correcta
3. Validar compatibilidad de esquemas con Redshift existente
4. Crear jobs de Glue para transformaciones Bronze → Silver → Gold
