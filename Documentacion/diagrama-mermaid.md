# Diagrama de Infraestructura AWS - Janis-Cencosud (Mermaid)

## Arquitectura General de Módulos Terraform

```mermaid
graph TB
    subgraph "TERRAFORM ROOT"
        MAIN[main.tf<br/>Orquestador Principal]
        VARS[variables.tf<br/>Variables Globales]
        OUTPUTS[outputs.tf<br/>Outputs]
        TFVARS[terraform.tfvars<br/>Configuración por Ambiente]
    end

    subgraph "MÓDULOS TERRAFORM"
        VPC[VPC Module<br/>Red, Subnets, NAT, IGW]
        SG[Security Groups Module<br/>7 Security Groups]
        ENDPOINTS[VPC Endpoints Module<br/>Gateway + Interface]
        NACL[NACLs Module<br/>Network ACLs]
        EB[EventBridge Module<br/>Scheduling + Event Bus]
        MON[Monitoring Module<br/>Flow Logs + Alarmas]
        TAG[Tagging Module<br/>Política Corporativa]
    end

    subgraph "AMBIENTES"
        DEV[dev/<br/>Desarrollo]
        QA[qa/<br/>QA/Staging]
        PROD[prod/<br/>Producción]
    end

    MAIN --> VPC
    MAIN --> SG
    MAIN --> ENDPOINTS
    MAIN --> NACL
    MAIN --> EB
    MAIN --> MON
    MAIN --> TAG
    
    VARS --> MAIN
    TFVARS --> MAIN
    MAIN --> OUTPUTS

    TFVARS -.-> DEV
    TFVARS -.-> QA
    TFVARS -.-> PROD

    style MAIN fill:#4A90E2,stroke:#2E5C8A,color:#fff
    style VPC fill:#50C878,stroke:#2E7D4E,color:#fff
    style SG fill:#FF6B6B,stroke:#C92A2A,color:#fff
    style ENDPOINTS fill:#FFD93D,stroke:#C9A000,color:#000
    style EB fill:#A78BFA,stroke:#7C3AED,color:#fff
    style MON fill:#F59E0B,stroke:#D97706,color:#fff
```

## Arquitectura de Red VPC (Single-AZ)

```mermaid
graph TB
    subgraph "AWS REGION: us-east-1"
        subgraph "VPC: 10.0.0.0/16"
            IGW[Internet Gateway]
            
            subgraph "AZ: us-east-1a"
                subgraph "Public Subnet A<br/>10.0.1.0/24"
                    NAT_A[NAT Gateway A<br/>+ Elastic IP]
                    APIGW[API Gateway<br/>Endpoints]
                end
                
                subgraph "Private Subnet 1A<br/>10.0.10.0/24"
                    LAMBDA[Lambda<br/>Functions]
                    MWAA[MWAA<br/>Airflow]
                    REDSHIFT[Redshift<br/>Cluster]
                    VPCE[VPC<br/>Endpoints]
                end
                
                subgraph "Private Subnet 2A<br/>10.0.20.0/24"
                    GLUE[AWS Glue<br/>ENIs]
                end
            end
            
            subgraph "AZ: us-east-1b (Multi-AZ OPCIONAL)"
                subgraph "Public Subnet B<br/>10.0.2.0/24 RESERVADO"
                    NAT_B[NAT Gateway B<br/>+ Elastic IP]
                end
                
                subgraph "Private Subnet 1B<br/>10.0.11.0/24 RESERVADO"
                    LAMBDA_B[Lambda/MWAA<br/>Redshift HA]
                end
                
                subgraph "Private Subnet 2B<br/>10.0.21.0/24 RESERVADO"
                    GLUE_B[AWS Glue<br/>ENIs HA]
                end
            end
        end
        
        INTERNET((Internet))
    end

    INTERNET --> IGW
    IGW --> NAT_A
    IGW --> NAT_B
    NAT_A --> LAMBDA
    NAT_A --> MWAA
    NAT_A --> GLUE
    NAT_B -.-> LAMBDA_B
    NAT_B -.-> GLUE_B
    
    LAMBDA --> VPCE
    MWAA --> VPCE
    GLUE --> VPCE
    REDSHIFT --> VPCE
    
    LAMBDA --> REDSHIFT
    MWAA --> REDSHIFT

    style IGW fill:#4A90E2,stroke:#2E5C8A,color:#fff
    style NAT_A fill:#50C878,stroke:#2E7D4E,color:#fff
    style NAT_B fill:#50C878,stroke:#2E7D4E,color:#fff,stroke-dasharray: 5 5
    style LAMBDA fill:#FF9900,stroke:#CC7A00,color:#fff
    style MWAA fill:#945DD6,stroke:#6B3FA0,color:#fff
    style REDSHIFT fill:#E74C3C,stroke:#C0392B,color:#fff
    style GLUE fill:#FFD93D,stroke:#C9A000,color:#000
    style VPCE fill:#A78BFA,stroke:#7C3AED,color:#fff
```

## Security Groups y Flujo de Tráfico

```mermaid
graph LR
    subgraph "EXTERNAL"
        JANIS[Janis API<br/>Webhooks]
        INTERNET[Internet]
    end

    subgraph "SECURITY GROUPS"
        SG_API[SG-API-Gateway<br/>:443 from Janis IPs]
        SG_LAMBDA[SG-Lambda]
        SG_MWAA[SG-MWAA]
        SG_GLUE[SG-Glue]
        SG_REDSHIFT[SG-Redshift<br/>:5439]
        SG_EB[SG-EventBridge]
        SG_VPCE[SG-VPC-Endpoints<br/>:443]
    end

    subgraph "AWS SERVICES"
        LAMBDA_SVC[Lambda Functions]
        MWAA_SVC[MWAA Airflow]
        GLUE_SVC[AWS Glue Jobs]
        REDSHIFT_SVC[Redshift Cluster]
        EB_SVC[EventBridge]
        VPCE_SVC[VPC Endpoints]
    end

    JANIS -->|HTTPS :443| SG_API
    SG_API --> LAMBDA_SVC
    
    LAMBDA_SVC --> SG_LAMBDA
    SG_LAMBDA -->|:5439| SG_REDSHIFT
    SG_LAMBDA -->|:443| SG_VPCE
    SG_LAMBDA -->|:443| INTERNET
    
    MWAA_SVC --> SG_MWAA
    SG_MWAA -->|:5439| SG_REDSHIFT
    SG_MWAA -->|:443| SG_VPCE
    SG_MWAA -->|:443| INTERNET
    
    GLUE_SVC --> SG_GLUE
    SG_GLUE -->|:443| SG_VPCE
    SG_GLUE -->|All TCP| SG_GLUE
    
    EB_SVC --> SG_EB
    SG_EB -->|:443| SG_MWAA
    SG_EB -->|:443| SG_VPCE
    
    REDSHIFT_SVC --> SG_REDSHIFT
    SG_REDSHIFT -->|:443| SG_VPCE
    
    VPCE_SVC --> SG_VPCE

    style JANIS fill:#FF6B6B,stroke:#C92A2A,color:#fff
    style SG_API fill:#FF6B6B,stroke:#C92A2A,color:#fff
    style SG_LAMBDA fill:#FF9900,stroke:#CC7A00,color:#fff
    style SG_MWAA fill:#945DD6,stroke:#6B3FA0,color:#fff
    style SG_GLUE fill:#FFD93D,stroke:#C9A000,color:#000
    style SG_REDSHIFT fill:#E74C3C,stroke:#C0392B,color:#fff
    style SG_EB fill:#A78BFA,stroke:#7C3AED,color:#fff
    style SG_VPCE fill:#4A90E2,stroke:#2E5C8A,color:#fff
```

## VPC Endpoints

```mermaid
graph TB
    subgraph "VPC ENDPOINTS"
        subgraph "GATEWAY ENDPOINTS (Gratis)"
            S3_GW[S3 Gateway Endpoint<br/>com.amazonaws.us-east-1.s3]
        end
        
        subgraph "INTERFACE ENDPOINTS (~$7.50/mes c/u)"
            GLUE_EP[AWS Glue<br/>com.amazonaws.us-east-1.glue]
            SM_EP[Secrets Manager<br/>com.amazonaws.us-east-1.secretsmanager]
            LOGS_EP[CloudWatch Logs<br/>com.amazonaws.us-east-1.logs]
            KMS_EP[AWS KMS<br/>com.amazonaws.us-east-1.kms]
            STS_EP[AWS STS<br/>com.amazonaws.us-east-1.sts]
            EB_EP[EventBridge<br/>com.amazonaws.us-east-1.events]
        end
    end

    subgraph "SERVICIOS EN VPC"
        LAMBDA_E[Lambda]
        MWAA_E[MWAA]
        GLUE_E[Glue]
        REDSHIFT_E[Redshift]
    end

    subgraph "AWS SERVICES"
        S3_SVC[Amazon S3]
        GLUE_SVC_E[AWS Glue Service]
        SM_SVC[Secrets Manager]
        CW_SVC[CloudWatch]
        KMS_SVC[AWS KMS]
        STS_SVC[AWS STS]
        EB_SVC_E[EventBridge]
    end

    LAMBDA_E --> S3_GW
    MWAA_E --> S3_GW
    GLUE_E --> S3_GW
    S3_GW --> S3_SVC

    LAMBDA_E --> GLUE_EP
    LAMBDA_E --> SM_EP
    LAMBDA_E --> LOGS_EP
    LAMBDA_E --> KMS_EP
    
    MWAA_E --> SM_EP
    MWAA_E --> LOGS_EP
    MWAA_E --> EB_EP
    
    GLUE_E --> GLUE_EP
    GLUE_E --> LOGS_EP
    GLUE_E --> KMS_EP
    
    REDSHIFT_E --> KMS_EP
    REDSHIFT_E --> STS_EP

    GLUE_EP --> GLUE_SVC_E
    SM_EP --> SM_SVC
    LOGS_EP --> CW_SVC
    KMS_EP --> KMS_SVC
    STS_EP --> STS_SVC
    EB_EP --> EB_SVC_E

    style S3_GW fill:#50C878,stroke:#2E7D4E,color:#fff
    style GLUE_EP fill:#FFD93D,stroke:#C9A000,color:#000
    style SM_EP fill:#A78BFA,stroke:#7C3AED,color:#fff
    style LOGS_EP fill:#F59E0B,stroke:#D97706,color:#fff
    style KMS_EP fill:#4A90E2,stroke:#2E5C8A,color:#fff
    style STS_EP fill:#945DD6,stroke:#6B3FA0,color:#fff
    style EB_EP fill:#FF6B6B,stroke:#C92A2A,color:#fff
```

## EventBridge - Orquestación de Polling

```mermaid
graph TB
    subgraph "EVENTBRIDGE MODULE"
        EB_BUS[Event Bus Principal]
        
        subgraph "SCHEDULED RULES"
            RULE_ORDERS[poll-orders-rule<br/>rate: 5 min]
            RULE_PRODUCTS[poll-products-rule<br/>rate: 60 min]
            RULE_STOCK[poll-stock-rule<br/>rate: 10 min]
            RULE_PRICES[poll-prices-rule<br/>rate: 30 min]
            RULE_STORES[poll-stores-rule<br/>rate: 1440 min]
        end
        
        DLQ[SQS Dead Letter Queue<br/>eventbridge-dlq<br/>Retention: 14 días]
    end

    subgraph "MWAA AIRFLOW"
        DAG_ORDERS[dag_poll_orders]
        DAG_PRODUCTS[dag_poll_products]
        DAG_STOCK[dag_poll_stock]
        DAG_PRICES[dag_poll_prices]
        DAG_STORES[dag_poll_stores]
    end

    EB_BUS --> RULE_ORDERS
    EB_BUS --> RULE_PRODUCTS
    EB_BUS --> RULE_STOCK
    EB_BUS --> RULE_PRICES
    EB_BUS --> RULE_STORES

    RULE_ORDERS -->|Trigger| DAG_ORDERS
    RULE_PRODUCTS -->|Trigger| DAG_PRODUCTS
    RULE_STOCK -->|Trigger| DAG_STOCK
    RULE_PRICES -->|Trigger| DAG_PRICES
    RULE_STORES -->|Trigger| DAG_STORES

    RULE_ORDERS -.->|Failed| DLQ
    RULE_PRODUCTS -.->|Failed| DLQ
    RULE_STOCK -.->|Failed| DLQ
    RULE_PRICES -.->|Failed| DLQ
    RULE_STORES -.->|Failed| DLQ

    style EB_BUS fill:#A78BFA,stroke:#7C3AED,color:#fff
    style RULE_ORDERS fill:#FF6B6B,stroke:#C92A2A,color:#fff
    style RULE_PRODUCTS fill:#4A90E2,stroke:#2E5C8A,color:#fff
    style RULE_STOCK fill:#50C878,stroke:#2E7D4E,color:#fff
    style RULE_PRICES fill:#FFD93D,stroke:#C9A000,color:#000
    style RULE_STORES fill:#F59E0B,stroke:#D97706,color:#fff
    style DLQ fill:#E74C3C,stroke:#C0392B,color:#fff
    style DAG_ORDERS fill:#945DD6,stroke:#6B3FA0,color:#fff
    style DAG_PRODUCTS fill:#945DD6,stroke:#6B3FA0,color:#fff
    style DAG_STOCK fill:#945DD6,stroke:#6B3FA0,color:#fff
    style DAG_PRICES fill:#945DD6,stroke:#6B3FA0,color:#fff
    style DAG_STORES fill:#945DD6,stroke:#6B3FA0,color:#fff
```

## Monitoring - CloudWatch

```mermaid
graph TB
    subgraph "MONITORING MODULE"
        subgraph "VPC FLOW LOGS"
            FL_LOG[CloudWatch Log Group<br/>/aws/vpc/flow-logs/]
            FL_ROLE[IAM Role<br/>vpc-flow-logs-role]
            FL_VPC[VPC Flow Log<br/>Traffic: ALL]
        end
        
        subgraph "DNS QUERY LOGGING"
            DNS_LOG[CloudWatch Log Group<br/>/aws/route53/resolver/]
            DNS_ROLE[IAM Role<br/>dns-query-logs-role]
            DNS_CONFIG[Route53 Resolver<br/>Query Log Config]
        end
        
        subgraph "LOG METRIC FILTERS"
            FILTER_REJECT[rejected_connections<br/>action=REJECT]
            FILTER_SCAN[port_scanning<br/>packets=1 + REJECT]
            FILTER_EXFIL[high_outbound_traffic<br/>bytes>10MB]
            FILTER_SSH[ssh_rdp_attempts<br/>port 22/3389]
        end
        
        subgraph "CLOUDWATCH ALARMS"
            ALARM_NAT[NAT Gateway Errors<br/>ErrorPortAllocation > 10]
            ALARM_DROPS[NAT Packet Drops<br/>PacketsDropCount > 1000]
            ALARM_REJECT[Rejected Connections<br/>> 100 in 5min]
            ALARM_SCAN[Port Scanning<br/>> 50 in 5min]
            ALARM_EXFIL[Data Exfiltration<br/>> 100MB in 5min]
            ALARM_SSH[SSH/RDP Activity<br/>> 20 in 5min]
            ALARM_EB[EventBridge Failed<br/>FailedInvocations > 5]
        end
        
        SNS[SNS Topic<br/>Notificaciones]
    end

    FL_VPC --> FL_LOG
    FL_ROLE --> FL_VPC
    
    DNS_CONFIG --> DNS_LOG
    DNS_ROLE --> DNS_CONFIG
    
    FL_LOG --> FILTER_REJECT
    FL_LOG --> FILTER_SCAN
    FL_LOG --> FILTER_EXFIL
    FL_LOG --> FILTER_SSH
    
    FILTER_REJECT --> ALARM_REJECT
    FILTER_SCAN --> ALARM_SCAN
    FILTER_EXFIL --> ALARM_EXFIL
    FILTER_SSH --> ALARM_SSH
    
    ALARM_NAT --> SNS
    ALARM_DROPS --> SNS
    ALARM_REJECT --> SNS
    ALARM_SCAN --> SNS
    ALARM_EXFIL --> SNS
    ALARM_SSH --> SNS
    ALARM_EB --> SNS

    style FL_LOG fill:#F59E0B,stroke:#D97706,color:#fff
    style DNS_LOG fill:#F59E0B,stroke:#D97706,color:#fff
    style FILTER_REJECT fill:#FFD93D,stroke:#C9A000,color:#000
    style FILTER_SCAN fill:#FFD93D,stroke:#C9A000,color:#000
    style FILTER_EXFIL fill:#FFD93D,stroke:#C9A000,color:#000
    style FILTER_SSH fill:#FFD93D,stroke:#C9A000,color:#000
    style ALARM_NAT fill:#E74C3C,stroke:#C0392B,color:#fff
    style ALARM_DROPS fill:#E74C3C,stroke:#C0392B,color:#fff
    style ALARM_REJECT fill:#E74C3C,stroke:#C0392B,color:#fff
    style ALARM_SCAN fill:#E74C3C,stroke:#C0392B,color:#fff
    style ALARM_EXFIL fill:#E74C3C,stroke:#C0392B,color:#fff
    style ALARM_SSH fill:#E74C3C,stroke:#C0392B,color:#fff
    style ALARM_EB fill:#E74C3C,stroke:#C0392B,color:#fff
    style SNS fill:#945DD6,stroke:#6B3FA0,color:#fff
```

## Flujo de Datos Completo

```mermaid
graph LR
    subgraph "EXTERNAL"
        JANIS_API[Janis API<br/>Webhooks + Polling]
    end

    subgraph "INGESTION LAYER"
        APIGW_F[API Gateway<br/>Webhooks]
        LAMBDA_F[Lambda<br/>Webhook Processor]
    end

    subgraph "ORCHESTRATION LAYER"
        EB_F[EventBridge<br/>Scheduled Rules]
        MWAA_F[MWAA Airflow<br/>DAGs]
    end

    subgraph "PROCESSING LAYER"
        GLUE_F[AWS Glue<br/>ETL Jobs]
    end

    subgraph "STORAGE LAYER"
        S3_BRONZE[S3 Bronze<br/>Raw Data]
        S3_SILVER[S3 Silver<br/>Cleaned Data]
        S3_GOLD[S3 Gold<br/>Curated Data]
        REDSHIFT_F[Redshift<br/>Data Warehouse]
    end

    subgraph "MONITORING"
        CW_F[CloudWatch<br/>Logs + Metrics]
        ALARMS_F[CloudWatch<br/>Alarms]
    end

    JANIS_API -->|Webhooks| APIGW_F
    APIGW_F --> LAMBDA_F
    LAMBDA_F --> S3_BRONZE
    
    EB_F -->|Trigger| MWAA_F
    MWAA_F -->|Poll API| JANIS_API
    MWAA_F --> S3_BRONZE
    
    S3_BRONZE --> GLUE_F
    GLUE_F --> S3_SILVER
    S3_SILVER --> GLUE_F
    GLUE_F --> S3_GOLD
    
    S3_GOLD --> REDSHIFT_F
    MWAA_F --> REDSHIFT_F
    
    LAMBDA_F --> CW_F
    MWAA_F --> CW_F
    GLUE_F --> CW_F
    EB_F --> CW_F
    
    CW_F --> ALARMS_F

    style JANIS_API fill:#FF6B6B,stroke:#C92A2A,color:#fff
    style APIGW_F fill:#FF9900,stroke:#CC7A00,color:#fff
    style LAMBDA_F fill:#FF9900,stroke:#CC7A00,color:#fff
    style EB_F fill:#A78BFA,stroke:#7C3AED,color:#fff
    style MWAA_F fill:#945DD6,stroke:#6B3FA0,color:#fff
    style GLUE_F fill:#FFD93D,stroke:#C9A000,color:#000
    style S3_BRONZE fill:#50C878,stroke:#2E7D4E,color:#fff
    style S3_SILVER fill:#4A90E2,stroke:#2E5C8A,color:#fff
    style S3_GOLD fill:#F59E0B,stroke:#D97706,color:#fff
    style REDSHIFT_F fill:#E74C3C,stroke:#C0392B,color:#fff
    style CW_F fill:#F59E0B,stroke:#D97706,color:#fff
    style ALARMS_F fill:#E74C3C,stroke:#C0392B,color:#fff
```

## Recursos AWS Creados por Ambiente

```mermaid
graph TB
    subgraph "RECURSOS POR AMBIENTE"
        subgraph "NETWORKING (VPC Module)"
            R1[1 VPC]
            R2[3-6 Subnets<br/>Single-AZ: 3<br/>Multi-AZ: 6]
            R3[1 Internet Gateway]
            R4[1-2 NAT Gateways<br/>+ Elastic IPs]
            R5[2-3 Route Tables]
        end
        
        subgraph "SECURITY (SG Module)"
            R6[7 Security Groups<br/>API/Lambda/MWAA/Glue<br/>Redshift/EB/VPC-Endpoints]
            R7[2 Network ACLs<br/>Public + Private]
        end
        
        subgraph "ENDPOINTS (VPC Endpoints Module)"
            R8[1 S3 Gateway Endpoint]
            R9[0-6 Interface Endpoints<br/>Glue/Secrets/Logs<br/>KMS/STS/Events]
        end
        
        subgraph "ORCHESTRATION (EventBridge Module)"
            R10[1 Event Bus]
            R11[5 Scheduled Rules<br/>Orders/Products/Stock<br/>Prices/Stores]
            R12[1 SQS DLQ]
        end
        
        subgraph "MONITORING (Monitoring Module)"
            R13[2 CloudWatch Log Groups<br/>VPC Flow + DNS Query]
            R14[4 Log Metric Filters]
            R15[11+ CloudWatch Alarms]
            R16[2 IAM Roles<br/>Flow Logs + DNS Logs]
            R17[1 Route53 Resolver Config]
        end
    end

    style R1 fill:#4A90E2,stroke:#2E5C8A,color:#fff
    style R2 fill:#4A90E2,stroke:#2E5C8A,color:#fff
    style R3 fill:#50C878,stroke:#2E7D4E,color:#fff
    style R4 fill:#50C878,stroke:#2E7D4E,color:#fff
    style R5 fill:#4A90E2,stroke:#2E5C8A,color:#fff
    style R6 fill:#FF6B6B,stroke:#C92A2A,color:#fff
    style R7 fill:#FF6B6B,stroke:#C92A2A,color:#fff
    style R8 fill:#FFD93D,stroke:#C9A000,color:#000
    style R9 fill:#FFD93D,stroke:#C9A000,color:#000
    style R10 fill:#A78BFA,stroke:#7C3AED,color:#fff
    style R11 fill:#A78BFA,stroke:#7C3AED,color:#fff
    style R12 fill:#E74C3C,stroke:#C0392B,color:#fff
    style R13 fill:#F59E0B,stroke:#D97706,color:#fff
    style R14 fill:#F59E0B,stroke:#D97706,color:#fff
    style R15 fill:#E74C3C,stroke:#C0392B,color:#fff
    style R16 fill:#945DD6,stroke:#6B3FA0,color:#fff
    style R17 fill:#4A90E2,stroke:#2E5C8A,color:#fff
```
