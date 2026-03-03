# 🧠 Apache Airflow: Sistema Nervioso Central - Resumen Ejecutivo

## 🎯 Vista Rápida

Apache Airflow actúa como el **Sistema Nervioso Central** de tu arquitectura de Data Lake, coordinando todas las operaciones de ingesta, transformación y carga de datos.

## 📊 Las 6 Conexiones Principales

```
                    🧠 APACHE AIRFLOW
                Sistema Nervioso Central
                          |
        +-----------------+-----------------+
        |                 |                 |
    ENTRADA           CONTROL            SALIDA
        |                 |                 |
    1️⃣ EventBridge    3️⃣ DynamoDB       4️⃣ S3 Bronze
    5️⃣ Webhooks                          6️⃣ Glue Jobs
                      2️⃣ Janis API
```

### 1️⃣ EventBridge → Airflow (ENTRADA)
**Qué hace:** Dispara DAGs en intervalos programados
**Dirección:** EventBridge → Airflow
**Frecuencia:** 5 min (orders), 10 min (stock), 30 min (prices), 1h (products), 24h (stores)

### 2️⃣ Airflow → Janis API (EXTRACCIÓN)
**Qué hace:** Obtiene datos operacionales de Janis
**Dirección:** Airflow → API Externa
**Método:** GET requests con filtros incrementales

### 3️⃣ Airflow ↔ DynamoDB (CONTROL)
**Qué hace:** Gestiona locks y timestamps para polling incremental
**Dirección:** Bidireccional (Lee y Escribe)
**Propósito:** Prevenir ejecuciones concurrentes

### 4️⃣ Airflow → S3 Bronze (PERSISTENCIA)
**Qué hace:** Guarda datos raw en formato JSON
**Dirección:** Airflow → S3
**Capa:** Bronze (datos sin procesar)

### 5️⃣ Lambda → Airflow (INTEGRACIÓN)
**Qué hace:** Procesa webhooks urgentes y dispara DAGs específicos
**Dirección:** Lambda → Airflow
**Trigger:** On-demand (eventos en tiempo real)

### 6️⃣ Airflow → Glue (ORQUESTACIÓN)
**Qué hace:** Inicia trabajos de transformación ETL
**Dirección:** Airflow → Glue
**Proceso:** Bronze → Silver → Gold

## 🔄 Flujo de Ejecución (Ejemplo: Orders)

```
⏰ EventBridge (10:25 AM)
    ↓
🔒 Acquire Lock en DynamoDB
    ↓
🔄 Build Incremental Filter (last_modified - 1 min)
    ↓
🌐 Poll Janis API (/orders)
    ↓
📄 Paginate Results (100 records/page)
    ↓
🔍 Deduplicate Records
    ↓
✅ Validate Schemas
    ↓
➕ Enrich Data (items, SKUs)
    ↓
💾 Write to S3 Bronze (JSON)
    ↓
🔓 Release Lock + Update Timestamp
    ↓
⚙️ Trigger Glue Job (Bronze → Silver)
    ↓
✅ DAG Completed
```

## 📈 Métricas Típicas

```
Ejecución de poll_orders:
├── Duración: 45 segundos
├── Records obtenidos: 245
├── Records únicos: 242
├── Records válidos: 240
├── API calls: 3 (paginación)
└── Estado: ✅ SUCCESS
```

## 🎨 Analogía Simple

Piensa en Airflow como un **Director de Orquesta**:

- 🎺 **EventBridge** = Marca el tempo (cuándo tocar)
- 🎻 **Janis API** = Toca la melodía (trae los datos)
- 🥁 **DynamoDB** = Mantiene el ritmo (control de estado)
- 🎹 **S3** = Armoniza (almacena los datos)
- 🎸 **Glue** = Improvisa (transforma los datos)

El director (Airflow) no toca ningún instrumento, solo **coordina** a todos los músicos.

## 💡 Puntos Clave

✅ **Airflow NO procesa datos pesados** - solo orquesta
✅ **Glue hace el procesamiento real** - transformaciones PySpark
✅ **DynamoDB previene concurrencia** - sistema de locks
✅ **Polling incremental** - solo trae datos nuevos/modificados
✅ **Overlap window de 1 minuto** - asegura no perder datos

## 📚 Documentación Completa

Para más detalles, consulta:
- [Arquitectura Completa](docs/ARQUITECTURA_AIRFLOW_VISUAL.md)
- [Diagrama Simplificado](docs/DIAGRAMA_SIMPLE_AIRFLOW.md)
- [Flujo Paso a Paso](docs/FLUJO_PASO_A_PASO.md)
- [Índice de Documentación](docs/README.md)

---

**¿Por qué tantas direcciones?**

Porque Airflow es el **cerebro** que coordina todo:
- Recibe instrucciones (EventBridge, Webhooks)
- Extrae información (Janis API)
- Controla el estado (DynamoDB)
- Almacena resultados (S3)
- Delega trabajo pesado (Glue)

Todo esto sin procesar los datos directamente, manteniendo la arquitectura **desacoplada** y **escalable**.
