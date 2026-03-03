#!/usr/bin/env python3
import json

with open('max/glue/etl-silver-to-gold/config/redshift_schemas.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Define all 20 remaining tables
remaining_tables = {
    'wms_order_status_changes': {
        'description': 'Cambios de estado de órdenes',
        'source_tables': ['metro_order_status_changes_clean'],
        'primary_key': ['status_change_id'],
        'partition_by': ['date_created'],
        'fields': {
            'status_change_id': {'type': 'VARCHAR(50)', 'nullable': False, 'description': 'ID único del cambio'},
            'order_id': {'type': 'VARCHAR(50)', 'nullable': False, 'description': 'ID de la orden'},
            'new_status': {'type': 'VARCHAR(50)', 'nullable': False, 'description': 'Nuevo estado'},
            'user_created': {'type': 'VARCHAR(100)', 'nullable': True, 'description': 'Usuario que creó el cambio'},
            'extra': {'type': 'VARCHAR(1000)', 'nullable': True, 'description': 'Información adicional'},
            'date_created': {'type': 'TIMESTAMP', 'nullable': False, 'description': 'Fecha del cambio'}
        },
        'quality_rules': {'critical_fields': ['status_change_id', 'order_id', 'new_status']}
    },
    'wms_order_payments': {
        'description': 'Pagos de órdenes',
        'source_tables': ['metro_order_payments_clean'],
        'primary_key': ['payment_id'],
        'partition_by': ['date_created'],
        'fields': {
            'payment_id': {'type': 'VARCHAR(50)', 'nullable': False, 'description': 'ID único del pago'},
            'order_id': {'type': 'VARCHAR(50)', 'nullable': False, 'description': 'ID de la orden'},
            'payment_method': {'type': 'VARCHAR(100)', 'nullable': False, 'description': 'Método de pago'},
            'payment_system_name': {'type': 'VARCHAR(100)', 'nullable': True, 'description': 'Nombre del sistema de pago'},
            'payment_group': {'type': 'VARCHAR(50)', 'nullable': True, 'description': 'Grupo de pago'},
            'acquirer': {'type': 'VARCHAR(100)', 'nullable': True, 'description': 'Adquirente'},
            'amount': {'type': 'DECIMAL(18,2)', 'nullable': False, 'description': 'Monto del pago'},
            'status': {'type': 'VARCHAR(50)', 'nullable': False, 'description': 'Estado del pago'},
            'date_created': {'type': 'TIMESTAMP', 'nullable': False, 'description': 'Fecha de creación'},
            'date_modified': {'type': 'TIMESTAMP', 'nullable': True, 'description': 'Fecha de modificación'}
        },
        'quality_rules': {'critical_fields': ['payment_id', 'order_id', 'amount'], 'numeric_ranges': {'amount': {'min': 0, 'max': 999999}}}
    },
    'wms_order_payments_connector_responses': {
        'description': 'Respuestas de conectores de pago',
        'source_tables': ['metro_order_payments_clean'],
        'primary_key': ['payment_id', 'field'],
        'partition_by': [],
        'fields': {
            'payment_id': {'type': 'VARCHAR(50)', 'nullable': False, 'description': 'ID del pago'},
            'field': {'type': 'VARCHAR(100)', 'nullable': False, 'description': 'Nombre del campo'},
            'value': {'type': 'VARCHAR(1000)', 'nullable': True, 'description': 'Valor del campo'}
        },
        'quality_rules': {'critical_fields': ['payment_id', 'field']}
    },
    'wms_order_custom_data_fields': {
        'description': 'Campos personalizados de órdenes',
        'source_tables': ['metro_orders_clean'],
        'primary_key': ['order_id', 'field'],
        'partition_by': [],
        'fields': {
            'order_id': {'type': 'VARCHAR(50)', 'nullable': False, 'description': 'ID de la orden'},
            'field': {'type': 'VARCHAR(100)', 'nullable': False, 'description': 'Nombre del campo'},
            'value': {'type': 'VARCHAR(1000)', 'nullable': True, 'description': 'Valor del campo'}
        },
        'quality_rules': {'critical_fields': ['order_id', 'field']}
    },
    'wms_order_item_weighables': {
        'description': 'Items pesables de órdenes',
        'source_tables': ['metro_order_items_clean'],
        'primary_key': ['order_item_id'],
        'partition_by': ['date_created'],
        'fields': {
            'order_item_id': {'type': 'VARCHAR(50)', 'nullable': False, 'description': 'ID del item'},
            'order_id': {'type': 'VARCHAR(50)', 'nullable': False, 'description': 'ID de la orden'},
            'weight_picked': {'type': 'DECIMAL(10,2)', 'nullable': True, 'description': 'Peso pickeado'},
            'quantity': {'type': 'INTEGER', 'nullable': False, 'description': 'Cantidad'},
            'measurement_unit': {'type': 'VARCHAR(20)', 'nullable': True, 'description': 'Unidad de medida'},
            'date_created': {'type': 'TIMESTAMP', 'nullable': False, 'description': 'Fecha de creación'},
            'date_modified': {'type': 'TIMESTAMP', 'nullable': True, 'description': 'Fecha de modificación'}
        },
        'quality_rules': {'critical_fields': ['order_item_id', 'order_id'], 'numeric_ranges': {'weight_picked': {'min': 0, 'max': 999999}}}
    }
}

data['tables'].update(remaining_tables)


# Continue with more tables
more_tables = {
    'wms_stores': {
        'description': 'Tiendas y almacenes',
        'source_tables': ['metro_stores_clean'],
        'primary_key': ['store_id'],
        'partition_by': [],
        'fields': {
            'store_id': {'type': 'VARCHAR(50)', 'nullable': False, 'description': 'ID de la tienda'},
            'store_name': {'type': 'VARCHAR(255)', 'nullable': False, 'description': 'Nombre de la tienda'},
            'code': {'type': 'VARCHAR(50)', 'nullable': True, 'description': 'Código de la tienda'},
            'country': {'type': 'VARCHAR(10)', 'nullable': True, 'description': 'País'},
            'city': {'type': 'VARCHAR(100)', 'nullable': True, 'description': 'Ciudad'},
            'address': {'type': 'VARCHAR(255)', 'nullable': True, 'description': 'Dirección'},
            'lat': {'type': 'DECIMAL(12,9)', 'nullable': True, 'description': 'Latitud'},
            'lng': {'type': 'DECIMAL(12,9)', 'nullable': True, 'description': 'Longitud'},
            'apply_quotation': {'type': 'BOOLEAN', 'nullable': True, 'description': 'Aplica cotización'},
            'status': {'type': 'VARCHAR(50)', 'nullable': False, 'description': 'Estado'},
            'date_created': {'type': 'TIMESTAMP', 'nullable': False, 'description': 'Fecha de creación'},
            'date_modified': {'type': 'TIMESTAMP', 'nullable': True, 'description': 'Fecha de modificación'}
        },
        'quality_rules': {'critical_fields': ['store_id', 'store_name'], 'numeric_ranges': {'lat': {'min': -90, 'max': 90}, 'lng': {'min': -180, 'max': 180}}}
    },
    'wms_logistic_carriers': {
        'description': 'Transportistas logísticos',
        'source_tables': ['metro_carriers_clean'],
        'primary_key': ['carrier_id'],
        'partition_by': [],
        'fields': {
            'carrier_id': {'type': 'VARCHAR(50)', 'nullable': False, 'description': 'ID del transportista'},
            'carrier_name': {'type': 'VARCHAR(255)', 'nullable': False, 'description': 'Nombre del transportista'},
            'code': {'type': 'VARCHAR(50)', 'nullable': True, 'description': 'Código'},
            'status': {'type': 'VARCHAR(50)', 'nullable': False, 'description': 'Estado'},
            'date_created': {'type': 'TIMESTAMP', 'nullable': False, 'description': 'Fecha de creación'},
            'date_modified': {'type': 'TIMESTAMP', 'nullable': True, 'description': 'Fecha de modificación'}
        },
        'quality_rules': {'critical_fields': ['carrier_id', 'carrier_name']}
    },
    'wms_logistic_delivery_planning': {
        'description': 'Planificación de entregas',
        'source_tables': ['metro_delivery_planning_clean'],
        'primary_key': ['planning_id'],
        'partition_by': ['date_start'],
        'fields': {
            'planning_id': {'type': 'VARCHAR(50)', 'nullable': False, 'description': 'ID de planificación'},
            'store_id': {'type': 'VARCHAR(50)', 'nullable': False, 'description': 'ID de la tienda'},
            'date_start': {'type': 'TIMESTAMP', 'nullable': False, 'description': 'Fecha inicio'},
            'date_end': {'type': 'TIMESTAMP', 'nullable': False, 'description': 'Fecha fin'},
            'capacity': {'type': 'INTEGER', 'nullable': False, 'description': 'Capacidad'},
            'available': {'type': 'INTEGER', 'nullable': False, 'description': 'Disponible'},
            'reserved': {'type': 'INTEGER', 'nullable': False, 'description': 'Reservado'},
            'date_created': {'type': 'TIMESTAMP', 'nullable': False, 'description': 'Fecha de creación'},
            'date_modified': {'type': 'TIMESTAMP', 'nullable': True, 'description': 'Fecha de modificación'}
        },
        'quality_rules': {'critical_fields': ['planning_id', 'store_id'], 'numeric_ranges': {'capacity': {'min': 0, 'max': 999999}}}
    },
    'wms_logistic_delivery_ranges': {
        'description': 'Rangos horarios de entrega',
        'source_tables': ['metro_delivery_ranges_clean'],
        'primary_key': ['range_id'],
        'partition_by': [],
        'fields': {
            'range_id': {'type': 'VARCHAR(50)', 'nullable': False, 'description': 'ID del rango'},
            'planning_id': {'type': 'VARCHAR(50)', 'nullable': False, 'description': 'ID de planificación'},
            'time_start': {'type': 'VARCHAR(10)', 'nullable': False, 'description': 'Hora inicio (HH:MM)'},
            'time_end': {'type': 'VARCHAR(10)', 'nullable': False, 'description': 'Hora fin (HH:MM)'},
            'date_created': {'type': 'TIMESTAMP', 'nullable': False, 'description': 'Fecha de creación'},
            'date_modified': {'type': 'TIMESTAMP', 'nullable': True, 'description': 'Fecha de modificación'}
        },
        'quality_rules': {'critical_fields': ['range_id', 'planning_id']}
    },
    'categories': {
        'description': 'Categorías de productos',
        'source_tables': ['metro_categories_clean'],
        'primary_key': ['category_id'],
        'partition_by': [],
        'fields': {
            'category_id': {'type': 'VARCHAR(50)', 'nullable': False, 'description': 'ID de categoría'},
            'category_name': {'type': 'VARCHAR(255)', 'nullable': False, 'description': 'Nombre de categoría'},
            'ref_id': {'type': 'VARCHAR(50)', 'nullable': True, 'description': 'ID de referencia'},
            'status': {'type': 'VARCHAR(50)', 'nullable': False, 'description': 'Estado'},
            'date_created': {'type': 'TIMESTAMP', 'nullable': False, 'description': 'Fecha de creación'}
        },
        'quality_rules': {'critical_fields': ['category_id', 'category_name']}
    },
    'brands': {
        'description': 'Marcas de productos',
        'source_tables': ['metro_brands_clean'],
        'primary_key': ['brand_id'],
        'partition_by': [],
        'fields': {
            'brand_id': {'type': 'VARCHAR(50)', 'nullable': False, 'description': 'ID de marca'},
            'brand_name': {'type': 'VARCHAR(255)', 'nullable': False, 'description': 'Nombre de marca'},
            'status': {'type': 'VARCHAR(50)', 'nullable': False, 'description': 'Estado'},
            'date_created': {'type': 'TIMESTAMP', 'nullable': False, 'description': 'Fecha de creación'}
        },
        'quality_rules': {'critical_fields': ['brand_id', 'brand_name']}
    }
}

data['tables'].update(more_tables)


# Final tables
final_tables = {
    'price': {
        'description': 'Precios de productos',
        'source_tables': ['metro_prices_clean'],
        'primary_key': ['price_id'],
        'partition_by': ['date_created'],
        'fields': {
            'price_id': {'type': 'VARCHAR(50)', 'nullable': False, 'description': 'ID del precio'},
            'sku': {'type': 'VARCHAR(100)', 'nullable': False, 'description': 'SKU'},
            'store_id': {'type': 'VARCHAR(50)', 'nullable': False, 'description': 'ID de tienda'},
            'price': {'type': 'DECIMAL(18,2)', 'nullable': False, 'description': 'Precio'},
            'list_price': {'type': 'DECIMAL(18,2)', 'nullable': True, 'description': 'Precio de lista'},
            'currency': {'type': 'VARCHAR(10)', 'nullable': False, 'description': 'Moneda'},
            'date_created': {'type': 'TIMESTAMP', 'nullable': False, 'description': 'Fecha de creación'},
            'date_modified': {'type': 'TIMESTAMP', 'nullable': True, 'description': 'Fecha de modificación'},
            'status': {'type': 'VARCHAR(50)', 'nullable': False, 'description': 'Estado'}
        },
        'quality_rules': {'critical_fields': ['price_id', 'sku', 'price'], 'numeric_ranges': {'price': {'min': 0, 'max': 999999}}}
    },
    'promotional_prices': {
        'description': 'Precios promocionales',
        'source_tables': ['metro_promotional_prices_clean'],
        'primary_key': ['promo_price_id'],
        'partition_by': ['date_start'],
        'fields': {
            'promo_price_id': {'type': 'VARCHAR(50)', 'nullable': False, 'description': 'ID del precio promocional'},
            'sku': {'type': 'VARCHAR(100)', 'nullable': False, 'description': 'SKU'},
            'store_id': {'type': 'VARCHAR(50)', 'nullable': False, 'description': 'ID de tienda'},
            'promotional_price': {'type': 'DECIMAL(18,2)', 'nullable': False, 'description': 'Precio promocional'},
            'original_price': {'type': 'DECIMAL(18,2)', 'nullable': False, 'description': 'Precio original'},
            'discount_percentage': {'type': 'DECIMAL(5,2)', 'nullable': True, 'description': 'Porcentaje de descuento'},
            'date_start': {'type': 'TIMESTAMP', 'nullable': False, 'description': 'Fecha inicio'},
            'date_end': {'type': 'TIMESTAMP', 'nullable': False, 'description': 'Fecha fin'},
            'status': {'type': 'VARCHAR(50)', 'nullable': False, 'description': 'Estado'},
            'date_created': {'type': 'TIMESTAMP', 'nullable': False, 'description': 'Fecha de creación'},
            'date_modified': {'type': 'TIMESTAMP', 'nullable': True, 'description': 'Fecha de modificación'}
        },
        'quality_rules': {'critical_fields': ['promo_price_id', 'sku'], 'numeric_ranges': {'promotional_price': {'min': 0, 'max': 999999}}}
    },
    'promotions': {
        'description': 'Promociones',
        'source_tables': ['metro_promotions_clean'],
        'primary_key': ['promotion_id'],
        'partition_by': ['date_start'],
        'fields': {
            'promotion_id': {'type': 'VARCHAR(50)', 'nullable': False, 'description': 'ID de promoción'},
            'promotion_name': {'type': 'VARCHAR(255)', 'nullable': False, 'description': 'Nombre de promoción'},
            'description': {'type': 'VARCHAR(1000)', 'nullable': True, 'description': 'Descripción'},
            'discount_type': {'type': 'VARCHAR(50)', 'nullable': False, 'description': 'Tipo de descuento'},
            'discount_value': {'type': 'DECIMAL(18,2)', 'nullable': False, 'description': 'Valor de descuento'},
            'date_start': {'type': 'TIMESTAMP', 'nullable': False, 'description': 'Fecha inicio'},
            'date_end': {'type': 'TIMESTAMP', 'nullable': False, 'description': 'Fecha fin'},
            'status': {'type': 'VARCHAR(50)', 'nullable': False, 'description': 'Estado'},
            'date_created': {'type': 'TIMESTAMP', 'nullable': False, 'description': 'Fecha de creación'},
            'date_modified': {'type': 'TIMESTAMP', 'nullable': True, 'description': 'Fecha de modificación'}
        },
        'quality_rules': {'critical_fields': ['promotion_id', 'promotion_name']}
    },
    'admins': {
        'description': 'Administradores del sistema',
        'source_tables': ['metro_admins_clean'],
        'primary_key': ['admin_id'],
        'partition_by': [],
        'fields': {
            'admin_id': {'type': 'VARCHAR(50)', 'nullable': False, 'description': 'ID del administrador'},
            'first_name': {'type': 'VARCHAR(100)', 'nullable': False, 'description': 'Nombre'},
            'last_name': {'type': 'VARCHAR(100)', 'nullable': False, 'description': 'Apellido'},
            'email': {'type': 'VARCHAR(255)', 'nullable': False, 'description': 'Email'},
            'document': {'type': 'VARCHAR(50)', 'nullable': True, 'description': 'Documento'},
            'status': {'type': 'VARCHAR(50)', 'nullable': False, 'description': 'Estado'},
            'date_created': {'type': 'TIMESTAMP', 'nullable': False, 'description': 'Fecha de creación'}
        },
        'quality_rules': {'critical_fields': ['admin_id', 'email']}
    },
    'customers': {
        'description': 'Clientes',
        'source_tables': ['metro_customers_clean'],
        'primary_key': ['customer_id'],
        'partition_by': ['date_created'],
        'fields': {
            'customer_id': {'type': 'VARCHAR(50)', 'nullable': False, 'description': 'ID del cliente'},
            'first_name': {'type': 'VARCHAR(100)', 'nullable': False, 'description': 'Nombre'},
            'last_name': {'type': 'VARCHAR(100)', 'nullable': False, 'description': 'Apellido'},
            'email': {'type': 'VARCHAR(255)', 'nullable': False, 'description': 'Email'},
            'phone': {'type': 'VARCHAR(50)', 'nullable': True, 'description': 'Teléfono'},
            'document': {'type': 'VARCHAR(50)', 'nullable': True, 'description': 'Documento'},
            'document_type': {'type': 'VARCHAR(20)', 'nullable': True, 'description': 'Tipo de documento'},
            'status': {'type': 'VARCHAR(50)', 'nullable': False, 'description': 'Estado'},
            'date_created': {'type': 'TIMESTAMP', 'nullable': False, 'description': 'Fecha de creación'},
            'date_modified': {'type': 'TIMESTAMP', 'nullable': True, 'description': 'Fecha de modificación'}
        },
        'quality_rules': {'critical_fields': ['customer_id', 'email']}
    },
    'wms_order_picking': {
        'description': 'Sesiones de picking',
        'source_tables': ['metro_picking_sessions_clean'],
        'primary_key': ['session_id'],
        'partition_by': ['pick_start_time'],
        'fields': {
            'session_id': {'type': 'VARCHAR(50)', 'nullable': False, 'description': 'ID de sesión'},
            'order_id': {'type': 'VARCHAR(50)', 'nullable': False, 'description': 'ID de orden'},
            'picker': {'type': 'VARCHAR(100)', 'nullable': True, 'description': 'Picker'},
            'pick_start_time': {'type': 'TIMESTAMP', 'nullable': False, 'description': 'Hora inicio picking'},
            'pick_end_time': {'type': 'TIMESTAMP', 'nullable': True, 'description': 'Hora fin picking'},
            'status': {'type': 'VARCHAR(50)', 'nullable': False, 'description': 'Estado'}
        },
        'quality_rules': {'critical_fields': ['session_id', 'order_id']}
    },
    'picking_round_orders': {
        'description': 'Órdenes en rondas de picking',
        'source_tables': ['metro_picking_round_orders_clean'],
        'primary_key': ['session_id', 'order_id'],
        'partition_by': [],
        'fields': {
            'session_id': {'type': 'VARCHAR(50)', 'nullable': False, 'description': 'ID de sesión'},
            'order_id': {'type': 'VARCHAR(50)', 'nullable': False, 'description': 'ID de orden'}
        },
        'quality_rules': {'critical_fields': ['session_id', 'order_id']}
    },
    'invoices': {
        'description': 'Facturas',
        'source_tables': ['metro_invoices_clean'],
        'primary_key': ['invoice_id'],
        'partition_by': ['date_created'],
        'fields': {
            'invoice_id': {'type': 'VARCHAR(50)', 'nullable': False, 'description': 'ID de factura'},
            'order_id': {'type': 'VARCHAR(50)', 'nullable': False, 'description': 'ID de orden'},
            'invoice_number': {'type': 'VARCHAR(100)', 'nullable': False, 'description': 'Número de factura'},
            'amount': {'type': 'DECIMAL(18,2)', 'nullable': False, 'description': 'Monto'},
            'status': {'type': 'VARCHAR(50)', 'nullable': False, 'description': 'Estado'},
            'date_created': {'type': 'TIMESTAMP', 'nullable': False, 'description': 'Fecha de creación'}
        },
        'quality_rules': {'critical_fields': ['invoice_id', 'order_id'], 'numeric_ranges': {'amount': {'min': 0, 'max': 999999}}}
    },
    'ff_comments': {
        'description': 'Comentarios de fulfillment',
        'source_tables': ['metro_comments_clean'],
        'primary_key': ['comment_id'],
        'partition_by': ['date_created'],
        'fields': {
            'comment_id': {'type': 'VARCHAR(50)', 'nullable': False, 'description': 'ID del comentario'},
            'order_id': {'type': 'VARCHAR(50)', 'nullable': False, 'description': 'ID de orden'},
            'user_id': {'type': 'VARCHAR(50)', 'nullable': True, 'description': 'ID de usuario'},
            'comment_text': {'type': 'VARCHAR(2000)', 'nullable': False, 'description': 'Texto del comentario'},
            'comment_type': {'type': 'VARCHAR(50)', 'nullable': True, 'description': 'Tipo de comentario'},
            'date_created': {'type': 'TIMESTAMP', 'nullable': False, 'description': 'Fecha de creación'},
            'date_modified': {'type': 'TIMESTAMP', 'nullable': True, 'description': 'Fecha de modificación'}
        },
        'quality_rules': {'critical_fields': ['comment_id', 'order_id']}
    }
}

data['tables'].update(final_tables)

# Write back
with open('max/glue/etl-silver-to-gold/config/redshift_schemas.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print(f'Successfully added all remaining tables. Total tables: {len(data["tables"])}')
