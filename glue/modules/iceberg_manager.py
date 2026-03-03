"""
Iceberg Table Manager Module

This module provides functionality for managing Apache Iceberg tables in AWS Glue,
including table creation, partitioning, ACID transactions, and snapshot management.

Task: 5.1 - Create IcebergTableManager class
Requirements: 5.1, 5.2, 5.3
"""

from typing import Dict, List, Optional
from pyspark.sql import SparkSession, DataFrame
from pyspark.sql.types import StructType
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class IcebergTableManager:
    """
    Manages Apache Iceberg tables with ACID transactions, partitioning, and snapshots.
    
    This class handles:
    - Table creation with appropriate partitioning strategies
    - Parquet format configuration with Snappy compression
    - ACID transaction support
    - Snapshot management for time travel
    - Registration in AWS Glue Data Catalog
    """
    
    def __init__(self, spark: SparkSession, catalog_name: str = "glue_catalog"):
        """
        Initialize the Iceberg Table Manager.
        
        Args:
            spark: Active SparkSession with Iceberg support
            catalog_name: Name of the Glue catalog (default: "glue_catalog")
        """
        self.spark = spark
        self.catalog_name = catalog_name
        
        # Configure Spark for Iceberg
        self._configure_iceberg()
        
        logger.info(f"IcebergTableManager initialized with catalog: {catalog_name}")
    
    def _configure_iceberg(self) -> None:
        """
        Configure Spark session for Iceberg support.
        
        Sets up:
        - Iceberg catalog configuration
        - Parquet format with Snappy compression
        - ACID transaction settings
        """
        # Iceberg catalog configuration
        self.spark.conf.set(f"spark.sql.catalog.{self.catalog_name}", 
                           "org.apache.iceberg.spark.SparkCatalog")
        self.spark.conf.set(f"spark.sql.catalog.{self.catalog_name}.catalog-impl", 
                           "org.apache.iceberg.aws.glue.GlueCatalog")
        self.spark.conf.set(f"spark.sql.catalog.{self.catalog_name}.warehouse", 
                           "s3://your-bucket/warehouse")
        
        # Parquet configuration
        self.spark.conf.set("spark.sql.parquet.compression.codec", "snappy")
        self.spark.conf.set("spark.sql.parquet.writeLegacyFormat", "false")
        
        # Iceberg write configuration
        self.spark.conf.set("spark.sql.iceberg.handle-timestamp-without-timezone", "true")
        
        logger.info("Iceberg configuration applied to Spark session")
    
    def create_table(
        self, 
        table_name: str, 
        schema: StructType, 
        partition_spec: Dict[str, List[str]],
        location: Optional[str] = None,
        properties: Optional[Dict[str, str]] = None
    ) -> None:
        """
        Create an Iceberg table with specified schema and partitioning.
        
        Args:
            table_name: Fully qualified table name (e.g., "database.table")
            schema: PySpark StructType defining the table schema
            partition_spec: Dictionary with partition configuration
                Example: {"partition_by": ["year(date_created)", "month(date_created)"]}
            location: Optional S3 location for table data
            properties: Optional table properties (compression, file size, etc.)
        
        Requirements: 5.1, 5.2
        """
        try:
            # Build partition clause
            partition_clause = ""
            if partition_spec and "partition_by" in partition_spec:
                partitions = ", ".join(partition_spec["partition_by"])
                partition_clause = f"PARTITIONED BY ({partitions})"
            
            # Build location clause
            location_clause = f"LOCATION '{location}'" if location else ""
            
            # Default table properties for optimal performance
            default_properties = {
                "write.format.default": "parquet",
                "write.parquet.compression-codec": "snappy",
                "write.target-file-size-bytes": str(128 * 1024 * 1024),  # 128 MB
                "write.metadata.compression-codec": "gzip",
                "commit.retry.num-retries": "3",
                "commit.retry.min-wait-ms": "100",
                "history.expire.max-snapshot-age-ms": str(30 * 24 * 60 * 60 * 1000),  # 30 days
            }
            
            # Merge with user-provided properties
            if properties:
                default_properties.update(properties)
            
            # Build properties clause
            props_list = [f"'{k}' = '{v}'" for k, v in default_properties.items()]
            properties_clause = f"TBLPROPERTIES ({', '.join(props_list)})"
            
            # Create table using Spark SQL
            # Note: We'll use DataFrame API to create schema, then SQL for Iceberg-specific features
            full_table_name = f"{self.catalog_name}.{table_name}"
            
            # Create empty DataFrame with schema
            empty_df = self.spark.createDataFrame([], schema)
            
            # Write as Iceberg table
            writer = empty_df.writeTo(full_table_name)
            
            # Apply partitioning
            if partition_spec and "partition_by" in partition_spec:
                for partition_col in partition_spec["partition_by"]:
                    writer = writer.partitionedBy(partition_col)
            
            # Apply properties
            for key, value in default_properties.items():
                writer = writer.option(key, value)
            
            # Create table
            writer.createOrReplace()
            
            logger.info(f"Successfully created Iceberg table: {full_table_name}")
            logger.info(f"Partitioning: {partition_spec.get('partition_by', 'None')}")
            logger.info(f"Properties: {default_properties}")
            
        except Exception as e:
            logger.error(f"Failed to create table {table_name}: {str(e)}")
            raise
    
    def compact_files(self, table_name: str) -> None:
        """
        Compact small files in an Iceberg table for better performance.
        
        Args:
            table_name: Fully qualified table name
        
        Requirements: 5.2
        """
        try:
            full_table_name = f"{self.catalog_name}.{table_name}"
            
            # Trigger compaction using Iceberg's rewrite_data_files procedure
            self.spark.sql(f"""
                CALL {self.catalog_name}.system.rewrite_data_files(
                    table => '{table_name}',
                    options => map(
                        'target-file-size-bytes', '134217728',  -- 128 MB
                        'min-file-size-bytes', '67108864'       -- 64 MB
                    )
                )
            """)
            
            logger.info(f"Successfully compacted files for table: {full_table_name}")
            
        except Exception as e:
            logger.error(f"Failed to compact table {table_name}: {str(e)}")
            raise
    
    def list_snapshots(self, table_name: str) -> List[Dict]:
        """
        List all snapshots for an Iceberg table.
        
        Args:
            table_name: Fully qualified table name
        
        Returns:
            List of snapshot metadata dictionaries
        
        Requirements: 5.3
        """
        try:
            full_table_name = f"{self.catalog_name}.{table_name}"
            
            # Query snapshots metadata table
            snapshots_df = self.spark.sql(f"""
                SELECT 
                    snapshot_id,
                    parent_id,
                    operation,
                    manifest_list,
                    summary,
                    committed_at
                FROM {full_table_name}.snapshots
                ORDER BY committed_at DESC
            """)
            
            snapshots = [row.asDict() for row in snapshots_df.collect()]
            
            logger.info(f"Found {len(snapshots)} snapshots for table: {full_table_name}")
            
            return snapshots
            
        except Exception as e:
            logger.error(f"Failed to list snapshots for table {table_name}: {str(e)}")
            raise
    
    def rollback_to_snapshot(self, table_name: str, snapshot_id: str) -> None:
        """
        Rollback an Iceberg table to a specific snapshot.
        
        Args:
            table_name: Fully qualified table name
            snapshot_id: ID of the snapshot to rollback to
        
        Requirements: 5.3
        """
        try:
            full_table_name = f"{self.catalog_name}.{table_name}"
            
            # Rollback using Iceberg's rollback_to_snapshot procedure
            self.spark.sql(f"""
                CALL {self.catalog_name}.system.rollback_to_snapshot(
                    table => '{table_name}',
                    snapshot_id => {snapshot_id}
                )
            """)
            
            logger.info(f"Successfully rolled back table {full_table_name} to snapshot: {snapshot_id}")
            
        except Exception as e:
            logger.error(f"Failed to rollback table {table_name} to snapshot {snapshot_id}: {str(e)}")
            raise
    
    def get_table_metadata(self, table_name: str) -> Dict:
        """
        Get metadata information for an Iceberg table.
        
        Args:
            table_name: Fully qualified table name
        
        Returns:
            Dictionary with table metadata
        """
        try:
            full_table_name = f"{self.catalog_name}.{table_name}"
            
            # Get table metadata
            metadata_df = self.spark.sql(f"DESCRIBE EXTENDED {full_table_name}")
            metadata = {row['col_name']: row['data_type'] 
                       for row in metadata_df.collect() 
                       if row['col_name'] and row['data_type']}
            
            logger.info(f"Retrieved metadata for table: {full_table_name}")
            
            return metadata
            
        except Exception as e:
            logger.error(f"Failed to get metadata for table {table_name}: {str(e)}")
            raise
    
    def table_exists(self, table_name: str) -> bool:
        """
        Check if an Iceberg table exists.
        
        Args:
            table_name: Fully qualified table name
        
        Returns:
            True if table exists, False otherwise
        """
        try:
            full_table_name = f"{self.catalog_name}.{table_name}"
            
            # Check if table exists in catalog
            tables = self.spark.sql(f"SHOW TABLES IN {self.catalog_name}").collect()
            table_names = [f"{row['namespace']}.{row['tableName']}" for row in tables]
            
            exists = full_table_name in table_names
            
            logger.info(f"Table {full_table_name} exists: {exists}")
            
            return exists
            
        except Exception as e:
            logger.error(f"Failed to check if table {table_name} exists: {str(e)}")
            return False
