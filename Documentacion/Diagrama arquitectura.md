```mermaid
graph TB
    subgraph "EXTERNAL"
        JANIS[Janis WMS<br/>Sistema Externo]
        INTERNET[Internet]
    end

    subgraph "AWS CLOUD - VPC 10.0.0.0/16"
        subgraph "PUBLIC SUBNET A - 10.0.1.0/24"
            IGW[Internet Gateway]
            NAT[NAT Gateway<br/>+ Elastic IP]
            APIGW[API Gateway<br/>Webhook Endpoints]
        end

        subgraph "PRIVATE SUBNET 1A - 10.0.10.0/24"
            LAMBDA[Lambda Functions<br/>Webhook Processor<br/>Data Enrichment]
            MWAA[MWAA<br/>Apache Airflow<br/>DAG Orchestration]
            REDSHIFT[Amazon Redshift<br/>Data Warehouse<br/>BI Analytics]
        end

        subgraph "PRIVATE SUBNET 2A - 10.0.20.0/24"
            GLUE[AWS Glue<br/>ETL Jobs<br/>Spark Cluster]
        end

        subgraph "VPC ENDPOINTS"
            S3_EP[S3 Gateway<br/>Endpoint]
            GLUE_EP[Glue Interface<br/>Endpoint]
            SM_EP[Secrets Manager<br/>Endpoint]
            LOGS_EP[CloudWatch Logs<br/>Endpoint]
            KMS_EP[KMS<br/>Endpoint]
            STS_EP[STS<br/>Endpoint]
            EB_EP[EventBridge<br/>Endpoint]
        end
    end

    subgraph "AWS MANAGED SERVICES"
        S3[Amazon S3<br/>Data Lake<br/>Bronze/Silver/Gold]
        EB[EventBridge<br/>Scheduled Rules<br/>5 Polling Jobs]
        CW[CloudWatch<br/>Logs + Metrics<br/>Alarms]
        SM[Secrets Manager<br/>Credentials]
        KMS[AWS KMS<br/>Encryption Keys]
    end

    subgraph "MONITORING"
        FLOW[VPC Flow Logs]
        DNS[DNS Query Logs]
        ALARMS[CloudWatch Alarms<br/>11+ Alerts]
        SNS[SNS Topic<br/>Notifications]
    end

    %% External Connections
    JANIS -->|Webhooks HTTPS| APIGW
    INTERNET --> IGW
    IGW --> NAT
    IGW --> APIGW

    %% API Gateway to Lambda
    APIGW -->|Trigger| LAMBDA

    %% Lambda Connections
    LAMBDA -->|Write Data| REDSHIFT
    LAMBDA -->|Poll Janis API| NAT
    LAMBDA -->|Write Raw Data| S3_EP
    LAMBDA -->|Get Credentials| SM_EP
    LAMBDA -->|Send Logs| LOGS_EP
    LAMBDA -->|Decrypt/Encrypt| KMS_EP

    %% EventBridge Orchestration
    EB -->|Trigger DAGs| EB_EP
    EB_EP -->|Schedule| MWAA
    EB -->|5 Scheduled Rules| MWAA

    %% MWAA Connections
    MWAA -->|Poll Janis API| NAT
    MWAA -->|Write to S3| S3_EP
    MWAA -->|Load Data| REDSHIFT
    MWAA -->|Get Credentials| SM_EP
    MWAA -->|Send Logs| LOGS_EP
    MWAA -->|Trigger Jobs| GLUE_EP

    %% Glue ETL Processing
    GLUE -->|Read/Write S3| S3_EP
    GLUE -->|Get Metadata| GLUE_EP
    GLUE -->|Send Logs| LOGS_EP
    GLUE -->|Encrypt Data| KMS_EP

    %% S3 Data Lake Layers
    S3_EP --> S3
    S3 -->|Bronze → Silver| GLUE
    S3 -->|Silver → Gold| GLUE
    S3 -->|Gold → Redshift| REDSHIFT

    %% VPC Endpoints to Services
    SM_EP --> SM
    LOGS_EP --> CW
    KMS_EP --> KMS
    GLUE_EP --> GLUE

    %% Monitoring Flow
    LAMBDA --> CW
    MWAA --> CW
    GLUE --> CW
    EB --> CW
    REDSHIFT --> CW
    
    CW --> FLOW
    CW --> DNS
    CW --> ALARMS
    ALARMS --> SNS

    %% Redshift Access
    REDSHIFT -->|BI Tools Access| INTERNET

    %% Styling
    style JANIS fill:#FF6B6B,stroke:#C92A2A,color:#fff
    style APIGW fill:#FF9900,stroke:#CC7A00,color:#fff
    style LAMBDA fill:#FF9900,stroke:#CC7A00,color:#fff
    style MWAA fill:#945DD6,stroke:#6B3FA0,color:#fff
    style GLUE fill:#FFD93D,stroke:#C9A000,color:#000
    style REDSHIFT fill:#E74C3C,stroke:#C0392B,color:#fff
    style S3 fill:#50C878,stroke:#2E7D4E,color:#fff
    style EB fill:#A78BFA,stroke:#7C3AED,color:#fff
    style CW fill:#F59E0B,stroke:#D97706,color:#fff
    style NAT fill:#4A90E2,stroke:#2E5C8A,color:#fff
    style IGW fill:#4A90E2,stroke:#2E5C8A,color:#fff
    style S3_EP fill:#50C878,stroke:#2E7D4E,color:#fff
    style ALARMS fill:#E74C3C,stroke:#C0392B,color:#fff
    style SNS fill:#945DD6,stroke:#6B3FA0,color:#fff
