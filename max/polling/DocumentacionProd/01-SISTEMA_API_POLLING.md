# Sistema de API Polling Multi-Tenant

**Fecha:** Febrero 24, 2026  
**Versión:** 1.0  
**Estado:** Completo y Funcional

---

## 📋 Tabla de Contenidos

1. [Resumen Ejecutivo](#resumen-ejecutivo)
2. [Arquitectura del Sistema](#arquitectura-del-sistema)
3. [Componentes Principales](#componentes-principales)
4. [Flujo de Datos](#flujo-de-datos)
5. [Multi-Tenant](#multi-tenant)
6. [Configuración](#configuración)
7. [Endpoints Soportados](#endpoints-soportados)

---

## 🎯 Resumen Ejecutivo

El Sistema de API Polling es una solución serverless diseñada para sincronizar datos desde la API de Janis hacia el Data Lake de Cencosud en AWS. El sistema implementa polling periódico con soporte multi-tenant, validación de datos, enriquecimiento automático y gestión de estado distribuido.

### Características Principales

✅ **Multi-Tenant**: Soporte para múltiples clientes (Metro, Wongio) con aislamiento de datos  
✅ **Polling Incremental**: Solo obtiene datos nuevos o modificados desde la última ejecución  
✅ **Validación Automática**: Valida datos contra esquemas JSON antes de procesarlos  
✅ **Enriquecimiento**: Obtiene datos relacionados automáticamente (items de órdenes, SKUs de productos)  
✅ **Gestión de Estado**: Locks distribuidos en DynamoDB para evitar ejecuciones concurrentes  
✅ **Rate Limiting**: Control de tasa de requests para no saturar la API  
✅ **Circuit Breaker**: Protección contra fallos en cascada  
✅ **Retry Logic**: Reintentos automáticos con backoff exponencial  

### Casos de Uso

1. **Sincronización de Órdenes**: Polling cada 5 minutos para mantener órdenes actualizadas
2. **Actualización de Inventario**: Polling cada 10 minutos para stock en tiempo real
3. **Catálogo de Productos**: Polling cada hora para productos y SKUs
4. **Precios**: Polling cada 30 minutos para mantener precios actualizados
5. **Tiendas**: Polling diario para información de ubicaciones

---

## 🏗️ Arquitectura del Sistema

### Diagrama de Alto Nivel

```
┌─────────────────────────────────────────────────────────────────────┐
│                         EventBridge                                 │
│  Triggers DAGs según schedule (rate expressions)                    │
└─────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────┐
│                      Amazon MWAA (Airflow)                          │
│  Orquesta el flujo de polling para cada endpoint/cliente            │
└─────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────┐
│                         Componentes Core                            │
│                                                                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐            │
│  │ StateManager │  │  APIClient   │  │ Pagination   │            │
│  │  (DynamoDB)  │  │  (Janis)     │  │  Handler     │            │
│  └──────────────┘  └──────────────┘  └──────────────┘            │
│                                                                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐            │
│  │ Incremental  │  │ DataValidator│  │ DataEnricher │            │
│  │  Polling     │  │  (Schemas)   │  │  (Parallel)  │            │
│  └──────────────┘  └──────────────┘  └──────────────┘            │
└─────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────┐
│                      Janis API (Origen)                             │
│  https://oms.janis.in/api, https://catalog.janis.in/api, etc.      │
└─────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────┐
│                    S3 Data Lake (Destino)                           │
│  s3://cencosud-datalake-bronze/janis/{data_type}/{client}/          │
└─────────────────────────────────────────────────────────────────────┘
```

### Capas del Sistema

#### 1. Capa de Orquestación
- **EventBridge**: Scheduler que dispara DAGs según configuración
- **MWAA (Airflow)**: Orquesta el flujo de tareas para cada polling

#### 2. Capa de Procesamiento
- **StateManager**: Gestión de locks y estado en DynamoDB
- **APIClient**: Cliente HTTP con rate limiting y reintentos
- **PaginationHandler**: Manejo automático de paginación con circuit breaker
- **IncrementalPolling**: Construcción de filtros y deduplicación
- **DataValidator**: Validación contra esquemas JSON
- **DataEnricher**: Enriquecimiento paralelo de datos

#### 3. Capa de Datos
- **DynamoDB**: Tabla `polling_control` para estado y locks
- **Janis API**: Fuente de datos externa
- **S3 Bronze**: Destino final de datos crudos

---

## 🔧 Componentes Principales

### 1. StateManager

**Propósito**: Gestionar locks distribuidos y estado de polling en DynamoDB.

**Funcionalidades**:
- Adquirir/liberar locks con keys compuestas multi-tenant
- Almacenar último timestamp procesado
- Registrar métricas de ejecución
- Prevenir ejecuciones concurrentes

**Tabla DynamoDB**:
```
polling_control
├── data_type (HASH KEY): "{data_type}-{client}" (ej: "orders-metro")
├── lock_acquired: boolean
├── execution_id: string
├── lock_timestamp: timestamp
├── status: "running" | "completed" | "failed"
├── last_modified_date: timestamp (último registro procesado)
├── last_successful_execution: timestamp
├── records_fetched: number
└── error_message: string (si aplica)
```

**Ejemplo de uso**:
```python
from state_manager import StateManager

state_manager = StateManager(
    table_name='polling_control',
    endpoint_url='http://localhost:4566'  # LocalStack para testing
)

# Adquirir lock
lock_key = "orders-metro"
execution_id = "exec-123"
if state_manager.acquire_lock(lock_key, execution_id):
    # Procesar datos...
    
    # Liberar lock
    state_manager.release_lock(
        data_type=lock_key,
        success=True,
        last_modified="2024-02-24T10:00:00Z",
        records_fetched=150
    )
```

---

### 2. JanisAPIClient

**Propósito**: Cliente HTTP para interactuar con la API de Janis con rate limiting y reintentos.

**Funcionalidades**:
- Rate limiting configurable (requests por minuto)
- Reintentos automáticos con backoff exponencial
- Headers multi-tenant (`janis-client`)
- Manejo de errores HTTP
- Logging detallado

**Configuración**:
```python
from api_client import JanisAPIClient

client = JanisAPIClient(
    base_url='https://oms.janis.in/api',
    api_key='your-api-key',
    rate_limit=100,  # 100 requests/minuto
    extra_headers={
        'janis-client': 'metro',
        'janis-api-key': 'your-api-key',
        'janis-api-secret': 'your-api-secret'
    }
)

# Hacer request
response = client.get('/order', params={'page': 1, 'pageSize': 100})
```

**Rate Limiting**:
- Usa token bucket algorithm
- Configurable por cliente
- Previene saturación de API
- Logs cuando se alcanza el límite

---

### 3. PaginationHandler

**Propósito**: Manejar paginación automática con circuit breaker para protección.

**Funcionalidades**:
- Paginación automática hasta obtener todos los datos
- Circuit breaker para prevenir loops infinitos
- Detección de páginas vacías
- Límite configurable de páginas

**Configuración**:
```python
from pagination_handler import PaginationHandler

handler = PaginationHandler(
    client=api_client,
    max_pages=1000,  # Límite de seguridad
    page_size=100
)

# Obtener todas las páginas
all_records = handler.fetch_all_pages(
    endpoint='/order',
    filters={'dateModified': '2024-02-24T00:00:00Z'}
)
```

**Circuit Breaker**:
- Se activa después de 3 páginas vacías consecutivas
- Previene loops infinitos
- Logs detallados de activación

---

### 4. IncrementalPolling

**Propósito**: Implementar polling incremental para obtener solo datos nuevos/modificados.

**Funcionalidades**:
- Construcción de filtros basados en último timestamp
- Deduplicación de registros por ID
- Overlap configurable para evitar pérdida de datos
- Soporte para múltiples campos de fecha

**Flujo**:
```python
from incremental_polling import build_incremental_filter, deduplicate_records

# 1. Construir filtro incremental
filters = build_incremental_filter(state_manager, "orders-metro")
# Retorna: {'dateModified': '2024-02-24T10:00:00Z', 'sortBy': 'dateModified', 'sortOrder': 'asc'}

# 2. Obtener datos con filtro
records = pagination_handler.fetch_all_pages('/order', filters=filters)

# 3. Deduplicar
unique_records = deduplicate_records(records)
```

**Overlap**:
- Por defecto: 1 minuto de overlap
- Previene pérdida de datos por timing
- Configurable en `api_config.json`

---

### 5. DataValidator

**Propósito**: Validar datos contra esquemas JSON antes de procesarlos.

**Funcionalidades**:
- Validación contra esquemas JSON Schema
- Detección de campos requeridos faltantes
- Validación de tipos de datos
- Métricas de validación detalladas
- Deduplicación adicional

**Esquemas**:
```
src/schemas/
├── orders_schema.json
├── products_schema.json
├── stock_schema.json
├── prices_schema.json
└── stores_schema.json
```

**Uso**:
```python
from data_validator import DataValidator

validator = DataValidator(data_type='orders')

# Validar lote de registros
valid_records, metrics = validator.validate_batch(records)

# Métricas retornadas:
# {
#   'total_received': 150,
#   'duplicates_in_batch': 2,
#   'valid_count': 145,
#   'invalid_count': 3,
#   'validation_pass_rate': 96.67,
#   'invalid_records': [...]
# }
```

---

### 6. DataEnricher

**Propósito**: Enriquecer datos con información relacionada de forma paralela.

**Funcionalidades**:
- Enriquecimiento paralelo con ThreadPoolExecutor
- Soporte para órdenes (items) y productos (SKUs)
- Manejo de errores por registro
- Marcado de registros enriquecidos
- Configurable número de workers

**Enriquecimiento de Órdenes**:
```python
from data_enricher import DataEnricher

enricher = DataEnricher(client=api_client, max_workers=5)

# Enriquecer órdenes con items
enriched_orders = enricher.enrich_orders(orders)

# Cada orden tendrá:
# - _enrichment_complete: True/False
# - _enrichment_error: string (si aplica)
# - items: [...] (si exitoso)
```

**Enriquecimiento de Productos**:
```python
# Enriquecer productos con SKUs
enriched_products = enricher.enrich_products(products)

# Cada producto tendrá:
# - _enrichment_complete: True/False
# - _enrichment_error: string (si aplica)
# - skus: [...] (si exitoso)
```

---

## 🔄 Flujo de Datos

### Flujo Completo de Polling

```
1. EventBridge Trigger
   ↓
2. MWAA DAG Execution
   ↓
3. Acquire Lock (DynamoDB)
   │ Lock Key: {data_type}-{client}
   │ Execution ID: unique-id
   ↓
4. Build Incremental Filter
   │ Query DynamoDB for last_modified_date
   │ Add overlap (1 minute)
   ↓
5. Poll Janis API
   │ Headers: janis-client, janis-api-key, janis-api-secret
   │ Params: dateModified, page, pageSize
   │ Pagination: Automatic until no more data
   ↓
6. Deduplicate Records
   │ Remove duplicates by 'id' field
   ↓
7. Validate Data
   │ Validate against JSON schema
   │ Filter out invalid records
   ↓
8. Enrich Data (if applicable)
   │ Orders: Fetch items for each order
   │ Products: Fetch SKUs for each product
   │ Parallel execution with ThreadPoolExecutor
   ↓
9. Output Data
   │ Add metadata: _ingestion_timestamp, _client, _source
   │ Write to S3 Bronze: s3://bucket/janis/{data_type}/{client}/
   ↓
10. Release Lock (DynamoDB)
    │ Update last_modified_date
    │ Update records_fetched
    │ Set status: completed
    │ Release lock
```

### Manejo de Errores

En cada paso, si ocurre un error:

1. **Log del error** con contexto completo
2. **Liberar lock** en DynamoDB con status='failed'
3. **Registrar error_message** en DynamoDB
4. **Notificar** (si configurado)
5. **Permitir retry** en siguiente ejecución

---

## 🏢 Multi-Tenant

### Concepto

El sistema soporta múltiples clientes (tenants) con aislamiento completo de datos:

- **Metro**: Cliente principal de supermercados
- **Wongio**: Cliente de e-commerce

### Implementación

#### 1. Lock Keys Compuestas

```python
# Formato: {data_type}-{client}
lock_key_metro = "orders-metro"
lock_key_wongio = "orders-wongio"

# Cada cliente tiene su propio lock
# Pueden ejecutarse en paralelo sin conflictos
```

#### 2. Headers Multi-Tenant

```python
headers = {
    'janis-client': 'metro',  # Identifica el cliente
    'janis-api-key': 'key',
    'janis-api-secret': 'secret'
}

# La API de Janis retorna datos filtrados por cliente
```

#### 3. Rutas S3 Separadas

```
s3://cencosud-datalake-bronze/janis/
├── orders/
│   ├── metro/
│   │   └── 2024-02-24/
│   │       └── orders_20240224_100000.json
│   └── wongio/
│       └── 2024-02-24/
│           └── orders_20240224_100000.json
├── products/
│   ├── metro/
│   └── wongio/
└── stock/
    ├── metro/
    └── wongio/
```

#### 4. Estado Independiente

Cada combinación `{data_type}-{client}` tiene:
- Su propio lock
- Su propio last_modified_date
- Sus propias métricas
- Su propio historial de ejecuciones

---

## ⚙️ Configuración

### Archivo: `config/api_config.json`

```json
{
  "apis": {
    "orders": {
      "endpoint": "orders",
      "schedule": "rate(5 minutes)",
      "requires_enrichment": true,
      "enrichment_endpoint": "orders/{id}/items",
      "priority": "high"
    },
    "products": {
      "endpoint": "products",
      "schedule": "rate(1 hour)",
      "requires_enrichment": true,
      "enrichment_endpoint": "products/{id}/skus",
      "priority": "medium"
    },
    "stock": {
      "endpoint": "stock",
      "schedule": "rate(10 minutes)",
      "requires_enrichment": false,
      "priority": "high"
    }
  },
  "rate_limiting": {
    "max_requests_per_minute": 100,
    "backoff_factor": 2,
    "max_retries": 3
  },
  "pagination": {
    "page_size": 100,
    "max_pages": 1000
  },
  "incremental": {
    "overlap_minutes": 1,
    "date_field": "dateModified"
  }
}
```

### Variables de Entorno

```bash
# Janis API
JANIS_API_KEY=your-api-key
JANIS_API_SECRET=your-api-secret

# AWS
AWS_REGION=us-east-1
DYNAMODB_TABLE=polling_control
S3_BUCKET=cencosud-datalake-bronze

# Configuración
RATE_LIMIT=100
MAX_PAGES=1000
PAGE_SIZE=100
```

---

## 📡 Endpoints Soportados

### 1. Orders (Órdenes)

**Endpoint**: `/order`  
**Base URL**: `https://oms.janis.in/api`  
**Schedule**: Cada 5 minutos  
**Enriquecimiento**: Sí (items)  
**Prioridad**: Alta  

**Datos obtenidos**:
- Información de orden
- Cliente y vendedor
- Items (enriquecido)
- Shipping
- Addresses
- Payments
- Totals

---

### 2. Catalog (Productos)

**Endpoints**: `/product`, `/sku`, `/category`, `/brand`  
**Base URL**: `https://catalog.janis.in/api`  
**Schedule**: Cada hora  
**Enriquecimiento**: Sí (SKUs)  
**Prioridad**: Media  

**Datos obtenidos**:
- Productos
- SKUs (enriquecido)
- Categorías
- Marcas

---

### 3. Stock (Inventario)

**Endpoint**: `/sku-stock`  
**Base URL**: `https://wms.janis.in/api`  
**Schedule**: Cada 10 minutos  
**Enriquecimiento**: No  
**Prioridad**: Alta  

**Datos obtenidos**:
- Stock por SKU
- Ubicación
- Cantidad disponible

---

### 4. Prices (Precios)

**Endpoints**: `/price`, `/price-sheet`, `/base-price`  
**Base URL**: `https://vtex.pricing.janis.in/api`  
**Schedule**: Cada 30 minutos  
**Enriquecimiento**: No  
**Prioridad**: Media  

**Datos obtenidos**:
- Precios por SKU
- Price sheets
- Precios base

---

### 5. Stores (Tiendas)

**Endpoint**: `/location`  
**Base URL**: `https://commerce.janis.in/api`  
**Schedule**: Cada día  
**Enriquecimiento**: No  
**Prioridad**: Baja  

**Datos obtenidos**:
- Ubicaciones de tiendas
- Información de contacto
- Horarios

---

## 📊 Métricas y Monitoreo

### Métricas Capturadas

Por cada ejecución se registra:

- **Timestamp de inicio/fin**
- **Registros obtenidos**
- **Registros válidos**
- **Registros inválidos**
- **Duplicados removidos**
- **Tiempo de ejecución**
- **Errores (si aplica)**

### Logs

Todos los componentes generan logs estructurados:

```python
logger.info(f"Lock adquirido: {lock_key}")
logger.info(f"Registros obtenidos: {len(records)}")
logger.warning(f"Registros inválidos: {invalid_count}")
logger.error(f"Error en enriquecimiento: {error}")
```

---

## 🔐 Seguridad

### Credenciales

- **API Keys**: Almacenadas en AWS Secrets Manager
- **Acceso DynamoDB**: IAM roles con permisos mínimos
- **Acceso S3**: IAM roles con permisos de escritura solo en Bronze

### Aislamiento

- Cada cliente tiene datos separados en S3
- Locks independientes por cliente
- Headers multi-tenant en todas las requests

---

## 📚 Referencias

- **Código fuente**: `max/polling/src/`
- **DAGs**: `max/polling/dags/`
- **Tests**: `max/polling/tests/`
- **Configuración**: `max/polling/config/`
- **Documentación adicional**: `max/polling/docs/`

---

**Última actualización**: Febrero 24, 2026  
**Autor**: Equipo de Integración Janis-Cencosud  
**Versión**: 1.0
