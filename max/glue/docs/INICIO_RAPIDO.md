# Inicio Rápido - Pipeline Bronze-to-Silver de Max

**Fecha:** 18 de Febrero, 2026  
**Objetivo:** Ejecutar el pipeline completo en LocalStack

---

## Prerequisitos

### 1. Docker Desktop
- ✅ Docker instalado (versión 29.1.3)
- ⏳ **ACCIÓN REQUERIDA:** Iniciar Docker Desktop manualmente
  - Buscar "Docker Desktop" en el menú de Windows
  - Hacer clic para iniciar
  - Esperar a que el ícono de Docker en la bandeja del sistema esté verde

### 2. Python y Dependencias
```bash
# Verificar Python
python --version  # Debe ser 3.11+

# Instalar dependencias
cd max
pip install -r requirements.txt
```

### 3. Java (para PySpark)
```bash
# Verificar Java
java -version  # Debe ser 11+
```

---

## Paso 1: Iniciar Docker Desktop

**IMPORTANTE:** Antes de continuar, asegúrate de que Docker Desktop esté corriendo.

**Verificar:**
```bash
docker ps
```

Si ves una lista de contenedores (puede estar vacía), Docker está corriendo. ✅  
Si ves un error, Docker no está corriendo. ❌

---

## Paso 2: Iniciar LocalStack

LocalStack simula servicios de AWS localmente (S3, IAM)

### Configuración Actual

El archivo `docker-compose.yml` en la raíz del proyecto ya está configurado con:

```yaml
version: '3.8'

services:
  localstack:
    container_name: localstack-janis-cencosud
    image: localstack/localstack:latest
    ports:
      - "4566:4566"
    environment:
      - SERVICES=s3,iam
      - DEBUG=1
      - AWS_DEFAULT_REGION=us-east-1
      - AWS_ACCESS_KEY_ID=test
      - AWS_SECRET_ACCESS_KEY=test
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:4566/_localstack/health"]
      interval: 10s
      timeout: 5s
      retries: 5
      start_period: 30s
```

### Iniciar LocalStack

```bash
# Desde la raíz del proyecto
docker-compose up -d
```

**Verificar:**
```bash
docker ps
# Deberías ver un contenedor "localstack-janis-cencosud" corriendo
```

---

## Paso 3: Crear Buckets S3 con Terraform

```bash
cd max/terraform

# Inicializar Terraform
terraform init

# Crear buckets
terraform apply -auto-approve
```

**Verificar buckets creados:**
```bash
aws --endpoint-url=http://localhost:4566 s3 ls
```

**Deberías ver:**
```
data-lake-bronze
data-lake-silver
glue-scripts-bin
```

---

## Paso 4: Subir Datos de Prueba

```bash
# Desde la carpeta max/
aws --endpoint-url=http://localhost:4566 s3 cp \
  tests/fixtures/sample_ventas_lines.json \
  s3://data-lake-bronze/ventas/sample_ventas_lines.json
```

**Verificar:**
```bash
aws --endpoint-url=http://localhost:4566 s3 ls s3://data-lake-bronze/ventas/
```

---

## Paso 5: Ejecutar Pipeline

```bash
# Desde la carpeta max/
python run_pipeline_to_silver.py
```

**Salida esperada:**
```
================================================================================
EJECUTANDO PIPELINE COMPLETO BRONZE-TO-SILVER (MODO LOCAL)
================================================================================
Input Path: s3a://data-lake-bronze/ventas/sample_ventas_lines.json
Output Path: s3a://data-lake-silver/ventas_procesadas (JSON)

Inicializando Spark session...
Spark session inicializada correctamente

================================================================================
EJECUTANDO TRANSFORMACIONES
================================================================================

1. Leyendo datos de Bronze...
   Registros leídos: 12

2. Ejecutando JSONFlattener...
   Resultado: 15 registros

3. Ejecutando DataCleaner...
   Resultado: 15 registros

4. Ejecutando DataNormalizer...
   Resultado: 15 registros

5. Ejecutando DataTypeConverter...
   Resultado: 15 registros

6. Ejecutando DuplicateDetector...
   Resultado: 15 registros

7. Ejecutando ConflictResolver...
   Resultado: 11 registros

8. Ejecutando DataGapHandler...
   Resultado: 11 registros

================================================================================
TRANSFORMACIONES COMPLETADAS
================================================================================

Escribiendo 11 registros a s3a://data-lake-silver/ventas_procesadas...
Datos escritos exitosamente en formato JSON

================================================================================
RESUMEN
================================================================================
✅ Bronze → Silver: 12 → 11 registros
✅ Datos guardados en: s3a://data-lake-silver/ventas_procesadas
✅ Resumen CSV en: output/silver/ventas_procesadas_summary.csv
```

---

## Paso 6: Verificar Resultados

### Ver datos en S3 Silver
```bash
aws --endpoint-url=http://localhost:4566 s3 ls s3://data-lake-silver/ventas_procesadas/ --recursive
```

### Ver resumen local
```bash
# El pipeline también guarda un CSV local para fácil inspección
cat output/silver/ventas_procesadas_summary.csv
```

---

## Troubleshooting

### Error: "Cannot connect to Docker"
**Solución:** Iniciar Docker Desktop y esperar a que esté completamente iniciado.

### Error: "Bucket does not exist"
**Solución:** Ejecutar `terraform apply` en `max/terraform/`

### Error: "File not found: sample_ventas_lines.json"
**Solución:** Verificar que el archivo existe en `max/tests/fixtures/`

### Error: "Java not found"
**Solución:** Instalar Java 11+ y configurar JAVA_HOME

### Error: "HADOOP_HOME not set" (Windows)
**Solución:** 
1. Descargar winutils: https://github.com/cdarlint/winutils
2. Extraer a `C:\hadoop\bin\`
3. Configurar: `$env:HADOOP_HOME = "C:\hadoop"`

### Error: "Address already in use" o problemas de red en Spark
**Solución:** El script ya incluye configuraciones de red para Windows:
- `spark.driver.host = localhost`
- `spark.driver.bindAddress = 127.0.0.1`
Estas configuraciones evitan conflictos de red en entornos Windows

---

## Limpieza

### Detener LocalStack
```bash
docker-compose down
```

### Reiniciar LocalStack
```bash
docker-compose restart
```

### Limpiar datos locales
```bash
rm -rf max/output/
```

---

## Próximos Pasos

Una vez que el pipeline funcione correctamente:

1. ✅ Documentar resultados en `Documentacion/RESULTADOS_PRUEBA_MAX.md`
2. ✅ Comparar esquema de salida con requirements
3. ✅ Comenzar integración con módulos de Vicente
4. ✅ Agregar property-based tests

---

## Comandos Útiles

```bash
# Ver logs de LocalStack
docker logs localstack -f

# Listar todos los buckets
aws --endpoint-url=http://localhost:4566 s3 ls

# Ver contenido de un bucket
aws --endpoint-url=http://localhost:4566 s3 ls s3://data-lake-bronze --recursive

# Descargar archivo de S3
aws --endpoint-url=http://localhost:4566 s3 cp \
  s3://data-lake-silver/ventas_procesadas/part-00000-xxx.json \
  resultado.json

# Reiniciar LocalStack
docker restart localstack
```

---

**¡Listo para empezar!** 🚀

Una vez que Docker Desktop esté corriendo, ejecuta los pasos en orden y el pipeline debería funcionar sin problemas.
