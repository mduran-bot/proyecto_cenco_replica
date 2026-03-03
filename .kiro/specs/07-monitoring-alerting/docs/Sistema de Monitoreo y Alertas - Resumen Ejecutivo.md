# Sistema de Monitoreo y Alertas - Resumen Ejecutivo

## Fecha de Actualización
15 de Enero, 2026

## Propósito

El Sistema de Monitoreo y Alertas proporciona observabilidad completa end-to-end de la plataforma de integración Janis-Cencosud. El sistema implementa monitoreo proactivo mediante CloudWatch, alertas inteligentes con enriquecimiento contextual, y dashboards personalizados para diferentes stakeholders, garantizando la detección temprana de problemas y reducción del tiempo de resolución (MTTR).

Este sistema es crítico para mantener la confiabilidad del pipeline de datos, asegurando que los datos lleguen a tiempo y con la calidad esperada para análisis de negocio.

## Arquitectura de Alto Nivel

### Componentes Principales

1. **Amazon CloudWatch**: Plataforma centralizada de métricas, logs y alarmas
2. **Amazon SNS**: Sistema de notificaciones multi-canal con niveles de severidad
3. **AWS Lambda**: Enriquecimiento de alertas con contexto y runbooks
4. **Amazon EventBridge**: Routing inteligente de alertas según severidad
5. **CloudWatch Dashboards**: Visualización en tiempo real para diferentes audiencias
6. **AWS CloudTrail**: Auditoría completa de acciones en AWS
7. **AWS Config**: Compliance monitoring y security posture

### Flujo de Monitoreo

```
Data Pipeline Components → CloudWatch (Metrics + Logs + Alarms) → Alert Enrichment Lambda → EventBridge Routing → SNS Topics (Tiered) → Notification Channels → Dashboards
```

### Proceso de Alerting

1. **Metric Collection**: Servicios AWS emiten métricas automáticamente a CloudWatch
2. **Log Aggregation**: Logs estructurados se centralizan en CloudWatch Logs
3. **Alarm Evaluation**: CloudWatch Alarms evalúan métricas contra umbrales
4. **Alert Enrichment**: Lambda enriquece alertas con contexto, runbooks y links
5. **Notification Routing**: EventBridge enruta alertas según severidad
6. **Multi-Channel Delivery**: SNS entrega notificaciones a PagerDuty, Slack, Email, SMS
7. **Dashboard Visualization**: CloudWatch Dashboards muestran métricas en tiempo real

## Características Clave

### 1. Recolección Completa de Métricas

**Standard Metrics** (Automáticas):
- API Gateway: Count, Latency, 4XXError, 5XXError
- Lambda: Invocations, Duration, Errors, ConcurrentExecutions
- Kinesis Firehose: DeliveryToS3.Success, DeliveryToS3.DataFreshness
- Glue: numCompletedTasks, numFailedTasks
- Redshift: CPUUtilization, DatabaseConnections, HealthStatus
- MWAA: TaskInstanceSuccesses, TaskInstanceFailures

**Custom Metrics** (Emitidas por aplicación):
- WebhooksReceived: Cantidad de webhooks procesados
- DataFreshnessMinutes: Tiempo desde última actualización de datos
- DataQualityScore: Score de calidad de datos por tabla
- RecordsProcessed: Cantidad de registros procesados por etapa
- BusinessKPIs: Métricas de negocio (órdenes, revenue, etc.)

**Metric Namespaces**:
- `JanisCencosud/DataPipeline`: Métricas de flujo de datos
- `JanisCencosud/DataQuality`: Métricas de calidad de datos
- `JanisCencosud/Business`: KPIs de negocio
- `JanisCencosud/Performance`: Métricas de rendimiento

### 2. Logging Estructurado con JSON

**Formato Consistente**:
```json
{
  "timestamp": "2026-01-15T10:30:45.123Z",
  "level": "INFO",
  "component": "webhook-processor",
  "correlation_id": "req-abc123-def456",
  "event_type": "order_created",
  "entity_id": "ORD-12345",
  "duration_ms": 245,
  "status": "success",
  "message": "Order webhook processed successfully",
  "metadata": {
    "records_processed": 1,
    "s3_key": "bronze/orders/2026/01/15/order-12345.json"
  }
}
```

**Log Groups Structure**:
- `/aws/lambda/janis-webhook-processor-prod`
- `/aws/lambda/janis-data-enrichment-prod`
- `/aws/glue/jobs/bronze-to-silver-orders`
- `/aws/mwaa/cencosud-mwaa-environment/dag-processor`
- `/aws/apigateway/janis-webhook-api-prod`

**Log Retention Policies**:
- Application logs: 90 días (balance entre costo y troubleshooting)
- Audit logs: 2557 días (7 años para compliance)
- Debug logs: 30 días (troubleshooting temporal)
- Performance logs: 90 días (análisis de tendencias)

### 3. Alarmas Inteligentes Multi-Capa

**Infrastructure Alarms**:
- API Gateway error rate > 5%
- Lambda error rate > 2%, duration > p99 baseline + 50%
- Kinesis DeliveryToS3.Success < 99%
- Glue job failure rate > 5%
- Redshift CPUUtilization > 80%, HealthStatus != 1

**Data Pipeline Alarms**:
- Data freshness > 30 minutos
- Data volume anomaly detection (spikes/drops inusuales)
- Validation failure rate > 1%
- Schema evolution events no esperados

**Performance Alarms**:
- Webhook latency p99 > 5 segundos
- Records processed per minute < baseline - 30%
- API requests per second > capacity * 0.8

### 4. Alertas Enriquecidas con Contexto

**Alert Enrichment Lambda** agrega:
- **Runbook**: Pasos específicos de remediación
- **Dashboard URL**: Link directo al dashboard relevante
- **Log Insights URL**: Query pre-configurado para logs relacionados
- **Business Impact**: Evaluación del impacto en negocio
- **Suggested Actions**: Lista de acciones recomendadas
- **Severity**: Determinación automática de severidad

**Tiered SNS Topics**:
```
janis-alerts-critical-prod   → PagerDuty + SMS (inmediato)
janis-alerts-high-prod       → Email + Slack (5 min)
janis-alerts-medium-prod     → Slack (15 min)
janis-alerts-low-prod        → Daily digest email
```

**Severity Determination**:
- **Critical**: Data loss, corruption, service unavailability
- **High**: Performance degradation > 50%, error rate > threshold
- **Medium**: Performance degradation < 50%, approaching limits
- **Low**: Informational, optimization opportunities

### 5. Alert Suppression Inteligente

**Prevención de Alert Fatigue**:
- Supresión de alertas duplicadas dentro de 15 minutos
- Detección de alarmas relacionadas (no alertar si alarma padre ya activa)
- Agrupación de alertas similares
- Rate limiting por tipo de alerta

### 6. Dashboards Personalizados por Audiencia

**Executive Dashboard** (Stakeholders no técnicos):
- System Health Status (0-100 score)
- Data Freshness Indicators por entidad
- Key Business Metrics (órdenes, revenue, quality score)
- Critical Alerts Summary

**Operations Dashboard** (Ingenieros de operaciones):
- Pipeline Status (records en cada etapa)
- Resource Utilization (Lambda, Glue, Redshift, API Gateway)
- Error Rates con anotaciones de deployments
- Performance Indicators (latency percentiles p50, p95, p99)
- Auto-refresh: 1 minuto

**Data Quality Dashboard**:
- Data Completeness Score por entidad
- Validation Failure Rates por tipo y entidad
- Schema Evolution Timeline
- Data Lineage Visualization

**Cost Management Dashboard**:
- Current Spend by Service (pie chart)
- Cost Trends (30 días + proyección)
- Cost per Record Processed
- Optimization Opportunities

### 7. Health Checks y Synthetic Monitoring

**Health Check Lambda** (cada 5 minutos):
- Verifica API Gateway, Lambda, Kinesis, Glue, Redshift
- Verifica conectividad con Janis API
- Calcula overall health score
- Emite métrica OverallHealth a CloudWatch

**Synthetic Transactions** (cada 15 minutos):
- Envía webhook sintético al endpoint
- Verifica procesamiento end-to-end
- Valida datos en S3
- Mide latencia y success rate
- Emite métricas WebhookLatency y EndToEndSuccess

**Circuit Breaker Pattern**:
- Previene cascading failures en llamadas a servicios externos
- Estados: CLOSED, OPEN, HALF_OPEN
- Threshold: 5 fallos consecutivos
- Timeout: 60 segundos antes de retry

### 8. Compliance y Auditoría

**CloudTrail Integration**:
- Auditoría completa de todas las acciones en AWS
- Multi-region trail con log file validation
- Monitored events: data access, config changes, authentication
- Retention: 90 días en CloudWatch Logs, indefinido en S3

**Security Monitoring**:
- AWS Config Rules para encryption at rest/in transit
- GuardDuty para threat detection
- Security Hub para consolidated security findings
- PII Access Monitoring con métricas dedicadas

**Data Retention Compliance**:
- Automated lifecycle policies en S3
- Redshift data retention monitoring
- Alertas cuando datos exceden retention period

### 9. Capacity Planning y Forecasting

**Resource Utilization Tracking**:
- Lambda concurrent executions
- Glue DPU hours
- Redshift storage y connections
- S3 storage
- API requests per hour

**Forecasting Model**:
- Time series analysis con Exponential Smoothing
- Weekly seasonality detection
- 30-day forecast con confidence intervals
- Recommended capacity calculations

**Cost Projection**:
- Growth scenarios: conservative (10%), moderate (30%), aggressive (50%)
- 12-month cost projections
- Per-service cost breakdown
- Optimization recommendations

### 10. Integración con Herramientas Externas

**ITSM Integration** (ServiceNow/Jira):
- Creación automática de incidents para alertas críticas
- Mapping de severidad a urgency/impact
- Tracking de incident numbers
- Work notes con runbooks

**Metrics Export**:
- Prometheus export para portabilidad
- Push to Prometheus gateway cada 1 minuto
- Gauges para data freshness y pipeline throughput

**Webhook Notifications**:
- Generic webhook integration para sistemas externos
- Payload estructurado con alert details
- Retry logic con timeout

**SSO/SAML Authentication**:
- Cognito User Pool para dashboard access
- SAML identity provider integration
- Role-based access control (RBAC)

## Componentes de Implementación

### Lambda Functions

| Función | Responsabilidad | Trigger |
|---------|-----------------|---------|
| alert-enrichment-lambda | Enriquecimiento de alertas con contexto | SNS (alarmas de CloudWatch) |
| health-check-lambda | Health check comprehensivo de componentes | EventBridge (cada 5 min) |
| synthetic-test-lambda | Synthetic transactions end-to-end | EventBridge (cada 15 min) |
| capacity-metrics-lambda | Recolección de métricas de capacidad | EventBridge (cada hora) |
| cost-projection-lambda | Proyección de costos y forecasting | EventBridge (semanal) |

### CloudWatch Resources

| Recurso | Cantidad | Propósito |
|---------|----------|-----------|
| Log Groups | 10+ | Logs por servicio AWS |
| Metric Namespaces | 4 | DataPipeline, DataQuality, Business, Performance |
| Alarms | 50+ | Infrastructure, pipeline, performance alarms |
| Dashboards | 4 | Executive, Operations, Data Quality, Cost |
| SNS Topics | 4 | Critical, High, Medium, Low alerts |

### Terraform Modules

| Módulo | Recursos | Ubicación |
|--------|----------|-----------|
| cloudwatch-metrics | Custom metrics, metric filters | `terraform/modules/cloudwatch/` |
| cloudwatch-alarms | Alarm definitions por servicio | `terraform/modules/cloudwatch/` |
| cloudwatch-dashboards | Dashboard JSON definitions | `terraform/modules/cloudwatch/` |
| sns-alerting | SNS topics, subscriptions | `terraform/modules/sns/` |
| lambda-monitoring | Lambda functions para monitoring | `terraform/modules/lambda/` |
| cloudtrail-audit | CloudTrail configuration | `terraform/modules/cloudtrail/` |

## Propiedades de Correctness

El sistema implementa 12 propiedades de correctness que garantizan comportamiento correcto:

### Métricas y Logs (Properties 1-3)
- Emisión completa de métricas críticas en cada ejecución del pipeline
- Consistencia de thresholds de alarmas con bounds válidos
- Validez de estructura de logs con campos requeridos

### Alertas (Properties 4-6)
- Completitud de enriquecimiento de alertas (runbook, dashboard, actions)
- Correctitud de routing de alertas según severidad
- Efectividad de supresión de alertas duplicadas

### Monitoreo (Properties 7-9)
- Precisión de métricas de data freshness
- Comprehensividad de health checks (todos los componentes críticos)
- Validación end-to-end de synthetic transactions

### Compliance y Costos (Properties 10-12)
- Completitud de audit logs para operaciones sensibles
- Precisión de métricas de costo
- Consistencia de datos en dashboards

## Métricas Clave de Monitoreo

### Availability Metrics
- Overall System Health Score: Target > 95%
- Component Availability: Target > 99.9% por componente
- Synthetic Transaction Success Rate: Target > 99%

### Performance Metrics
- Webhook Processing Latency p99: Target < 5 segundos
- Data Freshness: Target < 15 minutos
- Pipeline Throughput: Target > 100,000 records/minuto

### Quality Metrics
- Data Quality Score: Target > 95%
- Validation Failure Rate: Target < 1%
- Schema Evolution Success Rate: Target > 99%

### Operational Metrics
- Mean Time to Detect (MTTD): Target < 5 minutos
- Mean Time to Resolve (MTTR): Target < 30 minutos
- Alert Accuracy (no false positives): Target > 95%

## Configuración de Alarmas

### Critical Alarms (Notificación Inmediata)
- Job failure rate > 5% en 15 minutos
- Data quality score degradation > 5% en 15 minutos
- Service unavailability detectada
- Data loss o corruption detectada
- Resource exhaustion (CPU > 90%, Memory > 85%)

### High Alarms (Notificación en 5 minutos)
- Performance degradation > 50%
- Error rate > threshold configurado
- Data freshness > 30 minutos
- DLQ message count > 100

### Medium Alarms (Notificación en 15 minutos)
- Performance degradation < 50%
- Approaching resource limits (> 80%)
- Quality score degradation > 2% en 1 hora
- Iceberg table file count > 10,000

### Low Alarms (Daily Digest)
- Informational events
- Optimization opportunities
- Usage trends
- Capacity planning recommendations

## Dashboards CloudWatch

### Dashboard 1: Executive View
- **Audience**: Stakeholders no técnicos, management
- **Refresh**: 5 minutos
- **Widgets**: 4 (Health Status, Data Freshness, Business Metrics, Alerts Summary)
- **Purpose**: Vista de alto nivel del estado del sistema

### Dashboard 2: Operations View
- **Audience**: Ingenieros de operaciones, SRE
- **Refresh**: 1 minuto
- **Widgets**: 10+ (Pipeline Status, Resource Utilization, Error Rates, Performance)
- **Purpose**: Monitoreo técnico detallado en tiempo real

### Dashboard 3: Data Quality View
- **Audience**: Data engineers, data quality team
- **Refresh**: 5 minutos
- **Widgets**: 8 (Completeness, Validation Failures, Schema Evolution, Lineage)
- **Purpose**: Monitoreo de calidad y completitud de datos

### Dashboard 4: Cost Management View
- **Audience**: FinOps, management
- **Refresh**: Daily
- **Widgets**: 6 (Spend by Service, Cost Trends, Cost per Record, Optimization)
- **Purpose**: Visibilidad y optimización de costos

## Operaciones y Mantenimiento

### Procedimientos Operacionales Diarios

**Morning Checks (9 AM)**:
1. Revisar Executive Dashboard para overall health
2. Verificar alertas críticas/high de últimas 24 horas
3. Validar data freshness para todas las entidades
4. Revisar cost dashboard para anomalías de gasto

**Continuous Monitoring**:
- Operations Dashboard en pantalla dedicada
- Slack channel para alertas medium/high
- PagerDuty para alertas críticas 24/7

### Comandos Útiles

**Ver Métricas en CLI**:
```bash
# Data freshness para orders
aws cloudwatch get-metric-statistics \
  --namespace JanisCencosud/DataPipeline \
  --metric-name DataFreshnessMinutes \
  --dimensions Name=EntityType,Value=orders \
  --start-time 2026-01-15T00:00:00Z \
  --end-time 2026-01-15T23:59:59Z \
  --period 300 \
  --statistics Average
```

**Ver Logs Recientes**:
```bash
# Logs de webhook processor últimos 10 minutos
aws logs tail /aws/lambda/janis-webhook-processor-prod \
  --since 10m \
  --follow
```

**Buscar Errores en Logs**:
```bash
# CloudWatch Logs Insights query
aws logs start-query \
  --log-group-name /aws/lambda/janis-webhook-processor-prod \
  --start-time $(date -u -d '1 hour ago' +%s) \
  --end-time $(date -u +%s) \
  --query-string 'fields @timestamp, @message | filter level = "ERROR" | sort @timestamp desc | limit 20'
```

**Verificar Estado de Alarmas**:
```bash
# Listar alarmas en estado ALARM
aws cloudwatch describe-alarms \
  --state-value ALARM \
  --query 'MetricAlarms[*].[AlarmName,StateReason]' \
  --output table
```

**Trigger Manual de Health Check**:
```bash
# Invocar health check Lambda
aws lambda invoke \
  --function-name janis-cencosud-health-check-prod \
  --payload '{}' \
  response.json
```

## Seguridad

### Access Control
- IAM roles separados para Lambda functions de monitoring
- Principio de menor privilegio
- CloudWatch Logs encryption at rest
- SNS topic access policies restrictivas

### Audit Trail
- CloudTrail logging de todas las acciones
- CloudWatch Logs Insights para análisis de audit logs
- Retention de 7 años para compliance
- Alertas en accesos sospechosos

### Data Privacy
- PII access monitoring con métricas dedicadas
- Masking de datos sensibles en logs
- Encryption en tránsito (TLS 1.2+)
- Encryption en reposo (KMS)

## Monitoreo de Costos

### Cost Breakdown Estimado (Mensual)

| Servicio | Costo Estimado | Justificación |
|----------|----------------|---------------|
| CloudWatch Metrics | $50-100 | Custom metrics + standard metrics |
| CloudWatch Logs | $30-60 | Log ingestion + storage (90 días) |
| CloudWatch Alarms | $10-20 | ~50 alarmas |
| CloudWatch Dashboards | $9 | 3 dashboards (primero gratis) |
| SNS | $5-10 | Notificaciones |
| Lambda (monitoring) | $10-20 | Health checks + enrichment |
| CloudTrail | $5-10 | Event logging |
| **Total** | **$119-229/mes** | **Costo operacional de monitoring** |

### Cost Optimization Strategies
- Usar metric math para métricas derivadas (evitar custom metrics adicionales)
- Ajustar log retention según criticidad
- Usar CloudWatch Anomaly Detection (incluido) en lugar de alarmas estáticas
- Consolidar dashboards cuando sea posible
- Usar SNS filtering para reducir notificaciones innecesarias

## Plan de Implementación

El plan de implementación detallado se encuentra en `.kiro/specs/monitoring-alerting/tasks.md` y consta de 19 tareas principales organizadas en múltiples fases:

### Fase 1: Infraestructura Base y Métricas (Tasks 1-4)
- Setup de estructura de directorios Terraform
- Implementación de CloudWatch metric namespaces
- Biblioteca Python para emisión de métricas
- Configuración de alarmas de infraestructura (API Gateway, Lambda, Kinesis, Glue, Redshift)
- **Checkpoint**: Verificar alarmas de infraestructura

### Fase 2: Monitoreo de Pipeline y Logging (Tasks 5-6)
- Lambda para cálculo de data freshness
- Alarmas de pipeline de datos
- Tracking de volumen de datos
- Biblioteca de logging estructurado con formato JSON
- CloudWatch Log Groups con políticas de retención
- BufferedLogger para resiliencia

### Fase 3: Sistema de Alertas (Tasks 7-8)
- SNS topics con niveles (critical, high, medium, low)
- Lambda de enriquecimiento de alertas
- Lógica de routing de alertas
- Configuración de runbooks
- Supresión de alertas duplicadas
- **Checkpoint**: Verificar sistema de alertas

### Fase 4: Dashboards (Task 9)
- Executive Dashboard (health status, data freshness, business metrics, alerts)
- Operations Dashboard (pipeline status, resource utilization, error rates, performance)
- Data Quality Dashboard (completeness, validation failures, schema evolution)
- Cost Management Dashboard (spend by service, cost trends, cost per record, budget)

### Fase 5: Health Checks y Compliance (Tasks 10-12)
- Lambda de health check comprehensivo
- Synthetic transactions end-to-end
- Circuit breaker pattern para llamadas externas
- CloudTrail para auditoría
- AWS Config para compliance
- GuardDuty para threat detection
- Lambda de monitoreo de acceso a PII
- **Checkpoint**: Verificar compliance monitoring

### Fase 6: Capacity Planning e Integraciones (Tasks 13-14)
- Lambda de recolección de métricas de capacidad
- Lambda de forecasting con exponential smoothing
- Lambda de proyección de costos
- Integración con ITSM (ServiceNow/Jira)
- Export a Prometheus
- Soporte para webhook notifications

### Fase 7: Error Handling y Documentación (Tasks 15-17)
- Error handling en metric emission
- Error handling en alert enrichment
- Error handling en health checks
- Error handling en integraciones externas
- **Checkpoint**: Verificar error handling
- Scripts de deployment Terraform
- Documentación de runbooks
- Documentación operacional
- README del sistema de monitoreo

### Fase 8: Testing End-to-End (Tasks 18-19)
- Integration test de flujo de monitoreo completo
- Integration test de rendering de dashboards
- Integration test de health checks
- Integration test de synthetic transactions
- **Checkpoint Final**: Verificación completa del sistema

## Testing Strategy

### Property-Based Testing
- Framework: Hypothesis para Python
- Mínimo 100 iteraciones por property test
- Validación de 12 propiedades de correctness

### Unit Testing
- Testing de metric emission logic
- Testing de alarm configuration
- Testing de log formatting
- Testing de alert enrichment
- Testing de routing logic

### Integration Testing
- End-to-end monitoring flow
- Dashboard rendering
- Health check execution
- Synthetic transaction validation

### Load Testing
- Metric emission: 1000 metrics/segundo
- Alert processing: 100 alarmas simultáneas
- Dashboard performance: 50+ widgets

## Próximos Pasos

1. **Implementación Fase 1**: Desplegar infraestructura base de CloudWatch
2. **Implementación Fase 2**: Configurar alarmas y alertas
3. **Testing**: Validar alarmas con datos de prueba
4. **Implementación Fase 3**: Crear dashboards
5. **Implementación Fase 4-7**: Completar health checks, compliance e integraciones
6. **Production Deployment**: Rollout gradual con monitoreo intensivo

## Referencias

- **Especificación Completa**: `.kiro/specs/monitoring-alerting/design.md`
- **Requerimientos**: `.kiro/specs/monitoring-alerting/requirements.md` (pendiente)
- **Plan de Implementación**: `.kiro/specs/monitoring-alerting/tasks.md` (pendiente)
- **Arquitectura General**: `Documento Detallado de Diseño Janis-Cenco.md`
- **Sistemas Monitoreados**: Todos los componentes del pipeline Janis-Cencosud

## Contacto

Para preguntas o soporte relacionado con el Sistema de Monitoreo y Alertas, contactar al equipo de SRE/DevOps.
