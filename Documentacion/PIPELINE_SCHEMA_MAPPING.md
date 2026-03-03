# Pipeline con Mapeo de Esquema - Documentación Completa

**Fecha:** 19 de Febrero, 2026  
**Script:** `glue/scripts/pipeline_with_schema_mapping.py`  
**Estado:** ✅ Implementado y Documentado

---

## Resumen Ejecutivo

El script `pipeline_with_schema_mapping.py` implementa un pipeline completo que obtiene datos de la API de Janis y los transforma en el formato de las tablas finales de Redshift (wms_orders, wms_order_items, wms_order_shipping) aplicando mapeos explícitos de campos según el esquema definido.

---

## Propósito

Este script sirve como:
1. **Validador de mapeo de esquema** - Verifica que todos los campos se mapean correctamente
2. **Generador de datos de prueba** - Crea CSVs listos para carga a Redshift
3. **Documentación viva** - Muestra la relación entre API y tablas finales
4. **Herramienta de debugging** - Permite ver datos en cada etapa del pipeline

---

## Arquitectura del Script

### Flujo de Datos

```
API Janis
    ↓
fetch_order_from_api()
    ↓
Datos JSON Crudos
    ↓
┌─────────────────────────────────────┐
│  Mapeo de Esquema                   │
├─────────────────────────────────────┤
│  map_order_to_wms_orders()          │ → wms_orders (1 registro)
│  map_order_to_wms_order_items()     │ → wms_order_items (N registros)
│  map_order_to_wms_order_shipping()  │ → wms_order_shipping (N registros)
└─────────────────────────────────────┘
    ↓
DataFrames Pandas
    ↓
┌─────────────────────────────────────┐
│  Transformaciones del Pipeline      │
├─────────────────────────────────────┤
│  1. DataCleaner                     │
│  2. DataNormalizer                  │
│  3. DataTypeConverter               │
│  4. DataGapHandler                  │
└─────────────────────────────────────┘
    ↓
DataFrames Transformados
    ↓
┌─────────────────────────────────────┐
│  Salida                             │
├─────────────────────────────────────┤
│  - order_{id}_raw.json              │
│  - order_{id}_wms_orders.csv        │
│  - order_{id}_wms_order_items.csv   │
│  - order_{id}_wms_order_shipping.csv│
└─────────────────────────────────────┘
```

---

## Mapeos de Esquema

### 1. wms_orders (27 campos)

Tabla principal que contiene información de la orden.

| Campo Redshift | Campo API Janis | Tipo | Notas |
|----------------|-----------------|------|-------|
| vtex_id | commerceId | string | ID de comercio |
| id | id | string | ID único de orden |
| seq_id | commerceSequentialId | string | ID secuencial |
| ecommerce_account | account.id | string | Cuenta de ecommerce |
| seller_id | seller.id | string | ID del vendedor |
| seller_ecom_id | seller.commerceId | string | ID comercio del vendedor |
| website_name | salesChannelName | string | Nombre del canal |
| customer | customer.id | string | ID del cliente |
| customer_address | addresses[0].id | string | ID de dirección |
| store | statusPerLocation | string | ID de tienda (primer key) |
| sales_channel | salesChannelId | string | ID de canal de ventas |
| invoice_date | invoices[0].dateCreated | timestamp | Fecha de factura |
| invoice_number | invoices[0].number | string | Número de factura |
| invoice_ammount | invoices[0].amount | decimal | Monto de factura |
| product_qty | productsQuantity | integer | Cantidad de productos |
| items_qty | itemsQuantity | integer | Cantidad de items |
| total | totalAmount | decimal | Monto total |
| total_items | totals.items.amount | decimal | Total de items |
| total_discount | totals.discounts.amount | decimal | Total de descuentos |
| total_shipping | totals.shipping.amount | decimal | Total de envío |
| total_original | originalAmount | decimal | Monto original |
| status | status | string | Estado de la orden |
| user_created | userCreated | string | Usuario que creó |
| user_modified | userModified | string | Usuario que modificó |
| date_created | dateCreated | timestamp | Fecha de creación |
| date_picked | steps.picking.dateEnd | timestamp | Fecha de picking |

### 2. wms_order_items (11 campos)

Tabla de items de la orden (relación 1:N con wms_orders).

| Campo Redshift | Campo API Janis | Tipo | Notas |
|----------------|-----------------|------|-------|
| id | items[].id | string | ID del item |
| order_id | id | string | FK a wms_orders |
| sku | items[].skuId | string | SKU del producto |
| product | items[].commerceProductId | string | ID del producto |
| ref_id | items[].refId | string | ID de referencia |
| name | items[].name | string | Nombre del producto |
| list_price | items[].purchasedListPrice | decimal | Precio de lista |
| price | items[].purchasedPrice | decimal | Precio de compra |
| quantity | items[].purchasedQuantity | integer | Cantidad comprada |
| measurement_unit | items[].sellingMeasurementUnit | string | Unidad de medida |
| unit_multiplier | items[].sellingUnitMultiplier | decimal | Multiplicador de unidad |

### 3. wms_order_shipping (11 campos)

Tabla de envíos de la orden (relación 1:N con wms_orders).

| Campo Redshift | Campo API Janis | Tipo | Notas |
|----------------|-----------------|------|-------|
| id | shippings[].id | string | ID del shipping |
| order_id | id | string | FK a wms_orders |
| city | addresses[].city | string | Ciudad de envío |
| neighborhood | addresses[].neighborhood | string | Barrio |
| complement | addresses[].complement | string | Complemento de dirección |
| lat | addresses[].geolocation[1] | decimal | Latitud |
| lng | addresses[].geolocation[0] | decimal | Longitud |
| carrier_id | shippings[].carrierId | string | ID del transportista |
| shipping_window_start | shippings[].deliveryWindow.initialDate | timestamp | Inicio de ventana |
| shipping_window_end | shippings[].deliveryWindow.finalDate | timestamp | Fin de ventana |
| shipped_date_start | shippings[].dateModified | timestamp | Fecha de envío inicio |
| shipped_date_end | shippings[].dateModified | timestamp | Fecha de envío fin |

---

## Funciones Principales

### fetch_order_from_api(order_id)

Obtiene una orden de la API de Janis.

**Parámetros:**
- `order_id` (string): ID de la orden a obtener

**Retorna:**
- `dict`: Datos de la orden en formato JSON
- `None`: Si hay error en la conexión

**Ejemplo:**
```python
order_data = fetch_order_from_api("6913fcb6d134afc8da8ac3dd")
```

### extract_nested_value(data, path)

Extrae un valor de un objeto JSON anidado usando notación de punto.

**Parámetros:**
- `data` (dict): Diccionario con los datos
- `path` (string): Ruta al valor (ej: 'seller.id', 'items[0].name')

**Retorna:**
- Valor extraído o `None` si no existe

**Ejemplos:**
```python
# Acceso simple
value = extract_nested_value(data, 'seller.id')

# Acceso a array
value = extract_nested_value(data, 'items[0].name')

# Acceso anidado
value = extract_nested_value(data, 'account.seller.id')
```

### map_order_to_wms_orders(order_data)

Mapea datos de orden de Janis API a formato wms_orders.

**Parámetros:**
- `order_data` (dict): Datos de la orden desde la API

**Retorna:**
- `dict`: Datos mapeados a formato wms_orders (27 campos)

### map_order_to_wms_order_items(order_data)

Mapea datos de items de orden a formato wms_order_items.

**Parámetros:**
- `order_data` (dict): Datos de la orden desde la API

**Retorna:**
- `list`: Lista de items mapeados (N registros)

### map_order_to_wms_order_shipping(order_data)

Mapea datos de shipping a formato wms_order_shipping.

**Parámetros:**
- `order_data` (dict): Datos de la orden desde la API

**Retorna:**
- `list`: Lista de shippings mapeados (N registros)

### apply_transformations(df, table_name)

Aplica transformaciones básicas a un DataFrame usando pandas (versión simplificada).

**Parámetros:**
- `df` (DataFrame): DataFrame con los datos
- `table_name` (string): Nombre de la tabla (para logging)

**Retorna:**
- `DataFrame`: DataFrame transformado

**Transformaciones aplicadas:**
1. **Limpieza de datos** (pandas nativo):
   - Trim de espacios en blanco de columnas string
   - Conversión de strings vacíos a None
   - Conversión de espacios múltiples a None

2. **Normalización básica** (pandas nativo):
   - Emails a lowercase (sin validación compleja)

3. **Conversión de tipos básica** (pandas nativo):
   - Columnas con 'qty', 'quantity', 'count' → numérico
   - Columnas con 'price', 'amount', 'total' → numérico
   - Conversión con `errors='ignore'` para robustez

**Nota:** Esta es una versión simplificada que no requiere los módulos completos de transformación. Para transformaciones completas con validación robusta, usar los módulos integrados (DataCleaner, DataNormalizer, DataTypeConverter, DataGapHandler).

---

## Uso del Script

### Ejecución Básica

```bash
cd glue
python scripts/pipeline_with_schema_mapping.py
```

### Cambiar Order ID

Editar línea 434 del script:

```python
if __name__ == "__main__":
    # Cambiar este ID por el que desees probar
    ORDER_ID = "6913fcb6d134afc8da8ac3dd"
    
    run_pipeline(ORDER_ID)
```

### Agregar Nuevos Campos al Mapeo

Para agregar campos adicionales, editar los diccionarios de mapeo:

```python
WMS_ORDERS_MAPPING = {
    # Campos existentes...
    'nuevo_campo_redshift': 'ruta.en.api.janis',
}
```

---

## Archivos Generados

Para cada orden procesada, el script genera 4 archivos:

### 1. order_{id}_raw.json

Datos crudos tal como vienen de la API de Janis.

**Ubicación:** `glue/data/order_{id}_raw.json`  
**Formato:** JSON  
**Uso:** Debugging, análisis de estructura original

### 2. order_{id}_wms_orders.csv

Tabla principal de órdenes transformada.

**Ubicación:** `glue/data/order_{id}_wms_orders.csv`  
**Formato:** CSV  
**Registros:** 1 por orden  
**Columnas:** 27  
**Uso:** Carga a tabla wms_orders en Redshift

### 3. order_{id}_wms_order_items.csv

Tabla de items de orden transformada.

**Ubicación:** `glue/data/order_{id}_wms_order_items.csv`  
**Formato:** CSV  
**Registros:** N (1 por item)  
**Columnas:** 11  
**Uso:** Carga a tabla wms_order_items en Redshift

### 4. order_{id}_wms_order_shipping.csv

Tabla de envíos transformada.

**Ubicación:** `glue/data/order_{id}_wms_order_shipping.csv`  
**Formato:** CSV  
**Registros:** N (1 por shipping)  
**Columnas:** 11  
**Uso:** Carga a tabla wms_order_shipping en Redshift

---

## Reporte de Calidad

El script genera un reporte detallado de calidad de datos por tabla:

```
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
```

---

## Casos de Uso

### 1. Validación de Mapeo de Esquema

Verificar que todos los campos de la API se mapean correctamente a las tablas de Redshift.

```bash
python scripts/pipeline_with_schema_mapping.py
# Revisar archivos CSV generados
cat glue/data/order_*_wms_orders.csv
```

### 2. Generación de Datos de Prueba

Crear CSVs con datos reales para testing de carga a Redshift.

```bash
# Generar datos de múltiples órdenes
for order_id in "order1" "order2" "order3"; do
    # Editar ORDER_ID en el script
    python scripts/pipeline_with_schema_mapping.py
done
```

### 3. Documentación de Transformaciones

Entender qué transformaciones se aplican a cada campo.

```bash
# Comparar raw vs transformed
diff glue/data/order_*_raw.json glue/data/order_*_wms_orders.csv
```

### 4. Análisis de Completitud de Datos

Identificar campos faltantes o con problemas de calidad.

```bash
python scripts/pipeline_with_schema_mapping.py
# Revisar reporte de calidad en la salida
```

**Nota sobre Transformaciones:** El script usa transformaciones básicas con pandas nativo para facilitar testing sin dependencias complejas. En el pipeline de producción en AWS Glue, se usarán los módulos completos integrados (DataCleaner, DataNormalizer, DataTypeConverter, DataGapHandler) con validación robusta y manejo de errores completo.

---

## Limitaciones Conocidas

### 1. Arrays

Actualmente toma solo el primer elemento de arrays:
- `addresses[0]` - Primera dirección
- `invoices[0]` - Primera factura

**Mejora futura:** Explotar arrays completos en múltiples registros.

### 2. Campos Especiales

El campo `store` requiere procesamiento especial:
```python
# Extrae primer locationId del objeto statusPerLocation
status_per_loc = order_data.get('statusPerLocation', {})
if status_per_loc:
    mapped_data['store'] = list(status_per_loc.keys())[0]
```

### 3. Pandas vs PySpark

El script usa pandas para simplicidad. En producción con AWS Glue, se usará PySpark.

**Diferencias clave:**
- **Transformaciones:** Script usa pandas nativo (simplificado), producción usa módulos completos con PySpark
- **Validación:** Script tiene validación básica, producción tiene validación robusta
- **Escalabilidad:** Pandas para datasets pequeños, PySpark para procesamiento distribuido
- **Módulos:** Script no requiere módulos integrados, producción usa DataCleaner, DataNormalizer, DataTypeConverter, DataGapHandler completos

---

## Próximos Pasos

### Corto Plazo

1. ✅ Script implementado y documentado
2. ⏭️ Probar con múltiples órdenes diferentes
3. ⏭️ Validar completitud de mapeo de campos
4. ⏭️ Ajustar mapeos según feedback

### Mediano Plazo

1. ⏭️ Migrar a PySpark para AWS Glue
2. ⏭️ Implementar explosión completa de arrays
3. ⏭️ Agregar validación de esquema
4. ⏭️ Integrar con IcebergWriter

### Largo Plazo

1. ⏭️ Automatizar en AWS Glue Job
2. ⏭️ Agregar monitoreo de calidad
3. ⏭️ Implementar alertas por campos faltantes
4. ⏭️ Crear dashboard de completitud

---

## Referencias

### Documentación Relacionada

- **Guía de testing:** `Documentacion/COMO_PROBAR_PIPELINE.md`
- **Scripts disponibles:** `Documentacion/SCRIPTS_TESTING_DISPONIBLES.md`
- **Prueba API Janis:** `Documentacion/PRUEBA_EXITOSA_API_JANIS.md`
- **Guía del pipeline:** `Documentacion/GUIA_PIPELINE_Y_TESTING.md`

### Código Relacionado

- **Script principal:** `glue/scripts/pipeline_with_schema_mapping.py`
- **Test local:** `glue/scripts/test_pipeline_local.py`
- **Test API:** `glue/scripts/test_pipeline_janis_api.py`
- **Módulos:** `glue/modules/`

---

**Documento creado:** 19 de Febrero, 2026  
**Última actualización:** 19 de Febrero, 2026  
**Estado:** Documentación completa del pipeline con mapeo de esquema
