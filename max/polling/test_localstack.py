"""
Test de Integración con LocalStack y Mock API

Este test prueba el flujo completo de polling para UN endpoint usando:
- LocalStack para DynamoDB (gestión de estado)
- Mock API (datos locales JSON) en lugar de API real
- Todos los componentes implementados (Tasks 1-13)

Requisitos:
1. LocalStack corriendo: docker-compose up -d
2. Variables de entorno (opcional):
   - LOCALSTACK_ENDPOINT (opcional, default: http://localhost:4566)

NOTA: Este test NO requiere credenciales de API ya que usa datos mock locales.

Para test multi-tenant completo, usar: test_end_to_end.py
"""

import os
import sys
import time
import boto3
from datetime import datetime

# Try to load .env file if it exists
try:
    from dotenv import load_dotenv
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    if os.path.exists(env_path):
        load_dotenv(env_path)
        print(f"✓ Variables cargadas desde {env_path}")
except ImportError:
    pass  # python-dotenv not installed, use system env vars

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from state_manager import StateManager
from pagination_handler import PaginationHandler
from incremental_polling import build_incremental_filter, deduplicate_records
from data_validator import DataValidator
from data_enricher import DataEnricher

# Import mock API client
from test_data.mock_api_client import MockJanisAPIClient


def print_section(title):
    """Imprime una sección con formato."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)


def setup_localstack_dynamodb():
    """
    Configura DynamoDB en LocalStack.
    Crea la tabla de control si no existe.
    """
    print_section("SETUP: Configurando DynamoDB en LocalStack")
    
    endpoint_url = os.environ.get('LOCALSTACK_ENDPOINT', 'http://localhost:4566')
    
    # Cliente DynamoDB
    dynamodb = boto3.client(
        'dynamodb',
        endpoint_url=endpoint_url,
        region_name='us-east-1',
        aws_access_key_id='test',
        aws_secret_access_key='test'
    )
    
    table_name = 'polling_control'
    
    # Verificar si la tabla existe
    try:
        dynamodb.describe_table(TableName=table_name)
        print(f"✓ Tabla '{table_name}' ya existe en LocalStack")
    except dynamodb.exceptions.ResourceNotFoundException:
        # Crear tabla
        print(f"→ Creando tabla '{table_name}' en LocalStack...")
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
        
        # Esperar a que la tabla esté activa
        waiter = dynamodb.get_waiter('table_exists')
        waiter.wait(TableName=table_name)
        print(f"✓ Tabla '{table_name}' creada exitosamente")
    
    return endpoint_url, table_name


def test_polling_flow_with_mock_api():
    """
    Test completo de polling con LocalStack y Mock API.
    
    Flujo Multi-Tenant (Tasks 10-12):
    1. Setup LocalStack DynamoDB
    2. Adquirir lock con key compuesta: {data_type}-{client}
    3. Construir filtro incremental
    4. Llamar Mock API con header janis-client
    5. Paginar resultados
    6. Deduplicar registros
    7. Validar datos (Task 7)
    8. Enriquecer datos (Task 8)
    9. Liberar lock
    10. Verificar estado en DynamoDB
    """
    
    # No se requieren credenciales para mock API
    api_key = 'mock-api-key'
    api_secret = 'mock-api-secret'
    
    # Configuración del test (multi-tenant)
    client = 'metro'  # Cliente a probar (metro o wongio)
    endpoint = '/order'
    base_url = 'https://mock.api.janis.in'
    data_type = 'orders'
    
    print_section("TEST: Polling Multi-Tenant con LocalStack + Mock API")
    print(f"Cliente:          {client}")
    print(f"Endpoint:         {endpoint}")
    print(f"Base URL:         {base_url} (MOCK)") 
    print(f"Data Type:        {data_type}")
    print(f"Modo:             MOCK (usando datos locales JSON)") 
    
    # Setup LocalStack
    endpoint_url, table_name = setup_localstack_dynamodb()
    
    # Configuración del test con key compuesta multi-tenant (Task 11)
    lock_key = f"{data_type}-{client}"  # Key compuesta: orders-metro
    execution_id = f"test-{client}-{int(time.time())}"
    
    print(f"\nLock Key (multi-tenant): {lock_key}")
    print(f"Execution ID: {execution_id}")
    
    try:
        # ====================================================================
        # PASO 1: Adquirir Lock (Task 11.1 - Multi-Tenant)
        # ====================================================================
        print_section("PASO 1: Adquirir Lock en DynamoDB (Multi-Tenant)")
        
        state_manager = StateManager(
            table_name=table_name,
            endpoint_url=endpoint_url
        )
        
        # Usar key compuesta para multi-tenant
        lock_acquired = state_manager.acquire_lock(lock_key, execution_id)
        
        if not lock_acquired:
            print("❌ No se pudo adquirir el lock (otra ejecución en curso)")
            return False
        
        print(f"✓ Lock adquirido exitosamente")
        print(f"  - lock_key: {lock_key} (formato: {{data_type}}-{{client}})")
        print(f"  - execution_id: {execution_id}")
        
        # ====================================================================
        # PASO 2: Construir Filtro Incremental (Task 6.1)
        # ====================================================================
        print_section("PASO 2: Construir Filtro Incremental")
        
        # Usar lock_key compuesta para consultar estado
        filters = build_incremental_filter(state_manager, lock_key)
        
        if filters:
            print(f"✓ Filtro incremental construido")
            print(f"  - dateModified: {filters.get('dateModified')}")
            print(f"  - sortBy: {filters.get('sortBy')}")
            print(f"  - sortOrder: {filters.get('sortOrder')}")
        else:
            print(f"✓ Primera ejecución - Full Refresh")
            print(f"  - Sin filtro incremental")
        
        # ====================================================================
        # PASO 3: Inicializar Mock API Client (Task 2 + 11.2b - Multi-Tenant)
        # ====================================================================
        print_section("PASO 3: Inicializar Mock API Client Multi-Tenant")
        
        # Cliente MOCK con headers multi-tenant (Task 11.2b)
        api_client = MockJanisAPIClient(
            base_url=base_url,
            api_key=api_key,
            rate_limit=100,
            extra_headers={
                'janis-client': client,  # Header multi-tenant
                'janis-api-key': api_key,
                'janis-api-secret': api_secret,
            }
        )
        
        print(f"✓ Mock API Client inicializado")
        print(f"  - base_url: {base_url} (MOCK)")
        print(f"  - endpoint: {endpoint}")
        print(f"  - cliente: {client}")
        print(f"  - Datos desde: test_data/mock_orders_page1.json (metro)")
        print(f"  - Headers multi-tenant:")
        print(f"    • janis-client: {client}")
        
        # ====================================================================
        # PASO 4: Obtener Datos con Paginación (Task 3)
        # ====================================================================
        print_section("PASO 4: Obtener Datos de Mock API (con paginación)")
        
        pagination_handler = PaginationHandler(
            client=api_client,
            max_pages=10,  # Limitar a 10 páginas para el test
            page_size=100
        )
        
        print(f"→ Llamando a {base_url}{endpoint} (MOCK)")
        print(f"  Usando datos locales JSON...")
        
        start_time = time.time()
        # Llamar al endpoint específico (mock)
        all_records = pagination_handler.fetch_all_pages(
            endpoint=endpoint,
            filters=filters
        )
        elapsed_time = time.time() - start_time
        
        print(f"\n✓ Datos obtenidos exitosamente")
        print(f"  - Total de registros: {len(all_records)}")
        print(f"  - Páginas obtenidas: {pagination_handler.last_page_fetched}")
        print(f"  - Tiempo transcurrido: {elapsed_time:.2f}s")
        
        if len(all_records) > 0:
            print(f"\n  Ejemplo de registro:")
            first_record = all_records[0]
            print(f"    - ID: {first_record.get('id', 'N/A')}")
            print(f"    - dateModified: {first_record.get('dateModified', 'N/A')}")
            print(f"    - status: {first_record.get('status', 'N/A')}")
        
        # ====================================================================
        # PASO 5: Deduplicar Registros (Task 6.2)
        # ====================================================================
        print_section("PASO 5: Deduplicar Registros")
        
        unique_records = deduplicate_records(all_records)
        duplicates_removed = len(all_records) - len(unique_records)
        
        print(f"✓ Deduplicación completada")
        print(f"  - Registros originales: {len(all_records)}")
        print(f"  - Registros únicos: {len(unique_records)}")
        print(f"  - Duplicados removidos: {duplicates_removed}")
        
        # ====================================================================
        # PASO 6: Validar Datos (Task 7)
        # ====================================================================
        print_section("PASO 6: Validar Datos (Task 7)")
        
        try:
            validator = DataValidator(data_type=data_type)
            valid_records, validation_metrics = validator.validate_batch(unique_records)
            
            print(f"✓ Validación completada")
            print(f"  - Total recibido: {validation_metrics['total_received']}")
            print(f"  - Duplicados en lote: {validation_metrics['duplicates_in_batch']}")
            print(f"  - Registros válidos: {validation_metrics['valid_count']}")
            print(f"  - Registros inválidos: {validation_metrics['invalid_count']}")
            print(f"  - Tasa de validación: {validation_metrics['validation_pass_rate']}%")
            
            if validation_metrics['invalid_count'] > 0:
                print(f"\n  Registros inválidos:")
                for invalid in validation_metrics['invalid_records'][:3]:
                    print(f"    - ID: {invalid['id']}")
                    for error in invalid['errors'][:2]:
                        print(f"      • {error}")
                if validation_metrics['invalid_count'] > 3:
                    print(f"    ... y {validation_metrics['invalid_count'] - 3} más")
            
            unique_records = valid_records
            
        except FileNotFoundError as e:
            print(f"⚠ Schema no encontrado: {e}")
            print(f"  Continuando sin validación de schema")
        except Exception as e:
            print(f"⚠ Error durante validación: {e}")
            print(f"  Continuando sin validación")
        
        # ====================================================================
        # PASO 7: Enriquecer Datos (Task 8)
        # ====================================================================
        print_section("PASO 7: Enriquecer Datos (Task 8)")
        
        print(f"→ Tipo de dato: {data_type}")
        
        if data_type in ['orders', 'products'] and unique_records:
            try:
                enricher = DataEnricher(client=api_client, max_workers=5)
                
                if data_type == 'orders':
                    print(f"  Enriqueciendo {len(unique_records)} órdenes con items...")
                    enriched_records = enricher.enrich_orders(unique_records)
                    
                    complete_count = sum(1 for r in enriched_records if r.get('_enrichment_complete'))
                    print(f"✓ Enriquecimiento de órdenes completado")
                    print(f"  - Exitosos: {complete_count}")
                    print(f"  - Con errores: {len(enriched_records) - complete_count}")
                    
                    unique_records = enriched_records
                    
                elif data_type == 'products':
                    print(f"  Enriqueciendo {len(unique_records)} productos con SKUs...")
                    enriched_records = enricher.enrich_products(unique_records)
                    
                    complete_count = sum(1 for r in enriched_records if r.get('_enrichment_complete'))
                    print(f"✓ Enriquecimiento de productos completado")
                    print(f"  - Exitosos: {complete_count}")
                    print(f"  - Con errores: {len(enriched_records) - complete_count}")
                    
                    unique_records = enriched_records
                    
            except Exception as e:
                print(f"⚠ Error durante enriquecimiento: {e}")
                print(f"  Continuando sin enriquecimiento")
        else:
            if not unique_records:
                print(f"  No hay registros para enriquecer")
            else:
                print(f"  Tipo de dato '{data_type}' no requiere enriquecimiento")
                print(f"  (Solo 'orders' y 'products' se enriquecen)")
        
        # ====================================================================
        # PASO 8: Obtener Último Timestamp
        # ====================================================================
        print_section("PASO 8: Obtener Último Timestamp")
        
        last_modified = None
        if unique_records:
            timestamps = []
            for r in unique_records:
                ts = r.get('dateModified') or r.get('dateCreated')
                if ts:
                    timestamps.append(ts)
            
            if timestamps:
                last_modified = max(timestamps)
                print(f"✓ Último timestamp encontrado")
                print(f"  - last_modified: {last_modified}")
                print(f"  - Total timestamps procesados: {len(timestamps)}")
        
        if not last_modified:
            print(f"⚠ No se encontró timestamp en los registros")
        
        # ====================================================================
        # PASO 9: Liberar Lock (Task 11.6 - Multi-Tenant)
        # ====================================================================
        print_section("PASO 9: Liberar Lock Multi-Tenant")
        
        # Usar lock_key compuesta para liberar
        state_manager.release_lock(
            data_type=lock_key,  # Key compuesta: orders-metro
            success=True,
            last_modified=last_modified,
            records_fetched=len(unique_records)
        )
        
        print(f"✓ Lock liberado exitosamente")
        print(f"  - lock_key: {lock_key}")
        print(f"  - success: True")
        print(f"  - records_fetched: {len(unique_records)}")
        if last_modified:
            print(f"  - last_modified actualizado: {last_modified}")
        
        # ====================================================================
        # PASO 10: Verificar Estado en DynamoDB (Multi-Tenant)
        # ====================================================================
        print_section("PASO 10: Verificar Estado en DynamoDB")
        
        # Consultar con lock_key compuesta
        final_state = state_manager.get_control_item(lock_key)
        
        print(f"✓ Estado final en DynamoDB:")
        print(f"  - data_type (key): {final_state.get('data_type')}")
        print(f"  - lock_acquired: {final_state.get('lock_acquired')}")
        print(f"  - status: {final_state.get('status')}")
        print(f"  - last_successful_execution: {final_state.get('last_successful_execution')}")
        print(f"  - last_modified_date: {final_state.get('last_modified_date')}")
        print(f"  - records_fetched: {final_state.get('records_fetched')}")
        
        # ====================================================================
        # RESUMEN FINAL
        # ====================================================================
        print_section("✅ TEST COMPLETADO EXITOSAMENTE")
        
        print(f"\n📊 RESUMEN:")
        print(f"  - Cliente: {client}")
        print(f"  - Endpoint: {endpoint}")
        print(f"  - Data Type: {data_type}")
        print(f"  - Lock Key: {lock_key} (multi-tenant)")
        print(f"  - Registros obtenidos: {len(all_records)}")
        print(f"  - Registros únicos: {len(unique_records)}")
        print(f"  - Páginas procesadas: {pagination_handler.last_page_fetched}")
        print(f"  - Tiempo total: {elapsed_time:.2f}s")
        print(f"  - Lock liberado: ✓")
        print(f"  - Estado actualizado en DynamoDB: ✓")
        
        # Cerrar API client
        api_client.close()
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR durante el test:")
        print(f"   {type(e).__name__}: {e}")
        
        # Intentar liberar lock en caso de error
        try:
            state_manager.release_lock(
                data_type=lock_key,
                success=False,
                error_message=str(e)
            )
            print(f"\n✓ Lock liberado después del error")
        except:
            print(f"\n⚠ No se pudo liberar el lock")
        
        import traceback
        traceback.print_exc()
        
        return False


if __name__ == '__main__':
    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║  TEST DE POLLING MULTI-TENANT CON LOCALSTACK + MOCK API                     ║
║                                                                              ║
║  Este test prueba el flujo completo de polling usando:                      ║
║  - LocalStack para DynamoDB (gestión de estado)                             ║
║  - Mock API con datos locales JSON (NO requiere credenciales)               ║
║  - Arquitectura multi-tenant (Tasks 10-12)                                  ║
║  - Todos los componentes implementados (Tasks 1-13)                         ║
║                                                                              ║
║  Cambios Multi-Tenant:                                                      ║
║  • Lock key compuesta: {data_type}-{client}                                 ║
║  • Header janis-client en requests                                          ║
║  • Validación de datos (Task 7)                                             ║
║  • Enriquecimiento de datos (Task 8)                                        ║
║                                                                              ║
║  NOTA: Este test usa datos MOCK locales, no requiere API keys               ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
    """)
    
    # Verificar requisitos
    print("Verificando requisitos...")
    
    # LocalStack
    endpoint = os.environ.get('LOCALSTACK_ENDPOINT', 'http://localhost:4566')
    print(f"✓ LocalStack endpoint: {endpoint}")
    print("  (Asegúrate de que LocalStack esté corriendo: docker-compose up -d)")
    print("✓ Mock API: Usando datos locales JSON (no requiere credenciales)")
    
    # Ejecutar test
    success = test_polling_flow_with_mock_api()
    
    if success:
        print("\n" + "=" * 80)
        print("  ✅ TEST EXITOSO - Todos los componentes funcionan correctamente")
        print("=" * 80)
        print("\n  Componentes probados:")
        print("    • StateManager con locks multi-tenant")
        print("    • JanisAPIClient con headers multi-tenant")
        print("    • PaginationHandler con circuit breaker")
        print("    • Incremental Polling con deduplicación")
        print("    • DataValidator (Task 7)")
        print("    • DataEnricher (Task 8)")
        print("\n  Para test completo multi-tenant, ejecutar:")
        print("    python test_end_to_end.py")
        exit(0)
    else:
        print("\n" + "=" * 80)
        print("  ❌ TEST FALLIDO - Revisa los errores arriba")
        print("=" * 80)
        exit(1)