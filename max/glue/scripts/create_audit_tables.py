"""
Create Audit Tables Script

Este script crea las tablas de auditoría necesarias para el pipeline ETL:
- data_gaps_log: Registra campos faltantes (data gaps) por entidad
- data_quality_issues: Registra problemas de calidad de datos
- schema_changes_log: Registra cambios en esquemas de tablas

Uso:
    python create_audit_tables.py --environment localstack
    python create_audit_tables.py --environment aws --catalog glue_catalog

Requirements: 5.3
"""

import argparse
import sys
import os
from pyspark.sql import SparkSession
from pyspark.sql.types import (
    StructType, StructField, StringType, IntegerType, 
    TimestampType, BooleanType
)


def create_spark_session(environment: str = "localstack") -> SparkSession:
    """
    Crea una SparkSession configurada para el entorno especificado.
    
    Args:
        environment: 'localstack' o 'aws'
        
    Returns:
        SparkSession configurada
    """
    builder = SparkSession.builder.appName("CreateAuditTables")
    
    if environment == "localstack":
        # Configuración para LocalStack
        builder = builder \
            .config("spark.sql.extensions", "org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions") \
            .config("spark.sql.catalog.spark_catalog", "org.apache.iceberg.spark.SparkSessionCatalog") \
            .config("spark.sql.catalog.spark_catalog.type", "hive") \
            .config("spark.hadoop.fs.s3a.endpoint", "http://localhost:4566") \
            .config("spark.hadoop.fs.s3a.access.key", "test") \
            .config("spark.hadoop.fs.s3a.secret.key", "test") \
            .config("spark.hadoop.fs.s3a.path.style.access", "true") \
            .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem")
    else:
        # Configuración para AWS
        builder = builder \
            .config("spark.sql.extensions", "org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions") \
            .config("spark.sql.catalog.glue_catalog", "org.apache.iceberg.spark.SparkCatalog") \
            .config("spark.sql.catalog.glue_catalog.warehouse", "s3://data-lake-silver/") \
            .config("spark.sql.catalog.glue_catalog.catalog-impl", "org.apache.iceberg.aws.glue.GlueCatalog") \
            .config("spark.sql.catalog.glue_catalog.io-impl", "org.apache.iceberg.aws.s3.S3FileIO")
    
    return builder.getOrCreate()


def create_data_gaps_log_table(spark: SparkSession, catalog: str = "spark_catalog"):
    """
    Crea la tabla data_gaps_log en la capa Silver.
    
    Esquema:
    - gap_id: ID único del gap (VARCHAR)
    - entity_type: Tipo de entidad (orders, products, etc.)
    - table_name: Nombre de la tabla Gold (opcional)
    - field_name: Nombre del campo faltante
    - record_count: Cantidad de registros afectados
    - timestamp: Fecha y hora del registro
    
    Args:
        spark: SparkSession activa
        catalog: Nombre del catálogo ('spark_catalog' o 'glue_catalog')
    """
    print("Creating data_gaps_log table...")
    
    # Definir esquema
    schema = StructType([
        StructField("gap_id", StringType(), nullable=False),
        StructField("entity_type", StringType(), nullable=False),
        StructField("table_name", StringType(), nullable=True),
        StructField("field_name", StringType(), nullable=False),
        StructField("record_count", IntegerType(), nullable=False),
        StructField("timestamp", TimestampType(), nullable=False)
    ])
    
    # Crear DataFrame vacío con el esquema
    empty_df = spark.createDataFrame([], schema)
    
    # Crear tabla Iceberg
    table_name = f"{catalog}.silver.data_gaps_log"
    
    try:
        # Intentar crear la tabla
        empty_df.writeTo(table_name) \
            .using("iceberg") \
            .tableProperty("format-version", "2") \
            .tableProperty("write.parquet.compression-codec", "snappy") \
            .create()
        
        print(f"✓ Table {table_name} created successfully")
        
    except Exception as e:
        if "already exists" in str(e).lower():
            print(f"⚠ Table {table_name} already exists, skipping...")
        else:
            print(f"✗ Error creating table {table_name}: {e}")
            raise


def create_data_quality_issues_table(spark: SparkSession, catalog: str = "spark_catalog"):
    """
    Crea la tabla data_quality_issues en la capa Silver.
    
    Esquema:
    - issue_id: ID único del issue (VARCHAR)
    - table_name: Nombre de la tabla afectada
    - record_id: ID del registro con problema
    - validation_rule: Regla de validación que falló
    - error_message: Mensaje de error descriptivo
    - timestamp: Fecha y hora del registro
    
    Args:
        spark: SparkSession activa
        catalog: Nombre del catálogo
    """
    print("Creating data_quality_issues table...")
    
    schema = StructType([
        StructField("issue_id", StringType(), nullable=False),
        StructField("table_name", StringType(), nullable=False),
        StructField("record_id", StringType(), nullable=True),
        StructField("validation_rule", StringType(), nullable=False),
        StructField("error_message", StringType(), nullable=True),
        StructField("timestamp", TimestampType(), nullable=False)
    ])
    
    empty_df = spark.createDataFrame([], schema)
    table_name = f"{catalog}.silver.data_quality_issues"
    
    try:
        empty_df.writeTo(table_name) \
            .using("iceberg") \
            .tableProperty("format-version", "2") \
            .tableProperty("write.parquet.compression-codec", "snappy") \
            .create()
        
        print(f"✓ Table {table_name} created successfully")
        
    except Exception as e:
        if "already exists" in str(e).lower():
            print(f"⚠ Table {table_name} already exists, skipping...")
        else:
            print(f"✗ Error creating table {table_name}: {e}")
            raise


def create_schema_changes_log_table(spark: SparkSession, catalog: str = "spark_catalog"):
    """
    Crea la tabla schema_changes_log en la capa Silver.
    
    Esquema:
    - change_id: ID único del cambio (VARCHAR)
    - table_name: Nombre de la tabla modificada
    - change_type: Tipo de cambio (ADD_COLUMN, RENAME_COLUMN, etc.)
    - column_name: Nombre de la columna afectada
    - old_type: Tipo de dato anterior (opcional)
    - new_type: Tipo de dato nuevo (opcional)
    - timestamp: Fecha y hora del cambio
    
    Args:
        spark: SparkSession activa
        catalog: Nombre del catálogo
    """
    print("Creating schema_changes_log table...")
    
    schema = StructType([
        StructField("change_id", StringType(), nullable=False),
        StructField("table_name", StringType(), nullable=False),
        StructField("change_type", StringType(), nullable=False),
        StructField("column_name", StringType(), nullable=False),
        StructField("old_type", StringType(), nullable=True),
        StructField("new_type", StringType(), nullable=True),
        StructField("timestamp", TimestampType(), nullable=False)
    ])
    
    empty_df = spark.createDataFrame([], schema)
    table_name = f"{catalog}.silver.schema_changes_log"
    
    try:
        empty_df.writeTo(table_name) \
            .using("iceberg") \
            .tableProperty("format-version", "2") \
            .tableProperty("write.parquet.compression-codec", "snappy") \
            .create()
        
        print(f"✓ Table {table_name} created successfully")
        
    except Exception as e:
        if "already exists" in str(e).lower():
            print(f"⚠ Table {table_name} already exists, skipping...")
        else:
            print(f"✗ Error creating table {table_name}: {e}")
            raise


def main():
    """Función principal del script."""
    parser = argparse.ArgumentParser(
        description="Create audit tables for ETL pipeline"
    )
    parser.add_argument(
        "--environment",
        choices=["localstack", "aws"],
        default="localstack",
        help="Environment to create tables in (default: localstack)"
    )
    parser.add_argument(
        "--catalog",
        default="spark_catalog",
        help="Catalog name (default: spark_catalog for LocalStack, glue_catalog for AWS)"
    )
    parser.add_argument(
        "--tables",
        nargs="+",
        choices=["data_gaps_log", "data_quality_issues", "schema_changes_log", "all"],
        default=["all"],
        help="Which tables to create (default: all)"
    )
    
    args = parser.parse_args()
    
    # Ajustar catalog por defecto según environment
    if args.environment == "aws" and args.catalog == "spark_catalog":
        args.catalog = "glue_catalog"
    
    print(f"\n{'='*60}")
    print(f"Creating Audit Tables")
    print(f"{'='*60}")
    print(f"Environment: {args.environment}")
    print(f"Catalog: {args.catalog}")
    print(f"Tables: {', '.join(args.tables)}")
    print(f"{'='*60}\n")
    
    # Crear SparkSession
    spark = create_spark_session(args.environment)
    
    try:
        # Crear tablas según selección
        tables_to_create = args.tables
        if "all" in tables_to_create:
            tables_to_create = ["data_gaps_log", "data_quality_issues", "schema_changes_log"]
        
        if "data_gaps_log" in tables_to_create:
            create_data_gaps_log_table(spark, args.catalog)
        
        if "data_quality_issues" in tables_to_create:
            create_data_quality_issues_table(spark, args.catalog)
        
        if "schema_changes_log" in tables_to_create:
            create_schema_changes_log_table(spark, args.catalog)
        
        print(f"\n{'='*60}")
        print("✓ All audit tables created successfully!")
        print(f"{'='*60}\n")
        
    except Exception as e:
        print(f"\n{'='*60}")
        print(f"✗ Error creating audit tables: {e}")
        print(f"{'='*60}\n")
        sys.exit(1)
    
    finally:
        spark.stop()


if __name__ == "__main__":
    main()
