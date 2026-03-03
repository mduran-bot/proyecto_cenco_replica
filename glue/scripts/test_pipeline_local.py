"""
Script de Prueba Local del Pipeline Bronze-to-Silver

Este script simula el pipeline completo usando pandas (sin PySpark)
para que puedas probarlo localmente y ver qué hace cada paso.

Ejecutar: python glue/scripts/test_pipeline_local.py
"""

import sys
import os
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
    END = '\033[0m'

def print_section(title):
    print(f"\n{Colors.BLUE}{'='*70}")
    print(f"{title}")
    print(f"{'='*70}{Colors.END}\n")

def print_step(step_num, step_name):
    print(f"\n{Colors.GREEN}>>> PASO {step_num}: {step_name}{Colors.END}\n")

def print_dataframe(df, columns=None):
    if columns:
        print(df[columns].to_string(index=False))
    else:
        print(df.to_string(index=False))
    print()


def main():
    print_section("PRUEBA LOCAL DEL PIPELINE BRONZE-TO-SILVER")
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("Este script simula el pipeline completo con datos de ejemplo\n")
    
    # ========================================================================
    # DATOS DE ENTRADA (Bronze - Simulando datos de Janis API)
    # ========================================================================
    
    print_section("DATOS ORIGINALES (Bronze - Crudos de Janis API)")
    
    data = {
        'id': ['12345', '12345', '67890', '11111'],
        'dateCreated': ['1609459200', '1609459500', '1609459200', '1609459800'],
        'status': ['  pending  ', '  confirmed  ', 'delivered', '  pending  '],
        'email': ['  USER@TEST.COM  ', 'user@test.com', 'jane@test.com', 'BOB@TEST.COM'],
        'phone': ['(01) 234-5678', '(01) 234-5678', '(01) 987-6543', '(01) 111-2222'],
        'quantity': ['10', '10', '5', '8'],
        'quantity_picked': ['8', '9', '5', None],
        'amount': ['150.50', '150.50', '75.25', '120.00'],
        'originalAmount': ['145.00', '145.00', '75.25', '115.00']
    }
    
    df = pd.DataFrame(data)
    print("Problemas en los datos:")
    print("  ❌ Espacios en blanco en status y email")
    print("  ❌ Tipos incorrectos (todo es string)")
    print("  ❌ Emails sin normalizar (mayúsculas)")
    print("  ❌ Teléfonos sin formato estándar")
    print("  ❌ Valores faltantes (quantity_picked)")
    print("  ❌ Duplicados (id=12345 aparece 2 veces)")
    print()
    print_dataframe(df)
    
    # ========================================================================
    # PASO 1: LIMPIEZA DE DATOS
    # ========================================================================
    
    print_step(1, "LIMPIEZA DE DATOS (DataCleaner)")
    print("Acción: Eliminar espacios en blanco\n")
    
    # Simular DataCleaner (trim whitespace)
    df['status'] = df['status'].str.strip()
    df['email'] = df['email'].str.strip()
    
    print("Resultado:")
    print_dataframe(df, columns=['status', 'email'])
    print(f"{Colors.YELLOW}✓ Espacios eliminados{Colors.END}")
    
    # ========================================================================
    # PASO 2: CONVERSIÓN DE TIPOS
    # ========================================================================
    
    print_step(2, "CONVERSIÓN DE TIPOS (DataTypeConverter)")
    print("Acción: Convertir strings a tipos correctos\n")
    
    converter = DataTypeConverter()
    
    # Convertir timestamp
    df['dateCreated'] = df['dateCreated'].apply(
        lambda x: converter.convert_bigint_to_timestamp(int(x))
    )
    
    # Convertir numéricos
    df['quantity'] = df['quantity'].astype(int)
    df['amount'] = df['amount'].astype(float)
    df['originalAmount'] = df['originalAmount'].astype(float)
    df['quantity_picked'] = pd.to_numeric(df['quantity_picked'], errors='coerce')
    
    print("Resultado:")
    print("Tipos de datos:")
    print(f"  - dateCreated: {df['dateCreated'].dtype} (antes: string)")
    print(f"  - quantity: {df['quantity'].dtype} (antes: string)")
    print(f"  - amount: {df['amount'].dtype} (antes: string)")
    print()
    print_dataframe(df, columns=['dateCreated', 'quantity', 'amount'])
    print(f"{Colors.YELLOW}✓ Tipos convertidos correctamente{Colors.END}")
    
    # ========================================================================
    # PASO 3: NORMALIZACIÓN
    # ========================================================================
    
    print_step(3, "NORMALIZACIÓN (DataNormalizer)")
    print("Acción: Normalizar emails y teléfonos\n")
    
    normalizer = DataNormalizer()
    
    # Normalizar emails
    df['email'] = df['email'].apply(normalizer.validate_and_clean_email)
    
    # Normalizar teléfonos
    df['phone'] = df['phone'].apply(
        lambda x: normalizer.normalize_phone_number(x, country_code='51')
    )
    
    print("Resultado:")
    print_dataframe(df, columns=['email', 'phone'])
    print(f"{Colors.YELLOW}✓ Emails en lowercase{Colors.END}")
    print(f"{Colors.YELLOW}✓ Teléfonos en formato internacional (+51){Colors.END}")
    
    # ========================================================================
    # PASO 4: MANEJO DE GAPS Y CÁLCULOS
    # ========================================================================
    
    print_step(4, "MANEJO DE GAPS (DataGapHandler)")
    print("Acción: Calcular campos derivados\n")
    
    gap_handler = DataGapHandler()
    
    # Calcular campos
    df = gap_handler.calculate_items_qty_missing(df)
    df = gap_handler.calculate_total_changes(df)
    
    print("Resultado:")
    print("Campos calculados:")
    print("  - items_qty_missing = quantity - quantity_picked")
    print("  - total_changes = amount - originalAmount")
    print()
    print_dataframe(df, columns=['quantity', 'quantity_picked', 'items_qty_missing', 'amount', 'originalAmount', 'total_changes'])
    print(f"{Colors.YELLOW}✓ Campos derivados calculados{Colors.END}")
    
    # ========================================================================
    # PASO 5: DETECCIÓN DE DUPLICADOS
    # ========================================================================
    
    print_step(5, "DETECCIÓN DE DUPLICADOS (DuplicateDetector)")
    print("Acción: Marcar duplicados por business key (id)\n")
    
    # Simular DuplicateDetector
    df['is_duplicate'] = df.duplicated(subset=['id'], keep=False)
    df['duplicate_group_id'] = df.groupby('id').ngroup()
    df.loc[~df['is_duplicate'], 'duplicate_group_id'] = None
    
    print("Resultado:")
    print_dataframe(df, columns=['id', 'dateCreated', 'is_duplicate', 'duplicate_group_id'])
    print(f"{Colors.YELLOW}✓ Duplicados detectados: {df['is_duplicate'].sum()} registros{Colors.END}")
    
    # ========================================================================
    # PASO 6: RESOLUCIÓN DE CONFLICTOS
    # ========================================================================
    
    print_step(6, "RESOLUCIÓN DE CONFLICTOS (ConflictResolver)")
    print("Acción: Quedarse con el registro más reciente por id\n")
    
    print("Antes de resolver:")
    print(f"  Total registros: {len(df)}")
    print(f"  Duplicados: {df['is_duplicate'].sum()}")
    print()
    
    # Simular ConflictResolver (quedarse con el más reciente)
    df_sorted = df.sort_values('dateCreated', ascending=False)
    df_resolved = df_sorted.drop_duplicates(subset=['id'], keep='first').copy()
    
    print("Después de resolver:")
    print(f"  Total registros: {len(df_resolved)}")
    print(f"  Duplicados eliminados: {len(df) - len(df_resolved)}")
    print()
    print_dataframe(df_resolved, columns=['id', 'dateCreated', 'status'])
    print(f"{Colors.YELLOW}✓ Conflictos resueltos (quedó el más reciente){Colors.END}")
    
    # ========================================================================
    # PASO 7: GENERAR REPORTE DE CALIDAD
    # ========================================================================
    
    print_step(7, "REPORTE DE CALIDAD")
    
    # Marcar campos no disponibles (simulación)
    unavailable_fields = ['items_substituted_qty', 'items_qty_missing', 'total_changes']
    df_resolved = gap_handler.mark_unavailable_fields(df_resolved, unavailable_fields)
    
    # Generar reporte
    report = gap_handler.generate_data_gap_report(df_resolved)
    
    print("Métricas de Calidad:")
    print(f"  - Total registros: {report['total_records']}")
    print(f"  - Registros con gaps: {report['records_with_gaps']}")
    print(f"  - Impacto general: {report['impact_assessment']}")
    print(f"  - Campos calculados: {list(report['calculated_fields'].keys())}")
    print()
    
    # ========================================================================
    # RESULTADO FINAL
    # ========================================================================
    
    print_section("DATOS FINALES (Silver - Listos para Iceberg)")
    
    # Eliminar columnas auxiliares
    df_final = df_resolved.drop(columns=['is_duplicate', 'duplicate_group_id', '_data_gaps'])
    
    print("Mejoras aplicadas:")
    print("  ✅ JSON aplanado (si hubiera estructuras anidadas)")
    print("  ✅ Datos limpios (sin espacios)")
    print("  ✅ Tipos correctos (timestamp, int, float)")
    print("  ✅ Emails normalizados (lowercase)")
    print("  ✅ Teléfonos normalizados (formato internacional)")
    print("  ✅ Campos calculados (items_qty_missing, total_changes)")
    print("  ✅ Sin duplicados (solo el más reciente)")
    print("  ✅ Metadata de calidad generada")
    print()
    print_dataframe(df_final)
    
    # ========================================================================
    # COMPARACIÓN ANTES/DESPUÉS
    # ========================================================================
    
    print_section("COMPARACIÓN ANTES/DESPUÉS")
    
    print("ANTES (Bronze):")
    print(f"  - Registros: {len(df)}")
    print(f"  - Duplicados: {df['is_duplicate'].sum()}")
    print(f"  - Tipos: Todos string")
    print(f"  - Emails: Con espacios y mayúsculas")
    print(f"  - Teléfonos: Sin formato estándar")
    print()
    
    print("DESPUÉS (Silver):")
    print(f"  - Registros: {len(df_final)} (duplicados eliminados)")
    print(f"  - Duplicados: 0")
    print(f"  - Tipos: timestamp, int, float")
    print(f"  - Emails: Normalizados (lowercase)")
    print(f"  - Teléfonos: Formato internacional (+51)")
    print(f"  - Campos adicionales: items_qty_missing, total_changes")
    print()
    
    print(f"{Colors.GREEN}✓ PIPELINE COMPLETADO EXITOSAMENTE{Colors.END}")
    print()
    print("Próximo paso: Escribir estos datos a Iceberg con IcebergWriter")
    print()


if __name__ == "__main__":
    main()
