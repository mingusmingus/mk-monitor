"""
Capa de acceso a datos (SQLAlchemy).

- Define la sesión, engine y Base (Declarative) para modelos.
- En producción se inicializa vía Alembic (migraciones).
- Todas las entidades deberán incluir tenant_id para aislamiento multi-tenant.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session, declarative_base
from .config import Config

engine = create_engine(Config.DATABASE_URL, echo=False, future=True)
SessionLocal = scoped_session(sessionmaker(bind=engine, autocommit=False, autoflush=False))
Base = declarative_base()

def get_db():
    """Generador de sesiones para inyección controlada en rutas/servicios."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db(app=None):
    """
    Inicializador opcional para crear tablas base en desarrollo.
    En producción usar Alembic para versionado de esquema.
    """
    Base.metadata.create_all(bind=engine)