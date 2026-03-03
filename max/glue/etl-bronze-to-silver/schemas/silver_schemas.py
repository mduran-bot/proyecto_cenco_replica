"""
Silver Layer Schema Definitions

This module contains PySpark schema definitions for Silver layer Iceberg tables.
Silver layer contains clean, normalized, and deduplicated data.

Requirements: 2.5, 5.1
"""

from pyspark.sql.types import (
    StructType, StructField, StringType, TimestampType, 
    DecimalType, BooleanType, IntegerType, LongType
)


# Orders Silver Schema
orders_silver_schema = StructType([
    StructField("order_id", StringType(), nullable=False),
    StructField("date_created", TimestampType(), nullable=False),
    StructField("date_modified", TimestampType(), nullable=True),
    StructField("status", StringType(), nullable=False),
    StructField("amount", DecimalType(10, 2), nullable=False),
    StructField("customer_email", StringType(), nullable=True),
    StructField("customer_phone", StringType(), nullable=True),
    StructField("source", StringType(), nullable=False),
    StructField("ingestion_timestamp", TimestampType(), nullable=False),
    StructField("processing_timestamp", TimestampType(), nullable=False),
    # Data Gap metadata
    StructField("data_gap_flag", BooleanType(), nullable=False),
    StructField("gap_reason", StringType(), nullable=True),
    # Audit fields
    StructField("etl_job_id", StringType(), nullable=False),
    StructField("record_version", IntegerType(), nullable=False)
])

# Partition specification for orders
orders_partition_spec = {
    "partition_by": ["year(date_created)", "month(date_created)", "day(date_created)"],
    "rationale": "Queries typically filter by date ranges"
}


# Products Silver Schema
products_silver_schema = StructType([
    StructField("product_id", StringType(), nullable=False),
    StructField("sku", StringType(), nullable=False),
    StructField("name", StringType(), nullable=False),
    StructField("category", StringType(), nullable=True),
    StructField("brand", StringType(), nullable=True),
    StructField("price", DecimalType(10, 2), nullable=True),
    StructField("date_created", TimestampType(), nullable=False),
    StructField("date_modified", TimestampType(), nullable=True),
    StructField("source", StringType(), nullable=False),
    StructField("ingestion_timestamp", TimestampType(), nullable=False),
    StructField("processing_timestamp", TimestampType(), nullable=False),
    # Data Gap metadata
    StructField("data_gap_flag", BooleanType(), nullable=False),
    StructField("gap_reason", StringType(), nullable=True),
    # Audit fields
    StructField("etl_job_id", StringType(), nullable=False),
    StructField("record_version", IntegerType(), nullable=False)
])

# Partition specification for products
products_partition_spec = {
    "partition_by": ["category"],
    "rationale": "Products queried by category for analytics"
}


# Stock Silver Schema
stock_silver_schema = StructType([
    StructField("stock_id", StringType(), nullable=False),
    StructField("store_id", StringType(), nullable=False),
    StructField("product_id", StringType(), nullable=False),
    StructField("sku", StringType(), nullable=False),
    StructField("quantity", LongType(), nullable=False),
    StructField("date", TimestampType(), nullable=False),
    StructField("date_modified", TimestampType(), nullable=True),
    StructField("source", StringType(), nullable=False),
    StructField("ingestion_timestamp", TimestampType(), nullable=False),
    StructField("processing_timestamp", TimestampType(), nullable=False),
    # Data Gap metadata
    StructField("data_gap_flag", BooleanType(), nullable=False),
    StructField("gap_reason", StringType(), nullable=True),
    # Audit fields
    StructField("etl_job_id", StringType(), nullable=False),
    StructField("record_version", IntegerType(), nullable=False)
])

# Partition specification for stock
stock_partition_spec = {
    "partition_by": ["store_id", "year(date)", "month(date)"],
    "rationale": "Stock queries are store-specific and date-based"
}


# Prices Silver Schema
prices_silver_schema = StructType([
    StructField("price_id", StringType(), nullable=False),
    StructField("product_id", StringType(), nullable=False),
    StructField("sku", StringType(), nullable=False),
    StructField("price", DecimalType(10, 2), nullable=False),
    StructField("currency", StringType(), nullable=False),
    StructField("effective_date", TimestampType(), nullable=False),
    StructField("expiration_date", TimestampType(), nullable=True),
    StructField("date_modified", TimestampType(), nullable=True),
    StructField("source", StringType(), nullable=False),
    StructField("ingestion_timestamp", TimestampType(), nullable=False),
    StructField("processing_timestamp", TimestampType(), nullable=False),
    # Data Gap metadata
    StructField("data_gap_flag", BooleanType(), nullable=False),
    StructField("gap_reason", StringType(), nullable=True),
    # Audit fields
    StructField("etl_job_id", StringType(), nullable=False),
    StructField("record_version", IntegerType(), nullable=False)
])

# Partition specification for prices
prices_partition_spec = {
    "partition_by": ["year(effective_date)", "month(effective_date)"],
    "rationale": "Prices queried by effective date for historical analysis"
}
