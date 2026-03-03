# Índice de Documentación - Infraestructura AWS

Este documento proporciona un índice completo de toda la documentación disponible para la infraestructura AWS del proyecto Janis-Cencosud.

## 📚 Documentación Principal

### 🚀 Deployment y Configuración

| Documento | Descripción | Audiencia |
|-----------|-------------|-----------|
| **[../GUIA_COMPARTIR_PROYECTO.md](../GUIA_COMPARTIR_PROYECTO.md)** | ⭐ **Guía completa para nuevos usuarios** - Cómo ejecutar el proyecto | Nuevos usuarios |
| **[../AWS_INFRASTRUCTURE_VALIDATION_REPORT.md](../AWS_INFRASTRUCTURE_VALIDATION_REPORT.md)** | ⭐ **Reporte de validación de infraestructura** - 71 recursos, 93.75% compliance | Todos |
| **[DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md)** | ⭐ **Guía rápida de deployment** - Pasos simplificados para desplegar | Todos |
| [README.md](./README.md) | Documentación principal del proyecto Terraform | Todos |
| [environments/README.md](./environments/README.md) | Guía completa de configuración por ambiente | DevOps |
| [environments/QUICK_START.md](./environments/QUICK_START.md) | Comandos rápidos para deployment | DevOps |
| [environments/CONFIGURATION_SUMMARY.md](./environments/CONFIGURATION_SUMMARY.md) | Resumen de configuraciones por ambiente | DevOps |

### ✅ Validación y Testing

| Documento | Descripción | Audiencia |
|-----------|-------------|-----------|
| **[../AWS_INFRASTRUCTURE_VALIDATION_REPORT.md](../AWS_INFRASTRUCTURE_VALIDATION_REPORT.md)** | ⭐ **Reporte completo de validación** - Infraestructura desplegada en AWS | Todos |
| **[../VALIDATION_SUMMARY.md](../VALIDATION_SUMMARY.md)** | ⭐ **Resumen ejecutivo de validación** - 93.75% compliance | Management |
| [VALIDATION_SUMMARY.md](./VALIDATION_SUMMARY.md) | Estado de validación de todos los módulos | DevOps/QA |
| [test/VALIDATION_GUIDE.md](./test/VALIDATION_GUIDE.md) | Guía detallada de validación sin deployment | DevOps/QA |
| [QUICK_VALIDATION.md](./QUICK_VALIDATION.md) | Referencia rápida de validación | DevOps |
| [test/README.md](./test/README.md) | Documentación de tests automatizados | QA/Dev |
| [test/TESTING_GUIDE.md](./test/TESTING_GUIDE.md) | Guía completa de testing | QA/Dev |

### 🔧 Scripts y Automatización

| Documento | Descripción | Audiencia |
|-----------|-------------|-----------|
| [scripts/README.md](./scripts/README.md) | Documentación de scripts de deployment | DevOps |
| [scripts/DEPLOYMENT_SCRIPTS_SUMMARY.md](./scripts/DEPLOYMENT_SCRIPTS_SUMMARY.md) | Resumen de implementación de scripts | DevOps |
| **[../INVENTARIO_Y_PERMISOS_AWS.md](../INVENTARIO_Y_PERMISOS_AWS.md)** | ⭐ **Inventario completo de recursos AWS y análisis de permisos** | DevOps/Security |
| [../Documentación Cenco/Scripts de Inventario AWS - Resumen.md](../Documentación%20Cenco/Scripts%20de%20Inventario%20AWS%20-%20Resumen.md) | Documentación de scripts de inventario | DevOps |

### 🔄 Cambios y Actualizaciones

| Documento | Descripción | Audiencia |
|-----------|-------------|-----------|
| **[../DOCUMENTATION_UPDATE_VALIDATION_SUMMARY.md](../DOCUMENTATION_UPDATE_VALIDATION_SUMMARY.md)** | ⭐ **Resumen de actualización de documentación** - Deployment y validación AWS | Todos |
| [CHANGES_SUMMARY.md](./CHANGES_SUMMARY.md) | Resumen de todos los cambios para AWS deployment | Todos |
| [SECURITY_CHANGES_SUMMARY.md](./SECURITY_CHANGES_SUMMARY.md) | Cambios de seguridad y servicios del cliente | DevOps/Security |
| [VARIABLES_CLEANUP_SUMMARY.md](./VARIABLES_CLEANUP_SUMMARY.md) | Limpieza de variables WAF y actualización de IP ranges | DevOps |
| [TAGGING_UPDATE_SUMMARY.md](./TAGGING_UPDATE_SUMMARY.md) | Actualización de política de etiquetado | DevOps |
| [CORPORATE_TAGGING_IMPLEMENTATION.md](./CORPORATE_TAGGING_IMPLEMENTATION.md) | Implementación de tags corporativos | DevOps |
| [VPC_TAGGING_COMPLETION.md](./VPC_TAGGING_COMPLETION.md) | ✅ Completación del módulo VPC con tags corporativos | DevOps |
| [CLIENT_MANAGED_SERVICES.md](./CLIENT_MANAGED_SERVICES.md) | Servicios manejados por el cliente | Todos |

### 🏗️ Arquitectura y Diseño

| Documento | Descripción | Audiencia |
|-----------|-------------|-----------|
| [MULTI_AZ_EXPANSION.md](./MULTI_AZ_EXPANSION.md) | Guía de expansión a Multi-AZ | Arquitectos |
| [SINGLE_AZ_DEPLOYMENT.md](./SINGLE_AZ_DEPLOYMENT.md) | Documentación de deployment Single-AZ | Arquitectos |
| [DEPLOYMENT_NOTES.md](./DEPLOYMENT_NOTES.md) | Notas sobre módulos activos/deshabilitados | DevOps |

### 📋 Módulos Específicos

| Documento | Descripción | Audiencia |
|-----------|-------------|-----------|
| [modules/vpc/README.md](./modules/vpc/README.md) | Documentación del módulo VPC | DevOps |
| [modules/monitoring/README.md](./modules/monitoring/README.md) | Documentación del módulo de Monitoring | DevOps |
| [modules/tagging/README.md](./modules/tagging/README.md) | Estrategia de tagging | DevOps |
| [modules/tagging/INTEGRATION_GUIDE.md](./modules/tagging/INTEGRATION_GUIDE.md) | Guía de integración de tagging | Dev |

### 🧪 Testing Local

| Documento | Descripción | Audiencia |
|-----------|-------------|-----------|
| **[GUIA_INICIO_LOCALSTACK.md](../GUIA_INICIO_LOCALSTACK.md)** | ⭐ **Guía paso a paso para principiantes** - LocalStack desde cero | Nuevos usuarios |
| **[LOCALSTACK_TROUBLESHOOTING.md](../LOCALSTACK_TROUBLESHOOTING.md)** | ⭐ **Soluciones a problemas comunes** - Errores y fixes | Todos |
| [README-LOCALSTACK.md](../README-LOCALSTACK.md) | Guía de testing con LocalStack | Dev |
| [LOCALSTACK_CONFIG.md](./LOCALSTACK_CONFIG.md) | Documentación de localstack.tfvars | Dev |
| [LOCALSTACK_TAGGING_UPDATE.md](./LOCALSTACK_TAGGING_UPDATE.md) | Actualización de configuración de tagging | Dev |
| [localstack.tfvars](./localstack.tfvars) | Configuración específica para LocalStack | Dev |

## 📖 Documentación en "Documentación Cenco"

| Documento | Descripción | Audiencia |
|-----------|-------------|-----------|
| [Guía de Validación y Deployment.md](../Documentación%20Cenco/Guía%20de%20Validación%20y%20Deployment.md) | Guía completa de validación y deployment | Todos |
| [Infraestructura AWS - Resumen Ejecutivo.md](../Documentación%20Cenco/Infraestructura%20AWS%20-%20Resumen%20Ejecutivo.md) | Resumen ejecutivo de la infraestructura | Management |
| [Especificación Detallada de Infraestructura AWS.md](../Documentación%20Cenco/Especificación%20Detallada%20de%20Infraestructura%20AWS.md) | Especificación técnica completa | Arquitectos |

## 📖 Documentación para Compartir el Proyecto

| Documento | Descripción | Audiencia |
|-----------|-------------|-----------|
| [../GUIA_COMPARTIR_PROYECTO.md](../GUIA_COMPARTIR_PROYECTO.md) | ⭐ Guía completa para ejecutar el proyecto | Receptor del proyecto |
| [../INDICE_COMPARTIR.md](../INDICE_COMPARTIR.md) | Índice de documentación para compartir | Quien comparte |
| [../RESUMEN_COMPARTIR.md](../RESUMEN_COMPARTIR.md) | Resumen ejecutivo del proceso | Quien comparte |
| [../CHECKLIST_COMPARTIR.md](../CHECKLIST_COMPARTIR.md) | Lista de verificación completa | Quien comparte |
| [../TEMPLATE_MENSAJE_COMPARTIR.md](../TEMPLATE_MENSAJE_COMPARTIR.md) | Templates de mensajes | Quien comparte |
| [../scripts/preparar-para-compartir.ps1](../scripts/preparar-para-compartir.ps1) | Script de automatización | Quien comparte |

## 🎯 Guías por Caso de Uso

### "Soy nuevo y recibí este proyecto"
1. ⭐ **[../GUIA_COMPARTIR_PROYECTO.md](../GUIA_COMPARTIR_PROYECTO.md)** - Empieza aquí
2. [README.md](./README.md) - Overview del proyecto
3. [environments/README.md](./environments/README.md) - Configuración de ambientes

### "Quiero desplegar la infraestructura por primera vez"
1. ⭐ **[DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md)** - Empieza aquí
2. [environments/README.md](./environments/README.md) - Configuración de ambientes
3. [scripts/README.md](./scripts/README.md) - Scripts automatizados

### "Quiero ver el estado actual del deployment"
1. ⭐ **[../AWS_INFRASTRUCTURE_VALIDATION_REPORT.md](../AWS_INFRASTRUCTURE_VALIDATION_REPORT.md)** - Reporte completo de validación
2. **[../VALIDATION_SUMMARY.md](../VALIDATION_SUMMARY.md)** - Resumen ejecutivo
3. **[../DOCUMENTATION_UPDATE_VALIDATION_SUMMARY.md](../DOCUMENTATION_UPDATE_VALIDATION_SUMMARY.md)** - Resumen de actualización de documentación

### "Quiero validar sin desplegar"
1. [test/VALIDATION_GUIDE.md](./test/VALIDATION_GUIDE.md) - Guía completa
2. [VALIDATION_SUMMARY.md](./VALIDATION_SUMMARY.md) - Estado actual
3. [QUICK_VALIDATION.md](./QUICK_VALIDATION.md) - Referencia rápida

### "Quiero probar localmente sin AWS"
1. **[GUIA_INICIO_LOCALSTACK.md](../GUIA_INICIO_LOCALSTACK.md)** - Guía paso a paso para principiantes
2. **[LOCALSTACK_TROUBLESHOOTING.md](../LOCALSTACK_TROUBLESHOOTING.md)** - Soluciones a problemas comunes
3. [README-LOCALSTACK.md](../README-LOCALSTACK.md) - Guía de LocalStack
4. [README.md](./README.md) - Sección de LocalStack

### "Quiero expandir a Multi-AZ"
1. [MULTI_AZ_EXPANSION.md](./MULTI_AZ_EXPANSION.md) - Guía de expansión
2. [SINGLE_AZ_DEPLOYMENT.md](./SINGLE_AZ_DEPLOYMENT.md) - Estado actual

### "Quiero ejecutar tests automatizados"
1. [test/README.md](./test/README.md) - Documentación de tests
2. [test/TESTING_GUIDE.md](./test/TESTING_GUIDE.md) - Guía completa
3. [VALIDATION_SUMMARY.md](./VALIDATION_SUMMARY.md) - Resultados

### "Quiero usar los scripts de deployment"
1. [scripts/README.md](./scripts/README.md) - Documentación completa
2. [scripts/DEPLOYMENT_SCRIPTS_SUMMARY.md](./scripts/DEPLOYMENT_SCRIPTS_SUMMARY.md) - Resumen

### "Quiero ver el inventario de recursos AWS"
1. ⭐ **[../INVENTARIO_Y_PERMISOS_AWS.md](../INVENTARIO_Y_PERMISOS_AWS.md)** - Inventario completo y análisis de permisos
2. [../Documentación Cenco/Scripts de Inventario AWS - Resumen.md](../Documentación%20Cenco/Scripts%20de%20Inventario%20AWS%20-%20Resumen.md) - Scripts de inventario
3. [../scripts/inventario-aws-recursos.ps1](../scripts/inventario-aws-recursos.ps1) - Script principal

## 🔍 Búsqueda Rápida por Tema

### Credenciales y Seguridad
- [environments/README.md](./environments/README.md) - Gestión de credenciales
- [environments/CONFIGURATION_SUMMARY.md](./environments/CONFIGURATION_SUMMARY.md) - Seguridad por ambiente
- [scripts/README.md](./scripts/README.md) - Seguridad en scripts

### Costos
- ⭐ [DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md) - Estimación rápida
- [Documentación Cenco/Guía de Validación y Deployment.md](../Documentación%20Cenco/Guía%20de%20Validación%20y%20Deployment.md) - Costos detallados
- [MULTI_AZ_EXPANSION.md](./MULTI_AZ_EXPANSION.md) - Costos Multi-AZ

### Troubleshooting
- [test/VALIDATION_GUIDE.md](./test/VALIDATION_GUIDE.md) - Errores comunes
- [environments/README.md](./environments/README.md) - Troubleshooting de deployment
- [scripts/README.md](./scripts/README.md) - Troubleshooting de scripts

### Inventario y Permisos AWS
- ⭐ **[../INVENTARIO_Y_PERMISOS_AWS.md](../INVENTARIO_Y_PERMISOS_AWS.md)** - Inventario completo de recursos y análisis de permisos
- [../Documentación Cenco/Scripts de Inventario AWS - Resumen.md](../Documentación%20Cenco/Scripts%20de%20Inventario%20AWS%20-%20Resumen.md) - Scripts de inventario
- [../scripts/inventario-aws-recursos.ps1](../scripts/inventario-aws-recursos.ps1) - Script de inventario completo
- [../scripts/inventario-rapido.ps1](../scripts/inventario-rapido.ps1) - Inventario rápido
- [../scripts/inventario-permisos.ps1](../scripts/inventario-permisos.ps1) - Análisis de permisos

### Configuración por Ambiente
- [environments/dev/dev.tfvars](./environments/dev/dev.tfvars) - Desarrollo
- [environments/staging/staging.tfvars](./environments/staging/staging.tfvars) - Staging
- [environments/prod/prod.tfvars](./environments/prod/prod.tfvars) - Producción

## 📝 Notas

- Los documentos marcados con ⭐ son los más importantes para empezar
- Los documentos en **negrita** son guías de inicio rápido
- Todos los paths son relativos al directorio `terraform/`

## 🔄 Última Actualización

**Fecha:** 16 de Febrero de 2026  
**Estado:** Infraestructura desplegada y validada en AWS - 71 recursos operacionales (93.75% compliance)  
**Nuevo:** Inventario completo de recursos AWS y análisis de permisos disponible

---

**¿No encuentras lo que buscas?** Revisa el [README.md](./README.md) principal o contacta al equipo de DevOps.
