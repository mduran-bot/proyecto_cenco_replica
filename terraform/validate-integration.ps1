# ============================================================================
# Terraform Integration Validation Script
# ============================================================================
# Este script valida que la integración de módulos esté completa y correcta
# antes de ejecutar terraform init/plan/apply
# ============================================================================

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Terraform Integration Validation" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$ErrorCount = 0
$WarningCount = 0

# ============================================================================
# 1. Verificar estructura de directorios
# ============================================================================

Write-Host "[1/8] Verificando estructura de directorios..." -ForegroundColor Yellow

$RequiredDirs = @(
    "modules/vpc",
    "modules/security-groups",
    "modules/vpc-endpoints",
    "modules/eventbridge",
    "modules/monitoring",
    "modules/s3",
    "modules/kinesis-firehose",
    "modules/lambda",
    "modules/api-gateway",
    "modules/glue",
    "modules/mwaa"
)

foreach ($dir in $RequiredDirs) {
    if (Test-Path $dir) {
        Write-Host "  ✓ $dir" -ForegroundColor Green
    } else {
        Write-Host "  ✗ $dir - NO ENCONTRADO" -ForegroundColor Red
        $ErrorCount++
    }
}

Write-Host ""

# ============================================================================
# 2. Verificar archivos principales
# ============================================================================

Write-Host "[2/8] Verificando archivos principales..." -ForegroundColor Yellow

$RequiredFiles = @(
    "main.tf",
    "variables.tf",
    "outputs.tf",
    "versions.tf",
    "terraform.tfvars.testing"
)

foreach ($file in $RequiredFiles) {
    if (Test-Path $file) {
        Write-Host "  ✓ $file" -ForegroundColor Green
    } else {
        Write-Host "  ✗ $file - NO ENCONTRADO" -ForegroundColor Red
        $ErrorCount++
    }
}

Write-Host ""

# ============================================================================
# 3. Verificar módulos tienen archivos requeridos
# ============================================================================

Write-Host "[3/8] Verificando archivos de módulos..." -ForegroundColor Yellow

$ModuleFiles = @("main.tf", "variables.tf", "outputs.tf")

foreach ($dir in $RequiredDirs) {
    if (Test-Path $dir) {
        $ModuleName = Split-Path $dir -Leaf
        $AllFilesExist = $true
        
        foreach ($file in $ModuleFiles) {
            $FilePath = Join-Path $dir $file
            if (-not (Test-Path $FilePath)) {
                Write-Host "  ✗ $dir/$file - NO ENCONTRADO" -ForegroundColor Red
                $ErrorCount++
                $AllFilesExist = $false
            }
        }
        
        if ($AllFilesExist) {
            Write-Host "  ✓ $ModuleName - Completo" -ForegroundColor Green
        }
    }
}

Write-Host ""

# ============================================================================
# 4. Verificar variables requeridas en terraform.tfvars.testing
# ============================================================================

Write-Host "[4/8] Verificando variables en terraform.tfvars.testing..." -ForegroundColor Yellow

$RequiredVars = @(
    "aws_region",
    "aws_account_id",
    "vpc_cidr",
    "environment",
    "cost_center",
    "firehose_buffering_size",
    "lambda_runtime",
    "create_lambda_webhook_processor",
    "create_api_gateway",
    "glue_worker_type",
    "create_mwaa_environment"
)

$TfvarsContent = Get-Content "terraform.tfvars.testing" -Raw

foreach ($var in $RequiredVars) {
    if ($TfvarsContent -match "$var\s*=") {
        Write-Host "  ✓ $var" -ForegroundColor Green
    } else {
        Write-Host "  ✗ $var - NO DEFINIDA" -ForegroundColor Red
        $ErrorCount++
    }
}

Write-Host ""

# ============================================================================
# 5. Verificar sintaxis de Terraform
# ============================================================================

Write-Host "[5/8] Verificando sintaxis de Terraform..." -ForegroundColor Yellow

# Verificar si terraform está instalado
$TerraformInstalled = Get-Command terraform -ErrorAction SilentlyContinue

if ($TerraformInstalled) {
    Write-Host "  ✓ Terraform instalado: $($TerraformInstalled.Version)" -ForegroundColor Green
    
    # Formatear código
    Write-Host "  → Formateando código..." -ForegroundColor Cyan
    terraform fmt -recursive | Out-Null
    
    # Validar sintaxis (sin init)
    Write-Host "  → Validando sintaxis..." -ForegroundColor Cyan
    $ValidateResult = terraform validate -json 2>&1 | ConvertFrom-Json
    
    if ($ValidateResult.valid -eq $true) {
        Write-Host "  ✓ Sintaxis válida" -ForegroundColor Green
    } else {
        Write-Host "  ✗ Errores de sintaxis encontrados" -ForegroundColor Red
        $ValidateResult.diagnostics | ForEach-Object {
            Write-Host "    - $($_.summary): $($_.detail)" -ForegroundColor Red
        }
        $ErrorCount++
    }
} else {
    Write-Host "  ⚠ Terraform no instalado - Saltando validación de sintaxis" -ForegroundColor Yellow
    $WarningCount++
}

Write-Host ""

# ============================================================================
# 6. Verificar configuración de módulos en main.tf
# ============================================================================

Write-Host "[6/8] Verificando declaración de módulos en main.tf..." -ForegroundColor Yellow

$MainTfContent = Get-Content "main.tf" -Raw

$RequiredModules = @(
    "module `"vpc`"",
    "module `"security_groups`"",
    "module `"vpc_endpoints`"",
    "module `"eventbridge`"",
    "module `"monitoring`"",
    "module `"s3`"",
    "module `"kinesis_firehose`"",
    "module `"lambda`"",
    "module `"api_gateway`"",
    "module `"glue`"",
    "module `"mwaa`""
)

foreach ($module in $RequiredModules) {
    if ($MainTfContent -match [regex]::Escape($module)) {
        Write-Host "  ✓ $module" -ForegroundColor Green
    } else {
        Write-Host "  ✗ $module - NO DECLARADO" -ForegroundColor Red
        $ErrorCount++
    }
}

Write-Host ""

# ============================================================================
# 7. Verificar outputs en outputs.tf
# ============================================================================

Write-Host "[7/8] Verificando outputs en outputs.tf..." -ForegroundColor Yellow

$OutputsTfContent = Get-Content "outputs.tf" -Raw

$RequiredOutputs = @(
    "vpc_id",
    "bronze_bucket_name",
    "silver_bucket_name",
    "gold_bucket_name",
    "firehose_orders_stream_name",
    "webhook_processor_function_name",
    "api_gateway_id",
    "glue_bronze_database_name",
    "mwaa_environment_arn"
)

foreach ($output in $RequiredOutputs) {
    if ($OutputsTfContent -match "output `"$output`"") {
        Write-Host "  ✓ $output" -ForegroundColor Green
    } else {
        Write-Host "  ✗ $output - NO DEFINIDO" -ForegroundColor Red
        $ErrorCount++
    }
}

Write-Host ""

# ============================================================================
# 8. Verificar configuración de testing
# ============================================================================

Write-Host "[8/8] Verificando configuración de testing..." -ForegroundColor Yellow

# Verificar que componentes costosos estén deshabilitados
$TestingChecks = @{
    "create_mwaa_environment = false" = "MWAA deshabilitado (ahorro ~$300/mes)"
    "enable_multi_az = false" = "Multi-AZ deshabilitado (ahorro ~$32/mes)"
    "enable_s3_endpoint = false" = "VPC Endpoints deshabilitados (ahorro ~$7/mes)"
}

foreach ($check in $TestingChecks.Keys) {
    if ($TfvarsContent -match [regex]::Escape($check)) {
        Write-Host "  ✓ $($TestingChecks[$check])" -ForegroundColor Green
    } else {
        Write-Host "  ⚠ $($TestingChecks[$check]) - NO CONFIGURADO" -ForegroundColor Yellow
        $WarningCount++
    }
}

# Verificar que Lambda/API Gateway estén deshabilitados (sin código aún)
$CodeChecks = @{
    "create_lambda_webhook_processor = false" = "Lambda webhook-processor deshabilitado (sin código)"
    "create_api_gateway = false" = "API Gateway deshabilitado (sin Lambda)"
    "create_glue_bronze_to_silver_job = false" = "Glue jobs deshabilitados (sin scripts)"
}

foreach ($check in $CodeChecks.Keys) {
    if ($TfvarsContent -match [regex]::Escape($check)) {
        Write-Host "  ✓ $($CodeChecks[$check])" -ForegroundColor Green
    } else {
        Write-Host "  ⚠ $($CodeChecks[$check]) - PUEDE FALLAR SIN CÓDIGO" -ForegroundColor Yellow
        $WarningCount++
    }
}

foreach ($check in $CodeChecks.Keys) {
    if ($TfvarsContent -match [regex]::Escape($check)) {
        Write-Host "  ✓ $($CodeChecks[$check])" -ForegroundColor Green
    } else {
        Write-Host "  ⚠ $($CodeChecks[$check]) - PUEDE FALLAR SIN CÓDIGO" -ForegroundColor Yellow
        $WarningCount++
    }
}

Write-Host ""

# ============================================================================
# Resumen
# ============================================================================

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Resumen de Validación" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

if ($ErrorCount -eq 0 -and $WarningCount -eq 0) {
    Write-Host "✓ VALIDACIÓN EXITOSA" -ForegroundColor Green
    Write-Host "  No se encontraron errores ni advertencias" -ForegroundColor Green
    Write-Host ""
    Write-Host "Próximos pasos:" -ForegroundColor Cyan
    Write-Host "  1. terraform init" -ForegroundColor White
    Write-Host "  2. terraform plan -var-file=`"terraform.tfvars.testing`" -out=testing.tfplan" -ForegroundColor White
    Write-Host "  3. terraform apply testing.tfplan" -ForegroundColor White
} elseif ($ErrorCount -eq 0) {
    Write-Host "⚠ VALIDACIÓN CON ADVERTENCIAS" -ForegroundColor Yellow
    Write-Host "  Errores: $ErrorCount" -ForegroundColor Green
    Write-Host "  Advertencias: $WarningCount" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Puedes continuar con el deployment, pero revisa las advertencias." -ForegroundColor Yellow
} else {
    Write-Host "✗ VALIDACIÓN FALLIDA" -ForegroundColor Red
    Write-Host "  Errores: $ErrorCount" -ForegroundColor Red
    Write-Host "  Advertencias: $WarningCount" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Corrige los errores antes de continuar." -ForegroundColor Red
    exit 1
}

Write-Host ""
