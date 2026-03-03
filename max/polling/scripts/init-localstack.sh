#!/bin/bash
# Script para inicializar LocalStack con recursos necesarios

set -e

ENDPOINT="http://localhost:4566"
REGION="us-east-1"

echo "🚀 Inicializando LocalStack para Sistema de Polling..."

# Esperar a que LocalStack esté listo
echo "⏳ Esperando a que LocalStack esté listo..."
until aws --endpoint-url=$ENDPOINT dynamodb list-tables --region $REGION > /dev/null 2>&1; do
    sleep 2
done
echo "✅ LocalStack está listo"

# Crear tabla DynamoDB
echo "📊 Creando tabla DynamoDB 'polling_control'..."
aws --endpoint-url=$ENDPOINT dynamodb create-table \
    --table-name polling_control \
    --attribute-definitions \
        AttributeName=data_type,AttributeType=S \
    --key-schema \
        AttributeName=data_type,KeyType=HASH \
    --billing-mode PAY_PER_REQUEST \
    --region $REGION \
    > /dev/null 2>&1 || echo "⚠️  Tabla ya existe"

# Crear bucket S3
echo "🪣 Creando bucket S3 'janis-polling-staging'..."
aws --endpoint-url=$ENDPOINT s3 mb s3://janis-polling-staging \
    --region $REGION \
    > /dev/null 2>&1 || echo "⚠️  Bucket ya existe"

# Crear tópico SNS
echo "📧 Creando tópico SNS 'polling-errors'..."
aws --endpoint-url=$ENDPOINT sns create-topic \
    --name polling-errors \
    --region $REGION \
    > /dev/null 2>&1 || echo "⚠️  Tópico ya existe"

# Crear secreto para API key
echo "🔐 Creando secreto 'janis-api-credentials'..."
aws --endpoint-url=$ENDPOINT secretsmanager create-secret \
    --name janis-api-credentials \
    --secret-string '{"api_key":"test-api-key","base_url":"https://api.janis.com"}' \
    --region $REGION \
    > /dev/null 2>&1 || echo "⚠️  Secreto ya existe"

echo ""
echo "✨ LocalStack inicializado exitosamente!"
echo ""
echo "Recursos creados:"
echo "  - DynamoDB Table: polling_control"
echo "  - S3 Bucket: janis-polling-staging"
echo "  - SNS Topic: polling-errors"
echo "  - Secret: janis-api-credentials"
echo ""
echo "Para verificar los recursos:"
echo "  aws --endpoint-url=$ENDPOINT dynamodb list-tables"
echo "  aws --endpoint-url=$ENDPOINT s3 ls"
echo "  aws --endpoint-url=$ENDPOINT sns list-topics"
