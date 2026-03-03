# Design Document: Monitoring and Alerting System

## Overview

Este documento describe el diseño del sistema de monitoreo y alertas para la plataforma de integración Janis-Cencosud. El sistema proporciona observabilidad completa del pipeline de datos mediante CloudWatch, implementa alertas inteligentes con SNS, y ofrece dashboards personalizados para diferentes stakeholders.

### Design Principles

- **Observabilidad Completa**: Visibilidad end-to-end de todos los componentes y flujos de datos
- **Alertas Accionables**: Notificaciones contextuales con runbooks y pasos de remediación
- **Escalabilidad**: Diseño que escala con el crecimiento del pipeline de datos
- **Costo-Efectividad**: Optimización de retención de logs y métricas según criticidad
- **Automatización**: Detección automática de anomalías y respuesta proactiva

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     Data Pipeline Components                     │
│  API Gateway │ Lambda │ Kinesis │ Glue │ Redshift │ MWAA │ S3  │
└────────────┬────────────────────────────────────────────────────┘
             │ Metrics, Logs, Traces
             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      CloudWatch Services                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │   Metrics    │  │     Logs     │  │   Alarms     │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
└────────────┬────────────────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Alerting & Notification                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │  SNS Topics  │  │   Lambda     │  │  EventBridge │         │
│  │  (Tiered)    │  │  (Enrichment)│  │   (Routing)  │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
└────────────┬────────────────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Notification Channels                         │
│  PagerDuty │ Slack │ Email │ SMS │ ITSM Integration            │
└─────────────────────────────────────────────────────────────────┘

             ▼
┌─────────────────────────────────────────────────────────────────┐
│                         Dashboards                               │
│  Executive │ Operations │ Data Quality │ Cost Management        │
└─────────────────────────────────────────────────────────────────┘
```

### Component Interaction Flow

1. **Metric Collection**: Servicios AWS emiten métricas automáticamente a CloudWatch
2. **Log Aggregation**: Logs estructurados se centralizan en CloudWatch Logs
3. **Alarm Evaluation**: CloudWatch Alarms evalúan métricas contra umbrales
4. **Alert Enrichment**: Lambda enriquece alertas con contexto y runbooks
5. **Notification Routing**: EventBridge enruta alertas según severidad
6. **Multi-Channel Delivery**: SNS entrega notificaciones a múltiples canales
7. **Dashboard Visualization**: CloudWatch Dashboards muestran métricas en tiempo real

## Components and Interfaces

### 1. Metric Collection Layer

#### CloudWatch Metrics
**Purpose**: Recolección centralizada de métricas de todos los componentes AWS

**Standard Metrics** (Automáticas por servicio):
- API Gateway: Count, Latency, 4XXError, 5XXError
- Lambda: Invocations, Duration, Errors, ConcurrentExecutions
- Kinesis Firehose: DeliveryToS3.Success, DeliveryToS3.DataFreshness
- Glue: glue.driver.aggregate.numCompletedTasks, glue.driver.aggregate.numFailedTasks
- Redshift: CPUUtilization, DatabaseConnections, HealthStatus
- MWAA: DAGProcessingTotalParseTime, TaskInstanceSuccesses, TaskInstanceFailures

**Custom Metrics** (Emitidas por aplicación):
```python
# Ejemplo: Lambda emitiendo custom metrics
import boto3
cloudwatch = boto3.client('cloudwatch')

cloudwatch.put_metric_data(
    Namespace='JanisCencosud/DataPipeline',
    MetricData=[
        {
            'MetricName': 'WebhooksReceived',
            'Value': webhook_count,
            'Unit': 'Count',
            'Dimensions': [
                {'Name': 'EntityType', 'Value': 'orders'},
                {'Name': 'Environment', 'Value': 'prod'}
            ]
        }
    ]
)
```

**Metric Namespaces**:
- `JanisCencosud/DataPipeline`: Métricas de flujo de datos
- `JanisCencosud/DataQuality`: Métricas de calidad de datos
- `JanisCencosud/Business`: KPIs de negocio
- `JanisCencosud/Performance`: Métricas de rendimiento


#### Log Collection and Structured Logging

**Log Groups Structure**:
```
/aws/lambda/janis-webhook-processor-prod
/aws/lambda/janis-data-enrichment-prod
/aws/glue/jobs/bronze-to-silver-orders
/aws/mwaa/cencosud-mwaa-environment/dag-processor
/aws/apigateway/janis-webhook-api-prod
```

**Structured Log Format** (JSON):
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

**Log Retention Policies**:
- Application logs: 90 days (balance entre costo y troubleshooting)
- Audit logs: 2557 days (7 años para compliance)
- Debug logs: 30 days (solo para troubleshooting temporal)
- Performance logs: 90 days (análisis de tendencias)

**Rationale**: Retención diferenciada optimiza costos mientras cumple requisitos de compliance y operacionales.

### 2. Alarm Configuration Layer

#### Infrastructure Alarms

**API Gateway Alarms**:
```hcl
# Terraform configuration
resource "aws_cloudwatch_metric_alarm" "api_gateway_error_rate" {
  alarm_name          = "janis-api-gateway-error-rate-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "5XXError"
  namespace           = "AWS/ApiGateway"
  period              = 300
  statistic           = "Average"
  threshold           = 5.0
  alarm_description   = "API Gateway error rate exceeds 5%"
  alarm_actions       = [aws_sns_topic.critical_alerts.arn]
  
  dimensions = {
    ApiName = "janis-webhook-api"
  }
}
```

**Lambda Alarms**:
- Error rate > 2%: Indica problemas en lógica de procesamiento
- Duration > p99 baseline + 50%: Detecta degradación de performance
- Throttles > 0: Indica límites de concurrencia alcanzados
- Dead Letter Queue messages > 0: Mensajes fallidos requieren atención

**Kinesis Firehose Alarms**:
- DeliveryToS3.Success < 99%: Pérdida potencial de datos
- DeliveryToS3.DataFreshness > 900s: Retraso en entrega de datos

**Glue Job Alarms**:
- Job failure rate > 5%: Problemas en transformaciones ETL
- Job duration > baseline + 100%: Performance degradation

**Redshift Alarms**:
- CPUUtilization > 80%: Necesidad de scaling o optimización
- HealthStatus != 1: Cluster unhealthy
- PercentageDiskSpaceUsed > 85%: Riesgo de quedarse sin espacio


#### Data Pipeline Alarms

**Data Freshness Alarms**:
```python
# Custom metric for data freshness
def calculate_data_freshness():
    """Calculate time since last successful data update"""
    last_update = get_last_redshift_update_time()
    current_time = datetime.now(timezone.utc)
    freshness_minutes = (current_time - last_update).total_seconds() / 60
    
    cloudwatch.put_metric_data(
        Namespace='JanisCencosud/DataPipeline',
        MetricData=[{
            'MetricName': 'DataFreshnessMinutes',
            'Value': freshness_minutes,
            'Unit': 'None',
            'Dimensions': [
                {'Name': 'EntityType', 'Value': 'orders'},
                {'Name': 'Layer', 'Value': 'gold'}
            ]
        }]
    )
```

**Data Volume Anomaly Detection**:
- Usa CloudWatch Anomaly Detection para detectar spikes/drops inusuales
- Baseline automático basado en patrones históricos
- Alertas cuando volumen está fuera de banda de confianza

**Data Quality Alarms**:
- Validation failure rate > 1%: Problemas en calidad de datos fuente
- Schema evolution events: Cambios no esperados en estructura
- Completeness score < 95%: Datos incompletos o faltantes

#### Performance Alarms

**Latency Monitoring**:
```hcl
resource "aws_cloudwatch_metric_alarm" "webhook_latency_p99" {
  alarm_name          = "janis-webhook-latency-p99-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 3
  metric_name         = "Duration"
  namespace           = "AWS/Lambda"
  period              = 300
  extended_statistic  = "p99"
  threshold           = 5000  # 5 seconds
  alarm_description   = "Webhook processing p99 latency exceeds 5s"
  alarm_actions       = [aws_sns_topic.high_alerts.arn]
}
```

**Throughput Monitoring**:
- Records processed per minute < baseline - 30%: Degradación de throughput
- API requests per second > capacity * 0.8: Approaching limits

### 3. Alert Enrichment and Routing

#### Alert Enrichment Lambda

**Purpose**: Enriquecer alertas con contexto, runbooks y links relevantes

```python
# alert-enrichment-lambda/handler.py
import json
import boto3

def lambda_handler(event, context):
    """Enrich CloudWatch alarm with context and runbooks"""
    
    alarm = json.loads(event['Records'][0]['Sns']['Message'])
    alarm_name = alarm['AlarmName']
    
    # Get runbook for this alarm type
    runbook = get_runbook(alarm_name)
    
    # Get relevant dashboard links
    dashboard_url = get_dashboard_url(alarm_name)
    
    # Get recent related logs
    log_insights_url = get_log_insights_query(alarm_name)
    
    # Assess business impact
    impact = assess_business_impact(alarm)
    
    enriched_alert = {
        'alarm_name': alarm_name,
        'description': alarm['AlarmDescription'],
        'current_state': alarm['NewStateValue'],
        'reason': alarm['NewStateReason'],
        'timestamp': alarm['StateChangeTime'],
        'severity': determine_severity(alarm_name),
        'runbook': runbook,
        'dashboard_url': dashboard_url,
        'log_insights_url': log_insights_url,
        'business_impact': impact,
        'suggested_actions': get_suggested_actions(alarm_name)
    }
    
    # Route to appropriate SNS topic based on severity
    route_alert(enriched_alert)
    
    return {'statusCode': 200}
```


#### Tiered SNS Topics

**Topic Structure**:
```
janis-alerts-critical-prod   → PagerDuty + SMS
janis-alerts-high-prod       → Email + Slack (5 min)
janis-alerts-medium-prod     → Slack (15 min)
janis-alerts-low-prod        → Daily digest email
```

**Severity Determination Logic**:
- **Critical**: Data loss, corruption, service unavailability
- **High**: Performance degradation > 50%, error rate > threshold
- **Medium**: Performance degradation < 50%, approaching limits
- **Low**: Informational, optimization opportunities

**Alert Suppression**:
```python
def should_suppress_alert(alarm_name, current_time):
    """Prevent duplicate alerts for same issue"""
    
    # Check if same alarm fired in last 15 minutes
    recent_alerts = get_recent_alerts(alarm_name, minutes=15)
    if recent_alerts:
        return True
    
    # Check if related alarm already fired
    related_alarms = get_related_alarms(alarm_name)
    for related in related_alarms:
        if is_alarm_active(related):
            return True
    
    return False
```

### 4. Dashboard Layer

#### Executive Dashboard

**Purpose**: Vista de alto nivel para stakeholders no técnicos

**Widgets**:
1. **System Health Status** (Single Value)
   - Overall health score (0-100)
   - Color-coded: Green (>95), Yellow (90-95), Red (<90)

2. **Data Freshness Indicators** (Gauge)
   - Orders: Time since last update
   - Products: Time since last update
   - Inventory: Time since last update
   - Target: < 15 minutes

3. **Key Business Metrics** (Line Graph)
   - Orders processed today vs yesterday
   - Revenue trends
   - Data quality score

4. **Critical Alerts Summary** (Number)
   - Active critical alerts
   - Active high alerts
   - Alerts resolved in last 24h

**CloudWatch Dashboard JSON**:
```json
{
  "widgets": [
    {
      "type": "metric",
      "properties": {
        "metrics": [
          ["JanisCencosud/DataPipeline", "DataFreshnessMinutes", {"stat": "Average"}]
        ],
        "period": 300,
        "stat": "Average",
        "region": "us-east-1",
        "title": "Data Freshness",
        "yAxis": {"left": {"min": 0, "max": 30}}
      }
    }
  ]
}
```


#### Operations Dashboard

**Purpose**: Vista técnica detallada para ingenieros de operaciones

**Sections**:

1. **Pipeline Status** (Stacked Area Chart)
   - Records in each stage: Ingestion → Buffer → Transform → Load
   - Color-coded by stage

2. **Resource Utilization** (Multi-line Graph)
   - Lambda concurrent executions
   - Glue DPU utilization
   - Redshift CPU/Memory
   - API Gateway request rate

3. **Error Rates** (Line Graph with Annotations)
   - API Gateway 4XX/5XX
   - Lambda errors
   - Glue job failures
   - Redshift load failures
   - Annotations for deployments and incidents

4. **Performance Indicators** (Heatmap)
   - Latency percentiles (p50, p95, p99) por componente
   - Color intensity indica degradación

**Auto-refresh**: 1 minute para datos en tiempo real

#### Data Quality Dashboard

**Purpose**: Monitoreo de calidad y completitud de datos

**Widgets**:

1. **Data Completeness Score** (Gauge)
   - Percentage of expected fields populated
   - Per entity type (orders, products, inventory)

2. **Validation Failure Rates** (Stacked Bar Chart)
   - By validation rule type
   - By entity type
   - Trend over time

3. **Schema Evolution Timeline** (Event Timeline)
   - Schema changes detected
   - Impact assessment
   - Compatibility status

4. **Data Lineage Visualization** (Custom Widget)
   - Flow from source to destination
   - Transformation steps
   - Data quality checkpoints

**Implementation Note**: Data lineage visualization requiere custom widget usando CloudWatch Dashboard API con datos de AWS Glue Data Catalog.

#### Cost Management Dashboard

**Purpose**: Visibilidad de costos y optimización

**Widgets**:

1. **Current Spend by Service** (Pie Chart)
   - Breakdown: Lambda, Glue, Redshift, S3, Kinesis, etc.
   - Updated daily from Cost Explorer API

2. **Cost Trends** (Line Graph)
   - Daily spend last 30 days
   - Projected spend for month
   - Budget threshold line

3. **Cost per Record Processed** (Single Value)
   - Total cost / total records
   - Trend indicator (up/down)

4. **Optimization Opportunities** (Table)
   - Underutilized resources
   - Oversized instances
   - Potential savings

**Data Source**: AWS Cost Explorer API + custom Lambda para cálculos


### 5. Health Check and Synthetic Monitoring

#### Health Check Endpoints

**Lambda Health Check Function**:
```python
# health-check-lambda/handler.py
def lambda_handler(event, context):
    """Comprehensive health check for data pipeline"""
    
    health_status = {
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'overall_status': 'healthy',
        'components': {}
    }
    
    # Check API Gateway
    health_status['components']['api_gateway'] = check_api_gateway()
    
    # Check Lambda functions
    health_status['components']['lambda'] = check_lambda_functions()
    
    # Check Kinesis Firehose
    health_status['components']['kinesis'] = check_kinesis_streams()
    
    # Check Glue jobs
    health_status['components']['glue'] = check_glue_jobs()
    
    # Check Redshift
    health_status['components']['redshift'] = check_redshift_cluster()
    
    # Check external dependencies
    health_status['components']['janis_api'] = check_janis_api()
    
    # Determine overall status
    if any(c['status'] == 'unhealthy' for c in health_status['components'].values()):
        health_status['overall_status'] = 'unhealthy'
    elif any(c['status'] == 'degraded' for c in health_status['components'].values()):
        health_status['overall_status'] = 'degraded'
    
    # Emit metric
    cloudwatch.put_metric_data(
        Namespace='JanisCencosud/HealthCheck',
        MetricData=[{
            'MetricName': 'OverallHealth',
            'Value': 1 if health_status['overall_status'] == 'healthy' else 0,
            'Unit': 'None'
        }]
    )
    
    return {
        'statusCode': 200,
        'body': json.dumps(health_status)
    }
```

**Scheduled Execution**: EventBridge rule ejecuta cada 5 minutos

#### Synthetic Transactions

**Webhook Synthetic Test**:
```python
def test_webhook_endpoint():
    """Send synthetic webhook to test end-to-end flow"""
    
    synthetic_payload = {
        'event_type': 'synthetic_test',
        'entity_id': f'TEST-{uuid.uuid4()}',
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'data': {
            'test': True,
            'correlation_id': f'synthetic-{uuid.uuid4()}'
        }
    }
    
    # Send to webhook endpoint
    response = requests.post(
        WEBHOOK_URL,
        json=synthetic_payload,
        headers={'X-API-Key': get_api_key()}
    )
    
    # Track latency
    latency_ms = response.elapsed.total_seconds() * 1000
    
    # Verify data reached S3
    time.sleep(10)  # Wait for processing
    s3_exists = verify_s3_object(synthetic_payload['entity_id'])
    
    # Emit metrics
    cloudwatch.put_metric_data(
        Namespace='JanisCencosud/Synthetic',
        MetricData=[
            {
                'MetricName': 'WebhookLatency',
                'Value': latency_ms,
                'Unit': 'Milliseconds'
            },
            {
                'MetricName': 'EndToEndSuccess',
                'Value': 1 if s3_exists else 0,
                'Unit': 'None'
            }
        ]
    )
    
    return response.status_code == 200 and s3_exists
```

**Polling Synthetic Test**:
- Verifica conectividad con Janis API
- Simula polling de datos
- Valida respuesta y formato

**Frequency**: Synthetic tests ejecutan cada 15 minutos


#### Circuit Breaker Pattern

**Purpose**: Prevenir cascading failures en llamadas a servicios externos

```python
class CircuitBreaker:
    """Circuit breaker for external API calls"""
    
    def __init__(self, failure_threshold=5, timeout=60):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = 'CLOSED'  # CLOSED, OPEN, HALF_OPEN
    
    def call(self, func, *args, **kwargs):
        """Execute function with circuit breaker protection"""
        
        if self.state == 'OPEN':
            if time.time() - self.last_failure_time > self.timeout:
                self.state = 'HALF_OPEN'
            else:
                raise CircuitBreakerOpenError("Circuit breaker is OPEN")
        
        try:
            result = func(*args, **kwargs)
            self.on_success()
            return result
        except Exception as e:
            self.on_failure()
            raise
    
    def on_success(self):
        self.failure_count = 0
        self.state = 'CLOSED'
    
    def on_failure(self):
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = 'OPEN'
            # Emit metric
            cloudwatch.put_metric_data(
                Namespace='JanisCencosud/CircuitBreaker',
                MetricData=[{
                    'MetricName': 'CircuitBreakerOpen',
                    'Value': 1,
                    'Unit': 'Count'
                }]
            )

# Usage
janis_api_breaker = CircuitBreaker(failure_threshold=5, timeout=60)

def call_janis_api():
    return janis_api_breaker.call(requests.get, JANIS_API_URL)
```

### 6. Compliance and Audit Monitoring

#### CloudTrail Integration

**Purpose**: Auditoría completa de todas las acciones en AWS

**Configuration**:
```hcl
resource "aws_cloudtrail" "main" {
  name                          = "janis-cencosud-audit-trail"
  s3_bucket_name               = aws_s3_bucket.cloudtrail.id
  include_global_service_events = true
  is_multi_region_trail        = true
  enable_log_file_validation   = true
  
  event_selector {
    read_write_type           = "All"
    include_management_events = true
    
    data_resource {
      type   = "AWS::S3::Object"
      values = ["${aws_s3_bucket.datalake.arn}/*"]
    }
  }
  
  insight_selector {
    insight_type = "ApiCallRateInsight"
  }
}
```

**Monitored Events**:
- Data access: S3 GetObject, Redshift queries
- Configuration changes: IAM policy updates, security group modifications
- Authentication: Failed login attempts, MFA status
- Data modifications: S3 PutObject, Redshift COPY/INSERT


#### Security Monitoring

**AWS Config Rules**:
```hcl
# Encryption at rest
resource "aws_config_config_rule" "s3_encryption" {
  name = "s3-bucket-server-side-encryption-enabled"
  
  source {
    owner             = "AWS"
    source_identifier = "S3_BUCKET_SERVER_SIDE_ENCRYPTION_ENABLED"
  }
}

# Encryption in transit
resource "aws_config_config_rule" "api_gateway_ssl" {
  name = "api-gw-ssl-enabled"
  
  source {
    owner             = "AWS"
    source_identifier = "API_GW_SSL_ENABLED"
  }
}
```

**GuardDuty Integration**:
- Threat detection automático
- Alertas de actividad sospechosa
- Integration con SNS para notificaciones

**Security Hub**:
- Consolidated security findings
- Compliance checks (CIS AWS Foundations)
- Integration con SIEM corporativo

#### Data Privacy Compliance

**PII Access Monitoring**:
```python
def monitor_pii_access(event):
    """Monitor and log PII data access"""
    
    user = event['userIdentity']['principalId']
    resource = event['requestParameters']['key']
    action = event['eventName']
    
    # Check if resource contains PII
    if is_pii_resource(resource):
        log_pii_access(user, resource, action)
        
        # Emit metric
        cloudwatch.put_metric_data(
            Namespace='JanisCencosud/Compliance',
            MetricData=[{
                'MetricName': 'PIIAccess',
                'Value': 1,
                'Unit': 'Count',
                'Dimensions': [
                    {'Name': 'User', 'Value': user},
                    {'Name': 'Action', 'Value': action}
                ]
            }]
        )
```

**Data Retention Compliance**:
- Automated lifecycle policies en S3
- Redshift data retention monitoring
- Alertas cuando datos exceden retention period

### 7. Capacity Planning and Forecasting

#### Resource Utilization Tracking

**Time Series Data Collection**:
```python
def collect_capacity_metrics():
    """Collect resource utilization for capacity planning"""
    
    metrics = {
        'lambda_concurrent_executions': get_lambda_concurrency(),
        'glue_dpu_hours': get_glue_dpu_usage(),
        'redshift_storage_gb': get_redshift_storage(),
        'redshift_connections': get_redshift_connections(),
        's3_storage_gb': get_s3_storage(),
        'api_requests_per_hour': get_api_request_rate()
    }
    
    # Store in CloudWatch for trend analysis
    for metric_name, value in metrics.items():
        cloudwatch.put_metric_data(
            Namespace='JanisCencosud/Capacity',
            MetricData=[{
                'MetricName': metric_name,
                'Value': value,
                'Unit': 'None',
                'Timestamp': datetime.now(timezone.utc)
            }]
        )
    
    # Store in S3 for long-term analysis
    s3.put_object(
        Bucket='janis-cencosud-metrics',
        Key=f'capacity/{datetime.now().strftime("%Y/%m/%d/%H%M%S")}.json',
        Body=json.dumps(metrics)
    )
```


#### Forecasting Model

**Purpose**: Predecir necesidades futuras de capacidad basado en tendencias

**Approach**: Usar CloudWatch Anomaly Detection + custom ML model

```python
import pandas as pd
from statsmodels.tsa.holtwinters import ExponentialSmoothing

def forecast_capacity(metric_name, days_ahead=30):
    """Forecast resource needs using time series analysis"""
    
    # Get historical data (last 90 days)
    historical_data = get_cloudwatch_metric_history(
        metric_name=metric_name,
        days=90
    )
    
    # Convert to pandas series
    df = pd.DataFrame(historical_data)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df.set_index('timestamp', inplace=True)
    
    # Fit exponential smoothing model
    model = ExponentialSmoothing(
        df['value'],
        seasonal_periods=7,  # Weekly seasonality
        trend='add',
        seasonal='add'
    )
    fitted_model = model.fit()
    
    # Forecast
    forecast = fitted_model.forecast(steps=days_ahead)
    
    # Calculate confidence intervals
    confidence_interval = calculate_confidence_interval(forecast)
    
    return {
        'forecast': forecast.tolist(),
        'confidence_interval': confidence_interval,
        'current_capacity': get_current_capacity(metric_name),
        'recommended_capacity': calculate_recommended_capacity(forecast)
    }
```

**Scheduled Execution**: Weekly capacity planning report

#### Cost Projection

**Cost Modeling**:
```python
def project_costs(growth_scenario='moderate'):
    """Project costs based on growth scenarios"""
    
    # Get current costs
    current_costs = get_current_month_costs()
    
    # Growth scenarios
    growth_rates = {
        'conservative': 1.1,  # 10% growth
        'moderate': 1.3,      # 30% growth
        'aggressive': 1.5     # 50% growth
    }
    
    growth_rate = growth_rates[growth_scenario]
    
    # Project costs for next 12 months
    projections = []
    for month in range(1, 13):
        projected_cost = current_costs * (growth_rate ** (month / 12))
        projections.append({
            'month': month,
            'projected_cost': projected_cost,
            'scenario': growth_scenario
        })
    
    return projections
```

### 8. Integration with External Tools

#### ITSM Integration (ServiceNow/Jira)

**Incident Creation**:
```python
def create_itsm_incident(alert):
    """Create incident in corporate ITSM system"""
    
    incident_payload = {
        'short_description': alert['alarm_name'],
        'description': format_incident_description(alert),
        'urgency': map_severity_to_urgency(alert['severity']),
        'impact': alert['business_impact'],
        'category': 'Data Pipeline',
        'subcategory': determine_subcategory(alert),
        'assignment_group': 'Data Engineering',
        'caller_id': 'monitoring-system',
        'work_notes': alert['runbook']
    }
    
    response = requests.post(
        SERVICENOW_API_URL,
        json=incident_payload,
        auth=(SERVICENOW_USER, SERVICENOW_PASSWORD),
        headers={'Content-Type': 'application/json'}
    )
    
    if response.status_code == 201:
        incident_number = response.json()['result']['number']
        # Store incident number for tracking
        store_incident_mapping(alert['alarm_name'], incident_number)
    
    return response.status_code == 201
```


#### Metrics Export to Corporate Platforms

**Prometheus Export**:
```python
from prometheus_client import CollectorRegistry, Gauge, push_to_gateway

def export_to_prometheus():
    """Export CloudWatch metrics to Prometheus"""
    
    registry = CollectorRegistry()
    
    # Define gauges
    data_freshness = Gauge(
        'janis_data_freshness_minutes',
        'Time since last data update',
        ['entity_type'],
        registry=registry
    )
    
    pipeline_throughput = Gauge(
        'janis_pipeline_throughput',
        'Records processed per minute',
        ['stage'],
        registry=registry
    )
    
    # Get metrics from CloudWatch
    metrics = get_cloudwatch_metrics()
    
    # Set gauge values
    for entity_type, freshness in metrics['data_freshness'].items():
        data_freshness.labels(entity_type=entity_type).set(freshness)
    
    for stage, throughput in metrics['throughput'].items():
        pipeline_throughput.labels(stage=stage).set(throughput)
    
    # Push to Prometheus gateway
    push_to_gateway(
        PROMETHEUS_GATEWAY_URL,
        job='janis-cencosud-pipeline',
        registry=registry
    )
```

**Scheduled Export**: Every 1 minute via EventBridge

#### Webhook Notifications

**Generic Webhook Integration**:
```python
def send_webhook_notification(alert, webhook_url):
    """Send alert to external system via webhook"""
    
    payload = {
        'event_type': 'alert',
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'alert': {
            'name': alert['alarm_name'],
            'severity': alert['severity'],
            'description': alert['description'],
            'status': alert['current_state'],
            'dashboard_url': alert['dashboard_url'],
            'runbook_url': alert['runbook']
        },
        'metadata': {
            'source': 'janis-cencosud-monitoring',
            'environment': 'production'
        }
    }
    
    response = requests.post(
        webhook_url,
        json=payload,
        headers={'Content-Type': 'application/json'},
        timeout=10
    )
    
    return response.status_code == 200
```

#### SSO/SAML Authentication

**Dashboard Access Control**:
```hcl
# Cognito User Pool for SSO
resource "aws_cognito_user_pool" "dashboard_users" {
  name = "janis-cencosud-dashboard-users"
  
  # SAML identity provider
  schema {
    name                = "email"
    attribute_data_type = "String"
    required            = true
  }
}

resource "aws_cognito_identity_provider" "corporate_saml" {
  user_pool_id  = aws_cognito_user_pool.dashboard_users.id
  provider_name = "CorporateSAML"
  provider_type = "SAML"
  
  provider_details = {
    MetadataURL = var.corporate_saml_metadata_url
  }
  
  attribute_mapping = {
    email = "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/emailaddress"
  }
}
```

**API Gateway Authorization**:
- Cognito authorizer para dashboard API
- Role-based access control (RBAC)
- Audit logging de accesos


## Data Models

### Metric Data Model

```python
from dataclasses import dataclass
from typing import List, Dict, Optional
from datetime import datetime

@dataclass
class MetricDimension:
    """Dimension for metric filtering"""
    name: str
    value: str

@dataclass
class MetricDataPoint:
    """Single metric data point"""
    metric_name: str
    namespace: str
    value: float
    unit: str
    timestamp: datetime
    dimensions: List[MetricDimension]
    statistic: Optional[str] = None  # Average, Sum, Min, Max, p99, etc.

@dataclass
class Alarm:
    """CloudWatch alarm configuration"""
    alarm_name: str
    metric_name: str
    namespace: str
    comparison_operator: str  # GreaterThanThreshold, LessThanThreshold, etc.
    threshold: float
    evaluation_periods: int
    period: int  # seconds
    statistic: str
    dimensions: List[MetricDimension]
    alarm_actions: List[str]  # SNS topic ARNs
    alarm_description: str
    treat_missing_data: str = "notBreaching"
```

### Log Entry Data Model

```python
@dataclass
class LogEntry:
    """Structured log entry"""
    timestamp: datetime
    level: str  # ERROR, WARN, INFO, DEBUG
    component: str
    correlation_id: str
    message: str
    metadata: Dict[str, any]
    
    # Optional fields
    event_type: Optional[str] = None
    entity_id: Optional[str] = None
    duration_ms: Optional[int] = None
    status: Optional[str] = None
    error: Optional[Dict[str, str]] = None
    
    def to_json(self) -> str:
        """Convert to JSON for CloudWatch Logs"""
        return json.dumps({
            'timestamp': self.timestamp.isoformat(),
            'level': self.level,
            'component': self.component,
            'correlation_id': self.correlation_id,
            'message': self.message,
            'metadata': self.metadata,
            'event_type': self.event_type,
            'entity_id': self.entity_id,
            'duration_ms': self.duration_ms,
            'status': self.status,
            'error': self.error
        })
```

### Alert Data Model

```python
@dataclass
class Alert:
    """Enriched alert with context"""
    alert_id: str
    alarm_name: str
    severity: str  # CRITICAL, HIGH, MEDIUM, LOW
    current_state: str  # ALARM, OK, INSUFFICIENT_DATA
    previous_state: str
    state_change_time: datetime
    
    # Context
    description: str
    reason: str
    business_impact: str
    
    # Actionable information
    runbook: str
    suggested_actions: List[str]
    dashboard_url: str
    log_insights_url: str
    
    # Tracking
    acknowledged: bool = False
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None
    resolved: bool = False
    resolved_at: Optional[datetime] = None
    incident_number: Optional[str] = None
```


### Dashboard Configuration Model

```python
@dataclass
class DashboardWidget:
    """CloudWatch dashboard widget configuration"""
    widget_type: str  # metric, log, number, text
    title: str
    metrics: List[Dict[str, any]]
    properties: Dict[str, any]
    position: Dict[str, int]  # x, y, width, height

@dataclass
class Dashboard:
    """CloudWatch dashboard"""
    dashboard_name: str
    widgets: List[DashboardWidget]
    period_override: Optional[str] = None
    
    def to_cloudwatch_json(self) -> str:
        """Convert to CloudWatch dashboard JSON format"""
        return json.dumps({
            'widgets': [
                {
                    'type': w.widget_type,
                    'properties': {
                        'title': w.title,
                        'metrics': w.metrics,
                        **w.properties
                    },
                    **w.position
                }
                for w in self.widgets
            ]
        })
```

### Health Check Result Model

```python
@dataclass
class ComponentHealth:
    """Health status of a single component"""
    component_name: str
    status: str  # healthy, degraded, unhealthy
    last_check_time: datetime
    response_time_ms: Optional[int] = None
    error_message: Optional[str] = None
    details: Optional[Dict[str, any]] = None

@dataclass
class SystemHealth:
    """Overall system health"""
    timestamp: datetime
    overall_status: str  # healthy, degraded, unhealthy
    components: Dict[str, ComponentHealth]
    
    def calculate_health_score(self) -> float:
        """Calculate numeric health score (0-100)"""
        if not self.components:
            return 0.0
        
        status_scores = {
            'healthy': 100,
            'degraded': 50,
            'unhealthy': 0
        }
        
        total_score = sum(
            status_scores.get(c.status, 0)
            for c in self.components.values()
        )
        
        return total_score / len(self.components)
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Metric Emission Completeness

*For any* data pipeline execution, all critical metrics (ingestion count, transformation count, load count, error count) should be emitted to CloudWatch.

**Validates: Requirements 1.1, 2.1**

**Rationale**: Sin métricas completas, no podemos monitorear el pipeline efectivamente. Esta propiedad asegura que cada etapa del pipeline emite sus métricas.

### Property 2: Alarm Threshold Consistency

*For any* CloudWatch alarm configuration, the threshold value should be within valid bounds for the metric type and the evaluation period should be sufficient to avoid false positives.

**Validates: Requirements 1.2**

**Rationale**: Alarmas mal configuradas generan falsos positivos o fallan en detectar problemas reales.


### Property 3: Log Structure Validity

*For any* log entry emitted by the system, it should contain all required fields (timestamp, level, component, correlation_id, message) in the correct format.

**Validates: Requirements 8.2**

**Rationale**: Logs estructurados consistentemente permiten búsqueda, filtrado y análisis efectivos.

### Property 4: Alert Enrichment Completeness

*For any* alarm that transitions to ALARM state, the enriched alert should include runbook, dashboard URL, and suggested actions.

**Validates: Requirements 7.2**

**Rationale**: Alertas sin contexto no son accionables y retrasan la resolución de problemas.

### Property 5: Alert Routing Correctness

*For any* enriched alert, it should be routed to the correct SNS topic based on its severity level (Critical → critical topic, High → high topic, etc.).

**Validates: Requirements 7.1**

**Rationale**: Routing incorrecto puede enviar alertas críticas a canales de baja prioridad o viceversa.

### Property 6: Alert Suppression Effectiveness

*For any* alarm that fires multiple times within the suppression window (15 minutes), only the first occurrence should generate a notification.

**Validates: Requirements 7.3**

**Rationale**: Alertas duplicadas generan ruido y alert fatigue.

### Property 7: Data Freshness Accuracy

*For any* entity type (orders, products, inventory), the calculated data freshness metric should accurately reflect the time since the last successful data update in Redshift.

**Validates: Requirements 2.2**

**Rationale**: Métricas de freshness incorrectas pueden ocultar problemas de latencia en el pipeline.

### Property 8: Health Check Comprehensiveness

*For any* health check execution, it should verify the status of all critical components (API Gateway, Lambda, Kinesis, Glue, Redshift, external APIs).

**Validates: Requirements 9.1**

**Rationale**: Health checks incompletos no detectan todos los posibles puntos de fallo.

### Property 9: Synthetic Transaction End-to-End Validation

*For any* synthetic transaction, if it successfully reaches the webhook endpoint, the synthetic data should be verifiable in S3 within the expected time window.

**Validates: Requirements 9.2**

**Rationale**: Synthetic tests deben validar el flujo completo, no solo componentes individuales.

### Property 10: Audit Log Completeness

*For any* sensitive operation (data access, configuration change, authentication event), an audit log entry should be created in CloudTrail.

**Validates: Requirements 10.3**

**Rationale**: Audit trails incompletos comprometen compliance y dificultan investigaciones de seguridad.

### Property 11: Cost Metric Accuracy

*For any* cost calculation period, the sum of per-service costs should equal the total cost reported by AWS Cost Explorer (within rounding tolerance).

**Validates: Requirements 6.4**

**Rationale**: Métricas de costo incorrectas llevan a decisiones de optimización equivocadas.


### Property 12: Dashboard Widget Data Consistency

*For any* dashboard widget displaying a metric, the data shown should match the actual metric values in CloudWatch within the refresh interval.

**Validates: Requirements 6.1, 6.2, 6.3, 6.4**

**Rationale**: Dashboards con datos inconsistentes generan confusión y decisiones incorrectas.

## Error Handling

### Metric Emission Failures

**Scenario**: CloudWatch API call fails when emitting metrics

**Handling Strategy**:
1. **Retry with exponential backoff**: 3 attempts con delays de 1s, 2s, 4s
2. **Local buffering**: Si todos los retries fallan, buffer metrics localmente
3. **Batch emission**: Enviar metrics buffered en próxima ejecución exitosa
4. **Fallback logging**: Log metric values para recovery manual si es necesario

```python
def emit_metric_with_retry(metric_data, max_retries=3):
    """Emit metric with retry logic"""
    
    for attempt in range(max_retries):
        try:
            cloudwatch.put_metric_data(
                Namespace=metric_data['namespace'],
                MetricData=[metric_data]
            )
            return True
        except ClientError as e:
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
            else:
                # Buffer for later
                buffer_metric(metric_data)
                logger.error(f"Failed to emit metric after {max_retries} attempts: {e}")
                return False
```

### Alarm Action Failures

**Scenario**: SNS notification fails to deliver

**Handling Strategy**:
1. **SNS retry policy**: Configurar retry automático en SNS
2. **Dead Letter Queue**: Mensajes fallidos van a DLQ
3. **DLQ monitoring**: Alarma cuando DLQ tiene mensajes
4. **Manual intervention**: Proceso para reenviar mensajes desde DLQ

```hcl
resource "aws_sns_topic" "critical_alerts" {
  name = "janis-alerts-critical"
  
  # Delivery policy with retries
  delivery_policy = jsonencode({
    http = {
      defaultHealthyRetryPolicy = {
        minDelayTarget     = 20
        maxDelayTarget     = 20
        numRetries         = 3
        numMaxDelayRetries = 0
        numNoDelayRetries  = 0
        numMinDelayRetries = 0
        backoffFunction    = "linear"
      }
    }
  })
}

resource "aws_sqs_queue" "sns_dlq" {
  name = "janis-alerts-dlq"
  
  message_retention_seconds = 1209600  # 14 days
}
```

### Dashboard Rendering Failures

**Scenario**: Dashboard widget fails to load due to metric query error

**Handling Strategy**:
1. **Graceful degradation**: Mostrar mensaje de error en widget específico
2. **Partial rendering**: Otros widgets continúan funcionando
3. **Automatic retry**: Dashboard auto-refresh reintenta carga
4. **Fallback data**: Mostrar último valor conocido si disponible

### Log Ingestion Failures

**Scenario**: CloudWatch Logs API throttling o failures

**Handling Strategy**:
1. **Local buffering**: Buffer logs en memoria/disco
2. **Batch upload**: Enviar logs en batches para reducir API calls
3. **Priority queuing**: Logs de ERROR/WARN tienen prioridad sobre INFO/DEBUG
4. **Graceful degradation**: Continuar operación aunque logging falle

```python
class BufferedLogger:
    """Logger with local buffering for resilience"""
    
    def __init__(self, log_group, log_stream, buffer_size=100):
        self.log_group = log_group
        self.log_stream = log_stream
        self.buffer = []
        self.buffer_size = buffer_size
        self.logs_client = boto3.client('logs')
    
    def log(self, log_entry):
        """Add log entry to buffer"""
        self.buffer.append(log_entry)
        
        if len(self.buffer) >= self.buffer_size:
            self.flush()
    
    def flush(self):
        """Flush buffer to CloudWatch Logs"""
        if not self.buffer:
            return
        
        try:
            self.logs_client.put_log_events(
                logGroupName=self.log_group,
                logStreamName=self.log_stream,
                logEvents=[
                    {
                        'timestamp': int(entry.timestamp.timestamp() * 1000),
                        'message': entry.to_json()
                    }
                    for entry in self.buffer
                ]
            )
            self.buffer.clear()
        except Exception as e:
            # Keep buffer for next attempt
            logger.error(f"Failed to flush logs: {e}")
```


### Health Check Failures

**Scenario**: Health check Lambda times out or fails

**Handling Strategy**:
1. **Timeout protection**: Set appropriate Lambda timeout (30s)
2. **Partial results**: Return health status for components checked before timeout
3. **Degraded state**: Mark overall health as "degraded" if check fails
4. **Alert on check failures**: Separate alarm for health check failures

### External Integration Failures

**Scenario**: ITSM API or webhook endpoint unavailable

**Handling Strategy**:
1. **Circuit breaker**: Prevent cascading failures
2. **Retry queue**: Queue failed notifications for retry
3. **Fallback channels**: Use alternative notification method
4. **Manual escalation**: Alert ops team if integration down

```python
def send_notification_with_fallback(alert):
    """Send notification with fallback channels"""
    
    # Try primary channel (ITSM)
    try:
        if create_itsm_incident(alert):
            return True
    except Exception as e:
        logger.error(f"ITSM integration failed: {e}")
    
    # Fallback to email
    try:
        send_email_notification(alert)
        return True
    except Exception as e:
        logger.error(f"Email notification failed: {e}")
    
    # Last resort: write to S3 for manual processing
    try:
        s3.put_object(
            Bucket='janis-cencosud-failed-notifications',
            Key=f'alerts/{datetime.now().isoformat()}-{alert["alert_id"]}.json',
            Body=json.dumps(alert)
        )
    except Exception as e:
        logger.error(f"Failed to write alert to S3: {e}")
    
    return False
```

## Testing Strategy

### Unit Testing

**Metric Emission Tests**:
- Test metric data structure validation
- Test dimension formatting
- Test unit conversion
- Test namespace validation
- Mock CloudWatch client para evitar llamadas reales

**Alarm Configuration Tests**:
- Test threshold validation
- Test comparison operator logic
- Test evaluation period calculations
- Test alarm action configuration

**Log Formatting Tests**:
- Test structured log JSON generation
- Test timestamp formatting (ISO 8601)
- Test log level validation
- Test correlation ID generation

**Alert Enrichment Tests**:
- Test runbook lookup logic
- Test dashboard URL generation
- Test severity determination
- Test business impact assessment

### Property-Based Testing

**Framework**: Use `hypothesis` library for Python

**Configuration**: Minimum 100 iterations per property test

**Property Test Examples**:

```python
from hypothesis import given, strategies as st
import pytest

@given(
    metric_name=st.text(min_size=1, max_size=255),
    value=st.floats(min_value=0, allow_nan=False, allow_infinity=False),
    dimensions=st.lists(
        st.tuples(st.text(min_size=1), st.text(min_size=1)),
        max_size=10
    )
)
def test_metric_emission_completeness(metric_name, value, dimensions):
    """
    Property 1: Metric Emission Completeness
    Feature: monitoring-alerting, Property 1
    """
    metric_data = create_metric_data(metric_name, value, dimensions)
    
    # Verify all required fields present
    assert 'MetricName' in metric_data
    assert 'Value' in metric_data
    assert 'Timestamp' in metric_data
    assert 'Dimensions' in metric_data
    
    # Verify values are valid
    assert metric_data['MetricName'] == metric_name
    assert metric_data['Value'] == value
    assert len(metric_data['Dimensions']) == len(dimensions)
```


```python
@given(
    alarm_name=st.text(min_size=1, max_size=255),
    threshold=st.floats(min_value=0, max_value=100, allow_nan=False),
    evaluation_periods=st.integers(min_value=1, max_value=10)
)
def test_alarm_threshold_consistency(alarm_name, threshold, evaluation_periods):
    """
    Property 2: Alarm Threshold Consistency
    Feature: monitoring-alerting, Property 2
    """
    alarm_config = create_alarm_config(
        alarm_name=alarm_name,
        threshold=threshold,
        evaluation_periods=evaluation_periods
    )
    
    # Verify threshold is within valid bounds
    assert 0 <= alarm_config['threshold'] <= 100
    
    # Verify evaluation period is sufficient (at least 2 for stability)
    assert alarm_config['evaluation_periods'] >= 1
    
    # Verify period * evaluation_periods gives reasonable time window
    total_window = alarm_config['period'] * alarm_config['evaluation_periods']
    assert total_window >= 60  # At least 1 minute

@given(
    level=st.sampled_from(['ERROR', 'WARN', 'INFO', 'DEBUG']),
    component=st.text(min_size=1, max_size=100),
    message=st.text(min_size=1, max_size=1000)
)
def test_log_structure_validity(level, component, message):
    """
    Property 3: Log Structure Validity
    Feature: monitoring-alerting, Property 3
    """
    log_entry = create_log_entry(
        level=level,
        component=component,
        message=message
    )
    
    # Verify all required fields present
    assert 'timestamp' in log_entry
    assert 'level' in log_entry
    assert 'component' in log_entry
    assert 'correlation_id' in log_entry
    assert 'message' in log_entry
    
    # Verify timestamp is ISO 8601 format
    datetime.fromisoformat(log_entry['timestamp'].replace('Z', '+00:00'))
    
    # Verify level is valid
    assert log_entry['level'] in ['ERROR', 'WARN', 'INFO', 'DEBUG']

@given(
    alarm_name=st.text(min_size=1, max_size=255),
    severity=st.sampled_from(['CRITICAL', 'HIGH', 'MEDIUM', 'LOW'])
)
def test_alert_enrichment_completeness(alarm_name, severity):
    """
    Property 4: Alert Enrichment Completeness
    Feature: monitoring-alerting, Property 4
    """
    alarm_event = create_alarm_event(alarm_name, 'ALARM')
    enriched_alert = enrich_alert(alarm_event)
    
    # Verify enrichment fields present
    assert 'runbook' in enriched_alert
    assert 'dashboard_url' in enriched_alert
    assert 'suggested_actions' in enriched_alert
    assert 'log_insights_url' in enriched_alert
    
    # Verify runbook is not empty
    assert len(enriched_alert['runbook']) > 0
    
    # Verify suggested actions is a list
    assert isinstance(enriched_alert['suggested_actions'], list)
    assert len(enriched_alert['suggested_actions']) > 0

@given(
    severity=st.sampled_from(['CRITICAL', 'HIGH', 'MEDIUM', 'LOW'])
)
def test_alert_routing_correctness(severity):
    """
    Property 5: Alert Routing Correctness
    Feature: monitoring-alerting, Property 5
    """
    alert = create_alert(severity=severity)
    target_topic = route_alert(alert)
    
    # Verify routing matches severity
    expected_topics = {
        'CRITICAL': 'janis-alerts-critical-prod',
        'HIGH': 'janis-alerts-high-prod',
        'MEDIUM': 'janis-alerts-medium-prod',
        'LOW': 'janis-alerts-low-prod'
    }
    
    assert target_topic == expected_topics[severity]
```


```python
@given(
    alarm_name=st.text(min_size=1, max_size=255),
    fire_times=st.lists(
        st.datetimes(
            min_value=datetime(2026, 1, 1),
            max_value=datetime(2026, 12, 31)
        ),
        min_size=2,
        max_size=10
    )
)
def test_alert_suppression_effectiveness(alarm_name, fire_times):
    """
    Property 6: Alert Suppression Effectiveness
    Feature: monitoring-alerting, Property 6
    """
    # Sort fire times
    fire_times.sort()
    
    notifications_sent = []
    
    for fire_time in fire_times:
        should_notify = not should_suppress_alert(alarm_name, fire_time)
        if should_notify:
            notifications_sent.append(fire_time)
    
    # Verify no two notifications within 15 minutes
    for i in range(len(notifications_sent) - 1):
        time_diff = (notifications_sent[i + 1] - notifications_sent[i]).total_seconds()
        assert time_diff >= 900  # 15 minutes

@given(
    entity_type=st.sampled_from(['orders', 'products', 'inventory']),
    last_update_time=st.datetimes(
        min_value=datetime(2026, 1, 1),
        max_value=datetime(2026, 12, 31)
    )
)
def test_data_freshness_accuracy(entity_type, last_update_time):
    """
    Property 7: Data Freshness Accuracy
    Feature: monitoring-alerting, Property 7
    """
    # Mock Redshift last update time
    mock_redshift_update_time(entity_type, last_update_time)
    
    # Calculate freshness
    current_time = datetime.now(timezone.utc)
    calculated_freshness = calculate_data_freshness(entity_type)
    
    # Expected freshness
    expected_freshness = (current_time - last_update_time).total_seconds() / 60
    
    # Verify accuracy (within 1 minute tolerance)
    assert abs(calculated_freshness - expected_freshness) < 1.0

@given(
    components=st.lists(
        st.sampled_from([
            'api_gateway', 'lambda', 'kinesis', 'glue', 'redshift', 'janis_api'
        ]),
        min_size=1,
        unique=True
    )
)
def test_health_check_comprehensiveness(components):
    """
    Property 8: Health Check Comprehensiveness
    Feature: monitoring-alerting, Property 8
    """
    health_result = perform_health_check()
    
    # Verify all critical components are checked
    critical_components = [
        'api_gateway', 'lambda', 'kinesis', 'glue', 'redshift', 'janis_api'
    ]
    
    for component in critical_components:
        assert component in health_result['components']
        assert 'status' in health_result['components'][component]
        assert health_result['components'][component]['status'] in [
            'healthy', 'degraded', 'unhealthy'
        ]
```

### Integration Testing

**End-to-End Monitoring Flow**:
1. Emit test metric → Verify in CloudWatch
2. Trigger alarm → Verify SNS notification
3. Enrich alert → Verify enrichment fields
4. Route alert → Verify correct topic
5. Deliver notification → Verify in target channel

**Dashboard Testing**:
1. Create test metrics
2. Render dashboard
3. Verify widget data matches metrics
4. Test auto-refresh functionality

**Health Check Testing**:
1. Mock component responses
2. Execute health check
3. Verify all components checked
4. Verify overall status calculation

**Synthetic Transaction Testing**:
1. Send synthetic webhook
2. Verify processing through pipeline
3. Verify data in S3
4. Verify metrics emitted


### Load Testing

**Metric Emission Load Test**:
- Emit 1000 metrics/second
- Verify no throttling
- Verify all metrics received
- Measure latency

**Alert Processing Load Test**:
- Trigger 100 alarms simultaneously
- Verify all alerts enriched
- Verify all notifications sent
- Measure processing time

**Dashboard Performance Test**:
- Load dashboard with 50+ widgets
- Measure render time
- Verify responsiveness
- Test with high metric cardinality

## Design Decisions and Rationale

### Decision 1: CloudWatch vs Third-Party Monitoring

**Decision**: Use AWS CloudWatch as primary monitoring platform

**Rationale**:
- **Native integration**: Seamless integration con servicios AWS
- **Cost-effective**: No additional infrastructure costs
- **Unified platform**: Metrics, logs, alarms en un solo lugar
- **Scalability**: Escala automáticamente con carga
- **Compliance**: Cumple requisitos de seguridad corporativa

**Trade-offs**:
- Vendor lock-in con AWS
- Menos features avanzados que Datadog/New Relic
- Dashboards menos flexibles que Grafana

**Mitigation**: Exportar métricas a Prometheus para portabilidad futura

### Decision 2: Tiered Alerting with SNS

**Decision**: Implementar 4 niveles de severidad con SNS topics separados

**Rationale**:
- **Reduce alert fatigue**: Diferentes canales para diferentes severidades
- **Appropriate response time**: Critical alerts llegan inmediatamente
- **Cost optimization**: Low priority alerts en digest diario
- **Flexibility**: Fácil agregar/modificar canales por severidad

**Trade-offs**:
- Más complejidad en configuración
- Múltiples SNS topics para mantener

**Mitigation**: Terraform modules para configuración consistente

### Decision 3: Alert Enrichment Lambda

**Decision**: Usar Lambda para enriquecer alertas antes de notificar

**Rationale**:
- **Actionable alerts**: Incluir runbooks y contexto
- **Reduce MTTR**: Información necesaria disponible inmediatamente
- **Centralized logic**: Un lugar para lógica de enrichment
- **Flexible routing**: Puede enrutar basado en contexto adicional

**Trade-offs**:
- Latencia adicional en alerting
- Punto de fallo adicional

**Mitigation**: Lambda con retry logic y fallback directo a SNS

### Decision 4: Structured Logging with JSON

**Decision**: Usar JSON para todos los logs con formato consistente

**Rationale**:
- **Searchability**: CloudWatch Logs Insights puede parsear JSON
- **Consistency**: Mismo formato en todos los componentes
- **Correlation**: correlation_id permite tracing distribuido
- **Automation**: Fácil parsear para alertas y métricas

**Trade-offs**:
- Más verbose que logs de texto plano
- Requiere disciplina en desarrollo

**Mitigation**: Librerías compartidas para logging consistente


### Decision 5: Custom Metrics for Business KPIs

**Decision**: Emitir custom metrics para KPIs de negocio además de métricas técnicas

**Rationale**:
- **Business visibility**: Stakeholders pueden ver impacto de negocio
- **Anomaly detection**: Detectar problemas de datos vía business metrics
- **Correlation**: Relacionar problemas técnicos con impacto de negocio
- **Proactive monitoring**: Detectar anomalías antes de que usuarios reporten

**Trade-offs**:
- Costo adicional de custom metrics
- Complejidad en cálculo de métricas

**Mitigation**: Limitar a KPIs críticos, usar metric math para derivadas

### Decision 6: Separate Dashboards by Audience

**Decision**: Crear dashboards específicos para diferentes roles (Executive, Operations, Data Quality, Cost)

**Rationale**:
- **Relevant information**: Cada rol ve lo que necesita
- **Reduced complexity**: Dashboards más simples y enfocados
- **Better UX**: Información presentada apropiadamente para audiencia
- **Access control**: Puede restringir acceso por rol

**Trade-offs**:
- Múltiples dashboards para mantener
- Posible duplicación de widgets

**Mitigation**: Terraform modules para widgets reutilizables

### Decision 7: Health Checks with Synthetic Transactions

**Decision**: Implementar synthetic transactions además de health checks pasivos

**Rationale**:
- **Proactive detection**: Detectar problemas antes de que afecten usuarios
- **End-to-end validation**: Verifica flujo completo, no solo componentes
- **SLA monitoring**: Medir disponibilidad real del servicio
- **External dependency monitoring**: Detectar problemas con APIs externas

**Trade-offs**:
- Costo de ejecución de synthetic tests
- Puede generar datos de prueba en sistema

**Mitigation**: Marcar datos synthetic claramente, cleanup automático

### Decision 8: CloudTrail for Audit Logging

**Decision**: Usar CloudTrail para audit logging en lugar de custom solution

**Rationale**:
- **Comprehensive coverage**: Captura todas las API calls automáticamente
- **Compliance ready**: Cumple requisitos de auditoría
- **Tamper-proof**: Log file validation previene modificación
- **Long-term retention**: S3 storage para 7 años

**Trade-offs**:
- Costo de almacenamiento de logs
- Volumen alto de logs

**Mitigation**: Lifecycle policies para transicionar a Glacier

### Decision 9: Anomaly Detection for Data Volume

**Decision**: Usar CloudWatch Anomaly Detection para detectar anomalías en volumen de datos

**Rationale**:
- **Automatic baseline**: No necesita configuración manual de thresholds
- **Adapts to patterns**: Se ajusta a patrones estacionales
- **Reduces false positives**: Más inteligente que thresholds estáticos
- **Easy to implement**: Feature nativo de CloudWatch

**Trade-offs**:
- Requiere período de training (2 semanas)
- Menos control sobre sensibilidad

**Mitigation**: Combinar con thresholds estáticos para casos críticos

### Decision 10: Local Buffering for Resilience

**Decision**: Implementar buffering local en Lambda para métricas y logs

**Rationale**:
- **Resilience**: Continuar operación aunque CloudWatch no disponible
- **Batch efficiency**: Reducir API calls agrupando
- **Cost optimization**: Menos API calls = menor costo
- **Data preservation**: No perder datos durante outages

**Trade-offs**:
- Complejidad adicional en código
- Uso de memoria en Lambda

**Mitigation**: Límites de buffer size, flush periódico

## Implementation Notes

### Terraform Module Structure

```
terraform/modules/monitoring/
├── main.tf                    # Main resources
├── alarms.tf                  # CloudWatch alarms
├── dashboards.tf              # Dashboard configurations
├── sns.tf                     # SNS topics and subscriptions
├── lambda.tf                  # Alert enrichment Lambda
├── eventbridge.tf             # Health check scheduling
├── cloudtrail.tf              # Audit logging
├── variables.tf               # Input variables
├── outputs.tf                 # Output values
└── README.md                  # Module documentation
```

### Lambda Function Structure

```
lambda/
├── alert-enrichment/
│   ├── handler.py             # Main handler
│   ├── enrichment.py          # Enrichment logic
│   ├── routing.py             # Alert routing
│   ├── runbooks.py            # Runbook lookup
│   └── requirements.txt
├── health-check/
│   ├── handler.py
│   ├── checks.py              # Component checks
│   ├── synthetic.py           # Synthetic transactions
│   └── requirements.txt
└── shared/
    ├── logging.py             # Structured logging
    ├── metrics.py             # Metric emission
    └── models.py              # Data models
```

### Deployment Order

1. **CloudWatch Log Groups**: Crear primero para recibir logs
2. **SNS Topics**: Necesarios para alarm actions
3. **CloudWatch Alarms**: Configurar alarmas
4. **Lambda Functions**: Deploy enrichment y health check
5. **EventBridge Rules**: Schedule health checks
6. **Dashboards**: Crear dashboards
7. **CloudTrail**: Habilitar audit logging
8. **Testing**: Ejecutar synthetic tests

### Monitoring the Monitoring System

**Meta-monitoring**: El sistema de monitoreo debe monitorearse a sí mismo

**Key Metrics**:
- Alert enrichment Lambda errors
- Health check execution failures
- SNS delivery failures
- CloudWatch API throttling
- Dashboard load times

**Alerts**:
- Critical: Monitoring system down
- High: Partial monitoring failure
- Medium: Performance degradation

This ensures we detect problems with the monitoring system itself before they impact our ability to monitor the data pipeline.
