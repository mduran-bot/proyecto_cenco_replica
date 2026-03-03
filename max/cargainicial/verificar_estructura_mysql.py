#!/usr/bin/env python3
"""
Verificador de Estructura MySQL vs create_redshift_tables.sql
=============================================================
Compara las tablas y columnas definidas en el archivo SQL contra
la estructura real de la base de datos MySQL.

Uso:
    python verificar_estructura_mysql.py

Resultado:
    - Reporte en consola con tablas y columnas que coinciden / faltan / sobran
    - Archivo de reporte: verificacion_resultado.txt
"""

import re
import sys
import pymysql
from pathlib import Path
from datetime import datetime

# ============================================================================
# CONFIGURACIÓN
# ============================================================================

# Ruta al archivo SQL (ajustar si es necesario)
SQL_FILE_PATH = Path(r"C:\Users\maxim\Desktop\create_redshift_tables.sql")

# Conexión MySQL (mismas credenciales que los demás scripts)
MYSQL_CONFIG = {
    'host': 'cencodb.janis.in',
    'port': 3306,
    'user': 'cenco-replica',
    'password': 'zd2lhVnesCH2vV.9',
    'database': 'janis_wongio'
}

# Si quieres guardar el reporte en un archivo además de mostrarlo en consola
SAVE_REPORT = True
REPORT_FILE = Path("verificacion_resultado.txt")

# ============================================================================


def parse_sql_file(sql_path: Path) -> dict:
    """
    Parsea el archivo SQL y extrae las tablas con sus columnas.

    Retorna:
        {
            "nombre_tabla": ["col1", "col2", ...],
            ...
        }
    """
    if not sql_path.exists():
        raise FileNotFoundError(f"No se encontró el archivo SQL: {sql_path}")

    contenido = sql_path.read_text(encoding='utf-8', errors='replace')

    # Patrón para cada CREATE TABLE ... (...)
    patron_tabla = re.compile(
        r'CREATE TABLE IF NOT EXISTS\s+\w+\.(\w+)\s*\(([^;]+?)\);',
        re.IGNORECASE | re.DOTALL
    )

    tablas = {}

    for match in patron_tabla.finditer(contenido):
        nombre_tabla = match.group(1).strip()
        cuerpo = match.group(2)

        columnas = []
        for linea in cuerpo.splitlines():
            linea = linea.strip().rstrip(',')
            if not linea:
                continue
            # La primera palabra de cada línea es el nombre de columna
            # (se descartan líneas que sean constraints o comentarios)
            if linea.startswith('--'):
                continue
            # Comparar la primera palabra exacta, no prefijo
            # (evita que 'keywords' sea descartado por coincidir con 'KEY')
            primera_palabra = linea.split()[0].upper() if linea.split() else ''
            if primera_palabra in ('PRIMARY', 'UNIQUE', 'KEY', 'INDEX', 'CONSTRAINT', 'FOREIGN'):
                continue
            partes = linea.split()
            if partes:
                columnas.append(partes[0].strip('`"'))

        if columnas:
            tablas[nombre_tabla] = columnas

    return tablas


def obtener_estructura_mysql(config: dict) -> dict:
    """
    Consulta INFORMATION_SCHEMA para obtener tablas y columnas de la DB.

    Retorna:
        {
            "nombre_tabla": ["col1", "col2", ...],
            ...
        }
    """
    # Forzamos DictCursor y charset siempre, sin importar qué haya en el config
    params = {**config, 'charset': 'utf8mb4', 'cursorclass': pymysql.cursors.DictCursor}
    conexion = pymysql.connect(**params)
    try:
        with conexion.cursor() as cursor:
            query = """
                SELECT
                    TABLE_NAME,
                    COLUMN_NAME
                FROM
                    INFORMATION_SCHEMA.COLUMNS
                WHERE
                    TABLE_SCHEMA = %s
                ORDER BY
                    TABLE_NAME,
                    ORDINAL_POSITION
            """
            cursor.execute(query, (config['database'],))
            filas = cursor.fetchall()

        tablas = {}
        for fila in filas:
            tabla = fila['TABLE_NAME']
            columna = fila['COLUMN_NAME']
            if tabla not in tablas:
                tablas[tabla] = []
            tablas[tabla].append(columna)

        return tablas
    finally:
        conexion.close()


def comparar_estructuras(sql_tablas: dict, mysql_tablas: dict) -> dict:
    """
    Compara las dos estructuras y retorna un diccionario con los resultados.
    """
    sql_set = set(sql_tablas.keys())
    mysql_set = set(mysql_tablas.keys())

    resultado = {
        'tablas_ok': [],            # existen en ambos
        'tablas_faltantes_mysql': [],  # en SQL pero NO en MySQL
        'tablas_extra_mysql': [],    # en MySQL pero NO en SQL
        'detalle_columnas': {},      # por tabla: columnas ok / faltantes / extra
    }

    resultado['tablas_ok'] = sorted(sql_set & mysql_set)
    resultado['tablas_faltantes_mysql'] = sorted(sql_set - mysql_set)
    resultado['tablas_extra_mysql'] = sorted(mysql_set - sql_set)

    # Comparar columnas sólo en tablas que existen en ambos lados
    for tabla in resultado['tablas_ok']:
        sql_cols = set(c.lower() for c in sql_tablas[tabla])
        mysql_cols = set(c.lower() for c in mysql_tablas[tabla])

        cols_ok = sorted(sql_cols & mysql_cols)
        cols_faltantes = sorted(sql_cols - mysql_cols)  # en SQL pero NO en MySQL
        cols_extra = sorted(mysql_cols - sql_cols)       # en MySQL pero NO en SQL

        resultado['detalle_columnas'][tabla] = {
            'ok': cols_ok,
            'faltantes_mysql': cols_faltantes,
            'extra_mysql': cols_extra,
        }

    return resultado


def generar_reporte(resultado: dict, sql_tablas: dict, mysql_tablas: dict) -> str:
    """Genera el texto completo del reporte."""
    lineas = []
    sep = "=" * 70

    lineas.append(sep)
    lineas.append("  VERIFICACIÓN DE ESTRUCTURA: MySQL vs create_redshift_tables.sql")
    lineas.append(f"  Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lineas.append(sep)

    # ---- Resumen general ----
    total_sql = len(sql_tablas)
    total_mysql = len(mysql_tablas)
    tablas_ok = len(resultado['tablas_ok'])
    tablas_falt = len(resultado['tablas_faltantes_mysql'])
    tablas_extra = len(resultado['tablas_extra_mysql'])

    lineas.append("")
    lineas.append("RESUMEN GENERAL")
    lineas.append("-" * 40)
    lineas.append(f"  Tablas en SQL (Redshift)   : {total_sql}")
    lineas.append(f"  Tablas en MySQL            : {total_mysql}")
    lineas.append(f"  Tablas que coinciden ✅    : {tablas_ok}")
    lineas.append(f"  Faltan en MySQL ❌         : {tablas_falt}")
    lineas.append(f"  Extra en MySQL ⚠️          : {tablas_extra}")

    # ---- Tablas faltantes en MySQL ----
    lineas.append("")
    lineas.append(f"TABLAS DEL SQL QUE FALTAN EN MYSQL ({tablas_falt})")
    lineas.append("-" * 40)
    if resultado['tablas_faltantes_mysql']:
        for t in resultado['tablas_faltantes_mysql']:
            lineas.append(f"  ❌ {t}  ({len(sql_tablas[t])} columnas esperadas)")
    else:
        lineas.append("  ✅ Todas las tablas del SQL están presentes en MySQL")

    # ---- Tablas extra en MySQL ----
    lineas.append("")
    lineas.append(f"TABLAS EN MYSQL QUE NO ESTÁN EN EL SQL ({tablas_extra})")
    lineas.append("-" * 40)
    if resultado['tablas_extra_mysql']:
        for t in resultado['tablas_extra_mysql']:
            lineas.append(f"  ⚠️  {t}  ({len(mysql_tablas[t])} columnas)")
    else:
        lineas.append("  ✅ No hay tablas extra en MySQL")

    # ---- Detalle por tabla (columnas) ----
    lineas.append("")
    lineas.append("DETALLE DE COLUMNAS POR TABLA")
    lineas.append("-" * 40)

    tablas_con_diferencias = {
        t: d for t, d in resultado['detalle_columnas'].items()
        if d['faltantes_mysql'] or d['extra_mysql']
    }
    tablas_perfectas = [
        t for t, d in resultado['detalle_columnas'].items()
        if not d['faltantes_mysql'] and not d['extra_mysql']
    ]

    if tablas_perfectas:
        lineas.append(f"\n  ✅ Tablas con estructura IDÉNTICA ({len(tablas_perfectas)}):")
        for t in sorted(tablas_perfectas):
            n = len(resultado['detalle_columnas'][t]['ok'])
            lineas.append(f"      • {t}  ({n} columnas)")

    if tablas_con_diferencias:
        lineas.append(f"\n  ⚠️  Tablas con DIFERENCIAS en columnas ({len(tablas_con_diferencias)}):")
        for tabla in sorted(tablas_con_diferencias.keys()):
            d = tablas_con_diferencias[tabla]
            lineas.append(f"\n  📋 {tabla}")
            lineas.append(f"     Columnas que coinciden: {len(d['ok'])}")

            if d['faltantes_mysql']:
                lineas.append(f"     ❌ Faltan en MySQL ({len(d['faltantes_mysql'])}):")
                for col in d['faltantes_mysql']:
                    lineas.append(f"          - {col}")

            if d['extra_mysql']:
                lineas.append(f"     ⚠️  Extra en MySQL ({len(d['extra_mysql'])}):")
                for col in d['extra_mysql']:
                    lineas.append(f"          + {col}")
    else:
        lineas.append("\n  ✅ Todas las tablas coincidentes tienen columnas idénticas")

    lineas.append("")
    lineas.append(sep)

    # ---- Veredicto final ----
    hay_problemas = tablas_falt > 0 or any(
        d['faltantes_mysql'] for d in resultado['detalle_columnas'].values()
    )
    if hay_problemas:
        lineas.append("  RESULTADO: ❌ HAY DIFERENCIAS — revisar secciones anteriores")
    else:
        lineas.append("  RESULTADO: ✅ ESTRUCTURA COINCIDE COMPLETAMENTE")
    lineas.append(sep)

    return "\n".join(lineas)


def main():
    print(f"\n{'='*70}")
    print("  Verificador de Estructura MySQL vs SQL")
    print(f"{'='*70}\n")

    # 1. Parsear el SQL
    print(f"[1/3] Parseando archivo SQL: {SQL_FILE_PATH}")
    try:
        sql_tablas = parse_sql_file(SQL_FILE_PATH)
        print(f"      ✓ {len(sql_tablas)} tablas encontradas en el SQL")
        for t in sorted(sql_tablas.keys()):
            print(f"        • {t}  ({len(sql_tablas[t])} columnas)")
    except FileNotFoundError as e:
        print(f"      ✗ Error: {e}")
        sys.exit(1)

    # 2. Conectar a MySQL y obtener estructura real
    print(f"\n[2/3] Conectando a MySQL: {MYSQL_CONFIG['host']}/{MYSQL_CONFIG['database']}")
    try:
        mysql_tablas = obtener_estructura_mysql(MYSQL_CONFIG)
        print(f"      ✓ {len(mysql_tablas)} tablas encontradas en MySQL")
    except Exception as e:
        print(f"      ✗ Error conectando a MySQL: {e}")
        print("\n  Posibles causas:")
        print("    - Sin acceso de red al servidor")
        print("    - Credenciales incorrectas")
        print("    - Instalar dependencia: pip install pymysql cryptography")
        sys.exit(1)

    # 3. Comparar y generar reporte
    print(f"\n[3/3] Comparando estructuras...")
    resultado = comparar_estructuras(sql_tablas, mysql_tablas)
    reporte = generar_reporte(resultado, sql_tablas, mysql_tablas)

    print("\n" + reporte)

    if SAVE_REPORT:
        REPORT_FILE.write_text(reporte, encoding='utf-8')
        print(f"\n✓ Reporte guardado en: {REPORT_FILE.resolve()}")


if __name__ == "__main__":
    main()
