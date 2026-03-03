# Test Simple de Permisos AWS
param(
    [string]$Profile = "cencosud",
    [string]$Region = "us-east-1"
)

Write-Host "`n=== TEST DE PERMISOS AWS ===" -ForegroundColor Cyan
Write-Host "Perfil: $Profile | Region: $Region`n" -ForegroundColor Yellow

$results = @()

function Test-Perm {
    param([string]$Cmd, [string]$Name)
    try {
        $null = Invoke-Expression "aws $Cmd --profile $Profile --region $Region 2>&1"
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  [OK] $Name" -ForegroundColor Green
            $results += "[OK] $Name"
            return $true
        } else {
            Write-Host "  [NO] $Name" -ForegroundColor Red
            $results += "[NO] $Name"
            return $false
        }
    } catch {
        Write-Host "  [??] $Name" -ForegroundColor Yellow
        $results += "[??] $Name"
        return $false
    }
}

# S3
Write-Host "`n[S3]" -ForegroundColor Cyan
Test-Perm "s3api list-buckets" "S3: ListBuckets"
Test-Perm "s3api list-objects-v2 --bucket cencosud.desa.sm.peru.raw --max-items 1" "S3: ListObjects"

# Redshift
Write-Host "`n[REDSHIFT]" -ForegroundColor Cyan
Test-Perm "redshift describe-clusters --max-records 1" "Redshift: DescribeClusters"

# Glue
Write-Host "`n[GLUE]" -ForegroundColor Cyan
Test-Perm "glue get-databases --max-results 1" "Glue: GetDatabases"
Test-Perm "glue get-tables --database-name default --max-results 1" "Glue: GetTables"
Test-Perm "glue get-jobs --max-results 1" "Glue: GetJobs"

# Lambda
Write-Host "`n[LAMBDA]" -ForegroundColor Cyan
Test-Perm "lambda list-functions --max-items 1" "Lambda: ListFunctions"
Test-Perm "lambda get-function --function-name pe-janis-order-bi-sender-qa" "Lambda: GetFunction"

# IAM
Write-Host "`n[IAM]" -ForegroundColor Cyan
Test-Perm "iam list-roles --max-items 1" "IAM: ListRoles"
Test-Perm "iam get-role --role-name AWSServiceRoleForAmazonMWAA" "IAM: GetRole"

# VPC
Write-Host "`n[VPC/EC2]" -ForegroundColor Cyan
Test-Perm "ec2 describe-vpcs --max-results 1" "EC2: DescribeVpcs"
Test-Perm "ec2 describe-security-groups --max-results 1" "EC2: DescribeSecurityGroups"

# EventBridge
Write-Host "`n[EVENTBRIDGE]" -ForegroundColor Cyan
Test-Perm "events list-rules --max-results 1" "EventBridge: ListRules"

# MWAA
Write-Host "`n[MWAA]" -ForegroundColor Cyan
Test-Perm "mwaa list-environments" "MWAA: ListEnvironments"

# Secrets
Write-Host "`n[SECRETS]" -ForegroundColor Cyan
Test-Perm "secretsmanager list-secrets --max-results 1" "Secrets: ListSecrets"

# CloudWatch
Write-Host "`n[CLOUDWATCH]" -ForegroundColor Cyan
Test-Perm "logs describe-log-groups --max-items 1" "CloudWatch: DescribeLogGroups"

# Firehose
Write-Host "`n[FIREHOSE]" -ForegroundColor Cyan
Test-Perm "firehose list-delivery-streams" "Firehose: ListDeliveryStreams"

# API Gateway
Write-Host "`n[API GATEWAY]" -ForegroundColor Cyan
Test-Perm "apigateway get-rest-apis --limit 1" "APIGateway: GetRestApis"

Write-Host "`n=== RESUMEN ===" -ForegroundColor Cyan
Write-Host "Total pruebas: $($results.Count)" -ForegroundColor Yellow
Write-Host "Permitidas: $(($results | Where-Object { $_ -like '[OK]*' }).Count)" -ForegroundColor Green
Write-Host "Denegadas: $(($results | Where-Object { $_ -like '[NO]*' }).Count)" -ForegroundColor Red
Write-Host "Errores: $(($results | Where-Object { $_ -like '[??]*' }).Count)" -ForegroundColor Yellow

# Guardar resultados
$outputFile = "test-permisos-$(Get-Date -Format 'yyyyMMdd-HHmmss').txt"
$results | Out-File -FilePath $outputFile -Encoding UTF8
Write-Host "`nResultados guardados en: $outputFile" -ForegroundColor Cyan
