# Documentación - Data Transformation

Esta carpeta contiene la documentación específica relacionada con el spec de transformación de datos (data-transformation).

## Contenido

### Guías de Implementación

- **Sistema de Transformación de Datos - Resumen Ejecutivo.md**: Resumen del sistema ETL Bronze → Silver → Gold
- **Iceberg Manager - Guía de Uso.md**: Guía completa del módulo IcebergTableManager para gestión de tablas Apache Iceberg

### Documentación de Testing

- **Property-Based Testing - Iceberg Round Trip.md**: Documentación completa del test de propiedades para validar integridad de datos en operaciones write-read de Iceberg

## Archivos del Spec

- `requirements.md`: Requerimientos funcionales
- `design.md`: Diseño técnico
- `tasks.md`: Lista de tareas de implementación

## Tests Implementados

### Property-Based Tests (Hypothesis)

| Test | Archivo | Property | Estado | Documentación |
|------|---------|----------|--------|---------------|
| Write-Read Round Trip | `test_iceberg_roundtrip.py` | Property 5 | ✅ Implementado | [Ver docs](./Property-Based%20Testing%20-%20Iceberg%20Round%20Trip.md) |
| ACID Transactions | `test_iceberg_acid.py` | Property 11 | ✅ Implementado | - |
| Time Travel | `test_iceberg_timetravel.py` | Property 12 | ✅ Implementado | - |

### Ejecución de Tests

```bash
# Ejecutar todos los tests de propiedades
pytest glue/tests/property/ -v --hypothesis-show-statistics

# Ejecutar test específico
pytest glue/tests/property/test_iceberg_roundtrip.py -v

# Ejecutar con marker
pytest -m property -v
```
