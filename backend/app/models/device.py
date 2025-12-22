"""
Modelo de Dispositivo (Router Mikrotik).

Define la estructura para almacenar la información de los dispositivos de red gestionados.
Maneja información de conexión y credenciales cifradas.
"""

from ..db import db
from sqlalchemy.sql import func

class Device(db.Model):
    """
    Representa un dispositivo de red (Router) gestionado por el sistema.

    Nota: Las credenciales (usuario y contraseña) se almacenan cifradas en la base de datos
    utilizando cifrado simétrico (Fernet). Nunca deben almacenarse en texto plano.

    Attributes:
        id (int): Identificador único del dispositivo.
        tenant_id (int): Identificador del Tenant propietario.
        name (str): Nombre descriptivo o hostname del dispositivo.
        ip_address (str): Dirección IP de gestión.
        port (int): Puerto de gestión (SSH/API).
        username_encrypted (str): Nombre de usuario cifrado.
        password_encrypted (str): Contraseña cifrada.
        firmware_version (str): Versión del firmware detectada.
        location (str): Ubicación física o lógica del dispositivo.
        wan_type (str): Tipo de conexión WAN.
        created_at (datetime): Fecha de registro del dispositivo.
        is_active (bool): Indica si el dispositivo está activo (Soft Delete).
    """
    __tablename__ = "devices"

    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey("tenants.id"), nullable=False)
    name = db.Column(db.String(120), nullable=False)
    ip_address = db.Column(db.String(64), nullable=False)
    port = db.Column(db.Integer, nullable=False, default=22)
    username_encrypted = db.Column(db.String(512), nullable=False)
    password_encrypted = db.Column(db.String(512), nullable=False)
    firmware_version = db.Column(db.String(64), nullable=True)
    location = db.Column(db.String(120), nullable=True)
    wan_type = db.Column(db.String(64), nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, server_default=func.now())
    is_active = db.Column(db.Boolean, default=True, nullable=False)

    # Relaciones
    alerts = db.relationship("Alert", backref="device", lazy=True)
    logs = db.relationship("LogEntry", backref="device", lazy=True)
