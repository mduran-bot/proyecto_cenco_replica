# Guía de Deployment en Producción - Sistema de Polling (Simplificado)

## ⚡ Resumen Ejecutivo

### ¿Qué hace este sistema?
Consulta automáticamente las APIs de Janis con diferentes frecuencias para obtener datos actualizados:
- **Cada 5 min:** Orders, Picking Sessions, Order History, Shipping
- **Cada 10 min:** Stock
- **Cada 30 min:** Prices, SC-SKU Prices
- **Cada 1 hora:** Products, SKUs, Categories, Brands
- **Cada 24 horas:** Stores, Carriers, Delivery Planning, Delivery Ranges

### 🏗️ Arquitectura Simplificada
```
EventBridge (NUESTRO) - Triggers programados
    ↓
Lambda Orchestrator (NUESTRO)
    ↓ [REST API call]
Airflow Externo (CENCOSUD)
    ↓ [Ejecuta DAGs]
Tu Código Python (max/polling/)
    ├─ acquire_lock (DynamoDB - NUESTRO)
    ├─ poll_api_raw (sin filtros, sin deduplicación)
    ├─ write_json_to_s3 (JSON crudo → S3 NUESTRO)
    └─ release_lock (DynamoDB - NUESTRO)
    ↓
S3 Bronze (JSON crudo particionado - NUESTRO)
```

### 🎯 Cambios Clave vs Versión Anterior
- ❌ **NO desplegamos MWAA propio** - Usamos Airflow existente de Cencosud
- ✅ **SÍ desplegamos EventBridge** - Triggers programados (nuestro)
- ✅ **SÍ desplegamos Lambda Orchestrator** - Llama a Airflow API (nuestro)
- ❌ **NO validamos datos** - Escribimos JSON crudo
- ❌ **NO enriquecemos datos** - Sin llamadas adicionales a APIs
- ❌ **NO deduplicamos** - Datos tal cual vienen de la API
- ❌ **NO usamos filtros incrementales** - Fetch completo cada vez
- ✅ **SÍ escribimos JSON** - Formato crudo, no Parquet
- ✅ **SÍ particionamos por fecha** - year=/month=/day=
- ✅ **SÍ usamos locks** - Control de concurrencia con DynamoDB

### 📦 Componentes a Entregar
1. **Código Python** (max/polling/) - DAGs y módulos
2. **Configuración** (api_config.json) - Endpoints y frecuencias
3. **Requirements** (requirements.txt) - Dependencias Python
4. **Documentación** - Esta guía

### 📊 Resultado Final
Después del deployment:
- **15 DAGs en Airflow de Cencosud** (uno por endpoint único)
- **15 endpoints** consultados con diferentes frecuencias
- **Archivos JSON crudos** en S3 Bronze particionados por fecha
- **Multi-tenant:** 2 carpetas (wongio/ y metro/) con 26 tablas cada una
- **ETL posterior** (Fase 5) procesa JSON → Parquet → Silver/Gold

### 📁 Estructura Multi-Tenant en S3 Bronze

```
s3://cencosud-datalake-bronze-prod/
├── wongio/                                    ← Cliente 1
│   ├── orders/                                ← Tabla 1: wms_orders
│   │   └── year=2026/month=03/day=04/
│   │       ├── 1709567890.json
│   │       ├── 1709568190.json
│   │       └── ...
│   ├── order_items/                           ← Tabla 2: wms_order_items
│   ├── order_item_weighables/                ← Tabla 3: wms_order_item_weighables
│   ├── order_payments/                        ← Tabla 4: wms_order_payments
│   ├── order_payments_connector_responses/   ← Tabla 5
│   ├── order_custom_data_fields/             ← Tabla 6
│   ├── invoices/                              ← Tabla 7
│   ├── picking_sessions/                      ← Tabla 8: wms_order_picking
│   ├── order_history/                         ← Tabla 9: wms_order_status_changes
│   ├── shipping/                              ← Tabla 10: wms_order_shipping
│   ├── stock/                                 ← Tabla 11: stock
│   ├── prices/                                ← Tabla 12: price
│   ├── sc_sku_prices/                         ← Tabla 13: price (store-specific)
│   ├── products/                              ← Tabla 14: products
│   ├── skus/                                  ← Tabla 15: skus
│   ├── categories/                            ← Tabla 16: categories
│   ├── brands/                                ← Tabla 17: brands
│   ├── stores/                                ← Tabla 18: wms_stores
│   ├── carriers/                              ← Tabla 19: wms_logistic_carriers
│   ├── delivery_planning/                     ← Tabla 20: wms_logistic_delivery_planning
│   ├── delivery_ranges/                       ← Tabla 21: wms_logistic_delivery_ranges
│   ├── admins/                                ← Tabla 22: admins (solo carga inicial)
│   ├── customers/                             ← Tabla 23: customers (solo carga inicial)
│   ├── order_weighables/                      ← Tabla 24
│   ├── order_payments_connector/              ← Tabla 25
│   └── order_custom_data/                     ← Tabla 26
│
└── metro/                                     ← Cliente 2 (misma estructura)
    ├── orders/
    ├── order_items/
    ├── ... (26 tablas idénticas)
    └── order_custom_data/

Total: 2 clientes × 26 tablas = 52 carpetas en S3 Bronze
```

**Características Multi-Tenant:**
- ✅ **Separación completa por cliente** - Cada cliente tiene su propia carpeta raíz
- ✅ **Misma estructura de tablas** - Las 26 tablas se replican para cada cliente
- ✅ **Particionamiento por fecha** - Dentro de cada tabla: year=/month=/day=/
- ✅ **Aislamiento de datos** - Los datos de wongio y metro nunca se mezclan
- ✅ **Escalabilidad** - Fácil agregar nuevos clientes (ej: cliente3/)

---

## Índice
1. [Prerequisitos](#prerequisitos)
2. [Estructura del Proyecto](#estructura-del-proyecto)
3. [Configuración de Secrets Manager](#configuración-de-secrets-manager)
4. [Deployment de Infraestructura AWS](#deployment-de-infraestructura-aws)
5. [Entrega de DAGs al Equipo de Cencosud](#entrega-de-dags-al-equipo-de-cencosud)
6. [Verificación y Monitoreo](#verificación-y-monitoreo)
7. [Troubleshooting](#troubleshooting)

---

## Prerequisitos

### Información Requerida del Equipo de Cencosud
- **URL de Airflow:** `https://airflow.cencosud.com` (ejemplo)
- **Credenciales de Airflow:** Username + Password para API REST
- **Permisos en Airflow:** Crear y ejecutar DAGs en el ambiente de producción

### Permisos Requeridos en AWS (Nuestra Cuenta)
- **EventBridge:** Crear rules y targets
- **Lambda:** Crear funciones y roles
- **S3:** Crear bucket Bronze y escribir objetos
- **DynamoDB:** Crear tabla de control de locks
- **Secrets Manager:** Crear y leer secrets
- **IAM:** Crear roles y policies
- **CloudWatch:** Crear log groups y escribir logs

### Recursos AWS a Desplegar (Nuestra Infraestructura)
- ✅ **EventBridge Rules:** 5 rules con diferentes frecuencias
- ✅ **Lambda Orchestrator:** Función que llama a Airflow API
- ✅ **S3 Bronze Bucket:** `cencosud-datalake-bronze-prod`
- ✅ **DynamoDB Table:** `polling-control` (para locks)
- ✅ **Secrets Manager:** 3 secrets (airflow-credentials, janis-metro, janis-wongio)
- ✅ **IAM Roles:** Para Lambda, EventBridge, y Airflow

### Credenciales API Janis
- API Key de Metro
- API Key de Wongio

---

## Estructura del Proyecto
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
---

## Estructura del Proyecto

```
max/polling/
├── config/
│   └── api_config.json              # Configuración de APIs y frecuencias
├── dags/
│   ├── base_polling_dag.py          # Factory de DAGs (simplificado)
│   ├── poll_orders.py               # DAG de orders (5 min)
│   ├── poll_stock.py                # DAG de stock (10 min)
│   ├── poll_prices.py               # DAG de prices (30 min)
│   ├── poll_catalog.py              # DAG de products (1 hora)
│   └── poll_stores.py               # DAG de stores (24 horas)
├── src/
│   ├── airflow_tasks.py             # Tareas simplificadas (4 funciones)
│   ├── api_client.py                # Cliente HTTP para APIs Janis
│   ├── pagination_handler.py        # Manejo de paginación
│   ├── s3_writer.py                 # Escritura de JSON a S3
│   └── state_manager.py             # Control de locks en DynamoDB
├── requirements.txt                 # Dependencias Python
└── DocumentacionProd/
    └── 04-DEPLOYMENT_PRODUCCION.md  # Esta guía
```

### Flujo Simplificado por DAG

Cada DAG ejecuta 4 tareas por cliente:

```python
# Ejemplo: poll_orders para cliente "wongio"

1. acquire_lock_wongio
   └─ Adquiere lock en DynamoDB (orders-wongio)
   
2. poll_api_wongio
   └─ Consulta https://oms.janis.in/api/order
   └─ Fetch completo (sin filtros)
   └─ Paginación automática
   └─ Retorna JSON crudo
   
3. write_to_s3_wongio
   └─ Escribe a s3://bucket/wongio/orders/year=2026/month=03/day=04/timestamp.json
   
4. release_lock_wongio
   └─ Libera lock en DynamoDB
   └─ Actualiza timestamp de última ejecución
```

### APIs y Frecuencias

| DAG | Endpoint | Base URL | Frecuencia | Tablas Cubiertas |
|-----|----------|----------|------------|------------------|
| poll_orders | order | https://oms.janis.in/api | 5 min | wms_orders, wms_order_items, wms_order_item_weighables, wms_order_payments, wms_order_payments_connector_responses, wms_order_custom_data_fields, invoices |
| poll_picking_sessions | session | https://picking.janis.in/api | 5 min | wms_order_picking |
| poll_order_history | order/{id}/history | https://oms.janis.in/api | 5 min | wms_order_status_changes |
| poll_shipping | shipping | https://delivery.janis.in/api | 5 min | wms_order_shipping |
| poll_stock | stock | https://wms.janis.in/api | 10 min | stock |
| poll_prices | price | https://pricing.janis.in/api | 30 min | price |
| poll_sc_sku_prices | sc-sku-price | https://pricing.janis.in/api | 30 min | price (store-specific) |
| poll_products | product | https://catalog.janis.in/api | 1 hora | products |
| poll_skus | sku | https://catalog.janis.in/api | 1 hora | skus |
| poll_categories | category | https://catalog.janis.in/api | 1 hora | categories |
| poll_brands | brand | https://catalog.janis.in/api | 1 hora | brands |
| poll_stores | stores | https://commerce.janis.in/api | 24 horas | wms_stores |
| poll_carriers | carrier | https://delivery.janis.in/api | 24 horas | wms_logistic_carriers |
| poll_delivery_planning | route-planning | https://tms.janis.in/api | 24 horas | wms_logistic_delivery_planning |
| poll_delivery_ranges | time-slot | https://delivery.janis.in/api | 24 horas | wms_logistic_delivery_ranges |

**Total:** 15 DAGs × 2 clientes = 30 ejecuciones por ciclo completo
**Cobertura:** 26 tablas de Janis (admins y customers solo en carga inicial)

---

## Configuración de IAM Roles

### 1. Rol para Lambda Orchestrator

**Nombre:** `janis-polling-lambda-orchestrator-role`

**Trust Policy:**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
```

**Policies necesarias:**

#### Policy 1: Secrets Manager Access
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "secretsmanager:GetSecretValue"
      ],
      "Resource": [
        "arn:aws:secretsmanager:us-east-1:ACCOUNT_ID:secret:airflow-credentials-*",
        "arn:aws:secretsmanager:us-east-1:ACCOUNT_ID:secret:janis-api-credentials-*"
      ]
    }
  ]
}
```

#### Policy 2: CloudWatch Logs
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogStream",
        "logs:CreateLogGroup",
        "logs:PutLogEvents"
      ],
      "Resource": "arn:aws:logs:us-east-1:ACCOUNT_ID:log-group:/aws/lambda/janis-polling-*"
    }
  ]
}
```

**Comando para crear el rol:**
```bash
# Crear archivo de trust policy
cat > lambda-trust-policy.json << EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF

# Crear rol
aws iam create-role \
  --role-name janis-polling-lambda-orchestrator-role \
  --assume-role-policy-document file://lambda-trust-policy.json

# Adjuntar policies
aws iam attach-role-policy \
  --role-name janis-polling-lambda-orchestrator-role \
  --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole

# Crear policy custom para Secrets Manager
cat > secrets-policy.json << EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": "secretsmanager:GetSecretValue",
      "Resource": "arn:aws:secretsmanager:us-east-1:ACCOUNT_ID:secret:*"
    }
  ]
}
EOF

aws iam put-role-policy \
  --role-name janis-polling-lambda-orchestrator-role \
  --policy-name SecretsManagerAccess \
  --policy-document file://secrets-policy.json
```

### 2. Secret para Credenciales de Airflow

**Nombre:** `airflow-credentials`

**Formato:**
```json
{
  "url": "https://airflow.cencosud.com",
  "username": "janis-polling-user",
  "password": "TU_PASSWORD_AIRFLOW"
}
```

**Comando:**
```bash
aws secretsmanager create-secret \
  --name airflow-credentials \
  --description "Credenciales para Airflow externo de Cencosud" \
  --secret-string '{"url":"https://airflow.cencosud.com","username":"janis-polling-user","password":"xxx"}' \
  --tags Key=Environment,Value=prod Key=Service,Value=polling
```

---

## Configuración de Secrets Manager

### Secret 1: Credenciales API Janis - Metro

**Nombre:** `janis-api-credentials-metro`

**Formato:**
```json
{
  "janis_client": "metro",
  "janis_api_key": "TU_API_KEY_METRO"
}
```

**Comando:**
```bash
aws secretsmanager create-secret \
  --name janis-api-credentials-metro \
  --description "Credenciales API Janis para cliente Metro" \
  --secret-string '{"janis_client":"metro","janis_api_key":"xxx"}' \
  --tags Key=Environment,Value=prod Key=Client,Value=metro
```

### Secret 2: Credenciales API Janis - Wongio

**Nombre:** `janis-api-credentials-wongio`

**Formato:**
```json
{
  "janis_client": "wongio",
  "janis_api_key": "TU_API_KEY_WONGIO"
}
```

**Comando:**
```bash
aws secretsmanager create-secret \
  --name janis-api-credentials-wongio \
  --description "Credenciales API Janis para cliente Wongio" \
  --secret-string '{"janis_client":"wongio","janis_api_key":"yyy"}' \
  --tags Key=Environment,Value=prod Key=Client,Value=wongio
```

---

## Deployment de Infraestructura AWS

### Componentes a Desplegar

**NUESTRA INFRAESTRUCTURA:**
1. EventBridge Rules (5 rules con diferentes frecuencias)
2. Lambda Orchestrator (llama a Airflow API de Cencosud)
3. DynamoDB Table (control de locks)
4. S3 Bronze Bucket (almacenamiento de JSON)
5. Secrets Manager (credenciales)
6. IAM Roles y Policies

**INFRAESTRUCTURA DE CENCOSUD (Externo):**
- Airflow (ejecuta nuestros DAGs)

---

### 1. Crear DynamoDB Table para Locks

```bash
aws dynamodb create-table \
  --table-name polling-control \
  --attribute-definitions \
    AttributeName=data_type,AttributeType=S \
  --key-schema \
    AttributeName=data_type,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --tags Key=Environment,Value=prod Key=Service,Value=polling
```

### 2. Verificar S3 Bronze Bucket

```bash
# Verificar si existe
aws s3 ls s3://cencosud-datalake-bronze-prod/

# Si no existe, crear
aws s3 mb s3://cencosud-datalake-bronze-prod --region us-east-1

# Habilitar versioning (opcional pero recomendado)
aws s3api put-bucket-versioning \
  --bucket cencosud-datalake-bronze-prod \
  --versioning-configuration Status=Enabled
```

### 3. Crear Lambda Orchestrator

**Función:** Recibe eventos de EventBridge y llama a Airflow API de Cencosud.

```python
# lambda_orchestrator.py
import json
import boto3
import requests
import os

def lambda_handler(event, context):
    """
    Orchestrator que recibe eventos de EventBridge y triggerea DAGs en Airflow de Cencosud.
    """
    # Obtener credenciales de Airflow desde Secrets Manager
    secrets_client = boto3.client('secretsmanager')
    secret = secrets_client.get_secret_value(SecretId='airflow-credentials')
    airflow_creds = json.loads(secret['SecretString'])
    
    # Extraer información del evento
    dag_id = event['dag_id']  # Ej: 'poll_orders'
    
    # Llamar a Airflow API
    airflow_url = f"{airflow_creds['url']}/api/v1/dags/{dag_id}/dagRuns"
    
    response = requests.post(
        airflow_url,
        auth=(airflow_creds['username'], airflow_creds['password']),
        json={"conf": {}},
        headers={'Content-Type': 'application/json'}
    )
    
    return {
        'statusCode': response.status_code,
        'body': json.dumps(f'Triggered DAG: {dag_id}')
    }
```

**Deployment:**
```bash
# Crear archivo ZIP
zip lambda_orchestrator.zip lambda_orchestrator.py

# Crear función Lambda
aws lambda create-function \
  --function-name janis-polling-orchestrator \
  --runtime python3.11 \
  --role arn:aws:iam::ACCOUNT_ID:role/janis-polling-lambda-role \
  --handler lambda_orchestrator.lambda_handler \
  --zip-file fileb://lambda_orchestrator.zip \
  --timeout 30 \
  --memory-size 256
```

### 4. Crear EventBridge Rules

**15 Rules con diferentes frecuencias:**

```bash
# ===== FRECUENCIA: 5 MINUTOS =====

# Rule 1: Orders
aws events put-rule \
  --name janis-polling-orders-5min \
  --schedule-expression "rate(5 minutes)" \
  --state ENABLED

aws events put-targets \
  --rule janis-polling-orders-5min \
  --targets "Id"="1","Arn"="arn:aws:lambda:us-east-1:ACCOUNT_ID:function:janis-polling-orchestrator","Input"='{"dag_id":"poll_orders"}'

# Rule 2: Picking Sessions
aws events put-rule \
  --name janis-polling-picking-sessions-5min \
  --schedule-expression "rate(5 minutes)" \
  --state ENABLED

aws events put-targets \
  --rule janis-polling-picking-sessions-5min \
  --targets "Id"="1","Arn"="arn:aws:lambda:us-east-1:ACCOUNT_ID:function:janis-polling-orchestrator","Input"='{"dag_id":"poll_picking_sessions"}'

# Rule 3: Order History
aws events put-rule \
  --name janis-polling-order-history-5min \
  --schedule-expression "rate(5 minutes)" \
  --state ENABLED

aws events put-targets \
  --rule janis-polling-order-history-5min \
  --targets "Id"="1","Arn"="arn:aws:lambda:us-east-1:ACCOUNT_ID:function:janis-polling-orchestrator","Input"='{"dag_id":"poll_order_history"}'

# Rule 4: Shipping
aws events put-rule \
  --name janis-polling-shipping-5min \
  --schedule-expression "rate(5 minutes)" \
  --state ENABLED

aws events put-targets \
  --rule janis-polling-shipping-5min \
  --targets "Id"="1","Arn"="arn:aws:lambda:us-east-1:ACCOUNT_ID:function:janis-polling-orchestrator","Input"='{"dag_id":"poll_shipping"}'

# ===== FRECUENCIA: 10 MINUTOS =====

# Rule 5: Stock
aws events put-rule \
  --name janis-polling-stock-10min \
  --schedule-expression "rate(10 minutes)" \
  --state ENABLED

aws events put-targets \
  --rule janis-polling-stock-10min \
  --targets "Id"="1","Arn"="arn:aws:lambda:us-east-1:ACCOUNT_ID:function:janis-polling-orchestrator","Input"='{"dag_id":"poll_stock"}'

# ===== FRECUENCIA: 30 MINUTOS =====

# Rule 6: Prices
aws events put-rule \
  --name janis-polling-prices-30min \
  --schedule-expression "rate(30 minutes)" \
  --state ENABLED

aws events put-targets \
  --rule janis-polling-prices-30min \
  --targets "Id"="1","Arn"="arn:aws:lambda:us-east-1:ACCOUNT_ID:function:janis-polling-orchestrator","Input"='{"dag_id":"poll_prices"}'

# Rule 7: SC-SKU Prices
aws events put-rule \
  --name janis-polling-sc-sku-prices-30min \
  --schedule-expression "rate(30 minutes)" \
  --state ENABLED

aws events put-targets \
  --rule janis-polling-sc-sku-prices-30min \
  --targets "Id"="1","Arn"="arn:aws:lambda:us-east-1:ACCOUNT_ID:function:janis-polling-orchestrator","Input"='{"dag_id":"poll_sc_sku_prices"}'

# ===== FRECUENCIA: 1 HORA =====

# Rule 8: Products
aws events put-rule \
  --name janis-polling-products-1hour \
  --schedule-expression "rate(1 hour)" \
  --state ENABLED

aws events put-targets \
  --rule janis-polling-products-1hour \
  --targets "Id"="1","Arn"="arn:aws:lambda:us-east-1:ACCOUNT_ID:function:janis-polling-orchestrator","Input"='{"dag_id":"poll_products"}'

# Rule 9: SKUs
aws events put-rule \
  --name janis-polling-skus-1hour \
  --schedule-expression "rate(1 hour)" \
  --state ENABLED

aws events put-targets \
  --rule janis-polling-skus-1hour \
  --targets "Id"="1","Arn"="arn:aws:lambda:us-east-1:ACCOUNT_ID:function:janis-polling-orchestrator","Input"='{"dag_id":"poll_skus"}'

# Rule 10: Categories
aws events put-rule \
  --name janis-polling-categories-1hour \
  --schedule-expression "rate(1 hour)" \
  --state ENABLED

aws events put-targets \
  --rule janis-polling-categories-1hour \
  --targets "Id"="1","Arn"="arn:aws:lambda:us-east-1:ACCOUNT_ID:function:janis-polling-orchestrator","Input"='{"dag_id":"poll_categories"}'

# Rule 11: Brands
aws events put-rule \
  --name janis-polling-brands-1hour \
  --schedule-expression "rate(1 hour)" \
  --state ENABLED

aws events put-targets \
  --rule janis-polling-brands-1hour \
  --targets "Id"="1","Arn"="arn:aws:lambda:us-east-1:ACCOUNT_ID:function:janis-polling-orchestrator","Input"='{"dag_id":"poll_brands"}'

# ===== FRECUENCIA: 24 HORAS =====

# Rule 12: Stores
aws events put-rule \
  --name janis-polling-stores-24hours \
  --schedule-expression "rate(24 hours)" \
  --state ENABLED

aws events put-targets \
  --rule janis-polling-stores-24hours \
  --targets "Id"="1","Arn"="arn:aws:lambda:us-east-1:ACCOUNT_ID:function:janis-polling-orchestrator","Input"='{"dag_id":"poll_stores"}'

# Rule 13: Carriers
aws events put-rule \
  --name janis-polling-carriers-24hours \
  --schedule-expression "rate(24 hours)" \
  --state ENABLED

aws events put-targets \
  --rule janis-polling-carriers-24hours \
  --targets "Id"="1","Arn"="arn:aws:lambda:us-east-1:ACCOUNT_ID:function:janis-polling-orchestrator","Input"='{"dag_id":"poll_carriers"}'

# Rule 14: Delivery Planning
aws events put-rule \
  --name janis-polling-delivery-planning-24hours \
  --schedule-expression "rate(24 hours)" \
  --state ENABLED

aws events put-targets \
  --rule janis-polling-delivery-planning-24hours \
  --targets "Id"="1","Arn"="arn:aws:lambda:us-east-1:ACCOUNT_ID:function:janis-polling-orchestrator","Input"='{"dag_id":"poll_delivery_planning"}'

# Rule 15: Delivery Ranges
aws events put-rule \
  --name janis-polling-delivery-ranges-24hours \
  --schedule-expression "rate(24 hours)" \
  --state ENABLED

aws events put-targets \
  --rule janis-polling-delivery-ranges-24hours \
  --targets "Id"="1","Arn"="arn:aws:lambda:us-east-1:ACCOUNT_ID:function:janis-polling-orchestrator","Input"='{"dag_id":"poll_delivery_ranges"}'
```

### 5. Dar Permisos a EventBridge para Invocar Lambda

```bash
aws lambda add-permission \
  --function-name janis-polling-orchestrator \
  --statement-id AllowEventBridgeInvoke \
  --action lambda:InvokeFunction \
  --principal events.amazonaws.com
```

### 6. Configurar IAM Role para Airflow (Cencosud)

**NOTA:** Este rol lo debe configurar el equipo de Cencosud en su Airflow.

El rol de ejecución de Airflow necesita permisos para acceder a NUESTROS recursos:

#### DynamoDB Access
```json
{
  "Effect": "Allow",
  "Action": [
    "dynamodb:GetItem",
    "dynamodb:PutItem",
    "dynamodb:UpdateItem"
  ],
  "Resource": "arn:aws:dynamodb:us-east-1:ACCOUNT_ID:table/polling-control"
}
```

#### S3 Access (Write to Bronze)
```json
{
  "Effect": "Allow",
  "Action": [
    "s3:PutObject",
    "s3:ListBucket"
  ],
  "Resource": [
    "arn:aws:s3:::cencosud-datalake-bronze-prod",
    "arn:aws:s3:::cencosud-datalake-bronze-prod/*"
  ]
}
```

#### Secrets Manager Access
```json
{
  "Effect": "Allow",
  "Action": "secretsmanager:GetSecretValue",
  "Resource": [
    "arn:aws:secretsmanager:us-east-1:ACCOUNT_ID:secret:janis-api-credentials-metro-*",
    "arn:aws:secretsmanager:us-east-1:ACCOUNT_ID:secret:janis-api-credentials-wongio-*"
  ]
}
```

---

## Entrega de DAGs al Equipo de Cencosud

### 1. Preparar Paquete de Entrega

```bash
cd max/polling

# Crear directorio de entrega
mkdir -p entrega-cencosud

# Copiar archivos necesarios
cp -r dags/ entrega-cencosud/
cp -r src/ entrega-cencosud/
cp -r config/ entrega-cencosud/
cp requirements.txt entrega-cencosud/
cp DocumentacionProd/04-DEPLOYMENT_PRODUCCION.md entrega-cencosud/README.md

# Crear archivo ZIP
cd entrega-cencosud
zip -r ../janis-polling-dags.zip .
cd ..
```

### 2. Contenido del Paquete

```
janis-polling-dags.zip
├── dags/
│   ├── base_polling_dag.py
│   ├── poll_orders.py
│   ├── poll_picking_sessions.py
│   ├── poll_order_history.py
│   ├── poll_shipping.py
│   ├── poll_stock.py
│   ├── poll_prices.py
│   ├── poll_sc_sku_prices.py
│   ├── poll_products.py
│   ├── poll_skus.py
│   ├── poll_categories.py
│   ├── poll_brands.py
│   ├── poll_stores.py
│   ├── poll_carriers.py
│   ├── poll_delivery_planning.py
│   └── poll_delivery_ranges.py
├── src/
│   ├── airflow_tasks.py
│   ├── api_client.py
│   ├── pagination_handler.py
│   ├── s3_writer.py
│   └── state_manager.py
├── config/
│   └── api_config.json
├── requirements.txt
└── README.md
```

### 3. Instrucciones para el Equipo de Cencosud

**Enviar al equipo de Cencosud:**

```
Asunto: Entrega de DAGs - Sistema de Polling Janis

Hola equipo,

Adjunto el paquete con los DAGs del sistema de polling de APIs Janis.

ARCHIVOS ADJUNTOS:
- janis-polling-dags.zip

INSTRUCCIONES DE INSTALACIÓN:

1. Descomprimir el ZIP en el directorio de DAGs de Airflow:
   unzip janis-polling-dags.zip -d /opt/airflow/dags/janis-polling/

2. Instalar dependencias Python:
   pip install -r /opt/airflow/dags/janis-polling/requirements.txt

3. Configurar variables de entorno en Airflow:
   - DYNAMODB_TABLE_NAME=polling-control
   - S3_BRONZE_BUCKET=cencosud-datalake-bronze-prod
   - AWS_REGION=us-east-1

4. Verificar que los secrets existan en Secrets Manager:
   - janis-api-credentials-metro
   - janis-api-credentials-wongio

5. Activar los DAGs en la UI de Airflow (15 DAGs):
   - poll_orders (5 min)
   - poll_picking_sessions (5 min)
   - poll_order_history (5 min)
   - poll_shipping (5 min)
   - poll_stock (10 min)
   - poll_prices (30 min)
   - poll_sc_sku_prices (30 min)
   - poll_products (1 hora)
   - poll_skus (1 hora)
   - poll_categories (1 hora)
   - poll_brands (1 hora)
   - poll_stores (24 horas)
   - poll_carriers (24 horas)
   - poll_delivery_planning (24 horas)
   - poll_delivery_ranges (24 horas)

6. Los DAGs serán triggereados automáticamente por nuestro EventBridge según sus frecuencias configuradas

CONTACTO:
Para cualquier duda, contactar a [TU_EMAIL]

Saludos,
[TU_NOMBRE]
```

---

## Verificación y Monitoreo

### 1. Verificar DAGs en Airflow

```bash
# Listar DAGs (desde Airflow CLI)
airflow dags list | grep poll_

# Debería mostrar 15 DAGs:
# poll_orders
# poll_picking_sessions
# poll_order_history
# poll_shipping
# poll_stock
# poll_prices
# poll_sc_sku_prices
# poll_products
# poll_skus
# poll_categories
# poll_brands
# poll_stores
# poll_carriers
# poll_delivery_planning
# poll_delivery_ranges
```

### 2. Trigger Manual de Prueba

```bash
# Trigger manual de un DAG
airflow dags trigger poll_orders

# Ver logs
airflow tasks logs poll_orders acquire_lock_wongio 2026-03-04
```

### 3. Verificar Datos en S3 (Multi-Tenant)

```bash
# Listar estructura de clientes
aws s3 ls s3://cencosud-datalake-bronze-prod/

# Debería mostrar:
# PRE wongio/
# PRE metro/

# Listar tablas de wongio
aws s3 ls s3://cencosud-datalake-bronze-prod/wongio/

# Debería mostrar 26 carpetas:
# PRE orders/
# PRE order_items/
# PRE picking_sessions/
# PRE stock/
# PRE prices/
# ... (26 tablas total)

# Ver archivos de una tabla específica
aws s3 ls s3://cencosud-datalake-bronze-prod/wongio/orders/ --recursive

# Debería mostrar:
# wongio/orders/year=2026/month=03/day=04/1709567890.json
# wongio/orders/year=2026/month=03/day=04/1709568190.json

# Verificar que metro tiene la misma estructura
aws s3 ls s3://cencosud-datalake-bronze-prod/metro/orders/ --recursive

# Debería mostrar:
# metro/orders/year=2026/month=03/day=04/1709567890.json
# metro/orders/year=2026/month=03/day=04/1709568190.json
```

### 4. Verificar Locks en DynamoDB

```bash
# Ver items en tabla de control
aws dynamodb scan --table-name polling-control

# Debería mostrar locks activos o timestamps de última ejecución
```

### 5. Monitoreo con CloudWatch

```bash
# Ver logs de Airflow
aws logs tail /aws/airflow/janis-polling --follow

# Buscar errores
aws logs filter-pattern "ERROR" --log-group-name /aws/airflow/janis-polling
```

---

## Troubleshooting

### Problema 1: DAG no aparece en Airflow

**Síntomas:**
- DAG no visible en UI de Airflow
- Error "DAG not found"

**Solución:**
```bash
# Verificar que el archivo esté en el directorio correcto
ls -la /opt/airflow/dags/janis-polling/dags/

# Verificar sintaxis Python
python -m py_compile /opt/airflow/dags/janis-polling/dags/poll_orders.py

# Refrescar DAGs en Airflow
airflow dags list-import-errors
```

### Problema 2: Error de credenciales API Janis

**Síntomas:**
- Error 401 Unauthorized
- "JANIS_API_KEY must be set"

**Solución:**
```bash
# Verificar que el secret exista
aws secretsmanager get-secret-value --secret-id janis-api-credentials-wongio

# Verificar permisos del rol de Airflow
aws iam get-role-policy --role-name airflow-execution-role --policy-name SecretsManagerAccess
```

### Problema 3: No se escriben datos a S3

**Síntomas:**
- DAG completa exitosamente
- No hay archivos en S3

**Solución:**
```bash
# Verificar permisos S3
aws s3api get-bucket-policy --bucket cencosud-datalake-bronze-prod

# Verificar logs de la tarea write_to_s3
airflow tasks logs poll_orders write_to_s3_wongio 2026-03-04

# Verificar variable de entorno
echo $S3_BRONZE_BUCKET
```

### Problema 4: Lock no se libera

**Síntomas:**
- DAG se salta (skip) en ejecuciones siguientes
- "Lock already exists"

**Solución:**
```bash
# Ver locks activos
aws dynamodb get-item \
  --table-name polling-control \
  --key '{"data_type":{"S":"orders-wongio"}}'

# Liberar lock manualmente (CUIDADO: solo si estás seguro)
aws dynamodb delete-item \
  --table-name polling-control \
  --key '{"data_type":{"S":"orders-wongio"}}'
```

### Problema 5: Paginación incompleta

**Síntomas:**
- Solo se obtienen 100 registros
- Faltan datos

**Solución:**
```python
# Verificar configuración de paginación en api_config.json
{
  "pagination": {
    "page_size": 100,
    "max_pages": 1000  # Aumentar si es necesario
  }
}
```

---

## Resumen de Comandos Útiles

```bash
# Verificar estado de DAGs
airflow dags list-runs -d poll_orders

# Ver última ejecución
airflow dags list-runs -d poll_orders --state success --limit 1

# Pausar DAG
airflow dags pause poll_orders

# Reanudar DAG
airflow dags unpause poll_orders

# Ver configuración
airflow config get-value core dags_folder

# Limpiar metadata de DAG
airflow dags delete poll_orders

# Verificar conexiones
airflow connections list

# Ver variables
airflow variables list
```

---

## Contacto y Soporte

Para soporte técnico o consultas:
- **Email:** [TU_EMAIL]
- **Slack:** #janis-cencosud-integration
- **Documentación:** Ver carpeta `DocumentacionProd/`

---

**Última actualización:** 2026-03-04  
**Versión:** 2.0 (Simplificada - JSON crudo)

### Secret 3: Credenciales API Janis - Wongio

**Nombre:** `janis-api-credentials-wongio`

**Formato:**
```json
{
  "janis_client": "wongio",
  "janis_api_key": "TU_API_KEY_WONGIO",
  "janis_api_secret": "TU_API_SECRET_WONGIO"
}
```

**Comando:**
```bash
aws secretsmanager create-secret \
  --name janis-api-credentials-wongio \
  --description "Credenciales API Janis para cliente Wongio" \
  --secret-string '{"janis_client":"wongio","janis_api_key":"xxx","janis_api_secret":"yyy"}' \
  --tags Key=Environment,Value=prod Key=Client,Value=wongio
```

---

## Deployment con Terraform

### 1. Actualizar prod.tfvars

Editar `max/polling/terraform/prod.tfvars`:

```hcl
# Reemplazar con ARNs reales
mwaa_execution_role_arn = "arn:aws:iam::181398079618:role/janis-polling-mwaa-execution-role"
eventbridge_role_arn = "arn:aws:iam::181398079618:role/janis-polling-eventbridge-role"

# Reemplazar con ARN real del secret
secrets_manager_arns = [
  "arn:aws:secretsmanager:us-east-1:181398079618:secret:janis-api-credentials-wongio-XXXXXX"
]

# Verificar configuración
vpc_id = "vpc-0e70f630594378796"
private_subnet_ids = [
  "subnet-0f96d2e7838f2789c",
  "subnet-0f2a9da0a0eb89bcc"
]

bronze_bucket_name = "cencosud-datalake-bronze-prod"
clients = ["wongio"]
polling_rate_minutes = 5

error_notification_emails = [
  "vicente.morales@externos-cl.cencosud.com"
]
```

### 2. Crear S3 Bronze Bucket (si no existe)

**NOTA:** Si el bucket ya existe, saltar este paso.

```bash
# Verificar si existe
aws s3 ls s3://cencosud-datalake-bronze-prod

# Si no existe, crear:
aws s3 mb s3://cencosud-datalake-bronze-prod
aws s3api put-bucket-versioning \
  --bucket cencosud-datalake-bronze-prod \
  --versioning-configuration Status=Enabled
```

### 3. Autenticarse en AWS

```bash
# Opción 1: SSO
aws configure sso

# Opción 2: Credenciales temporales
export AWS_ACCESS_KEY_ID="xxx"
export AWS_SECRET_ACCESS_KEY="xxx"
export AWS_SESSION_TOKEN="xxx"

# Verificar
aws sts get-caller-identity
```

### 4. Ejecutar Terraform

```bash
cd max/polling/terraform

# Inicializar
terraform init

# Validar
terraform validate
terraform fmt -check

# Ver plan
terraform plan -var-file="prod.tfvars"

# Aplicar (tarda 20-30 minutos)
terraform apply -var-file="prod.tfvars"
```

### 5. Guardar Outputs

```bash
terraform output > deployment-outputs.txt

# Guardar valores importantes
MWAA_BUCKET=$(terraform output -raw mwaa_s3_bucket_name)
MWAA_URL=$(terraform output -raw mwaa_webserver_url)
DYNAMODB_TABLE=$(terraform output -raw dynamodb_table_name)

echo "MWAA Bucket: $MWAA_BUCKET"
echo "MWAA URL: $MWAA_URL"
echo "DynamoDB Table: $DYNAMODB_TABLE"
```

---

## Configuración Post-Deployment

### 1. Subir DAGs a MWAA

```bash
cd max/polling

# Subir DAGs
aws s3 sync dags/ s3://$MWAA_BUCKET/dags/

# Subir requirements
aws s3 cp requirements.txt s3://$MWAA_BUCKET/requirements.txt

# Verificar
aws s3 ls s3://$MWAA_BUCKET/dags/
```

### 2. Configurar Variables en Airflow

1. Abrir Airflow UI: `$MWAA_URL`
2. Ir a: **Admin → Variables**
3. Agregar:

| Key | Value |
|-----|-------|
| `JANIS_API_BASE_URL` | `https://oms.janis.in/api` |
| `DYNAMODB_TABLE_NAME` | `janis-polling-prod-polling-control` |
| `S3_BRONZE_BUCKET` | `cencosud-datalake-bronze-prod` |
| `AWS_REGION` | `us-east-1` |

### 3. Verificar DAGs

En Airflow UI deberías ver:
- ✅ `poll_orders_wongio`
- ✅ `poll_products_wongio`
- ✅ `poll_stock_wongio`
- ✅ `poll_prices_wongio`
- ✅ `poll_stores_wongio`

Todos en estado **PAUSED** (pausados)

### 4. Activar DAGs

Toggle ON cada DAG. EventBridge los triggereará cada 5 minutos.

---

## Verificación y Monitoreo

### 1. Verificar EventBridge Rules

```bash
aws events list-rules --name-prefix janis-polling-prod

# Ver targets de una rule
aws events list-targets-by-rule --rule janis-polling-prod-poll-orders-wongio
```

### 2. Monitorear Logs

```bash
# Logs de DAG processor
aws logs tail /aws/mwaa/janis-polling-prod-mwaa-environment/dag_processor --follow

# Logs de tasks
aws logs tail /aws/mwaa/janis-polling-prod-mwaa-environment/task --follow

# Logs generales
aws logs tail /aws/api-polling/prod --follow
```

### 3. Verificar Primera Ejecución

Esperar 5-10 minutos y verificar:

```bash
# Ver datos en S3 Bronze
aws s3 ls s3://cencosud-datalake-bronze-prod/bronze/wongio/ --recursive

# Deberías ver:
# bronze/wongio/orders/year=2026/month=03/day=XX/data_HHMM.parquet
# bronze/wongio/products/year=2026/month=03/day=XX/data_HHMM.parquet
# ...
```

### 4. Verificar DynamoDB

```bash
aws dynamodb scan --table-name janis-polling-prod-polling-control

# Deberías ver 5 items:
# - orders-wongio
# - products-wongio
# - stock-wongio
# - prices-wongio
# - stores-wongio
```

### 5. Dashboard de Monitoreo

Crear dashboard en CloudWatch con métricas:
- MWAA: DAG runs, task success/failure
- DynamoDB: Read/Write capacity
- S3: Object count, storage size
- EventBridge: Invocations

---

## Multi-Tenant: Configuración y Escalabilidad

### ✅ Multi-Tenant YA Implementado

El sistema está diseñado para soportar múltiples clientes desde el inicio:

**Clientes Actuales:**
1. **wongio** - Cliente 1
2. **metro** - Cliente 2

**Cómo Funciona:**

```python
# Cada DAG procesa AMBOS clientes automáticamente
# Ejemplo: poll_orders.py

dag = create_polling_dag(
    dag_id='poll_orders',
    data_type='orders',
    clients=['metro', 'wongio'],  # ← Lista de clientes
    endpoint='order',
    base_url='https://oms.janis.in/api',
)

# Esto crea automáticamente tareas para cada cliente:
# - acquire_lock_wongio → poll_wongio → write_wongio → release_lock_wongio
# - acquire_lock_metro → poll_metro → write_metro → release_lock_metro
```

**Resultado en S3:**
```
s3://cencosud-datalake-bronze-prod/
├── wongio/
│   ├── orders/year=2026/month=03/day=04/1709567890.json
│   ├── stock/year=2026/month=03/day=04/1709567890.json
│   └── ... (26 tablas)
└── metro/
    ├── orders/year=2026/month=03/day=04/1709567890.json
    ├── stock/year=2026/month=03/day=04/1709567890.json
    └── ... (26 tablas)
```

### Agregar Nuevo Cliente (Ejemplo: cliente3)

#### 1. Crear Secret para el nuevo cliente

```bash
aws secretsmanager create-secret \
  --name janis-api-credentials-cliente3 \
  --secret-string '{"janis_client":"cliente3","janis_api_key":"xxx"}'
```

#### 2. Actualizar DAGs

Editar cada DAG para incluir el nuevo cliente:

```python
# En cada archivo poll_*.py
dag = create_polling_dag(
    dag_id='poll_orders',
    data_type='orders',
    clients=['metro', 'wongio', 'cliente3'],  # ← Agregar cliente3
    endpoint='order',
    base_url='https://oms.janis.in/api',
)
```

#### 3. Subir DAGs actualizados a Airflow

```bash
aws s3 sync dags/ s3://MWAA_BUCKET/dags/
```

#### 4. Verificar nueva estructura en S3

```bash
aws s3 ls s3://cencosud-datalake-bronze-prod/

# Debería mostrar:
# PRE wongio/
# PRE metro/
# PRE cliente3/  ← Nueva carpeta automáticamente creada

# Verificar que tiene las 26 tablas
aws s3 ls s3://cencosud-datalake-bronze-prod/cliente3/
```

### Ventajas del Diseño Multi-Tenant

✅ **Un solo DAG por endpoint** - No necesitas crear DAGs separados por cliente
✅ **Escalabilidad horizontal** - Agregar clientes es solo actualizar la lista
✅ **Aislamiento de datos** - Cada cliente tiene su carpeta raíz en S3
✅ **Procesamiento paralelo** - Tareas de diferentes clientes corren en paralelo
✅ **Mantenimiento simple** - Un cambio en el DAG aplica a todos los clientes
✅ **Cost tracking** - Fácil medir costos por cliente usando S3 tags

---

## Troubleshooting

### DAGs no aparecen en Airflow

**Causa:** DAGs no se subieron correctamente o hay errores de sintaxis

**Solución:**
```bash
# Verificar que se subieron
aws s3 ls s3://$MWAA_BUCKET/dags/

# Ver logs de DAG processor
aws logs tail /aws/mwaa/janis-polling-prod-mwaa-environment/dag_processor --follow

# Buscar errores de sintaxis
```

### Error de permisos en DynamoDB

**Causa:** Rol MWAA no tiene permisos

**Solución:**
```bash
# Verificar policies del rol
aws iam list-attached-role-policies --role-name janis-polling-mwaa-execution-role
aws iam list-role-policies --role-name janis-polling-mwaa-execution-role

# Verificar que la tabla existe
aws dynamodb describe-table --table-name janis-polling-prod-polling-control
```

### No se escriben datos a S3

**Causa:** Variable S3_BRONZE_BUCKET incorrecta o permisos

**Solución:**
```bash
# Verificar variable en Airflow UI
# Admin → Variables → S3_BRONZE_BUCKET

# Verificar permisos del rol en el bucket
aws s3api get-bucket-policy --bucket cencosud-datalake-bronze-prod

# Ver logs de tasks
aws logs tail /aws/mwaa/janis-polling-prod-mwaa-environment/task --follow | grep "S3"
```

### EventBridge no triggerea DAGs

**Causa:** Rol EventBridge sin permisos o MWAA ARN incorrecto

**Solución:**
```bash
# Verificar rules
aws events list-rules --name-prefix janis-polling-prod

# Ver targets
aws events list-targets-by-rule --rule janis-polling-prod-poll-orders-wongio

# Verificar que el ARN de MWAA es correcto
aws mwaa get-environment --name janis-polling-prod-mwaa-environment | grep arn
```

### Error al obtener secrets

**Causa:** Secret no existe o rol sin permisos

**Solución:**
```bash
# Verificar que el secret existe
aws secretsmanager describe-secret --secret-id janis-api-credentials-wongio

# Verificar permisos del rol
aws iam get-role-policy \
  --role-name janis-polling-mwaa-execution-role \
  --policy-name SecretsManagerAccess
```

### DAG falla con "Lock already exists"

**Causa:** Ejecución anterior no terminó o no liberó el lock

**Solución:**
```bash
# Ver estado en DynamoDB
aws dynamodb get-item \
  --table-name janis-polling-prod-polling-control \
  --key '{"data_type": {"S": "orders-wongio"}}'

# Si lock_acquired=true pero no hay ejecución activa, eliminar el lock:
aws dynamodb update-item \
  --table-name janis-polling-prod-polling-control \
  --key '{"data_type": {"S": "orders-wongio"}}' \
  --update-expression "SET lock_acquired = :false" \
  --expression-attribute-values '{":false": {"BOOL": false}}'
```

### ¿El polling sobrescribirá los datos de carga inicial?

**Respuesta:** NO. Los datos de carga inicial están seguros.

**Explicación:**
- Carga inicial: archivos en `bronze/wongio/stock/*.parquet` (raíz)
- Polling: archivos en `bronze/wongio/stock/year=2026/month=03/day=02/*.parquet` (subdirectorios)
- Son diferentes niveles de directorio, no hay conflicto

**Verificación:**
```bash
# Ver estructura completa
aws s3 ls s3://cencosud-datalake-bronze-prod/bronze/wongio/stock/ --recursive

# Deberías ver:
# stock_part1.parquet                                    ← Carga inicial
# stock_part2.parquet                                    ← Carga inicial
# year=2026/month=03/day=02/data_0900.parquet           ← Polling
# year=2026/month=03/day=02/data_0905.parquet           ← Polling
```

### ¿Cómo proceso ambos conjuntos de datos en Glue?

**Respuesta:** Spark lee automáticamente ambos.

```python
# Leer todo (carga inicial + polling)
df = spark.read.parquet("s3://bucket/bronze/wongio/stock/")

# Spark detecta automáticamente:
# - Archivos en raíz (carga inicial)
# - Archivos en subdirectorios particionados (polling)

# Deduplicar si hay registros repetidos
df_dedup = df.dropDuplicates(['sku_id', 'location_id'])
```

### ¿Puedo eliminar la carga inicial después de un tiempo?

**Respuesta:** SÍ, pero con cuidado.

**Estrategia recomendada:**
1. Esperar al menos 30 días de polling exitoso
2. Verificar que polling tiene todos los datos necesarios
3. Hacer backup de carga inicial antes de eliminar
4. Eliminar solo archivos de carga inicial (no las particiones)

```bash
# Backup de carga inicial
aws s3 sync \
  s3://cencosud-datalake-bronze-prod/bronze/wongio/stock/ \
  s3://cencosud-backups/bronze-inicial/wongio/stock/ \
  --exclude "year=*"

# Eliminar solo archivos de carga inicial (NO las particiones)
aws s3 rm s3://cencosud-datalake-bronze-prod/bronze/wongio/stock/ \
  --recursive --exclude "year=*" --include "*.parquet"
```

### ¿Qué pasa si hay duplicados entre carga inicial y polling?

**Respuesta:** Es normal y se maneja en el procesamiento.

**Escenario:**
- Carga inicial tiene SKU 12345 con stock 100 (fecha: 2026-02-15)
- Polling trae SKU 12345 con stock 95 (fecha: 2026-03-02)

**Solución en Glue:**
```python
from pyspark.sql.functions import col, row_number
from pyspark.sql.window import Window

# Leer todo
df = spark.read.parquet("s3://bucket/bronze/wongio/stock/")

# Quedarse con el registro más reciente
window = Window.partitionBy('sku_id', 'location_id').orderBy(
    col('_ingestion_timestamp').desc()
)

df_latest = df.withColumn(
    'row_num', row_number().over(window)
).filter(col('row_num') == 1).drop('row_num')

# Resultado: SKU 12345 con stock 95 (más reciente)
```

---

## Comandos Útiles

### Estado de MWAA
```bash
aws mwaa get-environment --name janis-polling-prod-mwaa-environment
```

### Trigger Manual de DAG
En Airflow UI: DAGs → [nombre_dag] → Trigger DAG

### Ver Métricas
```bash
# DynamoDB
aws cloudwatch get-metric-statistics \
  --namespace AWS/DynamoDB \
  --metric-name ConsumedReadCapacityUnits \
  --dimensions Name=TableName,Value=janis-polling-prod-polling-control \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Sum

# MWAA
aws cloudwatch get-metric-statistics \
  --namespace AWS/MWAA \
  --metric-name TaskSuccessCount \
  --dimensions Name=Environment,Value=janis-polling-prod-mwaa-environment \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Sum
```

### Limpiar Recursos (Destroy)
```bash
cd max/polling/terraform
terraform destroy -var-file="prod.tfvars"
```

---

## Checklist de Deployment

- [ ] Roles IAM creados (MWAA + EventBridge)
- [ ] Secrets Manager configurado (wongio)
- [ ] S3 Bronze bucket existe
- [ ] prod.tfvars actualizado con ARNs reales
- [ ] Terraform apply exitoso
- [ ] DAGs subidos a S3 MWAA bucket
- [ ] Variables configuradas en Airflow UI
- [ ] DAGs visibles en Airflow
- [ ] DAGs activados (toggle ON)
- [ ] EventBridge rules activas
- [ ] Primera ejecución exitosa
- [ ] Datos en S3 Bronze verificados
- [ ] DynamoDB con 5 items
- [ ] Logs sin errores
- [ ] Dashboard de monitoreo creado

---

## APIs Consultadas por el Sistema

### Resumen de Endpoints

El sistema consulta **5 DAGs principales** que hacen polling a diferentes APIs de Janis:

| DAG | API Base | Endpoints | Frecuencia | Datos |
|-----|----------|-----------|------------|-------|
| `poll_orders` | `https://oms.janis.in/api` | `/order` | 5 min | Órdenes |
| `poll_catalog` | `https://catalog.janis.in/api` | `/product`, `/sku`, `/category`, `/brand` | 5 min | Catálogo |
| `poll_stock` | `https://wms.janis.in/api` | `/sku-stock` | 5 min | Inventario |
| `poll_prices` | `https://vtex.pricing.janis.in/api` | `/price`, `/price-sheet`, `/base-price` | 5 min | Precios |
| `poll_stores` | `https://commerce.janis.in/api` | `/location` | 5 min | Tiendas |

### Detalle por DAG

#### 1. Orders (Órdenes)
- **DAG:** `poll_orders_wongio`, `poll_orders_metro`
- **API:** `https://oms.janis.in/api`
- **Endpoint:** `/order`
- **Método:** GET con filtros incrementales
- **Datos:** Órdenes de compra, estados, items

#### 2. Catalog (Catálogo)
- **DAG:** `poll_catalog_wongio`, `poll_catalog_metro`
- **API:** `https://catalog.janis.in/api`
- **Endpoints:**
  - `/product` - Productos
  - `/sku` - SKUs
  - `/category` - Categorías
  - `/brand` - Marcas
- **Método:** GET con filtros incrementales
- **Datos:** Información de productos y catálogo

#### 3. Stock (Inventario)
- **DAG:** `poll_stock_wongio`, `poll_stock_metro`
- **API:** `https://wms.janis.in/api`
- **Endpoint:** `/sku-stock`
- **Método:** GET con filtros incrementales
- **Datos:** Niveles de inventario por SKU

#### 4. Prices (Precios)
- **DAG:** `poll_prices_wongio`, `poll_prices_metro`
- **API:** `https://vtex.pricing.janis.in/api`
- **Endpoints:**
  - `/price` - Precios actuales
  - `/price-sheet` - Listas de precios
  - `/base-price` - Precios base
- **Método:** GET con filtros incrementales
- **Datos:** Precios y promociones

#### 5. Stores (Tiendas)
- **DAG:** `poll_stores_wongio`, `poll_stores_metro`
- **API:** `https://commerce.janis.in/api`
- **Endpoint:** `/location`
- **Método:** GET con filtros incrementales
- **Datos:** Información de tiendas y ubicaciones

### Total de DAGs y Ejecuciones

**DAGs únicos:** 15 (uno por endpoint)

**Ejecuciones por cliente:**
- Cada DAG procesa AMBOS clientes (wongio y metro) en la misma ejecución
- Dentro del DAG, se crean tareas separadas por cliente:
  - `acquire_lock_wongio` + `poll_wongio` + `write_wongio` + `release_lock_wongio`
  - `acquire_lock_metro` + `poll_metro` + `write_metro` + `release_lock_metro`

**Resultado en S3:**
- Cada ejecución de DAG escribe en 2 carpetas:
  - `s3://bucket/wongio/{tabla}/year=/month=/day=/timestamp.json`
  - `s3://bucket/metro/{tabla}/year=/month=/day=/timestamp.json`

**Total de carpetas en S3:** 2 clientes × 26 tablas = 52 carpetas

### Estructura Multi-Tenant de Datos en S3

Los datos se escriben con separación completa por cliente:

```
s3://cencosud-datalake-bronze-prod/
├── wongio/                                    ← CLIENTE 1
│   ├── orders/                                ← 7 tablas relacionadas
│   │   └── year=2026/month=03/day=04/
│   │       ├── 1709567890.json
│   │       └── 1709568190.json
│   ├── order_items/
│   ├── order_item_weighables/
│   ├── order_payments/
│   ├── order_payments_connector_responses/
│   ├── order_custom_data_fields/
│   ├── invoices/
│   ├── picking_sessions/                      ← 1 tabla
│   ├── order_history/                         ← 1 tabla
│   ├── shipping/                              ← 1 tabla
│   ├── stock/                                 ← 1 tabla
│   ├── prices/                                ← 2 tablas de precios
│   ├── sc_sku_prices/
│   ├── products/                              ← 4 tablas de catálogo
│   ├── skus/
│   ├── categories/
│   ├── brands/
│   ├── stores/                                ← 4 tablas de logística
│   ├── carriers/
│   ├── delivery_planning/
│   ├── delivery_ranges/
│   ├── admins/                                ← Solo carga inicial
│   └── customers/                             ← Solo carga inicial
│
└── metro/                                     ← CLIENTE 2 (misma estructura)
    ├── orders/
    │   └── year=2026/month=03/day=04/
    │       ├── 1709567890.json
    │       └── 1709568190.json
    ├── order_items/
    ├── ... (26 tablas idénticas a wongio)
    └── customers/

TOTAL: 2 clientes × 26 tablas = 52 carpetas
```

**Ventajas del Multi-Tenant:**
- ✅ Aislamiento completo de datos por cliente
- ✅ Fácil agregar nuevos clientes (solo crear nueva carpeta raíz)
- ✅ Permisos IAM granulares por cliente
- ✅ Billing y cost tracking por cliente
- ✅ Procesamiento independiente por cliente en ETL

### Autenticación

Todas las APIs usan el mismo método de autenticación:
- **Header:** `janis-client: wongio` (o `metro`)
- **Credenciales:** API Key + API Secret desde Secrets Manager
- **Secret:** `janis-api-credentials-wongio`

---

## Compatibilidad con Carga Inicial Existente

### ✅ NO HAY CONFLICTO entre Carga Inicial y Polling

**Situación Actual:**
- Tienes 2 carpetas en Bronze: `metroio/` y `wongio/`
- Cada carpeta tiene 26 tablas con datos de carga inicial
- Los archivos Parquet de carga inicial están SIN particionamiento

**Estructura de Carga Inicial:**
```
s3://cencosud-datalake-bronze-prod/
└── bronze/
    ├── metroio/
    │   ├── stock/
    │   │   ├── file1.parquet
    │   │   ├── file2.parquet
    │   │   └── file3.parquet
    │   ├── orders/
    │   │   └── *.parquet
    │   └── ... (24 tablas más)
    └── wongio/
        ├── stock/
        │   ├── file1.parquet
        │   ├── file2.parquet
        │   └── file3.parquet
        ├── orders/
        │   └── *.parquet
        └── ... (24 tablas más)
```

**Estructura de Polling (CON particionamiento):**
```
s3://cencosud-datalake-bronze-prod/
└── bronze/
    └── wongio/
        ├── stock/
        │   └── year=2026/
        │       └── month=03/
        │           └── day=02/
        │               ├── data_0900.parquet
        │               ├── data_0905.parquet
        │               └── data_0910.parquet
        ├── orders/
        │   └── year=2026/month=03/day=02/
        │       └── data_*.parquet
        └── ... (otros tipos de datos)
```

### 🎯 Por Qué NO Hay Conflicto

1. **Diferentes estructuras de path:**
   - Carga inicial: `bronze/wongio/stock/*.parquet` (archivos directos)
   - Polling: `bronze/wongio/stock/year=2026/month=03/day=02/*.parquet` (con particiones)

2. **Coexistencia pacífica:**
   - Los archivos de carga inicial permanecen intactos
   - Los archivos de polling se escriben en subdirectorios con particiones
   - Ambos pueden leerse simultáneamente

3. **Queries en Glue/Athena:**
   - Glue Crawler detectará automáticamente ambas estructuras
   - Athena puede consultar ambos conjuntos de datos
   - Las particiones de polling mejoran el rendimiento de queries recientes

### 📁 Diagrama de Estructura

```
s3://cencosud-datalake-bronze-prod/bronze/wongio/stock/
│
├── stock_part1.parquet              ← CARGA INICIAL (histórico)
├── stock_part2.parquet              ← CARGA INICIAL (histórico)
├── stock_part3.parquet              ← CARGA INICIAL (histórico)
│
└── year=2026/                       ← POLLING (incremental)
    ├── month=02/
    │   └── day=28/
    │       ├── data_0900.parquet
    │       ├── data_0905.parquet
    │       └── data_0910.parquet
    │
    └── month=03/
        ├── day=01/
        │   ├── data_0900.parquet
        │   └── ... (288 archivos por día)
        │
        └── day=02/
            ├── data_0900.parquet
            ├── data_0905.parquet
            └── data_0910.parquet

✅ NO HAY CONFLICTO: Diferentes niveles de directorio
✅ CARGA INICIAL: Archivos en raíz de stock/
✅ POLLING: Archivos en subdirectorios year=/month=/day=/
```

### 📊 Ejemplo Real

**Antes del Polling (solo carga inicial):**
```bash
aws s3 ls s3://cencosud-datalake-bronze-prod/bronze/wongio/stock/
# Resultado:
# 2026-02-15 10:00:00  1234567  stock_part1.parquet
# 2026-02-15 10:00:00  2345678  stock_part2.parquet
# 2026-02-15 10:00:00  3456789  stock_part3.parquet
```

**Después del Polling (carga inicial + polling):**
```bash
aws s3 ls s3://cencosud-datalake-bronze-prod/bronze/wongio/stock/ --recursive
# Resultado:
# 2026-02-15 10:00:00  1234567  stock_part1.parquet          ← Carga inicial
# 2026-02-15 10:00:00  2345678  stock_part2.parquet          ← Carga inicial
# 2026-02-15 10:00:00  3456789  stock_part3.parquet          ← Carga inicial
# 2026-03-02 09:00:00   123456  year=2026/month=03/day=02/data_0900.parquet  ← Polling
# 2026-03-02 09:05:00   234567  year=2026/month=03/day=02/data_0905.parquet  ← Polling
# 2026-03-02 09:10:00   345678  year=2026/month=03/day=02/data_0910.parquet  ← Polling
```

### 🔍 Ventajas de Esta Estructura

1. **Datos históricos preservados:** Carga inicial intacta
2. **Datos incrementales organizados:** Polling con particiones por fecha
3. **Queries eficientes:** Athena puede filtrar por particiones para datos recientes
4. **Fácil identificación:** Claro qué datos vienen de carga inicial vs polling
5. **Rollback simple:** Puedes eliminar particiones de polling sin afectar carga inicial

### 🛠️ Procesamiento en Glue

Cuando proceses estos datos en Glue (Bronze → Silver), puedes:

**Opción 1: Procesar todo junto (Recomendado para análisis completo)**
```python
# Leer todos los datos (carga inicial + polling)
df = spark.read.parquet("s3://bucket/bronze/wongio/stock/")

# Spark lee automáticamente:
# - stock_part1.parquet, stock_part2.parquet, ... (carga inicial)
# - year=2026/month=03/day=02/data_*.parquet (polling)

# Eliminar duplicados si es necesario
df_dedup = df.dropDuplicates(['sku_id', 'location_id'])
```

**Opción 2: Procesar solo polling (Recomendado para incrementales)**
```python
# Leer solo datos de polling (con particiones)
df_polling = spark.read.parquet(
    "s3://bucket/bronze/wongio/stock/year=*/month=*/day=*/"
)

# Útil para procesar solo datos recientes
# Ejemplo: últimos 7 días
from datetime import datetime, timedelta
fecha_inicio = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')

df_recent = spark.read.parquet(
    "s3://bucket/bronze/wongio/stock/"
).filter(f"partition_date >= '{fecha_inicio}'")
```

**Opción 3: Procesar solo carga inicial (Para análisis histórico)**
```python
# Leer solo archivos directos (sin particiones)
# Esto excluye los subdirectorios year=/month=/day=
from pyspark.sql.functions import input_file_name

df_all = spark.read.parquet("s3://bucket/bronze/wongio/stock/")

# Filtrar solo archivos en raíz (carga inicial)
df_inicial = df_all.filter(
    ~input_file_name().contains("year=")
)
```

**Opción 4: Merge inteligente (Recomendado para Silver)**
```python
# Estrategia: Carga inicial como base + polling como updates
from pyspark.sql.functions import col, max as spark_max

# 1. Leer carga inicial
df_inicial = spark.read.parquet("s3://bucket/bronze/wongio/stock/*.parquet")

# 2. Leer polling
df_polling = spark.read.parquet(
    "s3://bucket/bronze/wongio/stock/year=*/month=*/day=*/"
)

# 3. Union
df_combined = df_inicial.union(df_polling)

# 4. Quedarse con el registro más reciente por SKU
from pyspark.sql.window import Window

window = Window.partitionBy('sku_id', 'location_id').orderBy(
    col('_ingestion_timestamp').desc()
)

df_latest = df_combined.withColumn(
    'row_num', row_number().over(window)
).filter(col('row_num') == 1).drop('row_num')

# 5. Escribir a Silver
df_latest.write.format('iceberg').mode('overwrite').save(
    's3://bucket/silver/wongio/stock'
)
```

### 🔄 Estrategia de Procesamiento Recomendada

**Para el pipeline Bronze → Silver:**

1. **Primera vez (con carga inicial):**
   ```python
   # Procesar TODO (carga inicial completa)
   df = spark.read.parquet("s3://bucket/bronze/wongio/stock/")
   # Escribir a Silver
   ```

2. **Ejecuciones subsecuentes (solo incrementales):**
   ```python
   # Procesar solo polling del último día
   df_incremental = spark.read.parquet(
       f"s3://bucket/bronze/wongio/stock/year={year}/month={month}/day={day}/"
   )
   # Merge con Silver existente
   ```

3. **Reprocesamiento completo (si es necesario):**
   ```python
   # Procesar todo nuevamente
   df = spark.read.parquet("s3://bucket/bronze/wongio/stock/")
   # Sobrescribir Silver
   ```

### 📊 Ejemplo de Job Glue Completo

```python
import sys
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
from pyspark.sql.functions import col, row_number
from pyspark.sql.window import Window

args = getResolvedOptions(sys.argv, ['JOB_NAME', 'CLIENT', 'DATA_TYPE'])
sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args['JOB_NAME'], args)

client = args['CLIENT']  # wongio
data_type = args['DATA_TYPE']  # stock

# Leer Bronze (carga inicial + polling)
bronze_path = f"s3://cencosud-datalake-bronze-prod/bronze/{client}/{data_type}/"
df_bronze = spark.read.parquet(bronze_path)

# Deduplicar por clave primaria (quedarse con más reciente)
window = Window.partitionBy('sku_id', 'location_id').orderBy(
    col('_ingestion_timestamp').desc()
)

df_dedup = df_bronze.withColumn(
    'row_num', row_number().over(window)
).filter(col('row_num') == 1).drop('row_num')

# Escribir a Silver (Iceberg)
silver_path = f"s3://cencosud-datalake-silver-prod/silver/{client}/{data_type}"
df_dedup.write.format('iceberg').mode('overwrite').save(silver_path)

job.commit()
```

---

## Resumen Final: ¿Está Listo el Polling?

### ✅ SÍ, siguiendo estas instrucciones el polling estará 100% funcional

**Después de completar todos los pasos:**

1. ✅ **5 DAGs activos** consultando APIs cada 5 minutos
2. ✅ **10 endpoints** siendo polleados (orders, catalog x4, stock, prices x3, stores)
3. ✅ **Datos en S3 Bronze** en formato Parquet con particionamiento por fecha
4. ✅ **DynamoDB** controlando locks y estado de polling
5. ✅ **EventBridge** triggereando automáticamente cada 5 minutos
6. ✅ **Multi-tenant** listo para agregar Metro cuando tengas credenciales
7. ✅ **Compatible con carga inicial** - no sobrescribe ni elimina datos existentes

### 📊 Volumen de Datos Esperado

**Por ciclo de polling (cada 5 minutos):**
- Orders: ~100-500 registros
- Catalog: ~50-200 registros (por endpoint)
- Stock: ~1000-5000 registros
- Prices: ~100-500 registros (por endpoint)
- Stores: ~10-50 registros

**Por día:**
- ~288 ejecuciones (cada 5 min x 24 horas)
- ~10-50 archivos Parquet por tipo de dato
- ~1-5 GB de datos totales (comprimidos)

### 🎯 Verificación de Éxito

**Después de 1 hora de operación, deberías ver:**

```bash
# 12 archivos por tipo de dato (12 ciclos de 5 min)
aws s3 ls s3://cencosud-datalake-bronze-prod/bronze/wongio/orders/ --recursive | wc -l
# Resultado esperado: ~12

# Datos en DynamoDB
aws dynamodb scan --table-name janis-polling-prod-polling-control | grep data_type
# Resultado esperado: 10 items (orders, catalog_product, catalog_sku, etc.)

# Logs sin errores
aws logs tail /aws/mwaa/janis-polling-prod-mwaa-environment/task --since 1h | grep ERROR
# Resultado esperado: Sin errores críticos
```

---

## Contactos y Soporte

- **Infraestructura AWS:** Equipo DevOps Cencosud
- **Permisos IAM:** Equipo Security Cencosud
- **Credenciales Janis:** Proveedor Janis
- **Soporte Técnico:** vicente.morales@externos-cl.cencosud.com
