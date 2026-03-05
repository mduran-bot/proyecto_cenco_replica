"""
Carriers Polling DAG.

This DAG polls the Janis carriers API every 24 hours (triggered by EventBridge).
It fetches carrier data and writes raw JSON to S3 Bronze.

Schedule: rate(24 hours) via EventBridge
Data Type: carriers
Clients: metro, wongio
Endpoint: carrier
Base URL: https://delivery.janis.in/api
Tables: wms_logistic_carriers
"""

from base_polling_dag import create_polling_dag

# Create carriers polling DAG
dag = create_polling_dag(
    dag_id='poll_carriers',
    data_type='carriers',
    clients=['metro', 'wongio'],
    endpoint='carrier',
    base_url='https://delivery.janis.in/api',
    tags=['polling', 'logistics', 'carriers', 'daily'],
)
