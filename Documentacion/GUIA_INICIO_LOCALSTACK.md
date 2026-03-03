# Guía de Inicio: LocalStack y Terraform

Esta guía te llevará paso a paso desde cero hasta tener LocalStack corriendo con toda la infraestructura desplegada.

## 📋 Pre-requisitos

Antes de empezar, verifica que tienes instalado:

```powershell
# Verificar Docker
docker --version
# Debe mostrar: Docker version 20.x.x o superior

# Verificar Terraform
terraform --version
# Debe mostrar: Terraform v1.x.x o superior

# Verificar AWS CLI (opcional pero recomendado)
aws --version
# Debe mostrar: aws-cli/2.x.x
```

Si falta algo:
- **Docker Desktop**: https://www.docker.com/products/docker-desktop/
- **Terraform**: https://www.terraform.io/downloads
- **AWS CLI**: https://aws.amazon.com/cli/

---

## 🚀 Paso 1: Iniciar Docker Desktop

1. Abre **Docker Desktop** desde el menú de inicio
2. Espera a que el ícono de Docker en la bandeja del sistema muestre "Docker Desktop is running"
3. Verifica que está corriendo:

```powershell
docker info
```

Si ves información del sistema Docker, estás listo para continuar.

---

## 🐳 Paso 2: Iniciar LocalStack

Desde la raíz del proyecto:

```powershell
# Iniciar LocalStack en background
docker-compose -f docker-compose.localstack.yml up -d
```

Deberías ver:
```
Creating network "janis-cencosud-integration_localstack-network" ... done
Creating localstack-janis-cencosud ... done
```

### Verificar que LocalStack está corriendo

```powershell
# Ver el contenedor
docker ps | findstr localstack

# Ver los logs (últimas 50 líneas)
docker logs localstack-janis-cencosud --tail 50

# Verificar health check
curl http://localhost:4566/_localstack/health
```

El health check debe mostrar servicios en estado "running":
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

**⏱️ Espera 30-60 segundos** después de iniciar LocalStack antes de continuar. Los servicios necesitan tiempo para inicializarse.

---

## 🏗️ Paso 3: Inicializar Terraform

Navega al directorio de Terraform:

```powershell
cd terraform
```

### Inicializar Terraform (primera vez)

```powershell
terraform init
```

Deberías ver:
```
Initializing modules...
Initializing the backend...
Initializing provider plugins...
Terraform has been successfully initialized!
```

---

## 📝 Paso 4: Planificar el Despliegue

Antes de crear recursos, revisa qué se va a crear:

```powershell
terraform plan -var-file="localstack.tfvars"
```

Verás una lista de todos los recursos que Terraform va a crear:
- VPC
- Subnets (pública y privadas)
- Internet Gateway
- NAT Gateway
- Security Groups
- Route Tables
- NACLs
- EventBridge rules
- Y más...

Revisa el output y asegúrate de que todo se ve correcto.

---

## ✅ Paso 5: Aplicar la Configuración

Ahora sí, crea todos los recursos en LocalStack:

```powershell
terraform apply -var-file="localstack.tfvars" -auto-approve
```

Este comando:
1. Crea todos los recursos en LocalStack
2. Guarda el estado en `terraform.tfstate`
3. Muestra los outputs al final

**⏱️ Esto puede tomar 2-5 minutos** dependiendo de tu máquina.

Al finalizar verás:
```
Apply complete! Resources: XX added, 0 changed, 0 destroyed.

Outputs:

vpc_id = "vpc-xxxxx"
public_subnet_ids = ["subnet-xxxxx"]
private_subnet_ids = ["subnet-xxxxx", "subnet-xxxxx"]
...
```

---

## 🔍 Paso 6: Verificar los Recursos Creados

### Ver outputs de Terraform

```powershell
terraform output
```

### Ver recursos en LocalStack con AWS CLI

```powershell
# Ver la VPC
aws --endpoint-url=http://localhost:4566 ec2 describe-vpcs

# Ver subnets
aws --endpoint-url=http://localhost:4566 ec2 describe-subnets --query 'Subnets[*].[SubnetId,CidrBlock,Tags[?Key==`Name`].Value|[0]]' --output table

# Ver security groups
aws --endpoint-url=http://localhost:4566 ec2 describe-security-groups --query 'SecurityGroups[*].[GroupId,GroupName]' --output table

# Ver route tables
aws --endpoint-url=http://localhost:4566 ec2 describe-route-tables --query 'RouteTables[*].[RouteTableId,Tags[?Key==`Name`].Value|[0]]' --output table
```

---

## 🎯 Resumen de Comandos Rápidos

### Iniciar todo desde cero

```powershell
# 1. Iniciar LocalStack
docker-compose -f docker-compose.localstack.yml up -d

# 2. Esperar 30 segundos
Start-Sleep -Seconds 30

# 3. Ir a terraform
cd terraform

# 4. Inicializar (solo primera vez)
terraform init

# 5. Desplegar
terraform apply -var-file="localstack.tfvars" -auto-approve
```

### Ver estado actual

```powershell
# Ver outputs
terraform output

# Ver todos los recursos
terraform state list

# Ver un recurso específico
terraform state show module.vpc.aws_vpc.main
```

### Limpiar y empezar de nuevo

```powershell
# Destruir recursos en LocalStack
terraform destroy -var-file="localstack.tfvars" -auto-approve

# Detener LocalStack
cd ..
docker-compose -f docker-compose.localstack.yml down

# Volver a iniciar
docker-compose -f docker-compose.localstack.yml up -d
```

---

## 🛠️ Scripts de Ayuda

El proyecto incluye scripts PowerShell para facilitar el trabajo:

### Script de despliegue completo

```powershell
# Desde la raíz del proyecto
.\scripts\deploy-localstack.ps1 -Action init    # Inicializar
.\scripts\deploy-localstack.ps1 -Action plan    # Ver plan
.\scripts\deploy-localstack.ps1 -Action apply   # Aplicar
.\scripts\deploy-localstack.ps1 -Action output  # Ver outputs
.\scripts\deploy-localstack.ps1 -Action destroy # Destruir
```

---

## ❌ Troubleshooting

**📖 GUÍA COMPLETA DE TROUBLESHOOTING:** Ver **[LOCALSTACK_TROUBLESHOOTING.md](LOCALSTACK_TROUBLESHOOTING.md)** para soluciones detalladas a todos los problemas comunes.

### Errores Más Comunes

#### Error: "Cannot connect to Docker daemon"

**Solución**: Asegúrate de que Docker Desktop está corriendo.

```powershell
# Verificar Docker
docker info
```

#### Error: "Connection refused to localhost:4566"

**Solución**: LocalStack no está corriendo o no está listo.

```powershell
# Ver si el contenedor está corriendo
docker ps | findstr localstack

# Ver logs para errores
docker logs localstack-janis-cencosud

# Reiniciar LocalStack
docker-compose -f docker-compose.localstack.yml restart

# Esperar 30 segundos
Start-Sleep -Seconds 30
```

#### Error: "Module not installed"

**Solución**: Necesitas inicializar Terraform.

```powershell
cd terraform
terraform init
```

#### Error: Scripts de PowerShell fallan

**Solución**: Usa comandos manuales o el script simplificado.

```powershell
# Opción 1: Script simplificado
.\scripts\start-localstack-simple.ps1

# Opción 2: Comandos manuales paso a paso
# Ver LOCALSTACK_TROUBLESHOOTING.md para la lista completa
```

### Más Ayuda

Para soluciones detalladas a estos y otros problemas, consulta:
- **[LOCALSTACK_TROUBLESHOOTING.md](LOCALSTACK_TROUBLESHOOTING.md)** - Guía completa de troubleshooting
- **[GUIA_LOCALSTACK.md](GUIA_LOCALSTACK.md)** - Guía de uso de LocalStack
- **[README-LOCALSTACK.md](README-LOCALSTACK.md)** - Documentación completa

---

## 📊 Verificación Completa

Ejecuta este script para verificar que todo está funcionando:

```powershell
# Verificar Docker
Write-Host "✓ Verificando Docker..." -ForegroundColor Yellow
docker info | Out-Null
if ($?) { Write-Host "  ✓ Docker OK" -ForegroundColor Green } else { Write-Host "  ✗ Docker no está corriendo" -ForegroundColor Red }

# Verificar LocalStack
Write-Host "✓ Verificando LocalStack..." -ForegroundColor Yellow
$response = Invoke-WebRequest -Uri http://localhost:4566/_localstack/health -UseBasicParsing -ErrorAction SilentlyContinue
if ($response.StatusCode -eq 200) { Write-Host "  ✓ LocalStack OK" -ForegroundColor Green } else { Write-Host "  ✗ LocalStack no responde" -ForegroundColor Red }

# Verificar Terraform
Write-Host "✓ Verificando Terraform..." -ForegroundColor Yellow
cd terraform
$tfState = Test-Path "terraform.tfstate"
if ($tfState) { Write-Host "  ✓ Terraform state existe" -ForegroundColor Green } else { Write-Host "  ✗ No hay state de Terraform" -ForegroundColor Yellow }

# Ver recursos
Write-Host "`n✓ Recursos creados:" -ForegroundColor Yellow
terraform state list 2>$null | Measure-Object -Line | ForEach-Object { Write-Host "  $($_.Lines) recursos" -ForegroundColor Cyan }
```

---

## 🎓 Próximos Pasos

Una vez que tengas todo funcionando:

1. **Explora los recursos**: Usa AWS CLI para ver los recursos creados
2. **Modifica la configuración**: Edita archivos `.tf` y vuelve a aplicar
3. **Agrega más módulos**: Lambda, API Gateway, S3, etc.
4. **Prueba el flujo completo**: Simula el pipeline de datos

---

## 📚 Archivos de Referencia

- `docker-compose.localstack.yml` - Configuración de LocalStack
- `terraform/localstack.tfvars` - Variables para LocalStack
- `terraform/localstack_override.tf` - Override de endpoints para LocalStack
- `GUIA_LOCALSTACK.md` - Guía detallada de LocalStack
- `README-LOCALSTACK.md` - Documentación completa

---

## 💡 Consejos

1. **Siempre espera** 30-60 segundos después de iniciar LocalStack
2. **Revisa los logs** si algo no funciona: `docker logs localstack-janis-cencosud`
3. **Usa `terraform plan`** antes de `apply` para ver qué va a cambiar
4. **Guarda el output** de `terraform output` para referencia
5. **Reinicia LocalStack** si ves comportamiento extraño

---

## 🆘 Ayuda Adicional

Si tienes problemas:

1. Revisa los logs de LocalStack: `docker logs localstack-janis-cencosud --tail 100`
2. Revisa los logs de Terraform: `$env:TF_LOG="DEBUG"` antes de ejecutar comandos
3. Consulta la documentación oficial: https://docs.localstack.cloud/
4. Revisa los archivos de troubleshooting en el proyecto

---

**¡Listo!** Ahora tienes LocalStack corriendo con toda la infraestructura AWS desplegada localmente. 🎉
