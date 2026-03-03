# 🚀 EMPIEZA AQUÍ: LocalStack

## ⚡ Opción 1: Script Simplificado (Recomendado)

```powershell
.\scripts\start-localstack-simple.ps1
```

Este script es más simple y no tiene problemas de sintaxis.

---

## ⚡ Opción 2: Comandos Manuales (Si el script falla)

Ejecuta estos comandos uno por uno:

### Paso 1: Iniciar LocalStack

```powershell
docker-compose -f docker-compose.localstack.yml up -d
```

### Paso 2: Esperar 30 segundos

```powershell
Start-Sleep -Seconds 30
```

### Paso 3: Verificar LocalStack

```powershell
curl http://localhost:4566/_localstack/health
```

### Paso 4: Ir a Terraform

```powershell
cd terraform
```

### Paso 5: Inicializar Terraform

```powershell
terraform init
```

### Paso 6: Validar

```powershell
terraform validate
```

### Paso 7: Desplegar

```powershell
terraform apply -var-file="terraform.tfvars" -auto-approve
```

### Paso 8: Ver Resultados

```powershell
terraform output
terraform state list
```

---

## ✅ Verificar que Funciona

```powershell
# Ver recursos creados
cd terraform
terraform state list | Measure-Object -Line

# Ver VPC
aws --endpoint-url=http://localhost:4566 ec2 describe-vpcs
```

---

## 🧹 Limpiar

```powershell
# Destruir infraestructura
cd terraform
terraform destroy -var-file="terraform.tfvars" -auto-approve

# Detener LocalStack
cd ..
docker-compose -f docker-compose.localstack.yml down
```

---

## 🐛 Si Tienes Problemas

Ver: `LOCALSTACK_TROUBLESHOOTING.md`

O ejecuta:
```powershell
.\scripts\verify-localstack.ps1
```

---

## 📚 Documentación

- **Este archivo** - Inicio rápido
- **LOCALSTACK_TROUBLESHOOTING.md** - Solución de problemas
- **LOCALSTACK_READY.md** - Guía completa
- **QUICK_START_LOCALSTACK.md** - Quick start

---

## 🎯 Resumen

```powershell
# Opción A: Script simple
.\scripts\start-localstack-simple.ps1

# Opción B: Manual
docker-compose -f docker-compose.localstack.yml up -d
Start-Sleep -Seconds 30
cd terraform
terraform init
terraform apply -var-file="terraform.tfvars" -auto-approve
```

**Tiempo:** 3-5 minutos

**Resultado:** ~35-40 recursos de AWS corriendo localmente

---

¡Listo! 🎉
