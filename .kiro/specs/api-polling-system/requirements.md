# Documento de Requerimientos: Sistema de Polling de APIs

## Introducción

El Sistema de Polling de APIs es una solución de ingesta de datos programada que consulta periódicamente las APIs de Janis para recuperar datos operacionales (órdenes, productos, stock, precios, tiendas). El sistema utiliza Amazon EventBridge para programación inteligente y Amazon MWAA (Apache Airflow) para orquestación de flujos de trabajo, asegurando sincronización de datos confiable e incremental con el Data Lake de Cencosud.

Este sistema opera independientemente de la ingesta basada en webhooks, proporcionando una red de seguridad para la sincronización de datos y soportando escenarios donde los webhooks en tiempo real no están disponibles o han fallado.

## Glosario

- **MWAA**: Amazon Managed Workflows for Apache Airflow - servicio de orquestación administrado
- **EventBridge**: Servicio AWS para programación y enrutamiento basado en eventos
- **DAG**: Directed Acyclic Graph - definición de flujo de trabajo de Airflow
- **S3_Bronze**: Capa Bronze del Data Lake donde se almacenan datos crudos en formato JSON (manejado por ETL posterior)
- **Tabla_Control_DynamoDB**: Tabla que almacena estado de ejecución y bloqueos para trabajos de polling
- **Polling_Incremental**: Obtención solo de registros nuevos o modificados desde la última ejecución
- **Limitador_Tasa**: Componente que aplica tasa máxima de solicitudes a API
- **Circuit_Breaker**: Patrón para prevenir bucles infinitos de paginación
- **Enriquecimiento_Datos**: Proceso de obtener entidades relacionadas para completar registros de datos
- **LocalStack**: Emulador local de nube AWS para pruebas

## Requerimientos

### Requerimiento 1: Configuración de Programación con EventBridge

**Historia de Usuario:** Como ingeniero de datos, quiero que EventBridge dispare DAGs de polling en intervalos apropiados, para que los requisitos de frescura de datos se cumplan sin sobrecargar MWAA.

#### Criterios de Aceptación

1. CUANDO EventBridge está configurado, EL Sistema DEBERÁ crear reglas programadas para cinco tipos de datos con intervalos específicos
2. EL Sistema DEBERÁ disparar el DAG de órdenes cada 5 minutos
3. EL Sistema DEBERÁ disparar el DAG de productos cada 1 hora
4. EL Sistema DEBERÁ disparar el DAG de stock cada 10 minutos
5. EL Sistema DEBERÁ disparar el DAG de precios cada 30 minutos
6. EL Sistema DEBERÁ disparar el DAG de tiendas cada 24 horas
7. CUANDO una regla programada se dispara, EL Sistema DEBERÁ invocar el DAG correspondiente de MWAA vía API
8. DONDE se usa LocalStack, EL Sistema DEBERÁ configurar reglas de EventBridge compatibles con LocalStack

### Requerimiento 2: Configuración del Entorno MWAA

**Historia de Usuario:** Como ingeniero de plataforma, quiero MWAA configurado para ejecución basada en eventos, para que los DAGs se ejecuten solo cuando son disparados por EventBridge.

#### Criterios de Aceptación

1. EL Sistema DEBERÁ desplegar MWAA con Apache Airflow versión 2.7.2
2. EL Sistema DEBERÁ configurar MWAA con runtime Python 3.11
3. CUANDO se definen DAGs, EL Sistema DEBERÁ establecer schedule_interval en None para ejecución basada en eventos
4. EL Sistema DEBERÁ configurar el entorno MWAA con mínimo 1 worker y máximo 3 workers
5. EL Sistema DEBERÁ almacenar archivos DAG en bucket S3 accesible por MWAA
6. EL Sistema DEBERÁ configurar MWAA con roles IAM apropiados para acceso a DynamoDB, S3 y CloudWatch
7. DONDE se usa LocalStack, EL Sistema DEBERÁ configurar MWAA para conectarse a endpoints de LocalStack

### Requerimiento 3: Gestión de Estado con DynamoDB

**Historia de Usuario:** Como ingeniero de datos, quiero que el estado de ejecución se rastree en DynamoDB, para que el polling sea incremental y se prevengan ejecuciones concurrentes.

#### Criterios de Aceptación

1. EL Sistema DEBERÁ crear una tabla DynamoDB con clave de partición data_type
2. CUANDO un DAG inicia, EL Sistema DEBERÁ intentar adquirir un bloqueo en la Tabla_Control_DynamoDB
3. SI ya existe un bloqueo para el tipo de dato, ENTONCES EL Sistema DEBERÁ omitir la ejecución y registrar una advertencia
4. CUANDO se adquiere un bloqueo, EL Sistema DEBERÁ registrar el timestamp de inicio de ejecución
5. CUANDO el polling se completa exitosamente, EL Sistema DEBERÁ actualizar el timestamp last_successful_execution
6. CUANDO el polling se completa exitosamente, EL Sistema DEBERÁ liberar el bloqueo
7. SI un DAG falla, ENTONCES EL Sistema DEBERÁ liberar el bloqueo y preservar el timestamp last_successful_execution anterior
8. EL Sistema DEBERÁ almacenar last_modified_date para consultas de polling incremental
9. CUANDO se solicita un refresh completo, EL Sistema DEBERÁ ignorar last_modified_date y obtener todos los registros

### Requerimiento 4: Lógica de Polling Incremental

**Historia de Usuario:** Como ingeniero de datos, quiero obtener solo registros nuevos o modificados, para que la carga de API se minimice y la transferencia de datos sea eficiente.

#### Criterios de Aceptación

1. CUANDO se consultan las APIs de Janis, EL Sistema DEBERÁ usar filtro dateModified con valor de last_successful_execution
2. EL Sistema DEBERÁ restar 1 minuto de last_successful_execution para crear ventana de solapamiento
3. CUANDO no existe ejecución previa, EL Sistema DEBERÁ realizar refresh completo sin filtro dateModified
4. CUANDO se detectan registros duplicados en ventana de solapamiento, EL Sistema DEBERÁ deduplicar basado en ID de entidad y timestamp de modificación
5. EL Sistema DEBERÁ incluir dateModified en orden ascendente en consultas API

### Requerimiento 5: Cliente API con Limitación de Tasa

**Historia de Usuario:** Como administrador de sistemas, quiero solicitudes API limitadas en tasa, para que la infraestructura de Janis no se sobrecargue.

#### Criterios de Aceptación

1. EL Limitador_Tasa DEBERÁ aplicar máximo 100 solicitudes por minuto a APIs de Janis
2. CUANDO se aproxima el límite de tasa, EL Limitador_Tasa DEBERÁ retrasar solicitudes para mantenerse dentro del límite
3. CUANDO una solicitud API falla con HTTP 429, EL Sistema DEBERÁ implementar reintento con backoff exponencial
4. EL Sistema DEBERÁ reintentar solicitudes fallidas hasta 3 veces con retrasos de 2, 4 y 8 segundos
5. CUANDO una solicitud API falla con HTTP 5xx, EL Sistema DEBERÁ reintentar con backoff exponencial
6. CUANDO una solicitud API falla con HTTP 4xx (excepto 429), EL Sistema DEBERÁ registrar error y omitir reintento
7. EL Sistema DEBERÁ incluir timeout de solicitud de 30 segundos para todas las llamadas API

### Requerimiento 6: Manejo de Paginación

**Historia de Usuario:** Como ingeniero de datos, quiero respuestas API grandes paginadas de forma segura, para que la memoria no se agote y se prevengan bucles infinitos.

#### Criterios de Aceptación

1. CUANDO se consultan APIs de Janis, EL Sistema DEBERÁ usar tamaño de página de 100 registros
2. EL Sistema DEBERÁ seguir enlaces de paginación hasta que no existan más páginas
3. CUANDO la paginación excede 1000 páginas, EL Circuit_Breaker DEBERÁ detener la obtención y generar una alerta
4. EL Sistema DEBERÁ rastrear número de página actual y total de registros obtenidos
5. CUANDO la paginación se interrumpe, EL Sistema DEBERÁ registrar la última página obtenida exitosamente

### Requerimiento 7: Enriquecimiento de Datos

**Historia de Usuario:** Como analista de datos, quiero entidades relacionadas obtenidas automáticamente, para que datos completos estén disponibles para análisis.

#### Criterios de Aceptación

1. CUANDO se obtienen órdenes, EL Sistema DEBERÁ recuperar items de orden para cada orden
2. CUANDO se obtienen productos, EL Sistema DEBERÁ recuperar detalles de SKU para cada producto
3. EL Sistema DEBERÁ usar ThreadPoolExecutor con máximo 5 hilos concurrentes para enriquecimiento paralelo
4. CUANDO el enriquecimiento falla para una entidad relacionada, EL Sistema DEBERÁ registrar el error y continuar con datos parciales
5. EL Sistema DEBERÁ incluir metadata de enriquecimiento indicando completitud de entidades relacionadas

### Requerimiento 8: Validación de Datos

**Historia de Usuario:** Como ingeniero de calidad de datos, quiero datos validados antes de la entrega, para que sistemas downstream reciban datos limpios.

#### Criterios de Aceptación

1. CUANDO se obtienen datos, EL Sistema DEBERÁ validar contra esquemas JSON predefinidos
2. CUANDO la validación de esquema falla, EL Sistema DEBERÁ registrar el registro inválido y excluirlo de la entrega
3. EL Sistema DEBERÁ detectar duplicados basados en ID de entidad dentro del mismo lote
4. EL Sistema DEBERÁ validar reglas de negocio como cantidades no negativas y formatos de fecha válidos
5. EL Sistema DEBERÁ calcular métricas de calidad de datos incluyendo tasa de aprobación de validación y conteo de duplicados

### Requerimiento 9: Almacenamiento Temporal de Datos

**Historia de Usuario:** Como ingeniero de datos, quiero datos validados almacenados temporalmente, para que estén disponibles para procesamiento posterior.

#### Criterios de Aceptación

1. CUANDO los datos están validados, EL Sistema DEBERÁ escribir registros en formato JSON
2. EL Sistema DEBERÁ agregar metadata de polling a cada registro incluyendo execution_id, poll_timestamp y data_type
3. EL Sistema DEBERÁ retornar los datos obtenidos para procesamiento downstream
4. EL Sistema DEBERÁ registrar total de registros procesados exitosamente

### Requerimiento 10: Compatibilidad con LocalStack

**Historia de Usuario:** Como desarrollador, quiero probar el sistema localmente con LocalStack, para que pueda validar funcionalidad antes del despliegue en AWS.

#### Criterios de Aceptación

1. EL Sistema DEBERÁ soportar variable de entorno LOCALSTACK_ENDPOINT para endpoints de servicio
2. CUANDO LOCALSTACK_ENDPOINT está configurado, EL Sistema DEBERÁ configurar todos los clientes AWS para usar LocalStack
3. EL Sistema DEBERÁ funcionar con servicios de LocalStack: EventBridge, DynamoDB, S3 y CloudWatch
4. EL Sistema DEBERÁ incluir configuración docker-compose para setup de LocalStack
5. EL Sistema DEBERÁ proporcionar scripts de prueba que se ejecuten contra LocalStack

### Requerimiento 11: Manejo de Errores y Recuperación

**Historia de Usuario:** Como operador de sistemas, quiero manejo de errores comprensivo, para que los fallos se registren y la recuperación sea automática cuando sea posible.

#### Criterios de Aceptación

1. CUANDO cualquier componente falla, EL Sistema DEBERÁ registrar información detallada de error incluyendo stack trace
2. CUANDO un DAG falla, EL Sistema DEBERÁ enviar notificación vía tópico SNS
3. EL Sistema DEBERÁ implementar operaciones idempotentes para soportar reintentos seguros
4. CUANDO no se puede adquirir bloqueo de DynamoDB, EL Sistema DEBERÁ salir graciosamente sin error
5. CUANDO la API es inalcanzable, EL Sistema DEBERÁ reintentar con backoff exponencial antes de fallar
