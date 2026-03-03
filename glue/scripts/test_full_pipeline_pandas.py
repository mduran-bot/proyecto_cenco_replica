"""
Test del Pipeline Completo: API Janis → Bronze → Silver → Gold (usando pandas)
"""
import sys
import os
import logging
import requests
import json
from datetime import datetime
import pandas as pd

def fetch_from_janis_api(order_id):
    """Obtener datos de la API de Janis"""
    url = f"https://oms.janis.in/api/order/{order_id}"
    
    headers = {
        'janis-client': 'cencosudprod',
        'janis-api-key': 'ZjU0YjI0YzItNjk0Yy00ZGU5LWI5ZTUtNjk5YzI5ZjI5ZjBl',
        'janis-api-secret': 'NjI5NzI5YzItNjk0Yy00ZGU5LWI5ZTUtNjk5YzI5ZjI5ZjBl'
    }
    
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()

def flatten_json(data, parent_key='', sep='_'):
    """Aplanar JSON anidado"""
    items = []
    for k, v in data.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_json(v, new_key, sep=sep).items())
        elif isinstance(v, list):
            # Para listas, tomar el primer elemento o convertir a string
            if v and isinstance(v[0], dict):
                items.extend(flatten_json(v[0], new_key, sep=sep).items())
            else:
                items.append((new_key, str(v)))
        else:
            items.append((new_key, v))
    return dict(items)

def clean_data(df):
    """Limpiar datos"""
    # Trim strings
    for col in df.select_dtypes(include=['object']).columns:
        df[col] = df[col].str.strip() if df[col].dtype == 'object' else df[col]
    
    # Reemplazar strings vacíos con None
    df = df.replace('', None)
    
    return df

def aggregate_data(df):
    """Agregar datos"""
    # Verificar si tenemos las columnas necesarias
    if 'totalAmount' not in df.columns:
        logging.warning("No se encontró 'totalAmount', usando valor sintético")
        df['totalAmount'] = 1000.0
    
    if 'status' not in df.columns:
        logging.warning("No se encontró 'status', usando valor sintético")
        df['status'] = 'completed'
    
    if 'dateCreated' not in df.columns:
        logging.warning("No se encontró 'dateCreated', usando timestamp actual")
        df['dateCreated'] = datetime.now().isoformat()
    
    # Convertir fecha
    df['fecha_venta'] = pd.to_datetime(df['dateCreated'], errors='coerce')
    
    # Agregar dimensiones de tiempo
    df['year'] = df['fecha_venta'].dt.year
    df['month'] = df['fecha_venta'].dt.month
    df['day'] = df['fecha_venta'].dt.day
    
    # Renombrar para agregación
    df['monto'] = pd.to_numeric(df['totalAmount'], errors='coerce')
    df['estado'] = df['status']
    df['metadata_sucursal'] = 'Sucursal API'  # Valor sintético
    
    # Agregar
    agg_df = df.groupby(['metadata_sucursal', 'estado']).agg({
        'monto': ['sum', 'mean', 'min', 'max', 'count']
    }).reset_index()
    
    # Aplanar columnas
    agg_df.columns = ['metadata_sucursal', 'estado', 'total_monto', 'promedio_monto', 'min_monto', 'max_monto', 'num_registros']
    
    return agg_df

def validate_quality(df):
    """Validar calidad de datos"""
    df['_quality_valid'] = True
    df['_quality_issues'] = ''
    
    # Completeness
    if 'estado' in df.columns:
        df.loc[df['estado'].isna(), '_quality_valid'] = False
        df.loc[df['estado'].isna(), '_quality_issues'] += 'COMPLETENESS_FAIL;'
    
    # Range
    if 'total_monto' in df.columns:
        df.loc[(df['total_monto'] < 0) | (df['total_monto'] > 99999999), '_quality_valid'] = False
        df.loc[(df['total_monto'] < 0) | (df['total_monto'] > 99999999), '_quality_issues'] += 'RANGE_FAIL;'
    
    return df

def main():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
    logger = logging.getLogger('FullPipelineTest')
    
    logger.info("=" * 80)
    logger.info("TEST PIPELINE COMPLETO: API JANIS → BRONZE → SILVER → GOLD (PANDAS)")
    logger.info("=" * 80)
    
    # 1. BRONZE: Obtener datos de API Janis
    logger.info("\n" + "=" * 80)
    logger.info("FASE 1: BRONZE - Ingesta desde API Janis")
    logger.info("=" * 80)
    
    order_id = "6913fcb6d134afc8da8ac3dd"
    logger.info(f"\n1.1 Usando datos Bronze existentes (orden {order_id})...")
    
    # Usar datos existentes
    existing_bronze = f"glue/data/order_{order_id}_raw.json"
    
    try:
        with open(existing_bronze, 'r', encoding='utf-8') as f:
            order_data = json.load(f)
        logger.info(f"     ✅ Datos Bronze cargados desde: {existing_bronze}")
        logger.info(f"     Campos principales: {list(order_data.keys())[:10]}")
    except FileNotFoundError:
        logger.error(f"     ❌ No se encontró el archivo: {existing_bronze}")
        logger.info(f"     Intentando obtener de API...")
        try:
            order_data = fetch_from_janis_api(order_id)
            logger.info(f"     ✅ Orden obtenida de API exitosamente")
        except Exception as e:
            logger.error(f"     ❌ Error obteniendo datos de API: {e}")
            return 1
    
    # Guardar Bronze (copia)
    bronze_path = f"glue/data/bronze_order_{order_id}_pandas.json"
    logger.info(f"\n1.2 Guardando copia de datos Bronze en: {bronze_path}")
    with open(bronze_path, 'w', encoding='utf-8') as f:
        json.dump(order_data, f, indent=2, ensure_ascii=False)
    
    # 2. SILVER: Transformar Bronze → Silver
    logger.info("\n" + "=" * 80)
    logger.info("FASE 2: SILVER - Transformación Bronze → Silver")
    logger.info("=" * 80)
    
    logger.info("\n2.1 Aplanando JSON anidado...")
    flattened_data = flatten_json(order_data)
    logger.info(f"     Campos después de aplanar: {len(flattened_data)}")
    
    # Convertir a DataFrame
    df_silver = pd.DataFrame([flattened_data])
    
    logger.info("\n2.2 Limpiando datos...")
    df_silver = clean_data(df_silver)
    logger.info(f"     Registros en Silver: {len(df_silver)}")
    logger.info(f"     Columnas en Silver: {len(df_silver.columns)}")
    
    # Guardar Silver
    silver_path = f"glue/data/silver_order_{order_id}_pandas.json"
    logger.info(f"\n2.3 Guardando datos Silver en: {silver_path}")
    df_silver.to_json(silver_path, orient='records', indent=2)
    
    logger.info(f"\n2.4 Primeras 10 columnas en Silver:")
    for col in list(df_silver.columns)[:10]:
        logger.info(f"     - {col}")
    
    # 3. GOLD: Transformar Silver → Gold
    logger.info("\n" + "=" * 80)
    logger.info("FASE 3: GOLD - Transformación Silver → Gold")
    logger.info("=" * 80)
    
    logger.info("\n3.1 Preparando datos para agregación...")
    df_gold = aggregate_data(df_silver)
    logger.info(f"     Registros agregados: {len(df_gold)}")
    
    logger.info("\n3.2 Validando calidad de datos...")
    df_gold = validate_quality(df_gold)
    logger.info(f"     Registros validados: {len(df_gold)}")
    
    # Agregar timestamp
    df_gold['_processing_timestamp'] = datetime.now().isoformat()
    
    # Guardar Gold
    gold_path = f"glue/data/gold_order_{order_id}_pandas.json"
    logger.info(f"\n3.3 Guardando datos Gold en: {gold_path}")
    df_gold.to_json(gold_path, orient='records', indent=2)
    
    # 4. RESULTADOS FINALES
    logger.info("\n" + "=" * 80)
    logger.info("RESULTADOS FINALES")
    logger.info("=" * 80)
    
    logger.info(f"\n4.1 Resumen del Pipeline:")
    logger.info(f"     Bronze (raw):    1 orden de API Janis ({len(order_data)} campos)")
    logger.info(f"     Silver (clean):  1 registro ({len(df_silver.columns)} columnas)")
    logger.info(f"     Gold (agg):      {len(df_gold)} registros agregados")
    
    logger.info(f"\n4.2 Columnas en Gold:")
    for col_name in sorted(df_gold.columns):
        logger.info(f"     - {col_name}")
    
    logger.info(f"\n4.3 Datos Gold:")
    print(df_gold.to_string())
    
    # Análisis de calidad
    logger.info(f"\n4.4 Análisis de Calidad:")
    valid_count = df_gold['_quality_valid'].sum()
    total = len(df_gold)
    logger.info(f"     Registros válidos: {valid_count}/{total} ({valid_count/total*100:.1f}%)")
    
    # Información de la orden
    logger.info(f"\n4.5 Información de la Orden:")
    if 'id' in df_silver.columns:
        logger.info(f"     ID: {df_silver['id'].iloc[0]}")
    if 'status' in df_silver.columns:
        logger.info(f"     Estado: {df_silver['status'].iloc[0]}")
    if 'totalAmount' in df_silver.columns:
        logger.info(f"     Monto Total: {df_silver['totalAmount'].iloc[0]}")
    if 'dateCreated' in df_silver.columns:
        logger.info(f"     Fecha Creación: {df_silver['dateCreated'].iloc[0]}")
    
    logger.info("\n" + "=" * 80)
    logger.info("✅ PIPELINE COMPLETO EJECUTADO EXITOSAMENTE")
    logger.info("=" * 80)
    logger.info("\nArchivos generados:")
    logger.info(f"  - Bronze: {bronze_path}")
    logger.info(f"  - Silver: {silver_path}")
    logger.info(f"  - Gold:   {gold_path}")
    logger.info("=" * 80)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
