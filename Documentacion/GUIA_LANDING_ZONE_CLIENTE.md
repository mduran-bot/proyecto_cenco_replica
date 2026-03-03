# Guía: Uso de Landing Zone Existente del Cliente

## Resumen

Este documento explica cómo adaptar el código Terraform para que el cliente pueda usar su propia Landing Zone (VPC, subnets, NAT Gateway, etc.) en lugar de crear una nueva.

---

## PASO 1: Comentar el Módulo VPC en main.tf

### Archivo: `terraform/main.tf`

**COMENTAR COMPLETAMENTE** el módulo VPC (líneas 27-52):

```terraform
# ============================================================================
# VPC Module - COMENTADO: El cliente usará su Landing Zone existente
# ============================================================================
/*
module "vpc" {
  source = "./modules/vpc"

  # Network Configuration
  vpc_cidr               = var.vpc_cidr
  public_subnet_a_cidr   = var.public_subnet_a_cidr
  private_subnet_1a_cidr = var.private_subnet_1a_cidr
  private_subnet_2a_cidr = var.private_subnet_2a_cidr

  # Multi-AZ Configuration
  enable_multi_az        = var.enable_multi_az
  public_subnet_b_cidr   = var.public_subnet_b_cidr
  private_subnet_1b_cidr = var.private_subnet_1b_cidr
  private_subnet_2b_cidr = var.private_subnet_2b_cidr

  # General Configuration
  aws_region  = var.aws_region
  name_prefix = local.name_prefix

  # Corporate Tags
  tags = local.all_tags
}
*/
```

---

## PASO 2: Agregar Variables para Recursos Existentes

### Archivo: `terraform/variables.tf`

**AGREGAR** estas nuevas variables después de la sección "Network Configuration" (después de la línea 70):

```terraform
# ============================================================================
# Existing Landing Zone Configuration (Cliente proporciona estos valores)
# ============================================================================

variable "existing_vpc_id" {
  description = "ID de la VPC existente del cliente"
  type        = string
  # Ejemplo: "vpc-0123456789abcdef0"
}

variable "existing_vpc_cidr" {
  description = "CIDR block de la VPC existente del cliente"
  type        = string
  # Ejemplo: "10.0.0.0/16"
}

variable "existing_public_subnet_ids" {
  description = "IDs de las subnets públicas existentes (para NAT Gateway, API Gateway)"
  type        = list(string)
  # Ejemplo: ["subnet-abc123", "subnet-def456"]
}

variable "existing_private_subnet_1_ids" {
  description = "IDs de las subnets privadas para servicios principales (Lambda, MWAA, Redshift)"
  type        = list(string)
  # Ejemplo: ["subnet-ghi789", "subnet-jkl012"]
}

variable "existing_private_subnet_2_ids" {
  description = "IDs de las subnets privadas para AWS Glue ENIs"
  type        = list(string)
  # Ejemplo: ["subnet-mno345", "subnet-pqr678"]
}

variable "existing_route_table_ids" {
  description = "IDs de las route tables para VPC Endpoints (Gateway)"
  type        = list(string)
  # Ejemplo: ["rtb-xyz789", "rtb-uvw012"]
}

variable "existing_nat_gateway_id" {
  description = "ID del NAT Gateway existente (para alarmas de CloudWatch)"
  type        = string
  default     = ""
  # Ejemplo: "nat-0a1b2c3d4e5f"
}

variable "existing_internet_gateway_id" {
  description = "ID del Internet Gateway existente (informativo)"
  type        = string
  default     = ""
  # Ejemplo: "igw-0123456789abcdef0"
}
```

**COMENTAR O ELIMINAR** las variables de creación de red (líneas 20-73):

```terraform
# ============================================================================
# Network Configuration - COMENTADO: No se creará VPC nueva
# ============================================================================
/*
variable "vpc_cidr" {
  description = "CIDR block for VPC (must provide 65,536 IPs)"
  type        = string
  default     = "10.0.0.0/16"

  validation {
    condition     = can(cidrhost(var.vpc_cidr, 0)) && tonumber(split("/", var.vpc_cidr)[1]) == 16
    error_message = "VPC CIDR must be a valid /16 IPv4 CIDR block."
  }
}

variable "public_subnet_a_cidr" {
  description = "CIDR block for public subnet in AZ A"
  type        = string
  default     = "10.0.1.0/24"
}

variable "private_subnet_1a_cidr" {
  description = "CIDR block for private subnet 1A (Lambda, MWAA, Redshift)"
  type        = string
  default     = "10.0.10.0/24"
}

variable "private_subnet_2a_cidr" {
  description = "CIDR block for private subnet 2A (Glue ENIs)"
  type        = string
  default     = "10.0.20.0/24"
}

variable "enable_multi_az" {
  description = "Enable Multi-AZ deployment (creates resources in us-east-1b)"
  type        = bool
  default     = false
}

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
*/
```

---

## PASO 3: Actualizar Referencias en main.tf

### Archivo: `terraform/main.tf`

**REEMPLAZAR** todas las referencias a `module.vpc.*` con las nuevas variables:

### 3.1 Módulo Security Groups (líneas 57-77):

```terraform
module "security_groups" {
  source = "./modules/security-groups"

  # CAMBIO: Usar VPC existente del cliente
  vpc_id      = var.existing_vpc_id
  vpc_cidr    = var.existing_vpc_cidr
  name_prefix = local.name_prefix

  # Existing Infrastructure
  existing_redshift_sg_id       = var.existing_redshift_sg_id
  existing_bi_security_groups   = var.existing_bi_security_groups
  existing_bi_ip_ranges         = var.existing_bi_ip_ranges
  existing_mysql_pipeline_sg_id = var.existing_mysql_pipeline_sg_id

  # Janis IPs
  allowed_janis_ip_ranges = var.allowed_janis_ip_ranges

  # Corporate Tags
  tags = local.all_tags
}
```

### 3.2 Módulo VPC Endpoints (líneas 78-106):

```terraform
module "vpc_endpoints" {
  source = "./modules/vpc-endpoints"

  # CAMBIO: Usar recursos existentes del cliente
  vpc_id             = var.existing_vpc_id
  private_subnet_ids = var.existing_private_subnet_1_ids
  route_table_ids    = var.existing_route_table_ids
  name_prefix        = local.name_prefix

  # Security Group for Interface Endpoints
  vpc_endpoints_security_group_id = module.security_groups.sg_vpc_endpoints_id

  # Enable/Disable specific endpoints
  enable_s3_endpoint              = var.enable_s3_endpoint
  enable_glue_endpoint            = var.enable_glue_endpoint
  enable_secrets_manager_endpoint = var.enable_secrets_manager_endpoint
  enable_logs_endpoint            = var.enable_logs_endpoint
  enable_kms_endpoint             = var.enable_kms_endpoint
  enable_sts_endpoint             = var.enable_sts_endpoint
  enable_events_endpoint          = var.enable_events_endpoint

  # Corporate Tags
  tags = local.all_tags
}
```

### 3.3 Módulo Monitoring (líneas 166-189):

```terraform
module "monitoring" {
  source = "./modules/monitoring"

  # CAMBIO: Usar recursos existentes del cliente
  vpc_id         = var.existing_vpc_id
  nat_gateway_id = var.existing_nat_gateway_id
  name_prefix    = local.name_prefix

  # Configuration
  vpc_flow_logs_retention_days = var.vpc_flow_logs_retention_days
  dns_logs_retention_days      = var.dns_logs_retention_days
  alarm_sns_topic_arn          = var.alarm_sns_topic_arn

  # Enable/Disable
  enable_vpc_flow_logs     = var.enable_vpc_flow_logs
  enable_dns_query_logging = var.enable_dns_query_logging

  # EventBridge rule names for alarms
  eventbridge_rule_names = module.eventbridge.rule_names

  # Corporate Tags
  tags = local.all_tags
}
```

---

## PASO 4: Actualizar Outputs

### Archivo: `terraform/outputs.tf`

**COMENTAR** todos los outputs relacionados con VPC (líneas 7-43):

```terraform
# ============================================================================
# VPC Outputs - COMENTADO: VPC es del cliente
# ============================================================================
/*
output "vpc_id" {
  description = "ID of the VPC"
  value       = module.vpc.vpc_id
}

output "vpc_cidr" {
  description = "CIDR block of the VPC"
  value       = module.vpc.vpc_cidr
}

output "public_subnet_ids" {
  description = "IDs of public subnets"
  value       = module.vpc.public_subnet_ids
}

output "private_subnet_ids" {
  description = "IDs of private subnets"
  value       = module.vpc.private_subnet_ids
}

output "nat_gateway_id" {
  description = "ID of the NAT Gateway"
  value       = module.vpc.nat_gateway_id
}

output "nat_gateway_public_ip" {
  description = "Public IP of the NAT Gateway"
  value       = module.vpc.nat_gateway_public_ip
}

output "internet_gateway_id" {
  description = "ID of the Internet Gateway"
  value       = module.vpc.internet_gateway_id
}
*/
```

**AGREGAR** outputs informativos con los valores del cliente:

```terraform
# ============================================================================
# Landing Zone Outputs (Recursos existentes del cliente)
# ============================================================================

output "client_vpc_id" {
  description = "ID de la VPC existente del cliente (informativo)"
  value       = var.existing_vpc_id
}

output "client_vpc_cidr" {
  description = "CIDR de la VPC existente del cliente (informativo)"
  value       = var.existing_vpc_cidr
}

output "client_subnet_ids" {
  description = "IDs de subnets existentes del cliente (informativo)"
  value = {
    public_subnets    = var.existing_public_subnet_ids
    private_subnets_1 = var.existing_private_subnet_1_ids
    private_subnets_2 = var.existing_private_subnet_2_ids
  }
}
```

**ACTUALIZAR** el output de resumen (líneas 120-135):

```terraform
output "deployment_summary" {
  description = "Summary of deployed infrastructure"
  value = {
    # CAMBIO: Usar valores del cliente
    vpc_id             = var.existing_vpc_id
    vpc_cidr           = var.existing_vpc_cidr
    # availability_zones se puede omitir o calcular de las subnets
    nat_gateway_id     = var.existing_nat_gateway_id
    # Note: WAF is managed by the client
    event_bus_name     = module.eventbridge.event_bus_name
    monitoring_enabled = var.enable_vpc_flow_logs || var.enable_dns_query_logging
  }
}
```

---

## PASO 5: Configurar terraform.tfvars

### Archivo: `terraform/terraform.tfvars`

**COMENTAR** las variables de creación de red (lineas 18-29):

```terraform
# ============================================================================
# Network Configuration - COMENTADO: Cliente usa Landing Zone existente
# ============================================================================
/*
vpc_cidr                = "10.0.0.0/16"
public_subnet_a_cidr    = "10.0.1.0/24"
private_subnet_1a_cidr  = "10.0.10.0/24"
private_subnet_2a_cidr  = "10.0.20.0/24"
enable_multi_az         = false
*/
```

**AGREGAR** las nuevas variables con valores que el cliente debe proporcionar:

```terraform
# ============================================================================
# Existing Landing Zone Configuration
# CLIENTE: Proporcionar IDs de recursos existentes
# ============================================================================

# VPC existente del cliente
existing_vpc_id   = "vpc-XXXXXXXXXXXXXXXXX"  # CLIENTE: Cambiar por VPC ID real
existing_vpc_cidr = "10.0.0.0/16"            # CLIENTE: Cambiar por CIDR real

# Subnets públicas (para NAT Gateway, API Gateway)
existing_public_subnet_ids = [
  "subnet-XXXXXXXXXXXXXXXXX",  # CLIENTE: Subnet pública AZ A
  # "subnet-XXXXXXXXXXXXXXXXX"  # CLIENTE: Subnet pública AZ B (opcional Multi-AZ)
]

# Subnets privadas 1 (para Lambda, MWAA, Redshift)
existing_private_subnet_1_ids = [
  "subnet-XXXXXXXXXXXXXXXXX",  # CLIENTE: Subnet privada 1 AZ A
  # "subnet-XXXXXXXXXXXXXXXXX"  # CLIENTE: Subnet privada 1 AZ B (opcional Multi-AZ)
]

# Subnets privadas 2 (para AWS Glue ENIs)
existing_private_subnet_2_ids = [
  "subnet-XXXXXXXXXXXXXXXXX",  # CLIENTE: Subnet privada 2 AZ A
  # "subnet-XXXXXXXXXXXXXXXXX"  # CLIENTE: Subnet privada 2 AZ B (opcional Multi-AZ)
]

# Route Tables (para VPC Endpoints Gateway)
existing_route_table_ids = [
  "rtb-XXXXXXXXXXXXXXXXX",  # CLIENTE: Route table privada AZ A
  # "rtb-XXXXXXXXXXXXXXXXX"  # CLIENTE: Route table privada AZ B (opcional Multi-AZ)
]

# NAT Gateway (para alarmas de CloudWatch)
existing_nat_gateway_id = "nat-XXXXXXXXXXXXXXXXX"  # CLIENTE: NAT Gateway ID

# Internet Gateway (informativo)
existing_internet_gateway_id = "igw-XXXXXXXXXXXXXXXXX"  # CLIENTE: IGW ID (opcional)
```

---

## PASO 6: Comandos para Obtener IDs de Recursos

El cliente puede usar estos comandos AWS CLI para obtener los IDs necesarios:

### VPC ID y CIDR:
```bash
aws ec2 describe-vpcs --query 'Vpcs[*].[VpcId,CidrBlock,Tags[?Key==`Name`].Value|[0]]' --output table
```

### Subnet IDs:
```bash
# Todas las subnets
aws ec2 describe-subnets --query 'Subnets[*].[SubnetId,CidrBlock,AvailabilityZone,Tags[?Key==`Name`].Value|[0]]' --output table

# Filtrar por VPC específica
aws ec2 describe-subnets --filters "Name=vpc-id,Values=vpc-XXXXXXXXX" --query 'Subnets[*].[SubnetId,CidrBlock,AvailabilityZone,Tags[?Key==`Name`].Value|[0]]' --output table
```

### Route Table IDs:
```bash
aws ec2 describe-route-tables --filters "Name=vpc-id,Values=vpc-XXXXXXXXX" --query 'RouteTables[*].[RouteTableId,Tags[?Key==`Name`].Value|[0]]' --output table
```

### NAT Gateway ID:
```bash
aws ec2 describe-nat-gateways --filter "Name=vpc-id,Values=vpc-XXXXXXXXX" --query 'NatGateways[*].[NatGatewayId,SubnetId,State]' --output table
```

### Internet Gateway ID:
```bash
aws ec2 describe-internet-gateways --filters "Name=attachment.vpc-id,Values=vpc-XXXXXXXXX" --query 'InternetGateways[*].[InternetGatewayId]' --output table
```

---

## PASO 7: Requisitos de la Landing Zone del Cliente

La Landing Zone del cliente DEBE cumplir con estos requisitos:

### Estructura de Subnets:
1. **Al menos 1 subnet pública** (con ruta a Internet Gateway)
   - Para NAT Gateway
   - Para API Gateway endpoints (si aplica)

2. **Al menos 1 subnet privada tipo 1** (con ruta a NAT Gateway)
   - Para Lambda Functions
   - Para MWAA (Managed Airflow)
   - Para Redshift Cluster

3. **Al menos 1 subnet privada tipo 2** (con ruta a NAT Gateway)
   - Dedicada para AWS Glue ENIs
   - Necesaria para comunicación del cluster Spark

### Componentes de Red:
- ✅ **Internet Gateway** funcional y asociado a la VPC
- ✅ **NAT Gateway** en subnet pública con Elastic IP
- ✅ **Route Tables** configuradas correctamente:
  - Subnet pública → Internet Gateway (0.0.0.0/0)
  - Subnets privadas → NAT Gateway (0.0.0.0/0)
- ✅ **DNS Resolution** habilitado en la VPC
- ✅ **DNS Hostnames** habilitado en la VPC

### Rangos CIDR:
- No deben solapar con otras VPCs o redes corporativas
- Suficiente espacio para los servicios:
  - Lambda: ~50 IPs
  - MWAA: ~20 IPs
  - Redshift: ~10 IPs
  - Glue: ~100 IPs (para cluster Spark)

### Multi-AZ (Opcional pero Recomendado para Producción):
- Subnets en al menos 2 Availability Zones
- NAT Gateway en cada AZ para alta disponibilidad
- Route tables separadas por AZ

---

## PASO 8: Validación Pre-Deployment

Antes de ejecutar `terraform apply`, el cliente debe validar:

### 1. Verificar conectividad de subnets:
```bash
# Verificar que subnets privadas tienen ruta a NAT Gateway
aws ec2 describe-route-tables --route-table-ids rtb-XXXXXXXXX --query 'RouteTables[*].Routes'
```

### 2. Verificar DNS en VPC:
```bash
aws ec2 describe-vpc-attribute --vpc-id vpc-XXXXXXXXX --attribute enableDnsSupport
aws ec2 describe-vpc-attribute --vpc-id vpc-XXXXXXXXX --attribute enableDnsHostnames
```

### 3. Verificar NAT Gateway funcional:
```bash
aws ec2 describe-nat-gateways --nat-gateway-ids nat-XXXXXXXXX --query 'NatGateways[*].[State,ConnectivityType]'
```

### 4. Probar conectividad desde subnet privada:
- Lanzar una instancia EC2 temporal en subnet privada
- Verificar que puede acceder a internet a través del NAT Gateway
- Verificar resolución DNS

---

## PASO 9: Deployment

Una vez configurado todo:

```bash
# 1. Inicializar Terraform
terraform init

# 2. Validar configuración
terraform validate

# 3. Revisar plan
terraform plan -var-file="terraform.tfvars"

# 4. Aplicar (con aprobación manual)
terraform apply -var-file="terraform.tfvars"
```

---

## Recursos Creados vs Existentes

### ✅ Recursos que SE CREARÁN (por Terraform):
- Security Groups (7 grupos)
- VPC Endpoints (Gateway + Interface)
- EventBridge Rules y Event Bus
- CloudWatch Log Groups, Alarms y Metric Filters
- IAM Roles para Flow Logs y DNS Logs
- SQS Dead Letter Queue

### ❌ Recursos que NO se crearán (usa Landing Zone del cliente):
- VPC
- Subnets (públicas y privadas)
- Internet Gateway
- NAT Gateway(s)
- Elastic IPs
- Route Tables
- Route Table Associations

---

## Troubleshooting

### Error: "vpc_id not found"
- Verificar que `existing_vpc_id` en terraform.tfvars es correcto
- Verificar permisos AWS para describir VPCs

### Error: "subnet not found"
- Verificar que todos los subnet IDs existen y están en la VPC correcta
- Usar comando: `aws ec2 describe-subnets --subnet-ids subnet-XXXXX`

### Error: "route table not found"
- Verificar que route table IDs son correctos
- Verificar que están asociados a la VPC correcta

### Error: VPC Flow Logs no se crean
- Verificar que la VPC no tiene Flow Logs existentes
- Verificar permisos IAM para crear Flow Logs

---

## Contacto y Soporte

Para dudas o problemas durante la configuración, contactar al equipo de infraestructura.
