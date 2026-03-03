"""
JSONFlattener Module

This module converts nested JSON structures into flat tabular format.
It handles struct types by flattening them with dot notation and array types
by exploding them into separate rows.

Source: Integrated from Max's implementation
"""

from pyspark.sql import DataFrame
from pyspark.sql.functions import col, explode_outer
from pyspark.sql.types import StructType, ArrayType


class JSONFlattener:
    """
    Flattens nested JSON structures in PySpark DataFrames.
    
    Converts:
    - Struct columns to flat columns with dot notation (e.g., "address.city")
    - Array columns to multiple rows using explode
    """
    
    def __init__(self):
        """Initialize JSONFlattener with maximum recursion depth."""
        self.max_depth = 10  # Maximum depth for recursive flattening
    
    def transform(self, df: DataFrame, config: dict) -> DataFrame:
        """
        Flatten all nested structures in the DataFrame.
        
        Args:
            df: Input PySpark DataFrame
            config: Configuration dictionary (not used currently)
            
        Returns:
            Flattened PySpark DataFrame
        """
        # First, explode all arrays
        df = self._explode_arrays(df)
        
        # Then, flatten all struct columns recursively
        depth = 0
        while self._has_struct_columns(df) and depth < self.max_depth:
            df = self._flatten_all_structs(df)
            depth += 1
        
        return df
    
    def _has_struct_columns(self, df: DataFrame) -> bool:
        """
        Check if DataFrame has any struct columns.
        
        Args:
            df: DataFrame to check
            
        Returns:
            True if DataFrame has struct columns, False otherwise
        """
        for field in df.schema.fields:
            if isinstance(field.dataType, StructType):
                return True
        return False
    
    def _flatten_all_structs(self, df: DataFrame) -> DataFrame:
        """
        Flatten all struct columns in the DataFrame by one level.
        
        Args:
            df: DataFrame with struct columns
            
        Returns:
            DataFrame with struct columns flattened by one level
        """
        for field in df.schema.fields:
            if isinstance(field.dataType, StructType):
                df = self._flatten_struct(df, field.name)
        return df
    
    def _flatten_struct(self, df: DataFrame, col_name: str, prefix: str = "") -> DataFrame:
        """
        Flatten a single struct column recursively.
        
        Args:
            df: DataFrame containing the struct column
            col_name: Name of the struct column to flatten
            prefix: Prefix for nested column names (used in recursion)
            
        Returns:
            DataFrame with the struct column flattened
        """
        # Get the struct field
        struct_field = None
        for field in df.schema.fields:
            if field.name == col_name:
                struct_field = field
                break
        
        if struct_field is None or not isinstance(struct_field.dataType, StructType):
            return df
        
        # Get existing column names for collision detection
        existing_names = list(df.columns)
        
        # Expand struct fields
        struct_type = struct_field.dataType
        expanded_cols = []
        
        # Keep all non-struct columns
        for field in df.schema.fields:
            if field.name != col_name:
                expanded_cols.append(col(field.name))
        
        # Add flattened struct fields
        for nested_field in struct_type.fields:
            new_col_name = f"{col_name}_{nested_field.name}"
            # Resolve name collisions
            new_col_name = self._resolve_name_collision(existing_names, new_col_name)
            # Use getField() to safely access nested fields
            expanded_cols.append(col(col_name).getField(nested_field.name).alias(new_col_name))
            existing_names.append(new_col_name)
        
        return df.select(*expanded_cols)
    
    def _explode_arrays(self, df: DataFrame) -> DataFrame:
        """
        Explode all array columns into separate rows.
        
        Args:
            df: DataFrame with array columns
            
        Returns:
            DataFrame with arrays exploded into rows
        """
        array_cols = []
        
        # Find all array columns
        for field in df.schema.fields:
            if isinstance(field.dataType, ArrayType):
                array_cols.append(field.name)
        
        # Explode each array column
        for array_col in array_cols:
            # Use explode_outer to preserve rows with null/empty arrays
            df = df.withColumn(array_col, explode_outer(col(array_col)))
        
        return df
    
    def _resolve_name_collision(self, existing_names: list, new_name: str) -> str:
        """
        Resolve column name collisions by adding numeric suffixes.
        
        Args:
            existing_names: List of existing column names
            new_name: Proposed new column name
            
        Returns:
            Unique column name with suffix if needed
        """
        if new_name not in existing_names:
            return new_name
        
        # Add numeric suffix to resolve collision
        suffix = 1
        while f"{new_name}_{suffix}" in existing_names:
            suffix += 1
        
        return f"{new_name}_{suffix}"
