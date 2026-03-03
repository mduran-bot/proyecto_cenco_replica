"""
Orders Polling DAG.

This DAG polls the Janis orders API every 5 minutes (triggered by EventBridge).
It fetches new or modified orders incrementally for multiple clients (metro, wongio)
and prepares them for ETL processing.

Schedule: rate(5 minutes) via EventBridge
Data Type: orders
Clients: metro, wongio
Endpoint: /order
Base URL: https://oms.janis.in/api
Enrichment: Fetches order items for each order
"""

from base_polling_dag import create_polling_dag

# Create orders polling DAG with multi-tenant support
# Requirements:
#   - 1.2: Poll orders every 5 minutes
dag = create_polling_dag(
    dag_id='poll_orders',
    data_type='orders',
    clients=['metro', 'wongio'],
    endpoint='/order',
    base_url='https://oms.janis.in/api',
    tags=['polling', 'orders', 'high-frequency'],
)
