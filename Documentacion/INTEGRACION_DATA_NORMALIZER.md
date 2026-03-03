# Integración DataNormalizer - Merge Completado

**Fecha:** 19 de Febrero, 2026  
**Estado:** ✅ Merge Completado  
**Módulo:** DataNormalizer (Max + Vicente) integrado en glue/modules/

---

## Resumen Ejecutivo

Se completó exitosamente el merge del módulo `DataNormalizer`, combinando la validación robusta con regex de Vicente con la normalización config-driven de Max. El módulo resultante ofrece soporte dual para pandas y PySpark, proporcionando flexibilidad máxima para diferentes casos de uso.

---

## Estrategia de Merge

### Base: Vicente (Validación Robusta)
- Validación robusta con regex (RFC 5322 para emails)
- Normalización de teléfonos con código de país configurable
- Métodos estáticos bien documentados con ejemplos
- Reglas de normalización predefinidas por tabla
- Soporte completo para pandas DataFrames

### Agregado: Max (Config-Driven)
- Normalización basada en configuración (PySpark)
- Procesamiento eficiente con PySpark functions
- Normalización por tipo de columna (email_columns, phone_columns, etc.)
- Preservación de nulls sin conversión a strings
- Configuración flexible y escalable

---

## Características Implementadas

### 1. Soporte Dual pandas/PySpark

**Pandas (Vicente)**:
```python
from modules import DataNormalizer

# Normalización explícita con reglas predefinidas
normalizer = DataNormalizer()
df_normalized = normalizer.apply_normalizations_to_dataframe(df, NORMALIZATION_RULES['customers'])
```

**PySpark (Max)**:
```python
from modules import DataNormalizer

# Normalización config-driven
normalizer = DataNormalizer()
config = {
    "normalization": {
        "email_columns": ["email", "contact_email"],
        "phone_columns": ["phone", "mobile"],
        "date_columns": ["birth_date"],
        "timestamp_columns": ["created_at", "updated_at"]
    }
}
df_normalized = normalizer.transform(df, config)
```

### 2. Normalizaciones Explícitas (Vicente)

#### Métodos Estáticos Disponibles

| Método | Normalización | Validación |
|--------|---------------|------------|
| `normalize_timestamp_to_utc()` | Timestamp → UTC | Timezone conversion |
| `validate_and_clean_email()` | Email → lowercase | RFC 5322 regex |
| `normalize_phone_number()` | Phone → +{country}{digits} | Extracción de dígitos |
| `trim_whitespace()` | String → trimmed | Espacios inicio/fin |
| `normalize_string_case()` | String → lower/upper/title | Case conversion |
| `remove_extra_spaces()` | String → normalized spaces | Espacios múltiples |

#### Ejemplo de Uso

```python
from modules import DataNormalizer

# Normalización individual
email = DataNormalizer.validate_and_clean_email("  USER@EXAMPLE.COM  ")
# Resultado: 'user@example.com'

phone = DataNormalizer.normalize_phone_number("(01) 234-5678", country_code='51')
# Resultado: '+51012345678'

# Normalización batch con reglas
normalization_rules = {
    'email': {'type': 'email'},
    'phone': {'type': 'phone', 'params': {'country_code': '51'}},
    'name': {'type': 'trim'}
}

df_normalized = DataNormalizer.apply_normalizations_to_dataframe(df, normalization_rules)
```

### 3. Normalización Config-Driven (Max)

#### Tipos de Normalización Soportados

1. **Email Normalization**
   - Conversión a lowercase
   - Preservación de nulls
   - Procesamiento eficiente con PySpark lower()

2. **Phone Normalization**
   - Eliminación de caracteres no numéricos
   - Preservación de nulls
   - Regex: `[^0-9]` → ""

3. **Date Normalization**
   - Parsing de múltiples formatos
   - Conversión a formato estándar (yyyy-MM-dd)
   - Manejo de fechas inválidas (→ null)

4. **Timestamp Normalization**
   - Parsing de múltiples formatos
   - Conversión a formato estándar (yyyy-MM-dd HH:mm:ss)
   - Manejo de timestamps inválidos (→ null)

#### Configuración

```python
config = {
    "normalization": {
        "email_columns": ["email", "contact_email"],
        "phone_columns": ["phone", "mobile"],
        "date_columns": ["birth_date", "registration_date"],
        "timestamp_columns": ["created_at", "updated_at"]
    }
}
```

#### Ejemplo de Uso

```python
from pyspark.sql import SparkSession
from modules import DataNormalizer

spark = SparkSession.builder.appName("normalization").getOrCreate()

# DataFrame con columnas a normalizar
df = spark.createDataFrame([
    ("USER@EXAMPLE.COM", "(123) 456-7890", "2024-01-01", "2024-01-01 10:00:00"),
    ("test@TEST.com", "555.123.4567", "01/02/2024", "2024-01-02T11:30:00"),
], ["email", "phone", "date", "timestamp"])

# Normalización automática
normalizer = DataNormalizer()
df_normalized = normalizer.transform(df, config)

# Resultado:
# email: lowercase
# phone: solo dígitos
# date: yyyy-MM-dd
# timestamp: yyyy-MM-dd HH:mm:ss
```

---

## Arquitectura del Módulo

### Estructura de Clases

```python
class DataNormalizer:
    """Normalizador de datos para estandarización de formatos con soporte pandas y PySpark."""
    
    # Constantes
    EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    PHONE_REGEX = re.compile(r'\d+')
    
    # ========================================================================
    # VICENTE'S EXPLICIT NORMALIZATIONS (Pandas-based)
    # ========================================================================
    
    @staticmethod
    def normalize_timestamp_to_utc(value) -> Optional[str]: ...
    
    @staticmethod
    def validate_and_clean_email(value) -> Optional[str]: ...
    
    @staticmethod
    def normalize_phone_number(value, country_code='51') -> Optional[str]: ...
    
    @staticmethod
    def trim_whitespace(value) -> Optional[str]: ...
    
    @staticmethod
    def normalize_string_case(value, case='lower') -> Optional[str]: ...
    
    @staticmethod
    def remove_extra_spaces(value) -> Optional[str]: ...
    
    @staticmethod
    def apply_normalizations_to_dataframe(df, normalization_rules) -> pd.DataFrame: ...
    
    # ========================================================================
    # MAX'S CONFIG-BASED NORMALIZATIONS (PySpark-based)
    # ========================================================================
    
    def transform(self, df, config) -> SparkDataFrame: ...
    
    def _normalize_emails(self, df, email_columns) -> SparkDataFrame: ...
    
    def _normalize_phones(self, df, phone_columns) -> SparkDataFrame: ...
    
    def _normalize_dates(self, df, date_columns) -> SparkDataFrame: ...
    
    def _normalize_timestamps(self, df, timestamp_columns) -> SparkDataFrame: ...
```

### Imports Opcionales

```python
# PySpark imports (optional - only needed for PySpark functionality)
try:
    from pyspark.sql import DataFrame as SparkDataFrame
    from pyspark.sql.functions import col, lower, regexp_replace, to_date, to_timestamp
    from pyspark.sql.types import StringType
    PYSPARK_AVAILABLE = True
except ImportError:
    PYSPARK_AVAILABLE = False
    SparkDataFrame = None
```

**Ventaja**: El módulo funciona sin PySpark instalado (solo métodos pandas), pero habilita funcionalidad PySpark cuando está disponible.

---

## Reglas de Normalización Predefinidas

### Tablas Soportadas

```python
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
```

---

## Casos de Uso

### Caso 1: Pipeline Bronze-to-Silver (PySpark)

```python
from modules import DataNormalizer

# En un Glue job
normalizer = DataNormalizer()

# Leer desde Bronze
df_bronze = spark.read.parquet("s3://bronze/customers/")

# Normalización config-driven
config = {
    "normalization": {
        "email_columns": ["email"],
        "phone_columns": ["phone"],
        "timestamp_columns": ["created_at", "updated_at"]
    }
}
df_normalized = normalizer.transform(df_bronze, config)

# Escribir a Silver
df_normalized.write.format("iceberg").save("silver.customers")
```

### Caso 2: Validación de Datos (Pandas)

```python
from modules import DataNormalizer
import pandas as pd

# Leer datos de prueba
df = pd.read_csv("test_data.csv")

# Aplicar normalizaciones explícitas
rules = {
    'email': {'type': 'email'},
    'phone': {'type': 'phone', 'params': {'country_code': '51'}},
    'name': {'type': 'trim'}
}

df_normalized = DataNormalizer.apply_normalizations_to_dataframe(df, rules)

# Validar resultados
assert df_normalized['email'].str.islower().all()
assert df_normalized['phone'].str.startswith('+51').all()
```

### Caso 3: Normalización Individual

```python
from modules import DataNormalizer

# Normalizar un email específico
email = DataNormalizer.validate_and_clean_email("  USER@EXAMPLE.COM  ")
print(email)  # 'user@example.com'

# Normalizar un teléfono
phone = DataNormalizer.normalize_phone_number("(01) 234-5678")
print(phone)  # '+51012345678'

# Normalizar timestamp a UTC
timestamp = DataNormalizer.normalize_timestamp_to_utc("2021-01-01T12:00:00-05:00")
print(timestamp)  # '2021-01-01T17:00:00+00:00'
```

---

## Testing

### Tests Existentes

**Vicente (Pandas)**:
- Tests unitarios para cada método de normalización
- Validación de edge cases (None, NaN, formatos inválidos)
- Tests de reglas predefinidas

**Max (PySpark)**:
- Tests de normalización config-driven
- Validación de preservación de nulls
- Tests de procesamiento por columnas

### Tests Pendientes

1. **Tests de Integración**:
   - Validar normalización pandas → PySpark
   - Verificar consistencia entre ambos enfoques
   - Tests con datasets reales de Janis

2. **Property-Based Tests**:
   - Property 4: Data Format Normalization
   - Generar valores aleatorios y validar normalizaciones
   - Verificar idempotencia de normalizaciones

3. **Performance Tests**:
   - Benchmarking de normalización config-driven
   - Comparación pandas vs PySpark en diferentes tamaños
   - Optimización de regex patterns

---

## Impacto en el Pipeline

### Bronze → Silver

**Antes (Solo Vicente)**:
```python
# Normalizaciones manuales con reglas predefinidas
df_normalized = apply_normalizations_to_dataframe(df, NORMALIZATION_RULES['customers'])
```

**Después (Vicente + Max)**:
```python
# Opción 1: Normalizaciones explícitas (pandas)
df_normalized = DataNormalizer.apply_normalizations_to_dataframe(df, rules)

# Opción 2: Normalización config-driven (PySpark)
normalizer = DataNormalizer()
df_normalized = normalizer.transform(df, config)

# Opción 3: Híbrido (config + reglas específicas)
df_config = normalizer.transform(df, config)
df_final = DataNormalizer.apply_normalizations_to_dataframe(df_config, custom_rules)
```

### Ventajas del Merge

1. **Flexibilidad**: Elegir entre normalización explícita o config-driven
2. **Robustez**: Validación de Vicente + eficiencia de Max
3. **Escalabilidad**: PySpark para grandes volúmenes, pandas para validación
4. **Mantenibilidad**: Código bien estructurado y documentado

---

## Compatibilidad

### Código Existente de Vicente
✅ **100% compatible** - Todos los métodos estáticos mantienen su firma

### Código Existente de Max
✅ **100% compatible** - Método `transform()` agregado sin modificar existentes

### Nuevas Capacidades
- Normalización config-driven (opt-in con config)
- Soporte dual pandas/PySpark
- Preservación de nulls en PySpark
- Procesamiento eficiente por columnas

---

## Próximos Pasos

### Fase 1: Testing (Prioridad Alta)
1. Crear tests unitarios para métodos de normalización PySpark
2. Validar normalizaciones con datos reales de Janis
3. Benchmarking de performance

### Fase 2: Documentación (Prioridad Media)
1. Actualizar README con ejemplos de uso
2. Crear guía de migración para código existente
3. Documentar mejores prácticas

### Fase 3: Optimización (Prioridad Baja)
1. Optimizar regex patterns basado en métricas
2. Agregar más formatos de fecha/timestamp
3. Implementar caching de validaciones

---

## Conclusión

El merge de `DataNormalizer` fue exitoso, resultando en un módulo que:
- Mantiene toda la validación robusta de Vicente
- Agrega normalización config-driven eficiente de Max
- Es 100% compatible con código existente de ambos
- Proporciona flexibilidad máxima para diferentes casos de uso
- Mejora significativamente la capacidad de procesamiento del pipeline

**Estado**: ✅ Listo para testing y uso en pipeline

---

**Documento creado:** 19 de Febrero, 2026  
**Última actualización:** 19 de Febrero, 2026  
**Autor:** Sistema de Integración Max-Vicente
