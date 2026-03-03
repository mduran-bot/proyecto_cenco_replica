"""
Iceberg Writer Module

This module provides functionality for writing DataFrames to Iceberg tables
with ACID transaction support and automatic registration in AWS Glue Data Catalog.

Task: 5.2 - Create IcebergWriter class
Requirements: 2.5, 5.5
"""

from typing import Optional, Dict
from pyspark.sql import DataFrame, SparkSession
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class IcebergWriter:
    """
    Writes DataFrames to Apache Iceberg tables with ACID guarantees.
    
    This class handles:
    - Writing DataFrames to Iceberg tables
    - ACID transaction commits
    - Automatic registration in AWS Glue Data Catalog
    - Append, overwrite, and upsert operations
    """
    
    def __init__(self, spark: SparkSession, catalog_name: str = "glue_catalog"):
        """
        Initialize the Iceberg Writer.
        
        Args:
            spark: Active SparkSession with Iceberg support
            catalog_name: Name of the Glue catalog (default: "glue_catalog")
        """
        self.spark = spark
        self.catalog_name = catalog_name
        
        logger.info(f"IcebergWriter initialized with catalog: {catalog_name}")
    
    def write_to_iceberg(
        self,
        df: DataFrame,
        table_name: str,
        mode: str = "append",
        merge_keys: Optional[list] = None,
        partition_overwrite: bool = False
    ) -> None:
        """
        Write a DataFrame to an Iceberg table.
        
        Args:
            df: DataFrame to write
            table_name: Fully qualified table name (e.g., "database.table")
            mode: Write mode - "append", "overwrite", or "merge"
            merge_keys: List of columns to use as merge keys (required for merge mode)
            partition_overwrite: If True, overwrite only matching partitions
        
        Requirements: 2.5, 5.5
        """
        try:
            full_table_name = f"{self.catalog_name}.{table_name}"
            
            if mode == "merge" and merge_keys:
                self._merge_into_table(df, table_name, merge_keys)
            else:
                # Standard write operation
                writer = df.writeTo(full_table_name)
                
                # Configure write options
                if partition_overwrite:
                    writer = writer.option("overwrite-mode", "dynamic")
                
                # Execute write based on mode
                if mode == "append":
                    writer.append()
                elif mode == "overwrite":
                    if partition_overwrite:
                        writer.overwritePartitions()
                    else:
                        writer.overwrite()
                else:
                    raise ValueError(f"Unsupported write mode: {mode}")
            
            logger.info(f"Successfully wrote {df.count()} records to {full_table_name} (mode: {mode})")
            
        except Exception as e:
            logger.error(f"Failed to write to table {table_name}: {str(e)}")
            raise
    
    def _merge_into_table(
        self,
        df: DataFrame,
        table_name: str,
        merge_keys: list
    ) -> None:
        """
        Merge DataFrame into Iceberg table using MERGE INTO operation.
        
        This implements UPSERT logic: update existing records, insert new ones.
        
        Args:
            df: DataFrame with new/updated data
            table_name: Target table name
            merge_keys: Columns to match for merge operation
        """
        try:
            full_table_name = f"{self.catalog_name}.{table_name}"
            
            # Create temporary view for source data
            temp_view = f"temp_{table_name.replace('.', '_')}_source"
            df.createOrReplaceTempView(temp_view)
            
            # Build merge condition
            merge_condition = " AND ".join([
                f"target.{key} = source.{key}" for key in merge_keys
            ])
            
            # Get all columns except merge keys for UPDATE SET clause
            all_columns = df.columns
            update_columns = [col for col in all_columns if col not in merge_keys]
            update_set = ", ".join([f"target.{col} = source.{col}" for col in update_columns])
            
            # Build INSERT VALUES clause
            insert_columns = ", ".join(all_columns)
            insert_values = ", ".join([f"source.{col}" for col in all_columns])
            
            # Execute MERGE INTO
            merge_sql = f"""
                MERGE INTO {full_table_name} AS target
                USING {temp_view} AS source
                ON {merge_condition}
                WHEN MATCHED THEN
                    UPDATE SET {update_set}
                WHEN NOT MATCHED THEN
                    INSERT ({insert_columns})
                    VALUES ({insert_values})
            """
            
            self.spark.sql(merge_sql)
            
            logger.info(f"Successfully merged data into {full_table_name}")
            
        except Exception as e:
            logger.error(f"Failed to merge into table {table_name}: {str(e)}")
            raise
    
    def append_to_table(self, df: DataFrame, table_name: str) -> None:
        """
        Append DataFrame to an Iceberg table.
        
        Args:
            df: DataFrame to append
            table_name: Fully qualified table name
        """
        self.write_to_iceberg(df, table_name, mode="append")
    
    def overwrite_table(
        self,
        df: DataFrame,
        table_name: str,
        partition_overwrite: bool = False
    ) -> None:
        """
        Overwrite an Iceberg table with DataFrame data.
        
        Args:
            df: DataFrame to write
            table_name: Fully qualified table name
            partition_overwrite: If True, overwrite only matching partitions
        """
        self.write_to_iceberg(
            df, 
            table_name, 
            mode="overwrite",
            partition_overwrite=partition_overwrite
        )
    
    def upsert_to_table(
        self,
        df: DataFrame,
        table_name: str,
        merge_keys: list
    ) -> None:
        """
        Upsert (update or insert) DataFrame to an Iceberg table.
        
        Args:
            df: DataFrame with data to upsert
            table_name: Fully qualified table name
            merge_keys: Columns to use for matching records
        """
        self.write_to_iceberg(
            df,
            table_name,
            mode="merge",
            merge_keys=merge_keys
        )
