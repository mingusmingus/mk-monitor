"""
Rutas NOC:

- Acciones del operador (marcar En curso/Resuelta, comentar).
- Placeholder de Blueprint sin endpoints todavía.
"""
from flask import Blueprint

noc_bp = Blueprint("noc", __name__, url_prefix="/api/noc")
