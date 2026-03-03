# Testing Suite for ETL Pipeline

This directory contains the complete testing suite for the Bronze→Silver→Gold ETL pipeline expansion.

## Overview

The testing suite validates the end-to-end functionality of processing 41 Janis API entities through the three-layer data lake architecture.

## Directory Structure

```
max/tests/
├── fixtures/              # Test data for 5 representative entities
│   ├── orders.json
│   ├── order-items.json
│   ├── products.json
│   ├── skus.json
│   ├── stock.json
│   └── README.md
└── README.md             # This file
```

## Test Scripts

### 1. End-to-End Test (`max/scripts/test_end_to_end.py`)

Comprehensive test that validates the complete pipeline from Bronze to Gold.

**What it tests:**
- Loading test data to Bronze layer
- Bronze→Silver transformation for 5 entities
- Silver→Gold transformation for 5 tables
- Schema validation against `redshift_schemas.json`
- Record count consistency across layers
- Calculated fields correctness

**Usage:**
```bash
# Test with metro client
cd max/scripts
python test_end_to_end.py

# Test with wongio client
python test_end_to_end.py --client wongio
```

**Expected Output:**
- Detailed logs for each step
- JSON report in `max/scripts/output/end_to_end_report_<client>_<timestamp>.json`
- Exit code 0 if all tests pass, 1 if any fail

**Test Entities:**
1. **orders** → **wms_orders** (Gold table)
2. **order-items** → **wms_order_items** (Gold table)
3. **products** → **products** (Gold table)
4. **skus** → **skus** (Gold table)
5. **stock** → **stock** (Gold table)

### 2. Cleanup Script (`max/scripts/cleanup_test_data.py`)

Utility to clean test data from all layers and restore environment to clean state.

**What it cleans:**
- Bronze layer S3 buckets
- Silver layer Iceberg tables
- Gold layer Iceberg tables
- Local output files
- Audit tables (data_gaps_log, data_quality_issues, etc.)

**Usage:**
```bash
# Clean all layers for metro client
cd max/scripts
python cleanup_test_data.py

# Clean all layers for wongio client
python cleanup_test_data.py --client wongio

# Clean both clients
python cleanup_test_data.py --all

# Clean only specific layer
python cleanup_test_data.py --layer bronze
python cleanup_test_data.py --layer silver
python cleanup_test_data.py --layer gold
python cleanup_test_data.py --layer local

# Dry-run (show what would be cleaned without executing)
python cleanup_test_data.py --dry-run
```

**Options:**
- `--client <metro|wongio>`: Client to clean (default: metro)
- `--all`: Clean both clients
- `--layer <bronze|silver|gold|local|audit>`: Clean only specific layer
- `--dry-run`: Simulate cleanup without executing

## Test Data Fixtures

Located in `max/tests/fixtures/`, these JSON files contain test data with:

### Edge Cases Covered

1. **Duplicates**: Records with same ID but different `dateModified` to test deduplication
2. **NULL values**: Optional fields with NULL to test NULL handling
3. **Empty structures**: Empty arrays `[]` and objects `{}` to test edge cases
4. **Nested JSON**: Complex nested structures to test JSON flattening
5. **Arrays**: Parent-child relationships to test array explosion
6. **Mixed timestamps**: Unix timestamps and ISO 8601 strings to test type conversion
7. **Missing fields**: Records with missing optional fields to test data gap handling

### Expected Behavior

**Before Deduplication:**
- orders: 3 records (1 duplicate)
- order-items: 4 records (1 duplicate)
- products: 4 records (1 duplicate)
- skus: 4 records (1 duplicate)
- stock: 5 records (1 duplicate)

**After Deduplication (keeping most recent `dateModified`):**
- orders: 2 unique records
- order-items: 3 unique records
- products: 3 unique records
- skus: 3 unique records
- stock: 4 unique records

## Running Tests

### Prerequisites

1. **LocalStack running**: Ensure LocalStack is running on `http://localhost:4566`
2. **AWS CLI configured**: AWS CLI should be configured to use LocalStack endpoint
3. **Python dependencies**: Install required packages from `requirements.txt`

### Full Test Workflow

```bash
# 1. Clean previous test data
cd max/scripts
python cleanup_test_data.py

# 2. Run end-to-end test
python test_end_to_end.py

# 3. Review results
cat output/end_to_end_report_metro_*.json

# 4. Clean up after testing
python cleanup_test_data.py
```

### Continuous Testing

For development, you can run tests repeatedly:

```bash
# Clean, test, and clean again
python cleanup_test_data.py && \
python test_end_to_end.py && \
python cleanup_test_data.py
```

## Test Reports

### End-to-End Report Structure

```json
{
  "timestamp": "2026-02-25T10:30:00",
  "client": "metro",
  "test_entities": ["orders", "order-items", "products", "skus", "stock"],
  "entity_to_gold_table": {
    "orders": "wms_orders",
    "order-items": "wms_order_items",
    "products": "products",
    "skus": "skus",
    "stock": "stock"
  },
  "results": {
    "bronze_to_silver": {
      "orders": {
        "status": "SUCCESS",
        "metrics": {
          "records_read": 3,
          "records_written": 2
        },
        "silver_verified": true
      }
    },
    "silver_to_gold": {
      "wms_orders": {
        "status": "SUCCESS",
        "metrics": {
          "records_read": 2,
          "records_written": 2
        },
        "gold_verified": true
      }
    },
    "validations": {
      "wms_orders": {
        "schema_validation": "PASSED",
        "record_count_validation": "PASSED",
        "calculated_fields_validation": "PASSED",
        "expected_fields": 43,
        "counts": {
          "bronze": 3,
          "silver": 2,
          "gold": 2
        }
      }
    }
  },
  "summary": {
    "bronze_to_silver": {
      "total": 5,
      "successful": 5,
      "success_rate": 100.0
    },
    "silver_to_gold": {
      "total": 5,
      "successful": 5,
      "success_rate": 100.0
    },
    "validations": {
      "total": 5,
      "passed": 5,
      "success_rate": 100.0
    }
  }
}
```

## Troubleshooting

### Common Issues

1. **LocalStack not running**
   ```
   Error: Could not connect to the endpoint URL: "http://localhost:4566"
   ```
   **Solution**: Start LocalStack with `docker-compose up -d`

2. **Fixtures not found**
   ```
   Error: Fixture file not found: max/tests/fixtures/orders.json
   ```
   **Solution**: Ensure you're running from the correct directory or use absolute paths

3. **Pipeline execution timeout**
   ```
   Error: Timeout executing pipeline for orders
   ```
   **Solution**: Increase timeout in test script or check LocalStack performance

4. **S3 bucket not found**
   ```
   Error: NoSuchBucket: The specified bucket does not exist
   ```
   **Solution**: Create buckets first or run terraform to set up infrastructure

### Debug Mode

Enable detailed logging:

```bash
# Set log level to DEBUG
export LOG_LEVEL=DEBUG
python test_end_to_end.py
```

## Integration with CI/CD

The test suite can be integrated into CI/CD pipelines:

```yaml
# Example GitHub Actions workflow
- name: Run End-to-End Tests
  run: |
    cd max/scripts
    python cleanup_test_data.py
    python test_end_to_end.py
    python cleanup_test_data.py
```

## Future Enhancements

Planned improvements to the testing suite:

1. **Property-Based Testing**: Add Hypothesis tests for universal properties
2. **Performance Testing**: Measure throughput and latency
3. **Data Quality Metrics**: Automated quality score calculation
4. **Visual Reports**: HTML reports with charts and graphs
5. **Parallel Execution**: Run tests for multiple clients in parallel
6. **Regression Testing**: Compare results against baseline

## Contributing

When adding new test entities:

1. Create fixture file in `max/tests/fixtures/<entity>.json`
2. Include edge cases (duplicates, NULLs, empty structures)
3. Update `test_entities` list in `test_end_to_end.py`
4. Update `entity_to_gold_table` mapping
5. Update this README with new entity details
6. Run full test suite to verify

## Support

For issues or questions about the testing suite:

1. Check this README for common issues
2. Review test logs in `max/scripts/output/`
3. Check pipeline documentation in `max/glue/docs/`
4. Contact the data engineering team
