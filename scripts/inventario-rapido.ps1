# Script de Inventario Rápido - Proyecto Janis-Cencosud
# Genera un resumen rápido de recursos AWS

param(
    [string]$Profile = "cencosud",
    [string]$Region = "us-east-1"
)

Write-Host "`n=== INVENTARIO RAPIDO AWS - PROYECTO JANIS-CENCOSUD ===" -ForegroundColor Cyan
Write-Host "Perfil: $Profile | Region: $Region`n" -ForegroundColor Yellow

function Get-ResourceCount {
    param([string]$Command, [string]$Name)
    try {
        $result = aws $Command --profile $Profile --region $Region --output json 2>$null | ConvertFrom-Json
        return $result
    } catch {
        return $null
    }
}

# S3 Buckets
Write-Host "[S3] S3 Buckets:" -ForegroundColor Green
$s3 = Get-ResourceCount "s3api list-buckets" "S3"
if ($s3) {
    $filtered = $s3.Buckets | Where-Object { $_.Name -like "*cencosud*" -or $_.Name -like "*janis*" }
    foreach ($bucket in $filtered) {
        Write-Host "   + $($bucket.Name)" -ForegroundColor White
    }
    Write-Host "   Total: $($filtered.Count)`n" -ForegroundColor Cyan
}

# Redshift
Write-Host "[REDSHIFT] Redshift Clusters:" -ForegroundColor Green
$redshift = Get-ResourceCount "redshift describe-clusters" "Redshift"
if ($redshift -and $redshift.Clusters) {
    foreach ($cluster in $redshift.Clusters) {
        Write-Host "   + $($cluster.ClusterIdentifier) [$($cluster.ClusterStatus)]" -ForegroundColor White
    }
    Write-Host "   Total: $($redshift.Clusters.Count)`n" -ForegroundColor Cyan
}

# Glue Databases
Write-Host "[GLUE] Glue Databases:" -ForegroundColor Green
$glueDb = Get-ResourceCount "glue get-databases" "Glue"
if ($glueDb -and $glueDb.DatabaseList) {
    foreach ($db in $glueDb.DatabaseList) {
        Write-Host "   + $($db.Name)" -ForegroundColor White
    }
    Write-Host "   Total: $($glueDb.DatabaseList.Count)`n" -ForegroundColor Cyan
}

# Glue Jobs
Write-Host "[GLUE] Glue Jobs:" -ForegroundColor Green
$glueJobs = Get-ResourceCount "glue get-jobs" "Glue Jobs"
if ($glueJobs -and $glueJobs.Jobs) {
    foreach ($job in $glueJobs.Jobs) {
        Write-Host "   + $($job.Name)" -ForegroundColor White
    }
    Write-Host "   Total: $($glueJobs.Jobs.Count)`n" -ForegroundColor Cyan
}

# Lambda Functions
Write-Host "[LAMBDA] Lambda Functions:" -ForegroundColor Green
$lambda = Get-ResourceCount "lambda list-functions" "Lambda"
if ($lambda -and $lambda.Functions) {
    $filtered = $lambda.Functions | Where-Object { $_.FunctionName -like "*cencosud*" -or $_.FunctionName -like "*janis*" }
    foreach ($func in $filtered) {
        Write-Host "   + $($func.FunctionName) [$($func.Runtime)]" -ForegroundColor White
    }
    Write-Host "   Total: $($filtered.Count)`n" -ForegroundColor Cyan
}

# API Gateway
Write-Host "[API] API Gateway:" -ForegroundColor Green
$api = Get-ResourceCount "apigateway get-rest-apis" "API Gateway"
if ($api -and $api.items) {
    foreach ($item in $api.items) {
        Write-Host "   + $($item.name)" -ForegroundColor White
    }
    Write-Host "   Total: $($api.items.Count)`n" -ForegroundColor Cyan
}

# Kinesis Firehose
Write-Host "[KINESIS] Kinesis Firehose:" -ForegroundColor Green
$firehose = Get-ResourceCount "firehose list-delivery-streams" "Firehose"
if ($firehose -and $firehose.DeliveryStreamNames) {
    foreach ($stream in $firehose.DeliveryStreamNames) {
        Write-Host "   + $stream" -ForegroundColor White
    }
    Write-Host "   Total: $($firehose.DeliveryStreamNames.Count)`n" -ForegroundColor Cyan
}

# VPC
Write-Host "[VPC] VPCs:" -ForegroundColor Green
$vpc = Get-ResourceCount "ec2 describe-vpcs" "VPC"
if ($vpc -and $vpc.Vpcs) {
    foreach ($v in $vpc.Vpcs) {
        $name = ($v.Tags | Where-Object { $_.Key -eq "Name" }).Value
        if ($name -like "*cencosud*" -or $name -like "*janis*") {
            Write-Host "   + $name ($($v.VpcId))" -ForegroundColor White
        }
    }
}

# IAM Roles
Write-Host "`n[IAM] IAM Roles (proyecto):" -ForegroundColor Green
$roles = Get-ResourceCount "iam list-roles" "IAM"
if ($roles -and $roles.Roles) {
    $filtered = $roles.Roles | Where-Object { 
        $_.RoleName -like "*cencosud*" -or 
        $_.RoleName -like "*janis*" -or 
        $_.RoleName -like "*glue*" -or 
        $_.RoleName -like "*lambda*"
    }
    foreach ($role in $filtered) {
        Write-Host "   + $($role.RoleName)" -ForegroundColor White
    }
    Write-Host "   Total: $($filtered.Count)`n" -ForegroundColor Cyan
}

# EventBridge
Write-Host "[EVENTBRIDGE] EventBridge Rules:" -ForegroundColor Green
$events = Get-ResourceCount "events list-rules" "EventBridge"
if ($events -and $events.Rules) {
    $filtered = $events.Rules | Where-Object { $_.Name -like "*cencosud*" -or $_.Name -like "*janis*" }
    foreach ($rule in $filtered) {
        Write-Host "   + $($rule.Name) [$($rule.State)]" -ForegroundColor White
    }
    Write-Host "   Total: $($filtered.Count)`n" -ForegroundColor Cyan
}

# MWAA
Write-Host "[MWAA] MWAA (Airflow):" -ForegroundColor Green
$mwaa = Get-ResourceCount "mwaa list-environments" "MWAA"
if ($mwaa -and $mwaa.Environments) {
    foreach ($env in $mwaa.Environments) {
        Write-Host "   + $env" -ForegroundColor White
    }
    Write-Host "   Total: $($mwaa.Environments.Count)`n" -ForegroundColor Cyan
}

# Secrets Manager
Write-Host "[SECRETS] Secrets Manager:" -ForegroundColor Green
$secrets = Get-ResourceCount "secretsmanager list-secrets" "Secrets"
if ($secrets -and $secrets.SecretList) {
    $filtered = $secrets.SecretList | Where-Object { $_.Name -like "*cencosud*" -or $_.Name -like "*janis*" }
    foreach ($secret in $filtered) {
        Write-Host "   + $($secret.Name)" -ForegroundColor White
    }
    Write-Host "   Total: $($filtered.Count)`n" -ForegroundColor Cyan
}

Write-Host "=== FIN DEL INVENTARIO ===" -ForegroundColor Cyan
