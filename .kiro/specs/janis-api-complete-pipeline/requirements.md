# Requirements Document: Pipeline Completo Janis API a Redshift

**Fecha:** 19 de Febrero, 2026  
**Estado:** 🚧 En Desarrollo  
**Objetivo:** Implementar pipeline completo end-to-end que procese TODOS los endpoints de la API de Janis y los transforme a esquemas de Redshift

---

## 1. Contexto y Motivación

### 1.1 Situación Actual

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

### 1.2 Valor de la Implementación

Este spec define la implementación práctica que:
- Procesa TODOS los endpoints de Janis API
- Genera TODAS las tablas de Redshift requeridas
- Integra TODOS los módulos existentes en un flujo completo
- Implementa los componentes faltantes (RedshiftLoader, orquestación)
- Proporciona un sistema funcional end-to-end listo para producción

---

## 2. Endpoints de Janis API a Procesar

### 2.1 Endpoints Identificados

Basado en la documentación de Janis y los specs existentes:

| Endpoint | Entidad | Frecuencia | Prioridad | Tablas Redshift |
|----------|---------|------------|-----------|-----------------|
| `/api/order/{id}` | Orders | 5 min | 🔴 Alta | wms_orders, wms_order_items, wms_order_shipping |
| `/api/product/{id}` | Products | 1 hora | 🟡 Media | wms_products, wms_product_skus |
| `/api/stock` | Stock | 10 min | 🔴 Alta | wms_stock |
| `/api/price` | Prices | 30 min | 🟡 Media | wms_prices |
| `/api/store/{id}` | Stores | 24 horas | 🟢 Baja | wms_stores |
| `/api/customer/{id}` | Customers | 1 hora | 🟡 Media | wms_customers |

### 2.2 Estructura de Datos por Endpoint

#### 2.2.1 Orders (`/api/order/{id}`)
**Respuesta JSON:** Objeto anidado con order, items[], shippings[], addresses[]

**Tablas Destino:**
- `wms_orders` (26 campos) - Información principal de la orden
- `wms_order_items` (11 campos) - Items de la orden
- `wms_order_shipping` (12 campos) - Información de envío

**Completitud Actual:** 69-92% según tabla

#### 2.2.2 Products (`/api/product/{id}`)
**Respuesta JSON:** Objeto con product, skus[], categories[], attributes[]

**Tablas Destino:**
- `wms_products` - Información del producto
- `wms_product_skus` - SKUs del producto

#### 2.2.3 Stock (`/api/stock`)
**Respuesta JSON:** Array de objetos con stock por SKU y ubicación

**Tablas Destino:**
- `wms_stock` - Inventario por SKU y ubicación

#### 2.2.4 Prices (`/api/price`)
**Respuesta JSON:** Array de objetos con precios por SKU

**Tablas Destino:**
- `wms_prices` - Precios por SKU

#### 2.2.5 Stores (`/api/store/{id}`)
**Respuesta JSON:** Objeto con información de tienda

**Tablas Destino:**
- `wms_stores` - Información de tiendas

#### 2.2.6 Customers (`/api/customer/{id}`)
**Respuesta JSON:** Objeto con información de cliente

**Tablas Destino:**
- `wms_customers` - Información de clientes

---

## 3. User Stories

### US-1: Como ingeniero de datos, quiero procesar todos los endpoints de Janis
**Criterios de aceptación:**
- 1.1 Sistema procesa endpoint `/api/order/{id}` y genera 3 tablas
- 1.2 Sistema procesa endpoint `/api/product/{id}` y genera 2 tablas
- 1.3 Sistema procesa endpoint `/api/stock` y genera 1 tabla
- 1.4 Sistema procesa endpoint `/api/price` y genera 1 tabla
- 1.5 Sistema procesa endpoint `/api/store/{id}` y genera 1 tabla
- 1.6 Sistema procesa endpoint `/api/customer/{id}` y genera 1 tabla
- 1.7 Cada endpoint tiene su propio transformer module
- 1.8 Todos los transformers siguen la misma interfaz

### US-2: Como arquitecto de datos, quiero un pipeline unificado Bronze → Silver → Gold → Redshift
**Criterios de aceptación:**
- 2.1 Pipeline lee datos de Bronze (S3)
- 2.2 Pipeline aplica transformaciones y escribe a Silver (Iceberg)
- 2.3 Pipeline agrega datos y escribe a Gold (Iceberg)
- 2.4 Pipeline carga datos a Redshift desde Gold
- 2.5 Pipeline maneja deduplicación y resolución de conflictos
- 2.6 Pipeline mantiene trazabilidad completa (lineage)

### US-3: Como desarrollador, quiero módulos reutilizables para cada endpoint
**Criterios de aceptación:**
- 3.1 Cada endpoint tiene su EndpointFetcher
- 3.2 Cada entidad tiene su SchemaMapper
- 3.3 Cada tabla tiene su RedshiftTransformer
- 3.4 Todos los módulos son configurables vía JSON
- 3.5 Módulos pueden ejecutarse independientemente para testing

### US-4: Como operador, quiero orquestación automática del pipeline
**Criterios de aceptación:**
- 4.1 EventBridge gatilla polling según frecuencias definidas
- 4.2 MWAA orquesta ejecución de Glue Jobs
- 4.3 Sistema maneja dependencias entre jobs
- 4.4 Sistema reintenta fallos automáticamente
- 4.5 Sistema alerta en caso de fallos críticos

### US-5: Como analista de BI, quiero datos actualizados en Redshift
**Criterios de aceptación:**
- 5.1 Datos de orders actualizados cada 5 minutos
- 5.2 Datos de stock actualizados cada 10 minutos
- 5.3 Datos de products actualizados cada hora
- 5.4 Datos de prices actualizados cada 30 minutos
- 5.5 Datos de stores actualizados cada 24 horas
- 5.6 Power BI puede consultar datos sin latencia

---

## 4. Requerimientos Funcionales

### RF-1: Endpoint Fetchers
**Descripción:** Módulos para obtener datos de cada endpoint de Janis API

**Módulos a implementar:**
- `OrderFetcher` - Obtiene órdenes con items y shipping
- `ProductFetcher` - Obtiene productos con SKUs
- `StockFetcher` - Obtiene inventario
- `PriceFetcher` - Obtiene precios
- `StoreFetcher` - Obtiene tiendas
- `CustomerFetcher` - Obtiene clientes

**Funcionalidad común:**
- Autenticación con headers Janis
- Manejo de paginación
- Retry con exponential backoff
- Rate limiting (100 req/min)
- Logging completo

**Validación:**
- Fetchers obtienen datos correctamente
- Manejo de errores robusto
- Respeta rate limits

### RF-2: Schema Mappers
**Descripción:** Módulos para mapear JSON de API a esquemas de tablas

**Módulos a implementar:**
- `OrdersMapper` - Mapea a wms_orders (26 campos)
- `OrderItemsMapper` - Mapea a wms_order_items (11 campos)
- `OrderShippingMapper` - Mapea a wms_order_shipping (12 campos)
- `ProductsMapper` - Mapea a wms_products
- `ProductSkusMapper` - Mapea a wms_product_skus
- `StockMapper` - Mapea a wms_stock
- `PricesMapper` - Mapea a wms_prices
- `StoresMapper` - Mapea a wms_stores
- `CustomersMapper` - Mapea a wms_customers

**Funcionalidad:**
- Extracción de campos anidados
- Manejo de arrays (items, shippings)
- Valores por defecto para campos faltantes
- Validación de tipos de datos

**Validación:**
- Mapeo correcto de todos los campos
- Manejo de campos opcionales
- Preservación de tipos de datos

### RF-3: Pipeline Bronze → Silver
**Descripción:** Transformación de datos raw a datos limpios

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

### RF-4: Pipeline Silver → Gold
**Descripción:** Agregación y optimización para BI

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

### RF-5: RedshiftLoader
**Descripción:** Carga incremental de Gold a Redshift

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

### RF-6: Orquestación con EventBridge + MWAA
**Descripción:** Scheduling y ejecución automática

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

---

## 5. Requerimientos No Funcionales

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

## 6. Dependencias

### Dependencias Técnicas
- AWS Glue 4.0
- Apache Iceberg 1.4+
- Amazon Redshift (existente)
- EventBridge
- MWAA (Airflow 2.7.2)
- Python 3.11
- PySpark 3.3+

### Dependencias de Código
- 16 módulos existentes en `glue/modules/`
- Script `pipeline_with_schema_mapping.py` (base)
- Specs existentes (webhooks, polling, transformation, redshift)

### Dependencias de Infraestructura
- VPC y subnets configuradas
- S3 buckets (Bronze/Silver/Gold)
- IAM roles
- Security groups
- Redshift cluster existente

---

## 7. Criterios de Éxito

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

## 8. Riesgos

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

## 9. Restricciones

### Restricción 1: Compatibilidad con Redshift Existente
- No se pueden modificar esquemas de tablas existentes
- Debe mantener compatibilidad con Power BI actual
- No se puede interrumpir servicio actual

### Restricción 2: Rate Limits de Janis API
- Máximo 100 requests/minuto
- Debe respetar límites para no ser bloqueado

### Restricción 3: Ventanas de Mantenimiento
- Cargas a Redshift solo en horarios permitidos
- No impactar consultas de BI en horario laboral

### Restricción 4: Presupuesto
- Optimizar costos de AWS
- Usar recursos eficientemente
- Monitorear gastos continuamente

---

## 10. Próximos Pasos

1. **Crear design document** con arquitectura detallada
2. **Crear tasks** para cada fase de implementación
3. **Implementar Fase 1:** Fetchers y Mappers
4. **Implementar Fase 2:** Pipeline Bronze → Silver
5. **Implementar Fase 3:** Pipeline Silver → Gold
6. **Implementar Fase 4:** RedshiftLoader
7. **Implementar Fase 5:** Orquestación
8. **Implementar Fase 6:** Testing y Validación

---

**Documento creado:** 19 de Febrero, 2026  
**Última actualización:** 19 de Febrero, 2026  
**Estado:** Requirements definidos - Listo para diseño
