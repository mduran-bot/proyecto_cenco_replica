# DynamoDB Module - API Polling Control Table

Este módulo de Terraform crea una tabla DynamoDB para gestión de estado y locks del sistema de polling de APIs de Janis.

## Propósito

La tabla de control DynamoDB es el componente central para:
- **Prevenir ejecuciones concurrentes** mediante locks distribuidos
- **Habilitar polling incremental** almacenando timestamps de última ejecución
- **Rastrear estado de ejecución** para monitoreo y debugging
- **Detectar contención** mediante CloudWatch alarms

## Características

### Seguridad
- ✅ Server-side encryption habilitado por defecto
- ✅ Soporte para KMS custom keys
- ✅ Point-in-time recovery para protección de datos
- ✅ Conditional updates para prevenir race conditions

### Monitoreo
- ✅ CloudWatch alarms para throttling de lectura/escritura
- ✅ Alarma de contención de locks (ConditionalCheckFailed)
- ✅ Integración con SNS para notificaciones

### Flexibilidad
- ✅ Billing mode configurable (PAY_PER_REQUEST o PROVISIONED)
- ✅ TTL opcional para expiración automática de items
- ✅ Alarms opcionales (pueden deshabilitarse)

## Schema de la Tabla

**Clave de Partición:** `data_type` (String)

**Atributos del Item:**
```json
{
  "data_type": "orders",              // PK: tipo de dato (orders, products, stock, prices, stores)
  "lock_acquired": true,              // Estado del lock (true/false)
  "lock_timestamp": "2024-01-15T10:30:00Z",  // Timestamp de adquisición del lock
  "execution_id": "uuid-1234",        // ID único de ejecución
  "last_successful_execution": "2024-01-15T10:25:00Z",  // Última ejecución exitosa
  "last_modified_date": "2024-01-15T10:24:00Z",  // Para filtro incremental
  "status": "running",                // Estado: running | completed | failed
  "records_fetched": 0,               // Contador de registros obtenidos
  "error_message": null               // Mensaje de error si aplica
}
```

## Uso

### Ejemplo Básico

```hcl
module "polling_control_table" {
  source = "./modules/dynamodb"
  
  table_name = "janis-polling-control-prod"
  
  tags = {
    Environment = "prod"
    Project     = "janis-polling"
  }
}
```

### Ejemplo Completo

```hcl
module "polling_control_table" {
  source = "./modules/dynamodb"
  
  # Configuración de tabla
  table_name                     = "${var.project_name}-polling-control-${var.environment}"
  billing_mode                   = "PAY_PER_REQUEST"
  
  # Seguridad
  enable_point_in_time_recovery  = true
  kms_key_arn                    = aws_kms_key.dynamodb.arn
  
  # Monitoreo
  enable_alarms                  = true
  alarm_sns_topic_arn            = module.error_notifications.topic_arn
  
  # TTL (opcional)
  ttl_attribute_name             = "expiration_time"
  
  tags = {
    Environment = var.environment
    Project     = var.project_name
    ManagedBy   = "terraform"
    CostCenter  = "data-engineering"
  }
}
```

### Ejemplo con Billing Mode PROVISIONED

```hcl
module "polling_control_table" {
  source = "./modules/dynamodb"
  
  table_name     = "janis-polling-control-dev"
  billing_mode   = "PROVISIONED"
  read_capacity  = 5
  write_capacity = 5
  
  tags = {
    Environment = "dev"
  }
}
```

## Variables

| Variable | Tipo | Default | Descripción |
|----------|------|---------|-------------|
| `table_name` | string | - | Nombre de la tabla DynamoDB (requerido) |
| `billing_mode` | string | `"PAY_PER_REQUEST"` | Modo de facturación (PROVISIONED o PAY_PER_REQUEST) |
| `read_capacity` | number | `5` | Unidades de capacidad de lectura (solo PROVISIONED) |
| `write_capacity` | number | `5` | Unidades de capacidad de escritura (solo PROVISIONED) |
| `enable_point_in_time_recovery` | bool | `true` | Habilitar recuperación point-in-time |
| `kms_key_arn` | string | `null` | ARN de clave KMS para cifrado (null = AWS managed) |
| `ttl_attribute_name` | string | `""` | Nombre del atributo TTL (vacío = deshabilitado) |
| `enable_alarms` | bool | `true` | Habilitar CloudWatch alarms |
| `alarm_sns_topic_arn` | string | `""` | ARN del tópico SNS para alarmas |
| `tags` | map(string) | `{}` | Tags a aplicar a todos los recursos |

## Outputs

| Output | Descripción |
|--------|-------------|
| `table_name` | Nombre de la tabla DynamoDB |
| `table_arn` | ARN de la tabla DynamoDB |
| `table_id` | ID de la tabla DynamoDB |
| `table_stream_arn` | ARN del stream de la tabla (si está habilitado) |
| `table_stream_label` | Label del stream de la tabla |

## CloudWatch Alarms

El módulo crea 3 alarmas de CloudWatch cuando `enable_alarms = true`:

### 1. Read Throttle Alarm
- **Métrica:** `ReadThrottleEvents`
- **Threshold:** 10 eventos en 5 minutos
- **Descripción:** Alerta cuando la tabla experimenta throttling de lectura

### 2. Write Throttle Alarm
- **Métrica:** `WriteThrottleEvents`
- **Threshold:** 10 eventos en 5 minutos
- **Descripción:** Alerta cuando la tabla experimenta throttling de escritura

### 3. Conditional Check Failed Alarm
- **Métrica:** `ConditionalCheckFailedRequests`
- **Threshold:** 50 eventos en 5 minutos
- **Descripción:** Alerta cuando hay alta contención de locks (muchos intentos fallidos de adquisición)

## Operaciones de Lock

### Adquirir Lock

```python
import boto3
from datetime import datetime

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('janis-polling-control-prod')

def acquire_lock(data_type: str, execution_id: str) -> bool:
    """
    Intenta adquirir lock usando conditional update.
    Retorna True si lock adquirido, False si ya existe.
    """
    try:
        table.update_item(
            Key={'data_type': data_type},
            UpdateExpression='SET lock_acquired = :true, lock_timestamp = :now, execution_id = :exec_id, #status = :running',
            ConditionExpression='attribute_not_exists(lock_acquired) OR lock_acquired = :false',
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={
                ':true': True,
                ':false': False,
                ':now': datetime.utcnow().isoformat(),
                ':exec_id': execution_id,
                ':running': 'running'
            }
        )
        return True
    except ClientError as e:
        if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
            return False
        raise
```

### Liberar Lock

```python
def release_lock(data_type: str, success: bool, last_modified: str = None):
    """
    Libera lock y actualiza timestamps si exitoso.
    """
    update_expr = 'SET lock_acquired = :false, #status = :status'
    expr_values = {':false': False}
    
    if success:
        update_expr += ', last_successful_execution = :now'
        expr_values[':now'] = datetime.utcnow().isoformat()
        expr_values[':status'] = 'completed'
        
        if last_modified:
            update_expr += ', last_modified_date = :last_mod'
            expr_values[':last_mod'] = last_modified
    else:
        expr_values[':status'] = 'failed'
    
    table.update_item(
        Key={'data_type': data_type},
        UpdateExpression=update_expr,
        ExpressionAttributeNames={'#status': 'status'},
        ExpressionAttributeValues=expr_values
    )
```

## Costos Estimados

### PAY_PER_REQUEST (On-Demand)
- **Lectura:** $0.25 por millón de read request units
- **Escritura:** $1.25 por millón de write request units
- **Estimado mensual:** ~$5 para 5 data types con polling frecuente

### PROVISIONED
- **Lectura:** $0.00013 por hora por RCU
- **Escritura:** $0.00065 por hora por WCU
- **Estimado mensual:** ~$3.50 (5 RCU + 5 WCU)

### Point-in-Time Recovery
- **Costo:** $0.20 por GB-mes de almacenamiento
- **Estimado:** ~$0.01/mes (tabla pequeña)

## Testing con LocalStack

```bash
# Aplicar módulo en LocalStack
terraform apply \
  -var="table_name=polling-control-test" \
  -var="enable_alarms=false" \
  -target=module.polling_control_table

# Verificar tabla creada
aws --endpoint-url=http://localhost:4566 dynamodb describe-table \
  --table-name polling-control-test

# Insertar item de prueba
aws --endpoint-url=http://localhost:4566 dynamodb put-item \
  --table-name polling-control-test \
  --item '{
    "data_type": {"S": "orders"},
    "lock_acquired": {"BOOL": false},
    "status": {"S": "idle"}
  }'

# Leer item
aws --endpoint-url=http://localhost:4566 dynamodb get-item \
  --table-name polling-control-test \
  --key '{"data_type": {"S": "orders"}}'
```

## Troubleshooting

### Error: ConditionalCheckFailedException
**Causa:** Otro proceso ya tiene el lock adquirido.
**Solución:** Esto es comportamiento esperado. El DAG debe salir graciosamente.

### Error: ProvisionedThroughputExceededException
**Causa:** Throttling en modo PROVISIONED.
**Solución:** Aumentar read_capacity/write_capacity o cambiar a PAY_PER_REQUEST.

### Alarma: High Conditional Check Failed
**Causa:** Múltiples DAGs intentando adquirir lock simultáneamente.
**Solución:** Revisar schedules de EventBridge para evitar solapamiento.

## Mejores Prácticas

1. **Usar PAY_PER_REQUEST** para cargas de trabajo impredecibles
2. **Habilitar point-in-time recovery** en producción
3. **Configurar alarmas** con SNS topic apropiado
4. **Usar KMS custom keys** para compliance estricto
5. **Implementar TTL** si los items tienen vida útil limitada
6. **Monitorear métricas** de CloudWatch regularmente

## Referencias

- [DynamoDB Best Practices](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/best-practices.html)
- [DynamoDB Conditional Writes](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/WorkingWithItems.html#WorkingWithItems.ConditionalUpdate)
- [DynamoDB Encryption](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/EncryptionAtRest.html)
