"""
Unit tests for ConflictResolver module

Tests conflict resolution for duplicate records.
"""

import pytest
from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, StringType, IntegerType, TimestampType
from datetime import datetime
from modules.conflict_resolver import ConflictResolver


@pytest.fixture(scope="module")
def spark():
    """Create a Spark session for testing."""
    return SparkSession.builder \
        .appName("test_conflict_resolver") \
        .master("local[2]") \
        .getOrCreate()


def test_resolve_by_timestamp(spark):
    """Test resolving conflicts by most recent timestamp."""
    # Arrange
    schema = StructType([
        StructField("order_id", StringType(), True),
        StructField("amount", IntegerType(), True),
        StructField("timestamp", TimestampType(), True),
        StructField("is_duplicate", StringType(), True),  # Using StringType for boolean
        StructField("duplicate_group_id", IntegerType(), True)
    ])
    
    data = [
        ("1", 100, datetime(2024, 1, 1, 10, 0, 0), "true", 1),
        ("1", 150, datetime(2024, 1, 1, 12, 0, 0), "true", 1),  # Most recent - should be kept
        ("2", 200, datetime(2024, 1, 1, 10, 0, 0), "false", 2)
    ]
    
    df = spark.createDataFrame(data, schema)
    
    # Convert string boolean to actual boolean
    from pyspark.sql.functions import col, when
    df = df.withColumn("is_duplicate", when(col("is_duplicate") == "true", True).otherwise(False))
    
    resolver = ConflictResolver()
    config = {
        "conflict_resolution": {
            "timestamp_column": "timestamp"
        }
    }
    
    # Act
    result = resolver.transform(df, config)
    
    # Assert
    assert result.count() == 2  # One duplicate resolved
    assert "is_duplicate" not in result.columns
    assert "duplicate_group_id" not in result.columns
    
    # Verify the most recent record was kept
    order1 = result.filter(result.order_id == "1").collect()
    assert len(order1) == 1
    assert order1[0]["amount"] == 150  # Most recent amount


def test_resolve_by_null_count(spark):
    """Test resolving conflicts by fewest null values."""
    # Arrange
    schema = StructType([
        StructField("order_id", StringType(), True),
        StructField("name", StringType(), True),
        StructField("email", StringType(), True),
        StructField("phone", StringType(), True),
        StructField("is_duplicate", StringType(), True),
        StructField("duplicate_group_id", IntegerType(), True)
    ])
    
    data = [
        ("1", "John", None, None, "true", 1),  # 2 nulls
        ("1", "John", "john@example.com", "+123", "true", 1),  # 0 nulls - should be kept
        ("2", "Jane", "jane@example.com", None, "false", 2)
    ]
    
    df = spark.createDataFrame(data, schema)
    
    # Convert string boolean to actual boolean
    from pyspark.sql.functions import col, when
    df = df.withColumn("is_duplicate", when(col("is_duplicate") == "true", True).otherwise(False))
    
    resolver = ConflictResolver()
    config = {}  # No timestamp column
    
    # Act
    result = resolver.transform(df, config)
    
    # Assert
    assert result.count() == 2
    
    # Verify record with fewest nulls was kept
    order1 = result.filter(result.order_id == "1").collect()
    assert len(order1) == 1
    assert order1[0]["email"] == "john@example.com"
    assert order1[0]["phone"] == "+123"


def test_no_duplicates(spark):
    """Test with DataFrame that has no duplicates."""
    # Arrange
    schema = StructType([
        StructField("order_id", StringType(), True),
        StructField("amount", IntegerType(), True)
    ])
    
    data = [
        ("1", 100),
        ("2", 200),
        ("3", 300)
    ]
    
    df = spark.createDataFrame(data, schema)
    resolver = ConflictResolver()
    config = {}
    
    # Act
    result = resolver.transform(df, config)
    
    # Assert
    assert result.count() == 3
    assert result.columns == ["order_id", "amount"]


def test_missing_duplicate_columns(spark):
    """Test with DataFrame missing duplicate marking columns."""
    # Arrange
    schema = StructType([
        StructField("order_id", StringType(), True),
        StructField("amount", IntegerType(), True)
    ])
    
    data = [
        ("1", 100),
        ("2", 200)
    ]
    
    df = spark.createDataFrame(data, schema)
    resolver = ConflictResolver()
    config = {}
    
    # Act
    result = resolver.transform(df, config)
    
    # Assert - should return DataFrame unchanged
    assert result.count() == 2
    assert result.columns == ["order_id", "amount"]


def test_invalid_timestamp_column(spark):
    """Test with invalid timestamp column in config."""
    # Arrange
    schema = StructType([
        StructField("order_id", StringType(), True),
        StructField("amount", IntegerType(), True),
        StructField("is_duplicate", StringType(), True),
        StructField("duplicate_group_id", IntegerType(), True)
    ])
    
    data = [
        ("1", 100, "true", 1),
        ("1", 150, "true", 1)
    ]
    
    df = spark.createDataFrame(data, schema)
    
    # Convert string boolean to actual boolean
    from pyspark.sql.functions import col, when
    df = df.withColumn("is_duplicate", when(col("is_duplicate") == "true", True).otherwise(False))
    
    resolver = ConflictResolver()
    config = {
        "conflict_resolution": {
            "timestamp_column": "nonexistent_column"
        }
    }
    
    # Act - should not raise error, just ignore invalid timestamp column
    result = resolver.transform(df, config)
    
    # Assert
    assert result.count() == 1  # One duplicate resolved


def test_multiple_duplicate_groups(spark):
    """Test resolving multiple duplicate groups."""
    # Arrange
    schema = StructType([
        StructField("order_id", StringType(), True),
        StructField("amount", IntegerType(), True),
        StructField("timestamp", TimestampType(), True),
        StructField("is_duplicate", StringType(), True),
        StructField("duplicate_group_id", IntegerType(), True)
    ])
    
    data = [
        ("1", 100, datetime(2024, 1, 1, 10, 0, 0), "true", 1),
        ("1", 150, datetime(2024, 1, 1, 12, 0, 0), "true", 1),  # Group 1 - keep this
        ("2", 200, datetime(2024, 1, 1, 10, 0, 0), "true", 2),
        ("2", 250, datetime(2024, 1, 1, 11, 0, 0), "true", 2),  # Group 2 - keep this
        ("3", 300, datetime(2024, 1, 1, 10, 0, 0), "false", 3)
    ]
    
    df = spark.createDataFrame(data, schema)
    
    # Convert string boolean to actual boolean
    from pyspark.sql.functions import col, when
    df = df.withColumn("is_duplicate", when(col("is_duplicate") == "true", True).otherwise(False))
    
    resolver = ConflictResolver()
    config = {
        "conflict_resolution": {
            "timestamp_column": "timestamp"
        }
    }
    
    # Act
    result = resolver.transform(df, config)
    
    # Assert
    assert result.count() == 3  # 2 duplicates resolved + 1 non-duplicate
    
    # Verify correct records kept
    order1 = result.filter(result.order_id == "1").collect()
    assert order1[0]["amount"] == 150
    
    order2 = result.filter(result.order_id == "2").collect()
    assert order2[0]["amount"] == 250


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
