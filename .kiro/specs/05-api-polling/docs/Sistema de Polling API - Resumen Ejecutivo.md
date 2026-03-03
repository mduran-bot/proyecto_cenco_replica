# Sistema de Polling API - Resumen Ejecutivo

## Fecha de Actualización
15 de Enero, 2026

## Propósito

El Sistema de Polling API implementa una arquitectura event-driven que utiliza Amazon EventBridge para gatillar flujos de trabajo de Apache Airflow (MWAA) de manera programada. Este sistema actúa como red de seguridad complementaria a los webhooks, garantizando que no se pierda información crítica de las APIs de Janis.

## Arquitectura de Alto Nivel

### Componentes Principales

1. **Amazon EventBridge**: Scheduler inteligente que gatilla ejecuciones de DAGs según intervalos programados
2. **Amazon MWAA (Apache Airflow)**: Motor de orquestación que ejecuta workflows bajo demanda
3. **DynamoDB Control Table**: Mantiene estado de última ejecución exitosa para polling incremental
4. **AWS Systems Manager Parameter Store**: Configuración centralizada del sistema
5. **Amazon Kinesis Firehose**: Destino de datos polleados (mismo que webhooks)

### Flujo de Datos

```
EventBridge (Schedule) → MWAA DAG → Janis API → Validación → Kinesis Firehose → S3 Bronze Layer
                            ↓
                    Control Table (DynamoDB)
```

## Frecuencias de Polling

| Tipo de Dato | Frecuencia | DAG |
|--------------|-----------|-----|
| Orders | 5 minutos | dag_poll_orders |
| Products | 1 hora | dag_poll_products |
| Stock | 10 minutos | dag_poll_stock |
| Prices | 30 minutos | dag_poll_prices |
| Stores | 24 horas | dag_poll_stores |

## Ventajas de la Arquitectura EventBridge + MWAA

### Reducción de Overhead
- **Antes**: MWAA mantiene workers activos constantemente para evaluar schedules
- **Ahora**: MWAA opera en modo "on-demand", iniciando workers solo cuando EventBridge gatilla trabajo real

### Optimización de Costos
- Workers de MWAA se escalan de 1 a 3 según demanda
- No hay overhead de scheduling continuo
- Recursos se utilizan solo cuando hay trabajo que ejecutar

### Escalabilidad
- EventBridge maneja millones de eventos sin overhead
- MWAA se enfoca exclusivamente en ejecución de tareas
- Separación clara de responsabilidades

## Características Clave

### 1. Polling Incremental
- Consulta solo datos nuevos o modificados desde última ejecución
- Overlap de 1 minuto para prevenir pérdida de datos
- Control de estado en DynamoDB

### 2. Manejo de Concurrencia
- Mecanismo de locks en Control Table
- Previene ejecuciones simultáneas del mismo tipo de polling
- Graceful exit si lock está activo

### 3. Rate Limiting
- Máximo 100 requests por minuto a APIs de Janis
- Sliding window rate limiter
- Retry con exponential backoff (1s, 2s, 4s)

### 4. Paginación Inteligente
- Procesamiento streaming de páginas
- Circuit breaker (máximo 1000 páginas)
- Minimiza uso de memoria

### 5. Enriquecimiento de Datos
- Fetch paralelo de entidades relacionadas (order items, SKUs)
- ThreadPoolExecutor con 5 workers
- Respeta rate limits globales

### 6. Validación de Calidad
- Validación contra JSON schemas
- Detección de duplicados
- Métricas de calidad de datos

### 7. Entrega Confiable
- Batching eficiente (500 records por batch)
- Retry logic para fallos de entrega
- Dead Letter Queue para fallos persistentes

## Plan de Implementación

El plan de implementación se encuentra detallado en `.kiro/specs/api-polling/tasks.md` y consta de 28 tareas principales organizadas en las siguientes fases:

### Fase 1: Infraestructura Base (Tasks 1-7)
- Setup de estructura de proyecto
- Terraform para DynamoDB Control Table
- Terraform para EventBridge scheduling
- Terraform para MWAA environment
- Configuración de Systems Manager y Secrets Manager
- **Checkpoint de validación**

### Fase 2: Plugins Python (Tasks 8-15)
- ConfigManager para gestión de configuración
- JanisAPIClient con rate limiting
- Pagination handler con circuit breaker
- DataEnrichmentEngine para fetch paralelo
- DataValidationEngine con JSON schemas
- ControlTableManager para estado incremental
- FirehoseDeliveryManager para entrega confiable
- **Checkpoint de validación**

### Fase 3: DAGs de Airflow (Tasks 16-21)
- DAG para polling de orders (con enrichment)
- DAG para polling de products (con SKU fetch)
- DAG para polling de stock
- DAG para polling de prices
- DAG para polling de stores
- requirements.txt para MWAA

### Fase 4: Monitoreo y Operaciones (Tasks 22-24)
- CloudWatch alarms y métricas custom
- Error handling comprehensivo
- Optimizaciones de performance

### Fase 5: Deployment y Documentación (Tasks 25-28)
- Scripts de deployment
- JSON schemas para validación
- Testing end-to-end
- Runbooks operacionales

## Monitoreo y Alertas

### Métricas Clave
- **DAGExecutionDuration**: Duración de ejecución de DAGs
- **DAGExecutionSuccess**: Tasa de éxito de DAGs
- **RecordsRetrieved**: Cantidad de registros obtenidos
- **APIResponseTime**: Tiempo de respuesta de APIs
- **APIErrorRate**: Tasa de errores de API
- **DataQualityScore**: Score de calidad de datos
- **FirehoseDeliverySuccess**: Tasa de éxito de entrega
- **EventBridgeTriggerLatency**: Latencia de trigger de EventBridge

### Alarmas Críticas
- Fallo de ejecución de DAG
- Tasa de error de API > 10%
- Anomalías de volumen de datos > 50%
- Tiempo de ejecución excedido
- Fallo de reglas de EventBridge
- Delay de trigger de EventBridge > 5 minutos

### Notificaciones
- **Críticas** (Inmediatas): Fallos de DAG, errores de autenticación, fallos de EventBridge
- **Warnings** (Cada hora): Tasa de error alta, anomalías de volumen, delays de ejecución
- **Info** (Diario): Resumen de ejecuciones, tendencias de calidad, métricas de performance

## Seguridad

### Network Security
- MWAA desplegado en subnets privadas
- VPC endpoints para servicios AWS
- Security groups restrictivos

### Data Security
- Cifrado en reposo (DynamoDB, S3, CloudWatch Logs)
- Cifrado en tránsito (TLS 1.2+)
- Credenciales en AWS Secrets Manager

### Access Control
- IAM roles con principio de menor privilegio
- Separación de roles por servicio
- No wildcard permissions en producción

## Performance SLA

| Tipo de Polling | Target | Volumen Máximo |
|-----------------|--------|----------------|
| Orders | 4 minutos | 10,000 records |
| Products | 10 minutos | 5,000 products |
| Stock | 3 minutos | 20,000 records |
| Prices | 5 minutos | 15,000 records |
| Stores | 2 minutos | 500 stores |

## Configuración por Ambiente

### Development
- API base URL: https://api-dev.janis.com
- Rate limit: 50 requests/min
- Frecuencias reducidas (orders cada 15 min)

### Production
- API base URL: https://api.janis.com
- Rate limit: 100 requests/min
- Frecuencias completas según tabla

## Operaciones y Mantenimiento

### Procedimientos Operacionales

1. **Manual DAG Rerun**
   ```bash
   aws mwaa create-cli-token --name cencosud-mwaa-environment
   # Usar token en Airflow UI para trigger manual
   ```

2. **Reset Control Table**
   - Útil para recovery o replay de datos
   - Actualiza timestamp de última ejecución

3. **Disable/Enable EventBridge Rules**
   ```bash
   aws events disable-rule --name poll-orders-rule
   aws events enable-rule --name poll-orders-rule
   ```

4. **Data Replay**
   - Eliminar entrada en Control Table para full refresh
   - O ajustar timestamp para replay desde fecha específica

### Troubleshooting Común

- **Lock conflicts**: Verificar ejecuciones en progreso, liberar locks manualmente si necesario
- **API rate limiting**: Revisar configuración de rate limit, ajustar si necesario
- **Data quality issues**: Revisar logs de validación, actualizar schemas si API cambió
- **Firehose delivery failures**: Verificar permisos IAM, revisar DLQ

## Próximos Pasos

1. **Implementación Fase 1**: Desplegar infraestructura base (Tasks 1-7)
2. **Desarrollo Plugins**: Implementar componentes Python reutilizables (Tasks 8-15)
3. **Desarrollo DAGs**: Crear workflows de Airflow (Tasks 16-21)
4. **Testing**: Validación end-to-end en ambiente dev
5. **Deployment Producción**: Rollout gradual con monitoreo intensivo

## Referencias

- **Especificación Completa**: `.kiro/specs/api-polling/design.md`
- **Requerimientos**: `.kiro/specs/api-polling/requirements.md`
- **Plan de Implementación**: `.kiro/specs/api-polling/tasks.md`
- **Arquitectura General**: `Documento Detallado de Diseño Janis-Cenco.md`

## Contacto

Para preguntas o soporte relacionado con el Sistema de Polling API, contactar al equipo de Data Engineering.
