"""
Modelo Alert (alertas operativas generadas por IA):

Campos esperados:
- id (PK)
- tenant_id (FK)
- device_id (FK)
- estado ("Aviso" | "Alerta Menor" | "Alerta Severa" | "Alerta Crítica")
- accion_recomendada (texto corto)
- status_operativo ("Pendiente" | "En curso" | "Resuelta")
- comentario_ultimo
- created_at, updated_at
"""

from ..db import db
from sqlalchemy.sql import func

class Alert(db.Model):
    __tablename__ = "alerts"

    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey("tenants.id"), nullable=False)
    device_id = db.Column(db.Integer, db.ForeignKey("devices.id"), nullable=False)

    estado = db.Column(db.String(32), nullable=False)  # Aviso | Alerta Menor | Alerta Severa | Alerta Crítica
    titulo = db.Column(db.String(120), nullable=False)
    descripcion = db.Column(db.String(512), nullable=False)
    accion_recomendada = db.Column(db.String(255), nullable=False)

    status_operativo = db.Column(db.String(16), nullable=False, default="Pendiente")  # Pendiente | En curso | Resuelta
    comentario_ultimo = db.Column(db.String(255), nullable=True)

    created_at = db.Column(db.DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    histories = db.relationship("AlertStatusHistory", backref="alert", lazy=True)