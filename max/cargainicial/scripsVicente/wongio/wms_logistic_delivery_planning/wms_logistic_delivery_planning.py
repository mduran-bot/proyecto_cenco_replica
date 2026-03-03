#!/usr/bin/env python3
"""
MySQL to Parquet Extractor - Versión con particionamiento por número de archivos
Extrae una tabla específica y la divide en múltiples archivos Parquet según cantidad de registros
"""
import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional, List
import pandas as pd
import pymysql
import pyarrow as pa
import pyarrow.parquet as pq


# ============================================================================
# CONFIGURACIÓN - MODIFICAR ESTAS VARIABLES
# ============================================================================

# Tabla a procesar
TARGET_TABLE = 'wms_logistic_delivery_planning'

# Directorio de salida base
OUTPUT_BASE_DIR = Path(r"D:\tests parquets")

# Configuración de MySQL
MYSQL_CONFIG = {
    'host': 'cencodb.janis.in',
    'port': 3306,
    'user': 'cenco-replica',
    'password': 'zd2lhVnesCH2vV.9',
    'database': 'janis_wongio'
}

# Modo debug (cambiar a True para ver queries SQL y diagnóstico)
DEBUG_MODE = True

# Tamaño de batch para lectura (ajustar según RAM disponible)
BATCH_SIZE = 5000

# CONFIGURACIÓN DE PARTICIONAMIENTO
# Número de archivos Parquet en los que dividir la tabla
NUM_PARTITIONS = 2  # Ejemplo: tabla de 4000 registros → 5 archivos de ~800 registros cada uno

# Filtros opcionales (None para procesar toda la tabla)
WHERE_CLAUSE = None  # Ejemplo: "status = 'active'" o "id > 1000"

# ============================================================================


class PartitionedMySQLExtractor:
    """Extractor de datos MySQL a Parquet con particionamiento por número de archivos"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.connection = None
    
    def connect(self):
        """Conecta a MySQL"""
        try:
            self.connection = pymysql.connect(
                host=self.config['host'],
                port=self.config.get('port', 3306),
                user=self.config['user'],
                password=self.config['password'],
                database=self.config['database'],
                charset='utf8mb4',
                cursorclass=pymysql.cursors.DictCursor,
                use_unicode=True,
                client_flag=0
            )
            print(f"✓ Conectado a MySQL: {self.config['host']}/{self.config['database']}")
        except Exception as e:
            print(f"✗ Error conectando a MySQL: {e}")
            print("\nSoluciones posibles:")
            print("  1. Instalar cryptography: pip install cryptography")
            print("  2. Cambiar método de autenticación en MySQL")
            print("  3. Usar mysql_native_password en lugar de caching_sha2_password")
            raise
    
    def disconnect(self):
        """Desconecta de MySQL"""
        if self.connection:
            self.connection.close()
            print("✓ Desconectado de MySQL")
    
    def get_table_count(self, table_name: str, where_clause: Optional[str] = None) -> int:
        """
        Obtiene el número total de registros en la tabla
        
        Args:
            table_name: Nombre de la tabla
            where_clause: Cláusula WHERE opcional para filtrar
            
        Returns:
            Número total de registros
        """
        with self.connection.cursor() as cursor:
            query = f"SELECT COUNT(*) as total FROM {table_name}"
            if where_clause:
                query += f" WHERE {where_clause}"
            
            if DEBUG_MODE:
                print(f"  DEBUG - Query count: {query}")
            
            cursor.execute(query)
            result = cursor.fetchone()
            return result['total']
    
    def extract_partition(self, table_name: str, partition_num: int,
                         offset: int, limit: int, where_clause: Optional[str],
                         output_path: Path, batch_size: int = 5000) -> int:
        """
        Extrae datos de una partición específica usando LIMIT/OFFSET
        
        Args:
            table_name: Nombre de la tabla
            partition_num: Número de partición (para logging)
            offset: Offset inicial para la partición
            limit: Número máximo de registros a extraer
            where_clause: Cláusula WHERE opcional
            output_path: Ruta del archivo Parquet
            batch_size: Tamaño del batch para lectura
            
        Returns:
            Número de registros extraídos
        """
        # Construir query
        query = f"SELECT * FROM {table_name}"
        if where_clause:
            query += f" WHERE {where_clause}"
        query += f" LIMIT {limit} OFFSET {offset}"
        
        if DEBUG_MODE:
            print(f"  DEBUG - Query: {query}")
        
        # Crear directorio si no existe
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        rows_written = 0
        writer = None
        schema = None
        column_types = None  # Guardar tipos detectados
        
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(query)
                
                while True:
                    rows = cursor.fetchmany(batch_size)
                    if not rows:
                        break
                    
                    # Convertir a DataFrame
                    chunk_df = pd.DataFrame(rows)
                    
                    # Convertir tipos
                    is_first = (rows_written == 0)
                    if is_first:
                        # Primera vez: detectar tipos y guardar
                        chunk_df, column_types = self.convert_types_with_detection(
                            chunk_df, table_name, is_first_batch=True
                        )
                    else:
                        # Batches siguientes: aplicar tipos ya detectados
                        chunk_df = self.apply_column_types(chunk_df, column_types)
                    
                    if is_first:
                        # Obtener schema del primer batch
                        table = pa.Table.from_pandas(chunk_df)
                        schema = table.schema
                        # Crear writer
                        writer = pq.ParquetWriter(
                            output_path,
                            schema,
                            compression='snappy',
                            use_dictionary=True,
                            write_statistics=True
                        )
                    
                    # Escribir batch
                    table = pa.Table.from_pandas(chunk_df, schema=schema)
                    writer.write_table(table)
                    
                    rows_written += len(rows)
                    
                    # Liberar memoria
                    del chunk_df
                    del table
            
        finally:
            if writer:
                writer.close()
        
        return rows_written
    
    def convert_types_with_detection(self, df: pd.DataFrame, table_name: str, 
                                    is_first_batch: bool = False) -> tuple:
        """
        Convierte tipos de datos detectando automáticamente el tipo apropiado
        REGLA CRÍTICA: Todas las columnas 'object' DEBEN convertirse a string o numeric
        antes de pasarlas a PyArrow, nunca dejar como 'object'
        
        Returns:
            Tupla (DataFrame convertido, diccionario de tipos por columna)
        """
        column_types = {}
        
        for col in df.columns:
            original_dtype = df[col].dtype
            
            # CRÍTICO: Convertir TODAS las columnas 'object' a algo específico
            if df[col].dtype == 'object':
                non_null_values = df[col].dropna()
                
                if len(non_null_values) == 0:
                    # Columna vacía - convertir a string
                    df[col] = df[col].astype(str)
                    df[col] = df[col].replace('nan', None)
                    column_types[col] = 'string'
                    continue
                
                # Intentar detectar si es numérico puro
                numeric_count = 0
                total_sample = min(len(non_null_values), 100)
                
                for val in non_null_values.head(total_sample):
                    try:
                        float(val)
                        numeric_count += 1
                    except (ValueError, TypeError):
                        pass
                
                # Si >95% son numéricos, convertir a numeric
                if numeric_count / total_sample > 0.95:
                    if is_first_batch and DEBUG_MODE:
                        print(f"  DEBUG - Columna '{col}': Detectada como numérica ({numeric_count}/{total_sample} valores)")
                    df[col] = pd.to_numeric(df[col], errors='coerce')
                    column_types[col] = 'numeric'
                else:
                    # Cualquier cosa con valores mixtos -> STRING
                    if is_first_batch and DEBUG_MODE:
                        print(f"  DEBUG - Columna '{col}': Convertida a string (valores mixtos: {numeric_count}/{total_sample} numéricos)")
                    
                    # Convertir TODO a string, sin excepciones
                    df[col] = df[col].astype(str)
                    
                    # Limpiar valores especiales
                    df[col] = df[col].replace('None', None)
                    df[col] = df[col].replace('nan', None)
                    df[col] = df[col].replace('NaN', None)
                    df[col] = df[col].replace('', None)
                    
                    column_types[col] = 'string'
            
            # Convertir timestamps Unix a datetime
            elif df[col].dtype in ['int64', 'float64'] and 'date_' in col.lower():
                try:
                    sample_values = df[col].dropna().head(10)
                    if len(sample_values) > 0 and sample_values.min() > 1000000000:
                        df[col] = pd.to_datetime(df[col], unit='s', errors='coerce')
                        column_types[col] = 'datetime'
                        if is_first_batch and DEBUG_MODE:
                            print(f"  DEBUG - Columna '{col}': Convertida de Unix timestamp a datetime")
                    else:
                        column_types[col] = 'numeric'
                except:
                    column_types[col] = 'numeric'
            
            # Convertir a boolean
            elif df[col].dtype == 'int64':
                unique_values = df[col].dropna().unique()
                if len(unique_values) <= 2 and all(v in [0, 1] for v in unique_values):
                    bool_keywords = ['is_', 'has_', 'can_', 'should_', 'enabled', 
                                   'disabled', 'active', 'validated', 'pending', 
                                   'gift', 'infinite', 'tracking']
                    if any(keyword in col.lower() for keyword in bool_keywords):
                        df[col] = df[col].astype(bool)
                        column_types[col] = 'boolean'
                        if is_first_batch and DEBUG_MODE:
                            print(f"  DEBUG - Columna '{col}': Convertida a boolean")
                    else:
                        column_types[col] = 'numeric'
                else:
                    column_types[col] = 'numeric'
            else:
                # Mantener tipo original
                column_types[col] = str(df[col].dtype)
        
        # VERIFICACIÓN FINAL: Asegurar que NO queden columnas 'object'
        for col in df.columns:
            if df[col].dtype == 'object':
                if is_first_batch:
                    print(f"  ⚠ WARNING - Columna '{col}' aún es 'object', forzando a string")
                df[col] = df[col].astype(str)
                df[col] = df[col].replace('None', None)
                df[col] = df[col].replace('nan', None)
                column_types[col] = 'string'
        
        return df, column_types
    
    def apply_column_types(self, df: pd.DataFrame, column_types: Dict) -> pd.DataFrame:
        """
        Aplica tipos de columna ya detectados a un DataFrame
        
        Args:
            df: DataFrame a convertir
            column_types: Diccionario con tipos por columna
            
        Returns:
            DataFrame con tipos aplicados
        """
        for col, col_type in column_types.items():
            if col not in df.columns:
                continue
                
            if col_type == 'numeric':
                df[col] = pd.to_numeric(df[col], errors='coerce')
            elif col_type == 'string':
                # Convertir a string y limpiar
                df[col] = df[col].astype(str)
                df[col] = df[col].replace('None', None)
                df[col] = df[col].replace('nan', None)
                df[col] = df[col].replace('NaN', None)
                df[col] = df[col].replace('', None)
            elif col_type == 'datetime':
                df[col] = pd.to_datetime(df[col], unit='s', errors='coerce')
            elif col_type == 'boolean':
                df[col] = df[col].astype(bool)
        
        # VERIFICACIÓN FINAL: NO permitir columnas 'object'
        for col in df.columns:
            if df[col].dtype == 'object':
                df[col] = df[col].astype(str)
                df[col] = df[col].replace('None', None)
                df[col] = df[col].replace('nan', None)
        
        return df
    
    def convert_types(self, df: pd.DataFrame, table_name: str, 
                     is_first_batch: bool = False) -> pd.DataFrame:
        """Método legacy - usa convert_types_with_detection en su lugar"""
        converted_df, _ = self.convert_types_with_detection(df, table_name, is_first_batch)
        return converted_df
    
    def extract_table_partitioned(self, table_name: str, date_field: Optional[str],
                                 output_base_dir: Path, ref_config: Optional[Dict] = None,
                                 start_date: Optional[datetime] = None,
                                 end_date: Optional[datetime] = None,
                                 batch_size: int = 5000,
                                 date_is_unix: bool = False) -> Dict:
        """
        Extrae tabla completa particionada por día
        
        Args:
            table_name: Nombre de la tabla
            date_field: Campo de fecha (None si usa referencia)
            output_base_dir: Directorio base de salida
            ref_config: Configuración de referencia
            start_date: Fecha inicial (None para usar mínimo de tabla)
            end_date: Fecha final (None para usar máximo de tabla)
            batch_size: Tamaño del batch
            
        Returns:
            Diccionario con metadata de la extracción
        """
        print(f"\n{'='*70}")
        print(f"Extrayendo tabla: {table_name}")
        print(f"{'='*70}")
        
        # Obtener rango de fechas
        print("\nObteniendo rango de fechas...")
        min_date, max_date = self.get_date_range(table_name, date_field, ref_config)
        
        # Usar fechas especificadas o las de la tabla
        start = start_date or min_date
        end = end_date or max_date
        
        print(f"  Rango en tabla: {min_date} a {max_date}")
        print(f"  Rango a procesar: {start} a {end}")
        
        # Asegurar que start y end sean datetime
        if not isinstance(start, datetime):
            start = pd.to_datetime(start)
        if not isinstance(end, datetime):
            end = pd.to_datetime(end)
        
        # Generar lista de días a procesar
        current_date = start.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date_normalized = end.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        days_to_process = []
        while current_date <= end_date_normalized:
            days_to_process.append(current_date)
            current_date += timedelta(days=1)
        
        print(f"  Total de días a procesar: {len(days_to_process)}")
        
        # Procesar cada día
        total_rows = 0
        total_files = 0
        total_size_mb = 0
        partitions = []
        
        for idx, partition_date in enumerate(days_to_process, 1):
            # Construir ruta de salida: año/mes/día/hora/archivo.parquet
            year = partition_date.strftime('%Y')
            month = partition_date.strftime('%m')
            day = partition_date.strftime('%d')
            hour = partition_date.strftime('%H')
            
            partition_dir = output_base_dir / table_name / year / month / day / hour
            output_file = partition_dir / f"{table_name}_{partition_date.strftime('%Y%m%d')}.parquet"
            
            # Extraer partición
            print(f"\n[{idx}/{len(days_to_process)}] Procesando {partition_date.strftime('%Y-%m-%d')}...", end=' ')
            
            try:
                rows = self.extract_partition(
                    table_name, date_field, partition_date, 
                    ref_config, output_file, batch_size, 
                    debug=DEBUG_MODE, date_is_unix=date_is_unix
                )
                
                if rows:
                    file_size_mb = output_file.stat().st_size / (1024 * 1024)
                    total_rows += rows
                    total_files += 1
                    total_size_mb += file_size_mb
                    
                    print(f"✓ {rows:,} registros ({file_size_mb:.2f} MB)")
                    
                    partitions.append({
                        'date': partition_date.strftime('%Y-%m-%d'),
                        'file_path': str(output_file),
                        'rows': rows,
                        'size_mb': round(file_size_mb, 2)
                    })
                else:
                    print("⊘ Sin datos")
                    
            except Exception as e:
                print(f"✗ Error: {e}")
                continue
        
        # Resumen
        print(f"\n{'='*70}")
        print(f"RESUMEN DE EXTRACCIÓN")
        print(f"{'='*70}")
        print(f"  Tabla: {table_name}")
        print(f"  Archivos generados: {total_files}")
        print(f"  Total registros: {total_rows:,}")
        print(f"  Tamaño total: {total_size_mb:.2f} MB")
        print(f"  Promedio por archivo: {total_size_mb/total_files:.2f} MB" if total_files > 0 else "")
        
        # Metadata
        metadata = {
            'table_name': table_name,
            'extraction_date': datetime.now().isoformat(),
            'date_field': date_field,
            'reference_config': ref_config if ref_config and ref_config.get('enabled') else None,
            'date_range': {
                'start': start.isoformat(),
                'end': end.isoformat()
            },
            'summary': {
                'total_files': total_files,
                'total_rows': total_rows,
                'total_size_mb': round(total_size_mb, 2)
            },
            'partitions': partitions
        }
        
        # Guardar metadata
        metadata_file = output_base_dir / table_name / "extraction_metadata.json"
        metadata_file.parent.mkdir(parents=True, exist_ok=True)
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        print(f"\n✓ Metadata guardada: {metadata_file}")
        
        return metadata
    
    def extract_table_partitioned(self, table_name: str, output_base_dir: Path,
                                 num_partitions: int, where_clause: Optional[str] = None,
                                 batch_size: int = 5000) -> Dict:
        """
        Extrae tabla completa particionada por número de archivos
        
        Args:
            table_name: Nombre de la tabla
            output_base_dir: Directorio base de salida
            num_partitions: Número de archivos Parquet a generar
            where_clause: Cláusula WHERE opcional para filtrar
            batch_size: Tamaño del batch para lectura
            
        Returns:
            Diccionario con metadata de la extracción
        """
        print(f"\n{'='*70}")
        print(f"Extrayendo tabla: {table_name}")
        print(f"{'='*70}")
        
        # Obtener total de registros
        print("\nContando registros...")
        total_records = self.get_table_count(table_name, where_clause)
        print(f"  Total de registros: {total_records:,}")
        
        if total_records == 0:
            print("✗ No hay registros para procesar")
            return {
                'table_name': table_name,
                'extraction_date': datetime.now().isoformat(),
                'summary': {
                    'total_files': 0,
                    'total_rows': 0,
                    'total_size_mb': 0
                },
                'partitions': []
            }
        
        # Calcular registros por partición
        records_per_partition = total_records // num_partitions
        remainder = total_records % num_partitions
        
        print(f"  Número de particiones: {num_partitions}")
        print(f"  Registros por partición: ~{records_per_partition:,}")
        if remainder > 0:
            print(f"  Registros adicionales en última partición: {remainder}")
        
        # Crear directorio de salida
        output_dir = output_base_dir / table_name
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Procesar cada partición
        total_rows = 0
        total_size_mb = 0
        partitions = []
        
        for partition_num in range(num_partitions):
            # Calcular offset y limit para esta partición
            offset = partition_num * records_per_partition
            
            # La última partición incluye el remainder
            if partition_num == num_partitions - 1:
                limit = records_per_partition + remainder
            else:
                limit = records_per_partition
            
            # Construir ruta de salida
            output_file = output_dir / f"{table_name}_part_{partition_num + 1:04d}.parquet"
            
            # Extraer partición
            print(f"\n[{partition_num + 1}/{num_partitions}] Procesando partición {partition_num + 1}...")
            print(f"  Offset: {offset:,}, Limit: {limit:,}")
            
            try:
                rows = self.extract_partition(
                    table_name, partition_num + 1, offset, limit,
                    where_clause, output_file, batch_size
                )
                
                if rows > 0:
                    file_size_mb = output_file.stat().st_size / (1024 * 1024)
                    total_rows += rows
                    total_size_mb += file_size_mb
                    
                    print(f"  ✓ {rows:,} registros escritos ({file_size_mb:.2f} MB)")
                    
                    partitions.append({
                        'partition_number': partition_num + 1,
                        'file_path': str(output_file),
                        'rows': rows,
                        'size_mb': round(file_size_mb, 2),
                        'offset': offset,
                        'limit': limit
                    })
                else:
                    print(f"  ⊘ Sin datos")
                    
            except Exception as e:
                print(f"  ✗ Error: {e}")
                import traceback
                traceback.print_exc()
                continue
        
        # Resumen
        print(f"\n{'='*70}")
        print(f"RESUMEN DE EXTRACCIÓN")
        print(f"{'='*70}")
        print(f"  Tabla: {table_name}")
        print(f"  Archivos generados: {len(partitions)}")
        print(f"  Total registros: {total_rows:,}")
        print(f"  Tamaño total: {total_size_mb:.2f} MB")
        if len(partitions) > 0:
            print(f"  Promedio por archivo: {total_size_mb/len(partitions):.2f} MB")
            print(f"  Promedio registros por archivo: {total_rows//len(partitions):,}")
        
        # Metadata
        metadata = {
            'table_name': table_name,
            'extraction_date': datetime.now().isoformat(),
            'where_clause': where_clause,
            'partitioning': {
                'num_partitions': num_partitions,
                'records_per_partition': records_per_partition,
                'total_records': total_records
            },
            'summary': {
                'total_files': len(partitions),
                'total_rows': total_rows,
                'total_size_mb': round(total_size_mb, 2)
            },
            'partitions': partitions
        }
        
        # Guardar metadata
        metadata_file = output_dir / "extraction_metadata.json"
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        print(f"\n✓ Metadata guardada: {metadata_file}")
        
        return metadata


def main():
    """Función principal"""
    
    print(f"""
{'='*70}
MySQL to Parquet - Extractor Particionado por Número de Archivos
{'='*70}

Configuración:
  - Tabla: {TARGET_TABLE}
  - Directorio salida: {OUTPUT_BASE_DIR}
  - Número de particiones: {NUM_PARTITIONS}
  - Batch size: {BATCH_SIZE:,}
  - Filtros: {WHERE_CLAUSE or 'Ninguno (toda la tabla)'}
""")
    
    # Crear extractor
    extractor = PartitionedMySQLExtractor(MYSQL_CONFIG)
    
    try:
        # Conectar
        extractor.connect()
        
        # Extraer tabla particionada
        metadata = extractor.extract_table_partitioned(
            table_name=TARGET_TABLE,
            output_base_dir=OUTPUT_BASE_DIR,
            num_partitions=NUM_PARTITIONS,
            where_clause=WHERE_CLAUSE,
            batch_size=BATCH_SIZE
        )
        
        print(f"\n{'='*70}")
        print("✓ EXTRACCIÓN COMPLETADA")
        print(f"{'='*70}\n")
        
    except Exception as e:
        print(f"\n✗ Error durante la extracción: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        # Desconectar
        extractor.disconnect()


if __name__ == "__main__":
    main()
