# Fix unused err variables by adding assert.NoError checks

$files = @(
    "routing_property_test.go",
    "security_groups_unit_test.go",
    "single_az_property_test.go",
    "vpc_unit_test.go",
    "vpc_cidr_property_test.go"
)

foreach ($file in $files) {
    Write-Host "Processing $file..." -ForegroundColor Yellow
    
    $lines = Get-Content $file
    $newLines = @()
    
    for ($i = 0; $i < $lines.Count; $i++) {
        $line = $lines[$i]
        $newLines += $line
        
        # If this line has "exitCode, err := terraform.InitAndPlanE" or "exitCode, err := terraform.ValidateE"
        if ($line -match 'exitCode, err := terraform\.(InitAndPlanE|ValidateE)') {
            # Add assert.NoError on the next line
            $indent = ($line -replace '\S.*$', '')  # Get the indentation
            $newLines += "$indent`assert.NoError(t, err)"
        }
    }
    
    Set-Content $file -Value $newLines
    Write-Host "  Fixed $file" -ForegroundColor Green
}

Write-Host ""
Write-Host "All files fixed!" -ForegroundColor Green
