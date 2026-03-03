"""
DataCleaner Module

This module cleans raw data by removing whitespace, handling null values,
and fixing encoding issues. It ensures data quality before further processing.

Source: Integrated from Max's implementation
"""

from pyspark.sql import DataFrame
from pyspark.sql.functions import col, trim, when, regexp_replace
from pyspark.sql.types import StringType


class DataCleaner:
    """
    Cleans data by trimming strings, converting empty strings to null,
    and fixing encoding issues.
    
    Transformations applied:
    - Trim whitespace from all string columns
    - Convert empty strings to null
    - Fix UTF-8 encoding errors
    """
    
    def transform(self, df: DataFrame, config: dict) -> DataFrame:
        """
        Clean the DataFrame by applying all cleaning rules.
        
        Args:
            df: Input PySpark DataFrame
            config: Configuration dictionary (not used currently)
            
        Returns:
            Cleaned PySpark DataFrame with same column order
        """
        # Apply cleaning transformations in sequence
        df = self._trim_strings(df)
        df = self._empty_to_null(df)
        df = self._fix_encoding(df)
        
        return df
    
    def _trim_strings(self, df: DataFrame) -> DataFrame:
        """
        Remove leading and trailing whitespace from all string columns.
        
        Args:
            df: DataFrame to clean
            
        Returns:
            DataFrame with trimmed string values
        """
        # Build list of columns with trimming applied to string columns
        trimmed_cols = []
        
        for field in df.schema.fields:
            if isinstance(field.dataType, StringType):
                # Apply trim to string columns
                trimmed_cols.append(trim(col(field.name)).alias(field.name))
            else:
                # Keep non-string columns as-is
                trimmed_cols.append(col(field.name))
        
        return df.select(*trimmed_cols)
    
    def _empty_to_null(self, df: DataFrame) -> DataFrame:
        """
        Convert empty strings to null values.
        
        Args:
            df: DataFrame to clean
            
        Returns:
            DataFrame with empty strings converted to null
        """
        # Build list of columns with empty string conversion for string columns
        converted_cols = []
        
        for field in df.schema.fields:
            if isinstance(field.dataType, StringType):
                # Convert empty strings to null
                converted_cols.append(
                    when(col(field.name) == "", None)
                    .otherwise(col(field.name))
                    .alias(field.name)
                )
            else:
                # Keep non-string columns as-is
                converted_cols.append(col(field.name))
        
        return df.select(*converted_cols)
    
    def _fix_encoding(self, df: DataFrame) -> DataFrame:
        """
        Detect and fix UTF-8 encoding errors by replacing invalid characters.
        
        This method replaces characters that cannot be properly encoded in UTF-8
        with a question mark '?'.
        
        Args:
            df: DataFrame to clean
            
        Returns:
            DataFrame with encoding errors fixed
        """
        # Build list of columns with encoding fixes for string columns
        fixed_cols = []
        
        for field in df.schema.fields:
            if isinstance(field.dataType, StringType):
                # Replace common encoding error patterns
                # This regex pattern matches invalid UTF-8 sequences
                # We replace them with '?'
                fixed_col = regexp_replace(
                    col(field.name),
                    "[^\x00-\x7F\u0080-\uFFFF]",  # Match invalid UTF-8 characters
                    "?"
                )
                fixed_cols.append(fixed_col.alias(field.name))
            else:
                # Keep non-string columns as-is
                fixed_cols.append(col(field.name))
        
        return df.select(*fixed_cols)
