"""
DuplicateDetector Module

This module identifies duplicate records based on business key columns.
It marks duplicates and assigns group IDs for conflict resolution.

Source: Integrated from Max's implementation
"""

from pyspark.sql import DataFrame
from pyspark.sql.functions import col, count, row_number, min as spark_min
from pyspark.sql.window import Window
from typing import List


class DuplicateDetector:
    """
    Detects duplicate records based on configured key columns.
    
    Adds two columns to the DataFrame:
    - is_duplicate: Boolean indicating if the record is a duplicate
    - duplicate_group_id: Unique ID for each group of duplicates
    """
    
    def __init__(self):
        """Initialize the DuplicateDetector."""
        pass
    
    def transform(self, df: DataFrame, config: dict) -> DataFrame:
        """
        Detect duplicates and add marking columns.
        
        Args:
            df: Input PySpark DataFrame
            config: Configuration dictionary with:
                - duplicate_detection.key_columns: List of column names to use as keys
            
        Returns:
            DataFrame with is_duplicate and duplicate_group_id columns added
            
        Raises:
            ValueError: If key_columns are not specified or don't exist in DataFrame
        """
        # Get duplicate detection configuration
        dup_config = config.get("duplicate_detection", {})
        key_columns = dup_config.get("key_columns", [])
        
        # Validate key columns
        if not key_columns:
            raise ValueError("duplicate_detection.key_columns must be specified in configuration")
        
        # Check that all key columns exist in the DataFrame
        missing_columns = [col_name for col_name in key_columns if col_name not in df.columns]
        if missing_columns:
            raise ValueError(f"Key columns not found in DataFrame: {missing_columns}")
        
        # Mark duplicates
        df_with_duplicates = self._mark_duplicates(df, key_columns)
        
        # Assign group IDs
        df_with_groups = self._assign_group_ids(df_with_duplicates, key_columns)
        
        return df_with_groups
    
    def _mark_duplicates(self, df: DataFrame, key_columns: List[str]) -> DataFrame:
        """
        Mark records as duplicates based on key columns.
        
        Args:
            df: Input DataFrame
            key_columns: List of column names to use as duplicate keys
            
        Returns:
            DataFrame with is_duplicate column added
        """
        # Count occurrences of each key combination
        # Create a window to count duplicates
        window_spec = Window.partitionBy(*key_columns)
        
        # Add a count column for each partition
        df_with_count = df.withColumn("_dup_count", count("*").over(window_spec))
        
        # Mark as duplicate if count > 1
        df_marked = df_with_count.withColumn(
            "is_duplicate",
            col("_dup_count") > 1
        )
        
        # Drop the temporary count column
        df_marked = df_marked.drop("_dup_count")
        
        return df_marked
    
    def _assign_group_ids(self, df: DataFrame, key_columns: List[str]) -> DataFrame:
        """
        Assign unique group IDs to duplicate groups.
        
        Args:
            df: DataFrame with is_duplicate column
            key_columns: List of column names used as duplicate keys
            
        Returns:
            DataFrame with duplicate_group_id column added
        """
        # Create a window partitioned by key columns
        global_window = Window.orderBy(*key_columns)
        
        # Assign row numbers globally
        df_with_row_num = df.withColumn("_row_num", row_number().over(global_window))
        
        # Get the minimum row number for each group (this becomes the group ID)
        window_for_min = Window.partitionBy(*key_columns)
        df_with_group_id = df_with_row_num.withColumn(
            "duplicate_group_id",
            spark_min("_row_num").over(window_for_min)
        )
        
        # Drop temporary column
        df_with_group_id = df_with_group_id.drop("_row_num")
        
        return df_with_group_id
