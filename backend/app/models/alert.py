"""
Modelo de Alerta.

Representa una incidencia operativa detectada en un dispositivo, generada automáticamente
por el sistema de análisis (IA o heurística).
"""

from ..db import db
from sqlalchemy.sql import func

class Alert(db.Model):
    """
    Entidad que representa una alerta operativa.

    Attributes:
        id (int): Identificador único de la alerta.
        tenant_id (int): Identificador del Tenant afectado.
        device_id (int): Identificador del dispositivo afectado.
        estado (str): Nivel de severidad ('Aviso', 'Alerta Menor', 'Alerta Severa', 'Alerta Crítica').
        titulo (str): Título breve de la alerta.
        descripcion (str): Descripción detallada del problema.
        accion_recomendada (str): Sugerencia de acción correctiva.
        status_operativo (str): Estado del ciclo de vida de la alerta ('Pendiente', 'En curso', 'Resuelta').
        comentario_ultimo (str): Último comentario agregado por un operador.
        created_at (datetime): Fecha de creación de la alerta.
        updated_at (datetime): Fecha de última actualización.
    """
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

    # Relaciones
    histories = db.relationship("AlertStatusHistory", backref="alert", lazy=True)
