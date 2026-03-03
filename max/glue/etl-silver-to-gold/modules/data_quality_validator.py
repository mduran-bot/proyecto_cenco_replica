"""
DataQualityValidator Module

Valida la calidad de datos en 6 dimensiones:
- Completeness: campos críticos no nulos
- Validity: formatos y rangos correctos
- Consistency: valores coherentes entre columnas
- Accuracy: valores dentro de rangos esperados de negocio
- Uniqueness: claves primarias únicas (PK)
- Referential Integrity: claves foráneas válidas (FK) - opcional

Si quality_gate=true en config, bloquea el pipeline si no se alcanza
el umbral mínimo de calidad configurado.

Lee reglas de validación desde redshift_schemas.json para aplicar
validaciones específicas por tabla.
"""

from pyspark.sql import DataFrame
from pyspark.sql.functions import col, when, lit, count, sum as spark_sum, avg, countDistinct
from pyspark.sql.types import BooleanType
from typing import Dict, Any, List
import logging
import json
import re


class DataQualityValidator:
    """
    Valida calidad de datos y opcionalmente bloquea el pipeline
    si no se alcanza el umbral mínimo configurado.

    Agrega columnas al DataFrame:
    - _quality_completeness: porcentaje de campos críticos completos
    - _quality_valid: boolean si el registro pasa todas las validaciones
    - _quality_issues: string con lista de problemas encontrados
    """

    def __init__(self, redshift_schemas_path: str = None):
        """
        Inicializa el DataQualityValidator.
        
        Args:
            redshift_schemas_path: Ruta al archivo redshift_schemas.json
                                  Si es None, usa ruta por defecto
        """
        self.logger = logging.getLogger('DataQualityValidator')
        self.redshift_schemas_path = redshift_schemas_path or "max/src/config/redshift_schemas.json"
        self.schemas = self._load_schemas()
    
    def _load_schemas(self) -> Dict:
        """Carga esquemas de Redshift desde JSON."""
        try:
            with open(self.redshift_schemas_path, 'r', encoding='utf-8') as f:
                schemas = json.load(f)
            self.logger.info(f"[DataQualityValidator] Cargados esquemas para {len(schemas.get('tables', {}))} tablas")
            return schemas.get('tables', {})
        except FileNotFoundError:
            self.logger.warning(f"[DataQualityValidator] Archivo no encontrado: {self.redshift_schemas_path}")
            return {}
        except json.JSONDecodeError as e:
            self.logger.error(f"[DataQualityValidator] Error parseando JSON: {e}")
            return {}

    def transform(self, df: DataFrame, config: dict) -> DataFrame:
        """
        Valida calidad del DataFrame según configuración.

        Args:
            df: DataFrame a validar
            config: Configuración con sección 'quality':
                - gold_table: nombre de la tabla Gold (para leer esquema)
                - critical_columns: columnas que no deben ser null (opcional, se lee de esquema)
                - valid_values: {columna: [valores_permitidos]}
                - numeric_ranges: {columna: {min: x, max: y}} (opcional, se lee de esquema)
                - consistency_rules: [{col_a: valor, col_b: valor}]
                - validate_pk_uniqueness: true/false (default: true)
                - validate_fk_integrity: true/false (default: false, costoso)
                - format_validations: {columna: regex_pattern}
                - quality_gate: true/false — bloquea si calidad < threshold
                - threshold: 0.0-1.0 — porcentaje mínimo de registros válidos

        Returns:
            DataFrame con columnas de calidad agregadas

        Raises:
            ValueError: Si quality_gate=true y calidad < threshold
        """
        quality_config = config.get("quality", {})
        gold_table = config.get("gold_table")

        # Si hay gold_table, cargar validaciones desde esquema
        if gold_table and gold_table in self.schemas:
            quality_config = self._merge_schema_validations(quality_config, gold_table)

        if not quality_config:
            self.logger.warning("[DataQualityValidator] No hay config de calidad — pasando sin validar")
            return df.withColumn("_quality_valid", lit(True)) \
                     .withColumn("_quality_issues", lit(""))

        critical_columns = quality_config.get("critical_columns", [])
        valid_values = quality_config.get("valid_values", {})
        numeric_ranges = quality_config.get("numeric_ranges", {})
        consistency_rules = quality_config.get("consistency_rules", [])
        format_validations = quality_config.get("format_validations", {})
        validate_pk = quality_config.get("validate_pk_uniqueness", True)
        validate_fk = quality_config.get("validate_fk_integrity", False)
        quality_gate = quality_config.get("quality_gate", False)
        threshold = quality_config.get("threshold", 0.8)

        # Aplicar validaciones
        df = self._validate_completeness(df, critical_columns)
        df = self._validate_validity(df, valid_values)
        df = self._validate_numeric_ranges(df, numeric_ranges)
        df = self._validate_consistency(df, consistency_rules)
        df = self._validate_formats(df, format_validations)
        
        # Validaciones a nivel de dataset (no por registro)
        if validate_pk:
            self._validate_pk_uniqueness(df, quality_config.get("primary_keys", []))
        
        if validate_fk:
            # FK validation requiere acceso a tablas padre (no implementado aquí)
            self.logger.info("[DataQualityValidator] FK validation solicitada pero no implementada en esta versión")

        # Consolidar resultado final por registro
        df = self._consolidate_quality(df)

        # Quality gate — bloquea el pipeline si calidad < threshold
        if quality_gate:
            self._check_quality_gate(df, threshold)

        return df
    
    def _merge_schema_validations(self, quality_config: dict, gold_table: str) -> dict:
        """
        Combina configuración manual con validaciones del esquema.
        
        Args:
            quality_config: Configuración manual de calidad
            gold_table: Nombre de la tabla Gold
        
        Returns:
            Configuración combinada
        """
        table_schema = self.schemas.get(gold_table, {})
        fields = table_schema.get("fields", {})
        
        # Extraer campos no nullable como críticos
        if not quality_config.get("critical_columns"):
            critical_columns = [
                field_name for field_name, field_config in fields.items()
                if not field_config.get("nullable", True)
            ]
            quality_config["critical_columns"] = critical_columns
        
        # Extraer rangos numéricos implícitos
        if not quality_config.get("numeric_ranges"):
            numeric_ranges = {}
            for field_name, field_config in fields.items():
                field_type = field_config.get("type", "")
                # Rangos implícitos para tipos comunes
                if "SMALLINT" in field_type:
                    numeric_ranges[field_name] = {"min": 0, "max": 32767}
                elif "INT" in field_type and "BIG" not in field_type:
                    numeric_ranges[field_name] = {"min": 0, "max": 2147483647}
                # Rangos específicos de negocio
                elif "quantity" in field_name.lower() or "stock" in field_name.lower():
                    numeric_ranges[field_name] = {"min": 0}
                elif "price" in field_name.lower() or "amount" in field_name.lower():
                    numeric_ranges[field_name] = {"min": 0}
                elif "lat" in field_name.lower():
                    numeric_ranges[field_name] = {"min": -90, "max": 90}
                elif "lng" in field_name.lower() or "lon" in field_name.lower():
                    numeric_ranges[field_name] = {"min": -180, "max": 180}
            
            quality_config["numeric_ranges"] = numeric_ranges
        
        # Extraer claves primarias
        if not quality_config.get("primary_keys"):
            primary_keys = [
                field_name for field_name, field_config in fields.items()
                if field_config.get("primary_key", False)
            ]
            quality_config["primary_keys"] = primary_keys
        
        # Extraer validaciones de formato
        if not quality_config.get("format_validations"):
            format_validations = {}
            for field_name, field_config in fields.items():
                # Email validation
                if "email" in field_name.lower():
                    format_validations[field_name] = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
                # Phone validation (solo dígitos y caracteres comunes)
                elif "phone" in field_name.lower():
                    format_validations[field_name] = r"^[\d\s\-\+\(\)]+$"
            
            quality_config["format_validations"] = format_validations
        
        return quality_config

    def _validate_completeness(self, df: DataFrame, critical_columns: list) -> DataFrame:
        """Marca registros con nulls en columnas críticas."""
        if not critical_columns:
            return df.withColumn("_completeness_ok", lit(True))

        # Solo validar columnas que existen en el DataFrame
        existing = [c for c in critical_columns if c in df.columns]
        missing_cols = [c for c in critical_columns if c not in df.columns]

        if missing_cols:
            self.logger.warning(f"[Completeness] Columnas no encontradas: {missing_cols}")

        if not existing:
            return df.withColumn("_completeness_ok", lit(True))

        # Un registro pasa completeness si NINGUNA columna crítica es null
        completeness_expr = lit(True)
        for col_name in existing:
            completeness_expr = completeness_expr & col(col_name).isNotNull()

        return df.withColumn("_completeness_ok", completeness_expr)

    def _validate_validity(self, df: DataFrame, valid_values: dict) -> DataFrame:
        """Valida que columnas tengan solo valores permitidos."""
        if not valid_values:
            return df.withColumn("_validity_ok", lit(True))

        validity_expr = lit(True)
        for col_name, allowed in valid_values.items():
            if col_name not in df.columns:
                self.logger.warning(f"[Validity] Columna '{col_name}' no existe")
                continue
            # Nulos se permiten — solo validar si no es null
            col_valid = col(col_name).isNull() | col(col_name).isin(allowed)
            validity_expr = validity_expr & col_valid

        return df.withColumn("_validity_ok", validity_expr)

    def _validate_numeric_ranges(self, df: DataFrame, numeric_ranges: dict) -> DataFrame:
        """Valida que columnas numéricas estén dentro de rangos esperados."""
        if not numeric_ranges:
            return df.withColumn("_range_ok", lit(True))

        range_expr = lit(True)
        for col_name, bounds in numeric_ranges.items():
            if col_name not in df.columns:
                self.logger.warning(f"[Range] Columna '{col_name}' no existe")
                continue

            min_val = bounds.get("min")
            max_val = bounds.get("max")

            col_expr = lit(True)
            if min_val is not None:
                col_expr = col_expr & (col(col_name).isNull() | (col(col_name) >= min_val))
            if max_val is not None:
                col_expr = col_expr & (col(col_name).isNull() | (col(col_name) <= max_val))

            range_expr = range_expr & col_expr

        return df.withColumn("_range_ok", range_expr)

    def _validate_consistency(self, df: DataFrame, consistency_rules: list) -> DataFrame:
        """
        Valida reglas de consistencia entre columnas.
        Ejemplo: si estado='completado' entonces monto no puede ser null.
        """
        if not consistency_rules:
            return df.withColumn("_consistency_ok", lit(True))

        consistency_expr = lit(True)
        for rule in consistency_rules:
            when_col = rule.get("when_column")
            when_val = rule.get("when_value")
            then_col = rule.get("then_column")
            then_not_null = rule.get("then_not_null", False)

            if not all([when_col, when_val, then_col]):
                continue
            if when_col not in df.columns or then_col not in df.columns:
                continue

            if then_not_null:
                # Si when_col == when_val → then_col no puede ser null
                rule_expr = (col(when_col) != when_val) | col(then_col).isNotNull()
                consistency_expr = consistency_expr & rule_expr

        return df.withColumn("_consistency_ok", consistency_expr)

    def _validate_formats(self, df: DataFrame, format_validations: dict) -> DataFrame:
        """
        Valida que campos de texto cumplan con formatos esperados (regex).
        Ejemplo: email con @, phone con dígitos.
        """
        if not format_validations:
            return df.withColumn("_format_ok", lit(True))

        format_expr = lit(True)
        for col_name, pattern in format_validations.items():
            if col_name not in df.columns:
                self.logger.warning(f"[Format] Columna '{col_name}' no existe")
                continue
            
            # Nulos se permiten — solo validar si no es null
            try:
                col_valid = col(col_name).isNull() | col(col_name).rlike(pattern)
                format_expr = format_expr & col_valid
            except Exception as e:
                self.logger.error(f"[Format] Error validando patrón para '{col_name}': {e}")
                continue

        return df.withColumn("_format_ok", format_expr)
    
    def _validate_pk_uniqueness(self, df: DataFrame, primary_keys: List[str]) -> None:
        """
        Valida que las claves primarias sean únicas.
        Esta es una validación a nivel de dataset, no por registro.
        
        Args:
            df: DataFrame a validar
            primary_keys: Lista de columnas que forman la clave primaria
        
        Raises:
            Warning si hay duplicados (no bloquea el pipeline)
        """
        if not primary_keys:
            self.logger.debug("[PK Uniqueness] No hay claves primarias definidas")
            return
        
        # Verificar que las columnas existan
        existing_pks = [pk for pk in primary_keys if pk in df.columns]
        if not existing_pks:
            self.logger.warning(f"[PK Uniqueness] Ninguna columna PK encontrada: {primary_keys}")
            return
        
        total_count = df.count()
        distinct_count = df.select(existing_pks).distinct().count()
        
        if total_count != distinct_count:
            duplicates_count = total_count - distinct_count
            self.logger.warning(
                f"[PK Uniqueness] ⚠️ Encontrados {duplicates_count} registros duplicados "
                f"en PK {existing_pks}. Total: {total_count}, Únicos: {distinct_count}"
            )
            
            # Opcional: mostrar algunos duplicados para debugging
            duplicates = df.groupBy(existing_pks).count().filter("count > 1").limit(5)
            if duplicates.count() > 0:
                self.logger.warning("[PK Uniqueness] Ejemplos de PKs duplicadas:")
                for row in duplicates.collect():
                    self.logger.warning(f"  {dict(row.asDict())}")
        else:
            self.logger.info(f"[PK Uniqueness] ✅ Todas las PKs son únicas ({total_count} registros)")

    def _consolidate_quality(self, df: DataFrame) -> DataFrame:
        """
        Consolida todas las validaciones en _quality_valid y _quality_issues.
        Elimina columnas intermedias.
        """
        quality_cols = ["_completeness_ok", "_validity_ok", "_range_ok", "_consistency_ok", "_format_ok"]
        existing_quality_cols = [c for c in quality_cols if c in df.columns]

        # Un registro es válido si pasa TODAS las validaciones
        valid_expr = lit(True)
        for qcol in existing_quality_cols:
            valid_expr = valid_expr & col(qcol)

        df = df.withColumn("_quality_valid", valid_expr)

        # Construir string de issues para debugging
        issues_expr = lit("")
        if "_completeness_ok" in df.columns:
            issues_expr = when(~col("_completeness_ok"),
                               issues_expr + "COMPLETENESS_FAIL;").otherwise(issues_expr)
        if "_validity_ok" in df.columns:
            issues_expr = when(~col("_validity_ok"),
                               issues_expr + "VALIDITY_FAIL;").otherwise(issues_expr)
        if "_range_ok" in df.columns:
            issues_expr = when(~col("_range_ok"),
                               issues_expr + "RANGE_FAIL;").otherwise(issues_expr)
        if "_consistency_ok" in df.columns:
            issues_expr = when(~col("_consistency_ok"),
                               issues_expr + "CONSISTENCY_FAIL;").otherwise(issues_expr)
        if "_format_ok" in df.columns:
            issues_expr = when(~col("_format_ok"),
                               issues_expr + "FORMAT_FAIL;").otherwise(issues_expr)

        df = df.withColumn("_quality_issues", issues_expr)

        # Limpiar columnas intermedias
        df = df.drop(*existing_quality_cols)

        return df

    def _check_quality_gate(self, df: DataFrame, threshold: float):
        """
        Verifica si el porcentaje de registros válidos supera el umbral.
        Lanza ValueError si no se alcanza — bloqueando el pipeline.
        """
        total = df.count()
        if total == 0:
            raise ValueError("[DataQualityValidator] Quality Gate: DataFrame vacío")

        valid_count = df.filter(col("_quality_valid") == True).count()
        quality_score = valid_count / total

        self.logger.info(
            f"[Quality Gate] {valid_count}/{total} registros válidos "
            f"({quality_score:.1%}) — umbral: {threshold:.1%}"
        )

        if quality_score < threshold:
            raise ValueError(
                f"[DataQualityValidator] Quality Gate BLOQUEADO: "
                f"{quality_score:.1%} < umbral {threshold:.1%}. "
                f"Registros inválidos: {total - valid_count}/{total}. "
                f"Revisa columna '_quality_issues' para detalles."
            )

        self.logger.info(f"[Quality Gate] ✅ Calidad aprobada: {quality_score:.1%}")
