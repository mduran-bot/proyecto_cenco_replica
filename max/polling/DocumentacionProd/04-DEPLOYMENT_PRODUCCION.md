# Guía de Deployment en Producción - Sistema de Polling

## ⚡ Resumen Ejecutivo

### ¿Qué hace este sistema?
Consulta automáticamente las APIs de Janis cada 5 minutos para obtener datos actualizados de:
- Órdenes (orders)
- Productos (products)
- Inventario (stock)
- Precios (prices)
- Tiendas (stores)

### 🏗️ Arquitectura
```
EventBridge (cada 5 min)
    ↓
Lambda Orchestrator
    ↓ [REST API call]
Airflow Externo de Cencosud
    ↓ [Orquestación: acquire lock, poll API, write S3, release lock]
S3 Bronze (datos crudos JSON)
    ↓
ETL (Fase 5 - separado)
```

### ✅ Compatibilidad con Datos Existentes
**NO sobrescribe ni elimina la carga inicial de 26 tablas.**

- **Carga inicial:** Archivos en `bronze/wongio/stock/*.parquet` (raíz)
- **Polling:** Archivos en `bronze/wongio/stock/year=2026/month=03/day=02/*.json` (subdirectorios)
- **Resultado:** Ambos coexisten pacíficamente en diferentes niveles de directorio

### 🎯 Prerequisitos Críticos
Antes de empezar, necesitas:
1. **Acceso al Airflow de Cencosud** (URL + credenciales)
2. **3 Secrets** en Secrets Manager (airflow-credentials, janis-metro, janis-wongio)
3. **1 Rol IAM** para Lambda Orchestrator
4. **1 Rol IAM** para EventBridge
5. **S3 Bronze Bucket** (si no existe): `cencosud-datalake-bronze-prod`
6. **DynamoDB Table** para locks

### 📊 Resultado Final
Después del deployment:
- **10 DAGs en Airflow de Cencosud** (5 por cliente: metro, wongio)
- **10 endpoints** consultados cada 5 minutos
- **~288 archivos JSON por día** por tipo de dato
- **Datos particionados** por año/mes/día
- **ETL posterior** transforma JSON a Parquet (Fase 5)

---

## Índice
1. [Prerequisitos](#prerequisitos)
2. [Configuración de Roles IAM](#configuración-de-roles-iam)
3. [Configuración de Secrets Manager](#configuración-de-secrets-manager)
4. [Deployment de Infraestructura AWS](#deployment-de-infraestructura-aws)
5. [Entrega de DAGs al Equipo de Cencosud](#entrega-de-dags-al-equipo-de-cencosud)
6. [Verificación y Monitoreo](#verificación-y-monitoreo)
7. [Multi-Tenant: Agregar Nuevos Clientes](#multi-tenant-agregar-nuevos-clientes)
8. [Troubleshooting](#troubleshooting)

---

## Prerequisitos

### Información Requerida del Equipo de Cencosud
- **URL de Airflow:** `https://airflow.cencosud.com` (ejemplo)
- **Credenciales de Airflow:** Username + Password para API REST
- **Permisos en Airflow:** Crear y ejecutar DAGs en el ambiente de producción

### Permisos Requeridos en AWS
- **Usuario con permisos IAM** para crear roles y policies
- **Usuario con permisos Secrets Manager** para crear secrets
- **Usuario con permisos para:**
  - Lambda (crear funciones)
  - EventBridge (crear rules)
  - DynamoDB (crear tablas)
  - S3 (crear buckets y escribir objetos)
  - CloudWatch (crear log groups)

### Recursos Existentes
- ⚠️ S3 Bronze Bucket: `cencosud-datalake-bronze-prod` (crear si no existe)
- ⚠️ Airflow de Cencosud (externo, gestionado por equipo de Cencosud)

### Credenciales API Janis
- API Key de Metro
- API Secret de Metro
- API Key de Wongio
- API Secret de Wongio

---

## Configuración de Roles IAM

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
        "secretsmanager:GetSecretValue",
        "secretsmanager:DescribeSecret"
      ],
      "Resource": "arn:aws:secretsmanager:us-east-1:181398079618:secret:airflow-credentials-*"
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
      "Resource": "arn:aws:logs:us-east-1:181398079618:log-group:/aws/lambda/janis-polling-*"
    }
  ]
}
```

**Comando para crear el rol:**
```bash
aws iam create-role \
  --role-name janis-polling-lambda-orchestrator-role \
  --assume-role-policy-document file://lambda-trust-policy.json

aws iam put-role-policy \
  --role-name janis-polling-lambda-orchestrator-role \
  --policy-name SecretsManagerAccess \
  --policy-document file://secrets-policy.json

aws iam put-role-policy \
  --role-name janis-polling-lambda-orchestrator-role \
  --policy-name CloudWatchLogs \
  --policy-document file://cloudwatch-policy.json
```

### 2. Rol para EventBridge

**Nombre:** `janis-polling-eventbridge-role`

**Trust Policy:**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "events.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
```

**Policy:**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": "lambda:InvokeFunction",
      "Resource": "arn:aws:lambda:us-east-1:181398079618:function:janis-polling-orchestrator"
    }
  ]
}
```

**Comando para crear:**
```bash
aws iam create-role \
  --role-name janis-polling-eventbridge-role \
  --assume-role-policy-document file://eventbridge-trust-policy.json

aws iam put-role-policy \
  --role-name janis-polling-eventbridge-role \
  --policy-name LambdaInvoke \
  --policy-document file://eventbridge-policy.json
```

### 3. Permisos para Airflow de Cencosud (Gestionado por Cencosud)

**NOTA:** Estos permisos los debe configurar el equipo de Cencosud en su Airflow.

El rol de ejecución de Airflow necesita:

#### DynamoDB Access
```json
{
  "Effect": "Allow",
  "Action": [
    "dynamodb:GetItem",
    "dynamodb:PutItem",
    "dynamodb:UpdateItem"
  ],
  "Resource": "arn:aws:dynamodb:us-east-1:181398079618:table/janis-polling-prod-polling-control"
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
    "arn:aws:s3:::cencosud-datalake-bronze-prod/raw/*"
  ]
}
```

#### Secrets Manager Access
```json
{
  "Effect": "Allow",
  "Action": "secretsmanager:GetSecretValue",
  "Resource": [
    "arn:aws:secretsmanager:us-east-1:181398079618:secret:janis-api-credentials-metro-*",
    "arn:aws:secretsmanager:us-east-1:181398079618:secret:janis-api-credentials-wongio-*"
  ]
}
```

---

## Configuración de Secrets Manager

### Secret 1: Credenciales de Airflow

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

### Secret 2: Credenciales API Janis - Metro

**Nombre:** `janis-api-credentials-metro`

**Formato:**
```json
{
  "janis_client": "metro",
  "janis_api_key": "TU_API_KEY_METRO",
  "janis_api_secret": "TU_API_SECRET_METRO"
}
```

**Comando:**
```bash
aws secretsmanager create-secret \
  --name janis-api-credentials-metro \
  --description "Credenciales API Janis para cliente Metro" \
  --secret-string '{"janis_client":"metro","janis_api_key":"xxx","janis_api_secret":"yyy"}' \
  --tags Key=Environment,Value=prod Key=Client,Value=metro
```

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

## Multi-Tenant: Agregar Nuevos Clientes

### Agregar Metro

#### 1. Crear Secret

```bash
aws secretsmanager create-secret \
  --name janis-api-credentials-metro \
  --secret-string '{"api_key":"xxx","api_secret":"yyy"}'
```

#### 2. Actualizar prod.tfvars

```hcl
# Agregar metro a la lista
clients = ["wongio", "metro"]

# Agregar ARN del secret
secrets_manager_arns = [
  "arn:aws:secretsmanager:us-east-1:181398079618:secret:janis-api-credentials-wongio-*",
  "arn:aws:secretsmanager:us-east-1:181398079618:secret:janis-api-credentials-metro-*"
]
```

#### 3. Aplicar Terraform

```bash
terraform plan -var-file="prod.tfvars"
terraform apply -var-file="prod.tfvars"
```

Esto creará automáticamente:
- 5 nuevas EventBridge rules para Metro
- Los DAGs detectarán el nuevo cliente automáticamente

#### 4. Verificar Nuevos DAGs

En Airflow UI deberías ver 5 DAGs adicionales:
- `poll_orders_metro`
- `poll_products_metro`
- `poll_stock_metro`
- `poll_prices_metro`
- `poll_stores_metro`

#### 5. Activar DAGs de Metro

Toggle ON los nuevos DAGs.

#### 6. Verificar Datos

```bash
aws s3 ls s3://cencosud-datalake-bronze-prod/bronze/metro/ --recursive
```

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

### Total de DAGs Creados

Con la configuración actual (`clients = ["wongio"]`):
- **5 DAGs** (uno por tipo de dato)

Cuando agregues Metro (`clients = ["wongio", "metro"]`):
- **10 DAGs** (5 por cliente)

### Estructura de Datos en S3

Los datos se escriben en:
```
s3://cencosud-datalake-bronze-prod/
└── bronze/
    └── wongio/
        ├── orders/
        │   └── year=2026/month=03/day=02/data_HHMM.parquet
        ├── catalog_product/
        │   └── year=2026/month=03/day=02/data_HHMM.parquet
        ├── catalog_sku/
        │   └── year=2026/month=03/day=02/data_HHMM.parquet
        ├── catalog_category/
        │   └── year=2026/month=03/day=02/data_HHMM.parquet
        ├── catalog_brand/
        │   └── year=2026/month=03/day=02/data_HHMM.parquet
        ├── stock/
        │   └── year=2026/month=03/day=02/data_HHMM.parquet
        ├── prices_price/
        │   └── year=2026/month=03/day=02/data_HHMM.parquet
        ├── prices_price_sheet/
        │   └── year=2026/month=03/day=02/data_HHMM.parquet
        ├── prices_base_price/
        │   └── year=2026/month=03/day=02/data_HHMM.parquet
        └── stores/
            └── year=2026/month=03/day=02/data_HHMM.parquet
```

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
