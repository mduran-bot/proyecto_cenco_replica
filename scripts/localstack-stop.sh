#!/bin/bash
# Script para detener LocalStack

echo "🛑 Deteniendo LocalStack..."

docker-compose -f docker-compose.localstack.yml down

echo "✅ LocalStack detenido"
