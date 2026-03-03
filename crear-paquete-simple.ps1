# Script para Crear Paquete de Entrega para Cencosud
# Crea un archivo ZIP con los archivos necesarios para deployment

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

Write-Host "Creando Paquete de Entrega para Cencosud..." -ForegroundColor Cyan
Write-Host ""

# Copiar código Terraform
Write-Host "[1/4] Copiando código Terraform..." -ForegroundColor Yellow
New-Item -ItemType Directory -Path "$tempDir/terraform" | Out-Null
New-Item -ItemType Directory -Path "$tempDir/terraform/modules" | Out-Null
New-Item -ItemType Directory -Path "$tempDir/terraform/scripts" | Out-Null

# Archivos principales
Copy-Item "terraform/main.tf" "$tempDir/terraform/"
Copy-Item "terraform/variables.tf" "$tempDir/terraform/"
Copy-Item "terraform/outputs.tf" "$tempDir/terraform/"
Copy-Item "terraform/versions.tf" "$tempDir/terraform/"
Copy-Item "terraform/.gitignore" "$tempDir/terraform/"
Copy-Item "terraform/terraform.tfvars.example" "$tempDir/terraform/"
Copy-Item "terraform/terraform.tfvars.prod" "$tempDir/terraform/"

# Módulos
$modules = @("vpc", "security-groups", "vpc-endpoints", "nacls", "eventbridge", "monitoring", "s3", "kinesis-firehose", "lambda", "api-gateway", "glue", "mwaa")
foreach ($module in $modules) {
    $modulePath = "terraform/modules/$module"
    if (Test-Path $modulePath) {
        Copy-Item -Recurse $modulePath "$tempDir/terraform/modules/"
    }
}

# Scripts
if (Test-Path "terraform/scripts") {
    Copy-Item "terraform/scripts/*.ps1" "$tempDir/terraform/scripts/" -ErrorAction SilentlyContinue
    Copy-Item "terraform/scripts/*.sh" "$tempDir/terraform/scripts/" -ErrorAction SilentlyContinue
}

Write-Host "  OK - Terraform copiado" -ForegroundColor Green

# Copiar documentación
Write-Host "[2/4] Copiando documentación..." -ForegroundColor Yellow
$docs = @(
    "README.md",
    "SPEC_1_COMPLIANCE_VERIFICATION.md",
    "RESUMEN_PARA_ENVIO_CENCOSUD.md",
    "ACCIONES_FINALES_ANTES_DE_ENVIAR.md",
    "DEPLOYMENT_SUCCESS_SUMMARY.md"
)

foreach ($doc in $docs) {
    if (Test-Path $doc) {
        Copy-Item $doc "$tempDir/"
    }
}

# Documentación de Terraform
if (Test-Path "terraform/DEPLOYMENT_GUIDE_COMPLETE.md") {
    Copy-Item "terraform/DEPLOYMENT_GUIDE_COMPLETE.md" "$tempDir/terraform/"
}
if (Test-Path "terraform/MULTI_AZ_EXPANSION.md") {
    Copy-Item "terraform/MULTI_AZ_EXPANSION.md" "$tempDir/terraform/"
}
if (Test-Path "terraform/README.md") {
    Copy-Item "terraform/README.md" "$tempDir/terraform/"
}

Write-Host "  OK - Documentación copiada" -ForegroundColor Green

# Copiar documentación adicional
Write-Host "[3/4] Copiando documentación adicional..." -ForegroundColor Yellow
if (Test-Path "Documentación Cenco") {
    Copy-Item -Recurse "Documentación Cenco" "$tempDir/"
}
Write-Host "  OK - Documentación adicional copiada" -ForegroundColor Green

# Crear archivo ZIP
Write-Host "[4/4] Creando archivo ZIP..." -ForegroundColor Yellow
if (Test-Path $packageName) {
    Remove-Item $packageName
}

Add-Type -Assembly "System.IO.Compression.FileSystem"
[System.IO.Compression.ZipFile]::CreateFromDirectory(
    (Resolve-Path $tempDir).Path,
    (Join-Path (Get-Location) $packageName),
    [System.IO.Compression.CompressionLevel]::Optimal,
    $false
)

Write-Host "  OK - ZIP creado" -ForegroundColor Green
Write-Host ""

# Limpiar
Remove-Item -Recurse -Force $tempDir

# Resumen
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Paquete Creado Exitosamente" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Archivo: $packageName" -ForegroundColor White
Write-Host "Tamaño: $([math]::Round((Get-Item $packageName).Length / 1MB, 2)) MB" -ForegroundColor White
Write-Host ""
Write-Host "Contenido:" -ForegroundColor Yellow
Write-Host "  - Código Terraform completo" -ForegroundColor White
Write-Host "  - 12 módulos" -ForegroundColor White
Write-Host "  - Archivos de configuración" -ForegroundColor White
Write-Host "  - Documentación completa" -ForegroundColor White
Write-Host "  - Scripts de utilidad" -ForegroundColor White
Write-Host ""
Write-Host "Listo para enviar a Cencosud!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
