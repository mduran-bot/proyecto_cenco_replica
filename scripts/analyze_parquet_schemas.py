#!/usr/bin/env python3
"""
Analiza esquemas de archivos Parquet de S3 Gold
"""
import pyarrow.parquet as pq
import json
from pathlib import Path

def analyze_parquet_file(file_path):
    """Analiza un archivo Parquet y retorna información detallada"""
    print(f"\n{'='*80}")
    print(f"Analizando: {file_path.name}")
    print(f"{'='*80}\n")
    
    # Leer metadata
    parquet_file = pq.ParquetFile(file_path)
    
    # Schema
    schema = parquet_file.schema_arrow
    print("SCHEMA:")
    print("-" * 80)
    for i, field in enumerate(schema):
        nullable = "NULL" if field.nullable else "NOT NULL"
        print(f"{i+1:3d}. {field.name:40s} {str(field.type):30s} {nullable}")
    
    print(f"\nTotal columnas: {len(schema)}")
    
    # Metadata
    print("\n\nMETADATA:")
    print("-" * 80)
    metadata = parquet_file.metadata
    print(f"Número de row groups: {metadata.num_row_groups}")
    print(f"Número de filas: {metadata.num_rows}")
    print(f"Número de columnas: {metadata.num_columns}")
    
    # Leer primeras filas
    table = pq.read_table(file_path)
    df = table.to_pandas()
    
    print("\n\nPRIMERAS 3 FILAS:")
    print("-" * 80)
    print(df.head(3).to_string())
    
    print("\n\nESTADÍSTICAS:")
    print("-" * 80)
    print(df.describe(include='all').to_string())
    
    # Valores nulos
    print("\n\nVALORES NULOS POR COLUMNA:")
    print("-" * 80)
    null_counts = df.isnull().sum()
    null_pcts = (null_counts / len(df) * 100).round(2)
    for col in df.columns:
        if null_counts[col] > 0:
            print(f"{col:40s}: {null_counts[col]:6d} ({null_pcts[col]:5.2f}%)")
    
    # Tipos de datos únicos
    print("\n\nTIPOS DE DATOS PYTHON:")
    print("-" * 80)
    for col in df.columns:
        dtype = df[col].dtype
        print(f"{col:40s}: {dtype}")
    
    return {
        'file': file_path.name,
        'num_columns': len(schema),
        'num_rows': metadata.num_rows,
        'schema': [(field.name, str(field.type), field.nullable) for field in schema]
    }

def main():
    samples_dir = Path('./parquet_samples')
    
    if not samples_dir.exists():
        print(f"Error: Directorio {samples_dir} no existe")
        return
    
    parquet_files = list(samples_dir.glob('*.parquet'))
    
    if not parquet_files:
        print(f"No se encontraron archivos .parquet en {samples_dir}")
        return
    
    print(f"Encontrados {len(parquet_files)} archivos Parquet\n")
    
    results = []
    for file_path in parquet_files:
        try:
            result = analyze_parquet_file(file_path)
            results.append(result)
        except Exception as e:
            print(f"\nError analizando {file_path.name}: {e}")
    
    # Guardar resumen
    summary_file = samples_dir / 'schema_analysis_summary.json'
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\n\n{'='*80}")
    print(f"Resumen guardado en: {summary_file}")
    print(f"{'='*80}\n")

if __name__ == '__main__':
    main()
