"""
ETL Pipeline Silver-to-Gold
Orquesta todos los módulos incluyendo cross-cutting y nuevos módulos de mapeo
"""
import json
import time
import logging
import os
from datetime import datetime
from pyspark.sql import SparkSession, DataFrame
from pyspark.sql.functions import current_timestamp

# Nuevos módulos de Fase 5
from modules.schema_mapper import SchemaMapper
from modules.calculated_fields_engine import CalculatedFieldsEngine

# Módulos existentes
from modules.incremental_processor import IncrementalProcessor
from modules.silver_to_gold_aggregator import SilverToGoldAggregator
from modules.denormalization_engine import DenormalizationEngine

# Cross-cutting
from modules.data_quality_validator import DataQualityValidator
from modules.error_handler import ErrorHandler
from modules.data_lineage_tracker import DataLineageTracker


class ETLPipelineGold:
    """
    Orquesta el pipeline Silver-to-Gold con módulos cross-cutting.

    Orden de ejecución actualizado:
    1. SchemaMapper            ← NUEVO: mapea campos Silver→Gold
    2. CalculatedFieldsEngine  ← NUEVO: calcula campos derivados
    3. IncrementalProcessor    ← filtra solo registros nuevos
    4. SilverToGoldAggregator  ← agrega métricas de negocio
    5. DenormalizationEngine   ← joins con dimensiones
    --- Cross-cutting ---
    6. DataQualityValidator    ← valida calidad del output Gold
    7. ErrorHandler            ← maneja registros fallidos
    8. DataLineageTracker      ← registra trazabilidad completa
    """

    def __init__(self, spark: SparkSession, config_path: str):
        self.spark = spark
        self.config = self._load_config(config_path)
        self.logger = self._init_logger()

        # Determinar rutas absolutas para archivos de configuración
        config_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config')
        field_mappings_path = os.path.join(config_dir, 'field_mappings.json')
        redshift_schemas_path = os.path.join(config_dir, 'redshift_schemas.json')

        # Módulos principales (orden actualizado)
        self.modules = [
            SchemaMapper(field_mappings_path),              # NUEVO: Primero mapear campos
            CalculatedFieldsEngine(redshift_schemas_path),  # NUEVO: Luego calcular campos derivados
            IncrementalProcessor(),
            SilverToGoldAggregator(),
            DenormalizationEngine(),
        ]

        # Cross-cutting
        self.quality_validator = DataQualityValidator()
        self.error_handler = ErrorHandler()
        self.lineage_tracker = DataLineageTracker()

    def _load_config(self, config_path: str) -> dict:
        with open(config_path, 'r') as f:
            return json.load(f)

    def _init_logger(self) -> logging.Logger:
        logger = logging.getLogger('ETLPipelineGold')
        logger.setLevel(logging.INFO)
        if not logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(logging.Formatter('[%(levelname)s] %(name)s: %(message)s'))
            logger.addHandler(handler)
        return logger

    def run(self, input_path: str, output_path: str):
        """
        Ejecuta el pipeline completo Silver → Gold.

        Args:
            input_path: Ruta S3 de la tabla Silver
            output_path: Ruta S3 destino Gold
        """
        pipeline_id = f"silver-to-gold-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        job_start = time.time()

        try:
            self.logger.info(f"Iniciando pipeline: {pipeline_id}")

            # 1. Leer Silver
            df = self.spark.read.json(input_path)
            initial_count = df.count()
            self.logger.info(f"Registros en Silver: {initial_count}")

            # 2. Iniciar lineage
            df = self.lineage_tracker.transform(df, self.config)

            # 3. Ejecutar módulos principales con tracking
            for module in self.modules:
                name = module.__class__.__name__
                self.logger.info(f"Ejecutando {name}...")
                df_before = df

                df = module.transform(df, self.config)
                count = df.count()
                self.logger.info(f"  → {count} registros")

                self.lineage_tracker.track_stage(
                    df_before, df, name, pipeline_id, self.config
                )

            # 4. Validar calidad del output Gold
            self.logger.info("Ejecutando DataQualityValidator...")
            df = self.quality_validator.transform(df, self.config)

            # 5. Manejar errores
            self.logger.info("Ejecutando ErrorHandler...")
            df = self.error_handler.transform(df, self.config)

            # 6. Agregar timestamp
            df = df.withColumn("_processing_timestamp", current_timestamp())

            # 7. Escribir a Gold
            final_count = df.count()
            self.logger.info(f"Escribiendo {final_count} registros a Gold: {output_path}")
            df.coalesce(1).write.mode("overwrite").json(output_path)

            # 8. Actualizar metadata incremental
            self.modules[0].update_timestamp(
                self.spark.read.json(input_path),
                self.config
            )

            # 9. Guardar reporte lineage
            self.lineage_tracker.save_lineage_report(self.config, pipeline_id, "success")

            job_duration = time.time() - job_start
            self.logger.info(f"✅ Pipeline Gold completado en {job_duration:.2f}s")

            return final_count

        except Exception as e:
            self.logger.error(f"Pipeline Gold falló: {str(e)}")
            self.lineage_tracker.save_lineage_report(self.config, pipeline_id, "failed")
            self.error_handler.log_pipeline_error("ETLPipelineGold", e, self.config)
            raise
