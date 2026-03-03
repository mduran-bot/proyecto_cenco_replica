# Instrucciones para Probar Pipeline de Max

**Fecha:** 18 de Febrero, 2026  
**Estado:** Listo para ejecutar (requiere iniciar Docker Desktop)  
**Guía Principal:** Ver `max/INICIO_RAPIDO.md` para instrucciones detalladas

---

## 🎯 Objetivo

Ejecutar el pipeline Bronze-to-Silver de Max con LocalStack para validar su funcionalidad antes de integrarlo con tu trabajo.

**NOTA:** Este documento proporciona un resumen. Para instrucciones paso a paso completas, consulta `max/INICIO_RAPIDO.md`.

---

## 📚 Documentación Disponible

### Guía de Inicio Rápido (RECOMENDADA)
**Archivo:** `max/INICIO_RAPIDO.md`

Guía completa y actualizada con:
- Prerequisitos detallados (Docker, Python, Java)
- Instrucciones paso a paso numeradas
- Troubleshooting exhaustivo
- Comandos útiles para debugging
- Ejemplos de salida esperada
- Opciones de configuración (Docker Compose vs Docker Run)

### Documentación de Análisis
- **Análisis comparativo:** `Documentacion/ANALISIS_COMPARATIVO_MAX_VICENTE.md`
- **Plan de integración:** `Documentacion/PLAN_INTEGRACION_MAX_VICENTE.md`
- **Sesión de revisión:** `Documentacion/SESION_REVISION_MAX_18FEB2026.md`

---

## ✅ Preparación Completada

Ya hemos preparado todo lo necesario:

1. ✅ Código de Max descargado en carpeta `max/`
2. ✅ Archivo `docker-compose.yml` configurado en la raíz (servicios: S3, IAM)
3. ✅ Guía de inicio rápido creada: `max/INICIO_RAPIDO.md`
4. ✅ Documentación de análisis y plan de integración

---

## 🚀 Pasos para Ejecutar (En Orden)

### Paso 1: Iniciar Docker Desktop

**ACCIÓN MANUAL REQUERIDA:**
1. Busca "Docker Desktop" en el menú de Windows
2. Haz clic para iniciar la aplicación
3. Espera a que el ícono de Docker en la bandeja del sistema esté verde
4. Esto puede tomar 1-2 minutos

**Verificar que Docker está corriendo:**
```bash
docker ps
```

Si ves una tabla (aunque esté vacía), Docker está listo. ✅

---

### Paso 2: Iniciar LocalStack

LocalStack simula AWS localmente (S3 e IAM para este pipeline)

**El archivo `docker-compose.yml` ya está configurado en la raíz del proyecto.**

```bash
# Desde la raíz del proyecto
docker-compose up -d
```

**Configuración actual de LocalStack:**
- Servicios habilitados: S3, IAM
- Puerto: 4566
- Región: us-east-1
- Credenciales de prueba: test/test

**Verificar que LocalStack está corriendo:**
```bash
docker ps
```

Deberías ver un contenedor llamado `localstack-janis-cencosud` con estado "Up".

**Ver logs de LocalStack (opcional):**
```bash
docker logs localstack-janis-cencosud -f
```

Presiona `Ctrl+C` para salir de los logs.

---

### Paso 3: Crear Buckets S3 con Terraform

```bash
cd max/terraform

# Inicializar Terraform (solo la primera vez)
terraform init

# Crear los buckets
terraform apply -auto-approve
```

**Verificar que los buckets se crearon:**
```bash
aws --endpoint-url=http://localhost:4566 s3 ls
```

**Deberías ver:**
```
2026-02-18 10:00:00 data-lake-bronze
2026-02-18 10:00:00 data-lake-silver
2026-02-18 10:00:00 glue-scripts-bin
```

---

### Paso 4: Subir Datos de Prueba a Bronze

```bash
# Volver a la carpeta max
cd ..

# Subir archivo de prueba
aws --endpoint-url=http://localhost:4566 s3 cp \
  tests/fixtures/sample_ventas_lines.json \
  s3://data-lake-bronze/ventas/sample_ventas_lines.json
```

**Verificar que el archivo se subió:**
```bash
aws --endpoint-url=http://localhost:4566 s3 ls s3://data-lake-bronze/ventas/
```

Deberías ver: `sample_ventas_lines.json`

---

### Paso 5: Ejecutar el Pipeline 🎉

```bash
# Asegúrate de estar en la carpeta max/
python run_pipeline_to_silver.py
```

**Salida esperada:**

El pipeline ejecutará 8 transformaciones en secuencia:
1. JSONFlattener (12 → 15 registros)
2. DataCleaner (15 → 15 registros)
3. DataNormalizer (15 → 15 registros)
4. DataTypeConverter (15 → 15 registros)
5. DuplicateDetector (15 → 15 registros)
6. ConflictResolver (15 → 11 registros)
7. DataGapHandler (11 → 11 registros)
8. IcebergWriter (escribe a Silver)

**Resultado final:**
- ✅ 11 registros procesados y escritos a Silver
- ✅ Archivo JSON en S3: `s3://data-lake-silver/ventas_procesadas/`
- ✅ Resumen CSV local: `output/silver/ventas_procesadas_summary.csv`

---

### Paso 6: Verificar Resultados

#### Ver archivos en S3 Silver
```bash
aws --endpoint-url=http://localhost:4566 s3 ls s3://data-lake-silver/ventas_procesadas/ --recursive
```

#### Ver resumen local (más fácil de leer)
```bash
# Ver el CSV generado
type output\silver\ventas_procesadas_summary.csv
```

#### Descargar un archivo JSON de S3 para inspección
```bash
# Listar archivos
aws --endpoint-url=http://localhost:4566 s3 ls s3://data-lake-silver/ventas_procesadas/

# Descargar (reemplaza el nombre del archivo)
aws --endpoint-url=http://localhost:4566 s3 cp \
  s3://data-lake-silver/ventas_procesadas/part-00000-xxxxx.json \
  resultado_silver.json

# Ver contenido
type resultado_silver.json
```

---

## 📊 Qué Documentar

Una vez que el pipeline ejecute exitosamente, documenta:

### 1. Capturas de Pantalla
- Ejecución del pipeline (logs)
- Listado de archivos en S3 Silver
- Contenido del CSV de resumen

### 2. Métricas
- Tiempo de ejecución total
- Registros procesados por módulo
- Tamaño de archivos generados

### 3. Esquema de Datos
- Columnas en el resultado final
- Tipos de datos
- Comparar con requirements

### 4. Problemas Encontrados
- Errores durante la ejecución
- Warnings importantes
- Soluciones aplicadas

**Guardar en:** `Documentacion/RESULTADOS_PRUEBA_MAX.md`

---

## 🛠️ Troubleshooting

### Error: "Cannot connect to Docker"
**Causa:** Docker Desktop no está corriendo  
**Solución:** Iniciar Docker Desktop y esperar a que esté listo

### Error: "Bucket does not exist"
**Causa:** Terraform no se ejecutó correctamente  
**Solución:** 
```bash
cd max/terraform
terraform destroy -auto-approve
terraform apply -auto-approve
```

### Error: "Connection refused to localhost:4566"
**Causa:** LocalStack no está corriendo  
**Solución:**
```bash
docker-compose down
docker-compose up -d
# Esperar 30 segundos
docker logs localstack-janis-cencosud
```

### Error: "Java not found" o "JAVA_HOME not set"
**Causa:** Java no está instalado o configurado  
**Solución:**
```bash
# Verificar Java
java -version

# Si no está instalado, descargar Java 11+ de:
# https://adoptium.net/
```

### Error: "HADOOP_HOME not set" (Windows)
**Causa:** PySpark necesita winutils en Windows  
**Solución:**
1. Descargar winutils: https://github.com/cdarlint/winutils/tree/master/hadoop-3.3.1/bin
2. Crear carpeta `C:\hadoop\bin\`
3. Copiar `winutils.exe` y `hadoop.dll` a esa carpeta
4. Configurar variable de entorno:
```powershell
$env:HADOOP_HOME = "C:\hadoop"
```

### Error: "Address already in use" o problemas de red en Spark
**Causa:** Conflictos de red en Windows con configuración por defecto de Spark  
**Solución:** El script `run_pipeline_to_silver.py` ya incluye las configuraciones necesarias:
- `spark.driver.host = localhost`
- `spark.driver.bindAddress = 127.0.0.1`

Estas configuraciones están incluidas automáticamente y evitan conflictos de red.

### Pipeline ejecuta pero no genera archivos
**Causa:** Permisos o configuración de S3  
**Solución:**
```bash
# Verificar que LocalStack está funcionando
curl http://localhost:4566/_localstack/health

# Reiniciar LocalStack
docker-compose restart
```

---

## 🧹 Limpieza (Después de Probar)

### Detener LocalStack (mantener datos)
```bash
docker-compose stop
```

### Detener y eliminar LocalStack (borrar datos)
```bash
docker-compose down
```

### Eliminar volúmenes de datos
```bash
docker-compose down -v
rm -rf localstack-data/
```

### Destruir infraestructura Terraform
```bash
cd max/terraform
terraform destroy -auto-approve
```

---

## 📝 Checklist de Ejecución

Marca cada paso conforme lo completes:

- [ ] Docker Desktop iniciado y corriendo
- [ ] LocalStack iniciado con `docker-compose up -d`
- [ ] Buckets creados con `terraform apply`
- [ ] Datos de prueba subidos a Bronze
- [ ] Pipeline ejecutado con `python run_pipeline_to_silver.py`
- [ ] Resultados verificados en S3 Silver
- [ ] CSV de resumen revisado
- [ ] Documentación de resultados creada
- [ ] Capturas de pantalla guardadas

---

## 🎯 Próximos Pasos (Después de Validar)

Una vez que el pipeline funcione correctamente:

1. **Documentar resultados** en `RESULTADOS_PRUEBA_MAX.md`
2. **Comparar esquemas** de salida con requirements
3. **Identificar diferencias** con tu implementación
4. **Comenzar Fase 2** del plan de integración:
   - Copiar módulos únicos de Max
   - Fusionar módulos duplicados
   - Integrar SchemaEvolutionManager

---

## 📚 Recursos Útiles

- **Guía rápida:** `max/INICIO_RAPIDO.md`
- **README de Max:** `max/README.md`
- **Análisis comparativo:** `Documentacion/ANALISIS_COMPARATIVO_MAX_VICENTE.md`
- **Plan de integración:** `Documentacion/PLAN_INTEGRACION_MAX_VICENTE.md`

---

## 💡 Tips

1. **Logs en tiempo real:** `docker logs localstack-janis-cencosud -f`
2. **Reiniciar si hay problemas:** `docker-compose restart`
3. **Ver estado de salud:** `curl http://localhost:4566/_localstack/health`
4. **Limpiar y empezar de nuevo:** `docker-compose down -v && docker-compose up -d`

---

**¡Todo está listo!** Solo necesitas iniciar Docker Desktop y seguir los pasos. 🚀

**Tiempo estimado:** 15-20 minutos (incluyendo instalación de dependencias)
