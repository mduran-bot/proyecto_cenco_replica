# API Polling System - Requirements Update

**Fecha:** 23 de Febrero de 2026  
**Spec:** `.kiro/specs/api-polling-system/`  
**Estado:** Requirements document completado

## Resumen Ejecutivo

Se ha completado el documento de requerimientos para el **Sistema de Polling de APIs**, que implementa una solución de ingesta programada que consulta periódicamente las APIs de Janis para recuperar datos operacionales. El sistema utiliza Amazon EventBridge para scheduling inteligente y Amazon MWAA (Apache Airflow) para orquestación de workflows.

## Componentes Principales

### 1. EventBridge Scheduling
- **Órdenes**: Cada 5 minutos
- **Productos**: Cada 1 hora
- **Stock**: Cada 10 minutos
- **Precios**: Cada 30 minutos
- **Tiendas**: Cada 24 horas

### 2. MWAA (Apache Airflow)
- **Versión**: 2.7.2
- **Python**: 3.11
- **Ejecución**: Event-driven (schedule_interval=None)
- **Workers**: 1-3 (auto-scaling)

### 3. DynamoDB Control Table
- **Propósito**: Gestión de estado y locks
- **Funcionalidad**: Prevención de ejecuciones concurrentes
- **Polling incremental**: Tracking de last_successful_execution

### 4. Kinesis Firehose
- **Propósito**: Entrega de datos validados al Data Lake
- **Batch size**: 500 registros
- **Retry logic**: Hasta 3 intentos para fallos parciales

## Requerimientos Clave

### Requirement 1: EventBridge Scheduling Configuration
- 5 reglas programadas para diferentes tipos de datos
- Intervalos específicos por tipo de dato
- Invocación de DAGs de MWAA vía API
- Compatibilidad con LocalStack

### Requirement 2: MWAA Environment Configuration
- Airflow 2.7.2 con Python 3.11
- Ejecución event-driven (sin scheduling interno)
- Auto-scaling de 1-3 workers
- Roles IAM para DynamoDB, Kinesis y CloudWatch

### Requirement 3: DynamoDB State Management
- Lock acquisition con conditional updates
- Prevención de ejecuciones concurrentes
- Tracking de timestamps para polling incremental
- Liberación de locks en éxito y fallo

### Requirement 4: Incremental Polling Logic
- Filtro dateModified basado en last_successful_execution
- Ventana de solapamiento de 1 minuto
- Full refresh cuando no existe ejecución previa
- Deduplicación de registros en ventana de solapamiento

### Requirement 5: API Client with Rate Limiting
- Máximo 100 requests por minuto
- Retry con backoff exponencial (2, 4, 8 segundos)
- Manejo diferenciado de errores HTTP (429, 4xx, 5xx)
- Timeout de 30 segundos por request

### Requirement 6: Pagination Handling
- Tamaño de página: 100 registros
- Circuit breaker: Máximo 1000 páginas
- Tracking de progreso de paginación
- Alertas cuando se excede el límite

### Requirement 7: Data Enrichment
- Enriquecimiento de órdenes con items
- Enriquecimiento de productos con SKUs
- Paralelización con ThreadPoolExecutor (5 workers)
- Manejo resiliente de fallos de enriquecimiento

### Requirement 8: Data Validation
- Validación contra esquemas JSON predefinidos
- Detección de duplicados en lote
- Validación de reglas de negocio
- Métricas de calidad de datos
- Alertas cuando validation pass rate < 95%

### Requirement 9: Kinesis Firehose Delivery
- Batching de 500 registros
- Metadata de polling agregada
- Retry de fallos parciales (hasta 3 intentos)
- Logging de fallos de entrega

### Requirement 10: LocalStack Compatibility
- Variable LOCALSTACK_ENDPOINT para testing local
- Configuración de clientes AWS para LocalStack
- Docker-compose para setup de LocalStack
- Scripts de prueba contra LocalStack

### Requirement 11: Error Handling and Recovery
- Logging detallado con stack traces
- Notificaciones SNS en fallos de DAG
- Operaciones idempotentes para reintentos seguros
- Salida graciosa cuando no se puede adquirir lock
- Retry con backoff exponencial para APIs inalcanzables

### Requirement 12: Monitoring and Observability
- Métricas CloudWatch: records fetched, validation failures, API errors
- Dashboard de salud de polling por tipo de dato
- Alarmas cuando validation pass rate < 95%
- Alarmas cuando DAG falla
- Correlation IDs en logs para trazabilidad

## Flujo de Ejecución

```
EventBridge Rule (schedule)
    ↓
MWAA DAG Trigger
    ↓
Acquire Lock (DynamoDB)
    ↓
Build Incremental Filter (last_successful_execution - 1 min)
    ↓
Poll Janis API (with rate limiting & pagination)
    ↓
Validate Data (schema + business rules)
    ↓
Enrich Data (parallel fetch of related entities)
    ↓
Batch to Kinesis Firehose (500 records)
    ↓
Update State & Release Lock (DynamoDB)
    ↓
Emit Metrics (CloudWatch)
```

## Arquitectura de Datos

### DynamoDB Control Table Schema
```json
{
  "data_type": "orders",
  "lock_acquired": true,
  "lock_timestamp": "2024-01-15T10:30:00Z",
  "execution_id": "uuid-1234",
  "last_successful_execution": "2024-01-15T10:25:00Z",
  "last_modified_date": "2024-01-15T10:24:00Z",
  "status": "running",
  "records_fetched": 0,
  "error_message": null
}
```

### Output Record Format
```json
{
  "_metadata": {
    "execution_id": "uuid-1234",
    "poll_timestamp": "2024-01-15T10:30:00Z",
    "data_type": "orders",
    "enrichment_complete": true
  },
  "id": "order-123",
  "dateModified": "2024-01-15T10:25:00Z",
  "status": "pending",
  "items": [...]
}
```

## Diferencias Clave vs Webhook Ingestion

| Aspecto | Webhook Ingestion | API Polling |
|---------|-------------------|-------------|
| **Trigger** | Eventos en tiempo real | Programado (EventBridge) |
| **Latencia** | Segundos | Minutos (según schedule) |
| **Completitud** | Depende de webhooks | Garantizada (full refresh) |
| **Carga API** | Baja (solo cambios) | Media (polling periódico) |
| **Resiliencia** | Requiere retry logic | Polling incremental con ventana |
| **Uso** | Datos críticos en tiempo real | Red de seguridad + datos históricos |

## Compatibilidad con LocalStack

El sistema está diseñado para ser completamente testeable en LocalStack:

- ✅ EventBridge rules y targets
- ✅ DynamoDB table con conditional updates
- ✅ Kinesis Firehose delivery streams
- ✅ S3 buckets para staging
- ✅ CloudWatch logs y métricas
- ✅ SNS topics para notificaciones

**Configuración**: Variable `LOCALSTACK_ENDPOINT=http://localhost:4566`

## Próximos Pasos

### Fase 1: Diseño Técnico
- [ ] Completar design document con arquitectura detallada
- [ ] Definir correctness properties para property-based testing
- [ ] Documentar interfaces de componentes
- [ ] Crear diagramas de flujo y secuencia

### Fase 2: Implementación
- [ ] Implementar cliente API con rate limiting
- [ ] Implementar manejador de paginación con circuit breaker
- [ ] Implementar gestión de estado con DynamoDB
- [ ] Crear DAGs de Airflow para 5 tipos de datos
- [ ] Implementar validador y enriquecedor de datos

### Fase 3: Testing
- [ ] Unit tests para componentes individuales
- [ ] Property-based tests para correctness properties
- [ ] Integration tests con LocalStack
- [ ] End-to-end tests con datos reales

### Fase 4: Deployment
- [ ] Configurar infraestructura con Terraform
- [ ] Desplegar MWAA environment
- [ ] Configurar EventBridge rules
- [ ] Validar en ambiente de testing

## Documentación Relacionada

### Especificaciones
- **[requirements.md](.kiro/specs/api-polling-system/requirements.md)** - Requerimientos completos ⭐ NUEVO
- **[design.md](.kiro/specs/api-polling-system/design.md)** - Design document (en progreso)
- **[tasks.md](.kiro/specs/api-polling-system/tasks.md)** - Plan de implementación (en progreso)

### Arquitectura General
- **[Documento Detallado de Diseño Janis-Cenco.md](Documento%20Detallado%20de%20Diseño%20Janis-Cenco.md)** - Arquitectura completa
- **[diagrama-mermaid.md](diagrama-mermaid.md)** - Diagramas de arquitectura

### Infraestructura
- **[.kiro/specs/01-aws-infrastructure/](../.kiro/specs/01-aws-infrastructure/)** - Infraestructura AWS base
- **[terraform/modules/eventbridge/](../terraform/modules/eventbridge/)** - Módulo EventBridge
- **[terraform/modules/mwaa/](../terraform/modules/mwaa/)** - Módulo MWAA (pendiente)

### Guías de Desarrollo
- **[.kiro/steering/tech.md](../.kiro/steering/tech.md)** - Tech stack y herramientas
- **[.kiro/steering/structure.md](../.kiro/steering/structure.md)** - Estructura del proyecto
- **[.kiro/steering/Buenas practicas de AWS.md](../.kiro/steering/Buenas%20practicas%20de%20AWS.md)** - Best practices AWS

## Notas Importantes

### Ventana de Solapamiento
El sistema usa una ventana de solapamiento de 1 minuto (last_successful_execution - 1 min) para prevenir pérdida de datos. Esto significa que algunos registros pueden procesarse dos veces, pero la deduplicación asegura que no haya duplicados en el output.

### Rate Limiting
El límite de 100 requests/minuto es conservador para no sobrecargar las APIs de Janis. Este valor puede ajustarse según la capacidad de la infraestructura de Janis.

### Circuit Breaker
El límite de 1000 páginas previene bucles infinitos de paginación. Para datasets muy grandes, considerar implementar checkpointing para reanudar desde la última página procesada.

### Idempotencia
Todas las operaciones están diseñadas para ser idempotentes, permitiendo reintentos seguros en caso de fallos. Esto es crítico para la confiabilidad del sistema.

### Monitoring
El sistema emite métricas detalladas a CloudWatch para permitir monitoreo proactivo. Las alarmas están configuradas para alertar cuando:
- Validation pass rate < 95%
- DAG falla
- Circuit breaker se activa

---

**Estado:** ✅ Requirements document completado  
**Próximo paso:** Completar design document con arquitectura detallada y correctness properties  
**Responsable:** Equipo de Data Engineering  
**Fecha estimada de implementación:** Marzo 2026
