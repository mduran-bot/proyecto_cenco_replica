"""
JSONFlattener Module

This module converts nested JSON structures into flat tabular format.
It handles struct types by flattening them with dot notation and array types
by exploding them into separate rows.

Supports multiple flattening modes:
- Standard: Flatten structs and explode arrays inline
- explode_to_child_table: Create separate child tables for arrays with FK relationships
- key_value_table: Convert dynamic objects to key-value pairs
"""

from pyspark.sql import DataFrame
from pyspark.sql.functions import col, explode_outer, lit, struct, array, map_from_arrays, explode
from pyspark.sql.types import StructType, ArrayType, MapType, StringType
from typing import Dict, List, Tuple, Optional


class JSONFlattener:
    """
    Flattens nested JSON structures in PySpark DataFrames.
    
    Converts:
    - Struct columns to flat columns with dot notation (e.g., "address.city")
    - Array columns to multiple rows using explode
    - Arrays to child tables with foreign key relationships (explode_to_child_table mode)
    - Dynamic objects to key-value tables (key_value_table mode)
    """
    
    def __init__(self):
        """Initialize JSONFlattener with maximum recursion depth."""
        self.max_depth = 10  # Maximum depth for recursive flattening
        self.child_tables = {}  # Store child tables created during processing
        self.key_value_tables = {}  # Store key-value tables created during processing
    
    def transform(self, df: DataFrame, config: dict) -> DataFrame:
        """
        Flatten all nested structures in the DataFrame.
        
        Args:
            df: Input PySpark DataFrame
            config: Configuration dictionary with options:
                - mode: "standard" (default), "explode_to_child_table", "key_value_table"
                - array_columns: List of array columns to process (for explode_to_child_table)
                - parent_key: Primary key column name for parent-child relationships
                - child_table_configs: Dict mapping array column names to child table configs
                - key_value_columns: List of object columns to convert to key-value (for key_value_table)
            
        Returns:
            Flattened PySpark DataFrame (parent table)
            Child tables and key-value tables are stored in self.child_tables and self.key_value_tables
        """
        mode = config.get("mode", "standard")
        
        if mode == "explode_to_child_table":
            return self._transform_with_child_tables(df, config)
        elif mode == "key_value_table":
            return self._transform_with_key_value_tables(df, config)
        else:
            # Standard mode: explode arrays inline and flatten structs
            # First, explode all arrays
            df = self._explode_arrays(df)
            
            # Then, flatten all struct columns recursively
            depth = 0
            while self._has_struct_columns(df) and depth < self.max_depth:
                df = self._flatten_all_structs(df)
                depth += 1
            
            return df
    
    def _transform_with_child_tables(self, df: DataFrame, config: dict) -> DataFrame:
        """
        Transform DataFrame by creating separate child tables for array columns.
        
        Args:
            df: Input DataFrame
            config: Configuration with:
                - parent_key: Primary key column name (e.g., "id", "order_id")
                - child_table_configs: Dict mapping array column names to configs:
                    {
                        "items": {
                            "child_table_name": "order_items",
                            "foreign_key": "order_id"
                        }
                    }
        
        Returns:
            Parent DataFrame with array columns removed
        """
        parent_key = config.get("parent_key", "id")
        child_table_configs = config.get("child_table_configs", {})
        
        # Process each array column configured for child table extraction
        for array_col, child_config in child_table_configs.items():
            if array_col in df.columns:
                child_table_name = child_config.get("child_table_name", f"{array_col}_table")
                foreign_key = child_config.get("foreign_key", f"{parent_key}")
                
                # Create child table
                child_df = self._create_child_table(df, array_col, parent_key, foreign_key)
                
                # Store child table
                self.child_tables[child_table_name] = child_df
                
                # Remove array column from parent
                df = df.drop(array_col)
        
        # Flatten remaining structs in parent table
        depth = 0
        while self._has_struct_columns(df) and depth < self.max_depth:
            df = self._flatten_all_structs(df)
            depth += 1
        
        return df
    
    def _create_child_table(self, df: DataFrame, array_col: str, parent_key: str, foreign_key: str) -> DataFrame:
        """
        Create a child table from an array column with foreign key relationship.
        
        Args:
            df: Parent DataFrame
            array_col: Name of array column to explode
            parent_key: Primary key column in parent table
            foreign_key: Foreign key column name in child table
        
        Returns:
            Child DataFrame with foreign key
        """
        # Select parent key and array column
        child_df = df.select(col(parent_key), col(array_col))
        
        # Explode array into rows
        child_df = child_df.withColumn(array_col, explode_outer(col(array_col)))
        
        # Rename parent key to foreign key
        child_df = child_df.withColumnRenamed(parent_key, foreign_key)
        
        # Flatten struct fields in the exploded array
        if array_col in child_df.columns:
            # Check if the exploded column is a struct
            for field in child_df.schema.fields:
                if field.name == array_col and isinstance(field.dataType, StructType):
                    # Flatten the struct
                    struct_fields = field.dataType.fields
                    expanded_cols = [col(foreign_key)]
                    
                    for nested_field in struct_fields:
                        new_col_name = nested_field.name
                        expanded_cols.append(col(array_col).getField(nested_field.name).alias(new_col_name))
                    
                    child_df = child_df.select(*expanded_cols)
                    break
        
        # Flatten any remaining nested structs
        depth = 0
        while self._has_struct_columns(child_df) and depth < self.max_depth:
            child_df = self._flatten_all_structs(child_df)
            depth += 1
        
        return child_df
    
    def _transform_with_key_value_tables(self, df: DataFrame, config: dict) -> DataFrame:
        """
        Transform DataFrame by converting dynamic object columns to key-value tables.
        
        Args:
            df: Input DataFrame
            config: Configuration with:
                - parent_key: Primary key column name (e.g., "id", "order_id")
                - key_value_columns: List of object column names to convert:
                    ["customData", "metadata"]
                - key_value_table_configs: Dict mapping column names to configs:
                    {
                        "customData": {
                            "table_name": "order_custom_data_fields",
                            "foreign_key": "order_id"
                        }
                    }
        
        Returns:
            Parent DataFrame with object columns removed
        """
        parent_key = config.get("parent_key", "id")
        key_value_columns = config.get("key_value_columns", [])
        key_value_table_configs = config.get("key_value_table_configs", {})
        
        # Process each object column configured for key-value extraction
        for obj_col in key_value_columns:
            if obj_col in df.columns:
                table_config = key_value_table_configs.get(obj_col, {})
                table_name = table_config.get("table_name", f"{obj_col}_key_value")
                foreign_key = table_config.get("foreign_key", parent_key)
                
                # Create key-value table
                kv_df = self._create_key_value_table(df, obj_col, parent_key, foreign_key)
                
                # Store key-value table
                self.key_value_tables[table_name] = kv_df
                
                # Remove object column from parent
                df = df.drop(obj_col)
        
        # Flatten remaining structs in parent table
        depth = 0
        while self._has_struct_columns(df) and depth < self.max_depth:
            df = self._flatten_all_structs(df)
            depth += 1
        
        return df
    
    def _create_key_value_table(self, df: DataFrame, obj_col: str, parent_key: str, foreign_key: str) -> DataFrame:
        """
        Create a key-value table from a dynamic object column.
        
        Args:
            df: Parent DataFrame
            obj_col: Name of object column to convert
            parent_key: Primary key column in parent table
            foreign_key: Foreign key column name in key-value table
        
        Returns:
            Key-value DataFrame with columns: foreign_key, field, value
        """
        from pyspark.sql.functions import explode, map_keys, map_values
        from pyspark.sql.types import StructType as SparkStructType, StructField, MapType as SparkMapType
        
        # Select parent key and object column
        kv_df = df.select(col(parent_key), col(obj_col))
        
        # Check if column is a struct (convert to map) or already a map
        field_type = None
        for field in kv_df.schema.fields:
            if field.name == obj_col:
                field_type = field.dataType
                break
        
        if isinstance(field_type, SparkStructType):
            # Convert struct to map by creating key-value pairs
            # Get all field names
            field_names = [f.name for f in field_type.fields]
            
            # Create array of keys and values
            from pyspark.sql.functions import array, struct as spark_struct, col as spark_col
            
            # Build key-value pairs
            kv_pairs = []
            for field_name in field_names:
                kv_pairs.append(
                    spark_struct(
                        lit(field_name).alias("field"),
                        spark_col(f"{obj_col}.{field_name}").cast(StringType()).alias("value")
                    )
                )
            
            # Create array of structs
            kv_df = kv_df.withColumn("kv_array", array(*kv_pairs))
            
            # Explode array
            kv_df = kv_df.withColumn("kv_pair", explode_outer(col("kv_array")))
            
            # Extract field and value
            kv_df = kv_df.select(
                col(parent_key).alias(foreign_key),
                col("kv_pair.field").alias("field"),
                col("kv_pair.value").alias("value")
            )
        
        elif isinstance(field_type, SparkMapType):
            # Already a map, explode directly
            kv_df = kv_df.select(
                col(parent_key).alias(foreign_key),
                explode_outer(col(obj_col)).alias("field", "value")
            )
            
            # Cast value to string
            kv_df = kv_df.withColumn("value", col("value").cast(StringType()))
        
        else:
            # Unsupported type, return empty DataFrame with correct schema
            schema = SparkStructType([
                StructField(foreign_key, StringType(), True),
                StructField("field", StringType(), True),
                StructField("value", StringType(), True)
            ])
            kv_df = df.sparkSession.createDataFrame([], schema)
        
        return kv_df
    
    def get_child_tables(self) -> Dict[str, DataFrame]:
        """
        Get all child tables created during transformation.
        
        Returns:
            Dictionary mapping table names to DataFrames
        """
        return self.child_tables
    
    def get_key_value_tables(self) -> Dict[str, DataFrame]:
        """
        Get all key-value tables created during transformation.
        
        Returns:
            Dictionary mapping table names to DataFrames
        """
        return self.key_value_tables
    
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
