"""
Script para ejecutar el pipeline Silver-to-Gold en LocalStack
Parametrizado para procesar cualquiera de las 26 tablas Gold
"""
import sys, os, logging, json, argparse
from pyspark.sql import SparkSession
from pyspark.sql.functions import current_timestamp

sys.path.insert(0, os.path.dirname(__file__))
from etl_pipeline_gold import ETLPipelineGold

os.environ["HADOOP_CONF_DIR"] = ""  # ← Agrega esto antes de init_spark()
def init_spark():
    spark = SparkSession.builder \
        .appName("silver-to-gold-local") \
        .master("local[*]") \
        .config("spark.jars.packages", "org.apache.hadoop:hadoop-aws:3.3.4,com.amazonaws:aws-java-sdk-bundle:1.12.262") \
        .config("spark.hadoop.fs.s3a.endpoint", "http://localhost:4566") \
        .config("spark.hadoop.fs.s3a.access.key", "test") \
        .config("spark.hadoop.fs.s3a.secret.key", "test") \
        .config("spark.hadoop.fs.s3a.path.style.access", "true") \
        .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem") \
        .config("spark.hadoop.fs.s3a.connection.ssl.enabled", "false") \
        .config("spark.hadoop.fs.s3a.aws.credentials.provider", "org.apache.hadoop.fs.s3a.SimpleAWSCredentialsProvider") \
        .config("spark.hadoop.fs.s3a.threads.keepalivetime", "60000") \
        .config("spark.hadoop.fs.s3a.multipart.purge.age", "86400") \
        .getOrCreate()
    
    # Sobrescribir propiedades de Hadoop directamente en el contexto
    hadoop_conf = spark.sparkContext._jsc.hadoopConfiguration()
    hadoop_conf.set("fs.s3a.endpoint", "http://localhost:4566")
    hadoop_conf.set("fs.s3a.access.key", "test")
    hadoop_conf.set("fs.s3a.secret.key", "test")
    hadoop_conf.set("fs.s3a.path.style.access", "true")
    hadoop_conf.set("fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem")
    hadoop_conf.set("fs.s3a.connection.ssl.enabled", "false")
    hadoop_conf.set("fs.s3a.aws.credentials.provider", "org.apache.hadoop.fs.s3a.SimpleAWSCredentialsProvider")
    hadoop_conf.set("fs.s3a.connection.timeout", "30000")
    hadoop_conf.set("fs.s3a.connection.establish.timeout", "5000")
    hadoop_conf.set("fs.s3a.threads.keepalivetime", "60000")
    hadoop_conf.set("fs.s3a.multipart.purge.age", "86400000")
    hadoop_conf.set("fs.s3a.attempts.maximum", "3")
    hadoop_conf.set("fs.s3a.connection.maximum", "15")
    
    spark.sparkContext.setLogLevel("WARN")
    return spark


def load_redshift_schemas(config_path: str = None) -> dict:
    """Carga el archivo de esquemas Redshift"""
    if config_path is None:
        # Buscar el archivo desde la ubicación del script
        script_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(script_dir, 'config', 'redshift_schemas.json')
    
    with open(config_path, 'r') as f:
        return json.load(f)


def get_table_config(gold_table: str, schemas: dict) -> dict:
    """
    Obtiene la configuración de una tabla Gold específica
    
    Args:
        gold_table: Nombre de la tabla Gold (ej: wms_orders, products, stock)
        schemas: Diccionario con esquemas de redshift_schemas.json
        
    Returns:
        dict: Configuración de la tabla incluyendo source_entity, partition_strategy, etc.
    """
    if gold_table not in schemas.get("tables", {}):
        raise ValueError(f"Tabla Gold '{gold_table}' no encontrada en redshift_schemas.json")
    
    table_schema = schemas["tables"][gold_table]
    
    # Determinar entidad(es) fuente desde field_mappings.json
    script_dir = os.path.dirname(os.path.abspath(__file__))
    field_mappings_path = os.path.join(script_dir, 'config', 'field_mappings.json')
    with open(field_mappings_path, 'r') as f:
        field_mappings = json.load(f)
    
    if gold_table not in field_mappings.get("mappings", {}):
        raise ValueError(f"Mapeo de campos para '{gold_table}' no encontrado en field_mappings.json")
    
    source_entity = field_mappings["mappings"][gold_table]["source_entity"]
    source_tables = field_mappings["mappings"][gold_table].get("source_tables", [])
    
    return {
        "gold_table": gold_table,
        "source_entity": source_entity,
        "source_tables": source_tables,
        "partition_strategy": table_schema.get("partition_strategy", {"type": "none"}),
        "fields": table_schema.get("fields", {}),
        "description": table_schema.get("description", "")
    }


def build_input_paths(source_entity: str, source_tables: list, source_client: str = "metro") -> list:
    """
    Construye las rutas de entrada desde Silver usando los nombres de tabla configurados
    
    Args:
        source_entity: Nombre de la entidad fuente (orders, products, etc.) - usado solo para logging
        source_tables: Lista de nombres de tablas Silver (ej: ["metro_order_items_clean"])
        source_client: Cliente fuente en Silver (siempre metro para datos existentes)
        
    Returns:
        list: Lista de rutas S3 de tablas Silver
    """
    # Usar los nombres de tabla configurados en field_mappings.json
    paths = []
    for table_name in source_tables:
        # Si la tabla ya tiene el prefijo del cliente, usarla directamente
        if table_name.startswith(f"{source_client}_"):
            base_path = f"s3a://data-lake-silver/{table_name}"
        else:
            # Si no, agregar el prefijo del cliente
            base_path = f"s3a://data-lake-silver/{source_client}_{table_name}"
        paths.append(base_path)
    return paths


def build_output_path(gold_table: str, source_entity: str, client: str = "wongio") -> str:
    """
    Construye la ruta de salida en Gold con estructura wongio/entity/
    
    Args:
        gold_table: Nombre de la tabla Gold
        source_entity: Entidad fuente (orders, products, etc.)
        client: Cliente (wongio por defecto)
        
    Returns:
        str: Ruta S3 de la tabla Gold
    """
    return f"s3a://data-lake-gold/{client}/{source_entity}"


def main():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
    logger = logging.getLogger('GoldPipeline')
    
    # Parse CLI arguments
    parser = argparse.ArgumentParser(description='Ejecutar pipeline Silver-to-Gold para una tabla específica')
    parser.add_argument('--gold-table', type=str, required=True,
                        help='Nombre de la tabla Gold (ej: wms_orders, products, stock)')
    parser.add_argument('--client', type=str, default='wongio',
                        help='Cliente (metro o wongio)')
    parser.add_argument('--config-path', type=str, default='config/silver-to-gold-config.json',
                        help='Ruta al archivo de configuración')
    
    args = parser.parse_args()
    
    logger.info("=" * 60)
    logger.info(f"PIPELINE SILVER → GOLD: {args.gold_table}")
    logger.info(f"Cliente: {args.client}")
    logger.info("=" * 60)
    
    # Cargar esquemas Redshift
    schemas = load_redshift_schemas()
    table_config = get_table_config(args.gold_table, schemas)
    
    logger.info(f"Tabla: {table_config['gold_table']}")
    logger.info(f"Entidad fuente: {table_config['source_entity']}")
    logger.info(f"Particionamiento: {table_config['partition_strategy']['type']}")
    
    # Construir rutas dinámicas
    # Silver siempre usa 'metro' como prefijo, Gold usa el cliente especificado
    input_paths = build_input_paths(
        table_config['source_entity'], 
        table_config['source_tables'],
        source_client="metro"
    )
    output_path = build_output_path(args.gold_table, table_config['source_entity'], args.client)
    
    logger.info(f"Input: {input_paths}")
    logger.info(f"Output: {output_path}")
    
    spark = init_spark()
    
    # Actualizar configuración con parámetros dinámicos
    pipeline = ETLPipelineGold(spark, args.config_path)
    pipeline.config['gold_table'] = args.gold_table
    pipeline.config['client'] = args.client
    pipeline.config['table_config'] = table_config
    
    # 1. Leer Silver (puede ser múltiples tablas)
    logger.info("Leyendo datos de Silver...")
    df = None
    for input_path in input_paths:
        logger.info(f"  Leyendo: {input_path}")
        df_temp = spark.read.json(input_path)
        if df is None:
            df = df_temp
        else:
            # Si hay múltiples tablas, hacer join (implementar lógica según necesidad)
            df = df.union(df_temp)
    
    logger.info(f"Registros en Silver: {df.count()}")
    
    # 2. Ejecutar módulos
    for module in pipeline.modules:
        name = module.__class__.__name__
        logger.info(f"Ejecutando {name}...")
        df = module.transform(df, pipeline.config)
        logger.info(f"  → {df.count()} registros")
    
    # 3. Agregar timestamp de procesamiento y columnas de particionamiento
    from pyspark.sql.functions import year, month, dayofmonth, to_date
    
    df = df.withColumn("_processing_timestamp", current_timestamp())
    
    # Extraer columnas de particionamiento desde date_created
    # Asumiendo que date_created existe en el DataFrame
    if "date_created" in df.columns:
            df = df.withColumn("year", year("_processing_timestamp"))
            df = df.withColumn("month", month("_processing_timestamp"))
            df = df.withColumn("day", dayofmonth("_processing_timestamp"))
    else:
        # Fallback: usar _processing_timestamp si date_created no existe
        logger.warning("Campo 'date_created' no encontrado, usando _processing_timestamp para particionamiento")
        df = df.withColumn("year", year("_processing_timestamp"))
        df = df.withColumn("month", month("_processing_timestamp"))
        df = df.withColumn("day", dayofmonth("_processing_timestamp"))
    
    # 4. Escribir a Gold en formato Parquet con particionamiento Hive-style
    logger.info(f"Escribiendo a Gold: {output_path}")
    logger.info("Formato: Parquet con compresión Snappy")
    logger.info("Particionamiento: year/month/day")
    
    df.write \
        .mode("overwrite") \
        .partitionBy("year", "month", "day") \
        .option("compression", "snappy") \
        .parquet(output_path)
    
    # 5. Actualizar metadata incremental
    if len(pipeline.modules) > 0 and hasattr(pipeline.modules[0], 'update_timestamp'):
        pipeline.modules[0].update_timestamp(
            spark.read.json(input_paths[0]), 
            pipeline.config
        )
    
    # 6. Verificar
    logger.info("Verificando datos escritos en Gold...")
    df_gold = spark.read.parquet(output_path)
    logger.info(f"✅ Registros en Gold: {df_gold.count()}")
    
    # Mostrar estructura de particiones
    logger.info("\nEstructura de particiones:")
    df_gold.select("year", "month", "day").distinct().orderBy("year", "month", "day").show()
    
    logger.info("\nMuestra de datos:")
    df_gold.show(10, truncate=False)
    
    spark.stop()
    return 0


if __name__ == "__main__":
    sys.exit(main())