"""
Stores Polling DAG.

This DAG polls the Janis stores API every 24 hours (triggered by EventBridge).
It fetches stores and writes raw JSON to S3 Bronze for multiple clients (metro, wongio).

Schedule: rate(24 hours) via EventBridge
Data Type: stores
Clients: metro, wongio
Endpoint: stores
Base URL: https://commerce.janis.in/api
"""

from base_polling_dag import create_polling_dag

# Create stores polling DAG with multi-tenant support
dag = create_polling_dag(
    dag_id='poll_stores',
    data_type='stores',
    clients=['metro', 'wongio'],
    endpoint='stores',
    base_url='https://commerce.janis.in/api',
    tags=['polling', 'stores', 'daily'],
)
