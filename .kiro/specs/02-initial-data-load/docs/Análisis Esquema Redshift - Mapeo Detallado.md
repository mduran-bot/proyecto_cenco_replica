# Análisis de Esquema Redshift - Mapeo Detallado para Integración Janis

**Fecha**: 2026-02-17  
**Base de Datos**: datalabs  
**Cluster**: dl-desa  
**Región**: us-east-1

## Resumen Ejecutivo

Se realizó un análisis exhaustivo del esquema de Redshift en la base de datos `datalabs` para identificar las estructuras de datos existentes y determinar los requisitos de transformación para la integración con el sistema WMS Janis.

### Hallazgos Clave

1. **Esquemas de Réplica Janis Vacíos**: Los esquemas `janis_aurorape_replica`, `janis_metroio_replica` y `janis_wongio_replica` existen pero no contienen tablas actualmente.

2. **Esquemas Activos Identificados**:
   - `dl_sp_table_stg`: Tablas de staging con dimensiones de productos y proveedores
   - `dl_sp_dashboards_ecommerce`: Tablas transaccionales de ecommerce
   - `dl_sp_dashboards_ventas`: Dashboards de ventas
   - Múltiples esquemas de staging y procesamiento

3. **Estructura de Datos Existente**: El Redshift ya tiene una estructura dimensional madura con tablas de dimensiones (dim_*) y tablas de hechos (tbl_trx_*).

## Esquemas Disponibles en Redshift

### Esquemas de Réplica Janis (Vacíos - Preparados para Carga)
```
- janis_aurorape_replica
- janis_metroio_replica  
- janis_wongio_replica
```

**Estado**: Esquemas creados pero sin tablas. Estos serán los destinos para la carga inicial de datos desde MySQL de Janis.

### Esquemas de Staging y Procesamiento
```
- dl_sp_table_stg              # Tablas de staging principales
- dl_sp_proc_stg               # Procedimientos de staging
- dl_sp_temporal               # Tablas temporales
- dl_sp_cargamanual            # Cargas manuales
```

### Esquemas de Dashboards y Analítica
```
- dl_sp_dashboards_ecommerce   # Dashboards de ecommerce
- dl_sp_dashboards_ventas      # Dashboards de ventas
- dl_sp_dashboards_ventas_linea # Dashboards de ventas por línea
- dl_sp_capa_semantica         # Capa semántica para BI
```

### Esquemas de Staging Específicos
```
- stg_ecommerce_b2b_qa         # Staging B2B QA
- stg_ecommerce_vtex           # Staging VTEX
```

### Esquemas de Otros Sistemas
```
- datpetest_cencosud_pe_sm_dmt_dev  # Data Mart Dev
- datpetest_cencosud_pe_sm_mst_dev  # Master Dev
- datpetest_cencosud_pe_sm_raw_dev  # Raw Dev
- datpetest_cencosud_pe_sm_stg_dev  # Staging Dev
- pe_sm_dmt_prod                     # Data Mart Prod
- per_super_pd_int                   # Super Perú Integración
- per_super_ts_int                   # Super Perú TS Integración
- per_super_ts_stg                   # Super Perú TS Staging
```

## Tablas Clave Identificadas

### Esquema: dl_sp_table_stg (Staging Principal)

#### Dimensiones de Productos
1. **dim_material** (Dimensión de Materiales/Productos)
   - Tabla dimensional principal para productos
   - Contiene 85+ columnas con información detallada
   - Campos clave identificados:
     - `sk_material` (Surrogate Key)
     - `id_material` (ID de negocio)
     - `desc_material` (Descripción)
     - `id_ean` (Código de barras)
     - `sk_marca`, `sk_proveedor`, `sk_categoria`
     - Campos de clasificación: `id_clasificado`, `id_aplica_ley`, `id_aplica_advertencia`
     - Campos de volumetría: `id_um_base`, `id_um_volumetria`, `cnt_um_volumetria_contenido_neto`
     - Campos de pricing: `id_familia_pricing`, `id_material_observado_pricing`
     - Campos de surtido: `sk_tipo_surtido_incluido`, `sk_clase_surtido`
     - Campos de estado: `sk_estado_corporativo`
     - Campos de gestión: `sk_gestor_material`
     - Campos de fechas: `sk_dia_creacion_material`

2. **dim_proveedor** (Dimensión de Proveedores)
   - Información de proveedores
   - Campos clave:
     - `sk_proveedor` (Surrogate Key)
     - `id_proveedor` (ID de negocio)
     - `cod_proveedor_ruc` (RUC)
     - `desc_proveedor` (Nombre)
     - `cod_proveedor_pais` (País)
     - `sk_tipo_flujo_proveedor` (Tipo de flujo)
     - `id_flag_cobro` (Flag de cobro)
     - `num_orden_proveedor` (Orden)

3. **dim_ean** (Dimensión de Códigos EAN)
   - Códigos de barras y SKUs

4. **dim_marca** (Dimensión de Marcas)
   - Información de marcas de productos

#### Tablas Catálogo
- `cat_material`: Catálogo de materiales
- `cat_proveedor`: Catálogo de proveedores
- `ic_material`: Información complementaria de materiales
- `material`: Tabla de materiales base

### Esquema: dl_sp_dashboards_ecommerce (Transaccional Ecommerce)

#### Tablas Transaccionales

1. **tbl_trx_quiebres_ecommerce** (Quiebres de Stock Ecommerce)
   - Tabla de hechos para análisis de quiebres de stock
   - 124 columnas identificadas
   - Campos clave:
     - Dimensiones: `sk_dia`, `sk_tienda`, `id_material`, `id_proveedor`
     - Métricas de stock: `cnt_stock_inicio_dia`, `cnt_stock_fin_dia`, `mto_stock_inicio_dia`, `mto_stock_fin_dia`
     - Métricas de ventas: `cnt_venta_dia`, `mto_venta_dia`, `cnt_pedido_dia`, `mto_pedido_dia`
     - Métricas de picking: `cnt_pedido_pickeado`, `cnt_pedido_no_pickeado`, `cnt_pedido_parcial`
     - Indicadores: `ultdiaventa`, `diassinventa`, `ultdiaingreso`, `diasultimoingreso`
     - Clasificación: `id_tipo_set_venta`, `id_clase_surtido`, `id_tipo_surtido_incluido`
     - Fill Rate: `found_rate_ecommerce`, `fr_15d`
     - Cobertura: `cob_inicio`, `cob_fin`
     - Gestión: `gestion`, `tipo`, `subtipo`
     - Flags: `id_void`, `id_set_venta`, `id_fictico`, `id_trastienda`, `id_picking`, `id_sin_stock`
     - Temporal: `sk_mes`, `sk_semana`, `fecha_registro_tabla`

2. **eco_logs_pedidos_hoy** (Logs de Pedidos del Día)
   - Logs operacionales de pedidos ecommerce

3. **arcus_productos_faltantes** (Productos Faltantes)
   - Tracking de productos faltantes

## Mapeo de Datos: Janis → Redshift

### Entidades Principales a Integrar

#### 1. Productos (Products)
**Origen**: API Janis `/products`  
**Destino Propuesto**: `janis_metroio_replica.products` (Bronze) → `dl_sp_table_stg.dim_material` (Silver/Gold)

**Campos a Mapear**:
```
Janis API          →  Redshift dim_material
-----------------     ----------------------
product_id         →  id_material
sku                →  id_material (alternativo)
name               →  desc_material
ean                →  id_ean (FK a dim_ean)
brand_id           →  sk_marca (FK a dim_marca)
supplier_id        →  sk_proveedor (FK a dim_proveedor)
category_id        →  sk_categoria
price              →  (campo a definir)
cost               →  (campo a definir)
stock_quantity     →  (campo a definir)
status             →  sk_estado_corporativo
created_at         →  sk_dia_creacion_material
updated_at         →  (campo de auditoría)
```

#### 2. Órdenes (Orders)
**Origen**: API Janis `/orders` + Webhooks  
**Destino Propuesto**: `janis_metroio_replica.orders` (Bronze) → `dl_sp_dashboards_ecommerce.tbl_trx_*` (Silver/Gold)

**Campos a Mapear**:
```
Janis API          →  Redshift tbl_trx_quiebres_ecommerce
-----------------     ----------------------------------------
order_id           →  (campo a definir - PK)
order_date         →  sk_dia (FK a dim_dia)
store_id           →  sk_tienda (FK a dim_tienda)
customer_id        →  (campo a definir)
status             →  (campo de estado)
total_amount       →  mto_pedido_dia
items[]            →  (detalle en tabla relacionada)
  - product_id     →  id_material
  - quantity       →  cnt_pedido_dia
  - price          →  mto_venta_dia
  - picked         →  cnt_pedido_pickeado
created_at         →  fecha_registro_tabla
updated_at         →  (campo de auditoría)
```

#### 3. Inventario (Stock)
**Origen**: API Janis `/stock`  
**Destino Propuesto**: `janis_metroio_replica.stock` (Bronze) → `dl_sp_dashboards_ecommerce.tbl_trx_quiebres_ecommerce` (Silver/Gold)

**Campos a Mapear**:
```
Janis API          →  Redshift tbl_trx_quiebres_ecommerce
-----------------     ----------------------------------------
product_id         →  id_material
store_id           →  sk_tienda
quantity           →  cnt_stock_fin_dia
value              →  mto_stock_fin_dia
location           →  (campo a definir)
last_updated       →  fecha_registro_tabla
```

#### 4. Precios (Prices)
**Origen**: API Janis `/prices`  
**Destino Propuesto**: `janis_metroio_replica.prices` (Bronze) → `dl_sp_table_stg.dim_material` o tabla de hechos de precios

**Campos a Mapear**:
```
Janis API          →  Redshift
-----------------     ----------------------
product_id         →  id_material
store_id           →  sk_tienda
price              →  (campo de precio)
cost               →  (campo de costo)
effective_date     →  sk_dia
price_type         →  (campo de tipo de precio)
```

#### 5. Tiendas (Stores)
**Origen**: API Janis `/stores`  
**Destino Propuesto**: `janis_metroio_replica.stores` (Bronze) → `dl_sp_table_stg.dim_tienda` (Silver/Gold)

**Campos a Mapear**:
```
Janis API          →  Redshift dim_tienda
-----------------     ----------------------
store_id           →  sk_tienda / id_tienda
name               →  desc_tienda
code               →  cod_tienda
region             →  (campo de región)
type               →  (campo de tipo)
status             →  (campo de estado)
```

## Arquitectura de Capas Propuesta

### Capa Bronze (Raw Data)
**Esquemas**: `janis_aurorape_replica`, `janis_metroio_replica`, `janis_wongio_replica`

- Datos crudos desde MySQL/API de Janis
- Estructura 1:1 con origen
- Sin transformaciones
- Formato: Tablas relacionales estándar

### Capa Silver (Cleaned & Conformed)
**Esquemas**: `dl_sp_table_stg`, `dl_sp_proc_stg`

- Datos limpios y conformados
- Aplicación de reglas de negocio
- Deduplicación y validación
- Formato: Tablas dimensionales y de staging

### Capa Gold (Business-Ready)
**Esquemas**: `dl_sp_dashboards_ecommerce`, `dl_sp_dashboards_ventas`, `dl_sp_capa_semantica`

- Datos agregados y optimizados para BI
- Modelos dimensionales completos
- Métricas de negocio calculadas
- Formato: Tablas de hechos y dimensiones para dashboards

## Transformaciones Requeridas

### 1. Transformaciones de Productos (Bronze → Silver)

```sql
-- Ejemplo conceptual de transformación
INSERT INTO dl_sp_table_stg.dim_material
SELECT 
    -- Generar surrogate key
    ROW_NUMBER() OVER (ORDER BY product_id) as sk_material,
    
    -- Campos de negocio
    product_id as id_material,
    name as desc_material,
    ean as id_ean,
    
    -- Lookups a otras dimensiones
    (SELECT sk_marca FROM dim_marca WHERE id_marca = brand_id) as sk_marca,
    (SELECT sk_proveedor FROM dim_proveedor WHERE id_proveedor = supplier_id) as sk_proveedor,
    
    -- Campos calculados
    CASE 
        WHEN status = 'active' THEN 1
        WHEN status = 'inactive' THEN 2
        ELSE 0
    END as sk_estado_corporativo,
    
    -- Auditoría
    CURRENT_TIMESTAMP as fecha_carga
FROM janis_metroio_replica.products
WHERE updated_at > (SELECT MAX(fecha_ultima_carga) FROM control_carga);
```

### 2. Transformaciones de Órdenes (Bronze → Gold)

```sql
-- Ejemplo conceptual de agregación para dashboard
INSERT INTO dl_sp_dashboards_ecommerce.tbl_trx_quiebres_ecommerce
SELECT 
    -- Dimensiones
    DATE_TRUNC('day', order_date) as sk_dia,
    store_id as sk_tienda,
    product_id as id_material,
    
    -- Métricas agregadas
    COUNT(DISTINCT order_id) as cnt_pedido_dia,
    SUM(total_amount) as mto_pedido_dia,
    SUM(CASE WHEN status = 'picked' THEN 1 ELSE 0 END) as cnt_pedido_pickeado,
    SUM(CASE WHEN status = 'not_picked' THEN 1 ELSE 0 END) as cnt_pedido_no_pickeado,
    
    -- Indicadores calculados
    ROUND(SUM(CASE WHEN status = 'picked' THEN 1 ELSE 0 END)::NUMERIC / 
          NULLIF(COUNT(*), 0), 4) as found_rate_ecommerce,
    
    -- Auditoría
    CURRENT_TIMESTAMP as fecha_registro_tabla
FROM janis_metroio_replica.orders o
JOIN janis_metroio_replica.order_items oi ON o.order_id = oi.order_id
WHERE o.order_date >= CURRENT_DATE - INTERVAL '1 day'
GROUP BY 1, 2, 3;
```

## Consideraciones Técnicas

### 1. Permisos y Acceso
- ✅ Acceso de lectura confirmado con usuario `usr_admin`
- ✅ Capacidad de ejecutar consultas en base de datos `datalabs`
- ⚠️ Permisos de escritura a validar para esquemas de réplica Janis
- ⚠️ Permisos de creación de tablas a validar

### 2. Volumetría Estimada
- **dim_material**: ~100K productos (estimado)
- **tbl_trx_quiebres_ecommerce**: ~1M registros/día (estimado)
- **orders**: ~50K órdenes/día (estimado)
- **stock**: ~500K registros de inventario (estimado)

### 3. Frecuencia de Actualización
- **Productos**: Diaria (polling) + Tiempo real (webhooks)
- **Órdenes**: Tiempo real (webhooks) + Polling cada 15 min
- **Stock**: Cada hora (polling)
- **Precios**: Diaria (polling)

### 4. Estrategia de Carga
- **Carga Inicial**: Full load desde MySQL backup
- **Carga Incremental**: CDC (Change Data Capture) vía webhooks + polling
- **Reconciliación**: Proceso diario de validación de conteos

## Próximos Pasos

### Fase 1: Validación de Permisos
1. ✅ Confirmar acceso de lectura a Redshift
2. ⬜ Validar permisos de escritura en esquemas `janis_*_replica`
3. ⬜ Crear tablas de prueba en esquema de réplica
4. ⬜ Validar permisos de creación de procedimientos almacenados

### Fase 2: Diseño Detallado de Esquemas
1. ⬜ Definir DDL completo para tablas Bronze (réplica 1:1 de Janis)
2. ⬜ Definir transformaciones Silver (staging y limpieza)
3. ⬜ Definir agregaciones Gold (dashboards y analítica)
4. ⬜ Documentar mapeo campo a campo completo

### Fase 3: Implementación de Pipeline
1. ⬜ Configurar AWS Glue jobs para transformaciones Bronze → Silver
2. ⬜ Configurar AWS Glue jobs para transformaciones Silver → Gold
3. ⬜ Implementar validaciones de calidad de datos
4. ⬜ Configurar monitoreo y alertas

### Fase 4: Carga Inicial
1. ⬜ Ejecutar carga inicial desde backup MySQL
2. ⬜ Validar conteos y reconciliación
3. ⬜ Ejecutar transformaciones completas
4. ⬜ Validar datos en capa Gold

### Fase 5: Sincronización Continua
1. ⬜ Activar webhooks de Janis
2. ⬜ Configurar polling programado
3. ⬜ Monitorear latencia de datos
4. ⬜ Ajustar frecuencias según necesidad

## Conclusiones

1. **Infraestructura Preparada**: Los esquemas de réplica Janis ya existen en Redshift, listos para recibir datos.

2. **Modelo Dimensional Maduro**: Redshift ya tiene un modelo dimensional bien estructurado que podemos aprovechar.

3. **Mapeo Claro**: Se identificaron las tablas destino y los campos clave para cada entidad de Janis.

4. **Transformaciones Definidas**: Se documentaron las transformaciones necesarias para cada capa (Bronze/Silver/Gold).

5. **Próximos Pasos Claros**: Se definió un plan de implementación por fases con tareas específicas.

## Recomendaciones

1. **Validar Permisos**: Antes de continuar, confirmar permisos de escritura en esquemas de réplica.

2. **Crear Spec Detallado**: Generar un spec de implementación con DDL completo y transformaciones.

3. **Implementar en Fases**: Comenzar con una entidad (ej: productos) como prueba de concepto.

4. **Monitoreo Proactivo**: Implementar alertas desde el inicio para detectar problemas temprano.

5. **Documentación Continua**: Mantener documentación actualizada del mapeo y transformaciones.
