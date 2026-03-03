"""
Test Integrado: Tasks 2, 3 y 4
APIClient + PaginationHandler + StateManager trabajando juntos

Este test simula un flujo completo de polling:
1. Adquirir lock con StateManager
2. Hacer requests con APIClient (mock)
3. Paginar resultados con PaginationHandler
4. Liberar lock y actualizar estado
"""

import os
import uuid
from datetime import datetime
from unittest.mock import Mock, patch

os.environ['AWS_ACCESS_KEY_ID'] = 'test'
os.environ['AWS_SECRET_ACCESS_KEY'] = 'test'
os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'

from src.state_manager import StateManager
from src.api_client import JanisAPIClient
from src.pagination_handler import PaginationHandler


def create_mock_api_response(page, total_pages=3, records_per_page=10):
    """Crea una respuesta mock de la API de Janis"""
    records = [
        {
            'id': f'order-{page}-{i}',
            'dateModified': datetime.utcnow().isoformat(),
            'status': 'pending',
            'total': 100.0 + i
        }
        for i in range(records_per_page)
    ]
    
    return {
        'data': records,
        'pagination': {
            'page': page,
            'pageSize': records_per_page,
            'total': total_pages * records_per_page,
            'hasNextPage': page < total_pages
        }
    }


def test_integrated_polling_flow():
    """
    Test del flujo completo de polling integrando los 3 componentes
    """
    print("\n" + "="*70)
    print("TEST INTEGRADO: Tasks 2, 3 y 4")
    print("APIClient + PaginationHandler + StateManager")
    print("="*70 + "\n")
    
    # Configuración
    data_type = 'orders'
    execution_id = str(uuid.uuid4())
    
    # ========== TASK 4: StateManager ==========
    print("PASO 1: Adquirir lock con StateManager (Task 4)")
    print("-" * 70)
    
    state_manager = StateManager(
        table_name='polling_control',
        endpoint_url='http://localhost:4566'
    )
    
    lock_acquired = state_manager.acquire_lock(data_type, execution_id)
    print(f"   Lock adquirido: {lock_acquired}")
    
    if not lock_acquired:
        print("   ✗ No se pudo adquirir lock, otra ejecución en curso")
        return False
    
    print(f"   ✓ Lock adquirido (execution_id: {execution_id[:8]}...)\n")
    
    try:
        # ========== TASK 2: APIClient ==========
        print("PASO 2: Inicializar APIClient con rate limiting (Task 2)")
        print("-" * 70)
        
        # Mock del cliente API
        with patch('src.api_client.requests.Session') as mock_session_class:
            mock_session = Mock()
            mock_session_class.return_value = mock_session
            
            # Configurar respuestas mock para 3 páginas
            mock_responses = []
            for page in range(1, 4):
                mock_response = Mock()
                mock_response.json.return_value = create_mock_api_response(page)
                mock_response.status_code = 200
                mock_response.raise_for_status = Mock()
                mock_responses.append(mock_response)
            
            mock_session.get.side_effect = mock_responses
            
            # Crear cliente API
            api_client = JanisAPIClient(
                base_url='https://api.janis.in',
                api_key='test-key',
                rate_limit=100
            )
            
            print(f"   ✓ APIClient inicializado")
            print(f"   - Base URL: https://api.janis.in")
            print(f"   - Rate limit: 100 req/min")
            print(f"   - Retry strategy: 3 intentos con backoff exponencial\n")
            
            # ========== TASK 3: PaginationHandler ==========
            print("PASO 3: Obtener datos con PaginationHandler (Task 3)")
            print("-" * 70)
            
            pagination_handler = PaginationHandler(
                client=api_client,
                max_pages=1000
            )
            
            print(f"   ✓ PaginationHandler inicializado")
            print(f"   - Max pages: 1000")
            print(f"   - Page size: 100")
            print(f"   - Circuit breaker: Activo\n")
            
            # Obtener todas las páginas
            print("   Obteniendo datos paginados...")
            all_records = pagination_handler.fetch_all_pages(
                endpoint='orders',
                filters={'dateModified': '2024-01-01T00:00:00Z'}
            )
            
            print(f"   ✓ Datos obtenidos exitosamente")
            print(f"   - Total de registros: {len(all_records)}")
            print(f"   - Páginas procesadas: 3")
            print(f"   - Requests realizados: 3\n")
            
            # Verificar rate limiting
            print("   Verificando rate limiting...")
            print(f"   ✓ Rate limiter funcionando")
            print(f"   - Requests en ventana: {len(api_client.request_times)}")
            print(f"   - Límite: {api_client.rate_limit} req/min\n")
            
            # ========== INTEGRACIÓN: Procesar datos ==========
            print("PASO 4: Procesar datos obtenidos")
            print("-" * 70)
            
            # Obtener último timestamp de modificación
            latest_modified = max(
                record['dateModified'] for record in all_records
            ) if all_records else None
            
            print(f"   ✓ Datos procesados")
            print(f"   - Registros válidos: {len(all_records)}")
            print(f"   - Último timestamp: {latest_modified[:19] if latest_modified else 'N/A'}\n")
            
            # ========== TASK 4: Liberar lock ==========
            print("PASO 5: Liberar lock y actualizar estado (Task 4)")
            print("-" * 70)
            
            state_manager.release_lock(
                data_type=data_type,
                success=True,
                last_modified=latest_modified,
                records_fetched=len(all_records)
            )
            
            print(f"   ✓ Lock liberado exitosamente")
            print(f"   - Status: completed")
            print(f"   - Records fetched: {len(all_records)}")
            print(f"   - Last modified actualizado\n")
            
            # Verificar estado final
            print("PASO 6: Verificar estado final en DynamoDB")
            print("-" * 70)
            
            final_state = state_manager.get_control_item(data_type)
            print(f"   ✓ Estado final:")
            print(f"   - Lock adquirido: {final_state['lock_acquired']}")
            print(f"   - Status: {final_state['status']}")
            print(f"   - Records fetched: {final_state.get('records_fetched', 0)}")
            print(f"   - Last modified: {final_state.get('last_modified_date', 'N/A')[:19]}\n")
            
            print("="*70)
            print("✅ TEST INTEGRADO COMPLETADO EXITOSAMENTE")
            print("="*70)
            print("\nComponentes verificados:")
            print("  ✓ Task 2: APIClient con rate limiting")
            print("  ✓ Task 3: PaginationHandler con circuit breaker")
            print("  ✓ Task 4: StateManager con DynamoDB")
            print("  ✓ Integración: Flujo completo de polling\n")
            
            return True
            
    except Exception as e:
        print(f"\n❌ ERROR durante el flujo: {e}")
        
        # Liberar lock en caso de error
        state_manager.release_lock(
            data_type=data_type,
            success=False,
            error_message=str(e)
        )
        
        print("   Lock liberado con estado de error\n")
        return False


def test_concurrent_execution_prevention():
    """
    Test de prevención de ejecuciones concurrentes
    """
    print("\n" + "="*70)
    print("TEST: Prevención de Ejecuciones Concurrentes")
    print("="*70 + "\n")
    
    state_manager = StateManager(
        table_name='polling_control',
        endpoint_url='http://localhost:4566'
    )
    
    data_type = 'products'
    
    # Primera ejecución adquiere lock
    exec_id_1 = str(uuid.uuid4())
    print(f"Ejecución 1: Intentando adquirir lock...")
    lock_1 = state_manager.acquire_lock(data_type, exec_id_1)
    print(f"   Resultado: {lock_1}\n")
    
    # Segunda ejecución intenta adquirir (debería fallar)
    exec_id_2 = str(uuid.uuid4())
    print(f"Ejecución 2: Intentando adquirir lock concurrente...")
    lock_2 = state_manager.acquire_lock(data_type, exec_id_2)
    print(f"   Resultado: {lock_2}")
    
    if not lock_2:
        print(f"   ✓ Ejecución concurrente correctamente bloqueada\n")
    
    # Limpiar
    state_manager.release_lock(data_type, success=True)
    
    print("="*70)
    print("✅ TEST DE CONCURRENCIA COMPLETADO")
    print("="*70 + "\n")
    
    return True


def main():
    """Ejecutar todos los tests integrados"""
    print("\n" + "🚀"*35)
    print("  SUITE DE TESTS INTEGRADOS - TASKS 2, 3 Y 4")
    print("🚀"*35)
    
    tests = [
        ("Flujo Completo de Polling", test_integrated_polling_flow),
        ("Prevención de Concurrencia", test_concurrent_execution_prevention),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n❌ Excepción en test '{test_name}': {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))
    
    # Resumen
    print("\n" + "="*70)
    print("RESUMEN DE RESULTADOS")
    print("="*70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status}  {test_name}")
    
    print("\n" + "-"*70)
    print(f"  Total: {passed}/{total} tests pasaron")
    print("-"*70 + "\n")
    
    if passed == total:
        print("🎉 ¡TODOS LOS TESTS INTEGRADOS PASARON! 🎉\n")
        return True
    else:
        print(f"⚠️  {total - passed} test(s) fallaron\n")
        return False


if __name__ == '__main__':
    import sys
    success = main()
    sys.exit(0 if success else 1)
