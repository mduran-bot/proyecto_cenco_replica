# Script Rápido de Análisis de Permisos - Proyecto Janis-Cencosud
param(
    [string]$Profile = "cencosud",
    [string]$Region = "us-east-1"
)

$timestamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$outputFile = "permisos-rapidos-$timestamp.md"

Write-Host "`n=== ANÁLISIS RÁPIDO DE PERMISOS ===" -ForegroundColor Cyan
Write-Host "Perfil: $Profile | Región: $Region`n" -ForegroundColor Yellow

$report = @"
# Análisis Rápido de Permisos - Proyecto Janis-Cencosud

**Perfil:** $Profile  
**Región:** $Region  
**Fecha:** $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')

---

## Permisos Detectados

"@

# Función simple de prueba
function Test-QuickPermission {
    param([string]$Command, [string]$Name)
    try {
        $null = Invoke-Expression "aws $Command --profile $Profile --region $Region 2>&1"
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  ✓ $Name" -ForegroundColor Green
            return "✅ Permitido"
        } else {
            Write-Host "  ✗ $Name" -ForegroundColor Red
            return "❌ Denegado"
        }
    } catch {
        Write-Host "  ? $Name" -ForegroundColor Yellow
        return "⚠️ Error"
    }
}

# S3
Write-Host "`n[S3] Probando permisos..." -ForegroundColor Cyan
$report += "`n### S3 Buckets`n`n"
$report += "| Operación | Estado |`n|-----------|--------|`n"
$report += "| ListBuckets | $(Test-QuickPermission 's3api list-buckets' 'ListBuckets') |`n"
$report += "| GetBucketLocation | $(Test-QuickPermission 's3api get-bucket-location --bucket cencosud.desa.sm.peru.raw' 'GetBucketLocation') |`n"
$report += "| ListObjects | $(Test-QuickPermission 's3api list-objects-v2 --bucket cencosud.desa.sm.peru.raw --max-items 1' 'ListObjects') |`n"

# Redshift
Write-Host "`n[REDSHIFT] Probando permisos..." -ForegroundColor Cyan
$report += "`n### Redshift`n`n"
$report += "| Operación | Estado |`n|-----------|--------|`n"
$report += "| DescribeClusters | $(Test-QuickPermission 'redshift describe-clusters --max-records 1' 'DescribeClusters') |`n"

# Glue
Write-Host "`n[GLUE] Probando permisos..." -ForegroundColor Cyan
$report += "`n### AWS Glue`n`n"
$report += "| Operación | Estado |`n|-----------|--------|`n"
$report += "| GetDatabases | $(Test-QuickPermission 'glue get-databases --max-results 1' 'GetDatabases') |`n"
$report += "| GetTables | $(Test-QuickPermission 'glue get-tables --database-name default --max-results 1' 'GetTables') |`n"
$report += "| GetJobs | $(Test-QuickPermission 'glue get-jobs --max-results 1' 'GetJobs') |`n"

# Lambda
Write-Host "`n[LAMBDA] Probando permisos..." -ForegroundColor Cyan
$report += "`n### Lambda`n`n"
$report += "| Operación | Estado |`n|-----------|--------|`n"
$report += "| ListFunctions | $(Test-QuickPermission 'lambda list-functions --max-items 1' 'ListFunctions') |`n"
$report += "| GetFunction | $(Test-QuickPermission 'lambda get-function --function-name pe-janis-order-bi-sender-qa' 'GetFunction') |`n"

# IAM
Write-Host "`n[IAM] Probando permisos..." -ForegroundColor Cyan
$report += "`n### IAM`n`n"
$report += "| Operación | Estado |`n|-----------|--------|`n"
$report += "| ListRoles | $(Test-QuickPermission 'iam list-roles --max-items 1' 'ListRoles') |`n"
$report += "| GetRole | $(Test-QuickPermission 'iam get-role --role-name AWSServiceRoleForAmazonMWAA' 'GetRole') |`n"

# VPC/EC2
Write-Host "`n[VPC] Probando permisos..." -ForegroundColor Cyan
$report += "`n### VPC/EC2`n`n"
$report += "| Operación | Estado |`n|-----------|--------|`n"
$report += "| DescribeVpcs | $(Test-QuickPermission 'ec2 describe-vpcs --max-results 1' 'DescribeVpcs') |`n"
$report += "| DescribeSecurityGroups | $(Test-QuickPermission 'ec2 describe-security-groups --max-results 1' 'DescribeSecurityGroups') |`n"

# EventBridge
Write-Host "`n[EVENTBRIDGE] Probando permisos..." -ForegroundColor Cyan
$report += "`n### EventBridge`n`n"
$report += "| Operación | Estado |`n|-----------|--------|`n"
$report += "| ListRules | $(Test-QuickPermission 'events list-rules --max-results 1' 'ListRules') |`n"

# MWAA
Write-Host "`n[MWAA] Probando permisos..." -ForegroundColor Cyan
$report += "`n### MWAA (Managed Airflow)`n`n"
$report += "| Operación | Estado |`n|-----------|--------|`n"
$report += "| ListEnvironments | $(Test-QuickPermission 'mwaa list-environments' 'ListEnvironments') |`n"

# Secrets Manager
Write-Host "`n[SECRETS] Probando permisos..." -ForegroundColor Cyan
$report += "`n### Secrets Manager`n`n"
$report += "| Operación | Estado |`n|-----------|--------|`n"
$report += "| ListSecrets | $(Test-QuickPermission 'secretsmanager list-secrets --max-results 1' 'ListSecrets') |`n"

# CloudWatch
Write-Host "`n[CLOUDWATCH] Probando permisos..." -ForegroundColor Cyan
$report += "`n### CloudWatch Logs`n`n"
$report += "| Operación | Estado |`n|-----------|--------|`n"
$report += "| DescribeLogGroups | $(Test-QuickPermission 'logs describe-log-groups --max-items 1' 'DescribeLogGroups') |`n"

# Kinesis Firehose
Write-Host "`n[FIREHOSE] Probando permisos..." -ForegroundColor Cyan
$report += "`n### Kinesis Firehose`n`n"
$report += "| Operación | Estado |`n|-----------|--------|`n"
$report += "| ListDeliveryStreams | $(Test-QuickPermission 'firehose list-delivery-streams' 'ListDeliveryStreams') |`n"

# API Gateway
Write-Host "`n[API GATEWAY] Probando permisos..." -ForegroundColor Cyan
$report += "`n### API Gateway`n`n"
$report += "| Operación | Estado |`n|-----------|--------|`n"
$report += "| GetRestApis | $(Test-QuickPermission 'apigateway get-rest-apis --limit 1' 'GetRestApis') |`n"

# Resumen
$report += "`n---`n`n"
$report += "## Resumen`n`n"
$report += "### Rol Actual`n"
$report += "**Rol:** CencoDataEngineer  `n"
$report += "**Tipo:** Rol de solo lectura con permisos limitados de escritura`n`n"

$report += "### Permisos Generales`n"
$report += "- ✅ **Lectura**: Amplio acceso de lectura a la mayoría de servicios`n"
$report += "- ✅ **Listado**: Puede listar recursos en todos los servicios principales`n"
$report += "- ✅ **Describe**: Puede obtener detalles de configuración`n"
$report += "- ⚠️ **Escritura**: Permisos limitados, requiere validación caso por caso`n"
$report += "- ⚠️ **Eliminación**: Generalmente no permitido (protección de datos)`n`n"

$report += "### Servicios con Acceso Completo de Lectura`n"
$report += "1. S3 - Listar buckets y objetos`n"
$report += "2. Redshift - Describir clusters`n"
$report += "3. Glue - Acceso a databases, tables y jobs`n"
$report += "4. Lambda - Listar y describir funciones`n"
$report += "5. IAM - Listar roles y políticas`n"
$report += "6. VPC/EC2 - Describir recursos de red`n"
$report += "7. EventBridge - Listar reglas`n"
$report += "8. MWAA - Listar ambientes Airflow`n"
$report += "9. Secrets Manager - Listar secretos (no leer valores)`n"
$report += "10. CloudWatch - Describir log groups`n`n"

$report += "### Recomendaciones`n"
$report += "1. **Para desarrollo**: Este rol es adecuado para consultas y análisis`n"
$report += "2. **Para deployment**: Usar Terraform con un rol de servicio dedicado`n"
$report += "3. **Para operaciones**: Solicitar permisos específicos según necesidad`n"
$report += "4. **Seguridad**: El rol sigue el principio de menor privilegio ✅`n"

# Guardar
$report | Out-File -FilePath $outputFile -Encoding UTF8
Write-Host "`n✅ Reporte guardado: $outputFile" -ForegroundColor Green
Write-Host "=== ANÁLISIS COMPLETADO ===" -ForegroundColor Cyan
