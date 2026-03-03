# Script de Inventario de Permisos IAM - Proyecto Janis-Cencosud
# Analiza roles, políticas y permisos de recursos AWS

param(
    [string]$Profile = "cencosud",
    [string]$Region = "us-east-1",
    [string]$OutputFile = "permisos-aws-cencosud-$(Get-Date -Format 'yyyyMMdd-HHmmss').md"
)

Write-Host "`n=== ANÁLISIS DE PERMISOS IAM - PROYECTO JANIS-CENCOSUD ===" -ForegroundColor Cyan
Write-Host "Perfil: $Profile | Región: $Region`n" -ForegroundColor Yellow

$report = @"
# Análisis de Permisos IAM - Proyecto Janis-Cencosud

**Perfil AWS:** $Profile  
**Región:** $Region  
**Fecha:** $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')

---

"@

function Get-AWSResource {
    param([string]$Command)
    try {
        $result = aws $Command --profile $Profile --region $Region --output json 2>$null | ConvertFrom-Json
        return $result
    } catch {
        return $null
    }
}

# 1. IAM Roles del Proyecto
Write-Host "📋 Analizando IAM Roles..." -ForegroundColor Green
$report += "`n## IAM Roles del Proyecto`n`n"

$roles = Get-AWSResource "iam list-roles"
if ($roles -and $roles.Roles) {
    $projectRoles = $roles.Roles | Where-Object { 
        ($_.RoleName -like "*cencosud*") -or 
        ($_.RoleName -like "*janis*") -or 
        ($_.RoleName -like "*glue*") -or 
        ($_.RoleName -like "*lambda*") -or
        ($_.RoleName -like "*firehose*") -or
        ($_.RoleName -like "*mwaa*")
    }
    
    foreach ($role in $projectRoles) {
        Write-Host "  Analizando: $($role.RoleName)" -ForegroundColor Gray
        
        $report += "### $($role.RoleName)`n`n"
        $report += "- **ARN:** ``$($role.Arn)```n"
        $report += "- **Fecha de creación:** $($role.CreateDate)`n"
        
        # Assume Role Policy
        $report += "- **Trust Policy (AssumeRole):**`n``````json`n"
        $assumePolicy = $role.AssumeRolePolicyDocument | ConvertTo-Json -Depth 5
        $report += "$assumePolicy`n``````n`n"
        
        # Políticas Administradas Adjuntas
        $attachedPolicies = Get-AWSResource "iam list-attached-role-policies --role-name $($role.RoleName)"
        if ($attachedPolicies -and $attachedPolicies.AttachedPolicies) {
            $report += "#### Políticas Administradas Adjuntas`n`n"
            foreach ($policy in $attachedPolicies.AttachedPolicies) {
                $report += "- **$($policy.PolicyName)**`n"
                $report += "  - ARN: ``$($policy.PolicyArn)```n"
                
                # Obtener versión de la política
                $policyVersion = Get-AWSResource "iam get-policy --policy-arn $($policy.PolicyArn)"
                if ($policyVersion) {
                    $policyDoc = Get-AWSResource "iam get-policy-version --policy-arn $($policy.PolicyArn) --version-id $($policyVersion.Policy.DefaultVersionId)"
                    if ($policyDoc) {
                        $report += "  - **Permisos:**`n``````json`n"
                        $report += ($policyDoc.PolicyVersion.Document | ConvertTo-Json -Depth 10)
                        $report += "`n``````n"
                    }
                }
            }
            $report += "`n"
        }
        
        # Políticas Inline
        $inlinePolicies = Get-AWSResource "iam list-role-policies --role-name $($role.RoleName)"
        if ($inlinePolicies -and $inlinePolicies.PolicyNames) {
            $report += "#### Políticas Inline`n`n"
            foreach ($policyName in $inlinePolicies.PolicyNames) {
                $report += "- **$policyName**`n"
                $policyDoc = Get-AWSResource "iam get-role-policy --role-name $($role.RoleName) --policy-name $policyName"
                if ($policyDoc) {
                    $report += "``````json`n"
                    $report += ($policyDoc.PolicyDocument | ConvertTo-Json -Depth 10)
                    $report += "`n``````n"
                }
            }
            $report += "`n"
        }
        
        $report += "---`n`n"
    }
}

# 2. Políticas de S3 Buckets
Write-Host "📦 Analizando políticas de S3..." -ForegroundColor Green
$report += "`n## Políticas de S3 Buckets`n`n"

$s3Buckets = Get-AWSResource "s3api list-buckets"
if ($s3Buckets -and $s3Buckets.Buckets) {
    $projectBuckets = $s3Buckets.Buckets | Where-Object { 
        ($_.Name -like "*cencosud*") -or ($_.Name -like "*janis*") 
    }
    
    foreach ($bucket in $projectBuckets) {
        Write-Host "  Analizando: $($bucket.Name)" -ForegroundColor Gray
        
        $report += "### $($bucket.Name)`n`n"
        
        # Bucket Policy
        $bucketPolicy = Get-AWSResource "s3api get-bucket-policy --bucket $($bucket.Name)"
        if ($bucketPolicy) {
            $report += "#### Bucket Policy`n``````json`n"
            $report += ($bucketPolicy.Policy | ConvertFrom-Json | ConvertTo-Json -Depth 10)
            $report += "`n``````n`n"
        } else {
            $report += "- Sin Bucket Policy configurada`n`n"
        }
        
        # ACL
        $bucketAcl = Get-AWSResource "s3api get-bucket-acl --bucket $($bucket.Name)"
        if ($bucketAcl) {
            $report += "#### Access Control List (ACL)`n"
            $report += "- **Owner:** $($bucketAcl.Owner.DisplayName)`n"
            if ($bucketAcl.Grants) {
                $report += "- **Grants:**`n"
                foreach ($grant in $bucketAcl.Grants) {
                    $report += "  - $($grant.Permission) → $($grant.Grantee.Type)`n"
                }
            }
            $report += "`n"
        }
        
        # Public Access Block
        $publicAccess = Get-AWSResource "s3api get-public-access-block --bucket $($bucket.Name)"
        if ($publicAccess) {
            $report += "#### Public Access Block`n"
            $report += "- BlockPublicAcls: $($publicAccess.PublicAccessBlockConfiguration.BlockPublicAcls)`n"
            $report += "- IgnorePublicAcls: $($publicAccess.PublicAccessBlockConfiguration.IgnorePublicAcls)`n"
            $report += "- BlockPublicPolicy: $($publicAccess.PublicAccessBlockConfiguration.BlockPublicPolicy)`n"
            $report += "- RestrictPublicBuckets: $($publicAccess.PublicAccessBlockConfiguration.RestrictPublicBuckets)`n`n"
        }
        
        $report += "---`n`n"
    }
}

# 3. Políticas de Lambda Functions
Write-Host "λ Analizando políticas de Lambda..." -ForegroundColor Green
$report += "`n## Políticas de Lambda Functions`n`n"

$lambdaFunctions = Get-AWSResource "lambda list-functions"
if ($lambdaFunctions -and $lambdaFunctions.Functions) {
    $projectFunctions = $lambdaFunctions.Functions | Where-Object { 
        ($_.FunctionName -like "*cencosud*") -or ($_.FunctionName -like "*janis*") 
    }
    
    foreach ($func in $projectFunctions) {
        Write-Host "  Analizando: $($func.FunctionName)" -ForegroundColor Gray
        
        $report += "### $($func.FunctionName)`n`n"
        $report += "- **Role:** ``$($func.Role)```n"
        
        # Resource-based Policy
        $funcPolicy = Get-AWSResource "lambda get-policy --function-name $($func.FunctionName)"
        if ($funcPolicy) {
            $report += "#### Resource-based Policy`n``````json`n"
            $report += ($funcPolicy.Policy | ConvertFrom-Json | ConvertTo-Json -Depth 10)
            $report += "`n``````n`n"
        } else {
            $report += "- Sin resource-based policy`n`n"
        }
        
        $report += "---`n`n"
    }
}

# 4. Security Groups
Write-Host "🔒 Analizando Security Groups..." -ForegroundColor Green
$report += "`n## Security Groups`n`n"

$securityGroups = Get-AWSResource "ec2 describe-security-groups"
if ($securityGroups -and $securityGroups.SecurityGroups) {
    $projectSGs = $securityGroups.SecurityGroups | Where-Object { 
        ($_.GroupName -like "*cencosud*") -or ($_.GroupName -like "*janis*") 
    }
    
    foreach ($sg in $projectSGs) {
        Write-Host "  Analizando: $($sg.GroupName)" -ForegroundColor Gray
        
        $report += "### $($sg.GroupName) ($($sg.GroupId))`n`n"
        $report += "- **VPC:** $($sg.VpcId)`n"
        $report += "- **Descripción:** $($sg.Description)`n`n"
        
        # Ingress Rules
        if ($sg.IpPermissions) {
            $report += "#### Reglas de Entrada (Ingress)`n`n"
            $report += "| Protocolo | Puerto | Origen | Descripción |`n"
            $report += "|-----------|--------|--------|-------------|`n"
            foreach ($rule in $sg.IpPermissions) {
                $protocol = if ($rule.IpProtocol -eq "-1") { "All" } else { $rule.IpProtocol }
                $port = if ($rule.FromPort) { "$($rule.FromPort)-$($rule.ToPort)" } else { "All" }
                
                if ($rule.IpRanges) {
                    foreach ($ipRange in $rule.IpRanges) {
                        $report += "| $protocol | $port | $($ipRange.CidrIp) | $($ipRange.Description) |`n"
                    }
                }
                if ($rule.UserIdGroupPairs) {
                    foreach ($groupPair in $rule.UserIdGroupPairs) {
                        $report += "| $protocol | $port | SG: $($groupPair.GroupId) | $($groupPair.Description) |`n"
                    }
                }
            }
            $report += "`n"
        }
        
        # Egress Rules
        if ($sg.IpPermissionsEgress) {
            $report += "#### Reglas de Salida (Egress)`n`n"
            $report += "| Protocolo | Puerto | Destino | Descripción |`n"
            $report += "|-----------|--------|---------|-------------|`n"
            foreach ($rule in $sg.IpPermissionsEgress) {
                $protocol = if ($rule.IpProtocol -eq "-1") { "All" } else { $rule.IpProtocol }
                $port = if ($rule.FromPort) { "$($rule.FromPort)-$($rule.ToPort)" } else { "All" }
                
                if ($rule.IpRanges) {
                    foreach ($ipRange in $rule.IpRanges) {
                        $report += "| $protocol | $port | $($ipRange.CidrIp) | $($ipRange.Description) |`n"
                    }
                }
            }
            $report += "`n"
        }
        
        $report += "---`n`n"
    }
}

# 5. Resumen de Permisos por Servicio
Write-Host "📊 Generando resumen..." -ForegroundColor Green
$report += "`n## Resumen de Permisos por Servicio`n`n"

$report += "### Servicios con Acceso Configurado`n`n"
$report += "- ✅ IAM Roles y Políticas`n"
$report += "- ✅ S3 Bucket Policies`n"
$report += "- ✅ Lambda Resource Policies`n"
$report += "- ✅ Security Groups (Network ACLs)`n"
$report += "- ✅ VPC Configuration`n`n"

$report += "### Recomendaciones de Seguridad`n`n"
$report += "1. **Principio de Menor Privilegio:** Revisar que cada rol tenga solo los permisos mínimos necesarios`n"
$report += "2. **Cifrado:** Verificar que todos los buckets S3 tengan cifrado habilitado`n"
$report += "3. **Public Access:** Confirmar que los buckets no tengan acceso público no deseado`n"
$report += "4. **Network Security:** Validar que los Security Groups solo permitan tráfico necesario`n"
$report += "5. **Auditoría:** Habilitar CloudTrail para auditar accesos a recursos`n"
$report += "6. **Rotación de Credenciales:** Implementar rotación automática de secrets en Secrets Manager`n"

# Guardar reporte
$report | Out-File -FilePath $OutputFile -Encoding UTF8
Write-Host "`n✅ Reporte de permisos guardado en: $OutputFile" -ForegroundColor Green
Write-Host "`n=== ANÁLISIS COMPLETADO ===" -ForegroundColor Cyan
