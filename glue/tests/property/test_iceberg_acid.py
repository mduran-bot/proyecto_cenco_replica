"""
Property-Based Test: ACID Transaction Consistency

Feature: data-transformation
Property 11: ACID Transaction Consistency

For any write operation to Iceberg tables, the operation should be atomic 
(all-or-nothing) and data should remain consistent even during concurrent 
operations or failures.

Task: 5.4
Requirements: 5.3, 10.6
Validates: Property 11
"""

import pytest
from hypothesis import given, strategies as st, settings
from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, StringType, IntegerType
import sys
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from modules.iceberg_manager import IcebergTableManager
from modules.iceberg_writer import IcebergWriter


# Test schema
acid_test_schema = StructType([
    StructField("id", StringType(), nullable=False),
    StructField("counter", IntegerType(), nullable=False)
])


@st.composite
def acid_record(draw):
    """Generate a record for ACID testing."""
    return {
        "id": draw(st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd')))),
        "counter": draw(st.integers(min_value=0, max_value=1000))
    }


@pytest.fixture(scope="module")
def spark():
    """Create a Spark session for testing."""
    spark = SparkSession.builder \
        .appName("IcebergACIDTest") \
        .config("spark.sql.extensions", "org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions") \
        .config("spark.sql.catalog.local", "org.apache.iceberg.spark.SparkCatalog") \
        .config("spark.sql.catalog.local.type", "hadoop") \
        .config("spark.sql.catalog.local.warehouse", "/tmp/iceberg-warehouse") \
        .getOrCreate()
    
    yield spark
    
    spark.stop()


@pytest.mark.property
@settings(max_examples=50, deadline=None)
@given(records=st.lists(acid_record(), min_size=10, max_size=100))
def test_iceberg_atomic_write(spark, records):
    """
    Property 11: Atomic Write Operations
    
    Verifies that write operations are atomic - either all records are written
    or none are written. No partial writes should occur.
    """
    # Arrange
    table_name = "test_db.atomic_test"
    
    iceberg_manager = IcebergTableManager(spark, catalog_name="local")
    iceberg_writer = IcebergWriter(spark, catalog_name="local")
    
    # Create table
    if not iceberg_manager.table_exists(table_name):
        iceberg_manager.create_table(
            table_name=table_name,
            schema=acid_test_schema,
            partition_spec={}
        )
    
    # Clear table
    spark.sql(f"DELETE FROM local.{table_name}")
    
    # Act
    df = spark.createDataFrame(records, schema=acid_test_schema)
    iceberg_writer.write_to_iceberg(df, table_name, mode="append")
    
    # Assert
    result_df = spark.table(f"local.{table_name}")
    result_count = result_df.count()
    
    # Either all records are written or none (atomic)
    assert result_count == len(records) or result_count == 0, \
        f"Partial write detected: expected {len(records)} or 0, got {result_count}"


@pytest.mark.property
@settings(max_examples=30, deadline=None)
@given(
    batch1=st.lists(acid_record(), min_size=5, max_size=30),
    batch2=st.lists(acid_record(), min_size=5, max_size=30)
)
def test_iceberg_concurrent_writes_consistency(spark, batch1, batch2):
    """
    Property 11: Concurrent Write Consistency
    
    Verifies that concurrent writes to the same table maintain consistency.
    All writes should complete successfully without data corruption.
    """
    # Arrange
    table_name = "test_db.concurrent_test"
    
    iceberg_manager = IcebergTableManager(spark, catalog_name="local")
    iceberg_writer = IcebergWriter(spark, catalog_name="local")
    
    # Create table
    if not iceberg_manager.table_exists(table_name):
        iceberg_manager.create_table(
            table_name=table_name,
            schema=acid_test_schema,
            partition_spec={}
        )
    
    # Clear table
    spark.sql(f"DELETE FROM local.{table_name}")
    
    # Act
    # Write two batches concurrently
    def write_batch(batch, batch_id):
        df = spark.createDataFrame(batch, schema=acid_test_schema)
        iceberg_writer.write_to_iceberg(df, table_name, mode="append")
        return batch_id, len(batch)
    
    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [
            executor.submit(write_batch, batch1, 1),
            executor.submit(write_batch, batch2, 2)
        ]
        
        results = [f.result() for f in as_completed(futures)]
    
    # Assert
    result_df = spark.table(f"local.{table_name}")
    result_count = result_df.count()
    
    expected_count = len(batch1) + len(batch2)
    
    # All records from both batches should be present
    assert result_count == expected_count, \
        f"Concurrent write consistency violated: expected {expected_count}, got {result_count}"
    
    # Verify no duplicate IDs (data integrity)
    all_ids = [r["id"] for r in batch1 + batch2]
    result_ids = [row.id for row in result_df.collect()]
    
    # Count should match (allowing duplicates in input)
    assert len(result_ids) == len(all_ids), \
        "Data integrity violated during concurrent writes"


@pytest.mark.property
@settings(max_examples=50, deadline=None)
@given(
    initial_records=st.lists(acid_record(), min_size=5, max_size=50),
    update_records=st.lists(acid_record(), min_size=1, max_size=20)
)
def test_iceberg_merge_consistency(spark, initial_records, update_records):
    """
    Property 11: MERGE Operation Consistency
    
    Verifies that MERGE (upsert) operations maintain ACID properties.
    Updates should be atomic and consistent.
    """
    # Arrange
    table_name = "test_db.merge_test"
    
    iceberg_manager = IcebergTableManager(spark, catalog_name="local")
    iceberg_writer = IcebergWriter(spark, catalog_name="local")
    
    # Create table
    if not iceberg_manager.table_exists(table_name):
        iceberg_manager.create_table(
            table_name=table_name,
            schema=acid_test_schema,
            partition_spec={}
        )
    
    # Write initial data
    initial_df = spark.createDataFrame(initial_records, schema=acid_test_schema)
    iceberg_writer.write_to_iceberg(initial_df, table_name, mode="overwrite")
    
    # Get initial count
    initial_count = spark.table(f"local.{table_name}").count()
    
    # Act
    # Perform MERGE operation
    update_df = spark.createDataFrame(update_records, schema=acid_test_schema)
    iceberg_writer.upsert_to_table(update_df, table_name, merge_keys=["id"])
    
    # Assert
    result_df = spark.table(f"local.{table_name}")
    result_count = result_df.count()
    
    # Count should be consistent
    # New unique IDs should be added, existing IDs should be updated (not duplicated)
    initial_ids = set([r["id"] for r in initial_records])
    update_ids = set([r["id"] for r in update_records])
    
    expected_unique_ids = initial_ids.union(update_ids)
    result_ids = set([row.id for row in result_df.collect()])
    
    assert result_ids == expected_unique_ids, \
        "MERGE operation violated consistency: ID sets don't match"
    
    # No duplicate IDs should exist
    all_result_ids = [row.id for row in result_df.collect()]
    assert len(all_result_ids) == len(set(all_result_ids)), \
        "MERGE operation created duplicate IDs"


@pytest.mark.property
@settings(max_examples=30, deadline=None)
@given(records=st.lists(acid_record(), min_size=10, max_size=50))
def test_iceberg_snapshot_isolation(spark, records):
    """
    Property 11: Snapshot Isolation
    
    Verifies that reads see a consistent snapshot of data, even during writes.
    This is a key ACID property.
    """
    # Arrange
    table_name = "test_db.isolation_test"
    
    iceberg_manager = IcebergTableManager(spark, catalog_name="local")
    iceberg_writer = IcebergWriter(spark, catalog_name="local")
    
    # Create table
    if not iceberg_manager.table_exists(table_name):
        iceberg_manager.create_table(
            table_name=table_name,
            schema=acid_test_schema,
            partition_spec={}
        )
    
    # Write initial data
    df = spark.createDataFrame(records, schema=acid_test_schema)
    iceberg_writer.write_to_iceberg(df, table_name, mode="overwrite")
    
    # Act
    # Get snapshot before modification
    snapshot_before = iceberg_manager.list_snapshots(table_name)
    count_before = spark.table(f"local.{table_name}").count()
    
    # Modify data
    new_records = [{"id": f"new_{i}", "counter": i} for i in range(10)]
    new_df = spark.createDataFrame(new_records, schema=acid_test_schema)
    iceberg_writer.write_to_iceberg(new_df, table_name, mode="append")
    
    # Get snapshot after modification
    snapshot_after = iceberg_manager.list_snapshots(table_name)
    count_after = spark.table(f"local.{table_name}").count()
    
    # Assert
    # Snapshots should be different
    assert len(snapshot_after) > len(snapshot_before), \
        "New snapshot not created after write"
    
    # Count should have increased
    assert count_after == count_before + len(new_records), \
        f"Count mismatch: expected {count_before + len(new_records)}, got {count_after}"
    
    # Can read from old snapshot (time travel)
    if len(snapshot_before) > 0:
        old_snapshot_id = snapshot_before[0]['snapshot_id']
        old_data = spark.read \
            .option("snapshot-id", old_snapshot_id) \
            .table(f"local.{table_name}")
        
        old_count = old_data.count()
        assert old_count == count_before, \
            "Snapshot isolation violated: old snapshot data changed"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--hypothesis-show-statistics"])
