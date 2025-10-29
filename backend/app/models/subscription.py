"""
Modelo Subscription (gestión de plan comercial):

Campos esperados:
- id (PK)
- tenant_id (FK)
- plan (BASICMAAT | INTERMAAT | PROMAAT)
- status (active | past_due | canceled)
- current_period_start, current_period_end
- external_ref (id de proveedor de pagos)
- created_at, updated_at
"""

from ..db import db
from sqlalchemy.sql import func

class Subscription(db.Model):
    __tablename__ = "subscriptions"

    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey("tenants.id"), nullable=False)
    plan_name = db.Column(db.String(32), nullable=False)  # BASICMAAT | INTERMAAT | PROMAAT
    max_devices = db.Column(db.Integer, nullable=False, default=5)
    activo_hasta = db.Column(db.DateTime(timezone=True), nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, server_default=func.now())