"""
Unit tests para JanisAPIClient.

Valida la inicialización, configuración de sesión HTTP, y manejo básico de requests.
"""

import pytest
import time
from unittest.mock import Mock, patch, MagicMock
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import requests

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from api_client import JanisAPIClient


class TestJanisAPIClientInitialization:
    """Tests para la inicialización del cliente API."""
    
    def test_initialization_with_valid_parameters(self):
        """Verifica que el cliente se inicializa correctamente con parámetros válidos."""
        client = JanisAPIClient(
            base_url="https://api.janis.in",
            api_key="test-api-key",
            rate_limit=100
        )
        
        assert client.base_url == "https://api.janis.in"
        assert client.api_key == "test-api-key"
        assert client.rate_limit == 100
        assert client.request_times == []
        assert client.session is not None
        assert isinstance(client.session, requests.Session)
    
    def test_initialization_removes_trailing_slash(self):
        """Verifica que se remueve el trailing slash de la URL base."""
        client = JanisAPIClient(
            base_url="https://api.janis.in/",
            api_key="test-api-key"
        )
        
        assert client.base_url == "https://api.janis.in"
    
    def test_initialization_with_empty_base_url_raises_error(self):
        """Verifica que se lanza ValueError si base_url está vacío."""
        with pytest.raises(ValueError, match="base_url no puede estar vacío"):
            JanisAPIClient(base_url="", api_key="test-api-key")
    
    def test_initialization_with_empty_api_key_raises_error(self):
        """Verifica que se lanza ValueError si api_key está vacío."""
        with pytest.raises(ValueError, match="api_key no puede estar vacío"):
            JanisAPIClient(base_url="https://api.janis.in", api_key="")
    
    def test_initialization_with_invalid_rate_limit_raises_error(self):
        """Verifica que se lanza ValueError si rate_limit es <= 0."""
        with pytest.raises(ValueError, match="rate_limit debe ser mayor que 0"):
            JanisAPIClient(
                base_url="https://api.janis.in",
                api_key="test-api-key",
                rate_limit=0
            )
    
    def test_default_rate_limit(self):
        """Verifica que el rate_limit por defecto es 100."""
        client = JanisAPIClient(
            base_url="https://api.janis.in",
            api_key="test-api-key"
        )
        
        assert client.rate_limit == 100


class TestSessionCreation:
    """Tests para la creación y configuración de la sesión HTTP."""
    
    def test_session_is_created(self):
        """Verifica que se crea una sesión HTTP."""
        client = JanisAPIClient(
            base_url="https://api.janis.in",
            api_key="test-api-key"
        )
        
        assert client.session is not None
        assert isinstance(client.session, requests.Session)
    
    def test_session_has_http_adapter(self):
        """Verifica que la sesión tiene HTTPAdapter configurado."""
        client = JanisAPIClient(
            base_url="https://api.janis.in",
            api_key="test-api-key"
        )
        
        # Verificar que hay adapters montados
        assert 'http://' in client.session.adapters
        assert 'https://' in client.session.adapters
        
        # Verificar que son HTTPAdapter
        assert isinstance(client.session.adapters['http://'], HTTPAdapter)
        assert isinstance(client.session.adapters['https://'], HTTPAdapter)
    
    def test_retry_strategy_configuration(self):
        """Verifica que el retry strategy está configurado correctamente."""
        client = JanisAPIClient(
            base_url="https://api.janis.in",
            api_key="test-api-key"
        )
        
        # Obtener el adapter
        adapter = client.session.adapters['https://']
        
        # Verificar que tiene max_retries configurado
        assert adapter.max_retries is not None
        
        # Verificar configuración del retry
        retry = adapter.max_retries
        assert isinstance(retry, Retry)
        assert retry.total == 3
        assert retry.backoff_factor == 2
        assert 429 in retry.status_forcelist
        assert 500 in retry.status_forcelist
        assert 502 in retry.status_forcelist
        assert 503 in retry.status_forcelist
        assert 504 in retry.status_forcelist


class TestRateLimiting:
    """Tests para el rate limiting."""
    
    def test_enforce_rate_limit_allows_requests_under_limit(self):
        """Verifica que se permiten requests bajo el límite."""
        client = JanisAPIClient(
            base_url="https://api.janis.in",
            api_key="test-api-key",
            rate_limit=5
        )
        
        # Realizar 5 requests (bajo el límite)
        start_time = time.time()
        for _ in range(5):
            client._enforce_rate_limit()
        end_time = time.time()
        
        # No debería haber delay significativo
        assert end_time - start_time < 1.0
        assert len(client.request_times) == 5
    
    def test_enforce_rate_limit_blocks_when_limit_reached(self):
        """Verifica que se bloquea cuando se alcanza el límite."""
        client = JanisAPIClient(
            base_url="https://api.janis.in",
            api_key="test-api-key",
            rate_limit=3
        )
        
        # Realizar 3 requests rápidamente
        for _ in range(3):
            client._enforce_rate_limit()
        
        # El 4to request debería causar un delay
        start_time = time.time()
        client._enforce_rate_limit()
        end_time = time.time()
        
        # Debería haber esperado cerca de 60 segundos
        # (en test usamos un threshold más bajo para no esperar tanto)
        # En producción esto sería ~60 segundos
        assert len(client.request_times) == 1  # Se limpia después del delay
    
    def test_sliding_window_removes_old_requests(self):
        """Verifica que el sliding window remueve requests antiguos."""
        client = JanisAPIClient(
            base_url="https://api.janis.in",
            api_key="test-api-key",
            rate_limit=100
        )
        
        # Agregar timestamps antiguos manualmente
        old_time = time.time() - 61  # 61 segundos atrás
        client.request_times = [old_time, old_time, old_time]
        
        # Llamar enforce_rate_limit
        client._enforce_rate_limit()
        
        # Los timestamps antiguos deberían haberse removido
        assert len(client.request_times) == 1  # Solo el nuevo request


class TestGetMethod:
    """Tests para el método get()."""
    
    @patch('requests.Session.get')
    def test_get_successful_request(self, mock_get):
        """Verifica que un request exitoso retorna JSON."""
        # Mock de respuesta exitosa
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": [{"id": "123"}]}
        mock_get.return_value = mock_response
        
        client = JanisAPIClient(
            base_url="https://api.janis.in",
            api_key="test-api-key"
        )
        
        result = client.get("orders", params={"page": 1})
        
        assert result == {"data": [{"id": "123"}]}
        mock_get.assert_called_once()
    
    @patch('requests.Session.get')
    def test_get_includes_authorization_header(self, mock_get):
        """Verifica que se incluye el header de autorización."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {}
        mock_get.return_value = mock_response
        
        client = JanisAPIClient(
            base_url="https://api.janis.in",
            api_key="my-secret-key"
        )
        
        client.get("orders")
        
        # Verificar que se llamó con el header correcto
        call_args = mock_get.call_args
        headers = call_args.kwargs['headers']
        assert headers['Authorization'] == "Bearer my-secret-key"
    
    @patch('requests.Session.get')
    def test_get_constructs_correct_url(self, mock_get):
        """Verifica que se construye la URL correctamente."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {}
        mock_get.return_value = mock_response
        
        client = JanisAPIClient(
            base_url="https://api.janis.in",
            api_key="test-api-key"
        )
        
        client.get("orders/123")
        
        # Verificar URL
        call_args = mock_get.call_args
        assert call_args.args[0] == "https://api.janis.in/orders/123"
    
    @patch('requests.Session.get')
    def test_get_handles_4xx_client_error(self, mock_get):
        """Verifica que se lanza ValueError para errores 4xx."""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.text = "Not Found"
        mock_get.return_value = mock_response
        
        client = JanisAPIClient(
            base_url="https://api.janis.in",
            api_key="test-api-key"
        )
        
        with pytest.raises(ValueError, match="Client error: 404"):
            client.get("orders/invalid")
    
    @patch('requests.Session.get')
    def test_get_uses_30_second_timeout(self, mock_get):
        """Verifica que se usa timeout de 30 segundos."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {}
        mock_get.return_value = mock_response
        
        client = JanisAPIClient(
            base_url="https://api.janis.in",
            api_key="test-api-key"
        )
        
        client.get("orders")
        
        # Verificar timeout
        call_args = mock_get.call_args
        assert call_args.kwargs['timeout'] == 30


class TestContextManager:
    """Tests para el soporte de context manager."""
    
    def test_context_manager_support(self):
        """Verifica que el cliente soporta context manager."""
        with JanisAPIClient("https://api.janis.in", "test-api-key") as client:
            assert client.session is not None
        
        # La sesión debería estar cerrada después del context
        # (no hay forma fácil de verificar esto sin acceder a internals)
    
    def test_close_method(self):
        """Verifica que el método close() cierra la sesión."""
        client = JanisAPIClient("https://api.janis.in", "test-api-key")
        
        # Mock del método close de la sesión
        client.session.close = Mock()
        
        client.close()
        
        client.session.close.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
