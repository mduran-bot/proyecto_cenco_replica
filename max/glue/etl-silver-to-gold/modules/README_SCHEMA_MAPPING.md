# Schema Mapping Modules for Gold Layer

Este documento describe los tres módulos implementados para el mapeo de esquemas desde Silver a Gold layer.

## Módulos Implementados

### 1. SchemaMapper (`schema_mapper.py`)

**Propósito**: Mapea campos desde Silver layer a Gold layer aplicando transformaciones según configuración en `field_mappings.json`.

**Funcionalidades**:
- ✅ Selección de campos específicos (ej: 43 de 91 campos para wms_orders)
- ✅ Renombrado de campos (dateCreated → date_created)
- ✅ Aplanamiento de JSON anidados (totals.items.amount → items_amount)
- ✅ Transformaciones de tipos de datos

**Transformaciones Soportadas**:
- `direct`: Copia directa del campo
- `flatten`: Extrae campo de objeto anidado (ej: addresses[0].city)
- `array_first`: Toma primer elemento de array
- `timestamp_to_iso8601`: Convierte Unix timestamp a ISO 8601
- `tinyint_to_boolean`: Convierte 0/1 a false/true
- `bigint_to_string`: Convierte BIGINT a VARCHAR
- `decimal_to_numeric`: Preserva precisión decimal
- `status_mapping`: Mapea códigos de estado a strings
- `parent_id`: Usa ID del registro padre
- `explode_array`: Explota array en múltiples registros (para tablas hijas)

**Uso**:
```python
from modules.schema_mapper import SchemaMapper

mapper = SchemaMapper()
config = {"gold_table": "wms_orders"}
mapped_df = mapper.transform(silver_df, config)
```

### 2. CalculatedFieldsEngine (`calculated_fields_engine.py`)

**Propósito**: Calcula campos derivados según configuración en `redshift_schemas.json`.

**Campos Calculados Implementados**:
- ✅ `total_changes` (wms_orders): `totals.items.amount - totals.items.originalAmount`
- ✅ `total_time` (wms_order_picking): `(endPickingTime - startPickingTime) / 1000`
- ✅ `username` (admins): `firstname + ' ' + lastname`
- ✅ `quantity_difference` (wms_order_items): `quantity_picked - quantity`

**Manejo de NULL**:
- Si algún campo fuente es NULL, el resultado es NULL (sin errores)
- Usa expresiones `when().otherwise()` de PySpark para manejo seguro

**Uso**:
```python
from modules.calculated_fields_engine import CalculatedFieldsEngine

engine = CalculatedFieldsEngine()
config = {"gold_table": "wms_orders"}
calculated_df = engine.transform(mapped_df, config)
```

### 3. DataQualityValidator (`data_quality_validator.py`)

**Propósito**: Valida calidad de datos en 6 dimensiones antes de escribir a Gold.

**Validaciones Implementadas**:
- ✅ **Completeness**: Campos críticos no nulos
- ✅ **Validity**: Valores permitidos
- ✅ **Numeric Ranges**: Rangos numéricos (quantity >= 0, price >= 0, lat entre -90 y 90)
- ✅ **Consistency**: Valores coherentes entre columnas
- ✅ **Format Validation**: Formatos de email (con @) y phone (numérico)
- ✅ **PK Uniqueness**: Claves primarias únicas
- ⚠️ **FK Integrity**: Claves foráneas válidas (opcional, costoso - no implementado)

**Integración con Esquemas**:
- Lee validaciones automáticamente desde `redshift_schemas.json`
- Extrae campos no nullable como críticos
- Infiere rangos numéricos según tipos de datos
- Detecta campos de email y phone para validación de formato

**Uso**:
```python
from modules.data_quality_validator import DataQualityValidator

validator = DataQualityValidator()
config = {
    "gold_table": "wms_orders",
    "quality": {
        "validate_pk_uniqueness": True,
        "validate_fk_integrity": False,  # Costoso
        "quality_gate": True,
        "threshold": 0.95
    }
}
validated_df = validator.transform(calculated_df, config)
```

## Flujo de Transformación Completo

```python
# 1. Mapeo de esquema (selección y renombrado)
mapper = SchemaMapper()
mapped_df = mapper.transform(silver_df, {"gold_table": "wms_orders"})

# 2. Cálculo de campos derivados
engine = CalculatedFieldsEngine()
calculated_df = engine.transform(mapped_df, {"gold_table": "wms_orders"})

# 3. Validación de calidad
validator = DataQualityValidator()
validated_df = validator.transform(calculated_df, {
    "gold_table": "wms_orders",
    "quality": {"quality_gate": True, "threshold": 0.95}
})

# 4. Escribir a Gold layer
validated_df.write.format("iceberg").mode("append").save("gold.wms_orders")
```

## Archivos de Configuración

### field_mappings.json
Define el mapeo de campos para cada tabla Gold:
```json
{
  "mappings": {
    "wms_orders": {
      "source_entity": "orders",
      "fields": {
        "order_id": {
          "source": "id",
          "transformation": "direct"
        },
        "total_changes": {
          "source": "calculated",
          "transformation": "calculate",
          "formula": "totals.items.amount - totals.items.originalAmount"
        }
      }
    }
  }
}
```

### redshift_schemas.json
Define esquemas completos de tablas Gold con tipos, PKs, FKs, campos calculados y data gaps:
```json
{
  "tables": {
    "wms_orders": {
      "fields": {
        "order_id": {
          "type": "BIGINT",
          "nullable": false,
          "primary_key": true
        },
        "total_changes": {
          "type": "NUMERIC(15,5)",
          "nullable": true,
          "calculated": true,
          "formula": "totals.items.amount - totals.items.originalAmount"
        }
      }
    }
  }
}
```

## Requisitos Validados

### Requirement 6.1, 6.2, 6.5, 6.6 (SchemaMapper)
✅ Aplica Schema_Mapping según documento de análisis
✅ Selecciona campos específicos (43 de 91 para wms_orders)
✅ Renombra campos (dateCreated → date_created)
✅ Aplana estructuras JSON anidadas

### Requirement 4.1, 4.2, 4.3, 4.4, 4.6 (CalculatedFieldsEngine)
✅ Calcula total_changes para wms_orders
✅ Calcula total_time para wms_order_picking
✅ Calcula username para admins
✅ Calcula quantity_difference para wms_order_items
✅ Maneja NULL sin errores

### Requirement 12.1, 12.2, 12.3, 12.4 (DataQualityValidator)
✅ Valida unicidad de PKs
⚠️ Valida integridad de FKs (opcional, no implementado - costoso)
✅ Valida rangos numéricos (quantity >= 0, price >= 0)
✅ Valida formatos (email con @, phone numérico)
✅ Lee reglas de validación desde redshift_schemas.json

## Próximos Pasos

Para integrar estos módulos en el pipeline Silver→Gold:

1. Actualizar `etl_pipeline_gold.py` para usar los nuevos módulos
2. Actualizar `run_pipeline_to_gold.py` para pasar configuración correcta
3. Crear tests unitarios para cada módulo
4. Probar con datos reales de 3-5 entidades representativas

## Notas Técnicas

- Todos los módulos manejan NULL gracefully sin generar errores
- Los módulos son independientes y pueden usarse por separado
- La configuración es centralizada en archivos JSON
- Los logs son detallados para debugging
- Las validaciones son configurables y extensibles
