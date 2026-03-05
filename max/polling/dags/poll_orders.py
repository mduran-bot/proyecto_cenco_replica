"""
Orders Polling DAG.

This DAG polls the Janis orders API every 5 minutes (triggered by EventBridge).
It fetches orders and writes raw JSON to S3 Bronze for multiple clients (metro, wongio).

Schedule: rate(5 minutes) via EventBridge
Data Type: orders
Clients: metro, wongio
Endpoint: order
Base URL: https://oms.janis.in/api
"""

from base_polling_dag import create_polling_dag

# Create orders polling DAG with multi-tenant support
dag = create_polling_dag(
    dag_id='poll_orders',
    data_type='orders',
    clients=['metro', 'wongio'],
    endpoint='order',
    base_url='https://oms.janis.in/api',
    tags=['polling', 'orders', 'high-frequency'],
)
