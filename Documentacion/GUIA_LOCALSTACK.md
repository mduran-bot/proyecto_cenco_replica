# Guía Rápida de LocalStack

Esta guía te ayudará a iniciar LocalStack y desplegar la infraestructura VPC localmente para pruebas.

## 📖 Guía Completa para Principiantes

**¿Primera vez con LocalStack?** Lee la **[GUIA_INICIO_LOCALSTACK.md](GUIA_INICIO_LOCALSTACK.md)** para una guía paso a paso completa desde cero.

## 🚀 Inicio Rápido

### 1. Iniciar LocalStack

LocalStack ya está corriendo en tu sistema. Puedes verificarlo con:

```powershell
docker ps | findstr localstack
```

Si no está corriendo, inícialo con:

```powershell
docker-compose -f docker-compose.localstack.yml up -d
```

### 2. Verificar Estado de LocalStack

```powershell
# Ver logs
docker logs localstack-janis-cencosud --tail 50

# Verificar servicios disponibles
Invoke-WebRequest -Uri http://localhost:4566/_localstack/health -UseBasicParsing | Select-Object -ExpandProperty Content
```

### 3. Desplegar la VPC

Usa el script PowerShell para facilitar el despliegue:

```powershell
# Paso 1: Inicializar Terraform
.\scripts\deploy-localstack.ps1 -Action init

# Paso 2: Ver el plan (qué se va a crear)
.\scripts\deploy-localstack.ps1 -Action plan

# Paso 3: Aplicar la configuración (crear recursos)
.\scripts\deploy-localstack.ps1 -Action apply

# Paso 4: Ver los outputs (IDs de recursos creados)
.\scripts\deploy-localstack.ps1 -Action output
```

## 📋 Comandos Útiles

### Ver Recursos Creados

```powershell
# Ver VPCs
aws --endpoint-url=http://localhost:4566 ec2 describe-vpcs

# Ver Subnets
aws --endpoint-url=http://localhost:4566 ec2 describe-subnets

# Ver Security Groups
aws --endpoint-url=http://localhost:4566 ec2 describe-security-groups

# Ver Route Tables
aws --endpoint-url=http://localhost:4566 ec2 describe-route-tables

# Ver Internet Gateways
aws --endpoint-url=http://localhost:4566 ec2 describe-internet-gateways

# Ver NAT Gateways
aws --endpoint-url=http://localhost:4566 ec2 describe-nat-gateways
```

### Terraform

```powershell
# Ver estado actual
cd terraform
terraform show

# Listar recursos
terraform state list

# Ver un recurso específico
terraform state show module.vpc.aws_vpc.main

# Ver outputs
terraform output

# Destruir todo
.\scripts\deploy-localstack.ps1 -Action destroy
```

## 🏗️ Recursos que se Crearán

Al ejecutar `apply`, se crearán los siguientes recursos en LocalStack:

### VPC Module
- ✅ VPC (10.0.0.0/16)
- ✅ Internet Gateway
- ✅ NAT Gateway (emulado con ID dummy: `dummy-nat-gateway-id`)
- ✅ Elastic IP (para NAT Gateway)
- ✅ 3 Subnets:
  - Public Subnet A (10.0.1.0/24)
  - Private Subnet 1A (10.0.11.0/24)
  - Private Subnet 2A (10.0.21.0/24)
- ✅ Route Tables (pública y privadas)
- ✅ Route Table Associations

### Security Groups Module
- ✅ API Gateway Security Group
- ✅ Lambda Security Group
- ✅ Glue Security Group
- ✅ VPC Endpoints Security Group
- ✅ Redshift Access Security Group

### NACLs Module
- ✅ Public Subnet NACL
- ✅ Private Subnet NACL

### WAF Module
- ⚠️ WAF disabled (enable_waf = false)
- ⚠️ Not supported in LocalStack Community

### EventBridge Module
- ✅ Custom Event Bus
- ✅ Scheduled Rules (polling)
- ✅ Dead Letter Queue (SQS)

### Monitoring Module
- ⚠️ VPC Flow Logs (deshabilitado en LocalStack)
- ⚠️ DNS Query Logging (deshabilitado en LocalStack)

## 🔍 Verificación de la VPC

Después de aplicar la configuración, verifica que la VPC se creó correctamente:

```powershell
# Ver detalles de la VPC
aws --endpoint-url=http://localhost:4566 ec2 describe-vpcs --query 'Vpcs[0]' --output json

# Ver subnets con sus CIDRs
aws --endpoint-url=http://localhost:4566 ec2 describe-subnets --query 'Subnets[*].[SubnetId,CidrBlock,AvailabilityZone]' --output table

# Ver security groups
aws --endpoint-url=http://localhost:4566 ec2 describe-security-groups --query 'SecurityGroups[*].[GroupId,GroupName]' --output table
```

## 🧹 Limpieza

Para destruir todos los recursos y empezar de nuevo:

```powershell
# Opción 1: Usar el script
.\scripts\deploy-localstack.ps1 -Action destroy

# Opción 2: Reiniciar LocalStack (elimina todo automáticamente)
docker-compose -f docker-compose.localstack.yml down
docker-compose -f docker-compose.localstack.yml up -d
```

## ⚠️ Limitaciones de LocalStack Community

- **VPC Endpoints**: Se crean pero no afectan el routing real
- **NAT Gateway**: Emulado con ID dummy (`dummy-nat-gateway-id`), no funciona como en AWS real
- **WAF**: Deshabilitado (enable_waf = false) - No soportado en Community
- **CloudWatch**: Métricas y logs básicos
- **EventBridge**: Funciona pero sin integración real con MWAA
- **Performance**: Operaciones muy lentas comparado con AWS real (5+ minutos vs segundos)
- **Stability**: Algunos recursos pueden atascarse durante deployment

**📖 Resultados de Testing**: Ver [terraform/DEPLOYMENT_STATUS_FINAL.md](terraform/DEPLOYMENT_STATUS_FINAL.md) para análisis completo de deployment en LocalStack, incluyendo:
- Qué módulos se despliegan exitosamente
- Qué recursos se atascan y por qué
- Recomendaciones para testing real vs LocalStack
- Comandos de verificación y troubleshooting

## 📚 Próximos Pasos

Una vez que la VPC esté funcionando en LocalStack:

1. ✅ Verificar que todos los recursos se crearon
2. ✅ Revisar los outputs de Terraform
3. ✅ Probar conectividad entre subnets
4. ⏭️ Agregar módulos de Lambda
5. ⏭️ Configurar API Gateway
6. ⏭️ Crear buckets S3 para el Data Lake

## 🆘 Troubleshooting

**📖 GUÍA COMPLETA:** Ver **[LOCALSTACK_TROUBLESHOOTING.md](../LOCALSTACK_TROUBLESHOOTING.md)** para soluciones detalladas.

### Errores Comunes

**Error: "LocalStack no está corriendo"**
```powershell
docker-compose -f docker-compose.localstack.yml up -d
docker logs localstack-janis-cencosud
```

**Error: "Terraform no puede conectar"**
```powershell
# Verificar que LocalStack está healthy
Invoke-WebRequest -Uri http://localhost:4566/_localstack/health -UseBasicParsing

# Verificar que el archivo localstack_override.tf existe
Get-Content terraform\localstack_override.tf
```

**Error: "Recursos no se crean"**
```powershell
# Ver logs de LocalStack en tiempo real
docker logs -f localstack-janis-cencosud

# Habilitar debug de Terraform
$env:TF_LOG="DEBUG"
.\scripts\deploy-localstack.ps1 -Action apply
```

**Error: Scripts de PowerShell fallan**
```powershell
# Usar comandos manuales paso a paso
# Ver LOCALSTACK_TROUBLESHOOTING.md para la lista completa
```

Para más soluciones, consulta [LOCALSTACK_TROUBLESHOOTING.md](../LOCALSTACK_TROUBLESHOOTING.md).

## 📖 Recursos Adicionales

- [LocalStack Docs](https://docs.localstack.cloud/)
- [Terraform con LocalStack](https://docs.localstack.cloud/user-guide/integrations/terraform/)
- [AWS CLI con LocalStack](https://docs.localstack.cloud/user-guide/integrations/aws-cli/)
