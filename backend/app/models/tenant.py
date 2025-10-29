"""
Modelo Tenant (cliente/empresa):

Campos esperados:
- id (PK)
- nombre
- plan (BASICMAAT | INTERMAAT | PROMAAT)
- max_devices (derivado del plan)
- estado_suscripcion (activo, suspendido, cancelado)
- created_at, updated_at
"""
# Placeholder para clase SQLAlchemy a crear con Alembic
# class Tenant(Base): ...