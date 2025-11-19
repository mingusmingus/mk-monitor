# Script PowerShell para ver estado actual de migraciones
# Uso: .\migration-status.ps1

Write-Host "📊 Estado actual de migraciones" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "Revisión actual:" -ForegroundColor Yellow
python -m alembic -c backend/alembic.ini current

Write-Host ""
Write-Host "Historial completo:" -ForegroundColor Yellow
python -m alembic -c backend/alembic.ini history --verbose
