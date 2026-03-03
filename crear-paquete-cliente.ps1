# ============================================================================
# Script para Crear Paquete de Entrega para Cencosud
# ============================================================================
# Este script crea un archivo ZIP con solo los archivos necesarios para
# que el cliente pueda ejecutar Terraform en su cuenta AWS
# ============================================================================

$ErrorActionPreference = "Stop"

# Nombre del paquete
$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$packageName = "janis-cencosud-aws-infrastructure-$timestamp.zip"

# Crear directorio temporal
$tempDir = "temp-package"
if (Test-Path $tempDir) {
    Remove-Item -Recurse -Force $tempDir
}
New-Item -ItemType Directory -Path $tempDir | Out-Null

Write-Host "==================================================================" -ForegroundColor Cyan
Write-Host "Creando Paquete de Entrega para Cencosud" -ForegroundColor Cyan
Write-Host "==================================================================" -ForegroundColor Cyan
Write-Host ""

# ============================================================================
# 1. Copiar código Terraform
# ============================================================================
Write-Host "[1/5] Copiando código Terraform..." -ForegroundColor Yellow

# Crear estructura de directorios
New-Item -ItemType Directory -Path "$tempDir/terraform" | Out-Null
New-Item -ItemType Directory -Path "$tempDir/terraform/modules" | Out-Null
New-Item -ItemType Directory -Path "$tempDir/terraform/scripts" | Out-Null

# Copiar archivos principales de Terraform
Copy-Item "terraform/main.tf" "$tempDir/terraform/"
Copy-Item "terraform/variables.tf" "$tempDir/terraform/"
Copy-Item "terraform/outputs.tf" "$tempDir/terraform/"
Copy-Item "terraform/versions.tf" "$tempDir/terraform/"
Copy-Item "terraform/.gitignore" "$tempDir/terraform/"

# Copiar archivos de configuración
Copy-Item "terraform/terraform.tfvars.example" "$tempDir/terraform/"
Copy-Item "terraform/terraform.tfvars.prod" "$tempDir/terraform/"

# Copiar todos los módulos
$modules = @(
    "vpc",
    "security-groups",
    "vpc-endpoints",
    "nacls",
    "eventbridge",
    "monitoring",
    "s3",
    "kinesis-firehose",
    "lambda",
    "api-gateway",
    "glue",
    "mwaa"
)

foreach ($module in $modules) {
    $modulePath = "terraform/modules/$module"
    if (Test-Path $modulePath) {
        Copy-Item -Recurse $modulePath "$tempDir/terraform/modules/"
        Write-Host "  ✓ Módulo $module copiado" -ForegroundColor Green
    }
}

# Copiar scripts de utilidad
Copy-Item "terraform/scripts/*.ps1" "$tempDir/terraform/scripts/" -ErrorAction SilentlyContinue
Copy-Item "terraform/scripts/*.sh" "$tempDir/terraform/scripts/" -ErrorAction SilentlyContinue

Write-Host "  ✓ Código Terraform copiado" -ForegroundColor Green
Write-Host ""

# ============================================================================
# 2. Copiar documentación principal
# ============================================================================
Write-Host "[2/5] Copiando documentación..." -ForegroundColor Yellow

# Documentación principal
$docs = @(
    "README.md",
    "SPEC_1_COMPLIANCE_VERIFICATION.md",
    "RESUMEN_PARA_ENVIO_CENCOSUD.md",
    "ACCIONES_FINALES_ANTES_DE_ENVIAR.md",
    "DEPLOYMENT_SUCCESS_SUMMARY.md",
    "INTEGRACION_COMPLETA_RESUMEN.md",
    "DATA_PIPELINE_MODULES_SUMMARY.md"
)

foreach ($doc in $docs) {
    if (Test-Path $doc) {
        Copy-Item $doc "$tempDir/"
        Write-Host "  ✓ $doc copiado" -ForegroundColor Green
    }
}

# Documentación de Terraform
$terraformDocs = @(
    "terraform/DEPLOYMENT_GUIDE_COMPLETE.md",
    "terraform/MULTI_AZ_EXPANSION.md",
    "terraform/README.md"
)

foreach ($doc in $terraformDocs) {
    if (Test-Path $doc) {
        Copy-Item $doc "$tempDir/terraform/"
        Write-Host "  ✓ $(Split-Path $doc -Leaf) copiado" -ForegroundColor Green
    }
}

Write-Host "  ✓ Documentación copiada" -ForegroundColor Green
Write-Host ""

# ============================================================================
# 3. Copiar documentación adicional de Cencosud
# ============================================================================
Write-Host "[3/5] Copiando documentación adicional..." -ForegroundColor Yellow

if (Test-Path "Documentación Cenco") {
    Copy-Item -Recurse "Documentación Cenco" "$tempDir/"
    Write-Host "  ✓ Documentación Cenco copiada" -ForegroundColor Green
}

Write-Host ""

# ============================================================================
# 4. Crear archivo README de instrucciones
# ============================================================================
Write-Host "[4/5] Creando README de instrucciones..." -ForegroundColor Yellow

$readmeContent = @"
# Janis-Cencosud AWS Infrastructure - Paquete de Entrega

**Fecha de Generación**: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")
**Versión**: 1.0
**Estado**: Listo para Deployment

---

## 📦 Contenido del Paquete

Este paquete contiene todo lo necesario para desplegar la infraestructura AWS de integración Janis-Cencosud:

### Código Terraform
- ``terraform/`` - Código completo de infraestructura
  - ``main.tf`` - Configuración principal
  - ``variables.tf`` - Variables (60+)
  - ``outputs.tf`` - Outputs (30+)
  - ``modules/`` - 12 módulos reutilizables
  - ``scripts/`` - Scripts de utilidad

### Archivos de Configuración
- ``terraform.tfvars.example`` - Plantilla de configuración
- ``terraform.tfvars.prod`` - Configuración de producción (base)

### Documentación
- ``SPEC_1_COMPLIANCE_VERIFICATION.md`` - Verificación de cumplimiento (100%)
- ``RESUMEN_PARA_ENVIO_CENCOSUD.md`` - Resumen ejecutivo
- ``DEPLOYMENT_SUCCESS_SUMMARY.md`` - Evidencia de deployment exitoso
- ``terraform/DEPLOYMENT_GUIDE_COMPLETE.md`` - Guía paso a paso
- ``terraform/MULTI_AZ_EXPANSION.md`` - Plan de expansión Multi-AZ

---

## 🚀 Inicio Rápido

### 1. Preparar Configuración

``````powershell
cd terraform
cp terraform.tfvars.prod terraform.tfvars
``````

Editar ``terraform.tfvars`` y actualizar:
- ``aws_account_id`` - Tu Account ID de AWS
- ``cost_center`` - Código de cost center real
- ``existing_redshift_cluster_id`` - ID de tu cluster Redshift
- ``existing_redshift_sg_id`` - Security Group de Redshift
- ``allowed_janis_ip_ranges`` - Rangos IP específicos de Janis

### 2. Inicializar Terraform

``````powershell
terraform init
``````

### 3. Validar Configuración

``````powershell
terraform fmt -recursive
terraform validate
``````

### 4. Planificar Deployment

``````powershell
terraform plan
``````

Revisar que se crearán aproximadamente 141 recursos.

### 5. Aplicar Infraestructura

``````powershell
terraform apply
``````

Confirmar con ``yes`` cuando se solicite.

---

## ⚠️ Importante Antes de Ejecutar

### Configuración Requerida

- [ ] Actualizar ``aws_account_id`` en terraform.tfvars
- [ ] Actualizar ``cost_center`` con código real
- [ ] Configurar ``existing_redshift_cluster_id`` y ``existing_redshift_sg_id``
- [ ] Cambiar ``allowed_janis_ip_ranges`` a rangos específicos (no 0.0.0.0/0)
- [ ] Configurar ``alarm_sns_topic_arn`` si existe
- [ ] Revisar y ajustar ``existing_bi_security_groups`` y ``existing_bi_ip_ranges``

### Componentes Deshabilitados (Correcto)

Los siguientes componentes están deshabilitados porque no tienen código aún:
- Lambda Functions (``create_lambda_*`` = false)
- API Gateway (``create_api_gateway`` = false)
- Glue Jobs (``create_glue_*_job`` = false)
- MWAA (``create_mwaa_environment`` = false)

Estos se habilitarán en Fase 2 cuando se desarrolle el código.

### Excepciones Acordadas

- **WAF**: NO implementado - Cencosud lo configura centralmente
- **CloudTrail**: NO implementado - Cencosud lo configura centralmente

---

## 📊 Recursos que se Crearán

- 1 VPC (10.0.0.0/16)
- 3 Subnets (1 pública, 2 privadas)
- 1 Internet Gateway
- 1 NAT Gateway + Elastic IP
- 3 Route Tables
- 7 Security Groups
- 2 Network ACLs
- 7 VPC Endpoints (1 Gateway + 6 Interface)
- 5 S3 Buckets (Bronze, Silver, Gold, Scripts, Logs)
- 1 Kinesis Firehose Stream
- 3 Glue Databases
- 1 EventBridge Event Bus
- 5 EventBridge Scheduled Rules
- 1 SQS Dead Letter Queue
- 5 IAM Roles
- VPC Flow Logs
- 11 CloudWatch Alarms
- 4 CloudWatch Metric Filters

**Total**: ~141 recursos

---

## 💰 Costos Estimados

### Infraestructura Base (Fase 1)
- NAT Gateway: ~`$32/mes
- S3 Storage: ~`$1-5/mes
- Kinesis Firehose: ~`$0.029/GB
- CloudWatch Logs: ~`$0.50/GB
- EventBridge: ~`$1/mes
- VPC Endpoints: ~`$7/mes por endpoint (~`$49/mes total)

**Total Fase 1**: ~`$85-100/mes

### Con Componentes Completos (Fase 2)
- Infraestructura Base: ~`$85-100/mes
- Lambda Functions: ~`$5-10/mes
- API Gateway: ~`$3.50/millón requests
- Glue Jobs: ~`$0.44/DPU-hour
- MWAA (mw1.small): ~`$300/mes

**Total Fase 2**: ~`$400-500/mes

---

## 📞 Soporte

Para consultas sobre este deployment:

1. Revisar ``SPEC_1_COMPLIANCE_VERIFICATION.md`` para verificación completa
2. Consultar ``terraform/DEPLOYMENT_GUIDE_COMPLETE.md`` para guía detallada
3. Revisar ``RESUMEN_PARA_ENVIO_CENCOSUD.md`` para resumen ejecutivo

---

## ✅ Checklist Pre-Deployment

- [ ] Configuración actualizada en terraform.tfvars
- [ ] Credenciales AWS configuradas
- [ ] ``terraform init`` ejecutado exitosamente
- [ ] ``terraform validate`` sin errores
- [ ] ``terraform plan`` revisado y aprobado
- [ ] Costos estimados revisados y aprobados
- [ ] Equipo de seguridad notificado (WAF, CloudTrail)
- [ ] Backup plan documentado

---

**Preparado por**: Equipo de Data Engineering
**Fecha**: $(Get-Date -Format "yyyy-MM-dd")
**Versión**: 1.0
**Estado**: ✅ Listo para Deployment en AWS Cencosud
"@

$readmeContent | Out-File -FilePath "$tempDir/LEEME_PRIMERO.md" -Encoding UTF8
Write-Host "  ✓ README de instrucciones creado" -ForegroundColor Green
Write-Host ""

# ============================================================================
# 5. Crear archivo ZIP
# ============================================================================
Write-Host "[5/5] Creando archivo ZIP..." -ForegroundColor Yellow

if (Test-Path $packageName) {
    Remove-Item $packageName
}

# Comprimir usando .NET (más confiable que Compress-Archive para archivos grandes)
Add-Type -Assembly "System.IO.Compression.FileSystem"
[System.IO.Compression.ZipFile]::CreateFromDirectory(
    (Resolve-Path $tempDir).Path,
    (Join-Path (Get-Location) $packageName),
    [System.IO.Compression.CompressionLevel]::Optimal,
    $false
)

Write-Host "  ✓ Archivo ZIP creado: $packageName" -ForegroundColor Green
Write-Host ""

# Limpiar directorio temporal
Remove-Item -Recurse -Force $tempDir

# ============================================================================
# Resumen Final
# ============================================================================
Write-Host "==================================================================" -ForegroundColor Cyan
Write-Host "✅ Paquete Creado Exitosamente" -ForegroundColor Green
Write-Host "==================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Archivo: $packageName" -ForegroundColor White
Write-Host "Tamaño: $([math]::Round((Get-Item $packageName).Length / 1MB, 2)) MB" -ForegroundColor White
Write-Host ""
Write-Host "Contenido:" -ForegroundColor Yellow
Write-Host "  ✓ Código Terraform completo (12 módulos)" -ForegroundColor Green
Write-Host "  ✓ Archivos de configuración" -ForegroundColor Green
Write-Host "  ✓ Documentación completa" -ForegroundColor Green
Write-Host "  ✓ Scripts de utilidad" -ForegroundColor Green
Write-Host "  ✓ Guías de deployment" -ForegroundColor Green
Write-Host ""
Write-Host "Próximos Pasos:" -ForegroundColor Yellow
Write-Host "  1. Enviar $packageName a Cencosud" -ForegroundColor White
Write-Host "  2. Cliente debe leer LEEME_PRIMERO.md" -ForegroundColor White
Write-Host "  3. Cliente configura terraform.tfvars" -ForegroundColor White
Write-Host "  4. Cliente ejecuta terraform apply" -ForegroundColor White
Write-Host ""
Write-Host "==================================================================" -ForegroundColor Cyan
"@

$readmeContent | Out-File -FilePath "$tempDir/LEEME_PRIMERO.md" -Encoding UTF8
Write-Host "  ✓ README de instrucciones creado" -ForegroundColor Green
Write-Host ""

# ============================================================================
# 5. Crear archivo ZIP
# ============================================================================
Write-Host "[5/5] Creando archivo ZIP..." -ForegroundColor Yellow

if (Test-Path $packageName) {
    Remove-Item $packageName
}

# Comprimir usando .NET (más confiable que Compress-Archive para archivos grandes)
Add-Type -Assembly "System.IO.Compression.FileSystem"
[System.IO.Compression.ZipFile]::CreateFromDirectory(
    (Resolve-Path $tempDir).Path,
    (Join-Path (Get-Location) $packageName),
    [System.IO.Compression.CompressionLevel]::Optimal,
    $false
)

Write-Host "  ✓ Archivo ZIP creado: $packageName" -ForegroundColor Green
Write-Host ""

# Limpiar directorio temporal
Remove-Item -Recurse -Force $tempDir

# ============================================================================
# Resumen Final
# ============================================================================
Write-Host "==================================================================" -ForegroundColor Cyan
Write-Host "✅ Paquete Creado Exitosamente" -ForegroundColor Green
Write-Host "==================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Archivo: $packageName" -ForegroundColor White
Write-Host "Tamaño: $([math]::Round((Get-Item $packageName).Length / 1MB, 2)) MB" -ForegroundColor White
Write-Host ""
Write-Host "Contenido:" -ForegroundColor Yellow
Write-Host "  ✓ Código Terraform completo (12 módulos)" -ForegroundColor Green
Write-Host "  ✓ Archivos de configuración" -ForegroundColor Green
Write-Host "  ✓ Documentación completa" -ForegroundColor Green
Write-Host "  ✓ Scripts de utilidad" -ForegroundColor Green
Write-Host "  ✓ Guías de deployment" -ForegroundColor Green
Write-Host ""
Write-Host "Próximos Pasos:" -ForegroundColor Yellow
Write-Host "  1. Enviar $packageName a Cencosud" -ForegroundColor White
Write-Host "  2. Cliente debe leer LEEME_PRIMERO.md" -ForegroundColor White
Write-Host "  3. Cliente configura terraform.tfvars" -ForegroundColor White
Write-Host "  4. Cliente ejecuta terraform apply" -ForegroundColor White
Write-Host ""
Write-Host "==================================================================" -ForegroundColor Cyan
