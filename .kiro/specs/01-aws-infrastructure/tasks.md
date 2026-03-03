# Implementation Plan: AWS Infrastructure

## Overview

This implementation plan creates the complete AWS infrastructure for the Janis-Cencosud data integration platform using Terraform. The infrastructure follows a single-AZ deployment pattern with reserved CIDR blocks for future multi-AZ expansion. All resources will be deployed using Infrastructure as Code principles with proper security, monitoring, and tagging strategies.

## Tasks

- [x] 1. Set up Terraform project structure and configuration
  - Create directory structure: terraform/environments/{dev,staging,prod}, terraform/modules/, terraform/shared/
  - Create backend.tf for local state management (no remote backend for free tier)
  - Create providers.tf with AWS provider ~> 5.0 configuration
  - Create variables.tf with common variables (aws_region, environment, project_name, etc.)
  - Add .gitignore to exclude terraform.tfstate, .terraform/, credentials.tfvars
  - _Requirements: 8.1, 8.2_

- [x] 2. Implement VPC module
  - [x] 2.1 Create VPC with CIDR 10.0.0.0/16
    - Enable DNS resolution and DNS hostnames
    - Configure IPv4 support
    - Apply mandatory tags (Project, Environment, Component, Owner, CostCenter)
    - _Requirements: 1.1, 1.3, 1.4, 8.1_
  
  - [ ]* 2.2 Write property test for VPC CIDR validity
    - **Property 1: VPC CIDR Block Validity**
    - **Validates: Requirements 1.1**
  
  - [ ]* 2.3 Write unit tests for VPC configuration
    - Test VPC creation with correct CIDR block
    - Test DNS settings are enabled
    - Test mandatory tags are applied
    - _Requirements: 1.1, 1.3, 1.4_

- [ ] 3. Implement subnet architecture
  - [ ] 3.1 Create public subnet in us-east-1a (10.0.1.0/24)
    - Enable auto-assign public IP
    - Apply subnet tags with purpose and tier
    - _Requirements: 2.1, 2.4, 2.5_
  
  - [ ] 3.2 Create private subnet 1A in us-east-1a (10.0.10.0/24)
    - Disable auto-assign public IP
    - Tag for Redshift, MWAA, Lambda usage
    - _Requirements: 2.2, 2.4, 2.5_
  
  - [ ] 3.3 Create private subnet 2A in us-east-1a (10.0.20.0/24)
    - Disable auto-assign public IP
    - Tag for Glue ENIs usage
    - _Requirements: 2.2, 2.4, 2.5_
  
  - [ ] 3.4 Document reserved CIDR blocks for future multi-AZ expansion
    - Document Public Subnet B: 10.0.2.0/24 (us-east-1b)
    - Document Private Subnet 1B: 10.0.11.0/24 (us-east-1b)
    - Document Private Subnet 2B: 10.0.21.0/24 (us-east-1b)
    - _Requirements: 2.3, 12.3, 12.4_
  
  - [ ]* 3.5 Write property test for subnet CIDR non-overlap
    - **Property 3: Subnet CIDR Non-Overlap**
    - **Validates: Requirements 2.1, 2.2**
  
  - [ ]* 3.6 Write property test for single-AZ deployment
    - **Property 2: Single-AZ Deployment**
    - **Validates: Requirements 1.2, 2.2, 2.3**

- [ ] 4. Checkpoint - Ensure VPC and subnets are created correctly
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 5. Implement internet connectivity
  - [ ] 5.1 Create Internet Gateway and attach to VPC
    - Apply mandatory tags
    - _Requirements: 3.1_
  
  - [ ] 5.2 Create NAT Gateway in public subnet
    - Allocate and assign Elastic IP
    - Apply mandatory tags
    - Document as single point of failure
    - _Requirements: 3.2, 3.3, 12.2_
  
  - [ ] 5.3 Create route tables for public and private subnets
    - Public route table: 0.0.0.0/0 → Internet Gateway
    - Private route table: 0.0.0.0/0 → NAT Gateway
    - Associate route tables with respective subnets
    - _Requirements: 3.4_
  
  - [ ]* 5.4 Write property tests for routing configuration
    - **Property 4: Public Subnet Internet Routing**
    - **Property 5: Private Subnet NAT Routing**
    - **Validates: Requirements 3.4**

- [ ] 6. Implement VPC endpoints
  - [ ] 6.1 Create S3 Gateway Endpoint
    - Associate with all route tables
    - Apply mandatory tags
    - _Requirements: 4.1, 4.4_
  
  - [ ] 6.2 Create Interface Endpoints for AWS services
    - Create endpoints for: Glue, Secrets Manager, CloudWatch Logs, KMS, STS, EventBridge
    - Enable private DNS for all Interface Endpoints
    - Associate with private subnets
    - Apply security groups (to be created in next task)
    - Apply mandatory tags
    - _Requirements: 4.2, 4.3, 4.5_
  
  - [ ]* 6.3 Write property test for VPC endpoint service coverage
    - **Property 6: VPC Endpoint Service Coverage**
    - **Validates: Requirements 4.1, 4.2**

- [ ] 7. Checkpoint - Ensure connectivity and endpoints are configured
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 8. Implement Security Groups
  - [ ] 8.1 Create SG-API-Gateway
    - Inbound: HTTPS (443) from 0.0.0.0/0
    - Outbound: All traffic to 0.0.0.0/0
    - Apply mandatory tags
    - _Requirements: 5.1_
  
  - [ ] 8.2 Create SG-Redshift-Existing
    - Inbound: PostgreSQL (5439) from SG-Lambda, SG-MWAA, existing BI systems
    - Outbound: HTTPS (443) to VPC Endpoints only
    - Apply mandatory tags
    - _Requirements: 5.2, 11.3_
  
  - [ ] 8.3 Create SG-Lambda
    - No inbound rules
    - Outbound: PostgreSQL (5439) to SG-Redshift-Existing, HTTPS (443) to VPC Endpoints and 0.0.0.0/0
    - Apply mandatory tags
    - _Requirements: 5.3_
  
  - [ ] 8.4 Create SG-MWAA
    - Inbound: HTTPS (443) from SG-MWAA (self-reference), EventBridge triggers
    - Outbound: HTTPS (443) to VPC Endpoints and 0.0.0.0/0, PostgreSQL (5439) to SG-Redshift-Existing
    - Apply mandatory tags
    - _Requirements: 5.4_
  
  - [ ] 8.5 Create SG-Glue
    - Inbound: All TCP from SG-Glue (self-reference)
    - Outbound: HTTPS (443) to VPC Endpoints, All TCP to SG-Glue (self-reference)
    - Apply mandatory tags
    - _Requirements: 5.5_
  
  - [ ] 8.6 Create SG-EventBridge
    - Outbound: HTTPS (443) to MWAA endpoints and VPC Endpoints
    - Apply mandatory tags
    - _Requirements: 5.6_
  
  - [ ]* 8.7 Write property tests for security group configuration
    - **Property 7: Security Group Least Privilege**
    - **Property 8: Security Group Self-Reference Validity**
    - **Validates: Requirements 5.1-5.6**
  
  - [ ]* 8.8 Write unit tests for security groups
    - Test each security group has correct inbound/outbound rules
    - Test no overly permissive rules
    - _Requirements: 5.1-5.6_

- [ ] 9. Implement Network Access Control Lists (NACLs)
  - [ ] 9.1 Create Public Subnet NACL
    - Inbound: HTTPS (443) from 0.0.0.0/0, Ephemeral ports (1024-65535) from 0.0.0.0/0
    - Outbound: All traffic to 0.0.0.0/0
    - Default: Deny all other traffic
    - Associate with public subnet
    - _Requirements: 6.1, 6.3_
  
  - [ ] 9.2 Create Private Subnet NACL
    - Inbound: All traffic from 10.0.0.0/16, HTTPS (443) from 0.0.0.0/0, Ephemeral ports from 0.0.0.0/0
    - Outbound: All traffic to 10.0.0.0/16, HTTPS (443) to 0.0.0.0/0
    - Default: Deny all other traffic
    - Associate with private subnets
    - _Requirements: 6.2, 6.3_
  
  - [ ]* 9.3 Write property test for NACL stateless bidirectionality
    - **Property 9: NACL Stateless Bidirectionality**
    - **Validates: Requirements 6.4**

- [ ] 10. Checkpoint - Ensure security groups and NACLs are configured
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 11. Implement Web Application Firewall (WAF)
  - [ ] 11.1 Create WAF Web ACL for API Gateway
    - Configure default action: Allow
    - Apply mandatory tags
    - _Requirements: 7.5_
  
  - [ ] 11.2 Create rate limiting rule
    - Limit: 2,000 requests per IP in 5 minutes
    - Action: Block with 429 response code
    - Priority: 1
    - _Requirements: 7.1_
  
  - [ ] 11.3 Create geo-blocking rule
    - Allow: Peru (PE) and AWS regions
    - Action: Block other countries
    - Priority: 2
    - _Requirements: 7.2_
  
  - [ ] 11.4 Add AWS Managed Rules
    - AWSManagedRulesAmazonIpReputationList
    - AWSManagedRulesCommonRuleSet
    - AWSManagedRulesKnownBadInputsRuleSet
    - _Requirements: 7.3_
  
  - [ ] 11.5 Configure WAF logging to CloudWatch
    - Log all blocked requests with full details
    - _Requirements: 7.4_
  
  - [ ]* 11.6 Write property tests for WAF rules
    - **Property 10: WAF Rate Limit Enforcement**
    - **Property 11: WAF Geo-Blocking Enforcement**
    - **Validates: Requirements 7.1, 7.2**

- [ ] 12. Implement EventBridge configuration
  - [ ] 12.1 Create custom event bus for polling operations
    - Name: janis-cencosud-polling-bus
    - Apply mandatory tags
    - _Requirements: 9.1_
  
  - [ ] 12.2 Create scheduled rules for polling
    - Order polling: rate(5 minutes)
    - Product polling: rate(60 minutes)
    - Stock polling: rate(10 minutes)
    - Price polling: rate(30 minutes)
    - Store polling: rate(1440 minutes)
    - _Requirements: 9.2_
  
  - [ ] 12.3 Configure rule targets with MWAA DAG ARNs
    - Include event metadata: polling_type, execution_time, rule_name
    - Configure IAM permissions for MWAA invocation
    - _Requirements: 9.3, 9.4_
  
  - [ ] 12.4 Create Dead Letter Queue for failed executions
    - Create SQS queue: eventbridge-dlq
    - Configure DLQ for all rules
    - _Requirements: 9.6_
  
  - [ ] 12.5 Enable CloudWatch monitoring for EventBridge rules
    - Configure metrics and alarms
    - _Requirements: 9.5_
  
  - [ ]* 12.6 Write property tests for EventBridge configuration
    - **Property 13: EventBridge Rule Target Validity**
    - **Property 14: EventBridge Schedule Expression Validity**
    - **Validates: Requirements 9.2, 9.3, 9.4**

- [ ] 13. Checkpoint - Ensure WAF and EventBridge are configured
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 14. Implement network monitoring and logging
  - [ ] 14.1 Enable VPC Flow Logs
    - Capture all traffic (accepted and rejected)
    - Store in CloudWatch Logs with 90-day retention
    - Include all metadata: source/destination IPs, ports, protocols, action
    - _Requirements: 10.1, 10.2, 10.3_
  
  - [ ] 14.2 Enable DNS query logging
    - Configure for security monitoring
    - _Requirements: 10.4_
  
  - [ ] 14.3 Create CloudWatch alarms for suspicious network patterns
    - Configure alarms for anomalies
    - _Requirements: 10.5_
  
  - [ ]* 14.4 Write property test for VPC Flow Logs completeness
    - **Property 15: VPC Flow Logs Capture Completeness**
    - **Validates: Requirements 10.2**

- [ ] 15. Implement resource tagging strategy
  - [ ] 15.1 Create tagging module with validation
    - Define mandatory tags: Project, Environment, Component, Owner, CostCenter
    - Define optional tags: CreatedBy, CreatedDate, LastModified
    - Implement tag validation logic
    - _Requirements: 8.1, 8.2, 8.3, 8.4_
  
  - [ ]* 15.2 Write property test for resource tagging completeness
    - **Property 12: Resource Tagging Completeness**
    - **Validates: Requirements 8.1, 8.4**

- [ ] 16. Document integration with existing Cencosud infrastructure
  - [ ] 16.1 Create documentation for Redshift integration
    - Document existing Redshift cluster configuration
    - Document network connectivity requirements
    - Document security group rules for existing BI systems
    - Document migration path from MySQL→Redshift connection
    - _Requirements: 11.1, 11.2, 11.3, 11.7_
  
  - [ ]* 16.2 Write property test for Redshift security group integration
    - **Property 16: Redshift Security Group Integration**
    - **Validates: Requirements 11.3**

- [ ] 17. Document single-AZ deployment and multi-AZ migration path
  - [ ] 17.1 Create documentation for single points of failure
    - Document NAT Gateway as single point of failure
    - Document single AZ deployment limitations
    - Document impact of AZ failure
    - _Requirements: 12.1, 12.2_
  
  - [ ] 17.2 Create multi-AZ migration documentation
    - Document reserved CIDR blocks for us-east-1b
    - Document migration steps from single-AZ to multi-AZ
    - Document architectural changes required
    - _Requirements: 12.3, 12.4, 12.5_
  
  - [ ]* 17.3 Write property test for single point of failure documentation
    - **Property 17: Single Point of Failure Documentation**
    - **Validates: Requirements 12.1, 12.2, 12.3, 12.5**

- [ ] 18. Create environment-specific configurations
  - [ ] 18.1 Create dev.tfvars with development configuration
    - Configure environment-specific variables
    - Document credential management approach
    - _Requirements: 8.1_
  
  - [ ] 18.2 Create staging.tfvars with staging configuration
    - Configure environment-specific variables
    - _Requirements: 8.1_
  
  - [ ] 18.3 Create prod.tfvars with production configuration
    - Configure environment-specific variables
    - _Requirements: 8.1_

- [ ] 19. Create deployment and utility scripts
  - [ ] 19.1 Create init-environment.sh script
    - Initialize Terraform for specific environment
    - Create directory structure
    - _Requirements: 8.1_
  
  - [ ] 19.2 Create deploy.sh script
    - Automate deployment with credential management
    - Include backup, validation, plan, and apply steps
    - Require manual confirmation
    - _Requirements: 8.1_
  
  - [ ] 19.3 Create backup-state.sh script
    - Automate state file backups
    - _Requirements: 8.1_

- [ ] 20. Final checkpoint - Complete infrastructure validation
  - [ ] 20.1 Run terraform validate on all modules
    - Ensure syntax is correct
    - _Requirements: All_
  
  - [ ] 20.2 Run terraform fmt on all files
    - Ensure consistent formatting
    - _Requirements: All_
  
  - [ ] 20.3 Run tfsec security scan
    - Ensure no security issues
    - _Requirements: All_
  
  - [ ]* 20.4 Run complete property-based test suite
    - Execute all 17 property tests with 100 iterations each
    - Verify all properties pass
    - _Requirements: All_
  
  - [ ]* 20.5 Run complete unit test suite
    - Execute all unit tests
    - Verify all tests pass
    - _Requirements: All_

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties
- Unit tests validate specific examples and edge cases
- All infrastructure is deployed in single-AZ (us-east-1a) with reserved CIDR blocks for future multi-AZ expansion
- Local state management is used (no remote backend for free tier)
- Credentials are passed via environment variables or command-line parameters, never hardcoded
