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
from ..config import Config
from .errors import AuthTokenExpired, AuthTokenInvalid

logger = logging.getLogger(__name__)

def create_jwt(user_id: int | str, tenant_id: int, role: str, expires_minutes: int = None, issuer: str | None = None) -> str:
    """
    Emite un JWT con expiración obligatoria.
    Payload:
      - sub: user_id (RFC7519 exige string; se castea con str() para compatibilidad PyJWT).
      - tenant_id
      - role
      - exp: timestamp UNIX futuro
      - iat: timestamp de emisión
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
    token = jwt.encode(payload, Config.JWT_SECRET_KEY, algorithm="HS256")
    token_prefix = token[:16] if isinstance(token, str) else str(token)[:16]
    logger.debug(
        "[AUTH] JWT issued for sub=%s tenant=%s role=%s exp=%s token_prefix=%s",
        payload["sub"], tenant_id, role, exp_ts, token_prefix
    )
    return token


def decode_jwt(token: str) -> Dict[str, Any]:
    """
    Valida y decodifica JWT. Lanza AuthTokenExpired o AuthTokenInvalid según corresponda.
    """
    issuer = getattr(Config, "JWT_ISSUER", None)
    try:
        if issuer:
            return jwt.decode(token, Config.JWT_SECRET_KEY, algorithms=["HS256"], issuer=issuer)
        return jwt.decode(token, Config.JWT_SECRET_KEY, algorithms=["HS256"])
    except ExpiredSignatureError as exc:
        logger.warning("[AUTH] JWT decode error: token expirado")
        raise AuthTokenExpired("Token expirado") from exc
    except InvalidTokenError as exc:
        logger.warning("[AUTH] JWT decode error: token inválido (%s)", exc)
        raise AuthTokenInvalid("Token inválido") from exc