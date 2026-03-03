# Parent-Child Relations Configuration

This document explains how to configure and use parent-child relationships in the ETL pipeline for handling nested arrays and dynamic objects.

## Overview

The `entities_mapping.json` file now includes a `parent_child_relations` section for each entity that defines how nested structures should be handled during transformation.

## Relationship Types

### 1. one_to_many
Used when a parent record has an array of child records.

**Example: orders → order-items**
```json
{
  "orders": {
    "parent_child_relations": {
      "items": {
        "child_entity": "order-items",
        "child_table": "order_items_clean",
        "foreign_key": "order_id",
        "relationship_type": "one_to_many"
      }
    }
  }
}
```

**Input JSON:**
```json
{
  "id": "123",
  "items": [
    {"sku": "A1", "quantity": 2},
    {"sku": "A2", "quantity": 1}
  ]
}
```

**Output:**
- Parent table `orders_clean`: `id=123` (without items array)
- Child table `order_items_clean`:
  - `order_id=123, sku=A1, quantity=2`
  - `order_id=123, sku=A2, quantity=1`

### 2. one_to_one
Used when a parent record has a single nested object.

**Example: orders → order-shipping**
```json
{
  "orders": {
    "parent_child_relations": {
      "shipping": {
        "child_entity": "order-shipping",
        "child_table": "order_shipping_clean",
        "foreign_key": "order_id",
        "relationship_type": "one_to_one"
      }
    }
  }
}
```

**Input JSON:**
```json
{
  "id": "123",
  "shipping": {
    "carrier": "DHL",
    "trackingNumber": "ABC123"
  }
}
```

**Output:**
- Parent table `orders_clean`: `id=123` (without shipping object)
- Child table `order_shipping_clean`: `order_id=123, carrier=DHL, trackingNumber=ABC123`

### 3. key_value
Used when a parent record has a dynamic object with unknown keys.

**Example: orders → customData**
```json
{
  "orders": {
    "parent_child_relations": {
      "customData": {
        "child_entity": "order-custom-data-fields",
        "child_table": "order_custom_data_fields_clean",
        "foreign_key": "order_id",
        "relationship_type": "key_value"
      }
    }
  }
}
```

**Input JSON:**
```json
{
  "id": "123",
  "customData": {
    "delivery_notes": "Ring doorbell",
    "gift_wrap": "true",
    "special_instructions": "Leave at door"
  }
}
```

**Output:**
- Parent table `orders_clean`: `id=123` (without customData object)
- Child table `order_custom_data_fields_clean`:
  - `order_id=123, field=delivery_notes, value=Ring doorbell`
  - `order_id=123, field=gift_wrap, value=true`
  - `order_id=123, field=special_instructions, value=Leave at door`

## Configuration Fields

### Required Fields
- `child_entity`: Name of the child entity type (matches Bronze prefix)
- `child_table`: Name of the Silver table for child records
- `foreign_key`: Column name for the foreign key in child table
- `relationship_type`: Type of relationship (one_to_many, one_to_one, key_value)

### Optional Fields
- `note`: Documentation about the relationship

## Usage in JSONFlattener

### Mode: explode_to_child_table

Use this mode to create separate child tables for array columns:

```python
from modules.json_flattener import JSONFlattener

flattener = JSONFlattener()

config = {
    "mode": "explode_to_child_table",
    "parent_key": "id",
    "child_table_configs": {
        "items": {
            "child_table_name": "order_items",
            "foreign_key": "order_id"
        },
        "payments": {
            "child_table_name": "order_payments",
            "foreign_key": "order_id"
        }
    }
}

# Transform parent DataFrame
parent_df = flattener.transform(orders_df, config)

# Get child tables
child_tables = flattener.get_child_tables()
order_items_df = child_tables["order_items"]
order_payments_df = child_tables["order_payments"]
```

### Mode: key_value_table

Use this mode to convert dynamic objects to key-value tables:

```python
config = {
    "mode": "key_value_table",
    "parent_key": "id",
    "key_value_columns": ["customData", "metadata"],
    "key_value_table_configs": {
        "customData": {
            "table_name": "order_custom_data_fields",
            "foreign_key": "order_id"
        }
    }
}

# Transform parent DataFrame
parent_df = flattener.transform(orders_df, config)

# Get key-value tables
kv_tables = flattener.get_key_value_tables()
custom_data_df = kv_tables["order_custom_data_fields"]
```

## Complete Entity Hierarchy

### Orders Domain
```
orders (parent)
├── order-items (one_to_many)
│   └── order-item-weighables (one_to_many)
├── order-payments (one_to_many)
│   └── order-payments-connector-responses (key_value)
├── order-shipping (one_to_one)
├── order-status-changes (one_to_many)
├── order-custom-data-fields (key_value)
└── invoices (one_to_one)
```

### Products Domain
```
products (parent)
└── skus (one_to_many)
```

### Picking Domain
```
picking-sessions (parent)
└── picking-round-orders (one_to_many)
```

### Delivery Domain
```
delivery-planning (parent)
└── delivery-ranges (one_to_many)
```

## Foreign Key Preservation

The JSONFlattener automatically preserves foreign key relationships:

1. **Parent Key**: The primary key from the parent table (e.g., `id`, `order_id`)
2. **Foreign Key**: The same value stored in the child table with the configured foreign key name
3. **Referential Integrity**: Child records always reference an existing parent record

## Best Practices

1. **Always define parent_key**: Specify the primary key column name in the config
2. **Use descriptive foreign_key names**: Follow naming convention `{parent}_id` (e.g., `order_id`, `product_id`)
3. **Document dynamic fields**: Add notes for key_value relationships to explain the data structure
4. **Test with sample data**: Verify parent-child relationships with small datasets before processing full data
5. **Monitor child table sizes**: Arrays can significantly increase row counts in child tables

## Troubleshooting

### Issue: Child table is empty
- Check if the array column exists in the parent DataFrame
- Verify the array column name matches the configuration
- Ensure the array is not null or empty in all records

### Issue: Foreign key values don't match
- Verify parent_key is correctly specified in config
- Check that parent records have non-null primary keys
- Ensure foreign_key name doesn't conflict with existing columns

### Issue: Key-value table has unexpected values
- Verify the object column is a struct or map type
- Check for nested objects within the dynamic object
- Ensure all values can be cast to string type

## Examples

See the test files for complete examples:
- `tests/test_json_flattener_child_tables.py`
- `tests/test_json_flattener_key_value.py`
