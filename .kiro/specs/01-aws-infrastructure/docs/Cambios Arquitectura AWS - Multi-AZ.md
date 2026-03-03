# Arquitectura AWS - Implementación Single-AZ con Preparación Multi-AZ

**Fecha**: 14 de enero de 2026  
**Versión**: 2.0  
**Estado**: Actualizado - Cambio a Single-AZ

## Resumen Ejecutivo

La arquitectura de infraestructura AWS para el proyecto Janis-Cencosud implementa un **despliegue Single-AZ (Single Availability Zone)** inicial en us-east-1a, optimizado para reducir costos y complejidad durante la fase de implementación inicial. La arquitectura está diseñada con CIDR blocks reservados y convenciones de nombres que facilitan la futura expansión a Multi-AZ sin cambios arquitectónicos mayores.

## Decisión de Arquitectura

### Estrategia de Despliegue

**Implementación Actual**: Despliegue en una sola Availability Zone (us-east-1a) con infraestructura completa operacional.

**Preparación Futura**: CIDR blocks reservados y documentados para us-east-1b, permitiendo expansión Multi-AZ cuando sea requerido por el negocio.

## Estructura de Red Single-AZ

### VPC Configuration
- **CIDR Block**: 10.0.0.0/16 (65,536 IPs disponibles)
- **Region**: us-east-1
- **Availability Zone Activa**: us-east-1a
- **Availability Zone Reservada**: us-east-1b (para expansión futura)

### Subredes Activas (us-east-1a)

#### Subred Pública
```
Public Subnet A: 10.0.1.0/24 (us-east-1a) - 256 IPs
  └── NAT Gateway (único punto de salida a Internet)
```

#### Subredes Privadas - Servicios de Procesamiento
```
Private Subnet 1A: 10.0.10.0/24 (us-east-1a) - 256 IPs
  └── Redshift, MWAA, Lambda
  └── Servicios de procesamiento de datos
```

#### Subredes Privadas - Glue ENIs
```
Private Subnet 2A: 10.0.20.0/24 (us-east-1a) - 256 IPs
  └── Glue ENIs (dedicado para evitar agotamiento de IPs)
```

### Subredes Reservadas para Expansión Multi-AZ (us-east-1b)

**Documentadas pero no implementadas inicialmente:**

```
Public Subnet B: 10.0.2.0/24 (us-east-1b) - RESERVADO
  └── NAT Gateway B (futuro)

Private Subnet 1B: 10.0.11.0/24 (us-east-1b) - RESERVADO
  └── Redshift, MWAA, Lambda (futuro)

Private Subnet 2B: 10.0.21.0/24 (us-east-1b) - RESERVADO
  └── Glue ENIs (futuro)
```

## Puntos Únicos de Fallo Identificados

### NAT Gateway Único
- **Ubicación**: Public Subnet A (us-east-1a)
- **Impacto de Fallo**: Pérdida completa de conectividad a Internet desde subredes privadas
- **Mitigación Actual**: VPC Endpoints para servicios AWS críticos (S3, Glue, Secrets Manager, CloudWatch)
- **Mitigación Futura**: Implementar NAT Gateway B en us-east-1b

### Deployment Single-AZ
- **Impacto de Fallo de AZ**: Sistema completo no disponible hasta restauración de us-east-1a
- **RTO Estimado**: Depende del tiempo de recuperación de AWS (típicamente < 1 hora)
- **RPO Estimado**: Datos en S3 no se pierden (replicación automática de AWS)
- **Mitigación Futura**: Expandir a Multi-AZ según plan documentado

## Distribución de Componentes (Single-AZ)

| Componente | us-east-1a (Activo) | us-east-1b (Reservado) |
|------------|---------------------|------------------------|
| **Redshift** | Cluster en Private Subnet 1A | CIDR reservado: 10.0.11.0/24 |
| **MWAA** | Environment en Private Subnet 1A | CIDR reservado: 10.0.11.0/24 |
| **Lambda** | Funciones en Private Subnet 1A | CIDR reservado: 10.0.11.0/24 |
| **Glue ENIs** | Private Subnet 2A | CIDR reservado: 10.0.21.0/24 |
| **NAT Gateway** | Public Subnet A | CIDR reservado: 10.0.2.0/24 |

## Beneficios de la Arquitectura Single-AZ

### Reducción de Costos
- **NAT Gateway único**: Ahorro de ~$32/mes + costos de transferencia
- **Sin transferencia inter-AZ**: Ahorro de $0.01/GB en tráfico entre zonas
- **Recursos simplificados**: Menor overhead operacional inicial

### Simplicidad Operacional
- **Deployment más rápido**: Menos recursos que configurar y validar
- **Troubleshooting simplificado**: Un solo punto de fallo para diagnosticar
- **Menor complejidad de red**: Routing y security groups más directos

### Preparación para Crecimiento
- **CIDR blocks reservados**: Expansión sin renumeración de red
- **Naming conventions**: Sufijos A/B preparados para Multi-AZ
- **Arquitectura escalable**: Diseño permite agregar AZ sin cambios mayores

## Trade-offs y Consideraciones

### Disponibilidad
- **SLA Objetivo**: 99.5% (vs 99.9% en Multi-AZ)
- **RTO**: Variable según recuperación de AWS (vs < 5 min en Multi-AZ)
- **RPO**: < 1 minuto (datos en S3 no se pierden)

### Costos vs Disponibilidad
- **Ahorro mensual estimado**: ~$40-50/mes en infraestructura
- **Costo de downtime**: Debe evaluarse según criticidad del negocio
- **Recomendación**: Iniciar Single-AZ, migrar a Multi-AZ cuando el volumen de negocio lo justifique

## Plan de Implementación

### Fase 1: Despliegue Single-AZ (Actual)

**Objetivo**: Implementar infraestructura funcional en us-east-1a con costos optimizados

**Componentes a Implementar**:
1. VPC con CIDR 10.0.0.0/16
2. Subredes activas en us-east-1a:
   - Public Subnet A (10.0.1.0/24)
   - Private Subnet 1A (10.0.10.0/24)
   - Private Subnet 2A (10.0.20.0/24)
3. NAT Gateway único en Public Subnet A
4. Internet Gateway
5. VPC Endpoints (S3, Glue, Secrets Manager, CloudWatch, KMS, STS, EventBridge)
6. Security Groups y NACLs
7. WAF en API Gateway
8. EventBridge para scheduling
9. Todos los servicios de procesamiento en us-east-1a

**Documentación Requerida**:
- ✅ CIDR blocks reservados para us-east-1b documentados
- ✅ Puntos únicos de fallo identificados
- ✅ Plan de migración a Multi-AZ preparado
- ✅ Naming conventions con sufijos A/B

**Criterios de Éxito**:
- [ ] Infraestructura desplegada y operacional en us-east-1a
- [ ] Todos los tests de Terraform pasando
- [ ] Documentación de arquitectura actualizada
- [ ] Plan de migración Multi-AZ validado

### Fase 2: Migración a Multi-AZ (Futura)

**Trigger para Migración**:
- Volumen de negocio justifica mayor disponibilidad
- Requerimientos de SLA > 99.5%
- Budget aprobado para costos adicionales (~$40-50/mes)

**Pasos de Migración**:

1. **Preparación (1-2 días)**:
   - Revisar y actualizar módulos de Terraform
   - Validar CIDR blocks reservados
   - Planificar ventana de mantenimiento

2. **Implementación de Red (2-3 horas)**:
   - Crear subredes en us-east-1b usando CIDRs reservados
   - Desplegar NAT Gateway B en Public Subnet B
   - Configurar route tables para us-east-1b
   - Actualizar VPC Endpoints para ambas AZs

3. **Migración de Servicios (4-6 horas)**:
   - Redshift: Habilitar Multi-AZ en cluster existente
   - MWAA: Actualizar environment para Multi-AZ
   - Lambda: Agregar subnets de us-east-1b a configuración
   - Glue: Configurar ENIs en Private Subnet 2B

4. **Validación y Testing (2-3 horas)**:
   - Verificar conectividad desde ambas AZs
   - Probar failover de NAT Gateway
   - Validar distribución de carga
   - Ejecutar tests de integración completos

5. **Monitoreo Post-Migración (1 semana)**:
   - Monitorear métricas de disponibilidad
   - Validar costos vs estimaciones
   - Ajustar configuraciones según necesidad

**Rollback Plan**:
- Mantener configuración Single-AZ en branch separado
- Backup de state de Terraform antes de migración
- Procedimiento documentado para revertir cambios

## Impacto en Implementación Actual

### Terraform
- **Módulos**: Diseñados para Single-AZ con variables para Multi-AZ
- **Variables**: `availability_zones = ["us-east-1a"]` (expandible a `["us-east-1a", "us-east-1b"]`)
- **Naming**: Recursos con sufijo `-a` para facilitar adición de `-b`
- **State Management**: Local state con backups manuales

### Seguridad
- Security Groups: Diseñados para funcionar en Single o Multi-AZ sin cambios
- NACLs: Aplicadas a subredes activas, fácilmente replicables a us-east-1b
- VPC Endpoints: Configurados para expandirse a múltiples AZs
- WAF: Sin cambios requeridos para Multi-AZ

### Monitoreo
- CloudWatch Alarms: Configuradas por recurso (no por AZ)
- Dashboards: Métricas agregadas, fácil agregar desglose por AZ
- Alertas: Notificaciones de disponibilidad del sistema completo
- VPC Flow Logs: Capturan tráfico de todas las subredes

## Consideraciones de Costos

### Costos Actuales (Single-AZ)
- **NAT Gateway**: ~$32/mes + $0.045/GB procesado
- **Elastic IP**: ~$3.60/mes (si no está en uso)
- **VPC Endpoints (Interface)**: ~$7.20/mes por endpoint × 6 = ~$43/mes
- **Transferencia de datos**: Variable según volumen
- **Total estimado**: ~$80-100/mes en infraestructura de red

### Costos Adicionales Multi-AZ (Futuros)
- **NAT Gateway adicional**: +$32/mes
- **Elastic IP adicional**: +$3.60/mes
- **Transferencia inter-AZ**: +$0.01/GB (solo tráfico entre AZs)
- **Total incremental**: ~$40-50/mes

### Optimización de Costos
- VPC Endpoints reducen tráfico a través de NAT Gateway
- S3 Gateway Endpoint es gratuito
- Compresión de datos minimiza transferencias
- Arquitectura serverless mantiene costos variables

## Referencias y Documentación

### Documentos Relacionados
- **Design Document**: `.kiro/specs/aws-infrastructure/design.md` - Diseño detallado Single-AZ
- **Implementation Tasks**: `.kiro/specs/aws-infrastructure/tasks.md` - Plan de implementación paso a paso
- **Requirements**: `.kiro/specs/aws-infrastructure/requirements.md` - Requerimientos funcionales
- **Documento Principal**: `Documento Detallado de Diseño Janis-Cenco.md` - Arquitectura completa del proyecto

### Recursos AWS
- **AWS Well-Architected Framework**: Pilar de Confiabilidad
- **VPC Best Practices**: https://docs.aws.amazon.com/vpc/latest/userguide/vpc-best-practices.html
- **High Availability**: https://docs.aws.amazon.com/whitepapers/latest/real-time-communication-on-aws/high-availability-and-scalability-on-aws.html

### Decisiones de Arquitectura

**ADR-001: Single-AZ Deployment**
- **Fecha**: 14 de enero de 2026
- **Estado**: Aprobado
- **Contexto**: Fase inicial del proyecto requiere optimización de costos
- **Decisión**: Implementar Single-AZ con preparación para Multi-AZ
- **Consecuencias**: 
  - ✅ Reducción de costos ~40%
  - ✅ Deployment más rápido
  - ⚠️ SLA reducido a 99.5%
  - ⚠️ Puntos únicos de fallo identificados y documentados

**ADR-002: Reserved CIDR Blocks**
- **Fecha**: 14 de enero de 2026
- **Estado**: Aprobado
- **Contexto**: Facilitar migración futura a Multi-AZ
- **Decisión**: Reservar CIDRs 10.0.2.0/24, 10.0.11.0/24, 10.0.21.0/24 para us-east-1b
- **Consecuencias**:
  - ✅ Migración sin renumeración de red
  - ✅ Naming conventions preparadas
  - ✅ Documentación clara de expansión

---

**Nota**: Esta arquitectura Single-AZ proporciona una base sólida y económica para la fase inicial del proyecto, con un camino claro y documentado hacia Multi-AZ cuando el volumen de negocio y los requerimientos de disponibilidad lo justifiquen. Los CIDR blocks reservados y las convenciones de nombres aseguran que la migración futura sea fluida y sin interrupciones mayores.
