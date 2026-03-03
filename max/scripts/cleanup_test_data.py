"""
Script de limpieza de datos de prueba

Este script:
1. Vacía buckets Bronze, Silver, Gold en LocalStack
2. Elimina tablas de prueba
3. Limpia archivos de output locales
4. Restaura el ambiente a un estado limpio

Uso:
    python cleanup_test_data.py                    # Limpia todo para cliente 'metro'
    python cleanup_test_data.py --client wongio    # Limpia todo para cliente 'wongio'
    python cleanup_test_data.py --all              # Limpia ambos clientes
    python cleanup_test_data.py --layer bronze     # Limpia solo Bronze layer
    python cleanup_test_data.py --dry-run          # Muestra qué se limpiaría sin ejecutar
"""

import os
import sys
import subprocess
import logging
import argparse
from datetime import datetime
from pathlib import Path

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger('CleanupTestData')


class TestDataCleaner:
    """Limpiador de datos de prueba"""
    
    def __init__(self, client='metro', dry_run=False):
        self.client = client
        self.dry_run = dry_run
        self.bronze_bucket = 'data-lake-bronze'
        self.silver_bucket = 'data-lake-silver'
        self.gold_bucket = 'data-lake-gold'
        
        # Entidades de prueba
        self.test_entities = [
            'orders', 'order-items', 'products', 'skus', 'stock',
            'categories', 'brands', 'stores', 'customers', 'carriers',
            'delivery-planning', 'prices', 'promotional-prices',
            'promotions', 'invoices', 'admins', 'comments'
        ]
        
        # Tablas Gold de prueba
        self.gold_tables = [
            'wms_orders', 'wms_order_items', 'wms_order_shipping',
            'wms_order_payments', 'wms_order_payments_connector_responses',
            'wms_order_custom_data_fields', 'wms_order_item_weighables',
            'wms_order_status_changes', 'wms_stores', 'wms_logistic_carriers',
            'wms_logistic_delivery_planning', 'wms_logistic_delivery_ranges',
            'wms_order_picking', 'picking_round_orders', 'products', 'skus',
            'categories', 'brands', 'customers', 'admins', 'price',
            'promotional_prices', 'promotions', 'stock', 'invoices', 'ff_comments'
        ]
        
        self.stats = {
            'bronze_cleaned': 0,
            'silver_cleaned': 0,
            'gold_cleaned': 0,
            'local_files_cleaned': 0,
            'errors': []
        }
    
    def clean_bronze_layer(self):
        """Limpiar Bronze layer"""
        logger.info("=" * 80)
        logger.info("LIMPIANDO BRONZE LAYER")
        logger.info("=" * 80)
        
        for entity in self.test_entities:
            s3_path = f"s3://{self.bronze_bucket}/{self.client}/{entity}/"
            
            if self.dry_run:
                logger.info(f"[DRY-RUN] Limpiaría: {s3_path}")
                continue
            
            logger.info(f"\n🗑️  Limpiando: {s3_path}")
            
            cmd = [
                'aws', 's3', 'rm',
                s3_path,
                '--recursive',
                '--endpoint-url', 'http://localhost:4566'
            ]
            
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, check=True)
                
                # Contar archivos eliminados
                deleted_count = result.stdout.count('delete:')
                if deleted_count > 0:
                    logger.info(f"   ✅ Eliminados {deleted_count} archivos")
                    self.stats['bronze_cleaned'] += deleted_count
                else:
                    logger.info(f"   ℹ️  No había archivos para eliminar")
                    
            except subprocess.CalledProcessError as e:
                if 'NoSuchBucket' in e.stderr or 'does not exist' in e.stderr:
                    logger.info(f"   ℹ️  Bucket no existe (ya limpio)")
                else:
                    logger.error(f"   ❌ Error: {e.stderr}")
                    self.stats['errors'].append(f"Bronze {entity}: {e.stderr}")
    
    def clean_silver_layer(self):
        """Limpiar Silver layer"""
        logger.info("\n" + "=" * 80)
        logger.info("LIMPIANDO SILVER LAYER")
        logger.info("=" * 80)
        
        for entity in self.test_entities:
            # Convertir entity name a table name
            table_name = f"{self.client}_{entity.replace('-', '_')}_clean"
            s3_path = f"s3://{self.silver_bucket}/{table_name}/"
            
            if self.dry_run:
                logger.info(f"[DRY-RUN] Limpiaría: {s3_path}")
                continue
            
            logger.info(f"\n🗑️  Limpiando: {s3_path}")
            
            cmd = [
                'aws', 's3', 'rm',
                s3_path,
                '--recursive',
                '--endpoint-url', 'http://localhost:4566'
            ]
            
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, check=True)
                
                deleted_count = result.stdout.count('delete:')
                if deleted_count > 0:
                    logger.info(f"   ✅ Eliminados {deleted_count} archivos")
                    self.stats['silver_cleaned'] += deleted_count
                else:
                    logger.info(f"   ℹ️  No había archivos para eliminar")
                    
            except subprocess.CalledProcessError as e:
                if 'NoSuchBucket' in e.stderr or 'does not exist' in e.stderr:
                    logger.info(f"   ℹ️  Bucket no existe (ya limpio)")
                else:
                    logger.error(f"   ❌ Error: {e.stderr}")
                    self.stats['errors'].append(f"Silver {table_name}: {e.stderr}")
    
    def clean_gold_layer(self):
        """Limpiar Gold layer"""
        logger.info("\n" + "=" * 80)
        logger.info("LIMPIANDO GOLD LAYER")
        logger.info("=" * 80)
        
        for gold_table in self.gold_tables:
            table_name = f"{self.client}_{gold_table}"
            s3_path = f"s3://{self.gold_bucket}/{table_name}/"
            
            if self.dry_run:
                logger.info(f"[DRY-RUN] Limpiaría: {s3_path}")
                continue
            
            logger.info(f"\n🗑️  Limpiando: {s3_path}")
            
            cmd = [
                'aws', 's3', 'rm',
                s3_path,
                '--recursive',
                '--endpoint-url', 'http://localhost:4566'
            ]
            
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, check=True)
                
                deleted_count = result.stdout.count('delete:')
                if deleted_count > 0:
                    logger.info(f"   ✅ Eliminados {deleted_count} archivos")
                    self.stats['gold_cleaned'] += deleted_count
                else:
                    logger.info(f"   ℹ️  No había archivos para eliminar")
                    
            except subprocess.CalledProcessError as e:
                if 'NoSuchBucket' in e.stderr or 'does not exist' in e.stderr:
                    logger.info(f"   ℹ️  Bucket no existe (ya limpio)")
                else:
                    logger.error(f"   ❌ Error: {e.stderr}")
                    self.stats['errors'].append(f"Gold {table_name}: {e.stderr}")
    
    def clean_local_output_files(self):
        """Limpiar archivos de output locales"""
        logger.info("\n" + "=" * 80)
        logger.info("LIMPIANDO ARCHIVOS LOCALES")
        logger.info("=" * 80)
        
        # Directorios de output a limpiar
        output_dirs = [
            Path('max/glue/output'),
            Path('max/glue/etl-bronze-to-silver/output'),
            Path('max/glue/etl-silver-to-gold/output'),
            Path('max/scripts/output')
        ]
        
        for output_dir in output_dirs:
            if not output_dir.exists():
                logger.info(f"\nℹ️  Directorio no existe: {output_dir}")
                continue
            
            if self.dry_run:
                logger.info(f"[DRY-RUN] Limpiaría archivos en: {output_dir}")
                continue
            
            logger.info(f"\n🗑️  Limpiando: {output_dir}")
            
            # Listar archivos
            files = list(output_dir.rglob('*'))
            file_count = len([f for f in files if f.is_file()])
            
            if file_count == 0:
                logger.info(f"   ℹ️  No hay archivos para eliminar")
                continue
            
            # Eliminar archivos
            deleted = 0
            for file_path in files:
                if file_path.is_file():
                    try:
                        file_path.unlink()
                        deleted += 1
                    except Exception as e:
                        logger.error(f"   ❌ Error eliminando {file_path}: {str(e)}")
                        self.stats['errors'].append(f"Local file {file_path}: {str(e)}")
            
            logger.info(f"   ✅ Eliminados {deleted} archivos")
            self.stats['local_files_cleaned'] += deleted
            
            # Eliminar directorios vacíos
            for dir_path in sorted([d for d in files if d.is_dir()], reverse=True):
                try:
                    if not any(dir_path.iterdir()):
                        dir_path.rmdir()
                except:
                    pass
    
    def clean_audit_tables(self):
        """Limpiar tablas de auditoría"""
        logger.info("\n" + "=" * 80)
        logger.info("LIMPIANDO TABLAS DE AUDITORÍA")
        logger.info("=" * 80)
        
        audit_tables = [
            'data_gaps_log',
            'data_quality_issues',
            'schema_changes_log',
            'lineage_metadata'
        ]
        
        for table in audit_tables:
            table_name = f"{self.client}_{table}"
            s3_path = f"s3://{self.silver_bucket}/{table_name}/"
            
            if self.dry_run:
                logger.info(f"[DRY-RUN] Limpiaría: {s3_path}")
                continue
            
            logger.info(f"\n🗑️  Limpiando tabla de auditoría: {table_name}")
            
            cmd = [
                'aws', 's3', 'rm',
                s3_path,
                '--recursive',
                '--endpoint-url', 'http://localhost:4566'
            ]
            
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, check=True)
                
                deleted_count = result.stdout.count('delete:')
                if deleted_count > 0:
                    logger.info(f"   ✅ Eliminados {deleted_count} archivos")
                else:
                    logger.info(f"   ℹ️  No había archivos para eliminar")
                    
            except subprocess.CalledProcessError as e:
                if 'NoSuchBucket' in e.stderr or 'does not exist' in e.stderr:
                    logger.info(f"   ℹ️  Tabla no existe (ya limpia)")
                else:
                    logger.error(f"   ❌ Error: {e.stderr}")
    
    def generate_report(self):
        """Generar reporte de limpieza"""
        logger.info("\n" + "=" * 80)
        logger.info("REPORTE DE LIMPIEZA")
        logger.info("=" * 80)
        
        logger.info(f"\n📊 Resumen:")
        logger.info(f"   Cliente: {self.client}")
        logger.info(f"   Modo: {'DRY-RUN (simulación)' if self.dry_run else 'EJECUCIÓN REAL'}")
        logger.info(f"   Timestamp: {datetime.now().isoformat()}")
        
        logger.info(f"\n📈 Estadísticas:")
        logger.info(f"   Archivos Bronze eliminados: {self.stats['bronze_cleaned']}")
        logger.info(f"   Archivos Silver eliminados: {self.stats['silver_cleaned']}")
        logger.info(f"   Archivos Gold eliminados: {self.stats['gold_cleaned']}")
        logger.info(f"   Archivos locales eliminados: {self.stats['local_files_cleaned']}")
        
        total_cleaned = (self.stats['bronze_cleaned'] + 
                        self.stats['silver_cleaned'] + 
                        self.stats['gold_cleaned'] + 
                        self.stats['local_files_cleaned'])
        
        logger.info(f"\n   Total archivos eliminados: {total_cleaned}")
        
        if self.stats['errors']:
            logger.info(f"\n⚠️  Errores encontrados: {len(self.stats['errors'])}")
            for error in self.stats['errors'][:5]:  # Mostrar primeros 5 errores
                logger.info(f"   - {error}")
            if len(self.stats['errors']) > 5:
                logger.info(f"   ... y {len(self.stats['errors']) - 5} errores más")
        
        logger.info("\n" + "=" * 80)
        if not self.dry_run:
            if self.stats['errors']:
                logger.info("⚠️  LIMPIEZA COMPLETADA CON ERRORES")
            else:
                logger.info("✅ LIMPIEZA COMPLETADA EXITOSAMENTE")
        else:
            logger.info("ℹ️  DRY-RUN COMPLETADO - No se eliminó nada")
        logger.info("=" * 80)
    
    def run_cleanup(self, layer=None):
        """Ejecutar limpieza completa o por capa"""
        logger.info("\n" + "=" * 80)
        logger.info("LIMPIEZA DE DATOS DE PRUEBA")
        logger.info("=" * 80)
        logger.info(f"Cliente: {self.client}")
        logger.info(f"Modo: {'DRY-RUN' if self.dry_run else 'EJECUCIÓN REAL'}")
        if layer:
            logger.info(f"Capa: {layer}")
        else:
            logger.info("Capa: TODAS")
        
        try:
            if layer is None or layer == 'bronze':
                self.clean_bronze_layer()
            
            if layer is None or layer == 'silver':
                self.clean_silver_layer()
            
            if layer is None or layer == 'gold':
                self.clean_gold_layer()
            
            if layer is None or layer == 'local':
                self.clean_local_output_files()
            
            if layer is None or layer == 'audit':
                self.clean_audit_tables()
            
            self.generate_report()
            
            return len(self.stats['errors']) == 0
            
        except Exception as e:
            logger.error(f"\n❌ Error crítico durante la limpieza: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return False


def main():
    """Función principal"""
    parser = argparse.ArgumentParser(
        description='Limpiar datos de prueba del pipeline ETL',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:
  python cleanup_test_data.py                    # Limpia todo para 'metro'
  python cleanup_test_data.py --client wongio    # Limpia todo para 'wongio'
  python cleanup_test_data.py --all              # Limpia ambos clientes
  python cleanup_test_data.py --layer bronze     # Limpia solo Bronze
  python cleanup_test_data.py --dry-run          # Simula sin ejecutar
        """
    )
    
    parser.add_argument(
        '--client',
        type=str,
        default='metro',
        choices=['metro', 'wongio'],
        help='Cliente a limpiar (default: metro)'
    )
    
    parser.add_argument(
        '--all',
        action='store_true',
        help='Limpiar ambos clientes (metro y wongio)'
    )
    
    parser.add_argument(
        '--layer',
        type=str,
        choices=['bronze', 'silver', 'gold', 'local', 'audit'],
        help='Limpiar solo una capa específica (default: todas)'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Simular limpieza sin ejecutar (mostrar qué se limpiaría)'
    )
    
    args = parser.parse_args()
    
    # Determinar clientes a limpiar
    clients = ['metro', 'wongio'] if args.all else [args.client]
    
    # Ejecutar limpieza para cada cliente
    all_success = True
    for client in clients:
        if len(clients) > 1:
            logger.info(f"\n{'='*80}")
            logger.info(f"LIMPIANDO CLIENTE: {client.upper()}")
            logger.info(f"{'='*80}")
        
        cleaner = TestDataCleaner(client=client, dry_run=args.dry_run)
        success = cleaner.run_cleanup(layer=args.layer)
        
        if not success:
            all_success = False
    
    # Retornar código de salida
    sys.exit(0 if all_success else 1)


if __name__ == "__main__":
    main()
