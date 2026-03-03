# Solicitud de Permisos AWS para Configuración y Soporte

**Proyecto:** Janis-Cencosud Data Integration Platform  
**Fecha:** 3 de Febrero, 2026  
**Destinatario:** Equipo de Infraestructura y Seguridad - Cencosud

---

## Resumen Ejecutivo

Para poder brindar soporte técnico durante la configuración, validación y deployment de la infraestructura Terraform del proyecto Janis-Cencosud, solicitamos acceso de **solo lectura (read-only)** a los servicios AWS relevantes.

**Importante:** No se requieren permisos de escritura, modificación o eliminación de recursos. El cliente ejecutará el Terraform por su cuenta, nosotros solo necesitamos visibilidad para validar configuraciones y dar soporte.

---

## Objetivo del Acceso

1. **Validar la Landing Zone existente** (VPC, subnets, NAT Gateway, etc.)
2. **Revisar recursos existentes** (Redshift, Security Groups, etc.)
3. **Verificar configuración de red** antes del deployment
4. **Dar soporte técnico** durante la ejecución de Terraform
5. **Troubleshooting** en caso de errores o problemas
6. **Validar compliance** con políticas corporativas de tagging

---

## Permisos Solicitados (Solo Lectura)

### 1. Networking y VPC
**Servicios:** Amazon VPC, EC2 Networking  
**Justificación:** Validar que la Landing Zone cumple con los requisitos del proyecto

**Permisos necesarios:**
- `ec2:DescribeVpcs`
- `ec2:DescribeSubnets`
- `ec2:DescribeRouteTables`
- `ec2:DescribeInternetGateways`
- `ec2:DescribeNatGateways`
- `ec2:DescribeSecurityGroups`
- `ec2:DescribeNetworkAcls`
- `ec2:DescribeVpcEndpoints`
- `ec2:DescribeAvailabilityZones`

### 2. IAM (Identity and Access Management)
**Justificación:** Validar roles y políticas existentes que usarán los servicios

**Permisos necesarios:**
- `iam:GetRole`
- `iam:GetPolicy`
- `iam:GetPolicyVersion`
- `iam:ListRoles`
- `iam:ListPolicies`
- `iam:ListAttachedRolePolicies`

### 3. Amazon S3
**Justificación:** Validar configuración de buckets para el Data Lake

**Permisos necesarios:**
- `s3:ListAllMyBuckets`
- `s3:GetBucketLocation`
- `s3:GetBucketVersioning`
- `s3:GetBucketEncryption`
- `s3:GetBucketPolicy`
- `s3:GetBucketTagging`

### 4. Amazon Redshift
**Justificación:** Validar cluster existente y configuración de conectividad

**Permisos necesarios:**
- `redshift:DescribeClusters`
- `redshift:DescribeClusterSubnetGroups`
- `redshift:DescribeClusterSecurityGroups`

### 5. AWS Lambda
**Justificación:** Validar configuración de funciones Lambda

**Permisos necesarios:**
- `lambda:ListFunctions`
- `lambda:GetFunction`
- `lambda:GetFunctionConfiguration`

### 6. Amazon MWAA (Managed Airflow)
**Justificación:** Validar ambiente de Airflow si existe

**Permisos necesarios:**
- `airflow:GetEnvironment`
- `airflow:ListEnvironments`

### 7. AWS Glue
**Justificación:** Validar configuración de jobs ETL

**Permisos necesarios:**
- `glue:GetDatabase`
- `glue:GetTable`
- `glue:GetJob`
- `glue:ListJobs`

### 8. Amazon EventBridge
**Justificación:** Validar reglas de scheduling

**Permisos necesarios:**
- `events:ListEventBuses`
- `events:ListRules`
- `events:DescribeRule`

### 9. Amazon CloudWatch
**Justificación:** Validar logs, métricas y alarmas

**Permisos necesarios:**
- `logs:DescribeLogGroups`
- `logs:DescribeLogStreams`
- `cloudwatch:DescribeAlarms`
- `cloudwatch:ListMetrics`

### 10. AWS Secrets Manager
**Justificación:** Validar gestión de credenciales

**Permisos necesarios:**
- `secretsmanager:ListSecrets`
- `secretsmanager:DescribeSecret`

### 11. AWS KMS
**Justificación:** Validar configuración de cifrado

**Permisos necesarios:**
- `kms:ListKeys`
- `kms:DescribeKey`
- `kms:ListAliases`

### 12. Otros Servicios
**Justificación:** Validación general y troubleshooting

**Permisos necesarios:**
- `sts:GetCallerIdentity` (validar identidad)
- `route53resolver:ListResolverQueryLogConfigs` (DNS logging)
- `route53resolver:GetResolverQueryLogConfig`
- `sqs:ListQueues` (Dead Letter Queues)
- `sqs:GetQueueAttributes`
- `sns:ListTopics` (notificaciones)
- `sns:GetTopicAttributes`
- `tag:GetResources` (compliance de tags)
- `tag:GetTagKeys`
- `tag:GetTagValues`

---

## Política IAM Propuesta

Hemos preparado una política IAM en formato JSON que el equipo de seguridad puede revisar y aplicar:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "ReadOnlyNetworking",
      "Effect": "Allow",
      "Action": [
        "ec2:Describe*"
      ],
      "Resource": "*"
    },
    {
      "Sid": "ReadOnlyIAM",
      "Effect": "Allow",
      "Action": [
        "iam:Get*",
        "iam:List*"
      ],
      "Resource": "*"
    },
    {
      "Sid": "ReadOnlyS3",
      "Effect": "Allow",
      "Action": [
        "s3:ListAllMyBuckets",
        "s3:GetBucket*"
      ],
      "Resource": "*"
    },
    {
      "Sid": "ReadOnlyDataServices",
      "Effect": "Allow",
      "Action": [
        "redshift:Describe*",
        "glue:Get*",
        "glue:List*",
        "lambda:List*",
        "lambda:Get*",
        "airflow:Get*",
        "airflow:List*"
      ],
      "Resource": "*"
    },
    {
      "Sid": "ReadOnlyMonitoring",
      "Effect": "Allow",
      "Action": [
        "logs:Describe*",
        "cloudwatch:Describe*",
        "cloudwatch:List*",
        "events:Describe*",
        "events:List*"
      ],
      "Resource": "*"
    },
    {
      "Sid": "ReadOnlySecurity",
      "Effect": "Allow",
      "Action": [
        "secretsmanager:List*",
        "secretsmanager:Describe*",
        "kms:List*",
        "kms:Describe*"
      ],
      "Resource": "*"
    },
    {
      "Sid": "ReadOnlyOther",
      "Effect": "Allow",
      "Action": [
        "sts:GetCallerIdentity",
        "route53resolver:List*",
        "route53resolver:Get*",
        "sqs:List*",
        "sqs:GetQueueAttributes",
        "sns:List*",
        "sns:GetTopicAttributes",
        "tag:Get*"
      ],
      "Resource": "*"
    }
  ]
}
```

**Nombre sugerido para la política:** `JanisCencosud-ReadOnly-Support-Policy`

---

## Método de Acceso Recomendado

Solicitamos que se cree uno de los siguientes métodos de acceso:

### Opción 1: IAM User (Recomendado para soporte externo)
- **Tipo:** IAM User con acceso programático
- **Política:** Adjuntar la política JSON proporcionada arriba
- **MFA:** Habilitado (recomendado)
- **Credenciales:** Access Key ID + Secret Access Key
- **Duración:** Temporal durante el período de configuración (ej: 30 días)

### Opción 2: IAM Role con AssumeRole
- **Tipo:** IAM Role que podemos asumir desde nuestra cuenta AWS
- **Política:** Adjuntar la política JSON proporcionada arriba
- **Trust Relationship:** Configurar para permitir AssumeRole desde nuestra cuenta
- **Duración de sesión:** 8 horas
- **MFA:** Requerido para asumir el rol

### Opción 3: AWS SSO (Si el cliente usa AWS Organizations)
- **Tipo:** Permission Set en AWS SSO
- **Política:** Adjuntar la política JSON proporcionada arriba
- **Duración de sesión:** 8 horas
- **MFA:** Habilitado

---

## Información Adicional Requerida

Además de los permisos de acceso, necesitamos que nos proporcionen la siguiente información:

### 1. IDs de Recursos Existentes

```
VPC ID:                    vpc-_________________
VPC CIDR:                  ___.___.___.___ / __

Subnet Pública AZ A:       subnet-_________________
Subnet Privada 1 AZ A:     subnet-_________________ (Lambda/MWAA/Redshift)
Subnet Privada 2 AZ A:     subnet-_________________ (Glue ENIs)

Route Table Privada:       rtb-_________________
NAT Gateway ID:            nat-_________________
Internet Gateway ID:       igw-_________________

Redshift Cluster ID:       _________________
Redshift Security Group:   sg-_________________

MWAA Environment ARN:      arn:aws:airflow:_________________
(si existe)

SNS Topic para Alarmas:    arn:aws:sns:_________________
(si existe)
```

### 2. Configuración Corporativa

```
AWS Region:                _________________
AWS Account ID:            _________________

Cost Center Code:          _________________
Business Unit:             _________________
Environment:               [ ] dev  [ ] qa  [ ] prod

Rangos IP de Janis:        _________________
                          _________________

Retención de Logs VPC:     ___ días
Retención de Logs DNS:     ___ días
```

### 3. Security Groups Existentes (si aplican)

```
BI Tools Security Groups:  sg-_________________
                          sg-_________________

MySQL Pipeline SG:         sg-_________________
(temporal durante migración)
```

---

## Garantías de Seguridad

Nos comprometemos a:

✅ **Usar los permisos únicamente para los fines descritos** (validación y soporte)  
✅ **No acceder a datos sensibles** en S3, Redshift o Secrets Manager  
✅ **No realizar modificaciones** en ningún recurso AWS  
✅ **Mantener las credenciales seguras** según mejores prácticas  
✅ **Habilitar MFA** en todas las cuentas de acceso  
✅ **Revocar acceso** inmediatamente al finalizar el proyecto  
✅ **Documentar todos los accesos** realizados  
✅ **Notificar cualquier hallazgo de seguridad** al equipo del cliente  

---

## Duración del Acceso

**Período solicitado:** 30 días desde la fecha de inicio del proyecto

**Justificación:**
- Semana 1-2: Validación de Landing Zone y configuración inicial
- Semana 3: Deployment y pruebas
- Semana 4: Ajustes finales y documentación

**Compromiso:** Solicitaremos la revocación del acceso inmediatamente al completar el proyecto o antes si no es necesario.

---

## Comandos para Crear el Acceso

### Crear la Política IAM:

```bash
# 1. Guardar la política JSON en un archivo: janis-readonly-policy.json

# 2. Crear la política en AWS
aws iam create-policy \
  --policy-name JanisCencosud-ReadOnly-Support-Policy \
  --policy-document file://janis-readonly-policy.json \
  --description "Read-only access for Janis-Cencosud project support"
```

### Crear IAM User (Opción 1):

```bash
# 1. Crear el usuario
aws iam create-user --user-name janis-support-readonly

# 2. Adjuntar la política
aws iam attach-user-policy \
  --user-name janis-support-readonly \
  --policy-arn arn:aws:iam::ACCOUNT_ID:policy/JanisCencosud-ReadOnly-Support-Policy

# 3. Crear access keys
aws iam create-access-key --user-name janis-support-readonly

# 4. Habilitar MFA (recomendado)
aws iam enable-mfa-device \
  --user-name janis-support-readonly \
  --serial-number arn:aws:iam::ACCOUNT_ID:mfa/janis-support-readonly \
  --authentication-code-1 CODE1 \
  --authentication-code-2 CODE2
```

### Crear IAM Role (Opción 2):

```bash
# 1. Crear trust policy (trust-policy.json)
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::EXTERNAL_ACCOUNT_ID:root"
      },
      "Action": "sts:AssumeRole",
      "Condition": {
        "Bool": {
          "aws:MultiFactorAuthPresent": "true"
        }
      }
    }
  ]
}

# 2. Crear el rol
aws iam create-role \
  --role-name JanisCencosud-Support-ReadOnly-Role \
  --assume-role-policy-document file://trust-policy.json

# 3. Adjuntar la política
aws iam attach-role-policy \
  --role-name JanisCencosud-Support-ReadOnly-Role \
  --policy-arn arn:aws:iam::ACCOUNT_ID:policy/JanisCencosud-ReadOnly-Support-Policy
```

---

## Validación del Acceso

Una vez creado el acceso, podemos validar que funciona correctamente con estos comandos:

```bash
# Validar identidad
aws sts get-caller-identity

# Listar VPCs (debe funcionar)
aws ec2 describe-vpcs

# Intentar crear un recurso (debe fallar - sin permisos)
aws ec2 create-vpc --cidr-block 10.0.0.0/16
# Esperado: AccessDenied
```

---

## Contacto

Para cualquier duda o aclaración sobre esta solicitud:

**Equipo de Desarrollo:**  
- Email: [tu-email@empresa.com]  
- Teléfono: [tu-teléfono]

**Horario de soporte:**  
- Lunes a Viernes: 9:00 AM - 6:00 PM (Hora local)

---

## Anexos

- **Anexo A:** Política IAM completa en formato JSON
- **Anexo B:** Diagrama de arquitectura del proyecto
- **Anexo C:** Guía de configuración de Landing Zone
- **Anexo D:** Checklist de validación pre-deployment

---

**Fecha de solicitud:** 3 de Febrero, 2026  
**Solicitado por:** [Tu Nombre/Empresa]  
**Aprobación requerida de:** Equipo de Seguridad y Compliance - Cencosud

---

## Notas Importantes

⚠️ **Este acceso NO incluye:**
- Permisos de escritura, modificación o eliminación
- Acceso a datos sensibles (contenido de S3, datos de Redshift)
- Acceso a billing o cost management
- Permisos para crear o modificar IAM roles/policies
- Acceso a otros proyectos o recursos fuera del scope de Janis-Cencosud

✅ **Este acceso SÍ permite:**
- Ver configuración de recursos existentes
- Validar arquitectura de red
- Revisar políticas y roles (sin modificar)
- Dar soporte técnico durante deployment
- Troubleshooting de errores de configuración
