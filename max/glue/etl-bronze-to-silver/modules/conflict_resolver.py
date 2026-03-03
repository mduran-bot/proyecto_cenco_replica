"""
ConflictResolver Module

This module resolves conflicts when duplicate records have contradictory values.
It selects the best record from each duplicate group based on timestamp, null count,
and deterministic ordering.

Source: Integrated from Max's implementation
"""

from pyspark.sql import DataFrame
from pyspark.sql.functions import col, when, row_number, monotonically_increasing_id, lit
from pyspark.sql.window import Window
from typing import Optional


class ConflictResolver:
    """
    Resolves conflicts in duplicate records by selecting the best record.
    
    Selection criteria (in order):
    1. Most recent timestamp
    2. Fewest null values
    3. First record encountered (deterministic)
    """
    
    def __init__(self):
        """Initialize the ConflictResolver."""
        pass
    
    def transform(self, df: DataFrame, config: dict) -> DataFrame:
        """
        Resolve conflicts by selecting the best record from each duplicate group.
        
        Args:
            df: Input PySpark DataFrame with is_duplicate and duplicate_group_id columns
            config: Configuration dictionary with:
                - conflict_resolution.timestamp_column: Column name for timestamp comparison (optional)
            
        Returns:
            DataFrame with duplicates resolved and auxiliary columns removed
        """
        # Check if DataFrame has duplicate marking columns
        if "is_duplicate" not in df.columns or "duplicate_group_id" not in df.columns:
            # If no duplicate columns, return as-is (already processed or no duplicates detected)
            return df
        
        # Get conflict resolution configuration
        conflict_config = config.get("conflict_resolution", {})
        timestamp_column = conflict_config.get("timestamp_column", None)
        
        # Validate timestamp column if specified
        if timestamp_column and timestamp_column not in df.columns:
            # If timestamp column doesn't exist, proceed without it (use null count and order)
            timestamp_column = None
        
        # Select best record from each duplicate group
        df_resolved = self._select_best_record(df, timestamp_column)
        
        # Remove auxiliary columns
        df_clean = df_resolved.drop("is_duplicate", "duplicate_group_id")
        
        return df_clean
    
    def _select_best_record(self, df: DataFrame, timestamp_column: Optional[str]) -> DataFrame:
        """
        Select the best record from each duplicate group.
        
        Args:
            df: DataFrame with is_duplicate and duplicate_group_id columns
            timestamp_column: Column name for timestamp comparison (optional)
            
        Returns:
            DataFrame with only the best record from each duplicate group
        """
        # Add null count column for all records
        df_with_null_count = self._count_nulls(df)
        
        # Build ordering criteria
        order_criteria = []
        
        # 1. Order by timestamp (most recent first) if available
        if timestamp_column:
            order_criteria.append(col(timestamp_column).desc())
        
        # 2. Order by null count (fewest nulls first)
        order_criteria.append(col("_null_count").asc())
        
        # 3. Add deterministic ordering using monotonically increasing ID
        df_with_id = df_with_null_count.withColumn("_row_id", monotonically_increasing_id())
        order_criteria.append(col("_row_id").asc())
        
        # Create window for ranking
        window_spec = Window.partitionBy("duplicate_group_id").orderBy(*order_criteria)
        
        # Assign rank to each record within its duplicate group
        df_ranked = df_with_id.withColumn("_rank", row_number().over(window_spec))
        
        # Keep only the best record (rank = 1) from each group
        df_best = df_ranked.filter(col("_rank") == 1)
        
        # Drop temporary columns
        df_best = df_best.drop("_null_count", "_row_id", "_rank")
        
        return df_best
    
    def _count_nulls(self, df: DataFrame) -> DataFrame:
        """
        Count the number of null values in each row.
        
        Args:
            df: Input DataFrame
            
        Returns:
            DataFrame with _null_count column added
        """
        # Create an expression that counts nulls across all columns
        # Exclude the duplicate marking columns from null counting
        columns_to_check = [
            c for c in df.columns 
            if c not in ["is_duplicate", "duplicate_group_id"]
        ]
        
        # Build expression: sum of (1 if null, 0 otherwise) for each column
        null_expressions = [when(col(c).isNull(), 1).otherwise(0) for c in columns_to_check]
        
        # Start with the first expression and add the rest
        if null_expressions:
            null_count_expr = null_expressions[0]
            for expr in null_expressions[1:]:
                null_count_expr = null_count_expr + expr
        else:
            # If no columns to check, set null count to 0
            null_count_expr = lit(0)
        
        # Add null count column
        df_with_count = df.withColumn("_null_count", null_count_expr)
        
        return df_with_count
