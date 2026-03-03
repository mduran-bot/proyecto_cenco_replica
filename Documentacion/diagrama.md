```mermaid
graph TD
    %% EventBridge Scheduling Layer
    EB[Amazon EventBridge<br/>Scheduled Rules]
    EB_ORDERS[Order Rule<br/>Every 5 min]
    EB_PRODUCTS[Product Rule<br/>Every 1 hour]
    EB_STOCK[Stock Rule<br/>Every 10 min]
    EB_PRICES[Price Rule<br/>Every 30 min]
    EB_STORES[Store Rule<br/>Every 24 hours]
    
    %% MWAA Orchestration Layer
    MWAA[Amazon MWAA<br/>Apache Airflow]
    DAG_ORDERS[dag_poll_orders<br/>schedule_interval=None]
    DAG_PRODUCTS[dag_poll_products<br/>schedule_interval=None]
    DAG_STOCK[dag_poll_stock<br/>schedule_interval=None]
    DAG_PRICES[dag_poll_prices<br/>schedule_interval=None]
    DAG_STORES[dag_poll_stores<br/>schedule_interval=None]
    
    %% External APIs
    JANIS[Janis APIs<br/>External System]
    
    %% Data Pipeline
    FIREHOSE[Kinesis Firehose<br/>Data Streaming]
    S3_BRONZE[S3 Bronze Layer<br/>Raw Data]
    GLUE[AWS Glue<br/>ETL Processing]
    S3_SILVER[S3 Silver Layer<br/>Cleaned Data]
    S3_GOLD[S3 Gold Layer<br/>Curated Data]
    REDSHIFT[Amazon Redshift<br/>Data Warehouse]
    
    %% Control and Monitoring
    CONTROL_TABLE[Control Table<br/>Last Execution State]
    CLOUDWATCH[CloudWatch<br/>Monitoring & Alerts]
    
    %% EventBridge to Rules
    EB --> EB_ORDERS
    EB --> EB_PRODUCTS
    EB --> EB_STOCK
    EB --> EB_PRICES
    EB --> EB_STORES
    
    %% EventBridge Rules trigger MWAA DAGs
    EB_ORDERS -->|Trigger with metadata| DAG_ORDERS
    EB_PRODUCTS -->|Trigger with metadata| DAG_PRODUCTS
    EB_STOCK -->|Trigger with metadata| DAG_STOCK
    EB_PRICES -->|Trigger with metadata| DAG_PRICES
    EB_STORES -->|Trigger with metadata| DAG_STORES
    
    %% DAGs are part of MWAA
    DAG_ORDERS -.-> MWAA
    DAG_PRODUCTS -.-> MWAA
    DAG_STOCK -.-> MWAA
    DAG_PRICES -.-> MWAA
    DAG_STORES -.-> MWAA
    
    %% DAGs interact with Control Table and APIs
    MWAA --> CONTROL_TABLE
    MWAA -->|Incremental Queries| JANIS
    
    %% Data Flow Pipeline
    JANIS -->|API Response| MWAA
    MWAA -->|Processed Data| FIREHOSE
    FIREHOSE --> S3_BRONZE
    S3_BRONZE --> GLUE
    GLUE --> S3_SILVER
    GLUE --> S3_GOLD
    S3_GOLD --> REDSHIFT
    
    %% Monitoring
    EB --> CLOUDWATCH
    MWAA --> CLOUDWATCH
    GLUE --> CLOUDWATCH
    FIREHOSE --> CLOUDWATCH
    
    %% Styling
    classDef eventbridge fill:#ff9999,stroke:#333,stroke-width:2px,color:#000
    classDef mwaa fill:#99ccff,stroke:#333,stroke-width:2px,color:#000
    classDef storage fill:#99ff99,stroke:#333,stroke-width:2px,color:#000
    classDef processing fill:#ffcc99,stroke:#333,stroke-width:2px,color:#000
    classDef external fill:#ffff99,stroke:#333,stroke-width:2px,color:#000
    
    class EB,EB_ORDERS,EB_PRODUCTS,EB_STOCK,EB_PRICES,EB_STORES eventbridge
    class MWAA,DAG_ORDERS,DAG_PRODUCTS,DAG_STOCK,DAG_PRICES,DAG_STORES mwaa
    class S3_BRONZE,S3_SILVER,S3_GOLD,REDSHIFT,CONTROL_TABLE storage
    class GLUE,FIREHOSE processing
    class JANIS,CLOUDWATCH external
