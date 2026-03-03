# 🔄 Git Workflow para el Equipo

**Fecha**: 18 de Febrero de 2026  
**Equipo**: Vicente + Max  
**Proyecto**: Janis-Cencosud Data Integration

---

## 📊 Estado Actual

### ✅ Rama de Vicente (Completada)
- **Rama**: `feature/task-5-iceberg-management`
- **Estado**: ✅ Subida a GitHub
- **Tarea**: Task 5 - Iceberg Table Management
- **Archivos**: 20 archivos modificados/creados
- **Commits**: 1 commit con mensaje descriptivo
- **Link PR**: https://github.com/vicemora97/Proyecto_Cenco/pull/new/feature/task-5-iceberg-management

### 🔄 Próximos Pasos

#### Para Vicente:
1. ✅ Rama creada y subida
2. ⏭️ Crear Pull Request en GitHub (opcional, ver abajo)
3. ⏭️ Esperar revisión de Max (opcional)
4. ⏭️ Continuar con otras tareas en nuevas ramas

#### Para Max:
1. ⏭️ Crear su propia rama para su trabajo
2. ⏭️ Trabajar en sus tareas asignadas
3. ⏭️ Subir su rama cuando termine
4. ⏭️ Coordinar merge a `main`

---

## 🌳 Estructura de Ramas

```
main (protegida, siempre estable)
  ├── feature/task-5-iceberg-management (Vicente) ✅ SUBIDA
  └── feature/task-X-nombre (Max) ⏭️ PENDIENTE
```

---

## 📝 Comandos Git para Max

### 1. Actualizar tu repositorio local
```bash
# Asegurarte de tener los últimos cambios
git fetch origin

# Ver todas las ramas
git branch -a
```

### 2. Crear tu propia rama
```bash
# Desde main, crear tu rama
git checkout main
git pull origin main
git checkout -b feature/task-X-nombre-descriptivo

# Ejemplo:
# git checkout -b feature/task-6-checkpoint
# git checkout -b feature/task-7-deduplication
```

### 3. Trabajar en tu rama
```bash
# Hacer cambios en tus archivos
# ...

# Agregar archivos
git add <archivos>

# Commit con mensaje descriptivo
git commit -m "feat(task-X): Descripción de tu trabajo"

# Subir tu rama
git push -u origin feature/task-X-nombre-descriptivo
```

### 4. Ver el trabajo de Vicente (opcional)
```bash
# Cambiar a la rama de Vicente para revisar
git checkout feature/task-5-iceberg-management

# Ver los cambios
git log
git diff main

# Volver a tu rama
git checkout feature/task-X-nombre-descriptivo
```

---

## 🔀 Opciones para Mergear a Main

### Opción 1: Merge Directo (Rápido, sin revisión)

**Cuándo usar**: Cuando confían en el trabajo del otro y quieren avanzar rápido.

```bash
# Vicente o Max pueden hacer esto:

# 1. Ir a main
git checkout main
git pull origin main

# 2. Mergear la rama de Vicente
git merge feature/task-5-iceberg-management

# 3. Subir a main
git push origin main

# 4. Avisar al equipo que main fue actualizado
```

### Opción 2: Pull Request en GitHub (Profesional, con revisión)

**Cuándo usar**: Cuando quieren revisar el código antes de mergear.

**Pasos:**
1. Ir a GitHub: https://github.com/vicemora97/Proyecto_Cenco
2. Verás un banner que dice "Compare & pull request"
3. Hacer clic y crear el Pull Request
4. Max revisa el código
5. Si todo está bien, Max aprueba y hace merge
6. La rama se mergea a `main`

### Opción 3: Merge Local con Revisión

**Cuándo usar**: Cuando quieren revisar juntos en persona.

```bash
# Max revisa el trabajo de Vicente:
git checkout feature/task-5-iceberg-management
# Revisar archivos, ejecutar tests, etc.

# Si todo está bien, mergear:
git checkout main
git merge feature/task-5-iceberg-management
git push origin main
```

---

## 🚨 Manejo de Conflictos

### Si hay conflictos al mergear:

```bash
# Git te dirá qué archivos tienen conflictos
git status

# Abrir los archivos con conflictos
# Buscar las marcas: <<<<<<< HEAD, =======, >>>>>>>

# Resolver manualmente eligiendo qué código mantener

# Después de resolver:
git add <archivos-resueltos>
git commit -m "fix: Resolve merge conflicts"
git push origin main
```

### Prevenir conflictos:
- Trabajar en archivos diferentes cuando sea posible
- Comunicarse sobre qué archivos van a modificar
- Hacer merges frecuentes a `main` para mantenerse sincronizados

---

## 📋 Convenciones de Nombres

### Ramas:
```
feature/task-5-iceberg-management     # Nueva funcionalidad
feature/task-7-deduplication          # Otra funcionalidad
bugfix/fix-serialization-issue        # Corrección de bug
docs/update-readme                    # Documentación
refactor/improve-error-handling       # Refactorización
```

### Commits:
```
feat(task-5): Implement Iceberg Table Management
fix(task-7): Resolve duplicate detection bug
docs: Update README with setup instructions
refactor: Improve error handling in writer
test: Add integration tests for ACID transactions
```

**Prefijos:**
- `feat`: Nueva funcionalidad
- `fix`: Corrección de bug
- `docs`: Documentación
- `test`: Tests
- `refactor`: Refactorización
- `chore`: Tareas de mantenimiento

---

## 🎯 Workflow Recomendado

### Flujo Diario:

1. **Inicio del día:**
   ```bash
   git checkout main
   git pull origin main
   git checkout tu-rama
   git merge main  # Traer cambios de main a tu rama
   ```

2. **Durante el trabajo:**
   ```bash
   # Hacer cambios
   git add .
   git commit -m "feat: Descripción"
   git push origin tu-rama
   ```

3. **Fin del día o al terminar tarea:**
   ```bash
   # Asegurarte de que todo está subido
   git push origin tu-rama
   
   # Avisar al equipo que terminaste
   # Coordinar merge a main
   ```

---

## 📞 Comunicación

### Antes de mergear a main:
- ✅ Avisar en el chat/grupo
- ✅ Asegurarse de que no hay trabajo en progreso que pueda romperse
- ✅ Ejecutar tests antes de mergear
- ✅ Documentar cambios importantes

### Después de mergear a main:
- ✅ Avisar al equipo
- ✅ Todos deben hacer `git pull origin main`
- ✅ Verificar que todo sigue funcionando

---

## 🔍 Comandos Útiles

### Ver estado:
```bash
git status                    # Ver cambios locales
git branch -a                 # Ver todas las ramas
git log --oneline --graph     # Ver historial gráfico
```

### Sincronizar:
```bash
git fetch origin              # Traer info del remoto
git pull origin main          # Actualizar main local
git push origin tu-rama       # Subir tu rama
```

### Limpiar:
```bash
git branch -d nombre-rama     # Borrar rama local (después de merge)
git push origin --delete nombre-rama  # Borrar rama remota
```

---

## ✅ Checklist antes de Mergear a Main

- [ ] Todos los tests pasan
- [ ] Código revisado (por ti mismo o por compañero)
- [ ] Documentación actualizada
- [ ] No hay archivos temporales o de prueba
- [ ] Commit messages son descriptivos
- [ ] No hay conflictos con main
- [ ] Compañero está informado

---

## 🎉 Resumen para Max

**Lo que necesitas hacer:**

1. **Actualizar tu repo:**
   ```bash
   git fetch origin
   git checkout main
   git pull origin main
   ```

2. **Crear tu rama:**
   ```bash
   git checkout -b feature/task-X-nombre
   ```

3. **Trabajar normalmente:**
   ```bash
   # Hacer cambios
   git add .
   git commit -m "feat(task-X): Tu trabajo"
   git push -u origin feature/task-X-nombre
   ```

4. **Cuando termines, coordinar con Vicente para mergear ambas ramas a main**

---

## 📚 Recursos

- [Git Branching Model](https://nvie.com/posts/a-successful-git-branching-model/)
- [Conventional Commits](https://www.conventionalcommits.org/)
- [GitHub Flow](https://guides.github.com/introduction/flow/)

---

**Generado**: 18 de Febrero de 2026  
**Versión**: 1.0  
**Equipo**: Vicente + Max
