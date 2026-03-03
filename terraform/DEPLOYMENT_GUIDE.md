# Guía de Deployment - Infraestructura AWS

**📖 Para deployment en ambiente de testing, ver [GUIA_DEPLOYMENT_TESTING.md](./GUIA_DEPLOYMENT_TESTING.md)**

## ✅ VALIDACIÓN EXITOSA

**Fecha:** 26 de Enero de 2026  
**Estado:** Todos los módulos validados correctamente

### Módulos Validados (7/8)

| Módulo | Estado |
|--------|--------|
| VPC | ✅ VÁLIDO |
| Security Groups | ✅ VÁLIDO |
| VPC Endpoints | ✅ VÁLIDO |
| Monitoring | ✅ VÁLIDO |
| EventBridge | ✅ VÁLIDO |
| WAF | ✅ VÁLIDO |
| NACLs | ⏸️ DESHABILITADO |
| Tagging | ✅ VÁLIDO |

**Nota**: El módulo NACLs está temporalmente deshabilitado. Ver [NACL_MODULE_DISABLED.md](./NACL_MODULE_DISABLED.md) para detalles.

## 🚀 Cómo Desplegar

### Paso 1: Configurar Credenciales AWS

```powershell
$env:AWS_ACCESS_KEY_ID = "TU_ACCESS_KEY"
$env:AWS_SECRET_ACCESS_KEY = "TU_SECRET_KEY"
$env:AWS_DEFAULT_REGION = "us-east-1"

# Verificar conexión
aws sts get-caller-identity
```

### Paso 2: Generar Plan

```powershell
cd terraform
terraform plan -var-file="environments/dev/dev.tfvars" -out=dev.tfplan
```

### Paso 3: Revisar Plan

```powershell
terraform show dev.tfplan
```

### Paso 4: Aplicar (CREA RECURSOS REALES)

```powershell
terraform apply dev.tfplan
```

## 📊 Recursos que se Crearán

**📖 Ver [AWS_PLAN_SUMMARY.md](./AWS_PLAN_SUMMARY.md) para desglose completo** ⭐ NUEVO

### Resumen por Módulo

- **VPC Module**: 15 recursos (VPC, 3 subnets, IGW, NAT Gateway, Route Tables)
- **Security Groups Module**: 28 recursos (7 security groups + 21 rules)
- **EventBridge Module**: 10 recursos (Event Bus, 5 rules, DLQ, IAM roles, alarms)
- **Monitoring Module**: 16 recursos (VPC Flow Logs, CloudWatch alarms, metric filters)
- **VPC Endpoints Module**: 1 recurso (S3 Gateway Endpoint)

**Total:** 70 recursos a crear

Ver [AWS_PLAN_SUMMARY.md](./AWS_PLAN_SUMMARY.md) para desglose detallado de cada recurso.

## 💰 Costos Estimados

**📖 Ver [AWS_PLAN_SUMMARY.md](./AWS_PLAN_SUMMARY.md) para desglose completo de costos** ⭐ NUEVO

### Costos Mensuales (Single-AZ)

| Recurso | Costo Mensual |
|---------|---------------|
| NAT Gateway | ~$32 USD |
| NAT Gateway Data Transfer | ~$0.045/GB |
| VPC Flow Logs | ~$0.50/GB |
| CloudWatch Logs | ~$0.50/GB |
| CloudWatch Alarms | $0 (primeros 10 gratis) |
| EventBridge Rules | $0 (primeros 14M gratis) |
| SQS Queue | $0 (primeros 1M gratis) |
| S3 Gateway Endpoint | $0 |
| **TOTAL BASE** | **~$35-50 USD/mes** |

**Nota:** Costos reales dependerán del tráfico de datos. Interface VPC Endpoints están deshabilitados para reducir costos (~$7.20/mes cada uno).

## ⚠️ IMPORTANTE

- `terraform plan` - Seguro, no crea nada
- `terraform apply` - Crea recursos reales y genera costos
- Tiempo estimado de deployment: 15-20 minutos

## 🧪 Verificación Post-Deployment

```powershell
# Ver outputs
terraform output

# Verificar VPC
aws ec2 describe-vpcs --filters "Name=tag:Project,Values=janis-cencosud"

# Verificar Security Groups
aws ec2 describe-security-groups --filters "Name=vpc-id,Values=<VPC_ID>"

# Verificar VPC Endpoints
aws ec2 describe-vpc-endpoints --filters "Name=vpc-id,Values=<VPC_ID>"
```

## 📊 Testing con LocalStack

Si quieres probar el deployment localmente antes de AWS real, puedes usar LocalStack. Sin embargo, ten en cuenta:

**⚠️ Limitaciones de LocalStack**:
- Operaciones muy lentas (5+ minutos vs segundos en AWS real)
- Algunos recursos se atascan durante deployment
- No representa el comportamiento real de AWS

**📖 Resultados de Testing**: Ver [DEPLOYMENT_STATUS_FINAL.md](./DEPLOYMENT_STATUS_FINAL.md) para análisis completo de deployment en LocalStack, incluyendo:
- Qué módulos se despliegan exitosamente (VPC, Security Groups, EventBridge)
- Qué recursos se atascan (Monitoring avanzado, EventBridge rules)
- Recomendaciones para testing real vs LocalStack

**Recomendación**: Para testing de infraestructura, usa AWS real con configuración de testing (~$40/mes). Ver [GUIA_DEPLOYMENT_TESTING.md](./GUIA_DEPLOYMENT_TESTING.md).

## 🗑️ Destruir Infraestructura

```powershell
terraform destroy -var-file="environments/dev/dev.tfvars"
```

---

**Siguiente paso:** Configurar credenciales AWS y ejecutar `terraform plan`
