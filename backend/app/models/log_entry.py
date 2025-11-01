"""
Modelo LogEntry (entrada de log crudo/normalizado):

Campos esperados:
- id (PK)
- tenant_id (FK)
- device_id (FK)
- raw (texto del log)
- normalized (opcional)
- timestamp_log (cuando ocurrió en el equipo)
- created_at
"""

from ..db import db
from sqlalchemy.sql import func

class LogEntry(db.Model):
    __tablename__ = "logs"
    __table_args__ = (
        db.Index("ix_logs_device_ts", "device_id", "timestamp_equipo"),
        # TODO: evaluar índice compuesto por (tenant_id, device_id, timestamp_equipo) para queries por rango,
        #       garantizando timestamps en UTC (timezone-aware) de extremo a extremo.
    )

    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey("tenants.id"), nullable=False)
    device_id = db.Column(db.Integer, db.ForeignKey("devices.id"), nullable=False)

    raw_log = db.Column(db.Text, nullable=False)  # Log Mikrotik tal cual
    log_level = db.Column(db.String(32), nullable=True)
    timestamp_equipo = db.Column(db.DateTime(timezone=True), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, server_default=func.now())

# Nota: Este histórico debe tener índice por (device_id, timestamp_equipo) para consultas por rango.