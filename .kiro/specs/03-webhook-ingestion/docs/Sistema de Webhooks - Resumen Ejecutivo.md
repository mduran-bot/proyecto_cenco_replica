# Sistema de Webhooks - Resumen Ejecutivo

## Fecha de Actualización
15 de Enero, 2026

## Propósito

El Sistema de Webhooks implementa una arquitectura serverless de ingesta en tiempo real que recibe notificaciones HTTP POST desde Janis, valida su autenticidad mediante HMAC-SHA256, enriquece los datos llamando a las APIs de Janis, y transmite la información al Data Lake para procesamiento downstream. Este sistema proporciona latencia mínima (segundos) para eventos críticos de negocio.

## Arquitectura de Alto Nivel

### Componentes Principales

1. **Amazon API Gateway**: Punto de entrada HTTPS para webhooks con rate limiting y validación
2. **AWS Lambda (Validator)**: Validación de firmas HMAC-SHA256 para autenticación
3. **AWS Lambda (Enrichment)**: Enriquecimiento de datos mediante llamadas a APIs de Janis
4. **AWS Secrets Manager**: Gestión segura de shared secrets y API keys
5. **Amazon Kinesis Firehose**: Buffering, compresión y entrega a S3
6. **Amazon S3 Bronze Layer**: Almacenamiento particionado de datos crudos enriquecidos
7. **Amazon SQS Dead Letter Queue**: Captura de mensajes fallidos para replay manual

### Flujo de Datos

```
Janis System → API Gateway → Lambda Validator → Lambda Enrichment → Kinesis Firehose → S3 Bronze Layer
                    ↓              ↓                    ↓                    ↓
              Rate Limiting   Signature Check    Janis API Call      Compression & Partition
                    ↓              ↓                    ↓
              CloudWatch      Secrets Manager         DLQ (on failure)
```

## Endpoints de Webhooks

| Endpoint | Evento | Enriquecimiento |
|----------|--------|-----------------|
| POST /webhook/order/created | Nueva orden creada | Order details + Order items |
| POST /webhook/order/updated | Orden modificada | Order details + Order items |
| POST /webhook/shipping/updated | Actualización de envío | Shipping details |
| POST /webhook/payment/updated | Cambio de estado de pago | Payment details |
| POST /webhook/picking/completed | Picking completado | Picking details |

## Ventajas de la Arquitectura Serverless

### Escalabilidad Automática
- **API Gateway**: Escala automáticamente a cualquier volumen de requests
- **Lambda**: Auto-scaling hasta 1,000 ejecuciones concurrentes (ampliable a 10,000+)
- **Kinesis Firehose**: Maneja hasta 5,000 records/segundo sin gestión de shards

### Optimización de Costos
- Pago por uso real (sin servidores idle)
- Provisioned concurrency solo en horas pico (9 AM - 6 PM)
- Compresión GZIP reduce costos de S3 en ~70%
- Costo estimado: ~$425/mes para 10M webhooks

### Alta Disponibilidad
- Deployment automático en múltiples AZs
- Failover automático sin intervención manual
- SLA objetivo: 99.95% uptime

## Características Clave

### 1. Autenticación Robusta
- Validación HMAC-SHA256 de todas las requests
- Shared secret rotado mensualmente con zero-downtime
- Soporte para múltiples versiones de secret durante rotación
- Comparación constant-time para prevenir timing attacks

### 2. Rate Limiting y Throttling
- 1,000 requests/segundo por endpoint
- 2,000 burst capacity para picos de tráfico
- Token bucket algorithm para control granular
- IP whitelisting mediante Resource Policy

### 3. Enriquecimiento de Datos
- Fetch automático de datos completos desde APIs de Janis
- Retry con exponential backoff (2s, 4s, 8s)
- Timeout de 10 segundos por llamada API
- Merge de webhook payload con respuesta API

### 4. Validación de Calidad
- JSON schema validation en API Gateway
- Validación de campos requeridos (event_type, entity_id, timestamp)
- Rechazo de payloads > 256 KB
- Respuestas HTTP descriptivas (400, 401, 429, 503)

### 5. Entrega Confiable
- Buffering inteligente (5 MB o 60 segundos)
- Compresión GZIP automática
- Particionamiento dinámico por event_type y fecha
- Retry automático por 1 hora en caso de fallos

### 6. Manejo de Errores
- Dead Letter Queue para mensajes fallidos
- Retry automático con Lambda (3 intentos totales)
- Alarmas CloudWatch en DLQ message count > 0
- Función de replay manual desde DLQ

### 7. Observabilidad Completa
- Distributed tracing con AWS X-Ray
- Structured logging en CloudWatch
- Métricas custom para KPIs de negocio
- Dashboards en tiempo real

## Seguridad

### Network Security
- API Gateway con TLS 1.2+ obligatorio
- Lambda en subnets privadas con NAT Gateway
- VPC endpoints para servicios AWS (Secrets Manager, S3, Kinesis)
- Security groups restrictivos (solo HTTPS outbound a Janis)

### Data Security
- Cifrado en tránsito (TLS) para todas las comunicaciones
- Cifrado en reposo (SSE-S3 AES-256) para datos en S3
- Secrets Manager con cifrado automático
- CloudWatch Logs con cifrado opcional (KMS)

### Access Control
- IAM roles con principio de menor privilegio
- No wildcard permissions en producción
- Separación de roles por función (validator, enrichment, delivery)
- Auditoría completa con CloudTrail

### Compliance
- Clasificación de datos: "Internal - Confidential"
- Retention policies con S3 lifecycle (30d Standard → 90d IA → 365d Glacier → Delete)
- Auditoría mensual de fallos de autenticación
- Revisión trimestral de permisos IAM

## Estructura de Datos

### Webhook Request (Entrada)
```json
{
  "event_type": "order.created",
  "event_id": "evt_1234567890abcdef",
  "timestamp": "2026-01-15T14:30:00Z",
  "entity_id": "ORD-2026-001234",
  "payload": {
    "order_id": "ORD-2026-001234",
    "status": "pending",
    "created_at": "2026-01-15T14:29:55Z"
  }
}
```

### Enriched Data (Bronze Layer)
```json
{
  "event_metadata": {
    "event_type": "order.created",
    "event_id": "evt_1234567890abcdef",
    "event_timestamp": "2026-01-15T14:30:00Z",
    "ingestion_timestamp": "2026-01-15T14:30:02.345Z",
    "source_type": "webhook",
    "schema_version": "1.0"
  },
  "original_webhook": { },
  "enriched_data": {
    "order": { },
    "order_items": [ ]
  }
}
```

### Particionamiento S3
```
s3://cencosud-datalake-bronze-prod/webhooks/
  orders/year=2026/month=01/day=15/hour=14/part-00001.json.gz
  order-items/year=2026/month=01/day=15/hour=14/part-00001.json.gz
  shipping/year=2026/month=01/day=15/hour=14/part-00001.json.gz
  payments/year=2026/month=01/day=15/hour=14/part-00001.json.gz
  picking/year=2026/month=01/day=15/hour=14/part-00001.json.gz
```

## Monitoreo y Alertas

### Métricas Clave
- **APIGatewayLatency**: Latencia de respuesta (p50, p95, p99)
- **LambdaDuration**: Tiempo de ejecución de funciones
- **WebhookProcessingLatency**: Latencia end-to-end
- **JanisAPICallDuration**: Tiempo de llamadas a APIs externas
- **EnrichmentSuccess/Failure**: Tasa de éxito de enriquecimiento
- **FirehoseDeliverySuccess**: Tasa de éxito de entrega a S3
- **DLQMessageCount**: Mensajes en Dead Letter Queue

### Alarmas Críticas (Notificación Inmediata)
- Error rate > 5% por 2 períodos consecutivos de 5 minutos
- p99 latency > 10 segundos por 2 períodos consecutivos
- DLQ message count > 0
- API Gateway 5xx errors > 10 en 5 minutos
- Lambda throttling events > 0

### Alarmas de Warning (Notificación en Horas Laborales)
- Error rate > 2% por 10 minutos
- p95 latency > 5 segundos por 10 minutos
- Firehose delivery success < 99% por 15 minutos
- Data freshness > 5 minutos por 10 minutos

### Dashboard CloudWatch
- **Throughput Panel**: Requests/segundo por endpoint, éxito vs. fallos
- **Latency Panel**: Latencias de API Gateway, Lambda y end-to-end
- **Error Panel**: Tasa de errores, tipos de error, mensajes en DLQ
- **Data Pipeline Panel**: Records en Kinesis, delivery success, objetos S3 creados
- **Resource Utilization Panel**: Ejecuciones concurrentes, memoria utilizada

## Performance SLA

| Métrica | Target | Medición |
|---------|--------|----------|
| Latencia p99 | < 5 segundos | API Gateway response time |
| Latencia p95 | < 3 segundos | API Gateway response time |
| Signature validation | < 100 ms | Lambda duration |
| Uptime | 99.95% | Successful requests / total requests |
| Data freshness | < 2 minutos | Ingestion to S3 write time |
| Error rate | < 1% | Failed requests / total requests |

## Disaster Recovery

### Multi-AZ Deployment
- Todos los servicios desplegados automáticamente en múltiples AZs
- Failover automático sin pérdida de datos
- S3 con 99.999999999% durability (11 nines)

### Cross-Region Replication
- Bronze layer replicado a us-west-2
- Replication lag < 15 minutos
- Permite recovery si región primaria falla

### Recovery Targets
- **RTO (Recovery Time Objective)**: 2 horas
- **RPO (Recovery Point Objective)**: 15 minutos
- **Backup Strategy**: Infrastructure as Code (Terraform) + S3 replication

### Procedimientos de Recovery
1. **Lambda Failure**: Retry automático + DLQ capture
2. **Kinesis Failure**: Retry por 1 hora + error bucket
3. **Region Failure**: Recrear stack en us-west-2 con Terraform

## Configuración por Ambiente

### Development
- API base URL: https://api-dev.janis.com
- Rate limit: 100 requests/min
- Provisioned concurrency: Deshabilitado
- Log level: DEBUG

### Production
- API base URL: https://api.janis.com
- Rate limit: 1,000 requests/segundo
- Provisioned concurrency: 50 instancias (9 AM - 6 PM)
- Log level: INFO

## Operaciones y Mantenimiento

### Procedimientos Operacionales

1. **Ver Webhooks Recientes**
   ```bash
   aws logs tail /aws/lambda/janis-webhook-enrichment-prod --follow
   ```

2. **Verificar Mensajes en DLQ**
   ```bash
   aws sqs get-queue-attributes \
     --queue-url https://sqs.us-east-1.amazonaws.com/123456789/webhook-dlq-prod \
     --attribute-names ApproximateNumberOfMessages
   ```

3. **Replay de Mensajes desde DLQ**
   ```bash
   aws lambda invoke \
     --function-name janis-webhook-dlq-replay-prod \
     --payload '{"maxMessages": 100}' \
     response.json
   ```

4. **Rotación Manual de Secrets**
   ```bash
   aws secretsmanager rotate-secret \
     --secret-id janis-webhook-shared-secret
   ```

### Troubleshooting Común

- **High error rate**: Verificar disponibilidad de Janis API, revisar logs de Lambda
- **High latency**: Analizar X-Ray traces, verificar tiempos de respuesta de Janis API
- **DLQ accumulation**: Identificar patrones de error, corregir causa raíz, replay mensajes
- **Rate limiting**: Verificar tráfico legítimo vs. ataque, ajustar límites si necesario

## Plan de Implementación

El plan de implementación se encuentra detallado en `.kiro/specs/webhook-ingestion/tasks.md` y consta de 18 tareas principales organizadas en las siguientes fases:

### Fase 1: Infraestructura Base (Tasks 1-3)
- Setup de estructura de proyecto y Terraform
- Terraform para AWS Secrets Manager con rotación mensual
- Terraform para S3 buckets (Bronze layer y error bucket)
- Configuración de lifecycle policies y cross-region replication
- **Checkpoint de validación**

### Fase 2: Lambda Functions (Tasks 4-6)
- Lambda function para HMAC-SHA256 signature validation
- Lambda function para data enrichment con Janis API calls
- Configuración de Dead Letter Queue (SQS)
- Property-based tests con Hypothesis
- **Checkpoint de validación** (Task 6)

### Fase 3: Streaming y API Gateway (Tasks 7-8)
- Terraform para Kinesis Firehose con dynamic partitioning
- Terraform para API Gateway con endpoints específicos por evento
- Configuración de rate limiting y throttling
- IP whitelisting y custom domain
- **Property tests para partitioning y buffering**

### Fase 4: Validación y Monitoreo (Tasks 9-11)
- JSON schema definitions para webhook payloads
- CloudWatch dashboards, métricas y alarmas
- AWS X-Ray tracing para distributed tracing
- SNS topics para notificaciones
- **Checkpoint de integración end-to-end** (Task 11)

### Fase 5: Alta Disponibilidad y Operaciones (Tasks 12-14)
- Configuración multi-AZ deployment
- Cross-region replication a us-west-2
- DLQ replay Lambda function
- Scripts operacionales (logs, DLQ check, secret rotation)
- VPC networking y security hardening

### Fase 6: Optimización y Deployment (Tasks 15-18)
- Performance optimization (connection pooling, caching)
- Provisioned concurrency para peak hours
- Scripts de deployment automatizado
- Runbooks operacionales y documentación
- **Checkpoint final de production readiness** (Task 18)

### Notas de Implementación
- Tasks marcadas con `*` son opcionales para MVP más rápido
- Property-based tests usan Hypothesis para validación universal
- Infraestructura desplegada con Terraform y local state management
- Credenciales AWS pasadas como variables, nunca hardcodeadas
- Lambda functions usan Python 3.11 runtime

## Integración con Sistema de Polling

El Sistema de Webhooks trabaja en conjunto con el Sistema de Polling API:

- **Webhooks**: Ingesta en tiempo real (latencia de segundos)
- **Polling**: Red de seguridad para datos perdidos (latencia de minutos)
- **Destino común**: Ambos escriben a S3 Bronze Layer con mismo formato
- **Deduplicación**: Downstream processing maneja duplicados por event_id
- **Complementariedad**: Webhooks para eventos críticos, polling para sincronización completa

## Próximos Pasos

1. **Implementación Fase 1**: Desplegar infraestructura base (VPC, S3, IAM)
2. **Desarrollo Lambda**: Implementar funciones de validación y enriquecimiento
3. **Configuración API Gateway**: Crear endpoints y configurar rate limiting
4. **Setup Kinesis**: Configurar Firehose con particionamiento dinámico
5. **Testing**: Validación end-to-end en ambiente dev
6. **Deployment Producción**: Rollout gradual con monitoreo intensivo

## Referencias

- **Especificación Completa**: `.kiro/specs/webhook-ingestion/design.md`
- **Requerimientos**: `.kiro/specs/webhook-ingestion/requirements.md`
- **Arquitectura General**: `Documento Detallado de Diseño Janis-Cenco.md`
- **Sistema Complementario**: `Sistema de Polling API - Resumen Ejecutivo.md`

## Contacto

Para preguntas o soporte relacionado con el Sistema de Webhooks, contactar al equipo de Data Engineering.
