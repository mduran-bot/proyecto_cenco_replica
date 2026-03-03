"""
Pipeline completo con mapeo de esquema desde CSV Schema Definition Janis.

Este script:
1. Obtiene datos de la API de Janis
2. Aplica el mapeo de campos según Schema Definition Janis.csv
3. Transforma los datos usando todos los módulos integrados
4. Genera salida en formato compatible con wms_orders y tablas relacionadas
"""

import json
import requests
import pandas as pd
from datetime import datetime
import sys
import os

# Agregar el directorio modules al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'modules'))

# Importar módulos integrados
from json_flattener import JSONFlattener
from data_cleaner import DataCleaner
from data_normalizer import DataNormalizer
from data_type_converter import DataTypeConverter
from data_gap_handler import DataGapHandler
from duplicate_detector import DuplicateDetector
from conflict_resolver import ConflictResolver


# Configuración de API Janis
API_CONFIG = {
    'base_url': 'https://oms.janis.in/api/order',
    'headers': {
        'janis-client': 'wongio',
        'janis-api-key': '8fc949ac-6d63-4447-a3d6-a16b66048e61',
        'janis-api-secret': 'UwPbe45dmE7lySRJ3zcA66Pfdt7xAY3QXWO181Y8OTgCxE3aZuyXpS8HyyPSwsWK'
    }
}


# Mapeo de campos según Schema Definition Janis.csv
# Tabla: wms_orders
WMS_ORDERS_MAPPING = {
    'vtex_id': 'commerceId',
    'id': 'id',
    'seq_id': 'commerceSequentialId',
    'ecommerce_account': 'account.id',
    'seller_id': 'seller.id',
    'seller_ecom_id': 'seller.commerceId',
    'website_name': 'salesChannelName',
    'customer': 'customer.id',
    'customer_address': 'addresses[0].id',  # Primer elemento del array
    'store': 'statusPerLocation',  # Requiere procesamiento especial
    'sales_channel': 'salesChannelId',
    'invoice_date': 'invoices[0].dateCreated',
    'invoice_number': 'invoices[0].number',
    'invoice_ammount': 'invoices[0].amount',
    'product_qty': 'productsQuantity',
    'items_qty': 'itemsQuantity',
    'total': 'totalAmount',
    'total_items': 'totals.items.amount',
    'total_discount': 'totals.discounts.amount',
    'total_shipping': 'totals.shipping.amount',
    'total_original': 'originalAmount',
    'status': 'status',
    'user_created': 'userCreated',
    'user_modified': 'userModified',
    'date_created': 'dateCreated',
    'date_picked': 'steps.picking.dateEnd',
}

# Tabla: wms_order_items
WMS_ORDER_ITEMS_MAPPING = {
    'id': 'items[].id',
    'order_id': 'id',  # ID de la orden padre
    'sku': 'items[].skuId',
    'product': 'items[].commerceProductId',
    'ref_id': 'items[].refId',
    'name': 'items[].name',
    'list_price': 'items[].purchasedListPrice',
    'price': 'items[].purchasedPrice',
    'quantity': 'items[].purchasedQuantity',
    'measurement_unit': 'items[].sellingMeasurementUnit',
    'unit_multiplier': 'items[].sellingUnitMultiplier',
}

# Tabla: wms_order_shipping
WMS_ORDER_SHIPPING_MAPPING = {
    'id': 'shippings[].id',
    'order_id': 'id',  # ID de la orden padre
    'city': 'addresses[].city',
    'neighborhood': 'addresses[].neighborhood',
    'complement': 'addresses[].complement',
    'lat': 'addresses[].geolocation[1]',  # Segundo elemento
    'lng': 'addresses[].geolocation[0]',  # Primer elemento
    'carrier_id': 'shippings[].carrierId',
    'shipping_window_start': 'shippings[].deliveryWindow.initialDate',
    'shipping_window_end': 'shippings[].deliveryWindow.finalDate',
    'shipped_date_start': 'shippings[].dateModified',
    'shipped_date_end': 'shippings[].dateModified',
}


def fetch_order_from_api(order_id):
    """
    Obtiene una orden de la API de Janis.
    
    Args:
        order_id: ID de la orden a obtener
        
    Returns:
        dict: Datos de la orden en formato JSON
    """
    url = f"{API_CONFIG['base_url']}/{order_id}"
    
    try:
        response = requests.get(url, headers=API_CONFIG['headers'])
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"❌ Error al obtener orden {order_id}: {e}")
        return None


def extract_nested_value(data, path):
    """
    Extrae un valor de un objeto JSON anidado usando notación de punto.
    
    Args:
        data: Diccionario con los datos
        path: Ruta al valor (ej: 'seller.id', 'items[].name')
        
    Returns:
        Valor extraído o None si no existe
    """
    # Manejar arrays
    if '[]' in path:
        # Por ahora, tomar el primer elemento del array
        path = path.replace('[]', '[0]')
    
    # Navegar por la ruta
    keys = path.replace('[', '.').replace(']', '').split('.')
    value = data
    
    for key in keys:
        if key.isdigit():
            # Es un índice de array
            try:
                value = value[int(key)]
            except (IndexError, TypeError, KeyError):
                return None
        else:
            # Es una clave de diccionario
            try:
                value = value.get(key) if isinstance(value, dict) else None
            except (AttributeError, TypeError):
                return None
            
            if value is None:
                return None
    
    return value


def map_order_to_wms_orders(order_data):
    """
    Mapea datos de orden de Janis API a formato wms_orders.
    
    Args:
        order_data: Datos de la orden desde la API
        
    Returns:
        dict: Datos mapeados a formato wms_orders
    """
    mapped_data = {}
    
    for db_field, api_path in WMS_ORDERS_MAPPING.items():
        # Casos especiales
        if api_path == 'statusPerLocation':
            # Extraer primer locationId del objeto statusPerLocation
            status_per_loc = order_data.get('statusPerLocation', {})
            if status_per_loc:
                mapped_data[db_field] = list(status_per_loc.keys())[0]
            else:
                mapped_data[db_field] = None
        else:
            # Extracción normal
            mapped_data[db_field] = extract_nested_value(order_data, api_path)
    
    return mapped_data


def map_order_to_wms_order_items(order_data):
    """
    Mapea datos de items de orden de Janis API a formato wms_order_items.
    
    Args:
        order_data: Datos de la orden desde la API
        
    Returns:
        list: Lista de items mapeados a formato wms_order_items
    """
    items = order_data.get('items', [])
    order_id = order_data.get('id')
    
    mapped_items = []
    for item in items:
        mapped_item = {
            'order_id': order_id,
            'id': item.get('id'),
            'sku': item.get('skuId'),
            'product': item.get('commerceProductId'),
            'ref_id': item.get('refId'),
            'name': item.get('name'),
            'list_price': item.get('purchasedListPrice'),
            'price': item.get('purchasedPrice'),
            'quantity': item.get('purchasedQuantity'),
            'measurement_unit': item.get('sellingMeasurementUnit'),
            'unit_multiplier': item.get('sellingUnitMultiplier'),
        }
        mapped_items.append(mapped_item)
    
    return mapped_items


def map_order_to_wms_order_shipping(order_data):
    """
    Mapea datos de shipping de orden de Janis API a formato wms_order_shipping.
    
    Args:
        order_data: Datos de la orden desde la API
        
    Returns:
        list: Lista de shippings mapeados a formato wms_order_shipping
    """
    shippings = order_data.get('shippings', [])
    addresses = order_data.get('addresses', [])
    order_id = order_data.get('id')
    
    mapped_shippings = []
    for i, shipping in enumerate(shippings):
        # Obtener dirección correspondiente (si existe)
        address = addresses[i] if i < len(addresses) else {}
        geolocation = address.get('geolocation', [None, None])
        
        mapped_shipping = {
            'order_id': order_id,
            'id': shipping.get('id'),
            'city': address.get('city'),
            'neighborhood': address.get('neighborhood'),
            'complement': address.get('complement'),
            'lat': geolocation[1] if len(geolocation) > 1 else None,
            'lng': geolocation[0] if len(geolocation) > 0 else None,
            'carrier_id': shipping.get('carrierId'),
            'shipping_window_start': shipping.get('deliveryWindow', {}).get('initialDate'),
            'shipping_window_end': shipping.get('deliveryWindow', {}).get('finalDate'),
            'shipped_date_start': shipping.get('dateModified'),
            'shipped_date_end': shipping.get('dateModified'),
        }
        mapped_shippings.append(mapped_shipping)
    
    return mapped_shippings


def apply_transformations(df, table_name):
    """
    Aplica transformaciones básicas usando pandas (versión simplificada).
    
    Args:
        df: DataFrame con los datos
        table_name: Nombre de la tabla (para logging)
        
    Returns:
        DataFrame transformado
    """
    print(f"\n🔄 Aplicando transformaciones a {table_name}...")
    
    # 1. Limpieza de datos (pandas)
    print("  - Limpiando datos...")
    # Trim whitespace de columnas string
    string_cols = df.select_dtypes(include=['object', 'string']).columns
    for col in string_cols:
        df[col] = df[col].str.strip() if hasattr(df[col], 'str') else df[col]
    
    # Convertir strings vacíos a None
    df = df.replace('', None)
    df = df.replace('  ', None)  # Espacios múltiples
    
    # 2. Normalización básica
    print("  - Normalizando datos...")
    
    # Normalizar emails (lowercase)
    email_cols = [col for col in df.columns if 'email' in col.lower()]
    for col in email_cols:
        if col in df.columns:
            df[col] = df[col].str.lower() if hasattr(df[col], 'str') else df[col]
    
    # 3. Conversión de tipos básica
    print("  - Convirtiendo tipos de datos...")
    
    # Convertir columnas numéricas
    for col in df.columns:
        if 'qty' in col.lower() or 'quantity' in col.lower() or 'count' in col.lower():
            try:
                df[col] = pd.to_numeric(df[col], errors='ignore')
            except:
                pass
        
        if 'price' in col.lower() or 'amount' in col.lower() or 'total' in col.lower():
            try:
                df[col] = pd.to_numeric(df[col], errors='ignore')
            except:
                pass
    
    print(f"✅ Transformaciones completadas para {table_name}")
    return df


def run_pipeline(order_id):
    """
    Ejecuta el pipeline completo para una orden.
    
    Args:
        order_id: ID de la orden a procesar
    """
    print(f"\n{'='*80}")
    print(f"🚀 INICIANDO PIPELINE CON MAPEO DE ESQUEMA")
    print(f"{'='*80}")
    print(f"Orden ID: {order_id}")
    print(f"Timestamp: {datetime.now().isoformat()}")
    
    # 1. Obtener datos de la API
    print(f"\n📥 Paso 1: Obteniendo datos de la API de Janis...")
    order_data = fetch_order_from_api(order_id)
    
    if not order_data:
        print("❌ No se pudieron obtener los datos de la orden")
        return
    
    print(f"✅ Datos obtenidos exitosamente")
    print(f"   - Orden: {order_data.get('commerceSequentialId')}")
    print(f"   - Items: {len(order_data.get('items', []))}")
    print(f"   - Shippings: {len(order_data.get('shippings', []))}")
    
    # Guardar datos crudos
    raw_file = f"data/order_{order_id}_raw.json"
    with open(raw_file, 'w', encoding='utf-8') as f:
        json.dump(order_data, f, indent=2, ensure_ascii=False)
    print(f"   - Guardado en: {raw_file}")
    
    # 2. Mapear a wms_orders
    print(f"\n🗺️  Paso 2: Mapeando a formato wms_orders...")
    wms_orders_data = map_order_to_wms_orders(order_data)
    df_orders = pd.DataFrame([wms_orders_data])
    print(f"✅ Mapeado completado: {len(df_orders)} registro(s)")
    print(f"   - Campos mapeados: {len([v for v in wms_orders_data.values() if v is not None])}/{len(wms_orders_data)}")
    
    # 3. Mapear a wms_order_items
    print(f"\n🗺️  Paso 3: Mapeando a formato wms_order_items...")
    wms_items_data = map_order_to_wms_order_items(order_data)
    df_items = pd.DataFrame(wms_items_data)
    print(f"✅ Mapeado completado: {len(df_items)} registro(s)")
    
    # 4. Mapear a wms_order_shipping
    print(f"\n🗺️  Paso 4: Mapeando a formato wms_order_shipping...")
    wms_shipping_data = map_order_to_wms_order_shipping(order_data)
    df_shipping = pd.DataFrame(wms_shipping_data)
    print(f"✅ Mapeado completado: {len(df_shipping)} registro(s)")
    
    # 5. Aplicar transformaciones
    print(f"\n🔧 Paso 5: Aplicando transformaciones del pipeline...")
    df_orders_transformed = apply_transformations(df_orders, "wms_orders")
    df_items_transformed = apply_transformations(df_items, "wms_order_items")
    df_shipping_transformed = apply_transformations(df_shipping, "wms_order_shipping")
    
    # 6. Guardar resultados
    print(f"\n💾 Paso 6: Guardando resultados...")
    
    orders_file = f"data/order_{order_id}_wms_orders.csv"
    df_orders_transformed.to_csv(orders_file, index=False)
    print(f"   - wms_orders: {orders_file}")
    
    items_file = f"data/order_{order_id}_wms_order_items.csv"
    df_items_transformed.to_csv(items_file, index=False)
    print(f"   - wms_order_items: {items_file}")
    
    shipping_file = f"data/order_{order_id}_wms_order_shipping.csv"
    df_shipping_transformed.to_csv(shipping_file, index=False)
    print(f"   - wms_order_shipping: {shipping_file}")
    
    # 7. Generar reporte de calidad
    print(f"\n📊 Paso 7: Generando reporte de calidad...")
    print(f"\n{'='*80}")
    print(f"REPORTE DE CALIDAD DE DATOS")
    print(f"{'='*80}")
    
    print(f"\n📋 wms_orders:")
    print(f"   - Total registros: {len(df_orders_transformed)}")
    print(f"   - Total columnas: {len(df_orders_transformed.columns)}")
    print(f"   - Campos con datos: {df_orders_transformed.notna().sum().sum()}")
    print(f"   - Campos vacíos: {df_orders_transformed.isna().sum().sum()}")
    print(f"   - Completitud: {(df_orders_transformed.notna().sum().sum() / (len(df_orders_transformed) * len(df_orders_transformed.columns)) * 100):.1f}%")
    
    print(f"\n📋 wms_order_items:")
    print(f"   - Total registros: {len(df_items_transformed)}")
    print(f"   - Total columnas: {len(df_items_transformed.columns)}")
    print(f"   - Campos con datos: {df_items_transformed.notna().sum().sum()}")
    print(f"   - Campos vacíos: {df_items_transformed.isna().sum().sum()}")
    print(f"   - Completitud: {(df_items_transformed.notna().sum().sum() / (len(df_items_transformed) * len(df_items_transformed.columns)) * 100):.1f}%")
    
    print(f"\n📋 wms_order_shipping:")
    print(f"   - Total registros: {len(df_shipping_transformed)}")
    print(f"   - Total columnas: {len(df_shipping_transformed.columns)}")
    print(f"   - Campos con datos: {df_shipping_transformed.notna().sum().sum()}")
    print(f"   - Campos vacíos: {df_shipping_transformed.isna().sum().sum()}")
    print(f"   - Completitud: {(df_shipping_transformed.notna().sum().sum() / (len(df_shipping_transformed) * len(df_shipping_transformed.columns)) * 100):.1f}%")
    
    print(f"\n{'='*80}")
    print(f"✅ PIPELINE COMPLETADO EXITOSAMENTE")
    print(f"{'='*80}")
    print(f"\nArchivos generados:")
    print(f"  - {raw_file}")
    print(f"  - {orders_file}")
    print(f"  - {items_file}")
    print(f"  - {shipping_file}")


if __name__ == "__main__":
    # Orden de ejemplo (la misma que usamos en pruebas anteriores)
    ORDER_ID = "6913fcb6d134afc8da8ac3dd"
    
    run_pipeline(ORDER_ID)
