# Solicitud de Permisos AWS - Resumen

**Fecha**: 3 de Febrero, 2026  
**Documento relacionado**: [../SOLICITUD_PERMISOS_AWS_CLIENTE.md](../SOLICITUD_PERMISOS_AWS_CLIENTE.md)

---

## Resumen Ejecutivo

Se ha creado un **documento formal de solicitud de permisos AWS** para facilitar el soporte técnico durante la configuración, validación y deployment de la infraestructura Terraform del proyecto Janis-Cencosud.

## Propósito

El documento de solicitud de permisos permite:
- ✅ Solicitar acceso read-only a servicios AWS relevantes
- ✅ Proporcionar justificación clara para cada permiso
- ✅ Incluir política IAM completa lista para usar
- ✅ Ofrecer múltiples métodos de acceso (IAM User, Role, SSO)
- ✅ Establecer garantías de seguridad y duración del acceso
- ✅ Facilitar la validación de la Landing Zone del cliente
- ✅ Permitir troubleshooting durante el deployment

## Contenido del Documento

### 1. Objetivo del Acceso

El documento explica claramente los 6 objetivos principales:
1. Validar la Landing Zone existente (VPC, subnets, NAT Gateway)
2. Revisar recursos existentes (Redshift, Security Groups)
3. Verificar configuración de red antes del deployment
4. Dar soporte técnico durante la ejecución de Terraform
5. Troubleshooting en caso de errores o problemas
6. Validar compliance con políticas corporativas de tagging

### 2. Permisos Solicitados (Solo Lectura)

El documento detalla permisos read-only para **12 categorías de servicios AWS**:

1. **Networking y VPC**: Validar Landing Zone
   - `ec2:DescribeVpcs`, `ec2:DescribeSubnets`, `ec2:DescribeRouteTables`, etc.

2. **IAM**: Validar roles y políticas
   - `iam:GetRole`, `iam:ListRoles`, `iam:ListPolicies`, etc.

3. **Amazon S3**: Validar configuración de buckets
   - `s3:ListAllMyBuckets`, `s3:GetBucketEncryption`, etc.

4. **Amazon Redshift**: Validar cluster existente
   - `redshift:DescribeClusters`, `redshift:DescribeClusterSubnetGroups`, etc.

5. **AWS Lambda**: Validar funciones Lambda
   - `lambda:ListFunctions`, `lambda:GetFunction`, etc.

6. **Amazon MWAA**: Validar ambiente de Airflow
   - `airflow:GetEnvironment`, `airflow:ListEnvironments`

7. **AWS Glue**: Validar jobs ETL
   - `glue:GetDatabase`, `glue:GetJob`, `glue:ListJobs`, etc.

8. **Amazon EventBridge**: Validar reglas de scheduling
   - `events:ListEventBuses`, `events:ListRules`, etc.

9. **Amazon CloudWatch**: Validar logs y alarmas
   - `logs:DescribeLogGroups`, `cloudwatch:DescribeAlarms`, etc.

10. **AWS Secrets Manager**: Validar gestión de credenciales
    - `secretsmanager:ListSecrets`, `secretsmanager:DescribeSecret`

11. **AWS KMS**: Validar configuración de cifrado
    - `kms:ListKeys`, `kms:DescribeKey`, etc.

12. **Otros Servicios**: Validación general
    - `sts:GetCallerIdentity`, `route53resolver:*`, `sqs:*`, `sns:*`, `tag:*`

### 3. Política IAM Propuesta

El documento incluye una **política IAM completa en formato JSON** lista para usar:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "ReadOnlyNetworking",
      "Effect": "Allow",
      "Action": ["ec2:Describe*"],
      "Resource": "*"
    },
    // ... 6 statements más para otros servicios
  ]
}
```

**Nombre sugerido**: `JanisCencosud-ReadOnly-Support-Policy`

### 4. Métodos de Acceso Recomendados

El documento propone **3 opciones de acceso**:

#### Opción 1: IAM User (Recomendado para soporte externo)
- IAM User con acceso programático
- MFA habilitado
- Credenciales: Access Key ID + Secret Access Key
- Duración: Temporal (30 días)

#### Opción 2: IAM Role con AssumeRole
- IAM Role asumible desde cuenta externa
- Trust Relationship configurado
- Duración de sesión: 8 horas
- MFA requerido para asumir el rol

#### Opción 3: AWS SSO
- Permission Set en AWS SSO
- Duración de sesión: 8 horas
- MFA habilitado

### 5. Información Adicional Requerida

El documento solicita al cliente que proporcione:

#### IDs de Recursos Existentes
- VPC ID y CIDR
- Subnet IDs (públicas y privadas)
- Route Table IDs
- NAT Gateway ID
- Internet Gateway ID
- Redshift Cluster ID y Security Group
- MWAA Environment ARN (si existe)
- SNS Topic para Alarmas (si existe)

#### Configuración Corporativa
- AWS Region y Account ID
- Cost Center Code
- Business Unit
- Environment (dev/qa/prod)
- Rangos IP de Janis
- Retención de Logs (VPC y DNS)

#### Security Groups Existentes
- BI Tools Security Groups
- MySQL Pipeline SG (temporal)

### 6. Garantías de Seguridad

El documento establece **8 compromisos de seguridad**:

✅ Usar permisos únicamente para validación y soporte  
✅ No acceder a datos sensibles  
✅ No realizar modificaciones  
✅ Mantener credenciales seguras  
✅ Habilitar MFA  
✅ Revocar acceso al finalizar  
✅ Documentar todos los accesos  
✅ Notificar hallazgos de seguridad  

### 7. Duración del Acceso

**Período solicitado**: 30 días

**Justificación por semana**:
- Semana 1-2: Validación de Landing Zone y configuración inicial
- Semana 3: Deployment y pruebas
- Semana 4: Ajustes finales y documentación

**Compromiso**: Revocación inmediata al completar el proyecto

### 8. Comandos para Crear el Acceso

El documento incluye **comandos AWS CLI completos** para:

#### Crear la Política IAM
```bash
aws iam create-policy \
  --policy-name JanisCencosud-ReadOnly-Support-Policy \
  --policy-document file://janis-readonly-policy.json
```

#### Crear IAM User (Opción 1)
```bash
aws iam create-user --user-name janis-support-readonly
aws iam attach-user-policy --user-name janis-support-readonly --policy-arn ...
aws iam create-access-key --user-name janis-support-readonly
```

#### Crear IAM Role (Opción 2)
```bash
aws iam create-role --role-name JanisCencosud-Support-ReadOnly-Role --assume-role-policy-document file://trust-policy.json
aws iam attach-role-policy --role-name JanisCencosud-Support-ReadOnly-Role --policy-arn ...
```

### 9. Validación del Acceso

El documento proporciona comandos para validar que el acceso funciona correctamente:

```bash
# Validar identidad
aws sts get-caller-identity

# Listar VPCs (debe funcionar)
aws ec2 describe-vpcs

# Intentar crear un recurso (debe fallar)
aws ec2 create-vpc --cidr-block 10.0.0.0/16
# Esperado: AccessDenied
```

### 10. Notas Importantes

El documento clarifica explícitamente:

**⚠️ Este acceso NO incluye:**
- Permisos de escritura, modificación o eliminación
- Acceso a datos sensibles (contenido de S3, datos de Redshift)
- Acceso a billing o cost management
- Permisos para crear o modificar IAM roles/policies
- Acceso a otros proyectos fuera del scope

**✅ Este acceso SÍ permite:**
- Ver configuración de recursos existentes
- Validar arquitectura de red
- Revisar políticas y roles (sin modificar)
- Dar soporte técnico durante deployment
- Troubleshooting de errores de configuración

## Beneficios del Documento

### Para el Equipo de Soporte
1. **Solicitud formal y profesional** lista para enviar
2. **Justificación clara** de cada permiso solicitado
3. **Política IAM completa** sin necesidad de crearla desde cero
4. **Comandos listos** para crear el acceso
5. **Validación incluida** para verificar que funciona

### Para el Cliente (Cencosud)
1. **Transparencia total** sobre qué permisos se solicitan y por qué
2. **Múltiples opciones** de métodos de acceso
3. **Garantías de seguridad** explícitas
4. **Duración limitada** del acceso (30 días)
5. **Comandos incluidos** para facilitar la configuración
6. **Validación clara** de qué se puede y no se puede hacer

### Para el Equipo de Seguridad del Cliente
1. **Política IAM revisable** en formato JSON estándar
2. **Solo permisos read-only** sin capacidad de modificar recursos
3. **Justificación técnica** para cada categoría de permisos
4. **Compromiso de revocación** al finalizar el proyecto
5. **Validación de acceso** para verificar que funciona correctamente

## Uso del Documento

### Cuándo Usar Este Documento

Usar este documento cuando:
- El cliente usa su propia Landing Zone existente
- Se necesita validar la configuración de red del cliente
- Se requiere dar soporte técnico durante el deployment
- Se necesita troubleshooting de errores de configuración
- Se quiere validar compliance con políticas corporativas

### Cómo Usar Este Documento

1. **Revisar y personalizar** el documento según necesidades específicas
2. **Completar información de contacto** (email, teléfono)
3. **Enviar al equipo de seguridad** del cliente para aprobación
4. **Esperar aprobación** y creación del acceso
5. **Validar el acceso** usando los comandos proporcionados
6. **Comenzar soporte técnico** con permisos read-only

### Flujo de Trabajo Recomendado

```
1. Cliente decide usar su Landing Zone existente
   ↓
2. Enviar SOLICITUD_PERMISOS_AWS_CLIENTE.md al equipo de seguridad
   ↓
3. Equipo de seguridad revisa y aprueba la política IAM
   ↓
4. Cliente crea el acceso (IAM User, Role o SSO)
   ↓
5. Validar el acceso con comandos proporcionados
   ↓
6. Comenzar validación de Landing Zone
   ↓
7. Dar soporte técnico durante deployment
   ↓
8. Revocar acceso al finalizar el proyecto
```

## Relación con Otros Documentos

### Documentos Complementarios

- **[../GUIA_LANDING_ZONE_CLIENTE.md](../GUIA_LANDING_ZONE_CLIENTE.md)** - Guía para usar Landing Zone existente
- **[Configuración Landing Zone - Resumen.md](Configuración%20Landing%20Zone%20-%20Resumen.md)** - Resumen de la guía
- **[../CONFIGURACION_CLIENTE.md](../CONFIGURACION_CLIENTE.md)** - Configuración requerida del cliente
- **[Configuración del Cliente - Resumen.md](Configuración%20del%20Cliente%20-%20Resumen.md)** - Resumen de configuración
- **[Guía de Validación y Deployment.md](Guía%20de%20Validación%20y%20Deployment.md)** - Validación y deployment

### Flujo de Documentación

```
1. Cliente decide usar Landing Zone existente
   ↓
2. Leer GUIA_LANDING_ZONE_CLIENTE.md
   ↓
3. Enviar SOLICITUD_PERMISOS_AWS_CLIENTE.md (ESTE DOCUMENTO)
   ↓
4. Esperar aprobación y creación de acceso
   ↓
5. Validar acceso con comandos proporcionados
   ↓
6. Comenzar validación de Landing Zone
   ↓
7. Configurar terraform.tfvars según CONFIGURACION_CLIENTE.md
   ↓
8. Deployment según Guía de Validación y Deployment.md
```

## Actualizaciones del Documento

El documento debe actualizarse cuando:
- Se requieran permisos adicionales para nuevos servicios
- Cambien las políticas de seguridad corporativas
- Se modifiquen los métodos de acceso recomendados
- Se agreguen nuevas validaciones o comandos
- Cambien los requisitos de información del cliente

## Notas Técnicas

### Formato del Documento
- **Formato**: Markdown con secciones estructuradas
- **Ubicación**: Raíz del proyecto (`SOLICITUD_PERMISOS_AWS_CLIENTE.md`)
- **Longitud**: ~484 líneas
- **Secciones**: 12 secciones principales + anexos

### Mantenimiento
- Actualizar después de cambios en requisitos de permisos
- Sincronizar con políticas de seguridad del cliente
- Revisar antes de cada nuevo proyecto
- Validar comandos AWS CLI con versiones actuales

### Versionado
- Incluir en control de versiones (Git)
- Documentar cambios en commits
- Mantener historial de versiones
- Referenciar en documentación técnica

## Próximos Pasos

1. **Equipo**: Revisar documento completo en [../SOLICITUD_PERMISOS_AWS_CLIENTE.md](../SOLICITUD_PERMISOS_AWS_CLIENTE.md)
2. **Personalizar**: Completar información de contacto y detalles específicos
3. **Enviar**: Enviar al equipo de seguridad del cliente para aprobación
4. **Validar**: Usar comandos proporcionados para validar el acceso
5. **Soporte**: Comenzar validación y soporte técnico con permisos read-only

---

**Preparado por**: Kiro AI Assistant  
**Fecha**: 3 de Febrero, 2026  
**Versión**: 1.0  
**Estado**: ✅ Documento de solicitud de permisos AWS creado

**Ubicación del Documento**: [../SOLICITUD_PERMISOS_AWS_CLIENTE.md](../SOLICITUD_PERMISOS_AWS_CLIENTE.md)
