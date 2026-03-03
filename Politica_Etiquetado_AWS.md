# Política de Etiquetado AWS (Tagging)

## 1. Objetivo
Definir una política estándar de etiquetado (tagging) para los recursos desplegados en AWS, con el fin de facilitar:
- La gestión de costos
- La trazabilidad de recursos
- La seguridad y el cumplimiento
- La automatización y el gobierno cloud

Esta política es obligatoria para todos los equipos que utilicen servicios en AWS.

---

## 2. Alcance
Aplica a **todos los recursos creados en AWS**, independientemente del servicio o cuenta, incluyendo ambientes productivos y no productivos.

---

## 3. Principios Generales
- Todos los recursos **deben ser creados con tags**
- Los tags obligatorios **no pueden quedar vacíos**
- Los nombres de las etiquetas son **case sensitive**
- Se debe respetar la convención definida para claves y valores

---

## 4. Tags Obligatorios

| Tag Key        | Descripción |
|---------------|------------|
| `Application` | Nombre de la aplicación o sistema |
| `Environment` | Ambiente donde corre el recurso |
| `Owner`       | Responsable del recurso |
| `CostCenter`  | Centro de costos asociado |
| `BusinessUnit`| Unidad de negocio |
| `Country`     | País |
| `Criticality` | Nivel de criticidad |

---

## 5. Valores Permitidos

### Environment
Valores permitidos:
- `prod`
- `qa`
- `dev`
- `uat`
- `sandbox`

### Criticality
Valores permitidos:
- `high`
- `medium`
- `low`

---

## 6. Convenciones de Nombres
- Usar valores **claros y descriptivos**
- Evitar espacios (usar `-` o `_` si es necesario)
- No usar caracteres especiales
- No usar valores genéricos como `test`, `temp`, `misc`

---

## 7. Buenas Prácticas
- Aplicar tags **al momento de crear** el recurso
- Usar políticas de IAM o SCP para **forzar el etiquetado**
- Revisar periódicamente recursos sin tags
- Automatizar el tagging mediante Terraform o CloudFormation

---

## 8. Ejemplo de Etiquetado Correcto

Application = ecommerce  
Environment = prod  
Owner = cloud-team  
CostCenter = CC1234  
BusinessUnit = retail  
Country = CL  
Criticality = high  

---

## 9. Cumplimiento
Los recursos que no cumplan con esta política:
- Pueden ser **bloqueados**
- Pueden ser **eliminados**
- No serán considerados en soporte ni monitoreo

El cumplimiento es responsabilidad del equipo propietario del recurso.

---

## 10. Referencias
- Cloud Core Team – Gobierno Cloud
- AWS Resource Tagging Best Practices
