"""
Utilidades JWT:

- create_jwt(user_id, tenant_id, role, expires_minutes)
- decode_jwt(token)
"""
from datetime import datetime, timezone
import jwt
from jwt import ExpiredSignatureError, InvalidTokenError
import logging
from typing import Dict, Any
from flask import current_app
from ..config import Config
from .errors import AuthTokenExpired, AuthTokenInvalid

logger = logging.getLogger(__name__)

def _get_secret():
    """Retrieves secret from current_app config or static Config as fallback."""
    try:
        return current_app.config.get("JWT_SECRET_KEY") or Config.JWT_SECRET_KEY
    except RuntimeError:
        # Outside of app context
        return Config.JWT_SECRET_KEY

def create_jwt(user_id: int | str, tenant_id: int, role: str, expires_minutes: int = None, issuer: str | None = None) -> str:
    """
    Emite un JWT con expiración obligatoria.
    """
    exp_minutes = expires_minutes if expires_minutes is not None else Config.TOKEN_EXP_MINUTES
    now = datetime.now(timezone.utc)
    exp_ts = int(now.timestamp()) + int(exp_minutes) * 60
    payload: Dict[str, Any] = {
        "sub": str(user_id),
        "tenant_id": tenant_id,
        "role": role,
        "exp": exp_ts,
        "iat": int(now.timestamp()),
    }
    issuer = issuer or getattr(Config, "JWT_ISSUER", None)
    if issuer:
        payload["iss"] = issuer

    secret = _get_secret()
    if not secret:
        raise RuntimeError("[ERROR] JWT_SECRET_KEY no configurado.")

    token = jwt.encode(payload, secret, algorithm="HS256")

    if isinstance(token, bytes):
        token = token.decode('utf-8')

    token_prefix = token[:16]
    logger.debug(
        "[AUTH] JWT issued for sub=%s tenant=%s role=%s exp=%s token_prefix=%s",
        payload["sub"], tenant_id, role, exp_ts, token_prefix
    )
    return token


def decode_jwt(token: str) -> Dict[str, Any]:
    """
    Valida y decodifica JWT.
    """
    secret = _get_secret()
    if not secret:
        raise RuntimeError("[ERROR] JWT_SECRET_KEY no configurado.")

    issuer = getattr(Config, "JWT_ISSUER", None)
    try:
        if issuer:
            return jwt.decode(token, secret, algorithms=["HS256"], issuer=issuer)
        return jwt.decode(token, secret, algorithms=["HS256"])
    except ExpiredSignatureError as exc:
        logger.warning("[AUTH] JWT decode error: token expirado")
        raise AuthTokenExpired("Token expirado") from exc
    except InvalidTokenError as exc:
        logger.warning("[AUTH] JWT decode error: token inválido (%s)", exc)
        raise AuthTokenInvalid("Token inválido") from exc
