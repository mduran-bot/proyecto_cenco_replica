"""
Prices Polling DAG.

This DAG polls the Janis prices API every 30 minutes (triggered by EventBridge).
It fetches price data and writes raw JSON to S3 Bronze.

Schedule: rate(30 minutes) via EventBridge
Data Type: prices
Clients: metro, wongio
Endpoint: price
Base URL: https://pricing.janis.in/api
Tables: price
"""

from base_polling_dag import create_polling_dag

# Create prices polling DAG
dag = create_polling_dag(
    dag_id='poll_prices',
    data_type='prices',
    clients=['metro', 'wongio'],
    endpoint='price',
    base_url='https://pricing.janis.in/api',
    tags=['polling', 'prices', 'medium-frequency'],
)
