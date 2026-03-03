#!/usr/bin/env python3
"""
Script para ejecutar el pipeline Silver-to-Gold para las 26 tablas Gold en secuencia

Este script:
1. Lee la lista de tablas desde redshift_schemas.json
2. Ejecuta run_pipeline_to_gold.py para cada tabla
3. Registra métricas de éxito/fallo por tabla
4. Genera un reporte final con estadísticas

Uso:
    python run_silver_to_gold_all.py --client metro
    python run_silver_to_gold_all.py --client wongio --tables wms_orders,products,stock
"""

import sys
import os
import json
import subprocess
import logging
import argparse
from datetime import datetime
from typing import List, Dict, Tuple

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f'silver_to_gold_all_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
    ]
)
logger = logging.getLogger('SilverToGoldAll')


def load_redshift_schemas(config_path: str = "../src/config/redshift_schemas.json") -> dict:
    """Carga el archivo de esquemas Redshift"""
    with open(config_path, 'r') as f:
        return json.load(f)


def get_all_gold_tables(schemas: dict) -> List[str]:
    """Obtiene la lista de todas las tablas Gold"""
    return list(schemas.get("tables", {}).keys())


def run_pipeline_for_table(gold_table: str, client: str, config_path: str) -> Tuple[bool, str, float]:
    """
    Ejecuta el pipeline Silver-to-Gold para una tabla específica
    
    Args:
        gold_table: Nombre de la tabla Gold
        client: Cliente (metro o wongio)
        config_path: Ruta al archivo de configuración
        
    Returns:
        Tuple[bool, str, float]: (success, error_message, duration_seconds)
    """
    logger.info(f"{'='*60}")
    logger.info(f"Procesando tabla: {gold_table} (cliente: {client})")
    logger.info(f"{'='*60}")
    
    start_time = datetime.now()
    
    try:
        # Construir comando
        cmd = [
            sys.executable,
            "../src/etl-silver-to-gold/run_pipeline_to_gold.py",
            "--gold-table", gold_table,
            "--client", client,
            "--config-path", config_path
        ]
        
        logger.info(f"Ejecutando: {' '.join(cmd)}")
        
        # Ejecutar pipeline
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=600  # 10 minutos timeout
        )
        
        duration = (datetime.now() - start_time).total_seconds()
        
        if result.returncode == 0:
            logger.info(f"✅ {gold_table} completado exitosamente en {duration:.2f}s")
            return True, "", duration
        else:
            error_msg = result.stderr or result.stdout
            logger.error(f"❌ {gold_table} falló: {error_msg}")
            return False, error_msg, duration
            
    except subprocess.TimeoutExpired:
        duration = (datetime.now() - start_time).total_seconds()
        error_msg = f"Timeout después de {duration:.2f}s"
        logger.error(f"❌ {gold_table} falló: {error_msg}")
        return False, error_msg, duration
        
    except Exception as e:
        duration = (datetime.now() - start_time).total_seconds()
        error_msg = str(e)
        logger.error(f"❌ {gold_table} falló: {error_msg}")
        return False, error_msg, duration


def generate_report(results: Dict[str, Dict], client: str) -> None:
    """
    Genera un reporte final con estadísticas
    
    Args:
        results: Diccionario con resultados por tabla
        client: Cliente procesado
    """
    logger.info(f"\n{'='*60}")
    logger.info(f"REPORTE FINAL - Cliente: {client}")
    logger.info(f"{'='*60}\n")
    
    total_tables = len(results)
    successful = sum(1 for r in results.values() if r['success'])
    failed = total_tables - successful
    total_duration = sum(r['duration'] for r in results.values())
    
    logger.info(f"Total de tablas procesadas: {total_tables}")
    logger.info(f"Exitosas: {successful} ({successful/total_tables*100:.1f}%)")
    logger.info(f"Fallidas: {failed} ({failed/total_tables*100:.1f}%)")
    logger.info(f"Duración total: {total_duration:.2f}s ({total_duration/60:.1f} minutos)")
    logger.info(f"Duración promedio por tabla: {total_duration/total_tables:.2f}s")
    
    if failed > 0:
        logger.info(f"\n{'='*60}")
        logger.info("TABLAS FALLIDAS:")
        logger.info(f"{'='*60}")
        for table, result in results.items():
            if not result['success']:
                logger.error(f"  - {table}: {result['error']}")
    
    # Guardar reporte en JSON
    report_file = f"silver_to_gold_report_{client}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w') as f:
        json.dump({
            'client': client,
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total_tables': total_tables,
                'successful': successful,
                'failed': failed,
                'total_duration_seconds': total_duration,
                'average_duration_seconds': total_duration / total_tables
            },
            'results': results
        }, f, indent=2)
    
    logger.info(f"\nReporte guardado en: {report_file}")


def main():
    parser = argparse.ArgumentParser(
        description='Ejecutar pipeline Silver-to-Gold para todas las tablas Gold'
    )
    parser.add_argument(
        '--client',
        type=str,
        default='metro',
        choices=['metro', 'wongio'],
        help='Cliente a procesar (metro o wongio)'
    )
    parser.add_argument(
        '--tables',
        type=str,
        default=None,
        help='Lista de tablas separadas por coma (ej: wms_orders,products,stock). Si no se especifica, procesa todas'
    )
    parser.add_argument(
        '--config-path',
        type=str,
        default='../src/etl-silver-to-gold/config/silver-to-gold-config.json',
        help='Ruta al archivo de configuración'
    )
    parser.add_argument(
        '--continue-on-error',
        action='store_true',
        help='Continuar procesando aunque una tabla falle'
    )
    
    args = parser.parse_args()
    
    logger.info(f"{'='*60}")
    logger.info(f"PIPELINE SILVER → GOLD - TODAS LAS TABLAS")
    logger.info(f"Cliente: {args.client}")
    logger.info(f"{'='*60}\n")
    
    # Cargar esquemas
    schemas = load_redshift_schemas()
    
    # Determinar qué tablas procesar
    if args.tables:
        tables_to_process = [t.strip() for t in args.tables.split(',')]
        logger.info(f"Procesando tablas específicas: {tables_to_process}")
    else:
        tables_to_process = get_all_gold_tables(schemas)
        logger.info(f"Procesando todas las {len(tables_to_process)} tablas Gold")
    
    # Validar que las tablas existan
    all_tables = get_all_gold_tables(schemas)
    invalid_tables = [t for t in tables_to_process if t not in all_tables]
    if invalid_tables:
        logger.error(f"Tablas inválidas: {invalid_tables}")
        logger.error(f"Tablas válidas: {all_tables}")
        return 1
    
    # Ejecutar pipeline para cada tabla
    results = {}
    start_time = datetime.now()
    
    for i, table in enumerate(tables_to_process, 1):
        logger.info(f"\n[{i}/{len(tables_to_process)}] Procesando {table}...")
        
        success, error, duration = run_pipeline_for_table(
            table,
            args.client,
            args.config_path
        )
        
        results[table] = {
            'success': success,
            'error': error,
            'duration': duration
        }
        
        # Si falla y no está habilitado continue-on-error, detener
        if not success and not args.continue_on_error:
            logger.error(f"\nPipeline detenido debido a fallo en {table}")
            logger.error("Use --continue-on-error para continuar procesando aunque fallen tablas")
            break
    
    total_duration = (datetime.now() - start_time).total_seconds()
    
    # Generar reporte final
    generate_report(results, args.client)
    
    # Retornar código de salida
    failed_count = sum(1 for r in results.values() if not r['success'])
    return 0 if failed_count == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
