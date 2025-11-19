# Desarrollo local (sin Docker)

Este documento describe cómo levantar el backend en un entorno local con `venv`, sin depender de Docker, y sin romper la configuración que usa Docker.

## Objetivos
- Mantener `infra/.env` orientado a Docker (hostname `postgres`).
- Usar variables de entorno en tu shell para desarrollo local.
- Evitar dependencia de Redis en local usando `memory://` para Flask-Limiter.

## Opción A: Script de activación (PowerShell)

1) Ejecuta el script para preparar variables en tu sesión actual:

```powershell
.\scripts\activate-local.ps1
```

2) Inicia el backend (dentro de tu venv):

```powershell
cd backend
python wsgi.py
```

Con esto:
- `DB_HOST=localhost` y `DATABASE_URL` apuntan a tu Postgres local.
- `REDIS_URL=memory://` evita necesitar Redis instalado.

> Nota: El script no modifica archivos, solo define variables en la sesión actual de PowerShell.

## Opción B: Archivo `.env.local` en `infra/`

1) Copia el ejemplo y personaliza:

```powershell
Copy-Item infra\.env.local.example infra\.env.local
```

2) Carga este archivo antes de correr Flask. Dos opciones:

- Exportar variables manualmente (PowerShell):
  ```powershell
  Get-Content infra\.env.local | ForEach-Object {
    if ($_ -match '^(?<k>[^#=]+)=(?<v>.*)$') { $Env:$($Matches['k'].Trim()) = $Matches['v'].Trim() }
  }
  ```
- O usar `python-dotenv` directamente para ejecutar:
  ```powershell
  python -m dotenv -f infra\.env.local run -- python backend\wsgi.py
  ```

> El código actual busca `infra/.env` automáticamente; `infra/.env.local` no se carga por defecto para no cambiar comportamientos en producción. Usa una de las técnicas anteriores si quieres que aplique.

## Postgres local

- Verifica que Postgres responde en `localhost:5432`:
  ```powershell
  Test-NetConnection -ComputerName localhost -Port 5432
  ```
- Si necesitas crear usuario y base:
  ```sql
  CREATE ROLE mkadmin LOGIN PASSWORD 'mkpassword';
  CREATE DATABASE mkmonitor OWNER mkadmin;
  ```

## Problemas comunes

- "could not translate host name 'postgres'": estás fuera de Docker con `DB_HOST=postgres`; usa `localhost` o `DATABASE_URL` a localhost.
- "password authentication failed": revisa usuario/clave/rol en Postgres.
- "connection refused": Postgres no está escuchando en `localhost:5432`.

## Notas de seguridad

- No subas `.env.local` ni claves reales al repo (está ignorado en `.gitignore`).
- `JWT_SECRET` y `ENCRYPTION_KEY` reales deben mantenerse fuera de archivos versionados.
- En producción, considera Redis real (no `memory://`) y configura límites adecuados.
