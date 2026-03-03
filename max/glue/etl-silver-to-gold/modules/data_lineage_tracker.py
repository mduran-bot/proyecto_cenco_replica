"""
DataLineageTracker Module

Trazabilidad completa de datos desde Bronze hasta Gold.
Registra en cada etapa:
- Cuántos registros entraron y salieron
- Qué transformaciones se aplicaron
- Timestamp de cada operación
- Hash de los datos para detectar cambios

Permite auditar el origen de cualquier registro en Gold.
"""

import json
import hashlib
import logging
from datetime import datetime
from typing import Dict, Any
from pyspark.sql import DataFrame
from pyspark.sql.functions import (
    col, lit, current_timestamp, concat_ws, md5, sha2
)
import boto3


class DataLineageTracker:
    """
    Registra trazabilidad completa del pipeline ETL.

    Agrega columnas de lineage a cada registro y guarda
    un log de cada etapa en S3 para auditoría.
    """

    def __init__(self):
        self.logger = logging.getLogger('DataLineageTracker')
        self.lineage_log = []  # Log en memoria de todas las etapas

    def transform(self, df: DataFrame, config: dict) -> DataFrame:
        """
        Agrega columnas de trazabilidad al DataFrame.

        Args:
            df: DataFrame a trackear
            config: Configuración con sección 'lineage':
                - pipeline_id: identificador único del pipeline
                - source_path: ruta origen de los datos
                - enabled: true/false
                - track_hash: true/false — agrega hash por registro
                - metadata_bucket: bucket para guardar logs de lineage
                - endpoint_url: para LocalStack

        Returns:
            DataFrame con columnas de lineage agregadas:
                - _lineage_pipeline_id: ID del pipeline
                - _lineage_source: origen de los datos
                - _lineage_timestamp: cuando fue procesado
                - _lineage_record_hash: hash del registro (si track_hash=true)
        """
        lineage_config = config.get("lineage", {})

        if not lineage_config.get("enabled", False):
            self.logger.info("[DataLineageTracker] Lineage desactivado — pasando sin trackear")
            return df

        pipeline_id = lineage_config.get("pipeline_id", f"pipeline_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        source_path = lineage_config.get("source_path", "unknown")
        track_hash = lineage_config.get("track_hash", True)

        # Agregar columnas de lineage
        df = df \
            .withColumn("_lineage_pipeline_id", lit(pipeline_id)) \
            .withColumn("_lineage_source", lit(source_path)) \
            .withColumn("_lineage_timestamp", current_timestamp())

        # Hash por registro para detectar cambios
        if track_hash:
            df = self._add_record_hash(df)

        # Registrar esta etapa en el log
        self._log_stage(
            pipeline_id=pipeline_id,
            stage="DataLineageTracker.transform",
            record_count=df.count(),
            source_path=source_path
        )

        return df

    def track_stage(
        self,
        df_before: DataFrame,
        df_after: DataFrame,
        stage_name: str,
        pipeline_id: str,
        config: dict
    ):
        """
        Registra métricas de una etapa del pipeline para auditoría.

        Llamar DESPUÉS de cada módulo para registrar cuántos
        registros entraron y salieron.

        Args:
            df_before: DataFrame antes de la transformación
            df_after: DataFrame después de la transformación
            stage_name: Nombre del módulo (ej: "DataCleaner")
            pipeline_id: ID único del pipeline
            config: Config del pipeline
        """
        lineage_config = config.get("lineage", {})

        if not lineage_config.get("enabled", False):
            return

        count_before = df_before.count()
        count_after = df_after.count()
        records_dropped = count_before - count_after

        stage_log = {
            "pipeline_id": pipeline_id,
            "stage": stage_name,
            "timestamp": datetime.now().isoformat(),
            "records_in": count_before,
            "records_out": count_after,
            "records_dropped": records_dropped,
            "drop_rate": f"{(records_dropped / count_before * 100):.1f}%" if count_before > 0 else "0%"
        }

        self.lineage_log.append(stage_log)

        self.logger.info(
            f"[Lineage] {stage_name}: "
            f"{count_before} → {count_after} registros "
            f"({records_dropped} eliminados)"
        )

    def save_lineage_report(self, config: dict, pipeline_id: str, status: str = "success"):
        """
        Guarda el reporte completo de lineage en S3.

        Llamar AL FINAL del pipeline para persistir el log completo.

        Args:
            config: Config del pipeline
            pipeline_id: ID único del pipeline
            status: Estado final — 'success' o 'failed'
        """
        lineage_config = config.get("lineage", {})

        if not lineage_config.get("enabled", False):
            return

        metadata_bucket = lineage_config.get("metadata_bucket", "data-lake-metadata")
        endpoint_url = lineage_config.get("endpoint_url", None)

        report = {
            "pipeline_id": pipeline_id,
            "generated_at": datetime.now().isoformat(),
            "status": status,
            "total_stages": len(self.lineage_log),
            "stages": self.lineage_log
        }

        try:
            client_kwargs = {"region_name": "us-east-1"}
            if endpoint_url:
                client_kwargs["endpoint_url"] = endpoint_url
                client_kwargs["aws_access_key_id"] = "test"
                client_kwargs["aws_secret_access_key"] = "test"

            s3 = boto3.client("s3", **client_kwargs)
            key = f"lineage/{pipeline_id}/report.json"

            s3.put_object(
                Bucket=metadata_bucket,
                Key=key,
                Body=json.dumps(report, indent=2)
            )

            self.logger.info(
                f"[DataLineageTracker] ✅ Reporte guardado en "
                f"s3://{metadata_bucket}/{key}"
            )

        except Exception as e:
            # Lineage no debe bloquear el pipeline
            self.logger.error(f"[DataLineageTracker] Error guardando reporte: {str(e)}")

    def _add_record_hash(self, df: DataFrame) -> DataFrame:
        """
        Agrega hash MD5 por registro para detectar cambios entre ejecuciones.
        Excluye columnas de metadata (_processing_timestamp, _lineage_*).
        """
        # Solo hashear columnas de negocio, no las de metadata
        business_cols = [
            c for c in df.columns
            if not c.startswith("_")
        ]

        if not business_cols:
            return df.withColumn("_lineage_record_hash", lit("no_business_cols"))

        # Concatenar todos los valores y hashear
        hash_expr = md5(concat_ws("|", *[col(c).cast("string") for c in business_cols]))

        return df.withColumn("_lineage_record_hash", hash_expr)

    def _log_stage(self, pipeline_id: str, stage: str, record_count: int, source_path: str):
        """Agrega entrada al log en memoria."""
        self.lineage_log.append({
            "pipeline_id": pipeline_id,
            "stage": stage,
            "timestamp": datetime.now().isoformat(),
            "records_out": record_count,
            "source": source_path
        })
