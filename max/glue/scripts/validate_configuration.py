#!/usr/bin/env python3
"""
Script para validar la configuración de las 41 entidades y 26 tablas Gold

Este script:
1. Valida que entities_mapping.json tenga las 41 entidades
2. Valida que field_mappings.json tenga las 26 tablas
3. Valida que redshift_schemas.json tenga las 26 tablas
4. Genera un reporte de validación

Uso:
    python scripts/validate_configuration.py
"""

import sys
import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Tuple

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger('ConfigValidator')


def load_json_file(file_path: str) -> dict:
    """Cargar archivo JSON"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error cargando {file_path}: {str(e)}")
        return {}


def validate_entities_mapping(config_dir: str = "etl-bronze-to-silver/config") -> Tuple[bool, List[str], int]:
    """
    Validar entities_mapping.json
    
    Returns:
        Tuple[bool, List[str], int]: (is_valid, entity_list, count)
    """
    logger.info("=" * 80)
    logger.info("VALIDANDO ENTITIES_MAPPING.JSON")
    logger.info("=" * 80)
    
    file_path = os.path.join(config_dir, "entities_mapping.json")
    data = load_json_file(file_path)
    
    if not data:
        logger.error("❌ No se pudo cargar entities_mapping.json")
        return False, [], 0
    
    entities = list(data.keys())
    entity_count = len(entities)
    
    logger.info(f"Entidades encontradas: {entity_count}")
    
    # Validar que tengamos al menos 41 entidades
    if entity_count >= 41:
        logger.info(f"✅ Configuración completa: {entity_count} entidades")
        is_valid = True
    else:
        logger.warning(f"⚠️ Configuración incompleta: {entity_count}/41 entidades")
        is_valid = False
    
    # Listar entidades
    logger.info("\nEntidades configuradas:")
    for i, entity in enumerate(sorted(entities), 1):
        logger.info(f"  {i:2d}. {entity}")
    
    return is_valid, entities, entity_count


def validate_field_mappings(config_dir: str = "etl-silver-to-gold/config") -> Tuple[bool, List[str], int]:
    """
    Validar field_mappings.json
    
    Returns:
        Tuple[bool, List[str], int]: (is_valid, table_list, count)
    """
    logger.info("\n" + "=" * 80)
    logger.info("VALIDANDO FIELD_MAPPINGS.JSON")
    logger.info("=" * 80)
    
    file_path = os.path.join(config_dir, "field_mappings.json")
    data = load_json_file(file_path)
    
    if not data:
        logger.error("❌ No se pudo cargar field_mappings.json")
        return False, [], 0
    
    mappings = data.get("mappings", {})
    tables = list(mappings.keys())
    table_count = len(tables)
    
    logger.info(f"Tablas con field mappings: {table_count}")
    
    # Validar que tengamos las 26 tablas
    expected_count = 26
    if table_count >= expected_count:
        logger.info(f"✅ Configuración completa: {table_count} tablas")
        is_valid = True
    else:
        logger.warning(f"⚠️ Configuración incompleta: {table_count}/{expected_count} tablas")
        is_valid = False
    
    # Listar tablas
    logger.info("\nTablas con field mappings:")
    for i, table in enumerate(sorted(tables), 1):
        field_count = len(mappings[table].get("fields", {}))
        logger.info(f"  {i:2d}. {table:40s} - {field_count} campos")
    
    return is_valid, tables, table_count


def validate_redshift_schemas(config_dir: str = "etl-silver-to-gold/config") -> Tuple[bool, List[str], int]:
    """
    Validar redshift_schemas.json
    
    Returns:
        Tuple[bool, List[str], int]: (is_valid, table_list, count)
    """
    logger.info("\n" + "=" * 80)
    logger.info("VALIDANDO REDSHIFT_SCHEMAS.JSON")
    logger.info("=" * 80)
    
    file_path = os.path.join(config_dir, "redshift_schemas.json")
    data = load_json_file(file_path)
    
    if not data:
        logger.error("❌ No se pudo cargar redshift_schemas.json")
        return False, [], 0
    
    tables_data = data.get("tables", {})
    tables = list(tables_data.keys())
    table_count = len(tables)
    
    logger.info(f"Tablas con schemas: {table_count}")
    
    # Validar que tengamos las 26 tablas
    expected_count = 26
    if table_count >= expected_count:
        logger.info(f"✅ Configuración completa: {table_count} tablas")
        is_valid = True
    else:
        logger.warning(f"⚠️ Configuración incompleta: {table_count}/{expected_count} tablas")
        is_valid = False
    
    # Listar tablas con detalles
    logger.info("\nTablas con schemas:")
    for i, table in enumerate(sorted(tables), 1):
        table_info = tables_data[table]
        field_count = len(table_info.get("fields", {}))
        pk = table_info.get("primary_key", [])
        partition = table_info.get("partition_by", [])
        
        logger.info(f"  {i:2d}. {table:40s} - {field_count} campos, PK: {pk}, Partition: {partition}")
    
    return is_valid, tables, table_count


def generate_validation_report(
    entities_valid: bool,
    entities: List[str],
    entity_count: int,
    mappings_valid: bool,
    mapping_tables: List[str],
    mapping_count: int,
    schemas_valid: bool,
    schema_tables: List[str],
    schema_count: int
) -> None:
    """Generar reporte de validación"""
    
    logger.info("\n" + "=" * 80)
    logger.info("REPORTE DE VALIDACIÓN")
    logger.info("=" * 80)
    
    # Calcular estado general
    all_valid = entities_valid and mappings_valid and schemas_valid
    
    logger.info(f"\nEstado General: {'✅ VÁLIDO' if all_valid else '⚠️ INCOMPLETO'}")
    logger.info("")
    logger.info(f"1. Entities Mapping:  {'✅' if entities_valid else '⚠️'} {entity_count}/41 entidades")
    logger.info(f"2. Field Mappings:    {'✅' if mappings_valid else '⚠️'} {mapping_count}/26 tablas")
    logger.info(f"3. Redshift Schemas:  {'✅' if schemas_valid else '⚠️'} {schema_count}/26 tablas")
    
    # Identificar tablas faltantes
    if not mappings_valid or not schemas_valid:
        logger.info("\n" + "-" * 80)
        logger.info("TABLAS FALTANTES")
        logger.info("-" * 80)
        
        # Tablas esperadas según el análisis
        expected_tables = {
            "wms_orders", "wms_order_items", "wms_order_shipping",
            "wms_logistic_carriers", "wms_order_item_weighables",
            "wms_order_status_changes", "wms_stores",
            "wms_logistic_delivery_planning", "wms_logistic_delivery_ranges",
            "wms_order_payments", "wms_order_payments_connector_responses",
            "wms_order_custom_data_fields", "products", "skus",
            "categories", "admins", "price", "brands", "customers",
            "wms_order_picking", "picking_round_orders", "stock",
            "promotional_prices", "promotions", "invoices", "ff_comments"
        }
        
        missing_mappings = expected_tables - set(mapping_tables)
        missing_schemas = expected_tables - set(schema_tables)
        
        if missing_mappings:
            logger.info(f"\nTablas sin field mappings ({len(missing_mappings)}):")
            for table in sorted(missing_mappings):
                logger.info(f"  - {table}")
        
        if missing_schemas:
            logger.info(f"\nTablas sin schemas ({len(missing_schemas)}):")
            for table in sorted(missing_schemas):
                logger.info(f"  - {table}")
    
    # Guardar reporte en JSON
    report_data = {
        "timestamp": datetime.now().isoformat(),
        "validation_status": "valid" if all_valid else "incomplete",
        "entities_mapping": {
            "valid": entities_valid,
            "count": entity_count,
            "expected": 41,
            "entities": entities
        },
        "field_mappings": {
            "valid": mappings_valid,
            "count": mapping_count,
            "expected": 26,
            "tables": mapping_tables
        },
        "redshift_schemas": {
            "valid": schemas_valid,
            "count": schema_count,
            "expected": 26,
            "tables": schema_tables
        }
    }
    
    report_path = f"output/configuration_validation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    os.makedirs("output", exist_ok=True)
    
    with open(report_path, 'w') as f:
        json.dump(report_data, f, indent=2)
    
    logger.info(f"\nReporte guardado en: {report_path}")
    logger.info("=" * 80)


def main():
    """Función principal"""
    logger.info("=" * 80)
    logger.info("VALIDADOR DE CONFIGURACIÓN - ETL 41 APIS")
    logger.info("=" * 80)
    logger.info(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("")
    
    try:
        # Validar entities_mapping.json
        entities_valid, entities, entity_count = validate_entities_mapping()
        
        # Validar field_mappings.json
        mappings_valid, mapping_tables, mapping_count = validate_field_mappings()
        
        # Validar redshift_schemas.json
        schemas_valid, schema_tables, schema_count = validate_redshift_schemas()
        
        # Generar reporte
        generate_validation_report(
            entities_valid, entities, entity_count,
            mappings_valid, mapping_tables, mapping_count,
            schemas_valid, schema_tables, schema_count
        )
        
        # Retornar código de salida
        all_valid = entities_valid and mappings_valid and schemas_valid
        return 0 if all_valid else 1
        
    except Exception as e:
        logger.error("=" * 80)
        logger.error("ERROR EN LA VALIDACIÓN")
        logger.error("=" * 80)
        logger.error(f"Error: {str(e)}")
        logger.exception("Traceback completo:")
        return 1


if __name__ == "__main__":
    sys.exit(main())
