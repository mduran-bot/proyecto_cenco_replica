# Diagrama de Infraestructura AWS - Janis-Cencosud Integration

## Opciones de Deployment

Este proyecto soporta **dos opciones de deployment**:

### Opción 1: VPC Nueva (Por Defecto)
- Terraform crea toda la infraestructura de red desde cero
- Incluye: VPC, subnets, NAT Gateway, Internet Gateway, Route Tables
- Ideal para: Desarrollo, QA, ambientes nuevos
- **Estado**: Implementado y probado ✅

### Opción 2: Landing Zone Existente del Cliente
- Terraform usa infraestructura VPC corporativa existente
- Requiere: VPC, subnets, NAT Gateway ya desplegados por el cliente
- Ideal para: Producción con Landing Zone corporativa establecida
- **Guía completa**: [GUIA_LANDING_ZONE_CLIENTE.md](GUIA_LANDING_ZONE_CLIENTE.md) ⭐ NUEVO

---

## Arquitectura General

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                           TERRAFORM INFRASTRUCTURE                                   │
│                        Janis-Cencosud AWS Integration                               │
└─────────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────────┐
│                              ESTRUCTURA DE MÓDULOS                                   │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  terraform/                                                                          │
│  ├── main.tf                    ← Orquestador principal                            │
│  ├── variables.tf               ← Variables globales                               │
│  ├── outputs.tf                 ← Outputs de infraestructura                       │
│  ├── terraform.tfvars           ← Configuración por ambiente                       │
│  │                                                                                  │
│  ├── modules/                                                                       │
│  │   ├── vpc/                   ← Red VPC, Subnets, NAT, IGW                      │
│  │   ├── security-groups/       ← 7 Security Groups                               │
│  │   ├── vpc-endpoints/         ← Gateway + Interface Endpoints                   │
│  │   ├── s3/                    ← Data Lake Buckets (Bronze/Silver/Gold)          │
│  │   ├── nacls/                 ← Network ACLs (comentado)                        │
│  │   ├── eventbridge/           ← Scheduling y Event Bus                          │
│  │   ├── monitoring/            ← Flow Logs, DNS Logs, Alarmas                   │
│  │   ├── waf/                   ← (Gestionado por cliente)                        │
│  │   └── tagging/               ← Política corporativa de tags                    │
│  │                                                                                  │
│  └── environments/                                                                  │
│      ├── dev/                   ← Ambiente desarrollo                              │
│      ├── qa/                    ← Ambiente QA/staging                              │
│      └── prod/                  ← Ambiente producción                              │
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘


## Arquitectura de Red AWS (VPC Module)

**⚠️ NOTA**: Este diagrama muestra la opción de **VPC Nueva** (por defecto). Si el cliente usa su **Landing Zone existente**, el módulo VPC se deshabilita y se usan los recursos de red existentes. Ver [GUIA_LANDING_ZONE_CLIENTE.md](GUIA_LANDING_ZONE_CLIENTE.md) para detalles.

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                                AWS REGION: us-east-1                                 │
│                                                                                      │
│  ┌────────────────────────────────────────────────────────────────────────────────┐ │
│  │                         VPC: 10.0.0.0/16 (65,536 IPs)                          │ │
│  │                                                                                 │ │
│  │  ┌──────────────────────────────────────────────────────────────────────────┐ │ │
│  │  │                    AVAILABILITY ZONE: us-east-1a                         │ │ │
│  │  │                                                                           │ │ │
│  │  │  ┌─────────────────────────────────────────────────────────────────┐    │ │ │
│  │  │  │  PUBLIC SUBNET A: 10.0.1.0/24 (256 IPs)                         │    │ │ │
│  │  │  │  ┌──────────────────┐  ┌──────────────────┐                     │    │ │ │
│  │  │  │  │  Internet        │  │  NAT Gateway A   │                     │    │ │ │
│  │  │  │  │  Gateway (IGW)   │  │  + Elastic IP    │                     │    │ │ │
│  │  │  │  └──────────────────┘  └──────────────────┘                     │    │ │ │
│  │  │  │  Purpose: NAT Gateway, API Gateway endpoints                    │    │ │ │
│  │  │  └─────────────────────────────────────────────────────────────────┘    │ │ │
│  │  │                                                                           │ │ │
│  │  │  ┌─────────────────────────────────────────────────────────────────┐    │ │ │
│  │  │  │  PRIVATE SUBNET 1A: 10.0.10.0/24 (256 IPs)                      │    │ │ │
│  │  │  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐        │    │ │ │
│  │  │  │  │  Lambda   │  │  MWAA    │  │ Redshift │  │   VPC    │        │    │ │ │
│  │  │  │  │ Functions │  │ (Airflow)│  │ Cluster  │  │Endpoints │        │    │ │ │
│  │  │  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘        │    │ │ │
│  │  │  │  Purpose: Servicios principales de procesamiento               │    │ │ │
│  │  │  └─────────────────────────────────────────────────────────────────┘    │ │ │
│  │  │                                                                           │ │ │
│  │  │  ┌─────────────────────────────────────────────────────────────────┐    │ │ │
│  │  │  │  PRIVATE SUBNET 2A: 10.0.20.0/24 (256 IPs)                      │    │ │ │
│  │  │  │  ┌──────────────────────────────────────────────────────┐       │    │ │ │
│  │  │  │  │  AWS Glue ENIs (Elastic Network Interfaces)          │       │    │ │ │
│  │  │  │  │  - Spark Cluster Communication                       │       │    │ │ │
│  │  │  │  │  - ETL Job Execution                                 │       │    │ │ │
│  │  │  │  └──────────────────────────────────────────────────────┘       │    │ │ │
│  │  │  │  Purpose: AWS Glue jobs y transformaciones ETL                  │    │ │ │
│  │  │  └─────────────────────────────────────────────────────────────────┘    │ │ │
│  │  │                                                                           │ │ │
│  │  └───────────────────────────────────────────────────────────────────────────┘ │ │
│  │                                                                                 │ │
│  │  ┌──────────────────────────────────────────────────────────────────────────┐ │ │
│  │  │              AVAILABILITY ZONE: us-east-1b (MULTI-AZ OPCIONAL)           │ │ │
│  │  │              ⚠️  Solo se crea si enable_multi_az = true                  │ │ │
│  │  │                                                                           │ │ │
│  │  │  ┌─────────────────────────────────────────────────────────────────┐    │ │ │
│  │  │  │  PUBLIC SUBNET B: 10.0.2.0/24 (RESERVADO)                       │    │ │ │
│  │  │  │  ┌──────────────────┐                                            │    │ │ │
│  │  │  │  │  NAT Gateway B   │                                            │    │ │ │
│  │  │  │  │  + Elastic IP    │                                            │    │ │ │
│  │  │  │  └──────────────────┘                                            │    │ │ │
│  │  │  └─────────────────────────────────────────────────────────────────┘    │ │ │
│  │  │                                                                           │ │ │
│  │  │  ┌─────────────────────────────────────────────────────────────────┐    │ │ │
│  │  │  │  PRIVATE SUBNET 1B: 10.0.11.0/24 (RESERVADO)                    │    │ │ │
│  │  │  │  Purpose: Lambda, MWAA, Redshift (HA)                           │    │ │ │
│  │  │  └─────────────────────────────────────────────────────────────────┘    │ │ │
│  │  │                                                                           │ │ │
│  │  │  ┌─────────────────────────────────────────────────────────────────┐    │ │ │
│  │  │  │  PRIVATE SUBNET 2B: 10.0.21.0/24 (RESERVADO)                    │    │ │ │
│  │  │  │  Purpose: AWS Glue ENIs (HA)                                    │    │ │ │
│  │  │  └─────────────────────────────────────────────────────────────────┘    │ │ │
│  │  │                                                                           │ │ │
│  │  └───────────────────────────────────────────────────────────────────────────┘ │ │
│  │                                                                                 │ │
│  └─────────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘

ROUTE TABLES:
├── Public Route Table
│   └── 0.0.0.0/0 → Internet Gateway
│
├── Private Route Table A
│   └── 0.0.0.0/0 → NAT Gateway A
│
└── Private Route Table B (Multi-AZ)
    └── 0.0.0.0/0 → NAT Gateway B
```


## Security Groups (7 grupos configurados)

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                            SECURITY GROUPS MODULE                                    │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  1. SG-API-Gateway                                                                   │
│     ├── Inbound:  HTTPS (443) desde IPs de Janis                                   │
│     └── Outbound: All traffic                                                       │
│                                                                                      │
│  2. SG-Lambda                                                                        │
│     ├── Inbound:  (ninguno)                                                         │
│     └── Outbound:                                                                    │
│         ├── PostgreSQL (5439) → SG-Redshift                                        │
│         ├── HTTPS (443) → SG-VPC-Endpoints                                         │
│         └── HTTPS (443) → Internet (Janis API)                                     │
│                                                                                      │
│  3. SG-MWAA (Managed Airflow)                                                       │
│     ├── Inbound:  HTTPS (443) desde sí mismo (workers)                            │
│     └── Outbound:                                                                    │
│         ├── HTTPS (443) → SG-VPC-Endpoints                                         │
│         ├── HTTPS (443) → Internet                                                 │
│         └── PostgreSQL (5439) → SG-Redshift                                        │
│                                                                                      │
│  4. SG-Glue                                                                          │
│     ├── Inbound:  All TCP (0-65535) desde sí mismo (Spark cluster)                │
│     └── Outbound:                                                                    │
│         ├── HTTPS (443) → SG-VPC-Endpoints                                         │
│         └── All TCP (0-65535) → sí mismo (Spark cluster)                          │
│                                                                                      │
│  5. SG-Redshift                                                                      │
│     ├── Inbound:                                                                     │
│     │   ├── PostgreSQL (5439) desde SG-Lambda                                      │
│     │   ├── PostgreSQL (5439) desde SG-MWAA                                        │
│     │   ├── PostgreSQL (5439) desde SGs de BI existentes                          │
│     │   ├── PostgreSQL (5439) desde IPs de BI                                     │
│     │   └── PostgreSQL (5439) desde SG-MySQL-Pipeline (temporal)                  │
│     └── Outbound:                                                                    │
│         └── HTTPS (443) → SG-VPC-Endpoints                                         │
│                                                                                      │
│  6. SG-EventBridge                                                                   │
│     ├── Inbound:  (ninguno)                                                         │
│     └── Outbound:                                                                    │
│         ├── HTTPS (443) → SG-MWAA                                                  │
│         └── HTTPS (443) → SG-VPC-Endpoints                                         │
│                                                                                      │
│  7. SG-VPC-Endpoints                                                                 │
│     ├── Inbound:  HTTPS (443) desde toda la VPC (10.0.0.0/16)                     │
│     └── Outbound: HTTPS (443) → AWS Services                                       │
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```


## VPC Endpoints (Optimización de Costos y Seguridad)

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                           VPC ENDPOINTS MODULE                                       │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  GATEWAY ENDPOINTS (Sin costo adicional)                                            │
│  ├── S3 Gateway Endpoint                                                            │
│  │   ├── Type: Gateway                                                              │
│  │   ├── Service: com.amazonaws.us-east-1.s3                                       │
│  │   ├── Associated: Todas las Route Tables                                        │
│  │   └── Purpose: Acceso privado a S3 sin NAT Gateway                              │
│  │                                                                                  │
│  INTERFACE ENDPOINTS (~$7.50/mes cada uno + $0.01/GB)                              │
│  ├── AWS Glue                                                                       │
│  │   ├── Type: Interface                                                            │
│  │   ├── Service: com.amazonaws.us-east-1.glue                                    │
│  │   ├── Subnet: Private Subnet 1A                                                 │
│  │   ├── Security Group: SG-VPC-Endpoints                                          │
│  │   └── Private DNS: Enabled                                                      │
│  │                                                                                  │
│  ├── AWS Secrets Manager                                                            │
│  │   ├── Type: Interface                                                            │
│  │   ├── Service: com.amazonaws.us-east-1.secretsmanager                          │
│  │   ├── Subnet: Private Subnet 1A                                                 │
│  │   ├── Security Group: SG-VPC-Endpoints                                          │
│  │   └── Private DNS: Enabled                                                      │
│  │                                                                                  │
│  ├── CloudWatch Logs                                                                │
│  │   ├── Type: Interface                                                            │
│  │   ├── Service: com.amazonaws.us-east-1.logs                                    │
│  │   ├── Subnet: Private Subnet 1A                                                 │
│  │   ├── Security Group: SG-VPC-Endpoints                                          │
│  │   └── Private DNS: Enabled                                                      │
│  │                                                                                  │
│  ├── AWS KMS                                                                         │
│  │   ├── Type: Interface                                                            │
│  │   ├── Service: com.amazonaws.us-east-1.kms                                     │
│  │   ├── Subnet: Private Subnet 1A                                                 │
│  │   ├── Security Group: SG-VPC-Endpoints                                          │
│  │   └── Private DNS: Enabled                                                      │
│  │                                                                                  │
│  ├── AWS STS                                                                         │
│  │   ├── Type: Interface                                                            │
│  │   ├── Service: com.amazonaws.us-east-1.sts                                     │
│  │   ├── Subnet: Private Subnet 1A                                                 │
│  │   ├── Security Group: SG-VPC-Endpoints                                          │
│  │   └── Private DNS: Enabled                                                      │
│  │                                                                                  │
│  └── Amazon EventBridge                                                             │
│      ├── Type: Interface                                                            │
│      ├── Service: com.amazonaws.us-east-1.events                                  │
│      ├── Subnet: Private Subnet 1A                                                 │
│      ├── Security Group: SG-VPC-Endpoints                                          │
│      └── Private DNS: Enabled                                                      │
│                                                                                      │
│  ⚙️  CONFIGURACIÓN:                                                                 │
│  Todos los endpoints son opcionales y se controlan con variables:                  │
│  - enable_s3_endpoint              = true  (RECOMENDADO - gratis)                 │
│  - enable_glue_endpoint            = true/false                                    │
│  - enable_secrets_manager_endpoint = true/false                                    │
│  - enable_logs_endpoint            = true/false                                    │
│  - enable_kms_endpoint             = true/false                                    │
│  - enable_sts_endpoint             = true/false                                    │
│  - enable_events_endpoint          = true/false                                    │
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```


## EventBridge Module (Orquestación de Polling)

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                          EVENTBRIDGE MODULE                                          │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  ┌────────────────────────────────────────────────────────────────────────────┐    │
│  │                        Event Bus Principal                                  │    │
│  │                                                                             │    │
│  │  ┌──────────────────────────────────────────────────────────────────────┐ │    │
│  │  │  SCHEDULED RULES (Polling Periódico)                                 │ │    │
│  │  │                                                                       │ │    │
│  │  │  1. poll-orders-rule                                                 │ │    │
│  │  │     ├── Schedule: rate(5 minutes)  [configurable]                   │ │    │
│  │  │     ├── Target: MWAA Environment                                     │ │    │
│  │  │     ├── DAG: dag_poll_orders                                         │ │    │
│  │  │     └── DLQ: eventbridge-dlq                                         │ │    │
│  │  │                                                                       │ │    │
│  │  │  2. poll-products-rule                                               │ │    │
│  │  │     ├── Schedule: rate(60 minutes) [configurable]                   │ │    │
│  │  │     ├── Target: MWAA Environment                                     │ │    │
│  │  │     ├── DAG: dag_poll_products                                       │ │    │
│  │  │     └── DLQ: eventbridge-dlq                                         │ │    │
│  │  │                                                                       │ │    │
│  │  │  3. poll-stock-rule                                                  │ │    │
│  │  │     ├── Schedule: rate(10 minutes) [configurable]                   │ │    │
│  │  │     ├── Target: MWAA Environment                                     │ │    │
│  │  │     ├── DAG: dag_poll_stock                                          │ │    │
│  │  │     └── DLQ: eventbridge-dlq                                         │ │    │
│  │  │                                                                       │ │    │
│  │  │  4. poll-prices-rule                                                 │ │    │
│  │  │     ├── Schedule: rate(30 minutes) [configurable]                   │ │    │
│  │  │     ├── Target: MWAA Environment                                     │ │    │
│  │  │     ├── DAG: dag_poll_prices                                         │ │    │
│  │  │     └── DLQ: eventbridge-dlq                                         │ │    │
│  │  │                                                                       │ │    │
│  │  │  5. poll-stores-rule                                                 │ │    │
│  │  │     ├── Schedule: rate(1440 minutes) [1 día - configurable]         │ │    │
│  │  │     ├── Target: MWAA Environment                                     │ │    │
│  │  │     ├── DAG: dag_poll_stores                                         │ │    │
│  │  │     └── DLQ: eventbridge-dlq                                         │ │    │
│  │  │                                                                       │ │    │
│  │  └──────────────────────────────────────────────────────────────────────┘ │    │
│  │                                                                             │    │
│  │  ┌──────────────────────────────────────────────────────────────────────┐ │    │
│  │  │  DEAD LETTER QUEUE (DLQ)                                             │ │    │
│  │  │                                                                       │ │    │
│  │  │  SQS Queue: eventbridge-dlq                                          │ │    │
│  │  │  ├── Purpose: Capturar eventos fallidos                             │ │    │
│  │  │  ├── Retention: 14 días                                              │ │    │
│  │  │  ├── Visibility Timeout: 300 segundos                                │ │    │
│  │  │  └── Alarm: Alerta si hay mensajes en DLQ                           │ │    │
│  │  │                                                                       │ │    │
│  │  └──────────────────────────────────────────────────────────────────────┘ │    │
│  │                                                                             │    │
│  └─────────────────────────────────────────────────────────────────────────────┘    │
│                                                                                      │
│  CONFIGURACIÓN DE FRECUENCIAS (variables):                                          │
│  ├── order_polling_rate_minutes   = 5     (recomendado: 5-15 min)                 │
│  ├── product_polling_rate_minutes = 60    (recomendado: 30-60 min)                │
│  ├── stock_polling_rate_minutes   = 10    (recomendado: 15-30 min)                │
│  ├── price_polling_rate_minutes   = 30    (recomendado: 60 min)                   │
│  └── store_polling_rate_minutes   = 1440  (recomendado: 1 día)                    │
│                                                                                      │
│  INTEGRACIÓN CON MWAA:                                                              │
│  └── mwaa_environment_arn: ARN del ambiente MWAA (Managed Airflow)                 │
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```


## Monitoring Module (Observabilidad y Seguridad)

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                           MONITORING MODULE                                          │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  ┌────────────────────────────────────────────────────────────────────────────┐    │
│  │  VPC FLOW LOGS                                                             │    │
│  │  ├── CloudWatch Log Group: /aws/vpc/flow-logs/{name_prefix}               │    │
│  │  ├── Retention: 90 días (configurable)                                    │    │
│  │  ├── Traffic Type: ALL (accepted + rejected)                              │    │
│  │  ├── Format: Custom (incluye IPs, puertos, protocolo, acción)            │    │
│  │  └── IAM Role: vpc-flow-logs-role                                         │    │
│  └────────────────────────────────────────────────────────────────────────────┘    │
│                                                                                      │
│  ┌────────────────────────────────────────────────────────────────────────────┐    │
│  │  DNS QUERY LOGGING                                                         │    │
│  │  ├── CloudWatch Log Group: /aws/route53/resolver/{name_prefix}            │    │
│  │  ├── Retention: 90 días (configurable)                                    │    │
│  │  ├── Purpose: Monitoreo de seguridad y troubleshooting                    │    │
│  │  ├── Route53 Resolver Query Log Config                                    │    │
│  │  └── IAM Role: dns-query-logs-role                                        │    │
│  └────────────────────────────────────────────────────────────────────────────┘    │
│                                                                                      │
│  ┌────────────────────────────────────────────────────────────────────────────┐    │
│  │  CLOUDWATCH ALARMS (10 alarmas configuradas)                              │    │
│  │                                                                             │    │
│  │  INFRAESTRUCTURA:                                                          │    │
│  │  ├── 1. NAT Gateway Errors                                                │    │
│  │  │   └── Métrica: ErrorPortAllocation > 10 en 5 min                      │    │
│  │  ├── 2. NAT Gateway Packet Drops                                          │    │
│  │  │   └── Métrica: PacketsDropCount > 1000 en 5 min                       │    │
│  │                                                                             │    │
│  │  SEGURIDAD (basadas en VPC Flow Logs):                                    │    │
│  │  ├── 3. Rejected Connections Spike                                        │    │
│  │  │   └── Métrica: RejectedConnections > 100 en 5 min                     │    │
│  │  ├── 4. Port Scanning Detected                                            │    │
│  │  │   └── Métrica: PortScanningAttempts > 50 en 5 min                     │    │
│  │  ├── 5. Data Exfiltration Risk                                            │    │
│  │  │   └── Métrica: HighOutboundTraffic > 100 MB en 5 min                  │    │
│  │  ├── 6. Unusual SSH/RDP Activity                                          │    │
│  │  │   └── Métrica: SSHRDPAttempts > 20 en 5 min                           │    │
│  │                                                                             │    │
│  │  EVENTBRIDGE (una alarma por cada rule):                                  │    │
│  │  ├── 7. EventBridge Failed - poll-orders                                  │    │
│  │  ├── 8. EventBridge Failed - poll-products                                │    │
│  │  ├── 9. EventBridge Failed - poll-stock                                   │    │
│  │  ├── 10. EventBridge Failed - poll-prices                                 │    │
│  │  └── 11. EventBridge Failed - poll-stores                                 │    │
│  │      └── Métrica: FailedInvocations > 5 en 5 min                         │    │
│  │                                                                             │    │
│  │  NOTIFICACIONES:                                                           │    │
│  │  └── SNS Topic: alarm_sns_topic_arn (configurable)                        │    │
│  │                                                                             │    │
│  └────────────────────────────────────────────────────────────────────────────┘    │
│                                                                                      │
│  ┌────────────────────────────────────────────────────────────────────────────┐    │
│  │  LOG METRIC FILTERS (4 filtros para detección de amenazas)                │    │
│  │                                                                             │    │
│  │  1. rejected_connections                                                   │    │
│  │     └── Pattern: action=REJECT                                             │    │
│  │                                                                             │    │
│  │  2. port_scanning                                                          │    │
│  │     └── Pattern: packets=1 + action=REJECT (múltiples puertos)           │    │
│  │                                                                             │    │
│  │  3. high_outbound_traffic                                                  │    │
│  │     └── Pattern: bytes>10000000 + action=ACCEPT                           │    │
│  │                                                                             │    │
│  │  4. ssh_rdp_attempts                                                       │    │
│  │     └── Pattern: dstport=22||3389 + protocol=6                            │    │
│  │                                                                             │    │
│  └────────────────────────────────────────────────────────────────────────────┘    │
│                                                                                      │
│  CONFIGURACIÓN:                                                                     │
│  ├── enable_vpc_flow_logs         = true/false                                     │
│  ├── enable_dns_query_logging     = true/false                                     │
│  ├── vpc_flow_logs_retention_days = 90 (7, 30, 90, 365)                           │
│  ├── dns_logs_retention_days      = 90 (7, 30, 90, 365)                           │
│  └── alarm_sns_topic_arn          = "arn:aws:sns:..." (opcional)                  │
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```


## S3 Module (Data Lake Buckets)

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                              S3 MODULE - DATA LAKE                                   │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  ARQUITECTURA DE DATA LAKE (Bronze/Silver/Gold)                                     │
│                                                                                      │
│  ┌────────────────────────────────────────────────────────────────────────────┐    │
│  │  1. BRONZE LAYER BUCKET - Raw Data                                         │    │
│  │     ├── Nombre: {name_prefix}-datalake-bronze                              │    │
│  │     ├── Propósito: Datos crudos de Janis API y webhooks                   │    │
│  │     ├── Formato: JSON, CSV, Parquet (según fuente)                         │    │
│  │     ├── Características:                                                    │    │
│  │     │   ├── ✅ Versionado habilitado                                       │    │
│  │     │   ├── ✅ Cifrado AES256                                              │    │
│  │     │   ├── ✅ Bloqueo de acceso público                                   │    │
│  │     │   ├── ✅ Access logging → logs bucket                                │    │
│  │     │   └── ✅ Lifecycle policy:                                           │    │
│  │     │       ├── Glacier: 90 días (configurable)                            │    │
│  │     │       └── Expiración: 365 días (configurable)                        │    │
│  │     └── Estructura:                                                         │    │
│  │         └── orders/year=2024/month=01/day=15/*.json                        │    │
│  └────────────────────────────────────────────────────────────────────────────┘    │
│                                                                                      │
│  ┌────────────────────────────────────────────────────────────────────────────┐    │
│  │  2. SILVER LAYER BUCKET - Cleaned Data                                     │    │
│  │     ├── Nombre: {name_prefix}-datalake-silver                              │    │
│  │     ├── Propósito: Datos limpiados, validados y normalizados              │    │
│  │     ├── Formato: Apache Iceberg con Parquet                                │    │
│  │     ├── Características:                                                    │    │
│  │     │   ├── ✅ Versionado habilitado                                       │    │
│  │     │   ├── ✅ Cifrado AES256                                              │    │
│  │     │   ├── ✅ Bloqueo de acceso público                                   │    │
│  │     │   ├── ✅ Access logging → logs bucket                                │    │
│  │     │   └── ✅ Lifecycle policy:                                           │    │
│  │     │       ├── Glacier: 180 días (configurable)                           │    │
│  │     │       └── Expiración: 730 días (2 años, configurable)               │    │
│  │     └── Estructura:                                                         │    │
│  │         └── orders/iceberg/metadata/ + data/                               │    │
│  └────────────────────────────────────────────────────────────────────────────┘    │
│                                                                                      │
│  ┌────────────────────────────────────────────────────────────────────────────┐    │
│  │  3. GOLD LAYER BUCKET - Business-Ready Data                                │    │
│  │     ├── Nombre: {name_prefix}-datalake-gold                                │    │
│  │     ├── Propósito: Datos agregados y optimizados para BI                  │    │
│  │     ├── Formato: Apache Iceberg con Parquet                                │    │
│  │     ├── Características:                                                    │    │
│  │     │   ├── ✅ Versionado habilitado                                       │    │
│  │     │   ├── ✅ Cifrado AES256                                              │    │
│  │     │   ├── ✅ Bloqueo de acceso público                                   │    │
│  │     │   ├── ✅ Access logging → logs bucket                                │    │
│  │     │   └── ✅ Lifecycle policy:                                           │    │
│  │     │       └── Intelligent Tiering: 30 días (configurable)               │    │
│  │     └── Estructura:                                                         │    │
│  │         └── orders_aggregated/, inventory_summary/, sales_metrics/         │    │
│  └────────────────────────────────────────────────────────────────────────────┘    │
│                                                                                      │
│  ┌────────────────────────────────────────────────────────────────────────────┐    │
│  │  4. SCRIPTS BUCKET - Code Repository                                       │    │
│  │     ├── Nombre: {name_prefix}-scripts                                      │    │
│  │     ├── Propósito: Lambda code, Glue jobs, MWAA DAGs                       │    │
│  │     ├── Características:                                                    │    │
│  │     │   ├── ✅ Versionado habilitado (control de versiones de código)     │    │
│  │     │   ├── ✅ Cifrado AES256                                              │    │
│  │     │   ├── ✅ Bloqueo de acceso público                                   │    │
│  │     │   └── ✅ Access logging → logs bucket                                │    │
│  │     └── Estructura:                                                         │    │
│  │         ├── lambda/webhook-processor/, data-enrichment/                    │    │
│  │         ├── glue/bronze-to-silver/, silver-to-gold/                        │    │
│  │         └── mwaa/dags/                                                      │    │
│  └────────────────────────────────────────────────────────────────────────────┘    │
│                                                                                      │
│  ┌────────────────────────────────────────────────────────────────────────────┐    │
│  │  5. LOGS BUCKET - Centralized Logging                                      │    │
│  │     ├── Nombre: {name_prefix}-logs                                         │    │
│  │     ├── Propósito: S3 access logs y application logs                       │    │
│  │     ├── Características:                                                    │    │
│  │     │   ├── ✅ Versionado habilitado                                       │    │
│  │     │   ├── ✅ Cifrado AES256                                              │    │
│  │     │   ├── ✅ Bloqueo de acceso público                                   │    │
│  │     │   └── ✅ Lifecycle policy:                                           │    │
│  │     │       ├── Standard-IA: 30 días                                       │    │
│  │     │       ├── Glacier: 90 días                                           │    │
│  │     │       └── Expiración: 365 días (configurable)                        │    │
│  │     └── Estructura:                                                         │    │
│  │         └── s3-access-logs/bronze/, silver/, gold/, scripts/               │    │
│  └────────────────────────────────────────────────────────────────────────────┘    │
│                                                                                      │
│  CONFIGURACIÓN DE LIFECYCLE (variables):                                            │
│  ├── bronze_glacier_transition_days = 90   (default)                               │
│  ├── bronze_expiration_days         = 365  (default)                               │
│  ├── silver_glacier_transition_days = 180  (default)                               │
│  ├── silver_expiration_days         = 730  (default)                               │
│  ├── gold_intelligent_tiering_days  = 30   (default)                               │
│  └── logs_expiration_days           = 365  (default)                               │
│                                                                                      │
│  ESTIMACIÓN DE COSTOS (1TB de datos):                                              │
│  ├── Bronze: $23/mes (Standard) → $4/mes (Glacier después de 90 días)             │
│  ├── Silver: $23/mes (Standard) → $4/mes (Glacier después de 180 días)            │
│  ├── Gold: $23/mes (Standard) → $15/mes (Intelligent Tiering)                     │
│  ├── Scripts: $1/mes (pocos GB)                                                    │
│  ├── Logs: $5/mes (con lifecycle)                                                  │
│  └── Total estimado: ~$52/mes para 1TB                                             │
│                                                                                      │
│  INTEGRACIÓN CON SERVICIOS:                                                         │
│  ├── Lambda: Escritura de datos crudos en Bronze                                   │
│  ├── AWS Glue: Transformaciones Bronze→Silver→Gold                                 │
│  ├── Redshift: COPY desde Gold layer                                               │
│  ├── MWAA: Lectura de DAGs desde Scripts bucket                                    │
│  └── CloudWatch: Logs de aplicaciones en Logs bucket                               │
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```


## Tagging Strategy (Política Corporativa)

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                        CORPORATE TAGGING POLICY                                      │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  TAGS OBLIGATORIOS (Corporate Policy):                                              │
│  ├── Application:  "janis-cencosud-integration"                                    │
│  ├── Environment:  "prod" | "qa" | "dev" | "uat" | "sandbox"                      │
│  ├── Owner:        "data-engineering-team"                                          │
│  ├── CostCenter:   "CC-XXXX" (REQUERIDO - contactar finanzas)                     │
│  ├── BusinessUnit: "Data-Analytics"                                                 │
│  ├── Country:      "CL" (Chile)                                                     │
│  ├── Criticality:  "high" | "medium" | "low"                                       │
│  └── ManagedBy:    "terraform"                                                      │
│                                                                                      │
│  TAGS ADICIONALES (Opcionales):                                                     │
│  └── additional_tags = {                                                            │
│      Purpose      = "..."                                                           │
│      AutoShutdown = "true/false"                                                    │
│      ...                                                                             │
│  }                                                                                   │
│                                                                                      │
│  APLICACIÓN:                                                                         │
│  ├── Todos los recursos AWS reciben estos tags automáticamente                     │
│  ├── Configurado en main.tf usando locals.common_tags                              │
│  ├── Merge con additional_tags para tags opcionales                                │
│  └── Validación automática en variables.tf                                         │
│                                                                                      │
│  RECURSOS ETIQUETADOS:                                                              │
│  ├── VPC y Subnets                                                                  │
│  ├── Security Groups                                                                │
│  ├── VPC Endpoints                                                                  │
│  ├── NAT Gateways y Elastic IPs                                                    │
│  ├── Route Tables                                                                   │
│  ├── S3 Buckets (Bronze, Silver, Gold, Scripts, Logs)                              │
│  ├── EventBridge Rules y Event Bus                                                 │
│  ├── CloudWatch Log Groups                                                          │
│  ├── CloudWatch Alarms                                                              │
│  ├── IAM Roles                                                                      │
│  └── SQS Queues                                                                     │
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```
