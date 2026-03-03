# Spec: Pipeline Completo Janis API a Redshift

**Fecha:** 19 de Febrero, 2026  
**Estado:** 🚧 En Desarrollo  
**Ubicación:** `.kiro/specs/janis-api-complete-pipeline/`

---

## 📋 Resumen Ejecutivo

Se ha creado un nuevo spec que define la implementación completa del pipeline end-to-end para procesar TODOS los endpoints de la API de Janis y cargar los datos a Redshift.

**Spec:** [.kiro/specs/janis-api-complete-pipeline/](../.kiro/specs/janis-api-complete-pipeline/)

---

## 🎯 Objetivo

Implementar un pipeline completo que:
- Procesa 6 endpoints de Janis API (orders, products, stock, prices, stores, customers)
- Genera 9 tablas de Redshift
- Integra todos los módulos existentes en un flujo completo
- Implementa componentes faltantes (RedshiftLoader, orquestación)
- Proporciona un sistema funcional end-to-end listo para producción

---

## 📊 Alcance del Proyecto

### Endpoints de Janis API

| Endpoint | Entidad | Frecuencia | Prioridad | Tablas Redshift |
|----------|---------|------------|-----------|-----------------|
| `/api/order/{id}` | Orders | 5 min | 🔴 Alta | wms_orders, wms_order_items, wms_order_shipping |
| `/api/product/{id}` | Products | 1 hora | 🟡 Media | wms_products, wms_product_skus |
| `/api/stock` | Stock | 10 min | 🔴 Alta | wms_stock |
| `/api/price` | Prices | 30 min | 🟡 Media | wms_prices |
| `/api/store/{id}` | Stores | 24 horas | 🟢 Baja | wms_stores |
| `/api/customer/{id}` | Customers | 1 hora | 🟡 Media | wms_customers |

### Tablas de Redshift

**9 tablas destino:**
1. `wms_orders` (26 campos) - Información principal de órdenes
2. `wms_order_items` (11 campos) - Items de órdenes
3. `wms_order_shipping` (12 campos) - Información de envío
4. `wms_products` - Información de productos
5. `wms_product_skus` - SKUs de productos
6. `wms_stock` - Inventario por SKU y ubicación
7. `wms_prices` - Precios por SKU
8. `wms_stores` - Información de tiendas
9. `wms_customers` - Información de clientes

---

## 🏗️ Arquitectura del Pipeline

### Flujo de Datos Completo

```
Janis API (6 endpoints)
    ↓
[Fetchers] - Obtención de datos con retry y rate limiting
    ↓
S3 Bronze (JSON raw)
    ↓
[Pipeline Bronze → Silver]
    - JSONFlattener
    - DataCleaner
    - DataNormalizer
    - DataTypeConverter
    - DataGapHandler
    - DuplicateDetector
    - ConflictResolver
    ↓
S3 Silver (Iceberg - datos limpios)
    ↓
[Pipeline Silver → Gold]
    - IncrementalProcessor
    - DataLineageTracker
    - DataQualityValidator
    - ErrorHandler
    - DenormalizationEngine
    - SilverToGoldAggregator
    ↓
S3 Gold (Iceberg - datos optimizados)
    ↓
[RedshiftLoader]
    - Manifest generation
    - Staging tables
    - COPY from S3
    - MERGE/UPSERT
    ↓
Amazon Redshift (9 tablas)
    ↓
Power BI / Herramientas BI
```

### Orquestación

```
EventBridge Rules (por endpoint)
    ↓
MWAA (Apache Airflow)
    ↓
Glue Jobs (transformaciones)
    ↓
Redshift (carga de datos)
```

---

## 📦 Componentes a Implementar

### Fase 1: Fetchers y Mappers (1 semana)

**Endpoint Fetchers:**
- `OrderFetcher` - Obtiene órdenes con items y shipping
- `ProductFetcher` - Obtiene productos con SKUs
- `StockFetcher` - Obtiene inventario
- `PriceFetcher` - Obtiene precios
- `StoreFetcher` - Obtiene tiendas
- `CustomerFetcher` - Obtiene clientes

**Schema Mappers:**
- `OrdersMapper` - Mapea a wms_orders (26 campos)
- `OrderItemsMapper` - Mapea a wms_order_items (11 campos)
- `OrderShippingMapper` - Mapea a wms_order_shipping (12 campos)
- `ProductsMapper` - Mapea a wms_products
- `ProductSkusMapper` - Mapea a wms_product_skus
- `StockMapper` - Mapea a wms_stock
- `PricesMapper` - Mapea a wms_prices
- `StoresMapper` - Mapea a wms_stores
- `CustomersMapper` - Mapea a wms_customers

**Funcionalidad común:**
- Autenticación con headers Janis
- Manejo de paginación
- Retry con exponential backoff
- Rate limiting (100 req/min)
- Logging completo

### Fase 2: Pipeline Bronze → Silver (1 semana)

**Flujo:**
1. Leer JSON desde Bronze (S3)
2. Aplicar JSONFlattener (si necesario)
3. Aplicar DataCleaner (trim, nulls)
4. Aplicar DataNormalizer (emails, fechas)
5. Aplicar DataTypeConverter (tipos correctos)
6. Aplicar DataGapHandler (campos derivados)
7. Aplicar DuplicateDetector (marcar duplicados)
8. Aplicar ConflictResolver (resolver conflictos)
9. Escribir a Silver (Iceberg) con IcebergWriter

**Validación:**
- Todos los módulos se ejecutan en orden
- Datos limpios en Silver
- Sin duplicados
- Trazabilidad completa

### Fase 3: Pipeline Silver → Gold (1 semana)

**Flujo:**
1. Leer desde Silver (Iceberg)
2. Aplicar IncrementalProcessor (solo nuevos)
3. Aplicar DataLineageTracker (trazabilidad)
4. Aplicar DataQualityValidator (validación)
5. Aplicar ErrorHandler (manejo errores)
6. Aplicar DenormalizationEngine (joins)
7. Aplicar SilverToGoldAggregator (métricas)
8. Escribir a Gold (Iceberg)

**Validación:**
- Agregaciones correctas
- Calidad de datos validada
- Datos optimizados para BI

### Fase 4: RedshiftLoader (1 semana)

**Funcionalidad:**
- Leer desde Gold (Iceberg)
- Generar manifest files
- Crear staging tables
- Ejecutar COPY desde S3
- Validar datos en staging
- Ejecutar MERGE/UPSERT a tablas finales
- Limpiar staging

**Validación:**
- Carga incremental funciona
- UPSERT correcto
- Sin pérdida de datos
- Performance óptimo

### Fase 5: Orquestación (1 semana)

**Componentes:**
- EventBridge rules por endpoint (frecuencias diferentes)
- MWAA DAGs por entidad
- Glue Jobs por transformación
- Dependencias entre jobs

**Validación:**
- Scheduling correcto
- Ejecución automática
- Manejo de dependencias
- Retry en fallos

### Fase 6: Testing y Validación (1 semana)

**Actividades:**
- Tests end-to-end completos
- Validación con datos reales
- Performance testing
- Documentación operacional

---

## 📝 Requerimientos Funcionales

### RF-1: Endpoint Fetchers
Módulos para obtener datos de cada endpoint de Janis API con autenticación, paginación, retry y rate limiting.

### RF-2: Schema Mappers
Módulos para mapear JSON de API a esquemas de tablas con extracción de campos anidados y validación de tipos.

### RF-3: Pipeline Bronze → Silver
Transformación de datos raw a datos limpios con todos los módulos integrados.

### RF-4: Pipeline Silver → Gold
Agregación y optimización para BI con validación de calidad.

### RF-5: RedshiftLoader
Carga incremental de Gold a Redshift con MERGE/UPSERT.

### RF-6: Orquestación con EventBridge + MWAA
Scheduling y ejecución automática con manejo de dependencias.

---

## 📊 Requerimientos No Funcionales

### RNF-1: Performance
- Pipeline completo Bronze → Redshift en < 15 minutos
- Procesar 100K registros/minuto
- Carga incremental a Redshift en < 5 minutos

### RNF-2: Escalabilidad
- Soportar hasta 1M órdenes/día
- Auto-scaling de Glue workers (2-10)
- Manejo de picos de tráfico (10x normal)

### RNF-3: Confiabilidad
- 99.9% uptime
- Retry automático (3 intentos)
- Dead Letter Queue para fallos
- Recovery automático

### RNF-4: Observabilidad
- CloudWatch metrics completos
- Dashboards en tiempo real
- Alertas proactivas
- Logging detallado

### RNF-5: Seguridad
- Cifrado en tránsito y reposo
- IAM roles con least privilege
- Secrets Manager para credenciales
- Auditoría completa

---

## 🎯 Criterios de Éxito

### Fase 1: Implementación de Fetchers y Mappers (1 semana)
- ✅ 6 EndpointFetchers implementados
- ✅ 9 SchemaMappers implementados
- ✅ Tests unitarios pasando
- ✅ Documentación completa

### Fase 2: Pipeline Bronze → Silver (1 semana)
- ✅ Integración de todos los módulos
- ✅ DuplicateDetector y ConflictResolver integrados
- ✅ Pipeline funcional para todos los endpoints
- ✅ Tests de integración pasando

### Fase 3: Pipeline Silver → Gold (1 semana)
- ✅ Agregaciones implementadas
- ✅ Validación de calidad
- ✅ Optimización para BI
- ✅ Tests end-to-end pasando

### Fase 4: RedshiftLoader (1 semana)
- ✅ Carga incremental implementada
- ✅ UPSERT funcionando
- ✅ Validación de datos
- ✅ Performance optimizado

### Fase 5: Orquestación (1 semana)
- ✅ EventBridge rules configuradas
- ✅ MWAA DAGs implementados
- ✅ Glue Jobs configurados
- ✅ Sistema completo funcionando

### Fase 6: Testing y Validación (1 semana)
- ✅ Tests end-to-end completos
- ✅ Validación con datos reales
- ✅ Performance testing
- ✅ Documentación operacional

---

## ⚠️ Riesgos y Mitigaciones

### Riesgo 1: Endpoints de Janis no documentados
**Probabilidad:** Media  
**Impacto:** Alto  
**Mitigación:** Probar endpoints con script de testing, documentar respuestas

### Riesgo 2: Performance insuficiente
**Probabilidad:** Baja  
**Impacto:** Alto  
**Mitigación:** Benchmarking temprano, optimización incremental

### Riesgo 3: Incompatibilidad con Redshift existente
**Probabilidad:** Baja  
**Impacto:** Crítico  
**Mitigación:** Validación exhaustiva de esquemas, testing en paralelo

### Riesgo 4: Complejidad de orquestación
**Probabilidad:** Media  
**Impacto:** Medio  
**Mitigación:** Implementación incremental, testing por componente

---

## 🔗 Documentación Relacionada

### Especificación Completa
- **[README](../.kiro/specs/janis-api-complete-pipeline/README.md)** - Índice de documentación ⭐
- **[Requirements](../.kiro/specs/janis-api-complete-pipeline/requirements.md)** - Requisitos funcionales ⭐
- **[Design Document](../.kiro/specs/janis-api-complete-pipeline/design.md)** - Diseño técnico (pendiente)
- **[Tasks](../.kiro/specs/janis-api-complete-pipeline/tasks.md)** - Plan de implementación (pendiente)

### Specs Relacionados
- [Spec 1: AWS Infrastructure](../.kiro/specs/01-aws-infrastructure/) - Infraestructura base
- [Spec 3: Webhook Ingestion](../.kiro/specs/webhook-ingestion/) - Ingesta en tiempo real
- [Spec 4: API Polling](../.kiro/specs/api-polling/) - Polling periódico
- [Spec 5: Data Transformation](../.kiro/specs/data-transformation/) - Transformaciones ETL
- [Spec 6: Redshift Loading](../.kiro/specs/redshift-loading/) - Carga a Redshift

### Documentación General
- [Estado del Proyecto](ESTADO_PROYECTO_FEBRERO_2026.md) - Estado general
- [Pipeline con Mapeo de Esquema](PIPELINE_CON_MAPEO_ESQUEMA.md) - Pipeline actual
- [Integración Max-Vicente](../.kiro/specs/integration-max-vicente/) - Integración de módulos

---

## 📊 Progreso

**Estado Actual:** Requirements definidos - Listo para diseño

**Próximos Pasos:**
1. **Crear design document** con arquitectura detallada
2. **Crear tasks** para cada fase de implementación
3. **Implementar Fase 1:** Fetchers y Mappers
4. **Implementar Fase 2:** Pipeline Bronze → Silver
5. **Implementar Fase 3:** Pipeline Silver → Gold
6. **Implementar Fase 4:** RedshiftLoader
7. **Implementar Fase 5:** Orquestación
8. **Implementar Fase 6:** Testing y Validación

---

## 💡 Contexto del Proyecto

### Situación Actual

**Logros hasta ahora:**
- ✅ 16 módulos de transformación implementados (94%)
- ✅ Pipeline con mapeo de esquema funcional para órdenes
- ✅ Infraestructura AWS desplegada (141 recursos)
- ✅ Specs completos documentados (webhooks, polling, transformación, redshift)

**Gap Crítico:**
- ❌ Solo se procesa el endpoint `/api/order/{id}` 
- ❌ Faltan endpoints: products, stock, prices, stores, customers
- ❌ No hay integración completa Bronze → Silver → Gold → Redshift
- ❌ DuplicateDetector y ConflictResolver no integrados en pipeline
- ❌ RedshiftLoader no implementado

### Valor de la Implementación

Este spec define la implementación práctica que:
- Procesa TODOS los endpoints de Janis API
- Genera TODAS las tablas de Redshift requeridas
- Integra TODOS los módulos existentes en un flujo completo
- Implementa los componentes faltantes (RedshiftLoader, orquestación)
- Proporciona un sistema funcional end-to-end listo para producción

---

**Documento creado:** 19 de Febrero, 2026  
**Última actualización:** 19 de Febrero, 2026  
**Estado:** Requirements definidos - Listo para diseño
