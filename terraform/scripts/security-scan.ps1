#!/usr/bin/env pwsh
# Security scan script for Terraform infrastructure
# This script performs basic security checks on Terraform code

Write-Host "=== Terraform Security Scan ===" -ForegroundColor Cyan
Write-Host ""

$ErrorCount = 0
$WarningCount = 0
$terraformDir = Split-Path -Parent $PSScriptRoot

# Function to check file for security issues
function Test-SecurityIssues {
    param(
        [string]$FilePath
    )
    
    $content = Get-Content $FilePath -Raw
    $fileName = Split-Path $FilePath -Leaf
    $issues = @()
    
    # Check for hardcoded credentials
    if ($content -match '(password|secret|api_key|access_key)\s*=\s*"[^$]') {
        $issues += "Potential hardcoded credentials found"
    }
    
    # Check for overly permissive CIDR blocks on sensitive ports
    if ($content -match 'cidr_blocks\s*=\s*\["0\.0\.0\.0/0"\]' -and 
        $content -match '(from_port|to_port)\s*=\s*(22|3389|5432|3306|1433)') {
        $issues += "Overly permissive security group rule (0.0.0.0/0 on sensitive port)"
    }
    
    # Check for unencrypted S3 buckets
    if ($content -match 'resource\s+"aws_s3_bucket"' -and 
        $content -notmatch 'aws_s3_bucket_server_side_encryption_configuration') {
        $issues += "S3 bucket may lack encryption configuration"
    }
    
    # Check for public S3 buckets
    if ($content -match 'acl\s*=\s*"public-read"') {
        $issues += "S3 bucket configured with public-read ACL"
    }
    
    # Check for disabled encryption
    if ($content -match 'encrypted\s*=\s*false') {
        $issues += "Encryption explicitly disabled"
    }
    
    # Check for missing VPC configuration on sensitive resources
    if ($content -match 'resource\s+"aws_db_instance"' -and 
        $content -notmatch 'db_subnet_group_name') {
        $issues += "RDS instance may not be in VPC"
    }
    
    # Check for publicly accessible databases
    if ($content -match 'publicly_accessible\s*=\s*true') {
        $issues += "Database configured as publicly accessible"
    }
    
    # Check for missing backup configuration
    if ($content -match 'resource\s+"aws_db_instance"' -and 
        $content -notmatch 'backup_retention_period') {
        $issues += "Database may lack backup configuration"
    }
    
    # Check for missing CloudWatch logs
    if ($content -match 'resource\s+"aws_vpc"' -and 
        $content -notmatch 'aws_flow_log') {
        # This is informational, not critical
    }
    
    # Check for missing tags
    if ($content -match 'resource\s+"aws_' -and 
        $content -notmatch 'tags\s*=') {
        $issues += "Resource may be missing tags"
    }
    
    return $issues
}

# Scan all Terraform files
Write-Host "Scanning Terraform files..." -ForegroundColor Yellow
$tfFiles = Get-ChildItem -Path $terraformDir -Filter "*.tf" -Recurse

foreach ($file in $tfFiles) {
    $issues = Test-SecurityIssues -FilePath $file.FullName
    
    if ($issues.Count -gt 0) {
        Write-Host "`n[!] $($file.FullName.Replace($terraformDir, '.'))" -ForegroundColor Red
        foreach ($issue in $issues) {
            Write-Host "    - $issue" -ForegroundColor Yellow
            $WarningCount++
        }
    }
}

Write-Host "`n=== Security Scan Summary ===" -ForegroundColor Cyan
Write-Host "Files scanned: $($tfFiles.Count)" -ForegroundColor White
Write-Host "Warnings found: $WarningCount" -ForegroundColor $(if ($WarningCount -gt 0) { "Yellow" } else { "Green" })

if ($WarningCount -eq 0) {
    Write-Host "`n[OK] No security issues detected!" -ForegroundColor Green
    exit 0
} else {
    Write-Host "`n[WARNING] Security warnings detected. Please review the issues above." -ForegroundColor Yellow
    Write-Host "Note: These are basic checks. For comprehensive security scanning, install tfsec or trivy." -ForegroundColor Gray
    exit 0  # Exit with 0 as these are warnings, not errors
}
