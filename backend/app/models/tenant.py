"""
Modelo de Tenant (Inquilino/Cliente).

Define la entidad principal para la arquitectura multi-tenant. Cada Tenant representa
un cliente u organización separada con sus propios recursos y usuarios.
"""

from ..db import db
from sqlalchemy.sql import func

class Tenant(db.Model):
    """
    Representa un cliente o entidad organizativa en el sistema.

    Attributes:
        id (int): Identificador único del Tenant.
        name (str): Nombre de la organización o cliente.
        plan (str): Plan de suscripción contratado (ej. 'BASICMAAT', 'PROMAAT').
        status_pago (str): Estado de la cuenta ('activo', 'suspendido').
        created_at (datetime): Fecha de registro en el sistema.
    """
    __tablename__ = "tenants"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    plan = db.Column(db.String(32), nullable=False, default="BASICMAAT")  # BASICMAAT | INTERMAAT | PROMAAT
    status_pago = db.Column(db.String(16), nullable=False, default="activo")  # activo | suspendido
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, server_default=func.now())

    # Relaciones
    users = db.relationship("User", backref="tenant", lazy=True)
    devices = db.relationship("Device", backref="tenant", lazy=True)
    subscriptions = db.relationship("Subscription", backref="tenant", lazy=True)
