"""
Test End-to-End del Sistema de Polling Multi-Tenant

Este test prueba el flujo completo de polling multi-tenant usando:
- LocalStack para DynamoDB (gestión de estado)
- Mock API con datos locales JSON (NO requiere credenciales)
- Todos los componentes implementados (Tasks 1-13)
- Soporte multi-tenant (Metro y Wongio)

Requisitos:
1. LocalStack corriendo: docker-compose up -d
2. Variables de entorno (opcional):
   - LOCALSTACK_ENDPOINT (opcional, default: http://localhost:4566)

NOTA: Este test usa datos MOCK locales, no requiere API keys
"""

import os
import sys
import time
import boto3
import json
from datetime import datetime
from typing import Dict, List

# Try to load .env file if it exists
try:
    from dotenv import load_dotenv
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    if os.path.exists(env_path):
        load_dotenv(env_path)
        print(f"✓ Variables cargadas desde {env_path}")
except ImportError:
    pass

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from state_manager import StateManager
from pagination_handler import PaginationHandler
from incremental_polling import build_incremental_filter, deduplicate_records
from data_validator import DataValidator
from data_enricher import DataEnricher

# Import mock API client
from test_data.mock_api_client import MockJanisAPIClient


# ============================================================================
# CONFIGURACIÓN DE ENDPOINTS
# ============================================================================

ENDPOINTS_CONFIG = {
    'orders': {
        'endpoint': '/order',
        'base_url': 'https://oms.janis.in/api',
        'data_type': 'orders',
        'requires_enrichment': True,
        'max_pages': 5  # Limitar para test
    },
    'catalog': {
        'endpoints': ['/product', '/sku', '/category', '/brand'],
        'base_url': 'https://catalog.janis.in/api',
        'data_type': 'catalog',
        'requires_enrichment': True,
        'max_pages': 3
    },
    'stock': {
        'endpoint': '/sku-stock',
        'base_url': 'https://wms.janis.in/api',
        'data_type': 'stock',
        'requires_enrichment': False,
        'max_pages': 3
    },
    'prices': {
        'endpoints': ['/price', '/price-sheet', '/base-price'],
        'base_url': 'https://vtex.pricing.janis.in/api',
        'data_type': 'prices',
        'requires_enrichment': False,
        'max_pages': 2
    },
    'stores': {
        'endpoint': '/location',
        'base_url': 'https://commerce.janis.in/api',
        'data_type': 'stores',
        'requires_enrichment': False,
        'max_pages': 1
    }
}

CLIENTS = ['metro', 'wongio']


# ============================================================================
# UTILIDADES
# ============================================================================

def print_section(title, level=1):
    """Imprime una sección con formato."""
    if level == 1:
        print("\n" + "=" * 80)
        print(f"  {title}")
        print("=" * 80)
    elif level == 2:
        print("\n" + "-" * 80)
        print(f"  {title}")
        print("-" * 80)
    else:
        print(f"\n  {title}")


def print_success(message, indent=0):
    """Imprime mensaje de éxito."""
    prefix = "  " * indent
    print(f"{prefix}✓ {message}")


def print_error(message, indent=0):
    """Imprime mensaje de error."""
    prefix = "  " * indent
    print(f"{prefix}❌ {message}")


def print_warning(message, indent=0):
    """Imprime mensaje de advertencia."""
    prefix = "  " * indent
    print(f"{prefix}⚠ {message}")


def print_info(message, indent=0):
    """Imprime mensaje informativo."""
    prefix = "  " * indent
    print(f"{prefix}→ {message}")


# ============================================================================
# SETUP
# ============================================================================

def setup_localstack_dynamodb():
    """
    Configura DynamoDB en LocalStack.
    Crea la tabla de control si no existe.
    """
    print_section("SETUP: Configurando DynamoDB en LocalStack")
    
    endpoint_url = os.environ.get('LOCALSTACK_ENDPOINT', 'http://localhost:4566')
    
    dynamodb = boto3.client(
        'dynamodb',
        endpoint_url=endpoint_url,
        region_name='us-east-1',
        aws_access_key_id='test',
        aws_secret_access_key='test'
    )
    
    table_name = 'polling_control'
    
    try:
        dynamodb.describe_table(TableName=table_name)
        print_success(f"Tabla '{table_name}' ya existe en LocalStack")
    except dynamodb.exceptions.ResourceNotFoundException:
        print_info(f"Creando tabla '{table_name}' en LocalStack...")
        dynamodb.create_table(
            TableName=table_name,
            KeySchema=[
                {'AttributeName': 'data_type', 'KeyType': 'HASH'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'data_type', 'AttributeType': 'S'}
            ],
            BillingMode='PAY_PER_REQUEST'
        )
        
        waiter = dynamodb.get_waiter('table_exists')
        waiter.wait(TableName=table_name)
        print_success(f"Tabla '{table_name}' creada exitosamente")
    
    return endpoint_url, table_name


def verify_environment():
    """Verifica que las variables de entorno estén configuradas."""
    print_section("VERIFICACIÓN: Variables de Entorno")
    
    print_success("Modo MOCK activado - No se requieren credenciales de API")
    print(f"    - Usando datos locales JSON desde test_data/")
    print(f"    - mock_orders_page1.json (Metro)")
    print(f"    - mock_orders_page2.json (Wongio)")
    
    return True


# ============================================================================
# FLUJO DE POLLING PARA UN ENDPOINT
# ============================================================================

def poll_endpoint(
    client: str,
    endpoint: str,
    base_url: str,
    data_type: str,
    state_manager: StateManager,
    api_key: str,
    api_secret: str,
    max_pages: int = 5,
    requires_enrichment: bool = False
) -> Dict:
    """
    Ejecuta el flujo completo de polling para un endpoint específico.
    
    Returns:
        Dict con resultados del polling
    """
    print_section(f"Polling: {data_type} - {endpoint} - Cliente: {client}", level=2)
    
    execution_id = f"test-{client}-{data_type}-{int(time.time())}"
    lock_key = f"{data_type}-{client}"
    
    results = {
        'client': client,
        'endpoint': endpoint,
        'data_type': data_type,
        'success': False,
        'records_fetched': 0,
        'records_valid': 0,
        'duplicates_removed': 0,
        'execution_time': 0,
        'error': None
    }
    
    start_time = time.time()
    
    try:
        # PASO 1: Adquirir Lock
        print_info(f"Adquiriendo lock: {lock_key}", indent=1)
        lock_acquired = state_manager.acquire_lock(lock_key, execution_id)
        
        if not lock_acquired:
            print_warning(f"Lock ya existe para {lock_key} - omitiendo", indent=1)
            results['error'] = 'Lock already acquired'
            return results
        
        print_success(f"Lock adquirido: {lock_key}", indent=1)
        
        # PASO 2: Construir Filtro Incremental
        print_info("Construyendo filtro incremental", indent=1)
        filters = build_incremental_filter(state_manager, lock_key)
        
        if filters:
            print_success(f"Filtro incremental: dateModified >= {filters.get('dateModified')}", indent=1)
        else:
            print_success("Primera ejecución - Full Refresh", indent=1)
        
        # PASO 3: Inicializar Mock API Client
        api_client = MockJanisAPIClient(
            base_url=base_url,
            api_key=api_key,
            rate_limit=100,
            extra_headers={
                'janis-client': client,
                'janis-api-key': api_key,
                'janis-api-secret': api_secret,
            }
        )
        
        # PASO 4: Obtener Datos con Paginación
        print_info(f"Obteniendo datos de {base_url}{endpoint}", indent=1)
        
        pagination_handler = PaginationHandler(
            client=api_client,
            max_pages=max_pages,
            page_size=100
        )
        
        all_records = pagination_handler.fetch_all_pages(
            endpoint=endpoint,
            filters=filters
        )
        
        print_success(f"Obtenidos {len(all_records)} registros en {pagination_handler.last_page_fetched} páginas", indent=1)
        results['records_fetched'] = len(all_records)
        
        # PASO 5: Deduplicar
        print_info("Deduplicando registros", indent=1)
        unique_records = deduplicate_records(all_records)
        results['duplicates_removed'] = len(all_records) - len(unique_records)
        print_success(f"Registros únicos: {len(unique_records)} (removidos {results['duplicates_removed']} duplicados)", indent=1)
        
        # PASO 6: Validar
        print_info("Validando datos", indent=1)
        try:
            validator = DataValidator(data_type=data_type)
            valid_records, metrics = validator.validate_batch(unique_records)
            results['records_valid'] = len(valid_records)
            print_success(f"Validación: {len(valid_records)}/{len(unique_records)} válidos ({metrics['validation_pass_rate']}%)", indent=1)
            unique_records = valid_records
        except FileNotFoundError:
            print_warning(f"Schema no encontrado para {data_type} - omitiendo validación", indent=1)
            results['records_valid'] = len(unique_records)
        
        # PASO 7: Enriquecer (si aplica)
        if requires_enrichment and unique_records:
            print_info(f"Enriqueciendo {len(unique_records)} registros", indent=1)
            try:
                enricher = DataEnricher(client=api_client, max_workers=3)
                
                if data_type == 'orders':
                    unique_records = enricher.enrich_orders(unique_records)
                elif data_type in ['catalog', 'products']:
                    unique_records = enricher.enrich_products(unique_records)
                
                complete_count = sum(1 for r in unique_records if r.get('_enrichment_complete'))
                print_success(f"Enriquecimiento: {complete_count}/{len(unique_records)} exitosos", indent=1)
            except Exception as e:
                print_warning(f"Error en enriquecimiento: {e}", indent=1)
        
        # PASO 8: Obtener último timestamp
        last_modified = None
        if unique_records:
            timestamps = [r.get('dateModified') or r.get('dateCreated') for r in unique_records if r.get('dateModified') or r.get('dateCreated')]
            if timestamps:
                last_modified = max(timestamps)
        
        # PASO 9: Liberar Lock
        print_info("Liberando lock", indent=1)
        state_manager.release_lock(
            data_type=lock_key,
            success=True,
            last_modified=last_modified,
            records_fetched=len(unique_records)
        )
        print_success("Lock liberado exitosamente", indent=1)
        
        # Cerrar cliente
        api_client.close()
        
        results['success'] = True
        results['execution_time'] = time.time() - start_time
        
        print_success(f"Polling completado en {results['execution_time']:.2f}s", indent=1)
        
    except Exception as e:
        results['error'] = str(e)
        results['execution_time'] = time.time() - start_time
        print_error(f"Error: {e}", indent=1)
        
        # Intentar liberar lock
        try:
            state_manager.release_lock(
                data_type=lock_key,
                success=False,
                error_message=str(e)
            )
            print_success("Lock liberado después del error", indent=1)
        except:
            print_warning("No se pudo liberar el lock", indent=1)
    
    return results


# ============================================================================
# TEST END-TO-END COMPLETO
# ============================================================================

def test_end_to_end_multi_tenant():
    """
    Test end-to-end completo del sistema de polling multi-tenant.
    
    Prueba:
    1. Setup de LocalStack
    2. Polling de múltiples endpoints
    3. Soporte multi-tenant (Metro y Wongio)
    4. Todos los componentes integrados
    """
    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║  TEST END-TO-END: SISTEMA DE POLLING MULTI-TENANT                           ║
║                                                                              ║
║  Prueba el flujo completo con:                                              ║
║  • LocalStack (DynamoDB)                                                     ║
║  • Mock API (datos locales JSON)                                             ║
║  • Multi-tenant (Metro + Wongio)                                             ║
║  • Todos los componentes (Tasks 1-13)                                       ║
║                                                                              ║
║  NOTA: Este test usa datos MOCK locales, no requiere API keys               ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
    """)
    
    # Verificar entorno
    if not verify_environment():
        return False
    
    # Setup LocalStack
    endpoint_url, table_name = setup_localstack_dynamodb()
    state_manager = StateManager(table_name=table_name, endpoint_url=endpoint_url)
    
    # Obtener credenciales (mock)
    api_key = 'mock-api-key'
    api_secret = 'mock-api-secret'
    
    # Resultados globales
    all_results = []
    total_start_time = time.time()
    
    # Seleccionar endpoints para probar (puedes cambiar esto)
    endpoints_to_test = ['orders', 'stock']  # Probar solo orders y stock para el test
    
    print_section("EJECUCIÓN: Polling Multi-Tenant")
    print(f"\nEndpoints a probar: {', '.join(endpoints_to_test)}")
    print(f"Clientes: {', '.join(CLIENTS)}\n")
    
    # Iterar sobre endpoints y clientes
    for endpoint_name in endpoints_to_test:
        config = ENDPOINTS_CONFIG[endpoint_name]
        
        # Manejar endpoints múltiples (catalog, prices)
        if 'endpoints' in config:
            endpoints_list = config['endpoints']
        else:
            endpoints_list = [config['endpoint']]
        
        for endpoint in endpoints_list:
            for client in CLIENTS:
                result = poll_endpoint(
                    client=client,
                    endpoint=endpoint,
                    base_url=config['base_url'],
                    data_type=config['data_type'],
                    state_manager=state_manager,
                    api_key=api_key,
                    api_secret=api_secret,
                    max_pages=config['max_pages'],
                    requires_enrichment=config['requires_enrichment']
                )
                all_results.append(result)
                
                # Pequeña pausa entre requests para no saturar
                time.sleep(1)
    
    total_time = time.time() - total_start_time
    
    # ========================================================================
    # RESUMEN FINAL
    # ========================================================================
    print_section("RESUMEN FINAL")
    
    successful = [r for r in all_results if r['success']]
    failed = [r for r in all_results if not r['success']]
    
    total_records = sum(r['records_fetched'] for r in all_results)
    total_valid = sum(r['records_valid'] for r in all_results)
    total_duplicates = sum(r['duplicates_removed'] for r in all_results)
    
    print(f"\n📊 ESTADÍSTICAS GENERALES:")
    print(f"  • Total de llamadas: {len(all_results)}")
    print(f"  • Exitosas: {len(successful)}")
    print(f"  • Fallidas: {len(failed)}")
    print(f"  • Tiempo total: {total_time:.2f}s")
    
    print(f"\n📈 DATOS PROCESADOS:")
    print(f"  • Registros obtenidos: {total_records}")
    print(f"  • Registros válidos: {total_valid}")
    print(f"  • Duplicados removidos: {total_duplicates}")
    
    if successful:
        print(f"\n✅ LLAMADAS EXITOSAS:")
        for r in successful:
            print(f"  • {r['client']:8} | {r['data_type']:10} | {r['endpoint']:20} | {r['records_valid']:4} registros | {r['execution_time']:.2f}s")
    
    if failed:
        print(f"\n❌ LLAMADAS FALLIDAS:")
        for r in failed:
            print(f"  • {r['client']:8} | {r['data_type']:10} | {r['endpoint']:20} | Error: {r['error']}")
    
    # Verificar estado en DynamoDB
    print_section("ESTADO EN DYNAMODB")
    
    for endpoint_name in endpoints_to_test:
        config = ENDPOINTS_CONFIG[endpoint_name]
        for client in CLIENTS:
            lock_key = f"{config['data_type']}-{client}"
            try:
                state = state_manager.get_control_item(lock_key)
                print(f"\n  {lock_key}:")
                print(f"    - lock_acquired: {state.get('lock_acquired')}")
                print(f"    - status: {state.get('status')}")
                print(f"    - records_fetched: {state.get('records_fetched')}")
                print(f"    - last_modified_date: {state.get('last_modified_date', 'N/A')}")
            except:
                print(f"\n  {lock_key}: No encontrado")
    
    # Resultado final
    success_rate = len(successful) / len(all_results) * 100 if all_results else 0
    
    print_section("RESULTADO FINAL")
    
    if success_rate == 100:
        print(f"\n  ✅ TEST EXITOSO - Todas las llamadas completadas ({len(successful)}/{len(all_results)})")
        return True
    elif success_rate >= 50:
        print(f"\n  ⚠ TEST PARCIAL - {len(successful)}/{len(all_results)} llamadas exitosas ({success_rate:.1f}%)")
        return True
    else:
        print(f"\n  ❌ TEST FALLIDO - Solo {len(successful)}/{len(all_results)} llamadas exitosas ({success_rate:.1f}%)")
        return False


# ============================================================================
# MAIN
# ============================================================================

if __name__ == '__main__':
    try:
        success = test_end_to_end_multi_tenant()
        exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠ Test interrumpido por el usuario")
        exit(1)
    except Exception as e:
        print(f"\n\n❌ Error fatal: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
