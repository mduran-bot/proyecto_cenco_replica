# Diagrama de Infraestructura Terraform - Resumen

**Fecha**: 3 de Febrero, 2026  
**Documento relacionado**: [../diagrama-infraestructura-terraform.md](../diagrama-infraestructura-terraform.md)

---

## Resumen Ejecutivo

Se ha creado un **diagrama visual completo de la infraestructura AWS** implementada con Terraform para el proyecto Janis-Cencosud. Este diagrama proporciona una representación clara y detallada de todos los componentes, módulos y su interconexión.

## Propósito

El diagrama de infraestructura permite:
- ✅ Visualizar la arquitectura completa de forma clara
- ✅ Entender la organización modular de Terraform
- ✅ Identificar componentes y sus relaciones
- ✅ Facilitar onboarding de nuevos miembros del equipo
- ✅ Documentar decisiones de arquitectura
- ✅ Servir como referencia para troubleshooting

## Formatos Disponibles

El diagrama de infraestructura está disponible en dos formatos:

1. **Diagrama ASCII** - [../diagrama-infraestructura-terraform.md](../diagrama-infraestructura-terraform.md)
   - Formato de texto plano con arte ASCII
   - Visualización detallada de todos los componentes
   - 7 diagramas principales (Módulos, VPC, Security Groups, VPC Endpoints, EventBridge, Monitoring, Tagging)
   - ~450 líneas de documentación visual

2. **Diagrama Mermaid** - [Diagrama arquitectura.md](Diagrama%20arquitectura.md) ⭐ NUEVO
   - Formato Mermaid para renderizado en GitHub/GitLab
   - Diagrama de flujo interactivo con colores
   - Visualización de conexiones y dependencias
   - Ideal para documentación en repositorios Git

## Contenido del Diagrama

### 1. Estructura de Módulos Terraform

El diagrama muestra la organización completa del código Terraform:

```
terraform/
├── main.tf                    ← Orquestador principal
├── variables.tf               ← Variables globales
├── outputs.tf                 ← Outputs de infraestructura
├── terraform.tfvars           ← Configuración por ambiente
│
├── modules/                   ← 8 módulos especializados
│   ├── vpc/
│   ├── security-groups/
│   ├── vpc-endpoints/
│   ├── nacls/
│   ├── eventbridge/
│   ├── monitoring/
│   ├── waf/
│   └── tagging/
│
└── environments/              ← Configuraciones por ambiente
    ├── dev/
    ├── qa/
    └── prod/
```

### 2. Arquitectura de Red AWS (VPC Module)

Visualización detallada de la red VPC:

**VPC Principal**:
- CIDR: 10.0.0.0/16 (65,536 IPs)
- Región: us-east-1
- DNS Resolution y DNS Hostnames habilitados

**Availability Zone A (us-east-1a)**:
- **Public Subnet A**: 10.0.1.0/24
  - Internet Gateway
  - NAT Gateway + Elastic IP
  - Purpose: NAT Gateway, API Gateway endpoints

- **Private Subnet 1A**: 10.0.10.0/24
  - Lambda Functions
  - MWAA (Airflow)
  - Redshift Cluster
  - VPC Endpoints
  - Purpose: Servicios principales de procesamiento

- **Private Subnet 2A**: 10.0.20.0/24
  - AWS Glue ENIs
  - Purpose: ETL jobs y transformaciones

**Availability Zone B (us-east-1b) - MULTI-AZ OPCIONAL**:
- Solo se crea si `enable_multi_az = true`
- Public Subnet B: 10.0.2.0/24 (NAT Gateway B)
- Private Subnet 1B: 10.0.11.0/24 (Lambda, MWAA, Redshift HA)
- Private Subnet 2B: 10.0.21.0/24 (Glue ENIs HA)

**Route Tables**:
- Public Route Table: 0.0.0.0/0 → Internet Gateway
- Private Route Table A: 0.0.0.0/0 → NAT Gateway A
- Private Route Table B: 0.0.0.0/0 → NAT Gateway B (Multi-AZ)

### 3. Security Groups (7 grupos configurados)

El diagrama detalla los 7 Security Groups y sus reglas:

1. **SG-API-Gateway**
   - Inbound: HTTPS (443) desde IPs de Janis
   - Outbound: All traffic

2. **SG-Lambda**
   - Inbound: Ninguno
   - Outbound: PostgreSQL → Redshift, HTTPS → VPC Endpoints, HTTPS → Internet

3. **SG-MWAA (Managed Airflow)**
   - Inbound: HTTPS (443) desde sí mismo
   - Outbound: HTTPS → VPC Endpoints, HTTPS → Internet, PostgreSQL → Redshift

4. **SG-Glue**
   - Inbound: All TCP (0-65535) desde sí mismo (Spark cluster)
   - Outbound: HTTPS → VPC Endpoints, All TCP → sí mismo

5. **SG-Redshift**
   - Inbound: PostgreSQL (5439) desde Lambda, MWAA, BI systems
   - Outbound: HTTPS → VPC Endpoints

6. **SG-EventBridge**
   - Inbound: Ninguno
   - Outbound: HTTPS → MWAA, HTTPS → VPC Endpoints

7. **SG-VPC-Endpoints**
   - Inbound: HTTPS (443) desde toda la VPC (10.0.0.0/16)
   - Outbound: HTTPS (443) → AWS Services

### 4. VPC Endpoints (Optimización de Costos)

**Gateway Endpoints (Sin costo adicional)**:
- S3 Gateway Endpoint (GRATIS)
  - Associated: Todas las Route Tables
  - Purpose: Acceso privado a S3 sin NAT Gateway

**Interface Endpoints (~$7.50/mes cada uno + $0.01/GB)**:
- AWS Glue
- AWS Secrets Manager
- CloudWatch Logs
- AWS KMS
- AWS STS
- Amazon EventBridge

**Configuración**:
Todos los endpoints son opcionales y se controlan con variables:
- `enable_s3_endpoint = true` (RECOMENDADO - gratis)
- `enable_glue_endpoint = true/false`
- `enable_secrets_manager_endpoint = true/false`
- `enable_logs_endpoint = true/false`
- `enable_kms_endpoint = true/false`
- `enable_sts_endpoint = true/false`
- `enable_events_endpoint = true/false`

### 5. EventBridge Module (Orquestación de Polling)

**Event Bus Principal** con 5 reglas de polling:

1. **poll-orders-rule**
   - Schedule: rate(5 minutes) [configurable]
   - Target: MWAA Environment
   - DAG: dag_poll_orders
   - DLQ: eventbridge-dlq

2. **poll-products-rule**
   - Schedule: rate(60 minutes) [configurable]
   - Target: MWAA Environment
   - DAG: dag_poll_products

3. **poll-stock-rule**
   - Schedule: rate(10 minutes) [configurable]
   - Target: MWAA Environment
   - DAG: dag_poll_stock

4. **poll-prices-rule**
   - Schedule: rate(30 minutes) [configurable]
   - Target: MWAA Environment
   - DAG: dag_poll_prices

5. **poll-stores-rule**
   - Schedule: rate(1440 minutes) [1 día - configurable]
   - Target: MWAA Environment
   - DAG: dag_poll_stores

**Dead Letter Queue (DLQ)**:
- SQS Queue: eventbridge-dlq
- Purpose: Capturar eventos fallidos
- Retention: 14 días
- Alarm: Alerta si hay mensajes en DLQ

**Configuración de Frecuencias**:
- `order_polling_rate_minutes = 5` (recomendado: 5-15 min)
- `product_polling_rate_minutes = 60` (recomendado: 30-60 min)
- `stock_polling_rate_minutes = 10` (recomendado: 15-30 min)
- `price_polling_rate_minutes = 30` (recomendado: 60 min)
- `store_polling_rate_minutes = 1440` (recomendado: 1 día)

### 6. Monitoring Module (Observabilidad y Seguridad)

**VPC Flow Logs**:
- CloudWatch Log Group: /aws/vpc/flow-logs/{name_prefix}
- Retention: 90 días (configurable)
- Traffic Type: ALL (accepted + rejected)
- Format: Custom (IPs, puertos, protocolo, acción)

**DNS Query Logging**:
- CloudWatch Log Group: /aws/route53/resolver/{name_prefix}
- Retention: 90 días (configurable)
- Purpose: Monitoreo de seguridad y troubleshooting

**CloudWatch Alarms (11 alarmas configuradas)**:

**Infraestructura**:
1. NAT Gateway Errors (ErrorPortAllocation > 10 en 5 min)
2. NAT Gateway Packet Drops (PacketsDropCount > 1000 en 5 min)

**Seguridad (basadas en VPC Flow Logs)**:
3. Rejected Connections Spike (> 100 en 5 min)
4. Port Scanning Detected (> 50 en 5 min)
5. Data Exfiltration Risk (> 100 MB en 5 min)
6. Unusual SSH/RDP Activity (> 20 en 5 min)

**EventBridge (una alarma por cada rule)**:
7-11. EventBridge Failed Invocations (> 5 en 5 min) para cada regla de polling

**Log Metric Filters (4 filtros para detección de amenazas)**:
1. rejected_connections (action=REJECT)
2. port_scanning (packets=1 + action=REJECT)
3. high_outbound_traffic (bytes>10000000 + action=ACCEPT)
4. ssh_rdp_attempts (dstport=22||3389 + protocol=6)

**Configuración**:
- `enable_vpc_flow_logs = true/false`
- `enable_dns_query_logging = true/false`
- `vpc_flow_logs_retention_days = 90` (7, 30, 90, 365)
- `dns_logs_retention_days = 90` (7, 30, 90, 365)
- `alarm_sns_topic_arn = "arn:aws:sns:..."` (opcional)

### 7. S3 Module (Data Lake Buckets)

**S3 Buckets (5 buckets configurados)**:
- S3 Bronze Layer (raw data)
- S3 Silver Layer (cleaned data)
- S3 Gold Layer (business-ready data)
- S3 Scripts Bucket (Lambda, Glue, MWAA code)
- S3 Logs Bucket (access logs, application logs)

**Configuración de Lifecycle (variables)**:
- `bronze_glacier_transition_days = 90` (recomendado: 30-90 días)
- `bronze_expiration_days = 365` (recomendado: 180-365 días)
- `silver_glacier_transition_days = 180` (recomendado: 90-180 días)
- `silver_expiration_days = 730` (recomendado: 365-730 días)
- `gold_intelligent_tiering_days = 30` (recomendado: 15-30 días)
- `logs_expiration_days = 365` (recomendado: 90-365 días)

### 8. Tagging Strategy (Política Corporativa)

**Tags Obligatorios (Corporate Policy)**:
- Application: "janis-cencosud-integration"
- Environment: "prod" | "qa" | "dev" | "uat" | "sandbox"
- Owner: "data-engineering-team"
- CostCenter: "CC-XXXX" (REQUERIDO - contactar finanzas)
- BusinessUnit: "Data-Analytics"
- Country: "CL" (Chile)
- Criticality: "high" | "medium" | "low"
- ManagedBy: "terraform"

**Tags Adicionales (Opcionales)**:
- Purpose
- AutoShutdown
- Otros según necesidad

**Aplicación**:
- Todos los recursos AWS reciben estos tags automáticamente
- Configurado en main.tf usando locals.common_tags
- Merge con additional_tags para tags opcionales
- Validación automática en variables.tf

**Recursos Etiquetados**:
- VPC y Subnets
- Security Groups
- VPC Endpoints
- NAT Gateways y Elastic IPs
- Route Tables
- S3 Buckets (Bronze, Silver, Gold, Scripts, Logs)
- EventBridge Rules y Event Bus
- CloudWatch Log Groups
- CloudWatch Alarms
- IAM Roles
- SQS Queues

## Formatos Disponibles

El diagrama de infraestructura está disponible en **tres formatos** para diferentes casos de uso:

### 1. Diagrama ASCII (diagrama-infraestructura-terraform.md)
- **Formato**: Texto plano con arte ASCII
- **Ubicación**: Raíz del proyecto
- **Contenido**: 7 diagramas detallados (Módulos, VPC, Security Groups, VPC Endpoints, EventBridge, Monitoring, Tagging)
- **Longitud**: ~450 líneas
- **Uso**: Documentación técnica detallada, referencia completa

### 2. Diagramas Mermaid - Múltiples Vistas (diagrama-mermaid.md)
- **Formato**: Mermaid (renderizable en GitHub/GitLab)
- **Ubicación**: Raíz del proyecto
- **Contenido**: 7 diagramas interactivos con colores
  - Arquitectura de Módulos Terraform
  - Arquitectura de Red VPC (Single-AZ)
  - Security Groups y Flujo de Tráfico
  - VPC Endpoints
  - EventBridge - Orquestación de Polling
  - Monitoring - CloudWatch
  - Flujo de Datos Completo
  - Recursos AWS Creados por Ambiente
- **Uso**: Documentación en repositorios Git, presentaciones, onboarding

### 3. Diagrama de Arquitectura Principal (Documentación Cenco/Diagrama arquitectura.md) ⭐ NUEVO
- **Formato**: Mermaid (renderizable en GitHub/GitLab)
- **Ubicación**: Documentación Cenco/
- **Contenido**: Diagrama de flujo completo de la arquitectura AWS
  - Conexiones entre componentes externos (Janis WMS) y AWS
  - VPC con subnets públicas y privadas
  - Servicios AWS (Lambda, MWAA, Glue, Redshift)
  - VPC Endpoints y servicios gestionados
  - Flujo de monitoreo y alertas
  - Estilos visuales con colores por tipo de servicio
- **Uso**: Vista de alto nivel de la arquitectura, documentación principal, README

## Cuándo Usar Cada Formato

### Diagrama ASCII
✅ Cuando necesitas:
- Referencia técnica detallada
- Documentación que funciona en cualquier editor de texto
- Especificaciones completas de configuración
- Detalles de cada módulo y componente

### Diagramas Mermaid (múltiples vistas)
✅ Cuando necesitas:
- Visualización interactiva en GitHub/GitLab
- Presentaciones técnicas
- Onboarding de nuevos miembros
- Documentación en repositorios Git
- Múltiples perspectivas de la arquitectura

### Diagrama de Arquitectura Principal (Mermaid)
✅ Cuando necesitas:
- Vista de alto nivel de toda la arquitectura
- Entender el flujo completo de datos
- Documentación principal del proyecto
- Presentaciones ejecutivas
- README y documentación de entrada

## Beneficios del Diagrama

### Claridad Visual
- Representación gráfica clara de la arquitectura
- Fácil identificación de componentes y relaciones
- Visualización de flujos de tráfico y comunicación

### Documentación Técnica
- Referencia completa de la infraestructura
- Detalles de configuración de cada módulo
- Especificaciones de red y seguridad

### Onboarding
- Facilita comprensión rápida para nuevos miembros
- Reduce curva de aprendizaje
- Proporciona contexto completo del proyecto

### Troubleshooting
- Identificación rápida de componentes afectados
- Visualización de dependencias
- Referencia para debugging

### Planificación
- Base para expansión futura (Multi-AZ)
- Identificación de optimizaciones
- Análisis de costos por componente

## Uso del Diagrama

### Para Desarrolladores
1. Entender la arquitectura general
2. Identificar dónde se despliegan sus componentes
3. Comprender flujos de datos y comunicación
4. Planificar integraciones

### Para Arquitectos
1. Revisar decisiones de diseño
2. Planificar expansiones (Multi-AZ)
3. Optimizar costos
4. Evaluar seguridad

### Para DevOps
1. Entender módulos de Terraform
2. Planificar deployments
3. Troubleshooting de infraestructura
4. Configurar monitoreo

### Para Stakeholders
1. Visualizar inversión en infraestructura
2. Entender capacidades del sistema
3. Evaluar escalabilidad
4. Comprender costos

## Relación con Otros Documentos

### Documentos Complementarios

- **[Infraestructura AWS - Resumen Ejecutivo.md](Infraestructura%20AWS%20-%20Resumen%20Ejecutivo.md)** - Visión general de alto nivel
- **[Especificación Detallada de Infraestructura AWS.md](Especificación%20Detallada%20de%20Infraestructura%20AWS.md)** - Detalles técnicos completos
- **[Configuración de Ambientes - Producción.md](Configuración%20de%20Ambientes%20-%20Producción.md)** - Configuración específica de producción
- **[../terraform/README.md](../terraform/README.md)** - Documentación de Terraform
- **[../terraform/MULTI_AZ_EXPANSION.md](../terraform/MULTI_AZ_EXPANSION.md)** - Plan de expansión Multi-AZ

### Flujo de Documentación

```
1. Diagrama de Infraestructura (ESTE DOCUMENTO)
   ↓ (Visualización general)
2. Infraestructura AWS - Resumen Ejecutivo
   ↓ (Contexto de alto nivel)
3. Especificación Detallada de Infraestructura AWS
   ↓ (Detalles técnicos)
4. Configuración de Ambientes - Producción
   ↓ (Configuración específica)
5. Deployment
   ✅ (Infraestructura desplegada)
```

## Actualizaciones del Diagrama

El diagrama debe actualizarse cuando:
- Se agreguen nuevos módulos de Terraform
- Se modifique la arquitectura de red
- Se agreguen o eliminen Security Groups
- Se cambien configuraciones de VPC Endpoints
- Se modifiquen reglas de EventBridge
- Se actualicen alarmas de monitoreo
- Se cambien políticas de tagging

## Notas Técnicas

### Formato del Diagrama
- Formato: Texto ASCII art
- Ubicación: `diagrama-infraestructura-terraform.md`
- Secciones: 7 diagramas principales
- Longitud: ~450 líneas

### Mantenimiento
- Actualizar después de cambios en infraestructura
- Sincronizar con código Terraform
- Revisar en cada release
- Validar con equipo de arquitectura

### Versionado
- Incluir en control de versiones (Git)
- Documentar cambios en commits
- Mantener historial de evolución
- Referenciar en documentación técnica

## Próximos Pasos

1. **Equipo**: Revisar diagrama completo en [../diagrama-infraestructura-terraform.md](../diagrama-infraestructura-terraform.md)
2. **Arquitectos**: Validar representación de la arquitectura
3. **DevOps**: Usar como referencia para deployments
4. **Desarrolladores**: Familiarizarse con la infraestructura
5. **Documentación**: Mantener sincronizado con cambios

---

**Preparado por**: Kiro AI Assistant  
**Fecha**: 3 de Febrero, 2026  
**Versión**: 1.1  
**Estado**: ✅ Diagramas completos de infraestructura Terraform creados (ASCII + Mermaid)

**Actualizaciones**:
- **v1.1** (3 Feb 2026): Agregado diagrama de arquitectura principal en formato Mermaid
- **v1.0** (3 Feb 2026): Diagrama completo de infraestructura Terraform creado (ASCII)

