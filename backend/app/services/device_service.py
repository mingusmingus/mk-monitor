"""
Servicio de Gestión de Dispositivos.

Provee funcionalidades para:
- Crear y listar dispositivos por tenant.
- Validar restricciones del plan comercial (límites de dispositivos).
- Cifrar y descifrar credenciales de acceso (routers) utilizando criptografía simétrica (Fernet).
"""
from typing import List, Dict, Any, Optional
from base64 import urlsafe_b64encode
from hashlib import sha256
from cryptography.fernet import Fernet
import logging
from ..models.device import Device
from ..db import db
from ..config import Config, is_dev, validate_encryption_key
from .subscription_service import can_add_device

class DeviceLimitReached(Exception):
    """
    Excepción lanzada cuando un tenant intenta exceder su límite de dispositivos.
    """
    def __init__(self, message: str, required_plan_hint: Optional[str] = None):
        super().__init__(message)
        self.message = message
        self.required_plan_hint = required_plan_hint
        self.upsell = True

def _get_fernet() -> Optional[Fernet]:
    """
    Obtiene una instancia de Fernet utilizando la clave de configuración ENCRYPTION_KEY.

    Comportamiento:
    - Producción: Requiere una clave Fernet válida (base64 urlsafe 32 bytes). Lanza error si falla.
    - Desarrollo: Permite fallback a texto plano o derivación de clave si la configuración es incorrecta,
      emitiendo advertencias.

    Returns:
        Optional[Fernet]: Instancia de cifrador, o None en modo desarrollo sin clave.
    """
    key = getattr(Config, "ENCRYPTION_KEY", None)

    # Caso: Clave ausente
    if not key:
        if is_dev():
            logging.warning("[WARNING] ENCRYPTION_KEY ausente en dev; usando passthrough (NO cifrado). Configura ENCRYPTION_KEY en infra/.env para probar cifrado.")
            return None
        raise RuntimeError("[ERROR] ENCRYPTION_KEY requerida en producción")

    # Caso: Clave válida (Fernet base64 urlsafe 32 bytes)
    if validate_encryption_key(key):
        try:
            return Fernet(key.encode("utf-8"))
        except Exception:
            pass

    # Caso: Clave no válida (Fallback Dev)
    if is_dev():
        logging.warning("[WARNING] ENCRYPTION_KEY no es una clave Fernet válida; derivando clave (DEV) con SHA-256")
        derived = urlsafe_b64encode(sha256(key.encode("utf-8")).digest())
        return Fernet(derived)

    raise RuntimeError("[ERROR] ENCRYPTION_KEY inválida; debe ser Fernet base64 urlsafe de 32 bytes en producción")

def encrypt_secret(plaintext: str) -> str:
    """
    Cifra un texto plano.

    Args:
        plaintext (str): Texto a cifrar.

    Returns:
        str: Texto cifrado en base64, o texto plano si no hay cifrador (solo dev).
    """
    if plaintext is None:
        return None
    f = _get_fernet()
    if not f:
        # Passthrough en dev
        return plaintext
    return f.encrypt(plaintext.encode("utf-8")).decode("utf-8")

def decrypt_secret(ciphertext: str) -> str:
    """
    Descifra un texto cifrado.

    Args:
        ciphertext (str): Texto cifrado.

    Returns:
        str: Texto plano descifrado.
    """
    if not ciphertext:
        return None
    f = _get_fernet()
    if not f:
        # Passthrough en dev: ya almacenado en claro
        return ciphertext
    return f.decrypt(ciphertext.encode("utf-8")).decode("utf-8")

def list_devices_for_tenant(tenant_id: int) -> List[Device]:
    """
    Lista todos los dispositivos asociados a un tenant.
    """
    return Device.query.filter_by(tenant_id=tenant_id).all()

def create_device(tenant_id: int, payload: Dict[str, Any]) -> Device:
    """
    Registra un nuevo dispositivo para un tenant.

    Valida el límite del plan y cifra las credenciales proporcionadas.

    Args:
        tenant_id (int): ID del tenant.
        payload (Dict[str, Any]): Datos del dispositivo (nombre, ip, usuario, password, etc.).

    Returns:
        Device: Instancia del dispositivo creado.

    Raises:
        DeviceLimitReached: Si el tenant ha alcanzado su límite de dispositivos.
    """
    can_add, reason = can_add_device(tenant_id)
    if not can_add:
        raise DeviceLimitReached(
            message=reason.get("message", "Límite de dispositivos alcanzado."),
            required_plan_hint=reason.get("required_plan_hint")
        )

    username_enc = payload.get("username_encrypted")
    password_enc = payload.get("password_encrypted")

    # Cifrar credenciales si vienen en texto plano
    if not username_enc and payload.get("username"):
        username_enc = encrypt_secret(payload["username"])
    if not password_enc and payload.get("password"):
        password_enc = encrypt_secret(payload["password"])

    device = Device(
        tenant_id=tenant_id,
        name=payload.get("name"),
        ip_address=payload.get("ip_address"),
        port=int(payload.get("port", 22)),
        username_encrypted=username_enc,
        password_encrypted=password_enc,
        firmware_version=payload.get("firmware_version"),
        location=payload.get("location"),
        wan_type=payload.get("wan_type"),
    )
    db.session.add(device)
    db.session.commit()
    return device
