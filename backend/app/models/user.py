"""
Modelo User (usuarios internos por tenant):

Campos esperados:
- id (PK)
- tenant_id (FK -> Tenant)
- email (único por tenant)
- password_hash (bcrypt)
- role ("admin" | "noc")
- is_active
- created_at, updated_at
"""

from ..db import db
from sqlalchemy.sql import func
from sqlalchemy import UniqueConstraint

class User(db.Model):
    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint("tenant_id", "email", name="uq_users_tenant_email"),
    )

    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey("tenants.id"), nullable=False)
    email = db.Column(db.String(255), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(16), nullable=False, default="noc")  # admin | noc
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())