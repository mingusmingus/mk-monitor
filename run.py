"""
Script de entrada principal (Run).

Este script inicializa el entorno cargando las variables desde la raíz (.env)
y ejecuta la aplicación Flask. Es útil para entornos de desarrollo.
"""
import sys
import os
from pathlib import Path

# 1. Configurar rutas
# Estamos en /run.py (Raíz)
root_dir = Path(__file__).resolve().parent
backend_dir = root_dir / "backend"

# Agregar raíz al sys.path para imports absolutos (backend.app)
sys.path.insert(0, str(root_dir))

# 2. Cargar variables de entorno DESDE LA RAÍZ
try:
    from dotenv import load_dotenv
    env_path = root_dir / ".env"
    if env_path.exists():
        print(f"[INFO] run.py: Cargando .env desde {env_path}")
        load_dotenv(env_path, override=True)
    else:
        print(f"[WARNING] run.py: No se encontró .env en {env_path}")
except ImportError:
    print("[ERROR] run.py: python-dotenv no está instalado.")
    sys.exit(1)

# 3. Importar y crear app
try:
    from backend.app import create_app
except ImportError as e:
    print(f"[ERROR] run.py: No se pudo importar la app. Verifique sys.path. Detalle: {e}")
    sys.exit(1)

app = create_app()

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    debug = os.getenv("DEBUG", "1") == "1"
    print(f"[INFO] run.py: Iniciando servidor en puerto {port} (Debug={debug})")
    app.run(host="0.0.0.0", port=port, debug=debug)
