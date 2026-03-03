# ============================================================================
# Script: Update Tags to Corporate Policy
# Purpose: Update all Terraform resources to use Corporate AWS Tagging Policy
# ============================================================================

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Updating Tags to Corporate Policy" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Define the modules to update
$modules = @(
    "modules/vpc/main.tf",
    "modules/security-groups/main.tf",
    "modules/vpc-endpoints/main.tf",
    "modules/nacls/main.tf",
    "modules/eventbridge/main.tf",
    "modules/monitoring/main.tf"
)

$rootPath = Split-Path -Parent $PSScriptRoot

foreach ($module in $modules) {
    $filePath = Join-Path $rootPath $module
    
    if (Test-Path $filePath) {
        Write-Host "Processing: $module" -ForegroundColor Yellow
        
        # Read the file content
        $content = Get-Content $filePath -Raw
        
        # Replace simple tags blocks with merge function
        # Pattern: tags = { ... }
        # Replace with: tags = merge(var.tags, { ... })
        
        $pattern = '(?s)(tags\s*=\s*)\{(\s*Name\s*=)'
        $replacement = '$1merge(var.tags, {$2'
        $content = $content -replace $pattern, $replacement
        
        # Add closing parenthesis for merge function
        # This is a simplified approach - may need manual review
        $pattern = '(?s)(tags\s*=\s*merge\(var\.tags,\s*\{[^}]+\})\s*\}'
        $replacement = '$1})'
        $content = $content -replace $pattern, $replacement
        
        # Write back to file
        Set-Content -Path $filePath -Value $content -NoNewline
        
        Write-Host "  ✓ Updated" -ForegroundColor Green
    } else {
        Write-Host "  ✗ File not found: $filePath" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "IMPORTANT: Manual Review Required" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "This script performed automated tag updates." -ForegroundColor Yellow
Write-Host "Please review the changes manually to ensure correctness." -ForegroundColor Yellow
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "1. Review all modified files" -ForegroundColor White
Write-Host "2. Add 'tags' variable to each module's variables.tf" -ForegroundColor White
Write-Host "3. Update main.tf to pass tags to all modules" -ForegroundColor White
Write-Host "4. Run 'terraform fmt -recursive'" -ForegroundColor White
Write-Host "5. Run 'terraform validate'" -ForegroundColor White
Write-Host ""
