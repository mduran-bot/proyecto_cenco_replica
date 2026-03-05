"""
Shipping Polling DAG.

This DAG polls the Janis shipping API every 5 minutes (triggered by EventBridge).
It fetches shipping data and writes raw JSON to S3 Bronze.

Schedule: rate(5 minutes) via EventBridge
Data Type: shipping
Clients: metro, wongio
Endpoint: shipping
Base URL: https://delivery.janis.in/api
Tables: wms_order_shipping (additional fields)
"""

from base_polling_dag import create_polling_dag

# Create shipping polling DAG
dag = create_polling_dag(
    dag_id='poll_shipping',
    data_type='shipping',
    clients=['metro', 'wongio'],
    endpoint='shipping',
    base_url='https://delivery.janis.in/api',
    tags=['polling', 'shipping', 'delivery', 'high-frequency'],
)
