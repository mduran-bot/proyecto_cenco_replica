"""
Ejemplos de uso de JanisAPIClient.

Este archivo demuestra cómo usar el cliente API de Janis en diferentes escenarios.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from api_client import JanisAPIClient


def example_basic_usage():
    """Ejemplo básico de uso del cliente."""
    print("=== Ejemplo 1: Uso Básico ===")
    
    # Crear cliente
    client = JanisAPIClient(
        base_url="https://api.janis.in",
        api_key="your-api-key-here"
    )
    
    try:
        # Realizar request
        response = client.get("orders", params={
            "page": 1,
            "pageSize": 100
        })
        
        print(f"Obtenidos {len(response.get('data', []))} registros")
        
    finally:
        # Cerrar sesión
        client.close()


def example_context_manager():
    """Ejemplo usando context manager (recomendado)."""
    print("\n=== Ejemplo 2: Context Manager ===")
    
    # Usar context manager para manejo automático de recursos
    with JanisAPIClient("https://api.janis.in", "your-api-key-here") as client:
        response = client.get("products", params={"page": 1})
        print(f"Productos obtenidos: {len(response.get('data', []))}")
    
    # La sesión se cierra automáticamente al salir del context


def example_custom_rate_limit():
    """Ejemplo con rate limit personalizado."""
    print("\n=== Ejemplo 3: Rate Limit Personalizado ===")
    
    # Configurar rate limit más bajo (50 requests/minuto)
    with JanisAPIClient(
        base_url="https://api.janis.in",
        api_key="your-api-key-here",
        rate_limit=50
    ) as client:
        
        # El cliente automáticamente limitará la tasa de requests
        for i in range(10):
            response = client.get("stock", params={"page": i + 1})
            print(f"Página {i + 1} procesada")


def example_error_handling():
    """Ejemplo de manejo de errores."""
    print("\n=== Ejemplo 4: Manejo de Errores ===")
    
    with JanisAPIClient("https://api.janis.in", "your-api-key-here") as client:
        try:
            # Intentar obtener un recurso que no existe
            response = client.get("orders/invalid-id")
            
        except ValueError as e:
            # Errores 4xx del cliente
            print(f"Error del cliente: {e}")
            
        except Exception as e:
            # Otros errores (timeout, red, etc.)
            print(f"Error inesperado: {e}")


def example_with_environment_variables():
    """Ejemplo usando variables de entorno."""
    print("\n=== Ejemplo 5: Variables de Entorno ===")
    
    # En producción, usar variables de entorno para credenciales
    base_url = os.environ.get("JANIS_API_URL", "https://api.janis.in")
    api_key = os.environ.get("JANIS_API_KEY", "")
    
    if not api_key:
        print("Error: JANIS_API_KEY no está configurado")
        return
    
    with JanisAPIClient(base_url, api_key) as client:
        response = client.get("orders", params={"page": 1})
        print(f"Órdenes obtenidas: {len(response.get('data', []))}")


def example_pagination():
    """Ejemplo de paginación de resultados."""
    print("\n=== Ejemplo 6: Paginación ===")
    
    with JanisAPIClient("https://api.janis.in", "your-api-key-here") as client:
        page = 1
        all_orders = []
        
        while True:
            response = client.get("orders", params={
                "page": page,
                "pageSize": 100
            })
            
            data = response.get('data', [])
            if not data:
                break
            
            all_orders.extend(data)
            print(f"Página {page}: {len(data)} registros")
            
            # Verificar si hay más páginas
            pagination = response.get('pagination', {})
            if not pagination.get('hasNextPage', False):
                break
            
            page += 1
        
        print(f"Total de órdenes obtenidas: {len(all_orders)}")


if __name__ == "__main__":
    print("Ejemplos de uso de JanisAPIClient")
    print("=" * 50)
    print("\nNOTA: Estos ejemplos requieren credenciales válidas de la API de Janis.")
    print("Configure JANIS_API_KEY en las variables de entorno antes de ejecutar.\n")
    
    # Descomentar los ejemplos que desee ejecutar:
    # example_basic_usage()
    # example_context_manager()
    # example_custom_rate_limit()
    # example_error_handling()
    # example_with_environment_variables()
    # example_pagination()
