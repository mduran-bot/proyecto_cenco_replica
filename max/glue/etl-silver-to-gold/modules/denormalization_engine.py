"""
DenormalizationEngine Module
Combina entidades relacionadas en tablas planas.
"""
from pyspark.sql import DataFrame


class DenormalizationEngine:
    
    def transform(self, df: DataFrame, config: dict) -> DataFrame:
        denorm_config = config.get("denormalization", {})
        
        if not denorm_config.get("enabled", False):
            return df
        
        joins = denorm_config.get("joins", [])
        return self._join_entities(df, joins)
    
    def _join_entities(self, base_df: DataFrame, join_configs: list) -> DataFrame:
        # Para LocalStack sin tablas adicionales, retorna el df base
        # En producción leería tablas Silver de clientes/productos
        for join in join_configs:
            print(f"[INFO] Join configurado: {join} (no ejecutado en modo local)")
        return base_df