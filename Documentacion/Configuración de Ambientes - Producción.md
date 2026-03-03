# Configuración de Ambiente de Producción
## Plataforma de Integración Janis-Cencosud

**Fecha**: 2 de Febrero, 2026  
**Versión**: 1.0  
**Estado**: Configuración actualizada con soporte Multi-AZ

---

## Resumen Ejecutivo

Este documento describe la configuración específica del ambiente de producción para la plataforma de integración Janis-Cencosud. La configuración ha sido actualizada para incluir soporte explícito de Multi-AZ, permitiendo alta disponibilidad cuando se despliegue en AWS.

---

## Cambios Recientes

### 2 de Febrero, 2026 - Actualización Multi-AZ

**Archivo modificado**: `terraform/environments/prod/main.tf`

**Cambios aplicados**:
1. Configuración explícita de `enable_multi_az = true`
2. Definición de CIDRs para todas las subnets (AZ A y AZ B)
3. Actualización de parámetros del módulo VPC

**Antes**:
```hcl
module "vpc" {
  source = "../../modules/vpc"

  vpc_cidr    = var.vpc_cidr
  name_prefix = local.name_prefix
  common_tags = local.common_tags
}
```

**Después**:
```hcl
module "vpc" {
  source = "../../modules/vpc"

  vpc_cidr                 = var.vpc_cidr
  aws_region               = var.aws_region
  name_prefix              = local.name_prefix
  tags                     = local.common_tags
  enable_multi_az          = true
  public_subnet_a_cidr     = "10.0.1.0/24"
  public_subnet_b_cidr     = "10.0.2.0/24"
  private_subnet_1a_cidr   = "10.0.11.0/24"
  private_subnet_1b_cidr   = "10.0.12.0/24"
  private_subnet_2a_cidr   = "10.0.21.0/24"
  private_subnet_2b_cidr   = "10.0.22.0/24"
}
```

---

## Configuración de Red

### VPC Configuration

```yaml
VPC:
  CIDR_Block: "10.0.0.0/16"
  Region: "us-east-1"
  DNS_Resolution: Enabled
  DNS_Hostnames: Enabled
  Multi_AZ: Enabled
```

### Subnet Architecture - Availability Zone A (us-east-1a)

#### Public Subnet A
```yaml
Public_Subnet_A:
  CIDR: "10.0.1.0/24"
  Availability_Zone: "us-east-1a"
  Total_IPs: 256
  Auto_Assign_Public_IP: true
  Purpose: "NAT Gateway, Load Balancers"
```

#### Private Subnet 1A
```yaml
Private_Subnet_1A:
  CIDR: "10.0.11.0/24"
  Availability_Zone: "us-east-1a"
  Total_IPs: 256
  Auto_Assign_Public_IP: false
  Purpose: "Lambda, MWAA, Redshift, Application Services"
```

#### Private Subnet 2A
```yaml
Private_Subnet_2A:
  CIDR: "10.0.21.0/24"
  Availability_Zone: "us-east-1a"
  Total_IPs: 256
  Auto_Assign_Public_IP: false
  Purpose: "AWS Glue ENIs, ETL Processing"
```

### Subnet Architecture - Availability Zone B (us-east-1b)

#### Public Subnet B
```yaml
Public_Subnet_B:
  CIDR: "10.0.2.0/24"
  Availability_Zone: "us-east-1b"
  Total_IPs: 256
  Auto_Assign_Public_IP: true
  Purpose: "NAT Gateway (HA), Load Balancers (HA)"
  Status: "Configurado para deployment"
```

#### Private Subnet 1B
```yaml
Private_Subnet_1B:
  CIDR: "10.0.12.0/24"
  Availability_Zone: "us-east-1b"
  Total_IPs: 256
  Auto_Assign_Public_IP: false
  Purpose: "Lambda (HA), MWAA (HA), Redshift (HA), Application Services"
  Status: "Configurado para deployment"
```

#### Private Subnet 2B
```yaml
Private_Subnet_2B:
  CIDR: "10.0.22.0/24"
  Availability_Zone: "us-east-1b"
  Total_IPs: 256
  Auto_Assign_Public_IP: false
  Purpose: "AWS Glue ENIs (HA), ETL Processing"
  Status: "Configurado para deployment"
```

---

## Beneficios de la Configuración Multi-AZ

### Alta Disponibilidad
- **Redundancia automática**: Servicios distribuidos en dos zonas de disponibilidad
- **Tolerancia a fallos**: Fallo de una AZ no afecta la operación
- **SLA mejorado**: AWS garantiza 99.99% uptime para servicios Multi-AZ

### Resiliencia
- **NAT Gateway redundante**: Segundo NAT Gateway en us-east-1b
- **Load Balancer distribuido**: Tráfico balanceado entre AZs
- **Redshift Multi-AZ**: Cluster con nodos en ambas AZs (si se configura)

### Continuidad del Negocio
- **Disaster Recovery**: Recuperación automática ante fallo de AZ
- **Mantenimiento sin downtime**: Actualizaciones rolling entre AZs
- **Backup automático**: Snapshots distribuidos geográficamente

---

## Arquitectura de Red Multi-AZ

```
Internet
    |
    v
[Internet Gateway]
    |
    +------------------+------------------+
    |                                     |
    v                                     v
[Public Subnet A]                 [Public Subnet B]
10.0.1.0/24 (us-east-1a)         10.0.2.0/24 (us-east-1b)
    |                                     |
    +-- NAT Gateway A                     +-- NAT Gateway B
    |                                     |
    v                                     v
[Private Subnet 1A]               [Private Subnet 1B]
10.0.11.0/24 (us-east-1a)        10.0.12.0/24 (us-east-1b)
    |                                     |
    +-- Lambda Functions                  +-- Lambda Functions (HA)
    +-- MWAA                              +-- MWAA (HA)
    +-- Redshift Node 1                   +-- Redshift Node 2
    |                                     |
    v                                     v
[Private Subnet 2A]               [Private Subnet 2B]
10.0.21.0/24 (us-east-1a)        10.0.22.0/24 (us-east-1b)
    |                                     |
    +-- AWS Glue ENIs                     +-- AWS Glue ENIs (HA)
```

---

## Consideraciones de Costos

### Costos Adicionales de Multi-AZ

**NAT Gateway Adicional**:
- Costo base: $32.40/mes
- Data transfer: $0.045/GB
- Total estimado: ~$50-80/mes (dependiendo del tráfico)

**Elastic IP Adicional**:
- Costo: $0/mes (mientras esté asociado al NAT Gateway)

**Cross-AZ Data Transfer**:
- Costo: $0.01/GB entre AZs
- Impacto: Bajo para esta arquitectura (mayoría del tráfico es intra-AZ)

**Redshift Multi-AZ** (si se configura):
- Costo: Mismo que single-AZ (nodos distribuidos, no duplicados)

**Total Incremental Estimado**: $50-100/mes

### Justificación de Costos

- **Disponibilidad**: 99.99% vs 99.9% (10x menos downtime)
- **Costo de downtime**: Típicamente $1,000-10,000/hora para sistemas críticos
- **ROI**: Costo adicional se recupera con 1-2 horas menos de downtime al año

---

## Deployment Strategy

### Fase 1: Single-AZ (Actual)
- Desplegar solo subnets en us-east-1a
- Un NAT Gateway en Public Subnet A
- Validar funcionalidad completa
- Costo optimizado para testing/staging

### Fase 2: Multi-AZ (Producción)
- Desplegar subnets en us-east-1b
- Segundo NAT Gateway en Public Subnet B
- Configurar servicios para alta disponibilidad
- Activar Auto Scaling cross-AZ

### Migración de Single-AZ a Multi-AZ

**Pasos recomendados**:
1. Crear subnets en us-east-1b (sin downtime)
2. Desplegar segundo NAT Gateway (sin downtime)
3. Actualizar route tables (sin downtime)
4. Configurar servicios para Multi-AZ:
   - Lambda: Actualizar VPC config para incluir subnets de ambas AZs
   - MWAA: Actualizar network configuration
   - Redshift: Migrar a cluster Multi-AZ (requiere mantenimiento)
5. Validar failover entre AZs
6. Actualizar monitoreo y alertas

**Downtime estimado**: 0-2 horas (solo para Redshift si se migra)

---

## Variables de Configuración

### Archivo: `terraform/environments/prod/prod.tfvars`

```hcl
# Environment Configuration
environment = "prod"
aws_region  = "us-east-1"

# Project Identification
project_name = "janis-cencosud-integration"
owner        = "cencosud-data-team"
cost_center  = "data-integration"

# Network Configuration
vpc_cidr = "10.0.0.0/16"

# Availability Zones
availability_zones = ["us-east-1a", "us-east-1b"]

# Additional Tags
additional_tags = {
  Criticality = "high"
  Compliance  = "required"
  Backup      = "daily"
}
```

---

## Outputs Disponibles

El módulo VPC en producción expone los siguientes outputs:

```hcl
output "vpc_id" {
  description = "ID of the VPC"
  value       = module.vpc.vpc_id
}

output "vpc_cidr_block" {
  description = "CIDR block of the VPC"
  value       = module.vpc.vpc_cidr_block
}

output "vpc_arn" {
  description = "ARN of the VPC"
  value       = module.vpc.vpc_arn
}
```

**Nota**: Outputs adicionales (subnet IDs, route table IDs, etc.) están disponibles en el módulo VPC y pueden ser expuestos según necesidad.

---

## Validación y Testing

### Pre-Deployment Checklist

- [ ] Verificar que CIDRs no conflictúen con redes corporativas
- [ ] Confirmar que `enable_multi_az = true` en prod/main.tf
- [ ] Validar que todos los CIDRs de subnets están definidos
- [ ] Revisar tags corporativos aplicados
- [ ] Confirmar presupuesto para costos adicionales de Multi-AZ

### Post-Deployment Validation

```bash
# Validar VPC creada
aws ec2 describe-vpcs --filters "Name=tag:Environment,Values=prod"

# Validar subnets en ambas AZs
aws ec2 describe-subnets --filters "Name=tag:Environment,Values=prod"

# Validar NAT Gateways
aws ec2 describe-nat-gateways --filter "Name=tag:Environment,Values=prod"

# Validar route tables
aws ec2 describe-route-tables --filters "Name=tag:Environment,Values=prod"
```

### Failover Testing

```bash
# Simular fallo de AZ deshabilitando NAT Gateway A
# Verificar que tráfico se redirige a NAT Gateway B
# Validar que servicios continúan operando

# Restaurar NAT Gateway A
# Verificar balanceo de tráfico entre AZs
```

---

## Seguridad

### Network Isolation
- Subnets privadas sin acceso directo a internet
- Todo tráfico saliente pasa por NAT Gateways
- VPC Flow Logs habilitados para auditoría

### Security Groups
- Configuración restrictiva por defecto
- Principio de menor privilegio aplicado
- Referencias entre security groups (no IPs hardcoded)

### Encryption
- Datos en tránsito: TLS 1.2+
- Datos en reposo: KMS encryption
- Secrets: AWS Secrets Manager

---

## Monitoreo y Alertas

### CloudWatch Metrics

**VPC Metrics**:
- NAT Gateway bytes in/out
- NAT Gateway packets dropped
- VPC Flow Logs analysis

**Multi-AZ Specific**:
- Cross-AZ data transfer
- AZ-specific error rates
- Failover events

### Alarmas Recomendadas

```yaml
NAT_Gateway_Errors:
  Metric: ErrorPortAllocation
  Threshold: "> 0"
  Period: 5 minutes
  Action: SNS notification

Cross_AZ_Data_Transfer_Spike:
  Metric: BytesOutToDestination
  Threshold: "> 100 GB/hour"
  Period: 1 hour
  Action: SNS notification + Cost alert

AZ_Availability:
  Metric: Custom (health checks)
  Threshold: "< 1 AZ healthy"
  Period: 1 minute
  Action: PagerDuty alert
```

---

## Troubleshooting

### Conectividad Issues

**Síntoma**: Servicios en una AZ no pueden comunicarse con otra AZ

**Diagnóstico**:
```bash
# Verificar route tables
aws ec2 describe-route-tables --filters "Name=tag:Environment,Values=prod"

# Verificar security groups
aws ec2 describe-security-groups --filters "Name=tag:Environment,Values=prod"

# Revisar VPC Flow Logs
aws logs filter-log-events --log-group-name "/aws/vpc/flow-logs/prod"
```

**Solución**: Verificar que security groups permiten tráfico entre subnets de diferentes AZs

### NAT Gateway Failures

**Síntoma**: Servicios pierden conectividad a internet

**Diagnóstico**:
```bash
# Verificar estado de NAT Gateways
aws ec2 describe-nat-gateways --filter "Name=state,Values=failed"

# Revisar CloudWatch metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/NATGateway \
  --metric-name ErrorPortAllocation
```

**Solución**: Verificar que hay NAT Gateway funcional en cada AZ, revisar route tables

---

## Referencias

- [AWS Multi-AZ Best Practices](https://docs.aws.amazon.com/whitepapers/latest/real-time-communication-on-aws/high-availability-and-scalability-on-aws.html)
- [VPC Subnet Sizing](https://docs.aws.amazon.com/vpc/latest/userguide/subnet-sizing.html)
- [NAT Gateway High Availability](https://docs.aws.amazon.com/vpc/latest/userguide/vpc-nat-gateway.html#nat-gateway-basics)
- [Terraform AWS VPC Module](https://registry.terraform.io/modules/terraform-aws-modules/vpc/aws/latest)

---

## Historial de Cambios

| Fecha | Versión | Cambios | Autor |
|-------|---------|---------|-------|
| 2026-02-02 | 1.0 | Documento inicial con configuración Multi-AZ | Kiro AI |
