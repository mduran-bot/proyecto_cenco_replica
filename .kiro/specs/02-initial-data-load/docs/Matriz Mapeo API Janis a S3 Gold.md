# Matriz de Mapeo: API Janis → S3 Gold

**Fecha**: 17 de Febrero de 2026  
**Versión**: 1.0  
**Estado**: Draft - En Revisión

---

## Resumen Ejecutivo

Este documento define el mapeo completo entre las entidades de la API de Janis y la estructura de archivos Parquet en S3 Gold, asegurando compatibilidad total con el sistema de Redshift existente de Cencosud.

### Objetivo

Transformar datos de la API REST de Janis (formato JSON) en archivos Parquet estructurados en S3 Gold que puedan ser consumidos directamente por Redshift sin modificaciones al sistema actual.

### Estructura de Destino

```
s3://cencosud.test.super.peru.analytics/
  ExternalAccess/
    janis_smk_pe/
      automatico/
        {tabla}/
          year=YYYY/month=MM/day=DD/
            part-{n}-{uuid}.c000.snappy.parquet
```

---

## Convenciones de Nomenclatura

### Naming Patterns

| Elemento | Patrón | Ejemplo |
|----------|--------|---------|
| Tabla | `{entidad_plural}` | `orders`, `products`, `stores` |
| Archivo | `part-{seq:05d}-{uuid}.c000.snappy.parquet` | `part-00000-a1b2c3d4.c000.snappy.parquet` |
| Partición | `year={YYYY}/month={MM}/day={DD}` | `year=2026/month=02/day=17` |
| Campo ID | `{entidad}_id` | `order_id`, `product_id` |
| Campo Timestamp | `{accion}_at` o `{accion}_timestamp` | `created_at`, `modified_at` |

### Tipos de Datos Parquet

| Tipo API Janis | Tipo Parquet | Tipo Redshift | Notas |
|----------------|--------------|---------------|-------|
| `string` | `STRING` | `VARCHAR(n)` | Longitud según campo |
| `integer` | `INT64` | `BIGINT` | Para IDs y contadores |
| `number` (decimal) | `DECIMAL(p,s)` | `NUMERIC(p,s)` | Preservar precisión |
| `boolean` | `BOOLEAN` | `SMALLINT` | Convertir a 0/1 en Redshift |
| `timestamp` (Unix) | `TIMESTAMP` | `TIMESTAMP` | Convertir a ISO 8601 UTC |
| `object` (JSON) | `STRING` | `VARCHAR(65535)` | Serializar como JSON string |
| `array` | `STRING` | `VARCHAR(65535)` | Serializar como JSON array |
| `null` | `NULL` | `NULL` | Mantener nullability |

---


## Entidad 1: Orders (Órdenes)

### Información General

| Atributo | Valor |
|----------|-------|
| **Endpoint API** | `GET /api/v2/orders` |
| **Webhook** | `POST /webhook/order/created`, `/webhook/order/updated` |
| **Tabla S3 Gold** | `janis_smk_pe/automatico/orders/` |
| **Partición Base** | `date_created` (fecha de creación de la orden) |
| **Frecuencia Actualización** | Tiempo real (webhooks) + Polling cada 5 minutos |
| **Volumen Estimado** | ~50,000 órdenes/día |
| **Tamaño Archivo Target** | 64-128 MB |

### Esquema API Janis (JSON)

```json
{
  "order_id": "ORD-12345",
  "order_number": "WEB-2026-001234",
  "status": "pending",
  "date_created": 1708200000,
  "date_modified": 1708200300,
  "store_id": "STORE-001",
  "customer_id": "CUST-98765",
  "customer_email": "customer@example.com",
  "customer_phone": "+51987654321",
  "delivery_type": "home_delivery",
  "delivery_address": {
    "street": "Av. Principal 123",
    "city": "Lima",
    "district": "Miraflores",
    "postal_code": "15074"
  },
  "payment_method": "credit_card",
  "payment_status": "paid",
  "subtotal": 150.50,
  "tax": 27.09,
  "shipping_cost": 10.00,
  "discount": 5.00,
  "total": 182.59,
  "currency": "PEN",
  "items_count": 5,
  "items_picked": 4,
  "items_substituted": 1,
  "picking_status": "completed",
  "shipping_status": "in_transit",
  "notes": "Entregar en la tarde",
  "metadata": {
    "source": "web",
    "campaign_id": "PROMO-2026"
  }
}
```

### Esquema Parquet S3 Gold

| Campo Parquet | Tipo Parquet | Tipo Redshift | Origen API Janis | Transformación | Nullable | Notas |
|---------------|--------------|---------------|------------------|----------------|----------|-------|
| `order_id` | `STRING` | `VARCHAR(50)` | `order_id` | Directo | NO | PK |
| `order_number` | `STRING` | `VARCHAR(50)` | `order_number` | Directo | NO | Business key |
| `status` | `STRING` | `VARCHAR(30)` | `status` | Directo | NO | Valores: pending, confirmed, picking, completed, cancelled |
| `date_created` | `TIMESTAMP` | `TIMESTAMP` | `date_created` | Unix → ISO 8601 UTC | NO | Partición base |
| `date_modified` | `TIMESTAMP` | `TIMESTAMP` | `date_modified` | Unix → ISO 8601 UTC | NO | |
| `store_id` | `STRING` | `VARCHAR(50)` | `store_id` | Directo | NO | FK a stores |
| `customer_id` | `STRING` | `VARCHAR(50)` | `customer_id` | Directo | SÍ | FK a customers |
| `customer_email` | `STRING` | `VARCHAR(255)` | `customer_email` | Lowercase, trim | SÍ | |
| `customer_phone` | `STRING` | `VARCHAR(20)` | `customer_phone` | Normalizar formato | SÍ | |
| `delivery_type` | `STRING` | `VARCHAR(30)` | `delivery_type` | Directo | NO | home_delivery, store_pickup |
| `delivery_street` | `STRING` | `VARCHAR(255)` | `delivery_address.street` | Extraer de objeto | SÍ | |
| `delivery_city` | `STRING` | `VARCHAR(100)` | `delivery_address.city` | Extraer de objeto | SÍ | |
| `delivery_district` | `STRING` | `VARCHAR(100)` | `delivery_address.district` | Extraer de objeto | SÍ | |
| `delivery_postal_code` | `STRING` | `VARCHAR(10)` | `delivery_address.postal_code` | Extraer de objeto | SÍ | |
| `payment_method` | `STRING` | `VARCHAR(30)` | `payment_method` | Directo | NO | |
| `payment_status` | `STRING` | `VARCHAR(30)` | `payment_status` | Directo | NO | |
| `subtotal` | `DECIMAL(18,2)` | `NUMERIC(18,2)` | `subtotal` | Directo | NO | |
| `tax` | `DECIMAL(18,2)` | `NUMERIC(18,2)` | `tax` | Directo | NO | |
| `shipping_cost` | `DECIMAL(18,2)` | `NUMERIC(18,2)` | `shipping_cost` | Directo | NO | |
| `discount` | `DECIMAL(18,2)` | `NUMERIC(18,2)` | `discount` | Directo | NO | |
| `total` | `DECIMAL(18,2)` | `NUMERIC(18,2)` | `total` | Directo | NO | |
| `currency` | `STRING` | `VARCHAR(3)` | `currency` | Directo | NO | ISO 4217 |
| `items_count` | `INT64` | `BIGINT` | `items_count` | Directo | NO | |
| `items_picked` | `INT64` | `BIGINT` | `items_picked` | Directo | SÍ | |
| `items_substituted` | `INT64` | `BIGINT` | `items_substituted` | Directo | SÍ | |
| `picking_status` | `STRING` | `VARCHAR(30)` | `picking_status` | Directo | SÍ | |
| `shipping_status` | `STRING` | `VARCHAR(30)` | `shipping_status` | Directo | SÍ | |
| `notes` | `STRING` | `VARCHAR(1000)` | `notes` | Directo | SÍ | |
| `metadata_json` | `STRING` | `VARCHAR(65535)` | `metadata` | JSON.stringify() | SÍ | Serializar objeto completo |
| `source_type` | `STRING` | `VARCHAR(20)` | N/A | Constante: "webhook" o "polling" | NO | Metadata de ingesta |
| `ingestion_timestamp` | `TIMESTAMP` | `TIMESTAMP` | N/A | CURRENT_TIMESTAMP | NO | Metadata de ingesta |
| `processing_job_id` | `STRING` | `VARCHAR(100)` | N/A | Glue Job ID | NO | Metadata de procesamiento |

### Campos Calculados (Agregados en Gold)

| Campo Calculado | Tipo | Fórmula | Propósito |
|-----------------|------|---------|-----------|
| `items_qty_missing` | `INT64` | `items_count - COALESCE(items_picked, 0)` | Items no encontrados |
| `total_changes` | `DECIMAL(18,2)` | `total - subtotal` | Cambios en total (tax + shipping - discount) |
| `is_complete` | `BOOLEAN` | `items_picked = items_count` | Orden completa sin faltantes |
| `has_substitutions` | `BOOLEAN` | `items_substituted > 0` | Tiene productos sustituidos |

### Ejemplo de Transformación

**Input (API JSON)**:
```json
{
  "order_id": "ORD-12345",
  "date_created": 1708200000,
  "total": 182.59,
  "delivery_address": {
    "street": "Av. Principal 123",
    "city": "Lima"
  }
}
```

**Output (Parquet)**:
```
order_id: "ORD-12345"
date_created: 2026-02-17T15:33:20Z
total: 182.59
delivery_street: "Av. Principal 123"
delivery_city: "Lima"
source_type: "webhook"
ingestion_timestamp: 2026-02-17T15:35:00Z
```

---


## Entidad 2: Order Items (Items de Orden)

### Información General

| Atributo | Valor |
|----------|-------|
| **Endpoint API** | `GET /api/v2/orders/{order_id}/items` |
| **Webhook** | Incluido en webhook de order |
| **Tabla S3 Gold** | `janis_smk_pe/automatico/order_items/` |
| **Partición Base** | `date_created` (de la orden padre) |
| **Frecuencia Actualización** | Tiempo real + Polling cada 5 minutos |
| **Volumen Estimado** | ~250,000 items/día (5 items promedio por orden) |
| **Relación** | N:1 con Orders |

### Esquema API Janis (JSON)

```json
{
  "item_id": "ITEM-67890",
  "order_id": "ORD-12345",
  "product_id": "PROD-111",
  "sku": "SKU-ABC-123",
  "product_name": "Leche Entera 1L",
  "quantity_ordered": 2,
  "quantity_picked": 2,
  "quantity_substituted": 0,
  "substitute_product_id": null,
  "substitute_type": null,
  "unit_price": 5.50,
  "subtotal": 11.00,
  "discount": 0.50,
  "total": 10.50,
  "picking_status": "picked",
  "picker_id": "PICKER-001",
  "picked_at": 1708200600,
  "notes": "Producto en buen estado"
}
```

### Esquema Parquet S3 Gold

| Campo Parquet | Tipo Parquet | Tipo Redshift | Origen API | Transformación | Nullable |
|---------------|--------------|---------------|------------|----------------|----------|
| `item_id` | `STRING` | `VARCHAR(50)` | `item_id` | Directo | NO |
| `order_id` | `STRING` | `VARCHAR(50)` | `order_id` | Directo | NO |
| `product_id` | `STRING` | `VARCHAR(50)` | `product_id` | Directo | NO |
| `sku` | `STRING` | `VARCHAR(50)` | `sku` | Directo | NO |
| `product_name` | `STRING` | `VARCHAR(255)` | `product_name` | Directo | NO |
| `quantity_ordered` | `INT64` | `BIGINT` | `quantity_ordered` | Directo | NO |
| `quantity_picked` | `INT64` | `BIGINT` | `quantity_picked` | Directo | SÍ |
| `quantity_substituted` | `INT64` | `BIGINT` | `quantity_substituted` | Directo | SÍ |
| `substitute_product_id` | `STRING` | `VARCHAR(50)` | `substitute_product_id` | Directo | SÍ |
| `substitute_type` | `STRING` | `VARCHAR(30)` | `substitute_type` | Directo | SÍ |
| `unit_price` | `DECIMAL(18,2)` | `NUMERIC(18,2)` | `unit_price` | Directo | NO |
| `subtotal` | `DECIMAL(18,2)` | `NUMERIC(18,2)` | `subtotal` | Directo | NO |
| `discount` | `DECIMAL(18,2)` | `NUMERIC(18,2)` | `discount` | Directo | NO |
| `total` | `DECIMAL(18,2)` | `NUMERIC(18,2)` | `total` | Directo | NO |
| `picking_status` | `STRING` | `VARCHAR(30)` | `picking_status` | Directo | SÍ |
| `picker_id` | `STRING` | `VARCHAR(50)` | `picker_id` | Directo | SÍ |
| `picked_at` | `TIMESTAMP` | `TIMESTAMP` | `picked_at` | Unix → ISO 8601 | SÍ |
| `notes` | `STRING` | `VARCHAR(1000)` | `notes` | Directo | SÍ |
| `date_created` | `TIMESTAMP` | `TIMESTAMP` | De order padre | Heredado | NO |

### Campos Calculados

| Campo | Tipo | Fórmula |
|-------|------|---------|
| `quantity_missing` | `INT64` | `quantity_ordered - COALESCE(quantity_picked, 0)` |
| `is_substituted` | `BOOLEAN` | `substitute_product_id IS NOT NULL` |
| `is_complete` | `BOOLEAN` | `quantity_picked = quantity_ordered` |

---

## Entidad 3: Products (Productos)

### Información General

| Atributo | Valor |
|----------|-------|
| **Endpoint API** | `GET /api/v2/products` |
| **Webhook** | `POST /webhook/product/updated` |
| **Tabla S3 Gold** | `janis_smk_pe/automatico/products/` |
| **Partición Base** | `date_modified` |
| **Frecuencia Actualización** | Polling cada 1 hora |
| **Volumen Estimado** | ~100,000 productos |

### Esquema API Janis (JSON)

```json
{
  "product_id": "PROD-111",
  "sku": "SKU-ABC-123",
  "name": "Leche Entera 1L",
  "description": "Leche entera pasteurizada",
  "brand_id": "BRAND-001",
  "brand_name": "Gloria",
  "category_id": "CAT-DAIRY",
  "category_name": "Lácteos",
  "supplier_id": "SUPP-001",
  "supplier_name": "Distribuidora ABC",
  "ean": "7750182001234",
  "price": 5.50,
  "cost": 3.80,
  "currency": "PEN",
  "unit_type": "unit",
  "unit_multiplier": 1,
  "weight_kg": 1.03,
  "volume_liters": 1.0,
  "is_active": true,
  "is_available": true,
  "stock_quantity": 150,
  "min_stock": 20,
  "max_stock": 500,
  "status": "active",
  "date_created": 1700000000,
  "date_modified": 1708200000,
  "metadata": {
    "nutritional_info": {},
    "allergens": ["lactose"]
  }
}
```

### Esquema Parquet S3 Gold

| Campo Parquet | Tipo Parquet | Tipo Redshift | Origen API | Nullable |
|---------------|--------------|---------------|------------|----------|
| `product_id` | `STRING` | `VARCHAR(50)` | `product_id` | NO |
| `sku` | `STRING` | `VARCHAR(50)` | `sku` | NO |
| `name` | `STRING` | `VARCHAR(255)` | `name` | NO |
| `description` | `STRING` | `VARCHAR(1000)` | `description` | SÍ |
| `brand_id` | `STRING` | `VARCHAR(50)` | `brand_id` | SÍ |
| `brand_name` | `STRING` | `VARCHAR(100)` | `brand_name` | SÍ |
| `category_id` | `STRING` | `VARCHAR(50)` | `category_id` | SÍ |
| `category_name` | `STRING` | `VARCHAR(100)` | `category_name` | SÍ |
| `supplier_id` | `STRING` | `VARCHAR(50)` | `supplier_id` | SÍ |
| `supplier_name` | `STRING` | `VARCHAR(255)` | `supplier_name` | SÍ |
| `ean` | `STRING` | `VARCHAR(20)` | `ean` | SÍ |
| `price` | `DECIMAL(18,2)` | `NUMERIC(18,2)` | `price` | NO |
| `cost` | `DECIMAL(18,2)` | `NUMERIC(18,2)` | `cost` | SÍ |
| `currency` | `STRING` | `VARCHAR(3)` | `currency` | NO |
| `unit_type` | `STRING` | `VARCHAR(20)` | `unit_type` | NO |
| `unit_multiplier` | `INT64` | `BIGINT` | `unit_multiplier` | NO |
| `weight_kg` | `DECIMAL(10,3)` | `NUMERIC(10,3)` | `weight_kg` | SÍ |
| `volume_liters` | `DECIMAL(10,3)` | `NUMERIC(10,3)` | `volume_liters` | SÍ |
| `is_active` | `BOOLEAN` | `SMALLINT` | `is_active` | NO |
| `is_available` | `BOOLEAN` | `SMALLINT` | `is_available` | NO |
| `stock_quantity` | `INT64` | `BIGINT` | `stock_quantity` | SÍ |
| `min_stock` | `INT64` | `BIGINT` | `min_stock` | SÍ |
| `max_stock` | `INT64` | `BIGINT` | `max_stock` | SÍ |
| `status` | `STRING` | `VARCHAR(30)` | `status` | NO |
| `date_created` | `TIMESTAMP` | `TIMESTAMP` | `date_created` | NO |
| `date_modified` | `TIMESTAMP` | `TIMESTAMP` | `date_modified` | NO |
| `metadata_json` | `STRING` | `VARCHAR(65535)` | `metadata` | SÍ |

---

## Entidad 4: Stores (Tiendas)

### Información General

| Atributo | Valor |
|----------|-------|
| **Endpoint API** | `GET /api/v2/stores` |
| **Tabla S3 Gold** | `janis_smk_pe/automatico/stores/` |
| **Partición Base** | `date_modified` |
| **Frecuencia Actualización** | Polling cada 24 horas |
| **Volumen Estimado** | ~50 tiendas |

### Esquema Parquet S3 Gold

| Campo | Tipo Parquet | Tipo Redshift | Origen API | Nullable |
|-------|--------------|---------------|------------|----------|
| `store_id` | `STRING` | `VARCHAR(50)` | `store_id` | NO |
| `store_code` | `STRING` | `VARCHAR(20)` | `store_code` | NO |
| `name` | `STRING` | `VARCHAR(255)` | `name` | NO |
| `type` | `STRING` | `VARCHAR(30)` | `type` | NO |
| `region` | `STRING` | `VARCHAR(100)` | `region` | SÍ |
| `city` | `STRING` | `VARCHAR(100)` | `city` | SÍ |
| `district` | `STRING` | `VARCHAR(100)` | `district` | SÍ |
| `address` | `STRING` | `VARCHAR(500)` | `address` | SÍ |
| `postal_code` | `STRING` | `VARCHAR(10)` | `postal_code` | SÍ |
| `phone` | `STRING` | `VARCHAR(20)` | `phone` | SÍ |
| `email` | `STRING` | `VARCHAR(255)` | `email` | SÍ |
| `is_active` | `BOOLEAN` | `SMALLINT` | `is_active` | NO |
| `supports_delivery` | `BOOLEAN` | `SMALLINT` | `supports_delivery` | NO |
| `supports_pickup` | `BOOLEAN` | `SMALLINT` | `supports_pickup` | NO |
| `date_created` | `TIMESTAMP` | `TIMESTAMP` | `date_created` | NO |
| `date_modified` | `TIMESTAMP` | `TIMESTAMP` | `date_modified` | NO |

---

## Entidad 5: Stock (Inventario)

### Información General

| Atributo | Valor |
|----------|-------|
| **Endpoint API** | `GET /api/v2/stock` |
| **Tabla S3 Gold** | `janis_smk_pe/automatico/stock/` |
| **Partición Base** | `snapshot_date` (fecha del snapshot) |
| **Frecuencia Actualización** | Polling cada 10 minutos |
| **Volumen Estimado** | ~500,000 registros por snapshot |

### Esquema Parquet S3 Gold

| Campo | Tipo Parquet | Tipo Redshift | Origen API | Nullable |
|-------|--------------|---------------|------------|----------|
| `stock_id` | `STRING` | `VARCHAR(50)` | Generado: `{product_id}_{store_id}_{date}` | NO |
| `product_id` | `STRING` | `VARCHAR(50)` | `product_id` | NO |
| `sku` | `STRING` | `VARCHAR(50)` | `sku` | NO |
| `store_id` | `STRING` | `VARCHAR(50)` | `store_id` | NO |
| `quantity` | `INT64` | `BIGINT` | `quantity` | NO |
| `reserved_quantity` | `INT64` | `BIGINT` | `reserved_quantity` | SÍ |
| `available_quantity` | `INT64` | `BIGINT` | `available_quantity` | NO |
| `unit_cost` | `DECIMAL(18,2)` | `NUMERIC(18,2)` | `unit_cost` | SÍ |
| `total_value` | `DECIMAL(18,2)` | `NUMERIC(18,2)` | `total_value` | SÍ |
| `location` | `STRING` | `VARCHAR(100)` | `location` | SÍ |
| `last_movement_date` | `TIMESTAMP` | `TIMESTAMP` | `last_movement_date` | SÍ |
| `snapshot_date` | `TIMESTAMP` | `TIMESTAMP` | CURRENT_TIMESTAMP | NO |

---

## Entidad 6: Prices (Precios)

### Información General

| Atributo | Valor |
|----------|-------|
| **Endpoint API** | `GET /api/v2/prices` |
| **Tabla S3 Gold** | `janis_smk_pe/automatico/prices/` |
| **Partición Base** | `effective_date` |
| **Frecuencia Actualización** | Polling cada 30 minutos |
| **Volumen Estimado** | ~100,000 registros por actualización |

### Esquema Parquet S3 Gold

| Campo | Tipo Parquet | Tipo Redshift | Origen API | Nullable |
|-------|--------------|---------------|------------|----------|
| `price_id` | `STRING` | `VARCHAR(50)` | Generado | NO |
| `product_id` | `STRING` | `VARCHAR(50)` | `product_id` | NO |
| `store_id` | `STRING` | `VARCHAR(50)` | `store_id` | SÍ |
| `price_type` | `STRING` | `VARCHAR(30)` | `price_type` | NO |
| `price` | `DECIMAL(18,2)` | `NUMERIC(18,2)` | `price` | NO |
| `cost` | `DECIMAL(18,2)` | `NUMERIC(18,2)` | `cost` | SÍ |
| `currency` | `STRING` | `VARCHAR(3)` | `currency` | NO |
| `effective_date` | `TIMESTAMP` | `TIMESTAMP` | `effective_date` | NO |
| `expiration_date` | `TIMESTAMP` | `TIMESTAMP` | `expiration_date` | SÍ |
| `is_active` | `BOOLEAN` | `SMALLINT` | `is_active` | NO |
| `date_modified` | `TIMESTAMP` | `TIMESTAMP` | `date_modified` | NO |

---


## Resumen de Transformaciones por Tipo

### Conversiones de Timestamps

**Regla General**: Todos los timestamps Unix (epoch) deben convertirse a ISO 8601 UTC

```python
# Ejemplo de conversión
def convert_unix_to_iso8601(unix_timestamp):
    """
    Convierte Unix timestamp a ISO 8601 UTC
    Input: 1708200000 (int)
    Output: "2026-02-17T15:33:20Z" (string)
    """
    from datetime import datetime
    return datetime.utcfromtimestamp(unix_timestamp).strftime('%Y-%m-%dT%H:%M:%SZ')
```

**Campos Afectados**:
- `date_created`
- `date_modified`
- `picked_at`
- `last_movement_date`
- `effective_date`
- `expiration_date`

### Conversiones de Booleanos

**Regla**: En Parquet mantener como BOOLEAN, en Redshift convertir a SMALLINT (0/1)

```python
def convert_boolean_for_redshift(value):
    """
    Convierte boolean a SMALLINT para Redshift
    Input: true/false (boolean)
    Output: 1/0 (int)
    """
    return 1 if value else 0
```

**Campos Afectados**:
- `is_active`
- `is_available`
- `supports_delivery`
- `supports_pickup`
- Todos los campos calculados booleanos

### Normalización de Strings

**Reglas**:
1. Trim whitespace de inicio y fin
2. Emails a lowercase
3. Teléfonos a formato estándar

```python
def normalize_string(value, field_type='default'):
    """
    Normaliza strings según tipo de campo
    """
    if value is None:
        return None
    
    value = value.strip()
    
    if field_type == 'email':
        return value.lower()
    elif field_type == 'phone':
        # Normalizar a formato +51XXXXXXXXX
        return normalize_phone_pe(value)
    
    return value
```

### Serialización de Objetos JSON

**Regla**: Objetos y arrays JSON se serializan como strings

```python
import json

def serialize_json_field(obj):
    """
    Serializa objeto/array JSON a string
    Input: {"key": "value"} (dict)
    Output: '{"key":"value"}' (string)
    """
    if obj is None:
        return None
    return json.dumps(obj, ensure_ascii=False)
```

**Campos Afectados**:
- `metadata_json`
- `delivery_address` (se descompone en campos individuales)

### Extracción de Objetos Anidados

**Regla**: Objetos anidados se descomponen en campos planos

```python
def flatten_address(address_obj):
    """
    Descompone objeto de dirección en campos individuales
    Input: {"street": "Av. Principal 123", "city": "Lima"}
    Output: {
        "delivery_street": "Av. Principal 123",
        "delivery_city": "Lima",
        ...
    }
    """
    if address_obj is None:
        return {}
    
    return {
        "delivery_street": address_obj.get("street"),
        "delivery_city": address_obj.get("city"),
        "delivery_district": address_obj.get("district"),
        "delivery_postal_code": address_obj.get("postal_code")
    }
```

---

## Metadata de Ingesta

### Campos Estándar de Metadata

Todos los archivos Parquet en S3 Gold deben incluir estos campos de metadata:

| Campo | Tipo | Descripción | Ejemplo |
|-------|------|-------------|---------|
| `source_type` | `STRING` | Origen de los datos | "webhook", "polling", "initial_load" |
| `ingestion_timestamp` | `TIMESTAMP` | Momento de ingesta | "2026-02-17T15:35:00Z" |
| `processing_job_id` | `STRING` | ID del job de Glue | "glue-job-abc123" |
| `api_version` | `STRING` | Versión de API Janis | "v2" |
| `schema_version` | `STRING` | Versión del esquema | "1.0" |

### Ejemplo de Registro Completo

```json
{
  "order_id": "ORD-12345",
  "status": "completed",
  "total": 182.59,
  "date_created": "2026-02-17T15:33:20Z",
  
  "_metadata": {
    "source_type": "webhook",
    "ingestion_timestamp": "2026-02-17T15:35:00Z",
    "processing_job_id": "glue-bronze-to-gold-20260217-153500",
    "api_version": "v2",
    "schema_version": "1.0"
  }
}
```

---

## Validaciones de Calidad de Datos

### Validaciones por Entidad

#### Orders
- `order_id` no nulo y único
- `total` = `subtotal` + `tax` + `shipping_cost` - `discount`
- `items_count` > 0
- `date_created` <= `date_modified`
- `status` en valores permitidos

#### Order Items
- `item_id` no nulo y único
- `order_id` existe en tabla orders
- `product_id` existe en tabla products
- `quantity_ordered` > 0
- `total` = (`unit_price` * `quantity_ordered`) - `discount`

#### Products
- `product_id` no nulo y único
- `sku` no nulo y único
- `price` >= 0
- `cost` >= 0 (si no es nulo)
- `price` >= `cost` (margen positivo)

#### Stock
- `quantity` >= 0
- `available_quantity` <= `quantity`
- `reserved_quantity` >= 0
- `quantity` = `available_quantity` + `reserved_quantity`

#### Prices
- `price` > 0
- `effective_date` <= `expiration_date` (si no es nulo)
- `product_id` existe en tabla products

---

## Estrategia de Particionamiento

### Reglas de Particionamiento por Entidad

| Entidad | Campo Partición | Formato | Ejemplo |
|---------|-----------------|---------|---------|
| Orders | `date_created` | `year=YYYY/month=MM/day=DD` | `year=2026/month=02/day=17` |
| Order Items | `date_created` (de order) | `year=YYYY/month=MM/day=DD` | `year=2026/month=02/day=17` |
| Products | `date_modified` | `year=YYYY/month=MM/day=DD` | `year=2026/month=02/day=17` |
| Stores | `date_modified` | `year=YYYY/month=MM/day=DD` | `year=2026/month=02/day=17` |
| Stock | `snapshot_date` | `year=YYYY/month=MM/day=DD` | `year=2026/month=02/day=17` |
| Prices | `effective_date` | `year=YYYY/month=MM/day=DD` | `year=2026/month=02/day=17` |

### Consideraciones de Particionamiento

1. **Granularidad**: Particionamiento diario para balance entre performance y número de particiones
2. **Queries Incrementales**: Facilita cargas incrementales en Redshift usando filtros de fecha
3. **Retención**: Simplifica aplicación de políticas de retención por fecha
4. **Performance**: Optimiza escaneo de datos en Athena/Spectrum

---

## Configuración de Archivos Parquet

### Propiedades de Compresión

```python
# Configuración recomendada para PyArrow
import pyarrow as pa
import pyarrow.parquet as pq

# Schema example
schema = pa.schema([
    ('order_id', pa.string()),
    ('total', pa.decimal128(18, 2)),
    ('date_created', pa.timestamp('us', tz='UTC'))
])

# Write options
pq.write_table(
    table,
    output_path,
    compression='snappy',
    use_dictionary=True,
    write_statistics=True,
    version='2.6'
)
```

### Configuración para Spark (Glue)

```python
# Configuración en Glue Job
df.write \
    .mode("append") \
    .format("parquet") \
    .option("compression", "snappy") \
    .option("parquet.block.size", 134217728)  # 128 MB \
    .partitionBy("year", "month", "day") \
    .save("s3://cencosud.test.super.peru.analytics/ExternalAccess/janis_smk_pe/automatico/orders/")
```

---

## Integración con Redshift

### Comandos COPY Recomendados

#### Carga de Orders

```sql
COPY dl_cs_bi.orders
FROM 's3://cencosud.test.super.peru.analytics/ExternalAccess/janis_smk_pe/automatico/orders/year=2026/month=02/day=17/'
IAM_ROLE 'arn:aws:iam::181398079618:role/RedshiftS3AccessRole'
FORMAT AS PARQUET
COMPUPDATE OFF
STATUPDATE OFF
MAXERROR 100;
```

#### Carga Incremental con Manifest

```sql
COPY dl_cs_bi.orders
FROM 's3://cencosud.test.super.peru.analytics/ExternalAccess/janis_smk_pe/automatico/orders/manifest.json'
IAM_ROLE 'arn:aws:iam::181398079618:role/RedshiftS3AccessRole'
FORMAT AS PARQUET
MANIFEST
COMPUPDATE OFF;
```

### Generación de Manifest Files

```json
{
  "entries": [
    {
      "url": "s3://cencosud.test.super.peru.analytics/ExternalAccess/janis_smk_pe/automatico/orders/year=2026/month=02/day=17/part-00000-abc123.c000.snappy.parquet",
      "mandatory": true
    },
    {
      "url": "s3://cencosud.test.super.peru.analytics/ExternalAccess/janis_smk_pe/automatico/orders/year=2026/month=02/day=17/part-00001-def456.c000.snappy.parquet",
      "mandatory": true
    }
  ]
}
```

---

## Checklist de Implementación

### Pre-requisitos

- [ ] Confirmar acceso a API Janis v2
- [ ] Validar estructura de respuestas JSON
- [ ] Obtener credenciales de API
- [ ] Configurar webhooks en Janis
- [ ] Validar permisos S3 Gold

### Desarrollo

- [ ] Implementar módulo de conversión de timestamps
- [ ] Implementar módulo de normalización de strings
- [ ] Implementar módulo de serialización JSON
- [ ] Implementar módulo de generación Parquet
- [ ] Implementar módulo de particionamiento
- [ ] Crear tests unitarios para cada transformación

### Validación

- [ ] Validar esquemas Parquet generados
- [ ] Validar estructura de carpetas en S3
- [ ] Validar naming de archivos
- [ ] Validar tamaños de archivo (64-128 MB)
- [ ] Probar carga en Redshift
- [ ] Validar tipos de datos en Redshift
- [ ] Ejecutar queries de validación

### Producción

- [ ] Configurar monitoreo de transformaciones
- [ ] Configurar alertas de errores
- [ ] Documentar procedimientos operativos
- [ ] Crear runbook de troubleshooting
- [ ] Capacitar equipo de operaciones

---

## Próximos Pasos

1. **Revisar y Aprobar Matriz** - Validar con stakeholders
2. **Crear Esquemas DDL** - Definir tablas en Redshift
3. **Implementar Transformaciones** - Desarrollar módulos de Glue
4. **Testing End-to-End** - Validar flujo completo
5. **Documentar Operaciones** - Crear guías operativas

---

**Documento Generado**: 17 de Febrero de 2026  
**Versión**: 1.0  
**Estado**: ✅ Completo - Listo para Revisión  
**Próxima Acción**: Revisión con equipo técnico
