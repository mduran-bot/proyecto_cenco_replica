# ============================================================================
# Script para Preparar Proyecto para GitLab
# Janis-Cencosud AWS Infrastructure
# ============================================================================

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Preparando proyecto para GitLab" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Directorio base
$baseDir = Get-Location

# ============================================================================
# 1. Verificar archivos sensibles
# ============================================================================

Write-Host "1. Verificando archivos sensibles..." -ForegroundColor Yellow

$sensitiveFiles = @(
    "terraform/terraform.tfstate",
    "terraform/terraform.tfstate.backup",
    "terraform/*.tfplan",
    "terraform/terraform.tfvars"
)

$foundSensitive = $false
foreach ($pattern in $sensitiveFiles) {
    $files = Get-ChildItem -Path $pattern -ErrorAction SilentlyContinue
    if ($files) {
        Write-Host "  ⚠️  ADVERTENCIA: Encontrado archivo sensible: $($files.Name)" -ForegroundColor Red
        $foundSensitive = $true
    }
}

if (-not $foundSensitive) {
    Write-Host "  ✅ No se encontraron archivos sensibles" -ForegroundColor Green
}

Write-Host ""

# ============================================================================
# 2. Crear archivos .example
# ============================================================================

Write-Host "2. Creando archivos .example..." -ForegroundColor Yellow

# terraform.tfvars.example
if (Test-Path "terraform/terraform.tfvars.testing") {
    Write-Host "  📝 Creando terraform.tfvars.example..." -ForegroundColor Gray
    
    $content = Get-Content "terraform/terraform.tfvars.testing" -Raw
    
    # Reemplazar valores sensibles con placeholders
    $content = $content -replace 'aws_region\s*=\s*"[^"]*"', 'aws_region = "us-east-1"'
    $content = $content -replace 'environment\s*=\s*"[^"]*"', 'environment = "dev"'
    $content = $content -replace 'project_name\s*=\s*"[^"]*"', 'project_name = "janis-cencosud-integration"'
    $content = $content -replace 'cost_center\s*=\s*"[^"]*"', 'cost_center = "YOUR-COST-CENTER"'
    $content = $content -replace 'owner\s*=\s*"[^"]*"', 'owner = "your-team"'
    $content = $content -replace 'allowed_janis_ip_ranges\s*=\s*\[[^\]]*\]', 'allowed_janis_ip_ranges = ["0.0.0.0/0"]  # CAMBIAR: Agregar IPs reales de Janis'
    $content = $content -replace 'alarm_sns_topic_arn\s*=\s*"[^"]*"', 'alarm_sns_topic_arn = ""  # CAMBIAR: Agregar ARN del SNS topic'
    $content = $content -replace 'mwaa_environment_arn\s*=\s*"[^"]*"', 'mwaa_environment_arn = ""  # Dejar vacío hasta que MWAA esté desplegado'
    
    $content | Out-File "terraform/terraform.tfvars.example" -Encoding UTF8
    Write-Host "  ✅ Creado terraform/terraform.tfvars.example" -ForegroundColor Green
}

# Archivos .example por ambiente
$environments = @("dev", "staging", "prod")
foreach ($env in $environments) {
    $envDir = "terraform/environments/$env"
    if (Test-Path $envDir) {
        $tfvarsFile = "$envDir/$env.tfvars"
        $exampleFile = "$envDir/$env.tfvars.example"
        
        if (Test-Path $tfvarsFile) {
            Write-Host "  📝 Creando $env.tfvars.example..." -ForegroundColor Gray
            Copy-Item $tfvarsFile $exampleFile -Force
            Write-Host "  ✅ Creado $exampleFile" -ForegroundColor Green
        }
    }
}

Write-Host ""

# ============================================================================
# 3. Listar archivos a eliminar
# ============================================================================

Write-Host "3. Archivos que serán excluidos por .gitignore:" -ForegroundColor Yellow

$excludePatterns = @(
    "*.tfstate*",
    "*.tfplan",
    ".terraform/",
    "*.log",
    "*testing*.ps1",
    "*localstack*",
    "test/"
)

Write-Host "  Los siguientes tipos de archivos NO se subirán a GitLab:" -ForegroundColor Gray
foreach ($pattern in $excludePatterns) {
    Write-Host "    - $pattern" -ForegroundColor DarkGray
}

Write-Host ""

# ============================================================================
# 4. Verificar .gitignore
# ============================================================================

Write-Host "4. Verificando .gitignore..." -ForegroundColor Yellow

if (Test-Path "terraform/.gitignore") {
    Write-Host "  ✅ .gitignore existe en terraform/" -ForegroundColor Green
} else {
    Write-Host "  ⚠️  .gitignore NO existe en terraform/" -ForegroundColor Red
    Write-Host "  📝 Se debe crear .gitignore antes de subir a GitLab" -ForegroundColor Yellow
}

Write-Host ""

# ============================================================================
# 5. Estructura del proyecto para GitLab
# ============================================================================

Write-Host "5. Estructura del proyecto para GitLab:" -ForegroundColor Yellow
Write-Host ""

$structure = @"
terraform/
├── .gitignore                    ✅ Incluir
├── README.md                     ✅ Incluir
├── DEPLOYMENT_GUIDE.md           ✅ Incluir
├── MULTI_AZ_EXPANSION.md         ✅ Incluir
├── SINGLE_AZ_DEPLOYMENT.md       ✅ Incluir
├── REDSHIFT_INTEGRATION.md       ✅ Incluir
│
├── main.tf                       ✅ Incluir
├── variables.tf                  ✅ Incluir
├── outputs.tf                    ✅ Incluir
├── versions.tf                   ✅ Incluir
├── terraform.tfvars.example      ✅ Incluir
│
├── modules/                      ✅ Incluir TODO
│   ├── vpc/
│   ├── security-groups/
│   ├── vpc-endpoints/
│   ├── nacls/
│   ├── waf/
│   ├── eventbridge/
│   ├── monitoring/
│   └── tagging/
│
├── environments/                 ✅ Incluir
│   ├── dev/
│   ├── staging/
│   └── prod/
│
├── scripts/                      ✅ Incluir
│   ├── deploy.sh
│   ├── init-environment.sh
│   └── backup-state.sh
│
└── shared/                       ✅ Incluir
    ├── backend.tf
    ├── providers.tf
    └── variables.tf
"@

Write-Host $structure -ForegroundColor Gray
Write-Host ""

# ============================================================================
# 6. Checklist final
# ============================================================================

Write-Host "6. Checklist antes de subir a GitLab:" -ForegroundColor Yellow
Write-Host ""

$checklist = @(
    @{Item = ".gitignore configurado"; Path = "terraform/.gitignore"},
    @{Item = "terraform.tfvars.example creado"; Path = "terraform/terraform.tfvars.example"},
    @{Item = "README.md actualizado"; Path = "terraform/README.md"},
    @{Item = "No hay archivos .tfstate"; Path = "terraform/*.tfstate"},
    @{Item = "No hay archivos .tfplan"; Path = "terraform/*.tfplan"}
)

foreach ($check in $checklist) {
    if ($check.Path -like "*\**") {
        # Pattern con wildcard
        $exists = Get-ChildItem -Path $check.Path -ErrorAction SilentlyContinue
        if ($exists) {
            Write-Host "  ❌ $($check.Item)" -ForegroundColor Red
        } else {
            Write-Host "  ✅ $($check.Item)" -ForegroundColor Green
        }
    } else {
        # Path específico
        if (Test-Path $check.Path) {
            Write-Host "  ✅ $($check.Item)" -ForegroundColor Green
        } else {
            Write-Host "  ❌ $($check.Item)" -ForegroundColor Red
        }
    }
}

Write-Host ""

# ============================================================================
# 7. Comandos Git sugeridos
# ============================================================================

Write-Host "7. Comandos Git para subir a GitLab:" -ForegroundColor Yellow
Write-Host ""

$gitCommands = @"
# Inicializar repositorio (si no existe)
cd terraform/
git init

# Agregar remote de GitLab
git remote add origin https://gitlab.com/tu-org/janis-cencosud-infrastructure.git

# Agregar archivos (respetando .gitignore)
git add .

# Verificar qué se va a subir
git status

# Commit inicial
git commit -m "Initial commit: AWS infrastructure for Janis-Cencosud integration"

# Push a GitLab
git branch -M main
git push -u origin main
"@

Write-Host $gitCommands -ForegroundColor Cyan
Write-Host ""

# ============================================================================
# Resumen
# ============================================================================

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Preparación completada" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "📖 Ver GITLAB_PREPARATION.md para guía completa" -ForegroundColor Yellow
Write-Host "📖 Ver CONFIGURACION_CLIENTE.md para configuración requerida del cliente" -ForegroundColor Yellow
Write-Host ""
