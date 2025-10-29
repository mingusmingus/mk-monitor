"""
Modelo Device (router MikroTik):

Campos esperados:
- id (PK)
- tenant_id (FK)
- nombre_amigable
- ip
- puerto
- username (cifrado en reposo)
- password (cifrado en reposo)
- salud (verde|amarillo|rojo calculado por alertas)
- created_at, updated_at
"""

from ..db import db
from sqlalchemy.sql import func

# IMPORTANTE:
# Las credenciales de Mikrotik (username/password) se almacenan cifradas
# usando una clave simétrica (ENCRYPTION_KEY) con cryptography.Fernet.
# No guardar nunca planos. Desencriptar sólo en uso operativo controlado.

class Device(db.Model):
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

    alerts = db.relationship("Alert", backref="device", lazy=True)
    logs = db.relationship("LogEntry", backref="device", lazy=True)