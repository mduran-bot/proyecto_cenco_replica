# Scripts de Testing Disponibles

**Fecha:** 19 de Febrero, 2026  
**Propósito:** Documentación de todos los scripts de prueba del pipeline

---

## Scripts de Testing Disponibles

El proyecto incluye múltiples scripts de testing para validar el pipeline de transformación de datos en diferentes escenarios:

1. **test_pipeline_local.py** - Datos simulados para desarrollo rápido (Bronze-to-Silver)
2. **test_pipeline_janis_api.py** - Datos reales de la API de Janis (Bronze-to-Silver)
3. **pipeline_with_schema_mapping.py** - Pipeline completo con mapeo de esquema a tablas Redshift (transformaciones simplificadas)
4. **test_integration_phase_1_2.py** - Tests de integración de módulos fusionados
5. **test_silver_to_gold_local.py** - Test del pipeline Silver-to-Gold con PySpark ⭐ NUEVO
6. **test_silver_to_gold_pandas.py** - Test del pipeline Silver-to-Gold con pandas (sin PySpark) ⭐ NUEVO
7. **test_full_pipeline_pandas.py** - Pipeline completo API → Bronze → Silver → Gold con pandas ⭐ NUEVO

**📖 Guía Visual:** Ver [GUIA_EJECUTAR_PRUEBAS_VISUALES.md](./GUIA_EJECUTAR_PRUEBAS_VISUALES.md) para instrucciones paso a paso con ejemplos visuales

---

## 1. test_pipeline_local.py

### Propósito
Probar el pipeline completo con datos de ejemplo simulados, sin necesidad de conexión a internet.

### Ubicación
`glue/scripts/test_pipeline_local.py`

### Características
- ✅ Datos de ejemplo predefinidos (4 registros)
- ✅ Simula problemas comunes (espacios, tipos incorrectos, duplicados)
- ✅ Ejecución rápida (~5 segundos)
- ✅ No requiere conexión a internet
- ✅ Output con colores para mejor visualización

### Uso
```bash
cd glue
python scripts/test_pipeline_local.py
```

### Datos de Entrada
```python
data = {
    'id': ['12345', '12345', '67890', '11111'],
    'dateCreated': ['1609459200', '1609459500', '1609459200', '1609459800'],
    'status': ['  pending  ', '  confirmed  ', 'delivered', '  pending  '],
    'email': ['  USER@TEST.COM  ', 'user@test.com', 'jane@test.com', 'BOB@TEST.COM'],
    'phone': ['(01) 234-5678', '(01) 234-5678', '(01) 987-6543', '(01) 111-2222'],
    # ... más campos
}
```

### Transformaciones Aplicadas
1. **Limpieza de datos** - Trim de espacios en blanco
2. **Conversión de tipos** - String → timestamp, int, float
3. **Normalización** - Emails lowercase, teléfonos formato internacional
4. **Cálculo de gaps** - items_qty_missing, total_changes
5. **Detección de duplicados** - Por business key (id)
6. **Resolución de conflictos** - Quedarse con el más reciente

### Output Esperado
```
============================================================
DATOS ORIGINALES (Bronze - Crudos de Janis API)
============================================================

Problemas en los datos:
  ❌ Espacios en blanco en status y email
  ❌ Tipos incorrectos (todo es string)
  ...

>>> PASO 1: LIMPIEZA DE DATOS (DataCleaner)
>>> PASO 2: CONVERSIÓN DE TIPOS (DataTypeConverter)
>>> PASO 3: NORMALIZACIÓN (DataNormalizer)
>>> PASO 4: MANEJO DE GAPS (DataGapHandler)
>>> PASO 5: DETECCIÓN DE DUPLICADOS (DuplicateDetector)
>>> PASO 6: RESOLUCIÓN DE CONFLICTOS (ConflictResolver)
>>> PASO 7: REPORTE DE CALIDAD

============================================================
DATOS FINALES (Silver - Listos para Iceberg)
============================================================

Mejoras aplicadas:
  ✅ Datos limpios (sin espacios)
  ✅ Tipos correctos (timestamp, int, float)
  ...
```

### Cuándo Usar
- Desarrollo inicial de transformaciones
- Testing rápido de cambios en módulos
- Debugging de lógica de transformación
- Demos y presentaciones

---

## 2. test_pipeline_janis_api.py

### Propósito
Probar el pipeline con datos reales obtenidos directamente de la API de Janis.

### Ubicación
`glue/scripts/test_pipeline_janis_api.py`

### Características
- ✅ Conexión real a la API de Janis
- ✅ Obtiene datos de órdenes específicas
- ✅ Aplana estructuras JSON complejas
- ✅ Guarda archivos intermedios para análisis
- ✅ Identifica columnas relevantes automáticamente
- ✅ Genera reporte de calidad de datos

### Uso
```bash
cd glue
python scripts/test_pipeline_janis_api.py
```

### Configuración

#### Cambiar Order ID
```python
# Línea 144 en test_pipeline_janis_api.py
order_id = "6913fcb6d134afc8da8ac3dd"  # Cambiar este ID
```

#### Credenciales de API
```python
headers = {
    'janis-client': 'wongio',
    'janis-api-key': '8fc949ac-6d63-4447-a3d6-a16b66048e61',
    'janis-api-secret': 'UwPbe45dmE7lySRJ3zcA66Pfdt7xAY3QXWO181Y8OTgCxE3aZuyXpS8HyyPSwsWK'
}
```

**⚠️ Nota:** En producción, usar AWS Secrets Manager.

### Endpoint de API
```
https://oms.janis.in/api/order/{order_id}/history
```

Retorna el historial completo de cambios de una orden.

### Archivos Generados

1. **janis_order_raw.json**
   - Datos crudos tal como vienen de la API
   - Formato: JSON con estructuras anidadas
   - Útil para: Debugging, análisis de estructura

2. **janis_order_flattened.csv**
   - Datos después de aplanar JSON
   - Formato: CSV con todas las columnas expandidas
   - Útil para: Ver estructura aplanada, análisis en Excel

3. **janis_order_transformed.csv**
   - Datos después de todas las transformaciones
   - Formato: CSV con datos limpios y normalizados
   - Útil para: Validar calidad final, comparar con esperado

### Pasos del Pipeline

1. **Obtener datos de API** - Conexión HTTP con autenticación
2. **Aplanar JSON** - Recursivo hasta estructuras simples
3. **Identificar columnas relevantes** - Filtrado por patrones
4. **Aplicar transformaciones**:
   - Limpieza de datos (trim, encoding)
   - Normalización de emails y teléfonos
   - Conversión de tipos (timestamps)
5. **Generar reporte de calidad** - Estadísticas de nulls

### Output Esperado
```
============================================================
PASO 0: OBTENER DATOS DE JANIS API
============================================================

Obteniendo orden: 6913fcb6d134afc8da8ac3dd
✓ Datos obtenidos exitosamente (Status: 200)
✓ Datos guardados en: glue/data/janis_order_raw.json

Estructura de datos recibidos:
  Tipo: <class 'list'>
  Cantidad de registros: 15

>>> PASO 1: APLANAR JSON (JSONFlattener)

Columnas después de aplanar: 87
Registros: 15
✓ Datos aplanados guardados en: glue/data/janis_order_flattened.csv

>>> PASO 2: IDENTIFICAR COLUMNAS RELEVANTES

Columnas relevantes encontradas: 45

>>> PASO 3: APLICAR TRANSFORMACIONES

3.1 Limpiando datos...
✓ Espacios en blanco eliminados

3.2 Normalizando emails...
✓   - customer_email normalizado

3.3 Normalizando teléfonos...
✓   - customer_phone normalizado

3.4 Convirtiendo tipos de datos...
✓   - dateCreated convertido a timestamp

>>> PASO 4: RESULTADOS FINALES

Datos transformados:
  - Registros: 15
  - Columnas: 45
✓ Datos transformados guardados en: glue/data/janis_order_transformed.csv

>>> PASO 5: REPORTE DE CALIDAD

✓ PIPELINE COMPLETADO EXITOSAMENTE CON DATOS REALES
```

### Cuándo Usar
- Validación con datos reales de producción
- Testing de estructuras JSON complejas
- Identificación de problemas de formato
- Análisis de calidad de datos de Janis
- Debugging de transformaciones específicas

### Prueba Exitosa Documentada
✅ **Ver:** `Documentacion/PRUEBA_EXITOSA_API_JANIS.md` para detalles completos de la prueba exitosa con la API real de Janis, incluyendo:
- Endpoint correcto identificado
- Estructura de datos obtenidos
- Archivos generados
- Transformaciones aplicadas
- Campos relevantes mapeados

### Troubleshooting

#### Error: "No se pudieron obtener datos de la API"
**Causas:**
- Sin conexión a internet
- Credenciales inválidas
- Order ID no existe
- API de Janis caída

**Solución:**
```bash
# Verificar conectividad
curl https://oms.janis.in/api/health

# Probar con otro order ID
```

#### Error: "ModuleNotFoundError: No module named 'requests'"
**Solución:**
```bash
pip install requests pandas
```

---

## 3. pipeline_with_schema_mapping.py

### Propósito
Pipeline completo que mapea datos de la API de Janis a las tablas finales de Redshift (wms_orders, wms_order_items, wms_order_shipping) según el esquema definido.

### Ubicación
`glue/scripts/pipeline_with_schema_mapping.py`

### Características
- ✅ Mapeo explícito de campos API → Redshift
- ✅ Genera 3 tablas relacionadas desde una orden
- ✅ Manejo de estructuras anidadas (addresses, items, shippings)
- ✅ Transformaciones básicas simplificadas (pandas nativo)
- ✅ Reporte de calidad por tabla
- ✅ Archivos CSV listos para carga a Redshift

**Nota:** Usa transformaciones simplificadas con pandas nativo para facilitar testing sin dependencias complejas. El pipeline de producción en AWS Glue usará los módulos completos integrados.

### Uso
```bash
cd glue
python scripts/pipeline_with_schema_mapping.py
```

### Mapeos Implementados

#### wms_orders (27 campos)
```python
WMS_ORDERS_MAPPING = {
    'vtex_id': 'commerceId',
    'id': 'id',
    'seq_id': 'commerceSequentialId',
    'ecommerce_account': 'account.id',
    'seller_id': 'seller.id',
    'total': 'totalAmount',
    'status': 'status',
    'date_created': 'dateCreated',
    # ... 19 campos más
}
```

#### wms_order_items (11 campos)
```python
WMS_ORDER_ITEMS_MAPPING = {
    'id': 'items[].id',
    'order_id': 'id',
    'sku': 'items[].skuId',
    'product': 'items[].commerceProductId',
    'price': 'items[].purchasedPrice',
    'quantity': 'items[].purchasedQuantity',
    # ... 5 campos más
}
```

#### wms_order_shipping (11 campos)
```python
WMS_ORDER_SHIPPING_MAPPING = {
    'id': 'shippings[].id',
    'order_id': 'id',
    'city': 'addresses[].city',
    'lat': 'addresses[].geolocation[1]',
    'lng': 'addresses[].geolocation[0]',
    'carrier_id': 'shippings[].carrierId',
    # ... 5 campos más
}
```

### Pasos del Pipeline

1. **Obtener datos de API** - Conexión a Janis API
2. **Mapear a wms_orders** - Extracción de campos de orden
3. **Mapear a wms_order_items** - Explosión de array de items
4. **Mapear a wms_order_shipping** - Explosión de array de shippings
5. **Aplicar transformaciones**:
   - Limpieza de datos (DataCleaner)
   - Normalización (DataNormalizer)
   - Conversión de tipos (DataTypeConverter)
   - Manejo de gaps (DataGapHandler)
6. **Guardar resultados** - 3 archivos CSV + 1 JSON raw
7. **Generar reporte de calidad** - Métricas por tabla

### Archivos Generados

Para cada orden procesada:

1. **order_{id}_raw.json**
   - Datos crudos de la API
   - Formato: JSON completo sin transformar

2. **order_{id}_wms_orders.csv**
   - Tabla principal de órdenes
   - 1 registro por orden
   - 27 columnas mapeadas

3. **order_{id}_wms_order_items.csv**
   - Tabla de items de orden
   - N registros (1 por item)
   - 11 columnas mapeadas

4. **order_{id}_wms_order_shipping.csv**
   - Tabla de envíos
   - N registros (1 por shipping)
   - 11 columnas mapeadas

### Output Esperado
```
================================================================================
🚀 INICIANDO PIPELINE CON MAPEO DE ESQUEMA
================================================================================
Orden ID: 6913fcb6d134afc8da8ac3dd
Timestamp: 2026-02-19T15:30:00

📥 Paso 1: Obteniendo datos de la API de Janis...
✅ Datos obtenidos exitosamente
   - Orden: 513111
   - Items: 3
   - Shippings: 1
   - Guardado en: glue/data/order_6913fcb6d134afc8da8ac3dd_raw.json

🗺️  Paso 2: Mapeando a formato wms_orders...
✅ Mapeado completado: 1 registro(s)
   - Campos mapeados: 24/27

🗺️  Paso 3: Mapeando a formato wms_order_items...
✅ Mapeado completado: 3 registro(s)

🗺️  Paso 4: Mapeando a formato wms_order_shipping...
✅ Mapeado completado: 1 registro(s)

🔧 Paso 5: Aplicando transformaciones del pipeline...

🔄 Aplicando transformaciones a wms_orders...
  - Limpiando datos...
  - Normalizando datos...
  - Convirtiendo tipos de datos...
  - Manejando gaps de datos...
✅ Transformaciones completadas para wms_orders

🔄 Aplicando transformaciones a wms_order_items...
  - Limpiando datos...
  - Normalizando datos...
  - Convirtiendo tipos de datos...
  - Manejando gaps de datos...
✅ Transformaciones completadas para wms_order_items

🔄 Aplicando transformaciones a wms_order_shipping...
  - Limpiando datos...
  - Normalizando datos...
  - Convirtiendo tipos de datos...
  - Manejando gaps de datos...
✅ Transformaciones completadas para wms_order_shipping

💾 Paso 6: Guardando resultados...
   - wms_orders: glue/data/order_6913fcb6d134afc8da8ac3dd_wms_orders.csv
   - wms_order_items: glue/data/order_6913fcb6d134afc8da8ac3dd_wms_order_items.csv
   - wms_order_shipping: glue/data/order_6913fcb6d134afc8da8ac3dd_wms_order_shipping.csv

📊 Paso 7: Generando reporte de calidad...

================================================================================
REPORTE DE CALIDAD DE DATOS
================================================================================

📋 wms_orders:
   - Total registros: 1
   - Total columnas: 27
   - Campos con datos: 24
   - Campos vacíos: 3
   - Completitud: 88.9%

📋 wms_order_items:
   - Total registros: 3
   - Total columnas: 11
   - Campos con datos: 30
   - Campos vacíos: 3
   - Completitud: 90.9%

📋 wms_order_shipping:
   - Total registros: 1
   - Total columnas: 11
   - Campos con datos: 9
   - Campos vacíos: 2
   - Completitud: 81.8%

================================================================================
✅ PIPELINE COMPLETADO EXITOSAMENTE
================================================================================

Archivos generados:
  - glue/data/order_6913fcb6d134afc8da8ac3dd_raw.json
  - glue/data/order_6913fcb6d134afc8da8ac3dd_wms_orders.csv
  - glue/data/order_6913fcb6d134afc8da8ac3dd_wms_order_items.csv
  - glue/data/order_6913fcb6d134afc8da8ac3dd_wms_order_shipping.csv
```

### Configuración

#### Cambiar Order ID
```python
# Línea 434 en pipeline_with_schema_mapping.py
ORDER_ID = "6913fcb6d134afc8da8ac3dd"  # Cambiar este ID
```

#### Agregar Nuevos Mapeos
Para agregar campos adicionales, editar los diccionarios de mapeo:

```python
WMS_ORDERS_MAPPING = {
    # Campos existentes...
    'nuevo_campo': 'ruta.en.api.janis',
}
```

### Casos de Uso

1. **Validar mapeo de esquema** - Verificar que todos los campos se mapean correctamente
2. **Generar datos de prueba** - Crear CSVs para testing de carga a Redshift
3. **Documentar estructura** - Entender relación entre API y tablas finales
4. **Debugging de transformaciones** - Ver datos en cada etapa del pipeline
5. **Análisis de calidad** - Identificar campos faltantes o con problemas

### Cuándo Usar
- Desarrollo de mapeos de esquema
- Validación de estructura de datos
- Generación de datos de prueba para Redshift
- Documentación de transformaciones
- Análisis de completitud de datos

### Ventajas sobre Otros Scripts
- **Mapeo explícito**: Claridad total sobre origen y destino de cada campo
- **Múltiples tablas**: Genera estructura relacional completa
- **Listo para Redshift**: CSVs en formato compatible con COPY
- **Reporte de calidad**: Métricas detalladas por tabla
- **Trazabilidad**: JSON raw + CSVs transformados

---

## 4. test_integration_phase_1_2.py

### Propósito
Tests de integración para validar los módulos fusionados de la Fase 1.2.

### Ubicación
`glue/scripts/test_integration_phase_1_2.py`

### Características
- ✅ Tests de integración de módulos fusionados
- ✅ Validación de compatibilidad pandas/PySpark
- ✅ Tests de DataTypeConverter, DataNormalizer, DataGapHandler
- ✅ Verificación de imports y exports

### Uso
```bash
cd glue
pytest scripts/test_integration_phase_1_2.py -v
```

### Tests Incluidos
1. **test_imports** - Validar que todos los módulos se importan correctamente
2. **test_data_type_converter_pandas** - Conversiones con pandas
3. **test_data_normalizer_pandas** - Normalizaciones con pandas
4. **test_data_gap_handler_pandas** - Cálculos de gaps con pandas

### Cuándo Usar
- Después de cambios en módulos fusionados
- Validación de compatibilidad entre versiones
- CI/CD pipeline
- Antes de merge a main

---

## 5. test_silver_to_gold_local.py ⭐ NUEVO

### Propósito
Probar el pipeline completo Silver-to-Gold con datos locales simulados, sin necesidad de LocalStack ni conexión a S3.

### Ubicación
`glue/scripts/test_silver_to_gold_local.py`

### Características
- ✅ Datos de prueba predefinidos (10 registros en formato Silver)
- ✅ Simula datos ya procesados por Bronze-to-Silver
- ✅ Ejecución rápida (~30 segundos)
- ✅ No requiere LocalStack ni S3
- ✅ Prueba 6 módulos Silver-to-Gold
- ✅ Logging detallado con análisis de calidad

### Uso
```bash
cd glue
python scripts/test_silver_to_gold_local.py
```

### Datos de Entrada (Silver)
```python
data = [
    ("1001", "Juan Pérez", "Laptop HP", 2500.80, datetime(2026, 2, 15, 10, 30), "completado", "Sucursal Centro", True, False),
    ("1002", "María González", "Teclado Mecánico", 850.50, datetime(2026, 2, 16, 14, 20), "completado", "Sucursal Norte", True, False),
    # ... 8 registros más
]
```

### Módulos Probados
1. **IncrementalProcessor** - Deshabilitado en test local
2. **SilverToGoldAggregator** - Agregaciones por sucursal y estado
3. **DenormalizationEngine** - Deshabilitado (no hay tablas de dimensiones)
4. **DataQualityValidator** - Validación de calidad en 4 dimensiones
5. **ErrorHandler** - Manejo de errores (modo flag)
6. **DataLineageTracker** - Deshabilitado en test local

### Transformaciones Aplicadas
1. **Agregaciones** - Por metadata_sucursal y estado:
   - sum(monto) → total_monto
   - avg(monto) → promedio_monto
   - min(monto) → min_monto
   - max(monto) → max_monto
   - count(*) → num_registros

2. **Validación de Calidad**:
   - Completeness: Campos críticos no nulos
   - Validity: Valores dentro de listas permitidas
   - Consistency: Reglas de coherencia
   - Accuracy: Valores dentro de rangos

3. **Error Handling**:
   - Marca registros con problemas
   - Modo "flag" (mantiene todos los registros)

### Output Esperado
```
============================================================
TEST PIPELINE SILVER → GOLD (LOCAL)
============================================================

1. Creando datos de prueba en formato Silver...
   Registros creados: 10

   Muestra de datos Silver:
+----+---------------+------------------+-------+-------------------+-----------+------------------+---------+------------------+
|id  |cliente_nombre |producto_nombre   |monto  |fecha_venta        |estado     |metadata_sucursal |es_valido|has_critical_gaps |
+----+---------------+------------------+-------+-------------------+-----------+------------------+---------+------------------+
|1001|Juan Pérez     |Laptop HP         |2500.80|2026-02-15 10:30:00|completado |Sucursal Centro   |true     |false             |
|1002|María González |Teclado Mecánico  |850.50 |2026-02-16 14:20:00|completado |Sucursal Norte    |true     |false             |
...

2. Guardando datos Silver en: glue/data/test_silver

3. Importando módulos Silver-to-Gold...

4. Leyendo datos Silver...
   Registros leídos: 10

5. Ejecutando módulos de transformación...

   5.1 IncrementalProcessor (skipped - disabled)
   
   5.2 SilverToGoldAggregator...
       → 6 registros agregados
   
   5.3 DenormalizationEngine (skipped - disabled)
   
   5.4 DataQualityValidator...
       → 6 registros validados
   
   5.5 ErrorHandler...
       → 6 registros después de error handling

6. Guardando datos Gold en: glue/data/test_gold

7. Verificando resultados en Gold...
   Total registros en Gold: 6

   Columnas en Gold:
   - _processing_timestamp
   - _quality_issues
   - _quality_valid
   - estado
   - max_monto
   - metadata_sucursal
   - min_monto
   - num_registros
   - promedio_monto
   - total_monto

   Muestra de datos Gold (agregados):
+------------------+-----------+-----------+--------------+---------+----------+-------------+--------------+
|metadata_sucursal |estado     |total_monto|promedio_monto|min_monto|max_monto |num_registros|_quality_valid|
+------------------+-----------+-----------+--------------+---------+----------+-------------+--------------+
|Sucursal Centro   |completado |20801.79   |6933.93       |280.00   |12500.99  |3            |true          |
|Sucursal Norte    |completado |850.50     |850.50        |850.50   |850.50    |1            |true          |
|Sucursal Centro   |pendiente  |350.00     |350.00        |350.00   |350.00    |1            |true          |
|Sucursal Sur      |completado |8800.00    |4400.00       |3200.00  |5600.00   |2            |true          |
|Sucursal Norte    |cancelado  |450.00     |450.00        |450.00   |450.00    |1            |false         |
|Sucursal Sur      |rechazado  |890.00     |890.00        |890.00   |890.00    |1            |false         |
+------------------+-----------+-----------+--------------+---------+----------+-------------+--------------+

8. Análisis de Calidad de Datos:
   Registros válidos: 4/6 (66.7%)
   Registros inválidos: 2/6 (33.3%)

   Registros con problemas de calidad:
+------------------+---------+---------------+
|metadata_sucursal |estado   |_quality_issues|
+------------------+---------+---------------+
|Sucursal Norte    |cancelado|VALIDITY_FAIL; |
|Sucursal Sur      |rechazado|VALIDITY_FAIL; |
+------------------+---------+---------------+

============================================================
✅ TEST COMPLETADO EXITOSAMENTE
============================================================
```

### Archivos Generados

1. **glue/data/test_silver/**
   - Datos Silver de entrada (JSON)
   - 10 registros simulados

2. **glue/data/test_gold/**
   - Datos Gold de salida (JSON)
   - 6 registros agregados (agrupados por sucursal + estado)

### Configuración Utilizada

```python
config = {
    "incremental": {
        "enabled": False  # Deshabilitado para test inicial
    },
    "aggregations": {
        "date_column": "fecha_venta",
        "dimensions": ["metadata_sucursal", "estado"],
        "metrics": [
            {"column": "monto", "functions": ["sum", "avg", "min", "max"]},
            {"column": "*", "functions": ["count"]}
        ]
    },
    "denormalization": {
        "enabled": False  # No hay tablas de dimensiones en test local
    },
    "quality": {
        "critical_columns": ["estado", "metadata_sucursal"],
        "valid_values": {
            "estado": ["completado", "pendiente", "cancelado", "rechazado"]
        },
        "numeric_ranges": {
            "monto": {"min": 0, "max": 99999999}
        },
        "consistency_rules": [
            {
                "when_column": "estado",
                "when_value": "completado",
                "then_column": "monto",
                "then_not_null": True
            }
        ],
        "quality_gate": False,
        "threshold": 0.8
    },
    "error_handler": {
        "dlq_enabled": False,  # Deshabilitado para test local
        "recovery_mode": "flag"
    },
    "lineage": {
        "enabled": False  # Deshabilitado para test local
    }
}
```

### Cuándo Usar
- Testing del pipeline Silver-to-Gold sin infraestructura
- Validación de agregaciones y métricas de negocio
- Prueba de validación de calidad de datos
- Desarrollo y debugging de transformaciones Gold
- Demos y presentaciones del pipeline completo

### Ventajas
- **Sin dependencias externas**: No requiere LocalStack, S3 ni AWS
- **Rápido**: Ejecución en ~30 segundos
- **Datos controlados**: Resultados predecibles para testing
- **Logging detallado**: Fácil debugging de transformaciones
- **Análisis de calidad**: Reporte completo de validación

### Limitaciones
- **No prueba procesamiento incremental**: IncrementalProcessor deshabilitado
- **No prueba desnormalización**: No hay tablas de dimensiones
- **No prueba DLQ**: Dead Letter Queue deshabilitado
- **No prueba lineage**: DataLineageTracker deshabilitado
- **Datos simulados**: No refleja complejidad de datos reales

### Próximos Pasos
1. Habilitar IncrementalProcessor con metadata tracking
2. Agregar tablas de dimensiones para probar DenormalizationEngine
3. Habilitar DLQ y probar error handling completo
4. Habilitar DataLineageTracker y verificar reportes
5. Probar con datos reales de Silver (output de Bronze-to-Silver)

---

## 6. test_silver_to_gold_pandas.py ⭐ NUEVO

### Propósito
Probar el pipeline Silver-to-Gold usando pandas puro (sin PySpark), ideal para desarrollo rápido y testing sin dependencias pesadas.

### Ubicación
`glue/scripts/test_silver_to_gold_pandas.py`

### Características
- ✅ Usa pandas en lugar de PySpark (más ligero)
- ✅ Datos de prueba predefinidos (10 registros en formato Silver)
- ✅ Ejecución muy rápida (~5 segundos)
- ✅ No requiere Spark ni Java
- ✅ Implementa lógica simplificada de módulos Silver-to-Gold
- ✅ Ideal para desarrollo y debugging rápido

### Uso
```bash
cd glue
python scripts/test_silver_to_gold_pandas.py
```

### Datos de Entrada (Silver)
```python
data = {
    "id": ["1001", "1002", "1003", "1004", "1005", "1006", "1007", "1008", "1009", "1010"],
    "cliente_nombre": ["Juan Pérez", "María González", ...],
    "producto_nombre": ["Laptop HP", "Teclado Mecánico", ...],
    "monto": [2500.80, 850.50, 350.00, ...],
    "fecha_venta": ["2026-02-15T10:30:00", ...],
    "estado": ["completado", "completado", "pendiente", ...],
    "metadata_sucursal": ["Sucursal Centro", "Sucursal Norte", ...],
    "es_valido": [True, True, True, ...],
    "has_critical_gaps": [False, False, False, ...]
}
```

### Transformaciones Aplicadas
1. **Agregación** - Por metadata_sucursal y estado:
   - sum(monto) → total_monto
   - avg(monto) → promedio_monto
   - min(monto) → min_monto
   - max(monto) → max_monto
   - count(*) → num_registros

2. **Validación de Calidad**:
   - Completeness: Campos críticos no nulos
   - Validity: Valores dentro de listas permitidas
   - Range: Valores numéricos en rango
   - Consolidación en _quality_valid y _quality_issues

3. **Error Handling**:
   - Marca registros con problemas
   - Agrega columna _error_handled

### Output Esperado
```
============================================================
TEST PIPELINE SILVER → GOLD (PANDAS)
============================================================

1. Creando datos de prueba en formato Silver...
   Registros creados: 10

   Muestra de datos Silver:
      id cliente_nombre producto_nombre   monto         fecha_venta     estado metadata_sucursal  es_valido  has_critical_gaps
0  1001    Juan Pérez       Laptop HP  2500.80 2026-02-15 10:30:00  completado   Sucursal Centro       True              False
1  1002 María González Teclado Mecánico   850.50 2026-02-16 14:20:00  completado   Sucursal Norte       True              False
...

2. Guardando datos Silver en: glue/data/test_silver_pandas.json

3. Ejecutando transformaciones Silver → Gold...

   3.1 SilverToGoldAggregator...
       → 6 registros agregados
   
   3.2 DataQualityValidator...
       → 6 registros validados
   
   3.3 ErrorHandler...
       → 6 registros después de error handling

4. Guardando datos Gold en: glue/data/test_gold_pandas.json

5. Verificando resultados en Gold...
   Total registros en Gold: 6

   Columnas en Gold:
   - _error_handled
   - _processing_timestamp
   - _quality_issues
   - _quality_valid
   - estado
   - max_monto
   - metadata_sucursal
   - min_monto
   - num_registros
   - promedio_monto
   - total_monto

   Muestra de datos Gold (agregados):
  metadata_sucursal     estado  total_monto  promedio_monto  min_monto  max_monto  num_registros  _quality_valid
0   Sucursal Centro  completado     20801.79         6933.93     280.00   12500.99              3            True
1   Sucursal Norte   completado       850.50          850.50     850.50     850.50              1            True
2   Sucursal Centro   pendiente       350.00          350.00     350.00     350.00              1            True
3      Sucursal Sur  completado      8800.00         4400.00    3200.00    5600.00              2            True
4   Sucursal Norte   cancelado       450.00          450.00     450.00     450.00              1           False
5      Sucursal Sur  rechazado       890.00          890.00     890.00     890.00              1           False

6. Análisis de Calidad de Datos:
   Registros válidos: 4/6 (66.7%)
   Registros inválidos: 2/6 (33.3%)

   Registros con problemas de calidad:
  metadata_sucursal    estado      _quality_issues
4   Sucursal Norte  cancelado       VALIDITY_FAIL;
5      Sucursal Sur  rechazado       VALIDITY_FAIL;

7. Resumen por Sucursal:
  metadata_sucursal  total_monto  num_registros
0   Sucursal Centro     21151.79              4
1   Sucursal Norte       1300.50              2
2      Sucursal Sur      9690.00              3

============================================================
✅ TEST COMPLETADO EXITOSAMENTE
============================================================

Archivos generados:
  - Silver: glue/data/test_silver_pandas.json
  - Gold:   glue/data/test_gold_pandas.json
============================================================
```

### Archivos Generados

1. **glue/data/test_silver_pandas.json**
   - Datos Silver de entrada (JSON)
   - 10 registros simulados con timestamps

2. **glue/data/test_gold_pandas.json**
   - Datos Gold de salida (JSON)
   - 6 registros agregados (agrupados por sucursal + estado)

### Funciones Implementadas

```python
def create_sample_silver_data():
    """Crear datos de prueba en formato Silver"""
    # Crea DataFrame pandas con 10 registros de ejemplo

def aggregate_data(df):
    """Agregar datos por sucursal y estado"""
    # Implementa lógica de SilverToGoldAggregator con pandas

def validate_quality(df):
    """Validar calidad de datos"""
    # Implementa lógica de DataQualityValidator con pandas

def handle_errors(df):
    """Manejar errores"""
    # Implementa lógica de ErrorHandler con pandas
```

### Cuándo Usar
- **Desarrollo rápido**: Probar lógica sin overhead de Spark
- **Debugging**: Más fácil de debuggear que PySpark
- **Testing unitario**: Validar transformaciones individuales
- **Demos**: Mostrar funcionalidad sin setup complejo
- **CI/CD**: Tests rápidos en pipeline de integración

### Ventajas
- **Muy rápido**: ~5 segundos vs ~30 segundos con PySpark
- **Sin dependencias pesadas**: Solo pandas (no requiere Java/Spark)
- **Fácil debugging**: Usar debugger Python estándar
- **Portable**: Funciona en cualquier ambiente con Python
- **Ideal para desarrollo**: Iteración rápida de lógica

### Limitaciones
- **No es producción**: Lógica simplificada, no usa módulos reales
- **Sin escalabilidad**: pandas no escala como PySpark
- **Funcionalidad reducida**: Solo agregación, validación y error handling básicos
- **No prueba integración**: No usa módulos Silver-to-Gold reales
- **Datos en memoria**: No apropiado para datasets grandes

### Diferencias con test_silver_to_gold_local.py

| Aspecto | test_silver_to_gold_pandas.py | test_silver_to_gold_local.py |
|---------|-------------------------------|------------------------------|
| **Framework** | pandas puro | PySpark |
| **Velocidad** | ~5 segundos | ~30 segundos |
| **Dependencias** | Solo pandas | PySpark + Java |
| **Módulos** | Lógica simplificada inline | Módulos reales importados |
| **Escalabilidad** | Limitada (memoria) | Alta (distribuido) |
| **Debugging** | Muy fácil | Más complejo |
| **Producción** | No | Más cercano |
| **Uso recomendado** | Desarrollo rápido | Testing completo |

### Próximos Pasos
1. Usar para desarrollo rápido de lógica de agregación
2. Validar transformaciones antes de implementar en PySpark
3. Crear tests unitarios basados en este script
4. Migrar lógica validada a módulos PySpark reales
5. Usar test_silver_to_gold_local.py para validación final

---

## Comparación de Scripts

| Característica | test_pipeline_local.py | test_pipeline_janis_api.py | pipeline_with_schema_mapping.py | test_integration_phase_1_2.py | test_silver_to_gold_local.py | test_silver_to_gold_pandas.py |
|----------------|------------------------|----------------------------|----------------------------------|-------------------------------|------------------------------|-------------------------------|
| **Pipeline** | Bronze-to-Silver | Bronze-to-Silver | Bronze-to-Silver + Mapeo | Módulos fusionados | Silver-to-Gold | Silver-to-Gold |
| **Datos** | Simulados | Reales de API | Reales de API | Simulados | Simulados (Silver) | Simulados (Silver) |
| **Framework** | pandas | pandas | pandas | PySpark | PySpark | pandas |
| **Conexión Internet** | No requerida | Requerida | Requerida | No requerida | No requerida | No requerida |
| **Velocidad** | Rápido (~5s) | Medio (~10-15s) | Medio (~15-20s) | Medio (~30s) | Medio (~30s) | Muy rápido (~5s) |
| **Dependencias** | pandas | pandas + requests | pandas + requests | PySpark | PySpark | pandas |
| **Módulos Reales** | Sí (adaptados) | Sí (adaptados) | Sí (simplificados) | Sí | Sí | No (inline) |
| **Agregaciones** | No | No | No | No | Sí (por dimensiones) | Sí (simplificadas) |
| **Validación de Calidad** | Básica | Básica | Básica | Completa | Completa (4 dimensiones) | Completa (simplificada) |
| **Uso Recomendado** | Desarrollo inicial | Validación con datos reales | Validación de mapeo a Redshift | Testing de integración | Testing Silver-to-Gold completo | Desarrollo rápido Silver-to-Gold |
| **Debugging** | Fácil (datos conocidos) | Medio (datos variables) | Medio (mapeo explícito) | Fácil (tests unitarios) | Fácil (datos controlados) | Muy fácil (pandas puro) |

---

## Workflow Recomendado

### 1. Desarrollo Inicial Bronze-to-Silver
```bash
# Usar test_pipeline_local.py para desarrollo rápido
python scripts/test_pipeline_local.py
```

### 2. Validación con Datos Reales Bronze-to-Silver
```bash
# Probar con datos reales de Janis
python scripts/test_pipeline_janis_api.py

# Analizar archivos generados
cat glue/data/janis_order_transformed.csv
```

### 3. Validación de Mapeo de Esquema
```bash
# Probar mapeo completo a tablas Redshift
python scripts/pipeline_with_schema_mapping.py

# Analizar archivos generados por tabla
cat glue/data/order_*_wms_orders.csv
cat glue/data/order_*_wms_order_items.csv
cat glue/data/order_*_wms_order_shipping.csv
```

### 4. Testing de Integración
```bash
# Ejecutar tests de integración
pytest scripts/test_integration_phase_1_2.py -v
```

### 5. Testing Silver-to-Gold ⭐ NUEVO
```bash
# Probar pipeline Silver-to-Gold con datos locales
python scripts/test_silver_to_gold_local.py

# Analizar resultados agregados
cat glue/data/test_gold/*.json
```

### 6. Deployment a AWS Glue
```bash
# Después de validar localmente, deployar a Glue
terraform apply -var-file="environments/dev/terraform.tfvars"
```

---

## Dependencias Requeridas

### Para test_pipeline_local.py
```bash
pip install pandas
```

### Para test_pipeline_janis_api.py
```bash
pip install pandas requests
```

### Para test_integration_phase_1_2.py
```bash
pip install pytest pyspark pandas
```

---

## Próximos Pasos

1. ✅ Scripts de testing creados y documentados
2. ⏭️ Crear tests end-to-end con PySpark
3. ⏭️ Integrar scripts en CI/CD pipeline
4. ⏭️ Crear tests de performance con datasets grandes
5. ⏭️ Documentar casos de uso adicionales

---

## Referencias

- **Guía completa del pipeline:** `Documentacion/GUIA_PIPELINE_Y_TESTING.md`
- **Cómo probar el pipeline:** `Documentacion/COMO_PROBAR_PIPELINE.md`
- **Estado de integración:** `Documentacion/ESTADO_MODULOS_INTEGRACION.md`
- **Resultados de testing:** `Documentacion/RESULTADO_TESTING_FASE_1_1_1_2.md`

---

**Documento creado:** 19 de Febrero, 2026  
**Última actualización:** 19 de Febrero, 2026  
**Estado:** Documentación completa de scripts de testing
