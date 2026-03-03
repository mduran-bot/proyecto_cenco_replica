"""
DataTypeConverter Module

This module converts data types from MySQL-compatible types to Redshift-compatible types.
It intelligently infers types from string columns and performs conversions.

Supported conversions:
- BIGINT Unix timestamp → TIMESTAMP ISO 8601
- TINYINT(1) → BOOLEAN
- DECIMAL(12,9) → NUMERIC(12,9)
- INT → BIGINT for IDs
- VARCHAR with numeric values → VARCHAR (passthrough)
"""

from pyspark.sql import DataFrame
from pyspark.sql.functions import col, when, lower, from_unixtime, to_timestamp
from pyspark.sql.types import (
    StringType, BooleanType, DateType, TimestampType, 
    DecimalType, IntegerType, LongType, FloatType, DoubleType
)
from typing import List, Optional, Dict
import re
from datetime import datetime


class DataTypeConverter:
    """
    Converts data types from MySQL to Redshift-compatible types.
    
    Supports conversion of:
    - BIGINT Unix timestamp to TIMESTAMP ISO 8601
    - TINYINT(1) to BooleanType
    - DECIMAL(12,9) to NUMERIC(12,9)
    - INT to BIGINT for IDs
    - String booleans to BooleanType
    - String dates to DateType
    - String timestamps to TimestampType
    - String decimals to DecimalType(18,2)
    - String integers to IntegerType/LongType
    """
    
    def __init__(self):
        """Initialize the DataTypeConverter with type mappings."""
        self.type_mapping = {
            "string_to_boolean": BooleanType(),
            "string_to_date": DateType(),
            "string_to_timestamp": TimestampType(),
            "string_to_decimal": DecimalType(18, 2),
            "string_to_integer": IntegerType(),
            "string_to_long": LongType(),
            "unix_timestamp_to_iso8601": TimestampType(),
            "tinyint_to_boolean": BooleanType(),
            "decimal_to_numeric": DecimalType(12, 9),
            "int_to_bigint": LongType()
        }
        
        # Configuration defaults
        self.inference_sample_size = 100
        self.inference_threshold = 0.9  # 90% of values must parse successfully
    
    def transform(self, df: DataFrame, config: dict) -> DataFrame:
        """
        Convert data types in the DataFrame based on configuration and inference.
        
        Args:
            df: Input PySpark DataFrame
            config: Configuration dictionary with:
                - type_conversion.enabled: bool (default True)
                - type_conversion.inference_sample_size: int (default 100)
                - type_conversion.inference_threshold: float (default 0.9)
                - type_mappings: dict with conversion rules
            
        Returns:
            DataFrame with converted types
        """
        # Check if type conversion is enabled
        type_config = config.get("type_conversion", {})
        if not type_config.get("enabled", True):
            return df
        
        # Update configuration if provided
        self.inference_sample_size = type_config.get("inference_sample_size", 100)
        self.inference_threshold = type_config.get("inference_threshold", 0.9)
        
        # Apply explicit conversions from type_mappings
        result_df = df
        type_mappings = config.get("type_mappings", {})
        
        # Apply Unix timestamp to ISO 8601 conversions
        if "unix_timestamp_to_iso8601" in type_mappings:
            timestamp_fields = type_mappings["unix_timestamp_to_iso8601"].get("fields", [])
            for field in timestamp_fields:
                if field in result_df.columns:
                    result_df = self._convert_unix_timestamp_to_iso8601(result_df, field)
        
        # Apply TINYINT to BOOLEAN conversions
        if "tinyint_to_boolean" in type_mappings:
            boolean_fields = type_mappings["tinyint_to_boolean"].get("fields", [])
            for field in boolean_fields:
                if field in result_df.columns:
                    result_df = self._convert_tinyint_to_boolean(result_df, field)
        
        # Apply DECIMAL to NUMERIC conversions
        if "decimal_to_numeric" in type_mappings:
            numeric_fields = type_mappings["decimal_to_numeric"].get("fields", [])
            precision = type_mappings["decimal_to_numeric"].get("precision", 12)
            scale = type_mappings["decimal_to_numeric"].get("scale", 9)
            for field in numeric_fields:
                if field in result_df.columns:
                    result_df = self._convert_decimal_to_numeric(result_df, field, precision, scale)
        
        # Apply INT to BIGINT conversions
        if "int_to_bigint" in type_mappings:
            bigint_fields = type_mappings["int_to_bigint"].get("fields", [])
            for field in bigint_fields:
                if field in result_df.columns:
                    result_df = self._convert_int_to_bigint(result_df, field)
        
        # Process remaining string columns with inference
        for field in result_df.schema.fields:
            if isinstance(field.dataType, StringType):
                # Skip if already processed by explicit conversions
                if field.name not in self._get_all_explicit_fields(type_mappings):
                    result_df = self._infer_and_convert(result_df, field.name)
        
        return result_df
    
    def _get_all_explicit_fields(self, type_mappings: Dict) -> List[str]:
        """Get all fields that have explicit conversions defined."""
        all_fields = []
        for mapping in type_mappings.values():
            if isinstance(mapping, dict) and "fields" in mapping:
                all_fields.extend(mapping["fields"])
        return all_fields
    
    def _convert_unix_timestamp_to_iso8601(self, df: DataFrame, col_name: str) -> DataFrame:
        """
        Convert BIGINT Unix timestamp to TIMESTAMP ISO 8601.
        
        Args:
            df: DataFrame containing the column
            col_name: Name of the column to convert
            
        Returns:
            DataFrame with the column converted to timestamp
            
        Example:
            1706025600 → 2024-01-23T12:00:00Z
        """
        # Convert Unix timestamp (seconds since epoch) to timestamp
        return df.withColumn(
            col_name,
            when(col(col_name).isNotNull(), from_unixtime(col(col_name)))
            .otherwise(None)
            .cast(TimestampType())
        )
    
    def _convert_tinyint_to_boolean(self, df: DataFrame, col_name: str) -> DataFrame:
        """
        Convert TINYINT(1) to BOOLEAN.
        
        Args:
            df: DataFrame containing the column
            col_name: Name of the column to convert
            
        Returns:
            DataFrame with the column converted to boolean
            
        Example:
            1 → true, 0 → false
        """
        return df.withColumn(
            col_name,
            when(col(col_name).isNull(), None)
            .when(col(col_name) == 1, True)
            .when(col(col_name) == 0, False)
            .otherwise(None)
        )
    
    def _convert_decimal_to_numeric(self, df: DataFrame, col_name: str, 
                                   precision: int = 12, scale: int = 9) -> DataFrame:
        """
        Convert DECIMAL(12,9) to NUMERIC(12,9) preserving precision.
        
        Args:
            df: DataFrame containing the column
            col_name: Name of the column to convert
            precision: Numeric precision (default 12)
            scale: Numeric scale (default 9)
            
        Returns:
            DataFrame with the column converted to numeric
            
        Example:
            -12.046374000 → -12.046374000 (preserving precision)
        """
        return df.withColumn(
            col_name,
            col(col_name).cast(DecimalType(precision, scale))
        )
    
    def _convert_int_to_bigint(self, df: DataFrame, col_name: str) -> DataFrame:
        """
        Convert INT to BIGINT for IDs.
        
        Args:
            df: DataFrame containing the column
            col_name: Name of the column to convert
            
        Returns:
            DataFrame with the column converted to bigint
            
        Example:
            123456 → 123456 (but with larger range)
        """
        return df.withColumn(
            col_name,
            col(col_name).cast(LongType())
        )
    
    def _infer_and_convert(self, df: DataFrame, col_name: str) -> DataFrame:
        """
        Infer the correct type for a string column and convert it.
        
        Args:
            df: DataFrame containing the column
            col_name: Name of the column to convert
            
        Returns:
            DataFrame with the column converted to inferred type
        """
        try:
            # Sample values from the column (non-null only)
            sample_values = (
                df.select(col_name)
                .filter(col(col_name).isNotNull())
                .limit(self.inference_sample_size)
                .collect()
            )
            
            if not sample_values:
                # No non-null values to infer from
                return df
            
            # Extract string values
            values = [row[col_name] for row in sample_values if row[col_name] is not None]
            
            if not values:
                return df
        except Exception as e:
            # If sampling fails (e.g., QUERY_ONLY_CORRUPT_RECORD_COLUMN error),
            # skip type inference for this column
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Could not infer type for column '{col_name}': {str(e)}")
            return df
        
        # Try to infer type in order of specificity
        # Boolean is most specific, then date/timestamp, then numeric
        
        if self._is_boolean_string(values):
            return self._convert_to_boolean(df, col_name)
        
        if self._is_date_string(values):
            return self._convert_to_date(df, col_name)
        
        if self._is_timestamp_string(values):
            return self._convert_to_timestamp(df, col_name)
        
        if self._is_numeric_string(values):
            return self._convert_to_numeric(df, col_name, values)
        
        # No conversion needed, keep as string
        return df
    
    def _is_boolean_string(self, values: List[str]) -> bool:
        """
        Detect if a column contains boolean string values.
        
        Args:
            values: List of string values to check
            
        Returns:
            True if values represent booleans, False otherwise
        """
        boolean_values = {
            "true", "false", "1", "0", 
            "yes", "no", "y", "n",
            "t", "f"
        }
        
        matches = 0
        for value in values:
            if value and value.lower().strip() in boolean_values:
                matches += 1
        
        return (matches / len(values)) >= self.inference_threshold
    
    def _is_date_string(self, values: List[str]) -> bool:
        """
        Detect if a column contains date string values.
        
        Args:
            values: List of string values to check
            
        Returns:
            True if values represent dates, False otherwise
        """
        # Common date patterns
        date_patterns = [
            r'^\d{4}-\d{2}-\d{2}$',  # YYYY-MM-DD
            r'^\d{2}/\d{2}/\d{4}$',  # DD/MM/YYYY or MM/DD/YYYY
            r'^\d{4}/\d{2}/\d{2}$',  # YYYY/MM/DD
        ]
        
        matches = 0
        for value in values:
            if not value:
                continue
            
            value_str = str(value).strip()
            
            # Check if it matches any date pattern
            for pattern in date_patterns:
                if re.match(pattern, value_str):
                    # Try to parse it to confirm it's a valid date
                    try:
                        # Try different formats
                        for fmt in ['%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y', '%Y/%m/%d']:
                            try:
                                datetime.strptime(value_str, fmt)
                                matches += 1
                                break
                            except ValueError:
                                continue
                        break
                    except:
                        pass
        
        return (matches / len(values)) >= self.inference_threshold
    
    def _is_timestamp_string(self, values: List[str]) -> bool:
        """
        Detect if a column contains timestamp string values.
        
        Args:
            values: List of string values to check
            
        Returns:
            True if values represent timestamps, False otherwise
        """
        # Common timestamp patterns
        timestamp_patterns = [
            r'^\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}',  # YYYY-MM-DD HH:MM:SS
            r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}',    # ISO format
            r'^\d{2}/\d{2}/\d{4}\s+\d{2}:\d{2}:\d{2}',  # DD/MM/YYYY HH:MM:SS
        ]
        
        matches = 0
        for value in values:
            if not value:
                continue
            
            value_str = str(value).strip()
            
            # Check if it matches any timestamp pattern
            for pattern in timestamp_patterns:
                if re.match(pattern, value_str):
                    matches += 1
                    break
        
        return (matches / len(values)) >= self.inference_threshold
    
    def _is_numeric_string(self, values: List[str]) -> bool:
        """
        Detect if a column contains numeric string values.
        
        Args:
            values: List of string values to check
            
        Returns:
            True if values represent numbers, False otherwise
        """
        matches = 0
        for value in values:
            if not value:
                continue
            
            value_str = str(value).strip()
            
            # Try to parse as number
            try:
                float(value_str)
                matches += 1
            except ValueError:
                pass
        
        return (matches / len(values)) >= self.inference_threshold
    
    def _convert_to_boolean(self, df: DataFrame, col_name: str) -> DataFrame:
        """
        Convert a string column to BooleanType.
        
        Args:
            df: DataFrame containing the column
            col_name: Name of the column to convert
            
        Returns:
            DataFrame with the column converted to boolean
        """
        # Map string values to boolean
        boolean_expr = (
            when(col(col_name).isNull(), None)
            .when(lower(col(col_name).cast("string")).isin(["true", "1", "yes", "y", "t"]), True)
            .when(lower(col(col_name).cast("string")).isin(["false", "0", "no", "n", "f"]), False)
            .otherwise(None)
        )
        
        # Replace the column
        return df.withColumn(col_name, boolean_expr)
    
    def _convert_to_date(self, df: DataFrame, col_name: str) -> DataFrame:
        """
        Convert a string column to DateType.
        
        Args:
            df: DataFrame containing the column
            col_name: Name of the column to convert
            
        Returns:
            DataFrame with the column converted to date
        """
        from pyspark.sql.functions import to_date, coalesce
        
        # Try multiple date formats
        date_expr = coalesce(
            to_date(col(col_name), "yyyy-MM-dd"),
            to_date(col(col_name), "dd/MM/yyyy"),
            to_date(col(col_name), "MM/dd/yyyy"),
            to_date(col(col_name), "yyyy/MM/dd")
        )
        
        return df.withColumn(col_name, date_expr)
    
    def _convert_to_timestamp(self, df: DataFrame, col_name: str) -> DataFrame:
        """
        Convert a string column to TimestampType.
        
        Args:
            df: DataFrame containing the column
            col_name: Name of the column to convert
            
        Returns:
            DataFrame with the column converted to timestamp
        """
        from pyspark.sql.functions import to_timestamp, coalesce
        
        # Try multiple timestamp formats
        timestamp_expr = coalesce(
            to_timestamp(col(col_name), "yyyy-MM-dd HH:mm:ss"),
            to_timestamp(col(col_name), "yyyy-MM-dd'T'HH:mm:ss"),
            to_timestamp(col(col_name), "dd/MM/yyyy HH:mm:ss"),
            to_timestamp(col(col_name), "MM/dd/yyyy HH:mm:ss")
        )
        
        return df.withColumn(col_name, timestamp_expr)
    
    def _convert_to_numeric(self, df: DataFrame, col_name: str, sample_values: List[str]) -> DataFrame:
        """
        Convert a string column to appropriate numeric type.
        
        Determines whether to use IntegerType, LongType, or DecimalType
        based on the sample values.
        
        Args:
            df: DataFrame containing the column
            col_name: Name of the column to convert
            sample_values: Sample values to determine numeric type
            
        Returns:
            DataFrame with the column converted to numeric type
        """
        # Analyze sample values to determine numeric type
        has_decimal = False
        max_value = 0
        
        for value in sample_values:
            if not value:
                continue
            
            try:
                num_value = float(str(value).strip())
                
                # Check if it has decimal places
                if '.' in str(value) or num_value != int(num_value):
                    has_decimal = True
                
                # Track maximum value
                max_value = max(max_value, abs(num_value))
            except ValueError:
                pass
        
        # Determine appropriate type
        if has_decimal:
            # Use DecimalType for decimal numbers
            return df.withColumn(col_name, col(col_name).cast(DecimalType(18, 2)))
        elif max_value > 2147483647:  # Max int value
            # Use LongType for large integers
            return df.withColumn(col_name, col(col_name).cast(LongType()))
        else:
            # Use IntegerType for regular integers
            return df.withColumn(col_name, col(col_name).cast(IntegerType()))
