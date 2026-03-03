# Pipeline Completo Janis API a Redshift

**Fecha:** 19 de Febrero, 2026  
**Estado:** 🚧 En Desarrollo  
**Objetivo:** Implementar pipeline completo end-to-end que procese TODOS los endpoints de la API de Janis y los transforme a esquemas de Redshift

---

## 📋 Documentos de la Especificación

### 1. [Requirements](requirements.md) ⭐
Requisitos funcionales y no funcionales del sistema completo.

**Contenido:**
- Contexto y motivación del proyecto
- Endpoints de Janis API a procesar (6 endpoints)
- User stories detalladas
- Requerimientos funcionales (RF-1 a RF-6)
- Requerimientos no funcionales (Performance, Escalabilidad, Confiabilidad)
- Dependencias técnicas y de infraestructura
- Criterios de éxito por fase
- Riesgos y restricciones

### 2. [Design Document](design.md) 📋
Diseño técnico detallado de la arquitectura del pipeline.

**Estado:** Pendiente de creación

**Contenido Planeado:**
- Arquitectura del sistema completo
- Diseño de módulos (Fetchers, Mappers, Transformers)
- Flujo de datos Bronze → Silver → Gold → Redshift
- Decisiones de diseño fundamentales
- Interfaces y contratos
- Patrones de diseño aplicados

### 3. [Tasks](tasks.md) 📋
Plan de implementación detallado con tareas discretas.

**Estado:** Pendiente de creación

**Contenido Planeado:**
- Fase 1: Fetchers y Mappers (1 semana)
- Fase 2: Pipeline Bronze → Silver (1 semana)
- Fase 3: Pipeline Silver → Gold (1 semana)
- Fase 4: RedshiftLoader (1 semana)
- Fase 5: Orquestación (1 semana)
- Fase 6: Testing y Validación (1 semana)

---

## 🎯 Visión General

### Problema a Resolver

Actualmente solo procesamos el endpoint `/api/order/{id}` de Janis API. Necesitamos:
- Procesar TODOS los endpoints (orders, products, stock, prices, stores, customers)
- Generar TODAS las tablas de Redshift requeridas (9 tablas)
- Integrar TODOS los módulos existentes en un flujo completo
- Implementar componentes faltantes (RedshiftLoader, orquestación)

### Solución Propuesta

Pipeline completo end-to-end que:
1. **Obtiene datos** de 6 endpoints de Janis API
2. **Transforma datos** a través de Bronze → Silver → Gold
3. **Carga datos** a 9 tablas de Redshift
4. **Orquesta ejecución** con EventBridge + MWAA
5. **Monitorea y alerta** sobre el estado del pipeline

---

## 📊 Endpoints y Tablas

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

### Flujo de Datos

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

## 🚀 Estado Actual

### Completado ✅
- ✅ 16 módulos de transformación implementados (94%)
- ✅ Pipeline con mapeo de esquema funcional para órdenes
- ✅ Infraestructura AWS desplegada (141 recursos)
- ✅ Specs completos documentados (webhooks, polling, transformación, redshift)

### Gap Crítico ❌
- ❌ Solo se procesa el endpoint `/api/order/{id}` 
- ❌ Faltan endpoints: products, stock, prices, stores, customers
- ❌ No hay integración completa Bronze → Silver → Gold → Redshift
- ❌ DuplicateDetector y ConflictResolver no integrados en pipeline
- ❌ RedshiftLoader no implementado

### Próximos Pasos 📋
1. **Crear design document** con arquitectura detallada
2. **Crear tasks** para cada fase de implementación
3. **Implementar Fase 1:** Fetchers y Mappers (1 semana)
4. **Implementar Fase 2:** Pipeline Bronze → Silver (1 semana)
5. **Implementar Fase 3:** Pipeline Silver → Gold (1 semana)
6. **Implementar Fase 4:** RedshiftLoader (1 semana)
7. **Implementar Fase 5:** Orquestación (1 semana)
8. **Implementar Fase 6:** Testing y Validación (1 semana)

---

## 📦 Componentes a Implementar

### Fase 1: Fetchers y Mappers
- `OrderFetcher`, `ProductFetcher`, `StockFetcher`, `PriceFetcher`, `StoreFetcher`, `CustomerFetcher`
- `OrdersMapper`, `OrderItemsMapper`, `OrderShippingMapper`, `ProductsMapper`, `ProductSkusMapper`, `StockMapper`, `PricesMapper`, `StoresMapper`, `CustomersMapper`

### Fase 2: Pipeline Bronze → Silver
- Integración de todos los módulos existentes
- DuplicateDetector y ConflictResolver integrados
- Pipeline funcional para todos los endpoints

### Fase 3: Pipeline Silver → Gold
- Agregaciones implementadas
- Validación de calidad
- Optimización para BI

### Fase 4: RedshiftLoader
- Carga incremental implementada
- UPSERT funcionando
- Validación de datos

### Fase 5: Orquestación
- EventBridge rules configuradas
- MWAA DAGs implementados
- Glue Jobs configurados

### Fase 6: Testing y Validación
- Tests end-to-end completos
- Validación con datos reales
- Performance testing

---

## 🔗 Documentación Relacionada

### Specs Relacionados
- [Spec 1: AWS Infrastructure](../01-aws-infrastructure/) - Infraestructura base
- [Spec 3: Webhook Ingestion](../webhook-ingestion/) - Ingesta en tiempo real
- [Spec 4: API Polling](../api-polling/) - Polling periódico
- [Spec 5: Data Transformation](../data-transformation/) - Transformaciones ETL
- [Spec 6: Redshift Loading](../redshift-loading/) - Carga a Redshift

### Documentación General
- [Estado del Proyecto](../../Documentacion/ESTADO_PROYECTO_FEBRERO_2026.md) - Estado general
- [Pipeline con Mapeo de Esquema](../../Documentacion/PIPELINE_CON_MAPEO_ESQUEMA.md) - Pipeline actual
- [Integración Max-Vicente](../integration-max-vicente/) - Integración de módulos

### Código
- Módulos existentes: `glue/modules/`
- Pipeline actual: `glue/scripts/pipeline_with_schema_mapping.py`
- Tests: `glue/tests/`

---

## 📝 Criterios de Éxito

### Funcionales
- ✅ Sistema procesa 6 endpoints de Janis API
- ✅ Sistema genera 9 tablas de Redshift
- ✅ Pipeline completo Bronze → Silver → Gold → Redshift funciona
- ✅ Deduplicación y resolución de conflictos integrados
- ✅ Orquestación automática con EventBridge + MWAA

### No Funcionales
- ✅ Pipeline completo en < 15 minutos
- ✅ Procesar 100K registros/minuto
- ✅ 99.9% uptime
- ✅ Retry automático en fallos
- ✅ Alertas proactivas

---

## ⚠️ Riesgos

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

## 📞 Contacto y Soporte

Para preguntas sobre este spec:
- Ver documentación en `.kiro/specs/janis-api-complete-pipeline/`
- Revisar código en `glue/modules/` y `glue/scripts/`
- Consultar specs relacionados en `.kiro/specs/`

---

**Documento creado:** 19 de Febrero, 2026  
**Última actualización:** 19 de Febrero, 2026  
**Estado:** Requirements definidos - Listo para diseño
