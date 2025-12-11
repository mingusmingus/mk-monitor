"""
Utilidades de Seguridad y Autenticación.

Provee funciones auxiliares para fortalecer la seguridad del sistema:
- Extracción confiable de dirección IP del cliente.
- Mecanismos de bloqueo temporal (Lockout) para prevenir ataques de fuerza bruta
  en login y registro.
- Configuración dinámica de políticas de intentos fallidos.
"""

import time
import logging
from flask import request

# Almacenamiento en memoria para protección anti-abuso (TODO: Migrar a Redis en prod)
FAILED_REGISTRATIONS: dict[tuple[str, str], dict] = {}
FAILED_LOGINS: dict[tuple[str, str], dict] = {}

# Valores por defecto (Seguros)
MAX_FAILED_ATTEMPTS = 5
LOCKOUT_SECONDS = 300  # 5 minutos

def configure_security(max_attempts: int, lockout_sec: int):
    """
    Actualiza los parámetros de seguridad globales desde la configuración.

    Args:
        max_attempts (int): Número máximo de intentos permitidos.
        lockout_sec (int): Tiempo de bloqueo en segundos.
    """
    global MAX_FAILED_ATTEMPTS, LOCKOUT_SECONDS
    MAX_FAILED_ATTEMPTS = max_attempts
    LOCKOUT_SECONDS = lockout_sec

def get_client_ip() -> str:
    """
    Extrae la dirección IP del cliente de los encabezados HTTP.
    Prioriza X-Forwarded-For para compatibilidad con proxies/load balancers.

    Returns:
        str: Dirección IP del cliente o 'unknown'.
    """
    hdr = request.headers.get("X-Forwarded-For", "").split(",", 1)[0].strip()
    return hdr or request.remote_addr or "unknown"

# --- Helpers para Bloqueo de Login ---

def is_login_locked(key: tuple[str, str]) -> bool:
    """
    Verifica si un intento de login está bloqueado para la llave dada (IP, Email).

    Args:
        key (tuple[str, str]): Identificador del intento (IP, Email).

    Returns:
        bool: True si está bloqueado, False en caso contrario.
    """
    entry = FAILED_LOGINS.get(key)
    if not entry:
        return False
    until = entry.get("blocked_until", 0)
    return until and until > int(time.time())

def register_login_failure(key: tuple[str, str]) -> int:
    """
    Registra un intento fallido de login e incrementa el contador.
    Aplica bloqueo si se supera el umbral.

    Args:
        key (tuple[str, str]): Identificador del intento.

    Returns:
        int: Número actual de intentos fallidos.
    """
    now = int(time.time())
    entry = FAILED_LOGINS.get(key) or {"count": 0, "blocked_until": 0}
    last = entry.get("last_failed", 0)

    # Reiniciar contador si ha pasado el tiempo de bloqueo desde el último fallo
    if last and now - last > LOCKOUT_SECONDS:
        entry["count"] = 0

    entry["count"] += 1
    entry["last_failed"] = now

    if entry["count"] >= MAX_FAILED_ATTEMPTS:
        entry["blocked_until"] = now + LOCKOUT_SECONDS

    FAILED_LOGINS[key] = entry
    return entry["count"]

def reset_login_lock(key: tuple[str, str]) -> None:
    """
    Limpia el registro de bloqueos para una llave (ej. tras login exitoso).

    Args:
        key (tuple[str, str]): Identificador del intento.
    """
    FAILED_LOGINS.pop(key, None)

# --- Helpers para Bloqueo de Registro ---

def is_registration_locked(key: tuple[str, str]) -> bool:
    """
    Verifica si el registro está bloqueado para la llave dada.

    Args:
        key (tuple[str, str]): Identificador del intento.

    Returns:
        bool: True si está bloqueado.
    """
    entry = FAILED_REGISTRATIONS.get(key)
    if not entry:
        return False
    until = entry.get("blocked_until", 0)
    return until and until > int(time.time())

def register_registration_failure(key: tuple[str, str]) -> int:
    """
    Registra un intento fallido de registro.

    Args:
        key (tuple[str, str]): Identificador del intento.

    Returns:
        int: Número actual de intentos fallidos.
    """
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

def reset_registration_lock(key: tuple[str, str]) -> None:
    """
    Limpia el registro de bloqueos de registro.

    Args:
        key (tuple[str, str]): Identificador del intento.
    """
    FAILED_REGISTRATIONS.pop(key, None)
