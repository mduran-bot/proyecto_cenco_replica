"""
Test básico de PySpark - Sin LocalStack

Este script verifica que PySpark funciona correctamente en tu máquina.
"""

from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, StringType, IntegerType
import time

print("=" * 60)
print("🧪 Test Básico de PySpark")
print("=" * 60)

# Crear Spark session (esto puede tomar 30-60 segundos la primera vez)
print("\n1️⃣ Creando Spark session (puede tomar un minuto)...")
start = time.time()

spark = SparkSession.builder \
    .appName("BasicTest") \
    .master("local[2]") \
    .config("spark.driver.memory", "1g") \
    .config("spark.ui.enabled", "false") \
    .getOrCreate()

spark.sparkContext.setLogLevel("ERROR")
print(f"✅ Spark session creada en {time.time() - start:.1f} segundos")

# Crear datos de prueba
print("\n2️⃣ Creando datos de prueba...")
data = [
    ("Alice", 25),
    ("Bob", 30),
    ("Charlie", 35)
]

schema = StructType([
    StructField("name", StringType(), False),
    StructField("age", IntegerType(), False)
])

df = spark.createDataFrame(data, schema)
print(f"✅ DataFrame creado con {df.count()} registros")

# Operaciones básicas
print("\n3️⃣ Operaciones básicas:")
avg_age = df.agg({'age': 'avg'}).collect()[0][0]
print(f"   - Edad promedio: {avg_age}")

filtered_count = df.filter(df.age > 25).count()
print(f"   - Registros con edad > 25: {filtered_count}")

# Cerrar Spark
spark.stop()

print("\n" + "=" * 60)
print("✅ ¡Test completado exitosamente!")
print("=" * 60)
print("\n🎉 PySpark está funcionando correctamente en tu máquina")
