# Scripts - Proyecto Janis-Cencosud

Este directorio contiene scripts de utilidad para el proyecto Janis-Cencosud, incluyendo inventarios de AWS y herramientas de análisis de datos.

## Categorías de Scripts

### 📊 Análisis de Datos
- `analyze_parquet_schemas.py` - Análisis de esquemas de archivos Parquet

### 🔍 Inventario AWS
- Scripts PowerShell para generar inventarios completos de recursos AWS

---

## 📊 Scripts de Análisis de Datos

### `analyze_parquet_schemas.py` - Análisis de Esquemas Parquet

Herramienta Python para analizar archivos Parquet y validar su estructura, esquema y calidad de datos.

**Uso:**
```bash
python scripts/analyze_parquet_schemas.py
```

**Características:**
- ✅ Análisis detallado de esquemas Arrow/Parquet
- ✅ Validación de tipos de datos y nullability
- ✅ Estadísticas descriptivas completas
- ✅ Identificación de valores nulos por columna
- ✅ Generación de resumen JSON estructurado
- ✅ Vista de primeras filas de datos

**Documentación Completa:**
Ver [Herramienta Análisis Parquet - Guía de Uso](../.kiro/specs/02-initial-data-load/docs/Herramienta%20Análisis%20Parquet%20-%20Guía%20de%20Uso.md)

**Casos de Uso:**
- Validar archivos Parquet generados por Glue jobs
- Verificar compatibilidad de esquemas con Redshift
- Comparar esquemas entre ambientes (dev/staging/prod)
- Identificar problemas de calidad de datos
- Documentar estructura de archivos existentes

---

## 🔍 Scripts de Inventario AWS

Este directorio contiene scripts PowerShell para generar inventarios completos de los recursos AWS del proyecto Janis-Cencosud.

## 🎯 Script Principal Recomendado

### `inventario-completo.ps1` - Inventario Unificado ⭐
**Este es el script que debes usar.** Genera un inventario completo con recursos, ambientes y análisis detallado de permisos en un solo archivo.

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

---

## Scripts Adicionales

### 1. `generar-inventario.ps1` - Inventario Base
Versión simplificada del inventario (usa `inventario-completo.ps1` en su lugar).

**Uso:**
```powershell
.\inventario-aws-recursos.ps1 -Profile cencosud -Region us-east-1
```

**Parámetros:**
- `-Profile`: Perfil de AWS CLI a usar (default: `cencosud`)
- `-Region`: Región de AWS (default: `us-east-1`)
- `-OutputFile`: Nombre del archivo JSON de salida (default: auto-generado con timestamp)
- `-OutputMarkdown`: Nombre del archivo Markdown de salida (default: auto-generado con timestamp)

**Salida:**
- Archivo JSON con todos los detalles de recursos
- Archivo Markdown con reporte legible

**Recursos analizados:**
- S3 Buckets
- Redshift Clusters
- AWS Glue (Databases, Tables, Jobs, Crawlers)
- Lambda Functions
- API Gateway
- Kinesis Firehose
- VPC y Subnets
- Security Groups
- IAM Roles
- EventBridge Rules
- MWAA (Managed Airflow)
- Secrets Manager
- CloudWatch Log Groups

---

### 2. `inventario-rapido.ps1` - Resumen Rápido
Genera un resumen rápido en consola sin archivos de salida.

**Uso:**
```powershell
.\inventario-rapido.ps1 -Profile cencosud -Region us-east-1
```

**Parámetros:**
- `-Profile`: Perfil de AWS CLI a usar (default: `cencosud`)
- `-Region`: Región de AWS (default: `us-east-1`)

**Salida:**
- Resumen en consola con emojis y colores
- Conteo rápido de recursos por servicio
- Ideal para verificaciones rápidas

---

### 3. `inventario-permisos.ps1` - Análisis de Permisos
Analiza en detalle todos los permisos IAM, políticas y configuraciones de seguridad.

**Uso:**
```powershell
.\inventario-permisos.ps1 -Profile cencosud -Region us-east-1
```

**Parámetros:**
- `-Profile`: Perfil de AWS CLI a usar (default: `cencosud`)
- `-Region`: Región de AWS (default: `us-east-1`)
- `-OutputFile`: Nombre del archivo Markdown de salida (default: auto-generado con timestamp)

**Salida:**
- Archivo Markdown con análisis detallado de permisos

**Análisis incluido:**
- IAM Roles con políticas administradas e inline
- Trust Policies (AssumeRole)
- S3 Bucket Policies y ACLs
- Lambda Resource-based Policies
- Security Groups (Ingress/Egress rules)
- Public Access Block configurations
- Recomendaciones de seguridad

---

## Requisitos Previos

### 1. AWS CLI Instalado
```powershell
# Verificar instalación
aws --version
```

Si no está instalado, descarga desde: https://aws.amazon.com/cli/

### 2. Perfil AWS Configurado
```powershell
# Verificar perfiles configurados
aws configure list-profiles

# Debería mostrar "cencosud" en la lista
```

### 3. Credenciales Válidas
```powershell
# Verificar que el perfil funciona
aws sts get-caller-identity --profile cencosud
```

Debería retornar información de tu cuenta AWS.

---

## Ejemplos de Uso

### Inventario Completo con Nombres Personalizados
```powershell
.\inventario-aws-recursos.ps1 `
    -Profile cencosud `
    -Region us-east-1 `
    -OutputFile "inventario-produccion.json" `
    -OutputMarkdown "inventario-produccion.md"
```

### Resumen Rápido para Verificación
```powershell
# Ejecutar y ver resultados en consola
.\inventario-rapido.ps1
```

### Análisis de Permisos para Auditoría
```powershell
.\inventario-permisos.ps1 `
    -Profile cencosud `
    -OutputFile "auditoria-permisos-$(Get-Date -Format 'yyyyMMdd').md"
```

---

## Interpretación de Resultados

### Inventario Completo (JSON)
El archivo JSON contiene:
```json
{
  "metadata": {
    "profile": "cencosud",
    "region": "us-east-1",
    "timestamp": "2026-02-16T...",
    "project": "janis-cencosud"
  },
  "resources": {
    "s3": [...],
    "redshift": [...],
    "lambda": [...],
    ...
  }
}
```

### Inventario Markdown
Documento legible con:
- Tabla resumen de recursos
- Detalles por servicio
- Configuraciones importantes

### Análisis de Permisos
Documento con:
- Roles IAM y sus políticas
- Permisos efectivos por recurso
- Configuraciones de seguridad
- Recomendaciones

---

## Troubleshooting

### Error: "Unable to locate credentials"
**Solución:**
```powershell
# Configurar credenciales
aws configure --profile cencosud
```

### Error: "Access Denied" en algunos recursos
**Causa:** El usuario/rol no tiene permisos para listar ese recurso.

**Solución:** Esto es normal. El script continuará con los recursos accesibles.

### Error: "Invalid profile"
**Solución:**
```powershell
# Listar perfiles disponibles
aws configure list-profiles

# Usar el perfil correcto
.\inventario-aws-recursos.ps1 -Profile <nombre-perfil-correcto>
```

### Script muy lento
**Causa:** Muchos recursos o latencia de red.

**Solución:** Usa `inventario-rapido.ps1` para verificaciones rápidas.

---

## Automatización

### Ejecutar Inventario Diario
Crear tarea programada en Windows:

```powershell
# Crear script wrapper
$scriptPath = "C:\ruta\a\scripts\inventario-aws-recursos.ps1"
$logPath = "C:\ruta\a\logs\inventario-$(Get-Date -Format 'yyyyMMdd').log"

& $scriptPath -Profile cencosud | Tee-Object -FilePath $logPath
```

Programar en Task Scheduler para ejecutar diariamente.

---

## Seguridad

⚠️ **IMPORTANTE:**
- Los archivos generados contienen información sensible de infraestructura
- NO commitear estos archivos a Git
- Almacenar en ubicación segura
- Compartir solo con personal autorizado
- Los archivos están en `.gitignore` por defecto

---

## Soporte

Para problemas o mejoras, contactar al equipo de DevOps del proyecto Janis-Cencosud.

---

## Changelog

### 2026-02-16
- ✅ Creación inicial de scripts de inventario
- ✅ Soporte para todos los servicios principales del proyecto
- ✅ Análisis detallado de permisos IAM
- ✅ Generación de reportes en JSON y Markdown
