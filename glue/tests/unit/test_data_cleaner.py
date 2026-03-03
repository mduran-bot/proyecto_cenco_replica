"""
Unit tests for DataCleaner module

Tests data cleaning functionality including trimming, null conversion, and encoding fixes.
"""

import pytest
from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, StringType, IntegerType
from modules.data_cleaner import DataCleaner


@pytest.fixture(scope="module")
def spark():
    """Create a Spark session for testing."""
    return SparkSession.builder \
        .appName("test_data_cleaner") \
        .master("local[2]") \
        .getOrCreate()


def test_trim_strings(spark):
    """Test trimming whitespace from string columns."""
    # Arrange
    schema = StructType([
        StructField("id", IntegerType(), True),
        StructField("name", StringType(), True),
        StructField("email", StringType(), True)
    ])
    
    data = [
        (1, "  John Doe  ", "  john@example.com  "),
        (2, "Jane Smith", "jane@example.com  "),
        (3, "  Bob Wilson", "bob@example.com")
    ]
    
    df = spark.createDataFrame(data, schema)
    cleaner = DataCleaner()
    
    # Act
    result = cleaner.transform(df, {})
    
    # Assert
    rows = result.collect()
    assert rows[0]["name"] == "John Doe"
    assert rows[0]["email"] == "john@example.com"
    assert rows[1]["name"] == "Jane Smith"
    assert rows[1]["email"] == "jane@example.com"
    assert rows[2]["name"] == "Bob Wilson"
    assert rows[2]["email"] == "bob@example.com"


def test_empty_to_null(spark):
    """Test converting empty strings to null."""
    # Arrange
    schema = StructType([
        StructField("id", IntegerType(), True),
        StructField("name", StringType(), True),
        StructField("email", StringType(), True)
    ])
    
    data = [
        (1, "John Doe", ""),
        (2, "", "jane@example.com"),
        (3, "Bob Wilson", "bob@example.com")
    ]
    
    df = spark.createDataFrame(data, schema)
    cleaner = DataCleaner()
    
    # Act
    result = cleaner.transform(df, {})
    
    # Assert
    rows = result.collect()
    assert rows[0]["name"] == "John Doe"
    assert rows[0]["email"] is None
    assert rows[1]["name"] is None
    assert rows[1]["email"] == "jane@example.com"
    assert rows[2]["name"] == "Bob Wilson"
    assert rows[2]["email"] == "bob@example.com"


def test_preserve_non_string_columns(spark):
    """Test that non-string columns are preserved unchanged."""
    # Arrange
    schema = StructType([
        StructField("id", IntegerType(), True),
        StructField("name", StringType(), True),
        StructField("age", IntegerType(), True)
    ])
    
    data = [
        (1, "  John Doe  ", 30),
        (2, "Jane Smith", 25)
    ]
    
    df = spark.createDataFrame(data, schema)
    cleaner = DataCleaner()
    
    # Act
    result = cleaner.transform(df, {})
    
    # Assert
    rows = result.collect()
    assert rows[0]["id"] == 1
    assert rows[0]["age"] == 30
    assert rows[1]["id"] == 2
    assert rows[1]["age"] == 25


def test_clean_empty_dataframe(spark):
    """Test cleaning an empty DataFrame."""
    # Arrange
    schema = StructType([
        StructField("id", IntegerType(), True),
        StructField("name", StringType(), True)
    ])
    
    df = spark.createDataFrame([], schema)
    cleaner = DataCleaner()
    
    # Act
    result = cleaner.transform(df, {})
    
    # Assert
    assert result.count() == 0
    assert result.columns == ["id", "name"]


def test_clean_all_null_values(spark):
    """Test cleaning DataFrame with all null values."""
    # Arrange
    schema = StructType([
        StructField("id", IntegerType(), True),
        StructField("name", StringType(), True),
        StructField("email", StringType(), True)
    ])
    
    data = [
        (1, None, None),
        (2, None, None)
    ]
    
    df = spark.createDataFrame(data, schema)
    cleaner = DataCleaner()
    
    # Act
    result = cleaner.transform(df, {})
    
    # Assert
    assert result.count() == 2
    rows = result.collect()
    assert rows[0]["name"] is None
    assert rows[0]["email"] is None


def test_combined_cleaning(spark):
    """Test all cleaning operations together."""
    # Arrange
    schema = StructType([
        StructField("id", IntegerType(), True),
        StructField("name", StringType(), True),
        StructField("email", StringType(), True),
        StructField("phone", StringType(), True)
    ])
    
    data = [
        (1, "  John Doe  ", "", "  +1234567890  "),
        (2, "", "jane@example.com", None),
        (3, "  Bob Wilson  ", "  bob@example.com  ", "")
    ]
    
    df = spark.createDataFrame(data, schema)
    cleaner = DataCleaner()
    
    # Act
    result = cleaner.transform(df, {})
    
    # Assert
    rows = result.collect()
    
    # Row 1: trimmed name, empty email to null, trimmed phone
    assert rows[0]["name"] == "John Doe"
    assert rows[0]["email"] is None
    assert rows[0]["phone"] == "+1234567890"
    
    # Row 2: empty name to null, email preserved, null phone preserved
    assert rows[1]["name"] is None
    assert rows[1]["email"] == "jane@example.com"
    assert rows[1]["phone"] is None
    
    # Row 3: trimmed name, trimmed email, empty phone to null
    assert rows[2]["name"] == "Bob Wilson"
    assert rows[2]["email"] == "bob@example.com"
    assert rows[2]["phone"] is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
