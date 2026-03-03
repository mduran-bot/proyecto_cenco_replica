"""
Test del Pipeline Silver-to-Gold con datos locales (sin LocalStack)
"""
import sys
import os
import logging
from datetime import datetime
from pyspark.sql import SparkSession
from pyspark.sql.functions import current_timestamp, lit, col
from pyspark.sql.types import StructType, StructField, StringType, DoubleType, TimestampType, BooleanType

# Agregar path de módulos
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def init_spark():
    """Inicializar Spark para ejecución local"""
    spark = SparkSession.builder \
        .appName("silver-to-gold-local-test") \
        .master("local[*]") \
        .config("spark.sql.shuffle.partitions", "2") \
        .getOrCreate()
    
    spark.sparkContext.setLogLevel("WARN")
    return spark

def create_sample_silver_data(spark):
    """Crear datos de prueba en formato Silver"""
    schema = StructType([
        StructField("id", StringType(), True),
        StructField("cliente_nombre", StringType(), True),
        StructField("producto_nombre", StringType(), True),
        StructField("monto", DoubleType(), True),
        StructField("fecha_venta", TimestampType(), True),
        StructField("estado", StringType(), True),
        StructField("metadata_sucursal", StringType(), True),
        StructField("es_valido", BooleanType(), True),
        StructField("has_critical_gaps", BooleanType(), True)
    ])
    
    data = [
        ("1001", "Juan Pérez", "Laptop HP", 2500.80, datetime(2026, 2, 15, 10, 30), "completado", "Sucursal Centro", True, False),
        ("1002", "María González", "Teclado Mecánico", 850.50, datetime(2026, 2, 16, 14, 20), "completado", "Sucursal Norte", True, False),
        ("1003", "Pedro López", "Mouse Inalámbrico", 350.00, datetime(2026, 2, 17, 9, 15), "pendiente", "Sucursal Centro", True, False),
        ("1004", "Ana Martínez", "Monitor 27\"", 3200.00, datetime(2026, 2, 18, 11, 45), "completado", "Sucursal Sur", True, False),
        ("1005", "Carlos Ruiz", "Webcam HD", 450.00, datetime(2026, 2, 18, 16, 30), "cancelado", "Sucursal Norte", False, False),
        ("1006", "Laura Sánchez", "Auriculares", 280.00, datetime(2026, 2, 19, 8, 0), "completado", "Sucursal Centro", True, True),
        ("1007", "Roberto Silva", "Impresora Láser", 5600.00, datetime(2026, 2, 19, 10, 15), "completado", "Sucursal Sur", True, False),
        ("1008", "Diana Torres", "Tablet", 1200.00, datetime(2026, 2, 19, 12, 30), "pendiente", "Sucursal Norte", False, True),
        ("1009", "Diego Torres", "Notebook Gaming", 12500.99, datetime(2026, 2, 19, 14, 0), "completado", "Sucursal Centro", True, False),
        ("1010", "Sofia Ramírez", "SSD 1TB", 890.00, datetime(2026, 2, 19, 15, 45), "rechazado", "Sucursal Sur", False, False),
    ]
    
    return spark.createDataFrame(data, schema)

def main():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
    logger = logging.getLogger('SilverToGoldTest')
    
    logger.info("=" * 60)
    logger.info("TEST PIPELINE SILVER → GOLD (LOCAL)")
    logger.info("=" * 60)
    
    # Inicializar Spark
    spark = init_spark()
    
    # Crear datos de prueba Silver
    logger.info("\n1. Creando datos de prueba en formato Silver...")
    df_silver = create_sample_silver_data(spark)
    logger.info(f"   Registros creados: {df_silver.count()}")
    
    logger.info("\n   Muestra de datos Silver:")
    df_silver.show(5, truncate=False)
    
    # Guardar Silver localmente
    silver_path = "glue/data/test_silver"
    logger.info(f"\n2. Guardando datos Silver en: {silver_path}")
    df_silver.coalesce(1).write.mode("overwrite").json(silver_path)
    
    # Importar módulos Silver-to-Gold
    logger.info("\n3. Importando módulos Silver-to-Gold...")
    from modules.silver_to_gold.incremental_processor import IncrementalProcessor
    from modules.silver_to_gold.silver_to_gold_aggregator import SilverToGoldAggregator
    from modules.silver_to_gold.denormalization_engine import DenormalizationEngine
    from modules.silver_to_gold.data_quality_validator import DataQualityValidator
    from modules.silver_to_gold.error_handler import ErrorHandler
    from modules.silver_to_gold.data_lineage_tracker import DataLineageTracker
    
    # Configuración simplificada
    config = {
        "incremental": {
            "enabled": False  # Deshabilitado para test inicial
        },
        "aggregations": {
            "date_column": "fecha_venta",
            "dimensions": ["metadata_sucursal", "estado"],
            "metrics": [
                {"column": "monto", "functions": ["sum", "avg", "min", "max"]},
                {"column": "*", "functions": ["count"]}
            ]
        },
        "denormalization": {
            "enabled": False  # No hay tablas de dimensiones en test local
        },
        "quality": {
            "critical_columns": ["estado", "metadata_sucursal"],
            "valid_values": {
                "estado": ["completado", "pendiente", "cancelado", "rechazado"]
            },
            "numeric_ranges": {
                "monto": {"min": 0, "max": 99999999}
            },
            "consistency_rules": [
                {
                    "when_column": "estado",
                    "when_value": "completado",
                    "then_column": "monto",
                    "then_not_null": True
                }
            ],
            "quality_gate": False,
            "threshold": 0.8
        },
        "error_handler": {
            "dlq_enabled": False,  # Deshabilitado para test local
            "recovery_mode": "flag"
        },
        "lineage": {
            "enabled": False  # Deshabilitado para test local
        }
    }
    
    # Leer datos Silver
    logger.info("\n4. Leyendo datos Silver...")
    df = spark.read.json(silver_path)
    logger.info(f"   Registros leídos: {df.count()}")
    
    # Ejecutar módulos principales
    logger.info("\n5. Ejecutando módulos de transformación...")
    
    # IncrementalProcessor (skip si disabled)
    logger.info("\n   5.1 IncrementalProcessor (skipped - disabled)")
    
    # SilverToGoldAggregator
    logger.info("\n   5.2 SilverToGoldAggregator...")
    aggregator = SilverToGoldAggregator()
    df = aggregator.transform(df, config)
    logger.info(f"       → {df.count()} registros agregados")
    
    # DenormalizationEngine (skip si disabled)
    logger.info("\n   5.3 DenormalizationEngine (skipped - disabled)")
    
    # DataQualityValidator
    logger.info("\n   5.4 DataQualityValidator...")
    validator = DataQualityValidator()
    df = validator.transform(df, config)
    logger.info(f"       → {df.count()} registros validados")
    
    # ErrorHandler
    logger.info("\n   5.5 ErrorHandler...")
    error_handler = ErrorHandler()
    df = error_handler.transform(df, config)
    logger.info(f"       → {df.count()} registros después de error handling")
    
    # Agregar timestamp de procesamiento
    df = df.withColumn("_processing_timestamp", current_timestamp())
    
    # Guardar Gold localmente
    gold_path = "glue/data/test_gold"
    logger.info(f"\n6. Guardando datos Gold en: {gold_path}")
    df.coalesce(1).write.mode("overwrite").json(gold_path)
    
    # Verificar resultados
    logger.info("\n7. Verificando resultados en Gold...")
    df_gold = spark.read.json(gold_path)
    logger.info(f"   Total registros en Gold: {df_gold.count()}")
    
    logger.info("\n   Columnas en Gold:")
    for col_name in sorted(df_gold.columns):
        logger.info(f"   - {col_name}")
    
    logger.info("\n   Muestra de datos Gold (agregados):")
    df_gold.select(
        "metadata_sucursal", "estado", 
        "total_monto", "promedio_monto", "min_monto", "max_monto", "num_registros",
        "_quality_valid"
    ).show(truncate=False)
    
    # Análisis de calidad
    logger.info("\n8. Análisis de Calidad de Datos:")
    valid_count = df_gold.filter(col("_quality_valid") == True).count()
    invalid_count = df_gold.filter(col("_quality_valid") == False).count()
    total = df_gold.count()
    
    logger.info(f"   Registros válidos: {valid_count}/{total} ({valid_count/total*100:.1f}%)")
    logger.info(f"   Registros inválidos: {invalid_count}/{total} ({invalid_count/total*100:.1f}%)")
    
    if invalid_count > 0:
        logger.info("\n   Registros con problemas de calidad:")
        df_gold.filter(col("_quality_valid") == False).select(
            "metadata_sucursal", "estado", "_quality_issues"
        ).show(truncate=False)
    
    logger.info("\n" + "=" * 60)
    logger.info("✅ TEST COMPLETADO EXITOSAMENTE")
    logger.info("=" * 60)
    
    spark.stop()
    return 0

if __name__ == "__main__":
    sys.exit(main())
