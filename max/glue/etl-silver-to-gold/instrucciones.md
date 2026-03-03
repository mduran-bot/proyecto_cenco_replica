#  Guía de Operación: Pipeline Cenco-Janis

Este documento detalla los pasos secuenciales para inicializar la infraestructura, cargar datos crudos y ejecutar el procesamiento hasta la capa Gold.

---

## Paso 1: Inicialización de Infraestructura
Antes de procesar, debemos crear los contenedores (buckets) en LocalStack utilizando Terraform.

1. **Levantar LocalStack**:
    ```bash
    docker-compose up -d
    ```

2. **Aplicar Terraform**:
    ```bash
    cd terraform/
    terraform init
    terraform apply -auto-approve
    ```
    *Esto creará los buckets: `data-lake-bronze`, `data-lake-silver`, `data-lake-gold` y `data-lake-dlq`.*

---

## Paso 2: Carga Inicial a Capa Bronze

Simularemos la extracción de las vistas de Janis cargando un archivo JSON crudo al área de aterrizaje:

```bash
aws --endpoint-url=http://localhost:4566 s3 cp   tests/fixtures/sample_ventas_lines.json   s3://data-lake-bronze/ventas/sample_ventas_lines.json
```

---

## Paso 3: Ejecución del Pipeline Bronze → Silver

Ejecutamos el script encargado de transformar los datos desde la capa Bronze a Silver:

```bash
python run_pipeline_to_silver.py
```

---

##  Paso 4: Ejecución del Pipeline Silver → Gold

Ingresamos al módulo correspondiente y ejecutamos el proceso que lleva los datos desde Silver hacia la capa Gold:

```bash
cd src/etl-silver-to-gold/

python run_pipeline_to_gold.py
```

---

##  Paso 5: Comprobación de Datos

| Capa   | Comando de Verificación |
|--------|--------------------------|
| Bronze | `aws --endpoint-url=http://localhost:4566 s3 ls s3://data-lake-bronze/ventas/` |
| Silver | `aws --endpoint-url=http://localhost:4566 s3 ls s3://data-lake-silver/ventas_procesadas/` |
| Gold   | `aws --endpoint-url=http://localhost:4566 s3 ls s3://data-lake-gold/ventas_agregadas/` |

