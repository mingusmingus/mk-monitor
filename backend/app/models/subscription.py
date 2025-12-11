"""
Modelo de Suscripción.

Gestiona los detalles del plan comercial contratado por un Tenant, incluyendo
límites de recursos y vigencia.
"""

from ..db import db
from sqlalchemy.sql import func

class Subscription(db.Model):
    """
    Representa la suscripción activa de un Tenant.

    Attributes:
        id (int): Identificador único de la suscripción.
        tenant_id (int): Identificador del Tenant asociado.
        plan_name (str): Nombre del plan comercial (ej. 'BASICMAAT').
        max_devices (int): Límite máximo de dispositivos permitidos.
        activo_hasta (datetime): Fecha de vencimiento de la suscripción.
        created_at (datetime): Fecha de creación del registro.
    """
    __tablename__ = "subscriptions"

    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey("tenants.id"), nullable=False)
    plan_name = db.Column(db.String(32), nullable=False)  # BASICMAAT | INTERMAAT | PROMAAT
    max_devices = db.Column(db.Integer, nullable=False, default=5)
    activo_hasta = db.Column(db.DateTime(timezone=True), nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, server_default=func.now())
