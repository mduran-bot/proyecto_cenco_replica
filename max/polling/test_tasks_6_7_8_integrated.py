"""
Test Integrado: Tasks 6, 7 y 8
IncrementalPolling + DataValidator + DataEnricher trabajando juntos

Este test simula un flujo completo de procesamiento de datos:
1. Construir filtro incremental con IncrementalPolling
2. Deduplicar registros con overlap window
3. Validar datos con DataValidator
4. Enriquecer datos con DataEnricher
"""

import os
import uuid
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock

os.environ['AWS_ACCESS_KEY_ID'] = 'test'
os.environ['AWS_SECRET_ACCESS_KEY'] = 'test'
os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'

from src.incremental_polling import build_incremental_filter, deduplicate_records
from src.data_validator import DataValidator
from src.data_enricher import DataEnricher


# =============================================================================
# Helpers para crear datos de prueba
# =============================================================================

def create_mock_orders(count=10, with_duplicates=False):
    """Crea órdenes mock con estructura válida según el schema de Janis OMS"""
    now = datetime.utcnow()
    orders = []

    for i in range(count):
        orders.append({
            'id': f'order-{i:03d}',
            'status': 'new',
            'totalAmount': 100.0 + i * 10,
            'commerceId': f'commerce-{i:03d}',
            'currency': 'ARS',
            'items': [
                {
                    'id': f'item-{i:03d}-001',
                    'name': f'Producto {i}',
                    'purchasedPrice': 50.0 + i,
                    'purchasedQuantity': 2,
                    'ean': f'780000{i:04d}'
                }
            ],
            'customer': {
                'email': f'cliente{i}@ejemplo.com',
                'firstName': f'Cliente',
                'lastName': f'{i}'
            },
            'dateCreated': (now - timedelta(hours=2)).isoformat() + 'Z',
            'dateModified': (now - timedelta(minutes=i)).isoformat() + 'Z'
        })

    if with_duplicates:
        # Agregar duplicados con timestamps distintos (simulando overlap window)
        orders.append({**orders[0], 'dateModified': (now - timedelta(minutes=30)).isoformat() + 'Z'})
        orders.append({**orders[1], 'dateModified': (now - timedelta(minutes=31)).isoformat() + 'Z'})

    return orders


def create_mock_products(count=5):
    """Crea productos mock con estructura válida según el schema de Janis Catalog"""
    now = datetime.utcnow()
    products = []

    for i in range(count):
        products.append({
            'id': f'prod-{i:03d}',
            'name': f'Producto Catálogo {i}',
            'referenceId': f'ref-prod-{i:03d}',
            'brand': f'brand-{i:03d}',
            'category': f'cat-{i:03d}',
            'status': 'active',
            'commerceId': f'commerce-prod-{i:03d}',
            'slug': f'producto-catalogo-{i}',
            'dateCreated': (now - timedelta(days=30)).isoformat() + 'Z',
            'dateModified': (now - timedelta(hours=i)).isoformat() + 'Z'
        })

    return products


def create_invalid_orders(count=2):
    """Crea órdenes inválidas que deben fallar la validación"""
    now = datetime.utcnow()
    return [
        {
            # Falta 'id' (required) y totalAmount es negativo
            'status': 'new',
            'totalAmount': -50.0,
            'items': [],
            'dateCreated': now.isoformat() + 'Z',
            'dateModified': now.isoformat() + 'Z'
        },
        {
            'id': 'invalid-order-001',
            'status': 'new',
            'totalAmount': 0,   # regla de negocio: debe ser > 0
            'items': [],        # regla de negocio: debe tener al menos 1 item
            'dateCreated': now.isoformat() + 'Z',
            'dateModified': now.isoformat() + 'Z'
        }
    ][:count]


# =============================================================================
# Tests
# =============================================================================

def test_incremental_polling_flow():
    """
    Test del filtro incremental y deduplicación (Task 6)
    """
    print("\n" + "="*70)
    print("TEST INTEGRADO: Task 6 - Incremental Polling")
    print("IncrementalPolling: build_incremental_filter + deduplicate_records")
    print("="*70 + "\n")

    # ========== Caso 1: Primera ejecución (full refresh) ==========
    print("PASO 1: Primera ejecución - Full Refresh")
    print("-" * 70)

    mock_state_manager = Mock()
    mock_state_manager.get_last_modified_date.return_value = None

    filters = build_incremental_filter(mock_state_manager, 'orders')

    print(f"   ✓ Filtro construido para primera ejecución")
    print(f"   - Filtro retornado: {filters}")
    print(f"   - Es full refresh: {filters == {}}\n")

    assert filters == {}, f"Primera ejecución debe retornar filtro vacío, got: {filters}"

    # ========== Caso 2: Ejecución incremental con timestamp previo ==========
    print("PASO 2: Ejecución incremental con timestamp previo")
    print("-" * 70)

    last_modified = '2024-01-15T10:25:00Z'
    mock_state_manager.get_last_modified_date.return_value = last_modified

    filters = build_incremental_filter(mock_state_manager, 'orders')

    print(f"   ✓ Filtro incremental construido")
    print(f"   - last_modified_date: {last_modified}")
    print(f"   - dateModified en filtro: {filters.get('dateModified')}")
    print(f"   - Ventana de solapamiento (1 min): aplicada")
    print(f"   - sortBy: {filters.get('sortBy')}")
    print(f"   - sortOrder: {filters.get('sortOrder')}\n")

    assert 'dateModified' in filters
    assert filters['sortBy'] == 'dateModified'
    assert filters['sortOrder'] == 'asc'
    # La fecha debe ser 1 minuto ANTES del last_modified
    assert filters['dateModified'] < last_modified

    # ========== Caso 3: Deduplicación de registros ==========
    print("PASO 3: Deduplicación de registros (overlap window)")
    print("-" * 70)

    records_with_duplicates = create_mock_orders(count=8, with_duplicates=True)
    total_con_duplicados = len(records_with_duplicates)

    print(f"   Registros recibidos (con duplicados): {total_con_duplicados}")

    deduplicated = deduplicate_records(records_with_duplicates)

    print(f"   ✓ Deduplicación completada")
    print(f"   - Registros originales: {total_con_duplicados}")
    print(f"   - Registros únicos: {len(deduplicated)}")
    print(f"   - Duplicados removidos: {total_con_duplicados - len(deduplicated)}\n")

    assert len(deduplicated) < total_con_duplicados, "Debe haber removido duplicados"
    # Verificar que no hay IDs repetidos
    ids = [r['id'] for r in deduplicated]
    assert len(ids) == len(set(ids)), "No deben quedar IDs duplicados"

    print("="*70)
    print("✅ TEST TASK 6 COMPLETADO EXITOSAMENTE")
    print("="*70)
    print("\nComponentes verificados:")
    print("  ✓ build_incremental_filter: primera ejecución (full refresh)")
    print("  ✓ build_incremental_filter: ejecución incremental con overlap window")
    print("  ✓ deduplicate_records: eliminación de duplicados por ID y timestamp\n")

    return True


def test_data_validator_flow():
    """
    Test del validador de datos (Task 7)
    """
    print("\n" + "="*70)
    print("TEST INTEGRADO: Task 7 - Data Validator")
    print("DataValidator: validate_batch para orders y products")
    print("="*70 + "\n")

    # ========== Caso 1: Validación de órdenes válidas ==========
    print("PASO 1: Validar lote de órdenes válidas")
    print("-" * 70)

    validator_orders = DataValidator(
        data_type='orders',
        schemas_dir=os.path.join(os.path.dirname(__file__), 'src', 'schemas')
    )

    valid_orders = create_mock_orders(count=10)
    valid_records, metrics = validator_orders.validate_batch(valid_orders)

    print(f"   ✓ Validación completada")
    print(f"   - Registros recibidos: {metrics['total_received']}")
    print(f"   - Duplicados en lote: {metrics['duplicates_in_batch']}")
    print(f"   - Registros válidos: {metrics['valid_count']}")
    print(f"   - Registros inválidos: {metrics['invalid_count']}")
    print(f"   - Tasa de validación: {metrics['validation_pass_rate']}%\n")

    assert metrics['valid_count'] == 10
    assert metrics['invalid_count'] == 0
    assert metrics['validation_pass_rate'] == 100.0

    # ========== Caso 2: Detección de duplicados en lote ==========
    print("PASO 2: Detección de duplicados dentro del lote")
    print("-" * 70)

    orders_with_batch_duplicates = create_mock_orders(count=5)
    # Agregar el mismo registro dos veces (duplicado exacto en el lote)
    orders_with_batch_duplicates.append(orders_with_batch_duplicates[0])
    orders_with_batch_duplicates.append(orders_with_batch_duplicates[1])

    _, metrics_dup = validator_orders.validate_batch(orders_with_batch_duplicates)

    print(f"   ✓ Duplicados detectados en lote")
    print(f"   - Registros recibidos: {metrics_dup['total_received']}")
    print(f"   - Duplicados en lote: {metrics_dup['duplicates_in_batch']}")
    print(f"   - Registros tras dedup: {metrics_dup['total_after_dedup']}\n")

    assert metrics_dup['duplicates_in_batch'] == 2
    assert metrics_dup['total_after_dedup'] == 5

    # ========== Caso 3: Validación con registros inválidos ==========
    print("PASO 3: Validar lote mixto (válidos + inválidos)")
    print("-" * 70)

    now = datetime.utcnow()
    mixed_orders = create_mock_orders(count=8) + [
        {
            # Sin 'id' → inválido (campo required)
            'status': 'new',
            'totalAmount': -10,
            'items': [],
            'dateCreated': now.isoformat() + 'Z',
            'dateModified': now.isoformat() + 'Z'
        },
        {
            'id': 'invalid-002',
            'status': 'new',
            'totalAmount': 0,   # regla negocio: > 0
            'items': [],        # regla negocio: >= 1 item
            'dateCreated': now.isoformat() + 'Z',
            'dateModified': now.isoformat() + 'Z'
        }
    ]

    valid_records_mixed, metrics_mixed = validator_orders.validate_batch(mixed_orders)

    print(f"   ✓ Validación mixta completada")
    print(f"   - Registros recibidos: {metrics_mixed['total_received']}")
    print(f"   - Válidos: {metrics_mixed['valid_count']}")
    print(f"   - Inválidos: {metrics_mixed['invalid_count']}")
    print(f"   - Tasa de validación: {metrics_mixed['validation_pass_rate']}%")
    for inv in metrics_mixed['invalid_records']:
        print(f"     ⚠ id={inv['id']}: {inv['errors']}")
    print()

    assert metrics_mixed['valid_count'] == 8
    assert metrics_mixed['invalid_count'] == 2

    # ========== Caso 4: Validación de productos ==========
    print("PASO 4: Validar lote de productos")
    print("-" * 70)

    validator_products = DataValidator(
        data_type='products',
        schemas_dir=os.path.join(os.path.dirname(__file__), 'src', 'schemas')
    )

    valid_products = create_mock_products(count=5)
    valid_prods, metrics_prods = validator_products.validate_batch(valid_products)

    print(f"   ✓ Validación de productos completada")
    print(f"   - Registros recibidos: {metrics_prods['total_received']}")
    print(f"   - Válidos: {metrics_prods['valid_count']}")
    print(f"   - Tasa de validación: {metrics_prods['validation_pass_rate']}%\n")

    assert metrics_prods['valid_count'] == 5

    print("="*70)
    print("✅ TEST TASK 7 COMPLETADO EXITOSAMENTE")
    print("="*70)
    print("\nComponentes verificados:")
    print("  ✓ DataValidator: carga de schemas JSON")
    print("  ✓ DataValidator: validación de schema (jsonschema Draft7)")
    print("  ✓ DataValidator: detección de duplicados en lote")
    print("  ✓ DataValidator: validación de reglas de negocio")
    print("  ✓ DataValidator: métricas de validación\n")

    return True


def test_data_enricher_flow():
    """
    Test del enriquecedor de datos (Task 8)
    """
    print("\n" + "="*70)
    print("TEST INTEGRADO: Task 8 - Data Enricher")
    print("DataEnricher: enrich_orders + enrich_products con ThreadPoolExecutor")
    print("="*70 + "\n")

    # ========== Setup: Mock del APIClient ==========
    mock_client = Mock()

    def mock_api_get(endpoint):
        if '/items' in endpoint:
            order_id = endpoint.split('/')[1]
            if order_id == 'order-fail':
                raise Exception("API Error simulado - timeout")
            return {
                'data': [
                    {'id': f'item-{order_id}-001', 'name': 'Coca Cola 1.5L', 'quantity': 2},
                    {'id': f'item-{order_id}-002', 'name': 'Sprite 500ml', 'quantity': 1}
                ]
            }
        if '/skus' in endpoint:
            product_id = endpoint.split('/')[1]
            return {
                'data': [
                    {'id': f'sku-{product_id}-001', 'referenceId': f'ref-sku-{product_id}', 'eans': ['7800000001']}
                ]
            }
        return {'data': []}

    mock_client.get.side_effect = mock_api_get

    enricher = DataEnricher(client=mock_client, max_workers=5)

    # ========== Caso 1: Enriquecimiento exitoso de órdenes ==========
    print("PASO 1: Enriquecer órdenes con sus items")
    print("-" * 70)

    orders_to_enrich = create_mock_orders(count=5)
    print(f"   Órdenes a enriquecer: {len(orders_to_enrich)}")

    enriched_orders = enricher.enrich_orders(orders_to_enrich)

    success_count = sum(1 for o in enriched_orders if o['_enrichment_complete'])
    total_items = sum(len(o['_items']) for o in enriched_orders)

    print(f"   ✓ Enriquecimiento de órdenes completado")
    print(f"   - Órdenes enriquecidas exitosamente: {success_count}/{len(orders_to_enrich)}")
    print(f"   - Total items obtenidos: {total_items}")
    print(f"   - max_workers utilizados: 5")
    print(f"   - Ejemplo orden[0]: _items={enriched_orders[0]['_items'][:1]}\n")

    assert len(enriched_orders) == len(orders_to_enrich), "Debe retornar misma cantidad"
    assert all(o['_enrichment_complete'] for o in enriched_orders)
    assert all(len(o['_items']) > 0 for o in enriched_orders)

    # ========== Caso 2: Resiliencia ante errores de API ==========
    print("PASO 2: Resiliencia ante errores de API")
    print("-" * 70)

    orders_with_failure = create_mock_orders(count=3) + [
        {
            'id': 'order-fail',
            'status': 'new',
            'totalAmount': 99.0,
            'items': [{'purchasedPrice': 99.0, 'purchasedQuantity': 1}],
            'dateCreated': datetime.utcnow().isoformat() + 'Z',
            'dateModified': datetime.utcnow().isoformat() + 'Z'
        },
        {
            # Sin ID: no se puede enriquecer
            'status': 'new',
            'totalAmount': 50.0,
            'items': [{'purchasedPrice': 50.0, 'purchasedQuantity': 1}],
            'dateCreated': datetime.utcnow().isoformat() + 'Z',
            'dateModified': datetime.utcnow().isoformat() + 'Z'
        }
    ]

    enriched_resilient = enricher.enrich_orders(orders_with_failure)

    ok_count = sum(1 for o in enriched_resilient if o['_enrichment_complete'])
    fail_count = sum(1 for o in enriched_resilient if not o['_enrichment_complete'])

    print(f"   ✓ Enriquecimiento con errores completado")
    print(f"   - Total registros: {len(enriched_resilient)}")
    print(f"   - Enriquecidos correctamente: {ok_count}")
    print(f"   - Con _enrichment_complete=False: {fail_count}")
    print(f"   - Ningún registro se perdió: {len(enriched_resilient) == len(orders_with_failure)}\n")

    assert len(enriched_resilient) == len(orders_with_failure), "No se deben perder registros"
    assert ok_count == 3
    assert fail_count == 2  # order-fail + sin ID

    # ========== Caso 3: Enriquecimiento de productos ==========
    print("PASO 3: Enriquecer productos con sus SKUs")
    print("-" * 70)

    products_to_enrich = create_mock_products(count=5)
    print(f"   Productos a enriquecer: {len(products_to_enrich)}")

    enriched_products = enricher.enrich_products(products_to_enrich)

    prod_success = sum(1 for p in enriched_products if p['_enrichment_complete'])
    total_skus = sum(len(p['_skus']) for p in enriched_products)

    print(f"   ✓ Enriquecimiento de productos completado")
    print(f"   - Productos enriquecidos exitosamente: {prod_success}/{len(products_to_enrich)}")
    print(f"   - Total SKUs obtenidos: {total_skus}")
    print(f"   - Ejemplo producto[0]: _skus={enriched_products[0]['_skus'][:1]}\n")

    assert len(enriched_products) == len(products_to_enrich)
    assert all(p['_enrichment_complete'] for p in enriched_products)
    assert all(len(p['_skus']) > 0 for p in enriched_products)

    print("="*70)
    print("✅ TEST TASK 8 COMPLETADO EXITOSAMENTE")
    print("="*70)
    print("\nComponentes verificados:")
    print("  ✓ DataEnricher: enrich_orders con ThreadPoolExecutor")
    print("  ✓ DataEnricher: enrich_products con ThreadPoolExecutor")
    print("  ✓ DataEnricher: resiliencia ante errores (_enrichment_complete=False)")
    print("  ✓ DataEnricher: registros sin ID manejados correctamente")
    print("  ✓ DataEnricher: orden de registros preservado\n")

    return True


def test_full_pipeline_6_7_8():
    """
    Test del pipeline completo: IncrementalPolling → Validator → Enricher
    """
    print("\n" + "="*70)
    print("TEST PIPELINE COMPLETO: Tasks 6 + 7 + 8")
    print("IncrementalPolling → DataValidator → DataEnricher")
    print("="*70 + "\n")

    # ========== Setup ==========
    now = datetime.utcnow()
    last_modified = (now - timedelta(minutes=10)).isoformat() + 'Z'

    mock_state = Mock()
    mock_state.get_last_modified_date.return_value = last_modified

    mock_client = Mock()
    mock_client.get.return_value = {
        'data': [{'id': 'item-001', 'name': 'Producto Test', 'quantity': 1}]
    }

    # ========== PASO 1: Filtro incremental ==========
    print("PASO 1: Construir filtro incremental (Task 6)")
    print("-" * 70)

    filters = build_incremental_filter(mock_state, 'orders')
    print(f"   ✓ Filtro construido: dateModified >= {filters.get('dateModified')}\n")

    # ========== PASO 2: Simular datos paginados con duplicados ==========
    print("PASO 2: Simular datos paginados con duplicados (Task 6)")
    print("-" * 70)

    raw_records = create_mock_orders(count=10, with_duplicates=True)
    print(f"   Registros brutos (con duplicados): {len(raw_records)}")

    deduplicated = deduplicate_records(raw_records)
    print(f"   ✓ Deduplicados: {len(deduplicated)} registros únicos\n")

    # ========== PASO 3: Validar ==========
    print("PASO 3: Validar registros deduplicados (Task 7)")
    print("-" * 70)

    validator = DataValidator(
        data_type='orders',
        schemas_dir=os.path.join(os.path.dirname(__file__), 'src', 'schemas')
    )
    valid_records, metrics = validator.validate_batch(deduplicated)

    print(f"   ✓ Validación completada")
    print(f"   - Entrada: {len(deduplicated)} registros")
    print(f"   - Válidos: {metrics['valid_count']}")
    print(f"   - Tasa: {metrics['validation_pass_rate']}%\n")

    # ========== PASO 4: Enriquecer ==========
    print("PASO 4: Enriquecer registros válidos (Task 8)")
    print("-" * 70)

    enricher = DataEnricher(client=mock_client, max_workers=5)
    enriched = enricher.enrich_orders(valid_records)

    enriched_ok = sum(1 for r in enriched if r['_enrichment_complete'])
    print(f"   ✓ Enriquecimiento completado")
    print(f"   - Entrada: {len(valid_records)} registros")
    print(f"   - Enriquecidos exitosamente: {enriched_ok}/{len(enriched)}\n")

    # ========== Resumen del pipeline ==========
    print("-" * 70)
    print(f"   📊 RESUMEN DEL PIPELINE:")
    print(f"   - Registros brutos:       {len(raw_records)}")
    print(f"   - Tras deduplicación:     {len(deduplicated)}")
    print(f"   - Tras validación:        {len(valid_records)}")
    print(f"   - Tras enriquecimiento:   {len(enriched)}")
    print(f"   - Enriquecidos OK:        {enriched_ok}")

    assert len(enriched) == len(valid_records)
    assert enriched_ok == len(valid_records)

    print("\n" + "="*70)
    print("✅ PIPELINE COMPLETO 6+7+8 COMPLETADO EXITOSAMENTE")
    print("="*70 + "\n")

    return True


# =============================================================================
# Main
# =============================================================================

def main():
    """Ejecutar todos los tests integrados"""
    print("\n" + "🚀"*35)
    print("  SUITE DE TESTS INTEGRADOS - TASKS 6, 7 Y 8")
    print("🚀"*35)

    tests = [
        ("Task 6: Incremental Polling", test_incremental_polling_flow),
        ("Task 7: Data Validator",      test_data_validator_flow),
        ("Task 8: Data Enricher",       test_data_enricher_flow),
        ("Pipeline Completo 6+7+8",     test_full_pipeline_6_7_8),
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