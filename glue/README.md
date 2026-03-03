# Glue ETL Jobs - Data Transformation Pipeline

Este directorio contiene los trabajos de AWS Glue para el pipeline de transformación de datos Bronze → Silver → Gold.

## 🚀 Quick Start - Desarrollo Local

**No necesitas AWS ni Terraform para desarrollar y probar!**

```bash
# 1. Instalar dependencias
pip install -r requirements.txt

# 2. Iniciar LocalStack
docker-compose -f ../docker-compose.localstack.yml up -d

# 3. Setup ambiente local
python local_setup.py

# 4. Ejecutar tests
python run_tests_local.py
```

📖 **Guía completa**: Ver [LOCAL_DEVELOPMENT.md](LOCAL_DEVELOPMENT.md)

## 📁 Estructura del Proyecto

```
glue/
├── jobs/                          # Glue jobs principales
│   ├── bronze_to_silver_job.py   # Job Bronze → Silver
│   └── silver_to_gold_job.py     # Job Silver → Gold
├── modules/                       # Módulos reutilizables
│   ├── iceberg_manager.py        # ✅ Gestión de tablas Iceberg
│   ├── iceberg_writer.py         # ✅ Escritura con ACID
│   ├── data_type_converter.py    # Conversión de tipos MySQL→Redshift
│   ├── data_normalizer.py        # Normalización de formatos
│   ├── data_gap_handler.py       # Manejo de campos faltantes
│   └── schema_evolution.py       # Evolución de esquemas (próximo)
├── tests/                         # Tests
│   ├── property/                  # ✅ Property-based tests (Hypothesis)
│   │   ├── test_iceberg_roundtrip.py
│   │   ├── test_iceberg_acid.py
│   │   └── test_iceberg_timetravel.py
│   └── unit/                      # Unit tests
├── schemas/                       # Definiciones de esquemas
│   ├── bronze_schemas.py
│   ├── silver_schemas.py         # ✅ Esquemas Silver layer
│   └── gold_schemas.py
├── local_setup.py                # ✅ Setup para desarrollo local
├── run_tests_local.py            # ✅ Ejecutor de tests local
├── requirements.txt              # ✅ Dependencias Python
├── pytest.ini                    # ✅ Configuración de pytest
└── LOCAL_DEVELOPMENT.md          # ✅ Guía de desarrollo local
```

## 🎯 Tareas Completadas

### Task 5: Iceberg Table Management ✅
- [x] 5.1 IcebergTableManager - Gestión completa de tablas
- [x] 5.2 IcebergWriter - Escritura con ACID transactions
- [x] 5.3 Property test: Write-Read Round Trip
- [x] 5.4 Property test: ACID Consistency
- [x] 5.5 Property test: Time Travel Snapshots

## 🧪 Testing

### Ejecutar Tests Localmente

```bash
# Todos los tests
python run_tests_local.py

# Test específico
python run_tests_local.py --test roundtrip
python run_tests_local.py --test acid
python run_tests_local.py --test timetravel

# Con pytest directamente
pytest tests/property/ -v --hypothesis-show-statistics
```

### Property-Based Testing

Usamos **Hypothesis** para generar casos de prueba automáticamente:

- **Property 5**: Iceberg Write-Read Round Trip
- **Property 11**: ACID Transaction Consistency
- **Property 12**: Time Travel Snapshot Access

Cada test ejecuta 100+ iteraciones con datos generados aleatoriamente.

## 🔧 Desarrollo Local vs AWS

| Aspecto | Local (LocalStack) | AWS Glue |
|---------|-------------------|----------|
| Spark | PySpark local | AWS Glue 4.0 |
| S3 | LocalStack S3 | Amazon S3 |
| Catalog | Local Hadoop | AWS Glue Data Catalog |
| Iceberg | Local warehouse | S3 warehouse |
| Costo | $0 | Pay per use |

**El código es idéntico** - lo que funciona localmente funciona en AWS.

## 📊 Arquitectura de Datos

### Bronze Layer (Raw Data)
- Datos sin procesar desde webhooks y polling
- Formato: JSON en S3
- Sin transformaciones

### Silver Layer (Clean Data)
- Datos limpios, normalizados y deduplicados
- Formato: Apache Iceberg (Parquet + Snappy)
- Transacciones ACID
- Particionado por fecha

### Gold Layer (Curated Data)
- Datos agregados y optimizados para BI
- Formato: Apache Iceberg
- Vistas materializadas
- Optimizado para Redshift

## 🔄 Workflow de Desarrollo

### 1. Desarrollo Local
```bash
# Desarrollar módulo
vim modules/my_module.py

# Probar localmente
python local_setup.py
python run_tests_local.py
```

### 2. Commit a GitHub
```bash
git add .
git commit -m "feat: implement new module"
git push origin main
```

### 3. Transferir a GitLab (desde otra máquina)
```bash
# Clonar desde GitHub
git clone https://github.com/vicemora97/Proyecto_Cenco.git

# Push a GitLab de Cencosud
git remote add gitlab https://gitlab.cencosud.com/your-repo.git
git push gitlab main
```

### 4. Deploy con Terraform (Cencosud)
Cencosud despliega desde GitLab usando Terraform.

## 🌐 Integración con API Janis

Puedes probar con datos reales de Janis localmente:

```python
from local_setup import create_local_spark_session
import requests

# Obtener datos de Janis
response = requests.get(
    "https://api.janis.com/orders",
    headers={"Authorization": "Bearer YOUR_TOKEN"}
)
orders = response.json()

# Procesar con Spark
spark = create_local_spark_session()
df = spark.createDataFrame(orders)

# Aplicar transformaciones
# ...

spark.stop()
```

## 📚 Recursos

- [Apache Iceberg Documentation](https://iceberg.apache.org/)
- [PySpark Documentation](https://spark.apache.org/docs/latest/api/python/)
- [Hypothesis Documentation](https://hypothesis.readthedocs.io/)
- [LocalStack Documentation](https://docs.localstack.cloud/)

## 🤝 Contribuir

1. Desarrollar localmente siguiendo [LOCAL_DEVELOPMENT.md](LOCAL_DEVELOPMENT.md)
2. Ejecutar todos los tests: `python run_tests_local.py`
3. Commit con mensaje descriptivo
4. Push a GitHub
5. Transferir a GitLab desde máquina con acceso

## ❓ Troubleshooting

Ver [LOCAL_DEVELOPMENT.md](LOCAL_DEVELOPMENT.md#troubleshooting) para soluciones comunes.

---

**Próximas tareas**: Task 11 (Schema Evolution Management)
