# Configuración Landing Zone Existente - Resumen

**Fecha**: 3 de Febrero, 2026  
**Documento relacionado**: [../GUIA_LANDING_ZONE_CLIENTE.md](../GUIA_LANDING_ZONE_CLIENTE.md)

---

## Resumen Ejecutivo

Se ha creado una **guía completa para usar Landing Zone existente del cliente** en lugar de crear una VPC nueva. Esta opción permite integrar la infraestructura Terraform con la red corporativa existente del cliente.

## Propósito

La guía de Landing Zone permite:
- ✅ Reutilizar infraestructura VPC corporativa existente
- ✅ Cumplir con políticas de red establecidas
- ✅ Reducir tiempo de deployment (no crear VPC nueva)
- ✅ Integrar con arquitectura de red existente
- ✅ Mantener consistencia con otros proyectos

## Opciones de Deployment

### Opción 1: VPC Nueva (Por Defecto)
- **Propósito**: Despliegue completo desde cero
- **Incluye**: VPC, subnets, NAT Gateway, Internet Gateway, Route Tables
- **Ventaja**: Control total de la infraestructura de red
- **Uso**: Ambientes de desarrollo, QA, o cuando no existe Landing Zone
- **Estado**: Implementado y probado ✅

### Opción 2: Landing Zone Existente (Nueva)
- **Propósito**: Integración con infraestructura VPC corporativa existente
- **Requiere**: VPC, subnets públicas/privadas, NAT Gateway ya desplegados
- **Ventaja**: Reutiliza infraestructura de red corporativa
- **Uso**: Producción en organizaciones con Landing Zone establecida
- **Estado**: Documentado en [GUIA_LANDING_ZONE_CLIENTE.md](../GUIA_LANDING_ZONE_CLIENTE.md) ⭐ NUEVO

## Contenido de la Guía

La guía completa incluye 9 pasos detallados:

### PASO 1: Comentar el Módulo VPC
- Deshabilitar creación de VPC en `terraform/main.tf`
- Comentar el módulo VPC completo

### PASO 2: Agregar Variables para Recursos Existentes
- Definir variables `existing_*` en `terraform/variables.tf`
- Variables para: VPC ID, CIDR, subnet IDs, route table IDs, NAT Gateway ID

### PASO 3: Actualizar Referencias en main.tf
- Reemplazar `module.vpc.*` con `var.existing_*`
- Actualizar módulos: Security Groups, VPC Endpoints, Monitoring

### PASO 4: Actualizar Outputs
- Comentar outputs de VPC creada
- Agregar outputs informativos con valores del cliente

### PASO 5: Configurar terraform.tfvars
- Comentar variables de creación de red
- Agregar valores de recursos existentes del cliente

### PASO 6: Comandos para Obtener IDs de Recursos
- AWS CLI commands para obtener VPC ID, subnet IDs, route table IDs
- Comandos para NAT Gateway ID, Internet Gateway ID

### PASO 7: Requisitos de la Landing Zone
- Estructura de subnets requerida
- Componentes de red necesarios
- Rangos CIDR y consideraciones Multi-AZ

### PASO 8: Validación Pre-Deployment
- Verificar conectividad de subnets
- Validar DNS en VPC
- Probar NAT Gateway funcional

### PASO 9: Deployment
- Comandos de Terraform para deployment
- Validación y aplicación

## Recursos Creados vs Existentes

### ✅ Recursos que SE CREARÁN (por Terraform)
- Security Groups (7 grupos)
- VPC Endpoints (Gateway + Interface)
- EventBridge Rules y Event Bus
- CloudWatch Log Groups, Alarms y Metric Filters
- IAM Roles para Flow Logs y DNS Logs
- SQS Dead Letter Queue

### ❌ Recursos que NO se crearán (usa Landing Zone del cliente)
- VPC
- Subnets (públicas y privadas)
- Internet Gateway
- NAT Gateway(s)
- Elastic IPs
- Route Tables
- Route Table Associations

## Requisitos de la Landing Zone del Cliente

### Estructura de Subnets Requerida

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

### Componentes de Red Necesarios

- ✅ **Internet Gateway** funcional y asociado a la VPC
- ✅ **NAT Gateway** en subnet pública con Elastic IP
- ✅ **Route Tables** configuradas correctamente:
  - Subnet pública → Internet Gateway (0.0.0.0/0)
  - Subnets privadas → NAT Gateway (0.0.0.0/0)
- ✅ **DNS Resolution** habilitado en la VPC
- ✅ **DNS Hostnames** habilitado en la VPC

### Rangos CIDR

- No deben solapar con otras VPCs o redes corporativas
- Suficiente espacio para los servicios:
  - Lambda: ~50 IPs
  - MWAA: ~20 IPs
  - Redshift: ~10 IPs
  - Glue: ~100 IPs (para cluster Spark)

## Comandos AWS CLI para Obtener IDs

### VPC ID y CIDR
```bash
aws ec2 describe-vpcs --query 'Vpcs[*].[VpcId,CidrBlock,Tags[?Key==`Name`].Value|[0]]' --output table
```

### Subnet IDs
```bash
# Todas las subnets
aws ec2 describe-subnets --query 'Subnets[*].[SubnetId,CidrBlock,AvailabilityZone,Tags[?Key==`Name`].Value|[0]]' --output table

# Filtrar por VPC específica
aws ec2 describe-subnets --filters "Name=vpc-id,Values=vpc-XXXXXXXXX" --query 'Subnets[*].[SubnetId,CidrBlock,AvailabilityZone,Tags[?Key==`Name`].Value|[0]]' --output table
```

### Route Table IDs
```bash
aws ec2 describe-route-tables --filters "Name=vpc-id,Values=vpc-XXXXXXXXX" --query 'RouteTables[*].[RouteTableId,Tags[?Key==`Name`].Value|[0]]' --output table
```

### NAT Gateway ID
```bash
aws ec2 describe-nat-gateways --filter "Name=vpc-id,Values=vpc-XXXXXXXXX" --query 'NatGateways[*].[NatGatewayId,SubnetId,State]' --output table
```

### Internet Gateway ID
```bash
aws ec2 describe-internet-gateways --filters "Name=attachment.vpc-id,Values=vpc-XXXXXXXXX" --query 'InternetGateways[*].[InternetGatewayId]' --output table
```

## Ejemplo de Configuración

### terraform.tfvars (Landing Zone Existente)

```terraform
# ============================================================================
# Existing Landing Zone Configuration
# ============================================================================

# VPC existente del cliente
existing_vpc_id   = "vpc-0a1b2c3d4e5f6g7h8"
existing_vpc_cidr = "10.0.0.0/16"

# Subnets públicas (para NAT Gateway, API Gateway)
existing_public_subnet_ids = [
  "subnet-0a1b2c3d4e5f6g7h8",  # Subnet pública AZ A
]

# Subnets privadas 1 (para Lambda, MWAA, Redshift)
existing_private_subnet_1_ids = [
  "subnet-1a2b3c4d5e6f7g8h9",  # Subnet privada 1 AZ A
]

# Subnets privadas 2 (para AWS Glue ENIs)
existing_private_subnet_2_ids = [
  "subnet-2a3b4c5d6e7f8g9h0",  # Subnet privada 2 AZ A
]

# Route Tables (para VPC Endpoints Gateway)
existing_route_table_ids = [
  "rtb-0a1b2c3d4e5f6g7h8",  # Route table privada AZ A
]

# NAT Gateway (para alarmas de CloudWatch)
existing_nat_gateway_id = "nat-0a1b2c3d4e5f6g7h8"

# Internet Gateway (informativo)
existing_internet_gateway_id = "igw-0a1b2c3d4e5f6g7h8"
```

## Validación Pre-Deployment

Antes de ejecutar `terraform apply`, el cliente debe validar:

### 1. Verificar conectividad de subnets
```bash
aws ec2 describe-route-tables --route-table-ids rtb-XXXXXXXXX --query 'RouteTables[*].Routes'
```

### 2. Verificar DNS en VPC
```bash
aws ec2 describe-vpc-attribute --vpc-id vpc-XXXXXXXXX --attribute enableDnsSupport
aws ec2 describe-vpc-attribute --vpc-id vpc-XXXXXXXXX --attribute enableDnsHostnames
```

### 3. Verificar NAT Gateway funcional
```bash
aws ec2 describe-nat-gateways --nat-gateway-ids nat-XXXXXXXXX --query 'NatGateways[*].[State,ConnectivityType]'
```

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

## Beneficios de Usar Landing Zone Existente

### Para el Cliente
- ✅ Reutiliza inversión en infraestructura existente
- ✅ Cumple con políticas de red corporativas
- ✅ Mantiene consistencia con otros proyectos
- ✅ Reduce tiempo de deployment
- ✅ Simplifica gestión de red

### Para el Proyecto
- ✅ Integración más rápida
- ✅ Menos recursos a crear y gestionar
- ✅ Alineación con arquitectura corporativa
- ✅ Menor complejidad de deployment

## Compatibilidad

### Compatible con:
- ✅ Single-AZ deployment
- ✅ Multi-AZ deployment (si Landing Zone tiene subnets en múltiples AZs)
- ✅ Todos los módulos de Terraform (Security Groups, VPC Endpoints, EventBridge, Monitoring)
- ✅ Todas las configuraciones de ambiente (dev, staging, prod)

### No Compatible con:
- ❌ Módulo VPC (se deshabilita)
- ❌ Creación de subnets nuevas
- ❌ Creación de NAT Gateway nuevo

## Relación con Otros Documentos

### Documentos Complementarios

- **[../GUIA_LANDING_ZONE_CLIENTE.md](../GUIA_LANDING_ZONE_CLIENTE.md)** - Guía completa paso a paso ⭐ PRINCIPAL
- **[Infraestructura AWS - Resumen Ejecutivo.md](Infraestructura%20AWS%20-%20Resumen%20Ejecutivo.md)** - Visión general de infraestructura
- **[Especificación Detallada de Infraestructura AWS.md](Especificación%20Detallada%20de%20Infraestructura%20AWS.md)** - Detalles técnicos completos
- **[../terraform/README.md](../terraform/README.md)** - Documentación de Terraform
- **[../terraform/DEPLOYMENT_GUIDE.md](../terraform/DEPLOYMENT_GUIDE.md)** - Guía de deployment

### Flujo de Documentación

```
1. Infraestructura AWS - Resumen Ejecutivo
   ↓ (Decidir opción de deployment)
2. GUIA_LANDING_ZONE_CLIENTE.md (SI usa Landing Zone existente)
   ↓ (Configurar Terraform)
3. terraform/DEPLOYMENT_GUIDE.md
   ↓ (Desplegar)
4. Validación y Testing
   ✅ (Infraestructura desplegada)
```

## Cuándo Usar Cada Opción

### Usar VPC Nueva cuando:
- Es un ambiente de desarrollo o QA
- No existe Landing Zone corporativa
- Se requiere control total de la red
- Es un proyecto piloto o proof of concept
- Se necesita aislamiento completo

### Usar Landing Zone Existente cuando:
- Es un ambiente de producción
- Existe Landing Zone corporativa establecida
- Se deben cumplir políticas de red corporativas
- Se requiere integración con otros sistemas
- Se busca consistencia con otros proyectos

## Próximos Pasos

1. **Cliente**: Decidir qué opción usar (VPC nueva vs Landing Zone existente)
2. **Si Landing Zone**: Revisar guía completa en [GUIA_LANDING_ZONE_CLIENTE.md](../GUIA_LANDING_ZONE_CLIENTE.md)
3. **Cliente**: Obtener IDs de recursos existentes usando comandos AWS CLI
4. **Cliente**: Configurar terraform.tfvars con valores reales
5. **Validación**: Ejecutar validaciones pre-deployment
6. **Deployment**: Ejecutar terraform apply
7. **Verificación**: Validar recursos creados

## Notas Técnicas

### Cambios en Código Terraform

**Archivos Modificados**:
- `terraform/main.tf` - Comentar módulo VPC, actualizar referencias
- `terraform/variables.tf` - Agregar variables `existing_*`
- `terraform/outputs.tf` - Comentar outputs de VPC, agregar outputs informativos
- `terraform/terraform.tfvars` - Configurar valores de recursos existentes

**Módulos Afectados**:
- Security Groups - Usa `var.existing_vpc_id` en lugar de `module.vpc.vpc_id`
- VPC Endpoints - Usa `var.existing_private_subnet_1_ids` y `var.existing_route_table_ids`
- Monitoring - Usa `var.existing_vpc_id` y `var.existing_nat_gateway_id`

### Mantenimiento

- Actualizar IDs si cambian recursos en Landing Zone
- Sincronizar con cambios en políticas de red corporativas
- Revisar compatibilidad con nuevos módulos
- Documentar cambios en configuración

### Versionado

- Incluir en control de versiones (Git)
- Documentar cambios en commits
- Mantener historial de configuraciones
- Referenciar en documentación técnica

---

**Preparado por**: Kiro AI Assistant  
**Fecha**: 3 de Febrero, 2026  
**Versión**: 1.0  
**Estado**: ✅ Guía completa de Landing Zone existente creada

**Ubicación de la Guía**: [../GUIA_LANDING_ZONE_CLIENTE.md](../GUIA_LANDING_ZONE_CLIENTE.md)
