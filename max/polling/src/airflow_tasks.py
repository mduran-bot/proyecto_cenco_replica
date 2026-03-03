"""
Airflow Task Functions for API Polling System

This module implements the task functions used in the polling DAGs.
Each function corresponds to a task in the DAG workflow.

Requirements:
- Task 11.1: acquire_dynamodb_lock - Acquire lock before polling
- Task 11.2: poll_janis_api - Poll API with incremental filters
- Task 11.3: validate_data - Validate against schemas
- Task 11.4: enrich_data - Enrich with related entities
- Task 11.5: output_data - Add metadata and prepare output
- Task 11.6: release_dynamodb_lock - Release lock and update state
"""

import os
import logging
from datetime import datetime
from typing import Dict, Any, Optional

# Import Airflow exception (may not be available in testing)
try:
    from airflow.exceptions import AirflowSkipException
except ImportError:
    # Define a placeholder for testing
    class AirflowSkipException(Exception):
        """Placeholder for Airflow skip exception when Airflow is not installed."""
        pass

# Import our polling components with fallback for different import contexts
try:
    # Try relative imports first (when imported as module)
    from .state_manager import StateManager
    from .api_client import JanisAPIClient
    from .pagination_handler import PaginationHandler
    from .incremental_polling import build_incremental_filter, deduplicate_records
    from .data_validator import DataValidator
    from .data_enricher import DataEnricher
    from .s3_writer import S3Writer
except ImportError:
    # Fall back to absolute imports (when run directly or in tests)
    from state_manager import StateManager
    from api_client import JanisAPIClient
    from pagination_handler import PaginationHandler
    from incremental_polling import build_incremental_filter, deduplicate_records
    from data_validator import DataValidator
    from data_enricher import DataEnricher
    from s3_writer import S3Writer

logger = logging.getLogger(__name__)


# ============================================================================
# Task 11.1: Acquire DynamoDB Lock
# ============================================================================

def acquire_dynamodb_lock(data_type: str, client: str, **context) -> bool:
    """
    Acquire lock in DynamoDB for the specified data type and client.
    
    This function attempts to acquire a distributed lock to prevent concurrent
    executions of the same polling job. If the lock cannot be acquired (another
    execution is running), it gracefully skips the current execution.
    
    Multi-tenant support: Uses composite key "{data_type}-{client}" for DynamoDB
    to allow independent polling per client.
    
    Requirements:
    - 3.2: Attempt to acquire lock with conditional update
    - 3.3: Skip execution if lock already exists
    - 11.4: Generate unique execution_id from Airflow context
    
    Args:
        data_type: Type of data being polled (orders, products, etc.)
        client: Client identifier (metro, wongio, etc.)
        **context: Airflow context with execution metadata (run_id, etc.)
    
    Returns:
        True if lock was acquired successfully
    
    Raises:
        AirflowSkipException: If lock cannot be acquired (graceful skip)
    
    Example:
        In DAG definition:
        >>> acquire_lock_task = PythonOperator(
        ...     task_id='acquire_lock_metro',
        ...     python_callable=acquire_dynamodb_lock,
        ...     op_kwargs={'data_type': 'orders', 'client': 'metro'},
        ...     provide_context=True,
        ... )
    """
    # Get execution_id from Airflow context
    execution_id = context['run_id']
    
    # Construct composite key for multi-tenant support
    composite_key = f"{data_type}-{client}"
    
    logger.info(
        f"[{composite_key}] Attempting to acquire lock "
        f"(execution_id: {execution_id})"
    )
    
    # Get DynamoDB configuration
    table_name = os.environ.get('DYNAMODB_TABLE_NAME', 'polling_control')
    endpoint_url = os.environ.get('LOCALSTACK_ENDPOINT')
    
    # Initialize StateManager
    state_manager = StateManager(
        table_name=table_name,
        endpoint_url=endpoint_url
    )
    
    # Attempt to acquire lock using composite key
    lock_acquired = state_manager.acquire_lock(composite_key, execution_id)
    
    if not lock_acquired:
        # Lock already exists - skip this execution gracefully
        logger.warning(
            f"[{composite_key}] Lock already exists, skipping execution. "
            "Another instance may be running."
        )
        raise AirflowSkipException(
            f"Lock already acquired for {composite_key}, skipping execution"
        )
    
    logger.info(
        f"[{composite_key}] Lock acquired successfully "
        f"(execution_id: {execution_id})"
    )
    
    # Store execution_id and client in XCom for downstream tasks
    context['task_instance'].xcom_push(key='execution_id', value=execution_id)
    context['task_instance'].xcom_push(key='client', value=client)
    
    return True


# ============================================================================
# Task 11.2: Poll Janis API
# ============================================================================

def poll_janis_api(data_type: str, client: str, endpoint: str, base_url: str, **context) -> Dict[str, Any]:
    """
    Poll Janis API with incremental filters and pagination.
    
    This function builds an incremental filter based on the last successful
    execution, polls the Janis API with pagination, and deduplicates the
    results. It handles both full refresh (first execution) and incremental
    polling (subsequent executions).
    
    Multi-tenant support: Uses composite key "{data_type}-{client}" for state
    management and includes "janis-client" header in API requests.
    
    Requirements:
    - 4.1: Build incremental filter with last_modified_date
    - 4.2: Use 1-minute overlap window
    - 4.4: Deduplicate records by ID and timestamp
    - 5.1: Apply rate limiting (handled by JanisAPIClient)
    - 6.1: Use pagination with page size 100
    - 6.2: Follow pagination links until completion
    
    Args:
        data_type: Type of data to poll (orders, products, stock, prices, stores)
        client: Client identifier (metro, wongio, etc.)
        endpoint: Specific API endpoint to call (e.g., /order, /product)
        base_url: Base URL for the API (e.g., https://oms.janis.in/api)
        **context: Airflow context
    
    Returns:
        Dictionary with:
            - records: List of deduplicated records
            - total_fetched: Total records fetched before deduplication
            - total_unique: Total unique records after deduplication
            - last_modified: Latest dateModified timestamp from records
    
    Example:
        In DAG definition:
        >>> poll_api_task = PythonOperator(
        ...     task_id='poll_api_metro',
        ...     python_callable=poll_janis_api,
        ...     op_kwargs={
        ...         'data_type': 'orders',
        ...         'client': 'metro',
        ...         'endpoint': '/order',
        ...         'base_url': 'https://oms.janis.in/api'
        ...     },
        ...     provide_context=True,
        ... )
    """
    # Construct composite key for multi-tenant support
    composite_key = f"{data_type}-{client}"
    
    logger.info(f"[{composite_key}] Starting API polling from {base_url}{endpoint}")
    
    # Get configuration from environment
    api_key = os.environ.get('JANIS_API_KEY')
    table_name = os.environ.get('DYNAMODB_TABLE_NAME', 'polling_control')
    endpoint_url_localstack = os.environ.get('LOCALSTACK_ENDPOINT')
    
    if not api_key:
        raise ValueError("JANIS_API_KEY must be set in environment")
    
    # Initialize components
    state_manager = StateManager(
        table_name=table_name,
        endpoint_url=endpoint_url_localstack
    )
    
    # Initialize API client with janis-client header
    api_client = JanisAPIClient(
        base_url=base_url,
        api_key=api_key,
        rate_limit=100,
        extra_headers={'janis-client': client}
    )
    
    pagination_handler = PaginationHandler(
        client=api_client,
        max_pages=1000,
        page_size=100
    )
    
    try:
        # Build incremental filter using composite key
        filters = build_incremental_filter(state_manager, composite_key)
        
        if filters:
            logger.info(
                f"[{composite_key}] Using incremental filter: "
                f"dateModified >= {filters.get('dateModified')}"
            )
        else:
            logger.info(
                f"[{composite_key}] Performing full refresh (no previous execution)"
            )
        
        # Fetch all pages from the specific endpoint
        all_records = pagination_handler.fetch_all_pages(
            endpoint=endpoint,
            filters=filters
        )
        
        total_fetched = len(all_records)
        logger.info(f"[{composite_key}] Fetched {total_fetched} records from API")
        
        # Deduplicate records
        unique_records = deduplicate_records(all_records)
        total_unique = len(unique_records)
        
        logger.info(
            f"[{composite_key}] After deduplication: "
            f"{total_unique} unique records "
            f"({total_fetched - total_unique} duplicates removed)"
        )
        
        # Find latest dateModified for state tracking
        last_modified = None
        if unique_records:
            # Get the most recent dateModified timestamp
            timestamps = [
                r.get('dateModified') for r in unique_records
                if r.get('dateModified')
            ]
            if timestamps:
                last_modified = max(timestamps)
                logger.info(
                    f"[{composite_key}] Latest dateModified: {last_modified}"
                )
        
        result = {
            'records': unique_records,
            'total_fetched': total_fetched,
            'total_unique': total_unique,
            'last_modified': last_modified
        }
        
        # Push to XCom for next task
        context['task_instance'].xcom_push(key='polling_result', value=result)
        
        return result
        
    finally:
        # Always close the API client
        api_client.close()


# ============================================================================
# Task 11.3: Validate Data
# ============================================================================

def validate_data(data_type: str, **context) -> Dict[str, Any]:
    """
    Validate data against JSON schemas and business rules.
    
    This function retrieves the polled data from XCom, validates each record
    against the JSON schema for the data type, detects duplicates within the
    batch, and applies business rules. It returns only valid records and
    comprehensive validation metrics.
    
    Requirements:
    - 8.1: Validate against JSON schemas
    - 8.2: Exclude invalid records from output
    - 8.3: Detect duplicates within batch
    - 8.4: Validate business rules
    - 8.5: Calculate and log validation metrics
    
    Args:
        data_type: Type of data being validated
        **context: Airflow context
    
    Returns:
        Dictionary with:
            - valid_records: List of records that passed validation
            - metrics: Validation metrics (counts, rates, errors)
    
    Example:
        In DAG definition:
        >>> validate_task = PythonOperator(
        ...     task_id='validate_data',
        ...     python_callable=validate_data,
        ...     op_kwargs={'data_type': 'orders'},
        ...     provide_context=True,
        ... )
    """
    logger.info(f"[{data_type}] Starting data validation")
    
    # Get polling result from XCom
    ti = context['task_instance']
    polling_result = ti.xcom_pull(
        task_ids='poll_api',
        key='polling_result'
    )
    
    if not polling_result:
        logger.warning(f"[{data_type}] No polling result found in XCom")
        return {
            'valid_records': [],
            'metrics': {
                'total_received': 0,
                'valid_count': 0,
                'invalid_count': 0,
                'validation_pass_rate': 100.0
            }
        }
    
    records = polling_result.get('records', [])
    
    if not records:
        logger.info(f"[{data_type}] No records to validate")
        return {
            'valid_records': [],
            'metrics': {
                'total_received': 0,
                'valid_count': 0,
                'invalid_count': 0,
                'validation_pass_rate': 100.0
            }
        }
    
    # Get schemas directory from environment or use default
    schemas_dir = os.environ.get(
        'SCHEMAS_DIR',
        os.path.join(os.path.dirname(__file__), 'schemas')
    )
    
    # Initialize validator
    validator = DataValidator(
        data_type=data_type,
        schemas_dir=schemas_dir
    )
    
    # Validate batch
    valid_records, metrics = validator.validate_batch(records)
    
    # Log validation results
    logger.info(
        f"[{data_type}] Validation completed: "
        f"{metrics['valid_count']}/{metrics['total_received']} records valid "
        f"({metrics['validation_pass_rate']:.2f}% pass rate)"
    )
    
    if metrics['invalid_count'] > 0:
        logger.warning(
            f"[{data_type}] {metrics['invalid_count']} invalid records excluded"
        )
    
    if metrics.get('duplicates_in_batch', 0) > 0:
        logger.info(
            f"[{data_type}] {metrics['duplicates_in_batch']} duplicates "
            "detected and removed"
        )
    
    result = {
        'valid_records': valid_records,
        'metrics': metrics
    }
    
    # Push to XCom for next task
    ti.xcom_push(key='validation_result', value=result)
    
    return result


# ============================================================================
# Task 11.4: Enrich Data
# ============================================================================

def enrich_data(data_type: str, **context) -> Dict[str, Any]:
    """
    Enrich data with related entities in parallel.
    
    This function retrieves validated data from XCom and enriches it based on
    the data type:
    - orders: Fetch items for each order
    - products: Fetch SKUs for each product
    - Other types: No enrichment (pass through)
    
    Enrichment is done in parallel using ThreadPoolExecutor. If enrichment
    fails for a record, it's included with _enrichment_complete=False.
    
    Requirements:
    - 7.1: Enrich orders with items via orders/{id}/items
    - 7.2: Enrich products with SKUs via products/{id}/skus
    - 7.4: Continue on enrichment failures with error flag
    - 7.5: Add enrichment metadata to records
    
    Args:
        data_type: Type of data being enriched
        **context: Airflow context
    
    Returns:
        Dictionary with:
            - enriched_records: List of enriched records
            - enrichment_stats: Statistics about enrichment success/failure
    
    Example:
        In DAG definition:
        >>> enrich_task = PythonOperator(
        ...     task_id='enrich_data',
        ...     python_callable=enrich_data,
        ...     op_kwargs={'data_type': 'orders'},
        ...     provide_context=True,
        ... )
    """
    logger.info(f"[{data_type}] Starting data enrichment")
    
    # Get validation result from XCom
    ti = context['task_instance']
    validation_result = ti.xcom_pull(
        task_ids='validate_data',
        key='validation_result'
    )
    
    if not validation_result:
        logger.warning(f"[{data_type}] No validation result found in XCom")
        return {
            'enriched_records': [],
            'enrichment_stats': {
                'total_records': 0,
                'enriched_count': 0,
                'failed_count': 0
            }
        }
    
    valid_records = validation_result.get('valid_records', [])
    
    if not valid_records:
        logger.info(f"[{data_type}] No valid records to enrich")
        return {
            'enriched_records': [],
            'enrichment_stats': {
                'total_records': 0,
                'enriched_count': 0,
                'failed_count': 0
            }
        }
    
    # Check if this data type requires enrichment
    enrichable_types = {'orders', 'products'}
    
    if data_type not in enrichable_types:
        logger.info(
            f"[{data_type}] No enrichment needed for this data type, "
            "passing through"
        )
        return {
            'enriched_records': valid_records,
            'enrichment_stats': {
                'total_records': len(valid_records),
                'enriched_count': 0,
                'failed_count': 0,
                'enrichment_skipped': True
            }
        }
    
    # Get API configuration
    api_base_url = os.environ.get('JANIS_API_BASE_URL')
    api_key = os.environ.get('JANIS_API_KEY')
    
    if not api_base_url or not api_key:
        raise ValueError(
            "JANIS_API_BASE_URL and JANIS_API_KEY must be set in environment"
        )
    
    # Initialize API client and enricher
    api_client = JanisAPIClient(
        base_url=api_base_url,
        api_key=api_key,
        rate_limit=100
    )
    
    enricher = DataEnricher(
        client=api_client,
        max_workers=5
    )
    
    try:
        # Enrich based on data type
        if data_type == 'orders':
            logger.info(f"[{data_type}] Enriching orders with items")
            enriched_records = enricher.enrich_orders(valid_records)
        elif data_type == 'products':
            logger.info(f"[{data_type}] Enriching products with SKUs")
            enriched_records = enricher.enrich_products(valid_records)
        else:
            # Should not reach here due to earlier check
            enriched_records = valid_records
        
        # Calculate enrichment statistics
        total_records = len(enriched_records)
        enriched_count = sum(
            1 for r in enriched_records
            if r.get('_enrichment_complete', False)
        )
        failed_count = total_records - enriched_count
        
        logger.info(
            f"[{data_type}] Enrichment completed: "
            f"{enriched_count}/{total_records} successful, "
            f"{failed_count} failed"
        )
        
        result = {
            'enriched_records': enriched_records,
            'enrichment_stats': {
                'total_records': total_records,
                'enriched_count': enriched_count,
                'failed_count': failed_count
            }
        }
        
        # Push to XCom for next task
        ti.xcom_push(key='enrichment_result', value=result)
        
        return result
        
    finally:
        # Always close the API client
        api_client.close()


# ============================================================================
# Task 11.5: Output Data
# ============================================================================

def output_data(data_type: str, client: str, **context) -> Dict[str, Any]:
    """
    Add metadata and prepare data for downstream processing.
    
    This function retrieves enriched data from XCom, adds polling metadata
    (execution_id, poll_timestamp, data_type, client) to each record, and prepares
    the final output. It logs the total number of records processed.
    
    Multi-tenant support: Includes client identifier in metadata and S3 path
    structure (bronze/{client}/{data_type}/).
    
    Requirements:
    - 9.2: Add polling metadata (execution_id, poll_timestamp, data_type)
    - 9.4: Log total records processed
    
    Args:
        data_type: Type of data being output
        client: Client identifier (metro, wongio, etc.)
        **context: Airflow context
    
    Returns:
        Dictionary with:
            - output_records: List of records with complete metadata
            - summary: Summary statistics
    
    Example:
        In DAG definition:
        >>> output_task = PythonOperator(
        ...     task_id='output_data_metro',
        ...     python_callable=output_data,
        ...     op_kwargs={'data_type': 'orders', 'client': 'metro'},
        ...     provide_context=True,
        ... )
    """
    # Construct composite key for multi-tenant support
    composite_key = f"{data_type}-{client}"
    
    logger.info(f"[{composite_key}] Preparing output data")
    
    # Get enrichment result from XCom
    ti = context['task_instance']
    enrichment_result = ti.xcom_pull(
        task_ids='enrich_data',
        key='enrichment_result'
    )
    
    if not enrichment_result:
        logger.warning(f"[{composite_key}] No enrichment result found in XCom")
        return {
            'output_records': [],
            'summary': {
                'total_records': 0,
                'execution_id': context['run_id'],
                'poll_timestamp': datetime.now(timezone.utc).isoformat(),
                'client': client
            }
        }
    
    enriched_records = enrichment_result.get('enriched_records', [])
    
    # Get execution_id from XCom (set in acquire_lock task)
    execution_id = ti.xcom_pull(
        task_ids='acquire_lock',
        key='execution_id'
    ) or context['run_id']
    
    # Generate poll timestamp
    poll_timestamp = datetime.now(timezone.utc).isoformat() + 'Z'
    
    # Add metadata to each record
    output_records = []
    for record in enriched_records:
        # Create a copy to avoid modifying original
        output_record = dict(record)
        
        # Add metadata including client
        output_record['_metadata'] = {
            'execution_id': execution_id,
            'poll_timestamp': poll_timestamp,
            'data_type': data_type,
            'client': client,
            'enrichment_complete': record.get('_enrichment_complete', True),
            's3_path': f"bronze/{client}/{data_type}/"
        }
        
        output_records.append(output_record)
    
    total_records = len(output_records)
    
    logger.info(
        f"[{composite_key}] Output prepared: {total_records} records processed "
        f"(execution_id: {execution_id})"
    )
    
    # Get validation and enrichment metrics for summary
    validation_result = ti.xcom_pull(
        task_ids='validate_data',
        key='validation_result'
    )
    
    polling_result = ti.xcom_pull(
        task_ids='poll_api',
        key='polling_result'
    )
    
    summary = {
        'total_records': total_records,
        'execution_id': execution_id,
        'poll_timestamp': poll_timestamp,
        'data_type': data_type,
        'client': client,
        's3_path': f"bronze/{client}/{data_type}/",
        'validation_metrics': validation_result.get('metrics', {}) if validation_result else {},
        'enrichment_stats': enrichment_result.get('enrichment_stats', {}),
        'last_modified': polling_result.get('last_modified') if polling_result else None
    }
    
    result = {
        'output_records': output_records,
        'summary': summary
    }
    
    # Push to XCom for release_lock task
    ti.xcom_push(key='output_result', value=result)
    
    return result


# ============================================================================
# Task 11.6: Write to S3 Bronze Layer
# ============================================================================

def write_to_s3_bronze(data_type: str, client: str, **context) -> Dict[str, Any]:
    """
    Write data to S3 Bronze layer in Parquet format with date partitioning.
    
    This function retrieves the output data from XCom and writes it to S3
    in Parquet format with Snappy compression. The data is partitioned by
    date (year/month/day) for efficient querying.
    
    Multi-tenant support: Data is written to separate paths per client:
    s3://{bucket}/bronze/{client}/{data_type}/year=YYYY/month=MM/day=DD/
    
    Requirements:
    - 9.1: Write to S3 in Parquet format with Snappy compression
    - 9.3: Partition by date (year/month/day)
    - 10.1: Use multi-tenant structure (bronze/{client}/{data_type}/)
    
    Args:
        data_type: Type of data being written
        client: Client identifier (metro, wongio, etc.)
        **context: Airflow context
    
    Returns:
        Dictionary with:
            - success: Boolean indicating write success
            - records_written: Number of records written
            - s3_path: Full S3 path where data was written
            - file_size_mb: Size of written file in MB
    
    Example:
        In DAG definition:
        >>> write_s3_task = PythonOperator(
        ...     task_id='write_to_s3_metro',
        ...     python_callable=write_to_s3_bronze,
        ...     op_kwargs={'data_type': 'orders', 'client': 'metro'},
        ...     provide_context=True,
        ... )
    """
    # Construct composite key for multi-tenant support
    composite_key = f"{data_type}-{client}"
    
    logger.info(f"[{composite_key}] Starting S3 write to Bronze layer")
    
    # Get output result from XCom
    ti = context['task_instance']
    output_result = ti.xcom_pull(
        task_ids='output_data',
        key='output_result'
    )
    
    if not output_result:
        logger.warning(f"[{composite_key}] No output result found in XCom")
        return {
            'success': True,
            'records_written': 0,
            'message': 'No data to write'
        }
    
    output_records = output_result.get('output_records', [])
    
    if not output_records:
        logger.info(f"[{composite_key}] No records to write to S3")
        return {
            'success': True,
            'records_written': 0,
            'message': 'No records to write'
        }
    
    # Get S3 configuration from environment or Airflow Variables
    s3_bucket = os.environ.get('S3_BRONZE_BUCKET')
  
    
    if not s3_bucket:
        raise ValueError(
            "S3_BRONZE_BUCKET must be set in environment or Airflow Variables"
        )
    
    # Initialize S3 writer
    s3_writer = S3Writer(
        bucket_name=s3_bucket,
        endpoint_url=None  # AWS real (no LocalStack)
    )
    
    try:
        # Write to S3 with current timestamp for partitioning
        write_result = s3_writer.write_to_bronze(
            data=output_records,
            client=client,
            data_type=data_type,
            partition_date=datetime.now(timezone.utc)
        )
        
        if write_result['success']:
            logger.info(
                f"[{composite_key}] Successfully wrote {write_result['records_written']} "
                f"records to {write_result['s3_path']} "
                f"({write_result['file_size_mb']:.2f} MB)"
            )
        else:
            logger.error(
                f"[{composite_key}] Failed to write to S3: "
                f"{write_result.get('error', 'Unknown error')}"
            )
        
        # Push result to XCom for release_lock task
        ti.xcom_push(key='s3_write_result', value=write_result)
        
        return write_result
        
    except Exception as e:
        logger.error(
            f"[{composite_key}] Unexpected error writing to S3: {str(e)}",
            exc_info=True
        )
        return {
            'success': False,
            'error': str(e),
            'records_written': 0
        }


# ============================================================================
# Task 11.7: Release DynamoDB Lock
# ============================================================================

def release_dynamodb_lock(data_type: str, client: str, **context) -> None:
    """
    Release lock in DynamoDB and update timestamps.
    
    This function always executes (trigger_rule='all_done') to ensure the lock
    is released even if upstream tasks fail. It determines execution success,
    updates the appropriate timestamps in DynamoDB, and emits CloudWatch metrics.
    
    Multi-tenant support: Uses composite key "{data_type}-{client}" for DynamoDB
    and includes client dimension in CloudWatch metrics.
    
    Requirements:
    - 3.5: Update last_successful_execution on success
    - 3.6: Release lock on success
    - 3.7: Release lock on failure but preserve timestamp
    
    Args:
        data_type: Type of data being polled
        client: Client identifier (metro, wongio, etc.)
        **context: Airflow context
    
    Returns:
        None
    
    Example:
        In DAG definition:
        >>> release_lock_task = PythonOperator(
        ...     task_id='release_lock_metro',
        ...     python_callable=release_dynamodb_lock,
        ...     op_kwargs={'data_type': 'orders', 'client': 'metro'},
        ...     provide_context=True,
        ...     trigger_rule='all_done',
        ... )
    """
    # Construct composite key for multi-tenant support
    composite_key = f"{data_type}-{client}"
    
    logger.info(f"[{composite_key}] Releasing lock")
    
    # Get DynamoDB configuration
    table_name = os.environ.get('DYNAMODB_TABLE_NAME', 'polling_control')
    endpoint_url = os.environ.get('LOCALSTACK_ENDPOINT')
    
    # Initialize StateManager
    state_manager = StateManager(
        table_name=table_name,
        endpoint_url=endpoint_url
    )
    
    # Determine if execution was successful
    # Check if all upstream tasks succeeded
    ti = context['task_instance']
    dag_run = context['dag_run']
    
    # Get task instances for upstream tasks
    upstream_task_ids = ['poll_api', 'validate_data', 'enrich_data', 'output_data']
    upstream_states = []
    
    for task_id in upstream_task_ids:
        task_instance = dag_run.get_task_instance(task_id)
        if task_instance:
            upstream_states.append(task_instance.state)
    
    # Execution is successful if all upstream tasks succeeded
    success = all(state == 'success' for state in upstream_states)
    
    # Get output result for last_modified and record count
    last_modified = None
    records_fetched = 0
    error_message = None
    
    if success:
        output_result = ti.xcom_pull(
            task_ids='output_data',
            key='output_result'
        )
        
        if output_result:
            summary = output_result.get('summary', {})
            last_modified = summary.get('last_modified')
            records_fetched = summary.get('total_records', 0)
            
            logger.info(
                f"[{composite_key}] Execution successful: "
                f"{records_fetched} records processed"
            )
            if last_modified:
                logger.info(
                    f"[{composite_key}] Updating last_modified_date to {last_modified}"
                )
    else:
        # Execution failed - determine error message
        failed_tasks = [
            task_id for task_id, state in zip(upstream_task_ids, upstream_states)
            if state != 'success'
        ]
        error_message = f"Tasks failed: {', '.join(failed_tasks)}"
        logger.error(
            f"[{composite_key}] Execution failed: {error_message}"
        )
    
    # Release lock with appropriate parameters using composite key
    try:
        state_manager.release_lock(
            data_type=composite_key,
            success=success,
            last_modified=last_modified,
            records_fetched=records_fetched,
            error_message=error_message
        )
        
        logger.info(
            f"[{composite_key}] Lock released successfully "
            f"(success={success})"
        )
        
    except Exception as e:
        logger.error(
            f"[{composite_key}] Error releasing lock: {e}",
            exc_info=True
        )
        # Don't raise - we want to ensure the task completes
        # even if lock release fails
    
    
    # This would require boto3 cloudwatch client
    # For now, just log the metrics
    logger.info(
        f"[{composite_key}] Metrics: "
        f"success={success}, "
        f"records_fetched={records_fetched}, "
        f"client={client}"
    )
