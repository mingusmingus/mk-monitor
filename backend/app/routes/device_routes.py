"""
Rutas de dispositivos:

- CRUD de equipos MikroTik y validación de límites por plan.
- Placeholder de Blueprint sin endpoints todavía.
"""
from flask import Blueprint

device_bp = Blueprint("devices", __name__, url_prefix="/api/devices")