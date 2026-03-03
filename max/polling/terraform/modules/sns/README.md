# SNS Module

Este módulo crea un tópico SNS para notificaciones de errores del sistema de polling de APIs.

## Propósito

El tópico SNS se utiliza para:
- Recibir notificaciones de errores de los DAGs de polling
- Distribuir alertas a múltiples suscriptores (email, SQS, Lambda)
- Habilitar monitoreo y respuesta a incidentes
- Proporcionar auditoría de errores del sistema

## Uso

```hcl
module "polling_error_topic" {
  source = "./modules/sns"
  
  topic_name     = "janis-polling-errors-prod"
  display_name   = "API Polling Errors"
  aws_account_id = data.aws_caller_identity.current.account_id
  
  # Email notifications
  email_addresses = [
    "data-team@cencosud.com",
    "ops-team@cencosud.com"
  ]
  
  # Allow MWAA and Lambda to publish
  allowed_iam_arns = [
    module.mwaa_role.role_arn,
    module.lambda_role.role_arn
  ]
  
  enable_alarms = true
  
  tags = {
    Environment = "prod"
    Project     = "janis-cencosud"
    ManagedBy   = "terraform"
  }
}
```

## Suscripciones de Email

Las suscripciones de email requieren confirmación manual. Después de aplicar la configuración de Terraform:

1. Los suscriptores recibirán un email de confirmación de AWS
2. Deben hacer clic en el enlace de confirmación para activar la suscripción
3. La suscripción permanecerá en estado "PendingConfirmation" hasta que se confirme

## Formato de Notificación de Error

El sistema de polling publica notificaciones de error en el siguiente formato JSON:

```json
{
  "data_type": "orders",
  "execution_id": "uuid-1234-5678",
  "error_type": "APIConnectionError",
  "error_message": "Failed to connect to Janis API after 3 retries",
  "timestamp": "2024-01-15T10:30:00Z",
  "stack_trace": "..."
}
```

## Soporte para LocalStack

El módulo funciona con LocalStack configurando el provider AWS con endpoints de LocalStack:

```hcl
provider "aws" {
  endpoints {
    sns = "http://localhost:4566"
  }
}
```
