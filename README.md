# Janis-Cencosud Data Integration Platform

[![Coverage](https://img.shields.io/badge/coverage-90%25-brightgreen)](max/polling/htmlcov/index.html)
[![Python](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org/)
[![Tests](https://img.shields.io/badge/tests-102%20passed-success)](max/polling/TESTING.md)

Plataforma de integración de datos moderna entre el sistema WMS Janis y el Data Lake de Cencosud en AWS.

## 🎯 Objetivos

- **Migración de Datos**: Transferir datos históricos desde MySQL de Janis hacia Redshift
- **Sincronización en Tiempo Real**: Mantener datos actualizados mediante webhooks y polling
- **Disponibilidad para BI**: Datos curados para Power BI y herramientas analíticas

## 🏗️ Arquitectura

### Componentes Core
- **Ingesta Híbrida**: Webhooks + polling programado
- **Data Lake**: Arquitectura Bronze/Silver/Gold con Apache Iceberg
- **Orquestación**: EventBridge + MWAA (Apache Airflow)
- **Procesamiento**: AWS Glue para transformaciones ETL

### Servicios AWS
- Amazon API Gateway
- AWS Lambda
- Amazon Kinesis Data Firehose
- Amazon S3
- AWS Glue
- Amazon Redshift
- Amazon MWAA
- Amazon DynamoDB
- AWS Secrets Manager

## 📁 Estructura del Proyecto

```
.
├── max/
│   └── polling/              # Sistema de polling de APIs
│       ├── src/              # Código fuente
│       │   ├── api_client.py
│       │   ├── pagination_handler.py
│       │   ├── state_manager.py
│       │   ├── s3_writer.py
│       │   └── airflow_tasks.py
│       ├── tests/            # Tests (102 tests, 90% coverage)
│       │   ├── test_api_client.py
│       │   ├── test_pagination_handler.py
│       │   ├── test_state_manager.py
│       │   ├── test_state_manager_integration.py
│       │   ├── test_s3_writer.py
│       │   ├── test_s3_writer_integration.py
│       │   └── test_airflow_tasks.py
│       ├── pytest.ini
│       ├── run_all_tests.ps1
│       └── TESTING.md
├── airflow/                  # DAGs de MWAA
├── terraform/                # Infrastructure as Code
├── sonar-project.properties  # Configuración SonarQube
└── README.md
```

## 🧪 Testing

### Coverage: 90%

| Módulo | Coverage | Tests |
|--------|----------|-------|
| s3_writer.py | 100% | 32 (18 unit + 14 integration) |
| airflow_tasks.py | 90% | 8 unit |
| api_client.py | 90% | 20 unit |
| state_manager.py | 90% | 27 (15 unit + 12 integration) |
| pagination_handler.py | 82% | 15 unit |

### Ejecutar Tests

```bash
# Todos los tests (requiere LocalStack)
cd max/polling
python -m pytest tests/ -v --cov=src --cov-report=html --cov-report=xml

# Solo tests unitarios
python -m pytest tests/ -v -m "not integration"

# Solo tests de integración
python -m pytest tests/ -v -m "integration"
```

### Tests de Integración con LocalStack

Los tests de integración ejecutan código real contra DynamoDB y S3 en LocalStack:

```bash
# Iniciar LocalStack
docker run -d -p 4566:4566 localstack/localstack

# Ejecutar tests
./run_all_tests.ps1
```

Ver [TESTING.md](max/polling/TESTING.md) para más detalles.

## 🚀 Instalación

### Requisitos
- Python 3.11+
- Docker (para LocalStack)
- AWS CLI
- Terraform

### Setup

```bash
# Instalar dependencias
pip install -r max/polling/requirements.txt

# Instalar dependencias de desarrollo
pip install pytest pytest-cov hypothesis boto3

# Configurar variables de entorno
cp .env.example .env
# Editar .env con tus credenciales
```

## 📊 SonarQube

El proyecto está configurado para análisis de calidad de código con SonarQube:

```bash
# Generar coverage
cd max/polling
python -m pytest tests/ --cov=src --cov-report=xml:coverage.xml

# Ejecutar análisis
cd ../..
sonar-scanner
```

## 🔒 Seguridad

- ✅ No hardcodear credenciales
- ✅ Usar AWS Secrets Manager
- ✅ Cifrado en reposo y en tránsito
- ✅ Principio de menor privilegio en IAM
- ✅ VPC con subnets privadas

## 📝 Documentación

- [Testing Guide](max/polling/TESTING.md)
- [Architecture Documentation](Documentacion/)
- [Terraform Best Practices](.kiro/steering/Terraform%20Best%20Practices.md)
- [AWS Best Practices](.kiro/steering/Buenas%20practicas%20de%20AWS.md)

## 🤝 Contribuir

1. Fork el proyecto
2. Crear feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit cambios (`git commit -m 'Add AmazingFeature'`)
4. Push al branch (`git push origin feature/AmazingFeature`)
5. Abrir Pull Request

### Estándares de Código

- Coverage mínimo: 60%
- Tests obligatorios para nuevas funcionalidades
- Seguir PEP 8
- Documentar funciones públicas

## 📄 Licencia

Este proyecto es privado y confidencial.

## 👥 Equipo

Proyecto desarrollado para Cencosud.

---

**Nota**: Este es un proyecto de integración de datos empresarial. No incluye datos sensibles ni credenciales en el repositorio.
