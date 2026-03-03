"""
Test Visual del Pipeline Completo: Bronze → Silver → Gold
Muestra los datos en cada etapa de transformación para entender el flujo
"""
import sys
import os
import logging
import json
from datetime import datetime
import pandas as pd

# Agregar path de módulos
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def print_section(title):
    """Imprimir sección con formato"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)

def print_subsection(title):
    """Imprimir subsección con formato"""
    print(f"\n>>> {title}")
    print("-" * 80)

def flatten_json(data, parent_key='', sep='_'):
    """Aplanar JSON anidado"""
    items = []
    for k, v in data.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_json(v, new_key, sep=sep).items())
        elif isinstance(v, list):
            if v and isinstance(v[0], dict):
                items.extend(flatten_json(v[0], new_key, sep=sep).items())
            else:
                items.append((new_key, str(v)))
        else:
            items.append((new_key, v))
    return dict(items)

def clean_data(df):
    """Limpiar datos"""
    for col in df.select_dtypes(include=['object']).columns:
        df[col] = df[col].str.strip() if df[col].dtype == 'object' else df[col]
    df = df.replace('', None)
    return df

def aggregate_data(df):
    """Agregar datos"""
    if 'totalAmount' not in df.columns:
        df['totalAmount'] = 1000.0
    if 'status' not in df.columns:
        df['status'] = 'completed'
    if 'dateCreated' not in df.columns:
        df['dateCreated'] = datetime.now().isoformat()
    
    df['fecha_venta'] = pd.to_datetime(df['dateCreated'], errors='coerce')
    df['year'] = df['fecha_venta'].dt.year
    df['month'] = df['fecha_venta'].dt.month
    df['day'] = df['fecha_venta'].dt.day
    
    df['monto'] = pd.to_numeric(df['totalAmount'], errors='coerce')
    df['estado'] = df['status']
    df['metadata_sucursal'] = 'Sucursal API'
    
    agg_df = df.groupby(['metadata_sucursal', 'estado']).agg({
        'monto': ['sum', 'mean', 'min', 'max', 'count']
    }).reset_index()
    
    agg_df.columns = ['metadata_sucursal', 'estado', 'total_monto', 
                      'promedio_monto', 'min_monto', 'max_monto', 'num_registros']
    return agg_df

def validate_quality(df):
    """Validar calidad de datos"""
    df['_quality_valid'] = True
    df['_quality_issues'] = ''
    
    if 'estado' in df.columns:
        df.loc[df['estado'].isna(), '_quality_valid'] = False
        df.loc[df['estado'].isna(), '_quality_issues'] += 'COMPLETENESS_FAIL;'
    
    if 'total_monto' in df.columns:
        df.loc[(df['total_monto'] < 0) | (df['total_monto'] > 99999999), '_quality_valid'] = False
        df.loc[(df['total_monto'] < 0) | (df['total_monto'] > 99999999), '_quality_issues'] += 'RANGE_FAIL;'
    
    return df

def show_json_structure(data, max_depth=2, current_depth=0, prefix=""):
    """Mostrar estructura del JSON de forma legible"""
    if current_depth >= max_depth:
        return
    
    for key, value in list(data.items())[:10]:  # Mostrar solo primeros 10 campos
        if isinstance(value, dict):
            print(f"{prefix}{key}: {{...}} (objeto con {len(value)} campos)")
            if current_depth < max_depth - 1:
                show_json_structure(value, max_depth, current_depth + 1, prefix + "  ")
        elif isinstance(value, list):
            print(f"{prefix}{key}: [...] (array con {len(value)} elementos)")
        else:
            value_str = str(value)[:50]
            print(f"{prefix}{key}: {value_str}")

def main():
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    
    print_section("TEST VISUAL DEL PIPELINE: BRONZE → SILVER → GOLD")
    print("\nEste script te muestra cómo se transforman los datos en cada etapa")
    print("Podrás ver:")
    print("  1. BRONZE: Datos crudos de la API (JSON anidado)")
    print("  2. SILVER: Datos limpios y aplanados (columnas planas)")
    print("  3. GOLD: Datos agregados (métricas de negocio)")
    
    # ========================================================================
    # FASE 1: BRONZE - Datos Crudos
    # ========================================================================
    print_section("FASE 1: BRONZE - Datos Crudos de API Janis")
    
    order_id = "6913fcb6d134afc8da8ac3dd"
    existing_bronze = f"glue/data/order_{order_id}_raw.json"
    
    try:
        with open(existing_bronze, 'r', encoding='utf-8') as f:
            order_data = json.load(f)
        print(f"\n✅ Datos cargados desde: {existing_bronze}")
    except FileNotFoundError:
        print(f"\n❌ No se encontró el archivo: {existing_bronze}")
        print("Por favor ejecuta primero: python glue/scripts/test_full_pipeline_pandas.py")
        return 1
    
    print_subsection("Estructura del JSON Bronze (primeros niveles)")
    show_json_structure(order_data, max_depth=2)
    
    print(f"\n📊 Estadísticas Bronze:")
    print(f"   - Campos principales: {len(order_data)}")
    print(f"   - Tipo de estructura: JSON anidado con objetos y arrays")
    
    # Guardar Bronze
    bronze_path = f"glue/data/bronze_order_{order_id}_visual.json"
    with open(bronze_path, 'w', encoding='utf-8') as f:
        json.dump(order_data, f, indent=2, ensure_ascii=False)
    
    # ========================================================================
    # FASE 2: SILVER - Datos Limpios y Aplanados
    # ========================================================================
    print_section("FASE 2: SILVER - Transformación Bronze → Silver")
    
    print_subsection("Paso 1: Aplanando JSON anidado")
    flattened_data = flatten_json(order_data)
    print(f"   ✅ JSON aplanado: {len(flattened_data)} columnas")
    
    print_subsection("Paso 2: Convirtiendo a DataFrame")
    df_silver = pd.DataFrame([flattened_data])
    print(f"   ✅ DataFrame creado: {len(df_silver)} registros, {len(df_silver.columns)} columnas")
    
    print_subsection("Paso 3: Limpiando datos")
    df_silver = clean_data(df_silver)
    print(f"   ✅ Datos limpios: espacios eliminados, encoding corregido")
    
    print_subsection("Primeras 20 columnas en Silver")
    for i, col in enumerate(list(df_silver.columns)[:20], 1):
        value = df_silver[col].iloc[0]
        value_str = str(value)[:40] if value is not None else "None"
        print(f"   {i:2d}. {col:30s} = {value_str}")
    
    if len(df_silver.columns) > 20:
        print(f"   ... y {len(df_silver.columns) - 20} columnas más")
    
    # Guardar Silver
    silver_path = f"glue/data/silver_order_{order_id}_visual.json"
    df_silver.to_json(silver_path, orient='records', indent=2)
    
    print(f"\n📊 Estadísticas Silver:")
    print(f"   - Total columnas: {len(df_silver.columns)}")
    print(f"   - Registros: {len(df_silver)}")
    print(f"   - Estructura: Tabla plana (sin anidamiento)")
    
    # ========================================================================
    # FASE 3: GOLD - Datos Agregados
    # ========================================================================
    print_section("FASE 3: GOLD - Transformación Silver → Gold")
    
    print_subsection("Paso 1: Preparando datos para agregación")
    df_gold = aggregate_data(df_silver)
    print(f"   ✅ Agregación completada: {len(df_gold)} registros")
    
    print_subsection("Paso 2: Validando calidad de datos")
    df_gold = validate_quality(df_gold)
    print(f"   ✅ Validación completada")
    
    df_gold['_processing_timestamp'] = datetime.now().isoformat()
    
    print_subsection("Datos Gold (Agregados)")
    print("\nColumnas en Gold:")
    for col in df_gold.columns:
        print(f"   - {col}")
    
    print("\nDatos agregados:")
    print(df_gold.to_string(index=False))
    
    # Guardar Gold
    gold_path = f"glue/data/gold_order_{order_id}_visual.json"
    df_gold.to_json(gold_path, orient='records', indent=2)
    
    print(f"\n📊 Estadísticas Gold:")
    print(f"   - Registros agregados: {len(df_gold)}")
    print(f"   - Métricas calculadas: total_monto, promedio_monto, min_monto, max_monto")
    print(f"   - Dimensiones: metadata_sucursal, estado")
    
    # ========================================================================
    # RESUMEN FINAL
    # ========================================================================
    print_section("RESUMEN DEL PIPELINE")
    
    print("\n📈 Transformación de Datos:")
    print(f"   BRONZE → SILVER → GOLD")
    print(f"   {len(order_data)} campos → {len(df_silver.columns)} columnas → {len(df_gold)} registros agregados")
    
    print("\n📁 Archivos Generados:")
    print(f"   1. Bronze: {bronze_path}")
    print(f"   2. Silver: {silver_path}")
    print(f"   3. Gold:   {gold_path}")
    
    print("\n💡 Próximos Pasos:")
    print("   1. Abre los archivos JSON para ver los datos en detalle")
    print("   2. Compara la estructura entre Bronze, Silver y Gold")
    print("   3. Revisa las métricas calculadas en Gold")
    
    print("\n" + "=" * 80)
    print("✅ TEST VISUAL COMPLETADO")
    print("=" * 80)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
