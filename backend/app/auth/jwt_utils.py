"""
Utilidades JWT:

- create_access_token(payload): emite JWT con expiración.
- decode_token(token): valida y decodifica JWT.
- Se usa para autenticar usuarios por tenant y rol.
"""
import time
import jwt
from typing import Dict, Any
from ..config import Config

def create_jwt(user_id: int, tenant_id: int, role: str, expires_minutes: int = None) -> str:
    """
    Emite un JWT con expiración obligatoria.
    Payload:
      - sub: user_id
      - tenant_id
      - role
      - exp: timestamp UNIX
    """
    exp_minutes = expires_minutes if expires_minutes is not None else Config.TOKEN_EXP_MINUTES
    payload: Dict[str, Any] = {
        "sub": user_id,
        "tenant_id": tenant_id,
        "role": role,
        "exp": int(time.time()) + int(exp_minutes) * 60,
    }
    return jwt.encode(payload, Config.JWT_SECRET_KEY, algorithm="HS256")

def decode_jwt(token: str) -> Dict[str, Any]:
    """
    Valida y decodifica JWT. Lanza excepción si inválido/expirado.
    """
    return jwt.decode(token, Config.JWT_SECRET_KEY, algorithms=["HS256"])