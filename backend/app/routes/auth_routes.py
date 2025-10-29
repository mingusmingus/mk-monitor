"""
Rutas de autenticación:

- Login, refresh token, gestión de usuarios por tenant.
- Placeholder de Blueprint sin endpoints todavía.
"""
from flask import Blueprint, request, jsonify
from ..auth.password import verify_password
from ..auth.jwt_utils import create_jwt
from ..models.user import User
from ..models.tenant import Tenant
from ..config import Config

auth_bp = Blueprint("auth", __name__)

@auth_bp.post("/auth/login")
def login():
    """
    Body: { email, password }
    Flujo:
      - Buscar user por email (y su tenant).
      - Verificar hash.
      - Verificar que el tenant no esté suspendido.
      - Emitir JWT con user_id, tenant_id y role.
    """
    data = request.get_json(silent=True) or {}
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    # TODO: Validaciones de input

    # TODO: Buscar usuario por email (y obtener tenant)
    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"error": "Credenciales inválidas"}), 401

    if not verify_password(password, user.password_hash):
        return jsonify({"error": "Credenciales inválidas"}), 401

    tenant = Tenant.query.get(user.tenant_id)
    if not tenant or tenant.status_pago == "suspendido":
        return jsonify({"error": "Tenant suspendido", "tenant_status": "suspendido"}), 403

    token = create_jwt(user.id, user.tenant_id, user.role, Config.TOKEN_EXP_MINUTES)
    return jsonify({
        "token": token,
        "role": user.role,
        "tenant_status": tenant.status_pago
    }), 200