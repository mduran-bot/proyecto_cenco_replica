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

# Función para detectar ambiente
function Get-Environment {
    param([string]$Name)
    
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
                $env = Get-Environment $bucket.Name
                Write-Host "  + $($bucket.Name) [$env]" -ForegroundColor White
                
                $bucketInfo = @{
                    name = $bucket.Name
                    creationDate = $bucket.CreationDate
                    environment = $env
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
            $env = Get-Environment $job.Name
            Write-Host "  + $($job.Name) [$env]" -ForegroundColor White
            
            $jobInfo = @{
                name = $job.Name
                role = $job.Role
                command = $job.Command.Name
                environment = $env
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
                $env = Get-Environment $func.FunctionName
                Write-Host "  + $($func.FunctionName) [$($func.Runtime)] [$env]" -ForegroundColor White
                
                $funcInfo = @{
                    name = $func.FunctionName
                    runtime = $func.Runtime
                    role = $func.Role
                    memorySize = $func.MemorySize
                    environment = $env
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
$markdown += "**Nota:** Este inventario muestra solo los recursos a los que el perfil '$Profile' tiene acceso.`n"

$markdown | Out-File -FilePath $mdFile -Encoding UTF8
Write-Host "+ Markdown guardado: $mdFile" -ForegroundColor Green

Write-Host "`n=== INVENTARIO COMPLETADO ===" -ForegroundColor Cyan
Write-Host "Archivos generados:" -ForegroundColor Yellow
Write-Host "  - $jsonFile" -ForegroundColor White
Write-Host "  - $mdFile" -ForegroundColor White
