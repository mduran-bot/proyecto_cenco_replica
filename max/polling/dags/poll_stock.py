"""
Stock Polling DAG.

This DAG polls the Janis stock API every 10 minutes (triggered by EventBridge).
It fetches new or modified stock levels incrementally for multiple clients (metro, wongio)
and prepares them for ETL processing.

Schedule: rate(10 minutes) via EventBridge
Data Type: stock
Clients: metro, wongio
Endpoint: /sku-stock
Base URL: https://wms.janis.in/api
Enrichment: None (stock records are self-contained)
"""

from base_polling_dag import create_polling_dag

# Create stock polling DAG with multi-tenant support
# Requirements:
#   - 1.4: Poll stock every 10 minutes
dag = create_polling_dag(
    dag_id='poll_stock',
    data_type='stock',
    clients=['metro', 'wongio'],
    endpoint='/sku-stock',
    base_url='https://wms.janis.in/api',
    tags=['polling', 'stock', 'medium-frequency'],
)
