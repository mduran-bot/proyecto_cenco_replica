"""
Tests unitarios para S3Writer.

Valida la escritura de datos a S3 Bronze con particionamiento.
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from botocore.exceptions import ClientError
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from s3_writer import S3Writer


class TestS3WriterInitialization:
    """Tests de inicialización del S3Writer."""
    
    @patch('s3_writer.boto3')
    def test_initialization_with_bucket_name(self, mock_boto3):
        """Test: Inicialización con nombre de bucket."""
        mock_client = Mock()
        mock_boto3.client.return_value = mock_client
        
        writer = S3Writer(bucket_name="test-bucket")
        
        assert writer.bucket_name == "test-bucket"
        mock_boto3.client.assert_called_once()
    
    @patch('s3_writer.boto3')
    def test_initialization_with_endpoint_url(self, mock_boto3):
        """Test: Inicialización con endpoint URL para LocalStack."""
        mock_client = Mock()
        mock_boto3.client.return_value = mock_client
        
        writer = S3Writer(
            bucket_name="test-bucket",
            endpoint_url="http://localhost:4566"
        )
        
        # Verificar que se pasó el endpoint_url
        call_kwargs = mock_boto3.client.call_args[1]
        assert call_kwargs['endpoint_url'] == "http://localhost:4566"


class TestEnsureBucketExists:
    """Tests del método ensure_bucket_exists."""
    
    @patch('s3_writer.boto3')
    def test_bucket_already_exists(self, mock_boto3):
        """Test: Bucket ya existe."""
        mock_client = Mock()
        mock_client.head_bucket = Mock()  # No lanza excepción
        mock_boto3.client.return_value = mock_client
        
        writer = S3Writer(bucket_name="test-bucket")
        writer.ensure_bucket_exists()
        
        # Verificar que se llamó head_bucket
        mock_client.head_bucket.assert_called_once_with(Bucket="test-bucket")
        # Verificar que NO se llamó create_bucket
        mock_client.create_bucket.assert_not_called()
    
    @patch('s3_writer.boto3')
    def test_bucket_does_not_exist(self, mock_boto3):
        """Test: Bucket no existe, debe crearse."""
        mock_client = Mock()
        
        # head_bucket lanza ClientError (bucket no existe)
        error_response = {'Error': {'Code': '404'}}
        mock_client.head_bucket.side_effect = ClientError(error_response, 'HeadBucket')
        mock_client.create_bucket = Mock()
        
        mock_boto3.client.return_value = mock_client
        
        writer = S3Writer(bucket_name="test-bucket")
        writer.ensure_bucket_exists()
        
        # Verificar que se intentó crear el bucket
        mock_client.create_bucket.assert_called_once_with(Bucket="test-bucket")


class TestWriteToBronze:
    """Tests del método write_to_bronze."""
    
    @patch('s3_writer.boto3')
    def test_write_to_bronze_success(self, mock_boto3):
        """Test: Escribir datos exitosamente."""
        mock_client = Mock()
        mock_client.put_object = Mock()
        mock_boto3.client.return_value = mock_client
        
        writer = S3Writer(bucket_name="bronze-bucket")
        
        # Datos de prueba
        data = [
            {'id': '1', 'status': 'active'},
            {'id': '2', 'status': 'pending'}
        ]
        
        execution_date = datetime(2024, 1, 15, 10, 30, 0)
        
        # Execute
        result = writer.write_to_bronze(
            data=data,
            client='wongio',
            data_type='orders',
            execution_date=execution_date
        )
        
        # Verify
        assert result['success'] is True
        assert result['records_written'] == 2
        assert 'wongio/orders' in result['s3_path']
        assert 'year=2024' in result['s3_path']
        assert 'month=01' in result['s3_path']
        assert 'day=15' in result['s3_path']
        assert result['file_size_mb'] > 0
        
        # Verificar que se llamó put_object
        mock_client.put_object.assert_called_once()
        
        # Verificar parámetros del put_object
        call_kwargs = mock_client.put_object.call_args[1]
        assert call_kwargs['Bucket'] == 'bronze-bucket'
        assert 'wongio/orders' in call_kwargs['Key']
        assert call_kwargs['ContentType'] == 'application/json'
    
    @patch('s3_writer.boto3')
    def test_write_to_bronze_empty_data(self, mock_boto3):
        """Test: Escribir datos vacíos."""
        mock_client = Mock()
        mock_boto3.client.return_value = mock_client
        
        writer = S3Writer(bucket_name="bronze-bucket")
        
        # Execute
        result = writer.write_to_bronze(
            data=[],
            client='wongio',
            data_type='orders'
        )
        
        # Verify
        assert result['success'] is True
        assert result['records_written'] == 0
        assert result['s3_path'] is None
        assert 'No data to write' in result['message']
        
        # Verificar que NO se llamó put_object
        mock_client.put_object.assert_not_called()
    
    @patch('s3_writer.boto3')
    def test_write_to_bronze_with_default_date(self, mock_boto3):
        """Test: Escribir datos con fecha por defecto (now)."""
        mock_client = Mock()
        mock_client.put_object = Mock()
        mock_boto3.client.return_value = mock_client
        
        writer = S3Writer(bucket_name="bronze-bucket")
        
        data = [{'id': '1'}]
        
        # Execute (sin execution_date)
        result = writer.write_to_bronze(
            data=data,
            client='wongio',
            data_type='orders'
        )
        
        # Verify
        assert result['success'] is True
        assert result['records_written'] == 1
        # Debe tener particionamiento por fecha
        assert 'year=' in result['s3_path']
        assert 'month=' in result['s3_path']
        assert 'day=' in result['s3_path']
    
    @patch('s3_writer.boto3')
    def test_write_to_bronze_partitioning(self, mock_boto3):
        """Test: Verificar estructura de particionamiento correcta."""
        mock_client = Mock()
        mock_client.put_object = Mock()
        mock_boto3.client.return_value = mock_client
        
        writer = S3Writer(bucket_name="bronze-bucket")
        
        data = [{'id': '1'}]
        execution_date = datetime(2024, 3, 5, 14, 30, 0)
        
        # Execute
        result = writer.write_to_bronze(
            data=data,
            client='metro',
            data_type='products',
            execution_date=execution_date
        )
        
        # Verify estructura: {client}/{data_type}/year={YYYY}/month={MM}/day={DD}/{timestamp}.json
        s3_path = result['s3_path']
        assert 'metro/products' in s3_path
        assert 'year=2024' in s3_path
        assert 'month=03' in s3_path
        assert 'day=05' in s3_path
        assert '.json' in s3_path
    
    @patch('s3_writer.boto3')
    def test_write_to_bronze_error_handling(self, mock_boto3):
        """Test: Manejo de errores al escribir."""
        mock_client = Mock()
        
        # Simular error en put_object
        mock_client.put_object.side_effect = Exception("S3 connection error")
        mock_boto3.client.return_value = mock_client
        
        writer = S3Writer(bucket_name="bronze-bucket")
        
        data = [{'id': '1'}]
        
        # Execute
        result = writer.write_to_bronze(
            data=data,
            client='wongio',
            data_type='orders'
        )
        
        # Verify
        assert result['success'] is False
        assert result['records_written'] == 0
        assert result['s3_path'] is None
        assert 'error' in result
        assert 'S3 connection error' in result['error']
    
    @patch('s3_writer.boto3')
    def test_write_to_bronze_json_serialization(self, mock_boto3):
        """Test: Serialización JSON correcta."""
        mock_client = Mock()
        mock_client.put_object = Mock()
        mock_boto3.client.return_value = mock_client
        
        writer = S3Writer(bucket_name="bronze-bucket")
        
        # Datos con diferentes tipos
        data = [
            {
                'id': '1',
                'quantity': 100,
                'price': 99.99,
                'active': True,
                'created_at': datetime(2024, 1, 15, 10, 0, 0)
            }
        ]
        
        # Execute
        result = writer.write_to_bronze(
            data=data,
            client='wongio',
            data_type='orders'
        )
        
        # Verify
        assert result['success'] is True
        
        # Verificar que el JSON se serializó correctamente
        call_kwargs = mock_client.put_object.call_args[1]
        json_body = call_kwargs['Body']
        
        # Debe ser bytes
        assert isinstance(json_body, bytes)
        
        # Debe ser JSON válido
        parsed = json.loads(json_body.decode('utf-8'))
        assert len(parsed) == 1
        assert parsed[0]['id'] == '1'


class TestListFiles:
    """Tests del método list_files."""
    
    @patch('s3_writer.boto3')
    def test_list_files_success(self, mock_boto3):
        """Test: Listar archivos exitosamente."""
        mock_client = Mock()
        
        # Simular respuesta de list_objects_v2
        mock_client.list_objects_v2.return_value = {
            'Contents': [
                {
                    'Key': 'wongio/orders/year=2024/month=01/day=15/1705315200.json',
                    'Size': 1024,
                    'LastModified': datetime(2024, 1, 15, 10, 0, 0)
                },
                {
                    'Key': 'wongio/orders/year=2024/month=01/day=15/1705318800.json',
                    'Size': 2048,
                    'LastModified': datetime(2024, 1, 15, 11, 0, 0)
                }
            ]
        }
        
        mock_boto3.client.return_value = mock_client
        
        writer = S3Writer(bucket_name="bronze-bucket")
        
        # Execute
        files = writer.list_files(client='wongio', data_type='orders')
        
        # Verify
        assert len(files) == 2
        assert files[0]['key'] == 'wongio/orders/year=2024/month=01/day=15/1705315200.json'
        assert files[0]['size'] == 1024
        assert 's3://bronze-bucket' in files[0]['full_path']
        
        # Verificar parámetros de list_objects_v2
        call_kwargs = mock_client.list_objects_v2.call_args[1]
        assert call_kwargs['Bucket'] == 'bronze-bucket'
        assert call_kwargs['Prefix'] == 'wongio/orders/'
    
    @patch('s3_writer.boto3')
    def test_list_files_empty(self, mock_boto3):
        """Test: Listar archivos cuando no hay ninguno."""
        mock_client = Mock()
        
        # Respuesta sin Contents
        mock_client.list_objects_v2.return_value = {}
        
        mock_boto3.client.return_value = mock_client
        
        writer = S3Writer(bucket_name="bronze-bucket")
        
        # Execute
        files = writer.list_files(client='wongio', data_type='orders')
        
        # Verify
        assert len(files) == 0
    
    @patch('s3_writer.boto3')
    def test_list_files_with_max_keys(self, mock_boto3):
        """Test: Listar archivos con límite."""
        mock_client = Mock()
        mock_client.list_objects_v2.return_value = {'Contents': []}
        mock_boto3.client.return_value = mock_client
        
        writer = S3Writer(bucket_name="bronze-bucket")
        
        # Execute
        writer.list_files(client='wongio', data_type='orders', max_keys=5)
        
        # Verify
        call_kwargs = mock_client.list_objects_v2.call_args[1]
        assert call_kwargs['MaxKeys'] == 5
    
    @patch('s3_writer.boto3')
    def test_list_files_error_handling(self, mock_boto3):
        """Test: Manejo de errores al listar."""
        mock_client = Mock()
        mock_client.list_objects_v2.side_effect = Exception("S3 error")
        mock_boto3.client.return_value = mock_client
        
        writer = S3Writer(bucket_name="bronze-bucket")
        
        # Execute
        files = writer.list_files(client='wongio', data_type='orders')
        
        # Verify - debe retornar lista vacía en caso de error
        assert len(files) == 0


class TestReadFile:
    """Tests del método read_file."""
    
    @patch('s3_writer.boto3')
    def test_read_file_success(self, mock_boto3):
        """Test: Leer archivo exitosamente."""
        mock_client = Mock()
        
        # Simular respuesta de get_object
        test_data = [{'id': '1', 'status': 'active'}]
        json_data = json.dumps(test_data)
        
        mock_body = Mock()
        mock_body.read.return_value = json_data.encode('utf-8')
        
        mock_client.get_object.return_value = {'Body': mock_body}
        mock_boto3.client.return_value = mock_client
        
        writer = S3Writer(bucket_name="bronze-bucket")
        
        # Execute
        data = writer.read_file('wongio/orders/year=2024/month=01/day=15/1705315200.json')
        
        # Verify
        assert len(data) == 1
        assert data[0]['id'] == '1'
        assert data[0]['status'] == 'active'
        
        # Verificar parámetros de get_object
        call_kwargs = mock_client.get_object.call_args[1]
        assert call_kwargs['Bucket'] == 'bronze-bucket'
        assert call_kwargs['Key'] == 'wongio/orders/year=2024/month=01/day=15/1705315200.json'
    
    @patch('s3_writer.boto3')
    def test_read_file_empty(self, mock_boto3):
        """Test: Leer archivo vacío."""
        mock_client = Mock()
        
        mock_body = Mock()
        mock_body.read.return_value = b'[]'
        
        mock_client.get_object.return_value = {'Body': mock_body}
        mock_boto3.client.return_value = mock_client
        
        writer = S3Writer(bucket_name="bronze-bucket")
        
        # Execute
        data = writer.read_file('test.json')
        
        # Verify
        assert len(data) == 0
    
    @patch('s3_writer.boto3')
    def test_read_file_error_handling(self, mock_boto3):
        """Test: Manejo de errores al leer."""
        mock_client = Mock()
        mock_client.get_object.side_effect = Exception("File not found")
        mock_boto3.client.return_value = mock_client
        
        writer = S3Writer(bucket_name="bronze-bucket")
        
        # Execute
        data = writer.read_file('nonexistent.json')
        
        # Verify - debe retornar lista vacía en caso de error
        assert len(data) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
