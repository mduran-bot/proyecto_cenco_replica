"""
Test del Pipeline Silver-to-Gold usando pandas (sin PySpark)
"""
import sys
import os
import logging
import json
from datetime import datetime
import pandas as pd

# Agregar path de módulos
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def create_sample_silver_data():
    """Crear datos de prueba en formato Silver"""
    data = {
        "id": ["1001", "1002", "1003", "1004", "1005", "1006", "1007", "1008", "1009", "1010"],
        "cliente_nombre": ["Juan Pérez", "María González", "Pedro López", "Ana Martínez", "Carlos Ruiz", 
                          "Laura Sánchez", "Roberto Silva", "Diana Torres", "Diego Torres", "Sofia Ramírez"],
        "producto_nombre": ["Laptop HP", "Teclado Mecánico", "Mouse Inalámbrico", "Monitor 27\"", "Webcam HD",
                           "Auriculares", "Impresora Láser", "Tablet", "Notebook Gaming", "SSD 1TB"],
        "monto": [2500.80, 850.50, 350.00, 3200.00, 450.00, 280.00, 5600.00, 1200.00, 12500.99, 890.00],
        "fecha_venta": [
            "2026-02-15T10:30:00", "2026-02-16T14:20:00", "2026-02-17T09:15:00", "2026-02-18T11:45:00",
            "2026-02-18T16:30:00", "2026-02-19T08:00:00", "2026-02-19T10:15:00", "2026-02-19T12:30:00",
            "2026-02-19T14:00:00", "2026-02-19T15:45:00"
        ],
        "estado": ["completado", "completado", "pendiente", "completado", "cancelado", 
                  "completado", "completado", "pendiente", "completado", "rechazado"],
        "metadata_sucursal": ["Sucursal Centro", "Sucursal Norte", "Sucursal Centro", "Sucursal Sur", "Sucursal Norte",
                             "Sucursal Centro", "Sucursal Sur", "Sucursal Norte", "Sucursal Centro", "Sucursal Sur"],
        "es_valido": [True, True, True, True, False, True, True, False, True, False],
        "has_critical_gaps": [False, False, False, False, False, True, False, True, False, False]
    }
    
    df = pd.DataFrame(data)
    df['fecha_venta'] = pd.to_datetime(df['fecha_venta'])
    return df

def aggregate_data(df):
    """Agregar datos por sucursal y estado"""
    # Agregar dimensiones de tiempo
    df['year'] = df['fecha_venta'].dt.year
    df['month'] = df['fecha_venta'].dt.month
    df['day'] = df['fecha_venta'].dt.day
    df['week'] = df['fecha_venta'].dt.isocalendar().week
    
    # Agregar por sucursal y estado
    agg_df = df.groupby(['metadata_sucursal', 'estado']).agg({
        'monto': ['sum', 'mean', 'min', 'max'],
        'id': 'count'
    }).reset_index()
    
    # Aplanar columnas multi-nivel
    agg_df.columns = ['metadata_sucursal', 'estado', 'total_monto', 'promedio_monto', 'min_monto', 'max_monto', 'num_registros']
    
    return agg_df

def validate_quality(df):
    """Validar calidad de datos"""
    # Completeness: campos críticos no nulos
    df['_completeness_ok'] = df['estado'].notna() & df['metadata_sucursal'].notna()
    
    # Validity: valores permitidos
    valid_estados = ['completado', 'pendiente', 'cancelado', 'rechazado']
    df['_validity_ok'] = df['estado'].isin(valid_estados)
    
    # Range: valores numéricos en rango
    df['_range_ok'] = (df['total_monto'] >= 0) & (df['total_monto'] <= 99999999)
    
    # Consolidar
    df['_quality_valid'] = df['_completeness_ok'] & df['_validity_ok'] & df['_range_ok']
    df['_quality_issues'] = ''
    df.loc[~df['_completeness_ok'], '_quality_issues'] += 'COMPLETENESS_FAIL;'
    df.loc[~df['_validity_ok'], '_quality_issues'] += 'VALIDITY_FAIL;'
    df.loc[~df['_range_ok'], '_quality_issues'] += 'RANGE_FAIL;'
    
    # Limpiar columnas intermedias
    df = df.drop(columns=['_completeness_ok', '_validity_ok', '_range_ok'])
    
    return df

def handle_errors(df):
    """Manejar errores"""
    df['_error_handled'] = ~df['_quality_valid']
    return df

def main():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
    logger = logging.getLogger('SilverToGoldTest')
    
    logger.info("=" * 60)
    logger.info("TEST PIPELINE SILVER → GOLD (PANDAS)")
    logger.info("=" * 60)
    
    # Crear datos de prueba Silver
    logger.info("\n1. Creando datos de prueba en formato Silver...")
    df_silver = create_sample_silver_data()
    logger.info(f"   Registros creados: {len(df_silver)}")
    
    logger.info("\n   Muestra de datos Silver:")
    print(df_silver.head())
    
    # Guardar Silver localmente
    silver_path = "glue/data/test_silver_pandas.json"
    logger.info(f"\n2. Guardando datos Silver en: {silver_path}")
    df_silver.to_json(silver_path, orient='records', date_format='iso', indent=2)
    
    # Ejecutar transformaciones
    logger.info("\n3. Ejecutando transformaciones Silver → Gold...")
    
    # Agregación
    logger.info("\n   3.1 SilverToGoldAggregator...")
    df_gold = aggregate_data(df_silver)
    logger.info(f"       → {len(df_gold)} registros agregados")
    
    # Validación de calidad
    logger.info("\n   3.2 DataQualityValidator...")
    df_gold = validate_quality(df_gold)
    logger.info(f"       → {len(df_gold)} registros validados")
    
    # Manejo de errores
    logger.info("\n   3.3 ErrorHandler...")
    df_gold = handle_errors(df_gold)
    logger.info(f"       → {len(df_gold)} registros después de error handling")
    
    # Agregar timestamp de procesamiento
    df_gold['_processing_timestamp'] = datetime.now().isoformat()
    
    # Guardar Gold localmente
    gold_path = "glue/data/test_gold_pandas.json"
    logger.info(f"\n4. Guardando datos Gold en: {gold_path}")
    df_gold.to_json(gold_path, orient='records', indent=2)
    
    # Verificar resultados
    logger.info("\n5. Verificando resultados en Gold...")
    logger.info(f"   Total registros en Gold: {len(df_gold)}")
    
    logger.info("\n   Columnas en Gold:")
    for col_name in sorted(df_gold.columns):
        logger.info(f"   - {col_name}")
    
    logger.info("\n   Muestra de datos Gold (agregados):")
    print(df_gold[['metadata_sucursal', 'estado', 'total_monto', 'promedio_monto', 
                   'min_monto', 'max_monto', 'num_registros', '_quality_valid']].to_string())
    
    # Análisis de calidad
    logger.info("\n6. Análisis de Calidad de Datos:")
    valid_count = df_gold['_quality_valid'].sum()
    invalid_count = (~df_gold['_quality_valid']).sum()
    total = len(df_gold)
    
    logger.info(f"   Registros válidos: {valid_count}/{total} ({valid_count/total*100:.1f}%)")
    logger.info(f"   Registros inválidos: {invalid_count}/{total} ({invalid_count/total*100:.1f}%)")
    
    if invalid_count > 0:
        logger.info("\n   Registros con problemas de calidad:")
        print(df_gold[~df_gold['_quality_valid']][['metadata_sucursal', 'estado', '_quality_issues']].to_string())
    
    # Resumen por sucursal
    logger.info("\n7. Resumen por Sucursal:")
    sucursal_summary = df_gold.groupby('metadata_sucursal').agg({
        'total_monto': 'sum',
        'num_registros': 'sum'
    }).reset_index()
    print(sucursal_summary.to_string())
    
    logger.info("\n" + "=" * 60)
    logger.info("✅ TEST COMPLETADO EXITOSAMENTE")
    logger.info("=" * 60)
    logger.info(f"\nArchivos generados:")
    logger.info(f"  - Silver: {silver_path}")
    logger.info(f"  - Gold:   {gold_path}")
    logger.info("=" * 60)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
