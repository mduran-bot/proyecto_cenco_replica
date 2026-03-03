# Guia Rapida de Deployment

**Proyecto**: Janis-Cencosud AWS Infrastructure

---

## Pasos para Desplegar

### 1. Configurar Credenciales AWS

```powershell
# Opcion 1: Variables de entorno
$env:AWS_ACCESS_KEY_ID = "AKIA..."
$env:AWS_SECRET_ACCESS_KEY = "..."
$env:AWS_SESSION_TOKEN = "..."  # Si usa MFA/STS

# Opcion 2: AWS CLI Profile
aws configure --profile cencosud-prod
```

### 2. Editar Configuracion

Editar el archivo **terraform/terraform.tfvars** con los valores de su ambiente:

- **aws_account_id**: Su Account ID de AWS
- **vpc_cidr**: Rangos de red (coordinar con equipo de redes)
- **allowed_janis_ip_ranges**: IPs publicas de Janis (NUNCA usar 0.0.0.0/0 en produccion)
- **cost_center**: Centro de costos real
- **existing_redshift_cluster_id**: ID de cluster Redshift si existe
- **mwaa_environment_arn**: ARN de MWAA si existe

Ver **terraform/terraform.tfvars.testing.annotated** para guia detallada de cada variable.

### 3. Inicializar Terraform

```powershell
cd terraform
terraform init
```

### 4. Validar Configuracion

```powershell
# Formatear codigo
terraform fmt -recursive

# Validar sintaxis
terraform validate

# Ver plan de deployment
terraform plan -var-file="terraform.tfvars"
```

### 5. Desplegar Infraestructura

```powershell
# Aplicar cambios (requiere confirmacion)
terraform apply -var-file="terraform.tfvars"

# O aplicar sin confirmacion (NO RECOMENDADO para produccion)
terraform apply -auto-approve -var-file="terraform.tfvars"
```

### 6. Verificar Deployment

Revisar los outputs de Terraform:
- VPC ID
- Subnet IDs
- Security Group IDs
- VPC Endpoint IDs
- NAT Gateway IP publica

---

## Comandos Utiles

### Ver Estado Actual
```powershell
terraform show
terraform state list
```

### Ver Outputs
```powershell
terraform output
terraform output vpc_id
```

### Destruir Infraestructura (CUIDADO)
```powershell
# Solo para ambientes de testing
terraform destroy -var-file="terraform.tfvars"
```

---

## Documentacion Completa

Ver los siguientes documentos en la carpeta **documentacion/**:

1. **CONFIGURACION_CLIENTE.md** - Guia completa de configuracion
2. **TERRAFORM_DEPLOYMENT_GUIDE.md** - Guia detallada de deployment
3. **Politica_Etiquetado_AWS.md** - Politica de tags corporativa
4. **TERRAFORM_DEPLOYMENT_TEST_RESULTS.md** - Resultados de testing

---

## Soporte

Para dudas o problemas:
1. Revisar la documentacion completa
2. Verificar logs de Terraform
3. Contactar al equipo de DevOps

---

**IMPORTANTE**: 
- Probar primero en ambiente de desarrollo/QA
- Coordinar con equipo de redes para rangos CIDR
- Obtener IPs publicas reales de Janis antes de produccion
- Crear SNS Topic para alarmas antes del deployment
