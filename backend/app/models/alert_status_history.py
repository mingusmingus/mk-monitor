"""
Modelo Histórico de Estado de Alertas.

Registra los cambios de estado operativo de una alerta para fines de auditoría
y cálculo de SLA (Acuerdos de Nivel de Servicio).
"""

from ..db import db
from sqlalchemy.sql import func

class AlertStatusHistory(db.Model):
    """
    Entidad que representa un registro en el historial de cambios de estado de una alerta.

    Attributes:
        id (int): Identificador único del registro histórico.
        alert_id (int): Referencia a la alerta asociada.
        previous_status_operativo (str): Estado operativo anterior.
        new_status_operativo (str): Nuevo estado operativo.
        changed_by_user_id (int): Identificador del usuario que realizó el cambio.
        changed_at (datetime): Fecha y hora del cambio.
    """
    __tablename__ = "alert_status_history"

    id = db.Column(db.Integer, primary_key=True)
    alert_id = db.Column(db.Integer, db.ForeignKey("alerts.id"), nullable=False)
    previous_status_operativo = db.Column(db.String(16), nullable=False)
    new_status_operativo = db.Column(db.String(16), nullable=False)
    changed_by_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    changed_at = db.Column(db.DateTime(timezone=True), nullable=False, server_default=func.now())
