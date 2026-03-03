# Documento de Requisitos: Pipeline ETL Bronze-to-Silver

## Introducción

Este documento especifica los requisitos para implementar un pipeline de transformación de datos ETL Bronze-to-Silver usando Python/PySpark con AWS Glue y Apache Iceberg. El sistema procesará datos raw en formato JSON desde el bucket Bronze de S3, aplicará transformaciones de conversión de tipos, limpieza, normalización y deduplicación, y escribirá los datos transformados en tablas Apache Iceberg en el bucket Silver.

El pipeline se ejecutará en LocalStack para desarrollo local y constará de 8 módulos de transformación que trabajarán en secuencia.

## Glosario

- **Bronze_Layer**: Capa de almacenamiento S3 que contiene datos raw sin procesar en formato JSON
- **Silver_Layer**: Capa de almacenamiento S3 que contiene datos transformados y limpios en formato Apache Iceberg
- **DataTypeConverter**: Módulo que convierte tipos de datos de MySQL a tipos compatibles con Redshift
- **DataNormalizer**: Módulo que estandariza formatos de emails, teléfonos y fechas
- **DataCleaner**: Módulo que elimina espacios, maneja valores nulos y corrige encodings
- **JSONFlattener**: Módulo que convierte estructuras JSON anidadas en formato tabular plano
- **IcebergTableManager**: Módulo que gestiona la creación y mantenimiento de tablas Apache Iceberg
- **IcebergWriter**: Módulo que escribe datos transformados en tablas Iceberg
- **DuplicateDetector**: Módulo que identifica registros duplicados basándose en claves de negocio
- **ConflictResolver**: Módulo que resuelve conflictos cuando existen datos contradictorios
- **DataGapHandler**: Módulo que maneja la ausencia de información en campos críticos
- **ETL_Pipeline**: Sistema completo que orquesta todos los módulos de transformación
- **PySpark_DataFrame**: Estructura de datos distribuida utilizada para procesamiento
- **LocalStack**: Emulador local de servicios AWS para desarrollo

## Requisitos

### Requisito 1: Conversión de Tipos de Datos MySQL a Redshift

**Historia de Usuario:** Como ingeniero de datos, quiero convertir automáticamente los tipos de datos de MySQL a tipos compatibles con Redshift, para que los datos puedan ser cargados correctamente en el data warehouse.

#### Criterios de Aceptación

1. CUANDO el DataTypeConverter recibe un PySpark_DataFrame con columnas de tipo IntegerType, THE DataTypeConverter DEBERÁ mantener el tipo IntegerType
2. CUANDO el DataTypeConverter recibe un PySpark_DataFrame con columnas de tipo LongType, THE DataTypeConverter DEBERÁ mantener el tipo LongType
3. CUANDO el DataTypeConverter recibe un PySpark_DataFrame con columnas de tipo FloatType, THE DataTypeConverter DEBERÁ mantener el tipo FloatType
4. CUANDO el DataTypeConverter recibe un PySpark_DataFrame con columnas de tipo DoubleType, THE DataTypeConverter DEBERÁ mantener el tipo DoubleType
5. CUANDO el DataTypeConverter recibe un PySpark_DataFrame con columnas de tipo StringType que representan valores booleanos, THE DataTypeConverter DEBERÁ convertirlas a BooleanType
6. CUANDO el DataTypeConverter recibe un PySpark_DataFrame con columnas de tipo StringType que representan fechas, THE DataTypeConverter DEBERÁ convertirlas a DateType
7. CUANDO el DataTypeConverter recibe un PySpark_DataFrame con columnas de tipo StringType que representan timestamps, THE DataTypeConverter DEBERÁ convertirlas a TimestampType
8. CUANDO el DataTypeConverter recibe un PySpark_DataFrame con columnas de tipo StringType que representan decimales, THE DataTypeConverter DEBERÁ convertirlas a DecimalType(18,2)

### Requisito 2: Limpieza de Datos

**Historia de Usuario:** Como ingeniero de datos, quiero limpiar datos raw eliminando espacios en blanco, manejando nulos y corrigiendo problemas de encoding, para que la calidad de los datos mejore antes del almacenamiento.

#### Criterios de Aceptación

1. CUANDO el DataCleaner recibe un PySpark_DataFrame con columnas de tipo string, THE DataCleaner DEBERÁ eliminar espacios en blanco al inicio y al final de todos los valores string
2. CUANDO el DataCleaner recibe un PySpark_DataFrame con valores de string vacíos, THE DataCleaner DEBERÁ convertir strings vacíos a valores null
3. CUANDO el DataCleaner recibe un PySpark_DataFrame con problemas de encoding, THE DataCleaner DEBERÁ detectar y corregir errores de encoding UTF-8
4. CUANDO el DataCleaner recibe un PySpark_DataFrame con valores null en columnas no críticas, THE DataCleaner DEBERÁ preservar esos valores null
5. CUANDO el DataCleaner procesa un DataFrame, THE DataCleaner DEBERÁ mantener el orden original de las columnas en el DataFrame de salida

### Requisito 3: Normalización de Datos

**Historia de Usuario:** Como ingeniero de datos, quiero normalizar formatos de datos basándome en mapeos configurables de columnas, para que los sistemas downstream puedan consumir datos consistentes y estandarizados.

#### Criterios de Aceptación

1. CUANDO el DataNormalizer recibe un PySpark_DataFrame y una configuración que especifica columnas de email, THE DataNormalizer DEBERÁ convertir todas las direcciones de email en esas columnas a minúsculas
2. CUANDO el DataNormalizer recibe un PySpark_DataFrame y una configuración que especifica columnas de teléfono, THE DataNormalizer DEBERÁ eliminar todos los caracteres no numéricos de los números de teléfono en esas columnas
3. CUANDO el DataNormalizer recibe un PySpark_DataFrame y una configuración que especifica columnas de fecha, THE DataNormalizer DEBERÁ parsear y estandarizar los formatos de fecha a un formato consistente
4. CUANDO el DataNormalizer recibe un PySpark_DataFrame y una configuración que especifica columnas de timestamp, THE DataNormalizer DEBERÁ parsear y estandarizar los formatos de timestamp a un formato consistente
5. CUANDO el DataNormalizer procesa cualquier columna, THE DataNormalizer DEBERÁ preservar valores null sin convertirlos a strings o valores vacíos

### Requisito 4: Aplanamiento de JSON

**Historia de Usuario:** Como ingeniero de datos, quiero aplanar estructuras JSON anidadas en formato tabular, para que los datos puedan ser almacenados en formatos columnares como Apache Iceberg.

#### Criterios de Aceptación

1. CUANDO el JSONFlattener recibe un PySpark_DataFrame con columnas de tipo struct anidadas, THE JSONFlattener DEBERÁ aplanar todos los campos anidados usando notación de punto (ej: "address.city")
2. CUANDO el JSONFlattener recibe un PySpark_DataFrame con columnas de tipo array, THE JSONFlattener DEBERÁ explotar los arrays en filas separadas
3. CUANDO el JSONFlattener recibe un PySpark_DataFrame con estructuras profundamente anidadas (3+ niveles), THE JSONFlattener DEBERÁ aplanar recursivamente todos los niveles
4. CUANDO el JSONFlattener encuentra colisiones de nombres de campos durante el aplanamiento, THE JSONFlattener DEBERÁ agregar un sufijo numérico para asegurar unicidad
5. CUANDO el JSONFlattener procesa un DataFrame sin estructuras anidadas, THE JSONFlattener DEBERÁ retornar el DataFrame sin cambios

### Requisito 5: Gestión de Tablas Iceberg

**Historia de Usuario:** Como ingeniero de datos, quiero gestionar tablas Apache Iceberg programáticamente, para poder crear, actualizar y mantener esquemas de tablas en la capa Silver.

#### Criterios de Aceptación

1. CUANDO el IcebergTableManager recibe una solicitud de creación de tabla con un esquema, THE IcebergTableManager DEBERÁ crear una nueva tabla Iceberg en el bucket Silver_Layer
2. CUANDO el IcebergTableManager recibe una solicitud para verificar si una tabla existe, THE IcebergTableManager DEBERÁ retornar true si la tabla existe y false en caso contrario
3. CUANDO el IcebergTableManager recibe una solicitud de actualización de esquema para una tabla existente, THE IcebergTableManager DEBERÁ evolucionar el esquema de la tabla para agregar nuevas columnas
4. CUANDO el IcebergTableManager recibe una solicitud para crear una tabla que ya existe, THE IcebergTableManager DEBERÁ omitir la creación y retornar la referencia de la tabla existente
5. CUANDO el IcebergTableManager crea una tabla, THE IcebergTableManager DEBERÁ configurar la tabla con particionamiento por columna de fecha si se especifica

### Requisito 6: Escritura de Datos en Iceberg

**Historia de Usuario:** Como ingeniero de datos, quiero escribir datos transformados en tablas Iceberg, para que los datos sean almacenados en un formato eficiente y consultable en la capa Silver.

#### Criterios de Aceptación

1. CUANDO el IcebergWriter recibe un PySpark_DataFrame y un nombre de tabla, THE IcebergWriter DEBERÁ escribir los datos en la tabla Iceberg especificada
2. CUANDO el IcebergWriter escribe datos en una tabla existente, THE IcebergWriter DEBERÁ agregar nuevos registros sin sobrescribir datos existentes
3. CUANDO el IcebergWriter escribe datos con un esquema que no coincide, THE IcebergWriter DEBERÁ activar la evolución de esquema a través del IcebergTableManager
4. CUANDO el IcebergWriter completa una operación de escritura, THE IcebergWriter DEBERÁ retornar el número de registros escritos
5. CUANDO el IcebergWriter encuentra un fallo en la escritura, THE IcebergWriter DEBERÁ hacer rollback de la transacción y preservar la integridad de los datos

### Requisito 7: Detección de Duplicados

**Historia de Usuario:** Como ingeniero de datos, quiero detectar registros duplicados basándome en claves de negocio, para poder identificar y manejar datos redundantes antes del almacenamiento.

#### Criterios de Aceptación

1. CUANDO el DuplicateDetector recibe un PySpark_DataFrame y una lista de columnas clave, THE DuplicateDetector DEBERÁ identificar todos los registros duplicados basándose en esas claves
2. CUANDO el DuplicateDetector encuentra duplicados, THE DuplicateDetector DEBERÁ agregar una columna booleana "is_duplicate" marcando los registros duplicados como true
3. CUANDO el DuplicateDetector encuentra duplicados, THE DuplicateDetector DEBERÁ agregar una columna "duplicate_group_id" con el mismo valor para todos los registros en un grupo de duplicados
4. CUANDO el DuplicateDetector recibe un DataFrame sin duplicados, THE DuplicateDetector DEBERÁ marcar todos los registros con is_duplicate como false
5. CUANDO el DuplicateDetector procesa registros, THE DuplicateDetector DEBERÁ preservar todas las columnas originales en el DataFrame de salida

### Requisito 8: Resolución de Conflictos

**Historia de Usuario:** Como ingeniero de datos, quiero resolver conflictos cuando registros duplicados tienen valores contradictorios, para que solo los datos más precisos o recientes sean retenidos.

#### Criterios de Aceptación

1. CUANDO el ConflictResolver recibe registros duplicados con valores diferentes, THE ConflictResolver DEBERÁ seleccionar el registro con el timestamp más reciente
2. CUANDO el ConflictResolver recibe registros duplicados con timestamps idénticos, THE ConflictResolver DEBERÁ seleccionar el registro con menos valores null
3. CUANDO el ConflictResolver recibe registros duplicados con timestamps idénticos y conteos de null idénticos, THE ConflictResolver DEBERÁ seleccionar el primer registro encontrado
4. CUANDO el ConflictResolver resuelve conflictos, THE ConflictResolver DEBERÁ eliminar las columnas "is_duplicate" y "duplicate_group_id" del output
5. CUANDO el ConflictResolver procesa un DataFrame sin duplicados, THE ConflictResolver DEBERÁ retornar el DataFrame sin cambios

### Requisito 9: Manejo de Brechas de Datos

**Historia de Usuario:** Como ingeniero de datos, quiero manejar datos faltantes en campos críticos, para que registros incompletos puedan ser marcados o rellenados con valores por defecto.

#### Criterios de Aceptación

1. CUANDO el DataGapHandler recibe un PySpark_DataFrame y una lista de columnas críticas, THE DataGapHandler DEBERÁ identificar registros con valores null en esas columnas
2. CUANDO el DataGapHandler encuentra valores null en columnas críticas, THE DataGapHandler DEBERÁ agregar una columna booleana "has_critical_gaps" marcando esos registros como true
3. CUANDO el DataGapHandler recibe una configuración con valores por defecto, THE DataGapHandler DEBERÁ rellenar valores null en columnas especificadas con los valores por defecto proporcionados
4. CUANDO el DataGapHandler recibe una configuración para rechazar registros incompletos, THE DataGapHandler DEBERÁ filtrar registros con brechas críticas
5. CUANDO el DataGapHandler procesa registros sin brechas críticas, THE DataGapHandler DEBERÁ marcar has_critical_gaps como false

### Requisito 10: Orquestación del Pipeline

**Historia de Usuario:** Como ingeniero de datos, quiero orquestar todos los módulos de transformación en un único job de AWS Glue, para que los datos fluyan desde Bronze a Silver a través de todas las transformaciones necesarias.

#### Criterios de Aceptación

1. CUANDO el ETL_Pipeline inicia, THE ETL_Pipeline DEBERÁ leer datos JSON desde el bucket Bronze_Layer de S3 usando PySpark
2. CUANDO el ETL_Pipeline procesa datos, THE ETL_Pipeline DEBERÁ ejecutar módulos en este orden: JSONFlattener, DataCleaner, DataNormalizer, DataTypeConverter, DuplicateDetector, ConflictResolver, DataGapHandler, IcebergWriter
3. CUANDO el ETL_Pipeline completa exitosamente, THE ETL_Pipeline DEBERÁ registrar el número de registros procesados en cada etapa en CloudWatch
4. CUANDO el ETL_Pipeline encuentra un error en cualquier módulo, THE ETL_Pipeline DEBERÁ registrar los detalles del error en CloudWatch y detener la ejecución
5. CUANDO el ETL_Pipeline completa, THE ETL_Pipeline DEBERÁ escribir metadata sobre la ejecución del job en el bucket Silver_Layer

### Requisito 11: Gestión de Configuración

**Historia de Usuario:** Como ingeniero de datos, quiero configurar el pipeline a través de archivos de configuración externos almacenados en S3, para poder ajustar el comportamiento sin modificar código.

#### Criterios de Aceptación

1. CUANDO el ETL_Pipeline inicia, THE ETL_Pipeline DEBERÁ leer configuración desde un archivo JSON almacenado en el bucket de scripts de S3
2. CUANDO la configuración especifica mapeos de columnas, THE ETL_Pipeline DEBERÁ aplicar esos mapeos para identificar columnas de email, teléfono, fecha y timestamp
3. CUANDO la configuración especifica columnas críticas, THE DataGapHandler DEBERÁ usar esas columnas para detección de brechas
4. CUANDO la configuración especifica columnas clave de duplicados, THE DuplicateDetector DEBERÁ usar esas columnas para detección de duplicados
5. CUANDO el archivo de configuración falta o es inválido, THE ETL_Pipeline DEBERÁ usar valores de configuración por defecto y registrar una advertencia en CloudWatch
