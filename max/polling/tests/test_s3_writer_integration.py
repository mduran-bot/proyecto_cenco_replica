"""
Tests de integración para S3Writer usando LocalStack.

Estos tests ejecutan código real contra S3 en LocalStack.
"""

import pytest
import os
import sys
from datetime import datetime
import boto3
from botocore.exceptions import ClientError

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from s3_writer import S3Writer


# Configuración de LocalStack
LOCALSTACK_ENDPOINT = os.getenv('LOCALSTACK_ENDPOINT', 'http://localhost:4566')
BUCKET_NAME = 'test-bronze-bucket'


@pytest.fixture(scope='module')
def s3_bucket():
    """Crear bucket de S3 en LocalStack para tests."""
    s3_client = boto3.client(
        's3',
        endpoint_url=LOCALSTACK_ENDPOINT,
        region_name='us-east-1',
        aws_access_key_id='test',
        aws_secret_access_key='test'
    )
    
    # Crear bucket
    try:
        s3_client.create_bucket(Bucket=BUCKET_NAME)
        yield s3_client
        
        # Cleanup: eliminar todos los objetos y el bucket
        try:
            response = s3_client.list_objects_v2(Bucket=BUCKET_NAME)
            if 'Contents' in response:
                for obj in response['Contents']:
                    s3_client.delete_object(Bucket=BUCKET_NAME, Key=obj['Key'])
            s3_client.delete_bucket(Bucket=BUCKET_NAME)
        except:
            pass
            
    except ClientError as e:
        if e.response['Error']['Code'] == 'BucketAlreadyOwnedByYou':
            # Bucket ya existe, usarlo
            yield s3_client
        else:
            raise


@pytest.fixture
def s3_writer():
    """Crear S3Writer conectado a LocalStack."""
    return S3Writer(
        bucket_name=BUCKET_NAME,
        endpoint_url=LOCALSTACK_ENDPOINT
    )


@pytest.fixture(autouse=True)
def cleanup_bucket(s3_bucket):
    """Limpiar bucket antes de cada test."""
    # Eliminar todos los objetos
    try:
        response = s3_bucket.list_objects_v2(Bucket=BUCKET_NAME)
        if 'Contents' in response:
            for obj in response['Contents']:
                s3_bucket.delete_object(Bucket=BUCKET_NAME, Key=obj['Key'])
    except:
        pass
    
    yield


class TestS3WriterIntegration:
    """Tests de integración con LocalStack."""
    
    def test_ensure_bucket_exists(self, s3_writer, s3_bucket):
        """Test: Verificar que el bucket existe."""
        # Execute
        s3_writer.ensure_bucket_exists()
        
        # Verify - no debe lanzar excepción
        response = s3_bucket.head_bucket(Bucket=BUCKET_NAME)
        assert response['ResponseMetadata']['HTTPStatusCode'] == 200
    
    def test_write_to_bronze_success(self, s3_writer, s3_bucket):
        """Test: Escribir datos exitosamente a S3."""
        # Datos de prueba
        data = [
            {'id': '1', 'status': 'active', 'quantity': 100},
            {'id': '2', 'status': 'pending', 'quantity': 50}
        ]
        
        execution_date = datetime(2024, 1, 15, 10, 30, 0)
        
        # Execute
        result = s3_writer.write_to_bronze(
            data=data,
            client='wongio',
            data_type='orders',
            execution_date=execution_date
        )
        
        # Verify resultado
        assert result['success'] is True
        assert result['records_written'] == 2
        assert 'wongio/orders' in result['s3_path']
        assert 'year=2024' in result['s3_path']
        assert 'month=01' in result['s3_path']
        assert 'day=15' in result['s3_path']
        assert result['file_size_mb'] > 0
        
        # Verificar que el archivo existe en S3
        response = s3_bucket.list_objects_v2(
            Bucket=BUCKET_NAME,
            Prefix='wongio/orders/'
        )
        
        assert 'Contents' in response
        assert len(response['Contents']) == 1
        
        # Verificar contenido del archivo
        s3_key = response['Contents'][0]['Key']
        obj = s3_bucket.get_object(Bucket=BUCKET_NAME, Key=s3_key)
        content = obj['Body'].read().decode('utf-8')
        
        import json
        parsed_data = json.loads(content)
        assert len(parsed_data) == 2
        assert parsed_data[0]['id'] == '1'
        assert parsed_data[1]['id'] == '2'
    
    def test_write_to_bronze_empty_data(self, s3_writer, s3_bucket):
        """Test: Escribir datos vacíos no crea archivo."""
        # Execute
        result = s3_writer.write_to_bronze(
            data=[],
            client='wongio',
            data_type='orders'
        )
        
        # Verify
        assert result['success'] is True
        assert result['records_written'] == 0
        assert result['s3_path'] is None
        
        # Verificar que no se creó ningún archivo
        response = s3_bucket.list_objects_v2(
            Bucket=BUCKET_NAME,
            Prefix='wongio/orders/'
        )
        
        assert 'Contents' not in response
    
    def test_write_to_bronze_partitioning(self, s3_writer, s3_bucket):
        """Test: Verificar estructura de particionamiento correcta."""
        data = [{'id': '1', 'name': 'Product A'}]
        execution_date = datetime(2024, 3, 5, 14, 30, 0)
        
        # Execute
        result = s3_writer.write_to_bronze(
            data=data,
            client='metro',
            data_type='products',
            execution_date=execution_date
        )
        
        # Verify estructura del path
        s3_path = result['s3_path']
        assert 'metro/products' in s3_path
        assert 'year=2024' in s3_path
        assert 'month=03' in s3_path
        assert 'day=05' in s3_path
        assert '.json' in s3_path
        
        # Verificar que el archivo existe en la ubicación correcta
        response = s3_bucket.list_objects_v2(
            Bucket=BUCKET_NAME,
            Prefix='metro/products/year=2024/month=03/day=05/'
        )
        
        assert 'Contents' in response
        assert len(response['Contents']) == 1
    
    def test_write_multiple_files_same_partition(self, s3_writer, s3_bucket):
        """Test: Escribir múltiples archivos en la misma partición."""
        execution_date = datetime(2024, 1, 15, 10, 0, 0)
        
        # Escribir primer archivo
        result1 = s3_writer.write_to_bronze(
            data=[{'id': '1'}],
            client='wongio',
            data_type='orders',
            execution_date=execution_date
        )
        
        # Escribir segundo archivo (mismo día, diferente timestamp)
        execution_date2 = datetime(2024, 1, 15, 11, 0, 0)
        result2 = s3_writer.write_to_bronze(
            data=[{'id': '2'}],
            client='wongio',
            data_type='orders',
            execution_date=execution_date2
        )
        
        # Verify
        assert result1['success'] is True
        assert result2['success'] is True
        
        # Verificar que hay 2 archivos en la misma partición
        response = s3_bucket.list_objects_v2(
            Bucket=BUCKET_NAME,
            Prefix='wongio/orders/year=2024/month=01/day=15/'
        )
        
        assert 'Contents' in response
        assert len(response['Contents']) == 2
    
    def test_list_files_success(self, s3_writer, s3_bucket):
        """Test: Listar archivos exitosamente."""
        # Escribir algunos archivos primero
        execution_date = datetime(2024, 1, 15, 10, 0, 0)
        
        s3_writer.write_to_bronze(
            data=[{'id': '1'}],
            client='wongio',
            data_type='orders',
            execution_date=execution_date
        )
        
        s3_writer.write_to_bronze(
            data=[{'id': '2'}],
            client='wongio',
            data_type='orders',
            execution_date=datetime(2024, 1, 15, 11, 0, 0)
        )
        
        # Execute
        files = s3_writer.list_files(client='wongio', data_type='orders')
        
        # Verify
        assert len(files) == 2
        assert all('wongio/orders' in f['key'] for f in files)
        assert all('full_path' in f for f in files)
        assert all('size' in f for f in files)
        assert all('last_modified' in f for f in files)
    
    def test_list_files_empty(self, s3_writer):
        """Test: Listar archivos cuando no hay ninguno."""
        # Execute
        files = s3_writer.list_files(client='wongio', data_type='orders')
        
        # Verify
        assert len(files) == 0
    
    def test_list_files_with_max_keys(self, s3_writer, s3_bucket):
        """Test: Listar archivos con límite."""
        # Escribir 5 archivos
        for i in range(5):
            s3_writer.write_to_bronze(
                data=[{'id': str(i)}],
                client='wongio',
                data_type='orders',
                execution_date=datetime(2024, 1, 15, 10 + i, 0, 0)
            )
        
        # Execute con límite de 3
        files = s3_writer.list_files(
            client='wongio',
            data_type='orders',
            max_keys=3
        )
        
        # Verify
        assert len(files) == 3
    
    def test_read_file_success(self, s3_writer, s3_bucket):
        """Test: Leer archivo exitosamente."""
        # Escribir archivo primero
        test_data = [
            {'id': '1', 'status': 'active'},
            {'id': '2', 'status': 'pending'}
        ]
        
        result = s3_writer.write_to_bronze(
            data=test_data,
            client='wongio',
            data_type='orders',
            execution_date=datetime(2024, 1, 15, 10, 0, 0)
        )
        
        # Extraer el key del path
        s3_path = result['s3_path']
        s3_key = s3_path.replace(f's3://{BUCKET_NAME}/', '')
        
        # Execute
        data = s3_writer.read_file(s3_key)
        
        # Verify
        assert len(data) == 2
        assert data[0]['id'] == '1'
        assert data[0]['status'] == 'active'
        assert data[1]['id'] == '2'
        assert data[1]['status'] == 'pending'
    
    def test_read_file_not_exists(self, s3_writer):
        """Test: Leer archivo que no existe."""
        # Execute
        data = s3_writer.read_file('nonexistent/file.json')
        
        # Verify - debe retornar lista vacía
        assert len(data) == 0
    
    def test_write_and_read_workflow(self, s3_writer):
        """Test: Flujo completo de escritura y lectura."""
        # 1. Escribir datos
        original_data = [
            {'id': '123', 'name': 'Product A', 'price': 99.99},
            {'id': '456', 'name': 'Product B', 'price': 149.99}
        ]
        
        write_result = s3_writer.write_to_bronze(
            data=original_data,
            client='metro',
            data_type='products',
            execution_date=datetime(2024, 2, 20, 15, 30, 0)
        )
        
        assert write_result['success'] is True
        
        # 2. Listar archivos
        files = s3_writer.list_files(client='metro', data_type='products')
        assert len(files) == 1
        
        # 3. Leer archivo
        s3_key = files[0]['key']
        read_data = s3_writer.read_file(s3_key)
        
        # 4. Verificar que los datos son idénticos
        assert len(read_data) == len(original_data)
        assert read_data[0]['id'] == original_data[0]['id']
        assert read_data[0]['name'] == original_data[0]['name']
        assert read_data[1]['id'] == original_data[1]['id']
    
    def test_multiple_clients_and_data_types(self, s3_writer, s3_bucket):
        """Test: Múltiples clientes y tipos de datos."""
        # Escribir datos para diferentes clientes y tipos
        s3_writer.write_to_bronze(
            data=[{'id': '1'}],
            client='wongio',
            data_type='orders',
            execution_date=datetime(2024, 1, 15, 10, 0, 0)
        )
        
        s3_writer.write_to_bronze(
            data=[{'id': '2'}],
            client='wongio',
            data_type='products',
            execution_date=datetime(2024, 1, 15, 10, 0, 0)
        )
        
        s3_writer.write_to_bronze(
            data=[{'id': '3'}],
            client='metro',
            data_type='orders',
            execution_date=datetime(2024, 1, 15, 10, 0, 0)
        )
        
        # Verify - cada combinación debe tener su propio archivo
        wongio_orders = s3_writer.list_files('wongio', 'orders')
        wongio_products = s3_writer.list_files('wongio', 'products')
        metro_orders = s3_writer.list_files('metro', 'orders')
        
        assert len(wongio_orders) == 1
        assert len(wongio_products) == 1
        assert len(metro_orders) == 1
        
        # Verificar que están en paths diferentes
        assert 'wongio/orders' in wongio_orders[0]['key']
        assert 'wongio/products' in wongio_products[0]['key']
        assert 'metro/orders' in metro_orders[0]['key']


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
