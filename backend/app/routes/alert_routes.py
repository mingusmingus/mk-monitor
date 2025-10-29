"""
Rutas de alertas:

- Listado, actualización de estado operativo y consulta por dispositivo.
- Placeholder de Blueprint sin endpoints todavía.
"""
from flask import Blueprint

alert_bp = Blueprint("alerts", __name__, url_prefix="/api/alerts")