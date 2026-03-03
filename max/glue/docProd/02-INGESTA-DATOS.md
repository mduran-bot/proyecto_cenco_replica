# Ingesta de Datos desde Janis WMS

## 📋 Tabla de Contenidos

- [Visión General](#visión-general)
- [Webhooks en Tiempo Real](#webhooks-en-tiempo-real)
- [Polling Programado](#polling-programado)
- [Carga Inicial](#carga-inicial)
- [Formato de Datos en Bronze](#formato-de-datos-en-bronze)

---

## Visión General

El sistema de ingesta implementa una estrategia híbrida para garantizar que todos los datos de Janis lleguen al Data Lake:

1. **Webhooks** (Primario): Eventos en tiempo real
2. **Polling** (Backup): Verificación periódica cada 15 minutos
3. **Carga Inicial** (One-time): Migración de datos históricos

### Arquitectura de Ingesta

```
┌─────────────────────────────────────────────────────────────────┐
│                        JANIS WMS API                            │
│                    https://api.janis.in                         │
└────────────┬────────────────────────────────────────────────────┘
             │
             ├─── 🔔 WEBHOOKS (Tiempo Real)
             │    │
             │    ▼
             │    ┌──────────────────────────────────────────┐
             │    │      Amazon API Gateway                  │
             │    │  POST /webhooks/{client}/{entity}        │
             │    └──────────────┬───────────────────────────┘
             │                   │
             │                   ▼
             │    ┌──────────────────────────────────────────┐
             │    │      AWS Lambda                          │
             │    │  webhook-processor                       │
             │    │  - Validación de payload                 │
             │    │  - Enriquecimiento de metadata           │
             │    └──────────────┬───────────────────────────┘
             │                   │
             │                   ▼
             │    ┌──────────────────────────────────────────┐
             │    │  Amazon Kinesis Data Firehose            │
             │    │  - Buffering (1 MB o 60 seg)             │
             │    │  - Compresión GZIP                       │
             │    └──────────────┬───────────────────────────┘
             │                   │
             │                   ▼
             │    ┌──────────────────────────────────────────┐
             │    │      Amazon S3 (Bronze)                  │
             │    │  s3://bronze/{client}/{entity}/date=...  │
             │    └──────────────────────────────────────────┘
             │
             └─── 🔄 POLLING (Backup cada 15 min)
                  │
                  ▼
                  ┌──────────────────────────────────────────┐
                  │      Amazon EventBridge                  │
                  │  Rule: rate(15 minutes)                  │
                  └──────────────┬───────────────────────────┘
                                 │
                                 ▼
                  ┌──────────────────────────────────────────┐
                  │      Amazon MWAA (Airflow)               │
                  │  DAG: dag_poll_orders                    │
                  │  - Consulta API Janis                    │
                  │  - Filtro por fecha modificación         │
                  └──────────────┬───────────────────────────┘
                                 │
                                 ▼
                  ┌──────────────────────────────────────────┐
                  │      AWS Lambda                          │
                  │  polling-processor                       │
                  │  - Paginación de resultados              │
                  │  - Deduplicación vs webhooks             │
                  └──────────────┬───────────────────────────┘
                                 │
                                 ▼
                  ┌──────────────────────────────────────────┐
                  │      Amazon S3 (Bronze)                  │
                  │  s3://bronze/{client}/{entity}/date=...  │
                  └──────────────────────────────────────────┘
```

---

## Webhooks en Tiempo Real

### Configuración en Janis

Los webhooks se configuran en el panel de administración de Janis para cada cliente:

**URL del Webhook**:
```
https://api.cencosud-datalake.com/webhooks/{client_id}/{entity_type}
```

**Ejemplos**:
- `https://api.cencosud-datalake.com/webhooks/metro/orders`
- `https://api.cencosud-datalake.com/webhooks/wongio/orders`

**Eventos Soportados**:
- `order.created`: Nueva orden creada
- `order.updated`: Orden actualizada (cambio de status, items, etc.)
- `order.deleted`: Orden eliminada (soft delete)
- `product.created`: Nuevo producto
- `product.updated`: Producto actualizado
- `stock.updated`: Actualización de inventario
- `price.updated`: Cambio de precio

### Payload del Webhook

**Headers**:
```http
POST /webhooks/metro/orders HTTP/1.1
Host: api.cencosud-datalake.com
Content-Type: application/json
X-Janis-Event: order.updated
X-Janis-Signature: sha256=abc123...
X-Janis-Timestamp: 1772122687991
```

**Body**:
```json
{
  "event": "order.updated",
  "timestamp": 1772122687991,
  "data": {
    "id": "ORD-METRO-001",
    "orderGroupId": "group-ORD-M",
    "status": "confirmed",
    "totalAmount": 250.75,
    "customer": {
      "id": "customer-001",
      "email": "customer@metro.com",
      "firstName": "Juan",
      "lastName": "Pérez"
    },
    "items": [
      {
        "id": "item-001",
        "productId": "prod-100",
        "quantity": 2,
        "price": 75.50
      }
    ],
    // ... resto del payload
  }
}
```

### Procesamiento del Webhook

**Lambda: webhook-processor**

```python
def lambda_handler(event, context):
    """
    Procesa webhooks de Janis y los envía a Kinesis Firehose
    """
    # 1. Extraer parámetros de la URL
    client_id = event['pathParameters']['client']
    entity_type = event['pathParameters']['entity']
    
    # 2. Validar firma del webhook
    signature = event['headers']['X-Janis-Signature']
    if not validate_signature(event['body'], signature):
        return {'statusCode': 401, 'body': 'Invalid signature'}
    
    # 3. Parsear payload
    payload = json.loads(event['body'])
    
    # 4. Enriquecer con metadata
    enriched_data = {
        "_metadata": {
            "client_id": client_id,
            "entity_type": entity_type,
            "ingestion_timestamp": datetime.now().isoformat(),
            "source": "webhook",
            "api_version": "v2",
            "event_type": payload.get('event'),
            "webhook_timestamp": payload.get('timestamp')
        },
        "data": payload.get('data')
    }
    
    # 5. Enviar a Kinesis Firehose
    firehose.put_record(
        DeliveryStreamName=f'{client_id}-{entity_type}-stream',
        Record={'Data': json.dumps(enriched_data)}
    )
    
    # 6. Responder a Janis
    return {
        'statusCode': 200,
        'body': json.dumps({'status': 'accepted'})
    }
```

### Kinesis Firehose Configuration

**Configuración del Stream**:
```json
{
  "DeliveryStreamName": "metro-orders-stream",
  "S3DestinationConfiguration": {
    "BucketARN": "arn:aws:s3:::cencosud-datalake-bronze",
    "Prefix": "metro/orders/date=!{timestamp:yyyy-MM-dd}/",
    "ErrorOutputPrefix": "errors/metro/orders/!{firehose:error-output-type}/",
    "BufferingHints": {
      "SizeInMBs": 1,
      "IntervalInSeconds": 60
    },
    "CompressionFormat": "UNCOMPRESSED",
    "DataFormatConversionConfiguration": {
      "Enabled": false
    }
  }
}
```

**Ventajas de Kinesis Firehose**:
- ✅ Buffering automático (reduce número de archivos)
- ✅ Retry automático en caso de fallo
- ✅ Transformación opcional con Lambda
- ✅ Particionamiento dinámico por fecha

---

## Polling Programado

### Configuración de EventBridge

**Rule: poll-janis-orders**

```json
{
  "Name": "poll-janis-orders-every-15min",
  "ScheduleExpression": "rate(15 minutes)",
  "State": "ENABLED",
  "Targets": [
    {
      "Arn": "arn:aws:airflow:us-east-1:123456789:environment/cencosud-mwaa",
      "RoleArn": "arn:aws:iam::123456789:role/EventBridgeToMWAA",
      "Input": "{\"dag_name\": \"dag_poll_orders\", \"conf\": {}}"
    }
  ]
}
```

### DAG de Airflow: dag_poll_orders

**Archivo**: `airflow/dags/dag_poll_orders.py`

```python
from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import requests
import boto3

default_args = {
    'owner': 'data-engineering',
    'depends_on_past': False,
    'start_date': datetime(2026, 1, 1),
    'email_on_failure': True,
    'email': ['alerts@cencosud.com'],
    'retries': 3,
    'retry_delay': timedelta(minutes=5)
}

dag = DAG(
    'dag_poll_orders',
    default_args=default_args,
    description='Poll Janis API for orders every 15 minutes',
    schedule_interval=None,  # Triggered by EventBridge
    catchup=False
)

def poll_janis_api(**context):
    """
    Consulta API de Janis para obtener órdenes modificadas
    en los últimos 20 minutos (overlap de 5 min con webhooks)
    """
    # 1. Calcular ventana de tiempo
    now = datetime.now()
    since = now - timedelta(minutes=20)
    
    # 2. Consultar API de Janis
    clients = ['metro', 'wongio']
    s3 = boto3.client('s3')
    
    for client_id in clients:
        # Obtener credenciales del cliente desde Secrets Manager
        api_key = get_secret(f'janis/{client_id}/api_key')
        
        # Consultar API con paginación
        page = 1
        has_more = True
        
        while has_more:
            response = requests.get(
                f'https://api.janis.in/api/order',
                headers={'Authorization': f'Bearer {api_key}'},
                params={
                    'dateModifiedFrom': since.isoformat(),
                    'dateModifiedTo': now.isoformat(),
                    'page': page,
                    'limit': 100
                }
            )
            
            data = response.json()
            orders = data.get('data', [])
            
            # Procesar cada orden
            for order in orders:
                # Enriquecer con metadata
                enriched_data = {
                    "_metadata": {
                        "client_id": client_id,
                        "entity_type": "orders",
                        "ingestion_timestamp": datetime.now().isoformat(),
                        "source": "polling",
                        "api_version": "v2",
                        "polling_window_start": since.isoformat(),
                        "polling_window_end": now.isoformat()
                    },
                    "data": order
                }
                
                # Guardar en S3 Bronze
                date_str = now.strftime('%Y-%m-%d')
                key = f"{client_id}/orders/date={date_str}/polling_{order['id']}_{now.timestamp()}.json"
                
                s3.put_object(
                    Bucket='cencosud-datalake-bronze',
                    Key=key,
                    Body=json.dumps(enriched_data),
                    ContentType='application/json'
                )
            
            # Verificar si hay más páginas
            has_more = data.get('hasNextPage', False)
            page += 1
    
    return {'status': 'success', 'orders_processed': len(orders)}

poll_task = PythonOperator(
    task_id='poll_janis_orders',
    python_callable=poll_janis_api,
    dag=dag
)
```

### Deduplicación Polling vs Webhooks

El módulo `DuplicateDetector` en Silver se encarga de eliminar duplicados:

```python
# Lógica de deduplicación
# 1. Agrupar por order_id
# 2. Ordenar por _metadata_ingestion_timestamp DESC
# 3. Tomar el primero (más reciente)
# 4. Si hay empate, priorizar source='webhook' sobre 'polling'

df_deduplicated = df \
    .withColumn('priority', 
        when(col('_metadata_source') == 'webhook', 1)
        .when(col('_metadata_source') == 'polling', 2)
        .otherwise(3)
    ) \
    .withColumn('row_num',
        row_number().over(
            Window.partitionBy('data_id')
            .orderBy(
                col('_metadata_ingestion_timestamp').desc(),
                col('priority').asc()
            )
        )
    ) \
    .filter(col('row_num') == 1) \
    .drop('priority', 'row_num')
```

---

## Carga Inicial

### Script de Migración

**Archivo**: `max/cargainicial/mysql_to_s3_bronze.py`

```python
import pymysql
import boto3
import json
from datetime import datetime

def migrate_orders_to_bronze():
    """
    Migra órdenes históricas desde MySQL de Janis a S3 Bronze
    """
    # 1. Conectar a MySQL
    conn = pymysql.connect(
        host='janis-mysql.example.com',
        user='readonly_user',
        password=get_secret('janis/mysql/password'),
        database='janis_wms'
    )
    
    # 2. Consultar órdenes
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    cursor.execute("""
        SELECT 
            o.*,
            c.email as customer_email,
            c.first_name as customer_first_name
        FROM orders o
        LEFT JOIN customers c ON o.customer_id = c.id
        WHERE o.date_created >= '2024-01-01'
        ORDER BY o.date_created
    """)
    
    # 3. Procesar en batches
    s3 = boto3.client('s3')
    batch_size = 1000
    batch = []
    
    for row in cursor:
        # Transformar a formato Janis API
        order_data = transform_mysql_to_api_format(row)
        
        # Enriquecer con metadata
        enriched_data = {
            "_metadata": {
                "client_id": "metro",
                "entity_type": "orders",
                "ingestion_timestamp": datetime.now().isoformat(),
                "source": "initial_load",
                "api_version": "v2",
                "original_date_created": row['date_created'].isoformat()
            },
            "data": order_data
        }
        
        batch.append(enriched_data)
        
        # Escribir batch a S3
        if len(batch) >= batch_size:
            write_batch_to_s3(s3, batch)
            batch = []
    
    # Escribir último batch
    if batch:
        write_batch_to_s3(s3, batch)
    
    cursor.close()
    conn.close()

def write_batch_to_s3(s3, batch):
    """Escribe batch de órdenes a S3 Bronze"""
    # Agrupar por fecha para particionamiento
    by_date = {}
    for item in batch:
        date_str = item['_metadata']['original_date_created'][:10]
        if date_str not in by_date:
            by_date[date_str] = []
        by_date[date_str].append(item)
    
    # Escribir cada partición
    for date_str, items in by_date.items():
        key = f"metro/orders/date={date_str}/initial_load_{datetime.now().timestamp()}.json"
        
        # Escribir como JSONL (una línea por registro)
        body = '\n'.join([json.dumps(item) for item in items])
        
        s3.put_object(
            Bucket='cencosud-datalake-bronze',
            Key=key,
            Body=body,
            ContentType='application/x-ndjson'
        )
```

### Ejecución de Carga Inicial

```bash
# 1. Configurar credenciales
export AWS_PROFILE=cencosud-prod
export JANIS_MYSQL_HOST=janis-mysql.example.com

# 2. Ejecutar migración
python max/cargainicial/mysql_to_s3_bronze.py \
  --client metro \
  --start-date 2024-01-01 \
  --end-date 2026-02-26 \
  --batch-size 1000

# 3. Verificar datos en Bronze
aws s3 ls s3://cencosud-datalake-bronze/metro/orders/ --recursive | wc -l

# 4. Trigger pipeline Bronze→Silver
aws glue start-job-run \
  --job-name etl-bronze-to-silver-orders \
  --arguments '{"--client":"metro","--entity-type":"orders"}'
```

---

## Formato de Datos en Bronze

### Estructura de Archivos

```
s3://cencosud-datalake-bronze/
├── metro/
│   ├── orders/
│   │   ├── date=2026-02-26/
│   │   │   ├── webhook_ORD-001_1772122687.json      (Webhook)
│   │   │   ├── webhook_ORD-002_1772122700.json      (Webhook)
│   │   │   ├── polling_ORD-003_1772123000.json      (Polling)
│   │   │   └── initial_load_1772100000.json         (Carga inicial)
│   │   └── date=2026-02-27/
│   │       └── ...
│   ├── products/
│   │   └── date=2026-02-26/
│   │       └── ...
│   └── stock/
│       └── date=2026-02-26/
│           └── ...
└── wongio/
    └── orders/
        └── date=2026-02-26/
            └── ...
```

### Formato JSON con Metadata

**Archivo**: `webhook_ORD-METRO-001_1772122687.json`

```json
{
  "_metadata": {
    "client_id": "metro",
    "entity_type": "orders",
    "ingestion_timestamp": "2026-02-26T14:18:07.991Z",
    "source": "webhook",
    "api_version": "v2",
    "event_type": "order.updated",
    "webhook_timestamp": 1772122687991,
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
        "id": "item-ORD-METRO-001-1",
        "productId": "prod-metro-100",
        "skuId": "sku-metro-100-1",
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
        "id": "payment-ORD-METRO-001-1",
        "method": "credit_card",
        "amount": 250.75,
        "status": "approved",
        "transactionId": "txn-ORD-METRO-001"
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

### Campos de Metadata

| Campo | Tipo | Descripción | Ejemplo |
|-------|------|-------------|---------|
| `client_id` | string | Identificador del cliente | `"metro"`, `"wongio"` |
| `entity_type` | string | Tipo de entidad | `"orders"`, `"products"`, `"stock"` |
| `ingestion_timestamp` | string (ISO 8601) | Timestamp de ingesta | `"2026-02-26T14:18:07.991Z"` |
| `source` | string | Fuente de datos | `"webhook"`, `"polling"`, `"initial_load"` |
| `api_version` | string | Versión de API Janis | `"v2"` |
| `event_type` | string | Tipo de evento (opcional) | `"order.created"`, `"order.updated"` |
| `webhook_timestamp` | number | Timestamp del webhook (opcional) | `1772122687991` |
| `version` | number | Versión del registro (opcional) | `1`, `2`, `3` |

---

## Monitoreo de Ingesta

### Métricas de CloudWatch

**Webhooks**:
- `WebhookRequestCount`: Número de webhooks recibidos
- `WebhookErrorRate`: Tasa de error en procesamiento
- `WebhookLatency`: Latencia de procesamiento
- `KinesisRecordCount`: Registros enviados a Firehose

**Polling**:
- `PollingExecutionCount`: Ejecuciones del DAG
- `PollingRecordCount`: Registros obtenidos por polling
- `PollingDuplicateRate`: Tasa de duplicados detectados
- `PollingAPILatency`: Latencia de API Janis

### Alertas Configuradas

```json
{
  "AlarmName": "webhook-high-error-rate",
  "MetricName": "WebhookErrorRate",
  "Threshold": 5.0,
  "ComparisonOperator": "GreaterThanThreshold",
  "EvaluationPeriods": 2,
  "Period": 300,
  "Statistic": "Average",
  "ActionsEnabled": true,
  "AlarmActions": ["arn:aws:sns:us-east-1:123456789:data-engineering-alerts"]
}
```

---

**Última actualización**: 2026-02-26  
**Versión**: 1.0.0
