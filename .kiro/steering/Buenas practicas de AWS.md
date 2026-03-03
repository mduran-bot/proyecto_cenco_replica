---
inclusion: always
---
# Buenas Prácticas de AWS

Este steering file proporciona directrices para el diseño, implementación y mantenimiento de infraestructura AWS siguiendo las mejores prácticas de la industria.

## Principios Fundamentales

### Well-Architected Framework
Seguir los 6 pilares del AWS Well-Architected Framework:
- **Excelencia Operacional**: Automatización, monitoreo y mejora continua
- **Seguridad**: Protección de datos y sistemas en tránsito y en reposo
- **Confiabilidad**: Recuperación automática de fallos y escalabilidad
- **Eficiencia de Rendimiento**: Uso eficiente de recursos computacionales
- **Optimización de Costos**: Evitar gastos innecesarios y optimizar recursos
- **Sostenibilidad**: Minimizar el impacto ambiental de las cargas de trabajo

## Seguridad

### Identity and Access Management (IAM)
- **Principio de menor privilegio**: Otorgar solo los permisos mínimos necesarios
- **Usar roles de IAM** en lugar de usuarios para servicios AWS
- **Habilitar MFA** para todos los usuarios con acceso a la consola
- **Rotar credenciales** regularmente y usar AWS Secrets Manager
- **Evitar hardcodear credenciales** en código o archivos de configuración

### Cifrado
- **Cifrar datos en reposo** usando KMS o cifrado nativo del servicio
- **Cifrar datos en tránsito** usando TLS/SSL
- **Usar AWS KMS** para gestión centralizada de claves
- **Implementar cifrado de extremo a extremo** cuando sea necesario

### Redes
- **Usar VPC** para aislamiento de red
- **Implementar subnets públicas y privadas** apropiadamente
- **Configurar Security Groups** como firewalls stateful
- **Usar NACLs** para control adicional a nivel de subnet
- **Implementar VPC Flow Logs** para monitoreo de tráfico

## Arquitectura y Diseño

### Alta Disponibilidad
<!---- **Diseñar para múltiples AZs** para tolerancia a fallos-->
- **Usar Auto Scaling Groups** para escalabilidad automática
- **Implementar Load Balancers** para distribución de tráfico
- **Configurar health checks** apropiados
- **Planificar para disaster recovery** con RTO y RPO definidos

### Microservicios y Serverless
- **Preferir arquitecturas serverless** cuando sea apropiado (Lambda, API Gateway)
- **Usar contenedores** (ECS/EKS) para aplicaciones complejas
- **Implementar circuit breakers** y retry logic
- **Diseñar APIs idempotentes** y stateless

### Almacenamiento de Datos
- **Elegir el tipo de base de datos apropiado** (RDS, DynamoDB, Redshift)
- **Implementar backups automáticos** y point-in-time recovery
- **Usar read replicas** para mejorar rendimiento de lectura
- **Configurar encryption at rest** para todas las bases de datos
- **Implementar data lifecycle policies** para S3

## Monitoreo y Observabilidad

### CloudWatch
- **Configurar métricas personalizadas** para KPIs de negocio
- **Crear dashboards** para visualización de métricas clave
- **Configurar alarmas** para eventos críticos
- **Usar CloudWatch Logs** para centralizar logs
- **Implementar log retention policies** apropiadas

### Distributed Tracing
- **Usar AWS X-Ray** para tracing de aplicaciones distribuidas
- **Implementar correlation IDs** en todos los servicios
- **Monitorear latencia end-to-end** de transacciones críticas

### Alerting
- **Configurar alertas proactivas** antes de que ocurran problemas
- **Usar SNS** para notificaciones multi-canal
- **Implementar escalation policies** para alertas críticas
- **Evitar alert fatigue** con thresholds apropiados

## Optimización de Costos

### Compute
- **Usar Reserved Instances** para cargas de trabajo predecibles
- **Implementar Spot Instances** para cargas de trabajo tolerantes a interrupciones
- **Right-size instances** basado en métricas de utilización
- **Usar AWS Compute Optimizer** para recomendaciones

### Storage
- **Implementar S3 Intelligent Tiering** para optimización automática
- **Usar lifecycle policies** para transicionar a storage classes más baratos
- **Eliminar snapshots y volumes** no utilizados regularmente
- **Comprimir y deduplicar datos** cuando sea posible

### Networking
- **Minimizar transferencia de datos** entre regiones
- **Usar CloudFront** para contenido estático y APIs
- **Optimizar VPC endpoints** para servicios AWS
- **Monitorear costos de NAT Gateway** y considerar alternativas

## Automatización y DevOps

### Infrastructure as Code (IaC)
- **Usar CloudFormation o CDK** para toda la infraestructura
- **Versionar templates** de infraestructura
- **Implementar drift detection** para detectar cambios manuales
- **Usar nested stacks** para modularidad
- **Validar templates** antes del deployment

### CI/CD
- **Implementar pipelines automatizados** con CodePipeline o GitHub Actions
- **Usar blue-green deployments** para minimizar downtime
- **Implementar automated testing** en todos los stages
- **Configurar rollback automático** en caso de fallos
- **Usar feature flags** para releases controlados

### Backup y Recovery
- **Automatizar backups** de todos los datos críticos
- **Probar recovery procedures** regularmente
- **Documentar RTO y RPO** para cada servicio
- **Usar cross-region replication** para datos críticos
- **Implementar automated disaster recovery** testing

## Compliance y Governance

### Tagging
- **Implementar tagging strategy** consistente
- **Usar tags obligatorios** para cost allocation
- **Automatizar tag compliance** con Config Rules
- **Tags mínimos requeridos**: Environment, Project, Owner, CostCenter

### Auditing
- **Habilitar CloudTrail** en todas las regiones
- **Usar Config** para compliance monitoring
- **Implementar GuardDuty** para threat detection
- **Configurar Security Hub** para security posture management

### Data Governance
- **Clasificar datos** por sensibilidad
- **Implementar data retention policies**
- **Usar AWS Macie** para data discovery y classification
- **Configurar access logging** para todos los data stores

## Patrones Específicos por Servicio

### Lambda
- **Optimizar memory allocation** basado en profiling
- **Usar environment variables** para configuración
- **Implementar proper error handling** y dead letter queues
- **Minimizar cold starts** con provisioned concurrency cuando sea necesario
- **Usar layers** para dependencias compartidas

### API Gateway
- **Implementar throttling** y rate limiting
- **Usar caching** para mejorar performance
- **Configurar proper CORS** settings
- **Implementar request/response validation**
- **Usar custom domain names** para APIs de producción

### RDS/Aurora
- **Usar parameter groups** personalizados
- **Implementar connection pooling**
- **Configurar automated backups** con retention apropiada
- **Usar read replicas** para scaling de lectura
- **Monitorear slow query logs**

### S3
- **Usar bucket policies** restrictivas
- **Habilitar versioning** para datos críticos
- **Configurar lifecycle rules** para cost optimization
- **Usar multipart upload** para archivos grandes
- **Implementar cross-region replication** para DR

## Checklist de Implementación

Antes de deployar cualquier infraestructura AWS, verificar:

- [ ] Security groups configurados con reglas mínimas necesarias
- [ ] Encryption habilitado para datos en reposo y en tránsito
- [ ] Backups automáticos configurados
- [ ] Monitoreo y alertas implementados
- [ ] Tags aplicados según la estrategia definida
- [ ] IAM roles siguiendo principio de menor privilegio
- [ ] Multi-AZ deployment para servicios críticos
- [ ] Cost optimization measures implementadas
- [ ] Disaster recovery plan documentado y probado
- [ ] Security scanning y compliance checks pasados

## Recursos Adicionales

- [AWS Well-Architected Framework](https://aws.amazon.com/architecture/well-architected/)
- [AWS Security Best Practices](https://aws.amazon.com/security/security-resources/)
- [AWS Cost Optimization](https://aws.amazon.com/aws-cost-management/)
- [AWS Operational Excellence](https://aws.amazon.com/architecture/operational-excellence/)