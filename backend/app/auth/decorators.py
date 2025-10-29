"""
Decoradores de autorización:

- @jwt_required: exige token JWT válido.
- @role_required("admin"|"noc"): controla acceso por rol.
- @tenant_required: asegura que el recurso consultado pertenece al tenant del token.
Nota: Implementaciones mínimas a completar cuando se creen endpoints.
"""
from functools import wraps
from flask import request, jsonify

def jwt_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        # TODO: Extraer y validar JWT del header Authorization: Bearer <token>
        # - Decodificar y adjuntar claims a request (p.ej. request.user)
        return fn(*args, **kwargs)
    return wrapper

def role_required(role: str):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            # TODO: Chequear rol en claims del JWT
            # - Rechazar con 403 si no coincide
            return fn(*args, **kwargs)
        return wrapper
    return decorator

def tenant_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        # TODO: Validar que la operación se realiza sobre datos del mismo tenant_id
        return fn(*args, **kwargs)
    return wrapper


#```

#````python
# // filepath: c:\Users\bravo\Downloads\PROYECTOS_PROGRAMACION\mk-monitor\backend\app\models\__init__.py
"""
Modelos de dominio (capas persistentes):

- Definen las entidades multi-tenant con tenant_id.
- No se implementa lógica, solo esqueleto/documentación.
"""