# Integración DataGapHandler - Merge Completado

**Fecha:** 19 de Febrero, 2026  
**Estado:** ✅ Merge Completado  
**Módulo:** DataGapHandler (Max + Vicente) integrado en glue/modules/

---

## Resumen Ejecutivo

Se completó exitosamente el merge del módulo `DataGapHandler`, combinando el sistema de metadata tracking y cálculos específicos del dominio de Vicente con el filling automático y filtrado de Max. El módulo resultante ofrece soporte dual para pandas y PySpark, proporcionando flexibilidad máxima para diferentes casos de uso.

---

## Estrategia de Merge

### Base: Vicente (Metadata Tracking)
- Cálculos específicos del dominio bien documentados
- Sistema de metadata tracking (_data_gaps)
- Método `generate_data_gap_report()` para documentación
- Reglas predefinidas (CALCULATED_FIELD_RULES, UNAVAILABLE_FIELDS)
- Marcado explícito de campos no disponibles

### Agregado: Max (Filling Automático)
- Filling automático con valores por defecto (PySpark)
- Marcado de registros con gaps críticos (has_critical_gaps)
- Filtrado opcional de registros incompletos
- Configuración de columnas críticas y defaults
- Procesamiento eficiente con PySpark

---

## Características Implementadas

### 1. Soporte Dual pandas/PySpark

**Pandas (Vicente)**:
```python
from modules import DataGapHandler

# Cálculos específicos del dominio
handler = DataGapHandler()
df_with_calcs = handler.calculate_items_substituted_qty(df)
df_with_calcs = handler.calculate_items_qty_missing(df_with_calcs)
df_with_calcs = handler.calculate_total_changes(df_with_calcs)

# Marcar campos no disponibles
df_marked = handler.mark_unavailable_fields(df_with_calcs, UNAVAILABLE_FIELDS['wms_orders'])

# Generar reporte
report = handler.generate_data_gap_report(df_marked)
```

**PySpark (Max)**:
```python
from modules import DataGapHandler

# Filling automático con configuración
handler = DataGapHandler()
config = {
    "data_gap_handling": {
        "critical_columns": ["order_id", "customer_id"],
        "default_values": {
            "status": "unknown",
            "quantity": 0
        },
        "filter_incomplete": True
    }
}
df_filled = handler.transform(df, config)
```

### 2. Cálculos Específicos del Dominio (Vicente)

#### Campos Calculados

| Campo | Fórmula | Descripción |
|-------|---------|-------------|
| `items_substituted_qty` | COUNT(items WHERE substitute_type = 'substitute') | Cantidad de items sustituidos |
| `items_qty_missing` | SUM(quantity - COALESCE(quantity_picked, 0)) | Cantidad faltante de items |
| `total_changes` | amount - originalAmount | Cambios totales en monto |

#### Ejemplo de Uso

```python
from modules import DataGapHandler
import pandas as pd

# DataFrame con datos de órdenes
df = pd.DataFrame({
    'order_id': [1, 2],
    'items': [
        [{'substitute_type': 'substitute'}, {'substitute_type': 'original'}],
        [{'substitute_type': 'substitute'}]
    ],
    'quantity': [10, 5],
    'quantity_picked': [8, 5],
    'amount': [100.0, 50.0],
    'originalAmount': [95.0, 50.0]
})

handler = DataGapHandler()

# Calcular campos
df = handler.calculate_items_substituted_qty(df)
df = handler.calculate_items_qty_missing(df)
df = handler.calculate_total_changes(df)

# Resultado:
# items_substituted_qty: [1, 1]
# items_qty_missing: [2, 0]
# total_changes: [5.0, 0.0]
```

### 3. Sistema de Metadata Tracking (Vicente)

#### Marcado de Campos No Disponibles

```python
from modules import DataGapHandler

# Definir campos no disponibles
unavailable_fields = {
    'wms_orders': [
        'items_substituted_qty',  # No disponible en API v2
        'items_qty_missing',      # No disponible en API v2
        'total_changes'           # No disponible en API v2
    ]
}

# Marcar campos
handler = DataGapHandler()
df_marked = handler.mark_unavailable_fields(df, unavailable_fields['wms_orders'])

# Resultado: Agrega columna _data_gaps con metadata
# _data_gaps: {
#     "unavailable_fields": ["items_substituted_qty", "items_qty_missing"],
#     "calculated_fields": ["total_changes"],
#     "impact": "medium"
# }
```

#### Generación de Reportes

```python
# Generar reporte de gaps
report = handler.generate_data_gap_report(df_marked)

# Resultado:
# {
#     "total_records": 100,
#     "records_with_gaps": 45,
#     "unavailable_fields": {
#         "items_substituted_qty": 45,
#         "items_qty_missing": 45
#     },
#     "calculated_fields": {
#         "total_changes": 100
#     },
#     "impact_assessment": "medium"
# }
```

### 4. Filling Automático (Max)

#### Configuración de Defaults

```python
config = {
    "data_gap_handling": {
        "critical_columns": ["order_id", "customer_id", "store_id"],
        "default_values": {
            "status": "unknown",
            "quantity": 0,
            "price": 0.0,
            "discount": 0.0
        },
        "filter_incomplete": True  # Filtrar registros con gaps críticos
    }
}
```

#### Ejemplo de Uso

```python
from pyspark.sql import SparkSession
from modules import DataGapHandler

spark = SparkSession.builder.appName("gap_handling").getOrCreate()

# DataFrame con gaps
df = spark.createDataFrame([
    (1, "John", None, 10),      # status missing
    (2, "Jane", "active", None), # quantity missing
    (None, "Bob", "active", 5),  # order_id missing (crítico)
], ["order_id", "customer", "status", "quantity"])

# Filling automático
handler = DataGapHandler()
df_filled = handler.transform(df, config)

# Resultado:
# - Registro 1: status = "unknown"
# - Registro 2: quantity = 0
# - Registro 3: Filtrado (order_id crítico faltante)
# - Columna has_critical_gaps agregada
```

---

## Arquitectura del Módulo

### Estructura de Clases

```python
class DataGapHandler:
    """Manejador de gaps de datos con soporte pandas y PySpark."""
    
    # ========================================================================
    # VICENTE'S DOMAIN-SPECIFIC CALCULATIONS (Pandas-based)
    # ========================================================================
    
    @staticmethod
    def calculate_items_substituted_qty(df) -> pd.DataFrame: ...
    
    @staticmethod
    def calculate_items_qty_missing(df) -> pd.DataFrame: ...
    
    @staticmethod
    def calculate_total_changes(df) -> pd.DataFrame: ...
    
    @staticmethod
    def mark_unavailable_fields(df, unavailable_fields) -> pd.DataFrame: ...
    
    @staticmethod
    def generate_data_gap_report(df) -> dict: ...
    
    # ========================================================================
    # MAX'S AUTOMATIC FILLING (PySpark-based)
    # ========================================================================
    
    def transform(self, df, config) -> SparkDataFrame: ...
    
    def _fill_missing_values(self, df, default_values) -> SparkDataFrame: ...
    
    def _mark_critical_gaps(self, df, critical_columns) -> SparkDataFrame: ...
    
    def _filter_incomplete_records(self, df) -> SparkDataFrame: ...
```

### Imports Opcionales

```python
# PySpark imports (optional - only needed for PySpark functionality)
try:
    from pyspark.sql import DataFrame as SparkDataFrame
    from pyspark.sql.functions import col, when, coalesce, lit
    PYSPARK_AVAILABLE = True
except ImportError:
    PYSPARK_AVAILABLE = False
    SparkDataFrame = None
```

---

## Reglas Predefinidas

### Campos Calculados

```python
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
```

### Campos No Disponibles

```python
UNAVAILABLE_FIELDS = {
    'wms_orders': [
        'items_substituted_qty',
        'items_qty_missing',
        'total_changes'
    ],
    'wms_order_items': [
        'discount_percentage',
        'tax_amount'
    ]
}
```

---

## Casos de Uso

### Caso 1: Pipeline Bronze-to-Silver (PySpark)

```python
from modules import DataGapHandler

# En un Glue job
handler = DataGapHandler()

# Leer desde Bronze
df_bronze = spark.read.parquet("s3://bronze/orders/")

# Filling automático con configuración
config = {
    "data_gap_handling": {
        "critical_columns": ["order_id", "customer_id"],
        "default_values": {
            "status": "unknown",
            "quantity": 0
        },
        "filter_incomplete": True
    }
}
df_filled = handler.transform(df_bronze, config)

# Escribir a Silver
df_filled.write.format("iceberg").save("silver.orders")
```

### Caso 2: Análisis de Gaps (Pandas)

```python
from modules import DataGapHandler
import pandas as pd

# Leer datos de prueba
df = pd.read_csv("test_data.csv")

# Calcular campos
handler = DataGapHandler()
df = handler.calculate_items_substituted_qty(df)
df = handler.calculate_items_qty_missing(df)
df = handler.calculate_total_changes(df)

# Marcar campos no disponibles
df = handler.mark_unavailable_fields(df, UNAVAILABLE_FIELDS['wms_orders'])

# Generar reporte
report = handler.generate_data_gap_report(df)
print(f"Records with gaps: {report['records_with_gaps']}")
print(f"Impact: {report['impact_assessment']}")
```

### Caso 3: Filling Selectivo

```python
from modules import DataGapHandler

# Filling solo para campos específicos
config = {
    "data_gap_handling": {
        "default_values": {
            "status": "pending",
            "priority": "normal"
        },
        "filter_incomplete": False  # No filtrar, solo llenar
    }
}

handler = DataGapHandler()
df_filled = handler.transform(df, config)
```

---

## Testing

### Tests Existentes

**Vicente (Pandas)**:
- Tests unitarios para cada cálculo
- Validación de fórmulas con datos conocidos
- Tests de generación de reportes

**Max (PySpark)**:
- Tests de filling automático
- Validación de marcado de gaps críticos
- Tests de filtrado de registros

### Tests Pendientes

1. **Tests de Integración**:
   - Validar cálculos pandas → filling PySpark
   - Verificar consistencia entre ambos enfoques
   - Tests con datasets reales de Janis

2. **Property-Based Tests**:
   - Property 8: Calculated Fields Correctness
   - Property 9: Missing Field Metadata Annotation
   - Property 10: Graceful Handling of Missing Non-Critical Fields

3. **Performance Tests**:
   - Benchmarking de filling automático
   - Comparación pandas vs PySpark en diferentes tamaños
   - Optimización de cálculos complejos

---

## Impacto en el Pipeline

### Bronze → Silver

**Antes (Solo Vicente)**:
```python
# Cálculos manuales con fórmulas predefinidas
df = calculate_items_substituted_qty(df)
df = calculate_items_qty_missing(df)
df = mark_unavailable_fields(df, UNAVAILABLE_FIELDS['wms_orders'])
```

**Después (Vicente + Max)**:
```python
# Opción 1: Cálculos explícitos (pandas)
handler = DataGapHandler()
df = handler.calculate_items_substituted_qty(df)
df = handler.mark_unavailable_fields(df, unavailable_fields)

# Opción 2: Filling automático (PySpark)
handler = DataGapHandler()
df = handler.transform(df, config)

# Opción 3: Híbrido (cálculos + filling)
df_calcs = handler.calculate_items_substituted_qty(df)
df_filled = handler.transform(df_calcs, config)
```

### Ventajas del Merge

1. **Flexibilidad**: Elegir entre cálculos explícitos o filling automático
2. **Robustez**: Cálculos de Vicente + automatización de Max
3. **Escalabilidad**: PySpark para grandes volúmenes, pandas para análisis
4. **Observabilidad**: Reportes detallados de gaps y su impacto

---

## Compatibilidad

### Código Existente de Vicente
✅ **100% compatible** - Todos los métodos estáticos mantienen su firma

### Código Existente de Max
✅ **100% compatible** - Método `transform()` agregado sin modificar existentes

### Nuevas Capacidades
- Filling automático con defaults configurables
- Marcado de gaps críticos
- Filtrado de registros incompletos
- Generación de reportes de impacto

---

## Próximos Pasos

### Fase 1: Testing (Prioridad Alta)
1. Crear tests unitarios para filling automático
2. Validar cálculos con datos reales de Janis
3. Benchmarking de performance

### Fase 2: Documentación (Prioridad Media)
1. Actualizar README con ejemplos de uso
2. Crear guía de configuración de defaults
3. Documentar mejores prácticas

### Fase 3: Optimización (Prioridad Baja)
1. Optimizar cálculos complejos
2. Agregar más estrategias de filling
3. Implementar interpolación para series de tiempo

---

## Conclusión

El merge de `DataGapHandler` fue exitoso, resultando en un módulo que:
- Mantiene todos los cálculos específicos del dominio de Vicente
- Agrega filling automático inteligente de Max
- Es 100% compatible con código existente de ambos
- Proporciona flexibilidad máxima para diferentes casos de uso
- Mejora significativamente la completitud de datos del pipeline

**Estado**: ✅ Listo para testing y uso en pipeline

---

**Documento creado:** 19 de Febrero, 2026  
**Última actualización:** 19 de Febrero, 2026  
**Autor:** Sistema de Integración Max-Vicente
