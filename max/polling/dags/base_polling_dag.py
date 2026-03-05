"""
Base Polling DAG Factory (Simplified).

This module provides a factory function to create reusable polling DAGs
for different data types (orders, products, stock, prices, stores).

Simplified workflow (no validation, enrichment, or deduplication):
1. Acquire lock in DynamoDB
2. Poll Janis API (raw data, no filters)
3. Write raw JSON to S3 Bronze
4. Release lock (always executes via trigger_rule='all_done')
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
    poll_janis_api_raw,
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
    Factory function to create a simplified polling DAG for a specific data type with multi-tenant support.
    
    Simplified workflow: lock → poll_raw → write_json → unlock
    
    Args:
        dag_id: Unique identifier for the DAG (e.g., 'poll_orders')
        data_type: Type of data to poll (e.g., 'orders', 'products')
        clients: List of client identifiers (e.g., ['metro', 'wongio'])
        endpoint: API endpoint to poll (e.g., 'order')
        base_url: Base URL for the API (e.g., 'https://oms.janis.in/api')
        tags: List of tags for the DAG (e.g., ['polling', 'orders'])
        default_args: Optional default arguments for the DAG
    
    Returns:
        Configured Airflow DAG instance
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
        description=f'Poll {data_type} from Janis API and write raw JSON to S3 Bronze',
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
            
            # Task 2: Poll Janis API (raw data, no filters, no deduplication)
            # Fetches all pages and returns raw JSON
            poll_api_task = PythonOperator(
                task_id=f'poll_api_{client}',
                python_callable=poll_janis_api_raw,
                op_kwargs={
                    'data_type': data_type,
                    'client': client,
                    'endpoint': endpoint,
                    'base_url': base_url
                },
            )
            
            # Task 3: Write raw JSON to S3 Bronze layer
            # Writes data to S3 in JSON format with date partitioning
            write_s3_task = PythonOperator(
                task_id=f'write_to_s3_{client}',
                python_callable=write_to_s3_bronze,
                op_kwargs={
                    'data_type': data_type,
                    'client': client
                },
            )
            
            # Task 4: Release lock
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
            
            # Define simplified task dependencies
            # Linear workflow: lock → poll → write → unlock
            acquire_lock_task >> poll_api_task >> write_s3_task >> release_lock_task
    
    return dag
