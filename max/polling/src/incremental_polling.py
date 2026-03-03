"""
Incremental Polling Logic for API Polling System

This module provides functions for incremental polling, including building
filters based on last execution timestamps and deduplicating records.

Requirements:
- 4.1: Use dateModified filter with last_successful_execution
- 4.2: Subtract 1 minute for overlap window
- 4.3: Handle first execution (full refresh)
- 4.4: Deduplicate records based on ID and modification timestamp
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


def build_incremental_filter(
    state_manager,
    key: str
) -> Dict:
    """
    Construye filtro incremental basado en última ejecución exitosa.
    
    Esta función consulta DynamoDB para obtener el timestamp de la última
    modificación procesada y construye un filtro para obtener solo registros
    nuevos o modificados desde entonces. Incluye una ventana de solapamiento
    de 1 minuto para asegurar que no se pierdan registros.
    
    Multi-tenant support: Accepts composite key "{data_type}-{client}" to support
    independent polling per client.
    
    Requirements:
    - 4.1: Use dateModified filter with last_successful_execution
    - 4.2: Subtract 1 minute for overlap window
    - 4.3: Handle first execution (full refresh)
    
    Args:
        state_manager: Instancia de StateManager para consultar DynamoDB
        key: Composite key for multi-tenant support (e.g., "orders-metro")
             or simple data_type for single-tenant (e.g., "orders")
    
    Returns:
        Dict: Filtro para la consulta API con los siguientes campos:
            - dateModified: Timestamp ISO desde el cual obtener registros (si existe)
            - sortBy: Campo por el cual ordenar (siempre 'dateModified')
            - sortOrder: Orden de los resultados (siempre 'asc')
            
            Si es la primera ejecución, retorna un dict vacío para full refresh.
    
    Example:
        >>> from state_manager import StateManager
        >>> state_mgr = StateManager("polling_control")
        >>> # Multi-tenant usage
        >>> filters = build_incremental_filter(state_mgr, "orders-metro")
        >>> # Single-tenant usage (backward compatible)
        >>> filters = build_incremental_filter(state_mgr, "orders")
        >>> # Primera ejecución: {}
        >>> # Ejecuciones subsecuentes: {
        >>> #     'dateModified': '2024-01-15T10:24:00Z',
        >>> #     'sortBy': 'dateModified',
        >>> #     'sortOrder': 'asc'
        >>> # }
    """
    try:
        # Obtener el timestamp de última modificación desde DynamoDB
        last_modified = state_manager.get_last_modified_date(key)
        
        # Si no existe timestamp previo, es la primera ejecución (full refresh)
        if not last_modified:
            logger.info(
                f"No se encontró last_modified_date para {key}. "
                "Realizando full refresh (sin filtro incremental)."
            )
            return {}
        
        # Parsear el timestamp ISO
        try:
            last_dt = datetime.fromisoformat(last_modified.replace('Z', '+00:00'))
        except ValueError as e:
            logger.error(
                f"Error parseando last_modified_date '{last_modified}' para {key}: {e}. "
                "Realizando full refresh."
            )
            return {}
        
        # Restar 1 minuto para crear ventana de solapamiento
        # Esto asegura que no se pierdan registros que pudieron haberse modificado
        # justo en el momento de la última ejecución
        overlap_dt = last_dt - timedelta(minutes=1)
        
        # Convertir de vuelta a formato ISO
        overlap_iso = overlap_dt.isoformat().replace('+00:00', 'Z')
        
        # Construir filtro incremental
        incremental_filter = {
            'dateModified': overlap_iso,
            'sortBy': 'dateModified',
            'sortOrder': 'asc'
        }
        
        logger.info(
            f"Filtro incremental construido para {key}: "
            f"dateModified >= {overlap_iso} (ventana de solapamiento de 1 minuto aplicada)"
        )
        
        return incremental_filter
        
    except Exception as e:
        logger.error(
            f"Error construyendo filtro incremental para {key}: {e}. "
            "Realizando full refresh.",
            exc_info=True
        )
        # En caso de error, retornar filtro vacío para full refresh
        return {}


def deduplicate_records(records: List[Dict]) -> List[Dict]:
    """
    Deduplica registros basado en ID y timestamp de modificación.
    
    Cuando hay registros duplicados (mismo ID), mantiene solo el registro
    con el timestamp de modificación más reciente. Esto es necesario debido
    a la ventana de solapamiento de 1 minuto en el polling incremental.
    
    Si el registro no tiene campo 'id', usa 'dateCreated' como identificador único.
    Esto es útil para endpoints de historial o eventos que no tienen ID explícito.
    
    Requirements:
    - 4.4: Deduplicate records based on ID and modification timestamp
    
    Args:
        records: Lista de registros obtenidos de la API
    
    Returns:
        List[Dict]: Lista de registros deduplicados, manteniendo solo el más reciente
                    de cada ID único
    
    Example:
        >>> records = [
        ...     {'id': '123', 'dateModified': '2024-01-15T10:25:00Z', 'status': 'pending'},
        ...     {'id': '123', 'dateModified': '2024-01-15T10:26:00Z', 'status': 'completed'},
        ...     {'id': '456', 'dateModified': '2024-01-15T10:25:00Z', 'status': 'pending'}
        ... ]
        >>> deduplicated = deduplicate_records(records)
        >>> # Resultado: [
        >>> #     {'id': '123', 'dateModified': '2024-01-15T10:26:00Z', 'status': 'completed'},
        >>> #     {'id': '456', 'dateModified': '2024-01-15T10:25:00Z', 'status': 'pending'}
        >>> # ]
    """
    if not records:
        logger.debug("No hay registros para deduplicar")
        return []
    
    # Diccionario para rastrear el registro más reciente de cada ID
    seen = {}
    duplicate_count = 0
    records_without_id = 0
    
    for record in records:
        record_id = record.get('id')
        
        # Si el registro no tiene ID, intentar usar dateCreated como identificador único
        if not record_id:
            date_created = record.get('dateCreated')
            if date_created:
                # Usar dateCreated como ID único para eventos de historial
                record_id = f"dateCreated_{date_created}"
                records_without_id += 1
            else:
                logger.warning(
                    f"Registro sin ID ni dateCreated encontrado, no se puede deduplicar: {record}"
                )
                continue
        
        modified_date = record.get('dateModified') or record.get('dateCreated')
        
        # Si el registro no tiene dateModified ni dateCreated, usar el registro actual
        if not modified_date:
            logger.warning(
                f"Registro {record_id} sin dateModified ni dateCreated, "
                "no se puede comparar timestamps para deduplicación"
            )
            # Si no existe en seen, agregarlo
            if record_id not in seen:
                seen[record_id] = record
            continue
        
        # Si es la primera vez que vemos este ID, agregarlo
        if record_id not in seen:
            seen[record_id] = record
        else:
            # Comparar timestamps y mantener el más reciente
            existing_date = seen[record_id].get('dateModified') or seen[record_id].get('dateCreated')
            
            # Si el registro existente no tiene timestamp, reemplazarlo
            if not existing_date:
                seen[record_id] = record
                duplicate_count += 1
                logger.debug(
                    f"Reemplazando registro {record_id} sin timestamp "
                    f"con registro con timestamp {modified_date}"
                )
            # Si el nuevo registro es más reciente, reemplazarlo
            elif modified_date > existing_date:
                seen[record_id] = record
                duplicate_count += 1
                logger.debug(
                    f"Registro duplicado {record_id}: "
                    f"manteniendo versión más reciente ({modified_date} > {existing_date})"
                )
            else:
                # El registro existente es más reciente o igual, mantenerlo
                duplicate_count += 1
                logger.debug(
                    f"Registro duplicado {record_id}: "
                    f"manteniendo versión existente ({existing_date} >= {modified_date})"
                )
    
    deduplicated = list(seen.values())
    
    if records_without_id > 0:
        logger.info(
            f"Se usó dateCreated como ID para {records_without_id} registros sin campo 'id'"
        )
    
    if duplicate_count > 0:
        logger.info(
            f"Deduplicación completada: {len(records)} registros originales, "
            f"{len(deduplicated)} registros únicos, "
            f"{duplicate_count} duplicados removidos"
        )
    else:
        logger.debug(
            f"No se encontraron duplicados en {len(records)} registros"
        )
    
    return deduplicated
