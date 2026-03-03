# Guía de Uso - Infraestructura AWS Terraform

## 📋 Contenido

1. [Requisitos Previos](#requisitos-previos)
2. [Configuración Inicial](#configuración-inicial)
3. [Personalización](#personalización)
4. [Deployment](#deployment)
5. [Verificación](#verificación)
6. [Troubleshooting](#troubleshooting)
7. [Migración a Multi-AZ](#migración-a-multi-az)

---

## Requisitos Previos

### Software Necesario

- **Terraform** >= 1.0 ([Descargar](https://www.terraform.io/downloads))
- **AWS CLI** ([Descargar](https://aws.amazon.com/cli/))
- **Git** (para versionado)

### Credenciales AWS

Necesitarás credenciales AWS con permisos para crear:
- VPC, Subnets, Internet Gateway, NAT Gateway
- Security Groups, NACLs
- VPC Endpoints
- WAF Web ACL
- EventBridge Event Bus y Rules
- CloudWatch Logs y Alarms
- IAM Roles y Policies

---

## Configuración Inicial

### 1. Copiar Archivo de Configuración

```bash
cd terraform
cp terraform.tfvars.example terraform.tfvars
```

### 2. Editar `terraform.tfvars`

Abre `terraform.tfvars` y completa con tus valores:

```hcl
# AWS Configuration
aws_region     = "us-east-1"
aws_account_id = "TU_ACCOUNT_ID_AQUI"

# Network Configuration
vpc_cidr = "10.0.0.0/16"  # Verificar que no conflictúe

# Existing Infrastructure
existing_redshift_cluster_id = "tu-redshift-cluster"
existing_redshift_sg_id      = "sg-xxxxx"
existing_bi_security_groups  = ["sg-xxxxx", "sg-yyyyy"]
existing_bi_ip_ranges        = ["192.168.1.0/24"]

# Tagging
project_name = "janis-cencosud-integration"
environment  = "production"
owner        = "tu-equipo"
cost_center  = "TU_COST_CENTER"

# Security
allowed_janis_ip_ranges = ["IP_REAL_DE_JANIS/32"]

# Monitoring
alarm_sns_topic_arn = "arn:aws:sns:us-east-1:xxxxx:tu-topic"
```

### 3. Configurar Credenciales AWS

**Opción A: Variables de Entorno**
```bash
export AWS_ACCESS_KEY_ID="tu-access-key"
export AWS_SECRET_ACCESS_KEY="tu-secret-key"
export AWS_SESSION_TOKEN="tu-session-token"  # opcional
```

**Opción B: AWS Profile**
```bash
export AWS_PROFILE="tu-profile"
```

---

## Personalización

### Ajustar Políticas Corporativas

#### Security Groups

Edita `modules/security-groups/main.tf` para:
- Agregar reglas específicas de tu organización
- Restringir IPs según políticas internas
- Modificar puertos permitidos

#### Tags

Edita `variables.tf` para agregar tags corporativos:
```hcl
variable "additional_tags" {
  default = {
    DataClassification = "Confidential"
    ComplianceLevel    = "SOC2"
    BusinessUnit       = "Data & Analytics"
    # Agregar más según necesidad
  }
}
```

#### WAF Rules

Edita `modules/waf/main.tf` para:
- Ajustar rate limits
- Modificar geo-blocking
- Agregar/remover managed rules

---

## Deployment

### Estado Actual de Implementación

**Completado (Fase 1 - Fundamentos de Red)** ✅:
- ✅ Task 1: Estructura de proyecto Terraform
- ✅ Task 2: Implementar VPC module (3/3 subtareas)
- ✅ Task 3: Arquitectura de subnets (6/6 subtareas)
- ✅ Task 4: Checkpoint VPC y subnets

**Completado (Fase 2 - Conectividad)** ✅:
- ✅ Task 5: Internet Gateway, NAT Gateway, Route Tables (4/4 subtareas)
- ✅ Task 6: VPC Endpoints (3/3 subtareas)
  - ✅ Task 6.1: S3 Gateway Endpoint
  - ✅ Task 6.2: 6 Interface Endpoints
  - ✅ Task 6.3: Property test para VPC endpoint service coverage
- ✅ Task 7: Checkpoint conectividad y endpoints

**Completado (Fase 3 - Seguridad parcial)** ✅:
- ✅ Task 8: Security Groups (8/8 subtareas completadas)
  - ✅ Task 8.1-8.6: 7 Security Groups implementados
  - ✅ Task 8.7: Property tests para security group configuration (completado)
  - ✅ Task 8.8: Unit tests para security groups (COMPLETADO)

**En Progreso (Fase 3 - Seguridad continuación)** 🔄:
- 🔄 Task 9: Implementar Network ACLs (3/3 subtareas en progreso)
  - ✅ Task 9.1: Public Subnet NACL implementado
  - ✅ Task 9.2: Private Subnet NACL implementado
  - 🔄 Task 9.3: Property test para NACL stateless bidirectionality (EN PROGRESO)

**Siguiente Fase (Fase 3 - Seguridad finalización)** ⏳:
- ⏳ Task 10: Checkpoint seguridad

**Plan Completo**: Ver `.kiro/specs/01-aws-infrastructure/tasks.md` para las 20 tareas organizadas en 6 fases.

### Opción 1: Script Automatizado (Recomendado)

```bash
chmod +x deploy.sh
./deploy.sh
```

El script:
1. ✅ Verifica que `terraform.tfvars` existe
2. ✅ Hace backup del state actual
3. ✅ Inicializa Terraform
4. ✅ Valida la configuración
5. ✅ Crea el plan
6. ✅ Solicita confirmación
7. ✅ Aplica los cambios

### Opción 2: Manual

```bash
# 1. Inicializar
terraform init

# 2. Validar
terraform validate
terraform fmt -check

# 3. Plan
terraform plan -var-file="terraform.tfvars" -out="plan.tfplan"

# 4. Revisar el plan y aplicar
terraform apply "plan.tfplan"
```

### Deployment por Ambientes

Para desplegar en diferentes ambientes, crear archivos `.tfvars` específicos:

```bash
# Desarrollo
terraform apply -var-file="dev.tfvars"

# Staging
terraform apply -var-file="staging.tfvars"

# Producción
terraform apply -var-file="prod.tfvars"
```

---

## Verificación

### Ver Recursos Creados

```bash
# Ver todos los outputs
terraform output

# Ver output específico
terraform output vpc_id
terraform output nat_gateway_public_ip
```

### Verificar en AWS Console

1. **VPC**: Buscar VPC con tag `Project=janis-cencosud-integration`
2. **Subnets**: Verificar 3 subnets en us-east-1a
3. **NAT Gateway**: Verificar en subnet pública
4. **Security Groups**: Verificar 7 security groups creados
5. **VPC Endpoints**: Verificar S3 Gateway + 6 Interface Endpoints
6. **WAF**: Verificar Web ACL con 5 reglas
7. **EventBridge**: Verificar custom event bus y 5 rules

### Verificar Conectividad

```bash
# VPC Flow Logs
aws logs tail /aws/vpc/flow-logs/janis-cencosud-production --follow

# EventBridge Rules
aws events list-rules --event-bus-name janis-cencosud-production-polling-bus

# WAF Metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/WAFV2 \
  --metric-name BlockedRequests \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Sum
```

---

## Troubleshooting

### Error: "terraform.tfvars not found"

**Solución**: Copiar el archivo de ejemplo
```bash
cp terraform.tfvars.example terraform.tfvars
```

### Error: "Invalid CIDR block"

**Causa**: El CIDR especificado no es válido o conflictúa con redes existentes

**Solución**: Verificar que el CIDR:
- Sea un /16 válido (ej: 10.0.0.0/16)
- No conflictúe con redes corporativas
- Esté en rango privado (10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16)

### Error: "Security Group not found"

**Causa**: Los IDs de security groups existentes son incorrectos

**Solución**: Verificar IDs reales en AWS Console:
```bash
aws ec2 describe-security-groups --filters "Name=vpc-id,Values=vpc-xxxxx"
```

### Error: "Insufficient permissions"

**Causa**: Las credenciales AWS no tienen permisos suficientes

**Solución**: Verificar que el usuario/role tiene permisos para:
- ec2:* (VPC, Subnets, Security Groups, etc.)
- wafv2:* (WAF)
- events:* (EventBridge)
- logs:* (CloudWatch Logs)
- iam:* (IAM Roles)

### Estado Corrupto

Si el state file se corrompe:

```bash
# 1. Restaurar desde backup
cp terraform.tfstate.backup.YYYYMMDD_HHMMSS terraform.tfstate

# 2. Verificar
terraform plan

# 3. Si es necesario, refresh
terraform refresh
```

---

## Migración a Multi-AZ

### Cuándo Migrar

Considera migrar a Multi-AZ cuando:
- ✅ El sistema está en producción y estable
- ✅ Se requiere alta disponibilidad (99.99%)
- ✅ El presupuesto permite $36-50/mes adicionales
- ✅ Se ha probado el sistema en Single-AZ

### Pasos para Migrar

#### 1. Actualizar Configuración

Editar `terraform.tfvars`:
```hcl
enable_multi_az = true
```

#### 2. Revisar Plan

```bash
terraform plan -var-file="terraform.tfvars"
```

Verificar que se crearán:
- 3 subnets adicionales en us-east-1b
- 1 NAT Gateway adicional
- 1 Elastic IP adicional
- 1 Route Table adicional

#### 3. Aplicar Cambios

```bash
terraform apply -var-file="terraform.tfvars"
```

#### 4. Verificar

```bash
# Ver availability zones
terraform output availability_zones

# Verificar subnets
aws ec2 describe-subnets --filters "Name=vpc-id,Values=$(terraform output -raw vpc_id)"
```

#### 5. Actualizar Servicios

Después de crear la infraestructura Multi-AZ:
- Configurar Lambda functions en ambas AZs
- Habilitar Multi-AZ en MWAA
- Actualizar Auto Scaling Groups

### Rollback a Single-AZ

Si es necesario volver a Single-AZ:

```hcl
enable_multi_az = false
```

```bash
terraform apply -var-file="terraform.tfvars"
```

⚠️ **Advertencia**: Esto destruirá recursos en us-east-1b

---

### Destrucción de Infraestructura

### ⚠️ PRECAUCIÓN

La destrucción es **PERMANENTE** y **NO REVERSIBLE**.

### Usando Script

```bash
chmod +x destroy.sh
./destroy.sh
```

### Manual

```bash
# 1. Ver qué se destruirá
terraform plan -destroy -var-file="terraform.tfvars"

# 2. Destruir (requiere confirmación)
terraform destroy -var-file="terraform.tfvars"
```

### Destrucción Selectiva

Para destruir solo ciertos recursos:

```bash
# Destruir solo WAF
terraform destroy -target=module.waf -var-file="terraform.tfvars"

# Destruir solo EventBridge
terraform destroy -target=module.eventbridge -var-file="terraform.tfvars"
```

---

## Mantenimiento

### Actualizar Infraestructura

```bash
# 1. Modificar archivos .tf o terraform.tfvars
# 2. Ver cambios
terraform plan -var-file="terraform.tfvars"

# 3. Aplicar
terraform apply -var-file="terraform.tfvars"
```

### Backup Regular

```bash
# Crear backup manual
cp terraform.tfstate terraform.tfstate.backup.$(date +%Y%m%d_%H%M%S)

# Automatizar con cron (Linux/Mac)
0 2 * * * cd /path/to/terraform && cp terraform.tfstate terraform.tfstate.backup.$(date +\%Y\%m\%d)
```

### Drift Detection

Detectar cambios manuales en AWS Console:

```bash
terraform plan -var-file="terraform.tfvars"
```

Si hay drift, Terraform mostrará los cambios necesarios para volver al estado deseado.

---

## Costos Estimados

### Single-AZ
- **Mensual**: $111.70-152.70
- **Anual**: ~$1,340-1,832

### Multi-AZ
- **Mensual**: $148.20-202.20
- **Anual**: ~$1,778-2,426
- **Incremento**: +$36.50-49.50/mes

### Monitorear Costos

```bash
# Ver costos en AWS Cost Explorer
aws ce get-cost-and-usage \
  --time-period Start=2026-01-01,End=2026-01-31 \
  --granularity MONTHLY \
  --metrics BlendedCost \
  --filter file://cost-filter.json
```

---

## Soporte

### Documentación Adicional

- **Especificación Completa**: `Documentación Cenco/Especificación Detallada de Infraestructura AWS.md`
- **Design Document**: `.kiro/specs/aws-infrastructure/design.md`
- **Tasks**: `.kiro/specs/aws-infrastructure/tasks.md`

### Contacto

Para preguntas o issues:
- Equipo de DevOps/Infrastructure
- Email: devops@cencosud.com

---

## Checklist de Deployment

Antes de aplicar en producción:

- [ ] `terraform.tfvars` configurado con valores reales
- [ ] Credenciales AWS configuradas
- [ ] CIDR verificado (no conflictúa con redes corporativas)
- [ ] IDs de recursos existentes verificados (Redshift, BI systems)
- [ ] Tags corporativos aplicados
- [ ] IPs de Janis configuradas correctamente
- [ ] SNS topic para alarmas creado
- [ ] Backup del state actual (si existe)
- [ ] `terraform validate` ejecutado sin errores
- [ ] `terraform plan` revisado y aprobado
- [ ] Equipo de BI notificado sobre cambios
- [ ] Ventana de mantenimiento coordinada
- [ ] Plan de rollback documentado

---

**Última actualización**: 21 de Enero, 2026
