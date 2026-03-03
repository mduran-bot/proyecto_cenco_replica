"""
Tests for JSONFlattener advanced modes (child tables and key-value tables)
Task 8.1 - Advanced JSON handling tests
"""

import pytest
from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, StringType, IntegerType, ArrayType
import sys
import os

# Add parent directory to path to import modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from modules.json_flattener import JSONFlattener


@pytest.fixture(scope="module")
def spark():
    """Create a Spark session for testing."""
    spark = SparkSession.builder \
        .appName("JSONFlattener Advanced Tests") \
        .master("local[2]") \
        .getOrCreate()
    yield spark
    spark.stop()


def test_explode_to_child_table_mode(spark):
    """Test explode_to_child_table mode creates separate child tables."""
    # Create test data with nested array
    schema = StructType([
        StructField("id", StringType(), False),
        StructField("store_id", StringType(), False),
        StructField("items", ArrayType(StructType([
            StructField("sku", StringType(), False),
            StructField("quantity", IntegerType(), False)
        ])), True)
    ])
    
    data = [
        ("order1", "store1", [
            {"sku": "SKU001", "quantity": 2},
            {"sku": "SKU002", "quantity": 1}
        ]),
        ("order2", "store1", [
            {"sku": "SKU003", "quantity": 5}
        ])
    ]
    
    df = spark.createDataFrame(data, schema)
    
    # Configure flattener
    flattener = JSONFlattener()
    config = {
        "mode": "explode_to_child_table",
        "parent_key": "id",
        "child_table_configs": {
            "items": {
                "child_table_name": "order_items",
                "foreign_key": "order_id"
            }
        }
    }
    
    # Transform
    parent_df = flattener.transform(df, config)
    
    # Verify parent table
    assert "items" not in parent_df.columns, "Array column should be removed from parent"
    assert "id" in parent_df.columns
    assert "store_id" in parent_df.columns
    assert parent_df.count() == 2
    
    # Verify child table
    child_tables = flattener.get_child_tables()
    assert "order_items" in child_tables
    
    child_df = child_tables["order_items"]
    assert "order_id" in child_df.columns
    assert "sku" in child_df.columns
    assert "quantity" in child_df.columns
    assert child_df.count() == 3  # 2 items from order1 + 1 item from order2
    
    # Verify foreign key relationships
    child_rows = child_df.collect()
    order_ids = [row.order_id for row in child_rows]
    assert "order1" in order_ids
    assert "order2" in order_ids


def test_key_value_table_mode(spark):
    """Test key_value_table mode converts dynamic objects to key-value pairs."""
    # Create test data with dynamic object
    schema = StructType([
        StructField("id", StringType(), False),
        StructField("customData", StructType([
            StructField("delivery_notes", StringType(), True),
            StructField("gift_wrap", StringType(), True),
            StructField("special_instructions", StringType(), True)
        ]), True)
    ])
    
    data = [
        ("order1", {"delivery_notes": "Ring doorbell", "gift_wrap": "true", "special_instructions": "Leave at door"}),
        ("order2", {"delivery_notes": "Call on arrival", "gift_wrap": "false", "special_instructions": None})
    ]
    
    df = spark.createDataFrame(data, schema)
    
    # Configure flattener
    flattener = JSONFlattener()
    config = {
        "mode": "key_value_table",
        "parent_key": "id",
        "key_value_columns": ["customData"],
        "key_value_table_configs": {
            "customData": {
                "table_name": "order_custom_data_fields",
                "foreign_key": "order_id"
            }
        }
    }
    
    # Transform
    parent_df = flattener.transform(df, config)
    
    # Verify parent table
    assert "customData" not in parent_df.columns, "Object column should be removed from parent"
    assert "id" in parent_df.columns
    assert parent_df.count() == 2
    
    # Verify key-value table
    kv_tables = flattener.get_key_value_tables()
    assert "order_custom_data_fields" in kv_tables
    
    kv_df = kv_tables["order_custom_data_fields"]
    assert "order_id" in kv_df.columns
    assert "field" in kv_df.columns
    assert "value" in kv_df.columns
    
    # Should have 6 rows (3 fields × 2 orders)
    assert kv_df.count() == 6
    
    # Verify field names
    kv_rows = kv_df.collect()
    field_names = [row.field for row in kv_rows]
    assert "delivery_notes" in field_names
    assert "gift_wrap" in field_names
    assert "special_instructions" in field_names


def test_standard_mode_still_works(spark):
    """Test that standard mode still works as before."""
    # Create test data with nested struct
    schema = StructType([
        StructField("id", StringType(), False),
        StructField("address", StructType([
            StructField("city", StringType(), True),
            StructField("country", StringType(), True)
        ]), True)
    ])
    
    data = [
        ("order1", {"city": "Lima", "country": "Peru"}),
        ("order2", {"city": "Santiago", "country": "Chile"})
    ]
    
    df = spark.createDataFrame(data, schema)
    
    # Configure flattener with standard mode
    flattener = JSONFlattener()
    config = {"mode": "standard"}
    
    # Transform
    result_df = flattener.transform(df, config)
    
    # Verify flattening
    assert "address" not in result_df.columns
    assert "address_city" in result_df.columns
    assert "address_country" in result_df.columns
    assert result_df.count() == 2


def test_multiple_child_tables(spark):
    """Test creating multiple child tables from one parent."""
    # Create test data with multiple arrays
    schema = StructType([
        StructField("id", StringType(), False),
        StructField("items", ArrayType(StructType([
            StructField("sku", StringType(), False)
        ])), True),
        StructField("payments", ArrayType(StructType([
            StructField("method", StringType(), False)
        ])), True)
    ])
    
    data = [
        ("order1", [{"sku": "SKU001"}], [{"method": "credit_card"}, {"method": "gift_card"}])
    ]
    
    df = spark.createDataFrame(data, schema)
    
    # Configure flattener
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
    
    # Transform
    parent_df = flattener.transform(df, config)
    
    # Verify both child tables were created
    child_tables = flattener.get_child_tables()
    assert "order_items" in child_tables
    assert "order_payments" in child_tables
    
    assert child_tables["order_items"].count() == 1
    assert child_tables["order_payments"].count() == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
