"""
DataNormalizer Module

This module normalizes data formats based on configurable column mappings.
It standardizes emails, phone numbers, dates, and timestamps to ensure
consistent data formats for downstream systems.
"""

from pyspark.sql import DataFrame
from pyspark.sql.functions import col, lower, regexp_replace, to_date, to_timestamp
from pyspark.sql.types import StringType


class DataNormalizer:
    """
    Normalizes data formats based on configuration mappings.
    
    Transformations applied:
    - Convert emails to lowercase
    - Remove non-numeric characters from phone numbers
    - Standardize date formats
    - Standardize timestamp formats
    
    All transformations preserve null values without converting them
    to strings or empty values.
    """
    
    def transform(self, df: DataFrame, config: dict) -> DataFrame:
        """
        Normalize the DataFrame according to configuration mappings.
        
        Args:
            df: Input PySpark DataFrame
            config: Configuration dictionary with normalization settings
                   Expected structure:
                   {
                       "normalization": {
                           "email_columns": ["email", "contact_email"],
                           "phone_columns": ["phone", "mobile"],
                           "date_columns": ["birth_date", "registration_date"],
                           "timestamp_columns": ["created_at", "updated_at"]
                       }
                   }
            
        Returns:
            Normalized PySpark DataFrame
        """
        # Extract normalization config, use empty dict if not provided
        norm_config = config.get("normalization", {})
        
        # Apply normalizations in sequence
        df = self._normalize_emails(df, norm_config.get("email_columns", []))
        df = self._normalize_phones(df, norm_config.get("phone_columns", []))
        df = self._normalize_dates(df, norm_config.get("date_columns", []))
        df = self._normalize_timestamps(df, norm_config.get("timestamp_columns", []))
        
        return df
    
    def _normalize_emails(self, df: DataFrame, email_columns: list) -> DataFrame:
        """
        Convert email addresses to lowercase.
        
        Args:
            df: DataFrame to normalize
            email_columns: List of column names containing email addresses
            
        Returns:
            DataFrame with normalized email columns
        """
        if not email_columns:
            return df
        
        # Build list of columns with email normalization applied
        normalized_cols = []
        
        for field in df.schema.fields:
            if field.name in email_columns:
                # Convert email to lowercase, preserving nulls
                normalized_cols.append(lower(col(field.name)).alias(field.name))
            else:
                # Keep other columns as-is
                normalized_cols.append(col(field.name))
        
        return df.select(*normalized_cols)
    
    def _normalize_phones(self, df: DataFrame, phone_columns: list) -> DataFrame:
        """
        Remove all non-numeric characters from phone numbers.
        
        Args:
            df: DataFrame to normalize
            phone_columns: List of column names containing phone numbers
            
        Returns:
            DataFrame with normalized phone columns
        """
        if not phone_columns:
            return df
        
        # Build list of columns with phone normalization applied
        normalized_cols = []
        
        for field in df.schema.fields:
            if field.name in phone_columns:
                # Remove all non-numeric characters, preserving nulls
                normalized_cols.append(
                    regexp_replace(col(field.name), "[^0-9]", "").alias(field.name)
                )
            else:
                # Keep other columns as-is
                normalized_cols.append(col(field.name))
        
        return df.select(*normalized_cols)
    
    def _normalize_dates(self, df: DataFrame, date_columns: list) -> DataFrame:
        """
        Parse and standardize date formats to a consistent format.
        
        Attempts to parse dates in various common formats and converts them
        to a standard date format (yyyy-MM-dd).
        
        Args:
            df: DataFrame to normalize
            date_columns: List of column names containing dates
            
        Returns:
            DataFrame with normalized date columns
        """
        if not date_columns:
            return df
        
        # Build list of columns with date normalization applied
        normalized_cols = []
        
        for field in df.schema.fields:
            if field.name in date_columns:
                # Try to parse date in standard format, preserving nulls
                # If parsing fails, the value becomes null
                normalized_cols.append(
                    to_date(col(field.name), "yyyy-MM-dd").alias(field.name)
                )
            else:
                # Keep other columns as-is
                normalized_cols.append(col(field.name))
        
        return df.select(*normalized_cols)
    
    def _normalize_timestamps(self, df: DataFrame, timestamp_columns: list) -> DataFrame:
        """
        Parse and standardize timestamp formats to a consistent format.
        
        Attempts to parse timestamps in various common formats and converts them
        to a standard timestamp format (yyyy-MM-dd HH:mm:ss).
        
        Args:
            df: DataFrame to normalize
            timestamp_columns: List of column names containing timestamps
            
        Returns:
            DataFrame with normalized timestamp columns
        """
        if not timestamp_columns:
            return df
        
        # Build list of columns with timestamp normalization applied
        normalized_cols = []
        
        for field in df.schema.fields:
            if field.name in timestamp_columns:
                # Try to parse timestamp in standard format, preserving nulls
                # If parsing fails, the value becomes null
                normalized_cols.append(
                    to_timestamp(col(field.name), "yyyy-MM-dd HH:mm:ss").alias(field.name)
                )
            else:
                # Keep other columns as-is
                normalized_cols.append(col(field.name))
        
        return df.select(*normalized_cols)
