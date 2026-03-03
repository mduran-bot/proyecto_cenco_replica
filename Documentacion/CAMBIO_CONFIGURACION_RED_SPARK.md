# Cambio de Configuración de Red en Spark - Pipeline Max

**Fecha:** 18 de Febrero, 2026  
**Archivo Modificado:** `max/run_pipeline_to_silver.py`  
**Tipo de Cambio:** Configuración de red para compatibilidad Windows

---

## Resumen del Cambio

Se agregaron dos configuraciones de red al SparkSession para resolver problemas de binding de red en entornos Windows:

```python
.config("spark.driver.host", "localhost")
.config("spark.driver.bindAddress", "127.0.0.1")
```

---

## Problema Resuelto

### Síntoma
En sistemas Windows, PySpark puede tener problemas al intentar hacer bind a direcciones de red, resultando en errores como:
- "Address already in use"
- "Cannot assign requested address"
- Timeouts en la inicialización del SparkContext

### Causa Raíz
Por defecto, Spark intenta detectar automáticamente la dirección IP del host y hacer bind a ella. En Windows, esto puede causar conflictos con:
- Múltiples interfaces de red
- VPNs activas
- Configuraciones de firewall
- Docker Desktop networking

---

## Solución Implementada

### Configuraciones Agregadas

```python
def init_spark_session_simple():
    """Inicializar SparkSession corrigiendo el error de formato numérico '60s'"""
    spark = SparkSession.builder \
        .appName("bronze-to-silver-local-test") \
        .master("local[*]") \
        .config("spark.driver.host", "localhost") \          # NUEVO
        .config("spark.driver.bindAddress", "127.0.0.1") \   # NUEVO
        .config("spark.jars.packages", "org.apache.hadoop:hadoop-aws:3.3.4,com.amazonaws:aws-java-sdk-bundle:1.12.262") \
        # ... resto de configuraciones
```

### Explicación de las Configuraciones

1. **`spark.driver.host = "localhost"`**
   - Especifica el hostname que el driver usará para anunciarse a los executors
   - Usar "localhost" asegura que funcione en cualquier entorno local
   - Evita problemas con resolución de DNS y múltiples interfaces

2. **`spark.driver.bindAddress = "127.0.0.1"`**
   - Especifica la dirección IP exacta donde el driver hará bind
   - 127.0.0.1 es la dirección loopback estándar
   - Garantiza que el binding sea exitoso en Windows

---

## Impacto

### Positivo
- ✅ Resuelve problemas de red en Windows
- ✅ Hace el pipeline más portable entre sistemas operativos
- ✅ Elimina dependencia de configuración de red específica del sistema
- ✅ Mejora la experiencia de desarrollo local

### Sin Impacto Negativo
- ✅ No afecta funcionalidad existente
- ✅ No cambia el comportamiento del pipeline
- ✅ Compatible con LocalStack
- ✅ No afecta producción (AWS Glue usa configuración diferente)

---

## Compatibilidad

### Sistemas Operativos
- ✅ Windows 10/11
- ✅ Linux (sin cambios)
- ✅ macOS (sin cambios)

### Entornos
- ✅ Desarrollo local con LocalStack
- ✅ Testing local sin Docker
- ✅ CI/CD pipelines
- ⚠️ No aplicable a AWS Glue (usa configuración gestionada)

---

## Documentación Actualizada

Los siguientes archivos fueron actualizados para reflejar este cambio:

1. **`max/README.md`**
   - Agregada sección en Troubleshooting sobre problemas de red
   - Documentadas las configuraciones incluidas

2. **`max/INICIO_RAPIDO.md`**
   - Agregada nota sobre configuraciones de red automáticas
   - Actualizado troubleshooting

3. **`Documentacion/INSTRUCCIONES_PRUEBA_PIPELINE_MAX.md`**
   - Agregada sección sobre problemas de red en Windows
   - Explicación de la solución incluida

---

## Referencias

- [Spark Configuration - Networking](https://spark.apache.org/docs/latest/configuration.html#networking)
- [Spark Standalone Mode - Network Configuration](https://spark.apache.org/docs/latest/spark-standalone.html#cluster-launch-scripts)
- [PySpark on Windows - Common Issues](https://spark.apache.org/docs/latest/api/python/getting_started/install.html)

---

## Próximos Pasos

No se requieren acciones adicionales. El cambio está completo y documentado.

---

**Implementado por:** Vicente  
**Revisado por:** [Pendiente]  
**Estado:** ✅ Completado y Documentado
