# Implementation Plan: Data Transformation System

## Overview

Este plan de implementación desglosa el diseño del sistema de transformación de datos en tareas discretas de codificación. Cada tarea construye sobre las anteriores y termina con la integración completa del sistema. El enfoque es incremental, validando funcionalidad core temprano a través de código y tests.

## 🎉 Actualización Reciente: Silver-to-Gold Pipeline (19 Feb 2026)

**Pipeline Silver-to-Gold completado e integrado** con 6 módulos principales:
- ✅ Task 15: Agregaciones Silver-to-Gold implementadas
- ✅ Task 17: Data Lineage Tracking implementado
- ✅ Task 18: Silver-to-Gold Glue Job implementado

**Módulos integrados**:
1. `IncrementalProcessor` - Procesamiento incremental con metadata tracking
2. `SilverToGoldAggregator` - Agregaciones de métricas de negocio
3. `DenormalizationEngine` - Joins con tablas de dimensiones
4. `DataQualityValidator` - Validación de calidad en 4 dimensiones
5. `ErrorHandler` - Manejo robusto de errores con DLQ
6. `DataLineageTracker` - Trazabilidad completa de datos

**Documentación**: Ver [INTEGRACION_SILVER_TO_GOLD_MAX.md](../../../Documentacion/INTEGRACION_SILVER_TO_GOLD_MAX.md)

**Pendiente**: Property tests y tests de integración end-to-end

---

## Tasks

- [ ] 1. Setup project structure and core infrastructure
  - Create directory structure for Glue jobs (bronze-to-silver, silver-to-gold, data-quality)
  - Define PySpark schemas for Bronze, Silver, and Gold layers
  - Setup Hypothesis testing framework configuration
  - Create base classes for Glue jobs with common functionality
  - _Requirements: 1.1, 1.2, 1.6_

- [ ] 2. Implement data type conversion module
  - [ ] 2.1 Create DataTypeConverter class
    - Implement MySQL to Redshift type conversion logic
    - Handle BIGINT timestamps → TIMESTAMP conversion
    - Handle TINYINT(1) → BOOLEAN conversion
    - Handle VARCHAR, DECIMAL, and JSON conversions
    - _Requirements: 2.1_

  - [ ] 2.2 Write property test for data type conversion
    - **Property 1: Data Type Conversion Correctness**
    - **Validates: Requirements 2.1**

- [ ] 3. Implement data normalization and cleansing
  - [ ] 3.1 Create DataNormalizer class
    - Standardize timestamps to 'YYYY-MM-DD HH:MM:SS' format
    - Validate and clean email addresses with regex
    - Normalize phone numbers to standard format
    - Standardize address components
    - _Requirements: 2.2_

  - [ ] 3.2 Write property test for data normalization
    - **Property 2: Data Format Normalization**
    - **Validates: Requirements 2.2**

  - [ ] 3.3 Create DataCleaner class
    - Trim whitespace from string fields
    - Convert empty strings to NULL
    - Handle encoding issues
    - _Requirements: 2.4_

  - [ ] 3.4 Write property test for data cleansing
    - **Property 4: Data Cleansing Rules**
    - **Validates: Requirements 2.4**

- [ ] 4. Implement JSON flattening module
  - [ ] 4.1 Create JSONFlattener class
    - Flatten nested JSON structures to individual columns
    - Handle arrays and nested objects
    - Preserve data types during flattening
    - _Requirements: 2.3_

  - [ ] 4.2 Write property test for JSON flattening
    - **Property 3: JSON Flattening Correctness**
    - **Validates: Requirements 2.3**

- [ ] 5. Implement Iceberg table management
  - [x] 5.1 Create IcebergTableManager class
    - Implement table creation with partitioning specs
    - Configure Parquet format with Snappy compression
    - Setup ACID transaction support
    - Implement snapshot management
    - _Requirements: 5.1, 5.2, 5.3_

  - [x] 5.2 Create IcebergWriter class
    - Write DataFrames to Iceberg tables
    - Handle transaction commits
    - Register tables in Glue Data Catalog
    - _Requirements: 2.5, 5.5_

  - [x] 5.3 Write property test for Iceberg write-read round trip
    - **Property 5: Iceberg Write-Read Round Trip**
    - **Validates: Requirements 2.5**

  - [x] 5.4 Write property test for ACID transactions
    - **Property 11: ACID Transaction Consistency**
    - **Validates: Requirements 5.3**

  - [x] 5.5 Write property test for time travel
    - **Property 12: Time Travel Snapshot Access**
    - **Validates: Requirements 5.4**

- [ ] 6. Checkpoint - Ensure basic transformation pipeline works
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 7. Implement deduplication engine
  - [ ] 7.1 Create DuplicateDetector class
    - Identify duplicates by business keys (order_id, item_id, product_id, sku_id)
    - Group records by business key
    - _Requirements: 3.1_

  - [ ] 7.2 Write property test for duplicate detection
    - **Property 6: Duplicate Detection by Business Key**
    - **Validates: Requirements 3.1**

  - [ ] 7.3 Create ConflictResolver class
    - Resolve conflicts using dateModified timestamp
    - Prefer webhook source over polling for identical timestamps
    - Handle missing timestamps edge case
    - _Requirements: 3.2, 3.5_

  - [ ] 7.4 Write property test for conflict resolution
    - **Property 7: Timestamp-Based Conflict Resolution**
    - **Validates: Requirements 3.2**

  - [ ] 7.5 Create MergeExecutor class
    - Execute Iceberg MERGE operations
    - Handle upsert logic
    - _Requirements: 3.3_

  - [ ] 7.6 Create AuditTracker for deduplication
    - Log deduplication decisions
    - Record which records were kept/discarded
    - _Requirements: 3.4_

- [ ] 8. Implement data gap handling
  - [ ] 8.1 Create DataGapHandler class
    - Identify documented data gaps from mapping
    - Calculate derived fields (items_substituted_qty, items_qty_missing, total_changes)
    - Annotate non-calculable fields with metadata flags
    - _Requirements: 4.1, 4.2, 4.3_

  - [ ] 8.2 Write property test for calculated fields
    - **Property 8: Calculated Fields Correctness**
    - **Validates: Requirements 4.2**

  - [ ] 8.3 Write property test for missing field annotation
    - **Property 9: Missing Field Metadata Annotation**
    - **Validates: Requirements 4.3**

  - [ ] 8.4 Write property test for graceful handling of missing fields
    - **Property 10: Graceful Handling of Missing Non-Critical Fields**
    - **Validates: Requirements 4.5**

  - [ ] 8.5 Create GapReporter class
    - Generate data gap reports
    - Document fields not available, calculated fields, and impact assessment
    - _Requirements: 4.4_

- [ ] 9. Implement Bronze-to-Silver Glue job
  - [ ] 9.1 Create BronzeToSilverJob main class
    - Orchestrate all transformation steps
    - Read from S3 Bronze layer
    - Apply type conversion, normalization, cleansing, flattening
    - Execute deduplication
    - Handle data gaps
    - Write to Iceberg Silver tables
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 3.1, 3.2, 4.2, 4.3_

  - [ ] 9.2 Write integration tests for Bronze-to-Silver pipeline
    - Test end-to-end transformation with sample data
    - Verify all transformations applied correctly
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

- [ ] 10. Checkpoint - Ensure Bronze-to-Silver pipeline is complete
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 11. Implement schema evolution management
  - [ ] 11.1 Create SchemaEvolutionManager class
    - Detect schema changes automatically
    - Validate schema changes before applying
    - Support safe operations (add column, rename, safe type change)
    - Maintain schema version history
    - _Requirements: 7.1, 7.2, 7.3, 7.4_

  - [ ] 11.2 Write property test for schema change detection
    - **Property 15: Schema Change Detection**
    - **Validates: Requirements 7.1**

  - [ ] 11.3 Write property test for safe schema evolution
    - **Property 16: Safe Schema Evolution**
    - **Validates: Requirements 7.2**

  - [ ] 11.4 Write property test for schema validation ordering
    - **Property 17: Schema Validation Before Application**
    - **Validates: Requirements 7.3**

  - [ ] 11.5 Write property test for schema version history
    - **Property 18: Schema Version History Completeness**
    - **Validates: Requirements 7.4**

  - [ ] 11.6 Implement alerting for unsafe schema changes
    - Send alerts when manual intervention required
    - _Requirements: 7.5_

  - [ ] 11.7 Write property test for unsafe schema alerting
    - **Property 19: Unsafe Schema Change Alerting**
    - **Validates: Requirements 7.5**

  - [ ] 11.8 Implement schema rollback capability
    - Rollback to previous schema version
    - _Requirements: 7.6_

  - [ ] 11.9 Write property test for schema rollback
    - **Property 20: Schema Rollback Capability**
    - **Validates: Requirements 7.6**

- [ ] 12. Implement data quality validation
  - [ ] 12.1 Create ValidationRuleEngine class
    - Implement null value validation
    - Implement data type validation
    - Implement range validation
    - Implement format validation
    - _Requirements: 8.1_

  - [ ] 12.2 Write property test for quality validation execution
    - **Property 21: Data Quality Validation Execution**
    - **Validates: Requirements 8.1**

  - [ ] 12.3 Create QualityMetricsCalculator class
    - Calculate completeness percentage
    - Calculate validity percentage
    - Calculate consistency percentage
    - Calculate accuracy percentage
    - _Requirements: 8.2_

  - [ ] 12.4 Write property test for quality metrics calculation
    - **Property 22: Quality Metrics Calculation Accuracy**
    - **Validates: Requirements 8.2**

  - [ ] 12.5 Create QualityReporter class
    - Generate quality reports with scores by table/column
    - Include trend analysis
    - Identify quality degradation
    - _Requirements: 8.3_

  - [ ] 12.6 Write property test for quality report completeness
    - **Property 23: Quality Report Completeness**
    - **Validates: Requirements 8.3**

  - [ ] 12.7 Create QualityGateEnforcer class
    - Block low-quality data from progressing
    - Compare metrics against thresholds
    - _Requirements: 8.4_

  - [ ] 12.8 Write property test for quality gate enforcement
    - **Property 24: Quality Gate Enforcement**
    - **Validates: Requirements 8.4**

- [ ] 13. Implement error handling and recovery
  - [ ] 13.1 Create ErrorHandler class
    - Classify errors by type (retryable, data quality, fatal, partial)
    - Route errors appropriately
    - _Requirements: 10.1_

  - [ ] 13.2 Write property test for comprehensive error handling
    - **Property 26: Comprehensive Error Handling**
    - **Validates: Requirements 10.1**

  - [ ] 13.3 Create StateManager class
    - Save processing state at checkpoints
    - Load processing state for restart
    - _Requirements: 10.2_

  - [ ] 13.4 Write property test for state persistence
    - **Property 27: Processing State Persistence**
    - **Validates: Requirements 10.2**

  - [ ] 13.5 Create DLQWriter class
    - Write failed records to Dead Letter Queue
    - Include original data, error context, timestamp, job ID
    - _Requirements: 10.3, 8.5_

  - [ ] 13.6 Write property test for DLQ routing
    - **Property 28: Failed Record DLQ Routing with Metadata**
    - **Validates: Requirements 8.5, 10.3**

  - [ ] 13.7 Create RetryOrchestrator class
    - Implement retry with exponential backoff
    - Retry up to 3 times
    - _Requirements: 1.5, 10.4_

  - [ ] 13.8 Write property test for retry behavior
    - **Property 29: Retry with Exponential Backoff**
    - **Validates: Requirements 1.5, 10.4**

  - [ ] 13.9 Implement checkpoint recovery
    - Resume from checkpoint after failure
    - _Requirements: 9.6_

  - [ ] 13.10 Write property test for checkpoint recovery
    - **Property 25: Checkpoint Recovery**
    - **Validates: Requirements 9.6**

  - [ ] 13.11 Implement manual reprocessing capability
    - Allow reprocessing of DLQ records
    - _Requirements: 10.5_

  - [ ] 13.12 Write property test for manual reprocessing
    - **Property 30: Manual Reprocessing Capability**
    - **Validates: Requirements 10.5**

- [ ] 14. Checkpoint - Ensure error handling and quality validation work
  - Ensure all tests pass, ask the user if questions arise.

- [x] 15. Implement Silver-to-Gold aggregations ✅ COMPLETADO (19 Feb 2026)
  - [x] 15.1 Create SilverToGoldAggregator class
    - Implement daily sales summary aggregation
    - Implement order fulfillment metrics aggregation
    - Implement product performance aggregation
    - _Requirements: 6.1_
    - **Status**: ✅ Implementado en `glue/modules/silver_to_gold/silver_to_gold_aggregator.py`

  - [ ] 15.2 Write property test for aggregation correctness
    - **Property 13: Aggregation Calculation Correctness**
    - **Validates: Requirements 6.1**
    - **Status**: ⏳ Pendiente - Módulo implementado, tests pendientes

  - [x] 15.3 Create DenormalizationEngine class
    - Denormalize related entities for faster joins
    - Pre-sort data by commonly filtered columns
    - _Requirements: 6.2_
    - **Status**: ✅ Implementado en `glue/modules/silver_to_gold/denormalization_engine.py`

  - [x] 15.4 Create IncrementalProcessor class
    - Process only new/modified records
    - Track last processed timestamp
    - _Requirements: 6.4_
    - **Status**: ✅ Implementado en `glue/modules/silver_to_gold/incremental_processor.py`

  - [ ] 15.5 Write property test for incremental processing
    - **Property 14: Incremental Processing Efficiency**
    - **Validates: Requirements 6.4**
    - **Status**: ⏳ Pendiente - Módulo implementado, tests pendientes

  - [ ] 15.6 Create MaterializedViewManager class
    - Create and manage materialized views
    - _Requirements: 6.3_
    - **Status**: ⏳ Pendiente de implementación

- [ ] 16. Implement monitoring and observability
  - [ ] 16.1 Create MetricsPublisher class
    - Publish job metrics to CloudWatch (duration, success rate, records processed)
    - Publish quality metrics to CloudWatch
    - Publish resource utilization metrics
    - Publish Iceberg table statistics
    - _Requirements: 11.1_

  - [ ] 16.2 Write property test for metrics publishing
    - **Property 31: CloudWatch Metrics Publishing**
    - **Validates: Requirements 11.1**

  - [ ] 16.3 Create AlarmManager class
    - Create CloudWatch alarms for job failures
    - Create alarms for processing time thresholds
    - Create alarms for quality degradation
    - Create alarms for resource exhaustion
    - _Requirements: 11.2_

  - [ ] 16.4 Create NotificationService class
    - Send notifications for critical events
    - Integrate with SNS for multi-channel notifications
    - _Requirements: 11.4_

  - [ ] 16.5 Write property test for critical event notifications
    - **Property 32: Critical Event Notifications**
    - **Validates: Requirements 11.4**

  - [ ] 16.6 Create DashboardGenerator class
- [x] 17. Implement data lineage tracking ✅ COMPLETADO (19 Feb 2026)
  - [x] 17.1 Create DataLineageTracker class
    - Record transformations with source and target information
    - Track transformation metadata (rules, job details, quality results)
    - Enable tracing individual records through all stages
    - _Requirements: 12.1, 12.2, 12.3_
    - **Status**: ✅ Implementado en `glue/modules/silver_to_gold/data_lineage_tracker.py`

  - [ ] 17.2 Write property test for complete lineage traceability
    - **Property 33: Complete Data Lineage Traceability**
    - **Validates: Requirements 6.5, 12.1, 12.3**
    - **Status**: ⏳ Pendiente - Módulo implementado, tests pendientes

  - [ ] 17.3 Write property test for transformation metadata completeness
    - **Property 34: Transformation Metadata Completeness**
    - **Validates: Requirements 3.4, 12.2, 12.4**
    - **Status**: ⏳ Pendiente - Módulo implementado, tests pendientes

  - [ ] 17.4 Create LineageQueryAPI class
    - Provide API for querying lineage information
    - Support filtering and search
    - _Requirements: 12.5_
    - **Status**: ⏳ Pendiente de implementación

  - [ ] 17.5 Create GovernanceIntegrator class
- [x] 18. Implement Silver-to-Gold Glue job ✅ COMPLETADO (19 Feb 2026)
  - [x] 18.1 Create SilverToGoldJob main class
    - Orchestrate aggregation pipeline
    - Read from Iceberg Silver tables
    - Apply aggregations and denormalization
    - Process incrementally
    - Write to Gold layer
    - Track lineage
    - _Requirements: 6.1, 6.2, 6.4, 6.5_
    - **Status**: ✅ Implementado en `glue/scripts/etl_pipeline_gold.py` (clase ETLPipelineGold)
    - **Módulos adicionales integrados**:
      - ✅ `DataQualityValidator` - Validación de calidad en 4 dimensiones
      - ✅ `ErrorHandler` - Manejo robusto de errores con DLQ y retry logic

  - [ ] 18.2 Write integration tests for Silver-to-Gold pipeline
    - Test end-to-end aggregation with sample data
    - Verify incremental processing
    - _Requirements: 6.1, 6.4_
    - **Status**: ⏳ Pendiente - Pipeline implementado, tests end-to-end pendientespipeline
    - Read from Iceberg Silver tables
    - Apply aggregations and denormalization
    - Process incrementally
    - Write to Gold layer
    - Track lineage
    - _Requirements: 6.1, 6.2, 6.4, 6.5_

  - [ ] 18.2 Write integration tests for Silver-to-Gold pipeline
    - Test end-to-end aggregation with sample data
    - Verify incremental processing
    - _Requirements: 6.1, 6.4_

- [ ] 19. Create Terraform infrastructure modules
  - [ ] 19.1 Create Glue job Terraform module
    - Define Glue job resources with proper configuration
    - Configure worker type, auto-scaling, timeout, retry policy
    - Setup VPC and security group configuration
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.7_

  - [x] 19.2 Create S3 bucket Terraform module
    - Define Bronze, Silver, Gold S3 buckets
    - Configure encryption and versioning
    - Setup lifecycle policies
    - _Requirements: 2.5, 5.1_

  - [x] 19.3 Create IAM roles Terraform module
    - Define IAM roles for Glue jobs
    - Apply least privilege principle
    - Grant necessary S3, Glue Catalog, CloudWatch permissions
    - _Requirements: 1.7_

  - [ ] 19.4 Create CloudWatch Terraform module
    - Define CloudWatch log groups
    - Create alarms and dashboards
    - Setup SNS topics for notifications
    - _Requirements: 11.1, 11.2, 11.3, 11.4_

- [ ] 20. Integration and deployment
  - [ ] 20.1 Wire all components together
    - Integrate Bronze-to-Silver job with all modules
    - Integrate Silver-to-Gold job with all modules
    - Configure job dependencies and triggers
    - _Requirements: All_

  - [ ] 20.2 Create deployment scripts
    - Script for deploying Terraform infrastructure
    - Script for uploading Glue job code to S3
    - Script for running end-to-end tests
    - _Requirements: All_

  - [ ] 20.3 Write end-to-end integration tests
    - Test complete pipeline from Bronze to Gold
    - Verify data quality, lineage, monitoring
    - Test error handling and recovery scenarios
    - _Requirements: All_

- [ ] 21. Final checkpoint - Ensure complete system works
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- All tasks are required for comprehensive implementation
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties
- Unit tests validate specific examples and edge cases
- Implementation follows the medallion architecture: Bronze → Silver → Gold
- All Glue jobs use PySpark with Hypothesis for property-based testing
