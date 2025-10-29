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

def create_access_token(payload: Dict[str, Any]) -> str:
    """
    Crea un JWT con expiración.
    Espera incluir: sub (user_id), tenant_id, role.
    """
    to_encode = payload.copy()
    to_encode["exp"] = int(time.time()) + int(Config.JWT_EXPIRES_MINUTES) * 60
    return jwt.encode(to_encode, Config.JWT_SECRET, algorithm=Config.JWT_ALGORITHM)

def decode_token(token: str) -> Dict[str, Any]:
    """
    Decodifica y valida un JWT. Lanza excepción si inválido/expirado.
    """
    return jwt.decode(token, Config.JWT_SECRET, algorithms=[Config.JWT_ALGORITHM])