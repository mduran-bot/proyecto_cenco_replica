# ✅ LocalStack: Listo para Iniciar

## 🎯 Objetivo

Probar toda la infraestructura localmente con LocalStack antes de deployar en AWS real.

---

## ⚡ Inicio Rápido (3 minutos)

### Opción 1: Script Automático (Recomendado)

```powershell
# Desde la raíz del proyecto
.\scripts\init-localstack.ps1
```

**Eso es todo!** El script hace todo automáticamente.

### Opción 2: Manual

```powershell
# 1. Iniciar LocalStack
docker-compose -f docker-compose.localstack.yml up -d
Start-Sleep -Seconds 30

# 2. Desplegar infraestructura
cd terraform
terraform init
terraform apply -var-file="terraform.tfvars" -auto-approve
```

---

## 🔍 Verificar que Todo Funciona

```powershell
# Ejecutar script de verificación
.\scripts\verify-localstack.ps1
```

Deberías ver:
```
✓ Docker is running
✓ LocalStack container is running
✓ LocalStack is responding
✓ Terraform installed
✓ Terraform state exists
✓ All critical checks passed!
```

---

## 📊 Ver Recursos Creados

### Con Terraform

```powershell
cd terraform

# Ver outputs
terraform output

# Listar todos los recursos
terraform state list

# Ver detalles de un recurso
terraform state show module.vpc.aws_vpc.main
```

### Con AWS CLI

```powershell
# VPC
aws --endpoint-url=http://localhost:4566 ec2 describe-vpcs

# Subnets
aws --endpoint-url=http://localhost:4566 ec2 describe-subnets \
  --query 'Subnets[*].[SubnetId,CidrBlock,Tags[?Key==`Name`].Value|[0]]' \
  --output table

# Security Groups
aws --endpoint-url=http://localhost:4566 ec2 describe-security-groups \
  --query 'SecurityGroups[*].[GroupId,GroupName]' \
  --output table

# Route Tables
aws --endpoint-url=http://localhost:4566 ec2 describe-route-tables \
  --query 'RouteTables[*].[RouteTableId,Tags[?Key==`Name`].Value|[0]]' \
  --output table
```

---

## 🎨 Recursos Creados

Cuando despliegas en LocalStack, se crean aproximadamente **35-40 recursos**:

### Networking (Core)
- ✅ 1 VPC (10.0.0.0/16)
- ✅ 3 Subnets (1 pública, 2 privadas en us-east-1a)
- ✅ 1 Internet Gateway
- ✅ 1 NAT Gateway (emulado)
- ✅ 3 Route Tables
- ✅ 6 Route Table Associations

### Security
- ✅ 7 Security Groups:
  - API Gateway
  - Redshift
  - Lambda
  - MWAA
  - Glue
  - EventBridge
  - VPC Endpoints
- ✅ 2 Network ACLs (Public y Private)
- ✅ ~20 Security Group Rules

### Orchestration
- ✅ 1 EventBridge Custom Event Bus
- ✅ 5 EventBridge Scheduled Rules:
  - Orders polling (cada 5 min)
  - Products polling (cada 60 min)
  - Stock polling (cada 10 min)
  - Prices polling (cada 30 min)
  - Stores polling (cada 24 hrs)
- ✅ 1 Dead Letter Queue (SQS)

### Monitoring
- ✅ CloudWatch Log Groups (básicos)

---

## 🧪 Probar Cambios

### 1. Modificar Configuración

Edita `terraform/terraform.tfvars`:

```hcl
# Ejemplo: Cambiar CIDR de VPC
vpc_cidr = "10.1.0.0/16"

# Ejemplo: Cambiar frecuencia de polling
order_polling_rate_minutes = 10
```

### 2. Ver Cambios

```powershell
cd terraform
terraform plan -var-file="terraform.tfvars"
```

### 3. Aplicar Cambios

```powershell
terraform apply -var-file="terraform.tfvars" -auto-approve
```

---

## 🔄 Comandos Útiles

### Ver Estado

```powershell
cd terraform

# Outputs
terraform output

# Recursos
terraform state list

# Contar recursos
terraform state list | Measure-Object -Line
```

### Logs

```powershell
# Logs de LocalStack (últimas 50 líneas)
docker logs localstack-janis-cencosud --tail 50

# Logs en tiempo real
docker logs localstack-janis-cencosud -f

# Logs de Terraform (debug)
$env:TF_LOG="DEBUG"
cd terraform
terraform apply -var-file="terraform.tfvars"
```

### Reiniciar

```powershell
# Reiniciar LocalStack
docker-compose -f docker-compose.localstack.yml restart
Start-Sleep -Seconds 30

# Reiniciar todo (destruir y recrear)
.\scripts\init-localstack.ps1 -DestroyFirst
```

---

## 🧹 Limpiar

### Destruir Infraestructura

```powershell
cd terraform
terraform destroy -var-file="terraform.tfvars" -auto-approve
```

### Detener LocalStack

```powershell
docker-compose -f docker-compose.localstack.yml down
```

### Limpiar Todo

```powershell
# Destruir infraestructura
cd terraform
terraform destroy -var-file="terraform.tfvars" -auto-approve

# Detener LocalStack
cd ..
docker-compose -f docker-compose.localstack.yml down

# Limpiar archivos de estado
cd terraform
Remove-Item terraform.tfstate* -Force
Remove-Item .terraform -Recurse -Force
```

---

## 🐛 Troubleshooting

### LocalStack no inicia

```powershell
# Ver logs
docker logs localstack-janis-cencosud

# Reiniciar
docker-compose -f docker-compose.localstack.yml restart

# Recrear
docker-compose -f docker-compose.localstack.yml down
docker-compose -f docker-compose.localstack.yml up -d
```

### Terraform falla

```powershell
# Verificar LocalStack
curl http://localhost:4566/_localstack/health

# Reinicializar Terraform
cd terraform
Remove-Item .terraform -Recurse -Force
terraform init

# Aplicar de nuevo
terraform apply -var-file="terraform.tfvars" -auto-approve
```

### "Cannot connect to Docker"

```powershell
# Iniciar Docker Desktop
# Esperar a que esté listo
docker info
```

### Recursos no se crean

```powershell
# Ver logs detallados
$env:TF_LOG="DEBUG"
cd terraform
terraform apply -var-file="terraform.tfvars"

# Ver logs de LocalStack
docker logs localstack-janis-cencosud --tail 100
```

---

## 📚 Documentación

### Guías
- **Quick Start:** `QUICK_START_LOCALSTACK.md` (5 minutos)
- **Guía Completa:** `GUIA_INICIO_LOCALSTACK.md` (paso a paso)
- **Configuración:** `terraform/LOCALSTACK_CONFIG.md`
- **README:** `README-LOCALSTACK.md`

### Scripts
- **Inicializar:** `scripts/init-localstack.ps1`
- **Verificar:** `scripts/verify-localstack.ps1`

---

## ✅ Checklist

Antes de ir a AWS, verifica en LocalStack:

- [ ] LocalStack inicia correctamente
- [ ] Terraform init funciona
- [ ] Terraform plan no tiene errores
- [ ] Terraform apply crea todos los recursos
- [ ] Outputs muestran valores correctos
- [ ] AWS CLI puede consultar recursos
- [ ] Tags corporativos están aplicados
- [ ] Security Groups tienen reglas correctas
- [ ] Subnets tienen CIDRs correctos
- [ ] Route Tables tienen rutas correctas

---

## 🚀 Próximos Pasos

Una vez que todo funciona en LocalStack:

### 1. Completar Tags Corporativos

Ver `QUICK_TAGGING_GUIDE.md` para actualizar módulos restantes.

### 2. Validar Configuración

```powershell
cd terraform
terraform fmt -recursive
terraform validate
.\scripts\validate-corporate-tags.ps1 -Environment dev
```

### 3. Deployar en AWS Dev

```powershell
# Asegúrate de NO usar localstack_override.tf
# Usa el archivo de ambiente correcto
cd terraform
terraform init
terraform plan -var-file="environments/dev/dev.tfvars"
terraform apply -var-file="environments/dev/dev.tfvars"
```

---

## 💡 Consejos

1. **Siempre usa LocalStack primero** para probar cambios
2. **Espera 30 segundos** después de iniciar LocalStack
3. **Revisa logs** si algo no funciona
4. **Usa `terraform plan`** antes de `apply`
5. **Destruye y recrea** si ves comportamiento extraño
6. **LocalStack es gratis** - úsalo sin miedo!

---

## 🎯 Resumen

```powershell
# Iniciar todo
.\scripts\init-localstack.ps1

# Verificar
.\scripts\verify-localstack.ps1

# Ver recursos
cd terraform && terraform output

# Limpiar
cd terraform && terraform destroy -var-file="terraform.tfvars" -auto-approve
docker-compose -f docker-compose.localstack.yml down
```

---

**¡Listo para probar!** LocalStack te permite validar toda la infraestructura sin costos de AWS. 🎉

**Tiempo total:** 3-5 minutos desde cero hasta infraestructura completa desplegada.
