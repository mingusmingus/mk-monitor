"""
Rutas de salud/monitor:

- Endpoint simple /api/health para verificar estado del servicio.
- Placeholder de Blueprint sin endpoints todavía.
"""
from flask import Blueprint

health_bp = Blueprint("health", __name__, url_prefix="/api/health")
