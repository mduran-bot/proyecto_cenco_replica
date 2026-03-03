# API Polling System

Sistema de polling programado para consultar periódicamente las APIs de Janis y sincronizar datos con el Data Lake de Cencosud.

## Visión General

El Sistema de Polling de APIs es una solución de ingesta programada que opera independientemente del sistema de webhooks, proporcionando una red de seguridad para sincronización de datos. Utiliza Amazon EventBridge para scheduling inteligente y Amazon MWAA (Apache Airflow) para orquestación de workflows.

### Características Principales

- **Polling Incremental**: Solo obtiene datos nuevos o modificados desde la última ejecución
- **Rate Limiting**: Máximo 100 requests/minuto con sliding window algorithm
- **Retry Strategy**: Reintentos automáticos con backoff exponencial (2, 4, 8 segundos)
- **Circuit Breaker**: Previene bucles infinitos en paginación (máx 1000 páginas)
- **Data Enrichment**: Obtención paralela de entidades relacionadas
- **Data Validation**: Validación contra esquemas JSON y reglas de negocio
- **Error Handling**: Manejo robusto con notificaciones SNS

## Estructura del Proyecto

```
max/polling/
├── src/                          # Código fuente
│   ├── api_client.py            # Cliente HTTP con rate limiting ✅
│   ├── pagination_handler.py   # Manejo de paginación 🔄 (en cola)
│   ├── state_manager.py         # Gestión de estado DynamoDB ✅
│   ├── data_validator.py        # Validación de datos (pendiente)
│   ├── data_enricher.py         # Enriquecimiento de datos (pendiente)
│   └── README.md                # Documentación del código fuente
├── tests/                        # Tests unitarios y de integración
│   ├── test_api_client.py       # Tests de JanisAPIClient ✅
│   ├── test_pagination.py       # Tests de paginación 🔄 (en cola)
│   ├── test_state_manager.py   # Tests de estado ✅
│   └── test_integration.py      # Tests de integración (pendiente)
├── examples/                     # Ejemplos de uso
│   ├── api_client_usage.py      # Ejemplos de JanisAPIClient ✅
│   ├── state_manager_usage.py   # Ejemplos de StateManager ✅
│   └── polling_workflow.py      # Workflow completo (pendiente)
├── terraform/                    # Infraestructura como código
│   ├── modules/                 # Módulos reutilizables
│   │   ├── dynamodb/           # Tabla de control ✅
│   │   ├── s3/                 # Bucket de staging ✅
│   │   ├── sns/                # Notificaciones ✅
│   │   └── iam/                # Roles y políticas (pendiente)
│   ├── main.tf                 # Configuración principal ✅
│   ├── variables.tf            # Variables de entrada ✅
│   ├── outputs.tf              # Outputs (pendiente)
│   ├── localstack.tfvars       # Config para LocalStack ✅
│   └── README.md               # Documentación de Terraform ✅
├── config/                       # Archivos de configuración
│   └── schemas/                 # Esquemas JSON (pendiente)
├── docker-compose.yml           # LocalStack setup ✅
├── LOCALSTACK_SETUP.md          # Guía de LocalStack ✅
├── test_task4.py                # Test simple de StateManager ✅
├── test_localstack_integration.py # Tests de integración completos ✅
├── requirements.txt             # Dependencias Python
└── README.md                    # Este archivo
```

## Estado Actual

### ✅ Completado

#### Infraestructura (Terraform)
- **Módulo DynamoDB**: Tabla de control con billing on-demand, encryption, point-in-time recovery y CloudWatch alarms
- **Módulo S3**: Bucket de staging con versioning, lifecycle policies y encryption
- **Módulo SNS**: Tópico de notificaciones con subscripciones email/SQS/Lambda
- **Configuración Principal**: Provider AWS con soporte para LocalStack

#### Entorno de Desarrollo
- **Docker Compose**: Configuración de LocalStack con servicios DynamoDB, S3, SNS, EventBridge, CloudWatch Logs y Secrets Manager
- **Networking**: Red bridge aislada para servicios de polling
- **Persistencia**: Volumen local para datos de LocalStack

#### Código Fuente
- **JanisAPIClient**: Cliente HTTP completo con:
  - Rate limiting (sliding window, 100 req/min)
  - Retry strategy (3 intentos, backoff exponencial)
  - Timeout de 30 segundos
  - Manejo de errores HTTP apropiado
  - Context manager support
  - Tests unitarios (14 tests, 100% cobertura)
  - Documentación detallada
  - Ejemplos de uso

### ✅ Completado (Continuación)

**✅ Task 4:** StateManager para DynamoDB
- ✅ Gestión de estado con DynamoDB
- ✅ Lock acquisition/release con conditional updates
- ✅ State tracking para polling incremental
- ✅ Test simple de verificación (test_task4.py) - 5/5 pruebas pasadas
- ✅ Documentación completa y ejemplos
- ✅ Integración con LocalStack verificada

**⚠️ Nota:** Tasks 2 y 3 tienen código implementado pero NO están integradas con StateManager aún. Se requiere prueba integrada de APIClient + PaginationHandler + StateManager.

### 🚧 En Progreso

- **Task 5**: Checkpoint - Verificar componentes base (PRÓXIMO)
  - Verificar integración de Tasks 2, 3 y 4
  - Crear prueba integrada de APIClient + PaginationHandler + StateManager
- **Task 6**: Implementar lógica de polling incremental
  - build_incremental_filter con ventana de solapamiento
  - deduplicate_records por ID y timestamp

### 📋 Pendiente

#### Componentes Core
- [ ] DataValidator con esquemas JSON (Task 7)
- [ ] DataEnricher con paralelización (Task 8)

#### Airflow DAGs
- [ ] DAG base reutilizable (Task 10.1)
- [ ] DAGs específicos: orders, products, stock, prices, stores (Tasks 10.2-10.6)
- [ ] Funciones de task: acquire_lock, poll_api, validate, enrich, output, release_lock (Task 11)

#### Infraestructura
- [ ] Módulo IAM para roles y políticas (Task 1.4)
- [ ] Configuración completa de LocalStack (Task 1.5, Task 15)
- [ ] EventBridge rules para scheduling (Task 12)

#### Testing y Deployment
- [ ] Property-based tests (Tasks 2.3, 2.4, 3.3, 3.4, 4.3, etc.)
- [ ] Tests de integración con LocalStack (Task 17)
- [ ] Manejo de errores y notificaciones (Task 14)
- [ ] Monitoreo y métricas (Task 16)

## Instalación

### Requisitos Previos

- Python 3.11+
- Terraform >= 1.0
- AWS CLI configurado
- Docker (para LocalStack)

### Instalación de Dependencias

```bash
# Instalar dependencias Python
pip install -r requirements.txt

# Inicializar Terraform
cd terraform
terraform init
```

### Configuración

#### Variables de Entorno

```bash
# API de Janis
export JANIS_API_URL="https://api.janis.in"
export JANIS_API_KEY="your-api-key-here"

# AWS (para LocalStack)
export AWS_ACCESS_KEY_ID="test"
export AWS_SECRET_ACCESS_KEY="test"
export AWS_DEFAULT_REGION="us-east-1"
export LOCALSTACK_ENDPOINT="http://localhost:4566"
```

#### Archivo .env

Crea un archivo `.env` basado en `.env.example`:

```bash
cp .env.example .env
# Edita .env con tus credenciales
```

## Uso

### Cliente API (Standalone)

```python
from src.api_client import JanisAPIClient

# Crear cliente
with JanisAPIClient("https://api.janis.in", "your-api-key") as client:
    # Obtener órdenes
    response = client.get("orders", params={
        "page": 1,
        "pageSize": 100,
        "dateModified": "2024-01-01T00:00:00Z"
    })
    
    orders = response.get('data', [])
    print(f"Obtenidos {len(orders)} órdenes")
```

Ver más ejemplos en `examples/api_client_usage.py`.

### Despliegue de Infraestructura

#### LocalStack (Desarrollo)

LocalStack proporciona un entorno local completo de AWS para desarrollo y testing.

**Servicios Configurados:**
- DynamoDB (tabla de control de polling)
- S3 (bucket de staging)
- SNS (notificaciones de errores)
- EventBridge (scheduling de DAGs)
- CloudWatch Logs (logging centralizado)
- Secrets Manager (credenciales de API)

**🚀 Quick Start (Recomendado):**

```powershell
# Desde el directorio max/polling/
cd max/polling

# Setup automático (hace todo por ti)
.\setup-localstack.ps1

# Ejecutar tests de integración
python test_localstack_integration.py
```

El script automáticamente:
- ✅ Inicia LocalStack
- ✅ Crea tabla DynamoDB
- ✅ Configura variables de entorno
- ✅ Ejecuta suite de tests de integración

**Setup Manual (si prefieres control total):**

```powershell
# 1. Iniciar LocalStack
docker-compose up -d
Start-Sleep -Seconds 15

# 2. Configurar variables de entorno
$env:AWS_ACCESS_KEY_ID="test"
$env:AWS_SECRET_ACCESS_KEY="test"
$env:AWS_DEFAULT_REGION="us-east-1"
$env:LOCALSTACK_ENDPOINT="http://localhost:4566"

# 3. Crear tabla DynamoDB
aws --endpoint-url=http://localhost:4566 dynamodb create-table `
  --table-name polling_control `
  --attribute-definitions AttributeName=data_type,AttributeType=S `
  --key-schema AttributeName=data_type,KeyType=HASH `
  --billing-mode PAY_PER_REQUEST

# 4. Verificar recursos
aws --endpoint-url=http://localhost:4566 dynamodb list-tables
```

**Verificar Recursos:**

```powershell
# Listar tablas DynamoDB
aws --endpoint-url=http://localhost:4566 dynamodb list-tables

# Ver contenido de tabla
aws --endpoint-url=http://localhost:4566 dynamodb scan --table-name polling_control --output table

# Ver un item específico
aws --endpoint-url=http://localhost:4566 dynamodb get-item `
  --table-name polling_control `
  --key '{"data_type":{"S":"orders"}}'
```

**Detener LocalStack:**

```powershell
# Detener contenedor
docker-compose down

# Detener y eliminar datos persistentes
docker-compose down
Remove-Item -Recurse -Force localstack-data -ErrorAction SilentlyContinue
```

**📚 Guías Detalladas:**
- **[QUICK_START.md](QUICK_START.md)** - Inicio rápido en 5 minutos
- **[GUIA_TESTING_LOCALSTACK.md](GUIA_TESTING_LOCALSTACK.md)** - Guía completa paso a paso con troubleshooting
- **[LOCALSTACK_SETUP.md](LOCALSTACK_SETUP.md)** - Documentación técnica detallada
- **[TESTING_CHECKLIST.md](TESTING_CHECKLIST.md)** - Checklist de verificación

#### AWS (Producción)

```bash
cd terraform

# Planificar cambios
terraform plan -var-file="prod.tfvars"

# Aplicar cambios
terraform apply -var-file="prod.tfvars"
```

## Testing

### Tests Unitarios (Sin LocalStack)

Los tests unitarios usan mocks y no requieren LocalStack:

```powershell
# Ejecutar todos los tests
python -m pytest tests/ -v

# Ejecutar tests específicos
python -m pytest tests/test_state_manager.py -v
python -m pytest tests/test_api_client.py -v
python -m pytest tests/test_pagination_handler.py -v

# Con cobertura
python -m pytest tests/ --cov=src --cov-report=html --cov-report=term
```

**Resultado esperado:** 40 tests pasan (20 StateManager + 12 APIClient + 8 PaginationHandler)

### Tests de Integración (Con LocalStack)

Los tests de integración verifican el funcionamiento real con DynamoDB:

```powershell
# 1. Iniciar LocalStack (si no está corriendo)
docker-compose up -d

# 2. Setup automático (crea tabla y configura entorno)
.\setup-localstack.ps1

# 3. Ejecutar tests de integración
python test_localstack_integration.py

# 4. Ejecutar test simple de Task 4 (StateManager)
python test_task4.py
```

**Resultado esperado:** 4/4 escenarios pasan
- ✅ Operaciones básicas de lock
- ✅ Escenario de fallo con preservación de timestamp
- ✅ Primera ejecución sin estado previo
- ✅ Actualización de last_modified_date

**Test Task 4 (test_task4.py):**
- ✅ Adquisición de lock exitosa
- ✅ Prevención de lock concurrente
- ✅ Consulta de estado actual
- ✅ Liberación de lock con éxito
- ✅ Verificación de estado después de liberar

### Ejemplos Interactivos

```powershell
# Ejemplo completo de StateManager
python examples/state_manager_usage.py

# Ejemplo de API Client
python examples/api_client_usage.py

# Ejemplo de Pagination Handler
python examples/pagination_handler_usage.py
```

### Checklist de Verificación

Usa el checklist completo para verificar que todo funciona:

```powershell
# Ver checklist interactivo
cat TESTING_CHECKLIST.md
```

**📚 Guías de Testing:**
- **[GUIA_TESTING_LOCALSTACK.md](GUIA_TESTING_LOCALSTACK.md)** - Guía completa con 8 pasos detallados
- **[TESTING_CHECKLIST.md](TESTING_CHECKLIST.md)** - Checklist de verificación con comandos
- **[QUICK_START.md](QUICK_START.md)** - Inicio rápido para testing

## Arquitectura

### Flujo de Ejecución

```
EventBridge → MWAA DAG → Acquire Lock (DynamoDB) → Poll API (JanisAPIClient)
                                                           ↓
                                                    Pagination Handler
                                                           ↓
                                                    Data Validator
                                                           ↓
                                                    Data Enricher
                                                           ↓
                                                    Output Handler
                                                           ↓
                                                    Release Lock
```

### Componentes

1. **EventBridge**: Dispara DAGs según schedules configurados
2. **MWAA (Airflow)**: Orquesta el workflow de polling
3. **DynamoDB**: Gestiona estado y locks para prevenir ejecuciones concurrentes
4. **JanisAPIClient**: Cliente HTTP con rate limiting y retry logic
5. **PaginationHandler**: Maneja paginación con circuit breaker
6. **DataValidator**: Valida datos contra esquemas JSON
7. **DataEnricher**: Obtiene entidades relacionadas en paralelo
8. **S3**: Almacena datos temporalmente antes del ETL
9. **SNS**: Notifica errores y eventos importantes

### Schedules de Polling

| Tipo de Dato | Frecuencia | EventBridge Rule |
|--------------|------------|------------------|
| Orders       | 5 minutos  | `rate(5 minutes)` |
| Products     | 1 hora     | `rate(1 hour)` |
| Stock        | 10 minutos | `rate(10 minutes)` |
| Prices       | 30 minutos | `rate(30 minutes)` |
| Stores       | 24 horas   | `rate(1 day)` |

## Documentación

### Especificaciones
- **[requirements.md](../../.kiro/specs/api-polling-system/requirements.md)** - Requerimientos completos (12 requerimientos)
- **[design.md](../../.kiro/specs/api-polling-system/design.md)** - Documento de diseño (20 propiedades de correctitud)
- **[tasks.md](../../.kiro/specs/api-polling-system/tasks.md)** - Plan de implementación (19 tareas)

### Documentación Técnica
- **[src/README.md](src/README.md)** - Documentación del código fuente
- **[terraform/README.md](terraform/README.md)** - Documentación de infraestructura
- **[terraform/modules/dynamodb/README.md](terraform/modules/dynamodb/README.md)** - Módulo DynamoDB
- **[LOCALSTACK_SETUP.md](LOCALSTACK_SETUP.md)** - Guía completa de LocalStack

### Guías
- **[Sistema de Polling de APIs - Resumen](../../Documentación%20Cenco/Sistema%20de%20Polling%20de%20APIs%20-%20Resumen.md)** - Resumen ejecutivo

## Monitoreo

### CloudWatch Metrics

- **RecordsFetched**: Total de registros obtenidos por ejecución
- **ValidationPassRate**: Porcentaje de registros válidos
- **ExecutionDuration**: Duración de cada ejecución
- **APIErrors**: Errores de API por tipo

### CloudWatch Alarms

- **DynamoDB Read/Write Throttle**: Alerta cuando hay throttling
- **Lock Contention**: Alerta cuando hay alta contención de locks
- **Validation Pass Rate**: Alerta cuando < 95%
- **DAG Failures**: Alerta cuando un DAG falla

### CloudWatch Logs

Logs estructurados con formato JSON:

```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "execution_id": "uuid-1234",
  "data_type": "orders",
  "level": "INFO",
  "message": "Polling completed successfully",
  "records_fetched": 150,
  "validation_pass_rate": 0.98
}
```

## Troubleshooting

### LocalStack Issues

Para troubleshooting detallado, consulta:
- **[GUIA_TESTING_LOCALSTACK.md](GUIA_TESTING_LOCALSTACK.md#-troubleshooting)** - Soluciones a problemas comunes
- **[LOCALSTACK_SETUP.md](LOCALSTACK_SETUP.md#troubleshooting)** - Troubleshooting técnico avanzado

**Soluciones Rápidas:**

```powershell
# Error: "Unable to locate credentials"
$env:AWS_ACCESS_KEY_ID="test"
$env:AWS_SECRET_ACCESS_KEY="test"
$env:AWS_DEFAULT_REGION="us-east-1"

# Error: "Could not connect to the endpoint URL"
docker ps | Select-String "localstack"
Test-NetConnection -ComputerName localhost -Port 4566

# Error: "ResourceNotFoundException: Cannot do operations on a non-existent table"
aws --endpoint-url=http://localhost:4566 dynamodb create-table `
  --table-name polling_control `
  --attribute-definitions AttributeName=data_type,AttributeType=S `
  --key-schema AttributeName=data_type,KeyType=HASH `
  --billing-mode PAY_PER_REQUEST

# Tests fallan con "Connection refused"
docker logs janis-polling-localstack
Start-Sleep -Seconds 20

# Reinicio completo
docker-compose down
Remove-Item -Recurse -Force localstack-data -ErrorAction SilentlyContinue
docker-compose up -d
Start-Sleep -Seconds 15
.\setup-localstack.ps1
```

### Error: "Rate limit exceeded"

**Causa**: Se alcanzó el límite de 100 requests/minuto.

**Solución**: El cliente automáticamente espera. Si persiste, revisar configuración de rate_limit.

### Error: "Lock already acquired"

**Causa**: Otra ejecución del mismo data_type está en progreso.

**Solución**: Esto es comportamiento esperado. El DAG debe salir graciosamente.

### Error: "Circuit breaker triggered"

**Causa**: La paginación excedió 1000 páginas.

**Solución**: Revisar filtros de consulta o aumentar el límite del circuit breaker.

### Error: "Validation pass rate < 95%"

**Causa**: Muchos registros inválidos en la respuesta de la API.

**Solución**: Revisar esquemas JSON y logs de validación para identificar problemas.

## Contribución

### Workflow de Desarrollo

1. Crear branch desde `develop`: `git checkout -b feature/my-feature`
2. Implementar cambios siguiendo las especificaciones en `.kiro/specs/api-polling-system/`
3. Escribir tests unitarios y de integración
4. Ejecutar tests: `pytest tests/ -v`
5. Formatear código: `black src/ tests/`
6. Crear pull request hacia `develop`

### Estándares de Código

- **Python**: PEP 8, type hints, docstrings
- **Terraform**: HCL formatting, módulos reutilizables
- **Tests**: Mínimo 80% de cobertura
- **Documentación**: README actualizado con cada cambio

## Próximos Pasos

### Fase Actual: Implementación Base

1. ✅ **Task 1.1**: Módulo DynamoDB (COMPLETADO)
2. ✅ **Task 1.2-1.3**: Módulos S3 y SNS (COMPLETADO)
3. ✅ **Task 1.5**: Configuración LocalStack con docker-compose (COMPLETADO)
4. ✅ **Task 2.1**: JanisAPIClient - Inicialización y sesión HTTP (COMPLETADO)
5. 🚧 **Task 2.2**: Rate limiting con sliding window (EN PROGRESO)
6. 🔄 **Task 3**: PaginationHandler con circuit breaker (EN COLA)
7. ✅ **Task 4**: StateManager para DynamoDB (COMPLETADO - test_task4.py disponible)
8. 📋 **Task 2.3-2.4**: Property tests para rate limiting y reintentos
9. 📋 **Task 1.4**: Módulo IAM para roles y políticas
10. 📋 **Task 5**: Checkpoint - Verificar componentes base

### Fase Siguiente: Implementación Core

- Tasks 6-8: Polling incremental, validación y enriquecimiento
- Tasks 10-11: DAGs de Airflow
- Task 12: EventBridge scheduling

Ver [tasks.md](../../.kiro/specs/api-polling-system/tasks.md) para el plan completo.

## Licencia

Propiedad de Cencosud - Uso interno únicamente.

## Contacto

- **Equipo**: Data Engineering
- **Proyecto**: Janis-Cencosud Integration
- **Spec**: `.kiro/specs/api-polling-system/`

---

**Última actualización**: 23 de Febrero de 2026  
**Estado**: ✅ Task 4 (StateManager) COMPLETADO y verificado con LocalStack - Próximo: Task 6 (Polling Incremental)  
**Versión**: 0.1.0-alpha
