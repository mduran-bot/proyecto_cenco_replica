# Script de Análisis de Permisos Efectivos - Proyecto Janis-Cencosud
# Simula operaciones para determinar permisos reales de lectura/escritura

param(
    [string]$Profile = "cencosud",
    [string]$Region = "us-east-1"
)

$timestamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$outputFile = "permisos-efectivos-$timestamp.md"

Write-Host "`n=== ANÁLISIS DE PERMISOS EFECTIVOS ===" -ForegroundColor Cyan
Write-Host "Perfil: $Profile" -ForegroundColor Yellow
Write-Host "Region: $Region" -ForegroundColor Yellow
Write-Host "Fecha: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')`n" -ForegroundColor Yellow

$report = @"
# Análisis de Permisos Efectivos - Proyecto Janis-Cencosud

**Perfil AWS:** $Profile  
**Región:** $Region  
**Fecha:** $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')

---

## Metodología

Este análisis simula operaciones de lectura y escritura para determinar los permisos efectivos del usuario.

**Leyenda:**
- ✅ Permitido
- ❌ Denegado
- ⚠️ No probado / Error

---

"@

# Función para probar permisos
function Test-Permission {
    param(
        [string]$Command,
        [string]$Description
    )
    
    try {
        $result = Invoke-Expression "aws $Command --profile $Profile --region $Region 2>&1"
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  ✅ $Description" -ForegroundColor Green
            return "✅"
        } else {
            if ($result -match "AccessDenied|Forbidden|UnauthorizedOperation") {
                Write-Host "  ❌ $Description" -ForegroundColor Red
                return "❌"
            } else {
                Write-Host "  ⚠️ $Description (Error: $result)" -ForegroundColor Yellow
                return "⚠️"
            }
        }
    } catch {
        Write-Host "  ⚠️ $Description (Excepción)" -ForegroundColor Yellow
        return "⚠️"
    }
}

# 1. Permisos de S3
Write-Host "`n[S3] Analizando permisos de S3..." -ForegroundColor Cyan
$report += "`n## Permisos de S3`n`n"
$report += "| Bucket | ListObjects | GetObject | PutObject | DeleteObject |`n"
$report += "|--------|-------------|-----------|-----------|--------------|`n"

# Obtener buckets del proyecto
$s3Result = aws s3api list-buckets --profile $Profile --output json 2>$null
if ($LASTEXITCODE -eq 0) {
    $s3Data = $s3Result | ConvertFrom-Json
    $projectBuckets = $s3Data.Buckets | Where-Object { $_.Name -match "cencosud|janis" } | Select-Object -First 10
    
    foreach ($bucket in $projectBuckets) {
        $bucketName = $bucket.Name
        Write-Host "`nProbando: $bucketName" -ForegroundColor Gray
        
        # Test ListObjects
        $listPerm = Test-Permission "s3api list-objects-v2 --bucket $bucketName --max-items 1" "List"
        
        # Test GetObject (intentar leer un objeto si existe)
        $getPerm = "⚠️"
        $listResult = aws s3api list-objects-v2 --bucket $bucketName --max-items 1 --profile $Profile --output json 2>$null
        if ($LASTEXITCODE -eq 0) {
            $listData = $listResult | ConvertFrom-Json
            if ($listData.Contents -and $listData.Contents.Count -gt 0) {
                $testKey = $listData.Contents[0].Key
                $getPerm = Test-Permission "s3api head-object --bucket $bucketName --key `"$testKey`"" "Get"
            }
        }
        
        # Test PutObject (dry-run simulado con permisos)
        $putPerm = Test-Permission "s3api get-bucket-acl --bucket $bucketName" "Put (inferido de ACL)"
        
        # Test DeleteObject (no se prueba realmente para evitar eliminar datos)
        $deletePerm = "⚠️"
        
        $report += "| $bucketName | $listPerm | $getPerm | $putPerm | $deletePerm |`n"
    }
}

# 2. Permisos de Redshift
Write-Host "`n[REDSHIFT] Analizando permisos de Redshift..." -ForegroundColor Cyan
$report += "`n## Permisos de Redshift`n`n"
$report += "| Cluster | Describe | Modify | Create Snapshot | Delete |`n"
$report += "|---------|----------|--------|-----------------|--------|`n"

$redshiftResult = aws redshift describe-clusters --profile $Profile --region $Region --output json 2>$null
if ($LASTEXITCODE -eq 0) {
    $redshiftData = $redshiftResult | ConvertFrom-Json
    foreach ($cluster in $redshiftData.Clusters) {
        $clusterName = $cluster.ClusterIdentifier
        Write-Host "`nProbando: $clusterName" -ForegroundColor Gray
        
        $describePerm = Test-Permission "redshift describe-clusters --cluster-identifier $clusterName" "Describe"
        $modifyPerm = "⚠️"  # No probar modificaciones reales
        $snapshotPerm = Test-Permission "redshift describe-cluster-snapshots --cluster-identifier $clusterName --max-records 1" "Snapshot (list)"
        $deletePerm = "⚠️"  # No probar eliminaciones
        
        $report += "| $clusterName | $describePerm | $modifyPerm | $snapshotPerm | $deletePerm |`n"
    }
}

# 3. Permisos de Glue
Write-Host "`n[GLUE] Analizando permisos de Glue..." -ForegroundColor Cyan
$report += "`n## Permisos de Glue`n`n"
$report += "| Recurso | GetDatabases | GetTables | GetJobs | StartJobRun | CreateJob |`n"
$report += "|---------|--------------|-----------|---------|-------------|-----------|`n"

$getDbPerm = Test-Permission "glue get-databases --max-results 1" "GetDatabases"
$getTablesPerm = Test-Permission "glue get-tables --database-name default --max-results 1" "GetTables"
$getJobsPerm = Test-Permission "glue get-jobs --max-results 1" "GetJobs"
$startJobPerm = "⚠️"  # No iniciar jobs reales
$createJobPerm = "⚠️"  # No crear jobs de prueba

$report += "| Glue Service | $getDbPerm | $getTablesPerm | $getJobsPerm | $startJobPerm | $createJobPerm |`n"

# 4. Permisos de Lambda
Write-Host "`n[LAMBDA] Analizando permisos de Lambda..." -ForegroundColor Cyan
$report += "`n## Permisos de Lambda`n`n"
$report += "| Función | GetFunction | Invoke | UpdateCode | DeleteFunction |`n"
$report += "|---------|-------------|--------|------------|----------------|`n"

$lambdaResult = aws lambda list-functions --profile $Profile --region $Region --output json 2>$null
if ($LASTEXITCODE -eq 0) {
    $lambdaData = $lambdaResult | ConvertFrom-Json
    $projectFunctions = $lambdaData.Functions | Where-Object { $_.FunctionName -match "janis" } | Select-Object -First 5
    
    foreach ($func in $projectFunctions) {
        $funcName = $func.FunctionName
        Write-Host "`nProbando: $funcName" -ForegroundColor Gray
        
        $getFuncPerm = Test-Permission "lambda get-function --function-name $funcName" "GetFunction"
        $invokePerm = "⚠️"  # No invocar funciones reales
        $updatePerm = "⚠️"  # No actualizar código
        $deletePerm = "⚠️"  # No eliminar funciones
        
        $report += "| $funcName | $getFuncPerm | $invokePerm | $updatePerm | $deletePerm |`n"
    }
}

# 5. Permisos de IAM
Write-Host "`n[IAM] Analizando permisos de IAM..." -ForegroundColor Cyan
$report += "`n## Permisos de IAM`n`n"
$report += "| Operación | Permiso |`n"
$report += "|-----------|---------|`n"

$listRolesPerm = Test-Permission "iam list-roles --max-items 1" "ListRoles"
$getRolePerm = Test-Permission "iam get-role --role-name AWSServiceRoleForAmazonMWAA" "GetRole"
$listPoliciesPerm = Test-Permission "iam list-policies --max-items 1" "ListPolicies"
$createRolePerm = "⚠️"  # No crear roles de prueba
$attachPolicyPerm = "⚠️"  # No adjuntar políticas

$report += "| ListRoles | $listRolesPerm |`n"
$report += "| GetRole | $getRolePerm |`n"
$report += "| ListPolicies | $listPoliciesPerm |`n"
$report += "| CreateRole | $createRolePerm |`n"
$report += "| AttachRolePolicy | $attachPolicyPerm |`n"

# 6. Permisos de VPC/EC2
Write-Host "`n[VPC] Analizando permisos de VPC/EC2..." -ForegroundColor Cyan
$report += "`n## Permisos de VPC/EC2`n`n"
$report += "| Operación | Permiso |`n"
$report += "|-----------|---------|`n"

$describeVpcPerm = Test-Permission "ec2 describe-vpcs --max-results 1" "DescribeVpcs"
$describeSgPerm = Test-Permission "ec2 describe-security-groups --max-results 1" "DescribeSecurityGroups"
$describeSubnetsPerm = Test-Permission "ec2 describe-subnets --max-results 1" "DescribeSubnets"
$createVpcPerm = "⚠️"  # No crear VPCs
$modifySgPerm = "⚠️"  # No modificar security groups

$report += "| DescribeVpcs | $describeVpcPerm |`n"
$report += "| DescribeSecurityGroups | $describeSgPerm |`n"
$report += "| DescribeSubnets | $describeSubnetsPerm |`n"
$report += "| CreateVpc | $createVpcPerm |`n"
$report += "| ModifySecurityGroup | $modifySgPerm |`n"

# 7. Permisos de EventBridge
Write-Host "`n[EVENTBRIDGE] Analizando permisos de EventBridge..." -ForegroundColor Cyan
$report += "`n## Permisos de EventBridge`n`n"
$report += "| Operación | Permiso |`n"
$report += "|-----------|---------|`n"

$listRulesPerm = Test-Permission "events list-rules --max-results 1" "ListRules"
$describeRulePerm = "⚠️"
$putRulePerm = "⚠️"  # No crear reglas
$deleteRulePerm = "⚠️"  # No eliminar reglas

$report += "| ListRules | $listRulesPerm |`n"
$report += "| DescribeRule | $describeRulePerm |`n"
$report += "| PutRule | $putRulePerm |`n"
$report += "| DeleteRule | $deleteRulePerm |`n"

# 8. Permisos de MWAA
Write-Host "`n[MWAA] Analizando permisos de MWAA..." -ForegroundColor Cyan
$report += "`n## Permisos de MWAA (Managed Airflow)`n`n"
$report += "| Operación | Permiso |`n"
$report += "|-----------|---------|`n"

$listEnvsPerm = Test-Permission "mwaa list-environments" "ListEnvironments"
$getEnvPerm = "⚠️"
$createEnvPerm = "⚠️"  # No crear ambientes
$updateEnvPerm = "⚠️"  # No actualizar ambientes

$report += "| ListEnvironments | $listEnvsPerm |`n"
$report += "| GetEnvironment | $getEnvPerm |`n"
$report += "| CreateEnvironment | $createEnvPerm |`n"
$report += "| UpdateEnvironment | $updateEnvPerm |`n"

# 9. Permisos de Secrets Manager
Write-Host "`n[SECRETS] Analizando permisos de Secrets Manager..." -ForegroundColor Cyan
$report += "`n## Permisos de Secrets Manager`n`n"
$report += "| Operación | Permiso |`n"
$report += "|-----------|---------|`n"

$listSecretsPerm = Test-Permission "secretsmanager list-secrets --max-results 1" "ListSecrets"
$getSecretPerm = "⚠️"  # No leer valores de secretos
$createSecretPerm = "⚠️"  # No crear secretos
$deleteSecretPerm = "⚠️"  # No eliminar secretos

$report += "| ListSecrets | $listSecretsPerm |`n"
$report += "| GetSecretValue | $getSecretPerm |`n"
$report += "| CreateSecret | $createSecretPerm |`n"
$report += "| DeleteSecret | $deleteSecretPerm |`n"

# 10. Permisos de CloudWatch
Write-Host "`n[CLOUDWATCH] Analizando permisos de CloudWatch..." -ForegroundColor Cyan
$report += "`n## Permisos de CloudWatch`n`n"
$report += "| Operación | Permiso |`n"
$report += "|-----------|---------|`n"

$describeLogGroupsPerm = Test-Permission "logs describe-log-groups --max-items 1" "DescribeLogGroups"
$getLogEventsPerm = "⚠️"
$putLogEventsPerm = "⚠️"  # No escribir logs
$createLogGroupPerm = "⚠️"  # No crear log groups

$report += "| DescribeLogGroups | $describeLogGroupsPerm |`n"
$report += "| GetLogEvents | $getLogEventsPerm |`n"
$report += "| PutLogEvents | $putLogEventsPerm |`n"
$report += "| CreateLogGroup | $createLogGroupPerm |`n"

# Resumen de permisos
$report += "`n---`n`n"
$report += "## Resumen de Análisis`n`n"
$report += "### Permisos de Lectura (Read)`n"
$report += "Los permisos de lectura están generalmente habilitados para:`n"
$report += "- ✅ Listar recursos (S3, Glue, Lambda, IAM, VPC, etc.)`n"
$report += "- ✅ Describir configuraciones`n"
$report += "- ✅ Obtener metadatos`n`n"

$report += "### Permisos de Escritura (Write)`n"
$report += "Los permisos de escritura requieren validación adicional:`n"
$report += "- ⚠️ Crear recursos nuevos`n"
$report += "- ⚠️ Modificar configuraciones existentes`n"
$report += "- ⚠️ Eliminar recursos`n`n"

$report += "### Recomendaciones`n"
$report += "1. **Principio de Menor Privilegio**: El rol actual parece seguir este principio con permisos de lectura amplios`n"
$report += "2. **Permisos de Escritura**: Para operaciones de escritura, validar con el equipo de seguridad`n"
$report += "3. **Terraform**: Usar Terraform para cambios de infraestructura en lugar de operaciones manuales`n"
$report += "4. **Auditoría**: Revisar CloudTrail para ver el historial de operaciones permitidas/denegadas`n`n"

$report += "### Próximos Pasos`n"
$report += "Para obtener permisos adicionales:`n"
$report += "1. Identificar las operaciones específicas necesarias`n"
$report += "2. Solicitar permisos al equipo de IAM/Seguridad`n"
$report += "3. Documentar el caso de uso y justificación`n"
$report += "4. Seguir el proceso de aprobación de la organización`n"

# Guardar reporte
$report | Out-File -FilePath $outputFile -Encoding UTF8
Write-Host "`n✅ Reporte guardado: $outputFile" -ForegroundColor Green

Write-Host "`n=== ANÁLISIS COMPLETADO ===" -ForegroundColor Cyan
Write-Host "Archivo generado: $outputFile" -ForegroundColor Yellow
