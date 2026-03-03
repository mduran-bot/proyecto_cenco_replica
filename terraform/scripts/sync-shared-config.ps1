# Sync Shared Configuration Script
#
# This script copies shared configuration files to each environment directory.
# Run this script whenever shared configuration files are updated.

$ErrorActionPreference = "Stop"

$sharedDir = "../shared"
$environments = @("dev", "staging", "prod")
$sharedFiles = @("backend.tf", "providers.tf", "variables.tf")

Write-Host "Syncing shared configuration files to environment directories..." -ForegroundColor Cyan

foreach ($env in $environments) {
    $envDir = "../environments/$env"
    
    Write-Host "`nProcessing environment: $env" -ForegroundColor Yellow
    
    foreach ($file in $sharedFiles) {
        $sourcePath = Join-Path $sharedDir $file
        $destPath = Join-Path $envDir $file
        
        if (Test-Path $sourcePath) {
            Copy-Item -Path $sourcePath -Destination $destPath -Force
            Write-Host "  ✓ Copied $file" -ForegroundColor Green
        } else {
            Write-Host "  ✗ Source file not found: $file" -ForegroundColor Red
        }
    }
}

Write-Host "`nSync completed!" -ForegroundColor Cyan
