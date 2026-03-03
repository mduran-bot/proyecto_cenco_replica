# 📚 Índice de Documentación - Sistema de API Polling

**Fecha:** Febrero 24, 2026  
**Versión:** 1.0  
**Estado:** Completo

---

## 🎯 Propósito de esta Documentación

Esta carpeta contiene la documentación completa del Sistema de API Polling Multi-Tenant para la integración Janis-Cencosud. Los documentos están organizados para facilitar tanto el entendimiento del sistema como su deployment a producción.

---

## 📖 Documentos Disponibles

### 1. Sistema de API Polling
**Archivo:** `01-SISTEMA_API_POLLING.md`

**Contenido:**
- ✅ Resumen ejecutivo del sistema
- ✅ Arquitectura completa con diagramas
- ✅ Componentes principales (StateManager, APIClient, etc.)
- ✅ Flujo de datos end-to-end
- ✅ Implementación multi-tenant
- ✅ Configuración y endpoints soportados
- ✅ Métricas y monitoreo

**Cuándo leer:**
- Para entender qué hace el sistema
- Para conocer la arquitectura
- Para entender cómo funcionan los componentes
- Como referencia técnica general

**Audiencia:** Desarrolladores, arquitectos, equipo técnico

---

### 2. Guía de Tests
**Archivo:** `02-GUIA_TESTS.md`

**Contenido:**
- ✅ Resumen de tests disponibles
- ✅ Configuración del entorno de testing
- ✅ Tests unitarios, integración y end-to-end
- ✅ Ejecución de tests con LocalStack
- ✅ Datos mock y MockAPIClient
- ✅ Troubleshooting de tests
- ✅ Validación de componentes

**Cuándo leer:**
- Antes de ejecutar tests
- Para validar cambios en el código
- Para entender qué se está probando
- Para troubleshooting de tests fallidos

**Audiencia:** Desarrolladores, QA, equipo de testing

---

### 3. Configuración para Producción
**Archivo:** `03-CONFIGURACION_PRODUCCION.md`

**Contenido:**
- ✅ Cambios requeridos por carpeta
- ✅ Configuración de EventBridge (IMPORTANTE)
- ✅ Configuración de MWAA (Airflow)
- ✅ Configuración de Terraform
- ✅ Variables de entorno y secrets
- ✅ Checklist completo de deployment
- ✅ Consideraciones de seguridad

**Cuándo leer:**
- Antes de hacer deployment a producción
- Para configurar EventBridge
- Para entender diferencias entre testing y producción
- Como guía de deployment paso a paso

**Audiencia:** DevOps, SRE, equipo de deployment

---

### 4. Deployment en Producción ⭐ NUEVO
**Archivo:** `04-DEPLOYMENT_PRODUCCION.md`

**Contenido:**
- ✅ Prerequisitos completos (roles IAM, secrets)
- ✅ Configuración detallada de roles IAM
- ✅ Configuración de Secrets Manager
- ✅ Deployment paso a paso con Terraform
- ✅ Configuración post-deployment
- ✅ Verificación y monitoreo
- ✅ Multi-tenant: agregar nuevos clientes
- ✅ Troubleshooting exhaustivo

**Cuándo leer:**
- ANTES de hacer deployment (obligatorio)
- Para crear roles IAM necesarios
- Para configurar secrets correctamente
- Para entender el proceso completo
- Para agregar nuevos clientes (Metro)

**Audiencia:** DevOps, SRE, administradores AWS, equipo de deployment

---

## 🗺️ Guía de Lectura por Rol

### Para Desarrolladores Nuevos

**Orden recomendado:**
1. `01-SISTEMA_API_POLLING.md` - Entender el sistema
2. `02-GUIA_TESTS.md` - Ejecutar tests localmente
3. `03-CONFIGURACION_PRODUCCION.md` - Entender deployment

**Tiempo estimado:** 2-3 horas

---

### Para DevOps/SRE

**Orden recomendado:**
1. `03-CONFIGURACION_PRODUCCION.md` - Configuración de producción
2. `01-SISTEMA_API_POLLING.md` - Arquitectura y componentes
3. `02-GUIA_TESTS.md` - Validación de deployment

**Tiempo estimado:** 1-2 horas

---

### Para QA/Testing

**Orden recomendado:**
1. `02-GUIA_TESTS.md` - Guía completa de tests
2. `01-SISTEMA_API_POLLING.md` - Entender qué se está probando
3. `03-CONFIGURACION_PRODUCCION.md` - Diferencias con producción

**Tiempo estimado:** 1-2 horas

---

### Para Arquitectos/Tech Leads

**Orden recomendado:**
1. `01-SISTEMA_API_POLLING.md` - Arquitectura completa
2. `03-CONFIGURACION_PRODUCCION.md` - Deployment y configuración
3. `02-GUIA_TESTS.md` - Estrategia de testing

**Tiempo estimado:** 2-3 horas

---

## 🚀 Quick Start por Escenario

### Escenario 1: "Quiero ejecutar tests localmente"

**Documentos:**
- `02-GUIA_TESTS.md` → Sección "Ejecución de Tests"

**Pasos rápidos:**
```bash
cd max/polling
docker-compose up -d
python test_localstack_real_api.py
```

**Tiempo:** 5 minutos

---

### Escenario 2: "Quiero entender cómo funciona el sistema"

**Documentos:**
- `01-SISTEMA_API_POLLING.md` → Secciones "Arquitectura" y "Componentes"

**Conceptos clave:**
- EventBridge dispara DAGs
- MWAA orquesta el flujo
- DynamoDB gestiona locks
- Multi-tenant con headers

**Tiempo:** 30 minutos

---

### Escenario 3: "Quiero hacer deployment a producción"

**Documentos:**
- `04-DEPLOYMENT_PRODUCCION.md` → Todo el documento (NUEVO)
- `03-CONFIGURACION_PRODUCCION.md` → Configuraciones específicas
- `01-SISTEMA_API_POLLING.md` → Sección "Configuración"

**Checklist:**
- [ ] Leer documento 04 completo
- [ ] Crear roles IAM (MWAA + EventBridge)
- [ ] Crear secrets en Secrets Manager
- [ ] Actualizar prod.tfvars con ARNs
- [ ] Ejecutar Terraform
- [ ] Subir DAGs a MWAA
- [ ] Configurar variables en Airflow
- [ ] Activar DAGs
- [ ] Validar deployment

**Tiempo:** 4-6 horas (primera vez)

---

### Escenario 4: "Tengo un problema con tests"

**Documentos:**
- `02-GUIA_TESTS.md` → Sección "Troubleshooting"

**Problemas comunes:**
- LocalStack no corriendo → `docker-compose up -d`
- Dependencias faltantes → `pip install -r requirements.txt`
- Tabla no encontrada → Reiniciar LocalStack

**Tiempo:** 10-15 minutos

---

## 📊 Resumen de Contenido

### Arquitectura y Diseño

| Tema | Documento | Sección |
|------|-----------|---------|
| Arquitectura general | 01 | Arquitectura del Sistema |
| Componentes core | 01 | Componentes Principales |
| Flujo de datos | 01 | Flujo de Datos |
| Multi-tenant | 01 | Multi-Tenant |

### Testing y Validación

| Tema | Documento | Sección |
|------|-----------|---------|
| Setup de tests | 02 | Configuración del Entorno |
| Ejecutar tests | 02 | Ejecución de Tests |
| Datos mock | 02 | Datos Mock |
| Troubleshooting | 02 | Troubleshooting |

### Deployment y Producción

| Tema | Documento | Sección |
|------|-----------|---------|
| Cambios por carpeta | 03 | Cambios Requeridos |
| EventBridge | 03 | Configuración de EventBridge |
| MWAA | 03 | Configuración de MWAA |
| Secrets | 03 | Credenciales y Secrets |
| Checklist | 03 | Checklist de Deployment |

---

## 🔍 Búsqueda Rápida

### Por Componente

| Componente | Documento | Página |
|------------|-----------|--------|
| StateManager | 01 | Componentes → StateManager |
| JanisAPIClient | 01 | Componentes → JanisAPIClient |
| PaginationHandler | 01 | Componentes → PaginationHandler |
| DataValidator | 01 | Componentes → DataValidator |
| DataEnricher | 01 | Componentes → DataEnricher |
| EventBridge | 03 | Configuración de EventBridge |
| MWAA | 03 | Configuración de MWAA |

### Por Tarea

| Tarea | Documento | Sección |
|-------|-----------|---------|
| Ejecutar tests | 02 | Ejecución de Tests |
| Configurar EventBridge | 03 | Configuración de EventBridge |
| Configurar MWAA | 03 | Configuración de MWAA |
| Configurar Terraform | 03 | Configuración de Terraform |
| Configurar Secrets | 03 | Credenciales y Secrets |
| Troubleshooting tests | 02 | Troubleshooting |

### Por Concepto

| Concepto | Documento | Sección |
|----------|-----------|---------|
| Multi-tenant | 01 | Multi-Tenant |
| Polling incremental | 01 | IncrementalPolling |
| Rate limiting | 01 | JanisAPIClient |
| Circuit breaker | 01 | PaginationHandler |
| Locks distribuidos | 01 | StateManager |
| Datos mock | 02 | Datos Mock |

---

## 📝 Notas Importantes

### ⚠️ EventBridge en Carpeta Separada

**CRÍTICO**: EventBridge NO está en `max/polling/terraform/`. Está en el proyecto principal de Terraform de Cencosud.

**Ubicación típica:**
```
terraform/
├── modules/
│   └── eventbridge/    # ← EventBridge aquí
└── main.tf
```

**Ver:** `03-CONFIGURACION_PRODUCCION.md` → Sección "Configuración de EventBridge"

---

### ✅ Tests Usan Datos Mock

Los tests NO requieren credenciales de API real. Usan `MockAPIClient` con datos locales JSON.

**Ventajas:**
- No requiere credenciales
- Tests más rápidos
- No consume cuota de API
- Resultados predecibles

**Ver:** `02-GUIA_TESTS.md` → Sección "Datos Mock"

---

### 🔐 Credenciales en Secrets Manager

En producción, NUNCA hardcodear credenciales. Usar AWS Secrets Manager.

**Secrets requeridos:**
- `prod/janis/api-key`
- `prod/janis/api-secret`

**Ver:** `03-CONFIGURACION_PRODUCCION.md` → Sección "Credenciales y Secrets"

---

## 🎓 Recursos Adicionales

### Documentación Técnica Adicional

Además de estos 3 documentos principales, existen otros documentos en el proyecto:

| Documento | Ubicación | Propósito |
|-----------|-----------|-----------|
| README principal | `max/polling/README.md` | Overview general |
| README de DAGs | `max/polling/dags/README.md` | Documentación de DAGs |
| README de src | `max/polling/src/README.md` | Documentación de módulos |
| Tests summary | `max/polling/TESTS_READY_SUMMARY.md` | Resumen de tests |
| Flow diagram | `max/polling/TEST_FLOW_DIAGRAM.md` | Diagramas de flujo |

### Especificaciones Técnicas

| Documento | Ubicación | Propósito |
|-----------|-----------|-----------|
| Tasks | `.kiro/specs/api-polling-system/tasks.md` | Plan de implementación |
| Requirements | `.kiro/specs/api-polling-system/requirements.md` | Requerimientos |

---

## 📞 Contacto y Soporte

### Para Preguntas Técnicas

1. **Revisar documentación** en este índice
2. **Buscar en sección específica** del documento relevante
3. **Consultar troubleshooting** en documento 02
4. **Contactar equipo** de Data Engineering

### Para Problemas en Producción

1. **Revisar CloudWatch Logs**
2. **Verificar estado en DynamoDB**
3. **Consultar documento 03** → Troubleshooting
4. **Escalar a on-call** si es crítico

---

## ✅ Checklist de Lectura

### Para Desarrolladores

- [ ] Leído documento 01 completo
- [ ] Ejecutado tests localmente (documento 02)
- [ ] Entendido diferencias con producción (documento 03)
- [ ] Revisado código fuente en `src/`
- [ ] Revisado DAGs en `dags/`

### Para DevOps

- [ ] Leído documento 03 completo
- [ ] Entendido configuración de EventBridge
- [ ] Entendido configuración de MWAA
- [ ] Revisado Terraform en `terraform/`
- [ ] Entendido gestión de secrets

### Para QA

- [ ] Leído documento 02 completo
- [ ] Ejecutado todos los tests
- [ ] Entendido datos mock
- [ ] Validado componentes
- [ ] Documentado casos de prueba

---

## 🎉 Conclusión

Esta documentación proporciona todo lo necesario para:

✅ **Entender** el sistema de polling  
✅ **Ejecutar** tests localmente  
✅ **Deployar** a producción  
✅ **Mantener** el sistema operando  
✅ **Troubleshoot** problemas comunes  

**Tiempo total de lectura:** 4-6 horas (lectura completa)  
**Tiempo para quick start:** 30 minutos (lectura selectiva)

---

**Última actualización:** Febrero 24, 2026  
**Autor:** Equipo de Integración Janis-Cencosud  
**Versión:** 1.0  
**Estado:** ✅ Completo y Validado
