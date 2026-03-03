# Guía para Ejecutar Pruebas y Ver Transformaciones de Datos

Esta guía te muestra cómo ejecutar las pruebas del pipeline y ver cómo se transforman los datos en cada etapa: Bronze → Silver → Gold.

---

## Opción 1: Prueba Completa del Pipeline (Recomendada)

Esta prueba usa datos reales de la API de Janis y muestra todas las transformaciones.

### Paso 1: Ejecutar el script de prueba

```bash
cd glue
python scripts/test_full_pipeline_pandas.py
```

### Paso 2: Ver los resultados en consola

El script mostrará en tiempo real:
- ✅ Datos Bronze (JSON raw de la API)
- ✅ Datos Silver (JSON limpio y aplanado)
- ✅ Datos Gold (agregaciones y métricas)

### Paso 3: Ver los archivos generados

Los datos se guardan en `glue/data/`:

```bash
# Ver datos Bronze (raw)
cat glue/data/bronze_order_6913fcb6d134afc8da8ac3dd_pandas.json

# Ver datos Silver (limpio)
cat glue/data/silver_order_6913fcb6d134afc8da8ac3dd_pandas.json

# Ver datos Gold (agregado)
cat glue/data/gold_order_6913fcb6d134afc8da8ac3dd_pandas.json
```

---

## Opción 2: Prueba Solo Silver → Gold

Esta prueba usa datos sintéticos y se enfoca en las transformaciones Silver → Gold.

### Paso 1: Ejecutar el script

```bash
cd glue
python scripts/test_silver_to_gold_pandas.py
```

### Paso 2: Ver los archivos generados

```bash
# Ver datos Silver de prueba
cat glue/data/test_silver_pandas.json

# Ver datos Gold agregados
cat glue/data/test_gold_pandas.json
```

---

## Opción 3: Prueba Visual Mejorada (NUEVA)

Creamos un script especial que muestra los datos de forma más visual y detallada.

### Paso 1: Ejecutar el script visual

```bash
cd glue
python scripts/test_pipeline_visual.py
```

Este script:
- 📊 Muestra tablas formateadas en cada etapa
- 🔍 Resalta las transformaciones aplicadas
- 📈 Genera gráficos de las métricas (si tienes matplotlib)
- 💾 Guarda reportes HTML para ver en el navegador

### Paso 2: Ver el reporte HTML

Abre en tu navegador:
```
glue/data/pipeline_report.html
```

---

## Qué Ver en Cada Etapa

### 🟤 BRONZE (Datos Raw)
**Archivo**: `bronze_order_*.json`

**Qué buscar**:
- JSON anidado completo de la API
- Estructuras complejas (arrays, objetos anidados)
- Datos sin procesar

**Ejemplo**:
```json
{
  "id": "6913fcb6d134afc8da8ac3dd",
  "status": "readyForDelivery",
  "totalAmount": 23.95,
  "shipping": {
    "address": {
      "street": "Calle Principal 123"
    }
  }
}
```

### 🥈 SILVER (Datos Limpios)
**Archivo**: `silver_order_*.json`

**Qué buscar**:
- JSON aplanado (sin anidamiento)
- Columnas con prefijos (ej: `shipping_address_street`)
- Datos limpios y normalizados
- Tipos de datos correctos

**Ejemplo**:
```json
{
  "id": "6913fcb6d134afc8da8ac3dd",
  "status": "readyForDelivery",
  "totalAmount": 23.95,
  "shipping_address_street": "Calle Principal 123"
}
```

### 🥇 GOLD (Datos Agregados)
**Archivo**: `gold_order_*.json`

**Qué buscar**:
- Agregaciones por dimensiones (sucursal, estado)
- Métricas calculadas (sum, avg, min, max, count)
- Dimensiones de tiempo (year, month, day)
- Columnas de calidad (`_quality_valid`, `_quality_issues`)

**Ejemplo**:
```json
{
  "metadata_sucursal": "Sucursal Centro",
  "estado": "completado",
  "total_monto": 15000.50,
  "promedio_monto": 2500.08,
  "min_monto": 350.00,
  "max_monto": 12500.99,
  "num_registros": 6,
  "_quality_valid": true
}
```

---

## Transformaciones Aplicadas

### Bronze → Silver

1. **JSONFlattener**: Aplana estructuras anidadas
   - `shipping.address.street` → `shipping_address_street`

2. **DataCleaner**: Limpia datos
   - Trim de espacios en blanco
   - Convierte strings vacíos a NULL

3. **DataNormalizer**: Normaliza formatos
   - Emails a lowercase
   - Teléfonos a formato estándar

4. **DataTypeConverter**: Convierte tipos
   - Strings a números
   - Strings a fechas
   - Strings a booleanos

### Silver → Gold

1. **IncrementalProcessor**: Filtra datos nuevos
   - Solo procesa registros con `fecha_venta > last_timestamp`

2. **SilverToGoldAggregator**: Calcula agregaciones
   - Agrupa por dimensiones (sucursal, estado)
   - Calcula métricas (sum, avg, min, max, count)
   - Agrega dimensiones de tiempo (year, month, day, week)

3. **DataQualityValidator**: Valida calidad
   - Completeness: campos críticos no nulos
   - Validity: valores dentro de rangos permitidos
   - Consistency: coherencia entre columnas
   - Accuracy: valores dentro de rangos de negocio

4. **ErrorHandler**: Maneja errores
   - Marca registros con problemas
   - Envía a DLQ si es necesario

5. **DataLineageTracker**: Rastrea origen
   - Agrega columnas de trazabilidad
   - Hash MD5 por registro

---

## Comparar Datos Entre Etapas

### Usando diff (Linux/Mac)

```bash
# Comparar Bronze vs Silver
diff glue/data/bronze_order_*.json glue/data/silver_order_*.json

# Ver solo las diferencias
diff -u glue/data/bronze_order_*.json glue/data/silver_order_*.json | grep "^[+-]"
```

### Usando Python

```python
import json
import pandas as pd

# Cargar datos
with open('glue/data/bronze_order_6913fcb6d134afc8da8ac3dd_pandas.json') as f:
    bronze = json.load(f)

with open('glue/data/silver_order_6913fcb6d134afc8da8ac3dd_pandas.json') as f:
    silver = json.load(f)

# Comparar número de campos
print(f"Bronze: {len(bronze)} campos")
print(f"Silver: {len(silver[0])} campos")

# Ver campos nuevos en Silver
bronze_keys = set(bronze.keys())
silver_keys = set(silver[0].keys())
print(f"Campos nuevos: {silver_keys - bronze_keys}")
```

---

## Métricas de Calidad

### Ver métricas de calidad en Gold

```python
import pandas as pd

# Cargar datos Gold
df = pd.read_json('glue/data/gold_order_6913fcb6d134afc8da8ac3dd_pandas.json')

# Ver registros válidos
print(f"Registros válidos: {df['_quality_valid'].sum()}/{len(df)}")

# Ver problemas de calidad
if '_quality_issues' in df.columns:
    print("\nProblemas encontrados:")
    print(df[~df['_quality_valid']][['metadata_sucursal', 'estado', '_quality_issues']])
```

---

## Troubleshooting

### Error: "No module named 'pandas'"

```bash
pip install pandas
```

### Error: "No module named 'requests'"

```bash
pip install requests
```

### Error: "FileNotFoundError"

Asegúrate de estar en el directorio correcto:
```bash
cd glue
python scripts/test_full_pipeline_pandas.py
```

### Los datos no se ven bien en la consola

Usa el script visual que genera HTML:
```bash
python scripts/test_pipeline_visual.py
```

---

## Próximos Pasos

1. ✅ Ejecuta las pruebas y familiarízate con los datos
2. ✅ Revisa los archivos JSON generados
3. ✅ Compara los datos entre etapas
4. ✅ Verifica las métricas de calidad
5. ⏳ Prueba con diferentes órdenes de la API
6. ⏳ Modifica la configuración y observa los cambios

---

**Documentación Relacionada**:
- [COMO_PROBAR_PIPELINE.md](./COMO_PROBAR_PIPELINE.md)
- [SCRIPTS_TESTING_DISPONIBLES.md](./SCRIPTS_TESTING_DISPONIBLES.md)
- [INTEGRACION_SILVER_TO_GOLD_MAX.md](./INTEGRACION_SILVER_TO_GOLD_MAX.md)
