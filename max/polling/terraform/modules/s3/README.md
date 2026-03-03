# S3 Module - Polling Staging Bucket

Este módulo crea un bucket S3 para almacenamiento temporal de datos de polling antes de ser procesados por el pipeline ETL.

## Propósito

El bucket S3 se utiliza para:
- Almacenar datos obtenidos de las APIs de Janis temporalmente
- Servir como staging area antes del procesamiento ETL
- Proporcionar durabilidad y disponibilidad de datos
- Habilitar notificaciones para procesamiento automático

## Uso

```hcl
module "polling_staging_bucket" {
  source = "./modules/s3"
  
  bucket_name         = "janis-polling-staging-prod"
  enable_versioning   = true
  
  # Lifecycle configuration
  intelligent_tiering_days = 30
  glacier_transition_days  = 90
  expiration_days          = 365
  
  # Optional: Enable access logging
  logging_bucket_name = "janis-logs-prod"
  
  # Optional: S3 notifications
  lambda_notifications = [
    {
      function_arn  = aws_lambda_function.process_polling_data.arn
      events        = ["s3:ObjectCreated:*"]
      filter_prefix = "orders/"
      filter_suffix = ".json"
    }
  ]
  
  tags = {
    Environment = "prod"
    Project     = "janis-cencosud"
    ManagedBy   = "terraform"
  }
}
```

## Estructura de Datos

Los datos se organizan en el bucket con la siguiente estructura:

```
s3://bucket-name/
├── orders/
│   ├── 2024-01-15/
│   │   ├── execution-uuid-1234.json
│   │   └── execution-uuid-5678.json
├── products/
│   ├── 2024-01-15/
│   │   └── execution-uuid-abcd.json
├── stock/
├── prices/
└── stores/
```

## Lifecycle Policies

El módulo configura las siguientes políticas de lifecycle:

1. **Intelligent Tiering** (30 días): Optimización automática de costos
2. **Glacier** (90 días): Archivado de datos antiguos
3. **Expiration** (365 días): Eliminación de datos muy antiguos
4. **Abort Incomplete Multipart Uploads** (7 días): Limpieza automática

## Seguridad

- Cifrado en reposo habilitado (AES256 o KMS)
- Bloqueo de acceso público
- Versionado habilitado para protección de datos
- Logging de acceso opcional

## Soporte para LocalStack

El módulo funciona con LocalStack configurando el provider AWS con endpoints de LocalStack:

```hcl
provider "aws" {
  endpoints {
    s3 = "http://s3.localhost.localstack.cloud:4566"
  }
}
```
