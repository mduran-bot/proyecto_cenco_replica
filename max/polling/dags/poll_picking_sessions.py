"""
Picking Sessions Polling DAG.

This DAG polls the Janis picking sessions API every 5 minutes (triggered by EventBridge).
It fetches picking session data and writes raw JSON to S3 Bronze.

Schedule: rate(5 minutes) via EventBridge
Data Type: picking_sessions
Clients: metro, wongio
Endpoint: session
Base URL: https://picking.janis.in/api
Tables: wms_order_picking
"""

from base_polling_dag import create_polling_dag

# Create picking sessions polling DAG
dag = create_polling_dag(
    dag_id='poll_picking_sessions',
    data_type='picking_sessions',
    clients=['metro', 'wongio'],
    endpoint='session',
    base_url='https://picking.janis.in/api',
    tags=['polling', 'picking', 'sessions', 'high-frequency'],
)
