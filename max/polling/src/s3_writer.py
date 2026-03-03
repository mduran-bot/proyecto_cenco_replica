"""
S3Writer - Escritor de datos a S3 Bronze con particionamiento.

Este módulo maneja la escritura de datos al bucket S3 Bronze con:
- Particionamiento por fecha (year=/month=/day=/)
- Formato Parquet
- Estructura multi-tenant (client/data_type/)
"""

import json
import boto3
from datetime import datetime
from typing import List, Dict, Optional, Any
import logging

logger = logging.getLogger(__name__)


class S3Writer:
    """
    Escritor de datos a S3 Bronze con particionamiento.
    
    Estructura de paths:
    s3://{bucket}/{client}/{data_type}/year={YYYY}/month={MM}/day={DD}/{timestamp}.json
    
    Ejemplo:
    s3://bronze-bucket/wongio/orders/year=2026/month=03/day=02/1709398800.json
    """
    
    def __init__(self, bucket_name: str, endpoint_url: Optional[str] = None):
        """
        Inicializa el escritor S3.
        
        Args:
            bucket_name: Nombre del bucket S3 Bronze
            endpoint_url: URL del endpoint S3 (para LocalStack)
        """
        self.bucket_name = bucket_name
        
        # Cliente S3
        if endpoint_url:
            # LocalStack
            self.s3_client = boto3.client(
                's3',
                endpoint_url=endpoint_url,
                region_name='us-east-1',
                aws_access_key_id='test',
                aws_secret_access_key='test'
            )
        else:
            # AWS real
            self.s3_client = boto3.client('s3', region_name='us-east-1')
        
        logger.info(f"S3Writer inicializado para bucket: {bucket_name}")
    
    def ensure_bucket_exists(self):
        """
        Verifica que el bucket exista, si no lo crea.
        """
        try:
            self.s3_client.head_bucket(Bucket=self.bucket_name)
            logger.info(f"Bucket '{self.bucket_name}' existe")
        except:
            logger.info(f"Creando bucket '{self.bucket_name}'...")
            self.s3_client.create_bucket(Bucket=self.bucket_name)
            logger.info(f"Bucket '{self.bucket_name}' creado")
    
    def write_to_bronze(
        self,
        data: List[Dict],
        client: str,
        data_type: str,
        execution_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Escribe datos al bucket S3 Bronze con particionamiento.
        
        Args:
            data: Lista de registros a escribir
            client: Nombre del cliente (wongio, metro)
            data_type: Tipo de dato (orders, products, etc.)
            execution_date: Fecha de ejecución (default: now)
        
        Returns:
            Dict con:
                - success: Boolean indicando éxito
                - records_written: Número de registros escritos
                - s3_path: Path S3 completo del archivo
                - file_size_mb: Tamaño del archivo en MB
        
        Example:
            >>> writer = S3Writer("bronze-bucket")
            >>> result = writer.write_to_bronze(
            ...     data=[{"id": "123", "status": "active"}],
            ...     client="wongio",
            ...     data_type="orders"
            ... )
            >>> print(result)
            {
                'success': True,
                'records_written': 1,
                's3_path': 's3://bronze-bucket/wongio/orders/year=2026/...',
                'file_size_mb': 0.05
            }
        """
        if not data:
            logger.warning("No hay datos para escribir a S3")
            return {
                'success': True,
                'records_written': 0,
                's3_path': None,
                'file_size_mb': 0.0,
                'message': 'No data to write'
            }
        
        try:
            # Fecha de ejecución
            if execution_date is None:
                execution_date = datetime.now()
            
            # Construir path con particionamiento
            year = execution_date.strftime("%Y")
            month = execution_date.strftime("%m")
            day = execution_date.strftime("%d")
            timestamp = int(execution_date.timestamp())
            
            # Path: {client}/{data_type}/year={YYYY}/month={MM}/day={DD}/{timestamp}.json
            s3_key = (
                f"{client}/{data_type}/"
                f"year={year}/month={month}/day={day}/"
                f"{timestamp}.json"
            )
            
            # Convertir datos a JSON
            json_data = json.dumps(data, indent=2, default=str)
            json_bytes = json_data.encode('utf-8')
            file_size_bytes = len(json_bytes)
            file_size_mb = file_size_bytes / (1024 * 1024)
            
            # Escribir a S3
            logger.info(f"Escribiendo {len(data)} registros a s3://{self.bucket_name}/{s3_key}")
            
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=json_bytes,
                ContentType='application/json'
            )
            
            full_path = f"s3://{self.bucket_name}/{s3_key}"
            logger.info(f"✓ Datos escritos exitosamente: {full_path}")
            
            return {
                'success': True,
                'records_written': len(data),
                's3_path': full_path,
                'file_size_mb': file_size_mb
            }
            
        except Exception as e:
            logger.error(f"Error escribiendo a S3: {e}")
            return {
                'success': False,
                'records_written': 0,
                's3_path': None,
                'file_size_mb': 0.0,
                'error': str(e)
            }
    
    def list_files(self, client: str, data_type: str, max_keys: int = 10) -> List[Dict]:
        """
        Lista archivos en S3 para un cliente y tipo de dato.
        
        Args:
            client: Nombre del cliente
            data_type: Tipo de dato
            max_keys: Número máximo de archivos a listar
        
        Returns:
            List[Dict]: Lista de archivos con metadata
        """
        prefix = f"{client}/{data_type}/"
        
        logger.info(f"Listando archivos en s3://{self.bucket_name}/{prefix}")
        
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix,
                MaxKeys=max_keys
            )
            
            files = []
            if 'Contents' in response:
                for obj in response['Contents']:
                    files.append({
                        'key': obj['Key'],
                        'size': obj['Size'],
                        'last_modified': obj['LastModified'],
                        'full_path': f"s3://{self.bucket_name}/{obj['Key']}"
                    })
            
            logger.info(f"✓ Encontrados {len(files)} archivos")
            return files
            
        except Exception as e:
            logger.error(f"Error listando archivos: {e}")
            return []
    
    def read_file(self, s3_key: str) -> List[Dict]:
        """
        Lee un archivo JSON desde S3.
        
        Args:
            s3_key: Key del archivo en S3
        
        Returns:
            List[Dict]: Datos parseados desde JSON
        """
        logger.info(f"Leyendo s3://{self.bucket_name}/{s3_key}")
        
        try:
            response = self.s3_client.get_object(
                Bucket=self.bucket_name,
                Key=s3_key
            )
            
            json_data = response['Body'].read().decode('utf-8')
            data = json.loads(json_data)
            
            logger.info(f"✓ Archivo leído: {len(data)} registros")
            return data
            
        except Exception as e:
            logger.error(f"Error leyendo archivo: {e}")
            return []
