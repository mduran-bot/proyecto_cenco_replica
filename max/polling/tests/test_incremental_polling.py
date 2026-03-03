"""
Unit tests for incremental polling logic.

Tests the build_incremental_filter and deduplicate_records functions
to ensure correct behavior for incremental polling operations.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock
from src.incremental_polling import build_incremental_filter, deduplicate_records


class TestBuildIncrementalFilter:
    """Tests for build_incremental_filter function."""
    
    def test_first_execution_no_previous_state(self):
        """
        Test that first execution returns empty filter for full refresh.
        
        Requirement 4.3: Handle first execution (full refresh)
        """
        # Mock StateManager que retorna None (no hay estado previo)
        state_manager = Mock()
        state_manager.get_last_modified_date.return_value = None
        
        # Ejecutar función
        result = build_incremental_filter(state_manager, "orders")
        
        # Verificar que retorna filtro vacío
        assert result == {}
        state_manager.get_last_modified_date.assert_called_once_with("orders")
    
    def test_incremental_filter_with_previous_state(self):
        """
        Test that incremental filter is built correctly with overlap window.
        
        Requirements:
        - 4.1: Use dateModified filter with last_successful_execution
        - 4.2: Subtract 1 minute for overlap window
        """
        # Mock StateManager con timestamp previo
        state_manager = Mock()
        last_modified = "2024-01-15T10:25:00Z"
        state_manager.get_last_modified_date.return_value = last_modified
        
        # Ejecutar función
        result = build_incremental_filter(state_manager, "orders")
        
        # Verificar estructura del filtro
        assert 'dateModified' in result
        assert 'sortBy' in result
        assert 'sortOrder' in result
        
        # Verificar valores
        assert result['sortBy'] == 'dateModified'
        assert result['sortOrder'] == 'asc'
        
        # Verificar que se restó 1 minuto (ventana de solapamiento)
        expected_dt = datetime.fromisoformat(last_modified.replace('Z', '+00:00')) - timedelta(minutes=1)
        expected_iso = expected_dt.isoformat().replace('+00:00', 'Z')
        assert result['dateModified'] == expected_iso
    
    def test_invalid_timestamp_format_returns_empty_filter(self):
        """
        Test that invalid timestamp format triggers full refresh.
        
        Requirement 4.3: Handle errors gracefully with full refresh
        """
        # Mock StateManager con timestamp inválido
        state_manager = Mock()
        state_manager.get_last_modified_date.return_value = "invalid-timestamp"
        
        # Ejecutar función
        result = build_incremental_filter(state_manager, "orders")
        
        # Verificar que retorna filtro vacío (full refresh)
        assert result == {}
    
    def test_exception_in_state_manager_returns_empty_filter(self):
        """
        Test that exceptions in StateManager trigger full refresh.
        
        Requirement 4.3: Handle errors gracefully
        """
        # Mock StateManager que lanza excepción
        state_manager = Mock()
        state_manager.get_last_modified_date.side_effect = Exception("DynamoDB error")
        
        # Ejecutar función
        result = build_incremental_filter(state_manager, "orders")
        
        # Verificar que retorna filtro vacío (full refresh)
        assert result == {}


class TestDeduplicateRecords:
    """Tests for deduplicate_records function."""
    
    def test_empty_list_returns_empty(self):
        """Test that empty list returns empty list."""
        result = deduplicate_records([])
        assert result == []
    
    def test_no_duplicates_returns_all_records(self):
        """Test that records with unique IDs are all returned."""
        records = [
            {'id': '123', 'dateModified': '2024-01-15T10:25:00Z', 'status': 'pending'},
            {'id': '456', 'dateModified': '2024-01-15T10:26:00Z', 'status': 'completed'},
            {'id': '789', 'dateModified': '2024-01-15T10:27:00Z', 'status': 'pending'}
        ]
        
        result = deduplicate_records(records)
        
        assert len(result) == 3
        assert all(r in result for r in records)
    
    def test_duplicates_keeps_most_recent(self):
        """
        Test that duplicate IDs keep only the most recent record.
        
        Requirement 4.4: Deduplicate records based on ID and modification timestamp
        """
        records = [
            {'id': '123', 'dateModified': '2024-01-15T10:25:00Z', 'status': 'pending'},
            {'id': '123', 'dateModified': '2024-01-15T10:26:00Z', 'status': 'completed'},
            {'id': '456', 'dateModified': '2024-01-15T10:25:00Z', 'status': 'pending'}
        ]
        
        result = deduplicate_records(records)
        
        # Debe haber solo 2 registros únicos
        assert len(result) == 2
        
        # Verificar que se mantuvo el registro más reciente de ID 123
        record_123 = next(r for r in result if r['id'] == '123')
        assert record_123['dateModified'] == '2024-01-15T10:26:00Z'
        assert record_123['status'] == 'completed'
        
        # Verificar que se mantuvo el registro de ID 456
        record_456 = next(r for r in result if r['id'] == '456')
        assert record_456['dateModified'] == '2024-01-15T10:25:00Z'
    
    def test_multiple_duplicates_keeps_most_recent(self):
        """Test that multiple duplicates of same ID keep only the most recent."""
        records = [
            {'id': '123', 'dateModified': '2024-01-15T10:25:00Z', 'status': 'pending'},
            {'id': '123', 'dateModified': '2024-01-15T10:26:00Z', 'status': 'processing'},
            {'id': '123', 'dateModified': '2024-01-15T10:27:00Z', 'status': 'completed'},
            {'id': '123', 'dateModified': '2024-01-15T10:24:00Z', 'status': 'created'}
        ]
        
        result = deduplicate_records(records)
        
        # Debe haber solo 1 registro
        assert len(result) == 1
        
        # Verificar que se mantuvo el más reciente
        assert result[0]['dateModified'] == '2024-01-15T10:27:00Z'
        assert result[0]['status'] == 'completed'
    
    def test_records_without_id_are_skipped(self):
        """Test that records without ID are skipped during deduplication."""
        records = [
            {'id': '123', 'dateModified': '2024-01-15T10:25:00Z', 'status': 'pending'},
            {'dateModified': '2024-01-15T10:26:00Z', 'status': 'no-id'},  # Sin ID
            {'id': '456', 'dateModified': '2024-01-15T10:27:00Z', 'status': 'completed'}
        ]
        
        result = deduplicate_records(records)
        
        # Solo deben estar los registros con ID
        assert len(result) == 2
        assert all(r.get('id') in ['123', '456'] for r in result)
    
    def test_records_without_dateModified_handled_gracefully(self):
        """Test that records without dateModified are handled gracefully."""
        records = [
            {'id': '123', 'dateModified': '2024-01-15T10:25:00Z', 'status': 'pending'},
            {'id': '123', 'status': 'no-timestamp'},  # Sin dateModified
            {'id': '456', 'dateModified': '2024-01-15T10:27:00Z', 'status': 'completed'}
        ]
        
        result = deduplicate_records(records)
        
        # Debe haber 2 registros únicos
        assert len(result) == 2
        
        # El registro 123 debe existir (uno de los dos)
        record_123 = next(r for r in result if r['id'] == '123')
        assert record_123 is not None
    
    def test_same_timestamp_keeps_one_record(self):
        """Test that records with same ID and timestamp keep one record."""
        records = [
            {'id': '123', 'dateModified': '2024-01-15T10:25:00Z', 'status': 'pending'},
            {'id': '123', 'dateModified': '2024-01-15T10:25:00Z', 'status': 'pending'}
        ]
        
        result = deduplicate_records(records)
        
        # Debe haber solo 1 registro
        assert len(result) == 1
        assert result[0]['id'] == '123'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
