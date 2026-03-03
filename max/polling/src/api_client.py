"""
JanisAPIClient - Cliente HTTP con rate limiting y retry strategy para APIs de Janis.

Este módulo implementa un cliente robusto para interactuar con las APIs REST de Janis,
incluyendo gestión de sesión HTTP, rate limiting y reintentos automáticos con backoff exponencial.
"""

import time
from typing import Dict, Optional
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


class JanisAPIClient:
    """
    Cliente HTTP para APIs de Janis con rate limiting y retry strategy.
    
    Características:
    - Rate limiting: Máximo 100 requests por minuto usando sliding window
    - Retry strategy: 3 intentos con backoff exponencial (2, 4, 8 segundos)
    - Timeout: 30 segundos por request
    - Manejo de errores HTTP apropiado
    
    Attributes:
        base_url (str): URL base de la API de Janis
        api_key (str): API key para autenticación
        rate_limit (int): Número máximo de requests por minuto
        request_times (list): Timestamps de requests para rate limiting
        session (requests.Session): Sesión HTTP configurada con retry strategy
    """
    
    def __init__(self, base_url: str, api_key: str, rate_limit: int = 100, extra_headers: Optional[Dict[str, str]] = None):
        """
        Inicializa el cliente API de Janis.
        
        Args:
            base_url: URL base de la API (ej: "https://api.janis.in")
            api_key: API key para autenticación Bearer
            rate_limit: Número máximo de requests por minuto (default: 100)
            extra_headers: Headers adicionales para incluir en cada request (opcional)
        
        Raises:
            ValueError: Si base_url o api_key están vacíos
        """
        if not base_url:
            raise ValueError("base_url no puede estar vacío")
        if not api_key:
            raise ValueError("api_key no puede estar vacío")
        if rate_limit <= 0:
            raise ValueError("rate_limit debe ser mayor que 0")
        
        self.base_url = base_url.rstrip('/')  # Remover trailing slash
        self.api_key = api_key
        self.rate_limit = rate_limit
        self.extra_headers = extra_headers or {}
        self.request_times = []
        self.session = self._create_session()
    
    def _create_session(self) -> requests.Session:
        """
        Crea y configura una sesión HTTP con retry strategy.
        
        Configuración de reintentos:
        - Total de intentos: 3
        - Backoff factor: 2 (delays de 2, 4, 8 segundos)
        - Status codes para reintentar: 429, 500, 502, 503, 504
        - Métodos permitidos: GET
        
        Returns:
            requests.Session: Sesión HTTP configurada con HTTPAdapter y retry strategy
        """
        session = requests.Session()
        
        # Configurar retry strategy con backoff exponencial
        retry_strategy = Retry(
            total=3,                    # 3 intentos totales
            backoff_factor=2,           # Backoff exponencial: 2, 4, 8 segundos
            status_forcelist=[429, 500, 502, 503, 504],  # Status codes para reintentar
            allowed_methods=["GET"],    # Solo GET requests
            raise_on_status=False       # No lanzar excepción, dejar que el código maneje
        )
        
        # Crear adapter con retry strategy
        adapter = HTTPAdapter(max_retries=retry_strategy)
        
        # Montar adapter para HTTP y HTTPS
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        return session
    
    def _enforce_rate_limit(self):
        """
        Aplica rate limiting usando algoritmo de sliding window.
        
        Mantiene un registro de timestamps de requests en los últimos 60 segundos.
        Si se alcanza el límite de rate, espera hasta que el request más antiguo
        tenga 60 segundos de antigüedad.
        
        Este método se llama automáticamente antes de cada request.
        """
        now = time.time()
        
        # Remover requests más antiguos que 60 segundos (sliding window)
        self.request_times = [t for t in self.request_times if now - t < 60]
        
        # Si alcanzamos el límite de rate, esperar
        if len(self.request_times) >= self.rate_limit:
            # Calcular cuánto tiempo esperar hasta que el request más antiguo expire
            oldest_request = self.request_times[0]
            sleep_time = 60 - (now - oldest_request)
            
            if sleep_time > 0:
                time.sleep(sleep_time)
                # Limpiar la ventana después de esperar
                self.request_times = []
        
        # Registrar el timestamp del nuevo request
        self.request_times.append(time.time())
    
    def get(self, endpoint: str, params: Optional[Dict] = None) -> Dict:
        """
        Realiza un GET request con rate limiting y manejo de errores.
        
        Args:
            endpoint: Endpoint de la API (ej: "orders", "products/123")
            params: Parámetros de query string opcionales
        
        Returns:
            Dict: Respuesta JSON parseada de la API
        
        Raises:
            ValueError: Para errores 4xx del cliente (excepto 429)
            requests.exceptions.HTTPError: Para errores de servidor después de reintentos
            requests.exceptions.Timeout: Si el request excede 30 segundos
            requests.exceptions.RequestException: Para otros errores de red
        
        Example:
            >>> client = JanisAPIClient("https://api.janis.in", "my-api-key")
            >>> response = client.get("orders", params={"page": 1, "pageSize": 100})
            >>> orders = response.get('data', [])
        """
        # Aplicar rate limiting antes del request
        self._enforce_rate_limit()
        
        # Debug: mostrar endpoint recibido
        print(f"[DEBUG] endpoint recibido: '{endpoint}'")
        
        # Construir URL completa
        # Si endpoint está vacío, usar solo la base_url
        if endpoint:
            url = f"{self.base_url}/{endpoint.lstrip('/')}"
        else:
            url = self.base_url
        
        print(f"[DEBUG] URL construida: {url}")
        
        # Configurar headers base
        headers = {
            "Content-Type": "application/json"
        }
        
        # Si hay extra_headers, usarlos en lugar del Bearer token
        # (para APIs como Janis que usan autenticación custom)
        if self.extra_headers:
            headers.update(self.extra_headers)
        else:
            # Usar Bearer token por defecto
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        try:
            # Debug: mostrar URL y headers (sin valores sensibles)
            print(f"\n[DEBUG] Request URL: {url}")
            print(f"[DEBUG] Headers: {list(headers.keys())}")
            print(f"[DEBUG] Params: {params}")
            
            # Realizar request con timeout de 30 segundos
            response = self.session.get(
                url,
                headers=headers,
                params=params,
                timeout=30
            )
            
            # Manejar diferentes códigos de estado HTTP
            if response.status_code == 429:
                # Rate limit hit - el retry strategy debería haber manejado esto
                # Si llegamos aquí, significa que se agotaron los reintentos
                raise requests.exceptions.HTTPError(
                    f"Rate limit exceeded después de reintentos: {response.status_code}",
                    response=response
                )
            elif 400 <= response.status_code < 500:
                # Client error (4xx) - no reintentar
                raise ValueError(
                    f"Client error: {response.status_code} - {response.text}"
                )
            elif response.status_code >= 500:
                # Server error (5xx) - el retry strategy debería haber manejado esto
                # Si llegamos aquí, significa que se agotaron los reintentos
                response.raise_for_status()
            
            # Request exitoso - parsear y retornar JSON
            return response.json()
            
        except requests.exceptions.Timeout:
            # Timeout después de 30 segundos
            raise
        except requests.exceptions.RequestException as e:
            logger.error(f"Error de red detectado: {e}")
            raise
    
    def close(self):
        """
        Cierra la sesión HTTP y libera recursos.
        
        Es buena práctica llamar este método cuando se termina de usar el cliente,
        especialmente en aplicaciones de larga duración.
        """
        if self.session:
            self.session.close()
    
    def __enter__(self):
        """Soporte para context manager."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Cierra la sesión al salir del context manager."""
        self.close()
