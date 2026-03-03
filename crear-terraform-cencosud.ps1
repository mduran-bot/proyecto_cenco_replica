# Script para crear paquete Terraform Cencosud
# Solo archivos necesarios para ejecutar Terraform

$zipName = "terraform-cencosud.zip"

Write-Host "Creando paquete Terraform Cencosud..." -ForegroundColor Cyan

# Crear directorio temporal
$tempDir = "temp_terraform_package"
if (Test-Path $tempDir) {
    Remove-Item -Recurse -Force $tempDir
}
New-Item -ItemType Directory -Path $tempDir | Out-Null

# Copiar directorio terraform completo
Write-Host "Copiando archivos Terraform..." -ForegroundColor Yellow
Copy-Item -Path "terraform" -Destination "$tempDir/terraform" -Recurse

# Limpiar archivos innecesarios del directorio terraform
$cleanupPaths = @(
    "$tempDir/terraform/.terraform",
    "$tempDir/terraform/terraform.tfstate",
    "$tempDir/terraform/terraform.tfstate.backup",
    "$tempDir/terraform/*.tfplan",
    "$tempDir/terraform/test",
    "$tempDir/terraform/environments"
)

foreach ($path in $cleanupPaths) {
    if (Test-Path $path) {
        Write-Host "  Eliminando: $path" -ForegroundColor Gray
        Remove-Item -Recurse -Force $path
    }
}

# Eliminar archivos de documentacion innecesarios en modules
Get-ChildItem -Path "$tempDir/terraform/modules" -Recurse -Include "*.md" | Where-Object {
    $_.Name -notlike "README.md"
} | ForEach-Object {
    Write-Host "  Eliminando: $($_.FullName)" -ForegroundColor Gray
    Remove-Item -Force $_.FullName
}

# Eliminar archivos .terraform.lock.hcl de subdirectorios
Get-ChildItem -Path "$tempDir/terraform/modules" -Recurse -Filter ".terraform.lock.hcl" | ForEach-Object {
    Write-Host "  Eliminando: $($_.FullName)" -ForegroundColor Gray
    Remove-Item -Force $_.FullName
}

# Crear README simple
$readmeContent = @"
# Terraform Cencosud - Infraestructura AWS

## Contenido

Este paquete contiene la infraestructura completa de AWS para el proyecto Janis-Cencosud.

## Requisitos Previos

1. Terraform >= 1.0
2. AWS CLI configurado con credenciales
3. Permisos AWS necesarios

## Deployment

### 1. Configurar Credenciales AWS

export AWS_ACCESS_KEY_ID="tu-access-key"
export AWS_SECRET_ACCESS_KEY="tu-secret-key"

### 2. Inicializar Terraform

cd terraform
terraform init

### 3. Planificar Deployment

terraform plan -var-file="terraform.tfvars.prod"

### 4. Aplicar Configuracion

terraform apply -var-file="terraform.tfvars.prod"

## Recursos Creados

El deployment crea aproximadamente 141 recursos:
- VPC y Networking
- Security Groups
- VPC Endpoints
- S3 Buckets (Bronze, Silver, Gold, Scripts, Logs)
- Glue Databases
- Kinesis Firehose
- EventBridge
- CloudWatch Monitoring

## Costos Estimados

Infraestructura base: ~145-185 USD/mes

---

Proyecto: Janis-Cencosud Integration
Version: 1.0
Fecha: Febrero 2026
"@

Set-Content -Path "$tempDir/README.md" -Value $readmeContent

# Crear archivo .gitignore
$gitignoreContent = @"
# Terraform
.terraform/
*.tfstate
*.tfstate.*
*.tfplan
*.tfplan.*
.terraform.lock.hcl

# Credenciales
credentials.tfvars
*.pem
*.key

# Logs
terraform.log
*.log
"@

Set-Content -Path "$tempDir/.gitignore" -Value $gitignoreContent

# Crear el ZIP
Write-Host "Creando archivo ZIP..." -ForegroundColor Yellow
if (Test-Path $zipName) {
    Remove-Item -Force $zipName
}

Compress-Archive -Path "$tempDir/*" -DestinationPath $zipName -CompressionLevel Optimal

# Limpiar directorio temporal
Remove-Item -Recurse -Force $tempDir

# Mostrar informacion del archivo
$zipInfo = Get-Item $zipName
$sizeKB = [math]::Round($zipInfo.Length / 1KB, 2)

Write-Host ""
Write-Host "Paquete creado exitosamente!" -ForegroundColor Green
Write-Host "  Archivo: $zipName" -ForegroundColor Cyan
Write-Host "  Tamano: $sizeKB KB" -ForegroundColor Cyan
Write-Host ""
Write-Host "Contenido del paquete:" -ForegroundColor Yellow
Write-Host "  - Codigo Terraform completo (12 modulos)"
Write-Host "  - Configuracion de produccion (terraform.tfvars.prod)"
Write-Host "  - README con instrucciones de deployment"
Write-Host "  - .gitignore para seguridad"
Write-Host ""
Write-Host "Listo para enviar!" -ForegroundColor Green
