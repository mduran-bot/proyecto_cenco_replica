"""
Ejemplos de uso de PaginationHandler.

Este script demuestra cómo usar el PaginationHandler para obtener
todas las páginas de resultados de las APIs de Janis.
"""

import os
import sys

# Agregar el directorio src al path para imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.api_client import JanisAPIClient
from src.pagination_handler import PaginationHandler, CircuitBreakerException


def example_basic_pagination():
    """
    Ejemplo 1: Paginación básica sin filtros.
    
    Obtiene todas las páginas de órdenes sin filtros adicionales.
    """
    print("=" * 60)
    print("Ejemplo 1: Paginación básica")
    print("=" * 60)
    
    # Configurar cliente API
    base_url = os.getenv('JANIS_API_URL', 'https://api.janis.in')
    api_key = os.getenv('JANIS_API_KEY', 'your-api-key-here')
    
    # Crear cliente y handler
    client = JanisAPIClient(base_url, api_key)
    handler = PaginationHandler(client, max_pages=1000, page_size=100)
    
    try:
        # Obtener todas las páginas de órdenes
        all_orders = handler.fetch_all_pages('orders')
        
        print(f"✓ Total de órdenes obtenidas: {len(all_orders)}")
        print(f"✓ Páginas procesadas: {handler.last_page_fetched}")
        
        # Mostrar primeras 3 órdenes
        if all_orders:
            print("\nPrimeras 3 órdenes:")
            for order in all_orders[:3]:
                print(f"  - ID: {order.get('id')}, Status: {order.get('status')}")
    
    except CircuitBreakerException as e:
        print(f"✗ Circuit breaker activado: {e}")
    
    finally:
        client.close()


def example_pagination_with_filters():
    """
    Ejemplo 2: Paginación con filtros incrementales.
    
    Obtiene órdenes modificadas después de una fecha específica,
    ordenadas por fecha de modificación.
    """
    print("\n" + "=" * 60)
    print("Ejemplo 2: Paginación con filtros incrementales")
    print("=" * 60)
    
    base_url = os.getenv('JANIS_API_URL', 'https://api.janis.in')
    api_key = os.getenv('JANIS_API_KEY', 'your-api-key-here')
    
    client = JanisAPIClient(base_url, api_key)
    handler = PaginationHandler(client, max_pages=500, page_size=100)
    
    # Definir filtros para polling incremental
    filters = {
        'dateModified': '2024-01-01T00:00:00Z',  # Desde esta fecha
        'sortBy': 'dateModified',                 # Ordenar por fecha
        'sortOrder': 'asc'                        # Orden ascendente
    }
    
    try:
        # Obtener órdenes con filtros
        filtered_orders = handler.fetch_all_pages('orders', filters)
        
        print(f"✓ Órdenes modificadas desde 2024-01-01: {len(filtered_orders)}")
        print(f"✓ Páginas procesadas: {handler.last_page_fetched}")
        
        # Mostrar rango de fechas
        if filtered_orders:
            first_date = filtered_orders[0].get('dateModified')
            last_date = filtered_orders[-1].get('dateModified')
            print(f"\nRango de fechas:")
            print(f"  - Primera: {first_date}")
            print(f"  - Última: {last_date}")
    
    except CircuitBreakerException as e:
        print(f"✗ Circuit breaker activado: {e}")
    
    finally:
        client.close()


def example_multiple_entities():
    """
    Ejemplo 3: Paginar múltiples tipos de entidades.
    
    Demuestra cómo reutilizar el mismo handler para diferentes endpoints
    usando el método reset().
    """
    print("\n" + "=" * 60)
    print("Ejemplo 3: Múltiples entidades con reset")
    print("=" * 60)
    
    base_url = os.getenv('JANIS_API_URL', 'https://api.janis.in')
    api_key = os.getenv('JANIS_API_KEY', 'your-api-key-here')
    
    client = JanisAPIClient(base_url, api_key)
    handler = PaginationHandler(client, max_pages=1000, page_size=100)
    
    entities = ['orders', 'products', 'stock']
    
    try:
        for entity in entities:
            # Reset del handler antes de cada entidad
            handler.reset()
            
            # Obtener todas las páginas
            records = handler.fetch_all_pages(entity)
            
            print(f"\n{entity.capitalize()}:")
            print(f"  - Total de registros: {len(records)}")
            print(f"  - Páginas procesadas: {handler.last_page_fetched}")
    
    except CircuitBreakerException as e:
        print(f"✗ Circuit breaker activado en {entity}: {e}")
    
    finally:
        client.close()


def example_circuit_breaker():
    """
    Ejemplo 4: Demostración del circuit breaker.
    
    Muestra cómo el circuit breaker previene bucles infinitos
    cuando hay demasiadas páginas.
    """
    print("\n" + "=" * 60)
    print("Ejemplo 4: Circuit breaker en acción")
    print("=" * 60)
    
    base_url = os.getenv('JANIS_API_URL', 'https://api.janis.in')
    api_key = os.getenv('JANIS_API_KEY', 'your-api-key-here')
    
    client = JanisAPIClient(base_url, api_key)
    
    # Configurar límite bajo para demostración
    handler = PaginationHandler(client, max_pages=5, page_size=10)
    
    try:
        # Intentar obtener muchas páginas
        all_records = handler.fetch_all_pages('orders')
        
        print(f"✓ Paginación completada sin activar circuit breaker")
        print(f"✓ Total de registros: {len(all_records)}")
    
    except CircuitBreakerException as e:
        print(f"✓ Circuit breaker activado correctamente:")
        print(f"  - Última página obtenida: {handler.last_page_fetched}")
        print(f"  - Mensaje: {str(e)[:100]}...")
    
    finally:
        client.close()


def example_custom_page_size():
    """
    Ejemplo 5: Configuración de tamaño de página personalizado.
    
    Demuestra cómo ajustar el tamaño de página según las necesidades.
    """
    print("\n" + "=" * 60)
    print("Ejemplo 5: Tamaño de página personalizado")
    print("=" * 60)
    
    base_url = os.getenv('JANIS_API_URL', 'https://api.janis.in')
    api_key = os.getenv('JANIS_API_KEY', 'your-api-key-here')
    
    client = JanisAPIClient(base_url, api_key)
    
    # Usar tamaño de página más pequeño
    handler = PaginationHandler(client, max_pages=1000, page_size=50)
    
    try:
        products = handler.fetch_all_pages('products')
        
        print(f"✓ Productos obtenidos con pageSize=50:")
        print(f"  - Total de productos: {len(products)}")
        print(f"  - Páginas procesadas: {handler.last_page_fetched}")
        print(f"  - Promedio por página: {len(products) / handler.last_page_fetched:.1f}")
    
    except CircuitBreakerException as e:
        print(f"✗ Circuit breaker activado: {e}")
    
    finally:
        client.close()


def example_context_manager():
    """
    Ejemplo 6: Uso con context manager.
    
    Demuestra el uso del cliente con context manager para
    gestión automática de recursos.
    """
    print("\n" + "=" * 60)
    print("Ejemplo 6: Context manager")
    print("=" * 60)
    
    base_url = os.getenv('JANIS_API_URL', 'https://api.janis.in')
    api_key = os.getenv('JANIS_API_KEY', 'your-api-key-here')
    
    # Usar context manager para gestión automática de recursos
    with JanisAPIClient(base_url, api_key) as client:
        handler = PaginationHandler(client, max_pages=1000, page_size=100)
        
        try:
            stores = handler.fetch_all_pages('stores')
            
            print(f"✓ Tiendas obtenidas: {len(stores)}")
            print(f"✓ Páginas procesadas: {handler.last_page_fetched}")
            
        except CircuitBreakerException as e:
            print(f"✗ Circuit breaker activado: {e}")
    
    # El cliente se cierra automáticamente al salir del context manager
    print("✓ Cliente cerrado automáticamente")


if __name__ == '__main__':
    """
    Ejecutar todos los ejemplos.
    
    Configurar variables de entorno antes de ejecutar:
    - JANIS_API_URL: URL base de la API de Janis
    - JANIS_API_KEY: API key para autenticación
    """
    print("\n" + "=" * 60)
    print("EJEMPLOS DE USO DE PAGINATIONHANDLER")
    print("=" * 60)
    
    # Verificar configuración
    if not os.getenv('JANIS_API_KEY') or os.getenv('JANIS_API_KEY') == 'your-api-key-here':
        print("\n⚠ ADVERTENCIA: Configurar JANIS_API_KEY antes de ejecutar")
        print("  export JANIS_API_URL='https://api.janis.in'")
        print("  export JANIS_API_KEY='tu-api-key'")
        print("\nEjecutando ejemplos con configuración de ejemplo...\n")
    
    # Ejecutar ejemplos
    try:
        example_basic_pagination()
        example_pagination_with_filters()
        example_multiple_entities()
        example_circuit_breaker()
        example_custom_page_size()
        example_context_manager()
        
        print("\n" + "=" * 60)
        print("✓ Todos los ejemplos completados")
        print("=" * 60)
    
    except Exception as e:
        print(f"\n✗ Error ejecutando ejemplos: {e}")
        import traceback
        traceback.print_exc()
