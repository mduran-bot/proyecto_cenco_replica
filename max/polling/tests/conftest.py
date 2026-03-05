"""
Configuración compartida de pytest para tests de polling.

Este archivo contiene fixtures y configuración común para todos los tests,
incluyendo la gestión de conexiones a LocalStack.
"""

import pytest
import os
import sys
import boto3
from botocore.exceptions import ClientError

# Agregar src al path para imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


# Configuración de LocalStack
LOCALSTACK_ENDPOINT = os.getenv('LOCALSTACK_ENDPOINT', 'http://localhost:4566')


def pytest_configure(config):
    """Configuración global de pytest."""
    # Configurar variables de entorno para LocalStack
    os.environ['AWS_ACCESS_KEY_ID'] = 'test'
    os.environ['AWS_SECRET_ACCESS_KEY'] = 'test'
    os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'


@pytest.fixture(scope='session')
def localstack_endpoint():
    """Endpoint de LocalStack para tests de integración."""
    return LOCALSTACK_ENDPOINT


@pytest.fixture(scope='session')
def aws_credentials():
    """Credenciales de AWS para LocalStack."""
    return {
        'aws_access_key_id': 'test',
        'aws_secret_access_key': 'test',
        'region_name': 'us-east-1'
    }


@pytest.fixture(scope='session')
def check_localstack():
    """
    Verifica que LocalStack esté disponible.
    
    Este fixture se ejecuta una vez por sesión y verifica la conectividad
    con LocalStack. Si LocalStack no está disponible, los tests de integración
    se saltarán automáticamente.
    """
    try:
        # Intentar conectar a LocalStack
        s3_client = boto3.client(
            's3',
            endpoint_url=LOCALSTACK_ENDPOINT,
            region_name='us-east-1',
            aws_access_key_id='test',
            aws_secret_access_key='test'
        )
        
        # Intentar listar buckets como health check
        s3_client.list_buckets()
        
        print(f"\n✓ LocalStack disponible en {LOCALSTACK_ENDPOINT}")
        return True
        
    except Exception as e:
        print(f"\n✗ LocalStack no disponible: {e}")
        print("Los tests de integración se saltarán.")
        return False


# Marker personalizado para tests de integración
def pytest_collection_modifyitems(config, items):
    """
    Marca automáticamente los tests de integración.
    
    Los tests en archivos *_integration.py se marcan como 'integration'
    y requieren LocalStack.
    """
    for item in items:
        if 'integration' in item.nodeid:
            item.add_marker(pytest.mark.integration)


# Configurar markers
def pytest_configure(config):
    """Registrar markers personalizados."""
    config.addinivalue_line(
        "markers", "integration: tests de integración que requieren LocalStack"
    )
    config.addinivalue_line(
        "markers", "unit: tests unitarios con mocks"
    )
