"""
Módulo de normalización de datos.

Este módulo implementa funciones de normalización para estandarizar formatos
de datos antes de cargarlos a Redshift.

Normalizaciones soportadas:
- Timestamps a UTC timezone
- Validación y limpieza de emails
- Normalización de números telefónicos
- Limpieza de whitespace en strings
"""

from datetime import datetime, timezone
from typing import Optional
import re
import pandas as pd


class DataNormalizer:
    """Normalizador de datos para estandarización de formatos."""
    
    # Regex para validación de email (RFC 5322 simplificado)
    EMAIL_REGEX = re.compile(
        r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    )
    
    # Regex para extracción de dígitos de teléfono
    PHONE_REGEX = re.compile(r'\d+')
    
    @staticmethod
    def normalize_timestamp_to_utc(value: Optional[str]) -> Optional[str]:
        """
        Normaliza timestamp a UTC timezone.
        
        Args:
            value: Timestamp en formato ISO 8601 (puede tener timezone o no)
            
        Returns:
            Timestamp en UTC con formato ISO 8601, o None si el valor es None/NaN
            
        Examples:
            >>> DataNormalizer.normalize_timestamp_to_utc("2021-01-01T12:00:00-05:00")
            '2021-01-01T17:00:00+00:00'
            >>> DataNormalizer.normalize_timestamp_to_utc("2021-01-01T12:00:00")
            '2021-01-01T12:00:00+00:00'
        """
        if pd.isna(value) or value is None:
            return None
            
        try:
            # Parsear timestamp
            dt = pd.to_datetime(value)
            
            # Si no tiene timezone, asumir UTC
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            else:
                # Convertir a UTC
                dt = dt.astimezone(timezone.utc)
            
            return dt.isoformat()
            
        except (ValueError, TypeError) as e:
            raise ValueError(f"Error normalizando timestamp {value}: {str(e)}")
    
    @staticmethod
    def validate_and_clean_email(value: Optional[str]) -> Optional[str]:
        """
        Valida y limpia dirección de email.
        
        Args:
            value: Email a validar y limpiar
            
        Returns:
            Email limpio y en minúsculas, o None si es inválido o None/NaN
            
        Examples:
            >>> DataNormalizer.validate_and_clean_email("  USER@EXAMPLE.COM  ")
            'user@example.com'
            >>> DataNormalizer.validate_and_clean_email("invalid-email")
            None
        """
        if pd.isna(value) or value is None:
            return None
            
        # Limpiar whitespace y convertir a minúsculas
        cleaned = str(value).strip().lower()
        
        # Validar formato
        if not DataNormalizer.EMAIL_REGEX.match(cleaned):
            return None
            
        return cleaned
    
    @staticmethod
    def normalize_phone_number(value: Optional[str], 
                               country_code: str = '51') -> Optional[str]:
        """
        Normaliza número telefónico a formato estándar.
        
        Args:
            value: Número telefónico en cualquier formato
            country_code: Código de país (default: '51' para Perú)
            
        Returns:
            Número en formato +{country_code}{digits}, o None si es inválido o None/NaN
            
        Examples:
            >>> DataNormalizer.normalize_phone_number("(01) 234-5678")
            '+51012345678'
            >>> DataNormalizer.normalize_phone_number("987654321")
            '+51987654321'
            >>> DataNormalizer.normalize_phone_number("+51 987 654 321")
            '+51987654321'
        """
        if pd.isna(value) or value is None:
            return None
            
        # Extraer solo dígitos
        digits = ''.join(DataNormalizer.PHONE_REGEX.findall(str(value)))
        
        if not digits:
            return None
        
        # Si ya tiene código de país, no agregarlo de nuevo
        if digits.startswith(country_code):
            return f'+{digits}'
        
        # Agregar código de país
        return f'+{country_code}{digits}'
    
    @staticmethod
    def trim_whitespace(value: Optional[str]) -> Optional[str]:
        """
        Elimina whitespace al inicio y final de strings.
        
        Args:
            value: String a limpiar
            
        Returns:
            String sin whitespace al inicio/final, o None si el valor es None/NaN
            
        Examples:
            >>> DataNormalizer.trim_whitespace("  hello world  ")
            'hello world'
            >>> DataNormalizer.trim_whitespace(None)
            None
        """
        if pd.isna(value) or value is None:
            return None
            
        return str(value).strip()
    
    @staticmethod
    def normalize_string_case(value: Optional[str], 
                             case: str = 'lower') -> Optional[str]:
        """
        Normaliza el case de un string.
        
        Args:
            value: String a normalizar
            case: Tipo de case ('lower', 'upper', 'title')
            
        Returns:
            String normalizado, o None si el valor es None/NaN
            
        Examples:
            >>> DataNormalizer.normalize_string_case("Hello World", 'lower')
            'hello world'
            >>> DataNormalizer.normalize_string_case("hello world", 'title')
            'Hello World'
        """
        if pd.isna(value) or value is None:
            return None
            
        str_value = str(value)
        
        if case == 'lower':
            return str_value.lower()
        elif case == 'upper':
            return str_value.upper()
        elif case == 'title':
            return str_value.title()
        else:
            raise ValueError(f"Case no soportado: {case}")
    
    @staticmethod
    def remove_extra_spaces(value: Optional[str]) -> Optional[str]:
        """
        Elimina espacios múltiples dentro de un string.
        
        Args:
            value: String a limpiar
            
        Returns:
            String con espacios normalizados, o None si el valor es None/NaN
            
        Examples:
            >>> DataNormalizer.remove_extra_spaces("hello    world")
            'hello world'
            >>> DataNormalizer.remove_extra_spaces("  multiple   spaces  ")
            'multiple spaces'
        """
        if pd.isna(value) or value is None:
            return None
            
        # Eliminar espacios múltiples y trim
        return ' '.join(str(value).split())
    
    @staticmethod
    def apply_normalizations_to_dataframe(df: pd.DataFrame, 
                                         normalization_rules: dict) -> pd.DataFrame:
        """
        Aplica normalizaciones a un DataFrame completo.
        
        Args:
            df: DataFrame con datos originales
            normalization_rules: Diccionario con reglas de normalización por columna
                                Formato: {
                                    'column_name': {
                                        'type': 'timestamp_to_utc' | 'email' | 'phone' | ...,
                                        'params': {...}  # Parámetros opcionales
                                    }
                                }
        
        Returns:
            DataFrame con normalizaciones aplicadas
            
        Examples:
            >>> rules = {
            ...     'email': {'type': 'email'},
            ...     'phone': {'type': 'phone', 'params': {'country_code': '51'}},
            ...     'name': {'type': 'trim'}
            ... }
            >>> df_normalized = DataNormalizer.apply_normalizations_to_dataframe(df, rules)
        """
        df_normalized = df.copy()
        
        normalization_methods = {
            'timestamp_to_utc': DataNormalizer.normalize_timestamp_to_utc,
            'email': DataNormalizer.validate_and_clean_email,
            'phone': DataNormalizer.normalize_phone_number,
            'trim': DataNormalizer.trim_whitespace,
            'case': DataNormalizer.normalize_string_case,
            'remove_extra_spaces': DataNormalizer.remove_extra_spaces,
        }
        
        for column, rule in normalization_rules.items():
            if column not in df_normalized.columns:
                continue
                
            normalization_type = rule.get('type')
            params = rule.get('params', {})
            
            if normalization_type not in normalization_methods:
                raise ValueError(f"Tipo de normalización no soportado: {normalization_type}")
            
            method = normalization_methods[normalization_type]
            
            # Aplicar normalización a la columna
            try:
                if params:
                    df_normalized[column] = df_normalized[column].apply(
                        lambda x: method(x, **params)
                    )
                else:
                    df_normalized[column] = df_normalized[column].apply(method)
            except Exception as e:
                raise ValueError(f"Error aplicando normalización a columna {column}: {str(e)}")
        
        return df_normalized


# Reglas de normalización predefinidas para tablas comunes
NORMALIZATION_RULES = {
    'admins': {
        'email': {'type': 'email'},
        'firstname': {'type': 'trim'},
        'lastname': {'type': 'trim'},
        'username': {'type': 'trim'},
    },
    'customers': {
        'email': {'type': 'email'},
        'phone': {'type': 'phone', 'params': {'country_code': '51'}},
        'firstname': {'type': 'trim'},
        'lastname': {'type': 'trim'},
    },
    'wms_stores': {
        'phone': {'type': 'phone', 'params': {'country_code': '51'}},
        'street_name': {'type': 'trim'},
        'city': {'type': 'trim'},
        'state': {'type': 'trim'},
        'neighborhood': {'type': 'trim'},
    },
}
