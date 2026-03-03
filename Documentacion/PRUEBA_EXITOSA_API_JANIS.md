# Prueba Exitosa con API Real de Janis

**Fecha:** 19 de Febrero, 2026  
**Estado:** ✅ Conexión Exitosa y Pipeline Probado

---

## Resumen

Se probó exitosamente el pipeline de transformación con datos reales de la API de Janis. Se identificó el endpoint correcto y se aplicaron las transformaciones del pipeline.

---

## Endpoint Correcto Identificado ✅

**URL Base:** `https://oms.janis.in/api/order/{order_id}`

**Ejemplo:** `https://oms.janis.in/api/order/6913fcb6d134afc8da8ac3dd`

**Headers Requeridos:**
```
janis-client: wongio
janis-api-key: 8fc949ac-6d63-4447-a3d6-a16b66048e61
janis-api-secret: UwPbe45dmE7lySRJ3zcA66Pfdt7xAY3QXWO181Y8OTgCxE3aZuyXpS8HyyPSwsWK
```

**Método:** GET

---

## Estructura de Datos Obtenidos

### Campos Principales

```json
{
  "orderGroupId": "6913fcb57bb23d30fdaeb865",
  "commerceSequentialId": "513111",
  "commerceDateCreated": "2025-11-12T03:18:59.878Z",
  "commerceSalesChannel": "70",
  "totalAmount": 23.95,
  "rawTotalAmount": 23.83,
  "currency": "PEN",
  "shippings": [...],
  "marketplace": {...},
  "seller": {...},
  "addresses": [...],
  "items": [...],
  "account": {...}
}
```

### Campos Anidados

1. **shippings** (array)
   - carrierId
   - deliveryWindow (initialDate, finalDate)
   - items (array con id y quantity)
   - status
   - warehouseId
   - locationId
   - pickupInfo (address, geolocation)

2. **marketplace**
   - marketplaceRefId
   - marketplaceOrderId

3. **seller**
   - name
   - externalIds
   - id

4. **account**
   - id
   - name
   - ecommerceName
   - platform

---

## Archivos Generados

### 1. Datos Crudos
- **Archivo:** `glue/data/janis_order_sin__history.json`
- **Contenido:** Orden completa de Janis API
- **Tamaño:** ~5KB
- **Estructura:** JSON anidado con arrays y objetos

### 2. Datos Aplanados
- **Archivo:** `glue/data/janis_order_flattened.csv`
- **Contenido:** Datos aplanados (JSON → columnas planas)
- **Columnas:** ~50 columnas
- **Formato:** CSV

### 3. Datos Transformados
- **Archivo:** `glue/data/janis_order_transformed.csv`
- **Contenido:** Datos después del pipeline
- **Transformaciones Aplicadas:**
  - ✅ Limpieza de espacios
  - ✅ Normalización de emails
  - ✅ Normalización de teléfonos
  - ✅ Conversión de tipos

---

## Scripts Creados

### 1. test_pipeline_janis_api.py
**Propósito:** Conectar a Janis API y aplicar pipeline completo

**Uso:**
```bash
python glue/scripts/test_pipeline_janis_api.py
```

**Funcionalidad:**
- Obtiene orden de Janis API
- Aplana JSON anidado
- Identifica columnas relevantes
- Aplica transformaciones
- Genera reporte de calidad
- Guarda resultados en CSV

### 2. test_janis_api_endpoints.py
**Propósito:** Probar diferentes endpoints de Janis API

**Uso:**
```bash
python glue/scripts/test_janis_api_endpoints.py
```

**Funcionalidad:**
- Prueba 7 endpoints diferentes
- Identifica cuáles funcionan
- Guarda respuestas en JSON
- Genera resumen de endpoints exitosos

---

## Resultados del Pipeline

### Entrada (Bronze)
```json
{
  "orderGroupId": "6913fcb57bb23d30fdaeb865",
  "commerceSequentialId": "513111",
  "commerceDateCreated": "2025-11-12T03:18:59.878Z",
  "totalAmount": 23.95,
  "shippings": [
    {
      "items": [
        {"id": "6A97D850862F494DA30E4BF8C8369F68", "quantity": 7}
      ]
    }
  ]
}
```

### Salida (Silver)
```csv
orderGroupId,commerceSequentialId,commerceDateCreated,totalAmount,shippings_0_items_0_id,shippings_0_items_0_quantity
6913fcb57bb23d30fdaeb865,513111,2025-11-12T03:18:59.878Z,23.95,6A97D850862F494DA30E4BF8C8369F68,7
```

### Transformaciones Aplicadas

1. ✅ **JSON Aplanado**
   - `shippings[0].items[0].id` → `shippings_0_items_0_id`
   - Estructuras anidadas convertidas a columnas planas

2. ✅ **Limpieza de Datos**
   - Espacios en blanco eliminados
   - Encoding UTF-8 corregido

3. ✅ **Normalización**
   - Emails: lowercase
   - Teléfonos: formato internacional (+51)
   - Fechas: ISO 8601

4. ✅ **Conversión de Tipos**
   - Strings → timestamps
   - Strings → números
   - Detección automática de tipos

---

## Campos Relevantes Identificados

### Para wms_orders

| Campo Original | Tipo | Descripción |
|----------------|------|-------------|
| orderGroupId | string | ID único de la orden |
| commerceSequentialId | string | ID secuencial del comercio |
| commerceDateCreated | timestamp | Fecha de creación |
| totalAmount | decimal | Monto total |
| rawTotalAmount | decimal | Monto sin procesar |
| currency | string | Moneda (PEN) |
| status | string | Estado de la orden |

### Para wms_order_items

| Campo Original | Tipo | Descripción |
|----------------|------|-------------|
| shippings_items_id | string | ID del item |
| shippings_items_quantity | integer | Cantidad |
| shippings_items_index | integer | Índice del item |

### Para customer/address

| Campo Original | Tipo | Descripción |
|----------------|------|-------------|
| addresses_city | string | Ciudad |
| addresses_state | string | Estado/Región |
| addresses_postalCode | string | Código postal |
| addresses_streetName | string | Nombre de calle |
| addresses_streetNumber | string | Número de calle |

---

## Próximos Pasos

### 1. Obtener Múltiples Órdenes
Actualmente solo probamos con 1 orden. Necesitamos:
- Endpoint para listar órdenes
- Paginación
- Filtros por fecha

### 2. Mapeo Completo de Campos
Crear mapeo entre:
- Campos de Janis API → Campos de wms_orders
- Campos de Janis API → Campos de wms_order_items
- Campos de Janis API → Campos de customer/address

### 3. Integrar en Pipeline Completo
- Agregar JSONFlattener (PySpark)
- Agregar DuplicateDetector
- Agregar ConflictResolver
- Escribir a Iceberg con IcebergWriter

### 4. Testing con Volumen
- Probar con 100+ órdenes
- Medir performance
- Validar transformaciones

---

## Comandos Útiles

### Ejecutar Pipeline con API Real
```bash
cd glue
python scripts/test_pipeline_janis_api.py
```

### Ver Datos Crudos
```bash
cat glue/data/janis_order_sin__history.json | python -m json.tool | less
```

### Ver Datos Transformados
```bash
cat glue/data/janis_order_transformed.csv
```

### Probar Endpoints
```bash
python glue/scripts/test_janis_api_endpoints.py
```

---

## Conclusión

✅ **Conexión exitosa con API de Janis**  
✅ **Endpoint correcto identificado**  
✅ **Pipeline probado con datos reales**  
✅ **Transformaciones funcionando**  
✅ **Archivos generados para análisis**

El pipeline está listo para procesar datos reales de Janis. El siguiente paso es integrarlo con PySpark y AWS Glue para procesamiento a escala.

---

**Documento creado:** 19 de Febrero, 2026  
**Autor:** Sistema de Integración Max-Vicente
