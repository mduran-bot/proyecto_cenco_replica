# Script para ejecutar tests de Iceberg en Windows
# Configura el entorno y ejecuta los tests

Write-Host "=== Ejecutando Tests de Iceberg ===" -ForegroundColor Green

# Verificar que estamos en el directorio correcto
if (-not (Test-Path "modules\iceberg_manager.py")) {
    Write-Host "Error: Debe ejecutar este script desde el directorio glue/" -ForegroundColor Red
    exit 1
}

# Verificar que el entorno virtual está activado
if (-not $env:VIRTUAL_ENV) {
    Write-Host "Advertencia: El entorno virtual no está activado" -ForegroundColor Yellow
    Write-Host "Activando venv..." -ForegroundColor Yellow
    & ".\venv\Scripts\Activate.ps1"
}

# Configurar HADOOP_HOME si no está configurado
if (-not $env:HADOOP_HOME) {
    $hadoopPath = Join-Path $PSScriptRoot "hadoop_home"
    $env:HADOOP_HOME = $hadoopPath
    Write-Host "HADOOP_HOME configurado en: $hadoopPath" -ForegroundColor Cyan
}

# Configurar Spark para Windows
$env:SPARK_LOCAL_HOSTNAME = "localhost"

Write-Host "`n=== Ejecutando Tests Básicos ===" -ForegroundColor Green
python -m pytest test_iceberg_local_simple.py -v

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n=== Tests Básicos PASARON ===" -ForegroundColor Green
    
    Write-Host "`n=== Ejecutando Property-Based Tests ===" -ForegroundColor Green
    Write-Host "Nota: Estos tests pueden tardar varios minutos..." -ForegroundColor Yellow
    
    # Ejecutar tests de property uno por uno
    Write-Host "`n--- Test: Iceberg Round Trip ---" -ForegroundColor Cyan
    python -m pytest tests/property/test_iceberg_roundtrip.py -v --tb=short
    
    Write-Host "`n--- Test: ACID Transactions ---" -ForegroundColor Cyan
    python -m pytest tests/property/test_iceberg_acid.py -v --tb=short
    
    Write-Host "`n--- Test: Time Travel ---" -ForegroundColor Cyan
    python -m pytest tests/property/test_iceberg_timetravel.py -v --tb=short
    
    Write-Host "`n=== Todos los tests completados ===" -ForegroundColor Green
} else {
    Write-Host "`n=== Tests Básicos FALLARON ===" -ForegroundColor Red
    Write-Host "Por favor, corrija los errores antes de ejecutar property tests" -ForegroundColor Red
}
