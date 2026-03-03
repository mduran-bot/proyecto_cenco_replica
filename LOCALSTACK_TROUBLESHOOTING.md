# 🔧 LocalStack Troubleshooting

## Error: Token '}' inesperado / Missing Catch or Finally

Este error ocurre por problemas de sintaxis en PowerShell. Usa el script simplificado:

```powershell
.\scripts\start-localstack-simple.ps1
```

---

## Solución Rápida: Comandos Manuales

Si los scripts fallan, ejecuta estos comandos uno por uno:

### 1. Iniciar LocalStack

```powershell
docker-compose -f docker-compose.localstack.yml up -d
```

Espera 30 segundos:
```powershell
Start-Sleep -Seconds 30
```

### 2. Verificar LocalStack

```powershell
curl http://localhost:4566/_localstack/health
```

O con PowerShell:
```powershell
Invoke-WebRequest -Uri http://localhost:4566/_localstack/health
```

### 3. Inicializar Terraform

```powershell
cd terraform
terraform init
```

### 4. Validar

```powershell
terraform validate
```

### 5. Desplegar

```powershell
terraform plan -var-file="terraform.tfvars"
terraform apply -var-file="terraform.tfvars" -auto-approve
```

### 6. Ver Resultados

```powershell
terraform output
terraform state list
```

---

## Errores Comunes

### Error: "Docker is not running"

**Solución:**
1. Abre Docker Desktop
2. Espera a que el ícono muestre "Docker Desktop is running"
3. Verifica: `docker info`

### Error: "Connection refused to localhost:4566"

**Solución:**
```powershell
# Ver si LocalStack está corriendo
docker ps | findstr localstack

# Si no está, iniciarlo
docker-compose -f docker-compose.localstack.yml up -d

# Esperar
Start-Sleep -Seconds 30

# Verificar
curl http://localhost:4566/_localstack/health
```

### Error: "Module not installed"

**Solución:**
```powershell
cd terraform
Remove-Item .terraform -Recurse -Force -ErrorAction SilentlyContinue
terraform init
```

### Error: "Error acquiring the state lock"

**Solución:**
```powershell
cd terraform
# Usar el Lock ID del mensaje de error
terraform force-unlock <LOCK_ID>
```

### Error: Terraform apply falla

**Solución:**
```powershell
# Ver logs detallados
$env:TF_LOG="DEBUG"
cd terraform
terraform apply -var-file="terraform.tfvars"

# Ver logs de LocalStack
docker logs localstack-janis-cencosud --tail 100
```

---

## Reiniciar Todo

Si nada funciona, reinicia desde cero:

```powershell
# 1. Destruir infraestructura (si existe)
cd terraform
terraform destroy -var-file="terraform.tfvars" -auto-approve
cd ..

# 2. Detener LocalStack
docker-compose -f docker-compose.localstack.yml down

# 3. Limpiar archivos
cd terraform
Remove-Item terraform.tfstate* -Force -ErrorAction SilentlyContinue
Remove-Item .terraform -Recurse -Force -ErrorAction SilentlyContinue
cd ..

# 4. Iniciar de nuevo
docker-compose -f docker-compose.localstack.yml up -d
Start-Sleep -Seconds 30

# 5. Desplegar
cd terraform
terraform init
terraform apply -var-file="terraform.tfvars" -auto-approve
```

---

## Verificar Estado

### LocalStack

```powershell
# Ver contenedor
docker ps | findstr localstack

# Ver logs
docker logs localstack-janis-cencosud --tail 50

# Ver health
curl http://localhost:4566/_localstack/health
```

### Terraform

```powershell
cd terraform

# Ver estado
terraform show

# Listar recursos
terraform state list

# Contar recursos
terraform state list | Measure-Object -Line
```

---

## Scripts Disponibles

### Script Simple (Recomendado si hay errores)

```powershell
.\scripts\start-localstack-simple.ps1
```

### Script Completo (Con validaciones)

```powershell
.\scripts\init-localstack.ps1
```

### Script de Verificación

```powershell
.\scripts\verify-localstack.ps1
```

---

## Comandos Útiles

### Docker

```powershell
# Ver contenedores corriendo
docker ps

# Ver todos los contenedores
docker ps -a

# Ver logs en tiempo real
docker logs localstack-janis-cencosud -f

# Reiniciar LocalStack
docker-compose -f docker-compose.localstack.yml restart

# Detener LocalStack
docker-compose -f docker-compose.localstack.yml down

# Iniciar LocalStack
docker-compose -f docker-compose.localstack.yml up -d
```

### Terraform

```powershell
cd terraform

# Formatear código
terraform fmt -recursive

# Validar
terraform validate

# Plan
terraform plan -var-file="terraform.tfvars"

# Apply
terraform apply -var-file="terraform.tfvars"

# Destroy
terraform destroy -var-file="terraform.tfvars"

# Ver outputs
terraform output

# Ver recursos
terraform state list

# Ver recurso específico
terraform state show module.vpc.aws_vpc.main
```

### AWS CLI con LocalStack

```powershell
# VPC
aws --endpoint-url=http://localhost:4566 ec2 describe-vpcs

# Subnets
aws --endpoint-url=http://localhost:4566 ec2 describe-subnets

# Security Groups
aws --endpoint-url=http://localhost:4566 ec2 describe-security-groups

# Route Tables
aws --endpoint-url=http://localhost:4566 ec2 describe-route-tables
```

---

## Logs de Debug

### Terraform Debug

```powershell
$env:TF_LOG="DEBUG"
$env:TF_LOG_PATH="terraform-debug.log"
cd terraform
terraform apply -var-file="terraform.tfvars"

# Ver log
Get-Content terraform-debug.log -Tail 50
```

### LocalStack Debug

```powershell
# Ver logs completos
docker logs localstack-janis-cencosud

# Ver últimas 100 líneas
docker logs localstack-janis-cencosud --tail 100

# Seguir logs en tiempo real
docker logs localstack-janis-cencosud -f
```

---

## Limpiar Completamente

```powershell
# Detener todo
docker-compose -f docker-compose.localstack.yml down

# Limpiar volúmenes (opcional)
docker volume prune -f

# Limpiar Terraform
cd terraform
Remove-Item terraform.tfstate* -Force -ErrorAction SilentlyContinue
Remove-Item .terraform -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item .terraform.lock.hcl -Force -ErrorAction SilentlyContinue
cd ..

# Reiniciar Docker Desktop (si es necesario)
# Cerrar y abrir Docker Desktop
```

---

## Contacto y Ayuda

Si sigues teniendo problemas:

1. **Revisa logs:**
   ```powershell
   docker logs localstack-janis-cencosud --tail 100
   ```

2. **Verifica Docker:**
   ```powershell
   docker info
   docker ps
   ```

3. **Verifica Terraform:**
   ```powershell
   cd terraform
   terraform version
   terraform validate
   ```

4. **Usa el script simple:**
   ```powershell
   .\scripts\start-localstack-simple.ps1
   ```

---

## Checklist de Diagnóstico

- [ ] Docker Desktop está corriendo
- [ ] `docker info` funciona
- [ ] LocalStack container está up: `docker ps | findstr localstack`
- [ ] LocalStack responde: `curl http://localhost:4566/_localstack/health`
- [ ] Terraform está instalado: `terraform version`
- [ ] Estás en el directorio correcto
- [ ] No hay otros procesos usando puerto 4566

---

**Tip:** Si todo falla, usa los comandos manuales paso a paso en lugar de los scripts.
