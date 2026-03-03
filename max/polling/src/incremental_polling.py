import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)

def _get_effective_id(record: Dict) -> Optional[str]:
    """Extrae el ID único del registro, usando dateCreated como fallback."""
    record_id = record.get('id')
    if not record_id:
        date_created = record.get('dateCreated')
        if date_created:
            return f"dateCreated_{date_created}"
    return record_id

def _get_effective_timestamp(record: Dict) -> Optional[str]:
    """Obtiene el timestamp de comparación (prioriza dateModified)."""
    return record.get('dateModified') or record.get('dateCreated')

def build_incremental_filter(state_manager, key: str) -> Dict:
    """Construye filtro incremental basado en última ejecución exitosa."""
    try:
        last_modified = state_manager.get_last_modified_date(key)
        
        if not last_modified:
            logger.info(f"No se encontró last_modified_date para {key}. Full refresh.")
            return {}
        
        try:
            # Reemplazo de utcnow() por now(timezone.utc) según recomendación de Sonar
            last_dt = datetime.fromisoformat(last_modified.replace('Z', '+00:00'))
        except ValueError as e:
            logger.error(f"Error parseando fecha '{last_modified}' para {key}: {e}")
            return {}
        
        overlap_iso = (last_dt - timedelta(minutes=1)).isoformat().replace('+00:00', 'Z')
        
        return {
            'dateModified': overlap_iso,
            'sortBy': 'dateModified',
            'sortOrder': 'asc'
        }
        
    except Exception as e:
        logger.error(f"Error construyendo filtro para {key}: {e}", exc_info=True)
        return {}

def deduplicate_records(records: List[Dict]) -> List[Dict]:
    """
    Deduplica registros manteniendo el más reciente. 
    Complejidad cognitiva reducida mediante sub-funciones.
    """
    if not records:
        return []

    seen = {}
    duplicate_count = 0

    for record in records:
        record_id = _get_effective_id(record)
        
        if not record_id:
            logger.warning(f"Registro sin ID identificable: {record}")
            continue

        new_ts = _get_effective_timestamp(record)
        
        if record_id not in seen:
            seen[record_id] = record
            continue

        # Lógica de comparación simplificada
        existing_ts = _get_effective_timestamp(seen[record_id])
        duplicate_count += 1

        if not existing_ts or (new_ts and new_ts > existing_ts):
            seen[record_id] = record

    if duplicate_count > 0:
        logger.info(f"Deduplicación: {len(records)} -> {len(seen)} ({duplicate_count} duplicados)")
        
    return list(seen.values())