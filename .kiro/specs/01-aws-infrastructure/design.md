# Design Document: AWS Infrastructure

## Overview

This design document defines the AWS infrastructure architecture for the Janis-Cencosud data integration platform. The infrastructure provides a secure, scalable, and resilient foundation for the entire data pipeline, supporting real-time webhook ingestion, scheduled API polling, ETL transformations, and data warehousing.

The design follows AWS Well-Architected Framework principles, emphasizing security through defense-in-depth, high availability through multi-AZ deployment, and cost optimization through serverless and managed services. The infrastructure integrates with Cencosud's existing Redshift cluster while maintaining network isolation and security compliance.

## Architecture

### High-Level Architecture

The infrastructure is organized into distinct layers:

1. **Network Layer**: VPC with public/private subnet architecture across two Availability Zones
2. **Security Layer**: Security Groups, NACLs, WAF, and VPC Endpoints for defense-in-depth
3. **Connectivity Layer**: Internet Gateway, NAT Gateways, and VPC Endpoints for AWS service access
4. **Orchestration Layer**: EventBridge for intelligent scheduling and event routing
5. **Integration Layer**: Connections to existing Cencosud Redshift infrastructure

### Network Topology

```
VPC (10.0.0.0/16)
└── Availability Zone A (us-east-1a)
    ├── Public Subnet (10.0.1.0/24)
    │   └── NAT Gateway
    ├── Private Subnet 1A (10.0.10.0/24)
    │   └── Redshift, MWAA, Lambda
    └── Private Subnet 2A (10.0.20.0/24)
        └── Glue ENIs

Reserved for Future Multi-AZ Expansion:
└── Availability Zone B (us-east-1b) [RESERVED]
    ├── Public Subnet (10.0.2.0/24) [RESERVED]
    ├── Private Subnet 1B (10.0.11.0/24) [RESERVED]
    └── Private Subnet 2B (10.0.21.0/24) [RESERVED]
```

### Design Decisions

**Single-AZ Initial Deployment**: The infrastructure is initially deployed in a single Availability Zone (us-east-1a) to reduce costs and complexity during the initial implementation phase. This approach accepts the trade-off of reduced availability in exchange for faster deployment and lower operational costs.

**Future Multi-AZ Readiness**: The CIDR block allocation and naming conventions are designed to support future multi-AZ expansion without requiring major architectural changes. Reserved CIDR blocks (10.0.2.0/24, 10.0.11.0/24, 10.0.21.0/24) are documented for us-east-1b deployment.

**Single Points of Failure**: The single-AZ deployment introduces several single points of failure:
- Single NAT Gateway: If it fails, private subnets lose internet connectivity
- Single AZ: If us-east-1a experiences an outage, the entire system becomes unavailable
- No automatic failover: Manual intervention required for disaster recovery

**Subnet Segregation**: Three subnets provide clear separation of concerns:
- Public subnet for internet-facing resources (NAT Gateway)
- Private subnet 1A for data processing services (Redshift, MWAA, Lambda)
- Private subnet 2A dedicated to Glue ENIs to avoid IP exhaustion

**VPC Endpoints**: Interface and Gateway endpoints minimize data transfer costs and improve security by keeping traffic within AWS network.

**EventBridge Integration**: EventBridge handles scheduling instead of relying solely on MWAA's internal scheduler, reducing MWAA overhead and enabling more flexible event-driven architectures.


## Components and Interfaces

### VPC and Networking Components

**VPC (Virtual Private Cloud)**
- CIDR Block: 10.0.0.0/16 (65,536 IP addresses)
- DNS Resolution: Enabled
- DNS Hostnames: Enabled
- IPv4 Support: Primary
- IPv6 Support: Prepared for future requirements

**Subnets**
- Public Subnet A: 10.0.1.0/24 (256 IPs) in us-east-1a
- Private Subnet 1A: 10.0.10.0/24 (256 IPs) in us-east-1a - Redshift, MWAA, Lambda
- Private Subnet 2A: 10.0.20.0/24 (256 IPs) in us-east-1a - Glue ENIs
- Reserved for future expansion:
  - Public Subnet B: 10.0.2.0/24 (reserved for us-east-1b)
  - Private Subnet 1B: 10.0.11.0/24 (reserved for us-east-1b)
  - Private Subnet 2B: 10.0.21.0/24 (reserved for us-east-1b)

**Internet Connectivity**
- Internet Gateway: Single IGW attached to VPC for public subnet internet access
- NAT Gateway: Single NAT Gateway in Public Subnet A with Elastic IP for private subnet outbound traffic

**Route Tables**
- Public Route Table: Routes 0.0.0.0/0 to Internet Gateway
- Private Route Table: Routes 0.0.0.0/0 to NAT Gateway

### VPC Endpoints

**Gateway Endpoint**
- S3 Gateway Endpoint (com.amazonaws.us-east-1.s3): Associated with all route tables for cost-free S3 access

**Interface Endpoints** (with Private DNS enabled)
- AWS Glue (com.amazonaws.us-east-1.glue): For Glue job execution and catalog access
- Secrets Manager (com.amazonaws.us-east-1.secretsmanager): For secure credential retrieval
- CloudWatch Logs (com.amazonaws.us-east-1.logs): For centralized logging
- KMS (com.amazonaws.us-east-1.kms): For encryption key operations
- STS (com.amazonaws.us-east-1.sts): For temporary credential generation
- EventBridge (com.amazonaws.us-east-1.events): For event routing and scheduling

### Security Groups

**SG-API-Gateway**
- Purpose: Protect API Gateway webhook endpoints
- Inbound Rules:
  - HTTPS (443) from 0.0.0.0/0 (webhook reception from Janis)
- Outbound Rules:
  - All traffic to 0.0.0.0/0

**SG-Redshift-Existing**
- Purpose: Control access to existing Cencosud Redshift cluster
- Inbound Rules:
  - PostgreSQL (5439) from SG-Lambda
  - PostgreSQL (5439) from SG-MWAA
  - PostgreSQL (5439) from existing Cencosud BI systems (specific IPs/SGs)
  - PostgreSQL (5439) from current MySQL→Redshift connection (during migration)
- Outbound Rules:
  - HTTPS (443) to VPC Endpoints only

**SG-Lambda**
- Purpose: Lambda function network security
- Inbound Rules: None (Lambda doesn't receive direct connections)
- Outbound Rules:
  - PostgreSQL (5439) to SG-Redshift-Existing
  - HTTPS (443) to VPC Endpoints and 0.0.0.0/0

**SG-MWAA**
- Purpose: MWAA environment security
- Inbound Rules:
  - HTTPS (443) from SG-MWAA (self-reference for worker communication)
  - EventBridge triggers from VPC Endpoint EventBridge
- Outbound Rules:
  - HTTPS (443) to VPC Endpoints and 0.0.0.0/0
  - PostgreSQL (5439) to SG-Redshift-Existing

**SG-Glue**
- Purpose: Glue job network security
- Inbound Rules:
  - All TCP from SG-Glue (self-reference for Spark cluster communication)
- Outbound Rules:
  - HTTPS (443) to VPC Endpoints
  - All TCP to SG-Glue (self-reference)

**SG-EventBridge**
- Purpose: EventBridge VPC endpoint security
- Inbound Rules: None (receives events internally)
- Outbound Rules:
  - HTTPS (443) to MWAA endpoints for DAG triggering
  - HTTPS (443) to VPC Endpoints


### Network Access Control Lists (NACLs)

**Public Subnet NACL**
- Inbound Rules:
  - Rule 100: HTTPS (443) from 0.0.0.0/0 - ALLOW
  - Rule 110: Ephemeral ports (1024-65535) from 0.0.0.0/0 - ALLOW
  - Rule *: All other traffic - DENY
- Outbound Rules:
  - Rule 100: All traffic to 0.0.0.0/0 - ALLOW
  - Rule *: All other traffic - DENY

**Private Subnet NACL**
- Inbound Rules:
  - Rule 100: All traffic from 10.0.0.0/16 - ALLOW
  - Rule 110: HTTPS (443) from 0.0.0.0/0 - ALLOW
  - Rule 120: Ephemeral ports (1024-65535) from 0.0.0.0/0 - ALLOW
  - Rule *: All other traffic - DENY
- Outbound Rules:
  - Rule 100: All traffic to 10.0.0.0/16 - ALLOW
  - Rule 110: HTTPS (443) to 0.0.0.0/0 - ALLOW
  - Rule *: All other traffic - DENY

### Web Application Firewall (WAF)

**WAF Web ACL Configuration**
- Scope: Regional (API Gateway)
- Default Action: Allow

**Rate Limiting Rule**
- Name: RateLimitRule
- Priority: 1
- Limit: 2,000 requests per IP in 5 minutes
- Action: Block with 429 (Too Many Requests) response

**Geo-Blocking Rule**
- Name: GeoBlockingRule
- Priority: 2
- Allowed Countries: Peru (PE), AWS regions
- Action: Block traffic from other countries

**AWS Managed Rules**
- AWSManagedRulesAmazonIpReputationList: Block known malicious IPs
- AWSManagedRulesCommonRuleSet: OWASP Top 10 protection
- AWSManagedRulesKnownBadInputsRuleSet: Block malicious payloads

**Logging Configuration**
- Destination: CloudWatch Logs
- Log all blocked requests with full request details

### EventBridge Configuration

**Custom Event Bus**
- Name: janis-cencosud-polling-bus
- Purpose: Dedicated bus for polling operations

**Scheduled Rules**

1. **Order Polling Rule**
   - Name: poll-orders-schedule
   - Schedule: rate(5 minutes)
   - Target: MWAA DAG (dag_poll_orders)
   - Event Metadata: { "polling_type": "orders", "execution_time": "$time", "rule_name": "poll-orders-schedule" }

2. **Product Polling Rule**
   - Name: poll-products-schedule
   - Schedule: rate(60 minutes)
   - Target: MWAA DAG (dag_poll_products)
   - Event Metadata: { "polling_type": "products", "execution_time": "$time", "rule_name": "poll-products-schedule" }

3. **Stock Polling Rule**
   - Name: poll-stock-schedule
   - Schedule: rate(10 minutes)
   - Target: MWAA DAG (dag_poll_stock)
   - Event Metadata: { "polling_type": "stock", "execution_time": "$time", "rule_name": "poll-stock-schedule" }

4. **Price Polling Rule**
   - Name: poll-prices-schedule
   - Schedule: rate(30 minutes)
   - Target: MWAA DAG (dag_poll_prices)
   - Event Metadata: { "polling_type": "prices", "execution_time": "$time", "rule_name": "poll-prices-schedule" }

5. **Store Polling Rule**
   - Name: poll-stores-schedule
   - Schedule: rate(1440 minutes)
   - Target: MWAA DAG (dag_poll_stores)
   - Event Metadata: { "polling_type": "stores", "execution_time": "$time", "rule_name": "poll-stores-schedule" }

**Dead Letter Queue Configuration**
- SQS Queue: eventbridge-dlq
- Purpose: Capture failed rule executions for retry and analysis

**IAM Permissions**
- EventBridge role with permissions to invoke MWAA DAGs
- CloudWatch Logs permissions for rule execution logging


## Data Models

### Tagging Data Model

All AWS resources follow a consistent tagging strategy for resource management, cost allocation, and compliance.

**Mandatory Tags**
```json
{
  "Project": "janis-cencosud-integration",
  "Environment": "production | staging | development",
  "Component": "<specific-component-name>",
  "Owner": "cencosud-data-team",
  "CostCenter": "<assigned-cost-center-code>"
}
```

**Optional Tags**
```json
{
  "CreatedBy": "<automation-tool-or-user>",
  "CreatedDate": "<ISO-8601-timestamp>",
  "LastModified": "<ISO-8601-timestamp>"
}
```

**Tag Validation Rules**
- All mandatory tags must be present before resource creation
- Environment tag must be one of: production, staging, development
- CostCenter must match approved cost center codes
- Tags are case-sensitive and must use exact naming

### Network Configuration Data Model

**VPC Configuration**
```hcl
{
  cidr_block: "10.0.0.0/16",
  enable_dns_support: true,
  enable_dns_hostnames: true,
  availability_zones: ["us-east-1a", "us-east-1b"],
  tags: <TaggingDataModel>
}
```

**Subnet Configuration**
```hcl
{
  subnet_id: string,
  cidr_block: string,
  availability_zone: string,
  subnet_type: "public" | "private",
  purpose: "general" | "glue-enis",
  map_public_ip_on_launch: boolean,
  route_table_id: string,
  tags: <TaggingDataModel>
}
```

**Security Group Rule**
```hcl
{
  type: "ingress" | "egress",
  from_port: number,
  to_port: number,
  protocol: "tcp" | "udp" | "icmp" | "-1",
  cidr_blocks: [string] | null,
  source_security_group_id: string | null,
  description: string
}
```

### EventBridge Rule Data Model

**Scheduled Rule Configuration**
```json
{
  "rule_name": "string",
  "schedule_expression": "rate(X minutes) | cron(...)",
  "state": "ENABLED | DISABLED",
  "event_bus_name": "string",
  "target": {
    "arn": "string",
    "role_arn": "string",
    "input": {
      "polling_type": "string",
      "execution_time": "string",
      "rule_name": "string"
    }
  },
  "dead_letter_config": {
    "arn": "string"
  }
}
```

### VPC Flow Logs Data Model

**Flow Log Record**
```
{
  "version": 2,
  "account_id": "string",
  "interface_id": "string",
  "srcaddr": "string",
  "dstaddr": "string",
  "srcport": number,
  "dstport": number,
  "protocol": number,
  "packets": number,
  "bytes": number,
  "start": timestamp,
  "end": timestamp,
  "action": "ACCEPT | REJECT",
  "log_status": "OK | NODATA | SKIPDATA"
}
```


## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: VPC CIDR Block Validity

*For any* VPC configuration, the CIDR block must be a valid IPv4 CIDR notation and provide exactly 65,536 IP addresses (10.0.0.0/16).

**Validates: Requirements 1.1**

### Property 2: Single-AZ Deployment

*For any* infrastructure deployment, all resources must be deployed in exactly one Availability Zone (us-east-1a) with reserved CIDR blocks documented for future multi-AZ expansion.

**Validates: Requirements 1.2, 2.2, 2.3**

### Property 3: Subnet CIDR Non-Overlap

*For any* pair of subnets within the VPC, their CIDR blocks must not overlap and must be valid subsets of the VPC CIDR block (10.0.0.0/16).

**Validates: Requirements 2.1, 2.2**

### Property 4: Public Subnet Internet Routing

*For any* public subnet, the route table must contain a route directing 0.0.0.0/0 traffic to the Internet Gateway.

**Validates: Requirements 3.4**

### Property 5: Private Subnet NAT Routing

*For any* private subnet, the route table must contain a route directing 0.0.0.0/0 traffic to the NAT Gateway in the public subnet.

**Validates: Requirements 3.4**

### Property 6: VPC Endpoint Service Coverage

*For any* required AWS service (S3, Glue, Secrets Manager, CloudWatch Logs, KMS, STS, EventBridge), a corresponding VPC endpoint must exist and be properly configured.

**Validates: Requirements 4.1, 4.2**

### Property 7: Security Group Least Privilege

*For any* security group rule, the rule must follow the principle of least privilege by specifying the minimum required ports, protocols, and source/destination ranges.

**Validates: Requirements 5.1, 5.2, 5.3, 5.4, 5.5, 5.6**

### Property 8: Security Group Self-Reference Validity

*For any* security group with self-referencing rules (SG-MWAA, SG-Glue), the source and destination security group IDs must match the security group's own ID.

**Validates: Requirements 5.4, 5.5**

### Property 9: NACL Stateless Bidirectionality

*For any* NACL allowing inbound traffic on a specific port, there must be a corresponding outbound rule allowing ephemeral ports (1024-65535) for return traffic, and vice versa.

**Validates: Requirements 6.4**

### Property 10: WAF Rate Limit Enforcement

*For any* IP address making requests to the API Gateway, if the request count exceeds 2,000 requests in a 5-minute window, subsequent requests must be blocked with a 429 response code.

**Validates: Requirements 7.1**

### Property 11: WAF Geo-Blocking Enforcement

*For any* incoming request to the API Gateway, if the source country is not Peru (PE) or an AWS region, the request must be blocked.

**Validates: Requirements 7.2**

### Property 12: Resource Tagging Completeness

*For any* AWS resource created by the infrastructure, all mandatory tags (Project, Environment, Component, Owner, CostCenter) must be present and non-empty.

**Validates: Requirements 8.1, 8.4**

### Property 13: EventBridge Rule Target Validity

*For any* EventBridge scheduled rule, the target must be a valid MWAA DAG ARN with proper IAM permissions and include required event metadata (polling_type, execution_time, rule_name).

**Validates: Requirements 9.3, 9.4**

### Property 14: EventBridge Schedule Expression Validity

*For any* EventBridge scheduled rule, the schedule expression must be a valid rate() or cron() expression matching the specified polling frequency.

**Validates: Requirements 9.2**

### Property 15: VPC Flow Logs Capture Completeness

*For any* network traffic within the VPC, the VPC Flow Logs must capture both accepted and rejected traffic with complete metadata (source/destination IPs, ports, protocols, action).

**Validates: Requirements 10.2**

### Property 16: Redshift Security Group Integration

*For any* new security group rule added to SG-Redshift-Existing, the rule must not conflict with existing Cencosud BI system access rules.

**Validates: Requirements 11.3**

### Property 17: Single Point of Failure Documentation

*For any* single-AZ deployment, the infrastructure documentation must clearly identify all single points of failure (NAT Gateway, AZ availability) and include a migration path to multi-AZ deployment.

**Validates: Requirements 12.1, 12.2, 12.3, 12.5**


## Error Handling

### Network Connectivity Errors

**NAT Gateway Failure**
- Detection: CloudWatch alarms on NAT Gateway connection count and error rate
- Response: Manual intervention required - no automatic failover in single-AZ deployment
- Recovery: Recreate NAT Gateway or wait for AWS to restore service
- Logging: VPC Flow Logs capture connection failures
- Impact: Complete loss of internet connectivity for private subnets until recovery

**Availability Zone Failure**
- Detection: AWS Service Health Dashboard and CloudWatch alarms
- Response: Complete system outage - no automatic failover in single-AZ deployment
- Recovery: Wait for AWS to restore AZ or manually migrate to different AZ
- Logging: AWS Service Health events and CloudWatch alarms
- Impact: Complete system unavailability until AZ is restored

**VPC Endpoint Unavailability**
- Detection: Service-specific error codes (503, connection timeouts)
- Response: Fallback to NAT Gateway routing for internet-based service access
- Recovery: Automatic retry with exponential backoff
- Logging: CloudWatch Logs capture endpoint connection errors

**Internet Gateway Failure**
- Detection: CloudWatch alarms on IGW packet loss and error rate
- Response: AWS automatically handles IGW redundancy (managed service)
- Recovery: Automatic by AWS
- Logging: VPC Flow Logs capture routing failures

### Security Errors

**WAF Rule Violations**
- Detection: WAF logs in CloudWatch showing blocked requests
- Response: Return 403 (Forbidden) or 429 (Too Many Requests) to client
- Recovery: Client must adjust request pattern or wait for rate limit reset
- Logging: Full request details logged to CloudWatch for security analysis

**Security Group Rule Conflicts**
- Detection: Terraform validation errors during infrastructure deployment
- Response: Deployment fails with descriptive error message
- Recovery: Manual correction of security group rules in Terraform code
- Logging: Terraform state and error logs

**NACL Misconfiguration**
- Detection: Connection timeouts or unexpected traffic blocks
- Response: VPC Flow Logs show REJECT actions
- Recovery: Manual NACL rule adjustment through Terraform
- Logging: VPC Flow Logs with NACL rule match information

### EventBridge Errors

**Rule Execution Failure**
- Detection: EventBridge metrics showing failed invocations
- Response: Failed events sent to Dead Letter Queue (SQS)
- Recovery: Manual replay from DLQ or automatic retry based on configuration
- Logging: CloudWatch Logs capture rule execution errors with full event details

**Target Invocation Failure**
- Detection: MWAA DAG fails to trigger or returns error
- Response: Event sent to DLQ for manual investigation
- Recovery: Fix underlying MWAA issue and replay event from DLQ
- Logging: Both EventBridge and MWAA logs capture failure details

**Schedule Expression Errors**
- Detection: Terraform validation during deployment
- Response: Deployment fails with invalid schedule expression error
- Recovery: Correct schedule expression in Terraform configuration
- Logging: Terraform error output

### Resource Quota Errors

**VPC Limit Exceeded**
- Detection: AWS API error during VPC creation (LimitExceeded)
- Response: Terraform deployment fails
- Recovery: Request quota increase through AWS Support or clean up unused VPCs
- Logging: Terraform error logs and AWS CloudTrail

**Elastic IP Limit Exceeded**
- Detection: AWS API error during EIP allocation
- Response: NAT Gateway creation fails
- Recovery: Request quota increase or release unused EIPs
- Logging: Terraform error logs and AWS CloudTrail

**Security Group Rule Limit Exceeded**
- Detection: AWS API error when adding rules (RulesPerSecurityGroupLimitExceeded)
- Response: Rule addition fails
- Recovery: Consolidate rules or create additional security groups
- Logging: Terraform error logs and AWS CloudTrail

### Tagging Errors

**Missing Mandatory Tags**
- Detection: Terraform validation or AWS Config rule evaluation
- Response: Resource creation blocked or flagged as non-compliant
- Recovery: Add missing tags through Terraform configuration
- Logging: AWS Config compliance logs

**Invalid Tag Values**
- Detection: Custom validation in Terraform or AWS Config rules
- Response: Resource creation blocked or flagged as non-compliant
- Recovery: Correct tag values in Terraform variables
- Logging: Terraform validation errors and AWS Config logs


## Testing Strategy

### Dual Testing Approach

The infrastructure will be validated through both unit tests and property-based tests to ensure comprehensive coverage:

- **Unit tests**: Verify specific infrastructure configurations, edge cases, and error conditions
- **Property tests**: Verify universal properties across all infrastructure components

Both testing approaches are complementary and necessary for comprehensive infrastructure validation.

### Property-Based Testing

**Testing Framework**: Terratest with Go for infrastructure testing

**Configuration**:
- Minimum 100 iterations per property test
- Each test references its corresponding design document property
- Tag format: `Feature: aws-infrastructure, Property {number}: {property_text}`

**Property Test Implementation**:

Each correctness property from the design document will be implemented as a property-based test:

1. **Property 1 Test**: Generate random VPC CIDR blocks and validate they provide exactly 65,536 IPs
2. **Property 2 Test**: Verify all resources are deployed in exactly one AZ (us-east-1a) with reserved CIDRs documented
3. **Property 3 Test**: Generate random subnet configurations and verify no CIDR overlaps
4. **Property 4 Test**: Verify public subnet routes 0.0.0.0/0 to IGW
5. **Property 5 Test**: Verify all private subnets route 0.0.0.0/0 to the single NAT Gateway
6. **Property 6 Test**: Verify all required AWS services have corresponding VPC endpoints
7. **Property 7 Test**: Verify all security group rules follow least privilege principle
8. **Property 8 Test**: Verify self-referencing security groups have matching source/destination IDs
9. **Property 9 Test**: Verify NACL rules allow bidirectional traffic with ephemeral ports
10. **Property 10 Test**: Simulate request patterns and verify WAF rate limiting at 2,000 req/5min
11. **Property 11 Test**: Simulate requests from various countries and verify geo-blocking
12. **Property 12 Test**: Verify all resources have complete mandatory tags
13. **Property 13 Test**: Verify all EventBridge rules have valid MWAA targets with metadata
14. **Property 14 Test**: Verify all EventBridge schedule expressions are valid rate/cron formats
15. **Property 15 Test**: Verify VPC Flow Logs capture all traffic types with complete metadata
16. **Property 16 Test**: Verify new Redshift security group rules don't conflict with existing rules
17. **Property 17 Test**: Verify documentation identifies all single points of failure and includes multi-AZ migration path

### Unit Testing

**Unit Test Focus Areas**:

1. **VPC Configuration Tests**
   - Test VPC creation with correct CIDR block (10.0.0.0/16)
   - Test DNS resolution and hostnames are enabled
   - Test VPC tags are applied correctly

2. **Subnet Configuration Tests**
   - Test each subnet has correct CIDR block
   - Test subnets are in correct AZ (us-east-1a)
   - Test reserved CIDR blocks are documented for future expansion
   - Test public IP assignment only on public subnet
   - Test subnet tags include purpose and tier

3. **Internet Connectivity Tests**
   - Test Internet Gateway is attached to VPC
   - Test single NAT Gateway is created in public subnet
   - Test Elastic IP is assigned to NAT Gateway
   - Test route tables direct traffic correctly
   - Test documentation identifies NAT Gateway as single point of failure

4. **VPC Endpoint Tests**
   - Test S3 Gateway Endpoint is created
   - Test all required Interface Endpoints are created
   - Test Private DNS is enabled on Interface Endpoints
   - Test endpoints are associated with correct route tables

5. **Security Group Tests**
   - Test each security group has correct inbound/outbound rules
   - Test security group references are valid
   - Test no overly permissive rules (0.0.0.0/0 on sensitive ports)

6. **NACL Tests**
   - Test NACL rules are in correct priority order
   - Test default deny rules are present
   - Test NACLs are associated with correct subnets

7. **WAF Tests**
   - Test WAF Web ACL is created and associated with API Gateway
   - Test rate limiting rule is configured correctly
   - Test geo-blocking rule allows only Peru
   - Test AWS Managed Rules are enabled

8. **EventBridge Tests**
   - Test custom event bus is created
   - Test all 5 scheduled rules are created with correct schedules
   - Test rules target correct MWAA DAGs
   - Test DLQ is configured for failed executions

9. **Tagging Tests**
   - Test all resources have mandatory tags
   - Test tag values are valid
   - Test tag consistency across resources

10. **Integration with Existing Infrastructure Tests**
    - Test Redshift security group allows connections from new components
    - Test no network conflicts with existing Cencosud infrastructure
    - Test existing BI systems can still access Redshift

11. **Single-AZ Deployment Tests**
    - Test all resources are deployed in us-east-1a only
    - Test reserved CIDR blocks are documented for future multi-AZ expansion
    - Test documentation identifies all single points of failure
    - Test migration path to multi-AZ is documented

### Infrastructure Testing Tools

**Terratest**: Primary testing framework for Terraform infrastructure
- Go-based testing framework
- Supports property-based testing through Go testing libraries
- Integrates with AWS SDK for validation

**terraform validate**: Syntax and configuration validation
**terraform plan**: Dry-run validation before deployment
**tfsec**: Security scanning for Terraform code
**checkov**: Policy-as-code validation for infrastructure

### Testing Workflow

1. **Local Development**:
   - Run `terraform fmt` to format code
   - Run `terraform validate` to check syntax
   - Run `tfsec` for security scanning
   - Run unit tests with Terratest

2. **Pre-Deployment**:
   - Run full property-based test suite (100 iterations each)
   - Run integration tests against temporary test environment
   - Validate against AWS Config rules

3. **Post-Deployment**:
   - Verify all resources are created successfully
   - Run smoke tests to validate connectivity
   - Verify VPC Flow Logs are capturing traffic
   - Verify EventBridge rules are triggering correctly

4. **Continuous Validation**:
   - AWS Config continuous compliance monitoring
   - CloudWatch alarms for infrastructure health
   - Regular drift detection with `terraform plan`

### Test Environment Strategy

**Ephemeral Test Environments**:
- Create temporary VPC for testing
- Deploy minimal infrastructure for validation
- Run tests against temporary environment
- Destroy environment after tests complete

**Test Isolation**:
- Use separate AWS account or isolated VPC for testing
- Avoid impacting production or staging environments
- Use unique resource naming to prevent conflicts

