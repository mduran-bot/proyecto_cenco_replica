"""
SKUs Polling DAG.

This DAG polls the Janis SKUs API every 1 hour (triggered by EventBridge).
It fetches SKU data and writes raw JSON to S3 Bronze.

Schedule: rate(1 hour) via EventBridge
Data Type: skus
Clients: metro, wongio
Endpoint: sku
Base URL: https://catalog.janis.in/api
Tables: skus
"""

from base_polling_dag import create_polling_dag

# Create SKUs polling DAG
dag = create_polling_dag(
    dag_id='poll_skus',
    data_type='skus',
    clients=['metro', 'wongio'],
    endpoint='sku',
    base_url='https://catalog.janis.in/api',
    tags=['polling', 'catalog', 'skus', 'hourly'],
)
