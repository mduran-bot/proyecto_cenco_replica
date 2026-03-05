# Documentación General - Janis-Cencosud Integration

Esta carpeta contiene toda la documentación general del proyecto que no está específicamente vinculada a un spec individual.

## Índice de Documentación

### Arquitectura y Diseño
- **Documento Detallado de Diseño Janis-Cenco.md**: Diseño completo del sistema de integración
- **Diagrama arquitectura.md**: Diagramas de arquitectura del sistema
- **Diagrama Arquitectura Mermaid - Resumen.md**: Diagramas en formato Mermaid
- **diagrama-mermaid.md**: Diagramas adicionales en Mermaid
- **Diagrama de Infraestructura - Resumen.md**: Resumen de la infraestructura
- **diagrama-infraestructura-terraform.md**: Diagramas de infraestructura Terraform
- **diagrama.md**: Diagramas generales del proyecto
- **API_POLLING_SYSTEM_REQUIREMENTS_UPDATE.md**: Actualización de requerimientos del sistema de polling ⭐ NUEVO

### Deployment y Configuración
- **GUIA_DEPLOYMENT_CENCOSUD.md**: Guía completa de deployment
- **Guía de Deployment Cencosud - Resumen.md**: Resumen de deployment
- **Guía de Validación y Deployment.md**: Validación pre-deployment
- **DEPLOYMENT_SUCCESS_SUMMARY.md**: Resumen de deployments exitosos
- **Configuración de Ambientes - Producción.md**: Configuración de ambiente productivo
- **Configuración terraform.tfvars - Resumen.md**: Configuración de variables Terraform
- **Validación de Código Terraform - Resumen.md**: Validación de código IaC

### Configuración del Cliente
- **CONFIGURACION_CLIENTE.md**: Configuración específica del cliente
- **Configuración del Cliente - Resumen.md**: Resumen de configuración
- **GUIA_LANDING_ZONE_CLIENTE.md**: Guía de Landing Zone
- **Configuración Landing Zone - Resumen.md**: Resumen de Landing Zone
- **ENTREGA_CLIENTE_README.md**: README para entrega al cliente
- **Entrega al Cliente - Resumen.md**: Resumen de entrega

### Guías de Proyecto
- **Guia proyecto Terraform Cencosud.md**: Guía completa del proyecto Terraform
- **Guía Proyecto Terraform Cencosud - Resumen.md**: Resumen de la guía
- **README-Cenco.md**: README principal del proyecto Cencosud
- **DOCUMENTACION.md**: Índice de documentación

### Integración y Módulos
- **INTEGRACION_COMPLETA_RESUMEN.md**: Resumen de integración completa
- **DATA_PIPELINE_MODULES_SUMMARY.md**: Resumen de módulos del pipeline
- **Integración Módulos Data Pipeline - Resumen.md**: Integración de módulos
- **EVENTBRIDGE_MWAA_INTEGRATION_IMPROVEMENT.md**: Mejoras de integración EventBridge-MWAA
- **Comparacion API v1 a v2.pdf**: Comparación de versiones de API

### LocalStack y Testing
- **GUIA_LOCALSTACK.md**: Guía de uso de LocalStack
- **GUIA_INICIO_LOCALSTACK.md**: Inicio rápido con LocalStack

### GitLab y CI/CD
- **GITLAB_PREPARATION.md**: Preparación para GitLab
- **Preparación para GitLab - Resumen.md**: Resumen de preparación

### Permisos y Seguridad
- **INVENTARIO_Y_PERMISOS_AWS.md**: Inventario de recursos y permisos AWS

### Instrucciones de Entrega
- **INSTRUCCIONES_PARA_ENVIO.md**: Instrucciones para envío al cliente
- **ACCIONES_FINALES_ANTES_DE_ENVIAR.md**: Checklist final antes de entrega

### Actualizaciones
- **Actualización Referencias Líneas - 2026-02-03.md**: Actualizaciones de referencias

## Documentación por Spec

La documentación específica de cada spec se encuentra en las carpetas correspondientes. Cada carpeta de spec contiene su propio README.md con índice de documentación:

- `.kiro/specs/01-aws-infrastructure/docs/` - Infraestructura AWS (VPC, Security Groups, EventBridge, WAF)
  - Ver [README.md](.kiro/specs/01-aws-infrastructure/docs/README.md) para índice completo
- `.kiro/specs/02-initial-data-load/docs/` - Carga inicial de datos desde MySQL a Redshift
  - Incluye análisis de esquema Redshift y mapeo detallado
- `.kiro/specs/api-polling-system/docs/` - Sistema de polling de API con EventBridge + MWAA
- `.kiro/specs/data-transformation/docs/` - Transformación de datos ETL (Bronze/Silver/Gold)
- `.kiro/specs/monitoring-alerting/docs/` - Monitoreo y alertas con CloudWatch
- `.kiro/specs/redshift-loading/docs/` - Carga incremental a Redshift
- `.kiro/specs/webhook-ingestion/docs/` - Ingesta de webhooks en tiempo real

## Documentación de Stored Procedures

La carpeta `Documentacion/` también contiene documentación de stored procedures SQL:
- sp_alerta_mayorista.txt
- sp_ejecutar_ods_picking_ecommerce.txt
- sp_genera_fact_publicaciones_ecommerce.txt
- sp_genera_operaciones_hoy.txt
- sp_genera_operaciones_leadtime.txt
- sp_genera_operaciones_micro_macro.txt
- sp_genera_tbl_analitica_liquidaciones_eco.txt
- sp_quiebres_ecommerce_hoy_pickeados.txt
- sp_reporte_quiebres_ecommmerce_tipologia.txt
- sp_ubicacion_pedidos_ecommerce.txt
- sp_venta_online_metro_almacenes.txt
- venta_ingresada_vtex_diario.txt
- indicadores_prime_region_semana.txt
- promociones_ecommerce_vtex.txt
