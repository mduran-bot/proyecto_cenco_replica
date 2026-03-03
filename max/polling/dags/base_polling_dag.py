"""
Base Polling DAG Factory.

This module provides a factory function to create reusable polling DAGs
for different data types (orders, products, stock, prices, stores).

Each DAG follows the same workflow:
1. Acquire lock in DynamoDB
2. Poll Janis API with incremental filters
3. Validate data against JSON schemas
4. Enrich data with related entities
5. Output data with metadata
6. Release lock (always executes via trigger_rule='all_done')
"""

import sys
import os
from datetime import datetime, timedelta
from airflow import DAG
from airflow.providers.standard.operators.python import PythonOperator
from typing import Dict, Any

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Import task functions
from airflow_tasks import (
    acquire_dynamodb_lock,
    poll_janis_api,
    validate_data,
    enrich_data,
    output_data,
    write_to_s3_bronze,
    release_dynamodb_lock
)


def create_polling_dag(
    dag_id: str,
    data_type: str,
    clients: list,
    endpoint: str,
    base_url: str,
    tags: list,
    default_args: Dict[str, Any] = None
) -> DAG:
    """
    Factory function to create a polling DAG for a specific data type with multi-tenant support.
    
    Args:
        dag_id: Unique identifier for the DAG (e.g., 'poll_orders')
        data_type: Type of data to poll (e.g., 'orders', 'products')
        clients: List of client identifiers (e.g., ['metro', 'wongio'])
        endpoint: API endpoint to poll (e.g., '/order')
        base_url: Base URL for the API (e.g., 'https://oms.janis.in/api')
        tags: List of tags for the DAG (e.g., ['polling', 'orders'])
        default_args: Optional default arguments for the DAG
    
    Returns:
        Configured Airflow DAG instance
    
    Requirements:
        - 2.3: schedule=None for event-driven execution
        - 3.2: Acquire lock before polling
        - 3.3: Skip execution if lock cannot be acquired
        - 3.5: Update timestamp on successful completion
        - 3.6: Release lock after completion
    """
    # Default arguments for all tasks
    if default_args is None:
        default_args = {
            'owner': 'data-engineering',
            'depends_on_past': False,
            'email_on_failure': True,
            'email_on_retry': False,
            'retries': 0,  # No retries at DAG level (handled by components)
            'retry_delay': timedelta(minutes=5),
        }
    
    # Create DAG with event-driven scheduling
    dag = DAG(
        dag_id=dag_id,
        default_args=default_args,
        description=f'Poll {data_type} from Janis API with incremental sync',
        schedule=None,  # Event-driven via EventBridge (Airflow 2.4+)
        start_date=datetime(2024, 1, 1),
        catchup=False,
        tags=tags,
        max_active_runs=1,  # Prevent concurrent executions
    )
    
    with dag:
        # Create tasks dynamically for each client
        for client in clients:
            # Task 1: Acquire lock in DynamoDB
            # Prevents concurrent executions for the same data_type-client combination
            acquire_lock_task = PythonOperator(
                task_id=f'acquire_lock_{client}',
                python_callable=acquire_dynamodb_lock,
                op_kwargs={
                    'data_type': data_type,
                    'client': client
                },
            )
            
            # Task 2: Poll Janis API
            # Fetches data with incremental filters and pagination
            poll_api_task = PythonOperator(
                task_id=f'poll_api_{client}',
                python_callable=poll_janis_api,
                op_kwargs={
                    'data_type': data_type,
                    'client': client,
                    'endpoint': endpoint,
                    'base_url': base_url
                },
            )
            
            # Task 3: Validate data
            # Validates against JSON schemas and business rules
            validate_data_task = PythonOperator(
                task_id=f'validate_data_{client}',
                python_callable=validate_data,
                op_kwargs={'data_type': data_type},
            )
            
            # Task 4: Enrich data
            # Fetches related entities in parallel
            enrich_data_task = PythonOperator(
                task_id=f'enrich_data_{client}',
                python_callable=enrich_data,
                op_kwargs={'data_type': data_type},
            )
            
            # Task 5: Output data
            # Adds metadata and prepares for downstream processing
            output_data_task = PythonOperator(
                task_id=f'output_data_{client}',
                python_callable=output_data,
                op_kwargs={
                    'data_type': data_type,
                    'client': client
                },
            )
            
            # Task 6: Write to S3 Bronze layer
            # Writes data to S3 in Parquet format with date partitioning
            write_s3_task = PythonOperator(
                task_id=f'write_to_s3_{client}',
                python_callable=write_to_s3_bronze,
                op_kwargs={
                    'data_type': data_type,
                    'client': client
                },
            )
            
            # Task 7: Release lock
            # Always executes to ensure lock is released even on failure
            release_lock_task = PythonOperator(
                task_id=f'release_lock_{client}',
                python_callable=release_dynamodb_lock,
                op_kwargs={
                    'data_type': data_type,
                    'client': client
                },
                trigger_rule='all_done',  # Execute even if upstream tasks fail
            )
            
            # Define task dependencies for this client
            # Linear workflow with S3 write and lock release always executing
            acquire_lock_task >> poll_api_task >> validate_data_task >> enrich_data_task >> output_data_task >> write_s3_task >> release_lock_task
    
    return dag
