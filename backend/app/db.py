"""
Módulo de acceso a datos (SQLAlchemy).

Este módulo gestiona la instancia de SQLAlchemy para la interacción con la base de datos.
Provee la función de inicialización que vincula la instancia de base de datos con la aplicación Flask.

Nota: En entornos de producción, la gestión del esquema debe realizarse mediante Alembic.
"""
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def init_db(app):
    """
    Inicializa la extensión de base de datos con la aplicación Flask.

    En entorno de desarrollo ('dev'), intenta crear las tablas automáticamente si no existen.
    En producción, se asume que las tablas son gestionadas por migraciones (Alembic).

    Args:
        app (Flask): La instancia de la aplicación Flask.
    """
    db.init_app(app)
    
    # Creación automática de tablas solo en entorno de desarrollo
    if app.config.get('APP_ENV') == 'dev':
        with app.app_context():
            db.create_all()
