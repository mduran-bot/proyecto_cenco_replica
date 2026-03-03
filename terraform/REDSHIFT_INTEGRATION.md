# Redshift Integration Documentation
## Janis-Cencosud Data Integration Platform

**Versión**: 1.0  
**Fecha**: 26 de Enero, 2026  
**Propósito**: Documentación de integración con infraestructura Redshift existente de Cencosud

---

## 1. RESUMEN EJECUTIVO

Este documento describe la integración de la nueva infraestructura AWS de Janis-Cencosud con el cluster Amazon Redshift existente de Cencosud. La integración está diseñada para:

- Mantener compatibilidad con sistemas BI existentes
- Proporcionar acceso seguro desde nuevos componentes (Lambda, MWAA, Glue)
- Permitir migración gradual desde el pipeline MySQL→Redshift actual
- No interrumpir operaciones actuales de Redshift

### 1.1 Componentes de Integración

- **Security Group SG-Redshift-Existing**: Control de acceso a nivel de red
- **VPC Endpoints**: Conectividad privada para servicios AWS
- **IAM Roles**: Permisos para acceso desde Lambda, MWAA, Glue
- **Secrets Manager**: Almacenamiento seguro de credenciales de Redshift

---

## 2. CONFIGURACIÓN EXISTENTE DE REDSHIFT

### 2.1 Información del Cluster Requerida

Antes de implementar la integración, el cliente debe proporcionar la siguiente información del cluster Redshift existente:

```yaml
Redshift_Cluster_Information:
  # Identificación del Cluster
  Cluster_Identifier: "<CLUSTER_ID>"
  Cluster_Endpoint: "<CLUSTER_ENDPOINT>.us-east-1.redshift.amazonaws.com"
  Port: 5439
  Database_Name: "<DATABASE_NAME>"
  
  # Configuración de Red
  VPC_ID: "<VPC_ID>"
  Subnet_IDs:
    - "<SUBNET_ID_1>"
    - "<SUBNET_ID_2>"
  Availability_Zone: "<AZ>" # e.g., us-east-1a, us-east-1b
  
  # Seguridad
  Security_Group_ID: "<EXISTING_REDSHIFT_SG_ID>"
  Encryption_At_Rest: true/false
  KMS_Key_ID: "<KMS_KEY_ID>" # Si encryption está habilitado
  
  # Configuración de Acceso
  Master_Username: "<MASTER_USER>"
  IAM_Roles_Attached:
    - "<IAM_ROLE_ARN_1>"
    - "<IAM_ROLE_ARN_2>"
```


### 2.2 Sistemas BI Existentes

Documentar todos los sistemas BI que actualmente acceden a Redshift:

```yaml
Existing_BI_Systems:
  System_1:
    Name: "<BI_SYSTEM_NAME>" # e.g., "Power BI Gateway"
    Security_Group_ID: "<BI_SG_ID>"
    IP_Ranges: ["<IP_CIDR_1>", "<IP_CIDR_2>"]
    Connection_Type: "Direct" # Direct, VPN, PrivateLink
    Access_Pattern: "Read-only queries"
    
  System_2:
    Name: "<BI_SYSTEM_NAME>" # e.g., "Tableau Server"
    Security_Group_ID: "<BI_SG_ID>"
    IP_Ranges: ["<IP_CIDR_1>"]
    Connection_Type: "Direct"
    Access_Pattern: "Read-only queries"
```

**Acción Requerida**: El cliente debe proporcionar esta información para configurar correctamente SG-Redshift-Existing sin interrumpir acceso actual.

### 2.3 Pipeline MySQL→Redshift Actual

Documentar el pipeline de migración actual que será reemplazado:

```yaml
Current_MySQL_Pipeline:
  Source:
    Type: "MySQL Database"
    Location: "<MYSQL_HOST>"
    Database: "<MYSQL_DATABASE>"
  
  Migration_Tool:
    Type: "<TOOL_NAME>" # e.g., AWS DMS, Custom ETL
    Security_Group_ID: "<MYSQL_PIPELINE_SG_ID>"
    IP_Range: "<PIPELINE_IP_CIDR>"
  
  Schedule:
    Frequency: "<FREQUENCY>" # e.g., "Every 6 hours"
    Last_Run: "<TIMESTAMP>"
  
  Migration_Status:
    Status: "Active" # Active, Deprecated, To be replaced
    Replacement_Timeline: "<DATE>"
```

**Nota Importante**: Durante la transición, ambos pipelines (MySQL→Redshift y Janis→Redshift) operarán simultáneamente. El security group debe permitir acceso desde ambos.

---

## 3. REQUISITOS DE CONECTIVIDAD DE RED

### 3.1 Escenario 1: Redshift en la Misma VPC

Si el cluster Redshift existente está en la misma VPC (10.0.0.0/16):

```yaml
Network_Configuration:
  Scenario: "Same VPC"
  
  Connectivity:
    - Source: "Lambda Functions (Private Subnet 1A)"
      Destination: "Redshift Cluster"
      Protocol: "TCP"
      Port: 5439
      Routing: "Direct (within VPC)"
    
    - Source: "MWAA Environment (Private Subnet 1A)"
      Destination: "Redshift Cluster"
      Protocol: "TCP"
      Port: 5439
      Routing: "Direct (within VPC)"
    
    - Source: "Glue Jobs (Private Subnet 2A)"
      Destination: "Redshift Cluster"
      Protocol: "TCP"
      Port: 5439
      Routing: "Direct (within VPC)"
  
  Security_Groups:
    Action: "Add inbound rules to existing Redshift SG"
    Rules_To_Add:
      - "PostgreSQL (5439) from SG-Lambda"
      - "PostgreSQL (5439) from SG-MWAA"
      - "PostgreSQL (5439) from SG-Glue (optional)"
```

**Ventajas**:
- Latencia mínima
- Sin costos de transferencia de datos
- Configuración simple


### 3.2 Escenario 2: Redshift en VPC Diferente

Si el cluster Redshift está en una VPC diferente:

```yaml
Network_Configuration:
  Scenario: "Different VPC"
  
  Options:
    Option_1_VPC_Peering:
      Description: "Establecer VPC Peering entre VPCs"
      Steps:
        - "Crear VPC Peering Connection"
        - "Aceptar peering en VPC de Redshift"
        - "Actualizar route tables en ambas VPCs"
        - "Actualizar security groups para permitir tráfico"
      Cost: "Sin costo por peering, solo data transfer"
      Latency: "Baja (dentro de AWS)"
      
    Option_2_PrivateLink:
      Description: "Usar AWS PrivateLink para acceso privado"
      Steps:
        - "Crear VPC Endpoint Service en VPC de Redshift"
        - "Crear VPC Endpoint en VPC nueva (10.0.0.0/16)"
        - "Configurar security groups"
      Cost: "$0.01/hora + $0.01/GB = ~$7.20/mes + data transfer"
      Latency: "Baja (dentro de AWS)"
      
    Option_3_Public_Endpoint:
      Description: "Acceso vía endpoint público de Redshift (NO RECOMENDADO)"
      Security_Risk: "Alto - tráfico sale de AWS network"
      Cost: "Data transfer out charges"
      Recommendation: "Evitar esta opción por seguridad"
```

**Recomendación**: VPC Peering es la opción más simple y sin costo adicional. PrivateLink proporciona mayor aislamiento si se requiere.

### 3.3 Verificación de Conectividad

Después de configurar la red, verificar conectividad:

```bash
# Desde Lambda o EC2 en Private Subnet 1A
nc -zv <REDSHIFT_ENDPOINT> 5439

# O usando psql
psql -h <REDSHIFT_ENDPOINT> -p 5439 -U <USERNAME> -d <DATABASE> -c "SELECT 1;"

# Verificar resolución DNS
nslookup <REDSHIFT_ENDPOINT>
```

---

## 4. CONFIGURACIÓN DE SECURITY GROUPS

### 4.1 Security Group SG-Redshift-Existing

Este security group controla el acceso al cluster Redshift existente. Debe ser actualizado para permitir conexiones desde los nuevos componentes.

```hcl
# Configuración de Terraform para SG-Redshift-Existing
resource "aws_security_group" "redshift_existing" {
  name        = "${var.name_prefix}-sg-redshift"
  description = "Security group for existing Redshift cluster"
  vpc_id      = var.vpc_id

  # Inbound Rules
  
  # Regla 1: Acceso desde Lambda
  ingress {
    description     = "PostgreSQL from Lambda functions"
    from_port       = 5439
    to_port         = 5439
    protocol        = "tcp"
    security_groups = [aws_security_group.lambda.id]
  }

  # Regla 2: Acceso desde MWAA
  ingress {
    description     = "PostgreSQL from MWAA Airflow"
    from_port       = 5439
    to_port         = 5439
    protocol        = "tcp"
    security_groups = [aws_security_group.mwaa.id]
  }

  # Regla 3: Acceso desde sistemas BI existentes
  ingress {
    description     = "PostgreSQL from existing BI systems"
    from_port       = 5439
    to_port         = 5439
    protocol        = "tcp"
    security_groups = var.existing_bi_security_groups
  }

  # Regla 4: Acceso desde pipeline MySQL actual (temporal)
  ingress {
    description     = "PostgreSQL from MySQL migration pipeline (temporary)"
    from_port       = 5439
    to_port         = 5439
    protocol        = "tcp"
    security_groups = [var.existing_mysql_pipeline_sg_id]
  }

  # Regla 5 (Opcional): Acceso desde Glue
  ingress {
    description     = "PostgreSQL from Glue jobs (optional)"
    from_port       = 5439
    to_port         = 5439
    protocol        = "tcp"
    security_groups = [aws_security_group.glue.id]
  }

  # Outbound Rules
  
  # Regla 1: HTTPS a VPC Endpoints
  egress {
    description     = "HTTPS to VPC Endpoints"
    from_port       = 443
    to_port         = 443
    protocol        = "tcp"
    security_groups = [aws_security_group.vpc_endpoints.id]
  }

  tags = merge(var.common_tags, {
    Name      = "${var.name_prefix}-sg-redshift"
    Component = "redshift"
  })
}
```


### 4.2 Variables Requeridas

```hcl
# terraform/variables.tf

variable "existing_redshift_sg_id" {
  description = "Security Group ID of existing Redshift cluster"
  type        = string
  default     = ""
  
  validation {
    condition     = can(regex("^sg-[a-f0-9]+$", var.existing_redshift_sg_id)) || var.existing_redshift_sg_id == ""
    error_message = "Redshift Security Group ID must be a valid SG ID (sg-xxxxxxxx) or empty string."
  }
}

variable "existing_bi_security_groups" {
  description = "List of Security Group IDs for existing BI systems accessing Redshift"
  type        = list(string)
  default     = []
}

variable "existing_bi_ip_ranges" {
  description = "List of IP CIDR ranges for existing BI systems (if not using security groups)"
  type        = list(string)
  default     = []
}

variable "existing_mysql_pipeline_sg_id" {
  description = "Security Group ID of current MySQL→Redshift migration pipeline (temporary)"
  type        = string
  default     = ""
}

variable "redshift_cluster_endpoint" {
  description = "Endpoint of existing Redshift cluster"
  type        = string
  default     = ""
}

variable "redshift_database_name" {
  description = "Database name in Redshift cluster"
  type        = string
  default     = "cencosud_dw"
}

variable "redshift_port" {
  description = "Port number for Redshift cluster"
  type        = number
  default     = 5439
}
```

### 4.3 Configuración en terraform.tfvars

```hcl
# terraform/terraform.tfvars

# Existing Redshift Configuration
existing_redshift_sg_id       = "sg-0123456789abcdef0"
redshift_cluster_endpoint     = "cencosud-redshift.c1a2b3c4d5e6.us-east-1.redshift.amazonaws.com"
redshift_database_name        = "cencosud_dw"
redshift_port                 = 5439

# Existing BI Systems
existing_bi_security_groups = [
  "sg-0a1b2c3d4e5f6g7h8",  # Power BI Gateway
  "sg-9i8h7g6f5e4d3c2b1"   # Tableau Server
]

# Alternative: Use IP ranges if security groups not available
existing_bi_ip_ranges = [
  "10.100.50.0/24",  # BI Network Range 1
  "10.100.51.0/24"   # BI Network Range 2
]

# MySQL Migration Pipeline (temporary)
existing_mysql_pipeline_sg_id = "sg-mysql123456789"
```

---

## 5. GESTIÓN DE CREDENCIALES

### 5.1 Almacenamiento en AWS Secrets Manager

Las credenciales de Redshift deben almacenarse en AWS Secrets Manager para acceso seguro desde Lambda, MWAA y Glue.

```json
{
  "secret_name": "janis-cencosud/redshift/credentials",
  "secret_value": {
    "host": "cencosud-redshift.c1a2b3c4d5e6.us-east-1.redshift.amazonaws.com",
    "port": 5439,
    "database": "cencosud_dw",
    "username": "janis_integration_user",
    "password": "<SECURE_PASSWORD>",
    "schema": "janis_data"
  }
}
```

### 5.2 Creación del Secret

```bash
# Crear secret en Secrets Manager
aws secretsmanager create-secret \
  --name janis-cencosud/redshift/credentials \
  --description "Redshift credentials for Janis-Cencosud integration" \
  --secret-string '{
    "host": "cencosud-redshift.c1a2b3c4d5e6.us-east-1.redshift.amazonaws.com",
    "port": 5439,
    "database": "cencosud_dw",
    "username": "janis_integration_user",
    "password": "SECURE_PASSWORD_HERE",
    "schema": "janis_data"
  }' \
  --tags Key=Project,Value=janis-cencosud-integration \
         Key=Environment,Value=production \
         Key=Component,Value=redshift-credentials

# Habilitar rotación automática (opcional pero recomendado)
aws secretsmanager rotate-secret \
  --secret-id janis-cencosud/redshift/credentials \
  --rotation-lambda-arn <ROTATION_LAMBDA_ARN> \
  --rotation-rules AutomaticallyAfterDays=30
```


### 5.3 Usuario de Base de Datos Dedicado

Crear un usuario dedicado en Redshift para la integración Janis:

```sql
-- Conectarse a Redshift como master user
-- Crear usuario para integración Janis
CREATE USER janis_integration_user WITH PASSWORD '<SECURE_PASSWORD>';

-- Crear schema dedicado para datos de Janis
CREATE SCHEMA IF NOT EXISTS janis_data;

-- Otorgar permisos necesarios
GRANT USAGE ON SCHEMA janis_data TO janis_integration_user;
GRANT CREATE ON SCHEMA janis_data TO janis_integration_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA janis_data TO janis_integration_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA janis_data GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO janis_integration_user;

-- Permisos de lectura en otros schemas si es necesario
GRANT USAGE ON SCHEMA public TO janis_integration_user;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO janis_integration_user;

-- Verificar permisos
SELECT 
    schemaname,
    tablename,
    HAS_TABLE_PRIVILEGE('janis_integration_user', schemaname||'.'||tablename, 'SELECT') as can_select,
    HAS_TABLE_PRIVILEGE('janis_integration_user', schemaname||'.'||tablename, 'INSERT') as can_insert
FROM pg_tables
WHERE schemaname IN ('janis_data', 'public')
ORDER BY schemaname, tablename;
```

**Principio de Menor Privilegio**: El usuario solo debe tener permisos en el schema `janis_data` y lectura en schemas necesarios para joins.

### 5.4 Acceso desde Lambda

```python
# lambda/webhook-processor/handler.py
import boto3
import psycopg2
import json

def get_redshift_credentials():
    """Retrieve Redshift credentials from Secrets Manager"""
    client = boto3.client('secretsmanager', region_name='us-east-1')
    
    response = client.get_secret_value(
        SecretId='janis-cencosud/redshift/credentials'
    )
    
    return json.loads(response['SecretString'])

def connect_to_redshift():
    """Establish connection to Redshift"""
    creds = get_redshift_credentials()
    
    conn = psycopg2.connect(
        host=creds['host'],
        port=creds['port'],
        database=creds['database'],
        user=creds['username'],
        password=creds['password'],
        sslmode='require',
        connect_timeout=10
    )
    
    return conn

def lambda_handler(event, context):
    """Lambda handler for Redshift operations"""
    try:
        conn = connect_to_redshift()
        cursor = conn.cursor()
        
        # Execute query
        cursor.execute("SELECT 1;")
        result = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'Connected successfully'})
        }
    except Exception as e:
        print(f"Error connecting to Redshift: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
```

### 5.5 Acceso desde MWAA (Airflow)

```python
# airflow/dags/dag_load_to_redshift.py
from airflow import DAG
from airflow.providers.amazon.aws.hooks.redshift_sql import RedshiftSQLHook
from airflow.operators.python import PythonOperator
from datetime import datetime

def load_data_to_redshift(**context):
    """Load data to Redshift using Airflow connection"""
    # Airflow connection configurada con Secrets Manager backend
    redshift_hook = RedshiftSQLHook(redshift_conn_id='redshift_janis')
    
    sql = """
    COPY janis_data.orders
    FROM 's3://cencosud-datalake-gold/orders/'
    IAM_ROLE '<REDSHIFT_IAM_ROLE_ARN>'
    FORMAT AS PARQUET;
    """
    
    redshift_hook.run(sql)

with DAG(
    'load_to_redshift',
    start_date=datetime(2026, 1, 1),
    schedule_interval=None,
    catchup=False
) as dag:
    
    load_task = PythonOperator(
        task_id='load_data',
        python_callable=load_data_to_redshift
    )
```

---

## 6. MIGRACIÓN DESDE MYSQL→REDSHIFT

### 6.1 Estrategia de Migración

La migración del pipeline actual MySQL→Redshift al nuevo pipeline Janis→Redshift debe ser gradual:

```yaml
Migration_Strategy:
  Phase_1_Parallel_Operation:
    Duration: "2-4 weeks"
    Description: "Ambos pipelines operan simultáneamente"
    Actions:
      - "Mantener pipeline MySQL→Redshift activo"
      - "Activar pipeline Janis→Redshift en paralelo"
      - "Comparar datos entre ambos pipelines"
      - "Validar integridad y completitud de datos"
    
  Phase_2_Validation:
    Duration: "1-2 weeks"
    Description: "Validación exhaustiva de datos"
    Actions:
      - "Ejecutar queries de reconciliación"
      - "Comparar métricas de negocio"
      - "Validar con usuarios de BI"
      - "Identificar y resolver discrepancias"
    
  Phase_3_Cutover:
    Duration: "1 day"
    Description: "Cambio al nuevo pipeline"
    Actions:
      - "Deshabilitar pipeline MySQL→Redshift"
      - "Confirmar pipeline Janis→Redshift como primario"
      - "Monitorear métricas de carga"
      - "Mantener pipeline MySQL como backup por 1 semana"
    
  Phase_4_Decommission:
    Duration: "1 week"
    Description: "Desmantelamiento del pipeline antiguo"
    Actions:
      - "Remover regla de security group para MySQL pipeline"
      - "Desactivar recursos de MySQL pipeline"
      - "Archivar configuración para referencia"
      - "Actualizar documentación"
```


### 6.2 Queries de Reconciliación

```sql
-- Comparar conteos de registros entre pipelines
-- Tabla de órdenes
SELECT 
    'MySQL Pipeline' as source,
    COUNT(*) as order_count,
    MIN(created_at) as earliest_order,
    MAX(created_at) as latest_order
FROM mysql_schema.orders
UNION ALL
SELECT 
    'Janis Pipeline' as source,
    COUNT(*) as order_count,
    MIN(created_at) as earliest_order,
    MAX(created_at) as latest_order
FROM janis_data.orders;

-- Comparar sumas de métricas clave
SELECT 
    'MySQL Pipeline' as source,
    SUM(total_amount) as total_revenue,
    COUNT(DISTINCT customer_id) as unique_customers,
    COUNT(DISTINCT product_id) as unique_products
FROM mysql_schema.orders
WHERE created_at >= CURRENT_DATE - 7
UNION ALL
SELECT 
    'Janis Pipeline' as source,
    SUM(total_amount) as total_revenue,
    COUNT(DISTINCT customer_id) as unique_customers,
    COUNT(DISTINCT product_id) as unique_products
FROM janis_data.orders
WHERE created_at >= CURRENT_DATE - 7;

-- Identificar registros faltantes
SELECT 'Missing in Janis' as issue, m.order_id, m.created_at
FROM mysql_schema.orders m
LEFT JOIN janis_data.orders j ON m.order_id = j.order_id
WHERE j.order_id IS NULL
  AND m.created_at >= CURRENT_DATE - 7
UNION ALL
SELECT 'Missing in MySQL' as issue, j.order_id, j.created_at
FROM janis_data.orders j
LEFT JOIN mysql_schema.orders m ON j.order_id = m.order_id
WHERE m.order_id IS NULL
  AND j.created_at >= CURRENT_DATE - 7;
```

### 6.3 Plan de Rollback

En caso de problemas durante la migración:

```yaml
Rollback_Plan:
  Trigger_Conditions:
    - "Discrepancias de datos > 1%"
    - "Latencia de carga > 2x esperada"
    - "Errores de conexión frecuentes"
    - "Feedback negativo de usuarios BI"
  
  Rollback_Steps:
    Step_1:
      Action: "Deshabilitar pipeline Janis→Redshift"
      Command: "aws events disable-rule --name poll-orders-schedule"
      Duration: "5 minutos"
    
    Step_2:
      Action: "Verificar pipeline MySQL→Redshift activo"
      Command: "Verificar última ejecución exitosa"
      Duration: "10 minutos"
    
    Step_3:
      Action: "Notificar a stakeholders"
      Method: "Email + Slack"
      Duration: "Inmediato"
    
    Step_4:
      Action: "Investigar causa raíz"
      Duration: "Variable"
    
    Step_5:
      Action: "Planificar reintento"
      Duration: "Variable"
  
  Data_Preservation:
    - "Mantener datos de Janis en schema separado"
    - "No eliminar datos durante rollback"
    - "Preservar logs para análisis"
```

---

## 7. MONITOREO Y PERFORMANCE

### 7.1 Métricas de Redshift a Monitorear

```yaml
Redshift_Metrics:
  Connection_Metrics:
    - "DatabaseConnections": "Número de conexiones activas"
    - "PercentageDiskSpaceUsed": "Uso de disco del cluster"
    - "CPUUtilization": "Uso de CPU"
    - "NetworkReceiveThroughput": "Throughput de red entrante"
    - "NetworkTransmitThroughput": "Throughput de red saliente"
  
  Query_Performance:
    - "QueryDuration": "Duración de queries"
    - "QueryThroughput": "Queries por segundo"
    - "ConcurrencyScalingActivity": "Uso de concurrency scaling"
  
  Load_Performance:
    - "LoadThroughput": "Throughput de COPY commands"
    - "LoadDuration": "Duración de cargas"
    - "RowsLoaded": "Filas cargadas por operación"
```

### 7.2 CloudWatch Alarms para Redshift

```hcl
# terraform/modules/monitoring/redshift_alarms.tf

resource "aws_cloudwatch_metric_alarm" "redshift_cpu_high" {
  alarm_name          = "${var.name_prefix}-redshift-cpu-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "CPUUtilization"
  namespace           = "AWS/Redshift"
  period              = "300"
  statistic           = "Average"
  threshold           = "80"
  alarm_description   = "Redshift CPU utilization is too high"
  alarm_actions       = [var.alarm_sns_topic_arn]

  dimensions = {
    ClusterIdentifier = var.redshift_cluster_id
  }
}

resource "aws_cloudwatch_metric_alarm" "redshift_disk_space_high" {
  alarm_name          = "${var.name_prefix}-redshift-disk-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "1"
  metric_name         = "PercentageDiskSpaceUsed"
  namespace           = "AWS/Redshift"
  period              = "300"
  statistic           = "Average"
  threshold           = "85"
  alarm_description   = "Redshift disk space usage is too high"
  alarm_actions       = [var.alarm_sns_topic_arn]

  dimensions = {
    ClusterIdentifier = var.redshift_cluster_id
  }
}

resource "aws_cloudwatch_metric_alarm" "redshift_connections_high" {
  alarm_name          = "${var.name_prefix}-redshift-connections-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "DatabaseConnections"
  namespace           = "AWS/Redshift"
  period              = "300"
  statistic           = "Average"
  threshold           = "450"  # Ajustar según límite del cluster
  alarm_description   = "Redshift connection count is too high"
  alarm_actions       = [var.alarm_sns_topic_arn]

  dimensions = {
    ClusterIdentifier = var.redshift_cluster_id
  }
}
```


### 7.3 Queries de Diagnóstico

```sql
-- Ver conexiones activas
SELECT 
    process,
    user_name,
    db_name,
    starttime,
    duration,
    query
FROM stv_sessions
WHERE user_name = 'janis_integration_user'
ORDER BY starttime DESC;

-- Ver queries lentas
SELECT 
    query,
    userid,
    starttime,
    endtime,
    DATEDIFF(seconds, starttime, endtime) as duration_seconds,
    substring(querytxt, 1, 100) as query_text
FROM stl_query
WHERE userid = (SELECT usesysid FROM pg_user WHERE usename = 'janis_integration_user')
  AND DATEDIFF(seconds, starttime, endtime) > 30
ORDER BY duration_seconds DESC
LIMIT 20;

-- Ver uso de espacio por tabla
SELECT 
    schema,
    "table",
    size,
    tbl_rows,
    size / NULLIF(tbl_rows, 0) as bytes_per_row
FROM svv_table_info
WHERE schema = 'janis_data'
ORDER BY size DESC;

-- Ver estadísticas de COPY
SELECT 
    query,
    starttime,
    endtime,
    DATEDIFF(seconds, starttime, endtime) as duration_seconds,
    rows,
    bytes,
    bytes / NULLIF(DATEDIFF(seconds, starttime, endtime), 0) as bytes_per_second
FROM stl_load_commits
WHERE filename LIKE '%janis%'
ORDER BY starttime DESC
LIMIT 20;
```

---

## 8. OPTIMIZACIÓN DE PERFORMANCE

### 8.1 Connection Pooling

Implementar connection pooling para reducir overhead de conexiones:

```python
# lambda/shared/redshift_pool.py
import psycopg2
from psycopg2 import pool
import boto3
import json

class RedshiftConnectionPool:
    _instance = None
    _pool = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(RedshiftConnectionPool, cls).__new__(cls)
        return cls._instance
    
    def initialize(self, minconn=1, maxconn=10):
        """Initialize connection pool"""
        if self._pool is None:
            creds = self._get_credentials()
            
            self._pool = psycopg2.pool.ThreadedConnectionPool(
                minconn,
                maxconn,
                host=creds['host'],
                port=creds['port'],
                database=creds['database'],
                user=creds['username'],
                password=creds['password'],
                sslmode='require',
                connect_timeout=10
            )
    
    def _get_credentials(self):
        """Retrieve credentials from Secrets Manager"""
        client = boto3.client('secretsmanager', region_name='us-east-1')
        response = client.get_secret_value(
            SecretId='janis-cencosud/redshift/credentials'
        )
        return json.loads(response['SecretString'])
    
    def get_connection(self):
        """Get connection from pool"""
        if self._pool is None:
            self.initialize()
        return self._pool.getconn()
    
    def return_connection(self, conn):
        """Return connection to pool"""
        if self._pool is not None:
            self._pool.putconn(conn)
    
    def close_all(self):
        """Close all connections in pool"""
        if self._pool is not None:
            self._pool.closeall()

# Usage in Lambda
pool = RedshiftConnectionPool()

def lambda_handler(event, context):
    conn = pool.get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT 1;")
        result = cursor.fetchone()
        cursor.close()
        return {'statusCode': 200, 'body': 'Success'}
    finally:
        pool.return_connection(conn)
```

### 8.2 Optimización de Tablas

```sql
-- Definir distribution keys y sort keys apropiados
CREATE TABLE janis_data.orders (
    order_id VARCHAR(50) NOT NULL,
    customer_id VARCHAR(50),
    store_id VARCHAR(50),
    order_date TIMESTAMP,
    total_amount DECIMAL(10,2),
    status VARCHAR(20),
    created_at TIMESTAMP,
    updated_at TIMESTAMP
)
DISTKEY(customer_id)  -- Distribuir por customer_id para joins eficientes
SORTKEY(order_date);  -- Ordenar por fecha para queries temporales

-- Crear índices para queries frecuentes
CREATE INDEX idx_orders_customer ON janis_data.orders(customer_id);
CREATE INDEX idx_orders_store ON janis_data.orders(store_id);
CREATE INDEX idx_orders_date ON janis_data.orders(order_date);

-- Ejecutar VACUUM y ANALYZE regularmente
VACUUM DELETE ONLY janis_data.orders;
ANALYZE janis_data.orders;
```

### 8.3 Uso de COPY en lugar de INSERT

```sql
-- MALO: INSERT individual (muy lento)
INSERT INTO janis_data.orders VALUES (...);

-- BUENO: COPY desde S3 (mucho más rápido)
COPY janis_data.orders
FROM 's3://cencosud-datalake-gold/orders/2026/01/26/'
IAM_ROLE 'arn:aws:iam::123456789012:role/RedshiftCopyRole'
FORMAT AS PARQUET
COMPUPDATE ON
STATUPDATE ON;

-- MEJOR: COPY con manifest para múltiples archivos
COPY janis_data.orders
FROM 's3://cencosud-datalake-gold/orders/manifest.json'
IAM_ROLE 'arn:aws:iam::123456789012:role/RedshiftCopyRole'
FORMAT AS PARQUET
MANIFEST;
```

---

## 9. SEGURIDAD Y COMPLIANCE

### 9.1 Cifrado

```yaml
Encryption_Configuration:
  At_Rest:
    Enabled: true
    Method: "AWS KMS"
    KMS_Key: "<KMS_KEY_ID>"
    Scope: "All data blocks and snapshots"
  
  In_Transit:
    Enabled: true
    Method: "SSL/TLS"
    Minimum_Version: "TLS 1.2"
    Certificate: "AWS managed certificate"
  
  Backup_Encryption:
    Enabled: true
    Method: "Same as cluster encryption"
```

### 9.2 Auditoría

```sql
-- Habilitar logging de auditoría en Redshift
-- (Configurado en AWS Console o CLI)

-- Ver logs de conexiones
SELECT 
    event,
    recordtime,
    username,
    remotehost,
    remoteport
FROM stl_connection_log
WHERE username = 'janis_integration_user'
ORDER BY recordtime DESC
LIMIT 100;

-- Ver logs de autenticación
SELECT 
    event,
    recordtime,
    username,
    remotehost,
    success
FROM stl_userlog
WHERE username = 'janis_integration_user'
ORDER BY recordtime DESC
LIMIT 100;
```

### 9.3 Compliance Checklist

```yaml
Compliance_Requirements:
  Access_Control:
    - "✓ Principio de menor privilegio aplicado"
    - "✓ Usuario dedicado con permisos limitados"
    - "✓ Credenciales en Secrets Manager"
    - "✓ Rotación de credenciales habilitada"
  
  Network_Security:
    - "✓ Security groups restrictivos"
    - "✓ Tráfico solo desde fuentes autorizadas"
    - "✓ VPC Endpoints para tráfico privado"
    - "✓ No acceso público a Redshift"
  
  Encryption:
    - "✓ Cifrado en reposo habilitado"
    - "✓ Cifrado en tránsito (SSL/TLS)"
    - "✓ KMS para gestión de claves"
  
  Auditing:
    - "✓ CloudWatch Logs habilitado"
    - "✓ VPC Flow Logs capturando tráfico"
    - "✓ Redshift audit logging habilitado"
    - "✓ CloudTrail para API calls"
  
  Backup_Recovery:
    - "✓ Automated snapshots habilitados"
    - "✓ Retention period configurado"
    - "✓ Cross-region backup (si requerido)"
```

---

## 10. TROUBLESHOOTING

### 10.1 Problemas Comunes

#### Problema 1: Connection Timeout

```yaml
Symptom: "Connection timeout after 10 seconds"
Possible_Causes:
  - "Security group no permite tráfico desde source"
  - "NACL bloqueando tráfico"
  - "Redshift cluster no está en running state"
  - "DNS resolution fallando"

Solutions:
  1. "Verificar security group rules"
  2. "Verificar NACL rules"
  3. "Verificar estado del cluster: aws redshift describe-clusters"
  4. "Verificar DNS: nslookup <REDSHIFT_ENDPOINT>"
  5. "Verificar VPC peering si aplica"
```


#### Problema 2: Authentication Failed

```yaml
Symptom: "FATAL: password authentication failed"
Possible_Causes:
  - "Credenciales incorrectas en Secrets Manager"
  - "Usuario no existe en Redshift"
  - "Password expirado"
  - "Usuario bloqueado por intentos fallidos"

Solutions:
  1. "Verificar credenciales en Secrets Manager"
  2. "Verificar usuario existe: SELECT * FROM pg_user WHERE usename = 'janis_integration_user';"
  3. "Resetear password si es necesario"
  4. "Desbloquear usuario si está bloqueado"
```

#### Problema 3: Slow Query Performance

```yaml
Symptom: "Queries toman mucho tiempo"
Possible_Causes:
  - "Tablas no tienen distribution/sort keys"
  - "Estadísticas desactualizadas"
  - "Necesita VACUUM"
  - "Cluster undersized"

Solutions:
  1. "Ejecutar ANALYZE en tablas"
  2. "Ejecutar VACUUM DELETE ONLY"
  3. "Revisar query execution plan: EXPLAIN <query>"
  4. "Considerar resize del cluster"
  5. "Optimizar distribution y sort keys"
```

#### Problema 4: Disk Space Full

```yaml
Symptom: "ERROR: disk full"
Possible_Causes:
  - "Demasiados datos sin VACUUM"
  - "Snapshots ocupando espacio"
  - "Tablas temporales no limpiadas"

Solutions:
  1. "Ejecutar VACUUM FULL (requiere downtime)"
  2. "Eliminar snapshots antiguos"
  3. "Limpiar tablas temporales"
  4. "Considerar resize del cluster"
  5. "Implementar data lifecycle policies"
```

### 10.2 Comandos de Diagnóstico

```bash
# Verificar conectividad desde Lambda/EC2
nc -zv <REDSHIFT_ENDPOINT> 5439

# Test de conexión con psql
psql -h <REDSHIFT_ENDPOINT> -p 5439 -U janis_integration_user -d cencosud_dw -c "SELECT 1;"

# Verificar security group rules
aws ec2 describe-security-groups --group-ids <SG_ID>

# Verificar estado del cluster
aws redshift describe-clusters --cluster-identifier <CLUSTER_ID>

# Ver logs de Redshift
aws logs tail /aws/redshift/cluster/<CLUSTER_ID>/connectionlog --follow

# Verificar VPC Flow Logs
aws logs tail /aws/vpc/flow-logs/<VPC_ID> --follow --filter-pattern "5439"
```

---

## 11. CHECKLIST DE IMPLEMENTACIÓN

### 11.1 Pre-Implementación

```yaml
Pre_Implementation_Checklist:
  Information_Gathering:
    - "[ ] Obtener Cluster ID de Redshift"
    - "[ ] Obtener Endpoint de Redshift"
    - "[ ] Obtener Security Group ID de Redshift"
    - "[ ] Obtener VPC ID donde está Redshift"
    - "[ ] Listar Security Groups de sistemas BI"
    - "[ ] Listar IP ranges de sistemas BI"
    - "[ ] Identificar Security Group de pipeline MySQL"
    - "[ ] Documentar schemas y tablas existentes"
  
  Credentials:
    - "[ ] Crear usuario janis_integration_user en Redshift"
    - "[ ] Crear schema janis_data"
    - "[ ] Otorgar permisos apropiados"
    - "[ ] Crear secret en Secrets Manager"
    - "[ ] Configurar rotación de credenciales"
  
  Network:
    - "[ ] Verificar conectividad VPC (same VPC o peering)"
    - "[ ] Planificar cambios en security groups"
    - "[ ] Coordinar con equipo de redes"
    - "[ ] Obtener aprobaciones necesarias"
```

### 11.2 Implementación

```yaml
Implementation_Checklist:
  Terraform_Configuration:
    - "[ ] Actualizar terraform.tfvars con información de Redshift"
    - "[ ] Configurar variables de security groups existentes"
    - "[ ] Ejecutar terraform plan"
    - "[ ] Revisar cambios propuestos"
    - "[ ] Obtener aprobación para apply"
    - "[ ] Ejecutar terraform apply"
  
  Security_Groups:
    - "[ ] Agregar reglas inbound a SG-Redshift-Existing"
    - "[ ] Verificar reglas no conflictúan con existentes"
    - "[ ] Documentar cambios realizados"
  
  Testing:
    - "[ ] Test de conectividad desde Lambda"
    - "[ ] Test de conectividad desde MWAA"
    - "[ ] Test de queries SELECT"
    - "[ ] Test de queries INSERT"
    - "[ ] Test de COPY desde S3"
    - "[ ] Verificar performance de queries"
```

### 11.3 Post-Implementación

```yaml
Post_Implementation_Checklist:
  Validation:
    - "[ ] Verificar sistemas BI siguen funcionando"
    - "[ ] Verificar pipeline MySQL sigue funcionando"
    - "[ ] Ejecutar queries de reconciliación"
    - "[ ] Monitorear métricas de Redshift"
    - "[ ] Verificar alarmas de CloudWatch"
  
  Documentation:
    - "[ ] Actualizar diagrama de arquitectura"
    - "[ ] Documentar cambios en security groups"
    - "[ ] Actualizar runbooks operacionales"
    - "[ ] Compartir documentación con equipo"
  
  Monitoring:
    - "[ ] Configurar dashboards de CloudWatch"
    - "[ ] Configurar alarmas de performance"
    - "[ ] Configurar alertas de errores"
    - "[ ] Establecer baseline de métricas"
```

---

## 12. CONTACTOS Y ESCALACIÓN

### 12.1 Equipo de Implementación

```yaml
Implementation_Team:
  Infrastructure_Team:
    Lead: "<NOMBRE>"
    Email: "<EMAIL>"
    Slack: "<SLACK_CHANNEL>"
    Responsibilities:
      - "Configuración de VPC y networking"
      - "Security groups y NACLs"
      - "VPC endpoints"
  
  Database_Team:
    Lead: "<NOMBRE>"
    Email: "<EMAIL>"
    Slack: "<SLACK_CHANNEL>"
    Responsibilities:
      - "Gestión de Redshift cluster"
      - "Creación de usuarios y schemas"
      - "Optimización de queries"
  
  BI_Team:
    Lead: "<NOMBRE>"
    Email: "<EMAIL>"
    Slack: "<SLACK_CHANNEL>"
    Responsibilities:
      - "Validación de acceso desde sistemas BI"
      - "Testing de queries de negocio"
      - "Aprobación de migración"
```

### 12.2 Procedimiento de Escalación

```yaml
Escalation_Procedure:
  Level_1_Team_Lead:
    Response_Time: "15 minutos"
    Contact: "<TEAM_LEAD_EMAIL>"
    Scope: "Problemas técnicos estándar"
  
  Level_2_Manager:
    Response_Time: "30 minutos"
    Contact: "<MANAGER_EMAIL>"
    Scope: "Problemas que afectan múltiples sistemas"
  
  Level_3_Director:
    Response_Time: "1 hora"
    Contact: "<DIRECTOR_EMAIL>"
    Scope: "Outages críticos o decisiones de negocio"
```

---

## 13. REFERENCIAS

### 13.1 Documentación AWS

- [Amazon Redshift Documentation](https://docs.aws.amazon.com/redshift/)
- [Redshift Security Best Practices](https://docs.aws.amazon.com/redshift/latest/mgmt/security-best-practices.html)
- [VPC Security Groups](https://docs.aws.amazon.com/vpc/latest/userguide/VPC_SecurityGroups.html)
- [AWS Secrets Manager](https://docs.aws.amazon.com/secretsmanager/)

### 13.2 Documentación Interna

- `Infraestructura AWS - Estado Actual.md`: Estado actual de la infraestructura
- `Especificación Detallada de Infraestructura AWS.md`: Especificaciones técnicas completas
- `.kiro/specs/01-aws-infrastructure/requirements.md`: Requerimientos de infraestructura
- `.kiro/specs/01-aws-infrastructure/design.md`: Diseño de infraestructura

### 13.3 Código Terraform

- `terraform/modules/security-groups/`: Módulo de security groups
- `terraform/modules/vpc/`: Módulo de VPC
- `terraform/modules/monitoring/`: Módulo de monitoreo

---

## APÉNDICE A: EJEMPLO COMPLETO DE CONFIGURACIÓN

### terraform.tfvars

```hcl
# AWS Configuration
aws_region     = "us-east-1"
aws_account_id = "123456789012"
environment    = "production"
project_name   = "janis-cencosud"

# Existing Redshift Configuration
existing_redshift_sg_id       = "sg-0123456789abcdef0"
redshift_cluster_endpoint     = "cencosud-redshift.c1a2b3c4d5e6.us-east-1.redshift.amazonaws.com"
redshift_database_name        = "cencosud_dw"
redshift_port                 = 5439

# Existing BI Systems
existing_bi_security_groups = [
  "sg-0a1b2c3d4e5f6g7h8",  # Power BI Gateway
  "sg-9i8h7g6f5e4d3c2b1"   # Tableau Server
]

# MySQL Migration Pipeline (temporary)
existing_mysql_pipeline_sg_id = "sg-mysql123456789"

# Tags
owner       = "cencosud-data-team"
cost_center = "data-integration-001"
```

---

**Fin del Documento**

Para preguntas o aclaraciones sobre esta documentación, contactar al equipo de Data Engineering.
