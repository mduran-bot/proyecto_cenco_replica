# **Guía Proyecto Terraform Cencosud - Implementación y Deployment**

Fecha: 5 de febrero de 2026  
Estado: Infraestructura Validada - Lista para Deployment  
Cuenta AWS: 827739413930  
Región: us-east-1

---

## **Resumen Ejecutivo**

Este documento proporciona la guía completa para el deployment de la infraestructura AWS del proyecto Janis-Cencosud utilizando Terraform. Incluye lo que se validó en las pruebas, los archivos entregados, las configuraciones que debe ajustar Cencosud, y los comandos exactos para ejecutar el deployment.

---

## **PARTE 1: LO QUE SE VALIDÓ EN LAS PRUEBAS**

### **Pruebas Realizadas**

**Terraform Plan**
- Validación de sintaxis: ✅ Exitosa
- Validación de configuración: ✅ Exitosa
- Recursos a crear: 141 recursos
- Tiempo de ejecución: ~30 segundos

**Terraform Apply**
- Deployment completo: ✅ Exitoso
- Recursos creados: 141 recursos
- Tiempo de ejecución: ~3 minutos
- Cuenta AWS: 827739413930
- Región: us-east-1

**Recursos Creados y Validados**

**VPC y Networking:**
- VPC: vpc-0a2a2c69ed1e513dc (10.0.0.0/16)
- Subnets: 3 (1 pública, 2 privadas)
- Internet Gateway: igw-0681804fdcb3892cd
- NAT Gateway: nat-0cde66ca4186fcdfc
- IP Pública NAT: 34.203.17.189
- Route Tables: 2
- Network ACLs: 2

**Security Groups:**
- vpc-endpoints: sg-08b7d1c7ddd3b1714
- lambda: sg-04993f88d8e4b79b6
- api-gateway: sg-076bda479b613a34b
- glue: sg-0252d456c3741698c
- mwaa: sg-0942978ba46eabf33
- redshift: sg-02fda7d7db3d28a71
- eventbridge: sg-03c15d3c0774b9b90

**VPC Endpoints:**
- S3 Gateway: vpce-0d5d64ab9bc5dd93a
- Glue: vpce-076a7071129507528
- Secrets Manager: vpce-0dfe00403a10e879b
- KMS: vpce-0dd58493aecfce40c
- CloudWatch Logs: vpce-015d2aeda1a0d139b
- STS: vpce-02f3c6cb6a3b2b9bc
- EventBridge: vpce-06607ac2dc0d9ce8a

**S3 Buckets:**
- Bronze: janis-cencosud-integration-prod-datalake-bronze
- Silver: janis-cencosud-integration-prod-datalake-silver
- Gold: janis-cencosud-integration-prod-datalake-gold
- Scripts: janis-cencosud-integration-prod-scripts
- Logs: janis-cencosud-integration-prod-logs

**Glue Databases:**
- Bronze: janis_cencosud_integration_prod_bronze
- Silver: janis_cencosud_integration_prod_silver
- Gold: janis_cencosud_integration_prod_gold

**Kinesis Firehose:**
- Stream: janis-cencosud-integration-prod-orders-stream
- Destino: S3 Bronze bucket
- Buffering: 5 MB / 300 segundos

**EventBridge:**
- Event Bus: janis-cencosud-integration-prod-polling-bus
- Reglas programadas: 5 (orders, products, stock, prices, stores)
- Dead Letter Queue: Configurado

**CloudWatch Monitoring:**
- Alarmas: 11 configuradas
- Metric Filters: 4 configurados
- VPC Flow Logs: Habilitados
- DNS Query Logs: Habilitados

**Terraform Destroy**
- Destrucción completa: ✅ Exitosa
- Recursos eliminados: 141 recursos
- Tiempo de ejecución: ~3 minutos
- Estado final: Limpio (sin recursos huérfanos)

### **Validación de Seguridad**

**Cifrado:**
- S3 buckets: AES256 habilitado
- Datos en tránsito: TLS/SSL en VPC endpoints
- KMS: Endpoint privado configurado

**Acceso:**
- Buckets S3: Acceso público bloqueado
- Subnets privadas: Sin acceso directo a internet
- NAT Gateway: Configurado para salida controlada
- Security Groups: Reglas de menor privilegio

**Monitoreo:**
- VPC Flow Logs: Activos
- DNS Query Logs: Activos
- CloudWatch Alarms: 11 alarmas críticas
- Metric Filters: Detección de anomalías

### **Archivo de Deployment Generado**

**Nombre:** terraform-cencosud.zip  
**Tamaño:** ~144 MB  
**Contenido:**
- Código Terraform completo (12 módulos)
- Configuración de producción (terraform.tfvars.prod)
- README con instrucciones
- .gitignore para seguridad

---

## **PARTE 2: LO QUE DEBE HACER CENCOSUD**

### **Requisitos Previos**

**Software Necesario:**
- Terraform >= 1.0 instalado
- AWS CLI configurado
- Acceso a cuenta AWS 827739413930 (o su cuenta de producción)
- Permisos de administrador o permisos específicos para crear recursos

**Credenciales AWS:**
- Access Key ID
- Secret Access Key
- Session Token (si usan MFA/STS)

### **Pasos de Configuración**

**Paso 1: Descomprimir el Paquete**

```bash
# Descomprimir el archivo
unzip terraform-cencosud.zip

# Navegar al directorio
cd terraform
```

Tiempo estimado: 1 minuto

**Paso 2: Revisar y Editar Configuración**

Archivo a editar: `terraform.tfvars.prod`

**Variables CRÍTICAS a revisar:**

```hcl
# 1. Región AWS (cambiar si no es us-east-1)
aws_region = "us-east-1"

# 2. CIDR blocks (cambiar si hay conflictos con red existente)
vpc_cidr = "10.0.0.0/16"
public_subnet_cidrs = ["10.0.0.0/24"]
private_subnet_cidrs = ["10.0.10.0/24", "10.0.11.0/24"]

# 3. IPs permitidas para acceso a Redshift (IPs de Power BI)
bi_allowed_ips = [
  "200.1.2.3/32",    # Cambiar por IP real de Power BI 1
  "200.1.2.4/32"     # Cambiar por IP real de Power BI 2
]

# 4. Tags corporativos (ajustar a estándares de Cencosud)
project_name = "janis-cencosud-integration"
owner = "data-engineering-team"
cost_center = "CC-12345"              # Cambiar por centro de costo real
business_unit = "Data-Analytics"
country = "CL"

# 5. Nombres de buckets S3 (deben ser únicos globalmente)
# Si ya existen buckets con estos nombres, cambiarlos
```

**Variables OPCIONALES a revisar:**

```hcl
# Zonas de disponibilidad
availability_zones = ["us-east-1a"]

# Configuración de EventBridge schedules
eventbridge_schedules = {
  orders   = "rate(15 minutes)"
  products = "rate(30 minutes)"
  stock    = "rate(15 minutes)"
  prices   = "rate(60 minutes)"
  stores   = "rate(24 hours)"
}

# Componentes deshabilitados (sin código aún)
enable_lambda_functions = false
enable_api_gateway = false
enable_glue_jobs = false
enable_mwaa = false
```

Tiempo estimado: 10-15 minutos

**Paso 3: Configurar Credenciales AWS**

**IMPORTANTE:** NO incluir credenciales en archivos .tfvars

**Opción A: Variables de entorno (recomendado)**

```bash
export AWS_ACCESS_KEY_ID="AKIAIOSFODNN7EXAMPLE"
export AWS_SECRET_ACCESS_KEY="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
export AWS_SESSION_TOKEN="token-si-usan-mfa"  # Opcional
```

**Opción B: AWS CLI Profile**

```bash
aws configure --profile cencosud
export AWS_PROFILE=cencosud
```

**Opción C: Pasar por línea de comandos**

```bash
terraform apply \
  -var-file="terraform.tfvars.prod" \
  -var="aws_access_key_id=$AWS_ACCESS_KEY_ID" \
  -var="aws_secret_access_key=$AWS_SECRET_ACCESS_KEY"
```

Tiempo estimado: 2-3 minutos

### **Total de Tiempo Estimado**

15-20 minutos de configuración inicial

### **Confirmación Requerida**

Antes de ejecutar `terraform apply`, confirmar:

1. ✅ Archivo terraform.tfvars.prod editado con valores correctos
2. ✅ Credenciales AWS configuradas
3. ✅ Permisos AWS verificados
4. ✅ CIDR blocks no tienen conflictos con red existente
5. ✅ Nombres de buckets S3 son únicos

---

## **PARTE 3: COMANDOS PARA EJECUTAR EL DEPLOYMENT**

### **Inicialización de Terraform**

**Paso 1: Inicializar Terraform**

```bash
cd terraform
terraform init
```

**Salida esperada:**
```
Initializing modules...
Initializing the backend...
Initializing provider plugins...
- Finding hashicorp/aws versions matching "~> 5.0"...
- Installing hashicorp/aws v5.100.0...

Terraform has been successfully initialized!
```

Tiempo estimado: 1-2 minutos

### **Validación de Configuración**

**Paso 2: Formatear código (opcional)**

```bash
terraform fmt -recursive
```

**Paso 3: Validar sintaxis**

```bash
terraform validate
```

**Salida esperada:**
```
Success! The configuration is valid.
```

### **Planificación del Deployment**

**Paso 4: Ejecutar Plan**

```bash
terraform plan -var-file="terraform.tfvars.prod" -out=prod.tfplan
```

**Salida esperada:**
```
Plan: 141 to add, 0 to change, 0 to destroy.

Saved the plan to: prod.tfplan
```

**Revisar el plan cuidadosamente:**
- Verificar que los recursos a crear son los esperados
- Verificar CIDRs, nombres, tags
- Verificar que no hay recursos a destruir (si es primera vez)

Tiempo estimado: 30-60 segundos

### **Ejecución del Deployment**

**Paso 5: Aplicar Configuración**

**Opción A: Con confirmación manual (recomendado primera vez)**

```bash
terraform apply -var-file="terraform.tfvars.prod"
```

Terraform pedirá confirmación:
```
Do you want to perform these actions?
  Terraform will perform the actions described above.
  Only 'yes' will be accepted to approve.

  Enter a value: yes
```

**Opción B: Sin confirmación (para automatización)**

```bash
terraform apply -var-file="terraform.tfvars.prod" -auto-approve
```

**Opción C: Usando el plan guardado**

```bash
terraform apply prod.tfplan
```

**Salida esperada:**
```
Apply complete! Resources: 141 added, 0 changed, 0 destroyed.

Outputs:

vpc_id = "vpc-xxxxxxxxxxxxxxxxx"
nat_gateway_public_ip = "xx.xx.xx.xx"
bronze_bucket_name = "janis-cencosud-integration-prod-datalake-bronze"
...
```

Tiempo estimado: 3-5 minutos

### **Validación Post-Deployment**

**Paso 6: Verificar Outputs**

```bash
terraform output
```

**Paso 7: Verificar recursos en AWS Console**

Navegar a AWS Console y verificar:
- VPC creada
- Subnets creadas
- S3 buckets creados
- Security Groups configurados

**Paso 8: Verificar estado de Terraform**

```bash
terraform show
```

### **Comandos de Gestión**

**Ver estado actual:**

```bash
terraform state list
```

**Ver detalles de un recurso específico:**

```bash
terraform state show module.vpc.aws_vpc.main
```

**Refrescar estado (sincronizar con AWS):**

```bash
terraform refresh -var-file="terraform.tfvars.prod"
```

**Ver plan de cambios sin aplicar:**

```bash
terraform plan -var-file="terraform.tfvars.prod"
```

### **Comandos de Troubleshooting**

**Habilitar logs detallados:**

```bash
export TF_LOG=DEBUG
export TF_LOG_PATH=terraform.log
terraform apply -var-file="terraform.tfvars.prod"
```

**Verificar versión de Terraform:**

```bash
terraform version
```

**Verificar providers instalados:**

```bash
terraform providers
```

**Validar credenciales AWS:**

```bash
aws sts get-caller-identity
```

### **Comandos de Limpieza (Solo si es necesario)**

**ADVERTENCIA:** Estos comandos destruyen toda la infraestructura

**Destruir todos los recursos:**

```bash
terraform destroy -var-file="terraform.tfvars.prod"
```

**Destruir recursos específicos:**

```bash
terraform destroy -target=module.s3.aws_s3_bucket.bronze -var-file="terraform.tfvars.prod"
```

---

## **Checklist de Deployment**

### **Pre-Deployment**

- [ ] Terraform >= 1.0 instalado
- [ ] AWS CLI configurado
- [ ] Credenciales AWS configuradas
- [ ] Archivo terraform.tfvars.prod editado
- [ ] CIDR blocks validados (sin conflictos)
- [ ] IPs de Power BI actualizadas
- [ ] Tags corporativos actualizados
- [ ] Nombres de buckets S3 únicos verificados

### **Durante Deployment**

- [ ] `terraform init` ejecutado exitosamente
- [ ] `terraform validate` sin errores
- [ ] `terraform plan` revisado y aprobado
- [ ] Plan muestra 141 recursos a crear
- [ ] `terraform apply` ejecutado
- [ ] Apply completado sin errores

### **Post-Deployment**

- [ ] Outputs de Terraform verificados
- [ ] VPC visible en AWS Console
- [ ] S3 buckets creados y accesibles
- [ ] Security Groups configurados correctamente
- [ ] VPC Endpoints operacionales
- [ ] CloudWatch alarms activas
- [ ] VPC Flow Logs habilitados
- [ ] Estado de Terraform guardado correctamente

---

## **Troubleshooting**

### **Error: "Bucket already exists"**

**Causa:** Nombre de bucket S3 ya existe globalmente

**Solución:**
```hcl
# En terraform.tfvars.prod, cambiar nombres de buckets
# Agregar sufijo único, por ejemplo:
# janis-cencosud-integration-prod-datalake-bronze-cl-2026
```

### **Error: "Insufficient permissions"**

**Causa:** Credenciales AWS sin permisos necesarios

**Solución:**
```bash
# Verificar permisos
aws iam get-user
aws iam list-attached-user-policies --user-name <username>

# Contactar administrador AWS para otorgar permisos
```

### **Error: "CIDR block overlaps"**

**Causa:** CIDR de VPC conflicta con VPC existente

**Solución:**
```hcl
# En terraform.tfvars.prod, cambiar CIDR
vpc_cidr = "10.10.0.0/16"  # Usar rango diferente
```

### **Error: "Provider configuration not present"**

**Causa:** Credenciales AWS no configuradas

**Solución:**
```bash
export AWS_ACCESS_KEY_ID="..."
export AWS_SECRET_ACCESS_KEY="..."
```

### **Error: "State lock"**

**Causa:** Otro proceso tiene el state bloqueado

**Solución:**
```bash
# Esperar a que termine el otro proceso, o forzar unlock
terraform force-unlock <lock-id>
```

---

## **Información de Contacto**

**Cuenta AWS de Prueba:**
- Account ID: 827739413930
- Región: us-east-1
- Recursos creados: 141
- Estado: Validado y destruido

**Archivos Entregados:**
- terraform-cencosud.zip (~144 MB)
- README.md (instrucciones básicas)
- .gitignore (seguridad)

**Documentación Adicional:**
- TERRAFORM_DEPLOYMENT_VERIFICATION.md (resultados de pruebas)
- terraform.tfvars.prod (configuración de producción)
- terraform.tfvars.example (ejemplo de configuración)

---

## **Próximos Pasos**

1. **Cencosud:** Revisar y editar terraform.tfvars.prod
2. **Cencosud:** Configurar credenciales AWS
3. **Cencosud:** Ejecutar terraform init
4. **Cencosud:** Ejecutar terraform plan y revisar
5. **Cencosud:** Ejecutar terraform apply
6. **Cencosud:** Validar recursos en AWS Console
7. **Cencosud:** Confirmar deployment exitoso
8. **3HTP:** Implementar código de Lambda, Glue, MWAA (Fase 2)

---

## **Recursos Creados - Resumen**

| Categoría | Cantidad | Estado |
|-----------|----------|--------|
| VPC & Networking | 15 | ✅ Validado |
| Security Groups | 7 | ✅ Validado |
| VPC Endpoints | 7 | ✅ Validado |
| S3 Buckets | 5 | ✅ Validado |
| Glue Databases | 3 | ✅ Validado |
| Kinesis Firehose | 1 | ✅ Validado |
| EventBridge | 6 | ✅ Validado |
| CloudWatch | 15+ | ✅ Validado |
| IAM Roles | 4 | ✅ Validado |
| **TOTAL** | **141** | ✅ **LISTO** |

---

## **Costos Estimados**

**Infraestructura Base (mensual):**
- NAT Gateway: ~$50
- VPC Endpoints: ~$50
- S3 Storage: ~$10-50 (según volumen)
- Kinesis Firehose: ~$20
- CloudWatch: ~$10
- EventBridge: ~$5

**Total Estimado:** $145-185 USD/mes

**Nota:** Costos de Lambda, Glue y MWAA se agregarán en Fase 2

---

Preparado por: Equipo 3HTP  
Fecha: 5 de febrero de 2026  
Versión: 1.0  
Estado: Infraestructura Validada - Lista para Deployment por Cencosud
