# Script para crear paquete de producción Terraform Cencosud
# Solo incluye archivos necesarios para deployment

$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$zipName = "janis-cencosud-terraform-prod-$timestamp.zip"
$tempDir = "temp-terraform-prod"

Write-Host "Creando paquete de producción Terraform..." -ForegroundColor Cyan

# Limpiar directorio temporal si existe
if (Test-Path $tempDir) {
    Remove-Item -Recurse -Force $tempDir
}

# Crear estructura de directorios
New-Item -ItemType Directory -Path $tempDir -Force | Out-Null
New-Item -ItemType Directory -Path "$tempDir/terraform" -Force | Out-Null
New-Item -ItemType Directory -Path "$tempDir/terraform/modules" -Force | Out-Null
New-Item -ItemType Directory -Path "$tempDir/terraform/shared" -Force | Out-Null
New-Item -ItemType Directory -Path "$tempDir/terraform/scripts" -Force | Out-Null

# Copiar archivos raíz de terraform
Write-Host "Copiando archivos principales de Terraform..." -ForegroundColor Yellow
$rootFiles = @(
    "terraform/main.tf",
    "terraform/variables.tf",
    "terraform/outputs.tf",
    "terraform/versions.tf",
    "terraform/terraform.tfvars.example",
    "terraform/terraform.tfvars.prod",
    "terraform/.gitignore"
)

foreach ($file in $rootFiles) {
    if (Test-Path $file) {
        Copy-Item $file "$tempDir/$file" -Force
        Write-Host "  ✓ $file" -ForegroundColor Green
    }
}

# Copiar módulos completos
Write-Host "`nCopiando módulos de Terraform..." -ForegroundColor Yellow
$modules = @(
    "api-gateway",
    "eventbridge",
    "glue",
    "kinesis-firehose",
    "lambda",
    "monitoring",
    "mwaa",
    "nacls",
    "s3",
    "security-groups",
    "tagging",
    "vpc",
    "vpc-endpoints",
    "waf"
)

foreach ($module in $modules) {
    $modulePath = "terraform/modules/$module"
    if (Test-Path $modulePath) {
        New-Item -ItemType Directory -Path "$tempDir/$modulePath" -Force | Out-Null
        
        # Copiar solo archivos .tf y .hcl
        Get-ChildItem "$modulePath" -Filter "*.tf" | ForEach-Object {
            Copy-Item $_.FullName "$tempDir/$modulePath/" -Force
        }
        
        Get-ChildItem "$modulePath" -Filter "*.hcl" | ForEach-Object {
            Copy-Item $_.FullName "$tempDir/$modulePath/" -Force
        }
        
        Write-Host "  ✓ $module" -ForegroundColor Green
    }
}

# Copiar archivos shared
Write-Host "`nCopiando configuración compartida..." -ForegroundColor Yellow
$sharedFiles = @(
    "terraform/shared/backend.tf",
    "terraform/shared/providers.tf",
    "terraform/shared/variables.tf"
)

foreach ($file in $sharedFiles) {
    if (Test-Path $file) {
        Copy-Item $file "$tempDir/$file" -Force
        Write-Host "  ✓ $file" -ForegroundColor Green
    }
}

# Copiar scripts de deployment
Write-Host "`nCopiando scripts de deployment..." -ForegroundColor Yellow
$scripts = @(
    "terraform/scripts/deploy.sh",
    "terraform/scripts/init-environment.sh",
    "terraform/scripts/backup-state.sh"
)

foreach ($script in $scripts) {
    if (Test-Path $script) {
        Copy-Item $script "$tempDir/$script" -Force
        Write-Host "  ✓ $script" -ForegroundColor Green
    }
}

# Crear README de deployment
Write-Host "`nCreando README de deployment..." -ForegroundColor Yellow
$readmeContent = @"
# Janis-Cencosud AWS Infrastructure - Terraform

## Contenido del Paquete

Este paquete contiene la infraestructura completa de AWS para el proyecto Janis-Cencosud, lista para deployment en producción.

### Estructura

``````
terraform/
├── main.tf                    # Configuración principal
├── variables.tf               # Variables de entrada
├── outputs.tf                 # Outputs de infraestructura
├── versions.tf                # Versiones de providers
├── terraform.tfvars.example   # Ejemplo de configuración
├── terraform.tfvars.prod      # Configuración de producción
├── modules/                   # Módulos reutilizables
├── shared/                    # Configuración compartida
└── scripts/                   # Scripts de deployment
``````

## Pre-requisitos

1. **Terraform**: >= 1.0
2. **AWS CLI**: Configurado con credenciales apropiadas
3. **Permisos AWS**: Acceso administrativo o permisos específicos documentados

## Configuración Inicial

### 1. Configurar Credenciales AWS

``````bash
# Opción 1: Variables de entorno
export AWS_ACCESS_KEY_ID="your-access-key"
export AWS_SECRET_ACCESS_KEY="your-secret-key"
export AWS_SESSION_TOKEN="your-session-token"  # Si usa STS

# Opción 2: AWS CLI Profile
aws configure --profile cencosud-prod
``````

### 2. Configurar Variables

Copiar y editar el archivo de variables:

``````bash
cd terraform
cp terraform.tfvars.example terraform.tfvars
``````

Editar `terraform.tfvars` con los valores específicos de su ambiente.

## Deployment

### Inicialización

``````bash
cd terraform
terraform init
``````

### Validación

``````bash
# Formatear código
terraform fmt -recursive

# Validar configuración
terraform validate

# Revisar plan de deployment
terraform plan -var-file="terraform.tfvars.prod"
``````

### Aplicar Cambios

``````bash
# Crear backup del state (si existe)
cp terraform.tfstate terraform.tfstate.backup.\$(date +%Y%m%d_%H%M%S)

# Aplicar infraestructura
terraform apply -var-file="terraform.tfvars.prod"
``````

## Módulos Incluidos

- **vpc**: Red privada virtual con subnets públicas/privadas
- **api-gateway**: API REST para webhooks
- **lambda**: Funciones serverless de procesamiento
- **kinesis-firehose**: Streaming de datos
- **s3**: Data Lake (Bronze/Silver/Gold)
- **glue**: Jobs ETL y Data Catalog
- **mwaa**: Apache Airflow managed
- **eventbridge**: Scheduling y event routing
- **monitoring**: CloudWatch dashboards y alarmas
- **security-groups**: Reglas de firewall
- **nacls**: Network ACLs
- **vpc-endpoints**: Endpoints privados para servicios AWS
- **waf**: Web Application Firewall
- **tagging**: Estrategia de etiquetado corporativo

## Configuración de Producción

El archivo `terraform.tfvars.prod` contiene la configuración optimizada para producción:

- Multi-AZ deployment para alta disponibilidad
- Cifrado habilitado en todos los servicios
- Backups automáticos configurados
- Monitoreo y alertas activos
- Tagging corporativo aplicado

## Seguridad

### Credenciales

- **NUNCA** commitear archivos con credenciales
- Usar variables de entorno o AWS Secrets Manager
- Rotar credenciales regularmente

### State Management

- El state se almacena localmente por defecto
- Crear backups antes de cada apply
- Coordinar cambios con el equipo

## Troubleshooting

### Error de Credenciales

``````bash
# Verificar credenciales
aws sts get-caller-identity

# Verificar permisos
aws iam get-user
``````

### Error de State Lock

``````bash
# Si el state está bloqueado, esperar o forzar unlock
terraform force-unlock <LOCK_ID>
``````

### Rollback

``````bash
# Restaurar desde backup
cp terraform.tfstate.backup.YYYYMMDD_HHMMSS terraform.tfstate
terraform refresh
``````

## Soporte

Para soporte técnico o preguntas sobre el deployment, contactar al equipo de infraestructura.

## Notas Importantes

1. **Backup**: Siempre crear backup del state antes de apply
2. **Validación**: Revisar el plan completo antes de aplicar
3. **Coordinación**: Coordinar deployments con el equipo
4. **Monitoreo**: Verificar CloudWatch después del deployment
5. **Costos**: Monitorear AWS Cost Explorer después del deployment

---

**Versión**: 1.0
**Fecha**: $(Get-Date -Format "yyyy-MM-dd")
**Proyecto**: Janis-Cencosud AWS Infrastructure
"@

Set-Content -Path "$tempDir/README.md" -Value $readmeContent -Encoding UTF8
Write-Host "  ✓ README.md creado" -ForegroundColor Green

# Crear .gitignore
Write-Host "`nCreando .gitignore..." -ForegroundColor Yellow
$gitignoreContent = @"
# Terraform
*.tfstate
*.tfstate.*
*.tfplan
*.tfplan.*
.terraform/
.terraform.lock.hcl

# Credenciales
terraform.tfvars
credentials.tfvars
*.pem
*.key

# Logs
*.log
terraform.log

# Backups
backups/
*.backup

# OS
.DS_Store
Thumbs.db
"@

Set-Content -Path "$tempDir/.gitignore" -Value $gitignoreContent -Encoding UTF8
Write-Host "  ✓ .gitignore creado" -ForegroundColor Green

# Crear archivo de deployment script para Linux/Mac
Write-Host "`nCreando script de deployment..." -ForegroundColor Yellow
$deployScript = @"
#!/bin/bash
# Script de deployment para Terraform Cencosud

set -e

echo "==================================="
echo "Janis-Cencosud Terraform Deployment"
echo "==================================="
echo ""

# Verificar que estamos en el directorio correcto
if [ ! -f "terraform/main.tf" ]; then
    echo "Error: Debe ejecutar este script desde el directorio raíz del proyecto"
    exit 1
fi

cd terraform

# Verificar credenciales AWS
echo "Verificando credenciales AWS..."
if ! aws sts get-caller-identity > /dev/null 2>&1; then
    echo "Error: Credenciales AWS no configuradas"
    echo "Configure sus credenciales con: aws configure"
    exit 1
fi

echo "✓ Credenciales AWS verificadas"
echo ""

# Inicializar Terraform
echo "Inicializando Terraform..."
terraform init

# Validar configuración
echo ""
echo "Validando configuración..."
terraform fmt -check -recursive
terraform validate

# Crear plan
echo ""
echo "Creando plan de deployment..."
terraform plan -var-file="terraform.tfvars.prod" -out="prod.tfplan"

# Confirmar deployment
echo ""
read -p "¿Desea aplicar este plan? (y/N): " confirm
if [ "\$confirm" = "y" ] || [ "\$confirm" = "Y" ]; then
    # Backup del state si existe
    if [ -f "terraform.tfstate" ]; then
        echo "Creando backup del state..."
        cp terraform.tfstate "terraform.tfstate.backup.\$(date +%Y%m%d_%H%M%S)"
    fi
    
    # Aplicar cambios
    echo ""
    echo "Aplicando infraestructura..."
    terraform apply "prod.tfplan"
    
    # Limpiar plan
    rm prod.tfplan
    
    echo ""
    echo "✓ Deployment completado exitosamente"
else
    echo "Deployment cancelado"
    rm prod.tfplan
    exit 0
fi
"@

Set-Content -Path "$tempDir/deploy.sh" -Value $deployScript -Encoding UTF8
Write-Host "  ✓ deploy.sh creado" -ForegroundColor Green

# Crear script de deployment para Windows
$deployScriptWin = @"
@echo off
REM Script de deployment para Terraform Cencosud (Windows)

echo ===================================
echo Janis-Cencosud Terraform Deployment
echo ===================================
echo.

REM Verificar que estamos en el directorio correcto
if not exist "terraform\main.tf" (
    echo Error: Debe ejecutar este script desde el directorio raiz del proyecto
    exit /b 1
)

cd terraform

REM Verificar credenciales AWS
echo Verificando credenciales AWS...
aws sts get-caller-identity >nul 2>&1
if errorlevel 1 (
    echo Error: Credenciales AWS no configuradas
    echo Configure sus credenciales con: aws configure
    exit /b 1
)

echo OK Credenciales AWS verificadas
echo.

REM Inicializar Terraform
echo Inicializando Terraform...
terraform init

REM Validar configuracion
echo.
echo Validando configuracion...
terraform fmt -check -recursive
terraform validate

REM Crear plan
echo.
echo Creando plan de deployment...
terraform plan -var-file="terraform.tfvars.prod" -out="prod.tfplan"

REM Confirmar deployment
echo.
set /p confirm="Desea aplicar este plan? (y/N): "
if /i "%confirm%"=="y" (
    REM Backup del state si existe
    if exist "terraform.tfstate" (
        echo Creando backup del state...
        copy terraform.tfstate "terraform.tfstate.backup.%date:~-4,4%%date:~-7,2%%date:~-10,2%_%time:~0,2%%time:~3,2%%time:~6,2%"
    )
    
    REM Aplicar cambios
    echo.
    echo Aplicando infraestructura...
    terraform apply "prod.tfplan"
    
    REM Limpiar plan
    del prod.tfplan
    
    echo.
    echo OK Deployment completado exitosamente
) else (
    echo Deployment cancelado
    del prod.tfplan
    exit /b 0
)
"@

Set-Content -Path "$tempDir/deploy.cmd" -Value $deployScriptWin -Encoding UTF8
Write-Host "  ✓ deploy.cmd creado" -ForegroundColor Green

# Crear el ZIP
Write-Host "`nCreando archivo ZIP..." -ForegroundColor Yellow
if (Test-Path $zipName) {
    Remove-Item $zipName -Force
}

Compress-Archive -Path "$tempDir/*" -DestinationPath $zipName -Force

# Limpiar directorio temporal
Remove-Item -Recurse -Force $tempDir

# Mostrar resumen
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "PAQUETE DE PRODUCCIÓN CREADO" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Archivo: $zipName" -ForegroundColor Yellow
Write-Host "Tamaño: $([math]::Round((Get-Item $zipName).Length / 1MB, 2)) MB" -ForegroundColor Yellow
Write-Host ""
Write-Host "Contenido incluido:" -ForegroundColor Cyan
Write-Host "  ✓ Archivos principales de Terraform (.tf)" -ForegroundColor Green
Write-Host "  ✓ 14 módulos completos" -ForegroundColor Green
Write-Host "  ✓ Configuración compartida" -ForegroundColor Green
Write-Host "  ✓ Scripts de deployment (Linux/Windows)" -ForegroundColor Green
Write-Host "  ✓ Configuración de producción" -ForegroundColor Green
Write-Host "  ✓ README con instrucciones completas" -ForegroundColor Green
Write-Host "  ✓ .gitignore configurado" -ForegroundColor Green
Write-Host ""
Write-Host "Archivos EXCLUIDOS:" -ForegroundColor Cyan
Write-Host "  ✗ Archivos .md de documentación" -ForegroundColor Gray
Write-Host "  ✗ Ejecutables de Terraform" -ForegroundColor Gray
Write-Host "  ✗ Archivos .tfstate" -ForegroundColor Gray
Write-Host "  ✗ Directorio .terraform/" -ForegroundColor Gray
Write-Host "  ✗ Archivos de test" -ForegroundColor Gray
Write-Host ""
Write-Host "Para usar el paquete:" -ForegroundColor Cyan
Write-Host "  1. Extraer el ZIP" -ForegroundColor White
Write-Host "  2. Configurar credenciales AWS" -ForegroundColor White
Write-Host "  3. Editar terraform/terraform.tfvars.prod" -ForegroundColor White
Write-Host "  4. Ejecutar deploy.sh (Linux/Mac) o deploy.cmd (Windows)" -ForegroundColor White
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
