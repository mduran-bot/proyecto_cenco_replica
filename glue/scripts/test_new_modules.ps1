# Script para probar los módulos integrados de Max
# Fase 1.1: Validación de integración

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "Testing Módulos Integrados de Max" -ForegroundColor Cyan
Write-Host "Fase 1.1: JSONFlattener, DataCleaner, DuplicateDetector, ConflictResolver" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

# Cambiar al directorio glue
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location (Join-Path $scriptPath "..")

Write-Host "📦 Instalando dependencias..." -ForegroundColor Yellow
pip install -q pytest pyspark

Write-Host ""
Write-Host "🧪 Ejecutando tests unitarios..." -ForegroundColor Yellow
Write-Host ""

$allPassed = $true

# Test 1: JSONFlattener
Write-Host "1️⃣  Testing JSONFlattener..." -ForegroundColor White
pytest tests/unit/test_json_flattener.py -v --tb=short
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ JSONFlattener: PASSED" -ForegroundColor Green
} else {
    Write-Host "❌ JSONFlattener: FAILED" -ForegroundColor Red
    $allPassed = $false
}

Write-Host ""

# Test 2: DataCleaner
Write-Host "2️⃣  Testing DataCleaner..." -ForegroundColor White
pytest tests/unit/test_data_cleaner.py -v --tb=short
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ DataCleaner: PASSED" -ForegroundColor Green
} else {
    Write-Host "❌ DataCleaner: FAILED" -ForegroundColor Red
    $allPassed = $false
}

Write-Host ""

# Test 3: DuplicateDetector
Write-Host "3️⃣  Testing DuplicateDetector..." -ForegroundColor White
pytest tests/unit/test_duplicate_detector.py -v --tb=short
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ DuplicateDetector: PASSED" -ForegroundColor Green
} else {
    Write-Host "❌ DuplicateDetector: FAILED" -ForegroundColor Red
    $allPassed = $false
}

Write-Host ""

# Test 4: ConflictResolver
Write-Host "4️⃣  Testing ConflictResolver..." -ForegroundColor White
pytest tests/unit/test_conflict_resolver.py -v --tb=short
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ ConflictResolver: PASSED" -ForegroundColor Green
} else {
    Write-Host "❌ ConflictResolver: FAILED" -ForegroundColor Red
    $allPassed = $false
}

Write-Host ""

if ($allPassed) {
    Write-Host "=========================================" -ForegroundColor Green
    Write-Host "✅ TODOS LOS TESTS PASARON" -ForegroundColor Green
    Write-Host "=========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Módulos integrados exitosamente:" -ForegroundColor Cyan
    Write-Host "  - JSONFlattener" -ForegroundColor White
    Write-Host "  - DataCleaner" -ForegroundColor White
    Write-Host "  - DuplicateDetector" -ForegroundColor White
    Write-Host "  - ConflictResolver" -ForegroundColor White
    Write-Host ""
    Write-Host "Próximo paso: Fase 1.2 - Fusionar módulos duplicados" -ForegroundColor Yellow
    Write-Host ""
} else {
    Write-Host "=========================================" -ForegroundColor Red
    Write-Host "❌ ALGUNOS TESTS FALLARON" -ForegroundColor Red
    Write-Host "=========================================" -ForegroundColor Red
    Write-Host ""
    Write-Host "Por favor revisa los errores arriba." -ForegroundColor Yellow
    Write-Host ""
    exit 1
}
