# Implementation Plan: Redshift Loading System

## Overview

Este plan de implementación cubre el desarrollo del sistema de carga incremental desde las capas Silver/Gold del Data Lake hacia el Amazon Redshift existente de Cencosud. El sistema garantiza compatibilidad total con la infraestructura actual, implementando una estrategia de migración sin downtime mediante tablas paralelas para validación antes del cutover definitivo.

**Lenguaje de Implementación**: Python 3.11 (para Glue jobs, Lambda, y MWAA DAGs)

## Tasks

- [ ] 1. Set up project structure for Redshift loading components
  - Create directory structure: `glue/redshift-loading/`, `airflow/dags/redshift/`, `lambda/redshift-monitoring/`
  - Create shared utilities directory: `glue/shared/redshift_utils/`
  - Set up Python package structure with `__init__.py` files
  - Create requirements.txt for dependencies (boto3, psycopg2-binary, pyiceberg)
  - _Requirements: 1.1, 1.2_

- [ ] 2. Implement Iceberg Snapshot Reader
  - [ ] 2.1 Create IcebergSnapshotReader class with Glue Data Catalog integration
    - Implement `get_latest_snapshot()` to query Iceberg metadata tables
    - Implement `get_incremental_files()` to extract delta between snapshots
    - Handle Iceberg table metadata parsing and snapshot comparison
    - _Requirements: 3.1_
  
  - [ ] 2.2 Write property test for snapshot delta identification
    - **Property 4: Incremental Snapshot Delta Identification**
    - **Validates: Requirements 3.1**
  
  - [ ] 2.3 Implement manifest file generator
    - Create `generate_manifest()` to produce Redshift-compatible JSON manifest
    - Format: `{"entries": [{"url": "s3://...", "mandatory": true}]}`
    - Write manifest to S3 location accessible by Redshift
    - _Requirements: 3.2_
  
  - [ ] 2.4 Write property test for manifest file completeness
    - **Property 5: Manifest File Completeness**
    - **Validates: Requirements 3.2**

- [ ] 3. Implement Schema Compatibility Validator
  - [ ] 3.1 Create SchemaValidator class with Redshift system table queries
    - Implement `get_redshift_schema()` querying pg_table_def, pg_constraint
    - Implement `get_iceberg_schema()` from Glue Data Catalog
    - Extract distribution keys, sort keys, compression encodings
    - _Requirements: 1.2, 1.3, 2.1, 2.2, 2.3, 2.4_
  
  - [ ] 3.2 Write property test for schema metadata preservation
    - **Property 1: Schema Metadata Preservation**
    - **Validates: Requirements 1.2, 1.3, 2.1, 2.2, 2.3, 2.4**
  
  - [ ] 3.3 Implement schema compatibility validation logic
    - Create `validate_compatibility()` comparing source vs target schemas
    - Check column names, data types, nullability, constraints
    - Validate distribution/sort key compatibility
    - Return detailed ValidationResult with specific incompatibilities
    - _Requirements: 2.6, 2.7_
  
  - [ ] 3.4 Write property test for dependent object compatibility
    - **Property 2: Dependent Object Compatibility**
    - **Validates: Requirements 1.4, 2.5**

- [ ] 4. Checkpoint - Validate schema extraction and snapshot reading
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 5. Implement Data Type Mapper
  - [ ] 5.1 Create DataTypeMapper class with comprehensive type mapping
    - Implement `map_type()` for all Iceberg → Redshift type conversions
    - Handle TIMESTAMP with timezone conversions (UTC → configured TZ)
    - Implement `determine_varchar_length()` with data profiling
    - Preserve DECIMAL precision and scale
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_
  
  - [ ] 5.2 Write property test for type mapping correctness
    - **Property 3: Type Mapping Correctness**
    - **Validates: Requirements 4.1, 4.2, 4.3, 4.4, 4.5, 6.2**
  
  - [ ] 5.3 Implement NULL value handling for all data types
    - Test NULL conversion for each type mapping
    - Validate NULL constraints during conversion
    - _Requirements: 4.2_

- [ ] 6. Implement Staging Table Manager
  - [ ] 6.1 Create StagingTableManager class with DDL generation
    - Implement `create_staging_table()` with `_staging` suffix
    - Copy exact schema from production table (columns, types, constraints)
    - Preserve distribution keys, sort keys, compression encodings
    - _Requirements: 3.3, 2.6_
  
  - [ ] 6.2 Write property test for staging table schema identity
    - **Property 6: Staging Table Schema Identity**
    - **Validates: Requirements 3.3, 2.6**
  
  - [ ] 6.3 Implement staging table lifecycle management
    - Create `drop_staging_table()` for cleanup
    - Implement `get_row_count()` for validation
    - Handle staging table errors and rollback
    - _Requirements: 3.3_

- [ ] 7. Implement COPY Command Executor
  - [ ] 7.1 Create CopyExecutor class with optimized COPY commands
    - Implement `execute_copy()` using manifest files
    - Configure: FORMAT AS PARQUET, MANIFEST, GZIP, COMPUPDATE OFF, STATUPDATE OFF
    - Use IAM role authentication (no hardcoded credentials)
    - Set MAXERROR 0 for strict validation
    - _Requirements: 3.4, 5.1, 5.2, 5.3, 5.4_
  
  - [ ] 7.2 Implement COPY error handling and logging
    - Query STL_LOAD_ERRORS for detailed error information
    - Create `get_copy_errors()` to extract failed record details
    - Log errors to CloudWatch with structured format
    - _Requirements: 8.3_
  
  - [ ] 7.3 Implement connection pooling for Redshift
    - Use psycopg2 connection pool (min: 2, max: 10 connections)
    - Implement health checks and automatic reconnection
    - Configure timeouts (connection: 30s, idle: 300s)
    - _Requirements: 9.3_

- [ ] 8. Checkpoint - Validate COPY operations and staging tables
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 9. Implement Data Quality Validator
  - [ ] 9.1 Create DataQualityValidator class with comprehensive checks
    - Implement `validate_row_counts()` comparing source vs staging
    - Implement `validate_checksums()` for critical columns
    - Implement `validate_constraints()` checking NOT NULL, ranges, formats
    - Implement `validate_referential_integrity()` for foreign keys
    - _Requirements: 6.1, 6.3, 6.4, 6.5_
  
  - [ ] 9.2 Write property test for row count invariant
    - **Property 7: Row Count Invariant**
    - **Validates: Requirements 6.1**
  
  - [ ] 9.3 Write property test for checksum invariant
    - **Property 8: Checksum Invariant**
    - **Validates: Requirements 6.4**
  
  - [ ] 9.4 Write property test for constraint satisfaction
    - **Property 9: Constraint Satisfaction**
    - **Validates: Requirements 6.3**
  
  - [ ] 9.5 Write property test for referential integrity preservation
    - **Property 10: Referential Integrity Preservation**
    - **Validates: Requirements 6.5**
  
  - [ ] 9.6 Implement quality report generation
    - Create `generate_quality_report()` with all validation results
    - Include pass/fail status, violation details, anomaly detection
    - Log reports to CloudWatch and store in S3
    - _Requirements: 6.6_

- [ ] 10. Implement UPSERT Executor
  - [ ] 10.1 Create UpsertExecutor class with MERGE and DELETE+INSERT patterns
    - Implement `execute_merge()` using Redshift MERGE statement (preferred)
    - Implement `execute_delete_insert()` as fallback for older Redshift versions
    - Wrap operations in explicit transactions for atomicity
    - _Requirements: 3.6, 8.1_
  
  - [ ] 10.2 Write property test for transaction atomicity
    - **Property 11: Transaction Atomicity**
    - **Validates: Requirements 8.1, 8.2**
  
  - [ ] 10.3 Implement lock management and optimization
    - Minimize lock duration by pre-computing deltas
    - Implement `estimate_lock_duration()` based on row count
    - Handle deadlocks and lock timeouts with retry logic
    - _Requirements: 3.6_

- [ ] 11. Implement State Manager
  - [ ] 11.1 Create StateManager class with DynamoDB integration
    - Implement `get_last_snapshot()` to retrieve last processed snapshot ID
    - Implement `update_state()` to store snapshot ID, metrics, timestamps
    - Implement `mark_in_progress()` and `mark_failed()` for status tracking
    - Use DynamoDB on-demand capacity mode
    - _Requirements: 3.1_
  
  - [ ] 11.2 Implement idempotency and recovery logic
    - Check state before starting load to prevent duplicates
    - Enable recovery from partial failures using stored state
    - Support concurrent loads of different tables
    - _Requirements: 8.4_

- [ ] 12. Checkpoint - Validate data quality and UPSERT operations
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 13. Implement Materialized View Manager
  - [ ] 13.1 Create MaterializedViewManager class
    - Implement `create_view()` with DDL for common BI patterns
    - Define views: daily sales summary, order fulfillment metrics, customer analytics, inventory turnover
    - _Requirements: 7.1_
  
  - [ ] 13.2 Implement materialized view refresh logic
    - Implement `refresh_view()` with incremental refresh when possible
    - Schedule refreshes during low-usage periods (2-6 AM)
    - Monitor refresh duration and optimize slow views
    - _Requirements: 7.2, 7.3_
  
  - [ ] 13.3 Implement view usage monitoring and cleanup
    - Implement `get_view_usage()` querying SVV_MV_INFO
    - Implement `drop_unused_views()` for views with zero usage >30 days
    - _Requirements: 7.4, 7.5_

- [ ] 14. Implement Error Handling and Recovery
  - [ ] 14.1 Create error handling framework
    - Implement retry logic with exponential backoff (1s, 2s, 4s)
    - Handle connection errors, transaction errors, COPY errors
    - Implement automatic rollback on failures
    - _Requirements: 8.1, 8.2, 8.4_
  
  - [ ] 14.2 Implement error record routing
    - Create error tables with schema: error_type, error_message, timestamp, source_data
    - Route failed records to error tables for manual review
    - _Requirements: 8.5_
  
  - [ ] 14.3 Write property test for error record routing
    - **Property 12: Error Record Routing**
    - **Validates: Requirements 8.5**
  
  - [ ] 14.4 Implement structured error logging
    - Log all errors to CloudWatch with JSON format
    - Include: timestamp, table_name, error_category, error_type, snapshot_id, severity
    - _Requirements: 8.3_

- [ ] 15. Implement AWS Glue Job for incremental loading
  - [ ] 15.1 Create main Glue job script (glue_redshift_loader.py)
    - Orchestrate: snapshot reading → manifest generation → staging → validation → UPSERT
    - Use all implemented components (IcebergSnapshotReader, SchemaValidator, etc.)
    - Handle job parameters: table_name, target_environment, dry_run
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7_
  
  - [ ] 15.2 Implement Glue job configuration
    - Configure worker type: G.1X (4 vCPU, 16 GB RAM)
    - Set auto-scaling: 2-10 workers
    - Configure timeout: 30 minutes
    - Set up IAM role with S3, Redshift, DynamoDB, Glue Catalog permissions
    - _Requirements: 5.1, 5.2_
  
  - [ ] 15.3 Implement job monitoring and metrics
    - Emit CloudWatch metrics: load_duration, records_loaded, success_rate
    - Log job progress at each stage
    - _Requirements: 10.1_

- [ ] 16. Checkpoint - Validate end-to-end Glue job execution
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 17. Implement MWAA DAG for orchestration
  - [ ] 17.1 Create Airflow DAG (dag_redshift_loader.py)
    - Configure: schedule_interval=None (triggered by EventBridge)
    - Define tasks: check_new_snapshots → run_glue_job → validate_load → refresh_views
    - Use GlueJobOperator for Glue job execution
    - _Requirements: 3.7_
  
  - [ ] 17.2 Implement DAG task dependencies and error handling
    - Set up task dependencies with proper error handling
    - Configure retries: 3 attempts with exponential backoff
    - Implement on_failure_callback for alerting
    - _Requirements: 8.4_
  
  - [ ] 17.3 Configure DAG for multiple tables
    - Parameterize DAG for different tables (orders, products, stock, prices, stores)
    - Use Airflow Variables for table-specific configuration
    - _Requirements: 3.1_

- [ ] 18. Implement EventBridge scheduling
  - [ ] 18.1 Create EventBridge rules for DAG triggering
    - Business hours schedule: every 15 minutes (8 AM - 8 PM)
    - Off-hours schedule: every 60 minutes (8 PM - 8 AM)
    - Configure target: MWAA environment with DAG name
    - _Requirements: 3.7_
  
  - [ ] 18.2 Implement event payload for table selection
    - Pass table_name and configuration in event payload
    - Handle multiple concurrent loads for different tables
    - _Requirements: 3.1_

- [ ] 19. Implement monitoring and alerting
  - [ ] 19.1 Create CloudWatch dashboards
    - Dashboard 1: Real-time load status (current loads, success rate, duration)
    - Dashboard 2: Historical trends (daily load counts, performance over time)
    - Dashboard 3: Data freshness (last load timestamp per table)
    - Dashboard 4: Resource utilization (Glue workers, Redshift queries)
    - _Requirements: 10.3_
  
  - [ ] 19.2 Create CloudWatch alarms
    - Alarm 1: Load failures (threshold: 1 failure)
    - Alarm 2: Performance degradation (threshold: load duration >15 minutes)
    - Alarm 3: Storage capacity warnings (threshold: 80% full)
    - Alarm 4: Long-running queries (threshold: >30 minutes)
    - _Requirements: 10.2_
  
  - [ ] 19.3 Configure SNS notifications
    - Create SNS topic for critical alerts
    - Subscribe operations team email/Slack
    - Configure alarm actions to publish to SNS
    - _Requirements: 10.4_
  
  - [ ] 19.4 Implement Lambda function for monitoring
    - Create Lambda to aggregate metrics and send custom alerts
    - Monitor data quality degradation trends
    - Alert on anomalies (row count spikes, checksum failures)
    - _Requirements: 10.1, 10.2_

- [ ] 20. Implement Terraform infrastructure
  - [ ] 20.1 Create Terraform module for Glue resources
    - Define Glue job resource with script location, worker config, IAM role
    - Create Glue Data Catalog database for Iceberg tables
    - Configure Glue connections for Redshift
    - _Requirements: 1.1, 9.1, 9.2_
  
  - [ ] 20.2 Create Terraform module for DynamoDB state table
    - Define DynamoDB table with on-demand capacity
    - Configure partition key: table_name
    - Enable encryption at rest
    - _Requirements: 3.1_
  
  - [ ] 20.3 Create Terraform module for EventBridge rules
    - Define EventBridge rules for business hours and off-hours schedules
    - Configure targets pointing to MWAA environment
    - _Requirements: 3.7_
  
  - [ ] 20.4 Create Terraform module for IAM roles and policies
    - GlueRedshiftLoadRole: Glue → Redshift + S3 + DynamoDB + Glue Catalog
    - MWAARedshiftRole: MWAA → Glue + Redshift + DynamoDB
    - RedshiftS3Role: Redshift → S3 read for COPY
    - Apply least-privilege principle
    - _Requirements: 9.1, 9.6_
  
  - [ ] 20.5 Create Terraform module for CloudWatch resources
    - Define log groups with retention policies (7 days operational, 30 days audit)
    - Create metric filters for custom metrics
    - Define alarms with SNS actions
    - Create dashboards with JSON definitions
    - _Requirements: 10.1, 10.2, 10.3_
  
  - [ ] 20.6 Create Terraform module for SNS topics
    - Define SNS topic for critical alerts
    - Configure email/Slack subscriptions
    - Set up access policies
    - _Requirements: 10.4_

- [ ] 21. Checkpoint - Validate complete infrastructure deployment
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 22. Implement Power BI integration optimizations
  - [ ] 22.1 Create optimized views for Power BI consumption
    - Define views with pre-aggregated data for common dashboards
    - Optimize column selection and data types for DirectQuery
    - Implement row-level security where required
    - _Requirements: 11.2, 11.3_
  
  - [ ] 22.2 Configure Redshift for Power BI connectivity
    - Document connection strings and authentication methods
    - Optimize WLM queues for Power BI queries
    - Configure query result caching
    - _Requirements: 11.1, 11.4_
  
  - [ ] 22.3 Create Power BI connection documentation
    - Document connection setup steps
    - Provide best practices for DirectQuery vs Import mode
    - Include troubleshooting guide
    - _Requirements: 11.5_

- [ ] 23. Implement backup and disaster recovery
  - [ ] 23.1 Configure automated Redshift backups
    - Enable automated snapshots with 7-day retention
    - Configure cross-region snapshot copies
    - _Requirements: 12.1, 12.2_
  
  - [ ] 23.2 Create backup testing procedures
    - Document monthly backup restoration test procedure
    - Create scripts for automated restoration testing
    - _Requirements: 12.3_
  
  - [ ] 23.3 Document RTO and RPO
    - Define recovery time objectives for each component
    - Define recovery point objectives for data
    - Create disaster recovery runbook
    - _Requirements: 12.4, 12.6_

- [ ] 24. Implement cost optimization
  - [ ] 24.1 Configure Redshift Serverless auto-pause
    - Set idle timeout for auto-pause during low usage
    - Configure auto-resume on query
    - _Requirements: 13.1_
  
  - [ ] 24.2 Implement S3 lifecycle policies
    - Transition manifest files to Glacier after 30 days
    - Delete old error logs after 90 days
    - _Requirements: 13.2_
  
  - [ ] 24.3 Create cost monitoring dashboard
    - Track Glue job costs (worker hours)
    - Track Redshift compute and storage costs
    - Track S3 storage and request costs
    - Set up budget alerts
    - _Requirements: 13.5, 13.6_

- [ ] 25. Create operational documentation
  - [ ] 25.1 Create daily operations runbook
    - Document morning checks (9 AM routine)
    - Document load monitoring procedures
    - Include troubleshooting guide for common issues
    - _Requirements: 10.1, 10.2_
  
  - [ ] 25.2 Create incident response procedures
    - Document severity levels and response times
    - Define escalation paths
    - Create incident templates
    - _Requirements: 8.6_
  
  - [ ] 25.3 Create deployment and migration guide
    - Document parallel validation phase (Phase 1)
    - Document cutover preparation (Phase 2)
    - Document production cutover procedure (Phase 3)
    - Include rollback procedures
    - _Requirements: 1.1, 1.5, 1.6, 1.7_

- [ ] 26. Final checkpoint - End-to-end validation
  - Run complete load cycle for all tables
  - Validate data quality reports
  - Verify monitoring and alerting
  - Confirm backup procedures
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- All tasks are required for comprehensive implementation
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation at key milestones
- Property tests validate universal correctness properties (minimum 100 iterations each)
- Unit tests validate specific examples and edge cases
- Implementation uses Python 3.11 for all components (Glue, Lambda, MWAA)
- Terraform manages all infrastructure with local state (no remote backend for free tier)
- Parallel validation phase allows testing without impacting production BI systems
