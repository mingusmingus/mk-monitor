# Activa variables de entorno para desarrollo local (fuera de Docker)
# Uso: En PowerShell, ejecutar:  .\scripts\activate-local.ps1
# Nota: No modifica archivos, solo la sesión actual de PowerShell.

# Backend (Flask + SQLAlchemy)
$Env:APP_ENV = "dev"
$Env:DB_HOST = "localhost"
$Env:DATABASE_URL = "postgresql+psycopg2://mkadmin:mkpassword@localhost:5432/mkmonitor"

# Rate limiting: evitar dependencia de Redis en local
# Usa almacenamiento en memoria para Flask-Limiter
$Env:REDIS_URL = "memory://"

Write-Host "Entorno local preparado:" -ForegroundColor Green
Write-Host "  APP_ENV=$Env:APP_ENV"
Write-Host "  DB_HOST=$Env:DB_HOST"
Write-Host "  DATABASE_URL=$Env:DATABASE_URL"
Write-Host "  REDIS_URL=$Env:REDIS_URL"
