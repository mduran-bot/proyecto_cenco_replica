# Requirements Document: API Polling

## Introduction

Este documento define los requerimientos para el sistema de polling periódico que consulta las APIs de Janis de manera programada para obtener actualizaciones de datos transaccionales. Este sistema actúa como red de seguridad complementaria a los webhooks, garantizando que no se pierda información crítica.

## Glossary

- **EventBridge**: Amazon EventBridge - Servicio de eventos que gatilla los procesos de polling
- **MWAA**: Amazon Managed Workflows for Apache Airflow - Servicio de orquestación
- **DAG**: Directed Acyclic Graph - Flujo de trabajo definido en Airflow
- **Polling**: Consulta periódica y programada a APIs externas
- **Incremental_Query**: Consulta que obtiene solo datos nuevos o modificados
- **Pagination**: Técnica para manejar respuestas grandes divididas en páginas
- **Rate_Limiting**: Control de velocidad de requests para respetar límites de API
- **Backoff**: Estrategia de espera incremental ante fallos
- **Control_Table**: Tabla que mantiene estado de última ejecución exitosa
- **API_Endpoint**: URL específica de la API de Janis para obtener datos
- **Event_Rule**: Regla de EventBridge que define cuándo gatillar un DAG

## Requirements

### Requirement 1: EventBridge Scheduling Setup

**User Story:** Como ingeniero de orquestación, quiero configurar Amazon EventBridge para gatillar los procesos de polling de manera programada, para que se reduzca el overhead de MWAA y se optimice el uso de recursos.

#### Acceptance Criteria

1. THE EventBridge SHALL create scheduled rules for each polling type:
   - Rule for order polling: every 5 minutes
   - Rule for product polling: every 1 hour
   - Rule for stock polling: every 10 minutes
   - Rule for price polling: every 30 minutes
   - Rule for store polling: every 24 hours
2. THE EventBridge SHALL target MWAA DAG execution for each rule
3. THE EventBridge SHALL pass event metadata to MWAA including:
   - polling_type: type of data to poll
   - execution_time: scheduled execution timestamp
   - rule_name: EventBridge rule identifier
4. THE EventBridge SHALL handle rule failures with retry policy
5. THE EventBridge SHALL integrate with CloudWatch for monitoring rule executions
6. THE EventBridge SHALL support rule enable/disable for maintenance windows

### Requirement 2: MWAA Environment Setup

**User Story:** Como ingeniero de orquestación, quiero configurar un entorno Apache Airflow gestionado optimizado para ejecución bajo demanda, para que pueda procesar los trabajos de polling gatillados por EventBridge de manera eficiente.

#### Acceptance Criteria

1. THE MWAA_Environment SHALL be configured with environment class mw1.small (1 vCPU, 2 GB RAM)
2. THE MWAA_Environment SHALL support auto-scaling from 1 to 3 workers based on workload
3. THE MWAA_Environment SHALL run Apache Airflow version 2.7.2 with Python 3.11
4. THE MWAA_Environment SHALL be deployed in private subnets with VPC connectivity
5. THE MWAA_Environment SHALL have access to S3 bucket for DAG storage and logs
6. THE MWAA_Environment SHALL integrate with AWS Secrets Manager for API credentials
7. THE MWAA_Environment SHALL enable web server access through secure authentication
8. THE MWAA_Environment SHALL accept EventBridge triggers for DAG execution
9. THE MWAA_Environment SHALL process EventBridge event metadata in DAG context

### Requirement 3: DAG Configuration for Event-Driven Polling

**User Story:** Como ingeniero de datos, quiero definir flujos de trabajo que respondan a eventos de EventBridge para cada tipo de dato, para que el sistema consulte las APIs de Janis de manera eficiente y sin overhead de scheduling continuo.

#### Acceptance Criteria

1. THE System SHALL create DAG for order polling (dag_poll_orders) triggered by EventBridge
2. THE System SHALL create DAG for product polling (dag_poll_products) triggered by EventBridge
3. THE System SHALL create DAG for stock polling (dag_poll_stock) triggered by EventBridge
4. THE System SHALL create DAG for price polling (dag_poll_prices) triggered by EventBridge
5. THE System SHALL create DAG for store polling (dag_poll_stores) triggered by EventBridge
6. THE System SHALL configure each DAG with:
   - No internal schedule (schedule_interval=None)
   - Retry policy: 3 attempts with exponential backoff
   - Timeout: 30 minutes per task
   - Email alerts on failure
   - Dependency management between tasks
7. THE System SHALL extract polling_type from EventBridge event payload
8. THE System SHALL validate EventBridge event structure before processing

### Requirement 4: Incremental Data Extraction

**User Story:** Como optimizador de rendimiento, quiero consultar solo datos nuevos o modificados en cada ejecución gatillada por EventBridge, para que se minimice la carga en las APIs de Janis y se reduzca el tiempo de procesamiento.

#### Acceptance Criteria

1. THE System SHALL maintain Control_Table with last successful execution timestamp per data type
2. THE System SHALL query Janis APIs using dateModified filter: dateModified >= lastTimestamp
3. THE System SHALL implement 1-minute overlap to prevent data loss during execution boundaries
4. THE System SHALL handle timezone conversions correctly (UTC for all timestamps)
5. THE System SHALL update Control_Table only after successful completion of entire DAG
6. THE System SHALL support full refresh mode for initial loads or error recovery
7. THE System SHALL use EventBridge execution_time as reference for incremental queries
8. THE System SHALL handle concurrent executions by checking Control_Table locks

### Requirement 5: API Request Management

**User Story:** Como integrador de APIs, quiero manejar las consultas a Janis de manera eficiente y respetuosa, para que no se excedan los límites de rate limiting y se mantenga una buena relación con el proveedor.

#### Acceptance Criteria

1. THE System SHALL implement rate limiting of maximum 100 requests per minute to Janis APIs
2. THE System SHALL use exponential backoff strategy for failed requests:
   - First retry: 1 second delay
   - Second retry: 2 seconds delay
   - Third retry: 4 seconds delay
3. THE System SHALL handle HTTP response codes appropriately:
   - 200: Process data normally
   - 429: Wait and retry with longer delay
   - 401/403: Alert and stop execution
   - 500/502/503: Retry with backoff
   - 404: Log warning and continue
4. THE System SHALL implement request timeout of 30 seconds per API call
5. THE System SHALL log all API requests and responses for debugging

### Requirement 6: Pagination Handling

**User Story:** Como procesador de datos, quiero manejar respuestas grandes de APIs de manera eficiente, para que pueda obtener todos los datos disponibles sin sobrecargar la memoria o exceder timeouts.

#### Acceptance Criteria

1. THE System SHALL implement pagination using limit/offset parameters
2. THE System SHALL use page size of 100 records per request for optimal performance
3. THE System SHALL continue fetching pages until empty response or end marker
4. THE System SHALL handle pagination metadata correctly:
   - total_count: total records available
   - has_more: boolean indicating more pages exist
   - next_offset: offset for next page
5. THE System SHALL implement circuit breaker to prevent infinite loops
6. THE System SHALL process each page immediately to minimize memory usage

### Requirement 7: Data Enrichment and Related Entities

**User Story:** Como analista de datos, quiero obtener información completa de entidades relacionadas, para que los datos estén completos y listos para análisis sin requerir consultas adicionales.

#### Acceptance Criteria

1. THE System SHALL fetch order items for each order retrieved: GET /order/{order_id}/items
2. THE System SHALL fetch product details for each product retrieved: GET /product/{product_id}
3. THE System SHALL fetch SKU information for each product: GET /product/{product_id}/skus
4. THE System SHALL implement parallel processing for related entity fetching
5. THE System SHALL handle missing related entities gracefully (log warning, continue processing)
6. THE System SHALL respect API rate limits when fetching related entities

### Requirement 8: Data Validation and Quality Checks

**User Story:** Como especialista en calidad de datos, quiero validar que todos los datos obtenidos por polling sean válidos y completos, para que se detecten problemas temprano en el pipeline.

#### Acceptance Criteria

1. THE System SHALL validate JSON response structure against expected schemas
2. THE System SHALL verify required fields are present and not null
3. THE System SHALL validate data types and formats:
   - Dates in expected format
   - IDs as non-empty strings
   - Numeric values within reasonable ranges
4. THE System SHALL detect and flag duplicate records within same polling execution
5. THE System SHALL compare record counts with previous executions to detect anomalies
6. THE System SHALL generate data quality metrics:
   - Records retrieved per API endpoint
   - Validation failure rates
   - Data completeness scores

### Requirement 9: Data Delivery to Kinesis Firehose

**User Story:** Como arquitecto de pipeline, quiero entregar los datos obtenidos por polling al mismo sistema de buffering que los webhooks, para que se mantenga consistencia en el procesamiento downstream.

#### Acceptance Criteria

1. THE System SHALL send all polled data to appropriate Kinesis Firehose streams
2. THE System SHALL add metadata to each record:
   - source_type: "polling"
   - polling_timestamp: when data was retrieved
   - dag_run_id: Airflow execution identifier
   - api_endpoint: source API endpoint
   - eventbridge_rule: EventBridge rule that triggered the execution
   - execution_time: EventBridge scheduled execution time
3. THE System SHALL batch records for efficient Firehose delivery (up to 500 records per batch)
4. THE System SHALL handle Firehose delivery failures with retry logic
5. THE System SHALL route failed deliveries to Dead Letter Queue
6. THE System SHALL maintain delivery order when possible

### Requirement 10: Error Handling and Recovery

**User Story:** Como ingeniero de operaciones, quiero que el sistema de polling sea resiliente ante fallos, para que pueda recuperarse automáticamente y no pierda datos críticos.

#### Acceptance Criteria

1. THE System SHALL implement comprehensive error handling for:
   - Network connectivity issues
   - API authentication failures
   - Rate limiting violations
   - Data validation errors
   - Downstream delivery failures
2. THE System SHALL maintain detailed error logs with:
   - Error type and description
   - Failed request details
   - Timestamp and context
   - Recovery actions taken
3. THE System SHALL implement automatic retry with exponential backoff
4. THE System SHALL alert operations team for critical failures
5. THE System SHALL provide manual recovery mechanisms:
   - Ability to rerun failed DAG executions
   - Option to reset Control_Table timestamps
   - Manual data replay capabilities
   - EventBridge rule disable/enable for maintenance
   - Manual DAG triggering bypassing EventBridge

### Requirement 11: Monitoring and Observability

**User Story:** Como ingeniero de monitoreo, quiero visibilidad completa de todos los procesos de polling, para que pueda detectar problemas proactivamente y optimizar el rendimiento.

#### Acceptance Criteria

1. THE System SHALL generate CloudWatch metrics for:
   - DAG execution duration and success rate
   - API response times and error rates
   - Records retrieved per polling cycle
   - Data quality scores
   - Firehose delivery success rate
   - EventBridge rule execution success rate
   - EventBridge to MWAA trigger latency
2. THE System SHALL create CloudWatch alarms for:
   - DAG execution failures
   - API error rate > 10%
   - Unusual data volume changes (>50% deviation)
   - Processing time > expected duration
   - EventBridge rule failures
   - EventBridge to MWAA trigger delays > 5 minutes
3. THE System SHALL provide Airflow UI dashboards showing:
   - DAG execution history and status
   - Task-level performance metrics
   - Error trends and patterns
4. THE System SHALL send notifications for:
   - DAG failures requiring intervention
   - Data quality issues
   - API connectivity problems
   - EventBridge rule failures
   - EventBridge scheduling anomalies

### Requirement 12: Configuration Management

**User Story:** Como administrador de sistemas, quiero gestionar todas las configuraciones de polling de manera centralizada, para que pueda ajustar parámetros sin modificar código y mantener consistencia entre entornos.

#### Acceptance Criteria

1. THE System SHALL store all configuration in AWS Systems Manager Parameter Store:
   - API endpoints and credentials
   - EventBridge rule schedules and intervals
   - Rate limiting parameters
   - Retry policies and timeouts
2. THE System SHALL support environment-specific configurations (dev, staging, prod)
3. THE System SHALL reload configuration changes without requiring DAG redeployment or EventBridge rule recreation
4. THE System SHALL validate configuration parameters at startup
5. THE System SHALL maintain configuration version history for rollback capability
6. THE System SHALL encrypt sensitive configuration values (API keys, passwords)

### Requirement 13: Performance Optimization

**User Story:** Como optimizador de rendimiento, quiero que el sistema de polling opere de manera eficiente, para que minimice el uso de recursos y complete las tareas dentro de las ventanas de tiempo asignadas.

#### Acceptance Criteria

1. THE System SHALL complete order polling within 4 minutes (allowing 1 minute buffer)
2. THE System SHALL process up to 10,000 records per polling cycle efficiently
3. THE System SHALL use connection pooling for API requests to reduce overhead
4. THE System SHALL implement parallel processing where possible without violating rate limits
5. THE System SHALL optimize memory usage by processing data in streaming fashion
6. THE System SHALL cache frequently accessed configuration and metadata
7. THE System SHALL monitor and report resource utilization metrics
8. THE System SHALL minimize MWAA overhead by using EventBridge scheduling
9. THE System SHALL optimize EventBridge rule execution to reduce trigger latency