"""
Sales Channel SKU Prices Polling DAG.

This DAG polls the Janis SC SKU prices API every 30 minutes (triggered by EventBridge).
It fetches sales channel specific SKU prices and writes raw JSON to S3 Bronze.

Schedule: rate(30 minutes) via EventBridge
Data Type: sc_sku_prices
Clients: metro, wongio
Endpoint: sc-sku-price
Base URL: https://pricing.janis.in/api
Tables: price (store_price field)
"""

from base_polling_dag import create_polling_dag

# Create SC SKU prices polling DAG
dag = create_polling_dag(
    dag_id='poll_sc_sku_prices',
    data_type='sc_sku_prices',
    clients=['metro', 'wongio'],
    endpoint='sc-sku-price',
    base_url='https://pricing.janis.in/api',
    tags=['polling', 'prices', 'sales-channel', 'medium-frequency'],
)
