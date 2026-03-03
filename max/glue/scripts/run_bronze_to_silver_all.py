"""
Script para ejecutar Bronze-to-Silver para todas las 41 entidades en secuencia

Este script:
1. Lee la lista de entidades desde entities_mapping.json
2. Ejecuta run_pipeline_to_silver.py para cada entidad
3. Registra métricas de éxito/fallo por entidad
4. Genera un reporte final con estadísticas

Uso:
    python scripts/run_bronze_to_silver_all.py --client metro
    python scripts/run_bronze_to_silver_all.py --client wongio --parallel 4
"""

import sys
import os
import json
import logging
import argparse
import subprocess
from datetime import datetime
from typing import Dict, List, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed

# Agregar directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def setup_logging():
    """Configurar logging"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    return logging.getLogger('RunAllBronzeToSilver')


def load_entities_list(config_dir: str = "src/config") -> List[str]:
    """
    Cargar lista de entidades desde entities_mapping.json
    
    Args:
        config_dir: Directorio donde se encuentra entities_mapping.json
        
    Returns:
        Lista de nombres de entidades
    """
    entities_mapping_path = os.path.join(config_dir, "entities_mapping.json")
    
    with open(entities_mapping_path, 'r') as f:
        entities_mapping = json.load(f)
    
    return list(entities_mapping.get("entities", {}).keys())


def run_entity_pipeline(entity_type: str, client: str, config_path: str, 
                       bronze_bucket: str, silver_bucket: str, logger) -> Tuple[str, bool, str, float]:
    """
    Ejecutar pipeline Bronze-to-Silver para una entidad específica
    
    Args:
        entity_type: Tipo de entidad a procesar
        client: Cliente (metro o wongio)
        config_path: Ruta al archivo de configuración
        bronze_bucket: Nombre del bucket Bronze
        silver_bucket: Nombre del bucket Silver
        logger: Logger para mensajes
        
    Returns:
        Tupla (entity_type, success, message, duration_seconds)
    """
    start_time = datetime.now()
    
    try:
        logger.info(f"Iniciando procesamiento de entidad: {entity_type}")
        
        # Construir comando
        cmd = [
            sys.executable,  # Python interpreter
            "run_pipeline_to_silver.py",
            "--entity-type", entity_type,
            "--client", client,
            "--config-path", config_path,
            "--bronze-bucket", bronze_bucket,
            "--silver-bucket", silver_bucket
        ]
        
        # Ejecutar comando
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=3600  # 1 hour timeout
        )
        
        duration = (datetime.now() - start_time).total_seconds()
        
        if result.returncode == 0:
            logger.info(f"✅ {entity_type}: Completado exitosamente en {duration:.2f}s")
            return (entity_type, True, "Success", duration)
        else:
            error_msg = result.stderr[-500:] if result.stderr else "Unknown error"
            logger.error(f"❌ {entity_type}: Falló - {error_msg}")
            return (entity_type, False, error_msg, duration)
            
    except subprocess.TimeoutExpired:
        duration = (datetime.now() - start_time).total_seconds()
        logger.error(f"❌ {entity_type}: Timeout después de {duration:.2f}s")
        return (entity_type, False, "Timeout", duration)
        
    except Exception as e:
        duration = (datetime.now() - start_time).total_seconds()
        logger.error(f"❌ {entity_type}: Error - {str(e)}")
        return (entity_type, False, str(e), duration)


def run_sequential(entities: List[str], client: str, config_path: str,
                  bronze_bucket: str, silver_bucket: str, logger) -> List[Tuple]:
    """
    Ejecutar pipelines secuencialmente
    
    Args:
        entities: Lista de entidades a procesar
        client: Cliente (metro o wongio)
        config_path: Ruta al archivo de configuración
        bronze_bucket: Nombre del bucket Bronze
        silver_bucket: Nombre del bucket Silver
        logger: Logger para mensajes
        
    Returns:
        Lista de resultados (entity_type, success, message, duration)
    """
    results = []
    
    for entity_type in entities:
        result = run_entity_pipeline(
            entity_type, client, config_path, 
            bronze_bucket, silver_bucket, logger
        )
        results.append(result)
    
    return results


def run_parallel(entities: List[str], client: str, config_path: str,
                bronze_bucket: str, silver_bucket: str, 
                max_workers: int, logger) -> List[Tuple]:
    """
    Ejecutar pipelines en paralelo
    
    Args:
        entities: Lista de entidades a procesar
        client: Cliente (metro o wongio)
        config_path: Ruta al archivo de configuración
        bronze_bucket: Nombre del bucket Bronze
        silver_bucket: Nombre del bucket Silver
        max_workers: Número máximo de workers paralelos
        logger: Logger para mensajes
        
    Returns:
        Lista de resultados (entity_type, success, message, duration)
    """
    results = []
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Enviar todas las tareas
        future_to_entity = {
            executor.submit(
                run_entity_pipeline,
                entity_type, client, config_path,
                bronze_bucket, silver_bucket, logger
            ): entity_type
            for entity_type in entities
        }
        
        # Recolectar resultados a medida que completan
        for future in as_completed(future_to_entity):
            entity_type = future_to_entity[future]
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                logger.error(f"❌ {entity_type}: Error en ejecución paralela - {str(e)}")
                results.append((entity_type, False, str(e), 0.0))
    
    return results


def generate_report(results: List[Tuple], client: str, start_time: datetime, logger):
    """
    Generar reporte final con estadísticas
    
    Args:
        results: Lista de resultados (entity_type, success, message, duration)
        client: Cliente procesado
        start_time: Timestamp de inicio
        logger: Logger para mensajes
    """
    total_duration = (datetime.now() - start_time).total_seconds()
    
    # Calcular estadísticas
    total_entities = len(results)
    successful = sum(1 for _, success, _, _ in results if success)
    failed = total_entities - successful
    
    total_processing_time = sum(duration for _, _, _, duration in results)
    avg_duration = total_processing_time / total_entities if total_entities > 0 else 0
    
    # Imprimir reporte
    logger.info("\n" + "=" * 80)
    logger.info("REPORTE FINAL - BRONZE TO SILVER")
    logger.info("=" * 80)
    logger.info(f"Cliente: {client}")
    logger.info(f"Tiempo total de ejecución: {total_duration:.2f}s ({total_duration/60:.2f} min)")
    logger.info(f"Tiempo total de procesamiento: {total_processing_time:.2f}s")
    logger.info(f"Tiempo promedio por entidad: {avg_duration:.2f}s")
    logger.info("")
    logger.info(f"Total de entidades: {total_entities}")
    logger.info(f"✅ Exitosas: {successful} ({successful/total_entities*100:.1f}%)")
    logger.info(f"❌ Fallidas: {failed} ({failed/total_entities*100:.1f}%)")
    logger.info("")
    
    # Listar entidades exitosas
    if successful > 0:
        logger.info("Entidades procesadas exitosamente:")
        for entity_type, success, _, duration in sorted(results, key=lambda x: x[3], reverse=True):
            if success:
                logger.info(f"  ✅ {entity_type:30s} - {duration:6.2f}s")
    
    # Listar entidades fallidas
    if failed > 0:
        logger.info("")
        logger.info("Entidades con errores:")
        for entity_type, success, message, duration in results:
            if not success:
                logger.info(f"  ❌ {entity_type:30s} - {message[:50]}")
    
    logger.info("=" * 80)
    
    # Guardar reporte en archivo
    report_path = f"output/bronze_to_silver_report_{client}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    os.makedirs("output", exist_ok=True)
    
    report_data = {
        "client": client,
        "timestamp": datetime.now().isoformat(),
        "total_duration_seconds": total_duration,
        "total_processing_time_seconds": total_processing_time,
        "avg_duration_seconds": avg_duration,
        "total_entities": total_entities,
        "successful": successful,
        "failed": failed,
        "success_rate": successful/total_entities if total_entities > 0 else 0,
        "results": [
            {
                "entity_type": entity_type,
                "success": success,
                "message": message,
                "duration_seconds": duration
            }
            for entity_type, success, message, duration in results
        ]
    }
    
    with open(report_path, 'w') as f:
        json.dump(report_data, f, indent=2)
    
    logger.info(f"\nReporte guardado en: {report_path}")


def parse_arguments():
    """Parsear argumentos de línea de comandos"""
    parser = argparse.ArgumentParser(
        description='Ejecutar pipeline Bronze-to-Silver para todas las entidades'
    )
    
    parser.add_argument(
        '--client',
        type=str,
        required=True,
        choices=['metro', 'wongio'],
        help='Cliente para procesar (metro o wongio)'
    )
    
    parser.add_argument(
        '--config-path',
        type=str,
        default='src/config/bronze-to-silver-config.example.json',
        help='Ruta al archivo de configuración del pipeline'
    )
    
    parser.add_argument(
        '--bronze-bucket',
        type=str,
        default='data-lake-bronze',
        help='Nombre del bucket Bronze en S3'
    )
    
    parser.add_argument(
        '--silver-bucket',
        type=str,
        default='data-lake-silver',
        help='Nombre del bucket Silver en S3'
    )
    
    parser.add_argument(
        '--parallel',
        type=int,
        default=1,
        help='Número de entidades a procesar en paralelo (default: 1 = secuencial)'
    )
    
    parser.add_argument(
        '--entities',
        type=str,
        nargs='+',
        help='Lista específica de entidades a procesar (opcional). Si no se especifica, procesa todas.'
    )
    
    return parser.parse_args()


def main():
    """Función principal"""
    logger = setup_logging()
    start_time = datetime.now()
    
    try:
        # Parsear argumentos
        args = parse_arguments()
        
        logger.info("=" * 80)
        logger.info("EJECUTANDO PIPELINE BRONZE-TO-SILVER PARA TODAS LAS ENTIDADES")
        logger.info("=" * 80)
        logger.info(f"Cliente: {args.client}")
        logger.info(f"Modo: {'Paralelo (' + str(args.parallel) + ' workers)' if args.parallel > 1 else 'Secuencial'}")
        logger.info(f"Timestamp: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("")
        
        # Cargar lista de entidades
        if args.entities:
            entities = args.entities
            logger.info(f"Procesando {len(entities)} entidades específicas: {', '.join(entities)}")
        else:
            entities = load_entities_list()
            logger.info(f"Procesando todas las {len(entities)} entidades desde entities_mapping.json")
        
        logger.info("")
        
        # Ejecutar pipelines
        if args.parallel > 1:
            logger.info(f"Ejecutando en modo PARALELO con {args.parallel} workers...")
            results = run_parallel(
                entities, args.client, args.config_path,
                args.bronze_bucket, args.silver_bucket,
                args.parallel, logger
            )
        else:
            logger.info("Ejecutando en modo SECUENCIAL...")
            results = run_sequential(
                entities, args.client, args.config_path,
                args.bronze_bucket, args.silver_bucket, logger
            )
        
        # Generar reporte
        generate_report(results, args.client, start_time, logger)
        
        # Determinar código de salida
        failed_count = sum(1 for _, success, _, _ in results if not success)
        return 0 if failed_count == 0 else 1
        
    except Exception as e:
        logger.error("=" * 80)
        logger.error("ERROR EN LA EJECUCIÓN")
        logger.error("=" * 80)
        logger.error(f"Error: {str(e)}")
        logger.exception("Traceback completo:")
        return 1


if __name__ == "__main__":
    sys.exit(main())
