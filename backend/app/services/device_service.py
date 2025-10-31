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
from ..models.device import Device
from ..db import db
from ..config import Config
from .subscription_service import can_add_device

class DeviceLimitReached(Exception):
    def __init__(self, message: str, required_plan_hint: Optional[str] = None):
        super().__init__(message)
        self.message = message
        self.required_plan_hint = required_plan_hint
        self.upsell = True

def _get_fernet() -> Fernet:
    """
    Deriva una clave válida de Fernet a partir de ENCRYPTION_KEY.
    Si la clave no es Fernet válida, derivamos con SHA-256.
    """
    raw = (Config.ENCRYPTION_KEY or "please-change-this-key").encode("utf-8")
    key = urlsafe_b64encode(sha256(raw).digest())
    return Fernet(key)

def encrypt_secret(plaintext: str) -> str:
    if plaintext is None:
        return None
    f = _get_fernet()
    return f.encrypt(plaintext.encode("utf-8")).decode("utf-8")

def decrypt_secret(ciphertext: str) -> str:
    if not ciphertext:
        return None
    f = _get_fernet()
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