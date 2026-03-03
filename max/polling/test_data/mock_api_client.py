"""
Mock API Client para Testing

Este módulo proporciona un cliente API mock que simula las respuestas
de la API real de Janis usando datos JSON locales.

Uso:
    from test_data.mock_api_client import MockJanisAPIClient
    
    client = MockJanisAPIClient(client='metro')
    response = client.get('/order', params={'page': 1})
"""

import json
import os
import time
from typing import Dict, Optional


class MockJanisAPIClient:
    """
    Cliente API mock que simula respuestas de Janis API.
    
    Simula:
    - Paginación (2 páginas de datos)
    - Rate limiting (delay artificial)
    - Datos específicos por cliente (metro/wongio)
    - Estructura de respuesta real de la API
    """
    
    def __init__(self, base_url: str = None, api_key: str = None, 
                 rate_limit: int = 100, extra_headers: Dict = None):
        """
        Inicializa el cliente mock.
        
        Args:
            base_url: URL base (ignorada en mock)
            api_key: API key (ignorada en mock)
            rate_limit: Rate limit (usado para simular delay)
            extra_headers: Headers adicionales (usado para detectar cliente)
        """
        self.base_url = base_url or "https://mock.api.janis.in"
        self.api_key = api_key or "mock-api-key"
        self.rate_limit = rate_limit
        self.extra_headers = extra_headers or {}
        self.request_count = 0
        
        # Detectar cliente desde headers
        self.client = self.extra_headers.get('janis-client', 'metro')
        
        # Cargar datos mock
        self.data_dir = os.path.join(os.path.dirname(__file__))
        self._load_mock_data()
    
    def _load_mock_data(self):
        """Carga datos mock desde archivos JSON."""
        # Mapeo de cliente a archivo
        client_files = {
            'metro': 'mock_orders_page1.json',
            'wongio': 'mock_orders_page2.json'
        }
        
        file_name = client_files.get(self.client, 'mock_orders_page1.json')
        file_path = os.path.join(self.data_dir, file_name)
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                self.mock_data = json.load(f)
            print(f"  [MOCK] Datos cargados desde: {file_name}")
        except FileNotFoundError:
            print(f"  [MOCK] ⚠ Archivo no encontrado: {file_path}")
            # Datos de fallback
            self.mock_data = {
                "data": [],
                "pagination": {
                    "page": 1,
                    "pageSize": 100,
                    "totalPages": 1,
                    "totalItems": 0,
                    "hasNextPage": False
                }
            }
    
    def get(self, endpoint: str, params: Optional[Dict] = None) -> Dict:
        """
        Simula un GET request a la API.
        
        Args:
            endpoint: Endpoint de la API (ej: '/order')
            params: Parámetros de query (page, pageSize, etc.)
        
        Returns:
            Dict con estructura de respuesta de la API
        """
        params = params or {}
        page = params.get('page', 1)
        page_size = params.get('pageSize', 100)
        
        self.request_count += 1
        
        # Simular delay de red (10-50ms)
        time.sleep(0.01 + (self.request_count * 0.005))
        
        print(f"  [MOCK] GET {endpoint} - Cliente: {self.client} - Página: {page}")
        
        # Simular paginación
        if page == 1:
            # Primera página: retornar datos del cliente
            response = self.mock_data.copy()
            response['pagination']['page'] = 1
            print(f"  [MOCK] → Retornando {len(response['data'])} registros (página 1)")
            return response
        elif page == 2:
            # Segunda página: retornar página vacía (simular fin de datos)
            response = {
                "data": [],
                "pagination": {
                    "page": 2,
                    "pageSize": page_size,
                    "totalPages": 1,
                    "totalItems": len(self.mock_data.get('data', [])),
                    "hasNextPage": False
                }
            }
            print(f"  [MOCK] → Retornando 0 registros (página 2 - fin)")
            return response
        else:
            # Páginas adicionales: vacías
            response = {
                "data": [],
                "pagination": {
                    "page": page,
                    "pageSize": page_size,
                    "totalPages": 1,
                    "totalItems": 0,
                    "hasNextPage": False
                }
            }
            print(f"  [MOCK] → Retornando 0 registros (página {page})")
            return response
    
    def close(self):
        """Cierra el cliente (no-op en mock)."""
        print(f"  [MOCK] Cliente cerrado - Total requests: {self.request_count}")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
        return False


def create_mock_client(client: str, base_url: str = None, api_key: str = None) -> MockJanisAPIClient:
    """
    Factory function para crear un cliente mock.
    
    Args:
        client: Identificador del cliente ('metro' o 'wongio')
        base_url: URL base (opcional)
        api_key: API key (opcional)
    
    Returns:
        MockJanisAPIClient configurado
    """
    return MockJanisAPIClient(
        base_url=base_url,
        api_key=api_key,
        extra_headers={
            'janis-client': client,
            'janis-api-key': api_key or 'mock-key',
            'janis-api-secret': 'mock-secret'
        }
    )
