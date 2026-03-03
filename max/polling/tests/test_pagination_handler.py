"""
Tests unitarios para PaginationHandler.

Valida el comportamiento de paginación, circuit breaker y manejo de errores.
"""

import pytest
from unittest.mock import Mock, MagicMock
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from pagination_handler import PaginationHandler, CircuitBreakerException


class TestPaginationHandlerInitialization:
    """Tests de inicialización del PaginationHandler."""
    
    def test_initialization_with_defaults(self):
        """Test: Inicialización con valores por defecto."""
        client = Mock()
        handler = PaginationHandler(client)
        
        assert handler.client == client
        assert handler.max_pages == 1000
        assert handler.page_size == 100
        assert handler.last_page_fetched == 0
    
    def test_initialization_with_custom_values(self):
        """Test: Inicialización con valores personalizados."""
        client = Mock()
        handler = PaginationHandler(client, max_pages=500, page_size=50)
        
        assert handler.max_pages == 500
        assert handler.page_size == 50
    
    def test_initialization_with_invalid_max_pages(self):
        """Test: Inicialización con max_pages inválido debe lanzar ValueError."""
        client = Mock()
        
        with pytest.raises(ValueError, match="max_pages debe ser mayor que 0"):
            PaginationHandler(client, max_pages=0)
        
        with pytest.raises(ValueError, match="max_pages debe ser mayor que 0"):
            PaginationHandler(client, max_pages=-1)
    
    def test_initialization_with_invalid_page_size(self):
        """Test: Inicialización con page_size inválido debe lanzar ValueError."""
        client = Mock()
        
        with pytest.raises(ValueError, match="page_size debe ser mayor que 0"):
            PaginationHandler(client, page_size=0)
        
        with pytest.raises(ValueError, match="page_size debe ser mayor que 0"):
            PaginationHandler(client, page_size=-1)


class TestFetchAllPages:
    """Tests del método fetch_all_pages."""
    
    def test_fetch_single_page(self):
        """Test: Obtener una sola página de resultados."""
        # Setup
        client = Mock()
        client.get.return_value = {
            'data': [{'id': '1'}, {'id': '2'}],
            'pagination': {'hasNextPage': False}
        }
        
        handler = PaginationHandler(client)
        
        # Act
        results = handler.fetch_all_pages('orders')
        
        # Assert
        assert len(results) == 2
        assert results[0]['id'] == '1'
        assert results[1]['id'] == '2'
        assert handler.last_page_fetched == 1
        
        # Verificar que se llamó con los parámetros correctos
        client.get.assert_called_once_with('orders', params={'pageSize': 100, 'page': 1})
    
    def test_fetch_multiple_pages(self):
        """Test: Obtener múltiples páginas de resultados."""
        # Setup
        client = Mock()
        
        # Simular 3 páginas de resultados
        client.get.side_effect = [
            {
                'data': [{'id': '1'}, {'id': '2'}],
                'pagination': {'hasNextPage': True}
            },
            {
                'data': [{'id': '3'}, {'id': '4'}],
                'pagination': {'hasNextPage': True}
            },
            {
                'data': [{'id': '5'}],
                'pagination': {'hasNextPage': False}
            }
        ]
        
        handler = PaginationHandler(client)
        
        # Act
        results = handler.fetch_all_pages('products')
        
        # Assert
        assert len(results) == 5
        assert handler.last_page_fetched == 3
        assert client.get.call_count == 3
    
    def test_fetch_with_filters(self):
        """Test: Obtener páginas con filtros adicionales."""
        # Setup
        client = Mock()
        client.get.return_value = {
            'data': [{'id': '1'}],
            'pagination': {'hasNextPage': False}
        }
        
        handler = PaginationHandler(client)
        filters = {
            'dateModified': '2024-01-01T00:00:00Z',
            'sortBy': 'dateModified',
            'sortOrder': 'asc'
        }
        
        # Act
        results = handler.fetch_all_pages('orders', filters)
        
        # Assert
        expected_params = {
            'dateModified': '2024-01-01T00:00:00Z',
            'sortBy': 'dateModified',
            'sortOrder': 'asc',
            'pageSize': 100,
            'page': 1
        }
        client.get.assert_called_once_with('orders', params=expected_params)
    
    def test_fetch_empty_response(self):
        """Test: Respuesta vacía debe terminar paginación."""
        # Setup
        client = Mock()
        client.get.return_value = {
            'data': [],
            'pagination': {'hasNextPage': True}
        }
        
        handler = PaginationHandler(client)
        
        # Act
        results = handler.fetch_all_pages('orders')
        
        # Assert
        assert len(results) == 0
        assert handler.last_page_fetched == 0
        assert client.get.call_count == 1
    
    def test_fetch_no_pagination_info(self):
        """Test: Respuesta sin información de paginación debe terminar."""
        # Setup
        client = Mock()
        client.get.return_value = {
            'data': [{'id': '1'}]
            # No 'pagination' key
        }
        
        handler = PaginationHandler(client)
        
        # Act
        results = handler.fetch_all_pages('orders')
        
        # Assert
        assert len(results) == 1
        assert handler.last_page_fetched == 1


class TestCircuitBreaker:
    """Tests del circuit breaker."""
    
    def test_circuit_breaker_activation(self):
        """Test: Circuit breaker debe activarse al exceder max_pages."""
        # Setup
        client = Mock()
        
        # Simular respuestas infinitas con hasNextPage=True
        client.get.return_value = {
            'data': [{'id': '1'}],
            'pagination': {'hasNextPage': True}
        }
        
        handler = PaginationHandler(client, max_pages=5)
        
        # Act & Assert
        with pytest.raises(CircuitBreakerException) as exc_info:
            handler.fetch_all_pages('orders')
        
        # Verificar mensaje de error
        assert "Circuit breaker activado" in str(exc_info.value)
        assert "5 páginas" in str(exc_info.value)
        assert handler.last_page_fetched == 5
        
        # Verificar que se llamó exactamente max_pages veces
        assert client.get.call_count == 5
    
    def test_circuit_breaker_with_custom_limit(self):
        """Test: Circuit breaker con límite personalizado."""
        # Setup
        client = Mock()
        client.get.return_value = {
            'data': [{'id': '1'}],
            'pagination': {'hasNextPage': True}
        }
        
        handler = PaginationHandler(client, max_pages=3)
        
        # Act & Assert
        with pytest.raises(CircuitBreakerException):
            handler.fetch_all_pages('products')
        
        assert handler.last_page_fetched == 3
        assert client.get.call_count == 3
    
    def test_no_circuit_breaker_when_within_limit(self):
        """Test: No activar circuit breaker cuando está dentro del límite."""
        # Setup
        client = Mock()
        
        # Simular 3 páginas, luego terminar
        client.get.side_effect = [
            {'data': [{'id': '1'}], 'pagination': {'hasNextPage': True}},
            {'data': [{'id': '2'}], 'pagination': {'hasNextPage': True}},
            {'data': [{'id': '3'}], 'pagination': {'hasNextPage': False}}
        ]
        
        handler = PaginationHandler(client, max_pages=10)
        
        # Act
        results = handler.fetch_all_pages('orders')
        
        # Assert - No debe lanzar excepción
        assert len(results) == 3
        assert handler.last_page_fetched == 3


class TestPageSizeConfiguration:
    """Tests de configuración de tamaño de página."""
    
    def test_default_page_size(self):
        """Test: Tamaño de página por defecto debe ser 100."""
        # Setup
        client = Mock()
        client.get.return_value = {
            'data': [{'id': '1'}],
            'pagination': {'hasNextPage': False}
        }
        
        handler = PaginationHandler(client)
        
        # Act
        handler.fetch_all_pages('orders')
        
        # Assert
        call_args = client.get.call_args
        assert call_args[1]['params']['pageSize'] == 100
    
    def test_custom_page_size(self):
        """Test: Tamaño de página personalizado."""
        # Setup
        client = Mock()
        client.get.return_value = {
            'data': [{'id': '1'}],
            'pagination': {'hasNextPage': False}
        }
        
        handler = PaginationHandler(client, page_size=50)
        
        # Act
        handler.fetch_all_pages('products')
        
        # Assert
        call_args = client.get.call_args
        assert call_args[1]['params']['pageSize'] == 50


class TestReset:
    """Tests del método reset."""
    
    def test_reset_last_page_fetched(self):
        """Test: Reset debe reiniciar el contador de última página."""
        # Setup
        client = Mock()
        client.get.return_value = {
            'data': [{'id': '1'}],
            'pagination': {'hasNextPage': False}
        }
        
        handler = PaginationHandler(client)
        
        # Act
        handler.fetch_all_pages('orders')
        assert handler.last_page_fetched == 1
        
        handler.reset()
        
        # Assert
        assert handler.last_page_fetched == 0
    
    def test_reset_allows_reuse(self):
        """Test: Reset permite reutilizar el handler."""
        # Setup
        client = Mock()
        client.get.return_value = {
            'data': [{'id': '1'}],
            'pagination': {'hasNextPage': False}
        }
        
        handler = PaginationHandler(client)
        
        # Primera paginación
        handler.fetch_all_pages('orders')
        assert handler.last_page_fetched == 1
        
        # Reset y segunda paginación
        handler.reset()
        handler.fetch_all_pages('products')
        
        # Assert
        assert handler.last_page_fetched == 1
        assert client.get.call_count == 2


class TestEdgeCases:
    """Tests de casos edge."""
    
    def test_response_without_data_key(self):
        """Test: Respuesta sin clave 'data' debe tratarse como vacía."""
        # Setup
        client = Mock()
        client.get.return_value = {
            'pagination': {'hasNextPage': False}
            # No 'data' key
        }
        
        handler = PaginationHandler(client)
        
        # Act
        results = handler.fetch_all_pages('orders')
        
        # Assert
        assert len(results) == 0
        assert handler.last_page_fetched == 0
    
    def test_large_number_of_pages(self):
        """Test: Manejar un gran número de páginas correctamente."""
        # Setup
        client = Mock()
        
        # Simular 100 páginas
        responses = []
        for i in range(100):
            responses.append({
                'data': [{'id': str(i)}],
                'pagination': {'hasNextPage': i < 99}  # Última página sin hasNextPage
            })
        
        client.get.side_effect = responses
        
        handler = PaginationHandler(client, max_pages=150)
        
        # Act
        results = handler.fetch_all_pages('orders')
        
        # Assert
        assert len(results) == 100
        assert handler.last_page_fetched == 100
        assert client.get.call_count == 100
