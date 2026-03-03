# Testing Quick Start Guide

Quick reference for running the ETL pipeline test suite.

## Prerequisites

```bash
# 1. Ensure LocalStack is running
docker-compose up -d

# 2. Verify LocalStack is accessible
aws s3 ls --endpoint-url http://localhost:4566

# 3. Navigate to scripts directory
cd max/scripts
```

## Quick Commands

### Run Full Test Suite

```bash
# Clean → Test → Clean (recommended)
python cleanup_test_data.py && \
python test_end_to_end.py && \
python cleanup_test_data.py
```

### Individual Steps

```bash
# 1. Clean test data
python cleanup_test_data.py

# 2. Run end-to-end test
python test_end_to_end.py

# 3. View results
cat output/end_to_end_report_metro_*.json | python -m json.tool

# 4. Clean up
python cleanup_test_data.py
```

### Test Different Clients

```bash
# Test metro client (default)
python test_end_to_end.py

# Test wongio client
python test_end_to_end.py --client wongio

# Clean both clients
python cleanup_test_data.py --all
```

### Partial Cleanup

```bash
# Clean only Bronze layer
python cleanup_test_data.py --layer bronze

# Clean only Silver layer
python cleanup_test_data.py --layer silver

# Clean only Gold layer
python cleanup_test_data.py --layer gold

# Clean only local files
python cleanup_test_data.py --layer local

# Dry-run (see what would be cleaned)
python cleanup_test_data.py --dry-run
```

## Expected Output

### Successful Test Run

```
================================================================================
TEST END-TO-END - PIPELINE BRONZE→SILVER→GOLD
================================================================================
Cliente: metro
Entidades: orders, order-items, products, skus, stock
Timestamp: 2026-02-25T10:30:00

================================================================================
PASO 1: CARGAR DATOS DE PRUEBA A BRONZE LAYER
================================================================================

📦 Cargando datos de prueba para: orders
   Registros en fixture: 3
   Limpiando datos anteriores de orders...
✅ Datos cargados exitosamente a: s3://data-lake-bronze/metro/orders/test_data.json

[... more output ...]

================================================================================
REPORTE END-TO-END
================================================================================

📊 Resumen General:
   Cliente: metro
   Timestamp: 2026-02-25T10:30:00

   Bronze→Silver:
      Total entidades: 5
      Exitosas: 5
      Tasa de éxito: 100.0%

   Silver→Gold:
      Total tablas: 5
      Exitosas: 5
      Tasa de éxito: 100.0%

   Validaciones:
      Total: 5
      Pasadas: 5
      Tasa de éxito: 100.0%

================================================================================
✅ TEST END-TO-END EXITOSO - Todos los pipelines y validaciones pasaron
================================================================================
```

### Failed Test Run

```
================================================================================
REPORTE END-TO-END
================================================================================

📊 Resumen General:
   [...]
   Bronze→Silver:
      Total entidades: 5
      Exitosas: 3
      Tasa de éxito: 60.0%

   Silver→Gold:
      Total tablas: 5
      Exitosas: 2
      Tasa de éxito: 40.0%

================================================================================
⚠️  TEST END-TO-END PARCIAL - Algunos pipelines o validaciones fallaron
================================================================================
```

## Test Data

Test fixtures are located in `max/tests/fixtures/`:

- `orders.json` - 3 records (1 duplicate)
- `order-items.json` - 4 records (1 duplicate)
- `products.json` - 4 records (1 duplicate)
- `skus.json` - 4 records (1 duplicate)
- `stock.json` - 5 records (1 duplicate)

Each fixture includes edge cases:
- Duplicates (same ID, different dateModified)
- NULL values
- Empty arrays/objects
- Nested JSON structures
- Missing optional fields

## Troubleshooting

### LocalStack Not Running

```bash
# Check if LocalStack is running
docker ps | grep localstack

# Start LocalStack
docker-compose up -d

# Check logs
docker-compose logs -f localstack
```

### Pipeline Fails

```bash
# Check pipeline logs
ls -la max/glue/etl-bronze-to-silver/output/
ls -la max/glue/etl-silver-to-gold/output/

# Run individual pipeline manually
cd max/glue/etl-bronze-to-silver
python run_pipeline.py --entity-type orders --client metro
```

### S3 Buckets Not Found

```bash
# Create buckets manually
aws s3 mb s3://data-lake-bronze --endpoint-url http://localhost:4566
aws s3 mb s3://data-lake-silver --endpoint-url http://localhost:4566
aws s3 mb s3://data-lake-gold --endpoint-url http://localhost:4566

# Or run terraform
cd terraform
terraform apply
```

### Clean Everything

```bash
# Nuclear option: clean everything
python cleanup_test_data.py --all

# Restart LocalStack
docker-compose restart localstack

# Re-run terraform if needed
cd terraform
terraform apply
```

## Exit Codes

- `0` - All tests passed
- `1` - Some tests failed or error occurred

Use in scripts:

```bash
if python test_end_to_end.py; then
    echo "Tests passed!"
else
    echo "Tests failed!"
    exit 1
fi
```

## Performance

Typical execution times:

- **Cleanup**: 10-30 seconds
- **End-to-End Test**: 2-5 minutes
- **Full Suite**: 3-6 minutes

Factors affecting performance:
- LocalStack performance
- Number of records in fixtures
- Network latency
- System resources

## Next Steps

After successful test run:

1. Review test report in `max/scripts/output/`
2. Verify data in S3 buckets (optional)
3. Run cleanup to restore clean state
4. Scale to more entities (see main README)

## Additional Resources

- Full documentation: `max/tests/README.md`
- Pipeline documentation: `max/glue/docs/`
- Configuration files: `max/glue/etl-*/config/`
- Fixtures: `max/tests/fixtures/`
