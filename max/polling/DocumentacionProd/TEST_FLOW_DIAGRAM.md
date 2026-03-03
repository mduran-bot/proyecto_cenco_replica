# 📊 Diagrama de Flujo de Tests

**Última actualización:** Febrero 24, 2026

---

## 🎯 Test Básico - Flujo Completo

```
┌─────────────────────────────────────────────────────────────────────┐
│                    TEST: test_localstack_real_api.py                │
│                                                                     │
│  Prueba: 1 endpoint (/order) con 1 cliente (metro)                │
│  Tiempo: 5-10 segundos                                             │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│ PASO 1: Setup LocalStack                                           │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────────┐                                                  │
│  │  LocalStack  │  ← Verificar que esté corriendo                  │
│  │  (DynamoDB)  │  ← Crear tabla 'polling_control' si no existe   │
│  └──────────────┘                                                  │
│                                                                     │
│  ✅ Tabla creada/verificada                                        │
└─────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────┐
│ PASO 2: Adquirir Lock Multi-Tenant                                 │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Lock Key: "orders-metro"  ← Formato: {data_type}-{client}        │
│  Execution ID: "test-metro-1708776000"                             │
│                                                                     │
│  ┌──────────────┐                                                  │
│  │  DynamoDB    │  ← PutItem con condition: lock_acquired = false │
│  │  Table       │  → Lock adquirido exitosamente                  │
│  └──────────────┘                                                  │
│                                                                     │
│  ✅ Lock: orders-metro adquirido                                   │
└─────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────┐
│ PASO 3: Construir Filtro Incremental                               │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────────┐                                                  │
│  │  DynamoDB    │  ← GetItem(data_type="orders-metro")            │
│  │  Table       │  → last_modified_date: null (primera vez)       │
│  └──────────────┘                                                  │
│                                                                     │
│  Filtro: null (Full Refresh)                                       │
│                                                                     │
│  ✅ Primera ejecución - sin filtro                                 │
└─────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────┐
│ PASO 4: Llamar Mock API                                            │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────────────┐                                              │
│  │ MockAPIClient    │  ← Headers: janis-client: metro             │
│  │ (test_data/)     │  ← Endpoint: /order                         │
│  └──────────────────┘  ← Params: page=1, pageSize=100             │
│           │                                                         │
│           ↓                                                         │
│  ┌──────────────────┐                                              │
│  │ mock_orders_     │  ← Cargar datos desde JSON                  │
│  │ page1.json       │  → Retornar 2 órdenes (Metro)               │
│  └──────────────────┘                                              │
│                                                                     │
│  Respuesta:                                                         │
│  {                                                                  │
│    "data": [orden1, orden2],                                       │
│    "pagination": {                                                  │
│      "page": 1,                                                     │
│      "hasNextPage": true                                            │
│    }                                                                │
│  }                                                                  │
│                                                                     │
│  ✅ 2 registros obtenidos (página 1)                               │
└─────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────┐
│ PASO 5: Paginación                                                  │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  hasNextPage = true → Llamar página 2                              │
│                                                                     │
│  ┌──────────────────┐                                              │
│  │ MockAPIClient    │  ← Params: page=2                           │
│  └──────────────────┘                                              │
│           │                                                         │
│           ↓                                                         │
│  ┌──────────────────┐                                              │
│  │ mock_orders_     │  → Retornar [] (página vacía)               │
│  │ page1.json       │  → hasNextPage: false                       │
│  └──────────────────┘                                              │
│                                                                     │
│  ✅ Paginación completa - 2 registros totales                      │
└─────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────┐
│ PASO 6: Deduplicación                                              │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Registros originales: 2                                            │
│                                                                     │
│  ┌─────────────────────────────────────────────┐                  │
│  │ deduplicate_records(records)                │                  │
│  │  → Usar 'id' como key única                │                  │
│  │  → Remover duplicados                       │                  │
│  └─────────────────────────────────────────────┘                  │
│                                                                     │
│  Registros únicos: 2                                                │
│  Duplicados removidos: 0                                            │
│                                                                     │
│  ✅ Deduplicación completa                                         │
└─────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────┐
│ PASO 7: Validación de Datos (Task 7)                               │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────────────────────────────────────┐                  │
│  │ DataValidator(data_type="orders")           │                  │
│  │  → Cargar schema JSON                       │                  │
│  │  → Validar cada registro                    │                  │
│  │  → Generar métricas                         │                  │
│  └─────────────────────────────────────────────┘                  │
│                                                                     │
│  Métricas:                                                          │
│  - Total recibido: 2                                                │
│  - Registros válidos: 2                                             │
│  - Registros inválidos: 0                                           │
│  - Tasa de validación: 100%                                         │
│                                                                     │
│  ✅ Validación exitosa - 2/2 válidos                               │
└─────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────┐
│ PASO 8: Enriquecimiento de Datos (Task 8)                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Tipo: orders → Enriquecer con items                               │
│                                                                     │
│  ┌─────────────────────────────────────────────┐                  │
│  │ DataEnricher(client=api_client)             │                  │
│  │  → enrich_orders(records)                   │                  │
│  │  → Llamar /order/{id}/items para cada uno  │                  │
│  │  → Agregar items a cada orden              │                  │
│  └─────────────────────────────────────────────┘                  │
│                                                                     │
│  Resultado:                                                         │
│  - Exitosos: 2/2                                                    │
│  - Con errores: 0                                                   │
│                                                                     │
│  ✅ Enriquecimiento completo                                       │
└─────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────┐
│ PASO 9: Obtener Último Timestamp                                   │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Extraer timestamps de registros:                                   │
│  - orden1.dateModified: "2024-02-24T10:15:00.000Z"                 │
│  - orden2.dateModified: "2024-02-24T10:20:00.000Z"                 │
│                                                                     │
│  last_modified = max(timestamps)                                    │
│                = "2024-02-24T10:20:00.000Z"                        │
│                                                                     │
│  ✅ Último timestamp: 2024-02-24T10:20:00.000Z                     │
└─────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────┐
│ PASO 10: Liberar Lock y Actualizar Estado                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────────┐                                                  │
│  │  DynamoDB    │  ← UpdateItem(data_type="orders-metro")         │
│  │  Table       │  ← lock_acquired = false                        │
│  └──────────────┘  ← status = "completed"                         │
│                    ← last_modified_date = "2024-02-24T10:20:00Z"  │
│                    ← records_fetched = 2                           │
│                    ← last_successful_execution = now()             │
│                                                                     │
│  ✅ Lock liberado y estado actualizado                             │
└─────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────┐
│ RESULTADO FINAL                                                     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ✅ TEST COMPLETADO EXITOSAMENTE                                   │
│                                                                     │
│  📊 RESUMEN:                                                        │
│    - Cliente: metro                                                 │
│    - Endpoint: /order                                               │
│    - Registros obtenidos: 2                                         │
│    - Registros válidos: 2                                           │
│    - Tiempo total: 0.15s                                            │
│    - Lock liberado: ✓                                               │
│    - Estado en DynamoDB: ✓                                          │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 🔄 Test End-to-End - Flujo Multi-Tenant

```
┌─────────────────────────────────────────────────────────────────────┐
│                    TEST: test_end_to_end.py                         │
│                                                                     │
│  Prueba: 2 endpoints × 2 clientes = 4 llamadas                    │
│  Tiempo: 10-20 segundos                                            │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│ CONFIGURACIÓN                                                       │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Endpoints: ['orders', 'stock']                                     │
│  Clientes: ['metro', 'wongio']                                      │
│                                                                     │
│  Matriz de llamadas:                                                │
│  ┌──────────┬─────────┬──────────┐                                │
│  │ Endpoint │ Cliente │ Lock Key │                                │
│  ├──────────┼─────────┼──────────┤                                │
│  │ orders   │ metro   │ orders-metro   │                          │
│  │ orders   │ wongio  │ orders-wongio  │                          │
│  │ stock    │ metro   │ stock-metro    │                          │
│  │ stock    │ wongio  │ stock-wongio   │                          │
│  └──────────┴─────────┴──────────┘                                │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────┐
│ EJECUCIÓN SECUENCIAL                                                │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────────────────────────────────┐                      │
│  │ Llamada 1: orders + metro               │                      │
│  │  → poll_endpoint(...)                   │                      │
│  │  → Lock: orders-metro                   │                      │
│  │  → Mock: mock_orders_page1.json         │                      │
│  │  → Resultado: 2 registros               │                      │
│  │  ✅ Exitoso (0.25s)                     │                      │
│  └─────────────────────────────────────────┘                      │
│                    ↓                                                │
│  ┌─────────────────────────────────────────┐                      │
│  │ Llamada 2: orders + wongio              │                      │
│  │  → poll_endpoint(...)                   │                      │
│  │  → Lock: orders-wongio                  │                      │
│  │  → Mock: mock_orders_page2.json         │                      │
│  │  → Resultado: 1 registro                │                      │
│  │  ✅ Exitoso (0.28s)                     │                      │
│  └─────────────────────────────────────────┘                      │
│                    ↓                                                │
│  ┌─────────────────────────────────────────┐                      │
│  │ Llamada 3: stock + metro                │                      │
│  │  → poll_endpoint(...)                   │                      │
│  │  → Lock: stock-metro                    │                      │
│  │  → Mock: [] (sin datos)                 │                      │
│  │  → Resultado: 0 registros               │                      │
│  │  ✅ Exitoso (0.15s)                     │                      │
│  └─────────────────────────────────────────┘                      │
│                    ↓                                                │
│  ┌─────────────────────────────────────────┐                      │
│  │ Llamada 4: stock + wongio               │                      │
│  │  → poll_endpoint(...)                   │                      │
│  │  → Lock: stock-wongio                   │                      │
│  │  → Mock: [] (sin datos)                 │                      │
│  │  → Resultado: 0 registros               │                      │
│  │  ✅ Exitoso (0.18s)                     │                      │
│  └─────────────────────────────────────────┘                      │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────┐
│ AGREGACIÓN DE RESULTADOS                                            │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  📊 ESTADÍSTICAS GENERALES:                                         │
│    • Total de llamadas: 4                                           │
│    • Exitosas: 4                                                    │
│    • Fallidas: 0                                                    │
│    • Tiempo total: 1.2s                                             │
│                                                                     │
│  📈 DATOS PROCESADOS:                                               │
│    • Registros obtenidos: 3                                         │
│    • Registros válidos: 3                                           │
│    • Duplicados removidos: 0                                        │
│                                                                     │
│  ✅ LLAMADAS EXITOSAS:                                              │
│    • metro    | orders | /order      | 2 registros | 0.25s        │
│    • wongio   | orders | /order      | 1 registros | 0.28s        │
│    • metro    | stock  | /sku-stock  | 0 registros | 0.15s        │
│    • wongio   | stock  | /sku-stock  | 0 registros | 0.18s        │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────┐
│ VERIFICACIÓN EN DYNAMODB                                            │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Estado de locks en DynamoDB:                                       │
│                                                                     │
│  ┌────────────────┬──────────┬───────────┬──────────┐             │
│  │ Lock Key       │ Acquired │ Status    │ Records  │             │
│  ├────────────────┼──────────┼───────────┼──────────┤             │
│  │ orders-metro   │ false    │ completed │ 2        │             │
│  │ orders-wongio  │ false    │ completed │ 1        │             │
│  │ stock-metro    │ false    │ completed │ 0        │             │
│  │ stock-wongio   │ false    │ completed │ 0        │             │
│  └────────────────┴──────────┴───────────┴──────────┘             │
│                                                                     │
│  ✅ Todos los locks liberados correctamente                        │
│  ✅ Estados actualizados en DynamoDB                                │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────┐
│ RESULTADO FINAL                                                     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ✅ TEST EXITOSO - Todas las llamadas completadas (4/4)            │
│                                                                     │
│  Tasa de éxito: 100%                                                │
│  Tiempo total: 1.2s                                                 │
│  Registros procesados: 3                                            │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 🎭 Mock API - Flujo de Datos

```
┌─────────────────────────────────────────────────────────────────────┐
│                    MockJanisAPIClient                               │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ↓
┌─────────────────────────────────────────────────────────────────────┐
│ 1. Inicialización                                                   │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  MockJanisAPIClient(                                                │
│    base_url='https://mock.api.janis.in',                           │
│    api_key='mock-key',                                              │
│    extra_headers={                                                  │
│      'janis-client': 'metro'  ← Detectar cliente                   │
│    }                                                                │
│  )                                                                  │
│                                                                     │
│  ↓                                                                  │
│  Detectar cliente: 'metro'                                          │
│  Cargar archivo: 'mock_orders_page1.json'                          │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────┐
│ 2. Request GET                                                      │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  client.get('/order', params={'page': 1})                           │
│                                                                     │
│  ↓                                                                  │
│  Simular delay (10-50ms)                                            │
│  Determinar página: 1                                               │
│                                                                     │
│  ↓                                                                  │
│  if page == 1:                                                      │
│    return mock_data  ← Datos del JSON                              │
│  elif page == 2:                                                    │
│    return {"data": [], "pagination": {...}}  ← Página vacía        │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────┐
│ 3. Respuesta                                                        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  {                                                                  │
│    "data": [                                                        │
│      {                                                              │
│        "id": "mock001order123456789abc",                           │
│        "commerceId": "SLR-v11209818test-01",                       │
│        "status": "new",                                             │
│        "seller": {"name": "Metro"},                                 │
│        "account": {"name": "metro"},                                │
│        ...                                                          │
│      },                                                             │
│      {...}                                                          │
│    ],                                                               │
│    "pagination": {                                                  │
│      "page": 1,                                                     │
│      "pageSize": 100,                                               │
│      "totalPages": 2,                                               │
│      "hasNextPage": true                                            │
│    }                                                                │
│  }                                                                  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 🔀 Mapeo Cliente → Archivo JSON

```
┌──────────────────────────────────────────────────────────────────┐
│                    Cliente Detection                             │
└──────────────────────────────────────────────────────────────────┘
                           │
           ┌───────────────┼───────────────┐
           │               │               │
           ↓               ↓               ↓
    ┌──────────┐    ┌──────────┐    ┌──────────┐
    │  metro   │    │  wongio  │    │  otros   │
    └──────────┘    └──────────┘    └──────────┘
           │               │               │
           ↓               ↓               ↓
    ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
    │ mock_orders_ │ │ mock_orders_ │ │ mock_orders_ │
    │ page1.json   │ │ page2.json   │ │ page1.json   │
    │              │ │              │ │ (default)    │
    │ 2 órdenes    │ │ 1 orden      │ │              │
    │ Metro        │ │ Wongio       │ │              │
    └──────────────┘ └──────────────┘ └──────────────┘
```

---

## 📊 Componentes y Dependencias

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Arquitectura de Tests                            │
└─────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────┐
│                         Test Files                               │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  test_localstack_real_api.py          test_end_to_end.py        │
│           │                                    │                 │
│           └────────────────┬───────────────────┘                 │
│                            │                                     │
└────────────────────────────┼─────────────────────────────────────┘
                             │
                             ↓
┌──────────────────────────────────────────────────────────────────┐
│                      Core Components                             │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────┐  ┌──────────────────┐  ┌────────────────┐ │
│  │ StateManager    │  │ MockAPIClient    │  │ Pagination     │ │
│  │ (DynamoDB)      │  │ (test_data/)     │  │ Handler        │ │
│  └─────────────────┘  └──────────────────┘  └────────────────┘ │
│                                                                  │
│  ┌─────────────────┐  ┌──────────────────┐  ┌────────────────┐ │
│  │ Incremental     │  │ DataValidator    │  │ DataEnricher   │ │
│  │ Polling         │  │ (Task 7)         │  │ (Task 8)       │ │
│  └─────────────────┘  └──────────────────┘  └────────────────┘ │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
                             │
                             ↓
┌──────────────────────────────────────────────────────────────────┐
│                      Data Sources                                │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────┐  ┌──────────────────┐                    │
│  │ LocalStack       │  │ Mock JSON Files  │                    │
│  │ (DynamoDB)       │  │ (test_data/)     │                    │
│  │                  │  │                  │                    │
│  │ - polling_control│  │ - page1.json     │                    │
│  │   table          │  │ - page2.json     │                    │
│  └──────────────────┘  └──────────────────┘                    │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

---

**Última actualización:** Febrero 24, 2026  
**Autor:** Kiro AI Assistant
