# Testing del Sistema de Polling

Este documento describe la estrategia de testing y cómo ejecutar los tests del sistema de polling.

## Estructura de Tests

```
tests/
├── conftest.py                          # Configuración compartida y fixtures de LocalStack
├── test_api_client.py                   # Tests unitarios del cliente API (20 tests)
├── test_pagination_handler.py           # Tests unitarios de paginación (15 tests)
├── test_state_manager.py                # Tests unitarios con mocks (15 tests)
├── test_state_manager_integration.py    # Tests de integración con LocalStack (12 tests)
├── test_s3_writer.py                    # Tests unitarios con mocks (18 tests)
└── test_s3_writer_integration.py        # Tests de integración con LocalStack (14 tests)
```

## Tipos de Tests

### Tests Unitarios (con mocks)
- Usan mocks para aislar componentes
- No requieren servicios externos
- Ejecución rápida
- Cobertura: ~19% (solo validan lógica de negocio)

### Tests de Integración (con LocalStack)
- Ejecutan código real contra DynamoDB y S3
- Requieren LocalStack corriendo
- Ejecución más lenta pero mayor cobertura
- Cobertura esperada: 60-70%

## Requisitos Previos

### Instalar Dependencias
```bash
pip install pytest pytest-cov hypothesis boto3
```

### Iniciar LocalStack (para tests de integración)
```bash
# Opción 1: Docker Compose
docker-compose up -d localstack

# Opción 2: Docker directo
docker run -d -p 4566:4566 localstack/localstack

# Verificar que está corriendo
curl http://localhost:4566/_localstack/health
```

## Ejecutar Tests

### Opción 1: Script PowerShell (Recomendado)
```powershell
cd max/polling
.\run_all_tests.ps1
```

El script automáticamente:
- Verifica si LocalStack está disponible
- Ejecuta tests unitarios + integración (si LocalStack está disponible)
- Ejecuta solo tests unitarios (si LocalStack no está disponible)
- Genera reportes HTML y XML

### Opción 2: Comando pytest directo

**Todos los tests (unitarios + integración):**
```bash
cd max/polling
python -m pytest tests/ -v --cov=src --cov-report=html:htmlcov --cov-report=xml:coverage.xml --cov-report=term-missing
```

**Solo tests unitarios:**
```bash
python -m pytest tests/ -v -m "not integration" --cov=src --cov-report=html --cov-report=xml
```

**Solo tests de integración:**
```bash
python -m pytest tests/ -v -m "integration" --cov=src --cov-report=html --cov-report=xml
```

### Opción 3: Tests específicos
```bash
# Solo StateManager
python -m pytest tests/test_state_manager*.py -v

# Solo S3Writer
python -m pytest tests/test_s3_writer*.py -v

# Solo API Client
python -m pytest tests/test_api_client.py -v
```

## Reportes de Coverage

Los tests generan dos tipos de reportes:

1. **HTML** (para visualización): `htmlcov/index.html`
   ```powershell
   start htmlcov/index.html
   ```

2. **XML** (para SonarQube): `coverage.xml`

## Módulos Testeados

### 1. API Client (`test_api_client.py`)
**Tests Unitarios: 20**
- ✅ Inicialización con parámetros válidos/inválidos
- ✅ Configuración de sesión HTTP con retry strategy
- ✅ Rate limiting con sliding window
- ✅ Manejo de errores HTTP (4xx, 5xx)
- ✅ Headers de autorización
- ✅ Timeout de 30 segundos
- ✅ Context manager support

Cobertura: ~25%

### 2. Pagination Handler (`test_pagination_handler.py`)
**Tests Unitarios: 15**
- ✅ Inicialización con valores por defecto/personalizados
- ✅ Paginación de una sola página
- ✅ Paginación de múltiples páginas
- ✅ Filtros adicionales en requests
- ✅ Circuit breaker para prevenir bucles infinitos
- ✅ Detección de hasNextPage
- ✅ Manejo de respuestas vacías
- ✅ Reset del handler

Cobertura: ~30%

### 3. State Manager
**Tests Unitarios: 15** (`test_state_manager.py`)
- ✅ Adquisición de lock con mocks
- ✅ Liberación de lock
- ✅ Obtención de estado

**Tests de Integración: 12** (`test_state_manager_integration.py`)
- ✅ Adquisición de lock en DynamoDB real
- ✅ Prevención de locks concurrentes
- ✅ Liberación de lock en éxito/fallo
- ✅ Actualización de last_modified_date
- ✅ Obtención de estado previo
- ✅ Manejo de primera ejecución
- ✅ Limpieza forzada de locks
- ✅ Flujo completo de lock/unlock

Cobertura: 20% (unitarios) → 65% (con integración)

### 4. S3 Writer
**Tests Unitarios: 18** (`test_s3_writer.py`)
- ✅ Inicialización con bucket name
- ✅ Escritura con mocks
- ✅ Listado con mocks
- ✅ Lectura con mocks

**Tests de Integración: 14** (`test_s3_writer_integration.py`)
- ✅ Verificación de bucket en S3 real
- ✅ Escritura de datos con particionamiento
- ✅ Estructura de paths (client/data_type/year=/month=/day=/)
- ✅ Manejo de datos vacíos
- ✅ Múltiples archivos en misma partición
- ✅ Listado de archivos
- ✅ Lectura de archivos
- ✅ Flujo completo escritura/lectura
- ✅ Múltiples clientes y tipos de datos

Cobertura: 15% (unitarios) → 70% (con integración)

## Configuración de pytest

El archivo `pytest.ini` configura:
- Directorio de tests: `tests/`
- Patrón de archivos: `test_*.py`
- Markers personalizados: `unit`, `integration`, `slow`
- Directorios ignorados (evita escanear sistema Windows)
- Opciones de output verboso

## Fixtures de LocalStack

El archivo `conftest.py` proporciona fixtures compartidos:

- `localstack_endpoint`: URL del endpoint de LocalStack
- `aws_credentials`: Credenciales de prueba
- `check_localstack`: Verifica disponibilidad de LocalStack
- `dynamodb_table`: Crea tabla de DynamoDB para tests
- `s3_bucket`: Crea bucket de S3 para tests

## Cobertura de Código

### Sin LocalStack (solo unitarios)
```
Module                    Coverage
---------------------------------
api_client.py             25%
pagination_handler.py     30%
state_manager.py          20%
s3_writer.py              15%
---------------------------------
TOTAL                     19%
```

### Con LocalStack (unitarios + integración)
```
Module                    Coverage
---------------------------------
api_client.py             25%
pagination_handler.py     30%
state_manager.py          65%
s3_writer.py              70%
---------------------------------
TOTAL                     60-70%
```

## Troubleshooting

### LocalStack no está disponible
```
✗ LocalStack no está disponible
Los tests de integración se saltarán
```
**Solución**: Iniciar LocalStack con Docker

### Tests de integración fallan
```
ClientError: Could not connect to the endpoint URL
```
**Solución**: Verificar que LocalStack está corriendo en `http://localhost:4566`

### Coverage muy bajo
```
TOTAL: 19%
```
**Solución**: Ejecutar con LocalStack para incluir tests de integración

## Próximos Pasos

1. ✅ Tests unitarios completos
2. ✅ Tests de integración con LocalStack
3. ⏳ Tests de performance
4. ⏳ Tests de carga
5. ⏳ Tests end-to-end completos
