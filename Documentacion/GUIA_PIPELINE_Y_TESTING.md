# Guía del Pipeline y Testing Práctico

**Fecha:** 19 de Febrero, 2026  
**Propósito:** Explicar qué hace cada módulo, cómo probar el pipeline, y qué datos entran/salen

---

## 1. ¿Qué Hace el Pipeline? 🎯

El pipeline transforma datos desde **Bronze** (datos crudos de Janis API) hacia **Silver** (datos limpios y estructurados en Iceberg).

### Flujo de Datos

```
┌─────────────────┐
│  Janis API      │ → JSON anidado con estructuras complejas
│  (Bronze S3)    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 1. JSONFlattener│ → Aplana estructuras JSON anidadas
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 2. DataCleaner  │ → Limpia espacios, encoding, nulls
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 3. TypeConverter│ → Convierte tipos de datos (strings → dates, etc)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 4. Normalizer   │ → Normaliza emails, teléfonos, fechas
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 5. GapHandler   │ → Calcula campos faltantes, marca gaps
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 6. DupDetector  │ → Detecta duplicados por business key
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 7. Resolver     │ → Resuelve conflictos (queda el más reciente)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 8. IcebergWriter│ → Escribe a Silver con ACID
│  (Silver Iceberg)│
└─────────────────┘
```

---

## 2. Datos de Entrada (Bronze) 📥

### Ejemplo: Orden de Janis API

```json
{
  "id": "12345",
  "dateCreated": "1609459200",
  "status": "  pending  ",
  "customer": {
    "email": "  USER@TEST.COM  ",
    "phone": "(01) 234-5678",
    "address": {
      "street": "Av. Principal 123",
      "city": "Lima"
    }
  },
  "items": [
    {
      "product_id": "P001",
      "quantity": "10",
      "quantity_picked": "8",
      "substitute_type": "original"
    },
    {
      "product_id": "P002",
      "quantity": "5",
      "quantity_picked": null,
      "substitute_type": "substitute"
    }
  ],
  "amount": "150.50",
  "originalAmount": "145.00"
}
```

### Problemas en los Datos Crudos

1. ❌ **JSON anidado** (customer.address.city)
2. ❌ **Espacios en blanco** ("  pending  ")
3. ❌ **Tipos incorrectos** (dateCreated es string, no timestamp)
4. ❌ **Emails sin normalizar** ("  USER@TEST.COM  ")
5. ❌ **Teléfonos sin formato** ("(01) 234-5678")
6. ❌ **Campos faltantes** (quantity_picked = null)
7. ❌ **Arrays que necesitan explotar** (items)

---

## 3. Transformaciones Paso a Paso 🔄

### Paso 1: JSONFlattener

**Entrada:**
```json
{
  "customer": {
    "email": "USER@TEST.COM",
    "address": {
      "city": "Lima"
    }
  }
}
```

**Salida:**
```
customer_email: "USER@TEST.COM"
customer_address_city: "Lima"
```

**Qué hace:** Convierte estructuras anidadas en columnas planas.

---

### Paso 2: DataCleaner

**Entrada:**
```
status: "  pending  "
email: "  USER@TEST.COM  "
```

**Salida:**
```
status: "pending"
email: "USER@TEST.COM"
```

**Qué hace:** Elimina espacios, corrige encoding UTF-8, convierte strings vacíos a NULL.

---

### Paso 3: DataTypeConverter

**Entrada:**
```
dateCreated: "1609459200" (string)
quantity: "10" (string)
amount: "150.50" (string)
```

**Salida:**
```
dateCreated: 2021-01-01 00:00:00 (timestamp)
quantity: 10 (integer)
amount: 150.50 (decimal)
```

**Qué hace:** Detecta y convierte tipos automáticamente.

---

### Paso 4: DataNormalizer

**Entrada:**
```
email: "USER@TEST.COM"
phone: "(01) 234-5678"
```

**Salida:**
```
email: "user@test.com"
phone: "+51012345678"
```

**Qué hace:** Normaliza emails (lowercase), teléfonos (formato internacional), fechas (ISO 8601).

---

### Paso 5: DataGapHandler

**Entrada:**
```
quantity: 10
quantity_picked: 8
items: [{"substitute_type": "substitute"}, ...]
amount: 150.50
originalAmount: 145.00
```

**Salida:**
```
quantity: 10
quantity_picked: 8
items_qty_missing: 2                    # Calculado: 10 - 8
items_substituted_qty: 1                # Calculado: COUNT(substitute)
total_changes: 5.50                     # Calculado: 150.50 - 145.00
_data_gaps: {"unavailable_fields": [...], "impact": "medium"}
```

**Qué hace:** Calcula campos derivados y marca campos no disponibles.

---

### Paso 6: DuplicateDetector

**Entrada:**
```
Row 1: id=12345, dateCreated=2021-01-01 10:00:00
Row 2: id=12345, dateCreated=2021-01-01 10:05:00  # Duplicado!
Row 3: id=67890, dateCreated=2021-01-01 10:00:00
```

**Salida:**
```
Row 1: id=12345, is_duplicate=True, duplicate_group_id=1
Row 2: id=12345, is_duplicate=True, duplicate_group_id=1
Row 3: id=67890, is_duplicate=False, duplicate_group_id=null
```

**Qué hace:** Marca duplicados por business key (id).

---

### Paso 7: ConflictResolver

**Entrada:**
```
Row 1: id=12345, dateCreated=2021-01-01 10:00:00, status="pending"
Row 2: id=12345, dateCreated=2021-01-01 10:05:00, status="confirmed"  # Más reciente
```

**Salida:**
```
Row 2: id=12345, dateCreated=2021-01-01 10:05:00, status="confirmed"
# Row 1 eliminado (era más antiguo)
```

**Qué hace:** Resuelve conflictos quedándose con el registro más reciente.

---

### Paso 8: IcebergWriter

**Entrada:** DataFrame limpio y deduplicado

**Salida:** Datos escritos en tabla Iceberg en S3 con:
- ✅ Transacciones ACID
- ✅ Snapshots para time travel
- ✅ Particionado por fecha
- ✅ Compresión Parquet

**Qué hace:** Escribe datos a Silver con garantías ACID.

---

## 4. Datos de Salida (Silver) 📤

### Ejemplo: Orden Transformada

```
id: "12345"
dateCreated: 2021-01-01 00:00:00
status: "pending"
customer_email: "user@test.com"
customer_phone: "+51012345678"
customer_address_street: "Av. Principal 123"
customer_address_city: "Lima"
items_qty_missing: 2
items_substituted_qty: 1
total_changes: 5.50
amount: 150.50
originalAmount: 145.00
is_duplicate: False
_data_gaps: {"unavailable_fields": [], "impact": "low"}
```

### Mejoras Aplicadas

✅ **JSON aplanado** (customer_email en lugar de customer.email)  
✅ **Datos limpios** (sin espacios)  
✅ **Tipos correctos** (timestamp, decimal, integer)  
✅ **Emails normalizados** (lowercase)  
✅ **Teléfonos normalizados** (formato internacional)  
✅ **Campos calculados** (items_qty_missing, total_changes)  
✅ **Sin duplicados** (solo el más reciente)  
✅ **Metadata de calidad** (_data_gaps)

---

## 5. Cómo Probar el Pipeline 🧪

### Opción 1: Test con Datos de Ejemplo (Recomendado para Inicio)

Script de prueba con datos simulados:

```python
# glue/scripts/test_pipeline_local.py
import pandas as pd
from modules import (
    DataCleaner,
    DataTypeConverter,
    DataNormalizer,
    DataGapHandler,
    DuplicateDetector,
    ConflictResolver
)

# 1. Crear datos de ejemplo (simulando Bronze)
data = {
    'id': ['12345', '12345', '67890'],
    'dateCreated': ['1609459200', '1609459500', '1609459200'],
    'status': ['  pending  ', '  confirmed  ', 'delivered'],
    'email': ['  USER@TEST.COM  ', 'user@test.com', 'jane@test.com'],
    'phone': ['(01) 234-5678', '(01) 234-5678', '(01) 987-6543'],
    'quantity': ['10', '10', '5'],
    'quantity_picked': ['8', '9', '5'],
    'amount': ['150.50', '150.50', '75.25'],
    'originalAmount': ['145.00', '145.00', '75.25']
}

df = pd.DataFrame(data)
print("=" * 60)
print("DATOS ORIGINALES (Bronze)")
print("=" * 60)
print(df)
print()

# 2. DataCleaner
cleaner = DataCleaner()
config_clean = {
    'data_cleaning': {
        'trim_columns': ['status', 'email'],
        'lowercase_columns': [],
        'null_replacement': {}
    }
}
# Nota: DataCleaner requiere PySpark, aquí simulamos con pandas
df['status'] = df['status'].str.strip()
df['email'] = df['email'].str.strip()
print("=" * 60)
print("DESPUÉS DE LIMPIEZA")
print("=" * 60)
print(df[['status', 'email']])
print()

# 3. DataTypeConverter
converter = DataTypeConverter()
df['dateCreated'] = df['dateCreated'].apply(
    lambda x: converter.convert_bigint_to_timestamp(int(x))
)
df['quantity'] = df['quantity'].astype(int)
df['amount'] = df['amount'].astype(float)
df['originalAmount'] = df['originalAmount'].astype(float)
print("=" * 60)
print("DESPUÉS DE CONVERSIÓN DE TIPOS")
print("=" * 60)
print(df[['dateCreated', 'quantity', 'amount']].dtypes)
print()

# 4. DataNormalizer
normalizer = DataNormalizer()
df['email'] = df['email'].apply(normalizer.validate_and_clean_email)
df['phone'] = df['phone'].apply(
    lambda x: normalizer.normalize_phone_number(x, country_code='51')
)
print("=" * 60)
print("DESPUÉS DE NORMALIZACIÓN")
print("=" * 60)
print(df[['email', 'phone']])
print()

# 5. DataGapHandler
gap_handler = DataGapHandler()
df = gap_handler.calculate_items_qty_missing(df)
df = gap_handler.calculate_total_changes(df)
print("=" * 60)
print("DESPUÉS DE CÁLCULO DE GAPS")
print("=" * 60)
print(df[['items_qty_missing', 'total_changes']])
print()

# 6. DuplicateDetector
detector = DuplicateDetector()
config_dup = {
    'duplicate_detection': {
        'key_columns': ['id']
    }
}
# Simulación con pandas
df['is_duplicate'] = df.duplicated(subset=['id'], keep=False)
df['duplicate_group_id'] = df.groupby('id').ngroup()
df.loc[~df['is_duplicate'], 'duplicate_group_id'] = None
print("=" * 60)
print("DESPUÉS DE DETECCIÓN DE DUPLICADOS")
print("=" * 60)
print(df[['id', 'is_duplicate', 'duplicate_group_id']])
print()

# 7. ConflictResolver
resolver = ConflictResolver()
# Simulación: quedarse con el más reciente por id
df_sorted = df.sort_values('dateCreated', ascending=False)
df_resolved = df_sorted.drop_duplicates(subset=['id'], keep='first')
print("=" * 60)
print("DESPUÉS DE RESOLUCIÓN DE CONFLICTOS")
print("=" * 60)
print(f"Registros antes: {len(df)}, después: {len(df_resolved)}")
print(df_resolved[['id', 'dateCreated', 'status']])
print()

# 8. Resultado final
print("=" * 60)
print("DATOS FINALES (Silver)")
print("=" * 60)
print(df_resolved)
```

**Ejecutar:**
```bash
cd glue
python scripts/test_pipeline_local.py
```

### Opción 2: Test con Datos Reales de Janis API

Script de prueba con datos reales desde la API de Janis:

```python
# glue/scripts/test_pipeline_janis_api.py
import sys
import os
import requests
import json
import pandas as pd
from datetime import datetime

# Agregar el directorio padre al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules import (
    DataTypeConverter,
    DataNormalizer,
    DataGapHandler
)

def fetch_order_from_janis(order_id):
    """Obtiene una orden desde la API de Janis."""
    base_url = "https://oms.janis.in/api/order"
    url = f"{base_url}/{order_id}/history"
    
    headers = {
        'janis-client': 'wongio',
        'janis-api-key': '8fc949ac-6d63-4447-a3d6-a16b66048e61',
        'janis-api-secret': 'UwPbe45dmE7lySRJ3zcA66Pfdt7xAY3QXWO181Y8OTgCxE3aZuyXpS8HyyPSwsWK'
    }
    
    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()
    return response.json()

def flatten_json(data, parent_key='', sep='_'):
    """Aplana un JSON anidado recursivamente."""
    # ... (implementación completa en el archivo)
    
def main():
    # 1. Obtener datos de la API
    order_id = "6913fcb6d134afc8da8ac3dd"
    order_data = fetch_order_from_janis(order_id)
    
    # 2. Aplanar JSON
    if isinstance(order_data, list):
        flattened_data = [flatten_json(item) for item in order_data]
    else:
        flattened_data = [flatten_json(order_data)]
    
    df = pd.DataFrame(flattened_data)
    
    # 3. Aplicar transformaciones
    # - Limpieza de datos
    # - Normalización de emails y teléfonos
    # - Conversión de tipos
    
    # 4. Guardar resultados
    df.to_csv('glue/data/janis_order_transformed.csv', index=False)
    
    print("✓ Pipeline completado con datos reales")
```

**Ejecutar:**
```bash
cd glue
python scripts/test_pipeline_janis_api.py
```

**Archivos generados:**
- `glue/data/janis_order_raw.json` - Datos crudos de la API
- `glue/data/janis_order_flattened.csv` - Datos aplanados
- `glue/data/janis_order_transformed.csv` - Datos transformados

### Opción 3: Test con PySpark (Más Realista)

Para probar con PySpark como en AWS Glue:

```python
# glue/scripts/test_pipeline_pyspark.py
from pyspark.sql import SparkSession
from modules import (
    JSONFlattener,
    DataCleaner,
    DataTypeConverter,
    DataNormalizer,
    DataGapHandler,
    DuplicateDetector,
    ConflictResolver
)

# Inicializar Spark
spark = SparkSession.builder \
    .appName("PipelineTest") \
    .getOrCreate()

# 1. Leer datos de Bronze
df = spark.read.json("data/bronze/orders/*.json")

# 2. Aplicar transformaciones
flattener = JSONFlattener()
df = flattener.transform(df, {})

cleaner = DataCleaner()
df = cleaner.clean(df, config_clean)

# ... etc
```

---

## 6. Configuración del Pipeline ⚙️

Cada módulo acepta una configuración. Ejemplo completo:

```python
pipeline_config = {
    # JSONFlattener
    'json_flattening': {
        'max_depth': 10
    },
    
    # DataCleaner
    'data_cleaning': {
        'trim_columns': ['status', 'email', 'phone'],
        'lowercase_columns': ['email'],
        'null_replacement': {
            'status': 'unknown',
            'quantity': 0
        }
    },
    
    # DataTypeConverter
    'type_conversion': {
        'inference_sample_size': 100,
        'inference_threshold': 0.9,
        'date_columns': ['dateCreated', 'dateModified'],
        'timestamp_columns': ['createdAt', 'updatedAt']
    },
    
    # DataNormalizer
    'data_normalization': {
        'email_columns': ['customer_email', 'billing_email'],
        'phone_columns': ['customer_phone', 'contact_phone'],
        'date_columns': ['birthdate'],
        'timestamp_columns': ['last_login']
    },
    
    # DataGapHandler
    'data_gap_handling': {
        'critical_columns': ['id', 'customer_id'],
        'default_values': {
            'status': 'unknown',
            'quantity': 0
        },
        'filter_incomplete': False
    },
    
    # DuplicateDetector
    'duplicate_detection': {
        'key_columns': ['id'],
        'mark_only': True
    },
    
    # ConflictResolver
    'conflict_resolution': {
        'key_columns': ['id'],
        'timestamp_column': 'dateCreated',
        'strategy': 'latest'
    }
}
```

---

## 7. Métricas de Calidad 📊

Después de ejecutar el pipeline, puedes generar métricas:

```python
# Generar reporte de calidad
gap_handler = DataGapHandler()
report = gap_handler.generate_data_gap_report(df)

print("Reporte de Calidad:")
print(f"- Total registros: {report['total_records']}")
print(f"- Registros con gaps: {report['records_with_gaps']}")
print(f"- Impacto: {report['impact_assessment']}")
print(f"- Campos no disponibles: {report['unavailable_fields']}")
```

---

## 8. Próximos Pasos 🚀

1. **Crear script de prueba local** (`test_pipeline_local.py`)
2. **Probar con datos de ejemplo**
3. **Validar resultados**
4. **Ajustar configuración según necesidades**
5. **Probar con datos reales de Janis**
6. **Integrar en AWS Glue Job**

---

## Resumen

**Entrada:** JSON anidado, sucio, con tipos incorrectos  
**Salida:** Datos planos, limpios, normalizados, sin duplicados, con metadata de calidad  
**Cómo probar:** Script local con pandas o PySpark  
**Configuración:** Archivo YAML o dict de Python

¿Quieres que cree el script de prueba local para que puedas ejecutarlo ahora?
