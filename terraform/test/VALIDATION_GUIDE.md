# Guía de Validación de Infraestructura con Terraform Plan

Esta guía te ayudará a validar toda la infraestructura AWS usando `terraform plan` sin necesidad de desplegar recursos reales.

## Requisitos Previos

1. **Terraform instalado** (versión >= 1.0)
2. **Credenciales AWS configuradas** (aunque no desplegaremos nada)
3. **Git Bash o PowerShell** en Windows

## Opción 1: Validación Rápida (Sin Credenciales AWS)

Si no tienes credenciales AWS o prefieres una validación rápida de sintaxis:

### Paso 1: Validar Sintaxis de Todos los Módulos

```powershell
# Desde el directorio terraform/
cd terraform

# Validar módulo VPC
cd modules/vpc
terraform init
terraform validate
cd ../..

# Validar módulo Security Groups
cd modules/security-groups
terraform init
terraform validate
cd ../..

# Validar módulo VPC Endpoints
cd modules/vpc-endpoints
terraform init
terraform validate
cd ../..

# Validar módulo Monitoring
cd modules/monitoring
terraform init
terraform validate
cd ../..

# Validar módulo EventBridge
cd modules/eventbridge
terraform init
terraform validate
cd ../..

# Validar módulo WAF
cd modules/waf
terraform init
terraform validate
cd ../..

# Validar módulo NACLs
cd modules/nacls
terraform init
terraform validate
cd ../..

# Validar módulo Tagging
cd modules/tagging
terraform init
terraform validate
cd ../..
```

## Opción 2: Validación Completa con Terraform Plan (Recomendado)

Esta opción valida que todos los módulos se integren correctamente y que la configuración sea válida.

### Paso 1: Preparar Credenciales AWS Temporales

Puedes usar credenciales temporales o incluso credenciales ficticias para el plan (no se conectará a AWS):

```powershell
# Configurar variables de entorno con credenciales temporales
$env:AWS_ACCESS_KEY_ID = "AKIAIOSFODNN7EXAMPLE"
$env:AWS_SECRET_ACCESS_KEY = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
$env:AWS_DEFAULT_REGION = "us-east-1"
```

**Nota:** Estas son credenciales de ejemplo de la documentación de AWS. Para un plan real, necesitarás credenciales válidas.

### Paso 2: Inicializar Terraform en el Directorio Principal

```powershell
cd terraform
terraform init
```

### Paso 3: Ejecutar Terraform Plan

```powershell
# Plan para ambiente de desarrollo
terraform plan -var-file="environments/dev/dev.tfvars" -out=dev.tfplan

# Si todo está bien, verás un resumen de los recursos que se crearían
```

### Paso 4: Revisar el Plan

El comando anterior generará un plan detallado mostrando:
- ✅ Recursos que se crearán
- ✅ Configuraciones de cada recurso
- ✅ Dependencias entre recursos
- ❌ Errores de configuración (si existen)

## Opción 3: Script Automatizado de Validación

He creado un script que valida toda la infraestructura automáticamente.

### Usar el Script de Validación

```powershell
cd terraform/test
.\validate_infrastructure.ps1
```

Este script:
1. Valida la sintaxis de todos los módulos
2. Verifica que no haya errores de configuración
3. Genera un reporte de validación
4. No requiere credenciales AWS reales

## Qué Validar en el Plan

Cuando ejecutes `terraform plan`, verifica:

### 1. VPC y Subnets
```
✓ VPC con CIDR 10.0.0.0/16
✓ 3 subnets en us-east-1a:
  - Public: 10.0.1.0/24
  - Private 1A: 10.0.10.0/24
  - Private 2A: 10.0.20.0/24
✓ DNS habilitado
```

### 2. Internet Connectivity
```
✓ Internet Gateway
✓ NAT Gateway en subnet pública
✓ Elastic IP para NAT Gateway
✓ Route tables configuradas correctamente
```

### 3. VPC Endpoints
```
✓ S3 Gateway Endpoint
✓ Interface Endpoints para:
  - Glue
  - Secrets Manager
  - CloudWatch Logs
  - KMS
  - STS
  - EventBridge
```

### 4. Security Groups
```
✓ SG-API-Gateway
✓ SG-Redshift-Existing
✓ SG-Lambda
✓ SG-MWAA
✓ SG-Glue
✓ SG-EventBridge
✓ SG-VPC-Endpoints
```

### 5. NACLs
```
✓ Public Subnet NACL
✓ Private Subnet NACL
```

### 6. WAF
```
✓ WAF Web ACL
✓ Rate limiting rule (2000 req/5min)
✓ Geo-blocking rule (solo Perú)
✓ AWS Managed Rules
```

### 7. EventBridge
```
✓ Custom event bus
✓ 5 scheduled rules (orders, products, stock, prices, stores)
✓ Dead Letter Queue
```

### 8. Monitoring
```
✓ VPC Flow Logs
✓ CloudWatch Log Groups
✓ CloudWatch Alarms
```

### 9. Tagging
```
✓ Todos los recursos tienen tags obligatorios:
  - Project
  - Environment
  - Component
  - Owner
  - CostCenter
```

## Errores Comunes y Soluciones

### Error: "No valid credential sources found"
**Solución:** Configura credenciales AWS temporales (ver Paso 1 de Opción 2)

### Error: "Module not installed"
**Solución:** Ejecuta `terraform init` primero

### Error: "Invalid CIDR block"
**Solución:** Verifica que los CIDR blocks en los .tfvars sean válidos

### Error: "Duplicate resource"
**Solución:** Verifica que no haya recursos duplicados en los módulos

## Validación Sin Despliegue

**IMPORTANTE:** `terraform plan` NO despliega nada en AWS. Solo:
- ✅ Valida la sintaxis
- ✅ Verifica la configuración
- ✅ Muestra qué se crearía
- ❌ NO crea recursos reales
- ❌ NO genera costos

## Siguiente Paso: Despliegue Real

Una vez que el plan esté validado y sin errores:

```powershell
# Para desplegar realmente (SOLO cuando estés listo)
terraform apply -var-file="environments/dev/dev.tfvars"
```

**⚠️ ADVERTENCIA:** `terraform apply` SÍ creará recursos reales en AWS y generará costos.

## Limpieza

Si ejecutaste `terraform init` y quieres limpiar:

```powershell
# Eliminar archivos temporales
Remove-Item -Recurse -Force .terraform
Remove-Item -Force .terraform.lock.hcl
Remove-Item -Force *.tfplan
```

## Resumen de Comandos

```powershell
# Validación rápida
cd terraform
terraform init
terraform validate

# Validación completa con plan
terraform plan -var-file="environments/dev/dev.tfvars"

# Ver plan guardado
terraform show dev.tfplan

# Limpiar
Remove-Item -Recurse -Force .terraform
```

## Soporte

Si encuentras errores durante la validación:
1. Lee el mensaje de error completo
2. Verifica la línea y archivo mencionados
3. Consulta la documentación de Terraform
4. Revisa los archivos .tfvars para valores incorrectos
