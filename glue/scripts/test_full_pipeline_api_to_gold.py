"""
Test del Pipeline Completo: API Janis → Bronze → Silver → Gold
"""
import sys
import os
import logging
import requests
import json
from datetime import datetime
from pyspark.sql import SparkSession
from pyspark.sql.functions import current_timestamp, col, lit
import pandas as pd

# Agregar path de módulos
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def init_spark():
    """Inicializar Spark para ejecución local"""
    spark = SparkSession.builder \
        .appName("full-pipeline-api-to-gold") \
        .master("local[*]") \
        .config("spark.sql.shuffle.partitions", "2") \
        .getOrCreate()
    
    spark.sparkContext.setLogLevel("WARN")
    return spark

def fetch_from_janis_api(order_id):
    """Obtener datos de la API de Janis"""
    url = f"https://oms.janis.in/api/order/{order_id}"
    
    headers = {
        'janis-client': 'cencosudprod',
        'janis-api-key': 'ZjU0YjI0YzItNjk0Yy00ZGU5LWI5ZTUtNjk5YzI5ZjI5ZjBl',
        'janis-api-secret': 'NjI5NzI5YzItNjk0Yy00ZGU5LWI5ZTUtNjk5YzI5ZjI5ZjBl'
    }
    
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()

def main():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
    logger = logging.getLogger('FullPipelineTest')
    
    logger.info("=" * 80)
    logger.info("TEST PIPELINE COMPLETO: API JANIS → BRONZE → SILVER → GOLD")
    logger.info("=" * 80)
    
    # Inicializar Spark
    spark = init_spark()
    
    # 1. BRONZE: Obtener datos de API Janis
    logger.info("\n" + "=" * 80)
    logger.info("FASE 1: BRONZE - Ingesta desde API Janis")
    logger.info("=" * 80)
    
    order_id = "6913fcb6d134afc8da8ac3dd"
    logger.info(f"\n1.1 Obteniendo orden {order_id} de API Janis...")
    
    try:
        order_data = fetch_from_janis_api(order_id)
        logger.info(f"     ✅ Orden obtenida exitosamente")
        logger.info(f"     Campos principales: {list(order_data.keys())[:10]}")
    except Exception as e:
        logger.error(f"     ❌ Error obteniendo datos de API: {e}")
        return 1
    
    # Guardar Bronze
    bronze_path = f"glue/data/bronze_order_{order_id}.json"
    logger.info(f"\n1.2 Guardando datos Bronze en: {bronze_path}")
    with open(bronze_path, 'w', encoding='utf-8') as f:
        json.dump(order_data, f, indent=2, ensure_ascii=False)
    
    # 2. SILVER: Transformar Bronze → Silver
    logger.info("\n" + "=" * 80)
    logger.info("FASE 2: SILVER - Transformación Bronze → Silver")
    logger.info("=" * 80)
    
    logger.info("\n2.1 Importando módulos Bronze-to-Silver...")
    from modules.json_flattener import JSONFlattener
    from modules.data_cleaner import DataCleaner
    from modules.data_normalizer import DataNormalizer
    from modules.data_type_converter import DataTypeConverter
    from modules.duplicate_detector import DuplicateDetector
    from modules.conflict_resolver import ConflictResolver
    from modules.data_gap_handler import DataGapHandler
    
    # Leer Bronze
    logger.info(f"\n2.2 Leyendo datos Bronze...")
    df_bronze = spark.read.json(bronze_path)
    logger.info(f"     Registros en Bronze: {df_bronze.count()}")
    logger.info(f"     Columnas en Bronze: {len(df_bronze.columns)}")
    
    # Configuración para módulos
    config_bronze_silver = {
        "business_keys": ["id"],
        "timestamp_column": "dateCreated",
        "critical_columns": ["id", "status"],
        "normalization_rules": {
            "email": ["email"],
            "phone": ["phone"],
            "date": ["dateCreated", "dateModified"]
        }
    }
    
    # Ejecutar pipeline Bronze → Silver
    logger.info("\n2.3 Ejecutando transformaciones Bronze → Silver...")
    
    df = df_bronze
    
    # JSONFlattener
    logger.info("     2.3.1 JSONFlattener...")
    flattener = JSONFlattener()
    df = flattener.transform(df, config_bronze_silver)
    logger.info(f"           → {df.count()} registros, {len(df.columns)} columnas")
    
    # DataCleaner
    logger.info("     2.3.2 DataCleaner...")
    cleaner = DataCleaner()
    df = cleaner.transform(df, config_bronze_silver)
    logger.info(f"           → {df.count()} registros")
    
    # DataNormalizer
    logger.info("     2.3.3 DataNormalizer...")
    normalizer = DataNormalizer()
    df = normalizer.transform(df, config_bronze_silver)
    logger.info(f"           → {df.count()} registros")
    
    # DataTypeConverter
    logger.info("     2.3.4 DataTypeConverter...")
    converter = DataTypeConverter()
    df = converter.transform(df, config_bronze_silver)
    logger.info(f"           → {df.count()} registros")
    
    # DuplicateDetector
    logger.info("     2.3.5 DuplicateDetector...")
    dup_detector = DuplicateDetector()
    df = dup_detector.transform(df, config_bronze_silver)
    logger.info(f"           → {df.count()} registros")
    
    # ConflictResolver
    logger.info("     2.3.6 ConflictResolver...")
    resolver = ConflictResolver()
    df = resolver.transform(df, config_bronze_silver)
    logger.info(f"           → {df.count()} registros")
    
    # DataGapHandler
    logger.info("     2.3.7 DataGapHandler...")
    gap_handler = DataGapHandler()
    df = gap_handler.transform(df, config_bronze_silver)
    logger.info(f"           → {df.count()} registros")
    
    # Guardar Silver
    silver_path = f"glue/data/silver_order_{order_id}"
    logger.info(f"\n2.4 Guardando datos Silver en: {silver_path}")
    df.coalesce(1).write.mode("overwrite").json(silver_path)
    
    logger.info(f"\n2.5 Datos Silver guardados exitosamente")
    logger.info(f"     Columnas en Silver: {len(df.columns)}")
    logger.info(f"     Primeras 10 columnas: {df.columns[:10]}")
    
    # 3. GOLD: Transformar Silver → Gold
    logger.info("\n" + "=" * 80)
    logger.info("FASE 3: GOLD - Transformación Silver → Gold")
    logger.info("=" * 80)
    
    logger.info("\n3.1 Importando módulos Silver-to-Gold...")
    from modules.silver_to_gold.silver_to_gold_aggregator import SilverToGoldAggregator
    from modules.silver_to_gold.data_quality_validator import DataQualityValidator
    from modules.silver_to_gold.error_handler import ErrorHandler
    
    # Leer Silver
    logger.info(f"\n3.2 Leyendo datos Silver...")
    df_silver = spark.read.json(silver_path)
    logger.info(f"     Registros en Silver: {df_silver.count()}")
    
    # Preparar datos para agregación (necesitamos campos específicos)
    logger.info("\n3.3 Preparando datos para agregación...")
    
    # Verificar si tenemos los campos necesarios
    required_fields = ["status", "dateCreated"]
    available_fields = [f for f in required_fields if f in df_silver.columns]
    
    if len(available_fields) < len(required_fields):
        logger.warning(f"     ⚠️  Faltan campos requeridos. Disponibles: {available_fields}")
        logger.info("     Creando campos sintéticos para demostración...")
        
        # Agregar campos sintéticos si no existen
        if "status" not in df_silver.columns:
            df_silver = df_silver.withColumn("status", lit("completado"))
        if "dateCreated" not in df_silver.columns:
            df_silver = df_silver.withColumn("dateCreated", current_timestamp())
        if "totalAmount" not in df_silver.columns:
            df_silver = df_silver.withColumn("totalAmount", lit(1000.0))
        if "metadata_sucursal" not in df_silver.columns:
            df_silver = df_silver.withColumn("metadata_sucursal", lit("Sucursal Centro"))
    
    # Renombrar columnas para que coincidan con config
    df_silver = df_silver.withColumnRenamed("dateCreated", "fecha_venta") \
                         .withColumnRenamed("totalAmount", "monto") \
                         .withColumnRenamed("status", "estado")
    
    # Configuración para Silver → Gold
    config_silver_gold = {
        "aggregations": {
            "date_column": "fecha_venta",
            "dimensions": ["metadata_sucursal", "estado"],
            "metrics": [
                {"column": "monto", "functions": ["sum", "avg", "min", "max"]},
                {"column": "*", "functions": ["count"]}
            ]
        },
        "quality": {
            "critical_columns": ["estado", "metadata_sucursal"],
            "valid_values": {
                "estado": ["completado", "pendiente", "cancelado", "rechazado", "pending", "completed"]
            },
            "numeric_ranges": {
                "monto": {"min": 0, "max": 99999999}
            },
            "quality_gate": False,
            "threshold": 0.8
        },
        "error_handler": {
            "dlq_enabled": False,
            "recovery_mode": "flag"
        }
    }
    
    # Ejecutar transformaciones Silver → Gold
    logger.info("\n3.4 Ejecutando transformaciones Silver → Gold...")
    
    df_gold = df_silver
    
    # SilverToGoldAggregator
    logger.info("     3.4.1 SilverToGoldAggregator...")
    aggregator = SilverToGoldAggregator()
    df_gold = aggregator.transform(df_gold, config_silver_gold)
    logger.info(f"           → {df_gold.count()} registros agregados")
    
    # DataQualityValidator
    logger.info("     3.4.2 DataQualityValidator...")
    validator = DataQualityValidator()
    df_gold = validator.transform(df_gold, config_silver_gold)
    logger.info(f"           → {df_gold.count()} registros validados")
    
    # ErrorHandler
    logger.info("     3.4.3 ErrorHandler...")
    error_handler = ErrorHandler()
    df_gold = error_handler.transform(df_gold, config_silver_gold)
    logger.info(f"           → {df_gold.count()} registros después de error handling")
    
    # Agregar timestamp de procesamiento
    df_gold = df_gold.withColumn("_processing_timestamp", current_timestamp())
    
    # Guardar Gold
    gold_path = f"glue/data/gold_order_{order_id}"
    logger.info(f"\n3.5 Guardando datos Gold en: {gold_path}")
    df_gold.coalesce(1).write.mode("overwrite").json(gold_path)
    
    # 4. RESULTADOS FINALES
    logger.info("\n" + "=" * 80)
    logger.info("RESULTADOS FINALES")
    logger.info("=" * 80)
    
    # Leer y mostrar Gold
    df_gold_final = spark.read.json(gold_path)
    
    logger.info(f"\n4.1 Resumen del Pipeline:")
    logger.info(f"     Bronze (raw):    1 orden de API Janis")
    logger.info(f"     Silver (clean):  {spark.read.json(silver_path).count()} registros")
    logger.info(f"     Gold (agg):      {df_gold_final.count()} registros agregados")
    
    logger.info(f"\n4.2 Columnas en Gold:")
    for col_name in sorted(df_gold_final.columns):
        logger.info(f"     - {col_name}")
    
    logger.info(f"\n4.3 Muestra de datos Gold:")
    # Seleccionar columnas relevantes si existen
    display_cols = []
    for col_name in ["metadata_sucursal", "estado", "total_monto", "promedio_monto", "num_registros", "_quality_valid"]:
        if col_name in df_gold_final.columns:
            display_cols.append(col_name)
    
    if display_cols:
        df_gold_final.select(*display_cols).show(truncate=False)
    else:
        df_gold_final.show(5, truncate=False)
    
    # Análisis de calidad
    if "_quality_valid" in df_gold_final.columns:
        logger.info(f"\n4.4 Análisis de Calidad:")
        valid_count = df_gold_final.filter(col("_quality_valid") == True).count()
        total = df_gold_final.count()
        logger.info(f"     Registros válidos: {valid_count}/{total} ({valid_count/total*100:.1f}%)")
    
    logger.info("\n" + "=" * 80)
    logger.info("✅ PIPELINE COMPLETO EJECUTADO EXITOSAMENTE")
    logger.info("=" * 80)
    logger.info("\nArchivos generados:")
    logger.info(f"  - Bronze: {bronze_path}")
    logger.info(f"  - Silver: {silver_path}/")
    logger.info(f"  - Gold:   {gold_path}/")
    logger.info("=" * 80)
    
    spark.stop()
    return 0

if __name__ == "__main__":
    sys.exit(main())
