"""
Example usage of incremental polling functions.

This example demonstrates how to use build_incremental_filter and
deduplicate_records for incremental polling operations.
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.state_manager import StateManager
from src.api_client import JanisAPIClient
from src.pagination_handler import PaginationHandler
from src.incremental_polling import build_incremental_filter, deduplicate_records


def example_incremental_polling():
    """
    Example of complete incremental polling workflow.
    
    This demonstrates:
    1. Building incremental filter from DynamoDB state
    2. Fetching data with pagination
    3. Deduplicating records from overlap window
    """
    print("=" * 80)
    print("Incremental Polling Example")
    print("=" * 80)
    
    # Initialize components
    # Note: Use LocalStack endpoint for testing
    endpoint_url = os.environ.get('LOCALSTACK_ENDPOINT', 'http://localhost:4566')
    
    state_manager = StateManager(
        table_name="polling_control",
        endpoint_url=endpoint_url
    )
    
    api_client = JanisAPIClient(
        base_url="https://api.janis.in",
        api_key="your-api-key-here",
        rate_limit=100
    )
    
    pagination_handler = PaginationHandler(
        client=api_client,
        max_pages=1000,
        page_size=100
    )
    
    data_type = "orders"
    
    print(f"\n1. Building incremental filter for '{data_type}'...")
    print("-" * 80)
    
    # Step 1: Build incremental filter
    filters = build_incremental_filter(state_manager, data_type)
    
    if filters:
        print(f"   Incremental filter created:")
        print(f"   - dateModified: {filters.get('dateModified')}")
        print(f"   - sortBy: {filters.get('sortBy')}")
        print(f"   - sortOrder: {filters.get('sortOrder')}")
        print(f"   (1-minute overlap window applied)")
    else:
        print(f"   No previous state found - performing FULL REFRESH")
    
    print(f"\n2. Fetching data from API with pagination...")
    print("-" * 80)
    
    try:
        # Step 2: Fetch all pages with filters
        # Note: This will fail without valid API credentials
        # In production, this would fetch actual data
        print(f"   Fetching pages from endpoint '{data_type}'...")
        print(f"   (This is a demo - would fetch real data in production)")
        
        # Simulated records for demonstration
        all_records = [
            {'id': '123', 'dateModified': '2024-01-15T10:25:00Z', 'status': 'pending'},
            {'id': '123', 'dateModified': '2024-01-15T10:26:00Z', 'status': 'completed'},
            {'id': '456', 'dateModified': '2024-01-15T10:25:00Z', 'status': 'pending'},
            {'id': '789', 'dateModified': '2024-01-15T10:27:00Z', 'status': 'processing'}
        ]
        
        print(f"   Fetched {len(all_records)} records (simulated)")
        
    except Exception as e:
        print(f"   Error fetching data: {e}")
        print(f"   Using simulated data for demonstration...")
        all_records = []
    
    print(f"\n3. Deduplicating records...")
    print("-" * 80)
    
    # Step 3: Deduplicate records
    deduplicated_records = deduplicate_records(all_records)
    
    print(f"   Original records: {len(all_records)}")
    print(f"   Deduplicated records: {len(deduplicated_records)}")
    print(f"   Duplicates removed: {len(all_records) - len(deduplicated_records)}")
    
    if deduplicated_records:
        print(f"\n   Deduplicated records:")
        for record in deduplicated_records:
            print(f"   - ID: {record['id']}, "
                  f"Modified: {record['dateModified']}, "
                  f"Status: {record['status']}")
    
    print(f"\n4. Summary")
    print("-" * 80)
    print(f"   Data type: {data_type}")
    print(f"   Filter type: {'Incremental' if filters else 'Full Refresh'}")
    print(f"   Records fetched: {len(all_records)}")
    print(f"   Records after deduplication: {len(deduplicated_records)}")
    
    print("\n" + "=" * 80)
    print("Example completed successfully!")
    print("=" * 80)


def example_first_execution():
    """
    Example of first execution (full refresh) scenario.
    """
    print("\n" + "=" * 80)
    print("First Execution Example (Full Refresh)")
    print("=" * 80)
    
    # Mock state manager that returns None (no previous state)
    class MockStateManager:
        def get_last_modified_date(self, data_type):
            return None
    
    state_manager = MockStateManager()
    data_type = "products"
    
    print(f"\nBuilding filter for '{data_type}' (first execution)...")
    filters = build_incremental_filter(state_manager, data_type)
    
    print(f"Result: {filters}")
    print(f"Interpretation: Empty filter = Full Refresh (fetch all records)")
    
    print("\n" + "=" * 80)


def example_deduplication_scenarios():
    """
    Example of different deduplication scenarios.
    """
    print("\n" + "=" * 80)
    print("Deduplication Scenarios")
    print("=" * 80)
    
    # Scenario 1: No duplicates
    print("\nScenario 1: No duplicates")
    print("-" * 80)
    records1 = [
        {'id': '123', 'dateModified': '2024-01-15T10:25:00Z'},
        {'id': '456', 'dateModified': '2024-01-15T10:26:00Z'},
        {'id': '789', 'dateModified': '2024-01-15T10:27:00Z'}
    ]
    result1 = deduplicate_records(records1)
    print(f"Input: {len(records1)} records")
    print(f"Output: {len(result1)} records")
    print(f"Result: All records kept (no duplicates)")
    
    # Scenario 2: Simple duplicates
    print("\nScenario 2: Simple duplicates (keep most recent)")
    print("-" * 80)
    records2 = [
        {'id': '123', 'dateModified': '2024-01-15T10:25:00Z', 'version': 'old'},
        {'id': '123', 'dateModified': '2024-01-15T10:26:00Z', 'version': 'new'}
    ]
    result2 = deduplicate_records(records2)
    print(f"Input: {len(records2)} records")
    print(f"Output: {len(result2)} records")
    print(f"Kept: {result2[0]['version']} (most recent timestamp)")
    
    # Scenario 3: Multiple duplicates
    print("\nScenario 3: Multiple duplicates of same ID")
    print("-" * 80)
    records3 = [
        {'id': '123', 'dateModified': '2024-01-15T10:25:00Z', 'version': 'v1'},
        {'id': '123', 'dateModified': '2024-01-15T10:26:00Z', 'version': 'v2'},
        {'id': '123', 'dateModified': '2024-01-15T10:27:00Z', 'version': 'v3'},
        {'id': '123', 'dateModified': '2024-01-15T10:24:00Z', 'version': 'v0'}
    ]
    result3 = deduplicate_records(records3)
    print(f"Input: {len(records3)} records")
    print(f"Output: {len(result3)} records")
    print(f"Kept: {result3[0]['version']} (most recent timestamp)")
    
    print("\n" + "=" * 80)


if __name__ == '__main__':
    # Run examples
    example_first_execution()
    example_deduplication_scenarios()
    example_incremental_polling()
