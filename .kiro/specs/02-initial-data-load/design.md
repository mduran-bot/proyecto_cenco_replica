# Design Document: Initial Data Load

## Overview

This design document describes the architecture and implementation approach for migrating historical data from the current MySQL-Janis database to the new Data Lake pipeline, ultimately loading into the existing Cencosud Redshift cluster. The solution implements a direct extraction approach from MySQL to S3 Gold layer, bypassing Bronze and Silver layers to optimize the one-time migration process while maintaining full compatibility with existing Redshift schemas and BI systems.

**Related Documentation:**
- [Análisis de Esquema Redshift - Resumen Ejecutivo](docs/Análisis de Esquema Redshift - Resumen Ejecutivo.md) - Analysis of existing Redshift schema (db_conf database)
- [Análisis Esquema Redshift - Mapeo Detallado](docs/Análisis Esquema Redshift - Mapeo Detallado.md) - Detailed mapping for Janis integration (datalabs database with replica schemas)
- [Análisis Estructura S3 Gold Producción](docs/Análisis Estructura S3 Gold Producción.md) - Analysis of existing S3 Gold structure and file format requirements

### Key Design Decisions

**Direct MySQL to Gold Extraction**: Skip Bronze/Silver layers for initial load since this is a one-time migration. Apply all transformations during extraction to produce Redshift-ready Parquet files directly in the Gold layer.

**Parallel Processing Architecture**: Use AWS Glue with parallel execution to extract up to 10 tables simultaneously, reducing total migration time from days to hours.

**Zero-Downtime Cutover**: Load data into parallel tables with "_new" suffix, validate completely, then perform atomic table rename during a maintenance window to minimize disruption.

**Redshift-Optimized Output**: Generate Parquet files sized 64-128 MB with Snappy compression, optimized partitioning following the existing S3 Gold structure pattern (`ExternalAccess/janis_smk_pe/automatico/{table}/year=YYYY/month=MM/day=DD/`), and manifest files for efficient COPY operations.

**Target Schemas**: Based on the Redshift schema analysis, data will be loaded into:
- **Bronze Layer**: `janis_aurorape_replica`, `janis_metroio_replica`, `janis_wongio_replica` schemas (empty, ready for data)
- **Silver Layer**: `dl_sp_table_stg`, `dl_sp_proc_stg` schemas (staging and transformation)
- **Gold Layer**: `dl_sp_dashboards_ecommerce`, `dl_sp_dashboards_ventas` schemas (business-ready analytics)

## Architecture

### High-Level Architecture

```
┌─────────────────┐
│  MySQL Janis    │
│  (Source DB)    │
└────────┬────────┘
         │
         │ SSL/TLS Connection
         │ Read-Only Access
         │
         ▼
┌─────────────────────────────────────────────────────┐
│         AWS Glue ETL Job (Orchestrator)             │
│  ┌──────────────────────────────────────────────┐   │
│  │  Schema Analysis & Validation Module         │   │
│  └──────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────┐   │
│  │  Parallel Extraction Workers (up to 10)      │   │
│  │  - Data Type Conversion                      │   │
│  │  - Data Normalization                        │   │
│  │  - Data Gap Handling                         │   │
│  │  - File Size Optimization                    │   │
│  └──────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────┐   │
│  │  Validation & Reconciliation Module          │   │
│  └──────────────────────────────────────────────┘   │
└─────────────────┬───────────────────────────────────┘
                  │
                  │ HTTPS (Encrypted)
                  │
                  ▼
         ┌────────────────────┐
         │   S3 Gold Layer    │
         │  Parquet + Snappy  │
         │  + Manifest Files  │
         └────────┬───────────┘
                  │
                  │ Redshift COPY Command
                  │ SSL Connection
                  │
                  ▼
         ┌────────────────────┐
         │ Redshift Existing  │
         │  (Parallel Tables) │
         │   table_name_new   │
         └────────┬───────────┘
                  │
                  │ Atomic Rename (Cutover)
                  │
                  ▼
         ┌────────────────────┐
         │ Redshift Existing  │
         │  (Production)      │
         │   table_name       │
         └────────────────────┘
```

### Component Interaction Flow

1. **Pre-Migration Analysis**: Glue job analyzes existing Redshift schemas and MySQL source tables
2. **Source Validation**: Validates MySQL data quality and generates pre-migration report
3. **Parallel Extraction**: Spawns multiple workers to extract tables concurrently
4. **Transformation**: Each worker applies data type conversions and normalization
5. **Gold Layer Write**: Writes Redshift-optimized Parquet files to S3 Gold
6. **Manifest Generation**: Creates manifest files for Redshift COPY commands
7. **Parallel Load**: Loads data into Redshift tables with "_new" suffix
8. **Validation**: Performs comprehensive data reconciliation
9. **Cutover**: Atomic table rename during maintenance window
10. **Post-Migration**: Final validation and rollback capability


## Components and Interfaces

### 1. Schema Analysis Module

**Purpose**: Analyze existing Redshift schemas and map to MySQL source tables.

**Responsibilities**:
- Connect to existing Redshift cluster (read-only)
- Extract table definitions, data types, constraints from both db_conf and datalabs databases
- Identify target schemas: janis_*_replica (Bronze), dl_sp_table_stg (Silver), dl_sp_dashboards_* (Gold)
- Query MySQL information_schema for source table structures
- Create compatibility matrix between source and target
- Identify custom transformations needed
- Document current query patterns and performance requirements
- Reference existing schema analysis documentation for baseline understanding

**Interfaces**:
- Input: Redshift connection parameters, MySQL connection parameters
- Output: Schema mapping document (JSON), compatibility matrix, transformation requirements

**Key Functions**:
```python
def analyze_redshift_schema(redshift_conn, schema_name) -> Dict[str, TableDefinition]
def analyze_mysql_schema(mysql_conn, database_name) -> Dict[str, TableDefinition]
def create_compatibility_matrix(redshift_tables, mysql_tables) -> CompatibilityMatrix
def identify_transformations(compatibility_matrix) -> List[Transformation]
```

### 2. Source Data Validation Module

**Purpose**: Validate MySQL source data quality before extraction.

**Responsibilities**:
- Verify all 25 expected tables exist
- Validate table structures match expected schemas
- Check data type consistency within tables
- Identify duplicate records using business keys
- Validate critical fields for NULL values
- Verify date ranges are reasonable
- Check referential integrity between tables
- Generate comprehensive data quality report

**Interfaces**:
- Input: MySQL connection, expected schema definitions
- Output: Data quality report (JSON/HTML), validation status, list of issues

**Key Functions**:
```python
def validate_table_existence(mysql_conn, expected_tables) -> ValidationResult
def validate_table_structure(mysql_conn, table_name, expected_schema) -> ValidationResult
def identify_duplicates(mysql_conn, table_name, business_keys) -> List[DuplicateRecord]
def validate_null_constraints(mysql_conn, table_name, critical_fields) -> ValidationResult
def validate_date_ranges(mysql_conn, table_name, date_fields) -> ValidationResult
def check_referential_integrity(mysql_conn, relationships) -> ValidationResult
def generate_quality_report(validation_results) -> DataQualityReport
```


### 3. Parallel Extraction Worker

**Purpose**: Extract data from MySQL tables and transform to Redshift-compatible format.

**Responsibilities**:
- Extract data from assigned MySQL table using streaming queries
- Apply data type conversions (timestamps, booleans, strings, decimals)
- Normalize data formats (UTC timestamps, email validation, phone normalization)
- Handle data gaps with calculated fields or NULL markers
- Optimize file sizes to 64-128 MB chunks
- Write Parquet files with Snappy compression to S3 Gold
- Generate partition structure: `gold/table_name/year=YYYY/month=MM/day=DD/`

**Interfaces**:
- Input: Table name, MySQL connection, S3 bucket path, transformation rules
- Output: Parquet files in S3 Gold, extraction metadata, error logs

**Key Functions**:
```python
def extract_table_data(mysql_conn, table_name, batch_size) -> Iterator[DataFrame]
def convert_data_types(df, conversion_rules) -> DataFrame
def normalize_data_formats(df, normalization_rules) -> DataFrame
def handle_data_gaps(df, gap_handling_rules) -> DataFrame
def optimize_file_size(df, target_size_mb) -> List[DataFrame]
def write_parquet_to_s3(df, s3_path, partition_cols) -> WriteResult
```

**Data Type Conversion Rules**:
- BIGINT (Unix timestamp) → TIMESTAMP (ISO 8601)
- TINYINT(1) → BOOLEAN
- VARCHAR(n) → VARCHAR(min(n, 65535))
- DECIMAL(p,s) → NUMERIC(p,s)
- JSON → VARCHAR(65535)
- TEXT → VARCHAR(65535)
- DATETIME → TIMESTAMP ('YYYY-MM-DD HH:MM:SS')


### 4. Manifest Generator

**Purpose**: Create Redshift COPY manifest files for efficient data loading.

**Responsibilities**:
- Scan S3 Gold layer for completed Parquet files
- Generate manifest JSON with file locations and sizes
- Set mandatory flag to true for all files
- Validate manifest format for Redshift compatibility
- Store manifests in S3 for COPY command consumption

**Interfaces**:
- Input: S3 bucket path, table name, partition information
- Output: Manifest file (JSON) in S3

**Manifest Format**:
```json
{
  "entries": [
    {
      "url": "s3://bucket/gold/table_name/year=2024/month=01/day=15/part-00001.parquet",
      "mandatory": true,
      "meta": {
        "content_length": 67108864
      }
    }
  ]
}
```

**Key Functions**:
```python
def scan_s3_files(s3_client, bucket, prefix) -> List[S3Object]
def generate_manifest(s3_files, table_name) -> ManifestFile
def validate_manifest_format(manifest) -> ValidationResult
def write_manifest_to_s3(manifest, s3_path) -> WriteResult
```


### 5. Redshift Loader

**Purpose**: Load data from S3 Gold into Redshift parallel tables.

**Responsibilities**:
- Create parallel tables with "_new" suffix
- Apply distribution keys (orders, order_items)
- Apply sort keys (dates, IDs)
- Execute COPY commands using manifest files
- Monitor COPY command progress and errors
- Validate load completion and data integrity

**Interfaces**:
- Input: Redshift connection, manifest file S3 path, table schema
- Output: Load status, row counts, error logs

**Key Functions**:
```python
def create_parallel_table(redshift_conn, table_name, schema_def) -> CreateResult
def execute_copy_command(redshift_conn, table_name, manifest_path) -> CopyResult
def monitor_copy_progress(redshift_conn, query_id) -> ProgressStatus
def validate_load_completion(redshift_conn, table_name, expected_count) -> ValidationResult
```

**COPY Command Template**:
```sql
COPY {table_name}_new
FROM 's3://bucket/manifests/{table_name}_manifest.json'
IAM_ROLE 'arn:aws:iam::account:role/RedshiftCopyRole'
FORMAT AS PARQUET
MANIFEST
COMPUPDATE ON
STATUPDATE ON;
```


### 6. Validation and Reconciliation Module

**Purpose**: Verify data integrity and completeness after migration.

**Responsibilities**:
- Compare record counts between MySQL and Redshift
- Validate data type conversions were applied correctly
- Verify NOT NULL constraints are respected
- Check date range preservation
- Generate checksums for critical tables
- Document orphaned records
- Produce comprehensive reconciliation report

**Interfaces**:
- Input: MySQL connection, Redshift connection, table list
- Output: Reconciliation report (JSON/HTML), validation status

**Key Functions**:
```python
def compare_record_counts(mysql_conn, redshift_conn, table_name) -> CountComparison
def validate_data_type_conversions(redshift_conn, table_name, conversion_rules) -> ValidationResult
def verify_not_null_constraints(redshift_conn, table_name, constraints) -> ValidationResult
def validate_date_ranges(mysql_conn, redshift_conn, table_name) -> ValidationResult
def generate_table_checksum(conn, table_name, key_columns) -> str
def identify_orphaned_records(redshift_conn, relationships) -> List[OrphanedRecord]
def generate_reconciliation_report(validation_results) -> ReconciliationReport
```

**Reconciliation Report Structure**:
```json
{
  "migration_summary": {
    "total_tables": 25,
    "successful_tables": 25,
    "failed_tables": 0,
    "total_records_migrated": 15000000,
    "total_processing_time_hours": 3.5
  },
  "table_details": [
    {
      "table_name": "orders",
      "mysql_count": 500000,
      "redshift_count": 500000,
      "match": true,
      "checksum_match": true,
      "orphaned_records": 0,
      "processing_time_minutes": 45,
      "file_size_mb": 1024,
      "compression_ratio": 0.35
    }
  ]
}
```


### 7. Cutover Orchestrator

**Purpose**: Manage zero-downtime cutover from old to new tables.

**Responsibilities**:
- Coordinate cutover timing during maintenance window
- Perform atomic table renames
- Preserve table statistics and query performance
- Maintain materialized views and dependent objects
- Provide rollback capability

**Interfaces**:
- Input: Redshift connection, table list, cutover schedule
- Output: Cutover status, rollback scripts

**Key Functions**:
```python
def prepare_cutover(redshift_conn, table_list) -> CutoverPlan
def execute_atomic_rename(redshift_conn, table_name) -> RenameResult
def preserve_table_statistics(redshift_conn, old_table, new_table) -> StatisticsResult
def update_dependent_objects(redshift_conn, table_name) -> UpdateResult
def generate_rollback_script(table_list) -> str
def execute_rollback(redshift_conn, rollback_script) -> RollbackResult
```

**Cutover SQL Template**:
```sql
BEGIN TRANSACTION;

-- Rename current table to backup
ALTER TABLE {table_name} RENAME TO {table_name}_old;

-- Rename new table to production
ALTER TABLE {table_name}_new RENAME TO {table_name};

-- Copy statistics
ANALYZE {table_name};

COMMIT;
```


### 8. Error Handling and Recovery Module

**Purpose**: Handle failures gracefully and enable recovery.

**Responsibilities**:
- Implement retry logic with exponential backoff
- Maintain processing state for restart capability
- Create detailed error logs
- Handle connection failures with automatic reconnection
- Validate S3 uploads before proceeding
- Provide manual recovery mechanisms

**Interfaces**:
- Input: Error events, processing state
- Output: Recovery actions, error logs, state checkpoints

**Key Functions**:
```python
def retry_with_backoff(func, max_retries, initial_delay) -> Result
def save_processing_state(state, s3_path) -> SaveResult
def load_processing_state(s3_path) -> ProcessingState
def handle_mysql_connection_failure(mysql_conn) -> ConnectionResult
def validate_s3_upload(s3_client, bucket, key) -> ValidationResult
def restart_table_extraction(table_name, last_checkpoint) -> RestartResult
```

**Processing State Structure**:
```json
{
  "migration_id": "migration-2024-01-15-001",
  "start_time": "2024-01-15T10:00:00Z",
  "tables_completed": ["orders", "products"],
  "tables_in_progress": ["order_items"],
  "tables_pending": ["inventory", "prices"],
  "last_checkpoint": {
    "table": "order_items",
    "last_processed_id": 150000,
    "s3_files_written": 15
  }
}
```


### 9. Monitoring and Observability Module

**Purpose**: Provide comprehensive visibility into migration progress.

**Responsibilities**:
- Emit CloudWatch metrics for all key operations
- Create CloudWatch alarms for critical failures
- Log processing milestones with timestamps
- Provide real-time progress dashboards
- Send SNS notifications for critical events

**Interfaces**:
- Input: Processing events, metrics data
- Output: CloudWatch metrics, alarms, logs, SNS notifications

**Key Functions**:
```python
def emit_metric(metric_name, value, dimensions) -> None
def create_alarm(alarm_name, metric, threshold, actions) -> AlarmResult
def log_milestone(milestone_name, metadata) -> None
def update_progress_dashboard(progress_data) -> None
def send_notification(topic_arn, subject, message) -> NotificationResult
```

**CloudWatch Metrics**:
- `MySQL/RecordsExtracted` - Records per minute
- `S3/UploadThroughput` - MB per second
- `S3/UploadSuccessRate` - Percentage
- `Redshift/CopyDuration` - Seconds per table
- `Redshift/CopySuccessRate` - Percentage
- `Processing/TableDuration` - Minutes per table
- `Errors/MySQLConnectionFailures` - Count
- `Errors/S3UploadFailures` - Count
- `Errors/RedshiftCopyFailures` - Count
- `Resources/CPUUtilization` - Percentage
- `Resources/MemoryUtilization` - Percentage


## Data Models

### TableDefinition

Represents the structure of a database table.

```python
@dataclass
class TableDefinition:
    table_name: str
    columns: List[ColumnDefinition]
    primary_key: List[str]
    foreign_keys: List[ForeignKeyDefinition]
    indexes: List[IndexDefinition]
    row_count: Optional[int]
    size_mb: Optional[float]
```

### ColumnDefinition

Represents a column in a table.

```python
@dataclass
class ColumnDefinition:
    column_name: str
    data_type: str
    is_nullable: bool
    default_value: Optional[str]
    max_length: Optional[int]
    precision: Optional[int]
    scale: Optional[int]
```

### CompatibilityMatrix

Maps source tables to target tables with transformation requirements.

```python
@dataclass
class CompatibilityMatrix:
    table_mappings: Dict[str, TableMapping]
    transformation_rules: List[TransformationRule]
    data_gaps: List[DataGap]
    
@dataclass
class TableMapping:
    source_table: str
    target_table: str
    column_mappings: Dict[str, ColumnMapping]
    requires_transformation: bool
    
@dataclass
class ColumnMapping:
    source_column: str
    target_column: str
    source_type: str
    target_type: str
    transformation: Optional[str]
```


### DataGap

Represents missing or calculated fields.

```python
@dataclass
class DataGap:
    field_name: str
    table_name: str
    gap_type: str  # 'missing', 'calculated', 'unavailable'
    calculation_formula: Optional[str]
    impact_description: str
    workaround: Optional[str]
```

### ValidationResult

Represents the result of a validation check.

```python
@dataclass
class ValidationResult:
    check_name: str
    passed: bool
    message: str
    details: Dict[str, Any]
    severity: str  # 'error', 'warning', 'info'
    timestamp: datetime
```

### ProcessingState

Tracks the state of the migration process.

```python
@dataclass
class ProcessingState:
    migration_id: str
    start_time: datetime
    tables_completed: List[str]
    tables_in_progress: List[str]
    tables_pending: List[str]
    last_checkpoint: Optional[Checkpoint]
    total_records_processed: int
    total_files_written: int
    
@dataclass
class Checkpoint:
    table_name: str
    last_processed_id: int
    s3_files_written: int
    timestamp: datetime
```


### ReconciliationReport

Comprehensive report of migration results.

```python
@dataclass
class ReconciliationReport:
    migration_id: str
    start_time: datetime
    end_time: datetime
    total_duration_hours: float
    migration_summary: MigrationSummary
    table_details: List[TableReconciliation]
    data_gaps_summary: List[DataGap]
    errors_summary: List[ErrorSummary]
    
@dataclass
class MigrationSummary:
    total_tables: int
    successful_tables: int
    failed_tables: int
    total_records_migrated: int
    total_size_mb: float
    average_compression_ratio: float
    
@dataclass
class TableReconciliation:
    table_name: str
    mysql_count: int
    redshift_count: int
    counts_match: bool
    checksum_match: bool
    orphaned_records: int
    processing_time_minutes: float
    file_size_mb: float
    compression_ratio: float
    validation_errors: List[str]
```


## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Schema Compatibility Preservation

*For any* table in the existing Redshift schema, the migrated data SHALL maintain exact schema compatibility including data types, constraints, and relationships.

**Validates: Requirements 1.2, 1.3, 7.3**

### Property 2: Record Count Consistency

*For any* table extracted from MySQL, the number of records loaded into Redshift SHALL equal the number of records in the source MySQL table.

**Validates: Requirements 8.1**

### Property 3: Data Type Conversion Correctness

*For any* data type conversion rule (MySQL type → Redshift type), all values SHALL be converted according to the specified mapping without data loss or corruption.

**Validates: Requirements 3.4, 4.1, 8.2**

### Property 4: Timestamp Normalization

*For any* timestamp field, all values SHALL be converted to UTC timezone and formatted as ISO 8601 or 'YYYY-MM-DD HH:MM:SS' format.

**Validates: Requirements 4.2**

### Property 5: File Size Optimization

*For any* Parquet file generated, the file size SHALL be between 64 MB and 128 MB (except for the last file of a table which may be smaller).

**Validates: Requirements 3.5, 6.1**


### Property 6: Partition Structure Consistency

*For any* table written to S3 Gold layer, the partition structure SHALL follow the pattern `gold/table_name/year=YYYY/month=MM/day=DD/`.

**Validates: Requirements 3.3**

### Property 7: Manifest File Completeness

*For any* table, the manifest file SHALL reference all Parquet files written for that table with correct S3 paths and mandatory flag set to true.

**Validates: Requirements 3.6, 6.3**

### Property 8: NOT NULL Constraint Preservation

*For any* column with NOT NULL constraint in Redshift, no NULL values SHALL exist in the migrated data.

**Validates: Requirements 8.3**

### Property 9: Date Range Validity

*For any* date or timestamp field, all values SHALL be within reasonable bounds (not future dates, within expected historical range).

**Validates: Requirements 2.6, 8.4**

### Property 10: Parallel Table Isolation

*For any* table being migrated, the parallel table with "_new" suffix SHALL be completely independent from the production table until cutover.

**Validates: Requirements 7.2, 7.4**

### Property 11: Atomic Cutover

*For any* cutover operation, the table rename SHALL be atomic (either fully succeeds or fully fails) with no intermediate state visible to queries.

**Validates: Requirements 7.4**


### Property 12: Rollback Capability

*For any* completed cutover, the system SHALL maintain the ability to rollback to the original tables by renaming "_old" tables back to production names.

**Validates: Requirements 7.8**

### Property 13: Data Gap Handling Consistency

*For any* calculated field defined in data gap handling rules, the calculation SHALL be applied consistently to all records.

**Validates: Requirements 5.2**

### Property 14: Encryption in Transit

*For any* data transfer (MySQL→Glue, Glue→S3, S3→Redshift), the connection SHALL use TLS 1.2 or higher encryption.

**Validates: Requirements 11.2**

### Property 15: Encryption at Rest

*For any* data written to S3 Gold layer or Redshift, the data SHALL be encrypted using AWS KMS.

**Validates: Requirements 11.3**

### Property 16: Retry with Exponential Backoff

*For any* transient failure (connection timeout, temporary service unavailability), the system SHALL retry with exponential backoff up to a maximum number of attempts.

**Validates: Requirements 9.1**

### Property 17: Processing State Persistence

*For any* table extraction in progress, the processing state SHALL be persisted to S3 to enable restart from the last checkpoint.

**Validates: Requirements 9.2**


### Property 18: Checksum Consistency

*For any* critical table, the checksum calculated on MySQL source data SHALL match the checksum calculated on Redshift destination data.

**Validates: Requirements 8.5**

### Property 19: Orphaned Record Documentation

*For any* record with invalid foreign key references, the system SHALL document it as orphaned but SHALL NOT fail the migration.

**Validates: Requirements 8.6, 8.7**

### Property 20: CloudWatch Metrics Emission

*For any* major processing event (extraction start/complete, upload complete, COPY complete), a corresponding CloudWatch metric SHALL be emitted.

**Validates: Requirements 10.1, 10.3**

### Property 21: Critical Event Notification

*For any* critical event (process start, completion, critical error), an SNS notification SHALL be sent.

**Validates: Requirements 10.5**

### Property 22: Least Privilege Access

*For any* AWS resource access, the IAM role SHALL have only the minimum permissions required for that specific operation.

**Validates: Requirements 11.4**

### Property 23: Audit Log Completeness

*For any* data access or processing activity, an audit log entry SHALL be created with timestamp, user/role, and operation details.

**Validates: Requirements 11.5**


## Error Handling

### Error Categories

**Transient Errors** (Retry with exponential backoff):
- MySQL connection timeouts
- S3 upload failures due to network issues
- Redshift COPY command temporary failures
- AWS service throttling

**Permanent Errors** (Log and skip or fail):
- Invalid MySQL credentials
- Missing MySQL tables
- S3 bucket access denied
- Redshift schema incompatibility
- Data type conversion impossible

**Data Quality Errors** (Log and continue):
- Duplicate records (document in report)
- Orphaned records (document in report)
- NULL values in non-critical fields
- Date range anomalies (document in report)

### Retry Strategy

```python
def retry_with_exponential_backoff(
    func: Callable,
    max_retries: int = 5,
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
    backoff_factor: float = 2.0
) -> Result:
    """
    Retry function with exponential backoff.
    
    Delay sequence: 1s, 2s, 4s, 8s, 16s (capped at max_delay)
    """
    delay = initial_delay
    for attempt in range(max_retries):
        try:
            return func()
        except TransientError as e:
            if attempt == max_retries - 1:
                raise
            log_retry_attempt(func.__name__, attempt + 1, delay, e)
            time.sleep(min(delay, max_delay))
            delay *= backoff_factor
```


### Error Recovery Procedures

**MySQL Connection Failure**:
1. Log error with connection details (host, port, database)
2. Retry with exponential backoff (up to 5 attempts)
3. If all retries fail, send critical alert via SNS
4. Save processing state to S3
5. Exit with error code for manual intervention

**S3 Upload Failure**:
1. Log error with file details (size, path, table)
2. Retry upload with exponential backoff (up to 5 attempts)
3. Validate upload after each retry using HEAD request
4. If all retries fail, mark file as failed in processing state
5. Continue with other files, report failed files at end

**Redshift COPY Failure**:
1. Query STL_LOAD_ERRORS for detailed error information
2. Log error with query details and error messages
3. Retry COPY command with exponential backoff (up to 3 attempts)
4. If data issue, document in reconciliation report
5. If persistent failure, send critical alert and halt

**Partial Table Extraction Failure**:
1. Save checkpoint with last successfully processed record ID
2. Log error with table name and checkpoint information
3. Provide manual recovery option to restart from checkpoint
4. Allow skipping problematic table and continuing with others
5. Document partial failure in final report


### Error Logging Format

```json
{
  "timestamp": "2024-01-15T14:23:45Z",
  "migration_id": "migration-2024-01-15-001",
  "error_type": "MySQLConnectionTimeout",
  "severity": "error",
  "component": "ParallelExtractionWorker",
  "table_name": "orders",
  "error_message": "Connection to MySQL timed out after 30 seconds",
  "context": {
    "mysql_host": "janis-mysql.example.com",
    "mysql_port": 3306,
    "database": "janis_production",
    "retry_attempt": 3,
    "last_processed_id": 150000
  },
  "stack_trace": "...",
  "recovery_action": "Retrying with exponential backoff (delay: 8s)"
}
```


## Testing Strategy

### Dual Testing Approach

The testing strategy combines unit tests for specific scenarios and property-based tests for universal correctness properties. Both approaches are complementary and necessary for comprehensive coverage.

**Unit Tests**: Verify specific examples, edge cases, and error conditions
**Property Tests**: Verify universal properties across all inputs

Together, these provide comprehensive coverage where unit tests catch concrete bugs and property tests verify general correctness.

### Unit Testing

**Schema Analysis Module**:
- Test Redshift schema extraction with known schema
- Test MySQL schema extraction with known schema
- Test compatibility matrix generation with matching schemas
- Test compatibility matrix with incompatible schemas
- Test transformation identification for common conversions

**Source Data Validation Module**:
- Test table existence validation with all tables present
- Test table existence validation with missing tables
- Test duplicate detection with known duplicates
- Test NULL validation with NULL values in critical fields
- Test date range validation with future dates
- Test referential integrity with orphaned records

**Parallel Extraction Worker**:
- Test data type conversion for each conversion rule
- Test data normalization for timestamps, emails, phones
- Test file size optimization with various data volumes
- Test partition structure generation
- Test handling of NULL values

**Manifest Generator**:
- Test manifest generation with multiple files
- Test manifest format validation
- Test handling of empty file lists

**Redshift Loader**:
- Test parallel table creation
- Test COPY command execution
- Test error handling for COPY failures

**Validation Module**:
- Test record count comparison with matching counts
- Test record count comparison with mismatched counts
- Test checksum generation and comparison
- Test orphaned record identification


### Property-Based Testing

Property-based tests will use **Hypothesis** (Python) as the testing framework. Each property test must run a minimum of 100 iterations to ensure comprehensive input coverage through randomization.

**Property Test Configuration**:
```python
from hypothesis import given, settings
import hypothesis.strategies as st

@settings(max_examples=100)
@given(...)
def test_property_name(...):
    # Feature: initial-data-load, Property N: property description
    pass
```

**Property Tests to Implement**:

1. **Schema Compatibility Preservation** (Property 1)
   - Generate random table schemas
   - Apply migration transformations
   - Verify schema compatibility is maintained

2. **Record Count Consistency** (Property 2)
   - Generate random datasets with known record counts
   - Extract and load data
   - Verify counts match exactly

3. **Data Type Conversion Correctness** (Property 3)
   - Generate random values for each MySQL data type
   - Apply conversion rules
   - Verify no data loss or corruption

4. **Timestamp Normalization** (Property 4)
   - Generate random timestamps in various timezones
   - Apply normalization
   - Verify all timestamps are UTC and properly formatted

5. **File Size Optimization** (Property 5)
   - Generate random datasets of various sizes
   - Create Parquet files
   - Verify file sizes are within 64-128 MB range (except last file)

6. **Partition Structure Consistency** (Property 6)
   - Generate random table names and dates
   - Create partition paths
   - Verify paths follow the required pattern

7. **Manifest File Completeness** (Property 7)
   - Generate random sets of S3 file paths
   - Create manifest
   - Verify all files are referenced with correct attributes


8. **NOT NULL Constraint Preservation** (Property 8)
   - Generate random datasets with NULL values
   - Apply NOT NULL constraints
   - Verify no NULLs exist in constrained columns

9. **Date Range Validity** (Property 9)
   - Generate random dates including edge cases
   - Apply date range validation
   - Verify all dates are within reasonable bounds

10. **Encryption in Transit** (Property 14)
    - Generate random connection configurations
    - Verify TLS 1.2+ is enforced for all connections

11. **Retry with Exponential Backoff** (Property 16)
    - Simulate random transient failures
    - Apply retry logic
    - Verify exponential backoff delays are correct

12. **Checksum Consistency** (Property 18)
    - Generate random datasets
    - Calculate checksums at source and destination
    - Verify checksums match

### Integration Testing

**End-to-End Migration Test**:
- Set up test MySQL database with sample data
- Set up test Redshift cluster
- Execute complete migration process
- Verify all data is correctly migrated
- Verify reconciliation report is accurate

**Cutover Test**:
- Load data into parallel tables
- Execute cutover process
- Verify atomic rename succeeded
- Verify rollback capability works

**Error Recovery Test**:
- Simulate various failure scenarios
- Verify recovery mechanisms work correctly
- Verify processing state is correctly saved and restored


### Performance Testing

**Parallel Extraction Performance**:
- Test with 1, 5, and 10 concurrent table extractions
- Measure total migration time
- Verify resource utilization stays within limits

**File Size Optimization Performance**:
- Test with various data volumes (1GB, 10GB, 100GB)
- Verify file sizes remain in optimal range
- Measure compression ratios achieved

**Redshift COPY Performance**:
- Test COPY commands with various file sizes
- Measure load times
- Verify optimal performance with 64-128 MB files

### Security Testing

**Encryption Verification**:
- Verify TLS 1.2+ is used for all connections
- Verify KMS encryption is applied to S3 files
- Verify Redshift encryption at rest is enabled

**Access Control Testing**:
- Verify IAM roles have least-privilege permissions
- Verify MySQL access is read-only
- Verify S3 access is limited to designated paths
- Verify Redshift access is limited to target schema

**Audit Log Testing**:
- Verify all data access is logged
- Verify log entries contain required information
- Verify logs are stored securely


## Implementation Notes

### AWS Glue Job Configuration

**Job Type**: Python Shell (for orchestration) + Spark (for data processing)

**Python Shell Job** (Orchestrator):
- Runtime: Python 3.9
- DPU: 0.0625 (1/16 DPU)
- Timeout: 48 hours
- Max concurrent runs: 1
- Purpose: Coordinate overall migration process

**Spark Job** (Data Extraction):
- Glue Version: 4.0
- Worker Type: G.1X (4 vCPU, 16 GB RAM)
- Number of Workers: 10 (for parallel extraction)
- Timeout: 24 hours
- Max concurrent runs: 1
- Purpose: Extract and transform data from MySQL

### MySQL Connection Configuration

```python
mysql_config = {
    "host": "janis-mysql.example.com",
    "port": 3306,
    "database": "janis_production",
    "user": "readonly_user",
    "ssl": {
        "ssl_ca": "/path/to/ca-cert.pem",
        "ssl_verify_cert": True,
        "ssl_verify_identity": True
    },
    "connect_timeout": 30,
    "read_timeout": 300,
    "charset": "utf8mb4"
}
```

### S3 Bucket Structure

Based on the analysis of the existing S3 Gold production structure (see [Análisis Estructura S3 Gold Producción](docs/Análisis Estructura S3 Gold Producción.md)), the data will follow the established pattern:

```
s3://cencosud.test.super.peru.analytics/ExternalAccess/janis_smk_pe/automatico/
├── orders/
│   ├── year=2024/
│   │   ├── month=01/
│   │   │   ├── day=15/
│   │   │   │   ├── part-00000-{uuid}.c000.snappy.parquet
│   │   │   │   ├── part-00001-{uuid}.c000.snappy.parquet
│   │   │   │   └── ...
├── order_items/
│   └── year=YYYY/month=MM/day=DD/
│       └── part-{n}-{uuid}.c000.snappy.parquet
├── products/
│   └── year=YYYY/month=MM/day=DD/
├── skus/
│   └── year=YYYY/month=MM/day=DD/
├── stores/
│   └── year=YYYY/month=MM/day=DD/
└── stock/
    └── year=YYYY/month=MM/day=DD/
```

**Key Characteristics:**
- **Naming Convention**: `part-{sequence:05d}-{uuid}.c000.snappy.parquet`
- **Compression**: Snappy (consistent with existing milocal_smk_pe tables)
- **File Size**: 64-128 MB (optimized for Redshift COPY)
- **Partitioning**: Hive-style `year=YYYY/month=MM/day=DD/`
- **Location**: Under `ExternalAccess/janis_smk_pe/automatico/` to match existing system patterns

**Bronze/Silver/Gold Layer Structure:**
- **Bronze**: `s3://cencosud.test.super.peru.raw/janis/` (raw JSON data)
- **Silver**: `s3://cencosud.test.super.peru.raw-structured/janis/` (cleaned Parquet)
- **Gold**: `s3://cencosud.test.super.peru.analytics/ExternalAccess/janis_smk_pe/` (business-ready)


### Redshift Table Configuration

**Distribution Keys**:
- `orders`: DISTKEY(order_id)
- `order_items`: DISTKEY(order_id)
- `products`: DISTKEY(product_id)
- `inventory`: DISTKEY(product_id)

**Sort Keys**:
- `orders`: SORTKEY(created_at, order_id)
- `order_items`: SORTKEY(order_id, item_id)
- `products`: SORTKEY(product_id)
- `inventory`: SORTKEY(product_id, warehouse_id)

### IAM Roles and Permissions

**Glue Job Execution Role**:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:DeleteObject"
      ],
      "Resource": "arn:aws:s3:::cencosud-datalake-gold-prod/*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "secretsmanager:GetSecretValue"
      ],
      "Resource": "arn:aws:secretsmanager:*:*:secret:mysql-credentials-*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "kms:Decrypt",
        "kms:GenerateDataKey"
      ],
      "Resource": "arn:aws:kms:*:*:key/*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "arn:aws:logs:*:*:*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "cloudwatch:PutMetricData"
      ],
      "Resource": "*"
    }
  ]
}
```


**Redshift COPY Role**:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::cencosud-datalake-gold-prod",
        "arn:aws:s3:::cencosud-datalake-gold-prod/*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "kms:Decrypt"
      ],
      "Resource": "arn:aws:kms:*:*:key/*"
    }
  ]
}
```

### CloudWatch Dashboard Configuration

**Dashboard Name**: `initial-data-load-migration`

**Widgets**:
1. Overall Progress (Number widget)
   - Metric: Custom/Migration/ProgressPercentage
   
2. Tables Processed (Number widget)
   - Metric: Custom/Migration/TablesCompleted
   
3. Records Extracted (Line graph)
   - Metric: MySQL/RecordsExtracted
   - Period: 1 minute
   
4. S3 Upload Throughput (Line graph)
   - Metric: S3/UploadThroughput
   - Period: 1 minute
   
5. Redshift COPY Duration (Bar chart)
   - Metric: Redshift/CopyDuration
   - Dimension: TableName
   
6. Error Rates (Line graph)
   - Metrics: Errors/MySQLConnectionFailures, Errors/S3UploadFailures, Errors/RedshiftCopyFailures
   - Period: 5 minutes


### Migration Execution Timeline

**Phase 1: Pre-Migration (2 hours)**
- Schema analysis and mapping
- Source data validation
- Generate data quality report
- Review and approve migration plan

**Phase 2: Data Extraction (8-12 hours)**
- Parallel extraction of 25 tables
- Data type conversion and normalization
- Write Parquet files to S3 Gold
- Generate manifest files

**Phase 3: Redshift Load (4-6 hours)**
- Create parallel tables with "_new" suffix
- Execute COPY commands for all tables
- Monitor load progress

**Phase 4: Validation (2-4 hours)**
- Record count reconciliation
- Checksum validation
- Data quality checks
- Generate reconciliation report

**Phase 5: Cutover (30 minutes)**
- Schedule maintenance window
- Execute atomic table renames
- Verify production queries work
- Monitor for issues

**Phase 6: Post-Migration (1 hour)**
- Final validation
- Update documentation
- Archive old tables
- Close migration

**Total Estimated Time**: 18-26 hours


### Rollback Procedures

**Scenario 1: Validation Failures Before Cutover**
- No rollback needed
- Fix issues and re-run validation
- Parallel tables remain isolated

**Scenario 2: Issues Discovered After Cutover**
```sql
-- Rollback script (execute within 24 hours)
BEGIN TRANSACTION;

-- Rename current tables to failed
ALTER TABLE orders RENAME TO orders_failed;
ALTER TABLE order_items RENAME TO order_items_failed;
-- ... repeat for all tables

-- Restore old tables
ALTER TABLE orders_old RENAME TO orders;
ALTER TABLE order_items_old RENAME TO order_items;
-- ... repeat for all tables

-- Analyze tables
ANALYZE orders;
ANALYZE order_items;
-- ... repeat for all tables

COMMIT;
```

**Scenario 3: Partial Migration Failure**
- Review processing state in S3
- Identify failed tables
- Restart extraction for failed tables only
- Continue from last checkpoint

### Monitoring and Alerting Configuration

**Critical Alarms** (SNS notification to on-call):
- MySQL connection failures > 3 in 5 minutes
- S3 upload failures > 5 in 10 minutes
- Redshift COPY failures > 1
- Processing time for any table > 2 hours
- Error rate > 1%

**Warning Alarms** (Email notification):
- Resource utilization > 80%
- Processing slower than expected (ETA increases)
- Data quality issues detected


### Security Considerations

**Credential Management**:
- MySQL credentials stored in AWS Secrets Manager
- Automatic rotation after migration completion
- Credentials encrypted with KMS
- Access logged in CloudTrail

**Network Security**:
- Glue jobs run in VPC private subnets
- MySQL connection through VPN or Direct Connect
- No public internet access for data transfer
- Security groups restrict access to necessary ports only

**Data Protection**:
- All data encrypted in transit (TLS 1.2+)
- All data encrypted at rest (KMS)
- PII data masked if required by compliance
- Access logs retained for audit purposes

**Compliance**:
- GDPR compliance for EU customer data
- Data retention policies enforced
- Right to be forgotten supported
- Audit trail maintained for all operations

### Performance Optimization

**MySQL Query Optimization**:
- Use streaming queries to avoid loading entire tables in memory
- Add indexes on columns used for ordering/filtering
- Use read replicas to avoid impacting production database
- Batch size: 10,000 records per batch

**S3 Upload Optimization**:
- Use multipart upload for files > 100 MB
- Parallel uploads for multiple files
- Retry failed uploads automatically
- Validate uploads with MD5 checksums

**Redshift COPY Optimization**:
- Use manifest files for efficient file discovery
- Enable COMPUPDATE for automatic compression
- Enable STATUPDATE for automatic statistics
- Use appropriate file sizes (64-128 MB)


### Cost Estimation

**AWS Glue**:
- Python Shell Job: $0.44 per DPU-hour × 0.0625 DPU × 48 hours = $1.32
- Spark Job: $0.44 per DPU-hour × 10 DPU × 12 hours = $52.80
- Total Glue: ~$54

**S3 Storage** (temporary, 1 month):
- 500 GB × $0.023 per GB = $11.50

**S3 Requests**:
- PUT requests: 10,000 × $0.005 per 1,000 = $0.05
- GET requests: 10,000 × $0.0004 per 1,000 = $0.004

**Redshift** (existing cluster, no additional cost)

**Data Transfer**:
- MySQL to AWS: Depends on connection type (VPN/Direct Connect)
- Within AWS: Free

**CloudWatch**:
- Metrics: 50 custom metrics × $0.30 = $15
- Logs: 10 GB × $0.50 = $5
- Alarms: 10 alarms × $0.10 = $1

**Total Estimated Cost**: ~$87 (one-time migration)

### Dependencies and Prerequisites

**External Dependencies**:
- MySQL database accessible from AWS VPC
- Existing Redshift cluster with sufficient storage
- S3 bucket for Gold layer (cencosud-datalake-gold-prod)
- AWS Secrets Manager for credentials
- KMS key for encryption
- SNS topic for notifications

**Required Permissions**:
- Glue job execution role with S3, Secrets Manager, KMS access
- Redshift COPY role with S3 read access
- CloudWatch permissions for metrics and logs

**Software Dependencies**:
- Python 3.9+
- PySpark 3.3+
- PyMySQL or mysql-connector-python
- boto3 (AWS SDK)
- pandas
- pyarrow (for Parquet)

