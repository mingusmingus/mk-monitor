"""
Rutas de autenticación:

- Login, refresh token, gestión de usuarios por tenant.
"""
from flask import Blueprint, request, jsonify
from ..auth.password import verify_password
from ..auth.jwt_utils import create_jwt
from ..models.user import User
from ..models.tenant import Tenant
from ..config import Config
from ..__init__ import limiter
import time

# Protección básica anti fuerza bruta (en memoria).
# En producción usar Redis + rate limiter (por ejemplo, ventana deslizante) detrás de un proxy inverso.
FAILED_LOGINS: dict[tuple[str, str], dict] = {}
MAX_FAILED_ATTEMPTS = int(getattr(Config, "MAX_FAILED_ATTEMPTS", 5))
LOCKOUT_SECONDS = int(getattr(Config, "LOCKOUT_SECONDS", 5 * 60))  # 5 minutos

def _client_ip() -> str:
    xfwd = request.headers.get("X-Forwarded-For", "")
    if xfwd:
        return xfwd.split(",")[0].strip()
    return request.remote_addr or "unknown"

def _is_locked(key: tuple[str, str]) -> bool:
    entry = FAILED_LOGINS.get(key)
    if not entry:
        return False
    until = entry.get("blocked_until", 0)
    return until and until > int(time.time())

def _register_failed(key: tuple[str, str]) -> int:
    now = int(time.time())
    entry = FAILED_LOGINS.get(key) or {"count": 0, "blocked_until": 0}
    # Si han pasado más de LOCKOUT_SECONDS desde el último fallo, resetea contador
    last = entry.get("last_failed", 0)
    if last and now - last > LOCKOUT_SECONDS:
        entry["count"] = 0
    entry["count"] += 1
    entry["last_failed"] = now
    if entry["count"] >= MAX_FAILED_ATTEMPTS:
        entry["blocked_until"] = now + LOCKOUT_SECONDS
    FAILED_LOGINS[key] = entry
    return entry["count"]

def _reset_lock(key: tuple[str, str]) -> None:
    FAILED_LOGINS.pop(key, None)

auth_bp = Blueprint("auth", __name__)

@auth_bp.post("/auth/login")
@limiter.limit("10/minute; 50/hour", override_defaults=False)
def login():
    """
    Body: { email, password }
    Flujo:
      - Verifica hash de contraseña.
      - Si demasiados fallos consecutivos por IP+email, 429 durante un tiempo.
      - Emite JWT con user_id, tenant_id y role.
    """
    data = request.get_json(silent=True) or {}
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    # Anti fuerza bruta: bloquear por IP+email tras demasiados fallos consecutivos
    ip = _client_ip()
    lock_key = (ip, email)
    if _is_locked(lock_key):
        return jsonify({"error": "Demasiados intentos. Intenta nuevamente más tarde."}), 429

    user = User.query.filter_by(email=email).first()
    if not user:
        # Registrar fallo y potencialmente bloquear
        count = _register_failed(lock_key)
        status = 429 if count >= MAX_FAILED_ATTEMPTS else 401
        return jsonify({"error": "Credenciales inválidas"}), status

    if not verify_password(password, user.password_hash):
        count = _register_failed(lock_key)
        status = 429 if count >= MAX_FAILED_ATTEMPTS else 401
        return jsonify({"error": "Credenciales inválidas"}), status

    # Éxito: limpiar contador de fallos
    _reset_lock(lock_key)

    tenant = Tenant.query.get(user.tenant_id)

    token = create_jwt(user.id, user.tenant_id, user.role, Config.TOKEN_EXP_MINUTES)
    return jsonify({
        "token": token,
        "role": user.role,
        "tenant_status": tenant.status_pago if tenant else "activo"
    }), 200