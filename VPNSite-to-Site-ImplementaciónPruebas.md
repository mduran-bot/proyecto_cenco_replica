# **VPN Site-to-Site \- Implementación y Pruebas**

Fecha: 2 de febrero de 2026 Estado: VPN Creada \- Pendiente Configuración Cliente Cuenta: Network Account (189993504257)

## **Resumen Ejecutivo**

Este documento resume la implementación de la VPN Site-to-Site entre AWS y la red on-premise de AWS Fashions, incluyendo lo que se hizo en AWS, lo que debe hacer el cliente, y cómo validar la conectividad.

## **PARTE 1: LO QUE HICIMOS EN AWS**

### **Recursos Creados**

**Customer Gateway**

* ID: cgw-016cf3c3f922d5521  
* IP Pública On-Premise: 186.67.142.226  
* ASN On-Premise: 65400  
* Dispositivo: FortiGate-1100E v7.4.9

**VPN Connection**

* ID: vpn-0813456f62265cd44  
* Estado: available (esperando configuración cliente)  
* Tipo: IPsec con BGP dinámico  
* Conectado a: Transit Gateway tgw-0f394aab46e2e43c1  
* Túneles: 2 (para redundancia)

**Túnel 1**

* IP AWS: 18.204.0.101  
* IP interna AWS: 169.254.105.197/30  
* IP interna on-premise: 169.254.105.198/30  
* Pre-shared key: mXCYeFqZxjjevnfMzEWMeYkTvqZcXmpb

**Túnel 2**

* IP AWS: 98.88.53.226  
* IP interna AWS: Ver archivo vpn-config-fortigate.txt  
* IP interna on-premise: Ver archivo vpn-config-fortigate.txt  
* Pre-shared key: Ver archivo vpn-config-fortigate.txt

### **Configuración BGP**

**Lado AWS:**

* ASN: 65000  
* Hold time: 30 segundos  
* Rutas anunciadas automáticamente:  
  * 10.0.0.0/16 (VPC Hub)  
  * 10.2.0.0/16 (VPC QA)  
  * 10.3.0.0/16 (VPC Development)

**Lado On-Premise (a configurar por cliente):**

* ASN: 65400  
* Hold time: 30 segundos  
* Rutas a anunciar: 172.21.0.0/22

### **Archivo de Configuración**

Se generó el archivo vpn-config-fortigate.txt con toda la configuración necesaria para el FortiGate, incluyendo:

* Parámetros de los 2 túneles IPsec  
* Pre-shared keys  
* IPs internas de los túneles  
* Configuración IKE (Phase 1\)  
* Configuración IPsec (Phase 2\)  
* Parámetros BGP

### **Script Utilizado**

Archivo: scripts/create-vpn-site-to-site.sh

Comando ejecutado:

```
bash scripts/create-vpn-site-to-site.sh
```

## **PARTE 2: LO QUE DEBE HACER EL CLIENTE**

### **Requisitos Previos**

El cliente ya tiene:

* FortiGate-1100E v7.4.9 operacional  
* BGP configurado con ASN 65400  
* Experiencia con configuración de túneles VPN  
* Acceso administrativo al FortiGate

### **Pasos de Configuración**

**Paso 1: Configurar Túneles IPsec**

Usar el archivo vpn-config-fortigate.txt enviado por correo.

Configurar 2 túneles IPsec con:

* Túnel 1 hacia 18.204.0.101  
* Túnel 2 hacia 98.88.53.226  
* Usar pre-shared keys del archivo  
* Aplicar parámetros IKE e IPsec del archivo

Tiempo estimado: 10-15 minutos

**Paso 2: Configurar BGP**

Agregar 2 neighbors BGP a su configuración existente:

```
config router bgp
    config neighbor
        edit "169.254.105.197"
            set remote-as 65000
            set interface "vpn-tunnel-aws-1"
        next
        
        edit "169.254.XXX.XXX"  # Segunda IP en archivo
            set remote-as 65000
            set interface "vpn-tunnel-aws-2"
        next
    end
    
    config network
        edit X  # Siguiente número disponible
            set prefix 172.21.0.0/22
        next
    end
end
```

Tiempo estimado: 5 minutos

**Paso 3: Validar Configuración**

Comandos para validar en FortiGate:

```
# Ver estado de túneles
get vpn ipsec tunnel summary

# Ver estado BGP
get router info bgp summary
get router info bgp neighbors

# Ver rutas aprendidas
get router info routing-table bgp
```

Tiempo estimado: 5 minutos

### **Total de Tiempo Estimado**

20-25 minutos (el cliente tiene experiencia con BGP)

### **Confirmación Requerida**

El cliente debe confirmar cuando:

1. Los 2 túneles estén en estado UP  
2. BGP esté establecido (estado Established)  
3. Las rutas de AWS aparezcan en su tabla de rutas

---

## **PARTE 3: CÓMO VALIDAR Y PROBAR LA VPN**

### **Validación Desde AWS**

**Paso 1: Verificar Estado de Túneles**

Comando:

```
aws ec2 describe-vpn-connections \
  --vpn-connection-ids vpn-0813456f62265cd44 \
  --region us-east-1 \
  --query 'VpnConnections[0].VgwTelemetry[*].[OutsideIpAddress,Status,StatusMessage,AcceptedRouteCount]' \
  --output table
```

Estado esperado:

* Status: UP (ambos túneles)  
* StatusMessage: "IPSEC IS UP"  
* AcceptedRouteCount: 1 (ruta 172.21.0.0/22 recibida)

**Paso 2: Verificar Rutas BGP en Transit Gateway**

Comando:

```
aws ec2 search-transit-gateway-routes \
  --transit-gateway-route-table-id <route-table-id> \
  --filters "Name=type,Values=propagated" \
  --region us-east-1
```

Debe aparecer: 172.21.0.0/22 como ruta propagada desde VPN

### **Pruebas de Conectividad**

**Opción A: Crear Instancia EC2 de Prueba en cuenta Dev**

**Paso 1: Crear Instancia EC2 en VPC DEV**

Especificaciones:

* Tipo: t3.micro (gratis en free tier o \~7 USD/mes)  
* AMI: Amazon Linux 2023  
* Subnet: dev-vpc-development-private-a (10.3.11.0/24)  
* IP privada: 10.3.11.50 (ejemplo)  
* Security Group: Permitir ICMP desde 172.21.0.0/22

Comando para crear Security Group:

```
# Asumir rol en cuenta DEV
aws sts assume-role \
  --role-arn "arn:aws:iam::322156488591:role/AWSControlTowerExecution" \
  --role-session-name "test-session" \
  --profile mfa-session

# Crear Security Group
aws ec2 create-security-group \
  --group-name vpn-test-sg \
  --description "Security group para pruebas VPN" \
  --vpc-id vpc-03cd2b57974e59051 \
  --region us-east-1

# Agregar regla ICMP
aws ec2 authorize-security-group-ingress \
  --group-id <sg-id> \
  --protocol icmp \
  --port -1 \
  --cidr 172.21.0.0/22 \
  --region us-east-1
```

Comando para crear instancia:

```
aws ec2 run-instances \
  --image-id ami-0c55b159cbfafe1f0 \
  --instance-type t3.micro \
  --subnet-id <subnet-id> \
  --security-group-ids <sg-id> \
  --private-ip-address 10.3.11.50 \
  --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=vpn-test-instance},{Key=Project,Value=Landing-Zone-Base},{Key=Environment,Value=dev},{Key=map-migrated,Value=migNIVH9GC55D}]' \
  --region us-east-1
```

**Paso 2: Prueba de Ping desde On-Premise a AWS**

Desde un servidor en la red on-premise (172.21.x.x):

```
ping 10.3.11.50
```

Resultado esperado: Respuesta exitosa

**Paso 3: Prueba de Ping desde AWS a On-Premise**

Conectarse a la instancia EC2 via Systems Manager Session Manager:

```
aws ssm start-session \
  --target <instance-id> \
  --region us-east-1
```

Desde la instancia, hacer ping a una IP on-premise:

```
ping 172.21.1.10  # Ejemplo: servidor en segmento administrativo
```

Resultado esperado: Respuesta exitosa

**Opción B: Validación Sin Instancia EC2**

Si no quieres crear instancia, el cliente puede:

1. Hacer ping desde on-premise a cualquier IP en rango 10.3.11.0/24  
2. Aunque no haya instancia, si la VPN y routing están correctos, el ping llegará a AWS  
3. AWS responderá con "Destination Host Unreachable" (normal, no hay host)  
4. Esto confirma que el tráfico está llegando a AWS

### **Comandos de Monitoreo Continuo**

**Script para monitorear estado de túneles cada 30 segundos:**

```
#!/bin/bash
while true; do
  clear
  echo "Estado de Túneles VPN - $(date)"
  echo "================================"
  aws ec2 describe-vpn-connections \
    --vpn-connection-ids vpn-0813456f62265cd44 \
    --region us-east-1 \
    --query 'VpnConnections[0].VgwTelemetry[*].[OutsideIpAddress,Status,StatusMessage,AcceptedRouteCount]' \
    --output table
  sleep 30
done
```

### **Checklist de Validación**

**Validación Básica:**

* Túnel 1 en estado UP  
* Túnel 2 en estado UP  
* BGP establecido (AcceptedRouteCount \> 0\)  
* Ruta 172.21.0.0/22 visible en Transit Gateway

**Validación Completa:**

* Ping desde on-premise a AWS exitoso  
* Ping desde AWS a on-premise exitoso  
* Traceroute muestra ruta correcta via VPN  
* Latencia aceptable (\< 50ms)

### **Troubleshooting**

**Si túneles no suben:**

* Verificar pre-shared keys en FortiGate  
* Verificar IPs públicas correctas  
* Verificar parámetros IKE e IPsec coinciden  
* Revisar logs en FortiGate

**Si BGP no se establece:**

* Verificar ASN correcto (65400 on-premise, 65000 AWS)  
* Verificar IPs internas de túneles correctas  
* Verificar que túneles IPsec estén UP primero  
* Revisar configuración de neighbors en FortiGate

**Si ping no funciona:**

* Verificar Security Groups permiten ICMP  
* Verificar rutas en Transit Gateway  
* Verificar que cliente está anunciando 172.21.0.0/22  
* Verificar que AWS está anunciando 10.3.0.0/16

---

## **Información de Contacto**

**Para Soporte AWS:**

* Cuenta: Network Account (189993504257)  
* Región: us-east-1  
* Rol: AWSControlTowerExecution

**Para Coordinación con Cliente:**

* Archivo de configuración: vpn-config-fortigate.txt  
* Correo enviado: 2 de febrero de 2026

**Recursos Relacionados:**

* Transit Gateway: tgw-0f394aab46e2e43c1  
* VPC Development: vpc-03cd2b57974e59051  
* Script de creación: scripts/create-vpn-site-to-site.sh

---

## **Próximos Pasos**

1. Esperar confirmación del cliente que configuró FortiGate  
2. Validar estado de túneles desde AWS  
3. Crear instancia EC2 de prueba en VPC DEV  
4. Realizar pruebas de ping bidireccionales  
5. Documentar resultados de pruebas  
6. Confirmar conectividad operacional

---

Preparado por: Equipo de Infraestructura 3HTP Fecha: 2 de febrero de 2026 Versión: 1.0 Estado: VPN Creada \- Pendiente Configuración Cliente

