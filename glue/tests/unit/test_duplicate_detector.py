"""
Unit tests for DuplicateDetector module

Tests duplicate detection based on business key columns.
"""

import pytest
from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, StringType, IntegerType
from modules.duplicate_detector import DuplicateDetector


@pytest.fixture(scope="module")
def spark():
    """Create a Spark session for testing."""
    return SparkSession.builder \
        .appName("test_duplicate_detector") \
        .master("local[2]") \
        .getOrCreate()


def test_detect_duplicates_single_key(spark):
    """Test detecting duplicates with a single key column."""
    # Arrange
    schema = StructType([
        StructField("order_id", StringType(), True),
        StructField("amount", IntegerType(), True),
        StructField("status", StringType(), True)
    ])
    
    data = [
        ("1", 100, "pending"),
        ("1", 100, "completed"),  # Duplicate
        ("2", 200, "pending"),
        ("3", 300, "completed")
    ]
    
    df = spark.createDataFrame(data, schema)
    detector = DuplicateDetector()
    config = {
        "duplicate_detection": {
            "key_columns": ["order_id"]
        }
    }
    
    # Act
    result = detector.transform(df, config)
    
    # Assert
    assert "is_duplicate" in result.columns
    assert "duplicate_group_id" in result.columns
    
    # Check duplicate marking
    duplicates = result.filter(result.is_duplicate == True).collect()
    assert len(duplicates) == 2  # Both records with order_id=1
    
    non_duplicates = result.filter(result.is_duplicate == False).collect()
    assert len(non_duplicates) == 2  # order_id=2 and order_id=3


def test_detect_duplicates_multiple_keys(spark):
    """Test detecting duplicates with multiple key columns."""
    # Arrange
    schema = StructType([
        StructField("order_id", StringType(), True),
        StructField("item_id", StringType(), True),
        StructField("quantity", IntegerType(), True)
    ])
    
    data = [
        ("1", "A", 10),
        ("1", "A", 15),  # Duplicate (same order_id and item_id)
        ("1", "B", 20),  # Not duplicate (different item_id)
        ("2", "A", 30)   # Not duplicate (different order_id)
    ]
    
    df = spark.createDataFrame(data, schema)
    detector = DuplicateDetector()
    config = {
        "duplicate_detection": {
            "key_columns": ["order_id", "item_id"]
        }
    }
    
    # Act
    result = detector.transform(df, config)
    
    # Assert
    duplicates = result.filter(result.is_duplicate == True).collect()
    assert len(duplicates) == 2  # order_id=1, item_id=A (both records)
    
    non_duplicates = result.filter(result.is_duplicate == False).collect()
    assert len(non_duplicates) == 2


def test_assign_group_ids(spark):
    """Test that duplicate groups get unique group IDs."""
    # Arrange
    schema = StructType([
        StructField("order_id", StringType(), True),
        StructField("amount", IntegerType(), True)
    ])
    
    data = [
        ("1", 100),
        ("1", 150),  # Duplicate group 1
        ("2", 200),
        ("2", 250),  # Duplicate group 2
        ("3", 300)   # No duplicate
    ]
    
    df = spark.createDataFrame(data, schema)
    detector = DuplicateDetector()
    config = {
        "duplicate_detection": {
            "key_columns": ["order_id"]
        }
    }
    
    # Act
    result = detector.transform(df, config)
    
    # Assert
    # Get unique group IDs for duplicates
    group_ids = result.filter(result.is_duplicate == True) \
                      .select("duplicate_group_id") \
                      .distinct() \
                      .collect()
    
    assert len(group_ids) == 2  # Two duplicate groups
    
    # Verify same order_id has same group_id
    order1_groups = result.filter(result.order_id == "1") \
                          .select("duplicate_group_id") \
                          .distinct() \
                          .collect()
    assert len(order1_groups) == 1  # All order_id=1 have same group_id


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
    detector = DuplicateDetector()
    config = {
        "duplicate_detection": {
            "key_columns": ["order_id"]
        }
    }
    
    # Act
    result = detector.transform(df, config)
    
    # Assert
    duplicates = result.filter(result.is_duplicate == True).collect()
    assert len(duplicates) == 0
    
    non_duplicates = result.filter(result.is_duplicate == False).collect()
    assert len(non_duplicates) == 3


def test_missing_key_columns_config(spark):
    """Test error handling when key_columns not specified."""
    # Arrange
    schema = StructType([
        StructField("order_id", StringType(), True)
    ])
    
    df = spark.createDataFrame([("1",)], schema)
    detector = DuplicateDetector()
    config = {}  # No duplicate_detection config
    
    # Act & Assert
    with pytest.raises(ValueError, match="key_columns must be specified"):
        detector.transform(df, config)


def test_invalid_key_columns(spark):
    """Test error handling when key columns don't exist in DataFrame."""
    # Arrange
    schema = StructType([
        StructField("order_id", StringType(), True)
    ])
    
    df = spark.createDataFrame([("1",)], schema)
    detector = DuplicateDetector()
    config = {
        "duplicate_detection": {
            "key_columns": ["invalid_column"]
        }
    }
    
    # Act & Assert
    with pytest.raises(ValueError, match="Key columns not found"):
        detector.transform(df, config)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
