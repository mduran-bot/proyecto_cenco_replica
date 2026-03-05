"""
Tests unitarios para StateManager.

Valida la gestión de estado en DynamoDB con distributed locking.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from botocore.exceptions import ClientError
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from state_manager import StateManager


class TestStateManagerInitialization:
    """Tests de inicialización del StateManager."""
    
    @patch('state_manager.boto3')
    def test_initialization_with_defaults(self, mock_boto3):
        """Test: Inicialización con valores por defecto."""
        mock_resource = Mock()
        mock_table = Mock()
        mock_resource.Table.return_value = mock_table
        mock_boto3.resource.return_value = mock_resource
        
        manager = StateManager()
        
        assert manager.table_name == "polling_control"
        mock_boto3.resource.assert_called_once()
        mock_resource.Table.assert_called_once_with("polling_control")
    
    @patch('state_manager.boto3')
    def test_initialization_with_custom_table(self, mock_boto3):
        """Test: Inicialización con nombre de tabla personalizado."""
        mock_resource = Mock()
        mock_table = Mock()
        mock_resource.Table.return_value = mock_table
        mock_boto3.resource.return_value = mock_resource
        
        manager = StateManager(table_name="custom_table")
        
        assert manager.table_name == "custom_table"
        mock_resource.Table.assert_called_once_with("custom_table")
    
    @patch('state_manager.boto3')
    def test_initialization_with_endpoint_url(self, mock_boto3):
        """Test: Inicialización con endpoint URL para LocalStack."""
        mock_resource = Mock()
        mock_table = Mock()
        mock_resource.Table.return_value = mock_table
        mock_boto3.resource.return_value = mock_resource
        
        manager = StateManager(endpoint_url="http://localhost:4566")
        
        # Verificar que se pasó el endpoint_url
        call_kwargs = mock_boto3.resource.call_args[1]
        assert call_kwargs['endpoint_url'] == "http://localhost:4566"


class TestAcquireLock:
    """Tests del método acquire_lock."""
    
    @patch('state_manager.boto3')
    @patch('state_manager.datetime')
    def test_acquire_lock_success(self, mock_datetime, mock_boto3):
        """Test: Adquirir lock exitosamente."""
        # Setup mocks
        mock_now = datetime(2024, 1, 15, 10, 0, 0)
        mock_datetime.now.return_value = mock_now
        
        mock_resource = Mock()
        mock_table = Mock()
        mock_table.update_item = Mock()
        mock_resource.Table.return_value = mock_table
        mock_boto3.resource.return_value = mock_resource
        
        manager = StateManager()
        
        # Execute
        result = manager.acquire_lock('orders', 'exec-123')
        
        # Verify
        assert result is True
        mock_table.update_item.assert_called_once()
        
        # Verificar parámetros del update_item
        call_kwargs = mock_table.update_item.call_args[1]
        assert call_kwargs['Key'] == {'data_type': 'orders'}
        assert ':true' in str(call_kwargs['ExpressionAttributeValues'])
        assert 'exec-123' in str(call_kwargs['ExpressionAttributeValues'])
    
    @patch('state_manager.boto3')
    def test_acquire_lock_already_exists(self, mock_boto3):
        """Test: Lock ya existe, debe retornar False."""
        # Setup mocks
        mock_resource = Mock()
        mock_table = Mock()
        
        # Simular ConditionalCheckFailedException
        error_response = {'Error': {'Code': 'ConditionalCheckFailedException'}}
        mock_table.update_item.side_effect = ClientError(error_response, 'UpdateItem')
        
        mock_resource.Table.return_value = mock_table
        mock_boto3.resource.return_value = mock_resource
        
        manager = StateManager()
        
        # Execute
        result = manager.acquire_lock('orders', 'exec-123')
        
        # Verify
        assert result is False
    
    @patch('state_manager.boto3')
    def test_acquire_lock_dynamodb_error(self, mock_boto3):
        """Test: Error de DynamoDB debe propagarse."""
        # Setup mocks
        mock_resource = Mock()
        mock_table = Mock()
        
        # Simular otro tipo de error
        error_response = {'Error': {'Code': 'InternalServerError'}}
        mock_table.update_item.side_effect = ClientError(error_response, 'UpdateItem')
        
        mock_resource.Table.return_value = mock_table
        mock_boto3.resource.return_value = mock_resource
        
        manager = StateManager()
        
        # Execute & Verify
        with pytest.raises(ClientError):
            manager.acquire_lock('orders', 'exec-123')


class TestReleaseLock:
    """Tests del método release_lock."""
    
    @patch('state_manager.boto3')
    @patch('state_manager.datetime')
    def test_release_lock_on_success(self, mock_datetime, mock_boto3):
        """Test: Liberar lock después de ejecución exitosa."""
        # Setup mocks
        mock_now = datetime(2024, 1, 15, 10, 0, 0)
        mock_datetime.utcnow.return_value = mock_now
        
        mock_resource = Mock()
        mock_table = Mock()
        mock_table.update_item = Mock()
        mock_resource.Table.return_value = mock_table
        mock_boto3.resource.return_value = mock_resource
        
        manager = StateManager()
        
        # Execute
        manager.release_lock(
            data_type='orders',
            success=True,
            last_modified='2024-01-15T09:00:00Z',
            records_fetched=100
        )
        
        # Verify
        mock_table.update_item.assert_called_once()
        
        # Verificar parámetros
        call_kwargs = mock_table.update_item.call_args[1]
        assert call_kwargs['Key'] == {'data_type': 'orders'}
        assert 'last_successful_execution' in call_kwargs['UpdateExpression']
        assert 'last_modified_date' in call_kwargs['UpdateExpression']
        assert 'records_fetched' in call_kwargs['UpdateExpression']
    
    @patch('state_manager.boto3')
    def test_release_lock_on_failure(self, mock_boto3):
        """Test: Liberar lock después de ejecución fallida."""
        # Setup mocks
        mock_resource = Mock()
        mock_table = Mock()
        mock_table.update_item = Mock()
        mock_resource.Table.return_value = mock_table
        mock_boto3.resource.return_value = mock_resource
        
        manager = StateManager()
        
        # Execute
        manager.release_lock(
            data_type='orders',
            success=False,
            error_message='API timeout'
        )
        
        # Verify
        mock_table.update_item.assert_called_once()
        
        # Verificar que se guardó el error
        call_kwargs = mock_table.update_item.call_args[1]
        assert 'error_message' in call_kwargs['UpdateExpression']
        assert ':error' in call_kwargs['ExpressionAttributeValues']
    
    @patch('state_manager.boto3')
    def test_release_lock_without_last_modified(self, mock_boto3):
        """Test: Liberar lock sin last_modified."""
        # Setup mocks
        mock_resource = Mock()
        mock_table = Mock()
        mock_table.update_item = Mock()
        mock_resource.Table.return_value = mock_table
        mock_boto3.resource.return_value = mock_resource
        
        manager = StateManager()
        
        # Execute
        manager.release_lock(
            data_type='orders',
            success=True,
            records_fetched=50
        )
        
        # Verify
        mock_table.update_item.assert_called_once()
        
        # Verificar que NO se incluyó last_modified_date
        call_kwargs = mock_table.update_item.call_args[1]
        assert 'last_modified_date' not in call_kwargs['UpdateExpression']


class TestGetControlItem:
    """Tests del método get_control_item."""
    
    @patch('state_manager.boto3')
    def test_get_control_item_exists(self, mock_boto3):
        """Test: Obtener item existente."""
        # Setup mocks
        mock_resource = Mock()
        mock_table = Mock()
        
        mock_item = {
            'data_type': 'orders',
            'lock_acquired': False,
            'last_successful_execution': '2024-01-15T10:00:00Z',
            'last_modified_date': '2024-01-15T09:00:00Z'
        }
        mock_table.get_item.return_value = {'Item': mock_item}
        
        mock_resource.Table.return_value = mock_table
        mock_boto3.resource.return_value = mock_resource
        
        manager = StateManager()
        
        # Execute
        result = manager.get_control_item('orders')
        
        # Verify
        assert result == mock_item
        mock_table.get_item.assert_called_once_with(Key={'data_type': 'orders'})
    
    @patch('state_manager.boto3')
    def test_get_control_item_not_exists(self, mock_boto3):
        """Test: Item no existe (primera ejecución)."""
        # Setup mocks
        mock_resource = Mock()
        mock_table = Mock()
        mock_table.get_item.return_value = {}  # Sin 'Item'
        
        mock_resource.Table.return_value = mock_table
        mock_boto3.resource.return_value = mock_resource
        
        manager = StateManager()
        
        # Execute
        result = manager.get_control_item('orders')
        
        # Verify
        assert result is None
    
    @patch('state_manager.boto3')
    def test_get_control_item_error(self, mock_boto3):
        """Test: Error al obtener item."""
        # Setup mocks
        mock_resource = Mock()
        mock_table = Mock()
        
        error_response = {'Error': {'Code': 'InternalServerError'}}
        mock_table.get_item.side_effect = ClientError(error_response, 'GetItem')
        
        mock_resource.Table.return_value = mock_table
        mock_boto3.resource.return_value = mock_resource
        
        manager = StateManager()
        
        # Execute & Verify
        with pytest.raises(ClientError):
            manager.get_control_item('orders')


class TestUpdateLastModified:
    """Tests del método update_last_modified."""
    
    @patch('state_manager.boto3')
    def test_update_last_modified_success(self, mock_boto3):
        """Test: Actualizar last_modified exitosamente."""
        # Setup mocks
        mock_resource = Mock()
        mock_table = Mock()
        mock_table.update_item = Mock()
        mock_resource.Table.return_value = mock_table
        mock_boto3.resource.return_value = mock_resource
        
        manager = StateManager()
        
        # Execute
        manager.update_last_modified('orders', '2024-01-15T10:00:00Z')
        
        # Verify
        mock_table.update_item.assert_called_once()
        
        call_kwargs = mock_table.update_item.call_args[1]
        assert call_kwargs['Key'] == {'data_type': 'orders'}
        assert 'last_modified_date' in call_kwargs['UpdateExpression']
        assert call_kwargs['ExpressionAttributeValues'][':last_mod'] == '2024-01-15T10:00:00Z'


class TestGetLastModifiedDate:
    """Tests del método get_last_modified_date."""
    
    @patch('state_manager.boto3')
    def test_get_last_modified_date_exists(self, mock_boto3):
        """Test: Obtener last_modified_date existente."""
        # Setup mocks
        mock_resource = Mock()
        mock_table = Mock()
        
        mock_item = {
            'data_type': 'orders',
            'last_modified_date': '2024-01-15T09:00:00Z'
        }
        mock_table.get_item.return_value = {'Item': mock_item}
        
        mock_resource.Table.return_value = mock_table
        mock_boto3.resource.return_value = mock_resource
        
        manager = StateManager()
        
        # Execute
        result = manager.get_last_modified_date('orders')
        
        # Verify
        assert result == '2024-01-15T09:00:00Z'
    
    @patch('state_manager.boto3')
    def test_get_last_modified_date_not_set(self, mock_boto3):
        """Test: last_modified_date no está configurado."""
        # Setup mocks
        mock_resource = Mock()
        mock_table = Mock()
        
        mock_item = {'data_type': 'orders'}  # Sin last_modified_date
        mock_table.get_item.return_value = {'Item': mock_item}
        
        mock_resource.Table.return_value = mock_table
        mock_boto3.resource.return_value = mock_resource
        
        manager = StateManager()
        
        # Execute
        result = manager.get_last_modified_date('orders')
        
        # Verify
        assert result is None
    
    @patch('state_manager.boto3')
    def test_get_last_modified_date_item_not_exists(self, mock_boto3):
        """Test: Item no existe (primera ejecución)."""
        # Setup mocks
        mock_resource = Mock()
        mock_table = Mock()
        mock_table.get_item.return_value = {}
        
        mock_resource.Table.return_value = mock_table
        mock_boto3.resource.return_value = mock_resource
        
        manager = StateManager()
        
        # Execute
        result = manager.get_last_modified_date('orders')
        
        # Verify
        assert result is None


class TestClearLock:
    """Tests del método clear_lock."""
    
    @patch('state_manager.boto3')
    def test_clear_lock_success(self, mock_boto3):
        """Test: Limpiar lock exitosamente."""
        # Setup mocks
        mock_resource = Mock()
        mock_table = Mock()
        mock_table.update_item = Mock()
        mock_resource.Table.return_value = mock_table
        mock_boto3.resource.return_value = mock_resource
        
        manager = StateManager()
        
        # Execute
        manager.clear_lock('orders')
        
        # Verify
        mock_table.update_item.assert_called_once()
        
        call_kwargs = mock_table.update_item.call_args[1]
        assert call_kwargs['Key'] == {'data_type': 'orders'}
        assert 'lock_acquired' in call_kwargs['UpdateExpression']


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
