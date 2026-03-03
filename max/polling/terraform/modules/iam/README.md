# IAM Module - API Polling System

Este módulo crea roles y políticas IAM para los componentes del sistema de polling de APIs.

## Propósito

El módulo crea recursos IAM para:
- **MWAA Execution Role**: Permite a los DAGs de Airflow acceder a DynamoDB, S3, SNS, Secrets Manager
- **EventBridge Role**: Permite a EventBridge invocar DAGs de MWAA

## Uso

```hcl
module "polling_iam" {
  source = "./modules/iam"
  
  # MWAA Configuration
  mwaa_role_name        = "janis-mwaa-polling-role-prod"
  mwaa_environment_arn  = "arn:aws:airflow:us-east-1:123456789012:environment/janis-mwaa-prod"
  
  # EventBridge Configuration
  eventbridge_role_name = "janis-eventbridge-mwaa-role-prod"
  
  # Resource ARNs
  dynamodb_table_arn = module.polling_control_table.table_arn
  sns_topic_arn      = module.polling_error_topic.topic_arn
  s3_bucket_arns = [
    module.mwaa_bucket.bucket_arn,
    module.staging_bucket.bucket_arn
  ]
  secrets_manager_arns = [
    "arn:aws:secretsmanager:us-east-1:123456789012:secret:janis-api-key"
  ]
  
  # AWS Configuration
  aws_region     = "us-east-1"
  aws_account_id = "123456789012"
  
  tags = {
    Environment = "prod"
    Project     = "janis-cencosud"
    ManagedBy   = "terraform"
  }
}
```

## Permisos IAM

### MWAA Execution Role

El rol de MWAA tiene los siguientes permisos:

1. **DynamoDB**: GetItem, PutItem, UpdateItem, DeleteItem, Query, Scan, DescribeTable
2. **S3**: GetObject, PutObject, DeleteObject, ListBucket
3. **SNS**: Publish
4. **CloudWatch Logs**: CreateLogGroup, CreateLogStream, PutLogEvents, DescribeLogStreams
5. **CloudWatch Metrics**: PutMetricData
6. **Secrets Manager**: GetSecretValue, DescribeSecret (si se configuran secretos)

### EventBridge Role

El rol de EventBridge puede:
- Crear tokens CLI para MWAA (para disparar DAGs)

## Mejores Prácticas de Seguridad

- Sigue el principio de menor privilegio
- Usa ARNs específicos de recursos (no wildcards)
- Roles separados para diferentes componentes
- Logging de CloudWatch habilitado para todos los roles

## Soporte para LocalStack

El módulo funciona con LocalStack. No se necesita configuración especial ya que IAM es un servicio global.
