# Single-AZ Deployment Documentation

## Overview

The Janis-Cencosud AWS infrastructure is initially deployed in a **single Availability Zone (us-east-1a)** to reduce costs and complexity during the initial implementation phase. This document identifies the single points of failure, deployment limitations, and the impact of potential AZ failures.

## Single Points of Failure

### 1. NAT Gateway (Critical)

**Location**: Public Subnet A (10.0.1.0/24) in us-east-1a

**Function**: Provides internet connectivity for all private subnets

**Single Point of Failure Impact**:
- **Severity**: HIGH
- **Affected Services**: All services in private subnets (Lambda, MWAA, Glue, Redshift)
- **Impact**: Complete loss of internet connectivity for private resources
- **Services Affected**:
  - Lambda functions cannot access external APIs or services
  - MWAA cannot download DAG dependencies or connect to external systems
  - Glue jobs cannot access external data sources
  - Redshift cannot load data from external sources
  - No outbound HTTPS traffic to VPC endpoints or internet

**Failure Scenarios**:
- NAT Gateway hardware failure (AWS managed, rare but possible)
- NAT Gateway capacity exhaustion (connection limits reached)
- Elastic IP disassociation or release
- AWS service disruption affecting NAT Gateway service

**Detection**:
- CloudWatch alarms on NAT Gateway connection count
- CloudWatch alarms on NAT Gateway error rate
- VPC Flow Logs showing rejected connections from private subnets
- Application-level timeouts and connection failures

**Recovery Time**:
- Manual intervention required: 5-15 minutes
- Terraform recreation: 2-5 minutes
- Total estimated downtime: 7-20 minutes

**Mitigation (Current)**:
- CloudWatch alarms configured for NAT Gateway metrics
- VPC Flow Logs enabled for connection monitoring
- Documented recovery procedure (see Recovery Procedures section)

**Future Multi-AZ Solution**:
- Deploy second NAT Gateway in Public Subnet B (us-east-1b)
- Configure route tables to use local AZ NAT Gateway
- Automatic failover through route table updates

### 2. Availability Zone Failure (Critical)

**Location**: All resources deployed in us-east-1a

**Function**: Physical data center hosting all infrastructure

**Single Point of Failure Impact**:
- **Severity**: CRITICAL
- **Affected Services**: ALL services and data
- **Impact**: Complete system unavailability
- **Services Affected**:
  - API Gateway webhook endpoints unavailable
  - Lambda functions cannot execute
  - MWAA workflows cannot run
  - Glue jobs cannot process data
  - Redshift cluster unavailable
  - S3 data remains accessible (S3 is region-level, not AZ-level)
  - EventBridge rules cannot trigger (targets unavailable)

**Failure Scenarios**:
- AWS Availability Zone outage (rare, typically < 0.1% annual probability)
- Power failure affecting entire AZ
- Network connectivity issues to AZ
- Natural disaster or physical damage to data center

**Detection**:
- AWS Service Health Dashboard notifications
- CloudWatch alarms showing all services down
- Application-level complete unavailability
- AWS Personal Health Dashboard alerts

**Recovery Time**:
- Wait for AWS to restore AZ: Hours to days (AWS SLA dependent)
- Manual migration to different AZ: 2-4 hours
- Total estimated downtime: Hours to days

**Mitigation (Current)**:
- AWS Service Health Dashboard monitoring
- CloudWatch alarms for service availability
- Documented disaster recovery procedure
- Regular backups of critical data

**Future Multi-AZ Solution**:
- Deploy resources across us-east-1a and us-east-1b
- Automatic failover for stateless services
- Multi-AZ Redshift cluster for database availability
- Load balancing across AZs

### 3. Internet Gateway (Low Risk)

**Location**: Attached to VPC (region-level resource)

**Function**: Provides internet connectivity for public subnet

**Single Point of Failure Impact**:
- **Severity**: LOW (AWS manages redundancy)
- **Affected Services**: Public subnet resources and NAT Gateway
- **Impact**: Loss of inbound webhook traffic and NAT Gateway functionality

**Failure Scenarios**:
- AWS-managed Internet Gateway failure (extremely rare, AWS handles redundancy)

**Detection**:
- VPC Flow Logs showing routing failures
- CloudWatch alarms on IGW packet loss

**Recovery Time**:
- Automatic by AWS (no manual intervention required)
- Typical recovery: < 1 minute

**Mitigation (Current)**:
- AWS manages Internet Gateway redundancy automatically
- No additional configuration required

### 4. VPC Endpoints (Medium Risk)

**Location**: Interface Endpoints in Private Subnets (us-east-1a)

**Function**: Private connectivity to AWS services

**Single Point of Failure Impact**:
- **Severity**: MEDIUM
- **Affected Services**: Services using VPC endpoints (Glue, Secrets Manager, CloudWatch, KMS, STS, EventBridge)
- **Impact**: Degraded performance, fallback to NAT Gateway routing

**Failure Scenarios**:
- VPC Endpoint service disruption
- Network connectivity issues to endpoint
- Endpoint ENI failure

**Detection**:
- Service-specific error codes (503, connection timeouts)
- CloudWatch Logs showing endpoint connection errors
- Increased NAT Gateway traffic (fallback routing)

**Recovery Time**:
- Automatic fallback to NAT Gateway: Immediate
- Endpoint recreation: 2-5 minutes

**Mitigation (Current)**:
- Automatic retry with exponential backoff in application code
- Fallback to NAT Gateway routing for internet-based service access
- CloudWatch alarms for endpoint availability

**Future Multi-AZ Solution**:
- Deploy VPC endpoints in multiple subnets across AZs
- Automatic failover through DNS resolution

## Single-AZ Deployment Limitations

### Availability Limitations

1. **No Automatic Failover**
   - All resources in single AZ means no automatic failover capability
   - Manual intervention required for all failure scenarios
   - Recovery depends on AWS restoring AZ or manual migration

2. **Reduced Availability SLA**
   - Single-AZ deployment typically provides 99.5% availability
   - Multi-AZ deployment provides 99.99% availability
   - Difference: ~43 hours vs ~52 minutes of downtime per year

3. **Maintenance Windows**
   - AWS maintenance on us-east-1a affects all services
   - No ability to perform rolling updates across AZs
   - Planned maintenance requires complete system downtime

### Performance Limitations

1. **Network Bottlenecks**
   - Single NAT Gateway can become bottleneck for high-traffic workloads
   - NAT Gateway connection limits: 55,000 simultaneous connections
   - Bandwidth limits: 45 Gbps (burst), 5 Gbps (sustained)

2. **Resource Contention**
   - All resources competing for capacity in single AZ
   - Potential for "noisy neighbor" effects
   - Limited ability to distribute load

### Scalability Limitations

1. **Capacity Constraints**
   - Limited to capacity available in single AZ
   - Cannot scale beyond AZ limits
   - Potential for resource exhaustion during peak loads

2. **IP Address Exhaustion**
   - Fixed CIDR blocks per subnet
   - Cannot easily expand without disruption
   - Must plan capacity carefully

### Cost Implications

1. **Data Transfer Costs**
   - All inter-service communication within single AZ (no cross-AZ charges)
   - Lower data transfer costs compared to multi-AZ
   - Trade-off: Lower costs vs. lower availability

2. **NAT Gateway Costs**
   - Single NAT Gateway: ~$32/month + data processing charges
   - Multi-AZ would require 2 NAT Gateways: ~$64/month
   - Current savings: ~$32/month

## Impact of AZ Failure

### Immediate Impact (T+0 to T+5 minutes)

1. **Service Unavailability**
   - All API Gateway endpoints return 503 errors
   - Webhook ingestion completely stopped
   - No new data entering the system

2. **Processing Halt**
   - All Lambda functions fail to execute
   - MWAA workflows cannot run
   - Glue jobs terminate abnormally
   - EventBridge rules cannot trigger targets

3. **Data Access Loss**
   - Redshift cluster unavailable
   - BI tools cannot query data
   - Dashboards show stale data

4. **Monitoring Degradation**
   - CloudWatch metrics may be delayed
   - Alarms may not trigger immediately
   - VPC Flow Logs may have gaps

### Short-Term Impact (T+5 minutes to T+1 hour)

1. **Data Loss Risk**
   - In-flight webhook data lost (not yet persisted to S3)
   - Kinesis Firehose buffers may be lost
   - Incomplete Glue job transformations

2. **Business Impact**
   - Orders not synchronized to Redshift
   - Inventory data becomes stale
   - BI reports show outdated information
   - Business decisions based on incomplete data

3. **Operational Impact**
   - On-call team alerted
   - Incident response procedures initiated
   - Communication to stakeholders required

### Medium-Term Impact (T+1 hour to T+24 hours)

1. **Data Backlog**
   - Accumulated webhook events need reprocessing
   - Polling schedules missed
   - Large data backlog to process once recovered

2. **Recovery Efforts**
   - Manual intervention to restore services
   - Potential data reconciliation required
   - Testing and validation of restored services

3. **Business Continuity**
   - Fallback to manual processes
   - Alternative data sources for critical decisions
   - Customer communication about service disruption

### Long-Term Impact (T+24 hours+)

1. **Data Integrity Concerns**
   - Potential gaps in historical data
   - Need for data quality validation
   - Reconciliation with source systems

2. **Trust and Reliability**
   - Stakeholder confidence in system reliability
   - Pressure to implement multi-AZ solution
   - Increased scrutiny of architecture decisions

## Recovery Procedures

### NAT Gateway Failure Recovery

**Automated Detection**:
```bash
# CloudWatch alarm triggers on NAT Gateway connection failures
# SNS notification sent to operations team
```

**Manual Recovery Steps**:

1. **Verify Failure**:
   ```bash
   # Check NAT Gateway status
   aws ec2 describe-nat-gateways --nat-gateway-ids <nat-gateway-id>
   
   # Check VPC Flow Logs for connection failures
   aws logs filter-log-events \
     --log-group-name /aws/vpc/flowlogs \
     --filter-pattern "[version, account, eni, source, destination, srcport, dstport, protocol, packets, bytes, start, end, action=REJECT, status]"
   ```

2. **Recreate NAT Gateway** (if necessary):
   ```bash
   # Using Terraform
   cd terraform/environments/prod
   terraform taint aws_nat_gateway.main
   terraform apply -var-file="prod.tfvars"
   ```

3. **Verify Recovery**:
   ```bash
   # Test connectivity from private subnet
   # Check Lambda function execution
   # Verify MWAA can access external resources
   ```

4. **Post-Recovery**:
   - Review CloudWatch metrics
   - Validate all services operational
   - Document incident and lessons learned

**Estimated Recovery Time**: 7-20 minutes

### Availability Zone Failure Recovery

**Automated Detection**:
```bash
# AWS Service Health Dashboard notifications
# CloudWatch alarms showing all services down
```

**Manual Recovery Options**:

**Option 1: Wait for AWS to Restore AZ** (Recommended for short outages)
- Monitor AWS Service Health Dashboard
- Communicate status to stakeholders
- Prepare for service restoration
- Estimated time: Hours to days (AWS dependent)

**Option 2: Manual Migration to Different AZ** (For extended outages)

1. **Prepare New Environment**:
   ```bash
   # Update Terraform configuration to use us-east-1b
   # Modify subnet configurations
   # Update availability zone references
   ```

2. **Deploy to New AZ**:
   ```bash
   cd terraform/environments/prod
   terraform apply -var-file="prod.tfvars" -var="availability_zone=us-east-1b"
   ```

3. **Restore Data**:
   ```bash
   # Restore Redshift from latest snapshot
   # Verify S3 data integrity (S3 is region-level, should be intact)
   # Replay missed webhook events from source system
   ```

4. **Validate and Switch**:
   ```bash
   # Test all services in new AZ
   # Update DNS/routing if necessary
   # Communicate restoration to stakeholders
   ```

**Estimated Recovery Time**: 2-4 hours

## Monitoring and Alerting

### Critical Alarms

1. **NAT Gateway Health**:
   - Metric: `ConnectionAttemptCount`, `ConnectionEstablishedCount`
   - Threshold: Connection success rate < 95%
   - Action: Page on-call engineer

2. **AZ Availability**:
   - Metric: Service-specific health checks
   - Threshold: All services unavailable
   - Action: Escalate to senior engineering

3. **VPC Endpoint Health**:
   - Metric: Endpoint connection errors
   - Threshold: Error rate > 5%
   - Action: Alert operations team

### Monitoring Dashboard

Key metrics to monitor:
- NAT Gateway connection count and error rate
- VPC Flow Logs for rejected connections
- Lambda function error rates
- MWAA workflow success rates
- Glue job completion rates
- Redshift cluster availability
- API Gateway 5xx error rates

## Recommendations

### Immediate Actions

1. **Document Recovery Procedures**:
   - Create runbooks for each failure scenario
   - Train operations team on recovery procedures
   - Conduct disaster recovery drills

2. **Enhance Monitoring**:
   - Implement comprehensive CloudWatch alarms
   - Create operational dashboards
   - Set up automated health checks

3. **Improve Backup Strategy**:
   - Automate Redshift snapshots
   - Implement S3 versioning for critical data
   - Test restore procedures regularly

### Short-Term Actions (1-3 months)

1. **Plan Multi-AZ Migration**:
   - Review MULTI_AZ_EXPANSION.md documentation
   - Estimate costs and timeline
   - Obtain stakeholder approval

2. **Implement Additional Redundancy**:
   - Consider Lambda function retries
   - Implement circuit breakers
   - Add dead letter queues for failed events

### Long-Term Actions (3-6 months)

1. **Execute Multi-AZ Migration**:
   - Deploy resources across us-east-1a and us-east-1b
   - Implement automatic failover
   - Achieve 99.99% availability SLA

2. **Implement Disaster Recovery**:
   - Cross-region replication for critical data
   - Automated failover to secondary region
   - Regular DR testing and validation

## Conclusion

The single-AZ deployment provides a cost-effective initial implementation but introduces significant availability risks. The primary single points of failure are:

1. **NAT Gateway** (HIGH risk, 7-20 minute recovery)
2. **Availability Zone** (CRITICAL risk, hours to days recovery)
3. **VPC Endpoints** (MEDIUM risk, automatic fallback)

Organizations should carefully weigh the cost savings (~$32/month for NAT Gateway alone) against the availability risks and potential business impact of extended outages. For production workloads requiring high availability, migration to multi-AZ deployment is strongly recommended.

See **MULTI_AZ_EXPANSION.md** for detailed migration planning and implementation guidance.
