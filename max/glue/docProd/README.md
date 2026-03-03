# Documentación de Producción - Pipeline ETL Janis-Cencosud

## 📚 Índice de Documentación

Esta carpeta contiene toda la documentación necesaria para desplegar y operar el pipeline ETL en producción.

### Documentos Disponibles

1. **[01-ARQUITECTURA-ETL.md](01-ARQUITECTURA-ETL.md)**
   - Arquitectura completa del pipeline Bronze → Silver → Gold
   - Flujo de datos y transformaciones
   - Decisiones de diseño y patrones utilizados

2. **[02-INGESTA-DATOS.md](02-INGESTA-DATOS.md)**
   - Cómo llegan los datos desde Janis (webhooks + polling)
   - Formato de datos crudos en Bronze
   - Configuración de API Gateway y Lambda

3. **[03-CONFIGURACION-PRODUCCION.md](03-CONFIGURACION-PRODUCCION.md)**
   - Configuración de AWS Glue Jobs
   - Variables de entorno y parámetros
   - Configuración de buckets S3
   - IAM roles y permisos necesarios

4. **[04-DEPLOYMENT-GUIDE.md](04-DEPLOYMENT-GUIDE.md)**
   - Pasos para desplegar en producción
   - Checklist de validación
   - Rollback procedures

5. **[05-OPERACION-MANTENIMIENTO.md](05-OPERACION-MANTENIMIENTO.md)**
   - Monitoreo y alertas
   - Troubleshooting común
   - Procedimientos de mantenimiento

6. **[06-ESQUEMAS-DATOS.md](06-ESQUEMAS-DATOS.md)**
   - Esquemas de datos por capa (Bronze/Silver/Gold)
   - Mapeo de campos
   - Transformaciones aplicadas

## 🚀 Quick Start

Para desplegar el pipeline en producción:

1. Leer [03-CONFIGURACION-PRODUCCION.md](03-CONFIGURACION-PRODUCCION.md)
2. Seguir [04-DEPLOYMENT-GUIDE.md](04-DEPLOYMENT-GUIDE.md)
3. Configurar monitoreo según [05-OPERACION-MANTENIMIENTO.md](05-OPERACION-MANTENIMIENTO.md)

## 📞 Contacto y Soporte

Para preguntas o soporte, contactar al equipo de Data Engineering.

---

**Última actualización**: 2026-02-26  
**Versión**: 1.0.0
