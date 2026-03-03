# Multi-AZ Expansion Plan

## Overview

The Janis-Cencosud AWS infrastructure is initially deployed in a **single Availability Zone (us-east-1a)** to reduce costs and complexity during the initial implementation phase. However, the architecture is designed with reserved CIDR blocks and conditional resource creation to support future multi-AZ expansion without requiring major architectural changes.

## Current Single-AZ Architecture

### Active Subnets (us-east-1a)

| Subnet Name | CIDR Block | Purpose | Auto-Assign Public IP |
|-------------|------------|---------|----------------------|
| Public Subnet A | 10.0.1.0/24 | NAT Gateway, API Gateway | Yes |
| Private Subnet 1A | 10.0.10.0/24 | Lambda, MWAA, Redshift | No |
| Private Subnet 2A | 10.0.20.0/24 | Glue ENIs | No |

### Single Points of Failure

The single-AZ deployment introduces the following single points of failure:

1. **NAT Gateway**: Single NAT Gateway in us-east-1a
   - If it fails, private subnets lose internet connectivity
   - Manual intervention required for recovery
   - No automatic failover

2. **Availability Zone**: All resources in us-east-1a
   - If us-east-1a experiences an outage, the entire system becomes unavailable
   - No automatic failover to another AZ
   - Recovery requires AWS to restore the AZ

3. **Network Connectivity**: Single route to internet
   - No redundant paths for internet access
   - Dependent on single IGW and single NAT Gateway

## Reserved CIDR Blocks for Multi-AZ Expansion

### Reserved Subnets (us-east-1b)

The following CIDR blocks are **reserved** for future multi-AZ expansion and should **NOT** be used for any other purpose:

| Subnet Name | CIDR Block | Purpose | Status |
|-------------|------------|---------|--------|
| Public Subnet B | 10.0.2.0/24 | NAT Gateway, API Gateway | RESERVED |
| Private Subnet 1B | 10.0.11.0/24 | Lambda, MWAA, Redshift | RESERVED |
| Private Subnet 2B | 10.0.21.0/24 | Glue ENIs | RESERVED |

### CIDR Block Allocation Strategy

The VPC uses CIDR block 10.0.0.0/16, providing 65,536 IP addresses. The allocation strategy follows this pattern:

- **10.0.1.0/24 - 10.0.9.0/24**: Public subnets (256 IPs each)
  - 10.0.1.0/24: Public Subnet A (us-east-1a) - ACTIVE
  - 10.0.2.0/24: Public Subnet B (us-east-1b) - RESERVED
  - 10.0.3.0/24 - 10.0.9.0/24: Available for future expansion

- **10.0.10.0/24 - 10.0.19.0/24**: Private subnets for data processing (256 IPs each)
  - 10.0.10.0/24: Private Subnet 1A (us-east-1a) - ACTIVE
  - 10.0.11.0/24: Private Subnet 1B (us-east-1b) - RESERVED
  - 10.0.12.0/24 - 10.0.19.0/24: Available for future expansion

- **10.0.20.0/24 - 10.0.29.0/24**: Private subnets for Glue ENIs (256 IPs each)
  - 10.0.20.0/24: Private Subnet 2A (us-east-1a) - ACTIVE
  - 10.0.21.0/24: Private Subnet 2B (us-east-1b) - RESERVED
  - 10.0.22.0/24 - 10.0.29.0/24: Available for future expansion

- **10.0.30.0/24 - 10.0.255.0/24**: Available for future use cases

## Migration Path to Multi-AZ

### Prerequisites

Before enabling multi-AZ deployment:

1. **Cost Analysis**: Understand the cost implications
   - Additional NAT Gateway: ~$32/month + data transfer costs
   - Additional Elastic IP: ~$3.60/month
   - Cross-AZ data transfer: $0.01/GB

2. **Business Requirements**: Confirm the need for high availability
   - Define RTO (Recovery Time Objective)
   - Define RPO (Recovery Point Objective)
   - Assess impact of AZ failure on business operations

3. **Testing Plan**: Prepare for multi-AZ testing
   - Test failover scenarios
   - Validate application behavior across AZs
   - Verify data consistency

### Migration Steps

#### Phase 1: Pre-Migration Planning (1-2 weeks)

**1.1 Stakeholder Communication**
- Notify all stakeholders of planned multi-AZ migration
- Schedule maintenance window (recommended: low-traffic period)
- Prepare rollback plan and communication templates
- Assign roles and responsibilities for migration team

**1.2 Cost Analysis and Approval**
- Calculate expected cost increase (~$35.60/month + data transfer)
- Estimate cross-AZ data transfer costs based on current traffic patterns
- Obtain budget approval from finance team
- Document cost-benefit analysis for high availability

**1.3 Backup and Recovery Preparation**
- Create full backup of Terraform state files
- Take Redshift cluster snapshot
- Document current configuration and resource IDs
- Verify backup restoration procedures
- Test rollback procedures in development environment

**1.4 Testing Environment Setup**
- Deploy multi-AZ configuration in development environment
- Run integration tests across both AZs
- Validate failover scenarios
- Document any issues and resolutions

#### Phase 2: Infrastructure Migration (2-4 hours)

**2.1 Enable Multi-AZ in Terraform**

Update the Terraform configuration to enable multi-AZ:

```bash
# Backup current state
cd terraform/environments/prod
cp terraform.tfstate terraform.tfstate.backup.$(date +%Y%m%d_%H%M%S)

# Update terraform.tfvars
cat >> prod.tfvars << EOF
# Multi-AZ Configuration
enable_multi_az = true
EOF
```

**2.2 Review Infrastructure Changes**

```bash
# Review the changes that will be made
terraform plan -var-file="prod.tfvars" -out=multi-az.tfplan

# Expected changes:
# + Create Public Subnet B in us-east-1b (10.0.2.0/24)
# + Create Private Subnet 1B in us-east-1b (10.0.11.0/24)
# + Create Private Subnet 2B in us-east-1b (10.0.21.0/24)
# + Create NAT Gateway B in Public Subnet B
# + Create Elastic IP for NAT Gateway B
# + Create Private Route Table B
# + Associate Private Subnets 1B and 2B with Private Route Table B
# + Update VPC Endpoint associations to include new subnets
# + Update Security Group rules if necessary
# ~ Modify existing resources to support multi-AZ (minimal changes)

# Verify no unexpected deletions or replacements
# Look for resources marked with "-" (delete) or "-/+" (replace)
```

**2.3 Apply Infrastructure Changes**

```bash
# Apply the multi-AZ configuration
terraform apply multi-az.tfplan

# Monitor progress
# Expected duration: 5-10 minutes
# NAT Gateway creation is the longest operation (~2-3 minutes)

# Verify successful completion
terraform show | grep "us-east-1b"
```

**2.4 Validate Network Infrastructure**

```bash
# Verify subnets are created in both AZs
aws ec2 describe-subnets \
  --filters "Name=vpc-id,Values=$(terraform output -raw vpc_id)" \
  --query 'Subnets[*].[SubnetId,CidrBlock,AvailabilityZone,Tags[?Key==`Name`].Value|[0]]' \
  --output table

# Expected output:
# |  subnet-xxx  |  10.0.1.0/24   |  us-east-1a  |  public-subnet-a   |
# |  subnet-xxx  |  10.0.2.0/24   |  us-east-1b  |  public-subnet-b   |
# |  subnet-xxx  |  10.0.10.0/24  |  us-east-1a  |  private-subnet-1a |
# |  subnet-xxx  |  10.0.11.0/24  |  us-east-1b  |  private-subnet-1b |
# |  subnet-xxx  |  10.0.20.0/24  |  us-east-1a  |  private-subnet-2a |
# |  subnet-xxx  |  10.0.21.0/24  |  us-east-1b  |  private-subnet-2b |

# Verify NAT Gateways are running in both AZs
aws ec2 describe-nat-gateways \
  --filter "Name=vpc-id,Values=$(terraform output -raw vpc_id)" \
  --query 'NatGateways[*].[NatGatewayId,State,SubnetId,Tags[?Key==`Name`].Value|[0]]' \
  --output table

# Expected output:
# |  nat-xxx  |  available  |  subnet-xxx  |  nat-gateway-a  |
# |  nat-xxx  |  available  |  subnet-xxx  |  nat-gateway-b  |

# Verify route tables are configured correctly
aws ec2 describe-route-tables \
  --filters "Name=vpc-id,Values=$(terraform output -raw vpc_id)" \
  --query 'RouteTables[*].[RouteTableId,Tags[?Key==`Name`].Value|[0],Routes[?DestinationCidrBlock==`0.0.0.0/0`].NatGatewayId|[0]]' \
  --output table

# Verify VPC endpoints are associated with new subnets
aws ec2 describe-vpc-endpoints \
  --filters "Name=vpc-id,Values=$(terraform output -raw vpc_id)" \
  --query 'VpcEndpoints[*].[VpcEndpointId,ServiceName,SubnetIds]' \
  --output table
```

#### Phase 3: Application Migration (2-4 hours)

**3.1 Update Lambda Functions**

```bash
# Update Lambda VPC configuration to include both AZs
# This can be done gradually, function by function

# Example: Update webhook processor Lambda
aws lambda update-function-configuration \
  --function-name janis-cencosud-webhook-processor-prod \
  --vpc-config SubnetIds=$(terraform output -raw private_subnet_1a_id),$(terraform output -raw private_subnet_1b_id),SecurityGroupIds=$(terraform output -raw lambda_security_group_id)

# Verify Lambda can execute in both AZs
aws lambda invoke \
  --function-name janis-cencosud-webhook-processor-prod \
  --payload '{"test": "multi-az"}' \
  response.json

# Check CloudWatch Logs for successful execution
```

**3.2 Update MWAA Environment**

```bash
# MWAA requires recreation to update subnet configuration
# This will cause temporary downtime for workflows

# Option 1: Update via Terraform (recommended)
# Update MWAA module configuration to include both private subnets
terraform apply -var-file="prod.tfvars" -target=module.mwaa

# Option 2: Update via AWS CLI
aws mwaa update-environment \
  --name cencosud-mwaa-environment \
  --network-configuration SubnetIds=$(terraform output -raw private_subnet_1a_id),$(terraform output -raw private_subnet_1b_id)

# Monitor MWAA environment update (takes 20-30 minutes)
aws mwaa get-environment --name cencosud-mwaa-environment \
  --query 'Environment.Status'

# Wait for status to be "AVAILABLE"
```

**3.3 Update Redshift Cluster (Optional)**

```bash
# Consider enabling multi-AZ for Redshift cluster
# This requires cluster modification and may cause brief downtime

# Check current Redshift configuration
aws redshift describe-clusters \
  --cluster-identifier cencosud-redshift-cluster \
  --query 'Clusters[0].[ClusterIdentifier,AvailabilityZone,MultiAZ]'

# Enable multi-AZ (if supported by cluster type)
aws redshift modify-cluster \
  --cluster-identifier cencosud-redshift-cluster \
  --multi-az \
  --apply-immediately

# Note: Multi-AZ Redshift is only available for RA3 node types
# For other node types, consider using snapshots for DR
```

**3.4 Update Glue Connections**

```bash
# Update Glue connections to use both private subnets
# This ensures Glue jobs can run in either AZ

# List current Glue connections
aws glue get-connections \
  --query 'ConnectionList[*].[Name,ConnectionProperties.JDBC_CONNECTION_URL]'

# Update each Glue connection
aws glue update-connection \
  --name redshift-connection \
  --connection-input '{
    "Name": "redshift-connection",
    "ConnectionType": "JDBC",
    "PhysicalConnectionRequirements": {
      "SubnetId": "'$(terraform output -raw private_subnet_1a_id)'",
      "SecurityGroupIdList": ["'$(terraform output -raw glue_security_group_id)'"],
      "AvailabilityZone": "us-east-1a"
    }
  }'

# Create additional connection for AZ B
aws glue create-connection \
  --connection-input '{
    "Name": "redshift-connection-azb",
    "ConnectionType": "JDBC",
    "PhysicalConnectionRequirements": {
      "SubnetId": "'$(terraform output -raw private_subnet_1b_id)'",
      "SecurityGroupIdList": ["'$(terraform output -raw glue_security_group_id)'"],
      "AvailabilityZone": "us-east-1b"
    }
  }'
```

**3.5 Update API Gateway (if applicable)**

```bash
# API Gateway is a regional service and automatically benefits from multi-AZ
# No configuration changes required

# Verify API Gateway is healthy
aws apigateway get-rest-apis \
  --query 'items[?name==`janis-cencosud-api`].[id,name]'

# Test API endpoint
curl -X POST https://your-api-id.execute-api.us-east-1.amazonaws.com/prod/webhook \
  -H "Content-Type: application/json" \
  -d '{"test": "multi-az"}'
```

#### Phase 4: Validation and Testing (1-2 hours)

**4.1 Functional Testing**

```bash
# Test webhook ingestion
curl -X POST https://your-api-id.execute-api.us-east-1.amazonaws.com/prod/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "order.created",
    "entity_id": "test-order-123",
    "timestamp": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'"
  }'

# Verify Lambda execution in CloudWatch Logs
aws logs tail /aws/lambda/janis-cencosud-webhook-processor-prod --follow

# Test MWAA DAG execution
# Trigger a test DAG run via Airflow UI or CLI

# Verify Glue job execution
aws glue start-job-run --job-name bronze-to-silver-orders

# Monitor job progress
aws glue get-job-run --job-name bronze-to-silver-orders --run-id <run-id>
```

**4.2 Failover Testing**

```bash
# Test 1: Simulate NAT Gateway A failure
# Temporarily modify route table to point to invalid NAT Gateway
# Verify resources in AZ B continue to function

# Test 2: Verify cross-AZ connectivity
# Deploy test Lambda in AZ A and AZ B
# Verify both can access Redshift and VPC endpoints

# Test 3: Load distribution
# Monitor CloudWatch metrics to verify traffic is distributed across AZs
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Invocations \
  --dimensions Name=FunctionName,Value=janis-cencosud-webhook-processor-prod \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Sum
```

**4.3 Performance Validation**

```bash
# Monitor cross-AZ data transfer
aws cloudwatch get-metric-statistics \
  --namespace AWS/EC2 \
  --metric-name NetworkIn \
  --dimensions Name=InstanceId,Value=<nat-gateway-id> \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Average,Maximum

# Verify no performance degradation
# Compare latency metrics before and after migration
# Check for any increased error rates
```

**4.4 Cost Monitoring**

```bash
# Enable Cost Explorer for detailed cost tracking
# Monitor daily costs for first week after migration
# Verify costs align with estimates

# Check NAT Gateway data processing charges
aws cloudwatch get-metric-statistics \
  --namespace AWS/NATGateway \
  --metric-name BytesOutToDestination \
  --dimensions Name=NatGatewayId,Value=<nat-gateway-id> \
  --start-time $(date -u -d '1 day ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 3600 \
  --statistics Sum
```

#### Phase 5: Post-Migration Activities (1 week)

**5.1 Documentation Updates**
- Update architecture diagrams to reflect multi-AZ deployment
- Document new subnet IDs and resource ARNs
- Update runbooks and operational procedures
- Update disaster recovery plans

**5.2 Monitoring and Alerting**
- Configure CloudWatch alarms for both AZs
- Set up cross-AZ traffic monitoring
- Create dashboards showing AZ-specific metrics
- Test alert escalation procedures

**5.3 Team Training**
- Train operations team on multi-AZ architecture
- Conduct failover drills
- Document lessons learned
- Update on-call procedures

**5.4 Continuous Optimization**
- Monitor cross-AZ data transfer costs
- Optimize resource placement to minimize cross-AZ traffic
- Review and adjust auto-scaling policies
- Plan for future capacity needs

### Rollback Plan

If issues arise during multi-AZ migration:

```bash
# Rollback to single-AZ configuration
# Update terraform.tfvars
enable_multi_az = false

# Plan and apply rollback
terraform plan -var-file="environments/prod/terraform.tfvars"
terraform apply -var-file="environments/prod/terraform.tfvars"
```

**Warning**: Rollback will destroy resources in us-east-1b. Ensure no critical workloads are running in AZ B before rollback.

## Architectural Changes for Multi-AZ

### Network Architecture Changes

**Single-AZ (Current)**:
```
VPC (10.0.0.0/16)
└── us-east-1a
    ├── Public Subnet A (10.0.1.0/24)
    │   └── NAT Gateway A → Internet Gateway
    ├── Private Subnet 1A (10.0.10.0/24)
    │   └── Route: 0.0.0.0/0 → NAT Gateway A
    └── Private Subnet 2A (10.0.20.0/24)
        └── Route: 0.0.0.0/0 → NAT Gateway A
```

**Multi-AZ (Future)**:
```
VPC (10.0.0.0/16)
├── us-east-1a
│   ├── Public Subnet A (10.0.1.0/24)
│   │   └── NAT Gateway A → Internet Gateway
│   ├── Private Subnet 1A (10.0.10.0/24)
│   │   └── Route: 0.0.0.0/0 → NAT Gateway A
│   └── Private Subnet 2A (10.0.20.0/24)
│       └── Route: 0.0.0.0/0 → NAT Gateway A
└── us-east-1b
    ├── Public Subnet B (10.0.2.0/24)
    │   └── NAT Gateway B → Internet Gateway
    ├── Private Subnet 1B (10.0.11.0/24)
    │   └── Route: 0.0.0.0/0 → NAT Gateway B
    └── Private Subnet 2B (10.0.21.0/24)
        └── Route: 0.0.0.0/0 → NAT Gateway B
```

### Service-Specific Architectural Changes

#### 1. Lambda Functions

**Single-AZ Configuration**:
```hcl
vpc_config {
  subnet_ids         = [private_subnet_1a_id]
  security_group_ids = [lambda_security_group_id]
}
```

**Multi-AZ Configuration**:
```hcl
vpc_config {
  subnet_ids         = [private_subnet_1a_id, private_subnet_1b_id]
  security_group_ids = [lambda_security_group_id]
}
```

**Changes**:
- Lambda automatically distributes executions across both AZs
- Each execution runs in one AZ (not both simultaneously)
- AWS manages load distribution and failover
- No application code changes required

**Benefits**:
- Automatic failover if one AZ becomes unavailable
- Better load distribution during high traffic
- Reduced cold start impact (warm containers in both AZs)

#### 2. MWAA (Apache Airflow)

**Single-AZ Configuration**:
```hcl
network_configuration {
  subnet_ids         = [private_subnet_1a_id]
  security_group_ids = [mwaa_security_group_id]
}
```

**Multi-AZ Configuration**:
```hcl
network_configuration {
  subnet_ids         = [private_subnet_1a_id, private_subnet_1b_id]
  security_group_ids = [mwaa_security_group_id]
}
```

**Changes**:
- MWAA web server and scheduler run in primary AZ
- Worker nodes distributed across both AZs
- Requires environment update (20-30 minute downtime)
- DAG files remain in S3 (already multi-AZ)

**Benefits**:
- Worker redundancy across AZs
- Continued DAG execution if one AZ fails
- Better resource utilization

#### 3. AWS Glue

**Single-AZ Configuration**:
```hcl
connection {
  subnet_id              = private_subnet_2a_id
  security_group_id_list = [glue_security_group_id]
  availability_zone      = "us-east-1a"
}
```

**Multi-AZ Configuration**:
```hcl
# Create connections for both AZs
connection "az_a" {
  subnet_id              = private_subnet_2a_id
  security_group_id_list = [glue_security_group_id]
  availability_zone      = "us-east-1a"
}

connection "az_b" {
  subnet_id              = private_subnet_2b_id
  security_group_id_list = [glue_security_group_id]
  availability_zone      = "us-east-1b"
}
```

**Changes**:
- Glue jobs can use connections from either AZ
- Spark executors distributed across both AZs
- ENIs created in both Private Subnet 2A and 2B
- Job configuration may need updates to specify connection

**Benefits**:
- Job execution continues if one AZ fails
- Better Spark cluster distribution
- Reduced ENI exhaustion risk

#### 4. Amazon Redshift

**Single-AZ Configuration**:
```hcl
cluster {
  availability_zone = "us-east-1a"
  multi_az          = false
}
```

**Multi-AZ Configuration (Option 1: Multi-AZ Cluster)**:
```hcl
cluster {
  multi_az = true  # Only for RA3 node types
}
```

**Multi-AZ Configuration (Option 2: Cross-AZ Snapshots)**:
```hcl
cluster {
  availability_zone           = "us-east-1a"
  automated_snapshot_retention_period = 7
  # Snapshots stored in S3 (multi-AZ by default)
}
```

**Changes**:
- Option 1: Redshift manages multi-AZ automatically (RA3 only)
- Option 2: Use snapshots for DR, manual failover to AZ B
- Security groups must allow access from both AZs
- Connection strings remain the same (DNS-based)

**Benefits**:
- Option 1: Automatic failover, minimal downtime
- Option 2: Cost-effective DR, manual failover required

#### 5. VPC Endpoints

**Single-AZ Configuration**:
```hcl
vpc_endpoint {
  subnet_ids = [private_subnet_1a_id, private_subnet_2a_id]
}
```

**Multi-AZ Configuration**:
```hcl
vpc_endpoint {
  subnet_ids = [
    private_subnet_1a_id,
    private_subnet_2a_id,
    private_subnet_1b_id,
    private_subnet_2b_id
  ]
}
```

**Changes**:
- Interface endpoints create ENIs in all specified subnets
- DNS resolution automatically routes to nearest endpoint
- No application changes required
- Increased ENI usage (2 per endpoint per AZ)

**Benefits**:
- Reduced latency (local AZ endpoint)
- Automatic failover if endpoint in one AZ fails
- Better performance for cross-AZ traffic

#### 6. Security Groups

**No Configuration Changes Required**:
- Security groups are VPC-level resources (not AZ-specific)
- Same security group rules apply to resources in both AZs
- Self-referencing rules work across AZs automatically

**Considerations**:
- Ensure rules allow traffic from both AZ CIDR blocks
- VPC CIDR (10.0.0.0/16) covers both AZs
- No additional rules needed for cross-AZ communication

#### 7. EventBridge

**No Configuration Changes Required**:
- EventBridge is a regional service (not AZ-specific)
- Rules automatically target resources in available AZs
- MWAA targets distributed across worker nodes in both AZs

**Benefits**:
- Automatic failover if MWAA workers in one AZ fail
- Continued rule execution during AZ outage

### Data Flow Changes

**Single-AZ Data Flow**:
```
Webhook → API Gateway (Regional)
  ↓
Lambda (AZ A) → Kinesis Firehose (Regional)
  ↓
S3 (Regional) → Glue Job (AZ A)
  ↓
S3 (Regional) → Redshift (AZ A)
```

**Multi-AZ Data Flow**:
```
Webhook → API Gateway (Regional)
  ↓
Lambda (AZ A or AZ B) → Kinesis Firehose (Regional)
  ↓
S3 (Regional) → Glue Job (AZ A or AZ B)
  ↓
S3 (Regional) → Redshift (AZ A with Multi-AZ or Snapshots)
```

**Key Changes**:
- Lambda and Glue jobs can run in either AZ
- Cross-AZ data transfer when Lambda in AZ A accesses Redshift in AZ A (optimal)
- Cross-AZ data transfer when Lambda in AZ B accesses Redshift in AZ A (cost impact)
- S3 and Kinesis Firehose are regional (no AZ-specific routing)

### Routing and Traffic Patterns

**Intra-AZ Traffic (Optimal)**:
- Lambda (AZ A) → Redshift (AZ A): No cross-AZ charges
- Glue (AZ A) → S3 via VPC Endpoint (AZ A): No cross-AZ charges
- MWAA Worker (AZ A) → Redshift (AZ A): No cross-AZ charges

**Cross-AZ Traffic (Cost Impact)**:
- Lambda (AZ B) → Redshift (AZ A): $0.01/GB cross-AZ charge
- Glue (AZ B) → Redshift (AZ A): $0.01/GB cross-AZ charge
- MWAA Worker (AZ B) → Redshift (AZ A): $0.01/GB cross-AZ charge

**Optimization Strategies**:
1. **Prefer Local AZ Resources**: Configure applications to prefer resources in same AZ
2. **Use S3 for Large Data Transfers**: S3 is regional, no cross-AZ charges
3. **Batch Processing**: Minimize cross-AZ API calls, batch when possible
4. **Monitor Cross-AZ Traffic**: Use CloudWatch to identify high-traffic patterns

### High Availability Benefits

After multi-AZ migration:

1. **NAT Gateway Redundancy**: Two NAT Gateways, one per AZ
   - If NAT Gateway A fails, resources in AZ B continue to function
   - Automatic failover for resources in AZ B
   - Recovery time: 0 seconds (automatic)

2. **AZ Redundancy**: Resources distributed across two AZs
   - If us-east-1a fails, resources in us-east-1b continue to function
   - Reduced impact of AZ-level outages
   - Recovery time: 0 seconds (automatic for stateless services)

3. **Network Redundancy**: Multiple paths to internet
   - Each AZ has its own NAT Gateway and route to internet
   - Reduced single points of failure
   - Independent failure domains

4. **Service Availability**:
   - Lambda: Automatic failover, no downtime
   - MWAA: Worker redundancy, continued DAG execution
   - Glue: Job execution continues in available AZ
   - Redshift: Depends on configuration (multi-AZ or snapshots)
   - API Gateway: Regional service, automatic multi-AZ

### Availability SLA Improvements

**Single-AZ Availability**:
- Estimated availability: 99.5%
- Expected downtime: ~43 hours/year
- MTTR (Mean Time To Recover): Hours to days

**Multi-AZ Availability**:
- Estimated availability: 99.99%
- Expected downtime: ~52 minutes/year
- MTTR (Mean Time To Recover): 0 seconds (automatic failover)

**Improvement**: 50x reduction in downtime

### Cost Implications

**Single-AZ Monthly Costs**:
- NAT Gateway: ~$32/month
- Elastic IP: ~$3.60/month
- Data transfer: Variable
- **Total**: ~$35.60/month + data transfer

**Multi-AZ Monthly Costs**:
- NAT Gateway A: ~$32/month
- NAT Gateway B: ~$32/month
- Elastic IP A: ~$3.60/month
- Elastic IP B: ~$3.60/month
- Cross-AZ data transfer: ~$0.01/GB
- **Total**: ~$71.20/month + data transfer

**Cost Increase**: ~$35.60/month + cross-AZ data transfer costs

## Terraform Configuration

### Variable Configuration

The multi-AZ feature is controlled by a single variable:

```hcl
# terraform/variables.tf
variable "enable_multi_az" {
  description = "Enable Multi-AZ deployment (creates resources in us-east-1b)"
  type        = bool
  default     = false
}
```

### Conditional Resource Creation

Resources in us-east-1b are created conditionally:

```hcl
# terraform/modules/vpc/main.tf

# Public Subnet B (us-east-1b)
resource "aws_subnet" "public_b" {
  count = var.enable_multi_az ? 1 : 0
  
  vpc_id                  = aws_vpc.main.id
  cidr_block              = var.public_subnet_b_cidr
  availability_zone       = "us-east-1b"
  map_public_ip_on_launch = true
  
  tags = merge(var.tags, {
    Name = "${var.name_prefix}-public-subnet-b"
    Tier = "Public"
    AZ   = "us-east-1b"
  })
}

# Private Subnet 1B (us-east-1b)
resource "aws_subnet" "private_1b" {
  count = var.enable_multi_az ? 1 : 0
  
  vpc_id                  = aws_vpc.main.id
  cidr_block              = var.private_subnet_1b_cidr
  availability_zone       = "us-east-1b"
  map_public_ip_on_launch = false
  
  tags = merge(var.tags, {
    Name    = "${var.name_prefix}-private-subnet-1b"
    Tier    = "Private"
    Purpose = "Lambda, MWAA, Redshift"
    AZ      = "us-east-1b"
  })
}

# Private Subnet 2B (us-east-1b)
resource "aws_subnet" "private_2b" {
  count = var.enable_multi_az ? 1 : 0
  
  vpc_id                  = aws_vpc.main.id
  cidr_block              = var.private_subnet_2b_cidr
  availability_zone       = "us-east-1b"
  map_public_ip_on_launch = false
  
  tags = merge(var.tags, {
    Name    = "${var.name_prefix}-private-subnet-2b"
    Tier    = "Private"
    Purpose = "Glue ENIs"
    AZ      = "us-east-1b"
  })
}

# Elastic IP for NAT Gateway B
resource "aws_eip" "nat_b" {
  count = var.enable_multi_az ? 1 : 0
  
  domain = "vpc"
  
  tags = merge(var.tags, {
    Name = "${var.name_prefix}-nat-eip-b"
    AZ   = "us-east-1b"
  })
}

# NAT Gateway B
resource "aws_nat_gateway" "main_b" {
  count = var.enable_multi_az ? 1 : 0
  
  allocation_id = aws_eip.nat_b[0].id
  subnet_id     = aws_subnet.public_b[0].id
  
  tags = merge(var.tags, {
    Name = "${var.name_prefix}-nat-gateway-b"
    AZ   = "us-east-1b"
  })
  
  depends_on = [aws_internet_gateway.main]
}

# Private Route Table B
resource "aws_route_table" "private_b" {
  count = var.enable_multi_az ? 1 : 0
  
  vpc_id = aws_vpc.main.id
  
  tags = merge(var.tags, {
    Name = "${var.name_prefix}-private-rt-b"
    Tier = "Private"
    AZ   = "us-east-1b"
  })
}

# Route to NAT Gateway B
resource "aws_route" "private_nat_b" {
  count = var.enable_multi_az ? 1 : 0
  
  route_table_id         = aws_route_table.private_b[0].id
  destination_cidr_block = "0.0.0.0/0"
  nat_gateway_id         = aws_nat_gateway.main_b[0].id
}

# Associate Private Subnet 1B with Private Route Table B
resource "aws_route_table_association" "private_1b" {
  count = var.enable_multi_az ? 1 : 0
  
  subnet_id      = aws_subnet.private_1b[0].id
  route_table_id = aws_route_table.private_b[0].id
}

# Associate Private Subnet 2B with Private Route Table B
resource "aws_route_table_association" "private_2b" {
  count = var.enable_multi_az ? 1 : 0
  
  subnet_id      = aws_subnet.private_2b[0].id
  route_table_id = aws_route_table.private_b[0].id
}
```

### Reserved CIDR Variables

Reserved CIDR blocks are defined with default values:

```hcl
# terraform/variables.tf
variable "public_subnet_b_cidr" {
  description = "CIDR block for public subnet in AZ B (reserved for Multi-AZ)"
  type        = string
  default     = "10.0.2.0/24"
}

variable "private_subnet_1b_cidr" {
  description = "CIDR block for private subnet 1B (reserved for Multi-AZ)"
  type        = string
  default     = "10.0.11.0/24"
}

variable "private_subnet_2b_cidr" {
  description = "CIDR block for private subnet 2B (reserved for Multi-AZ)"
  type        = string
  default     = "10.0.21.0/24"
}
```

### Output Updates

Update outputs to handle both single-AZ and multi-AZ configurations:

```hcl
# terraform/modules/vpc/outputs.tf

output "public_subnet_ids" {
  description = "List of public subnet IDs"
  value = concat(
    [aws_subnet.public_a.id],
    var.enable_multi_az ? [aws_subnet.public_b[0].id] : []
  )
}

output "private_subnet_1_ids" {
  description = "List of private subnet 1 IDs (Lambda, MWAA, Redshift)"
  value = concat(
    [aws_subnet.private_1a.id],
    var.enable_multi_az ? [aws_subnet.private_1b[0].id] : []
  )
}

output "private_subnet_2_ids" {
  description = "List of private subnet 2 IDs (Glue ENIs)"
  value = concat(
    [aws_subnet.private_2a.id],
    var.enable_multi_az ? [aws_subnet.private_2b[0].id] : []
  )
}

output "nat_gateway_ids" {
  description = "List of NAT Gateway IDs"
  value = concat(
    [aws_nat_gateway.main_a.id],
    var.enable_multi_az ? [aws_nat_gateway.main_b[0].id] : []
  )
}

output "availability_zones" {
  description = "List of availability zones in use"
  value = var.enable_multi_az ? ["us-east-1a", "us-east-1b"] : ["us-east-1a"]
}
```

### VPC Endpoint Updates

Update VPC endpoints to include subnets from both AZs:

```hcl
# terraform/modules/vpc-endpoints/main.tf

resource "aws_vpc_endpoint" "glue" {
  vpc_id              = var.vpc_id
  service_name        = "com.amazonaws.${var.aws_region}.glue"
  vpc_endpoint_type   = "Interface"
  
  subnet_ids = concat(
    var.private_subnet_1_ids,
    var.private_subnet_2_ids
  )
  
  security_group_ids  = [var.vpc_endpoint_security_group_id]
  private_dns_enabled = true
  
  tags = merge(var.tags, {
    Name = "${var.name_prefix}-glue-endpoint"
  })
}

# Similar updates for other Interface Endpoints:
# - Secrets Manager
# - CloudWatch Logs
# - KMS
# - STS
# - EventBridge
```

### Lambda Function Updates

Update Lambda functions to use subnets from both AZs:

```hcl
# terraform/modules/lambda/main.tf

resource "aws_lambda_function" "webhook_processor" {
  function_name = "${var.name_prefix}-webhook-processor"
  role          = aws_iam_role.lambda.arn
  
  vpc_config {
    subnet_ids         = var.private_subnet_1_ids  # Now includes both AZs
    security_group_ids = [var.lambda_security_group_id]
  }
  
  # ... other configuration
}
```

### MWAA Environment Updates

Update MWAA to use subnets from both AZs:

```hcl
# terraform/modules/mwaa/main.tf

resource "aws_mwaa_environment" "main" {
  name = "${var.name_prefix}-mwaa-environment"
  
  network_configuration {
    subnet_ids         = var.private_subnet_1_ids  # Now includes both AZs
    security_group_ids = [var.mwaa_security_group_id]
  }
  
  # ... other configuration
}
```

### Terraform State Considerations

**Important**: Enabling multi-AZ creates new resources but does NOT modify existing resources. This means:

1. **No Downtime for Existing Resources**: Existing Lambda, MWAA, Glue remain operational
2. **Incremental Migration**: Update application configurations gradually
3. **Rollback Safety**: Can disable multi-AZ without destroying existing resources
4. **State File Growth**: State file will include additional resources

**State File Backup**:
```bash
# Always backup state before enabling multi-AZ
cp terraform.tfstate terraform.tfstate.backup.$(date +%Y%m%d_%H%M%S)
```

## Monitoring and Alerting

### Single-AZ Monitoring

Current monitoring focuses on single points of failure:

1. **NAT Gateway Health**: Monitor connection count and error rate
2. **AZ Availability**: Monitor AWS Service Health Dashboard
3. **Network Connectivity**: Monitor VPC Flow Logs for connection failures

### Multi-AZ Monitoring

After multi-AZ migration, add monitoring for:

1. **Cross-AZ Traffic**: Monitor data transfer costs and patterns
2. **AZ-Specific Metrics**: Compare metrics across AZs for anomalies
3. **Failover Testing**: Regular automated failover tests

## References

- **Requirements**: 2.3, 12.3, 12.4, 12.5
- **Design Document**: `.kiro/specs/01-aws-infrastructure/design.md`
- **Single-AZ Documentation**: `terraform/SINGLE_AZ_DEPLOYMENT.md`
- **AWS Multi-AZ Best Practices**: https://docs.aws.amazon.com/vpc/latest/userguide/vpc-subnets-commands-example.html
- **AWS NAT Gateway**: https://docs.aws.amazon.com/vpc/latest/userguide/vpc-nat-gateway.html
- **AWS Lambda Multi-AZ**: https://docs.aws.amazon.com/lambda/latest/dg/configuration-vpc.html
- **AWS MWAA High Availability**: https://docs.aws.amazon.com/mwaa/latest/userguide/vpc-create.html

## Risk Assessment and Decision Framework

### When to Migrate to Multi-AZ

Consider multi-AZ migration when:

1. **Business Impact of Downtime is High**
   - Revenue loss > $1,000/hour during outage
   - Critical business decisions depend on real-time data
   - SLA commitments to customers require high availability
   - Regulatory compliance requires specific uptime guarantees

2. **Current Availability is Insufficient**
   - Experiencing frequent AZ-related issues
   - AWS Service Health Dashboard shows recurring AZ problems
   - Business stakeholders requesting higher availability
   - Competitive pressure requires better uptime

3. **Cost-Benefit Analysis Favors Multi-AZ**
   - Cost of downtime > Cost of multi-AZ (~$35/month)
   - Business growth justifies infrastructure investment
   - Budget available for infrastructure improvements
   - Long-term cost savings from reduced incident response

4. **Operational Maturity is Sufficient**
   - Team has experience with multi-AZ architectures
   - Monitoring and alerting systems are mature
   - Disaster recovery procedures are documented and tested
   - Change management processes are established

### When to Stay Single-AZ

Consider staying single-AZ when:

1. **Cost Constraints are Tight**
   - Budget cannot accommodate ~$35/month increase
   - Cost of downtime < Cost of multi-AZ
   - Early-stage project with uncertain future
   - Proof-of-concept or development environment

2. **Availability Requirements are Modest**
   - 99.5% availability is acceptable (43 hours/year downtime)
   - Business can tolerate occasional outages
   - No SLA commitments requiring higher availability
   - Manual processes can handle temporary unavailability

3. **Operational Complexity is a Concern**
   - Small team without multi-AZ experience
   - Limited operational resources for monitoring
   - Prefer simpler architecture for easier troubleshooting
   - Risk of misconfiguration outweighs availability benefits

4. **Temporary Deployment**
   - Short-term project (< 6 months)
   - Planned migration to different architecture
   - Proof-of-concept or pilot program
   - Development or testing environment

### Decision Matrix

| Factor | Weight | Single-AZ Score | Multi-AZ Score | Recommendation |
|--------|--------|-----------------|----------------|----------------|
| Cost | 20% | 10 (Lower cost) | 5 (Higher cost) | Depends on budget |
| Availability | 30% | 5 (99.5%) | 10 (99.99%) | Multi-AZ for production |
| Complexity | 15% | 10 (Simpler) | 6 (More complex) | Single-AZ for small teams |
| Scalability | 15% | 6 (Limited) | 10 (Better) | Multi-AZ for growth |
| Recovery Time | 20% | 3 (Hours) | 10 (Automatic) | Multi-AZ for critical systems |

**Scoring Guide**:
- Calculate weighted score: (Factor Weight × Score) for each option
- Single-AZ Total: (20%×10) + (30%×5) + (15%×10) + (15%×6) + (20%×3) = 6.6
- Multi-AZ Total: (20%×5) + (30%×10) + (15%×6) + (15%×10) + (20%×10) = 8.4
- **Recommendation**: Multi-AZ for production workloads, Single-AZ for dev/test

### Migration Timeline Recommendations

**Immediate (0-1 month)**:
- Stay single-AZ during initial deployment
- Focus on core functionality and stability
- Establish monitoring and alerting
- Document architecture and procedures

**Short-term (1-3 months)**:
- Evaluate availability requirements based on actual usage
- Analyze cost of downtime from any incidents
- Assess team readiness for multi-AZ management
- Plan multi-AZ migration if business case is strong

**Medium-term (3-6 months)**:
- Execute multi-AZ migration for production environment
- Maintain single-AZ for development/staging (cost savings)
- Implement comprehensive monitoring across AZs
- Conduct regular failover drills

**Long-term (6+ months)**:
- Consider cross-region disaster recovery
- Evaluate additional availability improvements
- Optimize costs through reserved instances
- Continuously improve operational procedures

## Troubleshooting Multi-AZ Issues

### Common Issues and Solutions

#### Issue 1: High Cross-AZ Data Transfer Costs

**Symptoms**:
- Unexpected increase in AWS bill
- CloudWatch shows high cross-AZ traffic
- Cost Explorer shows significant data transfer charges

**Root Causes**:
- Lambda in AZ B frequently accessing Redshift in AZ A
- Glue jobs in AZ B reading/writing large datasets to Redshift in AZ A
- Inefficient data flow patterns

**Solutions**:
1. **Optimize Resource Placement**:
   ```bash
   # Pin Lambda functions to specific AZ if they frequently access Redshift
   # Use subnet_ids with only AZ A subnet
   ```

2. **Use S3 for Large Data Transfers**:
   ```python
   # Instead of direct Redshift writes from AZ B
   # Write to S3 first (no cross-AZ charges), then COPY to Redshift
   ```

3. **Monitor and Alert**:
   ```bash
   # Set up CloudWatch alarm for cross-AZ data transfer
   aws cloudwatch put-metric-alarm \
     --alarm-name high-cross-az-transfer \
     --metric-name BytesOutToDestination \
     --namespace AWS/NATGateway \
     --threshold 100000000000  # 100 GB
   ```

#### Issue 2: Uneven Load Distribution

**Symptoms**:
- Most Lambda executions in one AZ
- One NAT Gateway heavily utilized, other idle
- Performance degradation in one AZ

**Root Causes**:
- AWS Lambda load balancing favoring one AZ
- Application configuration pinning to specific AZ
- Network issues in one AZ

**Solutions**:
1. **Verify Subnet Configuration**:
   ```bash
   # Ensure Lambda has both subnets configured
   aws lambda get-function-configuration \
     --function-name janis-cencosud-webhook-processor-prod \
     --query 'VpcConfig.SubnetIds'
   ```

2. **Check AWS Service Health**:
   ```bash
   # Verify no issues with specific AZ
   aws health describe-events \
     --filter eventTypeCategories=issue
   ```

3. **Force Rebalancing**:
   ```bash
   # Update Lambda configuration to trigger rebalancing
   aws lambda update-function-configuration \
     --function-name janis-cencosud-webhook-processor-prod \
     --description "Force rebalancing $(date)"
   ```

#### Issue 3: VPC Endpoint Connectivity Issues

**Symptoms**:
- Intermittent connection failures to AWS services
- Increased latency for VPC endpoint calls
- Error logs showing endpoint timeouts

**Root Causes**:
- VPC endpoint not associated with all subnets
- Security group rules blocking cross-AZ traffic
- DNS resolution issues

**Solutions**:
1. **Verify Endpoint Subnet Associations**:
   ```bash
   aws ec2 describe-vpc-endpoints \
     --vpc-endpoint-ids <endpoint-id> \
     --query 'VpcEndpoints[0].SubnetIds'
   ```

2. **Check Security Group Rules**:
   ```bash
   aws ec2 describe-security-groups \
     --group-ids <sg-id> \
     --query 'SecurityGroups[0].IpPermissions'
   ```

3. **Test DNS Resolution**:
   ```bash
   # From Lambda or EC2 in each AZ
   nslookup glue.us-east-1.amazonaws.com
   ```

#### Issue 4: MWAA Worker Distribution Issues

**Symptoms**:
- All MWAA workers in one AZ
- DAG execution failures during AZ issues
- Uneven resource utilization

**Root Causes**:
- MWAA environment not updated with both subnets
- Insufficient worker capacity in one AZ
- Network connectivity issues

**Solutions**:
1. **Verify MWAA Configuration**:
   ```bash
   aws mwaa get-environment \
     --name cencosud-mwaa-environment \
     --query 'Environment.NetworkConfiguration.SubnetIds'
   ```

2. **Update MWAA Environment**:
   ```bash
   # If only one subnet configured, update to include both
   aws mwaa update-environment \
     --name cencosud-mwaa-environment \
     --network-configuration SubnetIds=<subnet-1a>,<subnet-1b>
   ```

3. **Monitor Worker Distribution**:
   ```bash
   # Check CloudWatch Logs for worker AZ distribution
   aws logs filter-log-events \
     --log-group-name /aws/mwaa/cencosud-mwaa-environment \
     --filter-pattern "worker"
   ```

## Best Practices for Multi-AZ Operations

### 1. Monitoring and Observability

**AZ-Specific Dashboards**:
- Create separate CloudWatch dashboards for each AZ
- Monitor metrics by AZ dimension
- Set up alarms for AZ-specific anomalies
- Track cross-AZ data transfer costs

**Key Metrics to Monitor**:
- NAT Gateway connection count per AZ
- Lambda invocation count per AZ
- VPC endpoint request count per AZ
- Cross-AZ data transfer volume
- Error rates by AZ

### 2. Cost Optimization

**Minimize Cross-AZ Traffic**:
- Use S3 for large data transfers (regional service)
- Pin latency-sensitive workloads to same AZ as dependencies
- Batch cross-AZ API calls
- Use VPC endpoints to reduce NAT Gateway usage

**Monitor Costs**:
- Enable Cost Explorer with AZ-level granularity
- Set up billing alarms for unexpected increases
- Review Cost and Usage Reports monthly
- Tag resources by AZ for cost allocation

### 3. Operational Procedures

**Regular Failover Testing**:
- Conduct monthly failover drills
- Test application behavior during AZ failure
- Validate monitoring and alerting
- Document lessons learned

**Change Management**:
- Test changes in single-AZ dev environment first
- Deploy to multi-AZ staging for validation
- Use blue-green deployments for production
- Maintain rollback procedures

**Incident Response**:
- Define escalation procedures for AZ failures
- Maintain runbooks for common scenarios
- Conduct post-incident reviews
- Update documentation based on incidents

### 4. Security Considerations

**Network Security**:
- Ensure security groups allow cross-AZ traffic
- Verify NACLs don't block inter-AZ communication
- Use VPC Flow Logs to monitor cross-AZ traffic
- Implement least privilege for cross-AZ access

**Data Security**:
- Encrypt data in transit between AZs
- Use KMS for encryption key management
- Implement data classification and handling policies
- Audit cross-AZ data transfers

## Change Log

| Date | Version | Changes | Author |
|------|---------|---------|--------|
| 2026-01-26 | 2.0 | Enhanced with detailed migration steps, architectural changes, risk assessment, and troubleshooting guide | Kiro AI |
| 2026-01-22 | 1.0 | Initial documentation of reserved CIDR blocks and multi-AZ migration path | Kiro AI |

