

  

**Análisis y Mapeo de Datos Cencosud Janis**

**"Accesos a Datos Janis para Cencosud Perú"**

| Información del Documento |  |  |  |  |  |
| ----- | :---: | :---: | :---: | :---: | :---: |
| **Document Type** Especificación Técnica |  |  |  |  |  |
| **Code 3HTP-CEN-002** | **Revisión** 1.0 | **Pages** 19 |  | **Creation Date** 24 de Octubre de 2025 | **Last Update** 24 de Octubre de 2025 |
| **Created by** [Sebastian Lepe](mailto:slepe@3htp.com) |  |  | **Reviewed by**  |  |  |

# 

[1\. Resumen Ejecutivo	6](#1.-resumen-ejecutivo)

[2\. Objetivos del Análisis	7](#2.-objetivos-del-análisis)

[3\. Metodología	8](#3.-metodología)

[4\. Resumen de Mapeo y Hallazgos	9](#4.-resumen-de-mapeo-y-hallazgos)

[4.1 Tabla: wms\_orders	9](#4.1-tabla:-wms_orders)

[4.2 Tabla: wms\_order\_shipping	9](#4.2-tabla:-wms_order_shipping)

[4.3 Tabla: wms\_logistic\_carriers	10](#4.3-tabla:-wms_logistic_carriers)

[4.4 Tabla: wms\_order\_items	11](#4.4-tabla:-wms_order_items)

[4.5 Tabla: wms\_order\_item\_weighables	12](#4.5-tabla:-wms_order_item_weighables)

[4.6 Tabla: wms\_order\_status\_changes	12](#4.6-tabla:-wms_order_status_changes)

[4.7 Tabla: wms\_stores	13](#4.7-tabla:-wms_stores)

[4.8 Tabla: wms\_logistic\_delivery\_planning	14](#4.8-tabla:-wms_logistic_delivery_planning)

[4.9 Tabla: wms\_logistic\_delivery\_ranges	15](#4.9-tabla:-wms_logistic_delivery_ranges)

[4.10 Tabla: wms\_order\_payments	15](#4.10-tabla:-wms_order_payments)

[4.11 Tabla: wms\_order\_payments\_connector\_responses	16](#4.11-tabla:-wms_order_payments_connector_responses)

[4.12 Tabla: wms\_order\_custom\_data\_fields	17](#4.12-tabla:-wms_order_custom_data_fields)

[4.13 Tabla: products	17](#4.13-tabla:-products)

[4.14 Tabla: skus	18](#4.14-tabla:-skus)

[4.15 Tabla: categories	19](#4.15-tabla:-categories)

[4.16 Tabla: admins	20](#4.16-tabla:-admins)

[4.17 Tabla: price	20](#4.17-tabla:-price)

[4.18 Tabla: brands	21](#4.18-tabla:-brands)

[4.19 Tabla: customers	22](#4.19-tabla:-customers)

[4.20 Tabla: wms\_order\_picking	22](#4.20-tabla:-wms_order_picking)

[4.21 Tabla: picking\_round\_orders	23](#4.21-tabla:-picking_round_orders)

[4.22 Tabla: stock	24](#4.22-tabla:-stock)

[4.23 Tabla: promotional\_prices	25](#4.23-tabla:-promotional_prices)

[4.24 Tabla: promotions	25](#4.24-tabla:-promotions)

[4.25 Tabla: invoices	26](#4.25-tabla:-invoices)

[4.26 Tabla: ff\_comments	27](#4.26-tabla:-ff_comments)

[5\. Resumen de Brechas de Datos (Data Gaps)	28](#5.-resumen-de-brechas-de-datos-\(data-gaps\))

[6\. Conclusiones y Recomendaciones Preliminares	29](#6.-conclusiones-y-recomendaciones-preliminares)

# **1\. Resumen Ejecutivo** {#1.-resumen-ejecutivo}

El presente documento tiene como objetivo principal realizar un análisis exhaustivo de la transición de datos desde el actual acceso a la base de datos MySQL de Janis hacia el nuevo modelo basado en APIs y Webhooks. Se busca mapear de forma detallada las tablas y campos consumidos por el equipo de BI de Cencosud, identificar las brechas de información (Data Gaps) existentes entre ambos sistemas y evaluar el impacto potencial sobre los reportes de Power BI. Este análisis es el pilar fundamental para el diseño de la nueva arquitectura de Data Lake en AWS.

# **2\. Objetivos del Análisis** {#2.-objetivos-del-análisis}

* Mapear la Estructura Actual: Identificar y documentar el 100% de las tablas y campos de las bases de datos Legado, WongIO y MetroIO que son utilizados en los procesos de BI actuales.  
* Identificar Fuentes de Datos Nuevas: Correlacionar cada tabla y campo del modelo actual con su correspondiente endpoint en la API de Janis o evento de Webhook.  
* Cuantificar las Brechas (Data Gaps): Determinar con precisión qué datos críticos para la operación de BI no están disponibles a través de las nuevas fuentes.  
* Evaluar el Impacto: Analizar cómo la ausencia de ciertos datos podría afectar la integridad, precisión y disponibilidad de los reportes existentes en Power BI.  
* Proporcionar Insumos para el Diseño: Generar la información necesaria para diseñar un Data Lake que cumpla con los requerimientos de Cencosud, mitigando los riesgos identificados.

# **3\. Metodología** {#3.-metodología}

El análisis se llevará a cabo siguiendo estos pasos:

* Revisión de Fuentes: Se utilizará como base el documento Tablas y campos Actuales Janis MySQL Consumidos en Procesos BI.xlsx para entender el consumo actual.  
* Análisis de APIs/Webhooks: Se estudiará la documentación de Janis (\[JANIS \- CENCO PE\] \- Guía de Integración vía APIs\_2207025.pdf y \[JANIS \- CENCO PE\] \- Mapeo Data Lake \+ APIS \- V2.xlsx) para encontrar las fuentes de datos equivalentes.  
* Mapeo Exhaustivo en Anexo: Todo el mapeo detallado (campo por campo) se realizará en un documento Excel separado (Schema\_Definition\_Janis.xlsx), que servirá como anexo técnico.  
* Documentación de Hallazgos: Los resúmenes, conclusiones y Gaps identificados en el anexo se consolidarán en la sección "Resumen de Mapeo y Hallazgos" de este documento.

# **4\. Resumen de Mapeo y Hallazgos** {#4.-resumen-de-mapeo-y-hallazgos}

Esta sección presenta el resumen consolidado del análisis de cobertura para cada tabla crítica. El mapeo detallado campo por campo se encuentra en el documento anexo: Anexo \- [Schema Definition Janis.xlsx](https://docs.google.com/spreadsheets/d/1IccoqkuQj-p5kGCsH5vvBExH6_mhTql8/edit?usp=sharing&ouid=111913538953004260889&rtpof=true&sd=true).

### **4.1 Tabla: wms\_orders** {#4.1-tabla:-wms_orders}

**Resumen de Cobertura:**

* Campos Totales en Origen: 91  
* Campos Utilizados por BI: 43  
* Campos Mapeados: 39  
* Gaps Críticos: 4  
* Gaps No Críticos: 0  
* Campos con Mapeo Parcial: 1

**Gaps Críticos Identificados:**  
*Campos no encontrados en la documentación de la API de Janis que son utilizados por el equipo de BI.*

* items\_substituted\_qty  
* items\_qty\_missing  
* points\_card  
* status\_vtex

**Gaps No Críticos Identificados:**  
*Campos no encontrados en la documentación de la API de Janis que no son utilizados por el equipo de BI.*

* 

**Observaciones y Mapeos Parciales:**

* **total\_changes**: Se reemplaza por totals.items.amount \- totals.items.originalAmount

**Endpoints Necesarios:**

* [https://oms.janisqa.in/api/order](https://oms.janisqa.in/api/order)  
* https://picking.janis.in/api/session/{id}

### **4.2 Tabla: wms\_order\_shipping** {#4.2-tabla:-wms_order_shipping}

**Resumen de Cobertura:**

* Campos Totales en Origen: 38  
* Campos Utilizados por BI: 14  
* Campos Mapeados: 14  
* Gaps Críticos: 0  
* Gaps No Críticos: 0  
* Campos con Mapeo Parcial: 8

**Gaps Críticos Identificados:**  
*Campos no encontrados en la documentación de la API de Janis que son utilizados por el equipo de BI.*

* 

**Gaps No Críticos Identificados:**  
*Campos no encontrados en la documentación de la API de Janis que no son utilizados por el equipo de BI.*

* 

**Observaciones y Mapeos Parciales:**

* Los valores city, neighborhood, complement, lat y lng están ubicados en addresses array anidado  
* shipping\_window\_start y shipping\_window\_end: Conversión bigint (timestamp) → ISO 8601  
* shipped\_date\_start y shipped\_date\_end: Aproximación: fecha de modificación del shipping

**Endpoints Necesarios:**

* [h](https://oms.janis.in/api/order)ttps://oms.janis.in/api/order  
* https://delivery.janis.in/api/shipping/{id}

### **4.3 Tabla: wms\_logistic\_carriers** {#4.3-tabla:-wms_logistic_carriers}

**Resumen de Cobertura:**

* Campos Totales en Origen: 40  
* Campos Utilizados por BI: 6  
* Campos Mapeados: 6  
* Gaps Críticos: 0  
* Gaps No Críticos: 0  
* Campos con Mapeo Parcial: 0

**Gaps Críticos Identificados:**  
*Campos no encontrados en la documentación de la API de Janis que son utilizados por el equipo de BI.*

* 

**Gaps No Críticos Identificados:**  
*Campos no encontrados en la documentación de la API de Janis que no son utilizados por el equipo de BI.*

* 

**Observaciones y Mapeos Parciales:**

**Endpoints Necesarios:**

* https://delivery.janis.in/api/carrier

### **4\.4 Tabla: wms\_order\_items** {#4.4-tabla:-wms_order_items}

**Resumen de Cobertura:**

* Campos Totales en Origen: 43  
* Campos Utilizados por BI: 18  
* Campos Mapeados: 18  
* Gaps Críticos: 0  
* Gaps No Críticos: 0  
* Campos con Mapeo Parcial: 5

**Gaps Críticos Identificados:**  
*Campos no encontrados en la documentación de la API de Janis que son utilizados por el equipo de BI.*

* 

**Gaps No Críticos Identificados:**  
*Campos no encontrados en la documentación de la API de Janis que no son utilizados por el equipo de BI.*

**Observaciones y Mapeos Parciales:**

* **substitute\_of y quantity\_picked:** Disponible en pickingResult después del picking  
* **quantity\_invoiced:** Disponible después de facturación  
* **quantity\_returned:** Disponible si hay devoluciones  
* **substitute\_type:** Disponible en pickingResult (original/substitute/candidate)  
* 

**Endpoints Necesarios:**

* https://oms.janis.in/api/order/{id}  
* https://oms.janis.in/api/order/

### **4\.5 Tabla: wms\_order\_item\_weighables** {#4.5-tabla:-wms_order_item_weighables}

**Resumen de Cobertura:**

* Campos Totales en Origen: 10  
* Campos Utilizados por BI: 7  
* Campos Mapeados: 7  
* Gaps Críticos: 0  
* Gaps No Críticos: 0  
* Campos con Mapeo Parcial: 3

**Gaps Críticos Identificados:**  
*Campos no encontrados en la documentación de la API de Janis que son utilizados por el equipo de BI.*

* 

**Gaps No Críticos Identificados:**  
*Campos no encontrados en la documentación de la API de Janis que no son utilizados por el equipo de BI.*

* 

**Observaciones y Mapeos Parciales:**

* **id:** items.measurementUnit: kg // ProductGroup name:weightables (Confirmar mas adelante)  
* **weight\_picked:** Solo disponible después del picking, para items con isPrepacked=true  
* **quantity:** Disponible solo despues del picking

**Endpoints Necesarios:**

* https://oms.janis.in/api/order/{id}

### **4\.6 Tabla: wms\_order\_status\_changes** {#4.6-tabla:-wms_order_status_changes}

**Resumen de Cobertura:**

* Campos Totales en Origen: 9  
* Campos Utilizados por BI: 6  
* Campos Mapeados: 6  
* Gaps Críticos: 0  
* Gaps No Críticos: 0  
* Campos con Mapeo Parcial: 4

**Gaps Críticos Identificados:**  
*Campos no encontrados en la documentación de la API de Janis que son utilizados por el equipo de BI.*

* 

**Gaps No Críticos Identificados:**  
*Campos no encontrados en la documentación de la API de Janis que no son utilizados por el equipo de BI.*

* 

**Observaciones y Mapeos Parciales:**

* **extra:** Objeto JSON en API, text en BD  
* **new\_status:** API usa strings (new, needsIntervention), BD usa números  
* **user\_created:** Puede ser Null en la API  
* **date\_created:** Conversión ISO 8601 → Unix timestamp

**Endpoints Necesarios:**

* https://oms.janis.in/api/order/{id}/  
* https://oms.janis.in/api/order/{id}/history

### **4\.7 Tabla: wms\_stores** {#4.7-tabla:-wms_stores}

**Resumen de Cobertura:**

* Campos Totales en Origen: 45  
* Campos Utilizados por BI: 23  
* Campos Mapeados: 23  
* Gaps Críticos: 0  
* Gaps No Críticos: 0  
* Campos con Mapeo Parcial: 0

**Gaps Críticos Identificados:**  
*Campos no encontrados en la documentación de la API de Janis que son utilizados por el equipo de BI.*

* 

**Gaps No Críticos Identificados:**  
*Campos no encontrados en la documentación de la API de Janis que no son utilizados por el equipo de BI.*

* 

**Observaciones y Mapeos Parciales:**

* **country:** API devuelve ISO3 (ej: PER), BD usa ID numérico  
* **lat y lng:** Conversión decimal(12,9) → number  
* **apply\_quotation:** Conversión tinyint(1) → boolean  
* **date\_modified y date\_created:** Conversión bigint (timestamp) → ISO 8601

**Endpoints Necesarios:**

* https://commerce.janis.in/api/stores

### **4.8 Tabla: wms\_logistic\_delivery\_planning** {#4.8-tabla:-wms_logistic_delivery_planning}

**Resumen de Cobertura:**

* Campos Totales en Origen: 26  
* Campos Utilizados por BI: 26  
* Campos Mapeados: 21  
* Gaps Críticos: 5  
* Gaps No Críticos: 1  
* Campos con Mapeo Parcial: 0

**Gaps Críticos Identificados:**  
*Campos no encontrados en la documentación de la API de Janis que son utilizados por el equipo de BI.*

* dynamic\_quota  
* carrier  
* quota  
* offset\_start  
* edited

**Gaps No Críticos Identificados:**  
*Campos no encontrados en la documentación de la API de Janis que no son utilizados por el equipo de BI.*

* delivery\_range

**Observaciones y Mapeos Parciales:**

* **carrier:** falta confirmación por parte de Janis  
* **dynamic\_quota:** No existe en V2/ cenco usa cupos dinámicos  
* **date\_start, date\_end, date\_created y date\_modified:** Fecha del schedule en formato ISO 8601

**Endpoints Necesarios:**

* https://tms.janis.in/api/route-planning  
* https://delivery.janis.in/api/carrier  
* https://tms.janis.in/api/route-capacity-slot  
* https://delivery.janis.in/api/time-slot-order  
* https://delivery.janis.in/api/carrier-group-time-slot  
* https://delivery.janis.in/api/time-slot

### 

### **4.9 Tabla: wms\_logistic\_delivery\_ranges** {#4.9-tabla:-wms_logistic_delivery_ranges}

**Resumen de Cobertura:**

* Campos Totales en Origen: 10  
* Campos Utilizados por BI: 6  
* Campos Mapeados: 6  
* Gaps Críticos: 0  
* Gaps No Críticos: 0  
* Campos con Mapeo Parcial: 0

**Gaps Críticos Identificados:**  
*Campos no encontrados en la documentación de la API de Janis que son utilizados por el equipo de BI.*

**Gaps No Críticos Identificados:**  
*Campos no encontrados en la documentación de la API de Janis que no son utilizados por el equipo de BI.*

**Observaciones y Mapeos Parciales:**

* **time\_start y time\_end:** Formato HH:MM

**Endpoints Necesarios:**

* https://delivery.janis.in/api/time-slot

### **4.10 Tabla: wms\_order\_payments** {#4.10-tabla:-wms_order_payments}

**Resumen de Cobertura:**

* Campos Totales en Origen: 56  
* Campos Utilizados por BI: 11  
* Campos Mapeados: 10  
* Gaps Críticos: 1  
* Gaps No Críticos: 0  
* Campos con Mapeo Parcial: 3

**Gaps Críticos Identificados:**  
*Campos no encontrados en la documentación de la API de Janis que son utilizados por el equipo de BI.*

* authorization\_code

**Gaps No Críticos Identificados:**  
*Campos no encontrados en la documentación de la API de Janis que no son utilizados por el equipo de BI.*

* 

**Observaciones y Mapeos Parciales:**

* **authorization\_code:** Chequeo por parte de Janis  
* **cc\_bank:** Campo acquirer puede contener banco adquirente  
* **cc\_brand:** Marca de tarjeta en paymentSystemName (Visa, Mastercard, etc)  
* **cc\_type:** Tipo de tarjeta en paymentGroup (Credit Card, Debit Card)

**Endpoints Necesarios:**

* https://oms.janis.in/api/order/{id}

### **4.11 Tabla: wms\_order\_payments\_connector\_responses** {#4.11-tabla:-wms_order_payments_connector_responses}

**Resumen de Cobertura:**

* Campos Totales en Origen: 5  
* Campos Utilizados por BI: 5  
* Campos Mapeados: 3  
* Gaps Críticos: 2  
* Gaps No Críticos: 0  
* Campos con Mapeo Parcial: 0

**Gaps Críticos Identificados:**  
*Campos no encontrados en la documentación de la API de Janis que son utilizados por el equipo de BI.*

* id  
* parent

**Gaps No Críticos Identificados:**  
*Campos no encontrados en la documentación de la API de Janis que no son utilizados por el equipo de BI.*

* 

**Observaciones y Mapeos Parciales:**

* **id:** Chequeo por parte de Janis  
* **parent:** Chequeo por parte de Janis  
* **payment\_id:** ID del payment al que pertenece la respuesta  
* **field:** Nombre del campo (key del objeto JSON)  
* **value:** Valor del campo (value del objeto JSON)

**Endpoints Necesarios:**

* https://oms.janis.in/api/order

### 

### **4.12 Tabla: wms\_order\_custom\_data\_fields** {#4.12-tabla:-wms_order_custom_data_fields}

**Resumen de Cobertura:**

* Campos Totales en Origen: 5  
* Campos Utilizados por BI: 5  
* Campos Mapeados: 4  
* Gaps Críticos: 1  
* Gaps No Críticos: 0  
* Campos con Mapeo Parcial: 0

**Gaps Críticos Identificados:**  
*Campos no encontrados en la documentación de la API de Janis que son utilizados por el equipo de BI.*

* id

**Gaps No Críticos Identificados:**  
*Campos no encontrados en la documentación de la API de Janis que no son utilizados por el equipo de BI.*

* 

**Observaciones y Mapeos Parciales:**

* **id:** Falta chequeo por parte de Janis

**Endpoints Necesarios:**

* https://oms.janis.in/api/order

### **4.13 Tabla: products** {#4.13-tabla:-products}

**Resumen de Cobertura:**

* Campos Totales en Origen: 40  
* Campos Utilizados por BI: 20  
* Campos Mapeados: 15  
* Gaps Críticos: 2  
* Gaps No Críticos: 3  
* Campos con Mapeo Parcial: 4

**Gaps Críticos Identificados:**  
*Campos no encontrados en la documentación de la API de Janis que son utilizados por el equipo de BI.*

* cart\_limit  
* min\_stock

**Gaps No Críticos Identificados:**  
*Campos no encontrados en la documentación de la API de Janis que no son utilizados por el equipo de BI.*

* erp\_category  
* erp\_brand  
* supplier

**Observaciones y Mapeos Parciales:**

* **erp\_category:** Cenco ya no usa este campo  
* **erp\_brand**: Cenco ya no usa este campo  
* **supplier:** Cenco ya no usa este campo  
* **id:** Tipo de valor es string  
* **category:** Tipo de valor es string  
* **brand:** Tipo de valor es string  
* **status:** Tipo de valor es string  
* **user\_modified:** Tipo de valor es string  
* **date\_modified:** Conversión bigint timestamp → ISO 8601  
* **infinite\_stock:** Conversión tinyint(1) → boolean, requiere confirmación

**Endpoints Necesarios:**

* https://catalog.janis.in/api/product

### 

### **4.14 Tabla: skus** {#4.14-tabla:-skus}

**Resumen de Cobertura:**

* Campos Totales en Origen: 47  
* Campos Utilizados por BI: 32  
* Campos Mapeados: 32  
* Gaps Críticos: 5  
* Gaps No Críticos: 0  
* Campos con Mapeo Parcial: 4

**Gaps Críticos Identificados:**  
*Campos no encontrados en la documentación de la API de Janis que son utilizados por el equipo de BI.*

* ord  
* cart\_limit  
* legal\_unit\_multiplier  
* min\_stock

**Gaps No Críticos Identificados:**  
*Campos no encontrados en la documentación de la API de Janis que no son utilizados por el equipo de BI.*

* 

**Observaciones y Mapeos Parciales:**

* **ord:** Chequeo por parte de Janis  
* **attributes\[?\]:** Posiblemente en atributos personalizados \- requiere consulta adicional  
* **measurementUnit:** Puede ser el mismo que measurement\_unit  
* 

**Endpoints Necesarios:**

* [https://catalog.janis.in/api/sku](https://catalog.janis.in/api/sku)  
* https://catalog.janis.in/api/sku/{id}/attribute

### **4.15 Tabla: categories** {#4.15-tabla:-categories}

**Resumen de Cobertura:**

* Campos Totales en Origen: 13  
* Campos Utilizados por BI: 5  
* Campos Mapeados: 5  
* Gaps Críticos: 0  
* Gaps No Críticos: 0  
* Campos con Mapeo Parcial: 0

**Gaps Críticos Identificados:**  
*Campos no encontrados en la documentación de la API de Janis que son utilizados por el equipo de BI.*

* 

**Gaps No Críticos Identificados:**  
*Campos no encontrados en la documentación de la API de Janis que no son utilizados por el equipo de BI.*

* 

**Observaciones y Mapeos Parciales:**

* **ref\_id:** Conversión int → string  
* **status:** Conversión int → string  
* **id:** Conversión bigint → string, valores diferentes por diseño

**Endpoints Necesarios:**

* https://catalog.janis.in/api/category

### **4.16 Tabla: admins** {#4.16-tabla:-admins}

**Resumen de Cobertura:**

* Campos Totales en Origen: 22  
* Campos Utilizados por BI: 7  
* Campos Mapeados: 7  
* Gaps Críticos: 0  
* Gaps No Críticos: 0  
* Campos con Mapeo Parcial: 3

**Gaps Críticos Identificados:**  
*Campos no encontrados en la documentación de la API de Janis que son utilizados por el equipo de BI.*

* 

**Gaps No Críticos Identificados:**  
*Campos no encontrados en la documentación de la API de Janis que no son utilizados por el equipo de BI.*

* 

**Observaciones y Mapeos Parciales:**

* **id**: El id es alfanumerico en la API y bigint en la DB  
* **username**: Se concatena firstName y lastName  
* **document:** Cambió el nombre del campo pero entran los mismos datos

**Endpoints Necesarios:**

* https://id.janis.in/api/user/{id}  
* https://id.janis.in/api/user

### **4.17 Tabla: price** {#4.17-tabla:-price}

**Resumen de Cobertura:**

* Campos Totales en Origen: 26  
* Campos Utilizados por BI: 10  
* Campos Mapeados: 26  
* Gaps Críticos: 0  
* Gaps No Críticos: 0  
* Campos con Mapeo Parcial: 3

**Gaps Críticos Identificados:**  
*Campos no encontrados en la documentación de la API de Janis que son utilizados por el equipo de BI.*

* 

**Gaps No Críticos Identificados:**  
*Campos no encontrados en la documentación de la API de Janis que no son utilizados por el equipo de BI.*

* 

**Observaciones y Mapeos Parciales:**

* **item\_id**: SKU ID mapeado a sku  
* **store\_id**: Requiere /sc-sku-price para precios por tienda  
* **store\_price:** Precio específico por sales channel, requiere desagregación

**Endpoints Necesarios:**

* https://pricing.janis.in/api/price  
* https://pricing.janis.in/api/sc-sku-price

### **4.18 Tabla: brands** {#4.18-tabla:-brands}

**Resumen de Cobertura:**

* Campos Totales en Origen: 12  
* Campos Utilizados por BI: 4  
* Campos Mapeados: 4  
* Gaps Críticos: 0  
* Gaps No Críticos: 0  
* Campos con Mapeo Parcial: 1

**Gaps Críticos Identificados:**  
*Campos no encontrados en la documentación de la API de Janis que son utilizados por el equipo de BI.*

* 

**Gaps No Críticos Identificados:**  
*Campos no encontrados en la documentación de la API de Janis que no son utilizados por el equipo de BI.*

* 

**Observaciones y Mapeos Parciales:**

* **id:** Conversión bigint → string, valores diferentes por diseño V1→V2

**Endpoints Necesarios:**

* https://catalog.janis.in/api/brand

### **4.19 Tabla: customers** {#4.19-tabla:-customers}

**Resumen de Cobertura:**

* Campos Totales en Origen: 34  
* Campos Utilizados por BI: 13  
* Campos Mapeados: 13  
* Gaps Críticos: 2  
* Gaps No Críticos: 0  
* Campos con Mapeo Parcial: 0

**Gaps Críticos Identificados:**  
*Campos no encontrados en la documentación de la API de Janis que son utilizados por el equipo de BI.*

* vtex\_id  
* phone\_alt

**Gaps No Críticos Identificados:**  
*Campos no encontrados en la documentación de la API de Janis que no son utilizados por el equipo de BI.*

* 

**Observaciones y Mapeos Parciales:**

* **vtex\_id:** Chequear con Janis  
* **phone\_alt:** Chequear con Janis

**Endpoints Necesarios:**

* https://crm.janis.in/api/customer

### 

### **4.20 Tabla: wms\_order\_picking** {#4.20-tabla:-wms_order_picking}

**Resumen de Cobertura:**

* Campos Totales en Origen: 7  
* Campos Utilizados por BI: 6  
* Campos Mapeados: 6  
* Gaps Críticos: 0  
* Gaps No Críticos: 4  
* Campos con Mapeo Parcial: 2

**Gaps Críticos Identificados:**  
*Campos no encontrados en la documentación de la API de Janis que son utilizados por el equipo de BI.*

* 

**Gaps No Críticos Identificados:**  
*Campos no encontrados en la documentación de la API de Janis que no son utilizados por el equipo de BI.*

* picker  
* pick\_start\_time  
* pick\_end\_time  
* total\_time  
* status

**Observaciones y Mapeos Parciales:**

* **picker**: Se menciona en la API pero no aparece...  
* **pick\_start\_time**: Se menciona en la API pero no aparece...  
* **pick\_end\_time**: Se menciona en la API pero no aparece…  
* **total\_time**: Se calcula en ETL: (endPickingTime \- startPickingTime) / 1000  
* **status:** Valores diferentes: BD usa números, API usa strings (pending/completed/etc)

**Endpoints Necesarios:**

* https://picking.janis.in/api/session

### **4.21 Tabla: picking\_round\_orders** {#4.21-tabla:-picking_round_orders}

**Resumen de Cobertura:**

* Campos Totales en Origen: 2  
* Campos Utilizados por BI: 2  
* Campos Mapeados: 2  
* Gaps Críticos: 1  
* Gaps No Críticos: 0  
* Campos con Mapeo Parcial: 0

**Gaps Críticos Identificados:**  
*Campos no encontrados en la documentación de la API de Janis que son utilizados por el equipo de BI.*

* picking\_round

**Gaps No Críticos Identificados:**  
*Campos no encontrados en la documentación de la API de Janis que no son utilizados por el equipo de BI.*

* 

**Observaciones y Mapeos Parciales:**

* Tabla vacía en el endpoint

**Endpoints Necesarios:**

* https://picking.janis.in/api/session-picker-batch

### **4.22 Tabla: stock** {#4.22-tabla:-stock}

**Resumen de Cobertura:**

* Campos Totales en Origen: 22  
* Campos Utilizados por BI: 12  
* Campos Mapeados: 12  
* Gaps Críticos: 0  
* Gaps No Críticos: 0  
* Campos con Mapeo Parcial: 0

**Gaps Críticos Identificados:**  
*Campos no encontrados en la documentación de la API de Janis que son utilizados por el equipo de BI.*

* 

**Gaps No Críticos Identificados:**  
*Campos no encontrados en la documentación de la API de Janis que no son utilizados por el equipo de BI.*

* 

**Observaciones y Mapeos Parciales:**

* 

**Endpoints Necesarios:**

* https://wms.janis.in/api/stock

### **4.23 Tabla: promotional\_prices** {#4.23-tabla:-promotional_prices}

**Resumen de Cobertura:**

* Campos Totales en Origen: 26  
* Campos Utilizados por BI: 15  
* Campos Mapeados: 15  
* Gaps Críticos: 0  
* Gaps No Críticos: 0  
* Campos con Mapeo Parcial: 0

**Gaps Críticos Identificados:**  
*Campos no encontrados en la documentación de la API de Janis que son utilizados por el equipo de BI.*

* 

**Gaps No Críticos Identificados:**  
*Campos no encontrados en la documentación de la API de Janis que no son utilizados por el equipo de BI.*

* 

**Observaciones y Mapeos Parciales:**

* Todos los campos existen y son los mismos, la consulta es por tienda  
* Se debe confirmar el endpoint con Janis

**Endpoints Necesarios:**

* \[Endpoint1\]

### **4.24 Tabla: promotions** {#4.24-tabla:-promotions}

**Resumen de Cobertura:**

* Campos Totales en Origen: 26  
* Campos Utilizados por BI: 12  
* Campos Mapeados: 12  
* Gaps Críticos: 0  
* Gaps No Críticos: 0  
* Campos con Mapeo Parcial: 0

**Gaps Críticos Identificados:**  
*Campos no encontrados en la documentación de la API de Janis que son utilizados por el equipo de BI.*

* 

**Gaps No Críticos Identificados:**  
*Campos no encontrados en la documentación de la API de Janis que no son utilizados por el equipo de BI.*

* 

**Observaciones y Mapeos Parciales:**

* Se encuentran en la tabla VTEX  
* confirmar valores con Janis

**Endpoints Necesarios:**

* Confirmar endpoint con Janis

### **4.25 Tabla: invoices** {#4.25-tabla:-invoices}

**Resumen de Cobertura:**

* Campos Totales en Origen: 16  
* Campos Utilizados por BI: 6  
* Campos Mapeados: 6  
* Gaps Críticos: 0  
* Gaps No Críticos: 0  
* Campos con Mapeo Parcial: 0

**Gaps Críticos Identificados:**  
*Campos no encontrados en la documentación de la API de Janis que son utilizados por el equipo de BI.*

* 

**Gaps No Críticos Identificados:**  
*Campos no encontrados en la documentación de la API de Janis que no son utilizados por el equipo de BI.*

* 

**Observaciones y Mapeos Parciales:**

* **invoices\[\].dateCreated:** Conversión Unix timestamp → ISO 8601

**Endpoints Necesarios:**

* https://oms.janis.in/api/order

### **4.26 Tabla: ff\_comments** {#4.26-tabla:-ff_comments}

**Resumen de Cobertura:**

* Campos Totales en Origen: 7  
* Campos Utilizados por BI: 7  
* Campos Mapeados: \[TBD\]  
* Gaps Críticos: \[TBD\]  
* Gaps No Críticos: \[TBD\]  
* Campos con Mapeo Parcial: \[TBD\]

**Gaps Críticos Identificados:**  
*Campos no encontrados en la documentación de la API de Janis que son utilizados por el equipo de BI.*

* \[Campo no crítico 1\]

**Gaps No Críticos Identificados:**  
*Campos no encontrados en la documentación de la API de Janis que no son utilizados por el equipo de BI.*

* \[Campo no crítico 1\]  
* \[Campo no crítico 2\]

**Observaciones y Mapeos Parciales:**

* \[Observación de incongruencias entre campos\]

**Endpoints Necesarios:**

* \[Endpoint1\]

### **5\. Resumen de Brechas de Datos (Data Gaps)** {#5.-resumen-de-brechas-de-datos-(data-gaps)}

En esta sección se listan de forma consolidada los principales Gaps identificados durante el mapeo.

| ID | Dato Faltante | Descripción del Gap | Impacto Potencial en BI | Prioridad |
| :---: | ----- | ----- | ----- | ----- |
|  |  |  |  |  |

# 

# 

# 

# 

# **6\. Conclusiones y Recomendaciones Preliminares** {#6.-conclusiones-y-recomendaciones-preliminares}

* **Conclusión 1:** Se observa una cobertura aparentemente buena para los datos transaccionales principales (órdenes, items, clientes).

* **Conclusión 2:** Existen brechas críticas identificadas preliminarmente en entidades maestras como promotions, lo cual representa un riesgo alto para los reportes de BI.

* **Recomendación 1:** Priorizar la investigación y validación de los Data Gaps de prioridad Alta mediante consultas directas al equipo técnico de Janis.

* **Recomendación 2:** Iniciar la creación de scripts o cuadernos de prueba para consumir los endpoints identificados y validar la estructura real de los payloads JSON.