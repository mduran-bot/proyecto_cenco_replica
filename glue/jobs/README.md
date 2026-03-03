# Glue Jobs

Este directorio contiene los trabajos principales de AWS Glue para el pipeline de transformación de datos.

## Estructura

```
glue/
├── jobs/                          # Glue jobs principales
│   ├── bronze_to_silver_job.py   # Job Bronze → Silver
│   └── silver_to_gold_job.py     # Job Silver → Gold
├── modules/                       # Módulos reutilizables
│   ├── data_type_converter.py    # Conversión de tipos
│   ├── data_normalizer.py        # Normalización de datos
│   ├── data_gap_handler.py       # Manejo de data gaps
│   ├── iceberg_manager.py        # Gestión de tablas Iceberg (Task 5)
│   ├── schema_evolution.py       # Evolución de esquemas (Task 11)
│   └── ...
├── tests/                         # Tests unitarios y de propiedades
│   ├── unit/
│   └── property/
└── schemas/                       # Definiciones de esquemas
    ├── bronze_schemas.py
    ├── silver_schemas.py
    └── gold_schemas.py
```

## Convenciones

- Todos los módulos usan PySpark
- Tests con Hypothesis para property-based testing
- Seguir PEP 8 para estilo de código
