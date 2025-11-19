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
import logging
import re

from ..db import db
from ..services.subscription_service import create_initial_subscription
from ..services.subscription_service import PLAN_LIMITS
from ..auth.password import hash_password

# Registro: protección básica anti abuso independiente del login
FAILED_REGISTRATIONS: dict[tuple[str, str], dict] = {}
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

def _reg_is_locked(key: tuple[str, str]) -> bool:
    entry = FAILED_REGISTRATIONS.get(key)
    if not entry:
        return False
    until = entry.get("blocked_until", 0)
    return until and until > int(time.time())

def _reg_register_failed(key: tuple[str, str]) -> int:
    now = int(time.time())
    entry = FAILED_REGISTRATIONS.get(key) or {"count": 0, "blocked_until": 0}
    last = entry.get("last_failed", 0)
    if last and now - last > LOCKOUT_SECONDS:
        entry["count"] = 0
    entry["count"] += 1
    entry["last_failed"] = now
    if entry["count"] >= MAX_FAILED_ATTEMPTS:
        entry["blocked_until"] = now + LOCKOUT_SECONDS
    FAILED_REGISTRATIONS[key] = entry
    return entry["count"]

def _reg_reset(key: tuple[str, str]) -> None:
    FAILED_REGISTRATIONS.pop(key, None)

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


@auth_bp.post("/auth/register")
@limiter.limit("5/minute; 30/hour", override_defaults=False)
def register():
    """
    Registro público:
      - Body: { email, password, full_name? (opcional), website? (honeypot) }
      - Valida email (formato básico), password >= 8, email único global.
      - Crea Tenant (nombre = parte antes de '@'), User (role admin), y Subscription BASICMAAT.
      - Honeypot: si 'website' viene no vacío -> 400.
      - No emite JWT. Respuestas:
        * 201 { ok: true }
        * 409 { error: "email_taken" }
        * 400 { error: "..."} en validaciones
        * 429 rate limiting
    """
    logger = logging.getLogger(__name__)
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    full_name = (data.get("full_name") or "").strip()
    honeypot = (data.get("website") or "").strip()

    # Honeypot (bots)
    if honeypot:
        return jsonify({"error": "Bad request"}), 400

    # Anti fuerza-bruta por IP+email para registro
    ip = _client_ip()
    reg_key = (ip, email)
    if _reg_is_locked(reg_key):
        return jsonify({"error": "Demasiados intentos. Intenta nuevamente más tarde."}), 429

    # Validaciones
    if not email:
        _reg_register_failed(reg_key)
        return jsonify({"error": "email_required"}), 400
    if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        _reg_register_failed(reg_key)
        return jsonify({"error": "invalid_email"}), 400
    if len(password) < 8:
        _reg_register_failed(reg_key)
        return jsonify({"error": "weak_password"}), 400

    # Email único global (aunque la restricción de DB es por tenant)
    if User.query.filter_by(email=email).first():
        return jsonify({"error": "email_taken"}), 409

    # Crear Tenant + Usuario + Suscripción
    tenant_name = email.split("@")[0] or "tenant"
    try:
        tenant = Tenant(name=tenant_name, plan="BASICMAAT", status_pago="activo")
        db.session.add(tenant)
        db.session.flush()  # asegurar tenant.id

        user = User(
            tenant_id=tenant.id,
            email=email,
            password_hash=hash_password(password),
            role="admin",  # usar rol existente en el sistema
        )
        db.session.add(user)

        # Suscripción inicial BASICMAAT (5 dispositivos)
        create_initial_subscription(tenant.id, plan="BASICMAAT")

        db.session.commit()
        _reg_reset(reg_key)
        logger.info("Nuevo tenant y usuario creados tenant_id=%s email=%s plan=BASICMAAT", tenant.id, email)
        return jsonify({"ok": True}), 201
    except Exception as e:
        db.session.rollback()
        logger.exception("Error al registrar tenant/user para email=%s", email)
        # Registrar fallo a efectos del lockout
        _reg_register_failed(reg_key)
        return jsonify({"error": "server_error"}), 500