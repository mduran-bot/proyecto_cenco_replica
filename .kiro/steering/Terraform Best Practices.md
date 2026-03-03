# Terraform Best Practices

Este steering file establece las mejores prácticas para el uso de Terraform en la gestión de infraestructura AWS, asegurando código mantenible, seguro y escalable.

## Principios Fundamentales

### Infrastructure as Code (IaC)
- **Toda la infraestructura debe ser definida en código Terraform**
- **No realizar cambios manuales** en la consola AWS
- **Versionar todo el código** de infraestructura en Git
- **Usar Terraform para crear, modificar y destruir recursos**
- **Documentar cambios** en commits descriptivos

## Estructura de Proyecto

### Organización de Directorios
```
terraform/
├── environments/
│   ├── dev/
│   ├── staging/
│   └── prod/
├── modules/
│   ├── vpc/
│   ├── lambda/
│   ├── rds/
│   └── s3/
├── shared/
│   ├── backend.tf
│   ├── providers.tf
│   └── variables.tf
└── scripts/
    ├── plan.sh
    ├── apply.sh
    └── destroy.sh
```

### Separación por Ambientes
- **Usar workspaces o directorios separados** para cada ambiente
- **Mantener configuraciones específicas** por ambiente
- **Usar diferentes backends** para cada ambiente
- **Implementar promoción controlada** entre ambientes

## Gestión de Estado (State Management)

### Local State (Versión Gratuita)
- **Usar local state** almacenado en el directorio del proyecto
- **Incluir .tfstate en .gitignore** para evitar conflictos
- **Crear backups manuales** antes de cambios importantes
- **Usar terraform.tfstate.backup** para recuperación
- **Coordinar cambios** en equipo para evitar conflictos

### Backend Configuration Local
```hcl
# No configurar backend remoto - usar local por defecto
terraform {
  required_version = ">= 1.0"
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# El state se guardará automáticamente en terraform.tfstate
```

### Estructura de State Files
```
terraform/
├── environments/
│   ├── dev/
│   │   ├── terraform.tfstate      # State de desarrollo
│   │   ├── terraform.tfstate.backup
│   │   └── .terraform/
│   ├── staging/
│   │   ├── terraform.tfstate      # State de staging
│   │   ├── terraform.tfstate.backup
│   │   └── .terraform/
│   └── prod/
│       ├── terraform.tfstate      # State de producción
│       ├── terraform.tfstate.backup
│       └── .terraform/
```

### State Security Local
- **Añadir a .gitignore**: terraform.tfstate, terraform.tfstate.backup, .terraform/
- **Crear backups regulares** antes de apply
- **Usar diferentes directorios** por ambiente para separar states
- **Documentar ubicación** de state files para el equipo

## Desarrollo de Módulos

### Principios de Módulos
- **Crear módulos reutilizables** para componentes comunes
- **Seguir single responsibility principle**
- **Usar semantic versioning** para módulos
- **Documentar inputs y outputs** claramente
- **Implementar validation** en variables

### Estructura de Módulo
```
modules/vpc/
├── main.tf          # Recursos principales
├── variables.tf     # Input variables
├── outputs.tf       # Output values
├── versions.tf      # Provider requirements
├── README.md        # Documentación
└── examples/        # Ejemplos de uso
```

### Variables y Outputs
```hcl
# variables.tf
variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  validation {
    condition     = can(cidrhost(var.vpc_cidr, 0))
    error_message = "VPC CIDR must be a valid IPv4 CIDR block."
  }
}

# outputs.tf
output "vpc_id" {
  description = "ID of the VPC"
  value       = aws_vpc.main.id
}
```

## Naming Conventions

### Recursos
- **Usar nombres descriptivos** y consistentes
- **Incluir environment** en nombres de recursos
- **Usar snake_case** para nombres de recursos Terraform
- **Seguir convenciones AWS** para nombres de recursos

### Variables y Locals
```hcl
# Naming pattern: {environment}_{service}_{resource_type}
locals {
  common_tags = {
    Environment = var.environment
    Project     = var.project_name
    ManagedBy   = "terraform"
    Owner       = var.owner
  }
  
  name_prefix = "${var.environment}-${var.project_name}"
}
```

## Gestión de Variables

### Tipos de Variables
- **Usar .tfvars files** para valores específicos por ambiente
- **Definir defaults sensatos** en variables.tf
- **Usar environment variables** para valores sensibles
- **Implementar validation rules** cuando sea apropiado

### Variables Sensibles y Credenciales
```hcl
variable "aws_access_key_id" {
  description = "AWS Access Key ID"
  type        = string
  sensitive   = true
}

variable "aws_secret_access_key" {
  description = "AWS Secret Access Key"
  type        = string
  sensitive   = true
}

variable "aws_session_token" {
  description = "AWS Session Token (opcional para STS)"
  type        = string
  sensitive   = true
  default     = null
}

# Provider configuration con credenciales pasadas
provider "aws" {
  region     = var.aws_region
  access_key = var.aws_access_key_id
  secret_key = var.aws_secret_access_key
  token      = var.aws_session_token
  
  default_tags {
    tags = local.common_tags
  }
}
```

### Archivos de Variables por Ambiente
```hcl
# dev.tfvars
environment = "dev"
aws_region  = "us-east-1"
# Las credenciales se pasan por línea de comandos o variables de entorno

# prod.tfvars  
environment = "prod"
aws_region  = "us-east-1"
# Las credenciales se pasan por línea de comandos o variables de entorno
```

### Métodos de Autenticación
```bash
# Opción 1: Variables de entorno
export AWS_ACCESS_KEY_ID="your-access-key"
export AWS_SECRET_ACCESS_KEY="your-secret-key"
export AWS_SESSION_TOKEN="your-session-token"  # opcional
terraform apply -var-file="dev.tfvars"

# Opción 2: Pasar credenciales por línea de comandos
terraform apply \
  -var-file="dev.tfvars" \
  -var="aws_access_key_id=your-access-key" \
  -var="aws_secret_access_key=your-secret-key"

# Opción 3: Archivo de credenciales (NO commitear)
# credentials.tfvars (añadir a .gitignore)
aws_access_key_id     = "your-access-key"
aws_secret_access_key = "your-secret-key"

terraform apply -var-file="dev.tfvars" -var-file="credentials.tfvars"
```

## Seguridad

### Secrets Management Local
- **NUNCA hardcodear secretos** en código Terraform
- **Usar variables de entorno** para credenciales AWS
- **Marcar variables como sensitive**
- **Crear archivo credentials.tfvars** (añadir a .gitignore)
- **Documentar método de autenticación** para el equipo

### Credenciales AWS
- **Pasar credenciales como variables** en tiempo de ejecución
- **Usar variables de entorno** cuando sea posible
- **Rotar credenciales** regularmente
- **No almacenar credenciales** en archivos versionados
- **Usar diferentes credenciales** por ambiente

### IAM y Permisos
- **Aplicar principio de menor privilegio**
- **Usar roles de IAM** en lugar de usuarios
- **Crear policies específicas** para Terraform
- **Auditar permisos** regularmente

### Resource Security
```hcl
# Ejemplo: S3 bucket con seguridad
resource "aws_s3_bucket" "example" {
  bucket = local.bucket_name
  tags   = local.common_tags
}

resource "aws_s3_bucket_encryption" "example" {
  bucket = aws_s3_bucket.example.id
  
  server_side_encryption_configuration {
    rule {
      apply_server_side_encryption_by_default {
        sse_algorithm = "AES256"
      }
    }
  }
}

resource "aws_s3_bucket_public_access_block" "example" {
  bucket = aws_s3_bucket.example.id
  
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}
```

## Versionado y Providers

### Provider Versions
```hcl
terraform {
  required_version = ">= 1.0"
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
  
  default_tags {
    tags = local.common_tags
  }
}
```

### Version Constraints
- **Usar version constraints** específicos
- **Evitar latest** en producción
- **Probar upgrades** en ambientes de desarrollo primero
- **Documentar breaking changes**

## Tagging Strategy

### Tags Obligatorios
```hcl
locals {
  required_tags = {
    Environment   = var.environment
    Project      = var.project_name
    Owner        = var.owner
    ManagedBy    = "terraform"
    CostCenter   = var.cost_center
    CreatedDate  = formatdate("YYYY-MM-DD", timestamp())
  }
}
```

### Tag Enforcement
- **Aplicar tags** a todos los recursos que los soporten
- **Usar default_tags** en el provider AWS
- **Validar tags** con policies
- **Automatizar tag compliance** checking

## Testing y Validation

### Pre-commit Hooks
```bash
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/antonbabenko/pre-commit-terraform
    rev: v1.81.0
    hooks:
      - id: terraform_fmt
      - id: terraform_validate
      - id: terraform_docs
      - id: terraform_tflint
```

### Validation Commands (Local)
```bash
# Formatear código
terraform fmt -recursive

# Validar sintaxis
terraform validate

# Plan con credenciales por variables de entorno
export AWS_ACCESS_KEY_ID="your-access-key"
export AWS_SECRET_ACCESS_KEY="your-secret-key"
terraform plan -var-file="dev.tfvars"

# Plan con credenciales por parámetros
terraform plan \
  -var-file="dev.tfvars" \
  -var="aws_access_key_id=$AWS_ACCESS_KEY_ID" \
  -var="aws_secret_access_key=$AWS_SECRET_ACCESS_KEY"

# Verificar security issues
tfsec .

# Backup manual del state antes de apply
cp terraform.tfstate terraform.tfstate.backup.$(date +%Y%m%d_%H%M%S)
```

### Testing Framework
- **Usar Terratest** para testing automatizado
- **Implementar unit tests** para módulos
- **Crear integration tests** para infraestructura completa
- **Automatizar tests** en CI/CD pipeline

## CI/CD Integration

### Pipeline Stages (Local Development)
```bash
# Script de deployment local
#!/bin/bash
# deploy.sh

set -e

ENVIRONMENT=$1
AWS_ACCESS_KEY_ID=$2
AWS_SECRET_ACCESS_KEY=$3

if [ -z "$ENVIRONMENT" ] || [ -z "$AWS_ACCESS_KEY_ID" ] || [ -z "$AWS_SECRET_ACCESS_KEY" ]; then
    echo "Usage: ./deploy.sh <environment> <access_key> <secret_key>"
    exit 1
fi

cd "environments/$ENVIRONMENT"

# Backup del state actual
if [ -f "terraform.tfstate" ]; then
    cp terraform.tfstate "terraform.tfstate.backup.$(date +%Y%m%d_%H%M%S)"
fi

# Validación
terraform fmt -check
terraform validate

# Plan
terraform plan \
  -var-file="$ENVIRONMENT.tfvars" \
  -var="aws_access_key_id=$AWS_ACCESS_KEY_ID" \
  -var="aws_secret_access_key=$AWS_SECRET_ACCESS_KEY" \
  -out="$ENVIRONMENT.tfplan"

# Confirmación manual
read -p "Apply plan? (y/N): " confirm
if [ "$confirm" = "y" ] || [ "$confirm" = "Y" ]; then
    terraform apply "$ENVIRONMENT.tfplan"
    rm "$ENVIRONMENT.tfplan"
else
    echo "Deployment cancelled"
    rm "$ENVIRONMENT.tfplan"
    exit 1
fi
```

### Automation Rules (Local)
- **Automatizar validate y fmt** en pre-commit hooks
- **Requerir manual confirmation** para apply
- **Crear backups automáticos** del state
- **Usar scripts** para deployment consistente
- **Documentar proceso** de deployment

## Monitoring y Maintenance

### State Monitoring (Local)
- **Verificar integridad** del state regularmente
- **Crear backups manuales** antes de cambios importantes
- **Monitorear drift** comparando plan vs recursos reales
- **Documentar cambios** en el state file
- **Coordinar con el equipo** para evitar conflictos

### Resource Lifecycle
```hcl
# Ejemplo: Prevenir destrucción accidental
resource "aws_s3_bucket" "important_data" {
  bucket = "critical-data-bucket"
  
  lifecycle {
    prevent_destroy = true
  }
  
  tags = local.common_tags
}
```

### Cleanup Procedures (Local)
- **Limpiar recursos** no utilizados regularmente
- **Usar terraform destroy** con cuidado
- **Mantener backups** del state antes de destroy
- **Verificar dependencias** antes de eliminar recursos

## Documentation

### Code Documentation
```hcl
# Comentarios descriptivos
# This module creates a VPC with public and private subnets
# across multiple availability zones for high availability

resource "aws_vpc" "main" {
  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = true
  enable_dns_support   = true
  
  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-vpc"
  })
}
```

### README Requirements
- **Describir propósito** del módulo/configuración
- **Documentar inputs y outputs**
- **Incluir ejemplos** de uso
- **Especificar requirements** y dependencies
- **Mantener actualizada** la documentación

## Error Handling y Troubleshooting

### Common Issues (Local)
- **State lock conflicts**: No aplica con local state, pero coordinar cambios en equipo
- **Resource dependencies**: Usar depends_on explícitamente
- **Provider authentication**: Verificar credenciales pasadas correctamente
- **Resource limits**: Monitorear service quotas de AWS
- **State corruption**: Restaurar desde backup más reciente

### Debugging (Local)
```bash
# Enable detailed logging
export TF_LOG=DEBUG
export TF_LOG_PATH=terraform.log

# Refresh state (con credenciales)
terraform refresh \
  -var="aws_access_key_id=$AWS_ACCESS_KEY_ID" \
  -var="aws_secret_access_key=$AWS_SECRET_ACCESS_KEY"

# Import existing resources
terraform import \
  -var="aws_access_key_id=$AWS_ACCESS_KEY_ID" \
  -var="aws_secret_access_key=$AWS_SECRET_ACCESS_KEY" \
  aws_instance.example i-1234567890abcdef0

# Verificar state integrity
terraform show
terraform state list
```

### Backup y Recovery
```bash
# Script de backup automático
#!/bin/bash
# backup-state.sh

ENVIRONMENT=$1
BACKUP_DIR="backups"

mkdir -p "$BACKUP_DIR"

if [ -f "environments/$ENVIRONMENT/terraform.tfstate" ]; then
    cp "environments/$ENVIRONMENT/terraform.tfstate" \
       "$BACKUP_DIR/terraform.tfstate.$ENVIRONMENT.$(date +%Y%m%d_%H%M%S)"
    echo "Backup created for $ENVIRONMENT"
else
    echo "No state file found for $ENVIRONMENT"
fi
```

## Performance Optimization

### Plan Optimization
- **Usar -target** para cambios específicos
- **Implementar parallelism** apropiado
- **Usar -refresh=false** cuando sea seguro
- **Optimizar provider configuration**

### State Performance
- **Minimizar state size**
- **Usar remote state** eficientemente
- **Implementar state splitting** para proyectos grandes
- **Monitorear plan/apply times**

## Checklist de Implementación (Local)

Antes de aplicar cualquier configuración Terraform:

- [ ] Código formateado con `terraform fmt`
- [ ] Validación pasada con `terraform validate`
- [ ] Security scan completado con `tfsec`
- [ ] Credenciales AWS configuradas correctamente
- [ ] Backup del state actual creado
- [ ] Plan revisado y aprobado
- [ ] Tags aplicados según estrategia definida
- [ ] Variables sensibles manejadas apropiadamente
- [ ] Documentación actualizada
- [ ] Coordinación con equipo para evitar conflictos
- [ ] Rollback plan documentado

## Configuración de .gitignore

```gitignore
# Terraform
*.tfstate
*.tfstate.*
*.tfplan
*.tfplan.*
.terraform/
.terraform.lock.hcl

# Credenciales (NUNCA commitear)
credentials.tfvars
**/credentials.tfvars
*.pem
*.key

# Logs
terraform.log
*.log

# Backups locales
backups/
*.backup
```

## Scripts de Utilidad

### Script de Inicialización
```bash
#!/bin/bash
# init-environment.sh

ENVIRONMENT=$1

if [ -z "$ENVIRONMENT" ]; then
    echo "Usage: ./init-environment.sh <environment>"
    exit 1
fi

mkdir -p "environments/$ENVIRONMENT"
cd "environments/$ENVIRONMENT"

# Inicializar Terraform
terraform init

# Crear archivo de variables base
cat > "$ENVIRONMENT.tfvars" << EOF
environment = "$ENVIRONMENT"
aws_region  = "us-east-1"
project_name = "janis-cencosud"
EOF

echo "Environment $ENVIRONMENT initialized"
```

## Recursos Adicionales

- [Terraform Best Practices](https://www.terraform.io/docs/cloud/guides/recommended-practices/index.html)
- [AWS Provider Documentation](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)
- [Terraform Style Guide](https://www.terraform.io/docs/language/syntax/style.html)
- [Terragrunt for DRY Terraform](https://terragrunt.gruntwork.io/)