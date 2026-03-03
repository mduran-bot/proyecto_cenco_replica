# Script PowerShell para usar Terraform con LocalStack

param(
    [Parameter(Mandatory=$true)]
    [ValidateSet('init', 'plan', 'apply', 'destroy', 'output')]
    [string]$Action
)

$ErrorActionPreference = "Stop"

Write-Host "🔧 Terraform con LocalStack - Acción: $Action" -ForegroundColor Cyan

# Cambiar al directorio de LocalStack
Set-Location "terraform/environments/localstack"

switch ($Action) {
    'init' {
        Write-Host "📦 Inicializando Terraform..." -ForegroundColor Yellow
        terraform init
    }
    'plan' {
        Write-Host "📋 Generando plan de ejecución..." -ForegroundColor Yellow
        terraform plan -var-file="localstack.tfvars"
    }
    'apply' {
        Write-Host "🚀 Aplicando configuración..." -ForegroundColor Yellow
        terraform apply -var-file="localstack.tfvars" -auto-approve
    }
    'destroy' {
        Write-Host "💣 Destruyendo infraestructura..." -ForegroundColor Red
        terraform destroy -var-file="localstack.tfvars" -auto-approve
    }
    'output' {
        Write-Host "📤 Mostrando outputs..." -ForegroundColor Yellow
        terraform output
    }
}

Write-Host "✅ Completado" -ForegroundColor Green

# Volver al directorio raíz
Set-Location "../../.."
