"""
Tests unitarios para el módulo data_type_converter.
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timezone
import sys
import os

# Agregar el directorio raíz al path para imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from glue.modules.data_type_converter import DataTypeConverter, CONVERSION_RULES


class TestBigintToTimestamp:
    """Tests para conversión de BIGINT a TIMESTAMP."""
    
    def test_valid_timestamp(self):
        """Test con timestamp válido."""
        result = DataTypeConverter.convert_bigint_to_timestamp(1609459200)
        assert result == '2021-01-01T00:00:00+00:00'
    
    def test_null_value(self):
        """Test con valor NULL."""
        assert DataTypeConverter.convert_bigint_to_timestamp(None) is None
        assert DataTypeConverter.convert_bigint_to_timestamp(np.nan) is None
    
    def test_invalid_timestamp_negative(self):
        """Test con timestamp negativo."""
        with pytest.raises(ValueError, match="fuera de rango"):
            DataTypeConverter.convert_bigint_to_timestamp(-1)
    
    def test_invalid_timestamp_future(self):
        """Test con timestamp muy futuro."""
        with pytest.raises(ValueError, match="fuera de rango"):
            DataTypeConverter.convert_bigint_to_timestamp(5000000000)
    
    def test_recent_timestamp(self):
        """Test con timestamp reciente."""
        # 2024-01-01
        result = DataTypeConverter.convert_bigint_to_timestamp(1704067200)
        assert '2024-01-01' in result


class TestTinyintToBoolean:
    """Tests para conversión de TINYINT a BOOLEAN."""
    
    def test_one_to_true(self):
        """Test conversión 1 -> True."""
        assert DataTypeConverter.convert_tinyint_to_boolean(1) is True
    
    def test_zero_to_false(self):
        """Test conversión 0 -> False."""
        assert DataTypeConverter.convert_tinyint_to_boolean(0) is False
    
    def test_null_value(self):
        """Test con valor NULL."""
        assert DataTypeConverter.convert_tinyint_to_boolean(None) is None
        assert DataTypeConverter.convert_tinyint_to_boolean(np.nan) is None
    
    def test_other_numbers(self):
        """Test con otros números."""
        assert DataTypeConverter.convert_tinyint_to_boolean(2) is True
        assert DataTypeConverter.convert_tinyint_to_boolean(-1) is True


class TestVarcharConversion:
    """Tests para conversión de VARCHAR."""
    
    def test_normal_string(self):
        """Test con string normal."""
        result = DataTypeConverter.convert_varchar("test string", 100)
        assert result == "test string"
    
    def test_truncation(self):
        """Test truncamiento de string largo."""
        long_string = "a" * 100
        result = DataTypeConverter.convert_varchar(long_string, 10)
        assert result == "aaaaaaaaaa"
        assert len(result) == 10
    
    def test_max_length_limit(self):
        """Test límite máximo de Redshift."""
        long_string = "a" * 70000
        result = DataTypeConverter.convert_varchar(long_string)
        assert len(result) == 65535
    
    def test_null_value(self):
        """Test con valor NULL."""
        assert DataTypeConverter.convert_varchar(None) is None
        assert DataTypeConverter.convert_varchar(np.nan) is None


class TestDecimalConversion:
    """Tests para conversión de DECIMAL."""
    
    def test_normal_decimal(self):
        """Test con decimal normal."""
        result = DataTypeConverter.convert_decimal(123.456789, 10, 2)
        assert result == 123.46
    
    def test_rounding(self):
        """Test redondeo."""
        result = DataTypeConverter.convert_decimal(123.455, 10, 2)
        assert result == 123.46  # Redondeo hacia arriba
    
    def test_null_value(self):
        """Test con valor NULL."""
        assert DataTypeConverter.convert_decimal(None) is None
        assert DataTypeConverter.convert_decimal(np.nan) is None
    
    def test_precision_exceeded(self):
        """Test cuando se excede la precisión."""
        with pytest.raises(ValueError, match="excede precisión"):
            DataTypeConverter.convert_decimal(12345678901, 10, 2)
    
    def test_integer_value(self):
        """Test con valor entero."""
        result = DataTypeConverter.convert_decimal(100, 10, 2)
        assert result == 100.0


class TestJsonToVarchar:
    """Tests para conversión de JSON a VARCHAR."""
    
    def test_dict_to_json(self):
        """Test conversión de dict a JSON."""
        data = {"key": "value", "number": 123}
        result = DataTypeConverter.convert_json_to_varchar(data)
        assert '"key"' in result
        assert '"value"' in result
    
    def test_list_to_json(self):
        """Test conversión de list a JSON."""
        data = [1, 2, 3, "test"]
        result = DataTypeConverter.convert_json_to_varchar(data)
        assert result == '[1, 2, 3, "test"]'
    
    def test_json_string(self):
        """Test con string JSON válido."""
        json_str = '{"key": "value"}'
        result = DataTypeConverter.convert_json_to_varchar(json_str)
        assert result == json_str
    
    def test_invalid_json_string(self):
        """Test con string JSON inválido."""
        with pytest.raises(ValueError, match="Error convirtiendo JSON"):
            DataTypeConverter.convert_json_to_varchar("{invalid json}")
    
    def test_null_value(self):
        """Test con valor NULL."""
        assert DataTypeConverter.convert_json_to_varchar(None) is None


class TestDatetimeToTimestamp:
    """Tests para conversión de DATETIME a TIMESTAMP."""
    
    def test_string_datetime(self):
        """Test con string datetime."""
        result = DataTypeConverter.convert_datetime_to_timestamp("2021-01-01 12:30:45")
        assert result == "2021-01-01 12:30:45"
    
    def test_datetime_object(self):
        """Test con objeto datetime."""
        dt = datetime(2021, 1, 1, 12, 30, 45)
        result = DataTypeConverter.convert_datetime_to_timestamp(dt)
        assert result == "2021-01-01 12:30:45"
    
    def test_null_value(self):
        """Test con valor NULL."""
        assert DataTypeConverter.convert_datetime_to_timestamp(None) is None
    
    def test_invalid_format(self):
        """Test con formato inválido."""
        with pytest.raises(ValueError):
            DataTypeConverter.convert_datetime_to_timestamp("invalid date")


class TestDataFrameConversions:
    """Tests para aplicación de conversiones a DataFrames."""
    
    def test_apply_conversions(self):
        """Test aplicación de múltiples conversiones."""
        df = pd.DataFrame({
            'id': [1, 2, 3],
            'date_created': [1609459200, 1609545600, 1609632000],
            'is_active': [1, 0, 1],
            'price': [123.456, 789.012, 456.789]
        })
        
        rules = {
            'date_created': {'type': 'bigint_to_timestamp'},
            'is_active': {'type': 'tinyint_to_boolean'},
            'price': {'type': 'decimal', 'params': {'precision': 10, 'scale': 2}}
        }
        
        result = DataTypeConverter.apply_conversions_to_dataframe(df, rules)
        
        # Verificar conversiones
        assert '2021-01-01' in result['date_created'].iloc[0]
        assert result['is_active'].iloc[0] is True
        assert result['is_active'].iloc[1] is False
        assert result['price'].iloc[0] == 123.46
    
    def test_missing_column(self):
        """Test con columna faltante en reglas."""
        df = pd.DataFrame({'id': [1, 2]})
        rules = {'nonexistent': {'type': 'bigint_to_timestamp'}}
        
        # No debe fallar, solo ignorar la columna
        result = DataTypeConverter.apply_conversions_to_dataframe(df, rules)
        assert len(result) == 2
    
    def test_invalid_conversion_type(self):
        """Test con tipo de conversión inválido."""
        df = pd.DataFrame({'id': [1, 2]})
        rules = {'id': {'type': 'invalid_type'}}
        
        with pytest.raises(ValueError, match="no soportado"):
            DataTypeConverter.apply_conversions_to_dataframe(df, rules)


class TestPredefinedRules:
    """Tests para reglas de conversión predefinidas."""
    
    def test_wms_orders_rules_exist(self):
        """Test que existen reglas para wms_orders."""
        assert 'wms_orders' in CONVERSION_RULES
        assert 'date_created' in CONVERSION_RULES['wms_orders']
    
    def test_wms_order_items_rules_exist(self):
        """Test que existen reglas para wms_order_items."""
        assert 'wms_order_items' in CONVERSION_RULES
        assert 'price' in CONVERSION_RULES['wms_order_items']


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
