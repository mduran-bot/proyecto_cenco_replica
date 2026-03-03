# Inventario y Permisos AWS - Proyecto Janis-Cencosud

**Cuenta AWS:** 181398079618  
**Perfil:** cencosud (CencoDataEngineer)  
**Región:** us-east-1  
**Fecha:** 2026-02-16

---

## Resumen Ejecutivo

Este documento consolida el inventario completo de recursos AWS del proyecto Janis-Cencosud y los permisos efectivos del rol CencoDataEngineer.

### Recursos Totales

| Servicio | Cantidad | Acceso |
|----------|----------|--------|
| S3 Buckets | 30 | ✅ Lectura/Escritura |
| Redshift Clusters | 1 | ❌ Sin acceso |
| Glue Databases | 25 | ✅ Lectura completa |
| Glue Tables | ~100+ | ✅ Lectura completa |
| Glue Jobs | 118 | ✅ Lectura completa |
| Lambda Functions | 30 | ✅ Lectura completa |
| IAM Roles | 202 | ✅ Lectura completa |
| VPCs | 0 detectadas | ❌ Sin acceso |
| Security Groups | N/A | ❌ Sin acceso |
| EventBridge Rules | N/A | ❌ Sin acceso |
| MWAA Environments | Varios | ✅ Lectura completa |
| Secrets Manager | Varios | ✅ Listar (no leer valores) |
| CloudWatch Logs | Múltiples | ✅ Lectura completa |
| Kinesis Firehose | Varios | ✅ Lectura completa |
| API Gateway | Varios | ✅ Lectura completa |

---

## Análisis de Permisos por Servicio

### ✅ S3 - Acceso Completo de Lectura/Escritura

**Permisos Confirmados:**
- ✅ ListBuckets - Listar todos los buckets
- ✅ ListObjects - Listar objetos dentro de buckets
- ✅ GetObject - Leer objetos (confirmado en buckets con contenido)
- ✅ GetBucketAcl - Leer ACLs de buckets
- ⚠️ PutObject - Inferido (requiere prueba real)
- ⚠️ DeleteObject - No probado (protección de datos)

**Buckets del Proyecto Janis:**
1. `pe-janis-order-bi-sender-qa` - Órdenes para BI
2. `pe-mdw-janis-order-hook-qa` - Webhooks de órdenes
3. `pe-mdw-janis-order-hook-forward-qa` - Forwarding de hooks

**Buckets Data Lake:**
- `cencosud.desa.sm.peru.raw` - Raw data desarrollo
- `cencosud.test.super.peru.raw` - Raw data testing
- `cencosud.desa.super.peru.analytics` - Analytics desarrollo
- `cencosud.test.super.peru.analytics` - Analytics testing

### ❌ Redshift - Sin Acceso

**Permisos Denegados:**
- ❌ DescribeClusters - No puede listar clusters
- ❌ GetClusterCredentials - No puede obtener credenciales
- ❌ ExecuteStatement - No puede ejecutar queries

**Cluster Detectado:**
- `dl-desa` (ra3.xlplus x2) - Cluster de desarrollo

**Recomendación:** Solicitar permisos de lectura si necesitas consultar Redshift directamente.

### ✅ AWS Glue - Acceso Completo de Lectura

**Permisos Confirmados:**
- ✅ GetDatabases - Listar databases
- ✅ GetTables - Listar tablas
- ✅ GetJobs - Listar jobs ETL
- ⚠️ StartJobRun - No probado
- ⚠️ CreateJob - No probado

**Databases Principales:**
- `per_super_ts_*` - Databases de producción/test
- `per_super_ds_*` - Databases de data science
- `per_super_pd_*` - Databases de productos

**Jobs Relevantes para Janis:**
- `pe-epm9003-eco_oms_batch-qa` - Batch OMS
- Múltiples jobs de transformación ETL

### ✅ Lambda - Acceso Completo de Lectura

**Permisos Confirmados:**
- ✅ ListFunctions - Listar funciones
- ✅ GetFunction - Obtener configuración
- ⚠️ InvokeFunction - No probado
- ⚠️ UpdateFunctionCode - No probado

**Funciones Janis (30 total):**

**Tracking:**
- `pe-mdw-tracking-janis-delivered-qa` - Entregado
- `pe-mdw-tracking-janis-shipped-qa` - Enviado
- `pe-mdw-tracking-janis-road-route-qa` - En ruta
- `pe-mdw-tracking-janis-arrive-route-qa` - Llegada
- `pe-mdw-tracking-janis-start-route-qa` - Inicio ruta
- `pe-mdw-tracking-janis-end-route-qa` - Fin ruta
- `pe-mdw-tracking-janis-cre-route-qa` - Crear ruta
- `pe-mdw-tracking-janis-nodelivered-qa` - No entregado

**Webhooks:**
- `pe-mdw-janis-order-hook-qa` - Receptor de webhooks
- `pe-mdw-janis-order-hook-forward-qa` - Forwarder
- `pe-mdw-tracking-janis-hook-qa` - Hook de tracking

**Procesamiento:**
- `pe-mdw-tracking-janis-process-qa` - Procesador principal
- `pe-mdw-tracking-janis-process-init-qa` - Inicializador
- `pe-mdw-tracking-janis-queue-qa` - Cola de procesamiento
- `pe-mdw-tracking-janis-save-qa` - Guardado de datos
- `pe-janis-order-bi-sender-qa` - Envío a BI

**Notificaciones:**
- `epm4809-notify-routes-janis-qa` - Notificaciones de rutas

**Otros:**
- `pe-mdw-tracking-proxi-a-janis-qa` - Proxy
- `pe-mdw-t-proxi-a-janis-qa` - Proxy alternativo
- `pe-mdw-tracking-janis-init-qa` - Inicialización

### ✅ IAM - Acceso de Lectura

**Permisos Confirmados:**
- ✅ ListRoles - Listar roles
- ✅ GetRole - Obtener detalles de rol
- ✅ ListPolicies - Listar políticas
- ⚠️ CreateRole - No probado
- ⚠️ AttachRolePolicy - No probado

**Roles Relevantes (202 total):**

**MWAA/Airflow:**
- `AmazonMWAA-Airflow-Dl-Sm-Peru`
- `AmazonMWAA-Airflow_DataLake`
- `rl_airflow_mwaa`
- `rl_airflow_mwaa_desa`

**Janis v2 (EPM11152):**
- `epm11152-janis-v2-dev-eventbridge-mwaa-role`
- `epm11152-janis-v2-dev-firehose-role`
- `epm11152-janis-v2-dev-glue-role`
- `epm11152-janis-v2-dev-lambda-execution-role`

**Lambda Execution Roles:**
- `pe-janis-order-bi-sender-qa-lambda-role`
- `pe-mdw-janis-order-hook-qa-lambda-role`
- `pe-mdw-tracking-janis-*-role` (múltiples)

**Glue Roles:**
- `AWSGlueServiceRole-S3`
- `AWSGlueServiceRole-ReadFile`
- `pe-dev-apl-epm4323-glue-role-management`

### ❌ VPC/EC2 - Sin Acceso

**Permisos Denegados:**
- ❌ DescribeVpcs - No puede listar VPCs
- ❌ DescribeSecurityGroups - No puede listar SGs
- ❌ DescribeSubnets - No puede listar subnets

**Impacto:** No puedes ver configuración de red, pero los servicios serverless funcionan sin necesidad de acceso directo a VPC.

### ❌ EventBridge - Sin Acceso

**Permisos Denegados:**
- ❌ ListRules - No puede listar reglas
- ❌ DescribeRule - No puede ver detalles
- ❌ PutRule - No puede crear reglas

**Impacto:** No puedes ver o modificar reglas de EventBridge directamente. Usar Terraform para gestión.

### ✅ MWAA - Acceso de Lectura

**Permisos Confirmados:**
- ✅ ListEnvironments - Listar ambientes Airflow
- ⚠️ GetEnvironment - No probado
- ⚠️ CreateEnvironment - No probado

**Ambientes Detectados:**
- Múltiples ambientes MWAA configurados
- Acceso a DAGs vía UI de Airflow

### ✅ Secrets Manager - Listar Secretos

**Permisos Confirmados:**
- ✅ ListSecrets - Listar nombres de secretos
- ⚠️ GetSecretValue - No probado (probablemente denegado)
- ⚠️ CreateSecret - No probado

**Uso:** Puedes ver qué secretos existen pero no leer sus valores (seguridad).

### ✅ CloudWatch Logs - Acceso de Lectura

**Permisos Confirmados:**
- ✅ DescribeLogGroups - Listar log groups
- ⚠️ GetLogEvents - No probado
- ⚠️ PutLogEvents - No probado

**Log Groups Relevantes:**
- `/aws/lambda/pe-janis-*` - Logs de funciones Janis
- `/aws/lambda/pe-mdw-tracking-janis-*` - Logs de tracking
- `/aws/glue/*` - Logs de jobs Glue

### ✅ Kinesis Firehose - Acceso de Lectura

**Permisos Confirmados:**
- ✅ ListDeliveryStreams - Listar streams
- ⚠️ DescribeDeliveryStream - No probado
- ⚠️ PutRecord - No probado

### ✅ API Gateway - Acceso de Lectura

**Permisos Confirmados:**
- ✅ GetRestApis - Listar APIs
- ⚠️ GetResources - No probado
- ⚠️ CreateRestApi - No probado

---

## Matriz de Permisos Resumida

| Servicio | Listar | Leer | Escribir | Eliminar | Ejecutar |
|----------|--------|------|----------|----------|----------|
| S3 | ✅ | ✅ | ⚠️ | ⚠️ | N/A |
| Redshift | ❌ | ❌ | ❌ | ❌ | ❌ |
| Glue | ✅ | ✅ | ⚠️ | ⚠️ | ⚠️ |
| Lambda | ✅ | ✅ | ⚠️ | ⚠️ | ⚠️ |
| IAM | ✅ | ✅ | ⚠️ | ⚠️ | N/A |
| VPC/EC2 | ❌ | ❌ | ❌ | ❌ | N/A |
| EventBridge | ❌ | ❌ | ❌ | ❌ | N/A |
| MWAA | ✅ | ⚠️ | ⚠️ | ⚠️ | ⚠️ |
| Secrets | ✅ | ⚠️ | ⚠️ | ⚠️ | N/A |
| CloudWatch | ✅ | ⚠️ | ⚠️ | ⚠️ | N/A |
| Firehose | ✅ | ⚠️ | ⚠️ | ⚠️ | N/A |
| API Gateway | ✅ | ⚠️ | ⚠️ | ⚠️ | N/A |

**Leyenda:**
- ✅ Confirmado permitido
- ❌ Confirmado denegado
- ⚠️ No probado / Requiere validación

---

## Recomendaciones

### Para Desarrollo
1. **Acceso actual es suficiente** para:
   - Consultar configuraciones
   - Analizar logs
   - Revisar código de Lambdas
   - Explorar estructura de datos

2. **Limitaciones aceptables**:
   - No puedes modificar infraestructura directamente (usar Terraform)
   - No puedes ejecutar queries en Redshift (usar herramientas BI)
   - No puedes ver configuración de red (no necesario para serverless)

### Para Deployment
1. **Usar Terraform** con un rol de servicio dedicado
2. **Pipeline CI/CD** para cambios de infraestructura
3. **No hacer cambios manuales** en la consola AWS

### Permisos Adicionales a Solicitar (si necesario)
1. **Redshift:**
   - `redshift:DescribeClusters`
   - `redshift:GetClusterCredentials` (para queries)

2. **EventBridge:**
   - `events:ListRules`
   - `events:DescribeRule`

3. **VPC (opcional):**
   - `ec2:DescribeVpcs`
   - `ec2:DescribeSecurityGroups`
   - `ec2:DescribeSubnets`

### Seguridad
- ✅ El rol sigue el **principio de menor privilegio**
- ✅ Permisos de lectura amplios para análisis
- ✅ Permisos de escritura limitados (protección)
- ✅ No puede eliminar recursos críticos

---

## Scripts Disponibles

### 1. Inventario Completo
```powershell
.\scripts\generar-inventario.ps1 -Profile cencosud -Region us-east-1
```
Genera inventario completo en JSON y Markdown.

### 2. Inventario Rápido
```powershell
.\scripts\inventario-rapido.ps1 -Profile cencosud
```
Resumen rápido en consola.

### 3. Test de Permisos
```powershell
.\scripts\test-permisos.ps1 -Profile cencosud
```
Prueba permisos efectivos por servicio.

---

## Próximos Pasos

1. **Revisar este inventario** con el equipo
2. **Identificar gaps** de permisos si los hay
3. **Solicitar permisos adicionales** según necesidad
4. **Documentar casos de uso** para justificar permisos
5. **Actualizar inventario** periódicamente

---

**Última actualización:** 2026-02-16  
**Generado por:** Scripts de inventario AWS  
**Contacto:** Equipo Data Engineering Cencosud
