"""
Rutas de autenticación:

- Login, registro y verificación de sesión.
"""
from flask import Blueprint, request, jsonify
from ..auth.password import verify_password, hash_password
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

from ..auth.decorators import require_auth

# Registro: protección básica anti abuso independiente del login
FAILED_REGISTRATIONS: dict[tuple[str, str], dict] = {}
# Protección básica anti fuerza bruta (en memoria).
FAILED_LOGINS: dict[tuple[str, str], dict] = {}
MAX_FAILED_ATTEMPTS = int(getattr(Config, "MAX_FAILED_ATTEMPTS", 5))
LOCKOUT_SECONDS = int(getattr(Config, "LOCKOUT_SECONDS", 5 * 60))  # 5 minutos

def _client_ip() -> str:
    from flask import request as _req
    hdr = _req.headers.get("X-Forwarded-For", "").split(",", 1)[0].strip()
    return hdr or _req.remote_addr or "unknown"

def _is_locked(key: tuple[str, str]) -> bool:
    entry = FAILED_LOGINS.get(key)
    if not entry:
        return False
    until = entry.get("blocked_until", 0)
    return until and until > int(time.time())

def _register_failed(key: tuple[str, str]) -> int:
    now = int(time.time())
    entry = FAILED_LOGINS.get(key) or {"count": 0, "blocked_until": 0}
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
logger = logging.getLogger(__name__)

@auth_bp.post("/auth/login")
@limiter.limit("10/minute; 50/hour", override_defaults=False)
def login():
    """
    Body: { email, password }
    Emite JWT si credenciales correctas.
    """
    data = request.get_json(silent=True) or {}
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    ip = _client_ip()
    lock_key = (ip, email)
    if _is_locked(lock_key):
        logger.info("[AUTH] login blocked ip=%s email=%s", ip, email)
        return jsonify({"error": "Demasiados intentos. Intenta nuevamente más tarde."}), 429

    user = User.query.filter_by(email=email).first()
    if not user:
        count = _register_failed(lock_key)
        status = 429 if count >= MAX_FAILED_ATTEMPTS else 401
        logger.warning("[AUTH] login failed (user not found) ip=%s email=%s count=%s", ip, email, count)
        return jsonify({"error": "Credenciales inválidas"}), status

    if not verify_password(password, user.password_hash):
        count = _register_failed(lock_key)
        status = 429 if count >= MAX_FAILED_ATTEMPTS else 401
        logger.warning("[AUTH] login failed (bad password) ip=%s email=%s count=%s", ip, email, count)
        return jsonify({"error": "Credenciales inválidas"}), status

    _reset_lock(lock_key)
    tenant = Tenant.query.get(user.tenant_id)
    token = create_jwt(user.id, user.tenant_id, user.role, Config.TOKEN_EXP_MINUTES)
    logger.info("[AUTH] login ok sub=%s tenant_id=%s role=%s", user.id, user.tenant_id, user.role)
    return jsonify({
        "token": token,
        "role": user.role,
        "tenant_status": tenant.status_pago if tenant else "activo"
    }), 200

@auth_bp.post("/auth/register")
@limiter.limit("5/minute; 30/hour", override_defaults=False)
def register():
    """
    Registro público.
    """
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    full_name = (data.get("full_name") or "").strip()
    honeypot = (data.get("website") or "").strip()

    ip = _client_ip()
    reg_key = (ip, email)

    if honeypot:
        return jsonify({"error": "Bad request"}), 400
    if _reg_is_locked(reg_key):
        return jsonify({"error": "Demasiados intentos. Intenta nuevamente más tarde."}), 429

    if not email:
        _reg_register_failed(reg_key)
        return jsonify({"error": "email_required"}), 400
    if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        _reg_register_failed(reg_key)
        return jsonify({"error": "invalid_email"}), 400
    if len(password) < 8:
        _reg_register_failed(reg_key)
        return jsonify({"error": "weak_password"}), 400
    if User.query.filter_by(email=email).first():
        return jsonify({"error": "email_taken"}), 409

    tenant_name = email.split("@")[0] or "tenant"
    try:
        tenant = Tenant(name=tenant_name, plan="BASICMAAT", status_pago="activo")
        db.session.add(tenant)
        db.session.flush()

        user = User(
            tenant_id=tenant.id,
            email=email,
            password_hash=hash_password(password),
            role="admin",
            full_name=full_name or None,
        )
        db.session.add(user)

        create_initial_subscription(tenant.id, plan="BASICMAAT")
        db.session.commit()
        _reg_reset(reg_key)
        logger.info("[AUTH] register ok tenant_id=%s email=%s", tenant.id, email)
        return jsonify({"ok": True}), 201
    except Exception as e:
        db.session.rollback()
        logger.exception("[AUTH] register error email=%s", email)
        _reg_register_failed(reg_key)
        return jsonify({"error": "server_error"}), 500

@auth_bp.get("/auth/me")
@require_auth()
def auth_me():
    """
    Verificación rápida de validez de token JWT.
    Respuesta: { ok:true, sub, tenant_id, role }
    """
    return jsonify({
        "ok": True,
        "sub": getattr(logger, "user_id", None) or None,  # fallback simple
        "tenant_id": getattr(logger, "tenant_id", None) or None,
        "role": getattr(logger, "role", None) or None
    }), 200