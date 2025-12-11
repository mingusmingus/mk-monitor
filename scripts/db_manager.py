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
from typing import List, Tuple

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
        # Usamos shell=False para mayor seguridad
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

def resolve_paths() -> Tuple[str, str, str]:
    """
    Detecta las rutas críticas del proyecto de forma robusta.
    Retorna: (root_dir, backend_dir, infra_dir)
    """
    # db_manager.py está en scripts/
    current_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.dirname(current_dir) # scripts/.. -> root

    backend_dir = os.path.join(root_dir, "backend")
    infra_dir = os.path.join(root_dir, "infra")

    # Validaciones estructurales
    if not os.path.isdir(backend_dir):
        log_error(f"Estructura inválida: No se encontró backend en {backend_dir}")
        sys.exit(1)

    if not os.path.isdir(infra_dir):
        log_error(f"Estructura inválida: No se encontró infra en {infra_dir}")
        sys.exit(1)

    return root_dir, backend_dir, infra_dir

def verify_environment(infra_dir: str):
    """Verifica que exista el archivo .env en infra/."""
    env_path = os.path.join(infra_dir, ".env")
    if not os.path.exists(env_path):
        log_error(f"No se encontró el archivo de entorno crítico: {env_path}")
        log_info("Por favor cree el archivo infra/.env con las variables necesarias (DATABASE_URL, etc).")
        # No salimos aquí estrictamente, porque env.py también hace su chequeo, pero es mejor avisar.
        # El usuario pidió "Debe verificar que infra/.env existe antes de llamar a Alembic."
        sys.exit(1)
    else:
        log_success(f"Archivo de entorno encontrado: {env_path}")

def get_alembic_args(backend_dir: str) -> List[str]:
    """Retorna los argumentos base para alembic incluyendo el config explícito."""
    ini_path = os.path.join(backend_dir, "alembic.ini")
    if not os.path.exists(ini_path):
        log_error(f"No se encontró alembic.ini en: {ini_path}")
        sys.exit(1)

    return [sys.executable, "-m", "alembic", "-c", ini_path]

def check_connection(backend_dir):
    """Verifica la conexión a la base de datos (simulada o vía alembic current)."""
    log_info("Verificando conexión y estado actual...")
    # 'alembic current' muestra la revisión actual. Si falla, hay problemas de conexión o config.
    cmd = get_alembic_args(backend_dir) + ["current"]
    return run_command(cmd, cwd=backend_dir)

def make_migration(message, backend_dir):
    """Crea una nueva revisión de migración."""
    if not message:
        log_error("Debe proporcionar un mensaje para la migración.")
        return 1

    log_info(f"Creando migración con mensaje: '{message}'")
    cmd = get_alembic_args(backend_dir) + ["revision", "--autogenerate", "-m", message]
    return run_command(cmd, cwd=backend_dir)

def upgrade_db(backend_dir):
    """Aplica las migraciones pendientes (upgrade head)."""
    log_info("Aplicando migraciones pendientes...")
    cmd = get_alembic_args(backend_dir) + ["upgrade", "head"]
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

    # 1. Resolver rutas
    root_dir, backend_dir, infra_dir = resolve_paths()

    # 2. Verificar entorno
    verify_environment(infra_dir)

    # 3. Asegurar dependencias
    try:
        import dotenv
        import alembic
    except ImportError as e:
        log_error(f"Falta dependencia crítica: {e.name}")
        log_info("Ejecute: pip install python-dotenv alembic")
        sys.exit(1)

    # 4. Ejecutar comandos
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
