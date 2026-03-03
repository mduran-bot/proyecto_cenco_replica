# Product Overview

## Janis-Cencosud Data Integration Platform

Este proyecto implementa una plataforma de integración de datos moderna entre el sistema WMS Janis y el Data Lake de Cencosud en AWS. La solución permite la migración y sincronización continua de datos transaccionales críticos para habilitar análisis de negocio en tiempo real.

### Objetivos Principales

- **Migración de Datos**: Transferir datos históricos desde MySQL de Janis hacia Redshift de Cencosud
- **Sincronización en Tiempo Real**: Mantener datos actualizados mediante webhooks y polling periódico
- **Disponibilidad para BI**: Proporcionar datos curados y optimizados para Power BI y herramientas analíticas

### Componentes Core

- **Ingesta Híbrida**: Webhooks para eventos en tiempo real + polling programado como red de seguridad
- **Data Lake Moderno**: Arquitectura Bronze/Silver/Gold con Apache Iceberg para transacciones ACID
- **Orquestación Inteligente**: EventBridge + MWAA para optimizar recursos y reducir overhead
- **Procesamiento Serverless**: AWS Glue para transformaciones ETL escalables

### Valor de Negocio

- Visibilidad operativa completa de órdenes, productos, inventario y precios
- Reducción de latencia de datos de horas a minutos
- Base escalable para futuros casos de uso analíticos
- Cumplimiento de estándares de seguridad corporativa