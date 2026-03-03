# Spec: Pipeline ETL Silver-to-Gold

## Overview

Pipeline ETL que transforma datos limpios desde la capa Silver hacia datos agregados y optimizados para análisis en la capa Gold.

## Documentos del Spec

- **[requirements.md](./requirements.md)**: Requisitos funcionales con historias de usuario y criterios de aceptación
- **[design.md](./design.md)**: Diseño técnico detallado con interfaces, modelos de datos y propiedades de correctness
- **[tasks.md](./tasks.md)**: Lista de tareas de implementación

## Estado del Proyecto

**Fecha de Integración**: 19 de Febrero 2026  
**Desarrollador**: Max  
**Branch Origen**: `origin/bronze-to-silver-max`

### Implementación

- ✅ Todos los módulos implementados
- ✅ Configuración completa
- ✅ Scripts de ejecución para LocalStack
- ⏳ Testing end-to-end pendiente
- ⏳ Validación de datos en Gold pendiente

## Arquitectura

```
S3 Silver → IncrementalProcessor → SilverToGoldAggregator → DenormalizationEngine
    → DataQualityValidator → ErrorHandler → DataLineageTracker → S3 Gold
```

## Módulos Implementados

### Módulos Principales
1. **IncrementalProcessor**: Procesa solo datos nuevos basándose en timestamps
2. **SilverToGoldAggregator**: Calcula agregaciones para métricas de negocio
3. **DenormalizationEngine**: Combina entidades relacionadas en tablas planas

### Módulos Cross-Cutting
4. **DataQualityValidator**: Valida calidad en 4 dimensiones (completeness, validity, consistency, accuracy)
5. **ErrorHandler**: Manejo de errores con DLQ, retry y recovery
6. **DataLineageTracker**: Trazabilidad completa de datos

## Ubicación de Archivos

```
glue/
├── config/
│   └── silver-to-gold-config.json
├── modules/silver_to_gold/
│   ├── incremental_processor.py
│   ├── silver_to_gold_aggregator.py
│   ├── denormalization_engine.py
│   ├── data_quality_validator.py
│   ├── error_handler.py
│   └── data_lineage_tracker.py
└── scripts/
    ├── etl_pipeline_gold.py
    └── run_pipeline_to_gold.py
```

## Cómo Ejecutar

### LocalStack (Testing)

```bash
# Asegurarse de tener datos en Silver
python glue/scripts/run_pipeline_to_gold.py
```

### Producción (AWS Glue)

```python
from etl_pipeline_gold import ETLPipelineGold

spark = SparkSession.builder.appName("silver-to-gold").getOrCreate()
pipeline = ETLPipelineGold(spark, "s3://glue-scripts-bin/config/silver-to-gold-config.json")
pipeline.run(
    input_path="s3://data-lake-silver/ventas_procesadas",
    output_path="s3://data-lake-gold/ventas_agregadas"
)
```

## Configuración

Ver `glue/config/silver-to-gold-config.json` para configuración completa de:
- Procesamiento incremental
- Agregaciones y dimensiones
- Reglas de calidad de datos
- Configuración de DLQ
- Lineage tracking

## Documentación Adicional

- [Integración Silver-to-Gold](../../../Documentacion/INTEGRACION_SILVER_TO_GOLD_MAX.md): Documentación completa de la integración
- [Estado de Módulos](../../../Documentacion/ESTADO_MODULOS_INTEGRACION.md): Estado general del proyecto

## Próximos Pasos

1. Ejecutar testing end-to-end con datos reales
2. Validar agregaciones y métricas calculadas
3. Verificar funcionamiento de DLQ y error handling
4. Documentar resultados de testing
5. Preparar para deployment en producción
