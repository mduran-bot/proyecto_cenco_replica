"""
DataGapHandler - Merged Module (Vicente + Max)

Este módulo combina:
- Vicente: Cálculos específicos del dominio y metadata tracking (pandas)
- Max: Filling automático y filtrado de registros incompletos (PySpark)
"""

import pandas as pd
import json
from typing import List, Dict, Any, Optional

# PySpark imports (optional)
try:
    from pyspark.sql import DataFrame as SparkDataFrame
    from pyspark.sql.functions import col, when, coalesce, lit
    PYSPARK_AVAILABLE = True
except ImportError:
    PYSPARK_AVAILABLE = False
    SparkDataFrame = None

# Reglas predefinidas
CALCULATED_FIELD_RULES = {
    'wms_orders': {
        'items_substituted_qty': {
            'formula': 'COUNT(items WHERE substitute_type = "substitute")',
            'source_fields': ['items'],
            'impact': 'medium'
        },
        'items_qty_missing': {
            'formula': 'SUM(quantity - COALESCE(quantity_picked, 0))',
            'source_fields': ['quantity', 'quantity_picked'],
            'impact': 'high'
        },
        'total_changes': {
            'formula': 'amount - originalAmount',
            'source_fields': ['amount', 'originalAmount'],
            'impact': 'low'
        }
    }
}

UNAVAILABLE_FIELDS = {
    'wms_orders': ['items_substituted_qty', 'items_qty_missing', 'total_changes'],
    'wms_order_items': ['discount_percentage', 'tax_amount']
}


class DataGapHandler:
    """Manejador de gaps de datos con soporte pandas y PySpark."""
    
    def __init__(self):
        """Inicializa el handler."""
        pass


    
    # Vicente's methods
    @staticmethod
    def calculate_items_substituted_qty(df: pd.DataFrame) -> pd.DataFrame:
        """Calcula la cantidad de items sustituidos por orden."""
        def count_substitutes(items):
            if not isinstance(items, list):
                return 0
            return sum(1 for item in items if isinstance(item, dict) and item.get('substitute_type') == 'substitute')
        
        df = df.copy()
        if 'items' in df.columns:
            df['items_substituted_qty'] = df['items'].apply(count_substitutes)
        else:
            df['items_substituted_qty'] = 0
        return df
    
    @staticmethod
    def calculate_items_qty_missing(df: pd.DataFrame) -> pd.DataFrame:
        """Calcula la cantidad faltante de items por orden."""
        df = df.copy()
        if 'quantity' in df.columns and 'quantity_picked' in df.columns:
            df['items_qty_missing'] = df['quantity'] - df['quantity_picked'].fillna(0)
        elif 'quantity' in df.columns:
            df['items_qty_missing'] = df['quantity']
        else:
            df['items_qty_missing'] = 0
        return df
    
    @staticmethod
    def calculate_total_changes(df: pd.DataFrame) -> pd.DataFrame:
        """Calcula los cambios totales en monto."""
        df = df.copy()
        if 'amount' in df.columns and 'originalAmount' in df.columns:
            df['total_changes'] = df['amount'] - df['originalAmount']
        else:
            df['total_changes'] = 0.0
        return df


    
    @staticmethod
    def mark_unavailable_fields(df: pd.DataFrame, unavailable_fields: List[str]) -> pd.DataFrame:
        """Marca campos no disponibles en metadata."""
        df = df.copy()
        
        def create_metadata(row):
            unavailable = [field for field in unavailable_fields if field in df.columns]
            calculated = [field for field in unavailable if field in row.index and pd.notna(row[field])]
            
            impact = 'low'
            for field in unavailable:
                if field in CALCULATED_FIELD_RULES.get('wms_orders', {}):
                    field_impact = CALCULATED_FIELD_RULES['wms_orders'][field].get('impact', 'low')
                    if field_impact == 'high':
                        impact = 'high'
                    elif field_impact == 'medium' and impact == 'low':
                        impact = 'medium'
            
            return json.dumps({
                'unavailable_fields': unavailable,
                'calculated_fields': calculated,
                'impact': impact
            })
        
        df['_data_gaps'] = df.apply(create_metadata, axis=1)
        return df
    
    @staticmethod
    def generate_data_gap_report(df: pd.DataFrame) -> Dict[str, Any]:
        """Genera un reporte de gaps de datos."""
        if '_data_gaps' not in df.columns:
            return {
                'total_records': len(df),
                'records_with_gaps': 0,
                'unavailable_fields': {},
                'calculated_fields': {},
                'impact_assessment': 'none'
            }
        
        total_records = len(df)
        records_with_gaps = 0
        unavailable_counts = {}
        calculated_counts = {}
        impact_levels = {'low': 0, 'medium': 0, 'high': 0}
        
        for gap_json in df['_data_gaps']:
            try:
                gap_data = json.loads(gap_json)
                if gap_data.get('unavailable_fields') or gap_data.get('calculated_fields'):
                    records_with_gaps += 1
                for field in gap_data.get('unavailable_fields', []):
                    unavailable_counts[field] = unavailable_counts.get(field, 0) + 1
                for field in gap_data.get('calculated_fields', []):
                    calculated_counts[field] = calculated_counts.get(field, 0) + 1
                impact = gap_data.get('impact', 'low')
                impact_levels[impact] = impact_levels.get(impact, 0) + 1
            except json.JSONDecodeError:
                continue
        
        if impact_levels['high'] > 0:
            overall_impact = 'high'
        elif impact_levels['medium'] > 0:
            overall_impact = 'medium'
        elif impact_levels['low'] > 0:
            overall_impact = 'low'
        else:
            overall_impact = 'none'
        
        return {
            'total_records': total_records,
            'records_with_gaps': records_with_gaps,
            'unavailable_fields': unavailable_counts,
            'calculated_fields': calculated_counts,
            'impact_assessment': overall_impact
        }


    
    # Max's methods
    def transform(self, df, config: Dict[str, Any]):
        """Aplica filling automático de gaps con configuración."""
        if not PYSPARK_AVAILABLE:
            raise ImportError("PySpark is required for transform() method")
        
        gap_config = config.get('data_gap_handling', {})
        
        default_values = gap_config.get('default_values', {})
        if default_values:
            df = self._fill_missing_values(df, default_values)
        
        critical_columns = gap_config.get('critical_columns', [])
        if critical_columns:
            df = self._mark_critical_gaps(df, critical_columns)
        
        if gap_config.get('filter_incomplete', False):
            df = self._filter_incomplete_records(df)
        
        return df
    
    def _fill_missing_values(self, df, default_values: Dict[str, Any]):
        """Llena valores faltantes con defaults configurados."""
        if not PYSPARK_AVAILABLE:
            raise ImportError("PySpark is required for this method")
        
        for column, default_value in default_values.items():
            if column in df.columns:
                df = df.withColumn(column, coalesce(col(column), lit(default_value)))
        return df
    
    def _mark_critical_gaps(self, df, critical_columns: List[str]):
        """Marca registros con gaps en columnas críticas."""
        if not PYSPARK_AVAILABLE:
            raise ImportError("PySpark is required for this method")
        
        has_gap_condition = None
        for column in critical_columns:
            if column in df.columns:
                if has_gap_condition is None:
                    has_gap_condition = col(column).isNull()
                else:
                    has_gap_condition = has_gap_condition | col(column).isNull()
        
        if has_gap_condition is not None:
            df = df.withColumn('has_critical_gaps', has_gap_condition)
        else:
            df = df.withColumn('has_critical_gaps', lit(False))
        return df
    
    def _filter_incomplete_records(self, df):
        """Filtra registros con gaps críticos."""
        if not PYSPARK_AVAILABLE:
            raise ImportError("PySpark is required for this method")
        
        if 'has_critical_gaps' in df.columns:
            df = df.filter(col('has_critical_gaps') == False)
        return df
