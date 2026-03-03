"""
Integration tests for incremental polling workflow.

Tests the complete workflow of incremental polling including:
- StateManager integration
- Filter building
- Deduplication
"""

import pytest
from unittest.mock import Mock, MagicMock
from datetime import datetime, timedelta
from src.incremental_polling import build_incremental_filter, deduplicate_records


class TestIncrementalPollingIntegration:
    """Integration tests for complete incremental polling workflow."""
    
    def test_complete_incremental_polling_workflow(self):
        """
        Test complete workflow: build filter -> fetch data -> deduplicate.
        
        This simulates a real polling scenario with:
        1. Previous execution state in DynamoDB
        2. API returning data with overlap
        3. Deduplication of overlapping records
        """
        # Setup: Mock StateManager with previous execution
        state_manager = Mock()
        last_modified = "2024-01-15T10:25:00Z"
        state_manager.get_last_modified_date.return_value = last_modified
        
        # Step 1: Build incremental filter
        filters = build_incremental_filter(state_manager, "orders")
        
        # Verify filter was built correctly
        assert filters['sortBy'] == 'dateModified'
        assert filters['sortOrder'] == 'asc'
        
        # Verify 1-minute overlap was applied
        expected_dt = datetime.fromisoformat(last_modified.replace('Z', '+00:00')) - timedelta(minutes=1)
        expected_iso = expected_dt.isoformat().replace('+00:00', 'Z')
        assert filters['dateModified'] == expected_iso
        
        # Step 2: Simulate API response with overlapping records
        # These records would come from pagination_handler.fetch_all_pages()
        api_records = [
            # Records from overlap window (will have duplicates)
            {'id': '123', 'dateModified': '2024-01-15T10:24:30Z', 'status': 'pending'},
            {'id': '123', 'dateModified': '2024-01-15T10:25:30Z', 'status': 'completed'},
            {'id': '456', 'dateModified': '2024-01-15T10:24:45Z', 'status': 'pending'},
            # New records after last execution
            {'id': '789', 'dateModified': '2024-01-15T10:26:00Z', 'status': 'processing'},
            {'id': '101', 'dateModified': '2024-01-15T10:27:00Z', 'status': 'pending'}
        ]
        
        # Step 3: Deduplicate records
        unique_records = deduplicate_records(api_records)
        
        # Verify deduplication worked correctly
        assert len(unique_records) == 4  # 5 records -> 4 unique (ID 123 deduplicated)
        
        # Verify ID 123 kept the most recent version
        record_123 = next(r for r in unique_records if r['id'] == '123')
        assert record_123['dateModified'] == '2024-01-15T10:25:30Z'
        assert record_123['status'] == 'completed'
        
        # Verify all other records are present
        record_ids = {r['id'] for r in unique_records}
        assert record_ids == {'123', '456', '789', '101'}
    
    def test_first_execution_workflow(self):
        """
        Test workflow for first execution (no previous state).
        
        Should perform full refresh without filters.
        """
        # Setup: Mock StateManager with no previous state
        state_manager = Mock()
        state_manager.get_last_modified_date.return_value = None
        
        # Step 1: Build filter (should be empty for full refresh)
        filters = build_incremental_filter(state_manager, "products")
        
        # Verify empty filter (full refresh)
        assert filters == {}
        
        # Step 2: Simulate API response (full dataset)
        api_records = [
            {'id': '001', 'dateModified': '2024-01-01T00:00:00Z', 'name': 'Product 1'},
            {'id': '002', 'dateModified': '2024-01-02T00:00:00Z', 'name': 'Product 2'},
            {'id': '003', 'dateModified': '2024-01-03T00:00:00Z', 'name': 'Product 3'}
        ]
        
        # Step 3: Deduplicate (should have no duplicates in full refresh)
        unique_records = deduplicate_records(api_records)
        
        # Verify all records kept (no duplicates)
        assert len(unique_records) == 3
        assert all(r in unique_records for r in api_records)
    
    def test_error_recovery_workflow(self):
        """
        Test workflow when StateManager fails.
        
        Should fallback to full refresh gracefully.
        """
        # Setup: Mock StateManager that throws exception
        state_manager = Mock()
        state_manager.get_last_modified_date.side_effect = Exception("DynamoDB connection error")
        
        # Step 1: Build filter (should fallback to empty filter)
        filters = build_incremental_filter(state_manager, "stock")
        
        # Verify fallback to full refresh
        assert filters == {}
        
        # Step 2: Continue with full refresh
        api_records = [
            {'id': 'SKU-001', 'dateModified': '2024-01-15T10:00:00Z', 'quantity': 100},
            {'id': 'SKU-002', 'dateModified': '2024-01-15T10:00:00Z', 'quantity': 50}
        ]
        
        # Step 3: Deduplicate
        unique_records = deduplicate_records(api_records)
        
        # Verify workflow completed successfully despite error
        assert len(unique_records) == 2
    
    def test_high_duplicate_rate_scenario(self):
        """
        Test scenario with high duplicate rate (large overlap window).
        
        Simulates a case where many records were modified during overlap period.
        """
        # Setup: Mock StateManager
        state_manager = Mock()
        state_manager.get_last_modified_date.return_value = "2024-01-15T10:25:00Z"
        
        # Step 1: Build filter
        filters = build_incremental_filter(state_manager, "orders")
        
        # Step 2: Simulate API response with many duplicates
        api_records = []
        
        # Add 10 records, each with 3 versions (30 total records)
        for i in range(10):
            record_id = f"order-{i:03d}"
            # Old version (from overlap)
            api_records.append({
                'id': record_id,
                'dateModified': '2024-01-15T10:24:00Z',
                'status': 'pending'
            })
            # Middle version
            api_records.append({
                'id': record_id,
                'dateModified': '2024-01-15T10:25:00Z',
                'status': 'processing'
            })
            # Latest version
            api_records.append({
                'id': record_id,
                'dateModified': '2024-01-15T10:26:00Z',
                'status': 'completed'
            })
        
        # Step 3: Deduplicate
        unique_records = deduplicate_records(api_records)
        
        # Verify deduplication efficiency
        assert len(api_records) == 30  # Original count
        assert len(unique_records) == 10  # Deduplicated count
        
        # Verify all kept records have latest status
        for record in unique_records:
            assert record['status'] == 'completed'
            assert record['dateModified'] == '2024-01-15T10:26:00Z'
    
    def test_mixed_data_quality_scenario(self):
        """
        Test scenario with mixed data quality (missing fields).
        
        Simulates real-world scenario where some records have missing data.
        """
        # Setup
        state_manager = Mock()
        state_manager.get_last_modified_date.return_value = "2024-01-15T10:25:00Z"
        
        # Step 1: Build filter
        filters = build_incremental_filter(state_manager, "prices")
        
        # Step 2: Simulate API response with data quality issues
        api_records = [
            # Good record
            {'id': 'price-001', 'dateModified': '2024-01-15T10:26:00Z', 'amount': 100},
            # Duplicate with missing dateModified
            {'id': 'price-001', 'amount': 150},
            # Record without ID (will be skipped)
            {'dateModified': '2024-01-15T10:26:00Z', 'amount': 200},
            # Good record
            {'id': 'price-002', 'dateModified': '2024-01-15T10:27:00Z', 'amount': 300}
        ]
        
        # Step 3: Deduplicate (should handle gracefully)
        unique_records = deduplicate_records(api_records)
        
        # Verify handling of data quality issues
        assert len(unique_records) == 2  # Only records with IDs
        
        # Verify IDs present
        record_ids = {r['id'] for r in unique_records}
        assert record_ids == {'price-001', 'price-002'}


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
