# 

# 

# 

# 

# 

# 

# 

# “Documento Detallado de Diseño Proyecto Janis-Cencosud”

## **V 1.1**

[**Capítulo 1: Resumen Ejecutivo	7**](#capítulo-1:-resumen-ejecutivo)

[1.1 Visión General del Proyecto	7](#1.1-visión-general-del-proyecto)

[1.2 Arquitectura de Solución	7](#1.2-arquitectura-de-solución)

[1.3 Estrategia de Procesamiento de Datos	8](#1.3-estrategia-de-procesamiento-de-datos)

[1.3.1 Carga Inicial (Baseline)	8](#1.3.1-carga-inicial-\(baseline\))

[1.3.2 Cargas Regulares (Operación DataOps)	8](#1.3.2-cargas-regulares-\(operación-dataops\))

[1.4 Modelo de Datos y Calidad	8](#1.4-modelo-de-datos-y-calidad)

[1.5 Seguridad, Resiliencia y Observabilidad	9](#1.5-seguridad,-resiliencia-y-observabilidad)

[1.6 Conclusión	9](#1.6-conclusión)

[**Capítulo 2: Arquitectura de Solución en AWS	10**](#capítulo-2:-arquitectura-de-solución-en-aws)

[2.1 Componentes Core y Decisiones Tecnológicas	10](#2.1-componentes-core-y-decisiones-tecnológicas)

[2.1.1 Visión General de la Arquitectura	10](#2.1.1-visión-general-de-la-arquitectura)

[2.1.2 API Gateway	10](#2.1.2-api-gateway)

[Descripción del Componente	10](#descripción-del-componente)

[Rol en la Arquitectura	10](#rol-en-la-arquitectura)

[2.1.3 Amazon Kinesis Data Firehose	10](#2.1.3-amazon-kinesis-data-firehose)

[Descripción del Componente	10](#descripción-del-componente-1)

[Rol en la Arquitectura	11](#rol-en-la-arquitectura-1)

[2.1.4 Amazon S3 \+ Apache Iceberg	11](#2.1.4-amazon-s3-+-apache-iceberg)

[Descripción del Componente	11](#descripción-del-componente-2)

[Rol en la Arquitectura	11](#rol-en-la-arquitectura-2)

[2.1.5 AWS Glue	12](#2.1.5-aws-glue)

[Descripción del Componente	12](#descripción-del-componente-3)

[Rol en la Arquitectura	12](#rol-en-la-arquitectura-3)

[2.1.6 Amazon Redshift	13](#2.1.6-amazon-redshift)

[Descripción del Componente	13](#descripción-del-componente-4)

[Rol en la Arquitectura	13](#rol-en-la-arquitectura-4)

[2.1.7 Amazon MWAA (Managed Workflows for Apache Airflow)	13](#2.1.7-amazon-mwaa-\(managed-workflows-for-apache-airflow\))

[Descripción del Componente	13](#descripción-del-componente-5)

[Rol en la Arquitectura	13](#rol-en-la-arquitectura-5)

[2.1.8 AWS Lambda	14](#2.1.8-aws-lambda)

[Descripción del Componente	14](#descripción-del-componente-6)

[Rol en la Arquitectura	14](#rol-en-la-arquitectura-6)

[Configuración Propuesta:\*\*	14](#configuración-propuesta:**)

[2.2 Topología de Red y Seguridad Perimetral	14](#2.2-topología-de-red-y-seguridad-perimetral)

[2.2.1 Diseño de VPC	14](#2.2.1-diseño-de-vpc)

[Configuración de VPC	14](#configuración-de-vpc)

[Subredes	15](#subredes)

[2.2.2 Gateways y Routing	16](#2.2.2-gateways-y-routing)

[Internet Gateway	16](#internet-gateway)

[NAT Gateways	16](#nat-gateways)

[Route Tables	16](#route-tables)

[2.2.3 VPC Endpoints	17](#2.2.3-vpc-endpoints)

[2.2.4 Security Groups	17](#2.2.4-security-groups)

[SG-API-Gateway	17](#sg-api-gateway)

[SG-Redshift	18](#sg-redshift)

[SG-Lambda	18](#sg-lambda)

[SG-MWAA	18](#sg-mwaa)

[SG-Glue	18](#sg-glue)

[2.2.5 Network ACLs	19](#2.2.5-network-acls)

[2.2.6 AWS WAF (Web Application Firewall)	19](#2.2.6-aws-waf-\(web-application-firewall\))

[2.2.7 Diagrama de Topología de Red	20](#2.2.7-diagrama-de-topología-de-red)

[2.2.8 Estrategia de Aislamiento	21](#2.2.8-estrategia-de-aislamiento)

[**Capítulo 3: Diseño esquema de datos	22**](#capítulo-3:-diseño-esquema-de-datos)

[3.1 Introducción al Modelo de Datos	22](#3.1-introducción-al-modelo-de-datos)

[3.1.1 Objetivo del Capítulo	22](#3.1.1-objetivo-del-capítulo)

[3.1.2 Principios de Diseño	22](#3.1.2-principios-de-diseño)

[3.2 Resumen de Tablas	22](#3.2-resumen-de-tablas)

[3.2.1 Inventario Completo de Tablas	22](#3.2.1-inventario-completo-de-tablas)

[3.3 Conversiones de Tipos de Datos	24](#3.3-conversiones-de-tipos-de-datos)

[3.3.1 Mapeo de Tipos MySQL → Redshift	24](#3.3.1-mapeo-de-tipos-mysql-→-redshift)

[3.3.2 Conversiones Especiales	25](#3.3.2-conversiones-especiales)

[Timestamps Unix a ISO 8601	25](#timestamps-unix-a-iso-8601)

[Boolean de TINYINT	26](#boolean-de-tinyint)

[3.4 Estrategias de Distribución y Ordenamiento	26](#3.4-estrategias-de-distribución-y-ordenamiento)

[3.4.1 Distribution Keys	26](#3.4.1-distribution-keys)

[3.4.2 Sort Keys	27](#3.4.2-sort-keys)

[3.4.3 Estrategia por Tabla	27](#3.4.3-estrategia-por-tabla)

[3.5 Definición de Tablas Principales	28](#3.5-definición-de-tablas-principales)

[3.5.1 Tabla: wms\_orders	28](#3.5.1-tabla:-wms_orders)

[3.5.2 Tabla: wms\_order\_items	29](#3.5.2-tabla:-wms_order_items)

[3.5.3 Tabla: wms\_stores	30](#3.5.3-tabla:-wms_stores)

[3.5.4 Tabla: customers	31](#3.5.4-tabla:-customers)

[3.6 Manejo de Data Gaps	33](#3.6-manejo-de-data-gaps)

[3.6.1 Resumen de Gaps Críticos	33](#3.6.1-resumen-de-gaps-críticos)

[3.6.2 Campos Calculados	33](#3.6.2-campos-calculados)

[3.7 Scripts DDL Completos	34](#3.7-scripts-ddl-completos)

[**Capítulo 4: Diseño del Proceso: Carga Inicial**](#capítulo-4:-diseño-del-proceso:-carga-inicial-\(via-backup-base-de-datos\))   
[**(Via backup Base de Datos)	36**](#capítulo-4:-diseño-del-proceso:-carga-inicial-\(via-backup-base-de-datos\))

[4.1 Architecture	36](#4.1-architecture)

[4.1.1 Arquitectura de Alto Nivel	36](#4.1.1-arquitectura-de-alto-nivel)

[4.1.2 Componentes Principales	37](#heading)

[4.2 Componentes e interfaces	38](#4.2-componentes-e-interfaces)

[4.2.1. Módulo de Acceso al Respaldo AWS	38](#4.2.1.-módulo-de-acceso-al-respaldo-aws)

[4.2.2. Módulo de Validación de Datos Raw	39](#4.2.2.-módulo-de-validación-de-datos-raw)

[4.2.3. Módulo de Transformación Bronze → Silver	39](#4.2.3.-módulo-de-transformación-bronze-→-silver)

[4.2.5. Módulo de Carga a Redshift	40](#4.2.5.-módulo-de-carga-a-redshift)

[4.2.6. Módulo de Validación y Reconciliación	40](#4.2.6.-módulo-de-validación-y-reconciliación)

[4.3 Data Models	41](#4.3-data-models)

[4.3.1 S3 Bronze (Raw Data)	41](#4.3.1-s3-bronze-\(raw-data\))

[4.3.2 S3 Silver (Cleaned Data \- Todos los datos históricos)	41](#4.3.2-s3-silver-\(cleaned-data---todos-los-datos-históricos\))

[4.3.3 S3 Gold (Curated Data \- Optimizado para Redshift)	42](#4.3.3-s3-gold-\(curated-data---optimizado-para-redshift\))

[4.3.4 Monitoreo y Alertas	42](#4.3.4-monitoreo-y-alertas)

[4.4 Testing Strategy	42](#4.4-testing-strategy)

[4.4.1 Enfoque de Testing	42](#4.4.1-enfoque-de-testing)

[4.4.2 Criterios de Aceptación	42](#4.4.2-criterios-de-aceptación)

[4.5 Uso del Respaldo AWS	43](#4.5-uso-del-respaldo-aws)

[4.5.1 Beneficios Operacionales	43](#4.5.1-beneficios-operacionales)

[4.5.2 Beneficios Técnicos	43](#4.5.2-beneficios-técnicos)

[4.6 Consideraciones de seguridad	44](#4.6-consideraciones-de-seguridad)

[4.6.1 Seguridad del Respaldo AWS	44](#4.6.1-seguridad-del-respaldo-aws)

[4.6.2 Fases de Ejecución	45](#4.6.2-fases-de-ejecución)

[4.6.2.1 Fase 1: Preparación (Pre-Migration)	45](#4.6.2.1-fase-1:-preparación-\(pre-migration\))

[4.6.2.2 Fase 2: Extracción desde Respaldo AWS (Extraction & Landing)	46](#4.6.2.2-fase-2:-extracción-desde-respaldo-aws-\(extraction-&-landing\))

[4.6.2.3 Fase 3: Transformación y Curación (Transformation & Curation)	46](#4.6.2.3-fase-3:-transformación-y-curación-\(transformation-&-curation\))

[4.6.2.4 Fase 4: Carga y Validación Final (Load & Validation)	47](#4.6.2.4-fase-4:-carga-y-validación-final-\(load-&-validation\))

[4.6.2.5 Criterios de Éxito Global	48](#4.6.2.5-criterios-de-éxito-global)

[**Capítulo 5: Diseño del Proceso: Cargas Regulares (Operación DataOps)	49**](#capítulo-5:-diseño-del-proceso:-cargas-regulares-\(operación-dataops\))

[5.1 Introducción	49](#5.1-introducción)

[5.1.1 Objetivo del Proceso	49](#5.1.1-objetivo-del-proceso)

[5.1.2 Alcance de las Cargas Regulares	49](#5.1.2-alcance-de-las-cargas-regulares)

[5.1.3 Principios de Diseño	50](#5.1.3-principios-de-diseño)

[5.2 Arquitectura General del Proceso	51](#5.2-arquitectura-general-del-proceso)

[5.2.1 Vista de Alto Nivel	51](#5.2.1-vista-de-alto-nivel)

[5.2.2 Diagrama de Flujo Completo	52](#5.2.2-diagrama-de-flujo-completo)

[5.3 Capa de Ingesta Dual: Webhooks y Polling	53](#5.3-capa-de-ingesta-dual:-webhooks-y-polling)

[5.3.1 Estrategia de Ingesta Híbrida	53](#5.3.1-estrategia-de-ingesta-híbrida)

[5.3.2 Webhooks: Notificaciones de Eventos	53](#5.3.2-webhooks:-notificaciones-de-eventos)

[5.3.3 Polling Periódico: Consulta Activa de APIs	54](#5.3.3-polling-periódico:-consulta-activa-de-apis)

[5.3.4 Deduplicación de Datos	56](#5.3.4-deduplicación-de-datos)

[5.4 Capa de Buffer: Kinesis Firehose y S3 Bronze	56](#5.4-capa-de-buffer:-kinesis-firehose-y-s3-bronze)

[5.4.1 Rol de Kinesis Firehose	56](#5.4.1-rol-de-kinesis-firehose)

[5.4.2 Estructura de S3 Bronze	57](#5.4.2-estructura-de-s3-bronze)

[5.5 Capa de Procesamiento: AWS Glue y Apache Iceberg Silver	59](#5.5-capa-de-procesamiento:-aws-glue-y-apache-iceberg-silver)

[5.5.1 Transformaciones de Datos	59](#5.5.1-transformaciones-de-datos)

[5.5.2 Apache Iceberg en Capa Silver	60](#5.5.2-apache-iceberg-en-capa-silver)

[5.5.3 Estructura de Tablas Silver	61](#5.5.3-estructura-de-tablas-silver)

[5.6 Capa de Orquestación: Apache Airflow (MWAA)	62](#heading=h.oej5x02kbqs5)

[5.6.1 Rol de Apache Airflow	62](#heading=h.dt9iwabsckuo)

[5.6.2 DAGs Principales	62](#heading=h.3a8ho3igxzd5)

[5.6.3 Manejo de Errores y Reintentos	64](#heading=h.s7m79ixhumoj)

[5.7 Capa de Disponibilización: Redshift y Power BI	65](#5.7-capa-de-disponibilización:-redshift-y-power-bi)

[5.7.1 Carga Incremental a Redshift	65](#5.7.1-carga-incremental-a-redshift)

[5.7.2 Integración con Power BI	66](#5.7.2-integración-con-power-bi)

[5.8 Monitoreo y Observabilidad	67](#5.8-monitoreo-y-observabilidad)

[5.8.1 Métricas Clave	67](#5.8.1-métricas-clave)

[5.8.2 Dashboards de Monitoreo	68](#5.8.2-dashboards-de-monitoreo)

[5.8.3 Alertas y Notificaciones	69](#5.8.3-alertas-y-notificaciones)

[5.9 Seguridad y Cumplimiento	70](#5.9-seguridad-y-cumplimiento)

[5.9.1 Seguridad en Tránsito	70](#5.9.1-seguridad-en-tránsito)

[5.9.2 Seguridad en Reposo	70](#5.9.2-seguridad-en-reposo)

[5.9.3 Auditoría y Trazabilidad	70](#5.9.3-auditoría-y-trazabilidad)

# 

# Capítulo 1: Resumen Ejecutivo {#capítulo-1:-resumen-ejecutivo}

## 1.1 Visión General del Proyecto {#1.1-visión-general-del-proyecto}

El presente documento detalla la arquitectura, diseño e implementación de la solución de integración de datos entre la plataforma Janis (WMS) y el Data Lake de Cencosud en AWS. El objetivo primordial es hacer un traspaso transparente desde la BDD de Janis hacía una gestionada por Cencosud permitiendo la disponibilidad operativa para el área de negocios mediante herramientas BI.

La solución aborda dos desafíos principales: la migración histórica de datos (Carga Inicial) y la actualización continua en tiempo casi real (Cargas Regulares), garantizando la integridad de la información y soportando la toma de decisiones basada en datos.

## 1.2 Arquitectura de Solución {#1.2-arquitectura-de-solución}

La arquitectura propuesta es **Serverless** y nativa de AWS, diseñada para minimizar la carga operativa y maximizar la escalabilidad. El flujo de datos se organiza en un esquema de **Data Lake moderno** con capas lógicas (Bronze, Silver, Gold) utilizando **Apache Iceberg** para garantizar transacciones ACID y evolución de esquemas.

Los componentes core de la arquitectura son:

* **Ingesta:** Estrategia híbrida utilizando **Amazon API Gateway** para recibir Webhooks en tiempo real y **Amazon MWAA (Airflow)** para sondeo (polling) periódico de APIs.  
* **Buffer y Persistencia:** **Amazon Kinesis Data Firehose** gestiona la captura y entrega optimizada de datos hacia **Amazon S3** (Capa Bronze), aplicando compresión y particionamiento automático.  
* **Procesamiento:** **AWS Glue** actúa como motor ETL serverless para limpiar, deduplicar y transformar datos entre las capas Silver y Gold.  
* **Disponibilización:** **Amazon Redshift** sirve como Data Warehouse final, optimizado con claves de distribución y ordenamiento para consultas de alto rendimiento desde Power BI.

## 

## 1.3 Estrategia de Procesamiento de Datos {#1.3-estrategia-de-procesamiento-de-datos}

El diseño contempla dos flujos de trabajo distintos pero complementarios:

### 1.3.1 Carga Inicial (Baseline) {#1.3.1-carga-inicial-(baseline)}

Se debe hacer una carga inicial de datos siguiendo el nuevo esquema de datos entregado por las APIs de Janis y de esta forma la ingesta continua de datos no genere ningún problema de conflictos con la nueva base administrada por Cencosud**.** Este proceso omite validaciones de llaves foráneas para permitir la carga de datos históricos parciales y mitigar *Data Gaps* críticos identificados en el mapeo**.**

### 1.3.2 Cargas Regulares (Operación DataOps) {#1.3.2-cargas-regulares-(operación-dataops)}

El núcleo operativo se basa en una estrategia de ingesta híbrida para balancear latencia y confiabilidad:

* Webhooks (Event-Driven)**:** Janis notifica eventos críticos (ej. `order.created`) para una actualización inmediata.  
* Polling (Scheduled)**:** Un proceso de consulta activa cada 5 minutos actúa como red de seguridad para recuperar datos que pudieran perderse por fallos de red.  
* Deduplicación**:** Se implementa lógica de idempotencia en la capa Silver para unificar registros provenientes de ambas fuentes, priorizando el timestamp más reciente.

## 1.4 Modelo de Datos y Calidad {#1.4-modelo-de-datos-y-calidad}

Se ha diseñado un esquema compatible con MySQL que mapea 26 tablas críticas hacia Redshift. El modelo prioriza la analítica sobre la integridad referencial estricta, utilizando estrategias de *Distribution Keys* y *Sort Keys* para optimizar JOINS y filtros frecuentes.

* Cobertura**:** Se cubren \~97% de los campos requeridos por BI.  
* Manejo de Gaps: Para campos no disponibles en la API de Janis (ej. `items_substituted_qty`), se implementaron reglas de cálculo derivado o flags de metadatos para mantener la transparencia en los reportes.

## 

## 1.5 Seguridad, Resiliencia y Observabilidad {#1.5-seguridad,-resiliencia-y-observabilidad}

La solución cumple con estrictos estándares de seguridad corporativa y continuidad operativa:

* Seguridad**:** Aislamiento de red mediante VPC privada, encriptación en reposo (KMS) y tránsito (TLS), y enmascaramiento de datos sensibles (PII) como emails y teléfonos antes de su exposición a analistas.  
* Resiliencia**:** Implementación de Dead Letter Queues (DLQ) para capturar y reprocesar fallos sin detener el pipeline, junto con políticas de *Retry* con *Exponential Backoff*.  
* Monitoreo**:** Dashboards integrados en CloudWatch y SLAs definidos con objetivos de disponibilidad del 99.5% para el pipeline completo.

## 1.6 Conclusión {#1.6-conclusión}

Este diseño proporciona a Cencosud una plataforma de datos moderna que no solo resuelve la necesidad inmediata de integración con Janis, sino que establece una base arquitectónica escalable (Apache Iceberg \+ Serverless) preparada para futuros crecimientos de volumen y casos de uso analíticos avanzados.

# Capítulo 2: Arquitectura de Solución en AWS {#capítulo-2:-arquitectura-de-solución-en-aws}

---

## 2.1 Componentes Core y Decisiones Tecnológicas {#2.1-componentes-core-y-decisiones-tecnológicas}

### 2.1.1 Visión General de la Arquitectura {#2.1.1-visión-general-de-la-arquitectura}

La arquitectura propuesta para Cencosud se basa en servicios nativos de AWS, diseñada para proporcionar una solución escalable, resiliente y de bajo mantenimiento operativo. La solución implementa un Data Lake moderno con capas Bronze, Silver y Gold utilizando Apache Iceberg, y un Data Warehouse en Amazon Redshift para consumo de Power BI.

### 2.1.2 API Gateway {#2.1.2-api-gateway}

#### Descripción del Componente {#descripción-del-componente}

Amazon API Gateway actúa como la puerta de entrada para todos los Webhooks provenientes de Janis. Proporciona una interfaz REST segura y escalable para recibir eventos en tiempo real.

#### Rol en la Arquitectura {#rol-en-la-arquitectura}

- **Ingesta de Webhooks**: Recibe notificaciones HTTP POST desde Janis  
- **Autenticación**: Valida API keys y tokens de autenticación  
- **Throttling**: Controla la tasa de requests para prevenir sobrecarga  
- **Transformación**: Mapea payloads JSON a formato estándar  
- **Enrutamiento**: Dirige eventos a Kinesis Firehose según tipo de evento

**Configuración Propuesta:**

- Tipo: REST API (no HTTP API por requerimientos de transformación)  
- Autenticación: API Key \+ IAM roles  
- Throttling: 10,000 requests/segundo con burst de 5,000  
- Timeout: 29 segundos (máximo de API Gateway)  
- Logging: Completo en CloudWatch Logs

### 2.1.3 Amazon Kinesis Data Firehose {#2.1.3-amazon-kinesis-data-firehose}

#### Descripción del Componente {#descripción-del-componente-1}

Kinesis Firehose es un servicio de streaming completamente gestionado que captura, transforma y carga datos en tiempo real hacia S3.

#### Rol en la Arquitectura {#rol-en-la-arquitectura-1}

- **Buffering**: Acumula eventos antes de escribir a S3 (reduce costos de PUT)  
- **Batching**: Agrupa múltiples eventos en archivos más grandes  
- **Compresión**: Comprime datos antes de almacenar (GZIP, Snappy)  
- **Particionamiento**: Organiza datos por fecha/hora en S3  
- **Resiliencia**: Reintentos automáticos y DLQ para fallos

**Configuración Propuesta:**

- Buffer size: 5 MB (balance entre latencia y costo)  
- Buffer interval: 300 segundos (5 minutos)  
- Compresión: GZIP (mejor ratio de compresión)  
- Particionamiento: `year=YYYY/month=MM/day=DD/hour=HH/`  
- Error handling: DLQ en S3 separado

### 2.1.4 Amazon S3 \+ Apache Iceberg {#2.1.4-amazon-s3-+-apache-iceberg}

#### Descripción del Componente {#descripción-del-componente-2}

Amazon S3 actúa como el almacenamiento principal del Data Lake, organizado en tres capas (Bronze, Silver, Gold) utilizando Apache Iceberg como formato de tabla.

#### Rol en la Arquitectura {#rol-en-la-arquitectura-2}

**Bronze Layer (Raw Data):**

- Datos sin procesar directamente desde Firehose  
- Formato: JSON comprimido con GZIP  
- Retención: 90 días  
- Uso: Auditoría y reprocesamiento

**Silver Layer (Cleaned Data):**

- Datos limpiados y normalizados  
- Formato: Apache Iceberg (Parquet)  
- Retención: 2 años  
- Uso: Transformaciones y análisis

**Gold Layer (Curated Data):**

- Datos agregados y optimizados  
- Formato: Apache Iceberg (Parquet)  
- Retención: 5 años  
- Uso: Consumo directo por Redshift

**Ventajas Clave de Iceberg:**

1. **Transacciones ACID**: Garantiza que las escrituras sean atómicas y consistentes  
2. **Time Travel**: Permite consultar datos históricos sin duplicar almacenamiento  
3. **Schema Evolution**: Facilita agregar/modificar columnas sin reescribir datos  
4. **Partition Evolution**: Permite cambiar estrategia de particionamiento sin migración  
5. **Hidden Partitioning**: Los usuarios no necesitan especificar particiones en queries  
6. **Metadata Management**: Gestión eficiente de metadatos para tablas grandes

**Configuración Propuesta:**

```
Bronze Layer:
  bucket: s3://cencosud-datalake-bronze/
  format: JSON + GZIP
  partitioning: year/month/day/hour
  lifecycle: 90 días → Glacier → Delete después de 1 año

Silver Layer:
  bucket: s3://cencosud-datalake-silver/
  format: Apache Iceberg (Parquet + Snappy)
  partitioning: Hidden partitioning por fecha
  lifecycle: 2 años en S3 Standard
  
Gold Layer:
  bucket: s3://cencosud-datalake-gold/
  format: Apache Iceberg (Parquet + Snappy)
  partitioning: Optimizado por queries de BI
  lifecycle: 5 años en S3 Standard
```

### 2.1.5 AWS Glue {#2.1.5-aws-glue}

#### Descripción del Componente {#descripción-del-componente-3}

AWS Glue es un servicio de ETL serverless que transforma datos entre las capas del Data Lake.

#### Rol en la Arquitectura {#rol-en-la-arquitectura-3}

- **Data Catalog**: Almacena metadatos de tablas Iceberg  
- **ETL Jobs**: Transforma datos de Bronze → Silver → Gold  
- **Crawlers**: Descubre esquemas automáticamente  
- **Schema Registry**: Gestiona evolución de esquemas  
- **Job Scheduling**: Ejecuta transformaciones programadas

**Configuración Propuesta:**

- Tipo de job: Glue 4.0 (última versión)  
- Worker type: G.1X (4 vCPU, 16 GB RAM)  
- Number of workers: Auto-scaling 2-10  
- Timeout: 2 horas  
- Retries: 3 intentos con exponential backoff  
- Lenguaje: PySpark

### 2.1.6 Amazon Redshift {#2.1.6-amazon-redshift}

#### Descripción del Componente {#descripción-del-componente-4}

Amazon Redshift es el data warehouse columnar que almacena los datos finales para consumo de Power BI.

#### Rol en la Arquitectura {#rol-en-la-arquitectura-4}

- **Data Warehouse**: Almacenamiento final de datos curados  
- **Query Engine**: Procesa queries de Power BI  
- **Compatibilidad**: Mantiene esquema compatible con MySQL  
- **Performance**: Optimizado para queries analíticas  
- **Concurrencia**: Soporta múltiples usuarios simultáneos

**Configuración Propuesta:**

- Reutilización de la actual plataforma de Cenco

### 2.1.7 Amazon MWAA (Managed Workflows for Apache Airflow) {#2.1.7-amazon-mwaa-(managed-workflows-for-apache-airflow)}

#### Descripción del Componente {#descripción-del-componente-5}

MWAA es un servicio gestionado de Apache Airflow que orquesta todos los workflows de datos.

#### Rol en la Arquitectura {#rol-en-la-arquitectura-5}

- **Orquestación**: Coordina ejecución de Glue jobs  
- **Scheduling**: Programa cargas periódicas desde APIs  
- **Monitoring**: Monitorea estado de pipelines  
- **Alerting**: Notifica fallos y anomalías  
- **Dependency Management**: Gestiona dependencias entre tareas

**Configuración Propuesta:**

- Environment class: mw1.small (1 vCPU, 2 GB RAM)  
- Min workers: 1  
- Max workers: 3  
- Scheduler: 2 schedulers para HA  
- Airflow version: 2.7.2 (última estable)  
- Python version: 3.11

### 2.1.8 AWS Lambda {#2.1.8-aws-lambda}

#### Descripción del Componente {#descripción-del-componente-6}

AWS Lambda proporciona computación serverless para procesamiento de eventos y transformaciones ligeras.

#### Rol en la Arquitectura {#rol-en-la-arquitectura-6}

- **Validación**: Valida payloads de Webhooks  
- **Transformación**: Transforma datos antes de Firehose  
- **Notificaciones**: Envía alertas vía SNS  
- **Triggers**: Dispara procesos basados en eventos S3  
- **Utilidades**: Funciones auxiliares para operaciones

#### Configuración Propuesta:\*\* {#configuración-propuesta:**}

- Runtime: Python 3.11  
- Memory: 512 MB (ajustable según carga)  
- Timeout: 30 segundos  
- Concurrency: 100 ejecuciones simultáneas  
- VPC: Dentro de VPC para acceso a Redshift

---

## 2.2 Topología de Red y Seguridad Perimetral {#2.2-topología-de-red-y-seguridad-perimetral}

### 2.2.1 Diseño de VPC {#2.2.1-diseño-de-vpc}

**Esta es la estructura de red propuesta, sin embargo algunos detalles de diseño como los IP deberán ser definidos por el cliente en el momento de la implementación.** 

#### Configuración de VPC {#configuración-de-vpc}

```
VPC: cencosud-datalake-vpc
CIDR: 10.0.0.0/16 (65,536 IPs)
Region: us-east-1 (N. Virginia)
Availability Zones: us-east-1a, us-east-1b (para HA)
DNS Resolution: Enabled
DNS Hostnames: Enabled
```

#### Subredes {#subredes}

**Subredes Públicas (para recursos con acceso a Internet):**

```
Public Subnet A: 10.0.1.0/24 (us-east-1a) - 256 IPs
  - NAT Gateway A
  - Bastion Host (opcional)
  
Public Subnet B: 10.0.2.0/24 (us-east-1b) - 256 IPs
  - NAT Gateway B (para HA)
```

**Subredes Privadas (para recursos internos):**

```
Private Subnet 1A: 10.0.10.0/24 (us-east-1a) - 256 IPs
  - Redshift, MWAA, Lambda
  - Servicios de procesamiento de datos
  
Private Subnet 1B: 10.0.11.0/24 (us-east-1b) - 256 IPs
  - Redshift, MWAA, Lambda
  - Servicios de procesamiento de datos (HA)
  
Private Subnet 2A: 10.0.20.0/24 (us-east-1a) - 256 IPs
  - Glue ENIs (dedicado para evitar agotamiento de IPs)
  
Private Subnet 2B: 10.0.21.0/24 (us-east-1b) - 256 IPs
  - Glue ENIs (dedicado para evitar agotamiento de IPs)
```

**Decisiones de Diseño:**

- **Multi-AZ Deployment**: Todos los componentes críticos distribuidos en dos Availability Zones para alta disponibilidad y tolerancia a fallos
- **Segregación de Subredes**: Cuatro tipos de subredes para separación clara de responsabilidades
- **Subredes Dedicadas para Glue**: Subredes 2A/2B exclusivas para ENIs de Glue para evitar agotamiento de direcciones IP

### 2.2.2 Gateways y Routing {#2.2.2-gateways-y-routing}

#### Internet Gateway {#internet-gateway}

```
Internet Gateway: cencosud-igw
Attached to: cencosud-datalake-vpc
Purpose: Permite acceso a Internet desde subredes públicas
```

#### NAT Gateways {#nat-gateways}

```
NAT Gateway A: nat-gateway-a (en Public Subnet A)
  - Elastic IP: Asignado automáticamente
  - Purpose: Permite a recursos privados en us-east-1a acceder a Internet
  - Availability Zone: us-east-1a
  
NAT Gateway B: nat-gateway-b (en Public Subnet B)
  - Elastic IP: Asignado automáticamente
  - Purpose: Permite a recursos privados en us-east-1b acceder a Internet
  - Availability Zone: us-east-1b
  - Redundancia: Alta disponibilidad multi-AZ
```

#### Route Tables {#route-tables}

**Public Route Table:**

```
Destination         Target
10.0.0.0/16        local
0.0.0.0/0          igw-xxxxx (Internet Gateway)
```

**Private Route Table 1A:**

```
Destination         Target
10.0.0.0/16        local
0.0.0.0/0          nat-gateway-a (NAT Gateway A)
```

**Private Route Table 1B:**

```
Destination         Target
10.0.0.0/16        local
0.0.0.0/0          nat-gateway-b (NAT Gateway B)
```

**Private Route Table 2A (Glue ENIs):**

```
Destination         Target
10.0.0.0/16        local
0.0.0.0/0          nat-gateway-a (NAT Gateway A)
```

**Private Route Table 2B (Glue ENIs):**

```
Destination         Target
10.0.0.0/16        local
0.0.0.0/0          nat-gateway-b (NAT Gateway B)
```

### 2.2.3 VPC Endpoints {#2.2.3-vpc-endpoints}

Para reducir costos de transferencia de datos y mejorar seguridad, se implementan VPC Endpoints para servicios de AWS:

```
Gateway Endpoints (sin costo):
  - S3: com.amazonaws.us-east-1.s3
  

Interface Endpoints (con costo):
  - Glue: com.amazonaws.us-east-1.glue
  - Secrets Manager: com.amazonaws.us-east-1.secretsmanager
  - CloudWatch Logs: com.amazonaws.us-east-1.logs
  - KMS: com.amazonaws.us-east-1.kms
  - STS: com.amazonaws.us-east-1.sts
```

**Beneficios:**

- Tráfico permanece dentro de la red de AWS  
- Reduce costos de NAT Gateway  
- Mejora latencia y seguridad  
- No requiere Internet Gateway para estos servicios

### 2.2.4 Security Groups {#2.2.4-security-groups}

#### SG-API-Gateway {#sg-api-gateway}

```
Inbound Rules:
  - HTTPS (443) desde 0.0.0.0/0 (Webhooks de Janis)
  
Outbound Rules:
  - All traffic a 0.0.0.0/0
```

#### SG-Redshift {#sg-redshift}

```
Inbound Rules:
  - PostgreSQL (5439) desde SG-Lambda
  - PostgreSQL (5439) desde SG-MWAA
  - PostgreSQL (5439) desde SG-PowerBI (VPN o Direct Connect)
  
Outbound Rules:
  - HTTPS (443) a VPC Endpoint S3
  - HTTPS (443) a VPC Endpoint Secrets Manager
```

#### SG-Lambda {#sg-lambda}

```
Inbound Rules:
  - None (Lambda no recibe conexiones entrantes)
  
Outbound Rules:
  - PostgreSQL (5439) a SG-Redshift
  - HTTPS (443) a VPC Endpoints
  - HTTPS (443) a 0.0.0.0/0 (para APIs de Janis)
```

#### SG-MWAA {#sg-mwaa}

```
Inbound Rules:
  - HTTPS (443) desde SG-MWAA (self-reference para workers)
  
Outbound Rules:
  - HTTPS (443) a VPC Endpoints
  - HTTPS (443) a 0.0.0.0/0 (para APIs de Janis)
  - PostgreSQL (5439) a SG-Redshift
```

#### SG-Glue {#sg-glue}

```
Inbound Rules:
  - All TCP desde SG-Glue (self-reference para Spark)
  
Outbound Rules:
  - HTTPS (443) a VPC Endpoints
  - All TCP a SG-Glue (self-reference)
```

### 2.2.5 Network ACLs {#2.2.5-network-acls}

Las Network ACLs actúan como firewall a nivel de subnet (stateless):

**Public Subnet NACL:**

```
Inbound Rules:
  100: HTTPS (443) from 0.0.0.0/0 - ALLOW
  110: Ephemeral ports (1024-65535) from 0.0.0.0/0 - ALLOW
  *: All traffic - DENY

Outbound Rules:
  100: All traffic to 0.0.0.0/0 - ALLOW
  *: All traffic - DENY
```

**Private Subnet NACL:**

```
Inbound Rules:
  100: All traffic from 10.0.0.0/16 - ALLOW
  110: HTTPS (443) from 0.0.0.0/0 - ALLOW (para responses)
  120: Ephemeral ports (1024-65535) from 0.0.0.0/0 - ALLOW
  *: All traffic - DENY

Outbound Rules:
  100: All traffic to 10.0.0.0/16 - ALLOW
  110: HTTPS (443) to 0.0.0.0/0 - ALLOW
  *: All traffic - DENY
```

### 2.2.6 AWS WAF (Web Application Firewall) {#2.2.6-aws-waf-(web-application-firewall)}

AWS WAF se configura en API Gateway para proteger contra ataques comunes:

**Reglas Implementadas:**

1. **Rate Limiting:**  
     
   - Límite: 2,000 requests por IP en 5 minutos  
   - Acción: Block con respuesta 429 (Too Many Requests)

   

2. **Geo-Blocking:**  
     
   - Permitir: Solo tráfico desde Perú (PE) y AWS regions  
   - Acción: Block para otros países

   

3. **IP Reputation:**  
     
   - AWS Managed Rule: AWSManagedRulesAmazonIpReputationList  
   - Bloquea IPs con mala reputación conocida

   

4. **Common Vulnerabilities:**  
     
   - AWS Managed Rule: AWSManagedRulesCommonRuleSet  
   - Protege contra OWASP Top 10

   

5. **Known Bad Inputs:**  
     
   - AWS Managed Rule: AWSManagedRulesKnownBadInputsRuleSet  
   - Bloquea payloads maliciosos conocidos

**Logging:**

- Todos los requests bloqueados se loguean en CloudWatch  
- Alertas automáticas para patrones de ataque

### 2.2.7 Diagrama de Topología de Red {#2.2.7-diagrama-de-topología-de-red}

\<imagen-1\>

### 2.2.8 Estrategia de Aislamiento {#2.2.8-estrategia-de-aislamiento}

La arquitectura implementa múltiples capas de aislamiento:

1. **Aislamiento de Red**: VPC privada sin acceso directo desde Internet  
2. **Aislamiento de Subredes**: Recursos críticos en subredes privadas  
3. **Aislamiento de Security Groups**: Reglas restrictivas por componente  
4. **Aislamiento de IAM**: Roles con mínimo privilegio

**Aislamiento de Datos**: Encriptación en todas las capas

# Capítulo 3: Diseño esquema de datos {#capítulo-3:-diseño-esquema-de-datos}

## 3.1 Introducción al Modelo de Datos {#3.1-introducción-al-modelo-de-datos}

### 3.1.1 Objetivo del Capítulo {#3.1.1-objetivo-del-capítulo}

Este capítulo documenta el diseño completo del esquema de datos que se implementará en Amazon Redshift, manteniendo compatibilidad con el esquema actual de MySQL de Janis. El diseño incluye:

- Mapeo de 26 tablas de MySQL a Redshift  
- Conversiones de tipos de datos  
- Estrategias de distribución y ordenamiento  
- Manejo de Data Gaps identificados  
- Scripts DDL para creación de tablas

### 3.1.2 Principios de Diseño {#3.1.2-principios-de-diseño}

1. **Compatibilidad**: Mantener nombres de tablas y columnas idénticos cuando sea posible  
2. **Optimización**: Aprovechar características de Redshift (columnar, compresión)  
3. **Simplicidad**: No implementar foreign keys debido a naturaleza parcial de datos  
4. **Performance**: Optimizar distribution y sort keys para queries de BI  
5. **Escalabilidad**: Diseñar para crecimiento futuro de datos

---

## 3.2 Resumen de Tablas {#3.2-resumen-de-tablas}

### 3.2.1 Inventario Completo de Tablas {#3.2.1-inventario-completo-de-tablas}

| \# | Tabla | Campos BI | Campos Mapeados | Gaps Críticos | Prioridad |
| :---- | :---- | :---- | :---- | :---- | :---- |
| 1 | wms\_orders | 43 | 39 | 4 | ALTA |
| 2 | wms\_order\_shipping | 14 | 14 | 0 | ALTA |
| 3 | wms\_logistic\_carriers | 6 | 6 | 0 | MEDIA |
| 4 | wms\_order\_items | 18 | 18 | 0 | ALTA |
| 5 | wms\_order\_item\_weighables | 7 | 7 | 0 | MEDIA |
| 6 | wms\_order\_status\_changes | 6 | 6 | 0 | ALTA |
| 7 | wms\_stores | 23 | 23 | 0 | ALTA |
| 8 | wms\_logistic\_delivery\_planning | 26 | 21 | 5 | ALTA |
| 9 | wms\_logistic\_delivery\_ranges | 6 | 6 | 0 | MEDIA |
| 10 | wms\_order\_payments | 11 | 10 | 1 | ALTA |
| 11 | wms\_order\_payments\_connector\_responses | 5 | 3 | 2 | MEDIA |
| 12 | wms\_order\_custom\_data\_fields | 5 | 4 | 1 | BAJA |
| 13 | products | 20 | 15 | 2 | ALTA |
| 14 | skus | 32 | 32 | 5 | ALTA |
| 15 | categories | 5 | 5 | 0 | MEDIA |
| 16 | admins | 7 | 7 | 0 | BAJA |
| 17 | price | 10 | 10 | 0 | ALTA |
| 18 | brands | 4 | 4 | 0 | MEDIA |
| 19 | customers | 13 | 13 | 2 | ALTA |
| 20 | wms\_order\_picking | 6 | 6 | 0 | ALTA |
| 21 | picking\_round\_orders | 2 | 2 | 1 | MEDIA |
| 22 | stock | 12 | 12 | 0 | ALTA |
| 23 | promotional\_prices | 15 | 15 | 0 | MEDIA |
| 24 | promotions | 12 | 12 | 0 | MEDIA |
| 25 | invoices | 6 | 6 | 0 | ALTA |
| 26 | ff\_comments | 7 | TBD | TBD | BAJA |

**Totales:**

- Campos utilizados por BI: 314  
- Campos mapeados: \~305  
- Gaps críticos identificados: 23  
- Cobertura general: \~97%

---

## 3.3 Conversiones de Tipos de Datos {#3.3-conversiones-de-tipos-de-datos}

### 3.3.1 Mapeo de Tipos MySQL → Redshift {#3.3.1-mapeo-de-tipos-mysql-→-redshift}

| Tipo MySQL | Tipo Redshift | Notas |
| :---- | :---- | :---- |
| BIGINT | BIGINT | Directo |
| INT | INTEGER | Directo |
| TINYINT(1) | BOOLEAN | Conversión 0/1 → false/true |
| VARCHAR(n) | VARCHAR(n) | Directo, max 65535 |
| TEXT | VARCHAR(65535) | Redshift no tiene TEXT |
| DECIMAL(p,s) | NUMERIC(p,s) | Directo |
| DATETIME | TIMESTAMP | Directo |
| DATE | DATE | Directo |
| TIMESTAMP | TIMESTAMP | Conversión Unix → ISO 8601 |
| JSON | VARCHAR(65535) | Redshift tiene SUPER pero usamos VARCHAR |
| ENUM | VARCHAR(50) | Conversión a string |

### 3.3.2 Conversiones Especiales {#3.3.2-conversiones-especiales}

#### Timestamps Unix a ISO 8601 {#timestamps-unix-a-iso-8601}

**Origen (MySQL):**

```sql
date_created BIGINT -- 1698172800 (Unix timestamp)
```

**Destino (Redshift):**

```sql
date_created TIMESTAMP -- '2023-10-24 16:00:00'
```

**Transformación en Glue:**

```py
from datetime import datetime

def convert_unix_to_timestamp(unix_ts):
    if unix_ts is None:
        return None
    return datetime.fromtimestamp(unix_ts).strftime('%Y-%m-%d %H:%M:%S')
```

#### Boolean de TINYINT {#boolean-de-tinyint}

**Origen (MySQL):**

```sql
is_active TINYINT(1) -- 0 o 1
```

**Destino (Redshift):**

```sql
is_active BOOLEAN -- false o true
```

**Transformación en Glue:**

```py
def convert_tinyint_to_boolean(value):
    if value is None:
        return None
    return value == 1
```

---

## 3.4 Estrategias de Distribución y Ordenamiento {#3.4-estrategias-de-distribución-y-ordenamiento}

### 3.4.1 Distribution Keys {#3.4.1-distribution-keys}

Redshift distribuye datos entre nodos usando tres estrategias:

**KEY Distribution:**

- Distribuye filas basándose en valores de una columna  
- Usado para tablas grandes que se joinean frecuentemente  
- Ejemplo: `wms_orders` distribuido por `order_id`

**ALL Distribution:**

- Copia tabla completa en cada nodo  
- Usado para tablas pequeñas de dimensiones  
- Ejemplo: `wms_stores`, `categories`, `brands`

**EVEN Distribution:**

- Distribuye filas uniformemente (round-robin)  
- Usado cuando no hay joins frecuentes  
- Ejemplo: `ff_comments`

### 3.4.2 Sort Keys {#3.4.2-sort-keys}

Redshift ordena datos físicamente usando sort keys:

**Compound Sort Key:**

- Ordena por múltiples columnas en orden  
- Mejor para queries con filtros en orden específico  
- Ejemplo: `(date_created, status)` en `wms_orders`

**Interleaved Sort Key:**

- Da igual peso a todas las columnas  
- Mejor para queries con filtros variables  
- Más costoso de mantener (VACUUM)

### 3.4.3 Estrategia por Tabla {#3.4.3-estrategia-por-tabla}

| Tabla | Distribution Style | Distribution Key | Sort Key | Justificación |
| :---- | :---- | :---- | :---- | :---- |
| wms\_orders | KEY | order\_id | date\_created | Tabla grande, joins frecuentes por order\_id |
| wms\_order\_items | KEY | order\_id | (order\_id, item\_id) | Join con orders, filtros por item |
| wms\_stores | ALL | \- | store\_id | Tabla pequeña (\~50 tiendas) |
| customers | KEY | customer\_id | date\_created | Tabla grande, joins por customer\_id |
| products | KEY | product\_id | (category, brand) | Joins frecuentes, filtros por categoría |
| skus | KEY | sku\_id | (product\_id, sku\_id) | Join con products |
| stock | KEY | sku\_id | (store\_id, sku\_id) | Queries por tienda y SKU |

---

## 3.5 Definición de Tablas Principales {#3.5-definición-de-tablas-principales}

### 3.5.1 Tabla: wms\_orders {#3.5.1-tabla:-wms_orders}

**Descripción:** Tabla principal de órdenes de compra.

**DDL:**

```sql
CREATE TABLE wms_orders (
    -- Identificadores
    order_id VARCHAR(50) NOT NULL,
    client_id VARCHAR(50),
    store_id VARCHAR(50),
    
    -- Información del cliente
    customer_id VARCHAR(50),
    customer_email VARCHAR(255),
    customer_phone VARCHAR(50),
    
    -- Fechas (convertidas de Unix timestamp)
    date_created TIMESTAMP,
    date_modified TIMESTAMP,
    date_delivered TIMESTAMP,
    
    -- Estados
    status VARCHAR(50),
    status_code INTEGER,
    
    -- Totales
    total_amount NUMERIC(10,2),
    total_discount NUMERIC(10,2),
    total_shipping NUMERIC(10,2),
    
    -- Campos calculados
    total_changes NUMERIC(10,2), -- Calculado: amount - originalAmount
    
    -- Flags
    is_test BOOLEAN,
    has_invoice BOOLEAN,
    
    -- Metadatos
    source_system VARCHAR(50) DEFAULT 'janis',
    ingestion_timestamp TIMESTAMP DEFAULT GETDATE(),
    
    PRIMARY KEY (order_id)
)
DISTSTYLE KEY
DISTKEY (order_id)
SORTKEY (date_created);
```

**Data Gaps Críticos:**

- `items_substituted_qty`: No disponible en API  
- `items_qty_missing`: No disponible en API  
- `points_card`: No disponible en API  
- `status_vtex`: No disponible en API

**Mitigación:**

- Coordinar con Janis para agregar campos a API  
- Usar datos históricos del backup para análisis retrospectivo  
- Documentar limitación en reportes afectados

### 3.5.2 Tabla: wms\_order\_items {#3.5.2-tabla:-wms_order_items}

**DDL:**

```sql
CREATE TABLE wms_order_items (
    -- Identificadores
    item_id VARCHAR(50) NOT NULL,
    order_id VARCHAR(50) NOT NULL,
    sku_id VARCHAR(50),
    product_id VARCHAR(50),
    
    -- Cantidades
    quantity INTEGER,
    quantity_picked INTEGER, -- Disponible post-picking
    quantity_invoiced INTEGER, -- Disponible post-facturación
    quantity_returned INTEGER, -- Disponible si hay devoluciones
    
    -- Precios
    unit_price NUMERIC(10,2),
    total_price NUMERIC(10,2),
    discount NUMERIC(10,2),
    
    -- Información del producto
    product_name VARCHAR(500),
    sku_name VARCHAR(500),
    
    -- Sustituciones
    substitute_of VARCHAR(50), -- ID del item original
    substitute_type VARCHAR(20), -- original/substitute/candidate
    
    -- Metadatos
    date_created TIMESTAMP,
    ingestion_timestamp TIMESTAMP DEFAULT GETDATE(),
    
    PRIMARY KEY (item_id)
)
DISTSTYLE KEY
DISTKEY (order_id)
SORTKEY (order_id, item_id);
```

### 3.5.3 Tabla: wms\_stores {#3.5.3-tabla:-wms_stores}

**DDL:**

```sql
CREATE TABLE wms_stores (
    -- Identificadores
    store_id VARCHAR(50) NOT NULL,
    store_code VARCHAR(50),
    client_id VARCHAR(50),
    
    -- Información básica
    name VARCHAR(255),
    address VARCHAR(500),
    city VARCHAR(100),
    state VARCHAR(100),
    country VARCHAR(3), -- ISO3: PER
    postal_code VARCHAR(20),
    
    -- Geolocalización
    latitude NUMERIC(12,9),
    longitude NUMERIC(12,9),
    
    -- Configuración
    is_active BOOLEAN,
    is_pickup_point BOOLEAN,
    apply_quotation BOOLEAN,
    
    -- Horarios (JSON como VARCHAR)
    business_hours VARCHAR(1000),
    
    -- Fechas
    date_created TIMESTAMP,
    date_modified TIMESTAMP,
    
    -- Metadatos
    ingestion_timestamp TIMESTAMP DEFAULT GETDATE(),
    
    PRIMARY KEY (store_id)
)
DISTSTYLE ALL; -- Tabla pequeña, replicada en todos los nodos
```

### 3.5.4 Tabla: customers {#3.5.4-tabla:-customers}

**DDL:**

```sql
CREATE TABLE customers (
    -- Identificadores
    customer_id VARCHAR(50) NOT NULL,
    client_id VARCHAR(50),
    
    -- Información personal
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    email VARCHAR(255),
    phone VARCHAR(50),
    document_type VARCHAR(20),
    document_number VARCHAR(50),
    
    -- Dirección
    address VARCHAR(500),
    city VARCHAR(100),
    state VARCHAR(100),
    postal_code VARCHAR(20),
    
    -- Fechas
    date_created TIMESTAMP,
    date_modified TIMESTAMP,
    
    -- Metadatos
    ingestion_timestamp TIMESTAMP DEFAULT GETDATE(),
    
    PRIMARY KEY (customer_id)
)
DISTSTYLE KEY
DISTKEY (customer_id)
SORTKEY (date_created);
```

**Data Gaps Críticos:**

- `vtex_id`: ID de cliente en VTEX, no disponible  
- `phone_alt`: Teléfono alternativo, no disponible

---

## 3.6 Manejo de Data Gaps {#3.6-manejo-de-data-gaps}

### 3.6.1 Resumen de Gaps Críticos {#3.6.1-resumen-de-gaps-críticos}

| Tabla | Campo Faltante | Impacto en BI | Estrategia de Mitigación |
| :---- | :---- | :---- | :---- |
| wms\_orders | items\_substituted\_qty | Reportes de sustituciones | Calcular desde wms\_order\_items |
| wms\_orders | items\_qty\_missing | Reportes de faltantes | Calcular desde wms\_order\_items |
| wms\_orders | points\_card | Reportes de loyalty | Coordinar con Janis |
| wms\_orders | status\_vtex | Integración VTEX | Usar status de Janis |
| wms\_logistic\_delivery\_planning | dynamic\_quota | Planificación de entregas | Usar quota estático |
| wms\_logistic\_delivery\_planning | carrier | Asignación de carriers | Coordinar con Janis |
| wms\_order\_payments | authorization\_code | Conciliación de pagos | Coordinar con Janis |
| customers | vtex\_id | Integración VTEX | Usar customer\_id de Janis |
| customers | phone\_alt | Contacto alternativo | Usar phone principal |

### 3.6.2 Campos Calculados {#3.6.2-campos-calculados}

Algunos gaps pueden mitigarse calculando valores desde otras tablas:

**items\_substituted\_qty:**

```sql
-- Calcular cantidad de items sustituidos por orden
SELECT 
    order_id,
    COUNT(*) as items_substituted_qty
FROM wms_order_items
WHERE substitute_type = 'substitute'
GROUP BY order_id;
```

**items\_qty\_missing:**

```sql
-- Calcular cantidad faltante por orden
SELECT 
    order_id,
    SUM(quantity - COALESCE(quantity_picked, 0)) as items_qty_missing
FROM wms_order_items
GROUP BY order_id;
```

---

## 3.7 Scripts DDL Completos {#3.7-scripts-ddl-completos}

Cada script incluye:

- Definición completa de columnas con tipos de datos  
- Primary keys (sin foreign keys)  
- Distribution y sort keys optimizados  
- Comentarios explicativos  
- Valores por defecto

**Ejemplo de estructura:**

```sql
-- ============================================
-- Tabla: wms_orders
-- Descripción: Órdenes de compra principales
-- Fuente: API /order + Webhook order.created
-- Actualización: Tiempo real + Batch diario
-- ============================================

CREATE TABLE IF NOT EXISTS wms_orders (
    -- [Definición de columnas]
)
DISTSTYLE KEY
DISTKEY (order_id)
SORTKEY (date_created)
;

-- Comentarios de columnas
COMMENT ON TABLE wms_orders IS 'Órdenes de compra de e-commerce';
COMMENT ON COLUMN wms_orders.order_id IS 'Identificador único de orden';
-- [Más comentarios]
```

# 

# Capítulo 4: Diseño del Proceso: Carga Inicial  (Via backup Base de Datos) {#capítulo-4:-diseño-del-proceso:-carga-inicial-(via-backup-base-de-datos)}

 

Este capítulo describe el diseño detallado del proceso de carga inicial de datos históricos desde un respaldo de la base de datos original de Janis (almacenado en AWS) hacia el Data Lake en AWS y Amazon Redshift. La carga inicial es un proceso crítico que establece el baseline de datos en el nuevo sistema antes de comenzar con las cargas incrementales regulares.  
   
Contexto Crítico: Existe un respaldo completo de la base de datos original de Janis almacenado en AWS (fuera de Redshift), el cual contiene todos los datos históricos necesarios. El nuevo sistema utilizará una instancia de Amazon Redshift completamente nueva (desde cero), sin datos preexistentes. Por lo tanto, la estrategia de carga inicial debe:  
   
\- Utilizar el respaldo completo de AWS como fuente única para la carga inicial  
\- Cargar todos los datos históricos desde el respaldo hacia el Redshift nuevo (vacío)  
\- No requiere verificación de duplicados ya que Redshift estará inicialmente vacío  
\- Omitir la validación de integridad referencial (foreign keys) ya que no se puede garantizar que todos los datos relacionados estén disponibles  
\- Aprovechar la infraestructura AWS existente para optimizar la transferencia de datos  
   
Este enfoque de "carga completa inicial desde respaldo AWS" permite una migración limpia y completa de todos los datos históricos, aprovechando el respaldo disponible y eliminando complejidades de verificación de duplicados.

## 4.1 Architecture {#4.1-architecture}

### 4.1.1 Arquitectura de Alto Nivel {#4.1.1-arquitectura-de-alto-nivel}

La carga inicial sigue una arquitectura de procesamiento por lotes (batch processing) aprovechando el respaldo existente en AWS:

###  {#heading}

### \<imagen-2\>    4.1.2 Componentes Principales

1\. Fuente de Datos: Respaldo completo de la base de datos original de Janis almacenado en AWS  
2\. Redshift Nuevo: Instancia nueva de Amazon Redshift (inicialmente vacía)  
3\. Capa de Extracción: Herramientas de acceso al respaldo AWS (S3, RDS snapshot, o almacenamiento específico)  
4\. S3 Bronze: Almacenamiento de datos raw extraídos del respaldo  
5\. Módulo de Validación: Componente que valida integridad y calidad de datos extraídos  
6\. AWS Glue: Motor de transformación ETL para procesamiento Bronze → Silver → Gold  
7\. S3 Silver/Gold: Capas de datos transformados y curados (todos los datos históricos)  
8\. Amazon Redshift: Data warehouse destino final (todos los datos históricos cargados)  
9\. AWS Glue Data Catalog: Registro de metadatos y esquemas  
10\. Amazon CloudWatch: Monitoreo y logging de todo el proceso

 

 

## 4.2 Componentes e interfaces  {#4.2-componentes-e-interfaces}

###  4.2.1. Módulo de Acceso al Respaldo AWS {#4.2.1.-módulo-de-acceso-al-respaldo-aws}

   
**Responsabilidad**: Acceder y extraer datos desde el respaldo de la base de datos original de Janis almacenado en AWS  
**Componente**: AWS Glue Job \+ Scripts de acceso específicos según el tipo de respaldo  
 Tipos de Respaldo Soportados:  
   
1\. RDS Snapshot:  
   \- Restauración temporal de snapshot para acceso directo  
   \- Conexión via JDBC desde Glue  
   \- Extracción tabla por tabla  
   
2\. Archivos en S3:  
   \- Acceso directo a archivos Parquet/CSV del respaldo  
   \- Lectura optimizada con Spark  
   \- Sin necesidad de restauración  
   
3\. Backup Comprimido:  
   \- Descompresión y procesamiento de archivos SQL  
   \- Conversión a formato columnar  
   \- Procesamiento por lotes  
   
Proceso de Extracción:  
   
1\. Identificación del Tipo de Respaldo: Determinar el formato y ubicación del respaldo AWS  
2\. Configuración de Acceso: Establecer credenciales y permisos necesarios  
3\. Extracción Paralela: Procesar múltiples tablas simultáneamente  
4\. Conversión a Parquet: Estandarizar formato para procesamiento posterior  
5\. Carga a S3 Bronze: Almacenar datos extraídos en capa Bronze  
   
Ventajas del Enfoque:  
\- No impacta sistemas productivos de Janis  
\- Aprovecha infraestructura AWS existente  
\- Transferencia de datos optimizada dentro de AWS  
\- Acceso a datos históricos completos  
\- Paralelización nativa en AWS

 

### 4.2.2. Módulo de Validación de Datos Raw {#4.2.2.-módulo-de-validación-de-datos-raw}

   
**Responsabilidad**: Validar la integridad y calidad de todos los datos extraídos del respaldo AWS  
**Componente**: AWS Glue Job (PySpark)

Validaciones Aplicadas:  
   
1\. Validación de Estructura: Verificar que todas las tablas esperadas estén presentes y con la estructura correcta  
	  
2\. Validación de Completitud: Confirmar que no hay archivos corruptos o incompletos  
	  
3\. Validación de Tipos de Datos: Verificar que los tipos de datos sean consistentes  
	  
4\. Validación de Integridad: Detectar registros duplicados dentro de cada tabla  
   
Proceso de Validación:  
\- Conteo de Registros: Verificar que el conteo de registros por tabla sea consistente  
\- Detección de Nulos: Identificar campos críticos con valores nulos inesperados  
\- Validación de Rangos: Verificar que fechas y valores numéricos estén en rangos válidos  
\- Registros Huérfanos: Documentar registros que referencian claves inexistentes (sin bloquear el proceso)  
 

### 4.2.3. Módulo de Transformación Bronze → Silver {#4.2.3.-módulo-de-transformación-bronze-→-silver}

   
**Responsabilidad**: Normalizar y limpiar todos los datos raw extraídos del respaldo  
**Componente**: AWS Glue Job (PySpark)  
   
Transformaciones Aplicadas:  
   
1\. Conversión de Tipos de Datos: Transformar tipos de datos MySQL a tipos compatibles con Redshift  
2\. Normalización de Formatos: Estandarizar formatos de fechas, números y texto  
3\. Extracción de Campos Anidados: Procesar campos JSON o XML embebidos  
4\. Limpieza de Datos: Eliminar caracteres especiales y normalizar encoding  
5\. Particionamiento: Organizar datos por fechas para optimizar consultas posteriores

 4.2.4. Módulo de Transformación Silver → Gold  
   
**Responsabilidad**: Generar tablas finales optimizadas para Redshift, sin validar integridad referencial  
 **Componente**: AWS Glue Job (PySpark)  
   
Transformaciones Aplicadas:  
   
1\. Optimización de Esquema: Generar esquema optimizado para Redshift (distribution keys, sort keys)  
2\. Cálculos Derivados: Procesar campos calculados y métricas agregadas necesarias  
3\. Eliminación de Gaps: Identificar y documentar datos faltantes sin bloquear la carga  
4\. Formato Final: Convertir a formato óptimo para comando COPY de Redshift  
5\. Omisión de Integridad Referencial: Cargar datos sin validar foreign keys (documentando huérfanos)  
 

### 4.2.5. Módulo de Carga a Redshift {#4.2.5.-módulo-de-carga-a-redshift}

   
**Responsabilidad**: Cargar todos los datos curados desde S3 Gold a Amazon Redshift nuevo  
**Componente**: AWS Glue Job \+ Redshift COPY Command  
   
Proceso de Carga:  
   
1\. Preparación de Redshift: Crear cluster nuevo y configurar esquemas de base de datos  
2\. Creación de Tablas: Generar todas las tablas con esquemas optimizados para Redshift  
3\. Carga Masiva: Usar comando COPY para cargar datos desde S3 Gold de forma paralela  
4\. Configuración Final: Aplicar índices, estadísticas y configuraciones de performance  
5\. Sin Validación de FKs: Cargar datos sin restricciones de integridad referencial  
 

### 4.2.6. Módulo de Validación y Reconciliación {#4.2.6.-módulo-de-validación-y-reconciliación}

   
**Responsabilidad**: Verificar la completitud y calidad de los datos cargados (sin validar integridad referencial)  
**Componente**: AWS Glue Job \+ Python Scripts  
   
Validaciones Implementadas:  
   
1\. Conteo de Registros: Verificar que el conteo total de registros en Redshift coincida con el respaldo original  
   
2\. Validación de Checksums (para datos críticos): Comparar checksums entre S3 Gold y Redshift para datos críticos  
   
3\. Validación de Tipos de Datos: Verificar que los tipos de datos en Redshift coincidan con el esquema esperado y detectar conversiones incorrectas  
   
4\. Validación de Valores Nulos: Verificar que campos NOT NULL no contengan nulos y registrar campos con alta proporción de nulos  
   
5\. Validación de Rangos de Fechas: Verificar que los datos relacionados a fechas coincidan con un rango válido  
   
6\. NO se valida integridad referencial: No se verifican foreign keys, se aceptan registros huérfanos y se documenta en el reporte de validación qué tablas tienen registros sin relaciones  
 

## 4.3 Data Models {#4.3-data-models}

   
A continuación, se muestra cómo se estructuran los datos en S3

### 4.3.1 S3 Bronze (Raw Data) {#4.3.1-s3-bronze-(raw-data)}

s3://cencosud-janis-datalake-bronze/  
├── initial-load/  
│   ├── wms\_orders/  
│   │   ├── export\_20251209\_part\_001.parquet  
│   │   ├── export\_20251209\_part\_002.parquet  
│   │   └── \_metadata.json  
│   ├── wms\_order\_items/  
│   │   └── export\_20251209.parquet  
│   └── \[otras 23 tablas\]/

 

### 4.3.2 S3 Silver (Cleaned Data \- Todos los datos históricos) {#4.3.2-s3-silver-(cleaned-data---todos-los-datos-históricos)}

s3://cencosud-janis-datalake-silver/  
├── initial-load/  
│   ├── wms\_orders/  
│   │   ├── year=2024/month=01/day=15/data.parquet  
│   │   ├── year=2024/month=01/day=16/data.parquet  
│   │   └── \_metadata.json  
 

### 4.3.3 S3 Gold (Curated Data \- Optimizado para Redshift) {#4.3.3-s3-gold-(curated-data---optimizado-para-redshift)}

s3://cencosud-janis-datalake-gold/  
├── initial-load/  
│   ├── wms\_orders/  
│   │   ├── year=2024/month=01/data.parquet  
│   │   ├── year=2024/month=02/data.parquet  
│   │   └── \_manifest.json

### 4.3.4 Monitoreo y Alertas {#4.3.4-monitoreo-y-alertas}

Se llevará registro de los siguientes tópicos con respecto a la información de la carga  
   
\- Errores críticos  
\- Advertencias  
\- Información general


## 4.4 Testing Strategy {#4.4-testing-strategy}

### 4.4.1 Enfoque de Testing {#4.4.1-enfoque-de-testing}

La estrategia de testing para la carga inicial se enfocará en:  
1\. Unit Tests: Validar funciones individuales de transformación y validación  
2\. Integration Tests: Verificar el flujo completo de datos entre componentes  
3\. Data Quality Tests: Asegurar la calidad y completitud de los datos cargados  
4\. Performance Tests: Validar tiempos de ejecución y uso de recursos

 

### 4.4.2 Criterios de Aceptación {#4.4.2-criterios-de-aceptación}

Para considerar exitosa la carga inicial, se deben cumplir:  
   
1\. Completitud: 100% de registros históricos cargados desde el respaldo AWS  
2\. Calidad: \< 1% de registros en DLQ  
3\. Performance: Tiempo de ejecución \< 8 horas para todas las 25 tablas  
4\. Validación: Conteo de registros coincide entre respaldo original y Redshift  
5\. Esquema: Esquema en Redshift optimizado y funcionando correctamente  
6\. Registros Huérfanos: Se documentan, pero no bloquean la carga  
 

## 4.5 Uso del Respaldo AWS {#4.5-uso-del-respaldo-aws}

### 4.5.1 Beneficios Operacionales {#4.5.1-beneficios-operacionales}

1\. Reducción de Impacto en Sistemas Productivos:  
   \- No requiere acceso directo a la base de datos productiva de Janis  
   \- Elimina la carga adicional en sistemas críticos durante la migración  
   \- Permite ejecutar la carga inicial sin afectar operaciones diarias  
   
2\. Optimización de Transferencia de Datos:  
   \- Transferencia interna dentro de la infraestructura AWS  
   \- Mayor ancho de banda y menor latencia  
   \- Reducción significativa de costos de transferencia de datos  
   \- Aprovechamiento de la red backbone de AWS  
   
3\. Disponibilidad y Confiabilidad:  
   \- Acceso 24/7 al respaldo sin dependencias externas  
   \- No requiere coordinación con equipos de Janis para acceso  
   \- Respaldo completo garantiza disponibilidad de todos los datos históricos  
   \- Reducción de puntos de falla en el proceso  
   
4\. Flexibilidad de Ejecución:  
   \- Posibilidad de ejecutar múltiples intentos sin impacto  
   \- Facilita pruebas y validaciones previas  
   \- Permite ejecución en horarios óptimos para Cencosud  
   \- Capacidad de pausar y reanudar el proceso según necesidades  
 

### 4.5.2 Beneficios Técnicos {#4.5.2-beneficios-técnicos}

   
1\. Consistencia de Datos:

   \- Snapshot consistente en el tiempo del respaldo  
   \- Eliminación de problemas de concurrencia durante extracción  
   \- Datos estables para validaciones y reconciliaciones  
   
2\. Escalabilidad:  
   \- Aprovechamiento de recursos AWS elásticos  
   \- Paralelización optimizada dentro del ecosistema AWS  
   \- Capacidad de escalar recursos según demanda del proceso  
   
3\. Integración Nativa:  
   \- Integración directa con servicios AWS (Glue, S3, Redshift)  
   \- Uso de conectores nativos optimizados  
   \- Aprovechamiento de metadatos y catálogos existentes  
 

## 4.6 Consideraciones de seguridad {#4.6-consideraciones-de-seguridad}

   
Se tomarán en cuenta distintas medidas de seguridad específicas para el acceso al respaldo AWS y la carga de datos sensibles:

### 4.6.1 Seguridad del Respaldo AWS {#4.6.1-seguridad-del-respaldo-aws}

1\. Acceso Controlado al Respaldo:  
   \- Uso de IAM roles específicos para acceso al respaldo  
   \- Principio de menor privilegio para permisos  
   \- Auditoría de accesos al respaldo mediante CloudTrail  
   \- Rotación de credenciales de acceso  
   
2\. Cifrado de Datos:  
   \- Verificar cifrado en reposo del respaldo AWS  
   \- Cifrado en tránsito durante extracción (TLS 1.2+)  
   \- Cifrado en S3 Bronze/Silver/Gold (SSE-S3 o SSE-KMS)  
   \- Cifrado en Redshift con claves gestionadas  
   
3\. Transferencia Segura:  
   \- Uso de VPC endpoints para transferencias internas AWS  
   \- Evitar tráfico por internet público  
   \- Monitoreo de transferencias con VPC Flow Logs  
   \- Validación de integridad durante transferencia  
   
4\. Datos Sensibles:  
   \- Identificación de campos PII en el respaldo  
   \- Aplicación de políticas de enmascaramiento si requerido  
   \- Registro de auditoría para acceso a datos sensibles  
   \- Cumplimiento con políticas de retención de Cencosud  
   
5\. Aislamiento de Procesos:  
   \- Ejecución de Glue Jobs en subredes privadas  
   \- Restricción de acceso de red mediante Security Groups  
   \- Separación de ambientes (dev/test/prod)  
   \- Monitoreo continuo con CloudWatch y GuardDuty

 

### 4.6.2 Fases de Ejecución {#4.6.2-fases-de-ejecución}

 

La carga inicial se ejecutará en 4 fases principales, con checkpoints de validación entre cada una.

#### 4.6.2.1 Fase 1: Preparación (Pre-Migration) {#4.6.2.1-fase-1:-preparación-(pre-migration)}

   
Actividades:  
   
1\. Validar Acceso al Respaldo AWS:  
   \- Identificar ubicación y formato del respaldo de Janis en AWS  
   \- Validar permisos de acceso al respaldo  
   \- Probar conectividad y acceso a los datos del respaldo  
   
2\. Preparar Ambiente AWS:  
   \- Crear nuevo cluster de Redshift optimizado  
   \- Generar buckets S3 necesarios para el proceso  
   \- Configurar Roles IAM con permisos específicos  
   \- Configurar VPC y Security Groups  
   \- Crear Glue Data Catalog databases  
   
3\. Validar Conectividad:  
   \- Test de conexión al nuevo Redshift  
   \- Validar acceso a buckets S3 del Data Lake  
   \- Verificar permisos de AWS Glue  
   
4\. Análisis del Respaldo:  
   \- Inventariar todas las tablas disponibles en el respaldo  
   \- Analizar esquemas y tipos de datos del respaldo  
   \- Diseñar esquemas optimizados para Redshift  
   \- Estimar volumen total de datos a migrar  
   
Criterios de Éxito:  
\- Acceso validado al respaldo AWS de Janis  
\- Nuevo cluster de Redshift creado y configurado  
\- Ambiente AWS configurado y probado  
\- Conectividad validada a todos los sistemas  
\- Inventario completo del respaldo documentado  
\- Esquemas de Redshift diseñados y validados

 

#### 4.6.2.2 Fase 2: Extracción desde Respaldo AWS (Extraction & Landing)  {#4.6.2.2-fase-2:-extracción-desde-respaldo-aws-(extraction-&-landing)}

Actividades:  
   
1\. Acceso y Extracción del Respaldo:  
   \- Acceder al respaldo completo de Janis en AWS  
   \- Extraer datos de las 25 tablas críticas  
   \- Convertir a formato Parquet optimizado  
   \- Aplicar compresión y particionamiento  
   
2\. Carga a S3 Bronze:  
   \- Transferir datos extraídos a S3 Bronze  
   \- Organizar por tabla y fecha de extracción  
   \- Generar metadata para cada tabla  
   \- Crear manifiestos de archivos  
   
3\. Validación de Integridad:  
   \- Verificar completitud de extracción  
   \- Validar checksums de archivos  
   \- Confirmar estructura de datos  
   \- Monitorear con CloudWatch  
   
Criterios de Éxito:  
\- 25 tablas extraídas exitosamente del respaldo AWS  
\- Datos cargados completamente en S3 Bronze  
\- Metadata generada para cada tabla  
\- Validación de integridad pasada  
\- Tiempo de extracción dentro de ventana estimada

\- Logs de proceso disponibles en CloudWatch

 

#### 4.6.2.3 Fase 3: Transformación y Curación (Transformation & Curation)  {#4.6.2.3-fase-3:-transformación-y-curación-(transformation-&-curation)}

Actividades:  
   
1\. Validación de Datos Raw:  
   \- Ejecutar validaciones de integridad en S3 Bronze  
   \- Identificar y documentar registros problemáticos  
   \- Generar reporte de calidad de datos  
   
2\. Transformación Bronze → Silver:  
   \- Aplicar limpieza y normalización de datos  
   \- Convertir tipos de datos para compatibilidad con Redshift  
   \- Particionar datos por fechas para optimización  
   
3\. Transformación Silver → Gold:  
   \- Generar esquemas optimizados para Redshift  
   \- Aplicar cálculos derivados necesarios  
   \- Preparar datos en formato óptimo para COPY  
   
Criterios de Éxito:  
\- Validaciones de datos raw completadas  
\- Transformaciones Bronze → Silver completadas para todas las tablas  
\- Transformaciones Silver → Gold completadas  
\- Esquema optimizado para Redshift generado  
\- \< 1% de registros en DLQ

 

#### 4.6.2.4 Fase 4: Carga y Validación Final (Load & Validation) {#4.6.2.4-fase-4:-carga-y-validación-final-(load-&-validation)}

Actividades:  
   
1\. Carga Masiva a Redshift:  
   \- Crear todas las tablas en el nuevo Redshift  
   \- Ejecutar comandos COPY paralelos desde S3 Gold  
   \- Monitorear progreso y performance de carga  
   
2\. Validación de Datos Cargados:  
   \- Verificar conteos de registros  
   \- Validar checksums de datos críticos  
   \- Confirmar tipos de datos y esquemas  
   
3\. Configuración Final:  
   \- Aplicar índices y estadísticas  
   \- Configurar distribución y sort keys  
   \- Optimizar configuraciones de cluster  
   
4\. Reconciliación con Equipo de BI:  
   \- Validar conectividad desde herramientas de BI  
   \- Verificar que consultas básicas funcionan  
   \- Documentar cualquier discrepancia  
   
Criterios de Éxito:  
\- Todas las 25 tablas cargadas exitosamente en Redshift  
\- Validaciones de datos pasadas (con excepción de FK)  
\- Configuraciones de performance aplicadas  
\- Equipo de BI confirma acceso y funcionalidad básica  
\- Reporte final de migración generado

 

#### 4.6.2.5 Criterios de Éxito Global {#4.6.2.5-criterios-de-éxito-global}

Para considerar exitosa la carga inicial completa:  
   
1\. Completitud: 100% de registros históricos cargados desde respaldo AWS  
2\. Calidad: \< 1% de registros en DLQ  
3\. Performance: Tiempo total \< 24 horas  
4\. Validación: Todas las validaciones pasadas (excepto FK)  
5\. BI: Herramientas de BI pueden conectarse y consultar datos  
6\. Documentación: Reporte final entregado y aprobado  
7\. Registros Huérfanos: Documentados y aceptados por el negocio

# Capítulo 5: Diseño del Proceso: Cargas Regulares (Operación DataOps) {#capítulo-5:-diseño-del-proceso:-cargas-regulares-(operación-dataops)}

## 5.1 Introducción {#5.1-introducción}

### 5.1.1 Objetivo del Proceso {#5.1.1-objetivo-del-proceso}

El proceso de cargas regulares constituye el núcleo operativo de la solución de integración de datos entre Janis y el Data Lake de Cencosud en AWS. A diferencia de la carga inicial que migra datos históricos de forma masiva, este proceso está diseñado para mantener la información actualizada de manera continua y confiable, capturando cambios en tiempo casi real.

El objetivo principal es establecer un flujo de datos robusto y escalable que:

- Capture eventos de negocio críticos desde Janis mediante notificaciones webhook  
- Consulte periódicamente las APIs de Janis para obtener actualizaciones de datos transaccionales  
- Procese y transforme los datos a través de una arquitectura de capas (Bronze, Silver, Gold)  
- Garantice la disponibilidad de información actualizada para análisis de BI en Power BI  
- Mantenga la integridad y trazabilidad de los datos a lo largo de todo el pipeline

### 5.1.2 Alcance de las Cargas Regulares {#5.1.2-alcance-de-las-cargas-regulares}

**Datos en Alcance:**

- **Eventos transaccionales**: Órdenes nuevas, cambios de estado, actualizaciones de envío  
- **Datos maestros**: Productos, SKUs, precios, inventario, tiendas  
- **Datos operacionales**: Picking, facturación, pagos, devoluciones  
- **Frecuencia de actualización**: Variable según tipo de dato (tiempo real a 5 minutos)

**Fuera de Alcance:**

- Datos históricos previos a la fecha de go-live (manejados por carga inicial)  
- Datos no expuestos por las APIs de Janis  
- Procesamiento de datos en tiempo real estricto (\< 1 segundo)

### 5.1.3 Principios de Diseño {#5.1.3-principios-de-diseño}

El diseño del proceso de cargas regulares se fundamenta en los siguientes principios arquitectónicos:

**1\. Arquitectura Híbrida de Ingesta**

Se implementa una estrategia dual que combina dos mecanismos complementarios:

- **Webhooks para eventos críticos**: Janis notifica proactivamente cuando ocurren eventos importantes (nueva orden, cambio de estado, actualización de envío). Esto permite reaccionar rápidamente a cambios de negocio sin necesidad de polling constante.  
    
- **Polling periódico para datos transaccionales**: El sistema consulta las APIs de Janis cada 5 minutos aproximadamente para obtener actualizaciones de órdenes e ítems. Esta estrategia garantiza que no se pierda información incluso si un webhook falla o se pierde.

**2\. Arquitectura de Capas con Apache Iceberg**

Los datos fluyen a través de tres capas conceptuales, cada una con un propósito específico:

- **Bronze (Raw)**: Almacena datos tal como llegan desde Janis, sin transformaciones  
- **Silver (Cleansed)**: Contiene datos limpios, normalizados y enriquecidos  
- **Gold (Curated)**: Presenta datos agregados y optimizados para consumo de BI

**3\. Idempotencia y Deduplicación**

Dado que el mismo dato puede llegar tanto por webhook como por polling, el sistema debe ser capaz de identificar y eliminar duplicados. Cada registro se identifica de forma única mediante claves de negocio (order\_id, item\_id, etc.) y timestamps de modificación.

**4\. Resiliencia y Recuperación**

El diseño contempla múltiples mecanismos de recuperación ante fallos:

- Reintentos automáticos con backoff exponencial  
- Almacenamiento persistente en cada capa para permitir reprocesamiento  
- Monitoreo continuo con alertas proactivas  
- Capacidad de replay desde cualquier punto del pipeline

**5\. Escalabilidad Horizontal**

Todos los componentes están diseñados para escalar horizontalmente según la carga:

- API Gateway maneja miles de webhooks concurrentes  
- Kinesis Firehose escala automáticamente según throughput  
- AWS Glue permite agregar workers según necesidad  
- Apache Iceberg soporta petabytes de datos sin degradación

---

## 5.2 Arquitectura General del Proceso {#5.2-arquitectura-general-del-proceso}

### 5.2.1 Vista de Alto Nivel {#5.2.1-vista-de-alto-nivel}

La arquitectura del proceso de cargas regulares se organiza en cinco capas funcionales que trabajan de forma coordinada:

**Capa 1: Ingesta Dual (Webhooks \+ Polling)**

Esta capa es el punto de entrada de todos los datos desde Janis. Opera bajo un modelo híbrido:

- **Webhooks**: Janis envía notificaciones HTTP POST a endpoints específicos en API Gateway cuando ocurren eventos relevantes. Estas notificaciones contienen información mínima (tipo de evento, ID de entidad afectada, timestamp) y actúan como "gatillos" que indican que hay nueva información disponible.  
    
- **Polling Periódico**: Un proceso orquestado por Apache Airflow consulta las APIs de Janis cada 5 minutos para obtener órdenes e ítems actualizados. Este mecanismo complementa los webhooks y garantiza que no se pierda información.

**Capa 2: Buffer y Persistencia (Kinesis Firehose \+ S3 Bronze)**

Los datos ingresados se almacenan inmediatamente en S3 en formato raw (JSON) sin transformaciones. Kinesis Firehose actúa como buffer inteligente que:

- Agrupa múltiples eventos en lotes para optimizar escrituras a S3  
- Particiona automáticamente los datos por fecha y tipo de evento  
- Garantiza durabilidad mediante replicación automática en múltiples zonas de disponibilidad  
- Permite configurar el tamaño de lote y tiempo de espera según necesidades

**Capa 3: Procesamiento y Transformación (AWS Glue \+ Iceberg Silver)**

AWS Glue ejecuta jobs de transformación que:

- Leen datos raw desde S3 Bronze  
- Aplican limpieza, normalización y enriquecimiento  
- Convierten tipos de datos (timestamps Unix a ISO 8601, booleans, decimales)  
- Manejan Data Gaps identificados mediante cálculos derivados  
- Escriben resultados en tablas Apache Iceberg en la capa Silver

**Capa 4: Orquestación (Apache Airflow en MWAA)**

Apache Airflow coordina todos los workflows mediante DAGs (Directed Acyclic Graphs) que:

- Programan ejecuciones periódicas de polling  
- Gestionan dependencias entre tareas  
- Implementan lógica de reintentos y manejo de errores  
- Monitorean el estado de cada pipeline  
- Generan métricas y logs para observabilidad

**Capa 5: Disponibilización (Redshift \+ Power BI)**

Los datos transformados se cargan en Amazon Redshift para consumo de BI:

- Carga incremental desde tablas Iceberg Silver/Gold  
- Optimización mediante comandos VACUUM y ANALYZE  
- Exposición de vistas y tablas a Power BI  
- Actualización según SLAs definidos con el negocio

### 5.2.2 Diagrama de Flujo Completo {#5.2.2-diagrama-de-flujo-completo}

\<imagen-3\>  
---

## 5.3 Capa de Ingesta Dual: Webhooks y Polling {#5.3-capa-de-ingesta-dual:-webhooks-y-polling}

### 5.3.1 Estrategia de Ingesta Híbrida {#5.3.1-estrategia-de-ingesta-híbrida}

La decisión de implementar una estrategia dual de ingesta responde a la necesidad de balancear dos objetivos aparentemente contradictorios:

**Objetivo 1: Baja Latencia**

Los eventos críticos de negocio (nueva orden, cambio de estado a "entregado", actualización de envío) deben reflejarse rápidamente en el sistema de BI para permitir toma de decisiones oportuna. Los webhooks permiten notificaciones en tiempo casi real (segundos) sin necesidad de polling constante.

**Objetivo 2: Completitud y Confiabilidad**

Los webhooks, por su naturaleza, pueden perderse debido a problemas de red, timeouts, o indisponibilidad temporal del receptor. El polling periódico actúa como red de seguridad que garantiza que todos los datos eventualmente se capturen, incluso si las notificaciones webhook fallan.

### 5.3.2 Webhooks: Notificaciones de Eventos {#5.3.2-webhooks:-notificaciones-de-eventos}

**Funcionamiento Conceptual**

Cuando ocurre un evento relevante en Janis (por ejemplo, se crea una nueva orden), el sistema Janis envía una notificación HTTP POST a un endpoint específico en API Gateway. Esta notificación contiene información mínima:

- Tipo de evento (order.created, order.updated, shipping.updated)  
- ID de la entidad afectada (order\_id)  
- Timestamp del evento  
- Firma digital para validación de autenticidad

**Importante**: El webhook NO contiene los datos completos de la orden. Es simplemente una notificación de que algo cambió. El sistema receptor debe entonces consultar la API de Janis para obtener los datos completos.

**Endpoints de Webhook en API Gateway**

Eventualmente se configuran múltiples endpoints, uno por tipo de evento:

- `/webhook/order/created`: Nueva orden creada  
- `/webhook/order/updated`: Orden actualizada (cambio de estado, modificación de items)  
- `/webhook/shipping/updated`: Información de envío actualizada  
- `/webhook/payment/updated`: Estado de pago actualizado  
- `/webhook/picking/completed`: Proceso de picking completado

**Procesamiento de Webhooks**

Cuando API Gateway recibe un webhook:

1. **Validación de Firma**: Se verifica la firma digital usando una clave secreta compartida con Janis para garantizar que la notificación es auténtica y no ha sido alterada.  
     
2. **Enriquecimiento**: Una función Lambda se activa automáticamente y consulta la API de Janis para obtener los datos completos de la entidad (por ejemplo, GET /order/{order\_id}).  
     
3. **Envío a Buffer**: Los datos completos se envían a Kinesis Firehose para persistencia en S3 Bronze.  
     
4. **Respuesta Rápida**: API Gateway responde inmediatamente con HTTP 200 OK a Janis para confirmar recepción, sin esperar a que el procesamiento completo termine. Esto evita timeouts.

**Configuración de Seguridad**

- **Autenticación**: Validación de firma HMAC-SHA256 en cada webhook  
- **Rate Limiting**: Límite de 1000 requests por segundo por endpoint  
- **Throttling**: Protección contra ráfagas mediante token bucket  
- **IP Whitelisting**: Solo se aceptan webhooks desde IPs conocidas de Janis

### 5.3.3 Polling Periódico: Consulta Activa de APIs {#5.3.3-polling-periódico:-consulta-activa-de-apis}

**Justificación del Polling**

A pesar de contar con webhooks, se implementa polling periódico por las siguientes razones:

1. **Redundancia**: Si un webhook se pierde, el polling lo capturará en la siguiente ejecución  
2. **Datos históricos**: Permite recuperar datos de períodos donde el sistema estuvo inactivo  
3. **Validación**: Sirve como mecanismo de validación cruzada contra los webhooks  
4. **Datos no notificados**: Algunos cambios menores pueden no generar webhooks

**Frecuencia de Polling**

Se establece una frecuencia de **5 minutos** para órdenes e ítems, basándose en:

- Balance entre frescura de datos y carga en APIs de Janis  
- Requisitos de SLA de BI (datos actualizados cada 10-15 minutos)  
- Capacidad de procesamiento del pipeline

Para otros tipos de datos, la frecuencia varía:

- **Productos y SKUs**: Cada 1 hora (cambian con menor frecuencia)  
- **Precios**: Cada 30 minutos (pueden cambiar por promociones)  
- **Stock**: Cada 10 minutos (alta volatilidad)  
- **Tiendas**: Cada 24 horas (muy estables)

**Implementación del Polling**

El polling se implementa mediante DAGs de Apache Airflow que:

1. **Mantienen Estado**: Guardan el timestamp de la última ejecución exitosa en una tabla de control  
2. **Consultan Incrementalmente**: Usan filtros de fecha (dateModified \> lastRun) para obtener solo datos nuevos o modificados  
3. **Paginan Resultados**: Manejan respuestas grandes mediante paginación (limit/offset)  
4. **Manejan Errores**: Implementan reintentos con backoff exponencial ante fallos

**Lógica de Consulta Incremental**

Para cada ejecución del DAG de polling:

1. Se consulta la tabla de control para obtener el último timestamp procesado  
2. Se construye la query a la API: `/order?dateModified>${lastTimestamp}&limit=100`  
3. Se procesan los resultados en lotes de 100 registros  
4. Para cada orden, se consultan sus ítems: `/order/{orderId}/items`  
5. Se envían todos los datos a Kinesis Firehose  
6. Se actualiza el timestamp en la tabla de control solo si todo fue exitoso

**Manejo de Ventanas de Tiempo**

Para evitar perder datos durante la ejecución del polling, se implementa un overlap de 1 minuto:

- Si la última ejecución fue a las 14:00:00  
- La siguiente consulta usa dateModified \>= 13:59:00  
- Esto garantiza capturar datos que pudieron llegar justo en el límite  
- La deduplicación posterior elimina registros duplicados

### 5.3.4 Deduplicación de Datos {#5.3.4-deduplicación-de-datos}

Dado que el mismo dato puede llegar tanto por webhook como por polling, es crítico implementar deduplicación efectiva.

**Estrategia de Deduplicación**

La deduplicación ocurre en la capa de transformación (Bronze → Silver) usando:

1. **Clave de Negocio**: Identificador único de la entidad (order\_id, item\_id, etc.)  
2. **Timestamp de Modificación**: Campo dateModified de Janis  
3. **Regla de Resolución**: Se mantiene el registro con el timestamp más reciente

**Implementación en AWS Glue**

Los jobs de Glue implementan deduplicación mediante:

- Lectura de todos los registros nuevos desde Bronze  
- Agrupación por clave de negocio  
- Selección del registro con max(dateModified) por grupo  
- Merge con datos existentes en Silver usando operaciones UPSERT de Iceberg

---

## 5.4 Capa de Buffer: Kinesis Firehose y S3 Bronze {#5.4-capa-de-buffer:-kinesis-firehose-y-s3-bronze}

### 5.4.1 Rol de Kinesis Firehose {#5.4.1-rol-de-kinesis-firehose}

Amazon Kinesis Firehose actúa como buffer inteligente entre la ingesta y el almacenamiento persistente. Sus responsabilidades incluyen:

**Buffering y Batching**

Firehose no escribe cada evento individual a S3 inmediatamente. En su lugar, agrupa múltiples eventos en lotes según dos criterios configurables:

- **Tamaño de buffer**: Escribe cuando se acumulan 5 MB de datos  
- **Intervalo de buffer**: Escribe cada 60 segundos, incluso si no se alcanzó el tamaño

Esta estrategia optimiza costos de S3 (menos PUT requests) y mejora eficiencia de procesamiento posterior.

**Compresión Automática**

Firehose comprime los datos usando GZIP antes de escribir a S3, reduciendo:

- Costos de almacenamiento (típicamente 70-80% de reducción)  
- Tiempo de transferencia en lecturas posteriores  
- Costos de transferencia de datos

**Particionamiento Dinámico**

Firehose puede particionar automáticamente los datos según campos del payload JSON:

- Por tipo de evento: orders/, order-items/, products/  
- Por fecha: year=2024/month=12/day=09/hour=14/  
- Por tienda: store\_id=STORE001/

Esto optimiza las consultas posteriores al permitir "partition pruning" (leer solo particiones relevantes).

**Transformación en Tránsito**

Opcionalmente, Firehose puede invocar una función Lambda para transformar datos antes de escribir:

- Enmascarar datos sensibles (PII)  
- Agregar metadatos (timestamp de ingesta, versión de esquema)  
- Validar formato y rechazar datos inválidos

### 5.4.2 Estructura de S3 Bronze {#5.4.2-estructura-de-s3-bronze}

**Organización de Buckets**

Se utiliza un único bucket con prefijos para organizar datos:

```
s3://cencosud-datalake-bronze/
├── orders/
│   ├── year=2024/
│   │   ├── month=12/
│   │   │   ├── day=09/
│   │   │   │   ├── hour=14/
│   │   │   │   │   ├── data-1-2024-12-09-14-00-00.json.gz
│   │   │   │   │   ├── data-2-2024-12-09-14-05-00.json.gz
│   │   │   │   │   └── ...
├── order-items/
├── products/
├── stock/
└── ...
```

**Formato de Datos en Bronze**

Los datos se almacenan en formato JSON comprimido, manteniendo la estructura exacta recibida desde Janis:

- **Sin transformaciones**: Datos tal como llegan desde la API  
- **Con metadatos adicionales**: Timestamp de ingesta, fuente (webhook/polling), versión de esquema  
- **Compresión GZIP**: Para optimizar almacenamiento

**Gestión con Apache Iceberg**

Aunque los datos están en JSON, se registran como tablas Iceberg en el Glue Data Catalog:

- Permite consultas SQL sobre datos JSON  
- Mantiene historial de snapshots  
- Facilita time travel para auditoría  
- Soporta schema evolution cuando Janis cambia su API

**Políticas de Retención**

Los datos en Bronze se retienen según políticas definidas:

- **Datos transaccionales** (orders, items): 90 días  
- **Datos maestros** (products, stores): 365 días  
- **Logs y metadatos**: 30 días

Después del período de retención, los datos se mueven a S3 Glacier para archivo de largo plazo.

---

## 5.5 Capa de Procesamiento: AWS Glue y Apache Iceberg Silver {#5.5-capa-de-procesamiento:-aws-glue-y-apache-iceberg-silver}

### 5.5.1 Transformaciones de Datos {#5.5.1-transformaciones-de-datos}

Los jobs de AWS Glue leen datos desde S3 Bronze y aplican múltiples transformaciones para producir datos limpios y normalizados en la capa Silver.

**Conversión de Tipos de Datos**

Las APIs de Janis usan tipos de datos que no siempre coinciden con los esperados en Redshift:

- **Timestamps Unix → ISO 8601**: Los campos de fecha vienen como enteros Unix timestamp (1698172800) y se convierten a formato ISO 8601 ('2023-10-24 16:00:00')  
    
- **Booleans**: Janis usa true/false en JSON, que se mapean directamente a BOOLEAN en Redshift  
    
- **Decimales**: Los montos vienen como números con precisión variable y se normalizan a NUMERIC(10,2)  
    
- **Enums → Strings**: Valores enumerados se convierten a strings descriptivos

**Normalización de Estructuras**

Los datos JSON de Janis contienen estructuras anidadas que deben aplanarse:

- **Arrays de direcciones**: Se extrae la dirección principal y se crean campos individuales (street, city, state, postalCode)  
    
- **Objetos de totales**: Se descomponen en campos individuales (totalAmount, totalDiscount, totalShipping)  
    
- **Metadatos anidados**: Se extraen campos relevantes y se descartan datos innecesarios

**Enriquecimiento de Datos**

Los datos se enriquecen con información de otras fuentes:

- **Datos maestros**: Se agregan nombres de tienda, categoría de producto, marca  
- **Datos calculados**: Se derivan campos como total\_changes (amount \- originalAmount)  
- **Flags de calidad**: Se marcan registros con datos incompletos o sospechosos

**Manejo de Data Gaps**

Según el análisis de mapeo, existen campos utilizados por BI que no están disponibles en las APIs de Janis. Se implementan estrategias de mitigación:

- **items\_substituted\_qty**: Se calcula contando items con substitute\_type \= 'substitute'  
- **items\_qty\_missing**: Se calcula como SUM(quantity \- quantity\_picked)  
- **Campos no calculables**: Se marcan como NULL con flag indicando que el dato no está disponible

**Validación de Calidad**

Cada registro transformado pasa por validaciones:

- Campos obligatorios no pueden ser NULL  
- Rangos de valores deben ser válidos (fechas futuras, montos negativos)  
- Relaciones entre campos deben ser consistentes (quantity\_picked \<= quantity)  
- Checksums para detectar corrupción de datos

### 5.5.2 Apache Iceberg en Capa Silver {#5.5.2-apache-iceberg-en-capa-silver}

**Decisión de Usar Apache Iceberg**

Se selecciona Apache Iceberg como formato de tabla para la capa Silver por sus capacidades avanzadas:

**Transacciones ACID**

Iceberg garantiza atomicidad, consistencia, aislamiento y durabilidad:

- Las escrituras son atómicas: o se completan totalmente o no se aplican  
- Múltiples jobs pueden leer y escribir concurrentemente sin conflictos  
- Los lectores siempre ven snapshots consistentes de los datos

**Time Travel**

Iceberg mantiene historial completo de snapshots:

- Se puede consultar el estado de una tabla en cualquier punto del pasado  
- Útil para auditoría y análisis de cambios históricos  
- Permite rollback a versiones anteriores si se detectan problemas

**Schema Evolution**

Cuando Janis modifica su API agregando o cambiando campos:

- Iceberg permite agregar columnas sin reescribir datos existentes  
- Soporta renombrar columnas manteniendo compatibilidad  
- Permite cambiar tipos de datos de forma segura

**Partition Evolution**

La estrategia de particionamiento puede cambiar sin migrar datos:

- Inicialmente particionado por día  
- Puede cambiar a particionamiento por hora sin reescribir  
- Iceberg maneja transparentemente la transición

**Operaciones UPSERT Eficientes**

Iceberg soporta operaciones MERGE que permiten:

- Actualizar registros existentes  
- Insertar registros nuevos  
- Eliminar registros obsoletos  
- Todo en una sola operación atómica

**Integración con AWS Glue Catalog**

Las tablas Iceberg se registran en Glue Data Catalog:

- Visibles desde Athena, Redshift Spectrum, EMR  
- Metadatos centralizados y versionados  
- Estadísticas de columnas para optimización de queries

### 5.5.3 Estructura de Tablas Silver {#5.5.3-estructura-de-tablas-silver}

Las tablas en Silver siguen el esquema definido en el Capítulo 3, con optimizaciones específicas:

**Particionamiento**

Cada tabla se particiona según su patrón de acceso:

- **wms\_orders**: Particionado por year, month, day de date\_created  
- **wms\_order\_items**: Particionado igual que orders para co-location  
- **products**: Particionado por category  
- **stock**: Particionado por store\_id y date

**Formato de Almacenamiento**

- **Formato**: Parquet con compresión Snappy  
- **Tamaño de archivo**: Optimizado a \~128 MB por archivo  
- **Encoding**: Automático según tipo de columna (dictionary, RLE, etc.)

---

# **5.6 Capa de Orquestación y Procesamiento: Arquitectura Event-Driven & MWAA**

### **5.6.1 Rol de la Arquitectura de Datos**

El sistema Janis-Cencosud implementa un pipeline de datos **event-driven** que actúa como el motor de sincronización entre el ecosistema Janis y el Data Lake de Cencosud. A diferencia de los sistemas tradicionales basados únicamente en lotes (batch), esta arquitectura elimina colas y tiempos de espera, garantizando un flujo continuo con una latencia de **2 a 4 minutos**.

**Ventajas del enfoque híbrido (Event-Driven \+ MWAA):**

* **Inmediatez**: Procesamiento en tiempo real vía webhooks a través de API Gateway.  
* **Resiliencia**: Amazon MWAA actúa como una "red de seguridad" mediante polling constante para evitar pérdida de datos.  
* **Escalabilidad**: Capacidad para manejar desde 150 hasta 2,000 registros por tipo de datos con escalamiento automático.  
* **Consistencia**: Uso de formato **Apache Iceberg** en la capa Silver para garantizar transacciones ACID.

### **5.6.2 Flujos Principales de Datos (Pipeline)**

#### **Flujo 1: Ingesta Híbrida (Webhooks & Polling)**

Este flujo asegura que cada evento en Janis sea capturado inmediatamente o recuperado por el sistema de seguridad.

* **Tareas de Ingesta**:  
  * **webhook\_receive**: API Gateway recibe notificaciones y valida firmas HMAC-SHA256.  
  * **polling\_safety\_net (MWAA)**: Ejecuta consultas cada 5 minutos a las APIs de Janis para capturar datos omitidos.  
  * **data\_validation**: AWS Lambda valida y transforma el esquema inicial del JSON.  
  * **kinesis\_buffering**: Firehose acumula datos hasta alcanzar 1 MB o 60 segundos antes de escribir en S3.  
* **Configuración**:  
  * **Throttling API**: 10,000 requests por segundo.  
  * **Polling Interval**: Cada 5 minutos (vía MWAA mw1.small).  
  * **Retries**: Backoff exponencial para el polling de APIs.

#### **Flujo 2: Transformación Bronze a Silver/Silver a Gold (AWS Glue)**

Se activa automáticamente mediante eventos de S3 para transformar datos crudos en datos analíticos.

* **Tareas de Transformación**:  
  * **s3\_event\_trigger**: Notificación de "Object Created" en la capa Bronze/Silver/Gold.  
  * **sqs\_orchestration**: Encolamiento en SQS FIFO para garantizar el orden y evitar duplicidad.  
  * **glue\_job\_execution**: Jobs especializados para órdenes, ítems, productos y stock.  
  * **iceberg\_commit**: Escritura de datos normalizados en formato Apache Iceberg en la capa Silver/Gold.  
* **Configuración**:  
  * **SQS Visibility Timeout**: 15 minutos para permitir la finalización de Glue.  
  * **Workers**: Variables según el volumen (especialmente alto para ítems de órdenes).

#### **Flujo 3: Carga Incremental a Redshift**

El paso final que disponibiliza la información para BI y analítica.

* **Tareas de Carga**:  
  * **detect\_iceberg\_commit**: Lambda detecta cambios en los metadatos de Iceberg.  
  * **staging\_upsert**: Creación de tablas temporales para manejo de datos nuevos.  
  * **redshift\_copy**: Ejecución de comando COPY para actualizar registros existentes e insertar nuevos desde la capa gold.  
* **Configuración**:  
  * **Capacidad**: Redshift Serverless desde 8 hasta 64 RPUs.  
  * **Método**: UPSERT eficiente para evitar duplicados.

### **5.6.3 Resiliencia, Monitoreo y Manejo de Errores**

#### **Estrategia de Recuperación**

El sistema está diseñado para fallar de forma segura y permitir la recuperación total.

* **Dead Letter Queues (DLQ)**: Cada cola SQS tiene una DLQ asociada para capturar mensajes que fallan tras múltiples intentos.  
* **Replay Capability**: Capacidad de re-procesar datos desde la capa Bronze si es necesario.  
* **Deduplicación**: Firehose y SQS FIFO implementan lógica para evitar procesar el mismo registro dos veces.

#### **Tipos de Errores Manejados**

1. **Errores Transitorios (Auto-recuperables)**:  
   * Timeouts de API Janis (manejados por el backoff de MWAA).  
   * Picos de tráfico (manejados por el escalamiento de Lambda y Kinesis).  
2. **Errores Críticos (Alertables)**:  
   * Fallos en la validación HMAC (seguridad).  
   * Anomalías en la tasa de errores detectadas por CloudWatch.

#### **Monitoreo y Auditoría**

* **CloudWatch Dashboards**: Métricas de latencia y throughput en tiempo real.  
* **Alertas**: Notificaciones automáticas en menos de 5 minutos ante anomalías.  
* **CloudTrail**: Log completo de todas las operaciones para trazabilidad y cumplimiento.

---

## 5.7 Capa de Disponibilización: Redshift y Power BI {#5.7-capa-de-disponibilización:-redshift-y-power-bi}

### 5.7.1 Carga Incremental a Redshift {#5.7.1-carga-incremental-a-redshift}

**Estrategia de Carga**

Se implementa carga incremental en lugar de full refresh para optimizar tiempos y recursos:

**Identificación de Datos Nuevos**

Iceberg mantiene snapshots de cada tabla. El proceso de carga:

1. Consulta el último snapshot procesado (guardado en tabla de control)  
2. Identifica el snapshot actual de la tabla Iceberg  
3. Calcula el delta: registros nuevos o modificados entre snapshots  
4. Genera manifest file con ubicaciones S3 de archivos Parquet del delta

**Proceso de COPY**

Los datos se cargan en dos fases:

**Fase 1: Carga a Staging**

Se crean tablas staging temporales con estructura idéntica a las principales:

- Se ejecuta comando COPY desde S3 usando manifest file  
- Los datos se cargan en staging sin afectar tablas principales  
- Se validan conteos y calidad de datos

**Fase 2: Merge a Tablas Principales**

Se ejecuta operación MERGE que:

- Actualiza registros existentes (basándose en primary key)  
- Inserta registros nuevos  
- Opcionalmente elimina registros marcados como deleted  
- Todo en una transacción atómica

**Optimización Post-Carga**

Después de cada carga se ejecutan comandos de mantenimiento:

**VACUUM**

Reorganiza datos físicamente y recupera espacio:

- Elimina filas marcadas como deleted  
- Reordena datos según sort key  
- Compacta bloques fragmentados  
- Típicamente se ejecuta en ventanas de bajo uso

**ANALYZE**

Actualiza estadísticas de tabla para el optimizador de queries:

- Calcula distribución de valores por columna  
- Identifica columnas con alta cardinalidad  
- Actualiza histogramas para estimación de costos  
- Mejora planes de ejecución de queries

### 5.7.2 Integración con Power BI {#5.7.2-integración-con-power-bi}

**Modo de Conexión**

Power BI se conecta a Redshift usando DirectQuery:

- Las queries se ejecutan directamente en Redshift  
- No se importan datos a Power BI Desktop  
- Siempre se consultan datos actualizados  
- Requiere optimización de queries para performance

**Optimizaciones para BI**

**Vistas Materializadas**

Se crean vistas materializadas para agregaciones frecuentes:

- Ventas diarias por tienda  
- Top productos por categoría  
- Métricas de fulfillment por hora  
- KPIs de operación

Estas vistas se refrescan automáticamente según schedule definido.

**Tablas de Dimensiones**

Las tablas maestras (stores, products, categories) se configuran con:

- Distribution style ALL (replicadas en todos los nodos)  
- Sort keys por campos de join frecuentes  
- Encoding optimizado para compresión

**Tablas de Hechos**

Las tablas transaccionales (orders, order\_items) se optimizan con:

- Distribution keys para co-location de joins  
- Sort keys por campos de filtro frecuentes (date\_created, status)  
- Particionamiento por fecha para partition pruning

---

## 5.8 Monitoreo y Observabilidad {#5.8-monitoreo-y-observabilidad}

### 5.8.1 Métricas Clave {#5.8.1-métricas-clave}

Se monitorean métricas en cada capa del pipeline:

**Capa de Ingesta**

- Webhooks recibidos por segundo  
- Latencia de procesamiento de webhooks  
- Tasa de error en validación de firma  
- Registros obtenidos por polling  
- Tiempo de respuesta de APIs de Janis

**Capa de Buffer**

- Throughput de Kinesis Firehose (MB/s)  
- Tamaño de buffer actual  
- Frecuencia de flush a S3  
- Tasa de compresión lograda  
- Errores de escritura a S3

**Capa de Procesamiento**

- Duración de jobs de Glue  
- Registros procesados por job  
- Tasa de error en transformaciones  
- Uso de DPUs (Data Processing Units)  
- Tamaño de datos en Silver

**Capa de Orquestación**

- Duración de DAGs  
- Tasa de éxito/fallo de tareas  
- Tiempo de espera en colas  
- Uso de workers de Airflow  
- Backlog de tareas pendientes

**Capa de Disponibilización**

- Duración de cargas a Redshift  
- Registros cargados por ejecución  
- Uso de CPU/memoria de cluster  
- Queries ejecutadas por Power BI  
- Latencia de queries

### 5.8.2 Dashboards de Monitoreo {#5.8.2-dashboards-de-monitoreo}

Se implementan dashboards en CloudWatch y Airflow UI:

**Dashboard Operacional**

Vista en tiempo real del estado del pipeline:

- Estado de cada DAG (running, success, failed)  
- Métricas de throughput por capa  
- Alertas activas  
- Últimas ejecuciones y su duración

**Dashboard de Calidad de Datos**

Métricas de calidad y completitud:

- Porcentaje de registros con datos completos  
- Conteos por tabla y capa  
- Freshness de datos (tiempo desde última actualización)  
- Tendencias de volumen de datos  
- Anomalías detectadas

**Dashboard de Costos**

Seguimiento de costos por servicio:

- Costos de Kinesis Firehose  
- Costos de almacenamiento S3  
- Costos de procesamiento Glue  
- Costos de Redshift  
- Proyección de costos mensuales

### 5.8.3 Alertas y Notificaciones {#5.8.3-alertas-y-notificaciones}

Se configuran alertas para condiciones críticas:

**Alertas Críticas** (notificación inmediata):

- DAG falla después de todos los reintentos  
- Datos no actualizados en más de 2 horas  
- Tasa de error \> 10% en cualquier componente  
- Cluster de Redshift con uso \> 90%  
- Costos exceden presupuesto en \> 20%

**Alertas de Advertencia** (notificación agregada):

- Duración de DAG excede promedio en \> 50%  
- Volumen de datos anormal (muy alto o muy bajo)  
- Queries lentas en Redshift (\> 30 segundos)  
- Uso de recursos cerca de límites

**Canales de Notificación**

- Email para alertas críticas  
- Slack para alertas de advertencia  
- PagerDuty para incidentes fuera de horario  
- Dashboard centralizado para todas las alertas

---

## 5.9 Seguridad y Cumplimiento {#5.9-seguridad-y-cumplimiento}

### 5.9.1 Seguridad en Tránsito {#5.9.1-seguridad-en-tránsito}

**Cifrado de Comunicaciones**

- Webhooks: HTTPS con TLS 1.2+  
- APIs de Janis: HTTPS con TLS 1.2+  
- Comunicación entre servicios AWS: TLS 1.2+  
- Conexión Power BI \- Redshift: SSL/TLS

**Autenticación y Autorización**

- Webhooks: Validación de firma HMAC-SHA256  
- APIs de Janis: API keys rotadas mensualmente  
- Servicios AWS: IAM roles con principio de mínimo privilegio  
- Redshift: Usuarios con permisos granulares

### 5.9.2 Seguridad en Reposo {#5.9.2-seguridad-en-reposo}

**Cifrado de Datos**

- S3: Cifrado SSE-S3 o SSE-KMS  
- Redshift: Cifrado con KMS  
- Secrets Manager: Cifrado de credenciales  
- Backups: Cifrados automáticamente

**Control de Acceso**

- S3 buckets: Políticas de bucket restrictivas, no acceso público  
- Redshift: VPC privada, sin acceso desde internet  
- Glue: Roles de ejecución con permisos específicos  
- Airflow: Autenticación con SSO corporativo

### 5.9.3 Auditoría y Trazabilidad {#5.9.3-auditoría-y-trazabilidad}

**Logging Completo**

- CloudTrail: Todas las acciones en servicios AWS  
- CloudWatch Logs: Logs de aplicación de todos los componentes  
- Redshift: Query logging habilitado  
- Airflow: Logs de ejecución de DAGs y tareas

**Retención de Logs**

- Logs operacionales: 90 días en CloudWatch  
- Logs de auditoría: 7 años en S3 Glacier  
- Logs de acceso: 1 año en S3 Standard

**Trazabilidad de Datos**

Cada registro mantiene metadatos de linaje:

- Timestamp de ingesta  
- Fuente de datos (webhook/polling)  
- Versión de esquema  
- ID de job de transformación  
- Snapshot de Iceberg

