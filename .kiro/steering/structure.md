# Project Structure and Organization

## Repository Layout

```
janis-cencosud-integration/
├── .kiro/
│   ├── specs/                    # Especificaciones detalladas por componente
│   │   ├── aws-infrastructure/   # Requerimientos de infraestructura VPC, redes
│   │   ├── webhook-ingestion/    # Sistema de ingesta de webhooks en tiempo real
│   │   ├── api-polling/          # Polling periódico con EventBridge + MWAA
│   │   ├── data-transformation/  # Transformaciones ETL Bronze→Silver→Gold
│   │   ├── initial-data-load/    # Carga inicial desde backup MySQL
│   │   ├── redshift-loading/     # Carga incremental a Redshift
│   │   └── monitoring-alerting/  # Observabilidad y alertas
│   └── steering/                 # Guías de desarrollo y mejores prácticas
├── terraform/                    # Infrastructure as Code
│   ├── environments/
│   │   ├── dev/
│   │   ├── staging/
│   │   └── prod/
│   ├── modules/
│   │   ├── vpc/
│   │   ├── api-gateway/
│   │   ├── lambda/
│   │   ├── kinesis/
│   │   ├── glue/
│   │   ├── mwaa/
│   │   ├── eventbridge/
│   │   └── redshift/
│   └── shared/
├── airflow/                      # DAGs y configuración de MWAA
│   ├── dags/
│   │   ├── dag_poll_orders.py
│   │   ├── dag_poll_products.py
│   │   ├── dag_poll_stock.py
│   │   ├── dag_poll_prices.py
│   │   └── dag_poll_stores.py
│   ├── plugins/
│   └── requirements.txt
├── lambda/                       # Funciones Lambda
│   ├── webhook-processor/
│   ├── data-enrichment/
│   └── monitoring/
├── glue/                         # Jobs de AWS Glue
│   ├── bronze-to-silver/
│   ├── silver-to-gold/
│   └── data-quality/
├── schemas/                      # Esquemas JSON y validaciones
│   ├── webhook-schemas/
│   ├── api-schemas/
│   └── redshift-ddl/
├── docs/                         # Documentación del proyecto
│   ├── architecture/
│   ├── deployment/
│   └── operations/
└── scripts/                      # Scripts de utilidad y deployment
    ├── deploy.sh
    ├── test-webhooks.py
    └── data-validation.py
```

## Organización por Capas

### Infrastructure Layer (terraform/)
- **Propósito**: Definición completa de infraestructura AWS
- **Estructura modular**: Un módulo por servicio AWS
- **Separación por ambiente**: dev/staging/prod con configuraciones específicas
- **Estado remoto**: S3 + DynamoDB para locking y colaboración

### Orchestration Layer (airflow/)
- **DAGs event-driven**: Triggered por EventBridge, no por schedule interno
- **Estructura por entidad**: Un DAG por tipo de dato (orders, products, etc.)
- **Configuración centralizada**: Variables y conexiones en MWAA
- **Plugins compartidos**: Utilidades comunes para todos los DAGs

### Processing Layer (lambda/ + glue/)
- **Lambda**: Procesamiento ligero y en tiempo real
- **Glue**: Transformaciones pesadas y batch processing
- **Separación por función**: Un directorio por responsabilidad específica
- **Código reutilizable**: Librerías compartidas entre funciones

### Data Layer (schemas/)
- **Validación de entrada**: Esquemas JSON para webhooks y APIs
- **Definición de salida**: DDL de Redshift y estructuras Iceberg
- **Versionado**: Control de cambios en esquemas de datos
- **Documentación**: Descripción de campos y transformaciones

## Convenciones de Naming

### Archivos y Directorios
- **Directorios**: kebab-case (webhook-ingestion, api-polling)
- **Archivos Python**: snake_case (dag_poll_orders.py)
- **Archivos Terraform**: snake_case (main.tf, variables.tf)
- **Archivos de configuración**: kebab-case (requirements.txt, docker-compose.yml)

### Recursos AWS
- **Prefijo del proyecto**: janis-cencosud
- **Sufijo de ambiente**: -dev, -staging, -prod
- **Formato general**: {proyecto}-{servicio}-{propósito}-{ambiente}
- **Ejemplos**:
  - S3: janis-cencosud-datalake-bronze-prod
  - Lambda: janis-cencosud-webhook-processor-prod
  - Glue Job: janis-cencosud-bronze-to-silver-orders-prod

### Código y Variables
- **Python**: snake_case para variables y funciones
- **Terraform**: snake_case para recursos y variables
- **Constantes**: UPPER_SNAKE_CASE
- **Clases**: PascalCase

## Flujo de Desarrollo

### Branching Strategy
- **main**: Código de producción estable
- **develop**: Integración de features
- **feature/***: Desarrollo de nuevas funcionalidades
- **hotfix/***: Correcciones urgentes de producción

### Deployment Pipeline
1. **Development**: Deploy automático a ambiente dev
2. **Testing**: Validación automática de infraestructura y código
3. **Staging**: Deploy manual con aprobación para testing
4. **Production**: Deploy manual con doble aprobación

### Configuration Management
- **Terraform**: Variables por ambiente en archivos .tfvars
- **MWAA**: Variables de Airflow en AWS Systems Manager
- **Lambda**: Variables de entorno por función
- **Secrets**: AWS Secrets Manager para credenciales sensibles

## Patrones de Organización

### Separación de Responsabilidades
- **Ingesta**: API Gateway + Lambda + Kinesis Firehose
- **Orquestación**: EventBridge + MWAA
- **Transformación**: AWS Glue con jobs especializados
- **Almacenamiento**: S3 (Bronze/Silver/Gold) + Redshift
- **Monitoreo**: CloudWatch + SNS + dashboards

### Modularidad
- **Terraform modules**: Reutilizables entre ambientes
- **Airflow plugins**: Funcionalidades compartidas entre DAGs
- **Lambda layers**: Dependencias comunes entre funciones
- **Glue libraries**: Transformaciones reutilizables

### Configuración Centralizada
- **AWS Systems Manager**: Parámetros de configuración
- **AWS Secrets Manager**: Credenciales y API keys
- **Terraform variables**: Configuración de infraestructura
- **Airflow Variables**: Configuración de workflows

## Documentación y Specs

### Estructura de Specs (.kiro/specs/)
- **requirements.md**: Requerimientos funcionales detallados
- **architecture.md**: Decisiones de diseño y patrones
- **implementation.md**: Detalles técnicos de implementación
- **testing.md**: Estrategias y casos de prueba

### Documentación Técnica (docs/)
- **Architecture**: Diagramas y decisiones de alto nivel
- **Deployment**: Guías de instalación y configuración
- **Operations**: Procedimientos de mantenimiento y troubleshooting
- **API**: Documentación de interfaces y contratos