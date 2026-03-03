"""
IncrementalProcessor Module
Procesa solo datos nuevos basándose en el último timestamp procesado.
"""
import json
import boto3
from datetime import datetime, timezone
from pyspark.sql import DataFrame
from pyspark.sql.functions import col, max as spark_max


class IncrementalProcessor:
    
    def __init__(self):
        self.s3_client = boto3.client(
            's3',
            endpoint_url='http://localhost:4566',
            aws_access_key_id='test',
            aws_secret_access_key='test'
        )
    
    def transform(self, df: DataFrame, config: dict) -> DataFrame:
        incr_config = config.get("incremental", {})
        
        if not incr_config.get("enabled", False):
            return df
        
        ts_col = incr_config.get("timestamp_column", "fecha_venta")
        last_ts = self._get_last_processed_timestamp(incr_config)
        
        if last_ts:
            df = df.filter(col(ts_col) > last_ts)
        
        return df
    
    def update_timestamp(self, df: DataFrame, config: dict):
        """Llamar DESPUÉS de escribir exitosamente"""
        incr_config = config.get("incremental", {})
        ts_col = incr_config.get("timestamp_column", "fecha_venta")
        
        max_ts = df.select(spark_max(col(ts_col))).collect()[0][0]
        if max_ts:
            self._update_last_processed_timestamp(incr_config, max_ts)
    
    def _get_last_processed_timestamp(self, incr_config: dict):
        try:
            bucket = incr_config["metadata_bucket"]
            key = incr_config["metadata_key"]
            response = self.s3_client.get_object(Bucket=bucket, Key=key)
            data = json.loads(response['Body'].read())
            return data.get("last_timestamp")
        except Exception:
            return None  # Primera ejecución
    
    def _update_last_processed_timestamp(self, incr_config: dict, timestamp):
        try:
            bucket = incr_config["metadata_bucket"]
            key = incr_config["metadata_key"]
            data = {"last_timestamp": str(timestamp)}
            self.s3_client.put_object(
                Bucket=bucket,
                Key=key,
                Body=json.dumps(data)
            )
        except Exception as e:
            print(f"[WARNING] No se pudo actualizar timestamp: {e}")