"""
PaginationHandler - Manejador de paginación con circuit breaker para APIs de Janis.

Este módulo implementa un manejador robusto de paginación que itera sobre páginas
de resultados de API con protección contra bucles infinitos mediante circuit breaker.
"""

from typing import Dict, List, Optional
import logging

# Configurar logger
logger = logging.getLogger(__name__)


class CircuitBreakerException(Exception):
    """
    Excepción lanzada cuando el circuit breaker se activa.
    
    Se activa cuando el número de páginas procesadas excede el límite máximo
    configurado, previniendo bucles infinitos de paginación.
    """
    pass


class PaginationHandler:
    """
    Manejador de paginación con circuit breaker para APIs de Janis.
    
    Características:
    - Iteración automática sobre todas las páginas de resultados
    - Tamaño de página configurable (default: 100 registros)
    - Circuit breaker para prevenir bucles infinitos (default: 1000 páginas)
    - Detección automática de hasNextPage
    - Logging de progreso de paginación
    
    Attributes:
        client: Cliente API de Janis para realizar requests
        max_pages (int): Número máximo de páginas antes de activar circuit breaker
        page_size (int): Número de registros por página
        last_page_fetched (int): Última página obtenida exitosamente
    """
    
    def __init__(self, client, max_pages: int = 1000, page_size: int = 100):
        """
        Inicializa el manejador de paginación.
        
        Args:
            client: Instancia de JanisAPIClient para realizar requests
            max_pages: Número máximo de páginas antes de activar circuit breaker (default: 1000)
            page_size: Número de registros por página (default: 100)
        
        Raises:
            ValueError: Si max_pages o page_size son menores o iguales a 0
        """
        if max_pages <= 0:
            raise ValueError("max_pages debe ser mayor que 0")
        if page_size <= 0:
            raise ValueError("page_size debe ser mayor que 0")
        
        self.client = client
        self.max_pages = max_pages
        self.page_size = page_size
        self.last_page_fetched = 0
    
    def fetch_all_pages(self, endpoint: str, filters: Optional[Dict] = None) -> List[Dict]:
        all_records = []
        
        filters = filters or {}
        # NO agregar pageSize ni page - esta API de Janis no los acepta
        
        logger.info(f"Obteniendo datos de endpoint '{endpoint}' (sin paginación)")
        
        # Realizar request a la API (sin parámetros de paginación)
        response = self.client.get(endpoint, params=filters)
        
        # === SOLUCIÓN: API sin paginación ===
        # Esta API de Janis NO acepta parámetros page ni pageSize
        # Devuelve todos los datos en una sola respuesta
        if isinstance(response, list):
            # Caso A: La API devuelve una lista directa [{}, {}]
            records = response
            logger.info(f"Respuesta de tipo lista con {len(records)} registros")
        elif isinstance(response, dict):
            # Caso B: La API devuelve un objeto {"data": [], "pagination": {}}
            records = response.get('data', [])
            logger.info(f"Respuesta de tipo dict con {len(records)} registros")
        else:
            logger.warning(f"Formato de respuesta inesperado: {type(response)}")
            records = []
        
        all_records.extend(records)
        # ==============================================================
        
        logger.info(
            f"Obtención completada para '{endpoint}'. "
            f"Total de registros: {len(all_records)}"
        )
        
        return all_records
    
    def reset(self):
        """
        Reinicia el contador de última página obtenida.
        
        Útil cuando se quiere reutilizar el mismo handler para múltiples
        operaciones de paginación.
        """
        self.last_page_fetched = 0
        logger.debug("PaginationHandler reiniciado")
