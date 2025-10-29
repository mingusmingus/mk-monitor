"""
Modelo Tenant (cliente/empresa):

Campos esperados:
- id (PK)
- nombre
- plan (BASICMAAT | INTERMAAT | PROMAAT)
- max_devices (derivado del plan)
- estado_suscripcion (activo, suspendido, cancelado)
- created_at, updated_at
"""

from ..db import db
from sqlalchemy.sql import func

class Tenant(db.Model):
    __tablename__ = "tenants"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    plan = db.Column(db.String(32), nullable=False, default="BASICMAAT")  # BASICMAAT | INTERMAAT | PROMAAT
    status_pago = db.Column(db.String(16), nullable=False, default="activo")  # activo | suspendido
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, server_default=func.now())

    # Relaciones (opcionales)
    users = db.relationship("User", backref="tenant", lazy=True)
    devices = db.relationship("Device", backref="tenant", lazy=True)
    subscriptions = db.relationship("Subscription", backref="tenant", lazy=True)