# Environment Configuration Standardization

**Fecha**: 29 de Enero, 2026  
**Cambio**: Estandarización de configuraciones de ambientes

## Resumen del Cambio

Se ha estandarizado la configuración del módulo VPC en todos los ambientes (dev, staging, prod) para garantizar consistencia y facilitar el mantenimiento.

## Configuración Estandarizada

Todos los ambientes ahora utilizan la misma estructura de configuración del módulo VPC:

```hcl
module "vpc" {
  source = "../../modules/vpc"

  vpc_cidr                 = var.vpc_cidr
  aws_region               = var.aws_region
  name_prefix              = local.name_prefix
  tags                     = local.common_tags
  enable_multi_az          = false  # true solo en prod
  public_subnet_a_cidr     = "10.0.1.0/24"
  public_subnet_b_cidr     = "10.0.2.0/24"
  private_subnet_1a_cidr   = "10.0.11.0/24"
  private_subnet_1b_cidr   = "10.0.12.0/24"
  private_subnet_2a_cidr   = "10.0.21.0/24"
  private_subnet_2b_cidr   = "10.0.22.0/24"
}
```

## Cambios Específicos

### Ambiente Dev (terraform/environments/dev/main.tf)

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
  enable_multi_az          = false
  public_subnet_a_cidr     = "10.0.1.0/24"
  public_subnet_b_cidr     = "10.0.2.0/24"
  private_subnet_1a_cidr   = "10.0.11.0/24"
  private_subnet_1b_cidr   = "10.0.12.0/24"
  private_subnet_2a_cidr   = "10.0.21.0/24"
  private_subnet_2b_cidr   = "10.0.22.0/24"
}
```

### Ambientes Staging y Prod

Ya estaban configurados con la estructura estandarizada. La única diferencia es:
- **Dev y Staging**: `enable_multi_az = false`
- **Prod**: `enable_multi_az = true`

## Bloques CIDR Estandarizados

### Single-AZ (Activos en todos los ambientes)

| Subnet | CIDR | AZ | Propósito |
|--------|------|-----|-----------|
| Public Subnet A | 10.0.1.0/24 | us-east-1a | NAT Gateway, ALB |
| Private Subnet 1A | 10.0.11.0/24 | us-east-1a | Lambda, MWAA, Redshift |
| Private Subnet 2A | 10.0.21.0/24 | us-east-1a | AWS Glue ENIs |

### Multi-AZ (Reservados para expansión)

| Subnet | CIDR | AZ | Estado |
|--------|------|-----|--------|
| Public Subnet B | 10.0.2.0/24 | us-east-1b | RESERVADO |
| Private Subnet 1B | 10.0.12.0/24 | us-east-1b | RESERVADO |
| Private Subnet 2B | 10.0.22.0/24 | us-east-1b | RESERVADO |

## Beneficios de la Estandarización

1. **Consistencia**: Todos los ambientes tienen la misma estructura de red
2. **Mantenibilidad**: Cambios en un ambiente se pueden replicar fácilmente
3. **Documentación**: Una sola referencia para todos los ambientes
4. **Testing**: Los tests de validación funcionan igual en todos los ambientes
5. **Expansión Multi-AZ**: Preparado para activar con un solo cambio de variable

## Variables Explícitas vs Implícitas

### Antes (Implícito)
El módulo VPC usaba valores por defecto internos para:
- `aws_region`
- `tags` (vs `common_tags`)
- `enable_multi_az`
- CIDRs de subnets

### Después (Explícito)
Todos los valores se pasan explícitamente desde el ambiente, proporcionando:
- Mayor claridad sobre qué se está configurando
- Facilidad para override en ambientes específicos
- Mejor documentación del código
- Menos "magia" y más transparencia

## Impacto en Documentación

Se actualizaron los siguientes documentos para reflejar los CIDRs correctos:

1. **Documentación Cenco/Especificación Detallada de Infraestructura AWS.md**
   - Sección 2.2.2: Private Subnet 1A (10.0.10.0/24 → 10.0.11.0/24)
   - Sección 2.2.3: Private Subnet 2A (10.0.20.0/24 → 10.0.21.0/24)
   - Sección 3.3: Route Tables

2. **terraform/README.md**
   - Sección "Single-AZ Deployment"

## Próximos Pasos

1. ✅ Configuración estandarizada en todos los ambientes
2. ✅ Documentación actualizada
3. ⏭️ Validar con `terraform plan` en cada ambiente
4. ⏭️ Aplicar cambios en dev primero
5. ⏭️ Validar funcionamiento en dev
6. ⏭️ Aplicar en staging y prod

## Comandos de Validación

```bash
# Validar dev
cd terraform/environments/dev
terraform init
terraform plan -var-file="dev.tfvars"

# Validar staging
cd terraform/environments/staging
terraform init
terraform plan -var-file="staging.tfvars"

# Validar prod
cd terraform/environments/prod
terraform init
terraform plan -var-file="prod.tfvars"
```

## Notas Importantes

⚠️ **IMPORTANTE**: Los bloques CIDR 10.0.2.0/24, 10.0.12.0/24, y 10.0.22.0/24 están **RESERVADOS** para expansión Multi-AZ. No deben ser utilizados para ningún otro propósito.

✅ **VENTAJA**: Para habilitar Multi-AZ en cualquier ambiente, solo se necesita cambiar `enable_multi_az = true` en el archivo main.tf del ambiente correspondiente.

---

**Autor**: Kiro AI Assistant  
**Revisión**: Pendiente  
**Estado**: Documentación completa
