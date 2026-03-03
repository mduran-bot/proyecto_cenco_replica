# Guía de Uso de LocalStack

LocalStack te permite probar toda la infraestructura AWS localmente sin costos. Este proyecto incluye una configuración completa de LocalStack con Docker Compose para desarrollo y testing de la infraestructura Janis-Cencosud.

## 🚀 Inicio Rápido

**¿Primera vez usando LocalStack?** Lee la **[GUIA_INICIO_LOCALSTACK.md](GUIA_INICIO_LOCALSTACK.md)** para una guía paso a paso desde cero.

## Requisitos Previos

- Docker Desktop instalado y corriendo
- Terraform instalado (>= 1.0)
- AWS CLI instalado (opcional, para testing manual)
- 4GB RAM mínimo disponible para Docker

## Configuración de LocalStack

El archivo `docker-compose.localstack.yml` configura LocalStack con los siguientes servicios AWS:

- **Networking**: VPC, EC2, Subnets, Security Groups, NAT Gateway
- **Storage**: S3
- **Compute**: Lambda
- **API**: API Gateway
- **Streaming**: Kinesis
- **ETL**: Glue (funcionalidad básica)
- **Data Warehouse**: Redshift (emulación básica)
- **Security**: Secrets Manager, IAM, STS, KMS
- **Monitoring**: CloudWatch, EventBridge

### Características de la Configuración

- **Puerto principal**: 4566 (LocalStack Gateway)
- **Persistencia**: Deshabilitada (configuración limpia en cada inicio)
- **Región**: us-east-1 (igual que producción)
- **Debug**: Habilitado para troubleshooting
- **Lambda Executor**: Docker (para mejor compatibilidad)

## Inicio Rápido

### 1. Iniciar LocalStack

```powershell
# Iniciar LocalStack en background
docker-compose -f docker-compose.localstack.yml up -d

# Ver logs en tiempo real
docker-compose -f docker-compose.localstack.yml logs -f

# Verificar que está corriendo
curl http://localhost:4566/_localstack/health
```

Deberías ver una respuesta JSON con el estado de los servicios:
```json
{
  "services": {
    "s3": "running",
    "lambda": "running",
    "ec2": "running",
    ...
  }
}
```

O usa el script helper:
```bash
bash scripts/localstack-start.sh
```

### 2. Verificar Conectividad con LocalStack (Opcional)

Antes de desplegar la infraestructura completa, puedes probar la conectividad con un test simple:

```powershell
# Desde el directorio terraform/
cd terraform

# Inicializar Terraform
terraform init

# Desplegar infraestructura con configuración de LocalStack
terraform plan -var-file="localstack.tfvars"
terraform apply -var-file="localstack.tfvars" -auto-approve
```

### 3. Desplegar Infraestructura Completa con Terraform

El proyecto incluye un archivo de configuración específico para LocalStack: `terraform/localstack.tfvars`

**Características de la configuración LocalStack:**
- VPC con subnets en Single-AZ (us-east-1a)
- Valores dummy para servicios no soportados (Redshift, MWAA)
- VPC Endpoints deshabilitados (no necesarios en LocalStack)
- Monitoreo deshabilitado (VPC Flow Logs, DNS logging)
- Configuración mínima para testing rápido
- **Corporate tagging policy aplicada** vía `local.all_tags` (consistente con producción)

```powershell
# Desde el directorio terraform/
cd terraform

# Inicializar Terraform
terraform init

# Ver el plan
terraform plan -var-file="localstack.tfvars"

# Aplicar la configuración
terraform apply -var-file="localstack.tfvars" -auto-approve
```

O usa el script PowerShell:
```powershell
# Desde la raíz del proyecto
.\scripts\terraform-localstack.ps1 -Action init
.\scripts\terraform-localstack.ps1 -Action plan
.\scripts\terraform-localstack.ps1 -Action apply
```

### 4. Verificar Recursos Creados

```powershell
# Listar VPCs
aws --endpoint-url=http://localhost:4566 ec2 describe-vpcs

# Listar Security Groups
aws --endpoint-url=http://localhost:4566 ec2 describe-security-groups

# Listar Subnets
aws --endpoint-url=http://localhost:4566 ec2 describe-subnets

# Ver outputs de Terraform
cd terraform
terraform output

# Deberías ver:
# vpc_id = "vpc-xxxxx"
# public_subnet_ids = ["subnet-xxxxx"]
# private_subnet_ids = ["subnet-xxxxx", "subnet-xxxxx"]
# security_group_ids = {...}
```

### 5. Detener LocalStack

```powershell
# Detener y remover contenedores
docker-compose -f docker-compose.localstack.yml down

# Nota: Con persistencia deshabilitada, todos los datos se eliminan automáticamente
```

O usa el script:
```bash
bash scripts/localstack-stop.sh
```

### 6. Reiniciar LocalStack

```powershell
# Reiniciar (empezará desde cero)
docker-compose -f docker-compose.localstack.yml restart

# O detener y volver a iniciar
docker-compose -f docker-compose.localstack.yml down
docker-compose -f docker-compose.localstack.yml up -d
```

## Comandos Útiles

### AWS CLI con LocalStack

Todos los comandos AWS CLI necesitan el flag `--endpoint-url`:

```powershell
# Configurar alias (opcional)
Set-Alias awslocal 'aws --endpoint-url=http://localhost:4566'

# Ejemplos
awslocal s3 mb s3://test-bucket
awslocal s3 ls
awslocal ec2 describe-vpcs
awslocal lambda list-functions
```

### Terraform

```powershell
# Ver estado actual
terraform show

# Listar recursos
terraform state list

# Ver un recurso específico
terraform state show module.vpc.aws_vpc.main

# Destruir todo
terraform destroy -var-file="localstack.tfvars" -auto-approve
```

### Docker

```powershell
# Ver logs de LocalStack
docker logs -f localstack-janis-cencosud

# Reiniciar LocalStack
docker restart localstack-janis-cencosud

# Ver recursos de Docker
docker stats localstack-janis-cencosud
```

## Limitaciones de LocalStack

LocalStack Community (gratuito) tiene algunas limitaciones:

### Servicios Completamente Soportados
- ✅ **S3**: Buckets, objetos, lifecycle policies
- ✅ **Lambda**: Funciones, layers, triggers
- ✅ **API Gateway**: REST APIs, stages, deployments
- ✅ **DynamoDB**: Tablas, índices, streams
- ✅ **Kinesis**: Streams, Firehose (básico)
- ✅ **CloudWatch**: Logs, métricas básicas
- ✅ **IAM**: Roles, policies, usuarios
- ✅ **STS**: AssumeRole, credenciales temporales
- ✅ **Secrets Manager**: Secretos, rotación básica
- ✅ **KMS**: Claves, cifrado/descifrado
- ✅ **EC2**: VPC, subnets, security groups, NAT (emulado)
- ✅ **EventBridge**: Event buses, rules, targets

### Servicios con Funcionalidad Limitada
- ⚠️ **Glue**: Data Catalog básico, jobs no ejecutan PySpark real
- ⚠️ **Redshift**: Emulación básica, no performance real
- ⚠️ **VPC Endpoints**: Creados pero no afectan routing real

### Servicios No Soportados (Community)
- ❌ **MWAA**: Managed Airflow no disponible en Community
- ❌ **WAF**: No soportado en Community
- ❌ **GuardDuty**: No soportado en Community

Para features completos, considera [LocalStack Pro](https://localstack.cloud/pricing/).

## Troubleshooting

### LocalStack no inicia
```powershell
# Verificar Docker está corriendo
docker info

# Ver logs detallados
docker-compose -f docker-compose.localstack.yml logs

# Verificar puertos disponibles
netstat -an | findstr "4566"

# Reiniciar Docker Desktop y volver a intentar
docker-compose -f docker-compose.localstack.yml restart
```

### Error: "Cannot connect to Docker daemon"
```powershell
# En Windows, asegúrate que Docker Desktop está corriendo
# Verifica en la bandeja del sistema

# Verifica que Docker socket está disponible
docker ps
```

### Terraform falla al conectar
```powershell
# Verificar que LocalStack está corriendo
curl http://localhost:4566/_localstack/health

# Verificar endpoints en providers.tf
# Deben apuntar a localhost:4566

# Verificar variables de entorno
echo $env:AWS_ENDPOINT_URL
```

### Recursos no se crean
```powershell
# Ver logs detallados de Terraform
$env:TF_LOG="DEBUG"
terraform apply -var-file="localstack.tfvars"

# Ver logs de LocalStack en tiempo real
docker-compose -f docker-compose.localstack.yml logs -f

# Verificar servicio específico
curl http://localhost:4566/_localstack/health | jq '.services.ec2'
```

### Persistencia no funciona
```powershell
# Nota: La persistencia está deshabilitada por defecto en este proyecto
# Esto significa que LocalStack empezará limpio en cada inicio
# Para habilitar persistencia, edita docker-compose.localstack.yml:
#   - PERSISTENCE=1
# Y agrega el volumen:
#   - "./localstack-data:/tmp/localstack"
```

### Puerto 4566 ya en uso
```powershell
# Encontrar proceso usando el puerto
netstat -ano | findstr "4566"

# Detener el proceso o cambiar el puerto en docker-compose.localstack.yml
# Cambiar "4566:4566" a "4567:4566" por ejemplo
```

## Workflow de Desarrollo

### Ciclo de Desarrollo Típico

1. **Iniciar LocalStack**
   ```powershell
   docker-compose -f docker-compose.localstack.yml up -d
   ```

2. **Desarrollar**: Escribe tu código Terraform en `terraform/`

3. **Probar localmente**: Despliega en LocalStack
   ```powershell
   cd terraform
   terraform init
   terraform apply -var-file="localstack.tfvars" -auto-approve
   ```

4. **Validar**: Verifica que los recursos se crean correctamente
   ```powershell
   terraform output
   aws --endpoint-url=http://localhost:4566 ec2 describe-vpcs
   ```

5. **Iterar**: Ajusta código y vuelve a desplegar
   ```powershell
   terraform apply -var-file="localstack.tfvars" -auto-approve
   ```

6. **Limpiar**: Destruye recursos cuando termines la sesión
   ```powershell
   terraform destroy -var-file="localstack.tfvars" -auto-approve
   ```

7. **Detener LocalStack**: Los datos se eliminan automáticamente
   ```powershell
   docker-compose -f docker-compose.localstack.yml down
   ```

8. **Desplegar a AWS**: Una vez validado, despliega a AWS real
   ```powershell
   cd terraform/environments/dev
   terraform init
   terraform apply -var-file="dev.tfvars"
   ```

### Persistencia de Datos

LocalStack está configurado **sin persistencia** por defecto:

- **Comportamiento**: Los recursos se eliminan al detener LocalStack
- **Beneficio**: Cada sesión empieza limpia, sin estado residual
- **Uso**: Ideal para testing rápido y desarrollo iterativo
- **Habilitar persistencia**: Si necesitas mantener datos entre sesiones, edita `docker-compose.localstack.yml`:
  ```yaml
  environment:
    - PERSISTENCE=1
  volumes:
    - "./localstack-data:/tmp/localstack"
  ```

```powershell
# Con persistencia deshabilitada (configuración actual)
# Los datos se eliminan automáticamente al detener LocalStack
docker-compose -f docker-compose.localstack.yml down

# Para empezar una nueva sesión limpia
docker-compose -f docker-compose.localstack.yml up -d
```

## Configuración Avanzada

### Variables de Entorno de LocalStack

El archivo `docker-compose.localstack.yml` configura las siguientes variables:

- `SERVICES`: Lista de servicios AWS a emular
- `DEBUG=1`: Habilita logs detallados para troubleshooting
- `LAMBDA_EXECUTOR=docker`: Ejecuta Lambdas en contenedores Docker
- `DOCKER_HOST=unix:///var/run/docker.sock`: Acceso al Docker daemon
- `AWS_DEFAULT_REGION=us-east-1`: Región por defecto (igual que producción)
- `PERSISTENCE=0`: Persistencia deshabilitada (configuración limpia en cada inicio)

### Personalizar Configuración

Puedes modificar `docker-compose.localstack.yml` para:

```yaml
# Agregar más servicios
environment:
  - SERVICES=s3,lambda,apigateway,kinesis,glue,redshift,secretsmanager,cloudwatch,events,iam,sts,kms,ec2,vpc,sns,sqs

# Cambiar nivel de debug
environment:
  - DEBUG=0  # Desactivar logs detallados

# Cambiar región
environment:
  - AWS_DEFAULT_REGION=us-west-2

# Habilitar persistencia (mantener datos entre sesiones)
environment:
  - PERSISTENCE=1
volumes:
  - "./localstack-data:/tmp/localstack"
```

### Recursos de Docker

LocalStack puede consumir recursos significativos:

- **RAM**: 2-4 GB recomendado
- **CPU**: 2+ cores recomendado
- **Disco**: Variable según datos persistidos

Ajustar en Docker Desktop → Settings → Resources si es necesario.

## Próximos Pasos

Una vez que tengas la infraestructura básica funcionando en LocalStack:

1. Agrega módulos de Lambda
2. Configura API Gateway
3. Crea buckets S3 para el Data Lake
4. Prueba el flujo completo de datos

## Recursos

- [LocalStack Docs](https://docs.localstack.cloud/)
- [LocalStack AWS CLI](https://docs.localstack.cloud/user-guide/integrations/aws-cli/)
- [Terraform con LocalStack](https://docs.localstack.cloud/user-guide/integrations/terraform/)
