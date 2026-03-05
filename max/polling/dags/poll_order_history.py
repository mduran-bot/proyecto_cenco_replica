"""
Order History Polling DAG.

This DAG polls the Janis order history API every 5 minutes (triggered by EventBridge).
It fetches order status changes and writes raw JSON to S3 Bronze.

Schedule: rate(5 minutes) via EventBridge
Data Type: order_history
Clients: metro, wongio
Endpoint: order/{id}/history
Base URL: https://oms.janis.in/api
Tables: wms_order_status_changes
"""

from base_polling_dag import create_polling_dag

# Create order history polling DAG
dag = create_polling_dag(
    dag_id='poll_order_history',
    data_type='order_history',
    clients=['metro', 'wongio'],
    endpoint='order/history',  # Note: Will need order IDs from previous poll
    base_url='https://oms.janis.in/api',
    tags=['polling', 'orders', 'history', 'high-frequency'],
)
