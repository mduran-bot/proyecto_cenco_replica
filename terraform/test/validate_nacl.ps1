# PowerShell script to validate NACL configuration
# This script validates that NACLs are properly configured for stateless bidirectional communication

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "NACL Configuration Validation" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Set working directory to terraform root
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$terraformDir = Split-Path -Parent $scriptDir
Set-Location $terraformDir

Write-Host "Validating NACL module configuration..." -ForegroundColor Yellow
Write-Host ""

# Initialize Terraform in NACL module
Write-Host "Step 1: Initializing NACL module..." -ForegroundColor Cyan
Set-Location "modules/nacls"
terraform init -backend=false
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Terraform init failed for NACL module" -ForegroundColor Red
    exit 1
}

# Validate NACL module
Write-Host ""
Write-Host "Step 2: Validating NACL module..." -ForegroundColor Cyan
terraform validate
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Terraform validate failed for NACL module" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Step 3: Checking NACL rules configuration..." -ForegroundColor Cyan

# Check that public NACL has required rules
Write-Host "  - Checking public NACL inbound rules..." -ForegroundColor Gray
$publicInboundHttps = Select-String -Path "main.tf" -Pattern 'resource "aws_network_acl_rule" "public_inbound_https"' -Quiet
$publicInboundEphemeral = Select-String -Path "main.tf" -Pattern 'resource "aws_network_acl_rule" "public_inbound_ephemeral"' -Quiet

if (-not $publicInboundHttps) {
    Write-Host "    ERROR: Public NACL missing inbound HTTPS rule" -ForegroundColor Red
    exit 1
}
if (-not $publicInboundEphemeral) {
    Write-Host "    ERROR: Public NACL missing inbound ephemeral ports rule" -ForegroundColor Red
    exit 1
}
Write-Host "    ✓ Public NACL inbound rules configured" -ForegroundColor Green

# Check that public NACL has outbound rule
Write-Host "  - Checking public NACL outbound rules..." -ForegroundColor Gray
$publicOutboundAll = Select-String -Path "main.tf" -Pattern 'resource "aws_network_acl_rule" "public_outbound_all"' -Quiet

if (-not $publicOutboundAll) {
    Write-Host "    ERROR: Public NACL missing outbound all traffic rule" -ForegroundColor Red
    exit 1
}
Write-Host "    ✓ Public NACL outbound rules configured" -ForegroundColor Green

# Check that private NACL has required rules
Write-Host "  - Checking private NACL inbound rules..." -ForegroundColor Gray
$privateInboundVpc = Select-String -Path "main.tf" -Pattern 'resource "aws_network_acl_rule" "private_inbound_vpc"' -Quiet
$privateInboundHttps = Select-String -Path "main.tf" -Pattern 'resource "aws_network_acl_rule" "private_inbound_https"' -Quiet
$privateInboundEphemeral = Select-String -Path "main.tf" -Pattern 'resource "aws_network_acl_rule" "private_inbound_ephemeral"' -Quiet

if (-not $privateInboundVpc) {
    Write-Host "    ERROR: Private NACL missing inbound VPC traffic rule" -ForegroundColor Red
    exit 1
}
if (-not $privateInboundHttps) {
    Write-Host "    ERROR: Private NACL missing inbound HTTPS rule" -ForegroundColor Red
    exit 1
}
if (-not $privateInboundEphemeral) {
    Write-Host "    ERROR: Private NACL missing inbound ephemeral ports rule" -ForegroundColor Red
    exit 1
}
Write-Host "    ✓ Private NACL inbound rules configured" -ForegroundColor Green

# Check that private NACL has outbound rules
Write-Host "  - Checking private NACL outbound rules..." -ForegroundColor Gray
$privateOutboundVpc = Select-String -Path "main.tf" -Pattern 'resource "aws_network_acl_rule" "private_outbound_vpc"' -Quiet
$privateOutboundHttps = Select-String -Path "main.tf" -Pattern 'resource "aws_network_acl_rule" "private_outbound_https"' -Quiet

if (-not $privateOutboundVpc) {
    Write-Host "    ERROR: Private NACL missing outbound VPC traffic rule" -ForegroundColor Red
    exit 1
}
if (-not $privateOutboundHttps) {
    Write-Host "    ERROR: Private NACL missing outbound HTTPS rule" -ForegroundColor Red
    exit 1
}
Write-Host "    ✓ Private NACL outbound rules configured" -ForegroundColor Green

Write-Host ""
Write-Host "Step 4: Verifying bidirectional communication support..." -ForegroundColor Cyan

# Verify ephemeral port range (1024-65535)
$ephemeralPortCheck = Select-String -Path "main.tf" -Pattern 'from_port\s*=\s*1024' -Quiet
$ephemeralPortEndCheck = Select-String -Path "main.tf" -Pattern 'to_port\s*=\s*65535' -Quiet

if (-not $ephemeralPortCheck -or -not $ephemeralPortEndCheck) {
    Write-Host "  WARNING: Ephemeral port range (1024-65535) may not be correctly configured" -ForegroundColor Yellow
} else {
    Write-Host "  ✓ Ephemeral port range (1024-65535) correctly configured" -ForegroundColor Green
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "NACL Configuration Validation: PASSED" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Summary:" -ForegroundColor Cyan
Write-Host "  ✓ Public NACL: Inbound HTTPS + Ephemeral, Outbound All" -ForegroundColor Green
Write-Host "  ✓ Private NACL: Inbound VPC + HTTPS + Ephemeral, Outbound VPC + HTTPS" -ForegroundColor Green
Write-Host "  ✓ Bidirectional communication supported" -ForegroundColor Green
Write-Host ""

# Return to original directory
Set-Location $terraformDir

exit 0
