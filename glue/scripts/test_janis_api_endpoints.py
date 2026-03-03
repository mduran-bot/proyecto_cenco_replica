"""
Script para probar diferentes endpoints de Janis API

Este script prueba varios endpoints para encontrar el que devuelve
la información completa de la orden (wms_orders).

Ejecutar: python glue/scripts/test_janis_api_endpoints.py
"""

import requests
import json
from datetime import datetime

# Configuración de la API
BASE_URL = "https://oms.janis.in/api"
ORDER_ID = "6913fcb6d134afc8da8ac3dd"

HEADERS = {
    'janis-client': 'wongio',
    'janis-api-key': '8fc949ac-6d63-4447-a3d6-a16b66048e61',
    'janis-api-secret': 'UwPbe45dmE7lySRJ3zcA66Pfdt7xAY3QXWO181Y8OTgCxE3aZuyXpS8HyyPSwsWK'
}

# Colores
class Colors:
    GREEN = '\033[92m'
    BLUE = '\033[94m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'

def test_endpoint(endpoint_name, url):
    """Prueba un endpoint y muestra los resultados."""
    print(f"\n{Colors.BLUE}{'='*70}")
    print(f"Probando: {endpoint_name}")
    print(f"URL: {url}")
    print(f"{'='*70}{Colors.END}\n")
    
    try:
        response = requests.get(url, headers=HEADERS, timeout=30)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"{Colors.GREEN}✓ Éxito!{Colors.END}")
            print(f"\nTipo de respuesta: {type(data)}")
            
            # Limpiar nombre para archivo
            safe_name = endpoint_name.replace(' ', '_').replace('/', '_').replace('(', '').replace(')', '').lower()
            
            if isinstance(data, dict):
                print(f"Claves principales: {list(data.keys())[:15]}")
                
                # Guardar respuesta
                filename = f"glue/data/janis_{safe_name}.json"
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                print(f"\n{Colors.GREEN}✓ Datos guardados en: {filename}{Colors.END}")
                
                # Mostrar preview
                print("\nPreview (primeros 1000 caracteres):")
                print(json.dumps(data, indent=2, ensure_ascii=False)[:1000] + "...")
                
            elif isinstance(data, list):
                print(f"Cantidad de elementos: {len(data)}")
                if data:
                    print(f"Tipo del primer elemento: {type(data[0])}")
                    if isinstance(data[0], dict):
                        print(f"Claves del primer elemento: {list(data[0].keys())[:15]}")
                
                # Guardar respuesta
                filename = f"glue/data/janis_{safe_name}.json"
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                print(f"\n{Colors.GREEN}✓ Datos guardados en: {filename}{Colors.END}")
            
            return True
            
        elif response.status_code == 404:
            print(f"{Colors.YELLOW}⚠ Endpoint no encontrado (404){Colors.END}")
            return False
            
        elif response.status_code == 401:
            print(f"{Colors.RED}✗ No autorizado (401) - Verificar credenciales{Colors.END}")
            return False
            
        else:
            print(f"{Colors.RED}✗ Error: {response.status_code}{Colors.END}")
            print(f"Respuesta: {response.text[:500]}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"{Colors.RED}✗ Error de conexión: {e}{Colors.END}")
        return False


def main():
    print(f"\n{Colors.BLUE}{'='*70}")
    print("PRUEBA DE ENDPOINTS DE JANIS API")
    print(f"{'='*70}{Colors.END}")
    print(f"\nFecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Order ID: {ORDER_ID}")
    print()
    
    # Lista de endpoints a probar
    endpoints = [
        ("Order (sin /history)", f"{BASE_URL}/order/{ORDER_ID}"),
        ("Order History", f"{BASE_URL}/order/{ORDER_ID}/history"),
        ("Orders (plural)", f"{BASE_URL}/orders/{ORDER_ID}"),
        ("WMS Order", f"{BASE_URL}/wms/order/{ORDER_ID}"),
        ("WMS Orders", f"{BASE_URL}/wms/orders/{ORDER_ID}"),
        ("Order Detail", f"{BASE_URL}/order/{ORDER_ID}/detail"),
        ("Order Full", f"{BASE_URL}/order/{ORDER_ID}/full"),
    ]
    
    successful_endpoints = []
    
    for name, url in endpoints:
        if test_endpoint(name, url):
            successful_endpoints.append((name, url))
        
        # Pequeña pausa entre requests
        import time
        time.sleep(0.5)
    
    # Resumen
    print(f"\n{Colors.BLUE}{'='*70}")
    print("RESUMEN")
    print(f"{'='*70}{Colors.END}\n")
    
    if successful_endpoints:
        print(f"{Colors.GREEN}Endpoints exitosos:{Colors.END}")
        for name, url in successful_endpoints:
            print(f"  ✓ {name}: {url}")
    else:
        print(f"{Colors.YELLOW}No se encontraron endpoints exitosos{Colors.END}")
    
    print()
    print("Próximo paso:")
    print("  1. Revisar los archivos JSON generados en glue/data/")
    print("  2. Identificar cuál tiene la información completa de la orden")
    print("  3. Usar ese endpoint en el pipeline")
    print()


if __name__ == "__main__":
    main()
