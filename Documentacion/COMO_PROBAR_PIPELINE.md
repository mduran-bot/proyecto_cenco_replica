# Cómo Probar el Pipeline - Guía Rápida

**Fecha:** 19 de Febrero, 2026  
**Propósito:** Instrucciones para probar el pipeline localmente

---

## Ejecución Rápida 🚀

### Opción 1: Test con Datos de Ejemplo Bronze-to-Silver (Recomendado para Inicio)

```bash
cd glue
python scripts/test_pipeline_local.py
```

Este script:
- ✅ Crea datos de ejemplo (simulando Janis API)
- ✅ Aplica todas las transformaciones del pipeline Bronze-to-Silver
- ✅ Muestra el resultado de cada paso
- ✅ Genera un reporte de calidad
- ✅ Compara antes/después

### Opción 2: Test con Datos Reales de Janis API

```bash
cd glue
python scripts/test_pipeline_janis_api.py
```

Este script:
- ✅ Se conecta a la API real de Janis
- ✅ Obtiene una orden específica (configurable)
- ✅ Aplana estructuras JSON anidadas
- ✅ Aplica transformaciones del pipeline
- ✅ Guarda resultados en archivos CSV/JSON
- ✅ Genera reporte de calidad de datos

**✅ Prueba Exitosa Documentada:** Ver `Documentacion/PRUEBA_EXITOSA_API_JANIS.md` para detalles completos de la conexión exitosa con la API de Janis, incluyendo endpoint correcto, estructura de datos, y transformaciones aplicadas.

### Opción 3: Pipeline Completo con Mapeo de Esquema

```bash
cd glue
python scripts/pipeline_with_schema_mapping.py
```

Este script:
- ✅ Obtiene datos reales de Janis API
- ✅ Mapea campos a tablas Redshift (wms_orders, wms_order_items, wms_order_shipping)
- ✅ Aplica transformaciones completas
- ✅ Genera 4 archivos (1 JSON raw + 3 CSV por tabla)
- ✅ Reporte de calidad por tabla
- ✅ Datos listos para carga a Redshift

**📖 Documentación Completa:** Ver [PIPELINE_CON_MAPEO_ESQUEMA.md](PIPELINE_CON_MAPEO_ESQUEMA.md) para detalles completos del pipeline, mapeos de campos, y análisis de completitud.

### Opción 4: Test Pipeline Silver-to-Gold ⭐ NUEVO

**Opción 4a: Con PySpark (completo)**
```bash
cd glue
python scripts/test_silver_to_gold_local.py
```

**Opción 4b: Con pandas (rápido)**
```bash
cd glue
python scripts/test_silver_to_gold_pandas.py
```

Estos scripts:
- ✅ Crean datos de ejemplo en formato Silver (ya procesados)
- ✅ Aplican transformaciones Silver-to-Gold (agregaciones, validación)
- ✅ Generan métricas de negocio por dimensiones
- ✅ Validan calidad de datos en 4 dimensiones
- ✅ Guardan resultados en formato Gold
- ✅ Reporte detallado de calidad y agregaciones

**Diferencias:**
- `test_silver_to_gold_local.py`: Usa PySpark y módulos reales (~30s)
- `test_silver_to_gold_pandas.py`: Usa pandas puro, más rápido (~5s)

**📖 Documentación Completa:** Ver [SILVER_TO_GOLD_MODULOS.md](SILVER_TO_GOLD_MODULOS.md) para detalles de los módulos Silver-to-Gold.

---

## Resultados Esperados 📊

### Test con Datos de Ejemplo Bronze-to-Silver (test_pipeline_local.py)

El script mostrará:

```
============================================================
DATOS ORIGINALES (Bronze - Crudos de Janis API)
============================================================

Problemas en los datos:
  ❌ Espacios en blanco en status y email
  ❌ Tipos incorrectos (todo es string)
  ❌ Emails sin normalizar (mayúsculas)
  ❌ Teléfonos sin formato estándar
  ❌ Valores faltantes (quantity_picked)
  ❌ Duplicados (id=12345 aparece 2 veces)

>>> PASO 1: LIMPIEZA DE DATOS (DataCleaner)
>>> PASO 2: CONVERSIÓN DE TIPOS (DataTypeConverter)
>>> PASO 3: NORMALIZACIÓN (DataNormalizer)
>>> PASO 4: MANEJO DE GAPS (DataGapHandler)
>>> PASO 5: DETECCIÓN DE DUPLICADOS (DuplicateDetector)
>>> PASO 6: RESOLUCIÓN DE CONFLICTOS (ConflictResolver)
>>> PASO 7: REPORTE DE CALIDAD

============================================================
DATOS FINALES (Silver - Listos para Iceberg)
============================================================

Mejoras aplicadas:
  ✅ Datos limpios (sin espacios)
  ✅ Tipos correctos (timestamp, int, float)
  ✅ Emails normalizados (lowercase)
  ✅ Teléfonos normalizados (formato internacional)
  ✅ Campos calculados (items_qty_missing, total_changes)
  ✅ Sin duplicados (solo el más reciente)
  ✅ Metadata de calidad generada
```

### Test con Datos Reales (test_pipeline_janis_api.py)

El script mostrará:

```
============================================================
PASO 0: OBTENER DATOS DE JANIS API
============================================================

Obteniendo orden: 6913fcb6d134afc8da8ac3dd
Conectando a: https://oms.janis.in/api/order/6913fcb6d134afc8da8ac3dd/history
✓ Datos obtenidos exitosamente (Status: 200)
✓ Datos guardados en: glue/data/janis_order_raw.json

Estructura de datos recibidos:
  Tipo: <class 'list'>
  Cantidad de registros: 15
  Claves del primer registro: ['id', 'status', 'dateCreated', ...]

>>> PASO 1: APLANAR JSON (JSONFlattener)

Columnas después de aplanar: 87
Registros: 15
✓ Datos aplanados guardados en: glue/data/janis_order_flattened.csv

>>> PASO 2: IDENTIFICAR COLUMNAS RELEVANTES

Columnas relevantes encontradas: 45
Columnas seleccionadas:
  - id: 6913fcb6d134afc8da8ac3dd
  - status: pending
  - dateCreated: 1609459200
  ...

>>> PASO 3: APLICAR TRANSFORMACIONES

3.1 Limpiando datos...
✓ Espacios en blanco eliminados

3.2 Normalizando emails...
✓   - customer_email normalizado

3.3 Normalizando teléfonos...
✓   - customer_phone normalizado

3.4 Convirtiendo tipos de datos...
✓   - dateCreated convertido a timestamp

>>> PASO 4: RESULTADOS FINALES

Datos transformados:
  - Registros: 15
  - Columnas: 45
✓ Datos transformados guardados en: glue/data/janis_order_transformed.csv

>>> PASO 5: REPORTE DE CALIDAD

Estadísticas de calidad:
  - Valores nulos por columna:
    • customer_address: 2 (13.3%)
    • shipping_notes: 5 (33.3%)
    ✓ No hay valores nulos críticos

✓ PIPELINE COMPLETADO EXITOSAMENTE CON DATOS REALES

Archivos generados:
  1. glue/data/janis_order_raw.json - Datos crudos de la API
  2. glue/data/janis_order_flattened.csv - Datos aplanados
  3. glue/data/janis_order_transformed.csv - Datos transformados
```

---

## Archivos Creados 📁

### Scripts de Prueba

1. **test_pipeline_local.py**
   - **Ubicación:** `glue/scripts/test_pipeline_local.py`
   - **Propósito:** Probar el pipeline con datos de ejemplo simulados
   - **Uso:** `python glue/scripts/test_pipeline_local.py`
   - **Ventajas:** Rápido, no requiere conexión a internet, datos controlados

2. **test_pipeline_janis_api.py**
   - **Ubicación:** `glue/scripts/test_pipeline_janis_api.py`
   - **Propósito:** Probar el pipeline con datos reales de Janis API
   - **Uso:** `python glue/scripts/test_pipeline_janis_api.py`
   - **Ventajas:** Datos reales, valida integración con API, detecta problemas de formato

3. **pipeline_with_schema_mapping.py** ⭐ NUEVO
   - **Ubicación:** `glue/scripts/pipeline_with_schema_mapping.py`
   - **Propósito:** Pipeline completo con mapeo explícito a tablas Redshift
   - **Uso:** `python glue/scripts/pipeline_with_schema_mapping.py`
   - **Ventajas:** Mapeo de esquema, múltiples tablas, datos listos para Redshift

### Datos de Ejemplo

- **Ubicación:** `glue/data/bronze_sample.json`
- **Propósito:** Datos de ejemplo en formato JSON (simulando Janis API)
- **Contenido:** 3 órdenes con estructuras anidadas, duplicados, y problemas de calidad

### Archivos Generados (test_pipeline_janis_api.py)

Cuando ejecutas el script con datos reales, se generan:

1. **janis_order_raw.json**
   - Datos crudos tal como vienen de la API
   - Formato: JSON con estructuras anidadas
   - Útil para: Debugging, análisis de estructura

2. **janis_order_flattened.csv**
   - Datos después de aplanar JSON
   - Formato: CSV con todas las columnas expandidas
   - Útil para: Ver estructura aplanada, análisis en Excel

3. **janis_order_transformed.csv**
   - Datos después de todas las transformaciones
   - Formato: CSV con datos limpios y normalizados
   - Útil para: Validar calidad final, comparar con esperado

### Archivos Generados (pipeline_with_schema_mapping.py) ⭐ NUEVO

Cuando ejecutas el script con mapeo de esquema, se generan:

1. **order_{id}_raw.json**
   - Datos crudos de la API sin transformar
   - Formato: JSON completo de la orden

2. **order_{id}_wms_orders.csv**
   - Tabla principal de órdenes
   - 1 registro por orden
   - 27 columnas mapeadas según esquema Redshift

3. **order_{id}_wms_order_items.csv**
   - Tabla de items de orden
   - N registros (1 por item en la orden)
   - 11 columnas mapeadas

4. **order_{id}_wms_order_shipping.csv**
   - Tabla de envíos
   - N registros (1 por shipping)
   - 11 columnas mapeadas

---

## Configuración del Script de API Real

### Cambiar el Order ID

Para probar con una orden diferente, edita el archivo `test_pipeline_janis_api.py`:

```python
# Línea 144
order_id = "6913fcb6d134afc8da8ac3dd"  # Cambia este ID
```

### Credenciales de API

Las credenciales están hardcodeadas en el script (solo para testing):

```python
headers = {
    'janis-client': 'wongio',
    'janis-api-key': '8fc949ac-6d63-4447-a3d6-a16b66048e61',
    'janis-api-secret': 'UwPbe45dmE7lySRJ3zcA66Pfdt7xAY3QXWO181Y8OTgCxE3aZuyXpS8HyyPSwsWK'
}
```

**⚠️ Nota de Seguridad:** En producción, estas credenciales deben estar en AWS Secrets Manager.

### Endpoint de API

El script usa el endpoint de historial de órdenes:

```
https://oms.janis.in/api/order/{order_id}/history
```

Este endpoint retorna el historial completo de cambios de una orden, incluyendo todas las versiones.

---

## Comparación de Scripts

| Característica | test_pipeline_local.py | test_pipeline_janis_api.py |
|----------------|------------------------|----------------------------|
| **Datos** | Simulados | Reales de API |
| **Conexión Internet** | No requerida | Requerida |
| **Velocidad** | Rápido (~5s) | Medio (~10-15s) |
| **Estructuras JSON** | Simples | Complejas y anidadas |
| **Archivos Generados** | Ninguno | 3 archivos (JSON + 2 CSV) |
| **Uso Recomendado** | Desarrollo inicial | Validación con datos reales |
| **Debugging** | Fácil (datos conocidos) | Medio (datos variables) |

### Entrada (Bronze)
```json
{
  "id": "12345",
  "dateCreated": "1609459200",
  "status": "  pending  ",
  "email": "  USER@TEST.COM  ",
  "phone": "(01) 234-5678",
  "quantity": "10",
  "quantity_picked": "8"
}
```

### Salida (Silver)
```
id: "12345"
dateCreated: 2021-01-01 00:00:00
status: "pending"
email: "user@test.com"
phone: "+51012345678"
quantity: 10
quantity_picked: 8
items_qty_missing: 2
total_changes: 5.50
```

---

## Próximos Pasos 🚀

1. ✅ **Ejecutar test local** - Ver el pipeline en acción con datos de ejemplo
2. ✅ **Ejecutar test con API real** - Validar con datos reales de Janis
3. ✅ **Ejecutar pipeline con mapeo** - Generar tablas Redshift desde API
4. ⏭️ **Analizar archivos generados** - Revisar CSV para validar transformaciones
5. ⏭️ **Probar con diferentes órdenes** - Cambiar order_id para probar variedad
6. ⏭️ **Validar mapeo de esquema** - Verificar que todos los campos se mapean correctamente
7. ⏭️ **Ajustar configuración** - Modificar config según necesidades
8. ⏭️ **Integrar en AWS Glue** - Crear Glue Job con el pipeline

---

## Troubleshooting 🔧

### Error: "No se pudieron obtener datos de la API"

**Posibles causas:**
1. Sin conexión a internet
2. Credenciales inválidas o expiradas
3. Order ID no existe
4. API de Janis caída

**Solución:**
```bash
# Verificar conectividad
curl https://oms.janis.in/api/health

# Probar con otro order ID
# Editar test_pipeline_janis_api.py línea 144
```

### Error: "ModuleNotFoundError: No module named 'modules'"

**Causa:** Script ejecutado desde directorio incorrecto

**Solución:**
```bash
# Asegurarse de estar en el directorio correcto
cd glue
python scripts/test_pipeline_janis_api.py
```

### Error: "ModuleNotFoundError: No module named 'requests'"

**Causa:** Dependencia faltante

**Solución:**
```bash
pip install requests pandas
```

### Archivos no se generan en glue/data/

**Causa:** Directorio no existe

**Solución:**
```bash
mkdir -p glue/data
python scripts/test_pipeline_janis_api.py
```

---

## Preguntas Frecuentes ❓

### ¿Necesito PySpark instalado?
No para el test local. El script usa pandas para simular el pipeline.

### ¿Puedo usar mis propios datos?
Sí, modifica el script para leer tus datos en lugar de los de ejemplo.

### ¿Cómo ajusto la configuración?
Edita el diccionario `pipeline_config` en el script.

### ¿Funciona igual en AWS Glue?
Sí, pero en Glue usarás PySpark en lugar de pandas.

---

## Resumen

**Comando:** `python glue/scripts/test_pipeline_local.py`  
**Tiempo:** ~5 segundos  
**Resultado:** Ver el pipeline completo en acción con datos de ejemplo

¡Listo para probar! 🎉
