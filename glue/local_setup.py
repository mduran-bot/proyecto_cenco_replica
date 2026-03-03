"""
Local Development Setup for Glue ETL Jobs

This script sets up a local PySpark environment for testing Glue jobs
without needing AWS infrastructure or Terraform.

Usage:
    python local_setup.py
"""

import os
import sys
from pyspark.sql import SparkSession


def create_local_spark_session(app_name="LocalGlueJob"):
    """
    Create a local Spark session configured for Iceberg and local testing.
    
    This simulates the AWS Glue environment locally.
    """
    # Set environment variables for local testing
    os.environ['AWS_ACCESS_KEY_ID'] = 'test'
    os.environ['AWS_SECRET_ACCESS_KEY'] = 'test'
    os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'
    
    # Create Spark session with Iceberg support
    spark = SparkSession.builder \
        .appName(app_name) \
        .master("local[*]") \
        .config("spark.sql.extensions", "org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions") \
        .config("spark.sql.catalog.local", "org.apache.iceberg.spark.SparkCatalog") \
        .config("spark.sql.catalog.local.type", "hadoop") \
        .config("spark.sql.catalog.local.warehouse", "./local-warehouse") \
        .config("spark.sql.catalog.local.io-impl", "org.apache.iceberg.aws.s3.S3FileIO") \
        .config("spark.hadoop.fs.s3a.endpoint", "http://localhost:4566") \
        .config("spark.hadoop.fs.s3a.access.key", "test") \
        .config("spark.hadoop.fs.s3a.secret.key", "test") \
        .config("spark.hadoop.fs.s3a.path.style.access", "true") \
        .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem") \
        .config("spark.jars.packages", 
                "org.apache.iceberg:iceberg-spark-runtime-3.3_2.12:1.4.2,"
                "org.apache.hadoop:hadoop-aws:3.3.4,"
                "com.amazonaws:aws-java-sdk-bundle:1.12.262") \
        .getOrCreate()
    
    # Set log level to reduce noise
    spark.sparkContext.setLogLevel("WARN")
    
    print(f"✅ Local Spark session created: {app_name}")
    print(f"📁 Warehouse location: ./local-warehouse")
    print(f"🔗 LocalStack endpoint: http://localhost:4566")
    
    return spark


def setup_local_s3_buckets(spark):
    """
    Create local S3 buckets in LocalStack for testing.
    """
    import boto3
    
    # Connect to LocalStack S3
    s3_client = boto3.client(
        's3',
        endpoint_url='http://localhost:4566',
        aws_access_key_id='test',
        aws_secret_access_key='test',
        region_name='us-east-1'
    )
    
    # Create test buckets
    buckets = [
        'test-bronze',
        'test-silver',
        'test-gold'
    ]
    
    for bucket in buckets:
        try:
            s3_client.create_bucket(Bucket=bucket)
            print(f"✅ Created bucket: {bucket}")
        except Exception as e:
            if 'BucketAlreadyOwnedByYou' in str(e):
                print(f"ℹ️  Bucket already exists: {bucket}")
            else:
                print(f"❌ Error creating bucket {bucket}: {e}")


def run_sample_etl():
    """
    Run a sample ETL job to verify the setup works.
    """
    print("\n🚀 Running sample ETL job...")
    
    # Create Spark session
    spark = create_local_spark_session("SampleETL")
    
    # Create sample data
    data = [
        {"id": "1", "name": "Product A", "price": 10.50},
        {"id": "2", "name": "Product B", "price": 20.75},
        {"id": "3", "name": "Product C", "price": 15.00}
    ]
    
    df = spark.createDataFrame(data)
    
    print("\n📊 Sample data:")
    df.show()
    
    # Write to local Iceberg table
    table_name = "local.test_db.sample_products"
    
    print(f"\n💾 Writing to Iceberg table: {table_name}")
    
    df.writeTo(table_name).createOrReplace()
    
    # Read back
    result_df = spark.table(table_name)
    
    print("\n✅ Data read back from Iceberg:")
    result_df.show()
    
    print("\n🎉 Sample ETL completed successfully!")
    
    spark.stop()


if __name__ == "__main__":
    print("=" * 60)
    print("🔧 Local Glue ETL Development Setup")
    print("=" * 60)
    
    # Check if LocalStack is running
    import requests
    try:
        response = requests.get("http://localhost:4566/_localstack/health")
        if response.status_code == 200:
            print("✅ LocalStack is running")
        else:
            print("⚠️  LocalStack might not be fully ready")
    except:
        print("❌ LocalStack is not running!")
        print("   Start it with: docker-compose -f docker-compose.localstack.yml up -d")
        sys.exit(1)
    
    # Setup
    spark = create_local_spark_session()
    setup_local_s3_buckets(spark)
    spark.stop()
    
    # Run sample
    print("\n" + "=" * 60)
    run_sample_etl()
