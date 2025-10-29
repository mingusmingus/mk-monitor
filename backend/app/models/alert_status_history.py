"""
Modelo AlertStatusHistory (histórico de estados para SLA):

Campos esperados:
- id (PK)
- alert_id (FK)
- old_status, new_status
- changed_by (user_id o sistema)
- changed_at (timestamp)
"""

from ..db import db
from sqlalchemy.sql import func

class AlertStatusHistory(db.Model):
    __tablename__ = "alert_status_history"

    id = db.Column(db.Integer, primary_key=True)
    alert_id = db.Column(db.Integer, db.ForeignKey("alerts.id"), nullable=False)
    previous_status_operativo = db.Column(db.String(16), nullable=False)
    new_status_operativo = db.Column(db.String(16), nullable=False)
    changed_by_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    changed_at = db.Column(db.DateTime(timezone=True), nullable=False, server_default=func.now())