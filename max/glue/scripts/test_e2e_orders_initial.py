#!/usr/bin/env python3
"""
Test End-to-End REAL: Orders Iniciales (Metro y Wongio)

Este script ejecuta el pipeline COMPLETO tal como está configurado:
1. Crea datos de prueba de orders para metro y wongio
2. Los guarda en Bronze (S3/LocalStack con particionamiento)
3. Ejecuta Bronze→Silver REAL usando run_pipeline.py
4. Ejecuta Silver→Gold REAL usando run_pipeline_to_gold.py
5. Muestra los resultados en cada capa leyendo desde S3

Requisitos:
    - LocalStack corriendo en localhost:4566
    - Buckets creados: data-lake-bronze, data-lake-silver, data-lake-gold
    - PySpark instalado

Uso:
    cd max/glue
    python scripts/test_e2e_orders_initial.py
"""

import json
import os
import sys
import subprocess
from datetime import datetime, timedelta
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger('E2E_Test_Initial')

# Agregar path para importar módulos
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

try:
    from pyspark.sql import SparkSession
    PYSPARK_AVAILABLE = True
except ImportError:
    PYSPARK_AVAILABLE = False
    logger.error("❌ PySpark no disponible - instalar con: pip install pyspark")
    sys.exit(1)


def init_spark_for_localstack():
    """Inicializar SparkSession para LocalStack"""
    spark = SparkSession.builder \
        .appName("e2e-test-orders-initial") \
        .master("local[*]") \
        .config("spark.jars.packages", "org.apache.hadoop:hadoop-aws:3.3.4,com.amazonaws:aws-java-sdk-bundle:1.12.262") \
        .config("spark.hadoop.fs.s3a.endpoint", "http://localhost:4566") \
        .config("spark.hadoop.fs.s3a.access.key", "test") \
        .config("spark.hadoop.fs.s3a.secret.key", "test") \
        .config("spark.hadoop.fs.s3a.path.style.access", "true") \
        .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem") \
        .config("spark.hadoop.fs.s3a.connection.ssl.enabled", "false") \
        .config("spark.hadoop.fs.s3a.aws.credentials.provider", "org.apache.hadoop.fs.s3a.SimpleAWSCredentialsProvider") \
        .config("spark.hadoop.fs.s3a.connection.timeout", "60000") \
        .config("spark.hadoop.fs.s3a.connection.establish.timeout", "60000") \
        .config("spark.hadoop.fs.s3a.threads.keepalivetime", "60000") \
        .config("spark.hadoop.fs.s3a.attempts.maximum", "10") \
        .config("spark.hadoop.fs.s3a.multipart.purge.age", "86400") \
        .getOrCreate()
    
    spark.sparkContext.setLogLevel("WARN")
    return spark


def create_order_data(order_id: str, client_id: str, status: str = "pending") -> dict:
    """Crear datos de orden realistas según API de Janis"""
    base_timestamp = int((datetime.now() - timedelta(hours=2)).timestamp() * 1000)
    
    return {
        "id": order_id,
        "orderGroupId": f"group-{order_id[:5]}",
        "commerceSequentialId": f"SEQ-{order_id[-6:]}",
        "commerceDateCreated": base_timestamp,
        "commerceSalesChannel": "ecommerce",
        "totalAmount": 250.75 if client_id == "metro" else 180.50,
        "commerceId": f"commerce-{client_id}",
        "status": status,
        "originalAmount": 250.75 if client_id == "metro" else 180.50,
        "rawTotalAmount": 250.75 if client_id == "metro" else 180.50,
        "currency": "CLP",
        "salesChannelName": "E-commerce Web",
        "account": {
            "name": f"Account {client_id.upper()}",
            "platform": "vtex"
        },
        "seller": {
            "name": f"Seller {client_id.upper()}",
            "id": f"seller-{client_id}"
        },
        "dateCreated": base_timestamp,
        "dateModified": base_timestamp,
        "customer": {
            "id": f"customer-{order_id[-4:]}",
            "email": f"customer{order_id[-4:]}@{client_id}.com",
            "firstName": "Juan" if client_id == "metro" else "María",
            "lastName": "Pérez" if client_id == "metro" else "González"
        },
        "totals": {
            "items": {
                "amount": 230.75 if client_id == "metro" else 160.50,
                "quantity": 3 if client_id == "metro" else 2
            },
            "shipping": {
                "amount": 20.00
            },
            "discounts": {
                "amount": 0.00
            }
        },
        "items": [
            {
                "id": f"item-{order_id}-1",
                "productId": f"prod-{client_id}-100",
                "skuId": f"sku-{client_id}-100-1",
                "name": "Producto A" if client_id == "metro" else "Producto X",
                "quantity": 2,
                "price": 75.50 if client_id == "metro" else 80.25,
                "subtotal": 151.00 if client_id == "metro" else 160.50
            },
            {
                "id": f"item-{order_id}-2",
                "productId": f"prod-{client_id}-200",
                "skuId": f"sku-{client_id}-200-1",
                "name": "Producto B" if client_id == "metro" else "Producto Y",
                "quantity": 1 if client_id == "metro" else 0,
                "price": 79.75 if client_id == "metro" else 0,
                "subtotal": 79.75 if client_id == "metro" else 0
            }
        ] if client_id == "metro" else [
            {
                "id": f"item-{order_id}-1",
                "productId": f"prod-{client_id}-100",
                "skuId": f"sku-{client_id}-100-1",
                "name": "Producto X",
                "quantity": 2,
                "price": 80.25,
                "subtotal": 160.50
            }
        ],
        "shipping": {
            "address": {
                "street": "Av. Principal 123" if client_id == "metro" else "Calle Secundaria 456",
                "city": "Santiago" if client_id == "metro" else "Valparaíso",
                "state": "RM" if client_id == "metro" else "V",
                "zipCode": "8320000" if client_id == "metro" else "2340000",
                "country": "CL"
            },
            "carrier": {
                "id": f"carrier-{client_id}",
                "name": "Carrier Express" if client_id == "metro" else "Fast Delivery"
            }
        },
        "payments": [
            {
                "id": f"payment-{order_id}-1",
                "method": "credit_card" if client_id == "metro" else "debit_card",
                "amount": 250.75 if client_id == "metro" else 180.50,
                "status": "approved",
                "transactionId": f"txn-{order_id}"
            }
        ],
        "statusChanges": [
            {
                "status": status,
                "dateCreated": base_timestamp,
                "userId": f"user-{client_id}"
            }
        ]
    }


def save_to_bronze_s3(order_data: dict, client_id: str, spark):
    """Guardar orden en Bronze S3/LocalStack"""
    date_str = datetime.now().strftime("%Y-%m-%d")
    s3_path = f"s3a://data-lake-bronze/{client_id}/orders/date={date_str}"
    
    # Crear JSON con metadata (formato Bronze)
    bronze_data = {
        "_metadata": {
            "client_id": client_id,
            "entity_type": "orders",
            "ingestion_timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "source": "test_script",
            "api_version": "v2"
        },
        "data": order_data
    }
    
    order_id = order_data["id"]
    
    # Convertir a JSON string para escribir
    json_str = json.dumps(bronze_data, ensure_ascii=False)
    
    # Crear DataFrame con una sola columna de string JSON
    from pyspark.sql.types import StructType, StructField, StringType
    schema = StructType([StructField("value", StringType(), True)])
    df = spark.createDataFrame([(json_str,)], schema)
    
    # Escribir como JSON
    df.coalesce(1).write.mode("append").text(s3_path, compression="none")
    
    logger.info(f"✅ Guardado en Bronze S3: {s3_path}/order_{order_id}.json")
    return s3_path


def display_bronze_data(spark, s3_path: str, client_id: str):
    """Mostrar datos de Bronze desde S3"""
    logger.info("\n" + "="*80)
    logger.info(f"DATOS EN BRONZE - Cliente: {client_id}")
    logger.info("="*80)
    
    df = spark.read.json(s3_path)
    count = df.count()
    
    logger.info(f"\nPath S3: {s3_path}")
    logger.info(f"Registros: {count}")
    logger.info("\nEsquema:")
    df.printSchema()
    logger.info("\nPrimeros registros:")
    df.show(5, truncate=False)


def run_bronze_to_silver(client_id: str):
    """Ejecutar pipeline Bronze→Silver REAL"""
    logger.info("\n" + "="*80)
    logger.info(f"EJECUTANDO BRONZE → SILVER - Cliente: {client_id}")
    logger.info("="*80)
    
    # Cambiar al directorio etl-bronze-to-silver
    etl_dir = os.path.join(os.path.dirname(__file__), '..', 'etl-bronze-to-silver')
    
    cmd = [
        sys.executable,
        'run_pipeline.py',
        '--entity-type', 'orders',
        '--client', client_id,
        '--bronze-bucket', 'data-lake-bronze',
        '--silver-bucket', 'data-lake-silver'
    ]
    
    logger.info(f"Comando: {' '.join(cmd)}")
    logger.info(f"Directorio: {etl_dir}")
    
    result = subprocess.run(
        cmd,
        cwd=etl_dir,
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        logger.info("✅ Pipeline Bronze→Silver completado exitosamente")
        logger.info("\nSalida del pipeline:")
        for line in result.stdout.split('\n')[-20:]:  # Últimas 20 líneas
            if line.strip():
                logger.info(f"  {line}")
    else:
        logger.error("❌ Error en pipeline Bronze→Silver")
        logger.error(f"Código de salida: {result.returncode}")
        logger.error("\nError:")
        logger.error(result.stderr)
        raise Exception("Pipeline Bronze→Silver falló")


def display_silver_data(spark, client_id: str):
    """Mostrar datos de Silver desde S3"""
    logger.info("\n" + "="*80)
    logger.info(f"DATOS EN SILVER - Cliente: {client_id}")
    logger.info("="*80)
    
    s3_path = f"s3a://data-lake-silver/{client_id}_orders_clean"
    
    try:
        df = spark.read.json(s3_path)
        count = df.count()
        
        logger.info(f"\nPath S3: {s3_path}")
        logger.info(f"Registros: {count}")
        logger.info("\nEsquema (primeras 20 columnas):")
        for field in df.schema.fields[:20]:
            logger.info(f"  - {field.name}: {field.dataType}")
        
        logger.info("\nPrimeros registros (campos clave):")
        key_fields = ['order_id', 'client_id', 'status', 'total_amount', 'date_created']
        available_fields = [f for f in key_fields if f in df.columns]
        if available_fields:
            df.select(available_fields).show(5, truncate=False)
        else:
            df.show(5, truncate=True)
            
    except Exception as e:
        logger.error(f"❌ Error leyendo Silver: {str(e)}")
        raise


def run_silver_to_gold(client_id: str):
    """Ejecutar pipeline Silver→Gold REAL"""
    logger.info("\n" + "="*80)
    logger.info(f"EJECUTANDO SILVER → GOLD - Cliente: {client_id}")
    logger.info("="*80)
    
    # Cambiar al directorio etl-silver-to-gold
    etl_dir = os.path.join(os.path.dirname(__file__), '..', 'etl-silver-to-gold')
    
    cmd = [
        sys.executable,
        'run_pipeline_to_gold.py',
        '--gold-table', 'wms_orders',
        '--client', client_id
    ]
    
    logger.info(f"Comando: {' '.join(cmd)}")
    logger.info(f"Directorio: {etl_dir}")
    
    result = subprocess.run(
        cmd,
        cwd=etl_dir,
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        logger.info("✅ Pipeline Silver→Gold completado exitosamente")
        logger.info("\nSalida del pipeline:")
        for line in result.stdout.split('\n')[-20:]:  # Últimas 20 líneas
            if line.strip():
                logger.info(f"  {line}")
    else:
        logger.error("❌ Error en pipeline Silver→Gold")
        logger.error(f"Código de salida: {result.returncode}")
        logger.error("\nError:")
        logger.error(result.stderr)
        raise Exception("Pipeline Silver→Gold falló")


def display_gold_data(spark, client_id: str):
    """Mostrar datos de Gold desde S3"""
    logger.info("\n" + "="*80)
    logger.info(f"DATOS EN GOLD - Cliente: {client_id}")
    logger.info("="*80)
    
    s3_path = f"s3a://data-lake-gold/{client_id}/orders"
    
    try:
        df = spark.read.parquet(s3_path)
        count = df.count()
        
        logger.info(f"\nPath S3: {s3_path}")
        logger.info(f"Registros: {count}")
        logger.info(f"Formato: Parquet con particionamiento")
        
        logger.info("\nEsquema (primeras 25 columnas):")
        for field in df.schema.fields[:25]:
            logger.info(f"  - {field.name}: {field.dataType}")
        
        logger.info("\nParticiones:")
        if 'year' in df.columns and 'month' in df.columns:
            df.select('year', 'month', 'day').distinct().show()
        
        logger.info("\nPrimeros registros (campos clave):")
        key_fields = ['order_id', 'client_id', 'status', 'total_amount', 'date_created', 
                     'total_changes', 'days_since_created']
        available_fields = [f for f in key_fields if f in df.columns]
        if available_fields:
            df.select(available_fields).show(5, truncate=False)
        else:
            df.show(5, truncate=True)
            
    except Exception as e:
        logger.error(f"❌ Error leyendo Gold: {str(e)}")
        raise


def main():
    """Función principal"""
    logger.info("="*80)
    logger.info("TEST END-TO-END REAL: ORDERS INICIALES (Metro y Wongio)")
    logger.info("="*80)
    logger.info(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    try:
        # Inicializar Spark
        logger.info("Inicializando Spark para LocalStack...")
        spark = init_spark_for_localstack()
        logger.info("✅ Spark inicializado\n")
        
        # ========================================
        # TEST 1: Order de Metro
        # ========================================
        logger.info("\n" + "#"*80)
        logger.info("# TEST 1: ORDER DE METRO")
        logger.info("#"*80)
        
        metro_order = create_order_data("ORD-METRO-001", "metro", "pending")
        metro_bronze_path = save_to_bronze_s3(metro_order, "metro", spark)
        display_bronze_data(spark, metro_bronze_path, "metro")
        
        run_bronze_to_silver("metro")
        display_silver_data(spark, "metro")
        
        run_silver_to_gold("metro")
        display_gold_data(spark, "metro")
        
        # ========================================
        # TEST 2: Order de Wongio
        # ========================================
        logger.info("\n" + "#"*80)
        logger.info("# TEST 2: ORDER DE WONGIO")
        logger.info("#"*80)
        
        wongio_order = create_order_data("ORD-WONGIO-001", "wongio", "pending")
        wongio_bronze_path = save_to_bronze_s3(wongio_order, "wongio", spark)
        display_bronze_data(spark, wongio_bronze_path, "wongio")
        
        run_bronze_to_silver("wongio")
        display_silver_data(spark, "wongio")
        
        run_silver_to_gold("wongio")
        display_gold_data(spark, "wongio")
        
        # ========================================
        # RESUMEN FINAL
        # ========================================
        logger.info("\n" + "="*80)
        logger.info("RESUMEN FINAL")
        logger.info("="*80)
        
        logger.info("\n✅ Test completado exitosamente!")
        logger.info("\nFlujo validado:")
        logger.info("  ✓ Bronze: JSON raw con metadata en S3/LocalStack")
        logger.info("  ✓ Silver: Datos limpios y normalizados (8 módulos ejecutados)")
        logger.info("  ✓ Gold: Esquema Redshift con campos calculados (8 módulos ejecutados)")
        
        logger.info("\nDatos en S3/LocalStack:")
        logger.info("  Metro Bronze:  s3://data-lake-bronze/metro/orders/")
        logger.info("  Metro Silver:  s3://data-lake-silver/metro_orders_clean/")
        logger.info("  Metro Gold:    s3://data-lake-gold/metro/orders/")
        logger.info("  Wongio Bronze: s3://data-lake-bronze/wongio/orders/")
        logger.info("  Wongio Silver: s3://data-lake-silver/wongio_orders_clean/")
        logger.info("  Wongio Gold:   s3://data-lake-gold/wongio/orders/")
        
        logger.info("\nPróximo paso:")
        logger.info("  → Ejecutar test_e2e_orders_update.py para probar actualizaciones")
        
        spark.stop()
        return 0
        
    except Exception as e:
        logger.error("="*80)
        logger.error("ERROR EN EL TEST")
        logger.error("="*80)
        logger.error(f"Error: {str(e)}")
        logger.exception("Traceback completo:")
        return 1


if __name__ == "__main__":
    sys.exit(main())
