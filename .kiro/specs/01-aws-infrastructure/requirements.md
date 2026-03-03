# Requirements Document: AWS Infrastructure

## Introduction

Este documento define los requerimientos para la infraestructura AWS que soportará la integración de datos entre Janis y el Redshift existente de Cencosud a través del nuevo Data Lake. La infraestructura debe proporcionar una base segura, escalable y resiliente para todos los componentes del pipeline de datos, manteniendo compatibilidad con la infraestructura existente de Cencosud.

## Glossary

- **VPC**: Virtual Private Cloud - Red virtual aislada en AWS
- **Security_Group**: Firewall virtual que controla tráfico de instancias
- **VPC_Endpoint**: Conexión privada entre VPC y servicios AWS
- **NAT_Gateway**: Servicio que permite acceso a internet desde subredes privadas
- **WAF**: Web Application Firewall - Protección contra ataques web
- **CIDR**: Classless Inter-Domain Routing - Notación para rangos IP
- **AZ**: Availability Zone - Zona de disponibilidad física en AWS
- **EventBridge**: Amazon EventBridge - Servicio de eventos serverless para orquestación

## Requirements

### Requirement 1: VPC Network Foundation

**User Story:** Como arquitecto de infraestructura, quiero establecer una VPC segura y bien estructurada, para que todos los servicios del pipeline de datos operen en un entorno de red aislado y controlado.

#### Acceptance Criteria

1. THE VPC SHALL be created with CIDR block 10.0.0.0/16 providing 65,536 IP addresses
2. THE VPC SHALL be deployed in a single Availability Zone (us-east-1a) for initial implementation
3. THE VPC SHALL have DNS resolution and DNS hostnames enabled
4. THE VPC SHALL be tagged with project identification and environment information
5. THE VPC SHALL support both IPv4 and be prepared for future IPv6 requirements
6. THE VPC SHALL be designed to support future multi-AZ expansion without requiring major architectural changes

### Requirement 2: Subnet Architecture

**User Story:** Como ingeniero de redes, quiero organizar las subredes de manera lógica, para que los recursos públicos y privados estén correctamente segregados según sus necesidades de conectividad.

#### Acceptance Criteria

1. THE System SHALL create one public subnet (10.0.1.0/24) in us-east-1a for internet-facing resources
2. THE System SHALL create two private subnets in us-east-1a for internal resources:
   - Private 1A: 10.0.10.0/24 (Redshift, MWAA, Lambda)
   - Private 2A: 10.0.20.0/24 (Glue ENIs)
3. THE System SHALL reserve CIDR blocks for future multi-AZ expansion:
   - Public Subnet B: 10.0.2.0/24 (reserved for us-east-1b)
   - Private Subnet 1B: 10.0.11.0/24 (reserved for us-east-1b)
   - Private Subnet 2B: 10.0.21.0/24 (reserved for us-east-1b)
4. THE System SHALL enable automatic public IP assignment only for public subnets
5. THE System SHALL tag all subnets with their purpose and tier information

### Requirement 3: Internet Connectivity

**User Story:** Como administrador de sistemas, quiero configurar el acceso a internet de manera segura, para que los recursos privados puedan acceder a servicios externos sin exponerse directamente.

#### Acceptance Criteria

1. THE System SHALL create one Internet Gateway attached to the VPC
2. THE System SHALL create one NAT Gateway in the public subnet for private subnet internet access
3. THE System SHALL assign an Elastic IP to the NAT Gateway automatically
4. THE System SHALL configure route tables to direct internet traffic appropriately:
   - Public subnet routes 0.0.0.0/0 to Internet Gateway
   - Private subnets route 0.0.0.0/0 to NAT Gateway
5. THE System SHALL document the single point of failure for NAT Gateway and plan for future redundancy

### Requirement 4: VPC Endpoints for AWS Services

**User Story:** Como ingeniero de costos, quiero implementar VPC endpoints para servicios AWS críticos, para que el tráfico permanezca dentro de la red AWS y se reduzcan los costos de transferencia de datos.

#### Acceptance Criteria

1. THE System SHALL create a Gateway Endpoint for S3 service (com.amazonaws.us-east-1.s3)
2. THE System SHALL create Interface Endpoints for critical services:
   - AWS Glue (com.amazonaws.us-east-1.glue)
   - Secrets Manager (com.amazonaws.us-east-1.secretsmanager)
   - CloudWatch Logs (com.amazonaws.us-east-1.logs)
   - KMS (com.amazonaws.us-east-1.kms)
   - STS (com.amazonaws.us-east-1.sts)
   - EventBridge (com.amazonaws.us-east-1.events)
3. THE System SHALL configure Interface Endpoints with private DNS enabled
4. THE System SHALL associate VPC endpoints with appropriate route tables
5. THE System SHALL apply security groups to Interface Endpoints restricting access to authorized resources

### Requirement 5: Security Groups Configuration

**User Story:** Como especialista en seguridad, quiero definir Security Groups granulares para cada tipo de servicio, para que el tráfico de red esté controlado según el principio de menor privilegio.

#### Acceptance Criteria

1. THE System SHALL create SG-API-Gateway allowing:
   - Inbound HTTPS (443) from 0.0.0.0/0 for webhook reception
   - Outbound all traffic to 0.0.0.0/0
2. THE System SHALL create SG-Redshift-Existing allowing:
   - Inbound PostgreSQL (5439) from SG-Lambda, SG-MWAA, and existing Cencosud BI systems
   - Inbound PostgreSQL (5439) from current MySQL→Redshift connection (during migration)
   - Outbound HTTPS (443) to VPC Endpoints only
3. THE System SHALL create SG-Lambda allowing:
   - No inbound rules (Lambda doesn't receive direct connections)
   - Outbound PostgreSQL (5439) to SG-Redshift-Existing
   - Outbound HTTPS (443) to VPC Endpoints and 0.0.0.0/0
4. THE System SHALL create SG-MWAA allowing:
   - Inbound HTTPS (443) from SG-MWAA (self-reference for workers)
   - Inbound EventBridge triggers from VPC Endpoint EventBridge
   - Outbound HTTPS (443) to VPC Endpoints and 0.0.0.0/0
   - Outbound PostgreSQL (5439) to SG-Redshift-Existing
5. THE System SHALL create SG-Glue allowing:
   - Inbound all TCP from SG-Glue (self-reference for Spark communication)
   - Outbound HTTPS (443) to VPC Endpoints
   - Outbound all TCP to SG-Glue (self-reference)
6. THE System SHALL create SG-EventBridge allowing:
   - Outbound HTTPS (443) to MWAA endpoints for DAG triggering
   - Outbound HTTPS (443) to VPC Endpoints

### Requirement 6: Network Access Control Lists

**User Story:** Como auditor de seguridad, quiero implementar NACLs como capa adicional de seguridad, para que exista protección a nivel de subred complementando los Security Groups.

#### Acceptance Criteria

1. THE System SHALL create Public Subnet NACL with rules:
   - Inbound: HTTPS (443) from 0.0.0.0/0 ALLOW, Ephemeral ports (1024-65535) from 0.0.0.0/0 ALLOW
   - Outbound: All traffic to 0.0.0.0/0 ALLOW
   - Default: All other traffic DENY
2. THE System SHALL create Private Subnet NACL with rules:
   - Inbound: All traffic from 10.0.0.0/16 ALLOW, HTTPS (443) from 0.0.0.0/0 ALLOW, Ephemeral ports from 0.0.0.0/0 ALLOW
   - Outbound: All traffic to 10.0.0.0/16 ALLOW, HTTPS (443) to 0.0.0.0/0 ALLOW
   - Default: All other traffic DENY
3. THE System SHALL associate NACLs with their respective subnet groups
4. THE System SHALL ensure NACL rules are stateless and properly configured for bidirectional communication
5. THE System SHALL log NACL rule matches for security monitoring

### Requirement 7: Web Application Firewall

**User Story:** Como especialista en ciberseguridad, quiero implementar AWS WAF en API Gateway, para que los webhooks estén protegidos contra ataques comunes y patrones maliciosos.

#### Acceptance Criteria

1. THE System SHALL create WAF Web ACL with rate limiting rule:
   - Limit: 2,000 requests per IP in 5 minutes
   - Action: Block with 429 response code
2. THE System SHALL implement geo-blocking rule:
   - Allow: Traffic only from Peru (PE) and AWS regions
   - Action: Block traffic from other countries
3. THE System SHALL apply AWS Managed Rules:
   - AWSManagedRulesAmazonIpReputationList (block known bad IPs)
   - AWSManagedRulesCommonRuleSet (OWASP Top 10 protection)
   - AWSManagedRulesKnownBadInputsRuleSet (block malicious payloads)
4. THE System SHALL configure WAF logging to CloudWatch for all blocked requests
5. THE System SHALL associate WAF Web ACL with API Gateway for webhook endpoints

### Requirement 8: Resource Tagging Strategy

**User Story:** Como administrador de recursos, quiero implementar una estrategia de etiquetado consistente, para que todos los recursos sean fácilmente identificables y gestionables.

#### Acceptance Criteria

1. THE System SHALL apply mandatory tags to all resources:
   - Project: "janis-cencosud-integration"
   - Environment: "production" | "staging" | "development"
   - Component: specific component name
   - Owner: "cencosud-data-team"
   - CostCenter: assigned cost center code
2. THE System SHALL apply optional tags for better organization:
   - CreatedBy: automation tool or user
   - CreatedDate: resource creation timestamp
   - LastModified: last modification timestamp
3. THE System SHALL ensure tag consistency across all AWS services
4. THE System SHALL validate that critical tags are present before resource creation
5. THE System SHALL support tag-based cost allocation and reporting

### Requirement 9: EventBridge Configuration

**User Story:** Como ingeniero de orquestación, quiero configurar Amazon EventBridge para gatillar procesos de polling de manera eficiente, para que se reduzca el overhead de MWAA y se optimice el uso de recursos del sistema.

#### Acceptance Criteria

1. THE System SHALL create EventBridge custom event bus for polling operations
2. THE System SHALL create scheduled rules for each polling type:
   - Order polling rule: every 5 minutes (rate(5 minutes))
   - Product polling rule: every 1 hour (rate(60 minutes))
   - Stock polling rule: every 10 minutes (rate(10 minutes))
   - Price polling rule: every 30 minutes (rate(30 minutes))
   - Store polling rule: every 24 hours (rate(1440 minutes))
3. THE System SHALL configure each rule to target MWAA DAG execution with proper IAM permissions
4. THE System SHALL include event metadata in rule targets:
   - polling_type: type of data to poll
   - execution_time: scheduled execution timestamp
   - rule_name: EventBridge rule identifier
5. THE System SHALL enable CloudWatch monitoring for all EventBridge rules
6. THE System SHALL configure dead letter queues for failed rule executions
7. THE System SHALL implement rule state management (enable/disable) for maintenance windows

### Requirement 10: Network Monitoring and Logging

**User Story:** Como ingeniero de operaciones, quiero habilitar logging completo de la red, para que pueda monitorear el tráfico y detectar anomalías de seguridad.

#### Acceptance Criteria

1. THE System SHALL enable VPC Flow Logs for the entire VPC
2. THE System SHALL configure Flow Logs to capture:
   - All traffic (accepted and rejected)
   - Source and destination IPs, ports, and protocols
   - Packet and byte counts
   - Action taken (accept/reject)
3. THE System SHALL store Flow Logs in CloudWatch Logs with 90-day retention
4. THE System SHALL enable DNS query logging for security monitoring
5. THE System SHALL create CloudWatch alarms for suspicious network patterns

### Requirement 11: Integration with Existing Cencosud Infrastructure

**User Story:** Como arquitecto de integración, quiero asegurar que la nueva infraestructura se integre correctamente con los sistemas existentes de Cencosud, para que no haya interrupciones en los servicios actuales.

#### Acceptance Criteria

1. THE System SHALL identify and document existing Redshift cluster configuration and network settings
2. THE System SHALL ensure VPC connectivity with existing Redshift cluster without network conflicts
3. THE System SHALL maintain existing security group rules for current BI systems accessing Redshift
4. THE System SHALL coordinate with existing backup and monitoring systems
5. THE System SHALL respect existing maintenance windows and operational procedures
6. THE System SHALL ensure new infrastructure doesn't impact current Redshift performance
7. THE System SHALL provide migration path that allows rollback to current MySQL→Redshift connection

### Requirement 12: High Availability and Disaster Recovery

**User Story:** Como arquitecto de soluciones, quiero documentar las limitaciones de disponibilidad de la infraestructura single-AZ actual y planificar la futura expansión multi-AZ, para que el sistema pueda evolucionar hacia alta disponibilidad sin requerir rediseño completo.

#### Acceptance Criteria

1. THE System SHALL document that the initial deployment uses a single AZ (us-east-1a)
2. THE System SHALL document the single points of failure in the single-AZ architecture (NAT Gateway, subnet availability)
3. THE System SHALL design the infrastructure to support future multi-AZ expansion without major architectural changes
4. THE System SHALL reserve CIDR blocks and naming conventions for future AZ resources
5. THE System SHALL document the migration path from single-AZ to multi-AZ deployment
6. THE System SHALL implement backup and recovery procedures appropriate for single-AZ deployment