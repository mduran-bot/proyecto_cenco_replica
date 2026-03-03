# Max - Proyecto de Integración Janis-Cencosud

Este directorio contiene todos los componentes del proyecto de integración entre Janis Commerce y Cencosud.

## Estructura de Carpetas

```
max/
├── glue/           # ETL Pipeline (Bronze → Silver → Gold)
├── polling/        # Sistema de polling de APIs de Janis
├── api/            # Definiciones de APIs de Janis (JSON schemas)
└── terraform/      # Infraestructura como código (LocalStack)
```

## Componentes

### 📊 glue/
Contiene todo el código relacionado con el pipeline ETL de transformación de datos:

- **src/**: Código fuente del pipeline
  - `config/`: Archivos de configuración (field_mappings.json, redshift_schemas.json, etc.)
  - `modules/`: Módulos de transformación (data_cleaner, json_flattener, etc.)
  - `etl-silver-to-gold/`: Pipeline Silver → Gold con módulos especializados
- **scripts/**: Scripts de ejecución y validación
  - `run_bronze_to_silver_all.py`: Ejecuta Bronze→Silver para todas las entidades
  - `run_silver_to_gold_all.py`: Ejecuta Silver→Gold para todas las tablas
  - `validate_*.py`: Scripts de validación
- **tests/**: Tests unitarios y de integración
  - `fixtures/`: Datos de prueba
- **output/**: Resultados de ejecuciones locales

**Pipeline ETL:**
```
Bronze (JSON raw) → Silver (limpio/normalizado) → Gold (agregado/analítico)
```

### 🔄 polling/
Sistema de polling periódico de las APIs de Janis usando Apache Airflow (MWAA):

- **dags/**: DAGs de Airflow para polling de diferentes entidades
- **src/**: Código fuente del sistema de polling
- **config/**: Configuración de endpoints y credenciales
- **tests/**: Tests del sistema de polling
- **terraform/**: Infraestructura específica de polling

### 📡 api/
Definiciones de las 41 APIs de Janis Commerce en formato JSON:

- Esquemas de endpoints
- Estructuras de datos
- Documentación de campos

### 🏗️ terraform/
Infraestructura como código para despliegue en LocalStack y AWS:

- Configuración de servicios AWS
- Networking y seguridad
- Recursos de datos

## Inicio Rápido

### ETL Pipeline (glue/)

```bash
cd max/glue

# Ejecutar Bronze → Silver para una entidad
python run_pipeline_to_silver.py --entity-type orders --client metro

# Ejecutar Silver → Gold para una tabla
cd src/etl-silver-to-gold
python run_pipeline_to_gold.py --gold-table wms_orders --client metro

# Ejecutar todo el pipeline
cd ../../scripts
python run_bronze_to_silver_all.py
python run_silver_to_gold_all.py
```

### Sistema de Polling

```bash
cd max/polling

# Ver documentación específica
cat README.md
```

## Documentación Adicional

- **glue/GUIA_SCRIPTS_PIPELINE.md**: Guía detallada de scripts ETL
- **glue/INICIO_RAPIDO.md**: Inicio rápido del pipeline ETL
- **polling/README.md**: Documentación del sistema de polling
- **.kiro/specs/etl-41-apis-expansion/**: Especificaciones del proyecto

## Requisitos

- Python 3.11+
- PySpark 3.5+
- LocalStack (para desarrollo local)
- Docker (para LocalStack)

Ver `glue/requirements.txt` y `polling/requirements.txt` para dependencias específicas.
