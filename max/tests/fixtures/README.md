# Test Fixtures for ETL Pipeline

This directory contains test data fixtures for end-to-end testing of the Bronze→Silver→Gold ETL pipeline.

## Entities Covered

1. **orders.json** - Order data with nested structures
2. **order-items.json** - Order line items
3. **products.json** - Product catalog data
4. **skus.json** - SKU (Stock Keeping Unit) data
5. **stock.json** - Inventory/stock data

## Test Data Characteristics

### Edge Cases Included

1. **Duplicates**: Each entity includes duplicate records with the same ID but different `dateModified` timestamps to test deduplication logic
2. **NULL values**: Records with NULL/null values in optional fields to test NULL handling
3. **Empty arrays/objects**: Records with empty arrays (`[]`) and empty objects (`{}`) to test edge cases
4. **Nested structures**: Orders include nested JSON objects (totals, shipping, customer, customData) to test JSON flattening
5. **Arrays**: Orders include items arrays to test array explosion into child tables
6. **Timestamps**: Mix of Unix timestamps (integers) and ISO 8601 strings to test type conversion
7. **Missing fields**: Some records have missing optional fields to test data gap handling

### Data Relationships

- **orders** → **order-items**: Parent-child relationship via `order_id`
- **products** → **skus**: Parent-child relationship via `product_id`
- **skus** → **stock**: Relationship via `sku` field

### Record Counts

- **orders**: 3 records (1 duplicate)
- **order-items**: 4 records (1 duplicate)
- **products**: 4 records (1 duplicate)
- **skus**: 4 records (1 duplicate)
- **stock**: 5 records (1 duplicate)

## Expected Behavior After Deduplication

After deduplication (keeping most recent `dateModified`):

- **orders**: 2 unique records
- **order-items**: 3 unique records
- **products**: 3 unique records
- **skus**: 3 unique records
- **stock**: 4 unique records

## Usage

These fixtures are used by:

1. `max/scripts/test_end_to_end.py` - End-to-end pipeline testing
2. Unit tests in `max/glue/etl-bronze-to-silver/tests/`
3. Integration tests in `max/glue/etl-silver-to-gold/tests/`

## Data Format

All files are in JSON format with arrays of objects. Each object represents a single record that would be ingested from the Bronze layer.

## Updating Fixtures

When updating fixtures:

1. Maintain the edge cases (duplicates, NULLs, empty structures)
2. Ensure relationships between entities remain valid
3. Update this README if adding new edge cases
4. Run `max/scripts/test_end_to_end.py` to verify changes don't break tests
