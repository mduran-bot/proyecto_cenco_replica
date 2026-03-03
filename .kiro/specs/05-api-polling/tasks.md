# Implementation Plan: API Polling System

## Overview

Este plan implementa un sistema de polling periódico event-driven que utiliza Amazon EventBridge para gatillar flujos de trabajo de Apache Airflow (MWAA). El sistema consulta las APIs de Janis de manera programada, actuando como red de seguridad complementaria a los webhooks.

## Tasks

- [ ] 1. Setup project structure and configuration
  - Create directory structure for Terraform modules, Airflow DAGs, and Python plugins
  - Setup .gitignore for Terraform state files and credentials
  - Create environment-specific configuration files (dev, staging, prod)
  - _Requirements: 12.1, 12.2_

- [ ] 2. Implement Terraform infrastructure for DynamoDB Control Table
  - [ ] 2.1 Create DynamoDB table module with partition key polling_type
    - Define table schema with all required attributes (last_execution_timestamp, lock_acquired_at, etc.)
    - Configure PAY_PER_REQUEST billing mode
    - Enable DynamoDB streams for change tracking
    - _Requirements: 4.1, 4.8_
  
  - [ ]* 2.2 Write property test for Control Table lock mechanism
    - **Property 13: Concurrent Execution Prevention**
    - **Validates: Requirements 4.8**
  
  - [ ] 2.3 Create IAM policies for DynamoDB access
    - Define read/write permissions for MWAA execution role
    - Apply least privilege principle
    - _Requirements: 4.1_

- [ ] 3. Implement Terraform infrastructure for EventBridge scheduling
  - [ ] 3.1 Create EventBridge rules module for all polling types
    - Define rules for orders (5 min), products (1 hour), stock (10 min), prices (30 min), stores (24 hours)
    - Configure event payload with polling_type, execution_time, rule_name
    - Set up retry policy with exponential backoff
    - _Requirements: 1.1, 1.2, 1.3, 1.4_
  
  - [ ]* 3.2 Write property test for EventBridge trigger delivery
    - **Property 1: EventBridge Trigger Delivery**
    - **Validates: Requirements 1.2, 1.3**
  
  - [ ] 3.3 Create IAM role for EventBridge to invoke MWAA
    - Define permissions to trigger MWAA DAG executions
    - _Requirements: 1.2_
  
  - [ ] 3.4 Configure CloudWatch integration for EventBridge monitoring
    - Set up metrics for TriggeredRules, FailedInvocations, ThrottledRules
    - _Requirements: 1.5_

- [ ] 4. Implement Terraform infrastructure for MWAA environment
  - [ ] 4.1 Create MWAA environment module
    - Configure environment class mw1.small with auto-scaling (1-3 workers)
    - Set Apache Airflow version 2.7.2 with Python 3.11
    - Deploy in private subnets with VPC connectivity
    - _Requirements: 2.1, 2.2, 2.3, 2.4_
  
  - [ ] 4.2 Create S3 bucket for DAGs, plugins, and logs
    - Configure bucket with encryption and versioning
    - Set up folder structure (dags/, plugins/, requirements.txt, logs/)
    - _Requirements: 2.5_
  
  - [ ] 4.3 Configure MWAA IAM execution role
    - Grant access to S3, Secrets Manager, Systems Manager, Kinesis Firehose, DynamoDB, CloudWatch
    - Apply least privilege principle
    - _Requirements: 2.6_
  
  - [ ] 4.4 Enable MWAA to accept EventBridge triggers
    - Configure MWAA to process EventBridge event metadata in DAG context
    - _Requirements: 2.8, 2.9_

- [ ] 5. Implement Systems Manager Parameter Store configuration
  - [ ] 5.1 Create Terraform module for SSM parameters
    - Define parameters for API configuration (base_url, rate_limit, timeout, page_size)
    - Define parameters for retry policy (max_attempts, backoff_base)
    - Define parameters for Firehose streams (orders, products, stock, prices, stores)
    - Define parameters for EventBridge schedules
    - Define parameters for monitoring (alert_email, SNS topics)
    - Define parameters for performance tuning (max_workers, circuit_breaker, lock_timeout)
    - _Requirements: 12.1_
  
  - [ ]* 5.2 Write property test for configuration reload
    - **Property 14: Configuration Reload**
    - **Validates: Requirements 12.3**

- [ ] 6. Implement Secrets Manager for API credentials
  - [ ] 6.1 Create Terraform module for Secrets Manager
    - Define secret for Janis API credentials (api_key, client_id, client_secret)
    - Enable automatic rotation (90 days)
    - Configure encryption with KMS
    - _Requirements: 2.6_

- [ ] 7. Checkpoint - Validate infrastructure deployment
  - Ensure all Terraform modules deploy successfully
  - Verify MWAA environment is accessible
  - Confirm EventBridge rules are created (but disabled)
  - Validate DynamoDB Control Table exists
  - Ask the user if questions arise

- [ ] 8. Implement Python plugin for configuration management
  - [ ] 8.1 Create ConfigManager class
    - Implement get_parameter() with caching (5-minute TTL)
    - Implement get_all_parameters() for bulk loading
    - Implement validate_configuration() for startup validation
    - _Requirements: 12.3, 12.4_
  
  - [ ]* 8.2 Write unit tests for ConfigManager
    - Test parameter caching behavior
    - Test cache expiration and reload
    - Test validation logic for numeric parameters

- [ ] 9. Implement Python plugin for Janis API client
  - [ ] 9.1 Create JanisAPIClient class with rate limiting
    - Implement sliding window rate limiter (100 requests per minute)
    - Configure HTTP session with connection pooling (10 pools, 20 max connections)
    - Implement retry strategy with exponential backoff (1s, 2s, 4s)
    - Handle HTTP status codes (200, 429, 401/403, 500/502/503, 404)
    - Implement 30-second timeout per request
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_
  
  - [ ]* 9.2 Write property test for rate limit compliance
    - **Property 3: Rate Limit Compliance**
    - **Validates: Requirements 5.1**
  
  - [ ]* 9.3 Write property test for retry backoff progression
    - **Property 4: Retry Backoff Progression**
    - **Validates: Requirements 5.2**
  
  - [ ]* 9.4 Write unit tests for API client
    - Test timeout handling
    - Test connection pooling configuration
    - Test various HTTP status code responses

- [ ] 10. Implement Python plugin for pagination handling
  - [ ] 10.1 Create fetch_paginated_data() function
    - Implement pagination with limit/offset parameters (page size 100)
    - Parse pagination metadata (total_count, has_more, next_offset)
    - Implement circuit breaker (max 1000 pages)
    - Process each page immediately (streaming approach)
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6_
  
  - [ ]* 10.2 Write property test for pagination completeness
    - **Property 5: Pagination Completeness**
    - **Validates: Requirements 6.3**
  
  - [ ]* 10.3 Write property test for circuit breaker protection
    - **Property 6: Circuit Breaker Protection**
    - **Validates: Requirements 6.5**
  
  - [ ]* 10.4 Write unit tests for pagination
    - Test handling of empty pages
    - Test pagination metadata parsing

- [ ] 11. Implement Python plugin for data enrichment
  - [ ] 11.1 Create DataEnrichmentEngine class
    - Implement enrich_orders() with parallel order items fetching
    - Implement enrich_products() with parallel SKU fetching
    - Use ThreadPoolExecutor with 5 workers
    - Handle missing related entities gracefully
    - Respect API rate limits across threads
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6_
  
  - [ ]* 11.2 Write property test for data enrichment completeness
    - **Property 7: Data Enrichment Completeness**
    - **Validates: Requirements 7.1**
  
  - [ ]* 11.3 Write unit tests for enrichment engine
    - Test parallel processing behavior
    - Test graceful handling of missing entities

- [ ] 12. Implement Python plugin for data validation
  - [ ] 12.1 Create DataValidationEngine class
    - Implement validate_records() with JSON schema validation
    - Implement duplicate detection by record ID
    - Validate required fields are present and not null
    - Validate data types and formats (dates, IDs, numeric ranges)
    - Generate data quality metrics (validation_failure_rate, duplicate_rate, completeness_score)
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5, 8.6_
  
  - [ ]* 12.2 Write property test for schema validation
    - **Property 8: Schema Validation**
    - **Validates: Requirements 8.1, 8.2**
  
  - [ ]* 12.3 Write property test for duplicate detection
    - **Property 9: Duplicate Detection**
    - **Validates: Requirements 8.4**
  
  - [ ]* 12.4 Write unit tests for validation engine
    - Test business rule validation
    - Test data quality metrics calculation

- [ ] 13. Implement Python plugin for Control Table management
  - [ ] 13.1 Create ControlTableManager class
    - Implement acquire_lock() with conditional update for atomicity
    - Implement release_lock() to clear lock fields
    - Implement calculate_query_window() for incremental queries with 1-minute overlap
    - Implement update_last_timestamp() for state persistence
    - Handle timezone conversions (UTC for all timestamps)
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7, 4.8_
  
  - [ ]* 13.2 Write property test for incremental query correctness
    - **Property 2: Incremental Query Correctness**
    - **Validates: Requirements 4.2, 4.3**
  
  - [ ]* 13.3 Write property test for control table update atomicity
    - **Property 12: Control Table Update Atomicity**
    - **Validates: Requirements 4.5**
  
  - [ ]* 13.4 Write property test for concurrent execution prevention
    - **Property 13: Concurrent Execution Prevention**
    - **Validates: Requirements 4.8**

- [ ] 14. Implement Python plugin for Kinesis Firehose delivery
  - [ ] 14.1 Create FirehoseDeliveryManager class
    - Implement deliver_records() with batching (500 records per batch)
    - Implement metadata enrichment (source_type, polling_timestamp, dag_run_id, api_endpoint, eventbridge_rule, execution_time)
    - Implement retry logic for failed deliveries (3 attempts with exponential backoff)
    - Implement DLQ routing for persistent failures
    - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5, 9.6_
  
  - [ ]* 14.2 Write property test for metadata enrichment
    - **Property 10: Metadata Enrichment**
    - **Validates: Requirements 9.2**
  
  - [ ]* 14.3 Write property test for batch size compliance
    - **Property 11: Batch Size Compliance**
    - **Validates: Requirements 9.3**
  
  - [ ]* 14.4 Write unit tests for Firehose delivery
    - Test retry logic for failed deliveries
    - Test DLQ routing

- [ ] 15. Checkpoint - Validate all Python plugins
  - Ensure all plugins are implemented and tested
  - Verify plugins can be imported without errors
  - Run all unit tests and property tests
  - Ask the user if questions arise

- [ ] 16. Implement DAG for order polling
  - [ ] 16.1 Create dag_poll_orders.py
    - Configure DAG with schedule_interval=None (EventBridge triggered)
    - Set default_args (retries=3, retry_delay with exponential backoff, timeout=30 minutes)
    - Create task: validate_event (validate EventBridge payload)
    - Create task: acquire_lock (try to acquire lock in Control Table)
    - Create task: get_last_timestamp (read last execution timestamp)
    - Create task: poll_api (fetch orders with pagination)
    - Create task: enrich_data (fetch order items)
    - Create task: validate_data (validate and deduplicate)
    - Create task: send_to_firehose (deliver to Kinesis Firehose)
    - Create task: update_control_table (update timestamp and release lock)
    - Define task dependencies
    - _Requirements: 3.1, 3.6, 3.7, 3.8_
  
  - [ ]* 16.2 Write integration test for order polling DAG
    - Test complete polling cycle from EventBridge trigger to Firehose delivery
    - Test incremental query logic with Control Table

- [ ] 17. Implement DAG for product polling
  - [ ] 17.1 Create dag_poll_products.py
    - Follow same structure as order polling DAG
    - Configure for product-specific enrichment (fetch SKUs)
    - _Requirements: 3.2, 3.6_
  
  - [ ]* 17.2 Write integration test for product polling DAG

- [ ] 18. Implement DAG for stock polling
  - [ ] 18.1 Create dag_poll_stock.py
    - Follow same structure as order polling DAG
    - No enrichment required for stock data
    - _Requirements: 3.3, 3.6_

- [ ] 19. Implement DAG for price polling
  - [ ] 19.1 Create dag_poll_prices.py
    - Follow same structure as order polling DAG
    - No enrichment required for price data
    - _Requirements: 3.4, 3.6_

- [ ] 20. Implement DAG for store polling
  - [ ] 20.1 Create dag_poll_stores.py
    - Follow same structure as order polling DAG
    - No enrichment required for store data
    - _Requirements: 3.5, 3.6_

- [ ] 21. Create requirements.txt for MWAA
  - [ ] 21.1 Define Python dependencies
    - Add boto3, requests, hypothesis (for property testing)
    - Add jsonschema for data validation
    - Add psutil for resource monitoring
    - Pin versions for reproducibility

- [ ] 22. Implement CloudWatch monitoring and alarms
  - [ ] 22.1 Create Terraform module for CloudWatch alarms
    - Create alarm for DAG execution failures
    - Create alarm for API error rate > 10%
    - Create alarm for data volume anomalies > 50% deviation
    - Create alarm for execution time > 4 minutes (orders)
    - Create alarm for EventBridge rule failures
    - Create alarm for EventBridge trigger delay > 5 minutes
    - Configure SNS topics for notifications (critical, warning, info)
    - _Requirements: 11.2_
  
  - [ ] 22.2 Implement custom CloudWatch metrics in DAGs
    - Publish DAGExecutionDuration, DAGExecutionSuccess
    - Publish RecordsRetrieved, APIResponseTime, APIErrorRate
    - Publish DataQualityScore, FirehoseDeliverySuccess
    - Publish EventBridgeTriggerLatency
    - _Requirements: 11.1_

- [ ] 23. Implement error handling and recovery mechanisms
  - [ ] 23.1 Add comprehensive error handling to all DAG tasks
    - Handle network errors with retry and exponential backoff
    - Handle API authentication errors (401/403) with immediate alert
    - Handle rate limiting (429) with Retry-After header
    - Handle API server errors (500/502/503) with retry
    - Handle data validation errors with logging and continuation
    - Handle Firehose delivery failures with retry and DLQ
    - Handle Control Table lock conflicts with graceful exit
    - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5_
  
  - [ ]* 23.2 Write unit tests for error handling
    - Test each error category and recovery action

- [ ] 24. Implement performance optimizations
  - [ ] 24.1 Add connection pooling to API client
    - Configure HTTPAdapter with pool_connections=10, pool_maxsize=20
    - _Requirements: 13.3_
  
  - [ ] 24.2 Implement streaming approach for pagination
    - Process each page immediately to minimize memory usage
    - Stream records to Firehose in batches
    - _Requirements: 13.5_
  
  - [ ] 24.3 Add resource utilization monitoring
    - Publish CPU, memory, and network metrics
    - _Requirements: 13.7_
  
  - [ ]* 24.4 Write property test for performance SLA compliance
    - **Property 15: Performance SLA Compliance**
    - **Validates: Requirements 13.1, 13.2**

- [ ] 25. Create deployment scripts
  - [ ] 25.1 Create Terraform deployment script
    - Script to initialize, plan, and apply Terraform changes
    - Include backup of state files
    - Support environment-specific deployments (dev, staging, prod)
  
  - [ ] 25.2 Create DAG deployment script
    - Script to upload DAGs, plugins, and requirements.txt to S3
    - Validate DAG syntax before upload
    - Support rollback to previous versions

- [ ] 26. Create JSON schemas for data validation
  - [ ] 26.1 Define JSON schemas for all entity types
    - Create schema for orders
    - Create schema for products
    - Create schema for stock
    - Create schema for prices
    - Create schema for stores
    - _Requirements: 8.1_

- [ ] 27. Final checkpoint - End-to-end testing
  - Deploy complete infrastructure to dev environment
  - Manually trigger EventBridge rules
  - Verify DAGs execute successfully
  - Verify data flows to Kinesis Firehose
  - Verify CloudWatch metrics and alarms
  - Test error handling and recovery scenarios
  - Validate performance meets SLA targets
  - Ask the user if questions arise

- [ ] 28. Documentation and runbooks
  - [ ] 28.1 Create operational runbook
    - Document manual DAG rerun procedure
    - Document Control Table reset procedure
    - Document EventBridge rule enable/disable procedure
    - Document data replay procedure
  
  - [ ] 28.2 Create troubleshooting guide
    - Document common issues and solutions
    - Document debugging procedures
    - Document backup and recovery procedures

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties using Hypothesis with minimum 100 iterations
- Unit tests validate specific examples and edge cases
- All Python code should follow PEP 8 style guidelines
- All Terraform code should follow HashiCorp style guidelines
- Infrastructure should be deployed in order: DynamoDB → EventBridge → MWAA → Monitoring
- DAGs should be tested individually before enabling EventBridge triggers
