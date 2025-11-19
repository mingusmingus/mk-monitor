# Script PowerShell para crear nueva migración
# Uso: .\new-migration.ps1 "descripcion del cambio"

param(
    [Parameter(Mandatory=$true)]
    [string]$Message
)

Write-Host "📝 Generando nueva migración: $Message" -ForegroundColor Cyan
python -m alembic -c backend/alembic.ini revision --autogenerate -m "$Message"

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Migración generada exitosamente" -ForegroundColor Green
    Write-Host "📋 Revisa el archivo generado en backend/migrations/versions/" -ForegroundColor Yellow
    Write-Host "🚀 Para aplicarla: .\migrate.ps1" -ForegroundColor Yellow
} else {
    Write-Host "❌ Error al generar migración" -ForegroundColor Red
    exit 1
}
