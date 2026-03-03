# Requirements Document: ETL Pipeline Expansion for 41 Janis APIs

## Introduction

Este documento define los requisitos para expandir el pipeline ETL existente (Bronze→Silver→Gold) para procesar 41 tipos de entidades de Janis Commerce y generar 26 tablas finales en la capa Gold/Redshift. El sistema actual procesa solo 1 tipo de dato (ventas) y debe expandirse para manejar todas las entidades del ecosistema Janis. El alcance se limita exclusivamente a AWS Glue Jobs de transformación, asumiendo que los datos JSON ya están disponibles en la capa Bronze.

## Glossary

- **Bronze_Layer**: Capa de almacenamiento raw en S3 que contiene datos JSON sin procesar de 41 tipos de entidades, organizados por cliente (metro/wongio) y con particionamiento temporal (year/month/day/hour). Estructura: `s3://data-lake-bronze/{client}/{entity_type}/year=.../month=.../day=.../hour=.../*.json`
- **Silver_Layer**: Capa intermedia de transformación que aplica limpieza, deduplicación, conversión de tipos y normalización a los datos Bronze. Mantiene separación por cliente con tablas: `silver.{client}_{entity_type}_clean`
- **Gold_Layer**: Capa final con 26 tablas en formato Apache Iceberg optimizadas para consultas analíticas en Redshift. Mantiene separación por cliente con tablas: `gold.{client}_{table_name}`
- **Client**: Identificador del tenant (metro o wongio) que determina la segregación de datos en las tres capas del Data Lake
- **Glue_Job**: Script PySpark ejecutado en AWS Glue que transforma datos entre capas del Data Lake
- **Glue_Catalog**: Metastore de AWS Glue que almacena definiciones de esquemas y tablas para las tres capas
- **Iceberg_Table**: Tabla en formato Apache Iceberg que soporta ACID transactions, time travel y schema evolution
- **Entity_Type**: Tipo de dato de Janis (orders, products, skus, etc.) que corresponde a un prefijo en Bronze
- **Data_Gap**: Campo requerido por BI que no está disponible en las APIs de Janis y requiere manejo especial
- **Type_Conversion**: Transformación de tipos de datos MySQL (BIGINT, TINYINT, DECIMAL) a tipos Redshift (TIMESTAMP, BOOLEAN, NUMERIC)
- **Calculated_Field**: Campo derivado que se calcula a partir de otros campos (ej: total_changes = amount - originalAmount)
- **LocalStack**: Emulador local de servicios AWS usado para desarrollo y testing del pipeline
- **Partitioning_Strategy**: Estrategia de organización de datos en S3 usando claves de partición (year, month, day, hour)
- **Deduplication_Logic**: Lógica para eliminar registros duplicados basada en claves primarias y timestamps
- **Schema_Mapping**: Mapeo entre estructura JSON de Bronze y esquema tabular de Gold según documento de análisis

## Requirements

### Requirement 1: Expansión de Glue Jobs Bronze-to-Silver para 41 Entidades Multi-Tenant

**User Story:** Como ingeniero de datos, quiero Glue Jobs que transformen los 41 tipos de entidades desde Bronze a Silver manteniendo separación por cliente (metro/wongio), para que los datos raw se limpien y normalicen antes de llegar a Gold.

#### Acceptance Criteria

1. THE Glue_Job SHALL procesar 41 Entity_Type distintos desde Bronze_Layer a Silver_Layer (orders, order-items, products, skus, categories, brands, stores, customers, stock, prices, promotional-prices, promotions, carriers, shipping, delivery-planning, delivery-ranges, payments, invoices, picking-sessions, picking-round-orders, order-status-changes, custom-data-fields, weighables, admins, comments, y 15 tipos adicionales)
2. THE Glue_Job SHALL procesar datos de ambos clientes (metro y wongio) manteniendo separación completa: input desde `s3://data-lake-bronze/{client}/{entity_type}/` y output a tabla `silver.{client}_{entity_type}_clean`
3. WHEN un Glue_Job procesa datos Bronze THEN THE Silver_Layer SHALL aplicar Deduplication_Logic basada en claves primarias (id, order_id, sku_id según Entity_Type)
4. WHEN se detectan registros duplicados THEN THE Glue_Job SHALL retener el registro con timestamp más reciente (date_modified o date_created)
5. THE Glue_Job SHALL aplicar Type_Conversion de tipos MySQL a tipos compatibles con Redshift (BIGINT timestamp → TIMESTAMP, TINYINT(1) → BOOLEAN, DECIMAL(12,9) → NUMERIC)
6. THE Glue_Job SHALL validar que campos obligatorios no sean NULL antes de escribir en Silver_Layer
7. WHEN un campo obligatorio es NULL THEN THE Glue_Job SHALL registrar el error en CloudWatch Logs y mover el registro a una tabla de errores
8. THE Glue_Job SHALL aceptar parámetros CLI: `--client` (metro o wongio) y `--entity-type` (orders, products, etc.)

### Requirement 2: Creación de 26 Tablas Iceberg en Gold Layer Multi-Tenant

**User Story:** Como analista de BI, quiero 26 tablas Iceberg en Gold_Layer con esquemas optimizados y separación por cliente (metro/wongio), para que pueda consultar datos desde Redshift con alto rendimiento y consistencia.

#### Acceptance Criteria

1. THE Glue_Catalog SHALL definir 26 Iceberg_Table en Gold_Layer por cada cliente (52 tablas totales): `gold.metro_wms_orders`, `gold.wongio_wms_orders`, `gold.metro_products`, `gold.wongio_products`, etc. (wms_orders, wms_order_items, wms_order_shipping, wms_logistic_carriers, wms_order_item_weighables, wms_order_status_changes, wms_stores, wms_logistic_delivery_planning, wms_logistic_delivery_ranges, wms_order_payments, wms_order_payments_connector_responses, wms_order_custom_data_fields, products, skus, categories, admins, price, brands, customers, wms_order_picking, picking_round_orders, stock, promotional_prices, promotions, invoices, ff_comments)
2. THE Iceberg_Table SHALL usar formato Parquet con compresión Snappy para optimizar almacenamiento y consultas
3. THE Iceberg_Table SHALL implementar particionamiento por fecha (year, month, day) para tablas transaccionales (orders, payments, invoices)
4. THE Iceberg_Table SHALL implementar particionamiento por store_id para tablas de inventario (stock, prices)
5. THE Iceberg_Table SHALL NO usar particionamiento para tablas maestras pequeñas (categories, brands, carriers)
6. THE Glue_Catalog SHALL registrar esquemas de Iceberg_Table con tipos de datos Redshift-compatible (TIMESTAMP, BOOLEAN, VARCHAR, NUMERIC, BIGINT)
7. THE Glue_Job SHALL aceptar parámetros CLI: `--client` (metro o wongio) y `--gold-table` (wms_orders, products, etc.)

### Requirement 3: Transformaciones de Conversión de Tipos

**User Story:** Como ingeniero de datos, quiero que los Glue Jobs conviertan tipos de datos MySQL a tipos Redshift, para que las tablas Gold sean compatibles con las consultas de BI existentes.

#### Acceptance Criteria

1. WHEN un campo es BIGINT timestamp Unix THEN THE Glue_Job SHALL convertirlo a TIMESTAMP ISO 8601 (ej: 1706025600 → 2024-01-23T12:00:00Z)
2. WHEN un campo es TINYINT(1) THEN THE Glue_Job SHALL convertirlo a BOOLEAN (0 → false, 1 → true)
3. WHEN un campo es DECIMAL(12,9) para coordenadas THEN THE Glue_Job SHALL convertirlo a NUMERIC(12,9) preservando precisión
4. WHEN un campo es VARCHAR con valores numéricos THEN THE Glue_Job SHALL mantenerlo como VARCHAR sin conversión
5. WHEN un campo es INT representando IDs THEN THE Glue_Job SHALL convertirlo a BIGINT para compatibilidad con Redshift
6. THE Glue_Job SHALL registrar en logs cualquier conversión que falle con el valor original y tipo esperado

### Requirement 4: Implementación de Campos Calculados

**User Story:** Como analista de BI, quiero que los Glue Jobs calculen campos derivados automáticamente, para que no tenga que replicar lógica de negocio en mis consultas SQL.

#### Acceptance Criteria

1. WHEN se procesa wms_orders THEN THE Glue_Job SHALL calcular total_changes = totals.items.amount - totals.items.originalAmount
2. WHEN se procesa wms_order_picking THEN THE Glue_Job SHALL calcular total_time = (endPickingTime - startPickingTime) / 1000
3. WHEN se procesa admins THEN THE Glue_Job SHALL calcular username = firstName + " " + lastName
4. WHEN se procesa wms_order_items THEN THE Glue_Job SHALL calcular quantity_difference = quantity_picked - quantity si ambos campos existen
5. THE Glue_Job SHALL validar que los campos fuente existan antes de calcular Calculated_Field
6. WHEN un campo fuente es NULL THEN THE Glue_Job SHALL asignar NULL al Calculated_Field sin generar error

### Requirement 5: Manejo de Data Gaps Críticos

**User Story:** Como ingeniero de datos, quiero que el sistema maneje Data_Gap identificados en el análisis, para que los reportes de BI no fallen por campos faltantes.

#### Acceptance Criteria

1. WHEN un Data_Gap crítico no está disponible en la API THEN THE Glue_Job SHALL asignar NULL al campo en Gold_Layer
2. THE Glue_Job SHALL registrar en CloudWatch Logs cada Data_Gap encontrado con Entity_Type, campo faltante y order_id/record_id
3. THE Glue_Job SHALL crear una tabla de auditoría data_gaps_log en Silver_Layer con columnas (entity_type, field_name, record_id, timestamp)
4. WHEN se procesa wms_orders THEN THE Glue_Job SHALL manejar Data_Gap para items_substituted_qty, items_qty_missing, points_card, status_vtex
5. WHEN se procesa wms_logistic_delivery_planning THEN THE Glue_Job SHALL manejar Data_Gap para dynamic_quota, carrier, quota, offset_start, edited
6. THE Glue_Job SHALL generar un reporte diario con conteo de Data_Gap por Entity_Type y campo

### Requirement 6: Glue Jobs Silver-to-Gold con Schema Mapping Multi-Tenant

**User Story:** Como ingeniero de datos, quiero Glue Jobs que transformen datos Silver a Gold aplicando Schema_Mapping y manteniendo separación por cliente, para que las tablas finales coincidan con el esquema esperado por BI.

#### Acceptance Criteria

1. THE Glue_Job SHALL aplicar Schema_Mapping según documento "Análisis y Mapeo de Datos Cencosud Janis.md" para cada una de las 26 tablas Gold
2. THE Glue_Job SHALL leer datos desde tablas Silver específicas del cliente: `silver.{client}_{entity_type}_clean` y escribir a tablas Gold específicas del cliente: `gold.{client}_{table_name}`
3. WHEN se mapea wms_orders THEN THE Glue_Job SHALL extraer 43 campos de 91 disponibles según mapeo documentado
4. WHEN se mapea wms_order_items THEN THE Glue_Job SHALL extraer 18 campos de 43 disponibles según mapeo documentado
5. WHEN se mapea products THEN THE Glue_Job SHALL extraer 20 campos de 40 disponibles según mapeo documentado
6. THE Glue_Job SHALL renombrar campos según Schema_Mapping (ej: dateCreated → date_created, firstName → first_name)
7. THE Glue_Job SHALL aplanar estructuras JSON anidadas (ej: addresses[0].city → city, totals.items.amount → items_amount)

### Requirement 7: Procesamiento de Estructuras JSON Anidadas

**User Story:** Como ingeniero de datos, quiero que los Glue Jobs aplanar estructuras JSON complejas, para que las tablas Gold sean relacionales y consultables desde Redshift.

#### Acceptance Criteria

1. WHEN un campo es un array JSON THEN THE Glue_Job SHALL crear registros separados en tabla hija (ej: order.items[] → wms_order_items con order_id como FK)
2. WHEN un campo es un objeto JSON anidado THEN THE Glue_Job SHALL aplanar campos con prefijo (ej: totals.items.amount → totals_items_amount)
3. WHEN se procesa wms_order_shipping THEN THE Glue_Job SHALL extraer addresses[0].city, addresses[0].neighborhood, addresses[0].lat, addresses[0].lng como columnas separadas
4. WHEN se procesa wms_order_payments_connector_responses THEN THE Glue_Job SHALL convertir objeto JSON connectorResponse en registros key-value (field, value)
5. WHEN se procesa wms_order_custom_data_fields THEN THE Glue_Job SHALL convertir objeto JSON customData en registros key-value (field, value)
6. THE Glue_Job SHALL preservar relaciones padre-hijo usando claves foráneas (order_id, payment_id, session_id)

### Requirement 8: Estrategia de Particionamiento para Tablas Gold

**User Story:** Como ingeniero de datos, quiero que las tablas Gold usen Partitioning_Strategy optimizada, para que las consultas de BI sean rápidas y eficientes.

#### Acceptance Criteria

1. THE Iceberg_Table para wms_orders, wms_order_items, wms_order_payments, invoices SHALL usar particionamiento por (year, month, day) basado en date_created
2. THE Iceberg_Table para stock, price, promotional_prices SHALL usar particionamiento por store_id
3. THE Iceberg_Table para wms_order_picking, picking_round_orders SHALL usar particionamiento por (year, month, day) basado en pick_start_time
4. THE Iceberg_Table para categories, brands, carriers, admins SHALL NO usar particionamiento (tablas maestras pequeñas)
5. THE Glue_Job SHALL escribir datos en particiones usando INSERT OVERWRITE para tablas maestras y APPEND para tablas transaccionales
6. THE Glue_Job SHALL compactar particiones pequeñas automáticamente cuando superen 100 archivos

### Requirement 9: Configuración de Glue Jobs en LocalStack

**User Story:** Como desarrollador, quiero que los Glue Jobs funcionen en LocalStack, para que pueda desarrollar y probar el pipeline localmente sin costos de AWS.

#### Acceptance Criteria

1. THE Glue_Job SHALL usar variables de entorno para configurar endpoints de S3, Glue Catalog y Redshift (permitir override para LocalStack)
2. THE Glue_Job SHALL funcionar con URLs de LocalStack (http://localhost:4566) en lugar de endpoints reales de AWS
3. THE Glue_Job SHALL usar credenciales dummy (test/test) cuando se ejecuta en LocalStack
4. THE Glue_Job SHALL detectar entorno LocalStack mediante variable AWS_ENDPOINT_URL y ajustar configuración automáticamente
5. THE Glue_Job SHALL usar formato Iceberg REST Catalog para LocalStack en lugar de AWS Glue Catalog nativo
6. THE Glue_Job SHALL registrar en logs el entorno detectado (LocalStack vs AWS) al iniciar ejecución

### Requirement 10: Orquestación de Glue Jobs con Step Functions Multi-Tenant

**User Story:** Como ingeniero de datos, quiero que los Glue Jobs se ejecuten en secuencia correcta para ambos clientes (metro y wongio), para que las dependencias entre capas se respeten y los datos fluyan correctamente.

#### Acceptance Criteria

1. THE Step_Functions SHALL orquestar ejecución de Glue Jobs en tres fases: Bronze-to-Silver (paralelo), Silver-to-Gold (paralelo por dominio), Validación (secuencial)
2. WHEN se ejecuta fase Bronze-to-Silver THEN THE Step_Functions SHALL ejecutar 82 Glue Jobs en paralelo (41 Entity_Type × 2 clientes)
3. WHEN se ejecuta fase Silver-to-Gold THEN THE Step_Functions SHALL ejecutar 52 Glue Jobs agrupados por dominio y cliente (26 tablas × 2 clientes)
4. THE Step_Functions SHALL procesar metro y wongio en paralelo para maximizar throughput
5. WHEN un Glue_Job falla THEN THE Step_Functions SHALL reintentar hasta 3 veces con backoff exponencial (1min, 2min, 4min)
6. WHEN un Glue_Job falla después de 3 reintentos THEN THE Step_Functions SHALL marcar el job como fallido y continuar con otros jobs independientes
7. THE Step_Functions SHALL enviar notificación SNS cuando un job falle definitivamente con detalles de error, Entity_Type y Client afectado

### Requirement 11: Monitoreo y Logging de Transformaciones

**User Story:** Como ingeniero de operaciones, quiero logs detallados de cada transformación, para que pueda diagnosticar problemas y monitorear el volumen de datos procesados.

#### Acceptance Criteria

1. THE Glue_Job SHALL registrar en CloudWatch Logs métricas de inicio: Entity_Type, timestamp, particiones a procesar, registros estimados
2. THE Glue_Job SHALL registrar en CloudWatch Logs métricas de finalización: registros leídos, registros escritos, registros con errores, duración, memoria usada
3. THE Glue_Job SHALL registrar en CloudWatch Logs cada Type_Conversion aplicada con conteo de registros afectados
4. THE Glue_Job SHALL registrar en CloudWatch Logs cada Data_Gap encontrado con Entity_Type, campo, y conteo de registros afectados
5. THE Glue_Job SHALL generar métricas custom en CloudWatch: RecordsProcessed, RecordsWithErrors, DataGapsFound, ProcessingDuration por Entity_Type
6. THE Glue_Job SHALL crear alarmas CloudWatch cuando tasa de errores supere 5% o cuando Data_Gap afecte más de 10% de registros

### Requirement 12: Validación de Calidad de Datos en Gold

**User Story:** Como analista de BI, quiero que el sistema valide calidad de datos en Gold, para que pueda confiar en la integridad de los reportes.

#### Acceptance Criteria

1. THE Glue_Job SHALL validar que claves primarias sean únicas en cada Iceberg_Table (id, order_id, sku_id según tabla)
2. THE Glue_Job SHALL validar que claves foráneas existan en tablas padre (order_id en wms_order_items debe existir en wms_orders)
3. THE Glue_Job SHALL validar rangos de valores para campos numéricos (quantity >= 0, price >= 0, lat entre -90 y 90)
4. THE Glue_Job SHALL validar formatos de campos (email con @, phone con dígitos, timestamps válidos)
5. WHEN una validación falla THEN THE Glue_Job SHALL registrar el error en tabla data_quality_issues con (table_name, record_id, validation_rule, error_message, timestamp)
6. THE Glue_Job SHALL generar reporte diario de calidad con conteo de issues por tabla y tipo de validación

### Requirement 13: Manejo de Schema Evolution en Iceberg

**User Story:** Como ingeniero de datos, quiero que las tablas Iceberg soporten schema evolution, para que pueda agregar campos nuevos sin romper el pipeline existente.

#### Acceptance Criteria

1. THE Iceberg_Table SHALL soportar agregar columnas nuevas sin reescribir datos existentes (ADD COLUMN)
2. THE Iceberg_Table SHALL soportar renombrar columnas preservando datos (RENAME COLUMN)
3. THE Iceberg_Table SHALL soportar cambiar tipo de columna cuando sea compatible (INT → BIGINT, VARCHAR(50) → VARCHAR(100))
4. WHEN se detecta un campo nuevo en Bronze THEN THE Glue_Job SHALL agregar la columna automáticamente a Silver y Gold con valor NULL para registros históricos
5. WHEN se detecta un cambio de tipo incompatible THEN THE Glue_Job SHALL registrar error y mantener tipo original
6. THE Glue_Job SHALL registrar en tabla schema_changes_log cada evolución de esquema con (table_name, change_type, column_name, old_type, new_type, timestamp)
7. THE System SHALL validar cambios de esquema antes de aplicarlos verificando compatibilidad con datos existentes
8. THE System SHALL enviar alerta a data engineers cuando se detecte cambio de esquema que requiere intervención manual
9. THE System SHALL proporcionar capacidad de rollback a versión anterior de esquema sin pérdida de datos
10. THE System SHALL mantener historial completo de cambios de esquema con timestamps y usuario responsable

### Requirement 14: Optimización de Performance

**User Story:** Como ingeniero de performance, quiero que las transformaciones se ejecuten de manera eficiente, para que el pipeline complete dentro de las ventanas de tiempo asignadas y minimice costos.

#### Acceptance Criteria

1. THE System SHALL procesar mínimo 100,000 registros por minuto para transformaciones Bronze-to-Silver estándar
2. THE System SHALL procesar mínimo 50,000 registros por minuto para transformaciones Silver-to-Gold con agregaciones
3. THE Glue_Job SHALL usar columnar processing optimizations en Spark para mejorar rendimiento
4. THE Glue_Job SHALL implementar predicate pushdown para minimizar data movement desde S3
5. THE Glue_Job SHALL usar broadcast joins para tablas de dimensiones pequeñas (< 100 MB)
6. THE Glue_Job SHALL particionar procesamiento por date ranges para habilitar paralelización
7. THE Glue_Job SHALL implementar checkpointing cada 10,000 registros para transformaciones de larga duración
8. THE Glue_Job SHALL optimizar Iceberg file layouts mediante compactación automática cuando particiones superen 100 archivos pequeños
9. THE Glue_Job SHALL usar auto-scaling de workers basado en volumen de datos (2-10 workers)
10. THE Glue_Job SHALL registrar métricas de performance (throughput, latency, resource utilization) en CloudWatch

### Requirement 15: Data Lineage y Trazabilidad

**User Story:** Como auditor de datos, quiero rastrear el linaje completo de los datos, para que pueda entender el origen y transformaciones aplicadas a cualquier registro.

#### Acceptance Criteria

1. THE System SHALL mantener linaje completo de datos desde Bronze hasta Gold layer para cada registro
2. THE System SHALL registrar metadata de transformación incluyendo: source file locations, transformation rules applied, job execution details, data quality results
3. THE System SHALL habilitar tracing de registros individuales a través de todas las etapas de transformación usando correlation IDs
4. THE System SHALL crear tabla lineage_metadata en Silver layer con columnas: lineage_id, source_layer, source_table, source_file_path, target_layer, target_table, transformation_job_id, transformation_timestamp, records_processed
5. THE System SHALL mantener audit logs de todas las modificaciones de datos con timestamps y job IDs
6. THE System SHALL proporcionar API para consultar linaje de datos por table_name, record_id, o date_range
7. THE System SHALL generar reportes de linaje en formato JSON para integración con herramientas de governance
8. THE System SHALL preservar linaje durante operaciones de deduplicación registrando qué registros fueron merged
9. THE System SHALL incluir en metadata de linaje: data quality scores, records failed, records deduplicated, processing duration
10. THE System SHALL retener metadata de linaje por mínimo 90 días para auditoría y compliance
