"""
ErrorHandler Module

Maneja errores del pipeline con:
- Dead Letter Queue (DLQ): registros fallidos se guardan en S3
- Retry con exponential backoff: reintenta operaciones fallidas
- Recovery: separa registros problemáticos para no bloquear el pipeline
"""

import json
import time
import logging
from datetime import datetime
from typing import Callable, Any
from pyspark.sql import DataFrame
from pyspark.sql.functions import col, lit, current_timestamp, when
import boto3


class ErrorHandler:
    """
    Maneja errores en el pipeline ETL con DLQ, retry y recovery.

    En vez de fallar todo el pipeline por registros problemáticos,
    los separa en una Dead Letter Queue para revisión posterior.
    """

    def __init__(self):
        self.logger = logging.getLogger('ErrorHandler')
        self.max_retries = 3
        self.base_delay = 2  # segundos

    def transform(self, df: DataFrame, config: dict) -> DataFrame:
        """
        Aplica manejo de errores al DataFrame.

        Separa registros con problemas de calidad conocidos
        y los envía a DLQ si está configurado.

        Args:
            df: DataFrame con columna _quality_valid (del DataQualityValidator)
            config: Configuración con sección 'error_handler':
                - dlq_enabled: true/false
                - dlq_bucket: bucket S3 para DLQ
                - dlq_prefix: prefijo S3 para archivos DLQ
                - recovery_mode: 'exclude' (excluye malos) o 'flag' (los marca)

        Returns:
            DataFrame limpio según recovery_mode configurado
        """
        error_config = config.get("error_handler", {})

        if not error_config:
            self.logger.warning("[ErrorHandler] No hay config — pasando sin filtrar errores")
            return df

        dlq_enabled = error_config.get("dlq_enabled", False)
        recovery_mode = error_config.get("recovery_mode", "flag")

        # Verificar si viene del DataQualityValidator
        has_quality_col = "_quality_valid" in df.columns

        if not has_quality_col:
            self.logger.warning(
                "[ErrorHandler] No se encontró '_quality_valid'. "
                "Ejecutar DataQualityValidator antes que ErrorHandler."
            )
            return df.withColumn("_error_handled", lit(False))

        # Separar registros buenos y malos
        df_good = df.filter(col("_quality_valid") == True)
        df_bad = df.filter(col("_quality_valid") == False)

        bad_count = df_bad.count()
        good_count = df_good.count()

        self.logger.info(f"[ErrorHandler] Registros válidos: {good_count} | Fallidos: {bad_count}")

        # Enviar malos a DLQ si está habilitado
        if dlq_enabled and bad_count > 0:
            self._send_to_dlq(df_bad, error_config)

        # Aplicar recovery según modo configurado
        if recovery_mode == "exclude":
            # Excluir registros malos del pipeline
            self.logger.info(f"[ErrorHandler] Modo EXCLUDE — eliminando {bad_count} registros fallidos")
            result_df = df_good.withColumn("_error_handled", lit(True))
        else:
            # Modo FLAG — mantener todos pero marcados
            self.logger.info(f"[ErrorHandler] Modo FLAG — marcando {bad_count} registros fallidos")
            result_df = df.withColumn(
                "_error_handled",
                when(col("_quality_valid") == False, lit(True)).otherwise(lit(False))
            )

        return result_df

    def retry_with_backoff(self, operation: Callable, operation_name: str = "operación") -> Any:
        """
        Ejecuta una operación con retry y exponential backoff.

        Args:
            operation: Función a ejecutar (sin argumentos)
            operation_name: Nombre para logging

        Returns:
            Resultado de la operación si fue exitosa

        Raises:
            RuntimeError: Si todos los reintentos fallan
        """
        last_exception = None

        for attempt in range(1, self.max_retries + 1):
            try:
                self.logger.info(f"[ErrorHandler] {operation_name} — intento {attempt}/{self.max_retries}")
                result = operation()
                self.logger.info(f"[ErrorHandler] {operation_name} — exitoso en intento {attempt}")
                return result

            except Exception as e:
                last_exception = e
                delay = self.base_delay ** attempt  # 2s, 4s, 8s

                if attempt < self.max_retries:
                    self.logger.warning(
                        f"[ErrorHandler] {operation_name} falló (intento {attempt}): {str(e)}. "
                        f"Reintentando en {delay}s..."
                    )
                    time.sleep(delay)
                else:
                    self.logger.error(
                        f"[ErrorHandler] {operation_name} falló después de {self.max_retries} intentos"
                    )

        raise RuntimeError(
            f"[ErrorHandler] '{operation_name}' falló después de {self.max_retries} intentos. "
            f"Último error: {str(last_exception)}"
        )

    def _send_to_dlq(self, df_bad: DataFrame, error_config: dict):
        """
        Envía registros fallidos a Dead Letter Queue en S3.

        Args:
            df_bad: DataFrame con registros fallidos
            error_config: Config del error handler
        """
        dlq_bucket = error_config.get("dlq_bucket", "data-lake-dlq")
        dlq_prefix = error_config.get("dlq_prefix", "failed-records")
        endpoint_url = error_config.get("endpoint_url", None)  # para LocalStack

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        dlq_path = f"s3a://{dlq_bucket}/{dlq_prefix}/{timestamp}"

        try:
            self.logger.info(f"[ErrorHandler] Enviando {df_bad.count()} registros a DLQ: {dlq_path}")

            # Agregar metadata de DLQ
            df_bad_with_meta = df_bad \
                .withColumn("_dlq_timestamp", current_timestamp()) \
                .withColumn("_dlq_reason", col("_quality_issues"))

            df_bad_with_meta.coalesce(1).write.mode("append").json(dlq_path)

            self.logger.info(f"[ErrorHandler] ✅ Registros enviados a DLQ exitosamente")

        except Exception as e:
            # DLQ no debe bloquear el pipeline principal
            self.logger.error(f"[ErrorHandler] Error enviando a DLQ: {str(e)}")
            self.logger.error("[ErrorHandler] Continuando pipeline sin DLQ")

    def log_pipeline_error(self, stage: str, error: Exception, config: dict):
        """
        Registra un error crítico del pipeline en S3 para auditoría.

        Args:
            stage: Nombre del módulo donde ocurrió el error
            error: La excepción capturada
            config: Config del pipeline
        """
        error_config = config.get("error_handler", {})
        dlq_bucket = error_config.get("dlq_bucket", "data-lake-dlq")
        endpoint_url = error_config.get("endpoint_url", None)

        error_record = {
            "timestamp": datetime.now().isoformat(),
            "stage": stage,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "pipeline": "etl-pipeline"
        }

        try:
            client_kwargs = {"region_name": "us-east-1"}
            if endpoint_url:
                client_kwargs["endpoint_url"] = endpoint_url
                client_kwargs["aws_access_key_id"] = "test"
                client_kwargs["aws_secret_access_key"] = "test"

            s3 = boto3.client("s3", **client_kwargs)
            key = f"pipeline-errors/{datetime.now().strftime('%Y%m%d_%H%M%S')}_{stage}.json"

            s3.put_object(
                Bucket=dlq_bucket,
                Key=key,
                Body=json.dumps(error_record)
            )
            self.logger.info(f"[ErrorHandler] Error registrado en s3://{dlq_bucket}/{key}")

        except Exception as log_error:
            # Nunca bloquear por fallo de logging
            self.logger.error(f"[ErrorHandler] No se pudo registrar el error: {str(log_error)}")
