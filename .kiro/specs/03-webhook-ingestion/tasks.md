# Implementation Plan: Webhook Ingestion System

## Overview

This implementation plan covers the development of a serverless webhook ingestion system using AWS API Gateway, Lambda, Kinesis Firehose, and S3. The system receives real-time event notifications from Janis, validates their authenticity, enriches the data by calling Janis APIs, and streams the enriched data to the Bronze layer of the Data Lake.

The implementation follows a modular approach with Terraform for infrastructure, Python for Lambda functions, and comprehensive testing including property-based tests using Hypothesis.

## Tasks

- [ ] 1. Set up project structure and Terraform configuration
  - Create directory structure: `terraform/modules/webhook-ingestion/`, `lambda/webhook-processor/`, `lambda/data-enrichment/`
  - Configure Terraform backend (local state for free tier)
  - Set up AWS provider with version constraints (~> 5.0)
  - Create shared variables file for common configuration
  - Add .gitignore for state files and credentials
  - _Requirements: 10.1, 10.2_

- [ ] 2. Implement Secrets Manager module
  - [ ] 2.1 Create Terraform module for AWS Secrets Manager
    - Define secrets for HMAC shared key and Janis API key
    - Configure monthly rotation for webhook shared secret
    - Set up IAM policies for Lambda access
    - _Requirements: 2.2, 2.5_
  
  - [ ]* 2.2 Write property test for secret rotation
    - **Property 1: Secret rotation maintains availability**
    - **Validates: Requirements 2.5**

- [ ] 3. Implement S3 Bronze layer infrastructure
  - [ ] 3.1 Create S3 bucket module for Bronze layer
    - Configure bucket with encryption (SSE-S3)
    - Set up lifecycle policies (IA after 30 days, Glacier after 90 days, delete after 365 days)
    - Enable versioning for error bucket
    - Block all public access
    - Configure cross-region replication to us-west-2
    - _Requirements: 6.1, 6.5, 11.4_
  
  - [ ] 3.2 Create S3 error bucket for failed deliveries
    - Configure with same security settings as Bronze bucket
    - Set up 14-day retention policy
    - _Requirements: 5.6_

- [ ] 4. Implement Lambda signature validation function
  - [ ] 4.1 Create Python Lambda function for HMAC-SHA256 validation
    - Implement signature extraction from X-Janis-Signature header
    - Retrieve secrets from Secrets Manager (current and previous versions)
    - Implement constant-time signature comparison
    - Add secret caching with 5-minute TTL
    - Return 401 for invalid signatures
    - Log authentication failures
    - _Requirements: 2.1, 2.3, 2.4, 2.6_
  
  - [ ]* 4.2 Write property test for signature validation
    - **Property 1: Signature validation rejects invalid requests**
    - **Validates: Requirements 2.1, 2.3, 2.6**
  
  - [ ]* 4.3 Write property test for validation performance
    - **Property 9: Signature validation completes within 100ms**
    - **Validates: Requirements 2.4**
  
  - [ ] 4.4 Create Terraform module for validator Lambda
    - Configure runtime (Python 3.11), memory (256 MB), timeout (5 seconds)
    - Set up environment variables for secret ARNs
    - Configure IAM role with Secrets Manager read access
    - Deploy in VPC private subnets
    - _Requirements: 2.1, 2.4_

- [ ] 5. Implement Lambda data enrichment function
  - [ ] 5.1 Create Python Lambda function for data enrichment
    - Parse webhook payload to extract event_type and entity_id
    - Implement API endpoint mapping for different event types
    - Call Janis API with exponential backoff retry (max 3 attempts)
    - Fetch additional data for order events (order items)
    - Merge webhook data with API responses
    - Add metadata: ingestion_timestamp, source_type, schema_version
    - _Requirements: 4.2, 4.3, 4.4, 4.5_
  
  - [ ] 5.2 Implement error handling and DLQ routing
    - Handle malformed JSON with 400 Bad Request
    - Implement retry logic for Janis API timeouts
    - Route failed messages to SQS DLQ after 3 attempts
    - Include error details in DLQ messages
    - _Requirements: 4.4, 7.2, 7.3, 7.4_
  
  - [ ]* 5.3 Write property test for data enrichment
    - **Property 4: Enrichment includes complete entity data**
    - **Validates: Requirements 4.3, 4.5**
  
  - [ ]* 5.4 Write property test for processing timeout
    - **Property 2: Valid webhooks are processed within timeout**
    - **Validates: Requirements 4.6**
  
  - [ ]* 5.5 Write property test for DLQ routing
    - **Property 5: Failed processing routes to Dead Letter Queue**
    - **Validates: Requirements 7.2, 7.3, 7.4**
  
  - [ ] 5.6 Create Terraform module for enrichment Lambda
    - Configure runtime (Python 3.11), memory (512 MB), timeout (30 seconds)
    - Set up environment variables for Janis API URL and configuration
    - Configure IAM role with Secrets Manager and Kinesis access
    - Set up provisioned concurrency (50 instances) for peak hours
    - Configure SQS DLQ with 14-day retention
    - _Requirements: 4.6, 7.1, 7.2_

- [ ] 6. Checkpoint - Validate Lambda functions
  - Test signature validation with valid and invalid signatures
  - Test data enrichment with mock Janis API responses
  - Verify error handling and DLQ routing
  - Ensure all tests pass, ask the user if questions arise

- [ ] 7. Implement Kinesis Data Firehose
  - [ ] 7.1 Create Terraform module for Kinesis Firehose delivery streams
    - Configure buffer size (5 MB) and interval (60 seconds)
    - Enable GZIP compression
    - Set up dynamic partitioning by event_type and date
    - Configure S3 destination with partitioning pattern
    - Set up error handling with retry (1 hour) and error bucket routing
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6_
  
  - [ ]* 7.2 Write property test for Firehose partitioning
    - **Property 6: Firehose partitions data by event type and date**
    - **Validates: Requirements 5.4**
  
  - [ ]* 7.3 Write property test for buffering behavior
    - **Property 11: Firehose buffers data based on size or time thresholds**
    - **Validates: Requirements 5.2**
  
  - [ ]* 7.4 Write property test for metadata inclusion
    - **Property 7: All stored data includes required metadata**
    - **Validates: Requirements 6.3**

- [ ] 8. Implement API Gateway REST API
  - [ ] 8.1 Create Terraform module for API Gateway
    - Define REST API with event-specific endpoints
    - Configure POST method for each endpoint
    - Set up Lambda proxy integration with enrichment function
    - Enable request validation with JSON schema
    - Configure throttling (1,000 req/s per endpoint, 2,000 burst)
    - Implement per-IP rate limiting (100 req/min)
    - _Requirements: 1.1, 1.2, 3.1, 3.2, 3.5_
  
  - [ ] 8.2 Configure API Gateway security and logging
    - Set up resource policy for IP whitelisting
    - Configure custom domain (webhook.cencosud-datalake.com)
    - Enable full request/response logging to CloudWatch
    - Add rate limit headers to responses
    - _Requirements: 1.5, 2.7, 3.6_
  
  - [ ]* 8.3 Write property test for rate limiting
    - **Property 3: Rate limiting enforces configured thresholds**
    - **Validates: Requirements 3.1, 3.4**
  
  - [ ]* 8.4 Write property test for API Gateway response time
    - **Property 10: API Gateway responds within 5 seconds**
    - **Validates: Requirements 1.3**
  
  - [ ]* 8.5 Write property test for invalid payload rejection
    - **Property 8: Invalid payloads are rejected with detailed errors**
    - **Validates: Requirements 9.2, 9.4**

- [ ] 9. Implement data validation
  - [ ] 9.1 Create JSON schema definitions for webhook payloads
    - Define schemas for each event type
    - Specify required fields and data types
    - Add format validation for timestamps (ISO 8601)
    - _Requirements: 9.1, 9.2, 9.3_
  
  - [ ] 9.2 Implement validation in Lambda enrichment function
    - Validate payload structure against JSON schema
    - Verify required fields are present and not null
    - Validate data types and formats
    - Return detailed error messages for validation failures
    - _Requirements: 9.1, 9.2, 9.3, 9.4_
  
  - [ ]* 9.3 Write unit tests for validation logic
    - Test valid payloads pass validation
    - Test missing required fields are rejected
    - Test invalid data types are rejected
    - Test malformed timestamps are rejected
    - _Requirements: 9.1, 9.2, 9.3_

- [ ] 10. Implement CloudWatch monitoring and alarms
  - [ ] 10.1 Create CloudWatch metrics and dashboards
    - Configure custom metrics for webhook processing
    - Create dashboard with throughput, latency, and error panels
    - Add resource utilization panel
    - Set up X-Ray tracing for distributed tracing
    - _Requirements: 8.1, 8.3_
  
  - [ ] 10.2 Configure CloudWatch alarms
    - Create critical alarms (error rate > 5%, DLQ messages > 0, 5xx errors)
    - Create warning alarms (error rate > 2%, latency > 5s)
    - Set up SNS topics for notifications
    - Configure alarm actions for different severity levels
    - _Requirements: 8.2, 8.4_
  
  - [ ]* 10.3 Write unit tests for monitoring configuration
    - Verify all required metrics are configured
    - Verify alarm thresholds are correct
    - Test SNS notification delivery
    - _Requirements: 8.1, 8.2_

- [ ] 11. Checkpoint - Integration testing
  - Deploy complete infrastructure to dev environment
  - Send test webhooks through API Gateway
  - Verify end-to-end flow: API Gateway → Lambda → Kinesis → S3
  - Verify partitioning and compression in S3
  - Test error scenarios and DLQ routing
  - Ensure all tests pass, ask the user if questions arise

- [ ] 12. Implement high availability and disaster recovery
  - [ ] 12.1 Configure multi-AZ deployment
    - Verify API Gateway multi-AZ deployment
    - Verify Lambda multi-AZ execution
    - Verify Kinesis Firehose multi-AZ replication
    - _Requirements: 11.1, 11.3, 11.6_
  
  - [ ] 12.2 Set up cross-region replication
    - Configure S3 cross-region replication to us-west-2
    - Set up replication for Bronze and error buckets
    - Verify replication lag < 15 minutes
    - _Requirements: 11.4_
  
  - [ ]* 12.3 Write property test for multi-AZ availability
    - **Property 12: System maintains multi-AZ availability**
    - **Validates: Requirements 11.1, 11.6**

- [ ] 13. Implement operational tooling
  - [ ] 13.1 Create DLQ replay Lambda function
    - Implement function to retrieve messages from DLQ
    - Reprocess messages through enrichment pipeline
    - Track replay success/failure
    - _Requirements: 7.6_
  
  - [ ] 13.2 Create operational scripts
    - Script to view recent webhooks from CloudWatch Logs
    - Script to check DLQ message count
    - Script to trigger secret rotation
    - Script to backup Terraform state
    - _Requirements: 2.5, 7.6_
  
  - [ ]* 13.3 Write unit tests for operational tooling
    - Test DLQ replay function with sample messages
    - Test scripts with mock AWS responses
    - _Requirements: 7.6_

- [ ] 14. Implement security hardening
  - [ ] 14.1 Configure VPC networking
    - Deploy Lambda functions in private subnets
    - Set up VPC endpoints for AWS services
    - Configure security groups for outbound HTTPS only
    - _Requirements: 2.7_
  
  - [ ] 14.2 Implement additional security controls
    - Configure AWS WAF rules (optional)
    - Set up GuardDuty for threat detection
    - Enable CloudTrail logging for all API calls
    - Configure S3 access logging
    - _Requirements: 2.6, 2.7_

- [ ] 15. Performance optimization
  - [ ] 15.1 Optimize Lambda functions
    - Implement connection pooling for Janis API calls
    - Optimize secret caching strategy
    - Minimize deployment package size
    - Tune memory allocation based on profiling
    - _Requirements: 10.5, 10.6_
  
  - [ ] 15.2 Configure provisioned concurrency
    - Set up provisioned concurrency for peak hours (9 AM - 6 PM)
    - Configure auto-scaling for Lambda concurrency
    - _Requirements: 10.3_
  
  - [ ]* 15.3 Write performance tests
    - Test Lambda cold start times
    - Test API Gateway latency under load
    - Test Kinesis Firehose throughput
    - _Requirements: 10.5, 10.6_

- [ ] 16. Create deployment automation
  - [ ] 16.1 Create Terraform deployment scripts
    - Script for environment initialization
    - Script for plan and apply with credential handling
    - Script for state backup before changes
    - Script for rollback procedures
    - _Requirements: 10.1, 10.2_
  
  - [ ] 16.2 Set up CI/CD pipeline configuration
    - Define deployment stages (dev → staging → prod)
    - Configure automated testing in pipeline
    - Set up manual approval gates for production
    - Document deployment procedures
    - _Requirements: 10.1, 10.2_

- [ ] 17. Documentation and runbooks
  - [ ] 17.1 Create operational runbooks
    - Runbook for viewing recent webhooks
    - Runbook for handling DLQ messages
    - Runbook for secret rotation
    - Runbook for troubleshooting common issues
    - _Requirements: 8.1, 8.2_
  
  - [ ] 17.2 Create architecture documentation
    - Document component interactions
    - Create deployment diagrams
    - Document security controls
    - Document disaster recovery procedures
    - _Requirements: 11.1, 11.2, 11.7_

- [ ] 18. Final checkpoint - Production readiness
  - Review all security controls are in place
  - Verify monitoring and alerting is configured
  - Test disaster recovery procedures
  - Validate performance meets requirements
  - Complete security assessment
  - Ensure all tests pass, ask the user if questions arise

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties using Hypothesis
- Unit tests validate specific examples and edge cases
- Infrastructure is deployed using Terraform with local state management
- All credentials must be passed as variables, never hardcoded
- Lambda functions use Python 3.11 runtime
- The system is designed for serverless, auto-scaling architecture
