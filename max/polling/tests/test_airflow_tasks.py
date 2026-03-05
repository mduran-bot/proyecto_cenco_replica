"""
Tests for Airflow task functions.

This module tests the task functions implemented for the polling DAGs.
"""

import pytest
import os
import sys
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from airflow_tasks import (
    acquire_dynamodb_lock,
    poll_janis_api_raw,
    write_to_s3_bronze,
    release_dynamodb_lock,
    AirflowSkipException
)


class TestAcquireDynamoDBLock:
    """Tests for acquire_dynamodb_lock function."""
    
    @patch('airflow_tasks.StateManager')
    def test_acquire_lock_success(self, mock_state_manager):
        """Test successful lock acquisition."""
        # Mock context
        context = {
            'run_id': 'test-run-123',
            'task_instance': Mock()
        }
        context['task_instance'].xcom_push = Mock()
        
        # Mock StateManager
        mock_instance = Mock()
        mock_instance.acquire_lock.return_value = True
        mock_state_manager.return_value = mock_instance
        
        # Execute
        result = acquire_dynamodb_lock(
            data_type='orders',
            client='wongio',
            **context
        )
        
        # Verify
        assert result is True
        mock_instance.acquire_lock.assert_called_once_with(
            'orders-wongio',
            'test-run-123'
        )
        
        # Verify XCom pushes
        assert context['task_instance'].xcom_push.call_count == 2
    
    @patch('airflow_tasks.StateManager')
    def test_acquire_lock_already_exists(self, mock_state_manager):
        """Test lock acquisition when lock already exists."""
        # Mock context
        context = {
            'run_id': 'test-run-123',
            'task_instance': Mock()
        }
        
        # Mock StateManager
        mock_instance = Mock()
        mock_instance.acquire_lock.return_value = False
        mock_state_manager.return_value = mock_instance
        
        # Execute and verify exception
        with pytest.raises(AirflowSkipException):
            acquire_dynamodb_lock(
                data_type='orders',
                client='wongio',
                **context
            )


class TestPollJanisAPIRaw:
    """Tests for poll_janis_api_raw function."""
    
    @patch('airflow_tasks.StateManager')
    @patch('airflow_tasks.PaginationHandler')
    @patch('airflow_tasks.JanisAPIClient')
    def test_poll_api_with_records(
        self,
        mock_api_client,
        mock_pagination,
        mock_state_manager
    ):
        """Test polling API with records returned."""
        # Mock context
        context = {
            'run_id': 'test-run-123',
            'task_instance': Mock()
        }
        context['task_instance'].xcom_push = Mock()
        
        # Mock environment
        os.environ['JANIS_API_KEY'] = 'test-key'
        
        # Mock records
        mock_records = [
            {'id': '1', 'dateModified': '2024-01-15T10:00:00Z'},
            {'id': '2', 'dateModified': '2024-01-15T10:01:00Z'}
        ]
        
        # Setup mocks
        mock_state_instance = Mock()
        mock_state_instance.get_last_modified_date.return_value = None
        mock_state_manager.return_value = mock_state_instance
        
        mock_pagination_instance = Mock()
        mock_pagination_instance.fetch_all_pages.return_value = mock_records
        mock_pagination.return_value = mock_pagination_instance
        
        mock_api_instance = Mock()
        mock_api_instance.close = Mock()
        mock_api_client.return_value = mock_api_instance
        
        # Execute
        result = poll_janis_api_raw(
            data_type='orders',
            client='wongio',
            endpoint='order',
            base_url='https://api.test.com',
            **context
        )
        
        # Verify
        assert result['total_fetched'] == 2
        assert result['last_modified_date'] == '2024-01-15T10:01:00Z'
        assert len(result['records']) == 2
        
        # Verify API client was closed
        mock_api_instance.close.assert_called_once()
    
    @patch('airflow_tasks.StateManager')
    @patch('airflow_tasks.PaginationHandler')
    @patch('airflow_tasks.JanisAPIClient')
    def test_poll_api_with_incremental_filter(
        self,
        mock_api_client,
        mock_pagination,
        mock_state_manager
    ):
        """Test polling API with incremental filter."""
        # Mock context
        context = {
            'run_id': 'test-run-123',
            'task_instance': Mock()
        }
        context['task_instance'].xcom_push = Mock()
        
        # Mock environment
        os.environ['JANIS_API_KEY'] = 'test-key'
        
        # Mock last_modified_date exists
        mock_state_instance = Mock()
        mock_state_instance.get_last_modified_date.return_value = '2024-01-14T00:00:00Z'
        mock_state_manager.return_value = mock_state_instance
        
        mock_pagination_instance = Mock()
        mock_pagination_instance.fetch_all_pages.return_value = []
        mock_pagination.return_value = mock_pagination_instance
        
        mock_api_instance = Mock()
        mock_api_instance.close = Mock()
        mock_api_client.return_value = mock_api_instance
        
        # Execute
        result = poll_janis_api_raw(
            data_type='orders',
            client='wongio',
            endpoint='order',
            base_url='https://api.test.com',
            **context
        )
        
        # Verify incremental filter was used
        mock_pagination_instance.fetch_all_pages.assert_called_once()
        call_args = mock_pagination_instance.fetch_all_pages.call_args
        assert call_args[1]['filters']['modified_since'] == '2024-01-14T00:00:00Z'


class TestWriteToS3Bronze:
    """Tests for write_to_s3_bronze function."""
    
    @patch('airflow_tasks.S3Writer')
    def test_write_to_s3_success(self, mock_s3_writer):
        """Test successful write to S3."""
        # Mock context
        context = {
            'task_instance': Mock()
        }
        
        # Mock polling result
        polling_result = {
            'records': [
                {'id': '1', 'status': 'active'},
                {'id': '2', 'status': 'pending'}
            ],
            'total_fetched': 2
        }
        context['task_instance'].xcom_pull = Mock(return_value=polling_result)
        context['task_instance'].xcom_push = Mock()
        
        # Mock environment
        os.environ['S3_BRONZE_BUCKET'] = 'test-bronze-bucket'
        
        # Mock S3Writer
        mock_writer_instance = Mock()
        mock_writer_instance.write_to_bronze.return_value = {
            'success': True,
            'records_written': 2,
            's3_path': 's3://test-bronze-bucket/wongio/orders/year=2024/...',
            'file_size_mb': 0.05
        }
        mock_s3_writer.return_value = mock_writer_instance
        
        # Execute
        result = write_to_s3_bronze(
            data_type='orders',
            client='wongio',
            **context
        )
        
        # Verify
        assert result['success'] is True
        assert result['records_written'] == 2
        mock_writer_instance.write_to_bronze.assert_called_once()
    
    @patch('airflow_tasks.S3Writer')
    def test_write_to_s3_no_records(self, mock_s3_writer):
        """Test write to S3 with no records."""
        # Mock context
        context = {
            'task_instance': Mock()
        }
        
        # Mock empty polling result
        polling_result = {
            'records': [],
            'total_fetched': 0
        }
        context['task_instance'].xcom_pull = Mock(return_value=polling_result)
        
        # Mock environment
        os.environ['S3_BRONZE_BUCKET'] = 'test-bronze-bucket'
        
        # Execute
        result = write_to_s3_bronze(
            data_type='orders',
            client='wongio',
            **context
        )
        
        # Verify
        assert result['success'] is True
        assert result['records_written'] == 0
        assert 'No records to write' in result['message']


class TestReleaseDynamoDBLock:
    """Tests for release_dynamodb_lock function."""
    
    @patch('airflow_tasks.StateManager')
    def test_release_lock_on_success(self, mock_state_manager):
        """Test lock release after successful execution."""
        # Mock context
        context = {
            'task_instance': Mock(),
            'dag_run': Mock()
        }
        
        # Mock successful task instances
        mock_poll_ti = Mock()
        mock_poll_ti.state = 'success'
        
        mock_write_ti = Mock()
        mock_write_ti.state = 'success'
        
        context['dag_run'].get_task_instance = Mock(
            side_effect=[mock_poll_ti, mock_write_ti]
        )
        
        # Mock polling result
        polling_result = {
            'total_fetched': 10,
            'last_modified_date': '2024-01-15T10:00:00Z'
        }
        context['task_instance'].xcom_pull = Mock(return_value=polling_result)
        
        # Mock StateManager
        mock_instance = Mock()
        mock_instance.release_lock = Mock()
        mock_state_manager.return_value = mock_instance
        
        # Execute
        release_dynamodb_lock(
            data_type='orders',
            client='wongio',
            **context
        )
        
        # Verify
        mock_instance.release_lock.assert_called_once()
        call_args = mock_instance.release_lock.call_args
        assert call_args[1]['data_type'] == 'orders-wongio'
        assert call_args[1]['success'] is True
        assert call_args[1]['last_modified'] == '2024-01-15T10:00:00Z'
        assert call_args[1]['records_fetched'] == 10
    
    @patch('airflow_tasks.StateManager')
    def test_release_lock_on_failure(self, mock_state_manager):
        """Test lock release after failed execution."""
        # Mock context
        context = {
            'task_instance': Mock(),
            'dag_run': Mock()
        }
        
        # Mock failed task instances
        mock_poll_ti = Mock()
        mock_poll_ti.state = 'failed'
        
        mock_write_ti = Mock()
        mock_write_ti.state = 'success'
        
        context['dag_run'].get_task_instance = Mock(
            side_effect=[mock_poll_ti, mock_write_ti]
        )
        
        context['task_instance'].xcom_pull = Mock(return_value=None)
        
        # Mock StateManager
        mock_instance = Mock()
        mock_instance.release_lock = Mock()
        mock_state_manager.return_value = mock_instance
        
        # Execute
        release_dynamodb_lock(
            data_type='orders',
            client='wongio',
            **context
        )
        
        # Verify
        mock_instance.release_lock.assert_called_once()
        call_args = mock_instance.release_lock.call_args
        assert call_args[1]['data_type'] == 'orders-wongio'
        assert call_args[1]['success'] is False
        assert call_args[1]['error_message'] is not None


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
