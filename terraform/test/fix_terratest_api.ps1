# Script to fix Terratest API changes in Go test files
# Terratest now returns (exitCode, error) instead of just exitCode

Write-Host "Fixing Terratest API changes in test files..." -ForegroundColor Cyan

$files = @(
    "routing_property_test.go",
    "security_groups_unit_test.go",
    "single_az_property_test.go",
    "vpc_unit_test.go",
    "vpc_cidr_property_test.go"
)

foreach ($file in $files) {
    Write-Host "Processing $file..." -ForegroundColor Yellow
    
    $content = Get-Content $file -Raw
    
    # Fix InitAndPlanE calls
    $content = $content -replace 'exitCode := terraform\.InitAndPlanE\(t, terraformOptions\)', 'exitCode, err := terraform.InitAndPlanE(t, terraformOptions)'
    
    # Fix ValidateE calls
    $content = $content -replace 'exitCode := terraform\.ValidateE\(t, terraformOptions\)', 'exitCode, err := terraform.ValidateE(t, terraformOptions)'
    
    # Add error check after InitAndPlanE (before assert.Equal)
    $content = $content -replace '(exitCode, err := terraform\.InitAndPlanE\(t, terraformOptions\))\s+assert\.Equal', '$1' + "`n`t`t`tassert.NoError(t, err, `"Terraform plan should not error`")`n`t`t`tassert.Equal"
    
    # Add error check after ValidateE (before if tc.expectValid or if tc.shouldPass or if tc.shouldSucceed or if tc.expectValidConfig)
    $content = $content -replace '(exitCode, err := terraform\.ValidateE\(t, terraformOptions\))\s+(if tc\.(expectValid|shouldPass|shouldSucceed|expectValidConfig))', '$1' + "`n`t`t`tassert.NoError(t, err, `"Terraform validate should not error`")`n`t`t`t`$2"
    
    Set-Content $file -Value $content
    Write-Host "  Fixed $file" -ForegroundColor Green
}

Write-Host ""
Write-Host "All files fixed successfully!" -ForegroundColor Green
