"""
Modelo de Entrada de Log.

Almacena los registros de log individuales recopilados de los dispositivos.
Utilizado para auditoría forense y análisis histórico.
"""

from ..db import db
from sqlalchemy.sql import func

class LogEntry(db.Model):
    """
    Representa una línea de log individual proveniente de un dispositivo.

    Attributes:
        id (int): Identificador único de la entrada de log.
        tenant_id (int): Identificador del Tenant propietario.
        device_id (int): Identificador del dispositivo origen.
        raw_log (str): Contenido crudo del log tal como se recibió.
        log_level (str): Nivel de severidad extraído (ej. 'info', 'error').
        timestamp_equipo (datetime): Fecha y hora del evento según el dispositivo.
        created_at (datetime): Fecha y hora de ingestión en el sistema.
    """
    __tablename__ = "logs"
    __table_args__ = (
        db.Index("ix_logs_device_ts", "device_id", "timestamp_equipo"),
        # Índice optimizado para consultas temporales por dispositivo
    )

    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey("tenants.id"), nullable=False)
    device_id = db.Column(db.Integer, db.ForeignKey("devices.id"), nullable=False)

    raw_log = db.Column(db.Text, nullable=False)  # Log Mikrotik tal cual
    log_level = db.Column(db.String(32), nullable=True)
    timestamp_equipo = db.Column(db.DateTime(timezone=True), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, server_default=func.now())
