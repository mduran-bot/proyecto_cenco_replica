"""
Stores Polling DAG.

This DAG polls the Janis stores API every 24 hours (triggered by EventBridge).
It fetches new or modified stores incrementally for multiple clients (metro, wongio)
and prepares them for ETL processing.

Schedule: rate(1 day) via EventBridge
Data Type: stores
Clients: metro, wongio
Endpoint: /location
Base URL: https://commerce.janis.in/api
Enrichment: None (store records are self-contained)
"""

from base_polling_dag import create_polling_dag

# Create stores polling DAG with multi-tenant support
# Requirements:
#   - 1.6: Poll stores every 24 hours
dag = create_polling_dag(
    dag_id='poll_stores',
    data_type='stores',
    clients=['metro', 'wongio'],
    endpoint='/location',
    base_url='https://commerce.janis.in/api',
    tags=['polling', 'stores', 'daily'],
)
