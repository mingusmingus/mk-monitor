"""
Capa de acceso a datos (SQLAlchemy).

- Instancia Flask-SQLAlchemy para integración con Flask.
- En producción se inicializa vía Alembic (migraciones).
- Todas las entidades incluyen tenant_id para aislamiento multi-tenant.
"""
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def init_db(app):
    """
    Inicializa la extensión de base de datos con la app Flask.
    En desarrollo puede crear tablas (NO recomendado en prod, usar Alembic).
    """
    db.init_app(app)
    
    # Solo en desarrollo, crear tablas si no existen
    if app.config.get('APP_ENV') == 'dev':
        with app.app_context():
            db.create_all()