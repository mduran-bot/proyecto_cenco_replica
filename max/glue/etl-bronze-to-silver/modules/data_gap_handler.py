"""
DataGapHandler Module

This module handles missing data in critical fields by marking records with gaps,
filling default values, and optionally filtering incomplete records.

Updated for Task 9.1:
- Lee data_gaps desde redshift_schemas.json
- Asigna NULL a campos faltantes
- Registra en tabla data_gaps_log (entity_type, field_name, record_count)
"""

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql.functions import col, when, coalesce, lit, current_timestamp
from pyspark.sql.types import StructType, StructField, StringType, IntegerType, TimestampType
from typing import List, Dict, Optional, Any
import json
import os
from datetime import datetime


class DataGapHandler:
    """
    Handles data gaps in critical fields.
    
    Transformations applied:
    - Mark records with null values in critical columns
    - Fill null values with configured defaults
    - Optionally filter out incomplete records
    - Add NULL columns for documented data gaps from redshift_schemas.json
    - Log data gaps to data_gaps_log table
    
    Adds one column to the DataFrame:
    - has_critical_gaps: Boolean indicating if the record has gaps in critical fields
    """
    
    def __init__(self, config_path: Optional[str] = None, spark: Optional[SparkSession] = None):
        """
        Initialize the DataGapHandler.
        
        Args:
            config_path: Ruta al archivo redshift_schemas.json
            spark: SparkSession para logging a data_gaps_log
        """
        self.config_path = config_path
        self.spark = spark
        self.schemas_config = None
        self.data_gaps_log = []  # Buffer para logs de gaps
        
        if config_path and os.path.exists(config_path):
            with open(config_path, 'r') as f:
                self.schemas_config = json.load(f)
    
    def transform(self, df: DataFrame, config: dict) -> DataFrame:
        """
        Handle data gaps according to configuration.
        
        Args:
            df: Input PySpark DataFrame
            config: Configuration dictionary with:
                - data_gaps.critical_columns: List of column names that are critical
                - data_gaps.default_values: Dict mapping column names to default values
                - data_gaps.reject_incomplete: Boolean to filter incomplete records
            
        Returns:
            DataFrame with has_critical_gaps column added and gaps handled
            
        Raises:
            ValueError: If critical_columns are specified but don't exist in DataFrame
        """
        # Get data gaps configuration
        gaps_config = config.get("data_gaps", {})
        critical_columns = gaps_config.get("critical_columns", [])
        default_values = gaps_config.get("default_values", {})
        reject_incomplete = gaps_config.get("reject_incomplete", False)
        
        # Validate critical columns if specified
        if critical_columns:
            missing_columns = [col_name for col_name in critical_columns 
                             if col_name not in df.columns]
            if missing_columns:
                raise ValueError(
                    f"Critical columns not found in DataFrame: {missing_columns}"
                )
        
        # Mark critical gaps
        df_marked = self._mark_critical_gaps(df, critical_columns)
        
        # Fill defaults if configured
        if default_values:
            df_marked = self._fill_defaults(df_marked, default_values)
        
        # Filter incomplete records if configured
        if reject_incomplete:
            df_marked = self._filter_incomplete(df_marked, reject_incomplete)
        
        return df_marked
    
    def _mark_critical_gaps(self, df: DataFrame, critical_columns: List[str]) -> DataFrame:
        """
        Mark records that have null values in critical columns.
        
        Args:
            df: Input DataFrame
            critical_columns: List of column names that are critical
            
        Returns:
            DataFrame with has_critical_gaps column added
        """
        if not critical_columns:
            # If no critical columns specified, mark all as having no gaps
            return df.withColumn("has_critical_gaps", lit(False))
        
        # Build condition to check if any critical column is null
        # Start with False, then OR with each null check
        gap_condition = lit(False)
        
        for col_name in critical_columns:
            gap_condition = gap_condition | col(col_name).isNull()
        
        # Add the has_critical_gaps column
        df_marked = df.withColumn("has_critical_gaps", gap_condition)
        
        return df_marked
    
    def _fill_defaults(self, df: DataFrame, default_values: Dict[str, any]) -> DataFrame:
        """
        Fill null values in specified columns with default values.
        
        Args:
            df: DataFrame to fill
            default_values: Dictionary mapping column names to default values
            
        Returns:
            DataFrame with null values filled with defaults
        """
        if not default_values:
            return df
        
        # Build list of columns with defaults applied
        filled_cols = []
        
        for field in df.schema.fields:
            if field.name in default_values:
                # Fill null values with the configured default
                default_value = default_values[field.name]
                filled_cols.append(
                    coalesce(col(field.name), lit(default_value)).alias(field.name)
                )
            else:
                # Keep other columns as-is
                filled_cols.append(col(field.name))
        
        return df.select(*filled_cols)
    
    def _filter_incomplete(self, df: DataFrame, reject_incomplete: bool) -> DataFrame:
        """
        Filter out records with critical gaps if configured.
        
        Args:
            df: DataFrame with has_critical_gaps column
            reject_incomplete: Boolean indicating whether to filter incomplete records
            
        Returns:
            DataFrame with incomplete records filtered out if reject_incomplete is True
        """
        if not reject_incomplete:
            return df
        
        # Filter out records where has_critical_gaps is True
        return df.filter(col("has_critical_gaps") == False)
    
    # ========== NEW METHODS FOR TASK 9.1 ==========
    
    def get_data_gaps_for_table(self, table_name: str) -> List[str]:
        """
        Obtiene la lista de campos con data gaps para una tabla específica.
        
        Args:
            table_name: Nombre de la tabla (ej: wms_orders, products)
            
        Returns:
            Lista de nombres de campos que tienen data gaps
        """
        if not self.schemas_config:
            return []
        
        tables = self.schemas_config.get('tables', {})
        table_config = tables.get(table_name, {})
        fields = table_config.get('fields', {})
        
        # Identificar campos que no están disponibles en la API
        # Estos son campos que no tienen source_field o están marcados como data_gap
        data_gap_fields = []
        for field_name, field_config in fields.items():
            if field_config.get('data_gap', False) or field_config.get('source_field') is None:
                # Si el campo no tiene source_field y no es calculado, es un data gap
                if not field_config.get('calculated', False):
                    data_gap_fields.append(field_name)
        
        return data_gap_fields
    
    def add_null_columns_for_gaps(self, df: DataFrame, table_name: str, entity_type: str) -> DataFrame:
        """
        Agrega columnas con NULL para campos con data gaps.
        
        Args:
            df: DataFrame de PySpark
            table_name: Nombre de la tabla Gold (ej: wms_orders)
            entity_type: Tipo de entidad (ej: orders, products)
            
        Returns:
            DataFrame con columnas NULL agregadas y logs registrados
        """
        data_gap_fields = self.get_data_gaps_for_table(table_name)
        
        if not data_gap_fields:
            return df
        
        record_count = df.count()
        
        # Agregar columnas NULL para cada data gap
        for field_name in data_gap_fields:
            if field_name not in df.columns:
                # Determinar el tipo de dato desde la configuración
                field_type = self._get_field_type(table_name, field_name)
                df = df.withColumn(field_name, lit(None).cast(field_type))
                
                # Registrar el gap en el buffer de logs
                self.data_gaps_log.append({
                    'entity_type': entity_type,
                    'table_name': table_name,
                    'field_name': field_name,
                    'record_count': record_count,
                    'timestamp': datetime.now().isoformat()
                })
        
        return df
    
    def _get_field_type(self, table_name: str, field_name: str) -> str:
        """
        Obtiene el tipo de dato de un campo desde la configuración.
        
        Args:
            table_name: Nombre de la tabla
            field_name: Nombre del campo
            
        Returns:
            Tipo de dato en formato PySpark (string, integer, etc.)
        """
        if not self.schemas_config:
            return "string"
        
        tables = self.schemas_config.get('tables', {})
        table_config = tables.get(table_name, {})
        fields = table_config.get('fields', {})
        field_config = fields.get(field_name, {})
        
        # Mapear tipos Redshift a tipos PySpark
        redshift_type = field_config.get('type', 'VARCHAR(255)')
        
        if 'VARCHAR' in redshift_type or 'TEXT' in redshift_type:
            return "string"
        elif 'INTEGER' in redshift_type or 'INT' in redshift_type:
            return "integer"
        elif 'BIGINT' in redshift_type:
            return "long"
        elif 'DECIMAL' in redshift_type or 'NUMERIC' in redshift_type:
            return "decimal(18,2)"
        elif 'TIMESTAMP' in redshift_type:
            return "timestamp"
        elif 'BOOLEAN' in redshift_type:
            return "boolean"
        else:
            return "string"
    
    def flush_data_gaps_log(self, output_path: Optional[str] = None) -> Optional[DataFrame]:
        """
        Escribe los logs de data gaps a la tabla data_gaps_log.
        
        Args:
            output_path: Ruta de salida para la tabla (opcional, usa Iceberg por defecto)
            
        Returns:
            DataFrame con los logs escritos, o None si no hay logs
        """
        if not self.spark:
            # Si no hay Spark, retornar None
            return None
        
        if not self.data_gaps_log:
            return None
        
        # Crear DataFrame de logs
        schema = StructType([
            StructField("gap_id", StringType(), False),
            StructField("entity_type", StringType(), False),
            StructField("table_name", StringType(), True),
            StructField("field_name", StringType(), False),
            StructField("record_count", IntegerType(), False),
            StructField("timestamp", TimestampType(), False)
        ])
        
        # Agregar gap_id único a cada log
        logs_with_id = []
        for i, log in enumerate(self.data_gaps_log):
            log_copy = log.copy()
            log_copy['gap_id'] = f"{log['entity_type']}_{log['field_name']}_{i}"
            # Convertir timestamp string a datetime si es necesario
            if isinstance(log_copy['timestamp'], str):
                log_copy['timestamp'] = datetime.fromisoformat(log_copy['timestamp'])
            logs_with_id.append(log_copy)
        
        logs_df = self.spark.createDataFrame(logs_with_id, schema=schema)
        
        # Escribir a tabla Iceberg o path especificado
        if output_path:
            logs_df.write.mode("append").parquet(output_path)
        else:
            # Escribir a tabla Iceberg silver.data_gaps_log
            try:
                logs_df.writeTo("silver.data_gaps_log").append()
            except Exception as e:
                # Si falla, escribir a parquet como fallback
                print(f"Warning: Could not write to Iceberg table, writing to parquet: {e}")
                logs_df.write.mode("append").parquet("s3://data-lake-silver/data_gaps_log/")
        
        # Limpiar buffer
        self.data_gaps_log = []
        
        return logs_df
