#!/usr/bin/env python3
"""
Fix Terratest API changes in Go test files

This script automatically updates Go test files to handle Terratest API changes.
Specifically, it fixes the return signature change where functions like
InitAndPlanE and ValidateE now return (exitCode, err) instead of just exitCode.

The script:
1. Scans specified Go test files for Terratest function calls
2. Detects calls that return (exitCode, err)
3. Adds assert.NoError(t, err) after each call if not present
4. Maintains proper code indentation

Usage:
    cd terraform/test
    python fix_go_tests.py

Files processed:
    - routing_property_test.go
    - security_groups_unit_test.go
    - single_az_property_test.go
    - vpc_unit_test.go
    - vpc_cidr_property_test.go

When to use:
    - After updating Terratest to a newer version
    - When tests fail due to API signature changes
    - When adding new test files that use Terratest
"""

import re

files = [
    "routing_property_test.go",
    "security_groups_unit_test.go",
    "single_az_property_test.go",
    "vpc_unit_test.go",
    "vpc_cidr_property_test.go"
]

for filename in files:
    print(f"Processing {filename}...")
    
    with open(filename, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find all lines with "exitCode, err := terraform.InitAndPlanE" or "exitCode, err := terraform.ValidateE"
    # and add "assert.NoError(t, err)" on the next line if not already present
    
    lines = content.split('\n')
    new_lines = []
    
    for i, line in enumerate(lines):
        new_lines.append(line)
        
        # Check if this line has the pattern
        if 'exitCode, err := terraform.InitAndPlanE' in line or 'exitCode, err := terraform.ValidateE' in line:
            # Check if the next line already has assert.NoError
            if i + 1 < len(lines) and 'assert.NoError(t, err)' not in lines[i + 1]:
                # Get the indentation from the current line
                indent = len(line) - len(line.lstrip())
                # Add assert.NoError with the same indentation
                new_lines.append('\t' * (indent // 4) + 'assert.NoError(t, err)')
    
    # Write back
    with open(filename, 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(new_lines))
    
    print(f"  Fixed {filename}")

print("\nAll files fixed!")
