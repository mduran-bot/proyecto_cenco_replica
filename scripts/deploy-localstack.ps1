# Script para desplegar infraestructura en LocalStack
# Uso: .\scripts\deploy-localstack.ps1 [-Action <init|plan|apply|destroy|output>]

param(
    [Parameter(Mandatory=$false)]
    [ValidateSet("init", "plan", "apply", "destroy", "output", "show")]
    [string]$Action = "plan"
)

$ErrorActionPreference = "Stop"

Write-Host "🚀 Janis-Cencosud LocalStack Deployment" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Verificar que LocalStack está corriendo
Write-Host "🔍 Verificando LocalStack..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:4566/_localstack/health" -UseBasicParsing -TimeoutSec 5
    Write-Host "✅ LocalStack está corriendo" -ForegroundColor Green
} catch {
    Write-Host "❌ Error: LocalStack no está corriendo" -ForegroundColor Red
    Write-Host "   Inicia LocalStack con: docker-compose -f docker-compose.localstack.yml up -d" -ForegroundColor Yellow
    exit 1
}

# Cambiar al directorio de Terraform
$terraformDir = Join-Path $PSScriptRoot ".." "terraform"
Set-Location $terraformDir

Write-Host ""
Write-Host "📁 Directorio de trabajo: $terraformDir" -ForegroundColor Cyan
Write-Host ""

# Ejecutar acción de Terraform
switch ($Action) {
    "init" {
        Write-Host "🔧 Inicializando Terraform..." -ForegroundColor Yellow
        terraform init
    }
    "plan" {
        Write-Host "📋 Generando plan de Terraform..." -ForegroundColor Yellow
        terraform plan -var-file="localstack.tfvars"
    }
    "apply" {
        Write-Host "🚀 Aplicando configuración de Terraform..." -ForegroundColor Yellow
        Write-Host "⚠️  Esto creará recursos en LocalStack" -ForegroundColor Yellow
        Write-Host ""
        terraform apply -var-file="localstack.tfvars"
    }
    "destroy" {
        Write-Host "🗑️  Destruyendo recursos de LocalStack..." -ForegroundColor Yellow
        terraform destroy -var-file="localstack.tfvars"
    }
    "output" {
        Write-Host "📤 Mostrando outputs de Terraform..." -ForegroundColor Yellow
        terraform output
    }
    "show" {
        Write-Host "📊 Mostrando estado actual..." -ForegroundColor Yellow
        terraform show
    }
}

Write-Host ""
Write-Host "✅ Acción '$Action' completada" -ForegroundColor Green
Write-Host ""
Write-Host "💡 Comandos útiles:" -ForegroundColor Cyan
Write-Host "   Ver VPCs:     aws --endpoint-url=http://localhost:4566 ec2 describe-vpcs" -ForegroundColor Gray
Write-Host "   Ver Subnets:  aws --endpoint-url=http://localhost:4566 ec2 describe-subnets" -ForegroundColor Gray
Write-Host "   Ver SGs:      aws --endpoint-url=http://localhost:4566 ec2 describe-security-groups" -ForegroundColor Gray
Write-Host ""
