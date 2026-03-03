# Script de Validación de Infraestructura AWS
# Este script valida toda la configuración de Terraform sin desplegar recursos

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Validación de Infraestructura AWS" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$ErrorActionPreference = "Continue"
$validationsPassed = 0
$validationsFailed = 0
$startLocation = Get-Location

# Función para validar un módulo
function Validate-Module {
    param(
        [string]$ModulePath,
        [string]$ModuleName
    )
    
    Write-Host "Validando: $ModuleName" -ForegroundColor Yellow
    Write-Host "Ruta: $ModulePath" -ForegroundColor Gray
    
    try {
        # Cambiar al directorio del módulo
        Set-Location $ModulePath
        
        # Inicializar Terraform
        Write-Host "  - Inicializando..." -ForegroundColor Gray
        $initOutput = terraform init -backend=false 2>&1
        
        if ($LASTEXITCODE -ne 0) {
            Write-Host "  X Error en inicialización" -ForegroundColor Red
            Write-Host $initOutput -ForegroundColor Red
            $script:validationsFailed++
            return $false
        }
        
        # Validar configuración
        Write-Host "  - Validando configuración..." -ForegroundColor Gray
        $validateOutput = terraform validate 2>&1
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  OK $ModuleName - VALIDO" -ForegroundColor Green
            $script:validationsPassed++
            return $true
        } else {
            Write-Host "  X $ModuleName - INVALIDO" -ForegroundColor Red
            Write-Host $validateOutput -ForegroundColor Red
            $script:validationsFailed++
            return $false
        }
    }
    catch {
        Write-Host "  X Error inesperado: $($_.Exception.Message)" -ForegroundColor Red
        $script:validationsFailed++
        return $false
    }
    finally {
        # Volver al directorio original
        Set-Location $startLocation
        Write-Host ""
    }
}

# Función para validar el plan completo
function Validate-CompletePlan {
    param(
        [string]$Environment = "dev"
    )
    
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "Validación del Plan Completo ($Environment)" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
    
    try {
        Set-Location "$startLocation\.."
        
        # Verificar si existe el archivo tfvars
        $tfvarsPath = "environments\$Environment\$Environment.tfvars"
        if (-not (Test-Path $tfvarsPath)) {
            Write-Host "X Archivo $tfvarsPath no encontrado" -ForegroundColor Red
            return $false
        }
        
        Write-Host "Inicializando Terraform en directorio principal..." -ForegroundColor Yellow
        $initOutput = terraform init -backend=false 2>&1
        
        if ($LASTEXITCODE -ne 0) {
            Write-Host "X Error en inicialización" -ForegroundColor Red
            Write-Host $initOutput -ForegroundColor Red
            return $false
        }
        
        Write-Host "OK Inicialización exitosa" -ForegroundColor Green
        Write-Host ""
        
        Write-Host "Ejecutando terraform plan..." -ForegroundColor Yellow
        Write-Host "Nota: Esto puede tomar varios minutos..." -ForegroundColor Gray
        Write-Host ""
        
        # Ejecutar plan (puede fallar si no hay credenciales, pero validará la sintaxis)
        $planOutput = terraform plan -var-file=$tfvarsPath -detailed-exitcode 2>&1
        $planExitCode = $LASTEXITCODE
        
        # Analizar resultado
        if ($planExitCode -eq 0) {
            Write-Host "OK Plan ejecutado exitosamente - No hay cambios" -ForegroundColor Green
            return $true
        }
        elseif ($planExitCode -eq 2) {
            Write-Host "OK Plan ejecutado exitosamente - Hay cambios planificados" -ForegroundColor Green
            Write-Host ""
            Write-Host "Resumen del Plan:" -ForegroundColor Cyan
            
            # Extraer resumen del plan
            $summary = $planOutput | Select-String -Pattern "Plan:" -Context 0,3
            if ($summary) {
                Write-Host $summary -ForegroundColor White
            }
            
            return $true
        }
        else {
            Write-Host "X Error en el plan" -ForegroundColor Red
            Write-Host ""
            
            # Mostrar solo errores relevantes
            $errors = $planOutput | Select-String -Pattern "Error:" -Context 2,2
            if ($errors) {
                Write-Host "Errores encontrados:" -ForegroundColor Red
                Write-Host $errors -ForegroundColor Red
            }
            
            return $false
        }
    }
    catch {
        Write-Host "X Error inesperado: $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
    finally {
        Set-Location $startLocation
    }
}

# Inicio de validaciones
Write-Host "Iniciando validación de módulos individuales..." -ForegroundColor Cyan
Write-Host ""

# Validar cada módulo
$modules = @(
    @{Path="../modules/vpc"; Name="VPC Module"},
    @{Path="../modules/security-groups"; Name="Security Groups Module"},
    @{Path="../modules/vpc-endpoints"; Name="VPC Endpoints Module"},
    @{Path="../modules/monitoring"; Name="Monitoring Module"},
    @{Path="../modules/eventbridge"; Name="EventBridge Module"},
    @{Path="../modules/waf"; Name="WAF Module"},
    @{Path="../modules/nacls"; Name="NACLs Module"},
    @{Path="../modules/tagging"; Name="Tagging Module"}
)

foreach ($module in $modules) {
    $modulePath = Join-Path $startLocation $module.Path
    if (Test-Path $modulePath) {
        Validate-Module -ModulePath $modulePath -ModuleName $module.Name
    } else {
        Write-Host "Advertencia: Módulo no encontrado: $($module.Path)" -ForegroundColor Yellow
        Write-Host ""
    }
}

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Resumen de Validación de Módulos" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Módulos válidos: $validationsPassed" -ForegroundColor Green
Write-Host "Módulos inválidos: $validationsFailed" -ForegroundColor $(if ($validationsFailed -eq 0) { "Green" } else { "Red" })
Write-Host ""

# Preguntar si desea validar el plan completo
Write-Host "Deseas validar el plan completo de infraestructura?" -ForegroundColor Yellow
Write-Host "Nota: Esto requiere que los módulos estén válidos" -ForegroundColor Gray
Write-Host ""
Write-Host "Opciones:" -ForegroundColor Cyan
Write-Host "  1 - Validar plan de desarrollo (dev)" -ForegroundColor White
Write-Host "  2 - Validar plan de staging" -ForegroundColor White
Write-Host "  3 - Validar plan de producción (prod)" -ForegroundColor White
Write-Host "  4 - Saltar validación de plan completo" -ForegroundColor White
Write-Host ""

$choice = Read-Host "Selecciona una opción (1-4)"

switch ($choice) {
    "1" {
        Write-Host ""
        $planResult = Validate-CompletePlan -Environment "dev"
        if ($planResult) {
            Write-Host ""
            Write-Host "OK Validación completa exitosa para ambiente DEV" -ForegroundColor Green
        }
    }
    "2" {
        Write-Host ""
        $planResult = Validate-CompletePlan -Environment "staging"
        if ($planResult) {
            Write-Host ""
            Write-Host "OK Validación completa exitosa para ambiente STAGING" -ForegroundColor Green
        }
    }
    "3" {
        Write-Host ""
        $planResult = Validate-CompletePlan -Environment "prod"
        if ($planResult) {
            Write-Host ""
            Write-Host "OK Validación completa exitosa para ambiente PROD" -ForegroundColor Green
        }
    }
    "4" {
        Write-Host ""
        Write-Host "Validación de plan completo omitida" -ForegroundColor Yellow
    }
    default {
        Write-Host ""
        Write-Host "Opción inválida. Validación de plan completo omitida" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Validación Completada" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

if ($validationsFailed -eq 0) {
    Write-Host "OK Todos los módulos son válidos" -ForegroundColor Green
    Write-Host ""
    Write-Host "Siguiente paso:" -ForegroundColor Cyan
    Write-Host "  - Revisa la guía VALIDATION_GUIDE.md para más detalles" -ForegroundColor White
    Write-Host "  - Cuando estés listo, ejecuta 'terraform apply' para desplegar" -ForegroundColor White
    Write-Host ""
    exit 0
} else {
    Write-Host "X Algunos módulos tienen errores" -ForegroundColor Red
    Write-Host ""
    Write-Host "Revisa los errores arriba y corrige los problemas" -ForegroundColor Yellow
    Write-Host ""
    exit 1
}
