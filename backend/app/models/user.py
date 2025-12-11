"""
Modelo de Usuario.

Define la estructura de datos para los usuarios del sistema, pertenecientes a un Tenant específico.
Maneja autenticación, roles y metadatos básicos.
"""

from ..db import db
from sqlalchemy.sql import func
from sqlalchemy import UniqueConstraint

class User(db.Model):
    """
    Representa un usuario dentro del sistema, asociado a un Tenant.

    Attributes:
        id (int): Identificador único del usuario.
        tenant_id (int): Referencia al Tenant al que pertenece el usuario.
        email (str): Correo electrónico del usuario (único por Tenant).
        password_hash (str): Hash de la contraseña del usuario.
        role (str): Rol del usuario en el sistema ('admin', 'noc').
        full_name (str): Nombre completo del usuario.
        created_at (datetime): Fecha y hora de creación.
        updated_at (datetime): Fecha y hora de última actualización.
    """
    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint("tenant_id", "email", name="uq_users_tenant_email"),
    )

    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey("tenants.id"), nullable=False)
    email = db.Column(db.String(255), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(16), nullable=False, default="noc")  # admin | noc
    full_name = db.Column(db.String(120), nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
