"""
CalculatedFieldsEngine Module

Calcula campos derivados a partir de otros campos según configuración
en redshift_schemas.json.

Campos calculados soportados:
- total_changes (wms_orders): totals.items.amount - totals.items.originalAmount
- total_time (wms_order_picking): (endPickingTime - startPickingTime) / 1000
- username (admins): firstname + ' ' + lastname
- quantity_difference (wms_order_items): quantity_picked - quantity

Maneja NULL sin errores: si algún campo fuente es NULL, el resultado es NULL.
"""

from pyspark.sql import DataFrame
from pyspark.sql.functions import (
    col, lit, when, concat, coalesce, expr
)
from typing import Dict, Any
import logging
import json


class CalculatedFieldsEngine:
    """
    Calcula campos derivados según configuración en redshift_schemas.json.
    
    Lee la sección 'calculated' de cada campo para determinar la fórmula
    a aplicar. Maneja NULL gracefully sin generar errores.
    """

    def __init__(self, redshift_schemas_path: str = None):
        """
        Inicializa el CalculatedFieldsEngine.
        
        Args:
            redshift_schemas_path: Ruta al archivo redshift_schemas.json
                                  Si es None, usa ruta por defecto
        """
        self.logger = logging.getLogger('CalculatedFieldsEngine')
        self.redshift_schemas_path = redshift_schemas_path or "max/src/config/redshift_schemas.json"
        self.schemas = self._load_schemas()

    def _load_schemas(self) -> Dict:
        """Carga esquemas de Redshift desde JSON."""
        try:
            with open(self.redshift_schemas_path, 'r', encoding='utf-8') as f:
                schemas = json.load(f)
            self.logger.info(f"[CalculatedFieldsEngine] Cargados esquemas para {len(schemas.get('tables', {}))} tablas")
            return schemas.get('tables', {})
        except FileNotFoundError:
            self.logger.error(f"[CalculatedFieldsEngine] Archivo no encontrado: {self.redshift_schemas_path}")
            return {}
        except json.JSONDecodeError as e:
            self.logger.error(f"[CalculatedFieldsEngine] Error parseando JSON: {e}")
            return {}

    def transform(self, df: DataFrame, config: dict) -> DataFrame:
        """
        Calcula campos derivados para el DataFrame.
        
        Args:
            df: DataFrame con campos fuente
            config: Configuración con:
                - gold_table: nombre de la tabla Gold destino
        
        Returns:
            DataFrame con campos calculados agregados
        """
        gold_table = config.get("gold_table")
        if not gold_table:
            self.logger.error("[CalculatedFieldsEngine] Falta 'gold_table' en config")
            return df

        if gold_table not in self.schemas:
            self.logger.warning(f"[CalculatedFieldsEngine] No hay esquema para tabla '{gold_table}' — pasando sin cambios")
            return df

        table_schema = self.schemas[gold_table]
        fields = table_schema.get("fields", {})
        
        # Identificar campos calculados
        calculated_fields = {
            field_name: field_config 
            for field_name, field_config in fields.items() 
            if field_config.get("calculated", False)
        }
        
        if not calculated_fields:
            self.logger.info(f"[CalculatedFieldsEngine] No hay campos calculados para '{gold_table}'")
            return df
        
        self.logger.info(f"[CalculatedFieldsEngine] Calculando {len(calculated_fields)} campos para '{gold_table}'")
        
        # Aplicar cálculos
        result_df = df
        for field_name, field_config in calculated_fields.items():
            formula = field_config.get("formula", "")
            if not formula:
                self.logger.warning(f"[CalculatedFieldsEngine] Campo '{field_name}' marcado como calculado pero sin fórmula")
                continue
            
            try:
                result_df = self._calculate_field(result_df, field_name, formula, gold_table)
            except Exception as e:
                self.logger.error(f"[CalculatedFieldsEngine] Error calculando '{field_name}': {e}")
                # Agregar columna NULL en caso de error
                result_df = result_df.withColumn(field_name, lit(None))
        
        self.logger.info(f"[CalculatedFieldsEngine] ✅ Calculados {len(calculated_fields)} campos para '{gold_table}'")
        return result_df

    def _calculate_field(self, df: DataFrame, field_name: str, formula: str, table_name: str) -> DataFrame:
        """
        Calcula un campo específico según su fórmula.
        
        Args:
            df: DataFrame fuente
            field_name: Nombre del campo a calcular
            formula: Fórmula de cálculo
            table_name: Nombre de la tabla (para lógica específica)
        
        Returns:
            DataFrame con campo calculado agregado
        """
        # Implementar cálculos específicos por tabla
        if table_name == "wms_orders" and field_name == "total_changes":
            return self._calculate_total_changes(df, field_name)
        
        elif table_name == "wms_order_picking" and field_name == "total_time":
            return self._calculate_total_time(df, field_name)
        
        elif table_name == "admins" and field_name == "username":
            return self._calculate_username(df, field_name)
        
        elif table_name == "wms_order_items" and field_name == "quantity_difference":
            return self._calculate_quantity_difference(df, field_name)
        
        else:
            # Intentar evaluar fórmula genérica
            self.logger.warning(f"[CalculatedFieldsEngine] Fórmula genérica no implementada para '{field_name}': {formula}")
            return df.withColumn(field_name, lit(None))

    def _calculate_total_changes(self, df: DataFrame, field_name: str) -> DataFrame:
        """
        Calcula total_changes = totals.items.amount - totals.items.originalAmount
        
        Maneja NULL: si alguno de los campos es NULL, el resultado es NULL.
        """
        # Verificar que los campos fuente existan
        # Los campos ya deberían estar aplanados por SchemaMapper
        # Buscar campos que contengan 'items_amount' y 'items_original_amount'
        
        items_amount_col = None
        items_original_amount_col = None
        
        for col_name in df.columns:
            if 'items_amount' in col_name.lower() and 'original' not in col_name.lower():
                items_amount_col = col_name
            elif 'items_original_amount' in col_name.lower() or 'original_amount' in col_name.lower():
                items_original_amount_col = col_name
        
        # También buscar por nombres exactos mapeados
        if 'total_items' in df.columns:
            items_amount_col = 'total_items'
        if 'total_original' in df.columns:
            items_original_amount_col = 'total_original'
        
        if items_amount_col and items_original_amount_col:
            # Calcular diferencia, manejando NULL
            calc_expr = when(
                col(items_amount_col).isNotNull() & col(items_original_amount_col).isNotNull(),
                col(items_amount_col) - col(items_original_amount_col)
            ).otherwise(lit(None))
            
            self.logger.debug(f"[CalculatedFieldsEngine] Calculando {field_name} = {items_amount_col} - {items_original_amount_col}")
            return df.withColumn(field_name, calc_expr)
        else:
            self.logger.warning(
                f"[CalculatedFieldsEngine] No se encontraron campos fuente para {field_name}. "
                f"Buscados: items_amount={items_amount_col}, items_original_amount={items_original_amount_col}"
            )
            return df.withColumn(field_name, lit(None))

    def _calculate_total_time(self, df: DataFrame, field_name: str) -> DataFrame:
        """
        Calcula total_time = (endPickingTime - startPickingTime) / 1000
        
        Convierte diferencia de timestamps Unix a segundos.
        Maneja NULL: si alguno de los campos es NULL, el resultado es NULL.
        """
        # Buscar campos de tiempo de picking
        start_time_col = None
        end_time_col = None
        
        for col_name in df.columns:
            if 'start' in col_name.lower() and 'pick' in col_name.lower():
                start_time_col = col_name
            elif 'end' in col_name.lower() and 'pick' in col_name.lower():
                end_time_col = col_name
        
        # También buscar por nombres exactos mapeados
        if 'pick_start_time' in df.columns:
            start_time_col = 'pick_start_time'
        if 'pick_end_time' in df.columns:
            end_time_col = 'pick_end_time'
        
        if start_time_col and end_time_col:
            # Calcular diferencia en segundos, manejando NULL
            # Si los campos ya son timestamps, usar unix_timestamp para convertir a segundos
            calc_expr = when(
                col(start_time_col).isNotNull() & col(end_time_col).isNotNull(),
                (expr(f"unix_timestamp({end_time_col})") - expr(f"unix_timestamp({start_time_col})"))
            ).otherwise(lit(None))
            
            self.logger.debug(f"[CalculatedFieldsEngine] Calculando {field_name} = ({end_time_col} - {start_time_col})")
            return df.withColumn(field_name, calc_expr)
        else:
            self.logger.warning(
                f"[CalculatedFieldsEngine] No se encontraron campos fuente para {field_name}. "
                f"Buscados: start_time={start_time_col}, end_time={end_time_col}"
            )
            return df.withColumn(field_name, lit(None))

    def _calculate_username(self, df: DataFrame, field_name: str) -> DataFrame:
        """
        Calcula username = firstname + ' ' + lastname
        
        Maneja NULL: si alguno de los campos es NULL, usa solo el disponible.
        Si ambos son NULL, el resultado es NULL.
        """
        firstname_col = None
        lastname_col = None
        
        for col_name in df.columns:
            if 'firstname' in col_name.lower() or 'first_name' in col_name.lower():
                firstname_col = col_name
            elif 'lastname' in col_name.lower() or 'last_name' in col_name.lower():
                lastname_col = col_name
        
        if firstname_col and lastname_col:
            # Concatenar con espacio, manejando NULL
            calc_expr = when(
                col(firstname_col).isNotNull() & col(lastname_col).isNotNull(),
                concat(col(firstname_col), lit(' '), col(lastname_col))
            ).when(
                col(firstname_col).isNotNull(),
                col(firstname_col)
            ).when(
                col(lastname_col).isNotNull(),
                col(lastname_col)
            ).otherwise(lit(None))
            
            self.logger.debug(f"[CalculatedFieldsEngine] Calculando {field_name} = {firstname_col} + ' ' + {lastname_col}")
            return df.withColumn(field_name, calc_expr)
        else:
            self.logger.warning(
                f"[CalculatedFieldsEngine] No se encontraron campos fuente para {field_name}. "
                f"Buscados: firstname={firstname_col}, lastname={lastname_col}"
            )
            return df.withColumn(field_name, lit(None))

    def _calculate_quantity_difference(self, df: DataFrame, field_name: str) -> DataFrame:
        """
        Calcula quantity_difference = quantity_picked - quantity
        
        Maneja NULL: si alguno de los campos es NULL, el resultado es NULL.
        """
        quantity_col = None
        quantity_picked_col = None
        
        for col_name in df.columns:
            if col_name.lower() == 'quantity' or col_name.lower() == 'quantity_purchased':
                quantity_col = col_name
            elif 'quantity_picked' in col_name.lower():
                quantity_picked_col = col_name
        
        if quantity_col and quantity_picked_col:
            # Calcular diferencia, manejando NULL
            calc_expr = when(
                col(quantity_picked_col).isNotNull() & col(quantity_col).isNotNull(),
                col(quantity_picked_col) - col(quantity_col)
            ).otherwise(lit(None))
            
            self.logger.debug(f"[CalculatedFieldsEngine] Calculando {field_name} = {quantity_picked_col} - {quantity_col}")
            return df.withColumn(field_name, calc_expr)
        else:
            self.logger.warning(
                f"[CalculatedFieldsEngine] No se encontraron campos fuente para {field_name}. "
                f"Buscados: quantity={quantity_col}, quantity_picked={quantity_picked_col}"
            )
            return df.withColumn(field_name, lit(None))

    def get_calculated_fields(self, gold_table: str) -> Dict[str, str]:
        """
        Retorna diccionario de campos calculados para una tabla Gold.
        
        Args:
            gold_table: Nombre de la tabla Gold
        
        Returns:
            Diccionario {field_name: formula}
        """
        if gold_table not in self.schemas:
            return {}
        
        table_schema = self.schemas[gold_table]
        fields = table_schema.get("fields", {})
        
        return {
            field_name: field_config.get("formula", "")
            for field_name, field_config in fields.items()
            if field_config.get("calculated", False)
        }
