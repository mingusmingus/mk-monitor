"""
Punto de entrada WSGI para el servidor de aplicaciones.

Este módulo inicializa la aplicación Flask y permite su ejecución
tanto en entornos de desarrollo como de producción (vía servidores WSGI).

Ejemplo de ejecución con Gunicorn:
    gunicorn backend.wsgi:app --bind 0.0.0.0:8000
"""
import sys
import os
from pathlib import Path

# Agregar la raíz del proyecto al path para resolver 'backend' como módulo
# Esto permite ejecutar 'python backend/wsgi.py' sin errores de importación
current_dir = Path(__file__).resolve().parent
# backend/wsgi.py -> backend -> root
project_root = current_dir.parent
sys.path.insert(0, str(project_root))

# Cargar variables de entorno explícitamente desde la raíz
# Esto es crítico para asegurar que gunicorn o wsgi carguen la config correcta
try:
    from dotenv import load_dotenv
    env_path = project_root / ".env"
    if env_path.exists():
        load_dotenv(env_path)
except ImportError:
    pass # Si no hay dotenv, asumimos variables de entorno del sistema

from backend.app import create_app

app = create_app()

if __name__ == "__main__":
    # Ejecución en modo desarrollo
    app.run(host="0.0.0.0", port=5000, debug=True)
