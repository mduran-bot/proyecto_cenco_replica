"""
Stock Polling DAG.

This DAG polls the Janis stock API every 10 minutes (triggered by EventBridge).
It fetches stock levels and writes raw JSON to S3 Bronze for multiple clients (metro, wongio).

Schedule: rate(10 minutes) via EventBridge
Data Type: stock
Clients: metro, wongio
Endpoint: stock
Base URL: https://wms.janis.in/api
"""

from base_polling_dag import create_polling_dag

# Create stock polling DAG with multi-tenant support
dag = create_polling_dag(
    dag_id='poll_stock',
    data_type='stock',
    clients=['metro', 'wongio'],
    endpoint='stock',
    base_url='https://wms.janis.in/api',
    tags=['polling', 'stock', 'medium-frequency'],
)
