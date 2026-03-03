# S3 Module - Data Lake Buckets

Este módulo crea todos los buckets S3 necesarios para la plataforma de integración Janis-Cencosud, implementando una arquitectura de Data Lake con capas Bronze, Silver y Gold.

## Arquitectura de Data Lake

### Bronze Layer (Raw Data)
- **Propósito**: Almacenar datos crudos sin procesar de la API de Janis y webhooks
- **Formato**: JSON, CSV, Parquet (según fuente)
- **Retención**: 365 días (configurable)
- **Lifecycle**: Transición a Glacier después de 90 días

### Silver Layer (Cleaned Data)
- **Propósito**: Datos limpiados, validados y normalizados
- **Formato**: Apache Iceberg con Parquet
- **Retención**: 730 días (2 años, configurable)
- **Lifecycle**: Transición a Glacier después de 180 días

### Gold Layer (Business-Ready Data)
- **Propósito**: Datos agregados y optimizados para BI
- **Formato**: Apache Iceberg con Parquet
- **Retención**: Indefinida (con Intelligent Tiering)
- **Lifecycle**: Intelligent Tiering después de 30 días

### Scripts Bucket
- **Propósito**: Almacenar código de Lambda, Glue jobs, y DAGs de MWAA
- **Versionado**: Habilitado para control de cambios
- **Cifrado**: AES256

### Logs Bucket
- **Propósito**: Almacenar logs de acceso S3 y logs de aplicaciones
- **Retención**: 365 días (configurable)
- **Lifecycle**: 
  - Standard-IA después de 30 días
  - Glacier después de 90 días
  - Expiración después de 365 días

## Características de Seguridad

Todos los buckets implementan:
- ✅ **Cifrado en reposo**: AES256 server-side encryption
- ✅ **Versionado**: Habilitado para recuperación de datos
- ✅ **Bloqueo de acceso público**: Todos los accesos públicos bloqueados
- ✅ **Access logging**: Logs de acceso enviados al bucket de logs
- ✅ **Lifecycle policies**: Optimización automática de costos

## Uso

```hcl
module "s3" {
  source = "./modules/s3"

  name_prefix = "janis-cencosud-dev"

  # Lifecycle configuration (opcional)
  bronze_glacier_transition_days = 90
  bronze_expiration_days         = 365
  silver_glacier_transition_days = 180
  silver_expiration_days         = 730
  gold_intelligent_tiering_days  = 30
  logs_expiration_days           = 365

  # Tags corporativos
  tags = {
    Environment  = "dev"
    Project      = "janis-cencosud"
    ManagedBy    = "terraform"
    Owner        = "data-team"
    CostCenter   = "analytics"
  }
}
```

## Outputs

El módulo proporciona outputs para todos los buckets:

```hcl
# Acceder a nombres de buckets
module.s3.bronze_bucket_id
module.s3.silver_bucket_id
module.s3.gold_bucket_id
module.s3.scripts_bucket_id
module.s3.logs_bucket_id

# Acceder a ARNs (para IAM policies)
module.s3.bronze_bucket_arn
module.s3.silver_bucket_arn
module.s3.gold_bucket_arn

# Mapa de todos los buckets
module.s3.all_bucket_names
module.s3.all_bucket_arns
```

## Estructura de Directorios Recomendada

### Bronze Layer
```
bronze/
├── orders/
│   ├── year=2024/
│   │   ├── month=01/
│   │   │   ├── day=15/
│   │   │   │   └── orders_20240115_*.json
├── products/
├── stock/
├── prices/
└── stores/
```

### Silver Layer
```
silver/
├── orders/
│   └── iceberg/
│       ├── metadata/
│       └── data/
├── products/
├── stock/
├── prices/
└── stores/
```

### Gold Layer
```
gold/
├── orders_aggregated/
├── inventory_summary/
├── sales_metrics/
└── store_performance/
```

### Scripts Bucket
```
scripts/
├── lambda/
│   ├── webhook-processor/
│   └── data-enrichment/
├── glue/
│   ├── bronze-to-silver/
│   └── silver-to-gold/
└── mwaa/
    └── dags/
```

## Estimación de Costos

### Storage Costs (estimado para 1TB de datos)
- **Bronze**: $23/mes (Standard) → $4/mes (Glacier después de 90 días)
- **Silver**: $23/mes (Standard) → $4/mes (Glacier después de 180 días)
- **Gold**: $23/mes (Standard) → $15/mes (Intelligent Tiering)
- **Scripts**: $1/mes (pocos GB)
- **Logs**: $5/mes (con lifecycle)

### Request Costs
- PUT/COPY/POST: $0.005 por 1,000 requests
- GET/SELECT: $0.0004 por 1,000 requests

### Data Transfer
- Transferencia dentro de AWS: Gratis
- Transferencia a internet: $0.09/GB

## Integración con Otros Servicios

### Lambda Functions
```python
import boto3

s3 = boto3.client('s3')
bronze_bucket = 'janis-cencosud-dev-datalake-bronze'

# Escribir datos crudos
s3.put_object(
    Bucket=bronze_bucket,
    Key='orders/year=2024/month=01/day=15/order_12345.json',
    Body=json.dumps(order_data)
)
```

### AWS Glue
```python
# Leer desde Bronze
bronze_df = spark.read.json('s3://janis-cencosud-dev-datalake-bronze/orders/')

# Escribir a Silver (Iceberg)
bronze_df.write \
    .format('iceberg') \
    .mode('append') \
    .save('s3://janis-cencosud-dev-datalake-silver/orders/')
```

### Redshift COPY
```sql
COPY orders
FROM 's3://janis-cencosud-dev-datalake-gold/orders_aggregated/'
IAM_ROLE 'arn:aws:iam::123456789012:role/RedshiftCopyRole'
FORMAT AS PARQUET;
```

## Mejores Prácticas

1. **Particionamiento**: Usar particiones por fecha (year/month/day) para optimizar queries
2. **Compresión**: Usar Snappy o Gzip para reducir costos de storage
3. **Formato**: Preferir Parquet sobre JSON para mejor performance
4. **Versionado**: Mantener habilitado para recuperación de datos
5. **Lifecycle**: Ajustar políticas según patrones de acceso reales
6. **Monitoring**: Configurar CloudWatch metrics para monitorear uso

## Troubleshooting

### Error: Bucket name already exists
Los nombres de buckets S3 son globalmente únicos. Cambiar el `name_prefix` para usar un nombre diferente.

### Error: Access Denied
Verificar que el IAM role/user tenga permisos `s3:CreateBucket`, `s3:PutObject`, etc.

### Costos inesperados
Revisar lifecycle policies y considerar reducir períodos de retención o habilitar Intelligent Tiering.

## Referencias

- [AWS S3 Best Practices](https://docs.aws.amazon.com/AmazonS3/latest/userguide/best-practices.html)
- [S3 Lifecycle Configuration](https://docs.aws.amazon.com/AmazonS3/latest/userguide/object-lifecycle-mgmt.html)
- [Apache Iceberg on S3](https://iceberg.apache.org/docs/latest/aws/)
