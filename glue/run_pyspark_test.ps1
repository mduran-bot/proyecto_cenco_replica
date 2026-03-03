# Script para ejecutar el test básico de PySpark
# Activa el entorno virtual y ejecuta el test

Write-Host "Activando entorno virtual..." -ForegroundColor Cyan
& .\venv\Scripts\Activate.ps1

Write-Host "`nEjecutando test de PySpark..." -ForegroundColor Cyan
python test_pyspark_basic.py

Write-Host "`nPresiona cualquier tecla para salir..." -ForegroundColor Yellow
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
