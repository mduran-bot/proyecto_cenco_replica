# 🔄 FLUJO MULTI-TENANT: API POLLING + API GATEWAY

## 🎯 CONCEPTO MULTI-TENANT

**2 Clientes (Tenants):**
- **Metro** → Base de datos independiente en Janis
- **Wongio** → Base de datos independiente en Janis

**Identificación:** Header HTTP `janis-client: metro` o `janis-client: wongio`

---

## 📊 FLUJO 1: API POLLING (Janis → AWS)

```
┌─────────────────────────────────────────────────────────────┐
│                    EVENTBRIDGE                              │
│                 (Trigger cada X min)                        │
└────────────────────────┬────────────────────────────────────┘
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    MWAA (Airflow)                           │
│                                                             │
│  DAG: poll_orders                                           │
│  ┌───────────────────────────────────────────────────────┐ │
│  │  FOR client IN ['metro', 'wongio']:                  │ │
│  │                                                       │ │
│  │    Task 1: fetch_orders(client='metro')              │ │
│  │       ├─ GET last_sync from DynamoDB                 │ │
│  │       ├─ Call Janis API:                             │ │
│  │       │    GET https://oms.janis.in/api/order        │ │
│  │       │    Header: janis-client: metro               │ │
│  │       ├─ Save to S3: bronze/metro/orders/            │ │
│  │       └─ Update DynamoDB: last_sync                  │ │
│  │                                                       │ │
│  │    Task 2: fetch_orders(client='wongio')             │ │
│  │       ├─ GET last_sync from DynamoDB                 │ │
│  │       ├─ Call Janis API:                             │ │
│  │       │    GET https://oms.janis.in/api/order        │ │
│  │       │    Header: janis-client: wongio              │ │
│  │       ├─ Save to S3: bronze/wongio/orders/           │ │
│  │       └─ Update DynamoDB: last_sync                  │ │
│  └───────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    JANIS APIs                               │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Recibe header: janis-client: metro                  │  │
│  │  → Devuelve datos de base de datos Metro            │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Recibe header: janis-client: wongio                 │  │
│  │  → Devuelve datos de base de datos Wongio           │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    S3 BRONZE                                │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  bronze/metro/orders/2026-02-24T10-05-00.json       │  │
│  │  bronze/metro/products/...                           │  │
│  │  bronze/metro/stock/...                              │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  bronze/wongio/orders/2026-02-24T10-05-00.json      │  │
│  │  bronze/wongio/products/...                          │  │
│  │  bronze/wongio/stock/...                             │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## 📡 FLUJO 2: API GATEWAY (AWS → Consumidores)

```
┌─────────────────────────────────────────────────────────────┐
│                    CONSUMIDORES                             │
│  (Power BI, Aplicaciones, Analistas)                       │
└────────────────────────┬────────────────────────────────────┘
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    API GATEWAY                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  GET /api/orders?client=metro                        │  │
│  │  Header: x-api-key: ***                              │  │
│  │                                                       │  │
│  │  → Valida API Key                                    │  │
│  │  → Extrae parámetro: client=metro                    │  │
│  │  → Invoca Lambda con client                          │  │
│  └──────────────────────────────────────────────────────┘  │
└────────────────────────┬────────────────────────────────────┘
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    LAMBDA FUNCTION                          │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  def get_orders(event):                              │  │
│  │    client = event['queryStringParameters']['client'] │  │
│  │                                                       │  │
│  │    if client == 'metro':                             │  │
│  │      path = 'gold/metro/orders/'                     │  │
│  │    elif client == 'wongio':                          │  │
│  │      path = 'gold/wongio/orders/'                    │  │
│  │                                                       │  │
│  │    data = read_from_s3(path)                         │  │
│  │    return data                                       │  │
│  └──────────────────────────────────────────────────────┘  │
└────────────────────────┬────────────────────────────────────┘
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    S3 GOLD                                  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  gold/metro/orders/                                  │  │
│  │  gold/metro/products/                                │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  gold/wongio/orders/                                 │  │
│  │  gold/wongio/products/                               │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    RESPUESTA                                │
│  {                                                          │
│    "client": "metro",                                       │
│    "orders": [...]                                          │
│  }                                                          │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔑 PUNTOS CLAVE MULTI-TENANT

### **1. API Polling (Entrada de datos)**
- Cada cliente se identifica con header `janis-client`
- Los datos se guardan en rutas S3 separadas por cliente
- DynamoDB trackea el estado por cliente

### **2. API Gateway (Salida de datos)**
- Cada request incluye parámetro `?client=metro` o `?client=wongio`
- Lambda lee datos de la ruta S3 correspondiente al cliente
- Los datos nunca se mezclan entre clientes

### **3. Separación de Datos**
```
S3 Structure:
├── bronze/
│   ├── metro/     ← Datos crudos de Metro
│   └── wongio/    ← Datos crudos de Wongio
├── silver/
│   ├── metro/     ← Datos transformados de Metro
│   └── wongio/    ← Datos transformados de Wongio
└── gold/
    ├── metro/     ← Datos curados de Metro
    └── wongio/    ← Datos curados de Wongio
```

---

## 📋 RESUMEN

| Componente | Multi-Tenant | Método |
|------------|--------------|--------|
| **API Polling** | ✅ | Header `janis-client: {tenant}` |
| **S3 Storage** | ✅ | Rutas separadas por tenant |
| **DynamoDB** | ✅ | Keys incluyen tenant |
| **API Gateway** | ✅ | Query param `?client={tenant}` |
| **Lambda** | ✅ | Lee datos según tenant |

**Total de llamadas:** 10 endpoints × 2 clientes = 20 llamadas por ciclo completo
