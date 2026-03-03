# Especificación Detallada de Infraestructura AWS
## Plataforma de Integración Janis-Cencosud

**Versión**: 1.0  
**Fecha**: 21 de Enero, 2026  
**Propósito**: Documento de especificación técnica para implementación de infraestructura AWS

---

## 1. RESUMEN EJECUTIVO

Este documento proporciona las especificaciones técnicas detalladas de toda la infraestructura AWS requerida para la plataforma de integración Janis-Cencosud. El cliente puede usar este documento como base para implementar la infraestructura aplicando sus propias normativas internas de seguridad, tageo, y políticas corporativas.

### 1.1 Alcance del Documento

- Especificaciones completas de componentes de red (VPC, subnets, routing)
- Configuraciones de seguridad (Security Groups, NACLs, WAF)
- Conectividad y endpoints
- Orquestación de eventos (EventBridge)
- Monitoreo y logging
- Integración con infraestructura existente

### 1.2 Arquitectura de Despliegue

- **Región AWS**: us-east-1 (Virginia del Norte)
- **Estrategia de Disponibilidad**: Single-AZ inicial (us-east-1a) con capacidad de expansión a Multi-AZ
- **Gestión de Infraestructura**: Infrastructure as Code (Terraform recomendado)

---

## 2. COMPONENTES DE RED

### 2.1 Virtual Private Cloud (VPC)

**Especificación Técnica**:

```yaml
VPC:
  CIDR_Block: "10.0.0.0/16"
  Total_IPs: 65,536
  DNS_Resolution: Enabled
  DNS_Hostnames: Enabled
  IPv4_Support: Primary
  IPv6_Support: Optional (preparado para futuro)
  Region: us-east-1
```

**Justificación del CIDR Block**:
- Proporciona 65,536 direcciones IP
- Suficiente para crecimiento futuro de la plataforma
- Compatible con rangos de red corporativa de Cencosud
- Permite subnetting flexible para diferentes propósitos

**Requisitos de Implementación**:
- El cliente debe verificar que 10.0.0.0/16 no conflictúe con redes corporativas existentes
- Si hay conflicto, seleccionar un CIDR alternativo del rango privado (10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16)
- Aplicar tags corporativos según política interna
- Habilitar VPC Flow Logs para auditoría

### 2.2 Arquitectura de Subnets

#### 2.2.1 Subnet Pública

**Especificación**:
```yaml
Public_Subnet_A:
  CIDR: "10.0.1.0/24"
  Availability_Zone: "us-east-1a"
  Total_IPs: 256
  Auto_Assign_Public_IP: true
  Propósito: "NAT Gateway, API Gateway endpoints"
  Routing: "0.0.0.0/0 → Internet Gateway"
```

**Recursos que residirán en esta subnet**:
- NAT Gateway con Elastic IP
- Application Load Balancer (si se requiere)
- Bastion hosts (si se requiere acceso SSH)


#### 2.2.2 Subnet Privada 1A (Servicios de Datos)

**Especificación**:
```yaml
Private_Subnet_1A:
  CIDR: "10.0.11.0/24"
  Availability_Zone: "us-east-1a"
  Total_IPs: 256
  Auto_Assign_Public_IP: false
  Propósito: "Lambda, MWAA, Redshift, Secrets Manager"
  Routing: "0.0.0.0/0 → NAT Gateway"
```

**Recursos que residirán en esta subnet**:
- AWS Lambda functions (webhook processor, data enrichment)
- Amazon MWAA (Managed Workflows for Apache Airflow)
- Amazon Redshift cluster (si se despliega nuevo)
- AWS Secrets Manager endpoints
- Otros servicios de procesamiento de datos

#### 2.2.3 Subnet Privada 2A (AWS Glue)

**Especificación**:
```yaml
Private_Subnet_2A:
  CIDR: "10.0.21.0/24"
  Availability_Zone: "us-east-1a"
  Total_IPs: 256
  Auto_Assign_Public_IP: false
  Propósito: "AWS Glue ENIs (Elastic Network Interfaces)"
  Routing: "0.0.0.0/0 → NAT Gateway"
```

**Justificación de Subnet Dedicada**:
- AWS Glue puede consumir múltiples IPs durante ejecución de jobs
- Separación evita agotamiento de IPs en subnet principal
- Facilita troubleshooting y monitoreo de tráfico Glue


#### 2.2.4 Subnets Reservadas para Expansión Multi-AZ

**Especificación**:
```yaml
Reserved_Subnets_us-east-1b:
  Public_Subnet_B:
    CIDR: "10.0.2.0/24"
    Status: "Reservado para futuro"
    Propósito: "Segundo NAT Gateway, ALB en segunda AZ"
  
  Private_Subnet_1B:
    CIDR: "10.0.11.0/24"
    Status: "Reservado para futuro"
    Propósito: "Lambda, MWAA, Redshift en segunda AZ"
  
  Private_Subnet_2B:
    CIDR: "10.0.21.0/24"
    Status: "Reservado para futuro"
    Propósito: "AWS Glue ENIs en segunda AZ"
```

**Nota Importante**: Estos CIDRs están reservados y NO deben ser asignados a otros propósitos. Facilitan migración futura a arquitectura Multi-AZ sin reconfiguración de red.

---

## 3. CONECTIVIDAD E INTERNET

### 3.1 Internet Gateway

**Especificación**:
```yaml
Internet_Gateway:
  Attachment: "Attached to VPC"
  Purpose: "Conectividad bidireccional a internet para subnet pública"
  High_Availability: "Managed by AWS (redundante automáticamente)"
  Cost: "Sin costo"
```

**Configuración de Routing**:
- Route Table pública debe incluir: `0.0.0.0/0 → Internet Gateway ID`
- Asociar route table con Public Subnet A


### 3.2 NAT Gateway

**Especificación**:
```yaml
NAT_Gateway:
  Location: "Public Subnet A (10.0.1.0/24)"
  Elastic_IP: "Requerido (asignación automática)"
  Purpose: "Conectividad saliente para subnets privadas"
  Bandwidth: "Hasta 45 Gbps (auto-scaling)"
  High_Availability: "Dentro de AZ (managed by AWS)"
  Cost_Estimate: "$32.40/mes + data transfer"
```

**Configuración de Routing**:
- Route Tables privadas deben incluir: `0.0.0.0/0 → NAT Gateway ID`
- Asociar route tables con Private Subnet 1A y 2A

**⚠️ PUNTO CRÍTICO - Single Point of Failure**:
- En despliegue Single-AZ, el NAT Gateway es un punto único de fallo
- Si us-east-1a falla, subnets privadas pierden conectividad saliente
- Para alta disponibilidad, desplegar segundo NAT Gateway en us-east-1b (costo adicional ~$32/mes)

**Requisitos del Cliente**:
- Evaluar si el riesgo de Single-AZ es aceptable para el negocio
- Considerar segundo NAT Gateway si se requiere alta disponibilidad
- Documentar procedimiento de recuperación ante fallo de AZ

### 3.3 Route Tables

**Especificación de Route Table Pública**:
```yaml
Public_Route_Table:
  Name: "janis-cencosud-public-rt"
  Routes:
    - Destination: "10.0.0.0/16"
      Target: "local"
    - Destination: "0.0.0.0/0"
      Target: "Internet Gateway ID"
  Associated_Subnets:
    - "Public Subnet A (10.0.1.0/24)"
```


**Especificación de Route Table Privada**:
```yaml
Private_Route_Table:
  Name: "janis-cencosud-private-rt"
  Routes:
    - Destination: "10.0.0.0/16"
      Target: "local"
    - Destination: "0.0.0.0/0"
      Target: "NAT Gateway ID"
    - Destination: "s3-prefix-list"
      Target: "S3 Gateway Endpoint ID"
  Associated_Subnets:
    - "Private Subnet 1A (10.0.11.0/24)"
    - "Private Subnet 2A (10.0.21.0/24)"
```

---

## 4. VPC ENDPOINTS

### 4.1 S3 Gateway Endpoint

**Especificación**:
```yaml
S3_Gateway_Endpoint:
  Service: "com.amazonaws.us-east-1.s3"
  Type: "Gateway"
  Route_Table_Association: "Todas las route tables (pública y privadas)"
  Policy: "Full access (o restringir según política corporativa)"
  Cost: "Sin costo"
  Data_Transfer_Cost: "Sin costo"
```

**Beneficios**:
- Acceso privado a S3 sin pasar por NAT Gateway
- Reduce costos de transferencia de datos
- Mejora performance y seguridad
- Tráfico permanece dentro de la red AWS

**Requisitos del Cliente**:
- Aplicar endpoint policy si se requiere restringir acceso a buckets específicos
- Considerar VPC endpoint policy para cumplimiento de seguridad


### 4.2 Interface Endpoints (AWS PrivateLink)

**Especificación General**:
```yaml
Interface_Endpoints_Configuration:
  Type: "Interface (PrivateLink)"
  Subnet_Association: "Private Subnets (1A y 2A)"
  Private_DNS: "Enabled (recomendado)"
  Security_Group: "SG-VPC-Endpoints (ver sección 5.7)"
  Cost_Per_Endpoint: "$0.01/hora = $7.20/mes"
  Data_Transfer_Cost: "$0.01/GB"
```

#### 4.2.1 AWS Glue Endpoint

```yaml
Glue_Endpoint:
  Service: "com.amazonaws.us-east-1.glue"
  Purpose: "Acceso privado a Glue Data Catalog y Glue Jobs"
  Required_By: "AWS Glue jobs, Lambda functions, MWAA"
  Estimated_Cost: "$7.20/mes + data transfer"
```

#### 4.2.2 AWS Secrets Manager Endpoint

```yaml
Secrets_Manager_Endpoint:
  Service: "com.amazonaws.us-east-1.secretsmanager"
  Purpose: "Recuperación segura de credenciales"
  Required_By: "Lambda, MWAA, Glue jobs"
  Estimated_Cost: "$7.20/mes + data transfer"
```

#### 4.2.3 CloudWatch Logs Endpoint

```yaml
CloudWatch_Logs_Endpoint:
  Service: "com.amazonaws.us-east-1.logs"
  Purpose: "Envío de logs sin pasar por NAT Gateway"
  Required_By: "Lambda, Glue, MWAA, VPC Flow Logs"
  Estimated_Cost: "$7.20/mes + data transfer"
```


#### 4.2.4 AWS KMS Endpoint

```yaml
KMS_Endpoint:
  Service: "com.amazonaws.us-east-1.kms"
  Purpose: "Operaciones de cifrado/descifrado"
  Required_By: "Lambda, Glue, Secrets Manager, S3"
  Estimated_Cost: "$7.20/mes + data transfer"
```

#### 4.2.5 AWS STS Endpoint

```yaml
STS_Endpoint:
  Service: "com.amazonaws.us-east-1.sts"
  Purpose: "Generación de credenciales temporales"
  Required_By: "Lambda, Glue, MWAA (AssumeRole operations)"
  Estimated_Cost: "$7.20/mes + data transfer"
```

#### 4.2.6 Amazon EventBridge Endpoint

```yaml
EventBridge_Endpoint:
  Service: "com.amazonaws.us-east-1.events"
  Purpose: "Event routing y scheduling"
  Required_By: "EventBridge rules, Lambda, MWAA"
  Estimated_Cost: "$7.20/mes + data transfer"
```

**Costo Total Estimado de Interface Endpoints**: $43.20/mes + data transfer

**Requisitos del Cliente**:
- Evaluar si todos los endpoints son necesarios según arquitectura final
- Considerar endpoint policies para restringir acceso
- Aplicar security groups apropiados (ver sección 5)
- Habilitar Private DNS para simplificar configuración de aplicaciones

---

## 5. SEGURIDAD - SECURITY GROUPS

Los Security Groups actúan como firewalls stateful a nivel de instancia/ENI. El cliente debe adaptar estas reglas según sus políticas de seguridad corporativa.


### 5.1 SG-API-Gateway

**Propósito**: Proteger endpoints de API Gateway que reciben webhooks de Janis

```yaml
SG_API_Gateway:
  Name: "janis-cencosud-sg-api-gateway"
  Description: "Security group for API Gateway webhook endpoints"
  
  Inbound_Rules:
    - Protocol: TCP
      Port: 443
      Source: 0.0.0.0/0
      Description: "HTTPS from Janis webhooks"
  
  Outbound_Rules:
    - Protocol: All
      Port: All
      Destination: 0.0.0.0/0
      Description: "Allow all outbound traffic"
```

**Consideraciones del Cliente**:
- Si se conocen IPs específicas de Janis, restringir source a esos rangos
- Considerar integración con AWS WAF para protección adicional (ver sección 7)
- Evaluar si se requiere logging de conexiones rechazadas

### 5.2 SG-Redshift-Existing

**Propósito**: Controlar acceso al cluster Redshift existente de Cencosud

```yaml
SG_Redshift_Existing:
  Name: "janis-cencosud-sg-redshift"
  Description: "Security group for existing Redshift cluster"
  
  Inbound_Rules:
    - Protocol: TCP
      Port: 5439
      Source: "SG-Lambda"
      Description: "PostgreSQL from Lambda functions"
    
    - Protocol: TCP
      Port: 5439
      Source: "SG-MWAA"
      Description: "PostgreSQL from MWAA Airflow"
    
    - Protocol: TCP
      Port: 5439
      Source: "<EXISTING_BI_SECURITY_GROUP>"
      Description: "PostgreSQL from existing BI systems"
    
    - Protocol: TCP
      Port: 5439
      Source: "<MYSQL_MIGRATION_SOURCE>"
      Description: "PostgreSQL from current MySQL→Redshift pipeline (temporal)"
  
  Outbound_Rules:
    - Protocol: TCP
      Port: 443
      Destination: "<VPC_ENDPOINT_SECURITY_GROUP>"
      Description: "HTTPS to VPC Endpoints only"
```


**⚠️ REQUISITOS CRÍTICOS DEL CLIENTE**:
- Reemplazar `<EXISTING_BI_SECURITY_GROUP>` con el security group real de sistemas BI de Cencosud
- Reemplazar `<MYSQL_MIGRATION_SOURCE>` con el security group o CIDR del pipeline MySQL actual
- Coordinar con equipo de BI para no interrumpir acceso existente
- Planificar remoción de regla MySQL→Redshift después de migración completa
- Aplicar principio de menor privilegio: solo permitir acceso desde fuentes necesarias

### 5.3 SG-Lambda

**Propósito**: Security group para funciones Lambda (webhook processor, data enrichment)

```yaml
SG_Lambda:
  Name: "janis-cencosud-sg-lambda"
  Description: "Security group for Lambda functions"
  
  Inbound_Rules:
    # Lambda no recibe conexiones directas, no requiere reglas inbound
    - None
  
  Outbound_Rules:
    - Protocol: TCP
      Port: 5439
      Destination: "SG-Redshift-Existing"
      Description: "PostgreSQL to Redshift cluster"
    
    - Protocol: TCP
      Port: 443
      Destination: "<VPC_ENDPOINT_SECURITY_GROUP>"
      Description: "HTTPS to VPC Endpoints (Secrets Manager, S3, etc.)"
    
    - Protocol: TCP
      Port: 443
      Destination: 0.0.0.0/0
      Description: "HTTPS to internet (Janis API polling)"
```

**Consideraciones del Cliente**:
- Si Lambda solo debe acceder a servicios AWS internos, remover regla 0.0.0.0/0
- Considerar VPC endpoints para todos los servicios AWS para eliminar tráfico a internet
- Aplicar políticas de IAM restrictivas además de security groups


### 5.4 SG-MWAA

**Propósito**: Security group para Amazon MWAA (Managed Workflows for Apache Airflow)

```yaml
SG_MWAA:
  Name: "janis-cencosud-sg-mwaa"
  Description: "Security group for MWAA Airflow environment"
  
  Inbound_Rules:
    - Protocol: TCP
      Port: 443
      Source: "SG-MWAA" # Self-reference
      Description: "HTTPS from MWAA workers (self-reference for cluster communication)"
    
    - Protocol: TCP
      Port: 443
      Source: "<EVENTBRIDGE_VPC_ENDPOINT_SG>"
      Description: "HTTPS from EventBridge for DAG triggering"
  
  Outbound_Rules:
    - Protocol: TCP
      Port: 443
      Destination: "<VPC_ENDPOINT_SECURITY_GROUP>"
      Description: "HTTPS to VPC Endpoints"
    
    - Protocol: TCP
      Port: 443
      Destination: 0.0.0.0/0
      Description: "HTTPS to internet (Janis API, external dependencies)"
    
    - Protocol: TCP
      Port: 5439
      Destination: "SG-Redshift-Existing"
      Description: "PostgreSQL to Redshift cluster"
```

**Nota Importante**: La regla self-reference (SG-MWAA → SG-MWAA) es requerida para comunicación entre workers de Airflow.

**Requisitos del Cliente**:
- Verificar que MWAA tenga acceso a todos los servicios AWS necesarios vía VPC endpoints
- Considerar restricción de tráfico a internet si no es necesario
- Aplicar IAM roles restrictivos para MWAA además de security groups


### 5.5 SG-Glue

**Propósito**: Security group para AWS Glue jobs y crawlers

```yaml
SG_Glue:
  Name: "janis-cencosud-sg-glue"
  Description: "Security group for AWS Glue jobs and crawlers"
  
  Inbound_Rules:
    - Protocol: TCP
      Port: 0-65535 # All TCP ports
      Source: "SG-Glue" # Self-reference
      Description: "All TCP from Glue (self-reference for Spark cluster communication)"
  
  Outbound_Rules:
    - Protocol: TCP
      Port: 443
      Destination: "<VPC_ENDPOINT_SECURITY_GROUP>"
      Description: "HTTPS to VPC Endpoints (Glue Catalog, S3, etc.)"
    
    - Protocol: TCP
      Port: 0-65535 # All TCP ports
      Destination: "SG-Glue" # Self-reference
      Description: "All TCP to Glue (self-reference for Spark cluster communication)"
```

**Nota Crítica**: AWS Glue requiere reglas self-reference amplias para comunicación entre nodos del cluster Spark. Esto es un requisito de AWS Glue y no puede ser más restrictivo.

**Requisitos del Cliente**:
- No modificar reglas self-reference, son requeridas por AWS Glue
- Asegurar que Glue tenga acceso a VPC endpoints necesarios
- Considerar subnet dedicada para Glue (ya especificada en sección 2.2.3)

### 5.6 SG-EventBridge

**Propósito**: Security group para VPC endpoint de EventBridge

```yaml
SG_EventBridge:
  Name: "janis-cencosud-sg-eventbridge"
  Description: "Security group for EventBridge VPC endpoint"
  
  Inbound_Rules:
    # EventBridge recibe eventos internamente, no requiere reglas inbound específicas
    - None
  
  Outbound_Rules:
    - Protocol: TCP
      Port: 443
      Destination: "<MWAA_ENDPOINT_SG>"
      Description: "HTTPS to MWAA for DAG triggering"
    
    - Protocol: TCP
      Port: 443
      Destination: "<VPC_ENDPOINT_SECURITY_GROUP>"
      Description: "HTTPS to other VPC Endpoints"
```


### 5.7 SG-VPC-Endpoints

**Propósito**: Security group común para todos los VPC Interface Endpoints

```yaml
SG_VPC_Endpoints:
  Name: "janis-cencosud-sg-vpc-endpoints"
  Description: "Security group for VPC Interface Endpoints"
  
  Inbound_Rules:
    - Protocol: TCP
      Port: 443
      Source: "10.0.0.0/16" # Entire VPC CIDR
      Description: "HTTPS from all VPC resources"
  
  Outbound_Rules:
    - Protocol: TCP
      Port: 443
      Destination: 0.0.0.0/0
      Description: "HTTPS to AWS services"
```

**Requisitos del Cliente**:
- Considerar reglas más restrictivas si se conocen exactamente qué security groups necesitan acceso
- Aplicar endpoint policies además de security groups para control granular
- Monitorear tráfico a endpoints para detectar uso anómalo

---

## 6. SEGURIDAD - NETWORK ACCESS CONTROL LISTS (NACLs)

Las NACLs actúan como firewalls stateless a nivel de subnet. Son una segunda capa de defensa después de Security Groups.

### 6.1 NACL para Subnet Pública

```yaml
Public_Subnet_NACL:
  Name: "janis-cencosud-nacl-public"
  Associated_Subnets:
    - "Public Subnet A (10.0.1.0/24)"
  
  Inbound_Rules:
    - Rule_Number: 100
      Protocol: TCP
      Port: 443
      Source: 0.0.0.0/0
      Action: ALLOW
      Description: "HTTPS from internet"
    
    - Rule_Number: 110
      Protocol: TCP
      Port: 1024-65535 # Ephemeral ports
      Source: 0.0.0.0/0
      Action: ALLOW
      Description: "Return traffic (ephemeral ports)"
    
    - Rule_Number: "*" # Default rule
      Protocol: All
      Port: All
      Source: 0.0.0.0/0
      Action: DENY
      Description: "Deny all other traffic"
  
  Outbound_Rules:
    - Rule_Number: 100
      Protocol: All
      Port: All
      Destination: 0.0.0.0/0
      Action: ALLOW
      Description: "Allow all outbound traffic"
```


### 6.2 NACL para Subnets Privadas

```yaml
Private_Subnets_NACL:
  Name: "janis-cencosud-nacl-private"
  Associated_Subnets:
    - "Private Subnet 1A (10.0.10.0/24)"
    - "Private Subnet 2A (10.0.20.0/24)"
  
  Inbound_Rules:
    - Rule_Number: 100
      Protocol: All
      Port: All
      Source: 10.0.0.0/16 # VPC CIDR
      Action: ALLOW
      Description: "Allow all traffic from VPC"
    
    - Rule_Number: 110
      Protocol: TCP
      Port: 443
      Source: 0.0.0.0/0
      Action: ALLOW
      Description: "HTTPS from internet (return traffic)"
    
    - Rule_Number: 120
      Protocol: TCP
      Port: 1024-65535 # Ephemeral ports
      Source: 0.0.0.0/0
      Action: ALLOW
      Description: "Return traffic (ephemeral ports)"
    
    - Rule_Number: "*" # Default rule
      Protocol: All
      Port: All
      Source: 0.0.0.0/0
      Action: DENY
      Description: "Deny all other traffic"
  
  Outbound_Rules:
    - Rule_Number: 100
      Protocol: All
      Port: All
      Destination: 10.0.0.0/16 # VPC CIDR
      Action: ALLOW
      Description: "Allow all traffic to VPC"
    
    - Rule_Number: 110
      Protocol: TCP
      Port: 443
      Destination: 0.0.0.0/0
      Action: ALLOW
      Description: "HTTPS to internet"
    
    - Rule_Number: "*" # Default rule
      Protocol: All
      Port: All
      Destination: 0.0.0.0/0
      Action: DENY
      Description: "Deny all other traffic"
```

**Nota Importante sobre NACLs Stateless**: A diferencia de Security Groups, las NACLs son stateless. Esto significa que se debe permitir explícitamente tanto el tráfico entrante como el saliente, incluyendo puertos efímeros para tráfico de retorno.

**Requisitos del Cliente**:
- Ajustar reglas según políticas de seguridad corporativa
- Considerar reglas más restrictivas si se conocen exactamente los patrones de tráfico
- Monitorear VPC Flow Logs para identificar tráfico bloqueado por NACLs

---

## 7. AWS WAF (WEB APPLICATION FIREWALL)


AWS WAF protege los endpoints de API Gateway contra ataques web comunes y abuse.

### 7.1 Web ACL Configuration

```yaml
WAF_Web_ACL:
  Name: "janis-cencosud-waf-api-gateway"
  Scope: "REGIONAL" # Para API Gateway regional
  Default_Action: "ALLOW"
  Associated_Resources:
    - "API Gateway REST API ARN"
  CloudWatch_Metrics: "Enabled"
  Sampled_Requests: "Enabled"
```

### 7.2 Rate Limiting Rule

```yaml
Rate_Limiting_Rule:
  Name: "RateLimitRule"
  Priority: 1
  Type: "RATE_BASED"
  
  Configuration:
    Limit: 2000 # requests per 5 minutes
    Evaluation_Window: 300 # seconds (5 minutes)
    Aggregate_Key_Type: "IP"
    Scope_Down_Statement: null # Apply to all requests
  
  Action:
    Type: "BLOCK"
    Custom_Response:
      Response_Code: 429
      Response_Headers:
        - Name: "Retry-After"
          Value: "300"
  
  CloudWatch_Metrics: "Enabled"
```

**Justificación**: 2,000 requests por IP en 5 minutos permite tráfico legítimo mientras previene abuse y DDoS básicos.

**Requisitos del Cliente**:
- Ajustar límite según patrones de tráfico esperados de Janis
- Considerar rate limiting diferenciado por endpoint si es necesario
- Monitorear métricas de CloudWatch para ajustar límites
- Implementar whitelist de IPs conocidas de Janis si se requiere


### 7.3 Geo-Blocking Rule

```yaml
Geo_Blocking_Rule:
  Name: "GeoBlockingRule"
  Priority: 2
  Type: "GEO_MATCH"
  
  Configuration:
    Allowed_Countries:
      - "PE" # Peru
    Forwarded_IP_Config: null # Use source IP
  
  Action:
    Type: "BLOCK"
    Custom_Response:
      Response_Code: 403
      Response_Body: "Access denied from your location"
  
  CloudWatch_Metrics: "Enabled"
```

**Justificación**: Janis opera exclusivamente en Perú, bloquear otros países reduce superficie de ataque.

**Requisitos del Cliente**:
- Verificar que Janis no tenga infraestructura en otros países
- Considerar permitir países adicionales si Cencosud tiene operaciones internacionales
- Whitelist de IPs específicas si se requiere acceso desde otros países para testing/soporte

### 7.4 AWS Managed Rule Groups

```yaml
AWS_Managed_Rules:
  
  - Name: "AWSManagedRulesAmazonIpReputationList"
    Priority: 10
    Description: "Bloquea IPs con mala reputación conocida"
    Override_Action: "NONE" # Use rule group's actions
    Excluded_Rules: [] # No exclusions
  
  - Name: "AWSManagedRulesCommonRuleSet"
    Priority: 11
    Description: "Protección contra OWASP Top 10"
    Override_Action: "NONE"
    Excluded_Rules: [] # Ajustar si hay falsos positivos
  
  - Name: "AWSManagedRulesKnownBadInputsRuleSet"
    Priority: 12
    Description: "Bloquea payloads maliciosos conocidos"
    Override_Action: "NONE"
    Excluded_Rules: []
```

**Requisitos del Cliente**:
- Monitorear falsos positivos en los primeros días de operación
- Ajustar `Excluded_Rules` si reglas específicas causan problemas
- Considerar managed rules adicionales según necesidades de seguridad


### 7.5 WAF Logging

```yaml
WAF_Logging:
  Enabled: true
  Destination: "CloudWatch Logs"
  Log_Group: "/aws/waf/janis-cencosud-api-gateway"
  Retention_Days: 90
  
  Logged_Fields:
    - "timestamp"
    - "formatVersion"
    - "webaclId"
    - "terminatingRuleId"
    - "terminatingRuleType"
    - "action"
    - "httpSourceName"
    - "httpSourceId"
    - "ruleGroupList"
    - "rateBasedRuleList"
    - "httpRequest"
    - "labels"
  
  Redacted_Fields: [] # Redactar campos sensibles si es necesario
```

**Requisitos del Cliente**:
- Ajustar retention según políticas de compliance corporativo
- Considerar envío de logs a SIEM corporativo si existe
- Implementar alertas de CloudWatch para patrones de ataque
- Redactar campos sensibles (tokens, passwords) si aparecen en logs

**Costo Estimado de WAF**:
- Web ACL: $5/mes
- Rules: $1/mes por regla (4 reglas = $4/mes)
- Managed Rule Groups: $0 (incluidos en AWS)
- Requests: $0.60 por millón de requests
- Logging: Según volumen de CloudWatch Logs
- **Total Base**: ~$10-15/mes + requests

---

## 8. AMAZON EVENTBRIDGE

EventBridge maneja el scheduling inteligente de polling de la API de Janis, reduciendo overhead de MWAA.

### 8.1 Custom Event Bus

```yaml
Custom_Event_Bus:
  Name: "janis-cencosud-polling-bus"
  Description: "Dedicated event bus for Janis API polling operations"
  Event_Source_Name: null # No external event sources
  Tags:
    Project: "janis-cencosud"
    Component: "eventbridge"
    Purpose: "polling-orchestration"
```

**Justificación**: Event bus dedicado facilita:
- Separación de eventos de polling vs otros eventos
- Políticas de acceso específicas
- Monitoreo y troubleshooting simplificado
- Facturación separada por componente


### 8.2 Scheduled Rules (Polling)

#### 8.2.1 Order Polling Rule

```yaml
Order_Polling_Rule:
  Name: "poll-orders-schedule"
  Event_Bus: "janis-cencosud-polling-bus"
  State: "ENABLED"
  Schedule_Expression: "rate(5 minutes)"
  Description: "Trigger MWAA DAG for order polling every 5 minutes"
  
  Target:
    Type: "MWAA_DAG"
    ARN: "<MWAA_ENVIRONMENT_ARN>"
    DAG_Name: "dag_poll_orders"
    Role_ARN: "<EVENTBRIDGE_MWAA_ROLE_ARN>"
    
    Input:
      polling_type: "orders"
      execution_time: "$time" # EventBridge variable
      rule_name: "poll-orders-schedule"
      environment: "<ENVIRONMENT>" # dev/staging/prod
  
  Dead_Letter_Config:
    ARN: "<SQS_DLQ_ARN>"
  
  Retry_Policy:
    Maximum_Event_Age: 3600 # 1 hour
    Maximum_Retry_Attempts: 2
```

**Justificación de Frecuencia**: Órdenes cambian frecuentemente, 5 minutos balancea latencia vs costo.

#### 8.2.2 Product Polling Rule

```yaml
Product_Polling_Rule:
  Name: "poll-products-schedule"
  Event_Bus: "janis-cencosud-polling-bus"
  State: "ENABLED"
  Schedule_Expression: "rate(60 minutes)"
  Description: "Trigger MWAA DAG for product polling every hour"
  
  Target:
    Type: "MWAA_DAG"
    ARN: "<MWAA_ENVIRONMENT_ARN>"
    DAG_Name: "dag_poll_products"
    Role_ARN: "<EVENTBRIDGE_MWAA_ROLE_ARN>"
    
    Input:
      polling_type: "products"
      execution_time: "$time"
      rule_name: "poll-products-schedule"
      environment: "<ENVIRONMENT>"
  
  Dead_Letter_Config:
    ARN: "<SQS_DLQ_ARN>"
  
  Retry_Policy:
    Maximum_Event_Age: 3600
    Maximum_Retry_Attempts: 2
```

**Justificación de Frecuencia**: Productos cambian menos frecuentemente, 1 hora es suficiente.


#### 8.2.3 Stock Polling Rule

```yaml
Stock_Polling_Rule:
  Name: "poll-stock-schedule"
  Event_Bus: "janis-cencosud-polling-bus"
  State: "ENABLED"
  Schedule_Expression: "rate(10 minutes)"
  Description: "Trigger MWAA DAG for stock polling every 10 minutes"
  
  Target:
    Type: "MWAA_DAG"
    ARN: "<MWAA_ENVIRONMENT_ARN>"
    DAG_Name: "dag_poll_stock"
    Role_ARN: "<EVENTBRIDGE_MWAA_ROLE_ARN>"
    
    Input:
      polling_type: "stock"
      execution_time: "$time"
      rule_name: "poll-stock-schedule"
      environment: "<ENVIRONMENT>"
  
  Dead_Letter_Config:
    ARN: "<SQS_DLQ_ARN>"
  
  Retry_Policy:
    Maximum_Event_Age: 3600
    Maximum_Retry_Attempts: 2
```

**Justificación de Frecuencia**: Inventario requiere actualización frecuente para decisiones operacionales.

#### 8.2.4 Price Polling Rule

```yaml
Price_Polling_Rule:
  Name: "poll-prices-schedule"
  Event_Bus: "janis-cencosud-polling-bus"
  State: "ENABLED"
  Schedule_Expression: "rate(30 minutes)"
  Description: "Trigger MWAA DAG for price polling every 30 minutes"
  
  Target:
    Type: "MWAA_DAG"
    ARN: "<MWAA_ENVIRONMENT_ARN>"
    DAG_Name: "dag_poll_prices"
    Role_ARN: "<EVENTBRIDGE_MWAA_ROLE_ARN>"
    
    Input:
      polling_type: "prices"
      execution_time: "$time"
      rule_name: "poll-prices-schedule"
      environment: "<ENVIRONMENT>"
  
  Dead_Letter_Config:
    ARN: "<SQS_DLQ_ARN>"
  
  Retry_Policy:
    Maximum_Event_Age: 3600
    Maximum_Retry_Attempts: 2
```

**Justificación de Frecuencia**: Precios cambian moderadamente, 30 minutos balancea actualidad vs costo.


#### 8.2.5 Store Polling Rule

```yaml
Store_Polling_Rule:
  Name: "poll-stores-schedule"
  Event_Bus: "janis-cencosud-polling-bus"
  State: "ENABLED"
  Schedule_Expression: "rate(1440 minutes)" # 24 hours
  Description: "Trigger MWAA DAG for store polling once daily"
  
  Target:
    Type: "MWAA_DAG"
    ARN: "<MWAA_ENVIRONMENT_ARN>"
    DAG_Name: "dag_poll_stores"
    Role_ARN: "<EVENTBRIDGE_MWAA_ROLE_ARN>"
    
    Input:
      polling_type: "stores"
      execution_time: "$time"
      rule_name: "poll-stores-schedule"
      environment: "<ENVIRONMENT>"
  
  Dead_Letter_Config:
    ARN: "<SQS_DLQ_ARN>"
  
  Retry_Policy:
    Maximum_Event_Age: 3600
    Maximum_Retry_Attempts: 2
```

**Justificación de Frecuencia**: Tiendas cambian raramente, 1 vez al día es suficiente.

### 8.3 Dead Letter Queue (DLQ)

```yaml
EventBridge_DLQ:
  Type: "SQS"
  Name: "janis-cencosud-eventbridge-dlq"
  Message_Retention_Period: 1209600 # 14 days
  Visibility_Timeout: 300 # 5 minutes
  Receive_Wait_Time: 0 # Short polling
  
  Encryption:
    Type: "SSE-SQS" # Server-side encryption
    KMS_Master_Key_ID: null # Use AWS managed key
  
  CloudWatch_Alarms:
    - Metric: "ApproximateNumberOfMessagesVisible"
      Threshold: 0
      Comparison: "GreaterThanThreshold"
      Evaluation_Periods: 1
      Action: "<SNS_TOPIC_ARN>" # Alert on any failed events
```

**Propósito**: Capturar eventos que fallan al invocar MWAA para análisis y reprocessamiento manual.

**Requisitos del Cliente**:
- Configurar SNS topic para alertas de mensajes en DLQ
- Implementar proceso de revisión y reprocessamiento de eventos fallidos
- Considerar Lambda function para reprocessamiento automático de ciertos errores


### 8.4 IAM Role para EventBridge → MWAA

```yaml
EventBridge_MWAA_Role:
  Name: "janis-cencosud-eventbridge-mwaa-role"
  Description: "IAM role for EventBridge to invoke MWAA DAGs"
  
  Trust_Policy:
    Service: "events.amazonaws.com"
  
  Permissions:
    - Effect: "Allow"
      Actions:
        - "airflow:CreateCliToken"
      Resources:
        - "<MWAA_ENVIRONMENT_ARN>"
    
    - Effect: "Allow"
      Actions:
        - "sqs:SendMessage"
      Resources:
        - "<SQS_DLQ_ARN>"
```

**Requisitos del Cliente**:
- Aplicar principio de menor privilegio
- Restringir recursos a ARNs específicos (no usar wildcards)
- Auditar uso del role regularmente

**Costo Estimado de EventBridge**:
- Custom Event Bus: Sin costo
- Rules: Sin costo (primeras 100 rules)
- Invocations: $1 por millón de invocaciones
- Estimado mensual: ~$1-2 (basado en frecuencias de polling)

---

## 9. MONITOREO Y LOGGING

### 9.1 VPC Flow Logs

```yaml
VPC_Flow_Logs:
  Name: "janis-cencosud-vpc-flow-logs"
  Resource_Type: "VPC"
  Resource_ID: "<VPC_ID>"
  Traffic_Type: "ALL" # Capture accepted and rejected traffic
  
  Destination:
    Type: "CloudWatch_Logs"
    Log_Group: "/aws/vpc/flow-logs/janis-cencosud"
    IAM_Role: "<VPC_FLOW_LOGS_ROLE_ARN>"
  
  Log_Format: "DEFAULT" # Use AWS default format
  
  Log_Fields:
    - "version"
    - "account-id"
    - "interface-id"
    - "srcaddr"
    - "dstaddr"
    - "srcport"
    - "dstport"
    - "protocol"
    - "packets"
    - "bytes"
    - "start"
    - "end"
    - "action" # ACCEPT or REJECT
    - "log-status"
  
  Retention_Days: 90
  
  Tags:
    Project: "janis-cencosud"
    Component: "vpc-flow-logs"
    Purpose: "security-audit"
```


**Casos de Uso**:
- Troubleshooting de conectividad
- Detección de patrones de tráfico anómalos
- Auditoría de seguridad y compliance
- Análisis forense post-incidente
- Identificación de recursos que generan más tráfico

**Requisitos del Cliente**:
- Ajustar retention según políticas de compliance corporativo
- Considerar exportación a S3 para análisis de largo plazo
- Implementar CloudWatch Logs Insights queries para análisis común
- Integrar con SIEM corporativo si existe

### 9.2 DNS Query Logging

```yaml
DNS_Query_Logging:
  Name: "janis-cencosud-dns-query-logs"
  VPC_ID: "<VPC_ID>"
  
  Destination:
    Type: "CloudWatch_Logs"
    Log_Group: "/aws/route53/janis-cencosud-dns-queries"
  
  Retention_Days: 90
  
  Logged_Fields:
    - "version"
    - "account_id"
    - "region"
    - "vpc_id"
    - "query_timestamp"
    - "query_name"
    - "query_type"
    - "query_class"
    - "rcode"
    - "answers"
    - "srcaddr"
    - "srcport"
    - "transport"
    - "srcids"
```

**Casos de Uso**:
- Detectar DNS tunneling (exfiltración de datos)
- Identificar comunicación con dominios maliciosos
- Troubleshooting de resolución DNS
- Auditoría de acceso a servicios externos

**Requisitos del Cliente**:
- Implementar alertas para queries a dominios sospechosos
- Integrar con threat intelligence feeds
- Considerar análisis de frecuencia de queries para detectar anomalías


### 9.3 CloudWatch Alarms

#### 9.3.1 NAT Gateway Alarms

```yaml
NAT_Gateway_Alarms:
  
  - Name: "janis-cencosud-nat-gateway-connection-errors"
    Metric: "ErrorPortAllocation"
    Namespace: "AWS/NATGateway"
    Statistic: "Sum"
    Period: 300 # 5 minutes
    Evaluation_Periods: 2
    Threshold: 10
    Comparison: "GreaterThanThreshold"
    Actions:
      - "<SNS_TOPIC_ARN>"
    Description: "Alert when NAT Gateway has port allocation errors"
  
  - Name: "janis-cencosud-nat-gateway-packets-drop"
    Metric: "PacketsDropCount"
    Namespace: "AWS/NATGateway"
    Statistic: "Sum"
    Period: 300
    Evaluation_Periods: 2
    Threshold: 1000
    Comparison: "GreaterThanThreshold"
    Actions:
      - "<SNS_TOPIC_ARN>"
    Description: "Alert when NAT Gateway drops packets"
```

#### 9.3.2 VPC Flow Logs Alarms

```yaml
VPC_Flow_Logs_Alarms:
  
  - Name: "janis-cencosud-rejected-connections-spike"
    Metric_Filter:
      Pattern: "[version, account, eni, source, destination, srcport, dstport, protocol, packets, bytes, windowstart, windowend, action=REJECT, flowlogstatus]"
      Metric_Name: "RejectedConnections"
      Metric_Namespace: "JanisCencosud/VPC"
      Metric_Value: "1"
    
    Alarm:
      Statistic: "Sum"
      Period: 300
      Evaluation_Periods: 1
      Threshold: 100
      Comparison: "GreaterThanThreshold"
      Actions:
        - "<SNS_TOPIC_ARN>"
      Description: "Alert on spike in rejected connections"
```

#### 9.3.3 EventBridge Alarms

```yaml
EventBridge_Alarms:
  
  - Name: "janis-cencosud-eventbridge-failed-invocations"
    Metric: "FailedInvocations"
    Namespace: "AWS/Events"
    Dimensions:
      - Name: "RuleName"
        Value: "*" # All rules
    Statistic: "Sum"
    Period: 300
    Evaluation_Periods: 1
    Threshold: 5
    Comparison: "GreaterThanThreshold"
    Actions:
      - "<SNS_TOPIC_ARN>"
    Description: "Alert when EventBridge rules fail to invoke targets"
```

**Requisitos del Cliente**:
- Configurar SNS topics para notificaciones (email, SMS, Slack, etc.)
- Ajustar thresholds según patrones de tráfico observados
- Implementar escalation policies para alertas críticas
- Integrar con sistema de incident management corporativo


---

## 10. ESTRATEGIA DE TAGGING

Tags consistentes son críticos para gestión de costos, seguridad, y operaciones.

### 10.1 Tags Obligatorios

Todos los recursos AWS deben incluir estos tags:

```yaml
Mandatory_Tags:
  Project:
    Description: "Nombre del proyecto"
    Value: "janis-cencosud-integration"
    Validation: "Must match approved project names"
  
  Environment:
    Description: "Ambiente de deployment"
    Values: ["development", "staging", "production"]
    Validation: "Must be one of the allowed values"
  
  Component:
    Description: "Componente específico de la arquitectura"
    Examples: ["vpc", "lambda", "glue", "redshift", "eventbridge", "waf"]
    Validation: "Must be descriptive and consistent"
  
  Owner:
    Description: "Equipo responsable del recurso"
    Value: "data-engineering-team"
    Validation: "Must match approved team names"
  
  CostCenter:
    Description: "Centro de costos para facturación"
    Value: "<COST_CENTER_CODE>"
    Validation: "Must match approved cost center codes"
```

### 10.2 Tags Opcionales

```yaml
Optional_Tags:
  CreatedBy:
    Description: "Usuario o sistema que creó el recurso"
    Examples: ["terraform", "cloudformation", "john.doe@cencosud.com"]
  
  CreatedDate:
    Description: "Fecha de creación del recurso"
    Format: "YYYY-MM-DD"
    Example: "2026-01-21"
  
  LastModified:
    Description: "Fecha de última modificación"
    Format: "YYYY-MM-DD"
    Example: "2026-01-21"
  
  BackupPolicy:
    Description: "Política de backup aplicable"
    Examples: ["daily", "weekly", "none"]
  
  DataClassification:
    Description: "Clasificación de datos según política corporativa"
    Examples: ["public", "internal", "confidential", "restricted"]
```


### 10.3 Enforcement de Tags

**Terraform Default Tags**:
```hcl
provider "aws" {
  region = var.aws_region
  
  default_tags {
    tags = {
      Project     = "janis-cencosud-integration"
      Environment = var.environment
      Owner       = "data-engineering-team"
      CostCenter  = var.cost_center
      ManagedBy   = "terraform"
    }
  }
}
```

**AWS Config Rules**:
```yaml
Tag_Compliance_Rules:
  
  - Rule_Name: "required-tags"
    Source: "AWS_MANAGED"
    Identifier: "REQUIRED_TAGS"
    Parameters:
      tag1Key: "Project"
      tag2Key: "Environment"
      tag3Key: "Component"
      tag4Key: "Owner"
      tag5Key: "CostCenter"
    Remediation: "Manual or automated tag addition"
  
  - Rule_Name: "tag-value-validation"
    Source: "CUSTOM_LAMBDA"
    Description: "Validate tag values match approved lists"
    Lambda_Function: "<TAG_VALIDATION_LAMBDA_ARN>"
```

**Requisitos del Cliente**:
- Adaptar tags según estándares corporativos de Cencosud
- Implementar proceso de aprobación para nuevos valores de tags
- Auditar compliance de tags regularmente
- Automatizar corrección de tags faltantes o incorrectos

---

## 11. INTEGRACIÓN CON INFRAESTRUCTURA EXISTENTE

### 11.1 Redshift Cluster Existente

**Información Requerida del Cliente**:

```yaml
Existing_Redshift_Cluster:
  Cluster_Identifier: "<REDSHIFT_CLUSTER_ID>"
  Endpoint: "<REDSHIFT_ENDPOINT>"
  Port: 5439
  Database_Name: "<DATABASE_NAME>"
  VPC_ID: "<EXISTING_VPC_ID>" # Si está en VPC diferente
  Security_Group_ID: "<EXISTING_REDSHIFT_SG>"
  Subnet_Group: "<EXISTING_SUBNET_GROUP>"
  
  Network_Configuration:
    Same_VPC: true/false
    VPC_Peering_Required: true/false
    Transit_Gateway_Required: true/false
  
  Access_Requirements:
    - Source: "Lambda functions"
      Protocol: "PostgreSQL"
      Port: 5439
      Authentication: "IAM or Username/Password"
    
    - Source: "MWAA Airflow"
      Protocol: "PostgreSQL"
      Port: 5439
      Authentication: "IAM or Username/Password"
    
    - Source: "Existing BI Systems"
      IPs_or_Security_Groups: ["<IP_RANGE_1>", "<SG_ID_1>"]
      Must_Not_Disrupt: true
```


**Acciones Requeridas**:

1. **Si Redshift está en la misma VPC**:
   - Actualizar security group de Redshift para permitir conexiones desde SG-Lambda y SG-MWAA
   - Verificar que no se interrumpa acceso existente de sistemas BI

2. **Si Redshift está en VPC diferente**:
   - Configurar VPC Peering entre VPCs
   - Actualizar route tables en ambas VPCs
   - Configurar security groups para permitir tráfico cross-VPC
   - Alternativa: Usar AWS Transit Gateway si hay múltiples VPCs

3. **Autenticación**:
   - Preferir IAM authentication para Lambda y MWAA
   - Almacenar credenciales username/password en AWS Secrets Manager como fallback
   - Rotar credenciales regularmente

### 11.2 Sistemas BI Existentes

**Información Requerida del Cliente**:

```yaml
Existing_BI_Systems:
  - System_Name: "Power BI"
    Connection_Type: "Direct Query or Import"
    Source_IPs: ["<IP_RANGE>"]
    Security_Group: "<SG_ID>"
    Access_Pattern: "Read-only queries to Redshift"
    Must_Not_Disrupt: true
  
  - System_Name: "Tableau"
    Connection_Type: "Live Connection"
    Source_IPs: ["<IP_RANGE>"]
    Security_Group: "<SG_ID>"
    Access_Pattern: "Read-only queries to Redshift"
    Must_Not_Disrupt: true
  
  - System_Name: "<OTHER_BI_TOOL>"
    Connection_Type: "<CONNECTION_TYPE>"
    Source_IPs: ["<IP_RANGE>"]
    Security_Group: "<SG_ID>"
    Access_Pattern: "<ACCESS_PATTERN>"
    Must_Not_Disrupt: true
```

**Acciones Requeridas**:
- Documentar todos los sistemas BI que acceden a Redshift
- Verificar que security group rules no interrumpan acceso existente
- Coordinar testing de conectividad con equipos de BI
- Implementar monitoreo de queries de BI para detectar impacto


### 11.3 Pipeline MySQL → Redshift Actual

**Información Requerida del Cliente**:

```yaml
Current_MySQL_Pipeline:
  Source:
    Type: "MySQL Database"
    Location: "<MYSQL_HOST>"
    Database: "<DATABASE_NAME>"
    Connection_Method: "<VPN/Direct Connect/Public>"
  
  ETL_Tool:
    Name: "<ETL_TOOL_NAME>" # e.g., AWS DMS, Talend, custom scripts
    Location: "<EC2/On-Premise/Other>"
    Security_Group: "<SG_ID>"
  
  Destination:
    Type: "Redshift"
    Cluster: "<REDSHIFT_CLUSTER_ID>"
    Schema: "<SCHEMA_NAME>"
    Tables: ["<TABLE_1>", "<TABLE_2>", "..."]
  
  Migration_Plan:
    Phase_1: "Deploy new pipeline in parallel"
    Phase_2: "Validate data consistency"
    Phase_3: "Cutover to new pipeline"
    Phase_4: "Decommission old pipeline"
    Rollback_Plan: "Revert to old pipeline if issues"
```

**Acciones Requeridas**:
1. Mantener pipeline MySQL→Redshift operacional durante migración
2. Crear tablas paralelas en Redshift con sufijo `_new` para validación
3. Implementar proceso de validación de datos (row counts, checksums, sample queries)
4. Coordinar cutover con equipos de BI y negocio
5. Documentar procedimiento de rollback
6. Remover security group rules del pipeline antiguo después de decommission

---

## 12. LIMITACIONES Y CONSIDERACIONES DE SINGLE-AZ

### 12.1 Single Points of Failure Identificados

```yaml
Single_Points_of_Failure:
  
  NAT_Gateway:
    Location: "Public Subnet A (us-east-1a)"
    Impact_if_Failed: "Subnets privadas pierden conectividad saliente"
    Services_Affected:
      - "Lambda functions (no pueden llamar APIs externas)"
      - "AWS Glue jobs (no pueden acceder a internet)"
      - "MWAA Airflow (no puede instalar packages de PyPI)"
    Mitigation: "Webhooks continúan funcionando (API Gateway no depende de NAT)"
    Recovery_Time: "Manual - crear nuevo NAT Gateway (~5-10 minutos)"
    Cost_to_Eliminate: "$32.40/mes (segundo NAT Gateway en us-east-1b)"
  
  Availability_Zone:
    Location: "us-east-1a"
    Impact_if_Failed: "Sistema completo offline"
    Services_Affected: "Todos los servicios"
    Mitigation: "Datos en S3 no se pierden, recovery automático cuando AZ vuelve"
    Recovery_Time: "Depende de AWS (típicamente minutos a horas)"
    Cost_to_Eliminate: "$45-90/mes (segundo NAT Gateway + recursos duplicados)"
```


### 12.2 Análisis de Riesgo

```yaml
Risk_Assessment:
  
  Probability_of_AZ_Failure:
    Historical_Data: "< 0.1% anual por AZ (AWS SLA)"
    Expected_Downtime: "< 8.76 horas/año"
    Business_Impact: "<CLIENTE_DEBE_EVALUAR>"
  
  Probability_of_NAT_Gateway_Failure:
    Historical_Data: "Muy baja (managed service con 99.95% SLA)"
    Expected_Downtime: "< 4.38 horas/año"
    Business_Impact: "<CLIENTE_DEBE_EVALUAR>"
  
  Cost_Benefit_Analysis:
    Single_AZ_Cost: "$101.60-142.60/mes"
    Multi_AZ_Cost: "$146.60-232.60/mes"
    Additional_Cost: "$45-90/mes"
    Availability_Improvement: "99.5% → 99.99%"
    Decision: "<CLIENTE_DEBE_DECIDIR>"
```

**Requisitos del Cliente**:
- Evaluar tolerancia del negocio a downtime
- Calcular costo de downtime vs costo de Multi-AZ
- Definir RTO (Recovery Time Objective) y RPO (Recovery Point Objective)
- Documentar decisión y justificación

### 12.3 Path de Migración a Multi-AZ

**Fase 1: Preparación (Sin Downtime)**
```yaml
Phase_1_Preparation:
  Duration: "1-2 días"
  Downtime: "Ninguno"
  
  Tasks:
    - Create_Subnets:
        - "Public Subnet B (10.0.2.0/24) en us-east-1b"
        - "Private Subnet 1B (10.0.11.0/24) en us-east-1b"
        - "Private Subnet 2B (10.0.21.0/24) en us-east-1b"
    
    - Create_NAT_Gateway:
        Location: "Public Subnet B"
        Elastic_IP: "Allocate new EIP"
    
    - Update_Route_Tables:
        - "Create new private route table for us-east-1b subnets"
        - "Route 0.0.0.0/0 to new NAT Gateway"
    
    - Update_VPC_Endpoints:
        - "Associate Interface Endpoints with new subnets"
```


**Fase 2: Deployment Multi-AZ (Downtime Mínimo)**
```yaml
Phase_2_Deployment:
  Duration: "2-4 horas"
  Downtime: "< 5 minutos (durante cutover)"
  
  Tasks:
    - Deploy_Lambda:
        Configuration: "Deploy functions in both AZs"
        Method: "Update Lambda VPC configuration to include both subnets"
    
    - Configure_MWAA:
        Configuration: "Enable Multi-AZ for MWAA environment"
        Method: "Update MWAA environment configuration"
        Note: "Requires environment restart (~20 minutes)"
    
    - Migrate_Redshift:
        Option_1: "Keep in single AZ (Redshift handles AZ failure internally)"
        Option_2: "Enable Multi-AZ for Redshift (if supported by cluster type)"
        Recommendation: "Option 1 - Redshift ya tiene redundancia interna"
    
    - Update_Security_Groups:
        Action: "Verify all security groups allow traffic from both AZs"
```

**Fase 3: Testing y Validación**
```yaml
Phase_3_Testing:
  Duration: "1-2 días"
  
  Tests:
    - Connectivity_Test:
        Description: "Verify all services can communicate across AZs"
        Method: "Execute test transactions through entire pipeline"
    
    - Failover_Test:
        Description: "Simulate AZ failure"
        Method: "Disable NAT Gateway in us-east-1a, verify traffic routes through us-east-1b"
        Expected_Result: "No service interruption"
    
    - Performance_Test:
        Description: "Measure latency impact of Multi-AZ"
        Method: "Compare response times before/after"
        Expected_Result: "< 5ms increase in latency"
    
    - Cost_Validation:
        Description: "Verify actual cost increase matches estimates"
        Method: "Monitor AWS Cost Explorer for 1 week"
```

**Fase 4: Monitoreo Post-Migración**
```yaml
Phase_4_Monitoring:
  Duration: "30 días"
  
  Metrics:
    - Availability: "Track uptime and incidents"
    - Performance: "Monitor latency and throughput"
    - Cost: "Validate cost increase is within budget"
    - Errors: "Monitor error rates and failed transactions"
```

---

## 13. ESTIMACIÓN DE COSTOS

### 13.1 Costos Mensuales - Single-AZ (Producción)

```yaml
Infrastructure_Costs_Single_AZ:
  
  Networking:
    VPC: "$0"
    Internet_Gateway: "$0"
    NAT_Gateway_Hours: "$32.40" # $0.045/hour × 720 hours
    NAT_Gateway_Data_Transfer: "$10-30" # $0.045/GB (variable)
    Elastic_IP_NAT: "$0" # Sin costo si está attached
  
  VPC_Endpoints:
    S3_Gateway_Endpoint: "$0"
    Interface_Endpoints_Hours: "$43.20" # 6 endpoints × $0.01/hour × 720 hours
    Interface_Endpoints_Data: "$5-15" # $0.01/GB (variable)
  
  Security:
    Security_Groups: "$0"
    NACLs: "$0"
    WAF_Web_ACL: "$5"
    WAF_Rules: "$4" # 4 custom rules × $1/rule
    WAF_Managed_Rules: "$0"
    WAF_Requests: "$0.60" # Per million requests (variable)
  
  Orchestration:
    EventBridge_Custom_Bus: "$0"
    EventBridge_Rules: "$0" # First 100 rules free
    EventBridge_Invocations: "$1-2" # $1 per million invocations
    SQS_DLQ: "$0.40" # Minimal usage expected
  
  Monitoring:
    VPC_Flow_Logs: "$5-10" # Ingestion + storage
    DNS_Query_Logs: "$2-5"
    CloudWatch_Alarms: "$0.10" # $0.10 per alarm
    CloudWatch_Dashboards: "$3" # $3 per dashboard
  
  Total_Monthly_Single_AZ: "$111.70-152.70"
```


### 13.2 Costos Mensuales - Multi-AZ (Producción)

```yaml
Infrastructure_Costs_Multi_AZ:
  
  Networking:
    VPC: "$0"
    Internet_Gateway: "$0"
    NAT_Gateway_1_Hours: "$32.40"
    NAT_Gateway_2_Hours: "$32.40" # Second NAT Gateway
    NAT_Gateway_Data_Transfer: "$15-40" # Slightly higher with two gateways
    Elastic_IPs: "$0" # Both attached
  
  VPC_Endpoints:
    S3_Gateway_Endpoint: "$0"
    Interface_Endpoints_Hours: "$43.20" # Same endpoints, more ENIs
    Interface_Endpoints_Data: "$5-15"
  
  Security:
    Security_Groups: "$0"
    NACLs: "$0"
    WAF_Web_ACL: "$5"
    WAF_Rules: "$4"
    WAF_Managed_Rules: "$0"
    WAF_Requests: "$0.60"
  
  Orchestration:
    EventBridge_Custom_Bus: "$0"
    EventBridge_Rules: "$0"
    EventBridge_Invocations: "$1-2"
    SQS_DLQ: "$0.40"
  
  Monitoring:
    VPC_Flow_Logs: "$8-15" # More traffic to log
    DNS_Query_Logs: "$3-7"
    CloudWatch_Alarms: "$0.20" # More alarms
    CloudWatch_Dashboards: "$3"
  
  Total_Monthly_Multi_AZ: "$148.20-202.20"
  
  Additional_Cost_vs_Single_AZ: "$36.50-49.50"
```

### 13.3 Costos por Ambiente

```yaml
Cost_by_Environment:
  
  Development:
    Infrastructure: "$50-80/mes"
    Notes: "Recursos más pequeños, menos tráfico, Single-AZ"
  
  Staging:
    Infrastructure: "$80-120/mes"
    Notes: "Recursos medianos, tráfico moderado, Single-AZ"
  
  Production_Single_AZ:
    Infrastructure: "$111.70-152.70/mes"
    Notes: "Recursos completos, tráfico real, Single-AZ"
  
  Production_Multi_AZ:
    Infrastructure: "$148.20-202.20/mes"
    Notes: "Recursos completos, tráfico real, Multi-AZ"
  
  Total_All_Environments_Single_AZ: "$241.70-352.70/mes"
  Total_All_Environments_Multi_AZ: "$278.20-402.20/mes"
```

**Nota**: Estos costos son solo para infraestructura base. No incluyen:
- Lambda execution costs
- MWAA environment costs
- Glue job execution costs
- Redshift cluster costs
- S3 storage and requests
- Data transfer out to internet


---

## 14. REQUISITOS DE IMPLEMENTACIÓN PARA EL CLIENTE

### 14.1 Información Requerida Antes de Implementación

El cliente debe proporcionar la siguiente información:

```yaml
Required_Information:
  
  AWS_Account:
    Account_ID: "<AWS_ACCOUNT_ID>"
    Region: "us-east-1" # Confirmar o cambiar
    Access_Method: "IAM User / IAM Role / SSO"
  
  Networking:
    VPC_CIDR_Confirmation: "10.0.0.0/16 o alternativo si hay conflicto"
    Existing_Network_Ranges: ["<CORPORATE_CIDR_1>", "<CORPORATE_CIDR_2>"]
    VPN_or_Direct_Connect: "Yes/No"
  
  Redshift:
    Cluster_ID: "<REDSHIFT_CLUSTER_ID>"
    Endpoint: "<REDSHIFT_ENDPOINT>"
    Port: 5439
    VPC_ID: "<VPC_ID>"
    Security_Group_ID: "<SG_ID>"
    Same_VPC_as_New_Infrastructure: "Yes/No"
  
  BI_Systems:
    - System_Name: "<BI_TOOL_NAME>"
      Source_IPs: ["<IP_RANGE>"]
      Security_Group: "<SG_ID>"
  
  Security_Policies:
    Allowed_Inbound_IPs: ["<JANIS_IP_RANGES>"]
    Encryption_Requirements: "<ENCRYPTION_STANDARDS>"
    Compliance_Requirements: ["<COMPLIANCE_1>", "<COMPLIANCE_2>"]
  
  Tagging_Standards:
    Project_Name: "<APPROVED_PROJECT_NAME>"
    Cost_Center: "<COST_CENTER_CODE>"
    Owner_Team: "<TEAM_NAME>"
    Additional_Required_Tags: {}
  
  Monitoring:
    SNS_Topic_for_Alarms: "<SNS_TOPIC_ARN>"
    Email_for_Alerts: "<EMAIL_ADDRESS>"
    Integration_with_SIEM: "Yes/No"
    SIEM_Endpoint: "<SIEM_ENDPOINT>"
  
  Budget:
    Monthly_Budget: "<BUDGET_AMOUNT>"
    Cost_Alerts_Threshold: "<THRESHOLD_PERCENTAGE>"
```


### 14.2 Decisiones Requeridas del Cliente

```yaml
Client_Decisions:
  
  High_Availability:
    Question: "¿Desplegar en Single-AZ o Multi-AZ?"
    Options:
      - "Single-AZ: Menor costo, mayor riesgo"
      - "Multi-AZ: Mayor costo, alta disponibilidad"
    Impact: "$36.50-49.50/mes adicional para Multi-AZ"
    Recommendation: "Single-AZ para MVP, migrar a Multi-AZ después"
  
  VPC_CIDR:
    Question: "¿Usar 10.0.0.0/16 o CIDR alternativo?"
    Validation: "Verificar que no conflictúe con redes corporativas"
    Impact: "Cambio de CIDR requiere actualizar todas las especificaciones"
  
  WAF_Configuration:
    Question: "¿Ajustar límites de rate limiting?"
    Current: "2,000 requests per IP en 5 minutos"
    Consideration: "Basado en patrones de tráfico esperados de Janis"
  
  Geo_Blocking:
    Question: "¿Permitir solo Perú o países adicionales?"
    Current: "Solo Perú (PE)"
    Consideration: "Si Cencosud tiene operaciones internacionales"
  
  Monitoring_Retention:
    Question: "¿Cuántos días retener logs?"
    Current: "90 días"
    Options: ["30 días", "90 días", "180 días", "365 días"]
    Impact: "Mayor retention = mayor costo de CloudWatch Logs"
  
  Backup_Strategy:
    Question: "¿Política de backup para state files de Terraform?"
    Options:
      - "Manual backups antes de cada apply"
      - "Automated backups diarios"
      - "Remote state en S3 con versioning"
    Recommendation: "Remote state en S3 para producción"
```

### 14.3 Adaptaciones Requeridas a Políticas Corporativas

El cliente debe adaptar las siguientes áreas según sus políticas internas:

```yaml
Corporate_Policy_Adaptations:
  
  Security_Groups:
    Action: "Revisar y ajustar reglas según políticas de firewall corporativo"
    Examples:
      - "Restringir source IPs a rangos conocidos"
      - "Eliminar reglas 0.0.0.0/0 si no son necesarias"
      - "Agregar reglas para herramientas de monitoreo corporativo"
  
  Tagging:
    Action: "Reemplazar tags con estándares corporativos de Cencosud"
    Examples:
      - "Agregar tags de compliance corporativo"
      - "Usar nomenclatura de cost centers de Cencosud"
      - "Incluir tags de data classification"
  
  Encryption:
    Action: "Aplicar estándares de cifrado corporativo"
    Examples:
      - "Usar KMS keys corporativos en lugar de AWS managed keys"
      - "Aplicar políticas de rotación de keys"
      - "Configurar encryption en tránsito según estándares"
  
  Logging:
    Action: "Integrar con sistemas de logging corporativo"
    Examples:
      - "Enviar logs a SIEM corporativo"
      - "Aplicar retention policies corporativas"
      - "Configurar alertas según procedimientos de incident response"
  
  IAM:
    Action: "Aplicar políticas de IAM corporativas"
    Examples:
      - "Usar IAM roles corporativos"
      - "Aplicar permission boundaries"
      - "Integrar con SSO corporativo"
```


---

## 15. CHECKLIST DE IMPLEMENTACIÓN

### 15.1 Pre-Implementación

```yaml
Pre_Implementation_Checklist:
  
  Planning:
    - [ ] Revisar especificaciones completas con equipo técnico
    - [ ] Validar que VPC CIDR no conflictúe con redes corporativas
    - [ ] Obtener aprobación de arquitectura de seguridad corporativa
    - [ ] Confirmar presupuesto y aprobación de costos
    - [ ] Identificar stakeholders y puntos de contacto
  
  Information_Gathering:
    - [ ] Recopilar información de Redshift cluster existente
    - [ ] Documentar sistemas BI que acceden a Redshift
    - [ ] Obtener rangos de IPs de Janis para whitelist
    - [ ] Definir políticas de tagging corporativas
    - [ ] Identificar SNS topics para alertas
  
  Access_and_Permissions:
    - [ ] Configurar acceso AWS (IAM users/roles)
    - [ ] Configurar credenciales para Terraform
    - [ ] Verificar permisos necesarios para crear recursos
    - [ ] Configurar acceso a AWS Secrets Manager
  
  Tooling:
    - [ ] Instalar Terraform >= 1.0
    - [ ] Configurar AWS CLI
    - [ ] Configurar Git para versionado de código
    - [ ] Preparar ambiente de desarrollo
```

### 15.2 Implementación por Fases

```yaml
Implementation_Phases:
  
  Phase_1_VPC_and_Networking:
    Duration: "1-2 días"
    Tasks:
      - [ ] Crear VPC con CIDR 10.0.0.0/16
      - [ ] Crear subnets (pública y privadas)
      - [ ] Crear Internet Gateway
      - [ ] Crear NAT Gateway con Elastic IP
      - [ ] Configurar route tables
      - [ ] Validar conectividad básica
    Validation:
      - [ ] VPC creado correctamente
      - [ ] Subnets en AZ correcta
      - [ ] Routing configurado
      - [ ] Tags aplicados
  
  Phase_2_VPC_Endpoints:
    Duration: "1 día"
    Tasks:
      - [ ] Crear S3 Gateway Endpoint
      - [ ] Crear Interface Endpoints (Glue, Secrets Manager, etc.)
      - [ ] Configurar Private DNS
      - [ ] Asociar endpoints con subnets
    Validation:
      - [ ] Endpoints creados y disponibles
      - [ ] Private DNS resolviendo correctamente
      - [ ] Asociaciones de subnet correctas
  
  Phase_3_Security_Groups:
    Duration: "1 día"
    Tasks:
      - [ ] Crear todos los security groups
      - [ ] Configurar reglas inbound/outbound
      - [ ] Configurar self-references donde necesario
      - [ ] Actualizar SG de Redshift existente
    Validation:
      - [ ] Todos los security groups creados
      - [ ] Reglas configuradas según especificación
      - [ ] No se interrumpe acceso existente a Redshift
  
  Phase_4_NACLs:
    Duration: "0.5 días"
    Tasks:
      - [ ] Crear NACLs para subnet pública
      - [ ] Crear NACLs para subnets privadas
      - [ ] Asociar NACLs con subnets
    Validation:
      - [ ] NACLs creados y asociados
      - [ ] Reglas en orden de prioridad correcto
      - [ ] Tráfico permitido según especificación
```


```yaml
  Phase_5_WAF:
    Duration: "0.5 días"
    Tasks:
      - [ ] Crear WAF Web ACL
      - [ ] Configurar rate limiting rule
      - [ ] Configurar geo-blocking rule
      - [ ] Agregar AWS Managed Rules
      - [ ] Configurar logging a CloudWatch
      - [ ] Asociar WAF con API Gateway (cuando esté disponible)
    Validation:
      - [ ] WAF Web ACL creado
      - [ ] Reglas configuradas y habilitadas
      - [ ] Logging funcionando
  
  Phase_6_EventBridge:
    Duration: "1 día"
    Tasks:
      - [ ] Crear custom event bus
      - [ ] Crear scheduled rules para polling
      - [ ] Configurar targets (MWAA DAGs)
      - [ ] Crear Dead Letter Queue (SQS)
      - [ ] Configurar IAM role para EventBridge→MWAA
    Validation:
      - [ ] Event bus creado
      - [ ] Todas las rules creadas y habilitadas
      - [ ] DLQ configurado
      - [ ] IAM permissions correctas
  
  Phase_7_Monitoring:
    Duration: "1 día"
    Tasks:
      - [ ] Habilitar VPC Flow Logs
      - [ ] Habilitar DNS Query Logging
      - [ ] Crear CloudWatch alarms
      - [ ] Configurar SNS topics para alertas
      - [ ] Crear CloudWatch dashboards
    Validation:
      - [ ] Logs fluyendo a CloudWatch
      - [ ] Alarms configuradas y funcionando
      - [ ] Alertas llegando a destinatarios correctos
  
  Phase_8_Testing:
    Duration: "2-3 días"
    Tasks:
      - [ ] Testing de conectividad end-to-end
      - [ ] Validar acceso a Redshift desde Lambda/MWAA
      - [ ] Validar VPC Endpoints funcionando
      - [ ] Testing de WAF rules
      - [ ] Testing de EventBridge triggers
      - [ ] Validar que sistemas BI existentes siguen funcionando
    Validation:
      - [ ] Todos los tests pasando
      - [ ] No hay impacto en sistemas existentes
      - [ ] Performance dentro de expectativas
```

### 15.3 Post-Implementación

```yaml
Post_Implementation_Checklist:
  
  Documentation:
    - [ ] Documentar todos los recursos creados con ARNs
    - [ ] Documentar procedimientos operacionales
    - [ ] Crear runbooks para troubleshooting común
    - [ ] Documentar procedimiento de rollback
    - [ ] Actualizar diagramas de arquitectura
  
  Handover:
    - [ ] Training a equipo de operaciones
    - [ ] Transferir accesos y credenciales
    - [ ] Documentar contactos de soporte
    - [ ] Establecer procedimientos de escalation
  
  Monitoring:
    - [ ] Configurar monitoreo de costos
    - [ ] Establecer alertas de budget
    - [ ] Monitorear métricas de performance
    - [ ] Revisar logs regularmente
  
  Optimization:
    - [ ] Revisar costos después de 1 mes
    - [ ] Ajustar alarmas según patrones observados
    - [ ] Optimizar security group rules si es necesario
    - [ ] Planificar mejoras futuras
```

---

## 16. TROUBLESHOOTING Y OPERACIONES

### 16.1 Problemas Comunes y Soluciones


```yaml
Common_Issues:
  
  Issue_1_No_Internet_Connectivity_from_Private_Subnets:
    Symptoms:
      - "Lambda functions timeout al llamar APIs externas"
      - "Glue jobs fallan al descargar dependencies"
      - "MWAA no puede instalar packages de PyPI"
    Possible_Causes:
      - "NAT Gateway no creado o no funcionando"
      - "Route table no apunta a NAT Gateway"
      - "Security groups bloqueando tráfico saliente"
      - "NACLs bloqueando tráfico"
    Troubleshooting:
      - "Verificar NAT Gateway status en consola AWS"
      - "Verificar route table de subnets privadas"
      - "Verificar security group outbound rules"
      - "Revisar VPC Flow Logs para tráfico REJECT"
    Solution:
      - "Crear NAT Gateway si no existe"
      - "Actualizar route table: 0.0.0.0/0 → NAT Gateway"
      - "Agregar regla outbound en security group"
      - "Ajustar NACL rules para permitir tráfico"
  
  Issue_2_Cannot_Connect_to_Redshift:
    Symptoms:
      - "Lambda/MWAA timeout al conectar a Redshift"
      - "Connection refused errors"
    Possible_Causes:
      - "Security group de Redshift no permite conexiones"
      - "Lambda/MWAA no están en VPC correcta"
      - "Credenciales incorrectas"
      - "Redshift cluster no disponible"
    Troubleshooting:
      - "Verificar security group rules de Redshift"
      - "Verificar que Lambda/MWAA están en subnets privadas"
      - "Verificar credenciales en Secrets Manager"
      - "Verificar status de Redshift cluster"
    Solution:
      - "Agregar regla inbound en SG-Redshift desde SG-Lambda/SG-MWAA"
      - "Configurar Lambda/MWAA en VPC correcta"
      - "Actualizar credenciales en Secrets Manager"
      - "Esperar a que Redshift cluster esté disponible"
  
  Issue_3_VPC_Endpoint_Not_Working:
    Symptoms:
      - "Servicios AWS no accesibles desde subnets privadas"
      - "Tráfico yendo por NAT Gateway en lugar de endpoint"
    Possible_Causes:
      - "Private DNS no habilitado"
      - "Security group bloqueando tráfico al endpoint"
      - "Endpoint no asociado con subnet correcta"
    Troubleshooting:
      - "Verificar Private DNS enabled en endpoint"
      - "Verificar security group del endpoint"
      - "Verificar subnet associations"
      - "Hacer nslookup del servicio AWS"
    Solution:
      - "Habilitar Private DNS en endpoint"
      - "Agregar regla inbound en SG del endpoint"
      - "Asociar endpoint con subnets privadas"
```


```yaml
  Issue_4_WAF_Blocking_Legitimate_Traffic:
    Symptoms:
      - "Webhooks de Janis siendo bloqueados"
      - "429 Too Many Requests errors"
      - "403 Forbidden errors"
    Possible_Causes:
      - "Rate limiting muy restrictivo"
      - "Geo-blocking bloqueando IPs legítimas"
      - "AWS Managed Rules con falsos positivos"
    Troubleshooting:
      - "Revisar WAF logs en CloudWatch"
      - "Identificar regla que está bloqueando"
      - "Verificar IP source y país"
    Solution:
      - "Ajustar rate limit threshold"
      - "Agregar IPs de Janis a whitelist"
      - "Excluir reglas específicas de Managed Rule Groups"
      - "Ajustar geo-blocking para permitir países adicionales"
  
  Issue_5_EventBridge_Not_Triggering_MWAA:
    Symptoms:
      - "DAGs de MWAA no ejecutándose según schedule"
      - "Eventos en Dead Letter Queue"
    Possible_Causes:
      - "IAM permissions incorrectas"
      - "MWAA environment no disponible"
      - "DAG name incorrecto en target"
      - "Network connectivity issues"
    Troubleshooting:
      - "Verificar EventBridge metrics (FailedInvocations)"
      - "Revisar mensajes en DLQ"
      - "Verificar IAM role de EventBridge"
      - "Verificar MWAA environment status"
    Solution:
      - "Actualizar IAM role con permisos correctos"
      - "Esperar a que MWAA esté disponible"
      - "Corregir DAG name en EventBridge target"
      - "Verificar security groups y network connectivity"
```

### 16.2 Comandos Útiles de AWS CLI

```bash
# VPC y Networking
# Listar VPCs
aws ec2 describe-vpcs --filters "Name=tag:Project,Values=janis-cencosud"

# Listar subnets
aws ec2 describe-subnets --filters "Name=vpc-id,Values=<VPC_ID>"

# Verificar NAT Gateway status
aws ec2 describe-nat-gateways --filter "Name=vpc-id,Values=<VPC_ID>"

# Verificar route tables
aws ec2 describe-route-tables --filters "Name=vpc-id,Values=<VPC_ID>"

# Security Groups
# Listar security groups
aws ec2 describe-security-groups --filters "Name=vpc-id,Values=<VPC_ID>"

# Ver reglas de security group específico
aws ec2 describe-security-group-rules --filters "Name=group-id,Values=<SG_ID>"

# VPC Endpoints
# Listar VPC endpoints
aws ec2 describe-vpc-endpoints --filters "Name=vpc-id,Values=<VPC_ID>"

# Verificar status de endpoint
aws ec2 describe-vpc-endpoints --vpc-endpoint-ids <ENDPOINT_ID>

# VPC Flow Logs
# Ver logs recientes
aws logs tail /aws/vpc/flow-logs/janis-cencosud --follow

# Query logs con Insights
aws logs start-query \
  --log-group-name /aws/vpc/flow-logs/janis-cencosud \
  --start-time $(date -u -d '1 hour ago' +%s) \
  --end-time $(date -u +%s) \
  --query-string 'fields @timestamp, srcaddr, dstaddr, action | filter action = "REJECT"'

# WAF
# Ver métricas de WAF
aws cloudwatch get-metric-statistics \
  --namespace AWS/WAFV2 \
  --metric-name BlockedRequests \
  --dimensions Name=Rule,Value=ALL \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Sum

# Ver logs de WAF
aws logs tail /aws/waf/janis-cencosud-api-gateway --follow

# EventBridge
# Listar rules
aws events list-rules --event-bus-name janis-cencosud-polling-bus

# Ver targets de una rule
aws events list-targets-by-rule --rule poll-orders-schedule

# Ver métricas de rule
aws cloudwatch get-metric-statistics \
  --namespace AWS/Events \
  --metric-name FailedInvocations \
  --dimensions Name=RuleName,Value=poll-orders-schedule \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Sum

# Dead Letter Queue
# Ver mensajes en DLQ
aws sqs receive-message --queue-url <DLQ_URL> --max-number-of-messages 10

# Redshift
# Verificar cluster status
aws redshift describe-clusters --cluster-identifier <CLUSTER_ID>

# Ver security groups de cluster
aws redshift describe-clusters --cluster-identifier <CLUSTER_ID> \
  --query 'Clusters[0].VpcSecurityGroups'
```


---

## 17. REFERENCIAS Y RECURSOS

### 17.1 Documentación AWS Oficial

```yaml
AWS_Documentation:
  
  VPC:
    - "VPC User Guide: https://docs.aws.amazon.com/vpc/"
    - "VPC Endpoints: https://docs.aws.amazon.com/vpc/latest/privatelink/"
    - "VPC Flow Logs: https://docs.aws.amazon.com/vpc/latest/userguide/flow-logs.html"
  
  Security:
    - "Security Groups: https://docs.aws.amazon.com/vpc/latest/userguide/VPC_SecurityGroups.html"
    - "NACLs: https://docs.aws.amazon.com/vpc/latest/userguide/vpc-network-acls.html"
    - "AWS WAF: https://docs.aws.amazon.com/waf/"
  
  EventBridge:
    - "EventBridge User Guide: https://docs.aws.amazon.com/eventbridge/"
    - "EventBridge Scheduler: https://docs.aws.amazon.com/scheduler/"
  
  Monitoring:
    - "CloudWatch User Guide: https://docs.aws.amazon.com/cloudwatch/"
    - "CloudWatch Logs Insights: https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/AnalyzingLogData.html"
  
  Best_Practices:
    - "AWS Well-Architected Framework: https://aws.amazon.com/architecture/well-architected/"
    - "Security Best Practices: https://docs.aws.amazon.com/security/"
```

### 17.2 Documentación del Proyecto

```yaml
Project_Documentation:
  
  Specs:
    - "Requirements: .kiro/specs/aws-infrastructure/requirements.md"
    - "Design: .kiro/specs/aws-infrastructure/design.md"
    - "Tasks: .kiro/specs/aws-infrastructure/tasks.md"
  
  Executive_Summaries:
    - "Infrastructure Overview: Documentación Cenco/Infraestructura AWS - Resumen Ejecutivo.md"
    - "Overall Architecture: Documento Detallado de Diseño Janis-Cenco.md"
  
  Steering_Files:
    - "Terraform Best Practices: .kiro/steering/Terraform Best Practices.md"
    - "AWS Best Practices: .kiro/steering/Buenas practicas de AWS.md"
    - "Tech Stack: .kiro/steering/tech.md"
    - "Project Structure: .kiro/steering/structure.md"
```

### 17.3 Herramientas Recomendadas

```yaml
Recommended_Tools:
  
  Infrastructure_as_Code:
    - Name: "Terraform"
      Version: ">= 1.0"
      Purpose: "Infrastructure provisioning"
      URL: "https://www.terraform.io/"
    
    - Name: "Terragrunt"
      Purpose: "DRY Terraform configurations"
      URL: "https://terragrunt.gruntwork.io/"
  
  Security_Scanning:
    - Name: "tfsec"
      Purpose: "Security scanning for Terraform"
      URL: "https://github.com/aquasecurity/tfsec"
    
    - Name: "Checkov"
      Purpose: "Policy-as-code for infrastructure"
      URL: "https://www.checkov.io/"
  
  Testing:
    - Name: "Terratest"
      Purpose: "Infrastructure testing"
      URL: "https://terratest.gruntwork.io/"
  
  Monitoring:
    - Name: "AWS CLI"
      Purpose: "Command-line management"
      URL: "https://aws.amazon.com/cli/"
    
    - Name: "AWS Console Mobile App"
      Purpose: "Mobile monitoring and alerts"
      URL: "https://aws.amazon.com/console/mobile/"
  
  Visualization:
    - Name: "Cloudcraft"
      Purpose: "AWS architecture diagrams"
      URL: "https://www.cloudcraft.co/"
    
    - Name: "draw.io"
      Purpose: "Network diagrams"
      URL: "https://www.draw.io/"
```

---

## 18. GLOSARIO

```yaml
Glossary:
  
  AZ:
    Full_Name: "Availability Zone"
    Description: "Ubicación física aislada dentro de una región AWS"
  
  CIDR:
    Full_Name: "Classless Inter-Domain Routing"
    Description: "Método de asignación de direcciones IP y routing"
  
  ENI:
    Full_Name: "Elastic Network Interface"
    Description: "Interfaz de red virtual en VPC"
  
  IGW:
    Full_Name: "Internet Gateway"
    Description: "Componente de VPC que permite comunicación con internet"
  
  NACL:
    Full_Name: "Network Access Control List"
    Description: "Firewall stateless a nivel de subnet"
  
  NAT:
    Full_Name: "Network Address Translation"
    Description: "Permite que recursos en subnet privada accedan a internet"
  
  SG:
    Full_Name: "Security Group"
    Description: "Firewall stateful a nivel de instancia/ENI"
  
  VPC:
    Full_Name: "Virtual Private Cloud"
    Description: "Red virtual aislada en AWS"
  
  WAF:
    Full_Name: "Web Application Firewall"
    Description: "Firewall de aplicación web para proteger contra ataques"
```

---

## 19. CONTROL DE CAMBIOS

```yaml
Change_Log:
  
  Version_1.0:
    Date: "2026-01-21"
    Author: "Kiro AI Assistant"
    Changes:
      - "Documento inicial creado"
      - "Especificaciones completas de infraestructura"
      - "Configuraciones de red, seguridad, y monitoreo"
      - "Guías de implementación y troubleshooting"
    Status: "Released for Client Review"
```

---

## 20. APROBACIONES

```yaml
Approvals_Required:
  
  Technical_Review:
    Reviewer: "<TECHNICAL_LEAD_NAME>"
    Date: "<DATE>"
    Status: "Pending"
    Comments: ""
  
  Security_Review:
    Reviewer: "<SECURITY_TEAM_LEAD>"
    Date: "<DATE>"
    Status: "Pending"
    Comments: ""
  
  Architecture_Review:
    Reviewer: "<CLOUD_ARCHITECT>"
    Date: "<DATE>"
    Status: "Pending"
    Comments: ""
  
  Budget_Approval:
    Approver: "<FINANCE_MANAGER>"
    Date: "<DATE>"
    Status: "Pending"
    Comments: ""
  
  Final_Approval:
    Approver: "<PROJECT_SPONSOR>"
    Date: "<DATE>"
    Status: "Pending"
    Comments: ""
```

---

## ANEXO A: PLANTILLA DE TERRAFORM

El cliente puede usar esta plantilla como punto de partida para su implementación:

```hcl
# terraform/modules/vpc/main.tf

terraform {
  required_version = ">= 1.0"
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# VPC
resource "aws_vpc" "main" {
  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = true
  enable_dns_support   = true
  
  tags = merge(
    var.common_tags,
    {
      Name      = "${var.project_name}-vpc"
      Component = "vpc"
    }
  )
}

# Public Subnet A
resource "aws_subnet" "public_a" {
  vpc_id                  = aws_vpc.main.id
  cidr_block              = var.public_subnet_a_cidr
  availability_zone       = "${var.aws_region}a"
  map_public_ip_on_launch = true
  
  tags = merge(
    var.common_tags,
    {
      Name      = "${var.project_name}-public-subnet-a"
      Component = "subnet"
      Tier      = "public"
      Purpose   = "nat-gateway-api-gateway"
    }
  )
}

# Private Subnet 1A
resource "aws_subnet" "private_1a" {
  vpc_id                  = aws_vpc.main.id
  cidr_block              = var.private_subnet_1a_cidr
  availability_zone       = "${var.aws_region}a"
  map_public_ip_on_launch = false
  
  tags = merge(
    var.common_tags,
    {
      Name      = "${var.project_name}-private-subnet-1a"
      Component = "subnet"
      Tier      = "private"
      Purpose   = "lambda-mwaa-redshift"
    }
  )
}

# Private Subnet 2A
resource "aws_subnet" "private_2a" {
  vpc_id                  = aws_vpc.main.id
  cidr_block              = var.private_subnet_2a_cidr
  availability_zone       = "${var.aws_region}a"
  map_public_ip_on_launch = false
  
  tags = merge(
    var.common_tags,
    {
      Name      = "${var.project_name}-private-subnet-2a"
      Component = "subnet"
      Tier      = "private"
      Purpose   = "glue-enis"
    }
  )
}

# Internet Gateway
resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id
  
  tags = merge(
    var.common_tags,
    {
      Name      = "${var.project_name}-igw"
      Component = "internet-gateway"
    }
  )
}

# Elastic IP for NAT Gateway
resource "aws_eip" "nat" {
  domain = "vpc"
  
  tags = merge(
    var.common_tags,
    {
      Name      = "${var.project_name}-nat-eip"
      Component = "elastic-ip"
    }
  )
  
  depends_on = [aws_internet_gateway.main]
}

# NAT Gateway
resource "aws_nat_gateway" "main" {
  allocation_id = aws_eip.nat.id
  subnet_id     = aws_subnet.public_a.id
  
  tags = merge(
    var.common_tags,
    {
      Name      = "${var.project_name}-nat-gateway"
      Component = "nat-gateway"
    }
  )
  
  depends_on = [aws_internet_gateway.main]
}

# Public Route Table
resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id
  
  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main.id
  }
  
  tags = merge(
    var.common_tags,
    {
      Name      = "${var.project_name}-public-rt"
      Component = "route-table"
      Tier      = "public"
    }
  )
}

# Private Route Table
resource "aws_route_table" "private" {
  vpc_id = aws_vpc.main.id
  
  route {
    cidr_block     = "0.0.0.0/0"
    nat_gateway_id = aws_nat_gateway.main.id
  }
  
  tags = merge(
    var.common_tags,
    {
      Name      = "${var.project_name}-private-rt"
      Component = "route-table"
      Tier      = "private"
    }
  )
}

# Route Table Associations
resource "aws_route_table_association" "public_a" {
  subnet_id      = aws_subnet.public_a.id
  route_table_id = aws_route_table.public.id
}

resource "aws_route_table_association" "private_1a" {
  subnet_id      = aws_subnet.private_1a.id
  route_table_id = aws_route_table.private.id
}

resource "aws_route_table_association" "private_2a" {
  subnet_id      = aws_subnet.private_2a.id
  route_table_id = aws_route_table.private.id
}
```

**Nota**: Esta es solo una plantilla de ejemplo. El cliente debe adaptarla según sus estándares de Terraform y políticas corporativas.

---

**FIN DEL DOCUMENTO**

---

**Contacto para Consultas**:
- Equipo de Arquitectura: <architecture@cencosud.com>
- Equipo de Seguridad: <security@cencosud.com>
- Equipo de DevOps: <devops@cencosud.com>
