"""
Tests de integración para StateManager usando LocalStack.

Estos tests ejecutan código real contra DynamoDB en LocalStack.
"""

import pytest
import os
import sys
from datetime import datetime
import boto3
from botocore.exceptions import ClientError

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from state_manager import StateManager


# Configuración de LocalStack
LOCALSTACK_ENDPOINT = os.getenv('LOCALSTACK_ENDPOINT', 'http://localhost:4566')
TABLE_NAME = 'test_polling_control'


@pytest.fixture(scope='module')
def dynamodb_table():
    """Crear tabla de DynamoDB en LocalStack para tests."""
    dynamodb = boto3.resource(
        'dynamodb',
        endpoint_url=LOCALSTACK_ENDPOINT,
        region_name='us-east-1',
        aws_access_key_id='test',
        aws_secret_access_key='test'
    )
    
    # Crear tabla
    try:
        table = dynamodb.create_table(
            TableName=TABLE_NAME,
            KeySchema=[
                {'AttributeName': 'data_type', 'KeyType': 'HASH'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'data_type', 'AttributeType': 'S'}
            ],
            BillingMode='PAY_PER_REQUEST'
        )
        
        # Esperar a que la tabla esté activa
        table.wait_until_exists()
        
        yield table
        
        # Cleanup
        table.delete()
        
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceInUseException':
            # Tabla ya existe, usarla
            table = dynamodb.Table(TABLE_NAME)
            yield table
        else:
            raise


@pytest.fixture
def state_manager():
    """Crear StateManager conectado a LocalStack."""
    return StateManager(
        table_name=TABLE_NAME,
        endpoint_url=LOCALSTACK_ENDPOINT
    )


@pytest.fixture(autouse=True)
def cleanup_table(dynamodb_table):
    """Limpiar tabla antes de cada test."""
    # Escanear y eliminar todos los items
    response = dynamodb_table.scan()
    with dynamodb_table.batch_writer() as batch:
        for item in response.get('Items', []):
            batch.delete_item(Key={'data_type': item['data_type']})
    
    yield


class TestStateManagerIntegration:
    """Tests de integración con LocalStack."""
    
    def test_acquire_lock_success(self, state_manager, dynamodb_table):
        """Test: Adquirir lock exitosamente en DynamoDB real."""
        # Execute
        result = state_manager.acquire_lock('orders', 'exec-123')
        
        # Verify
        assert result is True
        
        # Verificar en DynamoDB
        response = dynamodb_table.get_item(Key={'data_type': 'orders'})
        assert 'Item' in response
        assert response['Item']['lock_acquired'] is True
        assert response['Item']['execution_id'] == 'exec-123'
        assert response['Item']['status'] == 'running'
    
    def test_acquire_lock_already_exists(self, state_manager, dynamodb_table):
        """Test: No puede adquirir lock si ya existe."""
        # Adquirir lock primero
        state_manager.acquire_lock('orders', 'exec-123')
        
        # Intentar adquirir nuevamente
        result = state_manager.acquire_lock('orders', 'exec-456')
        
        # Verify
        assert result is False
        
        # Verificar que el lock original se mantiene
        response = dynamodb_table.get_item(Key={'data_type': 'orders'})
        assert response['Item']['execution_id'] == 'exec-123'
    
    def test_release_lock_on_success(self, state_manager, dynamodb_table):
        """Test: Liberar lock después de ejecución exitosa."""
        # Adquirir lock primero
        state_manager.acquire_lock('orders', 'exec-123')
        
        # Liberar lock
        state_manager.release_lock(
            data_type='orders',
            success=True,
            last_modified='2024-01-15T10:00:00Z',
            records_fetched=100
        )
        
        # Verify
        response = dynamodb_table.get_item(Key={'data_type': 'orders'})
        item = response['Item']
        
        assert item['lock_acquired'] is False
        assert item['status'] == 'completed'
        assert item['last_modified_date'] == '2024-01-15T10:00:00Z'
        assert item['records_fetched'] == 100
        assert 'last_successful_execution' in item
        assert 'error_message' not in item
    
    def test_release_lock_on_failure(self, state_manager, dynamodb_table):
        """Test: Liberar lock después de ejecución fallida."""
        # Adquirir lock primero
        state_manager.acquire_lock('orders', 'exec-123')
        
        # Liberar lock con error
        state_manager.release_lock(
            data_type='orders',
            success=False,
            error_message='API timeout'
        )
        
        # Verify
        response = dynamodb_table.get_item(Key={'data_type': 'orders'})
        item = response['Item']
        
        assert item['lock_acquired'] is False
        assert item['status'] == 'failed'
        assert item['error_message'] == 'API timeout'
        # No debe actualizar last_successful_execution en caso de fallo
    
    def test_get_control_item_exists(self, state_manager, dynamodb_table):
        """Test: Obtener item existente."""
        # Crear item primero
        state_manager.acquire_lock('orders', 'exec-123')
        state_manager.release_lock(
            data_type='orders',
            success=True,
            last_modified='2024-01-15T10:00:00Z',
            records_fetched=50
        )
        
        # Obtener item
        item = state_manager.get_control_item('orders')
        
        # Verify
        assert item is not None
        assert item['data_type'] == 'orders'
        assert item['lock_acquired'] is False
        assert item['last_modified_date'] == '2024-01-15T10:00:00Z'
    
    def test_get_control_item_not_exists(self, state_manager):
        """Test: Obtener item que no existe (primera ejecución)."""
        # Execute
        item = state_manager.get_control_item('products')
        
        # Verify
        assert item is None
    
    def test_update_last_modified(self, state_manager, dynamodb_table):
        """Test: Actualizar last_modified_date."""
        # Crear item primero
        state_manager.acquire_lock('orders', 'exec-123')
        state_manager.release_lock('orders', success=True)
        
        # Actualizar last_modified
        state_manager.update_last_modified('orders', '2024-01-16T12:00:00Z')
        
        # Verify
        response = dynamodb_table.get_item(Key={'data_type': 'orders'})
        assert response['Item']['last_modified_date'] == '2024-01-16T12:00:00Z'
    
    def test_get_last_modified_date_exists(self, state_manager):
        """Test: Obtener last_modified_date existente."""
        # Crear item con last_modified
        state_manager.acquire_lock('orders', 'exec-123')
        state_manager.release_lock(
            'orders',
            success=True,
            last_modified='2024-01-15T10:00:00Z'
        )
        
        # Execute
        last_modified = state_manager.get_last_modified_date('orders')
        
        # Verify
        assert last_modified == '2024-01-15T10:00:00Z'
    
    def test_get_last_modified_date_not_exists(self, state_manager):
        """Test: Obtener last_modified_date cuando no existe."""
        # Execute
        last_modified = state_manager.get_last_modified_date('products')
        
        # Verify
        assert last_modified is None
    
    def test_clear_lock(self, state_manager, dynamodb_table):
        """Test: Limpiar lock forzadamente."""
        # Adquirir lock primero
        state_manager.acquire_lock('orders', 'exec-123')
        
        # Limpiar lock
        state_manager.clear_lock('orders')
        
        # Verify
        response = dynamodb_table.get_item(Key={'data_type': 'orders'})
        assert response['Item']['lock_acquired'] is False
    
    def test_full_workflow(self, state_manager, dynamodb_table):
        """Test: Flujo completo de lock/unlock."""
        # 1. Primera ejecución - no hay estado previo
        last_modified = state_manager.get_last_modified_date('orders')
        assert last_modified is None
        
        # 2. Adquirir lock
        acquired = state_manager.acquire_lock('orders', 'exec-001')
        assert acquired is True
        
        # 3. Procesar datos (simulado)
        # ...
        
        # 4. Liberar lock con éxito
        state_manager.release_lock(
            'orders',
            success=True,
            last_modified='2024-01-15T10:00:00Z',
            records_fetched=100
        )
        
        # 5. Segunda ejecución - hay estado previo
        last_modified = state_manager.get_last_modified_date('orders')
        assert last_modified == '2024-01-15T10:00:00Z'
        
        # 6. Adquirir lock nuevamente
        acquired = state_manager.acquire_lock('orders', 'exec-002')
        assert acquired is True
        
        # 7. Liberar lock
        state_manager.release_lock(
            'orders',
            success=True,
            last_modified='2024-01-15T11:00:00Z',
            records_fetched=50
        )
        
        # Verificar estado final
        item = state_manager.get_control_item('orders')
        assert item['lock_acquired'] is False
        assert item['last_modified_date'] == '2024-01-15T11:00:00Z'
        assert item['records_fetched'] == 50


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
