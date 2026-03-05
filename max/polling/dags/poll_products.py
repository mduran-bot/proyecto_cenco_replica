"""
Products Polling DAG.

This DAG polls the Janis products API every 1 hour (triggered by EventBridge).
It fetches product data and writes raw JSON to S3 Bronze.

Schedule: rate(1 hour) via EventBridge
Data Type: products
Clients: metro, wongio
Endpoint: product
Base URL: https://catalog.janis.in/api
Tables: products
"""

from base_polling_dag import create_polling_dag

# Create products polling DAG
dag = create_polling_dag(
    dag_id='poll_products',
    data_type='products',
    clients=['metro', 'wongio'],
    endpoint='product',
    base_url='https://catalog.janis.in/api',
    tags=['polling', 'catalog', 'products', 'hourly'],
)
