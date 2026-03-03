"""
SilverToGoldAggregator Module
Calcula agregaciones para métricas de negocio.
"""
from pyspark.sql import DataFrame
from pyspark.sql import functions as F


class SilverToGoldAggregator:
    
    def transform(self, df: DataFrame, config: dict) -> DataFrame:
        agg_config = config.get("aggregations", {})
        date_col = agg_config.get("date_column", "fecha_venta")
        dimensions = agg_config.get("dimensions", [])
        metrics = agg_config.get("metrics", [])
        
        # Agregar dimensiones de tiempo
        df = self._add_time_dimensions(df, date_col)
        
        # Calcular agregaciones
        df = self._aggregate_by_dimensions(df, dimensions, metrics)
        
        return df
    
    def _add_time_dimensions(self, df: DataFrame, date_col: str) -> DataFrame:
        if date_col not in df.columns:
            return df
        return df \
            .withColumn("year", F.year(F.col(date_col))) \
            .withColumn("month", F.month(F.col(date_col))) \
            .withColumn("day", F.dayofmonth(F.col(date_col))) \
            .withColumn("week", F.weekofyear(F.col(date_col)))
    
    def _aggregate_by_dimensions(self, df: DataFrame, dimensions: list, metrics: list) -> DataFrame:
        if not dimensions or not metrics:
            return df
        
        # Filtrar dimensions que existen en el df
        valid_dims = [d for d in dimensions if d in df.columns]
        
        agg_exprs = []
        for metric in metrics:
            column = metric.get("column")
            functions = metric.get("functions", [])
            
            for func in functions:
                if column == "*":
                    if func == "count":
                        agg_exprs.append(F.count("*").alias("num_registros"))
                elif column in df.columns:
                    if func == "sum":
                        agg_exprs.append(F.sum(column).alias(f"total_{column}"))
                    elif func == "avg":
                        agg_exprs.append(F.avg(column).alias(f"promedio_{column}"))
                    elif func == "min":
                        agg_exprs.append(F.min(column).alias(f"min_{column}"))
                    elif func == "max":
                        agg_exprs.append(F.max(column).alias(f"max_{column}"))
        
        if not agg_exprs:
            return df
        
        return df.groupBy(*valid_dims).agg(*agg_exprs)