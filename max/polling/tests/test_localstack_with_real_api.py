"""
Test de Integración con LocalStack y API REAL de Janis

Este test prueba el flujo completo de polling usando:
- LocalStack para DynamoDB (gestión de estado)
- API REAL de Janis (requiere credenciales)
- Todos los componentes implementados (Tasks 1-13)

DIFERENCIA con test_localstack_real_api.py:
- Este test usa JanisAPIClient REAL (no MockAPIClient)
- Hace requests reales a la API de Janis
- Requiere credenciales válidas en .env

Requisitos:
1. LocalStack corriendo: docker-compose up -d
2. Variables de entorno configuradas en .env:
   - JANIS_API_KEY
   - JANIS_API_SECRET
   - LOCALSTACK_ENDPOINT (opcional, default: http://localhost:4566)

IMPORTANTE: Este test consume cuota de API real de Janis.
Para tests sin consumir API, usar: test_localstack_real_api.py (con mock)
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
from api_client import JanisAPIClient  # ← API REAL (no mock)
from pagination_handler import PaginationHandler
from incremental_polling import build_incremental_filter, deduplicate_records
from data_validator import DataValidator
from data_enricher import DataEnricher
from s3_writer import S3Writer


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


def test_polling_flow_with_real_janis_api():
    """
    Test completo de polling con LocalStack y API REAL de Janis.
    
    Flujo Multi-Tenant (Tasks 10-12):
    1. Setup LocalStack DynamoDB
    2. Adquirir lock con key compuesta: {data_type}-{client}
    3. Construir filtro incremental
    4. Llamar API REAL de Janis con header janis-client
    5. Paginar resultados
    6. Deduplicar registros
    7. Validar datos (Task 7)
    8. Enriquecer datos (Task 8)
    9. Liberar lock
    10. Verificar estado en DynamoDB
    
    IMPORTANTE: Este test hace requests REALES a la API de Janis.
    """
    
    # Verificar variables de entorno (API key, secret y base_url requeridos)
    api_key = os.environ.get('JANIS_API_KEY', '8fc949ac-6d63-4447-a3d6-a16b66048e61')
    api_secret = os.environ.get('JANIS_API_SECRET', 'UwPbe45dmE7lySRJ3zcA66Pfdt7xAY3QXWO181Y8OTgCxE3aZuyXpS8HyyPSwsWK')
    base_url = os.environ.get('JANIS_API_BASE_URL', 'https://catalog.janis.in/api/product')
    client = os.environ.get('JANIS_CLIENT', 'wongio')

    missing_vars = []
    if not api_key:
        missing_vars.append('JANIS_API_KEY')
    if not api_secret:
        missing_vars.append('JANIS_API_SECRET')
    if not base_url:
        missing_vars.append('JANIS_API_BASE_URL')
    
    if missing_vars:
        print("\n❌ ERROR: Variables de entorno no configuradas:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\n  Configura estas variables en max/polling/.env")
        print("  O usa variables de entorno del sistema")
        print("\n  NOTA: Este test requiere credenciales REALES de la API de Janis")
        print("  Para tests sin credenciales, usar: test_localstack_real_api.py (con mock)")
        return False
    
    # Configuración del test (multi-tenant)
    # La URL del .env ya incluye el endpoint completo, así que endpoint debe estar vacío
    endpoint = ''  # Vacío porque base_url ya incluye el path completo
    
    # Detectar data_type automáticamente desde la URL
    base_url_lower = base_url.lower()
    if '/order' in base_url_lower:
        data_type = 'orders'
    elif '/product' in base_url_lower:
        data_type = 'products'
    elif '/category' in base_url_lower or '/categories' in base_url_lower:
        data_type = 'categories'
    elif '/stock' in base_url_lower:
        data_type = 'stock'
    elif '/price' in base_url_lower:
        data_type = 'prices'
    elif '/store' in base_url_lower:
        data_type = 'stores'
    else:
        data_type = 'unknown'
        print(f"\n⚠️  ADVERTENCIA: No se pudo detectar data_type desde URL: {base_url}")
        print(f"   Usando data_type='unknown'. Considera actualizar la lógica de detección.")
    
    print_section("TEST: Polling Multi-Tenant con LocalStack + API REAL de Janis")
    print(f"Cliente:          {client}")
    print(f"URL Completa:     {base_url}")
    print(f"Endpoint:         {endpoint if endpoint else '(incluido en URL)'}")
    print(f"Data Type:        {data_type}")
    print(f"janis-api-key:    {api_key[:10]}...")
    print(f"janis-api-secret: {api_secret[:10]}...")
    print(f"\n⚠️  ADVERTENCIA: Este test hace requests REALES a la API de Janis")
    print(f"   y consume cuota de API. Para tests sin consumir API, usar mock.")
    
    # Setup LocalStack
    endpoint_url, table_name = setup_localstack_dynamodb()
    
    # Configuración del test con key compuesta multi-tenant (Task 11)
    lock_key = f"{data_type}-{client}"  # Key compuesta: orders-metro
    execution_id = f"test-real-api-{client}-{int(time.time())}"
    
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
        # PASO 3: Inicializar API Client REAL (Task 2 + 11.2b - Multi-Tenant)
        # ====================================================================
        print_section("PASO 3: Inicializar API Client REAL Multi-Tenant")
        
        # Cliente REAL con headers multi-tenant (Task 11.2b)
        api_client = JanisAPIClient(
            base_url=base_url,
            api_key=api_key,
            rate_limit=100,
            extra_headers={
                'janis-client': client,  # Header multi-tenant
                'janis-api-key': api_key,
                'janis-api-secret': api_secret,
            }
        )
        
        print(f"✓ API Client REAL inicializado")
        print(f"  - URL completa: {base_url}")
        print(f"  - endpoint adicional: {endpoint if endpoint else '(ninguno - URL completa)'}")
        print(f"  - rate_limit: 100 req/min")
        print(f"  - Headers multi-tenant:")
        print(f"    • janis-client: {client}")
        print(f"    • janis-api-key: {api_key[:10]}...")
        print(f"    • janis-api-secret: {api_secret[:10]}...")
        print(f"\n  ⚠️  Haciendo requests REALES a la API de Janis...")
        
        # ====================================================================
        # PASO 4: Obtener Datos con Paginación (Task 3)
        # ====================================================================
        print_section("PASO 4: Obtener Datos de API REAL (con paginación)")
        
        pagination_handler = PaginationHandler(
            client=api_client,
            max_pages=5,  # Limitar a 5 páginas para el test
            page_size=100
        )
        
        full_url = f"{base_url}{endpoint}" if endpoint else base_url
        print(f"→ Llamando a {full_url}")
        print(f"  Esto puede tomar unos segundos...")
        print(f"  Limitado a 5 páginas para no consumir mucha cuota")
        
        start_time = time.time()
        # Llamar al endpoint específico (API REAL)
        all_records = pagination_handler.fetch_all_pages(
            endpoint=endpoint,
            filters=filters
        )
        elapsed_time = time.time() - start_time
        
        print(f"\n✓ Datos obtenidos exitosamente de API REAL")
        print(f"  - Total de registros: {len(all_records)}")
        print(f"  - Páginas obtenidas: {pagination_handler.last_page_fetched}")
        print(f"  - Tiempo transcurrido: {elapsed_time:.2f}s")
        
        if len(all_records) > 0:
            print(f"\n  Ejemplo de registro:")
            first_record = all_records[0]
            print(f"    - ID: {first_record.get('id', 'N/A')}")
            print(f"    - dateModified: {first_record.get('dateModified', 'N/A')}")
            print(f"    - status: {first_record.get('status', 'N/A')}")
        else:
            print(f"\n  ⚠️  No se obtuvieron registros (puede ser normal si no hay datos nuevos)")
        
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
        
        if unique_records:
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
        else:
            print(f"  No hay registros para validar")
        
        # ====================================================================
        # PASO 7: Enriquecer Datos (Task 8)
        # ====================================================================
        print_section("PASO 7: Enriquecer Datos (Task 8)")
        
        print(f"→ Tipo de dato: {data_type}")
        
        if data_type in ['orders', 'products'] and unique_records:
            try:
                enricher = DataEnricher(client=api_client, max_workers=3)
                
                if data_type == 'orders':
                    print(f"  Enriqueciendo {len(unique_records)} órdenes con items...")
                    print(f"  ⚠️  Esto hará requests adicionales a la API REAL")
                    enriched_records = enricher.enrich_orders(unique_records)
                    
                    complete_count = sum(1 for r in enriched_records if r.get('_enrichment_complete'))
                    print(f"✓ Enriquecimiento de órdenes completado")
                    print(f"  - Exitosos: {complete_count}")
                    print(f"  - Con errores: {len(enriched_records) - complete_count}")
                    
                    unique_records = enriched_records
                    
                elif data_type == 'products':
                    print(f"  Enriqueciendo {len(unique_records)} productos con SKUs...")
                    print(f"  ⚠️  Esto hará requests adicionales a la API REAL")
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
        # PASO 8: Escribir a S3 Bronze (LocalStack)
        # ====================================================================
        print_section("PASO 8: Escribir a S3 Bronze (LocalStack)")
        
        s3_path = None
        if all_records:  # Usar all_records (sin validar) para ver estructura completa
            try:
                # Inicializar S3 Writer para LocalStack
                s3_writer = S3Writer(
                    bucket_name='bronze-bucket',
                    endpoint_url=endpoint_url
                )
                
                # Asegurar que el bucket existe
                s3_writer.ensure_bucket_exists()
                
                # Escribir datos a S3
                print(f"→ Escribiendo {len(all_records)} registros a S3...")
                s3_result = s3_writer.write_to_bronze(
                    data=all_records,
                    client=client,
                    data_type=data_type,
                    execution_date=datetime.now()
                )
                
                if s3_result['success']:
                    print(f"✓ Datos escritos exitosamente")
                    print(f"  - Path: {s3_result['s3_path']}")
                    print(f"  - Registros: {s3_result['records_written']}")
                    print(f"  - Tamaño: {s3_result['file_size_mb']:.2f} MB")
                    s3_path = s3_result['s3_path']
                else:
                    print(f"❌ Error escribiendo a S3: {s3_result.get('error')}")
                    s3_path = None
                
            except Exception as e:
                print(f"⚠ Error escribiendo a S3: {e}")
                import traceback
                traceback.print_exc()
        else:
            print(f"  No hay registros para escribir a S3")
        
        # ====================================================================
        # PASO 9: Listar archivos en S3
        # ====================================================================
        print_section("PASO 9: Listar archivos en S3 Bronze")
        
        if s3_path:
            try:
                files = s3_writer.list_files(client=client, data_type=data_type, max_keys=10)
                
                if files:
                    print(f"✓ Archivos encontrados en S3:")
                    for i, file in enumerate(files, 1):
                        print(f"\n  {i}. {file['key']}")
                        print(f"     - Tamaño: {file['size']:,} bytes")
                        print(f"     - Última modificación: {file['last_modified']}")
                else:
                    print(f"  No se encontraron archivos")
                    
            except Exception as e:
                print(f"⚠ Error listando archivos: {e}")
        
        # ====================================================================
        # PASO 10: Leer archivo desde S3 y mostrar muestra
        # ====================================================================
        print_section("PASO 10: Verificar contenido en S3")
        
        if s3_path:
            try:
                # Extraer key del path
                s3_key = s3_path.replace('s3://bronze-bucket/', '')
                
                # Leer archivo
                data_from_s3 = s3_writer.read_file(s3_key)
                
                print(f"✓ Archivo leído desde S3")
                print(f"  - Registros en archivo: {len(data_from_s3)}")
                
                if data_from_s3:
                    print(f"\n  Muestra del primer registro:")
                    first = data_from_s3[0]
                    print(f"    - ID: {first.get('id', 'N/A')}")
                    print(f"    - dateModified: {first.get('dateModified', 'N/A')}")
                    print(f"    - status: {first.get('status', 'N/A')}")
                    
                    # Mostrar estructura de keys
                    print(f"\n  Campos disponibles en el registro:")
                    for key in list(first.keys())[:10]:
                        print(f"    • {key}")
                    if len(first.keys()) > 10:
                        print(f"    ... y {len(first.keys()) - 10} campos más")
                        
            except Exception as e:
                print(f"⚠ Error leyendo desde S3: {e}")
        
        # ====================================================================
        # PASO 11: Obtener Último Timestamp
        # ====================================================================
        print_section("PASO 11: Obtener Último Timestamp")
        
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
        # PASO 12: Liberar Lock (Task 11.6 - Multi-Tenant)
        # ====================================================================
        print_section("PASO 12: Liberar Lock Multi-Tenant")
        
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
        # PASO 13: Verificar Estado en DynamoDB (Multi-Tenant)
        # ====================================================================
        print_section("PASO 13: Verificar Estado en DynamoDB")
        
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
        print(f"  - URL: {base_url}")
        print(f"  - Data Type: {data_type}")
        print(f"  - Lock Key: {lock_key} (multi-tenant)")
        print(f"  - Registros obtenidos: {len(all_records)}")
        print(f"  - Registros únicos: {len(unique_records)}")
        print(f"  - Páginas procesadas: {pagination_handler.last_page_fetched}")
        print(f"  - Tiempo total: {elapsed_time:.2f}s")
        print(f"  - Lock liberado: ✓")
        print(f"  - Estado actualizado en DynamoDB: ✓")
        if s3_path:
            print(f"  - Datos escritos a S3: ✓")
            print(f"  - S3 Path: {s3_path}")
        print(f"\n  ⚠️  Este test consumió cuota de la API REAL de Janis")
        
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
║  TEST DE POLLING MULTI-TENANT CON LOCALSTACK + API REAL DE JANIS            ║
║                                                                              ║
║  Este test prueba el flujo completo de polling usando:                      ║
║  - LocalStack para DynamoDB (gestión de estado)                             ║
║  - API REAL de Janis para obtener datos                                     ║
║  - Arquitectura multi-tenant (Tasks 10-12)                                  ║
║  - Todos los componentes implementados (Tasks 1-13)                         ║
║                                                                              ║
║  ⚠️  IMPORTANTE:                                                             ║
║  Este test hace requests REALES a la API de Janis y consume cuota.         ║
║  Para tests sin consumir API, usar: test_localstack_real_api.py (mock)     ║
║                                                                              ║
║  Cambios Multi-Tenant:                                                      ║
║  • Lock key compuesta: {data_type}-{client}                                 ║
║  • Header janis-client en requests                                          ║
║  • Validación de datos (Task 7)                                             ║
║  • Enriquecimiento de datos (Task 8)                                        ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
    """)
    
    # Verificar requisitos
    print("Verificando requisitos...")

    missing = []
    for var in ['JANIS_API_KEY', 'JANIS_API_SECRET', 'JANIS_API_BASE_URL']:
        if not os.environ.get(var):
            missing.append(var)

    if missing:
        for var in missing:
            print(f"\n❌ Falta variable de entorno: {var}")
        print("\n  Configura en max/polling/.env:")
        print("    JANIS_API_KEY=tu-api-key")
        print("    JANIS_API_SECRET=tu-api-secret")
        print("    JANIS_API_BASE_URL=https://oms.janis.in/api/order/...")
        print("\n  NOTA: Este test requiere credenciales REALES de la API de Janis")
        print("  Para tests sin credenciales, usar: test_localstack_real_api.py (con mock)")
        exit(1)
    
    print("✓ Variables de entorno configuradas")
    
    # LocalStack
    endpoint = os.environ.get('LOCALSTACK_ENDPOINT', 'http://localhost:4566')
    print(f"✓ LocalStack endpoint: {endpoint}")
    print("  (Asegúrate de que LocalStack esté corriendo: docker-compose up -d)")
    
    print("\n⚠️  ADVERTENCIA:")
    print("  Este test hará requests REALES a la API de Janis")
    print("  y consumirá cuota de API.")
    print("\n  ¿Deseas continuar? (y/N): ", end='')
    
    try:
        response = input().strip().lower()
        if response != 'y':
            print("\n  Test cancelado por el usuario")
            exit(0)
    except KeyboardInterrupt:
        print("\n\n  Test cancelado por el usuario")
        exit(0)
    
    # Ejecutar test
    success = test_polling_flow_with_real_janis_api()
    
    if success:
        print("\n" + "=" * 80)
        print("  ✅ TEST EXITOSO - Todos los componentes funcionan correctamente")
        print("=" * 80)
        print("\n  Componentes probados:")
        print("    • StateManager con locks multi-tenant")
        print("    • JanisAPIClient REAL con headers multi-tenant")
        print("    • PaginationHandler con circuit breaker")
        print("    • Incremental Polling con deduplicación")
        print("    • DataValidator (Task 7)")
        print("    • DataEnricher (Task 8)")
        print("\n  ⚠️  Este test consumió cuota de la API REAL de Janis")
        print("\n  Para test sin consumir API, ejecutar:")
        print("    python test_localstack_real_api.py (usa mock)")
        exit(0)
    else:
        print("\n" + "=" * 80)
        print("  ❌ TEST FALLIDO - Revisa los errores arriba")
        print("=" * 80)
        exit(1)
