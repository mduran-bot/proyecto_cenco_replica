"""
Script de Prueba del Pipeline con Datos Reales de Janis API

Este script:
1. Se conecta a la API de Janis
2. Obtiene datos reales de wms_orders
3. Aplica el pipeline completo de transformación
4. Muestra los resultados paso a paso

Ejecutar: python glue/scripts/test_pipeline_janis_api.py
"""

import sys
import os
import requests
import json
import pandas as pd
from datetime import datetime

# Agregar el directorio padre al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules import (
    DataTypeConverter,
    DataNormalizer,
    DataGapHandler
)

# Colores para output
class Colors:
    GREEN = '\033[92m'
    BLUE = '\033[94m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'

def print_section(title):
    print(f"\n{Colors.BLUE}{'='*70}")
    print(f"{title}")
    print(f"{'='*70}{Colors.END}\n")

def print_step(step_num, step_name):
    print(f"\n{Colors.GREEN}>>> PASO {step_num}: {step_name}{Colors.END}\n")

def print_error(msg):
    print(f"{Colors.RED}✗ ERROR: {msg}{Colors.END}")

def print_success(msg):
    print(f"{Colors.GREEN}✓ {msg}{Colors.END}")


def fetch_order_from_janis(order_id):
    """
    Obtiene una orden desde la API de Janis.
    
    Args:
        order_id: ID de la orden a obtener
        
    Returns:
        dict: Datos de la orden en formato JSON
    """
    # Configuración de la API
    base_url = "https://oms.janis.in/api/order"
    url = f"{base_url}/{order_id}/history"
    
    # Headers de autenticación
    headers = {
        'janis-client': 'wongio',
        'janis-api-key': '8fc949ac-6d63-4447-a3d6-a16b66048e61',
        'janis-api-secret': 'UwPbe45dmE7lySRJ3zcA66Pfdt7xAY3QXWO181Y8OTgCxE3aZuyXpS8HyyPSwsWK'
    }
    
    print(f"Conectando a: {url}")
    print(f"Headers: janis-client={headers['janis-client']}")
    print()
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        print_success(f"Datos obtenidos exitosamente (Status: {response.status_code})")
        return data
        
    except requests.exceptions.RequestException as e:
        print_error(f"Error al conectar con la API: {e}")
        return None


def flatten_json(data, parent_key='', sep='_'):
    """
    Aplana un JSON anidado recursivamente.
    
    Args:
        data: Diccionario o lista a aplanar
        parent_key: Clave padre para recursión
        sep: Separador para claves anidadas
        
    Returns:
        dict: Diccionario aplanado
    """
    items = []
    
    if isinstance(data, dict):
        for k, v in data.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            
            if isinstance(v, dict):
                items.extend(flatten_json(v, new_key, sep=sep).items())
            elif isinstance(v, list):
                # Para listas, crear una representación string o procesar cada elemento
                if v and isinstance(v[0], dict):
                    # Si es lista de objetos, guardar como JSON string
                    items.append((new_key, json.dumps(v)))
                else:
                    # Si es lista simple, guardar como está
                    items.append((new_key, v))
            else:
                items.append((new_key, v))
    elif isinstance(data, list):
        # Si el dato raíz es una lista, procesar cada elemento
        for i, item in enumerate(data):
            new_key = f"{parent_key}{sep}{i}" if parent_key else str(i)
            if isinstance(item, (dict, list)):
                items.extend(flatten_json(item, new_key, sep=sep).items())
            else:
                items.append((new_key, item))
    else:
        items.append((parent_key, data))
    
    return dict(items)


def main():
    print_section("PRUEBA DEL PIPELINE CON DATOS REALES DE JANIS API")
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # ========================================================================
    # PASO 0: OBTENER DATOS DE LA API
    # ========================================================================
    
    print_section("PASO 0: OBTENER DATOS DE JANIS API")
    
    # ID de orden de ejemplo (puedes cambiarlo)
    order_id = "6913fcb6d134afc8da8ac3dd"
    
    print(f"Obteniendo orden: {order_id}")
    print()
    
    order_data = fetch_order_from_janis(order_id)
    
    if not order_data:
        print_error("No se pudieron obtener datos de la API")
        print("Verifica:")
        print("  1. Que la URL sea correcta")
        print("  2. Que las credenciales sean válidas")
        print("  3. Que tengas conexión a internet")
        return
    
    # Guardar datos crudos para referencia
    with open('glue/data/janis_order_raw.json', 'w', encoding='utf-8') as f:
        json.dump(order_data, f, indent=2, ensure_ascii=False)
    print_success("Datos guardados en: glue/data/janis_order_raw.json")
    
    # Mostrar estructura de datos
    print()
    print("Estructura de datos recibidos:")
    print(f"  Tipo: {type(order_data)}")
    
    if isinstance(order_data, dict):
        print(f"  Claves principales: {list(order_data.keys())[:10]}")
    elif isinstance(order_data, list):
        print(f"  Cantidad de registros: {len(order_data)}")
        if order_data:
            print(f"  Claves del primer registro: {list(order_data[0].keys())[:10]}")
    
    print()
    print("Vista previa de datos (primeros 500 caracteres):")
    print(json.dumps(order_data, indent=2, ensure_ascii=False)[:500] + "...")
    
    # ========================================================================
    # PASO 1: APLANAR JSON
    # ========================================================================
    
    print_step(1, "APLANAR JSON (JSONFlattener)")
    
    # Si es una lista, procesar cada elemento
    if isinstance(order_data, list):
        flattened_data = [flatten_json(item) for item in order_data]
    else:
        flattened_data = [flatten_json(order_data)]
    
    # Convertir a DataFrame
    df = pd.DataFrame(flattened_data)
    
    print(f"Columnas después de aplanar: {len(df.columns)}")
    print(f"Registros: {len(df)}")
    print()
    print("Primeras 10 columnas:")
    print(list(df.columns)[:10])
    print()
    
    # Guardar datos aplanados
    df.to_csv('glue/data/janis_order_flattened.csv', index=False)
    print_success("Datos aplanados guardados en: glue/data/janis_order_flattened.csv")
    
    # ========================================================================
    # PASO 2: IDENTIFICAR COLUMNAS RELEVANTES
    # ========================================================================
    
    print_step(2, "IDENTIFICAR COLUMNAS RELEVANTES")
    
    # Buscar columnas comunes de órdenes
    relevant_columns = []
    column_patterns = [
        'id', 'order', 'date', 'status', 'email', 'phone', 
        'customer', 'amount', 'quantity', 'item', 'product',
        'address', 'city', 'store'
    ]
    
    for col in df.columns:
        col_lower = col.lower()
        if any(pattern in col_lower for pattern in column_patterns):
            relevant_columns.append(col)
    
    print(f"Columnas relevantes encontradas: {len(relevant_columns)}")
    print()
    print("Columnas seleccionadas:")
    for col in relevant_columns[:20]:  # Mostrar primeras 20
        sample_value = df[col].iloc[0] if len(df) > 0 else None
        # Truncar valores largos
        if isinstance(sample_value, str) and len(sample_value) > 50:
            sample_value = sample_value[:50] + "..."
        print(f"  - {col}: {sample_value}")
    
    if len(relevant_columns) > 20:
        print(f"  ... y {len(relevant_columns) - 20} columnas más")
    
    # ========================================================================
    # PASO 3: APLICAR TRANSFORMACIONES
    # ========================================================================
    
    print_step(3, "APLICAR TRANSFORMACIONES")
    
    # Seleccionar solo columnas relevantes para el pipeline
    df_relevant = df[relevant_columns].copy() if relevant_columns else df.copy()
    
    print("Transformaciones a aplicar:")
    print("  1. Limpieza de datos (trim, encoding)")
    print("  2. Conversión de tipos")
    print("  3. Normalización (emails, teléfonos)")
    print("  4. Cálculo de campos derivados")
    print()
    
    # 3.1 Limpieza básica
    print("3.1 Limpiando datos...")
    for col in df_relevant.select_dtypes(include=['object']).columns:
        if df_relevant[col].dtype == 'object':
            df_relevant[col] = df_relevant[col].apply(
                lambda x: x.strip() if isinstance(x, str) else x
            )
    print_success("Espacios en blanco eliminados")
    
    # 3.2 Normalización de emails
    print("3.2 Normalizando emails...")
    normalizer = DataNormalizer()
    email_cols = [col for col in df_relevant.columns if 'email' in col.lower()]
    for col in email_cols:
        try:
            df_relevant[col] = df_relevant[col].apply(
                lambda x: normalizer.validate_and_clean_email(x) if pd.notna(x) and isinstance(x, str) else x
            )
            print_success(f"  - {col} normalizado")
        except Exception as e:
            print(f"  ⚠ No se pudo normalizar {col}: {e}")
    
    # 3.3 Normalización de teléfonos
    print("3.3 Normalizando teléfonos...")
    phone_cols = [col for col in df_relevant.columns if 'phone' in col.lower() or 'telefono' in col.lower()]
    for col in phone_cols:
        try:
            df_relevant[col] = df_relevant[col].apply(
                lambda x: normalizer.normalize_phone_number(x, country_code='51') if pd.notna(x) and isinstance(x, str) else x
            )
            print_success(f"  - {col} normalizado")
        except Exception as e:
            print(f"  ⚠ No se pudo normalizar {col}: {e}")
    
    # 3.4 Conversión de tipos (timestamps)
    print("3.4 Convirtiendo tipos de datos...")
    converter = DataTypeConverter()
    date_cols = [col for col in df_relevant.columns if 'date' in col.lower() or 'created' in col.lower()]
    for col in date_cols:
        try:
            # Intentar convertir si parece un timestamp Unix
            if df_relevant[col].dtype in ['int64', 'float64']:
                df_relevant[col] = df_relevant[col].apply(
                    lambda x: converter.convert_bigint_to_timestamp(int(x)) if pd.notna(x) else x
                )
                print_success(f"  - {col} convertido a timestamp")
        except Exception as e:
            print(f"  ⚠ No se pudo convertir {col}: {e}")
    
    # ========================================================================
    # PASO 4: RESULTADOS
    # ========================================================================
    
    print_step(4, "RESULTADOS FINALES")
    
    print("Datos transformados:")
    print(f"  - Registros: {len(df_relevant)}")
    print(f"  - Columnas: {len(df_relevant.columns)}")
    print()
    
    # Guardar resultados
    df_relevant.to_csv('glue/data/janis_order_transformed.csv', index=False)
    print_success("Datos transformados guardados en: glue/data/janis_order_transformed.csv")
    
    # Mostrar muestra de datos transformados
    print()
    print("Muestra de datos transformados (primeras 5 columnas):")
    print(df_relevant.iloc[:, :5].to_string(index=False))
    
    # ========================================================================
    # PASO 5: REPORTE DE CALIDAD
    # ========================================================================
    
    print_step(5, "REPORTE DE CALIDAD")
    
    # Estadísticas básicas
    print("Estadísticas de calidad:")
    print(f"  - Valores nulos por columna:")
    null_counts = df_relevant.isnull().sum()
    for col, count in null_counts[null_counts > 0].items():
        print(f"    • {col}: {count} ({count/len(df_relevant)*100:.1f}%)")
    
    if null_counts.sum() == 0:
        print("    ✓ No hay valores nulos")
    
    print()
    print(f"{Colors.GREEN}✓ PIPELINE COMPLETADO EXITOSAMENTE CON DATOS REALES{Colors.END}")
    print()
    print("Archivos generados:")
    print("  1. glue/data/janis_order_raw.json - Datos crudos de la API")
    print("  2. glue/data/janis_order_flattened.csv - Datos aplanados")
    print("  3. glue/data/janis_order_transformed.csv - Datos transformados")
    print()
    print("Próximo paso: Revisar los archivos CSV para validar las transformaciones")


if __name__ == "__main__":
    main()
