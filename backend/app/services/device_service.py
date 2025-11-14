"""
Servicio de dispositivos:

- Alta/baja/modificación de equipos por tenant.
- Enforce de plan comercial (máximo de equipos).
- Cifrado/descifrado de credenciales de router con clave simétrica (ENCRYPTION_KEY).
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
    def __init__(self, message: str, required_plan_hint: Optional[str] = None):
        super().__init__(message)
        self.message = message
        self.required_plan_hint = required_plan_hint
        self.upsell = True

def _get_fernet() -> Optional[Fernet]:
    """
    Obtiene Fernet a partir de ENCRYPTION_KEY.
    - Dev: si ENCRYPTION_KEY ausente -> WARNING y passthrough (None).
    - Dev: si ENCRYPTION_KEY no es válida Fernet -> derivar por SHA-256 (WARNING).
    - Prod: si ausente o inválida -> excepción clara (Config ya valida en boot; doble guardia aquí).
    """
    key = getattr(Config, "ENCRYPTION_KEY", None)
    # Ausente
    if not key:
        if is_dev():
            logging.warning("ENCRYPTION_KEY ausente en dev; usando passthrough (NO cifrado). TODO: configura ENCRYPTION_KEY en infra/.env")
            return None
        raise RuntimeError("ENCRYPTION_KEY requerida en producción")

    # Válida (Fernet base64 urlsafe 32 bytes)
    if validate_encryption_key(key):
        try:
            return Fernet(key.encode("utf-8"))
        except Exception:
            # Si fallara por algún motivo inesperado, tratamos como inválida abajo
            pass

    # No válida
    if is_dev():
        logging.warning("ENCRYPTION_KEY no es una clave Fernet válida; derivando clave (DEV) con SHA-256")
        derived = urlsafe_b64encode(sha256(key.encode("utf-8")).digest())
        return Fernet(derived)
    raise RuntimeError("ENCRYPTION_KEY inválida; debe ser Fernet base64 urlsafe de 32 bytes en producción")

def encrypt_secret(plaintext: str) -> str:
    if plaintext is None:
        return None
    f = _get_fernet()
    if not f:
        # Passthrough en dev (NO cifrado). Evita logs de secretos.
        return plaintext
    return f.encrypt(plaintext.encode("utf-8")).decode("utf-8")

def decrypt_secret(ciphertext: str) -> str:
    if not ciphertext:
        return None
    f = _get_fernet()
    if not f:
        # Passthrough en dev: ya almacenado en claro
        return ciphertext
    return f.decrypt(ciphertext.encode("utf-8")).decode("utf-8")

def list_devices_for_tenant(tenant_id: int) -> List[Device]:
    return Device.query.filter_by(tenant_id=tenant_id).all()

def create_device(tenant_id: int, payload: Dict[str, Any]) -> Device:
    """
    Crea un device validando límite de plan y cifrando credenciales.
    Puede lanzar DeviceLimitReached con info de upsell.
    """
    can_add, reason = can_add_device(tenant_id)
    if not can_add:
        raise DeviceLimitReached(
            message=reason.get("message", "Límite de dispositivos alcanzado."),
            required_plan_hint=reason.get("required_plan_hint")
        )

    username_enc = payload.get("username_encrypted")
    password_enc = payload.get("password_encrypted")

    # Permitir entrada en claro y cifrar aquí si vienen como username/password
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