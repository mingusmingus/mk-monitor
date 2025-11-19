# 🗄️ Guía Rápida: Alembic para mk-monitor

## ✅ Estado Actual

- ✅ Base de datos: PostgreSQL local
- ✅ Migración inicial: `a1b2c3d4e5f6` (aplicada)
- ✅ Modelos y BD: **100% sincronizados**
- ✅ Template: Reparado y funcional

## 🚀 Comandos Esenciales (Windows PowerShell)

### Ver estado actual
```powershell
.\migration-status.ps1
```

### Crear nueva migración (cuando modificas un modelo)
```powershell
.\new-migration.ps1 "añade campo timezone a devices"
```

### Aplicar migraciones pendientes
```powershell
.\migrate.ps1
```

### Comandos directos (alternativos)
```powershell
# Estado actual
python -m alembic -c backend/alembic.ini current

# Crear migración
python -m alembic -c backend/alembic.ini revision --autogenerate -m "descripcion"

# Aplicar migraciones
python -m alembic -c backend/alembic.ini upgrade head

# Ver historial
python -m alembic -c backend/alembic.ini history

# Retroceder una migración (⚠️ cuidado en producción)
python -m alembic -c backend/alembic.ini downgrade -1
```

## 📝 Flujo de Trabajo Típico

### 1. Modificas un modelo
```python
# backend/app/models/device.py
class Device(db.Model):
    # ... campos existentes ...
    timezone = db.Column(db.String(50), default='UTC')  # NUEVO
```

### 2. Generas migración
```powershell
.\new-migration.ps1 "añade timezone a devices"
```

### 3. Revisas el archivo generado
```powershell
# Busca en: backend/migrations/versions/XXXX_añade_timezone_a_devices.py
# Verifica que el upgrade() tenga el ALTER TABLE correcto
```

### 4. Aplicas la migración
```powershell
.\migrate.ps1
```

### 5. Commiteas al repo
```powershell
git add backend/migrations/versions/XXXX_*.py
git commit -m "Migration: añade timezone a devices"
```

## ⚠️ Errores Comunes

### Error: "Could not determine revision id"
**Causa**: Archivo de migración corrupto o vacío.  
**Solución**: Eliminar el archivo `.py` problemático de `backend/migrations/versions/` y regenerar.

### Error: "Target database is not up to date"
**Causa**: BD desincronizada con código.  
**Solución**: 
```powershell
python -m alembic -c backend/alembic.ini upgrade head
```

### Error: "Can't locate revision identified by 'XXXX'"
**Causa**: Archivo de migración falta o mal nombrado.  
**Solución**: Verificar que todos los archivos `.py` en `versions/` tengan `revision = 'XXXX'` válido.

## 🔒 Reglas de Oro

1. **NUNCA** edites manualmente las tablas en producción → siempre usa migraciones.
2. **SIEMPRE** revisa el contenido del archivo generado antes de aplicar.
3. **NUNCA** hagas `downgrade` en producción sin backup.
4. **COMMITEA** los archivos de migración junto con los cambios de modelos.
5. **APLICA** migraciones en orden en todos los entornos (dev → staging → prod).

## 🎯 Próximos Pasos (cuando sea necesario)

- Modificar modelos → generar migración → aplicar
- En producción: integrar `migrate.ps1` en pipeline de deploy
- Backups automáticos antes de cada migración en producción

## 📞 Ayuda

Si algo falla:
1. Verifica estado: `.\migration-status.ps1`
2. Revisa logs de Alembic (INFO/ERROR)
3. Consulta `backend/migrations/README.md`
