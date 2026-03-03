"""
Tests for Airflow task functions.

This module tests the task functions implemented for the polling DAGs.
"""

import pytest
import os
import sys
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from airflow_tasks import (
    acquire_dynamodb_lock,
    poll_janis_api,
    validate_data,
    enrich_data,
    output_data,
    release_dynamodb_lock,
    AirflowSkipException
)


class TestAcquireDynamoDBLock:
    """Tests for acquire_dynamodb_lock function."""
    
    def test_acquire_lock_success(self):
        """Test successful lock acquisition."""
        # Mock context
        context = {
            'run_id': 'test-run-123',
            'task_instance': Mock()
        }
        context['task_instance'].xcom_push = Mock()
        
        # Mock environment
        os.environ['DYNAMODB_TABLE_NAME'] = 'test_table'
        
        # Mock StateManager
        with patch('airflow_tasks.StateManager') as mock_state_manager:
            mock_instance = Mock()
            mock_instance.acquire_lock.return_value = True
            mock_state_manager.return_value = mock_instance
            
            # Execute
            result = acquire_dynamodb_lock(data_type='orders', **context)
            
            # Verify
            assert result is True
            mock_instance.acquire_lock.assert_called_once_with('orders', 'test-run-123')
            context['task_instance'].xcom_push.assert_called_once_with(
                key='execution_id',
                value='test-run-123'
            )
    
    def test_acquire_lock_already_exists(self):
        """Test lock acquisition when lock already exists."""
        # Mock context
        context = {
            'run_id': 'test-run-123',
            'task_instance': Mock()
        }
        
        # Mock environment
        os.environ['DYNAMODB_TABLE_NAME'] = 'test_table'
        
        # Mock StateManager
        with patch('airflow_tasks.StateManager') as mock_state_manager:
            mock_instance = Mock()
            mock_instance.acquire_lock.return_value = False
            mock_state_manager.return_value = mock_instance
            
            # Execute and verify exception
            with pytest.raises(AirflowSkipException):
                acquire_dynamodb_lock(data_type='orders', **context)


class TestPollJanisAPI:
    """Tests for poll_janis_api function."""
    
    def test_poll_api_with_records(self):
        """Test polling API with records returned."""
        # Mock context
        context = {
            'run_id': 'test-run-123',
            'task_instance': Mock()
        }
        context['task_instance'].xcom_push = Mock()
        
        # Mock environment
        os.environ['JANIS_API_BASE_URL'] = 'https://api.test.com'
        os.environ['JANIS_API_KEY'] = 'test-key'
        os.environ['DYNAMODB_TABLE_NAME'] = 'test_table'
        
        # Mock records
        mock_records = [
            {'id': '1', 'dateModified': '2024-01-15T10:00:00Z'},
            {'id': '2', 'dateModified': '2024-01-15T10:01:00Z'}
        ]
        
        # Mock components
        with patch('airflow_tasks.StateManager') as mock_state_manager, \
             patch('airflow_tasks.JanisAPIClient') as mock_api_client, \
             patch('airflow_tasks.PaginationHandler') as mock_pagination, \
             patch('airflow_tasks.build_incremental_filter') as mock_filter, \
             patch('airflow_tasks.deduplicate_records') as mock_dedup:
            
            # Setup mocks
            mock_filter.return_value = {}
            mock_pagination_instance = Mock()
            mock_pagination_instance.fetch_all_pages.return_value = mock_records
            mock_pagination.return_value = mock_pagination_instance
            mock_dedup.return_value = mock_records
            
            mock_api_instance = Mock()
            mock_api_instance.close = Mock()
            mock_api_client.return_value = mock_api_instance
            
            # Execute
            result = poll_janis_api(data_type='orders', **context)
            
            # Verify
            assert result['total_fetched'] == 2
            assert result['total_unique'] == 2
            assert result['last_modified'] == '2024-01-15T10:01:00Z'
            assert len(result['records']) == 2
            
            # Verify API client was closed
            mock_api_instance.close.assert_called_once()


class TestValidateData:
    """Tests for validate_data function."""
    
    def test_validate_data_success(self):
        """Test data validation with valid records."""
        # Mock context
        context = {
            'task_instance': Mock()
        }
        
        # Mock polling result
        polling_result = {
            'records': [
                {'id': '1', 'name': 'Test'},
                {'id': '2', 'name': 'Test2'}
            ]
        }
        context['task_instance'].xcom_pull = Mock(return_value=polling_result)
        context['task_instance'].xcom_push = Mock()
        
        # Mock DataValidator
        with patch('airflow_tasks.DataValidator') as mock_validator:
            mock_instance = Mock()
            mock_instance.validate_batch.return_value = (
                polling_result['records'],
                {
                    'total_received': 2,
                    'valid_count': 2,
                    'invalid_count': 0,
                    'validation_pass_rate': 100.0
                }
            )
            mock_validator.return_value = mock_instance
            
            # Execute
            result = validate_data(data_type='orders', **context)
            
            # Verify
            assert len(result['valid_records']) == 2
            assert result['metrics']['valid_count'] == 2
            assert result['metrics']['validation_pass_rate'] == 100.0


class TestEnrichData:
    """Tests for enrich_data function."""
    
    def test_enrich_orders(self):
        """Test enriching orders with items."""
        # Mock context
        context = {
            'task_instance': Mock()
        }
        
        # Mock validation result
        validation_result = {
            'valid_records': [
                {'id': '1', 'status': 'pending'},
                {'id': '2', 'status': 'completed'}
            ]
        }
        context['task_instance'].xcom_pull = Mock(return_value=validation_result)
        context['task_instance'].xcom_push = Mock()
        
        # Mock environment
        os.environ['JANIS_API_BASE_URL'] = 'https://api.test.com'
        os.environ['JANIS_API_KEY'] = 'test-key'
        
        # Mock enriched records
        enriched_records = [
            {'id': '1', 'status': 'pending', '_items': [], '_enrichment_complete': True},
            {'id': '2', 'status': 'completed', '_items': [], '_enrichment_complete': True}
        ]
        
        # Mock components
        with patch('airflow_tasks.JanisAPIClient') as mock_api_client, \
             patch('airflow_tasks.DataEnricher') as mock_enricher:
            
            mock_api_instance = Mock()
            mock_api_instance.close = Mock()
            mock_api_client.return_value = mock_api_instance
            
            mock_enricher_instance = Mock()
            mock_enricher_instance.enrich_orders.return_value = enriched_records
            mock_enricher.return_value = mock_enricher_instance
            
            # Execute
            result = enrich_data(data_type='orders', **context)
            
            # Verify
            assert len(result['enriched_records']) == 2
            assert result['enrichment_stats']['total_records'] == 2
            assert result['enrichment_stats']['enriched_count'] == 2
            
            # Verify API client was closed
            mock_api_instance.close.assert_called_once()
    
    def test_enrich_non_enrichable_type(self):
        """Test enrichment for data types that don't need enrichment."""
        # Mock context
        context = {
            'task_instance': Mock()
        }
        
        # Mock validation result
        validation_result = {
            'valid_records': [
                {'id': '1', 'quantity': 100}
            ]
        }
        context['task_instance'].xcom_pull = Mock(return_value=validation_result)
        context['task_instance'].xcom_push = Mock()
        
        # Execute
        result = enrich_data(data_type='stock', **context)
        
        # Verify - should pass through without enrichment
        assert len(result['enriched_records']) == 1
        assert result['enrichment_stats']['enrichment_skipped'] is True


class TestOutputData:
    """Tests for output_data function."""
    
    def test_output_data_adds_metadata(self):
        """Test that output_data adds metadata to records."""
        # Mock context
        context = {
            'run_id': 'test-run-123',
            'task_instance': Mock()
        }
        
        # Mock enrichment result
        enrichment_result = {
            'enriched_records': [
                {'id': '1', 'status': 'pending'},
                {'id': '2', 'status': 'completed'}
            ],
            'enrichment_stats': {
                'total_records': 2,
                'enriched_count': 2,
                'failed_count': 0
            }
        }
        
        # Setup xcom_pull to return different values for different tasks
        def xcom_pull_side_effect(task_ids, key):
            if task_ids == 'enrich_data':
                return enrichment_result
            elif task_ids == 'acquire_lock':
                return 'test-run-123'
            elif task_ids == 'validate_data':
                return {'metrics': {}}
            elif task_ids == 'poll_api':
                return {'last_modified': '2024-01-15T10:00:00Z'}
            return None
        
        context['task_instance'].xcom_pull = Mock(side_effect=xcom_pull_side_effect)
        context['task_instance'].xcom_push = Mock()
        
        # Execute
        result = output_data(data_type='orders', **context)
        
        # Verify
        assert len(result['output_records']) == 2
        assert result['summary']['total_records'] == 2
        assert result['summary']['execution_id'] == 'test-run-123'
        
        # Verify metadata was added to each record
        for record in result['output_records']:
            assert '_metadata' in record
            assert record['_metadata']['execution_id'] == 'test-run-123'
            assert record['_metadata']['data_type'] == 'orders'
            assert 'poll_timestamp' in record['_metadata']


class TestReleaseDynamoDBLock:
    """Tests for release_dynamodb_lock function."""
    
    def test_release_lock_on_success(self):
        """Test lock release after successful execution."""
        # Mock context
        context = {
            'task_instance': Mock(),
            'dag_run': Mock()
        }
        
        # Mock successful task instances
        mock_task_instances = []
        for task_id in ['poll_api', 'validate_data', 'enrich_data', 'output_data']:
            mock_ti = Mock()
            mock_ti.state = 'success'
            mock_task_instances.append(mock_ti)
        
        context['dag_run'].get_task_instance = Mock(
            side_effect=mock_task_instances
        )
        
        # Mock output result
        output_result = {
            'summary': {
                'last_modified': '2024-01-15T10:00:00Z',
                'total_records': 10
            }
        }
        context['task_instance'].xcom_pull = Mock(return_value=output_result)
        
        # Mock environment
        os.environ['DYNAMODB_TABLE_NAME'] = 'test_table'
        
        # Mock StateManager
        with patch('airflow_tasks.StateManager') as mock_state_manager:
            mock_instance = Mock()
            mock_instance.release_lock = Mock()
            mock_state_manager.return_value = mock_instance
            
            # Execute
            release_dynamodb_lock(data_type='orders', **context)
            
            # Verify
            mock_instance.release_lock.assert_called_once()
            call_args = mock_instance.release_lock.call_args
            assert call_args[1]['data_type'] == 'orders'
            assert call_args[1]['success'] is True
            assert call_args[1]['last_modified'] == '2024-01-15T10:00:00Z'
            assert call_args[1]['records_fetched'] == 10
    
    def test_release_lock_on_failure(self):
        """Test lock release after failed execution."""
        # Mock context
        context = {
            'task_instance': Mock(),
            'dag_run': Mock()
        }
        
        # Mock failed task instances
        mock_task_instances = []
        for i, task_id in enumerate(['poll_api', 'validate_data', 'enrich_data', 'output_data']):
            mock_ti = Mock()
            # Make validate_data fail
            mock_ti.state = 'failed' if task_id == 'validate_data' else 'success'
            mock_task_instances.append(mock_ti)
        
        context['dag_run'].get_task_instance = Mock(
            side_effect=mock_task_instances
        )
        
        context['task_instance'].xcom_pull = Mock(return_value=None)
        
        # Mock environment
        os.environ['DYNAMODB_TABLE_NAME'] = 'test_table'
        
        # Mock StateManager
        with patch('airflow_tasks.StateManager') as mock_state_manager:
            mock_instance = Mock()
            mock_instance.release_lock = Mock()
            mock_state_manager.return_value = mock_instance
            
            # Execute
            release_dynamodb_lock(data_type='orders', **context)
            
            # Verify
            mock_instance.release_lock.assert_called_once()
            call_args = mock_instance.release_lock.call_args
            assert call_args[1]['data_type'] == 'orders'
            assert call_args[1]['success'] is False
            assert call_args[1]['error_message'] is not None


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
