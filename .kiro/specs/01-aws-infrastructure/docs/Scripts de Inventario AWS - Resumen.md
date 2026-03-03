# Scripts de Inventario AWS - Resumen

**Fecha**: 16 de Febrero, 2026  
**Documento**: scripts/README-INVENTARIO.md  
**Estado**: ✅ Scripts operacionales y documentados

---

## 🎯 Propósito

Los scripts de inventario AWS permiten generar reportes completos de todos los recursos AWS desplegados en el proyecto Janis-Cencosud, facilitando auditorías, troubleshooting y documentación de la infraestructura.

## 📍 Ubicación

**Directorio**: `scripts/`  
**Documentación**: `scripts/README-INVENTARIO.md`

## 🎯 Script Principal Recomendado

### `inventario-completo.ps1` - Inventario Unificado ⭐

**Este es el script que debes usar.** Genera un inventario completo con recursos, ambientes y análisis detallado de permisos en un solo archivo.

**Propósito**: Proporcionar una herramienta única y simplificada para generar inventarios completos de recursos AWS con clasificación automática por ambiente usando tags oficiales de Cencosud.

**Uso:**
```powershell
.\scripts\inventario-completo.ps1
```

**Características:**
- ✅ Inventario completo de recursos AWS (S3, Lambda, Glue, Redshift, IAM, VPC, etc.)
- ✅ Clasificación automática por ambiente usando tags de Cencosud (dev, qa, test, prod, staging)
- ✅ Análisis detallado de permisos por servicio (Lectura, Escritura, Eliminación)
- ✅ Prueba de permisos en tiempo real para CloudWatch, EventBridge, Kinesis
- ✅ Genera 3 archivos: JSON (datos estructurados) + Markdown (reporte legible) + CSV (para Excel)
- ✅ Completamente portable (funciona en cualquier máquina con AWS CLI)
- ✅ Manejo inteligente de errores y timeouts

**Salida:**
- `inventario-aws-cencosud-YYYYMMDD-HHMMSS.json` - Datos estructurados con permisos
- `inventario-aws-cencosud-YYYYMMDD-HHMMSS.md` - Reporte legible con tablas y análisis
- `inventario-completo-YYYYMMDD-HHMMSS.csv` - Archivo Excel con filtros

**Análisis de Permisos Incluido:**
- **S3**: Listar, Leer, Escribir, Eliminar, Tagging
- **Lambda**: Listar, Leer, Invocar, Actualizar, Eliminar
- **Glue**: Listar, Leer, Escribir, Eliminar (databases y jobs)
- **Redshift**: Listar, Leer, Escribir, Eliminar
- **IAM**: Listar, Leer (solo lectura por seguridad)
- **VPC/EC2**: Listar, Leer configuración de red
- **CloudWatch Logs**: Listar, Leer logs
- **EventBridge**: Listar, Leer reglas
- **Kinesis Firehose**: Listar, Leer delivery streams

**Detección de Ambientes:**
- Prioriza tags oficiales de Cencosud (tag "Environment")
- Fallback a detección por nombre si no hay tags
- Muestra fuente de detección ("via tag" o "via nombre")
- Estadísticas de cobertura de tags al final

**Parámetros:**
- `-Profile`: Perfil de AWS CLI (default: `cencosud`)
- `-Region`: Región AWS (default: `us-east-1`)

---

## 📋 Scripts Adicionales

### 1. inventario-aws-recursos.ps1 - Inventario Detallado (Legacy)

**Propósito**: Genera un inventario exhaustivo de todos los recursos AWS con detalles completos.

**Nota**: Este script es más complejo. Se recomienda usar `inventario-completo.ps1` en su lugar.

**Características**:
- Genera archivo JSON con estructura completa de recursos
- Genera archivo Markdown legible para humanos
- Incluye metadata (perfil, región, timestamp, proyecto)
- Analiza 13+ servicios AWS diferentes

**Uso**:
```powershell
.\inventario-aws-recursos.ps1 -Profile cencosud -Region us-east-1
```

**Parámetros**:
- `-Profile`: Perfil de AWS CLI (default: `cencosud`)
- `-Region`: Región AWS (default: `us-east-1`)
- `-OutputFile`: Nombre del archivo JSON (default: auto-generado con timestamp)
- `-OutputMarkdown`: Nombre del archivo Markdown (default: auto-generado con timestamp)

**Salida**:
- `inventario-aws-cencosud-YYYYMMDD-HHMMSS.json`
- `inventario-aws-cencosud-YYYYMMDD-HHMMSS.md`

**Recursos Analizados**:
- S3 Buckets (con políticas, cifrado, versionado)
- Redshift Clusters (con configuración completa)
- AWS Glue (Databases, Tables, Jobs, Crawlers)
- Lambda Functions (con políticas y configuración)
- API Gateway (REST APIs)
- Kinesis Firehose (Delivery Streams)
- VPC y Subnets
- Security Groups (con reglas ingress/egress)
- IAM Roles (con políticas adjuntas)
- EventBridge Rules
- MWAA (Managed Airflow)
- Secrets Manager
- CloudWatch Log Groups

---

### 2. inventario-rapido.ps1 - Resumen Rápido

**Propósito**: Genera un resumen rápido en consola sin archivos de salida.

**Características**:
- Salida directa en consola con colores y emojis
- Conteo rápido de recursos por servicio
- Ideal para verificaciones rápidas
- No genera archivos

**Uso**:
```powershell
.\inventario-rapido.ps1 -Profile cencosud -Region us-east-1
```

**Parámetros**:
- `-Profile`: Perfil de AWS CLI (default: `cencosud`)
- `-Region`: Región AWS (default: `us-east-1`)

**Salida Ejemplo**:
```
📦 S3 Buckets:
   ✓ janis-cencosud-integration-dev-datalake-bronze
   ✓ janis-cencosud-integration-dev-datalake-silver
   Total: 5

🗄️  Redshift Clusters:
   ✓ cencosud-redshift-prod [available]
   Total: 1
```

---

### 3. inventario-permisos.ps1 - Análisis de Permisos

**Propósito**: Analiza en detalle todos los permisos IAM, políticas y configuraciones de seguridad.

**Características**:
- Análisis detallado de IAM Roles con políticas administradas e inline
- Trust Policies (AssumeRole)
- S3 Bucket Policies y ACLs
- Lambda Resource-based Policies
- Security Groups (reglas Ingress/Egress)
- Public Access Block configurations
- Recomendaciones de seguridad

**Uso**:
```powershell
.\inventario-permisos.ps1 -Profile cencosud -Region us-east-1
```

**Parámetros**:
- `-Profile`: Perfil de AWS CLI (default: `cencosud`)
- `-Region`: Región AWS (default: `us-east-1`)
- `-OutputFile`: Nombre del archivo Markdown (default: auto-generado con timestamp)

**Salida**:
- `permisos-aws-cencosud-YYYYMMDD-HHMMSS.md`

**Análisis Incluido**:
1. **IAM Roles del Proyecto**
   - ARN y fecha de creación
   - Trust Policy (AssumeRole) en JSON
   - Políticas Administradas Adjuntas con permisos completos
   - Políticas Inline con documento completo

2. **Políticas de S3 Buckets**
   - Bucket Policy en JSON
   - Access Control List (ACL)
   - Public Access Block configuration

3. **Políticas de Lambda Functions**
   - Role de ejecución
   - Resource-based Policy

4. **Security Groups**
   - Reglas de Entrada (Ingress) en tabla
   - Reglas de Salida (Egress) en tabla

5. **Resumen de Permisos por Servicio**
   - Servicios con acceso configurado
   - Recomendaciones de seguridad (6 puntos)

---

## 📊 Estructura de Salida

### Inventario JSON

```json
{
  "metadata": {
    "profile": "cencosud",
    "region": "us-east-1",
    "timestamp": "2026-02-16T...",
    "project": "janis-cencosud"
  },
  "resources": {
    "s3": [
      {
        "name": "janis-cencosud-integration-dev-datalake-bronze",
        "creationDate": "2026-02-04T...",
        "policy": { /* JSON policy */ }
      }
    ],
    "redshift": [ /* ... */ ],
    "lambda": [ /* ... */ ],
    // ... más servicios
  }
}
```

### Inventario Markdown

```markdown
# Inventario de Recursos AWS - Proyecto Janis-Cencosud

**Perfil AWS:** cencosud
**Región:** us-east-1
**Fecha:** 2026-02-16 10:30:00

## Resumen Ejecutivo

| Servicio | Cantidad |
|----------|----------|
| S3 Buckets | 5 |
| Redshift Clusters | 1 |
| Lambda Functions | 3 |
...

## S3 Buckets

### janis-cencosud-integration-dev-datalake-bronze
- **Fecha de creación:** 2026-02-04T...
- **Política:** Configurada
- **Cifrado:** Habilitado
...
```

### Análisis de Permisos Markdown

```markdown
# Análisis de Permisos IAM - Proyecto Janis-Cencosud

## IAM Roles del Proyecto

### janis-cencosud-integration-dev-lambda-execution-role

- **ARN:** arn:aws:iam::827739413930:role/...
- **Trust Policy (AssumeRole):**
```json
{
  "Version": "2012-10-17",
  "Statement": [ /* ... */ ]
}
```

#### Políticas Administradas Adjuntas
- **AWSLambdaVPCAccessExecutionRole**
  - Permisos: ...
...
```

---

## 🔧 Requisitos Previos

### 1. AWS CLI Instalado

```powershell
# Verificar instalación
aws --version
```

Si no está instalado: https://aws.amazon.com/cli/

### 2. Perfil AWS Configurado

```powershell
# Verificar perfiles
aws configure list-profiles

# Debería mostrar "cencosud"
```

### 3. Credenciales Válidas

```powershell
# Verificar que funciona
aws sts get-caller-identity --profile cencosud
```

---

## 💡 Casos de Uso

### Caso 1: Auditoría de Infraestructura

**Objetivo**: Generar reporte completo para auditoría de seguridad

**Comandos**:
```powershell
# Inventario completo
.\inventario-aws-recursos.ps1 -Profile cencosud -OutputFile "auditoria-$(Get-Date -Format 'yyyyMMdd').json"

# Análisis de permisos
.\inventario-permisos.ps1 -Profile cencosud -OutputFile "permisos-auditoria-$(Get-Date -Format 'yyyyMMdd').md"
```

**Resultado**: Archivos JSON y Markdown con toda la información para auditoría.

---

### Caso 2: Troubleshooting Rápido

**Objetivo**: Verificar rápidamente qué recursos existen

**Comando**:
```powershell
.\inventario-rapido.ps1
```

**Resultado**: Resumen en consola en segundos.

---

### Caso 3: Documentación de Deployment

**Objetivo**: Documentar recursos creados después de deployment

**Comandos**:
```powershell
# Antes del deployment
.\inventario-aws-recursos.ps1 -OutputFile "pre-deployment.json"

# Después del deployment
.\inventario-aws-recursos.ps1 -OutputFile "post-deployment.json"

# Comparar archivos para ver qué se creó
```

---

### Caso 4: Validación de Permisos

**Objetivo**: Verificar que los permisos IAM son correctos

**Comando**:
```powershell
.\inventario-permisos.ps1 -OutputFile "validacion-permisos.md"
```

**Resultado**: Documento Markdown con análisis completo de permisos y recomendaciones.

---

## 🚨 Troubleshooting

### Error: "Unable to locate credentials"

**Causa**: Credenciales AWS no configuradas

**Solución**:
```powershell
aws configure --profile cencosud
```

---

### Error: "Access Denied" en algunos recursos

**Causa**: El usuario/rol no tiene permisos para listar ese recurso

**Solución**: Esto es normal. El script continuará con los recursos accesibles.

---

### Error: "Invalid profile"

**Causa**: El perfil especificado no existe

**Solución**:
```powershell
# Listar perfiles disponibles
aws configure list-profiles

# Usar el perfil correcto
.\inventario-aws-recursos.ps1 -Profile <nombre-perfil-correcto>
```

---

### Script muy lento

**Causa**: Muchos recursos o latencia de red

**Solución**: Usa `inventario-rapido.ps1` para verificaciones rápidas.

---

## 🔒 Seguridad

### ⚠️ IMPORTANTE

Los archivos generados contienen información sensible de infraestructura:

- ❌ **NO commitear** estos archivos a Git
- ❌ **NO compartir** públicamente
- ✅ **Almacenar** en ubicación segura
- ✅ **Compartir** solo con personal autorizado
- ✅ Los archivos están en `.gitignore` por defecto

### Información Sensible Incluida

- ARNs de recursos AWS
- IDs de Security Groups
- Configuraciones de red (CIDRs, IPs)
- Políticas IAM completas
- Nombres de buckets S3
- Endpoints de servicios

---

## 🤖 Automatización

### Ejecutar Inventario Diario

Crear tarea programada en Windows Task Scheduler:

```powershell
# Script wrapper
$scriptPath = "C:\ruta\a\scripts\inventario-aws-recursos.ps1"
$logPath = "C:\ruta\a\logs\inventario-$(Get-Date -Format 'yyyyMMdd').log"

& $scriptPath -Profile cencosud | Tee-Object -FilePath $logPath
```

Programar para ejecutar diariamente a las 2:00 AM.

---

## 📈 Beneficios

### Para DevOps
- ✅ Auditoría rápida de infraestructura
- ✅ Troubleshooting eficiente
- ✅ Documentación automática
- ✅ Validación de deployments

### Para Seguridad
- ✅ Análisis completo de permisos IAM
- ✅ Identificación de configuraciones inseguras
- ✅ Recomendaciones de seguridad
- ✅ Auditoría de accesos

### Para Compliance
- ✅ Reportes detallados para auditorías
- ✅ Historial de cambios en infraestructura
- ✅ Documentación de configuraciones
- ✅ Evidencia de compliance

---

## 🔗 Relación con Otros Documentos

### Documentos Relacionados

- **[../README.md](../README.md)** - Documentación principal del proyecto
- **[README.md](README.md)** - Índice de documentación Cenco
- **[../terraform/README.md](../terraform/README.md)** - Documentación de Terraform
- **[../INVENTARIO_Y_PERMISOS_AWS.md](../INVENTARIO_Y_PERMISOS_AWS.md)** - Inventario consolidado y análisis de permisos
- **[../AWS_INFRASTRUCTURE_VALIDATION_REPORT.md](../AWS_INFRASTRUCTURE_VALIDATION_REPORT.md)** - Reporte de validación

### Flujo de Trabajo

1. **Deployment** → Desplegar infraestructura con Terraform
2. **Inventario** → Ejecutar scripts de inventario
3. **Validación** → Comparar con especificaciones
4. **Documentación** → Guardar reportes para referencia

### Documento Consolidado

El archivo **[INVENTARIO_Y_PERMISOS_AWS.md](../INVENTARIO_Y_PERMISOS_AWS.md)** proporciona:
- Inventario completo de recursos AWS en la cuenta de Cencosud
- Análisis detallado de permisos efectivos del rol CencoDataEngineer
- Matriz de permisos por servicio (Listar, Leer, Escribir, Eliminar, Ejecutar)
- Recomendaciones de seguridad y mejores prácticas
- Referencias a los scripts de inventario disponibles

---

## 📊 Métricas

- **Scripts disponibles**: 3
- **Servicios AWS analizados**: 13+
- **Formatos de salida**: JSON, Markdown, Consola
- **Tiempo de ejecución**: 1-5 minutos (según cantidad de recursos)
- **Líneas de código**: ~1,200 (total de los 3 scripts)

---

## 🎉 Conclusión

Los scripts de inventario AWS proporcionan una herramienta poderosa para:

- Auditar infraestructura desplegada
- Troubleshooting rápido
- Documentación automática
- Validación de permisos
- Compliance y seguridad

**Estado**: ✅ Scripts operacionales y documentados  
**Próxima revisión**: Según necesidades del proyecto  
**Mantenimiento**: Actualizar según nuevos servicios AWS

---

**Preparado por**: Kiro AI Assistant  
**Fecha**: 16 de Febrero, 2026  
**Versión**: 1.0  
**Estado**: ✅ Documentación completa

