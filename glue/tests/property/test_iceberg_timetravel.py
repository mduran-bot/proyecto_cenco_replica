"""
Property-Based Test: Time Travel Snapshot Access

Feature: data-transformation
Property 12: Time Travel Snapshot Access

For any Iceberg table with historical snapshots, querying a past snapshot 
should return the data as it existed at that point in time.

Task: 5.5
Requirements: 5.4
Validates: Property 12
"""

import pytest
from hypothesis import given, strategies as st, settings
from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, StringType, IntegerType
import sys
import os
import time

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from modules.iceberg_manager import IcebergTableManager
from modules.iceberg_writer import IcebergWriter


# Test schema
timetravel_schema = StructType([
    StructField("id", StringType(), nullable=False),
    StructField("version", IntegerType(), nullable=False),
    StructField("data", StringType(), nullable=True)
])


@st.composite
def timetravel_record(draw, version):
    """Generate a record with specific version."""
    return {
        "id": draw(st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd')))),
        "version": version,
        "data": draw(st.text(min_size=0, max_size=100))
    }


@pytest.fixture(scope="module")
def spark():
    """Create a Spark session for testing."""
    spark = SparkSession.builder \
        .appName("IcebergTimeTravelTest") \
        .config("spark.sql.extensions", "org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions") \
        .config("spark.sql.catalog.local", "org.apache.iceberg.spark.SparkCatalog") \
        .config("spark.sql.catalog.local.type", "hadoop") \
        .config("spark.sql.catalog.local.warehouse", "/tmp/iceberg-warehouse") \
        .getOrCreate()
    
    yield spark
    
    spark.stop()


@pytest.mark.property
@settings(max_examples=30, deadline=None)
@given(
    version1_records=st.lists(timetravel_record(version=1), min_size=5, max_size=20),
    version2_records=st.lists(timetravel_record(version=2), min_size=5, max_size=20)
)
def test_iceberg_snapshot_time_travel(spark, version1_records, version2_records):
    """
    Property 12: Time Travel to Historical Snapshots
    
    Verifies that:
    1. Multiple snapshots can be created
    2. Each snapshot preserves data as it existed at that time
    3. Reading from old snapshots returns correct historical data
    """
    # Arrange
    table_name = "test_db.timetravel_test"
    
    iceberg_manager = IcebergTableManager(spark, catalog_name="local")
    iceberg_writer = IcebergWriter(spark, catalog_name="local")
    
    # Create table
    if not iceberg_manager.table_exists(table_name):
        iceberg_manager.create_table(
            table_name=table_name,
            schema=timetravel_schema,
            partition_spec={}
        )
    
    # Act
    # Write version 1 data
    v1_df = spark.createDataFrame(version1_records, schema=timetravel_schema)
    iceberg_writer.write_to_iceberg(v1_df, table_name, mode="overwrite")
    
    # Get snapshot after version 1
    snapshots_v1 = iceberg_manager.list_snapshots(table_name)
    snapshot_v1_id = snapshots_v1[0]['snapshot_id']
    
    # Small delay to ensure different timestamps
    time.sleep(0.1)
    
    # Write version 2 data (append)
    v2_df = spark.createDataFrame(version2_records, schema=timetravel_schema)
    iceberg_writer.write_to_iceberg(v2_df, table_name, mode="append")
    
    # Get snapshot after version 2
    snapshots_v2 = iceberg_manager.list_snapshots(table_name)
    
    # Assert
    # Should have at least 2 snapshots
    assert len(snapshots_v2) >= 2, \
        f"Expected at least 2 snapshots, got {len(snapshots_v2)}"
    
    # Read current data (should have both versions)
    current_data = spark.table(f"local.{table_name}")
    current_count = current_data.count()
    expected_current_count = len(version1_records) + len(version2_records)
    
    assert current_count == expected_current_count, \
        f"Current data count mismatch: expected {expected_current_count}, got {current_count}"
    
    # Read from version 1 snapshot (time travel)
    v1_snapshot_data = spark.read \
        .option("snapshot-id", snapshot_v1_id) \
        .table(f"local.{table_name}")
    
    v1_snapshot_count = v1_snapshot_data.count()
    
    # Version 1 snapshot should only have version 1 records
    assert v1_snapshot_count == len(version1_records), \
        f"Version 1 snapshot count mismatch: expected {len(version1_records)}, got {v1_snapshot_count}"
    
    # Verify version 1 snapshot contains only version 1 data
    v1_versions = [row.version for row in v1_snapshot_data.collect()]
    assert all(v == 1 for v in v1_versions), \
        "Version 1 snapshot contains data from other versions"


@pytest.mark.property
@settings(max_examples=20, deadline=None)
@given(
    initial_records=st.lists(timetravel_record(version=1), min_size=10, max_size=30),
    num_updates=st.integers(min_value=2, max_value=5)
)
def test_iceberg_multiple_snapshot_history(spark, initial_records, num_updates):
    """
    Property 12: Multiple Snapshot History
    
    Verifies that multiple sequential updates create distinct snapshots,
    and each can be accessed independently.
    """
    # Arrange
    table_name = "test_db.history_test"
    
    iceberg_manager = IcebergTableManager(spark, catalog_name="local")
    iceberg_writer = IcebergWriter(spark, catalog_name="local")
    
    # Create table
    if not iceberg_manager.table_exists(table_name):
        iceberg_manager.create_table(
            table_name=table_name,
            schema=timetravel_schema,
            partition_spec={}
        )
    
    # Write initial data
    initial_df = spark.createDataFrame(initial_records, schema=timetravel_schema)
    iceberg_writer.write_to_iceberg(initial_df, table_name, mode="overwrite")
    
    # Track snapshots and expected counts
    snapshot_ids = []
    expected_counts = [len(initial_records)]
    
    # Get initial snapshot
    snapshots = iceberg_manager.list_snapshots(table_name)
    snapshot_ids.append(snapshots[0]['snapshot_id'])
    
    # Act
    # Perform multiple updates
    for i in range(num_updates):
        time.sleep(0.1)  # Ensure different timestamps
        
        # Add more records
        new_records = [
            {"id": f"update_{i}_{j}", "version": i + 2, "data": f"data_{i}_{j}"}
            for j in range(5)
        ]
        new_df = spark.createDataFrame(new_records, schema=timetravel_schema)
        iceberg_writer.write_to_iceberg(new_df, table_name, mode="append")
        
        # Track snapshot and count
        snapshots = iceberg_manager.list_snapshots(table_name)
        snapshot_ids.append(snapshots[0]['snapshot_id'])
        expected_counts.append(expected_counts[-1] + len(new_records))
    
    # Assert
    # Should have num_updates + 1 snapshots
    final_snapshots = iceberg_manager.list_snapshots(table_name)
    assert len(final_snapshots) >= num_updates + 1, \
        f"Expected at least {num_updates + 1} snapshots, got {len(final_snapshots)}"
    
    # Verify each snapshot has correct count
    for i, (snapshot_id, expected_count) in enumerate(zip(snapshot_ids, expected_counts)):
        snapshot_data = spark.read \
            .option("snapshot-id", snapshot_id) \
            .table(f"local.{table_name}")
        
        actual_count = snapshot_data.count()
        
        assert actual_count == expected_count, \
            f"Snapshot {i} count mismatch: expected {expected_count}, got {actual_count}"


@pytest.mark.property
@settings(max_examples=20, deadline=None)
@given(
    records_v1=st.lists(timetravel_record(version=1), min_size=10, max_size=30),
    records_v2=st.lists(timetravel_record(version=2), min_size=10, max_size=30)
)
def test_iceberg_rollback_to_snapshot(spark, records_v1, records_v2):
    """
    Property 12: Rollback to Previous Snapshot
    
    Verifies that rolling back to a previous snapshot restores data
    to that exact state.
    """
    # Arrange
    table_name = "test_db.rollback_test"
    
    iceberg_manager = IcebergTableManager(spark, catalog_name="local")
    iceberg_writer = IcebergWriter(spark, catalog_name="local")
    
    # Create table
    if not iceberg_manager.table_exists(table_name):
        iceberg_manager.create_table(
            table_name=table_name,
            schema=timetravel_schema,
            partition_spec={}
        )
    
    # Write version 1
    v1_df = spark.createDataFrame(records_v1, schema=timetravel_schema)
    iceberg_writer.write_to_iceberg(v1_df, table_name, mode="overwrite")
    
    # Get version 1 snapshot
    snapshots_v1 = iceberg_manager.list_snapshots(table_name)
    snapshot_v1_id = snapshots_v1[0]['snapshot_id']
    v1_count = len(records_v1)
    
    time.sleep(0.1)
    
    # Write version 2 (overwrite)
    v2_df = spark.createDataFrame(records_v2, schema=timetravel_schema)
    iceberg_writer.write_to_iceberg(v2_df, table_name, mode="overwrite")
    
    # Verify version 2 is current
    current_count_before_rollback = spark.table(f"local.{table_name}").count()
    assert current_count_before_rollback == len(records_v2), \
        "Version 2 not correctly written"
    
    # Act
    # Rollback to version 1
    iceberg_manager.rollback_to_snapshot(table_name, snapshot_v1_id)
    
    # Assert
    # Current data should match version 1
    current_data_after_rollback = spark.table(f"local.{table_name}")
    current_count_after_rollback = current_data_after_rollback.count()
    
    assert current_count_after_rollback == v1_count, \
        f"Rollback failed: expected {v1_count} records, got {current_count_after_rollback}"
    
    # Verify data content matches version 1
    current_versions = [row.version for row in current_data_after_rollback.collect()]
    assert all(v == 1 for v in current_versions), \
        "Rollback did not restore version 1 data correctly"


@pytest.mark.property
@settings(max_examples=20, deadline=None)
@given(records=st.lists(timetravel_record(version=1), min_size=10, max_size=50))
def test_iceberg_snapshot_metadata_completeness(spark, records):
    """
    Property 12: Snapshot Metadata Completeness
    
    Verifies that snapshot metadata contains all required information
    for time travel operations.
    """
    # Arrange
    table_name = "test_db.metadata_test"
    
    iceberg_manager = IcebergTableManager(spark, catalog_name="local")
    iceberg_writer = IcebergWriter(spark, catalog_name="local")
    
    # Create table
    if not iceberg_manager.table_exists(table_name):
        iceberg_manager.create_table(
            table_name=table_name,
            schema=timetravel_schema,
            partition_spec={}
        )
    
    # Write data
    df = spark.createDataFrame(records, schema=timetravel_schema)
    iceberg_writer.write_to_iceberg(df, table_name, mode="overwrite")
    
    # Act
    snapshots = iceberg_manager.list_snapshots(table_name)
    
    # Assert
    assert len(snapshots) > 0, "No snapshots found"
    
    # Verify each snapshot has required metadata
    for snapshot in snapshots:
        assert 'snapshot_id' in snapshot, "Snapshot missing snapshot_id"
        assert 'committed_at' in snapshot, "Snapshot missing committed_at timestamp"
        assert 'operation' in snapshot, "Snapshot missing operation type"
        
        # Snapshot ID should be valid
        assert snapshot['snapshot_id'] is not None, "Snapshot ID is None"
        
        # Timestamp should be valid
        assert snapshot['committed_at'] is not None, "Committed timestamp is None"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--hypothesis-show-statistics"])
