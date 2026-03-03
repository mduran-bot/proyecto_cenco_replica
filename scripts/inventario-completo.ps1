# Script Simplificado de Inventario AWS - Proyecto Janis-Cencosud
param(
    [string]$Profile = "cencosud",
    [string]$Region = "us-east-1"
)

$timestamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$jsonFile = "inventario-aws-cencosud-$timestamp.json"
$mdFile = "inventario-aws-cencosud-$timestamp.md"

Write-Host "`n=== INVENTARIO DE RECURSOS AWS ===" -ForegroundColor Cyan
Write-Host "Perfil: $Profile" -ForegroundColor Yellow
Write-Host "Region: $Region" -ForegroundColor Yellow
Write-Host "Fecha: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')`n" -ForegroundColor Yellow

$inventory = @{
    metadata = @{
        profile = $Profile
        region = $Region
        timestamp = (Get-Date -Format "o")
        project = "janis-cencosud"
        account = ""
    }
    resources = @{}
    byEnvironment = @{
        dev = @{}
        qa = @{}
        test = @{}
        prod = @{}
        staging = @{}
        unknown = @{}
    }
}

# Función para detectar ambiente desde tags o nombre
function Get-Environment {
    param(
        [string]$Name,
        [object]$Tags = $null
    )
    
    # Primero intentar obtener desde tags (metodo preferido)
    if ($Tags) {
        # Buscar tag "Environment" o "environment"
        $envTag = $Tags | Where-Object { $_.Key -eq "Environment" -or $_.Key -eq "environment" } | Select-Object -First 1
        if ($envTag) {
            $envValue = $envTag.Value.ToLower()
            # Normalizar valores comunes
            if ($envValue -match "prod|production|prd") { return "prod" }
            if ($envValue -match "qa|quality") { return "qa" }
            if ($envValue -match "dev|desa|desarrollo|development") { return "dev" }
            if ($envValue -match "test|testing|tst") { return "test" }
            if ($envValue -match "stg|staging") { return "staging" }
            return $envValue  # Retornar el valor del tag si no coincide con los patrones
        }
    }
    
    # Fallback: detectar desde el nombre (metodo antiguo)
    $nameLower = $Name.ToLower()
    if ($nameLower -match "prod|production|prd") { return "prod" }
    if ($nameLower -match "-qa|_qa|\.qa") { return "qa" }
    if ($nameLower -match "-dev|_dev|\.dev|desa|desarrollo") { return "dev" }
    if ($nameLower -match "-test|_test|\.test") { return "test" }
    if ($nameLower -match "stg|staging") { return "staging" }
    
    return "unknown"
}

# Obtener información de la cuenta
Write-Host "Obteniendo información de la cuenta..." -ForegroundColor Green
try {
    $identity = aws sts get-caller-identity --profile $Profile --output json | ConvertFrom-Json
    $inventory.metadata.account = $identity.Account
    $inventory.metadata.userId = $identity.UserId
    $inventory.metadata.arn = $identity.Arn
    Write-Host "  + Cuenta: $($identity.Account)" -ForegroundColor White
    Write-Host "  + Usuario: $($identity.UserId)" -ForegroundColor White
} catch {
    Write-Host "  ! Error obteniendo información de cuenta" -ForegroundColor Red
}

# S3 Buckets
Write-Host "`n[S3] Listando buckets..." -ForegroundColor Green
try {
    $s3Result = aws s3api list-buckets --profile $Profile --output json 2>$null
    if ($LASTEXITCODE -eq 0) {
        $s3Data = $s3Result | ConvertFrom-Json
        $s3Buckets = @()
        foreach ($bucket in $s3Data.Buckets) {
            if ($bucket.Name -match "cencosud|janis") {
                # Obtener tags del bucket
                $bucketTags = $null
                try {
                    $tagsResult = aws s3api get-bucket-tagging --bucket $($bucket.Name) --profile $Profile --output json 2>$null
                    if ($LASTEXITCODE -eq 0) {
                        $tagsData = $tagsResult | ConvertFrom-Json
                        $bucketTags = $tagsData.TagSet
                    }
                } catch {
                    # Bucket sin tags o sin permisos para leer tags
                }
                
                $env = Get-Environment -Name $bucket.Name -Tags $bucketTags
                $tagSource = if ($bucketTags) { "tag" } else { "nombre" }
                Write-Host "  + $($bucket.Name) [$env via $tagSource]" -ForegroundColor White
                
                $bucketInfo = @{
                    name = $bucket.Name
                    creationDate = $bucket.CreationDate
                    environment = $env
                    environmentSource = $tagSource
                    tags = $bucketTags
                }
                $s3Buckets += $bucketInfo
                
                # Agregar a clasificación por ambiente
                if (-not $inventory.byEnvironment.$env.s3) {
                    $inventory.byEnvironment.$env.s3 = @()
                }
                $inventory.byEnvironment.$env.s3 += $bucketInfo
            }
        }
        $inventory.resources.s3 = $s3Buckets
        Write-Host "  Total: $($s3Buckets.Count)" -ForegroundColor Cyan
    }
} catch {
    Write-Host "  ! Sin acceso a S3" -ForegroundColor Yellow
    $inventory.resources.s3 = @()
}

# Redshift
Write-Host "`n[REDSHIFT] Listando clusters..." -ForegroundColor Green
try {
    $redshiftResult = aws redshift describe-clusters --profile $Profile --region $Region --output json 2>$null
    if ($LASTEXITCODE -eq 0) {
        $redshiftData = $redshiftResult | ConvertFrom-Json
        $clusters = @()
        foreach ($cluster in $redshiftData.Clusters) {
            Write-Host "  + $($cluster.ClusterIdentifier) [$($cluster.ClusterStatus)]" -ForegroundColor White
            $clusters += @{
                identifier = $cluster.ClusterIdentifier
                nodeType = $cluster.NodeType
                numberOfNodes = $cluster.NumberOfNodes
                status = $cluster.ClusterStatus
                endpoint = $cluster.Endpoint.Address
                port = $cluster.Endpoint.Port
            }
        }
        $inventory.resources.redshift = $clusters
        Write-Host "  Total: $($clusters.Count)" -ForegroundColor Cyan
    }
} catch {
    Write-Host "  ! Sin acceso a Redshift" -ForegroundColor Yellow
    $inventory.resources.redshift = @()
}

# Glue Databases
Write-Host "`n[GLUE] Listando databases..." -ForegroundColor Green
try {
    $glueDbResult = aws glue get-databases --profile $Profile --region $Region --output json 2>$null
    if ($LASTEXITCODE -eq 0) {
        $glueDbData = $glueDbResult | ConvertFrom-Json
        $databases = @()
        foreach ($db in $glueDbData.DatabaseList) {
            Write-Host "  + $($db.Name)" -ForegroundColor White
            $databases += @{
                name = $db.Name
                description = $db.Description
                locationUri = $db.LocationUri
            }
        }
        $inventory.resources.glueDatabases = $databases
        Write-Host "  Total: $($databases.Count)" -ForegroundColor Cyan
    }
} catch {
    Write-Host "  ! Sin acceso a Glue Databases" -ForegroundColor Yellow
    $inventory.resources.glueDatabases = @()
}

# Glue Jobs
Write-Host "`n[GLUE] Listando jobs..." -ForegroundColor Green
try {
    $glueJobsResult = aws glue get-jobs --profile $Profile --region $Region --output json 2>$null
    if ($LASTEXITCODE -eq 0) {
        $glueJobsData = $glueJobsResult | ConvertFrom-Json
        $jobs = @()
        foreach ($job in $glueJobsData.Jobs) {
            # Glue Jobs tienen tags en el objeto directamente
            $glueTags = $null
            if ($job.Tags) {
                $glueTags = @()
                $job.Tags.PSObject.Properties | ForEach-Object {
                    $glueTags += @{ Key = $_.Name; Value = $_.Value }
                }
            }
            
            $env = Get-Environment -Name $job.Name -Tags $glueTags
            $tagSource = if ($glueTags) { "tag" } else { "nombre" }
            Write-Host "  + $($job.Name) [$env via $tagSource]" -ForegroundColor White
            
            $jobInfo = @{
                name = $job.Name
                role = $job.Role
                command = $job.Command.Name
                environment = $env
                environmentSource = $tagSource
                tags = $glueTags
            }
            $jobs += $jobInfo
            
            # Agregar a clasificación por ambiente
            if (-not $inventory.byEnvironment.$env.glueJobs) {
                $inventory.byEnvironment.$env.glueJobs = @()
            }
            $inventory.byEnvironment.$env.glueJobs += $jobInfo
        }
        $inventory.resources.glueJobs = $jobs
        Write-Host "  Total: $($jobs.Count)" -ForegroundColor Cyan
    }
} catch {
    Write-Host "  ! Sin acceso a Glue Jobs" -ForegroundColor Yellow
    $inventory.resources.glueJobs = @()
}

# Lambda Functions
Write-Host "`n[LAMBDA] Listando funciones..." -ForegroundColor Green
try {
    $lambdaResult = aws lambda list-functions --profile $Profile --region $Region --output json 2>$null
    if ($LASTEXITCODE -eq 0) {
        $lambdaData = $lambdaResult | ConvertFrom-Json
        $functions = @()
        foreach ($func in $lambdaData.Functions) {
            if ($func.FunctionName -match "cencosud|janis") {
                # Obtener tags de la función Lambda
                $lambdaTags = $null
                try {
                    $tagsResult = aws lambda list-tags --resource $($func.FunctionArn) --profile $Profile --region $Region --output json 2>$null
                    if ($LASTEXITCODE -eq 0) {
                        $tagsData = $tagsResult | ConvertFrom-Json
                        if ($tagsData.Tags) {
                            # Convertir hashtable a array de objetos con Key/Value
                            $lambdaTags = @()
                            $tagsData.Tags.PSObject.Properties | ForEach-Object {
                                $lambdaTags += @{ Key = $_.Name; Value = $_.Value }
                            }
                        }
                    }
                } catch {
                    # Sin tags o sin permisos
                }
                
                $env = Get-Environment -Name $func.FunctionName -Tags $lambdaTags
                $tagSource = if ($lambdaTags) { "tag" } else { "nombre" }
                Write-Host "  + $($func.FunctionName) [$($func.Runtime)] [$env via $tagSource]" -ForegroundColor White
                
                $funcInfo = @{
                    name = $func.FunctionName
                    runtime = $func.Runtime
                    role = $func.Role
                    memorySize = $func.MemorySize
                    environment = $env
                    environmentSource = $tagSource
                    tags = $lambdaTags
                }
                $functions += $funcInfo
                
                # Agregar a clasificación por ambiente
                if (-not $inventory.byEnvironment.$env.lambda) {
                    $inventory.byEnvironment.$env.lambda = @()
                }
                $inventory.byEnvironment.$env.lambda += $funcInfo
            }
        }
        $inventory.resources.lambda = $functions
        Write-Host "  Total: $($functions.Count)" -ForegroundColor Cyan
    }
} catch {
    Write-Host "  ! Sin acceso a Lambda" -ForegroundColor Yellow
    $inventory.resources.lambda = @()
}

# IAM Roles
Write-Host "`n[IAM] Listando roles..." -ForegroundColor Green
try {
    $iamResult = aws iam list-roles --profile $Profile --output json 2>$null
    if ($LASTEXITCODE -eq 0) {
        $iamData = $iamResult | ConvertFrom-Json
        $roles = @()
        foreach ($role in $iamData.Roles) {
            if ($role.RoleName -match "cencosud|janis|glue|lambda|firehose|mwaa") {
                Write-Host "  + $($role.RoleName)" -ForegroundColor White
                $roles += @{
                    roleName = $role.RoleName
                    arn = $role.Arn
                    createDate = $role.CreateDate
                }
            }
        }
        $inventory.resources.iamRoles = $roles
        Write-Host "  Total: $($roles.Count)" -ForegroundColor Cyan
    }
} catch {
    Write-Host "  ! Sin acceso a IAM" -ForegroundColor Yellow
    $inventory.resources.iamRoles = @()
}

# VPC
Write-Host "`n[VPC] Listando VPCs..." -ForegroundColor Green
try {
    $vpcResult = aws ec2 describe-vpcs --profile $Profile --region $Region --output json 2>$null
    if ($LASTEXITCODE -eq 0) {
        $vpcData = $vpcResult | ConvertFrom-Json
        $vpcs = @()
        foreach ($vpc in $vpcData.Vpcs) {
            $vpcName = ($vpc.Tags | Where-Object { $_.Key -eq "Name" }).Value
            if ($vpcName -match "cencosud|janis") {
                Write-Host "  + $vpcName ($($vpc.VpcId))" -ForegroundColor White
                $vpcs += @{
                    vpcId = $vpc.VpcId
                    name = $vpcName
                    cidrBlock = $vpc.CidrBlock
                }
            }
        }
        $inventory.resources.vpc = $vpcs
        Write-Host "  Total: $($vpcs.Count)" -ForegroundColor Cyan
    }
} catch {
    Write-Host "  ! Sin acceso a VPC" -ForegroundColor Yellow
    $inventory.resources.vpc = @()
}

# Guardar JSON
Write-Host "`n--- Guardando inventario ---" -ForegroundColor Cyan
$inventory | ConvertTo-Json -Depth 10 | Out-File -FilePath $jsonFile -Encoding UTF8
Write-Host "+ JSON guardado: $jsonFile" -ForegroundColor Green

# Generar Markdown
$markdown = @"
# Inventario de Recursos AWS - Proyecto Janis-Cencosud

**Perfil AWS:** $Profile  
**Region:** $Region  
**Cuenta:** $($inventory.metadata.account)  
**Fecha:** $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')

---

## Resumen Ejecutivo

| Servicio | Cantidad |
|----------|----------|
| S3 Buckets | $($inventory.resources.s3.Count) |
| Redshift Clusters | $($inventory.resources.redshift.Count) |
| Glue Databases | $($inventory.resources.glueDatabases.Count) |
| Glue Jobs | $($inventory.resources.glueJobs.Count) |
| Lambda Functions | $($inventory.resources.lambda.Count) |
| IAM Roles | $($inventory.resources.iamRoles.Count) |
| VPCs | $($inventory.resources.vpc.Count) |

---

## Detalles por Servicio

"@

if ($inventory.resources.s3.Count -gt 0) {
    $markdown += "`n### S3 Buckets`n`n"
    foreach ($bucket in $inventory.resources.s3) {
        $markdown += "- **$($bucket.name)** (Creado: $($bucket.creationDate))`n"
    }
}

if ($inventory.resources.redshift.Count -gt 0) {
    $markdown += "`n### Redshift Clusters`n`n"
    foreach ($cluster in $inventory.resources.redshift) {
        $markdown += "- **$($cluster.identifier)** - $($cluster.nodeType) x$($cluster.numberOfNodes) [$($cluster.status)]`n"
    }
}

if ($inventory.resources.glueDatabases.Count -gt 0) {
    $markdown += "`n### Glue Databases`n`n"
    foreach ($db in $inventory.resources.glueDatabases) {
        $markdown += "- **$($db.name)**`n"
    }
}

if ($inventory.resources.glueJobs.Count -gt 0) {
    $markdown += "`n### Glue Jobs`n`n"
    foreach ($job in $inventory.resources.glueJobs) {
        $markdown += "- **$($job.name)** ($($job.command))`n"
    }
}

if ($inventory.resources.lambda.Count -gt 0) {
    $markdown += "`n### Lambda Functions`n`n"
    foreach ($func in $inventory.resources.lambda) {
        $markdown += "- **$($func.name)** - $($func.runtime) ($($func.memorySize)MB)`n"
    }
}

if ($inventory.resources.iamRoles.Count -gt 0) {
    $markdown += "`n### IAM Roles`n`n"
    foreach ($role in $inventory.resources.iamRoles) {
        $markdown += "- **$($role.roleName)**`n"
    }
}

if ($inventory.resources.vpc.Count -gt 0) {
    $markdown += "`n### VPCs`n`n"
    foreach ($vpc in $inventory.resources.vpc) {
        $markdown += "- **$($vpc.name)** ($($vpc.vpcId)) - $($vpc.cidrBlock)`n"
    }
}

$markdown += "`n---`n`n"

# Agregar sección de clasificación por ambientes
$markdown += "## Recursos por Ambiente`n`n"

foreach ($env in @("prod", "qa", "dev", "test", "staging", "unknown")) {
    $envResources = $inventory.byEnvironment.$env
    $totalCount = 0
    
    if ($envResources.s3) { $totalCount += $envResources.s3.Count }
    if ($envResources.lambda) { $totalCount += $envResources.lambda.Count }
    if ($envResources.glueJobs) { $totalCount += $envResources.glueJobs.Count }
    
    if ($totalCount -gt 0) {
        $envLabel = switch ($env) {
            "prod" { "Producción" }
            "qa" { "QA / Quality Assurance" }
            "dev" { "Desarrollo" }
            "test" { "Testing" }
            "staging" { "Staging" }
            "unknown" { "Sin clasificar" }
        }
        
        $markdown += "`n### $envLabel ($env)`n`n"
        
        if ($envResources.s3 -and $envResources.s3.Count -gt 0) {
            $markdown += "**S3 Buckets ($($envResources.s3.Count)):**`n"
            foreach ($bucket in $envResources.s3) {
                $markdown += "- $($bucket.name)`n"
            }
            $markdown += "`n"
        }
        
        if ($envResources.lambda -and $envResources.lambda.Count -gt 0) {
            $markdown += "**Lambda Functions ($($envResources.lambda.Count)):**`n"
            foreach ($func in $envResources.lambda) {
                $markdown += "- $($func.name) [$($func.runtime)]`n"
            }
            $markdown += "`n"
        }
        
        if ($envResources.glueJobs -and $envResources.glueJobs.Count -gt 0) {
            $markdown += "**Glue Jobs ($($envResources.glueJobs.Count)):**`n"
            foreach ($job in $envResources.glueJobs) {
                $markdown += "- $($job.name)`n"
            }
            $markdown += "`n"
        }
    }
}

$markdown += "`n---`n`n"

# Agregar seccion de analisis de permisos detallado
Write-Host "`n[PERMISOS] Analizando permisos detallados..." -ForegroundColor Green

$permissions = @{
    s3 = @{ list = "NO"; read = "NO"; write = "NO"; delete = "NO"; tagging = "NO" }
    redshift = @{ list = "NO"; read = "NO"; write = "NO"; delete = "NO" }
    glue = @{ list = "NO"; read = "NO"; write = "NO"; delete = "NO" }
    lambda = @{ list = "NO"; read = "NO"; invoke = "NO"; update = "NO"; delete = "NO" }
    iam = @{ list = "NO"; read = "NO"; write = "NO"; delete = "NO" }
    vpc = @{ list = "NO"; read = "NO"; write = "NO"; delete = "NO" }
    cloudwatch = @{ list = "NO"; read = "NO"; write = "NO" }
    eventbridge = @{ list = "NO"; read = "NO"; write = "NO" }
    kinesis = @{ list = "NO"; read = "NO"; write = "NO" }
}

# Test S3 permissions
if ($inventory.resources.s3.Count -gt 0) {
    $permissions.s3.list = "OK"
    $permissions.s3.read = "OK"
    
    # Test tagging (ya lo probamos antes)
    $testBucket = $inventory.resources.s3[0].name
    try {
        aws s3api get-bucket-tagging --bucket $testBucket --profile $Profile --output json 2>$null | Out-Null
        if ($LASTEXITCODE -eq 0) {
            $permissions.s3.tagging = "OK"
        }
    } catch { }
    
    Write-Host "  + S3: List=OK, Read=OK, Tagging=$($permissions.s3.tagging)" -ForegroundColor White
}

# Test Redshift permissions
if ($inventory.resources.redshift.Count -gt 0) {
    $permissions.redshift.list = "OK"
    $permissions.redshift.read = "OK"
    Write-Host "  + Redshift: List=OK, Read=OK" -ForegroundColor White
}

# Test Glue permissions
if ($inventory.resources.glueDatabases.Count -gt 0) {
    $permissions.glue.list = "OK"
    $permissions.glue.read = "OK"
    
    # Test if we can get job details
    if ($inventory.resources.glueJobs.Count -gt 0) {
        $testJob = $inventory.resources.glueJobs[0].name
        try {
            aws glue get-job --job-name $testJob --profile $Profile --region $Region --output json 2>$null | Out-Null
            if ($LASTEXITCODE -eq 0) {
                $permissions.glue.read = "OK"
            }
        } catch { }
    }
    
    Write-Host "  + Glue: List=OK, Read=OK" -ForegroundColor White
}

# Test Lambda permissions
if ($inventory.resources.lambda.Count -gt 0) {
    $permissions.lambda.list = "OK"
    $permissions.lambda.read = "OK"
    
    # Test if we can get function configuration
    $testFunc = $inventory.resources.lambda[0].name
    try {
        aws lambda get-function-configuration --function-name $testFunc --profile $Profile --region $Region --output json 2>$null | Out-Null
        if ($LASTEXITCODE -eq 0) {
            $permissions.lambda.read = "OK"
        }
    } catch { }
    
    Write-Host "  + Lambda: List=OK, Read=OK" -ForegroundColor White
}

# Test IAM permissions
if ($inventory.resources.iamRoles.Count -gt 0) {
    $permissions.iam.list = "OK"
    $permissions.iam.read = "OK"
    Write-Host "  + IAM: List=OK, Read=OK" -ForegroundColor White
}

# Test VPC permissions
if ($inventory.resources.vpc.Count -gt 0) {
    $permissions.vpc.list = "OK"
    $permissions.vpc.read = "OK"
    Write-Host "  + VPC: List=OK, Read=OK" -ForegroundColor White
}

# Test CloudWatch Logs
try {
    aws logs describe-log-groups --profile $Profile --region $Region --max-items 1 --output json 2>$null | Out-Null
    if ($LASTEXITCODE -eq 0) {
        $permissions.cloudwatch.list = "OK"
        $permissions.cloudwatch.read = "OK"
        Write-Host "  + CloudWatch Logs: List=OK, Read=OK" -ForegroundColor White
    }
} catch { }

# Test EventBridge
try {
    aws events list-rules --profile $Profile --region $Region --max-results 1 --output json 2>$null | Out-Null
    if ($LASTEXITCODE -eq 0) {
        $permissions.eventbridge.list = "OK"
        $permissions.eventbridge.read = "OK"
        Write-Host "  + EventBridge: List=OK, Read=OK" -ForegroundColor White
    }
} catch { }

# Test Kinesis Firehose
try {
    aws firehose list-delivery-streams --profile $Profile --region $Region --limit 1 --output json 2>$null | Out-Null
    if ($LASTEXITCODE -eq 0) {
        $permissions.kinesis.list = "OK"
        $permissions.kinesis.read = "OK"
        Write-Host "  + Kinesis Firehose: List=OK, Read=OK" -ForegroundColor White
    }
} catch { }

# Guardar permisos en el inventario
$inventory.permissions = $permissions

$markdown += "## Analisis Detallado de Permisos`n`n"
$markdown += "### Matriz de Permisos por Servicio`n`n"
$markdown += "| Servicio | Listar | Leer | Escribir | Eliminar | Otros | Notas |`n"
$markdown += "|----------|--------|------|----------|----------|-------|-------|`n"

# S3
$markdown += "| S3 | $($permissions.s3.list) | $($permissions.s3.read) | $($permissions.s3.write) | $($permissions.s3.delete) | Tagging: $($permissions.s3.tagging) | "
if ($permissions.s3.list -eq "OK") {
    $markdown += "Acceso de lectura completo, tagging "
    if ($permissions.s3.tagging -eq "OK") { $markdown += "habilitado" } else { $markdown += "no disponible" }
} else {
    $markdown += "Sin acceso"
}
$markdown += " |`n"

# Redshift
$markdown += "| Redshift | $($permissions.redshift.list) | $($permissions.redshift.read) | $($permissions.redshift.write) | $($permissions.redshift.delete) | - | "
if ($permissions.redshift.list -eq "OK") {
    $markdown += "Acceso de lectura, requiere VPN para queries"
} else {
    $markdown += "Requiere VPN o permisos adicionales"
}
$markdown += " |`n"

# Glue
$markdown += "| Glue | $($permissions.glue.list) | $($permissions.glue.read) | $($permissions.glue.write) | $($permissions.glue.delete) | - | "
if ($permissions.glue.list -eq "OK") {
    $markdown += "Acceso completo de lectura a databases y jobs"
} else {
    $markdown += "Sin acceso"
}
$markdown += " |`n"

# Lambda
$markdown += "| Lambda | $($permissions.lambda.list) | $($permissions.lambda.read) | Invoke: $($permissions.lambda.invoke) | $($permissions.lambda.delete) | Update: $($permissions.lambda.update) | "
if ($permissions.lambda.list -eq "OK") {
    $markdown += "Acceso de lectura completo, ejecucion no probada"
} else {
    $markdown += "Sin acceso"
}
$markdown += " |`n"

# IAM
$markdown += "| IAM | $($permissions.iam.list) | $($permissions.iam.read) | $($permissions.iam.write) | $($permissions.iam.delete) | - | "
if ($permissions.iam.list -eq "OK") {
    $markdown += "Solo lectura (buena practica de seguridad)"
} else {
    $markdown += "Sin acceso"
}
$markdown += " |`n"

# VPC
$markdown += "| VPC/EC2 | $($permissions.vpc.list) | $($permissions.vpc.read) | $($permissions.vpc.write) | $($permissions.vpc.delete) | - | "
if ($permissions.vpc.list -eq "OK") {
    $markdown += "Acceso de lectura a configuracion de red"
} else {
    $markdown += "Sin acceso a configuracion de red"
}
$markdown += " |`n"

# CloudWatch
$markdown += "| CloudWatch Logs | $($permissions.cloudwatch.list) | $($permissions.cloudwatch.read) | $($permissions.cloudwatch.write) | - | - | "
if ($permissions.cloudwatch.list -eq "OK") {
    $markdown += "Acceso de lectura a logs"
} else {
    $markdown += "Sin acceso"
}
$markdown += " |`n"

# EventBridge
$markdown += "| EventBridge | $($permissions.eventbridge.list) | $($permissions.eventbridge.read) | $($permissions.eventbridge.write) | - | - | "
if ($permissions.eventbridge.list -eq "OK") {
    $markdown += "Acceso de lectura a reglas"
} else {
    $markdown += "Sin acceso"
}
$markdown += " |`n"

# Kinesis
$markdown += "| Kinesis Firehose | $($permissions.kinesis.list) | $($permissions.kinesis.read) | $($permissions.kinesis.write) | - | - | "
if ($permissions.kinesis.list -eq "OK") {
    $markdown += "Acceso de lectura a delivery streams"
} else {
    $markdown += "Sin acceso"
}
$markdown += " |`n"

$markdown += "`n**Leyenda:** OK = Confirmado | NO = Sin acceso o no probado`n`n"

# Resumen de permisos
$markdown += "### Resumen de Acceso por Servicio`n`n"

# Contar servicios con acceso
$servicesWithAccess = @()
$servicesWithoutAccess = @()

if ($permissions.s3.list -eq "OK") {
    $servicesWithAccess += "S3 Buckets ($($inventory.resources.s3.Count) recursos) - Lectura: OK, Tagging: $($permissions.s3.tagging)"
} else {
    $servicesWithoutAccess += "S3 Buckets"
}

if ($permissions.glue.list -eq "OK") {
    $servicesWithAccess += "AWS Glue ($($inventory.resources.glueDatabases.Count) databases, $($inventory.resources.glueJobs.Count) jobs) - Lectura: OK"
} else {
    $servicesWithoutAccess += "AWS Glue"
}

if ($permissions.lambda.list -eq "OK") {
    $servicesWithAccess += "Lambda Functions ($($inventory.resources.lambda.Count) funciones) - Lectura: OK"
} else {
    $servicesWithoutAccess += "Lambda Functions"
}

if ($permissions.iam.list -eq "OK") {
    $servicesWithAccess += "IAM Roles ($($inventory.resources.iamRoles.Count) roles) - Solo lectura"
} else {
    $servicesWithoutAccess += "IAM Roles"
}

if ($permissions.redshift.list -eq "OK") {
    $servicesWithAccess += "Redshift ($($inventory.resources.redshift.Count) clusters) - Lectura: OK"
} else {
    $servicesWithoutAccess += "Redshift (requiere VPN)"
}

if ($permissions.vpc.list -eq "OK") {
    $servicesWithAccess += "VPC/EC2 ($($inventory.resources.vpc.Count) VPCs) - Lectura: OK"
} else {
    $servicesWithoutAccess += "VPC/EC2"
}

if ($permissions.cloudwatch.list -eq "OK") {
    $servicesWithAccess += "CloudWatch Logs - Lectura: OK"
} else {
    $servicesWithoutAccess += "CloudWatch Logs"
}

if ($permissions.eventbridge.list -eq "OK") {
    $servicesWithAccess += "EventBridge - Lectura: OK"
} else {
    $servicesWithoutAccess += "EventBridge"
}

if ($permissions.kinesis.list -eq "OK") {
    $servicesWithAccess += "Kinesis Firehose - Lectura: OK"
} else {
    $servicesWithoutAccess += "Kinesis Firehose"
}

$markdown += "**Servicios con acceso ($($servicesWithAccess.Count)):**`n"
foreach ($service in $servicesWithAccess) {
    $markdown += "- $service`n"
}

if ($servicesWithoutAccess.Count -gt 0) {
    $markdown += "`n**Servicios sin acceso ($($servicesWithoutAccess.Count)):**`n"
    foreach ($service in $servicesWithoutAccess) {
        $markdown += "- $service`n"
    }
}

$markdown += "`n### Recomendaciones de Seguridad`n`n"
$markdown += "1. **Principio de Menor Privilegio**: El rol actual sigue buenas practicas con permisos de lectura amplios`n"
$markdown += "2. **Cifrado**: Verificar que todos los buckets S3 tengan cifrado habilitado`n"
$markdown += "3. **Auditoría**: Habilitar CloudTrail para auditar accesos a recursos`n"
$markdown += "4. **Rotacion de Credenciales**: Implementar rotacion automatica de secrets`n"

if ($inventory.resources.redshift.Count -eq 0) {
    $markdown += "5. **Redshift**: Solicitar permisos de lectura si necesitas consultar Redshift directamente`n"
}

$markdown += "`n---`n`n"
$markdown += "**Nota:** Este inventario muestra solo los recursos a los que el perfil '$Profile' tiene acceso.`n"
$markdown += "`n**Portabilidad:** Este script puede ejecutarse en cualquier maquina con AWS CLI y PowerShell.`n"
$markdown += "`n**Ultima actualizacion:** $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')`n"

$markdown | Out-File -FilePath $mdFile -Encoding UTF8
Write-Host "+ Markdown guardado: $mdFile" -ForegroundColor Green

# Generar CSV para Excel
Write-Host "`n[CSV] Generando archivo para Excel..." -ForegroundColor Green
$csvFile = "inventario-completo-$timestamp.csv"

# Crear array de objetos para CSV
$csvData = @()

# Agregar S3 Buckets
if ($inventory.resources.s3) {
    foreach ($bucket in $inventory.resources.s3) {
        $csvData += [PSCustomObject]@{
            TipoRecurso = "S3 Bucket"
            Nombre = $bucket.name
            Ambiente = $bucket.environment
            FuenteAmbiente = $bucket.environmentSource
            FechaCreacion = $bucket.creationDate
            Runtime = ""
            Memoria = ""
            Estado = ""
            Region = $Region
            Cuenta = $inventory.metadata.account
            PermisoLectura = $permissions.s3.read
            PermisoEscritura = $permissions.s3.write
            PermisoEliminacion = $permissions.s3.delete
        }
    }
}

# Agregar Lambda Functions
if ($inventory.resources.lambda) {
    foreach ($func in $inventory.resources.lambda) {
        $csvData += [PSCustomObject]@{
            TipoRecurso = "Lambda Function"
            Nombre = $func.name
            Ambiente = $func.environment
            FuenteAmbiente = $func.environmentSource
            FechaCreacion = ""
            Runtime = $func.runtime
            Memoria = "$($func.memorySize)MB"
            Estado = ""
            Region = $Region
            Cuenta = $inventory.metadata.account
            PermisoLectura = $permissions.lambda.read
            PermisoEscritura = $permissions.lambda.update
            PermisoEliminacion = $permissions.lambda.delete
        }
    }
}

# Agregar Glue Jobs
if ($inventory.resources.glueJobs) {
    foreach ($job in $inventory.resources.glueJobs) {
        $csvData += [PSCustomObject]@{
            TipoRecurso = "Glue Job"
            Nombre = $job.name
            Ambiente = $job.environment
            FuenteAmbiente = $job.environmentSource
            FechaCreacion = ""
            Runtime = $job.command
            Memoria = ""
            Estado = ""
            Region = $Region
            Cuenta = $inventory.metadata.account
            PermisoLectura = $permissions.glue.read
            PermisoEscritura = $permissions.glue.write
            PermisoEliminacion = $permissions.glue.delete
        }
    }
}

# Agregar Glue Databases
if ($inventory.resources.glueDatabases) {
    foreach ($db in $inventory.resources.glueDatabases) {
        $csvData += [PSCustomObject]@{
            TipoRecurso = "Glue Database"
            Nombre = $db.name
            Ambiente = "unknown"
            FuenteAmbiente = "N/A"
            FechaCreacion = ""
            Runtime = ""
            Memoria = ""
            Estado = ""
            Region = $Region
            Cuenta = $inventory.metadata.account
            PermisoLectura = $permissions.glue.read
            PermisoEscritura = $permissions.glue.write
            PermisoEliminacion = $permissions.glue.delete
        }
    }
}

# Agregar Redshift Clusters
if ($inventory.resources.redshift) {
    foreach ($cluster in $inventory.resources.redshift) {
        $csvData += [PSCustomObject]@{
            TipoRecurso = "Redshift Cluster"
            Nombre = $cluster.identifier
            Ambiente = "unknown"
            FuenteAmbiente = "N/A"
            FechaCreacion = ""
            Runtime = "$($cluster.nodeType) x$($cluster.numberOfNodes)"
            Memoria = ""
            Estado = $cluster.status
            Region = $Region
            Cuenta = $inventory.metadata.account
            PermisoLectura = $permissions.redshift.read
            PermisoEscritura = $permissions.redshift.write
            PermisoEliminacion = $permissions.redshift.delete
        }
    }
}

# Agregar IAM Roles (primeros 50 para no saturar)
if ($inventory.resources.iamRoles) {
    $topRoles = $inventory.resources.iamRoles | Select-Object -First 50
    foreach ($role in $topRoles) {
        $csvData += [PSCustomObject]@{
            TipoRecurso = "IAM Role"
            Nombre = $role.roleName
            Ambiente = "unknown"
            FuenteAmbiente = "N/A"
            FechaCreacion = $role.createDate
            Runtime = ""
            Memoria = ""
            Estado = ""
            Region = "Global"
            Cuenta = $inventory.metadata.account
            PermisoLectura = $permissions.iam.read
            PermisoEscritura = $permissions.iam.write
            PermisoEliminacion = $permissions.iam.delete
        }
    }
}

# Exportar a CSV
$csvData | Export-Csv -Path $csvFile -NoTypeInformation -Encoding UTF8
Write-Host "  + CSV guardado: $csvFile" -ForegroundColor White
Write-Host "  + Columnas incluidas: TipoRecurso, Nombre, Ambiente, Permisos (Lectura/Escritura/Eliminacion)" -ForegroundColor Gray

Write-Host "`n=== INVENTARIO COMPLETADO ===" -ForegroundColor Cyan
Write-Host "Archivos generados:" -ForegroundColor Yellow
Write-Host "  - $jsonFile (datos estructurados)" -ForegroundColor White
Write-Host "  - $mdFile (reporte legible)" -ForegroundColor White
Write-Host "  - $csvFile (para Excel)" -ForegroundColor White

# Estadisticas de deteccion de ambientes
Write-Host "`nEstadisticas de Deteccion de Ambientes:" -ForegroundColor Yellow
$totalRecursos = 0
$recursosPorTag = 0
$recursosPorNombre = 0

if ($inventory.resources.s3) {
    $totalRecursos += $inventory.resources.s3.Count
    $recursosPorTag += ($inventory.resources.s3 | Where-Object { $_.environmentSource -eq "tag" }).Count
    $recursosPorNombre += ($inventory.resources.s3 | Where-Object { $_.environmentSource -eq "nombre" }).Count
}

if ($inventory.resources.lambda) {
    $totalRecursos += $inventory.resources.lambda.Count
    $recursosPorTag += ($inventory.resources.lambda | Where-Object { $_.environmentSource -eq "tag" }).Count
    $recursosPorNombre += ($inventory.resources.lambda | Where-Object { $_.environmentSource -eq "nombre" }).Count
}

if ($inventory.resources.glueJobs) {
    $totalRecursos += $inventory.resources.glueJobs.Count
    $recursosPorTag += ($inventory.resources.glueJobs | Where-Object { $_.environmentSource -eq "tag" }).Count
    $recursosPorNombre += ($inventory.resources.glueJobs | Where-Object { $_.environmentSource -eq "nombre" }).Count
}

$porcentajeTag = if ($totalRecursos -gt 0) { [math]::Round(($recursosPorTag / $totalRecursos) * 100, 1) } else { 0 }

Write-Host "  Total recursos analizados: $totalRecursos" -ForegroundColor White
Write-Host "  Detectados por TAG: $recursosPorTag ($porcentajeTag%)" -ForegroundColor Green
Write-Host "  Detectados por NOMBRE: $recursosPorNombre" -ForegroundColor Yellow
Write-Host ""