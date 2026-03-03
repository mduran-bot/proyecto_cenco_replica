"""
ETLPipeline Module - Bronze to Silver
Orquesta el pipeline completo incluyendo módulos cross-cutting:
DataQualityValidator, ErrorHandler, DataLineageTracker
"""

import json
import time
import logging
from datetime import datetime
from typing import Dict, List, Any

from pyspark.sql import SparkSession, DataFrame
from pyspark.sql.functions import current_timestamp

from modules.json_flattener import JSONFlattener
from modules.data_cleaner import DataCleaner
from modules.data_normalizer import DataNormalizer
from modules.data_type_converter import DataTypeConverter
from modules.duplicate_detector import DuplicateDetector
from modules.conflict_resolver import ConflictResolver
from modules.data_gap_handler import DataGapHandler
from modules.iceberg_manager import IcebergTableManager
from modules.iceberg_writer import IcebergWriter


class ETLPipeline:
    """
    Orquesta el pipeline Bronze-to-Silver con módulos cross-cutting.

    Orden de ejecución:
    1. JSONFlattener
    2. DataCleaner
    3. DataNormalizer
    4. DataTypeConverter
    5. DuplicateDetector
    6. ConflictResolver
    7. DataGapHandler
    --- Cross-cutting ---
    8. DataQualityValidator  ← valida calidad, puede bloquear pipeline
    9. ErrorHandler          ← separa malos registros, envía a DLQ
    --- Escritura ---
    10. IcebergWriter
    """

    def __init__(self, spark: SparkSession, config_path: str):
        self.spark = spark
        self.config_path = config_path
        self.config = self._load_config(config_path)
        self.logger = self._init_logger()

        # Módulos de transformación
        self.modules = [
            JSONFlattener(),
            DataCleaner(),
            DataNormalizer(),
            DataTypeConverter(),
            DuplicateDetector(),
            ConflictResolver(),
            DataGapHandler(),
        ]

        # Cross-cutting (TODO: implementar estos módulos)
        # self.quality_validator = DataQualityValidator()
        # self.error_handler = ErrorHandler()
        # self.lineage_tracker = DataLineageTracker()

        self.stage_metrics = []

    def _load_config(self, config_path: str) -> Dict[str, Any]:
        try:
            if config_path.startswith("s3://"):
                import boto3
                s3 = boto3.client('s3')
                path_parts = config_path.replace("s3://", "").split("/", 1)
                bucket = path_parts[0]
                key = path_parts[1] if len(path_parts) > 1 else ""
                response = s3.get_object(Bucket=bucket, Key=key)
                config = json.loads(response['Body'].read().decode('utf-8'))
            else:
                with open(config_path, 'r') as f:
                    config = json.load(f)
            return config
        except Exception as e:
            print(f"[WARNING] Config no cargado: {e} — usando defaults")
            return {
                "normalization": {},
                "duplicate_detection": {"key_columns": []},
                "data_gaps": {"critical_columns": [], "default_values": {}, "reject_incomplete": False},
                "type_conversion": {"enabled": True},
                "quality": {},
                "error_handler": {},
                "lineage": {"enabled": False}
            }

    def _init_logger(self) -> logging.Logger:
        logger = logging.getLogger('ETLPipeline')
        logger.setLevel(logging.INFO)
        if not logger.handlers:
            handler = logging.StreamHandler()
            handler.setLevel(logging.INFO)
            handler.setFormatter(logging.Formatter('[%(levelname)s] %(name)s: %(message)s'))
            logger.addHandler(handler)
        return logger

    def run(self, input_path: str, output_database: str, output_table: str):
        """
        Ejecuta el pipeline completo Bronze → Silver.
        """
        job_start = time.time()
        pipeline_id = f"bronze-to-silver-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

        try:
            self.logger.info(f"Iniciando pipeline: {pipeline_id}")
            self.logger.info(f"Input: {input_path} → Output: {output_database}.{output_table}")

            # 1. Leer Bronze
            df = self.spark.read.json(input_path)
            initial_count = df.count()
            self.logger.info(f"Registros leídos de Bronze: {initial_count}")

            # 2. Iniciar lineage tracking
            df = self.lineage_tracker.transform(df, self.config)

            # 3. Ejecutar módulos de transformación con tracking
            for module in self.modules:
                module_name = module.__class__.__name__
                self.logger.info(f"Ejecutando {module_name}...")
                df_before = df
                stage_start = time.time()

                df = module.transform(df, self.config)

                stage_duration = time.time() - stage_start
                record_count = df.count()
                self.logger.info(f"  → {record_count} registros ({stage_duration:.2f}s)")

                # Registrar en lineage
                self.lineage_tracker.track_stage(
                    df_before, df, module_name, pipeline_id, self.config
                )
                self._log_metrics(module_name, record_count, stage_duration)

            # 4. Validar calidad
            self.logger.info("Ejecutando DataQualityValidator...")
            df = self.quality_validator.transform(df, self.config)
            self.logger.info(f"  → {df.count()} registros post-validación")

            # 5. Manejar errores y DLQ
            self.logger.info("Ejecutando ErrorHandler...")
            df = self.error_handler.transform(df, self.config)
            self.logger.info(f"  → {df.count()} registros post-error-handling")

            # 6. Agregar timestamp de procesamiento
            df = df.withColumn("_processing_timestamp", current_timestamp())

            # 7. Escribir a Silver
            final_count = df.count()
            self.logger.info(f"Escribiendo {final_count} registros a Silver...")

            warehouse_path = self.config.get("output", {}).get(
                "warehouse_path", "s3://data-lake-silver/iceberg"
            )
            table_manager = IcebergTableManager("iceberg", warehouse_path)
            writer = IcebergWriter(table_manager)
            records_written = writer.write(df, output_database, output_table, mode="append")

            self.logger.info(f"✅ {records_written} registros escritos en Silver")

            # 8. Guardar reporte de lineage
            self.lineage_tracker.save_lineage_report(self.config, pipeline_id, "success")

            job_duration = time.time() - job_start
            self.logger.info(f"Pipeline completado en {job_duration:.2f}s")

        except Exception as e:
            job_duration = time.time() - job_start
            self.logger.error(f"Pipeline falló: {str(e)}")

            # Registrar error en lineage
            self.lineage_tracker.save_lineage_report(self.config, pipeline_id, "failed")

            # Registrar error crítico
            self.error_handler.log_pipeline_error("ETLPipeline", e, self.config)

            raise

    def _log_metrics(self, stage: str, record_count: int, duration: float):
        self.stage_metrics.append({
            "stage": stage,
            "record_count": record_count,
            "duration_seconds": round(duration, 2),
            "timestamp": datetime.now().isoformat()
        })
