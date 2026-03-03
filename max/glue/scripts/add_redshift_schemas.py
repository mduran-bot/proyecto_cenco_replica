#!/usr/bin/env python3
"""
Script to add remaining 21 tables to redshift_schemas.json
"""
import json
import sys

# Read current schemas
with open('max/glue/etl-silver-to-gold/config/redshift_schemas.json', 'r') as f:
    schemas = json.load(f)

# Define the 21 new tables to add
new_tables = {
    "wms_order_shipping": {
        "description": "Información de envío de órdenes",
        "source_tables": ["metro_order_shipping_clean"],
        "primary_key": ["shipping_id"],
        "partition_by": ["date_created"],
        "fields": {
            "shipping_id": {"type": "VARCHAR(50)", "nullable": False, "description": "ID único del envío"},
            "order_id": {"type": "VARCHAR(50)", "nullable": False, "description": "ID de la orden"},
            "city": {"type": "VARCHAR(100)", "nullable": True, "description": "Ciudad de entrega"},
            "neighborhood": {"type": "VARCHAR(100)", "nullable": True, "description": "Barrio de entrega"},
            "complement": {"type": "VARCHAR(255)", "nullable": True, "description": "Complemento de dirección"},
            "lat": {"type": "DECIMAL(12,9)", "nullable": True, "description": "Latitud"},
            "lng": {"type": "DECIMAL(12,9)", "nullable": True, "description": "Longitud"},
            "shipping_window_start": {"type": "TIMESTAMP", "nullable": True, "description": "Inicio ventana de envío"},
            "shipping_window_end": {"type": "TIMESTAMP", "nullable": True, "description": "Fin ventana de envío"},
            "shipped_date_start": {"type": "TIMESTAMP", "nullable": True, "description": "Fecha inicio envío"},
            "shipped_date_end": {"type": "TIMESTAMP", "nullable": True, "description": "Fecha fin envío"},
            "date_created": {"type": "TIMESTAMP", "nullable": False, "description": "Fecha de creación"},
            "date_modified": {"type": "TIMESTAMP", "nullable": True, "description": "Fecha de modificación"},
            "status": {"type": "VARCHAR(50)", "nullable": False, "description": "Estado del envío"}
        },
        "quality_rules": {
            "critical_fields": ["shipping_id", "order_id", "date_created"],
            "numeric_ranges": {
                "lat": {"min": -90, "max": 90},
                "lng": {"min": -180, "max": 180}
            }
        }
    }
}

# Add new tables
schemas["tables"].update(new_tables)

# Write back
with open('max/glue/etl-silver-to-gold/config/redshift_schemas.json', 'w') as f:
    json.dump(schemas, f, indent=2)

print("Added 1 table to redshift_schemas.json")
print("Remaining: 20 tables")
