# Guía de Desarrollo Local - Glue ETL Jobs

Esta guía te permite desarrollar y probar los jobs de Glue localmente sin necesidad de AWS o Terraform.

## Requisitos Previos

### 1. Instalar Python y dependencias

```bash
# Crear entorno virtual
python -m venv venv

# Activar entorno virtual
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt
```

### 2. Instalar Java (requerido por PySpark)

PySpark requiere Java 8 o 11:
- Windows: Descargar desde https://adoptium.net/
- Linux: `sudo apt install openjdk-11-jdk`
- Mac: `brew install openjdk@11`

### 3. Iniciar LocalStack

```bash
# Iniciar LocalStack con Docker
docker-compose -f docker-compose.localstack.yml up -d

# Verificar que está corriendo
curl http://localhost:4566/_localstack/health
```

## Flujo de Desarrollo Local

### Paso 1: Setup Inicial

```bash
cd glue

# Ejecutar setup local (crea Spark session y buckets S3)
python local_setup.py
```

**¿Qué hace `local_setup.py`?**

1. **Verifica LocalStack**: Comprueba que LocalStack esté corriendo en `http://localhost:4566`
2. **Crea Spark Session**: Configura PySpark con soporte para Apache Iceberg
3. **Configura Iceberg**: 
   - Catalog local tipo Hadoop
   - Warehouse en `./local-warehouse`
   - Integración con LocalStack S3
4. **Crea Buckets S3**: Crea buckets de prueba en LocalStack
   - `test-bronze` - Para datos raw
   - `test-silver` - Para datos limpios
   - `test-gold` - Para datos curados
5. **Ejecuta ETL de Ejemplo**: Demuestra el flujo completo:
   - Crea datos de muestra
   - Escribe a tabla Iceberg
   - Lee datos de vuelta
   - Valida round-trip

**Salida esperada:**
```
============================================================
🔧 Local Glue ETL Development Setup
============================================================
✅ LocalStack is running
✅ Local Spark session created: LocalGlueJob
📁 Warehouse location: ./local-warehouse
🔗 LocalStack endpoint: http://localhost:4566
✅ Created bucket: test-bronze
✅ Created bucket: test-silver
✅ Created bucket: test-gold

============================================================
🚀 Running sample ETL job...
✅ Local Spark session created: SampleETL
📁 Warehouse location: ./local-warehouse
🔗 LocalStack endpoint: http://localhost:4566

📊 Sample data:
+---+---------+-----+
| id|     name|price|
+---+---------+-----+
|  1|Product A| 10.5|
|  2|Product B|20.75|
|  3|Product C| 15.0|
+---+---------+-----+

💾 Writing to Iceberg table: local.test_db.sample_products

✅ Data read back from Iceberg:
+---+---------+-----+
| id|     name|price|
+---+---------+-----+
|  1|Product A| 10.5|
|  2|Product B|20.75|
|  3|Product C| 15.0|
+---+---------+-----+

🎉 Sample ETL completed successfully!
```

Esto creará:
- ✅ Spark session local con soporte Iceberg
- ✅ Buckets S3 en LocalStack (test-bronze, test-silver, test-gold)
- ✅ Warehouse local en `./local-warehouse`
- ✅ Tabla de ejemplo con datos de prueba

### Paso 2: Desarrollar Módulos

Edita los módulos en `glue/modules/`:
- `iceberg_manager.py` - Gestión de tablas Iceberg
- `iceberg_writer.py` - Escritura con ACID
- `data_type_converter.py` - Conversión de tipos
- etc.

### Paso 3: Ejecutar Tests

```bash
# Ejecutar todos los tests
python run_tests_local.py

# Ejecutar test específico
python run_tests_local.py --test roundtrip
python run_tests_local.py --test acid
python run_tests_local.py --test timetravel
```

### Paso 4: Probar con Datos Reales de Janis

Crea un script de prueba con datos de la API de Janis:

```python
# test_with_janis_data.py
from local_setup import create_local_spark_session
from modules.iceberg_manager import IcebergTableManager
from modules.iceberg_writer import IcebergWriter
import requests

# Obtener datos de Janis API
response = requests.get("https://api.janis.com/orders", headers={"Authorization": "Bearer YOUR_TOKEN"})
orders_data = response.json()

# Crear Spark session
spark = create_local_spark_session("JanisDataTest")

# Crear DataFrame
df = spark.createDataFrame(orders_data)

# Escribir a Iceberg
iceberg_manager = IcebergTableManager(spark, catalog_name="local")
iceberg_writer = IcebergWriter(spark, catalog_name="local")

# Crear tabla
iceberg_manager.create_table(
    table_name="test_db.janis_orders",
    schema=df.schema,
    partition_spec={"partition_by": ["year(date_created)"]}
)

# Escribir datos
iceberg_writer.write_to_iceberg(df, "test_db.janis_orders", mode="overwrite")

# Leer y verificar
result = spark.table("local.test_db.janis_orders")
result.show()

spark.stop()
```

## Estructura de Archivos Local

```
glue/
├── modules/              # Código de módulos ETL
├── tests/               # Tests
│   ├── property/        # Property-based tests
│   └── unit/           # Unit tests
├── schemas/            # Definiciones de esquemas
├── local-warehouse/    # Warehouse Iceberg local (generado)
├── local_setup.py      # Setup de ambiente local
├── run_tests_local.py  # Ejecutor de tests
└── requirements.txt    # Dependencias Python
```

## Debugging

### Ver logs de Spark

```python
spark.sparkContext.setLogLevel("INFO")  # o "DEBUG"
```

### Inspeccionar tablas Iceberg

```python
# Listar tablas
spark.sql("SHOW TABLES IN local.test_db").show()

# Ver esquema
spark.sql("DESCRIBE EXTENDED local.test_db.my_table").show(truncate=False)

# Ver snapshots
spark.sql("SELECT * FROM local.test_db.my_table.snapshots").show()
```

### Acceder a S3 en LocalStack

```bash
# Instalar AWS CLI
pip install awscli-local

# Listar buckets
awslocal s3 ls

# Ver contenido de bucket
awslocal s3 ls s3://test-bronze/
```

## Workflow Completo: Local → GitHub → GitLab

### 1. Desarrollo Local
```bash
# Desarrollar y probar localmente
python local_setup.py
python run_tests_local.py

# Hacer cambios en módulos
# ...

# Ejecutar tests nuevamente
python run_tests_local.py
```

### 2. Commit a GitHub
```bash
git add .
git commit -m "feat: implement new ETL module"
git push origin main
```

### 3. Transferir a GitLab (desde otra máquina)
```bash
# En la máquina con acceso a GitLab:

# Clonar desde GitHub
git clone https://github.com/vicemora97/Proyecto_Cenco.git

# Agregar remote de GitLab
git remote add gitlab https://gitlab.cencosud.com/your-repo.git

# Push a GitLab
git push gitlab main
```

## Ventajas de este Enfoque

✅ **No necesitas Terraform** - Todo corre localmente
✅ **No necesitas AWS** - LocalStack simula los servicios
✅ **Desarrollo rápido** - Ciclo de feedback inmediato
✅ **Tests confiables** - Property-based testing con Hypothesis
✅ **Datos reales** - Puedes usar la API de Janis directamente
✅ **Portabilidad** - El código funciona igual en AWS Glue

## Troubleshooting

### Error: "Java not found"
```bash
# Instalar Java 11
# Windows: Descargar de https://adoptium.net/
# Linux: sudo apt install openjdk-11-jdk
# Mac: brew install openjdk@11
```

### Error: "LocalStack not running"
```bash
# Iniciar LocalStack
docker-compose -f docker-compose.localstack.yml up -d

# Ver logs
docker logs localstack-janis-cencosud
```

### Error: "Module not found"
```bash
# Asegúrate de estar en el entorno virtual
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Reinstalar dependencias
pip install -r requirements.txt
```

## Próximos Pasos

1. ✅ Desarrollar módulos localmente
2. ✅ Ejecutar property tests
3. ✅ Probar con datos de Janis API
4. ✅ Commit a GitHub
5. ✅ Transferir a GitLab desde otra máquina
6. ✅ Cencosud despliega con Terraform desde GitLab

¡Listo para desarrollar! 🚀
