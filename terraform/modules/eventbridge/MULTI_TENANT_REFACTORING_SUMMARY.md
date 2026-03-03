# EventBridge Multi-Tenant Refactoring Summary

## Overview

This document summarizes the changes made to the EventBridge module to support multi-tenant API polling with specific endpoints for Metro and Wongio clients.

## Changes Made

### 1. Updated EventBridge Rules (main.tf)

All 5 EventBridge rules have been updated to pass multi-tenant configuration:

#### Orders Rule
- **Schedule**: Every 5 minutes
- **DAG**: `poll_orders`
- **Configuration**:
  ```json
  {
    "clients": ["metro", "wongio"],
    "endpoint": "/order",
    "base_url": "https://oms.janis.in/api"
  }
  ```

#### Catalog Rule (formerly Products)
- **Schedule**: Every 1 hour
- **DAG**: `poll_catalog`
- **Configuration**:
  ```json
  {
    "clients": ["metro", "wongio"],
    "endpoints": ["/product", "/sku", "/category", "/brand"],
    "base_url": "https://catalog.janis.in/api"
  }
  ```
- **Note**: Handles 4 endpoints × 2 clients = 8 API calls per execution

#### Stock Rule
- **Schedule**: Every 10 minutes
- **DAG**: `poll_stock`
- **Configuration**:
  ```json
  {
    "clients": ["metro", "wongio"],
    "endpoint": "/sku-stock",
    "base_url": "https://wms.janis.in/api"
  }
  ```

#### Prices Rule
- **Schedule**: Every 30 minutes
- **DAG**: `poll_prices`
- **Configuration**:
  ```json
  {
    "clients": ["metro", "wongio"],
    "endpoints": ["/price", "/price-sheet", "/base-price"],
    "base_url": "https://vtex.pricing.janis.in/api"
  }
  ```
- **Note**: Handles 3 endpoints × 2 clients = 6 API calls per execution

#### Stores Rule
- **Schedule**: Every 1 day
- **DAG**: `poll_stores`
- **Configuration**:
  ```json
  {
    "clients": ["metro", "wongio"],
    "endpoint": "/location",
    "base_url": "https://commerce.janis.in/api"
  }
  ```

### 2. Updated Variables (variables.tf)

- Renamed `product_polling_rate` to `catalog_polling_rate` to reflect the broader scope
- All other variables remain unchanged

### 3. Updated Outputs (outputs.tf)

- Changed `products` key to `catalog` in `rule_arns` output
- Updated `rule_names` to reference `poll_catalog` instead of `poll_products`

### 4. IAM Role Verification

The existing IAM role configuration is correct and includes:
- Trust policy allowing `events.amazonaws.com` to assume the role
- Policy with `airflow:CreateCliToken` permission for MWAA invocation
- Permission to send messages to DLQ

## Multi-Tenant Architecture

### Key Changes from Single-Tenant

**Before (Single-Tenant)**:
```json
{
  "dag_id": "poll_orders",
  "conf": {
    "data_type": "orders"
  }
}
```

**After (Multi-Tenant)**:
```json
{
  "dag_id": "poll_orders",
  "conf": {
    "clients": ["metro", "wongio"],
    "endpoint": "/order",
    "base_url": "https://oms.janis.in/api"
  }
}
```

### Total API Calls Per Cycle

When all 5 DAGs execute once:
- Orders: 1 endpoint × 2 clients = 2 calls
- Catalog: 4 endpoints × 2 clients = 8 calls
- Stock: 1 endpoint × 2 clients = 2 calls
- Prices: 3 endpoints × 2 clients = 6 calls
- Stores: 1 endpoint × 2 clients = 2 calls

**Total: 20 API calls per complete cycle**

## Downstream Impact

The DAGs must be updated to handle the new configuration format:
1. Accept `clients`, `endpoint`/`endpoints`, and `base_url` parameters
2. Iterate over clients to create separate tasks
3. Use client-specific DynamoDB keys: `{data_type}-{client}`
4. Store data in client-specific S3 paths: `bronze/{client}/{data_type}/`
5. Include `janis-client` header in API requests

## Testing Recommendations

1. Validate Terraform configuration with `terraform validate`
2. Test with LocalStack before deploying to AWS
3. Verify EventBridge rules are created with correct schedules
4. Confirm IAM role has necessary permissions
5. Test DAG execution with multi-tenant configuration

## Deployment Notes

- No breaking changes to existing infrastructure
- Rules will be disabled if `mwaa_environment_arn` is empty
- Dead letter queue and retry policies remain unchanged
- CloudWatch alarms continue to monitor rule invocations

## Related Tasks

- Task 10: DAG refactoring for multi-tenant support
- Task 11: Task function refactoring for multi-tenant support
- Task 13.5: Documentation updates

## Date Completed

February 24, 2026
