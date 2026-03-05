"""
Delivery Ranges Polling DAG.

This DAG polls the Janis delivery ranges API every 24 hours (triggered by EventBridge).
It fetches time slot data and writes raw JSON to S3 Bronze.

Schedule: rate(24 hours) via EventBridge
Data Type: delivery_ranges
Clients: metro, wongio
Endpoint: time-slot
Base URL: https://delivery.janis.in/api
Tables: wms_logistic_delivery_ranges
"""

from base_polling_dag import create_polling_dag

# Create delivery ranges polling DAG
dag = create_polling_dag(
    dag_id='poll_delivery_ranges',
    data_type='delivery_ranges',
    clients=['metro', 'wongio'],
    endpoint='time-slot',
    base_url='https://delivery.janis.in/api',
    tags=['polling', 'logistics', 'delivery-ranges', 'daily'],
)
