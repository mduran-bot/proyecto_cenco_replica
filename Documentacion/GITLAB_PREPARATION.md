# Preparación para Subir a GitLab

**Fecha**: 30 de Enero, 2026  
**Objetivo**: Preparar el proyecto de infraestructura Terraform para repositorio GitLab

---

## Archivos a INCLUIR en GitLab

### 📁 Directorio Raíz `terraform/`

#### Archivos Core de Terraform (INCLUIR)
```
✅ main.tf                    # Orquestador principal
✅ variables.tf               # Declaración de variables
✅ outputs.tf                 # Outputs del deployment
✅ versions.tf                # Versiones de Terraform y providers
✅ .gitignore                 # Ignorar archivos sensibles
✅ terraform.tfvars.example   # Plantilla de configuración
```

#### Documentación Esencial (INCLUIR)
```
✅ README.md                  # Guía principal del proyecto
✅ DEPLOYMENT_GUIDE.md        # Guía de deployment
✅ MULTI_AZ_EXPANSION.md      # Guía para expandir a Multi-AZ
✅ SINGLE_AZ_DEPLOYMENT.md    # Documentación de Single-AZ
✅ REDSHIFT_INTEGRATION.md    # Integración con Redshift
```

### 📁 `terraform/modules/` (INCLUIR TODO)

Todos los módulos son necesarios:
```
✅ modules/vpc/
✅ modules/security-groups/
✅ modules/vpc-endpoints/
✅ modules/nacls/
✅ modules/waf/
✅ modules/eventbridge/
✅ modules/monitoring/
✅ modules/tagging/
```

Cada módulo debe incluir:
- `main.tf`
- `variables.tf`
- `outputs.tf`
- `versions.tf` (si existe)
- `README.md` (si existe)

### 📁 `terraform/environments/` (INCLUIR)

```
✅ environments/dev/
✅ environments/staging/
✅ environments/prod/
✅ environments/README.md
```

Cada ambiente debe tener:
- `main.tf` (si existe)
- `*.tfvars.example` (plantillas)
- README específico

### 📁 `terraform/scripts/` (INCLUIR)

Scripts útiles para deployment:
```
✅ scripts/deploy.sh
✅ scripts/init-environment.sh
✅ scripts/backup-state.sh
✅ scripts/README.md
```

### 📁 `terraform/shared/` (INCLUIR)

Configuración compartida:
```
✅ shared/backend.tf
✅ shared/providers.tf
✅ shared/variables.tf
```

---

## Archivos a EXCLUIR de GitLab

### ❌ Archivos de Estado y Planes
```
❌ *.tfstate
❌ *.tfstate.*
❌ *.tfplan
❌ .terraform/
❌ .terraform.lock.hcl
```

### ❌ Archivos de Testing y LocalStack
```
❌ terraform.tfvars.testing*
❌ localstack.tfvars
❌ localstack_override.tf*
❌ test_localstack.tf
❌ *localstack*.cmd
❌ *localstack*.ps1
❌ LOCALSTACK_*.md
```

### ❌ Logs y Archivos Temporales
```
❌ *.log
❌ *.backup
❌ *.backup.*
```

### ❌ Scripts de Testing/Debug
```
❌ deploy-testing*.ps1
❌ diagnose-*.ps1
❌ force-plan.ps1
❌ disable-*.ps1
❌ destroy-*.ps1
❌ remove-*.ps1
❌ clean-*.ps1
❌ validate-aws-deployment.ps1
❌ validate_all.ps1
❌ pre-deployment-check.ps1
❌ prepare-aws-deployment.ps1
```

### ❌ Documentación de Testing/Debug
```
❌ DEPLOYMENT_STATUS_FINAL.md
❌ DEPLOYMENT_NOTES.md
❌ TROUBLESHOOTING_*.md
❌ SOLUCION_FINAL.md
❌ VALIDATION_SUMMARY.md
❌ *_SUMMARY.md (excepto los de módulos)
❌ CHECKLIST_CLIENTE.md
❌ CLIENT_MANAGED_SERVICES.md
❌ COMANDOS_UTILES.md
❌ GUIA_DEPLOYMENT_TESTING.md
❌ QUICK_*.md
❌ AWS_DEPLOYMENT_QUICKSTART.md
❌ AWS_PLAN_SUMMARY.md
❌ READY_FOR_AWS.md
```

### ❌ Directorio de Tests Completo
```
❌ test/ (todo el directorio)
```

### ❌ Archivos de Configuración con Valores Reales
```
❌ terraform.tfvars (si contiene valores reales del cliente)
⚠️ NOTA: terraform.tfvars existe como plantilla con valores de ejemplo
⚠️ El cliente debe personalizarlo localmente pero NO commitear valores reales
```

---

## Estructura Final para GitLab

```
janis-cencosud-infrastructure/
├── .gitignore
├── README.md
├── DEPLOYMENT_GUIDE.md
├── MULTI_AZ_EXPANSION.md
├── SINGLE_AZ_DEPLOYMENT.md
├── REDSHIFT_INTEGRATION.md
│
├── main.tf
├── variables.tf
├── outputs.tf
├── versions.tf
├── terraform.tfvars.example
│
├── modules/
│   ├── vpc/
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   ├── outputs.tf
│   │   └── versions.tf
│   ├── security-groups/
│   ├── vpc-endpoints/
│   ├── nacls/
│   ├── waf/
│   ├── eventbridge/
│   ├── monitoring/
│   └── tagging/
│
├── environments/
│   ├── README.md
│   ├── dev/
│   │   └── dev.tfvars.example
│   ├── staging/
│   │   └── staging.tfvars.example
│   └── prod/
│       └── prod.tfvars.example
│
├── scripts/
│   ├── README.md
│   ├── deploy.sh
│   ├── init-environment.sh
│   └── backup-state.sh
│
└── shared/
    ├── backend.tf
    ├── providers.tf
    └── variables.tf
```

---

## Pasos para Preparar el Proyecto

### 1. Crear/Actualizar .gitignore

Asegurarse que `.gitignore` incluya:
```gitignore
# Terraform
*.tfstate
*.tfstate.*
*.tfplan
*.tfplan.*
.terraform/
.terraform.lock.hcl

# Credenciales y configuraciones sensibles
# NOTA: terraform.tfvars es una plantilla y puede incluirse en Git
# Si se personaliza con valores reales, usar terraform.tfvars.local
terraform.tfvars.local
**/credentials.tfvars
*.pem
*.key

# Logs
*.log
terraform.log

# Backups
*.backup
*.backup.*

# LocalStack
localstack.tfvars
localstack_override.tf*
test_localstack.tf

# Testing
terraform.tfvars.testing*
```

**Estrategia Recomendada para Configuración:**
- `terraform.tfvars` - Plantilla con valores de ejemplo (incluir en Git)
- `terraform.tfvars.local` - Valores reales del cliente (excluir de Git)
- Cliente copia plantilla a `.local` y personaliza localmente

### 2. Limpiar Comentarios en Archivos Core

Archivos a limpiar:
- `main.tf` - Dejar solo comentarios de secciones y notas importantes
- `variables.tf` - Limpiar comentarios redundantes
- `outputs.tf` - Mantener descripciones claras
- Módulos individuales - Limpiar comentarios de debug

### 3. Crear Archivos .example

**NOTA**: El archivo `terraform.tfvars` ya existe como plantilla con valores de ejemplo.
Este archivo puede incluirse en Git ya que contiene solo placeholders.

Para ambientes específicos, crear plantillas sin valores sensibles:
```bash
# En directorio terraform/
cp terraform.tfvars terraform.tfvars.example
# Editar y reemplazar valores reales con placeholders

# En cada ambiente
cp environments/dev/dev.tfvars environments/dev/dev.tfvars.example
cp environments/staging/staging.tfvars environments/staging/staging.tfvars.example
cp environments/prod/prod.tfvars environments/prod/prod.tfvars.example
```

### 4. Actualizar README.md

Asegurarse que README incluya:
- Descripción del proyecto
- Requisitos previos
- Instrucciones de configuración
- Comandos básicos
- Estructura del proyecto
- Guía de deployment

### 5. Eliminar Archivos Innecesarios

Antes de commit, eliminar:
```bash
# Desde directorio terraform/
rm -rf .terraform/
rm *.tfstate*
rm *.tfplan
rm *.log
rm *testing*.ps1
rm *localstack*
rm -rf test/
```

---

## Comandos Git para Subir a GitLab

```bash
# 1. Inicializar repositorio (si no existe)
cd terraform/
git init

# 2. Agregar remote de GitLab
git remote add origin https://gitlab.com/tu-org/janis-cencosud-infrastructure.git

# 3. Agregar archivos (respetando .gitignore)
git add .

# 4. Verificar qué se va a subir
git status

# 5. Commit inicial
git commit -m "Initial commit: AWS infrastructure for Janis-Cencosud integration

- VPC with public/private subnets (Single-AZ)
- 7 Security Groups
- VPC Endpoints (S3, Glue, Secrets Manager, etc.)
- EventBridge for polling orchestration
- Monitoring with VPC Flow Logs and CloudWatch
- WAF for API Gateway protection
- Modular Terraform structure
- Multi-environment support (dev/staging/prod)
"

# 6. Push a GitLab
git branch -M main
git push -u origin main
```

---

## Checklist Final

Antes de hacer push a GitLab:

- [ ] `.gitignore` está configurado correctamente
- [ ] No hay archivos `.tfstate` o `.tfplan`
- [ ] No hay credenciales en ningún archivo
- [ ] Archivos `.tfvars` tienen valores de ejemplo (placeholders)
- [ ] Comentarios innecesarios eliminados
- [ ] README.md está actualizado
- [ ] Documentación esencial incluida
- [ ] Módulos tienen README propios
- [ ] Scripts tienen permisos de ejecución
- [ ] No hay archivos de testing/debug
- [ ] No hay logs o backups

---

## Notas Importantes

### ⚠️ Seguridad

**NUNCA subir a GitLab:**
- Archivos `terraform.tfstate` (contienen IDs de recursos y pueden tener datos sensibles)
- Archivos con credenciales AWS
- Archivos `.tfvars` con valores reales
- Logs que puedan contener información sensible

### 📝 Buenas Prácticas

1. **Usar archivos .example**: Siempre crear plantillas sin valores reales
2. **Documentar cambios**: Commits descriptivos
3. **Proteger rama main**: Configurar en GitLab para requerir merge requests
4. **CI/CD**: Considerar agregar pipeline de GitLab CI para validación automática
5. **Tags**: Usar tags de Git para versiones estables

### 🔄 Mantenimiento

Después del push inicial:
- Crear branches para cambios (`feature/`, `fix/`, `docs/`)
- Usar merge requests para revisión de código
- Mantener documentación actualizada
- Versionar cambios importantes con tags

---

**Preparado por**: Vicente Morales
**Fecha**: 30 de Enero, 2026  
**Versión**: 1.0
