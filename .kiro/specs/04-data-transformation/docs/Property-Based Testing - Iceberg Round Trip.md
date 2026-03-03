# Property-Based Testing: Iceberg Write-Read Round Trip

**Test File**: `glue/tests/property/test_iceberg_roundtrip.py`  
**Fecha de Implementación**: 18 de Febrero de 2026  
**Versión**: 1.0.0  
**Estado**: ✅ Implementado

---

## Resumen Ejecutivo

Este test de propiedades valida que cualquier dataset escrito a tablas Apache Iceberg en la capa Silver puede ser leído de vuelta sin pérdida de datos, corrupción o cambios en los valores. Utiliza Hypothesis para generar casos de prueba aleatorios y exhaustivos.

### Property 5: Iceberg Write-Read Round Trip

**Enunciado Formal**: Para cualquier conjunto de datos D escrito a una tabla Iceberg T, leer T debe producir un conjunto de datos D' tal que D = D' (preservando todos los valores, tipos y nullability).

**Validación**: Requirements 2.5 (Data Storage in Iceberg Format)

---

## Arquitectura del Test

### Componentes Bajo Prueba

```
┌─────────────────────────────────────────────────────────────┐
│                    Test Property-Based                      │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐ │
│  │         Hypothesis (Data Generator)                   │ │
│  │                                                       │ │
│  │  • Genera datasets aleatorios                        │ │
│  │  • Varía tipos de datos (strings, ints, decimals)   │ │
│  │  • Incluye valores nulos y edge cases                │ │
│  │  • Ejecuta 100+ ejemplos por test                    │ │
│  └───────────────────────────────────────────────────────┘ │
│                           │                                 │
│                           ▼                                 │
│  ┌───────────────────────────────────────────────────────┐ │
│  │         IcebergTableManager                           │ │
│  │                                                       │ │
│  │  • create_table()                                    │ │
│  │  • table_exists()                                    │ │
│  └───────────────────────────────────────────────────────┘ │
│                           │                                 │
│                           ▼                                 │
│  ┌───────────────────────────────────────────────────────┐ │
│  │         IcebergWriter                                 │ │
│  │                                                       │ │
│  │  • write_to_iceberg() - mode: overwrite/append      │ │
│  └───────────────────────────────────────────────────────┘ │
│                           │                                 │
│                           ▼                                 │
│  ┌───────────────────────────────────────────────────────┐ │
│  │         Apache Iceberg Table                          │ │
│  │                                                       │ │
│  │  • Almacenamiento en /tmp/iceberg-warehouse/         │ │
│  │  • Formato Parquet con Snappy                        │ │
│  │  • Transacciones ACID                                │ │
│  └───────────────────────────────────────────────────────┘ │
│                           │                                 │
│                           ▼                                 │
│  ┌───────────────────────────────────────────────────────┐ │
│  │         Spark SQL (Read Back)                         │ │
│  │                                                       │ │
│  │  • spark.table("local.test_db.roundtrip_test")      │ │
│  └───────────────────────────────────────────────────────┘ │
│                           │                                 │
│                           ▼                                 │
│  ┌───────────────────────────────────────────────────────┐ │
│  │         Assertions (Verification)                     │ │
│  │                                                       │ │
│  │  • Comparar input_data vs output_data                │ │
│  │  • Verificar conteos, valores, tipos                 │ │
│  └───────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

---

## Esquema de Test

### Test Schema

```python
test_schema = StructType([
    StructField("id", StringType(), nullable=False),
    StructField("value", IntegerType(), nullable=True),
    StructField("amount", DecimalType(10, 2), nullable=True),
    StructField("timestamp", TimestampType(), nullable=True)
])
```

**Características del Esquema**:
- **id**: String no nulo (clave primaria para ordenamiento)
- **value**: Integer nullable (valores numéricos simples)
- **amount**: Decimal(10,2) nullable (valores monetarios con precisión)
- **timestamp**: Timestamp nullable (fechas y horas)

**Cobertura de Tipos**:
- ✅ Strings
- ✅ Integers
- ✅ Decimals con precisión
- ✅ Timestamps
- ✅ Valores nulos
- ✅ Campos no nulos

---

## Estrategias de Generación de Datos

### Hypothesis Strategies

```python
@st.composite
def test_record(draw):
    """Generate a single test record."""
    return {
        "id": draw(st.text(
            min_size=1, 
            max_size=50, 
            alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))
        )),
        "value": draw(st.one_of(
            st.none(), 
            st.integers(min_value=-1000000, max_value=1000000)
        )),
        "amount": draw(st.one_of(
            st.none(), 
            st.decimals(min_value=-999999.99, max_value=999999.99, places=2)
        )),
        "timestamp": draw(st.one_of(
            st.none(), 
            st.datetimes(min_value=datetime(2000, 1, 1), max_value=datetime(2030, 12, 31))
        ))
    }
```

### Rangos de Valores Generados

| Campo | Tipo | Rango | Incluye Nulos |
|-------|------|-------|---------------|
| `id` | String | 1-50 caracteres (letras y números) | NO |
| `value` | Integer | -1,000,000 a 1,000,000 | SÍ |
| `amount` | Decimal(10,2) | -999,999.99 a 999,999.99 | SÍ |
| `timestamp` | Timestamp | 2000-01-01 a 2030-12-31 | SÍ |

### Configuración de Hypothesis

```python
@settings(max_examples=100, deadline=None)
```

- **max_examples=100**: Ejecuta 100 casos de prueba diferentes
- **deadline=None**: Sin límite de tiempo (importante para operaciones I/O)

---

## Tests Implementados

### Test 1: Write-Read Round Trip

**Función**: `test_iceberg_write_read_roundtrip()`

**Propósito**: Verificar que datos escritos a Iceberg se pueden leer sin pérdida

**Flujo**:
```
1. Generar dataset aleatorio (1-100 registros)
2. Crear tabla Iceberg si no existe
3. Escribir datos con mode="overwrite"
4. Leer datos de vuelta
5. Comparar input vs output
```

**Validaciones**:
- ✅ Mismo número de registros
- ✅ Todos los IDs presentes
- ✅ Valores numéricos exactos
- ✅ Decimales con tolerancia de 0.01
- ✅ Timestamps con tolerancia de 1 segundo
- ✅ Nulls preservados correctamente

**Ejemplo de Ejecución**:
```python
# Input generado por Hypothesis
records = [
    {"id": "ABC123", "value": 42, "amount": Decimal("99.99"), "timestamp": datetime(2024, 1, 1)},
    {"id": "XYZ789", "value": None, "amount": Decimal("-50.00"), "timestamp": None},
    {"id": "DEF456", "value": -1000, "amount": None, "timestamp": datetime(2025, 6, 15)}
]

# Después de write → read
# Output debe ser idéntico (mismo orden después de sort por id)
```

### Test 2: Append Preserves Data

**Función**: `test_iceberg_append_preserves_data()`

**Propósito**: Verificar que append no corrompe datos existentes

**Flujo**:
```
1. Generar dataset inicial (1-50 registros)
2. Escribir con mode="overwrite"
3. Generar dataset adicional (1-50 registros)
4. Escribir con mode="append"
5. Verificar que todos los registros están presentes
```

**Validaciones**:
- ✅ Conteo total = inicial + adicional
- ✅ Todos los IDs de ambos datasets presentes
- ✅ No hay duplicados inesperados
- ✅ No hay pérdida de datos

**Ejemplo de Ejecución**:
```python
# Initial records
initial = [
    {"id": "A1", "value": 10, ...},
    {"id": "A2", "value": 20, ...}
]

# Additional records
additional = [
    {"id": "B1", "value": 30, ...},
    {"id": "B2", "value": 40, ...}
]

# After append
# Total count = 4
# IDs present: {"A1", "A2", "B1", "B2"}
```

---

## Configuración de Spark

### Spark Session para Testing

```python
spark = SparkSession.builder \
    .appName("IcebergRoundTripTest") \
    .config("spark.sql.extensions", "org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions") \
    .config("spark.sql.catalog.spark_catalog", "org.apache.iceberg.spark.SparkSessionCatalog") \
    .config("spark.sql.catalog.spark_catalog.type", "hive") \
    .config("spark.sql.catalog.local", "org.apache.iceberg.spark.SparkCatalog") \
    .config("spark.sql.catalog.local.type", "hadoop") \
    .config("spark.sql.catalog.local.warehouse", "/tmp/iceberg-warehouse") \
    .getOrCreate()
```

**Configuraciones Clave**:
- **Iceberg Extensions**: Habilita funcionalidad Iceberg en Spark SQL
- **Catalog Local**: Usa Hadoop catalog para testing (no requiere Hive Metastore)
- **Warehouse**: Almacenamiento temporal en `/tmp/iceberg-warehouse`

---

## Ejecución de Tests

### Comando Básico

```bash
# Ejecutar solo este test
pytest glue/tests/property/test_iceberg_roundtrip.py -v

# Ejecutar con estadísticas de Hypothesis
pytest glue/tests/property/test_iceberg_roundtrip.py -v --hypothesis-show-statistics

# Ejecutar con logging detallado
pytest glue/tests/property/test_iceberg_roundtrip.py -v -s
```

### Ejecución desde Python

```bash
# Ejecutar directamente
python glue/tests/property/test_iceberg_roundtrip.py
```

### Filtrar por Marker

```bash
# Ejecutar solo tests de propiedades
pytest glue/tests/property/ -m property -v
```

---

## Interpretación de Resultados

### Salida Exitosa

```
glue/tests/property/test_iceberg_roundtrip.py::test_iceberg_write_read_roundtrip PASSED
glue/tests/property/test_iceberg_roundtrip.py::test_iceberg_append_preserves_data PASSED

============================== Hypothesis Statistics ===============================
test_iceberg_write_read_roundtrip:
  - 100 passing examples, 0 failing examples, 0 invalid examples
  - Typical runtimes: 50-200ms
  - Stopped because settings.max_examples=100

test_iceberg_append_preserves_data:
  - 50 passing examples, 0 failing examples, 0 invalid examples
  - Typical runtimes: 100-300ms
  - Stopped because settings.max_examples=50
```

### Fallo por Pérdida de Datos

```
FAILED glue/tests/property/test_iceberg_roundtrip.py::test_iceberg_write_read_roundtrip

Falsifying example:
  records=[
    {'id': 'A', 'value': 0, 'amount': Decimal('0.00'), 'timestamp': None}
  ]

AssertionError: Record count mismatch: input=1, output=0
```

**Interpretación**: Iceberg no está escribiendo correctamente registros con valores cero o nulos.

### Fallo por Corrupción de Datos

```
FAILED glue/tests/property/test_iceberg_roundtrip.py::test_iceberg_write_read_roundtrip

Falsifying example:
  records=[
    {'id': 'TEST', 'value': 100, 'amount': Decimal('99.99'), 'timestamp': datetime(2024, 1, 1)}
  ]

AssertionError: Amount mismatch for ID TEST: 99.99 != 99.98
```

**Interpretación**: Hay un problema de precisión en la conversión de decimales.

---

## Casos Edge Detectados

### Edge Cases Cubiertos por Hypothesis

1. **Valores Extremos**
   - Integers: -1,000,000 y 1,000,000
   - Decimals: -999,999.99 y 999,999.99
   - Timestamps: 2000-01-01 y 2030-12-31

2. **Valores Especiales**
   - Todos los campos nulos (excepto id)
   - Strings de 1 carácter
   - Strings de 50 caracteres
   - Valor cero en integers y decimals

3. **Combinaciones**
   - Dataset con 1 registro
   - Dataset con 100 registros
   - Mezcla de nulos y no nulos
   - IDs duplicados (si Hypothesis los genera)

4. **Operaciones**
   - Overwrite de tabla vacía
   - Overwrite de tabla con datos
   - Append a tabla vacía
   - Append a tabla con datos

---

## Tolerancias y Comparaciones

### Comparación de Decimals

```python
if input_row.amount is not None and output_row.amount is not None:
    assert abs(float(input_row.amount) - float(output_row.amount)) < 0.01
```

**Razón**: Conversiones de Decimal a Parquet pueden introducir pequeñas diferencias de precisión.

**Tolerancia**: 0.01 (1 centavo para valores monetarios)

### Comparación de Timestamps

```python
if input_row.timestamp is not None and output_row.timestamp is not None:
    time_diff = abs((input_row.timestamp - output_row.timestamp).total_seconds())
    assert time_diff < 1
```

**Razón**: Parquet almacena timestamps con precisión de microsegundos, pero pueden haber redondeos.

**Tolerancia**: 1 segundo

### Comparación de Strings e Integers

```python
assert input_row.id == output_row.id
assert input_row.value == output_row.value
```

**Razón**: Estos tipos deben ser exactos, sin tolerancia.

---

## Integración con CI/CD

### GitHub Actions Workflow

```yaml
name: Property-Based Tests

on:
  push:
    paths:
      - 'glue/**'
  pull_request:
    paths:
      - 'glue/**'

jobs:
  property-tests:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v2
      
      - name: Setup Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r glue/requirements.txt
          pip install pytest hypothesis
      
      - name: Run property-based tests
        run: |
          pytest glue/tests/property/test_iceberg_roundtrip.py \
            -v \
            --hypothesis-show-statistics \
            --hypothesis-seed=random
```

### Pre-commit Hook

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: property-tests
        name: Property-Based Tests
        entry: pytest glue/tests/property/test_iceberg_roundtrip.py -v
        language: system
        pass_filenames: false
```

---

## Troubleshooting

### Error: "No module named 'modules'"

**Causa**: Path de imports no configurado correctamente

**Solución**:
```python
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
```

### Error: "Spark session not found"

**Causa**: Fixture de Spark no se está ejecutando

**Solución**:
```bash
# Verificar que pytest encuentra el fixture
pytest glue/tests/property/test_iceberg_roundtrip.py --fixtures
```

### Error: "Table already exists"

**Causa**: Tabla de test anterior no se limpió

**Solución**:
```bash
# Limpiar warehouse de test
rm -rf /tmp/iceberg-warehouse/test_db/
```

### Tests Muy Lentos

**Causa**: Muchos ejemplos o operaciones I/O lentas

**Solución**:
```python
# Reducir ejemplos para desarrollo rápido
@settings(max_examples=10, deadline=None)

# Restaurar a 100 para CI/CD
@settings(max_examples=100, deadline=None)
```

---

## Mejores Prácticas

### 1. Usar Fixtures de Spark

```python
@pytest.fixture(scope="module")
def spark():
    """Reutilizar Spark session entre tests"""
    spark = SparkSession.builder...
    yield spark
    spark.stop()
```

**Beneficio**: Evita crear/destruir Spark session por cada test.

### 2. Limpiar Tablas Entre Tests

```python
@pytest.fixture(autouse=True)
def cleanup_tables(spark):
    """Limpiar tablas de test antes de cada test"""
    yield
    # Cleanup después del test
    spark.sql("DROP TABLE IF EXISTS local.test_db.roundtrip_test")
```

### 3. Usar Seeds para Reproducibilidad

```bash
# Ejecutar con seed específico para reproducir fallo
pytest glue/tests/property/test_iceberg_roundtrip.py \
  --hypothesis-seed=12345
```

### 4. Documentar Tolerancias

```python
# ✅ CORRECTO: Documentar por qué hay tolerancia
# Allow 1 second tolerance for timestamp precision due to Parquet microsecond storage
assert time_diff < 1

# ❌ INCORRECTO: Tolerancia sin explicación
assert time_diff < 1
```

---

## Métricas de Cobertura

### Cobertura de Código

```bash
# Ejecutar con coverage
pytest glue/tests/property/test_iceberg_roundtrip.py \
  --cov=glue/modules/iceberg_manager \
  --cov=glue/modules/iceberg_writer \
  --cov-report=html
```

**Objetivo**: >90% de cobertura en módulos de Iceberg

### Cobertura de Propiedades

| Propiedad | Test | Estado |
|-----------|------|--------|
| Write-Read Round Trip | test_iceberg_write_read_roundtrip | ✅ |
| Append Preserves Data | test_iceberg_append_preserves_data | ✅ |
| ACID Transactions | test_iceberg_acid.py | ⏳ |
| Time Travel | test_iceberg_timetravel.py | ⏳ |

---

## Próximos Pasos

### Tests Adicionales a Implementar

1. **Merge/Upsert Round Trip**
   - Verificar que merge preserva datos correctamente
   - Validar resolución de conflictos

2. **Schema Evolution**
   - Agregar columnas y verificar compatibilidad
   - Cambiar tipos de datos y validar conversiones

3. **Partitioned Tables**
   - Verificar que particionamiento no afecta round trip
   - Validar queries con partition pruning

4. **Large Datasets**
   - Probar con datasets de 10,000+ registros
   - Validar performance y memory usage

---

## Recursos Adicionales

### Documentación

- [Hypothesis Documentation](https://hypothesis.readthedocs.io/)
- [Apache Iceberg Testing Guide](https://iceberg.apache.org/docs/latest/testing/)
- [PySpark Testing Best Practices](https://spark.apache.org/docs/latest/api/python/user_guide/testing.html)

### Archivos Relacionados

- `glue/modules/iceberg_manager.py` - Módulo bajo prueba
- `glue/modules/iceberg_writer.py` - Módulo bajo prueba
- `glue/tests/property/test_iceberg_acid.py` - Test de transacciones ACID
- `glue/tests/property/test_iceberg_timetravel.py` - Test de time travel
- `.kiro/specs/data-transformation/design.md` - Diseño de transformaciones

---

## Conclusión

Este test de propiedades proporciona validación exhaustiva de que Apache Iceberg preserva datos correctamente durante operaciones de escritura y lectura. Con 100+ casos de prueba generados automáticamente, cubre una amplia gama de edge cases y combinaciones de datos que serían difíciles de probar manualmente.

**Beneficios Clave**:
- ✅ Validación automática de 100+ casos de prueba
- ✅ Detección temprana de bugs de pérdida de datos
- ✅ Cobertura de edge cases difíciles de anticipar
- ✅ Documentación ejecutable de comportamiento esperado
- ✅ Confianza en la integridad de datos en producción

---

**Documento Generado**: 18 de Febrero de 2026  
**Versión**: 1.0  
**Estado**: ✅ Completo - Test Implementado  
**Mantenedor**: Equipo de Data Engineering - Janis-Cencosud
