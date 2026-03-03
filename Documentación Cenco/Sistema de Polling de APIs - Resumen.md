# Sistema de Polling de APIs - Resumen Ejecutivo

**Fecha:** 23 de Febrero de 2026  
**Estado:** Requirements completados, Design en progreso  
**Spec:** `.kiro/specs/api-polling-system/`

## ¿Qué es el Sistema de Polling de APIs?

El Sistema de Polling de APIs es una solución de ingesta programada que consulta periódicamente las APIs de Janis para recuperar datos operacionales. Opera independientemente del sistema de webhooks, proporcionando una red de seguridad para sincronización de datos.

## Componentes Principales

### 1. Amazon EventBridge
**Propósito:** Scheduling inteligente de polling

**Schedules Configurados:**
- **Orders**: Cada 5 minutos (alta frecuencia)
- **Products**: Cada 1 hora (baja frecuencia)
- **Stock**: Cada 10 minutos (media frecuencia)
- **Prices**: Cada 30 minutos (media frecuencia)
- **Stores**: Cada 24 horas (muy baja frecuencia)

**Ventaja:** Reduce overhead de MWAA al disparar DAGs solo cuando es necesario.

### 2. Amazon MWAA (Apache Airflow)
**Propósito:** Orquestación de workflows de polling

**Configuración:**
- Airflow 2.7.2
- Python 3.11
- Event-driven (schedule_interval=None)
- Auto-scaling: 1-3 workers

**DAGs:** Un DAG por tipo de dato (5 total)

### 3. DynamoDB Control Table
**Propósito:** Gestión de estado y prevención de ejecuciones concurrentes

**Configuración Terraform:**
- Billing mode: PAY_PER_REQUEST (on-demand)
- Encryption: Server-side encryption habilitado
- Point-in-time recovery: Habilitado
- CloudWatch Alarms: 3 alarmas configuradas

**Funcionalidades:**
- Lock acquisition con conditional updates
- Tracking de last_successful_execution
- Polling incremental (solo datos nuevos)
- Liberación automática de locks

**CloudWatch Alarms:**
1. **Read Throttle**: Alerta cuando hay throttling de lectura (threshold: 10 eventos en 5 min)
2. **Write Throttle**: Alerta cuando hay throttling de escritura (threshold: 10 eventos en 5 min)
3. **Conditional Check Failed**: Alerta cuando hay alta contención de locks (threshold: 50 en 5 min)

**Schema de la Tabla:**
```json
{
  "data_type": "orders",              // PK: tipo de dato
  "lock_acquired": true,              // Estado del lock
  "lock_timestamp": "2024-01-15T10:30:00Z",
  "execution_id": "uuid-1234",
  "last_successful_execution": "2024-01-15T10:25:00Z",
  "last_modified_date": "2024-01-15T10:24:00Z",
  "status": "running",                // running | completed | failed
  "records_fetched": 0,
  "error_message": null
}
```

### 4. Kinesis Firehose
**Propósito:** Entrega de datos validados al Data Lake

**Configuración:**
- Batch size: 500 registros
- Retry logic: Hasta 3 intentos
- Destino: S3 Bronze Layer

## Flujo de Ejecución

```
┌─────────────────┐
│ EventBridge     │ Trigger según schedule
│ Rule            │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ MWAA DAG        │ Inicia ejecución
│ (Airflow)       │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Acquire Lock    │ Previene ejecuciones concurrentes
│ (DynamoDB)      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Build Filter    │ last_successful_execution - 1 min
│ (Incremental)   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Poll Janis API  │ Rate limiting + Pagination
│ (HTTP Client)   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Validate Data   │ Schema + Business rules
│ (Validator)     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Enrich Data     │ Fetch related entities (parallel)
│ (Enricher)      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Batch to        │ 500 records per batch
│ Kinesis         │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Update State &  │ Update timestamps, release lock
│ Release Lock    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Emit Metrics    │ CloudWatch metrics
│ (Monitoring)    │
└─────────────────┘
```

## Características Clave

### Polling Incremental
- Solo obtiene datos nuevos o modificados desde última ejecución
- Ventana de solapamiento de 1 minuto para prevenir pérdida de datos
- Deduplicación automática de registros duplicados

### Rate Limiting
- Máximo 100 requests por minuto
- Retry con backoff exponencial (2, 4, 8 segundos)
- Manejo diferenciado de errores HTTP

### Pagination Handling
- Tamaño de página: 100 registros
- Circuit breaker: Máximo 1000 páginas
- Previene bucles infinitos

### Data Enrichment
- Orders → Order Items (paralelo)
- Products → SKUs (paralelo)
- ThreadPoolExecutor con 5 workers
- Manejo resiliente de fallos

### Data Validation
- Validación contra esquemas JSON
- Detección de duplicados en lote
- Validación de reglas de negocio
- Alertas cuando validation pass rate < 95%

### Error Handling
- Logging detallado con stack traces
- Notificaciones SNS en fallos
- Operaciones idempotentes
- Salida graciosa sin lock

## Diferencias vs Webhook Ingestion

| Aspecto | Webhook Ingestion | API Polling |
|---------|-------------------|-------------|
| **Trigger** | Eventos en tiempo real | Programado (EventBridge) |
| **Latencia** | Segundos | Minutos (según schedule) |
| **Completitud** | Depende de webhooks | Garantizada (full refresh) |
| **Carga API** | Baja (solo cambios) | Media (polling periódico) |
| **Resiliencia** | Requiere retry logic | Polling incremental con ventana |
| **Uso** | Datos críticos en tiempo real | Red de seguridad + datos históricos |

## Ventajas del Sistema

### 1. Red de Seguridad
Si los webhooks fallan o se pierden eventos, el polling asegura que todos los datos eventualmente se sincronicen.

### 2. Datos Históricos
Permite obtener datos históricos que no fueron capturados por webhooks.

### 3. Independencia
Opera independientemente del sistema de webhooks, proporcionando redundancia.

### 4. Optimización de Recursos
EventBridge dispara DAGs solo cuando es necesario, reduciendo costos de MWAA.

### 5. Polling Incremental
Solo obtiene datos nuevos, minimizando carga en APIs de Janis.

## Monitoreo y Observabilidad

### CloudWatch Metrics
- **RecordsFetched**: Total de registros obtenidos
- **ValidationPassRate**: Porcentaje de registros válidos
- **ExecutionDuration**: Duración de ejecución
- **APIErrors**: Errores de API

### CloudWatch Alarms
- Validation pass rate < 95%
- DAG falla
- Circuit breaker activado

### CloudWatch Logs
- Logs estructurados con correlation IDs
- Niveles: INFO, WARNING, ERROR
- Filtrado por data_type y execution_id

### SNS Notifications
- Notificaciones en fallos de DAG
- Incluye data_type, execution_id, error details

## Testing con LocalStack

El sistema está diseñado para ser completamente testeable en LocalStack con una suite completa de tests de integración.

### 🚀 Quick Start

```powershell
# Desde max/polling/
cd max/polling

# Setup automático (hace todo por ti)
.\setup-localstack.ps1

# Ejecutar tests de integración completos
python test_localstack_integration.py

# O ejecutar test simple de Task 4
python test_task4.py
```

### Componentes Testeables

**✅ Implementados y Testeados:**
1. **StateManager** - Gestión de estado con DynamoDB
   - Lock acquisition/release
   - Concurrent execution prevention
   - Timestamp preservation on failure
   - First execution handling
   
2. **JanisAPIClient** - Cliente HTTP con rate limiting
   - Rate limiting (100 req/min)
   - Retry strategy (exponential backoff)
   - Error handling (4xx, 5xx, 429)
   
3. **PaginationHandler** - Paginación con circuit breaker
   - Page iteration
   - Circuit breaker (max 1000 pages)
   - hasNextPage detection

### Suite de Tests de Integración

**4 Escenarios Principales:**

1. **Operaciones Básicas de Lock**
   - Adquirir lock exitosamente
   - Rechazar lock concurrente
   - Liberar lock correctamente
   - Adquirir nuevo lock después de liberar

2. **Escenario de Fallo**
   - Preservar last_modified_date en fallo
   - Actualizar status a 'failed'
   - Registrar error_message
   - Liberar lock automáticamente

3. **Primera Ejecución**
   - get_control_item() retorna None
   - get_last_modified_date() retorna None
   - Establecer baseline correctamente

4. **Actualización de Timestamp**
   - Actualizar last_modified_date en éxito
   - Actualizar last_successful_execution
   - Registrar records_fetched

### Tests Disponibles

**test_localstack_integration.py** - Suite completa de tests de integración
- 4 escenarios principales
- Verificación completa de funcionalidad
- Tiempo de ejecución: <10 segundos

**test_task4.py** - Test simple y rápido de StateManager
- Prueba básica de lock acquisition/release
- Verificación de prevención de locks concurrentes
- Consulta de estado actual
- Ideal para verificación rápida después de cambios

### Verificación de Datos

```powershell
# Ver todos los items en DynamoDB
aws --endpoint-url=http://localhost:4566 dynamodb scan `
  --table-name polling_control --output table

# Ver un item específico
aws --endpoint-url=http://localhost:4566 dynamodb get-item `
  --table-name polling_control `
  --key '{"data_type":{"S":"orders"}}'

# Ver logs de LocalStack
docker logs -f janis-polling-localstack
```

### Guías de Testing

El proyecto incluye documentación completa de testing:

- **[GUIA_TESTING_LOCALSTACK.md](../max/polling/GUIA_TESTING_LOCALSTACK.md)** - Guía completa paso a paso (8 pasos detallados)
- **[QUICK_START.md](../max/polling/QUICK_START.md)** - Inicio rápido en 5 minutos
- **[TESTING_CHECKLIST.md](../max/polling/TESTING_CHECKLIST.md)** - Checklist de verificación
- **[LOCALSTACK_SETUP.md](../max/polling/LOCALSTACK_SETUP.md)** - Documentación técnica avanzada

### Métricas de Testing

**Tests Unitarios:**
- ✅ 40/40 tests pasan
- ✅ 100% pass rate
- ✅ >80% cobertura de código

**Tests de Integración:**
- ✅ 4/4 escenarios pasan
- ✅ 100% pass rate
- ✅ <10 segundos tiempo de ejecución

## Costos Estimados

### Componentes
- **MWAA**: ~$300/mes (mw1.small, 1-3 workers)
- **EventBridge**: ~$1/mes (5 rules)
- **DynamoDB**: ~$5/mes (on-demand)
- **Kinesis Firehose**: ~$10/mes (según volumen)
- **CloudWatch**: ~$5/mes (logs + métricas)

**Total Estimado:** ~$320/mes

### Optimizaciones
- MWAA solo se activa cuando EventBridge dispara DAGs
- Polling incremental reduce carga de API
- Batch operations reducen costos de Kinesis

## Estado Actual

### ✅ Completado
- [x] Requirements document (12 requerimientos)
- [x] Design document con 20 propiedades de correctitud
- [x] Arquitectura de alto nivel
- [x] Definición de componentes
- [x] Flujo de ejecución
- [x] Estrategia de testing
- [x] Plan de implementación (19 tareas)
- [x] **Módulo DynamoDB** (Task 1.1) - Tabla de control con alarms y monitoring
- [x] **JanisAPIClient** (Task 2.1) - Cliente HTTP completo con rate limiting y retry logic
- [x] **PaginationHandler** (Task 3) - Paginación con circuit breaker
  - ✅ Iteración de páginas con hasNextPage
  - ✅ Circuit breaker (max 1000 páginas)
  - ✅ 8 tests unitarios
  - ✅ Ejemplos de uso
- [x] **StateManager** (Task 4) - Gestión de estado con DynamoDB ✅ COMPLETADO
  - ✅ Lock acquisition/release con conditional updates
  - ✅ State tracking para polling incremental
  - ✅ 20 tests unitarios (100% pass rate)
  - ✅ 4 tests de integración con LocalStack (100% pass rate)
  - ✅ Test simple de verificación (test_task4.py)
  - ✅ Documentación completa y ejemplos
  - ✅ Integración con LocalStack verificada
- [x] **Guías de Testing con LocalStack**
  - ✅ GUIA_TESTING_LOCALSTACK.md - Guía completa paso a paso
  - ✅ QUICK_START.md - Inicio rápido en 5 minutos
  - ✅ TESTING_CHECKLIST.md - Checklist de verificación
  - ✅ test_localstack_integration.py - Suite de tests de integración
  - ✅ setup-localstack.ps1 - Script de setup automático
  - ✅ test_task4.py - Test simple de StateManager
  - ✅ pruebas_de_tareas.md - Documentación de resultados de pruebas

### 🚧 En Progreso
- [~] **Task 6: Implementar lógica de polling incremental** (PRÓXIMO)
  - [ ] Crear función build_incremental_filter
  - [ ] Crear función deduplicate_records
  - [ ] Property tests para polling incremental

### 📋 Pendiente

#### Componentes Core
- [ ] Polling incremental (Task 6)
  - [ ] build_incremental_filter con ventana de solapamiento
  - [ ] deduplicate_records por ID y timestamp
- [ ] DataValidator con esquemas JSON (Task 7)
- [ ] DataEnricher con paralelización (Task 8)

#### Airflow DAGs
- [ ] DAG base reutilizable (Task 10.1)
- [ ] DAGs específicos: orders, products, stock, prices, stores (Tasks 10.2-10.6)
- [ ] Funciones de task: acquire_lock, poll_api, validate, enrich, output, release_lock (Task 11)

#### Infraestructura
- [ ] Módulo IAM para roles y políticas (Task 1.4)
- [ ] EventBridge rules para scheduling (Task 12)

#### Testing y Deployment
- [ ] Property-based tests (Tasks 2.3, 2.4, 3.3, 3.4, 4.3, 6.3, 7.3, 8.3)
- [ ] Manejo de errores y notificaciones (Task 14)
- [ ] Monitoreo y métricas (Task 16)
- [ ] Tests de integración end-to-end (Task 17)

## Próximos Pasos

### ✅ Fase 1: Diseño (COMPLETADA)
1. ✅ Requirements document (12 requerimientos)
2. ✅ Design document con 20 propiedades de correctitud
3. ✅ Interfaces de componentes documentadas
4. ✅ Plan de implementación con 19 tareas

### ✅ Fase 2: Componentes Base (COMPLETADA)

**✅ Task 1.1:** Módulo DynamoDB
- ✅ Tabla de control con schema definido
- ✅ Billing mode PAY_PER_REQUEST
- ✅ Server-side encryption y point-in-time recovery
- ✅ CloudWatch alarms (throttling, lock contention)

**✅ Task 2.1:** JanisAPIClient
- ✅ Cliente HTTP completo con rate limiting
- ✅ Retry strategy con backoff exponencial
- ✅ 14 tests unitarios (100% cobertura)
- ✅ Documentación y ejemplos

**✅ Task 3:** PaginationHandler
- ✅ Paginación con circuit breaker
- ✅ Iteración de páginas con hasNextPage
- ✅ 8 tests unitarios
- ✅ Ejemplos de uso

**✅ Task 4:** StateManager
- ✅ Gestión de estado con DynamoDB
- ✅ Lock acquisition/release
- ✅ 20 tests unitarios + 4 tests de integración
- ✅ Documentación completa

**✅ Testing Infrastructure:**
- ✅ LocalStack setup con docker-compose
- ✅ Suite de tests de integración
- ✅ Guías completas de testing
- ✅ Scripts de setup automático

### 🚧 Fase 3: Implementación Core (EN PROGRESO)

**Próximas tareas inmediatas:**
1. **Task 5**: Checkpoint - Verificar componentes base ✅
2. **Task 6**: Implementar lógica de polling incremental (PRÓXIMO)
   - build_incremental_filter con ventana de solapamiento
   - deduplicate_records por ID y timestamp
3. **Task 7**: DataValidator con esquemas JSON
4. **Task 8**: DataEnricher con paralelización
5. **Tasks 10-11**: DAGs de Airflow
6. **Task 12**: EventBridge scheduling

### Fase 4: Testing y Deployment (Pendiente)
1. Property-based tests para todos los componentes
2. Manejo de errores y notificaciones (Task 14)
3. Monitoreo y métricas (Task 16)
4. Tests de integración end-to-end (Task 17)
5. Documentación final (Task 18)

## Documentación

### Especificaciones
- **[requirements.md](.kiro/specs/api-polling-system/requirements.md)** - Requerimientos completos ⭐
- **[design.md](.kiro/specs/api-polling-system/design.md)** - Design document (en progreso)
- **[tasks.md](.kiro/specs/api-polling-system/tasks.md)** - Plan de implementación (en progreso)

### Documentación General
- **[API_POLLING_SYSTEM_REQUIREMENTS_UPDATE.md](../Documentacion/API_POLLING_SYSTEM_REQUIREMENTS_UPDATE.md)** - Resumen de actualización
- **[Documento Detallado de Diseño Janis-Cenco.md](../Documento%20Detallado%20de%20Diseño%20Janis-Cenco.md)** - Arquitectura completa

### Guías Técnicas
- **[.kiro/steering/tech.md](../.kiro/steering/tech.md)** - Tech stack
- **[.kiro/steering/Buenas practicas de AWS.md](../.kiro/steering/Buenas%20practicas%20de%20AWS.md)** - Best practices

## Contacto

Para preguntas sobre el Sistema de Polling de APIs:
- **Equipo:** Data Engineering
- **Spec Owner:** [Nombre]
- **Documentación:** `.kiro/specs/api-polling-system/`

---

**Última actualización:** 23 de Febrero de 2026  
**Estado:** ✅ Task 4 (StateManager) COMPLETADO y verificado con LocalStack - Próximo: Task 6 (Polling Incremental)  
**Próxima acción:** Task 6 - Implementar lógica de polling incremental (build_incremental_filter, deduplicate_records)
