# Herramienta de Análisis de Esquemas Parquet

**Script**: `scripts/analyze_parquet_schemas.py`  
**Fecha de Creación**: 17 de Febrero de 2026  
**Propósito**: Analizar archivos Parquet de S3 Gold para validar esquemas, tipos de datos y estructura

---

## Resumen Ejecutivo

Esta herramienta Python analiza archivos Parquet locales y genera reportes detallados sobre su estructura, esquema, tipos de datos, estadísticas y calidad de datos. Es esencial para:

- Validar que los archivos Parquet generados cumplan con los requisitos de S3 Gold
- Verificar compatibilidad de esquemas con Redshift
- Identificar problemas de calidad de datos (valores nulos, tipos incorrectos)
- Documentar la estructura de archivos existentes en producción

---

## Características Principales

### 1. Análisis de Esquema
- Lista todas las columnas con sus tipos de datos Arrow/Parquet
- Indica si cada campo es nullable o not null
- Muestra el número total de columnas

### 2. Metadata del Archivo
- Número de row groups (importante para performance)
- Número total de filas
- Número de columnas
- Información de compresión

### 3. Vista de Datos
- Muestra las primeras 3 filas del archivo
- Permite verificar formato y contenido real de los datos

### 4. Estadísticas Descriptivas
- Estadísticas completas para todas las columnas (count, mean, std, min, max, percentiles)
- Incluye columnas numéricas y categóricas

### 5. Análisis de Calidad de Datos
- Identifica columnas con valores nulos
- Calcula porcentaje de nulos por columna
- Ayuda a identificar problemas de completitud de datos

### 6. Tipos de Datos Python
- Muestra cómo Pandas interpreta cada columna
- Útil para validar conversiones de tipos

### 7. Resumen JSON
- Genera archivo JSON con resumen estructurado
- Facilita procesamiento automatizado y comparaciones

---

## Requisitos

### Dependencias Python

```bash
pip install pyarrow pandas
```

**Versiones recomendadas:**
- `pyarrow >= 12.0.0`
- `pandas >= 2.0.0`

### Estructura de Directorios

El script espera encontrar archivos Parquet en:
```
./parquet_samples/
├── archivo1.parquet
├── archivo2.parquet
└── ...
```

---

## Uso

### Uso Básico

```bash
# Desde la raíz del proyecto
python scripts/analyze_parquet_schemas.py
```

### Preparación de Archivos

1. **Crear directorio de muestras:**
```bash
mkdir -p parquet_samples
```

2. **Copiar archivos Parquet desde S3:**
```bash
# Ejemplo: Descargar muestras de S3 Gold
aws s3 cp s3://cencosud.test.super.peru.analytics/ExternalAccess/milocal_smk_pe/automatico/vw_milocal_centro/year=2024/month=07/day=10/part-00000-*.parquet ./parquet_samples/milocal_centro.parquet

aws s3 cp s3://cencosud.test.super.peru.analytics/ExternalAccess/milocal_smk_pe/automatico/vw_milocal_material/year=2024/month=07/day=10/part-00000-*.parquet ./parquet_samples/milocal_material.parquet
```

3. **Ejecutar análisis:**
```bash
python scripts/analyze_parquet_schemas.py
```

---

## Salida del Script

### Salida en Consola

Para cada archivo Parquet, el script imprime:

```
================================================================================
Analizando: milocal_centro.parquet
================================================================================

SCHEMA:
--------------------------------------------------------------------------------
  1. centro_id                              STRING                        NOT NULL
  2. centro_nombre                          STRING                        NOT NULL
  3. region                                 STRING                        NULL
  4. ciudad                                 STRING                        NULL
  5. direccion                              STRING                        NULL
...

Total columnas: 15

METADATA:
--------------------------------------------------------------------------------
Número de row groups: 1
Número de filas: 50
Número de columnas: 15

PRIMERAS 3 FILAS:
--------------------------------------------------------------------------------
  centro_id  centro_nombre    region  ...
0  CENT-001   Lima Centro     Lima    ...
1  CENT-002   Miraflores      Lima    ...
2  CENT-003   San Isidro      Lima    ...

ESTADÍSTICAS:
--------------------------------------------------------------------------------
       centro_id  centro_nombre  ...
count         50             50  ...
unique        50             50  ...
top    CENT-001   Lima Centro   ...
...

VALORES NULOS POR COLUMNA:
--------------------------------------------------------------------------------
region                                  :      5 ( 10.00%)
telefono                                :     12 ( 24.00%)

TIPOS DE DATOS PYTHON:
--------------------------------------------------------------------------------
centro_id                               : object
centro_nombre                           : object
region                                  : object
...
```

### Archivo JSON de Resumen

**Ubicación**: `./parquet_samples/schema_analysis_summary.json`

**Contenido**:
```json
[
  {
    "file": "milocal_centro.parquet",
    "num_columns": 15,
    "num_rows": 50,
    "schema": [
      ["centro_id", "string", false],
      ["centro_nombre", "string", false],
      ["region", "string", true],
      ["ciudad", "string", true],
      ...
    ]
  },
  {
    "file": "milocal_material.parquet",
    "num_columns": 25,
    "num_rows": 1000,
    "schema": [...]
  }
]
```

---

## Casos de Uso

### 1. Validar Archivos Generados por Glue

**Escenario**: Verificar que los archivos Parquet generados por jobs de Glue tienen el esquema correcto.

**Proceso**:
```bash
# 1. Descargar muestra de S3 Gold
aws s3 cp s3://cencosud.test.super.peru.analytics/ExternalAccess/janis_smk_pe/automatico/orders/year=2026/month=02/day=17/part-00000-*.parquet ./parquet_samples/orders_sample.parquet

# 2. Analizar
python scripts/analyze_parquet_schemas.py

# 3. Verificar:
# - Tipos de datos coinciden con matriz de mapeo
# - Campos nullable/not null correctos
# - No hay valores nulos en campos requeridos
```

### 2. Comparar Esquemas Entre Ambientes

**Escenario**: Asegurar que dev, staging y prod tienen esquemas consistentes.

**Proceso**:
```bash
# Descargar muestras de cada ambiente
aws s3 cp s3://cencosud-dev.../orders/... ./parquet_samples/orders_dev.parquet
aws s3 cp s3://cencosud-staging.../orders/... ./parquet_samples/orders_staging.parquet
aws s3 cp s3://cencosud-prod.../orders/... ./parquet_samples/orders_prod.parquet

# Analizar todos
python scripts/analyze_parquet_schemas.py

# Comparar schema_analysis_summary.json entre archivos
```

### 3. Documentar Estructura de Archivos Existentes

**Escenario**: Documentar la estructura de archivos Parquet existentes en S3 Gold de producción.

**Proceso**:
```bash
# Descargar muestras de todas las tablas existentes
aws s3 cp s3://.../milocal_smk_pe/automatico/vw_milocal_centro/... ./parquet_samples/
aws s3 cp s3://.../milocal_smk_pe/automatico/vw_milocal_material/... ./parquet_samples/

# Analizar
python scripts/analyze_parquet_schemas.py

# Usar salida para actualizar documentación
```

### 4. Identificar Problemas de Calidad de Datos

**Escenario**: Detectar columnas con muchos valores nulos o tipos de datos incorrectos.

**Proceso**:
```bash
# Analizar archivo sospechoso
python scripts/analyze_parquet_schemas.py

# Revisar sección "VALORES NULOS POR COLUMNA"
# Si una columna NOT NULL tiene nulos, hay un problema en la transformación
```

### 5. Validar Compatibilidad con Redshift

**Escenario**: Verificar que los tipos de datos Parquet son compatibles con Redshift.

**Proceso**:
```bash
# Analizar archivo
python scripts/analyze_parquet_schemas.py

# Comparar tipos de datos con matriz de mapeo:
# - STRING → VARCHAR
# - INT64 → BIGINT
# - DECIMAL(p,s) → NUMERIC(p,s)
# - TIMESTAMP → TIMESTAMP
# - BOOLEAN → SMALLINT (en Redshift)
```

---

## Interpretación de Resultados

### Tipos de Datos Arrow/Parquet

| Tipo Arrow | Tipo Redshift | Notas |
|------------|---------------|-------|
| `string` | `VARCHAR(n)` | Verificar longitud máxima |
| `int64` | `BIGINT` | Para IDs y contadores |
| `decimal128(p,s)` | `NUMERIC(p,s)` | Preservar precisión |
| `bool` | `SMALLINT` | Convertir a 0/1 |
| `timestamp[us, tz=UTC]` | `TIMESTAMP` | Debe ser UTC |
| `null` | `NULL` | Verificar nullability |

### Indicadores de Problemas

**🚨 Problemas Críticos:**
- Columna NOT NULL con valores nulos
- Tipos de datos incorrectos (ej: string donde debería ser int64)
- Número de columnas diferente al esperado

**⚠️ Advertencias:**
- Más del 50% de valores nulos en columna nullable
- Tipos de datos Python inesperados (ej: object en lugar de int64)
- Número de row groups muy alto (>100) o muy bajo (1 para archivos grandes)

**✅ Indicadores Saludables:**
- Tipos de datos coinciden con matriz de mapeo
- Valores nulos solo en columnas nullable
- Número apropiado de row groups (1-10 para archivos de 64-128 MB)

---

## Troubleshooting

### Error: "ModuleNotFoundError: No module named 'pyarrow'"

**Solución:**
```bash
pip install pyarrow pandas
```

### Error: "Directorio parquet_samples no existe"

**Solución:**
```bash
mkdir -p parquet_samples
# Copiar archivos Parquet al directorio
```

### Error: "No se encontraron archivos .parquet"

**Solución:**
```bash
# Verificar que hay archivos .parquet en el directorio
ls -la parquet_samples/

# Copiar archivos desde S3
aws s3 cp s3://bucket/path/file.parquet ./parquet_samples/
```

### Error al leer archivo Parquet

**Posibles causas:**
- Archivo corrupto
- Formato no es Parquet válido
- Versión de pyarrow incompatible

**Solución:**
```bash
# Verificar que es un archivo Parquet válido
file parquet_samples/archivo.parquet

# Intentar con versión más reciente de pyarrow
pip install --upgrade pyarrow
```

### Valores nulos inesperados

**Diagnóstico:**
1. Verificar si la columna debería ser nullable según matriz de mapeo
2. Revisar transformación en Glue job que genera el archivo
3. Verificar datos fuente en capa Bronze/Silver

**Solución:**
- Si columna debe ser NOT NULL: Corregir transformación para manejar nulos
- Si columna debe ser nullable: Actualizar documentación

---

## Integración con Pipeline

### En Jobs de Glue

Después de generar archivos Parquet, validar con este script:

```python
# En Glue job (Python Shell)
import subprocess
import boto3

# Descargar muestra del archivo generado
s3 = boto3.client('s3')
s3.download_file(
    'cencosud.test.super.peru.analytics',
    'ExternalAccess/janis_smk_pe/automatico/orders/year=2026/month=02/day=17/part-00000-abc123.parquet',
    '/tmp/sample.parquet'
)

# Analizar con pyarrow
import pyarrow.parquet as pq
parquet_file = pq.ParquetFile('/tmp/sample.parquet')
schema = parquet_file.schema_arrow

# Validar esquema esperado
expected_columns = ['order_id', 'order_number', 'status', ...]
actual_columns = [field.name for field in schema]

assert set(expected_columns) == set(actual_columns), "Schema mismatch!"
```

### En CI/CD Pipeline

```yaml
# .github/workflows/validate-parquet.yml
name: Validate Parquet Files

on:
  push:
    paths:
      - 'glue/**'

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Setup Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install pyarrow pandas boto3
      
      - name: Download sample files
        run: |
          mkdir -p parquet_samples
          aws s3 cp s3://bucket/path/ ./parquet_samples/ --recursive
      
      - name: Analyze schemas
        run: |
          python scripts/analyze_parquet_schemas.py
      
      - name: Validate schemas
        run: |
          python scripts/validate_schemas.py  # Script adicional para validación
```

---

## Mejoras Futuras

### Funcionalidades Planeadas

1. **Validación Automática de Esquemas**
   - Comparar contra esquema esperado definido en JSON
   - Generar reporte de diferencias
   - Exit code no-cero si hay discrepancias

2. **Análisis de Performance**
   - Tamaño de archivo vs número de filas
   - Ratio de compresión
   - Número óptimo de row groups

3. **Comparación de Archivos**
   - Comparar esquemas entre dos archivos
   - Detectar cambios de esquema (schema evolution)
   - Validar compatibilidad backward/forward

4. **Integración con S3**
   - Descargar archivos directamente desde S3
   - Analizar múltiples particiones
   - Generar reporte agregado

5. **Validación de Datos**
   - Verificar constraints (ej: valores en rango esperado)
   - Validar foreign keys
   - Detectar duplicados

---

## Archivos Relacionados

### Documentación
- [Matriz Mapeo API Janis a S3 Gold](./Matriz%20Mapeo%20API%20Janis%20a%20S3%20Gold.md) - Esquemas esperados
- [Análisis Estructura S3 Gold Producción](./Análisis%20Estructura%20S3%20Gold%20Producción.md) - Formato de archivos
- [Plan de Adaptación a Estructura Gold Existente](./Plan%20de%20Adaptación%20a%20Estructura%20Gold%20Existente.md) - Requisitos de compatibilidad

### Código
- `glue/modules/data_type_converter.py` - Conversiones de tipos de datos
- `glue/modules/data_normalizer.py` - Normalización de datos
- `terraform/modules/glue/` - Configuración de jobs de Glue

---

## Ejemplo Completo de Uso

### Escenario: Validar Archivos de Orders Generados

```bash
# 1. Preparar ambiente
mkdir -p parquet_samples
cd parquet_samples

# 2. Descargar muestra de producción (referencia)
aws s3 cp \
  s3://cencosud.test.super.peru.analytics/ExternalAccess/milocal_smk_pe/automatico/vw_milocal_centro/year=2024/month=07/day=10/part-00000-5a8af952-c799-46c8-855e-0f969f6c7694.c000.snappy.parquet \
  ./reference_sample.parquet

# 3. Descargar archivo generado por nuestro pipeline
aws s3 cp \
  s3://cencosud.test.super.peru.analytics/ExternalAccess/janis_smk_pe/automatico/orders/year=2026/month=02/day=17/part-00000-abc123.c000.snappy.parquet \
  ./orders_generated.parquet

# 4. Volver a raíz del proyecto
cd ..

# 5. Analizar ambos archivos
python scripts/analyze_parquet_schemas.py

# 6. Revisar salida
cat parquet_samples/schema_analysis_summary.json

# 7. Comparar esquemas manualmente o con jq
jq '.[0].schema' parquet_samples/schema_analysis_summary.json > reference_schema.json
jq '.[1].schema' parquet_samples/schema_analysis_summary.json > generated_schema.json
diff reference_schema.json generated_schema.json
```

---

## Conclusión

Esta herramienta es esencial para:
- ✅ Validar archivos Parquet generados por el pipeline
- ✅ Asegurar compatibilidad con Redshift
- ✅ Identificar problemas de calidad de datos tempranamente
- ✅ Documentar estructura de archivos existentes
- ✅ Facilitar troubleshooting de problemas de esquema

**Recomendación**: Ejecutar este script después de cada cambio en transformaciones de Glue para validar que los archivos generados mantienen el esquema correcto.

---

**Documento Generado**: 17 de Febrero de 2026  
**Versión**: 1.0  
**Estado**: ✅ Completo - Listo para Uso  
**Mantenedor**: Equipo de Data Engineering - Janis-Cencosud
