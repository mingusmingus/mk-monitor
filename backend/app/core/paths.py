"""
Módulo de Rutas Central (Single Source of Truth).
Define las rutas absolutas del proyecto para eliminar fragilidad por rutas relativas.
"""
from pathlib import Path
import os

# Determinamos la ubicación de este archivo: backend/app/core/paths.py
# .resolve() elimina symlinks y normaliza la ruta
CORE_FILE = Path(__file__).resolve()

# backend/app/core
CORE_DIR = CORE_FILE.parent

# backend/app
APP_DIR = CORE_DIR.parent

# backend (BASE_DIR según instrucciones)
BASE_DIR = APP_DIR.parent

# root del repo (PROJECT_ROOT según instrucciones)
PROJECT_ROOT = BASE_DIR.parent

# infra (Donde vive el .env)
INFRA_DIR = PROJECT_ROOT / "infra"

# Verificaciones de sanidad (opcional pero recomendado para fail-fast)
if not BASE_DIR.exists():
    # Esto sería muy raro ya que estamos ejecutando código desde ahí, pero por consistencia.
    raise RuntimeError(f"Error Crítico: No se pudo determinar BASE_DIR: {BASE_DIR}")

if not PROJECT_ROOT.exists():
    raise RuntimeError(f"Error Crítico: No se pudo determinar PROJECT_ROOT: {PROJECT_ROOT}")

# Función para obtener rutas de forma segura
def get_env_file() -> Path:
    """Retorna la ruta absoluta al archivo .env en infra/."""
    return INFRA_DIR / ".env"
