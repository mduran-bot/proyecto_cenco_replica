"""
DataValidator - Validador de datos para el Sistema de Polling de APIs de Janis.

Este módulo implementa validación de esquemas JSON, detección de duplicados
en lote y validación de reglas de negocio para las 5 entidades principales:
orders, products, stock, prices, stores.

Requirements:
- 8.1: Cargar esquemas JSON y validar con jsonschema
- 8.2: Implementar validate_batch
- 8.3: Detección de duplicados en lote
- 8.4: Validación de reglas de negocio
- 8.5: Emitir métricas de validación
"""

import json
import logging
import os
from typing import Dict, List, Optional, Tuple

import jsonschema
from jsonschema import Draft7Validator, ValidationError

logger = logging.getLogger(__name__)

# Reglas de negocio por entidad
BUSINESS_RULES = {
    "orders": [
        {
            "name": "total_amount_positive",
            "description": "El monto total de la orden debe ser mayor a 0",
            "validate": lambda record: record.get("totalAmount", 0) > 0,
            "error": "totalAmount debe ser mayor a 0"
        },
        {
            "name": "items_not_empty",
            "description": "La orden debe tener al menos un ítem",
            "validate": lambda record: len(record.get("items", [])) > 0,
            "error": "La orden debe contener al menos un ítem"
        },
        {
            "name": "item_quantities_positive",
            "description": "La cantidad de cada ítem debe ser mayor a 0",
            "validate": lambda record: all(
                item.get("purchasedQuantity", 0) > 0
                for item in record.get("items", [])
            ),
            "error": "Todos los ítems deben tener purchasedQuantity > 0"
        }
    ],
    "products": [
        {
            "name": "name_not_empty",
            "description": "El nombre del producto no puede estar vacío",
            "validate": lambda record: bool(record.get("name", "").strip()),
            "error": "El campo name no puede estar vacío"
        },
        {
            "name": "reference_id_not_empty",
            "description": "El referenceId no puede estar vacío",
            "validate": lambda record: bool(record.get("referenceId", "").strip()),
            "error": "El campo referenceId no puede estar vacío"
        }
    ],
    "stock": [
        {
            "name": "quantity_non_negative",
            "description": "La cantidad en stock no puede ser negativa",
            "validate": lambda record: record.get("quantity", 0) >= 0,
            "error": "quantity no puede ser negativo"
        },
        {
            "name": "available_lte_quantity",
            "description": "La cantidad disponible no puede superar la cantidad total",
            "validate": lambda record: (
                record.get("availableQuantity") is None or
                record.get("availableQuantity", 0) <= record.get("quantity", 0)
            ),
            "error": "availableQuantity no puede ser mayor que quantity"
        }
    ],
    "prices": [
        {
            "name": "price_positive",
            "description": "El precio debe ser mayor a 0",
            "validate": lambda record: record.get("price", 0) > 0,
            "error": "price debe ser mayor a 0"
        },
        {
            "name": "valid_dates_order",
            "description": "validFrom debe ser anterior a validTo si ambos están presentes",
            "validate": lambda record: (
                record.get("validFrom") is None or
                record.get("validTo") is None or
                record.get("validFrom") <= record.get("validTo")
            ),
            "error": "validFrom debe ser anterior o igual a validTo"
        }
    ],
    "stores": [
        {
            "name": "name_not_empty",
            "description": "El nombre de la tienda no puede estar vacío",
            "validate": lambda record: bool(record.get("name", "").strip()),
            "error": "El campo name no puede estar vacío"
        },
        {
            "name": "reference_id_not_empty",
            "description": "El referenceId no puede estar vacío",
            "validate": lambda record: bool(record.get("referenceId", "").strip()),
            "error": "El campo referenceId no puede estar vacío"
        }
    ],
    "janis-order-history": [
        {
            "name": "type_valid",
            "description": "El tipo de evento debe ser válido",
            "validate": lambda record: record.get("type") in ["statusChange", "milestone", "note", "other"],
            "error": "type debe ser uno de: statusChange, milestone, note, other"
        },
        {
            "name": "name_not_empty",
            "description": "El nombre del evento no puede estar vacío",
            "validate": lambda record: bool(record.get("name", "").strip()),
            "error": "El campo name no puede estar vacío"
        }
    ]
}


class DataValidator:
    """
    Validador de datos para las 5 entidades principales del sistema de polling.

    Responsabilidades:
    - Cargar esquemas JSON desde archivos de configuración
    - Validar registros contra esquemas con jsonschema (Draft7)
    - Detectar duplicados dentro de un lote
    - Aplicar reglas de negocio específicas por entidad
    - Reportar métricas de validación

    Attributes:
        data_type (str): Tipo de entidad a validar (orders, products, stock, prices, stores)
        schema (dict): Esquema JSON cargado desde archivo
        validator (Draft7Validator): Validador de jsonschema configurado
        schemas_dir (str): Directorio donde residen los archivos de esquema
    """

    SUPPORTED_DATA_TYPES = {"orders", "products", "stock", "prices", "stores", "janis-order-history"}

    def __init__(self, data_type: str, schemas_dir: Optional[str] = None):
        """
        Inicializa el validador para el tipo de dato especificado.

        Args:
            data_type: Tipo de entidad a validar. Debe ser uno de:
                       orders, products, stock, prices, stores
            schemas_dir: Directorio donde están los archivos de esquema JSON.
                         Por defecto usa el directorio 'schemas' relativo a este archivo.

        Raises:
            ValueError: Si data_type no está soportado
            FileNotFoundError: Si el archivo de esquema no se encuentra
            json.JSONDecodeError: Si el archivo de esquema tiene formato inválido
        """
        if data_type not in self.SUPPORTED_DATA_TYPES:
            raise ValueError(
                f"data_type '{data_type}' no soportado. "
                f"Valores válidos: {self.SUPPORTED_DATA_TYPES}"
            )

        self.data_type = data_type

        # Resolver directorio de schemas
        if schemas_dir is None:
            schemas_dir = os.path.join(os.path.dirname(__file__), "schemas")
        self.schemas_dir = schemas_dir

        # Cargar schema
        self.schema = self._load_schema()

        # Crear validador Draft7
        self.validator = Draft7Validator(self.schema)

        logger.info(
            f"DataValidator inicializado para '{data_type}' "
            f"con schema desde '{self.schemas_dir}'"
        )

    def _load_schema(self) -> Dict:
        """
        Carga el esquema JSON desde el archivo correspondiente al data_type.

        Returns:
            Dict: Esquema JSON parseado

        Raises:
            FileNotFoundError: Si el archivo no existe
            json.JSONDecodeError: Si el JSON es inválido
        """
        schema_path = os.path.join(self.schemas_dir, f"{self.data_type}.json")

        if not os.path.exists(schema_path):
            raise FileNotFoundError(
                f"Archivo de esquema no encontrado: {schema_path}"
            )

        with open(schema_path, "r", encoding="utf-8") as f:
            schema = json.load(f)

        logger.debug(f"Schema cargado desde {schema_path}")
        return schema

    def validate_record(self, record: Dict) -> Tuple[bool, List[str]]:
        """
        Valida un único registro contra el esquema y las reglas de negocio.

        Args:
            record: Registro a validar

        Returns:
            Tuple[bool, List[str]]: (es_válido, lista_de_errores)
        """
        errors = []

        # 1. Validación de esquema JSON
        schema_errors = list(self.validator.iter_errors(record))
        for error in schema_errors:
            path = " -> ".join(str(p) for p in error.absolute_path) if error.absolute_path else "root"
            errors.append(f"[Schema] {path}: {error.message}")

        # 2. Validación de reglas de negocio
        business_rules = BUSINESS_RULES.get(self.data_type, [])
        for rule in business_rules:
            try:
                if not rule["validate"](record):
                    errors.append(f"[BusinessRule:{rule['name']}] {rule['error']}")
            except Exception as e:
                errors.append(f"[BusinessRule:{rule['name']}] Error evaluando regla: {e}")

        is_valid = len(errors) == 0
        return is_valid, errors

    def detect_duplicates(self, records: List[Dict]) -> Tuple[List[Dict], int]:
        """
        Detecta y elimina duplicados dentro de un lote por ID.

        A diferencia de deduplicate_records (que mantiene el más reciente por
        dateModified), este método simplemente detecta IDs duplicados dentro
        del lote y conserva la primera ocurrencia, reportando cuántos fueron
        eliminados.

        Requirements:
        - 8.3: Detección de duplicados en lote

        Args:
            records: Lista de registros del lote

        Returns:
            Tuple[List[Dict], int]: (registros_sin_duplicados, cantidad_duplicados)
        """
        seen_ids = set()
        unique_records = []
        duplicate_count = 0

        for record in records:
            record_id = record.get("id")

            if record_id is None:
                # Sin ID: incluir de todas formas, no podemos deduplicar
                unique_records.append(record)
                logger.warning(f"Registro sin 'id' encontrado en lote, no se puede deduplicar")
                continue

            if record_id in seen_ids:
                duplicate_count += 1
                logger.debug(f"Duplicado detectado en lote: id={record_id}")
            else:
                seen_ids.add(record_id)
                unique_records.append(record)

        if duplicate_count > 0:
            logger.info(
                f"Detección de duplicados en lote: "
                f"{len(records)} registros → {len(unique_records)} únicos, "
                f"{duplicate_count} duplicados removidos"
            )

        return unique_records, duplicate_count

    def validate_batch(
        self, records: List[Dict]
    ) -> Tuple[List[Dict], Dict]:
        """
        Valida un lote completo de registros.

        Proceso:
        1. Detecta duplicados en el lote
        2. Valida cada registro contra el esquema JSON
        3. Aplica reglas de negocio
        4. Retorna registros válidos y métricas

        Requirements:
        - 8.1: Validar con jsonschema
        - 8.2: Implementar validate_batch
        - 8.3: Detectar duplicados en lote
        - 8.4: Validar reglas de negocio
        - 8.5: Retornar métricas de validación

        Args:
            records: Lista de registros a validar

        Returns:
            Tuple[List[Dict], Dict]: (registros_válidos, métricas)
                métricas contiene:
                - total_received: total de registros recibidos
                - duplicates_in_batch: duplicados detectados en el lote
                - total_after_dedup: registros después de deduplicar
                - valid_count: registros válidos
                - invalid_count: registros inválidos
                - validation_pass_rate: porcentaje de registros válidos (0-100)
                - invalid_records: lista con id y errores de registros inválidos

        Example:
            >>> validator = DataValidator("orders")
            >>> valid_records, metrics = validator.validate_batch(records)
            >>> print(f"Válidos: {metrics['valid_count']}/{metrics['total_received']}")
        """
        if not records:
            logger.warning("validate_batch llamado con lista vacía")
            return [], {
                "total_received": 0,
                "duplicates_in_batch": 0,
                "total_after_dedup": 0,
                "valid_count": 0,
                "invalid_count": 0,
                "validation_pass_rate": 100.0,
                "invalid_records": []
            }

        total_received = len(records)
        logger.info(f"Iniciando validación de lote: {total_received} registros ({self.data_type})")

        # Paso 1: Detectar y eliminar duplicados en el lote
        unique_records, duplicate_count = self.detect_duplicates(records)
        total_after_dedup = len(unique_records)

        # Paso 2: Validar cada registro
        valid_records = []
        invalid_records_info = []

        for record in unique_records:
            is_valid, errors = self.validate_record(record)

            if is_valid:
                valid_records.append(record)
            else:
                record_id = record.get("id", "UNKNOWN")
                invalid_records_info.append({
                    "id": record_id,
                    "errors": errors
                })
                logger.debug(
                    f"Registro inválido id={record_id}: {errors}"
                )

        valid_count = len(valid_records)
        invalid_count = len(invalid_records_info)

        # Calcular tasa de validación
        validation_pass_rate = (
            (valid_count / total_after_dedup * 100)
            if total_after_dedup > 0 else 100.0
        )

        metrics = {
            "total_received": total_received,
            "duplicates_in_batch": duplicate_count,
            "total_after_dedup": total_after_dedup,
            "valid_count": valid_count,
            "invalid_count": invalid_count,
            "validation_pass_rate": round(validation_pass_rate, 2),
            "invalid_records": invalid_records_info
        }

        logger.info(
            f"Validación de lote completada ({self.data_type}): "
            f"total={total_received}, "
            f"duplicados={duplicate_count}, "
            f"válidos={valid_count}, "
            f"inválidos={invalid_count}, "
            f"tasa={validation_pass_rate:.2f}%"
        )

        if invalid_count > 0:
            logger.warning(
                f"{invalid_count} registros inválidos en el lote de {self.data_type}. "
                f"Ver 'invalid_records' en métricas para detalle."
            )

        return valid_records, metrics
