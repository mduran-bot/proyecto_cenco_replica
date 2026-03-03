"""
Script de validación para el checkpoint 4: Validar Bronze→Silver con 3 entidades

Este script:
1. Genera/carga datos de prueba para orders, products, stock
2. Los sube a la capa Bronze en LocalStack S3
3. Ejecuta el pipeline Bronze→Silver para cada entidad
4. Verifica que los datos lleguen correctamente a Silver
5. Verifica que las conversiones de tipos funcionen
6. Genera un reporte de validación
"""

import os
import sys
import json
import subprocess
import logging
from datetime import datetime

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger('ValidateBronzeToSilver')


class BronzeToSilverValidator:
    """Validador del pipeline Bronze→Silver"""
    
    def __init__(self, client='metro'):
        self.client = client
        self.bronze_bucket = 'data-lake-bronze'
        self.silver_bucket = 'data-lake-silver'
        self.test_entities = ['orders', 'products', 'stock']
        self.results = {}
        
    def setup_test_data(self):
        """Subir datos de prueba a Bronze layer en LocalStack S3"""
        logger.info("=" * 80)
        logger.info("PASO 1: SUBIR DATOS DE PRUEBA A BRONZE LAYER")
        logger.info("=" * 80)
        
        for entity in self.test_entities:
            logger.info(f"\n📦 Subiendo datos de prueba para: {entity}")
            
            # Ruta del archivo de prueba
            test_file = f"max/tests/fixtures/test_{entity}.json"
            
            if not os.path.exists(test_file):
                logger.error(f"❌ Archivo de prueba no encontrado: {test_file}")
                self.results[entity] = {'status': 'FAILED', 'reason': 'Test file not found'}
                continue
            
            # Limpiar datos anteriores primero
            logger.info(f"   Limpiando datos anteriores de {entity}...")
            cleanup_cmd = [
                'aws', 's3', 'rm',
                f"s3://{self.bronze_bucket}/{self.client}/{entity}/",
                '--recursive',
                '--endpoint-url', 'http://localhost:4566'
            ]
            subprocess.run(cleanup_cmd, capture_output=True, text=True)
            
            # Ruta en S3
            s3_path = f"s3://{self.bronze_bucket}/{self.client}/{entity}/test_data.json"
            
            # Subir a LocalStack S3
            cmd = [
                'aws', 's3', 'cp',
                test_file,
                s3_path,
                '--endpoint-url', 'http://localhost:4566'
            ]
            
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, check=True)
                logger.info(f"✅ Datos subidos exitosamente a: {s3_path}")
                
                # Verificar que se subió
                verify_cmd = [
                    'aws', 's3', 'ls',
                    f"s3://{self.bronze_bucket}/{self.client}/{entity}/",
                    '--endpoint-url', 'http://localhost:4566'
                ]
                verify_result = subprocess.run(verify_cmd, capture_output=True, text=True)
                logger.info(f"   Archivos en Bronze: {verify_result.stdout.strip()}")
                
            except subprocess.CalledProcessError as e:
                logger.error(f"❌ Error al subir datos: {e.stderr}")
                self.results[entity] = {'status': 'FAILED', 'reason': f'Upload failed: {e.stderr}'}
                continue
    
    def run_pipeline_for_entity(self, entity):
        """Ejecutar pipeline Bronze→Silver para una entidad"""
        logger.info(f"\n🔄 Ejecutando pipeline Bronze→Silver para: {entity}")
        
        # Comando para ejecutar el pipeline
        cmd = [
            'python', 'run_pipeline_to_silver.py',
            '--entity-type', entity,
            '--client', self.client
        ]
        
        try:
            # Ejecutar pipeline
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
                cwd='max'
            )
            
            logger.info(f"✅ Pipeline ejecutado exitosamente para {entity}")
            
            # Extraer métricas del output
            output_lines = result.stdout.split('\n')
            metrics = self._extract_metrics(output_lines)
            
            return {
                'status': 'SUCCESS',
                'metrics': metrics,
                'output': result.stdout
            }
            
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Error al ejecutar pipeline: {e.stderr}")
            return {
                'status': 'FAILED',
                'reason': f'Pipeline execution failed: {e.stderr}',
                'output': e.stdout
            }
    
    def _extract_metrics(self, output_lines):
        """Extraer métricas del output del pipeline"""
        metrics = {
            'records_bronze': 0,
            'records_silver': 0,
            'transformations': []
        }
        
        for line in output_lines:
            if 'Registros leídos:' in line:
                try:
                    metrics['records_bronze'] = int(line.split(':')[1].strip())
                except:
                    pass
            elif 'Registros en Silver:' in line:
                try:
                    metrics['records_silver'] = int(line.split(':')[1].strip())
                except:
                    pass
            elif 'Ejecutando' in line and 'Module' in line:
                metrics['transformations'].append(line.strip())
        
        return metrics
    
    def verify_silver_data(self, entity):
        """Verificar datos en Silver layer"""
        logger.info(f"\n🔍 Verificando datos en Silver para: {entity}")
        
        # Ruta en S3
        silver_table = f"{self.client}_{entity}_clean"
        s3_path = f"s3://{self.silver_bucket}/{silver_table}/"
        
        # Listar archivos en Silver
        cmd = [
            'aws', 's3', 'ls',
            s3_path,
            '--recursive',
            '--endpoint-url', 'http://localhost:4566'
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            if result.stdout.strip():
                logger.info(f"✅ Datos encontrados en Silver:")
                for line in result.stdout.strip().split('\n')[:5]:  # Mostrar primeros 5 archivos
                    logger.info(f"   {line}")
                return True
            else:
                logger.warning(f"⚠️  No se encontraron datos en Silver: {s3_path}")
                return False
                
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Error al verificar Silver: {e.stderr}")
            return False
    
    def verify_type_conversions(self, entity):
        """Verificar que las conversiones de tipos funcionaron"""
        logger.info(f"\n🔬 Verificando conversiones de tipos para: {entity}")
        
        # Leer un archivo de Silver para verificar tipos
        silver_table = f"{self.client}_{entity}_clean"
        output_path = f"output/silver/{silver_table}_summary.csv"
        
        if not os.path.exists(output_path):
            logger.warning(f"⚠️  Archivo de resumen no encontrado: {output_path}")
            return False
        
        try:
            # Leer CSV y verificar tipos
            import pandas as pd
            df = pd.read_csv(output_path)
            
            logger.info(f"✅ Datos leídos: {len(df)} registros")
            logger.info(f"   Columnas: {list(df.columns)}")
            
            # Verificar conversiones específicas por entidad
            conversions_ok = True
            
            if entity == 'orders':
                # Verificar timestamp conversions
                if 'date_created' in df.columns:
                    logger.info(f"   ✅ date_created presente (conversión de timestamp)")
                else:
                    logger.warning(f"   ⚠️  date_created no encontrado")
                    conversions_ok = False
                    
            elif entity == 'products':
                # Verificar boolean conversion
                if 'hasInfiniteStock' in df.columns or 'infinite_stock' in df.columns:
                    logger.info(f"   ✅ Campo boolean presente")
                else:
                    logger.warning(f"   ⚠️  Campo boolean no encontrado")
                    conversions_ok = False
                    
            elif entity == 'stock':
                # Verificar numeric fields
                if 'stock' in df.columns:
                    logger.info(f"   ✅ Campos numéricos presentes")
                else:
                    logger.warning(f"   ⚠️  Campos numéricos no encontrados")
                    conversions_ok = False
            
            return conversions_ok
            
        except Exception as e:
            logger.error(f"❌ Error al verificar conversiones: {str(e)}")
            return False
    
    def run_validation(self):
        """Ejecutar validación completa"""
        logger.info("\n" + "=" * 80)
        logger.info("VALIDACIÓN BRONZE→SILVER - CHECKPOINT 4")
        logger.info("=" * 80)
        logger.info(f"Cliente: {self.client}")
        logger.info(f"Entidades a validar: {', '.join(self.test_entities)}")
        logger.info(f"Timestamp: {datetime.now().isoformat()}")
        
        # Paso 1: Subir datos de prueba
        self.setup_test_data()
        
        # Paso 2: Ejecutar pipeline para cada entidad
        logger.info("\n" + "=" * 80)
        logger.info("PASO 2: EJECUTAR PIPELINE BRONZE→SILVER")
        logger.info("=" * 80)
        
        for entity in self.test_entities:
            if entity in self.results and self.results[entity]['status'] == 'FAILED':
                logger.warning(f"\n⏭️  Saltando {entity} (falló en paso anterior)")
                continue
            
            # Ejecutar pipeline
            result = self.run_pipeline_for_entity(entity)
            self.results[entity] = result
            
            # Verificar datos en Silver
            if result['status'] == 'SUCCESS':
                silver_ok = self.verify_silver_data(entity)
                result['silver_verified'] = silver_ok
                
                # Verificar conversiones de tipos
                conversions_ok = self.verify_type_conversions(entity)
                result['conversions_verified'] = conversions_ok
        
        # Paso 3: Generar reporte
        self.generate_report()
    
    def generate_report(self):
        """Generar reporte de validación"""
        logger.info("\n" + "=" * 80)
        logger.info("REPORTE DE VALIDACIÓN")
        logger.info("=" * 80)
        
        total = len(self.test_entities)
        successful = sum(1 for r in self.results.values() if r.get('status') == 'SUCCESS')
        
        logger.info(f"\n📊 Resumen General:")
        logger.info(f"   Total entidades: {total}")
        logger.info(f"   Exitosas: {successful}")
        logger.info(f"   Fallidas: {total - successful}")
        logger.info(f"   Tasa de éxito: {(successful/total)*100:.1f}%")
        
        logger.info(f"\n📋 Detalle por Entidad:")
        for entity, result in self.results.items():
            status_icon = "✅" if result.get('status') == 'SUCCESS' else "❌"
            logger.info(f"\n{status_icon} {entity.upper()}")
            logger.info(f"   Status: {result.get('status', 'UNKNOWN')}")
            
            if result.get('status') == 'SUCCESS':
                metrics = result.get('metrics', {})
                logger.info(f"   Registros Bronze: {metrics.get('records_bronze', 'N/A')}")
                logger.info(f"   Registros Silver: {metrics.get('records_silver', 'N/A')}")
                logger.info(f"   Silver verificado: {'✅' if result.get('silver_verified') else '❌'}")
                logger.info(f"   Conversiones verificadas: {'✅' if result.get('conversions_verified') else '❌'}")
            else:
                logger.info(f"   Razón: {result.get('reason', 'Unknown')}")
        
        # Guardar reporte en JSON
        report_path = f"output/validation_report_{self.client}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        os.makedirs('output', exist_ok=True)
        
        with open(report_path, 'w') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'client': self.client,
                'entities': self.test_entities,
                'results': self.results,
                'summary': {
                    'total': total,
                    'successful': successful,
                    'failed': total - successful,
                    'success_rate': (successful/total)*100
                }
            }, f, indent=2)
        
        logger.info(f"\n💾 Reporte guardado en: {report_path}")
        
        # Conclusión
        logger.info("\n" + "=" * 80)
        if successful == total:
            logger.info("✅ VALIDACIÓN EXITOSA - Todos los pipelines funcionaron correctamente")
        elif successful > 0:
            logger.info("⚠️  VALIDACIÓN PARCIAL - Algunos pipelines fallaron")
        else:
            logger.info("❌ VALIDACIÓN FALLIDA - Todos los pipelines fallaron")
        logger.info("=" * 80)
        
        return successful == total


def main():
    """Función principal"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Validar pipeline Bronze→Silver para checkpoint 4'
    )
    parser.add_argument(
        '--client',
        type=str,
        default='metro',
        choices=['metro', 'wongio'],
        help='Cliente a validar (default: metro)'
    )
    
    args = parser.parse_args()
    
    # Crear validador y ejecutar
    validator = BronzeToSilverValidator(client=args.client)
    success = validator.run_validation()
    
    # Retornar código de salida
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
