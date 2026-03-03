#!/bin/bash
# Script para iniciar LocalStack

echo "🚀 Iniciando LocalStack..."

# Verificar si Docker está corriendo
if ! docker info > /dev/null 2>&1; then
    echo "❌ Error: Docker no está corriendo"
    exit 1
fi

# Iniciar LocalStack con docker-compose
docker-compose -f docker-compose.localstack.yml up -d

# Esperar a que LocalStack esté listo
echo "⏳ Esperando a que LocalStack esté listo..."
sleep 10

# Verificar que LocalStack está corriendo
if curl -s http://localhost:4566/_localstack/health | grep -q "running"; then
    echo "✅ LocalStack está corriendo correctamente"
    echo ""
    echo "📋 Servicios disponibles en: http://localhost:4566"
    echo "🔍 Health check: http://localhost:4566/_localstack/health"
    echo ""
    echo "Para usar AWS CLI con LocalStack:"
    echo "  aws --endpoint-url=http://localhost:4566 s3 ls"
else
    echo "❌ Error: LocalStack no está respondiendo"
    exit 1
fi
