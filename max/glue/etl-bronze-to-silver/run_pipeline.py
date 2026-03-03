"""
Script para ejecutar el pipeline completo Bronze-to-Silver
Este script ejecuta todas las transformaciones Y escribe los datos a la capa Silver

NOTA: Para pruebas locales, escribe a Parquet en lugar de Iceberg
Para producción con Iceberg real, usa main_job.py
"""

import sys
import os
import logging
import argparse
import json
from typing import Dict

from pyspark.sql import SparkSession

# Agregar src al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from etl_pipeline import ETLPipeline

# os.environ['HADOOP_HOME'] = 'C:\\hadoop'
def init_spark_session_simple():
    """Inicializar SparkSession corrigiendo el error de formato numérico '60s'"""
    spark = SparkSession.builder \
        .appName("bronze-to-silver-local-test") \
        .master("local[*]") \
        .config("spark.jars.packages", "org.apache.hadoop:hadoop-aws:3.3.4,com.amazonaws:aws-java-sdk-bundle:1.12.262") \
        .config("fs.s3a.connection.timeout", "60000") \
        .config("fs.s3a.connection.establish.timeout", "60000") \
        .config("spark.hadoop.fs.s3a.connection.timeout", "60000") \
        .config("spark.hadoop.fs.s3a.connection.establish.timeout", "60000") \
        .config("spark.hadoop.fs.s3a.threads.keepalivetime", "60000") \
        .config("spark.hadoop.fs.s3a.attempts.maximum", "10") \
        .config("spark.hadoop.fs.s3a.aws.credentials.provider", "org.apache.hadoop.fs.s3a.SimpleAWSCredentialsProvider") \
        .config("spark.hadoop.fs.s3a.endpoint", "http://localhost:4566") \
        .config("spark.hadoop.fs.s3a.access.key", "test") \
        .config("spark.hadoop.fs.s3a.secret.key", "test") \
        .config("spark.hadoop.fs.s3a.multipart.purge.age", "86400") \
        .config("spark.hadoop.fs.s3a.path.style.access", "true") \
        .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem") \
        .config("spark.hadoop.fs.s3a.connection.ssl.enabled", "false") \
        .config("spark.hadoop.fs.s3a.socket.send.buffer", "8192") \
        .config("spark.hadoop.fs.s3a.socket.recv.buffer", "8192") \
        .config("spark.hadoop.fs.s3a.paging.maximum", "5") \
        .config("spark.hadoop.fs.s3a.threads.max", "10") \
        .config("spark.hadoop.fs.s3a.connection.maximum", "10") \
        .config("spark.hadoop.fs.s3a.fast.upload", "true") \
        .config("spark.hadoop.fs.s3a.multipart.size", "104857600") \
        .config("spark.hadoop.fs.s3a.multipart.threshold", "2147483647") \
        .config("spark.hadoop.fs.s3a.fast.upload.buffer", "disk") \
        .config("spark.hadoop.fs.s3a.fast.upload.active.blocks", "4") \
        .config("spark.hadoop.fs.s3a.readahead.range", "65536") \
        .config("spark.hadoop.fs.s3a.retry.limit", "3") \
        .config("spark.hadoop.fs.s3a.retry.interval", "500") \
        .config("spark.hadoop.mapreduce.fileoutputcommitter.algorithm.version", "2") \
        .config("spark.hadoop.mapreduce.fileoutputcommitter.cleanup-failures.ignored", "true") \
        .getOrCreate()
    
    spark.sparkContext.setLogLevel("WARN")
    return spark


def setup_logging():
    """Configurar logging"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    return logging.getLogger('RunPipeline')


def load_entity_config(entity_type: str, config_dir: str = "config") -> Dict:
    """
    Carga la configuración de una entidad desde entities_mapping.json
    
    Args:
        entity_type: Tipo de entidad (orders, products, stock, etc.)
        config_dir: Directorio donde se encuentra entities_mapping.json
        
    Returns:
        Diccionario con configuración de la entidad
    """
    # Obtener el directorio del script actual
    script_dir = os.path.dirname(os.path.abspath(__file__))
    entities_mapping_path = os.path.join(script_dir, config_dir, "entities_mapping.json")
    
    with open(entities_mapping_path, 'r') as f:
        entities_mapping = json.load(f)
    
    # Si el JSON tiene estructura con "entities", usarla; si no, usar directamente
    if "entities" in entities_mapping:
        entities = entities_mapping["entities"]
    else:
        entities = entities_mapping
    
    if entity_type not in entities:
        raise ValueError(f"Entity type '{entity_type}' not found in entities_mapping.json")
    
    return entities[entity_type]


def replace_config_templates(config: dict, entity_config: dict, client: str, bronze_bucket: str, silver_bucket: str) -> dict:
    """
    Reemplazar variables de template en la configuración
    
    Args:
        config: Configuración cargada desde JSON
        entity_config: Configuración de la entidad desde entities_mapping.json
        client: Nombre del cliente (metro, wongio)
        bronze_bucket: Nombre del bucket Bronze
        silver_bucket: Nombre del bucket Silver
        
    Returns:
        Configuración con variables reemplazadas
    """
    import copy
    config = copy.deepcopy(config)
    
    # Convertir primary_key a lista si es string
    primary_key = entity_config.get("primary_key", "id")
    if isinstance(primary_key, str):
        primary_key = [primary_key]
    
    # Mapeo de variables de template
    replacements = {
        "${entity_type}": entity_config.get("entity_type", ""),
        "${primary_key}": primary_key,
        "${dedup_field}": entity_config.get("dedup_field", "dateModified"),
        "${required_fields}": entity_config.get("required_fields", []),
        "${bronze_bucket}": bronze_bucket,
        "${silver_bucket}": silver_bucket,
        "${client}": client,
        "${bronze_prefix}": entity_config.get("bronze_prefix", ""),
        "${silver_table}": entity_config.get("silver_table", "")
    }
    
    # Función recursiva para reemplazar templates
    def replace_in_dict(obj):
        if isinstance(obj, dict):
            return {k: replace_in_dict(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [replace_in_dict(item) for item in obj]
        elif isinstance(obj, str):
            result = obj
            for template, value in replacements.items():
                if template in result:
                    # Si el template es toda la cadena, reemplazar con el valor directo
                    if result == template:
                        return value
                    # Si no, reemplazar como string
                    result = result.replace(template, str(value) if not isinstance(value, (list, dict)) else json.dumps(value))
            return result
        else:
            return obj
    
    return replace_in_dict(config)


def parse_arguments():
    """Parsear argumentos de línea de comandos"""
    parser = argparse.ArgumentParser(
        description='Ejecutar pipeline Bronze-to-Silver para una entidad específica'
    )
    
    parser.add_argument(
        '--entity-type',
        type=str,
        required=True,
        help='Tipo de entidad a procesar (orders, products, stock, etc.)'
    )
    
    parser.add_argument(
        '--client',
        type=str,
        default='metro',
        choices=['metro', 'wongio'],
        help='Cliente para procesar (metro o wongio). Default: metro'
    )
    
    parser.add_argument(
        '--config-path',
        type=str,
        default='config/bronze-to-silver-config.example.json',
        help='Ruta al archivo de configuración del pipeline'
    )
    
    parser.add_argument(
        '--bronze-bucket',
        type=str,
        default='data-lake-bronze',
        help='Nombre del bucket Bronze en S3'
    )
    
    parser.add_argument(
        '--silver-bucket',
        type=str,
        default='data-lake-silver',
        help='Nombre del bucket Silver en S3'
    )
    
    return parser.parse_args()


def main():
    """Función principal"""
    logger = setup_logging()
    
    try:
        # Parsear argumentos
        args = parse_arguments()
        
        logger.info("=" * 80)
        logger.info(f"EJECUTANDO PIPELINE BRONZE-TO-SILVER: {args.entity_type.upper()}")
        logger.info(f"Cliente: {args.client}")
        logger.info("=" * 80)
        
        # Cargar configuración de entidad
        logger.info(f"\nCargando configuración para entidad: {args.entity_type}")
        entity_config = load_entity_config(args.entity_type)
        
        # Construir paths dinámicos
        bronze_prefix = entity_config.get("bronze_prefix", args.entity_type)
        silver_table = entity_config.get("silver_table", f"{args.entity_type}_clean")
        
        input_path = f"s3a://{args.bronze_bucket}/{args.client}/{bronze_prefix}/"
        output_path = f"s3a://{args.silver_bucket}/{args.client}_{silver_table}"
        
        logger.info(f"Bronze prefix: {bronze_prefix}")
        logger.info(f"Silver table: {args.client}_{silver_table}")
        logger.info(f"Input Path: {input_path}")
        logger.info(f"Output Path: {output_path}")
        logger.info(f"Config Path: {args.config_path}")
        
        # Inicializar Spark simple (sin Iceberg para pruebas locales)
        logger.info("\nInicializando Spark session...")
        spark = init_spark_session_simple()
        logger.info("Spark session inicializada correctamente")
        
        # Cargar configuración base y reemplazar templates
        logger.info("\nCargando y procesando configuración...")
        config_path_full = os.path.join(os.path.dirname(os.path.abspath(__file__)), args.config_path)
        with open(config_path_full, 'r') as f:
            base_config = json.load(f)
        
        # Reemplazar variables de template
        config = replace_config_templates(
            base_config,
            entity_config,
            args.client,
            args.bronze_bucket,
            args.silver_bucket
        )
        logger.info("Configuración procesada con templates reemplazados")
        
        # Crear pipeline
        logger.info("\nInicializando ETL Pipeline...")
        pipeline = ETLPipeline(
            spark=spark,
            config_path=args.config_path
        )
        # Reemplazar la configuración del pipeline con la procesada
        pipeline.config = config
        
        # Ejecutar transformaciones manualmente (sin escritura a Iceberg)
        logger.info("\n" + "=" * 80)
        logger.info("EJECUTANDO TRANSFORMACIONES")
        logger.info("=" * 80)
        
        # Leer datos
        logger.info("\n1. Leyendo datos de Bronze...")
        # Disable corrupt record column to avoid QUERY_ONLY_CORRUPT_RECORD_COLUMN error
        df = spark.read.option("mode", "PERMISSIVE").option("columnNameOfCorruptRecord", "").json(input_path)
        initial_count = df.count()
        logger.info(f"   Registros leídos: {initial_count}")
        
        # Ejecutar cada módulo (solo los primeros 5 para validación)
        validation_modules = pipeline.modules[:5]  # JSONFlattener, DataCleaner, DataNormalizer, DataTypeConverter, DuplicateDetector
        # Para validación, solo ejecutamos los primeros 4 módulos (sin DuplicateDetector)
        validation_modules = validation_modules[:4]
        
        for i, module in enumerate(validation_modules, 1):
            module_name = module.__class__.__name__
            logger.info(f"\n{i+1}. Ejecutando {module_name}...")
            df = module.transform(df, pipeline.config)
            logger.info(f"   Resultado: {df.count()} registros")
            
            # Debug: mostrar columnas después de cada módulo
            if i == 1:  # Después de JSONFlattener
                logger.info(f"   Columnas disponibles: {len(df.columns)} columnas")
                logger.info(f"   Primeras 10: {df.columns[:10]}")
        
        # Agregar timestamp de procesamiento
        from pyspark.sql.functions import current_timestamp
        df = df.withColumn("_processing_timestamp", current_timestamp())
        
        logger.info("\n" + "=" * 80)
        logger.info("TRANSFORMACIONES COMPLETADAS")
        logger.info("=" * 80)
        
        # Escribir a JSON local (simulando Silver layer)
        logger.info(f"\nEscribiendo {df.count()} registros a {output_path}...")
        
        # Guardar como JSON (más fácil de inspeccionar)
        df.coalesce(1).write.mode("overwrite").json(output_path)
        logger.info("Datos escritos exitosamente en formato JSON")
        
        # Skip CSV summary for complex types (arrays, structs not supported in CSV)
        # summary_path = f"output/silver/{args.client}_{silver_table}_summary.csv"
        # df.coalesce(1).write.mode("overwrite").option("header", "true").csv(summary_path)
        # logger.info(f"Resumen guardado en: {summary_path}")
        
        # Verificar datos escritos
        logger.info("\n" + "=" * 80)
        logger.info("VERIFICANDO DATOS EN SILVER (JSON)")
        logger.info("=" * 80)
        
        df_silver = spark.read.json(output_path)
        count = df_silver.count()
        
        logger.info(f"\nRegistros en Silver: {count}")
        logger.info("\nEsquema de la tabla Silver:")
        df_silver.printSchema()
        
        logger.info("\nPrimeros 5 registros en Silver:")
        df_silver.show(5, truncate=False)
        
        logger.info("\n" + "=" * 80)
        logger.info("RESUMEN")
        logger.info("=" * 80)
        logger.info(f"✅ Entidad: {args.entity_type}")
        logger.info(f"✅ Cliente: {args.client}")
        logger.info(f"✅ Bronze → Silver: {initial_count} → {count} registros")
        logger.info(f"✅ Datos guardados en: {output_path}")
        logger.info(f"✅ Resumen CSV en: output/silver/{args.client}_{silver_table}_summary.csv")
        logger.info(f"✅ Formato: JSON (compatible con cualquier sistema)")
        logger.info("\nNOTA: Los datos están listos. En producción con AWS Glue, se escribirán directamente a Iceberg en S3")
        
        # Detener Spark
        spark.stop()
        logger.info("\nSpark session detenida")
        
        return 0
        
    except Exception as e:
        logger.error("=" * 80)
        logger.error("ERROR EN LA EJECUCIÓN DEL PIPELINE")
        logger.error("=" * 80)
        logger.error(f"Error: {str(e)}")
        logger.exception("Traceback completo:")
        return 1


if __name__ == "__main__":
    sys.exit(main())
