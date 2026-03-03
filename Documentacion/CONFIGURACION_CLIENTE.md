# Configuración Requerida del Cliente

**Fecha**: 3 de Febrero, 2026  
**Proyecto**: Janis-Cencosud AWS Infrastructure  
**Propósito**: Documentar qué debe configurar el cliente antes del deployment

---

## Resumen Ejecutivo

Este documento detalla los elementos que **el cliente (Cencosud) debe proporcionar o configurar** antes de desplegar la infraestructura en su cuenta AWS. Estos elementos no están incluidos en el código Terraform porque son específicos del ambiente del cliente.

---

## 1. Credenciales AWS

### ¿Qué necesita el cliente?

El cliente debe proporcionar credenciales AWS con permisos suficientes para crear recursos:

```bash
# Opción 1: Variables de entorno
export AWS_ACCESS_KEY_ID="AKIA..."
export AWS_SECRET_ACCESS_KEY="..."
export AWS_SESSION_TOKEN="..."  # Si usa STS/MFA

# Opción 2: AWS CLI Profile
aws configure --profile cencosud-prod
```

### Permisos Requeridos

El usuario/rol debe tener permisos para crear:
- VPC, Subnets, Route Tables, Internet Gateway, NAT Gateway
- Security Groups, NACLs
- VPC Endpoints
- VPC Flow Logs (CloudWatch Logs)
- EventBridge Rules
- CloudWatch Alarms
- WAF Web ACL
- IAM Roles (para VPC Flow Logs)

**Recomendación**: Usar un rol con política `PowerUserAccess` o crear una política custom específica.

---

## 2. Configuración de Red (Networking)

### 2.1 Rangos CIDR

El cliente debe definir los rangos de red que usará:

```hcl
# En terraform.tfvars
vpc_cidr                = "10.X.0.0/16"      # DEFINIR: Rango VPC
public_subnet_a_cidr    = "10.X.1.0/24"     # DEFINIR: Subnet pública
private_subnet_1a_cidr  = "10.X.10.0/24"    # DEFINIR: Subnet privada 1
private_subnet_2a_cidr  = "10.X.20.0/24"    # DEFINIR: Subnet privada 2
```

**Importante**: 
- Los rangos NO deben solaparse con redes existentes
- Coordinar con el equipo de redes de Cencosud
- Verificar que no conflicten con VPCs existentes si hay VPC Peering

### 2.2 IPs Permitidas de Janis

El cliente debe proporcionar los rangos de IP desde donde Janis enviará webhooks:

```hcl
# En terraform.tfvars
allowed_janis_ip_ranges = [
  "X.X.X.X/32",    # IP 1 de Janis
  "Y.Y.Y.Y/32",    # IP 2 de Janis
  "Z.Z.Z.Z/24"     # Rango de Janis
]
```

**Importante**: 
- NUNCA usar `0.0.0.0/0` en producción
- Solicitar a Janis sus IPs públicas estáticas
- Documentar el propósito de cada IP/rango

---

## 3. Integración con Infraestructura Existente

### 3.1 Redshift (Data Warehouse)

Si el cliente ya tiene un cluster Redshift, debe proporcionar:

```hcl
# En terraform.tfvars
existing_redshift_cluster_id = "cencosud-redshift-prod"
existing_redshift_sg_id      = "sg-XXXXXXXXX"
```

**Cómo obtener estos valores**:
```bash
# Cluster ID
aws redshift describe-clusters --query 'Clusters[*].[ClusterIdentifier]'

# Security Group ID
aws redshift describe-clusters \
  --cluster-identifier cencosud-redshift-prod \
  --query 'Clusters[0].VpcSecurityGroups[*].VpcSecurityGroupId'
```

### 3.2 Herramientas BI Existentes

Si hay herramientas BI (Power BI, Tableau, etc.) que necesitan acceso:

```hcl
# En terraform.tfvars
existing_bi_security_groups = ["sg-AAAAAAA", "sg-BBBBBBB"]
existing_bi_ip_ranges       = ["10.20.0.0/16"]
```

### 3.3 Pipeline MySQL Existente

Si hay un pipeline existente desde MySQL:

```hcl
# En terraform.tfvars
existing_mysql_pipeline_sg_id = "sg-CCCCCCC"
```

---

## 4. Política de Etiquetado (Tagging)

### 4.1 Tags Obligatorios

El cliente debe definir los valores para los tags corporativos:

```hcl
# En terraform.tfvars
# Tags corporativos obligatorios
application_name = "janis-cencosud-integration"
environment      = "prod"                    # DEFINIR: prod/qa/dev/uat/sandbox
owner            = "data-engineering-team"   # DEFINIR: Equipo responsable
cost_center      = "CC-12345"                # DEFINIR: Centro de costos real
business_unit    = "Data-Analytics"          # DEFINIR: Unidad de negocio
country          = "CL"                      # DEFINIR: País (código ISO)
criticality      = "high"                    # DEFINIR: high/medium/low

# Tags adicionales opcionales
additional_tags = {
  DataClassification = "Confidential"
  BackupPolicy       = "daily"
  ComplianceLevel    = "SOC2"
}
```

### 4.2 Valores Permitidos

Según la política de etiquetado de Cencosud:

**Environment**:
- `prod` - Producción
- `qa` - Quality Assurance
- `dev` - Desarrollo
- `uat` - User Acceptance Testing
- `sandbox` - Pruebas

**Criticality**:
- `high` - Servicios críticos de negocio
- `medium` - Servicios importantes pero no críticos
- `low` - Servicios de desarrollo/testing

**Referencia**: Ver `Politica_Etiquetado_AWS.md` para detalles completos.

---

## 5. Monitoreo y Alertas

### 5.1 SNS Topic para Alarmas

El cliente debe crear un SNS Topic para recibir alarmas de CloudWatch:

```bash
# Crear SNS Topic
aws sns create-topic --name cencosud-infrastructure-alarms

# Suscribir emails
aws sns subscribe \
  --topic-arn arn:aws:sns:us-east-1:ACCOUNT_ID:cencosud-infrastructure-alarms \
  --protocol email \
  --notification-endpoint team@cencosud.com
```

Luego configurar en Terraform:

```hcl
# En terraform.tfvars
alarm_sns_topic_arn = "arn:aws:sns:us-east-1:ACCOUNT_ID:cencosud-infrastructure-alarms"
```

### 5.2 Retención de Logs

El cliente debe definir cuántos días retener logs:

```hcl
# En terraform.tfvars
vpc_flow_logs_retention_days = 30    # DEFINIR: 7, 30, 90, 365
dns_logs_retention_days      = 30    # DEFINIR: 7, 30, 90, 365
```

**Recomendaciones**:
- Producción: 90 días mínimo
- Desarrollo: 7-30 días
- Considerar costos de almacenamiento en CloudWatch Logs

---

## 6. Orquestación (MWAA/Airflow)

### 6.1 ARN del Ambiente MWAA

Si el cliente ya tiene Amazon MWAA (Managed Airflow) desplegado:

```hcl
# En terraform.tfvars
mwaa_environment_arn = "arn:aws:airflow:us-east-1:ACCOUNT_ID:environment/cencosud-mwaa"
```

**Cómo obtenerlo**:
```bash
aws mwaa get-environment --name cencosud-mwaa \
  --query 'Environment.Arn'
```

**Si no existe**: Dejar vacío `""` y EventBridge no configurará triggers a MWAA.

### 6.2 Frecuencias de Polling

El cliente debe definir cada cuánto tiempo hacer polling a la API de Janis:

```hcl
# En terraform.tfvars (valores en minutos)
order_polling_rate_minutes   = 15     # DEFINIR: Cada cuánto consultar órdenes
product_polling_rate_minutes = 60     # DEFINIR: Cada cuánto consultar productos
stock_polling_rate_minutes   = 30     # DEFINIR: Cada cuánto consultar stock
price_polling_rate_minutes   = 60     # DEFINIR: Cada cuánto consultar precios
store_polling_rate_minutes   = 1440   # DEFINIR: Cada cuánto consultar tiendas (1440 = 1 día)
```

**Recomendaciones**:
- Órdenes: 5-15 minutos (datos más críticos)
- Productos: 30-60 minutos
- Stock: 15-30 minutos
- Precios: 60 minutos
- Tiendas: 1440 minutos (1 vez al día)

---

## 7. VPC Endpoints (Opcional)

### 7.1 Habilitar Endpoints

El cliente debe decidir qué VPC Endpoints habilitar para reducir costos de transferencia de datos:

```hcl
# En terraform.tfvars
enable_s3_endpoint              = true   # DEFINIR: Recomendado para S3
enable_glue_endpoint            = true   # DEFINIR: Si usa AWS Glue
enable_secrets_manager_endpoint = true   # DEFINIR: Si usa Secrets Manager
enable_logs_endpoint            = false  # DEFINIR: Para CloudWatch Logs
enable_kms_endpoint             = false  # DEFINIR: Para KMS
enable_sts_endpoint             = false  # DEFINIR: Para STS
enable_events_endpoint          = false  # DEFINIR: Para EventBridge
```

**Costos**:
- Cada VPC Endpoint Interface cuesta ~$7.50/mes + $0.01/GB transferido
- VPC Endpoint Gateway (S3, DynamoDB) es GRATIS
- Evaluar costo vs beneficio según volumen de datos

**Recomendaciones**:
- **S3**: Siempre habilitado (gratis y reduce costos)
- **Glue**: Habilitado si se usa AWS Glue intensivamente
- **Secrets Manager**: Habilitado si se consulta frecuentemente
- **Otros**: Evaluar según uso

---

## 8. Configuración Multi-AZ (Opcional)

### 8.1 Alta Disponibilidad

El cliente debe decidir si desplegar en múltiples Availability Zones:

```hcl
# En terraform.tfvars
enable_multi_az = true   # DEFINIR: true para producción, false para dev/testing
```

**Si `enable_multi_az = true`**, también definir:

```hcl
# Subnets adicionales en AZ-b
public_subnet_b_cidr    = "10.X.2.0/24"     # DEFINIR
private_subnet_1b_cidr  = "10.X.11.0/24"    # DEFINIR
private_subnet_2b_cidr  = "10.X.21.0/24"    # DEFINIR
```

**Costos**:
- Multi-AZ duplica algunos recursos (NAT Gateway, subnets)
- NAT Gateway adicional: ~$32/mes + transferencia de datos
- Mayor resiliencia ante fallos de AZ

**Recomendaciones**:
- **Producción**: `enable_multi_az = true` (alta disponibilidad)
- **Desarrollo/Testing**: `enable_multi_az = false` (ahorro de costos)

---

## 9. Cuenta AWS

### 9.1 Account ID

El cliente debe proporcionar el Account ID de AWS:

```hcl
# En terraform.tfvars
aws_account_id = "123456789012"   # DEFINIR: Account ID de AWS
```

**Cómo obtenerlo**:
```bash
aws sts get-caller-identity --query 'Account' --output text
```

### 9.2 Región

El cliente debe definir la región AWS:

```hcl
# En terraform.tfvars
aws_region = "us-east-1"   # DEFINIR: Región AWS
```

**Regiones comunes**:
- `us-east-1` - Virginia del Norte (más servicios, más barato)
- `us-east-2` - Ohio
- `sa-east-1` - São Paulo (Latinoamérica)

---

## 10. Checklist de Configuración

Antes de ejecutar `terraform apply`, verificar:

### Credenciales y Cuenta
- [ ] Credenciales AWS configuradas
- [ ] Account ID definido
- [ ] Región AWS definida
- [ ] Permisos IAM verificados

### Networking
- [ ] Rangos CIDR definidos (VPC y subnets)
- [ ] Rangos no solapan con redes existentes
- [ ] IPs de Janis obtenidas y configuradas
- [ ] Multi-AZ decidido (true/false)

### Integración
- [ ] Redshift cluster ID obtenido (si existe)
- [ ] Security Groups existentes identificados
- [ ] MWAA ARN obtenido (si existe)

### Tagging
- [ ] Todos los tags obligatorios definidos
- [ ] Cost Center asignado
- [ ] Owner/equipo responsable definido
- [ ] Criticality definida según ambiente

### Monitoreo
- [ ] SNS Topic creado para alarmas
- [ ] Emails suscritos al SNS Topic
- [ ] Retención de logs definida
- [ ] Frecuencias de polling definidas

### Costos
- [ ] VPC Endpoints evaluados (cuáles habilitar)
- [ ] Multi-AZ evaluado (costo vs disponibilidad)
- [ ] Retención de logs evaluada (costo vs compliance)

---

## 11. Archivo de Configuración Final

Una vez definidos todos los valores, el cliente debe editar el archivo plantilla:

```
terraform/terraform.tfvars
```

**IMPORTANTE**: Este archivo ya existe como plantilla con valores de ejemplo. El cliente debe:
1. Revisar cada sección del archivo
2. Reemplazar los valores de ejemplo con valores reales
3. Verificar que no haya conflictos de red con infraestructura existente
4. Confirmar que todos los tags corporativos estén correctos

**Estructura actual del archivo**:

```hcl
# ============================================================================
# AWS Configuration
# ============================================================================
aws_region     = "us-east-1"
aws_account_id = "123456789012"

# ============================================================================
# Network Configuration
# ============================================================================
vpc_cidr                = "10.50.0.0/16"
public_subnet_a_cidr    = "10.50.1.0/24"
private_subnet_1a_cidr  = "10.50.10.0/24"
private_subnet_2a_cidr  = "10.50.20.0/24"
enable_multi_az         = true

# ============================================================================
# Security Configuration
# ============================================================================
allowed_janis_ip_ranges = [
  "203.0.113.10/32",
  "203.0.113.20/32"
]

# ============================================================================
# Tagging Strategy
# ============================================================================
project_name     = "janis-cencosud-integration"
application_name = "janis-cencosud-integration"
environment      = "prod"
owner            = "data-engineering-team"
cost_center      = "CC-12345"
business_unit    = "Data-Analytics"
country          = "CL"
criticality      = "high"

additional_tags = {
  DataClassification = "Confidential"
  BackupPolicy       = "daily"
  ComplianceLevel    = "SOC2"
}

# ============================================================================
# Monitoring Configuration
# ============================================================================
vpc_flow_logs_retention_days = 90
alarm_sns_topic_arn          = "arn:aws:sns:us-east-1:123456789012:infra-alarms"

# ============================================================================
# EventBridge Configuration
# ============================================================================
order_polling_rate_minutes   = 15
product_polling_rate_minutes = 60
stock_polling_rate_minutes   = 30
price_polling_rate_minutes   = 60
store_polling_rate_minutes   = 1440
mwaa_environment_arn         = "arn:aws:airflow:us-east-1:123456789012:environment/cencosud-mwaa"

# ============================================================================
# VPC Endpoints Configuration
# ============================================================================
enable_s3_endpoint              = true
enable_glue_endpoint            = true
enable_secrets_manager_endpoint = true
enable_logs_endpoint            = false
enable_kms_endpoint             = false
enable_sts_endpoint             = false
enable_events_endpoint          = false

# ============================================================================
# Existing Infrastructure Integration
# ============================================================================
existing_redshift_cluster_id  = "cencosud-redshift-prod"
existing_redshift_sg_id       = "sg-0123456789abcdef0"
existing_bi_security_groups   = ["sg-0abcdef123456789"]
existing_bi_ip_ranges         = ["10.20.0.0/16"]
existing_mysql_pipeline_sg_id = ""
```

---

## 12. Soporte y Contacto

Para dudas sobre la configuración:

1. **Documentación Técnica**: Ver `terraform/README.md`
2. **Guía de Deployment**: Ver `terraform/DEPLOYMENT_GUIDE.md`
3. **Política de Tagging**: Ver `Politica_Etiquetado_AWS.md`
4. **Multi-AZ**: Ver `terraform/MULTI_AZ_EXPANSION.md`

---

**Preparado por**: Vicente Morales, 3HTP  
**Fecha**: 3 de Febrero, 2026  
**Versión**: 1.0  
**Estado**: ✅ Listo para revisión del cliente
