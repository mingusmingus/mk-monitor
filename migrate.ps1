# Script PowerShell para aplicar migraciones
# Uso: .\migrate.ps1

Write-Host "🔄 Aplicando migraciones pendientes..." -ForegroundColor Cyan
python -m alembic -c backend/alembic.ini upgrade head

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Migraciones aplicadas exitosamente" -ForegroundColor Green
} else {
    Write-Host "❌ Error al aplicar migraciones" -ForegroundColor Red
    exit 1
}
