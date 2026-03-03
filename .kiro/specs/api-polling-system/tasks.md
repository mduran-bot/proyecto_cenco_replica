# Plan de Implementación: Sistema de Polling de APIs

## Visión General

Este plan implementa un sistema de polling programado que consulta las 41 APIs de Janis usando EventBridge para scheduling y MWAA (Apache Airflow) para orquestación. El sistema utiliza DynamoDB para gestión de estado, implementa polling incremental con ventana de solapamiento, y entrega datos validados y enriquecidos.

## Tareas

- [x] 1. Configurar infraestructura base con Terraform
  - Crear módulo de Terraform para tabla DynamoDB de control
  - Crear módulo de Terraform para bucket S3 de staging
  - Crear módulo de Terraform para tópico SNS de errores
  - Crear módulo de Terraform para roles y políticas IAM
  - Configurar soporte para LocalStack con variables de entorno
  - _Requerimientos: 2.6, 3.1, 10.1, 10.2_

- [ ] 2. Implementar cliente de API con rate limiting
  - [x] 2.1 Crear clase JanisAPIClient con gestión de sesión
    - Implementar inicialización con base_url, api_key y rate_limit
    - Configurar sesión HTTP con retry strategy (3 intentos, backoff 2x)
    - Implementar método _create_session con HTTPAdapter
    - _Requerimientos: 5.1, 5.3, 5.4, 5.7_
  
  - [x] 2.2 Implementar rate limiting con sliding window
    - Crear método _enforce_rate_limit que rastrea timestamps de requests
    - Implementar lógica de sliding window (100 requests/minuto)
    - Agregar sleep cuando se alcanza el límite
    - _Requerimientos: 5.1, 5.2_
  
  - [ ]* 2.3 Escribir property test para rate limiting
    - **Propiedad 8: Rate Limiting de Requests**
    - **Valida: Requerimientos 5.1**
  
  - [ ]* 2.4 Escribir property test para reintentos
    - **Propiedad 9: Reintentos con Backoff Exponencial**
    - **Valida: Requerimientos 5.3, 5.4**

- [x] 3. Implementar manejador de paginación con circuit breaker
  - [x] 3.1 Crear clase PaginationHandler
    - Implementar método fetch_all_pages con iteración de páginas
    - Configurar tamaño de página en 100 registros
    - Implementar detección de hasNextPage
    - _Requerimientos: 6.1, 6.2_
  
  - [x] 3.2 Implementar circuit breaker
    - Agregar contador de páginas con límite de 1000
    - Lanzar CircuitBreakerException cuando se excede el límite
    - Registrar última página obtenida exitosamente
    - _Requerimientos: 6.3, 6.5_
  
  - [ ]* 3.3 Escribir property test para circuit breaker
    - **Propiedad 11: Circuit Breaker en Paginación**
    - **Valida: Requerimientos 6.3**
  
  - [ ]* 3.4 Escribir property test para tamaño de página
    - **Propiedad 10: Tamaño de Página Consistente**
    - **Valida: Requerimientos 6.1**

- [x] 4. Implementar gestión de estado con DynamoDB
  - [x] 4.1 Crear funciones de lock en DynamoDB
    - Implementar acquire_lock con conditional update
    - Implementar release_lock con actualización de timestamps
    - Manejar ConditionalCheckFailedException para locks existentes
    - _Requerimientos: 3.2, 3.3, 3.5, 3.6, 3.7_
  
  - [x] 4.2 Implementar funciones de consulta de estado
    - Crear get_control_item para leer estado actual
    - Crear update_last_modified para actualizar timestamp incremental
    - Implementar manejo de items inexistentes (primera ejecución)
    - _Requerimientos: 3.8, 4.3_
  
  - [ ]* 4.3 Escribir property tests para locks
    - **Propiedad 1: Adquisición de Lock Exitosa**
    - **Propiedad 2: Prevención de Ejecuciones Concurrentes**
    - **Propiedad 3: Actualización de Timestamp en Éxito**
    - **Propiedad 4: Liberación de Lock en Éxito**
    - **Propiedad 5: Liberación de Lock en Fallo Preservando Timestamp**
    - **Valida: Requerimientos 3.2, 3.3, 3.5, 3.6, 3.7**

- [ ] 5. Checkpoint - Verificar componentes base
  - Asegurar que todos los tests pasen, preguntar al usuario si surgen dudas.

- [x] 6. Implementar lógica de polling incremental
  - [x] 6.1 Crear función build_incremental_filter
    - Consultar DynamoDB para obtener last_modified_date
    - Restar 1 minuto para ventana de solapamiento
    - Construir filtro con dateModified, sortBy y sortOrder
    - Manejar caso de primera ejecución (full refresh)
    - _Requerimientos: 4.1, 4.2, 4.3_
  
  - [x] 6.2 Crear función deduplicate_records
    - Agrupar registros por ID
    - Comparar timestamps de modificación
    - Mantener registro con timestamp más reciente
    - _Requerimientos: 4.4_
  
  - [ ]* 6.3 Escribir property tests para polling incremental
    - **Propiedad 6: Filtro Incremental con Timestamp Previo**
    - **Propiedad 7: Deduplicación por ID y Timestamp**
    - **Valida: Requerimientos 4.1, 4.2, 4.4**

- [ ] 7. Implementar validador de datos
  - [x] 7.1 Crear clase DataValidator
    - Cargar esquemas JSON desde archivos de configuración
    - Implementar método validate_batch con jsonschema
    - Implementar detección de duplicados en lote
    - Implementar validación de reglas de negocio
    - _Requerimientos: 8.1, 8.2, 8.3, 8.4_
  
  - [x] 7.2 Crear esquemas JSON para las 5 entidades principales
    - Definir esquema para orders (campos obligatorios, tipos)
    - Definir esquema para products
    - Definir esquema para stock
    - Definir esquema para prices
    - Definir esquema para stores
    - _Requerimientos: 8.1_
  
  - [ ] 7.3 Escribir property tests para validación

    - **Propiedad 15: Validación de Esquema JSON**
    - **Propiedad 16: Detección de Duplicados en Lote**
    - **Propiedad 17: Validación de Reglas de Negocio**
    - **Valida: Requerimientos 8.1, 8.3, 8.4**

- [x] 8. Implementar enriquecedor de datos
  - [x] 8.1 Crear clase DataEnricher
    - Implementar método enrich_orders con ThreadPoolExecutor
    - Implementar método enrich_products con ThreadPoolExecutor
    - Configurar max_workers en 5 para paralelización
    - Implementar manejo de errores con _enrichment_complete flag
    - _Requerimientos: 7.1, 7.2, 7.3, 7.4_
  
  - [x] 8.2 Implementar métodos auxiliares de enriquecimiento
    - Crear _fetch_order_items para obtener items de órdenes
    - Crear _fetch_product_skus para obtener SKUs de productos
    - Agregar logging de errores de enriquecimiento
    - _Requerimientos: 7.1, 7.2, 7.4_
  
  - [ ]* 8.3 Escribir property tests para enriquecimiento
    - **Propiedad 12: Enriquecimiento de Órdenes**
    - **Propiedad 13: Enriquecimiento de Productos**
    - **Propiedad 14: Resiliencia en Enriquecimiento**
    - **Valida: Requerimientos 7.1, 7.2, 7.4**

- [x] 9. Checkpoint - Verificar componentes de procesamiento
  - Asegurar que todos los tests pasen, preguntar al usuario si surgen dudas.

- [x] 10. REFACTORIZAR DAGs de Airflow para polling multi-tenant (10 endpoints × 2 clientes)
  - [x] 10.1 MODIFICAR `max/polling/dags/base_polling_dag.py` para soportar multi-tenant
    - **ARCHIVO EXISTENTE:** `max/polling/dags/base_polling_dag.py`
    - **ACCIÓN:** Modificar función `create_polling_dag()` para:
      - Aceptar parámetros adicionales: `clients`, `endpoint`, `base_url`
      - Crear tasks dinámicamente para cada cliente usando loops
      - Pasar `client`, `endpoint`, `base_url` a cada task function
    - **CAMBIOS ESPECÍFICOS:**
      - Agregar parámetros: `clients: list`, `endpoint: str`, `base_url: str` a la función
      - Crear tasks dentro de loop: `for client in clients:`
      - Nombrar tasks con sufijo de cliente: `acquire_lock_{client}`, `poll_api_{client}`, etc.
      - Pasar `client` en `op_kwargs` de cada PythonOperator
    - _Requerimientos: 2.3, 3.2, 3.3, 3.5, 3.6_
  
  - [x] 10.2 ACTUALIZAR `max/polling/dags/poll_orders.py`
    - **ARCHIVO EXISTENTE:** `max/polling/dags/poll_orders.py`
    - **ACCIÓN:** Reemplazar llamada a `create_polling_dag()` con nuevos parámetros
    - **CAMBIOS ESPECÍFICOS:**
      ```python
      dag = create_polling_dag(
          dag_id='poll_orders',
          data_type='orders',
          clients=['metro', 'wongio'],
          endpoint='/order',
          base_url='https://oms.janis.in/api',
          tags=['polling', 'orders', 'high-frequency']
      )
      ```
    - _Requerimientos: 1.2_
  
  - [x] 10.3 ACTUALIZAR `max/polling/dags/poll_stock.py`
    - **ARCHIVO EXISTENTE:** `max/polling/dags/poll_stock.py`
    - **ACCIÓN:** Reemplazar llamada a `create_polling_dag()` con nuevos parámetros
    - **CAMBIOS ESPECÍFICOS:**
      ```python
      dag = create_polling_dag(
          dag_id='poll_stock',
          data_type='stock',
          clients=['metro', 'wongio'],
          endpoint='/sku-stock',
          base_url='https://wms.janis.in/api',
          tags=['polling', 'stock', 'medium-frequency']
      )
      ```
    - _Requerimientos: 1.4_
  
  - [x] 10.4 ACTUALIZAR `max/polling/dags/poll_prices.py`
    - **ARCHIVO EXISTENTE:** `max/polling/dags/poll_prices.py`
    - **ACCIÓN:** Modificar para manejar 3 endpoints × 2 clientes
    - **CAMBIOS ESPECÍFICOS:**
      - Cambiar a crear tasks manualmente (no usar factory) O
      - Modificar factory para aceptar múltiples endpoints
      - Endpoints: ['/price', '/price-sheet', '/base-price']
      - Base URL: 'https://vtex.pricing.janis.in/api'
      - Total: 6 llamadas (3 endpoints × 2 clientes)
    - _Requerimientos: 1.5_
  
  - [x] 10.5 RENOMBRAR Y ACTUALIZAR `max/polling/dags/poll_products.py` → `poll_catalog.py`
    - **ARCHIVO EXISTENTE:** `max/polling/dags/poll_products.py` (si existe)
    - **ACCIÓN:** Renombrar a `poll_catalog.py` y modificar para 4 endpoints × 2 clientes
    - **CAMBIOS ESPECÍFICOS:**
      - Renombrar archivo: `poll_products.py` → `poll_catalog.py`
      - Endpoints: ['/product', '/sku', '/category', '/brand']
      - Base URL: 'https://catalog.janis.in/api'
      - Total: 8 llamadas (4 endpoints × 2 clientes)
    - **NOTA:** Si no existe poll_products.py, crear poll_catalog.py desde cero
    - _Requerimientos: 1.3_
  
  - [x] 10.6 ACTUALIZAR `max/polling/dags/poll_stores.py`
    - **ARCHIVO EXISTENTE:** `max/polling/dags/poll_stores.py`
    - **ACCIÓN:** Reemplazar llamada a `create_polling_dag()` con nuevos parámetros
    - **CAMBIOS ESPECÍFICOS:**
      ```python
      dag = create_polling_dag(
          dag_id='poll_stores',
          data_type='stores',
          clients=['metro', 'wongio'],
          endpoint='/location',
          base_url='https://commerce.janis.in/api',
          tags=['polling', 'stores', 'daily']
      )
      ```
    - _Requerimientos: 1.6_
  
  - **ARCHIVOS A MODIFICAR:**
    - `max/polling/dags/base_polling_dag.py` (modificar factory function)
    - `max/polling/dags/poll_orders.py` (actualizar parámetros)
    - `max/polling/dags/poll_stock.py` (actualizar parámetros)
    - `max/polling/dags/poll_prices.py` (actualizar para múltiples endpoints)
    - `max/polling/dags/poll_products.py` (renombrar y actualizar)
    - `max/polling/dags/poll_stores.py` (actualizar parámetros)
  
  - **RESUMEN:** 5 DAGs que manejan 10 endpoints × 2 clientes = 20 llamadas de API por ciclo completo

- [x] 11. REFACTORIZAR funciones de task de Airflow con soporte multi-tenant
  - [x] 11.1 MODIFICAR `max/polling/src/airflow_tasks.py` - función `acquire_dynamodb_lock()`
    - **ARCHIVO EXISTENTE:** `max/polling/src/airflow_tasks.py`
    - **FUNCIÓN:** `acquire_dynamodb_lock(data_type: str, **context)`
    - **CAMBIOS REQUERIDOS:**
      - Agregar parámetro: `client: str`
      - Cambiar signature: `acquire_dynamodb_lock(data_type: str, client: str, **context)`
      - Modificar key de DynamoDB: `f"{data_type}-{client}"` en lugar de solo `data_type`
      - Modificar execution_id: `f"{data_type}-{client}-{timestamp}"`
      - Actualizar logs para incluir cliente
    - **LÍNEAS A MODIFICAR:** ~línea 80-130
    - _Requerimientos: 3.2, 3.3, 11.4_
  
  - [x] 11.2 MODIFICAR `max/polling/src/airflow_tasks.py` - función `poll_janis_api()`
    - **ARCHIVO EXISTENTE:** `max/polling/src/airflow_tasks.py`
    - **FUNCIÓN:** `poll_janis_api(data_type: str, **context)`
    - **CAMBIOS REQUERIDOS:**
      - Agregar parámetros: `client: str`, `endpoint: str`, `base_url: str`
      - Cambiar signature: `poll_janis_api(data_type: str, client: str, endpoint: str, base_url: str, **context)`
      - Modificar key de DynamoDB en `build_incremental_filter()`: `f"{data_type}-{client}"`
      - Usar `base_url` en lugar de variable de entorno genérica
      - Usar `endpoint` específico en lugar de `data_type`
    - **LÍNEAS A MODIFICAR:** ~línea 135-230
    - _Requerimientos: 4.1, 4.2, 4.4, 5.1, 6.1, 6.2_
  
  - [x] 11.2b MODIFICAR `max/polling/src/api_client.py` - clase `JanisAPIClient`
    - **ARCHIVO EXISTENTE:** `max/polling/src/api_client.py`
    - **CLASE:** `JanisAPIClient`
    - **CAMBIOS REQUERIDOS:**
      - Agregar método para configurar headers personalizados
      - Modificar método `request()` para incluir header `janis-client: {client}`
      - Agregar parámetro `client` al constructor o a cada request
    - **OPCIÓN 1:** Agregar `client` al constructor y configurar header permanente
    - **OPCIÓN 2:** Agregar parámetro `client` a método `request()` y configurar header dinámicamente
    - _Requerimientos: 5.1_
  
  - [x] 11.3 VERIFICAR `max/polling/src/airflow_tasks.py` - función `validate_data()`
    - **ARCHIVO EXISTENTE:** `max/polling/src/airflow_tasks.py`
    - **FUNCIÓN:** `validate_data(data_type: str, **context)`
    - **ACCIÓN:** Revisar código, probablemente NO necesita cambios
    - **VERIFICAR:** Que funcione correctamente con datos que vienen de XCom
    - **LÍNEAS A REVISAR:** ~línea 235-310
    - _Requerimientos: 8.1, 8.2, 8.3, 8.4, 8.5_
  
  - [x] 11.4 VERIFICAR `max/polling/src/airflow_tasks.py` - función `enrich_data()`
    - **ARCHIVO EXISTENTE:** `max/polling/src/airflow_tasks.py`
    - **FUNCIÓN:** `enrich_data(data_type: str, **context)`
    - **ACCIÓN:** Revisar código, probablemente NO necesita cambios
    - **VERIFICAR:** Que funcione correctamente con datos que vienen de XCom
    - **POSIBLE CAMBIO:** Si enriquecimiento requiere llamadas a API, agregar header `janis-client`
    - **LÍNEAS A REVISAR:** ~línea 315-420
    - _Requerimientos: 7.1, 7.2, 7.4, 7.5_
  
  - [x] 11.5 MODIFICAR `max/polling/src/airflow_tasks.py` - función `output_data()`
    - **ARCHIVO EXISTENTE:** `max/polling/src/airflow_tasks.py`
    - **FUNCIÓN:** `output_data(data_type: str, **context)`
    - **CAMBIOS REQUERIDOS:**
      - Agregar parámetro: `client: str`
      - Cambiar signature: `output_data(data_type: str, client: str, **context)`
      - Modificar path de S3: `f"bronze/{client}/{data_type}/timestamp.json"`
      - Agregar `client` a metadata: `output_record['_metadata']['client'] = client`
      - Actualizar logs para incluir cliente
    - **LÍNEAS A MODIFICAR:** ~línea 425-500
    - **NOTA:** Actualmente NO guarda en S3, solo prepara datos. Verificar si necesita implementar escritura a S3
    - _Requerimientos: 9.2, 9.4_
  
  - [x] 11.6 MODIFICAR `max/polling/src/airflow_tasks.py` - función `release_dynamodb_lock()`
    - **ARCHIVO EXISTENTE:** `max/polling/src/airflow_tasks.py`
    - **FUNCIÓN:** `release_dynamodb_lock(data_type: str, **context)`
    - **CAMBIOS REQUERIDOS:**
      - Agregar parámetro: `client: str`
      - Cambiar signature: `release_dynamodb_lock(data_type: str, client: str, **context)`
      - Modificar key de DynamoDB: `f"{data_type}-{client}"` en `release_lock()`
      - Agregar dimensión de cliente a métricas CloudWatch (si se implementan)
      - Actualizar logs para incluir cliente
    - **LÍNEAS A MODIFICAR:** ~línea 505-600
    - _Requerimientos: 3.5, 3.6, 3.7_
  
  - [x] 11.7 MODIFICAR `max/polling/src/state_manager.py` - métodos que usan data_type
    - **ARCHIVO EXISTENTE:** `max/polling/src/state_manager.py`
    - **CLASE:** `StateManager`
    - **CAMBIOS REQUERIDOS:**
      - **OPCIÓN 1 (Recomendada):** NO modificar StateManager, pasar key compuesta desde airflow_tasks
        - En airflow_tasks: `state_manager.acquire_lock(f"{data_type}-{client}", execution_id)`
      - **OPCIÓN 2:** Modificar todos los métodos para aceptar `client` como parámetro separado
        - Cambiar signatures de: `acquire_lock(data_type, ...)` a `acquire_lock(data_type, client, ...)`
        - Construir key internamente: `key = f"{data_type}-{client}"`
    - **RECOMENDACIÓN:** Usar OPCIÓN 1 para minimizar cambios
    - _Requerimientos: 3.2, 3.3, 3.5, 3.6, 3.7, 3.8_
  
  - [x] 11.8 MODIFICAR `max/polling/src/incremental_polling.py` - función `build_incremental_filter()`
    - **ARCHIVO EXISTENTE:** `max/polling/src/incremental_polling.py`
    - **FUNCIÓN:** `build_incremental_filter(state_manager, data_type)`
    - **CAMBIOS REQUERIDOS:**
      - **OPCIÓN 1 (Recomendada):** Cambiar parámetro `data_type` a `key`
        - Signature: `build_incremental_filter(state_manager, key: str)`
        - Llamar desde airflow_tasks: `build_incremental_filter(state_manager, f"{data_type}-{client}")`
      - **OPCIÓN 2:** Agregar parámetro `client`
        - Signature: `build_incremental_filter(state_manager, data_type, client)`
        - Construir key internamente: `key = f"{data_type}-{client}"`
    - **RECOMENDACIÓN:** Usar OPCIÓN 1 para minimizar cambios
    - _Requerimientos: 4.1, 4.2, 4.3_
  
  - **ARCHIVOS A MODIFICAR:**
    - `max/polling/src/airflow_tasks.py` (6 funciones)
    - `max/polling/src/api_client.py` (agregar soporte para header janis-client)
    - `max/polling/src/state_manager.py` (opcional, depende de enfoque)
    - `max/polling/src/incremental_polling.py` (opcional, depende de enfoque)
  
  - **ARCHIVOS QUE PROBABLEMENTE NO NECESITAN CAMBIOS:**
    - `max/polling/src/pagination_handler.py`
    - `max/polling/src/data_validator.py`
    - `max/polling/src/data_enricher.py`
  
  - **RESUMEN DE CAMBIOS:**
    - Todas las task functions principales reciben parámetro `client`
    - DynamoDB keys se construyen como: `f"{data_type}-{client}"`
    - S3 paths incluyen cliente: `bronze/{client}/{data_type}/`
    - API client incluye header: `janis-client: {client}`
    - Métricas incluyen dimensión de cliente

- [x] 12. REFACTORIZAR configuración de EventBridge para scheduling multi-tenant
  - [x] 12.1 VERIFICAR Y ACTUALIZAR módulo de Terraform para EventBridge
    - **ARCHIVOS A BUSCAR:**
      - `terraform/modules/eventbridge/main.tf` (si existe)
      - `terraform/modules/mwaa/main.tf` (puede contener reglas de EventBridge)
      - `max/polling/terraform/main.tf` (puede contener configuración local)
    - **ACCIÓN:** Localizar dónde están definidas las reglas de EventBridge actuales
    - **CAMBIOS REQUERIDOS:**
      - Definir 5 reglas con nombres descriptivos:
        - `poll-orders-schedule` → rate(5 minutes)
        - `poll-stock-schedule` → rate(10 minutes)
        - `poll-prices-schedule` → rate(30 minutes)
        - `poll-catalog-schedule` → rate(1 hour)
        - `poll-stores-schedule` → rate(1 day)
      - Cada regla debe tener target apuntando a MWAA environment
    - **NOTA:** Si no existen reglas de EventBridge, crearlas desde cero en módulo apropiado
    - _Requerimientos: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6_
  
  - [x] 12.2 CONFIGURAR targets de EventBridge con input JSON multi-tenant
    - **ARCHIVO:** Mismo archivo donde están las reglas (identificado en 12.1)
    - **CAMBIOS REQUERIDOS:** Para cada regla, configurar target con input JSON específico
    
    - **Target para poll-orders-schedule:**
      ```hcl
      target {
        arn      = aws_mwaa_environment.main.arn
        role_arn = aws_iam_role.eventbridge_mwaa.arn
        
        input = jsonencode({
          dag_id = "poll_orders"
          conf = {
            clients  = ["metro", "wongio"]
            endpoint = "/order"
            base_url = "https://oms.janis.in/api"
          }
        })
      }
      ```
    
    - **Target para poll-stock-schedule:**
      ```hcl
      target {
        arn      = aws_mwaa_environment.main.arn
        role_arn = aws_iam_role.eventbridge_mwaa.arn
        
        input = jsonencode({
          dag_id = "poll_stock"
          conf = {
            clients  = ["metro", "wongio"]
            endpoint = "/sku-stock"
            base_url = "https://wms.janis.in/api"
          }
        })
      }
      ```
    
    - **Target para poll-prices-schedule:**
      ```hcl
      target {
        arn      = aws_mwaa_environment.main.arn
        role_arn = aws_iam_role.eventbridge_mwaa.arn
        
        input = jsonencode({
          dag_id = "poll_prices"
          conf = {
            clients   = ["metro", "wongio"]
            endpoints = ["/price", "/price-sheet", "/base-price"]
            base_url  = "https://vtex.pricing.janis.in/api"
          }
        })
      }
      ```
    
    - **Target para poll-catalog-schedule:**
      ```hcl
      target {
        arn      = aws_mwaa_environment.main.arn
        role_arn = aws_iam_role.eventbridge_mwaa.arn
        
        input = jsonencode({
          dag_id = "poll_catalog"
          conf = {
            clients   = ["metro", "wongio"]
            endpoints = ["/product", "/sku", "/category", "/brand"]
            base_url  = "https://catalog.janis.in/api"
          }
        })
      }
      ```
    
    - **Target para poll-stores-schedule:**
      ```hcl
      target {
        arn      = aws_mwaa_environment.main.arn
        role_arn = aws_iam_role.eventbridge_mwaa.arn
        
        input = jsonencode({
          dag_id = "poll_stores"
          conf = {
            clients  = ["metro", "wongio"]
            endpoint = "/location"
            base_url = "https://commerce.janis.in/api"
          }
        })
      }
      ```
    
    - _Requerimientos: 1.7_
  
  - [x] 12.3 VERIFICAR IAM role para EventBridge → MWAA
    - **ARCHIVO A BUSCAR:** 
      - `terraform/modules/eventbridge/iam.tf` (si existe)
      - `terraform/modules/mwaa/iam.tf` (puede contener el role)
    - **ACCIÓN:** Verificar que existe IAM role con permisos para invocar MWAA
    - **PERMISOS REQUERIDOS:**
      ```hcl
      {
        "Effect": "Allow",
        "Action": [
          "airflow:CreateCliToken"
        ],
        "Resource": "arn:aws:airflow:*:*:environment/*"
      }
      ```
    - **NOTA:** Si no existe, crear IAM role con trust policy para EventBridge
  
  - **ARCHIVOS POTENCIALES A MODIFICAR:**
    - `terraform/modules/eventbridge/main.tf` (reglas y targets)
    - `terraform/modules/eventbridge/iam.tf` (IAM role)
    - `terraform/modules/mwaa/main.tf` (si EventBridge está aquí)
    - `max/polling/terraform/main.tf` (configuración local para testing)
  
  - **NOTA:** Cada trigger ejecutará el DAG una vez, pero el DAG internamente iterará sobre clientes

- [x] 13. Checkpoint - Verificar integración completa
  - Asegurar que todos los tests pasen, preguntar al usuario si surgen dudas.

- [x] 13.5 ACTUALIZAR/ELIMINAR documentación obsoleta
  - [x] 13.5.1 ACTUALIZAR `max/polling/dags/README.md`
    - **ARCHIVO EXISTENTE:** `max/polling/dags/README.md`
    - **CAMBIOS REQUERIDOS:**
      - Actualizar sección "Available DAGs" para reflejar:
        - 10 endpoints específicos (no 5 categorías genéricas)
        - Multi-tenant con Metro y Wongio
        - Renombrar poll_products.py → poll_catalog.py
        - Agregar información de múltiples endpoints para prices y catalog
      - Actualizar sección "Event-Driven Execution" con ejemplos de input JSON multi-tenant
      - Actualizar sección "Configuration" con nuevas variables de entorno (si aplica)
      - Actualizar ejemplos de EventBridge con input JSON que incluye clients, endpoint, base_url
  
  - [x] 13.5.2 ACTUALIZAR O ELIMINAR `max/polling/dags/IMPLEMENTATION_SUMMARY.md`
    - **ARCHIVO EXISTENTE:** `max/polling/dags/IMPLEMENTATION_SUMMARY.md`
    - **OPCIÓN 1 (Recomendada):** ELIMINAR archivo porque está desactualizado
      - El archivo documenta implementación anterior sin multi-tenant
      - Marca Task 10 como completada cuando ahora está pendiente
      - Puede causar confusión
    - **OPCIÓN 2:** Actualizar completamente para reflejar:
      - Estado actual: Task 10 pendiente de refactorización
      - Cambios multi-tenant requeridos
      - 10 endpoints × 2 clientes = 20 llamadas
  
  - [x] 13.5.3 ACTUALIZAR `max/polling/src/README.md`
    - **ARCHIVO EXISTENTE:** `max/polling/src/README.md`
    - **CAMBIOS REQUERIDOS:**
      - Agregar sección sobre soporte multi-tenant en JanisAPIClient
      - Documentar header `janis-client` requerido
      - Actualizar ejemplos de uso para incluir cliente
      - Actualizar sección "Integración con MWAA" con ejemplos multi-tenant
      - Actualizar "Próximos Pasos" para reflejar estado actual
  
  - **RECOMENDACIÓN:** Eliminar IMPLEMENTATION_SUMMARY.md y actualizar los otros dos READMEs

- [ ] 14. Implementar manejo de errores y notificaciones
  - [ ] 14.1 Crear función notify_error
    - Publicar mensaje a tópico SNS con detalles de error
    - Incluir data_type, execution_id, error_type, error_message
    - _Requerimientos: 11.2_
  
  - [ ] 14.2 Crear clase StructuredLogger
    - Implementar logging estructurado con JSON
    - Incluir execution_id, data_type, timestamp en cada log
    - Configurar niveles de log apropiados
    - _Requerimientos: 11.1_
  
  - [ ] 14.3 Agregar manejo de errores a funciones de task
    - Envolver cada función de task con try-except
    - Llamar a notify_error en caso de excepción
    - Asegurar que release_lock se ejecute siempre (trigger_rule='all_done')
    - _Requerimientos: 11.1, 11.2, 11.3_
  
  - [ ]* 14.4 Escribir property test para idempotencia
    - **Propiedad 19: Idempotencia de Operaciones**
    - **Valida: Requerimientos 11.3**

- [ ] 15. Implementar soporte para LocalStack
  - [ ] 15.1 Crear configuración de docker-compose
    - Definir servicio localstack con servicios necesarios
    - Configurar puertos y volúmenes
    - _Requerimientos: 10.4_
  
  - [ ] 15.2 Crear script de inicialización de LocalStack
    - Crear tabla DynamoDB en LocalStack
    - Crear bucket S3 en LocalStack
    - Crear tópico SNS en LocalStack
    - _Requerimientos: 10.3, 10.4_
  
  - [ ] 15.3 Agregar detección de entorno LocalStack
    - Leer variable LOCALSTACK_ENDPOINT
    - Configurar clientes AWS con endpoint de LocalStack
    - Usar credenciales dummy cuando LOCALSTACK_ENDPOINT está configurado
    - _Requerimientos: 10.1, 10.2_

- [ ] 16. Implementar monitoreo y métricas
  - [ ] 16.1 Crear función emit_metrics
    - Publicar métricas personalizadas a CloudWatch
    - Incluir RecordsFetched, ValidationPassRate, ExecutionDuration
    - Agregar dimensión DataType para filtrado
    - _Requerimientos: 8.5_
  
  - [ ] 16.2 Agregar emisión de métricas a release_lock
    - Calcular duración de ejecución
    - Obtener métricas de validación
    - Llamar a emit_metrics con todas las métricas
    - _Requerimientos: 8.5_

- [x] 17. Crear tests de integración con LocalStack
  - [x]* 17.1 Escribir test end-to-end del flujo de polling
    - Configurar LocalStack con testcontainers
    - Crear tabla DynamoDB y bucket S3
    - Ejecutar DAG completo
    - Verificar lock liberado y datos escritos
    - _Requerimientos: 10.3, 10.4, 10.5_
  
  - [x]* 17.2 Escribir tests de integración para cada componente
    - Test de cliente API con mock server
    - Test de paginación con respuestas simuladas
    - Test de validación con datos de prueba
    - Test de enriquecimiento con datos de prueba

- [x] 18. Crear documentación y configuración
  - [x] 18.1 Crear archivo requirements.txt para Airflow
    - Listar dependencias: boto3, requests, jsonschema, hypothesis
    - Especificar versiones compatibles con Python 3.11
    - _Requerimientos: 2.2_
    - **COMPLETADO**: requirements.txt ya existe con todas las dependencias
  
  - [x] 18.2 Crear archivo .env.example
    - Documentar variables de entorno necesarias
    - Incluir ejemplos para LocalStack y AWS
    - _Requerimientos: 10.1, 10.2_
    - **COMPLETADO**: .env.example ya existe con documentación completa
  
  - [x] 18.3 Crear documentación completa del sistema
    - Documentar arquitectura y componentes
    - Incluir instrucciones de setup local con LocalStack
    - Documentar proceso de deployment a AWS
    - Incluir ejemplos de uso y troubleshooting
    - **COMPLETADO**: 3 documentos creados en DocumentacionProd/
      - 01-SISTEMA_API_POLLING.md - Arquitectura y componentes
      - 02-GUIA_TESTS.md - Tests y validación
      - 03-CONFIGURACION_PRODUCCION.md - Deployment a producción

- [x] 19. Checkpoint final - Verificar sistema completo
  - Asegurar que todos los tests pasen, preguntar al usuario si surgen dudas.

## Notas

- Las tareas marcadas con `*` son opcionales y pueden omitirse para un MVP más rápido
- Cada tarea referencia requerimientos específicos para trazabilidad
- Los checkpoints aseguran validación incremental
- Los property tests validan propiedades de correctitud universales
- Los unit tests validan ejemplos específicos y casos edge
- El sistema está diseñado para ser testeable localmente con LocalStack antes del deployment a AWS

## CAMBIOS MULTI-TENANT - RESUMEN EJECUTIVO

### Contexto
El sistema fue implementado inicialmente para 5 entidades genéricas (orders, products, stock, prices, stores). Ahora se requiere:
- **10 endpoints específicos** de Janis API (no 5 categorías genéricas)
- **Multi-tenant**: 2 clientes activos (Metro y Wongio)
- **Total de llamadas**: 10 endpoints × 2 clientes = 20 llamadas por ciclo

### Archivos a Modificar (Tasks 10-12)
1. **DAGs** (`max/polling/dags/`):
   - `base_polling_dag.py` - Agregar soporte multi-tenant
   - `poll_orders.py` - Configurar endpoint específico
   - `poll_stock.py` - Configurar endpoint específico
   - `poll_prices.py` - Manejar 3 endpoints × 2 clientes
   - `poll_products.py` → `poll_catalog.py` - Renombrar y configurar 4 endpoints × 2 clientes
   - `poll_stores.py` - Configurar endpoint específico

2. **Task Functions** (`max/polling/src/`):
   - `airflow_tasks.py` - 6 funciones necesitan parámetro `client`
   - `api_client.py` - Agregar header `janis-client`
   - `state_manager.py` - Usar keys compuestas (opcional)
   - `incremental_polling.py` - Usar keys compuestas (opcional)

3. **Terraform** (ubicación a determinar):
   - Módulo EventBridge - 5 reglas con input JSON multi-tenant
   - IAM roles - Permisos EventBridge → MWAA

4. **Documentación** (`max/polling/`):
   - `dags/README.md` - Actualizar con info multi-tenant
   - `dags/IMPLEMENTATION_SUMMARY.md` - ELIMINAR (obsoleto)
   - `src/README.md` - Actualizar con ejemplos multi-tenant

### Cambios Clave
- **DynamoDB keys**: `{data_type}-{client}` (ej: `orders-metro`)
- **S3 paths**: `bronze/{client}/{data_type}/` (ej: `bronze/metro/orders/`)
- **HTTP headers**: `janis-client: metro` o `janis-client: wongio`
- **Métricas**: Dimensión `Client=metro` o `Client=wongio`

### Mapeo: Tablas → APIs
- **Órdenes** (13 tablas) → 1 endpoint: GET /order @ oms.janis.in
- **Productos** (4 tablas) → 4 endpoints: GET /product, /sku, /category, /brand @ catalog.janis.in
- **Tiendas** (1 tabla) → 1 endpoint: GET /location @ commerce.janis.in
- **Stock** (1 tabla) → 1 endpoint: GET /sku-stock @ wms.janis.in
- **Precios** (3 tablas) → 3 endpoints: GET /price, /price-sheet, /base-price @ vtex.pricing.janis.in
