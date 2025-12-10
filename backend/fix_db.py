"""
Script de reparación de base de datos.
Ejecutar para agregar la columna faltante 'full_name' a la tabla 'users'.

Uso:
    python backend/fix_db.py
"""
import sys
import os

# Asegurar que el directorio backend está en el path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.db import db
from sqlalchemy import text

def fix_database():
    app = create_app()
    with app.app_context():
        try:
            print("🔍 Verificando esquema de base de datos...")
            with db.engine.connect() as connection:
                # Verificar si existe la columna full_name en users
                result = connection.execute(text(
                    "SELECT column_name FROM information_schema.columns WHERE table_name='users' AND column_name='full_name';"
                ))

                if not result.fetchone():
                    print("⚠️ Columna 'full_name' faltante en 'users'. Agregando...")
                    connection.execute(text("ALTER TABLE users ADD COLUMN full_name VARCHAR(120);"))
                    connection.commit()
                    print("✅ Columna 'full_name' agregada exitosamente.")
                else:
                    print("ℹ️ La columna 'full_name' ya existe en la tabla 'users'.")

        except Exception as e:
            print(f"❌ Error al intentar reparar la base de datos: {e}")

if __name__ == "__main__":
    fix_database()
