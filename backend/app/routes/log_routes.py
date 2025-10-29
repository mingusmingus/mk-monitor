"""
Rutas de logs:

- Consulta histórica con filtros de fecha y dispositivo.
- Placeholder de Blueprint sin endpoints todavía.
"""
from flask import Blueprint

log_bp = Blueprint("logs", __name__, url_prefix="/api/logs")