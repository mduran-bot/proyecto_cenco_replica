# Integración de SonarQube Cloud Analysis con GitHub Actions

## Descripción General

Este proyecto implementa análisis automático de calidad de código usando SonarQube Cloud integrado con GitHub Actions. El workflow ejecuta tests con cobertura y envía los resultados a SonarCloud para análisis continuo de calidad y seguridad del código.

## Configuración del Workflow

### Archivo: `.github/workflows/sonar.yml`

El workflow se ejecuta automáticamente en:
- **Push a main**: Cada vez que se hace push a la rama principal
- **Pull Requests**: Cuando se abre, sincroniza o reabre un PR

### Componentes del Workflow

#### 1. Checkout del Código
```yaml
- uses: actions/checkout@v4
  with:
    fetch-depth: 0
```
- Descarga el código completo del repositorio
- `fetch-depth: 0` obtiene todo el historial para análisis de SonarCloud

#### 2. Configuración de Python
```yaml
- name: Set up Python
  uses: actions/setup-python@v4
  with:
    python-version: '3.10'
```
- Configura Python 3.10 como runtime
- Compatible con las dependencias del proyecto

#### 3. Instalación de Dependencias
```yaml
- name: Install dependencies
  run: |
    python -m pip install --upgrade pip
    pip install pytest pytest-cov requests pandas jsonschema hypothesis pyspark boto3 apache-airflow
    if [ -f requirements.txt ]; then pip install -r requirements.txt; fi
```

Dependencias instaladas:
- **pytest**: Framework de testing
- **pytest-cov**: Plugin de cobertura de código
- **requests**: Cliente HTTP
- **pandas**: Manipulación de datos
- **jsonschema**: Validación de esquemas JSON
- **hypothesis**: Property-based testing
- **pyspark**: Procesamiento distribuido
- **boto3**: SDK de AWS
- **apache-airflow**: Orquestación de workflows

#### 4. Ejecución de Tests con Cobertura
```yaml
- name: Test with pytest and generate coverage
  env:
    PYTHONPATH: ${{ github.workspace }}:${{ github.workspace }}/max/polling:${{ github.workspace }}/max/polling/src
  run: |
    pytest max/polling/test_localstack_with_real_api.py --cov=max/polling/src --cov-report=xml:coverage.xml --junitxml=nosetests.xml
  continue-on-error: true
```

Características clave:
- **PYTHONPATH**: Configura rutas para importar módulos desde `max/polling` y `max/polling/src`
- **Test específico**: Ejecuta solo `test_localstack_with_real_api.py` para validación de integración
- **--cov=max/polling/src**: Mide cobertura del código fuente en `max/polling/src`
- **--cov-report=xml**: Genera reporte XML para SonarCloud
- **--junitxml**: Genera reporte de tests en formato JUnit
- **continue-on-error: true**: Permite que SonarCloud reciba reportes incluso si tests fallan

#### 5. Análisis de SonarCloud
```yaml
- name: SonarCloud Scan
  uses: SonarSource/sonarcloud-github-action@master
  env:
    GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
    SONAR_TOKEN: ${{ secrets.SONAR_TOKEN }}
```

Variables de entorno requeridas:
- **GITHUB_TOKEN**: Token automático de GitHub Actions
- **SONAR_TOKEN**: Token de autenticación de SonarCloud (configurado en secrets)

## Configuración de SonarCloud

### Archivo: `sonar-project.properties`

```properties
# Identificadores del proyecto
sonar.projectKey=mduran-bot_proyecto_cenco_replica
sonar.organization=mduran-bot

# Reportes de cobertura y tests
sonar.python.coverage.reportPaths=coverage.xml
sonar.python.xunit.reportPath=nosetests.xml

# Organización del análisis
sonar.sources=.
sonar.tests=max/polling/
sonar.exclusions=**/venv/**, **/tests/**
```

### Parámetros de Configuración

#### Identificadores
- **sonar.projectKey**: Identificador único del proyecto en SonarCloud
- **sonar.organization**: Organización en SonarCloud

#### Reportes
- **sonar.python.coverage.reportPaths**: Ruta al reporte de cobertura XML
- **sonar.python.xunit.reportPath**: Ruta al reporte de tests JUnit

#### Análisis de Código
- **sonar.sources**: Directorio raíz del código fuente (`.` = todo el proyecto)
- **sonar.tests**: Directorio donde están los tests (`max/polling/`)
- **sonar.exclusions**: Archivos/directorios excluidos del análisis
  - `**/venv/**`: Entornos virtuales de Python
  - `**/tests/**`: Archivos de test (no se analizan como código fuente)

## Métricas Analizadas

SonarCloud analiza automáticamente:

### Calidad de Código
- **Code Smells**: Problemas de mantenibilidad
- **Technical Debt**: Tiempo estimado para resolver issues
- **Duplicación**: Código duplicado
- **Complejidad Ciclomática**: Complejidad de funciones

### Seguridad
- **Vulnerabilidades**: Problemas de seguridad conocidos
- **Security Hotspots**: Código sensible que requiere revisión
- **Security Rating**: Calificación de seguridad (A-E)

### Confiabilidad
- **Bugs**: Errores potenciales en el código
- **Reliability Rating**: Calificación de confiabilidad (A-E)

### Cobertura de Tests
- **Coverage**: Porcentaje de código cubierto por tests
- **Line Coverage**: Líneas ejecutadas por tests
- **Branch Coverage**: Ramas de decisión cubiertas

## Configuración de Secrets en GitHub

Para que el workflow funcione, se deben configurar los siguientes secrets en GitHub:

1. Ir a **Settings** → **Secrets and variables** → **Actions**
2. Agregar los siguientes secrets:

### SONAR_TOKEN
- Obtener desde SonarCloud:
  1. Ir a [SonarCloud](https://sonarcloud.io)
  2. **My Account** → **Security** → **Generate Token**
  3. Copiar el token generado
  4. Agregarlo como secret en GitHub con nombre `SONAR_TOKEN`

### GITHUB_TOKEN
- Este token se genera automáticamente por GitHub Actions
- No requiere configuración manual

## Visualización de Resultados

### En GitHub Actions
1. Ir a la pestaña **Actions** del repositorio
2. Seleccionar el workflow **SonarQube Cloud Analysis**
3. Ver los resultados de cada ejecución

### En SonarCloud
1. Acceder a [SonarCloud](https://sonarcloud.io)
2. Navegar al proyecto `mduran-bot_proyecto_cenco_replica`
3. Ver dashboards con:
   - Métricas de calidad
   - Cobertura de tests
   - Issues detectados
   - Tendencias históricas

## Integración con Pull Requests

SonarCloud comenta automáticamente en los PRs con:
- **Quality Gate Status**: Aprobado/Fallido
- **New Issues**: Problemas introducidos en el PR
- **Coverage Changes**: Cambios en cobertura de código
- **Duplications**: Código duplicado nuevo

## Mejores Prácticas

### Para Desarrolladores
1. **Ejecutar tests localmente** antes de hacer push
2. **Revisar comentarios de SonarCloud** en PRs
3. **Resolver issues críticos** antes de merge
4. **Mantener cobertura** de tests por encima del umbral

### Para el Proyecto
1. **Configurar Quality Gates** apropiados en SonarCloud
2. **Definir umbrales** de cobertura mínima
3. **Revisar regularmente** el Technical Debt
4. **Actualizar exclusiones** según sea necesario

## Troubleshooting

### Tests Fallan pero Workflow Continúa
- Esto es intencional (`continue-on-error: true`)
- Permite que SonarCloud reciba reportes incluso con tests fallidos
- Los tests fallidos se reportan en SonarCloud

### Error de Autenticación en SonarCloud
- Verificar que `SONAR_TOKEN` esté configurado correctamente
- Regenerar token en SonarCloud si es necesario
- Verificar que el token tenga permisos suficientes

### Módulos No Encontrados en Tests
- Verificar configuración de `PYTHONPATH` en el workflow
- Asegurar que las rutas incluyan `max/polling` y `max/polling/src`
- Revisar estructura de imports en el código (debe importar desde `src` y `api_client`)

### Cobertura No Se Reporta
- Verificar que `coverage.xml` se genere correctamente
- Revisar ruta en `sonar-project.properties`
- Asegurar que pytest-cov esté instalado

## Mantenimiento

### Actualización de Dependencias
Revisar y actualizar regularmente:
- Versión de Python en el workflow
- Versiones de dependencias pip
- Versión de actions (checkout, setup-python)
- Versión de sonarcloud-github-action

### Revisión de Configuración
Periódicamente revisar:
- Exclusiones en `sonar-project.properties`
- Umbrales de Quality Gates en SonarCloud
- Configuración de PYTHONPATH según estructura del proyecto

## Referencias

- [SonarCloud Documentation](https://docs.sonarcloud.io/)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [pytest-cov Documentation](https://pytest-cov.readthedocs.io/)
- [SonarQube Python Analysis](https://docs.sonarqube.org/latest/analysis/languages/python/)
