"""
Test de Integración con API Real de Janis

Este script prueba la integración completa:
1. Conectar a API de Janis
2. Obtener datos reales de orders
3. Escribir a tabla Iceberg
4. Leer y validar datos

Credenciales Janis:
- Client: wongio
- API Key: 8fc949ac-6d63-4447-a3d6-a16b66048e61
- API Secret: UwPbe45dmE7lySRJ3zcA66Pfdt7xAY3QXWO181Y8OTgCxE3aZuyXpS8HyyPSwsWK
"""

import os
import sys
import requests
from datetime import datetime
from decimal import Decimal
from pyspark.sql import SparkSession
from pyspark.sql.types import (
    StructType, StructField, StringType, IntegerType, 
    TimestampType, DecimalType, BooleanType
)

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from modules.iceberg_manager import IcebergTableManager
from modules.iceberg_writer import IcebergWriter


# Configuración de API Janis
JANIS_API_BASE_URL = "https://api.janis.com"
JANIS_CLIENT = "wongio"
JANIS_API_KEY = "8fc949ac-6d63-4447-a3d6-a16b66048e61"
JANIS_API_SECRET = "UwPbe45dmE7lySRJ3zcA66Pfdt7xAY3QXWO181Y8OTgCxE3aZuyXpS8HyyPSwsWK"


def get_spark_session():
    """Crear SparkSession para testing local."""
    # Configurar HADOOP_HOME si no está configurado
    if 'HADOOP_HOME' not in os.environ:
        hadoop_home = os.path.join(os.path.dirname(__file__), 'hadoop_home')
        os.environ['HADOOP_HOME'] = os.path.abspath(hadoop_home)
    
    # Fix for Windows
    os.environ['SPARK_LOCAL_HOSTNAME'] = 'localhost'
    
    spark = SparkSession.builder \
        .appName("JanisAPIIntegrationTest") \
        .master("local[2]") \
        .config("spark.driver.memory", "1g") \
        .config("spark.driver.host", "localhost") \
        .config("spark.driver.bindAddress", "127.0.0.1") \
        .config("spark.sql.warehouse.dir", "./test-warehouse-janis") \
        .config("spark.sql.extensions", "org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions") \
        .config("spark.sql.catalog.local", "org.apache.iceberg.spark.SparkCatalog") \
        .config("spark.sql.catalog.local.type", "hadoop") \
        .config("spark.sql.catalog.local.warehouse", "./test-warehouse-janis") \
        .config("spark.ui.enabled", "false") \
        .config("spark.hadoop.fs.file.impl", "org.apache.hadoop.fs.LocalFileSystem") \
        .config("spark.jars.packages", 
                "org.apache.iceberg:iceberg-spark-runtime-3.5_2.12:1.5.2") \
        .getOrCreate()
    
    spark.sparkContext.setLogLevel("ERROR")
    return spark


def call_janis_api(endpoint, params=None):
    """
    Llamar a la API de Janis con autenticación.
    
    Args:
        endpoint: Endpoint de la API (ej: '/api/v2/orders')
        params: Parámetros de query (opcional)
    
    Returns:
        dict: Respuesta JSON de la API
    """
    url = f"{JANIS_API_BASE_URL}{endpoint}"
    
    headers = {
        "janis-client": JANIS_CLIENT,
        "janis-api-key": JANIS_API_KEY,
        "janis-api-secret": JANIS_API_SECRET,
        "Content-Type": "application/json"
    }
    
    print(f"\n📡 Llamando a API Janis: {endpoint}")
    print(f"   URL: {url}")
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        print(f"✅ Respuesta exitosa: {response.status_code}")
        
        return data
    
    except requests.exceptions.RequestException as e:
        print(f"❌ Error en llamada a API: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"   Status Code: {e.response.status_code}")
            print(f"   Response: {e.response.text[:500]}")
        raise


def convert_unix_to_timestamp(unix_timestamp):
    """Convertir Unix timestamp a datetime."""
    if unix_timestamp is None:
        return None
    return datetime.utcfromtimestamp(unix_timestamp)


def transform_order_to_silver(order_json):
    """
    Transformar orden de API JSON a formato Silver.
    
    Args:
        order_json: Orden en formato JSON de API Janis
    
    Returns:
        dict: Orden transformada para Silver layer
    """
    # Extraer delivery address si existe
    delivery_address = order_json.get('delivery_address', {}) or {}
    
    # Extraer metadata si existe
    metadata = order_json.get('metadata', {})
    
    transformed = {
        # IDs y referencias
        "order_id": order_json.get('order_id'),
        "order_number": order_json.get('order_number'),
        "status": order_json.get('status'),
        
        # Timestamps
        "date_created": convert_unix_to_timestamp(order_json.get('date_created')),
        "date_modified": convert_unix_to_timestamp(order_json.get('date_modified')),
        
        # Referencias
        "store_id": order_json.get('store_id'),
        "customer_id": order_json.get('customer_id'),
        "customer_email": order_json.get('customer_email'),
        "customer_phone": order_json.get('customer_phone'),
        
        # Delivery
        "delivery_type": order_json.get('delivery_type'),
        "delivery_street": delivery_address.get('street'),
        "delivery_city": delivery_address.get('city'),
        "delivery_district": delivery_address.get('district'),
        "delivery_postal_code": delivery_address.get('postal_code'),
        
        # Payment
        "payment_method": order_json.get('payment_method'),
        "payment_status": order_json.get('payment_status'),
        
        # Montos
        "subtotal": Decimal(str(order_json.get('subtotal', 0))),
        "tax": Decimal(str(order_json.get('tax', 0))),
        "shipping_cost": Decimal(str(order_json.get('shipping_cost', 0))),
        "discount": Decimal(str(order_json.get('discount', 0))),
        "total": Decimal(str(order_json.get('total', 0))),
        "currency": order_json.get('currency', 'PEN'),
        
        # Items
        "items_count": order_json.get('items_count', 0),
        "items_picked": order_json.get('items_picked'),
        "items_substituted": order_json.get('items_substituted'),
        
        # Status
        "picking_status": order_json.get('picking_status'),
        "shipping_status": order_json.get('shipping_status'),
        
        # Notas
        "notes": order_json.get('notes'),
        
        # Metadata de ingesta
        "source_type": "api_test",
        "ingestion_timestamp": datetime.utcnow(),
        "api_version": "v2"
    }
    
    return transformed


def create_orders_silver_schema():
    """Crear esquema para tabla orders en Silver layer."""
    return StructType([
        # IDs y referencias
        StructField("order_id", StringType(), nullable=False),
        StructField("order_number", StringType(), nullable=True),
        StructField("status", StringType(), nullable=True),
        
        # Timestamps
        StructField("date_created", TimestampType(), nullable=True),
        StructField("date_modified", TimestampType(), nullable=True),
        
        # Referencias
        StructField("store_id", StringType(), nullable=True),
        StructField("customer_id", StringType(), nullable=True),
        StructField("customer_email", StringType(), nullable=True),
        StructField("customer_phone", StringType(), nullable=True),
        
        # Delivery
        StructField("delivery_type", StringType(), nullable=True),
        StructField("delivery_street", StringType(), nullable=True),
        StructField("delivery_city", StringType(), nullable=True),
        StructField("delivery_district", StringType(), nullable=True),
        StructField("delivery_postal_code", StringType(), nullable=True),
        
        # Payment
        StructField("payment_method", StringType(), nullable=True),
        StructField("payment_status", StringType(), nullable=True),
        
        # Montos
        StructField("subtotal", DecimalType(18, 2), nullable=True),
        StructField("tax", DecimalType(18, 2), nullable=True),
        StructField("shipping_cost", DecimalType(18, 2), nullable=True),
        StructField("discount", DecimalType(18, 2), nullable=True),
        StructField("total", DecimalType(18, 2), nullable=True),
        StructField("currency", StringType(), nullable=True),
        
        # Items
        StructField("items_count", IntegerType(), nullable=True),
        StructField("items_picked", IntegerType(), nullable=True),
        StructField("items_substituted", IntegerType(), nullable=True),
        
        # Status
        StructField("picking_status", StringType(), nullable=True),
        StructField("shipping_status", StringType(), nullable=True),
        
        # Notas
        StructField("notes", StringType(), nullable=True),
        
        # Metadata de ingesta
        StructField("source_type", StringType(), nullable=False),
        StructField("ingestion_timestamp", TimestampType(), nullable=False),
        StructField("api_version", StringType(), nullable=True)
    ])


def main():
    """Función principal del test de integración."""
    print("=" * 80)
    print("🧪 TEST DE INTEGRACIÓN: API JANIS → ICEBERG")
    print("=" * 80)
    
    try:
        # Paso 1: Obtener datos de API Janis
        print("\n📋 PASO 1: Obtener datos de API Janis")
        print("-" * 80)
        
        # Llamar a API de orders (limitar a 10 para prueba)
        api_response = call_janis_api("/api/v2/orders", params={"limit": 10})
        
        # Verificar respuesta
        if not api_response:
            print("❌ No se recibieron datos de la API")
            return False
        
        # Extraer orders del response
        orders = api_response.get('data', []) if isinstance(api_response, dict) else api_response
        
        if not orders:
            print("❌ No se encontraron orders en la respuesta")
            print(f"   Respuesta completa: {api_response}")
            return False
        
        print(f"✅ Se obtuvieron {len(orders)} orders de la API")
        print(f"\n📊 Ejemplo de orden (primera):")
        print(f"   Order ID: {orders[0].get('order_id')}")
        print(f"   Status: {orders[0].get('status')}")
        print(f"   Total: {orders[0].get('total')} {orders[0].get('currency')}")
        
        # Paso 2: Transformar datos a formato Silver
        print("\n🔄 PASO 2: Transformar datos a formato Silver")
        print("-" * 80)
        
        transformed_orders = []
        for order in orders:
            try:
                transformed = transform_order_to_silver(order)
                transformed_orders.append(transformed)
            except Exception as e:
                print(f"⚠️  Error transformando orden {order.get('order_id')}: {e}")
                continue
        
        print(f"✅ Se transformaron {len(transformed_orders)} orders")
        
        if not transformed_orders:
            print("❌ No se pudieron transformar las orders")
            return False
        
        # Paso 3: Crear SparkSession
        print("\n⚡ PASO 3: Crear SparkSession")
        print("-" * 80)
        
        spark = get_spark_session()
        print("✅ SparkSession creado exitosamente")
        
        # Paso 4: Crear tabla Iceberg
        print("\n🗄️  PASO 4: Crear tabla Iceberg")
        print("-" * 80)
        
        table_name = "test_db.janis_orders_silver"
        schema = create_orders_silver_schema()
        
        iceberg_manager = IcebergTableManager(spark, catalog_name="local")
        
        if not iceberg_manager.table_exists(table_name):
            iceberg_manager.create_table(
                table_name=table_name,
                schema=schema,
                partition_spec={}  # Sin particiones para test
            )
            print(f"✅ Tabla Iceberg creada: {table_name}")
        else:
            print(f"ℹ️  Tabla ya existe: {table_name}")
        
        # Paso 5: Escribir datos a Iceberg
        print("\n💾 PASO 5: Escribir datos a Iceberg")
        print("-" * 80)
        
        # Crear DataFrame
        df = spark.createDataFrame(transformed_orders, schema=schema)
        print(f"   DataFrame creado con {df.count()} registros")
        
        # Escribir a Iceberg
        iceberg_writer = IcebergWriter(spark, catalog_name="local")
        iceberg_writer.write_to_iceberg(df, table_name, mode="overwrite")
        
        print(f"✅ Datos escritos a tabla Iceberg")
        
        # Paso 6: Leer y validar datos
        print("\n📖 PASO 6: Leer y validar datos desde Iceberg")
        print("-" * 80)
        
        # Leer datos
        result_df = spark.table(f"local.{table_name}")
        result_count = result_df.count()
        
        print(f"✅ Se leyeron {result_count} registros desde Iceberg")
        
        # Validar conteo
        if result_count != len(transformed_orders):
            print(f"❌ Error: Conteo no coincide")
            print(f"   Esperado: {len(transformed_orders)}")
            print(f"   Obtenido: {result_count}")
            return False
        
        # Mostrar muestra de datos
        print("\n📊 Muestra de datos leídos:")
        result_df.select("order_id", "status", "total", "currency", "date_created").show(5, truncate=False)
        
        # Paso 7: Validar integridad de datos
        print("\n✅ PASO 7: Validar integridad de datos")
        print("-" * 80)
        
        # Obtener IDs originales y leídos
        original_ids = set([o['order_id'] for o in transformed_orders])
        read_ids = set([row.order_id for row in result_df.collect()])
        
        if original_ids == read_ids:
            print(f"✅ Todos los order_ids coinciden ({len(original_ids)} registros)")
        else:
            print(f"❌ Error: IDs no coinciden")
            print(f"   Faltantes: {original_ids - read_ids}")
            print(f"   Extras: {read_ids - original_ids}")
            return False
        
        # Validar campos específicos
        sample_row = result_df.first()
        print(f"\n📋 Validación de campos (primer registro):")
        print(f"   Order ID: {sample_row.order_id}")
        print(f"   Status: {sample_row.status}")
        print(f"   Total: {sample_row.total}")
        print(f"   Date Created: {sample_row.date_created}")
        print(f"   Source Type: {sample_row.source_type}")
        print(f"   Ingestion Timestamp: {sample_row.ingestion_timestamp}")
        
        # Resumen final
        print("\n" + "=" * 80)
        print("🎉 TEST DE INTEGRACIÓN COMPLETADO EXITOSAMENTE")
        print("=" * 80)
        print(f"\n📊 Resumen:")
        print(f"   ✅ Orders obtenidas de API: {len(orders)}")
        print(f"   ✅ Orders transformadas: {len(transformed_orders)}")
        print(f"   ✅ Orders escritas a Iceberg: {len(transformed_orders)}")
        print(f"   ✅ Orders leídas desde Iceberg: {result_count}")
        print(f"   ✅ Integridad de datos: VERIFICADA")
        print(f"\n🗄️  Tabla Iceberg: {table_name}")
        print(f"📁 Ubicación: ./test-warehouse-janis/")
        
        return True
    
    except Exception as e:
        print(f"\n❌ ERROR EN TEST DE INTEGRACIÓN:")
        print(f"   {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # Cerrar Spark session
        if 'spark' in locals():
            spark.stop()
            print("\n🔌 SparkSession cerrado")


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
