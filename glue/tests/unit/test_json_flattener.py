"""
Unit tests for JSONFlattener module

Tests basic functionality of JSON flattening for nested structures.
"""

import pytest
from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, StringType, IntegerType, ArrayType
from modules.json_flattener import JSONFlattener


@pytest.fixture(scope="module")
def spark():
    """Create a Spark session for testing."""
    return SparkSession.builder \
        .appName("test_json_flattener") \
        .master("local[2]") \
        .getOrCreate()


def test_flatten_simple_struct(spark):
    """Test flattening a simple nested struct."""
    # Arrange
    schema = StructType([
        StructField("id", IntegerType(), True),
        StructField("customer", StructType([
            StructField("name", StringType(), True),
            StructField("email", StringType(), True)
        ]), True)
    ])
    
    data = [
        (1, ("John Doe", "john@example.com")),
        (2, ("Jane Smith", "jane@example.com"))
    ]
    
    df = spark.createDataFrame(data, schema)
    flattener = JSONFlattener()
    
    # Act
    result = flattener.transform(df, {})
    
    # Assert
    assert "customer_name" in result.columns
    assert "customer_email" in result.columns
    assert "customer" not in result.columns
    assert result.count() == 2
    
    # Verify data
    first_row = result.filter(result.id == 1).collect()[0]
    assert first_row["customer_name"] == "John Doe"
    assert first_row["customer_email"] == "john@example.com"


def test_flatten_array(spark):
    """Test exploding array columns."""
    # Arrange
    schema = StructType([
        StructField("order_id", IntegerType(), True),
        StructField("items", ArrayType(StringType()), True)
    ])
    
    data = [
        (1, ["item1", "item2", "item3"]),
        (2, ["item4"])
    ]
    
    df = spark.createDataFrame(data, schema)
    flattener = JSONFlattener()
    
    # Act
    result = flattener.transform(df, {})
    
    # Assert
    assert result.count() == 4  # 3 items from order 1 + 1 item from order 2
    
    # Verify data
    order1_items = result.filter(result.order_id == 1).collect()
    assert len(order1_items) == 3


def test_flatten_nested_struct(spark):
    """Test flattening deeply nested structures."""
    # Arrange
    schema = StructType([
        StructField("id", IntegerType(), True),
        StructField("address", StructType([
            StructField("street", StringType(), True),
            StructField("city", StructType([
                StructField("name", StringType(), True),
                StructField("zip", StringType(), True)
            ]), True)
        ]), True)
    ])
    
    data = [
        (1, ("123 Main St", ("Springfield", "12345")))
    ]
    
    df = spark.createDataFrame(data, schema)
    flattener = JSONFlattener()
    
    # Act
    result = flattener.transform(df, {})
    
    # Assert
    assert "address_street" in result.columns
    assert "address_city_name" in result.columns
    assert "address_city_zip" in result.columns
    assert result.count() == 1


def test_flatten_empty_dataframe(spark):
    """Test flattening an empty DataFrame."""
    # Arrange
    schema = StructType([
        StructField("id", IntegerType(), True),
        StructField("data", StructType([
            StructField("value", StringType(), True)
        ]), True)
    ])
    
    df = spark.createDataFrame([], schema)
    flattener = JSONFlattener()
    
    # Act
    result = flattener.transform(df, {})
    
    # Assert
    assert result.count() == 0
    assert "data_value" in result.columns


def test_flatten_null_values(spark):
    """Test flattening with null values in nested structures."""
    # Arrange
    schema = StructType([
        StructField("id", IntegerType(), True),
        StructField("customer", StructType([
            StructField("name", StringType(), True),
            StructField("email", StringType(), True)
        ]), True)
    ])
    
    data = [
        (1, ("John Doe", "john@example.com")),
        (2, None)  # Null customer
    ]
    
    df = spark.createDataFrame(data, schema)
    flattener = JSONFlattener()
    
    # Act
    result = flattener.transform(df, {})
    
    # Assert
    assert result.count() == 2
    
    # Verify null handling
    null_row = result.filter(result.id == 2).collect()[0]
    assert null_row["customer_name"] is None
    assert null_row["customer_email"] is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
