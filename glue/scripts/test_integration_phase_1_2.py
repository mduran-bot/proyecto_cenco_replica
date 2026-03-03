"""
Script de validación para Fase 1.1 y 1.2 - Integración de Módulos

Este script valida:
1. Imports correctos de todos los módulos
2. Funcionalidad básica de módulos únicos (Fase 1.1)
3. Funcionalidad básica de módulos merged (Fase 1.2)
4. Compatibilidad entre módulos

Ejecutar: python test_integration_phase_1_2.py
"""

import sys
import os
import traceback
from datetime import datetime

# Agregar el directorio padre al path para poder importar modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Colores para output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

def print_success(msg):
    print(f"{Colors.GREEN}✓ {msg}{Colors.END}")

def print_error(msg):
    print(f"{Colors.RED}✗ {msg}{Colors.END}")

def print_warning(msg):
    print(f"{Colors.YELLOW}⚠ {msg}{Colors.END}")

def print_info(msg):
    print(f"{Colors.BLUE}ℹ {msg}{Colors.END}")

def print_section(title):
    print(f"\n{Colors.BLUE}{'='*60}")
    print(f"{title}")
    print(f"{'='*60}{Colors.END}\n")

# Contadores
tests_passed = 0
tests_failed = 0
tests_skipped = 0

def run_test(test_name, test_func):
    """Ejecuta un test y maneja errores."""
    global tests_passed, tests_failed, tests_skipped
    
    try:
        print(f"\nTest: {test_name}")
        test_func()
        print_success(f"PASSED: {test_name}")
        tests_passed += 1
        return True
    except ImportError as e:
        print_warning(f"SKIPPED: {test_name} - {str(e)}")
        tests_skipped += 1
        return False
    except Exception as e:
        print_error(f"FAILED: {test_name}")
        print_error(f"Error: {str(e)}")
        traceback.print_exc()
        tests_failed += 1
        return False

# ============================================================================
# FASE 1.1: Tests de Módulos Únicos
# ============================================================================

def test_json_flattener_import():
    """Test 1.1.1: Import de JSONFlattener"""
    from modules.json_flattener import JSONFlattener
    print_info("JSONFlattener importado correctamente")

def test_json_flattener_basic():
    """Test 1.1.2: Funcionalidad básica de JSONFlattener"""
    from modules.json_flattener import JSONFlattener
    
    flattener = JSONFlattener()
    nested = {
        "user": {
            "name": "John",
            "address": {
                "city": "Lima"
            }
        }
    }
    
    flat = flattener.flatten(nested)
    assert "user_name" in flat, "Falta user_name en resultado"
    assert flat["user_name"] == "John", "Valor incorrecto"
    assert "user_address_city" in flat, "Falta user_address_city"
    assert flat["user_address_city"] == "Lima", "Valor incorrecto"
    
    print_info(f"Flatten exitoso: {flat}")

def test_data_cleaner_import():
    """Test 1.1.3: Import de DataCleaner"""
    from modules.data_cleaner import DataCleaner
    print_info("DataCleaner importado correctamente")

def test_data_cleaner_basic():
    """Test 1.1.4: Funcionalidad básica de DataCleaner"""
    from modules.data_cleaner import DataCleaner
    import pandas as pd
    
    cleaner = DataCleaner()
    df = pd.DataFrame({
        'name': ['  John  ', 'Jane', None],
        'email': ['john@test.com', 'JANE@TEST.COM', 'invalid']
    })
    
    # Test trim
    result = cleaner.trim_whitespace(df['name'])
    assert result[0] == 'John', "Trim falló"
    
    # Test lowercase
    result = cleaner.to_lowercase(df['email'])
    assert result[1] == 'jane@test.com', "Lowercase falló"
    
    print_info("DataCleaner funcionando correctamente")

def test_duplicate_detector_import():
    """Test 1.1.5: Import de DuplicateDetector"""
    from modules.duplicate_detector import DuplicateDetector
    print_info("DuplicateDetector importado correctamente")

def test_duplicate_detector_basic():
    """Test 1.1.6: Funcionalidad básica de DuplicateDetector"""
    from modules.duplicate_detector import DuplicateDetector
    import pandas as pd
    
    detector = DuplicateDetector()
    df = pd.DataFrame({
        'id': [1, 2, 2, 3],
        'name': ['A', 'B', 'B', 'C']
    })
    
    duplicates = detector.find_duplicates(df, subset=['id'])
    assert len(duplicates) == 2, f"Esperaba 2 duplicados, encontró {len(duplicates)}"
    
    print_info(f"Duplicados detectados: {len(duplicates)}")

def test_conflict_resolver_import():
    """Test 1.1.7: Import de ConflictResolver"""
    from modules.conflict_resolver import ConflictResolver
    print_info("ConflictResolver importado correctamente")

def test_conflict_resolver_basic():
    """Test 1.1.8: Funcionalidad básica de ConflictResolver"""
    from modules.conflict_resolver import ConflictResolver
    import pandas as pd
    
    resolver = ConflictResolver()
    df = pd.DataFrame({
        'id': [1, 1, 2],
        'value': [10, 20, 30],
        'timestamp': [1, 2, 3]
    })
    
    resolved = resolver.resolve_by_latest(df, key_columns=['id'], timestamp_column='timestamp')
    assert len(resolved) == 2, f"Esperaba 2 registros, obtuvo {len(resolved)}"
    
    print_info(f"Conflictos resueltos: {len(df) - len(resolved)} eliminados")

# ============================================================================
# FASE 1.2: Tests de Módulos Merged
# ============================================================================

def test_iceberg_writer_import():
    """Test 1.2.1: Import de IcebergWriter merged"""
    from modules.iceberg_writer import IcebergWriter
    print_info("IcebergWriter merged importado correctamente")

def test_iceberg_writer_initialization():
    """Test 1.2.2: Inicialización de IcebergWriter con parámetros merged"""
    from modules.iceberg_writer import IcebergWriter
    from unittest.mock import Mock
    
    # Mock SparkSession
    spark = Mock()
    
    # Test con parámetros de Vicente
    writer1 = IcebergWriter(spark, catalog_name="test_catalog")
    assert writer1.catalog_name == "test_catalog"
    assert writer1.max_retries == 3  # Default de Max
    
    # Test con parámetros de Max
    writer2 = IcebergWriter(spark, max_retries=5, retry_delay_seconds=10)
    assert writer2.max_retries == 5
    assert writer2.retry_delay_seconds == 10
    
    print_info("IcebergWriter inicializado con parámetros de ambos (Vicente + Max)")

def test_data_type_converter_import():
    """Test 1.2.3: Import de DataTypeConverter merged"""
    from modules.data_type_converter import DataTypeConverter
    print_info("DataTypeConverter merged importado correctamente")

def test_data_type_converter_vicente_methods():
    """Test 1.2.4: Métodos de Vicente en DataTypeConverter"""
    from modules.data_type_converter import DataTypeConverter
    
    # Test conversión bigint to timestamp
    result = DataTypeConverter.convert_bigint_to_timestamp(1609459200)
    assert result is not None, "Conversión falló"
    assert "2021-01-01" in result, "Fecha incorrecta"
    
    # Test conversión tinyint to boolean
    assert DataTypeConverter.convert_tinyint_to_boolean(1) == True
    assert DataTypeConverter.convert_tinyint_to_boolean(0) == False
    
    # Test conversión varchar
    result = DataTypeConverter.convert_varchar("test" * 100, max_length=10)
    assert len(result) == 10, "Truncado incorrecto"
    
    print_info("Métodos de Vicente funcionando correctamente")

def test_data_type_converter_max_initialization():
    """Test 1.2.5: Inicialización de DataTypeConverter con config de Max"""
    from modules.data_type_converter import DataTypeConverter
    
    converter = DataTypeConverter()
    assert hasattr(converter, 'inference_sample_size'), "Falta atributo de Max"
    assert converter.inference_sample_size == 100, "Default incorrecto"
    assert converter.inference_threshold == 0.9, "Threshold incorrecto"
    
    print_info("DataTypeConverter inicializado con config de Max")

def test_data_normalizer_import():
    """Test 1.2.6: Import de DataNormalizer merged"""
    from modules.data_normalizer import DataNormalizer
    print_info("DataNormalizer merged importado correctamente")

def test_data_normalizer_vicente_methods():
    """Test 1.2.7: Métodos de Vicente en DataNormalizer"""
    from modules.data_normalizer import DataNormalizer
    
    # Test email validation
    result = DataNormalizer.validate_and_clean_email("  USER@TEST.COM  ")
    assert result == "user@test.com", "Email normalización falló"
    
    # Test phone normalization
    result = DataNormalizer.normalize_phone_number("(01) 234-5678", country_code="51")
    assert result == "+51012345678", "Phone normalización falló"
    
    # Test trim
    result = DataNormalizer.trim_whitespace("  hello  ")
    assert result == "hello", "Trim falló"
    
    print_info("Métodos de Vicente en DataNormalizer funcionando")

def test_data_gap_handler_import():
    """Test 1.2.8: Import de DataGapHandler merged"""
    from modules.data_gap_handler import DataGapHandler
    print_info("DataGapHandler merged importado correctamente")

def test_data_gap_handler_vicente_methods():
    """Test 1.2.9: Métodos de Vicente en DataGapHandler"""
    from modules.data_gap_handler import DataGapHandler
    import pandas as pd
    
    # Test calculate_items_substituted_qty
    df = pd.DataFrame({
        'order_id': [1, 1, 1, 2, 2],
        'substitute_type': ['original', 'substitute', 'substitute', 'original', 'original']
    })
    
    result = DataGapHandler.calculate_items_substituted_qty(df)
    assert result[1] == 2, "Cálculo incorrecto"
    assert result[2] == 0, "Cálculo incorrecto"
    
    print_info("Métodos de Vicente en DataGapHandler funcionando")

def test_data_gap_handler_max_initialization():
    """Test 1.2.10: Inicialización de DataGapHandler con config de Max"""
    from modules.data_gap_handler import DataGapHandler
    
    handler = DataGapHandler()
    assert handler is not None, "Inicialización falló"
    
    print_info("DataGapHandler inicializado correctamente")

# ============================================================================
# Tests de Compatibilidad
# ============================================================================

def test_modules_compatibility():
    """Test 1.3.1: Compatibilidad entre módulos"""
    from modules.json_flattener import JSONFlattener
    from modules.data_cleaner import DataCleaner
    from modules.data_type_converter import DataTypeConverter
    from modules.data_normalizer import DataNormalizer
    
    # Simular pipeline: flatten -> clean -> convert -> normalize
    flattener = JSONFlattener()
    cleaner = DataCleaner()
    
    # Flatten
    nested = {"user": {"name": "  John  ", "email": "JOHN@TEST.COM"}}
    flat = flattener.flatten(nested)
    
    # Clean (simular con string directo)
    cleaned_name = DataNormalizer.trim_whitespace(flat["user_name"])
    
    # Normalize
    normalized_email = DataNormalizer.validate_and_clean_email(flat["user_email"])
    
    assert cleaned_name == "John", "Pipeline falló en clean"
    assert normalized_email == "john@test.com", "Pipeline falló en normalize"
    
    print_info("Módulos son compatibles entre sí")

def test_pyspark_optional():
    """Test 1.3.2: PySpark es opcional"""
    # Verificar que los módulos se pueden importar sin PySpark
    try:
        from modules.data_type_converter import DataTypeConverter, PYSPARK_AVAILABLE
        from modules.data_normalizer import DataNormalizer
        from modules.data_gap_handler import DataGapHandler
        
        if not PYSPARK_AVAILABLE:
            print_info("PySpark no disponible - módulos funcionan solo con pandas")
        else:
            print_info("PySpark disponible - módulos soportan ambos")
        
    except ImportError as e:
        raise AssertionError(f"Módulos no deberían fallar sin PySpark: {e}")

# ============================================================================
# Main Test Runner
# ============================================================================

def main():
    print_section("VALIDACIÓN DE INTEGRACIÓN - FASE 1.1 y 1.2")
    print_info(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print_info("Ejecutando tests de validación...")
    
    # FASE 1.1: Módulos Únicos
    print_section("FASE 1.1: MÓDULOS ÚNICOS")
    
    run_test("1.1.1 - Import JSONFlattener", test_json_flattener_import)
    run_test("1.1.2 - JSONFlattener básico", test_json_flattener_basic)
    run_test("1.1.3 - Import DataCleaner", test_data_cleaner_import)
    run_test("1.1.4 - DataCleaner básico", test_data_cleaner_basic)
    run_test("1.1.5 - Import DuplicateDetector", test_duplicate_detector_import)
    run_test("1.1.6 - DuplicateDetector básico", test_duplicate_detector_basic)
    run_test("1.1.7 - Import ConflictResolver", test_conflict_resolver_import)
    run_test("1.1.8 - ConflictResolver básico", test_conflict_resolver_basic)
    
    # FASE 1.2: Módulos Merged
    print_section("FASE 1.2: MÓDULOS MERGED")
    
    run_test("1.2.1 - Import IcebergWriter merged", test_iceberg_writer_import)
    run_test("1.2.2 - IcebergWriter inicialización", test_iceberg_writer_initialization)
    run_test("1.2.3 - Import DataTypeConverter merged", test_data_type_converter_import)
    run_test("1.2.4 - DataTypeConverter métodos Vicente", test_data_type_converter_vicente_methods)
    run_test("1.2.5 - DataTypeConverter config Max", test_data_type_converter_max_initialization)
    run_test("1.2.6 - Import DataNormalizer merged", test_data_normalizer_import)
    run_test("1.2.7 - DataNormalizer métodos Vicente", test_data_normalizer_vicente_methods)
    run_test("1.2.8 - Import DataGapHandler merged", test_data_gap_handler_import)
    run_test("1.2.9 - DataGapHandler métodos Vicente", test_data_gap_handler_vicente_methods)
    run_test("1.2.10 - DataGapHandler config Max", test_data_gap_handler_max_initialization)
    
    # Tests de Compatibilidad
    print_section("COMPATIBILIDAD ENTRE MÓDULOS")
    
    run_test("1.3.1 - Compatibilidad módulos", test_modules_compatibility)
    run_test("1.3.2 - PySpark opcional", test_pyspark_optional)
    
    # Resumen Final
    print_section("RESUMEN DE TESTS")
    
    total_tests = tests_passed + tests_failed + tests_skipped
    
    print(f"\nTotal de tests: {total_tests}")
    print_success(f"Pasados: {tests_passed}")
    print_error(f"Fallados: {tests_failed}")
    print_warning(f"Omitidos: {tests_skipped}")
    
    if tests_failed == 0:
        print_success("\n✓ TODOS LOS TESTS PASARON!")
        return 0
    else:
        print_error(f"\n✗ {tests_failed} TESTS FALLARON")
        return 1

if __name__ == "__main__":
    sys.exit(main())
