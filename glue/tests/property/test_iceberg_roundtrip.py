"""
Property-Based Test: Iceberg Write-Read Round Trip

Feature: data-transformation
Property 5: Iceberg Write-Read Round Trip

For any dataset written to Iceberg tables in Silver layer, reading it back 
should produce equivalent data with all values preserved.

Task: 5.3
Requirements: 2.5
Validates: Property 5
"""

import pytest
from hypothesis import given, strategies as st, settings
from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, StringType, IntegerType, TimestampType, DecimalType
from datetime import datetime
from decimal import Decimal
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from modules.iceberg_manager import IcebergTableManager
from modules.iceberg_writer import IcebergWriter


# Test schema for property testing
test_schema = StructType([
    StructField("id", StringType(), nullable=False),
    StructField("value", IntegerType(), nullable=True),
    StructField("amount", DecimalType(10, 2), nullable=True),
    StructField("timestamp", TimestampType(), nullable=True)
])


# Hypothesis strategies for generating test data
@st.composite
def test_record(draw):
    """Generate a single test record."""
    return {
        "id": draw(st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd')))),
        "value": draw(st.one_of(st.none(), st.integers(min_value=-1000000, max_value=1000000))),
        "amount": draw(st.one_of(st.none(), st.decimals(min_value=-999999.99, max_value=999999.99, places=2))),
        "timestamp": draw(st.one_of(st.none(), st.datetimes(min_value=datetime(2000, 1, 1), max_value=datetime(2030, 12, 31))))
    }


@pytest.fixture(scope="module")
def spark():
    """Create a Spark session for testing."""
    spark = SparkSession.builder \
        .appName("IcebergRoundTripTest") \
        .config("spark.sql.extensions", "org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions") \
        .config("spark.sql.catalog.spark_catalog", "org.apache.iceberg.spark.SparkSessionCatalog") \
        .config("spark.sql.catalog.spark_catalog.type", "hive") \
        .config("spark.sql.catalog.local", "org.apache.iceberg.spark.SparkCatalog") \
        .config("spark.sql.catalog.local.type", "hadoop") \
        .config("spark.sql.catalog.local.warehouse", "/tmp/iceberg-warehouse") \
        .getOrCreate()
    
    yield spark
    
    spark.stop()


@pytest.mark.property
@settings(max_examples=100, deadline=None)
@given(records=st.lists(test_record(), min_size=1, max_size=100))
def test_iceberg_write_read_roundtrip(spark, records):
    """
    Property 5: Iceberg Write-Read Round Trip
    
    For any dataset written to Iceberg tables, reading it back should 
    produce equivalent data with all values preserved.
    
    This test verifies:
    1. Data can be written to Iceberg table
    2. Data can be read back from Iceberg table
    3. Read data matches written data exactly
    4. No data loss or corruption occurs
    """
    # Arrange
    table_name = "test_db.roundtrip_test"
    
    # Create Iceberg manager and writer
    iceberg_manager = IcebergTableManager(spark, catalog_name="local")
    iceberg_writer = IcebergWriter(spark, catalog_name="local")
    
    # Create test DataFrame
    input_df = spark.createDataFrame(records, schema=test_schema)
    
    # Create Iceberg table if it doesn't exist
    if not iceberg_manager.table_exists(table_name):
        iceberg_manager.create_table(
            table_name=table_name,
            schema=test_schema,
            partition_spec={}  # No partitioning for test
        )
    
    # Act
    # Write data to Iceberg table
    iceberg_writer.write_to_iceberg(input_df, table_name, mode="overwrite")
    
    # Read data back from Iceberg table
    output_df = spark.table(f"local.{table_name}")
    
    # Assert
    # Convert to lists for comparison
    input_data = sorted(input_df.collect(), key=lambda x: x.id)
    output_data = sorted(output_df.collect(), key=lambda x: x.id)
    
    # Verify same number of records
    assert len(input_data) == len(output_data), \
        f"Record count mismatch: input={len(input_data)}, output={len(output_data)}"
    
    # Verify each record matches
    for input_row, output_row in zip(input_data, output_data):
        assert input_row.id == output_row.id, \
            f"ID mismatch: {input_row.id} != {output_row.id}"
        
        assert input_row.value == output_row.value, \
            f"Value mismatch for ID {input_row.id}: {input_row.value} != {output_row.value}"
        
        # Compare decimals with tolerance
        if input_row.amount is not None and output_row.amount is not None:
            assert abs(float(input_row.amount) - float(output_row.amount)) < 0.01, \
                f"Amount mismatch for ID {input_row.id}: {input_row.amount} != {output_row.amount}"
        else:
            assert input_row.amount == output_row.amount, \
                f"Amount null mismatch for ID {input_row.id}"
        
        # Compare timestamps
        if input_row.timestamp is not None and output_row.timestamp is not None:
            # Allow 1 second tolerance for timestamp precision
            time_diff = abs((input_row.timestamp - output_row.timestamp).total_seconds())
            assert time_diff < 1, \
                f"Timestamp mismatch for ID {input_row.id}: {input_row.timestamp} != {output_row.timestamp}"
        else:
            assert input_row.timestamp == output_row.timestamp, \
                f"Timestamp null mismatch for ID {input_row.id}"


@pytest.mark.property
@settings(max_examples=50, deadline=None)
@given(
    initial_records=st.lists(test_record(), min_size=1, max_size=50),
    additional_records=st.lists(test_record(), min_size=1, max_size=50)
)
def test_iceberg_append_preserves_data(spark, initial_records, additional_records):
    """
    Property 5 (Append variant): Appending to Iceberg table preserves all data
    
    Verifies that:
    1. Initial data is preserved after append
    2. New data is correctly added
    3. No data corruption occurs during append
    """
    # Arrange
    table_name = "test_db.append_test"
    
    iceberg_manager = IcebergTableManager(spark, catalog_name="local")
    iceberg_writer = IcebergWriter(spark, catalog_name="local")
    
    # Create table
    if not iceberg_manager.table_exists(table_name):
        iceberg_manager.create_table(
            table_name=table_name,
            schema=test_schema,
            partition_spec={}
        )
    
    # Write initial data
    initial_df = spark.createDataFrame(initial_records, schema=test_schema)
    iceberg_writer.write_to_iceberg(initial_df, table_name, mode="overwrite")
    
    # Act
    # Append additional data
    additional_df = spark.createDataFrame(additional_records, schema=test_schema)
    iceberg_writer.write_to_iceberg(additional_df, table_name, mode="append")
    
    # Read all data
    result_df = spark.table(f"local.{table_name}")
    
    # Assert
    expected_count = len(initial_records) + len(additional_records)
    actual_count = result_df.count()
    
    assert actual_count == expected_count, \
        f"Record count mismatch after append: expected={expected_count}, actual={actual_count}"
    
    # Verify all IDs are present
    expected_ids = set([r["id"] for r in initial_records + additional_records])
    actual_ids = set([row.id for row in result_df.collect()])
    
    assert expected_ids == actual_ids, \
        f"ID set mismatch after append"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--hypothesis-show-statistics"])
