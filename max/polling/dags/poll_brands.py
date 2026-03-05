"""
Brands Polling DAG.

This DAG polls the Janis brands API every 1 hour (triggered by EventBridge).
It fetches brand data and writes raw JSON to S3 Bronze.

Schedule: rate(1 hour) via EventBridge
Data Type: brands
Clients: metro, wongio
Endpoint: brand
Base URL: https://catalog.janis.in/api
Tables: brands
"""

from base_polling_dag import create_polling_dag

# Create brands polling DAG
dag = create_polling_dag(
    dag_id='poll_brands',
    data_type='brands',
    clients=['metro', 'wongio'],
    endpoint='brand',
    base_url='https://catalog.janis.in/api',
    tags=['polling', 'catalog', 'brands', 'hourly'],
)
