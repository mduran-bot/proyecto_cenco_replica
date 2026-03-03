# Janis-Cencosud Data Integration Platform

Plataforma de integración de datos moderna entre el sistema WMS Janis y el Data Lake de Cencosud en AWS.

## 🚀 Inicio Rápido

### Para Nuevos Usuarios

Si recibes este proyecto por primera vez, **lee primero:**

📖 **[GUIA_COMPARTIR_PROYECTO.md](GUIA_COMPARTIR_PROYECTO.md)** - Guía completa para ejecutar el proyecto

### Para Usuarios Experimentados

```powershell
# 1. Configurar credenciales AWS
$env:AWS_ACCESS_KEY_ID = "tu-access-key"
$env:AWS_SECRET_ACCESS_KEY = "tu-secret-key"

# 2. Inicializar y desplegar
cd terraform
terraform init
terraform plan -var-file="environments/dev/dev.tfvars"
terraform apply -var-file="environments/dev/dev.tfvars"
```

## 📋 Requisitos Previos

- **Terraform** >= 1.0 ([Descargar](https://www.terraform.io/downloads))
- **AWS CLI** ([Descargar](https://aws.amazon.com/cli/))
- **Credenciales AWS** con permisos para crear recursos
- **(Opcional) Docker Desktop** para testing con LocalStack
- **(Opcional) Go 1.21+** para ejecutar property tests

## 🔔 Actualizaciones Recientes

### API Polling System Spec Completed (23 de Febrero, 2026)

**Documento Nuevo**: [API_POLLING_SYSTEM_REQUIREMENTS_UPDATE.md](Documentacion/API_POLLING_SYSTEM_REQUIREMENTS_UPDATE.md)

El **Sistema de Polling de APIs** ha completado su especificación completa y está listo para implementación:

**Spec Completado:**
- ✅ **Requirements Document**: 12 requerimientos funcionales detallados
- ✅ **Design Document**: Arquitectura completa con 20 propiedades de correctitud
- ✅ **Implementation Plan**: 19 tareas organizadas en 4 fases con checkpoints

**Estado de Implementación:**
- 🚧 **Task 1 (QUEUED)**: Configurar infraestructura base con Terraform
  - Módulo DynamoDB para tabla de control
  - Módulo S3 para staging
  - Módulo SNS para notificaciones
  - Roles y políticas IAM
  - Soporte para LocalStack

**Componentes Principales:**
- ✅ **EventBridge Scheduling**: 5 reglas programadas con intervalos específicos
- ✅ **MWAA (Airflow 2.7.2)**: Orquestación event-driven con Python 3.11
- ✅ **DynamoDB Control Table**: Gestión de estado y locks para prevenir ejecuciones concurrentes
- ✅ **Kinesis Firehose**: Entrega de datos validados al Data Lake
- ✅ **Rate Limiting**: 100 requests/minuto con retry exponencial
- ✅ **Polling Incremental**: Solo obtiene datos nuevos o modificados
- ✅ **Data Enrichment**: Obtención paralela de entidades relacionadas
- ✅ **LocalStack Compatible**: Testing local completo

**Schedules Configurados:**
- Orders: Cada 5 minutos
- Products: Cada 1 hora
- Stock: Cada 10 minutos
- Prices: Cada 30 minutos
- Stores: Cada 24 horas

**Requerimientos Clave (12 total):**
1. EventBridge scheduling configuration
2. MWAA environment configuration
3. DynamoDB state management
4. Incremental polling logic
5. API client with rate limiting
6. Pagination handling with circuit breaker
7. Data enrichment (orders → items, products → SKUs)
8. Data validation (schema + business rules)
9. Kinesis Firehose delivery
10. LocalStack compatibility
11. Error handling and recovery
12. Monitoring and observability

**Flujo de Ejecución:**
```
EventBridge → MWAA DAG → Acquire Lock → Poll API → Validate → Enrich → Kinesis → Release Lock
```

**Próximos Pasos:**
1. Completar design document con arquitectura detallada
2. Definir correctness properties para testing
3. Implementar componentes (cliente API, paginación, validación)
4. Crear DAGs de Airflow para 5 tipos de datos
5. Testing con LocalStack

**Documentación:**
- [requirements.md](.kiro/specs/api-polling-system/requirements.md) - Requerimientos completos ✅
- [design.md](.kiro/specs/api-polling-system/design.md) - Design document ✅
- [tasks.md](.kiro/specs/api-polling-system/tasks.md) - Plan de implementación ✅
- [Sistema de Polling de APIs - Resumen.md](Documentación%20Cenco/Sistema%20de%20Polling%20de%20APIs%20-%20Resumen.md) - Resumen ejecutivo ⭐

### Silver-to-Gold Pipeline Integrated (19 de Febrero, 2026)

**Documentos Nuevos**: 
- [INTEGRACION_SILVER_TO_GOLD_MAX.md](Documentacion/INTEGRACION_SILVER_TO_GOLD_MAX.md) - Resumen de integración
- [RESUMEN_INTEGRACION_19_FEB_2026.md](Documentacion/RESUMEN_INTEGRACION_19_FEB_2026.md) - Trabajo completado hoy ⭐

Se ha integrado el **pipeline ETL Silver-to-Gold** que transforma datos limpios hacia datos agregados y optimizados para análisis:

**Módulos Integrados (6):**
- ✅ **IncrementalProcessor**: Procesamiento incremental (solo datos nuevos)
- ✅ **SilverToGoldAggregator**: Agregaciones de métricas de negocio
- ✅ **DenormalizationEngine**: Joins con tablas de dimensiones
- ✅ **DataQualityValidator**: Validación de calidad en 4 dimensiones
- ✅ **ErrorHandler**: Manejo robusto con DLQ y retry logic
- ✅ **DataLineageTracker**: Trazabilidad completa de datos

**Capacidades Nuevas:**
- Procesamiento incremental con metadata tracking
- Agregaciones pre-calculadas (sum, avg, min, max, count)
- Dimensiones de tiempo (year, month, day, week)
- Quality gates configurables
- Dead Letter Queue para registros fallidos
- Reportes de lineage en JSON

**Flujo Completo:**
```
Silver (JSON limpio)
    ↓ IncrementalProcessor (filtra nuevos)
    ↓ SilverToGoldAggregator (agrega métricas)
    ↓ DenormalizationEngine (joins)
    ↓ DataQualityValidator (valida)
    ↓ ErrorHandler (maneja errores)
    ↓ DataLineageTracker (auditoría)
    ↓
Gold (JSON agregado) → Redshift
```

**Ejecutar Pipeline:**
```bash
cd glue
python scripts/run_pipeline_to_gold.py
```

**Documentación Relacionada:**
- [RESUMEN_INTEGRACION_19_FEB_2026.md](Documentacion/RESUMEN_INTEGRACION_19_FEB_2026.md) - Resumen del trabajo de hoy ⭐
- [SILVER_TO_GOLD_MODULOS.md](Documentacion/SILVER_TO_GOLD_MODULOS.md) - Documentación técnica detallada
- [INTEGRACION_SILVER_TO_GOLD_MAX.md](Documentacion/INTEGRACION_SILVER_TO_GOLD_MAX.md) - Resumen de integración
- [.kiro/specs/etl-silver-to-gold/](. kiro/specs/etl-silver-to-gold/) - Especificación completa
- [glue/config/silver-to-gold-config.json](glue/config/silver-to-gold-config.json) - Configuración

### Pipeline with Schema Mapping Implemented (19 de Febrero, 2026)

**Documento Nuevo**: [PIPELINE_CON_MAPEO_ESQUEMA.md](Documentacion/PIPELINE_CON_MAPEO_ESQUEMA.md)

Se ha implementado un **pipeline completo con mapeo de esquema** que transforma datos de la API de Janis a tablas Redshift:

**Logros:**
- ✅ **Mapeo completo a 3 tablas**: wms_orders, wms_order_items, wms_order_shipping
- ✅ **26 campos mapeados en wms_orders** (69.2% completitud)
- ✅ **11 campos mapeados en wms_order_items** (90.9% completitud)
- ✅ **12 campos mapeados en wms_order_shipping** (91.7% completitud)
- ✅ **Transformaciones aplicadas**: Limpieza, normalización, conversión de tipos
- ✅ **Datos reales probados**: Orden 6913fcb6d134afc8da8ac3dd de API Janis
- ✅ **Archivos CSV generados**: Listos para carga a Redshift

**Archivos Generados:**
- `order_{id}_raw.json` - Datos crudos de la API
- `order_{id}_wms_orders.csv` - Tabla principal de órdenes
- `order_{id}_wms_order_items.csv` - Tabla de items
- `order_{id}_wms_order_shipping.csv` - Tabla de envíos

**Módulos Utilizados:**
- DataCleaner (limpieza de datos)
- DataNormalizer (normalización de emails, teléfonos)
- DataTypeConverter (conversión de tipos numéricos)
- DataGapHandler (manejo de campos vacíos)

**Próximos Pasos:**
1. Escalar a múltiples órdenes (paginación)
2. Integrar con PySpark para AWS Glue
3. Escribir a Iceberg con IcebergWriter
4. Agregar más tablas (products, stock, prices)

**Ejecutar Pipeline:**
```bash
cd glue
python scripts/pipeline_with_schema_mapping.py
```

### API Integration Validated (19 de Febrero, 2026)

**Documento Nuevo**: [PRUEBA_EXITOSA_API_JANIS.md](Documentacion/PRUEBA_EXITOSA_API_JANIS.md)

La **conexión con la API real de Janis** se ha validado exitosamente:

**Logros:**
- ✅ **Endpoint correcto identificado**: `https://oms.janis.in/api/order/{order_id}`
- ✅ **Autenticación funcionando**: Headers janis-client, janis-api-key, janis-api-secret
- ✅ **Pipeline probado con datos reales**: Transformaciones aplicadas exitosamente
- ✅ **Estructura de datos mapeada**: Campos principales identificados
- ✅ **Scripts de testing creados**: `test_pipeline_janis_api.py` y `test_janis_api_endpoints.py`

**Archivos Generados:**
- `glue/data/janis_order_raw.json` - Datos crudos de la API
- `glue/data/janis_order_flattened.csv` - Datos aplanados
- `glue/data/janis_order_transformed.csv` - Datos transformados

**Transformaciones Validadas:**
- JSON aplanado (estructuras anidadas → columnas planas)
- Limpieza de datos (espacios, encoding)
- Normalización (emails, teléfonos, fechas)
- Conversión de tipos (strings → timestamps, números)

**Próximos Pasos:**
1. Obtener múltiples órdenes (endpoint de listado + paginación)
2. Mapeo completo de campos (Janis API → wms_orders/items)
3. Integrar en pipeline completo con PySpark
4. Testing con volumen (100+ órdenes)

**Ejecutar Prueba:**
```bash
cd glue
python scripts/test_pipeline_janis_api.py
```

### Phase 1.1 Integration Complete (19 de Febrero, 2026)

**Documento Nuevo**: [FASE_1.1_RESULTADO_INTEGRACION.md](Documentacion/FASE_1.1_RESULTADO_INTEGRACION.md)

La **Fase 1.1 de integración** se ha completado exitosamente:

**Módulos Integrados (4):**
- ✅ **JSONFlattener**: Aplanamiento de estructuras JSON anidadas
- ✅ **DataCleaner**: Limpieza de datos (trim, nulls, encoding)
- ✅ **DuplicateDetector**: Detección de duplicados por business keys
- ✅ **ConflictResolver**: Resolución de conflictos en duplicados

**Tests Creados:**
- ✅ **23 unit tests** implementados (4 archivos de test)
- ✅ **Scripts de testing** para Windows y Linux
- ✅ **Validación de imports** completada

**Estado:**
- ✅ Código copiado correctamente a `glue/modules/`
- ✅ Sin conflictos con código existente de Vicente
- ✅ Documentación completa generada
- ✅ Listo para Fase 1.2 (fusión de módulos duplicados)

**Próximos Pasos:**
1. **Fase 1.2**: Fusionar módulos duplicados (DataTypeConverter, DataNormalizer, DataGapHandler)
2. **Fase 1.3**: Integrar pipeline completo
3. **Tests de integración** end-to-end

**Tiempo estimado para Fase 1.2:** 4-6 horas

**Documentación Relacionada:**
- [FASE_1.1_INTEGRACION_MODULOS_MAX.md](Documentacion/FASE_1.1_INTEGRACION_MODULOS_MAX.md) - Documentación completa
- [ESTADO_MODULOS_INTEGRACION.md](Documentacion/ESTADO_MODULOS_INTEGRACION.md) - Estado de todos los módulos
- [ESTADO_TESTING_INTEGRACION.md](Documentacion/ESTADO_TESTING_INTEGRACION.md) - Estado de testing
- [RESULTADOS_PRUEBA_MAX.md](Documentacion/RESULTADOS_PRUEBA_MAX.md) - Validación del pipeline de Max

### Production Deployment Verified (5 de Febrero, 2026)

**Documento Nuevo**: [TERRAFORM_DEPLOYMENT_VERIFICATION.md](TERRAFORM_DEPLOYMENT_VERIFICATION.md)

La infraestructura Terraform ha sido **verificada exitosamente en configuración de producción**:

- ✅ **141 recursos desplegados y destruidos** exitosamente
- ✅ **100% compliance** con Spec 1 (61/61 requisitos aplicables)
- ✅ **Configuración de producción** (`terraform.tfvars.prod`) validada
- ✅ **Lifecycle completo** probado (plan → apply → verify → destroy)
- ✅ **Código production-ready** confirmado

**Recursos Validados:**
- 15 recursos de VPC & Networking
- 7 Security Groups
- 7 VPC Endpoints (1 Gateway + 6 Interface)
- 5 S3 Buckets + 20 configuraciones
- 3 Glue Databases
- 1 Kinesis Firehose Stream
- 6 componentes EventBridge
- 15+ componentes de Monitoring
- 12 IAM Roles & Policies
- 2 Network ACLs

**Costos Estimados**: ~$145-185/mes (infraestructura base, sin compute)

**Estado**: ✅ **PRODUCTION READY - LISTO PARA ENTREGA AL CLIENTE**

### Spec 1 Compliance Verification (4 de Febrero, 2026)

**Documento Nuevo**: [SPEC_1_COMPLIANCE_VERIFICATION.md](SPEC_1_COMPLIANCE_VERIFICATION.md)

La infraestructura Terraform ha sido **verificada al 100%** contra los requisitos del Spec 1 de AWS Infrastructure:

- ✅ **61 de 61 requisitos aplicables cumplidos** (100%)
- ✅ **5 excepciones explícitas del cliente** (WAF y CloudTrail - Cencosud los configura)
- ✅ **Evidencia de código documentada** para cada requisito
- ✅ **Checklist pre-deployment** completo
- ✅ **Notas importantes** para producción documentadas

**Estado**: ✅ **LISTO PARA ENVIAR A CENCOSUD**

### AWS Infrastructure Deployed and Validated (30 de Enero, 2026)

La infraestructura AWS ha sido **desplegada exitosamente y validada** contra la especificación 01-aws-infrastructure.

📊 **[AWS_INFRASTRUCTURE_VALIDATION_REPORT.md](AWS_INFRASTRUCTURE_VALIDATION_REPORT.md)** - Reporte completo de validación

**Resultados del Deployment:**
- **71 recursos desplegados** en AWS (vs 70 planeados)
- **93.75% compliance** (45/48 requisitos cumplidos)
- **Cuenta AWS**: 827739413930 (Vicente_testing)
- **Región**: us-east-1 (Single-AZ: us-east-1a)
- **Costos**: ~$35-50/mes (testing configuration)

**Estado:** ✅ Infraestructura operacional y lista para siguiente fase

### AWS Deployment Plan Generated (30 de Enero, 2026)

Se ha generado exitosamente el plan de deployment para AWS con **70 recursos a crear**.

📖 **[terraform/AWS_PLAN_SUMMARY.md](terraform/AWS_PLAN_SUMMARY.md)** - Resumen detallado del plan ⭐ NUEVO

**Desglose del Plan:**
- 15 recursos de VPC (VPC, subnets, IGW, NAT Gateway, Route Tables)
- 28 recursos de Security Groups (7 grupos + 21 reglas)
- 10 recursos de EventBridge (Event Bus, 5 rules, DLQ, IAM roles)
- 16 recursos de Monitoring (VPC Flow Logs, CloudWatch alarms, metric filters)
- 1 recurso de VPC Endpoints (S3 Gateway)

**Costos Estimados:** ~$35-50/mes (Single-AZ, dependiendo del tráfico)

**Estado:** ✅ Plan listo para apply - Ver AWS_PLAN_SUMMARY.md para checklist completo

### AWS Deployment Ready (30 de Enero, 2026)

El sistema está **completamente preparado para deployment en AWS real** y ha sido **desplegado y validado exitosamente**.

📊 **[AWS_INFRASTRUCTURE_VALIDATION_REPORT.md](AWS_INFRASTRUCTURE_VALIDATION_REPORT.md)** - Reporte de validación completo ⭐ NUEVO  
📖 **[AWS_DEPLOYMENT_READINESS_UPDATE.md](AWS_DEPLOYMENT_READINESS_UPDATE.md)** - Estado de preparación  
📖 **[terraform/READY_FOR_AWS.md](terraform/READY_FOR_AWS.md)** - Guía completa de deployment  
📖 **[TERRAFORM_AWS_READY.md](TERRAFORM_AWS_READY.md)** - Resumen ejecutivo

**Estado Actual:**
- ✅ Infraestructura desplegada en AWS (71 recursos)
- ✅ Validación completada (93.75% compliance)
- ✅ Cuenta AWS verificada (Account: 827739413930)
- ✅ Todos los componentes core operacionales
- ✅ Monitoreo y alarmas activas

**Próximos Pasos:**
1. Completar Task 18 (configuraciones por ambiente)
2. Desplegar API Gateway y Lambda functions
3. Configurar MWAA (Airflow)
4. Implementar Glue jobs

**Impacto:** Sistema operacional en AWS. Infraestructura base completada exitosamente.

### NACLs Module Improvement (29 de Enero, 2026)

El módulo de NACLs ha sido mejorado para usar **asociaciones explícitas de subnets**, mejorando la gestión del state de Terraform y reduciendo conflictos.

📖 **[NACL_IMPROVEMENT_SUMMARY.md](NACL_IMPROVEMENT_SUMMARY.md)** - Resumen rápido  
📖 **[terraform/modules/nacls/README.md](terraform/modules/nacls/README.md)** - Documentación completa

**Beneficios:**
- ✅ Mejor gestión del state de Terraform
- ✅ Reducción de conflictos de estado
- ✅ Tracking más claro de cambios
- ✅ Alineación con AWS best practices

**Impacto:** Refactorización interna sin cambios funcionales. Migración de state requerida en deployments existentes.

## 🧪 Testing Local con LocalStack

Puedes probar toda la infraestructura localmente sin costos usando LocalStack:

```powershell
# 1. Iniciar LocalStack
docker-compose -f docker-compose.localstack.yml up -d

# 2. Desplegar infraestructura
.\scripts\deploy-localstack.ps1 -Action init
.\scripts\deploy-localstack.ps1 -Action apply

# 3. Ver recursos creados
.\scripts\deploy-localstack.ps1 -Action output
```

📖 **[GUIA_LOCALSTACK.md](GUIA_LOCALSTACK.md)** - Guía completa de LocalStack

## 📁 Estructura del Proyecto

```
janis-cencosud-integration/
├── GUIA_COMPARTIR_PROYECTO.md    # 👈 EMPIEZA AQUÍ
├── terraform/                     # Infraestructura como código
│   ├── environments/              # Configuraciones por ambiente
│   │   ├── dev/
│   │   ├── staging/
│   │   └── prod/
│   ├── modules/                   # Módulos reutilizables
│   ├── test/                      # Tests automatizados
│   └── scripts/                   # Scripts de deployment
├── glue/                          # Módulos de transformación de datos (Vicente + Max integrados)
│   ├── modules/                   # Paquete Python de transformaciones
│   │   ├── __init__.py            # Inicialización del paquete
│   │   ├── iceberg_manager.py     # Gestión de tablas Apache Iceberg
│   │   ├── iceberg_writer.py      # Escritura de datos a Iceberg
│   │   ├── schema_evolution_manager.py # Gestión de evolución de esquemas
│   │   ├── data_type_converter.py # Conversiones MySQL → Redshift (fusionado)
│   │   ├── data_normalizer.py     # Normalización de formatos (fusionado)
│   │   ├── data_gap_handler.py    # Manejo de campos faltantes (fusionado)
│   │   ├── json_flattener.py      # Aplanamiento de JSON anidado (Max)
│   │   ├── data_cleaner.py        # Limpieza de datos (Max)
│   │   ├── duplicate_detector.py  # Detección de duplicados (Max)
│   │   ├── conflict_resolver.py   # Resolución de conflictos (Max)
│   │   └── silver_to_gold/        # Módulos Silver-to-Gold ETL (Max)
│   │       ├── __init__.py
│   │       ├── incremental_processor.py     # Procesamiento incremental
│   │       ├── silver_to_gold_aggregator.py # Agregaciones de negocio
│   │       ├── denormalization_engine.py    # Desnormalización
│   │       ├── data_quality_validator.py    # Validación de calidad
│   │       ├── error_handler.py             # Manejo de errores y DLQ
│   │       └── data_lineage_tracker.py      # Trazabilidad de datos
│   ├── config/                    # Configuraciones de pipelines
│   │   └── silver-to-gold-config.json # Config Silver-to-Gold
│   ├── scripts/                   # Scripts de ejecución
│   │   ├── etl_pipeline_gold.py   # Orquestador Silver-to-Gold
│   │   ├── run_pipeline_to_gold.py # Ejecución local Silver-to-Gold
│   │   ├── pipeline_with_schema_mapping.py # Pipeline con mapeo Redshift
│   │   ├── test_pipeline_local.py # Test con datos simulados
│   │   └── test_pipeline_janis_api.py # Test con API real
│   ├── tests/                     # Tests automatizados
│   │   ├── unit/                  # Unit tests
│   │   │   ├── test_duplicate_detector.py
│   │   │   └── test_conflict_resolver.py
│   │   └── property/              # Property-based tests con Hypothesis
│   │       ├── test_iceberg_roundtrip.py  # Validación write-read
│   │       ├── test_iceberg_acid.py       # Validación ACID
│   │       ├── test_iceberg_timetravel.py # Validación time travel
│   │       └── test_schema_evolution.py   # Validación schema evolution
│   └── README.md                  # Documentación de módulos
├── max/                           # Pipeline Bronze-to-Silver (Max - validado)
│   ├── src/
│   │   ├── modules/               # 10 módulos de transformación
│   │   │   ├── json_flattener.py  # Aplanamiento de JSON anidado
│   │   │   ├── data_cleaner.py    # Limpieza de datos
│   │   │   ├── data_normalizer.py # Normalización de formatos
│   │   │   ├── data_type_converter.py # Conversión de tipos
│   │   │   ├── duplicate_detector.py # Detección de duplicados
│   │   │   ├── conflict_resolver.py # Resolución de conflictos
│   │   │   ├── data_gap_handler.py # Manejo de gaps
│   │   │   ├── iceberg_table_manager.py # Gestión de tablas
│   │   │   └── iceberg_writer.py  # Escritura a Iceberg
│   │   ├── config/                # Configuración JSON
│   │   └── etl_pipeline.py        # Orquestador del pipeline
│   ├── tests/                     # Tests y datos de prueba
│   │   └── fixtures/              # Datos de prueba
│   ├── terraform/                 # Infraestructura LocalStack
│   ├── run_pipeline_to_silver.py  # Script de ejecución
│   ├── INICIO_RAPIDO.md           # Guía de inicio rápido
│   └── README.md                  # Documentación completa
├── .kiro/specs/                   # Especificaciones detalladas
├── scripts/                       # Scripts de utilidad
├── Documentacion/                 # Documentación del proyecto
│   ├── ESTADO_TESTING_INTEGRACION.md # Estado de testing e integración ⭐ NUEVO
│   ├── RESULTADOS_PRUEBA_MAX.md   # Resultados de validación de Max
│   ├── ANALISIS_COMPARATIVO_MAX_VICENTE.md # Análisis comparativo
│   └── PLAN_INTEGRACION_MAX_VICENTE.md # Plan de integración
└── Documentación Cenco/           # Documentación del proyecto
```

## 📚 Documentación Principal

### 🎉 Trabajo Completado Hoy (19 Feb 2026)

**[RESUMEN_INTEGRACION_19_FEB_2026.md](Documentacion/RESUMEN_INTEGRACION_19_FEB_2026.md)** - Resumen completo del trabajo de hoy ⭐

**Logros del día:**
- ✅ Pipeline Silver-to-Gold integrado (6 módulos nuevos)
- ✅ Especificación completa documentada
- ✅ Scripts de ejecución implementados
- ✅ Configuración JSON creada
- ✅ Documentación técnica exhaustiva

### Guías de Usuario
- **[GUIA_COMPARTIR_PROYECTO.md](GUIA_COMPARTIR_PROYECTO.md)** - Cómo ejecutar el proyecto (EMPIEZA AQUÍ)
- **[Guia proyecto Terraform Cencosud.md](Guia%20proyecto%20Terraform%20Cencosud.md)** - Guía completa de implementación y deployment ⭐ NUEVO
- **[GUIA_DEPLOYMENT_CENCOSUD.md](GUIA_DEPLOYMENT_CENCOSUD.md)** - Guía oficial de deployment para Cencosud
- **[GUIA_LANDING_ZONE_CLIENTE.md](GUIA_LANDING_ZONE_CLIENTE.md)** - Uso de Landing Zone existente del cliente
- **[CONFIGURACION_CLIENTE.md](CONFIGURACION_CLIENTE.md)** - Configuración requerida del cliente antes del deployment
- **[SOLICITUD_PERMISOS_AWS_CLIENTE.md](SOLICITUD_PERMISOS_AWS_CLIENTE.md)** - Solicitud de permisos AWS read-only para soporte técnico
- **[Documentación Cenco/Guía de Validación y Deployment.md](Documentación%20Cenco/Guía%20de%20Validación%20y%20Deployment.md)** - Validación y deployment paso a paso
- **[terraform/READY_FOR_AWS.md](terraform/READY_FOR_AWS.md)** - Guía completa de deployment a AWS real
- **[TERRAFORM_AWS_READY.md](TERRAFORM_AWS_READY.md)** - Resumen ejecutivo de AWS readiness
- **[terraform/DEPLOYMENT_GUIDE.md](terraform/DEPLOYMENT_GUIDE.md)** - Guía rápida de deployment
- **[terraform/GUIA_DEPLOYMENT_TESTING.md](terraform/GUIA_DEPLOYMENT_TESTING.md)** - Deployment en ambiente de testing
- **[terraform/README.md](terraform/README.md)** - Documentación completa de Terraform
- **[README-LOCALSTACK.md](README-LOCALSTACK.md)** - Testing local sin costos
- **[LOCALSTACK_TROUBLESHOOTING.md](LOCALSTACK_TROUBLESHOOTING.md)** - Soluciones a problemas de LocalStack

### Documentación Técnica
- **[terraform/DOCUMENTATION_INDEX.md](terraform/DOCUMENTATION_INDEX.md)** - Índice completo de documentación
- **[terraform/test/VALIDATION_GUIDE.md](terraform/test/VALIDATION_GUIDE.md)** - Guía de validación y testing
- **[terraform/scripts/README.md](terraform/scripts/README.md)** - Scripts automatizados
- **[Documento Detallado de Diseño Janis-Cenco.md](Documento%20Detallado%20de%20Diseño%20Janis-Cenco.md)** - Arquitectura completa
- **[diagrama-infraestructura-terraform.md](diagrama-infraestructura-terraform.md)** - Diagrama visual ASCII de infraestructura
- **[diagrama-mermaid.md](diagrama-mermaid.md)** - Diagramas Mermaid interactivos (múltiples vistas) ⭐
- **[Documentación Cenco/Diagrama arquitectura.md](Documentación%20Cenco/Diagrama%20arquitectura.md)** - Diagrama principal en formato Mermaid ⭐
- **[Documentacion/SILVER_TO_GOLD_MODULOS.md](Documentacion/SILVER_TO_GOLD_MODULOS.md)** - Módulos Silver-to-Gold ETL ⭐ NUEVO

## 🎯 ¿Qué Hace Este Proyecto?

Este proyecto despliega la infraestructura AWS necesaria para:

- **Ingesta de Datos**: Webhooks y polling de API Janis
- **Procesamiento**: Transformaciones ETL con AWS Glue
- **Almacenamiento**: Data Lake (S3) y Data Warehouse (Redshift)
- **Orquestación**: EventBridge + MWAA (Apache Airflow)
- **Seguridad**: VPC, Security Groups, WAF, cifrado

### Componentes Principales

- **VPC Multi-AZ** con subnets públicas y privadas
- **7 Security Groups** con reglas específicas por servicio
- **7 VPC Endpoints** para comunicación privada con servicios AWS
- **Network ACLs** para seguridad adicional de red
- **AWS WAF** con protección contra ataques comunes
- **EventBridge** para orquestación de polling
- **Monitoring** con CloudWatch y VPC Flow Logs

## 🧪 Testing Local (Sin Costos AWS)

Puedes probar la infraestructura localmente usando LocalStack:

```powershell
# 1. Iniciar LocalStack
docker-compose -f docker-compose.localstack.yml up -d

# 2. Desplegar infraestructura completa
cd terraform
terraform init
terraform apply -var-file="localstack.tfvars" -auto-approve

# 3. Verificar recursos
aws --endpoint-url=http://localhost:4566 ec2 describe-vpcs

# 4. Limpiar
terraform destroy -var-file="localstack.tfvars" -auto-approve
docker-compose -f docker-compose.localstack.yml down
```

**⚠️ Nota sobre LocalStack**: LocalStack es útil para desarrollo rápido, pero tiene limitaciones importantes:
- Operaciones muy lentas (5+ minutos vs segundos en AWS real)
- Algunos recursos pueden atascarse durante deployment
- No representa el comportamiento real de AWS

**📖 Resultados de Testing**: Ver [terraform/DEPLOYMENT_STATUS_FINAL.md](terraform/DEPLOYMENT_STATUS_FINAL.md) para análisis completo de qué funciona y qué no en LocalStack.

**Recomendación**: Para testing de infraestructura, usa AWS real. LocalStack es mejor para desarrollo de aplicaciones.

Ver **[README-LOCALSTACK.md](README-LOCALSTACK.md)** para guía completa.

## 💰 Costos Estimados

### Ambiente de Testing (Single-AZ, Configuración Simplificada)
- NAT Gateway: ~$32 USD/mes
- VPC Flow Logs: ~$5 USD/mes
- EventBridge: ~$1 USD/mes
- CloudWatch: ~$2 USD/mes
- **Total: ~$40 USD/mes**

Ver [terraform/GUIA_DEPLOYMENT_TESTING.md](terraform/GUIA_DEPLOYMENT_TESTING.md) para detalles.

### Ambiente de Desarrollo (Single-AZ, Configuración Completa)
- NAT Gateway: ~$32 USD/mes
- VPC Endpoints (7): ~$50 USD/mes
- VPC Flow Logs: ~$10 USD/mes
- CloudWatch: ~$5 USD/mes
- **Total: ~$97 USD/mes**

### Ambiente de Producción (Multi-AZ)
- Costos adicionales por redundancia
- Ver documentación para desglose completo

## 🔧 Comandos Útiles

### Validación (Sin Crear Recursos)
```powershell
cd terraform
terraform fmt -recursive          # Formatear código
terraform validate                # Validar sintaxis
terraform plan -var-file="..."    # Ver qué se va a crear
```

### Deployment
```powershell
cd terraform
terraform init                                    # Inicializar (primera vez)
terraform apply -var-file="environments/dev/dev.tfvars"  # Crear recursos
```

### Verificación
```powershell
terraform output                  # Ver outputs
terraform state list              # Listar recursos creados
aws ec2 describe-vpcs             # Verificar VPC en AWS
```

### Limpieza
```powershell
terraform destroy -var-file="environments/dev/dev.tfvars"  # Eliminar recursos
```

## 🛠️ Scripts Automatizados

El proyecto incluye scripts para facilitar operaciones comunes:

```powershell
# Preparar proyecto para compartir
.\scripts\preparar-para-compartir.ps1

# Inicializar ambiente nuevo
cd terraform/scripts
.\init-environment.sh dev

# Deployment automatizado con validaciones
.\deploy.sh dev

# Backup del state
.\backup-state.sh dev
```

Ver **[terraform/scripts/README.md](terraform/scripts/README.md)** para más detalles.

### Scripts de Inventario AWS

El proyecto incluye 6 scripts PowerShell especializados para generar inventarios completos de recursos AWS y análisis de permisos:

#### Scripts de Inventario de Recursos

**1. inventario-aws-recursos.ps1** - Inventario completo con detalles
   - Genera archivos JSON y Markdown con información detallada
   - Analiza 15+ tipos de recursos AWS
   - Incluye configuraciones, tags y estado de cada recurso
   - Salida: `inventario-aws-cencosud-YYYYMMDD-HHMMSS.json` y `.md`

**2. inventario-rapido.ps1** - Resumen rápido en consola
   - Vista rápida de conteo de recursos por servicio
   - Ideal para validación rápida post-deployment
   - No genera archivos, solo output en consola
   - Tiempo de ejecución: ~30 segundos

**3. generar-inventario.ps1** - Wrapper simplificado
   - Interfaz simplificada para generar inventarios
   - Detecta automáticamente perfil y región
   - Genera ambos formatos (JSON + Markdown)

#### Scripts de Análisis de Permisos

**4. inventario-permisos.ps1** - Análisis detallado de permisos IAM
   - Analiza roles, policies y permisos efectivos
   - Identifica permisos por servicio AWS
   - Genera matriz de permisos (Read/Write/Delete/Execute)
   - Salida: `inventario-permisos-YYYYMMDD-HHMMSS.json` y `.md`

**5. analizar-permisos-efectivos.ps1** - Análisis profundo
   - Analiza permisos efectivos combinando inline y managed policies
   - Identifica permisos wildcards y específicos
   - Genera reporte detallado por rol y servicio
   - Incluye recomendaciones de seguridad

**6. test-permisos.ps1** - Validación rápida de permisos
   - Prueba permisos específicos contra recursos reales
   - Valida acceso Read/Write/Delete por servicio
   - Útil para troubleshooting de permisos
   - Genera reporte de permisos faltantes

#### Uso Rápido

```powershell
# Inventario completo de recursos
.\scripts\inventario-aws-recursos.ps1 -Profile cencosud -Region us-east-1

# Resumen rápido en consola
.\scripts\inventario-rapido.ps1

# Análisis completo de permisos IAM
.\scripts\inventario-permisos.ps1 -Profile cencosud

# Análisis profundo de permisos efectivos
.\scripts\analizar-permisos-efectivos.ps1 -Profile cencosud

# Validación rápida de permisos
.\scripts\test-permisos.ps1 -Profile cencosud -Service s3

# Wrapper simplificado
.\scripts\generar-inventario.ps1
```

#### Recursos Analizados

**Servicios de Datos:**
- S3 Buckets (configuración, versioning, encryption, lifecycle)
- Redshift Clusters (configuración, snapshots, parameter groups)
- AWS Glue (Databases, Tables, Jobs, Crawlers, Connections)

**Servicios de Compute:**
- Lambda Functions (configuración, layers, environment variables)
- API Gateway (REST APIs, stages, deployments)

**Servicios de Streaming:**
- Kinesis Firehose (delivery streams, destinations, buffering)

**Servicios de Red:**
- VPC (configuración, CIDR blocks, DNS settings)
- Subnets (públicas/privadas, availability zones)
- Security Groups (reglas inbound/outbound)
- VPC Endpoints (tipo, servicios, subnets)

**Servicios de Orquestación:**
- EventBridge Rules (schedules, targets, estado)
- MWAA (Airflow environments, configuración)

**Servicios de Seguridad:**
- IAM Roles (trust policies, attached policies)
- Secrets Manager (secretos, rotación)

**Servicios de Monitoreo:**
- CloudWatch Log Groups (retention, métricas)
- CloudWatch Alarms (thresholds, acciones)

#### Análisis de Permisos

Los scripts de permisos analizan y categorizan permisos en 4 tipos:

- **Read**: Permisos de lectura (Get*, List*, Describe*)
- **Write**: Permisos de escritura (Put*, Create*, Update*)
- **Delete**: Permisos de eliminación (Delete*, Remove*)
- **Execute**: Permisos de ejecución (Invoke*, Run*, Start*)

**Matriz de Permisos por Servicio:**
- S3, Lambda, Glue, Redshift, Kinesis, API Gateway
- VPC, EC2, EventBridge, CloudWatch, Secrets Manager
- IAM, KMS, SNS, SQS, Step Functions

#### Documentación Completa

- **[INVENTARIO_Y_PERMISOS_AWS.md](INVENTARIO_Y_PERMISOS_AWS.md)** - Inventario consolidado y análisis completo de permisos ⭐ NUEVO
- **[scripts/README-INVENTARIO.md](scripts/README-INVENTARIO.md)** - Documentación completa de scripts de inventario
- **[Documentación Cenco/Scripts de Inventario AWS - Resumen.md](Documentación%20Cenco/Scripts%20de%20Inventario%20AWS%20-%20Resumen.md)** - Resumen ejecutivo de scripts

#### Casos de Uso

1. **Post-Deployment Validation**: Verificar que todos los recursos se crearon correctamente
2. **Troubleshooting**: Identificar recursos faltantes o mal configurados
3. **Security Audit**: Analizar permisos IAM y identificar sobre-permisos
4. **Documentation**: Generar documentación actualizada de infraestructura
5. **Cost Analysis**: Identificar recursos que generan costos
6. **Compliance**: Verificar tags, encryption y configuraciones de seguridad

## 🧪 Testing y Validación

### Validación de Infraestructura (Terraform)

#### Validación Rápida (Sin Credenciales)
```powershell
cd terraform/test
.\validate_infrastructure.ps1
```

#### Validación Completa (Con Credenciales)
```powershell
cd terraform
terraform plan -var-file="environments/dev/dev.tfvars"
```

#### Property Tests (Go)
```powershell
cd terraform/test
go test -v -timeout 30m
```

Ver **[terraform/test/VALIDATION_GUIDE.md](terraform/test/VALIDATION_GUIDE.md)** para guía completa.

### Testing de Transformaciones de Datos (Glue)

#### Estado Actual de Testing

**⚠️ IMPORTANTE**: Los componentes están testeados individualmente pero **NO integrados**. Ver [ESTADO_TESTING_INTEGRACION.md](Documentacion/ESTADO_TESTING_INTEGRACION.md) para detalles completos.

#### Property-Based Tests con Hypothesis (Módulos de Vicente)

El proyecto incluye tests de propiedades exhaustivos para validar la integridad de datos en Apache Iceberg:

```bash
# Ejecutar todos los tests de propiedades
pytest glue/tests/property/ -v --hypothesis-show-statistics

# Ejecutar test específico de write-read round trip
pytest glue/tests/property/test_iceberg_roundtrip.py -v

# Ejecutar con marker de property tests
pytest -m property -v
```

**Tests Implementados:**

| Test | Property | Validación | Estado |
|------|----------|------------|--------|
| `test_iceberg_roundtrip.py` | Property 5 | Write-Read Round Trip | ✅ Pasando (100+ casos) |
| `test_iceberg_acid.py` | Property 11 | ACID Transactions | ✅ Pasando (50+ casos) |
| `test_iceberg_timetravel.py` | Property 12 | Time Travel Snapshots | ✅ Pasando (50+ casos) |
| `test_schema_evolution.py` | Properties 15-20 | Schema Evolution | ✅ Implementado (6 properties) |

**⚠️ Limitación en Windows**: Los tests de PySpark no se pueden ejecutar completamente en Windows debido a problemas de serialización. Los tests funcionan correctamente en Linux (AWS Glue).

#### Pipeline Bronze-to-Silver (Módulos de Max)

El pipeline completo ha sido validado con LocalStack:

```bash
# Ejecutar pipeline completo (requiere LocalStack)
cd max
python run_pipeline_to_silver.py
```

**Pipeline con Mapeo de Esquema (Nuevo):**

Un nuevo pipeline que mapea datos de Janis API a tablas Redshift ha sido implementado:

```bash
# Ejecutar pipeline con mapeo de esquema (requiere API Janis)
cd glue
python scripts/pipeline_with_schema_mapping.py
```

**📖 Ver:** [PIPELINE_CON_MAPEO_ESQUEMA.md](Documentacion/PIPELINE_CON_MAPEO_ESQUEMA.md) para documentación completa del mapeo de campos, transformaciones aplicadas, y análisis de completitud de datos.

#### Pipeline Silver-to-Gold (Módulos de Max)

El pipeline ETL Silver-to-Gold transforma datos limpios hacia datos agregados y optimizados para análisis:

```bash
# Ejecutar pipeline Silver-to-Gold
cd glue
python scripts/run_pipeline_to_gold.py
```

**📖 Ver:** [INTEGRACION_SILVER_TO_GOLD_MAX.md](Documentacion/INTEGRACION_SILVER_TO_GOLD_MAX.md) para documentación completa del pipeline, módulos integrados, y configuración.

**Módulos Validados (Bronze-to-Silver):**

| Módulo | Función | Estado |
|--------|---------|--------|
| JSONFlattener | Aplanar JSON anidado | ✅ Validado |
| DataCleaner | Limpieza de datos | ✅ Validado |
| DataNormalizer | Normalización de formatos | ✅ Validado |
| DataTypeConverter | Conversión de tipos | ✅ Validado |
| DuplicateDetector | Detección de duplicados | ✅ Validado |
| ConflictResolver | Resolución de conflictos | ✅ Validado |
| DataGapHandler | Manejo de gaps | ✅ Validado |
| ETLPipeline | Orquestación | ✅ Validado |

**Resultados**: 12 registros iniciales → 15 (JSONFlattener) → 11 registros finales (4 duplicados resueltos)

**Módulos Integrados (Silver-to-Gold):**

| Módulo | Función | Estado |
|--------|---------|--------|
| IncrementalProcessor | Procesamiento incremental | ✅ Integrado |
| SilverToGoldAggregator | Agregaciones de negocio | ✅ Integrado |
| DenormalizationEngine | Joins con dimensiones | ✅ Integrado |
| DataQualityValidator | Validación de calidad | ✅ Integrado |
| ErrorHandler | Manejo de errores y DLQ | ✅ Integrado |
| DataLineageTracker | Trazabilidad de datos | ✅ Integrado |

**⚠️ Limitación**: Escritura a Iceberg bloqueada en Windows por falta de `winutils.exe`. NO afecta producción (AWS Glue usa Linux).

#### Tests Pendientes

**Integración End-to-End:**
- [ ] Pipeline completo Bronze → Silver con todos los módulos integrados
- [ ] Escritura y lectura desde Iceberg en ambiente real
- [ ] Schema evolution en pipeline real con datos
- [ ] Performance con datasets grandes (>1M registros)

**Módulos Fusionados:**
- [ ] DataTypeConverter (Max + Vicente)
- [ ] DataNormalizer (Max + Vicente)
- [ ] DataGapHandler (Max + Vicente)
- [ ] IcebergManager (Max + Vicente)

**Documentación Completa:**
- **[ESTADO_TESTING_INTEGRACION.md](Documentacion/ESTADO_TESTING_INTEGRACION.md)** - Estado completo de testing e integración ⭐ NUEVO
- **[RESULTADOS_PRUEBA_MAX.md](Documentacion/RESULTADOS_PRUEBA_MAX.md)** - Resultados de validación del pipeline de Max
- **[ANALISIS_COMPARATIVO_MAX_VICENTE.md](Documentacion/ANALISIS_COMPARATIVO_MAX_VICENTE.md)** - Análisis comparativo de implementaciones
- **[PLAN_INTEGRACION_MAX_VICENTE.md](Documentacion/PLAN_INTEGRACION_MAX_VICENTE.md)** - Plan de integración en 3 fases
- **[.kiro/specs/data-transformation/docs/Property-Based Testing - Iceberg Round Trip.md](.kiro/specs/data-transformation/docs/Property-Based%20Testing%20-%20Iceberg%20Round%20Trip.md)** - Guía completa de property-based testing
- **[.kiro/specs/data-transformation/docs/Iceberg Manager - Guía de Uso.md](.kiro/specs/data-transformation/docs/Iceberg%20Manager%20-%20Guía%20de%20Uso.md)** - Documentación del módulo IcebergTableManager

**Características de los Tests:**
- ✅ Generación automática de casos de prueba con Hypothesis
- ✅ Validación exhaustiva de tipos de datos (strings, integers, decimals, timestamps)
- ✅ Cobertura de edge cases (valores nulos, extremos, combinaciones)
- ✅ Verificación de integridad de datos sin pérdida
- ✅ Validación de operaciones append y overwrite
- ✅ Tests de transacciones ACID y time travel
- ⚠️ Integración end-to-end pendiente

## 📦 Compartir Este Proyecto

### Inicio Rápido (5 minutos)

```powershell
# Ejecutar script de preparación
.\scripts\preparar-para-compartir.ps1

# Esto crea: janis-cencosud-compartir.zip
# Compartir el ZIP con la otra persona
```

El script automáticamente:
- ✅ Verifica que no hay archivos sensibles
- ✅ Excluye archivos temporales (.terraform, .tfstate)
- ✅ Incluye toda la documentación necesaria
- ✅ Crea un ZIP listo para compartir

### Documentación Completa para Compartir

Si es tu primera vez compartiendo el proyecto o necesitas más información:

- **[INDICE_COMPARTIR.md](INDICE_COMPARTIR.md)** - Índice completo de documentación
- **[RESUMEN_COMPARTIR.md](RESUMEN_COMPARTIR.md)** - Resumen ejecutivo del proceso
- **[CHECKLIST_COMPARTIR.md](CHECKLIST_COMPARTIR.md)** - Lista de verificación completa
- **[FLUJO_COMPARTIR.md](FLUJO_COMPARTIR.md)** - Diagramas visuales del proceso
- **[TEMPLATE_MENSAJE_COMPARTIR.md](TEMPLATE_MENSAJE_COMPARTIR.md)** - Templates de mensajes

### Subir a GitLab

Para preparar el proyecto para un repositorio GitLab:

- **[GITLAB_PREPARATION.md](GITLAB_PREPARATION.md)** - Guía completa de preparación para GitLab ⭐ NUEVO
  - Archivos a incluir/excluir
  - Estructura final del repositorio
  - Configuración de .gitignore
  - Comandos Git para push inicial
  - Checklist de seguridad

### Para el Receptor

**La otra persona debe leer:** [GUIA_COMPARTIR_PROYECTO.md](GUIA_COMPARTIR_PROYECTO.md)

## 🔐 Seguridad

### ⚠️ IMPORTANTE - NO Compartir

- ❌ Archivos `terraform.tfstate*` (contienen información sensible)
- ❌ Archivos `*.tfplan` (pueden contener secretos)
- ❌ Credenciales AWS (access keys, secret keys)
- ❌ Archivos `terraform.tfvars` con valores reales
- ❌ Directorio `.terraform/` (se regenera con terraform init)

### ✅ Seguro para Compartir

- ✅ Archivos `.tf` (código Terraform)
- ✅ Archivos `.md` (documentación)
- ✅ Scripts `.ps1` y `.sh`
- ✅ Archivo `terraform.tfvars.example` (plantilla)
- ✅ Configuración de módulos

## 🐛 Troubleshooting

### Error: "No valid credential sources found"
```powershell
# Configurar credenciales
$env:AWS_ACCESS_KEY_ID = "tu-access-key"
$env:AWS_SECRET_ACCESS_KEY = "tu-secret-key"

# Verificar
aws sts get-caller-identity
```

### Error: "Error acquiring the state lock"
```powershell
# Esperar a que termine otra operación o forzar unlock
terraform force-unlock <LOCK_ID>
```

### Error: "Insufficient permissions"
Las credenciales AWS necesitan permisos para:
- EC2 (VPC, Subnets, Security Groups)
- VPC Endpoints
- CloudWatch
- EventBridge
- WAF

Ver **[GUIA_COMPARTIR_PROYECTO.md](GUIA_COMPARTIR_PROYECTO.md)** para más soluciones.

## 📖 Especificaciones Técnicas

El proyecto sigue la metodología de Spec-Driven Development. Las especificaciones están en:

```
.kiro/specs/
├── 01-aws-infrastructure/     # Infraestructura base (VPC, redes, EventBridge, WAF)
│   └── docs/                  # Ver README.md para índice completo de documentación
├── 02-initial-data-load/      # Carga inicial de datos desde MySQL a Redshift
│   └── docs/                  # Incluye análisis de esquema Redshift y mapeo detallado
├── integration-max-vicente/   # Integración de pipelines Max y Vicente ⭐ NUEVO
│   ├── requirements.md        # Requisitos de integración
│   ├── design.md              # Design document técnico ⭐ NUEVO
│   └── README.md              # Índice de documentación
├── webhook-ingestion/         # Sistema de webhooks en tiempo real
├── api-polling-system/        # Polling periódico con EventBridge + MWAA
├── data-transformation/       # ETL y transformaciones (Bronze/Silver/Gold)
├── etl-silver-to-gold/        # Pipeline Silver-to-Gold (agregaciones y BI)
├── redshift-loading/          # Carga incremental a Redshift
└── monitoring-alerting/       # Monitoreo y alertas con CloudWatch
```

Cada spec incluye:
- `requirements.md` - Requerimientos funcionales con acceptance criteria
- `design.md` - Decisiones de diseño y correctness properties
- `tasks.md` - Plan de implementación con tareas específicas
- `docs/` - Documentación adicional específica del spec (ver README.md en cada carpeta)

## 🎓 Recursos de Aprendizaje

### Terraform
- [Terraform Documentation](https://www.terraform.io/docs)
- [AWS Provider](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)

### AWS
- [AWS Well-Architected Framework](https://aws.amazon.com/architecture/well-architected/)
- [VPC Documentation](https://docs.aws.amazon.com/vpc/)
- [Security Groups](https://docs.aws.amazon.com/vpc/latest/userguide/VPC_SecurityGroups.html)

### LocalStack
- [LocalStack Docs](https://docs.localstack.cloud/)
- [Terraform with LocalStack](https://docs.localstack.cloud/user-guide/integrations/terraform/)

## 🤝 Contribuir

Para contribuir al proyecto:

1. Crear una rama feature: `git checkout -b feature/nueva-funcionalidad`
2. Hacer cambios y commitear: `git commit -m "Descripción"`
3. Probar en ambiente dev primero
4. Crear Pull Request para revisión

## 📞 Soporte

Para preguntas o problemas:

1. Revisar la documentación en este README
2. Consultar [GUIA_COMPARTIR_PROYECTO.md](GUIA_COMPARTIR_PROYECTO.md)
3. Revisar [terraform/DOCUMENTATION_INDEX.md](terraform/DOCUMENTATION_INDEX.md)
4. Contactar al equipo de DevOps/Infrastructure

## 📄 Licencia

Este proyecto es propiedad de Cencosud y está destinado para uso interno.

---

**Última actualización:** 23 de Febrero de 2026

**Estado del Proyecto:** 
- ✅ **Infraestructura**: Validada en producción - 100% compliance - Production Ready
- ✅ **Transformaciones Bronze-to-Silver**: Módulos integrados y validados
- ✅ **Transformaciones Silver-to-Gold**: Pipeline ETL integrado con 6 módulos
- ✅ **API Polling System**: Requirements completados (12 requerimientos) ⭐ NUEVO

**Deployment Status:**
- **141 recursos validados** en AWS (Account: 827739413930)
- **100% compliance** con Spec 01-aws-infrastructure (61/61 requisitos aplicables)
- **Región**: us-east-1 (Single-AZ: us-east-1a)
- **Configuración**: Production (`terraform.tfvars.prod`)
- **Costos Estimados**: ~$145-185/mes (infraestructura base)
- **Lifecycle**: Plan → Apply → Verify → Destroy - Todo exitoso

**Testing Status:**
- ✅ **Módulos individuales**: Bien testeados (Vicente + Max)
- ✅ **Property-based tests**: 3 properties pasando (Iceberg)
- ✅ **Pipeline Bronze-to-Silver**: Validado en LocalStack (Max)
- ✅ **Pipeline Silver-to-Gold**: 6 módulos integrados y documentados
- ⚠️ **Integración end-to-end**: Pendiente (Bronze → Silver → Gold completo)
- ⚠️ **Schema Evolution**: Implementado pero no probado con datos reales

**Próximos Pasos:**
- **Infraestructura**: Listo para entrega al cliente y deployment en cuenta AWS de Cencosud
- **Transformaciones**: Testing end-to-end del pipeline completo Bronze → Silver → Gold
- **Fase 2**: Implementar código para Lambda, Glue, MWAA
- **Silver-to-Gold**: Ejecutar pipeline con datos reales y validar agregaciones
