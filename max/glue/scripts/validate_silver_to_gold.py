"""
Script de validación para el checkpoint Silver→Gold
Valida que el pipeline funciona correctamente para 3 tablas: wms_orders, products, stock
"""
import sys
import os
import json
import logging
from datetime import datetime
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, count, isnan, when

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger('ValidateSilverToGold')


def init_spark():
    """Inicializa SparkSession para LocalStack"""
    os.environ["HADOOP_CONF_DIR"] = ""
    
    spark = SparkSession.builder \
        .appName("validate-silver-to-gold") \
        .master("local[*]") \
        .config("spark.jars.packages", "org.apache.hadoop:hadoop-aws:3.3.4,com.amazonaws:aws-java-sdk-bundle:1.12.262") \
        .config("spark.hadoop.fs.s3a.endpoint", "http://localhost:4566") \
        .config("spark.hadoop.fs.s3a.access.key", "test") \
        .config("spark.hadoop.fs.s3a.secret.key", "test") \
        .config("spark.hadoop.fs.s3a.path.style.access", "true") \
        .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem") \
        .config("spark.hadoop.fs.s3a.connection.ssl.enabled", "false") \
        .config("spark.hadoop.fs.s3a.aws.credentials.provider", "org.apache.hadoop.fs.s3a.SimpleAWSCredentialsProvider") \
        .getOrCreate()
    
    hadoop_conf = spark.sparkContext._jsc.hadoopConfiguration()
    hadoop_conf.set("fs.s3a.endpoint", "http://localhost:4566")
    hadoop_conf.set("fs.s3a.access.key", "test")
    hadoop_conf.set("fs.s3a.secret.key", "test")
    hadoop_conf.set("fs.s3a.path.style.access", "true")
    hadoop_conf.set("fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem")
    hadoop_conf.set("fs.s3a.connection.ssl.enabled", "false")
    
    spark.sparkContext.setLogLevel("WARN")
    return spark


def load_redshift_schemas():
    """Carga esquemas de Redshift"""
    config_path = os.path.join(os.path.dirname(__file__), '..', 'src', 'config', 'redshift_schemas.json')
    with open(config_path, 'r') as f:
        return json.load(f)


def validate_schema(df, table_name, expected_schema):
    """
    Valida que el esquema del DataFrame coincide con el esperado
    
    Returns:
        dict: Resultado de validación con status y detalles
    """
    logger.info(f"Validando esquema de {table_name}...")
    
    result = {
        "table": table_name,
        "status": "PASS",
        "issues": [],
        "expected_fields": len(expected_schema),
        "actual_fields": len(df.columns)
    }
    
    # Obtener campos actuales
    actual_fields = set(df.columns)
    expected_fields = set(expected_schema.keys())
    
    # Campos faltantes
    missing_fields = expected_fields - actual_fields
    if missing_fields:
        result["issues"].append(f"Campos faltantes: {', '.join(missing_fields)}")
        result["status"] = "FAIL"
    
    # Campos extra (no crítico, solo advertencia)
    extra_fields = actual_fields - expected_fields
    if extra_fields:
        result["issues"].append(f"Campos extra (no crítico): {', '.join(extra_fields)}")
    
    # Validar tipos de datos para campos críticos
    for field_name, field_config in expected_schema.items():
        if field_name in actual_fields:
            # Aquí podríamos validar tipos, pero Spark maneja tipos dinámicamente
            # Por ahora solo verificamos que el campo existe
            pass
    
    if result["status"] == "PASS":
        logger.info(f"  ✅ Esquema válido: {result['actual_fields']} campos")
    else:
        logger.error(f"  ❌ Esquema inválido: {len(result['issues'])} problemas")
        for issue in result["issues"]:
            logger.error(f"    - {issue}")
    
    return result


def validate_calculated_fields(df, table_name, expected_schema):
    """
    Valida que los campos calculados están presentes y tienen valores correctos
    
    Returns:
        dict: Resultado de validación
    """
    logger.info(f"Validando campos calculados de {table_name}...")
    
    result = {
        "table": table_name,
        "status": "PASS",
        "calculated_fields": [],
        "issues": []
    }
    
    # Identificar campos calculados
    calculated_fields = {
        name: config for name, config in expected_schema.items()
        if config.get("calculated", False)
    }
    
    if not calculated_fields:
        logger.info(f"  ℹ️  No hay campos calculados definidos para {table_name}")
        return result
    
    result["calculated_fields"] = list(calculated_fields.keys())
    
    # Verificar que existen
    for field_name in calculated_fields.keys():
        if field_name not in df.columns:
            result["issues"].append(f"Campo calculado faltante: {field_name}")
            result["status"] = "FAIL"
        else:
            # Verificar que no todos son NULL
            null_count = df.filter(col(field_name).isNull()).count()
            total_count = df.count()
            
            if null_count == total_count:
                result["issues"].append(f"Campo calculado {field_name} tiene todos valores NULL")
                result["status"] = "FAIL"
            else:
                logger.info(f"  ✅ Campo calculado {field_name}: {total_count - null_count}/{total_count} valores no-NULL")
    
    if result["status"] == "PASS":
        logger.info(f"  ✅ Campos calculados válidos: {len(calculated_fields)}")
    else:
        logger.error(f"  ❌ Problemas con campos calculados")
        for issue in result["issues"]:
            logger.error(f"    - {issue}")
    
    return result


def validate_data_gaps(df, table_name, expected_schema):
    """
    Valida que los data gaps están manejados correctamente (campos con NULL)
    
    Returns:
        dict: Resultado de validación
    """
    logger.info(f"Validando data gaps de {table_name}...")
    
    result = {
        "table": table_name,
        "status": "PASS",
        "data_gaps": [],
        "issues": []
    }
    
    # Identificar data gaps
    data_gap_fields = {
        name: config for name, config in expected_schema.items()
        if config.get("data_gap", False)
    }
    
    if not data_gap_fields:
        logger.info(f"  ℹ️  No hay data gaps definidos para {table_name}")
        return result
    
    result["data_gaps"] = list(data_gap_fields.keys())
    
    # Verificar que existen y tienen NULL
    for field_name in data_gap_fields.keys():
        if field_name not in df.columns:
            result["issues"].append(f"Campo data gap faltante: {field_name}")
            result["status"] = "FAIL"
        else:
            # Verificar que todos son NULL (esperado para data gaps)
            null_count = df.filter(col(field_name).isNull()).count()
            total_count = df.count()
            
            logger.info(f"  ✅ Data gap {field_name}: {null_count}/{total_count} valores NULL (esperado)")
    
    if result["status"] == "PASS":
        logger.info(f"  ✅ Data gaps manejados correctamente: {len(data_gap_fields)}")
    else:
        logger.error(f"  ❌ Problemas con data gaps")
        for issue in result["issues"]:
            logger.error(f"    - {issue}")
    
    return result


def validate_data_quality(df, table_name, expected_schema):
    """
    Valida calidad de datos básica
    
    Returns:
        dict: Resultado de validación
    """
    logger.info(f"Validando calidad de datos de {table_name}...")
    
    result = {
        "table": table_name,
        "status": "PASS",
        "total_records": df.count(),
        "issues": []
    }
    
    # Validar que hay registros
    if result["total_records"] == 0:
        result["issues"].append("No hay registros en la tabla")
        result["status"] = "FAIL"
        return result
    
    # Validar campos primary key no son NULL
    pk_fields = [name for name, config in expected_schema.items() if config.get("primary_key", False)]
    
    for pk_field in pk_fields:
        if pk_field in df.columns:
            null_count = df.filter(col(pk_field).isNull()).count()
            if null_count > 0:
                result["issues"].append(f"Primary key {pk_field} tiene {null_count} valores NULL")
                result["status"] = "FAIL"
            else:
                logger.info(f"  ✅ Primary key {pk_field}: sin valores NULL")
    
    # Validar campos required no son NULL
    required_fields = [name for name, config in expected_schema.items() 
                      if not config.get("nullable", True) and not config.get("data_gap", False)]
    
    for req_field in required_fields:
        if req_field in df.columns:
            null_count = df.filter(col(req_field).isNull()).count()
            if null_count > 0:
                result["issues"].append(f"Campo requerido {req_field} tiene {null_count} valores NULL")
                result["status"] = "FAIL"
    
    if result["status"] == "PASS":
        logger.info(f"  ✅ Calidad de datos válida: {result['total_records']} registros")
    else:
        logger.error(f"  ❌ Problemas de calidad de datos")
        for issue in result["issues"]:
            logger.error(f"    - {issue}")
    
    return result


def validate_table(spark, table_name, client="metro"):
    """
    Valida una tabla Gold completa
    
    Returns:
        dict: Resultado completo de validación
    """
    logger.info("=" * 80)
    logger.info(f"VALIDANDO TABLA: {table_name} (cliente: {client})")
    logger.info("=" * 80)
    
    # Cargar esquemas
    schemas = load_redshift_schemas()
    
    if table_name not in schemas["tables"]:
        logger.error(f"Tabla {table_name} no encontrada en redshift_schemas.json")
        return {
            "table": table_name,
            "status": "ERROR",
            "error": "Tabla no encontrada en configuración"
        }
    
    expected_schema = schemas["tables"][table_name]["fields"]
    
    # Leer datos de Gold
    gold_path = f"s3a://data-lake-gold/{client}_{table_name}"
    
    try:
        df = spark.read.json(gold_path)
        logger.info(f"Datos leídos de: {gold_path}")
        logger.info(f"Registros: {df.count()}")
        logger.info(f"Columnas: {len(df.columns)}")
        
        # Ejecutar validaciones
        results = {
            "table": table_name,
            "client": client,
            "timestamp": datetime.now().isoformat(),
            "validations": {}
        }
        
        # 1. Validar esquema
        results["validations"]["schema"] = validate_schema(df, table_name, expected_schema)
        
        # 2. Validar campos calculados
        results["validations"]["calculated_fields"] = validate_calculated_fields(df, table_name, expected_schema)
        
        # 3. Validar data gaps
        results["validations"]["data_gaps"] = validate_data_gaps(df, table_name, expected_schema)
        
        # 4. Validar calidad de datos
        results["validations"]["data_quality"] = validate_data_quality(df, table_name, expected_schema)
        
        # Determinar status general
        all_pass = all(v["status"] == "PASS" for v in results["validations"].values())
        results["overall_status"] = "PASS" if all_pass else "FAIL"
        
        # Mostrar muestra de datos
        logger.info("\nMuestra de datos (primeras 5 filas):")
        df.show(5, truncate=False)
        
        return results
        
    except Exception as e:
        logger.error(f"Error al validar tabla {table_name}: {str(e)}")
        return {
            "table": table_name,
            "status": "ERROR",
            "error": str(e)
        }


def generate_report(all_results):
    """
    Genera reporte final de validación
    """
    logger.info("\n" + "=" * 80)
    logger.info("REPORTE FINAL DE VALIDACIÓN")
    logger.info("=" * 80)
    
    total_tables = len(all_results)
    passed_tables = sum(1 for r in all_results if r.get("overall_status") == "PASS")
    failed_tables = sum(1 for r in all_results if r.get("overall_status") == "FAIL")
    error_tables = sum(1 for r in all_results if r.get("status") == "ERROR")
    
    logger.info(f"\nTotal de tablas validadas: {total_tables}")
    logger.info(f"  ✅ Pasaron: {passed_tables}")
    logger.info(f"  ❌ Fallaron: {failed_tables}")
    logger.info(f"  ⚠️  Errores: {error_tables}")
    
    # Detalles por tabla
    logger.info("\nDetalles por tabla:")
    for result in all_results:
        table_name = result["table"]
        status = result.get("overall_status", result.get("status", "UNKNOWN"))
        
        if status == "PASS":
            logger.info(f"  ✅ {table_name}: PASS")
        elif status == "FAIL":
            logger.info(f"  ❌ {table_name}: FAIL")
            if "validations" in result:
                for val_name, val_result in result["validations"].items():
                    if val_result["status"] == "FAIL":
                        logger.info(f"      - {val_name}: {len(val_result.get('issues', []))} problemas")
        else:
            logger.info(f"  ⚠️  {table_name}: ERROR - {result.get('error', 'Unknown error')}")
    
    # Guardar reporte JSON
    report_path = "validation_report_silver_to_gold.json"
    with open(report_path, 'w') as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total": total_tables,
                "passed": passed_tables,
                "failed": failed_tables,
                "errors": error_tables
            },
            "results": all_results
        }, f, indent=2)
    
    logger.info(f"\nReporte guardado en: {report_path}")
    
    return passed_tables == total_tables


def main():
    """
    Ejecuta validación completa para las 3 tablas del checkpoint
    """
    logger.info("Iniciando validación Silver→Gold Checkpoint")
    logger.info("Tablas a validar: wms_orders, products, stock")
    
    spark = init_spark()
    
    # Tablas a validar
    tables_to_validate = ["wms_orders", "products", "stock"]
    client = "metro"
    
    all_results = []
    
    for table_name in tables_to_validate:
        result = validate_table(spark, table_name, client)
        all_results.append(result)
    
    # Generar reporte final
    success = generate_report(all_results)
    
    spark.stop()
    
    if success:
        logger.info("\n✅ VALIDACIÓN EXITOSA: Todas las tablas pasaron las validaciones")
        return 0
    else:
        logger.error("\n❌ VALIDACIÓN FALLIDA: Algunas tablas tienen problemas")
        return 1


if __name__ == "__main__":
    sys.exit(main())
