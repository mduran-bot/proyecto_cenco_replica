# Script para instalar Java 11 (requerido por PySpark)

Write-Host "============================================================"
Write-Host "Instalador de Java 11 para PySpark"
Write-Host "============================================================"

# Verificar si Java ya está instalado
$javaInstalled = $false
try {
    $null = java -version 2>&1
    $javaInstalled = $true
} catch {
    $javaInstalled = $false
}

if ($javaInstalled) {
    Write-Host "`n✅ Java ya está instalado"
    java -version
    Write-Host "`n⚠️  NOTA: PySpark 4.x requiere Java 11 o superior"
    Write-Host "Si tienes Java 8, necesitas actualizar a Java 11"
    exit 0
}

Write-Host "`n⚠️  Java no está instalado. Procediendo con la instalación..."
Write-Host "`n📦 Instalando OpenJDK 11..."

# Intentar con winget
try {
    winget install Microsoft.OpenJDK.11 --silent --accept-package-agreements --accept-source-agreements
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "`n✅ Java 11 instalado correctamente"
        Write-Host "`n⚠️  IMPORTANTE: Cierra y vuelve a abrir PowerShell para que los cambios surtan efecto"
        Write-Host "`nLuego ejecuta: java -version"
    } else {
        Write-Host "`n❌ Error al instalar con winget"
        Write-Host "`n📝 Instalación manual requerida:"
        Write-Host "1. Ve a: https://adoptium.net/"
        Write-Host "2. Descarga OpenJDK 11 (LTS)"
        Write-Host "3. Ejecuta el instalador"
        Write-Host "4. Reinicia PowerShell"
    }
} catch {
    Write-Host "`n❌ Error al instalar con winget"
    Write-Host "`n📝 Instalación manual requerida:"
    Write-Host "1. Ve a: https://adoptium.net/"
    Write-Host "2. Descarga OpenJDK 11 (LTS)"
    Write-Host "3. Ejecuta el instalador"
    Write-Host "4. Reinicia PowerShell"
}
