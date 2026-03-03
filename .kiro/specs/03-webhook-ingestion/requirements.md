# Requirements Document: Webhook Ingestion

## Introduction

Este documento define los requerimientos para el sistema de ingesta de webhooks que permite recibir notificaciones en tiempo real desde Janis cuando ocurren eventos críticos de negocio. El sistema debe procesar estas notificaciones de manera segura, eficiente y confiable, almacenando los datos en la capa Bronze del Data Lake.

## Glossary

- **Webhook**: Notificación HTTP POST enviada por Janis cuando ocurre un evento
- **API_Gateway**: Servicio AWS que expone endpoints REST para recibir webhooks
- **HMAC_SHA256**: Algoritmo de firma digital para validar autenticidad de webhooks
- **Lambda_Function**: Función serverless que procesa webhooks y enriquece datos
- **Kinesis_Firehose**: Servicio de streaming que bufferiza y entrega datos a S3
- **Bronze_Layer**: Capa de almacenamiento de datos raw en S3
- **Event_Type**: Tipo de evento de negocio (order.created, order.updated, etc.)
- **Payload**: Contenido JSON del webhook
- **Rate_Limiting**: Control de velocidad de requests para prevenir sobrecarga

## Requirements

### Requirement 1: API Gateway Webhook Endpoints

**User Story:** Como sistema Janis, quiero enviar notificaciones de eventos a endpoints específicos, para que el sistema de Cencosud pueda reaccionar inmediatamente a cambios importantes de negocio.

#### Acceptance Criteria

1. THE API_Gateway SHALL expose REST endpoints for different event types:
   - /webhook/order/created for new order notifications
   - /webhook/order/updated for order modification notifications
   - /webhook/shipping/updated for shipping information updates
   - /webhook/payment/updated for payment status changes
   - /webhook/picking/completed for picking process completion
2. THE API_Gateway SHALL accept only HTTP POST requests with JSON payloads
3. THE API_Gateway SHALL respond with HTTP 200 OK within 5 seconds for valid requests
4. THE API_Gateway SHALL respond with appropriate HTTP error codes for invalid requests:
   - 400 Bad Request for malformed JSON
   - 401 Unauthorized for invalid signatures
   - 429 Too Many Requests for rate limit violations
5. THE API_Gateway SHALL log all requests and responses to CloudWatch Logs

### Requirement 2: Authentication and Security

**User Story:** Como especialista en seguridad, quiero validar que todos los webhooks provienen realmente de Janis, para que el sistema esté protegido contra ataques de falsificación y manipulación de datos.

#### Acceptance Criteria

1. THE System SHALL validate HMAC-SHA256 signatures on all incoming webhooks
2. THE System SHALL use a shared secret key stored securely in AWS Secrets Manager
3. THE System SHALL reject webhooks with invalid or missing signatures with HTTP 401
4. THE System SHALL implement signature validation within 100ms to minimize latency
5. THE System SHALL rotate the shared secret key monthly with zero downtime
6. THE System SHALL log all authentication failures for security monitoring
7. THE System SHALL accept webhooks only from whitelisted IP addresses of Janis

### Requirement 3: Rate Limiting and Throttling

**User Story:** Como ingeniero de sistemas, quiero proteger la infraestructura contra picos de tráfico excesivos, para que el sistema mantenga estabilidad y disponibilidad bajo cualquier condición de carga.

#### Acceptance Criteria

1. THE API_Gateway SHALL implement rate limiting of 1,000 requests per second per endpoint
2. THE API_Gateway SHALL allow burst capacity of 2,000 requests for short periods
3. THE API_Gateway SHALL use token bucket algorithm for smooth rate limiting
4. THE API_Gateway SHALL return HTTP 429 when rate limits are exceeded
5. THE API_Gateway SHALL implement per-IP rate limiting of 100 requests per minute
6. THE API_Gateway SHALL provide rate limit headers in responses:
   - X-RateLimit-Limit: maximum requests allowed
   - X-RateLimit-Remaining: requests remaining in current window
   - X-RateLimit-Reset: timestamp when limit resets

### Requirement 4: Webhook Processing and Enrichment

**User Story:** Como ingeniero de datos, quiero enriquecer las notificaciones webhook con datos completos de Janis, para que el pipeline downstream tenga toda la información necesaria para el procesamiento.

#### Acceptance Criteria

1. THE Lambda_Function SHALL be triggered automatically by API Gateway for each valid webhook
2. THE Lambda_Function SHALL parse the webhook payload to extract event type and entity ID
3. THE Lambda_Function SHALL call the appropriate Janis API to fetch complete entity data:
   - GET /order/{order_id} for order events
   - GET /order/{order_id}/items for order item details
   - GET /product/{product_id} for product events
   - GET /shipping/{shipping_id} for shipping events
4. THE Lambda_Function SHALL handle API call failures with exponential backoff retry (max 3 attempts)
5. THE Lambda_Function SHALL enrich webhook data with:
   - Complete entity information from Janis API
   - Processing timestamp
   - Event source identifier
   - Schema version
6. THE Lambda_Function SHALL complete processing within 30 seconds timeout

### Requirement 5: Data Buffering and Streaming

**User Story:** Como arquitecto de datos, quiero bufferizar los eventos procesados antes de almacenarlos, para que se optimicen los costos de almacenamiento y se mejore la eficiencia del pipeline.

#### Acceptance Criteria

1. THE Kinesis_Firehose SHALL receive enriched webhook data from Lambda functions
2. THE Kinesis_Firehose SHALL buffer data based on size (5 MB) or time (60 seconds) thresholds
3. THE Kinesis_Firehose SHALL compress data using GZIP before writing to S3
4. THE Kinesis_Firehose SHALL partition data by event type and date:
   - orders/year=YYYY/month=MM/day=DD/hour=HH/
   - order-items/year=YYYY/month=MM/day=DD/hour=HH/
   - products/year=YYYY/month=MM/day=DD/hour=HH/
5. THE Kinesis_Firehose SHALL handle delivery failures with automatic retries
6. THE Kinesis_Firehose SHALL route failed deliveries to error bucket for manual review

### Requirement 6: Bronze Layer Storage

**User Story:** Como ingeniero de almacenamiento, quiero persistir todos los datos de webhook en la capa Bronze, para que estén disponibles para procesamiento posterior y auditoría.

#### Acceptance Criteria

1. THE System SHALL store webhook data in S3 Bronze bucket in JSON format
2. THE System SHALL maintain original webhook structure without transformations
3. THE System SHALL add metadata to each record:
   - ingestion_timestamp: when data was received
   - source_type: "webhook"
   - event_type: type of business event
   - schema_version: version of data structure
4. THE System SHALL organize files with hierarchical partitioning for efficient querying
5. THE System SHALL apply lifecycle policies:
   - Transition to S3 Infrequent Access after 30 days
   - Transition to S3 Glacier after 90 days
   - Delete after 365 days

### Requirement 7: Error Handling and Dead Letter Queues

**User Story:** Como ingeniero de operaciones, quiero que el sistema maneje errores de manera robusta, para que ningún evento se pierda y todos los fallos sean visibles para resolución.

#### Acceptance Criteria

1. THE System SHALL implement Dead Letter Queues (DLQ) for failed webhook processing
2. THE System SHALL route messages to DLQ after 3 failed processing attempts
3. THE System SHALL preserve original webhook data in DLQ for manual reprocessing
4. THE System SHALL include error details in DLQ messages:
   - Error type and description
   - Failure timestamp
   - Processing attempt count
   - Original webhook payload
5. THE System SHALL alert operations team when DLQ receives messages
6. THE System SHALL provide mechanism to replay messages from DLQ after issue resolution

### Requirement 8: Monitoring and Observability

**User Story:** Como ingeniero de monitoreo, quiero visibilidad completa del flujo de webhooks, para que pueda detectar problemas rápidamente y optimizar el rendimiento del sistema.

#### Acceptance Criteria

1. THE System SHALL generate CloudWatch metrics for:
   - Webhooks received per second by endpoint
   - Processing latency (p50, p95, p99)
   - Success/failure rates
   - API Gateway throttling events
   - Lambda function duration and errors
   - Kinesis Firehose delivery success rate
2. THE System SHALL create CloudWatch alarms for:
   - Error rate > 5% in any 5-minute period
   - Processing latency > 10 seconds
   - DLQ message count > 0
   - API Gateway 5xx errors
   - Lambda function failures
3. THE System SHALL provide real-time dashboard showing:
   - Current webhook throughput
   - Processing pipeline health
   - Error trends and patterns
4. THE System SHALL send SNS notifications for critical alerts

### Requirement 9: Data Quality and Validation

**User Story:** Como especialista en calidad de datos, quiero validar que todos los webhooks contienen datos válidos y completos, para que el pipeline downstream no falle por datos corruptos.

#### Acceptance Criteria

1. THE System SHALL validate webhook payload structure against expected JSON schema
2. THE System SHALL verify that required fields are present and not null:
   - event_type
   - entity_id (order_id, product_id, etc.)
   - timestamp
3. THE System SHALL validate data types and formats:
   - Timestamps in ISO 8601 format
   - IDs as non-empty strings
   - Numeric fields within reasonable ranges
4. THE System SHALL reject invalid webhooks with detailed error messages
5. THE System SHALL track data quality metrics:
   - Percentage of valid webhooks
   - Common validation failures
   - Data completeness scores

### Requirement 10: Performance and Scalability

**User Story:** Como arquitecto de sistemas, quiero que el sistema de webhooks escale automáticamente, para que pueda manejar picos de tráfico sin degradación del servicio.

#### Acceptance Criteria

1. THE API_Gateway SHALL handle up to 10,000 concurrent requests without degradation
2. THE Lambda_Function SHALL scale automatically to handle webhook volume
3. THE Lambda_Function SHALL use provisioned concurrency during peak hours
4. THE Kinesis_Firehose SHALL auto-scale delivery capacity based on throughput
5. THE System SHALL maintain sub-second response times under normal load
6. THE System SHALL complete 99.9% of webhook processing within 5 seconds
7. THE System SHALL handle traffic spikes up to 10x normal volume

### Requirement 11: Disaster Recovery and High Availability

**User Story:** Como ingeniero de confiabilidad, quiero que el sistema de webhooks sea altamente disponible, para que los eventos críticos de negocio nunca se pierdan debido a fallos de infraestructura.

#### Acceptance Criteria

1. THE System SHALL deploy across multiple Availability Zones
2. THE System SHALL maintain 99.9% uptime availability
3. THE System SHALL implement automatic failover for all components
4. THE System SHALL replicate data across multiple AZs for durability
5. THE System SHALL provide backup webhook endpoints in case of primary failure
6. THE System SHALL maintain processing capability during single AZ outage
7. THE System SHALL recover automatically from transient failures without data loss