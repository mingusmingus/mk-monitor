"""
Script para inicializar la base de datos en desarrollo.
Crea todas las tablas definidas en los modelos.
"""
import os
import sys

# Asegurar que APP_ENV esté en modo desarrollo
os.environ['APP_ENV'] = 'dev'

# Configurar credenciales de DB si usas valores diferentes
os.environ['DB_USER'] = 'mkadmin'
os.environ['DB_PASS'] = 'tu_contraseña'  # Reemplaza con tu contraseña real
os.environ['DB_NAME'] = 'mkmonitor'
os.environ['DB_HOST'] = 'localhost'

from app import create_app
from app.db import db

def init_database():
    """Inicializa la base de datos creando todas las tablas."""
    app = create_app()
    
    with app.app_context():
        print("Creando tablas en la base de datos...")
        db.create_all()
        print("✓ Tablas creadas exitosamente!")
        
        # Mostrar tablas creadas
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        print(f"\nTablas creadas ({len(tables)}):")
        for table in sorted(tables):
            print(f"  - {table}")

if __name__ == '__main__':
    init_database()
