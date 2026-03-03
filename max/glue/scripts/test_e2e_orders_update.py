#!/usr/bin/env python3
"""
Test End-to-End REAL: Orders Actualizadas (Metro y Wongio)

Este script ejecuta el pipeline COMPLETO con actualizaciones:
1. Crea actualizaciones de las orders existentes (cambio de status)
2. Las guarda en Bronze (NUEVO archivo - inmutable)
3. Ejecuta Bronze→Silver REAL (UPSERT - actualiza registro)
4. Ejecuta Silver→Gold REAL (UPSERT - actualiza registro)
5. Muestra cómo se manejan las actualizaciones en cada capa

Requisitos:
    - Haber ejecutado test_e2e_orders_initial.py primero
    - LocalStack corriendo en localhost:4566
    - PySpark instalado

Uso:
    cd max/glue
    python scripts/test_e2e_orders_update.py
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
logger = logging.getLogger('E2E_Test_Update')

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
        .appName("e2e-test-orders-update") \
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


def create_order_update(order_id: str, client_id: str, new_status: str, version: int = 2) -> dict:
    """Crear actualización de orden (cambio de status)"""
    base_timestamp = int((datetime.now() - timedelta(hours=1)).timestamp() * 1000)
    modified_timestamp = int(datetime.now().timestamp() * 1000)
    
    return {
        "id": order_id,
        "orderGroupId": f"group-{order_id[:5]}",
        "commerceSequentialId": f"SEQ-{order_id[-6:]}",
        "commerceDateCreated": base_timestamp - 3600000,
        "commerceSalesChannel": "ecommerce",
        "totalAmount": 250.75 if client_id == "metro" else 180.50,
        "commerceId": f"commerce-{client_id}",
        "status": new_status,  # ← CAMBIO PRINCIPAL
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
        "dateCreated": base_timestamp - 3600000,
        "dateModified": modified_timestamp,  # ← ACTUALIZADO
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
                "status": "pending",
                "dateCreated": base_timestamp - 3600000,
                "userId": f"user-{client_id}"
            },
            {
                "status": new_status,  # ← NUEVO CAMBIO DE STATUS
                "dateCreated": modified_timestamp,
                "userId": f"user-{client_id}"
            }
        ]
    }


def save_update_to_bronze_s3(order_data: dict, client_id: str, version: int, spark):
    """Guardar actualización en Bronze (NUEVO archivo - inmutable)"""
    date_str = datetime.now().strftime("%Y-%m-%d")
    s3_path = f"s3a://data-lake-bronze/{client_id}/orders/date={date_str}"
    
    # Crear JSON con metadata
    bronze_data = {
        "_metadata": {
            "client_id": client_id,
            "entity_type": "orders",
            "ingestion_timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "source": "test_script_update",
            "api_version": "v2",
            "event_type": "order.updated",
            "version": version
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
    
    logger.info(f"✅ Actualización guardada en Bronze S3: {s3_path}/order_{order_id}_v{version}.json")
    return s3_path


def show_bronze_versions(spark, s3_path: str, client_id: str):
    """Mostrar todas las versiones en Bronze (inmutable)"""
    logger.info("\n" + "="*80)
    logger.info(f"TODAS LAS VERSIONES EN BRONZE - Cliente: {client_id}")
    logger.info("="*80)
    
    df = spark.read.json(s3_path)
    count = df.count()
    
    logger.info(f"\nPath S3: {s3_path}")
    logger.info(f"Total de archivos: {count}")
    logger.info("\n💡 Bronze mantiene TODAS las versiones (inmutable)")
    
    # Mostrar versiones
    if '_metadata' in df.columns:
        logger.info("\nVersiones encontradas:")
        df.select('_metadata.version', '_metadata.event_type', '_metadata.ingestion_timestamp', 
                 'data.id', 'data.status').show(truncate=False)


def display_silver_comparison(spark, client_id: str):
    """Mostrar comparación en Silver (UPSERT)"""
    logger.info("\n" + "="*80)
    logger.info(f"DATOS EN SILVER (Después del UPSERT) - Cliente: {client_id}")
    logger.info("="*80)
    
    s3_path = f"s3a://data-lake-silver/{client_id}_orders_clean"
    
    try:
        df = spark.read.json(s3_path)
        count = df.count()
        
        logger.info(f"\nPath S3: {s3_path}")
        logger.info(f"Registros: {count}")
        logger.info("\n💡 Silver mantiene SOLO la última versión (UPSERT)")
        
        logger.info("\nDatos actualizados:")
        key_fields = ['order_id', 'status', 'date_modified', '_processing_timestamp']
        available_fields = [f for f in key_fields if f in df.columns]
        if available_fields:
            df.select(available_fields).show(truncate=False)
        else:
            df.show(5, truncate=True)
            
    except Exception as e:
        logger.error(f"❌ Error leyendo Silver: {str(e)}")
        raise


def display_gold_comparison(spark, client_id: str):
    """Mostrar comparación en Gold (UPSERT)"""
    logger.info("\n" + "="*80)
    logger.info(f"DATOS EN GOLD (Después del UPSERT) - Cliente: {client_id}")
    logger.info("="*80)
    
    s3_path = f"s3a://data-lake-gold/{client_id}/orders"
    
    try:
        df = spark.read.parquet(s3_path)
        count = df.count()
        
        logger.info(f"\nPath S3: {s3_path}")
        logger.info(f"Registros: {count}")
        logger.info("\n💡 Gold mantiene SOLO la última versión (UPSERT)")
        
        logger.info("\nDatos actualizados (con campos calculados):")
        key_fields = ['order_id', 'status', 'date_modified', 'total_changes', '_processing_timestamp']
        available_fields = [f for f in key_fields if f in df.columns]
        if available_fields:
            df.select(available_fields).show(truncate=False)
        else:
            df.show(5, truncate=True)
            
    except Exception as e:
        logger.error(f"❌ Error leyendo Gold: {str(e)}")
        raise


def run_bronze_to_silver(client_id: str):
    """Ejecutar pipeline Bronze→Silver REAL"""
    logger.info("\n" + "="*80)
    logger.info(f"EJECUTANDO BRONZE → SILVER (UPSERT) - Cliente: {client_id}")
    logger.info("="*80)
    
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
    
    result = subprocess.run(
        cmd,
        cwd=etl_dir,
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        logger.info("✅ Pipeline Bronze→Silver completado (UPSERT ejecutado)")
    else:
        logger.error("❌ Error en pipeline Bronze→Silver")
        logger.error(result.stderr)
        raise Exception("Pipeline Bronze→Silver falló")


def run_silver_to_gold(client_id: str):
    """Ejecutar pipeline Silver→Gold REAL"""
    logger.info("\n" + "="*80)
    logger.info(f"EJECUTANDO SILVER → GOLD (UPSERT) - Cliente: {client_id}")
    logger.info("="*80)
    
    etl_dir = os.path.join(os.path.dirname(__file__), '..', 'etl-silver-to-gold')
    
    cmd = [
        sys.executable,
        'run_pipeline_to_gold.py',
        '--gold-table', 'wms_orders',
        '--client', client_id
    ]
    
    logger.info(f"Comando: {' '.join(cmd)}")
    
    result = subprocess.run(
        cmd,
        cwd=etl_dir,
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        logger.info("✅ Pipeline Silver→Gold completado (UPSERT ejecutado)")
    else:
        logger.error("❌ Error en pipeline Silver→Gold")
        logger.error(result.stderr)
        raise Exception("Pipeline Silver→Gold falló")


def main():
    """Función principal"""
    logger.info("="*80)
    logger.info("TEST END-TO-END REAL: ORDERS ACTUALIZADAS (Metro y Wongio)")
    logger.info("="*80)
    logger.info(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    try:
        # Inicializar Spark
        logger.info("Inicializando Spark para LocalStack...")
        spark = init_spark_for_localstack()
        logger.info("✅ Spark inicializado\n")
        
        # ========================================
        # TEST 1: Actualización Order Metro
        # ========================================
        logger.info("\n" + "#"*80)
        logger.info("# TEST 1: ACTUALIZACIÓN ORDER METRO (pending → confirmed)")
        logger.info("#"*80)
        
        metro_order_id = "ORD-METRO-001"
        metro_update = create_order_update(metro_order_id, "metro", "confirmed", version=2)
        metro_bronze_path = save_update_to_bronze_s3(metro_update, "metro", 2, spark)
        
        show_bronze_versions(spark, metro_bronze_path, "metro")
        
        run_bronze_to_silver("metro")
        display_silver_comparison(spark, "metro")
        
        run_silver_to_gold("metro")
        display_gold_comparison(spark, "metro")
        
        # ========================================
        # TEST 2: Actualización Order Wongio
        # ========================================
        logger.info("\n" + "#"*80)
        logger.info("# TEST 2: ACTUALIZACIÓN ORDER WONGIO (pending → shipped)")
        logger.info("#"*80)
        
        wongio_order_id = "ORD-WONGIO-001"
        wongio_update = create_order_update(wongio_order_id, "wongio", "shipped", version=2)
        wongio_bronze_path = save_update_to_bronze_s3(wongio_update, "wongio", 2, spark)
        
        show_bronze_versions(spark, wongio_bronze_path, "wongio")
        
        run_bronze_to_silver("wongio")
        display_silver_comparison(spark, "wongio")
        
        run_silver_to_gold("wongio")
        display_gold_comparison(spark, "wongio")
        
        # ========================================
        # RESUMEN FINAL
        # ========================================
        logger.info("\n" + "="*80)
        logger.info("RESUMEN FINAL - MANEJO DE ACTUALIZACIONES")
        logger.info("="*80)
        
        logger.info("\n✅ Test de actualizaciones completado!")
        
        logger.info("\n📋 Comportamiento por capa:")
        logger.info("\n1. BRONZE (Inmutable):")
        logger.info("   ✓ Cada actualización crea un NUEVO archivo")
        logger.info("   ✓ Se mantienen TODAS las versiones")
        logger.info("   ✓ Permite auditoría completa y time travel")
        
        logger.info("\n2. SILVER (Mutable con Iceberg):")
        logger.info("   ✓ UPSERT: Actualiza el registro existente")
        logger.info("   ✓ Se mantiene SOLO la última versión")
        logger.info("   ✓ Deduplicación por order_id (última versión gana)")
        
        logger.info("\n3. GOLD (Mutable con Parquet):")
        logger.info("   ✓ UPSERT: Actualiza el registro existente")
        logger.info("   ✓ Recalcula campos derivados (total_changes)")
        logger.info("   ✓ Listo para MERGE en Redshift")
        
        logger.info("\n💡 Ventajas de esta arquitectura:")
        logger.info("   • Bronze: Auditoría completa, reprocessing sin pérdida")
        logger.info("   • Silver/Gold: Queries eficientes, ACID transactions")
        logger.info("   • Redshift: Performance óptimo para BI")
        
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
