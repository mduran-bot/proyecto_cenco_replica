"""
Módulo de conversión de tipos de datos de MySQL a Redshift.

Este módulo implementa las conversiones necesarias para transformar datos desde
el formato MySQL de Janis al formato compatible con Redshift de Cencosud.

Conversiones soportadas:
- BIGINT Unix timestamp → TIMESTAMP ISO 8601
- TINYINT(1) → BOOLEAN
- VARCHAR(n) → VARCHAR(min(n, 65535))
- DECIMAL(p,s) → NUMERIC(p,s)
- JSON → VARCHAR(65535)
- TEXT → VARCHAR(65535)
- DATETIME → TIMESTAMP 'YYYY-MM-DD HH:MM:SS'
"""

from datetime import datetime, timezone
from typing import Any, Optional, Union
import json
import pandas as pd
import numpy as np


class DataTypeConverter:
    """Conversor de tipos de datos MySQL a Redshift."""
    
    # Límite máximo de VARCHAR en Redshift
    MAX_VARCHAR_LENGTH = 65535
    
    @staticmethod
    def convert_bigint_to_timestamp(value: Optional[Union[int, float]]) -> Optional[str]:
        """
        Convierte BIGINT Unix timestamp a TIMESTAMP ISO 8601.
        
        Args:
            value: Unix timestamp en segundos (puede ser None)
            
        Returns:
            String en formato ISO 8601 o None si el valor es None/NaN
            
        Raises:
            ValueError: Si el timestamp está fuera de rango válido
            
        Examples:
            >>> DataTypeConverter.convert_bigint_to_timestamp(1609459200)
            '2021-01-01T00:00:00+00:00'
            >>> DataTypeConverter.convert_bigint_to_timestamp(None)
            None
        """
        if pd.isna(value) or value is None:
            return None
            
        try:
            # Validar rango razonable (1970-2100)
            if value < 0 or value > 4102444800:
                raise ValueError(f"Timestamp fuera de rango válido: {value}")
                
            # Convertir a datetime UTC
            dt = datetime.fromtimestamp(value, tz=timezone.utc)
            return dt.isoformat()
            
        except (ValueError, OSError, OverflowError) as e:
            raise ValueError(f"Error convirtiendo timestamp {value}: {str(e)}")
    
    @staticmethod
    def convert_tinyint_to_boolean(value: Optional[Union[int, bool]]) -> Optional[bool]:
        """
        Convierte TINYINT(1) a BOOLEAN.
        
        Args:
            value: Valor TINYINT (0, 1, o None)
            
        Returns:
            Boolean (True/False) o None si el valor es None/NaN
            
        Examples:
            >>> DataTypeConverter.convert_tinyint_to_boolean(1)
            True
            >>> DataTypeConverter.convert_tinyint_to_boolean(0)
            False
            >>> DataTypeConverter.convert_tinyint_to_boolean(None)
            None
        """
        if pd.isna(value) or value is None:
            return None
            
        return bool(value)
    
    @staticmethod
    def convert_varchar(value: Optional[str], max_length: int = MAX_VARCHAR_LENGTH) -> Optional[str]:
        """
        Convierte VARCHAR(n) a VARCHAR con límite máximo de Redshift.
        
        Args:
            value: String a convertir
            max_length: Longitud máxima deseada (default: 65535)
            
        Returns:
            String truncado si excede max_length, o None si el valor es None/NaN
            
        Examples:
            >>> DataTypeConverter.convert_varchar("test", 10)
            'test'
            >>> DataTypeConverter.convert_varchar("a" * 100, 10)
            'aaaaaaaaaa'
        """
        if pd.isna(value) or value is None:
            return None
            
        # Asegurar que es string
        str_value = str(value)
        
        # Aplicar límite máximo
        effective_max = min(max_length, DataTypeConverter.MAX_VARCHAR_LENGTH)
        
        if len(str_value) > effective_max:
            return str_value[:effective_max]
            
        return str_value
    
    @staticmethod
    def convert_decimal(value: Optional[Union[int, float]], 
                       precision: int = 15, 
                       scale: int = 5) -> Optional[float]:
        """
        Convierte DECIMAL(p,s) a NUMERIC(p,s) validando precisión y escala.
        
        Args:
            value: Valor numérico
            precision: Número total de dígitos
            scale: Número de dígitos decimales
            
        Returns:
            Float redondeado a la escala especificada, o None si el valor es None/NaN
            
        Raises:
            ValueError: Si el valor excede la precisión especificada
            
        Examples:
            >>> DataTypeConverter.convert_decimal(123.456789, 10, 2)
            123.46
            >>> DataTypeConverter.convert_decimal(None)
            None
        """
        if pd.isna(value) or value is None:
            return None
            
        try:
            # Redondear a la escala especificada
            rounded_value = round(float(value), scale)
            
            # Validar que no excede la precisión
            # Contar dígitos totales (antes y después del punto decimal)
            str_value = str(abs(rounded_value)).replace('.', '')
            if len(str_value) > precision:
                raise ValueError(
                    f"Valor {value} excede precisión {precision} (tiene {len(str_value)} dígitos)"
                )
                
            return rounded_value
            
        except (ValueError, TypeError) as e:
            raise ValueError(f"Error convirtiendo decimal {value}: {str(e)}")
    
    @staticmethod
    def convert_json_to_varchar(value: Optional[Union[dict, list, str]]) -> Optional[str]:
        """
        Convierte campo JSON a VARCHAR(65535) con validación.
        
        Args:
            value: Objeto JSON (dict, list) o string JSON
            
        Returns:
            String JSON serializado, o None si el valor es None/NaN
            
        Raises:
            ValueError: Si el JSON no es válido
            
        Examples:
            >>> DataTypeConverter.convert_json_to_varchar({"key": "value"})
            '{"key": "value"}'
            >>> DataTypeConverter.convert_json_to_varchar('{"key": "value"}')
            '{"key": "value"}'
        """
        if pd.isna(value) or value is None:
            return None
            
        try:
            # Si ya es string, validar que sea JSON válido
            if isinstance(value, str):
                json.loads(value)  # Validar
                json_str = value
            else:
                # Serializar objeto a JSON
                json_str = json.dumps(value, ensure_ascii=False)
            
            # Aplicar límite de VARCHAR
            return DataTypeConverter.convert_varchar(json_str, DataTypeConverter.MAX_VARCHAR_LENGTH)
            
        except (json.JSONDecodeError, TypeError) as e:
            raise ValueError(f"Error convirtiendo JSON {value}: {str(e)}")
    
    @staticmethod
    def convert_text_to_varchar(value: Optional[str]) -> Optional[str]:
        """
        Convierte TEXT a VARCHAR(65535).
        
        Args:
            value: Texto a convertir
            
        Returns:
            String truncado a 65535 caracteres, o None si el valor es None/NaN
            
        Examples:
            >>> DataTypeConverter.convert_text_to_varchar("Long text...")
            'Long text...'
        """
        return DataTypeConverter.convert_varchar(value, DataTypeConverter.MAX_VARCHAR_LENGTH)
    
    @staticmethod
    def convert_datetime_to_timestamp(value: Optional[Union[str, datetime]]) -> Optional[str]:
        """
        Convierte DATETIME a TIMESTAMP en formato 'YYYY-MM-DD HH:MM:SS'.
        
        Args:
            value: String datetime o objeto datetime
            
        Returns:
            String en formato 'YYYY-MM-DD HH:MM:SS', o None si el valor es None/NaN
            
        Raises:
            ValueError: Si el formato datetime no es válido
            
        Examples:
            >>> DataTypeConverter.convert_datetime_to_timestamp("2021-01-01 12:30:45")
            '2021-01-01 12:30:45'
            >>> DataTypeConverter.convert_datetime_to_timestamp(datetime(2021, 1, 1, 12, 30, 45))
            '2021-01-01 12:30:45'
        """
        if pd.isna(value) or value is None:
            return None
            
        try:
            # Si es string, parsear a datetime
            if isinstance(value, str):
                dt = pd.to_datetime(value)
            elif isinstance(value, datetime):
                dt = value
            else:
                raise ValueError(f"Tipo no soportado: {type(value)}")
            
            # Formatear como 'YYYY-MM-DD HH:MM:SS'
            return dt.strftime('%Y-%m-%d %H:%M:%S')
            
        except (ValueError, TypeError) as e:
            raise ValueError(f"Error convirtiendo datetime {value}: {str(e)}")
    
    @staticmethod
    def apply_conversions_to_dataframe(df: pd.DataFrame, 
                                      conversion_rules: dict) -> pd.DataFrame:
        """
        Aplica conversiones de tipos de datos a un DataFrame completo.
        
        Args:
            df: DataFrame con datos originales
            conversion_rules: Diccionario con reglas de conversión por columna
                             Formato: {
                                 'column_name': {
                                     'type': 'bigint_to_timestamp' | 'tinyint_to_boolean' | ...,
                                     'params': {...}  # Parámetros opcionales
                                 }
                             }
        
        Returns:
            DataFrame con conversiones aplicadas
            
        Examples:
            >>> rules = {
            ...     'date_created': {'type': 'bigint_to_timestamp'},
            ...     'status': {'type': 'tinyint_to_boolean'}
            ... }
            >>> df_converted = DataTypeConverter.apply_conversions_to_dataframe(df, rules)
        """
        df_converted = df.copy()
        
        conversion_methods = {
            'bigint_to_timestamp': DataTypeConverter.convert_bigint_to_timestamp,
            'tinyint_to_boolean': DataTypeConverter.convert_tinyint_to_boolean,
            'varchar': DataTypeConverter.convert_varchar,
            'decimal': DataTypeConverter.convert_decimal,
            'json_to_varchar': DataTypeConverter.convert_json_to_varchar,
            'text_to_varchar': DataTypeConverter.convert_text_to_varchar,
            'datetime_to_timestamp': DataTypeConverter.convert_datetime_to_timestamp,
        }
        
        for column, rule in conversion_rules.items():
            if column not in df_converted.columns:
                continue
                
            conversion_type = rule.get('type')
            params = rule.get('params', {})
            
            if conversion_type not in conversion_methods:
                raise ValueError(f"Tipo de conversión no soportado: {conversion_type}")
            
            method = conversion_methods[conversion_type]
            
            # Aplicar conversión a la columna
            try:
                if params:
                    df_converted[column] = df_converted[column].apply(
                        lambda x: method(x, **params)
                    )
                else:
                    df_converted[column] = df_converted[column].apply(method)
            except Exception as e:
                raise ValueError(f"Error aplicando conversión a columna {column}: {str(e)}")
        
        return df_converted


# Reglas de conversión predefinidas para tablas comunes
CONVERSION_RULES = {
    'wms_orders': {
        'invoice_date': {'type': 'bigint_to_timestamp'},
        'date_created': {'type': 'bigint_to_timestamp'},
        'date_picked': {'type': 'bigint_to_timestamp'},
        'apply_quotation': {'type': 'tinyint_to_boolean'},
    },
    'wms_order_items': {
        'list_price': {'type': 'decimal', 'params': {'precision': 12, 'scale': 2}},
        'price': {'type': 'decimal', 'params': {'precision': 12, 'scale': 2}},
        'selling_price': {'type': 'decimal', 'params': {'precision': 15, 'scale': 5}},
    },
    'wms_stores': {
        'date_created': {'type': 'bigint_to_timestamp'},
        'date_modified': {'type': 'bigint_to_timestamp'},
        'apply_quotation': {'type': 'tinyint_to_boolean'},
        'lat': {'type': 'decimal', 'params': {'precision': 12, 'scale': 9}},
        'lng': {'type': 'decimal', 'params': {'precision': 12, 'scale': 9}},
    },
    'admins': {
        'firstname': {'type': 'varchar', 'params': {'max_length': 255}},
        'lastname': {'type': 'varchar', 'params': {'max_length': 255}},
        'email': {'type': 'varchar', 'params': {'max_length': 255}},
    },
}
