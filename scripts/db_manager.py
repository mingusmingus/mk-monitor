#!/usr/bin/env python3
"""
Gestor de Base de Datos Unificado
---------------------------------
Herramienta CLI para gestionar migraciones y estado de la base de datos
de forma robusta y multiplataforma.

Uso:
    python scripts/db_manager.py make "Mensaje de migración"
    python scripts/db_manager.py upgrade
    python scripts/db_manager.py check
"""
import sys
import os
import subprocess
import argparse
from typing import List

# Definimos colores para logs si es compatible, o usamos prefijos simples
INFO_PREFIX = "[INFO] ℹ️ "
ERROR_PREFIX = "[ERROR] ❌ "
SUCCESS_PREFIX = "[SUCCESS] ✅ "

def log_info(msg):
    print(f"{INFO_PREFIX} {msg}")

def log_error(msg):
    print(f"{ERROR_PREFIX} {msg}")

def log_success(msg):
    print(f"{SUCCESS_PREFIX} {msg}")

def run_command(command: List[str], cwd: str = None) -> int:
    """Ejecuta un comando en un subproceso y maneja errores."""
    cmd_str = " ".join(command)
    log_info(f"Ejecutando: {cmd_str}")

    try:
        # Usamos shell=False para mayor seguridad, a menos que sea estrictamente necesario
        # En Windows, si command[0] es un script .cmd o .bat, shell=True puede ser necesario,
        # pero 'alembic' suele ser un ejecutable en Scripts/ o bin/ del venv.
        # Para máxima compatibilidad, llamamos a través de 'python -m alembic'

        result = subprocess.run(
            command,
            cwd=cwd,
            check=False,
            env=os.environ.copy() # Pasamos el entorno actual
        )

        if result.returncode != 0:
            log_error(f"El comando falló con código {result.returncode}")
            return result.returncode

        return 0
    except FileNotFoundError:
        log_error(f"Comando no encontrado: {command[0]}")
        return 1
    except Exception as e:
        log_error(f"Error inesperado: {e}")
        return 1

def get_backend_dir():
    """Retorna la ruta absoluta al directorio backend."""
    # scripts/db_manager.py -> scripts/ -> root -> backend/
    current_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.dirname(current_dir)
    backend_dir = os.path.join(root_dir, "backend")

    if not os.path.isdir(backend_dir):
        log_error(f"No se encontró el directorio backend en: {backend_dir}")
        sys.exit(1)

    return backend_dir

def check_connection(backend_dir):
    """Verifica la conexión a la base de datos (simulada o vía alembic current)."""
    log_info("Verificando conexión y estado actual...")
    # 'alembic current' muestra la revisión actual. Si falla, hay problemas de conexión o config.
    cmd = [sys.executable, "-m", "alembic", "current"]
    return run_command(cmd, cwd=backend_dir)

def make_migration(message, backend_dir):
    """Crea una nueva revisión de migración."""
    if not message:
        log_error("Debe proporcionar un mensaje para la migración.")
        return 1

    log_info(f"Creando migración con mensaje: '{message}'")
    cmd = [sys.executable, "-m", "alembic", "revision", "--autogenerate", "-m", message]
    return run_command(cmd, cwd=backend_dir)

def upgrade_db(backend_dir):
    """Aplica las migraciones pendientes (upgrade head)."""
    log_info("Aplicando migraciones pendientes...")
    cmd = [sys.executable, "-m", "alembic", "upgrade", "head"]
    return run_command(cmd, cwd=backend_dir)

def main():
    parser = argparse.ArgumentParser(description="Gestor de Base de Datos Unificado")
    subparsers = parser.add_subparsers(dest="command", help="Comandos disponibles")

    # Comando make
    make_parser = subparsers.add_parser("make", help="Crea una nueva migración (revision --autogenerate)")
    make_parser.add_argument("message", help="Mensaje descriptivo de la migración")

    # Comando upgrade
    subparsers.add_parser("upgrade", help="Aplica cambios pendientes (upgrade head)")

    # Comando check
    subparsers.add_parser("check", help="Verifica conexión y versión actual")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    backend_dir = get_backend_dir()

    # Aseguramos que python-dotenv y alembic estén instalados verificando imports
    try:
        import dotenv
        import alembic
    except ImportError as e:
        log_error(f"Falta dependencia crítica: {e.name}")
        log_info("Ejecute: pip install python-dotenv alembic")
        sys.exit(1)

    if args.command == "check":
        sys.exit(check_connection(backend_dir))
    elif args.command == "make":
        sys.exit(make_migration(args.message, backend_dir))
    elif args.command == "upgrade":
        sys.exit(upgrade_db(backend_dir))

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n")
        log_info("Operación cancelada por el usuario.")
        sys.exit(0)
