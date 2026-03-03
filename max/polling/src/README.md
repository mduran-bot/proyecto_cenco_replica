# API Client Module

## JanisAPIClient

Cliente HTTP robusto para interactuar con las APIs REST de Janis, con soporte para rate limiting, reintentos automáticos, manejo de errores y multi-tenant.

### Características

- **Rate Limiting**: Limita automáticamente las solicitudes a 100 requests/minuto (configurable) usando algoritmo de sliding window
- **Retry Strategy**: Reintenta automáticamente requests fallidos hasta 3 veces con backoff exponencial (2, 4, 8 segundos)
- **Timeout**: Timeout de 30 segundos por request para evitar bloqueos
- **Manejo de Errores**: Manejo apropiado de errores HTTP 4xx y 5xx
- **Multi-Tenant Support**: Soporte para header `janis-client` para identificación de cliente
- **Context Manager**: Soporte para uso con `with` statement para manejo automático de recursos

### Instalación

Las dependencias requeridas están en `requirements.txt`:

```bash
pip install -r requirements.txt
```

### Uso Básico

```python
from api_client import JanisAPIClient

# Crear cliente con identificación de cliente
with JanisAPIClient("https://api.janis.in", "your-api-key", client="metro") as client:
    # Realizar request - el header janis-client se incluye automáticamente
    response = client.get("orders", params={"page": 1, "pageSize": 100})
    orders = response.get('data', [])
    print(f"Obtenidos {len(orders)} órdenes para cliente metro")
```

### Multi-Tenant Support

El cliente soporta identificación de cliente mediante el header `janis-client`, requerido para el sistema multi-tenant:

```python
# Cliente para Metro
with JanisAPIClient("https://api.janis.in", "api-key", client="metro") as metro_client:
    metro_orders = metro_client.get("orders")

# Cliente para Wongio
with JanisAPIClient("https://api.janis.in", "api-key", client="wongio") as wongio_client:
    wongio_orders = wongio_client.get("orders")
```

El header `janis-client` se incluye automáticamente en todas las requests cuando se especifica el parámetro `client` en el constructor.

### Configuración

#### Parámetros de Inicialización

- `base_url` (str, requerido): URL base de la API de Janis
- `api_key` (str, requerido): API key para autenticación Bearer
- `client` (str, opcional): Identificador del cliente para header `janis-client` (ej: "metro", "wongio")
- `rate_limit` (int, opcional): Número máximo de requests por minuto (default: 100)

#### Variables de Entorno

Se recomienda usar variables de entorno para credenciales:

```bash
export JANIS_API_URL="https://api.janis.in"
export JANIS_API_KEY="your-api-key-here"
```

```python
import os
from api_client import JanisAPIClient

base_url = os.environ.get("JANIS_API_URL")
api_key = os.environ.get("JANIS_API_KEY")
client_id = os.environ.get("JANIS_CLIENT", "metro")  # Default to metro

with JanisAPIClient(base_url, api_key, client=client_id) as client:
    response = client.get("orders")
```

### Métodos

#### `get(endpoint: str, params: Optional[Dict] = None) -> Dict`

Realiza un GET request a la API.

**Parámetros:**
- `endpoint`: Endpoint de la API (ej: "orders", "products/123")
- `params`: Parámetros de query string opcionales

**Retorna:**
- `Dict`: Respuesta JSON parseada

**Excepciones:**
- `ValueError`: Para errores 4xx del cliente (excepto 429)
- `requests.exceptions.HTTPError`: Para errores de servidor después de reintentos
- `requests.exceptions.Timeout`: Si el request excede 30 segundos

**Ejemplo:**
```python
response = client.get("orders", params={
    "page": 1,
    "pageSize": 100,
    "dateModified": "2024-01-01T00:00:00Z"
})
```

#### `close()`

Cierra la sesión HTTP y libera recursos.

**Ejemplo:**
```python
client = JanisAPIClient("https://api.janis.in", "api-key")
try:
    response = client.get("orders")
finally:
    client.close()
```

### Rate Limiting

El cliente implementa rate limiting usando un algoritmo de sliding window:

1. Mantiene un registro de timestamps de requests en los últimos 60 segundos
2. Si se alcanza el límite configurado, espera hasta que el request más antiguo expire
3. Automáticamente limpia timestamps antiguos

**Ejemplo con rate limit personalizado:**
```python
# Limitar a 50 requests por minuto para cliente específico
with JanisAPIClient("https://api.janis.in", "api-key", client="metro", rate_limit=50) as client:
    for i in range(100):
        response = client.get("orders", params={"page": i + 1})
        # El cliente automáticamente esperará si se alcanza el límite
```

### Retry Strategy

El cliente reintenta automáticamente requests fallidos:

- **Total de intentos**: 3
- **Backoff factor**: 2 (delays de 2, 4, 8 segundos)
- **Status codes para reintentar**: 429, 500, 502, 503, 504
- **Métodos permitidos**: GET

La estrategia de reintentos se aplica automáticamente. No se requiere código adicional.

### Manejo de Errores

```python
from api_client import JanisAPIClient
import requests

with JanisAPIClient("https://api.janis.in", "api-key") as client:
    try:
        response = client.get("orders/invalid-id")
        
    except ValueError as e:
        # Errores 4xx del cliente (404, 400, etc.)
        print(f"Error del cliente: {e}")
        
    except requests.exceptions.HTTPError as e:
        # Errores 5xx del servidor después de reintentos
        print(f"Error del servidor: {e}")
        
    except requests.exceptions.Timeout as e:
        # Timeout después de 30 segundos
        print(f"Timeout: {e}")
        
    except requests.exceptions.RequestException as e:
        # Otros errores de red
        print(f"Error de red: {e}")
```

### Ejemplos Avanzados

Ver `examples/api_client_usage.py` para ejemplos completos de:

- Uso básico
- Context manager
- Rate limit personalizado
- Manejo de errores
- Variables de entorno
- Paginación de resultados

### Testing

Ejecutar tests unitarios:

```bash
pytest tests/test_api_client.py -v
```

Ejecutar tests con cobertura:

```bash
pytest tests/test_api_client.py --cov=src --cov-report=html
```

### Arquitectura

El cliente está diseñado siguiendo los requerimientos del sistema de polling:

- **Requerimiento 5.1**: Rate limiting de 100 requests/minuto
- **Requerimiento 5.3**: Reintentos con backoff exponencial para HTTP 429
- **Requerimiento 5.4**: 3 intentos con delays de 2, 4, 8 segundos
- **Requerimiento 5.7**: Timeout de 30 segundos

### Integración con MWAA

El cliente está diseñado para usarse en DAGs de Apache Airflow (MWAA) con soporte multi-tenant:

```python
from airflow import DAG
from airflow.operators.python import PythonOperator
from api_client import JanisAPIClient
import os

def poll_janis_api(client: str, endpoint: str, base_url: str, **context):
    """
    Función de task para polling multi-tenant.
    
    Args:
        client: Identificador del cliente (metro, wongio)
        endpoint: Endpoint específico de la API
        base_url: URL base de la API
    """
    api_key = os.environ['JANIS_API_KEY']
    
    with JanisAPIClient(base_url, api_key, client=client) as api_client:
        response = api_client.get(endpoint, params={"page": 1})
        return response

dag = DAG('poll_orders', schedule_interval=None)

# Crear tasks para cada cliente
for client in ['metro', 'wongio']:
    poll_task = PythonOperator(
        task_id=f'poll_api_{client}',
        python_callable=poll_janis_api,
        op_kwargs={
            'client': client,
            'endpoint': 'orders',
            'base_url': 'https://oms.janis.in/api'
        },
        dag=dag
    )
```

**Configuración EventBridge:**

Los DAGs reciben configuración multi-tenant desde EventBridge:

```json
{
  "dag_id": "poll_orders",
  "conf": {
    "clients": ["metro", "wongio"],
    "endpoint": "/order",
    "base_url": "https://oms.janis.in/api"
  }
}
```

El DAG itera sobre los clientes y crea tasks dinámicamente, cada uno con su propio lock en DynamoDB usando la clave compuesta `{data_type}-{client}`.

### Notas de Implementación

- La sesión HTTP se reutiliza para múltiples requests (connection pooling)
- Los adapters HTTP están configurados para HTTP y HTTPS
- El rate limiting es thread-safe para uso en entornos concurrentes
- La autenticación usa Bearer token en el header Authorization
- El header `janis-client` se incluye automáticamente cuando se especifica el parámetro `client`
- Cada instancia del cliente mantiene su propio rate limiter independiente

## Módulos Implementados

### 1. JanisAPIClient (`api_client.py`)
Cliente HTTP robusto con rate limiting y reintentos automáticos.

**Estado**: ✅ Completado
**Documentación**: Ver sección anterior

### 2. PaginationHandler (`pagination_handler.py`)
Manejo de paginación con circuit breaker para prevenir bucles infinitos.

**Estado**: ✅ Completado
**Características**:
- Paginación automática con límite de 1000 páginas
- Circuit breaker para prevenir bucles infinitos
- Integración con JanisAPIClient

### 3. StateManager (`state_manager.py`)
Gestión de estado con DynamoDB para locks distribuidos y polling incremental.

**Estado**: 🔄 En Cola
**Características**:
- Distributed locking para prevenir ejecuciones concurrentes
- Tracking de estado para polling incremental
- Soporte para LocalStack
- Manejo de primera ejecución

**Documentación completa**: Ver `state_manager_README.md`

**Uso básico**:
```python
from state_manager import StateManager
import uuid

state_manager = StateManager(table_name='polling_control')
execution_id = str(uuid.uuid4())

# Adquirir lock
if state_manager.acquire_lock('orders', execution_id):
    try:
        # Realizar polling
        records = fetch_data()
        
        # Liberar lock con éxito
        state_manager.release_lock(
            data_type='orders',
            success=True,
            last_modified=get_latest_timestamp(records),
            records_fetched=len(records)
        )
    except Exception as e:
        # Liberar lock con error
        state_manager.release_lock(
            data_type='orders',
            success=False,
            error_message=str(e)
        )
else:
    print("Lock ya existe, omitiendo ejecución")
```

### Próximos Pasos

Los siguientes componentes están en desarrollo o pendientes:

1. **Incremental Polling Logic**: Construcción de filtros incrementales y deduplicación
2. **Data Validator**: Validación de esquemas JSON
3. **Data Enricher**: Enriquecimiento paralelo de datos
4. **Airflow Task Functions**: Refactorización para soporte multi-tenant completo
   - Modificar funciones de task para aceptar parámetro `client`
   - Actualizar DynamoDB keys a formato `{data_type}-{client}`
   - Actualizar S3 paths a formato `bronze/{client}/{data_type}/`

**Estado Actual del Sistema:**
- ✅ JanisAPIClient con soporte multi-tenant
- ✅ PaginationHandler con circuit breaker
- ✅ StateManager con DynamoDB locking
- ✅ DAG structure con EventBridge triggering
- 🔄 Task functions pendientes de refactorización multi-tenant (Tasks 10-12)

Ver `.kiro/specs/api-polling-system/tasks.md` para el plan completo de implementación.
