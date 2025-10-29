"""
Rutas de autenticación:

- Login, refresh token, gestión de usuarios por tenant.
- Placeholder de Blueprint sin endpoints todavía.
"""
from flask import Blueprint

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")