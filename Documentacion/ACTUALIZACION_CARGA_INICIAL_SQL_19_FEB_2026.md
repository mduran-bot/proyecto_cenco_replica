# Actualización: Recomendaciones para Carga Inicial SQL

**Fecha:** 19 de Febrero, 2026  
**Tipo:** Nueva documentación técnica  
**Impacto:** Spec 2 (Initial Data Load)

---

## Resumen de Cambios

Se ha creado un documento completo con recomendaciones técnicas para la recepción y procesamiento de archivos SQL de la carga inicial de datos históricos desde MySQL Janis.

---

## Documento Creado

### RECOMENDACIONES_CARGA_INICIAL_SQL.md

**Ubicación:** `Documentacion/RECOMENDACIONES_CARGA_INICIAL_SQL.md`

**Propósito:** Proporcionar guía técnica detallada para el proceso de carga inicial de datos históricos desde archivos SQL comprimidos proporcionados por Cencosud.

**Contenido:**
1. Métodos de transferencia recomendados (S3, SFTP, URL pre-firmada)
2. Formato y compresión de archivos SQL
3. Proceso completo de recepción y validación
4. Estrategia de carga a base de datos temporal
5. Extracción y transformación usando spec 02-initial-data-load
6. Cronograma estimado (8 días laborables)
7. Costos estimados (~$155 USD)
8. Checklist de comunicación con Cencosud

---

## Decisiones Técnicas Clave

### 1. Método de Transferencia: S3 Directo (Recomendado)

**Decisión:** Transferencia directa a S3 usando AWS CLI

**Rationale:**
- Evita transferencias intermedias innecesarias
- Datos quedan directamente en AWS donde se procesarán
- Más seguro (cifrado en tránsito y en reposo)
- Más rápido para archivos grandes
- Cumple con políticas de seguridad corporativa

**Implementación:**
```bash
aws s3 cp archivo_comprimido.sql.gz s3://janis-cencosud-initial-load-staging-prod/raw/ \
  --region us-east-1 \
  --sse aws:kms \
  --sse-kms-key-id alias/janis-cencosud-kms
```

### 2. Formato: SQL Dump Comprimido

**Decisión:** Archivos .sql.gz con mysqldump estándar

**Rationale:**
- Formato estándar y ampliamente soportado
- Buena compresión (típicamente 10:1)
- Fácil de validar y procesar
- Compatible con herramientas estándar

**Requisitos para Cencosud:**
- Incluir `CREATE TABLE` statements
- Incluir `INSERT` statements con datos
- Sin `DROP TABLE` (por seguridad)
- Con `--single-transaction` para consistencia
- Con `--extended-insert` para mejor performance

### 3. Procesamiento: RDS MySQL Temporal

**Decisión:** Cargar SQL dump a RDS MySQL temporal antes de extracción

**Rationale:**
- Permite validación completa de datos con SQL nativo
- Facilita transformaciones y limpieza
- Permite usar el proceso de extracción diseñado en spec 02-initial-data-load
- Más control sobre el proceso
- Fácil de debuggear y recuperar ante errores

**Configuración:**
- Instancia: db.r6g.xlarge (4 vCPU, 32 GB RAM)
- Storage: 500 GB gp3 con auto-scaling
- Duración: 1 semana (eliminar después de migración exitosa)
- Costo: ~$95 para toda la migración
- VPC: Misma VPC que Glue jobs para acceso directo

### 4. Extracción: Usar Spec 02-initial-data-load

**Decisión:** Usar el proceso diseñado en spec 02-initial-data-load

**Rationale:**
- Aprovecha infraestructura y procesos ya diseñados
- Máxima validación y control de calidad
- Cumple con todos los requirements del spec
- Mantiene consistencia con el resto del pipeline

**Flujo:**
1. Schema Analysis Module → Analizar esquema de BD temporal
2. Source Data Validation Module → Validar calidad de datos
3. Parallel Extraction Workers → Extraer a S3 Gold layer
4. Redshift Loader → Cargar a tablas paralelas (_new)

---

## Cronograma Detallado

### Día 1: Recepción y Validación
- Recibir archivos en S3 (2 horas)
- Validar integridad (1 hora)
- Extraer metadata (1 hora)

### Día 2: Preparación de Infraestructura
- Crear RDS temporal (1 hora)
- Configurar Glue jobs (2 horas)
- Configurar monitoreo (1 hora)

### Día 3-4: Carga y Validación en BD Temporal
- Restaurar dump en RDS (4-8 horas según tamaño)
- Ejecutar validaciones de calidad (2 horas)
- Revisar y resolver issues (4 horas)

### Día 5-6: Extracción y Transformación
- Ejecutar Glue jobs de extracción (6-12 horas)
- Validar archivos Parquet en S3 (2 horas)
- Generar manifest files (1 hora)

### Día 7: Carga a Redshift
- Cargar a tablas paralelas (4-6 horas)
- Validación y reconciliación (2 horas)
- Cutover (1 hora en ventana de mantenimiento)

### Día 8: Validación Final y Limpieza
- Pruebas con equipo BI (4 horas)
- Limpieza de recursos temporales (1 hora)
- Documentación final (2 horas)

**Total estimado: 8 días laborables**

---

## Costos Estimados

### Desglose de Costos

**RDS MySQL Temporal (db.r6g.xlarge):**
- Instancia: $0.48/hora × 24 horas × 7 días = $80.64
- Storage: 500 GB × $0.115/GB-mes × 0.25 mes = $14.38
- Subtotal RDS: ~$95

**S3 Storage Temporal:**
- 100 GB staging × $0.023/GB = $2.30
- Requests y transferencias: ~$5
- Subtotal S3: ~$7

**Glue Jobs:**
- 10 DPU × 12 horas × $0.44/DPU-hora = $52.80
- Subtotal Glue: ~$53

**Total Estimado: ~$155 USD**

---

## Estructura S3 para Carga Inicial

### Bucket Temporal

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

### Lifecycle Policy

- Archivos en `raw/`: Mover a Glacier después de 30 días
- Archivos en `extracted/`: Eliminar después de 7 días
- Archivos en `validation/`: Retener por 90 días

---

## Checklist de Comunicación con Cencosud

### Información a Solicitar

- [ ] Tamaño aproximado del archivo comprimido
- [ ] Tamaño descomprimido estimado
- [ ] Número de tablas incluidas
- [ ] Versión de MySQL usada para generar el dump
- [ ] Fecha de generación del dump
- [ ] Método de generación (mysqldump, otro)
- [ ] Opciones usadas en mysqldump (si aplica)
- [ ] Checksum MD5/SHA256 del archivo
- [ ] Ventana de tiempo disponible para la transferencia

### Información a Proporcionar

- [ ] Método de transferencia elegido (S3, SFTP, URL)
- [ ] Credenciales temporales o URL pre-firmada
- [ ] Instrucciones paso a paso para la subida
- [ ] Contacto técnico para soporte durante transferencia
- [ ] Confirmación de recepción exitosa
- [ ] Timeline estimado del proceso completo

---

## Alternativas Consideradas

### Opción B: Transferencia vía SFTP

**Pros:**
- Método más tradicional y familiar
- No requiere AWS CLI instalado

**Contras:**
- Requiere configurar AWS Transfer Family
- Paso adicional de transferencia
- Más complejo de configurar

**Decisión:** No recomendado como primera opción

### Opción C: URL Pre-firmada

**Pros:**
- Muy simple (solo navegador)
- No requiere herramientas adicionales

**Contras:**
- Solo para archivos pequeños (<5GB)
- Menos control sobre el proceso
- Timeout de 24 horas

**Decisión:** Solo para archivos pequeños

### Opción D: Procesamiento Directo de SQL

**Pros:**
- Evita crear RDS temporal
- Potencialmente más rápido

**Contras:**
- Más complejo de implementar
- Menos robusto ante errores
- No permite validaciones SQL nativas
- Más difícil de debuggear

**Decisión:** No recomendado

---

## Riesgos y Mitigaciones

### Riesgo 1: Archivo SQL Corrupto

**Probabilidad:** Baja  
**Impacto:** Alto  
**Mitigación:**
- Validar checksum antes de procesar
- Probar descompresión antes de carga
- Solicitar re-envío si hay problemas

### Riesgo 2: Esquema Incompatible

**Probabilidad:** Media  
**Impacto:** Alto  
**Mitigación:**
- Validar CREATE TABLE statements
- Comparar con esquema esperado
- Documentar diferencias y ajustar transformaciones

### Riesgo 3: Datos Incompletos o Inconsistentes

**Probabilidad:** Media  
**Impacto:** Medio  
**Mitigación:**
- Ejecutar validaciones de calidad exhaustivas
- Generar reporte de calidad detallado
- Coordinar con Cencosud para resolver issues

### Riesgo 4: Tiempo de Carga Excesivo

**Probabilidad:** Baja  
**Impacto:** Medio  
**Mitigación:**
- Usar instancia RDS apropiada (db.r6g.xlarge)
- Monitorear progreso de carga
- Tener plan B con instancia más grande si es necesario

---

## Próximos Pasos Inmediatos

### Acciones Técnicas

1. **Crear bucket S3 staging**
   ```bash
   aws s3 mb s3://janis-cencosud-initial-load-staging-prod --region us-east-1
   ```

2. **Configurar lifecycle policies**
   - Mover a Glacier después de 30 días
   - Eliminar archivos temporales después de 7 días

3. **Generar credenciales temporales**
   ```bash
   aws sts get-session-token --duration-seconds 86400
   ```

4. **Preparar script de validación**
   - Validar integridad de archivo
   - Extraer metadata
   - Generar reporte

5. **Preparar Terraform para RDS temporal**
   - Módulo RDS MySQL
   - Security groups
   - Subnet groups

### Acciones de Coordinación

1. **Contactar a Cencosud**
   - Solicitar información del dump SQL
   - Coordinar ventana de transferencia
   - Proporcionar instrucciones

2. **Preparar documentación**
   - Guía paso a paso para Cencosud
   - Troubleshooting guide
   - Contactos de soporte

3. **Coordinar con equipo**
   - Asignar responsables
   - Definir horarios de disponibilidad
   - Preparar plan de contingencia

---

## Impacto en el Proyecto

### Beneficios

- ✅ Proceso claro y documentado para carga inicial
- ✅ Reduce riesgo de errores en transferencia
- ✅ Aprovecha infraestructura y procesos existentes
- ✅ Costo razonable y predecible
- ✅ Timeline realista y alcanzable

### Dependencias

- ⏳ Confirmación de Cencosud sobre tamaño del dump
- ⏳ Aprobación de costos (~$155 USD)
- ⏳ Coordinación de ventana de transferencia
- ⏳ Preparación de infraestructura (bucket S3, RDS temporal)

---

## Documentación Actualizada

### Archivos Modificados

1. **Documentacion/ESTADO_PROYECTO_FEBRERO_2026.md**
   - Agregada sección de Spec 2 con proceso de carga inicial
   - Actualizada versión a 1.1
   - Actualizada fecha de última modificación

### Archivos Creados

1. **Documentacion/RECOMENDACIONES_CARGA_INICIAL_SQL.md** ⭐
   - Documento técnico completo (371 líneas)
   - 8 secciones principales
   - Guía paso a paso
   - Checklist de comunicación

2. **Documentacion/ACTUALIZACION_CARGA_INICIAL_SQL_19_FEB_2026.md** ⭐
   - Este documento
   - Resumen de cambios
   - Decisiones técnicas
   - Próximos pasos

---

## Referencias

### Documentación Relacionada

- [RECOMENDACIONES_CARGA_INICIAL_SQL.md](RECOMENDACIONES_CARGA_INICIAL_SQL.md) - Documento técnico completo ⭐
- [ESTADO_PROYECTO_FEBRERO_2026.md](ESTADO_PROYECTO_FEBRERO_2026.md) - Estado del proyecto actualizado
- [.kiro/specs/02-initial-data-load/](../.kiro/specs/02-initial-data-load/) - Spec de carga inicial

### Specs Relacionados

- Spec 2: Initial Data Load - Proceso de extracción y transformación
- Spec 5: Data Transformation - Módulos de transformación
- Spec 6: Redshift Loading - Carga a Redshift

---

## Conclusión

Se ha documentado completamente el proceso de carga inicial de datos históricos desde archivos SQL. El enfoque recomendado (S3 directo + RDS temporal + spec 02-initial-data-load) proporciona un balance óptimo entre simplicidad, robustez, y costo.

**Recomendación:** Proceder con coordinación con Cencosud para confirmar detalles del dump SQL y programar la transferencia.

---

**Documento creado:** 19 de Febrero, 2026  
**Última actualización:** 19 de Febrero, 2026  
**Estado:** Documentación completa - Listo para coordinación con Cencosud
