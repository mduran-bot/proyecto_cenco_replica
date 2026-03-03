# Requirements Document: Initial Data Load

## Introduction

Este documento define los requerimientos para el proceso de migración de datos desde la base de datos MySQL actual de Janis hacia el nuevo pipeline de datos que alimentará el Redshift existente de Cencosud. Esta migración reemplaza la conexión directa actual entre MySQL-Janis y Redshift por el nuevo sistema de Data Lake con capas Bronze, Silver y Gold, manteniendo la compatibilidad con el Redshift existente.

## Glossary

- **MySQL_Janis_Current**: Base de datos MySQL actual de Janis que alimenta directamente a Redshift
- **Redshift_Existing**: Cluster de Amazon Redshift existente de Cencosud (ya en producción)
- **Data_Lake_Pipeline**: Nuevo pipeline de datos con capas Bronze, Silver y Gold
- **Migration_Process**: Proceso de transición desde conexión directa MySQL→Redshift al nuevo pipeline
- **Schema_Compatibility**: Mantenimiento de compatibilidad con esquemas existentes en Redshift
- **Cutover**: Momento de cambio desde el sistema actual al nuevo pipeline
- **Parallel_Load**: Carga paralela para validar datos antes del cutover
- **Rollback_Plan**: Plan de contingencia para volver al sistema anterior

## Requirements

### Requirement 1: Current System Analysis and Schema Mapping

**User Story:** Como arquitecto de migración, quiero analizar el sistema actual MySQL→Redshift, para que pueda mapear correctamente los esquemas y asegurar compatibilidad con el nuevo pipeline.

#### Acceptance Criteria

1. THE System SHALL analyze the existing Redshift schema structure and table definitions
2. THE System SHALL document current data types, constraints, and relationships in Redshift
3. THE System SHALL map existing Redshift tables to corresponding MySQL Janis tables
4. THE System SHALL identify any custom transformations currently applied in the direct connection
5. THE System SHALL document current data loading schedules and dependencies
6. THE System SHALL analyze current query patterns and performance requirements
7. THE System SHALL create compatibility matrix between current schema and new pipeline output

### Requirement 2: Source Data Validation

**User Story:** Como especialista en calidad de datos, quiero validar la integridad de todos los datos en la base de datos MySQL fuente, para que pueda identificar y documentar cualquier problema antes del procesamiento.

#### Acceptance Criteria

1. THE System SHALL verify that all 25 expected tables are present in the MySQL database
2. THE System SHALL validate table structure consistency against expected schemas
3. THE System SHALL verify data type consistency within each table
4. THE System SHALL identify and document duplicate records within each table using business keys
5. THE System SHALL validate that critical fields are not unexpectedly null
6. THE System SHALL verify date ranges are within expected bounds (not future dates, reasonable historical range)
7. THE System SHALL check referential integrity between related tables
8. THE System SHALL generate a comprehensive data quality report before extraction begins

### Requirement 3: Direct Data Extraction to Gold Layer

**User Story:** Como arquitecto de datos, quiero extraer datos directamente desde MySQL hacia la capa Gold en S3, para que se optimice el proceso eliminando transformaciones intermedias innecesarias.

#### Acceptance Criteria

1. THE System SHALL extract data directly from MySQL tables to S3 Gold layer in Parquet format with Snappy compression
2. THE System SHALL implement parallel extraction of multiple tables simultaneously (up to 10 concurrent extractions)
3. THE System SHALL organize data with partitioning structure optimized for Redshift: `gold/table_name/year=YYYY/month=MM/day=DD/`
4. THE System SHALL apply Redshift-compatible data type conversions during extraction:
   - BIGINT Unix timestamps to TIMESTAMP ISO 8601 format
   - TINYINT(1) to BOOLEAN (0/1 to false/true)
   - VARCHAR(n) to VARCHAR(n) with max 65535 limit
   - DECIMAL(p,s) to NUMERIC(p,s)
   - JSON fields to VARCHAR(65535)
5. THE System SHALL optimize file sizes to 64-128 MB for efficient Redshift COPY operations
6. THE System SHALL generate manifest files for each table pointing to S3 Gold locations

### Requirement 4: Data Type Conversion and Normalization

**User Story:** Como ingeniero de ETL, quiero convertir los datos MySQL a formatos compatibles con Redshift durante la extracción, para que estén listos para carga directa sin procesamiento adicional.

#### Acceptance Criteria

1. THE System SHALL convert MySQL data types to Redshift-compatible types during extraction:
   - BIGINT Unix timestamps to TIMESTAMP ISO 8601 format
   - TINYINT(1) to BOOLEAN (0/1 to false/true)
   - VARCHAR(n) to VARCHAR(n) with maximum 65535 characters
   - DECIMAL(p,s) to NUMERIC(p,s) maintaining precision
   - JSON fields to VARCHAR(65535) with validation
   - TEXT fields to VARCHAR(65535)
   - DATETIME to TIMESTAMP in 'YYYY-MM-DD HH:MM:SS' format
2. THE System SHALL normalize data formats during extraction:
   - Standardize all timestamps to UTC timezone
   - Clean and validate email addresses using regex patterns
   - Normalize phone numbers to standard format
   - Trim whitespace from string fields
3. THE System SHALL handle NULL values appropriately for each target data type
4. THE System SHALL validate data ranges during conversion to prevent overflow
5. THE System SHALL log all data type conversion issues for review

### Requirement 5: Data Gap Handling

**User Story:** Como analista de negocio, quiero que el sistema identifique y maneje campos faltantes de manera transparente, para que los reportes de BI reflejen claramente qué información no está disponible.

#### Acceptance Criteria

1. THE System SHALL identify all Data Gaps documented in the mapping analysis
2. THE System SHALL implement calculated fields where possible:
   - items_substituted_qty: COUNT of items with substitute_type = 'substitute'
   - items_qty_missing: SUM(quantity - COALESCE(quantity_picked, 0))
   - total_changes: amount - originalAmount
3. THE System SHALL mark non-calculable fields as NULL with metadata flags indicating unavailability
4. THE System SHALL generate a Data Gap report documenting:
   - Fields not available in source
   - Fields calculated from other data
   - Impact on BI reports
5. THE System SHALL NOT block the loading process due to missing non-critical fields

### Requirement 6: Redshift-Optimized File Generation

**User Story:** Como especialista en data warehouse, quiero generar archivos optimizados para Redshift directamente desde MySQL, para que las cargas posteriores tengan el mejor rendimiento posible.

#### Acceptance Criteria

1. THE System SHALL generate Parquet files with Redshift-optimized characteristics:
   - File sizes between 64-128 MB for optimal COPY performance
   - Snappy compression for balance between size and decompression speed
   - Column-oriented storage with appropriate encoding
2. THE System SHALL create Redshift-compatible schemas with:
   - Distribution keys for frequently joined tables (orders, order_items)
   - Sort keys for commonly filtered columns (dates, IDs)
   - Appropriate data types for storage efficiency
3. THE System SHALL generate manifest files for Redshift COPY commands with:
   - S3 file locations and sizes
   - Mandatory flag set to true
   - Proper JSON formatting for COPY command
4. THE System SHALL organize files by table with consistent naming convention
5. THE System SHALL validate file integrity and completeness before marking as ready for Redshift load

### Requirement 7: Migration to Existing Redshift

**User Story:** Como administrador de base de datos, quiero migrar los datos del nuevo pipeline al Redshift existente de Cencosud, para que mantenga compatibilidad total con los sistemas BI actuales.

#### Acceptance Criteria

1. THE System SHALL load data to the existing Redshift cluster without disrupting current operations
2. THE System SHALL create new tables with "_new" suffix for parallel validation before cutover
3. THE System SHALL maintain exact schema compatibility with existing Redshift tables
4. THE System SHALL implement zero-downtime cutover process:
   - Load data to parallel tables
   - Validate data consistency
   - Rename tables atomically during maintenance window
5. THE System SHALL preserve existing table statistics and query performance
6. THE System SHALL maintain existing materialized views and dependent objects
7. THE System SHALL complete migration validation within 4 hours
8. THE System SHALL provide rollback capability to restore original tables if needed

### Requirement 8: Data Validation and Reconciliation

**User Story:** Como auditor de datos, quiero verificar que todos los datos se cargaron correctamente desde MySQL a Redshift, para que pueda confirmar la integridad y completitud de la migración directa.

#### Acceptance Criteria

1. THE System SHALL verify record counts match between MySQL source and Redshift destination
2. THE System SHALL validate data type conversions were applied correctly during the direct transfer
3. THE System SHALL confirm that NOT NULL constraints are respected in Redshift
4. THE System SHALL verify date ranges are preserved correctly after conversion
5. THE System SHALL generate checksums for critical tables and compare between MySQL and Redshift
6. THE System SHALL document orphaned records (records without valid foreign key references)
7. THE System SHALL NOT fail validation due to missing foreign key relationships
8. THE System SHALL produce a final reconciliation report with:
   - Total records loaded per table
   - Data type conversion summary
   - Orphaned records summary
   - Processing time and performance metrics
   - File sizes and compression ratios achieved

### Requirement 9: Error Handling and Recovery

**User Story:** Como ingeniero de operaciones, quiero que el sistema maneje errores de manera robusta durante la carga directa, para que pueda recuperarse de fallos sin perder datos o corromper el estado.

#### Acceptance Criteria

1. THE System SHALL implement retry logic with exponential backoff for transient failures:
   - MySQL connection timeouts
   - S3 upload failures
   - Redshift COPY command failures
2. THE System SHALL maintain processing state to enable restart from failure point per table
3. THE System SHALL create detailed error logs with:
   - Error type and description
   - Failed record details (when applicable)
   - MySQL query context
   - S3 file location context
   - Timestamp and processing context
4. THE System SHALL handle MySQL connection failures gracefully with automatic reconnection
5. THE System SHALL validate S3 file uploads before proceeding to Redshift load
6. THE System SHALL provide manual recovery mechanisms:
   - Ability to restart individual table extractions
   - Option to skip problematic tables and continue with others
   - Manual validation and reprocessing capabilities
7. THE System SHALL ensure that partial failures do not corrupt successfully processed data

### Requirement 10: Monitoring and Observability

**User Story:** Como ingeniero de monitoreo, quiero visibilidad completa del proceso de carga inicial directa, para que pueda detectar problemas temprano y optimizar el rendimiento.

#### Acceptance Criteria

1. THE System SHALL generate CloudWatch metrics for:
   - Records extracted per minute from MySQL
   - S3 upload throughput and success rate
   - Redshift COPY command duration and success rate
   - Processing duration per table
   - Error rates and types by component (MySQL, S3, Redshift)
   - Resource utilization (CPU, memory, network I/O)
2. THE System SHALL create CloudWatch alarms for:
   - MySQL connection failures
   - S3 upload failures
   - Redshift COPY failures
   - Processing time exceeding expected thresholds per table
   - High error rates (>1%)
   - Resource exhaustion
3. THE System SHALL log all major processing milestones with timestamps:
   - Table extraction start/completion
   - S3 upload completion
   - Redshift table creation
   - COPY command execution
4. THE System SHALL provide real-time progress visibility through dashboards showing:
   - Overall progress percentage
   - Current table being processed
   - Records processed vs. total estimated
   - ETA for completion
5. THE System SHALL send notifications for critical events:
   - Process start and completion
   - Critical errors requiring intervention
   - Final success/failure status with summary

### Requirement 11: Security and Compliance

**User Story:** Como oficial de seguridad, quiero asegurar que el proceso de carga inicial directa cumple con todos los estándares de seguridad, para que los datos sensibles estén protegidos durante todo el proceso.

#### Acceptance Criteria

1. THE System SHALL access MySQL database using IAM database authentication or encrypted credentials stored in AWS Secrets Manager
2. THE System SHALL encrypt all data in transit using TLS 1.2+:
   - MySQL connections with SSL/TLS
   - S3 uploads with HTTPS
   - Redshift connections with SSL
3. THE System SHALL encrypt all data at rest using AWS KMS:
   - S3 Gold layer files with server-side encryption
   - Redshift cluster with encryption at rest
4. THE System SHALL implement least-privilege access:
   - Read-only access to MySQL source database
   - Write access only to designated S3 Gold bucket paths
   - Redshift access limited to target database and schema
5. THE System SHALL maintain audit logs of all data access and processing activities:
   - MySQL query execution logs
   - S3 file upload logs
   - Redshift COPY command logs
   - User access and authentication logs
6. THE System SHALL mask or tokenize PII data (emails, phone numbers) during extraction if required
7. THE System SHALL rotate database credentials after completion
8. THE System SHALL comply with data retention policies throughout the process