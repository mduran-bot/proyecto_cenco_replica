"""
Categories Polling DAG.

This DAG polls the Janis categories API every 1 hour (triggered by EventBridge).
It fetches category data and writes raw JSON to S3 Bronze.

Schedule: rate(1 hour) via EventBridge
Data Type: categories
Clients: metro, wongio
Endpoint: category
Base URL: https://catalog.janis.in/api
Tables: categories
"""

from base_polling_dag import create_polling_dag

# Create categories polling DAG
dag = create_polling_dag(
    dag_id='poll_categories',
    data_type='categories',
    clients=['metro', 'wongio'],
    endpoint='category',
    base_url='https://catalog.janis.in/api',
    tags=['polling', 'catalog', 'categories', 'hourly'],
)
