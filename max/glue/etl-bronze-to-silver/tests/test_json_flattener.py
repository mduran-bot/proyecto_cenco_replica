"""
Property-based tests for JSONFlattener module.

These tests validate the correctness properties defined in the design document
using hypothesis for property-based testing.
"""

import pytest
from hypothesis import given, strategies as st, settings
from pyspark.sql import SparkSession
from pyspark.sql.types import (
    StructType, StructField, StringType, IntegerType, 
    ArrayType, DoubleType, BooleanType
)
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from modules.json_flattener import JSONFlattener


@pytest.fixture(scope="module")
def spark():
    """Create a SparkSession for testing."""
    spark = SparkSession.builder \
        .appName("JSONFlattenerTests") \
        .master("local[2]") \
        .getOrCreate()
    yield spark
    spark.stop()


# Feature: etl-bronze-to-silver, Property 13: Aplanamiento de estructuras anidadas
@settings(max_examples=100)
@given(
    name=st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll'))),
    age=st.integers(min_value=0, max_value=120),
    city=st.text(min_size=1, max_size=30, alphabet=st.characters(whitelist_categories=('Lu', 'Ll'))),
    street=st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll')))
)
def test_property_13_flatten_nested_structures(spark, name, age, city, street):
    """
    Property 13: Aplanamiento de estructuras anidadas
    
    Para cualquier DataFrame con columnas de tipo StructType, después del aplanamiento,
    no debe haber columnas de tipo StructType en el DataFrame resultante.
    
    Valida: Requisito 4.1
    """
    # Create DataFrame with nested struct
    schema = StructType([
        StructField("id", IntegerType(), True),
        StructField("person", StructType([
            StructField("name", StringType(), True),
            StructField("age", IntegerType(), True)
        ]), True),
        StructField("address", StructType([
            StructField("city", StringType(), True),
            StructField("street", StringType(), True)
        ]), True)
    ])
    
    data = [(1, (name, age), (city, street))]
    df = spark.createDataFrame(data, schema)
    
    # Apply flattening
    flattener = JSONFlattener()
    result = flattener.transform(df, {})
    
    # Verify: No StructType columns remain
    for field in result.schema.fields:
        assert not isinstance(field.dataType, StructType), \
            f"Column {field.name} is still a StructType after flattening"
    
    # Verify: Flattened columns exist with dot notation
    column_names = result.columns
    assert "person.name" in column_names or any("person" in col and "name" in col for col in column_names)
    assert "person.age" in column_names or any("person" in col and "age" in col for col in column_names)
    assert "address.city" in column_names or any("address" in col and "city" in col for col in column_names)
    assert "address.street" in column_names or any("address" in col and "street" in col for col in column_names)



# Feature: etl-bronze-to-silver, Property 14: Explosión de arrays
@settings(max_examples=100)
@given(
    num_items=st.integers(min_value=1, max_value=10),
    product_names=st.lists(
        st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll'))),
        min_size=1,
        max_size=10
    )
)
def test_property_14_explode_arrays(spark, num_items, product_names):
    """
    Property 14: Explosión de arrays
    
    Para cualquier DataFrame con columnas de tipo ArrayType, después del aplanamiento,
    el número total de filas debe ser igual a la suma de las longitudes de todos los arrays.
    
    Valida: Requisito 4.2
    """
    # Create DataFrame with array column
    schema = StructType([
        StructField("id", IntegerType(), True),
        StructField("items", ArrayType(StringType()), True)
    ])
    
    # Limit the list to num_items
    items_list = product_names[:num_items]
    data = [(1, items_list)]
    df = spark.createDataFrame(data, schema)
    
    # Apply flattening
    flattener = JSONFlattener()
    result = flattener.transform(df, {})
    
    # Verify: Number of rows equals array length
    expected_rows = len(items_list)
    actual_rows = result.count()
    assert actual_rows == expected_rows, \
        f"Expected {expected_rows} rows after array explosion, got {actual_rows}"
    
    # Verify: No ArrayType columns remain
    for field in result.schema.fields:
        assert not isinstance(field.dataType, ArrayType), \
            f"Column {field.name} is still an ArrayType after flattening"


# Feature: etl-bronze-to-silver, Property 15: Aplanamiento recursivo de estructuras profundas
@settings(max_examples=100)
@given(
    level1_val=st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll'))),
    level2_val=st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll'))),
    level3_val=st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll')))
)
def test_property_15_recursive_flattening(spark, level1_val, level2_val, level3_val):
    """
    Property 15: Aplanamiento recursivo de estructuras profundas
    
    Para cualquier DataFrame con estructuras anidadas de 3 o más niveles,
    después del aplanamiento, todas las estructuras deben estar completamente aplanadas.
    
    Valida: Requisito 4.3
    """
    # Create DataFrame with 3-level nested structure
    schema = StructType([
        StructField("id", IntegerType(), True),
        StructField("level1", StructType([
            StructField("value1", StringType(), True),
            StructField("level2", StructType([
                StructField("value2", StringType(), True),
                StructField("level3", StructType([
                    StructField("value3", StringType(), True)
                ]), True)
            ]), True)
        ]), True)
    ])
    
    data = [(1, (level1_val, (level2_val, (level3_val,))))]
    df = spark.createDataFrame(data, schema)
    
    # Apply flattening
    flattener = JSONFlattener()
    result = flattener.transform(df, {})
    
    # Verify: No StructType columns remain (all flattened)
    for field in result.schema.fields:
        assert not isinstance(field.dataType, StructType), \
            f"Column {field.name} is still a StructType after recursive flattening"
    
    # Verify: Deep nested values are accessible
    column_names = result.columns
    has_deep_column = any(
        "level1" in col and "level2" in col and "level3" in col and "value3" in col
        for col in column_names
    )
    assert has_deep_column or "level1.level2.level3.value3" in column_names, \
        "Deep nested value not found in flattened columns"


# Feature: etl-bronze-to-silver, Property 16: Unicidad de nombres de columnas
@settings(max_examples=100)
@given(
    val1=st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll'))),
    val2=st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll')))
)
def test_property_16_unique_column_names(spark, val1, val2):
    """
    Property 16: Unicidad de nombres de columnas
    
    Para cualquier DataFrame procesado por JSONFlattener, todos los nombres de columnas
    en el DataFrame resultante deben ser únicos (sin colisiones).
    
    Valida: Requisito 4.4
    """
    # Create DataFrame with potential name collision
    # (two structs with same field name)
    schema = StructType([
        StructField("id", IntegerType(), True),
        StructField("data1", StructType([
            StructField("value", StringType(), True)
        ]), True),
        StructField("data2", StructType([
            StructField("value", StringType(), True)
        ]), True)
    ])
    
    data = [(1, (val1,), (val2,))]
    df = spark.createDataFrame(data, schema)
    
    # Apply flattening
    flattener = JSONFlattener()
    result = flattener.transform(df, {})
    
    # Verify: All column names are unique
    column_names = result.columns
    unique_names = set(column_names)
    assert len(column_names) == len(unique_names), \
        f"Duplicate column names found: {[name for name in column_names if column_names.count(name) > 1]}"


# Feature: etl-bronze-to-silver, Property 17: Idempotencia del aplanamiento
@settings(max_examples=100)
@given(
    id_val=st.integers(min_value=1, max_value=1000),
    name_val=st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll'))),
    age_val=st.integers(min_value=0, max_value=120)
)
def test_property_17_idempotence(spark, id_val, name_val, age_val):
    """
    Property 17: Idempotencia del aplanamiento
    
    Para cualquier DataFrame sin estructuras anidadas (solo tipos primitivos),
    después del aplanamiento, el DataFrame debe ser idéntico al DataFrame de entrada.
    
    Valida: Requisito 4.5
    """
    # Create DataFrame with only primitive types (no nesting)
    schema = StructType([
        StructField("id", IntegerType(), True),
        StructField("name", StringType(), True),
        StructField("age", IntegerType(), True)
    ])
    
    data = [(id_val, name_val, age_val)]
    df = spark.createDataFrame(data, schema)
    
    # Apply flattening
    flattener = JSONFlattener()
    result = flattener.transform(df, {})
    
    # Verify: Schema is identical
    assert df.schema == result.schema, \
        "Schema changed after flattening a flat DataFrame"
    
    # Verify: Data is identical
    assert df.collect() == result.collect(), \
        "Data changed after flattening a flat DataFrame"
    
    # Verify: Column names are identical
    assert df.columns == result.columns, \
        "Column names changed after flattening a flat DataFrame"
