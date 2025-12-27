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
from pathlib import Path

# Prefijos de log (Sin emojis)
INFO_PREFIX = "[INFO]"
ERROR_PREFIX = "[ERROR]"
SUCCESS_PREFIX = "[SUCCESS]"

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

def resolve_paths() -> Tuple[Path, Path]:
    """
    Detecta las rutas críticas del proyecto de forma robusta usando pathlib.
    Retorna: (root_dir, backend_dir)
    """
    # Este script está en scripts/db_manager.py
    script_path = Path(__file__).resolve()
    # scripts/db_manager.py -> scripts -> root
    root_dir = script_path.parent.parent
    backend_dir = root_dir / "backend"

    # Validaciones estructurales
    if not backend_dir.is_dir():
        log_error(f"Estructura inválida: No se encontró backend en {backend_dir}")
        sys.exit(1)

    return root_dir, backend_dir

def verify_environment(root_dir: Path):
    """Verifica que exista el archivo .env en la RAÍZ."""
    env_path = root_dir / ".env"
    if not env_path.exists():
        log_error(f"No se encontró el archivo de entorno crítico: {env_path}")
        log_info("Por favor cree el archivo .env en la raíz del proyecto.")
        sys.exit(1)
    else:
        log_success(f"Archivo de entorno encontrado: {env_path}")
        # Cargar variables de entorno explícitamente para este proceso
        try:
            from dotenv import load_dotenv
            load_dotenv(env_path)
        except ImportError:
            log_error("Falta la librería python-dotenv.")
            log_info("Ejecute: pip install python-dotenv")
            sys.exit(1)

def get_alembic_args(backend_dir: Path) -> List[str]:
    """Retorna los argumentos base para alembic incluyendo el config explícito."""
    ini_path = backend_dir / "alembic.ini"
    if not ini_path.exists():
        log_error(f"No se encontró alembic.ini en: {ini_path}")
        sys.exit(1)

    return [sys.executable, "-m", "alembic", "-c", str(ini_path)]

def check_connection(backend_dir: Path):
    """Verifica la conexión a la base de datos (simulada o vía alembic current)."""
    log_info("Verificando conexión y estado actual...")
    # 'alembic current' muestra la revisión actual. Si falla, hay problemas de conexión o config.
    cmd = get_alembic_args(backend_dir) + ["current"]
    return run_command(cmd, cwd=str(backend_dir))

def make_migration(message: str, backend_dir: Path):
    """Crea una nueva revisión de migración."""
    if not message:
        log_error("Debe proporcionar un mensaje para la migración.")
        return 1

    log_info(f"Creando migración con mensaje: '{message}'")
    cmd = get_alembic_args(backend_dir) + ["revision", "--autogenerate", "-m", message]
    return run_command(cmd, cwd=str(backend_dir))

def upgrade_db(backend_dir: Path):
    """Aplica las migraciones pendientes (upgrade head)."""
    log_info("Aplicando migraciones pendientes...")
    cmd = get_alembic_args(backend_dir) + ["upgrade", "head"]
    return run_command(cmd, cwd=str(backend_dir))

def main():
    parser = argparse.ArgumentParser(description="Gestor de Base de Datos Unificado")
    subparsers = parser.add_subparsers(dest="command", help="Comandos disponibles")

    # Comando make
    make_parser = subparsers.add_parser("make", help="Crea una nueva migración (revision --autogenerate)")
    make_parser.add_argument("message", help="Mensaje descriptivo de la migración")

    # Comando upgrade
    subparsers.add_parser("upgrade", help="Aplica cambios pendientes (upgrade head)")
    # Alias migrate -> upgrade
    subparsers.add_parser("migrate", help="Alias para 'upgrade' (aplica cambios pendientes)")

    # Comando check
    subparsers.add_parser("check", help="Verifica conexión y versión actual")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # 1. Resolver rutas
    root_dir, backend_dir = resolve_paths()

    # 2. Verificar entorno y cargar .env
    verify_environment(root_dir)

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
    elif args.command in ["upgrade", "migrate"]:
        sys.exit(upgrade_db(backend_dir))

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n")
        log_info("Operación cancelada por el usuario.")
        sys.exit(0)
