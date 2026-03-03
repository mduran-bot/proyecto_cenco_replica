# Esquemas de Datos por Capa

## 📋 Tabla de Contenidos

- [Esquema Bronze](#esquema-bronze)
- [Esquema Silver](#esquema-silver)
- [Esquema Gold](#esquema-gold)
- [Mapeo de Campos](#mapeo-de-campos)
- [Transformaciones Aplicadas](#transformaciones-aplicadas)

---

## Esquema Bronze

### Estructura General

```json
{
  "_metadata": {
    "client_id": "string",
    "entity_type": "string",
    "ingestion_timestamp": "string (ISO 8601)",
    "source": "string (webhook|polling|initial_load)",
    "api_version": "string",
    "event_type": "string (opcional)",
    "version": "number (opcional)"
  },
  "data": {
    // Payload completo de Janis API (estructura nested)
  }
}
```

### Ejemplo Completo: Orders

```json
{
  "_metadata": {
    "client_id": "metro",
    "entity_type": "orders",
    "ingestion_timestamp": "2026-02-26T14:18:07.991Z",
    "source": "webhook",
    "api_version": "v2",
    "event_type": "order.updated",
    "version": 2
  },
  "data": {
    "id": "ORD-METRO-001",
    "orderGroupId": "group-ORD-M",
    "commerceSequentialId": "SEQ-RO-001",
    "commerceDateCreated": 1772122687991,
    "commerceSalesChannel": "ecommerce",
    "totalAmount": 250.75,
    "commerceId": "commerce-metro",
    "status": "confirmed",
    "originalAmount": 250.75,
    "rawTotalAmount": 250.75,
    "currency": "CLP",
    "salesChannelName": "E-commerce Web",
    "account": {
      "name": "Account METRO",
      "platform": "vtex"
    },
    "seller": {
      "name": "Seller METRO",
      "id": "seller-metro"
    },
    "dateCreated": 1772122687991,
    "dateModified": 1772130245391,
    "customer": {
      "id": "customer-001",
      "email": "customer@metro.com",
      "firstName": "Juan",
      "lastName": "Pérez"
    },
    "totals": {
      "items": {
        "amount": 230.75,
        "quantity": 3
      },
      "shipping": {
        "amount": 20.0
      },
      "discounts": {
        "amount": 0.0
      }
    },
    "items": [
      {
        "id": "item-001",
        "productId": "prod-100",
        "skuId": "sku-100-1",
        "name": "Producto A",
        "quantity": 2,
        "price": 75.5,
        "subtotal": 151.0
      }
    ],
    "shipping": {
      "address": {
        "street": "Av. Principal 123",
        "city": "Santiago",
        "state": "RM",
        "zipCode": "8320000",
        "country": "CL"
      },
      "carrier": {
        "id": "carrier-metro",
        "name": "Carrier Express"
      }
    },
    "payments": [
      {
        "id": "payment-001",
        "method": "credit_card",
        "amount": 250.75,
        "status": "approved",
        "transactionId": "txn-001"
      }
    ],
    "statusChanges": [
      {
        "status": "pending",
        "dateCreated": 1772123045391,
        "userId": "user-metro"
      },
      {
        "status": "confirmed",
        "dateCreated": 1772130245391,
        "userId": "user-metro"
      }
    ]
  }
}
```

---

## Esquema Silver

### Estructura Flat (42 columnas)

**Metadata (6 columnas)**:
```
_metadata_api_version: string
_metadata_client_id: string
_metadata_entity_type: string
_metadata_ingestion_timestamp: string (ISO 8601)
_metadata_source: string
_processing_timestamp: string (ISO 8601)
```

**Datos Principales (36 columnas)**:
```
data_id: string
data_orderGroupId: string
data_commerceSequentialId: string
data_commerceDateCreated: long (Unix timestamp)
data_commerceSalesChannel: string
data_totalAmount: double
data_commerceId: string
data_status: string
data_originalAmount: double
data_rawTotalAmount: double
data_currency: string
data_salesChannelName: string
data_dateCreated: long
data_dateModified: long

# Account (2 columnas)
data_account_name: string
data_account_platform: string

# Seller (2 columnas)
data_seller_id: string
data_seller_name: string

# Customer (4 columnas)
data_customer_id: string
data_customer_email: string
data_customer_firstName: string
data_customer_lastName: string

# Shipping Address (5 columnas)
data_shipping_address_street: string
data_shipping_address_city: string
data_shipping_address_state: string
data_shipping_address_zipCode: long
data_shipping_address_country: string

# Shipping Carrier (2 columnas)
data_shipping_carrier_id: string
data_shipping_carrier_name: string

# Totals (4 columnas)
data_totals_items_amount: double
data_totals_items_quantity: long
data_totals_shipping_amount: double
data_totals_discounts_amount: double

# Arrays preservados como JSON strings
data_items: string (JSON array)
data_payments: string (JSON array)
data_statusChanges: string (JSON array)

# Particionamiento
date: string (YYYY-MM-DD)
```

### Ejemplo de Registro Silver

```json
{
  "_metadata_api_version": "v2",
  "_metadata_client_id": "metro",
  "_metadata_entity_type": "orders",
  "_metadata_ingestion_timestamp": "2026-02-26T14:18:07.000-04:00",
  "_metadata_source": "webhook",
  "_processing_timestamp": "2026-02-26T14:18:54.993-04:00",
  "data_id": "ORD-METRO-001",
  "data_orderGroupId": "group-ORD-M",
  "data_commerceSequentialId": "SEQ-RO-001",
  "data_commerceDateCreated": 1772122687991,
  "data_commerceSalesChannel": "ecommerce",
  "data_totalAmount": 250.75,
  "data_commerceId": "commerce-metro",
  "data_status": "confirmed",
  "data_originalAmount": 250.75,
  "data_rawTotalAmount": 250.75,
  "data_currency": "CLP",
  "data_salesChannelName": "E-commerce Web",
  "data_dateCreated": 1772122687991,
  "data_dateModified": 1772130245391,
  "data_account_name": "Account METRO",
  "data_account_platform": "vtex",
  "data_seller_id": "seller-metro",
  "data_seller_name": "Seller METRO",
  "data_customer_id": "customer-001",
  "data_customer_email": "customer@metro.com",
  "data_customer_firstName": "Juan",
  "data_customer_lastName": "Pérez",
  "data_shipping_address_street": "Av. Principal 123",
  "data_shipping_address_city": "Santiago",
  "data_shipping_address_state": "RM",
  "data_shipping_address_zipCode": 8320000,
  "data_shipping_address_country": "CL",
  "data_shipping_carrier_id": "carrier-metro",
  "data_shipping_carrier_name": "Carrier Express",
  "data_totals_items_amount": 230.75,
  "data_totals_items_quantity": 3,
  "data_totals_shipping_amount": 20.0,
  "data_totals_discounts_amount": 0.0,
  "data_items": "[{\"id\":\"item-001\",\"productId\":\"prod-100\",\"quantity\":2,\"price\":75.5}]",
  "data_payments": "[{\"id\":\"payment-001\",\"method\":\"credit_card\",\"amount\":250.75}]",
  "data_statusChanges": "[{\"status\":\"pending\",\"dateCreated\":1772123045391},{\"status\":\"confirmed\",\"dateCreated\":1772130245391}]",
  "date": "2026-02-26"
}
```

---

## Esquema Gold

### Estructura Redshift (wms_orders)

```sql
CREATE TABLE wms_orders (
  -- Identificadores
  order_id VARCHAR(50) PRIMARY KEY,
  client_id VARCHAR(20) NOT NULL,
  order_group_id VARCHAR(50),
  commerce_sequential_id VARCHAR(50),
  commerce_id VARCHAR(50),
  
  -- Información de Orden
  status VARCHAR(20) NOT NULL,
  sales_channel VARCHAR(50),
  sales_channel_name VARCHAR(100),
  currency VARCHAR(3) DEFAULT 'CLP',
  
  -- Montos
  total_amount DECIMAL(18,2) NOT NULL,
  original_amount DECIMAL(18,2),
  raw_total_amount DECIMAL(18,2),
  items_amount DECIMAL(18,2),
  shipping_amount DECIMAL(18,2),
  discounts_amount DECIMAL(18,2),
  
  -- Cliente
  customer_id VARCHAR(50),
  customer_email VARCHAR(255),
  customer_first_name VARCHAR(100),
  customer_last_name VARCHAR(100),
  
  -- Seller
  seller_id VARCHAR(50),
  seller_name VARCHAR(100),
  
  -- Account
  account_name VARCHAR(100),
  account_platform VARCHAR(50),
  
  -- Dirección de Envío
  shipping_street VARCHAR(255),
  shipping_city VARCHAR(100),
  shipping_state VARCHAR(50),
  shipping_zip_code VARCHAR(20),
  shipping_country VARCHAR(2),
  
  -- Carrier
  carrier_id VARCHAR(50),
  carrier_name VARCHAR(100),
  
  -- Fechas
  date_created TIMESTAMP NOT NULL,
  date_modified TIMESTAMP,
  commerce_date_created TIMESTAMP,
  
  -- Campos Calculados
  total_changes INT DEFAULT 0,
  days_since_created INT,
  last_status_change TIMESTAMP,
  items_quantity INT,
  
  -- Metadata ETL
  etl_timestamp TIMESTAMP NOT NULL,
  etl_source VARCHAR(50),
  
  -- Particionamiento
  year INT NOT NULL,
  month INT NOT NULL,
  day INT NOT NULL
)
DISTKEY(client_id)
SORTKEY(date_created, client_id);
```

### Ejemplo de Registro Gold

```json
{
  "order_id": "ORD-METRO-001",
  "client_id": "metro",
  "order_group_id": "group-ORD-M",
  "commerce_sequential_id": "SEQ-RO-001",
  "commerce_id": "commerce-metro",
  "status": "confirmed",
  "sales_channel": "ecommerce",
  "sales_channel_name": "E-commerce Web",
  "currency": "CLP",
  "total_amount": 250.75,
  "original_amount": 250.75,
  "raw_total_amount": 250.75,
  "items_amount": 230.75,
  "shipping_amount": 20.0,
  "discounts_amount": 0.0,
  "customer_id": "customer-001",
  "customer_email": "customer@metro.com",
  "customer_first_name": "Juan",
  "customer_last_name": "Pérez",
  "seller_id": "seller-metro",
  "seller_name": "Seller METRO",
  "account_name": "Account METRO",
  "account_platform": "vtex",
  "shipping_street": "Av. Principal 123",
  "shipping_city": "Santiago",
  "shipping_state": "RM",
  "shipping_zip_code": "8320000",
  "shipping_country": "CL",
  "carrier_id": "carrier-metro",
  "carrier_name": "Carrier Express",
  "date_created": "2026-02-26T12:18:07.991Z",
  "date_modified": "2026-02-26T14:00:45.391Z",
  "commerce_date_created": "2026-02-26T12:18:07.991Z",
  "total_changes": 2,
  "days_since_created": 0,
  "last_status_change": "2026-02-26T14:00:45.391Z",
  "items_quantity": 3,
  "etl_timestamp": "2026-02-26T14:25:19.272652Z",
  "etl_source": "silver-to-gold-pipeline",
  "year": 2026,
  "month": 2,
  "day": 26
}
```

---

## Mapeo de Campos

### Bronze → Silver

| Bronze (Nested) | Silver (Flat) | Tipo | Transformación |
|-----------------|---------------|------|----------------|
| `data.id` | `data_id` | string | Ninguna |
| `data.status` | `data_status` | string | Lowercase |
| `data.totalAmount` | `data_totalAmount` | double | Ninguna |
| `data.customer.email` | `data_customer_email` | string | Lowercase |
| `data.customer.firstName` | `data_customer_firstName` | string | Trim |
| `data.dateCreated` | `data_dateCreated` | long | Ninguna |
| `data.items[]` | `data_items` | string (JSON) | JSON.stringify |

### Silver → Gold

| Silver | Gold (Redshift) | Tipo | Transformación |
|--------|-----------------|------|----------------|
| `data_id` | `order_id` | VARCHAR(50) | Ninguna |
| `_metadata_client_id` | `client_id` | VARCHAR(20) | Ninguna |
| `data_status` | `status` | VARCHAR(20) | Ninguna |
| `data_totalAmount` | `total_amount` | DECIMAL(18,2) | Ninguna |
| `data_customer_email` | `customer_email` | VARCHAR(255) | Ninguna |
| `data_dateCreated` | `date_created` | TIMESTAMP | Unix → ISO 8601 |
| `data_dateModified` | `date_modified` | TIMESTAMP | Unix → ISO 8601 |
| - | `total_changes` | INT | COUNT(statusChanges) |
| - | `days_since_created` | INT | DATEDIFF(NOW, date_created) |
| `_processing_timestamp` | `etl_timestamp` | TIMESTAMP | Ninguna |

---

## Transformaciones Aplicadas

### Bronze → Silver

#### 1. Flatten de Estructuras Nested

**Antes (Bronze)**:
```json
{
  "data": {
    "customer": {
      "email": "test@example.com",
      "firstName": "Juan"
    }
  }
}
```

**Después (Silver)**:
```json
{
  "data_customer_email": "test@example.com",
  "data_customer_firstName": "Juan"
}
```

#### 2. Normalización de Strings

**Antes**:
```json
{
  "data_customer_email": "JUAN@EXAMPLE.COM",
  "data_status": "CONFIRMED"
}
```

**Después**:
```json
{
  "data_customer_email": "juan@example.com",
  "data_status": "confirmed"
}
```

#### 3. Conversión de Timestamps

**Antes**:
```json
{
  "data_dateCreated": 1772122687991
}
```

**Después**:
```json
{
  "data_dateCreated": 1772122687991,
  "date_created_iso": "2026-02-26T12:18:07.991Z"
}
```

---

### Silver → Gold

#### 1. Mapeo de Nombres

**Antes (Silver)**:
```json
{
  "data_id": "ORD-001",
  "data_totalAmount": 250.75
}
```

**Después (Gold)**:
```json
{
  "order_id": "ORD-001",
  "total_amount": 250.75
}
```

#### 2. Cálculo de Campos Derivados

```python
# total_changes
total_changes = len(json.loads(data_statusChanges))

# days_since_created
days_since_created = (datetime.now() - datetime.fromtimestamp(data_dateCreated/1000)).days

# last_status_change
status_changes = json.loads(data_statusChanges)
last_status_change = max([sc['dateCreated'] for sc in status_changes])
```

#### 3. Particionamiento por Fecha

```python
# Extraer año, mes, día desde date_created
year = date_created.year
month = date_created.month
day = date_created.day
```

---

## Validaciones de Calidad

### Reglas de Validación

**Bronze**:
- ✅ `_metadata.client_id` no nulo
- ✅ `_metadata.entity_type` no nulo
- ✅ `data` no vacío

**Silver**:
- ✅ `data_id` único por cliente
- ✅ `data_totalAmount` > 0
- ✅ `data_customer_email` formato válido
- ✅ `data_dateCreated` <= NOW()

**Gold**:
- ✅ `order_id` PRIMARY KEY
- ✅ `total_amount` = `items_amount` + `shipping_amount` - `discounts_amount`
- ✅ `date_modified` >= `date_created`
- ✅ `total_changes` >= 1

---

**Última actualización**: 2026-02-26  
**Versión**: 1.0.0
