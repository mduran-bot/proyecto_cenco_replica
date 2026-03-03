# Iceberg Manager - Guía de Uso

**Módulo**: `glue/modules/iceberg_manager.py`  
**Fecha de Implementación**: 18 de Febrero de 2026  
**Versión**: 1.0.0  
**Estado**: ✅ Implementado

---

## Resumen Ejecutivo

El módulo `IcebergTableManager` proporciona una interfaz completa para gestionar tablas Apache Iceberg en AWS Glue, incluyendo creación de tablas, particionamiento, transacciones ACID, gestión de snapshots y compactación de archivos.

### Características Principales

- ✅ Creación de tablas Iceberg con esquemas PySpark
- ✅ Particionamiento configurable (hidden partitioning)
- ✅ Formato Parquet con compresión Snappy
- ✅ Transacciones ACID automáticas
- ✅ Gestión de snapshots para time travel
- ✅ Compactación de archivos pequeños
- ✅ Integración con AWS Glue Data Catalog
- ✅ Rollback a snapshots anteriores
- ✅ Validación de existencia de tablas

---

## Arquitectura

### Integración con AWS Glue

```
┌─────────────────────────────────────────────────────────────┐
│                    AWS Glue Job (PySpark)                   │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐ │
│  │         IcebergTableManager                           │ │
│  │                                                       │ │
│  │  • create_table()      • list_snapshots()           │ │
│  │  • compact_files()     • rollback_to_snapshot()     │ │
│  │  • table_exists()      • get_table_metadata()       │ │
│  └───────────────────────────────────────────────────────┘ │
│                           │                                 │
│                           ▼                                 │
│  ┌───────────────────────────────────────────────────────┐ │
│  │         Apache Iceberg (Spark Integration)            │ │
│  │                                                       │ │
│  │  • ACID Transactions   • Hidden Partitioning         │ │
│  │  • Snapshot Management • Schema Evolution            │ │
│  │  • Time Travel         • File Compaction             │ │
│  └───────────────────────────────────────────────────────┘ │
│                           │                                 │
└───────────────────────────┼─────────────────────────────────┘
                            │
                            ▼
        ┌───────────────────────────────────────┐
        │     AWS Glue Data Catalog             │
        │                                       │
        │  • Table Metadata                    │
        │  • Schema Versions                   │
        │  • Partition Information             │
        └───────────────────────────────────────┘
                            │
                            ▼
        ┌───────────────────────────────────────┐
        │     Amazon S3 (Data Lake)             │
        │                                       │
        │  s3://bucket/warehouse/               │
        │    └── database/                      │
        │        └── table/                     │
        │            ├── data/                  │
        │            │   └── *.parquet          │
        │            └── metadata/              │
        │                ├── snapshots/         │
        │                └── manifests/         │
        └───────────────────────────────────────┘
```

### Flujo de Datos

```
1. Crear Tabla
   ├── Definir esquema PySpark (StructType)
   ├── Especificar particionamiento
   ├── Configurar propiedades (compresión, file size)
   └── Registrar en Glue Data Catalog

2. Escribir Datos (via IcebergWriter)
   ├── Validar esquema
   ├── Aplicar particionamiento hidden
   ├── Escribir archivos Parquet con Snappy
   ├── Crear snapshot
   └── Commit transacción ACID

3. Gestión de Snapshots
   ├── Listar snapshots históricos
   ├── Consultar datos en snapshot específico (time travel)
   └── Rollback a snapshot anterior si es necesario

4. Optimización
   ├── Compactar archivos pequeños
   ├── Expirar snapshots antiguos
   └── Mantener performance óptimo
```

---

## Instalación y Requisitos

### Dependencias

```python
# requirements.txt para Glue Job
pyspark>=3.3.0
pyiceberg>=0.5.0
```

### Configuración de Glue Job

```python
# En AWS Glue Job configuration
{
  "GlueVersion": "4.0",
  "Command": {
    "Name": "glueetl",
    "ScriptLocation": "s3://bucket/scripts/job.py",
    "PythonVersion": "3"
  },
  "DefaultArguments": {
    "--enable-glue-datacatalog": "true",
    "--enable-spark-ui": "true",
    "--spark-event-logs-path": "s3://bucket/spark-logs/",
    "--enable-metrics": "true",
    "--enable-continuous-cloudwatch-log": "true",
    "--extra-jars": "s3://bucket/jars/iceberg-spark-runtime.jar",
    "--datalake-formats": "iceberg"
  }
}
```

---

## Uso Básico

### 1. Inicialización

```python
from pyspark.sql import SparkSession
from glue.modules.iceberg_manager import IcebergTableManager

# Crear Spark session
spark = SparkSession.builder \
    .appName("IcebergExample") \
    .config("spark.sql.extensions", "org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions") \
    .config("spark.sql.catalog.glue_catalog", "org.apache.iceberg.spark.SparkCatalog") \
    .config("spark.sql.catalog.glue_catalog.catalog-impl", "org.apache.iceberg.aws.glue.GlueCatalog") \
    .getOrCreate()

# Inicializar manager
iceberg_manager = IcebergTableManager(
    spark=spark,
    catalog_name="glue_catalog"
)
```

### 2. Crear Tabla

```python
from pyspark.sql.types import StructType, StructField, StringType, TimestampType, DecimalType, IntegerType

# Definir esquema
orders_schema = StructType([
    StructField("order_id", StringType(), nullable=False),
    StructField("order_number", StringType(), nullable=False),
    StructField("status", StringType(), nullable=False),
    StructField("date_created", TimestampType(), nullable=False),
    StructField("date_modified", TimestampType(), nullable=False),
    StructField("store_id", StringType(), nullable=False),
    StructField("customer_id", StringType(), nullable=True),
    StructField("total", DecimalType(18, 2), nullable=False),
    StructField("items_count", IntegerType(), nullable=False)
])

# Crear tabla con particionamiento por fecha
iceberg_manager.create_table(
    table_name="silver.orders",
    schema=orders_schema,
    partition_spec={
        "partition_by": [
            "year(date_created)",
            "month(date_created)",
            "day(date_created)"
        ]
    },
    location="s3://cencosud-datalake-silver-prod/orders/",
    properties={
        "write.target-file-size-bytes": str(128 * 1024 * 1024),  # 128 MB
        "write.parquet.compression-codec": "snappy",
        "commit.retry.num-retries": "5"
    }
)
```

### 3. Verificar Existencia de Tabla

```python
# Verificar si tabla existe antes de operaciones
if iceberg_manager.table_exists("silver.orders"):
    print("✅ Tabla silver.orders existe")
else:
    print("❌ Tabla silver.orders no existe")
```

### 4. Obtener Metadata de Tabla

```python
# Obtener información de la tabla
metadata = iceberg_manager.get_table_metadata("silver.orders")

print(f"Columnas: {len(metadata)}")
for col_name, col_type in metadata.items():
    print(f"  - {col_name}: {col_type}")
```

---

## Gestión de Snapshots

### Listar Snapshots

```python
# Obtener todos los snapshots de una tabla
snapshots = iceberg_manager.list_snapshots("silver.orders")

print(f"Total snapshots: {len(snapshots)}")
for snapshot in snapshots:
    print(f"""
    Snapshot ID: {snapshot['snapshot_id']}
    Parent ID: {snapshot['parent_id']}
    Operation: {snapshot['operation']}
    Committed At: {snapshot['committed_at']}
    """)
```

### Time Travel - Consultar Snapshot Específico

```python
# Leer datos de un snapshot específico
snapshot_id = snapshots[0]['snapshot_id']

df_historical = spark.read \
    .format("iceberg") \
    .option("snapshot-id", snapshot_id) \
    .table("glue_catalog.silver.orders")

print(f"Registros en snapshot {snapshot_id}: {df_historical.count()}")
```

### Rollback a Snapshot Anterior

```python
# Rollback a un snapshot anterior (útil para recovery)
target_snapshot_id = "1234567890123456789"

iceberg_manager.rollback_to_snapshot(
    table_name="silver.orders",
    snapshot_id=target_snapshot_id
)

print(f"✅ Tabla rolled back a snapshot {target_snapshot_id}")
```

---

## Optimización de Performance

### Compactación de Archivos

```python
# Compactar archivos pequeños para mejorar performance de lectura
iceberg_manager.compact_files("silver.orders")

print("✅ Archivos compactados exitosamente")

# La compactación:
# - Combina archivos pequeños (<64 MB) en archivos más grandes (128 MB)
# - Mejora performance de queries
# - Reduce overhead de metadata
# - No afecta datos, solo reorganiza archivos
```

### Configuración de Compactación Personalizada

```python
# Compactación con parámetros personalizados
spark.sql(f"""
    CALL glue_catalog.system.rewrite_data_files(
        table => 'silver.orders',
        options => map(
            'target-file-size-bytes', '268435456',  -- 256 MB
            'min-file-size-bytes', '134217728',     -- 128 MB
            'max-file-group-size-bytes', '1073741824'  -- 1 GB
        )
    )
""")
```

---

## Casos de Uso Avanzados

### 1. Crear Tabla con Propiedades Personalizadas

```python
# Tabla con configuración específica para datos de alta frecuencia
iceberg_manager.create_table(
    table_name="silver.order_items",
    schema=order_items_schema,
    partition_spec={
        "partition_by": ["year(date_created)", "month(date_created)"]
    },
    location="s3://cencosud-datalake-silver-prod/order_items/",
    properties={
        # File size más pequeño para escrituras frecuentes
        "write.target-file-size-bytes": str(64 * 1024 * 1024),  # 64 MB
        
        # Compresión más agresiva
        "write.parquet.compression-codec": "zstd",
        "write.parquet.compression-level": "3",
        
        # Retries más agresivos
        "commit.retry.num-retries": "10",
        "commit.retry.min-wait-ms": "50",
        
        # Expiración de snapshots más corta
        "history.expire.max-snapshot-age-ms": str(7 * 24 * 60 * 60 * 1000),  # 7 días
        
        # Metadata compression
        "write.metadata.compression-codec": "gzip"
    }
)
```

### 2. Particionamiento por Múltiples Dimensiones

```python
# Tabla particionada por fecha y tienda
iceberg_manager.create_table(
    table_name="silver.stock",
    schema=stock_schema,
    partition_spec={
        "partition_by": [
            "year(snapshot_date)",
            "month(snapshot_date)",
            "store_id"  # Partición adicional por tienda
        ]
    },
    location="s3://cencosud-datalake-silver-prod/stock/"
)
```

### 3. Validación y Recovery

```python
# Workflow completo de validación y recovery
def safe_table_operation(table_name, operation_func):
    """
    Ejecuta operación con snapshot de respaldo para recovery
    """
    # 1. Listar snapshots antes de operación
    snapshots_before = iceberg_manager.list_snapshots(table_name)
    latest_snapshot = snapshots_before[0]['snapshot_id'] if snapshots_before else None
    
    print(f"📸 Snapshot actual: {latest_snapshot}")
    
    try:
        # 2. Ejecutar operación
        operation_func()
        print("✅ Operación completada exitosamente")
        
    except Exception as e:
        print(f"❌ Error en operación: {e}")
        
        # 3. Rollback en caso de error
        if latest_snapshot:
            print(f"🔄 Ejecutando rollback a snapshot {latest_snapshot}")
            iceberg_manager.rollback_to_snapshot(table_name, latest_snapshot)
            print("✅ Rollback completado")
        
        raise

# Uso
def risky_operation():
    # Operación que puede fallar
    spark.sql("UPDATE glue_catalog.silver.orders SET status = 'cancelled' WHERE ...")

safe_table_operation("silver.orders", risky_operation)
```

---

## Integración con Pipeline de Transformación

### Bronze → Silver con Iceberg

```python
from glue.modules.iceberg_manager import IcebergTableManager
from glue.modules.iceberg_writer import IcebergWriter
from glue.modules.data_type_converter import DataTypeConverter
from glue.modules.data_normalizer import DataNormalizer

# 1. Inicializar managers
iceberg_manager = IcebergTableManager(spark, "glue_catalog")
iceberg_writer = IcebergWriter(spark, "glue_catalog")

# 2. Crear tabla Silver si no existe
if not iceberg_manager.table_exists("silver.orders"):
    iceberg_manager.create_table(
        table_name="silver.orders",
        schema=orders_schema,
        partition_spec={"partition_by": ["year(date_created)", "month(date_created)"]},
        location="s3://cencosud-datalake-silver-prod/orders/"
    )

# 3. Leer datos de Bronze
df_bronze = spark.read.parquet("s3://cencosud-datalake-bronze-prod/orders/")

# 4. Aplicar transformaciones
df_transformed = DataTypeConverter.apply_conversions_to_dataframe(df_bronze, conversion_rules)
df_normalized = DataNormalizer.apply_normalizations_to_dataframe(df_transformed, normalization_rules)

# 5. Escribir a Silver (Iceberg)
iceberg_writer.write_dataframe(
    df=df_normalized,
    table_name="silver.orders",
    mode="append"
)

# 6. Compactar si es necesario
iceberg_manager.compact_files("silver.orders")
```

---

## Monitoreo y Troubleshooting

### Verificar Estado de Tabla

```python
def check_table_health(table_name):
    """
    Verifica el estado de salud de una tabla Iceberg
    """
    print(f"🔍 Verificando tabla: {table_name}")
    
    # 1. Verificar existencia
    if not iceberg_manager.table_exists(table_name):
        print(f"❌ Tabla {table_name} no existe")
        return
    
    # 2. Obtener metadata
    metadata = iceberg_manager.get_table_metadata(table_name)
    print(f"✅ Columnas: {len(metadata)}")
    
    # 3. Listar snapshots
    snapshots = iceberg_manager.list_snapshots(table_name)
    print(f"✅ Snapshots: {len(snapshots)}")
    
    if snapshots:
        latest = snapshots[0]
        print(f"   Último snapshot: {latest['snapshot_id']}")
        print(f"   Operación: {latest['operation']}")
        print(f"   Fecha: {latest['committed_at']}")
    
    # 4. Contar registros
    df = spark.table(f"glue_catalog.{table_name}")
    count = df.count()
    print(f"✅ Registros: {count:,}")
    
    # 5. Verificar particiones
    partitions = spark.sql(f"SHOW PARTITIONS glue_catalog.{table_name}").collect()
    print(f"✅ Particiones: {len(partitions)}")

# Uso
check_table_health("silver.orders")
```

### Logs y Debugging

```python
import logging

# Configurar logging detallado
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# El IcebergTableManager ya incluye logging automático
# Todos los métodos logean operaciones y errores
```

---

## Mejores Prácticas

### 1. Naming Conventions

```python
# ✅ CORRECTO: Nombres descriptivos y consistentes
iceberg_manager.create_table(
    table_name="silver.orders",  # layer.entity
    schema=orders_schema,
    partition_spec={"partition_by": ["year(date_created)", "month(date_created)"]}
)

# ❌ INCORRECTO: Nombres ambiguos
iceberg_manager.create_table(
    table_name="tbl1",
    schema=schema,
    partition_spec={}
)
```

### 2. Particionamiento

```python
# ✅ CORRECTO: Particionamiento por fecha para queries temporales
partition_spec = {
    "partition_by": [
        "year(date_created)",
        "month(date_created)",
        "day(date_created)"  # Solo si hay muchos datos por mes
    ]
}

# ❌ INCORRECTO: Sobre-particionamiento
partition_spec = {
    "partition_by": [
        "year(date_created)",
        "month(date_created)",
        "day(date_created)",
        "hour(date_created)",  # Demasiado granular
        "minute(date_created)"  # Genera demasiadas particiones
    ]
}
```

### 3. Propiedades de Tabla

```python
# ✅ CORRECTO: Propiedades optimizadas para caso de uso
properties = {
    "write.target-file-size-bytes": str(128 * 1024 * 1024),  # 128 MB para balance
    "write.parquet.compression-codec": "snappy",  # Snappy para balance compresión/velocidad
    "commit.retry.num-retries": "3",  # Retries razonables
    "history.expire.max-snapshot-age-ms": str(30 * 24 * 60 * 60 * 1000)  # 30 días
}

# ❌ INCORRECTO: Valores extremos
properties = {
    "write.target-file-size-bytes": str(1 * 1024 * 1024),  # 1 MB - demasiado pequeño
    "commit.retry.num-retries": "100",  # Demasiados retries
    "history.expire.max-snapshot-age-ms": str(365 * 24 * 60 * 60 * 1000)  # 1 año - demasiado largo
}
```

### 4. Gestión de Snapshots

```python
# ✅ CORRECTO: Limpiar snapshots antiguos periódicamente
def cleanup_old_snapshots(table_name, days_to_keep=30):
    """
    Expira snapshots más antiguos que X días
    """
    spark.sql(f"""
        CALL glue_catalog.system.expire_snapshots(
            table => '{table_name}',
            older_than => TIMESTAMP '{datetime.now() - timedelta(days=days_to_keep)}'
        )
    """)

# Ejecutar semanalmente
cleanup_old_snapshots("silver.orders", days_to_keep=30)
```

### 5. Error Handling

```python
# ✅ CORRECTO: Manejo robusto de errores
try:
    iceberg_manager.create_table(
        table_name="silver.orders",
        schema=orders_schema,
        partition_spec=partition_spec
    )
except Exception as e:
    logger.error(f"Error creando tabla: {e}")
    # Implementar lógica de recovery o alertas
    raise

# ❌ INCORRECTO: Ignorar errores
try:
    iceberg_manager.create_table(...)
except:
    pass  # Nunca hacer esto
```

---

## Performance Tuning

### Optimización de File Size

```python
# Para datos de alta frecuencia (muchas escrituras pequeñas)
properties = {
    "write.target-file-size-bytes": str(64 * 1024 * 1024)  # 64 MB
}

# Para datos de baja frecuencia (pocas escrituras grandes)
properties = {
    "write.target-file-size-bytes": str(256 * 1024 * 1024)  # 256 MB
}
```

### Optimización de Compactación

```python
# Compactación agresiva para tablas con muchas escrituras
spark.sql(f"""
    CALL glue_catalog.system.rewrite_data_files(
        table => 'silver.orders',
        options => map(
            'target-file-size-bytes', '134217728',  -- 128 MB
            'min-file-size-bytes', '33554432',      -- 32 MB (más agresivo)
            'max-concurrent-file-group-rewrites', '10'
        )
    )
""")
```

---

## Troubleshooting

### Problema: Tabla no se crea

**Síntomas**: Error al crear tabla, tabla no aparece en Glue Catalog

**Soluciones**:
1. Verificar permisos IAM para Glue Data Catalog
2. Verificar permisos S3 para ubicación de tabla
3. Verificar que el esquema es válido
4. Verificar que el catalog_name es correcto

```python
# Debug: Verificar configuración
print(f"Catalog: {iceberg_manager.catalog_name}")
print(f"Spark configs: {spark.sparkContext.getConf().getAll()}")
```

### Problema: Snapshots no se listan

**Síntomas**: `list_snapshots()` retorna lista vacía

**Soluciones**:
1. Verificar que la tabla tiene datos escritos
2. Verificar que se usó formato Iceberg para escritura
3. Verificar permisos de lectura en S3

```python
# Debug: Verificar metadata de tabla
metadata = iceberg_manager.get_table_metadata("silver.orders")
print(f"Metadata: {metadata}")
```

### Problema: Compactación falla

**Síntomas**: Error al ejecutar `compact_files()`

**Soluciones**:
1. Verificar que hay archivos para compactar
2. Verificar permisos de escritura en S3
3. Aumentar memoria del Glue job
4. Reducir `target-file-size-bytes`

---

## Recursos Adicionales

### Documentación Oficial

- [Apache Iceberg Documentation](https://iceberg.apache.org/docs/latest/)
- [AWS Glue Iceberg Support](https://docs.aws.amazon.com/glue/latest/dg/aws-glue-programming-etl-format-iceberg.html)
- [PySpark Iceberg Integration](https://iceberg.apache.org/docs/latest/spark-getting-started/)

### Archivos Relacionados

- `glue/modules/iceberg_writer.py` - Escritura de datos a Iceberg
- `glue/schemas/silver_schemas.py` - Esquemas de capa Silver
- `.kiro/specs/data-transformation/design.md` - Diseño de transformaciones
- `.kiro/specs/data-transformation/tasks.md` - Plan de implementación

---

## Conclusión

El módulo `IcebergTableManager` proporciona una interfaz robusta y fácil de usar para gestionar tablas Apache Iceberg en AWS Glue. Con soporte completo para transacciones ACID, snapshots, particionamiento y optimización, es la base para construir un Data Lake moderno y confiable.

**Próximos pasos**:
1. Implementar `IcebergWriter` para escritura de datos (Task 5.2)
2. Implementar tests de propiedades para validar ACID (Task 5.4)
3. Implementar tests de time travel (Task 5.5)

---

**Documento Generado**: 18 de Febrero de 2026  
**Versión**: 1.0  
**Estado**: ✅ Completo - Módulo Implementado  
**Mantenedor**: Equipo de Data Engineering - Janis-Cencosud
