"""
DynamoDB State Manager for API Polling System

This module provides state management functionality using DynamoDB for the polling system.
It implements distributed locking and state tracking to prevent concurrent executions
and enable incremental polling.

Requirements:
- 3.2: Acquire lock when DAG starts
- 3.3: Skip execution if lock already exists
- 3.5: Update last_successful_execution on success
- 3.6: Release lock on success
- 3.7: Release lock on failure, preserve timestamp
- 3.8: Store last_modified_date for incremental queries
- 4.3: Handle first execution (no previous state)
"""

import os
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any
import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)

LOCK_ACQUIRED_VAL = ':false'
class StateManager:
    """
    Manages polling state in DynamoDB with distributed locking.
    
    This class provides methods to acquire and release locks for polling operations,
    ensuring that only one execution runs at a time for each data type.
    """
    
    def __init__(self, table_name: str = "polling_control", endpoint_url: Optional[str] = None):
        """
        Initialize StateManager with DynamoDB connection.
        
        Args:
            table_name: Name of the DynamoDB control table
            endpoint_url: Optional endpoint URL for LocalStack testing
        """
        self.table_name = table_name
        
        # Configure DynamoDB client
        client_config = {'region_name': os.environ.get('AWS_DEFAULT_REGION', 'us-east-1')}
        if endpoint_url:
            client_config['endpoint_url'] = endpoint_url
            # Usar credenciales de test para LocalStack
            client_config['aws_access_key_id'] = os.environ.get('AWS_ACCESS_KEY_ID', 'test')
            client_config['aws_secret_access_key'] = os.environ.get('AWS_SECRET_ACCESS_KEY', 'test')
        
        self.dynamodb = boto3.resource('dynamodb', **client_config)
        self.table = self.dynamodb.Table(table_name)
        
        logger.info(f"StateManager initialized with table: {table_name}")
    
    def acquire_lock(self, data_type: str, execution_id: str) -> bool:
        """
        Attempt to acquire a lock for the given data type using conditional update.
        
        This method implements distributed locking by using DynamoDB's conditional
        update feature. It will only succeed if no lock currently exists or if
        the existing lock is released (lock_acquired = False).
        
        Requirements:
        - 3.2: Acquire lock when DAG starts
        - 3.3: Skip execution if lock already exists
        
        Args:
            data_type: Type of data being polled (orders, products, etc.)
            execution_id: Unique identifier for this execution
            
        Returns:
            True if lock was acquired successfully, False if lock already exists
            
        Raises:
            ClientError: For DynamoDB errors other than ConditionalCheckFailed
        """
        try:
            now = datetime.now(timezone.utc)
            
            self.table.update_item(
                Key={'data_type': data_type},
                UpdateExpression=(
                    'SET lock_acquired = :true, '
                    'lock_timestamp = :now, '
                    'execution_id = :exec_id, '
                    '#status = :running'
                ),
                ConditionExpression=(
                    'attribute_not_exists(lock_acquired) OR lock_acquired = :false'
                ),
                ExpressionAttributeNames={
                    '#status': 'status'
                },
                ExpressionAttributeValues={
                    ':true': True,
                    'LOCK_ACQUIRED_VAL': False,
                    ':now': now,
                    ':exec_id': execution_id,
                    ':running': 'running'
                }
            )
            
            logger.info(
                f"Lock acquired successfully for {data_type} "
                f"(execution_id: {execution_id})"
            )
            return True
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
                logger.warning(
                    f"Lock already exists for {data_type}, skipping execution"
                )
                return False
            else:
                logger.error(
                    f"Failed to acquire lock for {data_type}: {e}",
                    exc_info=True
                )
                raise
    
    def release_lock(
        self,
        data_type: str,
        success: bool,
        last_modified: Optional[str] = None,
        records_fetched: int = 0,
        error_message: Optional[str] = None
    ) -> None:
        """
        Release the lock and update execution state.
        
        On success, updates last_successful_execution and optionally last_modified_date.
        On failure, releases lock but preserves previous timestamps.
        
        Requirements:
        - 3.5: Update last_successful_execution on success
        - 3.6: Release lock on success
        - 3.7: Release lock on failure, preserve timestamp
        
        Args:
            data_type: Type of data being polled
            success: Whether the execution was successful
            last_modified: Latest modification timestamp from fetched data (optional)
            records_fetched: Number of records fetched in this execution
            error_message: Error message if execution failed (optional)
        """
        try:
            update_expr = 'SET lock_acquired = :false, #status = :status'
            expr_values = {'LOCK_ACQUIRED_VAL': False}
            expr_names = {'#status': 'status'}
            
            if success:
                # Update timestamps and metrics on success
                now = datetime.utcnow().isoformat()
                update_expr += ', last_successful_execution = :now, records_fetched = :records'
                expr_values[':now'] = now
                expr_values[':status'] = 'completed'
                expr_values[':records'] = records_fetched
                
                if last_modified:
                    update_expr += ', last_modified_date = :last_mod'
                    expr_values[':last_mod'] = last_modified
                
                # Clear any previous error message
                update_expr += ' REMOVE error_message'
                
                logger.info(
                    f"Releasing lock for {data_type} after successful execution "
                    f"({records_fetched} records fetched)"
                )
            else:
                # On failure, just release lock and record error
                expr_values[':status'] = 'failed'
                
                if error_message:
                    update_expr += ', error_message = :error'
                    expr_values[':error'] = error_message
                
                logger.warning(
                    f"Releasing lock for {data_type} after failed execution: "
                    f"{error_message or 'Unknown error'}"
                )
            
            self.table.update_item(
                Key={'data_type': data_type},
                UpdateExpression=update_expr,
                ExpressionAttributeNames=expr_names,
                ExpressionAttributeValues=expr_values
            )
            
        except ClientError as e:
            logger.error(
                f"Failed to release lock for {data_type}: {e}",
                exc_info=True
            )
            raise

    def get_control_item(self, data_type: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve the current state for a given data type.
        
        This method reads the control item from DynamoDB. Returns None if the item
        doesn't exist (first execution scenario).
        
        Requirements:
        - 3.8: Read last_modified_date for incremental queries
        - 4.3: Handle first execution (no previous state)
        
        Args:
            data_type: Type of data being polled
            
        Returns:
            Dictionary with state information, or None if item doesn't exist
        """
        try:
            response = self.table.get_item(Key={'data_type': data_type})
            
            if 'Item' in response:
                item = response['Item']
                logger.debug(f"Retrieved state for {data_type}: {item}")
                return item
            else:
                logger.info(
                    f"No existing state found for {data_type} (first execution)"
                )
                return None
                
        except ClientError as e:
            logger.error(
                f"Failed to retrieve state for {data_type}: {e}",
                exc_info=True
            )
            raise
    
    def update_last_modified(self, data_type: str, last_modified: str) -> None:
        """
        Update the last_modified_date timestamp for incremental polling.
        
        This method updates only the last_modified_date field, which is used
        to construct incremental filters for subsequent polling operations.
        
        Requirements:
        - 3.8: Store last_modified_date for incremental queries
        
        Args:
            data_type: Type of data being polled
            last_modified: Latest modification timestamp from fetched data
        """
        try:
            self.table.update_item(
                Key={'data_type': data_type},
                UpdateExpression='SET last_modified_date = :last_mod',
                ExpressionAttributeValues={
                    ':last_mod': last_modified
                }
            )
            
            logger.info(
                f"Updated last_modified_date for {data_type} to {last_modified}"
            )
            
        except ClientError as e:
            logger.error(
                f"Failed to update last_modified for {data_type}: {e}",
                exc_info=True
            )
            raise
    
    def get_last_modified_date(self, data_type: str) -> Optional[str]:
        """
        Get the last_modified_date for a data type.
        
        Convenience method to retrieve just the last_modified_date field,
        which is commonly needed for building incremental filters.
        
        Requirements:
        - 3.8: Read last_modified_date for incremental queries
        - 4.3: Handle first execution (no previous state)
        
        Args:
            data_type: Type of data being polled
            
        Returns:
            ISO format timestamp string, or None if not set or item doesn't exist
        """
        item = self.get_control_item(data_type)
        
        if item:
            last_modified = item.get('last_modified_date')
            if last_modified:
                logger.debug(
                    f"Last modified date for {data_type}: {last_modified}"
                )
                return last_modified
        
        logger.info(
            f"No last_modified_date found for {data_type} "
            "(will perform full refresh)"
        )
        return None
    
    def clear_lock(self, data_type: str) -> None:
        """
        Clear the lock for a data type (for testing/recovery purposes).
        
        This method forcefully releases a lock without updating other fields.
        Should only be used for testing or manual recovery scenarios.
        
        Args:
            data_type: Type of data being polled
        """
        try:
            self.table.update_item(
                Key={'data_type': data_type},
                UpdateExpression='SET lock_acquired = :false',
                ExpressionAttributeValues={
                    'LOCK_ACQUIRED_VAL': False
                }
            )
            
            logger.warning(f"Lock forcefully cleared for {data_type}")
            
        except ClientError as e:
            logger.error(
                f"Failed to clear lock for {data_type}: {e}",
                exc_info=True
            )
            raise
