# Integración de SonarQube Cloud Analysis con GitHub Actions

## Descripción General

Este documento describe la configuración de SonarQube Cloud para análisis automático de calidad de código y cobertura de pruebas en el proyecto Janis-Cencosud Integration. El análisis se ejecuta automáticamente en cada push a la rama `main` y en cada pull request.

## Componentes de la Integración

### 1. GitHub Actions Workflow (`.github/workflows/sonar.yml`)

El workflow automatiza el proceso de testing y análisis de código con los siguientes pasos:

#### Configuración del Entorno
- **Sistema Operativo**: Ubuntu Latest
- **Python**: 3.10
- **Checkout**: Fetch completo del historial de Git (necesario para análisis de blame)

#### Instalación de Dependencias
El workflow instala las siguientes dependencias:

```bash
# Herramientas de testing
pip install pytest pytest-cov

# Dependencias del proyecto
pip install pyspark boto3

# Dependencias adicionales desde requirements.txt (si existe)
if [ -f requirements.txt ]; then pip install -r requirements.txt; fi
```

**Dependencias Clave**:
- `pytest`: Framework de testing para Python
- `pytest-cov`: Plugin de cobertura de código para pytest
- `pyspark`: Requerido para jobs de AWS Glue y transformaciones ETL
- `boto3`: SDK de AWS para Python, usado en Lambda functions y scripts

#### Ejecución de Tests y Generación de Reportes

```bash
pytest --cov=. --cov-report=xml:coverage.xml --junitxml=nosetests.xml
```

**Parámetros**:
- `--cov=.`: Mide cobertura de toda la carpeta actual
- `--cov-report=xml:coverage.xml`: Genera reporte de cobertura en formato XML para SonarCloud
- `--junitxml=nosetests.xml`: Genera reporte de resultados de tests en formato JUnit

#### Análisis de SonarCloud

Utiliza la acción oficial de SonarSource para enviar los reportes generados:

```yaml
- name: SonarCloud Scan
  uses: SonarSource/sonarcloud-github-action@master
  env:
    GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
    SONAR_TOKEN: ${{ secrets.SONAR_TOKEN }}
```

**Tokens Requeridos**:
- `GITHUB_TOKEN`: Token automático de GitHub (proporcionado por GitHub Actions)
- `SONAR_TOKEN`: Token de autenticación de SonarCloud (configurado manualmente en GitHub Secrets)

### 2. Configuración de SonarCloud (`sonar-project.properties`)

#### Identificadores del Proyecto

```properties
sonar.projectKey=mduran-bot_proyecto_cenco_replica
sonar.organization=mduran-bot
```

Estos valores deben coincidir exactamente con la configuración en el panel de SonarCloud.

#### Configuración de Reportes

```properties
sonar.python.coverage.reportPaths=coverage.xml
sonar.python.xunit.reportPath=nosetests.xml
```

Especifica la ubicación de los reportes generados por pytest para que SonarCloud pueda procesarlos.

#### Organización del Análisis

```properties
sonar.sources=.
sonar.tests=max/polling/
sonar.exclusions=**/venv/**, **/tests/**
```

**Configuración**:
- `sonar.sources=.`: Analiza todo el código en la raíz del proyecto
- `sonar.tests=max/polling/`: Indica la ubicación de los archivos de prueba
- `sonar.exclusions`: Excluye directorios que no deben analizarse como código fuente:
  - `**/venv/**`: Entornos virtuales de Python
  - `**/tests/**`: Archivos de test (se analizan por separado)

## Triggers del Workflow

### Push a Main
El análisis se ejecuta automáticamente cada vez que se hace push a la rama `main`:

```yaml
on:
  push:
    branches: [ main ]
```

### Pull Requests
El análisis también se ejecuta en pull requests para detectar problemas antes del merge:

```yaml
on:
  pull_request:
    types: [opened, synchronize, reopened]
```

## Configuración de Secretos en GitHub

### Paso 1: Obtener SONAR_TOKEN

1. Acceder a [SonarCloud](https://sonarcloud.io/)
2. Navegar a **My Account** → **Security**
3. Generar un nuevo token con permisos de análisis
4. Copiar el token generado

### Paso 2: Configurar Secret en GitHub

1. Ir al repositorio en GitHub
2. Navegar a **Settings** → **Secrets and variables** → **Actions**
3. Hacer clic en **New repository secret**
4. Nombre: `SONAR_TOKEN`
5. Valor: Pegar el token copiado de SonarCloud
6. Guardar el secret

## Métricas Analizadas

SonarCloud proporciona análisis de las siguientes métricas:

### Calidad de Código
- **Bugs**: Errores que pueden causar comportamiento incorrecto
- **Vulnerabilities**: Problemas de seguridad
- **Code Smells**: Problemas de mantenibilidad
- **Technical Debt**: Tiempo estimado para resolver todos los code smells

### Cobertura de Tests
- **Coverage**: Porcentaje de líneas cubiertas por tests
- **Line Coverage**: Cobertura por línea de código
- **Branch Coverage**: Cobertura de ramas condicionales

### Duplicación
- **Duplicated Lines**: Porcentaje de líneas duplicadas
- **Duplicated Blocks**: Bloques de código duplicados

### Complejidad
- **Cyclomatic Complexity**: Complejidad ciclomática del código
- **Cognitive Complexity**: Complejidad cognitiva (qué tan difícil es entender el código)

## Interpretación de Resultados

### Quality Gate
SonarCloud evalúa el código contra un "Quality Gate" que define umbrales mínimos de calidad:

- ✅ **Passed**: El código cumple con todos los criterios de calidad
- ❌ **Failed**: El código no cumple con uno o más criterios

### Ratings
Cada categoría recibe una calificación de A (mejor) a E (peor):

- **A**: Excelente
- **B**: Bueno
- **C**: Aceptable
- **D**: Necesita mejora
- **E**: Crítico

## Integración con Pull Requests

Cuando se crea o actualiza un pull request:

1. GitHub Actions ejecuta el workflow automáticamente
2. Se ejecutan todos los tests con cobertura
3. Los resultados se envían a SonarCloud
4. SonarCloud comenta en el PR con:
   - Estado del Quality Gate
   - Nuevos bugs, vulnerabilities o code smells introducidos
   - Cambios en la cobertura de código
   - Link al análisis completo

## Troubleshooting

### Error: "SONAR_TOKEN not found"
**Solución**: Verificar que el secret `SONAR_TOKEN` esté configurado correctamente en GitHub Settings.

### Error: "Project key does not match"
**Solución**: Verificar que `sonar.projectKey` y `sonar.organization` en `sonar-project.properties` coincidan con la configuración en SonarCloud.

### Error: "Coverage report not found"
**Solución**: 
1. Verificar que pytest se ejecute correctamente
2. Confirmar que `coverage.xml` se genere en la raíz del proyecto
3. Revisar que la ruta en `sonar.python.coverage.reportPaths` sea correcta

### Tests Fallan en CI pero Pasan Localmente
**Posibles Causas**:
1. Dependencias faltantes en el workflow
2. Diferencias de versión de Python
3. Variables de entorno no configuradas

**Solución**: 
- Agregar las dependencias faltantes al paso "Install dependencies"
- Verificar que la versión de Python coincida
- Configurar variables de entorno necesarias en el workflow

### Error: "Import Error: No module named 'pyspark'"
**Solución**: Ya resuelto en la última versión del workflow. El paso de instalación ahora incluye:
```bash
pip install pyspark boto3
```

## Mejores Prácticas

### 1. Mantener Alta Cobertura de Tests
- Objetivo: >80% de cobertura de código
- Escribir tests para todo código nuevo
- Priorizar tests para lógica de negocio crítica

### 2. Resolver Issues Rápidamente
- Revisar y resolver bugs y vulnerabilities inmediatamente
- Abordar code smells en refactorings planificados
- No ignorar warnings sin justificación

### 3. Revisar Análisis en PRs
- Verificar que el Quality Gate pase antes de merge
- Revisar nuevos issues introducidos
- Mantener o mejorar la cobertura de código

### 4. Configurar Exclusiones Apropiadas
- Excluir código generado automáticamente
- Excluir dependencias de terceros
- No excluir código de producción sin justificación

## Recursos Adicionales

- [SonarCloud Documentation](https://docs.sonarcloud.io/)
- [SonarQube Python Analysis](https://docs.sonarqube.org/latest/analysis/languages/python/)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [pytest Documentation](https://docs.pytest.org/)
- [pytest-cov Documentation](https://pytest-cov.readthedocs.io/)

## Historial de Cambios

### 2026-03-03
- ✅ Agregada instalación de PySpark y boto3 en el workflow
- ✅ Mejorados comentarios en el workflow para mayor claridad
- ✅ Documentación inicial creada

## Contacto y Soporte

Para problemas con la configuración de SonarCloud o el workflow de CI/CD, contactar al equipo de DevOps o abrir un issue en el repositorio.
