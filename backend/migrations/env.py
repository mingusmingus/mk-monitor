from __future__ import annotations
import os
import sys
from logging.config import fileConfig
from dotenv import load_dotenv

from alembic import context
from sqlalchemy import engine_from_config, pool

# ---------------------------------------------------------
# CARGA ROBUSTA DE VARIABLES DE ENTORNO
# ---------------------------------------------------------
# Calculamos la ruta absoluta al archivo .env (asumiendo que está en backend/)
current_dir = os.path.dirname(os.path.abspath(__file__))  # backend/migrations
backend_dir = os.path.dirname(current_dir)              # backend
dotenv_path = os.path.join(backend_dir, ".env")

# Carga explícita
load_dotenv(dotenv_path=dotenv_path)

# Validación Crítica de DATABASE_URL
db_url = os.getenv("DATABASE_URL")

if not db_url:
    # Intento de fallback: buscar en root si no está en backend
    root_dir = os.path.dirname(backend_dir)
    dotenv_path_root = os.path.join(root_dir, ".env")
    load_dotenv(dotenv_path=dotenv_path_root)
    db_url = os.getenv("DATABASE_URL")

if not db_url:
    print("❌ Error: No se encontró DATABASE_URL en .env")
    print(f"   Ruta buscada: {dotenv_path}")
    sys.exit(1)

# Config de Alembic
config = context.config

# Permite logging si alembic.ini define [loggers]
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# No usamos autogenerate (target_metadata=None) en este MVP
target_metadata = None

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