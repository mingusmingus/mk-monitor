"""
Decoradores de autorización:

- @jwt_required: exige token JWT válido.
- @role_required("admin"|"noc"): controla acceso por rol.
- @tenant_required: asegura que el recurso consultado pertenece al tenant del token.
Nota: Implementaciones mínimas a completar cuando se creen endpoints.
"""
from functools import wraps
from flask import request, jsonify, g
from .jwt_utils import decode_jwt

def require_auth(role: str | None = None):
    """
    Decorador para proteger endpoints con JWT.
    - Lee Authorization: Bearer <token>
    - Decodifica y adjunta g.user_id, g.tenant_id, g.role
    - Si role está definido, valida autorización (403 si no cumple)
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            auth_header = request.headers.get("Authorization", "")
            if not auth_header.startswith("Bearer "):
                return jsonify({"error": "Unauthorized"}), 401
            token = auth_header.split(" ", 1)[1].strip()
            try:
                claims = decode_jwt(token)
            except Exception:
                return jsonify({"error": "Invalid or expired token"}), 401

            g.user_id = claims.get("sub")
            g.tenant_id = claims.get("tenant_id")
            g.role = claims.get("role")

            if role is not None and g.role != role:
                return jsonify({"error": "Forbidden"}), 403

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