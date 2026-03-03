# Explicación: Bases de Datos Actuales vs Solución Propuesta

## Situación Actual de Cencosud

### 🗄️ Tres Bases de Datos MySQL Separadas

Actualmente, Cencosud consume datos de **tres réplicas independientes** de bases de datos MySQL 8 de Janis:

```
┌─────────────────────────────────────────────────────────────┐
│                    SITUACIÓN ACTUAL                          │
└─────────────────────────────────────────────────────────────┘

    ┌──────────────────┐      ┌──────────────────┐      ┌──────────────────┐
    │   MySQL Legacy   │      │  MySQL WongIO    │      │  MySQL MetroIO   │
    │   (Janis V1)     │      │   (Janis V1)     │      │   (Janis V1)     │
    └────────┬─────────┘      └────────┬─────────┘      └────────┬─────────┘
             │                         │                         │
             │ Réplica                 │ Réplica                 │ Réplica
             │ Directa                 │ Directa                 │ Directa
             ▼                         ▼                         ▼
    ┌──────────────────┐      ┌──────────────────┐      ┌──────────────────┐
    │  Redshift Cenco  │      │  Redshift Cenco  │      │  Redshift Cenco  │
    │                  │      │                  │      │                  │
    │ wms_orders       │      │ wms_orders       │      │ wms_orders       │
    │ wms_order_items  │      │ wms_order_items  │      │ wms_order_items  │
    │ wms_stores       │      │ wms_stores       │      │ wms_stores       │
    │ customers        │      │ customers        │      │ customers        │
    │ ...              │      │ ...              │      │ ...              │
    └──────────────────┘      └──────────────────┘      └──────────────────┘
         (26 tablas)              (26 tablas)              (26 tablas)
```

### 📊 Características de las Bases Actuales

| Aspecto | Descripción |
|---------|-------------|
| **Número de Bases** | 3 bases MySQL independientes |
| **Origen** | Janis API V1 (legacy) |
| **Canales** | Legacy, WongIO, MetroIO |
| **Estructura** | **Las 26 tablas son IDÉNTICAS en estructura** |
| **Diferencia** | Solo varía el **contenido** (datos por canal/banner) |
| **Conexión** | Réplica directa MySQL → Redshift |
| **Problema** | Redundancia, complejidad operativa, dependencia de V1 |

### 🔍 ¿Las Tablas son Diferentes?

**NO. Las tablas tienen la MISMA estructura en las 3 bases de datos.**

La diferencia está en el **contenido**:
- **Legacy**: Datos históricos de operaciones antiguas
- **WongIO**: Datos del canal Wong (banner/tienda)
- **MetroIO**: Datos del canal Metro (banner/tienda)

**Ejemplo:**
```sql
-- Las 3 bases tienen la MISMA tabla wms_orders con los MISMOS campos:
CREATE TABLE wms_orders (
    id BIGINT,
    vtex_id VARCHAR(50),
    seq_id VARCHAR(50),
    ecommerce_account BIGINT,
    seller_id BIGINT,
    website_name VARCHAR(100),
    customer BIGINT,
    store BIGINT,
    total DECIMAL(15,5),
    status SMALLINT,
    date_created BIGINT,
    ...
);

-- Lo que cambia es el CONTENIDO:
-- Legacy: órdenes antiguas
-- WongIO: órdenes de Wong
-- MetroIO: órdenes de Metro
```

---

## Solución Propuesta: Data Lake Unificado

### 🎯 Arquitectura de Integración Única

La solución propuesta **elimina la redundancia** y centraliza todo en un único flujo:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         SOLUCIÓN PROPUESTA                               │
└─────────────────────────────────────────────────────────────────────────┘

                    ┌──────────────────────────────┐
                    │      Janis API V2            │
                    │   (Fuente Única Unificada)   │
                    └──────────┬───────────────────┘
                               │
                ┌──────────────┴──────────────┐
                │                             │
                ▼                             ▼
        ┌───────────────┐           ┌─────────────────┐
        │   Webhooks    │           │  API Polling    │
        │ (Tiempo Real) │           │  (Scheduled)    │
        └───────┬───────┘           └────────┬────────┘
                │                            │
                └──────────┬─────────────────┘
                           ▼
                ┌──────────────────────┐
                │   API Gateway +      │
                │  Kinesis Firehose    │
                └──────────┬───────────┘
                           ▼
                ┌──────────────────────┐
                │   S3 Bronze Layer    │
                │   (Raw JSON Data)    │
                │                      │
                │ ✓ orders/            │
                │ ✓ products/          │
                │ ✓ stores/            │
                │ ✓ customers/         │
                └──────────┬───────────┘
                           ▼
                ┌──────────────────────┐
                │    AWS Glue ETL      │
                │  (Transformaciones)  │
                └──────────┬───────────┘
                           ▼
                ┌──────────────────────┐
                │  S3 Silver Layer     │
                │  (Apache Iceberg)    │
                │                      │
                │ ✓ Limpieza           │
                │ ✓ Normalización      │
                │ ✓ Deduplicación      │
                │ ✓ Conversión Tipos   │
                └──────────┬───────────┘
                           ▼
                ┌──────────────────────┐
                │   S3 Gold Layer      │
                │  (Apache Iceberg)    │
                │                      │
                │ ✓ Agregaciones       │
                │ ✓ Métricas           │
                │ ✓ Optimizado BI      │
                └──────────┬───────────┘
                           ▼
                ┌──────────────────────┐
                │  Redshift Unificado  │
                │                      │
                │ wms_orders           │
                │ wms_order_items      │
                │ wms_stores           │
                │ customers            │
                │ ...                  │
                │                      │
                │ + sales_channel      │
                │ + banner_id          │
                └──────────┬───────────┘
                           ▼
                ┌──────────────────────┐
                │      Power BI        │
                │  (Reportes Únicos)   │
                └──────────────────────┘
```

### 🔄 Cómo se Manejan los Datos de las 3 Fuentes

#### 1️⃣ **Fuente Única: Janis API V2**

En lugar de 3 bases de datos separadas, ahora hay **UNA sola API** que entrega todos los datos:

```json
// Ejemplo: Orden de Wong
{
  "id": "123456",
  "commerceId": "WONG-ORD-001",
  "salesChannelId": 1,           // ← Identifica el canal
  "salesChannelName": "Wong",    // ← Identifica el banner
  "account": {
    "id": 100,
    "name": "Wong Peru"
  },
  "seller": {
    "id": 200,
    "name": "Wong Store Lima"
  },
  "totalAmount": 150.50,
  "status": "delivered",
  ...
}

// Ejemplo: Orden de Metro
{
  "id": "789012",
  "commerceId": "METRO-ORD-002",
  "salesChannelId": 2,           // ← Identifica el canal
  "salesChannelName": "Metro",   // ← Identifica el banner
  "account": {
    "id": 101,
    "name": "Metro Peru"
  },
  "seller": {
    "id": 201,
    "name": "Metro Store Callao"
  },
  "totalAmount": 89.99,
  "status": "picking",
  ...
}
```

#### 2️⃣ **Identificación por Campos de Origen**

La solución **NO replica la separación física** de las 3 bases. En su lugar:

| Método de Identificación | Campo en API | Campo en Redshift | Propósito |
|--------------------------|--------------|-------------------|-----------|
| **Canal de Venta** | `salesChannelId` | `sales_channel` | Identifica Wong, Metro, Legacy |
| **Nombre del Canal** | `salesChannelName` | `website_name` | Nombre legible del canal |
| **Cuenta Ecommerce** | `account.id` | `ecommerce_account` | ID de la cuenta comercial |
| **Seller** | `seller.id` | `seller_id` | ID del vendedor/tienda |

**Ejemplo en Redshift:**
```sql
-- Tabla ÚNICA wms_orders con datos de TODOS los canales
SELECT 
    id,
    vtex_id,
    website_name,        -- 'Wong', 'Metro', 'Legacy'
    sales_channel,       -- 1, 2, 3
    ecommerce_account,   -- 100, 101, 102
    total,
    status
FROM wms_orders
WHERE website_name = 'Wong';  -- Filtrar por canal

-- Power BI puede filtrar por canal sin necesidad de 3 tablas separadas
```

#### 3️⃣ **¿Qué Pasa si los Datos son Diferentes?**

##### Caso A: Datos con Estructura Diferente

Si un campo existe en Wong pero no en Metro:

```
┌─────────────────────────────────────────────────────────┐
│  Estrategia: Campos Opcionales + Metadata Tracking      │
└─────────────────────────────────────────────────────────┘

API Wong:
{
  "id": "123",
  "loyaltyPoints": 500,  // ← Campo exclusivo de Wong
  "salesChannel": "Wong"
}

API Metro:
{
  "id": "456",
  // loyaltyPoints NO existe
  "salesChannel": "Metro"
}

Redshift (Tabla Unificada):
┌────┬──────────────┬──────────────┬──────────────┐
│ id │ sales_channel│ loyalty_points│ data_source │
├────┼──────────────┼──────────────┼──────────────┤
│123 │ Wong         │ 500          │ Wong API    │
│456 │ Metro        │ NULL         │ Metro API   │
└────┴──────────────┴──────────────┴──────────────┘
                        ↑
                  Campo opcional
                  (NULL para Metro)
```

**Solución:**
- **Campos opcionales** en el esquema Redshift
- **Metadata tracking** para saber qué campos están disponibles por canal
- **Documentación clara** de qué campos aplican a qué canales

##### Caso B: Datos con Mismo Campo pero Formato Diferente

Si Wong usa formato numérico y Metro usa string:

```
┌─────────────────────────────────────────────────────────┐
│  Estrategia: Normalización en Capa Silver               │
└─────────────────────────────────────────────────────────┘

Bronze (Raw):
Wong:  {"orderId": 12345}        // número
Metro: {"orderId": "ORD-67890"}  // string

Silver (Normalizado):
Wong:  {"order_id": "12345"}     // string normalizado
Metro: {"order_id": "67890"}     // string normalizado

Gold (Redshift):
┌────────────┬──────────────┐
│ order_id   │ sales_channel│
├────────────┼──────────────┤
│ 12345      │ Wong         │
│ 67890      │ Metro        │
└────────────┴──────────────┘
```

**Solución:**
- **Normalización en AWS Glue** (capa Silver)
- **Conversión de tipos** consistente
- **Validación de datos** antes de cargar a Redshift

##### Caso C: Datos Idénticos (Mismo Esquema)

Si las tablas son estructuralmente idénticas:

```
┌─────────────────────────────────────────────────────────┐
│  Estrategia: Consolidación + Flag de Origen             │
└─────────────────────────────────────────────────────────┘

Bronze:
Wong:  {"id": 1, "name": "Product A", "price": 10.50}
Metro: {"id": 2, "name": "Product B", "price": 15.00}

Silver/Gold (Consolidado):
┌────┬───────────┬───────┬──────────────┐
│ id │ name      │ price │ sales_channel│
├────┼───────────┼───────┼──────────────┤
│ 1  │ Product A │ 10.50 │ Wong         │
│ 2  │ Product B │ 15.00 │ Metro        │
└────┴───────────┴───────┴──────────────┘
```

**Solución:**
- **Tabla única** en Redshift
- **Columna de origen** (`sales_channel`, `website_name`)
- **Power BI filtra** por canal según necesidad

---

## 🎯 Respuestas a tus Preguntas

### ❓ "¿Las tablas son diferentes por base de datos?"

**NO.** Las 26 tablas tienen la **misma estructura** en las 3 bases de datos actuales (Legacy, WongIO, MetroIO).

Lo que cambia es el **contenido** (datos por canal/banner).

### ❓ "¿Para la solución todo debe estar preparado para recibir cada tabla?"

**SÍ.** La solución está diseñada para recibir **todas las tablas** de forma unificada:

1. **Bronze Layer**: Recibe datos raw de la API (JSON)
2. **Silver Layer**: Limpia, normaliza y deduplica
3. **Gold Layer**: Agrega y optimiza para BI
4. **Redshift**: Tabla única por entidad con campo de origen

### ❓ "¿Las tablas son las mismas?"

**SÍ.** Las tablas en Redshift serán las **mismas 26 tablas** que existen actualmente, pero:

- **Unificadas**: Una sola tabla `wms_orders` en lugar de 3
- **Con identificador de origen**: Campo `sales_channel` o `website_name`
- **Optimizadas**: Con claves de distribución y ordenamiento
- **Completas**: Con todos los campos necesarios para BI

---

## 📋 Mapeo de Tablas: Actual vs Propuesta

### Situación Actual (3 Bases Separadas)

```
Redshift Actual:
├── wms_orders_legacy
├── wms_orders_wongio
├── wms_orders_metroio
├── wms_order_items_legacy
├── wms_order_items_wongio
├── wms_order_items_metroio
├── wms_stores_legacy
├── wms_stores_wongio
├── wms_stores_metroio
└── ... (78 tablas en total = 26 × 3)
```

### Solución Propuesta (Unificada)

```
Redshift Propuesto:
├── wms_orders              (datos de Wong + Metro + Legacy)
├── wms_order_items         (datos de Wong + Metro + Legacy)
├── wms_stores              (datos de Wong + Metro + Legacy)
├── customers               (datos de Wong + Metro + Legacy)
├── wms_order_shipping      (datos de Wong + Metro + Legacy)
├── wms_logistic_carriers   (datos de Wong + Metro + Legacy)
└── ... (26 tablas en total, todas unificadas)

Cada tabla incluye:
- sales_channel (1=Wong, 2=Metro, 3=Legacy)
- website_name ('Wong', 'Metro', 'Legacy')
- ecommerce_account (ID de cuenta)
```

---

## 🔧 Preparación de la Solución

### ¿Qué se Necesita Preparar?

#### 1. **Esquema Unificado en Redshift**

```sql
-- Ejemplo: Tabla wms_orders unificada
CREATE TABLE wms_orders (
    id BIGINT,
    vtex_id VARCHAR(50),
    seq_id VARCHAR(50),
    ecommerce_account BIGINT,        -- Identifica cuenta
    seller_id BIGINT,
    website_name VARCHAR(100),       -- 'Wong', 'Metro', 'Legacy'
    sales_channel SMALLINT,          -- 1, 2, 3
    customer BIGINT,
    store BIGINT,
    total DECIMAL(15,5),
    status SMALLINT,
    date_created BIGINT,
    -- ... resto de campos
    
    -- Metadata de origen
    data_source VARCHAR(50),         -- 'Janis API V2'
    ingestion_timestamp TIMESTAMP,   -- Cuándo se ingirió
    
    PRIMARY KEY (id)
)
DISTKEY(store)
SORTKEY(date_created, sales_channel);
```

#### 2. **Mapeo de Campos API → Redshift**

El archivo `Schema Definition Janis Final.csv` ya contiene el mapeo completo:

| Tabla Redshift | Campo Redshift | Campo API | Cobertura |
|----------------|----------------|-----------|-----------|
| wms_orders | vtex_id | commerceId | Completa |
| wms_orders | id | id | Completa |
| wms_orders | website_name | salesChannelName | Completa |
| wms_orders | sales_channel | salesChannelId | Completa |
| wms_orders | total | totalAmount | Completa |
| ... | ... | ... | ... |

#### 3. **Transformaciones en AWS Glue**

```python
# Ejemplo: Transformación Bronze → Silver
def transform_orders(bronze_df):
    """
    Transforma datos raw de API a formato Silver
    """
    silver_df = bronze_df.select(
        col("id").cast("bigint"),
        col("commerceId").alias("vtex_id"),
        col("salesChannelId").alias("sales_channel"),
        col("salesChannelName").alias("website_name"),
        col("account.id").alias("ecommerce_account"),
        col("totalAmount").cast("decimal(15,5)").alias("total"),
        col("status").cast("smallint"),
        from_unixtime(col("dateCreated")).alias("date_created"),
        # ... más campos
        lit("Janis API V2").alias("data_source"),
        current_timestamp().alias("ingestion_timestamp")
    )
    
    return silver_df
```

#### 4. **Deduplicación por Origen**

```python
# Si un registro viene por Webhook Y Polling, mantener el más reciente
deduplicated_df = silver_df \
    .withColumn("row_num", 
        row_number().over(
            Window.partitionBy("id")
                  .orderBy(col("date_modified").desc())
        )
    ) \
    .filter(col("row_num") == 1) \
    .drop("row_num")
```

---

## ✅ Ventajas de la Solución Unificada

| Aspecto | Situación Actual | Solución Propuesta |
|---------|------------------|-------------------|
| **Número de Tablas** | 78 (26 × 3) | 26 (unificadas) |
| **Complejidad Queries** | JOINs entre 3 tablas | Query única con filtro |
| **Mantenimiento** | 3 pipelines separados | 1 pipeline unificado |
| **Escalabilidad** | Difícil agregar canales | Fácil: solo agregar flag |
| **Consistencia** | Riesgo de desincronización | Datos siempre consistentes |
| **Performance** | Queries lentos (3 tablas) | Queries rápidos (1 tabla) |
| **Costo** | 3× almacenamiento | 1× almacenamiento |

---

## 📊 Ejemplo Práctico: Query en Power BI

### Antes (3 Tablas Separadas)

```sql
-- Power BI debe hacer UNION de 3 tablas
SELECT * FROM wms_orders_wongio
WHERE date_created >= '2024-01-01'
UNION ALL
SELECT * FROM wms_orders_metroio
WHERE date_created >= '2024-01-01'
UNION ALL
SELECT * FROM wms_orders_legacy
WHERE date_created >= '2024-01-01';
```

### Después (Tabla Unificada)

```sql
-- Power BI hace query simple con filtro
SELECT * 
FROM wms_orders
WHERE date_created >= '2024-01-01'
  AND website_name IN ('Wong', 'Metro');  -- Filtro opcional
```

---

## 🎯 Conclusión

### La Solución Propuesta:

1. ✅ **Elimina redundancia**: 1 tabla en lugar de 3
2. ✅ **Mantiene trazabilidad**: Campo `sales_channel` identifica origen
3. ✅ **Simplifica queries**: Filtro simple en lugar de UNIONs
4. ✅ **Facilita escalabilidad**: Agregar nuevos canales es trivial
5. ✅ **Reduce costos**: 1× almacenamiento en lugar de 3×
6. ✅ **Mejora performance**: Queries más rápidos
7. ✅ **Unifica mantenimiento**: 1 pipeline en lugar de 3

### Las Tablas:

- ✅ **Son las mismas 26 tablas** que existen actualmente
- ✅ **Tienen la misma estructura** en las 3 bases actuales
- ✅ **Se unifican en 1 sola tabla** por entidad en la solución
- ✅ **Incluyen campo de origen** para identificar canal/banner
- ✅ **Están preparadas** para recibir datos de todos los canales

---

**Fecha de Creación:** 24 de Febrero, 2026  
**Autor:** Kiro AI Assistant  
**Versión:** 1.0
