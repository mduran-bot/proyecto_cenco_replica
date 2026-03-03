# Incremental Polling Module

## Overview

The `incremental_polling` module provides functions for implementing incremental data polling from APIs. It enables efficient data synchronization by fetching only new or modified records since the last successful execution, with built-in deduplication to handle overlap windows.

## Features

- **Incremental Filtering**: Build API filters based on last execution timestamp
- **Overlap Window**: 1-minute overlap to ensure no records are missed
- **Deduplication**: Remove duplicate records based on ID and modification timestamp
- **First Execution Handling**: Automatic full refresh when no previous state exists
- **Error Resilience**: Graceful fallback to full refresh on errors

## Functions

### `build_incremental_filter(state_manager, data_type)`

Constructs an incremental filter for API queries based on the last successful execution.

**Parameters:**
- `state_manager` (StateManager): Instance to query DynamoDB for last execution state
- `data_type` (str): Type of data being polled (e.g., "orders", "products")

**Returns:**
- `Dict`: Filter dictionary with the following structure:
  ```python
  {
      'dateModified': '2024-01-15T10:24:00Z',  # Last modified - 1 minute
      'sortBy': 'dateModified',
      'sortOrder': 'asc'
  }
  ```
  Returns empty dict `{}` for first execution (full refresh)

**Requirements Satisfied:**
- 4.1: Use dateModified filter with last_successful_execution
- 4.2: Subtract 1 minute for overlap window
- 4.3: Handle first execution (full refresh)

**Example:**
```python
from src.state_manager import StateManager
from src.incremental_polling import build_incremental_filter

state_mgr = StateManager("polling_control")
filters = build_incremental_filter(state_mgr, "orders")

# First execution: {}
# Subsequent executions: {'dateModified': '...', 'sortBy': 'dateModified', 'sortOrder': 'asc'}
```

### `deduplicate_records(records)`

Removes duplicate records, keeping only the most recent version of each unique ID.

**Parameters:**
- `records` (List[Dict]): List of records from API with 'id' and 'dateModified' fields

**Returns:**
- `List[Dict]`: Deduplicated list with only the most recent version of each ID

**Requirements Satisfied:**
- 4.4: Deduplicate records based on ID and modification timestamp

**Example:**
```python
from src.incremental_polling import deduplicate_records

records = [
    {'id': '123', 'dateModified': '2024-01-15T10:25:00Z', 'status': 'pending'},
    {'id': '123', 'dateModified': '2024-01-15T10:26:00Z', 'status': 'completed'},
    {'id': '456', 'dateModified': '2024-01-15T10:25:00Z', 'status': 'pending'}
]

deduplicated = deduplicate_records(records)
# Result: 2 records (ID 123 with most recent timestamp, ID 456)
```

## Complete Workflow Example

```python
from src.state_manager import StateManager
from src.api_client import JanisAPIClient
from src.pagination_handler import PaginationHandler
from src.incremental_polling import build_incremental_filter, deduplicate_records

# Initialize components
state_mgr = StateManager("polling_control")
api_client = JanisAPIClient("https://api.janis.in", "api-key")
pagination = PaginationHandler(api_client)

# Step 1: Build incremental filter
filters = build_incremental_filter(state_mgr, "orders")

# Step 2: Fetch data with pagination
all_records = pagination.fetch_all_pages("orders", filters)

# Step 3: Deduplicate records from overlap window
unique_records = deduplicate_records(all_records)

print(f"Fetched: {len(all_records)}, Unique: {len(unique_records)}")
```

## Overlap Window Strategy

The incremental polling uses a 1-minute overlap window to ensure data consistency:

1. **Last Execution**: 10:25:00
2. **Overlap Applied**: 10:24:00 (subtract 1 minute)
3. **Filter**: `dateModified >= 10:24:00`
4. **Result**: Fetches records from 10:24:00 onwards
5. **Deduplication**: Removes duplicates from the overlap period

This strategy ensures that:
- No records are missed due to timing issues
- Records modified during the last execution are captured
- Duplicates from the overlap are automatically removed

## Error Handling

The module handles various error scenarios gracefully:

### Invalid Timestamp Format
```python
# If last_modified_date has invalid format
# Returns: {} (full refresh)
```

### Missing State
```python
# If no previous execution exists
# Returns: {} (full refresh)
```

### DynamoDB Errors
```python
# If StateManager throws exception
# Returns: {} (full refresh)
```

### Records Without ID
```python
# Records without 'id' field are skipped during deduplication
# Logged as warning
```

### Records Without dateModified
```python
# Records without 'dateModified' are kept but can't be compared
# First occurrence is kept
```

## Testing

The module includes comprehensive unit tests:

```bash
# Run tests
cd max/polling
python -m pytest tests/test_incremental_polling.py -v

# Run with coverage
python -m pytest tests/test_incremental_polling.py --cov=src.incremental_polling --cov-report=term
```

### Test Coverage

- ✅ First execution (no previous state)
- ✅ Incremental filter with overlap window
- ✅ Invalid timestamp format handling
- ✅ Exception handling in StateManager
- ✅ Empty list deduplication
- ✅ No duplicates scenario
- ✅ Simple duplicates (keep most recent)
- ✅ Multiple duplicates of same ID
- ✅ Records without ID
- ✅ Records without dateModified
- ✅ Same timestamp handling

## Integration with Other Components

### StateManager Integration
```python
# StateManager provides last_modified_date
state_mgr.get_last_modified_date("orders")  # Returns ISO timestamp or None
```

### API Client Integration
```python
# Filters are passed to API client
api_client.get("orders", params=filters)
```

### Pagination Handler Integration
```python
# Filters are passed through pagination
pagination.fetch_all_pages("orders", filters)
```

## Performance Considerations

### Memory Usage
- Deduplication uses a dictionary to track unique IDs
- Memory usage: O(n) where n is number of unique records
- For large datasets (>100k records), consider batch processing

### Time Complexity
- `build_incremental_filter`: O(1) - single DynamoDB query
- `deduplicate_records`: O(n) - single pass through records

### Optimization Tips
1. Use appropriate page size (100 records recommended)
2. Implement circuit breaker to prevent infinite pagination
3. Monitor overlap window size vs duplicate rate
4. Consider adjusting overlap window based on API update frequency

## Logging

The module uses Python's standard logging:

```python
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)

# Log levels used:
# - INFO: Normal operations, filter creation, deduplication summary
# - DEBUG: Detailed deduplication decisions
# - WARNING: Records without ID or dateModified
# - ERROR: Exceptions, invalid timestamps
```

## Requirements Mapping

| Requirement | Function | Description |
|-------------|----------|-------------|
| 4.1 | `build_incremental_filter` | Use dateModified filter with last_successful_execution |
| 4.2 | `build_incremental_filter` | Subtract 1 minute for overlap window |
| 4.3 | `build_incremental_filter` | Handle first execution (full refresh) |
| 4.4 | `deduplicate_records` | Deduplicate based on ID and timestamp |

## See Also

- [StateManager README](state_manager_README.md) - DynamoDB state management
- [API Client README](api_client_README.md) - HTTP client with rate limiting
- [Pagination Handler README](pagination_handler_README.md) - Pagination with circuit breaker
- [Examples](../examples/incremental_polling_usage.py) - Complete usage examples
