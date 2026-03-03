"""
Example usage of StateManager for DynamoDB state management.

This example demonstrates how to use the StateManager class to implement
distributed locking and state tracking for the polling system.
"""

import os
import uuid
from datetime import datetime
from src.state_manager import StateManager


def example_successful_polling():
    """
    Example of a successful polling execution with lock management.
    """
    print("=== Example: Successful Polling Execution ===\n")
    
    # Initialize StateManager
    # For LocalStack testing, pass endpoint_url
    endpoint_url = os.environ.get('LOCALSTACK_ENDPOINT')
    state_manager = StateManager(
        table_name='polling_control',
        endpoint_url=endpoint_url
    )
    
    # Generate unique execution ID
    execution_id = str(uuid.uuid4())
    data_type = 'orders'
    
    print(f"Attempting to acquire lock for {data_type}...")
    
    # Try to acquire lock
    lock_acquired = state_manager.acquire_lock(data_type, execution_id)
    
    if not lock_acquired:
        print(f"Lock already exists for {data_type}, skipping execution")
        return
    
    print(f"Lock acquired successfully (execution_id: {execution_id})")
    
    try:
        # Check for previous execution state
        print("\nChecking for previous execution state...")
        last_modified = state_manager.get_last_modified_date(data_type)
        
        if last_modified:
            print(f"Found previous execution, last_modified: {last_modified}")
            print("Will perform incremental polling")
        else:
            print("No previous execution found, will perform full refresh")
        
        # Simulate polling operation
        print("\nSimulating API polling...")
        # In real implementation, this would call the API
        records_fetched = 150
        latest_modified = datetime.utcnow().isoformat()
        
        print(f"Fetched {records_fetched} records")
        print(f"Latest modification timestamp: {latest_modified}")
        
        # Release lock with success
        print("\nReleasing lock after successful execution...")
        state_manager.release_lock(
            data_type=data_type,
            success=True,
            last_modified=latest_modified,
            records_fetched=records_fetched
        )
        
        print("Lock released successfully")
        
    except Exception as e:
        # Release lock with failure
        print(f"\nError during polling: {e}")
        print("Releasing lock after failed execution...")
        
        state_manager.release_lock(
            data_type=data_type,
            success=False,
            error_message=str(e)
        )
        
        print("Lock released (previous timestamp preserved)")


def example_concurrent_execution_prevention():
    """
    Example demonstrating prevention of concurrent executions.
    """
    print("\n\n=== Example: Concurrent Execution Prevention ===\n")
    
    endpoint_url = os.environ.get('LOCALSTACK_ENDPOINT')
    state_manager = StateManager(
        table_name='polling_control',
        endpoint_url=endpoint_url
    )
    
    data_type = 'products'
    
    # First execution acquires lock
    execution_id_1 = str(uuid.uuid4())
    print(f"Execution 1 attempting to acquire lock...")
    lock_1 = state_manager.acquire_lock(data_type, execution_id_1)
    print(f"Execution 1 lock acquired: {lock_1}")
    
    # Second execution tries to acquire lock (should fail)
    execution_id_2 = str(uuid.uuid4())
    print(f"\nExecution 2 attempting to acquire lock...")
    lock_2 = state_manager.acquire_lock(data_type, execution_id_2)
    print(f"Execution 2 lock acquired: {lock_2}")
    
    if not lock_2:
        print("Execution 2 correctly skipped (lock already held)")
    
    # Release lock from first execution
    print(f"\nExecution 1 releasing lock...")
    state_manager.release_lock(
        data_type=data_type,
        success=True,
        records_fetched=75
    )
    
    # Now second execution can acquire lock
    print(f"\nExecution 2 attempting to acquire lock again...")
    lock_2_retry = state_manager.acquire_lock(data_type, execution_id_2)
    print(f"Execution 2 lock acquired: {lock_2_retry}")
    
    # Clean up
    state_manager.release_lock(
        data_type=data_type,
        success=True,
        records_fetched=80
    )


def example_first_execution():
    """
    Example of first execution with no previous state.
    """
    print("\n\n=== Example: First Execution (No Previous State) ===\n")
    
    endpoint_url = os.environ.get('LOCALSTACK_ENDPOINT')
    state_manager = StateManager(
        table_name='polling_control',
        endpoint_url=endpoint_url
    )
    
    data_type = 'new_entity'
    execution_id = str(uuid.uuid4())
    
    print(f"Checking for previous state for {data_type}...")
    control_item = state_manager.get_control_item(data_type)
    
    if control_item is None:
        print("No previous state found - this is the first execution")
        print("Will perform full data refresh")
    
    print(f"\nAcquiring lock for first execution...")
    lock_acquired = state_manager.acquire_lock(data_type, execution_id)
    print(f"Lock acquired: {lock_acquired}")
    
    # Simulate first polling
    print("\nPerforming full data refresh...")
    records_fetched = 1000
    latest_modified = datetime.utcnow().isoformat()
    
    print(f"Fetched {records_fetched} records")
    
    # Release lock and establish baseline
    print("\nReleasing lock and establishing baseline state...")
    state_manager.release_lock(
        data_type=data_type,
        success=True,
        last_modified=latest_modified,
        records_fetched=records_fetched
    )
    
    print("Baseline state established for future incremental polling")


def example_query_state():
    """
    Example of querying state information.
    """
    print("\n\n=== Example: Querying State Information ===\n")
    
    endpoint_url = os.environ.get('LOCALSTACK_ENDPOINT')
    state_manager = StateManager(
        table_name='polling_control',
        endpoint_url=endpoint_url
    )
    
    data_type = 'orders'
    
    print(f"Retrieving complete state for {data_type}...")
    control_item = state_manager.get_control_item(data_type)
    
    if control_item:
        print("\nCurrent state:")
        print(f"  Data Type: {control_item.get('data_type')}")
        print(f"  Lock Acquired: {control_item.get('lock_acquired')}")
        print(f"  Status: {control_item.get('status')}")
        print(f"  Last Successful Execution: {control_item.get('last_successful_execution')}")
        print(f"  Last Modified Date: {control_item.get('last_modified_date')}")
        print(f"  Records Fetched: {control_item.get('records_fetched', 0)}")
        
        if control_item.get('error_message'):
            print(f"  Last Error: {control_item.get('error_message')}")
    else:
        print("No state found")
    
    # Query just the last_modified_date
    print(f"\nRetrieving last_modified_date for {data_type}...")
    last_modified = state_manager.get_last_modified_date(data_type)
    
    if last_modified:
        print(f"Last modified date: {last_modified}")
    else:
        print("No last_modified_date found (will perform full refresh)")


def example_error_handling():
    """
    Example of error handling and lock release on failure.
    """
    print("\n\n=== Example: Error Handling ===\n")
    
    endpoint_url = os.environ.get('LOCALSTACK_ENDPOINT')
    state_manager = StateManager(
        table_name='polling_control',
        endpoint_url=endpoint_url
    )
    
    data_type = 'stock'
    execution_id = str(uuid.uuid4())
    
    print(f"Acquiring lock for {data_type}...")
    lock_acquired = state_manager.acquire_lock(data_type, execution_id)
    
    if not lock_acquired:
        print("Could not acquire lock, exiting gracefully")
        return
    
    print("Lock acquired")
    
    # Get previous state to preserve it
    print("\nRetrieving previous state...")
    previous_state = state_manager.get_control_item(data_type)
    previous_last_modified = previous_state.get('last_modified_date') if previous_state else None
    
    if previous_last_modified:
        print(f"Previous last_modified_date: {previous_last_modified}")
    
    try:
        # Simulate an error during polling
        print("\nSimulating API error...")
        raise Exception("API connection timeout")
        
    except Exception as e:
        print(f"Error occurred: {e}")
        print("\nReleasing lock with failure status...")
        
        state_manager.release_lock(
            data_type=data_type,
            success=False,
            error_message=str(e)
        )
        
        print("Lock released")
        
        # Verify previous timestamp was preserved
        print("\nVerifying previous timestamp was preserved...")
        current_state = state_manager.get_control_item(data_type)
        current_last_modified = current_state.get('last_modified_date')
        
        if current_last_modified == previous_last_modified:
            print("✓ Previous timestamp preserved correctly")
        else:
            print("✗ Timestamp was modified (unexpected)")


def main():
    """
    Run all examples.
    """
    print("StateManager Usage Examples")
    print("=" * 60)
    
    # Note: These examples assume DynamoDB table exists
    # For LocalStack testing, run init-localstack.ps1 first
    
    try:
        example_successful_polling()
        example_concurrent_execution_prevention()
        example_first_execution()
        example_query_state()
        example_error_handling()
        
        print("\n" + "=" * 60)
        print("All examples completed successfully!")
        
    except Exception as e:
        print(f"\nError running examples: {e}")
        print("\nMake sure DynamoDB table exists:")
        print("  - For LocalStack: Run terraform/scripts/init-localstack.ps1")
        print("  - For AWS: Deploy terraform infrastructure")


if __name__ == '__main__':
    main()
