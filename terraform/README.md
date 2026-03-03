# Infraestructura AWS - Janis-Cencosud Integration

Este directorio contiene el código Terraform completo para desplegar toda la infraestructura AWS de la plataforma de integración Janis-Cencosud.

## Estructura del Proyecto

```
terraform/
├── README.md                    # Este archivo
├── DEPLOYMENT_NOTES.md          # ⚠️ Notas sobre módulos activos/deshabilitados
├── MULTI_AZ_EXPANSION.md        # Documentación de expansión Multi-AZ
├── main.tf                      # Orquestación principal
├── variables.tf                 # Definición de variables
├── outputs.tf                   # Outputs de recursos creados
├── versions.tf                  # Versiones de Terraform y providers
├── terraform.tfvars.example     # Plantilla para configuración del cliente
│
└── modules/
    ├── vpc/                     # VPC, Subnets, IGW, NAT Gateway
    ├── vpc-endpoints/           # Gateway y Interface Endpoints
    ├── security-groups/         # Security Groups
    ├── nacls/                   # Network ACLs (⚠️ Deshabilitado temporalmente)
    ├── waf/                     # AWS WAF
    ├── eventbridge/             # EventBridge
    └── monitoring/              # VPC Flow Logs, DNS Logs, Alarms
```

**⚠️ Nota Importante**: 6 de 7 módulos de infraestructura están habilitados en `main.tf`. El módulo NACLs está temporalmente deshabilitado (comentado) pendiente de decisión del cliente sobre implementación de Network ACLs. Ver [NACL_MODULE_DISABLED.md](./NACL_MODULE_DISABLED.md) para detalles sobre el estado actual y cómo habilitar NACLs cuando sea necesario.

## Arquitectura de Red

### Single-AZ Deployment (Actual)

La infraestructura está desplegada en una sola Availability Zone (us-east-1a) para reducir costos y complejidad:

- **Public Subnet A**: 10.0.1.0/24 (us-east-1a)
- **Private Subnet 1A**: 10.0.11.0/24 (us-east-1a) - Lambda, MWAA, Redshift
- **Private Subnet 2A**: 10.0.21.0/24 (us-east-1a) - Glue ENIs

### Reserved CIDR Blocks para Multi-AZ

Los siguientes bloques CIDR están **RESERVADOS** para futura expansión Multi-AZ:

- **Public Subnet B**: 10.0.2.0/24 (us-east-1b) - RESERVADO
- **Private Subnet 1B**: 10.0.11.0/24 (us-east-1b) - RESERVADO
- **Private Subnet 2B**: 10.0.21.0/24 (us-east-1b) - RESERVADO

⚠️ **NO usar estos CIDR blocks para ningún otro propósito**

Para instrucciones detalladas sobre migración a Multi-AZ, ver [MULTI_AZ_EXPANSION.md](./MULTI_AZ_EXPANSION.md).

## Testing Local con LocalStack

Antes de desplegar a AWS, puedes probar tu infraestructura localmente usando LocalStack:

### 1. Iniciar LocalStack
```bash
# Iniciar contenedor LocalStack
docker-compose -f docker-compose.localstack.yml up -d

# Verificar estado
curl http://localhost:4566/_localstack/health
```

### 2. Verificar Conectividad (Opcional)

Antes de desplegar toda la infraestructura, puedes probar la conectividad con un test simple:

```bash
cd terraform
terraform init

# Usar configuración de LocalStack
terraform plan -var-file="localstack.tfvars"
terraform apply -var-file="localstack.tfvars" -auto-approve
```

### 3. Configurar Terraform para LocalStack

LocalStack requiere configuración especial de endpoints. Crea un archivo `localstack.tfvars`:

```hcl
# localstack.tfvars
aws_region     = "us-east-1"
aws_account_id = "000000000000"  # Account ID fake para LocalStack
environment    = "localstack"

# Configuración simplificada para testing
enable_multi_az = false
enable_vpc_flow_logs = false
enable_dns_query_logging = false
```

Y configura el provider para usar LocalStack:

```hcl
# providers.tf (para LocalStack)
provider "aws" {
  region                      = "us-east-1"
  access_key                  = "test"
  secret_key                  = "test"
  skip_credentials_validation = true
  skip_metadata_api_check     = true
  skip_requesting_account_id  = true

  endpoints {
    ec2            = "http://localhost:4566"
    s3             = "http://localhost:4566"
    lambda         = "http://localhost:4566"
    apigateway     = "http://localhost:4566"
    kinesis        = "http://localhost:4566"
    glue           = "http://localhost:4566"
    secretsmanager = "http://localhost:4566"
    cloudwatch     = "http://localhost:4566"
    events         = "http://localhost:4566"
    iam            = "http://localhost:4566"
    sts            = "http://localhost:4566"
    kms            = "http://localhost:4566"
  }
}
```

### 4. Desplegar a LocalStack

```bash
terraform init
terraform plan -var-file="localstack.tfvars"
terraform apply -var-file="localstack.tfvars" -auto-approve
```

### 5. Verificar Recursos

```bash
# Listar VPCs
aws --endpoint-url=http://localhost:4566 ec2 describe-vpcs

# Listar Security Groups
aws --endpoint-url=http://localhost:4566 ec2 describe-security-groups

# Listar buckets S3 (incluye el bucket de test si lo creaste)
aws --endpoint-url=http://localhost:4566 s3 ls

# Ver outputs de Terraform
terraform output
```

### 5. Limpiar

```bash
# Destruir recursos
terraform destroy -var-file="localstack.tfvars" -auto-approve

# Detener LocalStack
docker-compose -f docker-compose.localstack.yml down
```

**Beneficios de LocalStack**:
- ✅ Desarrollo sin costos de AWS
- ✅ Iteración rápida sin esperar deployments reales
- ✅ Testing de módulos antes de aplicar a AWS
- ✅ Trabajo offline sin conexión a AWS

**Limitaciones**:
- ⚠️ Algunos servicios tienen funcionalidad limitada (Glue, Redshift)
- ⚠️ WAF y MWAA no soportados en versión Community
- ⚠️ Performance no refleja AWS real
- ⚠️ Operaciones pueden ser muy lentas (5+ minutos vs segundos en AWS real)
- ⚠️ Algunos recursos pueden atascarse durante deployment

**📖 Resultados de Testing**: Ver [DEPLOYMENT_STATUS_FINAL.md](./DEPLOYMENT_STATUS_FINAL.md) para análisis completo de deployment en LocalStack, incluyendo qué funciona, qué se atasca, y recomendaciones.

Ver [README-LOCALSTACK.md](../README-LOCALSTACK.md) para guía completa.

## 🚀 Quick Start - Deployment

**📖 Ver [GUIA_DEPLOYMENT_CENCOSUD.md](./GUIA_DEPLOYMENT_CENCOSUD.md) para guía oficial de deployment para Cencosud** ⭐ NUEVO

**📖 Ver [../AWS_DEPLOYMENT_READINESS_UPDATE.md](../AWS_DEPLOYMENT_READINESS_UPDATE.md) para estado actual**

**📖 Ver [AWS_PLAN_SUMMARY.md](./AWS_PLAN_SUMMARY.md) para resumen detallado del plan**

**📖 Ver [READY_FOR_AWS.md](./READY_FOR_AWS.md) para guía completa de deployment a AWS real**

**📖 Ver [DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md) para guía rápida de deployment**

**📖 Ver [GUIA_DEPLOYMENT_TESTING.md](./GUIA_DEPLOYMENT_TESTING.md) para deployment en ambiente de testing**

**📖 Ver [DEPLOYMENT_GUIDE_COMPLETE.md](./DEPLOYMENT_GUIDE_COMPLETE.md) para guía técnica completa paso a paso**

**📚 Ver [DOCUMENTATION_INDEX.md](./DOCUMENTATION_INDEX.md) para índice completo de documentación**

### Código Validado y Listo (3 de Febrero, 2026) ✅

El código Terraform ha sido **validado exitosamente mediante deployment de prueba**:
- ✅ 84 recursos desplegados y destruidos sin errores
- ✅ Todos los módulos funcionan correctamente
- ✅ Tags corporativos aplicados correctamente
- ✅ Correcciones aplicadas durante testing
- ✅ Listo para entrega al cliente

**Correcciones Aplicadas:**
- Tag BusinessUnit corregido (eliminado carácter `&` inválido)
- Security Groups ficticios reemplazados
- VPC Endpoints configurados para una sola subnet por AZ

Ver [TERRAFORM_DEPLOYMENT_TEST_RESULTS.md](../TERRAFORM_DEPLOYMENT_TEST_RESULTS.md) para detalles completos.

### Deployment en Testing

La guía de deployment en testing incluye:
- ✅ Estado de validación de todos los módulos
- 📋 Pasos simples para desplegar (4 pasos)
- 💰 Estimación de costos mensuales (~$40/mes)
- 🧪 Comandos de verificación post-deployment
- ⚠️ Advertencias importantes sobre costos

### Deployment en Ambiente de Testing

Si vas a deployar en una cuenta AWS de testing, usa la guía específica:

```powershell
cd terraform
.\deploy-testing.ps1
```

Ver [GUIA_DEPLOYMENT_TESTING.md](./GUIA_DEPLOYMENT_TESTING.md) para:
- Configuración de credenciales AWS
- Valores específicos para testing
- Script automatizado de deployment
- Estimación de costos (~$40/mes)
- Troubleshooting común

**⚠️ Si el script se atasca:** El paso de creación del plan puede tomar 2-5 minutos con infraestructura existente. Ver [TROUBLESHOOTING_PLAN_STUCK.md](./TROUBLESHOOTING_PLAN_STUCK.md) para soluciones si tarda más.

## Requisitos Previos

- Terraform >= 1.0
- AWS CLI configurado
- Credenciales AWS con permisos suficientes

## Testing Local con LocalStack

Antes de desplegar a AWS, puedes probar tu infraestructura localmente usando LocalStack:

1. **Iniciar LocalStack**:
   ```bash
   docker-compose up -d
   ```

2. **Verificar estado**:
   ```bash
   curl http://localhost:4566/_localstack/health
   ```

3. **Ver guía completa**: Consulta [LOCALSTACK_GUIDE.md](../LOCALSTACK_GUIDE.md) en la raíz del proyecto para instrucciones detalladas sobre:
   - Configuración de Terraform para LocalStack
   - Comandos útiles de AWS CLI
   - Troubleshooting
   - Limitaciones y servicios soportados

**Beneficios de LocalStack**:
- ✅ Desarrollo sin costos de AWS
- ✅ Iteración rápida sin esperar deployments
- ✅ Testing de módulos antes de aplicar a AWS real
- ✅ Trabajo offline

## Configuración del Cliente

1. **Copiar el archivo de ejemplo**:
   ```bash
   cp terraform.tfvars.example terraform.tfvars
   ```

2. **Editar `terraform.tfvars`** con los valores específicos de su organización:
   - AWS Account ID y región
   - CIDR de VPC (verificar que no conflictúe con redes corporativas)
   - IDs de recursos existentes (Redshift, Security Groups de BI)
   - Rangos de IPs permitidos
   - Tags corporativos
   - Configuración de monitoreo

3. **Revisar y ajustar módulos** según políticas corporativas:
   - Security Groups: Ajustar reglas según políticas de firewall
   - WAF: Ajustar rate limits y geo-blocking
   - Tags: Agregar tags corporativos adicionales
   - Monitoring: Ajustar retention periods

## Deployment

### Automated Deployment Scripts

El directorio `scripts/` contiene scripts de utilidad para facilitar el deployment y gestión de la infraestructura:

#### 1. init-environment.sh - Inicialización de Ambientes

Inicializa un nuevo ambiente Terraform con la estructura correcta:

```bash
cd terraform/scripts
./init-environment.sh dev
```

**Características**:
- Crea estructura de directorios
- Configura symlinks a archivos compartidos
- Genera main.tf, outputs.tf, y .tfvars base
- Ejecuta terraform init y validate
- Crea .gitignore para proteger archivos sensibles

#### 2. deploy.sh - Deployment Automatizado

Script completo de deployment con validaciones y confirmación manual:

```bash
cd terraform/scripts

# Usando variables de entorno
export AWS_ACCESS_KEY_ID="your-key"
export AWS_SECRET_ACCESS_KEY="your-secret"
./deploy.sh dev

# Pasando credenciales como argumentos
./deploy.sh dev AKIAIOSFODNN7EXAMPLE wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
```

**Características**:
- Backup automático del state antes de cambios
- Validación de formato (terraform fmt)
- Validación de configuración (terraform validate)
- Security scan con tfsec (si está instalado)
- Plan con revisión manual
- Confirmación explícita antes de apply
- Logging de deployment con metadata

#### 3. backup-state.sh - Gestión de Backups

Automatiza backups del state file con opciones de gestión:

```bash
cd terraform/scripts

# Backup de un ambiente
./backup-state.sh dev

# Backup de todos los ambientes
./backup-state.sh --all

# Listar backups existentes
./backup-state.sh dev --list

# Limpiar backups antiguos (mantener últimos 10)
./backup-state.sh dev --clean 10

# Restaurar desde backup
./backup-state.sh dev --restore environments/dev/backups/terraform.tfstate.backup.20240126_143000
```

**Características**:
- Backups con timestamp automático
- Listado de backups con tamaños
- Limpieza de backups antiguos
- Restauración segura con safety backup
- Soporte para múltiples ambientes

Ver documentación completa en [scripts/README.md](./scripts/README.md).

### Deployment Manual

Si prefieres ejecutar los comandos manualmente:

#### Inicialización
```bash
terraform init
```

### Validación
```bash
terraform validate
terraform fmt -check
```

### Plan
```bash
terraform plan -var-file="terraform.tfvars" -out="plan.tfplan"
```

### Aplicar
```bash
terraform apply "plan.tfplan"
```

### Destruir (con precaución)
```bash
terraform destroy -var-file="terraform.tfvars"
```

## Gestión de Credenciales

**Opción 1: Variables de entorno**
```bash
export AWS_ACCESS_KEY_ID="your-access-key"
export AWS_SECRET_ACCESS_KEY="your-secret-key"
export AWS_SESSION_TOKEN="your-session-token"  # opcional
terraform apply -var-file="terraform.tfvars"
```

**Opción 2: AWS CLI Profile**
```bash
export AWS_PROFILE="cencosud-prod"
terraform apply -var-file="terraform.tfvars"
```

## Ambientes

Para desplegar en diferentes ambientes, crear archivos `.tfvars` específicos:

```bash
# Desarrollo
terraform apply -var-file="dev.tfvars"

# Staging
terraform apply -var-file="staging.tfvars"

# Producción
terraform apply -var-file="prod.tfvars"
```

## Seguridad

⚠️ **IMPORTANTE**:
- Nunca commitear `terraform.tfvars` con valores reales
- Nunca commitear credenciales AWS
- Usar `.gitignore` para excluir archivos sensibles
- Rotar credenciales regularmente

## Costos Estimados

- **Single-AZ**: $111.70-152.70/mes
- **Multi-AZ**: $148.20-202.20/mes

Ver documento de especificación para desglose detallado.

## Testing y Validación

### Guía Rápida de Validación

Para validar la infraestructura sin desplegar recursos reales:

```powershell
# Opción 1: Script automatizado (más fácil)
cd test
.\validate_infrastructure.ps1

# Opción 2: Validación manual con terraform plan
cd terraform
terraform init
terraform plan -var-file="environments/dev/dev.tfvars"
```

**📖 Ver [test/VALIDATION_GUIDE.md](./test/VALIDATION_GUIDE.md) para guía completa** que incluye:
- Validación sin credenciales AWS
- Validación completa con terraform plan
- Qué validar en cada componente (VPC, Security Groups, WAF, etc.)
- Solución de errores comunes
- Comandos de limpieza

**📖 Ver [QUICK_VALIDATION.md](./QUICK_VALIDATION.md) para referencia rápida**

### Automated Tests

El directorio `test/` contiene tests automatizados para validar la infraestructura:

#### PowerShell Validation Scripts (Recomendado)

Scripts de validación que no requieren instalación de Go:

```powershell
cd test

# Validar Security Groups
.\validate_security_groups_unit_tests.ps1
.\validate_security_groups.ps1

# Validar Network ACLs
.\validate_nacl.ps1

# Validar Routing Configuration
.\validate_routing_configuration.ps1

# Validar VPC CIDR
.\validate_vpc_cidr.ps1
```

#### Go-Based Property Tests

Para tests más exhaustivos con Terratest (requiere Go 1.21+):

```bash
cd test

# Primero, corregir compatibilidad de API si es necesario
python fix_go_tests.py

# Ejecutar todos los tests
go test -v -timeout 30m

# Ejecutar tests específicos
go test -v -run TestSG
go test -v -run TestNACL
go test -v -run TestRouting
```

#### Test Maintenance

**fix_go_tests.py**: Script de mantenimiento que actualiza automáticamente los archivos de test Go para compatibilidad con versiones nuevas de Terratest.

```bash
cd test
python fix_go_tests.py
```

Usar este script:
- Después de actualizar Terratest
- Cuando los tests fallen por cambios de API
- Antes de ejecutar tests Go por primera vez

Ver [test/README.md](./test/README.md) y [test/TESTING_GUIDE.md](./test/TESTING_GUIDE.md) para documentación completa.

## Preparación para GitLab

Si necesitas subir este proyecto a un repositorio GitLab, consulta:

**[../GITLAB_PREPARATION.md](../GITLAB_PREPARATION.md)** - Guía completa de preparación para GitLab

La guía incluye:
- ✅ Lista de archivos a incluir/excluir
- ✅ Estructura final del repositorio
- ✅ Configuración de .gitignore
- ✅ Pasos para limpiar el proyecto
- ✅ Comandos Git para push inicial
- ✅ Checklist de seguridad
- ✅ Buenas prácticas de versionado

**Archivos clave a excluir:**
- ❌ `*.tfstate` y `*.tfstate.*` (contienen información sensible)
- ❌ `*.tfplan` (pueden contener secretos)
- ❌ `.terraform/` (se regenera con terraform init)
- ❌ `terraform.tfvars` con valores reales (usar .example)
- ❌ Archivos de testing y LocalStack
- ❌ Logs y backups

**Archivos a incluir:**
- ✅ Código Terraform (`.tf`)
- ✅ Documentación (`.md`)
- ✅ Scripts de deployment
- ✅ Plantillas de configuración (`.tfvars.example`)
- ✅ Módulos reutilizables

## Soporte

Para preguntas o issues, contactar al equipo de DevOps/Infrastructure.
