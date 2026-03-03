# Análisis de Esquema Redshift - Resumen Ejecutivo

**Fecha de Análisis**: 17 de Febrero de 2026  
**Cluster**: dl-desa  
**Base de Datos**: db_conf  
**Estado**: Available  
**Documento Completo**: `../redshift_schema_analysis.md`

## Propósito

Este documento resume el análisis exhaustivo del esquema de Redshift existente en Cencosud, identificando la estructura actual del Data Warehouse, tipos de datos utilizados, patrones de diseño y consideraciones críticas para la migración de datos desde MySQL-Janis.

## Hallazgos Clave

### Esquemas Identificados (7 total)

1. **`dw_cencofcic`** - Data Warehouse principal (5 tablas)
   - Contiene dimensiones y hechos del negocio
   - Esquema más completo y estructurado
   - Destino probable para datos de Janis

2. **`dl_cs_bi`** - Data Lake Cencosud BI (vacío)
   - **Candidato principal** para datos de Janis
   - Esquema vacío listo para recibir datos
   - Separación lógica de datos operacionales

3. **`dl_cs_bi_eva`** - Data Lake Eva (1 tabla de prueba)
4. **`dw_cencofcic_dbo`** - DW Cencosud DBO (1 tabla)
5. **`dl_sp_maestras`** - Stored Procedures Maestras
6. **`dbo`** - Schema por defecto
7. **`aws_sqlserver_ext`** - Extensiones SQL Server

### Tablas Analizadas (7 total)

#### Schema: dw_cencofcic (Principal)

1. **dim_material** (62 columnas) ⭐ TABLA MÁS COMPLEJA
   - Dimensión de productos con información exhaustiva
   - Incluye: pricing, fidelización, nutrición, volumetría
   - Información específica de Perú (octógonos nutricionales)
   - Jerarquía de productos (material_padre)

2. **dim_ean** (3 columnas)
   - Códigos de barras de productos
   - Relación con dim_material

3. **dim_promocion** (14 columnas)
   - Promociones comerciales detalladas
   - Múltiples clasificaciones

4. **dim_proveedor** (8 columnas)
   - Información de proveedores
   - Incluye RUC (identificación fiscal Perú)

5. **fact_rcv** (1 columna)
   - Tabla de hechos incompleta
   - Requiere análisis adicional

## Patrones de Diseño Identificados

### Naming Conventions

| Prefijo | Propósito | Ejemplo |
|---------|-----------|---------|
| `sk_*` | Surrogate keys (PK) | `sk_material`, `sk_proveedor` |
| `id_*` | Identificadores de negocio | `id_material`, `id_ean` |
| `desc_*` | Descripciones | `desc_material`, `desc_proveedor` |
| `cod_*` | Códigos estandarizados | `cod_proveedor_ruc` |
| `cnt_*` | Contadores/cantidades | `cnt_um_multiplicador` |
| `num_*` | Números | `num_orden_proveedor` |

### Tipos de Datos

**Numéricos:**
- `bigint` - Surrogate keys grandes (64 bits)
- `integer` - Surrogate keys estándar (32 bits)
- `smallint` - Flags booleanos (16 bits, valores 0/1)
- `numeric(p,s)` - Decimales con precisión

**Texto:**
- `varchar(n)` - Longitudes variables (3 a 765 caracteres)
- Más comunes: 30, 54, 60, 150, 300 caracteres

### Características Arquitectónicas

1. **Surrogate Keys**: Todas las dimensiones usan `sk_*` separado de IDs de negocio
2. **Flags Booleanos**: Uso de `smallint` (0/1) en lugar de `boolean`
3. **Jerarquías**: Soporte para relaciones padre-hijo (`sk_material_padre`)
4. **Metadata Rica**: Múltiples campos descriptivos y clasificatorios

## Conversiones MySQL → Redshift

### Mapeo de Tipos de Datos

| MySQL | Redshift | Notas |
|-------|----------|-------|
| `BIGINT` (Unix timestamp) | `TIMESTAMP` | Convertir a ISO 8601 UTC |
| `TINYINT(1)` | `SMALLINT` | Flags booleanos (0/1) |
| `VARCHAR(n)` | `VARCHAR(n)` | Mantener longitudes |
| `DECIMAL(p,s)` | `NUMERIC(p,s)` | Preservar precisión |
| `JSON` | `VARCHAR(65535)` o `SUPER` | Según versión Redshift |
| `TEXT` | `VARCHAR(65535)` | Longitud máxima |
| `DATETIME` | `TIMESTAMP` | Normalizar a UTC |

### Consideraciones Especiales

1. **Surrogate Keys**
   - MySQL: IDs auto-increment directos
   - Redshift: Surrogate keys (`sk_*`) separados
   - **Acción**: Generar surrogate keys durante migración

2. **Timestamps**
   - MySQL: Posiblemente BIGINT (Unix) o DATETIME
   - Redshift: TIMESTAMP
   - **Acción**: Conversión y normalización a UTC

3. **Campos Calculados**
   - Muchos campos en Redshift parecen derivados
   - Ejemplo: `cnt_um_multiplicador`, `cnt_um_volumetria_inner`
   - **Acción**: Identificar si vienen de MySQL o se calculan

## Implicaciones para Initial Data Load

### 1. Esquema de Destino

**Recomendación**: Usar esquema `dl_cs_bi` para datos de Janis

**Razones:**
- Esquema vacío y disponible
- Separación lógica de datos operacionales
- Nomenclatura consistente con Data Lake

**Alternativa**: Crear tablas en `dw_cencofcic` si se requiere integración directa

### 2. Estrategia de Surrogate Keys

**Opciones:**

a) **Generar durante migración** (Recomendado)
   - Usar secuencias de Redshift
   - Mantener mapeo de IDs originales en tabla auxiliar
   - Preservar integridad referencial

b) **Usar IDs originales como surrogate keys**
   - Más simple pero menos flexible
   - Requiere coordinación con esquemas existentes

### 3. Transformaciones Requeridas

**Críticas:**
- Conversión de timestamps Unix → TIMESTAMP
- Generación de surrogate keys
- Conversión de flags booleanos TINYINT → SMALLINT

**Opcionales:**
- Cálculo de campos derivados
- Normalización de nombres de columnas
- Aplicación de naming conventions de Redshift

### 4. Validación de Compatibilidad

**Antes de la migración:**
1. Obtener esquema completo de MySQL Janis (25 tablas)
2. Crear matriz de compatibilidad tabla por tabla
3. Identificar campos faltantes en MySQL
4. Definir estrategia para data gaps
5. Validar constraints y relaciones

## Información Técnica del Cluster

**Cluster**: dl-desa  
**Tipo de Nodo**: ra3.xlplus  
**Número de Nodos**: 2  
**Base de Datos**: db_conf  
**Usuario Master**: usr_admin  
**VPC**: vpc-0e70f630594378796  
**Región**: us-east-1  
**Endpoint**: dl-desa.celvg2uxindq.us-east-1.redshift.amazonaws.com

**Costo Estimado**: ~$2.17 USD/hora (~$1,560/mes)

## Próximos Pasos

### Inmediatos (Semana 1)

1. **Obtener Esquema MySQL Janis**
   - Conectar a base de datos MySQL
   - Extraer DDL de 25 tablas esperadas
   - Documentar tipos de datos y constraints

2. **Crear Matriz de Compatibilidad**
   - Mapear tablas MySQL → Redshift
   - Identificar conversiones necesarias
   - Documentar transformaciones requeridas

3. **Validar Esquema de Destino**
   - Confirmar con stakeholders: ¿`dl_cs_bi` o `dw_cencofcic`?
   - Definir naming conventions finales
   - Crear DDL de tablas de destino

### Corto Plazo (Semanas 2-3)

4. **Implementar Schema Analysis Module** (Task 2)
   - Conectar a Redshift (read-only)
   - Conectar a MySQL
   - Generar compatibility matrix automáticamente

5. **Implementar Data Type Conversion Module** (Task 5)
   - Conversiones de tipos de datos
   - Generación de surrogate keys
   - Normalización de timestamps

6. **Validar Datos Fuente** (Task 3)
   - Validar 25 tablas en MySQL
   - Ejecutar data quality checks
   - Generar reporte de validación

### Mediano Plazo (Semanas 4-6)

7. **Implementar Extraction Workers** (Tasks 7-9)
   - Extracción paralela desde MySQL
   - Transformación en vuelo
   - Escritura a S3 Gold

8. **Implementar Redshift Loader** (Tasks 10-12)
   - Carga a tablas staging
   - Validación de calidad
   - UPSERT a tablas de producción

## Documentos Relacionados

### Especificaciones Técnicas
- **Análisis Completo**: `../redshift_schema_analysis.md`
- **Datos Crudos**: `../redshift_columns_full.json`
- **Plan de Implementación**: `Initial Data Load - Plan de Implementación.md`
- **Design Spec**: `../.kiro/specs/02-initial-data-load/design.md`
- **Requirements**: `../.kiro/specs/02-initial-data-load/requirements.md`

### Arquitectura General
- **Documento de Diseño**: `../Documento Detallado de Diseño Janis-Cenco.md`
- **Sistema de Carga**: `Sistema de Carga a Redshift - Resumen Ejecutivo.md`
- **Infraestructura AWS**: `Especificación Detallada de Infraestructura AWS.md`

### Guías de Configuración
- **Tech Stack**: `../.kiro/steering/tech.md`
- **AWS Best Practices**: `../.kiro/steering/Buenas practicas de AWS.md`
- **Terraform Best Practices**: `../.kiro/steering/Terraform Best Practices.md`

## Conclusiones

1. **Estructura Existente**: Redshift tiene un data warehouse bien estructurado con patrones claros
2. **Esquema Disponible**: `dl_cs_bi` es el candidato ideal para datos de Janis
3. **Complejidad Moderada**: Conversiones necesarias son manejables con transformaciones estándar
4. **Siguiente Paso Crítico**: Obtener esquema de MySQL Janis para crear matriz de compatibilidad
5. **Tiempo Estimado**: 2-3 semanas para completar análisis y preparación antes de migración

---

**Documento generado**: 17 de Febrero de 2026  
**Próxima Revisión**: Después de obtener esquema MySQL Janis  
**Estado**: ✅ Análisis Completo - Listo para Fase de Mapeo
