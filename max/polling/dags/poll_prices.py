"""
Prices Polling DAG.

This DAG polls the Janis prices APIs every 30 minutes (triggered by EventBridge).
It fetches new or modified prices incrementally for multiple clients (metro, wongio)
from 3 different endpoints and prepares them for ETL processing.

Schedule: rate(30 minutes) via EventBridge
Data Type: prices
Clients: metro, wongio
Endpoints: /price, /price-sheet, /base-price (3 endpoints × 2 clients = 6 API calls)
Base URL: https://vtex.pricing.janis.in/api
Enrichment: None (price records are self-contained)
"""

import sys
import os
from datetime import datetime, timedelta
from airflow import DAG
from airflow.providers.standard.operators.python import PythonOperator

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Import task functions
from airflow_tasks import (
    acquire_dynamodb_lock,
    poll_janis_api,
    validate_data,
    enrich_data,
    output_data,
    release_dynamodb_lock
)

# Default arguments for all tasks
default_args = {
    'owner': 'data-engineering',
    'depends_on_past': False,
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 0,
    'retry_delay': timedelta(minutes=5),
}

# Create prices polling DAG with multiple endpoints
# Requirements:
#   - 1.5: Poll prices every 30 minutes
dag = DAG(
    dag_id='poll_prices',
    default_args=default_args,
    description='Poll prices from Janis API with incremental sync (3 endpoints × 2 clients)',
    schedule=None,  # Event-driven via EventBridge
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=['polling', 'prices', 'medium-frequency'],
    max_active_runs=1,
)

# Define clients and endpoints
clients = ['metro', 'wongio']
endpoints = ['/price', '/price-sheet', '/base-price']
base_url = 'https://vtex.pricing.janis.in/api'
data_type = 'prices'

with dag:
    # Create tasks for each client and endpoint combination
    for client in clients:
        for endpoint in endpoints:
            # Create a unique suffix for task naming
            endpoint_suffix = endpoint.replace('/', '').replace('-', '_')
            task_suffix = f'{client}_{endpoint_suffix}'
            
            # Task 1: Acquire lock
            acquire_lock_task = PythonOperator(
                task_id=f'acquire_lock_{task_suffix}',
                python_callable=acquire_dynamodb_lock,
                op_kwargs={
                    'data_type': f'{data_type}_{endpoint_suffix}',
                    'client': client
                },
            )
            
            # Task 2: Poll API
            poll_api_task = PythonOperator(
                task_id=f'poll_api_{task_suffix}',
                python_callable=poll_janis_api,
                op_kwargs={
                    'data_type': f'{data_type}_{endpoint_suffix}',
                    'client': client,
                    'endpoint': endpoint,
                    'base_url': base_url
                },
            )
            
            # Task 3: Validate data
            validate_data_task = PythonOperator(
                task_id=f'validate_data_{task_suffix}',
                python_callable=validate_data,
                op_kwargs={'data_type': f'{data_type}_{endpoint_suffix}'},
            )
            
            # Task 4: Enrich data
            enrich_data_task = PythonOperator(
                task_id=f'enrich_data_{task_suffix}',
                python_callable=enrich_data,
                op_kwargs={'data_type': f'{data_type}_{endpoint_suffix}'},
            )
            
            # Task 5: Output data
            output_data_task = PythonOperator(
                task_id=f'output_data_{task_suffix}',
                python_callable=output_data,
                op_kwargs={
                    'data_type': f'{data_type}_{endpoint_suffix}',
                    'client': client
                },
            )
            
            # Task 6: Release lock
            release_lock_task = PythonOperator(
                task_id=f'release_lock_{task_suffix}',
                python_callable=release_dynamodb_lock,
                op_kwargs={
                    'data_type': f'{data_type}_{endpoint_suffix}',
                    'client': client
                },
                trigger_rule='all_done',
            )
            
            # Define task dependencies for this client-endpoint combination
            acquire_lock_task >> poll_api_task >> validate_data_task >> enrich_data_task >> output_data_task >> release_lock_task

