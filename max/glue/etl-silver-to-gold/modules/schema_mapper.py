"""
SchemaMapper Module

Mapea campos desde Silver layer a Gold layer aplicando:
- Selección de campos específicos (ej: 43 de 91 campos para wms_orders)
- Renombrado de campos (dateCreated → date_created)
- Aplanamiento de JSON anidados (totals.items.amount → items_amount)
- Transformaciones de tipos de datos

Lee configuración desde field_mappings.json para determinar qué campos
mapear y cómo transformarlos.
"""

from pyspark.sql import DataFrame
from pyspark.sql.functions import (
    col, lit, when, concat, coalesce, 
    from_unixtime, to_timestamp, element_at, split
)
from pyspark.sql.types import (
    StringType, IntegerType, LongType, DoubleType, 
    BooleanType, TimestampType, DecimalType
)
from typing import Dict, Any, List
import logging
import json


class SchemaMapper:
    """
    Mapea campos desde Silver a Gold aplicando transformaciones
    según configuración en field_mappings.json.
    
    Transformaciones soportadas:
    - direct: copia directa del campo
    - flatten: extrae campo de objeto anidado (ej: addresses[0].city)
    - array_first: toma primer elemento de array
    - explode_array: explota array en múltiples registros (para tablas hijas)
    - parent_id: usa ID del registro padre
    - timestamp_to_iso8601: convierte Unix timestamp a ISO 8601
    - tinyint_to_boolean: convierte 0/1 a false/true
    - bigint_to_string: convierte BIGINT a VARCHAR
    - decimal_to_numeric: preserva precisión decimal
    - status_mapping: mapea códigos de estado a strings
    - calculate: campo calculado (manejado por CalculatedFieldsEngine)
    """

    def __init__(self, field_mappings_path: str = None):
        """
        Inicializa el SchemaMapper.
        
        Args:
            field_mappings_path: Ruta al archivo field_mappings.json
                                Si es None, usa ruta por defecto
        """
        self.logger = logging.getLogger('SchemaMapper')
        self.field_mappings_path = field_mappings_path or "max/src/config/field_mappings.json"
        self.field_mappings = self._load_field_mappings()

    def _load_field_mappings(self) -> Dict:
        """Carga configuración de mapeo de campos desde JSON."""
        try:
            with open(self.field_mappings_path, 'r', encoding='utf-8') as f:
                mappings = json.load(f)
            self.logger.info(f"[SchemaMapper] Cargados mapeos para {len(mappings.get('mappings', {}))} tablas")
            return mappings.get('mappings', {})
        except FileNotFoundError:
            self.logger.error(f"[SchemaMapper] Archivo no encontrado: {self.field_mappings_path}")
            return {}
        except json.JSONDecodeError as e:
            self.logger.error(f"[SchemaMapper] Error parseando JSON: {e}")
            return {}

    def transform(self, df: DataFrame, config: dict) -> DataFrame:
        """
        Aplica mapeo de esquema al DataFrame.
        
        Args:
            df: DataFrame de Silver layer
            config: Configuración con:
                - gold_table: nombre de la tabla Gold destino
                - source_entity: entidad fuente (opcional, se infiere de gold_table)
        
        Returns:
            DataFrame con esquema mapeado a Gold
        """
        gold_table = config.get("gold_table")
        if not gold_table:
            self.logger.error("[SchemaMapper] Falta 'gold_table' en config")
            return df

        if gold_table not in self.field_mappings:
            self.logger.warning(f"[SchemaMapper] No hay mapeo para tabla '{gold_table}' — pasando sin cambios")
            return df

        table_mapping = self.field_mappings[gold_table]
        fields_config = table_mapping.get("fields", {})
        
        self.logger.info(f"[SchemaMapper] Mapeando {len(fields_config)} campos para tabla '{gold_table}'")

        # Aplicar transformaciones campo por campo
        mapped_df = self._apply_field_mappings(df, fields_config)
        
        # Seleccionar solo los campos mapeados (eliminar campos no necesarios)
        target_columns = list(fields_config.keys())
        existing_columns = [c for c in target_columns if c in mapped_df.columns]
        
        if len(existing_columns) < len(target_columns):
            missing = set(target_columns) - set(existing_columns)
            self.logger.warning(f"[SchemaMapper] Campos no mapeados: {missing}")
        
        mapped_df = mapped_df.select(*existing_columns)
        
        self.logger.info(f"[SchemaMapper] ✅ Mapeados {len(existing_columns)} campos para '{gold_table}'")
        return mapped_df

    def _apply_field_mappings(self, df: DataFrame, fields_config: Dict) -> DataFrame:
        """
        Aplica transformaciones a cada campo según configuración.
        
        Args:
            df: DataFrame fuente
            fields_config: Diccionario con configuración de campos
        
        Returns:
            DataFrame con campos transformados
        """
        result_df = df
        
        for target_field, field_config in fields_config.items():
            source = field_config.get("source")
            transformation = field_config.get("transformation", "direct")
            
            # Saltar campos calculados (manejados por CalculatedFieldsEngine)
            if source == "calculated":
                self.logger.debug(f"[SchemaMapper] Saltando campo calculado: {target_field}")
                continue
            
            # Aplicar transformación según tipo
            try:
                if transformation == "direct":
                    result_df = self._transform_direct(result_df, source, target_field)
                
                elif transformation == "flatten":
                    result_df = self._transform_flatten(result_df, source, target_field)
                
                elif transformation == "array_first":
                    result_df = self._transform_array_first(result_df, source, target_field)
                
                elif transformation == "timestamp_to_iso8601":
                    result_df = self._transform_timestamp(result_df, source, target_field)
                
                elif transformation == "tinyint_to_boolean":
                    result_df = self._transform_boolean(result_df, source, target_field)
                
                elif transformation == "bigint_to_string":
                    result_df = self._transform_to_string(result_df, source, target_field)
                
                elif transformation == "decimal_to_numeric":
                    result_df = self._transform_decimal(result_df, source, target_field)
                
                elif transformation == "status_mapping":
                    result_df = self._transform_status(result_df, source, target_field)
                
                elif transformation == "parent_id":
                    result_df = self._transform_parent_id(result_df, source, target_field)
                
                elif transformation == "explode_array":
                    # Explode arrays se maneja en un paso separado (para tablas hijas)
                    self.logger.debug(f"[SchemaMapper] Explode array para {target_field} requiere procesamiento especial")
                    continue
                
                else:
                    self.logger.warning(f"[SchemaMapper] Transformación desconocida '{transformation}' para {target_field}")
                    
            except Exception as e:
                self.logger.error(f"[SchemaMapper] Error mapeando {target_field}: {e}")
                # Agregar columna NULL en caso de error
                result_df = result_df.withColumn(target_field, lit(None))
        
        return result_df

    def _transform_direct(self, df: DataFrame, source: str, target: str) -> DataFrame:
        """Copia directa del campo, renombrándolo si es necesario."""
        if source in df.columns:
            if source != target:
                return df.withColumn(target, col(source))
            return df
        else:
            self.logger.warning(f"[SchemaMapper] Campo fuente '{source}' no existe — asignando NULL a '{target}'")
            return df.withColumn(target, lit(None))

    def _transform_flatten(self, df: DataFrame, source: str, target: str) -> DataFrame:
        """
        Aplana campos anidados usando notación de punto.
        Ejemplo: 'addresses[0].city' o 'totals.items.amount'
        """
        # Manejar arrays con índice [0]
        if '[0]' in source:
            # Ejemplo: addresses[0].city → addresses.city con element_at
            parts = source.replace('[0].', '.').split('.')
            if parts[0] in df.columns:
                # Acceder al primer elemento del array y luego al campo
                expr = col(parts[0])
                if len(parts) > 1:
                    # Si es array, tomar primer elemento
                    expr = element_at(expr, 1)
                    # Luego acceder a campos anidados
                    for part in parts[1:]:
                        expr = expr.getField(part)
                return df.withColumn(target, expr)
        
        # Manejar objetos anidados simples
        elif '.' in source:
            parts = source.split('.')
            if parts[0] in df.columns:
                expr = col(parts[0])
                for part in parts[1:]:
                    expr = expr.getField(part)
                return df.withColumn(target, expr)
        
        # Si no es anidado, tratar como directo
        return self._transform_direct(df, source, target)

    def _transform_array_first(self, df: DataFrame, source: str, target: str) -> DataFrame:
        """
        Toma el primer elemento de un array.
        Ejemplo: 'addresses[0].city' → toma addresses[0] y luego .city
        """
        # Similar a flatten pero específicamente para arrays
        if '[0]' in source or '[]' in source:
            source_clean = source.replace('[0]', '').replace('[]', '')
            parts = source_clean.split('.')
            
            if parts[0] in df.columns:
                # Tomar primer elemento del array
                expr = element_at(col(parts[0]), 1)
                
                # Si hay campos anidados después del array
                if len(parts) > 1:
                    for part in parts[1:]:
                        expr = expr.getField(part)
                
                return df.withColumn(target, expr)
        
        return self._transform_direct(df, source, target)

    def _transform_timestamp(self, df: DataFrame, source: str, target: str) -> DataFrame:
        """
        Convierte Unix timestamp (BIGINT) a TIMESTAMP ISO 8601.
        Ejemplo: 1706025600 → 2024-01-23T12:00:00Z
        """
        if source in df.columns:
            # from_unixtime convierte Unix timestamp a timestamp
            timestamp_expr = from_unixtime(col(source))
            return df.withColumn(target, to_timestamp(timestamp_expr))
        else:
            return df.withColumn(target, lit(None).cast(TimestampType()))

    def _transform_boolean(self, df: DataFrame, source: str, target: str) -> DataFrame:
        """
        Convierte TINYINT(1) a BOOLEAN.
        0 → false, 1 → true, NULL → NULL
        """
        if source in df.columns:
            bool_expr = when(col(source) == 1, lit(True)) \
                       .when(col(source) == 0, lit(False)) \
                       .otherwise(lit(None))
            return df.withColumn(target, bool_expr.cast(BooleanType()))
        else:
            return df.withColumn(target, lit(None).cast(BooleanType()))

    def _transform_to_string(self, df: DataFrame, source: str, target: str) -> DataFrame:
        """Convierte BIGINT o INT a VARCHAR."""
        if source in df.columns:
            return df.withColumn(target, col(source).cast(StringType()))
        else:
            return df.withColumn(target, lit(None).cast(StringType()))

    def _transform_decimal(self, df: DataFrame, source: str, target: str) -> DataFrame:
        """
        Preserva precisión decimal para coordenadas.
        DECIMAL(12,9) → NUMERIC(12,9)
        """
        if source in df.columns:
            # Mantener como decimal con precisión
            return df.withColumn(target, col(source).cast(DecimalType(12, 9)))
        else:
            return df.withColumn(target, lit(None).cast(DecimalType(12, 9)))

    def _transform_status(self, df: DataFrame, source: str, target: str) -> DataFrame:
        """
        Mapea códigos de estado numéricos a strings descriptivos.
        Por ahora, convierte a string directamente.
        TODO: Implementar mapeo específico de códigos a nombres
        """
        if source in df.columns:
            # Por ahora, convertir a string
            # En el futuro, agregar mapeo: 1 → 'active', 2 → 'inactive', etc.
            return df.withColumn(target, col(source).cast(StringType()))
        else:
            return df.withColumn(target, lit(None).cast(StringType()))

    def _transform_parent_id(self, df: DataFrame, source: str, target: str) -> DataFrame:
        """
        Usa el ID del registro padre para tablas hijas.
        Ejemplo: en order_items, order_id viene del id de la orden padre.
        """
        # Para tablas hijas, el parent_id es típicamente el mismo que el source
        return self._transform_direct(df, source, target)

    def get_mapped_fields(self, gold_table: str) -> List[str]:
        """
        Retorna lista de campos mapeados para una tabla Gold.
        
        Args:
            gold_table: Nombre de la tabla Gold
        
        Returns:
            Lista de nombres de campos mapeados
        """
        if gold_table not in self.field_mappings:
            return []
        
        return list(self.field_mappings[gold_table].get("fields", {}).keys())

    def get_source_entity(self, gold_table: str) -> str:
        """
        Retorna la entidad fuente para una tabla Gold.
        
        Args:
            gold_table: Nombre de la tabla Gold
        
        Returns:
            Nombre de la entidad fuente (ej: 'orders', 'products')
        """
        if gold_table not in self.field_mappings:
            return ""
        
        return self.field_mappings[gold_table].get("source_entity", "")
