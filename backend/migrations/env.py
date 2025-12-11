from __future__ import annotations
import os
import sys
from logging.config import fileConfig
from dotenv import load_dotenv

from alembic import context
from sqlalchemy import engine_from_config, pool

# ---------------------------------------------------------
# CONFIGURACIÓN DE RUTAS Y ENTORNO
# ---------------------------------------------------------
# Aseguramos que sys.path incluya la raíz del backend y del proyecto
current_file_path = os.path.abspath(__file__)
backend_path = os.path.dirname(os.path.dirname(current_file_path))
root_path = os.path.dirname(backend_path)

if backend_path not in sys.path:
    sys.path.append(backend_path)
if root_path not in sys.path:
    sys.path.append(root_path)

# Intentamos cargar variables de entorno
try:
    from backend.app.core.paths import get_env_file
    dotenv_path = get_env_file()
except ImportError:
    # Fallback
    dotenv_path = os.path.join(root_path, "infra", ".env")
    print(f"Aviso: Usando ruta fallback para .env: {dotenv_path}")

if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path=dotenv_path)
else:
    print(f"Precaución: No se encontró .env en {dotenv_path}")

# Validación Crítica de DATABASE_URL
db_url = os.getenv("DATABASE_URL")
if not db_url:
    print("Error Crítico: No se encontró DATABASE_URL en variables de entorno.")
    sys.exit(1)

# Config de Alembic
config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# ---------------------------------------------------------
# IMPORTACIÓN DE MODELOS
# ---------------------------------------------------------
# Importamos la instancia de db (que contiene metadata)
# Ajustamos la ruta según lo encontrado en backend/app/db.py
from backend.app.db import db

# Importamos los modelos para que se registren en metadata
from backend.app.models import (
    tenant,
    user,
    device,
    subscription,
    alert,
    log_entry,
    alert_status_history,
)

# Asignar Metadata
target_metadata = db.metadata

# Configurar sqlalchemy.url forzando el valor del entorno
config.set_main_option("sqlalchemy.url", db_url)

def run_migrations_offline():
    """Modo offline: genera SQL usando la URL."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    """Modo online: conecta y ejecuta migraciones."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
