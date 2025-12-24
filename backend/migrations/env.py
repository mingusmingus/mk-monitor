from __future__ import annotations
import os
import sys
from logging.config import fileConfig
from dotenv import load_dotenv

from alembic import context
from sqlalchemy import engine_from_config, pool
from pathlib import Path

# ---------------------------------------------------------
# CONFIGURACIÓN DE RUTAS Y ENTORNO
# ---------------------------------------------------------
# Aseguramos que sys.path incluya la raíz del backend y del proyecto
current_file_path = Path(__file__).resolve()
# backend/migrations/env.py -> backend/migrations
migrations_dir = current_file_path.parent
# backend/migrations -> backend
backend_dir = migrations_dir.parent
# backend -> root
root_dir = backend_dir.parent

if str(backend_dir) not in sys.path:
    sys.path.append(str(backend_dir))
if str(root_dir) not in sys.path:
    sys.path.append(str(root_dir))

# Cargar variables de entorno desde la RAÍZ (./.env)
dotenv_path = root_dir / ".env"

if dotenv_path.exists():
    print(f"[Alembic] Cargando .env desde: {dotenv_path}")
    load_dotenv(dotenv_path=dotenv_path)
else:
    print(f"[Alembic] PRECAUCIÓN: No se encontró .env en {dotenv_path}")

# Validación Crítica de DATABASE_URL
db_url = os.getenv("DATABASE_URL")
if not db_url:
    print("[Alembic] Error Crítico: No se encontró DATABASE_URL en variables de entorno.")
    # No salimos aquí para permitir comandos que no requieren DB si fuera el caso,
    # pero para migraciones fallará más adelante.

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
# Importamos explícitamente todos los módulos
try:
    from backend.app.models import (
        tenant,
        user,
        device,
        subscription,
        alert,
        log_entry,
        alert_status_history,
    )
except ImportError as e:
    print(f"[Alembic] Error importando modelos: {e}")

# Asignar Metadata
target_metadata = db.metadata

# Configurar sqlalchemy.url forzando el valor del entorno si existe
if db_url:
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
    # Obtenemos la configuración de sqlalchemy
    conf_section = config.get_section(config.config_ini_section)
    if not conf_section:
        conf_section = {}

    # Aseguramos que url esté en la configuración
    if db_url:
        conf_section["sqlalchemy.url"] = db_url

    connectable = engine_from_config(
        conf_section,
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
