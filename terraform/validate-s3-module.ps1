# ============================================================================
# Script de Validación del Módulo S3
# ============================================================================
# Este script valida que el módulo S3 está correctamente configurado
# ============================================================================

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Validación del Módulo S3" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$ErrorCount = 0

# ============================================================================
# 1. Verificar que existen los archivos del módulo
# ============================================================================

Write-Host "1. Verificando archivos del módulo S3..." -ForegroundColor Yellow

$RequiredFiles = @(
    "modules/s3/main.tf",
    "modules/s3/variables.tf",
    "modules/s3/outputs.tf",
    "modules/s3/README.md"
)

foreach ($file in $RequiredFiles) {
    if (Test-Path $file) {
        Write-Host "  ✓ $file existe" -ForegroundColor Green
    } else {
        Write-Host "  ✗ $file NO existe" -ForegroundColor Red
        $ErrorCount++
    }
}

Write-Host ""

# ============================================================================
# 2. Verificar que main.tf incluye el módulo S3
# ============================================================================

Write-Host "2. Verificando integración en main.tf..." -ForegroundColor Yellow

$MainTfContent = Get-Content "main.tf" -Raw

if ($MainTfContent -match 'module\s+"s3"') {
    Write-Host "  ✓ Módulo S3 está declarado en main.tf" -ForegroundColor Green
} else {
    Write-Host "  ✗ Módulo S3 NO está declarado en main.tf" -ForegroundColor Red
    $ErrorCount++
}

Write-Host ""

# ============================================================================
# 3. Verificar que variables.tf tiene las variables de S3
# ============================================================================

Write-Host "3. Verificando variables en variables.tf..." -ForegroundColor Yellow

$VariablesTfContent = Get-Content "variables.tf" -Raw

$RequiredVariables = @(
    "bronze_glacier_transition_days",
    "bronze_expiration_days",
    "silver_glacier_transition_days",
    "silver_expiration_days",
    "gold_intelligent_tiering_days",
    "logs_expiration_days"
)

foreach ($var in $RequiredVariables) {
    if ($VariablesTfContent -match "variable\s+`"$var`"") {
        Write-Host "  ✓ Variable '$var' definida" -ForegroundColor Green
    } else {
        Write-Host "  ✗ Variable '$var' NO definida" -ForegroundColor Red
        $ErrorCount++
    }
}

Write-Host ""

# ============================================================================
# 4. Verificar que outputs.tf tiene los outputs de S3
# ============================================================================

Write-Host "4. Verificando outputs en outputs.tf..." -ForegroundColor Yellow

$OutputsTfContent = Get-Content "outputs.tf" -Raw

$RequiredOutputs = @(
    "bronze_bucket_name",
    "silver_bucket_name",
    "gold_bucket_name",
    "scripts_bucket_name",
    "logs_bucket_name"
)

foreach ($output in $RequiredOutputs) {
    if ($OutputsTfContent -match "output\s+`"$output`"") {
        Write-Host "  ✓ Output '$output' definido" -ForegroundColor Green
    } else {
        Write-Host "  ✗ Output '$output' NO definido" -ForegroundColor Red
        $ErrorCount++
    }
}

Write-Host ""

# ============================================================================
# 5. Verificar sintaxis de Terraform
# ============================================================================

Write-Host "5. Validando sintaxis de Terraform..." -ForegroundColor Yellow

# Verificar si terraform está instalado
$TerraformInstalled = Get-Command terraform -ErrorAction SilentlyContinue

if ($TerraformInstalled) {
    Write-Host "  Ejecutando terraform init..." -ForegroundColor Cyan
    terraform init -upgrade > $null 2>&1
    
    Write-Host "  Ejecutando terraform validate..." -ForegroundColor Cyan
    $ValidateResult = terraform validate 2>&1
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✓ Validación de Terraform exitosa" -ForegroundColor Green
    } else {
        Write-Host "  ✗ Validación de Terraform falló:" -ForegroundColor Red
        Write-Host $ValidateResult -ForegroundColor Red
        $ErrorCount++
    }
} else {
    Write-Host "  ⚠ Terraform no está instalado, saltando validación" -ForegroundColor Yellow
}

Write-Host ""

# ============================================================================
# 6. Contar recursos S3 en el módulo
# ============================================================================

Write-Host "6. Contando recursos S3 en el módulo..." -ForegroundColor Yellow

$ModuleMainContent = Get-Content "modules/s3/main.tf" -Raw

$BucketCount = ([regex]::Matches($ModuleMainContent, 'resource\s+"aws_s3_bucket"')).Count
$VersioningCount = ([regex]::Matches($ModuleMainContent, 'resource\s+"aws_s3_bucket_versioning"')).Count
$EncryptionCount = ([regex]::Matches($ModuleMainContent, 'resource\s+"aws_s3_bucket_server_side_encryption_configuration"')).Count
$PublicAccessCount = ([regex]::Matches($ModuleMainContent, 'resource\s+"aws_s3_bucket_public_access_block"')).Count
$LifecycleCount = ([regex]::Matches($ModuleMainContent, 'resource\s+"aws_s3_bucket_lifecycle_configuration"')).Count
$LoggingCount = ([regex]::Matches($ModuleMainContent, 'resource\s+"aws_s3_bucket_logging"')).Count

Write-Host "  Buckets: $BucketCount (esperado: 5)" -ForegroundColor $(if ($BucketCount -eq 5) { "Green" } else { "Red" })
Write-Host "  Versioning: $VersioningCount (esperado: 5)" -ForegroundColor $(if ($VersioningCount -eq 5) { "Green" } else { "Red" })
Write-Host "  Encryption: $EncryptionCount (esperado: 5)" -ForegroundColor $(if ($EncryptionCount -eq 5) { "Green" } else { "Red" })
Write-Host "  Public Access Block: $PublicAccessCount (esperado: 5)" -ForegroundColor $(if ($PublicAccessCount -eq 5) { "Green" } else { "Red" })
Write-Host "  Lifecycle: $LifecycleCount (esperado: 4)" -ForegroundColor $(if ($LifecycleCount -eq 4) { "Green" } else { "Red" })
Write-Host "  Logging: $LoggingCount (esperado: 4)" -ForegroundColor $(if ($LoggingCount -eq 4) { "Green" } else { "Red" })

if ($BucketCount -ne 5) { $ErrorCount++ }
if ($VersioningCount -ne 5) { $ErrorCount++ }
if ($EncryptionCount -ne 5) { $ErrorCount++ }
if ($PublicAccessCount -ne 5) { $ErrorCount++ }
if ($LifecycleCount -ne 4) { $ErrorCount++ }
if ($LoggingCount -ne 4) { $ErrorCount++ }

Write-Host ""

# ============================================================================
# Resumen Final
# ============================================================================

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Resumen de Validación" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

if ($ErrorCount -eq 0) {
    Write-Host ""
    Write-Host "✓ VALIDACIÓN EXITOSA" -ForegroundColor Green
    Write-Host ""
    Write-Host "El módulo S3 está correctamente configurado." -ForegroundColor Green
    Write-Host ""
    Write-Host "Próximos pasos:" -ForegroundColor Cyan
    Write-Host "  1. Revisar el plan: terraform plan -var-file=`"terraform.tfvars.testing`"" -ForegroundColor White
    Write-Host "  2. Aplicar cambios: terraform apply -var-file=`"terraform.tfvars.testing`"" -ForegroundColor White
    Write-Host "  3. Verificar buckets: aws s3 ls | grep janis-cencosud" -ForegroundColor White
    Write-Host ""
    exit 0
} else {
    Write-Host ""
    Write-Host "✗ VALIDACIÓN FALLÓ" -ForegroundColor Red
    Write-Host ""
    Write-Host "Se encontraron $ErrorCount errores." -ForegroundColor Red
    Write-Host "Por favor, revisa los mensajes anteriores y corrige los problemas." -ForegroundColor Red
    Write-Host ""
    exit 1
}
