"""
Decoradores de autorización:

- require_auth(role=None): exige token JWT válido y opcionalmente rol.
"""
from functools import wraps
from flask import request, jsonify, g
from .jwt_utils import decode_jwt
from .errors import AuthTokenExpired, AuthTokenInvalid
import logging

logger = logging.getLogger(__name__)

def require_auth(role: str | None = None):
    """
    Decorador para proteger endpoints con JWT.
    - Lee Authorization Bearer <token>
    - Decodifica y adjunta g.user_id, g.tenant_id, g.role
    - Si role está definido, valida autorización (403 si no cumple)
    Respuestas 401 incluyen razón estructurada:
      {"error":"unauthorized","reason":"missing_header|malformed|decode_error|expired"}
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            auth_header = request.headers.get("Authorization", "")
            if not auth_header:
                logger.warning("[AUTH] AUTH 401: missing Authorization header")
                return jsonify({"error": "unauthorized", "reason": "missing_header"}), 401
            if not auth_header.startswith("Bearer "):
                logger.warning("[AUTH] AUTH 401: malformed header value=%s", auth_header[:32])
                return jsonify({"error": "unauthorized", "reason": "malformed"}), 401
            token = auth_header.split(" ", 1)[1].strip()
            if not token:
                logger.warning("[AUTH] AUTH 401: empty token after Bearer")
                return jsonify({"error": "unauthorized", "reason": "malformed"}), 401
            try:
                claims = decode_jwt(token)
            except AuthTokenExpired:
                logger.warning("[AUTH] AUTH 401: token expirado")
                return jsonify({"error": "unauthorized", "reason": "expired", "message": "Token expirado"}), 401
            except AuthTokenInvalid:
                logger.warning("[AUTH] AUTH 401: token inválido")
                return jsonify({"error": "unauthorized", "reason": "invalid", "message": "Token inválido"}), 401

            user_id = claims.get("sub")
            tenant_id = claims.get("tenant_id")
            role_claim = claims.get("role")

            if user_id is None or tenant_id is None or role_claim is None:
                logger.warning("[AUTH] AUTH 401: token sin claims esenciales (sub/tenant_id/role)")
                return jsonify({"error": "unauthorized", "reason": "missing_claims"}), 401

            try:
                g.user_id = int(user_id)
            except (TypeError, ValueError):
                g.user_id = user_id
            g.tenant_id = tenant_id
            g.role = role_claim

            if role is not None and g.role != role:
                logger.warning("[AUTH] AUTH 403: role mismatch required=%s got=%s", role, g.role)
                return jsonify({"error": "forbidden", "reason": "role_mismatch"}), 403

            return fn(*args, **kwargs)
        return wrapper
    return decorator


#```

#````python
# // filepath: c:\Users\bravo\Downloads\PROYECTOS_PROGRAMACION\mk-monitor\backend\app\models\__init__.py
"""
Modelos de dominio (capas persistentes):

- Definen las entidades multi-tenant con tenant_id.
- No se implementa lógica, solo esqueleto/documentación.
"""