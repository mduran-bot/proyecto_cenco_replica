# Plan de Implementación: Pipeline ETL Bronze-to-Silver

## Resumen

Este plan describe la implementación de un pipeline ETL Bronze-to-Silver compuesto por 8 módulos de transformación de datos usando Python/PySpark, AWS Glue y Apache Iceberg. Todos los archivos se crearán dentro de la carpeta `max/`.

## Tareas

- [x] 1. Configurar estructura del proyecto y dependencias
  - Crear estructura de directorios en `max/src/modules/`
  - Crear archivo `max/requirements.txt` con dependencias (pyspark, pyiceberg, boto3, pytest, hypothesis)
  - Crear archivo `max/src/config/bronze-to-silver-config.json` con configuración por defecto
  - _Requisitos: 11.1, 11.5_

- [x] 2. Implementar módulo JSONFlattener
  - [x] 2.1 Crear clase JSONFlattener en `max/src/modules/json_flattener.py`
    - Implementar método `transform()` que recibe DataFrame y config
    - Implementar método `_flatten_struct()` para aplanar columnas struct recursivamente
    - Implementar método `_explode_arrays()` para explotar arrays
    - Implementar método `_resolve_name_collision()` para resolver colisiones de nombres
    - _Requisitos: 4.1, 4.2, 4.3, 4.4_
  
  - [x] 2.2 Escribir property test para aplanamiento de estructuras anidadas
    - **Propiedad 13: Aplanamiento de estructuras anidadas**
    - **Valida: Requisito 4.1**
  
  - [x] 2.3 Escribir property test para explosión de arrays
    - **Propiedad 14: Explosión de arrays**
    - **Valida: Requisito 4.2**
  
  - [x] 2.4 Escribir property test para aplanamiento recursivo
    - **Propiedad 15: Aplanamiento recursivo de estructuras profundas**
    - **Valida: Requisito 4.3**
  
  - [x] 2.5 Escribir property test para unicidad de nombres
    - **Propiedad 16: Unicidad de nombres de columnas**
    - **Valida: Requisito 4.4**
  
  - [x] 2.6 Escribir property test para idempotencia
    - **Propiedad 17: Idempotencia del aplanamiento**
    - **Valida: Requisito 4.5**

- [ ] 3. Implementar módulo DataCleaner
  - [x] 3.1 Crear clase DataCleaner en `max/src/modules/data_cleaner.py`
    - Implementar método `transform()` que recibe DataFrame y config
    - Implementar método `_trim_strings()` para eliminar espacios en blanco
    - Implementar método `_empty_to_null()` para convertir strings vacíos a null
    - Implementar método `_fix_encoding()` para corregir problemas de encoding UTF-8
    - _Requisitos: 2.1, 2.2, 2.3, 2.4, 2.5_
  
  - [ ] 3.2 Escribir property test para eliminación de espacios
    - **Propiedad 5: Eliminación de espacios en blanco**
    - **Valida: Requisito 2.1**
  
  - [ ] 3.3 Escribir property test para conversión de strings vacíos
    - **Propiedad 6: Conversión de strings vacíos a null**
    - **Valida: Requisito 2.2**
  
  - [ ] 3.4 Escribir property test para preservación de nulls
    - **Propiedad 7: Preservación de valores null**
    - **Valida: Requisitos 2.4, 3.5**
  
  - [ ] 3.5 Escribir property test para preservación del orden de columnas
    - **Propiedad 8: Preservación del orden de columnas**
    - **Valida: Requisito 2.5**

- [ ] 4. Implementar módulo DataNormalizer
  - [x] 4.1 Crear clase DataNormalizer en `max/src/modules/data_normalizer.py`
    - Implementar método `transform()` que recibe DataFrame y config
    - Implementar método `_normalize_emails()` para convertir emails a minúsculas
    - Implementar método `_normalize_phones()` para eliminar caracteres no numéricos
    - Implementar método `_normalize_dates()` para estandarizar formatos de fecha
    - Implementar método `_normalize_timestamps()` para estandarizar formatos de timestamp
    - _Requisitos: 3.1, 3.2, 3.3, 3.4, 3.5_
  
  - [ ] 4.2 Escribir property test para normalización de emails
    - **Propiedad 9: Normalización de emails a minúsculas**
    - **Valida: Requisito 3.1**
  
  - [ ] 4.3 Escribir property test para normalización de teléfonos
    - **Propiedad 10: Eliminación de caracteres no numéricos en teléfonos**
    - **Valida: Requisito 3.2**
  
  - [ ] 4.4 Escribir property test para normalización de fechas
    - **Propiedad 11: Estandarización de formatos de fecha**
    - **Valida: Requisito 3.3**
  
  - [ ] 4.5 Escribir property test para normalización de timestamps
    - **Propiedad 12: Estandarización de formatos de timestamp**
    - **Valida: Requisito 3.4**

- [ ] 5. Checkpoint - Verificar módulos de limpieza y normalización
  - Asegurar que todos los tests pasen, preguntar al usuario si surgen dudas.

- [ ] 6. Implementar módulo DataTypeConverter
  - [x] 6.1 Crear clase DataTypeConverter en `max/src/modules/data_type_converter.py`
    - Implementar método `transform()` que recibe DataFrame y config
    - Implementar método `_infer_and_convert()` para inferir y convertir tipos
    - Implementar método `_is_boolean_string()` para detectar strings booleanos
    - Implementar método `_is_date_string()` para detectar strings de fecha
    - Implementar método `_is_numeric_string()` para detectar strings numéricos
    - Definir diccionario `type_mapping` con mapeos de tipos
    - _Requisitos: 1.5, 1.6, 1.7, 1.8_
  
  - [ ] 6.2 Escribir property test para conversión de strings booleanos
    - **Propiedad 1: Conversión de strings booleanos**
    - **Valida: Requisito 1.5**
  
  - [ ] 6.3 Escribir property test para conversión de strings de fecha
    - **Propiedad 2: Conversión de strings de fecha**
    - **Valida: Requisito 1.6**
  
  - [ ] 6.4 Escribir property test para conversión de strings de timestamp
    - **Propiedad 3: Conversión de strings de timestamp**
    - **Valida: Requisito 1.7**
  
  - [ ] 6.5 Escribir property test para conversión de strings decimales
    - **Propiedad 4: Conversión de strings decimales**
    - **Valida: Requisito 1.8**

- [ ] 7. Implementar módulo DuplicateDetector
  - [x] 7.1 Crear clase DuplicateDetector en `max/src/modules/duplicate_detector.py`
    - Implementar método `transform()` que recibe DataFrame y config
    - Implementar método `_mark_duplicates()` para marcar duplicados con is_duplicate
    - Implementar método `_assign_group_ids()` para asignar duplicate_group_id
    - Usar Window functions de PySpark para agrupamiento eficiente
    - _Requisitos: 7.1, 7.2, 7.3, 7.4, 7.5_
  
  - [ ] 7.2 Escribir property test para detección completa de duplicados
    - **Propiedad 21: Detección completa de duplicados**
    - **Valida: Requisitos 7.1, 7.2, 7.3**
  
  - [ ] 7.3 Escribir property test para preservación de columnas originales
    - **Propiedad 22: Preservación de columnas originales**
    - **Valida: Requisito 7.5**

- [ ] 8. Implementar módulo ConflictResolver
  - [x] 8.1 Crear clase ConflictResolver en `max/src/modules/conflict_resolver.py`
    - Implementar método `transform()` que recibe DataFrame y config
    - Implementar método `_select_best_record()` para seleccionar mejor registro por grupo
    - Implementar método `_count_nulls()` para contar nulls por fila
    - Usar Window functions con ranking para selección determinística
    - _Requisitos: 8.1, 8.2, 8.3, 8.4, 8.5_
  
  - [ ] 8.2 Escribir property test para selección basada en timestamp
    - **Propiedad 23: Selección basada en timestamp más reciente**
    - **Valida: Requisito 8.1**
  
  - [ ] 8.3 Escribir property test para desempate basado en nulls
    - **Propiedad 24: Desempate basado en conteo de nulls**
    - **Valida: Requisito 8.2**
  
  - [ ] 8.4 Escribir property test para desempate determinístico
    - **Propiedad 25: Desempate determinístico**
    - **Valida: Requisito 8.3**
  
  - [ ] 8.5 Escribir property test para eliminación de columnas auxiliares
    - **Propiedad 26: Eliminación de columnas auxiliares**
    - **Valida: Requisito 8.4**
  
  - [ ] 8.6 Escribir property test para idempotencia sin duplicados
    - **Propiedad 27: Idempotencia para DataFrames sin duplicados**
    - **Valida: Requisito 8.5**

- [ ] 9. Implementar módulo DataGapHandler
  - [x] 9.1 Crear clase DataGapHandler en `max/src/modules/data_gap_handler.py`
    - Implementar método `transform()` que recibe DataFrame y config
    - Implementar método `_mark_critical_gaps()` para marcar registros con brechas
    - Implementar método `_fill_defaults()` para rellenar valores por defecto
    - Implementar método `_filter_incomplete()` para filtrar registros incompletos
    - _Requisitos: 9.1, 9.2, 9.3, 9.4, 9.5_
  
  - [ ] 9.2 Escribir property test para identificación de brechas críticas
    - **Propiedad 28: Identificación de brechas críticas**
    - **Valida: Requisitos 9.1, 9.2**
  
  - [ ] 9.3 Escribir property test para relleno con valores por defecto
    - **Propiedad 29: Relleno con valores por defecto**
    - **Valida: Requisito 9.3**
  
  - [ ] 9.4 Escribir property test para filtrado de registros incompletos
    - **Propiedad 30: Filtrado de registros incompletos**
    - **Valida: Requisito 9.4**

- [ ] 10. Checkpoint - Verificar módulos de deduplicación y manejo de brechas
  - Asegurar que todos los tests pasen, preguntar al usuario si surgen dudas.

- [ ] 11. Implementar módulo IcebergTableManager
  - [x] 11.1 Crear clase IcebergTableManager en `max/src/modules/iceberg_table_manager.py`
    - Implementar método `__init__()` para inicializar catálogo de Iceberg
    - Implementar método `_init_catalog()` para configurar catálogo Hadoop
    - Implementar método `table_exists()` para verificar existencia de tabla
    - Implementar método `create_table()` para crear nueva tabla con esquema
    - Implementar método `evolve_schema()` para agregar columnas a tabla existente
    - Implementar método `get_table()` para obtener referencia a tabla
    - _Requisitos: 5.1, 5.2, 5.3, 5.4, 5.5_
  
  - [ ] 11.2 Escribir property test para idempotencia de creación
    - **Propiedad 18: Idempotencia de creación de tablas**
    - **Valida: Requisito 5.4**
  
  - [ ] 11.3 Escribir unit tests para operaciones de tabla
    - Test de creación de tabla nueva
    - Test de verificación de existencia
    - Test de evolución de esquema
    - Test de particionamiento por fecha
    - _Requisitos: 5.1, 5.2, 5.3, 5.5_

- [ ] 12. Implementar módulo IcebergWriter
  - [x] 12.1 Crear clase IcebergWriter en `max/src/modules/iceberg_writer.py`
    - Implementar método `__init__()` que recibe IcebergTableManager
    - Implementar método `write()` para escribir DataFrame en tabla Iceberg
    - Implementar método `_ensure_table_exists()` para crear/evolucionar tabla
    - Implementar método `_write_with_retry()` para escritura con reintentos
    - _Requisitos: 6.1, 6.2, 6.3, 6.4, 6.5_
  
  - [ ] 12.2 Escribir property test para conteo correcto de registros
    - **Propiedad 19: Conteo correcto de registros escritos**
    - **Valida: Requisitos 6.1, 6.4**
  
  - [ ] 12.3 Escribir property test para append sin sobrescritura
    - **Propiedad 20: Append sin sobrescritura**
    - **Valida: Requisito 6.2**
  
  - [ ] 12.4 Escribir unit tests para manejo de errores
    - Test de rollback en caso de fallo
    - Test de evolución de esquema automática
    - _Requisitos: 6.3, 6.5_

- [ ] 13. Implementar orquestador ETLPipeline
  - [x] 13.1 Crear clase ETLPipeline en `max/src/etl_pipeline.py`
    - Implementar método `__init__()` para inicializar SparkSession y módulos
    - Implementar método `_load_config()` para leer configuración desde S3
    - Implementar método `_init_modules()` para instanciar todos los módulos en orden
    - Implementar método `_init_logger()` para configurar logging a CloudWatch
    - Implementar método `run()` para ejecutar pipeline completo
    - Implementar método `_log_metrics()` para registrar métricas por etapa
    - Implementar método `_write_job_metadata()` para escribir metadata de ejecución
    - _Requisitos: 10.1, 10.2, 10.3, 10.4, 10.5_
  
  - [ ] 13.2 Escribir unit tests para orquestación
    - Test de lectura de configuración
    - Test de orden de ejecución de módulos
    - Test de manejo de errores
    - _Requisitos: 10.2, 10.4, 11.1, 11.5_

- [ ] 14. Crear script principal de AWS Glue Job
  - [x] 14.1 Crear archivo `max/src/main_job.py` como entry point del Glue Job
    - Importar todas las clases de módulos
    - Inicializar SparkSession con configuración de Iceberg
    - Parsear argumentos del job (input_path, output_database, output_table, config_path)
    - Instanciar ETLPipeline con configuración
    - Ejecutar pipeline con manejo de errores
    - Registrar éxito/fallo en CloudWatch
    - _Requisitos: 10.1, 10.2, 10.3, 10.4, 10.5_

- [ ] 15. Checkpoint - Verificar integración completa
  - Asegurar que todos los tests pasen, preguntar al usuario si surgen dudas.

- [ ] 16. Crear tests de integración end-to-end
  - [ ] 16.1 Crear archivo `max/tests/test_integration.py`
    - Test de pipeline completo con datos de ejemplo
    - Verificar lectura desde S3 Bronze (LocalStack)
    - Verificar escritura a S3 Silver (LocalStack)
    - Verificar transformaciones aplicadas correctamente
    - Verificar metadata de job escrita
    - _Requisitos: 10.1, 10.2, 10.5_
  
  - [x] 16.2 Crear fixtures de datos de prueba
    - Crear archivo `max/tests/fixtures/sample_ventas.json` con datos de ejemplo
    - Incluir casos con estructuras anidadas, duplicados, valores null
    - _Requisitos: 4.1, 7.1, 9.1_

- [x] 17. Crear configuración de ejemplo y documentación
  - Crear archivo `max/src/config/bronze-to-silver-config.example.json` con configuración completa comentada
  - Crear archivo `max/README.md` con instrucciones de uso del pipeline
  - Documentar cómo ejecutar el job en LocalStack
  - Documentar cómo ejecutar tests
  - _Requisitos: 11.1, 11.2, 11.3, 11.4_

- [ ] 18. Configurar pytest y hypothesis
  - Crear archivo `max/pytest.ini` con configuración de pytest
  - Configurar hypothesis con perfil de CI (100 iteraciones mínimo)
  - Configurar markers para property tests e integration tests
  - Crear archivo `max/.coveragerc` para configuración de cobertura

- [ ] 19. Checkpoint final - Ejecutar suite completa de tests
  - Ejecutar todos los unit tests
  - Ejecutar todos los property tests
  - Ejecutar tests de integración
  - Verificar cobertura mínima de 80%
  - Asegurar que todos los tests pasen, preguntar al usuario si surgen dudas.

## Notas

- Todas las tareas son obligatorias para asegurar cobertura completa de tests
- Cada módulo sigue el patrón Strategy con interfaz `transform(df, config)`
- Los property tests usan `hypothesis` con mínimo 100 iteraciones
- Los tests de integración requieren LocalStack corriendo
- Todos los archivos se crean dentro de la carpeta `max/`
- La estructura de directorios será:
  ```
  max/
  ├── src/
  │   ├── modules/
  │   │   ├── __init__.py
  │   │   ├── json_flattener.py
  │   │   ├── data_cleaner.py
  │   │   ├── data_normalizer.py
  │   │   ├── data_type_converter.py
  │   │   ├── duplicate_detector.py
  │   │   ├── conflict_resolver.py
  │   │   ├── data_gap_handler.py
  │   │   ├── iceberg_table_manager.py
  │   │   └── iceberg_writer.py
  │   ├── config/
  │   │   ├── bronze-to-silver-config.json
  │   │   └── bronze-to-silver-config.example.json
  │   ├── etl_pipeline.py
  │   └── main_job.py
  ├── tests/
  │   ├── fixtures/
  │   │   └── sample_ventas.json
  │   ├── test_json_flattener.py
  │   ├── test_data_cleaner.py
  │   ├── test_data_normalizer.py
  │   ├── test_data_type_converter.py
  │   ├── test_duplicate_detector.py
  │   ├── test_conflict_resolver.py
  │   ├── test_data_gap_handler.py
  │   ├── test_iceberg_table_manager.py
  │   ├── test_iceberg_writer.py
  │   ├── test_etl_pipeline.py
  │   └── test_integration.py
  ├── requirements.txt
  ├── pytest.ini
  ├── .coveragerc
  └── README.md
  ```
