# Recomendaciones para Recepción y Procesamiento de Archivos SQL

**Fecha**: 19 de febrero de 2026  
**Contexto**: Cencosud tiene los archivos .sql comprimidos para la carga inicial de datos históricos desde MySQL Janis

---

## 1. Método de Transferencia Recomendado

### Opción A: Transferencia Directa a S3 (RECOMENDADA)

**Por qué es la mejor opción:**
- Evita transferencias intermedias innecesarias
- Los datos quedan directamente en AWS donde se procesarán
- Más seguro (cifrado en tránsito y en reposo)
- Más rápido para archivos grandes
- Cumple con las políticas de seguridad corporativa

**Proceso:**
1. Crear un bucket S3 temporal para recepción: `janis-cencosud-initial-load-staging-prod`
2. Generar credenciales temporales (STS) con permisos limitados solo para subir a ese bucket
3. Proporcionar a Cencosud:
   - Credenciales temporales (válidas por 12-24 horas)
   - Comando AWS CLI para subir archivos
   - O URL pre-firmada para subida vía navegador

**Comando para Cencosud:**
```bash
# Opción 1: AWS CLI (si tienen instalado)
aws s3 cp archivo_comprimido.sql.gz s3://janis-cencosud-initial-load-staging-prod/raw/ \
  --region us-east-1 \
  --sse aws:kms \
  --sse-kms-key-id alias/janis-cencosud-kms

# Opción 2: Subida multipart para archivos grandes (>5GB)
aws s3 cp archivo_comprimido.sql.gz s3://janis-cencosud-initial-load-staging-prod/raw/ \
  --region us-east-1 \
  --sse aws:kms \
  --sse-kms-key-id alias/janis-cencosud-kms \
  --storage-class STANDARD_IA
```

### Opción B: Transferencia Segura vía SFTP/SCP

**Cuándo usar:**
- Si Cencosud no puede usar AWS CLI
- Si prefieren un método más tradicional

**Proceso:**
1. Configurar AWS Transfer Family (SFTP) apuntando al bucket S3
2. Crear usuario temporal con credenciales SSH
3. Proporcionar hostname, usuario y clave SSH
4. Cencosud sube archivos vía SFTP cliente (FileZilla, WinSCP, etc.)

### Opción C: URL Pre-firmada (Para archivos pequeños <5GB)

**Cuándo usar:**
- Archivos relativamente pequeños
- Cencosud no tiene AWS CLI ni cliente SFTP
- Necesitan método simple vía navegador

**Proceso:**
```python
# Generar URL pre-firmada válida por 24 horas
import boto3
from datetime import timedelta

s3_client = boto3.client('s3')
url = s3_client.generate_presigned_url(
    'put_object',
    Params={
        'Bucket': 'janis-cencosud-initial-load-staging-prod',
        'Key': 'raw/mysql_dump.sql.gz'
    },
    ExpiresIn=86400  # 24 horas
)
```

---

## 2. Formato y Compresión Recomendados

### Formato Preferido

**Opción 1: SQL Dump Comprimido (RECOMENDADO)**
- Formato: `.sql.gz` o `.sql.bz2`
- Compresión: gzip o bzip2
- Ventajas: Estándar, fácil de procesar, buena compresión

**Opción 2: SQL Dump por Tabla**
- Formato: Múltiples archivos `tabla_nombre.sql.gz`
- Ventajas: Procesamiento paralelo más fácil, mejor para debugging
- Desventajas: Más archivos que gestionar

### Estructura Esperada del SQL Dump

```sql
-- Esperamos dumps con esta estructura:
CREATE TABLE IF NOT EXISTS `orders` (...);
INSERT INTO `orders` VALUES (...);
INSERT INTO `orders` VALUES (...);

CREATE TABLE IF NOT EXISTS `products` (...);
INSERT INTO `products` VALUES (...);
```

**Importante:** Solicitar a Cencosud que incluyan:
- `CREATE TABLE` statements (para validar esquema)
- `INSERT` statements con datos
- Sin `DROP TABLE` (por seguridad)
- Con `--single-transaction` si fue generado con mysqldump
- Con `--extended-insert` para mejor performance

---

## 3. Qué Hacer con los Archivos SQL

### Fase 1: Recepción y Validación (Inmediata)

**Ubicación en S3:**
```
s3://janis-cencosud-initial-load-staging-prod/
├── raw/                          # Archivos originales comprimidos
│   ├── mysql_dump.sql.gz
│   └── metadata.json             # Info sobre el dump
├── extracted/                    # Archivos descomprimidos
│   └── mysql_dump.sql
└── validation/                   # Reportes de validación
    └── validation_report.json
```

**Acciones:**
1. **Validar integridad del archivo**
   ```bash
   # Verificar que no está corrupto
   gunzip -t mysql_dump.sql.gz
   
   # Calcular checksum
   md5sum mysql_dump.sql.gz
   ```

2. **Extraer metadata**
   ```python
   # Script para extraer info del dump
   - Número de tablas
   - Tamaño descomprimido estimado
   - Versión de MySQL
   - Fecha de generación
   ```

3. **Validación básica de contenido**
   ```bash
   # Verificar que contiene las 25 tablas esperadas
   zcat mysql_dump.sql.gz | grep "CREATE TABLE" | wc -l
   
   # Listar tablas encontradas
   zcat mysql_dump.sql.gz | grep "CREATE TABLE" | sed 's/.*`\(.*\)`.*/\1/'
   ```

### Fase 2: Carga a Base de Datos Temporal (Recomendado)

**Por qué cargar a BD temporal:**
- Permite validación completa de datos
- Facilita transformaciones y limpieza
- Permite usar el proceso de extracción diseñado en el spec
- Más control sobre el proceso

**Opciones de BD Temporal:**

**Opción A: RDS MySQL Temporal (RECOMENDADA)**
```
Configuración:
- Instancia: db.r6g.xlarge (4 vCPU, 32 GB RAM)
- Storage: 500 GB gp3 (auto-scaling habilitado)
- Duración: 1 semana (eliminar después de migración exitosa)
- Costo estimado: ~$200 para toda la migración
- VPC: Misma VPC que Glue jobs para acceso directo
```

**Proceso:**
1. Crear RDS MySQL temporal
2. Restaurar dump SQL:
   ```bash
   # Descomprimir y cargar
   gunzip -c mysql_dump.sql.gz | mysql -h rds-endpoint -u admin -p janis_temp
   ```
3. Ejecutar validaciones del spec (Requirement 2)
4. Ejecutar proceso de extracción diseñado (Glue job)
5. Eliminar RDS temporal después de validación exitosa

**Opción B: Aurora Serverless v2 (Alternativa)**
```
Ventajas:
- Auto-scaling automático
- Pago por uso (más económico si el proceso es rápido)
- Mejor performance para cargas grandes

Configuración:
- Min capacity: 0.5 ACU
- Max capacity: 16 ACU
- Auto-pause: Deshabilitado durante migración
```

### Fase 3: Extracción y Transformación (Según Spec)

**Usar el proceso diseñado en el spec 02-initial-data-load:**

1. **Ejecutar Schema Analysis Module**
   - Analizar esquema de la BD temporal
   - Generar compatibility matrix
   - Validar contra esquema Redshift existente

2. **Ejecutar Source Data Validation Module**
   - Validar calidad de datos (Requirement 2)
   - Generar reporte de calidad
   - Identificar duplicados y problemas

3. **Ejecutar Parallel Extraction Workers**
   - Extraer directamente a S3 Gold layer
   - Aplicar transformaciones de tipos de datos
   - Generar archivos Parquet optimizados
   - Crear manifest files

4. **Ejecutar Redshift Loader**
   - Cargar a tablas paralelas (_new)
   - Validar carga
   - Ejecutar cutover

### Fase 4: Validación y Limpieza

**Validaciones finales:**
1. Reconciliación de conteos (MySQL temp vs Redshift)
2. Validación de checksums
3. Pruebas de queries en Redshift
4. Validación con equipo de BI de Cencosud

**Limpieza:**
1. Eliminar RDS/Aurora temporal
2. Archivar archivos SQL originales a S3 Glacier
3. Eliminar archivos de staging después de 30 días
4. Documentar proceso y resultados

---

## 4. Alternativa: Procesamiento Directo de SQL (No Recomendado)

**Si NO queremos usar BD temporal:**

Podríamos procesar el SQL directamente con un script Python que:
1. Parse el archivo SQL
2. Extraiga los INSERT statements
3. Convierta directamente a Parquet

**Desventajas:**
- Más complejo de implementar
- Menos robusto ante errores
- No permite validaciones SQL nativas
- Más difícil de debuggear

**Solo considerar si:**
- El dump es extremadamente grande (>1TB)
- Restricciones de tiempo muy ajustadas
- Restricciones de costo muy estrictas

---

## 5. Cronograma Estimado

```
Día 1: Recepción y Validación
- Recibir archivos en S3 (2 horas)
- Validar integridad (1 hora)
- Extraer metadata (1 hora)

Día 2: Preparación de Infraestructura
- Crear RDS temporal (1 hora)
- Configurar Glue jobs (2 horas)
- Configurar monitoreo (1 hora)

Día 3-4: Carga y Validación en BD Temporal
- Restaurar dump en RDS (4-8 horas según tamaño)
- Ejecutar validaciones de calidad (2 horas)
- Revisar y resolver issues (4 horas)

Día 5-6: Extracción y Transformación
- Ejecutar Glue jobs de extracción (6-12 horas)
- Validar archivos Parquet en S3 (2 horas)
- Generar manifest files (1 hora)

Día 7: Carga a Redshift
- Cargar a tablas paralelas (4-6 horas)
- Validación y reconciliación (2 horas)
- Cutover (1 hora en ventana de mantenimiento)

Día 8: Validación Final y Limpieza
- Pruebas con equipo BI (4 horas)
- Limpieza de recursos temporales (1 hora)
- Documentación final (2 horas)
```

**Total estimado: 8 días laborables**

---

## 6. Costos Estimados

```
RDS MySQL Temporal (db.r6g.xlarge):
- Instancia: $0.48/hora × 24 horas × 7 días = $80.64
- Storage: 500 GB × $0.115/GB-mes × 0.25 mes = $14.38
- Subtotal RDS: ~$95

S3 Storage Temporal:
- 100 GB staging × $0.023/GB = $2.30
- Requests y transferencias: ~$5
- Subtotal S3: ~$7

Glue Jobs:
- 10 DPU × 12 horas × $0.44/DPU-hora = $52.80
- Subtotal Glue: ~$53

Total Estimado: ~$155 USD
```

---

## 7. Checklist de Comunicación con Cencosud

**Información a solicitar:**
- [ ] Tamaño aproximado del archivo comprimido
- [ ] Tamaño descomprimido estimado
- [ ] Número de tablas incluidas
- [ ] Versión de MySQL usada para generar el dump
- [ ] Fecha de generación del dump
- [ ] Método de generación (mysqldump, otro)
- [ ] Opciones usadas en mysqldump (si aplica)
- [ ] Checksum MD5/SHA256 del archivo
- [ ] Ventana de tiempo disponible para la transferencia

**Información a proporcionar:**
- [ ] Método de transferencia elegido (S3, SFTP, URL)
- [ ] Credenciales temporales o URL pre-firmada
- [ ] Instrucciones paso a paso para la subida
- [ ] Contacto técnico para soporte durante transferencia
- [ ] Confirmación de recepción exitosa
- [ ] Timeline estimado del proceso completo

---

## 8. Recomendación Final

**Método Recomendado:**
1. **Transferencia**: S3 directo con AWS CLI (Opción A)
2. **Formato**: SQL dump comprimido (.sql.gz)
3. **Procesamiento**: Cargar a RDS MySQL temporal
4. **Extracción**: Usar proceso diseñado en spec 02-initial-data-load
5. **Timeline**: 8 días laborables

**Ventajas de este enfoque:**
- Usa la infraestructura y procesos ya diseñados
- Máxima validación y control de calidad
- Fácil de debuggear y recuperar ante errores
- Cumple con todos los requirements del spec
- Costo razonable (~$155)

**Próximos pasos inmediatos:**
1. Confirmar con Cencosud el tamaño aproximado del dump
2. Crear bucket S3 staging
3. Generar credenciales temporales
4. Enviar instrucciones a Cencosud
5. Preparar infraestructura (RDS temporal, Glue jobs)
