"""
Delivery Planning Polling DAG.

This DAG polls the Janis delivery planning API every 24 hours (triggered by EventBridge).
It fetches route planning data and writes raw JSON to S3 Bronze.

Schedule: rate(24 hours) via EventBridge
Data Type: delivery_planning
Clients: metro, wongio
Endpoint: route-planning
Base URL: https://tms.janis.in/api
Tables: wms_logistic_delivery_planning
"""

from base_polling_dag import create_polling_dag

# Create delivery planning polling DAG
dag = create_polling_dag(
    dag_id='poll_delivery_planning',
    data_type='delivery_planning',
    clients=['metro', 'wongio'],
    endpoint='route-planning',
    base_url='https://tms.janis.in/api',
    tags=['polling', 'logistics', 'delivery-planning', 'daily'],
)
