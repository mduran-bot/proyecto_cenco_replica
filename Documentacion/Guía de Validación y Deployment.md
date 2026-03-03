# Guía de Validación y Deployment de Infraestructura AWS

## 📖 Para Nuevos Usuarios

**Si recibes este proyecto por primera vez**, lee primero:

⭐ **[../GUIA_COMPARTIR_PROYECTO.md](../GUIA_COMPARTIR_PROYECTO.md)** - Guía completa paso a paso

Esta guía te ayudará a:
- Instalar los requisitos previos
- Configurar el proyecto
- Probar localmente con LocalStack (sin costos)
- Desplegar a AWS cuando estés listo

---

## 📊 Resultados de Validación

### ✅ Estado: CÓDIGO VALIDADO MEDIANTE DEPLOYMENT DE PRUEBA

Fecha: 3 de Febrero de 2026

**📊 Ver [../TERRAFORM_DEPLOYMENT_TEST_RESULTS.md](../TERRAFORM_DEPLOYMENT_TEST_RESULTS.md) para resultados completos del test** ⭐ NUEVO

### Validación Exitosa

El código Terraform ha sido validado mediante un deployment completo de prueba en AWS:

**Resultados del Test:**
- ✅ **84 recursos desplegados exitosamente**
- ✅ **84 recursos destruidos sin errores**
- ✅ **Duración del test**: ~5 minutos
- ✅ **Costo del test**: < $0.10 USD
- ✅ **Todos los módulos funcionan correctamente**

**Correcciones Aplicadas Durante Testing:**
1. Tag BusinessUnit corregido (eliminado carácter `&` inválido)
2. Security Groups ficticios reemplazados con arrays vacíos
3. VPC Endpoints configurados para una sola subnet por AZ

**Estado:** ✅ Código listo para entrega al cliente

### Módulos Validados (8/8)

| Módulo | Estado | Descripción |
|--------|--------|-------------|
| ✅ VPC | VÁLIDO | Red virtual con CIDR 10.0.0.0/16 |
| ✅ Security Groups | VÁLIDO | 7 grupos de seguridad configurados |
| ✅ VPC Endpoints | VÁLIDO | 7 endpoints (S3, Glue, Secrets Manager, etc.) |
| ✅ Monitoring | VÁLIDO | VPC Flow Logs y CloudWatch |
| ✅ EventBridge | VÁLIDO | 5 reglas programadas para polling |
| ✅ WAF | VÁLIDO | Web Application Firewall con reglas |
| ✅ NACLs | VÁLIDO | Network ACLs para subnets |
| ✅ Tagging | VÁLIDO | Estrategia de etiquetado |

### Configuración Principal

- ✅ **Sintaxis Terraform**: Válida
- ✅ **Estructura de Módulos**: Correcta
- ✅ **Archivos de Variables**: Configurados
- ⚠️ **Credenciales AWS**: Requeridas para deployment

## 🎯 Qué se Validó

### 1. Sintaxis y Configuración
```
✓ Todos los archivos .tf tienen sintaxis correcta
✓ Las variables están correctamente definidas
✓ Los módulos se referencian correctamente
✓ No hay errores de configuración
```

### 2. Arquitectura de Red
```
✓ VPC con CIDR 10.0.0.0/16
✓ 3 Subnets en us-east-1a:
  - Public: 10.0.1.0/24
  - Private 1A: 10.0.10.0/24
  - Private 2A: 10.0.20.0/24
✓ Internet Gateway
✓ NAT Gateway con Elastic IP
✓ Route Tables configuradas
```

### 3. Seguridad
```
✓ 7 Security Groups con reglas específicas
✓ 2 NACLs (Public y Private)
✓ WAF con rate limiting y geo-blocking
✓ VPC Endpoints para servicios AWS
```

### 4. Orquestación
```
✓ EventBridge custom bus
✓ 5 Scheduled Rules:
  - Orders: cada 5 minutos
  - Products: cada 60 minutos
  - Stock: cada 10 minutos
  - Prices: cada 30 minutos
  - Stores: cada 24 horas
✓ Dead Letter Queue configurada
```

### 5. Monitoreo
```
✓ VPC Flow Logs habilitados
✓ CloudWatch Log Groups
✓ Retención de 90 días
✓ Alarmas configuradas
```

## 📋 Recursos que se Crearán

Cuando ejecutes `terraform apply`, se crearán aproximadamente **50-60 recursos**:

### Red (10 recursos)
- 1 VPC
- 3 Subnets
- 1 Internet Gateway
- 1 NAT Gateway
- 1 Elastic IP
- 3 Route Tables

### Seguridad (15 recursos)
- 7 Security Groups
- 2 NACLs
- 1 WAF Web ACL
- 5 WAF Rules

### VPC Endpoints (7 recursos)
- S3 Gateway Endpoint
- Glue Interface Endpoint
- Secrets Manager Interface Endpoint
- CloudWatch Logs Interface Endpoint
- KMS Interface Endpoint
- STS Interface Endpoint
- EventBridge Interface Endpoint

### EventBridge (7 recursos)
- 1 Custom Event Bus
- 5 Scheduled Rules
- 1 SQS Dead Letter Queue

### Monitoreo (5+ recursos)
- VPC Flow Logs
- CloudWatch Log Groups
- CloudWatch Alarms
- IAM Roles para Flow Logs

### Tagging
- Todos los recursos tendrán tags obligatorios

## 🚀 Cómo Desplegar

**📖 GUÍA RÁPIDA:** Ver [terraform/DEPLOYMENT_GUIDE.md](../terraform/DEPLOYMENT_GUIDE.md) para pasos simplificados

### Opción 1: Deployment Completo (Recomendado)

```powershell
# 1. Configurar credenciales AWS
$env:AWS_ACCESS_KEY_ID = "TU_ACCESS_KEY"
$env:AWS_SECRET_ACCESS_KEY = "TU_SECRET_KEY"
$env:AWS_DEFAULT_REGION = "us-east-1"

# 2. Ir al directorio terraform
cd terraform

# 3. Inicializar (si no lo has hecho)
terraform init

# 4. Generar plan y revisarlo
terraform plan -var-file="environments/dev/dev.tfvars" -out=dev.tfplan

# 5. Revisar el plan
terraform show dev.tfplan

# 6. Aplicar (ESTO CREA RECURSOS REALES)
terraform apply dev.tfplan
```

### Opción 2: Deployment Modular

Si prefieres desplegar módulo por módulo para mayor control:

```powershell
# Desplegar solo VPC
terraform apply -target=module.vpc -var-file="environments/dev/dev.tfvars"

# Desplegar Security Groups
terraform apply -target=module.security_groups -var-file="environments/dev/dev.tfvars"

# Y así sucesivamente...
```

### Opción 3: Usar Script de Deployment

```powershell
cd terraform/scripts
.\deploy.sh dev
```

## ⚠️ IMPORTANTE: Antes de Desplegar

### 1. Verificar Credenciales AWS

Asegúrate de tener credenciales AWS válidas con permisos para:
- ✅ VPC y Networking
- ✅ EC2 (para NAT Gateway, Elastic IP)
- ✅ IAM (para roles y policies)
- ✅ CloudWatch
- ✅ EventBridge
- ✅ WAF
- ✅ VPC Endpoints

### 2. Verificar Límites de Servicio (Service Quotas)

Verifica que tu cuenta AWS tenga suficientes límites para:
- VPCs (necesitas 1)
- Elastic IPs (necesitas 1)
- NAT Gateways (necesitas 1)
- VPC Endpoints (necesitas 7)
- Security Groups (necesitas 7)

### 3. Estimar Costos

**Costos mensuales estimados para ambiente dev:**

| Recurso | Costo Mensual (USD) |
|---------|---------------------|
| NAT Gateway | ~$32 |
| VPC Endpoints (7) | ~$50 |
| VPC Flow Logs | ~$10 |
| CloudWatch | ~$5 |
| EventBridge | ~$1 |
| **TOTAL** | **~$98/mes** |

**Nota:** Los costos pueden variar según el uso y la región.

### 4. Configurar Variables

Revisa y ajusta los valores en `environments/dev/dev.tfvars`:

```hcl
# Valores actuales
aws_region = "us-east-1"
environment = "dev"
project_name = "janis-cencosud"

# Verifica estos valores
existing_redshift_sg_id = "sg-XXXXXXXXX"  # ← Actualizar
existing_bi_security_groups = []           # ← Actualizar si aplica
existing_bi_ip_ranges = []                 # ← Actualizar si aplica
```

## 🔄 Proceso de Deployment Paso a Paso

### Paso 1: Preparación (5 minutos)
```powershell
# Configurar credenciales
$env:AWS_ACCESS_KEY_ID = "TU_ACCESS_KEY"
$env:AWS_SECRET_ACCESS_KEY = "TU_SECRET_KEY"
$env:AWS_DEFAULT_REGION = "us-east-1"

# Verificar conexión
aws sts get-caller-identity
```

### Paso 2: Inicialización (2 minutos)
```powershell
cd terraform
terraform init
```

### Paso 3: Plan (5 minutos)
```powershell
terraform plan -var-file="environments/dev/dev.tfvars" -out=dev.tfplan
```

**Revisar el plan cuidadosamente:**
- ¿Se crearán los recursos correctos?
- ¿Los CIDR blocks son correctos?
- ¿Las reglas de seguridad son apropiadas?

### Paso 4: Apply (15-20 minutos)
```powershell
terraform apply dev.tfplan
```

**Durante el apply:**
- Terraform creará los recursos en orden de dependencias
- Verás el progreso en tiempo real
- El NAT Gateway tarda ~5 minutos en crearse
- Los VPC Endpoints tardan ~3-5 minutos cada uno

### Paso 5: Verificación (5 minutos)
```powershell
# Ver outputs
terraform output

# Verificar en AWS Console
# - VPC creada
# - Subnets creadas
# - Security Groups configurados
# - VPC Endpoints activos
```

## 🧪 Testing Post-Deployment

### 1. Verificar Conectividad de Red
```powershell
# Verificar que las subnets tengan las rutas correctas
aws ec2 describe-route-tables --filters "Name=vpc-id,Values=<VPC_ID>"

# Verificar NAT Gateway
aws ec2 describe-nat-gateways --filter "Name=vpc-id,Values=<VPC_ID>"
```

### 2. Verificar Security Groups
```powershell
# Listar security groups
aws ec2 describe-security-groups --filters "Name=vpc-id,Values=<VPC_ID>"
```

### 3. Verificar VPC Endpoints
```powershell
# Listar VPC endpoints
aws ec2 describe-vpc-endpoints --filters "Name=vpc-id,Values=<VPC_ID>"
```

### 4. Verificar EventBridge
```powershell
# Listar reglas de EventBridge
aws events list-rules --event-bus-name janis-cencosud-polling-bus
```

### 5. Verificar VPC Flow Logs
```powershell
# Verificar que Flow Logs estén activos
aws ec2 describe-flow-logs --filter "Name=resource-type,Values=VPC"
```

## 🔧 Troubleshooting

### Error: "Insufficient permissions"
**Solución:** Verifica que tu usuario IAM tenga los permisos necesarios

### Error: "Limit exceeded"
**Solución:** Solicita aumento de límites en AWS Service Quotas

### Error: "Resource already exists"
**Solución:** Verifica que no haya recursos con nombres duplicados

### Error: "Invalid CIDR block"
**Solución:** Verifica que los CIDR blocks no se solapen con VPCs existentes

## 🗑️ Cómo Destruir la Infraestructura

**⚠️ ADVERTENCIA:** Esto eliminará TODOS los recursos creados

```powershell
# Destruir todo
terraform destroy -var-file="environments/dev/dev.tfvars"

# Destruir recursos específicos
terraform destroy -target=module.vpc -var-file="environments/dev/dev.tfvars"
```

## 📚 Documentación Adicional

- `terraform/README.md` - Documentación general
- `terraform/QUICK_VALIDATION.md` - Guía de validación rápida
- `terraform/test/VALIDATION_GUIDE.md` - Guía detallada de validación
- `terraform/modules/*/README.md` - Documentación de cada módulo

## 🎓 Comandos Útiles

```powershell
# Ver estado actual
terraform show

# Ver outputs
terraform output

# Listar recursos
terraform state list

# Ver detalles de un recurso
terraform state show <resource_name>

# Formatear código
terraform fmt -recursive

# Validar configuración
terraform validate

# Refrescar estado
terraform refresh -var-file="environments/dev/dev.tfvars"
```

## ✅ Checklist de Deployment

Antes de ejecutar `terraform apply`:

- [ ] Credenciales AWS configuradas y válidas
- [ ] Variables en dev.tfvars revisadas y actualizadas
- [ ] Plan de Terraform revisado y aprobado
- [ ] Límites de servicio verificados
- [ ] Costos estimados y aprobados
- [ ] Backup del estado actual (si existe)
- [ ] Ventana de mantenimiento coordinada
- [ ] Equipo notificado del deployment
- [ ] Plan de rollback documentado

## 🎯 Próximos Pasos

1. **Configurar credenciales AWS**
2. **Revisar variables en dev.tfvars**
3. **Ejecutar terraform plan**
4. **Revisar el plan cuidadosamente**
5. **Ejecutar terraform apply**
6. **Verificar recursos creados**
7. **Documentar IDs de recursos importantes**
8. **Configurar monitoreo y alertas**

## 📞 Soporte

Si encuentras problemas:
1. Revisa los logs de Terraform
2. Consulta la documentación de AWS
3. Verifica los mensajes de error específicos
4. Revisa los archivos de estado de Terraform

---

**Última Actualización:** 26 de Enero de 2026  
**Estado:** Validación Exitosa - Listo para Deployment
