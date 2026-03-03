# Resumen: Pipeline con Mapeo de Esquema

**Fecha:** 19 de Febrero, 2026  
**Estado:** ✅ Completado y Probado

---

## ¿Qué se Logró?

Se creó un pipeline completo que transforma datos de la API de Janis al formato de base de datos usando el mapeo definido en **Schema Definition Janis.csv**.

---

## Flujo del Pipeline

```
API Janis → Mapeo de Campos → Transformaciones → CSV Output
```

1. **Obtiene** datos de Janis API (JSON)
2. **Mapea** campos según Schema Definition CSV
3. **Transforma** datos (limpieza, normalización, tipos)
4. **Genera** 3 archivos CSV + 1 JSON raw

---

## Tablas Generadas

| Tabla | Campos | Completitud | Registros |
|-------|--------|-------------|-----------|
| wms_orders | 26 | 69.2% | 1 |
| wms_order_items | 11 | 90.9% | 2 |
| wms_order_shipping | 12 | 91.7% | 1 |

---

## Ejemplo de Uso

```bash
cd glue
python scripts/pipeline_with_schema_mapping.py
```

**Salida:**
```
glue/data/
├── order_{id}_raw.json              # Datos crudos
├── order_{id}_wms_orders.csv        # Tabla órdenes
├── order_{id}_wms_order_items.csv   # Tabla items
└── order_{id}_wms_order_shipping.csv # Tabla shipping
```

---

## Campos Clave Mapeados

### wms_orders
- vtex_id ← commerceId
- seq_id ← commerceSequentialId
- total ← totalAmount
- status ← status
- date_created ← dateCreated

### wms_order_items
- product ← items[].commerceProductId
- name ← items[].name
- price ← items[].purchasedPrice
- quantity ← items[].purchasedQuantity

### wms_order_shipping
- city ← addresses[].city
- carrier_id ← shippings[].carrierId
- shipping_window_start ← deliveryWindow.initialDate

---

## Transformaciones Aplicadas

✅ Limpieza de espacios en blanco  
✅ Conversión de strings vacíos a NULL  
✅ Normalización de emails (lowercase)  
✅ Conversión automática de tipos numéricos  

---

## Próximos Pasos

1. **Escalar** a múltiples órdenes (paginación)
2. **Migrar** a PySpark para AWS Glue
3. **Escribir** a Iceberg con IcebergWriter
4. **Agregar** más tablas (products, stock, price)

---

## Archivos Relacionados

- **Script:** `glue/scripts/pipeline_with_schema_mapping.py`
- **Mapeo:** `Documentacion/Schema Definition Janis.csv`
- **Docs:** `Documentacion/PIPELINE_CON_MAPEO_ESQUEMA.md`
- **Datos:** `glue/data/order_*`

---

✅ Pipeline funcional con datos reales de Janis API  
✅ Mapeo completo según Schema Definition CSV  
✅ Listo para escalar a producción
