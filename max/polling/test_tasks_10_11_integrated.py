"""
Integration Tests for Tasks 10 and 11: DAGs and Airflow Task Functions

This module tests the integration between the DAG structure (Task 10) and
the Airflow task functions (Task 11).

Tests verify:
- DAG creation and configuration
- Task dependencies and workflow
- Task function execution in DAG context
- XCom data passing between tasks
- Lock acquisition and release flow
- End-to-end polling workflow
"""

import pytest
import os
import sys
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime

# Add src and dags to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'dags'))

from airflow_tasks import (
    acquire_dynamodb_lock,
    poll_janis_api,
    validate_data,
    enrich_data,
    output_data,
    release_dynamodb_lock,
    AirflowSkipException
)


class TestDAGStructure:
    """Tests for DAG structure and configuration (Task 10)."""
    
    def test_dag_creation(self):
        """Test that DAG can be created with correct configuration."""
        with patch('base_polling_dag.acquire_dynamodb_lock'), \
             patch('base_polling_dag.poll_janis_api'), \
             patch('base_polling_dag.validate_data'), \
             patch('base_polling_dag.enrich_data'), \
             patch('base_polling_dag.output_data'), \
             patch('base_polling_dag.release_dynamodb_lock'):
            
            from base_polling_dag import create_polling_dag
            
            # Create DAG
            dag = create_polling_dag(
                dag_id='test_poll_orders',
                data_type='orders',
                tags=['polling', 'orders', 'test']
            )
            
            # Verify DAG configuration
            assert dag.dag_id == 'test_poll_orders'
            assert dag.schedule is None  # Event-driven (Airflow 2.4+)
            assert dag.catchup is False
            assert dag.max_active_runs == 1
            assert 'polling' in dag.tags
            assert 'orders' in dag.tags
    
    def test_dag_task_structure(self):
        """Test that DAG has all required tasks with correct dependencies."""
        with patch('base_polling_dag.acquire_dynamodb_lock'), \
             patch('base_polling_dag.poll_janis_api'), \
             patch('base_polling_dag.validate_data'), \
             patch('base_polling_dag.enrich_data'), \
             patch('base_polling_dag.output_data'), \
             patch('base_polling_dag.release_dynamodb_lock'):
            
            from base_polling_dag import create_polling_dag
            
            dag = create_polling_dag(
                dag_id='test_poll_products',
                data_type='products',
                tags=['polling', 'products']
            )
            
            # Verify all tasks exist
            task_ids = [task.task_id for task in dag.tasks]
            expected_tasks = [
                'acquire_lock',
                'poll_api',
                'validate_data',
                'enrich_data',
                'output_data',
                'release_lock'
            ]
            
            for expected_task in expected_tasks:
                assert expected_task in task_ids, f"Task {expected_task} not found in DAG"
            
            # Verify task count
            assert len(dag.tasks) == 6
    
    def test_dag_task_dependencies(self):
        """Test that tasks have correct upstream/downstream dependencies."""
        with patch('base_polling_dag.acquire_dynamodb_lock'), \
             patch('base_polling_dag.poll_janis_api'), \
             patch('base_polling_dag.validate_data'), \
             patch('base_polling_dag.enrich_data'), \
             patch('base_polling_dag.output_data'), \
             patch('base_polling_dag.release_dynamodb_lock'):
            
            from base_polling_dag import create_polling_dag
            
            dag = create_polling_dag(
                dag_id='test_poll_stock',
                data_type='stock',
                tags=['polling', 'stock']
            )
            
            # Get tasks
            tasks = {task.task_id: task for task in dag.tasks}
            
            # Verify dependencies: acquire_lock >> poll_api
            assert 'poll_api' in [t.task_id for t in tasks['acquire_lock'].downstream_list]
            assert 'acquire_lock' in [t.task_id for t in tasks['poll_api'].upstream_list]
            
            # Verify dependencies: poll_api >> validate_data
            assert 'validate_data' in [t.task_id for t in tasks['poll_api'].downstream_list]
            assert 'poll_api' in [t.task_id for t in tasks['validate_data'].upstream_list]
            
            # Verify dependencies: validate_data >> enrich_data
            assert 'enrich_data' in [t.task_id for t in tasks['validate_data'].downstream_list]
            assert 'validate_data' in [t.task_id for t in tasks['enrich_data'].upstream_list]
            
            # Verify dependencies: enrich_data >> output_data
            assert 'output_data' in [t.task_id for t in tasks['enrich_data'].downstream_list]
            assert 'enrich_data' in [t.task_id for t in tasks['output_data'].upstream_list]
            
            # Verify dependencies: output_data >> release_lock
            assert 'release_lock' in [t.task_id for t in tasks['output_data'].downstream_list]
            assert 'output_data' in [t.task_id for t in tasks['release_lock'].upstream_list]
    
    def test_release_lock_trigger_rule(self):
        """Test that release_lock task has trigger_rule='all_done'."""
        with patch('base_polling_dag.acquire_dynamodb_lock'), \
             patch('base_polling_dag.poll_janis_api'), \
             patch('base_polling_dag.validate_data'), \
             patch('base_polling_dag.enrich_data'), \
             patch('base_polling_dag.output_data'), \
             patch('base_polling_dag.release_dynamodb_lock'):
            
            from base_polling_dag import create_polling_dag
            
            dag = create_polling_dag(
                dag_id='test_poll_prices',
                data_type='prices',
                tags=['polling', 'prices']
            )
            
            # Get release_lock task
            release_lock_task = None
            for task in dag.tasks:
                if task.task_id == 'release_lock':
                    release_lock_task = task
                    break
            
            assert release_lock_task is not None
            assert release_lock_task.trigger_rule == 'all_done'


class TestEndToEndWorkflow:
    """Tests for end-to-end workflow integration."""
    
    def test_successful_polling_workflow(self):
        """Test complete successful polling workflow from lock to release."""
        # Setup environment
        os.environ['DYNAMODB_TABLE_NAME'] = 'test_table'
        os.environ['JANIS_API_BASE_URL'] = 'https://api.test.com'
        os.environ['JANIS_API_KEY'] = 'test-key'
        
        # Mock context
        context = {
            'run_id': 'test-run-123',
            'task_instance': Mock(),
            'dag_run': Mock()
        }
        
        # Track XCom data
        xcom_data = {}
        
        def xcom_push_side_effect(key, value):
            xcom_data[key] = value
        
        def xcom_pull_side_effect(task_ids, key):
            return xcom_data.get(key)
        
        context['task_instance'].xcom_push = Mock(side_effect=xcom_push_side_effect)
        context['task_instance'].xcom_pull = Mock(side_effect=xcom_pull_side_effect)
        
        # Mock successful task instances for release_lock
        mock_task_instances = []
        for task_id in ['poll_api', 'validate_data', 'enrich_data', 'output_data']:
            mock_ti = Mock()
            mock_ti.state = 'success'
            mock_task_instances.append(mock_ti)
        
        context['dag_run'].get_task_instance = Mock(side_effect=mock_task_instances)
        
        # Mock data
        mock_records = [
            {'id': '1', 'dateModified': '2024-01-15T10:00:00Z', 'status': 'pending'},
            {'id': '2', 'dateModified': '2024-01-15T10:01:00Z', 'status': 'completed'}
        ]
        
        # Mock all components
        with patch('airflow_tasks.StateManager') as mock_state_manager, \
             patch('airflow_tasks.JanisAPIClient') as mock_api_client, \
             patch('airflow_tasks.PaginationHandler') as mock_pagination, \
             patch('airflow_tasks.build_incremental_filter') as mock_filter, \
             patch('airflow_tasks.deduplicate_records') as mock_dedup, \
             patch('airflow_tasks.DataValidator') as mock_validator, \
             patch('airflow_tasks.DataEnricher') as mock_enricher:
            
            # Setup StateManager
            mock_state_instance = Mock()
            mock_state_instance.acquire_lock.return_value = True
            mock_state_instance.release_lock = Mock()
            mock_state_manager.return_value = mock_state_instance
            
            # Setup API client
            mock_api_instance = Mock()
            mock_api_instance.close = Mock()
            mock_api_client.return_value = mock_api_instance
            
            # Setup pagination
            mock_pagination_instance = Mock()
            mock_pagination_instance.fetch_all_pages.return_value = mock_records
            mock_pagination.return_value = mock_pagination_instance
            
            # Setup filter and dedup
            mock_filter.return_value = {}
            mock_dedup.return_value = mock_records
            
            # Setup validator
            mock_validator_instance = Mock()
            mock_validator_instance.validate_batch.return_value = (
                mock_records,
                {
                    'total_received': 2,
                    'valid_count': 2,
                    'invalid_count': 0,
                    'validation_pass_rate': 100.0
                }
            )
            mock_validator.return_value = mock_validator_instance
            
            # Setup enricher
            enriched_records = [
                {'id': '1', 'status': 'pending', '_items': [], '_enrichment_complete': True},
                {'id': '2', 'status': 'completed', '_items': [], '_enrichment_complete': True}
            ]
            mock_enricher_instance = Mock()
            mock_enricher_instance.enrich_orders.return_value = enriched_records
            mock_enricher.return_value = mock_enricher_instance
            
            # Execute workflow
            # Step 1: Acquire lock
            lock_result = acquire_dynamodb_lock(data_type='orders', **context)
            assert lock_result is True
            assert 'execution_id' in xcom_data
            
            # Step 2: Poll API
            poll_result = poll_janis_api(data_type='orders', **context)
            assert poll_result['total_unique'] == 2
            assert 'polling_result' in xcom_data
            
            # Step 3: Validate data
            validate_result = validate_data(data_type='orders', **context)
            assert len(validate_result['valid_records']) == 2
            assert 'validation_result' in xcom_data
            
            # Step 4: Enrich data
            enrich_result = enrich_data(data_type='orders', **context)
            assert len(enrich_result['enriched_records']) == 2
            assert 'enrichment_result' in xcom_data
            
            # Step 5: Output data
            output_result = output_data(data_type='orders', **context)
            assert len(output_result['output_records']) == 2
            assert 'output_result' in xcom_data
            
            # Verify metadata was added
            for record in output_result['output_records']:
                assert '_metadata' in record
                assert record['_metadata']['data_type'] == 'orders'
            
            # Step 6: Release lock
            release_dynamodb_lock(data_type='orders', **context)
            
            # Verify lock was released with success=True
            mock_state_instance.release_lock.assert_called_once()
            call_args = mock_state_instance.release_lock.call_args
            assert call_args[1]['success'] is True
            assert call_args[1]['records_fetched'] == 2
    
    def test_workflow_with_lock_skip(self):
        """Test workflow when lock cannot be acquired (graceful skip)."""
        # Setup environment
        os.environ['DYNAMODB_TABLE_NAME'] = 'test_table'
        
        # Mock context
        context = {
            'run_id': 'test-run-456',
            'task_instance': Mock()
        }
        
        # Mock StateManager with lock already acquired
        with patch('airflow_tasks.StateManager') as mock_state_manager:
            mock_state_instance = Mock()
            mock_state_instance.acquire_lock.return_value = False
            mock_state_manager.return_value = mock_state_instance
            
            # Execute and verify skip
            with pytest.raises(AirflowSkipException):
                acquire_dynamodb_lock(data_type='orders', **context)
    
    def test_workflow_with_validation_failure(self):
        """Test workflow when validation fails and lock is still released."""
        # Setup environment
        os.environ['DYNAMODB_TABLE_NAME'] = 'test_table'
        
        # Mock context
        context = {
            'run_id': 'test-run-789',
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
        
        context['dag_run'].get_task_instance = Mock(side_effect=mock_task_instances)
        context['task_instance'].xcom_pull = Mock(return_value=None)
        
        # Mock StateManager
        with patch('airflow_tasks.StateManager') as mock_state_manager:
            mock_state_instance = Mock()
            mock_state_instance.release_lock = Mock()
            mock_state_manager.return_value = mock_state_instance
            
            # Execute release_lock
            release_dynamodb_lock(data_type='orders', **context)
            
            # Verify lock was released with success=False
            mock_state_instance.release_lock.assert_called_once()
            call_args = mock_state_instance.release_lock.call_args
            assert call_args[1]['success'] is False
            assert call_args[1]['error_message'] is not None


class TestXComDataFlow:
    """Tests for XCom data passing between tasks."""
    
    def test_xcom_data_structure(self):
        """Test that XCom data has correct structure at each stage."""
        # Setup environment
        os.environ['DYNAMODB_TABLE_NAME'] = 'test_table'
        os.environ['JANIS_API_BASE_URL'] = 'https://api.test.com'
        os.environ['JANIS_API_KEY'] = 'test-key'
        
        # Mock context
        context = {
            'run_id': 'test-run-xcom',
            'task_instance': Mock()
        }
        
        xcom_data = {}
        
        def xcom_push_side_effect(key, value):
            xcom_data[key] = value
        
        def xcom_pull_side_effect(task_ids, key):
            return xcom_data.get(key)
        
        context['task_instance'].xcom_push = Mock(side_effect=xcom_push_side_effect)
        context['task_instance'].xcom_pull = Mock(side_effect=xcom_pull_side_effect)
        
        # Mock components
        with patch('airflow_tasks.StateManager'), \
             patch('airflow_tasks.JanisAPIClient') as mock_api_client, \
             patch('airflow_tasks.PaginationHandler') as mock_pagination, \
             patch('airflow_tasks.build_incremental_filter') as mock_filter, \
             patch('airflow_tasks.deduplicate_records') as mock_dedup:
            
            mock_api_instance = Mock()
            mock_api_instance.close = Mock()
            mock_api_client.return_value = mock_api_instance
            
            mock_pagination_instance = Mock()
            mock_pagination_instance.fetch_all_pages.return_value = [
                {'id': '1', 'dateModified': '2024-01-15T10:00:00Z'}
            ]
            mock_pagination.return_value = mock_pagination_instance
            
            mock_filter.return_value = {}
            mock_dedup.return_value = [{'id': '1', 'dateModified': '2024-01-15T10:00:00Z'}]
            
            # Execute poll_api
            poll_janis_api(data_type='orders', **context)
            
            # Verify XCom structure
            assert 'polling_result' in xcom_data
            polling_result = xcom_data['polling_result']
            
            assert 'records' in polling_result
            assert 'total_fetched' in polling_result
            assert 'total_unique' in polling_result
            assert 'last_modified' in polling_result
            
            assert isinstance(polling_result['records'], list)
            assert isinstance(polling_result['total_fetched'], int)
            assert isinstance(polling_result['total_unique'], int)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
